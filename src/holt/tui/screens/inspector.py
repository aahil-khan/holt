"""The record behind an evidence id.

Opened from a claim. This is the screen that makes the report checkable: a
reader who does not believe a sentence presses enter on it and reads the record
it was drawn from, with its source, its timestamp and its url.

Resolution goes through the provider the run used, so what is shown here is what
Stage D saw. There are three outcomes and they are three different sentences,
because collapsing them would be a lie in at least one case:

* the record resolved, and is shown
* the id does not resolve, which is why the claim citing it was dropped
* this assessment came out of the store, so no provider is loaded — the id is
  not unresolvable, it simply has not been looked up in this process
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.tui import animation, theme
from holt.tui.visual import Line
from holt.tui.widgets.evidence import EvidenceDetail, cite


class InspectorScreen(Screen):
    BINDINGS = [
        ("escape", "back", "back"),
        ("q", "quit", "quit"),
    ]

    def __init__(
        self, evidence_id: str, record, resolvable: bool = True, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.evidence_id = evidence_id
        self.record = record
        #: False when the session has no provider — a stored assessment. Keeps
        #: the screen from reporting "does not resolve" about an id nobody
        #: asked the provider about.
        self.resolvable = resolvable

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt · evidence", id="chrome-left")
            yield Line(self._status(), id="chrome-right")
        yield Line("─" * 240, classes="rule")
        with VerticalScroll(id="record"):
            if self.record is None and not self.resolvable:
                yield Line(cite(self.evidence_id))
                yield Line("")
                yield Line(
                    Text(
                        "This assessment was reopened from storage, so no evidence "
                        "provider is loaded. Re-run it to read the record behind "
                        "this id.",
                        style=theme.FAINT,
                    ),
                    classes="empty",
                )
            else:
                yield EvidenceDetail(self.record)
        yield Line("─" * 240, classes="rule")
        yield Footer()

    def on_mount(self) -> None:
        animation.reveal(self.query_one("#record", VerticalScroll))

    def _status(self) -> Text:
        if self.record is not None:
            return Text("resolved", style=theme.FAINT)
        if not self.resolvable:
            return Text("not loaded", style=theme.FAINT)
        return Text("does not resolve", style=theme.DROP)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()
