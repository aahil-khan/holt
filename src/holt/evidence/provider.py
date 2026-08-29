"""The single chokepoint every fact passes through.

Both GitHub and web results resolve through this interface, in one of two
implementations: live (real network) or fixture (committed JSON). That buys
three things at once:

* fixture mode makes the eval reproducible with no token and no rate limits
* live mode is the real product
* one place asserts the holdout boundary, so contamination is structurally
  impossible rather than a matter of discipline

Subclasses implement ``_fetch_raw`` / ``_resolve_raw``. They cannot skip the
boundary check: the public methods own it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime

from holt.types import T_CUTOFF, EvidenceRecord, Window


class ContaminationError(AssertionError):
    """A provider returned a record from the wrong side of the holdout.

    This is a bug, not a condition to handle. It means the agent was about to
    see post-cutoff data, or a label was about to be computed from pre-cutoff
    data. Either invalidates the measured claim.
    """


class EvidenceProvider(ABC):
    def __init__(self, window: Window, cutoff: datetime = T_CUTOFF) -> None:
        self.window = window
        self.cutoff = cutoff

    def fetch(self, request: str, /, **params: object) -> list[EvidenceRecord]:
        records = list(self._fetch_raw(request, **params))
        for record in records:
            self._assert_in_window(record)
        return records

    def resolve(self, evidence_id: str) -> EvidenceRecord | None:
        """Return the record behind an id, or None if it does not resolve.

        Stage D uses the None case to drop findings rather than soften them.
        """
        record = self._resolve_raw(evidence_id)
        if record is not None:
            self._assert_in_window(record)
        return record

    def _assert_in_window(self, record: EvidenceRecord) -> None:
        if self.window is Window.PRE_T and record.timestamp > self.cutoff:
            raise ContaminationError(
                f"{record.evidence_id} is dated {record.timestamp.isoformat()}, "
                f"after the cutoff {self.cutoff.isoformat()}; the agent must not see it"
            )
        if self.window is Window.POST_T and record.timestamp <= self.cutoff:
            raise ContaminationError(
                f"{record.evidence_id} is dated {record.timestamp.isoformat()}, "
                f"at or before the cutoff {self.cutoff.isoformat()}; "
                "labels must not be computed from it"
            )

    @abstractmethod
    def _fetch_raw(self, request: str, /, **params: object) -> Iterable[EvidenceRecord]: ...

    @abstractmethod
    def _resolve_raw(self, evidence_id: str) -> EvidenceRecord | None: ...
