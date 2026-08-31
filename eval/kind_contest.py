"""Does contesting `repo_kind` ever contradict a *correct* classification?

`repo_kind` is the only model-derived field that decides a verdict on its own,
and Stage D cannot check it. `verdict.contested_kind` checks the reason the kind
rule would give against evidence already crawled. The number that matters for
such a rule is not how often it fires -- it is how often it fires on a
classification that was right, because dropping a true `registry` would cost the
project a rule the benchmark rests on.

So this scores specificity over every recorded classification in both pools: the
`repo_kind` the model actually produced, replayed from the committed
trajectories, against the committed fixtures. No model is called and nothing is
spent. Predictions and outcomes are in eval/PREREGISTRATION-4.md.

Run:  PYTHONPATH=. uv run python eval/kind_contest.py
"""

from __future__ import annotations

import json
import pathlib

from holt.agent.findings import Findings
from holt.agent.signals import build_threads, compute
from holt.agent.verdict import CATALOGUE_KINDS, CLOSED_KINDS, contested_kind
from holt.evidence.fixtures import FixtureProvider
from holt.model import TRAJECTORY_DIR
from holt.types import Window

POOLS = [
    ("pool 1 (thresholds chosen here)", "eval/pool.json", ["", "run1", "run2", "run3"]),
    ("pool 2 (out-of-sample)", "eval/pool2.json", ["", "p2r1", "p2r2", "p2r3"]),
]
CONTESTABLE = CATALOGUE_KINDS | CLOSED_KINDS


def recorded_kind(slug: str, tag: str) -> str | None:
    root = TRAJECTORY_DIR / tag if tag else TRAJECTORY_DIR
    path = root / (slug.replace("/", "__") + ".jsonl")
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.strip():
            entry = json.loads(line)
            if entry["label"] == "classify":
                return entry["response"]["repo_kind"]
    return None


def main() -> None:
    print("CONTESTED KINDS — does the rule ever contradict a correct classification?\n")
    for label, pool_file, tags in POOLS:
        slugs = json.loads(pathlib.Path(pool_file).read_text())["repos"]
        seen = contestable = fired = 0
        for slug in slugs:
            records = None
            for tag in tags:
                kind = recorded_kind(slug, tag)
                if kind is None:
                    continue
                if records is None:
                    try:
                        records = FixtureProvider(Window.PRE_T).fetch(slug)
                    except FileNotFoundError:
                        break
                seen += 1
                contestable += kind in CONTESTABLE
                findings = Findings()
                findings.add("repo_kind", kind, evidence_ids=("recorded",))
                meta = next(
                    (r.payload for r in records if r.evidence_id.endswith(":meta")), {}
                )
                reason = contested_kind(findings, compute(build_threads(records)), meta)
                if reason:
                    fired += 1
                    print(f"  FIRED  {slug} [{tag or 'frozen'}]  {reason}")
        print(f"{label}: {fired} fired / {seen} classifications "
              f"({contestable} of a kind that can flip a verdict)\n")

    print("Every kind in both pools is correct, so any firing is a false accusation.")
    print("See eval/PREREGISTRATION-4.md — an earlier criterion fired on")
    print("microsoft/winget-pkgs, a real registry, and was removed rather than tuned.")


if __name__ == "__main__":
    main()
