#!/usr/bin/env bash
# P3-GRID (W0-d) — script-only DR grid over the canonical C1->C2 route (NOT a policy rollout = rollout-HALT non-抵触).
# Pre-reg: eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P3_GRID_PREREG_20260705.md (counting/draw/derivations/abort PINNED).
# Per-cell command = the PROVEN b2_cpC_wave1.sh invocation VERBATIM (canonical route env-gate stack + DEMO_RECORD npz +
#   CABLE_XY_OFFSET[m]), expanded from CP-C's 17 offsets to the pre-reg's 81-cell grid, 4-way GPU-0 waves.
# 0-commit (result dir only). cuda:0 + MUJOCO_GL=egl + headless (device-fragile pin + BadWindow avoid). No --record-video.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p3_grid
mkdir -p "$BASE"
unset DISPLAY
SUMLOG="$BASE/_wave_summary.log"
START_WAVE=${START_WAVE:-1}; END_WAVE=${END_WAVE:-21}   # resumable by wave range (wave-1 sanity gate then rest)
[ "$START_WAVE" = "1" ] && : > "$SUMLOG"

# Canonical route env-gate stack — VERBATIM from b2_cpC_wave1.sh (committed square-on C1->C2 route bcb7393ec8).
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075)

run_one () {  # tag dx_m dy_m
  local tag="$1" dxm="$2" dym="$3"
  local OUT="$BASE/cell_$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$dxm,$dym" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --output-dir "$OUT" \
      > "$OUT/run.log" 2>&1
  echo "DONE $tag (off=$dxm,$dym) exit=$?"
}

# route_c2_pin.json parse -> one line: "<tag> verdict=<..> regrasp_ok=<..> seated=<..> finite=<..> qvel=<..>"
parse_cell () {  # tag
  local tag="$1" OUT="$BASE/cell_$1"
  if [ -f "$OUT/route_c2_pin.json" ]; then
    "$PY" - "$OUT/route_c2_pin.json" "$tag" <<'PYEOF'
import json,sys
d=json.load(open(sys.argv[1])); m=d.get("route_c2_metrics",{})
print(f"{sys.argv[2]} verdict={m.get('c2_regrasp_verdict')} regrasp_ok={m.get('c2_regrasp_ok')} "
      f"seated={m.get('c2_seated_honest')} finite={d.get('finite')} qvel={d.get('qvel_ok')} JSON=1")
PYEOF
  else
    local why="no-json"
    grep -qE "Traceback|IK NaN|NaN|explosion|CUDA error|out of memory" "$OUT/run.log" 2>/dev/null && why="INFRA(nan/crash/oom)"
    echo "$tag verdict=MISSING regrasp_ok=? seated=? finite=? qvel=? JSON=0 why=$why"
  fi
}

# ---- 81-cell grid: X,Y in {-20..+20} mm (9x9, 5mm pitch). mm tag + meters for CABLE_XY_OFFSET. ----
MM=(-20 -15 -10 -5 0 5 10 15 20)
MET=(-0.020 -0.015 -0.010 -0.005 0.000 0.005 0.010 0.015 0.020)
# Wave-1 = nominal + 3 edges (b2_cpC survivors) = SANITY (nominal must SUCCEED or abort).
CELLS=("x0_y0 0.000 0.000" "x20_y0 0.020 0.000" "x-20_y0 -0.020 0.000" "x0_y20 0.000 0.020")
for i in "${!MM[@]}"; do for j in "${!MM[@]}"; do
  tag="x${MM[$i]}_y${MM[$j]}"
  case "$tag" in x0_y0|x20_y0|x-20_y0|x0_y20) continue;; esac
  CELLS+=("$tag ${MET[$i]} ${MET[$j]}")
done; done
TOTAL=${#CELLS[@]}   # = 81

echo "=== P3-GRID START $(date '+%F %T') : $TOTAL cells, 4-way waves, cuda:0 ===" | tee -a "$SUMLOG"
NW=4; wave=0
for ((k=0; k<TOTAL; k+=NW)); do
  wave=$((wave+1))
  if (( wave < START_WAVE || wave > END_WAVE )); then continue; fi   # resume skip (cells already run in a prior range)
  echo "--- WAVE $wave launch $(date '+%T') ---" | tee -a "$SUMLOG"
  wave_tags=()
  for ((m=k; m<k+NW && m<TOTAL; m++)); do
    read -r tag dxm dym <<< "${CELLS[$m]}"; wave_tags+=("$tag")
    run_one "$tag" "$dxm" "$dym" &
  done
  wait
  # ---- wave summary + wave-granular abort (pre-reg §5: >=50% INFRA fail OR nominal fail -> STOP -> %12) ----
  infra=0
  for tag in "${wave_tags[@]}"; do
    line="$(parse_cell "$tag")"; echo "  $line" | tee -a "$SUMLOG"
    # infra/anomaly = no-json OR non-finite physics (NaN/explosion) — pre-reg §5 "NaN/explosion cluster" + %12 m1.
    echo "$line" | grep -qE "JSON=0|finite=False|finite=None" && infra=$((infra+1))
    if [ "$tag" = "x0_y0" ]; then
      echo "$line" | grep -qE "verdict=SUCCESS.*seated=True" || { echo "!! ABORT: nominal x0_y0 not SUCCESS/seated -> code-drift? STOP -> %12" | tee -a "$SUMLOG"; exit 3; }
    fi
  done
  n="${#wave_tags[@]}"
  if [ "$infra" -ge $(( (n+1)/2 )) ]; then
    echo "!! ABORT wave $wave: $infra/$n INFRA fails (no-json/nan/crash cluster) -> STOP -> %12" | tee -a "$SUMLOG"; exit 4
  fi
  echo "  wave $wave OK ($infra/$n infra) $(date '+%T')" | tee -a "$SUMLOG"
done
echo "=== P3-GRID ALL $TOTAL CELLS DONE $(date '+%F %T') ===" | tee -a "$SUMLOG"
