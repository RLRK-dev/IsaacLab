#!/usr/bin/env bash
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Layer 6: Cable-Model Label Guard
# The installed Newton sim cable is a rigid-capsule CABLE-joint chain (rigid-link REVOLUTE on
# SolverMuJoCo, since MuJoCo rejects CABLE joints), NOT a Cosserat rod (human-Rs correction,
# thread-vault/log.md:6042; rigid-link != Cosserat, log.md:6149). This layer fails if the
# "Cosserat Rod" LABEL reappears in the sim-cable definition locations (configs/, envs/). It
# delegates to scripts/check_cable_model_mislabel.sh (single source of the detection logic +
# its built-in --selftest true positive); the vision estimators/ Cosserat usage is legitimate
# and is deliberately not scanned.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GUARD="$REPO_ROOT/scripts/check_cable_model_mislabel.sh"
THREAD_DIR="$REPO_ROOT/thread_isaac_lab"

STAGED_ONLY="${1:-false}"   # unused: this invariant scans the full sim-cable definition set (configs+envs)
IGNORE_FILE="${2:-}"        # unused: the guard carries its own exclusions (estimators/ + backups + NOT-Cosserat)
FAIL_COUNT=0
WARN_COUNT=0

echo "=== Layer 6: Cable-Model Label Guard ==="
echo "  [CHECK 9] sim-cable 'Cosserat Rod' mislabel (cable = rigid-capsule CABLE-joint chain; log.md:6042)"

if [ ! -x "$GUARD" ]; then
    echo "  [FAIL] guard missing or not executable: $GUARD"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    # fail-closed: capture rc explicitly (rc=1 mislabel found, rc=2 guard-error -> both FAIL)
    GUARD_OUT="$("$GUARD" "$THREAD_DIR" 2>&1)" && GUARD_RC=0 || GUARD_RC=$?
    if [ "${GUARD_RC:-1}" -eq 0 ]; then
        echo "  [PASS] no sim-cable Cosserat-Rod mislabel (estimators/ legit usage preserved)"
    else
        echo "$GUARD_OUT" | sed 's/^/         /'
        echo "  [FAIL] cable-model mislabel guard returned rc=$GUARD_RC (1=mislabel, 2=guard-error/fail-closed)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
fi

echo "LAYER6_FAIL=$FAIL_COUNT"
echo "LAYER6_WARN=$WARN_COUNT"
