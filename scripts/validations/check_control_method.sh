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
#   never by writing the joint-position array directly. A line that assigns INTO a physics
#   joint-position array (`phys_jq` / `joint_q` / `qpos`) forces the pose with no physics =
#   a kinematic "forced placement", which RS71 §0#3 and §0#5 forbid on EVERY substrate
#   (PhysX AND Newton) — the invariant is substrate-agnostic, NOT a PhysX-only rule.
#   The ONE authorized kinematic exception is the clip-retention pin, which writes body_q /
#   an eq constraint (NOT a joint-position array), so it is not matched here.
#
# WHY THERE ARE KNOWN HITS:
#   The old VBD solver could not simulate the arm's revolute joints, so every Newton skill-env
#   drives the arm by writing joint_q directly (FK "forced placement") as a workaround
#   (LL-Newton.md:670). The current substrate is MuJoCo, which DOES support PD position
#   actuators (ur5e.xml arm actuators), so all of these sites must migrate to actuator control.
#   Until that remediation lands they are listed in BASELINE below and reported as WARN
#   (visible + tracked, non-blocking).
#
# HOW IT DECIDES:
#   Every direct write to a physics joint-position array in thread_isaac_lab/envs/*.py is
#   detected (the greedy index match also catches nested-bracket and slice indices). A hit whose
#   comment-stripped, whitespace-normalized code matches a BASELINE signature = KNOWN carryover
#   -> WARN. Any OTHER direct write = NEW kinematic forced-placement -> FAIL. When a site migrates
#   to actuator control, DELETE its BASELINE entry so any re-introduction FAILs (regression guard).
#
# Refs: thread-vault/04-Specs/RS71-System-Spec-SSOT.md §0#3/#5 ; .claude/rules/prohibited.md.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# ENVS_DIR is overridable (CHECK_CM_ENVS_DIR) so the FAIL path can be exercised against a fixture.
ENVS_DIR="${CHECK_CM_ENVS_DIR:-$REPO_ROOT/thread_isaac_lab/envs}"

# --- BASELINE: known VBD-era kinematic-arm-drive writes (comment-stripped, ALL whitespace removed).
# 16 sites across 5 env files (newton_aerial_regrasp / newton_approach_cable / newton_route_env /
# newton_skill_env_base / route_executor) collapse to these 12 unique signatures. 15 are ARM writes;
# the gripper-restore one is included as the same class (a direct joint-position write).
# ⚠ DELETE an entry when its site migrates to MuJoCo actuator control (so a regression re-FAILs).
BASELINE='
phys_jq[self._arm_ow_q_idx]=fk_jq[self._arm_ow_src]
phys_jq[self._arm_ow_q_idx]=jq_interp[:,_ARM_OVERWRITE_LOCAL].reshape(-1)
phys_jq[jq0:jq0+_N_ARM_JOINTS]=self._settled_fk_jq[:_N_ARM_JOINTS]
phys_jq[jq0:jq0+_N_ARM_JOINTS]=jq_interp[w,:_N_ARM_JOINTS]
phys_jq[self._arm_q_start[w]:self._arm_q_start[w]+n]=fk_jq
phys_jq[start:start+n]=fk_jq
phys_jq[arm_ow_q_idx]=fk_jq_1world[arm_ow_src]
phys_jq[arm_ow_q_idx]=jq_interp[:,_ARM_OVERWRITE_LOCAL].reshape(-1)
phys_jq[maps["arm_ow_q_idx"]]=banked["arm_q"]
phys_jq[maps["gripper_restore_q_idx"]]=banked["gripper_q"]
phys_jq[_ARM_OVERWRITE_LOCAL]=fk_state.joint_q.numpy()[_ARM_OVERWRITE_LOCAL]
phys_jq[:n]=fk_state.joint_q.numpy()[:n]
'

FAIL_COUNT=0
WARN_COUNT=0
warn_lines=""
fail_lines=""

echo "=== Layer 8: Control-Method Guard (§0 DiffIK-only / no-kinematic-trick) ==="
echo "  [CHECK 10] direct physics joint-position write (kinematic 'forced placement') — arm must be actuator-driven"

# All direct writes to a physics joint-position array. Greedy [^=]* runs up to the assignment '='
# then backtracks to the last ']', so nested-bracket (maps["arm..."]) and slice ([jq0:jq0+N]) indices
# are all caught. '=[^=]' excludes '=='/'>='/'<=' comparisons.
HITS=$(grep -rnE '(phys_jq|joint_q|qpos)\[[^=]*\][[:space:]]*=[^=]' "$ENVS_DIR" --include='*.py' 2>/dev/null \
    | grep -vE ':[0-9]+:[[:space:]]*#' \
    || true)

# Normalize a grep hit ("path:line:code") to its signature: drop the prefix, strip an inline comment,
# remove all whitespace.
sig_of() {
    printf '%s\n' "$1" | sed -E 's/^[^:]+:[0-9]+://; s/[[:space:]]*#.*$//; s/[[:space:]]+//g'
}

if [ -n "$HITS" ]; then
    while IFS= read -r hit; do
        [ -z "$hit" ] && continue
        sig=$(sig_of "$hit")
        [ -z "$sig" ] && continue
        loc=$(printf '%s\n' "$hit" | sed -E "s#^$ENVS_DIR/##")
        if printf '%s\n' "$BASELINE" | grep -qxF "$sig"; then
            WARN_COUNT=$((WARN_COUNT + 1))
            warn_lines="${warn_lines}         ${loc}"$'\n'
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            fail_lines="${fail_lines}         ${loc}"$'\n'
        fi
    done <<< "$HITS"
fi

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "  [FAIL] $FAIL_COUNT NEW direct joint-position write(s) = §0#5 kinematic-trick violation (arm must be actuator/ctrl-driven):"
    printf '%s' "$fail_lines"
    echo "         Fix: drive the arm via MuJoCo actuators (set ctrl / PD position target), NOT a joint_q write."
    echo "         (If this is a legitimate reset-init or the pin exception, add its normalized signature to BASELINE with a note.)"
fi
if [ "$WARN_COUNT" -gt 0 ]; then
    echo "  [WARN] $WARN_COUNT KNOWN kinematic-arm-drive site(s) — VBD-era carryover, PENDING migration to MuJoCo actuators (§0 remediation):"
    printf '%s' "$warn_lines"
fi
if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
    echo "  [PASS] no direct joint-position write in envs/"
fi

echo "LAYER8_FAIL=$FAIL_COUNT"
echo "LAYER8_WARN=$WARN_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
