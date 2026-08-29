"""Stage D — the only stage that removes things.

Every finding carries the evidence ids that support it. This resolves each one
against the provider. A finding whose evidence does not resolve is **dropped,
not softened**: the alternative is prose that hedges around a claim nobody can
check, which is how unsupported statements survive into reports.

No model runs here. Resolution is a lookup.
"""

from __future__ import annotations

from holt.agent.findings import Finding, Findings
from holt.evidence.provider import EvidenceProvider


def verify(findings: Findings, provider: EvidenceProvider) -> tuple[Findings, list[Finding]]:
    """Return (surviving findings, dropped findings)."""
    kept, dropped = Findings(), []
    for item in findings:
        if not item.evidence_ids:
            dropped.append(item)
            continue
        resolved = tuple(e for e in item.evidence_ids if provider.resolve(e) is not None)
        if not resolved:
            dropped.append(item)
            continue
        kept.add(item.field, item.value, resolved, item.note)
    return kept, dropped
