#!/usr/bin/env bash
# Self-test for check_safety.sh CHECK 6 typed exceptions (OPS-SUP-CODEX co-decide condition 4,
# Rs ruling "A" 2026-07-16; I0B_BUILD_RSTECHLEAD_20260716.md sec CHECK-6).
#
# Sources check_safety.sh and pipes fixtures through the PRODUCTION cvd_ban_filter (same code path,
# not a copy). Positive AND negative controls are pinned:
#   ALLOWED : child-env dict assignment with "# cvd-child-env" annotation (no os.environ on the line)
#   ALLOWED : read-only os.environ.get(...) with "# cvd-provenance-read" annotation
#   ALLOWED : pure comment line (pre-existing rule, regression pin)
#   BANNED  : unannotated child-env-shaped assignment
#   BANNED  : direct os.environ[...] mutation even WITH the child-env annotation (spoof attempt)
#   BANNED  : direct os.environ[...] mutation even WITH the provenance annotation (spoof attempt)
#   BANNED  : assignment disguised alongside a .get() with the provenance annotation
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=check_safety.sh
source "$HERE/check_safety.sh"

run_case() {
    local desc="$1" line="$2" expect="$3"  # expect: ALLOWED (filtered out) | BANNED (survives)
    local survived
    survived=$(printf '%s\n' "$line" | cvd_ban_filter || true)
    local got
    if [ -n "$survived" ]; then got="BANNED"; else got="ALLOWED"; fi
    if [ "$got" = "$expect" ]; then
        echo "  [PASS] $desc -> $got"
    else
        echo "  [FAIL] $desc -> got $got, expected $expect"
        FAILURES=$((FAILURES + 1))
    fi
}

FAILURES=0
echo "=== CHECK 6 cvd_ban_filter self-test ==="
run_case "child-env assignment, annotated" \
    'x.py:10:    env["CUDA_VISIBLE_DEVICES"] = str(gpu_index)  # cvd-child-env: launcher pin' ALLOWED
run_case "provenance read, annotated" \
    'x.py:11:        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),  # cvd-provenance-read' ALLOWED
run_case "pure comment line" \
    'x.py:12:# CUDA_VISIBLE_DEVICES example in a comment' ALLOWED
run_case "child-env assignment, NOT annotated" \
    'x.py:13:    env["CUDA_VISIBLE_DEVICES"] = "0"' BANNED
run_case "os.environ direct mutation, child-env annotation spoof" \
    'x.py:14:    os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # cvd-child-env: spoof' BANNED
run_case "os.environ direct mutation, provenance annotation spoof" \
    'x.py:15:    os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # cvd-provenance-read' BANNED
run_case "mutation disguised beside a get(), provenance annotation" \
    'x.py:16:    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("CUDA_VISIBLE_DEVICES")  # cvd-provenance-read' BANNED
run_case "bare env-var read without annotation" \
    'x.py:17:    d = os.environ.get("CUDA_VISIBLE_DEVICES")' BANNED

if [ "$FAILURES" -eq 0 ]; then
    echo "SELF-TEST PASS (8/8 controls)"
    exit 0
else
    echo "SELF-TEST FAIL ($FAILURES failing controls)"
    exit 1
fi
