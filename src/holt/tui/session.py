"""Running an analysis, and getting told about it.

This is the only file in the TUI that touches `holt.agent`, `holt.model` or the
evidence layer. Screens read a `Session`; they never build a provider, never
choose a model, and never call the pipeline. Moving the engine's entry point
therefore breaks one file rather than every screen.

The run happens on a worker thread and reports through a queue, so the interface
stays responsive during a live run and needs no cooperation from the engine to
do it. In `--replay` the whole thing finishes in well under a second; the same
machinery is used either way, because a demo path that differs from the real one
is a demo of the wrong thing.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from holt import model as model_module
from holt.agent import entry, pipeline
from holt.evidence.fixtures import FixtureProvider
from holt.evidence.provider import EvidenceProvider
from holt.report import EntryPoint
from holt.tui import events
from holt.tui.observe import ObservingModel, ObservingProvider
from holt.types import Window

# Mirrors `holt.cli`. Imported from there rather than restated so that the TUI
# reads the same fixtures the CLI and the eval harness read.
from holt.cli import ISSUE_ROOT, PATHFINDER_TRAJECTORIES, normalise


@dataclass
class RunOptions:
    repo: str
    replay: bool = True
    live: bool = False
    entry_points: bool = True


@dataclass
class Session:
    """One analysis: its options, its event stream, and its result.

    `events` accumulates every event in order, so a screen entered late — the
    assessment view, opened after the run finished — can replay the history
    instead of needing to have been watching.
    """

    options: RunOptions
    log: list[events.Event] = field(default_factory=list)
    assessment: Any = None
    trace: Any = None
    error: str | None = None
    #: The provider the run used. Evidence lookups from the interface go
    #: through it rather than through a fresh one, so a reader checking a claim
    #: sees exactly what Stage D saw — a new provider has fetched nothing and
    #: would report every id as unresolvable.
    provider: Any = None
    _queue: queue.Queue = field(default_factory=queue.Queue)
    _thread: threading.Thread | None = None

    # ─── lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("session already started")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def drain(self) -> list[events.Event]:
        """Every event that arrived since the last call. Never blocks."""
        out: list[events.Event] = []
        while True:
            try:
                event = self._queue.get_nowait()
            except queue.Empty:
                break
            self.log.append(event)
            if isinstance(event, events.RunFinished):
                self.assessment, self.trace = event.assessment, event.trace
            elif isinstance(event, events.RunFailed):
                self.error = event.error
            out.append(event)
        return out

    @property
    def finished(self) -> bool:
        return self.assessment is not None or self.error is not None

    def resolve(self, evidence_id: str):
        """The record behind an id, or None. Read-only, and never raises."""
        if self.provider is None:
            return None
        try:
            return self.provider.resolve(evidence_id)
        except Exception:  # noqa: BLE001 - the inspector reports it, not this
            return None

    def wait(self, timeout: float | None = None) -> None:
        """Block until the worker exits. Used by tests and by `--print`."""
        if self._thread is not None:
            self._thread.join(timeout)
        self.drain()

    # ─── the run ────────────────────────────────────────────────────────────

    def _emit(self, event: events.Event) -> None:
        self._queue.put(event)

    def _run(self) -> None:
        opts = self.options
        repo = normalise(opts.repo)
        try:
            provider = ObservingProvider(_provider(opts.live), self._emit)
            self.provider = provider
            client = ObservingModel(
                model_module.build(repo, replay=opts.replay), self._emit, repo
            )
            self._emit(events.RunStarted(repo=repo, replayed=opts.replay))

            assessment, trace = pipeline.analyze(repo, provider, client)

            # Stage D's drops are recovered from the trace rather than guessed
            # from the resolution stream: the engine already decided, and the
            # view must show what it decided, not a reconstruction of it.
            for dropped in trace.dropped:
                self._emit(
                    events.FindingDropped(
                        field=dropped.field,
                        value=dropped.value,
                        cited=tuple(dropped.evidence_ids),
                    )
                )
            self._emit(
                events.StageFinished(
                    stage="verify",
                    seconds=0.0,
                    summary=(
                        f"{trace.before_verification} findings → "
                        f"{trace.after_verification} kept, {len(trace.dropped)} dropped"
                    ),
                )
            )
            self._emit(
                events.StageFinished(
                    stage="verdict",
                    seconds=0.0,
                    summary=assessment.verdict.value,
                )
            )

            if opts.entry_points:
                self._rank(assessment, repo, provider, opts)

            self._emit(events.RunFinished(assessment=assessment, trace=trace))
        except Exception as exc:  # noqa: BLE001 - surfaced in the UI, not swallowed
            self._emit(events.RunFailed(error=f"{type(exc).__name__}: {exc}"))

    def _rank(self, assessment, repo: str, provider, opts: RunOptions) -> None:
        """Attach a reading order, or say nothing.

        Silent on a missing fixture for the same reason `holt.cli` is silent:
        a tool that invents an entry point when it has no issues is worse than
        one that omits the section.
        """
        try:
            issues = _issue_provider(opts.live).fetch(repo)
        except FileNotFoundError:
            return
        path = (
            model_module.TRAJECTORY_DIR
            / PATHFINDER_TRAJECTORIES
            / (repo.replace("/", "__") + ".jsonl")
        )
        try:
            client = (
                model_module.ReplayModel(path)
                if opts.replay
                else model_module.OpenAIModel(path)
            )
            self._emit(
                events.StageStarted(
                    stage="pathfinder", model=model_module.model_for("pathfinder")
                )
            )
            ranked = entry.rank(repo, list(issues), list(provider.fetch(repo)), client)
        except FileNotFoundError:
            return
        assessment.entry_points = [
            EntryPoint(r["evidence_id"], r["first_step"], r.get("why", ""))
            for r in ranked
        ]
        self._emit(
            events.StageFinished(
                stage="pathfinder",
                seconds=0.0,
                summary=f"{len(ranked)} issues ranked",
            )
        )


def _provider(live: bool) -> EvidenceProvider:
    if not live:
        return FixtureProvider(Window.PRE_T)
    from holt.evidence.github_graphql import LiveGitHubProvider

    return LiveGitHubProvider(Window.PRE_T)


def _issue_provider(live: bool) -> EvidenceProvider:
    if not live:
        return FixtureProvider(Window.PRE_T, root=Path(ISSUE_ROOT))
    from holt.evidence.github_graphql import LiveGitHubIssueProvider

    return LiveGitHubIssueProvider(Window.PRE_T)
