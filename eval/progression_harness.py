"""Score personalised contribution discovery against the things that could make
it unnecessary.

Everything here is fixed by `eval/PREREGISTRATION-3.md`, written before any of it
existed: the unit, the exclusions, the metrics, the arms, the weights and the
decision rule.

Primary metric is **hit@10** and the reason is arithmetic rather than
convenience: at a mean base rate of 2.4%, precision@3 puts nearly every pair at
0.000 for every arm, and a metric that is constant across arms cannot separate
them. precision@3 is reported anyway, always, whichever way it falls.

Run:  PYTHONPATH=. uv run python eval/progression_harness.py [--replay] [--arith-only]
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from math import comb
from pathlib import Path

from eval.labels import progression as truth
from holt.agent import progression as rank_lib
from holt.agent.entry import RANKER_SIGNALS
from holt.agent.signals import build_threads, compute
from holt.agent.stages import find_paths
from holt.evidence.fixtures import FixtureProvider
from holt.issues import issue_key
from holt.model import OpenAIModel, ReplayModel, TRAJECTORY_DIR
from holt.types import Window

ISSUE_ROOT = Path("fixtures/issues")
K_HIT = 10
K_PREC = 3
# `holt_arith` is the scorer exactly as registered; `holt_repaired` drops the
# three near-constant features under Amendment 1's rule. Both are kept so the
# registered loss stays reproducible rather than being replaced by what came
# after it.
ARMS = ("random", "recency", "blind", "path_overlap", "holt_arith", "holt_repaired", "holt_full", "holt_full_repaired")


def hit_at_k(ranked: list[str], hits: set[str], k: int) -> float:
    return float(any(x in hits for x in ranked[:k]))


def precision_at_k(ranked: list[str], hits: set[str], k: int) -> float:
    top = ranked[:k]
    return sum(1 for x in top if x in hits) / len(top) if top else 0.0


def paired(a: list[float], b: list[float], seed: int = 0) -> dict:
    d = [x - y for x, y in zip(a, b, strict=True)]
    rng = random.Random(seed)
    boot = sorted(statistics.mean(rng.choices(d, k=len(d))) for _ in range(20000))
    wins = sum(1 for x in d if x > 0)
    losses = sum(1 for x in d if x < 0)
    n = wins + losses
    k = min(wins, losses)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n) if n else 1.0
    return {"diff": statistics.mean(d), "lo": boot[500], "hi": boot[19500],
            "wins": wins, "losses": losses, "ties": len(d) - n, "p": p}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--arith-only", action="store_true",
                    help="skip every model call: runs the five non-LLM arms")
    ap.add_argument("--out", default="eval/progression_results.json")
    ap.add_argument("--pools", nargs="+", default=["eval/pool.json", "eval/pool2.json"])
    args = ap.parse_args()

    ipre = FixtureProvider(Window.PRE_T, root=ISSUE_ROOT)
    ipost = FixtureProvider(Window.POST_T, root=ISSUE_ROOT)
    ppre = FixtureProvider(Window.PRE_T)

    slugs = []
    for pool in args.pools:
        slugs += json.loads(Path(pool).read_text())["repos"]

    hits = {a: [] for a in ARMS}
    precs = {a: [] for a in ARMS}
    rows, considered, spend, deep = [], 0, 0.0, []

    for slug in slugs:
        try:
            pre_i, post_i, pre_p = list(ipre.fetch(slug)), list(ipost.fetch(slug)), list(ppre.fetch(slug))
        except FileNotFoundError:
            continue
        scorable, seen = truth.pairs(pre_p, pre_i, post_i)
        considered += seen
        if not scorable:
            continue

        # One contributor-blind ranking per repository, shared by every pair in
        # it. That is exactly what makes it the ablation: it cannot vary by person.
        blind_order: list[str] | None = None
        if not args.arith_only:
            path = TRAJECTORY_DIR / "pathfinder" / (slug.replace("/", "__") + ".jsonl")
            if path.exists():
                model = ReplayModel(path) if args.replay else OpenAIModel(path)
                signals = compute(build_threads(pre_p)).as_dict()
                from holt.issues import open_at_cutoff
                blind_order = [
                    issue_key(r["evidence_id"])
                    for r in find_paths(slug, list(open_at_cutoff(pre_i).values()),
                                        {k: signals[k] for k in RANKER_SIGNALS}, model)
                ]
                spend += getattr(model.usage, "cost_usd", 0.0)

        for history, candidates, realised in scorable:
            who = history.login
            contributor = rank_lib.Contributor(
                login=who, files=history.files, median_pr_size=history.median_size,
                engaged_with=history.engaged_with, merged_count=len(history.merged_prs),
            )
            base = len(realised) / len(candidates)
            recency = [k for k, _ in sorted(candidates.items(),
                                            key=lambda kv: kv[1].timestamp, reverse=True)]

            # path_overlap: the cheap heuristic, and the registered bar.
            def overlaps(record) -> bool:
                named = rank_lib.paths_in(record)
                dirs = {f.rsplit("/", 1)[0] for f in contributor.files if "/" in f}
                return any(
                    p in contributor.files
                    or any(p.endswith(f) or f.endswith(p) for f in contributor.files)
                    or any(d and d in p for d in dirs)
                    for p in named
                )
            matched = [k for k in recency if overlaps(candidates[k])]
            path_order = matched + [k for k in recency if k not in set(matched)]

            arith = [k for k, _, _ in rank_lib.rank(contributor, candidates)]
            repaired = [k for k, _, _ in rank_lib.rank(
                contributor, candidates, rank_lib.REPAIRED_WEIGHTS)]

            orders = {
                "holt_repaired": repaired,
                "recency": recency,
                "path_overlap": path_order,
                "holt_arith": arith,
                "blind": ([k for k in (blind_order or []) if k in candidates]
                          + [k for k in recency if k not in set(blind_order or [])]),
            }

            if args.arith_only:
                orders["holt_full"] = arith
                orders["holt_full_repaired"] = repaired
            else:
                path = TRAJECTORY_DIR / "progression" / (
                    slug.replace("/", "__") + "__" + who + ".jsonl")
                model = ReplayModel(path) if args.replay else OpenAIModel(path)
                contributor.profile = rank_lib.profile(slug, who, history.merged_prs, model)
                spend += getattr(model.usage, "cost_usd", 0.0)
                # One profile call, both weightings. The model contributes one
                # term out of five and still cannot reorder anything itself.
                orders["holt_full"] = [k for k, _, _ in rank_lib.rank(contributor, candidates)]
                orders["holt_full_repaired"] = [k for k, _, _ in rank_lib.rank(
                    contributor, candidates, rank_lib.REPAIRED_WEIGHTS)]

            for arm, order in orders.items():
                hits[arm].append(hit_at_k(order, realised, K_HIT))
                precs[arm].append(precision_at_k(order, realised, K_PREC))
            # Expected value under a uniformly random order, not one sample of it.
            hits["random"].append(1 - (1 - base) ** K_HIT)
            precs["random"].append(base)

            rows.append({"repo": slug, "login": who, "candidates": len(candidates),
                         "realised": len(realised), "merged_prs": len(history.merged_prs),
                         "hit": {a: hits[a][-1] for a in ARMS},
                         "prec": {a: precs[a][-1] for a in ARMS}})
            deep.append(len(history.merged_prs) >= 3)
            print(f"  {slug}/{who:<24} cand={len(candidates):>3} real={len(realised):>2} "
                  f"hit@10 arith={hits['holt_arith'][-1]:.0f} path={hits['path_overlap'][-1]:.0f}",
                  flush=True)

    n = len(rows)
    print(f"\n{n} scorable (repository, contributor) pairs of {considered} considered "
          f"({n/considered:.1%})")
    print(f"{sum(r['realised'] for r in rows)} realised next contributions, "
          f"{len({r['repo'] for r in rows})} repositories\n")

    print(f"{'arm':<14}{'hit@'+str(K_HIT):>9}{'prec@'+str(K_PREC):>10}")
    for arm in ARMS:
        print(f"{arm:<14}{statistics.mean(hits[arm]):>9.3f}{statistics.mean(precs[arm]):>10.3f}")

    print("\nPaired against the registered bar (path_overlap), hit@10:")
    for arm in ("holt_full_repaired", "holt_repaired", "holt_full", "holt_arith",
                "blind", "recency"):
        s = paired(hits[arm], hits["path_overlap"])
        print(f"  {arm:<12} {s['diff']:+.3f}  CI[{s['lo']:+.3f},{s['hi']:+.3f}]  "
              f"{s['wins']}W/{s['losses']}L/{s['ties']}T  p={s['p']:.3f}")

    if not args.arith_only:
        print("\nDoes the model add anything over the same arithmetic without it?")
        for a, b in (("holt_full_repaired", "holt_repaired"), ("holt_full", "holt_arith")):
            s = paired(hits[a], hits[b])
            print(f"  {a} - {b}: {s['diff']:+.3f}  CI[{s['lo']:+.3f},{s['hi']:+.3f}]  "
                  f"{s['wins']}W/{s['losses']}L/{s['ties']}T  p={s['p']:.3f}")

    print("\nBy history depth (declared before running):")
    for label, mask in ((">=3 pre-T merges", deep), ("thinner", [not d for d in deep])):
        idx = [i for i, m in enumerate(mask) if m]
        if not idx:
            continue
        print(f"  {label:<18} n={len(idx):<4}" + "".join(
            f"  {a}={statistics.mean(hits[a][i] for i in idx):.3f}"
            for a in ("path_overlap", "holt_arith", "holt_repaired", "holt_full", "holt_full_repaired")))

    print(f"\nspend: ${spend:.3f}")
    Path(args.out).write_text(json.dumps(
        {"pairs": rows, "considered": considered, "arms": ARMS,
         "hit_at_k": K_HIT, "precision_at_k": K_PREC}, indent=1) + "\n")
    print(f"per-pair results: {args.out}")


if __name__ == "__main__":
    main()
