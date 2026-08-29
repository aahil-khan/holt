"""Draw the scored pool from the T-era frame.

The pool is committed with a content hash *before* any agent run, and never
edited after results are seen. Sampling is seeded so a judge re-running this
script against the same frame gets the same 30 repos.

Universe (all criteria observable at or before T, so none of this leaks):
  * the repo opened at least one human (non-bot) pull request in the archive
    window, i.e. it existed and had inbound PR activity at T
  * at least MIN_OPENERS distinct human openers, so the repo is somewhere a
    person other than the owner was already sending work

Strata are PR-volume bands over the window. Sampling within bands rather than
uniformly stops the draw from being swamped by the long tail of one-PR repos,
which would leave nothing to discriminate between.

Run:  uv run python eval/sample_pool.py --dry-run
      uv run python eval/sample_pool.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

FRAME = Path("eval/frame.json")
OUT = Path("eval/pool.json")

SEED = 20260601
MIN_OPENERS = 2
POOL_SIZE = 30

# (label, lower_inclusive, upper_exclusive, how_many_to_draw)
BANDS: list[tuple[str, int, int, int]] = [
    ("quiet 2-4", 2, 5, 8),
    ("steady 5-14", 5, 15, 8),
    ("busy 15-49", 15, 50, 8),
    ("very busy 50+", 50, 10**9, 6),
]


def load_universe() -> dict[str, dict]:
    if not FRAME.exists():
        raise SystemExit("eval/frame.json missing; run eval/build_frame.py first")
    repos = json.loads(FRAME.read_text())["repos"]
    return {
        name: stats
        for name, stats in repos.items()
        if stats["distinct_openers"] >= MIN_OPENERS
    }


def stratify(universe: dict[str, dict]) -> dict[str, list[str]]:
    strata: dict[str, list[str]] = {label: [] for label, *_ in BANDS}
    for name, stats in universe.items():
        n = stats["prs_opened"]
        for label, low, high, _ in BANDS:
            if low <= n < high:
                strata[label].append(name)
                break
    # Sorted so the draw depends only on the seed, never on dict ordering.
    return {label: sorted(names) for label, names in strata.items()}


def draw(strata: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    rng = random.Random(SEED)
    pool: list[str] = []
    shortfalls: list[str] = []
    for label, _, _, want in BANDS:
        available = strata[label]
        take = min(want, len(available))
        if take < want:
            shortfalls.append(f"{label}: wanted {want}, only {len(available)} available")
        pool.extend(rng.sample(available, take))
    return sorted(pool), shortfalls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="commit the pool to eval/pool.json")
    args = parser.parse_args()

    universe = load_universe()
    strata = stratify(universe)
    pool, shortfalls = draw(strata)

    print(f"universe: {len(universe)} repos (>= {MIN_OPENERS} distinct human openers)")
    for label, _, _, want in BANDS:
        print(f"  {label:16s} available {len(strata[label]):5d}   drawing {want}")
    for note in shortfalls:
        print(f"  SHORTFALL  {note}")
    print(f"\npool: {len(pool)} repos")
    for name in pool:
        stats = universe[name]
        print(f"  {stats['prs_opened']:4d} PRs  {stats['distinct_openers']:3d} openers  {name}")

    if not args.write:
        print("\ndry run; nothing written. Re-run with --write to commit the pool.")
        return
    if shortfalls:
        raise SystemExit("refusing to write a pool with unfilled strata; widen the frame first")

    body = {
        "seed": SEED,
        "min_distinct_openers": MIN_OPENERS,
        "bands": [[label, low, high, want] for label, low, high, want in BANDS],
        "source_frame_files": json.loads(FRAME.read_text())["source_files"],
        "repos": pool,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    OUT.write_text(json.dumps({**body, "sha256": digest}, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT}  sha256={digest[:16]}")
    print("This pool is now fixed. Do not edit it after seeing results.")


if __name__ == "__main__":
    main()
