#!/usr/bin/env bash
# T-CLAMP-R-Train Phase 2 Smoke Actual Runner
#
# Source: T-CLAMP-R-Train-Phase-2-Smoke-Execute-Spec/execute_spec.md (732 行 §0-§9)
# Wrapper-only scope: invokes train_grip.py via subprocess, no env/config/orchestrator touches.
#
# Usage:
#   ./scripts/clamp_r_phase2_smoke_runner.sh [options]
#
# Options:
#   --seed N             Random seed (default: 42)
#   --world-count N      Parallel worlds (default: 64; alt 32/16 OOM fallback)
#   --max-iter N         Max iterations (default: 50; smoke ~1-2h budget)
#   --device-idx N       Physical CUDA device index (default: 2 for cuda:2 RTX PRO 4000 Blackwell 24GB)
#   --demo-path PATH     Demo HDF5 path (default: thread_isaac_lab/data/clamp_r_demos/{seed}.hdf5)
#   --log-base PATH      Log dir base (default: logs)
#   --tag NAME           Run tag suffix (default: clamp_r_train_smoke_seed{seed})
#   --expected-arm ARM   Clamp success predicate selector (default: right)
#   --dry-run            Run preflight + arg resolution only, do not launch train
#   --skip-preflight     Skip preflight checks (debug only, NOT for production smoke)
#   --no-monitor         Skip background monitor (for debug; use existing surr_rollback only)
#   --wall-timeout-min N Wall timeout cap in minutes (default: 130 = ~80-130 min ETA + buffer)
#   --estimated-gpu-hours N
#                        Estimated GPU hours; >=10 requires production launch gate
#   --production-scale   Mark this as production-scale; requires production launch gate
#   --multi-skill-chain  Mark this as multi-skill chain; requires production launch gate
#   --rs-approval-required
#                        Mark this run as Rs approval required; requires production launch gate
#   --gate-artifact PATH Production launch gate artifact path
#   -h, --help           Show this help
#
# Exit codes:
#   0  success (T1 saturation OR completed without abort, see RUN_METRICS verdict)
#   1  preflight FAIL (any of 5 verify cascade)
#   2  catastrophic abort (T3a-g)
#   3  plateau abort (T2)
#   4  inconclusive (50 iter complete, no signal)
#   5  internal error (unexpected)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISAACLAB_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HELPER_PY="${SCRIPT_DIR}/clamp_r_phase2_smoke_helper.py"
PYTHON_BIN="${ISAACLAB_ROOT}/env_isaaclab6/bin/python"
TRAIN_SCRIPT="${ISAACLAB_ROOT}/thread_isaac_lab/scripts/train_grip.py"

# Default arguments
seed=42
world_count=64
max_iter=50
device_idx=2
demo_path=""
log_base="${ISAACLAB_ROOT}/logs"
tag=""
expected_arm="right"
dry_run=0
skip_preflight=0
no_monitor=0
wall_timeout_min=130
estimated_gpu_hours=""
production_scale=0
multi_skill_chain=0
rs_approval_required=0
gate_artifact="${ISAACLAB_ROOT}/ProductionLaunchGate.md"

usage() {
  sed -n '3,30p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed) seed="$2"; shift 2 ;;
    --world-count) world_count="$2"; shift 2 ;;
    --max-iter) max_iter="$2"; shift 2 ;;
    --device-idx) device_idx="$2"; shift 2 ;;
    --demo-path) demo_path="$2"; shift 2 ;;
    --log-base) log_base="$2"; shift 2 ;;
    --tag) tag="$2"; shift 2 ;;
    --expected-arm) expected_arm="$2"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    --skip-preflight) skip_preflight=1; shift ;;
    --no-monitor) no_monitor=1; shift ;;
    --wall-timeout-min) wall_timeout_min="$2"; shift 2 ;;
    --estimated-gpu-hours) estimated_gpu_hours="$2"; shift 2 ;;
    --production-scale) production_scale=1; shift ;;
    --multi-skill-chain) multi_skill_chain=1; shift ;;
    --rs-approval-required) rs_approval_required=1; shift ;;
    --gate-artifact) gate_artifact="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[CLAMP-R-SMOKE][ERROR] Unknown argument: $1" >&2; usage; exit 5 ;;
  esac
