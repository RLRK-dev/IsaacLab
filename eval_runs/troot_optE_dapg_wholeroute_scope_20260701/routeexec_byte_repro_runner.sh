#!/usr/bin/env bash
# Layer-A byte-repro launch wrapper (node route-executor, D-1=C). Pins the device to cuda:0 (A6000,
# index 0) -- byte-repro is device-fragile (cuda:1 = MISMATCH; build plan §13.8). Device pinning lives
# in this eval_runs/ shell layer (the proven pattern of w0e_81rerun_snapdown_runner.sh); the Python
# orchestrator inherits CUDA_VISIBLE_DEVICES via os.environ and never sets it in code (validations
# check_safety.sh CHECK 6 bans the literal in THREAD python). All flags after the script name pass
# through to test_routeexec_byte_repro.py (e.g. --nproc 4 / --cells x0_y0 / --ref-subset x0_y0).
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
export CUDA_VISIBLE_DEVICES=0   # cuda:0 ONLY (device-fragile byte-repro; inherited by all workers)
export MUJOCO_GL=egl
unset DISPLAY

# GPU hygiene preflight (build plan §13.8 / §運用GPU): show current compute apps; A6000 <=4 proc.
echo "=== ROUTEEXEC BYTE-REPRO launch $(date '+%F %T') : device=cuda:0 (A6000 index0) ==="
nvidia-smi --query-compute-apps=pid,used_memory,gpu_name --format=csv,noheader 2>/dev/null \
  | sed 's/^/  [compute-apps] /' || echo "  (nvidia-smi unavailable)"

exec "$PY" thread_isaac_lab/scripts/test_routeexec_byte_repro.py "$@"
