#!/usr/bin/env bash
# Fetch GH Archive hourly event files for the days before the holdout cutoff.
#
# Contiguous full days, not a spread of sampled hours: a repo doing ~100 PRs a
# month appears 0-1 times in a thin sample, which makes in-window PR count a
# noisy proxy for activity and the volume strata degenerate.
set -u
out=data/gharchive
mkdir -p "$out"
for day in "$@"; do
  for hr in $(seq 0 23); do
    f="$day-$hr.json.gz"
    [ -s "$out/$f" ] && continue
    curl -sfS -o "$out/$f" "https://data.gharchive.org/$f" || echo "FAILED $f"
  done
  echo "  $day done ($(find $out -name '*.json.gz' | wc -l) files so far)"
done
echo "DOWNLOAD_COMPLETE files=$(find $out -name '*.json.gz' | wc -l) bytes=$(du -sb $out | cut -f1)"
