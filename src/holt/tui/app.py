"""The application shell.

It owns four things and nothing else: the screen registry, the global
keybindings, the store of past assessments, and the session currently being
looked at. It contains no rendering and no engine knowledge, so a new view is a
new file plus one line in `holt.tui.screens.REGISTRY`.

Navigation is deliberately shallow. Home holds everything you have; a run or a
stored result is one push deep; the evidence behind a claim is two. There is no
state you can get into where the way back is unclear, because every screen binds
escape to the thing above it.
"""

from __future__ import annotations

from textual.app import App

from holt.tui import store, theme
from holt.tui.screens import REGISTRY
from holt.tui.screens.assessment import AssessmentScreen
from holt.tui.screens.inspector import InspectorScreen
from holt.tui.screens.live import LiveScreen
from holt.tui.session import RunOptions, Session


class HoltApp(App):
    CSS = theme.CSS
    SCREENS = REGISTRY
    TITLE = "holt"

    BINDINGS = [
        ("ctrl+c", "quit", "quit"),
    ]

    def __init__(
        self,
        options: RunOptions | None = None,
        assessments: store.Store | None = None,
    ) -> None:
        super().__init__()
        self.store = assessments or store.Store()
        #: Set when the interface was launched with a repository to assess.
        #: Without one it opens on home, which is the ordinary case.
        self.initial = options
        self.session: Session | None = None

    def on_mount(self) -> None:
        self.push_screen("home")
        if self.initial is not None:
            self.start_run(self.initial)

    # ─── navigation ─────────────────────────────────────────────────────────

    def start_run(self, options: RunOptions) -> None:
        """Assess a repository, and watch it happen."""
        self.session = Session(options)
        self.session.start()
        self.push_screen(LiveScreen())

    def open_stored(self, entry) -> None:
        """Open an assessment that has already been produced. Nothing runs."""
        self.session = Session.restored(entry)
        self.push_screen(AssessmentScreen())

    def show_assessment(self) -> None:
        if self.session is not None and self.session.assessment is not None:
            self.push_screen(AssessmentScreen())

    def inspect(self, evidence_id: str) -> None:
        """Resolve an id and show the record behind it.

        The lookup goes through the provider the run used, so the interface
        cannot show a reader something Stage D did not have access to. A stored
        assessment has no provider, so the screen says the record is no longer
        loaded rather than claiming the id does not resolve — a very different
        statement, and only one of them would be true.
        """
        record = self.session.resolve(evidence_id) if self.session else None
        live = self.session is not None and self.session.provider is not None
        self.push_screen(InspectorScreen(evidence_id, record, resolvable=live))

    def go_home(self) -> None:
        """Back to the list, however deep the current screen is."""
        # Home sits at index 1, above Textual's own base screen. Popping to
        # exactly that leaves home on top however deep the stack got.
        while len(self.screen_stack) > 2:
            self.pop_screen()
        home = self.screen
        if hasattr(home, "refresh_entries"):
            # Coroutine: scheduled rather than awaited, because the caller is a
            # key binding and the list catching up a frame later is invisible.
            home.call_later(home.refresh_entries)

    # ─── persistence ────────────────────────────────────────────────────────

    def remember(self, session: Session) -> None:
        """Keep a finished assessment so the next launch opens on it."""
        entry = session.to_entry()
        if entry is not None:
            self.store.save(entry)


def run(options: RunOptions | None = None) -> None:
    HoltApp(options).run()
