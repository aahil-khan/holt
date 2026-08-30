"""The fifth kill: personalised discovery, refuted by four controls.

The idea was to move one step earlier than "analyse this repo" — given who you
are, which repositories should you even consider? The argument was that stars say
*alive* and language says *my world*, and neither says *will they take a patch
from a stranger*, which is the one thing this project can measure.

The evidence for it was: of 74 (contributor -> new repository) transitions across
the pool, **66 landed in an L1-viable repository**. That looked like a large lift
over the base rate, and it is the number this script reproduces first — because a
refutation that cannot first reproduce what it refutes is not a refutation.

Then four controls, each independently fatal. The headline survives none.

Run:  PYTHONPATH=. uv run python eval/mover_controls.py
Costs nothing and calls no model.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from eval.labels.progression import histories
from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

# The nine repositories that turned out to be one programme. Listed explicitly
# rather than detected, so a reader can check the membership themselves:
#   grep -oic gssoc fixtures/post_t/leonagoel__hybrid-recommender.json
COHORT = {
    "leonagoel/hybrid-recommender", "knoxiboy/DoubtDesk",
    "ronisarkarexe/story-spark-ai", "JhaSourav07/commitpulse",
    "anurag3407/career-pilot", "utksh1/SecuScan",
    "rishabh0510rishabh/EnvForage", "SandeepVashishtha/Eventra",
    "AseemPrasad/Legalassist-AI",
}

# GitHub's placeholder for a deleted account. Every deleted contributor collapses
# into this one login, so it is not a person and cannot be a data point.
DELETED_ACCOUNT = "(ghost)"


def viable_repos() -> set[str]:
    labels: dict = {}
    for path in ("eval/results_labels.json", "eval/results_labels_pool2.json"):
        labels.update(json.loads(Path(path).read_text())["l1"])
    return {
        slug for slug, row in labels.items()
        if row["qualifying_merges"] >= 2 and row["distinct_qualifying_contributors"] >= 2
    }


def main() -> None:
    pre, post = FixtureProvider(Window.PRE_T), FixtureProvider(Window.POST_T)
    viable = viable_repos()

    slugs: list[str] = []
    for pool in ("eval/pool.json", "eval/pool2.json"):
        slugs += json.loads(Path(pool).read_text())["repos"]

    before: dict[str, set[str]] = defaultdict(set)
    after: dict[str, set[str]] = defaultdict(set)
    merge_slots: Counter = Counter()
    universe: list[str] = []

    for slug in slugs:
        try:
            was, now = histories(pre.fetch(slug)), histories(post.fetch(slug))
        except FileNotFoundError:
            continue
        universe.append(slug)
        for who in was:
            before[who].add(slug)
        for who in now:
            after[who].add(slug)
        # Where post-cutoff merges actually happen. Control (c) needs this.
        merge_slots[slug] = sum(len(h.merged_prs) for h in now.values())

    movers = {w: (b, after[w] - b) for w, b in before.items() if after.get(w, set()) - b}
    transitions = [(w, sorted(b)[0], d) for w, (b, a) in movers.items() for d in a]
    landed = sum(1 for _, _, d in transitions if d in viable)

    print("THE CLAIM, reproduced from committed fixtures\n")
    print(f"  universe                      {len(universe)} repositories, "
          f"{len(set(universe) & viable)} L1-viable")
    print(f"  contributors merged before T  {len(before)}")
    print(f"  movers                        {len(movers)}")
    print(f"  transitions                   {len(transitions)}")
    print(f"  landed in a viable repository {landed} = {landed/len(transitions):.0%}")
    naive = len(set(universe) & viable) / len(universe)
    print(f"  against a naive base rate of  {naive:.0%}    <- the apparent lift")

    print("\n" + "=" * 66)
    print("CONTROL (a) — it is one programme, not a preference\n")
    inside = [t for t in transitions if t[1] in COHORT and t[2] in COHORT]
    print(f"  transitions with BOTH endpoints inside one 9-repository cluster: "
          f"{len(inside)}/{len(transitions)} ({len(inside)/len(transitions):.0%})")
    print("  Those nine repositories are GirlScript Summer of Code '26 projects with a")
    print("  points leaderboard. Contributors move between them because they are")
    print("  enrolled in the same programme. Programme membership is a common cause of")
    print("  both the move and the merge; it is not evidence that anything was chosen.")

    print("\nCONTROL (b) — outside the cluster the signal inverts\n")
    outside = [t for t in transitions if t not in inside]
    good = [t for t in outside if t[2] in viable]
    print(f"  transitions outside it: {len(outside)}, of which into viable: {len(good)}")
    for who, src, dst in sorted(outside, key=lambda t: t[2] not in viable):
        flag = "viable" if dst in viable else "  not "
        note = "  <- deleted-account placeholder, not a person" if who == DELETED_ACCOUNT else ""
        print(f"    [{flag}] {who:<24} {src[:28]:<30} -> {dst}{note}")
    print("\n  One of the two 'organic into-viable' cases is GitHub's deleted-account")
    print("  placeholder, which aliases many different people into one login. The")
    print("  independent evidence is a single transition.")

    print("\nCONTROL (c) — the base rate is the wrong null\n")
    total = sum(merge_slots.values())
    in_viable = sum(v for s, v in merge_slots.items() if s in viable)
    print(f"  A mover can only appear where an outsider's pull request merges, and")
    print(f"  L1-viability is *defined* by outsider merges. Weighting by where merges")
    print(f"  actually happen: {in_viable:,}/{total:,} post-cutoff merge slots sit in")
    print(f"  viable repositories = {in_viable/total:.0%}, not {naive:.0%}.")
    print(f"  The lift falls from {landed/len(transitions)-naive:+.0%} to "
          f"{landed/len(transitions)-in_viable/total:+.0%}, and control (a) accounts for that.")

    print("\nCONTROL (d) — the cheap comparator wins outright\n")
    destinations: dict[str, Counter] = defaultdict(Counter)
    for _, src, dst in transitions:
        destinations[src][dst] += 1
    top1 = top3 = 0
    for _, src, dst in transitions:
        counts = Counter(destinations[src])
        counts[dst] -= 1  # leave-one-out: never score a transition against itself
        ranked = [r for r, n in counts.most_common() if n > 0]
        top1 += ranked[:1] == [dst]
        top3 += dst in ranked[:3]
    print(f"  'where else did people from your repository go' predicts the exact")
    print(f"  destination: top-1 {top1}/{len(transitions)} ({top1/len(transitions):.0%}), "
          f"top-3 {top3}/{len(transitions)} ({top3/len(transitions):.0%}).")
    print(f"  A viability filter only narrows {len(universe)} repositories to "
          f"{len(set(universe) & viable)}. The cheap signal answers a strictly harder")
    print(f"  question — which one — and answers it well.")

    print("\n" + "=" * 66)
    print("VERDICT: personalised discovery is not built. The apparent lift is one")
    print("programme cohort, measured against the wrong null, and a free co-occurrence")
    print("heuristic beats anything the viability filter could contribute.")


if __name__ == "__main__":
    main()
