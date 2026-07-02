#!/usr/bin/env bash
# CP-⑤b RUN-1: None-path byte-identity re-proof on the fix-⑤ harness.
# CABLE_XY_OFFSET UNSET -> dx==0 -> fix-⑤ block skipped -> route_c2_pin.json sha256 MUST == e01ac1fa…
# Same env as run_canonical.sh + MUJOCO_GL=egl + unset DISPLAY (X11 BadWindow fix; physics byte-identical).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
OUT=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/b2_fix5_run1
rm -rf "$OUT"; mkdir -p "$OUT"
unset DISPLAY
echo "=== CP-⑤b RUN-1 (fix-⑤ harness, CABLE_XY_OFFSET UNSET, EGL) ==="
env S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
    SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075 \
    CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
    "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --record-video --output-dir "$OUT" \
    > "$OUT/run.log" 2>&1
echo "RUN1 EXIT=$?"
echo "############ RUN-1 sha bar ############"
BASE=e01ac1fad2ff415538a53c9786a9ed6060cb189b99a4ab6fc5fdda619717df6a
if [ -f "$OUT/route_c2_pin.json" ]; then
  GOT=$(sha256sum "$OUT/route_c2_pin.json" | awk '{print $1}')
  echo "baseline=$BASE"
  echo "run-1   =$GOT"
  [ "$GOT" = "$BASE" ] && echo "RUN1_VERDICT=BYTE_IDENTICAL_PASS" || echo "RUN1_VERDICT=MISMATCH_STOP"
else
  echo "RUN1_VERDICT=JSON_MISSING_STOP"
fi
echo "############ RUN-1 regrasp verdict ############"
test -f "$OUT/route_c2_pin.json" && "$PY" -c "import json;d=json.load(open('$OUT/route_c2_pin.json'));r=d.get('route_c2_regrasp',{});print('regrasp_ok=',r.get('regrasp_ok'),'verdict=',r.get('verdict'))" 2>/dev/null
echo "############ DONE RUN-1 ############"
