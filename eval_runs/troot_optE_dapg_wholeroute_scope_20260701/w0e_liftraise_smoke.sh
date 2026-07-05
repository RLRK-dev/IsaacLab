#!/usr/bin/env bash
# W0-e LIFT-RAISE smoke (Rs 2026-07-05 transport-clearance fix + Option A coordinate form). LIFT_M 0.05->0.08 (+30mm,
# GLOBAL incl nominal) = cable clears clip high-wall 850 during transport + C1_SEAT descent STARTS above clip -> v1
# X-comp vertical seat (no wall-ride). F-1a=v1 (W0E_F1A_V2=0), F-3 OFF, @150mm (CLIP2_Y=0.000). Generation-tagged
# dirs (new process rule: <HHMM>_<tag>/, NO in-place overwrite). 4 cell: nominal(new sha) + x-20 Fon + x-15 Fon +
# x0_y+12.5(B2 band). Videos nominal+x-20 -> ~/Downloads/w0e_liftraise_<tag>.mp4. Verify: transport cable z>854 /
# z_c1 829 / C1_ret_all / c2 honest / v1 z-x trace (vertical entry) / leg-diff SAME-STRUCTURE.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
HHMM=$(date '+%H%M')
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_liftraise_smoke
mkdir -p "$BASE"; unset DISPLAY
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.000)
FON_V1=(W0E_F1A=1 W0E_F1A_V2=0 W0E_F1B=1 W0E_F2=1 W0E_F3=0)   # step-table-faithful: v1 X-comp, F-3 OFF ; LIFT_M defaults 0.08 (global)

run_one () {  # tag offset video(0/1) [extra_env...]
  local tag="$1" off="$2" vid="$3"; shift 3; local OUT="$BASE/${HHMM}_${tag}"; mkdir -p "$OUT"
  local vflag=(); [ "$vid" = "1" ] && vflag=(--record-video)
  env "${ROUTE_ENV[@]}" "$@" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      "${vflag[@]}" --output-dir "$OUT" > "$OUT/run.log" 2>&1
  local rc=$?
  if [ "$vid" = "1" ] && [ -f "$OUT/route_c1_to_c2.mp4" ]; then
    cp "$OUT/route_c1_to_c2.mp4" "$HOME/Downloads/w0e_liftraise_${tag}.mp4"; echo "DONE ${HHMM}_${tag} rc=$rc VIDEO -> ~/Downloads/w0e_liftraise_${tag}.mp4"
  else echo "DONE ${HHMM}_${tag} rc=$rc off=$off (no video)"; fi
}

echo "=== W0E-LIFTRAISE-SMOKE START $(date '+%F %T') (cuda:0, LIFT_M=0.08, @150mm, tag=$HHMM) ==="
run_one nominal        "0,0"           1 W0E_F3=0 &
run_one x-20_y-15_Fon  "-0.020,-0.015" 1 "${FON_V1[@]}" &
run_one x-15_y0_Fon    "-0.015,0"      0 "${FON_V1[@]}" &
run_one x0_yp12.5_Fon  "0,0.0125"      0 "${FON_V1[@]}" &
wait
echo "=== W0E-LIFTRAISE-SMOKE DONE $(date '+%F %T') ==="
echo "--- nominal @LIFT_M0.08 NEW baseline sha (freeze candidate) ---"
sha256sum "$BASE/${HHMM}_nominal/route_demo_raw.npz" 2>/dev/null
ls -la ~/Downloads/w0e_liftraise_*.mp4 2>/dev/null
