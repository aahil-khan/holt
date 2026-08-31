"""Watching the pipeline work.

The screen owns no engine knowledge. It drains a `Session`'s event queue and
renders what arrives, dispatching on event type through `HANDLERS` — a dict, not
a chain of branches. Adding an event to the schema means adding an entry here;
an event with no entry still renders, as a dim line, because a screen that
raises on an unfamiliar event is a screen that breaks every time a stage learns
something new.

The screen watches; it does not own. The events are drained by the app, which
ticks whether or not this screen exists, and rendered here from the session's
log. Two things follow. Leaving does not stop the run — escape means "stop
looking", and stopping has its own key and its own confirmation. And coming
back replays the log from the start, so a run rejoined half way through shows
everything it did while nobody was watching.

When a run finishes with this screen up, it moves to the report. A finished run
has nothing left to watch, and making someone press a key to leave a screen that
is done is a small insult repeated every time. Storing the result is the app's
job, not this screen's: a screen that has been popped cannot store anything, and
that is exactly how a completed assessment used to get lost.
"""

from __future__ import annotations

from typing import Callable

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.tui import animation, events, mascot, theme
from holt.tui.visual import Line
from holt.types import T_CUTOFF
from holt.tui.widgets.masthead import Cat
from holt.tui.widgets.stages import DroppedFinding, EmittedFinding, StageList, unknown

POLL_SECONDS = 0.05

#: How long the finished screen stays up before the report replaces it. Long
#: enough to see the last stage land, short enough not to feel like waiting.
HANDOFF_SECONDS = 0.45


def evidence_line(event: events.EvidenceLoaded) -> str:
    """What the run read, and the boundary it actually stopped at.

    The date is the provider's, never a constant written here. T = 2026-06-01
    is an evaluation device: a live run reads through today, and a screen that
    printed T anyway would claim a holdout the run did not apply. Naming the
    holdout only when the cutoff really is T keeps the benchmark's own framing
    where it is true and out of the way where it is not.
    """
    if event.cutoff is None:
        return f"{event.count} evidence records"
    day = event.cutoff.date().isoformat()
    if event.cutoff == T_CUTOFF:
        return f"{event.count} evidence records · holdout window, ≤ {day}"
    return f"{event.count} evidence records · read through {day}"


