"""The list of assessments you already have.

Each row answers the three questions you actually have when you reopen the tool:
what did it say, how old is it, and how was it produced. The verdict carries the
only colour, because it is the only thing on the row you might act on.

Age is shown on every row without exception. A stored assessment that does not
say how old it is, is indistinguishable from a fresh one, and this list exists
precisely so that nothing has to be re-run to be re-read.

Runs still in flight appear in the same list, above the stored ones, marked and
updating in place. They belong here rather than on a screen of their own for the
same reason the stored ones do: the question on opening holt is "what is going
on with the things I care about", and an answer split across two screens is one
you have to go looking for. The gutter is two columns wide on every row so the
two kinds line up under each other instead of drifting apart.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import ListItem, ListView

from holt.report import VERDICT_HEADLINES, Verdict
from holt.tui import store, theme
from holt.tui.visual import Line

#: Every row starts with this many columns, so a running row and a stored one
#: put their repository names in the same place.
GUTTER = 2

#: The mark on a run in flight. A filled dot rather than a spinner: the row is
#: one line in a list, and a list of spinners is a light show.
RUNNING_MARK = "●"


#: Wide enough for the longest verdict the engine actually has, computed rather
#: than guessed. It was hardcoded to 22, and "Not enough evidence to say" is 26,
#: so that row rendered as "Not enough evidence to say8 hours ago".
HEADLINE_WIDTH = max(len(h) for h in VERDICT_HEADLINES.values()) + 2


def headline(verdict: Verdict) -> str:
    """The engine's own words for a verdict, not a second vocabulary.

    `holt.report` owns these. A verdict this build has not seen falls back to
    its raw value rather than raising, so the list keeps working across an
    engine that grows a fourth answer.
    """
    try:
        return VERDICT_HEADLINES[verdict]
    except (KeyError, TypeError):
        return str(getattr(verdict, "value", verdict)).replace("_", " ")


class RecentRow(ListItem):
    def __init__(self, entry: Any, width_hint: int = 78, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entry = entry
        self.width_hint = width_hint

    def compose(self):
        entry = self.entry
        verdict = entry.assessment.verdict
        value = getattr(verdict, "value", str(verdict))

        row = Text()
        row.append(" " * GUTTER)
        row.append(f"{_repo(entry.repo):<32}", style="")
        row.append(
            f"{headline(verdict):<{HEADLINE_WIDTH}}",
            style=theme.verdict_colour(value),
        )
        row.append(f"{store.describe_age(entry.age_seconds):<14}", style=theme.FAINT)
        row.append(entry.mode, style=theme.FAINT)
        yield Line(row)


def _repo(repo: str, width: int = 31) -> str:
    """Elide the owner first, then the name. The name is what you recognise.

    `Sistema-de-certificacion-academica/Sistema-de-certificacion-academica`
    truncated from the right is all owner and no name, which is the one part
    that distinguishes it from its neighbours.
    """
    if len(repo) <= width:
        return repo
    owner, sep, name = repo.partition("/")
    if not sep:
        return repo[: width - 1] + "…"
    if len(name) + 2 <= width:
        return f"…/{name}"
    return "…/" + name[: width - 3] + "…"


class RunningRow(ListItem):
    """A run in flight: what it is doing, for how long, and what it has spent.

    Redrawn in place rather than rebuilt, because a list that reconstructs
    itself twice a second loses the highlight under the reader's cursor and
    restarts every reveal animation on the rows below.
    """

    def __init__(self, session: Any, **kwargs) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self):
        yield Line(self.text(), classes="running-row")

    def refresh_row(self) -> None:
        try:
            self.query_one(Line).update(self.text())
        except Exception:  # noqa: BLE001 - a row mid-unmount is not an error
            pass

    def text(self) -> Text:
        session = self.session
        row = Text()
        row.append(f"{RUNNING_MARK} ", style=theme.RAIL)
        row.append(f"{_repo(session.options.repo):<32}", style="")
        row.append(f"{status(session):<{HEADLINE_WIDTH}}", style=theme.DIM)
        row.append(f"{elapsed(session.duration):<14}", style=theme.FAINT)
        row.append(session.options.mode, style=theme.FAINT)
        if session.cost_usd:
            row.append(f"   ${session.cost_usd:.4f}", style=theme.FAINT)
        return row


def status(session: Any) -> str:
    """What the run is doing, in the words the stage list already uses.

    A stop that has been asked for but not yet landed says `stopping`, never
    `stopped`: the worker is interrupted at its next model call, and a row that
    claimed otherwise would be lying for as long as that call takes.
    """
    if session.stopping:
        return "stopping…"
    stage = getattr(session, "stage", "")
    return f"running · {stage}" if stage else "starting"


def elapsed(seconds: float) -> str:
    minutes, whole = divmod(int(seconds), 60)
    return f"{minutes}:{whole:02d}"


class RecentList(ListView):
    def __init__(self, entries: list, **kwargs) -> None:
        super().__init__(*[RecentRow(e) for e in entries], **kwargs)
        self.entries = entries

    @property
    def selected(self) -> Any | None:
        """The stored assessment under the cursor, if that is what is there."""
        return getattr(self.highlighted_child, "entry", None)

    @property
    def selected_session(self) -> Any | None:
        """The run under the cursor, if the cursor is on a running row."""
        return getattr(self.highlighted_child, "session", None)

    def running_rows(self) -> list["RunningRow"]:
        return [row for row in self.children if isinstance(row, RunningRow)]
