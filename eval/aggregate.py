"""Aggregate the per-run results into the figures the README reports.

The headline numbers are means over three independent live runs. Without this
script there was no documented way to reproduce them from the committed
artefacts, which made the most prominent figures in the project the least
checkable ones.

Run:  PYTHONPATH=. uv run python eval/aggregate.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

RUNS = [Path(f"eval/results_eval_run{i}.json") for i in (1, 2, 3)]
METRICS = ["mcc", "balanced_accuracy", "f1", "sensitivity", "specificity"]
METHODS = ["always_viable", "never_viable", "name_only", "baseline", "holt"]


def main() -> None:
    missing = [p for p in RUNS if not p.exists()]
    if missing:
        raise SystemExit(
            f"missing {[str(p) for p in missing]}. Record them with "
            "`uv run python eval/harness.py --run-tag run1` (and run2, run3)."
        )
    runs = [json.loads(p.read_text()) for p in RUNS]

    print(f"mean +/- half-range over {len(runs)} independent live runs")
    print(f"total spend: ${sum(r['spend_usd'] for r in runs):.2f}\n")
    header = "  ".join(f"{m[:8]:>14}" for m in METRICS)
    print(f"{'method':<15} {header}")
    for meth in METHODS:
        cells = []
        for m in METRICS:
            vals = [next(x[m] for x in r["results"] if x["method"] == meth) for r in runs]
            cells.append(f"{statistics.mean(vals):>6.2f} +/-{(max(vals)-min(vals))/2:<5.2f}")
        print(f"{meth:<15} {'  '.join(cells)}")

    print("\nverdict stability -- repositories identical across all runs:")
    slugs = sorted(runs[0]["verdicts"]["holt"])
    for meth in ("baseline", "holt"):
        same = sum(1 for s in slugs if len({r["verdicts"][meth].get(s) for r in runs}) == 1)
        print(f"  {meth:<10} {same}/{len(slugs)}")

    print("\nThese intervals are seed variance. For uncertainty over repositories, "
          "which is larger and matters more, run eval/stats.py.")


if __name__ == "__main__":
    main()
