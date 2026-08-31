"""Where someone who has already landed work here might look next.

Reached from a report, because it answers the question that comes *after*
"is this worth my time". It needs a login, and it needs that login to have merged
something in the evidence — without a merge there is no set of touched paths and
the ranking has nothing to work from. That is stated when it happens rather than
producing an empty list.

**It reads what the report read.** This screen used to fetch from the committed
fixtures and nothing else, whatever mode the run had been in. Assess a repository
live — which is what the finder now hands you — press `n`, and it answered "no
committed evidence, so there is nothing to rank from" about a repository GitHub
would have answered for immediately. So the evidence the report was built from
is tried first, and a miss is a miss about the repository rather than about
where we happened to look.

**A live report is not answered from fixtures behind your back.** The fix above
went one step too far: when GitHub had nothing, the ranking silently fell
through to a recording taken before the holdout and mentioned it in a sentence
under an order that was already on screen. The order looked live. So the
fallback in that direction is now something you press `ctrl+e` for, and until
you do, a live miss reads as a live miss. The fallback the other way — a
replayed report reaching GitHub — is untouched: you already chose the
recording, and that direction moves toward the real repository rather than away
from it.

**Reads are reused for ten minutes, and say when they were.** Trying three
logins against one repository was three round trips to GitHub for the same two
fetches. The same ten minutes a stored assessment stays reusable for, for the
same reason: long enough to cover the way this screen is actually used, short
enough that nobody mistakes it for live data. Every reuse carries its age.

The ranking is `progression.path_overlap_rank`: deterministic, no model call.
Each row shows the tokens that put it there, so the order is inspectable rather
than asserted — the same standard the rest of the interface holds evidence to.
And it carries `NEXT_MEASUREMENT` whenever it shows an order, because a ranking
shown without the number saying how well it works is the overclaim this project
exists to avoid — `holt next` on the command line has always printed it.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Input

from holt.agent.progression import NEXT_MEASUREMENT
from holt.tui import animation, discovery, store, theme
from holt.tui.visual import Line
from holt.tui.widgets.evidence import cite

TOP = 10

#: How long a fetch is reused for. Deliberately the same window a stored
#: assessment is considered fresh for, and imported from there rather than
#: restated, so the interface has one answer to "how old is too old" instead of
#: two that can drift apart.
CACHE_SECONDS = store.DEFAULT_MAX_AGE_SECONDS

#: `(repo, kind, live) -> (read_at, records)`. Module level because the screen
#: is rebuilt every time `n` is pressed, so nothing on the instance survives to
#: the next visit — which is one of the two cases worth caching for.
_CACHE: dict[tuple[str, str, bool], tuple[float, Any]] = {}


def cache_clear() -> None:
    """Forget every reused read. For tests, and for nothing else."""
    _CACHE.clear()


class _NoEvidence(Exception):
    """Nothing to read, from either source. Carries the sentence to show."""



class NextScreen(Screen):
    BINDINGS = [
        ("escape", "back", "back"),
        # `ctrl+e`, not a bare letter: the login box holds focus the whole time
        # a reader would want this, and a printable key never reaches the
        # screen from inside an `Input` — it just types itself into the box.
        Binding("ctrl+e", "use_committed", "use committed evidence"),
        ("q", "quit", "quit"),
    ]

    def __init__(self, repo: str, live: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.repo = repo
        #: How the report this was opened from read its evidence. The ranking
        #: starts from the same place rather than assuming a recording exists.
        self.live = live
        #: Set only by `ctrl+e`. Until it is, a live report is never answered
        #: from the committed fixtures — see `_sources`.
        self.use_committed = False
        #: True while committed evidence is being *offered* rather than used,
        #: which is the only time `ctrl+e` means anything. Drives the footer.
        self._withheld = False
        #: The last login asked about, so `ctrl+e` can re-ask it rather than
        #: making the reader type it again.
        self._login = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt · what next", id="chrome-left")
            yield Line(Text(self.repo, style=theme.FAINT), id="chrome-right")
        yield Line("─" * 240, classes="rule")

        with Vertical(id="next-body"):
            yield Line(
                Text("Whose next issues?", style=theme.DIM), classes="section-label"
            )
            yield Input(placeholder="a GitHub login", id="login-input")
            yield Line(
                Text(
                    "Ranked by overlap with the files they have already had merged "
                    "here. Deterministic, and no model is called.",
                    style=theme.FAINT,
                ),
                id="next-notice",
            )
            # Filled in only when an order is on screen, and never omitted then.
            yield Line("", id="next-measurement")
            with VerticalScroll(id="next-results"):
                yield Line("")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#login-input", Input).focus()

    def _notice(self, message: str, tone: str = "") -> None:
        self.query_one("#next-notice", Line).update(
            Text(message, style=tone or theme.FAINT)
        )

    def _measurement(self, message: str = "") -> None:
        self.query_one("#next-measurement", Line).update(
            Text(message, style=theme.FAINT)
        )

    def _sources(self) -> list[bool]:
        """Which evidence to try, best first. `True` is GitHub, `False` is disk.

        The report was built from one of these and the ranking reads the same
        thing first. What happens on a miss is not symmetric, and deliberately
        so:

        * A **replayed** report falls through to GitHub. You chose the
          recording, and reaching past it goes toward the live repository.
        * A **live** report does *not* fall through to the committed fixtures.
          It used to, silently, and then said so in a sentence underneath a
          ranking already on screen — an order built from evidence recorded
          before the holdout, presented as though GitHub had answered. Reading
          fixtures is a choice, so it takes `ctrl+e`, which sets
          `use_committed` and asks again.

        Live is dropped from the list without a token rather than attempted and
        reported as a failure, which would name the wrong problem.
        """
        sources = [self.live]
        other = not self.live
        # `other` is truthy exactly when the fallback is *toward* GitHub, which
        # needs no permission. The fixture direction needs `ctrl+e`.
        if other or self.use_committed:
            sources.append(other)
        return [
            mode for mode in sources if not mode or discovery.missing_token() is None
        ]

    async def _fetch(self, make_provider, kind: str):
        """Evidence for this repo, from the first source that has it.

        Returns the records, whether they came from GitHub, and how long ago
        they were read — `None` when they were read just now. The age is
        returned rather than swallowed because a reused read is shown with it;
        a cache nobody can see the age of is a cache that lies.

        The fetch runs off the event loop: a live read is a network round trip
        and the interface must not freeze for the length of one.
        """
        from holt.tui import session as session_module

        failures: list[str] = []
        for live in self._sources():
            hit = _cached(self.repo, kind, live)
            if hit is not None:
                age, records = hit
                return records, live, age
            self._notice("reading GitHub…" if live else "reading committed evidence…")
            try:
                records = await asyncio.to_thread(
                    lambda live=live: make_provider(live=live).fetch(self.repo)
                )
            except FileNotFoundError:
                failures.append("nothing recorded")
                continue
            except Exception as exc:  # noqa: BLE001 - reported, never a traceback
                failures.append(session_module.readable(exc))
                continue
            _CACHE[(self.repo, kind, live)] = (time.time(), records)
            return records, live, None
        raise _NoEvidence(self._nothing_to_read(kind, failures))

    def _nothing_to_read(self, missing: str, failures: list[str]) -> str:
        """Why there is nothing, naming the thing that would fix it.

        Sets `_withheld` when the committed fixtures are the thing not tried,
        because that is the only state in which `ctrl+e` does anything, and the
        footer should not advertise a key that would be a no-op.
        """
        token = discovery.missing_token()
        if token:
            return (
                f"No committed {missing} for {self.repo}, and reading GitHub "
                "needs GITHUB_TOKEN — export a token, or put it in .env, and "
                "try again."
            )
        detail = f" ({failures[-1]})" if failures else ""
        if self.live and not self.use_committed:
            # Withheld, not missing. Said as an offer rather than done quietly,
            # which is the whole point of the key existing.
            self._withheld = True
            self.refresh_bindings()
            return (
                f"GitHub has no {missing} for {self.repo}{detail}, so there is "
                "nothing live to rank from. ctrl+e tries the committed evidence "
                "instead — a recording from before the holdout, not this "
                "repository as it is now."
            )
        return (
            f"No {missing} for {self.repo}, from the recording or from "
            f"GitHub{detail}, so there is nothing to rank from."
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        login = event.value.strip().lstrip("@")
        if not login:
            return
        await self._rank(login)

    async def _rank(self, login: str) -> None:
        from holt.agent import progression
        from holt.agent.signals import build_threads
        from holt.issues import open_at_cutoff
        from holt.tui import session as session_module

        results = self.query_one("#next-results", VerticalScroll)
        await results.remove_children()
        self._measurement()
        self._login = login
        # Cleared before every attempt: whether the fixtures are being withheld
        # is a fact about this attempt, not a mode the screen stays in.
        self._withheld = False
        self.refresh_bindings()

        try:
            records, from_live, evidence_age = await self._fetch(
                session_module._provider, "evidence"
            )
        except _NoEvidence as miss:
            self._notice(str(miss), theme.DROP)
            return

        contributor = progression.history_for(login, build_threads(records))
        if not contributor.merged_count:
            # Said plainly, because an empty list would look like a ranking that
            # found nothing rather than a question that cannot be asked yet.
            self._notice(
                f"{login} has no merged pull request here in this evidence, so "
                "there are no touched paths to rank against. The assessment "
                "answers the question that comes before this one.",
                theme.DROP,
            )
            return

        try:
            issues, issues_live, issue_age = await self._fetch(
                session_module._issue_provider, "issue evidence"
            )
        except _NoEvidence as miss:
            self._notice(str(miss), theme.DROP)
            return

        candidates = open_at_cutoff(issues)
        if not candidates:
            self._notice("No issue in this evidence was open at the cutoff.",
                         theme.DROP)
            return

        ranked = progression.path_overlap_rank(contributor.files, candidates)
        read = "read live from GitHub" if from_live and issues_live else (
            "read from committed evidence" if not (from_live or issues_live)
            else "read from both live and committed evidence"
        )
        read += _reuse(evidence_age, issue_age)
        self._notice(
            f"{login} has {contributor.merged_count} merged "
            f"{'PR' if contributor.merged_count == 1 else 'PRs'} here, touching "
            f"{len(contributor.files)} files. "
            f"{sum(1 for _k, toks in ranked if toks)} of {len(ranked)} open issues "
            f"overlap those paths. {read}."
        )
        # Never an order without the number that says how well it works. The
        # command line has always printed this; this screen is the second path
        # that shows a ranking and it was not printing it.
        self._measurement(NEXT_MEASUREMENT)

        for index, (key, tokens) in enumerate(ranked[:TOP], 1):
            record = candidates[key]
            await results.mount(_row(index, key, record, tokens))
            animation.reveal(results.children[-1], delay=animation.stagger(index))

    def check_action(self, action: str, parameters) -> bool | None:
        """Advertise `ctrl+e` only where it does something.

        `None` hides a binding rather than disabling it, which is what a key
        that is not currently a choice should be.
        """
        if action == "use_committed":
            return True if self._withheld else None
        return True

    async def action_use_committed(self) -> None:
        """Rank from the committed evidence after all, having been asked.

        This is the entire gate. Everything about reading fixtures on a live
        report happens because somebody pressed this, and the ranking that
        comes back says which source it came from.
        """
        if not self._withheld or not self._login:
            return
        self.use_committed = True
        await self._rank(self._login)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()


def _cached(repo: str, kind: str, live: bool) -> tuple[float, Any] | None:
    """A read from within the window, and its age. Expired entries are dropped.

    Dropped rather than left to rot: this dict lives for the process, and a
    long session against many repositories would otherwise only ever grow.
    """
    entry = _CACHE.get((repo, kind, live))
    if entry is None:
        return None
    read_at, records = entry
    age = max(0.0, time.time() - read_at)
    if age > CACHE_SECONDS:
        del _CACHE[(repo, kind, live)]
        return None
    return age, records


def _reuse(*ages: float | None) -> str:
    """How the sentence admits to a reused read, or "" when nothing was reused.

    The oldest of them, because that is the age of the claim as a whole — the
    freshest part of a mixed answer is not what it should be dated by.
    """
    known = [age for age in ages if age is not None]
    if not known:
        return ""
    if len(known) < len(ages):
        return f", partly reused from a read {store.describe_age(max(known))}"
    return f", reused from a read {store.describe_age(max(known))}"


def _row(index: int, key: str, record, tokens: set[str]) -> Line:
    title = str(record.payload.get("title", "")).strip()
    text = Text()
    text.append(f"{index}  ", style=theme.FAINT)
    text.append(title[:76] or key)
    text.append("\n     ")
    text.append_text(cite(key, width=44))
    if tokens:
        # Why this row is where it is. An order without a reason is an
        # assertion, and the rest of the interface does not make those.
        text.append("   overlaps ", style=theme.FAINT)
        text.append(", ".join(sorted(tokens)[:4]), style=theme.DIM)
    else:
        text.append("   no path overlap — listed by recency", style=theme.FAINT)
    return Line(text, classes="next-row")
