"""The list of assessments you already have.

Each row answers the three questions you actually have when you reopen the tool:
what did it say, how old is it, and how was it produced. The verdict carries the
only colour, because it is the only thing on the row you might act on.

Age is shown on every row without exception. A stored assessment that does not
say how old it is, is indistinguishable from a fresh one, and this list exists
precisely so that nothing has to be re-run to be re-read.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import ListItem, ListView

from holt.report import VERDICT_HEADLINES, Verdict
from holt.tui import store, theme
from holt.tui.visual import Line


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


class RecentList(ListView):
    def __init__(self, entries: list, **kwargs) -> None:
        super().__init__(*[RecentRow(e) for e in entries], **kwargs)
        self.entries = entries

    @property
    def selected(self) -> Any | None:
        return getattr(self.highlighted_child, "entry", None)
