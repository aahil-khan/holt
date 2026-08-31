"""The finished report, navigable.

The order is the engine's own: the answer, then the one-paragraph reason, then
what the evidence showed, then which rule decided it, then what could not be
determined, then where work actually landed, then the claims. That order is not
a layout preference — `Assessment.render()` uses it, and a reader who has seen
the markdown should find the same argument in the same sequence here.

Two things this screen refuses to do:

* **Bury what could not be determined.** It is a section with a heading, in the
  same type as everything else, in the position the engine puts it. A tool that
  hides its own limits into a footnote is doing something different from one
  that states them.
* **Let a stored assessment pass as a fresh one.** If this came out of the
  store, the age is in the chrome and re-running is one key.

Every field beyond `repo`, `verdict`, `summary` and `claims` is read through
`getattr` with a default. Those four are the contract; the rest the engine has
added over time, and a screen that hard-required them would break the next time
one moved.
"""

from __future__ import annotations

import textwrap

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.report import VERDICT_HEADLINES
from holt.tui import animation, mascot, store, theme
from holt.tui.visual import Line
from holt.tui.widgets.claims import ClaimList
from holt.tui.widgets.disclosure import EntryPointRow, MeasuredResult
from holt.tui.widgets.masthead import Cat


class AssessmentScreen(Screen):
    BINDINGS = [
        ("escape", "home", "home"),
        ("enter", "inspect", "open evidence"),
        ("ctrl+r", "rerun", "re-run"),
        ("n", "next", "what next"),
        ("t", "trace", "trace"),
        ("q", "quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        session = self.app.session
        assessment = session.assessment
        verdict = assessment.verdict

        with Horizontal(id="chrome"):
            yield Cat(
                mascot.mood_for_verdict(verdict.value), id="cat", classes="chrome-cat"
            )
            yield Line("", id="chrome-left")
            yield Line(self._provenance(), id="chrome-right")
        yield Line("─" * 240, classes="rule")

        with VerticalScroll(id="report"):
            # The answer, in the engine's own words, at the size of a headline.
            yield Line(
                Text(_headline(verdict), style=theme.verdict_colour(verdict.value)),
                id="verdict",
            )
            days = getattr(assessment, "contributor_days", 7)
            yield Line(
                Text(
                    f"for a contributor with {days} day{'' if days == 1 else 's'}",
                    style=theme.FAINT,
                ),
                id="verdict-budget",
            )

            bottom_line = getattr(assessment, "bottom_line", "")
            if bottom_line:
                yield Line(bottom_line, id="bottom-line")

            if assessment.summary:
                yield from _section("WHAT THE EVIDENCE SHOWS", assessment.summary)

            rules = getattr(assessment, "rules", None)
            if rules:
                # The deterministic half, shown rather than described. This is
                # what `verdict.py` decided; the prose above could not have
                # changed it, and printing both is how you can tell.
                yield Line(
                    Text("WHAT DECIDED IT", style=theme.DIM), classes="section-label"
                )
                for rule in rules:
                    yield Line(Text(_bullet(rule)), classes="rule-line")

            limits = getattr(assessment, "limits", "")
            if limits:
                yield from _section("WHAT COULD NOT BE DETERMINED", limits)

            landing = getattr(assessment, "landing", None)
            if landing:
                yield Line(
                    Text("WHERE WORK LANDED", style=theme.DIM), classes="section-label"
                )
                for line in landing:
                    # The engine emits a markdown heading because its primary
                    # output is a file. Here the section already has a label,
                    # and printing both says the same thing twice.
                    if line.strip() and not line.lstrip().startswith("#"):
                        yield Line(_plain(line), classes="landing-line")

            count = len(assessment.claims)
            yield Line(
                Text(
                    f"EVIDENCE   {count} {'claim' if count == 1 else 'claims'}, "
                    "every one carrying an id that resolved",
                    style=theme.DIM,
                ),
                classes="section-label",
            )
            yield ClaimList(assessment.claims, repo=assessment.repo, id="claims")

            # Only rendered when the engine supplied it. The ranking is opt-in
            # now, and nothing about this screen assumes the field exists.
            if getattr(assessment, "entry_points", None):
                yield Line(
                    Text("WHERE TO START", style=theme.DIM), classes="section-label"
                )
                yield MeasuredResult()
                for i, point in enumerate(assessment.entry_points, 1):
                    yield EntryPointRow(i, point)

            yield Line(
                Text(f"method  {assessment.method}", style=theme.FAINT),
                classes="section-label",
            )
            # The model-written sections are only as good as the model behind
            # them, while the counts and the verdict are not model-derived at
            # all. Naming the model is what lets a reader — or a screenshot —
            # tell those two halves apart afterwards.
            models = getattr(assessment, "models", None)
            if models:
                yield Line(
                    Text(f"model   {', '.join(models)}", style=theme.FAINT),
                    classes="section-label",
                )
        yield Line("─" * 240, classes="rule")
        yield Footer()

    def on_mount(self) -> None:
        for index, child in enumerate(self.query_one("#report", VerticalScroll).children):
            animation.reveal(child, delay=animation.stagger(index))

    def _provenance(self) -> Text:
        """Where this result came from, and how old it is. Never omitted."""
        session = self.app.session
        text = Text()
        text.append(f"{session.assessment.repo}   ", style=theme.FAINT)
        stored = session.restored_from
        if stored is not None:
            text.append(
                f"{store.describe_age(stored.age_seconds)} · {stored.mode}",
                style=theme.DIM,
            )
            text.append("   ctrl+r to re-run", style=theme.FAINT)
        else:
            text.append(session.options.mode, style=theme.FAINT)
            if session.cost_usd:
                text.append(f"   ${session.cost_usd:.4f}", style=theme.FAINT)
        return text

    # ─── actions ────────────────────────────────────────────────────────────

    def action_inspect(self) -> None:
        claim = self.query_one("#claims", ClaimList).selected
        if claim is None or not claim.evidence_id:
            return
        self.app.inspect(claim.evidence_id)

    def action_rerun(self) -> None:
        from holt.tui.session import RunOptions

        session = self.app.session
        self.app.start_run(
            RunOptions(
                repo=session.assessment.repo,
                replay=session.options.replay,
                live=session.options.live,
                contributor_days=session.options.contributor_days,
            )
        )

    def action_next(self) -> None:
        """Where someone who has already landed work here might look next."""
        from holt.tui.screens.next_steps import NextScreen

        self.app.push_screen(NextScreen(self.app.session.assessment.repo))

    def action_trace(self) -> None:
        """Back to the run that produced this, when there was one."""
        if self.app.session.restored_from is None and len(self.app.screen_stack) > 2:
            self.app.pop_screen()

    def action_home(self) -> None:
        self.app.go_home()

    def action_quit(self) -> None:
        self.app.exit()


def _headline(verdict) -> str:
    try:
        return VERDICT_HEADLINES[verdict]
    except (KeyError, TypeError):
        return str(getattr(verdict, "value", verdict)).replace("_", " ")


def _section(label: str, body: str):
    yield Line(Text(label, style=theme.DIM), classes="section-label")
    yield Line(body, classes="prose")


def _bullet(text: str, width: int = 88) -> str:
    """A bullet whose continuation lines sit under the text, not the mark.

    A wrapped rule that starts again in the mark column reads as two rules.
    """
    return textwrap.fill(
        " ".join(text.split()),
        width=width,
        initial_indent="· ",
        subsequent_indent="  ",
    )


def _plain(line: str) -> Text:
    """Markdown from `holt.agent.landing`, shown as text.

    The engine emits markdown because its primary output is a file. Rendering
    the asterisks here would be showing the reader the engine's plumbing.
    """
    return Text(line.replace("**", "").replace("`", ""))
