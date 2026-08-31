"""What you want to work on, said once.

`holt discover` reads this, and on the command line it is a set of prompts you
answer in sequence. In a terminal interface a form is better: every field is
visible at once, you can see what is already stored, and changing one does not
mean re-answering the rest.

The file is `holt.profile`'s, at `holt.profile.config_path()`, in the same
format the command-line version writes. Editing here and editing there are the
same thing, so nobody has to know which one produced the file they have.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input

from holt.tui import animation, theme
from holt.tui.visual import Line

#: Field name, label, and the sentence that says what it is for. The order is
#: the order the questions are asked in on the command line.
FIELDS: tuple[tuple[str, str, str], ...] = (
    ("languages", "languages", "comma separated — python, rust"),
    ("topics", "topics", "GitHub topics — cli, database"),
    ("contributions", "contributions", "docs, tests, ci, code"),
    ("days", "days", "how many days you actually have"),
)


class ProfileScreen(Screen):
    BINDINGS = [
        ("ctrl+s", "save", "save"),
        ("escape", "home", "home"),
        ("q", "quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        from holt import profile as profile_mod

        stored = profile_mod.load()

        with Horizontal(id="chrome"):
            yield Line("holt · profile", id="chrome-left")
            yield Line(
                Text(str(profile_mod.config_path()), style=theme.FAINT),
                id="chrome-right",
            )
        yield Line("─" * 240, classes="rule")

        with Vertical(id="profile-body"):
            yield Line(
                Text(
                    "Said once, and read by discover. Nothing here is sent "
                    "anywhere; it only shapes which repositories are searched for.",
                    style=theme.FAINT,
                ),
                classes="section-label",
            )
            for name, label, note in FIELDS:
                # The note is the placeholder and nothing else. Printing it as a
                # caption as well said the same thing twice on every field.
                yield Line(Text(label, style=theme.DIM), classes="section-label")
                yield Input(
                    value=_value(stored, name),
                    placeholder=note,
                    id=f"profile-{name}",
                )
            yield Line("", id="profile-notice")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#profile-languages", Input).focus()
        self._notice("ctrl+s saves    esc goes back without saving")

    def _notice(self, message: str, tone: str = "") -> None:
        widget = self.query_one("#profile-notice", Line)
        widget.update(Text(message, style=tone or theme.FAINT))
        animation.reveal(widget)

    # ─── actions ────────────────────────────────────────────────────────────

    def action_save(self) -> None:
        from holt import profile as profile_mod

        values = {
            name: self.query_one(f"#profile-{name}", Input).value.strip()
            for name, _label, _note in FIELDS
        }

        days_text = values["days"]
        if days_text and not days_text.isdigit():
            self._notice(f"“{days_text}” is not a number of days.", theme.DROP)
            return

        built = profile_mod.Profile(
            languages=_split(values["languages"]),
            topics=_split(values["topics"]),
            contributions=_split(values["contributions"]),
            days=int(days_text) if days_text else profile_mod.DEFAULT_CONTRIBUTOR_DAYS,
        )
        try:
            path = profile_mod.save(built)
        except OSError as exc:
            self._notice(f"Could not write the profile: {exc}", theme.DROP)
            return
        self._notice(f"Saved to {path}")

    def action_home(self) -> None:
        self.app.go_home()

    def action_quit(self) -> None:
        self.app.exit()


def _value(stored, name: str) -> str:
    if stored is None:
        return ""
    value = getattr(stored, name, None)
    if isinstance(value, list):
        return ", ".join(value)
    return "" if value is None else str(value)


def _split(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]
