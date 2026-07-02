#!/usr/bin/env bash
# Layer 2: Structural Boundary Enforcement
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
THREAD_DIR="$REPO_ROOT/thread_isaac_lab"

STAGED_ONLY="${1:-false}"
IGNORE_FILE="${2:-}"
FAIL_COUNT=0
WARN_COUNT=0

apply_ignore() {
    if [ -n "$IGNORE_FILE" ] && [ -s "$IGNORE_FILE" ]; then
        grep -v -F -f "$IGNORE_FILE"
    else
        cat
    fi
}

# ─── Check 4: Japanese text in Python source ───
check_japanese_text() {
    echo "  [CHECK 4] Japanese text in Python code"

    local tmpfiles
    tmpfiles=$(mktemp)
    if [ "$STAGED_ONLY" = "true" ]; then
        git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR -- "$THREAD_DIR" \
            | grep '\.py$' | grep -v '\.bak' \
            | while read -r f; do echo "$REPO_ROOT/$f"; done | apply_ignore > "$tmpfiles"
    else
        find "$THREAD_DIR" -name "*.py" -not -name "*.bak*" -not -path "*/.git/*" \
            2>/dev/null | apply_ignore > "$tmpfiles" || true
    fi

    if [ ! -s "$tmpfiles" ]; then
        echo "  [PASS] No Python files to check"
        rm -f "$tmpfiles"
        return
    fi

    local tmpresults
    tmpresults=$(mktemp)
    xargs grep -PnH --binary-files=without-match '[\x{3000}-\x{9FFF}]' < "$tmpfiles" 2>/dev/null \
        | grep -E ':\s*#|:\s*"""|:\s*'"'"'""' > "$tmpresults" || true

    if [ ! -s "$tmpresults" ]; then
        echo "  [PASS] No Japanese text in Python source"
    else
        while IFS= read -r line; do
            local short
            short=$(echo "$line" | head -c 120)
            echo "  [FAIL] Japanese text: $short"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        done < "$tmpresults"
    fi

    rm -f "$tmpfiles" "$tmpresults"
}

# ─── Check 5: Import direction verification ───
check_import_direction() {
    echo "  [CHECK 5] Import direction (config -> scripts reverse dependency)"

    local config_files=(
        "$THREAD_DIR/configs/task_config.py"
        "$THREAD_DIR/envs/dual_arm_cfg.py"
    )

    local any_fail=false

    for cfg in "${config_files[@]}"; do
        [ -f "$cfg" ] || continue

        local tmpresults
        tmpresults=$(mktemp)

        grep -n "from.*scripts" "$cfg" 2>/dev/null | grep -v "^\s*#" > "$tmpresults" || true
        grep -n "from.*collect_demo\|from.*train_\|from.*poc_" "$cfg" 2>/dev/null \
            | grep -v "^\s*#" >> "$tmpresults" || true

        if [ -s "$tmpresults" ]; then
            while IFS= read -r match; do
                echo "  [FAIL] Reverse dependency: ${cfg}:${match}"
                FAIL_COUNT=$((FAIL_COUNT + 1))
                any_fail=true
            done < "$tmpresults"
        fi

        rm -f "$tmpresults"
    done

    if [ "$any_fail" = false ]; then
        echo "  [PASS] Import direction is correct (scripts -> configs)"
    fi
}

# ─── Run ───
echo "=== Layer 2: Structural Boundaries ==="
check_japanese_text
check_import_direction

echo "LAYER2_FAIL=$FAIL_COUNT"
echo "LAYER2_WARN=$WARN_COUNT"
