"""A run, without an engine.

The screens render an `Assessment` and a stream of events. Neither of those
needs a model, a provider, or a committed trajectory — but until now every
screen test got them by driving the real pipeline, which meant a prompt change
in the engine broke a dozen tests about layout and wording.

So the screens are tested against a scripted run built here. Two consequences,
both wanted:

* **Engine churn stops breaking interface tests.** When the recordings and the
  prompts disagree, that is one failure in the tests that check the recordings,
  not thirty in the tests that check the interface.
* **States that are hard to reach on demand become ordinary.** A dropped
  finding, a failure part-way through, a verdict this build has never seen —
  each is a few lines here rather than a hunt for a repository that happens to
  produce it.

The scripted stream is kept faithful to a real one: it was written by reading
the events an actual `home-assistant/core` replay emitted, in the order it
emitted them. `tests/test_tui_observe.py` is what holds it to that — those tests
drive the real engine, and they are the ones that should fail when the engine
moves.
"""

from __future__ import annotations

import queue
import time
from typing import Any

from holt.report import Assessment, Claim, EntryPoint, Verdict
from holt.types import T_CUTOFF
from holt.tui import events, store
from holt.tui.session import RunOptions, Session

REPO = "home-assistant/core"


def assessment(
    repo: str = REPO,
    verdict: Verdict = Verdict.VIABLE,
    claims: int = 6,
    with_entry_points: bool = False,
) -> Assessment:
    """A realistic report, with every field the engine has grown."""
    built = Assessment(
        repo=repo,
        verdict=verdict,
        summary=(
            "The strongest signal is activity and timeliness: of 200 total threads, "
            "119 involved outside contributors and 28 distinct outsiders had "
            "first-time merges, while 55 outsider threads were ignored."
        ),
        claims=[
            Claim(
                text=f"thread_outcome = merged_after_review ({i})",
                evidence_id=f"pr:{repo}#17{2400 + i}:opened",
            )
            for i in range(claims)
        ],
        method="holt (A classify, B opportunity, C outcomes, D verify, "
        "deterministic verdict, E narrate)",
        replayed=True,
    )
    _set(built, "bottom_line", "You'll usually get a human reply fast — median "
         "first response 2.3 hours — and outside contributors do get merged.")
    _set(built, "limits", "I could not determine whether certain contribution "
         "types have materially different acceptance rates.")
    _set(built, "rules", ["28 first-time merges by 28 distinct people, out of "
                          "119 attempts by 81; median first response 2.3h"])
    _set(built, "landing", ["## Where outsider work landed",
                            "homeassistant/components  24 of 96"])
    _set(built, "contributor_days", 7)
    if with_entry_points:
        _set(built, "entry_points",
             [EntryPoint(f"issue:{repo}#1717{i}", f"Fix the thing numbered {i}",
                         "because it is small and testable") for i in range(3)])
    return built


def _set(obj: Any, name: str, value: Any) -> None:
    """Only set fields this build's `Assessment` actually has."""
    if hasattr(obj, name):
        setattr(obj, name, value)


def script(
    repo: str = REPO, drop: bool = False, fail: str = "", cutoff=T_CUTOFF
) -> list:
    """The events a run emits, in the order a real one emits them.

    `cutoff` defaults to T because the scripted run is a replay off committed
    fixtures, which really is cut there. A live run passes its own.
    """
    out: list = [
        events.RunStarted(repo=repo, replayed=True),
        events.EvidenceLoaded(count=1231, window="pre_t", cutoff=cutoff),
    ]
    for stage, summary in (
        ("classify", "real_software"),
        ("opportunity", "substantive"),
        ("outcomes", "mixed · 12 threads read"),
    ):
        out.append(events.StageStarted(stage=stage, model="gpt-5-mini-2025-08-07"))
        out.append(events.ToolResponse(stage=stage, payload={}))
        out.append(
            events.FindingEmitted(
                stage=stage,
                field={"classify": "repo_kind", "opportunity": "onboarding",
                       "outcomes": "outsider_posture"}[stage],
                value=summary.split(" ·")[0],
                evidence_ids=(f"repo:{repo}:meta",),
            )
        )
        out.append(events.StageFinished(stage=stage, seconds=0.4, summary=summary))

        if fail == stage:
            out.append(events.RunFailed(error="the network went away"))
            return out

    if drop:
        out.append(events.FindingDropped(field="onboarding", value="absent", cited=()))
        kept, total = 14, 15
    else:
        kept, total = 15, 15
    out.append(
        events.StageFinished(
            stage="verify",
            seconds=0.0,
            summary=f"{total} findings → {kept} kept, {total - kept} dropped",
        )
    )
    out.append(events.StageFinished(stage="verdict", seconds=0.0, summary="viable"))
    out.append(events.StageStarted(stage="narrate", model="gpt-5-mini-2025-08-07"))
    out.append(events.StageFinished(stage="narrate", seconds=0.9, summary="1209 characters"))
    out.append(
        events.RunFinished(assessment=assessment(repo, claims=kept), trace=None)
    )
    return out


def session(
    repo: str = REPO,
    replay: bool = True,
    queued: list | None = None,
) -> Session:
    """A session whose events are already waiting. No thread, no engine."""
    built = Session(RunOptions(repo=repo, replay=replay))
    built.started_at = time.time()
    pending: queue.Queue = queue.Queue()
    for event in queued if queued is not None else script(repo):
        pending.put(event)
    built._queue = pending
    return built


def finished(repo: str = REPO, **kw) -> Session:
    """A session that has already produced a report. Nothing left to drain."""
    built = session(repo=repo, queued=[])
    built.assessment = assessment(repo, **kw)
    built.finished_at = time.time()
    return built


def stored_entry(
    repo: str = REPO,
    mode: str = "replay",
    age: float = 0.0,
    trace: bool = False,
    **kw,
) -> store.Entry:
    """An assessment as the store holds one.

    `trace=True` gives it the run's events, which is what a real one saved
    since holt started keeping them has. The default is without, because that
    is also a real case: everything stored before then.
    """
    return store.Entry(
        repo=repo,
        mode=mode,
        created_at=time.time() - age,
        assessment=assessment(repo, **kw),
        contributor_days=7,
        events=script(repo) if trace else [],
    )
