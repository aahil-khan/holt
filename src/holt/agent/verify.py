"""Stage D — the only stage that removes things.

Two mechanical checks, both of which delete rather than soften.

**Resolution.** Every finding carries the evidence ids that support it. This
resolves each one against the provider. A finding whose evidence does not
resolve is dropped: the alternative is prose that hedges around a claim nobody
can check, which is how unsupported statements survive into reports.

**Quotation.** A claim can cite a pull request that exists and still put words
in its mouth. `eval/evidence_integrity.py` has measured that gap since Iteration
11 -- it is the difference between an id that resolves and evidence that says
what the claim says -- and the check here is the same function the metric uses,
so the number the eval reports and the guarantee the reader gets cannot drift
apart. A quote that is not in the record takes its claim with it, for the same
reason: keeping the outcome while deleting the fabricated quote is softening.

No model runs here. Resolution is a lookup and quotation is string matching.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from holt.agent.findings import Finding, Findings
from holt.evidence.provider import EvidenceProvider
from holt.types import EvidenceRecord

# A quote counts as present if a long-enough run of its words appears verbatim
# in the record. Models normalise whitespace and clip mid-sentence; penalising
# that would measure formatting rather than fidelity.
SHINGLE = 6

# `stages._render_thread` prefixes every reply with the speaker -- `[AUTHOR]`,
# `[octocat]` -- and a model quoting that reply routinely copies the prefix.
# Nobody said those words: they are ours. Stripping the tag before matching
# stops the guard blaming the model for our own formatting, which is the same
# lesson NO_REPLIES taught. What is left still has to be in the record, and a
# "quote" that is nothing *but* our scaffolding quotes nothing at all.
SPEAKER_TAG = re.compile(r"^\s*\[[^\]]{1,40}\]\s*")


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


# Punctuation is folded away with the whitespace, for the same reason. A model
# that quotes ``[`nixpkgs-review`]``(...) as ``[`nixpkgs-review`].`` -- closing a
# markdown link it truncated -- has quoted the thread; rejecting it would be
# measuring punctuation. What survives folding is the words, and those still
# have to be the record's words, in the record's order.
_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)


def normalise(text: str) -> str:
    return " ".join(_NON_WORD.sub(" ", (text or "").lower()).split())


def spoken_part(quote: str) -> str:
    """The words attributed to a person, with our speaker tag removed."""
    return SPEAKER_TAG.sub("", quote or "", count=1).strip()


def quote_supported(quote: str, haystack: str) -> bool:
    q, h = normalise(quote), normalise(haystack)
    if not q:
        return False
    words = q.split()
    if len(words) <= SHINGLE:
        return q in h
    return any(
        " ".join(words[i : i + SHINGLE]) in h for i in range(len(words) - SHINGLE + 1)
    )


def spoken_words(records: Iterable[EvidenceRecord]) -> dict[str, str]:
    """Everything said anywhere on each pull request, keyed by its number.

    Quotes come from reviews and comments, which live in their own records
    (`#12:review:0`, `#12:comment:1`) rather than in the `:opened` record a
    Stage C finding cites. Checking a quote against the cited record alone would
    reject every real quotation, so the haystack is the whole thread.
    """
    said: dict[str, list[str]] = {}
    for record in records:
        number = _pr_number(record.evidence_id)
        if number is None:
            continue
        payload = record.payload
        text = f"{payload.get('title') or ''} {payload.get('body') or ''}"
        if text.strip():
            said.setdefault(number, []).append(text)
    return {k: " ".join(v) for k, v in said.items()}


def _pr_number(evidence_id: str) -> str | None:
    if "#" not in evidence_id:
        return None
    return evidence_id.split("#")[-1].split(":")[0]


def check_quotes(
    findings: Findings, records: Iterable[EvidenceRecord]
) -> tuple[list[Finding], list[Finding]]:
    """Split findings into (quoting the record, putting words in its mouth).

    Findings that quote nothing pass through untouched -- there is nothing to
    check and nothing to accuse them of.
    """
    said = spoken_words(records)
    supported, invented = [], []
    for item in findings:
        raw = item.value.get("quote", "") if isinstance(item.value, dict) else ""
        if not raw or not str(raw).strip():
            supported.append(item)
            continue
        quote = spoken_part(str(raw))
        if not quote:
            # Entirely our own scaffolding. There is no quotation here to check,
            # and printing `“[octocat]”` to a reader is not evidence of anything.
            invented.append(item)
            continue
        number = _pr_number(item.evidence_ids[0]) if item.evidence_ids else None
        if number is not None and quote_supported(quote, said.get(number, "")):
            supported.append(item)
        else:
            invented.append(item)
    return supported, invented
