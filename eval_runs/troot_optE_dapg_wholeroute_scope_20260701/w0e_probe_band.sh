#!/usr/bin/env bash
# W0-e pre-build probe (spec v0.6 §0, step ①) — band_edge_sweep 拡張, existing runner, NO build/edit.
# ROUND 1 (done): P-1 dy=-2.5 (phase falsifier=PASS) / P-2 dy=13.5 (PASS) / P-3 dy=14.0 (PASS) -> UB<13.5 + B2 absolute-dy.
# ROUND 2 (this run, %12 (a)+(c)): P-4 dy=11.5 / P-5 dy=13.0 (B2 edges) / P-6 dy=-12.5 (|dy| mirror).
# canonical route env stack (= P3-grid / band_edge_sweep, confirmed resolved_clip [0.35,0.15]/[0.4,0.075]).
# band-fail readout (existing runner fields, pre-build): z_c1_final_mm >= 840 (C1 escape) OR c2_seated_honest == False.
# 0-commit into w0e_band_edge_sweep/. cuda:0 headless (no --record-video). render verdict = later; this = UB determination.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_band_edge_sweep
unset DISPLAY
RLOG="$BASE/_probe_summary.log"

ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075)

# tag dx_m dy_m  (dx=0 for all; phase = dy floor-mod 15)
# ROUND 2 (%12 (a)+(c) operand-split decision 17:11): pin B2 absolute-dy edges + negative mirror.
CELLS=(
  "cell_dx0_y11p5  0.0  0.0115"   # P-4: B2 lower edge (trigger 11.5)
  "cell_dx0_y13    0.0  0.0130"   # P-5: B2 upper edge pin (between dy12.5 FAIL / dy13.5 PASS)
  "cell_dx0_y-12p5 0.0 -0.0125"   # P-6: negative mirror (|dy| symmetry: FAIL=symmetric trigger / PASS=one-sided)
)

run_one () {  # tag dx dy
  local tag="$1" dxm="$2" dym="$3"
  local OUT="$BASE/$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$dxm,$dym" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      --output-dir "$OUT" > "$OUT/run.log" 2>&1
  local rc=$?
  echo "DONE $tag exit=$rc" | tee -a "$RLOG"
}

echo "=== W0E-PROBE START $(date '+%F %T') : P-1/P-2/P-3, 3-way, cuda:0 ===" | tee -a "$RLOG"
pids=()
for spec in "${CELLS[@]}"; do
  read -r tag dxm dym <<< "$spec"
  run_one "$tag" "$dxm" "$dym" &
  pids+=($!)
done
wait "${pids[@]}"
echo "=== W0E-PROBE DONE $(date '+%F %T') ===" | tee -a "$RLOG"
