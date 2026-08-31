"""A -> B -> C -> D -> verdict -> E.

The ordering that matters: the verdict is computed *before* narration and handed
to Stage E as an input it cannot alter. If the report and verdict.py could
disagree, the determinism claim would be worth nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from holt.agent import landing, stages
from holt.agent.findings import Finding, Findings
from holt.agent.signals import Signals, build_threads, compute
from holt.agent.verdict import classify as decide
from holt.agent.verdict import contested_kind
from holt.agent.verify import check_quotes, verify
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
    # Findings whose id resolved but whose quotation is not in the record.
    invented: list[Finding] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)


def analyze(
    repo: str,
    provider: EvidenceProvider,
    model: ModelClient,
    contributor_days: int = 7,
    as_of: datetime | None = None,
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

    # `repo_kind` is the only model-derived field that can decide the answer by
    # itself, and Stage D cannot check it -- an id resolving says nothing about
    # whether a classification is true. Where the evidence contradicts the
    # reason the kind rule would give, the field is dropped before it decides
    # anything and the disagreement is printed. See eval/PREREGISTRATION-4.md.
    meta = next((r for r in records if r.evidence_id.endswith(":meta")), None)
    contested = contested_kind(findings, signals, meta.payload if meta else None)
    if contested:
        findings.drop("repo_kind")

    verdict, rules = decide(findings, signals, contributor_days)
    if contested:
        rules.insert(0, contested)
    # The narration prompt is deliberately held to the signal fields that existed
    # when the trajectories were recorded. New signals reach the *verdict*
    # immediately but only reach the prose on the next re-record, so adding one
    # does not invalidate every committed trajectory and break replay for a judge.
    # When a new signal changes the outcome it still reaches the narrator, via
    # the rule trace.
    narrated_signals = {
        k: v for k, v in signals.as_dict().items()
        if k not in ("reviewed_share", "merge_rate", "merged_files_median",
                     "merged_dirs_median", "merged_with_files")
    }
    narrated = stages.narrate(
        repo, verdict.value, rules, findings, narrated_signals, model
    )

    # The evidence list is built from verified findings, not written by the
    # model. Stage E supplies prose; it cannot introduce a citation.
    #
    # The quote check runs here rather than inside Stage D on purpose. A claim
    # whose id does not resolve is worthless to everyone, narrator included, so
    # `verify` removes it before anything else runs. A claim whose id resolves
    # but whose words are not in the record is a different failure: the thread
    # is real and the outcome may well be right, and what must not reach the
    # reader is the quotation. Filtering the claim list is exactly that, and it
    # leaves the narration prompt byte-identical, so every committed trajectory
    # still replays -- a guarantee that would otherwise cost a re-record of the
    # frozen benchmark to buy.
    quoting, invented = check_quotes(findings, records)
    claims: list[Claim] = []
    for item in quoting:
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
        as_of=as_of,
        landing=landing.render(landing.compute(threads)),
        claims=claims,
        method="holt (A classify, B opportunity, C outcomes, D verify, deterministic verdict, E narrate)",
        replayed=model.replayed,
        models=list(model.usage.models),
        dropped_claims=len(dropped) + len(invented),
    )
    return assessment, Trace(
        signals=signals,
        before_verification=before,
        after_verification=len(findings),
        dropped=dropped,
        invented=invented,
        rules=rules,
    )
