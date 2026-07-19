#!/usr/bin/env bash
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Layer 8: Control-Method Guard — thin STRICT wrapper for the v3 AST checker.
#
# v3 (2026-07-19): the actual analysis lives in check_control_method.py (AST receiver analysis,
# alias tracking, body/eq/wp-copy coverage, pinned CABLE-SEED carry manifest, and a built-in
# negative-control self-test that must pass before anything is certified). This wrapper only
# resolves an interpreter and PROPAGATES the checker's exit code -- no || true, no fallback
# grep, no baseline (a wrapper that softens the rc re-opens the fail-open hole pN flagged as B4).
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PY=""
for cand in /home/rlrk/env_isaaclab7/bin/python python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "  [FAIL] no python interpreter found for the Layer 8 AST checker (fail-closed)"
    echo "LAYER8_FAIL=1"
    echo "LAYER8_WARN=0"
    exit 1
fi

exec "$PY" "$DIR/check_control_method.py"
