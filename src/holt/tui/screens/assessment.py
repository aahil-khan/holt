"""The finished report, navigable.

The verdict is the largest thing on the screen and the only element that gets
both weight and colour. Below it sit the rules the verdict was computed from —
they come from the pipeline's own `Trace`, not from the prose, because the
narration explains the verdict and is not allowed to restate it.

`entry_points` is treated as optional throughout. It is the one field of
`Assessment` still in flux, so its absence renders nothing at all rather than an
empty heading.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer

from holt.tui import theme
from holt.tui.widgets.claims import ClaimList
from holt.tui.widgets.disclosure import EntryPointRow, MeasuredResult
from holt.tui.visual import Line


class AssessmentScreen(Screen):
    BINDINGS = [
        ("enter", "inspect", "open evidence"),
        ("l", "live", "trace"),
        ("q", "quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        assessment = self.app.session.assessment
        trace = self.app.session.trace

        with Horizontal(id="chrome"):
            yield Line("holt", id="chrome-left")
            yield Line(
                Text(
                    f"{assessment.repo}   "
                    f"{'replay' if assessment.replayed else 'live'}",
                    style=theme.FAINT,
                ),
                id="chrome-right",
            )
        yield Line("─" * 200, classes="rule")

        with VerticalScroll():
            verdict = assessment.verdict.value
            yield Line(
                Text(theme.verdict_label(verdict), style=theme.verdict_colour(verdict)),
                id="verdict",
            )
            if trace is not None and getattr(trace, "rules", None):
                yield Line(
                    "\n".join(trace.rules),
                    id="verdict-rules",
                )
            yield Line(assessment.summary, id="summary")

            yield Line("─" * 200, classes="rule")
            count = len(assessment.claims)
            yield Line(
                Text(
                    f"EVIDENCE   {count} "
                    f"{'claim' if count == 1 else 'claims'}, every one carrying an id "
                    "that resolved",
                    style=theme.DIM,
                ),
                classes="section-label",
            )
            yield ClaimList(assessment.claims, repo=assessment.repo, id="claims")

            # Only rendered when the engine supplied it. Nothing about this
            # screen assumes the field exists.
            if getattr(assessment, "entry_points", None):
                yield Line("─" * 200, classes="rule")
                yield Line(
                    Text("WHERE TO START", style=theme.DIM), classes="section-label"
                )
                yield MeasuredResult()
                for i, point in enumerate(assessment.entry_points, 1):
                    yield EntryPointRow(i, point)

            yield Line("─" * 200, classes="rule")
            yield Line(
                Text(f"method  {assessment.method}", style=theme.FAINT),
                classes="section-label",
            )
        yield Footer()

    # ─── actions ────────────────────────────────────────────────────────────

    def action_inspect(self) -> None:
        claim = self.query_one("#claims", ClaimList).selected
        if claim is None or not claim.evidence_id:
            return
        self.app.inspect(claim.evidence_id)

    def action_live(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()
