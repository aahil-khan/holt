"""A -> B -> C -> D -> verdict -> E.

The ordering that matters: the verdict is computed *before* narration and handed
to Stage E as an input it cannot alter. If the report and verdict.py could
disagree, the determinism claim would be worth nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from holt.agent import landing, stages
from holt.agent.findings import Finding, Findings
from holt.agent.signals import Signals, build_threads, compute
from holt.agent.verdict import classify as decide
from holt.agent.verify import verify
from holt.evidence.provider import EvidenceProvider
from holt.model import ModelClient
from holt.report import Assessment, Claim, Verdict

MAX_CLAIM_CHARS = 240
MAX_QUOTE_CHARS = 180


def clip(text: str, limit: int) -> str:
    """Cut on a word boundary. Cutting mid-word reads as a bug, because it is one."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    head = text[:limit]
    cut = max(head.rfind(" "), head.rfind(". "))
    return (head[:cut] if cut > limit // 2 else head).rstrip(" ,;:.") + "…"


@dataclass(slots=True)
class Trace:
    """What happened, for the demo and the trajectory record."""

    signals: Signals
    before_verification: int = 0
    after_verification: int = 0
    dropped: list[Finding] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)


def analyze(
    repo: str,
    provider: EvidenceProvider,
    model: ModelClient,
    contributor_days: int = 7,
) -> tuple[Assessment, Trace]:
    records = provider.fetch(repo)
    threads = build_threads(records)
    signals = compute(threads)

    findings = Findings()
    stages.classify(repo, records, threads, model, findings)
    stages.assess_opportunity(repo, records, model, findings)
    stages.read_outcomes(repo, threads, model, findings)

    before = len(findings)
    findings, dropped = verify(findings, provider)

    verdict, rules = decide(findings, signals, contributor_days)
    # The narration prompt is deliberately held to the signal fields that existed
    # when the trajectories were recorded. New signals reach the *verdict*
    # immediately but only reach the prose on the next re-record, so adding one
    # does not invalidate every committed trajectory and break replay for a judge.
    # When a new signal changes the outcome it still reaches the narrator, via
    # the rule trace.
    narrated_signals = {
        k: v for k, v in signals.as_dict().items()
        if k not in ("reviewed_share", "merge_rate")
    }
    narrated = stages.narrate(
        repo, verdict.value, rules, findings, narrated_signals, model
    )

    # The evidence list is built from verified findings, not written by the
    # model. Stage E supplies prose; it cannot introduce a citation.
    claims: list[Claim] = []
    for item in findings:
        if item.field == "thread_outcome":
            outcome = item.value["outcome"].replace("_", " ")
            quote = (item.value.get("quote") or "").strip()
            # An empty quote used to render as a pair of quotation marks with
            # nothing between them, which reads as a bug because it is one.
            text = (f"{outcome} — “{clip(quote, MAX_QUOTE_CHARS)}”" if quote
                    else f"{outcome}, nothing said")
        else:
            text = f"{item.field.replace('_', ' ')}: {item.value}" + (
                f" — {clip(item.note, MAX_CLAIM_CHARS)}" if item.note else "")
        claims.append(Claim(text=text, evidence_id=item.evidence_ids[0]))

    assessment = Assessment(
        repo=repo,
        verdict=verdict,
        summary=narrated["what_the_evidence_shows"],
        bottom_line=narrated["bottom_line"],
        limits=narrated["what_could_not_be_determined"],
        rules=list(rules),
        contributor_days=contributor_days,
        landing=landing.render(landing.compute(threads)),
        claims=claims,
        method="holt (A classify, B opportunity, C outcomes, D verify, deterministic verdict, E narrate)",
        replayed=model.replayed,
    )
    return assessment, Trace(
        signals=signals,
        before_verification=before,
        after_verification=len(findings),
        dropped=dropped,
        rules=rules,
    )
