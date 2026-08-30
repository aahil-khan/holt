"""Capture issue evidence for Path Finder, split across the holdout.

Written to `fixtures/issues_pre_t/` and `fixtures/issues_post_t/` rather than
into the existing directories, so adding this cannot invalidate the pull request
fixtures every current result depends on.

Run:  HOLT_POOL=eval/pool.json uv run python scripts/capture_issues.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from holt.evidence.fixtures import write_fixture
from holt.evidence.github_graphql import GitHubGraphQL, project_issues
from holt.types import T_CUTOFF, Window

POOL = Path(os.environ.get("HOLT_POOL", "eval/pool.json"))
ROOT = Path("fixtures/issues")


def main() -> None:
    repos = json.loads(POOL.read_text())["repos"]
    t = GitHubGraphQL()
    day = T_CUTOFF.date().isoformat()
    failures = {}

    for i, slug in enumerate(repos, 1):
        target = ROOT / Window.PRE_T.value / (slug.replace("/", "__") + ".json")
        if target.exists():
            print(f"[{i}/{len(repos)}] {slug}: already captured", flush=True)
            continue
        try:
            nodes = list(t.search_issues(f"repo:{slug} is:issue created:<{day}", max_pages=6))
            records = list(project_issues(slug, nodes))
            pre = [r for r in records if r.timestamp <= T_CUTOFF]
            post = [r for r in records if r.timestamp > T_CUTOFF]
            write_fixture(slug, Window.PRE_T, pre, root=ROOT)
            write_fixture(slug, Window.POST_T, post, root=ROOT)
            print(f"[{i}/{len(repos)}] {slug}: {len(pre)} pre-cutoff, {len(post)} post "
                  f"(rate {t.remaining})", flush=True)
        except Exception as exc:
            failures[slug] = f"{type(exc).__name__}: {exc}"
            print(f"[{i}/{len(repos)}] {slug}: FAILED {type(exc).__name__}", flush=True)
        time.sleep(0.2)

    print(f"\nISSUE_CAPTURE_COMPLETE ok={len(repos)-len(failures)} failed={len(failures)}")


if __name__ == "__main__":
    main()
