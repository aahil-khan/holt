"""Running an analysis, and getting told about it.

This is the only file in the TUI that touches `holt.agent`, `holt.model` or the
evidence layer. Screens read a `Session`; they never build a provider, never
choose a model, and never call the pipeline. Moving the engine's entry point
therefore breaks one file rather than every screen.

The run happens on a worker thread and reports through a queue, so the interface
stays responsive while a live run spends a minute on the network, and needs no
cooperation from the engine to do it.

A session can also be *restored* from a stored assessment, in which case no
thread starts and nothing is spent. That path exists so that opening this
morning's result and running a new one are the same object to every screen.
"""

from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from holt import model as model_module
from holt.agent import entry, pipeline
from holt.evidence.fixtures import FixtureProvider
from holt.evidence.provider import EvidenceProvider
from holt.report import EntryPoint
from holt.tui import events, store
from holt.tui.observe import ObservingModel, ObservingProvider, RunCancelled
from holt.types import Window

# Mirrors `holt.cli`. Imported from there rather than restated so that the TUI
# reads the same fixtures the CLI and the eval harness read.
from holt.cli import ISSUE_ROOT, PATHFINDER_TRAJECTORIES, normalise


@dataclass
class RunOptions:
    repo: str
    replay: bool = True
    live: bool = False
    #: Off by default, matching `holt analyze`. The ranking does not beat
    #: GitHub's `good first issue` label, and the engine demoted it to opt-in;
    #: an interface that turned it back on would be quietly overriding a
    #: measured decision.
    entry_points: bool = False
    contributor_days: int = 7
    #: Where a live run records its trajectory.
    #:
    #: Deliberately **not** `fixtures/trajectories/`. `OpenAIModel` appends every
    #: call to the path it is given, so pointing it at the committed fixtures
    #: would have the interface rewrite the evidence the eval harness replays.
    run_root: Path = Path("runs")
    #: Stamped once so every call in a run lands in the same file.
    started: str = field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    )

    @property
    def mode(self) -> str:
        """What this run *is*, in one word, for display and for cache keys.

        `replay` reads a recording. `recorded` makes real model calls over the
        committed fixtures. `live` additionally reads GitHub.
        """
        if self.replay:
            return "replay"
        return "live" if self.live else "recorded"

    def recording(self, repo: str, kind: str) -> Path:
        slug = repo.replace("/", "__")
        return self.run_root / slug / self.started / f"{kind}.jsonl"


