"""Screen registry.

Adding a screen is a new file in this directory and one line in `REGISTRY`.
`app.py` reads this dict and never learns the names of individual screens, so
there is no switch statement to grow and no place where adding a view means
editing a view that already works.

Screens that take constructor arguments — the inspector needs an evidence id —
are pushed as instances rather than by name, so they are deliberately not
registered here.
"""

from __future__ import annotations

from textual.screen import Screen

from holt.tui.screens.assessment import AssessmentScreen
from holt.tui.screens.live import LiveScreen

REGISTRY: dict[str, type[Screen]] = {
    "live": LiveScreen,
    "assessment": AssessmentScreen,
}

__all__ = ["REGISTRY", "AssessmentScreen", "LiveScreen"]
