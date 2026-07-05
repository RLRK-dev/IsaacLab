#!/usr/bin/env bash
# W0-e build smoke — F-1a v2 + F-1b + F-2 built. Cells:
#  (1) nominal (0,0): byte-identity (npz sha vs RUN1_REFERENCE 3f44125551...).
#  (2) f2_x-20_y-15 / f2_x-15_y0: F-1a v2 + F-2 default-on (F-2 GUIDE follow validation + C1 v2 re-confirm 827.5).
#  (3) slowseat_x-20_y-15: F-1a v2 + W0E_F1A_SLOWSEAT=1 (deep-seat discriminator: z->829 dynamics / stays static).
# cuda:0 headless. 0-commit into w0e_build_smoke/.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_build_smoke
mkdir -p "$BASE"; unset DISPLAY
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075)

run_one () {  # tag offset [extra_env...]
  local tag="$1" off="$2"; shift 2; local OUT="$BASE/$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" "$@" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      --output-dir "$OUT" > "$OUT/run.log" 2>&1
  echo "DONE $tag exit=$? off=$off"
}

echo "=== W0E-BUILD-SMOKE START $(date '+%F %T') (cuda:0) ==="
run_one nominal_0_0 "0,0" &
run_one f2_x-20_y-15 "-0.020,-0.015" &
run_one f2_x-15_y0 "-0.015,0" &
run_one slowseat_x-20_y-15 "-0.020,-0.015" W0E_F1A_SLOWSEAT=1 &
wait
echo "=== W0E-BUILD-SMOKE DONE $(date '+%F %T') ==="
echo "--- nominal npz sha (expect 3f44125551868e278ff53e3ad454242e7ade17bd7a87237061f03d1d9cc3235d) ---"
sha256sum "$BASE/nominal_0_0/route_demo_raw.npz" 2>/dev/null
