"""The tool's negative result about itself, and the ranking it qualifies.

The reading order Holt prints was measured against the comparators that could
make it unnecessary, and it did not beat them. That measurement is displayed
here, above the ranking, in full.

Three deliberate choices, because how this is presented is the claim:

* **It is not an error.** No red, no warning icon. It is a considered disclosure
  and it is styled like the rest of the prose, set off by a quiet rail.
* **It is not collapsed.** There is no key to press to reveal it. A caveat filed
  behind a keystroke is a caveat filed where nobody looks.
* **It gets more room than the ranking.** The four precision figures are a table
  rather than a sentence, because the point is that they sit on top of each
  other, and a table shows that in one glance where prose hides it.

Every number comes from `holt.agent.entry.MEASURED`, the same constant the
report renders and the harness regenerates. There are no figures typed into this
file, so the interface cannot drift from the measurement.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget

from holt.agent.entry import MEASURED
from holt.tui import theme
from holt.tui.widgets.evidence import cite
from holt.tui.visual import Line


#: Display names for the comparators, in the order they are shown. Ours first,
#: because the honest reading is "this one, against the ones that beat it".
COMPARATORS: tuple[tuple[str, str], ...] = (
    ("this ranking", "holt"),
    ("good first issue", "good_first_issue"),
    ("recency", "recency"),
    ("random", "random"),
)


class MeasuredResult(Widget):
    def compose(self) -> ComposeResult:
        precision = MEASURED.get("precision_at_3", {})
        repos = MEASURED.get("repositories")
        issues = MEASURED.get("issues_ranked")
        low, high = MEASURED.get("paired_ci_vs_label", (0.0, 0.0))
        p_value = MEASURED.get("sign_test_p")
        unlabelled = MEASURED.get("repos_with_no_labelled_issue")

        yield Line(
            Text(
                "This ranking is not measurably better than picking at random.",
                style="bold",
            ),
            classes="measured-lede",
        )
        yield Line(
            f"Measured over {repos} repositories and {issues:,} issues held out "
            "before the cutoff."
        )
        yield Line("")

        for label, key in COMPARATORS:
            if key not in precision:
                continue
            row = Text()
            row.append(f"  {label:<20}", style="" if key == "holt" else theme.DIM)
            row.append(f"{precision[key]:.3f}", style="" if key == "holt" else theme.DIM)
            yield Line(row, classes="measured-row")

        yield Line("")
        yield Line(
            f"Differences well inside noise — paired 95% CI [{low:+.2f}, {high:+.2f}], "
            f"sign test p = {p_value}."
        )
        yield Line("")
        yield Line(
            f"Printed anyway because {unlabelled} of those {repos} repositories had no "
            "beginner-labelled issue at all, so on half of them there is no free "
            "signal to lose to. Read it as a reading order, not a recommendation."
        )
        yield Line("")
        check = Text()
        check.append("Check it yourself:  ", style=theme.DIM)
        check.append("uv run python eval/pathfinder_harness.py --replay")
        yield Line(check, classes="measured-check")


class EntryPointRow(Widget):
    """One suggested starting point.

    Numbered, because here the order is the content — it is a reading order, and
    the number is the only thing the ranking actually asserts. Nothing else in
    the interface is a sequence, so nothing else is numbered.
    """

    def __init__(self, index: int, point: Any, **kwargs) -> None:
        super().__init__(**kwargs)
        self.index = index
        self.point = point

    def compose(self) -> ComposeResult:
        head = Text()
        head.append(f"{self.index}  ", style=theme.FAINT)
        head.append(" ".join(self.point.first_step.split()))
        yield Line(head)

        row = Text("   ")
        row.append_text(cite(self.point.evidence_id, width=60))
        yield Line(row)

        if self.point.why:
            yield Line(
                Text(" ".join(self.point.why.split()), style=theme.FAINT),
                classes="entry-why",
            )
