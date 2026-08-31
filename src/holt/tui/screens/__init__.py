"""Screen registry.

Adding a screen is a new file in this directory and one line in `REGISTRY`.
`app.py` reads this dict and never learns the names of individual screens, so
there is no switch statement to grow and no place where adding a view means
editing a view that already works.

Screens that need constructor arguments — the inspector takes an evidence id —
are pushed as instances instead, so they are deliberately not registered here.
Only screens that can be opened by name belong in this dict.
"""

from __future__ import annotations

from textual.screen import Screen

from holt.tui.screens.discover import DiscoverScreen
from holt.tui.screens.home import HomeScreen
from holt.tui.screens.models import ModelsScreen
from holt.tui.screens.profile import ProfileScreen

REGISTRY: dict[str, type[Screen]] = {
    "home": HomeScreen,
    "discover": DiscoverScreen,
    "profile": ProfileScreen,
    "models": ModelsScreen,
}

__all__ = [
    "REGISTRY",
    "DiscoverScreen",
    "HomeScreen",
    "ModelsScreen",
    "ProfileScreen",
]
