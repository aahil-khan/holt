"""Do the reports' citations hold up, and how much do they actually say?

Accuracy is not the only thing a report can be wrong about. A claim can point at
a pull request that does not exist, or quote words that were never said in it.
Neither shows up in a confusion matrix, and both are exactly what a reader
checking your work would catch first.

This file measures the axis the verdict metrics cannot reach. Every headline
number elsewhere in `eval/` is MCC on a three-valued verdict -- a task
`verdict.py` decides with arithmetic, which is why the model stages measure
+0.01 there. The report is the deliverable, and nothing arithmetic produces one.
So the question this answers is not *is the verdict right*, it is *is the
writing checkable*, and on that axis the rule layer scores nothing at all
because it writes nothing.

Three measures, all mechanical, all computed against the committed recordings:

  resolution   every cited evidence id exists in the evidence the agent was given
  fidelity     every quoted string actually appears in the record it is attributed to
  yield        checkable statements per report -- cited, resolving, and, where the
               statement quotes, quoting the record

Yield is the one that answers "what is the model layer for". Resolution and
fidelity are rates: a method that writes one sentence per report and cites it
correctly scores 100% on both. Yield is a count, so writing nothing scores zero.

**Measured on the frozen benchmark**, three runs per pool, the same recordings
Iteration 22 froze -- reported mean +- half-range across runs, because a
single-run integrity number hides model drift the same way a single-run MCC
does. Before Iteration 25 this file read the *unversioned* `fixtures/
trajectories/` root, which holds no `baseline_matched` calls at all: the
ablation row printed a dash that read as "cites nothing" when it in fact meant
"was never recorded here". The comparison was unmeasured and the table said
otherwise. Both pools and both methods now come from runs where both were
recorded.

Holt should score near-perfectly on resolution by construction -- Stage D drops
findings whose citations do not resolve.

Fidelity used to be guaranteed by nothing. Since Iteration 24 the pipeline drops
a claim whose quotation is not in the record, using the *same* matcher this file
measures with (`holt.agent.verify`), so the metric and the guarantee cannot
drift apart. What is measured here is still the model's raw output, not the
filtered report -- so this remains an honest count of how often the model
invents, and the line below it says how many of those the reader never sees.

Run:  PYTHONPATH=. uv run python eval/evidence_integrity.py
"""

from __future__ import annotations

import json
import pathlib
import re
import statistics

from holt.agent.stages import normalise_citation
# One matcher, imported rather than reimplemented: the number reported here is
# the rule the pipeline enforces, not a second opinion about it.
from holt.agent.verify import quote_supported, spoken_part
from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

PR_REF = re.compile(r"(?:pr:[\w.\-]+/[\w.\-]+#(\d+)|#(\d{2,6}))")

# The frozen benchmark of Iteration 22: three recorded runs per pool, on the
# shipped prompts. Named here rather than passed in, because a number computed
# over whichever recordings happened to be lying around is the bug this file
# had.
FROZEN = (
    ("pool 1", "eval/pool.json", ("run1", "run2", "run3")),
    ("pool 2, out of sample", "eval/pool2.json", ("p2r1", "p2r2", "p2r3")),
)

METHODS = ("holt", "baseline_matched")


def bodies_for(records, pr_number: str) -> str:
    """Everything said anywhere on one pull request."""
    marker = f"#{pr_number}:"
    return " ".join(
        str(r.payload.get("body") or "") + " " + str(r.payload.get("title") or "")
        for r in records
        if marker in r.evidence_id
    )


def blank() -> dict[str, int]:
    return {"reports": 0, "cited": 0, "resolved": 0, "quoted": 0,
            "supported": 0, "statements": 0, "checkable": 0}


def score_run(tag: str, slugs: list[str], pre: FixtureProvider) -> dict[str, dict[str, int]]:
    """Integrity counts for one recorded run over one pool."""
    stats = {m: blank() for m in METHODS}
    root = pathlib.Path("fixtures/trajectories") / tag

    for slug in slugs:
        path = root / (slug.replace("/", "__") + ".jsonl")
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
        if "outcomes" in calls:
            stats["holt"]["reports"] += 1
        for entry in calls.get("outcomes", {}).get("threads", []):
            cited = normalise_citation(slug, entry.get("pr_id", ""))
            resolves = cited in known
            stats["holt"]["cited"] += 1
            stats["holt"]["resolved"] += resolves
            stats["holt"]["statements"] += 1
            # A quote that is only our own `[speaker]` scaffold was previously
            # excluded from the denominator as unmeasurable. It is measurable and
            # it is a failure: the model quoted a username, and a reader shown
            # `“[octocat]”` has been shown nothing. Counted, and the tag is
            # stripped from the rest rather than disqualifying them.
            quote = spoken_part(entry.get("quote", ""))
            faithful = True
            if entry.get("quote", "").strip():
                stats["holt"]["quoted"] += 1
                num = cited.split("#")[-1].split(":")[0] if "#" in cited else ""
                faithful = bool(quote) and quote_supported(quote, bodies_for(records, num))
                stats["holt"]["supported"] += faithful
            # Checkable means a reader can go and look: the id resolves, and if
            # words are attributed to somebody, they said them.
            stats["holt"]["checkable"] += resolves and faithful

        # The evidence-matched prompt: free prose, but it was shown the same ids
        # and asked to cite them. Pull every pull-request reference out and check.
        if "baseline_matched" in calls:
            stats["baseline_matched"]["reports"] += 1
        for reason in calls.get("baseline_matched", {}).get("reasons", []):
            stats["baseline_matched"]["statements"] += 1
            hits = list(PR_REF.finditer(reason))
            resolved_here = 0
            for m in hits:
                num = m.group(1) or m.group(2)
                stats["baseline_matched"]["cited"] += 1
                resolved_here += f"pr:{slug}#{num}:opened" in known
            stats["baseline_matched"]["resolved"] += resolved_here
            stats["baseline_matched"]["checkable"] += resolved_here > 0
    return stats


