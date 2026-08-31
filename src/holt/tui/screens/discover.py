"""Finding a repository when you do not have one in mind.

The rest of the interface assumes you can name what you want assessed. Often you
cannot — that is the actual starting position — and this is the screen for it: a
recorded search over a stated profile, screened for free, with every candidate
still on the page and the cut ones carrying their reason.

Two things it will not do:

* **Hide what it rejected.** Nine of twenty-five candidates being cut for free
  is the interesting result, not an implementation detail. They stay listed.
* **Reorder survivors.** Screening says a candidate is worth a closer look; it
  does not say one is better than another, and sorting them would assert that it
  did. They keep the order the search returned them in.

Pressing enter on a row assesses it through the ordinary run path, so there is
no second way of running a stage hiding behind this screen.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.tui import animation, discovery, session as session_module, theme
from holt.tui.visual import Line
from holt.tui.widgets.candidates import CandidateList

HINT = "enter assess this one    ctrl+o change what you are looking for    esc back"


class DiscoverScreen(Screen):
    BINDINGS = [
        ("ctrl+o", "profile", "change what you want"),
        ("escape", "home", "home"),
        ("q", "quit", "quit"),
    ]

    def __init__(self, session: str = discovery.DEFAULT_SESSION, **kwargs) -> None:
        super().__init__(**kwargs)
        # Not `self.name`: Textual widgets already own that, and assigning to it
        # raises inside the screen's constructor, where the failure surfaces as
        # a screen that simply never appears.
        self.session_name = session
        self.session: discovery.Session | None = None
        self.error = ""

    def compose(self) -> ComposeResult:
        try:
            self.session = discovery.load(self.session_name)
        except FileNotFoundError:
            self.error = (
                f"No recorded search named {self.session_name!r}. "
                "`holt discover --live --record <name>` makes one."
            )
        except Exception as exc:  # noqa: BLE001 - reported, never a traceback
            self.error = session_module.readable(exc)

        with Horizontal(id="chrome"):
            yield Line("holt · discover", id="chrome-left")
            yield Line(self._provenance(), id="chrome-right")
        yield Line("─" * 240, classes="rule")

        with Vertical(id="discover-body"):
            if self.error:
                yield Line(Text(self.error, style=theme.DROP), classes="empty")
                yield Footer()
                return

            found = self.session
            yield Line(
                Text(f"Looking for {found.profile_description}", style=theme.DIM),
                classes="section-label",
            )
            yield Line(Text(self._counts(), style=theme.FAINT), classes="section-label")
            yield Line(Text(HINT, style=theme.FAINT), id="discover-hint")
            with VerticalScroll(id="candidate-scroll"):
                yield CandidateList(found.rows, id="candidates")
        yield Footer()

    def on_mount(self) -> None:
        if self.error:
            return
        candidates = self.query_one("#candidates", CandidateList)
        for index, row in enumerate(candidates.children):
            animation.reveal(row, delay=animation.stagger(index))
        # The list, not the scroll box around it. Focus landed on the container
        # by default, where ↑↓ scrolled past the candidates and enter did
        # nothing — the only way to assess one was to click it.
        candidates.focus()

    def _counts(self) -> str:
        found = self.session
        if found is None:
            return ""
        total, survived = len(found.rows), len(found.survivors)
        text = (
            f"{total} candidates screened at no model cost · "
            f"{survived} worth a closer look · {total - survived} cut"
        )
        if found.skipped:
            text += f" · {len(found.skipped)} had no recorded evidence"
        return text

    def _provenance(self) -> Text:
        text = Text()
        if self.session is not None:
            text.append(f"{self.session.name}   ", style=theme.FAINT)
            text.append(
                f"recorded {self.session.as_of.date().isoformat()}", style=theme.FAINT
            )
        return text

    # ─── actions ────────────────────────────────────────────────────────────

    def on_list_view_selected(self, event) -> None:
        row = getattr(event.item, "row", None)
        if row is not None:
            self._assess(row)

    def _assess(self, row) -> None:
        """Assess this candidate through the ordinary path.

        Replay when a recording exists — free, and the demo works with no
        credentials. Otherwise live, which the run screen will refuse cleanly if
        the key is missing.
        """
        replay = session_module.has_recording(row.slug)
        options = session_module.RunOptions(
            repo=row.slug, replay=replay, live=not replay
        )
        cached = self.app.store.fresh(
            row.slug, options.mode, options.contributor_days
        )
        if cached is not None:
            self.app.open_stored(cached)
            return
        missing = session_module.missing_credentials(options)
        if missing:
            self.query_one("#discover-hint", Line).update(
                Text(missing[0], style=theme.DROP)
            )
            return
        self.app.start_run(options)

    def action_profile(self) -> None:
        """The profile is what this search was built from, so it is edited here."""
        self.app.push_screen("profile")

    def action_home(self) -> None:
        self.app.go_home()

    def action_quit(self) -> None:
        self.app.exit()
