#!/usr/bin/env bash
# W0-e SPACING discriminator smoke (Rs 2026-07-05: double C1-C2 spacing 75->150mm = CLIP2_Y=0.000, 07-01 slip-halving
# lever) + STEP-TABLE-FAITHFUL revision (Rs「43step表からはずれるな」: fixes = coordinate correction of EXISTING steps
# only; F-1a v2 lift/shift/trim + F-3 X-shift = invented motions -> OFF). 4 cells @ 150mm:
#   A=nominal (NEW baseline sha freeze + video) / B=x-20 F-1a v1(W0E_F1A_V2=0, simple g=0.5 comp on existing descent
#   legs) + F-1b + F-2, F-3 OFF / C=x-20 ALL-F-OFF (spacing-alone isolation) / D=x-15 same as B.
# Read: cradle all-leg / nonpin floor+wall / crossing / honest / escape. Videos A/B -> ~/Downloads/w0e_150mm_<cell>.mp4
# (--record-video verified NOT to affect npz). F-3 OFF everywhere (verdict: counterproductive, pre-F-3 honest=True).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_150mm_smoke
mkdir -p "$BASE"; unset DISPLAY
# CLIP2_Y=0.000 => 150mm spacing (C1 y=0.150 fixed, C2 y 0.075->0.000)
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.000)
# F-1a v1 (step-table-faithful: X-comp on existing descent, no lift/shift/trim) + F-1b + F-2, F-3 OFF
FON_V1=(W0E_F1A=1 W0E_F1A_V2=0 W0E_F1B=1 W0E_F2=1 W0E_F3=0)
FOFF=(W0E_F1A=0 W0E_F1B=0 W0E_F2=0 W0E_F3=0)

run_one () {  # tag offset video(0/1) [extra_env...]
  local tag="$1" off="$2" vid="$3"; shift 3; local OUT="$BASE/$tag"; mkdir -p "$OUT"
  local vflag=(); [ "$vid" = "1" ] && vflag=(--record-video)
  env "${ROUTE_ENV[@]}" "$@" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      "${vflag[@]}" --output-dir "$OUT" > "$OUT/run.log" 2>&1
  local rc=$?
  if [ "$vid" = "1" ] && [ -f "$OUT/route_c1_to_c2.mp4" ]; then
    cp "$OUT/route_c1_to_c2.mp4" "$HOME/Downloads/w0e_150mm_${tag}.mp4"; echo "DONE $tag rc=$rc VIDEO -> ~/Downloads/w0e_150mm_${tag}.mp4"
  else echo "DONE $tag rc=$rc off=$off (no video)"; fi
}

echo "=== W0E-150MM-SMOKE START $(date '+%F %T') (cuda:0, CLIP2_Y=0.000=150mm, step-table-faithful F-1a v1 / F-3 OFF) ==="
run_one nominal        "0,0"           1 W0E_F3=0 &
run_one x-20_y-15_Fon  "-0.020,-0.015" 1 "${FON_V1[@]}" &
run_one x-20_y-15_Foff "-0.020,-0.015" 1 "${FOFF[@]}" &
run_one x-15_y0_Fon    "-0.015,0"      0 "${FON_V1[@]}" &
wait
echo "=== W0E-150MM-SMOKE DONE $(date '+%F %T') ==="
echo "--- NEW nominal @150mm baseline sha (FREEZE candidate, retires old 3f4412) ---"
sha256sum "$BASE/nominal/route_demo_raw.npz" 2>/dev/null
ls -la ~/Downloads/w0e_150mm_*.mp4 2>/dev/null
