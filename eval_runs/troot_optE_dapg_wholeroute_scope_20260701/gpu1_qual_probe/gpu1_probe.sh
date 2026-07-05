#!/usr/bin/env bash
# GPU1 (RTX PRO 4000 Blackwell, nvidia-smi index 1) determinism-qualification probe.
# Purpose: Rs directive 2026-07-05 14:0x "GPU1が活用されていない" -> qualify cuda:1 for
# scale-out of determinism-anchored canonical-route runs (grid ran on A6000 = index 0).
# Method: re-run 3 known P3-grid cells (one per class: strict / seat_miss / FAIL) with the
# VERBATIM grid env stack (p3_grid_runner.sh:18-27), changing ONLY CUDA_VISIBLE_DEVICES=1
# (runtime device = cuda:0 under mask, same masking pattern as the 2026-05-16 chain-context
# pilot). Compare (verdict, c2_seated_honest, cable_z_at_c2_mm, c2_wall_dist) vs grid JSON.
# EXACT 3/3 -> cuda:1 qualified for future wave-splitting; any drift -> GPU1 = independent
# workloads only (device-fragility fact extended, memory project-canonical-route-device-fragile).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/gpu1_qual_probe

ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075)

run_one () {  # tag dx_m dy_m
  local tag="$1" dxm="$2" dym="$3"
  local OUT="$BASE/cell_$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$dxm,$dym" \
      CUDA_VISIBLE_DEVICES=1 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --output-dir "$OUT" \
      > "$OUT/run.log" 2>&1
  echo "DONE $tag exit=$?" | tee -a "$BASE/probe.log"
}

echo "=== GPU1 QUAL PROBE start $(date '+%F %T') ===" | tee -a "$BASE/probe.log"
run_one x0_y0    0.000  0.000   &
run_one x0_y-20  0.000  -0.020  &
run_one x-20_y5  -0.020 0.005   &
wait
echo "=== GPU1 QUAL PROBE all done $(date '+%F %T') ===" | tee -a "$BASE/probe.log"
