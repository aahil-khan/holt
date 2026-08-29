"""Stage D is the only stage that can remove a claim, so it is tested directly.

On a clean run it drops nothing, which is the correct outcome and also means the
rendered trajectories cannot demonstrate the behaviour. These tests do.
"""

from __future__ import annotations

from datetime import timedelta

from holt.agent.findings import Findings
from holt.agent.verify import verify
from holt.evidence.fixtures import FixtureProvider, write_fixture
from holt.types import T_CUTOFF, EvidenceRecord, Window

BEFORE = T_CUTOFF - timedelta(days=1)


def provider(tmp_path, ids):
    write_fixture(
        "a/b",
        Window.PRE_T,
        [EvidenceRecord(i, "github", "https://x", BEFORE, {"author": "sam"}) for i in ids],
        root=tmp_path,
    )
    p = FixtureProvider(Window.PRE_T, root=tmp_path)
    p.fetch("a/b")
    return p


def test_a_finding_with_no_resolving_evidence_is_dropped(tmp_path):
    p = provider(tmp_path, ["pr:a/b#1:opened"])
    f = Findings()
    f.add("repo_kind", "real_software", evidence_ids=("pr:a/b#999:opened",))
    kept, dropped = verify(f, p)
    assert len(kept) == 0 and len(dropped) == 1
    assert dropped[0].field == "repo_kind"


def test_an_unresolvable_citation_is_stripped_but_the_finding_survives(tmp_path):
    """Partial support is still support; the bad citation must not travel with it."""
    p = provider(tmp_path, ["pr:a/b#1:opened"])
    f = Findings()
    f.add("repo_kind", "registry", evidence_ids=("pr:a/b#1:opened", "pr:a/b#999:opened"))
    kept, dropped = verify(f, p)
    assert len(kept) == 1 and not dropped
    assert kept.items[0].evidence_ids == ("pr:a/b#1:opened",)


def test_a_finding_citing_nothing_at_all_is_dropped(tmp_path):
    """An uncited claim is exactly what this stage exists to remove."""
    f = Findings()
    f.add("repo_kind", "real_software")
    kept, dropped = verify(f, provider(tmp_path, ["pr:a/b#1:opened"]))
    assert len(kept) == 0 and len(dropped) == 1


def test_verification_never_rewrites_a_surviving_value(tmp_path):
    """It removes; it does not soften. A survivor comes through unchanged."""
    p = provider(tmp_path, ["repo:a/b:readme"])
    f = Findings()
    f.add("onboarding", "substantive", evidence_ids=("repo:a/b:readme",), note="because")
    kept, _ = verify(f, p)
    assert kept.items[0].value == "substantive"
    assert kept.items[0].note == "because"
