"""Re-scrub every committed fixture and report exactly what changed.

Run after `scripts/capture_fixtures.py` or `scripts/capture_issues.py`, and once
over the whole tree whenever the patterns in `holt.evidence.redact` change. It
rewrites in place and recomputes the content hash, so a fixture that changes here
is a fixture whose hash moves — which is the point: the committed hash must
describe the committed bytes.

Run:  PYTHONPATH=. uv run python scripts/redact_fixtures.py [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from holt.evidence.fixtures import content_hash, record_from_dict, record_to_dict, redact_records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report without writing; exit non-zero if anything would change")
    ap.add_argument("--root", default="fixtures")
    args = ap.parse_args()

    dirty = total = 0
    for path in sorted(Path(args.root).rglob("*.json")):
        data = json.loads(path.read_text())
        if "records" not in data:
            continue
        records, removed = redact_records(record_from_dict(r) for r in data["records"])
        if not removed:
            continue
        dirty += 1
        total += removed
        print(f"  {removed:>3} secret(s)  {path}")
        if args.check:
            continue
        data["records"] = [record_to_dict(r) for r in records]
        data["content_sha256"] = content_hash(records)
        data["credentials_redacted"] = removed
        path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")

    verb = "would be removed from" if args.check else "removed from"
    print(f"{total} credential-shaped string(s) {verb} {dirty} fixture(s)")
    if args.check and dirty:
        sys.exit(1)


if __name__ == "__main__":
    main()