done

# Argument validation
if [[ ! "${seed}" =~ ^[0-9]+$ ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] --seed must be non-negative integer: ${seed}" >&2; exit 5
fi
if [[ ! "${world_count}" =~ ^[0-9]+$ ]] || (( world_count < 1 )); then
  echo "[CLAMP-R-SMOKE][ERROR] --world-count must be positive integer: ${world_count}" >&2; exit 5
fi
if [[ ! "${max_iter}" =~ ^[0-9]+$ ]] || (( max_iter < 1 )); then
  echo "[CLAMP-R-SMOKE][ERROR] --max-iter must be positive integer: ${max_iter}" >&2; exit 5
fi
if [[ ! "${device_idx}" =~ ^[0-9]+$ ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] --device-idx must be non-negative integer: ${device_idx}" >&2; exit 5
fi
if [[ -n "${estimated_gpu_hours}" && ! "${estimated_gpu_hours}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] --estimated-gpu-hours must be non-negative number: ${estimated_gpu_hours}" >&2; exit 5
fi
if [[ -z "${demo_path}" ]]; then
  demo_path="${ISAACLAB_ROOT}/thread_isaac_lab/data/clamp_r_demos/${seed}.hdf5"
fi
if [[ -z "${tag}" ]]; then
  tag="clamp_r_train_smoke_seed${seed}"
fi
if [[ "${expected_arm}" != "right" && "${expected_arm}" != "left" && "${expected_arm}" != "both" ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] --expected-arm must be one of right,left,both: ${expected_arm}" >&2
  exit 5
fi

timestamp="$(date +%Y%m%d_%H%M%S)"
run_id="${tag}_${timestamp}"
log_dir="${log_base}/${run_id}"
metrics_dir="${ISAACLAB_ROOT}/data/test_${run_id}"

if [[ -e "${log_dir}" ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] Log dir already exists (refusing to overwrite): ${log_dir}" >&2
  exit 5
fi

# Sanity check tooling presence
for f in "${HELPER_PY}" "${TRAIN_SCRIPT}"; do
  if [[ ! -f "${f}" ]]; then
    echo "[CLAMP-R-SMOKE][ERROR] Missing required file: ${f}" >&2
    exit 5
  fi
done
if [[ "${dry_run}" -eq 0 && ! -x "${PYTHON_BIN}" ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] Python venv not executable: ${PYTHON_BIN}" >&2
  exit 5
fi

echo "[CLAMP-R-SMOKE] === Phase 2 Smoke Runner ==="
echo "[CLAMP-R-SMOKE] run_id          = ${run_id}"
echo "[CLAMP-R-SMOKE] seed            = ${seed}"
echo "[CLAMP-R-SMOKE] world_count     = ${world_count}"
echo "[CLAMP-R-SMOKE] max_iter        = ${max_iter}"
echo "[CLAMP-R-SMOKE] device_idx      = ${device_idx} (CUDA_VISIBLE_DEVICES=${device_idx} → torch cuda:0)"
echo "[CLAMP-R-SMOKE] demo_path       = ${demo_path}"
echo "[CLAMP-R-SMOKE] log_dir         = ${log_dir}"
echo "[CLAMP-R-SMOKE] metrics_dir     = ${metrics_dir}"
echo "[CLAMP-R-SMOKE] expected_arm    = ${expected_arm}"
echo "[CLAMP-R-SMOKE] wall_timeout    = ${wall_timeout_min} min"
echo "[CLAMP-R-SMOKE] dry_run         = ${dry_run}"
echo "[CLAMP-R-SMOKE] skip_preflight  = ${skip_preflight}"
echo "[CLAMP-R-SMOKE] no_monitor      = ${no_monitor}"
echo "[CLAMP-R-SMOKE] estimated_gpu_h = ${estimated_gpu_hours:-unset}"
echo "[CLAMP-R-SMOKE] production_scale= ${production_scale}"
echo "[CLAMP-R-SMOKE] multi_skill_chain=${multi_skill_chain}"
echo "[CLAMP-R-SMOKE] rs_approval_req = ${rs_approval_required}"
echo "[CLAMP-R-SMOKE] gate_artifact   = ${gate_artifact}"

requires_production_launch_gate() {
  if [[ "${production_scale}" -eq 1 || "${multi_skill_chain}" -eq 1 || "${rs_approval_required}" -eq 1 ]]; then
    return 0
  fi
  if [[ -n "${estimated_gpu_hours}" ]] && awk -v h="${estimated_gpu_hours}" 'BEGIN { exit !(h >= 10) }'; then
    return 0
  fi
  return 1
}

# Step 1: Preflight verification (Execute-Spec §2)
if [[ "${skip_preflight}" -eq 0 ]]; then
  echo "[CLAMP-R-SMOKE] --- Preflight verify ---"
  preflight_python="${PYTHON_BIN}"
  if [[ ! -x "${preflight_python}" ]]; then
    preflight_python="$(command -v python3 || true)"
  fi
  if [[ -z "${preflight_python}" || ! -x "${preflight_python}" ]]; then
    echo "[CLAMP-R-SMOKE][ERROR] No Python interpreter for preflight" >&2
    exit 1
  fi
  if ! "${preflight_python}" "${HELPER_PY}" preflight \
    --device-idx "${device_idx}" \
    --demo-path "${demo_path}" \
    --log-base "${log_base}" \
    --min-free-gb 23 \
    --min-disk-gb 5; then
    echo "[CLAMP-R-SMOKE][ERROR] Preflight FAIL — smoke launch refused" >&2
    exit 1
  fi
  echo "[CLAMP-R-SMOKE] Preflight PASS"
else
  echo "[CLAMP-R-SMOKE][WARN] Preflight skipped (--skip-preflight)"
fi

if requires_production_launch_gate; then
  echo "[CLAMP-R-SMOKE] --- Production launch gate ---"
  if ! bash "${ISAACLAB_ROOT}/harness/scripts/preflight_launch_gate.sh" "${gate_artifact}"; then
    echo "[CLAMP-R-SMOKE][ERROR] Production launch gate FAIL — high-cost launch refused" >&2
    exit 1
  fi
  echo "[CLAMP-R-SMOKE] Production launch gate PASS"
else
  echo "[CLAMP-R-SMOKE] Production launch gate not required for this run"
fi

# Dry-run: stop here, print would-be invocation
if [[ "${dry_run}" -eq 1 ]]; then
  echo "[CLAMP-R-SMOKE] --- DRY-RUN: would-be invocation ---"
  cat <<EOF
CUDA_VISIBLE_DEVICES=${device_idx} \\
  ${PYTHON_BIN} ${TRAIN_SCRIPT} \\
    --mode clamp --hand R --dual-arm --expected-arm ${expected_arm} \\
    --seed ${seed} --max-iterations ${max_iter} \\
    --world-count ${world_count} --device cuda:0 \\
    --demos ${demo_path} \\
    --log-dir ${log_dir} \\
    --alpha-init 0.5 --alpha-min 0.5
Background monitor:
  ${PYTHON_BIN} ${HELPER_PY} monitor \\
    --log-dir ${log_dir} --max-iter ${max_iter} \\
    --t1-sr 0.30 --t1-window 5 \\
    --t2-sr 0.05 --t2-window 10 \\
    --wall-timeout-sec $(( wall_timeout_min * 60 ))
Final aggregate:
  ${PYTHON_BIN} ${HELPER_PY} aggregate \\
    --log-dir ${log_dir} --metrics-dir ${metrics_dir} \\
    --run-id ${run_id} --seed ${seed} --iter-max ${max_iter} \\
    --expected-arm ${expected_arm} \\
    --demo-path ${demo_path}
EOF
  echo "[CLAMP-R-SMOKE] DRY-RUN complete (exit 0)"
  exit 0
fi

# Step 2: Actual launch
mkdir -p "${log_dir}" "${metrics_dir}"
started_at="$(date -Iseconds)"
echo "${started_at}" > "${log_dir}/started_at.txt"

echo "[CLAMP-R-SMOKE] --- Launch train_grip.py ---"
set +e
(
  export CUDA_VISIBLE_DEVICES="${device_idx}"
  "${PYTHON_BIN}" "${TRAIN_SCRIPT}" \
    --mode clamp --hand R --dual-arm --expected-arm "${expected_arm}" \
    --seed "${seed}" --max-iterations "${max_iter}" \
    --world-count "${world_count}" --device cuda:0 \
    --demos "${demo_path}" \
    --log-dir "${log_dir}" \
    --alpha-init 0.5 --alpha-min 0.5 \
    > "${log_dir}/stdout.log" 2>&1
) &
TRAIN_PID=$!
echo "${TRAIN_PID}" > "${log_dir}/train.pid"
echo "[CLAMP-R-SMOKE] train PID=${TRAIN_PID}"

# Step 3: Background monitor (Execute-Spec §4)
if [[ "${no_monitor}" -eq 0 ]]; then
  echo "[CLAMP-R-SMOKE] --- Launch monitor ---"
  "${PYTHON_BIN}" "${HELPER_PY}" monitor \
    --log-dir "${log_dir}" \
    --max-iter "${max_iter}" \
    --train-pid "${TRAIN_PID}" \
    --t1-sr 0.30 --t1-window 5 \
    --t2-sr 0.05 --t2-window 10 \
    --wall-timeout-sec "$(( wall_timeout_min * 60 ))" \
    > "${log_dir}/monitor.log" 2>&1 &
  MONITOR_PID=$!
  echo "${MONITOR_PID}" > "${log_dir}/monitor.pid"
  echo "[CLAMP-R-SMOKE] monitor PID=${MONITOR_PID}"
fi

# Step 4: Wait for train completion
wait "${TRAIN_PID}"
train_rc=$?
set -e

# Step 5: Stop monitor cleanly if still alive
if [[ "${no_monitor}" -eq 0 ]] && kill -0 "${MONITOR_PID:-0}" 2>/dev/null; then
  kill -TERM "${MONITOR_PID}" 2>/dev/null || true
  wait "${MONITOR_PID}" 2>/dev/null || true
fi

completed_at="$(date -Iseconds)"
echo "${completed_at}" > "${log_dir}/completed_at.txt"
echo "[CLAMP-R-SMOKE] train exit_code=${train_rc}"

# Step 6: Aggregate RUN_METRICS (Execute-Spec §6)
echo "[CLAMP-R-SMOKE] --- Aggregate RUN_METRICS ---"
"${PYTHON_BIN}" "${HELPER_PY}" aggregate \
  --log-dir "${log_dir}" \
  --metrics-dir "${metrics_dir}" \
  --run-id "${run_id}" \
  --seed "${seed}" \
  --iter-max "${max_iter}" \
  --expected-arm "${expected_arm}" \
  --demo-path "${demo_path}" \
  --train-exit-code "${train_rc}"

# Step 7: Resolve verdict and exit code
verdict_json="${metrics_dir}/RUN_METRICS.json"
if [[ ! -f "${verdict_json}" ]]; then
  echo "[CLAMP-R-SMOKE][ERROR] RUN_METRICS.json missing after aggregation" >&2
  exit 5
fi

verdict="$("${PYTHON_BIN}" "${HELPER_PY}" verdict --metrics-json "${verdict_json}" --field verdict)"
echo "[CLAMP-R-SMOKE] verdict=${verdict}"

case "${verdict}" in
  SUCCESS_PROMOTE_MULTI_SEED) exit 0 ;;
  FAIL_NO_SIGNAL_REDESIGN) exit 3 ;;
  FAIL_CATASTROPHE_FRESH_RESTART) exit 2 ;;
  RESULT_INCONCLUSIVE_RERUN_OR_ESCALATE) exit 4 ;;
  *)
    echo "[CLAMP-R-SMOKE][ERROR] Unknown verdict: ${verdict}" >&2
    exit 5
    ;;
esac
