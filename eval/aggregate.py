"""Aggregate the per-run results into the figures the README reports.

The headline numbers are means over three independent live runs. Without this
script there was no documented way to reproduce them from the committed
artefacts, which made the most prominent figures in the project the least
checkable ones.

Run:  PYTHONPATH=. uv run python eval/aggregate.py            # pool 1
      PYTHONPATH=. uv run python eval/aggregate.py --pool 2   # out of sample

Both pools are here because the README reports both, and pool 2 -- drawn and
labelled after every rule was written -- is the one it calls the more important
result. It was also the one with no documented way to reproduce its table.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

POOLS = {
    1: [Path(f"eval/results_eval_run{i}.json") for i in (1, 2, 3)],
    2: [Path(f"eval/results_eval_p2r{i}.json") for i in (1, 2, 3)],
}
METRICS = ["mcc", "balanced_accuracy", "f1", "sensitivity", "specificity"]
# `baseline_matched` is the evidence-matched ablation: the same evidence the
# pipeline saw, in one prompt. Leaving it out hid the row that says what the
# deterministic layer is worth.
METHODS = [
    "always_viable", "never_viable", "name_only", "baseline", "baseline_matched", "holt",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=int, choices=(1, 2), default=1,
                        help="1 (in sample) or 2 (out of sample); default 1")
    args = parser.parse_args()
    RUNS = POOLS[args.pool]
    missing = [p for p in RUNS if not p.exists()]
    if missing:
        raise SystemExit(
            f"missing {[str(p) for p in missing]}. Record them with "
            "`uv run python eval/harness.py --run-tag run1` (and run2, run3)."
        )
    runs = [json.loads(p.read_text()) for p in RUNS]

    label = "in sample" if args.pool == 1 else "out of sample"
    print(f"pool {args.pool} ({label})")
    print(f"mean +/- half-range over {len(runs)} independent live runs")
    print(f"total spend: ${sum(r['spend_usd'] for r in runs):.2f}\n")
    header = "  ".join(f"{m[:8]:>14}" for m in METRICS)
    print(f"{'method':<17} {header}")
    for meth in METHODS:
        cells = []
        for m in METRICS:
            vals = [
                next((x[m] for x in r["results"] if x["method"] == meth), None)
                for r in runs
            ]
            if any(v is None for v in vals):
                continue
            cells.append(f"{statistics.mean(vals):>6.2f} +/-{(max(vals)-min(vals))/2:<5.2f}")
        if cells:
            print(f"{meth:<17} {'  '.join(cells)}")

    print("\nverdict stability -- repositories identical across all runs:")
    slugs = sorted(runs[0]["verdicts"]["holt"])
    for meth in ("baseline", "holt"):
        same = sum(1 for s in slugs if len({r["verdicts"][meth].get(s) for r in runs}) == 1)
        print(f"  {meth:<10} {same}/{len(slugs)}")

    print("\nThese intervals are seed variance. For uncertainty over repositories, "
          "which is larger and matters more, run eval/stats.py.")


if __name__ == "__main__":
    main()
