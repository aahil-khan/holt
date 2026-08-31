"""A yes/no question, over whatever you were looking at.

Used for the two decisions that destroy work: stopping a run, and quitting with
runs still in flight. Both are cheap to ask about and expensive to get wrong —
a live run stopped at stage D has already been paid for.

Modal rather than a screen you navigate to, because the question is about the
thing underneath it: dismissing has to put you back exactly where you were.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen

from holt.tui import theme
from holt.tui.visual import Line


class ConfirmScreen(ModalScreen[bool]):
    """Returns True if the reader confirmed. Escape and `n` both mean no.

    `n` is bound as well as escape because the question is phrased as a
    question: someone reading "quit anyway? y/n" reaches for `n`, and a key
    that the prompt names has to work.
    """

    BINDINGS = [
        ("y", "confirm", "yes"),
        ("n", "cancel", "no"),
        ("escape", "cancel", "no"),
    ]

    def __init__(
        self,
        question: str,
        detail: str = "",
        yes: str = "y stop",
        no: str = "n keep running",
    ) -> None:
        super().__init__()
        self.question = question
        self.detail = detail
        self.yes = yes
        self.no = no

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Line(Text(self.question, style=theme.DIM), id="confirm-question")
            if self.detail:
                yield Line(Text(self.detail, style=theme.FAINT), id="confirm-detail")
            yield Line(
                Text(f"{self.yes}    {self.no}", style=theme.FAINT), id="confirm-keys"
            )

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