@dataclass
class Session:
    """One analysis: its options, its event stream, and its result."""

    options: RunOptions
    log: list[events.Event] = field(default_factory=list)
    assessment: Any = None
    trace: Any = None
    error: str | None = None
    #: Set when this session is a stored assessment rather than a fresh run.
    #: Every screen showing a result checks it, because a reader must never have
    #: to wonder whether what they are looking at was just computed.
    restored_from: Any = None
    started_at: float = 0.0
    finished_at: float = 0.0
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    #: The provider the run used. Evidence lookups from the interface go
    #: through it rather than through a fresh one, so a reader checking a claim
    #: sees exactly what Stage D saw — a new provider has fetched nothing and
    #: would report every id as unresolvable.
    provider: Any = None
    #: The stage the run is in, for anything showing progress without showing
    #: the stream. Set from the events, so it cannot disagree with them.
    stage: str = ""
    #: Set when the run was stopped on purpose. Distinct from `error`: a stop
    #: is not a failure, and nothing about it should read like one.
    cancelled: bool = False
    _queue: queue.Queue = field(default_factory=queue.Queue)
    _thread: threading.Thread | None = None
    _cancel: threading.Event = field(default_factory=threading.Event)
    #: Stages that finished before a stop landed. Recorded on the worker thread,
    #: which is the only thread that writes it.
    _completed: list[str] = field(default_factory=list)

    # ─── construction ───────────────────────────────────────────────────────

    @classmethod
    def restored(cls, stored: Any) -> "Session":
        """A finished session backed by a stored assessment. Nothing runs."""
        options = RunOptions(
            repo=stored.repo,
            replay=stored.mode == "replay",
            live=stored.mode == "live",
            contributor_days=stored.contributor_days,
        )
        session = cls(options=options)
        session.assessment = stored.assessment
        session.restored_from = stored
        session.started_at = stored.created_at
        session.finished_at = stored.created_at + stored.duration_seconds
        session.cost_usd = stored.cost_usd
        return session

    # ─── lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("session already started")
        if self.restored_from is not None:
            raise RuntimeError("a restored session has nothing to run")
        self.started_at = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Ask the run to stop. It stops at the next model call or evidence read.

        Cannot be undone, and deliberately does not join: the caller is a key
        binding, and blocking the interface until a live model call returns
        would freeze the very screen that has to say `stopping`.
        """
        self._cancel.set()

    @property
    def running(self) -> bool:
        """A worker is alive and has not yet produced an outcome."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def stopping(self) -> bool:
        """Stopped by the reader, but the worker has not wound down yet."""
        return self._cancel.is_set() and self.running

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
                self.finished_at = time.time()
            elif isinstance(event, events.RunFailed):
                self.error = event.error
                self.finished_at = time.time()
            elif isinstance(event, events.RunCancelled):
                self.cancelled = True
                self.finished_at = time.time()
            elif isinstance(event, events.StageStarted):
                self.stage = event.stage
            elif isinstance(event, events.UsageUpdated):
                self.input_tokens = event.input_tokens
                self.output_tokens = event.output_tokens
                # Cost, but only when a call was actually paid for. A replay
                # reports the token counts the *original* run recorded, and
                # those price out to a real number; carrying it here would let
                # any screen render spend for a run that bought nothing.
                if not self.options.replay:
                    self.cost_usd = event.cost_usd
            out.append(event)
        return out

    @property
    def finished(self) -> bool:
        """Nothing more will arrive: it produced a report, failed, or was stopped."""
        return self.assessment is not None or self.error is not None or self.cancelled

    @property
    def duration(self) -> float:
        if not self.started_at:
            return 0.0
        return (self.finished_at or time.time()) - self.started_at

    def resolve(self, evidence_id: str):
        """The record behind an id, or None. Read-only, and never raises."""
        if self.provider is None:
            return None
        try:
            return self.provider.resolve(evidence_id)
        except Exception:  # noqa: BLE001 - the inspector reports it, not this
            return None

    def wait(self, timeout: float | None = None) -> None:
        """Block until the worker exits. Used by tests."""
        if self._thread is not None:
            self._thread.join(timeout)
        self.drain()

    def to_entry(self) -> Any:
        """This session as something the store can keep, if it produced anything.

        A restored session returns nothing: re-saving it would move its
        timestamp forward and make a stored answer look freshly computed.
        """
        if self.assessment is None or self.restored_from is not None:
            return None
        return store.Entry(
            repo=self.options.repo,
            mode=self.options.mode,
            created_at=self.started_at or time.time(),
            assessment=self.assessment,
            contributor_days=self.options.contributor_days,
            duration_seconds=self.duration,
            cost_usd=self.cost_usd,
        )

    # ─── the run ────────────────────────────────────────────────────────────

    def _emit(self, event: events.Event) -> None:
        if isinstance(event, events.StageFinished):
            self._completed.append(event.stage)
        self._queue.put(event)

    def _run(self) -> None:
        opts = self.options
        repo = normalise(opts.repo)
        try:
            provider = ObservingProvider(
                _provider(opts.live), self._emit, self._cancel.is_set
            )
            self.provider = provider
            client = ObservingModel(
                _client(repo, opts, "verdict"), self._emit, repo, self._cancel.is_set
            )
            self._emit(events.RunStarted(repo=repo, replayed=opts.replay))

            assessment, trace = pipeline.analyze(
                repo, provider, client, contributor_days=opts.contributor_days
            )

            # Stage D's drops are recovered from the trace rather than guessed
            # from the resolution stream: the engine already decided, and the
            # view must show what it decided, not a reconstruction of it.
            for dropped in trace.dropped:
                self._emit(
                    events.FindingDropped(
                        field=dropped.field,
                        value=dropped.value,
                        cited=tuple(dropped.evidence_ids),
                        reason="unresolved",
                    )
                )
            for invented in trace.invented:
                self._emit(
                    events.FindingDropped(
                        field=invented.field,
                        value=invented.value,
                        cited=tuple(invented.evidence_ids),
                        reason="unquoted",
                    )
                )
            self._emit(
                events.StageFinished(
                    stage="verify",
                    seconds=0.0,
                    summary=(
                        f"{trace.before_verification} findings → "
                        f"{trace.after_verification} kept, {len(trace.dropped)} dropped"
                        + (f", {len(trace.invented)} unquoted" if trace.invented else "")
                    ),
                )
            )
            self._emit(
                events.StageFinished(
                    stage="verdict", seconds=0.0, summary=assessment.verdict.value
                )
            )

            if opts.entry_points:
                self._rank(assessment, repo, provider, opts)

            self._emit(events.RunFinished(assessment=assessment, trace=trace))
        except RunCancelled:
            # Caught ahead of `Exception`: a stop the reader asked for must not
            # be reported as a defect, and nothing partial is stored.
            self._emit(events.RunCancelled(completed_stages=tuple(self._completed)))
        except Exception as exc:  # noqa: BLE001 - surfaced in the UI, not swallowed
            self._emit(events.RunFailed(error=readable(exc)))

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
        try:
            client = _client(repo, opts, PATHFINDER_TRAJECTORIES)
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
        # Same reason as `holt.cli.add_entry_points`: the ranker has its own
        # client and can be pointed at its own model, and the footer names every
        # model that wrote something on the page.
        for name in client.usage.models:
            if name not in assessment.models:
                assessment.models.append(name)
        self._emit(
            events.StageFinished(
                stage="pathfinder", seconds=0.0, summary=f"{len(ranked)} issues ranked"
            )
        )


