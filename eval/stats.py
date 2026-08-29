"""Uncertainty over repositories, not over random seeds.

Reporting mean ± range across repeated runs measures how much the language model
wobbles. It says nothing about the far larger question: whether a 22-repository
sample supports the difference at all. Those are different quantities and
presenting the first where a reader expects the second overstates the result.

Two tests, both over repositories:

* a bootstrap confidence interval on the difference in Matthews correlation
* an exact McNemar test on per-repository correctness

Run:  PYTHONPATH=. uv run python eval/stats.py
"""

from __future__ import annotations

import json
import math
import random
from itertools import combinations
from math import comb
from pathlib import Path

BOOTSTRAP = 20_000
SEED = 20260830


def mcc(pairs: list[tuple[bool, bool]]) -> float:
    """pairs: (predicted_viable, actually_genuine)."""
    tp = sum(1 for p, g in pairs if p and g)
    fp = sum(1 for p, g in pairs if p and not g)
    fn = sum(1 for p, g in pairs if not p and g)
    tn = sum(1 for p, g in pairs if not p and not g)
    d = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn) - (fp * fn)) / d if d else 0.0


def exact_mcnemar(only_a: int, only_b: int) -> float:
    """Two-sided exact binomial p on the discordant pairs."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def bootstrap_difference(
    a: dict[str, bool], b: dict[str, bool], gold: dict[str, bool], seed: int = SEED
) -> tuple[float, float, float, float]:
    """Resample repositories. Returns (mean difference, lo, hi, P(difference <= 0))."""
    slugs = sorted(set(a) & set(b) & set(gold))
    rng = random.Random(seed)
    diffs = []
    for _ in range(BOOTSTRAP):
        picked = [slugs[rng.randrange(len(slugs))] for _ in slugs]
        diffs.append(
            mcc([(a[s], gold[s]) for s in picked]) - mcc([(b[s], gold[s]) for s in picked])
        )
    diffs.sort()
    return (
        sum(diffs) / len(diffs),
        diffs[int(0.025 * len(diffs))],
        diffs[int(0.975 * len(diffs))],
        sum(1 for d in diffs if d <= 0) / len(diffs),
    )


def main() -> None:
    lab = json.loads(Path("eval/results_labels.json").read_text())["l1"]
    gold = {
        s: (r["qualifying_merges"] >= 2 and r["distinct_qualifying_contributors"] >= 2)
        for s, r in lab.items()
        if r["bucket"] != "insufficient_evidence"
    }
    runs = [json.loads(Path(f"eval/results_eval_run{i}.json").read_text()) for i in (1, 2, 3)]

    print("Uncertainty over repositories (n = %d), not over seeds.\n" % len(gold))
    for i, r in enumerate(runs, 1):
        v = r["verdicts"]
        holt = {s: v["holt"][s] == "viable" for s in gold if s in v["holt"]}
        base = {s: v["baseline"][s] == "viable" for s in gold if s in v["baseline"]}
        shared = sorted(set(holt) & set(base))
        only_h = sum(1 for s in shared if (holt[s] == gold[s]) and (base[s] != gold[s]))
        only_b = sum(1 for s in shared if (base[s] == gold[s]) and (holt[s] != gold[s]))
        p = exact_mcnemar(only_h, only_b)
        mean, lo, hi, worse = bootstrap_difference(holt, base, gold)
        print(f"run {i}:")
        print(f"  McNemar          Holt right / baseline wrong on {only_h}, reverse on {only_b}"
              f"   exact two-sided p = {p:.2f}")
        print(f"  bootstrap MCC    difference {mean:+.2f}  95% CI [{lo:+.2f}, {hi:+.2f}]"
              f"   P(difference <= 0) = {worse:.2f}")

    print("\nRead this honestly: at 22 repositories the aggregate difference is not")
    print("statistically distinguishable. The trap-rejection result (4/5 against 0/5,")
    print("Fisher exact p = 0.048) and the positive control (3/3 against 1/3) are the")
    print("claims this sample can carry.")


if __name__ == "__main__":
    main()
