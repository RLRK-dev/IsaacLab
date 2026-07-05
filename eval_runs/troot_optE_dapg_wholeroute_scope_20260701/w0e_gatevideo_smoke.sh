#!/usr/bin/env bash
# W0-e Rs-gate videos ② x0_y+5 ③ x0_y+12.5 (same build/env as w0e_liftraise_smoke.sh, video ON).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
HHMM=$(date '+%H%M')
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_liftraise_smoke
mkdir -p "$BASE"; unset DISPLAY
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.000)
FON_V1=(W0E_F1A=1 W0E_F1A_V2=0 W0E_F1B=1 W0E_F2=1 W0E_F3=0)
run_one () {
  local tag="$1" off="$2"; shift 2; local OUT="$BASE/${HHMM}_${tag}"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" "$@" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      --record-video --output-dir "$OUT" > "$OUT/run.log" 2>&1
  local rc=$?
  [ -f "$OUT/route_c1_to_c2.mp4" ] && cp "$OUT/route_c1_to_c2.mp4" "$HOME/Downloads/w0e_liftraise_${tag}.mp4"
  echo "DONE ${HHMM}_${tag} rc=$rc"
}
echo "=== W0E-GATEVIDEO START $(date '+%F %T') tag=$HHMM ==="
run_one x0_yp5_Fon    "0,0.005"  "${FON_V1[@]}" &
run_one x0_yp12.5v_Fon "0,0.0125" "${FON_V1[@]}" &
wait
echo "=== W0E-GATEVIDEO DONE $(date '+%F %T') ==="
ls -la ~/Downloads/w0e_liftraise_x0_*.mp4 2>/dev/null
