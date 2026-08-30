"""Rendering an evidence id, and the record behind it.

An evidence id is the load-bearing element of the whole report: a claim with one
that resolves is checkable, and a claim without one never reaches the reader. So
it gets the only underline in the interface, and the difference between resolving
and not resolving is visible without reading a word.

Ids are rendered through Rich `Text` spans rather than console markup. Ids
contain brackets, colons and hashes, and markup would either mangle them or, at
worst, let a repository name inject styling into the interface.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget

from holt.tui import theme
from holt.tui.visual import Line


def elide(evidence_id: str, width: int) -> str:
    """Shorten an id from the middle, never from the end.

    Ids look like `pr:owner/name#172481:opened`. The owner and name repeat on
    every row and the part that identifies the record — the number and the
    event — is at the end, so cutting the tail would remove the only thing worth
    reading. The middle goes instead.
    """
    if len(evidence_id) <= width:
        return evidence_id
    if width <= 3:
        return evidence_id[:width]
    keep_tail = max(width * 2 // 3, 1)
    keep_head = width - keep_tail - 1
    if keep_head <= 0:
        return "…" + evidence_id[-(width - 1) :]
    return evidence_id[:keep_head] + "…" + evidence_id[-keep_tail:]


def cite(
    evidence_id: str,
    resolves: bool = True,
    width: int | None = None,
    repo: str | None = None,
) -> Text:
    """One evidence id, styled by whether the provider can resolve it.

    Inside a report about a single repository the `owner/name` in every id is
    the same, and on a long slug it crowds out the part that differs. Passing
    `repo` folds it to an ellipsis for display. The inspector always shows the
    id in full, so nothing is hidden from anyone checking a claim.
    """
    shown = evidence_id
    if repo and repo in shown:
        shown = shown.replace(repo, "…", 1)
    if width:
        shown = elide(shown, width)
    style = f"{theme.CITE} underline" if resolves else f"{theme.DROP} strike"
    return Text(shown, style=style, no_wrap=True, overflow="ellipsis")


class EvidenceDetail(Widget):
    """The record an id resolves to: where it came from, when, and what it says.

    Renders whatever payload the record carries rather than a fixed set of
    fields, because payloads differ by source and a hardcoded list would quietly
    hide anything new.
    """

    def __init__(self, record: Any, **kwargs) -> None:
        super().__init__(**kwargs)
        self.record = record

    def compose(self) -> ComposeResult:
        record = self.record
        if record is None:
            yield Line(
                Text(
                    "This id does not resolve. Stage D removed the claim that cited it.",
                    style=theme.DROP,
                ),
                classes="empty",
            )
            return

        yield Line(cite(record.evidence_id))
        yield Line(
            Text(f"{record.source} · {record.timestamp.isoformat()}", style=theme.FAINT),
            classes="record-meta",
        )
        yield Line(
            Text(record.url, style=theme.FAINT, no_wrap=True, overflow="ellipsis"),
            classes="record-meta",
        )
        yield Line("")
        for key, value in record.payload.items():
            yield Line(_field(key, value))

    @staticmethod
    def _noop() -> None:  # pragma: no cover - placeholder for future actions
        return None


def _field(key: str, value: Any) -> Text:
    text = Text()
    text.append(f"{key:<17}", style=theme.DIM)
    if isinstance(value, list):
        for i, item in enumerate(value[:8]):
            if i:
                text.append("\n" + " " * 17)
            text.append(str(item))
        if len(value) > 8:
            text.append("\n" + " " * 17)
            text.append(f"+{len(value) - 8} more", style=theme.FAINT)
    else:
        text.append(str(value))
    return text
