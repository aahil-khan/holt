"""Ground truth for Path Finder: which issues actually became entry points.

An issue open at the cutoff is a **realised entry point** if it was later closed
by a merged pull request whose author had not already landed work in the
repository before the cutoff.

Every term is mechanical, and the outsider test is the same one L1 uses, computed
from pre-cutoff evidence so it cannot leak. The design, its base rate, its
comparators and the conditions for abandoning it are in
`eval/PATHFINDER-DESIGN.md`, written before any of this existed.

This module must not import from holt.agent. A test enforces that.
"""

from __future__ import annotations

from collections.abc import Iterable

from eval.labels.qualifying import established_authors
from holt.types import T_CUTOFF, EvidenceRecord

CUTOFF_ISO = T_CUTOFF.isoformat()

# Below this many candidate issues, precision at 3 is noise rather than a
# measurement. Declared in the design document before any repository was scored.
MIN_CANDIDATE_ISSUES = 10


def issue_key(evidence_id: str) -> str:
    """`issue:owner/name#12:closed` -> `issue:owner/name#12`."""
    return ":".join(evidence_id.split(":")[:2])


def candidates(pre_t: Iterable[EvidenceRecord]) -> dict[str, EvidenceRecord]:
    """Issues open at the cutoff — the set Path Finder ranks.

    A record only reaches here if the provider already asserted its timestamp is
    at or before the cutoff, so "opened before T" needs no separate check. An
    issue closed *before* T never produces a pre-cutoff `:closed` record either,
    so anything with an `:opened` record and no pre-cutoff closure was open.
    """
    opened = {
        issue_key(r.evidence_id): r
        for r in pre_t
        if r.evidence_id.startswith("issue:") and r.evidence_id.endswith(":opened")
    }
    closed_before = {
        issue_key(r.evidence_id)
        for r in pre_t
        if r.evidence_id.startswith("issue:") and r.evidence_id.endswith(":closed")
    }
    return {k: v for k, v in opened.items() if k not in closed_before}


def realised(
    pre_t_pulls: Iterable[EvidenceRecord], post_t: Iterable[EvidenceRecord]
) -> set[str]:
    """Issues later closed by a merged pull request from someone new."""
    insiders = established_authors(pre_t_pulls)
    out: set[str] = set()
    for r in post_t:
        if not (r.evidence_id.startswith("issue:") and r.evidence_id.endswith(":closed")):
            continue
        for pr in r.payload.get("closing_prs") or []:
            if pr.get("author_is_bot"):
                continue
            if pr.get("author") not in insiders:
                out.add(issue_key(r.evidence_id))
                break
    return out


def score(
    pre_t: Iterable[EvidenceRecord], post_t: Iterable[EvidenceRecord]
) -> dict:
    pre_t = list(pre_t)
    cand = candidates(pre_t)
    hits = realised(pre_t, post_t) & set(cand)
    edited_after = sum(
        1
        for r in cand.values()
        if (u := r.payload.get("last_edited_at")) and u > CUTOFF_ISO
    )
    return {
        "candidates": len(cand),
        "realised": len(hits),
        "realised_keys": sorted(hits),
        "base_rate": (len(hits) / len(cand)) if cand else None,
        # The size of the known leak: issue bodies GitHub returns are current,
        # not as-of-cutoff. Reported rather than assumed away.
        "edited_after_cutoff": edited_after,
        "scorable": len(cand) >= MIN_CANDIDATE_ISSUES,
    }
