#!/usr/bin/env bash
# P3 render (W0-d J6) — re-run the 7 z-strata cells with --record-video (built-in mujoco.Renderer EGL, §運用14 banked
# path in _run_mujoco_grasp_route:3775). DETERMINISTIC device-matched re-run (render passive = physics byte-identical,
# memory reference-mujoco-headless-egl-video) -> reproduces the exact grid trajectory + verdict, + renders it.
# NOT npz-replay (arm_q = warp joint_q != mujoco qpos). Render-only; seat verdict = %12+%9 (NOT this script).
# Output per cell: render_<tag>/route_c1_to_c2.mp4 + _route_frames/f*.png (4-cam montage: overhead C1+C2 / front / zoom-Lclaw / oblique).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p3_grid
unset DISPLAY   # EGL headless (BadWindow avoid, memory 2026-07-02)
RLOG="$BASE/_render_summary.log"

# VERBATIM canonical route env-gate stack (same as grid = reproduces the verified trajectory).
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075)

# 7 z-strata render cells (tag dx_m dy_m) — %12 confirmed list 13:38 (z_gap label in comment).
CELLS=(
  "x0_y10   0.000  0.010"   # (1) STRICT floor ref     z_gap 0.3
  "x5_y20   0.005  0.020"   # (2) STRICT borderline    z_gap 3.0
  "x15_y5   0.015  0.005"   # (3) seat_miss typical    z_gap 4.1
  "x0_y-20  0.000 -0.020"   # (4) seat_miss under-seat z_gap 15.2 (CP-C repro)
  "x-15_y15 -0.015 0.015"   # (5) seat_miss perched    z_gap 43.2
  "x-20_y-15 -0.020 -0.015" # (6) seat_miss extreme    z_gap 56.2 wall-2.4 (body-swap crux)
  "x-20_y5  -0.020  0.005"  # (7) FAIL whiff           z_gap 5.7
)

run_one () {  # tag dx_m dy_m
  local tag="$1" dxm="$2" dym="$3"
  local OUT="$BASE/render_$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$dxm,$dym" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      --output-dir "$OUT" --record-video \
      > "$OUT/render.log" 2>&1
  local rc=$?
  local mp4="none"; [ -f "$OUT/route_c1_to_c2.mp4" ] && mp4="route_c1_to_c2.mp4"
  local nf; nf=$(ls "$OUT/_route_frames/"*.png 2>/dev/null | wc -l)
  echo "DONE $tag exit=$rc mp4=$mp4 frames=$nf" | tee -a "$RLOG"
}

NW=${NW:-3}   # 3-way (render heavier than headless: EGL + matplotlib per proc)
ONLY="${ONLY:-}"   # ONLY=x-20_y5 to render a single test cell first (§運用17 step-gate)
echo "=== P3-RENDER START $(date '+%F %T') : ${ONLY:-all 7} cells, ${NW}-way, cuda:0 EGL ===" | tee -a "$RLOG"
i=0; pids=()
for spec in "${CELLS[@]}"; do
  read -r tag dxm dym <<< "$spec"
  [ -n "$ONLY" ] && [ "$tag" != "$ONLY" ] && continue
  [ -z "$ONLY" ] && [ -f "$BASE/render_$tag/route_c1_to_c2.mp4" ] && { echo "SKIP $tag (mp4 exists)" | tee -a "$RLOG"; continue; }
  run_one "$tag" "$dxm" "$dym" &
  pids+=($!); i=$((i+1))
  if (( i % NW == 0 )); then wait "${pids[@]}"; pids=(); fi
done
[ ${#pids[@]} -gt 0 ] && wait "${pids[@]}"
echo "=== P3-RENDER DONE $(date '+%F %T') ===" | tee -a "$RLOG"
