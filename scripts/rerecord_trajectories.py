"""Re-record every model trajectory against the current prompts. Costs money.

Any change to a stage prompt or a stage's pinned model invalidates the recorded
trajectories: replay keys cover the prompt text, so a replay after the change
fails loudly instead of serving stale answers. This is the one command that
brings every recording back in line — the pool repositories from their committed
fixtures, and each discover session's analysed survivors from theirs.

Run:  PYTHONPATH=. uv run python scripts/rerecord_trajectories.py
      (needs OPENAI_API_KEY; roughly $1 for the pools at gpt-5-mini prices)
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from holt.agent.pipeline import analyze
from holt.discover import full_root, trajectory_for
from holt.evidence.fixtures import FixtureProvider
from holt.model import OpenAIModel, TRAJECTORY_DIR
from holt.types import Window


def rerecord(slug: str, provider: FixtureProvider, path: Path) -> float:
    path.unlink(missing_ok=True)
    client = OpenAIModel(path)
    started = time.monotonic()
    assessment, _ = analyze(slug, provider, client)
    print(f"  {time.monotonic() - started:5.0f}s  ${client.usage.cost_usd:.4f}  "
          f"{assessment.verdict.value:<22} {slug}", flush=True)
    return client.usage.cost_usd


def main() -> None:
    spent = 0.0
    failed: list[str] = []

    slugs: list[str] = []
    for pool in ("eval/pool.json", "eval/pool2.json"):
        slugs += json.loads(Path(pool).read_text())["repos"]
    print(f"pools: {len(slugs)} repositories")
    for i, slug in enumerate(slugs, 1):
        provider = FixtureProvider(Window.PRE_T)
        path = TRAJECTORY_DIR / (slug.replace("/", "__") + ".jsonl")
        try:
            provider.fetch(slug)
        except FileNotFoundError:
            continue
        print(f"[{i}/{len(slugs)}]", flush=True)
        try:
            spent += rerecord(slug, provider, path)
        except Exception as err:
            failed.append(slug)
            print(f"  FAILED {slug}: {err}", flush=True)

    for manifest_file in sorted(Path("fixtures/discover").glob("*.json")):
        manifest = json.loads(manifest_file.read_text())
        as_of = datetime.fromisoformat(manifest["as_of"])
        name = manifest["name"]
        print(f"discover session {name!r}: {len(manifest['analysed'])} analysed survivors")
        for slug in manifest["analysed"]:
            provider = FixtureProvider(Window.PRE_T, root=full_root(name), cutoff=as_of)
            try:
                spent += rerecord(slug, provider, trajectory_for(slug))
            except Exception as err:
                failed.append(slug)
                print(f"  FAILED {slug}: {err}", flush=True)

    print(f"\nspend ${spent:.3f}; failed {len(failed)}: {failed}")


if __name__ == "__main__":
    main()
