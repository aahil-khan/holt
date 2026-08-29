"""L1 — the qualifying label: outsider merges that were actually contributions.

L0 counts any merged pull request from an outsider. That rewards a repository
where merged work means appending one line to a manifest exactly as much as one
where it means changing software. L1 adds the filters L0 is missing, as a funnel
whose stages are counted separately so each one's effect is auditable rather
than folded into a single number.

Stages, applied in order to post-cutoff pull requests by outsiders:

  attempts      opened by someone not established before the cutoff
  human         author is not a bot
  merged        actually merged
  substantive   the diff is not docs-only, a single data-file entry, or a
                one-line change to a single file
  reviewed      a human other than the author reviewed or commented

Two filters, `substantive` and `reviewed`, are separable on purpose: which one
carries the discrimination is an empirical question, so both are measured
independently before either is trusted.

This module must not import from holt.agent. A test enforces that.
"""

from __future__ import annotations

from collections.abc import Iterable

from holt.types import EvidenceRecord

INSUFFICIENT_EVIDENCE = "insufficient_evidence"

DOC_EXTENSIONS = {".md", ".rst", ".adoc", ".txt"}
DOC_DIRS = ("docs/", "doc/", "website/", ".github/")
DATA_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".xml", ".lock"}

# A single file changed by ten lines or fewer is a manifest entry, a version
# bump or a typo fix. Real ones exist, which is why this is measured separately
# rather than folded silently into the headline number.
TRIVIAL_LINES = 10


def pr_key(evidence_id: str) -> str:
    """`pr:owner/name#12:review:3` -> `pr:owner/name#12`."""
    return ":".join(evidence_id.split(":")[:2])


def _ext(path: str) -> str:
    _, _, tail = path.rpartition("/")
    return tail[tail.rfind(".") :].lower() if "." in tail else ""


def is_docs_only(files: list[str]) -> bool:
    if not files:
        return False
    return all(_ext(f) in DOC_EXTENSIONS or f.startswith(DOC_DIRS) for f in files)


def is_data_only(files: list[str]) -> bool:
    """Every changed file is a data file, so nothing executable changed.

    First written as "exactly one data file", which let 99 of is-a-dev/register's
    368 merges through: a domain registration there touches two files, the domain
    entry and a provider verification record. Counting files was the wrong test;
    what matters is that none of them is source.
    """
    return bool(files) and all(_ext(f) in DATA_EXTENSIONS for f in files)


def is_trivial(changed: int, additions: int, deletions: int) -> bool:
    return changed == 1 and (additions + deletions) <= TRIVIAL_LINES


def is_substantive(payload: dict) -> bool:
    files = payload.get("files") or []
    changed = payload.get("changed_files") or 0
    if is_docs_only(files):
        return False
    if is_data_only(files):
        return False
    if is_trivial(changed, payload.get("additions") or 0, payload.get("deletions") or 0):
        return False
    return True


def established_authors(pre_t: Iterable[EvidenceRecord]) -> set[str]:
    """Authors with a pull request merged before the cutoff. Pre-cutoff data only."""
    return {r.payload["author"] for r in pre_t if r.evidence_id.endswith(":merged")}


def score(pre_t: Iterable[EvidenceRecord], post_t: Iterable[EvidenceRecord]) -> dict:
    insiders = established_authors(pre_t)
    post_t = list(post_t)

    opened = {
        pr_key(r.evidence_id): r
        for r in post_t
        if r.evidence_id.endswith(":opened")
    }
    merged = {pr_key(r.evidence_id) for r in post_t if r.evidence_id.endswith(":merged")}

    # Human engagement on a pull request, by anyone who is not its author and
    # not a bot. Rubber-stamped and auto-merged entries leave no such trace.
    engaged: dict[str, set[str]] = {}
    for r in post_t:
        if ":review:" not in r.evidence_id and ":comment:" not in r.evidence_id:
            continue
        key = pr_key(r.evidence_id)
        if r.payload.get("author_is_bot"):
            continue
        engaged.setdefault(key, set()).add(r.payload.get("author", ""))

    attempts = [k for k, r in opened.items() if r.payload.get("author") not in insiders]
    human = [k for k in attempts if not opened[k].payload.get("author_is_bot")]
    merged_h = [k for k in human if k in merged]
    substantive = [k for k in merged_h if is_substantive(opened[k].payload)]
    reviewed = [
        k for k in substantive if engaged.get(k, set()) - {opened[k].payload.get("author")}
    ]

    contributors = {opened[k].payload.get("author") for k in reviewed}
    return {
        "funnel": {
            "attempts": len(attempts),
            "human": len(human),
            "merged": len(merged_h),
            "substantive": len(substantive),
            "reviewed": len(reviewed),
        },
        "qualifying_merges": len(reviewed),
        "distinct_qualifying_contributors": len(contributors),
        "qualifying_rate": (len(reviewed) / len(human)) if human else None,
        "bucket": INSUFFICIENT_EVIDENCE if not human else "scored",
    }
