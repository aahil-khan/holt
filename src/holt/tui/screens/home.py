"""Where the interface opens.

The first question on reopening a tool like this is almost never "assess
something new" — it is "what did it say about the thing I ran earlier". So the
screen leads with an input you can type into immediately, and everything you
have already assessed sits underneath it, readable without spending anything.

Three behaviours worth stating, because they are the ones that make it usable:

* **Typing filters the list.** The same keystrokes that name a new repository
  narrow the ones you already have, so you find out you already assessed it
  instead of paying to learn that.
* **A recent enough answer is reused, and says so.** Pressing enter on a
  repository assessed four minutes ago opens that assessment rather than
  spending a minute and some money reproducing it. Its age is on screen and
  re-running is one key.
* **The mode is visible before you commit.** Replay is free and only works where
  there is a recording; live costs money and reads GitHub. You should never
  discover which one you were in by watching the bill.
"""

from __future__ import annotations

import os

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Input

from holt.cli import normalise
from holt.tui import animation, session as session_module, store, theme
from holt.tui.visual import Line
from holt.tui.widgets.recent import RecentList, RecentRow

#: Shown in the empty state. Must be a repository with a committed recording,
#: because the empty state promises the suggestion costs nothing —
#: `tests/test_tui_screens.py` holds it to that.
SUGGESTION = "home-assistant/core"

#: The standing hint under the input. Present by default rather than only in the
#: footer, because the question this screen has to answer immediately is "what
#: do I press", and a keybinding you have to go looking for is one you do not
#: know about.
HINT = (
    "⏎ assess    ↑↓ one you already have    ctrl+f find one    "
    "ctrl+t mode    ctrl+r re-run"
)


