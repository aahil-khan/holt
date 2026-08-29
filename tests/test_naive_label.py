"""L0 has to be correct before its output means anything.

The point of running L0 is to show what a naive metric rewards. That argument
only lands if the naive metric is faithfully implemented rather than strawmanned.
"""

from __future__ import annotations

from datetime import timedelta

from eval.labels.naive import INSUFFICIENT_EVIDENCE, established_authors, score
from holt.types import T_CUTOFF, EvidenceRecord

BEFORE = T_CUTOFF - timedelta(days=10)
AFTER = T_CUTOFF + timedelta(days=10)


def rec(evidence_id, timestamp, author):
    return EvidenceRecord(evidence_id, "github", "https://x", timestamp, {"author": author})


def test_insiders_come_from_pre_cutoff_merges_only():
    pre = [
        rec("pr:a/b#1:opened", BEFORE, "hopeful"),
        rec("pr:a/b#1:closed", BEFORE, "hopeful"),
        rec("pr:a/b#2:opened", BEFORE, "maintainer"),
        rec("pr:a/b#2:merged", BEFORE, "maintainer"),
    ]
    # Opening a PR that was rejected does not make someone established.
    assert established_authors(pre) == {"maintainer"}


def test_merge_rate_counts_only_outsider_attempts():
    pre = [rec("pr:a/b#1:opened", BEFORE, "maintainer"), rec("pr:a/b#1:merged", BEFORE, "maintainer")]
    post = [
        rec("pr:a/b#10:opened", AFTER, "maintainer"),  # insider, ignored
        rec("pr:a/b#10:merged", AFTER, "maintainer"),
        rec("pr:a/b#11:opened", AFTER, "newcomer"),
        rec("pr:a/b#11:merged", AFTER, "newcomer"),
        rec("pr:a/b#12:opened", AFTER, "other"),
        rec("pr:a/b#12:closed", AFTER, "other"),
    ]
    result = score(pre, post)
    assert result["outsider_attempts"] == 2
    assert result["outsider_merges"] == 1
    assert result["merge_rate"] == 0.5
    assert result["bucket"] == "scored"


def test_distinct_outsiders_is_people_not_pull_requests():
    pre = []
    post = [
        rec("pr:a/b#1:opened", AFTER, "sam"),
        rec("pr:a/b#1:merged", AFTER, "sam"),
        rec("pr:a/b#2:opened", AFTER, "sam"),
        rec("pr:a/b#2:merged", AFTER, "sam"),
    ]
    result = score(pre, post)
    assert result["outsider_merges"] == 2
    assert result["distinct_outsiders_merged"] == 1


def test_no_attempts_is_insufficient_evidence_not_a_zero():
    result = score([rec("pr:a/b#1:merged", BEFORE, "maintainer")], [])
    assert result["bucket"] == INSUFFICIENT_EVIDENCE
    assert result["merge_rate"] is None, "a repo nobody tried is not a repo that rejects everyone"
