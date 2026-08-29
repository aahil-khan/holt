"""Core types shared by the evidence layer, the agent stages, and the eval harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# The temporal holdout boundary.
#
# The agent may only see records at or before T; labels are computed only from
# records after T. T sits just past the model's May 2026 training cutoff so that
# the label window (Jun-Aug 2026) falls outside training data entirely. Moving T
# earlier would drag the label window *into* training data, which is the leak
# that actually matters.
T_CUTOFF = datetime(2026, 6, 1, tzinfo=UTC)


class Window(str, Enum):
    """Which side of the holdout a provider is permitted to read."""

    PRE_T = "pre_t"
    POST_T = "post_t"


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """A single retrieved fact, addressable by a stable id.

    Every claim Holt makes must cite an ``evidence_id`` that resolves back to one
    of these. Stage D drops any finding whose id does not.
    """

    evidence_id: str
    source: str
    url: str
    timestamp: datetime
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError(
                f"{self.evidence_id}: timestamp must be timezone-aware; "
                "naive datetimes cannot be compared against the holdout boundary"
            )
        if not self.evidence_id:
            raise ValueError("evidence_id must be non-empty")
