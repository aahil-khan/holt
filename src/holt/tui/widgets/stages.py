"""The stage list, and the moment Stage D removes a claim.

There is no progress bar here. A bar would have to invent a denominator — the
number of threads a stage will read is not known until it has read them — and a
bar that moves without meaning is worse than no bar. The count of what has been
read is the progress, and it is a real number.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget

from holt.tui import events, theme
from holt.tui.widgets.evidence import cite
from holt.tui.visual import Line


class StageRow(Line):
    """One stage: a gutter mark, its name, and where it has got to."""

    def __init__(self, stage: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stage = stage
        self._model = ""
        self._state = "pending"
        self._status = "—"

    def on_mount(self) -> None:
        self._repaint()

    def started(self, model: str) -> None:
        self._model, self._state, self._status = model, "running", "running"
        self._repaint()

    def finished(self, summary: str, seconds: float) -> None:
        self._state = "done"
        self._status = summary or "done"
        self._repaint()

    def _repaint(self) -> None:
        text = Text()
        text.append(f"{events.stage_mark(self.stage):<2} ", style=theme.FAINT)
        text.append(f"{events.stage_title(self.stage):<16}", style=theme.DIM)
        if self._state == "pending":
            text.append("—", style=theme.FAINT)
        elif self._state == "running":
            text.append(self._status, style=theme.DIM)
        else:
            text.append(self._status)
        self.update(text)


class StageList(Vertical):
    """Rows for the stages we expect, plus any the engine grows later.

    A stage the engine adds appears at the end of the list with a blank gutter
    mark rather than being dropped on the floor, so the interface reports the
    pipeline that ran instead of the pipeline it was written against.
    """

    def compose(self) -> ComposeResult:
        for stage, _mark in events.STAGE_ORDER:
            if stage in events.OPTIONAL_STAGES:
                continue
            yield StageRow(stage, id=f"stage-{stage}")

    def row(self, stage: str) -> StageRow | None:
        for row in self.query(StageRow):
            if row.stage == stage:
                return row
        return None

    def ensure(self, stage: str) -> StageRow:
        existing = self.row(stage)
        if existing is not None:
            return existing
        row = StageRow(stage)
        self.mount(row)
        return row


class EmittedFinding(Line):
    """A claim a stage just made, with the ids it says support it.

    Shown before Stage D has had its say, which is the point: the live view is
    where you watch a claim arrive and then, sometimes, be taken away.
    """

    def __init__(
        self, event: events.FindingEmitted, repo: str | None = None, **kwargs
    ) -> None:
        super().__init__(classes="finding", **kwargs)
        self.event = event
        self.repo = repo

    def on_mount(self) -> None:
        self.update(self._line())

    def _line(self) -> Text:
        event = self.event
        text = Text()
        if event.field == "thread_outcome" and isinstance(event.value, dict):
            for eid in event.evidence_ids[:1]:
                text.append_text(cite(eid, width=44, repo=self.repo))
            text.append("  ")
            text.append(str(event.value.get("outcome", "")), style=theme.DIM)
        else:
            text.append(f"{event.field} = {event.value}")
            for eid in event.evidence_ids[:1]:
                text.append("  ")
                text.append_text(cite(eid, width=40, repo=self.repo))
        return text


class DroppedFinding(Widget):
    """Stage D removed a claim.

    Given room rather than compressed to a line. This is the behaviour the whole
    pipeline is arranged around, and the reason a reader can trust the rest of
    the report: a claim the model made, whose evidence did not resolve, and which
    was therefore dropped rather than softened into a hedge.
    """

    def __init__(self, event: events.FindingDropped, **kwargs) -> None:
        super().__init__(**kwargs)
        self.event = event

    def compose(self) -> ComposeResult:
        event = self.event
        head = Text()
        head.append("✗ ", style=theme.DROP)
        head.append(f"{event.field} = {event.value!r}")
        yield Line(head)

        for eid in event.cited:
            row = Text("  ")
            row.append("cited  ", style=theme.DIM)
            row.append_text(cite(eid, resolves=False, width=50))
            row.append("   does not resolve", style=theme.DROP)
            yield Line(row)
        if not event.cited:
            row = Text("  ")
            row.append("cited  ", style=theme.DIM)
            row.append("nothing", style=theme.DROP)
            yield Line(row)

        yield Line(
            Text(
                "Dropped, not softened. The claim was asserted without a record that "
                "carries it, so it does not reach the reader.",
                style=theme.FAINT,
            ),
            classes="drop-reason",
        )


def unknown(event: object) -> Line:
    """Anything this file has no specific rendering for.

    An event added to the schema after this screen was written must still
    produce a truthful line. Nothing in the UI may raise on an event it has not
    seen before.
    """
    return Line(Text(events.describe(event), style=theme.FAINT), classes="finding")
