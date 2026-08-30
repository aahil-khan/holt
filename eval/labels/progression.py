"""Ground truth for personalised contribution discovery.

The unit is a **(repository, contributor) pair**, not a repository. For a
contributor who had already merged something in a repository before T, an issue
open at T is a **realised next contribution** if it was later closed by a merged
pull request that they authored.

Two exclusions, both declared in `eval/PREREGISTRATION-3.md` before any of this
was written:

* **Issues the contributor opened themselves are removed from the label and from
  the candidate set.** 46% of the raw matches were people closing their own
  issues. Predicting that somebody fixes the bug they filed is not a
  recommendation — the intent is already legible in pre-cutoff evidence — and a
  ranker that noticed it would have posted a large, meaningless win.
* **Pairs with no realised next contribution are not scored.** Every method
  including the comparators scores identically zero there, so they contribute a
  constant and nothing else. The proportion is reported instead.

This module must not import from holt.agent. `tests/test_label_isolation.py`
enforces that structurally.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from holt.issues import issue_key, open_at_cutoff
from holt.types import EvidenceRecord

BOT_SUFFIX = "[bot]"
KNOWN_BOT_WORDS = ("bot", "renovate", "dependabot", "imgbot", "greenkeeper", "codecov")


def looks_like_bot(login: str) -> bool:
    """Read-time bot test, duplicated rather than imported.

    `holt.agent.signals` has an equivalent. Importing it would let the graded
    agent decide who counts as a person in its own ground truth, which is the
    coupling this file exists to avoid.
    """
    low = login.lower()
    return low.endswith(BOT_SUFFIX) or any(w in low for w in KNOWN_BOT_WORDS)


@dataclass
class History:
    """What a contributor had demonstrably done in this repository before T."""

    login: str
    merged_prs: list[dict] = field(default_factory=list)

    @property
    def files(self) -> set[str]:
        return {f for pr in self.merged_prs for f in (pr.get("files") or [])}

    @property
    def median_size(self) -> int:
        sizes = sorted((pr.get("additions") or 0) + (pr.get("deletions") or 0)
                       for pr in self.merged_prs)
        return sizes[len(sizes) // 2] if sizes else 0

    @property
    def engaged_with(self) -> set[str]:
        """People who spoke on their merged pull requests."""
        return {a for pr in self.merged_prs for a in (pr.get("_responders") or [])}


def histories(pre_t_pulls: Iterable[EvidenceRecord]) -> dict[str, History]:
    """Merged pull requests before T, grouped by human author.

    Responders are attached to each pull request here rather than recomputed
    later, so the ranker and the label see one definition of "engaged with".
    """
    opened: dict[str, dict] = {}
    merged: set[str] = set()
    responders: dict[str, set[str]] = {}
    for record in pre_t_pulls:
        eid = record.evidence_id
        if not eid.startswith("pr:"):
            continue
        number = eid.split(":")[1]
        tail = eid.rsplit(":", 1)[-1]
        if eid.endswith(":opened"):
            opened[number] = record.payload
        elif eid.endswith(":merged") and record.payload.get("merged"):
            merged.add(number)
        elif tail.isdigit():
            author = record.payload.get("author")
            if author and not record.payload.get("author_is_bot"):
                responders.setdefault(number, set()).add(author)

    out: dict[str, History] = {}
    # Sorted, because `merged` is a set and Python randomises string hashing per
    # process. Unsorted iteration made the pull-request order inside a prompt vary
    # between runs, which turned every recorded trajectory into a replay miss.
    for number in sorted(merged, key=lambda n: (len(n), n)):
        payload = opened.get(number)
        if not payload:
            continue
        author = payload.get("author") or ""
        if not author or payload.get("author_is_bot") or looks_like_bot(author):
            continue
        enriched = dict(payload)
        enriched["_responders"] = sorted(responders.get(number, set()) - {author})
        out.setdefault(author, History(author)).merged_prs.append(enriched)
    return out


def candidates(pre_t_issues: Iterable[EvidenceRecord], login: str) -> dict[str, EvidenceRecord]:
    """Issues open at T that this contributor did not raise."""
    return {
        key: record
        for key, record in open_at_cutoff(pre_t_issues).items()
        if record.payload.get("author") != login
    }


def realised(
    pre_t_issues: Iterable[EvidenceRecord],
    post_t_issues: Iterable[EvidenceRecord],
    login: str,
) -> set[str]:
    """Issues this contributor actually resolved after T."""
    eligible = candidates(pre_t_issues, login)
    out: set[str] = set()
    for record in post_t_issues:
        eid = record.evidence_id
        if not (eid.startswith("issue:") and eid.endswith(":closed")):
            continue
        key = issue_key(eid)
        if key not in eligible:
            continue
        for pull in record.payload.get("closing_prs") or []:
            if pull.get("author_is_bot"):
                continue
            if pull.get("author") == login:
                out.add(key)
                break
    return out


def pairs(
    pre_t_pulls: Iterable[EvidenceRecord],
    pre_t_issues: Iterable[EvidenceRecord],
    post_t_issues: Iterable[EvidenceRecord],
) -> tuple[list[tuple[History, dict, set[str]]], int]:
    """Scorable pairs for one repository, and how many were considered.

    Returns `(scorable, considered)` so the harness can report the selection rate
    rather than only the surviving set.
    """
    pre_i = list(pre_t_issues)
    post_i = list(post_t_issues)
    everyone = histories(pre_t_pulls)
    scorable = []
    for login, history in sorted(everyone.items()):
        hits = realised(pre_i, post_i, login)
        if not hits:
            continue
        scorable.append((history, candidates(pre_i, login), hits))
    return scorable, len(everyone)
