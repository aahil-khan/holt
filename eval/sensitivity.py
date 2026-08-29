"""How much does the result depend on choices we made ourselves?

Two sensitivities, both uncomfortable and both published because a reader will
otherwise find them:

1. **Ground truth.** L1 keeps an outsider merge only if the diff is substantive
   and a human engaged with it. Both filters were chosen by us. What happens to
   the headline if either is dropped?

2. **The pipeline.** Which parts of the agent actually move the number, measured
   in MCC rather than in the F1 the project itself calls degenerate?

Run:  PYTHONPATH=. uv run python eval/sensitivity.py
"""

from __future__ import annotations

import json
import math
import pathlib
import statistics

from eval.labels.qualifying import established_authors, is_substantive, pr_key
from holt.agent.findings import Findings
from holt.agent.signals import build_threads, compute
from holt.evidence.fixtures import FixtureProvider
from holt.report import Verdict
from holt.types import Window
import holt.agent.verdict as V

MIN_MERGES, MIN_PEOPLE = 2, 2


def label(pre, post, *, use_substantive: bool, use_reviewed: bool) -> dict:
    """L1 with either filter optionally disabled."""
    insiders = established_authors(pre)
    post = list(post)
    opened = {pr_key(r.evidence_id): r for r in post if r.evidence_id.endswith(":opened")}
    merged = {pr_key(r.evidence_id) for r in post if r.evidence_id.endswith(":merged")}
    engaged: dict[str, set[str]] = {}
    for r in post:
        if ":review:" in r.evidence_id or ":comment:" in r.evidence_id:
            if not r.payload.get("author_is_bot"):
                engaged.setdefault(pr_key(r.evidence_id), set()).add(r.payload.get("author", ""))

    human = [
        k for k, r in opened.items()
        if r.payload.get("author") not in insiders and not r.payload.get("author_is_bot")
    ]
    keep = [k for k in human if k in merged]
    if use_substantive:
        keep = [k for k in keep if is_substantive(opened[k].payload)]
    if use_reviewed:
        keep = [k for k in keep if engaged.get(k, set()) - {opened[k].payload.get("author")}]
    people = {opened[k].payload.get("author") for k in keep}
    return {"n": len(keep), "people": len(people), "any_attempts": bool(human)}


def mcc(pred: dict[str, bool], gold: dict[str, bool]) -> float:
    tp = sum(1 for s, p in pred.items() if p and gold[s])
    fp = sum(1 for s, p in pred.items() if p and not gold[s])
    fn = sum(1 for s, p in pred.items() if not p and gold[s])
    tn = len(pred) - tp - fp - fn
    d = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn) - (fp * fn)) / d if d else 0.0


def main() -> None:
    pre_p, post_p = FixtureProvider(Window.PRE_T), FixtureProvider(Window.POST_T)
    pool = json.loads(pathlib.Path("eval/pool.json").read_text())["repos"]
    runs = [json.loads(pathlib.Path(f"eval/results_eval_run{i}.json").read_text()) for i in (1, 2, 3)]

    evidence = {}
    for slug in pool:
        try:
            evidence[slug] = (pre_p.fetch(slug), post_p.fetch(slug))
        except FileNotFoundError:
            pass

    print("1. GROUND-TRUTH SENSITIVITY — the two L1 filters are our own choices\n")
    print(f"{'ground truth':<26} {'positives':>10} {'holt':>8} {'baseline':>10}")
    for name, sub, rev in [
        ("L1 as shipped", True, True),
        ("drop `reviewed`", True, False),
        ("drop `substantive`", False, True),
        ("drop both (~= L0)", False, False),
    ]:
        gold = {}
        for slug, (pre, post) in evidence.items():
            lab = label(pre, post, use_substantive=sub, use_reviewed=rev)
            if not lab["any_attempts"]:
                continue
            gold[slug] = lab["n"] >= MIN_MERGES and lab["people"] >= MIN_PEOPLE
        scores = {}
        for meth in ("holt", "baseline"):
            vals = []
            for r in runs:
                pred = {s: r["verdicts"][meth][s] == "viable" for s in gold if s in r["verdicts"][meth]}
                vals.append(mcc(pred, gold))
            scores[meth] = statistics.mean(vals)
        print(f"{name:<26} {sum(gold.values()):>4}/{len(gold):<5} "
              f"{scores['holt']:>+8.2f} {scores['baseline']:>+10.2f}")

    print("\n2. PIPELINE ABLATION — in MCC, not the F1 this project calls degenerate\n")
    lab_now = json.loads(pathlib.Path("eval/results_labels.json").read_text())["l1"]
    gold = {s: (r["qualifying_merges"] >= 2 and r["distinct_qualifying_contributors"] >= 2)
            for s, r in lab_now.items() if r["bucket"] != "insufficient_evidence"}

    def variant(name, kinds_on, thresholds_on):
        saved = (V.NON_SOFTWARE_KINDS, V.CLOSED_KINDS, V.MIN_MERGES, V.MIN_DISTINCT_AUTHORS)
        if not kinds_on:
            V.NON_SOFTWARE_KINDS, V.CLOSED_KINDS = set(), set()
        if not thresholds_on:
            V.MIN_MERGES, V.MIN_DISTINCT_AUTHORS = 0, 0
        vals = []
        for tag in ("run1", "run2", "run3"):
            pred = {}
            for slug in gold:
                p = pathlib.Path("fixtures/trajectories") / tag / (slug.replace("/", "__") + ".jsonl")
                if not p.exists():
                    continue
                kind = next((json.loads(l)["response"]["repo_kind"]
                             for l in p.read_text().splitlines()
                             if l.strip() and json.loads(l)["label"] == "classify"), None)
                f = Findings(); f.add("repo_kind", kind, evidence_ids=("x",))
                pred[slug] = V.classify(f, compute(build_threads(evidence[slug][0])))[0] is Verdict.VIABLE
            vals.append(mcc(pred, gold))
        (V.NON_SOFTWARE_KINDS, V.CLOSED_KINDS, V.MIN_MERGES, V.MIN_DISTINCT_AUTHORS) = saved
        print(f"  {name:<44} {statistics.mean(vals):>+6.2f}")

    variant("full pipeline", True, True)
    variant("Stage A repository-kind rules disabled", False, True)
    variant("arithmetic thresholds set to zero", True, False)
    variant("both disabled", False, False)


if __name__ == "__main__":
    main()
