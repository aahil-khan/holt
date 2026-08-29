#!/usr/bin/env bash
set -u
out=data/gharchive
for day in 2026-05-27 2026-05-28 2026-05-29 2026-05-30; do
  for hr in 0 6 12 18; do
    f="$day-$hr.json.gz"
    [ -s "$out/$f" ] && continue
    curl -sfS -o "$out/$f" "https://data.gharchive.org/$f" || echo "FAILED $f"
  done
done
echo "DOWNLOAD_COMPLETE files=$(find $out -name '*.json.gz' | wc -l) bytes=$(du -sb $out | cut -f1)"
