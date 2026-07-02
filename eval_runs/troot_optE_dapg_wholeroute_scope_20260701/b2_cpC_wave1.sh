#!/usr/bin/env bash
# CP-C WAVE-1: 4 concurrent DEMO recordings on GPU-0 (per parallel addendum cfa48d6951).
# MUST include #(+10,0). No --record-video (avoids ~/Downloads fixed-path collision; demo npz is the deliverable).
# Per-run: unique dir for DEMO_OUT + --output-dir; CUDA_VISIBLE_DEVICES=0; MUJOCO_GL=egl; unset DISPLAY.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/b2_cpC_wave1
rm -rf "$BASE"; mkdir -p "$BASE"
unset DISPLAY

run_one () {
  local tag="$1"; local off="$2"
  local OUT="$BASE/rec_$tag"; mkdir -p "$OUT"
  env S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
      SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075 \
      DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --output-dir "$OUT" \
      > "$OUT/run.log" 2>&1
  echo "DONE $tag (off=$off) exit=$?"
}

echo "=== CP-C WAVE-1 launch (4 concurrent, GPU-0) $(date '+%H:%M:%S') ==="
run_one "p10_0"    "0.010,0"       &
run_one "m20_0"    "-0.020,0"      &
run_one "p20_p20"  "0.020,0.020"   &
run_one "m20_m20"  "-0.020,-0.020" &
wait
echo "=== WAVE-1 ALL DONE $(date '+%H:%M:%S') ==="

echo "############ WAVE-1 PER-OFFSET RESULTS ############"
for tag in p10_0 m20_0 p20_p20 m20_m20; do
  OUT="$BASE/rec_$tag"
  echo "--- $tag ---"
  grep -E "caveat-a-X" "$OUT/run.log" 2>/dev/null | head -1 || echo "  (no caveat-a-X echo)"
  if [ -f "$OUT/route_c2_pin.json" ]; then
    "$PY" -c "import json;d=json.load(open('$OUT/route_c2_pin.json'));m=d.get('route_c2_metrics',{});print('  regrasp_ok=',m.get('c2_regrasp_ok'),'verdict=',m.get('c2_regrasp_verdict'),'c2_seated_honest=',m.get('c2_seated_honest'),'finite=',d.get('finite'),'qvel_ok=',d.get('qvel_ok'))"
  else
    echo "  route_c2_pin.json MISSING"; echo "  TAXONOMY:"; grep -E "Traceback|Error|IK NaN|GRASP.*MISS|R_MISS|BLOCKED|assert" "$OUT/run.log" 2>/dev/null | tail -3
  fi
  if [ -f "$OUT/route_demo_raw.npz" ]; then echo "  demo npz: PRESENT ($(du -h "$OUT/route_demo_raw.npz" | cut -f1))"; else echo "  demo npz: MISSING"; fi
done
echo "############ DONE WAVE-1 ############"
