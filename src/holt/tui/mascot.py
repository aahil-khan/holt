"""The masthead, and the one piece of decoration in the interface.

A *holt* is an otter's den — the place an animal decides is worth settling into,
which is the question this tool asks about a repository. That is why the mascot
is an otter rather than a generic mark, and it is the whole of the argument for
it being here.

Two rules keep it from undermining the rest of the design:

* **It appears exactly once**, on the home screen, the way a masthead does. It
  is not a logo stamped on every view.
* **It has its own colour, and that colour means nothing.** The palette rule is
  that colour carries meaning — verdict state, evidence resolution, Stage D
  drops. A decorative element borrowing one of those would dilute all three, so
  the mascot gets a tone used nowhere else and encoding nothing. Seeing it tells
  you where you are, not what happened.

The masthead beside it is not filler either: it carries what the tool is, what
it will not do, and what you already have. An empty screen that says nothing is
the problem this replaces.
"""

from __future__ import annotations

#: Twelve columns, five rows. Negative space does the work — the eyes and the
#: muzzle are gaps, not glyphs, so it survives fonts that render half-blocks at
#: slightly different weights.
OTTER: tuple[str, ...] = (
    " ▄▄      ▄▄ ",
    "▐██████████▌",
    "▐█  █▄▄█  █▌",
    "▐██████████▌",
    " ▀██▀  ▀██▀ ",
)

WIDTH = max(len(row) for row in OTTER)

#: From `holt.cli`'s own docstring. The tool's description of itself, not a
#: second one written for the interface.
TAGLINE = "is this repository worth an outside contributor's week?"

#: The three things worth knowing before you type anything. Each is a fact about
#: how it behaves, not a feature list.
FACTS: tuple[str, ...] = (
    "read-only — never writes to GitHub, never opens a pull request",
    "every claim carries an evidence id you can open and check",
    "a claim whose evidence does not resolve is dropped, not softened",
)
