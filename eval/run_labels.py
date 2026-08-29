"""Run L0 and L1 over the committed pool and show what the extra filters change.

The delta between the two rankings is the measured improvement claim, so the
funnel is printed per repository rather than summarised: a filter that cannot be
inspected cannot be trusted.

Run:  PYTHONPATH=. uv run python eval/run_labels.py
"""

from __future__ import annotations

import json
from pathlib import Path

from eval.labels import naive, qualifying
from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

POOL = Path("eval/pool.json")


def main() -> None:
    pool = json.loads(POOL.read_text())
    pre, post = FixtureProvider(Window.PRE_T), FixtureProvider(Window.POST_T)

    l0: dict[str, dict] = {}
    l1: dict[str, dict] = {}
    unavailable: list[str] = []
    for slug in pool["repos"]:
        try:
            a, b = pre.fetch(slug), post.fetch(slug)
        except FileNotFoundError:
            unavailable.append(slug)
            continue
        l0[slug], l1[slug] = naive.score(a, b), qualifying.score(a, b)

    def rank(scores: dict[str, dict], key) -> list[str]:
        scored = [s for s in scores if scores[s]["bucket"] == "scored"]
        return sorted(scored, key=lambda s: key(scores[s]), reverse=True)

    r0 = rank(l0, lambda r: (r["merge_rate"], r["outsider_merges"]))
    r1 = rank(l1, lambda r: (r["qualifying_rate"], r["qualifying_merges"]))
    pos0 = {s: i + 1 for i, s in enumerate(r0)}
    pos1 = {s: i + 1 for i, s in enumerate(r1)}

    print(f"pool {pool['sha256'][:12]}   scored L0 {len(r0)}   scored L1 {len(r1)}   "
          f"unavailable {len(unavailable)}\n")
    print(f"{'L1':>3} {'L0':>4} {'move':>5}   {'qual':>5} {'sub':>5} {'merg':>5} {'try':>5}  repo")
    for i, slug in enumerate(r1, 1):
        f = l1[slug]["funnel"]
        was = pos0.get(slug)
        move = f"{was - i:+d}" if was else "new"
        print(
            f"{i:>3} {was if was else '-':>4} {move:>5}   "
            f"{f['reviewed']:>5} {f['substantive']:>5} {f['merged']:>5} {f['human']:>5}  {slug}"
        )

    Path("eval/results_labels.json").write_text(
        json.dumps(
            {
                "pool_sha256": pool["sha256"],
                "l0_ranking": r0,
                "l1_ranking": r1,
                "l0": l0,
                "l1": l1,
                "unavailable": unavailable,
            },
            indent=1,
        )
        + "\n"
    )
    print(f"\nwrote eval/results_labels.json")


if __name__ == "__main__":
    main()
