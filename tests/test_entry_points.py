"""A ranking may never appear without the number that says how well it works.

Path Finder is shipped despite losing to its own comparators, and the only thing
that makes that defensible is that the tool says so itself. If the disclaimer can
be separated from the ranking by any code path, the feature stops being honest
disclosure and becomes an unsupported ranking with a caveat filed in a document
nobody opens. These tests exist to make that separation impossible.
"""

from __future__ import annotations

from datetime import timedelta

from holt.agent import entry
from holt.issues import issue_key, open_at_cutoff
from holt.report import Assessment, Claim, EntryPoint, Verdict
from holt.types import T_CUTOFF, EvidenceRecord

BEFORE = T_CUTOFF - timedelta(days=1)


def issue(number: int, suffix: str = "opened") -> EvidenceRecord:
    return EvidenceRecord(
        f"issue:a/b#{number}:{suffix}", "github", "https://x", BEFORE, {"title": "t"}
    )


def assessment(points: list[EntryPoint]) -> str:
    return Assessment(
        repo="a/b",
        verdict=Verdict.VIABLE,
        summary="s",
        claims=[Claim("c", "pr:a/b#1:opened")],
        entry_points=points,
    ).render()


def test_a_rendered_ranking_always_carries_its_measured_precision():
    out = assessment([EntryPoint("issue:a/b#1", "do the thing", "because")])
    assert "do the thing" in out
    assert entry.DISCLAIMER in out


def test_the_headline_numbers_appear_verbatim_in_the_disclaimer():
    """If the measurement is updated, the printed claim has to move with it."""
    p = entry.MEASURED["precision_at_3"]
    assert f"{p['holt']:.3f}" in entry.DISCLAIMER
    assert f"{p['good_first_issue']:.3f}" in entry.DISCLAIMER
    assert f"{p['random']:.3f}" in entry.DISCLAIMER
    assert str(entry.MEASURED["repos_with_no_labelled_issue"]) in entry.DISCLAIMER
    assert "eval/pathfinder_harness.py" in entry.DISCLAIMER


def test_no_ranking_means_no_section_and_no_disclaimer():
    """Silence, not an empty heading with a caveat under it."""
    out = assessment([])
    assert "Where to start" not in out
    assert entry.DISCLAIMER not in out


def test_ranker_returns_nothing_when_no_issue_was_open(monkeypatch):
    """A model must not be called at all when there is nothing to rank."""
    def explode(*a, **k):  # pragma: no cover - the point is that it never runs
        raise AssertionError("the ranker called the model with no candidates")

    monkeypatch.setattr(entry, "find_paths", explode)
    assert entry.rank("a/b", [], [], model=None) == []


def test_an_issue_closed_before_the_cutoff_is_not_a_candidate():
    """It was not open, so nobody could have started there."""
    records = [issue(1), issue(1, "closed"), issue(2)]
    assert set(open_at_cutoff(records)) == {"issue:a/b#2"}


def test_the_ranker_and_the_label_module_share_one_candidate_set():
    """Drift here would silently invalidate every precision number we publish."""
    from eval.labels import pathfinder

    assert pathfinder.candidates is open_at_cutoff
    assert pathfinder.issue_key is issue_key
