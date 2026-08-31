"""Recorded discovery, as rows rather than as a page of markdown.

`discover.run_replay` returns rendered markdown, which is the right output for a
file and the wrong one for a screen you navigate: the interface needs the slug
under the cursor so that pressing enter can assess it. Parsing the markdown back
into data would make the interface depend on how the report is worded, which is
exactly the coupling the whole TUI has avoided.

So the screening step is reassembled here from `discover`'s own public parts —
the session manifest, `screen_root`, and `screen_records`, which is where the
rule actually lives. Nothing about *what survives* is decided in this file. It
walks the same candidates in the same order and asks the same function.

The full analysis of survivors is deliberately not reproduced. Assessing a
repository already has a path through this interface, and a second one would be
the duplicate way of running a stage that this feature must not become: pressing
enter on a row starts an ordinary run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from holt import discover
from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

#: The session that ships in the repository. Replays with no token and no key.
DEFAULT_SESSION = "demo"

#: What a screening category means in words, since the engine's labels are
#: short. A category added later falls through to its own label rather than
#: being dropped, so a new reason still says something.
CATEGORY_WORDS = {
    "registry": "a catalogue, not software",
    "inactive": "not active enough",
    "no_outsiders": "no outsider has landed work",
    "unclear": "not enough evidence",
    "archived": "archived",
    "mirror": "a mirror of work done elsewhere",
}


def cut_reason(category: str) -> str:
    return CATEGORY_WORDS.get(category, category.replace("_", " "))


@dataclass(slots=True)
class Row:
    """One candidate the recorded search turned up, and what screening said."""

    slug: str
    description: str
    language: str
    stars: int
    verdict: str
    #: `None` when the candidate survived screening; otherwise why it was cut.
    category: str | None
    reason: str

    @property
    def survived(self) -> bool:
        return self.category is None


@dataclass(slots=True)
class Session:
    name: str
    profile_description: str
    queries: list[str]
    as_of: datetime
    rows: list[Row]
    #: Candidates in the manifest with no recorded evidence. Listed, never
    #: silently dropped — a search that quietly loses candidates is a search
    #: whose count means nothing.
    skipped: list[str]

    @property
    def survivors(self) -> list[Row]:
        return [r for r in self.rows if r.survived]


def manifest_path_exists(name: str = DEFAULT_SESSION) -> bool:
    """Whether a recorded session is on disk. Used to skip, never to guess."""
    try:
        return discover.manifest_path(name).is_file()
    except OSError:
        return False


def available() -> list[str]:
    """Recorded session names, newest first by name."""
    try:
        return sorted(p.stem for p in discover.DISCOVER_ROOT.glob("*.json"))
    except OSError:
        return []


def load(name: str = DEFAULT_SESSION, days: int | None = None) -> Session:
    """Replay a recorded session's screening step. No model, no network.

    Raises `FileNotFoundError` when the session is not on disk, which the screen
    turns into a sentence rather than a traceback.
    """
    manifest: dict[str, Any] = json.loads(discover.manifest_path(name).read_text())
    as_of = datetime.fromisoformat(manifest["as_of"])

    from holt.profile import Profile

    profile = Profile(**manifest["profile"])
    if days:
        profile.days = days

    provider = FixtureProvider(
        Window.PRE_T, root=discover.screen_root(name), cutoff=as_of
    )

    rows: list[Row] = []
    skipped: list[str] = []
    for raw in manifest["candidates"]:
        candidate = discover.Candidate(**raw)
        try:
            records = provider.fetch(candidate.slug)
        except FileNotFoundError:
            skipped.append(candidate.slug)
            continue
        # The rule lives in the engine. This asks it; it does not restate it.
        screened = discover.screen_records(candidate, records, profile.days)
        rows.append(
            Row(
                slug=candidate.slug,
                description=(candidate.description or "").strip(),
                language=candidate.language or "",
                stars=candidate.stars,
                verdict=getattr(screened.verdict, "value", str(screened.verdict)),
                category=screened.category,
                reason=screened.trace[0] if screened.trace else "",
            )
        )

    # Survivors first: they are the ones you can act on. Within each group the
    # search's own order is kept, because reordering would be a claim about
    # which candidate is better and screening does not make one.
    rows.sort(key=lambda r: not r.survived)

    return Session(
        name=name,
        profile_description=profile.describe(),
        queries=list(manifest.get("queries", [])),
        as_of=as_of,
        rows=rows,
        skipped=skipped,
    )
