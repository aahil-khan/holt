"""The mascot and what sits beside it.

Laid out as two columns: the otter on the left at a fixed width, and on the
right the name, what the tool is, and what it will not do. The right-hand column
is the reason the left-hand one is allowed to exist — a mascot next to an empty
screen is decoration, a mascot next to the three facts you need before typing is
a masthead.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget

from holt.tui import mascot, theme
from holt.tui.visual import Line


def _version() -> str:
    """The installed version, or nothing. Never a guess and never a crash."""
    try:
        from importlib.metadata import version

        return version("holt")
    except Exception:  # noqa: BLE001 - a masthead is not worth an exception
        return ""


class Masthead(Widget):
    def compose(self) -> ComposeResult:
        with Horizontal(id="masthead"):
            art = Text()
            for index, row in enumerate(mascot.OTTER):
                if index:
                    art.append("\n")
                art.append(row, style=theme.MASCOT)
            yield Line(art, id="mascot")

            with Vertical(id="masthead-text"):
                title = Text("holt", style="bold")
                if _version():
                    # Not a bare repeat of the title bar two lines above: the
                    # version is the one thing here the chrome does not say.
                    title.append(f"  {_version()}", style=theme.FAINT)
                yield Line(title, classes="masthead-name")
                yield Line(Text(mascot.TAGLINE, style=theme.DIM))
                yield Line("")
                for fact in mascot.FACTS:
                    yield Line(Text(f"· {fact}", style=theme.FAINT),
                               classes="masthead-fact")
