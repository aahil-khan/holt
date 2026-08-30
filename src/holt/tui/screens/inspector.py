"""The record behind an evidence id.

Opened from a claim. This is the screen that makes the report checkable: a
reader who does not believe a sentence presses enter on it and reads the record
it was drawn from, with its source, its timestamp and its url.

Resolution goes through the provider, so what is shown here is what Stage D saw.
An id that does not resolve says so plainly rather than showing an empty pane.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.tui import theme
from holt.tui.widgets.evidence import EvidenceDetail
from holt.tui.visual import Line


class InspectorScreen(Screen):
    BINDINGS = [
        ("escape", "back", "back"),
        ("q", "quit", "quit"),
    ]

    def __init__(self, evidence_id: str, record, **kwargs) -> None:
        super().__init__(**kwargs)
        self.evidence_id = evidence_id
        self.record = record

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt · evidence", id="chrome-left")
            yield Line(
                Text(
                    "resolved" if self.record is not None else "does not resolve",
                    style=theme.FAINT if self.record is not None else theme.DROP,
                ),
                id="chrome-right",
            )
        yield Line("─" * 200, classes="rule")
        with VerticalScroll():
            yield EvidenceDetail(self.record)
        yield Line("─" * 200, classes="rule")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()
