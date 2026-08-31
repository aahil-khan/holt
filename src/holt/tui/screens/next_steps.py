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
would have answered for immediately. The evidence the report was built from is
tried first and the other source second, so a miss is a miss about the
repository rather than about where we happened to look.

**The read happens off the screen's own message pump.** Reading evidence takes
a thread and, on a live repository, a minute; awaiting it inside the submit
handler meant the screen answered no keys at all until it came back. It runs as
a worker, so the notice moves, escape still works, and pressing enter again
replaces the ranking in flight.

The ranking is `progression.path_overlap_rank`: deterministic, no model call.
Each row shows the tokens that put it there, so the order is inspectable rather
than asserted — the same standard the rest of the interface holds evidence to.
And it carries `NEXT_MEASUREMENT` whenever it shows an order, because a ranking
shown without the number saying how well it works is the overclaim this project
exists to avoid — `holt next` on the command line has always printed it.
"""

from __future__ import annotations

import asyncio

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Input

from holt.agent.progression import NEXT_MEASUREMENT
from holt.tui import animation, discovery, theme
from holt.tui.visual import Line
from holt.tui.widgets.evidence import cite

TOP = 10


class _NoEvidence(Exception):
    """Nothing to read, from either source. Carries the sentence to show."""



class NextScreen(Screen):
    BINDINGS = [
        ("escape", "back", "back"),
        ("q", "quit", "quit"),
    ]

    def __init__(self, repo: str, live: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.repo = repo
        #: How the report this was opened from read its evidence. The ranking
        #: starts from the same place rather than assuming a recording exists.
        self.live = live

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Line("holt · what next", id="chrome-left")
            yield Line(Text(self.repo, style=theme.FAINT), id="chrome-right")
        yield Line("─" * 240, classes="rule")

        with Vertical(id="next-body"):
            yield Line(
                Text(
                    "Whose next issues?  A GitHub username — yours, or anyone "
                    "who has had work merged here.",
                    style=theme.DIM,
                ),
                classes="section-label",
            )
            yield Input(
                placeholder="GitHub username, e.g. frenck — enter to rank",
                id="login-input",
            )
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
        """Which evidence to try, best first.

        The report was built from one of these and the ranking should read the
        same thing. The other is tried afterwards because a committed fixture
        and a live fetch answer the same question about the same repository —
        stopping at the first miss is what made this screen claim there was
        nothing to rank from about repositories GitHub knows all about.

        Live is dropped from the list without a token rather than attempted and
        reported as a failure, which would name the wrong problem.
        """
        return [
            mode
            for mode in (self.live, not self.live)
            if not mode or discovery.missing_token() is None
        ]

    async def _fetch(self, make_provider, missing: str):
        """Evidence for this repo, from the first source that has it.

        The fetch runs off the event loop: a live read is a network round trip
        and the interface must not freeze for the length of one.
        """
        from holt.tui import session as session_module

        failures: list[str] = []
        for live in self._sources():
            self._notice(
                "reading GitHub…" if live else "reading committed evidence…"
            )
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
            return records, live
        raise _NoEvidence(self._nothing_to_read(missing, failures))

    def _nothing_to_read(self, missing: str, failures: list[str]) -> str:
        """Why there is nothing, naming the thing that would fix it."""
        token = discovery.missing_token()
        if token:
            return (
                f"No committed {missing} for {self.repo}, and reading GitHub "
                "needs GITHUB_TOKEN — export a token, or put it in .env, and "
                "try again."
            )
        detail = f" ({failures[-1]})" if failures else ""
        return (
            f"No {missing} for {self.repo}, from the recording or from "
            f"GitHub{detail}, so there is nothing to rank from."
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Start the ranking. Deliberately not `async`, and deliberately not
        awaited.

        A message handler owns the screen's message pump for as long as it
        runs, and this one runs for as long as the evidence takes to read —
        which on a live repository is a minute of network. Awaiting it here
        meant the screen took no keys at all in the meantime: no escape, no
        typing, nothing. The work moves to a worker so the screen keeps
        answering while it happens, and pressing enter again replaces the
        ranking in flight rather than queueing a second one behind it.
        """
        login = event.value.strip().lstrip("@")
        if not login:
            return
        self.run_worker(self._rank(login), group="rank", exclusive=True)

    async def _rank(self, login: str) -> None:
        from holt.agent import progression
        from holt.agent.signals import build_threads
        from holt.issues import open_at_cutoff
        from holt.tui import session as session_module

        results = self.query_one("#next-results", VerticalScroll)
        await results.remove_children()
        self._measurement()

        try:
            records, from_live = await self._fetch(
                session_module._provider, "evidence"
            )
        except _NoEvidence as miss:
            self._notice(str(miss), theme.DROP)
            return

        # Off the loop for the same reason the fetch is: on a large repository
        # this is a second of work, and a second of dropped frames reads as the
        # interface having stopped.
        contributor = await asyncio.to_thread(
            lambda: progression.history_for(login, build_threads(records))
        )
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
            issues, issues_live = await self._fetch(
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

        ranked = await asyncio.to_thread(
            progression.path_overlap_rank, contributor.files, candidates
        )
        read = "read live from GitHub" if from_live and issues_live else (
            "read from committed evidence" if not (from_live or issues_live)
            else "read from both live and committed evidence"
        )
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

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()


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
