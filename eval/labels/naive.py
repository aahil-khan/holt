"""L0 — the naive label: outsider pull request merge rate.

This is the metric a reasonable engineer writes first, and it is meant to be
naive. It asks one question: of the pull requests outsiders opened after the
cutoff, what fraction got merged? No filter on what the diff touches, no bot
exclusion, no requirement that a human reviewed anything.

L0 is not dead code and not a straw man. It is the Baseline row of the changelog,
and running it is what turns a claim about naive metrics into a number.

This module must not import from holt.agent. A test enforces that: a label that
can see the agent is not a label.
"""

from __future__ import annotations

from collections.abc import Iterable

from holt.types import EvidenceRecord

# A repository with no outsider attempts at all is not a failure, it is an
# absence of evidence. Collapsing the two would let a silent repository score
# the same as a hostile one.
INSUFFICIENT_EVIDENCE = "insufficient_evidence"


def established_authors(pre_t: Iterable[EvidenceRecord]) -> set[str]:
    """Authors who already had a pull request merged before the cutoff.

    Computed from pre-cutoff evidence only. Deriving "outsider" from post-cutoff
    data would leak the thing being measured into the definition of who counts.
    """
    return {
        record.payload["author"]
        for record in pre_t
        if record.evidence_id.endswith(":merged")
    }


def _pr_key(evidence_id: str) -> str:
    """`pr:owner/name#12:merged` -> `pr:owner/name#12`."""
    return evidence_id.rsplit(":", 1)[0]


def score(pre_t: Iterable[EvidenceRecord], post_t: Iterable[EvidenceRecord]) -> dict:
    insiders = established_authors(pre_t)
    post_t = list(post_t)

    opened = {
        _pr_key(r.evidence_id): r.payload["author"]
        for r in post_t
        if r.evidence_id.endswith(":opened")
    }
    merged = {_pr_key(r.evidence_id) for r in post_t if r.evidence_id.endswith(":merged")}

    outsider_prs = {key: author for key, author in opened.items() if author not in insiders}
    outsider_merged = {key for key in outsider_prs if key in merged}

    attempts = len(outsider_prs)
    return {
        "insiders_pre_t": len(insiders),
        "outsider_attempts": attempts,
        "outsider_merges": len(outsider_merged),
        "distinct_outsiders_merged": len({outsider_prs[k] for k in outsider_merged}),
        "merge_rate": (len(outsider_merged) / attempts) if attempts else None,
        "bucket": INSUFFICIENT_EVIDENCE if attempts == 0 else "scored",
    }
