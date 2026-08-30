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


@dataclass(frozen=True, slots=True)
class EntryPoint:
    """One suggested place to start, with the issue it points at.

    Carried separately from `Claim` because it is a *suggestion* rather than a
    statement of fact, and the two must not be rendered as if they had the same
    standing. Claims are verified against evidence; this is a ranking whose
    measured precision is printed next to it.
    """

    evidence_id: str
    first_step: str
    why: str = ""


@dataclass(slots=True)
class Assessment:
    repo: str
    verdict: Verdict
    summary: str
    claims: list[Claim] = field(default_factory=list)
    method: str = "holt"
    replayed: bool = False
    entry_points: list[EntryPoint] = field(default_factory=list)

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
        if self.entry_points:
            # The disclaimer is emitted by the renderer, not by the caller, so
            # there is no code path that prints a ranking without the number that
            # says how well it works. A test holds this.
            from holt.agent.entry import DISCLAIMER

            lines += ["", "## Where to start", "", DISCLAIMER, ""]
            for point in self.entry_points:
                lines.append(f"- **{point.first_step}** — `{point.evidence_id}`")
                if point.why:
                    lines.append(f"  {point.why}")
        return "\n".join(lines).rstrip() + "\n"
