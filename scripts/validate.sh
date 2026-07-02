#!/usr/bin/env bash
# validate.sh - Main validation script
# Usage:
#   scripts/validate.sh              # Run all layers (respects .validateignore)
#   scripts/validate.sh --layer 1    # Run specific layer only
#   scripts/validate.sh --staged-only # Only check git-staged files (pre-commit)
#   scripts/validate.sh --no-ignore  # Ignore .validateignore (check everything)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATIONS_DIR="$REPO_ROOT/scripts/validations"
IGNORE_FILE="$REPO_ROOT/.validateignore"

# Parse arguments
LAYER=""
STAGED_ONLY="false"
USE_IGNORE="true"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --layer)
            LAYER="$2"
            shift 2
            ;;
        --staged-only)
            STAGED_ONLY="true"
            shift
            ;;
        --no-ignore)
            USE_IGNORE="false"
            shift
            ;;
        *)
            echo "Usage: $0 [--layer N] [--staged-only] [--no-ignore]"
            exit 1
            ;;
    esac
done

# Build grep exclude pattern from .validateignore
IGNORE_GREP_FILE=""
if [ "$USE_IGNORE" = "true" ] && [ -f "$IGNORE_FILE" ]; then
    IGNORE_GREP_FILE=$(mktemp)
    # Convert ignore entries to grep -v patterns (strip comments/blanks, prefix with thread_isaac_lab/)
    grep -v '^\s*#' "$IGNORE_FILE" | grep -v '^\s*$' \
        | sed 's|^|/thread_isaac_lab/|' > "$IGNORE_GREP_FILE"
fi

export IGNORE_GREP_FILE STAGED_ONLY

TOTAL_FAIL=0
TOTAL_WARN=0

TMP_RESULT=$(mktemp)
trap "rm -f $TMP_RESULT $IGNORE_GREP_FILE" EXIT

run_layer() {
    local script="$1"
    "$script" "$STAGED_ONLY" "$IGNORE_GREP_FILE" > "$TMP_RESULT" 2>&1 || true

    grep -a -v "^LAYER[0-9]_" "$TMP_RESULT" || true

    local fail warn
    fail=$(grep -a "^LAYER.*_FAIL=" "$TMP_RESULT" | tail -1 | cut -d= -f2 || echo "0")
    warn=$(grep -a "^LAYER.*_WARN=" "$TMP_RESULT" | tail -1 | cut -d= -f2 || echo "0")
    TOTAL_FAIL=$((TOTAL_FAIL + ${fail:-0}))
    TOTAL_WARN=$((TOTAL_WARN + ${warn:-0}))
}

echo "╔══════════════════════════════════════╗"
echo "║  validate.sh — SSOT & Safety Check   ║"
echo "╚══════════════════════════════════════╝"
if [ -n "$IGNORE_GREP_FILE" ] && [ -s "$IGNORE_GREP_FILE" ]; then
    local_count=$(wc -l < "$IGNORE_GREP_FILE")
    echo "  (.validateignore: ${local_count} patterns excluded)"
fi
echo ""

if [ -z "$LAYER" ] || [ "$LAYER" = "1" ]; then
    run_layer "$VALIDATIONS_DIR/check_ssot.sh"
    echo ""
fi

if [ -z "$LAYER" ] || [ "$LAYER" = "2" ]; then
    run_layer "$VALIDATIONS_DIR/check_structure.sh"
    echo ""
fi

if [ -z "$LAYER" ] || [ "$LAYER" = "3" ]; then
    run_layer "$VALIDATIONS_DIR/check_safety.sh"
    echo ""
fi

if [ -z "$LAYER" ] || [ "$LAYER" = "4" ]; then
    run_layer "$VALIDATIONS_DIR/check_vault_current_state.sh"
    echo ""
fi

if [ -z "$LAYER" ] || [ "$LAYER" = "5" ]; then
    run_layer "$VALIDATIONS_DIR/check_nest_freshness.sh"
    echo ""
fi

if [ -z "$LAYER" ] || [ "$LAYER" = "6" ]; then
    run_layer "$VALIDATIONS_DIR/check_cable_model.sh"
    echo ""
fi

if [ -z "$LAYER" ] || [ "$LAYER" = "7" ]; then
    run_layer "$VALIDATIONS_DIR/check_planning_consistency.sh"
    echo ""
fi

# Summary
echo "═══════════════════════════════════════"
if [ "$TOTAL_FAIL" -gt 0 ]; then
    echo "RESULT: FAIL ($TOTAL_FAIL failures, $TOTAL_WARN warnings)"
    exit 1
elif [ "$TOTAL_WARN" -gt 0 ]; then
    echo "RESULT: PASS with $TOTAL_WARN warning(s)"
    exit 0
else
    echo "RESULT: ALL PASS"
    exit 0
fi
