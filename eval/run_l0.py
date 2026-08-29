"""Run L0 across the committed pool and rank the results.

This is the Baseline row of the changelog. Whatever it prints is the result --
including if it fails to show what we expected.

Run:  uv run python eval/run_l0.py
"""

from __future__ import annotations

import json
from pathlib import Path

from eval.labels.naive import INSUFFICIENT_EVIDENCE, score
from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

POOL = Path("eval/pool.json")


def main() -> None:
    pool = json.loads(POOL.read_text())
    pre = FixtureProvider(Window.PRE_T)
    post = FixtureProvider(Window.POST_T)

    rows: list[tuple[str, dict]] = []
    unavailable: list[str] = []
    for slug in pool["repos"]:
        try:
            rows.append((slug, score(pre.fetch(slug), post.fetch(slug))))
        except FileNotFoundError:
            unavailable.append(slug)

    scored = [(s, r) for s, r in rows if r["bucket"] != INSUFFICIENT_EVIDENCE]
    silent = [(s, r) for s, r in rows if r["bucket"] == INSUFFICIENT_EVIDENCE]

    # L0's own ranking: merge rate first, then volume. This is the ordering a
    # naive metric produces, not one chosen to make a point.
    scored.sort(key=lambda sr: (sr[1]["merge_rate"], sr[1]["outsider_merges"]), reverse=True)

    print(f"pool sha256: {pool['sha256'][:16]}   repos: {len(pool['repos'])}")
    print(f"scored: {len(scored)}   insufficient evidence: {len(silent)}   "
          f"unavailable: {len(unavailable)}\n")
    print(f"{'#':>3}  {'rate':>6}  {'merged':>6}  {'tried':>6}  {'people':>6}  repo")
    for i, (slug, r) in enumerate(scored, 1):
        print(
            f"{i:>3}  {r['merge_rate']:>6.2f}  {r['outsider_merges']:>6}  "
            f"{r['outsider_attempts']:>6}  {r['distinct_outsiders_merged']:>6}  {slug}"
        )
    if silent:
        print("\ninsufficient evidence (no outsider attempts after the cutoff):")
        for slug, _ in silent:
            print(f"     {slug}")
    if unavailable:
        print("\nunavailable (repository no longer exists):")
        for slug in unavailable:
            print(f"     {slug}")

    Path("eval/results_l0.json").write_text(
        json.dumps(
            {
                "pool_sha256": pool["sha256"],
                "ranking": [s for s, _ in scored],
                "scores": {s: r for s, r in rows},
                "unavailable": unavailable,
            },
            indent=1,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
