"""The trajectory event schema. Frozen.

This module is the contract between the running pipeline and anything that
watches it. It imports nothing from Textual and nothing from the TUI, so a
future consumer — a log renderer, the eval harness, a test — can depend on it
without dragging a terminal framework in.

Two rules keep it stable:

* **Events are added, never changed.** A stage that learns to emit a new kind of
  finding adds a new event class. Existing classes keep their fields and their
  meanings, so a renderer written today keeps working.
* **Renderers dispatch on type through a registry, never a chain of isinstance
  branches.** An event a renderer has never seen must degrade to a plain line
  rather than raising; `describe()` below guarantees every event has one.

The event stream is a *view* of the run. It is not how the run works, and
nothing in `holt.agent` reads it. Deleting this package would leave the engine,
the CLI and the eval harness untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Union

# ─── the stage vocabulary ───────────────────────────────────────────────────
#
# Mirrors the labels the pipeline passes to `ModelClient.complete`, plus the two
# steps that run no model. Kept as data rather than an enum so that a stage
# added to the engine shows up as itself instead of crashing the renderer.

STAGE_TITLES: dict[str, str] = {
    "classify": "classify",
    "opportunity": "opportunity",
    "outcomes": "outcomes",
    "verify": "verify",
    "verdict": "verdict",
    "narrate": "narrate",
    "pathfinder": "reading order",
}

#: Display order and gutter marks. Stages not listed here render after these,
#: in arrival order, with a blank mark — new stages appear rather than vanish.
STAGE_ORDER: tuple[tuple[str, str], ...] = (
    ("classify", "A"),
    ("opportunity", "B"),
    ("outcomes", "C"),
    ("verify", "D"),
    ("verdict", " "),
    ("narrate", "E"),
    ("pathfinder", " "),
)

#: Stages that may legitimately not run — the reading order is skipped when a
#: repository has no issue fixture. Their rows are mounted when they start
#: rather than sitting at "—" after the run has finished, which would read as a
#: stage that stalled rather than one that was never asked for.
OPTIONAL_STAGES: frozenset[str] = frozenset({"pathfinder"})


def stage_title(stage: str) -> str:
    return STAGE_TITLES.get(stage, stage)


def stage_mark(stage: str) -> str:
    for name, mark in STAGE_ORDER:
        if name == stage:
            return mark
    return " "


# ─── events ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RunStarted:
    repo: str
    replayed: bool


@dataclass(frozen=True, slots=True)
class EvidenceLoaded:
    """The provider handed over its records. The size of what the agent may see.

    `cutoff` is the boundary the provider *actually* applied, not the benchmark
    constant. A live provider defaults it to today; only a fixture run or an
    explicit `--as-of` is cut at T. A watcher that assumed T would report a
    holdout the run never applied, so the run states its own.
    """

    count: int
    window: str
    #: Defaulted rather than required: events are added to, never changed, and
    #: a caller written before this field existed still constructs a valid one.
    cutoff: datetime | None = None


@dataclass(frozen=True, slots=True)
class StageStarted:
    stage: str
    model: str


@dataclass(frozen=True, slots=True)
class StageFinished:
    stage: str
    seconds: float
    summary: str = ""


@dataclass(frozen=True, slots=True)
class ToolResponse:
    """A structured model response, as it came back, before a stage interprets it."""

    stage: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FindingEmitted:
    """A claim a stage is making, with the ids it says support it.

    Emitted *before* Stage D runs, so the live view can show a claim appear and
    then be taken away again. `evidence_ids` here is what the model cited, not
    what resolved.
    """

    stage: str
    field: str
    value: Any
    evidence_ids: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceResolved:
    """One lookup in Stage D. `resolved` false is the interesting case."""

    evidence_id: str
    resolved: bool


@dataclass(frozen=True, slots=True)
class FindingDropped:
    """A claim was removed. The moment the whole pipeline exists to make.

    Two reasons, and the difference matters to a reader watching: the cited
    thread does not exist, or it exists and does not contain the quoted words.
    Defaulted so an older producer of this event still describes itself.
    """

    field: str
    value: Any
    cited: tuple[str, ...] = ()
    reason: str = "unresolved"


@dataclass(frozen=True, slots=True)
class UsageUpdated:
    """Running total after a model call. Zero throughout a replay.

    Added after the first version of this schema shipped, which is the case the
    module was arranged for: a new class, no change to any existing one, and
    screens that predate it keep working because they simply have no entry for
    it in their dispatch table.
    """

    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass(frozen=True, slots=True)
class Retry:
    stage: str
    attempt: int
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RunFailed:
    error: str


@dataclass(frozen=True, slots=True)
class RunFinished:
    """Carries the finished `Assessment` and the pipeline's own `Trace`.

    Typed as `Any` so this module stays importable without pulling in the rest
    of the package; the attribute is always a `holt.report.Assessment`.
    """

    assessment: Any
    trace: Any


Event = Union[
    RunStarted,
    EvidenceLoaded,
    StageStarted,
    StageFinished,
    ToolResponse,
    FindingEmitted,
    EvidenceResolved,
    FindingDropped,
    UsageUpdated,
    Retry,
    RunFailed,
    RunFinished,
]


def describe(event: object) -> str:
    """A one-line fallback for any event, including ones added after this file.

    A renderer that has no specific handling for an event still has something
    truthful to print. Nothing in the UI may raise on an unrecognised event.
    """
    name = type(event).__name__
    fields = getattr(event, "__slots__", None) or ()
    parts = []
    for key in fields:
        value = getattr(event, key, None)
        text = str(value)
        parts.append(f"{key}={text[:60]}")
    return f"{name} " + " ".join(parts) if parts else name
