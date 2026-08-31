"""Where the interface opens.

The first question on reopening a tool like this is almost never "assess
something new" — it is "what did it say about the thing I ran earlier". So the
screen leads with an input you can type into immediately, and everything you
have already assessed sits underneath it, readable without spending anything.

Three behaviours worth stating, because they are the ones that make it usable:

* **Typing filters the list.** The same keystrokes that name a new repository
  narrow the ones you already have, so you find out you already assessed it
  instead of paying to learn that. What you typed is normalised before it is
  matched, so a pasted `github.com` URL finds the same row `owner/name` does —
  they are the same repository and the list must not claim otherwise.
* **A recent enough answer is reused, and says so.** Pressing enter on a
  repository assessed four minutes ago opens that assessment rather than
  spending a minute and some money reproducing it. Its age is on screen and
  re-running is one key.
* **The mode is visible before you commit.** Replay is free and only works where
  there is a recording; live costs money and reads GitHub. You should never
  discover which one you were in by watching the bill.
* **Everything here is reachable from the keyboard.** The input holds focus the
  whole time — that is where you type — so ↑↓ are handled by the screen and
  move the highlight through the recent list underneath it. Nothing on this
  screen requires a mouse, and nothing requires guessing that tab exists.
"""

from __future__ import annotations

import os

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Input

from holt.cli import normalise
from holt.tui import animation, session as session_module, store, theme
from holt.tui.visual import Line
from holt.tui.widgets.masthead import Masthead
from holt.tui.widgets.recent import RecentList, RecentRow

#: Shown in the empty state. Must be a repository with a committed recording,
#: because the empty state promises the suggestion costs nothing —
#: `tests/test_tui_screens.py` holds it to that.
SUGGESTION = "home-assistant/core"

#: The standing hint under the input. Present by default rather than only in the
#: footer, because the question this screen has to answer immediately is "what
#: do I press", and a keybinding you have to go looking for is one you do not
#: know about.
#: `enter` spelled out rather than ⏎: the glyph renders as a box or as the
#: wrong arrow in several terminal fonts, and a hint nobody can read is worse
#: than one that takes five more columns.
HINT = (
    "enter assess    ↑↓ one you already have    ctrl+f find one    "
    "ctrl+t mode    ctrl+l models"
)


