"""One place where styled text becomes something Textual can lay out.

Spans are built with Rich `Text` throughout the widgets: evidence ids contain
brackets, colons and hashes, and building them as spans rather than console
markup means a repository name can never inject styling into the interface.

Textual's layout engine wants a `Content`. Converting in a single helper keeps
that detail out of every widget, and means a future change to how Textual
consumes renderables is a change to this file.
"""

from __future__ import annotations

from rich.text import Text
from textual.content import Content
from textual.widgets import Static


def visual(renderable):
    """Rich `Text` → Textual `Content`. Anything else passes through."""
    if isinstance(renderable, Text):
        return Content.from_rich_text(renderable)
    return renderable


class Line(Static):
    """A `Static` that accepts Rich `Text` as well as a plain string."""

    def __init__(self, renderable="", **kwargs) -> None:
        super().__init__(visual(renderable), **kwargs)

    def update(self, renderable="") -> None:
        super().update(visual(renderable))
