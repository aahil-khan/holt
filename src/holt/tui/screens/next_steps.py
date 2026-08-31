"""Where someone who has already landed work here might look next.

Reached from a report, because it answers the question that comes *after*
"is this worth my time". It needs a login, and it needs that login to have merged
something in the evidence — without a merge there is no set of touched paths and
the ranking has nothing to work from. That is stated when it happens rather than
producing an empty list.

The ranking is `progression.path_overlap_rank`: deterministic, no model call.
Each row shows the tokens that put it there, so the order is inspectable rather
than asserted — the same standard the rest of the interface holds evidence to.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Input

from holt.tui import animation, theme
from holt.tui.visual import Line
from holt.tui.widgets.evidence import cite

TOP = 10


class NextScreen(Screen):
    BINDINGS = [
        ("escape", "back", "back"),
        ("q", "quit", "quit"),
    ]

    def __init__(self, repo: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.repo = repo

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
            with VerticalScroll(id="next-results"):
                yield Line("")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#login-input", Input).focus()

    def _notice(self, message: str, tone: str = "") -> None:
        self.query_one("#next-notice", Line).update(
            Text(message, style=tone or theme.FAINT)
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

        try:
            records = session_module._provider(live=False).fetch(self.repo)
        except FileNotFoundError:
            self._notice(
                f"No committed evidence for {self.repo}, so there is nothing to "
                "rank from.",
                theme.DROP,
            )
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
            issues = session_module._issue_provider(live=False).fetch(self.repo)
        except FileNotFoundError:
            self._notice(f"No issue evidence for {self.repo}; nothing to rank.",
                         theme.DROP)
            return

        candidates = open_at_cutoff(issues)
        if not candidates:
            self._notice("No issue in this evidence was open at the cutoff.",
                         theme.DROP)
            return

        ranked = progression.path_overlap_rank(contributor.files, candidates)
        self._notice(
            f"{login} has {contributor.merged_count} merged "
            f"{'PR' if contributor.merged_count == 1 else 'PRs'} here, touching "
            f"{len(contributor.files)} files. "
            f"{sum(1 for _k, toks in ranked if toks)} of {len(ranked)} open issues "
            "overlap those paths."
        )

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