def readable(exc: BaseException) -> str:
    """Turn an exception into something a person can act on.

    The failures that actually happen get a sentence saying what to do next.
    Everything else is reported as itself rather than dressed up, because a
    confident wrong guess about a cause is worse than the raw error.
    """
    text = str(exc)
    if isinstance(exc, FileNotFoundError):
        return (
            "No recording for this repository, so it cannot be replayed. "
            "Run it live instead."
        )
    if "not found or not public" in text:
        return f"{text}. Check the owner and name, and that the repository is public."
    if "GITHUB_TOKEN" in text or "OPENAI_API_KEY" in text:
        return text
    if "rate limit" in text.lower():
        return f"{text}. GitHub is rate limiting; wait a few minutes."
    return f"{type(exc).__name__}: {text}"


def _client(repo: str, opts: RunOptions, kind: str):
    """The model client for one part of a run.

    Replay reads the committed trajectory, exactly as the CLI does. A live run
    records to `runs/` instead, so the interface never appends to the fixtures
    the eval harness replays.
    """
    if opts.replay:
        directory = (
            model_module.TRAJECTORY_DIR
            if kind == "verdict"
            else model_module.TRAJECTORY_DIR / kind
        )
        return model_module.ReplayModel(directory / (repo.replace("/", "__") + ".jsonl"))
    return model_module.OpenAIModel(opts.recording(repo, kind))


def missing_credentials(opts: RunOptions) -> list[str]:
    """What a run needs before it is worth starting.

    Checked up front so the answer arrives as a sentence rather than a traceback
    part-way through a full-screen interface.
    """
    missing = []
    if not opts.replay and not os.environ.get("OPENAI_API_KEY"):
        missing.append(
            "OPENAI_API_KEY — the stages call a model. Without it, use replay."
        )
    if opts.live and not os.environ.get("GITHUB_TOKEN"):
        missing.append(
            "GITHUB_TOKEN — live mode reads GitHub directly. Without it, only "
            "repositories with committed fixtures can be assessed."
        )
    return missing


def has_recording(repo: str) -> bool:
    """Whether this repository can be replayed for free."""
    try:
        return (
            model_module.TRAJECTORY_DIR / (repo.replace("/", "__") + ".jsonl")
        ).is_file()
    except OSError:
        return False


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
