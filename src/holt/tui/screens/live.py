"""Watching the pipeline work.

The screen owns no engine knowledge. It drains a `Session`'s event queue and
renders what arrives, dispatching on event type through `HANDLERS` — a dict, not
a chain of branches. Adding an event to the schema means adding an entry here;
an event with no entry still renders, as a dim line, because a screen that
raises on an unfamiliar event is a screen that breaks every time a stage learns
something new.
"""

from __future__ import annotations

from typing import Callable

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.tui import events, theme
from holt.tui.visual import Line
from holt.tui.widgets.stages import (
    DroppedFinding,
    EmittedFinding,
    StageList,
    unknown,
)


POLL_SECONDS = 0.1


class LiveScreen(Screen):
    BINDINGS = [
        ("a", "assessment", "assessment"),
        ("q", "quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt · analyze", id="chrome-left")
            yield Line("", id="chrome-right")
        yield Line("─" * 200, classes="rule")
        yield StageList(id="stages")
        yield VerticalScroll(id="stream")
        yield Line("─" * 200, classes="rule")
        yield Footer()

    _spend = ""

    def on_mount(self) -> None:
        self._paint_chrome()
        self.set_interval(POLL_SECONDS, self._pump)

    def _paint_chrome(self) -> None:
        options = self.app.session.options
        # Says what the run actually is. `replay` reads a recording; `recorded`
        # means real model calls are being made and written to `runs/`; `live`
        # additionally means GitHub was read directly.
        mode = "replay" if options.replay else ("live" if options.live else "recorded")
        parts = [options.repo, mode]
        if self._spend:
            parts.append(self._spend)
        self.query_one("#chrome-right", Line).update(
            Text("   ".join(parts), style=theme.FAINT)
        )

    # ─── event pump ─────────────────────────────────────────────────────────

    def _pump(self) -> None:
        for event in self.app.session.drain():
            self._handle(event)

    def _handle(self, event: events.Event) -> None:
        handler = HANDLERS.get(type(event))
        if handler is None:
            self._append(unknown(event))
            return
        handler(self, event)

    def _append(self, widget) -> None:
        stream = self.query_one("#stream", VerticalScroll)
        stream.mount(widget)
        stream.scroll_end(animate=False)

    # ─── per-event rendering ────────────────────────────────────────────────

    def _on_run_started(self, event: events.RunStarted) -> None:
        return

    def _on_evidence_loaded(self, event: events.EvidenceLoaded) -> None:
        self._append(
            Line(
                Text(
                    f"{event.count} evidence records · window {event.window} "
                    "≤ 2026-06-01",
                    style=theme.FAINT,
                ),
                classes="finding",
            )
        )

    def _on_stage_started(self, event: events.StageStarted) -> None:
        row = self.query_one("#stages", StageList).ensure(event.stage)
        row.started(event.model)

    def _on_stage_finished(self, event: events.StageFinished) -> None:
        row = self.query_one("#stages", StageList).ensure(event.stage)
        row.finished(event.summary, event.seconds)

    def _on_finding(self, event: events.FindingEmitted) -> None:
        self._append(EmittedFinding(event, repo=self.app.session.options.repo))

    def _on_dropped(self, event: events.FindingDropped) -> None:
        self._append(DroppedFinding(event))

    def _on_resolved(self, event: events.EvidenceResolved) -> None:
        # A lookup that succeeds is not news; only a failure is shown, and the
        # `FindingDropped` that follows says which claim it cost.
        if event.resolved:
            return
        # Labelled as a lookup, because that is the whole point: no model
        # decided this. Stage D asked the provider for the record and there
        # was not one. The drop that follows says what it cost.
        text = Text()
        text.append("lookup  ", style=theme.DIM)
        text.append(event.evidence_id, style=f"{theme.DROP} strike")
        text.append("  not found", style=theme.DROP)
        self._append(Line(text, classes="finding"))

    def _on_usage(self, event: events.UsageUpdated) -> None:
        # Spend belongs in the chrome, not the stream: it is a running total,
        # not something that happened.
        #
        # Never shown during a replay. `ReplayModel` reports the token counts
        # the *original* run recorded, which price out to a real number — and a
        # dollar figure on a run that called nothing would say you had just
        # spent money you did not spend. The event still carries the counts for
        # anything that wants them; this screen declines to render them as cost.
        if self.app.session.options.replay:
            return
        if not event.input_tokens and not event.output_tokens:
            return
        self._spend = (
            f"{event.input_tokens:,} in / {event.output_tokens:,} out   "
            f"${event.cost_usd:.4f}"
        )
        self._paint_chrome()

    def _on_retry(self, event: events.Retry) -> None:
        self._append(
            Line(
                Text(
                    f"retrying {event.stage} (attempt {event.attempt}) {event.reason}",
                    style=theme.DIM,
                ),
                classes="finding",
            )
        )

    def _on_failed(self, event: events.RunFailed) -> None:
        self._append(Line(Text(event.error, style=theme.DROP), classes="finding"))

    def _on_finished(self, event: events.RunFinished) -> None:
        self._append(
            Line(
                Text("done — press a for the assessment", style=theme.DIM),
                classes="finding",
            )
        )

    # ─── actions ────────────────────────────────────────────────────────────

    def action_assessment(self) -> None:
        if self.app.session.assessment is not None:
            self.app.push_screen("assessment")

    def action_quit(self) -> None:
        self.app.exit()


#: Event type → renderer. The registry is the extension point: a new event class
#: is a new entry, and nothing here needs restructuring to accept it.
HANDLERS: dict[type, Callable] = {
    events.RunStarted: LiveScreen._on_run_started,
    events.EvidenceLoaded: LiveScreen._on_evidence_loaded,
    events.StageStarted: LiveScreen._on_stage_started,
    events.StageFinished: LiveScreen._on_stage_finished,
    events.FindingEmitted: LiveScreen._on_finding,
    events.FindingDropped: LiveScreen._on_dropped,
    events.EvidenceResolved: LiveScreen._on_resolved,
    events.UsageUpdated: LiveScreen._on_usage,
    events.Retry: LiveScreen._on_retry,
    events.RunFailed: LiveScreen._on_failed,
    events.RunFinished: LiveScreen._on_finished,
    # `ToolResponse` carries the raw payload for future use and is deliberately
    # not rendered: the findings read off it are shown instead, and printing
    # both would be the log spew this view exists to avoid.
    events.ToolResponse: lambda self, event: None,
}
