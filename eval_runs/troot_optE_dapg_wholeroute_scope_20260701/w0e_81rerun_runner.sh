#!/usr/bin/env bash
# W0-e 81 RE-RUN (RUN-2) — script-only DR grid over the canonical C1->C2 route w/ the lift-raise fix build (rollout-HALT
#   non-抵触). %12 order 2026-07-06 02:05 (Rs video-gate OK). Adapted VERBATIM from p3_grid_runner.sh (old 40/81 grid),
#   only DELTAS: (1) ROUTE_ENV CLIP2_Y 0.075->0.000 (Rs 間隔倍化 150mm) (2) FON_V1 F-flags ON (offset-gated fixes:
#   F-1a v1 + F-1B + F-2 ON, F-3 OFF) applied to ALL cells (3) generation-tagged immutable dir w0e_81rerun_<HHMM>
#   (no in-place overwrite) (4) x0_y0 EARLY sha-gate vs RUN1_REFERENCE_V2 5f1c3f92 (leg ① protect, aborts ~5min if
#   byte-id breaks). build = current on-disk (LIFT_M 0.08 default). 0-commit. cuda:0 + EGL + headless, no --record-video.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
HHMM=$(date '+%H%M')
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_${HHMM}
mkdir -p "$BASE"
unset DISPLAY
SUMLOG="$BASE/_wave_summary.log"
START_WAVE=${START_WAVE:-1}; END_WAVE=${END_WAVE:-21}
[ "$START_WAVE" = "1" ] && : > "$SUMLOG"
RUN1_REF="5f1c3f9238f45057011cfad1d010ac43000cb179b76b61d0461733a9075416cf"   # RUN1_REFERENCE_V2 (new-build nominal)

# Canonical route env-gate stack — VERBATIM from p3_grid_runner.sh EXCEPT CLIP2_Y 0.075->0.000 (Rs 150mm 間隔倍化).
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.000)
# Fixes = offset-gated (inert at 0,0 -> nominal byte-id). F-1a v1 (V2 off), F-1B, F-2 ON; F-3 OFF (Rs step-table-faithful).
FON_V1=(W0E_F1A=1 W0E_F1A_V2=0 W0E_F1B=1 W0E_F2=1 W0E_F3=0)

run_one () {  # tag dx_m dy_m
  local tag="$1" dxm="$2" dym="$3"
  local OUT="$BASE/cell_$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" "${FON_V1[@]}" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$dxm,$dym" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --output-dir "$OUT" \
      > "$OUT/run.log" 2>&1
  echo "DONE $tag (off=$dxm,$dym) exit=$?"
}

parse_cell () {  # tag  -> one summary line from route_c2_pin.json
  local tag="$1" OUT="$BASE/cell_$1"
  if [ -f "$OUT/route_c2_pin.json" ]; then
    "$PY" - "$OUT/route_c2_pin.json" "$tag" <<'PYEOF'
import json,sys
d=json.load(open(sys.argv[1])); m=d.get("route_c2_metrics",{})
print(f"{sys.argv[2]} verdict={m.get('c2_regrasp_verdict')} regrasp_ok={m.get('c2_regrasp_ok')} "
      f"seated={m.get('c2_seated_honest')} c1ret={m.get('all_c1_retained_lowwall')} finite={d.get('finite')} qvel={d.get('qvel_ok')} JSON=1")
PYEOF
  else
    local why="no-json"
    grep -qE "Traceback|IK NaN|NaN|explosion|CUDA error|out of memory" "$OUT/run.log" 2>/dev/null && why="INFRA(nan/crash/oom)"
    echo "$tag verdict=MISSING regrasp_ok=? seated=? c1ret=? finite=? qvel=? JSON=0 why=$why"
  fi
}

# ---- 81-cell grid: X,Y in {-20..+20} mm (9x9, 5mm pitch) — IDENTICAL offset set to p3_grid (old 40/81). ----
MM=(-20 -15 -10 -5 0 5 10 15 20)
MET=(-0.020 -0.015 -0.010 -0.005 0.000 0.005 0.010 0.015 0.020)
CELLS=("x0_y0 0.000 0.000" "x20_y0 0.020 0.000" "x-20_y0 -0.020 0.000" "x0_y20 0.000 0.020")
for i in "${!MM[@]}"; do for j in "${!MM[@]}"; do
  tag="x${MM[$i]}_y${MM[$j]}"
  case "$tag" in x0_y0|x20_y0|x-20_y0|x0_y20) continue;; esac
  CELLS+=("$tag ${MET[$i]} ${MET[$j]}")
done; done
TOTAL=${#CELLS[@]}   # = 81

echo "=== W0E-81-RERUN START $(date '+%F %T') : $TOTAL cells, 4-way waves, cuda:0, dir=$BASE ===" | tee -a "$SUMLOG"
NW=4; wave=0
for ((k=0; k<TOTAL; k+=NW)); do
  wave=$((wave+1))
  if (( wave < START_WAVE || wave > END_WAVE )); then continue; fi
  echo "--- WAVE $wave launch $(date '+%T') ---" | tee -a "$SUMLOG"
  wave_tags=()
  for ((m=k; m<k+NW && m<TOTAL; m++)); do
    read -r tag dxm dym <<< "${CELLS[$m]}"; wave_tags+=("$tag")
    run_one "$tag" "$dxm" "$dym" &
  done
  wait
  infra=0
  for tag in "${wave_tags[@]}"; do
    line="$(parse_cell "$tag")"; echo "  $line" | tee -a "$SUMLOG"
    echo "$line" | grep -qE "JSON=0|finite=False|finite=None" && infra=$((infra+1))
    if [ "$tag" = "x0_y0" ]; then
      # nominal verdict sanity (code-drift guard, from p3_grid)
      echo "$line" | grep -qE "verdict=SUCCESS.*seated=True" || { echo "!! ABORT: nominal x0_y0 not SUCCESS/seated -> code-drift? STOP -> %12" | tee -a "$SUMLOG"; exit 3; }
      # leg ① EARLY sha-gate: (0,0) npz MUST == RUN1_REFERENCE_V2 (byte-id under FON_V1 offset-gating)
      got="$(sha256sum "$BASE/cell_x0_y0/route_demo_raw.npz" 2>/dev/null | awk '{print $1}')"
      if [ "$got" = "$RUN1_REF" ]; then
        echo "  [RUN1-GATE] x0_y0 npz sha == RUN1_REFERENCE_V2 EXACT ($got) -> leg ① PASS" | tee -a "$SUMLOG"
      else
        echo "!! ABORT: x0_y0 npz sha=$got != RUN1_REF=$RUN1_REF -> FON_V1 byte-id BROKEN at (0,0) -> STOP -> %12" | tee -a "$SUMLOG"; exit 5
      fi
    fi
  done
  n="${#wave_tags[@]}"
  if [ "$infra" -ge $(( (n+1)/2 )) ]; then
    echo "!! ABORT wave $wave: $infra/$n INFRA fails (no-json/nan/crash cluster) -> STOP -> %12" | tee -a "$SUMLOG"; exit 4
  fi
  echo "  wave $wave OK ($infra/$n infra) $(date '+%T')" | tee -a "$SUMLOG"
done
echo "=== W0E-81-RERUN ALL $TOTAL CELLS DONE $(date '+%F %T') dir=$BASE ===" | tee -a "$SUMLOG"
echo "--- nominal x0_y0 npz sha (RUN-1 leg, expect 5f1c3f92) ---" | tee -a "$SUMLOG"
sha256sum "$BASE/cell_x0_y0/route_demo_raw.npz" 2>/dev/null | tee -a "$SUMLOG"
