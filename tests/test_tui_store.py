"""Assessments that outlive the process, and the ways that can go wrong.

No Textual here. The store is where the interface's edge cases live — a file
half-written when a laptop slept, a cache entry from an older build, a clock
that moved — and none of that needs a terminal to test.
"""

from __future__ import annotations

import json
import time

import pytest

from holt.report import Assessment, Claim, EntryPoint, Verdict
from holt.tui import store


def make(repo: str = "owner/name", verdict: Verdict = Verdict.VIABLE) -> Assessment:
    assessment = Assessment(
        repo=repo,
        verdict=verdict,
        summary="what the evidence shows",
        claims=[Claim(text="repo_kind = real_software", evidence_id="repo:x:meta")],
        method="holt",
        replayed=True,
    )
    for name, value in (
        ("bottom_line", "the answer in a sentence"),
        ("limits", "what could not be determined"),
        ("rules", ["a rule fired"]),
        ("landing", ["## Where outsider work landed", "src/ 4 of 9"]),
        ("contributor_days", 7),
    ):
        if hasattr(assessment, name):
            setattr(assessment, name, value)
    if hasattr(assessment, "entry_points"):
        assessment.entry_points = [EntryPoint("issue:x#1", "do the thing", "because")]
    return assessment


def entry(repo="owner/name", mode="replay", age=0.0, **kw) -> store.Entry:
    return store.Entry(
        repo=repo,
        mode=mode,
        created_at=time.time() - age,
        assessment=make(repo),
        **kw,
    )


def test_a_saved_assessment_comes_back_whole(tmp_path):
    keep = store.Store(root=tmp_path)
    keep.save(entry())

    restored = store.Store(root=tmp_path).all()
    assert len(restored) == 1
    got = restored[0].assessment

    assert got.repo == "owner/name"
    assert got.verdict is Verdict.VIABLE
    assert got.summary == "what the evidence shows"
    assert [c.evidence_id for c in got.claims] == ["repo:x:meta"]
    for name, expected in (
        ("bottom_line", "the answer in a sentence"),
        ("limits", "what could not be determined"),
        ("rules", ["a rule fired"]),
    ):
        if hasattr(got, name):
            assert getattr(got, name) == expected
    if hasattr(got, "entry_points"):
        assert got.entry_points[0].first_step == "do the thing"


def test_a_corrupt_file_is_skipped_not_fatal(tmp_path):
    """History is a convenience. Losing it must not stop you assessing."""
    keep = store.Store(root=tmp_path)
    keep.save(entry(repo="good/one"))
    (tmp_path / "broken.json").write_text("{not json at all")
    (tmp_path / "empty.json").write_text("")
    (tmp_path / "wrong-shape.json").write_text(json.dumps({"hello": "world"}))

    repos = [e.repo for e in store.Store(root=tmp_path).all()]
    assert repos == ["good/one"]


def test_an_entry_from_another_schema_is_ignored(tmp_path):
    keep = store.Store(root=tmp_path)
    saved = keep.save(entry())
    raw = json.loads(saved.path.read_text())
    raw["schema_version"] = store.SCHEMA_VERSION + 1
    saved.path.write_text(json.dumps(raw))

    assert store.Store(root=tmp_path).all() == []


def test_a_verdict_this_build_does_not_know_is_ignored(tmp_path):
    """Better absent from the list than rendered as something it is not."""
    keep = store.Store(root=tmp_path)
    saved = keep.save(entry())
    raw = json.loads(saved.path.read_text())
    raw["assessment"]["verdict"] = "a_verdict_from_the_future"
    saved.path.write_text(json.dumps(raw))

    assert store.Store(root=tmp_path).all() == []


def test_freshness_is_bounded_and_the_key_includes_the_day_budget(tmp_path):
    keep = store.Store(root=tmp_path)
    keep.save(entry(age=30))

    assert keep.fresh("owner/name", "replay", 7) is not None
    assert keep.fresh("owner/name", "replay", 7, max_age=10) is None
    # A different question, even though it is the same repository: the day
    # budget reaches `verdict.py`, so the answer can genuinely differ.
    assert keep.fresh("owner/name", "replay", 30) is None
    # And a different mode is a different question too.
    assert keep.fresh("owner/name", "live", 7) is None


def test_a_clock_that_moved_backwards_does_not_produce_a_negative_age(tmp_path):
    future = entry(age=-3600)
    assert future.age_seconds == 0.0
    assert store.describe_age(future.age_seconds) == "just now"


def test_the_newest_entry_for_a_question_wins(tmp_path):
    keep = store.Store(root=tmp_path)
    keep.save(entry(age=600))
    keep.save(entry(age=0))

    everything = keep.all()
    assert len(everything) == 1
    assert everything[0].age_seconds < 60


def test_saving_never_raises_when_the_directory_cannot_be_written(tmp_path):
    """An unwritable disk degrades to memory and says so. It does not crash."""
    blocked = tmp_path / "a-file-not-a-directory"
    blocked.write_text("")
    keep = store.Store(root=blocked / "nested")

    saved = keep.save(entry())

    assert keep.read_only is True
    assert saved.path is None
    # Still usable for this session.
    assert [e.repo for e in keep.all()] == ["owner/name"]


def test_a_partial_write_cannot_replace_a_good_entry(tmp_path, monkeypatch):
    keep = store.Store(root=tmp_path)
    keep.save(entry(repo="owner/name"))
    good = json.loads((tmp_path / next(p.name for p in tmp_path.glob("*.json"))).read_text())

    def explode(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(store.json, "dump", explode)
    keep.save(entry(repo="owner/name"))

    surviving = [json.loads(p.read_text()) for p in tmp_path.glob("*.json")]
    assert surviving == [good]
    assert not list(tmp_path.glob(".tmp-*"))


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "just now"),
        (44, "just now"),
        (60, "1 min ago"),
        (300, "5 min ago"),
        (3600, "1 hour ago"),
        (7200, "2 hours ago"),
        (86400, "1 day ago"),
        (172800, "2 days ago"),
    ],
)
def test_age_reads_like_a_person_wrote_it(seconds, expected):
    assert store.describe_age(seconds) == expected
