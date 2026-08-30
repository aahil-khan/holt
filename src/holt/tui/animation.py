"""Motion, kept to the two things it is actually good at.

The rule this module exists to enforce: **animation reports state, or it does
not run.** A spinner means work is happening right now and you cannot know how
long it will take. A reveal means this line is new since you last looked. There
is nothing here that decorates, pulses, bounces or draws attention to something
that has not changed.

That rules out the obvious temptation, a progress bar. The number of threads a
stage will read is not known until it has read them, so a bar would have to
invent a denominator, and a bar that fills at a rate unrelated to the work is a
lie told smoothly.

Everything can be switched off in one place. `HOLT_TUI_NO_ANIMATION=1` disables
motion for people who do not want it, for terminals that render it badly, and
for the tests — which assert on text and should not race a fade.
"""

from __future__ import annotations

import os

#: Braille dots. Eight frames, all the same width, no baseline jitter as it
#: turns — the reason this shape is used everywhere rather than an ASCII
#: pinwheel, which visibly wobbles.
SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧"

#: Fast enough to read as continuous, slow enough not to strobe.
SPINNER_INTERVAL = 0.08

#: A new line arrives at 40% opacity and comes up to full. Short: this is meant
#: to be noticed peripherally, not watched.
REVEAL_DURATION = 0.18
REVEAL_FROM = 0.4

#: Recent rows come in one after another rather than all at once, which makes a
#: list read as a list. Capped so a long history does not turn into a slow
#: cascade the user waits through.
STAGGER_STEP = 0.03
STAGGER_MAX = 0.18


def enabled() -> bool:
    return os.environ.get("HOLT_TUI_NO_ANIMATION", "") in ("", "0", "false", "False")


def frame(tick: int) -> str:
    return SPINNER_FRAMES[tick % len(SPINNER_FRAMES)]


def reveal(widget, delay: float = 0.0) -> None:
    """Bring a freshly mounted widget up from dim.

    Silent about failure on purpose. Motion is the least important thing on the
    screen; if a widget is gone before its animation starts, that is not worth
    an exception in an interface whose job is to render an assessment.
    """
    if not enabled():
        return
    try:
        widget.styles.opacity = REVEAL_FROM
        widget.styles.animate(
            "opacity", value=1.0, duration=REVEAL_DURATION, delay=delay
        )
    except Exception:  # noqa: BLE001 - never let decoration break a screen
        try:
            widget.styles.opacity = 1.0
        except Exception:  # noqa: BLE001
            pass


def stagger(index: int) -> float:
    """The delay for the nth item in a revealed list."""
    return min(index * STAGGER_STEP, STAGGER_MAX)


def elapsed(seconds: float) -> str:
    """A running clock that never claims more precision than it has."""
    if seconds < 10:
        return f"{seconds:.1f}s"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}m{rest:02d}s"
