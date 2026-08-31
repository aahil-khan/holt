"""The cat, and the masthead it leads.

Two widgets. `Cat` is one line that can be dropped anywhere — a masthead, a
status bar, a chrome row — and changes mood when the run does. `Masthead` is the
home screen's opening: the cat, the tool's own description of itself, and the
three facts worth knowing before you type.

The launch reveal is deliberately short. It exists to make the screen feel like
it arrived rather than blinked into being, and it is over in about a quarter of
a second. It never takes the keyboard: the input is focused from the first
frame, so typing straight over the top of it works and the animation simply
stops. An intro you have to sit through is a worse thing than no intro.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget

from holt.tui import animation, mascot, theme
from holt.tui.visual import Line


def _version() -> str:
    """The installed version, or nothing. Never a guess and never a crash."""
    try:
        from importlib.metadata import version

        return version("holt")
    except Exception:  # noqa: BLE001 - a masthead is not worth an exception
        return ""


class Cat(Widget):
    """One line of cat. Blinks at rest, looks about while a run is going."""

    def __init__(self, mood: str = "idle", **kwargs) -> None:
        super().__init__(**kwargs)
        self._mood = mood
        self._tick = 0
        self._timer = None

    def on_mount(self) -> None:
        self._paint()
        if animation.enabled():
            self._timer = self.set_interval(mascot.TICK, self._advance)

    def on_unmount(self) -> None:
        self._stop()

    def _stop(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def set_mood(self, mood: str) -> None:
        if mood == self._mood:
            return
        self._mood = mood
        # Restart the cycle so a mood change reads immediately rather than
        # arriving part-way through the previous one's blink.
        self._tick = 0
        self._paint()

    def _advance(self) -> None:
        self._tick += 1
        self._paint()

    def _paint(self) -> None:
        cycle = mascot.frames(self._mood)
        frame = cycle[self._tick % len(cycle)] if animation.enabled() else cycle[0]
        self.update(Text(frame, style=self.app.accent))

    def update(self, renderable) -> None:
        # `Cat` is a plain Widget so it can own a timer; rendering goes through
        # the same conversion every other line uses.
        self._renderable = renderable
        self.refresh()

    def render(self):
        from holt.tui.visual import visual

        return visual(getattr(self, "_renderable", ""))


class Masthead(Widget):
    def compose(self) -> ComposeResult:
        with Horizontal(id="masthead"):
            yield Cat(id="cat")
            with Vertical(id="masthead-text"):
                title = Text("holt", style="bold")
                if _version():
                    # Not a bare repeat of the title bar two lines above: the
                    # version is the one thing here the chrome does not say.
                    title.append(f"  {_version()}", style=theme.FAINT)
                yield Line(title, id="masthead-title", classes="masthead-name")
                yield Line(
                    Text(mascot.TAGLINE, style=theme.DIM), id="masthead-tagline"
                )
                yield Line("")
                for index, fact in enumerate(mascot.FACTS):
                    yield Line(
                        Text(f"· {fact}", style=theme.FAINT),
                        id=f"masthead-fact-{index}",
                        classes="masthead-fact",
                    )

    def on_mount(self) -> None:
        """Reveal, briefly. Everything is already on screen and readable if
        motion is off, so this only ever adds, never gates."""
        if not animation.enabled():
            return
        for index, widget in enumerate(self.query(Line)):
            animation.reveal(widget, delay=animation.stagger(index))

    def set_mood(self, mood: str) -> None:
        try:
            self.query_one("#cat", Cat).set_mood(mood)
        except Exception:  # noqa: BLE001 - the cat is never load-bearing
            pass
