"""Do the reports' citations actually hold up?

Accuracy is not the only thing a report can be wrong about. A claim can point at
a pull request that does not exist, or quote words that were never said in it.
Neither shows up in a confusion matrix, and both are exactly what a reader
checking your work would catch first.

Two measures, both mechanical, both computed against the committed fixtures:

  resolution   every cited evidence id exists in the evidence the agent was given
  fidelity     every quoted string actually appears in the record it is attributed to

Holt should score near-perfectly on resolution by construction -- Stage D drops
findings whose citations do not resolve. Fidelity is *not* guaranteed by
anything: Stage D checks that an id exists, never that the evidence supports the
claim. So this measures a real gap in our own design as well as the baseline's.

Run:  PYTHONPATH=. uv run python eval/evidence_integrity.py
"""

from __future__ import annotations

import json
import pathlib
import re

from holt.agent.stages import normalise_citation
from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

# A quote is judged present if a long-enough run of its words appears verbatim in
# the record. Models normalise whitespace and clip mid-sentence, and penalising
# that would measure formatting rather than fidelity.
SHINGLE = 6
PR_REF = re.compile(r"(?:pr:[\w.\-]+/[\w.\-]+#(\d+)|#(\d{2,6}))")


def normalise(text: str) -> str:
    return " ".join((text or "").lower().split())


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


def bodies_for(records, pr_number: str) -> str:
    """Everything said anywhere on one pull request."""
    marker = f"#{pr_number}:"
    return " ".join(
        str(r.payload.get("body") or "") + " " + str(r.payload.get("title") or "")
        for r in records
        if marker in r.evidence_id
    )


def main() -> None:
    pre = FixtureProvider(Window.PRE_T)
    pools = [json.loads(pathlib.Path(f).read_text())["repos"]
             for f in ("eval/pool.json", "eval/pool2.json")]
    slugs = [s for pool in pools for s in pool]

    stats = {
        m: {"cited": 0, "resolved": 0, "quoted": 0, "supported": 0}
        for m in ("holt", "baseline_matched")
    }

    for slug in slugs:
        path = pathlib.Path("fixtures/trajectories") / (slug.replace("/", "__") + ".jsonl")
        if not path.exists():
            continue
        try:
            records = pre.fetch(slug)
        except FileNotFoundError:
            continue
        known = {r.evidence_id for r in records}
        calls = {}
        for line in path.read_text().splitlines():
            if line.strip():
                e = json.loads(line)
                calls[e["label"]] = e["response"]

        # Holt: structured citations, and Stage C quotes attributed to a thread.
        for entry in calls.get("outcomes", {}).get("threads", []):
            cited = normalise_citation(slug, entry.get("pr_id", ""))
            stats["holt"]["cited"] += 1
            stats["holt"]["resolved"] += cited in known
            quote = entry.get("quote", "")
            if quote and not quote.startswith("["):
                stats["holt"]["quoted"] += 1
                num = cited.split("#")[-1].split(":")[0] if "#" in cited else ""
                stats["holt"]["supported"] += quote_supported(quote, bodies_for(records, num))

        # The evidence-matched prompt: free prose, but it was shown the same ids
        # and asked to cite them. Pull every pull-request reference out and check.
        for reason in calls.get("baseline_matched", {}).get("reasons", []):
            for m in PR_REF.finditer(reason):
                num = m.group(1) or m.group(2)
                stats["baseline_matched"]["cited"] += 1
                stats["baseline_matched"]["resolved"] += (
                    f"pr:{slug}#{num}:opened" in known
                )

    print("EVIDENCE INTEGRITY — do the citations hold up?\n")
    print(f"{'method':<20} {'citations':>10} {'resolve':>9} {'quotes':>8} {'faithful':>10}")
    for m, s in stats.items():
        res = f"{s['resolved']}/{s['cited']}" if s["cited"] else "-"
        pct = f"{100*s['resolved']/s['cited']:.0f}%" if s["cited"] else "-"
        fid = (f"{s['supported']}/{s['quoted']} ({100*s['supported']/s['quoted']:.0f}%)"
               if s["quoted"] else "n/a — emits no quotes")
        print(f"{m:<20} {res:>10} {pct:>9} {s['quoted']:>8} {fid:>10}")

    h = stats["holt"]
    if h["quoted"]:
        print(f"\nHolt resolution is {100*h['resolved']/h['cited']:.0f}% by construction: "
              "Stage D drops findings whose ids do not resolve.")
        print(f"Fidelity is {100*h['supported']/h['quoted']:.0f}% and is guaranteed by "
              "nothing — Stage D checks that an id exists, never that the evidence")
        print("says what the claim says. That gap is ours, and it is measured here.")


if __name__ == "__main__":
    main()
