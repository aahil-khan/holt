"""The shared output shape.

The baseline solution and the full pipeline must produce the same thing, or the
comparison is not the same task. Both emit an Assessment; only the method of
arriving at one differs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    """Deliberately three-valued.

    A repository nobody has tried to contribute to is not the same as one that
    turns contributors away, and flattening them would hide the distinction the
    whole project is about. Saying so is a valid answer, not a failure.
    """

    VIABLE = "viable"
    NOT_VIABLE = "not_viable"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class Claim:
    """A statement with the evidence id that backs it.

    Stage D drops any claim whose id does not resolve. A claim without a
    resolvable id never reaches the reader.
    """

    text: str
    evidence_id: str | None = None


@dataclass(slots=True)
class Assessment:
    repo: str
    verdict: Verdict
    summary: str
    claims: list[Claim] = field(default_factory=list)
    method: str = "holt"
    replayed: bool = False

    def render(self) -> str:
        lines = [f"# {self.repo}", ""]
        if self.replayed:
            lines += [
                "> Replaying recorded model output. No model was called for this run.",
                "",
            ]
        lines += [f"**Verdict:** {self.verdict.value}", f"**Method:** {self.method}", ""]
        lines += [self.summary, ""]
        if self.claims:
            lines.append("## Evidence")
            for claim in self.claims:
                where = f" — `{claim.evidence_id}`" if claim.evidence_id else ""
                lines.append(f"- {claim.text}{where}")
        return "\n".join(lines).rstrip() + "\n"
