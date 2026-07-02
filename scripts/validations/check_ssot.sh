#!/usr/bin/env bash
# Layer 1: SSOT Integrity Checks
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TASK_CONFIG="$REPO_ROOT/thread_isaac_lab/configs/task_config.py"
CLAUDE_MD="$REPO_ROOT/CLAUDE.md"
THREAD_DIR="$REPO_ROOT/thread_isaac_lab"

STAGED_ONLY="${1:-false}"
IGNORE_FILE="${2:-}"
FAIL_COUNT=0
WARN_COUNT=0

# Filter file list through .validateignore
apply_ignore() {
    if [ -n "$IGNORE_FILE" ] && [ -s "$IGNORE_FILE" ]; then
        grep -v -F -f "$IGNORE_FILE"
    else
        cat
    fi
}

# ─── Check 1: Hardcoded task_config.py constants ───
check_hardcoded_constants() {
    echo "  [CHECK 1] task_config.py parameter hardcoding"

    if [ ! -f "$TASK_CONFIG" ]; then
        echo "  [WARN] task_config.py not found"
        WARN_COUNT=$((WARN_COUNT + 1))
        return
    fi

    local constants_list
    constants_list=$(grep -oE '^[A-Z][A-Z0-9_]+' "$TASK_CONFIG" | sort -u)
    [ -z "$constants_list" ] && { echo "  [PASS] No constants found"; return; }

    local pattern
    pattern="^($(echo "$constants_list" | tr '\n' '|' | sed 's/|$//')) *= *[0-9(\"'\\[]"

    local tmpfiles
    tmpfiles=$(mktemp)
    if [ "$STAGED_ONLY" = "true" ]; then
        git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR -- "$THREAD_DIR" \
            | grep '\.py$' | grep -v 'task_config\.py$' | grep -v '\.bak' \
            | while read -r f; do echo "$REPO_ROOT/$f"; done | apply_ignore > "$tmpfiles"
    else
        find "$THREAD_DIR" -name "*.py" -not -name "*.bak*" -not -path "*/.git/*" \
            -not -name "task_config.py" 2>/dev/null | apply_ignore > "$tmpfiles" || true
    fi

    if [ ! -s "$tmpfiles" ]; then
        echo "  [PASS] No files to check"
        rm -f "$tmpfiles"
        return
    fi

    local tmpresults
    tmpresults=$(mktemp)
    xargs grep -PnH "$pattern" < "$tmpfiles" 2>/dev/null \
        | grep -v "task_config" \
        | grep -v "^\s*#" > "$tmpresults" || true

    if [ ! -s "$tmpresults" ]; then
        echo "  [PASS] No hardcoded task_config constants found"
    else
        while IFS= read -r line; do
            echo "  [FAIL] Hardcoded constant: $line"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        done < "$tmpresults"
    fi

    rm -f "$tmpfiles" "$tmpresults"
}

# ─── Check 2: Golden file drift ───
check_golden_files() {
    echo "  [CHECK 2] Golden file drift"

    local tmpgolden
    tmpgolden=$(mktemp)
    find "$REPO_ROOT" -name "*.golden" -not -path "*/.git/*" 2>/dev/null | apply_ignore > "$tmpgolden" || true

    if [ ! -s "$tmpgolden" ]; then
        echo "  [PASS] No golden files found"
        rm -f "$tmpgolden"
        return
    fi

    local any_issue=false
    while IFS= read -r golden; do
        [ -z "$golden" ] && continue
        local actual="${golden%.golden}"

        if [ ! -f "$actual" ]; then
            echo "  [FAIL] Golden file has no corresponding source: $golden"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            any_issue=true
            continue
        fi

        if ! diff -q "$golden" "$actual" > /dev/null 2>&1; then
            echo "  [WARN] Golden file drift: $golden"
            WARN_COUNT=$((WARN_COUNT + 1))
            any_issue=true
        fi
    done < "$tmpgolden"

    if [ "$any_issue" = false ]; then
        echo "  [PASS] All golden files match"
    fi

    rm -f "$tmpgolden"
}

# ─── Check 3: Numeric parameters in CLAUDE.md ───
check_claude_md_numerics() {
    echo "  [CHECK 3] CLAUDE.md numeric parameter leakage"

    if [ ! -f "$CLAUDE_MD" ] || [ ! -f "$TASK_CONFIG" ]; then
        echo "  [PASS] CLAUDE.md or task_config.py not found"
        return
    fi

    local constants_list
    constants_list=$(grep -oE '^[A-Z][A-Z0-9_]+' "$TASK_CONFIG" | sort -u)
    local pattern
    pattern="($(echo "$constants_list" | tr '\n' '|' | sed 's/|$//')).*= *[0-9]"

    local tmpresults
    tmpresults=$(mktemp)
    grep -PnE "$pattern" "$CLAUDE_MD" 2>/dev/null \
        | grep -v "Isaac Sim [0-9]" \
        | grep -v "Python [0-9]" \
        | grep -v "cuda:[0-9]" \
        | grep -v "v[0-9]" > "$tmpresults" || true

    if [ ! -s "$tmpresults" ]; then
        echo "  [PASS] No task_config parameters hardcoded in CLAUDE.md"
    else
        while IFS= read -r line; do
            echo "  [FAIL] CLAUDE.md hardcoded param: $line"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        done < "$tmpresults"
    fi

    rm -f "$tmpresults"
}

# ─── Run ───
echo "=== Layer 1: SSOT Integrity ==="
check_hardcoded_constants
check_golden_files
check_claude_md_numerics

echo "LAYER1_FAIL=$FAIL_COUNT"
echo "LAYER1_WARN=$WARN_COUNT"
