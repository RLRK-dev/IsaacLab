#!/usr/bin/env bash
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Layer 8: Control-Method Guard — RS71 SSOT §0#3 "DiffIK-only" + §0#5 "no kinematic trick".
#
# WHAT IT ENFORCES (plain language):
#   The robot ARM must be moved by physics actuators (MuJoCo `ctrl` / PD position actuators),
#   never by writing joint state directly. Forcing joint positions (or velocities) bypasses
#   physics = a kinematic "forced placement", which RS71 §0#3/#5 forbid on EVERY substrate.
#   There are NO authorized exceptions (Rs directive 2026-07-19: the former clip-retention pin
#   exception is superseded; pins/welds/attachments/direct state drives are all prohibited).
#
# HOW IT DECIDES (two layers -- both must pass):
#   [CHECK 10] SUBSCRIPT layer: any line assigning into a canonical joint-state array name
#     (phys_jq / phys_jqd / joint_q / joint_qd / qpos / qvel). Fast first line of defense.
#     KNOWN LIMIT (proven 2026-07-19): a host-side alias (e.g. `_rep_jq = state.joint_q.numpy()`
#     then `_rep_jq[idx] = x`) escapes this pattern -- host mutations are INERT until delivered.
#   [CHECK 11] DELIVERY layer (airtight): a host mutation only reaches the sim through
#     `<state>.joint_q.assign(...)` / `<state>.joint_qd.assign(...)`. ALL such calls are
#     forbidden in envs/, except (a) FK scratch buffers (receiver contains `fk_state` -- an FK
#     evaluation state, never the stepped sim state) and (b) lines carrying the explicit marker
#     `# CABLE-SEED (design sec14.2 step-3 scope-out` (cable reset-init, Rs-acknowledged
#     deferred surface -- counted and echoed LOUDLY, never silent).
#   [CHECK 12] RAW-MUJOCO layer (defense): subscript writes to `.qpos` / `.qvel` of an mj/mjw
#     data object in envs/ (CPU-side mj writes are GPU-inert in multi-world but are still a
#     forced-placement attempt).
#   Historical allowlists/baselines are forbidden: every unmarked hit FAILs.
#
# Refs: RS71-System-Spec-SSOT.md §0#3/#5 ; .claude/rules/prohibited.md ;
#       ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md §14 (complete removal).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENVS_DIR="$REPO_ROOT/thread_isaac_lab/envs"
if [ ! -d "$ENVS_DIR" ] || ! find "$ENVS_DIR" -maxdepth 1 -type f -name '*.py' -print -quit | grep -q .; then
    echo "  [FAIL] canonical env scan root missing or empty: $ENVS_DIR"
    echo "LAYER8_FAIL=1"
    echo "LAYER8_WARN=0"
    exit 1
fi

FAIL_COUNT=0
WARN_COUNT=0
fail_lines=""

add_fails() {
    # $1 = hits (grep path:line:code, possibly empty)
    [ -z "$1" ] && return 0
    while IFS= read -r hit; do
        [ -z "$hit" ] && continue
        loc=$(printf '%s\n' "$hit" | sed -E "s#^$ENVS_DIR/##")
        FAIL_COUNT=$((FAIL_COUNT + 1))
        fail_lines="${fail_lines}         ${loc}"$'\n'
    done <<< "$1"
}

echo "=== Layer 8: Control-Method Guard (§0 DiffIK-only / no-kinematic-trick; NO exceptions) ==="

echo "  [CHECK 10] subscript writes into canonical joint-state arrays (q AND qd)"
HITS10=$(grep -rnE '(phys_jq|phys_jqd|joint_q|joint_qd|qpos|qvel)\[[^=]*\][[:space:]]*=[^=]' "$ENVS_DIR" --include='*.py' 2>/dev/null \
    | grep -vE ':[0-9]+:[[:space:]]*#' \
    || true)
add_fails "$HITS10"

echo "  [CHECK 11] joint-state .assign delivery surface (fk_state scratch exempt; CABLE-SEED marker = loud scope-out)"
HITS11_ALL=$(grep -rnE '\.(joint_q|joint_qd)\.assign\(' "$ENVS_DIR" --include='*.py' 2>/dev/null \
    | grep -vE ':[0-9]+:[[:space:]]*#' \
    | grep -v 'fk_state' \
    || true)
HITS11_MARKED=$(printf '%s\n' "$HITS11_ALL" | grep -F '# CABLE-SEED (design sec14.2 step-3 scope-out' || true)
HITS11=$(printf '%s\n' "$HITS11_ALL" | grep -vF '# CABLE-SEED (design sec14.2 step-3 scope-out' | grep -v '^$' || true)
add_fails "$HITS11"
MARKED_COUNT=0
if [ -n "$HITS11_MARKED" ]; then
    MARKED_COUNT=$(printf '%s\n' "$HITS11_MARKED" | grep -c . || true)
    echo "  [SCOPE-OUT] $MARKED_COUNT CABLE-SEED-marked joint-state assign(s) (cable reset-init, design sec14.2 step-3 -- deferred surface, NOT arm):"
    printf '%s\n' "$HITS11_MARKED" | sed -E "s#^$ENVS_DIR/#         #"
fi

echo "  [CHECK 12] raw mujoco qpos/qvel subscript writes (mj/mjw data objects)"
HITS12=$(grep -rnE '\.(qpos|qvel)\[[^=]*\][[:space:]]*=[^=]' "$ENVS_DIR" --include='*.py' 2>/dev/null \
    | grep -vE ':[0-9]+:[[:space:]]*#' \
    || true)
add_fails "$HITS12"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "  [FAIL] $FAIL_COUNT kinematic joint-state write path(s) = §0#3/#5 violation (arm must be actuator/ctrl-driven):"
    printf '%s' "$fail_lines"
    echo "         Fix: drive the arm via MuJoCo actuators (POSITION-servo ctrl target), NOT a joint-state write."
    echo "         No baseline, pin, or reset-init exception is permitted (Rs 2026-07-19)."
else
    echo "  [PASS] no kinematic joint-state write path in envs/ (CHECK 10/11/12 all clean)"
fi

echo "LAYER8_FAIL=$FAIL_COUNT"
echo "LAYER8_WARN=$WARN_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
