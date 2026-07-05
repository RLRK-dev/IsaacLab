#!/usr/bin/env bash
# W0-e INTERIM confirmation videos (Rs direct request 2026-07-05 19:29). Current build = F-1a v2 + F-1b + F-2,
# slowseat OFF, NO F-3 (process imports pre-F-3 route code at launch). EGL offscreen (MUJOCO_GL=egl + unset DISPLAY
# = the established X11 BadWindow recipe). cuda:0. mp4 -> ~/Downloads/w0e_interim_<cell>_<HHMM>.mp4. Parallel-safe
# (_frames_dir = output_dir/_route_frames :3777, per-cell). INTERIM: ① x-20_y-15 may be replaced by the slowseat decision.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
BASE=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_interim_video
mkdir -p "$BASE"; unset DISPLAY
ROUTE_ENV=(S6_GRASP_ROUTE=1 S13_ROUTE_C2=1 PERCLIP_PIN=1 CLIP2=1 CLIP_COLLISION=1 SPACER=1 CLIP_FLOAT_Z=0.020 \
           SEAT_TOPDOWN=1 C2_DUALSEAT=1 CLIP_X=0.35 CLIP_Y=0.150 S6_ENGAGE_YC=0.15 CLIP2_X=0.40 CLIP2_Y=0.075)

render_one () {  # tag offset
  local tag="$1" off="$2"; local OUT="$BASE/$tag"; mkdir -p "$OUT"
  env "${ROUTE_ENV[@]}" DEMO_RECORD=1 DEMO_OUT="$OUT" CABLE_XY_OFFSET="$off" \
      CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
      "$PY" thread_isaac_lab/scripts/test_newton_clip_routing.py --solver-backend mujoco \
      --record-video --output-dir "$OUT" > "$OUT/run.log" 2>&1
  local rc=$?
  local hhmm; hhmm=$(date '+%H%M')
  local dst="$HOME/Downloads/w0e_interim_${tag}_${hhmm}.mp4"
  if [ -f "$OUT/route_c1_to_c2.mp4" ]; then cp "$OUT/route_c1_to_c2.mp4" "$dst"; echo "VIDEO $tag OK rc=$rc -> $dst"; else echo "VIDEO $tag FAIL rc=$rc (no mp4)"; fi
}

echo "=== W0E-INTERIM-VIDEO START $(date '+%F %T') (cuda:0, parallel) ==="
render_one nominal_0_0 "0,0" &
render_one x-20_y-15 "-0.020,-0.015" &
wait
echo "=== W0E-INTERIM-VIDEO DONE $(date '+%F %T') ==="
ls -la ~/Downloads/w0e_interim_*.mp4 2>/dev/null
