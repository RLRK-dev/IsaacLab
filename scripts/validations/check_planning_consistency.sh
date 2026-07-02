#!/usr/bin/env bash
# Layer 7: Planning-surface consistency
# (planning-surface consolidation, node T-ROOT-Planning-Surfaces-Consolidation-20260702, M3).
#
#   C1 staleness (WARN)       : a planning surface's last_updated lags log.md newest heading by >48h
#   C2 dangling refs (WARN)   : backtick `T-...` node-id refs not in the NEST node set (minus allowlist).
#                               WARN-first (day-1) by design; promote to FAIL after a 0-FP dry run.
#                               (sha-token leg is assessed in the dry-run FP report, not live day-1.)
#   C3 GEN drift (FAIL)       : manifest §2 GEN region != build_nest_snapshot.py --check-manifest-section
#   C4 uncommitted-age (WARN) : a core planning file has uncommitted changes AND last commit >24h ago
#                               (commit-age, not mtime), minus planning_pending_rs.txt suppressions
#   C5 UPDATE-freeze (FAIL)   : manifest '^## UPDATE' count > frozen baseline (0) — append-log ban
#
# validate.sh layer contract: emits human lines + LAYER7_FAIL=/LAYER7_WARN= at end.
# The contract lines are emitted from an EXIT trap so a crash cannot fail-open to PASS
# (validate.sh discards the exit code and reads only the contract lines).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VAULT="$REPO_ROOT/thread_isaac_lab/thread-vault"
MANIFEST="$VAULT/00-Project-Management/project-tree-manifest.md"
MAP="$REPO_ROOT/docs/logical_decomposition.html"
LEDGER="$VAULT/07-Design/00-DESIGN-STATUS-LEDGER.md"
SOMA="$VAULT/04-Specs/SOMA.md"
INDEX="$VAULT/index.md"
LOG="$VAULT/log.md"
SNAPSHOT="$REPO_ROOT/docs/nest-tracker/nest-snapshot.json"
GEN="$REPO_ROOT/scripts/build_nest_snapshot.py"
PY="$REPO_ROOT/env_isaaclab/bin/python"
ALLOWLIST="$(cd "$(dirname "$0")" && pwd)/planning_dangling_allowlist.txt"
SUPPRESS="$(cd "$(dirname "$0")" && pwd)/planning_pending_rs.txt"

STAGED_ONLY="${1:-false}"
STALE_DAYS="${PLANNING_STALE_DAYS:-2}"            # C1: 48h
UNCOMMITTED_DAYS="${PLANNING_UNCOMMITTED_DAYS:-1}" # C4: 24h

FAIL_COUNT=0
WARN_COUNT=0
NOW=$(date +%s)
TMP=""
trap '[ -n "${TMP:-}" ] && rm -rf "$TMP"; echo "LAYER7_FAIL=${FAIL_COUNT:-1}"; echo "LAYER7_WARN=${WARN_COUNT:-0}"' EXIT

echo "=== Layer 7: Planning-surface consistency (M3) ==="

if [ "$STAGED_ONLY" = "true" ]; then
    echo "  [SKIP] repo-state check (not staged-file scoped; cf. layer 5)"
    exit 0
fi

TMP=$(mktemp -d)
_epoch() { date -d "$1" +%s 2>/dev/null || echo 0; }

# ---------------- C1 staleness (WARN) ----------------
log_newest=$(grep -oE '^## 2026-[0-9]{2}-[0-9]{2}' "$LOG" 2>/dev/null | grep -oE '2026-[0-9]{2}-[0-9]{2}' | sort | tail -1)
if [ -n "$log_newest" ]; then
    log_epoch=$(_epoch "$log_newest")
    _c1() {  # $1=label $2=date
        [ -n "$2" ] || return 0
        local se d; se=$(_epoch "$2"); [ "${se:-0}" -gt 0 ] || return 0
        d=$(( (log_epoch - se) / 86400 ))
        if [ "$d" -gt "$STALE_DAYS" ]; then
            echo "  [WARN] C1 $1 stale: last_updated $2 lags log.md newest ($log_newest) by ${d}d (>${STALE_DAYS}d)"
            WARN_COUNT=$((WARN_COUNT + 1))
        fi
    }
    _c1 manifest "$(grep -m1 '^last_updated:' "$MANIFEST" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"
    _c1 map "$(grep -m1 'last_updated:' "$MAP" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"
    _c1 LEDGER "$(grep -m1 -iE 'as of|last[_ ]updated' "$LEDGER" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"
else
    echo "  [INFO] C1 skipped: no '^## 2026-' heading in log.md"
fi

