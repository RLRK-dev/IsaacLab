#!/usr/bin/env bash
# CP-C WAVES 2-5: remaining 13 offsets, batched 4/GPU-0 (wait between batches).
# %12 wave-1 裁定: abort = NEW mechanism ONLY (Traceback|IK NaN|R_MISS_AT_88|missing route json);
# honest-seat fail = informative, CONTINUE. Same isolation as wave-1 (unique dir DEMO_OUT+output_dir,
# no --record-video, CUDA_VISIBLE_DEVICES=0, MUJOCO_GL=egl, unset DISPLAY).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/b2_cpC_waves2_5
rm -rf "$BASE"; mkdir -p "$BASE"
unset DISPLAY

# 13 remaining: front-load +X ride-up candidates (p20_0, p20_m20) for early hull info.
PAIRS=(
  "p20_0:0.020,0"        "p20_m20:0.020,-0.020"  "m20_p20:-0.020,0.020"  "z0_0:0,0"
  "z0_p20:0,0.020"       "z0_m20:0,-0.020"       "m10_0:-0.010,0"        "z0_p10:0,0.010"
  "z0_m10:0,-0.010"      "p8_p8:0.008,0.008"     "p8_m8:0.008,-0.008"    "m8_p8:-0.008,0.008"
  "m8_m8:-0.008,-0.008"
)

run_one () {
  local tag="$1"; local off="$2"; local OUT="$BASE/rec_$tag"; mkdir -p "$OUT"
  env S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
      SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075 \
      DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --output-dir "$OUT" \
      > "$OUT/run.log" 2>&1
  echo "DONE $tag (off=$off) exit=$?"
}

ABORT=0; i=0; N=${#PAIRS[@]}
while [ $i -lt $N ]; do
  echo "=== BATCH @i=$i  GPU-0 procs before: $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)  $(date '+%H:%M:%S') ==="
  batch=()
  for j in 0 1 2 3; do
    k=$((i+j)); [ $k -ge $N ] && break
    p="${PAIRS[$k]}"; tag="${p%%:*}"; off="${p#*:}"; batch+=("$tag"); run_one "$tag" "$off" &
  done
  wait
  for tag in "${batch[@]}"; do
    if grep -qE "Traceback|IK NaN|R_MISS_AT_88" "$BASE/rec_$tag/run.log" 2>/dev/null; then echo "!!! NEW-MECH ABORT: $tag !!!"; ABORT=1; fi
    [ -f "$BASE/rec_$tag/route_c2_pin.json" ] || { echo "!!! MISSING route json: $tag !!!"; ABORT=1; }
  done
  [ $ABORT -eq 1 ] && { echo "=== ABORT (new mechanism) — stopping remaining batches ==="; break; }
  i=$((i+4))
done
echo "=== WAVES 2-5 DONE (abort=$ABORT) $(date '+%H:%M:%S') ==="

echo "############ WAVES 2-5 PER-OFFSET ############"
for p in "${PAIRS[@]}"; do
  tag="${p%%:*}"; off="${p#*:}"; OUT="$BASE/rec_$tag"
  [ -d "$OUT" ] || { echo "--- $tag (off=$off): NOT RUN (aborted-before) ---"; continue; }
  echo "--- $tag (off=$off) ---"
  grep -E "caveat-a-X" "$OUT/run.log" 2>/dev/null | head -1 || echo "  (no caveat-a-X: dx=0 non-fire)"
  if [ -f "$OUT/route_c2_pin.json" ]; then
    "$PY" -c "import json;d=json.load(open('$OUT/route_c2_pin.json'));m=d.get('route_c2_metrics',{});print('  regrasp_ok=',m.get('c2_regrasp_ok'),'verdict=',m.get('c2_regrasp_verdict'),'c2_seated_honest=',m.get('c2_seated_honest'),'finite=',d.get('finite'),'qvel=',d.get('qvel_ok'))"
  else echo "  route_c2_pin.json MISSING"; grep -E "Traceback|IK NaN|R_MISS|BLOCKED" "$OUT/run.log" 2>/dev/null | tail -2; fi
  [ -f "$OUT/route_demo_raw.npz" ] && echo "  npz: PRESENT ($(du -h "$OUT/route_demo_raw.npz"|cut -f1))" || echo "  npz: MISSING"
done
echo "############ DONE ############"