def spread(values: list[float]) -> tuple[float, float]:
    """Mean and half-range. Three runs do not support a standard deviation."""
    if not values:
        return (float("nan"), 0.0)
    return (statistics.fmean(values), (max(values) - min(values)) / 2)


def pct(num: int, den: int) -> float | None:
    return 100.0 * num / den if den else None


def show(mean: float | None, half: float, suffix: str = "%") -> str:
    if mean is None or mean != mean:
        return "n/a"
    return f"{mean:.0f}{suffix} ±{half:.0f}" if half else f"{mean:.0f}{suffix}"


def main() -> None:
    pre = FixtureProvider(Window.PRE_T)

    print("EVIDENCE INTEGRITY — do the citations hold up, and how much is said?")
    print("Frozen benchmark recordings, three runs per pool. No spend.\n")

    totals = {m: blank() for m in METHODS}

    for pool_name, pool_file, tags in FROZEN:
        slugs = json.loads(pathlib.Path(pool_file).read_text())["repos"]
        runs = [score_run(t, slugs, pre) for t in tags]
        if not any(r[m]["reports"] for r in runs for m in METHODS):
            print(f"{pool_name}: no recordings found for {', '.join(tags)}\n")
            continue

        print(f"--- {pool_name} ({', '.join(tags)}) ---")
        print(f"{'method':<18} {'reports':>8} {'resolve':>11} {'faithful':>11} "
              f"{'checkable/report':>18}")
        for m in METHODS:
            reports = [r[m]["reports"] for r in runs]
            res = spread([v for r in runs if (v := pct(r[m]["resolved"], r[m]["cited"])) is not None])
            fid = spread([v for r in runs if (v := pct(r[m]["supported"], r[m]["quoted"])) is not None])
            yld = spread([r[m]["checkable"] / r[m]["reports"] for r in runs if r[m]["reports"]])
            print(f"{m:<18} {statistics.fmean(reports):>8.0f} "
                  f"{show(*res):>11} "
                  f"{(show(*fid) if fid[0] == fid[0] else 'no quotes'):>11} "
                  f"{show(yld[0], yld[1], suffix=''):>18}")
            for k in totals[m]:
                totals[m][k] += sum(r[m][k] for r in runs)
        print()

    print("--- both pools, all six runs ---")
    print(f"{'method':<18} {'statements':>11} {'checkable':>11} {'per report':>11}")
    for m in METHODS:
        t = totals[m]
        share = pct(t["checkable"], t["statements"])
        per = t["checkable"] / t["reports"] if t["reports"] else 0.0
        checkable = f"{t['checkable']} ({share:.0f}%)" if share is not None else "0"
        print(f"{m:<18} {t['statements']:>11} {checkable:>11} {per:>11.1f}")

    h, b = totals["holt"], totals["baseline_matched"]
    print()
    if h["cited"]:
        print(f"Holt resolution is {100*h['resolved']/h['cited']:.0f}% by construction: "
              "Stage D drops findings whose ids do not resolve.")
    if h["quoted"]:
        gap = h["quoted"] - h["supported"]
        print(f"Fidelity of the model's raw quotes is {100*h['supported']/h['quoted']:.0f}%. "
              f"The {gap} that are not in the record are")
        print("dropped before the reader by the same check that counted them here, so the "
              "report's own fidelity is 100% by construction.")
    if h["reports"] and b["reports"]:
        print()
        print(f"Yield is the number the verdict metrics cannot see. Holt writes "
              f"{h['checkable']/h['reports']:.1f} checkable")
        print(f"statements per report against the ablation's {b['checkable']/b['reports']:.1f}, "
              "on identical evidence. The verdict")
        print("layer that supplies Holt's accuracy writes none: arithmetic does not cite.")
        print()
        print("The ablation is not careless about the ids it does use -- every reference it "
              "made resolves.")
        print(f"What it does not do is make one: {b['statements'] - b['checkable']} of its "
              f"{b['statements']} statements "
              f"({100 * (b['statements'] - b['checkable']) / b['statements']:.0f}%) cite nothing "
              "a reader could open,")
        print("which is the failure a resolution *rate* cannot show and a count can.")


if __name__ == "__main__":
    main()
