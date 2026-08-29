"""Build the repository sampling frame from GH Archive events at T.

Why not just search GitHub today: the Search API reflects *today's* stars and
today's activity no matter what date filter is applied, so a pool drawn from it
is pre-filtered for repos that survived past T. That is survivorship bias baked
into the sampling frame, and no amount of care downstream removes it.

GH Archive is an hourly record of public events as they happened. Sampling from
events in the days before T gives a frame of repos as they appeared at T, with
no knowledge of which ones were still alive in August.

Run:  uv run python eval/build_frame.py
Out:  eval/frame.json
"""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path

ARCHIVE_DIR = Path("data/gharchive")
OUT = Path("eval/frame.json")

# Cheap substring gate before json.loads: PullRequestEvent is a small slice of
# all events, and parsing every line costs far more than scanning for one.
MARKER = b'"PullRequestEvent"'

BOT_SUFFIX = "[bot]"
KNOWN_BOTS = {"dependabot", "renovate", "greenkeeper", "imgbot", "allcontributors"}


def is_bot(login: str) -> bool:
    low = login.lower()
    return low.endswith(BOT_SUFFIX) or low in KNOWN_BOTS


def main() -> None:
    opened: dict[str, int] = defaultdict(int)
    actors: dict[str, set[str]] = defaultdict(set)
    bot_opened: dict[str, int] = defaultdict(int)
    files = sorted(ARCHIVE_DIR.glob("*.json.gz"))
    if not files:
        raise SystemExit(f"No archives in {ARCHIVE_DIR}; run scripts/fetch_gharchive.sh first")

    scanned = 0
    unreadable: list[str] = []
    for path in files:
        try:
            with gzip.open(path, "rb") as handle:
                for line in handle:
                    if MARKER not in line:
                        continue
                    event = json.loads(line)
                    if event.get("type") != "PullRequestEvent":
                        continue
                    if event.get("payload", {}).get("action") != "opened":
                        continue
                    scanned += 1
                    repo = event["repo"]["name"]
                    login = (event.get("actor") or {}).get("login", "")
                    if is_bot(login):
                        bot_opened[repo] += 1
                        continue
                    opened[repo] += 1
                    actors[repo].add(login)
        except (EOFError, OSError) as exc:
            # An archive that is bad as served would otherwise kill a run several
            # minutes in. Record it in the frame so the gap is auditable rather
            # than silently narrowing the universe.
            unreadable.append(path.name)
            print(f"  UNREADABLE {path.name}: {type(exc).__name__}", flush=True)
            continue
        print(f"  scanned {path.name}: running total {scanned} opened-PR events", flush=True)

    frame = {
        repo: {
            "prs_opened": count,
            "distinct_openers": len(actors[repo]),
            "bot_prs_opened": bot_opened.get(repo, 0),
        }
        for repo, count in opened.items()
    }
    readable = [f.name for f in files if f.name not in unreadable]
    OUT.write_text(
        json.dumps(
            {
                "source_files": readable,
                "unreadable_files": unreadable,
                "opened_pr_events": scanned,
                "repos": frame,
            }
        )
        + "\n"
    )
    print(f"frame: {len(frame)} repos with >=1 human-opened PR, from {scanned} events")
    if unreadable:
        print(f"WARNING: {len(unreadable)} archives unreadable and excluded: {unreadable}")


if __name__ == "__main__":
    main()
