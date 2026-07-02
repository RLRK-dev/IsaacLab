#!/usr/bin/env bash
# Layer 4: Vault current-state freshness checks
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AUDIT_SCRIPT="$REPO_ROOT/scripts/audit_thread_vault_current_state.py"
PY="$REPO_ROOT/env_isaaclab/bin/python"
VAULT_ROOT="$REPO_ROOT/thread_isaac_lab/thread-vault"

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

is_status_surface() {
    case "$1" in
        thread_isaac_lab/thread-vault/02-Workflow/HANDOFF.md) return 0 ;;
        thread_isaac_lab/thread-vault/04-Specs/SOMA.md) return 0 ;;
        thread_isaac_lab/thread-vault/log.md) return 0 ;;
        thread_isaac_lab/thread-vault/*/state.md) return 0 ;;
        thread_isaac_lab/thread-vault/*/*/state.md) return 0 ;;
        scripts/audit_thread_vault_current_state.py) return 0 ;;
        scripts/validations/check_vault_current_state.sh) return 0 ;;
        *) return 1 ;;
    esac
}

collect_staged_status_surfaces() {
    local tmp_changed="$1"
    local tmp_all
    local tmp_filtered
    tmp_all=$(mktemp)
    tmp_filtered=$(mktemp)

    git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR > "$tmp_all" || true
    if [ -n "$IGNORE_FILE" ] && [ -s "$IGNORE_FILE" ]; then
        grep -v -F -f "$IGNORE_FILE" "$tmp_all" > "$tmp_filtered" || true
    else
        cp "$tmp_all" "$tmp_filtered"
    fi

    while IFS= read -r rel; do
        if is_status_surface "$rel"; then
            printf '%s\n' "$REPO_ROOT/$rel"
        fi
    done < "$tmp_filtered" > "$tmp_changed"

    rm -f "$tmp_all" "$tmp_filtered"
}

collect_default_status_surfaces() {
    local tmp_files="$1"
    {
        printf '%s\n' "$VAULT_ROOT/02-Workflow/HANDOFF.md"
        printf '%s\n' "$VAULT_ROOT/04-Specs/SOMA.md"
        printf '%s\n' "$VAULT_ROOT/log.md"
    } > "$tmp_files"
}

check_vault_current_state() {
    echo "  [CHECK 9] Vault current-state freshness"

    if [ ! -f "$AUDIT_SCRIPT" ]; then
        echo "  [FAIL] Audit script missing: $AUDIT_SCRIPT"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return
    fi

    local tmp_files
    tmp_files=$(mktemp)
    if [ "$STAGED_ONLY" = "true" ]; then
        collect_staged_status_surfaces "$tmp_files"
        if [ ! -s "$tmp_files" ]; then
            echo "  [PASS] No staged Vault status surfaces"
            rm -f "$tmp_files"
            return
        fi
    else
        collect_default_status_surfaces "$tmp_files"
    fi

    local tmp_result
    tmp_result=$(mktemp)
    if ! "$PY" "$AUDIT_SCRIPT" --strict-log $(cat "$tmp_files") > "$tmp_result" 2>&1; then
        grep -a -v '^\[INFO\]' "$tmp_result" || true
        FAIL_COUNT=$((FAIL_COUNT + 1))
    else
        grep -a -v '^\[INFO\]' "$tmp_result" || true
        echo "  [PASS] Vault current-state surfaces are fresh"
    fi

    rm -f "$tmp_files" "$tmp_result"
}

echo "=== Layer 4: Vault Current-State Freshness ==="
check_vault_current_state

echo "LAYER4_FAIL=$FAIL_COUNT"
echo "LAYER4_WARN=$WARN_COUNT"
