"""The application shell.

It owns five things and nothing else: the screen registry, the global
keybindings, the store of past assessments, the runs currently in flight, and
the session being looked at. It contains no rendering and no engine knowledge,
so a new view is a new file plus one line in `holt.tui.screens.REGISTRY`.

Navigation is deliberately shallow. Home holds everything you have; a run or a
stored result is one push deep; the evidence behind a claim is two. There is no
state you can get into where the way back is unclear, because every screen binds
escape to the thing above it.

**A run belongs to the app, not to the screen watching it.** The pump that
drains every in-flight session lives here and ticks whether or not anyone is
looking, so walking away from a run leaves it running. It used to live on the
live screen, which meant popping that screen stopped the only thing consuming
the run's events: the worker thread carried on spending, its result was never
absorbed, and the assessment it produced was silently thrown away. A run now
ends for exactly one reason — it finished, it failed, or someone stopped it.
"""

from __future__ import annotations

from textual.app import App

from holt.cli import normalise
from holt.tui import mascot, store, theme
from holt.tui.commands import HoltCommands
from holt.tui.screens import REGISTRY
from holt.tui.screens.assessment import AssessmentScreen
from holt.tui.screens.confirm import ConfirmScreen
from holt.tui.screens.inspector import InspectorScreen
from holt.tui.screens.live import LiveScreen
from holt.tui.session import RunOptions, Session

#: How often the app absorbs what the running sessions have emitted. The same
#: interval the live screen redraws on: the screen renders what this has already
#: collected, so a slower pump here would show as a laggy stream.
PUMP_SECONDS = 0.05


class HoltApp(App):
    CSS = theme.CSS
    SCREENS = REGISTRY
    TITLE = "holt"

    #: One provider, not a union with `App.COMMANDS`. It yields holt's commands
    #: and then the framework's, so the order is written down rather than
    #: decided by set iteration and a race between concurrent providers.
    COMMANDS = {HoltCommands}

    BINDINGS = [
        ("ctrl+c", "quit", "quit"),
    ]

    def __init__(
        self,
        options: RunOptions | None = None,
        assessments: store.Store | None = None,
    ) -> None:
        super().__init__()
        #: Chosen once, at launch, and worn only by the cat and the masthead.
        #: The colours that mean something -- verdict, evidence, drops -- are
        #: fixed in `theme`, so a different accent each session changes how the
        #: interface looks and never what it says.
        self.accent = mascot.pick_accent()
        self.store = assessments or store.Store()
        #: Set when the interface was launched with a repository to assess.
        #: Without one it opens on home, which is the ordinary case.
        self.initial = options
        self.session: Session | None = None
        #: Runs in flight, keyed by repository. One run per repository: asking
        #: for one that is already running reattaches to it rather than paying
        #: twice for the same answer.
        self.runs: dict[str, Session] = {}

    def on_mount(self) -> None:
        self.set_interval(PUMP_SECONDS, self.pump)
        self.push_screen("home")
        if self.initial is not None:
            self.start_run(self.initial)

    # ─── the pump ───────────────────────────────────────────────────────────

    def pump(self) -> None:
        """Absorb what every in-flight run has emitted, and keep its result.

        Runs regardless of which screen is up. A session that has produced an
        outcome is stored and unregistered here — never by a screen, because a
        screen that has been popped cannot store anything.
        """
        for repo, session in list(self.runs.items()):
            session.drain()
            if session.finished:
                self.remember(session)
                self.runs.pop(repo, None)

    @property
    def in_flight(self) -> list[Session]:
        """Runs that are still working, newest last."""
        return [s for s in self.runs.values() if not s.finished]

    def running_for(self, repo: str) -> Session | None:
        return self.runs.get(normalise(repo))

    # ─── navigation ─────────────────────────────────────────────────────────

    def start_run(self, options: RunOptions) -> None:
        """Assess a repository, and watch it happen.

        Reattaches if that repository is already being assessed. Two runs of the
        same repository would produce two answers to one question, and on live
        they would be paid for separately.
        """
        repo = normalise(options.repo)
        existing = self.runs.get(repo)
        if existing is not None:
            self.watch_run(existing)
            return
        session = Session(options)
        self.runs[repo] = session
        self.session = session
        session.start()
        self.push_screen(LiveScreen())

    def watch_run(self, session: Session) -> None:
        """Reopen the live view on a run already in progress.

        The screen rebuilds from the session's log, so a run joined half way
        through shows everything it has done, not only what happens next.
        """
        self.session = session
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
        """Back to the list, however deep the current screen is.

        Leaves any run alone. Escape means "stop looking at this", never "stop
        doing this" — stopping has its own key and its own confirmation.
        """
        # Home sits at index 1, above Textual's own base screen. Popping to
        # exactly that leaves home on top however deep the stack got.
        while len(self.screen_stack) > 2:
            self.pop_screen()
        home = self.screen
        if hasattr(home, "refresh_entries"):
            # Coroutine: scheduled rather than awaited, because the caller is a
            # key binding and the list catching up a frame later is invisible.
            home.call_later(home.refresh_entries)

    # ─── stopping ───────────────────────────────────────────────────────────

    def confirm_stop(self, session: Session) -> None:
        """Ask before stopping. A stopped run keeps nothing it had computed."""
        if session is None or session.finished:
            return
        self.push_screen(
            ConfirmScreen(
                f"stop {session.options.repo}?",
                _spent(session),
                yes="y stop",
                no="n keep running",
            ),
            lambda confirmed: self._stop(session, bool(confirmed)),
        )

    def _stop(self, session: Session, confirmed: bool) -> None:
        if confirmed:
            session.cancel()

    def action_quit(self) -> None:
        """Quit, but never silently discard a run that is still working."""
        running = self.in_flight
        if not running:
            self.exit()
            return
        detail = "   ".join(f"{s.options.repo} {_spent(s)}" for s in running)
        self.push_screen(
            ConfirmScreen(
                f"{len(running)} run{'s' if len(running) > 1 else ''} still in flight",
                f"{detail}\nquitting stops {'them' if len(running) > 1 else 'it'}.",
                yes="y quit",
                no="n go back",
            ),
            lambda confirmed: self.exit() if confirmed else None,
        )

    # ─── persistence ────────────────────────────────────────────────────────

    def remember(self, session: Session) -> None:
        """Keep a finished assessment so the next launch opens on it."""
        entry = session.to_entry()
        if entry is not None:
            self.store.save(entry)


def _spent(session: Session) -> str:
    """Elapsed, and money if any was actually spent."""
    minutes, seconds = divmod(int(session.duration), 60)
    text = f"{minutes}:{seconds:02d}"
    if session.cost_usd:
        text += f"   ${session.cost_usd:.4f}"
    return text


def run(options: RunOptions | None = None) -> None:
    HoltApp(options).run()
