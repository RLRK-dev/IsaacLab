#!/usr/bin/env bash
# Option E — S2 §5.6 classification-aware mechanical audit (A3 regression guard).
# Materializes the design's "executor HARD GATE" as a committable, reusable artifact
# (closes %3 PV discrepancy D1). 0-GPU, read-only grep.
#
# CLAIM SCOPE (D2): this audit is the LIVE RL-env path (base + 6 skill envs). Off-live-path
# scripts/utils (demo-gen, routing_utils dup) intentionally retain Franka patterns and are a
# RECORDED deferred obligation (D3/D4), proven off-live by import-graph (no env imports them).
#
# PASS criteria:
#   (1) ZERO old Franka finger patterns across the live envs (every finger site was remapped
#       to the correct index SPACE -> no A3 mis-map / no missed site), AND
#   (2) the new SSOT space constants are PRESENT (the remap actually landed).
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 3   # repo root
ENVS=(
  thread_isaac_lab/envs/newton_skill_env_base.py
  thread_isaac_lab/envs/newton_approach_cable_env.py
  thread_isaac_lab/envs/newton_insert_clip_env.py
  thread_isaac_lab/envs/newton_unclamp_env.py
  thread_isaac_lab/envs/newton_grip_env.py
  thread_isaac_lab/envs/newton_clamp_env.py
  thread_isaac_lab/envs/newton_aerial_regrasp_env.py
)
fail=0

echo "=== S2 §5.6 AUDIT — A3 regression guard (LIVE RL-env path) ==="
echo "files: ${#ENVS[@]} (base + 6 skill envs)"
echo

# ---- (1) OLD Franka finger patterns: MUST be ZERO ----
declare -A OLD=(
  [P1_finger_joint_stride]='FRANKA_NUM_JOINTS[[:space:]]*\+[[:space:]]*[78]\b'
  [P2_exclusion_tuple]='\(7,[[:space:]]*8,[[:space:]]*FRANKA_NUM_JOINTS'
  [P3_renamed_local]='\bLEFT_FINGER_LOCAL\b'
  [P4a_filter_threshold]='local[[:space:]]*<[[:space:]]*7\b'
  [P4b_filter_membership]='local[[:space:]]+in[[:space:]]*\(7,[[:space:]]*8'
  [P4c_filter_lr]='local_[lr][[:space:]]+in[[:space:]]*\(7'
  [P5_finger_idx_literal]='(fk_jq|jq_solved|jq_target|jq_targets|jq_starts)\[[^]]*\b[78]\]'
)
echo "--- (1) OLD Franka finger patterns (expect 0 each) ---"
for name in $(printf '%s\n' "${!OLD[@]}" | sort); do
  hits=$(grep -rnE "${OLD[$name]}" "${ENVS[@]}" 2>/dev/null)
  n=$(printf '%s' "$hits" | grep -c . )
  printf "  %-26s %s\n" "$name" "$n"
  if [ "$n" -ne 0 ]; then
    fail=1
    printf '%s\n' "$hits" | sed 's/^/      HIT: /'
  fi
done

# ---- (2) NEW SSOT space constants: MUST be PRESENT (remap landed) ----
declare -A NEW=(
  [GRIPPER_DRIVER_JOINT_IDX]='\bGRIPPER_DRIVER_JOINT_IDX\b'
  [GRIPPER_JOINT_RANGE]='\bGRIPPER_JOINT_RANGE\b'
  [GRIPPER_PAD_BODY_IDX]='\bGRIPPER_PAD_BODY_IDX\b'
  [FINGER_LOCAL]='\bFINGER_LOCAL\b'
)
echo "--- (2) NEW SSOT space constants (expect > 0 each) ---"
for name in $(printf '%s\n' "${!NEW[@]}" | sort); do
  n=$(grep -rnE "${NEW[$name]}" "${ENVS[@]}" 2>/dev/null | grep -c .)
  printf "  %-26s %s\n" "$name" "$n"
  if [ "$n" -eq 0 ]; then fail=1; echo "      MISSING (remap did not land)"; fi
done

# ---- (3) FINGER_JOINT_INDICES (base) MUST be the dual-arm RANGE form, not (7,8,FN+7,FN+8) ----
echo "--- (3) FINGER_JOINT_INDICES = dual-arm RANGE form ---"
fji=$(grep -nE 'FINGER_JOINT_INDICES[[:space:]]*=' thread_isaac_lab/envs/newton_skill_env_base.py 2>/dev/null)
echo "  def: ${fji:-<none>}"
if printf '%s' "$fji" | grep -qE 'GRIPPER_JOINT_RANGE'; then
  echo "  -> RANGE-based (correct)"
else
  echo "  -> NOT range-based (A3 risk)"; fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "S2B_5_6_AUDIT=PASS  (live-env A3-guard clean; remap landed; FINGER_JOINT_INDICES=RANGE)"
else
  echo "S2B_5_6_AUDIT=FAIL"
fi
echo "S2B_5_6_AUDIT_DONE"
exit $fail
