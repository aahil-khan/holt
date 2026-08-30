"""The application shell.

It owns three things and nothing else: the screen registry, the global
keybindings, and the `Session` every screen reads. It contains no rendering and
no engine knowledge, so a new view never requires touching it beyond one line in
`holt.tui.screens.REGISTRY`.
"""

from __future__ import annotations

from textual.app import App

from holt.tui import theme
from holt.tui.screens import REGISTRY
from holt.tui.screens.inspector import InspectorScreen
from holt.tui.session import RunOptions, Session


class HoltApp(App):
    CSS = theme.CSS
    SCREENS = REGISTRY
    TITLE = "holt"

    BINDINGS = [
        ("ctrl+c", "quit", "quit"),
    ]

    def __init__(self, options: RunOptions) -> None:
        super().__init__()
        self.session = Session(options)

    def on_mount(self) -> None:
        self.session.start()
        self.push_screen("live")

    def inspect(self, evidence_id: str) -> None:
        """Resolve an id and show the record behind it.

        The lookup goes through the provider the run used, so the interface
        cannot show a reader something Stage D did not have access to. A failed
        lookup opens the screen anyway and says so.
        """
        self.push_screen(InspectorScreen(evidence_id, self.session.resolve(evidence_id)))


def run(options: RunOptions) -> None:
    HoltApp(options).run()