class HomeScreen(Screen):
    # Every key here has to survive a focused `Input`, which is where the
    # cursor sits the whole time. `ctrl+d` is the input's own delete, `ctrl+p`
    # is Textual's command palette, and a bare `q` never arrives at all — all
    # three would have been keys the footer advertised and nothing did.
    BINDINGS = [
        # ↑↓ are handled here rather than by the list, because the list never
        # holds focus — the input does, so that typing keeps working while you
        # are looking through what you already have. Hidden from the footer:
        # the hint under the input already says it, and two arrow rows would
        # crowd out the keys that are not otherwise discoverable.
        Binding("down", "browse_down", "recent", show=False),
        Binding("up", "browse_up", "recent", show=False),
        ("ctrl+f", "discover", "find a repository"),
        ("ctrl+o", "profile", "profile"),
        ("ctrl+l", "models", "models"),
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
        #: True once ↑↓ has moved the highlight, false again as soon as anything
        #: is typed. It is the whole of what enter means on this screen: in the
        #: box, enter assesses what you wrote; in the list, enter opens the
        #: assessment you highlighted. Without it, arrowing to a row and
        #: pressing enter would run the text still sitting in the box.
        self._browsing = False

    # ─── layout ─────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt", id="chrome-left")
            yield Line("", id="chrome-right")
        yield Line("─" * 240, classes="rule")

        with Vertical(id="home-body"):
            yield Masthead()
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

        The needle is `normalise`d first. Pasting a repository's URL is the
        commonest way of naming one, and matching the raw text meant a URL
        filtered the list to nothing and then announced "nothing assessed
        matches that" about a repository sitting in the store — while enter on
        the same text opened the stored answer. Both cannot be right.
        """
        needle = normalise(filter_text).lower()
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

        # Something is always highlighted when there is something to highlight.
        # A list with no highlight has no keyboard position to move from, which
        # is what made the mouse the only way into it.
        listing.index = 0 if entries else None

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
        # Typing puts you back in the box, and clears any complaint about what
        # was typed before it.
        self._browsing = False
        self._describe_typed(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        selected = self.query_one("#recent", RecentList).selected
        if self._browsing and selected is not None:
            # ↑↓ moved the highlight, so enter belongs to the list.
            self.app.open_stored(selected)
            return

        typed = event.value.strip()
        if not typed:
            # Enter on an empty box opens the highlighted recent, if there is
            # one. Doing nothing at all would read as the key not working.
            if selected is not None:
                self.app.open_stored(selected)
            return
        self.run_repo(typed)

    def on_list_view_selected(self, event) -> None:
        entry = getattr(event.item, "entry", None)
        if entry is not None:
            self.app.open_stored(entry)

    # ─── moving through what you already have ───────────────────────────────

    def action_browse_down(self) -> None:
        self._browse(1)

    def action_browse_up(self) -> None:
        self._browse(-1)

    def _browse(self, delta: int) -> None:
        """Move the highlight without taking focus off the input."""
        listing = self.query_one("#recent", RecentList)
        total = len(self._entries)
        if not total:
            return
        current = listing.index
        if current is None:
            index = 0 if delta > 0 else total - 1
        else:
            index = max(0, min(total - 1, current + delta))
        listing.index = index
        self._browsing = True
        self._describe_highlighted()

    def _describe_highlighted(self) -> None:
        """Say what enter will do now, since it no longer means what it did.

        Once ↑↓ has moved the highlight, enter opens a stored assessment rather
        than assessing whatever is in the box. That is a change of meaning, and
        an interface that changes what a key does without saying so is one you
        have to learn by being surprised.
        """
        entry = self.query_one("#recent", RecentList).selected
        if entry is None:
            return
        age = store.describe_age(entry.age_seconds)
        self.notice(
            f"enter opens {entry.repo} — assessed {age}, {entry.mode}.    "
            "ctrl+r assesses it again    esc back to the box"
        )

    def _describe_typed(self, typed: str) -> None:
        """Whether what is in the box is something already assessed.

        The filtered list shows the row, but a row in a list is easy to read as
        "something like this exists" rather than "this exact thing exists and
        enter will hand it back to you free". So it is said in words, and it is
        said accurately: only a stored answer this mode can actually reuse is
        described as one enter will open.
        """
        repo = normalise(typed)
        match = next((e for e in self._entries if e.repo == repo), None)
        if match is None:
            self.notice("")
            return
        age = store.describe_age(match.age_seconds)
        reusable = self.app.store.fresh(repo, self.mode, match.contributor_days)
        if reusable is not None:
            self.notice(
                f"Already assessed {age} ({match.mode}). "
                "enter opens that answer rather than paying for it again; "
                "ctrl+r assesses it again."
            )
        else:
            # Present in history but too old to reuse, or stored under the other
            # mode. Enter will genuinely run something, and says so.
            self.notice(
                f"Assessed {age} ({match.mode}) — too old to reuse in {self.mode}. "
                "enter assesses it again; ↑↓ then enter re-opens what you have."
            )

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
        selected = self.query_one("#recent", RecentList).selected
        if self._browsing and selected is not None:
            # The highlight is what you are looking at, so it is what ctrl+r
            # acts on — the same thing enter would open.
            self.run_repo(selected.repo, force=True)
            return
        typed = self.query_one("#repo-input", Input).value.strip()
        if typed:
            self.run_repo(typed, force=True)
            return
        if selected is not None:
            self.run_repo(selected.repo, force=True)

    def action_discover(self) -> None:
        """For when you cannot name a repository, which is the usual case."""
        self.app.push_screen("discover")

    def action_profile(self) -> None:
        self.app.push_screen("profile")

    def action_models(self) -> None:
        """Which model answers, and whether it can be reached."""
        self.app.push_screen("models")

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
        self._browsing = False
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
