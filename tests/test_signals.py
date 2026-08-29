"""Signals are arithmetic, so they are tested as arithmetic."""

from __future__ import annotations

from datetime import timedelta

from holt.agent.signals import build_threads, compute, newcomer_threads
from holt.types import T_CUTOFF, EvidenceRecord

T0 = T_CUTOFF - timedelta(days=30)


def rec(eid, offset_h, author, extra=None):
    payload = {"author": author, "author_is_bot": False}
    payload.update(extra or {})
    return EvidenceRecord(eid, "github", "https://x", T0 + timedelta(hours=offset_h), payload)


def test_merge_authors_are_counted_separately_from_attempters():
    """Conflating them printed "15 merges from 72 people" in a user-visible report."""
    threads = build_threads([
        rec("pr:a/b#1:opened", 0, "sam"),
        rec("pr:a/b#1:merged", 2, "sam"),
        rec("pr:a/b#2:opened", 4, "kim"),
        rec("pr:a/b#3:opened", 6, "lee"),
    ])
    s = compute(threads)
    assert s.distinct_outsider_authors == 3
    assert s.distinct_merged_authors == 1


def test_a_second_contribution_is_not_a_first_one():
    """The bug this replaced: defining outsider as 'has not merged' makes
    outsider-merge counts zero by construction."""
    threads = build_threads([
        rec("pr:a/b#1:opened", 0, "sam"),
        rec("pr:a/b#1:merged", 2, "sam"),
        rec("pr:a/b#2:opened", 10, "sam"),
        rec("pr:a/b#2:merged", 12, "sam"),
    ])
    firsts = {t.key for t in newcomer_threads(threads)}
    assert firsts == {"pr:a/b#1"}, "only the first landing counts as a newcomer landing"
    assert compute(threads).outsider_merged == 1


def test_bots_are_never_newcomers():
    threads = build_threads([
        EvidenceRecord("pr:a/b#1:opened", "github", "https://x", T0,
                       {"author": "dependabot[bot]", "author_is_bot": True}),
    ])
    assert newcomer_threads(threads) == []
    assert compute(threads).bot_share == 1.0


def test_first_response_ignores_the_author_talking_to_themselves():
    threads = build_threads([
        rec("pr:a/b#1:opened", 0, "sam"),
        rec("pr:a/b#1:comment:0", 1, "sam"),
        rec("pr:a/b#1:comment:1", 5, "maintainer"),
    ])
    assert threads["pr:a/b#1"].first_response_hours == 5.0
    assert threads["pr:a/b#1"].engaged


def test_a_thread_nobody_answered_counts_as_ignored():
    threads = build_threads([rec("pr:a/b#1:opened", 0, "sam")])
    s = compute(threads)
    assert s.outsider_ignored == 1 and s.median_first_response_hours is None


def test_merged_threads_are_not_ignored_even_without_comments():
    threads = build_threads([rec("pr:a/b#1:opened", 0, "sam"), rec("pr:a/b#1:merged", 1, "sam")])
    assert compute(threads).outsider_ignored == 0
