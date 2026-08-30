"""Which issues were open at the cutoff.

This lives outside both `holt.agent` and `eval.labels` on purpose. The label
modules must not import from the agent, so a definition they both need cannot
sit in either one. Duplicating it would let the ranked set and the scored set
drift apart without a test noticing, which is the one failure that would make a
Path Finder number meaningless.
"""

from __future__ import annotations

from collections.abc import Iterable

from holt.types import EvidenceRecord


def issue_key(evidence_id: str) -> str:
    """`issue:owner/name#12:closed` -> `issue:owner/name#12`."""
    return ":".join(evidence_id.split(":")[:2])


def open_at_cutoff(pre_t: Iterable[EvidenceRecord]) -> dict[str, EvidenceRecord]:
    """Issues open at T, keyed by issue.

    A record only reaches here if the provider already asserted its timestamp is
    at or before the cutoff, so "opened before T" needs no separate check. An
    issue closed *before* T never produces a pre-cutoff `:closed` record either,
    so anything with an `:opened` record and no pre-cutoff closure was open.
    """
    records = list(pre_t)
    opened = {
        issue_key(r.evidence_id): r
        for r in records
        if r.evidence_id.startswith("issue:") and r.evidence_id.endswith(":opened")
    }
    closed_before = {
        issue_key(r.evidence_id)
        for r in records
        if r.evidence_id.startswith("issue:") and r.evidence_id.endswith(":closed")
    }
    return {k: v for k, v in opened.items() if k not in closed_before}
