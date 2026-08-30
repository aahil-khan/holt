"""The shared output shape.

The baseline solution and the full pipeline must produce the same thing, or the
comparison is not the same task. Both emit an Assessment; only the method of
arriving at one differs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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


# The verdict word alone tells a reader almost nothing. These say what it means
# for the decision they are actually making.
VERDICT_HEADLINES = {
    Verdict.VIABLE: "Worth your time",
    Verdict.NOT_VIABLE: "Not worth your time",
    Verdict.INSUFFICIENT_EVIDENCE: "Not enough evidence to say",
}


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
    # Added, never replacing: `summary` still holds the prose. A reader deciding
    # where to spend a week needs the answer before the reasoning, and the rules
    # are printed because "which rule fired" is a question a chat answer cannot
    # be asked.
    bottom_line: str = ""
    limits: str = ""
    rules: list[str] = field(default_factory=list)
    contributor_days: int = 7
    # Rendered markdown lines from `holt.agent.landing`. Arithmetic over the file
    # lists we already crawl; the model never sees or writes this section.
    landing: list[str] = field(default_factory=list)
    # The date evidence was cut at. Stated in the output because a reader cannot
    # otherwise tell a quiet repository from one whose recent months were excluded.
    as_of: datetime | None = None

    def render(self) -> str:
        lines = [f"# {self.repo}", ""]
        if self.replayed:
            lines += [
                "> Replaying recorded model output. No model was called for this run.",
                "",
            ]
        budget = f"for a contributor with {self.contributor_days} day"
        budget += "" if self.contributor_days == 1 else "s"
        lines += [f"**{VERDICT_HEADLINES[self.verdict]}** — {budget}.", ""]
        if self.as_of:
            lines += [f"*Evidence up to {self.as_of.date().isoformat()}.*", ""]
        if self.bottom_line:
            lines += [self.bottom_line, ""]
        if self.summary:
            lines += ["## What the evidence shows", "", self.summary, ""]
        if self.rules:
            # The deterministic part, shown rather than described. `verdict.py`
            # decided this and the prose above could not have changed it.
            lines += ["## What decided it", ""]
            lines += [f"- {rule}" for rule in self.rules]
            lines.append("")
        if self.limits:
            lines += ["## What could not be determined", "", self.limits, ""]
        if self.landing:
            lines += self.landing + [""]
        if self.claims:
            lines += ["## Evidence", ""]
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
        lines += ["", f"*{self.method}*"]
        return "\n".join(lines).rstrip() + "\n"