class LiveScreen(Screen):
    BINDINGS = [
        # Named "leave running" rather than "home" because that is the fact
        # someone needs at the moment they press it.
        ("escape", "home", "leave running"),
        ("a", "assessment", "report"),
        ("ctrl+x", "stop", "stop"),
        ("q", "quit", "quit"),
    ]

    _spend = ""
    _handed_off = False
    #: How far through the session's log this screen has rendered. Rendering
    #: from the log rather than the queue is what lets a second visit replay a
    #: run from its beginning: the cursor starts at zero on a fresh screen.
    _cursor = 0

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Cat("working", id="cat", classes="chrome-cat")
            yield Line("assessing", id="chrome-left")
            yield Line("", id="chrome-right")
        yield Line("─" * 240, classes="rule")
        yield StageList(id="stages")
        yield VerticalScroll(id="stream")
        yield Line("─" * 240, classes="rule")
        yield Footer()

    def on_mount(self) -> None:
        self._paint_chrome()
        self.set_interval(POLL_SECONDS, self._pump)

    def _paint_chrome(self) -> None:
        options = self.app.session.options
        parts = [options.repo, options.mode]
        if self._spend:
            parts.append(self._spend)
        self.query_one("#chrome-right", Line).update(
            Text("   ".join(parts), style=theme.FAINT)
        )

    # ─── event pump ─────────────────────────────────────────────────────────

    def _pump(self) -> None:
        """Render whatever the app has absorbed since the last tick.

        Never drains the session itself. The app does that for every run at
        once, so this screen can be absent for a minute and still catch up.
        """
        log = self.app.session.log
        pending = log[self._cursor :]
        self._cursor = len(log)
        for event in pending:
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

    def _line(self, text: Text) -> None:
        line = Line(text, classes="finding")
        self._append(line)
        animation.reveal(line)

    # ─── per-event rendering ────────────────────────────────────────────────

    def _on_run_started(self, event: events.RunStarted) -> None:
        return

    def _on_evidence_loaded(self, event: events.EvidenceLoaded) -> None:
        self._line(Text(evidence_line(event), style=theme.FAINT))

    def _on_stage_started(self, event: events.StageStarted) -> None:
        self.query_one("#stages", StageList).ensure(event.stage).started(event.model)

    def _on_stage_finished(self, event: events.StageFinished) -> None:
        self.query_one("#stages", StageList).ensure(event.stage).finished(
            event.summary, event.seconds
        )

    def _on_finding(self, event: events.FindingEmitted) -> None:
        self._append(EmittedFinding(event, repo=self.app.session.options.repo))

    def _on_dropped(self, event: events.FindingDropped) -> None:
        # The cat notices. This is the moment the pipeline exists to make, and
        # the mascot reports state or it would not be here at all.
        self._mood("claim_dropped")
        self._append(DroppedFinding(event))

    def _on_resolved(self, event: events.EvidenceResolved) -> None:
        # A lookup that succeeds is not news; only a failure is shown, and the
        # drop that follows says which claim it cost. Labelled as a lookup
        # because that is the whole point: no model decided this. Stage D asked
        # the provider for the record and there was not one.
        if event.resolved:
            return
        text = Text()
        text.append("lookup  ", style=theme.DIM)
        text.append(event.evidence_id, style=f"{theme.DROP} strike")
        text.append("  not found", style=theme.DROP)
        self._line(text)

    def _on_usage(self, event: events.UsageUpdated) -> None:
        # Spend belongs in the chrome, not the stream: it is a running total,
        # not something that happened.
        #
        # Never shown during a replay. `ReplayModel` reports the token counts
        # the *original* run recorded, which price out to a real number, and a
        # dollar figure on a run that called nothing would say you had just
        # spent money you did not spend.
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
        self._line(
            Text(
                f"retrying {event.stage} (attempt {event.attempt}) {event.reason}",
                style=theme.DIM,
            )
        )

    def _mood(self, mood: str) -> None:
        try:
            self.query_one("#cat", Cat).set_mood(mood)
        except Exception:  # noqa: BLE001 - the cat is never load-bearing
            pass

    def _on_failed(self, event: events.RunFailed) -> None:
        # Every spinner stops. A stage left turning after a failure reads as
        # still working, which is the one thing it is definitely not doing.
        self.query_one("#stages", StageList).settle()
        self._line(Text(event.error, style=theme.DROP))
        self._line(Text("escape to go back", style=theme.FAINT))

    def _on_cancelled(self, event: events.RunCancelled) -> None:
        # Not styled as a failure. Nothing went wrong: the run did what it was
        # told. Naming the stages that had finished is the one useful thing to
        # say, because on live those were paid for.
        self.query_one("#stages", StageList).settle()
        self._line(Text("stopped", style=theme.DIM))
        if event.completed_stages:
            done = ", ".join(dict.fromkeys(event.completed_stages))
            self._line(Text(f"completed before stopping: {done}", style=theme.FAINT))
        self._line(Text("escape to go back", style=theme.FAINT))

    def _on_finished(self, event: events.RunFinished) -> None:
        verdict = getattr(event.assessment, "verdict", None)
        self._mood(mascot.mood_for_verdict(getattr(verdict, "value", "")))
        self.query_one("#stages", StageList).settle()
        if self._handed_off:
            return
        self._handed_off = True
        self.set_timer(HANDOFF_SECONDS, self._to_report)

    def _to_report(self) -> None:
        # Only if nobody has navigated away in the meantime.
        if self.app.screen is self:
            self.app.show_assessment()

    # ─── actions ────────────────────────────────────────────────────────────

    def action_assessment(self) -> None:
        self.app.show_assessment()

    def action_home(self) -> None:
        self.app.go_home()

    def action_stop(self) -> None:
        self.app.confirm_stop(self.app.session)

    def action_quit(self) -> None:
        # Through the app, so a run still in flight is named before it dies.
        self.app.action_quit()


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
    events.RunCancelled: LiveScreen._on_cancelled,
    events.RunFinished: LiveScreen._on_finished,
    # `ToolResponse` carries the raw payload for future use and is deliberately
    # not rendered: the findings read off it are shown instead, and printing
    # both would be the log spew this view exists to avoid.
    events.ToolResponse: lambda self, event: None,
}