# ---------------- C2 dangling node-id refs (WARN-first) ----------------
if [ -f "$SNAPSHOT" ] && [ -x "$PY" ]; then
    "$PY" -c "import json;[print(n['id']) for n in json.load(open('$SNAPSHOT'))['nodes']]" 2>/dev/null | sort -u > "$TMP/nodeset"
    if [ -f "$ALLOWLIST" ]; then grep -vE '^\s*#' "$ALLOWLIST" | grep -oE 'T-[A-Za-z0-9_.-]+' | sort -u > "$TMP/allow"; else : > "$TMP/allow"; fi
    # candidate backtick node-ids from surfaces, EXCLUDING the manifest GEN region (self-consistent)
    { sed '/GEN:NEST:BEGIN/,/GEN:NEST:END/d' "$MANIFEST" 2>/dev/null; cat "$MAP" "$LEDGER" "$INDEX" 2>/dev/null; } \
        | grep -oE '`T-[A-Za-z0-9_.-]+`' | tr -d '`' | sort -u > "$TMP/cands"
    comm -23 "$TMP/cands" "$TMP/nodeset" | comm -23 - "$TMP/allow" > "$TMP/dangling"
    while IFS= read -r nid; do
        [ -n "$nid" ] || continue
        echo "  [WARN] C2 dangling node-id ref: \`$nid\` not in NEST node set (nor allowlist)"
        WARN_COUNT=$((WARN_COUNT + 1))
    done < "$TMP/dangling"
    soma_n=$(grep -oE '`T-[A-Za-z0-9_.-]+`' "$SOMA" 2>/dev/null | tr -d '`' | sort -u | comm -23 - "$TMP/nodeset" | comm -23 - "$TMP/allow" | grep -c .)
    soma_n=$(printf '%s' "${soma_n:-0}" | tr -dc '0-9'); soma_n=${soma_n:-0}
    if [ "$soma_n" -gt 0 ]; then
        echo "  [WARN] C2 SOMA has ${soma_n} dangling node-id ref(s) — permanent WARN (04-Specs = Rs 専権)"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    echo "  [INFO] C2 = WARN-first (day-1); sha-token leg + FAIL-promotion via dry-run FP report (M3 deliverable)"
else
    echo "  [WARN] C2 skipped: nest-snapshot.json or python missing"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

# ---------------- C3 GEN drift (FAIL) ----------------
if [ -x "$PY" ] && [ -f "$GEN" ]; then
    if "$PY" "$GEN" --check-manifest-section >/dev/null 2>&1; then
        echo "  [PASS] C3 manifest §2 GEN region in sync with generator"
    else
        echo "  [FAIL] C3 GEN drift: manifest §2 != generator (fix: build_nest_snapshot.py --emit-manifest-section)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    echo "  [WARN] C3 skipped: generator or python missing"
    WARN_COUNT=$((WARN_COUNT + 1))
fi

# ---------------- C4 uncommitted-age (WARN) ----------------
for f in "$MAP" "$MANIFEST" "$LEDGER" "$REPO_ROOT/GOALS.md" "$INDEX"; do
    rel=${f#"$REPO_ROOT"/}
    st=$(git -C "$REPO_ROOT" status --porcelain -- "$f" 2>/dev/null)
    [ -n "$st" ] || continue
    if [ -f "$SUPPRESS" ] && grep -qF -- "$rel" "$SUPPRESS" 2>/dev/null; then continue; fi
    lc=$(git -C "$REPO_ROOT" log -1 --format=%ct -- "$f" 2>/dev/null)
    if [ -n "$lc" ]; then
        age=$(( (NOW - lc) / 86400 ))
        if [ "$age" -gt "$UNCOMMITTED_DAYS" ]; then
            echo "  [WARN] C4 uncommitted-age: $rel has uncommitted changes; last commit ${age}d ago (>${UNCOMMITTED_DAYS}d)"
            WARN_COUNT=$((WARN_COUNT + 1))
        fi
    else
        echo "  [WARN] C4 uncommitted: $rel untracked / no commit history (register in planning_pending_rs.txt if intentional)"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
done

# ---------------- C5 UPDATE-block freeze (FAIL) ----------------
FROZEN_UPDATE=0
upd=$(grep -c '^## UPDATE' "$MANIFEST" 2>/dev/null)
upd=$(printf '%s' "${upd:-0}" | tr -dc '0-9'); upd=${upd:-0}
if [ "$upd" -gt "$FROZEN_UPDATE" ]; then
    echo "  [FAIL] C5 UPDATE-block freeze: manifest has ${upd} '^## UPDATE' block(s) (frozen=${FROZEN_UPDATE}); node records -> state.md only"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
    echo "  [PASS] planning surfaces consistent (C1-C5 clean)"
fi
exit 0
