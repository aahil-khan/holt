"""How much evidence does Holt actually read, and could a person paste it?

The most common objection to a tool like this is "just paste the repo into
ChatGPT". This measures the premise rather than arguing with it.

`baseline` — the README plus repository metadata, one prompt — *is* what a person
pastes. It is already a scored arm in `eval/harness.py`. This script measures the
gap in raw material between that and what Holt assembles: how many records, how
many characters, how many separate pull-request conversations, and how many
distinct pages a person would have to open on github.com to see the same thing.

Nothing here calls a model. Run:
    PYTHONPATH=. uv run python eval/evidence_volume.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from holt.evidence.fixtures import FixtureProvider
from holt.types import Window

# github.com shows one pull request per page, and the repository landing page
# carries the README. A person checking Holt's evidence by hand opens that many
# tabs; there is no view that lists review states and reply latencies together.
LANDING_PAGES = 2  # the repository page and its CONTRIBUTING file


def payload_chars(record) -> int:
    return len(json.dumps(record.payload, separators=(",", ":")))


def main() -> None:
    pre = FixtureProvider(Window.PRE_T)
    slugs: list[str] = []
    for pool in ("eval/pool.json", "eval/pool2.json"):
        slugs += json.loads(Path(pool).read_text())["repos"]

    rows = []
    for slug in slugs:
        try:
            records = list(pre.fetch(slug))
        except FileNotFoundError:
            continue
        threads = {r.evidence_id.split(":")[1] for r in records if r.evidence_id.startswith("pr:")}
        # What a person pastes: the README, and the numbers on the repo page.
        pasteable = sum(
            payload_chars(r) for r in records
            if r.evidence_id.endswith((":readme", ":meta", ":contributing"))
        )
        rows.append({
            "repo": slug,
            "records": len(records),
            "chars": sum(payload_chars(r) for r in records),
            "threads": len(threads),
            "pasteable_chars": pasteable,
            "pages": len(threads) + LANDING_PAGES,
        })

    def col(key):
        return [r[key] for r in rows]

    print(f"Evidence assembled per repository, over {len(rows)} repositories\n")
    print(f"{'':<34}{'median':>12}{'mean':>12}{'max':>12}")
    for label, key in (("evidence records", "records"),
                       ("characters of evidence", "chars"),
                       ("pull-request conversations", "threads"),
                       ("github.com pages to see it", "pages")):
        v = col(key)
        print(f"{label:<34}{statistics.median(v):>12,.0f}{statistics.mean(v):>12,.0f}{max(v):>12,.0f}")

    total_chars = sum(col("chars"))
    total_paste = sum(col("pasteable_chars"))
    print(f"\nWhat a person can realistically paste — README, CONTRIBUTING and the\n"
          f"numbers on the repository page — against what Holt reads:\n")
    print(f"  pasteable            {statistics.median(col('pasteable_chars')):>10,.0f} characters (median)")
    print(f"  Holt                 {statistics.median(col('chars')):>10,.0f} characters (median)")
    print(f"  ratio                {total_chars / total_paste:>10,.1f}x")
    print(f"\n  across the whole evaluation: {total_chars:,} characters of evidence,")
    print(f"  {sum(col('records')):,} records, {sum(col('threads')):,} pull-request conversations,")
    print(f"  and {sum(col('pages')):,} github.com pages a person would have to open.")
    print(f"\nThe pasteable material is not a smaller sample of the same evidence. It\n"
          f"contains no review states, no reply latencies, and no record of what\n"
          f"happened to anyone who tried — which is the entire question.")

    Path("eval/evidence_volume.json").write_text(
        json.dumps({"per_repo": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