class HomeScreen(Screen):
    # Every key here has to survive a focused `Input`, which is where the
    # cursor sits the whole time. `ctrl+d` is the input's own delete, `ctrl+p`
    # is Textual's command palette, and a bare `q` never arrives at all — all
    # three would have been keys the footer advertised and nothing did.
    BINDINGS = [
        ("ctrl+f", "discover", "find a repository"),
        ("ctrl+o", "profile", "profile"),
        ("ctrl+r", "rerun", "re-run"),
        ("ctrl+t", "toggle_mode", "mode"),
        ("escape", "clear", "clear"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Live where it is possible, because that is what assessing a new
        # repository means. Falls back to replay so the interface is still
        # useful, and still honest about it, with no credentials at all.
        self.mode = "live" if os.environ.get("OPENAI_API_KEY") else "replay"
        self._entries: list = []
        self._notice = ""

    # ─── layout ─────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt", id="chrome-left")
            yield Line("", id="chrome-right")
        yield Line("─" * 240, classes="rule")

        with Vertical(id="home-body"):
            yield Line(
                Text("Assess a repository", style=theme.DIM), classes="section-label"
            )
            yield Input(
                placeholder="owner/name, or a github.com URL",
                id="repo-input",
            )
            yield Line(Text(HINT, style=theme.FAINT), id="home-notice")
            yield Line(Text("RECENT", style=theme.DIM), classes="section-label")
            yield Line("", id="home-empty", classes="empty")
            with VerticalScroll(id="recent-scroll"):
                yield RecentList([], id="recent")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_entries()
        self.query_one("#repo-input", Input).focus()
        self._paint_chrome()

    # ─── state ──────────────────────────────────────────────────────────────

    async def refresh_entries(self, filter_text: str = "") -> None:
        """Rebuild the recent list, optionally narrowed by what is typed.

        The list is emptied and refilled rather than replaced, because two
        widgets cannot share an id and the removal of the old one does not
        complete before the new one mounts.
        """
        needle = filter_text.strip().lower()
        entries = [
            e for e in self.app.store.all() if not needle or needle in e.repo.lower()
        ]
        self._entries = entries

        listing = self.query_one("#recent", RecentList)
        await listing.clear()
        listing.entries = entries
        for index, stored in enumerate(entries):
            row = RecentRow(stored)
            await listing.append(row)
            animation.reveal(row, delay=animation.stagger(index))

        self._paint_empty(entries, bool(needle))
        self._paint_chrome()

    def _paint_empty(self, entries: list, filtered: bool) -> None:
        widget = self.query_one("#home-empty", Line)
        if entries:
            widget.update("")
            widget.display = False
            return
        widget.display = True
        if filtered:
            message = "Nothing assessed matches that. Press enter to assess it."
        else:
            message = (
                f"Nothing assessed yet. Type a repository above — {SUGGESTION} has a "
                "recording, so it costs nothing — and press enter."
            )
        widget.update(Text(message, style=theme.FAINT))
        animation.reveal(widget)

    def _paint_chrome(self) -> None:
        count = len(self._entries)
        left = "holt"
        right = Text()
        if count:
            right.append(f"{count} assessed   ", style=theme.FAINT)
        right.append(self.mode, style=theme.DIM)
        self.query_one("#chrome-left", Line).update(Text(left, style=theme.DIM))
        self.query_one("#chrome-right", Line).update(right)

    def notice(self, message: str, tone: str = "") -> None:
        """One line under the input.

        Clearing it restores the hint rather than leaving a gap: the space is
        there either way, and an empty line teaches nobody anything.
        """
        self._notice = message
        widget = self.query_one("#home-notice", Line)
        widget.update(Text(message or HINT, style=tone or theme.FAINT))
        animation.reveal(widget)

    # ─── input ──────────────────────────────────────────────────────────────

    async def on_input_changed(self, event: Input.Changed) -> None:
        await self.refresh_entries(event.value)
        if self._notice:
            # Typing clears a complaint about what was typed before it.
            self.notice("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        typed = event.value.strip()
        if not typed:
            # Enter on an empty box opens the highlighted recent, if there is
            # one. Doing nothing at all would read as the key not working.
            selected = self.query_one("#recent", RecentList).selected
            if selected is not None:
                self.app.open_stored(selected)
            return
        self.run_repo(typed)

    def on_list_view_selected(self, event) -> None:
        entry = getattr(event.item, "entry", None)
        if entry is not None:
            self.app.open_stored(entry)

    # ─── actions ────────────────────────────────────────────────────────────

    def run_repo(self, typed: str, force: bool = False) -> None:
        """Assess a repository, or open a recent enough answer for it."""
        repo = normalise(typed)
        if not _looks_like_repo(repo):
            self.notice(
                f"“{typed}” is not an owner/name or a github.com URL.", theme.DROP
            )
            return

        options = session_module.RunOptions(
            repo=repo, replay=self.mode == "replay", live=self.mode == "live"
        )

        missing = session_module.missing_credentials(options)
        if missing:
            self.notice(missing[0], theme.DROP)
            return

        if options.replay and not session_module.has_recording(repo):
            self.notice(
                f"No recording for {repo}. Press ctrl+t to switch to live.", theme.DROP
            )
            return

        if not force:
            cached = self.app.store.fresh(repo, options.mode, options.contributor_days)
            if cached is not None:
                self.app.open_stored(cached)
                return

        self.app.start_run(options)

    def action_rerun(self) -> None:
        """Assess again, ignoring anything stored."""
        typed = self.query_one("#repo-input", Input).value.strip()
        if typed:
            self.run_repo(typed, force=True)
            return
        selected = self.query_one("#recent", RecentList).selected
        if selected is not None:
            self.run_repo(selected.repo, force=True)

    def action_discover(self) -> None:
        """For when you cannot name a repository, which is the usual case."""
        self.app.push_screen("discover")

    def action_profile(self) -> None:
        self.app.push_screen("profile")

    def action_toggle_mode(self) -> None:
        self.mode = "replay" if self.mode == "live" else "live"
        self._paint_chrome()
        self.notice(
            "replay reads a committed recording: free, and only where one exists."
            if self.mode == "replay"
            else "live reads GitHub and calls a model. Costs a few cents per run."
        )

    def action_clear(self) -> None:
        box = self.query_one("#repo-input", Input)
        box.value = ""
        box.focus()
        self.notice("")

    def action_quit(self) -> None:
        self.app.exit()


def _looks_like_repo(repo: str) -> bool:
    """`owner/name`, and nothing sillier.

    Catches the paste that went wrong before it becomes a network error with a
    worse message: an empty box, a bare word, a URL to something that is not a
    repository.
    """
    parts = repo.split("/")
    if len(parts) != 2:
        return False
    return all(part and not part.isspace() for part in parts)
