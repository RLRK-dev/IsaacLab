#!/usr/bin/env bash
# Layer 5: NEST freshness — silent-lapse guard.
#
# Surfaces (WARN-only, never FAIL) the conditions under which NEST tracking can
# silently lapse without anyone noticing (cf. the 2026-05-05/2026-05-13 freeze):
#   D1 snapshot-sync       : a node state.md is newer than nest-snapshot.json
#                            (snapshot not rebuilt after a node change)
#   D2 node heartbeat      : newest node state.md older than MAX_DAYS
#                            (active work not being node-ized)
#   D3 manifest freshness  : project-tree-manifest.md last_updated older than MAX_DAYS
#   D4 trial review overdue: a KN-Method-*.md still in trial status whose scheduled
#                            review date has already passed (e.g. Neumann 1ヶ月レビュー)
#
# WARN-only by design: a stale NEST should be made visible, not block work.
# Threshold tunable: NEST_FRESHNESS_MAX_DAYS (default 14).
#
# validate.sh layer contract: emits human lines + LAYER5_FAIL=/LAYER5_WARN= at end.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VAULT_ROOT="$REPO_ROOT/thread_isaac_lab/thread-vault"
MANIFEST="$VAULT_ROOT/00-Project-Management/project-tree-manifest.md"
SNAPSHOT="$REPO_ROOT/docs/nest-tracker/nest-snapshot.json"
KN_DIR="$VAULT_ROOT/06-Knowledge"

MAX_DAYS="${NEST_FRESHNESS_MAX_DAYS:-14}"

# validate.sh passes: $1=STAGED_ONLY $2=IGNORE_FILE (IGNORE_FILE unused here)
STAGED_ONLY="${1:-false}"

FAIL_COUNT=0   # WARN-only layer: always 0
WARN_COUNT=0
NOW_EPOCH=$(date +%s)

echo "=== Layer 5: NEST Freshness (silent-lapse guard, WARN-only, max_days=${MAX_DAYS}) ==="

# Repo-state heartbeat, not a per-file check: skip in staged-only (pre-commit) mode.
if [ "$STAGED_ONLY" = "true" ]; then
    echo "  [SKIP] NEST freshness is a repo-state check (not staged-file scoped)"
    echo "LAYER5_FAIL=0"
    echo "LAYER5_WARN=0"
    exit 0
fi

# --- newest node state.md (used by D1 + D2) ---
newest_state_epoch=0
newest_state_file=""
while IFS= read -r f; do
    [ -n "$f" ] || continue
    m=$(stat -c %Y "$f" 2>/dev/null || echo 0)
    if [ "${m:-0}" -gt "$newest_state_epoch" ]; then
        newest_state_epoch=$m
        newest_state_file=$f
    fi
done < <(find "$VAULT_ROOT" -name state.md 2>/dev/null)

# --- D1: snapshot sync ---
if [ ! -f "$SNAPSHOT" ]; then
    echo "  [WARN] D1 nest-snapshot.json missing: ${SNAPSHOT#"$REPO_ROOT"/}"
    WARN_COUNT=$((WARN_COUNT + 1))
elif [ "$newest_state_epoch" -gt 0 ]; then
    snap_epoch=$(stat -c %Y "$SNAPSHOT" 2>/dev/null || echo 0)
    if [ "$newest_state_epoch" -gt "${snap_epoch:-0}" ]; then
        echo "  [WARN] D1 snapshot stale: a node state.md is newer than nest-snapshot.json"
        echo "         newest node: ${newest_state_file#"$REPO_ROOT"/}"
        echo "         fix: env_isaaclab/bin/python scripts/build_nest_snapshot.py"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
fi

# --- D2: node-tracking heartbeat ---
if [ "$newest_state_epoch" -gt 0 ]; then
    age_days=$(( (NOW_EPOCH - newest_state_epoch) / 86400 ))
    if [ "$age_days" -gt "$MAX_DAYS" ]; then
        echo "  [WARN] D2 node-tracking lapse: newest NEST node touched ${age_days}d ago (> ${MAX_DAYS}d)"
        echo "         is active work being node-ized? (NEST LTM-1 §2.1)"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
fi

# --- D3: manifest last_updated freshness ---
if [ -f "$MANIFEST" ]; then
    lu=$(grep -m1 '^last_updated:' "$MANIFEST" 2>/dev/null | sed 's/^last_updated:[[:space:]]*//' | cut -dT -f1)
    if [ -n "${lu:-}" ]; then
        lu_epoch=$(date -d "$lu" +%s 2>/dev/null || echo 0)
        if [ "${lu_epoch:-0}" -gt 0 ]; then
            mage=$(( (NOW_EPOCH - lu_epoch) / 86400 ))
            if [ "$mage" -gt "$MAX_DAYS" ]; then
                echo "  [WARN] D3 manifest stale: project-tree-manifest.md last_updated ${lu} (${mage}d ago > ${MAX_DAYS}d)"
                WARN_COUNT=$((WARN_COUNT + 1))
            fi
        fi
    fi
fi

# --- D4: overdue trial-method reviews ---
# KN-Method-*.md still in trial status with a scheduled review date in the past.
if [ -d "$KN_DIR" ]; then
    while IFS= read -r kn; do
        [ -n "$kn" ] || continue
        status_line=$(grep -m1 '^- 状態:' "$kn" 2>/dev/null || echo "")
        # closed/terminal states: skip
        case "$status_line" in
            *CLOSED*|*ARCHIVED*|*WITHDRAWN*|*昇格済*|*採用済*|*adopted*|*ADOPTED*) continue ;;
        esac
        # only flag if still trial/open
        case "$status_line" in
            *trial*|*TRIAL*|*試走*) : ;;
            *) continue ;;
        esac
        # extract review dates from lines mentioning レビュー / review
        while IFS= read -r d; do
            [ -n "$d" ] || continue
            d_epoch=$(date -d "$d" +%s 2>/dev/null || echo 0)
            if [ "${d_epoch:-0}" -gt 0 ] && [ "$d_epoch" -lt "$NOW_EPOCH" ]; then
                echo "  [WARN] D4 trial review overdue: ${kn#"$REPO_ROOT"/}"
                echo "         scheduled review ${d} has passed but status is still trial — review or close it"
                WARN_COUNT=$((WARN_COUNT + 1))
            fi
        done < <(grep -iE 'レビュー|review' "$kn" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | sort -u)
    done < <(find "$KN_DIR" -maxdepth 1 -name 'KN-Method-*.md' 2>/dev/null)
fi

if [ "$WARN_COUNT" -eq 0 ]; then
    echo "  [PASS] NEST tracking, snapshot, manifest, and trial reviews are fresh"
fi

echo "LAYER5_FAIL=$FAIL_COUNT"
echo "LAYER5_WARN=$WARN_COUNT"
exit 0
