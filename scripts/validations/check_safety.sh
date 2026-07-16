#!/usr/bin/env bash
# Layer 3: Safety Guards
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

# ─── Check 6: CUDA_VISIBLE_DEVICES usage ban ───
# Typed exact-shape exceptions (Rs ruling "A" 2026-07-16 + OPS-SUP-CODEX co-decide conditions, tightened
# per the I0-b HOLD B1 controls; I0B_BUILD_RSTECHLEAD_20260716.md sec CHECK-6). The ban targets scripts
# grabbing a GPU for THEMSELVES instead of exposing --device. Two narrow allowances, each requiring the
# exact code shape AND an explicit annotation AND no compound statement (';' anywhere disqualifies):
#   1. "# cvd-child-env"       : the target must be literally `env["CUDA_VISIBLE_DEVICES"]` and the value
#                                str(<identifier>) or a quoted digit string -- the launcher shape pinning a
#                                CHILD's GPU (CLAUDE.md GPU rules / fork-B R1-3). Any os.environ on the
#                                line stays banned, annotated or not; cfg[...]/other targets stay banned.
#   2. "# cvd-provenance-read" : read-only os.environ.get("CUDA_VISIBLE_DEVICES") as a dict entry or a
#                                simple assignment. Any os.environ[...] subscript or any os.environ method
#                                other than .get on the line stays banned (update()/setdefault()/pop()...).
# Known residual (declared): a line-level grep cannot see dataflow (e.g. `env = os.environ` aliasing two
# lines apart) -- this check is a tripwire, review remains the backstop.
# The filter is a named function so the self-test (test_check_safety_cvd.sh) exercises the SAME code path.
cvd_ban_filter() {
    # stdin: "file:line:content" grep hits -> stdout: lines that VIOLATE the ban
    grep -vP ':\d+:\s*#' \
        | grep -vP '# .*(ban|don'\''t|deprecated|Do NOT use|禁止)' \
        | grep -vP '^(?!.*;)(?!.*os\.environ).*:\d+:\s*env\["CUDA_VISIBLE_DEVICES"\]\s*=\s*(str\([A-Za-z_][A-Za-z0-9_]*\)|"[0-9,]+")\s*#\s*cvd-child-env\b' \
        | grep -vP '^(?!.*;)(?!.*os\.environ\[)(?!.*os\.environ\.(?!get\())[^;]*:\d+:\s*("CUDA_VISIBLE_DEVICES":\s*|[A-Za-z_][A-Za-z0-9_]*\s*=\s*)os\.environ\.get\("CUDA_VISIBLE_DEVICES"\),?\s*#\s*cvd-provenance-read\b'
}

check_cuda_visible_devices() {
    echo "  [CHECK 6] CUDA_VISIBLE_DEVICES usage"

    local tmpfiles
    tmpfiles=$(mktemp)
    if [ "$STAGED_ONLY" = "true" ]; then
        git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR -- "$THREAD_DIR" \
            | grep -E '\.(py|sh)$' | grep -v '\.bak' \
            | while read -r f; do echo "$REPO_ROOT/$f"; done | apply_ignore > "$tmpfiles"
    else
        { find "$THREAD_DIR" -name "*.py" -not -name "*.bak*" -not -path "*/.git/*" 2>/dev/null
          find "$THREAD_DIR" -name "*.sh" -not -name "*.bak*" -not -path "*/.git/*" 2>/dev/null
        } | apply_ignore > "$tmpfiles"
    fi

    if [ ! -s "$tmpfiles" ]; then
        echo "  [PASS] No files to check"
        rm -f "$tmpfiles"
        return
    fi

    local tmpresults
    tmpresults=$(mktemp)
    xargs grep -nH "CUDA_VISIBLE_DEVICES" < "$tmpfiles" 2>/dev/null | cvd_ban_filter > "$tmpresults" || true

    if [ ! -s "$tmpresults" ]; then
        echo "  [PASS] No CUDA_VISIBLE_DEVICES usage"
    else
        while IFS= read -r line; do
            local short
            short=$(echo "$line" | head -c 120)
            echo "  [FAIL] CUDA_VISIBLE_DEVICES used: $short"
            echo "         Use --device cuda:N instead (see CLAUDE.md)"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        done < "$tmpresults"
    fi

    rm -f "$tmpfiles" "$tmpresults"
}

# ─── Check 7: Direct subprocess/os.system shell execution ───
check_direct_bash_execution() {
    echo "  [CHECK 7] Direct shell execution in Python"

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
    xargs grep -nH -E 'subprocess\.(run|Popen|call)|os\.system' < "$tmpfiles" 2>/dev/null \
        | grep -v "^\s*#" > "$tmpresults" || true

    if [ ! -s "$tmpresults" ]; then
        echo "  [PASS] No direct shell execution detected"
    else
        while IFS= read -r line; do
            local short
            short=$(echo "$line" | head -c 120)
            echo "  [WARN] Direct shell execution: $short"
            WARN_COUNT=$((WARN_COUNT + 1))
        done < "$tmpresults"
    fi

    rm -f "$tmpfiles" "$tmpresults"
}

# ─── Check 8: Video file size exceeding limit ───
check_video_size() {
    echo "  [CHECK 8] Video file size (>${MAX_VIDEO_MB:-30}MB)"

    local max_mb="${MAX_VIDEO_MB:-30}"
    local data_dir="$REPO_ROOT/data"

    if [ ! -d "$data_dir" ]; then
        echo "  [PASS] No data directory"
        return
    fi

    local tmpresults
    tmpresults=$(mktemp)

    find "$data_dir" \( -path "*/test_*/*.mp4" -o -path "*/demos_*/*.mp4" -o -path "*/training_results*/*.mp4" \) \
        -size "+${max_mb}M" 2>/dev/null > "$tmpresults" || true

    if [ ! -s "$tmpresults" ]; then
        echo "  [PASS] No oversized videos"
    else
        while IFS= read -r filepath; do
            local size_mb
            size_mb=$(awk "BEGIN {printf \"%.0f\", $(stat -c%s "$filepath") / 1048576}")
            echo "  [WARN] Video exceeds ${max_mb}MB: $filepath (${size_mb}MB). Run: scripts/compress_video.sh $filepath"
            echo "         Add --split if compression alone is insufficient"
            WARN_COUNT=$((WARN_COUNT + 1))
        done < "$tmpresults"
    fi

    rm -f "$tmpresults"
}

# ─── Run (skipped when sourced by the self-test, which needs the functions only) ───
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    echo "=== Layer 3: Safety Guards ==="
    check_cuda_visible_devices
    check_direct_bash_execution
    check_video_size

    echo "LAYER3_FAIL=$FAIL_COUNT"
    echo "LAYER3_WARN=$WARN_COUNT"
fi
