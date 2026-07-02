#!/usr/bin/env bash
# CP-⑤b RUN-2: dx=+20 physical confirm of fix-⑤ X-follow (wire-then-validate).
# CABLE_XY_OFFSET="0.020,0" -> dx=+20mm -> fix-⑤ block FIRES -> x_grasp re-centres to ~GRASP_X+20mm.
# PASS bar = grasp-capture + lift HOLD (existing gates). full-route SUCCESS = expected-but-informative.
# Grasp fail => STOP + report plainly (falsification output). §運用14 video-analyst leg on the mp4.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
OUT=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/b2_fix5_run2
rm -rf "$OUT"; mkdir -p "$OUT"
unset DISPLAY
echo "=== CP-⑤b RUN-2 (fix-⑤ harness, CABLE_XY_OFFSET=0.020,0 [dx=+20mm], EGL) ==="
env S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
    SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075 \
    CABLE_XY_OFFSET="0.020,0" \
    CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
    "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco --record-video --output-dir "$OUT" \
    > "$OUT/run.log" 2>&1
echo "RUN2 EXIT=$?"
cp -f "$OUT/route_c1_to_c2.mp4" "$HOME/Downloads/route_fix5_dx+20.mp4" 2>/dev/null && echo "video -> ~/Downloads/route_fix5_dx+20.mp4"
cp -f "$OUT/route_c1_to_c2.png" "$HOME/Downloads/route_fix5_dx+20.png" 2>/dev/null
echo "############ RUN-2 X-follow echo (expect delta ~+20mm) ############"
grep -E "\[S6_ROUTE\] caveat-a-X|\[S6_ROUTE\] caveat-a:" "$OUT/run.log" 2>/dev/null
echo "############ RUN-2 grasp/regrasp verdict ############"
grep -E "\[C2-REGRASP-GATE\]|\[C2-REGRASP-GRIP\]|IK NaN|Traceback|Error" "$OUT/run.log" 2>/dev/null | head
test -f "$OUT/route_c2_pin.json" && "$PY" -c "import json;d=json.load(open('$OUT/route_c2_pin.json'));r=d.get('route_c2_regrasp',{});print('regrasp_ok=',r.get('regrasp_ok'),'verdict=',r.get('verdict'));print('x_grasp=',d.get('route_c2_freeze_scope') and '','milestone_ok=',d.get('milestone_ok'))" 2>/dev/null || echo "(JSON MISSING => grasp likely failed, report plainly)"
echo "############ DONE RUN-2 ############"
