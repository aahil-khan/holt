"""Capture pre-T and post-T evidence for every repository in the committed pool.

Two passes per repo, one per side of the holdout, written to separate directories.
The provider asserts the window on every record, so a capture that would mix the
two fails here rather than silently poisoning a label months of work later.

Run:  uv run python scripts/capture_fixtures.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from holt.evidence.fixtures import FIXTURE_ROOT, write_fixture
from holt.evidence.github_graphql import GitHubGraphQL, LiveGitHubProvider
from holt.types import Window

POOL = Path("eval/pool.json")
# Pre-T is what the agent reads: recent threads before the cutoff. Post-T is what
# labels are computed from, so it wants fuller coverage of the window.
PAGES = {Window.PRE_T: 8, Window.POST_T: 20}


def main() -> None:
    repos: list[str] = json.loads(POOL.read_text())["repos"]
    transport = GitHubGraphQL()
    failures: dict[str, str] = {}

    for i, slug in enumerate(repos, 1):
        for window in (Window.PRE_T, Window.POST_T):
            target = FIXTURE_ROOT / window.value / (slug.replace("/", "__") + ".json")
            if target.exists():
                print(f"[{i}/{len(repos)}] {slug} {window.value}: already captured", flush=True)
                continue
            try:
                provider = LiveGitHubProvider(window, transport=transport, max_pages=PAGES[window])
                records = provider.fetch(slug)
                write_fixture(slug, window, records)
                print(
                    f"[{i}/{len(repos)}] {slug} {window.value}: {len(records)} records "
                    f"(rate {transport.remaining})",
                    flush=True,
                )
            except Exception as exc:
                failures[f"{slug}:{window.value}"] = f"{type(exc).__name__}: {exc}"
                print(f"[{i}/{len(repos)}] {slug} {window.value}: FAILED {exc}", flush=True)
            time.sleep(0.3)

    print(f"\nCAPTURE_COMPLETE ok={len(repos) * 2 - len(failures)} failed={len(failures)}")
    for key, reason in failures.items():
        print(f"  {key}: {reason}")
    if failures:
        Path("fixtures/capture_failures.json").write_text(json.dumps(failures, indent=1) + "\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
