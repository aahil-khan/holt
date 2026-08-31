"""The holdout boundary must be an assertion, not a convention.

These tests exist because the measured claim is only worth as much as the
separation between what the agent reads and what the labels are computed from.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from holt.evidence import ContaminationError, EvidenceProvider
from holt.types import T_CUTOFF, EvidenceRecord, Window

BEFORE = T_CUTOFF - timedelta(days=1)
AFTER = T_CUTOFF + timedelta(days=1)


def record(evidence_id: str, timestamp: datetime) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        source="github",
        url=f"https://github.com/example/repo/pull/{evidence_id}",
        timestamp=timestamp,
        payload={},
    )


class StubProvider(EvidenceProvider):
    """A provider that returns whatever it is handed, including bad records."""

    def __init__(self, window: Window, records: list[EvidenceRecord]) -> None:
        super().__init__(window)
        self._records = records

    def _fetch_raw(self, request: str, /, **params: object) -> list[EvidenceRecord]:
        return self._records

    def _resolve_raw(self, evidence_id: str) -> EvidenceRecord | None:
        return next((r for r in self._records if r.evidence_id == evidence_id), None)


def test_agent_side_rejects_post_cutoff_record():
    provider = StubProvider(Window.PRE_T, [record("pr:1", AFTER)])
    with pytest.raises(ContaminationError, match="must not see it"):
        provider.fetch("pulls")


def test_label_side_rejects_pre_cutoff_record():
    provider = StubProvider(Window.POST_T, [record("pr:1", BEFORE)])
    with pytest.raises(ContaminationError, match="labels must not be computed"):
        provider.fetch("pulls")


def test_cutoff_is_inclusive_on_the_agent_side():
    """T itself belongs to the agent's view; labels start strictly after it."""
    assert StubProvider(Window.PRE_T, [record("pr:1", T_CUTOFF)]).fetch("pulls")
    with pytest.raises(ContaminationError):
        StubProvider(Window.POST_T, [record("pr:1", T_CUTOFF)]).fetch("pulls")


def test_resolve_enforces_the_boundary_too():
    """Stage D resolves ids one at a time; that path is not a way around the check."""
    provider = StubProvider(Window.PRE_T, [record("pr:1", AFTER)])
    with pytest.raises(ContaminationError):
        provider.resolve("pr:1")


def test_unresolvable_id_returns_none_rather_than_raising():
    """Stage D drops findings whose evidence does not resolve; that is not an error."""
    provider = StubProvider(Window.PRE_T, [record("pr:1", BEFORE)])
    assert provider.resolve("pr:missing") is None


def test_a_subclass_cannot_bypass_the_check():
    """The public methods own the assertion, so overriding _fetch_raw cannot skip it."""

    class Sneaky(StubProvider):
        def _fetch_raw(self, request: str, /, **params: object) -> list[EvidenceRecord]:
            return [record("pr:leak", AFTER)]

    with pytest.raises(ContaminationError):
        Sneaky(Window.PRE_T, []).fetch("pulls")


def test_naive_timestamps_are_rejected_at_construction():
    """A naive datetime cannot be compared against the boundary, so it never enters."""
    with pytest.raises(ValueError, match="timezone-aware"):
        EvidenceRecord("pr:1", "github", "https://x", datetime(2026, 1, 1), {})


def test_live_provider_defaults_to_now_not_the_benchmark_cutoff():
    """T = 2026-06-01 is an evaluation device, not a product setting.

    A live provider constructed without an explicit cutoff must read up to now:
    the old default of T silently reported any repository created after June as
    having no history at all, live token in hand. The evaluation capture passes
    T explicitly, which is where that decision belongs.
    """
    from datetime import UTC

    from holt.evidence.github_graphql import LiveGitHubIssueProvider, LiveGitHubProvider
    from holt.types import T_CUTOFF

    dummy_transport = object()
    for cls in (LiveGitHubProvider, LiveGitHubIssueProvider):
        provider = cls(Window.PRE_T, transport=dummy_transport)
        assert provider.cutoff > T_CUTOFF
        assert (datetime.now(UTC) - provider.cutoff).total_seconds() < 60
