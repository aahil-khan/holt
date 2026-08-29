"""A -> B -> C -> D -> verdict -> E.

The ordering that matters: the verdict is computed *before* narration and handed
to Stage E as an input it cannot alter. If the report and verdict.py could
disagree, the determinism claim would be worth nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from holt.agent import stages
from holt.agent.findings import Finding, Findings
from holt.agent.signals import Signals, build_threads, compute
from holt.agent.verdict import classify as decide
from holt.agent.verify import verify
from holt.evidence.provider import EvidenceProvider
from holt.model import ModelClient
from holt.report import Assessment, Claim, Verdict


@dataclass(slots=True)
class Trace:
    """What happened, for the demo and the trajectory record."""

    signals: Signals
    before_verification: int = 0
    after_verification: int = 0
    dropped: list[Finding] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)


def analyze(
    repo: str, provider: EvidenceProvider, model: ModelClient
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

    verdict, rules = decide(findings, signals)
    summary = stages.narrate(
        repo, verdict.value, rules, findings, signals.as_dict(), model
    )

    # The evidence list is built from verified findings, not written by the
    # model. Stage E supplies prose; it cannot introduce a citation.
    claims: list[Claim] = []
    for item in findings:
        if item.field == "thread_outcome":
            text = f"{item.value['signal']}: {item.value['outcome']} — “{item.value['quote'][:160]}”"
        else:
            text = f"{item.field} = {item.value}" + (f" ({item.note})" if item.note else "")
        claims.append(Claim(text=text[:400], evidence_id=item.evidence_ids[0]))

    assessment = Assessment(
        repo=repo,
        verdict=verdict,
        summary=summary,
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
