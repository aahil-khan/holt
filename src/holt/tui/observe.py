"""Watching a run without changing it.

`pipeline.analyze` takes a provider and a model client and knows nothing about
being observed. Rather than thread a callback through the engine — which would
put a UI concern in the reproduction path and give the eval harness a parameter
it has no use for — these two classes *wrap* the objects the pipeline is handed.

Both are pure delegates. They forward every attribute to the object they wrap,
add no behaviour to it, and never mutate what passes through. Removing them from
the call gives the byte-identical run the CLI performs, which is what keeps
`holt tui` from becoming a second way of running a stage.

The one place this file mirrors the engine is `_findings_from`, which reads a
stage's structured response so the live view can show a claim appear *before*
Stage D decides whether it survives. That mirroring is deliberate and pinned by
`tests/test_tui_observe.py`, which replays real recorded trajectories and fails
if a key this file expects has stopped being produced. A silent UI is worse than
a loud test.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from holt.agent.stages import normalise_citation
from holt.tui import events

Emit = Callable[[events.Event], None]


class ObservingModel:
    """A `ModelClient` that narrates its own calls.

    Wraps rather than subclasses, so it works over `OpenAIModel`, `ReplayModel`,
    or anything else satisfying the protocol, without knowing which it has.
    """

    def __init__(self, inner: Any, emit: Emit, repo: str = "") -> None:
        self._inner = inner
        self._emit = emit
        self._repo = repo

    def __getattr__(self, name: str) -> Any:
        # `replayed`, `usage`, and anything the client grows later.
        return getattr(self._inner, name)

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict:
        model_name = _model_name(self._inner, label)
        self._emit(events.StageStarted(stage=label, model=model_name))
        started = time.monotonic()
        try:
            result = self._inner.complete(
                label=label, system=system, prompt=prompt, schema=schema
            )
        except Exception as exc:  # noqa: BLE001 - reported, then re-raised unchanged
            self._emit(events.RunFailed(error=f"{label}: {type(exc).__name__}: {exc}"))
            raise
        elapsed = time.monotonic() - started

        self._emit(events.ToolResponse(stage=label, payload=result))
        usage = getattr(self._inner, "usage", None)
        if usage is not None:
            self._emit(
                events.UsageUpdated(
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    cost_usd=usage.cost_usd,
                )
            )
        for finding in _findings_from(label, result, self._repo):
            self._emit(finding)
        self._emit(
            events.StageFinished(
                stage=label, seconds=elapsed, summary=_summarise(label, result)
            )
        )
        return result


class ObservingProvider:
    """An `EvidenceProvider` that reports what was read and what resolved.

    Stage D's drop is not a special hook: it is `resolve()` returning `None`.
    Watching resolution is therefore enough to see the pipeline's central
    moment, with nothing added to the engine to expose it.
    """

    def __init__(self, inner: Any, emit: Emit) -> None:
        self._inner = inner
        self._emit = emit

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def fetch(self, request: str, /, **params: object) -> list:
        records = self._inner.fetch(request, **params)
        window = getattr(getattr(self._inner, "window", None), "value", "")
        self._emit(
            events.EvidenceLoaded(
                count=len(records),
                window=window,
                cutoff=getattr(self._inner, "cutoff", None),
            )
        )
        return records

    def resolve(self, evidence_id: str):
        record = self._inner.resolve(evidence_id)
        self._emit(
            events.EvidenceResolved(evidence_id=evidence_id, resolved=record is not None)
        )
        return record


# ─── reading a stage response ───────────────────────────────────────────────


def _model_name(inner: Any, label: str) -> str:
    try:
        from holt.model import model_for

        return model_for(label)
    except Exception:  # noqa: BLE001 - a display string is never worth raising over
        return ""


def _summarise(label: str, result: dict) -> str:
    """The one-line status that sits on the stage's own row."""
    if label == "classify":
        return str(result.get("repo_kind", ""))
    if label == "opportunity":
        return str(result.get("onboarding", ""))
    if label == "outcomes":
        threads = result.get("threads", []) or []
        posture = result.get("posture", "")
        return f"{posture} · {len(threads)} threads read" if posture else ""
    if label == "narrate":
        # `narrate` returns three sections now, not one `summary`. The count
        # that matters to a watcher is how much prose came back.
        written = sum(
            len(result.get(key, ""))
            for key in (
                "bottom_line",
                "what_the_evidence_shows",
                "what_could_not_be_determined",
            )
        )
        return f"{written} characters"
    if label == "pathfinder":
        issues = result.get("ranked", result.get("issues", [])) or []
        return f"{len(issues)} issues ranked"
    return ""


def _findings_from(label: str, result: dict, repo: str) -> list[events.FindingEmitted]:
    """The claims a stage is about to record, read off its structured response.

    Mirrors `holt.agent.stages`. Every lookup is tolerant: a missing key yields
    fewer events, never an exception, because a run must not fail because
    something was watching it.
    """
    out: list[events.FindingEmitted] = []

    def cite(raw) -> tuple[str, ...]:
        try:
            return tuple(normalise_citation(repo, e) for e in (raw or ()))
        except Exception:  # noqa: BLE001
            return tuple(str(e) for e in (raw or ()))

    if label == "classify":
        if "repo_kind" in result:
            out.append(
                events.FindingEmitted(
                    stage=label,
                    field="repo_kind",
                    value=result["repo_kind"],
                    evidence_ids=cite(result.get("evidence_ids")),
                    note=result.get("rationale", ""),
                )
            )
        flags = [f for f in result.get("governance_flags", []) or [] if f != "none"]
        if flags:
            out.append(
                events.FindingEmitted(
                    stage=label,
                    field="governance_flags",
                    value=flags,
                    evidence_ids=cite(result.get("evidence_ids")),
                )
            )

    elif label == "opportunity":
        if "onboarding" in result:
            out.append(
                events.FindingEmitted(
                    stage=label,
                    field="onboarding",
                    value=result["onboarding"],
                    evidence_ids=cite(result.get("evidence_ids")),
                    note=result.get("rationale", ""),
                )
            )

    elif label == "outcomes":
        threads = result.get("threads", []) or []
        if "posture" in result:
            out.append(
                events.FindingEmitted(
                    stage=label,
                    field="outsider_posture",
                    value=result["posture"],
                    evidence_ids=cite([t.get("pr_id") for t in threads]),
                    note=result.get("posture_rationale", ""),
                )
            )
        for entry in threads:
            out.append(
                events.FindingEmitted(
                    stage=label,
                    field="thread_outcome",
                    value={
                        "outcome": entry.get("outcome", ""),
                        "signal": entry.get("signal", ""),
                        "quote": entry.get("quote", ""),
                    },
                    evidence_ids=cite([entry.get("pr_id")]),
                )
            )

    return out


#: The response keys the live view reads, by stage. `tests/test_tui_observe.py`
#: replays recorded trajectories and asserts each one still appears, so a change
#: to a stage's schema breaks a test rather than emptying a panel.
EXPECTED_KEYS: dict[str, tuple[str, ...]] = {
    "classify": ("repo_kind", "rationale", "evidence_ids"),
    "opportunity": ("onboarding", "rationale", "evidence_ids"),
    "outcomes": ("posture", "posture_rationale", "threads"),
    "narrate": (
        "bottom_line",
        "what_the_evidence_shows",
        "what_could_not_be_determined",
    ),
}
