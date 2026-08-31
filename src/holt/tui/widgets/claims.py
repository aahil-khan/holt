"""The claim list: statements, each with the id that survived Stage D.

Selection is by keyboard. Enter on a claim resolves its evidence id and opens
the record, which is the interaction the report is really about — a reader
should be one keystroke from checking any sentence Holt writes.

The list makes no assumption about how many claims there are or what fields
they carry. It renders what the `Assessment` holds.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import ListItem, ListView

from holt.tui import theme
from holt.tui.widgets.evidence import cite
from holt.tui.visual import Line
from holt.tui.widgets.scrolling import KeepsHighlightVisible


class ClaimItem(ListItem):
    def __init__(self, claim: Any, repo: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.claim = claim
        self.repo = repo

    def compose(self):
        claim = self.claim
        yield Line(
            Text(_headline(claim.text), no_wrap=True, overflow="ellipsis")
        )
        if claim.evidence_id:
            row = Text("  ")
            row.append_text(cite(claim.evidence_id, width=64, repo=self.repo))
            yield Line(row)
        else:
            # Should not occur — Stage D removes these — but the view reports
            # what it is given rather than asserting the engine's invariant.
            yield Line(Text("  no evidence id", style=theme.DROP))


class ClaimList(KeepsHighlightVisible, ListView):
    def __init__(self, claims: list, repo: str | None = None, **kwargs) -> None:
        super().__init__(*[ClaimItem(c, repo) for c in claims], **kwargs)
        self.claims = claims

    @property
    def selected(self) -> Any | None:
        item = self.highlighted_child
        return getattr(item, "claim", None)


def _headline(text: str) -> str:
    """The claim's first clause. The rationale in parentheses is the detail."""
    head = text.split(" (", 1)[0]
    return " ".join(head.split())
