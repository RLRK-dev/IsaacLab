#!/usr/bin/env bash
# check_map_freshness.sh — planning-map now-frame staleness guard (Rs 改善指示 2026-07-06).
# Compares the 地図 now-frame as-of date (docs/logical_decomposition.html 「今ここ (M/D ...)」)
# against the latest dated entry in the active node's state.md. Exit 0 = fresh (same day or newer),
# exit 3 = STALE (map older than state.md) — run at banking / joint-read / packet time.
set -u
MAP=/home/rlrk/IsaacLab/docs/logical_decomposition.html
STATE=${1:-/home/rlrk/IsaacLab/thread_isaac_lab/thread-vault/T-ROOT-optE-route-dapg-C1C2/state.md}

map_md=$(grep -o '今ここ ([0-9]*/[0-9]*' "$MAP" | head -1 | grep -o '[0-9]*/[0-9]*')
state_date=$(grep -oE '^- 20[0-9]{2}-[0-9]{2}-[0-9]{2}' "$STATE" | tail -1 | grep -oE '20[0-9]{2}-[0-9]{2}-[0-9]{2}')

if [ -z "$map_md" ] || [ -z "$state_date" ]; then
  echo "[MAP-FRESHNESS] PARSE-FAIL (map='$map_md' state='$state_date') — check formats"; exit 4
fi
# map date carries no year (M/D); resolve against the state year (maps update within days of state entries).
year=${state_date:0:4}
map_iso=$(printf '%s-%02d-%02d' "$year" "${map_md%%/*}" "${map_md##*/}")
# year-boundary guard: if that puts the map >6 months ahead of state, it was last year's date.
if [ "$(date -d "$map_iso" +%s)" -gt "$(date -d "$state_date + 180 days" +%s)" ]; then
  map_iso=$(printf '%s-%02d-%02d' "$((year-1))" "${map_md%%/*}" "${map_md##*/}")
fi

if [ "$(date -d "$map_iso" +%s)" -lt "$(date -d "$state_date" +%s)" ]; then
  echo "[MAP-FRESHNESS] STALE: map now-frame $map_iso < state.md latest $state_date — update the 地図 now-frame (short dashboard form) before banking"
  exit 3
fi
echo "[MAP-FRESHNESS] OK: map $map_iso >= state $state_date"
