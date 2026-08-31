"""Assessments that outlive the process, and the ways that can go wrong.

No Textual here. The store is where the interface's edge cases live — a file
half-written when a laptop slept, a cache entry from an older build, a clock
that moved — and none of that needs a terminal to test.
"""

from __future__ import annotations

import json
import time
from datetime import timedelta

import pytest

from holt.report import Assessment, Claim, EntryPoint, Verdict
from holt.tui import store
from holt.types import T_CUTOFF, EvidenceRecord


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


# ─── the run's trace ────────────────────────────────────────────────────────


def _trace() -> list:
    from holt.tui import events

    return [
        events.RunStarted(repo="owner/name", replayed=True),
        events.EvidenceLoaded(count=1231, window="pre_t", cutoff=T_CUTOFF),
        events.StageStarted(stage="classify", model="gpt-5-mini-2025-08-07"),
        events.ToolResponse(stage="classify", payload={"repo_kind": "real_software"}),
        events.FindingEmitted(
            stage="classify",
            field="repo_kind",
            value="real_software",
            evidence_ids=("repo:owner/name:meta",),
        ),
        events.StageFinished(stage="classify", seconds=0.4, summary="real_software"),
        events.EvidenceResolved(evidence_id="repo:owner/name:meta", resolved=True),
        events.FindingDropped(
            field="onboarding", value="absent", cited=("pr:owner/name#1:opened",)
        ),
        events.UsageUpdated(input_tokens=12, output_tokens=34, cost_usd=0.5),
        events.RunFinished(assessment=make(), trace=None),
    ]


def test_the_trace_survives_the_process_that_produced_it(tmp_path):
    """A stored assessment used to keep its claims and lose the run behind
    them, which is the only record of what was dropped and why."""
    from holt.tui import events

    keep = store.Store(root=tmp_path)
    keep.save(entry(events=_trace()))

    restored = store.Store(root=tmp_path).all()[0].events
    kinds = [type(e).__name__ for e in restored]

    # `ToolResponse` is a whole model payload nothing renders, and
    # `RunFinished` carries the assessment the entry already holds.
    assert "ToolResponse" not in kinds
    assert "RunFinished" not in kinds
    assert kinds == [
        "RunStarted",
        "EvidenceLoaded",
        "StageStarted",
        "FindingEmitted",
        "StageFinished",
        "EvidenceResolved",
        "FindingDropped",
        "UsageUpdated",
    ]

    loaded = restored[1]
    assert loaded.count == 1231 and loaded.cutoff == T_CUTOFF
    emitted = restored[3]
    assert emitted.evidence_ids == ("repo:owner/name:meta",)
    dropped = restored[6]
    assert isinstance(dropped, events.FindingDropped)
    assert dropped.cited == ("pr:owner/name#1:opened",)


def test_an_event_this_build_does_not_know_is_skipped_not_fatal(tmp_path):
    """Same rule as the rest of the store: a file written by a build that
    knows more than this one still opens, minus the part it cannot read."""
    keep = store.Store(root=tmp_path)
    keep.save(entry(events=_trace()))

    path = next(tmp_path.glob("*.json"))
    raw = json.loads(path.read_text())
    raw["events"].append({"event": "SomethingLearnedLater", "detail": "?"})
    raw["events"].append("not even a dict")
    path.write_text(json.dumps(raw))

    restored = store.Store(root=tmp_path).all()
    assert len(restored) == 1
    assert len(restored[0].events) == 8


def test_a_finding_that_will_not_serialise_does_not_lose_the_assessment(tmp_path):
    """A finding's value is whatever a model put in a field. History is a
    convenience; it must never be the reason a report fails to save."""
    from holt.tui import events

    keep = store.Store(root=tmp_path)
    keep.save(
        entry(
            events=[
                events.FindingEmitted(
                    stage="classify", field="repo_kind", value=object()
                )
            ]
        )
    )

    restored = store.Store(root=tmp_path).all()
    assert restored[0].assessment.repo == "owner/name"
    assert "object object" in restored[0].events[0].value


# ─── the records behind the claims ──────────────────────────────────────────


def record(evidence_id: str = "repo:x:meta") -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        source="github",
        url="https://github.com/owner/name",
        timestamp=T_CUTOFF - timedelta(days=3),
        payload={"stars": 4211, "title": "the thread this claim came from"},
    )


def test_the_records_behind_the_claims_survive_the_process(tmp_path):
    """A claim is only checkable while the record under it can be read.

    A live run's records are held in the process that crawled them and on no
    disk anywhere, so they are stored with the assessment. Reopening it a day
    later must answer the same id with the same record.
    """
    keep = store.Store(root=tmp_path)
    keep.save(entry(mode="live", evidence=[record(), record("issue:x#1")]))

    got = store.Store(root=tmp_path).all()[0]
    assert [r.evidence_id for r in got.evidence] == ["repo:x:meta", "issue:x#1"]
    assert got.evidence[0].payload["stars"] == 4211
    assert got.evidence[0].timestamp == T_CUTOFF - timedelta(days=3)
    assert got.evidence[0].source == "github"


def test_a_damaged_record_is_skipped_not_fatal(tmp_path):
    """Same rule as everywhere else here: the report is still worth opening,
    and the inspector already has a sentence for an id it cannot look up."""
    keep = store.Store(root=tmp_path)
    saved = keep.save(entry(mode="live", evidence=[record()]))
    raw = json.loads(saved.path.read_text())
    raw["evidence"].append({"evidence_id": "issue:x#2"})  # no timestamp
    raw["evidence"].append("not a record at all")
    saved.path.write_text(json.dumps(raw))

    got = store.Store(root=tmp_path).all()[0]
    assert [r.evidence_id for r in got.evidence] == ["repo:x:meta"]


def test_an_assessment_stored_before_records_were_kept_still_loads(tmp_path):
    keep = store.Store(root=tmp_path)
    saved = keep.save(entry(mode="live", evidence=[record()]))
    raw = json.loads(saved.path.read_text())
    del raw["evidence"]
    saved.path.write_text(json.dumps(raw))

    got = store.Store(root=tmp_path).all()[0]
    assert got.evidence == []
    assert got.assessment.verdict is Verdict.VIABLE
