"""The verdict is deterministic, so it can be tested exhaustively rather than sampled."""

from __future__ import annotations

from holt.agent.findings import Findings
from holt.agent.signals import Signals
from holt.agent.verdict import classify
from holt.report import Verdict


def signals(**over) -> Signals:
    base = dict(
        total_threads=20,
        outsider_threads=10,
        outsider_merged=4,
        outsider_ignored=1,
        median_first_response_hours=12.0,
        bot_share=0.1,
        distinct_outsider_authors=4,
        distinct_merged_authors=4,
        reviewed_share=0.5,
        merge_rate=0.4,
    )
    base.update(over)
    return Signals(**base)


def findings(**fields) -> Findings:
    f = Findings()
    for k, v in fields.items():
        f.add(k, v, evidence_ids=("repo:a/b:readme",))
    return f


def test_a_healthy_repo_is_viable():
    v, trace = classify(findings(repo_kind="real_software"), signals())
    assert v is Verdict.VIABLE and trace


def test_registries_are_not_viable_however_active():
    """The whole point: high merge volume must not rescue a registry."""
    v, trace = classify(
        findings(repo_kind="registry"),
        signals(outsider_merged=400, distinct_outsider_authors=150),
    )
    assert v is Verdict.NOT_VIABLE
    assert "not a software contribution" in trace[0]


def test_archived_beats_every_other_signal():
    v, _ = classify(findings(repo_kind="real_software", is_archived=True), signals())
    assert v is Verdict.NOT_VIABLE


def test_mirrors_are_not_viable():
    assert classify(findings(repo_kind="mirror"), signals())[0] is Verdict.NOT_VIABLE


def test_no_attempts_is_insufficient_not_hostile():
    v, trace = classify(findings(repo_kind="real_software"), signals(outsider_threads=0))
    assert v is Verdict.INSUFFICIENT_EVIDENCE
    assert "nothing to judge" in trace[0]


def test_ignored_attempts_with_no_merges_is_not_viable():
    v, _ = classify(
        findings(repo_kind="real_software"),
        signals(outsider_threads=10, outsider_merged=0, outsider_ignored=9),
    )
    assert v is Verdict.NOT_VIABLE


def test_one_person_merging_repeatedly_is_not_a_pattern():
    v, _ = classify(
        findings(repo_kind="real_software"),
        signals(outsider_merged=5, distinct_outsider_authors=1),
    )
    assert v is Verdict.INSUFFICIENT_EVIDENCE


def test_a_response_slower_than_a_week_blocks_viable():
    v, trace = classify(
        findings(repo_kind="real_software"), signals(median_first_response_hours=400.0)
    )
    assert v is Verdict.INSUFFICIENT_EVIDENCE
    assert any("exceeds" in t for t in trace)


def test_classify_is_pure():
    """Same inputs, same answer -- the property the reproduction claim rests on."""
    f, s = findings(repo_kind="real_software"), signals()
    assert classify(f, s) == classify(f, s)


def test_a_handful_of_ignored_attempts_is_not_proof_of_hostility():
    """Four ignored pull requests out of four is four data points, not a policy."""
    v, trace = classify(
        findings(repo_kind="real_software"),
        signals(outsider_threads=4, outsider_merged=0, outsider_ignored=4,
                median_first_response_hours=None, distinct_outsider_authors=3),
    )
    assert v is Verdict.INSUFFICIENT_EVIDENCE
    assert any("too thin" in t for t in trace)


def test_many_ignored_attempts_still_reads_as_hostile():
    v, _ = classify(
        findings(repo_kind="real_software"),
        signals(outsider_threads=40, outsider_merged=0, outsider_ignored=36),
    )
    assert v is Verdict.NOT_VIABLE


def test_a_rubber_stamp_is_rejected_even_when_everything_else_looks_healthy():
    """Landing easily and drawing no review is the registry signature."""
    v, trace = classify(
        findings(repo_kind="real_software"),
        signals(reviewed_share=0.09, merge_rate=0.69),
    )
    assert v is Verdict.NOT_VIABLE
    assert any("waved through unread" in t for t in trace)


def test_unreviewed_but_hard_to_land_is_not_a_rubber_stamp():
    """nixpkgs merges without visible review because review happened elsewhere.

    This is the case that killed the first rejection rule, so it has a test.
    """
    v, _ = classify(
        findings(repo_kind="real_software"),
        signals(reviewed_share=0.09, merge_rate=0.15),
    )
    assert v is Verdict.VIABLE


def test_reviewed_and_easy_to_land_is_a_welcoming_project():
    v, _ = classify(
        findings(repo_kind="real_software"),
        signals(reviewed_share=0.80, merge_rate=0.75),
    )
    assert v is Verdict.VIABLE


def test_the_time_budget_changes_what_counts_as_too_slow():
    """A five-day median reply is fine with three months and fatal with three days."""
    s = signals(median_first_response_hours=120.0)
    assert classify(findings(repo_kind="real_software"), s, contributor_days=90)[0] is Verdict.VIABLE
    v, trace = classify(findings(repo_kind="real_software"), s, contributor_days=3)
    assert v is Verdict.INSUFFICIENT_EVIDENCE
    assert any("3-day budget" in t for t in trace)
