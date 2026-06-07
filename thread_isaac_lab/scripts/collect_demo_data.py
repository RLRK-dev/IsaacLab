#!/usr/bin/env python3
"""
Collect Expert Demonstration Data for World Model Training.

This script collects expert demonstrations from the phase-based cable-on-hook
manipulation workflow, saving observations and actions in HDF5 format.

Data collected per step:
- Captured cameras (for video/API): front_left, front_center, front_right, back, overhead
- Stored camera images in HDF5 (256x256, JPEG): front_left, front_right, back, overhead
- proprio (34D): joint positions, velocities, EE positions for both arms
- task_state (44D): cable segments, hook, EE positions, distances
- action (18D): 7 joint deltas + 2 gripper per arm

Usage:
    cd /home/rlrk/IsaacLab
    DISPLAY=:1 timeout 1800 env_isaaclab/bin/python \
        thread_isaac_lab/scripts/collect_demo_data.py \
        --device cuda:0 --num_cycles 5 --output_dir data/demo_data_v1

Output:
    data/demo_data_v1/demo_cycle_XXXX.h5
"""

# --- Protocol Version Lock (v24.46) ---
# Note: Disabled - STATE.json.current_version tracks hypothesis version (v120, v121, etc.)
#       not protocol version (v24.46). These are different concepts.
# TODO: If re-enabling, use a separate field like STATE.json.protocol_version
import json
from pathlib import Path

PROTOCOL_VERSION = "v24.73"
STATE_JSON = Path("/home/rlrk/Claudecode/shared/STATE.json")

# Version check disabled - current_version is hypothesis version, not protocol version
print(f"[{PROTOCOL_VERSION}] Protocol version (check disabled)")
# --- end Protocol Version Lock ---

import sys
import atexit  # v24.30: Ensure video is saved on any exit (including Auto-abort)
import signal  # v24.30: Signal handlers for clean shutdown
import faulthandler  # H198: Hang diagnosis
import time as _time  # H198: Wall-time tracking
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, "/home/rlrk/IsaacLab")

# H198: Enable faulthandler for hang diagnosis
faulthandler.enable(file=sys.stderr, all_threads=True)
faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)  # H213/v199: Reduce to 120s for faster hang detection
print("[v199] faulthandler enabled: will dump traceback every 120s (2 min) if stuck")

def _h198_sigusr1_handler(signum, frame):
    """Handle SIGUSR1 by dumping traceback (H198)."""
    print("\n[H198] SIGUSR1 received - dumping traceback...", file=sys.stderr)
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    sys.stderr.flush()

signal.signal(signal.SIGUSR1, _h198_sigusr1_handler)
print("[H198] SIGUSR1 handler registered for traceback dump")

# v199: Watchdog timer for sim.step() hang detection
import threading
_v199_watchdog_timeout = 60  # seconds
_v199_watchdog_timer = None
_v199_watchdog_triggered = threading.Event()

def _v199_watchdog_handler():
    """Called when sim.step() exceeds watchdog timeout."""
    print(f"\n[v199 WATCHDOG] sim.step() blocked for > {_v199_watchdog_timeout}s - HANG DETECTED", file=sys.stderr)
    sys.stderr.flush()
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    sys.stderr.flush()
    _v199_watchdog_triggered.set()
    # Note: We don't forcibly kill here; faulthandler will continue periodic dumps
    # and external timeout (run_and_collect.sh) will terminate if needed

def v199_watchdog_start():
    """Start watchdog timer before sim.step()."""
    global _v199_watchdog_timer
    if _v199_watchdog_timer is not None:
        _v199_watchdog_timer.cancel()
    _v199_watchdog_timer = threading.Timer(_v199_watchdog_timeout, _v199_watchdog_handler)
    _v199_watchdog_timer.daemon = True
    _v199_watchdog_timer.start()

def v199_watchdog_stop():
    """Stop watchdog timer after sim.step() completes."""
    global _v199_watchdog_timer
    if _v199_watchdog_timer is not None:
        _v199_watchdog_timer.cancel()
        _v199_watchdog_timer = None

print(f"[v199] Watchdog timer enabled: {_v199_watchdog_timeout}s timeout for sim.step()")

# v201/H214: signal.alarm-based per-step timeout (Code C INTERRUPT response: PHASE3_HANG_PATTERN)
# Unlike v199 watchdog (threading.Timer, can't interrupt), this uses SIGALRM to actually interrupt sim.step()
_v201_step_timeout = 30  # seconds per sim.step() call
_v201_current_phase = 0
_v201_current_step = 0

class SimStepTimeoutError(Exception):
    """Raised when sim.step() exceeds timeout."""
    pass

def _v201_alarm_handler(signum, frame):
    """Handle SIGALRM by raising TimeoutError to interrupt sim.step()."""
    print(f"\n[v201 TIMEOUT] sim.step() exceeded {_v201_step_timeout}s at phase={_v201_current_phase} step={_v201_current_step}", file=sys.stderr)
    sys.stderr.flush()
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    sys.stderr.flush()
    # Raise exception to interrupt sim.step() - will be caught by sim_step_with_timeout()
    raise SimStepTimeoutError(f"sim.step() timeout at phase={_v201_current_phase}, step={_v201_current_step}")

# Register SIGALRM handler
signal.signal(signal.SIGALRM, _v201_alarm_handler)
print(f"[v201] signal.alarm per-step timeout enabled: {_v201_step_timeout}s (SIGALRM-based interruption)")

def sim_step_with_timeout(sim, phase: int, step: int):
    """Execute sim.step() with SIGALRM timeout protection.

    v201/H214: Response to Code C INTERRUPT (PHASE3_HANG_PATTERN)
    4 consecutive Phase 3 lift hangs required a stronger mechanism than v199 watchdog.

    Args:
        sim: Isaac Sim simulation object
        phase: Current phase number (for logging)
        step: Current step within phase (for logging)

    Raises:
        SimStepTimeoutError: If sim.step() exceeds timeout
    """
    global _v201_current_phase, _v201_current_step
    _v201_current_phase = phase
    _v201_current_step = step

    # Set alarm before sim.step()
    signal.alarm(_v201_step_timeout)
    try:
        sim.step()
    finally:
        # Cancel alarm after sim.step() (or on exception)
        signal.alarm(0)

# ActiveRun.json lifecycle management (added for stale entry prevention)
def cleanup_active_run_entry(run_id: str, active_run_path: str = "/home/rlrk/Claudecode/shared/ActiveRun.json"):
    """Remove this test from ActiveRun.json on exit (normal or abnormal)."""
    import json
    import fcntl
    from datetime import datetime
    lock_path = "/home/rlrk/Claudecode/shared/.ssot.lock"

    try:
        with open(lock_path, 'w') as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                with open(active_run_path, 'r') as f:
                    data = json.load(f)

                original_count = len(data.get('active_tests', []))
                data['active_tests'] = [t for t in data.get('active_tests', []) if t.get('run_id') != run_id]
                new_count = len(data['active_tests'])

                if original_count != new_count:
                    data['last_updated'] = datetime.now().isoformat()
                    tmp_path = f"{active_run_path}.tmp.{os.getpid()}"
                    with open(tmp_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    os.replace(tmp_path, active_run_path)
                    print(f"[ActiveRun] Removed {run_id} from ActiveRun.json ({original_count} -> {new_count})")
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
    except Exception as e:
        print(f"[ActiveRun] WARNING: Failed to cleanup: {e}")


def register_active_run_entry(run_id: str, active_run_path: str = "/home/rlrk/Claudecode/shared/ActiveRun.json"):
    """v24.76: Register this test in ActiveRun.json to prevent monitor_code_a.sh from killing it."""
    import json
    import fcntl
    from datetime import datetime
    lock_path = "/home/rlrk/Claudecode/shared/.ssot.lock"

    try:
        with open(lock_path, 'w') as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                # Read existing or create new
                if os.path.exists(active_run_path):
                    with open(active_run_path, 'r') as f:
                        data = json.load(f)
                else:
                    data = {'active_tests': []}

                # Add this test if not already present
                if not any(t.get('run_id') == run_id for t in data.get('active_tests', [])):
                    data.setdefault('active_tests', []).append({
                        'run_id': run_id,
                        'pid': os.getpid(),
                        'started_at': datetime.now().isoformat()
                    })
                    data['last_updated'] = datetime.now().isoformat()
                    tmp_path = f"{active_run_path}.tmp.{os.getpid()}"
                    with open(tmp_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    os.replace(tmp_path, active_run_path)
                    print(f"[ActiveRun] Registered {run_id} (PID {os.getpid()})")
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
    except Exception as e:
        print(f"[ActiveRun] WARNING: Failed to register: {e}")


import os
import io
import math  # H099: for cosine interpolation
import argparse
from datetime import datetime
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_cycles", type=int, default=5, help="Number of cycles to collect")
parser.add_argument("--max_phase", type=int, default=8, help="Maximum phase to execute (1-8, exits after completing this phase)")
parser.add_argument("--output_dir", type=str, default="data/demo_data_v1", help="Output directory")
parser.add_argument("--image_size", type=int, default=256, help="Image size (square)")
parser.add_argument("--jpeg_quality", type=int, default=85, help="JPEG compression quality")
parser.add_argument("--save_video", action="store_true", help="Save 2x2 grid video")
parser.add_argument("--video_output", type=str, default="data/videos/demo_collection.mp4", help="Video output path")
parser.add_argument("--video_fps", type=int, default=30, help="Video frame rate")
parser.add_argument("--single_camera", action="store_true", help="Use front_center camera only (5-cam crash workaround, LL-20260320-DIAG-001)")
parser.add_argument("--no_cameras", action="store_true", help="Disable ALL cameras and rendering (diagnostic: isolate rendering as crash root cause)")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = not getattr(args, 'no_cameras', False)
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import h5py
import torch
import numpy as np
import shutil
import subprocess
from PIL import Image
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    CABLE_SEGMENT_COUNT,  # H240: For dynamic segment index calculation
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS,
    PHASE45_LEFT_JOINTS, PHASE45_RIGHT_JOINTS,
    PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
    PHASE55_LEFT_JOINTS, PHASE55_RIGHT_JOINTS,
    PHASE7_LEFT_JOINTS, PHASE7_RIGHT_JOINTS,
    WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT,
    WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT,
    WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT,
    WAYPOINT_PHASE45A_LEFT, WAYPOINT_PHASE45A_RIGHT,
    WAYPOINT_PHASE45B_LEFT, WAYPOINT_PHASE45B_RIGHT,
    WAYPOINT_PHASE45C_LEFT, WAYPOINT_PHASE45C_RIGHT,
    WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT,
    WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT,
    WAYPOINT_PHASE55_LEFT, WAYPOINT_PHASE55_RIGHT,
    WAYPOINT_PHASE6_LEFT, WAYPOINT_PHASE6_RIGHT,
    WAYPOINT_PHASE7_LEFT, WAYPOINT_PHASE7_RIGHT,
    GRIPPER_CLOSE, GRIPPER_OPEN,
    RELEASE_STABILIZE_STEPS, RELEASE_GRIPPER_STEPS, PHASE55_TO_6_STEPS,
    CYCLE_RESET_STABILIZATION_STEPS,
    HOOK_X, HOOK_Y, HOOK_Z,
    ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE,
    ROBOT_BASE_QUAT_WXYZ, GRIPPER_DOWN_QUAT_WXYZ, GRIPPER_ROTATED_90_QUAT_WXYZ,
    USE_GEOFIK_FOR_STAGE_CD, GEOFIK_Q7_MIN, GEOFIK_Q7_MAX, GEOFIK_Q7_STEPS,
    # H097/v71: Stage 1b mid waypoint for elbow transition split
    WAYPOINT_STAGE1B_MID_LEFT, WAYPOINT_STAGE1B_MID_RIGHT, STAGE1B_MID_STABILIZE_STEPS,
    # H102/v76: Part 2 3-stage split for elbow boundary crossing
    PART2A_TARGET_Z, PART2B_TARGET_Z, PART2C_TARGET_Z,
    PART2A_STEPS, PART2B_STEPS, PART2C_STEPS,
    # H104: Fingertip offset for IK target Z correction
    FINGERTIP_OFFSET,
    # H115: J3 constraint and IK flip prevention
    STAGE2A_J3_MIN_DEG, STAGE2A_J3_MAX_DEG, MAX_JOINT_CHANGE_DEG, STAGE_CD_MAX_JOINT_CHANGE_DEG, STAGE2A_STEPS,
    # H136: Stage 2a-2 target positions + velocity clamping
    STAGE2A_POSITIONS, MAX_JOINT_VELOCITY,
    # H145: EE velocity limit for position-based interpolation
    MAX_EE_VELOCITY,
    # H157-fix: Lift verification threshold (was hardcoded 0.03)
    LIFT_VERIFY_THRESHOLD,
    # H164: Force R threshold-based dynamic velocity control
    FORCE_R_HIGH, FORCE_R_LOW, VEL_REDUCED, FORCE_L_ABORT, FORCE_R_ABORT,
    # H165: Force L direct monitoring for Stage B stabilization
    FORCE_L_HIGH_THRESHOLD, FORCE_L_LOW_THRESHOLD, FORCE_L_REDUCED_VELOCITY,
    # H191: B.5c mid-stabilization (Force spike suppression at step 36)
    H191_B5C_MID_STABILIZE_STEPS, H191_B5C_PART1_STEPS, H191_B5C_PART2_STEPS,
    # H192: Part 2 split (Force spike suppression at Part 2 step 26)
    H192_B5C_PART2A_STEPS, H192_B5C_PART2_MID_STABILIZE_STEPS, H192_B5C_PART2B_STEPS,
    # H193: Proportional follow (Left arm follows right arm movement)
    H193_LEFT_FOLLOW_RATIO, H193_FOLLOW_AXIS, H193_MIN_THRESHOLD_CM,
    # H200: B.5b X movement split (Force spike suppression at B.5b step 38)
    H200_B5B_PART1_X_R, H200_B5B_PART1_STEPS, H200_B5B_MID_STABILIZE_STEPS, H200_B5B_PART2_STEPS,
    # H202: Phase 3 Lift NaN root cause fix (velocity reduction + ramp extension)
    H202_MAX_EE_VELOCITY, H202_RAMP_STEPS, H202_LIFT_STEPS,
    # H204: Phase 3 IK tracking error countermeasure (JOINT_DELTA_MAX relaxation)
    H204_PHASE3_JOINT_DELTA_MAX,
    # H205: Phase 3 max_step A/B test
    H205_PHASE3_MAX_STEP_OVERRIDE, H205_PHASE3_MAX_STEP_MM,
    # H227: Phase 2 Early Exit (Hang Isolation Test)
    H227_EARLY_EXIT_AFTER_PHASE2,
    # H228: Phase 3 Start Early Exit (Hang Position Isolation)
    H228_EARLY_EXIT_AFTER_PHASE3_START, H228_PHASE3_EARLY_EXIT_STEPS,
    # H229: Left/Right Arm Target Swap Test (DISABLED - design bug)
    H229_SWAP_LR_TARGETS,
    # H230: Grasp Coordinate Swap Test (Correct Implementation)
    H230_SWAP_GRASP_COORDS,
    # H233: Left Arm Lambda Val Adjustment (IK tracking improvement - incremental tuning)
    H233_LEFT_LAMBDA_VAL,
    # H261: Stage C Intermediate Waypoints (IK Fix for Gate-R PASS)
    # H267: Fixed position constants removed - using dynamic calculation from B.5c end position
    # H261_WP1_LEFT, H261_WP1_RIGHT removed (dynamic calculation at L4782)
    # H261_WP2_LEFT, H261_WP2_RIGHT removed (dynamic calculation at L4814)
    H261_WP1_STEPS, H261_WP2_STEPS, H261_WP_STABILIZE_STEPS,
    # Gate System (v24.82) - Early exit on intermediate goal failure
    ENABLE_GATE_SYSTEM,
    GATE_G_ENABLED, GATE_L_ENABLED, GATE_R_ENABLED, GATE_H_ENABLED,
    GATE_WINDOW_FRAMES, GATE_OK_RATIO,
    GATE_G_GRIPPER_WIDTH_MAX, GATE_G_FINGERTIP_CABLE_DIST_MAX,
    GATE_L_LIFT_DZ_MIN, GATE_R_ROT_TOL_DEG, GATE_H_CABLE_HOOK_DIST_MAX,
    # H268: Phase 3 Render Interval (Viewport HANG Prevention)
    H268_PHASE3_RENDER_INTERVAL,
)

# H063/H077: Analytical IK for Stage 1b/1c (replacing Diff IK)
from thread_isaac_lab.scripts.franka_analytical_ik import solve_ik_best, solve_ik_best_near_current, franka_IK_EE_with_base

# v55: NaN Detection and Retry Mechanism
class NaNDetectedException(Exception):
    """Exception raised when NaN is detected in cable physics."""
    def __init__(self, location: str):
        self.location = location
        super().__init__(f"NaN detected at {location}")

# v56: Skip strategy (no retry, just skip failed cycles)
MAX_RETRIES = 0

# H270: Controlled Experiment (single-variable change for Stage C2/D right-arm X target)
H270_STAGE_CD_RIGHT_TARGET_X = 0.48

IK_TRACE_FILENAME = "IK_TRACE_v1.jsonl"
IK_TRACE_VERSION = "IK_TRACE_v1"
DIAG_TRACE_FILENAME = "DIAG_TRACE_v1.jsonl"
DIAG_TRACE_VERSION = "DIAG_TRACE_v1"
DIAG_SUMMARY_FILENAME = "DIAG_SUMMARY_v1.json"
DIAG_SUMMARY_VERSION = "DIAG_SUMMARY_v1"


# =============================================================================
# Gate System Functions (v24.82)
# =============================================================================

import json
from datetime import datetime

def log_gate_eval(gate_id: str, phase: str, ok: bool, metrics: dict,
                  thresholds: dict, action: str = None, verdict: str = None):
    """Log gate evaluation to EVENT_LOG.jsonl"""
    log_entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": "GATE_EVAL",
        "gate_id": gate_id,
        "phase": phase,
        "window": {"frames": GATE_WINDOW_FRAMES, "ok_ratio_required": GATE_OK_RATIO},
        "metrics": metrics,
        "thresholds": thresholds,
        "ok": ok,
    }
    if action:
        log_entry["action"] = action
    if verdict:
        log_entry["verdict"] = verdict

    log_path = "/home/rlrk/Claudecode/shared/EVENT_LOG.jsonl"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[GATE] Failed to write log: {e}")


def _quat_wxyz_to_xyzw(quat_wxyz: np.ndarray) -> np.ndarray:
    return np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]], dtype=float)


def _quat_xyzw_to_wxyz(quat_xyzw: np.ndarray) -> np.ndarray:
    return np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]], dtype=float)


def _pose_to_matrix(pos: np.ndarray, quat_wxyz: np.ndarray) -> np.ndarray:
    from scipy.spatial.transform import Rotation as R

    T = np.eye(4)
    T[:3, :3] = R.from_quat(_quat_wxyz_to_xyzw(np.asarray(quat_wxyz, dtype=float))).as_matrix()
    T[:3, 3] = np.asarray(pos, dtype=float)
    return T


def _matrix_to_pose_dict(T: np.ndarray) -> dict:
    from scipy.spatial.transform import Rotation as R

    quat_xyzw = R.from_matrix(T[:3, :3]).as_quat()
    quat_wxyz = _quat_xyzw_to_wxyz(quat_xyzw)
    return {
        "position_m": [float(x) for x in T[:3, 3]],
        "quaternion_wxyz": [float(x) for x in quat_wxyz],
    }


def _rotation_error_rad(R_target: np.ndarray, R_actual: np.ndarray) -> float:
    from scipy.spatial.transform import Rotation as R

    r_delta = R.from_matrix(R_actual).inv() * R.from_matrix(R_target)
    return float(r_delta.magnitude())


def _append_ik_trace(entry: dict):
    trace_path = os.path.join(args.output_dir, IK_TRACE_FILENAME)
    try:
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[IK_TRACE] Failed to write {trace_path}: {e}")


def _append_diag_trace(entry: dict):
    trace_path = os.path.join(args.output_dir, DIAG_TRACE_FILENAME)
    try:
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[DIAG_TRACE] Failed to write {trace_path}: {e}")


def _frontmatter_value(path: str, key: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return ""

    if not lines or lines[0].strip() != "---":
        return ""
    end = 1
    while end < len(lines) and lines[end].strip() != "---":
        end += 1
    if end >= len(lines):
        return ""

    prefix = f"{key}:"
    for ln in lines[1:end]:
        s = ln.strip()
        if s.startswith(prefix):
            return s[len(prefix):].strip()
    return ""


_DIAG_HYPOTHESIS_ID = os.environ.get(
    "HYPOTHESIS_ID",
    _frontmatter_value("/home/rlrk/Claudecode/shared/TASKS_B.md", "hypothesis_id"),
)
_DIAG_PROBE_PACK = os.environ.get(
    "PROBE_PACK",
    _frontmatter_value("/home/rlrk/Claudecode/shared/TASKS_B.md", "probe_pack"),
)
_DIAG_SUMMARY_STATE = {
    "samples": 0,
    "success_count": 0,
    "pos_err_sum": 0.0,
    "rot_err_sum": 0.0,
}


def _update_diag_summary(last_event: dict):
    err = last_event.get("error", {})
    status = last_event.get("status", {})

    _DIAG_SUMMARY_STATE["samples"] += 1
    if bool(status.get("success", False)):
        _DIAG_SUMMARY_STATE["success_count"] += 1

    pos_err = err.get("pos_err_m")
    rot_err = err.get("rot_err_rad")
    if pos_err is not None:
        _DIAG_SUMMARY_STATE["pos_err_sum"] += float(pos_err)
    if rot_err is not None:
        _DIAG_SUMMARY_STATE["rot_err_sum"] += float(rot_err)

    n = max(1, _DIAG_SUMMARY_STATE["samples"])
    mean_pos_err = _DIAG_SUMMARY_STATE["pos_err_sum"] / n
    mean_rot_err = _DIAG_SUMMARY_STATE["rot_err_sum"] / n
    success_rate = _DIAG_SUMMARY_STATE["success_count"] / n

    # Generic signature score: lower error + higher success => closer to 1.0.
    score_pos = max(0.0, min(1.0, 1.0 - (mean_pos_err / 0.05)))
    score_rot = max(0.0, min(1.0, 1.0 - (mean_rot_err / 0.5)))
    signature_score = (score_pos + score_rot + success_rate) / 3.0

    support_level = "INCONCLUSIVE"
    if signature_score >= 0.75 and success_rate >= 0.8:
        support_level = "REJECT"
    elif signature_score <= 0.35:
        support_level = "SUPPORT"

    summary = {
        "version": DIAG_SUMMARY_VERSION,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "hypothesis_id": _DIAG_HYPOTHESIS_ID,
        "probe_pack": _DIAG_PROBE_PACK,
        "signature_score": float(signature_score),
        "support_level": support_level,
        "evidence_completeness": {
            "samples": int(_DIAG_SUMMARY_STATE["samples"]),
            "has_hypothesis_id": bool(_DIAG_HYPOTHESIS_ID),
            "has_probe_pack": bool(_DIAG_PROBE_PACK),
        },
        "top_features": {
            "success_rate": float(success_rate),
            "mean_pos_err_m": float(mean_pos_err),
            "mean_rot_err_rad": float(mean_rot_err),
        },
    }

    out_path = os.path.join(args.output_dir, DIAG_SUMMARY_FILENAME)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DIAG_SUMMARY] Failed to write {out_path}: {e}")


def check_window_stability(history: list, threshold_check_fn) -> tuple:
    """
    Check if threshold is met for GATE_OK_RATIO of last GATE_WINDOW_FRAMES.
    Returns (ok, ok_ratio)
    """
    if len(history) < GATE_WINDOW_FRAMES:
        # Not enough data, assume OK to avoid false negatives
        return True, 1.0

    window = history[-GATE_WINDOW_FRAMES:]
    ok_count = sum(1 for v in window if threshold_check_fn(v))
    ok_ratio = ok_count / GATE_WINDOW_FRAMES
    return ok_ratio >= GATE_OK_RATIO, ok_ratio


def gate_g_check(gripper_width_history: list, fingertip_cable_dist_history: list) -> tuple:
    """
    Gate-G: Check grasp success (Phase 2→3)
    Returns (ok, detail_dict)
    """
    if not ENABLE_GATE_SYSTEM or not GATE_G_ENABLED:
        return True, {"skipped": True}

    width_ok, width_ratio = check_window_stability(
        gripper_width_history,
        lambda w: w < GATE_G_GRIPPER_WIDTH_MAX
    )
    dist_ok, dist_ratio = check_window_stability(
        fingertip_cable_dist_history,
        lambda d: d < GATE_G_FINGERTIP_CABLE_DIST_MAX
    )

    ok = width_ok and dist_ok
    detail = {
        "gripper_width_ok_ratio": width_ratio,
        "fingertip_cable_dist_ok_ratio": dist_ratio,
        "last_gripper_width": gripper_width_history[-1] if gripper_width_history else None,
        "last_fingertip_cable_dist": fingertip_cable_dist_history[-1] if fingertip_cable_dist_history else None,
    }
    return ok, detail


def gate_l_check(ee_z_history: list, initial_z: float) -> tuple:
    """
    Gate-L: Check lift success (Phase 3→4)
    Returns (ok, detail_dict)
    """
    if not ENABLE_GATE_SYSTEM or not GATE_L_ENABLED:
        return True, {"skipped": True}

    dz_history = [z - initial_z for z in ee_z_history]
    ok, ok_ratio = check_window_stability(
        dz_history,
        lambda dz: dz > GATE_L_LIFT_DZ_MIN
    )

    detail = {
        "lift_dz_ok_ratio": ok_ratio,
        "last_dz": dz_history[-1] if dz_history else None,
        "initial_z": initial_z,
    }
    return ok, detail


def gate_r_check(q_pre_rotation, q_current_history: list) -> tuple:
    """
    Gate-R: Check 90-degree rotation (Phase 4.5c→5)
    Returns (ok, detail_dict)

    Uses relative rotation: delta_rot = q_current * inverse(q_pre)
    """
    if not ENABLE_GATE_SYSTEM or not GATE_R_ENABLED:
        return True, {"skipped": True}

    from scipy.spatial.transform import Rotation as R

    # Convert pre-rotation quat (WXYZ) to scipy format (XYZW)
    q_pre_xyzw = np.array([q_pre_rotation[1], q_pre_rotation[2],
                           q_pre_rotation[3], q_pre_rotation[0]])
    r_pre = R.from_quat(q_pre_xyzw)
    r_pre_inv = r_pre.inv()

    def calc_delta_deg(q_current_wxyz):
        q_cur_xyzw = np.array([q_current_wxyz[1], q_current_wxyz[2],
                               q_current_wxyz[3], q_current_wxyz[0]])
        r_cur = R.from_quat(q_cur_xyzw)
        r_delta = r_cur * r_pre_inv
        angle_rad = r_delta.magnitude()  # Total rotation angle
        return np.degrees(angle_rad)

    delta_deg_history = [calc_delta_deg(q) for q in q_current_history]

    ok, ok_ratio = check_window_stability(
        delta_deg_history,
        lambda deg: abs(deg - 90) <= GATE_R_ROT_TOL_DEG
    )

    detail = {
        "rotation_ok_ratio": ok_ratio,
        "last_delta_deg": delta_deg_history[-1] if delta_deg_history else None,
        "target_deg": 90,
        "tolerance_deg": GATE_R_ROT_TOL_DEG,
    }
    return ok, detail


def gate_h_check(cable_hook_dist_history: list) -> tuple:
    """
    Gate-H: Check hook proximity (Phase 5.5c→6)
    Returns (ok, detail_dict)
    """
    if not ENABLE_GATE_SYSTEM or not GATE_H_ENABLED:
        return True, {"skipped": True}

    ok, ok_ratio = check_window_stability(
        cable_hook_dist_history,
        lambda d: d < GATE_H_CABLE_HOOK_DIST_MAX
    )

    detail = {
        "hook_dist_ok_ratio": ok_ratio,
        "last_cable_hook_dist": cable_hook_dist_history[-1] if cable_hook_dist_history else None,
    }
    return ok, detail


def early_exit(gate_id: str, phase: str, detail: dict, verdict: str):
    """
    Handle early exit due to gate failure.
    Returns exit info dict for caller to handle.
    """
    log_gate_eval(
        gate_id=gate_id,
        phase=phase,
        ok=False,
        metrics=detail,
        thresholds={
            "Gate-G": {"gripper_width_max": GATE_G_GRIPPER_WIDTH_MAX,
                       "fingertip_cable_dist_max": GATE_G_FINGERTIP_CABLE_DIST_MAX},
            "Gate-L": {"lift_dz_min": GATE_L_LIFT_DZ_MIN},
            "Gate-R": {"rotation_tol_deg": GATE_R_ROT_TOL_DEG},
            "Gate-H": {"cable_hook_dist_max": GATE_H_CABLE_HOOK_DIST_MAX},
        }.get(gate_id, {}),
        action="EARLY_EXIT",
        verdict=verdict
    )

    print(f"[GATE] {gate_id} FAILED at Phase {phase} -> EARLY_EXIT with verdict={verdict}")
    print(f"[GATE] Detail: {detail}")

    return {
        "exit_type": "EARLY_EXIT",
        "gate_id": gate_id,
        "phase": phase,
        "verdict": verdict,
        "detail": detail
    }


# H120: Adaptive step splitting for large joint motions (2026-01-12)
# Root cause fix: command-level clamping (H118/H119) doesn't limit actual physics motion
# Solution: split large target motions into smaller waypoints BEFORE sending to simulator
def split_large_motion_joints(start_joints: np.ndarray, target_joints: np.ndarray,
                               max_change_deg: float = 30.0) -> list:
    """Split large joint motions into smaller waypoints to prevent 30° violations.

    H120: This is a root cause fix. Unlike H118/H119 which clamp commands AFTER
    physics step (ineffective), this splits the target BEFORE sending to simulator.

    Args:
        start_joints: Current joint positions (7,) numpy array in radians
        target_joints: Target joint positions (7,) numpy array in radians
        max_change_deg: Maximum allowed change per step in degrees (default 30°)

    Returns:
        List of waypoint joint arrays. If motion is small, returns [target_joints].
        Otherwise, returns multiple intermediate waypoints.
    """
    delta = target_joints - start_joints
    max_delta_deg = np.degrees(np.abs(delta).max())

    if max_delta_deg > max_change_deg:
        num_splits = int(np.ceil(max_delta_deg / max_change_deg))
        waypoints = []
        for i in range(num_splits):
            alpha = (i + 1) / num_splits
            waypoints.append(start_joints + alpha * delta)
        print(f"  [H120] Large motion detected: {max_delta_deg:.1f}° → split into {num_splits} waypoints")
        sys.stdout.flush()
        return waypoints
    else:
        return [target_joints]


# Constants
HIGH_FRICTION = 8.0  # B0: Prevent grip loss (was: 5.0)
Z_OFFSET = 0.1173  # Corrected: fingertip at cable Z=0.755, panda_hand = 0.755 + 0.1123 = 0.8673

# H160 Investigation: Disable cable for manipulability test
# Set to True to teleport cable away and test pure arm movement
# H240: Cable ENABLED for Phase 3 test with v16_halfseg (10 segments)
# H239 diagnostic confirmed: cable causes Phase 3 hang
# Now testing if reduced segments (10 vs 20) resolves the issue
H160_DISABLE_CABLE = True  # H260: Cable DISABLED for PG0 v24.82 revalidation

# H240: Cable SPAWNED with reduced segments (v16_halfseg: 10 segments)
# H239 diagnostic completed: cable removal fixed Phase 3 hang
# Now restoring cable with reduced segment count to test PhysX load theory
H239_NO_CABLE_SPAWN = True  # H260: Cable NOT spawned for PG0 v24.82 revalidation

# LL-20260320-DIAG-001: Single camera mode to avoid non-deterministic 5-camera crash
SINGLE_CAMERA_MODE = getattr(args, 'single_camera', False)
# Diagnostic: Disable ALL cameras and rendering to isolate rendering as crash root cause
NO_CAMERAS_MODE = getattr(args, 'no_cameras', False)

# Phase step counts
PHASE1_STEPS = 100
PHASE12_STEPS = 300
GRASP_CLOSE_STEPS = 100  # Gradual gripper close (like opt_b)
GRASP_STABILIZE = 50  # H219: Reduced from 100 to preserve peak grasp force (LL-2026-01-30-GRIP-001)
LIFT_STEPS = H202_LIFT_STEPS  # H202: 1600 → 3200 (velocity reduction compensation)
PHASE34_STEPS = 400
PHASE445_STEPS = 300
PHASE455_STEPS = 300
PHASE55_STEPS = 200
POST_RETREAT_STEPS = 200
PHASE67_STEPS = 400
LIFT_CM = 10.0  # Target: 10cm lift with cable v5 + damping=80.0

# Frame collection interval
# Simulation at 240Hz, collection interval of 4 steps = 60Hz collection
# Increase frame count while maintaining video duration
FRAME_COLLECT_INTERVAL = 4  # Changed from 20 to 4 for 5x more frames

# Video frame skip (save every N data collection steps)
# Skip count relative to data collection steps
# 1 = Save video frame at every data step (maximum frame count)
# 2 = Save every 2nd step (half the frame count)
# H209: Increase to 10 to reduce I/O bottleneck (was 1, causing timeout in Phase 3)
VIDEO_FRAME_SKIP = 1  # v278b conclusion: any rendering causes crash. Reverted to 1 (R511). Post-hoc rendering planned.

# Data dimensions
PROPRIO_DIM = 34
TASK_STATE_DIM = 44
ACTION_DIM = 18

# Camera selection for capture (video/API) vs stored HDF5 dataset.
CAPTURE_CAMERA_NAMES = ["front_left", "front_center", "front_right", "back", "overhead"]
STORED_CAMERA_NAMES = ["front_left", "front_right", "back", "overhead"]

if NO_CAMERAS_MODE:
    CAPTURE_CAMERA_NAMES = []
    STORED_CAMERA_NAMES = []
elif SINGLE_CAMERA_MODE:
    CAPTURE_CAMERA_NAMES = ["front_center"]
    STORED_CAMERA_NAMES = []
    print(f"[SINGLE_CAMERA] Using front_center only (LL-20260320-DIAG-001)")

os.makedirs(args.output_dir, exist_ok=True)

# ActiveRun.json lifecycle: Register on start, cleanup on exit
# v24.76: Register FIRST to prevent monitor_code_a.sh from killing the process
# Extract run_id from output_dir and normalize to canonical form used by run_and_collect.sh
# e.g., ./data/test_v146_H198_fullcycle -> v146_H198_fullcycle
_activerun_id = os.path.basename(args.output_dir.rstrip('/'))
if _activerun_id.startswith("test_"):
    _activerun_id = _activerun_id[len("test_"):]
register_active_run_entry(_activerun_id)  # v24.76: Register in ActiveRun.json
atexit.register(cleanup_active_run_entry, _activerun_id)
print(f"[ActiveRun] Registered cleanup for {_activerun_id}")

# Video recording setup
VIDEO_FRAME_DIR = "/tmp/demo_video_frames"
video_frame_count = 0
video_collect_counter = 0  # Track data collection steps for video frame skip

if args.save_video:
    os.makedirs(VIDEO_FRAME_DIR, exist_ok=True)
    # Clear old frames
    for f in os.listdir(VIDEO_FRAME_DIR):
        os.remove(os.path.join(VIDEO_FRAME_DIR, f))
    video_output_dir = os.path.dirname(args.video_output)
    if video_output_dir:
        os.makedirs(video_output_dir, exist_ok=True)

print("=" * 70)
print("EXPERT DEMONSTRATION DATA COLLECTION")
print(f"Cycles: {args.num_cycles}")
print(f"Output: {args.output_dir}")
if args.save_video:
    print(f"Video: {args.video_output} ({args.video_fps} fps)")
print("=" * 70)


# H264: Checkpoint video function to save partial video at stage transitions
# This preserves visual evidence even if later stages fail
_checkpoint_video_counter = 0

def save_checkpoint_video(checkpoint_name: str, env_idx: int = 0):
    """Save a checkpoint video from collected frames up to current point.

    H264: Captures partial video at stage transitions for post-mortem analysis.
    Uses copy of frames to not interfere with final video generation.

    Args:
        checkpoint_name: Identifier for checkpoint (e.g., "stage_a_complete")
        env_idx: Environment index for multi-env runs
    """
    global _checkpoint_video_counter, video_frame_count

    if not args.save_video or video_frame_count == 0:
        print(f"[H264] No frames to save for checkpoint: {checkpoint_name}")
        return

    _checkpoint_video_counter += 1
    checkpoint_dir = os.path.dirname(args.video_output)
    if not checkpoint_dir:
        checkpoint_dir = "."

    # Create checkpoint video filename
    base_name = os.path.splitext(os.path.basename(args.video_output))[0]
    checkpoint_path = os.path.join(
        checkpoint_dir,
        f"{base_name}_checkpoint_{_checkpoint_video_counter:02d}_{checkpoint_name}.mp4"
    )

    print(f"\n[H264] Saving checkpoint video: {checkpoint_name}")
    print(f"[H264] Frames: {video_frame_count}, Output: {checkpoint_path}")

    # Use ffmpeg to create checkpoint video from current frames
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(args.video_fps),
        "-i", os.path.join(VIDEO_FRAME_DIR, "frame_%06d.jpg"),
        "-frames:v", str(video_frame_count),  # Only encode collected frames
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        checkpoint_path
    ]

    try:
        import subprocess
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            size_bytes = os.path.getsize(checkpoint_path) if os.path.exists(checkpoint_path) else 0
            print(f"[H264] Checkpoint saved: {checkpoint_path} ({size_bytes / 1024 / 1024:.2f} MB)")
        else:
            print(f"[H264] Checkpoint video failed: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"[H264] Checkpoint video timed out (120s)")
    except Exception as e:
        print(f"[H264] Checkpoint video error: {e}")


# v24.30: atexit-based video finalization to ensure video is saved on ANY exit
# This includes Auto-abort (H145 WARNING, Cable NaN, H150 threshold, etc.)
_video_finalized = False

def finalize_video():
    """Save video from collected frames. Called on exit via atexit.

    v24.30 compliance: Video must be saved before ANY exit, including:
    - H145 WARNING Auto-abort
    - Cable NaN Auto-abort
    - H150 fingertip distance threshold Auto-abort
    - Lift too low Auto-abort
    """
    global _video_finalized, video_frame_count

    if _video_finalized:
        return  # Already finalized, prevent double-call
    _video_finalized = True

    if not args.save_video or video_frame_count == 0:
        print("[v24.30] No video frames to save")
        return

    print("\n" + "=" * 70)
    print("[v24.30] FINALIZING VIDEO (atexit handler)")
    print("=" * 70)
    print(f"Total frames collected: {video_frame_count}")

    # H209: JPEG frames for I/O performance
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(args.video_fps),
        "-i", os.path.join(VIDEO_FRAME_DIR, "frame_%06d.jpg"),  # H209: .png → .jpg
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",  # H227 v221: Lower CRF for larger file size (1MB+ required)
        "-pix_fmt", "yuv420p",
        args.video_output
    ]

    # v24.49: Debug - check frame directory before ffmpeg
    # H209: Check for .jpg files instead of .png
    if os.path.exists(VIDEO_FRAME_DIR):
        frame_files = sorted([f for f in os.listdir(VIDEO_FRAME_DIR) if f.endswith('.jpg')])
        print(f"[v24.49] Frames in directory: {len(frame_files)}")
        if frame_files:
            print(f"[v24.49] First frame: {frame_files[0]}, Last frame: {frame_files[-1]}")
    else:
        print(f"[v24.49] WARNING: Frame directory does not exist: {VIDEO_FRAME_DIR}")

    print(f"Running: {' '.join(ffmpeg_cmd)}")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[v24.30] Video saved: {args.video_output}")
        if os.path.exists(args.video_output):
            size_mb = os.path.getsize(args.video_output) / (1024 * 1024)
            print(f"[v24.30] File size: {size_mb:.1f} MB")
        # v24.49: Always print ffmpeg stderr for debugging
        if result.stderr:
            print(f"[v24.49] FFmpeg info: {result.stderr[-500:]}")
    else:
        print(f"[v24.30] FFmpeg error: {result.stderr}")

    # Cleanup frames
    if os.path.exists(VIDEO_FRAME_DIR):
        print("[v24.30] Cleaning up temporary frames...")
        shutil.rmtree(VIDEO_FRAME_DIR)

# Register video finalization to run on ANY exit (including sys.exit)
atexit.register(finalize_video)


# v24.73: Signal handlers - save video before exit (Gate#31 compliance)
# Previous v24.51 skipped video save with os._exit() to avoid Isaac Sim hang.
# v24.73: finalize_video() only uses ffmpeg/file ops (no Isaac Sim), so safe to call.
def _signal_handler(signum, frame):
    """Handle termination signals - save video before exit.

    v24.73: Save video before exit to comply with Gate#31 (video required for analysis).
    finalize_video() is safe because it only uses ffmpeg and file operations,
    not Isaac Sim APIs that could hang in multithreaded environment.
    See LL-2026-01-24-BUG-001 for original hang issue context.
    """
    print(f"\n[v24.73] Received signal {signum}, saving video before exit...")
    sys.stdout.flush()
    try:
        finalize_video()  # Safe: only ffmpeg/file ops, no Isaac Sim calls
    except Exception as e:
        print(f"[v24.73] Video finalization failed: {e}")
    sys.stdout.flush()
    os._exit(128 + signum)  # Exit after video save attempt

# Register signal handlers for common termination signals
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# v24.38: NaN snapshot video saving
_nan_video_saved = False

def save_nan_snapshot_video(step: int):
    """Save video snapshot when NaN is detected.

    v24.38: Creates a separate video file capturing frames up to NaN detection.
    The main video.mp4 will still be saved on exit.

    Args:
        step: The step number where NaN was detected
    """
    global _nan_video_saved, video_frame_count

    if _nan_video_saved:
        return  # Already saved NaN snapshot
    _nan_video_saved = True

    if not args.save_video or video_frame_count == 0:
        print("[v24.38] No video frames for NaN snapshot")
        return

    # Determine output path
    output_dir = os.path.dirname(args.video_output)
    nan_video_path = os.path.join(output_dir, f"video_nan_step{step}.mp4")

    print(f"\n[v24.38] Saving NaN snapshot video at step {step}...")
    print(f"[v24.38] Frames collected so far: {video_frame_count}")

    # v24.49: Debug - check frame directory before NaN snapshot ffmpeg
    # H209: Check for .jpg files instead of .png
    if os.path.exists(VIDEO_FRAME_DIR):
        frame_files = sorted([f for f in os.listdir(VIDEO_FRAME_DIR) if f.endswith('.jpg')])
        print(f"[v24.49 NaN] Frames in directory: {len(frame_files)}")
        if frame_files:
            print(f"[v24.49 NaN] First: {frame_files[0]}, Last: {frame_files[-1]}")
    else:
        print(f"[v24.49 NaN] WARNING: Frame directory does not exist!")

    # H209: JPEG frames for I/O performance
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(args.video_fps),
        "-i", os.path.join(VIDEO_FRAME_DIR, "frame_%06d.jpg"),  # H209: .png → .jpg
        "-c:v", "libx264",
        "-preset", "fast",  # Faster encoding for snapshot
        "-crf", "18",  # H227 v221: Lower CRF for larger file size (1MB+ required)
        "-pix_fmt", "yuv420p",
        nan_video_path
    ]

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        if os.path.exists(nan_video_path):
            size_mb = os.path.getsize(nan_video_path) / (1024 * 1024)
            print(f"[v24.38] NaN snapshot saved: {nan_video_path} ({size_mb:.1f} MB)")
        else:
            print(f"[v24.38] NaN snapshot saved: {nan_video_path}")
        # v24.49: Print ffmpeg stderr for debugging
        if result.stderr:
            print(f"[v24.49 NaN] FFmpeg info: {result.stderr[-500:]}")
    else:
        print(f"[v24.38] FFmpeg error for NaN snapshot: {result.stderr}")

    # Note: Do NOT cleanup frames here - they're still needed for final video.mp4


def compress_image_jpeg(img_array: np.ndarray, quality: int = 85) -> bytes:
    """Compress numpy image array to JPEG bytes."""
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


def pil_to_jpeg_bytes(img: Image.Image, quality: int = 85) -> bytes:
    """Convert PIL image to JPEG bytes (for API upload)."""
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()


def save_video_frame(
    images: dict,
    resolution: int = 512,
    phase: int = None,
    step: int = None,
    save_to_disk: bool = False,
):
    """Build 3x2 grid frame and return as PIL image.

    Args:
        images: Dictionary of camera name -> numpy array
        resolution: Output resolution per camera
        save_to_disk: If True, also save frame to VIDEO_FRAME_DIR (legacy behavior)
    """
    global video_frame_count, video_collect_counter

    # v278 fix: Always increment counter unconditionally
    video_collect_counter += 1

    if not images:
        return None

    # Skip frames based on VIDEO_FRAME_SKIP
    if video_collect_counter % VIDEO_FRAME_SKIP != 0:
        return None

    # Resize images
    resized = {}
    for name, img_array in images.items():
        img = Image.fromarray(img_array)
        resized[name] = img.resize((resolution, resolution), Image.LANCZOS)

    if SINGLE_CAMERA_MODE:
        # Single camera: save single image (no grid)
        name = list(resized.keys())[0]
        out_img = resized[name]
    else:
        # Create 3x2 grid (3 columns, 2 rows)
        # Layout:
        # front_left | front_center | front_right
        # back       | overhead     | (empty)
        out_img = Image.new('RGB', (resolution * 3, resolution * 2))
        out_img.paste(resized["front_left"], (0, 0))
        out_img.paste(resized["front_center"], (resolution, 0))
        out_img.paste(resized["front_right"], (resolution * 2, 0))
        out_img.paste(resized["back"], (0, resolution))
        out_img.paste(resized["overhead"], (resolution, resolution))
        # Bottom-right slot left empty (black)

    # Optional legacy frame save for ffmpeg pipeline.
    if save_to_disk and args.save_video:
        # H209: PNG -> JPEG for I/O performance.
        os.makedirs(VIDEO_FRAME_DIR, exist_ok=True)
        out_img.save(os.path.join(VIDEO_FRAME_DIR, f"frame_{video_frame_count:06d}.jpg"), quality=85)
    video_frame_count += 1
    # v24.85: Frame-to-log synchronization for later video/log alignment
    if phase is not None and step is not None:
        print(f"[FRAME_SYNC] phase={phase} step={step} video_frame={video_frame_count-1} ts={datetime.utcnow().isoformat()}Z")
    return out_img


class DemoDataCollector:
    """Collects expert demonstration data during phase-based manipulation."""

    def __init__(self, scene, sim, output_dir: str, image_size: int = 256, jpeg_quality: int = 85):
        self.scene = scene
        self.sim = sim
        self.output_dir = output_dir
        self.image_size = image_size
        self.jpeg_quality = jpeg_quality
        self.device = scene["robot_left"].device

        # Cameras used for live observation/video/API.
        if NO_CAMERAS_MODE:
            self.cameras = {}
            print("[Cameras] NO_CAMERAS_MODE — all cameras disabled")
        else:
            self.cameras = {name: scene[f"{name}_camera"] for name in CAPTURE_CAMERA_NAMES}
            print(f"[Cameras] Found {len(self.cameras)} cameras")
            # Depth enablement verification: print output keys actually produced by each camera.
            for name, cam in self.cameras.items():
                try:
                    cam.update(self.sim.get_physics_dt())
                    print(f"[CameraOutputs] {name}: {list(cam.data.output.keys())}")
                except Exception as e:
                    print(f"[CameraOutputs] {name}: failed to query output keys ({e})")

        # Store previous state for action calculation
        self.prev_joint_pos_left = None
        self.prev_joint_pos_right = None
        self.prev_gripper_left = None
        self.prev_gripper_right = None

        self.reset_buffers()

    def reset_buffers(self):
        """Reset data collection buffers."""
        self.front_left_imgs = []
        self.front_right_imgs = []
        self.back_imgs = []
        self.overhead_imgs = []
        self.proprios = []
        self.task_states = []
        self.actions = []
        self.phases = []
        self.step_count = 0

    def get_camera_images(self) -> dict:
        """Get current RGB images from all capture cameras."""
        if not self.cameras:
            return {}
        # Update cameras
        for cam in self.cameras.values():
            cam.update(self.sim.get_physics_dt())

        images = {}
        for name, cam in self.cameras.items():
            rgb = cam.data.output["rgb"][0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            images[name] = rgb.astype(np.uint8)
        return images

    def get_proprio(self) -> np.ndarray:
        """Get proprioceptive observation (34D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        left_joint_pos = robot_left.data.joint_pos[0, :7].cpu().numpy()
        right_joint_pos = robot_right.data.joint_pos[0, :7].cpu().numpy()
        left_joint_vel = robot_left.data.joint_vel[0, :7].cpu().numpy()
        right_joint_vel = robot_right.data.joint_vel[0, :7].cpu().numpy()
        left_ee_pos = robot_left.data.body_pos_w[0, 8, :].cpu().numpy()
        right_ee_pos = robot_right.data.body_pos_w[0, 8, :].cpu().numpy()

        proprio = np.concatenate([
            left_joint_pos, left_joint_vel, left_ee_pos,
            right_joint_pos, right_joint_vel, right_ee_pos,
        ])
        return proprio.astype(np.float32)

    def get_task_state(self) -> np.ndarray:
        """Get task-relevant state information (44D)."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]
        # H239: Handle case when cable is not spawned (InteractiveScene has no .get() method)
        cable = None if H239_NO_CABLE_SPAWN else self.scene["cable"]
        hook_stem = self.scene["hook_stem"]

        # Hook position
        hook_pos = hook_stem.data.root_pos_w[0].cpu().numpy()

        # H239: Use dummy cable state when cable is not spawned
        if H239_NO_CABLE_SPAWN or cable is None:
            cable_pos = np.zeros(3, dtype=np.float32)
            cable_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        else:
            # Cable root position and orientation
            cable_pos = cable.data.root_pos_w[0].cpu().numpy()
            cable_quat = cable.data.root_quat_w[0].cpu().numpy()

            # Handle NaN values from unstable physics
            if np.any(np.isnan(cable_pos)) or np.any(np.isnan(cable_quat)):
                cable_pos = np.zeros(3, dtype=np.float32)
                cable_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

        # Compute virtual cable segment positions (10 segments x 3D = 30D)
        segment_positions = self._compute_cable_segments(cable_pos, cable_quat)

        # EE positions
        left_ee_pos = robot_left.data.body_pos_w[0, 8, :].cpu().numpy()
        right_ee_pos = robot_right.data.body_pos_w[0, 8, :].cpu().numpy()

        # Distances
        cable_center = cable_pos
        cable_hook_dist = np.linalg.norm(cable_center - hook_pos)
        left_ee_cable_dist = np.linalg.norm(left_ee_pos - cable_center)
        right_ee_cable_dist = np.linalg.norm(right_ee_pos - cable_center)
        left_ee_hook_dist = np.linalg.norm(left_ee_pos - hook_pos)
        right_ee_hook_dist = np.linalg.norm(right_ee_pos - hook_pos)

        task_state = np.concatenate([
            segment_positions.flatten(),  # 30D
            hook_pos,  # 3D
            left_ee_pos,  # 3D
            right_ee_pos,  # 3D
            [cable_hook_dist, left_ee_cable_dist, right_ee_cable_dist,
             left_ee_hook_dist, right_ee_hook_dist],  # 5D
        ])

        # Final NaN check
        task_state = np.nan_to_num(task_state, nan=0.0, posinf=10.0, neginf=-10.0)
        return task_state.astype(np.float32)

    def _compute_cable_segments(self, cable_pos: np.ndarray, cable_quat: np.ndarray) -> np.ndarray:
        """Compute virtual cable segment positions (10 segments)."""
        num_segments = 10
        cable_length = 0.5  # Approximate cable length

        # Convert quaternion to direction vector (local X axis)
        w, x, y, z = cable_quat
        R00 = 1 - 2 * (y * y + z * z)
        R10 = 2 * (x * y + z * w)
        R20 = 2 * (x * z - y * w)
        local_x = np.array([R00, R10, R20])

        # Compute segment positions along cable
        segment_offsets = np.linspace(-cable_length / 2, cable_length / 2, num_segments)
        segment_positions = cable_pos + segment_offsets[:, np.newaxis] * local_x
        return segment_positions

    def compute_action(self, gripper_left: float, gripper_right: float) -> np.ndarray:
        """Compute action from joint position changes."""
        robot_left = self.scene["robot_left"]
        robot_right = self.scene["robot_right"]

        curr_joint_pos_left = robot_left.data.joint_pos[0, :7].cpu().numpy()
        curr_joint_pos_right = robot_right.data.joint_pos[0, :7].cpu().numpy()

        if self.prev_joint_pos_left is None:
            # First step: zero action
            action = np.zeros(ACTION_DIM, dtype=np.float32)
        else:
            # Compute delta
            delta_left = curr_joint_pos_left - self.prev_joint_pos_left
            delta_right = curr_joint_pos_right - self.prev_joint_pos_right
            gripper_delta_left = gripper_left - self.prev_gripper_left
            gripper_delta_right = gripper_right - self.prev_gripper_right

            action = np.concatenate([
                delta_left,  # 7D
                [gripper_delta_left, gripper_delta_left],  # 2D (both fingers)
                delta_right,  # 7D
                [gripper_delta_right, gripper_delta_right],  # 2D
            ]).astype(np.float32)

        # Update previous state
        self.prev_joint_pos_left = curr_joint_pos_left.copy()
        self.prev_joint_pos_right = curr_joint_pos_right.copy()
        self.prev_gripper_left = gripper_left
        self.prev_gripper_right = gripper_right

        return action

    def collect_step(self, phase: int, gripper_left: float, gripper_right: float):
        """Collect one step of demonstration data.

        Args:
            phase: Current phase number
            gripper_left: Left gripper position
            gripper_right: Right gripper position
        """
        # Get observations
        images = self.get_camera_images()
        proprio = self.get_proprio()
        task_state = self.get_task_state()
        action = self.compute_action(gripper_left, gripper_right)

        # Store data (compressed images — only for available cameras)
        if 'front_left' in images:
            self.front_left_imgs.append(compress_image_jpeg(images['front_left'], self.jpeg_quality))
        if 'front_right' in images:
            self.front_right_imgs.append(compress_image_jpeg(images['front_right'], self.jpeg_quality))
        if 'back' in images:
            self.back_imgs.append(compress_image_jpeg(images['back'], self.jpeg_quality))
        if 'overhead' in images:
            self.overhead_imgs.append(compress_image_jpeg(images['overhead'], self.jpeg_quality))
        self.proprios.append(proprio)
        self.task_states.append(task_state)
        self.actions.append(action)
        self.phases.append(phase)
        self.step_count += 1

        # Save video frame (respects VIDEO_FRAME_SKIP)
        # Returns PIL image; pass save_to_disk=True only when legacy ffmpeg frame dump is needed.
        save_video_frame(images, phase=phase, step=self.step_count, save_to_disk=args.save_video)

    def save_cycle(self, cycle_idx: int):
        """Save collected cycle data to HDF5 file."""
        filename = os.path.join(self.output_dir, f"demo_cycle_{cycle_idx:04d}.h5")
        print(f"[Save] Saving {len(self.proprios)} steps to {filename}")

        with h5py.File(filename, 'w') as f:
            # Images (variable length JPEG bytes, only for available cameras)
            dt = h5py.special_dtype(vlen=np.uint8)

            cam_data = [
                ('front_left_img', self.front_left_imgs),
                ('front_right_img', self.front_right_imgs),
                ('back_img', self.back_imgs),
                ('overhead_img', self.overhead_imgs),
            ]
            for ds_name, img_list in cam_data:
                if img_list:
                    n_imgs = len(img_list)
                    ds = f.create_dataset(ds_name, shape=(n_imgs,), dtype=dt)
                    for i in range(n_imgs):
                        ds[i] = np.frombuffer(img_list[i], dtype=np.uint8)

            # State data
            f.create_dataset('proprio', data=np.array(self.proprios), dtype=np.float32)
            f.create_dataset('task_state', data=np.array(self.task_states), dtype=np.float32)
            f.create_dataset('action', data=np.array(self.actions), dtype=np.float32)
            f.create_dataset('phase', data=np.array(self.phases), dtype=np.int32)

            # Metadata
            f.attrs['num_steps'] = len(self.proprios)
            f.attrs['num_cameras'] = len(STORED_CAMERA_NAMES)
            f.attrs['camera_names'] = STORED_CAMERA_NAMES if STORED_CAMERA_NAMES else ["front_center"]
            f.attrs['proprio_dim'] = PROPRIO_DIM
            f.attrs['task_state_dim'] = TASK_STATE_DIM
            f.attrs['action_dim'] = ACTION_DIM
            f.attrs['cycle_idx'] = cycle_idx
            f.attrs['timestamp'] = datetime.now().isoformat()
            f.attrs['success'] = True

        print(f"[Save] Done: {len(self.proprios)} steps saved")
        self.reset_buffers()

    def save_partial_cycle(self, cycle_idx: int, failure_reason: str = "unknown"):
        """Save partial cycle data on failure (for debugging/video analysis).

        Args:
            cycle_idx: Cycle index
            failure_reason: Description of why the cycle failed
        """
        if len(self.proprios) == 0:
            print(f"[Save] No data to save for partial cycle {cycle_idx}")
            return None

        filename = os.path.join(self.output_dir, f"demo_cycle_{cycle_idx:04d}_partial.h5")
        print(f"[Save] Saving PARTIAL data ({len(self.proprios)} steps) to {filename}")
        print(f"[Save] Failure reason: {failure_reason}")

        with h5py.File(filename, 'w') as f:
            # Images (variable length JPEG bytes, only for available cameras)
            dt = h5py.special_dtype(vlen=np.uint8)

            cam_data = [
                ('front_left_img', self.front_left_imgs),
                ('front_right_img', self.front_right_imgs),
                ('back_img', self.back_imgs),
                ('overhead_img', self.overhead_imgs),
            ]
            for ds_name, img_list in cam_data:
                if img_list:
                    n_imgs = len(img_list)
                    ds = f.create_dataset(ds_name, shape=(n_imgs,), dtype=dt)
                    for i in range(n_imgs):
                        ds[i] = np.frombuffer(img_list[i], dtype=np.uint8)

            # State data
            f.create_dataset('proprio', data=np.array(self.proprios), dtype=np.float32)
            f.create_dataset('task_state', data=np.array(self.task_states), dtype=np.float32)
            f.create_dataset('action', data=np.array(self.actions), dtype=np.float32)
            f.create_dataset('phase', data=np.array(self.phases), dtype=np.int32)

            # Metadata (marked as partial/failed)
            f.attrs['num_steps'] = len(self.proprios)
            f.attrs['num_cameras'] = len(STORED_CAMERA_NAMES) if STORED_CAMERA_NAMES else 1
            f.attrs['camera_names'] = STORED_CAMERA_NAMES if STORED_CAMERA_NAMES else ["front_center"]
            f.attrs['proprio_dim'] = PROPRIO_DIM
            f.attrs['task_state_dim'] = TASK_STATE_DIM
            f.attrs['action_dim'] = ACTION_DIM
            f.attrs['cycle_idx'] = cycle_idx
            f.attrs['timestamp'] = datetime.now().isoformat()
            f.attrs['success'] = False  # Mark as failed
            f.attrs['partial'] = True   # Mark as partial data
            f.attrs['failure_reason'] = failure_reason
            # Record last phase for debugging
            if len(self.phases) > 0:
                f.attrs['last_phase'] = int(self.phases[-1])

        print(f"[Save] Partial save complete: {len(self.proprios)} steps")
        self.reset_buffers()
        return filename


# Setup simulation
sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, render_interval=2)  # H140: Increased physics resolution for solver stability
sim = sim_utils.SimulationContext(sim_cfg)


@configclass
class TestSceneCfg(DualArmSceneCfg):
    # H197: Fixed filter pattern - use Cable root, not Cable/* (which matches 39 segments)
    # See LL-2026-01-25-CFG-001 for PhysX tensors filter pattern mismatch issue
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.1, history_length=1, track_air_time=False,  # H208: 0.0→0.1 reduce PhysX query freq
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"], debug_vis=False,  # H197: /Cable not /Cable/.*
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.1, history_length=1, track_air_time=False,  # H208: 0.0→0.1 reduce PhysX query freq
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"], debug_vis=False,  # H197: /Cable not /Cable/.*
    )


@configclass
class TestSceneCfgNoCable(DualArmSceneCfg):
    """H239: Scene configuration WITHOUT cable for PhysX isolation test.

    This completely removes the cable from the scene to test if cable existence
    itself causes Phase 3 hang (even when teleported to Z=-10 with H160_DISABLE_CABLE).

    Evidence: EP-H239-B - 4 consecutive Phase 3 hangs (v234-v238) with cable disabled
    """
    # H239: Set cable to None to prevent spawning
    cable = None

    # Contact sensors still defined but filter will match nothing (no cable in scene)
    contact_left: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
        update_period=0.1, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"], debug_vis=False,
    )
    contact_right: ContactSensorCfg = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
        update_period=0.1, history_length=1, track_air_time=False,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable"], debug_vis=False,
    )


# H239: Select scene config based on H239_NO_CABLE_SPAWN flag
if H239_NO_CABLE_SPAWN:
    print("\n" + "="*70)
    print("[H239] NO CABLE SPAWN MODE - Cable completely removed from scene")
    print("       Purpose: Isolate PhysX/cable interaction for Phase 3 hang diagnosis")
    print("="*70 + "\n")
    scene_cfg = TestSceneCfgNoCable(num_envs=1, env_spacing=2.0)
else:
    scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)

# Diagnostic: Remove ALL cameras to isolate rendering as crash root cause
if NO_CAMERAS_MODE:
    scene_cfg.front_left_camera = None
    scene_cfg.front_right_camera = None
    scene_cfg.front_center_camera = None
    scene_cfg.back_camera = None
    scene_cfg.overhead_camera = None
    print("[NO_CAMERAS] ALL cameras removed from scene — rendering isolation test")
# LL-20260320-DIAG-001: Remove 4 cameras to prevent non-deterministic C++ crash
elif SINGLE_CAMERA_MODE:
    scene_cfg.front_left_camera = None
    scene_cfg.front_right_camera = None
    scene_cfg.back_camera = None
    scene_cfg.overhead_camera = None
    print("[SINGLE_CAMERA] Removed 4 cameras from scene, keeping front_center only")

scene = InteractiveScene(scene_cfg)
sim.reset()
scene.reset()

robot_left = scene["robot_left"]
robot_right = scene["robot_right"]
# H239: Cable is None when H239_NO_CABLE_SPAWN=True (cable not in scene)
cable = None if H239_NO_CABLE_SPAWN else scene["cable"]
device = robot_left.device

# H121: Explicitly apply init_state joint positions after scene.reset()
# scene.reset() does NOT write joint states to simulation - it only resets actuators
# We must manually call write_joint_state_to_sim() to apply default_joint_pos
print("[H121] Applying initial joint positions from ArticulationCfg.init_state...")
robot_left.write_joint_state_to_sim(
    robot_left.data.default_joint_pos,
    robot_left.data.default_joint_vel
)
robot_right.write_joint_state_to_sim(
    robot_right.data.default_joint_pos,
    robot_right.data.default_joint_vel
)
# Also set position targets for PD control to match
robot_left.set_joint_position_target(robot_left.data.default_joint_pos)
robot_right.set_joint_position_target(robot_right.data.default_joint_pos)
# Step simulation to apply the state
sim.step()
scene.update(sim.get_physics_dt())

# Store initial cable state for reset
# H239: Skip when cable is not spawned
if H239_NO_CABLE_SPAWN:
    initial_cable_root_state = None
    initial_cable_body_state = None
    initial_cable_joint_pos = None
    initial_cable_joint_vel = None
    cable_root_body_idx = None
    left_end_idx = None
    right_end_idx = None
    print("[H239] Cable state initialization SKIPPED (no cable in scene)")
else:
    initial_cable_root_state = cable.data.root_state_w.clone()

# H160: Teleport cable away for manipulability test
# H239: Skip teleport when cable is not spawned (already absent)
if H239_NO_CABLE_SPAWN:
    print("[H239] Cable teleport SKIPPED (no cable in scene)")
elif H160_DISABLE_CABLE:
    print("\n" + "="*70)
    print("[H160] CABLE DISABLED FOR MANIPULABILITY TEST")
    print("="*70)
    # Move cable to Z=-10 (far below scene)
    disabled_cable_state = initial_cable_root_state.clone()
    disabled_cable_state[0, 2] = -10.0  # Z = -10m
    cable.write_root_state_to_sim(disabled_cable_state)
    sim.step()
    scene.update(sim.get_physics_dt())
    print(f"  Cable teleported to Z=-10m")
    print("="*70 + "\n")

# Apply high friction
def set_friction(asset, sf, df):
    materials = asset.root_physx_view.get_material_properties()
    materials[..., 0] = sf
    materials[..., 1] = df
    asset.root_physx_view.set_material_properties(materials, torch.arange(1, device="cpu"))

set_friction(robot_left, HIGH_FRICTION, HIGH_FRICTION)
set_friction(robot_right, HIGH_FRICTION, HIGH_FRICTION)
# H239: Skip cable friction when cable is not spawned
if not H239_NO_CABLE_SPAWN:
    set_friction(cable, HIGH_FRICTION, HIGH_FRICTION)

# Setup Diff IK
# H233: Separate lambda_val for Left arm (0.002) vs Right arm (0.005)
# Reference: LL-2026-01-30-IK-005 (H232: λ=0.003→11.9mm, H233: λ=0.002→8.9mm predicted)
diff_ik_cfg_left = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": H233_LEFT_LAMBDA_VAL},  # H233: Left arm specific (0.002)
)
diff_ik_cfg_right = DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.005},  # H154: Right arm unchanged (0.005)
)
diff_ik_left = DifferentialIKController(diff_ik_cfg_left, num_envs=1, device=device)
diff_ik_right = DifferentialIKController(diff_ik_cfg_right, num_envs=1, device=device)

jacobian_body_left = robot_left.find_bodies("panda_hand")[0][0]
jacobian_body_right = robot_right.find_bodies("panda_hand")[0][0]

# Create data collector
collector = DemoDataCollector(scene, sim, args.output_dir, args.image_size, args.jpeg_quality)

# ============================================================
# INITIAL CABLE STABILIZATION (Critical for NaN prevention)
# ============================================================
# H239: Skip entirely when cable is not spawned
if H239_NO_CABLE_SPAWN:
    print("\n[Init] Skipping cable stabilization (H239: no cable spawned)")
elif H160_DISABLE_CABLE:
    print("\n[Init] Skipping cable stabilization (H160: cable disabled)")
else:
    _stab_max_steps = CYCLE_RESET_STABILIZATION_STEPS * 2
    _stab_max_seconds = 240  # B0: 4 minute timeout (was: 180, adjusted for damping=80)
    _stab_start = _time.time()
    print(f"\n[Init] Stabilizing cable physics... (max_steps={_stab_max_steps}, max_seconds={_stab_max_seconds})")
    cable.write_root_state_to_sim(initial_cable_root_state)
    for _stab_step in range(_stab_max_steps):  # Double stabilization on first init
        sim.step()
        scene.update(sim.get_physics_dt())
        # H198: Heartbeat every 100 steps
        if _stab_step % 100 == 0:
            _stab_elapsed = _time.time() - _stab_start
            print(f"  [H198 heartbeat] stabilize step={_stab_step}/{_stab_max_steps}, elapsed={_stab_elapsed:.1f}s")
            sys.stdout.flush()
            # H198: Wall-time timeout guard
            if _stab_elapsed >= _stab_max_seconds:
                print(f"  [H198 HANG_TIMEOUT] stabilize max_seconds={_stab_max_seconds} exceeded at step={_stab_step}")
                raise TimeoutError(f"stabilize_cable: wall-time {_stab_elapsed:.1f}s >= {_stab_max_seconds}s")
    _stab_elapsed = _time.time() - _stab_start
    print(f"  [H198] Stabilization loop completed: {_stab_max_steps} steps in {_stab_elapsed:.1f}s")

    # Verify cable state is valid
    cable_pos_init = cable.data.root_pos_w[0].cpu().numpy()
    if np.any(np.isnan(cable_pos_init)):
        print(f"  [ERROR] Cable position is NaN after initialization!")
        print(f"  Cable pos: {cable_pos_init}")
    else:
        print(f"  [OK] Cable position: {cable_pos_init}")
    print("[Init] Cable stabilization complete")

# H121+H149: Re-apply robot joint positions after cable stabilization with convergence check
# Cable stabilization loop may have caused joint drift
print("[H121] Re-applying robot joint positions after cable stabilization...")

# Use default_joint_pos (matches ArticulationCfg init_state) for more reliable reset
# Then converge using position control
robot_left.write_joint_state_to_sim(
    robot_left.data.default_joint_pos,
    robot_left.data.default_joint_vel
)
robot_right.write_joint_state_to_sim(
    robot_right.data.default_joint_pos,
    robot_right.data.default_joint_vel
)
robot_left.set_joint_position_target(robot_left.data.default_joint_pos)
robot_right.set_joint_position_target(robot_right.data.default_joint_pos)

# Target positions from task_config for verification
target_joints_l = torch.tensor(LEFT_ARM_INIT_JOINTS, device=device, dtype=torch.float32)
target_joints_r = torch.tensor(RIGHT_ARM_INIT_JOINTS, device=device, dtype=torch.float32)

# H149: Convergence verification loop (max 200 steps, threshold 0.02 rad = ~1.1°)
CONVERGENCE_THRESHOLD_RAD = 0.02
MAX_CONVERGENCE_STEPS = 200
converged = False
initial_error_l = None
initial_error_r = None

for conv_step in range(MAX_CONVERGENCE_STEPS):
    sim.step()
    scene.update(sim.get_physics_dt())

    actual_l = robot_left.data.joint_pos[0, :7]
    actual_r = robot_right.data.joint_pos[0, :7]
    error_l = (target_joints_l - actual_l).abs().max().item()
    error_r = (target_joints_r - actual_r).abs().max().item()
    max_error = max(error_l, error_r)

    if initial_error_l is None:
        initial_error_l = error_l
        initial_error_r = error_r
        print(f"  [H149] H121 initial error: L={np.degrees(initial_error_l):.2f}° R={np.degrees(initial_error_r):.2f}°")

    if conv_step % 50 == 0:
        print(f"  [H149] H121 step {conv_step}: L={np.degrees(error_l):.2f}° R={np.degrees(error_r):.2f}°")

    if max_error <= CONVERGENCE_THRESHOLD_RAD:
        print(f"  [H149] H121 converged at step {conv_step}: max_error={np.degrees(max_error):.2f}°")
        converged = True
        break

    # Keep commanding target position using default_joint_pos
    robot_left.set_joint_position_target(robot_left.data.default_joint_pos)
    robot_right.set_joint_position_target(robot_right.data.default_joint_pos)

if not converged:
    actual_l = robot_left.data.joint_pos[0, :7]
    actual_r = robot_right.data.joint_pos[0, :7]
    error_l = (target_joints_l - actual_l).abs().max().item()
    error_r = (target_joints_r - actual_r).abs().max().item()
    print(f"  [H149 WARNING] H121 did not converge after {MAX_CONVERGENCE_STEPS} steps: L={np.degrees(error_l):.2f}° R={np.degrees(error_r):.2f}°")

# 2026-01-06: Save state of all segments (root_state_w only covers 1 segment, incomplete)
# H239: Skip when cable is not spawned (variables already initialized to None above)
if not H239_NO_CABLE_SPAWN:
    initial_cable_body_state = cable.data.body_state_w.clone()  # [1, 20, 13] all segments
    initial_cable_joint_pos = cable.data.joint_pos.clone()
    initial_cable_joint_vel = cable.data.joint_vel.clone()
initial_robot_left_state = robot_left.data.root_state_w.clone()
initial_robot_right_state = robot_right.data.root_state_w.clone()
initial_joint_pos_left = robot_left.data.joint_pos.clone()
initial_joint_vel_left = robot_left.data.joint_vel.clone()
initial_joint_pos_right = robot_right.data.joint_pos.clone()
initial_joint_vel_right = robot_right.data.joint_vel.clone()

# Debug: Show actual joint positions at simulation start
print("  [Debug] Initial joint positions (from simulation):")
print(f"    Left:  {initial_joint_pos_left[0, :7].cpu().numpy()}")
print(f"    Right: {initial_joint_pos_right[0, :7].cpu().numpy()}")
print("  [Debug] Expected joint positions (from task_config):")
print(f"    Left:  {LEFT_ARM_INIT_JOINTS}")
print(f"    Right: {RIGHT_ARM_INIT_JOINTS}")

# H239: Skip cable body identification when cable is not spawned
if H239_NO_CABLE_SPAWN:
    print("  [H239] Cable body identification SKIPPED (no cable in scene)")
else:
    # 2026-01-07: Identify cable root body index by comparing root_pos_w with body_state_w positions
    # This is critical for correct reset - write_root_state_to_sim expects root body state
    cable_root_pos = cable.data.root_pos_w[0]  # [3]
    cable_body_positions = initial_cable_body_state[0, :, :3]  # [20, 3]
    # H197 debug: Print shape before accessing indices
    print(f"  [Debug] initial_cable_body_state shape: {initial_cable_body_state.shape}")
    print(f"  [Debug] cable_body_positions shape: {cable_body_positions.shape}")
    sys.stdout.flush()
    distances = torch.norm(cable_body_positions - cable_root_pos.unsqueeze(0), dim=1)
    cable_root_body_idx = distances.argmin().item()
    print(f"  [OK] Cable root body identified: seg_{cable_root_body_idx}")
    print(f"       Root position: {cable_root_pos.cpu().numpy()}")
    print(f"       seg_0 position:  {cable_body_positions[0].cpu().numpy()}")
    # H240: Dynamic segment count - use actual cable shape
    num_segs = cable_body_positions.shape[0]
    mid_idx = num_segs // 2
    last_idx = num_segs - 1
    print(f"       seg_{mid_idx} (mid) position: {cable_body_positions[mid_idx].cpu().numpy()}")
    print(f"       seg_{last_idx} (last) position: {cable_body_positions[last_idx].cpu().numpy()}")
    sys.stdout.flush()
    print(f"  [Debug] Cable segments: {num_segs} (H240 v16_halfseg: 10 segments)")

    # 2026-01-07: Check body_names order for debugging
    print(f"  [Debug] Cable body_names (first 5): {cable.body_names[:5]}")
    print(f"  [Debug] Cable body_names (last 5): {cable.body_names[-5:]}")
    # Find actual left end (most negative Y) and right end (most positive Y)
    # 2026-01-07: body_names order is NOT numerical! e.g., ['seg_9', 'seg_8', ...]
    # We need to find correct indices for actual endpoints
    y_positions = cable_body_positions[:, 1]
    left_end_idx = y_positions.argmin().item()  # Index of leftmost segment (most negative Y)
    right_end_idx = y_positions.argmax().item()  # Index of rightmost segment (most positive Y)
    print(f"  [Debug] Actual left end: idx={left_end_idx} ({cable.body_names[left_end_idx]}), Y={y_positions[left_end_idx].item():.4f}")
    print(f"  [Debug] Actual right end: idx={right_end_idx} ({cable.body_names[right_end_idx]}), Y={y_positions[right_end_idx].item():.4f}")

    print(f"  [OK] Initial states saved after stabilization")
    print(f"  Cable body_state shape: {initial_cable_body_state.shape}")  # Expected: [1, 20, 13]
    print(f"  Cable joint_pos shape: {initial_cable_joint_pos.shape}")


def set_robot_joints(robot, arm_joints, gripper_val):
    target = robot.data.joint_pos[0].unsqueeze(0).clone()
    target[0, :7] = torch.tensor(arm_joints, device=device)
    target[0, -2:] = gripper_val
    robot.set_joint_position_target(target)
    robot.write_data_to_sim()


def teleport_robot(robot, arm_joints, gripper_val):
    state = robot.data.joint_pos[0].unsqueeze(0).clone()
    state[0, :7] = torch.tensor(arm_joints, device=device)
    state[0, -2:] = gripper_val
    robot.write_joint_state_to_sim(state, robot.data.joint_vel[0].unsqueeze(0))


def gradual_move_both_robots(target_left, target_right, gripper_val, max_change_deg=30.0, steps_per_segment=10,
                              convergence_threshold_rad=0.02, max_convergence_steps=200):
    """H120+H149: Gradually move both robots simultaneously to target positions with convergence check.

    Instead of teleporting, split large motions into multiple small steps
    to avoid physical simulation instability.

    IMPORTANT: Both robots must be moved simultaneously to avoid one robot
    drifting while the other is being positioned.

    H149: Added convergence verification to ensure target joint angles are reached.
    H149-FIX: Added EE position verification using FK to detect tracking errors.

    Args:
        target_left: Target joint angles for left arm (7 values)
        target_right: Target joint angles for right arm (7 values)
        gripper_val: Gripper position value
        max_change_deg: Maximum allowed change per segment (default 30°)
        steps_per_segment: Number of simulation steps per segment
        convergence_threshold_rad: Max allowed joint error (default 0.01 rad = 0.57°)
        max_convergence_steps: Max steps for convergence loop (default 100)
    """
    current_joints_l = robot_left.data.joint_pos[0, :7].clone()
    current_joints_r = robot_right.data.joint_pos[0, :7].clone()
    target_joints_l = torch.tensor(target_left, device=device, dtype=torch.float32)
    target_joints_r = torch.tensor(target_right, device=device, dtype=torch.float32)

    delta_l = target_joints_l - current_joints_l
    delta_r = target_joints_r - current_joints_r
    max_delta_deg_l = np.degrees(delta_l.abs().max().item())
    max_delta_deg_r = np.degrees(delta_r.abs().max().item())
    max_delta_deg = max(max_delta_deg_l, max_delta_deg_r)

    if max_delta_deg <= max_change_deg:
        num_segments = 1
    else:
        num_segments = int(np.ceil(max_delta_deg / max_change_deg))

    print(f"  [H120] gradual_move_both: max_delta L={max_delta_deg_l:.1f}° R={max_delta_deg_r:.1f}° -> {num_segments} segments")

    for seg in range(num_segments):
        alpha = (seg + 1) / num_segments
        interp_l = current_joints_l + alpha * delta_l
        interp_r = current_joints_r + alpha * delta_r

        # Move both robots gradually to interpolated positions
        for step in range(steps_per_segment):
            target_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
            target_l[0, :7] = interp_l
            target_l[0, -2:] = gripper_val
            robot_left.set_joint_position_target(target_l)
            robot_left.write_data_to_sim()

            target_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
            target_r[0, :7] = interp_r
            target_r[0, -2:] = gripper_val
            robot_right.set_joint_position_target(target_r)
            robot_right.write_data_to_sim()

            sim.step()
            scene.update(sim.get_physics_dt())

    # H149: Convergence verification loop - ensure target joints are reached
    for conv_step in range(max_convergence_steps):
        actual_l = robot_left.data.joint_pos[0, :7]
        actual_r = robot_right.data.joint_pos[0, :7]
        error_l = (target_joints_l - actual_l).abs().max().item()
        error_r = (target_joints_r - actual_r).abs().max().item()
        max_error = max(error_l, error_r)

        if max_error <= convergence_threshold_rad:
            print(f"  [H149] Converged at step {conv_step}: max_error={np.degrees(max_error):.2f}°")
            break

        # Keep commanding target position
        target_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        target_l[0, :7] = target_joints_l
        target_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(target_l)
        robot_left.write_data_to_sim()

        target_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        target_r[0, :7] = target_joints_r
        target_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(target_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())
    else:
        # Did not converge within max steps
        actual_l = robot_left.data.joint_pos[0, :7]
        actual_r = robot_right.data.joint_pos[0, :7]
        error_l = (target_joints_l - actual_l).abs().max().item()
        error_r = (target_joints_r - actual_r).abs().max().item()
        print(f"  [H149 WARNING] Did not converge after {max_convergence_steps} steps: L={np.degrees(error_l):.2f}° R={np.degrees(error_r):.2f}°")

    # H149-FIX: EE position verification after convergence
    # Log actual EE position vs target to detect systematic tracking errors
    actual_ee_l = robot_left.data.body_pos_w[0, jacobian_body_left]
    actual_ee_r = robot_right.data.body_pos_w[0, jacobian_body_right]
    print(f"  [H149-FIX] EE position after convergence:")
    print(f"    Left  (panda_hand): ({actual_ee_l[0].item():.4f}, {actual_ee_l[1].item():.4f}, {actual_ee_l[2].item():.4f})")
    print(f"    Right (panda_hand): ({actual_ee_r[0].item():.4f}, {actual_ee_r[1].item():.4f}, {actual_ee_r[2].item():.4f})")
    # H149-FIX: Also log actual joint angles for FK verification
    final_joints_l = robot_left.data.joint_pos[0, :7]
    final_joints_r = robot_right.data.joint_pos[0, :7]
    print(f"  [H149-FIX] Final joint angles (deg):")
    print(f"    Left:  {[f'{np.degrees(j.item()):+.1f}' for j in final_joints_l]}")
    print(f"    Right: {[f'{np.degrees(j.item()):+.1f}' for j in final_joints_r]}")


def check_cable_nan_detailed(cable_obj):
    """Check each segment for NaN and return first NaN segment info."""
    # H239: Skip check when cable is not spawned
    if H239_NO_CABLE_SPAWN:
        dummy_pos = torch.zeros(20, 3)
        dummy_vel = torch.zeros(20, 3)
        return -1, dummy_pos.cpu().numpy(), dummy_vel.cpu().numpy()
    # H160: Skip check when cable is disabled
    if H160_DISABLE_CABLE:
        # Return dummy values indicating no NaN
        dummy_pos = torch.zeros(20, 3)
        dummy_vel = torch.zeros(20, 3)
        return -1, dummy_pos.cpu().numpy(), dummy_vel.cpu().numpy()

    num_segs = cable_obj.data.body_pos_w.shape[1]
    pos = cable_obj.data.body_pos_w[0]  # (num_segments, 3)
    vel = cable_obj.data.body_lin_vel_w[0]  # (num_segments, 3)

    for i in range(num_segs):
        if torch.any(torch.isnan(pos[i])) or torch.any(torch.isnan(vel[i])):
            return i, pos.cpu().numpy(), vel.cpu().numpy()
    return -1, pos.cpu().numpy(), vel.cpu().numpy()


def run_arc_rotation_with_collection(
    start_pos_left, start_pos_right, start_quat_left, start_quat_right,
    target_pos_left, target_pos_right, num_steps, gripper_val, phase: int
):
    """
    Rotate both grippers along an arc to maintain constant gripper distance.

    The rotation is done around the midpoint of the cable (center between grippers),
    maintaining the initial gripper distance throughout the rotation.
    """
    diff_ik_left.reset()
    diff_ik_right.reset()

    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # Get initial positions
    start_l = start_pos_left[0].cpu().numpy()  # [x, y, z]
    start_r = start_pos_right[0].cpu().numpy()
    target_l = target_pos_left[0].cpu().numpy()
    target_r = target_pos_right[0].cpu().numpy()

    # Calculate center point (midpoint between left and right grippers)
    start_center = (start_l + start_r) / 2  # [x, y, z]
    target_center = (target_l + target_r) / 2

    # Calculate initial radius from center to each gripper
    start_radius_l = np.linalg.norm(start_l[:2] - start_center[:2])  # XY distance
    start_radius_r = np.linalg.norm(start_r[:2] - start_center[:2])
    target_radius_l = np.linalg.norm(target_l[:2] - target_center[:2])
    target_radius_r = np.linalg.norm(target_r[:2] - target_center[:2])

    # Calculate initial and target angles (in XY plane, relative to center)
    start_angle_l = np.arctan2(start_l[1] - start_center[1], start_l[0] - start_center[0])
    start_angle_r = np.arctan2(start_r[1] - start_center[1], start_r[0] - start_center[0])
    target_angle_l = np.arctan2(target_l[1] - target_center[1], target_l[0] - target_center[0])
    target_angle_r = np.arctan2(target_r[1] - target_center[1], target_r[0] - target_center[0])

    # Debug info
    gripper_dist = np.linalg.norm(start_l - start_r)
    print(f"  Arc rotation: gripper_dist={gripper_dist:.3f}m")
    print(f"  Start angles: L={np.degrees(start_angle_l):.1f}°, R={np.degrees(start_angle_r):.1f}°")
    print(f"  Target angles: L={np.degrees(target_angle_l):.1f}°, R={np.degrees(target_angle_r):.1f}°")

    # NaN detection state
    last_good_pos = None
    last_good_vel = None
    nan_detected_step = -1

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Interpolate center position
        center = start_center + alpha * (target_center - start_center)

        # Interpolate angles and radii
        angle_l = start_angle_l + alpha * (target_angle_l - start_angle_l)
        angle_r = start_angle_r + alpha * (target_angle_r - start_angle_r)
        radius_l = start_radius_l + alpha * (target_radius_l - start_radius_l)
        radius_r = start_radius_r + alpha * (target_radius_r - start_radius_r)

        # Calculate gripper positions on arc (XY plane) + interpolated Z
        z = start_l[2] + alpha * (target_l[2] - start_l[2])

        pos_l = np.array([
            center[0] + radius_l * np.cos(angle_l),
            center[1] + radius_l * np.sin(angle_l),
            z
        ])
        pos_r = np.array([
            center[0] + radius_r * np.cos(angle_r),
            center[1] + radius_r * np.sin(angle_r),
            z
        ])

        # Convert to torch tensors
        cmd_pos_l = torch.tensor([pos_l], device=device, dtype=torch.float32)
        cmd_pos_r = torch.tensor([pos_r], device=device, dtype=torch.float32)

        cmd_l = torch.cat([cmd_pos_l, start_quat_left], dim=1)
        cmd_r = torch.cat([cmd_pos_r, start_quat_right], dim=1)

        diff_ik_left.set_command(cmd_l)
        diff_ik_right.set_command(cmd_r)

        jac_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
        jac_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

        ee_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        ee_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left]
        ee_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right]
        ee_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right]

        joint_pos_l = robot_left.data.joint_pos[:, :7]
        joint_pos_r = robot_right.data.joint_pos[:, :7]

        joint_cmd_l = diff_ik_left.compute(ee_pos_l, ee_quat_l, jac_left, joint_pos_l)
        joint_cmd_r = diff_ik_right.compute(ee_pos_r, ee_quat_r, jac_right, joint_pos_r)

        # v51: Joint delta clamping for stability (Phase 1-3)
        JOINT_DELTA_MAX = 0.02  # v53: optimal value from v51b
        delta_l = joint_cmd_l[0] - joint_pos_l[0]
        delta_r = joint_cmd_r[0] - joint_pos_r[0]
        delta_l_clamped = torch.clamp(delta_l, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        delta_r_clamped = torch.clamp(delta_r, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        joint_cmd_l_safe = joint_pos_l + delta_l_clamped.unsqueeze(0)
        joint_cmd_r_safe = joint_pos_r + delta_r_clamped.unsqueeze(0)

        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = joint_cmd_l_safe[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r_safe[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # NaN detection and progress logging
        nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
        if nan_seg >= 0 and nan_detected_step < 0:
            nan_detected_step = i
            print(f"\n{'!'*70}")
            print(f"[NaN DETECTED] Phase {phase} (arc), Step {i}/{num_steps} ({alpha*100:.1f}%)")
            print(f"First NaN segment: seg_{nan_seg}")
            print(f"{'!'*70}")
            sys.stdout.flush()
            # v24.38: Save NaN snapshot video
            save_nan_snapshot_video(i)
            if last_good_pos is not None:
                print(f"\nLast good state (step {i-1}):")
                speeds = np.linalg.norm(last_good_vel, axis=1)
                top_speed_idx = np.argsort(speeds)[-3:][::-1]
                print(f"Top 3 fastest segments:")
                for idx in top_speed_idx:
                    print(f"  seg_{idx}: speed={speeds[idx]:.4f} m/s")
                sys.stdout.flush()
        elif nan_detected_step < 0:
            last_good_pos = pos_arr.copy()
            last_good_vel = vel_arr.copy()
            # Progress logging: every 100 steps
            if i % 100 == 0 or i == num_steps - 1:
                speeds = np.linalg.norm(vel_arr, axis=1)
                z_vals = pos_arr[:, 2]
                ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
                ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
                actual_dist = torch.norm(ee_l - ee_r).item()
                print(f"  [P{phase} arc {i:4d}/{num_steps}] EE dist={actual_dist:.3f}m L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f})")
                sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def run_joint_space_motion_with_collection(target_joints_left: list, target_joints_right: list,
                                           num_steps: int, gripper_val, phase: int):
    """Run joint space interpolation motion while collecting demonstration data.

    2026-01-07: Added for Phase 4.5. Switched to joint space interpolation using
    precomputed PHASE45_*_JOINTS because Diff IK could not track the right arm.

    H119: Added 30 deg/step clamp (2026-01-12)
    - H118 only covered Diff IK, so the same protection is applied to Joint Space interpolation
    - Prevents NaN caused by abrupt joint changes during phase transitions

    H120: Adaptive step increase (2026-01-12)
    - H118/H119 were ineffective because command clamp != actual motion limit
    - Root cause fix: increase num_steps dynamically based on max joint delta
    - This ensures each step has < 30° change in target (not just command)

    Args:
        target_joints_left: Target joint angles for left arm (7 values)
        target_joints_right: Target joint angles for right arm (7 values)
        num_steps: Number of interpolation steps
        gripper_val: Gripper position value
        phase: Current phase number for logging
    """
    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # Get current joint positions
    start_joints_l = robot_left.data.joint_pos[:, :7].clone()
    start_joints_r = robot_right.data.joint_pos[:, :7].clone()

    # Convert target to tensors
    target_l = torch.tensor([target_joints_left], device=device, dtype=torch.float32)
    target_r = torch.tensor([target_joints_right], device=device, dtype=torch.float32)

    # H120: Calculate max joint delta and adjust num_steps if needed
    H120_MAX_CHANGE_DEG = 30.0
    delta_l = (target_l - start_joints_l).abs()
    delta_r = (target_r - start_joints_r).abs()
    max_delta_rad = max(delta_l.max().item(), delta_r.max().item())
    max_delta_deg = np.degrees(max_delta_rad)

    # H120: Increase num_steps so each step changes < 30°
    # Original num_steps means total motion / num_steps = delta per step
    # We want: total_delta / actual_steps < 30° → actual_steps > total_delta / 30°
    min_steps_for_30deg = int(np.ceil(max_delta_deg / H120_MAX_CHANGE_DEG))
    original_num_steps = num_steps
    if min_steps_for_30deg > num_steps:
        num_steps = min_steps_for_30deg
        print(f"  [H120] Phase {phase}: Large motion {max_delta_deg:.1f}° → steps increased {original_num_steps} → {num_steps}")
        sys.stdout.flush()

    print(f"  [Joint Space] Start joints L[0]={start_joints_l[0,0]:.3f}, R[0]={start_joints_r[0,0]:.3f}")
    print(f"  [Joint Space] Target joints L[0]={target_l[0,0]:.3f}, R[0]={target_r[0,0]:.3f}")

    # Track cable state for NaN diagnosis
    last_good_pos = None
    last_good_vel = None
    nan_detected_step = -1

    # H119: Track previous actual joint positions for 30°/step clamping
    # Initialize with current position (not None) to clamp first step
    prev_joint_l = start_joints_l.clone()
    prev_joint_r = start_joints_r.clone()
    H119_MAX_CHANGE_RAD = np.radians(30.0)  # H119: 30°/step limit

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Linear interpolation in joint space (raw target)
        interp_l = start_joints_l + alpha * (target_l - start_joints_l)
        interp_r = start_joints_r + alpha * (target_r - start_joints_r)

        # H119: 30°/step clamp based on actual previous joint positions
        delta_from_prev_l = interp_l[0] - prev_joint_l[0]
        delta_from_prev_r = interp_r[0] - prev_joint_r[0]
        # Clamp to 30°/step max change from actual previous position
        delta_h119_l = torch.clamp(delta_from_prev_l, -H119_MAX_CHANGE_RAD, H119_MAX_CHANGE_RAD)
        delta_h119_r = torch.clamp(delta_from_prev_r, -H119_MAX_CHANGE_RAD, H119_MAX_CHANGE_RAD)
        interp_l_clamped = prev_joint_l + delta_h119_l.unsqueeze(0)
        interp_r_clamped = prev_joint_r + delta_h119_r.unsqueeze(0)
        # Log if H119 clamp was applied (delta exceeded 30°)
        if (delta_from_prev_l.abs() > H119_MAX_CHANGE_RAD).any() or (delta_from_prev_r.abs() > H119_MAX_CHANGE_RAD).any():
            max_l = np.degrees(delta_from_prev_l.abs().max().item())
            max_r = np.degrees(delta_from_prev_r.abs().max().item())
            print(f"  [H119 Joint Space] Phase {phase} step {i}: clamped large delta L={max_l:.1f}° R={max_r:.1f}°")
            sys.stdout.flush()

        # Apply clamped joint positions
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = interp_l_clamped[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = interp_r_clamped[0]  # H119: Use clamped value
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # H119: Update prev_joint with actual positions after sim step
        prev_joint_l = robot_left.data.joint_pos[:, :7].clone()
        prev_joint_r = robot_right.data.joint_pos[:, :7].clone()

        # NaN detection and progress logging
        nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
        if nan_seg >= 0 and nan_detected_step < 0:
            nan_detected_step = i
            print(f"\n{'!'*70}")
            print(f"[NaN DETECTED] Phase {phase} (Joint Space), Step {i}/{num_steps} ({alpha*100:.1f}%)")
            print(f"First NaN segment: seg_{nan_seg}")
            print(f"{'!'*70}")
            sys.stdout.flush()
            # v24.38: Save NaN snapshot video
            save_nan_snapshot_video(i)
            if last_good_pos is not None:
                print(f"\nLast good state (step {i-1}):")
                print(f"{'Seg':>4} | {'X':>8} {'Y':>8} {'Z':>8} | {'Speed':>8}")
                print("-" * 50)
                for j in range(len(last_good_pos)):
                    speed = np.linalg.norm(last_good_vel[j])
                    print(f"{j:4d} | {last_good_pos[j,0]:8.4f} {last_good_pos[j,1]:8.4f} {last_good_pos[j,2]:8.4f} | {speed:8.4f}")
                sys.stdout.flush()
        else:
            last_good_pos = pos_arr.copy()
            last_good_vel = vel_arr.copy()
            # Progress logging: every 100 steps
            if i % 100 == 0 or i == num_steps - 1:
                ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
                ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
                z_vals = pos_arr[:, 2]
                print(f"  [P{phase} step {i:4d}/{num_steps}] EE: L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f}) cable_Z: {z_vals.min():.3f}-{z_vals.max():.3f}")
                sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def run_diff_ik_motion_with_collection(start_pos_left, start_pos_right, start_quat_left, start_quat_right,
                                       target_pos_left, target_pos_right, num_steps, gripper_val, phase: int,
                                       skip_ramp_up: bool = False):
    """Run Diff IK motion while collecting demonstration data.

    H120 (2026-01-12): Adaptive step increase based on expected joint motion.
    - Calculate IK solution for first step target
    - If joint delta > 30°, increase num_steps proportionally
    - This ensures smooth motion without large joint jumps
    """
    diff_ik_left.reset()
    diff_ik_right.reset()

    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # H120: Estimate max joint delta by computing IK for first step target
    # This is a pre-check to adjust num_steps before the main loop
    H120_MAX_CHANGE_DEG = 30.0
    current_joint_l = robot_left.data.joint_pos[:, :7].clone()
    current_joint_r = robot_right.data.joint_pos[:, :7].clone()

    # Compute first step target position (alpha = 1/num_steps)
    alpha_first = 1.0 / num_steps
    first_pos_l = start_pos_left + alpha_first * (target_pos_left - start_pos_left)
    first_pos_r = start_pos_right + alpha_first * (target_pos_right - start_pos_right)

    # Get Jacobian and compute IK for first step
    jac_l_h120 = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
    jac_r_h120 = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]
    ee_pos_l_h120 = robot_left.data.body_pos_w[:, jacobian_body_left]
    ee_quat_l_h120 = robot_left.data.body_quat_w[:, jacobian_body_left]
    ee_pos_r_h120 = robot_right.data.body_pos_w[:, jacobian_body_right]
    ee_quat_r_h120 = robot_right.data.body_quat_w[:, jacobian_body_right]

    cmd_l_h120 = torch.cat([first_pos_l, start_quat_left], dim=1)
    cmd_r_h120 = torch.cat([first_pos_r, start_quat_right], dim=1)
    diff_ik_left.set_command(cmd_l_h120)
    diff_ik_right.set_command(cmd_r_h120)
    ik_cmd_l_h120 = diff_ik_left.compute(ee_pos_l_h120, ee_quat_l_h120, jac_l_h120, current_joint_l[:, :7])
    ik_cmd_r_h120 = diff_ik_right.compute(ee_pos_r_h120, ee_quat_r_h120, jac_r_h120, current_joint_r[:, :7])

    # Calculate expected joint delta for first step
    delta_l_h120 = (ik_cmd_l_h120 - current_joint_l).abs()
    delta_r_h120 = (ik_cmd_r_h120 - current_joint_r).abs()
    max_delta_rad_h120 = max(delta_l_h120.max().item(), delta_r_h120.max().item())
    max_delta_deg_h120 = np.degrees(max_delta_rad_h120)

    # H120: If first step joint delta > 30°, we need more steps
    # Scale up: if delta is 90°, we need 3x more steps
    original_num_steps = num_steps
    if max_delta_deg_h120 > H120_MAX_CHANGE_DEG:
        scale_factor = max_delta_deg_h120 / H120_MAX_CHANGE_DEG
        num_steps = int(np.ceil(original_num_steps * scale_factor))
        print(f"  [H120] Phase {phase}: First step delta {max_delta_deg_h120:.1f}° → steps increased {original_num_steps} → {num_steps}")
        sys.stdout.flush()

    # Reset IK controllers after pre-check
    diff_ik_left.reset()
    diff_ik_right.reset()

    # For Phase 3 (lift), track cable state for NaN diagnosis
    last_good_pos = None
    last_good_vel = None
    nan_detected_step = -1

    # H118/H119: Track previous actual joint positions for 30°/step clamping
    # H119 FIX: Initialize with current position (not None) to clamp first step
    prev_joint_l = robot_left.data.joint_pos[:, :7].clone()
    prev_joint_r = robot_right.data.joint_pos[:, :7].clone()
    H118_MAX_CHANGE_RAD = np.radians(30.0)  # H118: 30°/step limit

    # H127/H202: Phase 3 cosine ramp-up to prevent sudden velocity changes at lift start
    # Root cause: Phase 2→3 transition causes abrupt Z velocity jump, breaking cable physics
    # H202: Extended ramp-up from 100 to 200 steps (LL-2026-01-25-NAN-001)
    H127_RAMP_STEPS = H202_RAMP_STEPS  # H202: 100 → 200 steps for extended ramp-up
    h127_logged = False  # Log once per phase
    h145_logged = False  # H145: Log once at start

    # H145/H202: Get simulation timestep for velocity-based step calculation
    # H202: Reduced max EE velocity from 0.6 to 0.3 m/s for Phase 3 NaN prevention
    dt = sim.get_physics_dt()
    max_step_per_iter = H202_MAX_EE_VELOCITY * dt  # H202: 0.3 m/s * 0.00208s = 0.625mm/step (was 1.25mm)

    # H205: Phase 3 max_step override for A/B test
    if phase == 3 and H205_PHASE3_MAX_STEP_OVERRIDE:
        max_step_per_iter = H205_PHASE3_MAX_STEP_MM / 1000.0  # Convert mm to m
        print(f"  [H205] Phase 3 max_step OVERRIDE: {H205_PHASE3_MAX_STEP_MM}mm/step (A/B test)")

    for i in range(num_steps):
        # H145: Position-based interpolation (replaces time-based alpha)
        # Read actual EE positions at start of each step
        actual_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        actual_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]

        # Compute remaining distance to target
        remaining_l = target_pos_left - actual_ee_l
        remaining_r = target_pos_right - actual_ee_r

        # H127: Apply cosine ramp-up for Phase 3 (lift) to smooth velocity transition
        # H206: skip_ramp_up=True skips ramp-up (for lift steps 2+, ramp-up already applied in step 1)
        if phase == 3 and not skip_ramp_up and i < H127_RAMP_STEPS:
            # Cosine interpolation: 0 → 1 over ramp steps, slower start
            ramp_factor = 0.5 * (1 - np.cos(np.pi * i / H127_RAMP_STEPS))
            effective_max_step = max_step_per_iter * ramp_factor
            if not h127_logged:
                print(f"  [H127] Phase 3: Applying cosine ramp-up for first {H127_RAMP_STEPS} steps")
                h127_logged = True
        else:
            effective_max_step = max_step_per_iter

        if not h145_logged:
            print(f"  [H145] Phase {phase}: Position-based interpolation, max_step={max_step_per_iter*1000:.3f}mm/step")
            h145_logged = True

        # Clamp step to effective max step (velocity limit)
        step_l = torch.clamp(remaining_l, -effective_max_step, effective_max_step)
        step_r = torch.clamp(remaining_r, -effective_max_step, effective_max_step)

        # Compute new target position (actual + clamped step)
        pos_left = actual_ee_l + step_l
        pos_right = actual_ee_r + step_r

        cmd_left = torch.cat([pos_left, start_quat_left], dim=1)
        cmd_right = torch.cat([pos_right, start_quat_right], dim=1)

        diff_ik_left.set_command(cmd_left)
        diff_ik_right.set_command(cmd_right)

        jac_left = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
        jac_right = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

        ee_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        ee_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left]
        ee_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right]
        ee_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right]

        joint_pos_l = robot_left.data.joint_pos[:, :7]
        joint_pos_r = robot_right.data.joint_pos[:, :7]

        joint_cmd_l = diff_ik_left.compute(ee_pos_l, ee_quat_l, jac_left, joint_pos_l)
        joint_cmd_r = diff_ik_right.compute(ee_pos_r, ee_quat_r, jac_right, joint_pos_r)

        # v51: Joint delta clamping for stability
        # H204: Phase 3 specific JOINT_DELTA_MAX relaxation (0.02 -> 0.05 rad/step)
        if phase == 3:
            JOINT_DELTA_MAX = H204_PHASE3_JOINT_DELTA_MAX  # H204: 0.05 rad/step for Phase 3 Lift
        else:
            JOINT_DELTA_MAX = 0.02  # v53: optimal value for Phase 1/2/4+
        delta_l = joint_cmd_l[0] - joint_pos_l[0]
        delta_r = joint_cmd_r[0] - joint_pos_r[0]
        delta_l_clamped = torch.clamp(delta_l, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        delta_r_clamped = torch.clamp(delta_r, -JOINT_DELTA_MAX, JOINT_DELTA_MAX)
        joint_cmd_l_safe = joint_pos_l + delta_l_clamped.unsqueeze(0)
        joint_cmd_r_safe = joint_pos_r + delta_r_clamped.unsqueeze(0)

        # H118/H119: 30°/step clamp based on actual previous joint positions
        # H119 FIX: Now always executes (prev_joint initialized, not None)
        delta_from_prev_l = joint_cmd_l_safe[0] - prev_joint_l[0]
        delta_from_prev_r = joint_cmd_r_safe[0] - prev_joint_r[0]
        # Clamp to 30°/step max change from actual previous position
        delta_h118_l = torch.clamp(delta_from_prev_l, -H118_MAX_CHANGE_RAD, H118_MAX_CHANGE_RAD)
        delta_h118_r = torch.clamp(delta_from_prev_r, -H118_MAX_CHANGE_RAD, H118_MAX_CHANGE_RAD)
        joint_cmd_l_safe = prev_joint_l + delta_h118_l.unsqueeze(0)
        joint_cmd_r_safe = prev_joint_r + delta_h118_r.unsqueeze(0)
        # Log if H118/H119 clamp was applied (delta exceeded 30°)
        if (delta_from_prev_l.abs() > H118_MAX_CHANGE_RAD).any() or (delta_from_prev_r.abs() > H118_MAX_CHANGE_RAD).any():
            max_l = np.degrees(delta_from_prev_l.abs().max().item())
            max_r = np.degrees(delta_from_prev_r.abs().max().item())
            print(f"  [H118/H119] Phase {phase} step {i}: clamped large delta L={max_l:.1f}° R={max_r:.1f}°")
            sys.stdout.flush()

        # Debug: Check joint command delta for Phase 4.5 (phase=4)
        if phase == 4 and i % 100 == 0:
            delta_l_max = delta_l.abs().max().item()
            delta_r_max = delta_r.abs().max().item()
            clamped_l = (delta_l.abs() > JOINT_DELTA_MAX).any().item()
            clamped_r = (delta_r.abs() > JOINT_DELTA_MAX).any().item()
            print(f"  [IK Debug step {i}] delta_max: L={delta_l_max:.4f}rad R={delta_r_max:.4f}rad, clamped: L={clamped_l} R={clamped_r}")
            print(f"    Target EE: L=({pos_left[0,0]:.3f},{pos_left[0,1]:.3f},{pos_left[0,2]:.3f}) "
                  f"R=({pos_right[0,0]:.3f},{pos_right[0,1]:.3f},{pos_right[0,2]:.3f})")
            print(f"    Actual EE: L=({ee_pos_l[0,0]:.3f},{ee_pos_l[0,1]:.3f},{ee_pos_l[0,2]:.3f}) "
                  f"R=({ee_pos_r[0,0]:.3f},{ee_pos_r[0,1]:.3f},{ee_pos_r[0,2]:.3f})")
            # EE position error
            err_l = ((pos_left - ee_pos_l).pow(2).sum(dim=1)).sqrt().item()
            err_r = ((pos_right - ee_pos_r).pow(2).sum(dim=1)).sqrt().item()
            print(f"    EE error: L={err_l*100:.1f}cm R={err_r*100:.1f}cm")
            sys.stdout.flush()

        # H226: Phase 3 IK Diagnostic Output (every 100 steps)
        # Root cause analysis for Left arm tracking failure (H221-H225 consecutive ik_failure)
        # Output: Joint angles, Jacobian condition number, EE error, DiffIK delta
        if phase == 3 and i % 100 == 0:
            # 1. Joint angles (degrees for readability)
            joint_l_deg = [np.degrees(j.item()) for j in joint_pos_l[0]]
            joint_r_deg = [np.degrees(j.item()) for j in joint_pos_r[0]]

            # 2. Jacobian condition number (indicator of singularity proximity)
            # High condition number (>100) indicates near-singularity, damping will suppress delta
            jac_l_np = jac_left[0].cpu().numpy()  # (6, 7) Jacobian matrix
            jac_r_np = jac_right[0].cpu().numpy()
            cond_l = np.linalg.cond(jac_l_np)
            cond_r = np.linalg.cond(jac_r_np)

            # 3. EE position error (target vs actual)
            ee_err_l = (pos_left - ee_pos_l)[0].cpu().numpy()
            ee_err_r = (pos_right - ee_pos_r)[0].cpu().numpy()
            ee_err_l_norm = np.linalg.norm(ee_err_l)
            ee_err_r_norm = np.linalg.norm(ee_err_r)

            # 4. DiffIK delta (raw, before clamping)
            delta_l_np = delta_l.cpu().numpy()
            delta_r_np = delta_r.cpu().numpy()
            delta_l_norm = np.linalg.norm(delta_l_np)
            delta_r_norm = np.linalg.norm(delta_r_np)

            # 5. Singular values for deeper analysis
            _, s_l, _ = np.linalg.svd(jac_l_np)
            _, s_r, _ = np.linalg.svd(jac_r_np)
            min_sv_l = s_l[-1]
            min_sv_r = s_r[-1]

            print(f"\n  [H226 Phase 3 Diag step {i}]")
            print(f"    Joint angles (deg): L=[{joint_l_deg[0]:.1f},{joint_l_deg[1]:.1f},{joint_l_deg[2]:.1f},{joint_l_deg[3]:.1f},{joint_l_deg[4]:.1f},{joint_l_deg[5]:.1f},{joint_l_deg[6]:.1f}]")
            print(f"                        R=[{joint_r_deg[0]:.1f},{joint_r_deg[1]:.1f},{joint_r_deg[2]:.1f},{joint_r_deg[3]:.1f},{joint_r_deg[4]:.1f},{joint_r_deg[5]:.1f},{joint_r_deg[6]:.1f}]")
            print(f"    Jacobian cond: L={cond_l:.1f} R={cond_r:.1f} (>100 = near singularity)")
            print(f"    Min singular val: L={min_sv_l:.4f} R={min_sv_r:.4f}")
            print(f"    EE error (mm): L=({ee_err_l[0]*1000:.1f},{ee_err_l[1]*1000:.1f},{ee_err_l[2]*1000:.1f}) norm={ee_err_l_norm*1000:.1f}")
            print(f"                   R=({ee_err_r[0]*1000:.1f},{ee_err_r[1]*1000:.1f},{ee_err_r[2]*1000:.1f}) norm={ee_err_r_norm*1000:.1f}")
            print(f"    DiffIK delta norm: L={delta_l_norm:.4f}rad R={delta_r_norm:.4f}rad")
            print(f"    Target EE: L=({pos_left[0,0]:.4f},{pos_left[0,1]:.4f},{pos_left[0,2]:.4f})")
            print(f"               R=({pos_right[0,0]:.4f},{pos_right[0,1]:.4f},{pos_right[0,2]:.4f})")
            print(f"    Actual EE: L=({ee_pos_l[0,0]:.4f},{ee_pos_l[0,1]:.4f},{ee_pos_l[0,2]:.4f})")
            print(f"               R=({ee_pos_r[0,0]:.4f},{ee_pos_r[0,1]:.4f},{ee_pos_r[0,2]:.4f})")
            sys.stdout.flush()

        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = joint_cmd_l_safe[0]
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = joint_cmd_r_safe[0]
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        # v201/H214: sim.step() with SIGALRM timeout protection (Code C INTERRUPT: PHASE3_HANG_PATTERN)
        # Replaces v199 threading.Timer watchdog with interrupt-capable signal.alarm
        _t_before_sim = _time.time()
        v199_watchdog_start()  # v199: Keep threading watchdog as secondary safety
        try:
            sim_step_with_timeout(sim, phase, i)  # v201: SIGALRM-based timeout (30s)
        except SimStepTimeoutError as e:
            v199_watchdog_stop()
            print(f"\n[v201] sim.step() TIMEOUT - exiting gracefully to save video", file=sys.stderr)
            sys.stderr.flush()
            # Exit will trigger atexit handler to save video (v24.30 compliance)
            sys.exit(1)
        v199_watchdog_stop()   # v199: Stop watchdog after sim.step()
        _t_after_sim = _time.time()
        _sim_step_duration = _t_after_sim - _t_before_sim
        # v199: Check if watchdog was triggered
        if _v199_watchdog_triggered.is_set():
            print(f"  [v199] WATCHDOG was triggered during sim.step() at phase={phase} step={i}")
            sys.stdout.flush()
        # Log if sim.step() takes > 1 second (potential hang warning)
        if _sim_step_duration > 1.0:
            print(f"  [H213 WARN] sim.step() took {_sim_step_duration:.2f}s at phase={phase} step={i}")
            sys.stdout.flush()
        # Every 100 steps, log timing stats (also every 50 steps in phase 3 for more granular debugging)
        elif (phase == 3 and i % 50 == 0) or i % 100 == 0:
            print(f"  [v201] sim.step() timing: {_sim_step_duration*1000:.1f}ms (phase={phase}, step={i})")
            sys.stdout.flush()
        scene.update(sim.get_physics_dt())

        # H118: Update previous joint positions for next iteration
        prev_joint_l = robot_left.data.joint_pos[:, :7].clone()
        prev_joint_r = robot_right.data.joint_pos[:, :7].clone()

        # NaN detection and progress logging for all phases
        nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
        if nan_seg >= 0 and nan_detected_step < 0:
            nan_detected_step = i
            progress_pct = (i + 1) / num_steps * 100
            print(f"\n{'!'*70}")
            print(f"[NaN DETECTED] Phase {phase}, Step {i}/{num_steps} ({progress_pct:.1f}%)")
            print(f"First NaN segment: seg_{nan_seg}")
            print(f"{'!'*70}")
            sys.stdout.flush()
            # v24.38: Save NaN snapshot video
            save_nan_snapshot_video(i)
            # v55: Raise exception for retry mechanism
            check_and_raise_nan(f"Phase {phase} Step {i}/{num_steps}")
            if last_good_pos is not None:
                print(f"\nLast good state (step {i-1}):")
                print(f"{'Seg':>4} | {'X':>8} {'Y':>8} {'Z':>8} | {'Vx':>8} {'Vy':>8} {'Vz':>8} | {'Speed':>8}")
                print("-" * 80)
                for j in range(len(last_good_pos)):
                    speed = np.linalg.norm(last_good_vel[j])
                    print(f"{j:4d} | {last_good_pos[j,0]:8.4f} {last_good_pos[j,1]:8.4f} {last_good_pos[j,2]:8.4f} | "
                          f"{last_good_vel[j,0]:+8.4f} {last_good_vel[j,1]:+8.4f} {last_good_vel[j,2]:+8.4f} | {speed:8.4f}")
                # Find segments with highest speed
                speeds = np.linalg.norm(last_good_vel, axis=1)
                top_speed_idx = np.argsort(speeds)[-3:][::-1]
                print(f"\nTop 3 fastest segments:")
                for idx in top_speed_idx:
                    print(f"  seg_{idx}: speed={speeds[idx]:.4f} m/s")
                sys.stdout.flush()
        elif nan_detected_step < 0:
            last_good_pos = pos_arr.copy()
            last_good_vel = vel_arr.copy()
            # Progress logging: every 100 steps (regardless of phase)
            if i % 100 == 0 or i == num_steps - 1:
                speeds = np.linalg.norm(vel_arr, axis=1)
                z_vals = pos_arr[:, 2]
                max_speed_idx = np.argmax(speeds)
                ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
                ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
                print(f"  [P{phase} step {i:4d}/{num_steps}] EE: L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f}) cable_Z: {z_vals.min():.3f}-{z_vals.max():.3f}")
                sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    # H145: Arrival check after loop completion
    final_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    final_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    final_error_l = (target_pos_left - final_ee_l).pow(2).sum(dim=1).sqrt().item()
    final_error_r = (target_pos_right - final_ee_r).pow(2).sum(dim=1).sqrt().item()
    if final_error_l > 0.020 or final_error_r > 0.020:  # H235: 20mm threshold (relaxed from 15mm to allow 17.2mm Z-axis tracking error)
        print(f"  [H145 WARNING] Phase {phase}: Target not reached - L={final_error_l*1000:.1f}mm R={final_error_r*1000:.1f}mm")

        # H226: Diagnostic output at H145 WARNING for root cause analysis
        # This helps identify whether the issue is singularity, joint limits, or damping
        if phase == 3:
            print(f"\n  [H226] === H145 WARNING ROOT CAUSE DIAGNOSTIC ===")
            # Get current state
            final_joint_l = robot_left.data.joint_pos[:, :7]
            final_joint_r = robot_right.data.joint_pos[:, :7]
            final_jac_l = robot_left.root_physx_view.get_jacobians()[:, jacobian_body_left - 1, :, :7]
            final_jac_r = robot_right.root_physx_view.get_jacobians()[:, jacobian_body_right - 1, :, :7]

            # Joint angles
            joint_l_deg = [np.degrees(j.item()) for j in final_joint_l[0]]
            joint_r_deg = [np.degrees(j.item()) for j in final_joint_r[0]]
            print(f"  [H226] Final joint angles (deg):")
            print(f"    L=[{joint_l_deg[0]:.1f},{joint_l_deg[1]:.1f},{joint_l_deg[2]:.1f},{joint_l_deg[3]:.1f},{joint_l_deg[4]:.1f},{joint_l_deg[5]:.1f},{joint_l_deg[6]:.1f}]")
            print(f"    R=[{joint_r_deg[0]:.1f},{joint_r_deg[1]:.1f},{joint_r_deg[2]:.1f},{joint_r_deg[3]:.1f},{joint_r_deg[4]:.1f},{joint_r_deg[5]:.1f},{joint_r_deg[6]:.1f}]")

            # Jacobian analysis
            jac_l_np = final_jac_l[0].cpu().numpy()
            jac_r_np = final_jac_r[0].cpu().numpy()
            cond_l = np.linalg.cond(jac_l_np)
            cond_r = np.linalg.cond(jac_r_np)
            _, s_l, _ = np.linalg.svd(jac_l_np)
            _, s_r, _ = np.linalg.svd(jac_r_np)
            print(f"  [H226] Jacobian condition number: L={cond_l:.1f} R={cond_r:.1f}")
            print(f"  [H226] Singular values:")
            print(f"    L=[{s_l[0]:.4f},{s_l[1]:.4f},{s_l[2]:.4f},{s_l[3]:.4f},{s_l[4]:.4f},{s_l[5]:.4f}]")
            print(f"    R=[{s_r[0]:.4f},{s_r[1]:.4f},{s_r[2]:.4f},{s_r[3]:.4f},{s_r[4]:.4f},{s_r[5]:.4f}]")
            print(f"  [H226] Min singular value: L={s_l[-1]:.4f} R={s_r[-1]:.4f} (low = near singularity)")

            # Target vs actual comparison
            print(f"  [H226] Target EE: L=({target_pos_left[0,0]:.4f},{target_pos_left[0,1]:.4f},{target_pos_left[0,2]:.4f})")
            print(f"                   R=({target_pos_right[0,0]:.4f},{target_pos_right[0,1]:.4f},{target_pos_right[0,2]:.4f})")
            print(f"  [H226] Actual EE: L=({final_ee_l[0,0]:.4f},{final_ee_l[0,1]:.4f},{final_ee_l[0,2]:.4f})")
            print(f"                    R=({final_ee_r[0,0]:.4f},{final_ee_r[0,1]:.4f},{final_ee_r[0,2]:.4f})")

            # Z-axis specific analysis (main issue axis for lift)
            z_err_l = (target_pos_left[0,2] - final_ee_l[0,2]).item()
            z_err_r = (target_pos_right[0,2] - final_ee_r[0,2]).item()
            print(f"  [H226] Z-axis error: L={z_err_l*1000:.1f}mm R={z_err_r*1000:.1f}mm")

            # Asymmetry analysis
            cond_ratio = cond_l / cond_r if cond_r > 0 else float('inf')
            print(f"  [H226] Asymmetry: cond(L)/cond(R) = {cond_ratio:.2f} (>2 = significant)")

            # H229: Swap test interpretation
            if H229_SWAP_LR_TARGETS:
                print(f"\n  [H229] === SWAP TEST INTERPRETATION ===")
                print(f"  [H229] Swap was ENABLED - targets were swapped")
                print(f"  [H229] Left arm was targeting Right's original Y (+Y)")
                print(f"  [H229] Right arm was targeting Left's original Y (-Y)")
                if z_err_l * 1000 > 5 and z_err_r * 1000 <= 5:
                    print(f"  [H229] RESULT: Left arm failed at +Y -> LEFT ARM INTRINSIC ISSUE")
                elif z_err_l * 1000 <= 5 and z_err_r * 1000 > 5:
                    print(f"  [H229] RESULT: Right arm failed at -Y -> POSITION-DEPENDENT ISSUE (-Y workspace)")
                elif z_err_l * 1000 > 5 and z_err_r * 1000 > 5:
                    print(f"  [H229] RESULT: Both arms failed -> BOTH ARM AND POSITION ISSUES")
                else:
                    print(f"  [H229] RESULT: Both arms succeeded -> ORIGINAL ISSUE WAS GRASP FORCE ASYMMETRY")
                print(f"  [H229] =========================================")
            print(f"  [H226] ============================================\n")
            sys.stdout.flush()

        # v24.77: Skip auto-abort when cable is disabled (no grasp = expected position error)
        if H160_DISABLE_CABLE:
            print(f"  [v24.77] H145 WARNING auto-abort SKIPPED (cable disabled, position error expected)")
            sys.stdout.flush()
        else:
            print(f"  [v24.30] Auto-abort: H145 WARNING detected. Saving video before exit.")
            sys.stdout.flush()
            finalize_video()  # v24.30: Save video before any exit
            sys.exit(1)

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def run_analytical_ik_motion_with_collection(
    target_pos_left: torch.Tensor,
    target_pos_right: torch.Tensor,
    num_steps: int,
    gripper_val,
    phase: int,
    stage_name: str = "Stage"
) -> tuple:
    """
    H078/v61: Task-space interpolation + Analytical IK with transition smoothing.

    Key improvements over v60:
    1. Use solve_ik_best (search multiple q7) instead of fixed q7
    2. Add warmup phase: first 50 steps blend from current joints to IK joints
    3. This prevents sudden joint jumps at Phase 4 -> Stage 1b transition

    Args:
        target_pos_left: Target EE position for left arm (1, 3)
        target_pos_right: Target EE position for right arm (1, 3)
        num_steps: Number of interpolation steps
        gripper_val: Gripper position value
        phase: Phase number for logging
        stage_name: Name of the stage for logging

    Returns:
        Tuple of (pos_left, pos_right, quat_left, quat_right)
    """
    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # Get current EE positions (task space start points)
    start_pos_l = robot_left.data.body_pos_w[0, jacobian_body_left].cpu().numpy()
    start_pos_r = robot_right.data.body_pos_w[0, jacobian_body_right].cpu().numpy()

    # Convert target positions to numpy
    target_l_np = target_pos_left[0].cpu().numpy() if torch.is_tensor(target_pos_left) else np.array(target_pos_left)
    target_r_np = target_pos_right[0].cpu().numpy() if torch.is_tensor(target_pos_right) else np.array(target_pos_right)

    # Robot base positions and orientations
    base_pos_l = np.array(ROBOT_LEFT_BASE)
    base_pos_r = np.array(ROBOT_RIGHT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    print(f"  [{stage_name}] Task-space interpolation + Analytical IK with warmup (v61)")
    print(f"    Left:  ({start_pos_l[0]:.3f}, {start_pos_l[1]:.3f}, {start_pos_l[2]:.3f}) -> ({target_l_np[0]:.3f}, {target_l_np[1]:.3f}, {target_l_np[2]:.3f})")
    print(f"    Right: ({start_pos_r[0]:.3f}, {start_pos_r[1]:.3f}, {start_pos_r[2]:.3f}) -> ({target_r_np[0]:.3f}, {target_r_np[1]:.3f}, {target_r_np[2]:.3f})")

    # ===== KEY CHANGE: Save current joints for warmup blending =====
    # H080: initial_joints for warmup blending, current_joints for IK tracking
    initial_joints_l = robot_left.data.joint_pos[0, :7].cpu().numpy()
    initial_joints_r = robot_right.data.joint_pos[0, :7].cpu().numpy()
    current_joints_l = initial_joints_l.copy()
    current_joints_r = initial_joints_r.copy()

    # Warmup configuration
    WARMUP_STEPS = 50  # Blend from current joints to IK joints over first 50 steps

    print(f"    Warmup: First {WARMUP_STEPS} steps blend from initial joints to IK solution")

    # H080: Warmup diagnostics with current-joint-aware IK
    success_diag_l, joints_diag_l, margin_diag_l, dist_diag_l = solve_ik_best_near_current(
        start_pos_l, base_pos_l, base_quat, current_joints_l,
        target_quat, q7_range=(-2.8, 2.8), q7_steps=15, min_margin_deg=5.0
    )
    success_diag_r, joints_diag_r, margin_diag_r, dist_diag_r = solve_ik_best_near_current(
        start_pos_r, base_pos_r, base_quat, current_joints_r,
        target_quat, q7_range=(-2.8, 2.8), q7_steps=15, min_margin_deg=5.0
    )
    if success_diag_l and success_diag_r:
        print(f"  [H080 Diagnostics]")
        print(f"    Joint delta at start: L={dist_diag_l:.1f}°, R={dist_diag_r:.1f}° (was 233° before H080)")
        if dist_diag_l > 30 or dist_diag_r > 30:
            print(f"    WARNING: Large joint delta! May need more warmup steps.")

    ik_failures = 0

    for i in range(num_steps):
        alpha = (i + 1) / num_steps

        # Task-space interpolation (straight line in Cartesian space)
        interp_pos_l = start_pos_l * (1 - alpha) + target_l_np * alpha
        interp_pos_r = start_pos_r * (1 - alpha) + target_r_np * alpha

        # ===== H080: Use solve_ik_best_near_current (v63 approach) =====
        # This searches multiple q7 values and prefers solutions near current joints
        # Avoids elbow flip problem identified in v61 (233° joint delta)
        success_l, joints_ik_l, margin_l, dist_l = solve_ik_best_near_current(
            interp_pos_l, base_pos_l, base_quat, current_joints_l,
            target_quat, q7_range=(-2.8, 2.8), q7_steps=15, min_margin_deg=5.0
        )
        success_r, joints_ik_r, margin_r, dist_r = solve_ik_best_near_current(
            interp_pos_r, base_pos_r, base_quat, current_joints_r,
            target_quat, q7_range=(-2.8, 2.8), q7_steps=15, min_margin_deg=5.0
        )

        if not success_l or not success_r:
            ik_failures += 1
            if i % 50 == 0:
                print(f"    Step {i}: IK failure (L={success_l}, R={success_r})")
            continue

        # H080: Update current_joints for next iteration (track the selected configuration)
        if success_l:
            current_joints_l = joints_ik_l
        if success_r:
            current_joints_r = joints_ik_r

        # ===== KEY CHANGE: Warmup blending =====
        # H080: During warmup phase, blend from INITIAL joints to IK joints
        if i < WARMUP_STEPS:
            warmup_alpha = (i + 1) / WARMUP_STEPS  # 0 to 1 over warmup period
            # Smooth interpolation using cosine for gentler transition
            smooth_alpha = 0.5 * (1 - np.cos(np.pi * warmup_alpha))

            joints_l = initial_joints_l * (1 - smooth_alpha) + joints_ik_l * smooth_alpha
            joints_r = initial_joints_r * (1 - smooth_alpha) + joints_ik_r * smooth_alpha

            if i % 10 == 0:
                delta_l = np.max(np.abs(joints_l - initial_joints_l))
                delta_r = np.max(np.abs(joints_r - initial_joints_r))
                print(f"    Warmup step {i}: blend_alpha={smooth_alpha:.2f}, delta_L={delta_l:.3f}, delta_R={delta_r:.3f}")
        else:
            # After warmup, use IK joints directly
            joints_l = joints_ik_l
            joints_r = joints_ik_r

        # Set joint targets
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = torch.tensor(joints_l, dtype=torch.float32, device=device)
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = torch.tensor(joints_r, dtype=torch.float32, device=device)
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # NaN detection (every 10 steps for efficiency)
        if i % 10 == 0:
            nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
            if nan_seg >= 0:
                print(f"\n{'!'*70}")
                print(f"[NaN DETECTED] {stage_name}, Step {i}/{num_steps} ({alpha*100:.1f}%)")
                print(f"First NaN segment: seg_{nan_seg}")
                print(f"{'!'*70}")
                sys.stdout.flush()
                # v24.38: Save NaN snapshot video
                save_nan_snapshot_video(i)
                check_and_raise_nan(f"{stage_name} Step {i}/{num_steps}")

        # Grasp force monitoring (every 50 steps)
        if i % 50 == 0:
            force_l, force_r = get_contact_force()
            if force_l < 5.0 or force_r < 5.0:
                print(f"  [Warning] Low grasp force at step {i}: L={force_l:.1f}N, R={force_r:.1f}N")
            elif i < 100:
                print(f"  [Warmup] Step {i}: Contact L={force_l:.1f}N R={force_r:.1f}N")

        # Progress logging every 100 steps
        if i % 100 == 0 or i == num_steps - 1:
            ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
            ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
            force_l, force_r = get_contact_force()
            if not H239_NO_CABLE_SPAWN:
                cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
                print(f"  [{stage_name} step {i:4d}/{num_steps}] EE: L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) "
                      f"R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f}) Force: L={force_l:.1f}N R={force_r:.1f}N cable_Z: {cable_z.min():.3f}-{cable_z.max():.3f}")
            else:
                print(f"  [{stage_name} step {i:4d}/{num_steps}] EE: L=({ee_l[0,0]:.3f},{ee_l[0,1]:.3f},{ee_l[0,2]:.3f}) "
                      f"R=({ee_r[0,0]:.3f},{ee_r[0,1]:.3f},{ee_r[0,2]:.3f}) Force: L={force_l:.1f}N R={force_r:.1f}N (cable not spawned)")
            sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    # Final status
    if ik_failures > 0:
        print(f"  [{stage_name}] Completed with {ik_failures} IK failures")

    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone())


def run_joint_space_motion_with_collection(
    target_pos_left: torch.Tensor,
    target_pos_right: torch.Tensor,
    num_steps: int,
    gripper_val,
    phase: int,
    stage_name: str = "Stage",
    max_velocity: float = None,  # H163: Optional velocity override (default: MAX_JOINT_VELOCITY)
    force_adaptive_velocity: bool = False,  # H164: Enable Force R threshold-based dynamic velocity control
    target_quat_wxyz: tuple = None  # H259: Optional gripper orientation (default: GRIPPER_DOWN_QUAT_WXYZ)
) -> tuple:
    """
    H088/v64: Execute motion by directly interpolating joint angles (no IK per step).

    For elbow flip transitions, interpolate in joint space instead of
    computing IK for each task space position. This ensures smooth transition
    even when elbow configuration changes (e.g., 55° elbow flip over 100 steps).

    Key difference from run_analytical_ik_motion_with_collection:
    - Computes IK ONCE at the start (for target position)
    - Interpolates joint angles directly from start to target
    - No IK computation per step = no elbow flip problem

    Args:
        target_pos_left: Target EE position for left arm (1, 3)
        target_pos_right: Target EE position for right arm (1, 3)
        num_steps: Number of interpolation steps (100 = ~1.67s at 60Hz)
        gripper_val: Gripper position value
        phase: Phase number for logging
        stage_name: Name of the stage for logging

    Returns:
        Tuple of (pos_left, pos_right, quat_left, quat_right, abort_flag)
        H200: abort_flag is True if H164/H174 ABORT occurred (skip stabilization)
    """
    # H200: Track if ABORT occurred (H164 Force L or H174 grip loss)
    h200_abort_flag = False

    gripper_float = float(gripper_val) if isinstance(gripper_val, torch.Tensor) else gripper_val

    # Get current joints (Phase 4 end)
    start_joints_l = robot_left.data.joint_pos[0, :7].cpu().numpy()
    start_joints_r = robot_right.data.joint_pos[0, :7].cpu().numpy()

    # Convert target positions to numpy
    target_l_np = target_pos_left[0].cpu().numpy() if torch.is_tensor(target_pos_left) else np.array(target_pos_left)
    target_r_np = target_pos_right[0].cpu().numpy() if torch.is_tensor(target_pos_right) else np.array(target_pos_right)

    # Robot base positions and orientations
    base_pos_l = np.array(ROBOT_LEFT_BASE)
    base_pos_r = np.array(ROBOT_RIGHT_BASE)
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)
    # H259: Use custom quaternion if provided, otherwise default to gripper-down
    target_quat = np.array(target_quat_wxyz if target_quat_wxyz is not None else GRIPPER_DOWN_QUAT_WXYZ)
    stage_cd_override = ("Stage C" in stage_name) or ("Stage D" in stage_name)

    # H271: Normalize IK input into solver frame (=base) at a single point.
    # Intent/diagnostics stay in world, solver input is explicitly base to avoid world/base ambiguity.
    T_ee_tcp = np.eye(4)
    T_ee_tcp[2, 3] = -FINGERTIP_OFFSET

    T_world_base_l = _pose_to_matrix(base_pos_l, base_quat)
    T_world_base_r = _pose_to_matrix(base_pos_r, base_quat)
    T_base_world_l = np.linalg.inv(T_world_base_l)
    T_base_world_r = np.linalg.inv(T_world_base_r)

    T_world_target_ee_l = _pose_to_matrix(target_l_np, target_quat)
    T_world_target_ee_r = _pose_to_matrix(target_r_np, target_quat)
    T_world_target_tcp_l = T_world_target_ee_l @ T_ee_tcp
    T_world_target_tcp_r = T_world_target_ee_r @ T_ee_tcp

    # Solver input (base frame)
    T_base_target_ee_l = T_base_world_l @ T_world_target_ee_l
    T_base_target_ee_r = T_base_world_r @ T_world_target_ee_r
    T_base_target_tcp_l = T_base_target_ee_l @ T_ee_tcp
    T_base_target_tcp_r = T_base_target_ee_r @ T_ee_tcp
    target_l_np_for_ik = T_base_target_tcp_l[:3, 3].copy()
    target_r_np_for_ik = T_base_target_tcp_r[:3, 3].copy()

    target_quat_l_for_ik = np.array(_matrix_to_pose_dict(T_base_target_ee_l)["quaternion_wxyz"], dtype=float)
    target_quat_r_for_ik = np.array(_matrix_to_pose_dict(T_base_target_ee_r)["quaternion_wxyz"], dtype=float)
    solver_base_pos = np.zeros(3, dtype=float)
    solver_base_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    target_l_np_eval_world = T_world_target_tcp_l[:3, 3].copy()
    target_r_np_eval_world = T_world_target_tcp_r[:3, 3].copy()

    print(f"  [{stage_name}] H088 Joint Space Interpolation (v64)")
    print(f"    [H104] panda_hand target: L=({target_l_np[0]:.3f}, {target_l_np[1]:.3f}, {target_l_np[2]:.3f})")
    print(f"    [H104] panda_hand target: R=({target_r_np[0]:.3f}, {target_r_np[1]:.3f}, {target_r_np[2]:.3f})")
    print(f"    [H271] IK tcp target(base): L=({target_l_np_for_ik[0]:.3f}, {target_l_np_for_ik[1]:.3f}, {target_l_np_for_ik[2]:.3f})")
    print(f"    [H271] IK tcp target(base): R=({target_r_np_for_ik[0]:.3f}, {target_r_np_for_ik[1]:.3f}, {target_r_np_for_ik[2]:.3f})")

    # H105: For Stage 1c, constrain IK to maintain elbow-back configuration (J3 < 0)
    # This prevents J3 sign flip that causes grasp loss during Y movement
    # Detect Stage 1c: left arm target Y ≈ -0.15 (moving from -0.232 to -0.150)
    is_stage_1c = (target_pos_left is not None and
                   abs(target_l_np[1] - (-0.15)) < 0.02)  # Y ≈ -0.15

    # H105: Check current J3 sign to decide constraint
    # H118 FIX: J3 is index 2 (not 3) - Franka: J1=0, J2=1, J3=2, J4=3...
    current_j3_sign_l = np.sign(start_joints_l[2])  # J3 is index 2 (elbow)

    if is_stage_1c and current_j3_sign_l < 0:
        # Keep elbow-back (J3 < 0) by limiting q7 search range
        q7_range_left = (-2.8, 0.0)
        print(f"    [H105] Stage 1c detected: constraining q7_range to {q7_range_left} for elbow-back")
        print(f"    [H105] Current J3 Left = {np.rad2deg(start_joints_l[2]):.1f}° (sign={current_j3_sign_l})")
    else:
        q7_range_left = (-2.8, 2.8)

    # Right arm uses full range (no elbow flip issue reported)
    q7_range_right = (-2.8, 2.8)

    # H088 FIX: Use solve_ik_best_near_current to find IK solution CLOSEST to current joints
    # This prevents selecting an IK solution on the "wrong side" of configuration space
    # Previous bug: solve_ik_best() maximized margin but ignored proximity to current joints

    # H116: No J3 constraint (removed due to trajectory inconsistency), only max_joint_change applied across all Stages
    # H115's J3 constraint [-45 deg, -30 deg] caused IK failure in all Stage 2a-1 through 2a-4, so it was removed
    j3_min = None  # No J3 constraint
    j3_max = None  # No J3 constraint
    max_change = STAGE_CD_MAX_JOINT_CHANGE_DEG if stage_cd_override else MAX_JOINT_CHANGE_DEG
    print(f"    [H116] max_joint_change={max_change}° (J3 constraint disabled)")
    if stage_cd_override:
        print(f"    [H269] Stage C/D max_joint_change override active: {STAGE_CD_MAX_JOINT_CHANGE_DEG}°")

    use_geofik_cd = USE_GEOFIK_FOR_STAGE_CD and stage_cd_override
    if use_geofik_cd:
        print(f"    [GeoFIK] Enabled for {stage_name} with q7 scan {GEOFIK_Q7_MIN}..{GEOFIK_Q7_MAX} ({GEOFIK_Q7_STEPS} steps)")

    success_l, target_joints_l, margin_l, dist_l = solve_ik_best_near_current(
        target_l_np_for_ik, solver_base_pos, solver_base_quat, start_joints_l,
        target_quat_l_for_ik, q7_range=q7_range_left, q7_steps=20, min_margin_deg=3.0,  # H105: Use constrained range
        j3_min_deg=j3_min, j3_max_deg=j3_max, max_joint_change_deg=max_change,  # H115
        use_geofik=use_geofik_cd, arm="L"
    )
    success_r, target_joints_r, margin_r, dist_r = solve_ik_best_near_current(
        target_r_np_for_ik, solver_base_pos, solver_base_quat, start_joints_r,
        target_quat_r_for_ik, q7_range=q7_range_right, q7_steps=20, min_margin_deg=3.0,
        j3_min_deg=j3_min, j3_max_deg=j3_max, max_joint_change_deg=max_change,  # H115
        use_geofik=use_geofik_cd, arm="R"
    )

    # H105: Log J3 after IK to verify no sign flip
    # H118 FIX: Use index 2 for J3 (not index 3 which is J4)
    if success_l and target_joints_l is not None:
        target_j3_sign_l = np.sign(target_joints_l[2])  # H118: J3 is index 2
        if target_j3_sign_l != current_j3_sign_l:
            print(f"    [H105 WARNING] J3 sign flip detected! {np.rad2deg(start_joints_l[2]):.1f}° → {np.rad2deg(target_joints_l[2]):.1f}°")
        else:
            print(f"    [H105] J3 sign preserved: {np.rad2deg(start_joints_l[2]):.1f}° → {np.rad2deg(target_joints_l[2]):.1f}°")

    # DEBUG v77/H271: Verify IK solution with FK + structured trace output.
    from thread_isaac_lab.scripts.franka_analytical_ik import forward_kinematics
    from scipy.spatial.transform import Rotation as R

    ee_link_name_l = robot_left.data.body_names[jacobian_body_left]
    ee_link_name_r = robot_right.data.body_names[jacobian_body_right]
    run_id = _activerun_id if "_activerun_id" in globals() else ""

    def verify_ik_with_fk(joints, base_pos, base_quat_wxyz):
        """Compute world-frame FK for solver EE frame."""
        T_base_ee = forward_kinematics(np.array(joints))
        R_base = R.from_quat(_quat_wxyz_to_xyzw(np.asarray(base_quat_wxyz, dtype=float))).as_matrix()
        T_base = np.eye(4)
        T_base[:3, :3] = R_base
        T_base[:3, 3] = base_pos
        T_world_ee = T_base @ T_base_ee
        return T_world_ee

    def emit_ik_trace(
        arm: str,
        ee_link_name: str,
        success: bool,
        margin_deg: float,
        dist_deg: float,
        target_tcp_T: np.ndarray,
        target_ee_T: np.ndarray,
        fk_ee_T: np.ndarray = None,
        fk_tcp_T: np.ndarray = None,
        pos_err_m: float = None,
        rot_err_rad: float = None,
    ):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "trace_version": IK_TRACE_VERSION,
            "run_id": run_id,
            "stage_name": stage_name,
            "phase": int(phase),
            "arm": arm,
            "target_frame": "world",
            "solver_input_frame": "base",
            "ee_link_name": ee_link_name,
            "ik_status": "success" if success else "fail",
            "iters": None,
            "residual": None,
            "margin_deg": float(margin_deg) if margin_deg is not None else None,
            "distance_deg": float(dist_deg) if dist_deg is not None else None,
            "use_geofik": bool(use_geofik_cd),
            "T_world_target_tcp": _matrix_to_pose_dict(target_tcp_T),
            "T_world_target_ee": _matrix_to_pose_dict(target_ee_T),
            "T_ee_tcp": _matrix_to_pose_dict(T_ee_tcp),
            "T_world_fk_ee": _matrix_to_pose_dict(fk_ee_T) if fk_ee_T is not None else None,
            "T_world_fk_tcp": _matrix_to_pose_dict(fk_tcp_T) if fk_tcp_T is not None else None,
            "pos_err_m": float(pos_err_m) if pos_err_m is not None else None,
            "rot_err_rad": float(rot_err_rad) if rot_err_rad is not None else None,
        }
        _append_ik_trace(entry)

        diag_event = {
            "ts": entry["ts"],
            "trace_version": DIAG_TRACE_VERSION,
            "step": None,
            "stage": "ik",
            "event_type": "IK_SOLVE",
            "intent": {
                "target_frame": "world",
                "T_world_target_tcp": entry["T_world_target_tcp"],
                "T_world_target_ee": entry["T_world_target_ee"],
            },
            "transform": {
                "solver_input_frame": "base",
                "T_ee_tcp": entry["T_ee_tcp"],
                "use_geofik": bool(use_geofik_cd),
                "max_joint_change_deg": float(max_change),
            },
            "realized": {
                "ee_link_name": ee_link_name,
                "T_world_fk_ee": entry["T_world_fk_ee"],
                "T_world_fk_tcp": entry["T_world_fk_tcp"],
            },
            "error": {
                "pos_err_m": entry["pos_err_m"],
                "rot_err_rad": entry["rot_err_rad"],
            },
            "status": {
                "success": bool(success),
                "ik_status": entry["ik_status"],
                "iters": entry["iters"],
                "residual": entry["residual"],
                "margin_deg": entry["margin_deg"],
                "distance_deg": entry["distance_deg"],
            },
            "context": {
                "run_id": run_id,
                "hypothesis_id": _DIAG_HYPOTHESIS_ID,
                "probe_pack": _DIAG_PROBE_PACK,
                "stage_name": stage_name,
                "phase": int(phase),
                "arm": arm,
            },
        }
        _append_diag_trace(diag_event)
        _update_diag_summary(diag_event)

    if success_l and target_joints_l is not None:
        T_world_fk_ee_l = verify_ik_with_fk(target_joints_l, base_pos_l, base_quat)
        T_world_fk_tcp_l = T_world_fk_ee_l @ T_ee_tcp
        ee_verify_l = T_world_fk_tcp_l[:3, 3]
        err_l = np.linalg.norm(ee_verify_l - target_l_np_eval_world)
        rot_err_l = _rotation_error_rad(T_world_target_tcp_l[:3, :3], T_world_fk_tcp_l[:3, :3])

        print(f"    [FK VERIFY L] TCP Target Z={target_l_np_eval_world[2]:.3f}, FK Z={ee_verify_l[2]:.3f}, Error={err_l:.3f}m")
        expected_panda_hand_z = ee_verify_l[2] + FINGERTIP_OFFSET
        print(f"    [H104] Expected panda_hand Z={expected_panda_hand_z:.3f} (target was {target_l_np[2]:.3f})")
        if err_l > 0.01:
            print(f"    [CRITICAL] IK-FK mismatch LEFT! Error={err_l:.3f}m > 0.01m threshold")

        emit_ik_trace(
            arm="L",
            ee_link_name=ee_link_name_l,
            success=True,
            margin_deg=margin_l,
            dist_deg=dist_l,
            target_tcp_T=T_world_target_tcp_l,
            target_ee_T=T_world_target_ee_l,
            fk_ee_T=T_world_fk_ee_l,
            fk_tcp_T=T_world_fk_tcp_l,
            pos_err_m=err_l,
            rot_err_rad=rot_err_l,
        )
    else:
        emit_ik_trace(
            arm="L",
            ee_link_name=ee_link_name_l,
            success=False,
            margin_deg=margin_l,
            dist_deg=dist_l,
            target_tcp_T=T_world_target_tcp_l,
            target_ee_T=T_world_target_ee_l,
        )

    if success_r and target_joints_r is not None:
        T_world_fk_ee_r = verify_ik_with_fk(target_joints_r, base_pos_r, base_quat)
        T_world_fk_tcp_r = T_world_fk_ee_r @ T_ee_tcp
        ee_verify_r = T_world_fk_tcp_r[:3, 3]
        err_r = np.linalg.norm(ee_verify_r - target_r_np_eval_world)
        rot_err_r = _rotation_error_rad(T_world_target_tcp_r[:3, :3], T_world_fk_tcp_r[:3, :3])

        print(f"    [FK VERIFY R] TCP Target Z={target_r_np_eval_world[2]:.3f}, FK Z={ee_verify_r[2]:.3f}, Error={err_r:.3f}m")
        expected_panda_hand_z_r = ee_verify_r[2] + FINGERTIP_OFFSET
        print(f"    [H104] Expected panda_hand Z={expected_panda_hand_z_r:.3f} (target was {target_r_np[2]:.3f})")
        if err_r > 0.01:
            print(f"    [CRITICAL] IK-FK mismatch RIGHT! Error={err_r:.3f}m > 0.01m threshold")

        emit_ik_trace(
            arm="R",
            ee_link_name=ee_link_name_r,
            success=True,
            margin_deg=margin_r,
            dist_deg=dist_r,
            target_tcp_T=T_world_target_tcp_r,
            target_ee_T=T_world_target_ee_r,
            fk_ee_T=T_world_fk_ee_r,
            fk_tcp_T=T_world_fk_tcp_r,
            pos_err_m=err_r,
            rot_err_rad=rot_err_r,
        )
    else:
        emit_ik_trace(
            arm="R",
            ee_link_name=ee_link_name_r,
            success=False,
            margin_deg=margin_r,
            dist_deg=dist_r,
            target_tcp_T=T_world_target_tcp_r,
            target_ee_T=T_world_target_ee_r,
        )

    if not success_l or not success_r:
        print(f"  [{stage_name}] IK failed for target position!")
        print(f"    Left: {success_l}, Right: {success_r}")
        # Return current positions if IK fails
        # H211: Fix early return to include 5th abort_flag (False since not ABORT, just IK failure)
        return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
                robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
                robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
                robot_right.data.body_quat_w[:, jacobian_body_right].clone(),
                False)  # H211: abort_flag=False (IK failure, not ABORT)

    # H088: Joint space interpolation diagnostic (using dist from solve_ik_best_near_current)
    delta_l = dist_l  # Already in degrees
    delta_r = dist_r  # Already in degrees
    delta_per_step_l = delta_l / num_steps
    delta_per_step_r = delta_r / num_steps

    print(f"    Left:  max joint delta = {delta_l:.1f}° ({delta_per_step_l:.2f}°/step)")
    print(f"    Right: max joint delta = {delta_r:.1f}° ({delta_per_step_r:.2f}°/step)")
    print(f"    Steps: {num_steps}, Target margins: L={margin_l:.1f}° R={margin_r:.1f}°")

    # Log target joints for future task_config.py addition
    print(f"    [H088 LOG] Start joints L: {[f'{x:.6f}' for x in start_joints_l]}")
    print(f"    [H088 LOG] Start joints R: {[f'{x:.6f}' for x in start_joints_r]}")
    print(f"    [H088 LOG] Target joints L: {[f'{x:.6f}' for x in target_joints_l]}")
    print(f"    [H088 LOG] Target joints R: {[f'{x:.6f}' for x in target_joints_r]}")

    # Safety check: warn if delta_per_step exceeds physical limits
    SAFE_DEG_PER_STEP = 5.0  # Franka safe rate
    if delta_per_step_l > SAFE_DEG_PER_STEP or delta_per_step_r > SAFE_DEG_PER_STEP:
        print(f"    [WARNING] Joint velocity may be too high!")
        print(f"    Consider increasing num_steps to at least {int(max(delta_l, delta_r) / SAFE_DEG_PER_STEP) + 1}")

    # H099/v73: Cosine interpolation in joint space (replaces linear)
    # Cosine interpolation has zero velocity at start/end, reducing force spikes
    # alpha'(0) = 0, alpha'(end) = 0

    # H128: Additional slow ramp-up for Stage 2a-1 (X-axis motion start)
    # Root cause: Stage 2a-1 has abrupt velocity change after Phase 4 stabilization
    # H135: Increased from 67 to 83 steps (proportional to STAGE2A_STEPS 600→750)
    H128_STAGE2A1_RAMP_STEPS = 83  # H135: 67→83 steps for longer ramp-up
    is_stage_2a1 = "2a-1" in stage_name
    h128_logged = False

    # H119: Track actual joint positions for 30°/step clamping
    # This fixes the issue where H118 only covered Diff IK, not Joint Space
    prev_joint_l = robot_left.data.joint_pos[:, :7].clone()
    prev_joint_r = robot_right.data.joint_pos[:, :7].clone()
    H119_MAX_CHANGE_RAD = np.radians(30.0)  # H119: 30°/step limit

    # H164: Force R threshold-based dynamic velocity control state
    h164_velocity_reduced = False  # Track if velocity is currently reduced
    h164_base_velocity = max_velocity if max_velocity is not None else MAX_JOINT_VELOCITY
    # H165: Force L direct monitoring state
    h165_force_l_reduced = False  # Track if velocity is reduced due to Force L
    if force_adaptive_velocity:
        print(f"  [H164] Force-adaptive velocity control ENABLED")
        print(f"  [H164] Base velocity: {h164_base_velocity:.2f} rad/s, Reduced: {VEL_REDUCED:.2f} rad/s")
        print(f"  [H164] Thresholds: FORCE_R_HIGH={FORCE_R_HIGH}N, FORCE_R_LOW={FORCE_R_LOW}N, FORCE_L_ABORT={FORCE_L_ABORT}N, FORCE_R_ABORT={FORCE_R_ABORT}N")
        print(f"  [H165] Force L monitoring ENABLED: HIGH={FORCE_L_HIGH_THRESHOLD}N, LOW={FORCE_L_LOW_THRESHOLD}N, VEL={FORCE_L_REDUCED_VELOCITY:.2f} rad/s")

    for i in range(num_steps):
        # H099: Cosine interpolation (smoother start/end)
        alpha = (1 - math.cos(math.pi * (i + 1) / num_steps)) / 2

        # H128: Apply additional slow ramp-up for Stage 2a-1
        if is_stage_2a1 and i < H128_STAGE2A1_RAMP_STEPS:
            # Additional cosine ramp-up for first 50 steps
            ramp_alpha = 0.5 * (1 - math.cos(math.pi * i / H128_STAGE2A1_RAMP_STEPS))
            alpha = alpha * ramp_alpha
            if not h128_logged:
                print(f"  [H128] Stage 2a-1: Applying cosine ramp-up for first {H128_STAGE2A1_RAMP_STEPS} steps")
                h128_logged = True

        # H142: Position-based interpolation (replaces time-based)
        # Root cause fix for LL-2026-01-13-TIM-003 positive feedback loop
        dt = 1.0 / 60.0

        # H164: Force R threshold-based dynamic velocity control
        if force_adaptive_velocity:
            force_l, force_r = get_contact_force()

            # H164: Force L safety abort check
            if force_l > FORCE_L_ABORT:
                print(f"  [H164] ABORT: Force L={force_l:.1f}N > {FORCE_L_ABORT}N at step {i}")
                print(f"  [H164] Breaking Stage B to prevent physics collapse")
                print(f"  [H200] Setting abort_flag=True (skip post-stage stabilization)")
                sys.stdout.flush()
                h200_abort_flag = True  # H200: Mark ABORT for caller to skip stabilization
                break  # Abort Stage B, continue to next phase

            # H174: Force R grip loss detection (force dropped below minimum threshold)
            # H214: Skip grip loss check when cable is disabled (Force=0.0N is expected)
            if not H160_DISABLE_CABLE and force_r < FORCE_R_ABORT:
                print(f"  [H174] ABORT: Force R={force_r:.1f}N < {FORCE_R_ABORT}N at step {i}")
                print(f"  [H174] Grip loss detected - aborting Stage B")
                print(f"  [H200] Setting abort_flag=True (skip post-stage stabilization)")
                sys.stdout.flush()
                h200_abort_flag = True  # H200: Mark ABORT for caller to skip stabilization
                break  # Abort Stage B, continue to next phase

            # H164: Hysteresis logic for velocity adjustment
            if not h164_velocity_reduced and force_r > FORCE_R_HIGH:
                # Force R exceeded high threshold - reduce velocity
                h164_velocity_reduced = True
                print(f"  [H164] Force R HIGH: {force_r:.1f}N > {FORCE_R_HIGH}N at step {i} - REDUCING velocity to {VEL_REDUCED:.2f} rad/s")
                sys.stdout.flush()
            elif h164_velocity_reduced and force_r < FORCE_R_LOW:
                # Force R dropped below low threshold - restore velocity
                h164_velocity_reduced = False
                print(f"  [H164] Force R LOW: {force_r:.1f}N < {FORCE_R_LOW}N at step {i} - RESTORING velocity to {h164_base_velocity:.2f} rad/s")
                sys.stdout.flush()

            # H165: Force L direct monitoring hysteresis logic
            if not h165_force_l_reduced and force_l > FORCE_L_HIGH_THRESHOLD:
                # Force L exceeded high threshold - reduce velocity more aggressively
                h165_force_l_reduced = True
                print(f"  [H165] Force L HIGH: {force_l:.1f}N > {FORCE_L_HIGH_THRESHOLD}N at step {i} - REDUCING velocity to {FORCE_L_REDUCED_VELOCITY:.2f} rad/s")
                sys.stdout.flush()
            elif h165_force_l_reduced and force_l < FORCE_L_LOW_THRESHOLD:
                # Force L dropped below low threshold - can restore velocity
                h165_force_l_reduced = False
                print(f"  [H165] Force L LOW: {force_l:.1f}N < {FORCE_L_LOW_THRESHOLD}N at step {i} - Force L control released")
                sys.stdout.flush()

            # Apply velocity based on current state (H165 takes priority over H164 if both triggered)
            if h165_force_l_reduced:
                effective_velocity = FORCE_L_REDUCED_VELOCITY  # H165: More conservative (0.30 rad/s)
            elif h164_velocity_reduced:
                effective_velocity = VEL_REDUCED  # H164: 0.5 rad/s
            else:
                effective_velocity = h164_base_velocity
        else:
            # H163: Use stage-specific velocity if provided, otherwise use global MAX_JOINT_VELOCITY
            effective_velocity = max_velocity if max_velocity is not None else MAX_JOINT_VELOCITY

        max_delta_h142 = effective_velocity * dt

        # Calculate remaining delta from actual position to target
        remaining_l = torch.tensor(target_joints_l, dtype=torch.float32, device=device) - prev_joint_l[0]
        remaining_r = torch.tensor(target_joints_r, dtype=torch.float32, device=device) - prev_joint_r[0]

        # Clamp step size by velocity limit (combines H119 and H136)
        delta_l_clamped = torch.clamp(remaining_l, -max_delta_h142, max_delta_h142)
        delta_r_clamped = torch.clamp(remaining_r, -max_delta_h142, max_delta_h142)

        # Apply from actual position (no lag accumulation)
        clamped_joints_l = prev_joint_l[0] + delta_l_clamped
        clamped_joints_r = prev_joint_r[0] + delta_r_clamped

        # Log velocity for monitoring (replaces H136 log)
        actual_vel_l = delta_l_clamped.abs().max().item() / dt
        actual_vel_r = delta_r_clamped.abs().max().item() / dt
        if i % 50 == 0:
            remain_l_deg = np.degrees(remaining_l.abs().max().item())
            remain_r_deg = np.degrees(remaining_r.abs().max().item())
            print(f"  [H142] {stage_name} step {i}: vel L={actual_vel_l:.2f} R={actual_vel_r:.2f} rad/s, remain L={remain_l_deg:.1f}° R={remain_r_deg:.1f}°")
            sys.stdout.flush()

        # Set joint targets (using H142 position-based values)
        tgt_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        tgt_l[0, :7] = clamped_joints_l  # H142: Use position-based clamped values
        tgt_l[0, -2:] = gripper_val
        robot_left.set_joint_position_target(tgt_l)
        robot_left.write_data_to_sim()

        tgt_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        tgt_r[0, :7] = clamped_joints_r  # H142: Use position-based clamped values
        tgt_r[0, -2:] = gripper_val
        robot_right.set_joint_position_target(tgt_r)
        robot_right.write_data_to_sim()

        # v24.75: sim.step() with timeout protection (fixes Phase 5 Stage 2a hang)
        try:
            sim_step_with_timeout(sim, phase, i)
        except SimStepTimeoutError as e:
            print(f"\n[v24.75] sim.step() TIMEOUT in {stage_name} at step {i} - exiting to save video", file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        scene.update(sim.get_physics_dt())

        # H142: Update previous joint positions for next iteration
        prev_joint_l = robot_left.data.joint_pos[:, :7].clone()
        prev_joint_r = robot_right.data.joint_pos[:, :7].clone()

        # NaN detection (every 10 steps for efficiency)
        if i % 10 == 0:
            nan_seg, pos_arr, vel_arr = check_cable_nan_detailed(cable)
            if nan_seg >= 0:
                print(f"\n{'!'*70}")
                print(f"[NaN DETECTED] {stage_name} (H088), Step {i}/{num_steps} ({alpha*100:.1f}%)")
                print(f"First NaN segment: seg_{nan_seg}")
                print(f"{'!'*70}")
                sys.stdout.flush()
                # v24.38: Save NaN snapshot video
                save_nan_snapshot_video(i)
                check_and_raise_nan(f"{stage_name} Step {i}/{num_steps}")

        # Grasp force monitoring (every 20 steps for H088 detailed tracking)
        if i % 20 == 0:
            force_l, force_r = get_contact_force()
            if force_l < 5.0 or force_r < 5.0:
                print(f"    [Warning] Low grasp force at step {i}: L={force_l:.1f}N R={force_r:.1f}N")

        # Progress logging every 50 steps (more frequent for H088)
        if i % 50 == 0 or i == num_steps - 1:
            ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
            ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
            force_l, force_r = get_contact_force()
            curr_joints_l = robot_left.data.joint_pos[0, :7].cpu().numpy()
            curr_joints_r = robot_right.data.joint_pos[0, :7].cpu().numpy()
            j3_l_deg = np.degrees(curr_joints_l[2])
            j3_r_deg = np.degrees(curr_joints_r[2])
            if not H239_NO_CABLE_SPAWN:
                cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
                print(f"  [{stage_name} step {i:4d}/{num_steps}] alpha={alpha:.2f} J3: L={j3_l_deg:.1f}° R={j3_r_deg:.1f}° "
                      f"Force: L={force_l:.1f}N R={force_r:.1f}N cable_Z: {cable_z.min():.3f}-{cable_z.max():.3f}")
            else:
                print(f"  [{stage_name} step {i:4d}/{num_steps}] alpha={alpha:.2f} J3: L={j3_l_deg:.1f}° R={j3_r_deg:.1f}° "
                      f"Force: L={force_l:.1f}N R={force_r:.1f}N (cable not spawned)")
            sys.stdout.flush()

        # Collect data at FRAME_COLLECT_INTERVAL
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(phase, gripper_float, gripper_float)

    print(f"  [{stage_name}] H088 completed successfully")

    # DEBUG v78: Compare simulation joints with FK and EE
    actual_joints_l = robot_left.data.joint_pos[0, :7].cpu().numpy()
    actual_joints_r = robot_right.data.joint_pos[0, :7].cpu().numpy()

    print(f"    [DEBUG v78] Coordinate System Analysis:")
    print(f"    [TARGET JOINTS L] {[f'{x:.4f}' for x in target_joints_l]}")
    print(f"    [SIM JOINTS L]    {[f'{x:.4f}' for x in actual_joints_l]}")
    joints_diff_l = np.abs(np.array(target_joints_l) - actual_joints_l).max()
    print(f"    [JOINTS DIFF L]   Max diff = {np.degrees(joints_diff_l):.2f} deg")

    # FK from actual simulation joints
    T_world_fk_sim_l = verify_ik_with_fk(actual_joints_l, base_pos_l, base_quat)
    ee_from_sim_joints_l = T_world_fk_sim_l[:3, 3]
    print(f"    [FK FROM SIM JOINTS L] ({ee_from_sim_joints_l[0]:.3f}, {ee_from_sim_joints_l[1]:.3f}, {ee_from_sim_joints_l[2]:.3f})")

    # Simulation EE position
    sim_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left][0].cpu().numpy()
    print(f"    [SIM EE L]              ({sim_ee_l[0]:.3f}, {sim_ee_l[1]:.3f}, {sim_ee_l[2]:.3f})")

    # Compare FK vs SIM EE
    fk_sim_diff = np.linalg.norm(ee_from_sim_joints_l - sim_ee_l)
    print(f"    [FK vs SIM EE] FK_Z={ee_from_sim_joints_l[2]:.3f}, SIM_Z={sim_ee_l[2]:.3f}, Total Diff={fk_sim_diff:.3f}m")

    # EE Body info
    print(f"    [EE BODY] jacobian_body_left index: {jacobian_body_left}")
    print(f"    [EE BODY] Name: {robot_left.data.body_names[jacobian_body_left]}")

    # H200: Return abort_flag as 5th element to indicate if ABORT occurred
    return (robot_left.data.body_pos_w[:, jacobian_body_left].clone(),
            robot_right.data.body_pos_w[:, jacobian_body_right].clone(),
            robot_left.data.body_quat_w[:, jacobian_body_left].clone(),
            robot_right.data.body_quat_w[:, jacobian_body_right].clone(),
            h200_abort_flag)


def check_cable_nan() -> bool:
    """Check if cable position/orientation contains NaN.

    Returns:
        True if cable state is valid (no NaN), False otherwise.
    """
    # H239: Always return True when cable is not spawned
    if H239_NO_CABLE_SPAWN:
        return True
    # H160: Always return True when cable is disabled
    if H160_DISABLE_CABLE:
        return True
    cable_pos = cable.data.root_pos_w[0]
    cable_quat = cable.data.root_quat_w[0]
    has_nan = torch.any(torch.isnan(cable_pos)) or torch.any(torch.isnan(cable_quat))
    return not has_nan.item()


def hold_position(num_steps: int = 20, gripper_val: float = None) -> None:
    """Hold current position for stabilization (H107: with joint control, H108: with gripper control).

    H107: Previous implementation just called sim.step() without joint control,
    which caused physics collapse (Right arm J0: 120° → 516°).

    H108: Added gripper control to prevent cable slippage during hold.
    Also reduced default steps from 50 to 20 per BLACKLIST recommendation.

    Args:
        num_steps: Number of simulation steps to hold (default: 20, was 50 before H108).
        gripper_val: Gripper position to maintain. If None, gripper control is skipped.
    """
    # H107: Get current joint positions to maintain
    current_joints_l = robot_left.data.joint_pos[0].clone()
    current_joints_r = robot_right.data.joint_pos[0].clone()

    for step in range(num_steps):
        # H107: Set joint position targets to current positions
        robot_left.set_joint_position_target(current_joints_l.unsqueeze(0))
        robot_right.set_joint_position_target(current_joints_r.unsqueeze(0))

        # H108: Maintain gripper position to prevent cable slippage
        if gripper_val is not None:
            gripper_target = torch.tensor([[gripper_val, gripper_val]], device=device)
            robot_left.set_joint_position_target(gripper_target, joint_ids=[7, 8])
            robot_right.set_joint_position_target(gripper_target, joint_ids=[7, 8])

        robot_left.write_data_to_sim()
        robot_right.write_data_to_sim()

        sim.step()
        scene.update(sim.get_physics_dt())

        # H107: Monitor for anomalies every 10 steps
        if step % 10 == 0:
            check_joints_l = robot_left.data.joint_pos[0]
            check_joints_r = robot_right.data.joint_pos[0]
            max_diff_l = (check_joints_l[:7] - current_joints_l[:7]).abs().max().item()
            max_diff_r = (check_joints_r[:7] - current_joints_r[:7]).abs().max().item()
            if max_diff_l > 0.5 or max_diff_r > 0.5:  # > 28.6° drift
                print(f"  [H107 Warning] Joint drift at step {step}: L={np.rad2deg(max_diff_l):.1f}° R={np.rad2deg(max_diff_r):.1f}°")


def check_and_raise_nan(location: str) -> None:
    """v55: Check cable physics and raise NaNDetectedException if NaN detected.

    Uses cable velocity to detect physics explosion before NaN appears.
    Threshold: velocity > 1e6 m/s indicates imminent NaN.

    Args:
        location: Description of where the check is performed (for error message).

    Raises:
        NaNDetectedException: If cable velocity exceeds threshold or NaN detected.
    """
    # H239: Skip check when cable is not spawned
    if H239_NO_CABLE_SPAWN:
        return
    # H160: Skip check when cable is disabled
    if H160_DISABLE_CABLE:
        return

    cable_obj = scene["cable"]
    cable_vel = cable_obj.data.body_vel_w[:, :, :3]
    max_vel = cable_vel.abs().max().item()

    # Check for extreme velocity (physics explosion)
    if max_vel > 1e6:
        raise NaNDetectedException(f"{location} (velocity={max_vel:.2e})")

    # Also check for actual NaN
    cable_pos = cable_obj.data.body_pos_w
    if torch.any(torch.isnan(cable_pos)):
        raise NaNDetectedException(f"{location} (NaN in position)")


def reset_cable_to_initial(max_retries: int = 5) -> bool:
    """Reset cable to initial position with comprehensive state restoration.

    2026-01-06 fix: Restore body_state_w for all segments + added position verification

    Args:
        max_retries: Maximum number of retry attempts.

    Returns:
        True if reset successful (no NaN and position verified), False otherwise.
    """
    # H239: Skip when cable is not spawned
    if H239_NO_CABLE_SPAWN:
        print("  [H239] Cable reset SKIPPED (no cable in scene)")
        return True

    # Expected initial Z position (obtained from initial_cable_body_state)
    expected_min_z = initial_cable_body_state[:, :, 2].min().item()
    expected_max_z = initial_cable_body_state[:, :, 2].max().item()
    print(f"  [Reset] Expected Z range: {expected_min_z:.3f} - {expected_max_z:.3f}")

    for attempt in range(max_retries):
        # 2026-01-07: More aggressive reset to clear accumulated PhysX state
        # First reset the simulation context (soft=False for complete reset)
        sim.reset(soft=True)  # H143 reverted: soft=False caused grasp failures
        scene.reset()  # Reset all scene entities
        sim.step()

        # 2026-01-06: Restore state of all segments (velocities zeroed out)
        # initial_cable_body_state: [1, num_bodies, 13]
        # 13 = pos(3) + quat(4) + lin_vel(3) + ang_vel(3)
        reset_body_state = initial_cable_body_state.clone()
        reset_body_state[:, :, 7:13] = 0.0  # Zero out linear and angular velocities

        # Write full body state for RigidObject
        # Use appropriate method depending on Articulation/RigidObject API
        has_body_write = hasattr(cable, 'write_body_state_to_sim')
        if has_body_write:
            cable.write_body_state_to_sim(reset_body_state)
            print(f"  [Reset] Using write_body_state_to_sim (attempt {attempt+1})")
        else:
            # Fallback: write root state only + joint state
            # 2026-01-07: Use correct root body index (not always seg_0!)
            root_state = reset_body_state[:, cable_root_body_idx, :]
            cable.write_root_state_to_sim(root_state)
            print(f"  [Reset] Using write_root_state_to_sim for seg_{cable_root_body_idx} (attempt {attempt+1})")

        # Restore joint state as well (zero velocity)
        zero_joint_vel = torch.zeros_like(initial_cable_joint_vel)
        cable.write_joint_state_to_sim(initial_cable_joint_pos, zero_joint_vel)

        # 2026-01-07: Code B recommendation - Clear articulation drive targets
        # This helps clear PhysX TGS solver warm-start state
        try:
            cable.set_joint_position_target(initial_cable_joint_pos)
            cable.set_joint_velocity_target(zero_joint_vel)
            print(f"  [Reset] Articulation drive targets cleared")
        except (AttributeError, TypeError) as e:
            print(f"  [Reset] Note: Drive target methods not available ({type(e).__name__})")

        cable.reset()
        cable.write_data_to_sim()

        # Apply state with minimal steps (minimize gravity effects)
        for _ in range(3):
            sim.step()
            scene.update(sim.get_physics_dt())

        # Restore robot states with more aggressive reset
        # 2026-01-07: Multiple write cycles to ensure precise joint positions
        for reset_iter in range(3):
            robot_left.write_root_state_to_sim(initial_robot_left_state)
            robot_right.write_root_state_to_sim(initial_robot_right_state)
            robot_left.write_joint_state_to_sim(initial_joint_pos_left, initial_joint_vel_left)
            robot_right.write_joint_state_to_sim(initial_joint_pos_right, initial_joint_vel_right)
            # Also set joint position targets to prevent drift
            robot_left.set_joint_position_target(initial_joint_pos_left)
            robot_right.set_joint_position_target(initial_joint_pos_right)
            robot_left.reset()
            robot_right.reset()
            robot_left.write_data_to_sim()
            robot_right.write_data_to_sim()
            sim.step()
            scene.update(sim.get_physics_dt())

        # 2026-01-07: Verify robot joint positions after reset
        actual_left_joints = robot_left.data.joint_pos[0, :7].cpu().numpy()
        actual_right_joints = robot_right.data.joint_pos[0, :7].cpu().numpy()
        expected_left_joints = initial_joint_pos_left[0, :7].cpu().numpy()
        expected_right_joints = initial_joint_pos_right[0, :7].cpu().numpy()
        left_diff = np.abs(actual_left_joints - expected_left_joints).max()
        right_diff = np.abs(actual_right_joints - expected_right_joints).max()
        print(f"  [Reset] Robot joint diff: L={left_diff:.4f}rad, R={right_diff:.4f}rad")

        # Minimal stabilization steps
        for _ in range(10):
            sim.step()
            scene.update(sim.get_physics_dt())

        # Position verification: check that cable Z and Y positions (endpoints) are close to expected values
        current_z = cable.data.body_state_w[:, :, 2]
        current_min_z = current_z.min().item()
        current_max_z = current_z.max().item()
        z_tolerance = 0.05  # 5cm tolerance

        z_ok = (abs(current_min_z - expected_min_z) < z_tolerance and
                abs(current_max_z - expected_max_z) < z_tolerance)
        nan_ok = check_cable_nan()

        # 2026-01-07: Added Y position verification (check if endpoints are at correct positions)
        # IMPORTANT: Use left_end_idx and right_end_idx, NOT hardcoded 0 and 19!
        # body_state_w indices don't match segment numbers (body_names order is NOT numerical)
        current_body_state = cable.data.body_state_w
        left_y = current_body_state[0, left_end_idx, 1].item()  # Actual left end
        right_y = current_body_state[0, right_end_idx, 1].item()  # Actual right end
        expected_left_y = initial_cable_body_state[0, left_end_idx, 1].item()
        expected_right_y = initial_cable_body_state[0, right_end_idx, 1].item()
        y_tolerance = 0.05  # 5cm tolerance
        y_ok = (abs(left_y - expected_left_y) < y_tolerance and
                abs(right_y - expected_right_y) < y_tolerance)

        print(f"  [Reset] Attempt {attempt+1}: Z={current_min_z:.3f}-{current_max_z:.3f} "
              f"(expected {expected_min_z:.3f}-{expected_max_z:.3f}), "
              f"Z_OK={z_ok}, NaN_OK={nan_ok}")
        print(f"  [Reset] Y endpoints: left={left_y:.3f} (exp {expected_left_y:.3f}), "
              f"right={right_y:.3f} (exp {expected_right_y:.3f}), Y_OK={y_ok}")

        if nan_ok and z_ok and y_ok:
            print(f"  [Reset] Success after {attempt+1} attempt(s)")
            # 2026-01-07: Extended post-reset stabilization to clear accumulated physics state
            # Increased from 50 to 200 steps per Code B recommendation (iteration v7)
            print(f"  [Reset] Post-reset stabilization (200 steps)...")
            for _ in range(200):
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())
            # Verify cable is still valid
            if not check_cable_nan():
                print(f"  [ERROR] Cable NaN after post-reset stabilization!")
                continue  # Try another reset attempt
            # Check velocity
            cable_vel = cable.data.body_state_w[:, :, 7:10]
            max_vel = cable_vel.abs().max().item()
            print(f"  [Reset] Post-stabilization velocity: {max_vel:.6f} m/s")
            return True
        elif not nan_ok:
            print(f"  [WARNING] Cable NaN detected after reset")
            print(f"  [v24.30] Auto-abort: Cable NaN detected. Saving video before exit.")
            sys.stdout.flush()
            finalize_video()  # v24.30: Save video before any exit
            sys.exit(2)
        elif not z_ok:
            print(f"  [WARNING] Cable Z position mismatch (Z diff: "
                  f"min={abs(current_min_z - expected_min_z):.3f}m, "
                  f"max={abs(current_max_z - expected_max_z):.3f}m)")
        elif not y_ok:
            print(f"  [WARNING] Cable Y position mismatch! "
                  f"left: {left_y:.3f} (exp {expected_left_y:.3f}, diff {abs(left_y - expected_left_y):.3f}m), "
                  f"right: {right_y:.3f} (exp {expected_right_y:.3f}, diff {abs(right_y - expected_right_y):.3f}m)")

    print(f"  [ERROR] Reset failed after {max_retries} attempts")
    return False


def get_contact_force() -> tuple:
    """Get contact force from both grippers.

    Returns:
        (left_force, right_force) in Newtons.
    """
    contact_left = scene["contact_left"]
    contact_right = scene["contact_right"]
    contact_left.update(sim.get_physics_dt())
    contact_right.update(sim.get_physics_dt())

    left_force = contact_left.data.net_forces_w[0].norm().item()
    right_force = contact_right.data.net_forces_w[0].norm().item()
    return left_force, right_force


def get_cable_z_str() -> str:
    """H260: Safely get cable Z range string for logging.

    Returns:
        String like "0.750-0.800" or "(no cable)" if cable is None.
    """
    # H260: Use global cable variable (already set at module level based on H239_NO_CABLE_SPAWN)
    global cable
    if cable is None or H239_NO_CABLE_SPAWN:
        return "(no cable)"
    try:
        cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
        return f"{cable_z.min():.3f}-{cable_z.max():.3f}"
    except Exception:
        return "(error)"


def run_cycle(cycle_idx: int):
    """Run one complete cycle and collect demonstration data."""
    global cable  # Required because cable is reassigned inside this function

    print(f"\n{'='*70}")
    print(f"CYCLE {cycle_idx + 1}/{args.num_cycles}")
    print("=" * 70)

    # Reset collector state for new cycle
    collector.prev_joint_pos_left = None
    collector.prev_joint_pos_right = None

    # 2026-01-07: Reset Diff IK controllers at cycle start
    # This clears any accumulated state from previous cycles
    diff_ik_left.reset()
    diff_ik_right.reset()
    print("  [Cycle Reset] Diff IK controllers reset")

    # ============================================================
    # PRE-CYCLE: CABLE STATE VERIFICATION
    # ============================================================
    # H160: Skip cable verification when cable is disabled
    if H160_DISABLE_CABLE:
        print("  [H160] Cable verification SKIPPED (cable disabled)")
        initial_cable_z = -10.0  # Dummy value for disabled cable
    else:
        if not check_cable_nan():
            print("  [WARNING] Cable NaN detected at cycle start, attempting reset...")
            print("  [v24.30] Auto-abort: Cable NaN detected. Saving video before exit.")
            sys.stdout.flush()
            finalize_video()  # v24.30: Save video before any exit
            sys.exit(2)

        # Record initial cable Z for lift measurement
        initial_cable_z = cable.data.root_pos_w[0, 2].item()
        print(f"  [OK] Cable Z at start: {initial_cable_z:.4f}m")

        # 2026-01-07: Detailed cable state logging for Cycle 2 NaN debugging
        cable_pos = cable.data.body_state_w[:, :, :3]
        cable_vel = cable.data.body_state_w[:, :, 7:10]
        max_vel = cable_vel.abs().max().item()
        print(f"  [Cycle {cycle_idx+1}] Cable state after reset:")
        print(f"    Position X: {cable_pos[:,:,0].min().item():.3f}~{cable_pos[:,:,0].max().item():.3f}")
        print(f"    Position Y: {cable_pos[:,:,1].min().item():.3f}~{cable_pos[:,:,1].max().item():.3f}")
        print(f"    Position Z: {cable_pos[:,:,2].min().item():.3f}~{cable_pos[:,:,2].max().item():.3f}")
        print(f"    Max velocity: {max_vel:.6f} m/s")
        if max_vel > 0.01:
            print(f"    [WARNING] Non-zero velocity after reset! (threshold: 0.01 m/s)")
            # Additional stabilization
            print(f"    [Stabilization] Running 100 extra steps...")
            for _ in range(100):
                scene.write_data_to_sim()
                sim.step()
                scene.update(sim.get_physics_dt())
            if not check_cable_nan():
                print(f"    [ERROR] Cable NaN after stabilization!")
                return False
            # Re-check velocity
            cable_vel = cable.data.body_state_w[:, :, 7:10]
            max_vel = cable_vel.abs().max().item()
            print(f"    Max velocity after stabilization: {max_vel:.6f} m/s")

    # ============================================================
    # PHASE 1: APPROACH
    # ============================================================
    # 2026-01-07: Cable endpoint logging per Code B (grasp failure diagnosis)
    # IMPORTANT: Use left_end_idx and right_end_idx, NOT hardcoded 0 and 19!
    # H239: Skip cable endpoint logging when cable is not spawned
    if not H239_NO_CABLE_SPAWN:
        cable_pos = cable.data.body_state_w[:, :, :3]
        left_end_pos = cable_pos[0, left_end_idx, :]   # Actual left end
        right_end_pos = cable_pos[0, right_end_idx, :]  # Actual right end
        print(f"[Cycle {cycle_idx+1}] Cable endpoints before Phase 1:")
        print(f"  {cable.body_names[left_end_idx]} (left):  X={left_end_pos[0].item():.4f}, Y={left_end_pos[1].item():.4f}, Z={left_end_pos[2].item():.4f}")
        print(f"  {cable.body_names[right_end_idx]} (right): X={right_end_pos[0].item():.4f}, Y={right_end_pos[1].item():.4f}, Z={right_end_pos[2].item():.4f}")
        print(f"  Expected Y: left={initial_cable_body_state[0, left_end_idx, 1].item():.3f}, right={initial_cable_body_state[0, right_end_idx, 1].item():.3f}")
    else:
        print(f"[Cycle {cycle_idx+1}] [H239] Cable endpoint logging SKIPPED (no cable)")

    print("\n[Phase 1] Approach...")
    # H120: Use gradual move instead of teleport to avoid 30° violations
    # IMPORTANT: Both robots must be moved simultaneously

    # H230: Swap Phase 1 init joints to match Phase 2 swap (physical arm movement)
    # This ensures continuity: Phase 1 APPROACH → Phase 2 GRASP uses same target sides
    if H230_SWAP_GRASP_COORDS:
        print("  [H230] Phase 1 init joints SWAPPED (Left↔Right) for continuity with Phase 2")
        print(f"    Left arm will use RIGHT_ARM_INIT_JOINTS (target +Y side)")
        print(f"    Right arm will use LEFT_ARM_INIT_JOINTS (target -Y side)")
        p1_left_joints = RIGHT_ARM_INIT_JOINTS  # Left arm goes to +Y (Right's usual position)
        p1_right_joints = LEFT_ARM_INIT_JOINTS  # Right arm goes to -Y (Left's usual position)
    else:
        p1_left_joints = LEFT_ARM_INIT_JOINTS
        p1_right_joints = RIGHT_ARM_INIT_JOINTS

    print("  [H120] Phase 1 initialization with gradual move...")
    gradual_move_both_robots(p1_left_joints, p1_right_joints, GRIPPER_OPEN)

    for i in range(PHASE1_STEPS):
        set_robot_joints(robot_left, p1_left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, p1_right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(1, GRIPPER_OPEN, GRIPPER_OPEN)

    p1_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p1_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p1_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p1_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # 2026-01-07: Gripper-Cable distance check per Code B (grasp failure diagnosis)
    # Use dynamic indices: left arm grasps left end, right arm grasps right end
    # H239: Skip cable distance check when cable is not spawned
    if not H239_NO_CABLE_SPAWN:
        cable_pos = cable.data.body_state_w[:, :, :3]
        left_cable_target = cable_pos[0, left_end_idx, :]   # Left arm grasps left end
        right_cable_target = cable_pos[0, right_end_idx, :]  # Right arm grasps right end
        # H147: Calculate both panda_hand and fingertip distances
        # panda_hand is the Jacobian body, but actual contact point is fingertip
        # which is FINGERTIP_OFFSET (0.1123m) below panda_hand in Z
        left_dist_panda_hand = torch.norm(p1_pos_l[0] - left_cable_target).item()
        right_dist_panda_hand = torch.norm(p1_pos_r[0] - right_cable_target).item()

        # H147: Compute fingertip position (panda_hand Z - FINGERTIP_OFFSET)
        fingertip_pos_l = p1_pos_l.clone()
        fingertip_pos_l[0, 2] -= FINGERTIP_OFFSET
        fingertip_pos_r = p1_pos_r.clone()
        fingertip_pos_r[0, 2] -= FINGERTIP_OFFSET
        left_dist_fingertip = torch.norm(fingertip_pos_l[0] - left_cable_target).item()
        right_dist_fingertip = torch.norm(fingertip_pos_r[0] - right_cable_target).item()

        print(f"[Phase 1] Gripper-Cable distance (H147: both panda_hand and fingertip):")
        print(f"  Left:  panda_hand={left_dist_panda_hand*100:.1f}cm, fingertip={left_dist_fingertip*100:.1f}cm -> {cable.body_names[left_end_idx]}")
        print(f"  Right: panda_hand={right_dist_panda_hand*100:.1f}cm, fingertip={right_dist_fingertip*100:.1f}cm -> {cable.body_names[right_end_idx]}")
        # H150 Option A: Phase-specific warning threshold
        # Phase 1 is hover position (EE_HOVER_HEIGHT=15cm above cable), so 13cm distance is expected
        # Threshold: 15cm for Phase 1 hover, 5cm for Phase 2/3 (strict)
        PHASE1_FINGERTIP_THRESHOLD = 0.15  # 15cm for hover phase
        if left_dist_fingertip > PHASE1_FINGERTIP_THRESHOLD or right_dist_fingertip > PHASE1_FINGERTIP_THRESHOLD:
            print(f"  [WARNING] Large fingertip distance detected! Exceeds Phase 1 hover threshold (15cm)")
    else:
        print("[Phase 1] [H239] Gripper-Cable distance check SKIPPED (no cable)")

    # ============================================================
    # PHASE 2: GRASP (Joint interpolation - same as test_multi_cycle.py)
    # ============================================================
    _p2_start = _time.time()
    _p2_max_seconds = 120  # H198: 2 minute timeout for Phase 2
    print(f"\n[Phase 2] Grasp... (max_steps={PHASE12_STEPS}, max_seconds={_p2_max_seconds})")

    # ============================================================
    # H230: Grasp Coordinate Swap Test (Correct Implementation)
    # Purpose: Diagnose IK asymmetry by physically moving arms to opposite sides
    # Reference: LL-2026-01-30-IMPL-001 (H229 design bug: swapped variables, not arms)
    # Difference from H229:
    #   - H229: Swapped current_pos_l/r variables -> IK saw 500mm position error
    #   - H230: Swap PHASE2 joints -> Arms physically move to opposite sides
    # ============================================================
    if H230_SWAP_GRASP_COORDS:
        print("\n" + "="*70)
        print("[H230] Grasp Coordinate Swap Test ENABLED (Physical Arm Movement)")
        print("  This is the CORRECT swap implementation (vs H229 design bug)")
        print("  Effect: Left arm will move to +Y (Right's usual position)")
        print("          Right arm will move to -Y (Left's usual position)")
        print("  Original PHASE2 joint targets:")
        print(f"    Left arm:  PHASE2_LEFT_JOINTS  (Y=-0.25 target)")
        print(f"    Right arm: PHASE2_RIGHT_JOINTS (Y=+0.25 target)")
        print("  SWAPPED PHASE2 joint targets:")
        print(f"    Left arm:  will use PHASE2_RIGHT_JOINTS (move to Y=+0.25)")
        print(f"    Right arm: will use PHASE2_LEFT_JOINTS  (move to Y=-0.25)")
        print("  Diagnostic interpretation after Phase 3:")
        print("    - If Left arm (now at +Y) FAILS: Left arm has intrinsic IK issue")
        print("    - If Right arm (now at -Y) FAILS: -Y position has workspace issue")
        print("    - If BOTH succeed: Original issue was grasp force asymmetry")
        print("="*70 + "\n")
        sys.stdout.flush()
        # Swap joint targets: Left arm uses Right's joints, Right arm uses Left's joints
        p2_left_joints = PHASE2_RIGHT_JOINTS   # Left arm moves to +Y (Right's position)
        p2_right_joints = PHASE2_LEFT_JOINTS   # Right arm moves to -Y (Left's position)
    else:
        # Normal operation
        p2_left_joints = PHASE2_LEFT_JOINTS
        p2_right_joints = PHASE2_RIGHT_JOINTS

    # Phase 2 approach: Joint interpolation from INIT to PHASE2 joints
    # (This method works in test_multi_cycle.py with 27N contact force)
    # H230: Use consistent start joints matching Phase 1 swap
    if H230_SWAP_GRASP_COORDS:
        p2_start_left_joints = RIGHT_ARM_INIT_JOINTS   # Left arm started at Right's init
        p2_start_right_joints = LEFT_ARM_INIT_JOINTS   # Right arm started at Left's init
    else:
        p2_start_left_joints = LEFT_ARM_INIT_JOINTS
        p2_start_right_joints = RIGHT_ARM_INIT_JOINTS

    for step in range(PHASE12_STEPS):
        alpha = (step + 1) / PHASE12_STEPS
        left_joints = [l + alpha * (p - l) for l, p in zip(p2_start_left_joints, p2_left_joints)]
        right_joints = [l + alpha * (p - l) for l, p in zip(p2_start_right_joints, p2_right_joints)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, GRIPPER_OPEN, GRIPPER_OPEN)
        # H198: Heartbeat every 50 steps
        if step % 50 == 0:
            _p2_elapsed = _time.time() - _p2_start
            print(f"  [H198 heartbeat] Phase2 step={step}/{PHASE12_STEPS}, elapsed={_p2_elapsed:.1f}s, alpha={alpha:.3f}")
            sys.stdout.flush()
            if _p2_elapsed >= _p2_max_seconds:
                print(f"  [H198 HANG_TIMEOUT] Phase2 max_seconds={_p2_max_seconds} exceeded at step={step}")
                raise TimeoutError(f"Phase2: wall-time {_p2_elapsed:.1f}s >= {_p2_max_seconds}s")

    # Grasp: Close grippers with contact force feedback control
    # 2026-01-07 v2: Lowered target force for more stable grasp
    # Previous: 25N target led to 30-37N after stabilization → NaN at 18.5%
    # H218: Increased from 20N to 30N (LL-2026-01-30-GRIP-001: cable compliance causes 50% force reduction)
    # H219: Further increase 30N→40N based on H218 results (peak only reached 50-57% of target)
    # H225: REDUCED 40N→25N - Code B hypothesis: high grip force causes Left arm IK constraint
    #       Evidence: H224 Left arm +4mm (vs Right +15mm), cable_Z left end unchanged
    #       Ref: R335, LL-2026-01-30-IK-003
    TARGET_CONTACT_FORCE = 25.0  # N - H225: reduced to test Left arm constraint hypothesis
    MAX_CONTACT_FORCE = 35.0     # N - H225: reduced accordingly
    MAX_GRASP_STEPS = 200        # Double the steps for safer closing

    print(f"  [Grasp] Closing grippers: {GRIPPER_OPEN} -> {GRIPPER_CLOSE} over {MAX_GRASP_STEPS} steps (max)")
    print(f"  [Grasp] Target force: {TARGET_CONTACT_FORCE}N, Max: {MAX_CONTACT_FORCE}N")

    grip_val_left = GRIPPER_OPEN
    grip_val_right = GRIPPER_OPEN
    grip_step = (GRIPPER_OPEN - GRIPPER_CLOSE) / MAX_GRASP_STEPS  # Slower closing
    grasp_complete = False

    for i in range(MAX_GRASP_STEPS):
        # Get current contact forces
        left_force, right_force = get_contact_force()

        # Check if target force reached on both grippers
        if left_force >= TARGET_CONTACT_FORCE and right_force >= TARGET_CONTACT_FORCE:
            print(f"    [Step {i+1}] Target force reached: L={left_force:.1f}N, R={right_force:.1f}N")
            grasp_complete = True
            break

        # Handle excessive force - relax grip slightly
        if right_force > MAX_CONTACT_FORCE:
            grip_val_right = min(GRIPPER_OPEN, grip_val_right + 0.001)
            print(f"    [Step {i+1}] Relaxing RIGHT grip (force={right_force:.1f}N)")
        else:
            grip_val_right = max(GRIPPER_CLOSE, grip_val_right - grip_step)

        if left_force > MAX_CONTACT_FORCE:
            grip_val_left = min(GRIPPER_OPEN, grip_val_left + 0.001)
            print(f"    [Step {i+1}] Relaxing LEFT grip (force={left_force:.1f}N)")
        else:
            grip_val_left = max(GRIPPER_CLOSE, grip_val_left - grip_step)

        # Apply gripper positions (use swapped joints if H230 enabled)
        set_robot_joints(robot_left, p2_left_joints, grip_val_left)
        set_robot_joints(robot_right, p2_right_joints, grip_val_right)
        sim.step()
        scene.update(sim.get_physics_dt())

        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, grip_val_left, grip_val_right)
        if i % 50 == 0:
            print(f"    [Step {i+1}/{MAX_GRASP_STEPS}] grip_L={grip_val_left:.4f}, grip_R={grip_val_right:.4f}, force_L={left_force:.1f}N, force_R={right_force:.1f}N")

    if not grasp_complete:
        print(f"  [Grasp] Max steps reached without target force")

    # Stabilize: Hold position with CONTINUOUS force monitoring
    # 2026-01-07 v2: Force monitoring during stabilization to prevent force buildup
    final_grip_left = grip_val_left
    final_grip_right = grip_val_right
    RELAX_STEP = 0.0005  # How much to relax grip when force is too high
    MIN_GRIP = GRIPPER_CLOSE  # Don't relax beyond minimum grip
    force_warnings = 0

    stabilize_start_time = _time.time()
    for i in range(GRASP_STABILIZE):
        # H201: Heartbeat for hang detection with flush (per LL-2026-01-25-HANG-003)
        if i % 10 == 0:
            stabilize_elapsed = _time.time() - stabilize_start_time
            print(f"    [H201 heartbeat] Stabilize step={i}/{GRASP_STABILIZE}, elapsed={stabilize_elapsed:.1f}s")
            sys.stdout.flush()

        # Monitor contact force during stabilization
        if i % 10 == 0:  # Check every 10 steps
            left_force, right_force = get_contact_force()

            # Relax grip if force exceeds limit
            if right_force > MAX_CONTACT_FORCE:
                final_grip_right = min(GRIPPER_OPEN, final_grip_right + RELAX_STEP)
                if force_warnings < 5:  # Limit log spam
                    print(f"    [Stabilize {i}] Relaxing RIGHT: force={right_force:.1f}N, grip→{final_grip_right:.4f}")
                force_warnings += 1

            if left_force > MAX_CONTACT_FORCE:
                final_grip_left = min(GRIPPER_OPEN, final_grip_left + RELAX_STEP)
                if force_warnings < 5:
                    print(f"    [Stabilize {i}] Relaxing LEFT: force={left_force:.1f}N, grip→{final_grip_left:.4f}")
                force_warnings += 1

        set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, final_grip_left)
        set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, final_grip_right)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(2, final_grip_left, final_grip_right)

    if force_warnings > 0:
        print(f"    [Stabilize] Total force warnings: {force_warnings}")

    # ============================================================
    # PHASE 2 VERIFICATION: Contact Force
    # ============================================================
    left_force, right_force = get_contact_force()
    print(f"  [Verify] Contact force: L={left_force:.1f}N, R={right_force:.1f}N")
    # 2026-01-07: Critical grasp verification per Code B
    # H208: Skip force check when cable is disabled (no grasp target)
    if H160_DISABLE_CABLE:
        print(f"  [H208] Grasp force check SKIPPED (cable disabled, no grasp target)")
    # H217: Threshold relaxed from 10N to 5N for cable-enabled mode
    # Rationale: LL-2026-01-30-GRIP-001 - cable compliance causes ~50% force reduction
    elif left_force < 5 or right_force < 5:
        print(f"  [ERROR] Grasp failed! L={left_force:.1f}N, R={right_force:.1f}N")
        print(f"  [ERROR] Aborting cycle - contact force below 5N threshold (H217)")
        print(f"         Expected: 5-25N for stable grasp")
        return False  # Abort this cycle
    elif left_force > 25 or right_force > 25:
        print(f"  [WARNING] High contact force detected (recommended: 10-25N)")
        print(f"           High force may cause instability in later phases")

    # Check cable NaN after grasp
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after grasp phase!")

    p2_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p2_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p2_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p2_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # ============================================================
    # H150 Option C: Phase 2 EE Position and Fingertip-Cable Distance Logging
    # ============================================================
    print(f"\n[H150] Phase 2 EE Position (panda_hand):")
    print(f"  Left:  ({p2_pos_l[0,0]:.4f}, {p2_pos_l[0,1]:.4f}, {p2_pos_l[0,2]:.4f})")
    print(f"  Right: ({p2_pos_r[0,0]:.4f}, {p2_pos_r[0,1]:.4f}, {p2_pos_r[0,2]:.4f})")

    # Calculate fingertip positions (panda_hand Z - FINGERTIP_OFFSET)
    p2_fingertip_l = p2_pos_l.clone()
    p2_fingertip_l[0, 2] -= FINGERTIP_OFFSET
    p2_fingertip_r = p2_pos_r.clone()
    p2_fingertip_r[0, 2] -= FINGERTIP_OFFSET
    print(f"[H150] Phase 2 Fingertip Position:")
    print(f"  Left:  ({p2_fingertip_l[0,0]:.4f}, {p2_fingertip_l[0,1]:.4f}, {p2_fingertip_l[0,2]:.4f})")
    print(f"  Right: ({p2_fingertip_r[0,0]:.4f}, {p2_fingertip_r[0,1]:.4f}, {p2_fingertip_r[0,2]:.4f})")

    # Calculate fingertip-cable distance for Phase 2 (strict 5cm threshold)
    # H239: Skip cable distance check when cable is not spawned
    if not H239_NO_CABLE_SPAWN:
        cable_pos_p2 = cable.data.body_state_w[:, :, :3]
        left_cable_p2 = cable_pos_p2[0, left_end_idx, :]
        right_cable_p2 = cable_pos_p2[0, right_end_idx, :]
        p2_dist_fingertip_l = torch.norm(p2_fingertip_l[0] - left_cable_p2).item()
        p2_dist_fingertip_r = torch.norm(p2_fingertip_r[0] - right_cable_p2).item()
        print(f"[H150] Phase 2 Fingertip-Cable Distance:")
        print(f"  Left:  {p2_dist_fingertip_l*100:.2f}cm, Right: {p2_dist_fingertip_r*100:.2f}cm")

        # H150: Phase 2/3 uses strict 5cm threshold (grasp should be close to cable)
        PHASE23_FINGERTIP_THRESHOLD = 0.05  # 5cm strict threshold for grasp phases
        if p2_dist_fingertip_l > PHASE23_FINGERTIP_THRESHOLD or p2_dist_fingertip_r > PHASE23_FINGERTIP_THRESHOLD:
            print(f"  [H150 WARNING] Fingertip distance > 5cm threshold in Phase 2!")
            print(f"  [v24.30] Auto-abort: H150 fingertip distance threshold exceeded. Saving video before exit.")
            sys.stdout.flush()
            finalize_video()  # v24.30: Save video before any exit
            sys.exit(1)
        else:
            print(f"  [H150] Phase 2 fingertip distance OK (both <= 5cm)")

        # ============================================================
        # PHASE 2→3 TRANSITION DIAGNOSTICS
        # ============================================================
        print("\n" + "="*70)
        print("[Phase 2→3 Transition] Detailed cable state before lift:")
        cable_pos = cable.data.body_pos_w[0].cpu().numpy()  # [CABLE_SEGMENT_COUNT, 3]
        cable_vel = cable.data.body_lin_vel_w[0].cpu().numpy()  # [CABLE_SEGMENT_COUNT, 3]
        speeds = np.linalg.norm(cable_vel, axis=1)
        # H240: Dynamic segment indices based on CABLE_SEGMENT_COUNT (10 or 20 segments)
        # For 10 segments: grasp points are at ends [0,1] and [8,9]
        # For 20 segments: grasp points were at [16,17,18,19]
        n_seg = CABLE_SEGMENT_COUNT
        grasp_segments = list(range(max(0, n_seg - 4), n_seg))  # Last 4 segments (or all if < 4)
        for seg_idx in grasp_segments:
            print(f"  seg_{seg_idx}: pos=({cable_pos[seg_idx, 0]:.4f}, {cable_pos[seg_idx, 1]:.4f}, {cable_pos[seg_idx, 2]:.4f}), "
                  f"vel=({cable_vel[seg_idx, 0]:.4f}, {cable_vel[seg_idx, 1]:.4f}, {cable_vel[seg_idx, 2]:.4f}), speed={speeds[seg_idx]:.4f} m/s")
        print(f"  Max segment speed: {speeds.max():.4f} m/s (seg_{np.argmax(speeds)})")
        print(f"  Contact force: L={left_force:.1f}N, R={right_force:.1f}N")
        print("="*70)
    else:
        print("[H239] Phase 2 fingertip-cable distance check SKIPPED (no cable)")
        print("[H239] Phase 2→3 transition diagnostics SKIPPED (no cable)")

    # ============================================================
    # H227: EARLY EXIT AFTER PHASE 2 (Hang Isolation Test)
    # Purpose: Isolate Phase 3 Lift hang by terminating after Phase 2 completion
    # Reference: LL-2026-01-30-BUG-001 (Phase 3 Lift hang with no output for 13+ minutes)
    # ============================================================
    if H227_EARLY_EXIT_AFTER_PHASE2:
        print("\n" + "="*70)
        print("[H227] Early Exit After Phase 2 (Hang Isolation Test)")
        print(f"  Phase 1-2 completed successfully")
        print(f"  Contact force: L={left_force:.1f}N, R={right_force:.1f}N")
        print(f"  Cable grasped: {left_force > 0.5 and right_force > 0.5}")
        print("="*70)

        # Return cycle result without proceeding to Phase 3
        # This allows video flush and HDF5 close to happen properly
        return {
            "status": "H227_EARLY_EXIT",
            "phase_reached": 2,
            "left_force": left_force,
            "right_force": right_force,
            "cable_grasped": left_force > 0.5 and right_force > 0.5,
        }

    # ============================================================
    # GATE-G: Grasp check before Phase 3 (v24.82)
    # ============================================================
    if ENABLE_GATE_SYSTEM and GATE_G_ENABLED:
        # Use contact force as proxy for grasp success
        # If force > 0.5N, gripper is closed around cable
        grasp_force_threshold = 0.5  # N

        # H260: Skip force check when no cable (PG0 kinematics test)
        if H239_NO_CABLE_SPAWN:
            grasp_ok = True  # No cable to grasp, pass kinematics check
            print("[GATE-G] Force check SKIPPED (no cable, PG0 mode)")
        else:
            grasp_ok = left_force > grasp_force_threshold and right_force > grasp_force_threshold

        # Fingertip-cable distance (if cable exists)
        if not H239_NO_CABLE_SPAWN:
            max_fingertip_dist = max(p2_dist_fingertip_l, p2_dist_fingertip_r)
        else:
            max_fingertip_dist = 0.0  # No cable, assume OK

        g_ok = grasp_ok and max_fingertip_dist < GATE_G_FINGERTIP_CABLE_DIST_MAX

        log_gate_eval("Gate-G", "2", g_ok,
                      {"left_force": left_force, "right_force": right_force,
                       "max_fingertip_dist": max_fingertip_dist, "grasp_ok": grasp_ok},
                      {"force_threshold": grasp_force_threshold,
                       "fingertip_cable_dist_max": GATE_G_FINGERTIP_CABLE_DIST_MAX})

        if not g_ok:
            print(f"[GATE-G] FAILED: grasp_ok={grasp_ok}, max_fingertip_dist={max_fingertip_dist*100:.1f}cm")
            finalize_video()  # v24.30: Save video before exit
            return early_exit("Gate-G", "2",
                             {"left_force": left_force, "right_force": right_force,
                              "max_fingertip_dist": max_fingertip_dist},
                             "FAIL")
        else:
            print(f"[GATE-G] PASSED: force L={left_force:.1f}N R={right_force:.1f}N, fingertip_dist={max_fingertip_dist*100:.1f}cm")

    # ============================================================
    # H268: Reduce viewport update frequency for Phase 3 HANG prevention
    # Reference: LL-2026-02-01-HANG-001, LL-2026-01-31-PIVOT-001
    # Root cause: 13 consecutive Phase 3 hangs traced to viewport/timeline processing
    # Solution: Increase render_interval from 2 to 10 (80% reduction in viewport updates)
    # ============================================================
    _h268_original_render_interval = sim.cfg.render_interval
    sim.cfg.render_interval = H268_PHASE3_RENDER_INTERVAL
    print(f"[H268] render_interval: {_h268_original_render_interval} -> {H268_PHASE3_RENDER_INTERVAL} (viewport HANG prevention)")

    # ============================================================
    # PHASE 3: LIFT (H147: 3-step incremental approach)
    # H157: Reverted to H154 Z-only lift (removed H155/H156 X offset)
    # Split 10cm lift into 10 × 1cm steps for better IK tracking (H151)
    # H209: Added 10-minute timeout to handle I/O bottleneck
    # ============================================================
    _p3_start = _time.time()
    _p3_max_seconds = 600  # H209: 10-minute timeout (was causing timeout at 2min due to PNG I/O)
    print(f"\n[Phase 3] Lift ({LIFT_CM}cm) - H157: Z-only lift (H209: timeout={_p3_max_seconds}s)...")
    H147_NUM_LIFT_STEPS = 6  # H222: Increase to 6 steps (1.67cm each) for smoother IK tracking
    H147_LIFT_INCREMENT = LIFT_CM / H147_NUM_LIFT_STEPS / 100.0  # ~1cm in meters
    H147_STABILIZE_STEPS = 50  # Stabilization steps between increments
    H147_STEPS_PER_INCREMENT = LIFT_STEPS // H147_NUM_LIFT_STEPS  # Distribute total steps

    # Start from Phase 2 end positions
    current_pos_l = p2_pos_l.clone()
    current_pos_r = p2_pos_r.clone()
    current_quat_l = p2_quat_l.clone()
    current_quat_r = p2_quat_r.clone()

    # ============================================================
    # H229: Left/Right Target Swap Test
    # Purpose: Diagnose IK asymmetry by swapping lift targets
    # Reference: LL-2026-01-30-IK-003, LL-2026-01-30-IK-004
    #   - H228 showed Left arm Z tracking 24% vs Right arm 88%
    #   - This test swaps the lift targets to isolate arm vs position dependency
    # ============================================================
    if H229_SWAP_LR_TARGETS:
        print("\n" + "="*70)
        print("[H229] Left/Right Target Swap Test ENABLED")
        print("  Original Phase 2 end positions:")
        print(f"    Left arm:  ({current_pos_l[0,0].item():.4f}, {current_pos_l[0,1].item():.4f}, {current_pos_l[0,2].item():.4f})")
        print(f"    Right arm: ({current_pos_r[0,0].item():.4f}, {current_pos_r[0,1].item():.4f}, {current_pos_r[0,2].item():.4f})")

        # Swap XY coordinates between arms
        # Left arm will lift from Right arm's XY position
        # Right arm will lift from Left arm's XY position
        orig_x_l = current_pos_l[0, 0].item()
        orig_y_l = current_pos_l[0, 1].item()
        orig_x_r = current_pos_r[0, 0].item()
        orig_y_r = current_pos_r[0, 1].item()

        current_pos_l[0, 0] = orig_x_r  # Left arm gets Right's X
        current_pos_l[0, 1] = orig_y_r  # Left arm gets Right's Y
        current_pos_r[0, 0] = orig_x_l  # Right arm gets Left's X
        current_pos_r[0, 1] = orig_y_l  # Right arm gets Left's Y

        print("  Swapped lift targets:")
        print(f"    Left arm:  ({current_pos_l[0,0].item():.4f}, {current_pos_l[0,1].item():.4f}, {current_pos_l[0,2].item():.4f}) <- was Right's XY")
        print(f"    Right arm: ({current_pos_r[0,0].item():.4f}, {current_pos_r[0,1].item():.4f}, {current_pos_r[0,2].item():.4f}) <- was Left's XY")
        print("  Diagnostic interpretation:")
        print("    - If Left arm (now at +Y) FAILS: Left arm has intrinsic IK issue")
        print("    - If Right arm (now at -Y) FAILS: -Y position has workspace issue")
        print("    - If BOTH succeed: Original issue was grasp force asymmetry")
        print("    - If BOTH fail: Both arm and position issues exist")
        print("="*70 + "\n")
        sys.stdout.flush()

    for lift_step in range(H147_NUM_LIFT_STEPS):
        step_target_l = current_pos_l.clone()
        step_target_l[0, 2] += H147_LIFT_INCREMENT
        step_target_r = current_pos_r.clone()
        step_target_r[0, 2] += H147_LIFT_INCREMENT

        # v199: Detailed log before each lift step (for hang diagnosis at lift_step=9)
        _p3_pre_lift_elapsed = _time.time() - _p3_start
        print(f"  [H147] Lift step {lift_step+1}/{H147_NUM_LIFT_STEPS}: +{H147_LIFT_INCREMENT*100:.1f}cm")
        print(f"    [v199] Pre-lift state: elapsed={_p3_pre_lift_elapsed:.1f}s, watchdog={_v199_watchdog_timeout}s")
        print(f"    [v199] Current EE L=({current_pos_l[0,0]:.4f},{current_pos_l[0,1]:.4f},{current_pos_l[0,2]:.4f})")
        print(f"    [v199] Current EE R=({current_pos_r[0,0]:.4f},{current_pos_r[0,1]:.4f},{current_pos_r[0,2]:.4f})")
        print(f"    [v199] Target EE L Z={step_target_l[0,2]:.4f}, R Z={step_target_r[0,2]:.4f}")
        sys.stdout.flush()

        # Run IK motion for this increment
        # H206: Apply ramp-up only for first lift step (lift_step == 0)
        # Subsequent steps skip ramp-up to maintain continuous velocity
        result_pos_l, result_pos_r, result_quat_l, result_quat_r = run_diff_ik_motion_with_collection(
            current_pos_l, current_pos_r, current_quat_l, current_quat_r,
            step_target_l, step_target_r, H147_STEPS_PER_INCREMENT, GRIPPER_CLOSE, phase=3,
            skip_ramp_up=(lift_step > 0)
        )

        # H147: Log IK tracking performance for each step
        actual_z_l = robot_left.data.body_pos_w[0, jacobian_body_left, 2].item()
        actual_z_r = robot_right.data.body_pos_w[0, jacobian_body_right, 2].item()
        target_z_l = step_target_l[0, 2].item()
        target_z_r = step_target_r[0, 2].item()
        tracking_error_l = abs(actual_z_l - target_z_l) * 1000  # mm
        tracking_error_r = abs(actual_z_r - target_z_r) * 1000  # mm
        tracking_rate_l = min(100, (1 - tracking_error_l / (H147_LIFT_INCREMENT * 1000)) * 100) if H147_LIFT_INCREMENT > 0 else 100
        tracking_rate_r = min(100, (1 - tracking_error_r / (H147_LIFT_INCREMENT * 1000)) * 100) if H147_LIFT_INCREMENT > 0 else 100

        print(f"    IK tracking: L={tracking_rate_l:.1f}% (err={tracking_error_l:.1f}mm), R={tracking_rate_r:.1f}% (err={tracking_error_r:.1f}mm)")

        if tracking_error_l > 5 or tracking_error_r > 5:
            print(f"    [WARNING] IK tracking error > 5mm threshold!")

        # H209: Heartbeat and timeout check after each lift step
        _p3_elapsed = _time.time() - _p3_start
        print(f"    [H209 heartbeat] Phase3 lift_step={lift_step+1}/{H147_NUM_LIFT_STEPS}, elapsed={_p3_elapsed:.1f}s")
        sys.stdout.flush()
        if _p3_elapsed >= _p3_max_seconds:
            print(f"    [H209 HANG_TIMEOUT] Phase3 max_seconds={_p3_max_seconds} exceeded at lift_step={lift_step+1}")
            print(f"    [v24.30] Auto-abort: Saving video before exit.")
            sys.stdout.flush()
            finalize_video()
            raise TimeoutError(f"Phase3: wall-time {_p3_elapsed:.1f}s >= {_p3_max_seconds}s")

        # H228: Early Exit after specified lift steps (Hang Position Isolation)
        # Purpose: Identify exact hang position within Phase 3 Lift
        if H228_EARLY_EXIT_AFTER_PHASE3_START and (lift_step + 1) >= H228_PHASE3_EARLY_EXIT_STEPS:
            print(f"\n[H228] Early Exit after Phase 3 lift step {lift_step+1}/{H147_NUM_LIFT_STEPS}")
            print(f"  [H228] Purpose: Hang position isolation - Phase 3 start verified")
            print(f"  [H228] Elapsed time: {_p3_elapsed:.1f}s")
            print(f"  [H228] EE Position after lift_step {lift_step+1}:")
            print(f"    L=({current_pos_l[0,0]:.4f}, {current_pos_l[0,1]:.4f}, {current_pos_l[0,2]:.4f})")
            print(f"    R=({current_pos_r[0,0]:.4f}, {current_pos_r[0,1]:.4f}, {current_pos_r[0,2]:.4f})")
            sys.stdout.flush()
            # Return partial Phase 3 result
            return {
                "status": "H228_EARLY_EXIT",
                "lift_steps_completed": lift_step + 1,
                "elapsed_seconds": _p3_elapsed,
                "ee_pos_l": (current_pos_l[0,0].item(), current_pos_l[0,1].item(), current_pos_l[0,2].item()),
                "ee_pos_r": (current_pos_r[0,0].item(), current_pos_r[0,1].item(), current_pos_r[0,2].item()),
            }

        # Stabilization steps (hold position)
        if lift_step < H147_NUM_LIFT_STEPS - 1:
            for _ in range(H147_STABILIZE_STEPS):
                sim.step()
                scene.update(sim.get_physics_dt())

        # Update current positions for next step
        current_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
        current_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
        current_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
        current_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Final positions after all lift steps
    p3_pos_l = current_pos_l
    p3_pos_r = current_pos_r
    p3_quat_l = current_quat_l
    p3_quat_r = current_quat_r

    # ============================================================
    # PHASE 3 VERIFICATION: Lift Distance and Force
    # ============================================================
    left_force_lift, right_force_lift = get_contact_force()
    print(f"  [Force] After lift: L={left_force_lift:.1f}N, R={right_force_lift:.1f}N")

    # H204: Skip cable-dependent verification when cable is disabled
    if H160_DISABLE_CABLE:
        print("  [H204] Cable verification SKIPPED (cable disabled)")
        print("  [H204] EE-only lift verification:")
        ee_z_l = robot_left.data.body_pos_w[0, jacobian_body_left, 2].item()
        ee_z_r = robot_right.data.body_pos_w[0, jacobian_body_right, 2].item()
        print(f"  [H204] EE Z: L={ee_z_l:.4f}m, R={ee_z_r:.4f}m")
    else:
        # Measure cable lift using grasped segments (endpoints)
        # cable.data.body_pos_w shape: [num_envs, num_bodies, 3]
        # Use dynamic indices from initialization
        left_end_z = cable.data.body_pos_w[0, left_end_idx, 2].item()
        right_end_z = cable.data.body_pos_w[0, right_end_idx, 2].item()
        grasped_z = (left_end_z + right_end_z) / 2
        lift_distance = grasped_z - initial_cable_z
        print(f"  [Verify] Lift distance: {lift_distance*100:.1f}cm (target: {LIFT_CM}cm)")
        print(f"  [Debug] {cable.body_names[left_end_idx]} Z: {left_end_z:.4f}m, {cable.body_names[right_end_idx]} Z: {right_end_z:.4f}m")

        # Debug: EE position after lift
        ee_z_l = robot_left.data.body_pos_w[0, jacobian_body_left, 2].item()
        ee_z_r = robot_right.data.body_pos_w[0, jacobian_body_right, 2].item()
        print(f"  [Debug] EE Z: L={ee_z_l:.4f}m, R={ee_z_r:.4f}m")

        # H150 Option C: Phase 3 EE Position and Fingertip-Cable Distance Logging
        p3_ee_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        p3_ee_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right]
        print(f"\n[H150] Phase 3 EE Position (panda_hand):")
        print(f"  Left:  ({p3_ee_pos_l[0,0]:.4f}, {p3_ee_pos_l[0,1]:.4f}, {p3_ee_pos_l[0,2]:.4f})")
        print(f"  Right: ({p3_ee_pos_r[0,0]:.4f}, {p3_ee_pos_r[0,1]:.4f}, {p3_ee_pos_r[0,2]:.4f})")

        # Calculate fingertip positions for Phase 3
        p3_fingertip_l = p3_ee_pos_l.clone()
        p3_fingertip_l[0, 2] -= FINGERTIP_OFFSET
        p3_fingertip_r = p3_ee_pos_r.clone()
        p3_fingertip_r[0, 2] -= FINGERTIP_OFFSET
        print(f"[H150] Phase 3 Fingertip Position:")
        print(f"  Left:  ({p3_fingertip_l[0,0]:.4f}, {p3_fingertip_l[0,1]:.4f}, {p3_fingertip_l[0,2]:.4f})")
        print(f"  Right: ({p3_fingertip_r[0,0]:.4f}, {p3_fingertip_r[0,1]:.4f}, {p3_fingertip_r[0,2]:.4f})")

        # Calculate fingertip-cable distance for Phase 3
        cable_pos_p3 = cable.data.body_state_w[:, :, :3]
        left_cable_p3 = cable_pos_p3[0, left_end_idx, :]
        right_cable_p3 = cable_pos_p3[0, right_end_idx, :]
        p3_dist_fingertip_l = torch.norm(p3_fingertip_l[0] - left_cable_p3).item()
        p3_dist_fingertip_r = torch.norm(p3_fingertip_r[0] - right_cable_p3).item()
        print(f"[H150] Phase 3 Fingertip-Cable Distance:")
        print(f"  Left:  {p3_dist_fingertip_l*100:.2f}cm, Right: {p3_dist_fingertip_r*100:.2f}cm")

        if lift_distance < LIFT_VERIFY_THRESHOLD:
            print(f"  [WARNING] Lift too low ({lift_distance*100:.1f}cm < {LIFT_VERIFY_THRESHOLD*100:.1f}cm) - possible grasp failure")
            print(f"  [v24.30] Auto-abort: Lift too low detected. Saving video before exit.")
            sys.stdout.flush()
            finalize_video()  # v24.30: Save video before any exit
            sys.exit(1)

        # Check cable NaN after lift
        if not check_cable_nan():
            print("  [ERROR] Cable NaN after lift phase!")

    # H212: Early exit for --max_phase option (Phase 3 short test)
    if args.max_phase <= 3:
        # Get current EE positions for reporting
        _exit_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
        _exit_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
        print(f"\n[H212] --max_phase={args.max_phase}: Exiting after Phase 3 (Lift) completion")
        print(f"  Phase 3 completed successfully:")
        print(f"  - Lift distance: {lift_distance*100:.1f}cm")
        print(f"  - EE Z positions: L={_exit_pos_l[0,2].item():.3f}m, R={_exit_pos_r[0,2].item():.3f}m")
        print(f"  Saving video and finalizing...")
        sys.stdout.flush()
        finalize_video()
        print(f"✅ Phase 3 test completed successfully. Exiting with code 0.")
        sys.exit(0)

    # ============================================================
    # H268: Restore original render_interval after Phase 3
    # ============================================================
    sim.cfg.render_interval = _h268_original_render_interval
    print(f"[H268] render_interval restored: {H268_PHASE3_RENDER_INTERVAL} -> {_h268_original_render_interval}")

    # ============================================================
    # GATE-L: Lift check before Phase 4 (v24.82)
    # ============================================================
    if ENABLE_GATE_SYSTEM and GATE_L_ENABLED:
        # Get current EE Z positions
        gate_l_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
        gate_l_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
        current_z_l = gate_l_pos_l[0, 2].item()
        current_z_r = gate_l_pos_r[0, 2].item()

        # Initial Z was at Phase 2 end (p2_pos_l/r)
        initial_z_l = p2_pos_l[0, 2].item()
        initial_z_r = p2_pos_r[0, 2].item()

        lift_dz_l = current_z_l - initial_z_l
        lift_dz_r = current_z_r - initial_z_r
        min_lift_dz = min(lift_dz_l, lift_dz_r)

        l_ok = min_lift_dz > GATE_L_LIFT_DZ_MIN

        log_gate_eval("Gate-L", "3", l_ok,
                      {"lift_dz_l": lift_dz_l, "lift_dz_r": lift_dz_r,
                       "min_lift_dz": min_lift_dz, "current_z_l": current_z_l, "current_z_r": current_z_r},
                      {"lift_dz_min": GATE_L_LIFT_DZ_MIN})

        if not l_ok:
            print(f"[GATE-L] FAILED: min_lift_dz={min_lift_dz*100:.1f}cm < {GATE_L_LIFT_DZ_MIN*100:.1f}cm")
            finalize_video()  # v24.30: Save video before exit
            return early_exit("Gate-L", "3",
                             {"lift_dz_l": lift_dz_l, "lift_dz_r": lift_dz_r, "min_lift_dz": min_lift_dz},
                             "FAIL")
        else:
            print(f"[GATE-L] PASSED: lift L={lift_dz_l*100:.1f}cm R={lift_dz_r*100:.1f}cm (min={min_lift_dz*100:.1f}cm > {GATE_L_LIFT_DZ_MIN*100:.1f}cm)")

    # ============================================================
    # PHASE 4: Lift higher before rotation
    # 2026-01-06: NaN occurred when inter-arm distance shrank during rotation (51cm -> 39cm)
    # Solution: Lift higher to provide more cable slack
    # ============================================================
    print("\n[Phase 4] Pre-rotation lift using Diff IK...")
    # 2026-01-07: PRE_ROTATION_Z=1.05m (original value)
    # Accounting for ~10cm cable sag: cable lowest point Z~0.95 > hook top Z=0.90
    # Margin: ~5cm (0.95-0.90)
    # Note: 1.10/1.15m exceeds right arm IK reachability limit (Z~1.035m), causing tracking failure
    PRE_ROTATION_Z = 1.05

    # Get current EE positions after Phase 3 lift
    p3_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p3_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p3_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p3_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
    print(f"  Start EE: L=({p3_pos_l[0,0]:.3f}, {p3_pos_l[0,1]:.3f}, {p3_pos_l[0,2]:.3f})")
    print(f"           R=({p3_pos_r[0,0]:.3f}, {p3_pos_r[0,1]:.3f}, {p3_pos_r[0,2]:.3f})")

    # H210: Dynamically compute Phase 4 target Z (Phase 3 end position + 2cm)
    # Rationale: LL-2026-01-25-CFG-002 (H209 had PHASE4_LIFT_TARGET_Z=0.90m < Phase 3 end 0.961m, causing a descent request)
    # Fix: Use dynamic calculation based on Phase 3 end position instead of hardcoded value
    # +2cm is achievable (Phase 3 achieved 10cm/320steps, Phase 4 has 1200steps)
    PHASE4_LIFT_MARGIN = 0.02  # 2cm margin above Phase 3 end
    p3_end_z = max(p3_pos_l[0,2].item(), p3_pos_r[0,2].item())
    PHASE4_LIFT_TARGET_Z = p3_end_z + PHASE4_LIFT_MARGIN
    print(f"  H210: Dynamic target Z = Phase 3 end ({p3_end_z:.3f}m) + {PHASE4_LIFT_MARGIN}m = {PHASE4_LIFT_TARGET_Z:.3f}m")

    # Lift target: same XY, higher Z (H210: dynamic calculation based on Phase 3 end)
    p4_lift_l = torch.tensor([[p3_pos_l[0,0].item(), p3_pos_l[0,1].item(), PHASE4_LIFT_TARGET_Z]], device=device)
    p4_lift_r = torch.tensor([[p3_pos_r[0,0].item(), p3_pos_r[0,1].item(), PHASE4_LIFT_TARGET_Z]], device=device)
    print(f"  Lift target Z: {PHASE4_LIFT_TARGET_Z:.3f}m (H210: dynamic, Phase 3 end + 2cm)")

    # H158: Increase steps for lower target (600→1200, 2x for better convergence)
    PHASE4_LIFT_STEPS = 1200  # H158: More steps for reliable target achievement
    p4_pos_l, p4_pos_r, p4_quat_l, p4_quat_r = run_diff_ik_motion_with_collection(
        p3_pos_l, p3_pos_r, p3_quat_l, p3_quat_r,
        p4_lift_l, p4_lift_r, PHASE4_LIFT_STEPS, GRIPPER_CLOSE, phase=4
    )

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after pre-rotation lift!")

    # Log Phase 4 end contact force
    p4_end_force_l, p4_end_force_r = get_contact_force()
    # H260: Skip cable access when no cable (PG0 mode)
    if cable is not None:
        p4_end_cable_z = cable.data.body_pos_w[0, :, 2].cpu().numpy()
        print(f"  [P4 End] Contact: L={p4_end_force_l:.1f}N, R={p4_end_force_r:.1f}N, cable_Z: {p4_end_cable_z.min():.3f}-{p4_end_cable_z.max():.3f}")
    else:
        print(f"  [P4 End] Contact: L={p4_end_force_l:.1f}N, R={p4_end_force_r:.1f}N (no cable)")

    # ============================================================
    # PHASE 4.5: 90-degree rotation (3-stage transition) - Separate X/Y movement to avoid NaN
    # 2026-01-07 v19: Separate X and Y movement to maintain IK solution space continuity
    # Stage 1b: X movement only (Y fixed)
    # Stage 1c: Y movement only (X fixed)
    # Stage 2: Move to final position
    # ============================================================
    print("\n[Phase 4.5] 90-degree rotation (3-stage X/Y split) using Diff IK...")
    print("  2026-01-07 v19: Separated X and Y movement to avoid NaN")

    # Get current EE positions after Phase 4 lift
    p4_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p4_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p4_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p4_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()
    print(f"  Start EE: L=({p4_pos_l[0,0]:.3f}, {p4_pos_l[0,1]:.3f}, {p4_pos_l[0,2]:.3f})")
    print(f"           R=({p4_pos_r[0,0]:.3f}, {p4_pos_r[0,1]:.3f}, {p4_pos_r[0,2]:.3f})")

    # H079/v62: Insert stabilization steps (before Phase 4 -> Stage 1b transition)
    # H219: Reduced from 100→50 steps to minimize grip force decay during stabilization
    # Reason: R307 analysis showed 50% force decay (15.8N→7.8N) during 100-step stabilization
    GRASP_STABILIZATION_STEPS = 50  # H219: Was 100, now 50
    print(f"  --- H079: Pre-Stage 1b Stabilization ({GRASP_STABILIZATION_STEPS} steps) ---")
    force_l_pre, force_r_pre = get_contact_force()
    print(f"  Phase 4 End Force: L={force_l_pre:.1f}N, R={force_r_pre:.1f}N")

    # H219: 50-step position hold (physics stabilization) - halved to reduce force decay
    for stab_step in range(GRASP_STABILIZATION_STEPS):
        sim.step()
        scene.update(sim.get_physics_dt())
        if stab_step % 25 == 0:
            force_l_stab, force_r_stab = get_contact_force()
            nan_check, _, _ = check_cable_nan_detailed(cable)
            if nan_check >= 0:
                print(f"  [ERROR] NaN during stabilization at step {stab_step}!")
                check_and_raise_nan(f"H079 Stabilization step {stab_step}")
            print(f"  [Stabilization] Step {stab_step}: L={force_l_stab:.1f}N, R={force_r_stab:.1f}N")

    force_l_post, force_r_post = get_contact_force()
    print(f"  Post-Stabilization Force: L={force_l_post:.1f}N, R={force_r_post:.1f}N")
    print(f"  Force change: L={force_l_post - force_l_pre:+.1f}N, R={force_r_post - force_r_pre:+.1f}N")

    # =======================================================================
    # H097/v71: Stage 1b - 2-phase split (split 88 deg elbow flip into 44 deg x 2)
    # Part 1: Phase 4 end -> mid waypoint (Z=0.95) - 50 steps
    # Mid stabilization: 20 steps
    # Part 2: Mid waypoint -> target (Z=1.05) - 50 steps
    # =======================================================================
    print("  --- Stage 1b: H097 2-Phase Elbow Transition ---")

    # Stage 1b Part 1: Phase 4 end -> mid waypoint
    print("  --- Stage 1b Part 1: Move to mid waypoint (Z=0.95) ---")
    # Use current Y position from Phase 4 end, mid waypoint Z
    MID_Z = WAYPOINT_STAGE1B_MID_LEFT[2]  # 0.95
    p45b_mid_l = torch.tensor([[WAYPOINT_STAGE1B_MID_LEFT[0], p4_pos_l[0,1].item(), MID_Z]], device=device)
    p45b_mid_r = torch.tensor([[WAYPOINT_STAGE1B_MID_RIGHT[0], p4_pos_r[0,1].item(), MID_Z]], device=device)
    print(f"  Stage 1b Mid Target: L=({p45b_mid_l[0,0]:.3f}, {p45b_mid_l[0,1]:.3f}, {p45b_mid_l[0,2]:.3f})")
    print(f"                       R=({p45b_mid_r[0,0]:.3f}, {p45b_mid_r[0,1]:.3f}, {p45b_mid_r[0,2]:.3f})")

    # Part 1: 50 steps to mid waypoint
    PHASE45B_PART1_STEPS = 50
    p45b_mid_pos_l, p45b_mid_pos_r, p45b_mid_quat_l, p45b_mid_quat_r, _ = run_joint_space_motion_with_collection(
        p45b_mid_l, p45b_mid_r, PHASE45B_PART1_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 1b Part 1 (H097 Mid)"
    )

    # Check NaN after Part 1
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 1b Part 1!")

    # Log Part 1 completion
    s1b_p1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s1b_p1_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    s1b_p1_force_l, s1b_p1_force_r = get_contact_force()
    # H260: Use helper for safe cable Z access
    print(f"  Stage 1b Part 1 Complete: L=({s1b_p1_ee_l[0,0]:.3f}, {s1b_p1_ee_l[0,1]:.3f}, {s1b_p1_ee_l[0,2]:.3f})")
    print(f"                            R=({s1b_p1_ee_r[0,0]:.3f}, {s1b_p1_ee_r[0,1]:.3f}, {s1b_p1_ee_r[0,2]:.3f})")
    print(f"  [P4.5 Stage1b-P1] Contact: L={s1b_p1_force_l:.1f}N, R={s1b_p1_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    # H100/v74: H097 stabilization REMOVED (caused probabilistic NaN in v73)
    # H098 also removed (caused cable slipping in v72)
    # Part 1 → Part 2 direct transition with cosine interpolation (H099)

    # H102/v76: Part 2 split into 3 stages to cross elbow boundary (Z=0.99-1.00) slowly
    # IK analysis shows J3 jumps from -31 deg to +37 deg (68 deg elbow flip) at Z=1.00
    # Splitting Part 2: (a) Z=0.95->0.99, (b) Z=0.99->1.01 (slow), (c) Z=1.01->1.05

    # --- Stage 1b Part 2a: Move to boundary (Z=0.99) ---
    print("  --- Stage 1b Part 2a: Move to elbow boundary (Z=0.99) ---")
    p45b_2a_target_l = torch.tensor([[WAYPOINT_PHASE45B_LEFT[0], p4_pos_l[0,1].item(), PART2A_TARGET_Z]], device=device)
    p45b_2a_target_r = torch.tensor([[WAYPOINT_PHASE45B_RIGHT[0], p4_pos_r[0,1].item(), PART2A_TARGET_Z]], device=device)
    print(f"  Part 2a Target: L=({p45b_2a_target_l[0,0]:.3f}, {p45b_2a_target_l[0,1]:.3f}, {p45b_2a_target_l[0,2]:.3f})")
    print(f"                  R=({p45b_2a_target_r[0,0]:.3f}, {p45b_2a_target_r[0,1]:.3f}, {p45b_2a_target_r[0,2]:.3f})")

    p45b_pos_l, p45b_pos_r, p45b_quat_l, p45b_quat_r, _ = run_joint_space_motion_with_collection(
        p45b_2a_target_l, p45b_2a_target_r, PART2A_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 1b Part 2a (boundary)"
    )

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Part 2a!")

    # --- Stage 1b Part 2b: Cross elbow boundary (Z=0.99->1.01, SLOW) ---
    print("  --- Stage 1b Part 2b: Cross elbow boundary (Z=0.99->1.01) SLOW ---")
    p45b_2b_target_l = torch.tensor([[WAYPOINT_PHASE45B_LEFT[0], p4_pos_l[0,1].item(), PART2B_TARGET_Z]], device=device)
    p45b_2b_target_r = torch.tensor([[WAYPOINT_PHASE45B_RIGHT[0], p4_pos_r[0,1].item(), PART2B_TARGET_Z]], device=device)
    print(f"  Part 2b Target: L=({p45b_2b_target_l[0,0]:.3f}, {p45b_2b_target_l[0,1]:.3f}, {p45b_2b_target_l[0,2]:.3f})")
    print(f"                  R=({p45b_2b_target_r[0,0]:.3f}, {p45b_2b_target_r[0,1]:.3f}, {p45b_2b_target_r[0,2]:.3f})")
    print(f"  [H102] Crossing elbow boundary with {PART2B_STEPS} steps (0.02m / {PART2B_STEPS} = slow)")

    p45b_pos_l, p45b_pos_r, p45b_quat_l, p45b_quat_r, _ = run_joint_space_motion_with_collection(
        p45b_2b_target_l, p45b_2b_target_r, PART2B_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 1b Part 2b (elbow boundary)"
    )

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Part 2b (elbow boundary crossing)!")

    # --- Stage 1b Part 2c: Move to final target (Z=1.05) ---
    print("  --- Stage 1b Part 2c: Move to final target (Z=1.05) ---")
    p45b_target_l = torch.tensor([[WAYPOINT_PHASE45B_LEFT[0], p4_pos_l[0,1].item(), PART2C_TARGET_Z]], device=device)
    p45b_target_r = torch.tensor([[WAYPOINT_PHASE45B_RIGHT[0], p4_pos_r[0,1].item(), PART2C_TARGET_Z]], device=device)
    print(f"  Part 2c Target: L=({p45b_target_l[0,0]:.3f}, {p45b_target_l[0,1]:.3f}, {p45b_target_l[0,2]:.3f})")
    print(f"                  R=({p45b_target_r[0,0]:.3f}, {p45b_target_r[0,1]:.3f}, {p45b_target_r[0,2]:.3f})")

    p45b_pos_l, p45b_pos_r, p45b_quat_l, p45b_quat_r, _ = run_joint_space_motion_with_collection(
        p45b_target_l, p45b_target_r, PART2C_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 1b Part 2c (final)"
    )

    # Check cable NaN after Stage 1b complete
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 1b Part 2c!")

    # Log Stage 1b completion with contact force
    s1b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s1b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    s1b_force_l, s1b_force_r = get_contact_force()
    # H260: Use helper for safe cable Z access
    print(f"  Stage 1b Complete: L=({s1b_ee_l[0,0]:.3f}, {s1b_ee_l[0,1]:.3f}, {s1b_ee_l[0,2]:.3f})")
    print(f"                     R=({s1b_ee_r[0,0]:.3f}, {s1b_ee_r[0,1]:.3f}, {s1b_ee_r[0,2]:.3f})")
    print(f"  [P4.5 Stage1b] Contact: L={s1b_force_l:.1f}N, R={s1b_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    # v53: Stabilization hold after Stage 1b (H108: reduced to 20 steps + gripper control)
    print("  [P4.5 Stage1b] Holding for stabilization (20 steps, H108)...")
    hold_position(20, gripper_val=GRIPPER_CLOSE)

    # Stage 1c: Y movement only (X fixed)
    print("  --- Stage 1c: Y movement only (X fixed) ---")
    p45c_target_l = torch.tensor([[WAYPOINT_PHASE45C_LEFT[0], WAYPOINT_PHASE45C_LEFT[1], PRE_ROTATION_Z]], device=device)
    p45c_target_r = torch.tensor([[WAYPOINT_PHASE45C_RIGHT[0], WAYPOINT_PHASE45C_RIGHT[1], PRE_ROTATION_Z]], device=device)
    print(f"  Stage 1c Target: L=({p45c_target_l[0,0]:.3f}, {p45c_target_l[0,1]:.3f}, {p45c_target_l[0,2]:.3f})")
    print(f"                   R=({p45c_target_r[0,0]:.3f}, {p45c_target_r[0,1]:.3f}, {p45c_target_r[0,2]:.3f})")

    # H088/v64: Use Joint Space Interpolation instead of Analytical IK for Stage 1c
    # H092/v68: Revert to 100 steps (200 was worse in v67)
    PHASE45C_Y_STEPS = 200  # H092: Revert to 100
    p45c_pos_l, p45c_pos_r, p45c_quat_l, p45c_quat_r, _ = run_joint_space_motion_with_collection(
        p45c_target_l, p45c_target_r, PHASE45C_Y_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 1c (H088 Joint Space)",
        force_adaptive_velocity=True  # H166: Enable Force L monitoring to reduce NaN
    )

    # Check cable NaN after Stage 1c
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 1c (Y movement)!")

    # Log Stage 1c completion with contact force
    s1c_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s1c_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    s1c_force_l, s1c_force_r = get_contact_force()
    # H260: Use helper for safe cable Z access
    print(f"  Stage 1c Complete: L=({s1c_ee_l[0,0]:.3f}, {s1c_ee_l[0,1]:.3f}, {s1c_ee_l[0,2]:.3f})")
    print(f"                     R=({s1c_ee_r[0,0]:.3f}, {s1c_ee_r[0,1]:.3f}, {s1c_ee_r[0,2]:.3f})")
    print(f"  [P4.5 Stage1c] Contact: L={s1c_force_l:.1f}N, R={s1c_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    # v53: Stabilization hold after Stage 1c (H108: reduced to 20 steps + gripper control)
    print("  [P4.5 Stage1c] Holding for stabilization (20 steps, H108)...")
    hold_position(20, gripper_val=GRIPPER_CLOSE)

    # ================================================================
    # Stage 2: v32 - Gradual Z descent approach
    # Stage 2a: X movement while keeping Z=1.05 (first half)
    # Stage 2b: X movement while descending Z (1.05 -> 1.00) (second half)
    # ================================================================

    # ============================================
    # v49: Stage 2a - 4-step subdivision (each 50mm or less)
    # H115: STAGE2A_STEPS is now imported from task_config.py (450 steps)
    # ============================================
    print("  --- Stage 2a: 4-step subdivision (v49) ---")
    print(f"  STAGE2A_STEPS = {STAGE2A_STEPS} (H115: from task_config.py)")

    # ============================================
    # H159: Stage 2a-0.5 - Intermediate step to split J3 angle change
    # Root cause (LL-2026-01-14-IK-014): J3 changes 20.4° in Stage 2a-1, causing grip loss
    # Solution: Split into two 10° steps by adding intermediate position
    # Stage 1c end: EE L=(0.31, -0.232, 0.95), J3=-32.5°
    # Stage 2a-0.5: EE L=(0.345, -0.216, 1.0), J3≈-22° (estimated 10° change)
    # Stage 2a-1: EE L=(0.38, -0.20, 1.05), J3≈-12° (another 10° change)
    # ============================================
    STAGE2A_05_STEPS = 750  # H159: Start with 750 steps, adjust if needed
    print(f"  --- Stage 2a-0.5: Intermediate step (H159) ---")
    print(f"  H159: Split J3 change to prevent grip loss (LL-IK-014)")
    p2a05_target_l = torch.tensor([[0.345, WAYPOINT_PHASE45_LEFT[1], 1.0]], device=device)  # H248: Y=0 (was -0.216)
    # H159: Right arm follows proportionally (X midpoint between Stage 1c and 2a-1)
    p2a05_target_r = torch.tensor([[0.295, WAYPOINT_PHASE45_RIGHT[1], 1.0]], device=device)
    print(f"  Stage 2a-0.5 Target: L=(0.345, {WAYPOINT_PHASE45_LEFT[1]:.3f}, 1.0), R=(0.295, {WAYPOINT_PHASE45_RIGHT[1]:.3f}, 1.0)")

    p2a05_pos_l, p2a05_pos_r, p2a05_quat_l, p2a05_quat_r, _ = run_joint_space_motion_with_collection(
        p2a05_target_l, p2a05_target_r, STAGE2A_05_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 2a-0.5 (H159 J3 Split)"
    )
    s2a05_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a05_force_l, s2a05_force_r = get_contact_force()
    print(f"  [P4.5 Stage2a-0.5] L=({s2a05_ee_l[0,0]:.3f}, {s2a05_ee_l[0,1]:.3f}, {s2a05_ee_l[0,2]:.3f}), Force: L={s2a05_force_l:.1f}N R={s2a05_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-0.5!")

    # H159: Check grip maintenance after 2a-0.5
    if s2a05_force_l < 5.0:
        print(f"  [H159 WARNING] Low grip force after Stage 2a-0.5: L={s2a05_force_l:.1f}N")

    # Stage 2a-1: H129 - reduced X step (0.38 instead of 0.445)
    # Root cause: Stage 1c ends at X=0.311, jump to X=0.445 was 13.4cm = IK failed
    # H129: Start with smaller step X=0.38 (7cm from 0.311)
    # H106: Migrate from Diff IK to H088 Joint Space Interpolation
    # H159: Now starting from Stage 2a-0.5 position (smaller J3 change)
    print(f"  Stage 2a-1: Target (0.38, {WAYPOINT_PHASE45_LEFT[1]:.3f}, 1.05) [H248: Y=0]")
    p2a1_target_l = torch.tensor([[0.38, WAYPOINT_PHASE45_LEFT[1], PRE_ROTATION_Z]], device=device)  # H248: Y=0 (was -0.20)
    # H109: Right arm follows left arm to maintain tension balance (R_X = 0.290)
    p2a1_target_r = torch.tensor([[0.290, WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p2a1_pos_l, p2a1_pos_r, p2a1_quat_l, p2a1_quat_r, _ = run_joint_space_motion_with_collection(
        p2a1_target_l, p2a1_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 2a-1 (H106 Joint Space)",
        force_adaptive_velocity=True  # H167: Enable Force L monitoring to prevent grip loss
    )
    s2a1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a1_force_l, s2a1_force_r = get_contact_force()
    print(f"  [P4.5 Stage2a-1] L=({s2a1_ee_l[0,0]:.3f}, {s2a1_ee_l[0,1]:.3f}, {s2a1_ee_l[0,2]:.3f}), Force: L={s2a1_force_l:.1f}N R={s2a1_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-1!")

    # Stage 2a-1.25: H132 - intermediate step to reduce delta_X
    # H132: X=0.395, Y=-0.197 (delta_X=1.5cm from 2a-1)
    # Root cause fix: X=0.38→0.415 (3.5cm) caused IK failed due to joint change > 45°
    print(f"  Stage 2a-1.25: Target (0.395, {WAYPOINT_PHASE45_LEFT[1]:.3f}, 1.05) [H248: Y=0]")
    p2a125_target_l = torch.tensor([[0.395, WAYPOINT_PHASE45_LEFT[1], PRE_ROTATION_Z]], device=device)  # H248: Y=0 (was -0.197)
    # H132: Right arm follows left arm (R_X = 0.2875, midpoint between 0.290 and 0.285)
    p2a125_target_r = torch.tensor([[0.2875, WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p2a125_pos_l, p2a125_pos_r, p2a125_quat_l, p2a125_quat_r, _ = run_joint_space_motion_with_collection(
        p2a125_target_l, p2a125_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 2a-1.25 (H132 Joint Space)"
    )
    s2a125_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a125_force_l, s2a125_force_r = get_contact_force()
    print(f"  [P4.5 Stage2a-1.25] L=({s2a125_ee_l[0,0]:.3f}, {s2a125_ee_l[0,1]:.3f}, {s2a125_ee_l[0,2]:.3f}), Force: L={s2a125_force_l:.1f}N R={s2a125_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-1.25!")

    # Stage 2a-1.5: H131 - intermediate step between 2a-1 and 2a-2
    # H131: X=0.415, Y=-0.195 (midpoint Y between 2a-1=-0.20 and 2a-2=-0.19)
    # Root cause fix: H130 Y=-0.17 was outside left arm workspace, fixed to -0.195
    print(f"  Stage 2a-1.5: Target (0.415, {WAYPOINT_PHASE45_LEFT[1]:.3f}, 1.05) [H248: Y=0]")
    p2a15_target_l = torch.tensor([[0.415, WAYPOINT_PHASE45_LEFT[1], PRE_ROTATION_Z]], device=device)  # H248: Y=0 (was -0.195)
    # H130: Right arm follows left arm (R_X = 0.285, midpoint between 0.290 and 0.280)
    p2a15_target_r = torch.tensor([[0.285, WAYPOINT_PHASE45_RIGHT[1], PRE_ROTATION_Z]], device=device)
    p2a15_pos_l, p2a15_pos_r, p2a15_quat_l, p2a15_quat_r, _ = run_joint_space_motion_with_collection(
        p2a15_target_l, p2a15_target_r, STAGE2A_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="Stage 2a-1.5 (H130 Joint Space)"
    )
    s2a15_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s2a15_force_l, s2a15_force_r = get_contact_force()
    print(f"  [P4.5 Stage2a-1.5] L=({s2a15_ee_l[0,0]:.3f}, {s2a15_ee_l[0,1]:.3f}, {s2a15_ee_l[0,2]:.3f}), Force: L={s2a15_force_l:.1f}N R={s2a15_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Stage 2a-1.5!")

    # ============================================
    # H160: New trajectory - Right arm extends to X=0.70 at low Z
    # ============================================
    # Root cause (LL-2026-01-14-IK-015): Left arm max reach X≈0.42 at Z=1.05
    # Root cause (LL-2026-01-14-IK-016): Right arm X=0.70 safe at Z≤0.88 (margin≥10°)
    # Solution: Right arm handles X=0.70, Left arm stays at X≤0.40
    # Lower Z trajectory (1.05→0.95→0.92→0.90→0.88) for IK safety
    print("  --- H160: Right arm extension trajectory (role swap) ---")
    print("  [H160] LL-IK-015: Left arm limit X≤0.42 at Z=1.05")
    print("  [H160] LL-IK-016: Right arm X=0.70 safe at Z≤0.88")

    H160_STAGE_STEPS = 600  # Steps per stage

    # H162 Stage A: J3-safe target with higher Z and adjusted X/Y
    # From Stage 2a-1.5 end: L≈(0.415, -0.195, 1.05), R≈(0.285, +0.227, 1.05)
    # H162 Option A: pA_target_l changed from (0.40, -0.19, 0.95) to (0.38, -0.22, 0.98)
    # This keeps J3(L) > -55° to prevent grip loss at step 360
    print(f"  Stage A: H248 J3-safe target (Z=0.98, X=0.38, Y=0)")
    H160_STAGE_A_Z = 0.98  # H162: 0.95 → 0.98 (higher Z for J3 margin)
    pA_target_l = torch.tensor([[0.38, WAYPOINT_PHASE45_LEFT[1], H160_STAGE_A_Z]], device=device)  # H248: Y=0 (was -0.22)
    pA_target_r = torch.tensor([[0.38, WAYPOINT_PHASE45_RIGHT[1], H160_STAGE_A_Z]], device=device)  # H248: Y=0 (was 0.18)
    print(f"  Target: L=(0.38, {WAYPOINT_PHASE45_LEFT[1]:.3f}, {H160_STAGE_A_Z}), R=(0.38, {WAYPOINT_PHASE45_RIGHT[1]:.3f}, {H160_STAGE_A_Z})")
    pA_pos_l, pA_pos_r, pA_quat_l, pA_quat_r, _ = run_joint_space_motion_with_collection(
        pA_target_l, pA_target_r, H160_STAGE_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H160 Stage A (Z descent + role swap)"
    )
    sA_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sA_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sA_force_l, sA_force_r = get_contact_force()
    print(f"  [H160 Stage A] L=({sA_ee_l[0,0]:.3f}, {sA_ee_l[0,1]:.3f}, {sA_ee_l[0,2]:.3f}), R=({sA_ee_r[0,0]:.3f}, {sA_ee_r[0,1]:.3f}, {sA_ee_r[0,2]:.3f})")
    print(f"  Force: L={sA_force_l:.1f}N R={sA_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H160 Stage A!")

    # H264: Save checkpoint video after Stage A (90-degree rotation complete)
    # This captures the critical rotation evidence for post-mortem analysis
    save_checkpoint_video("stage_a_rotation_complete", env_idx=0)

    # H171: Stage B-0.5 (NEW intermediate step)
    # Root cause: H168-H170 failed in Stage B due to combined Z descent + X extension
    # Solution: Split into two phases - B-0.5 (X extend at Z=0.95), B (Z descent only)
    # Reference: LL-2026-01-15-PHY-002/003/004, Code B 5 Whys analysis
    H171_STAGE_B05_STEPS = 400  # Code B recommendation: 400+400 split
    H171_STAGE_B_STEPS = 400

    print("  Stage B-0.5: Extend Right X to 0.42 at Z=0.95 (H248: Y=0)")
    H171_STAGE_B05_Z = 0.95  # Higher Z to reduce cable tension during X extension
    pB05_target_l = torch.tensor([[0.38, WAYPOINT_PHASE45_LEFT[1], H171_STAGE_B05_Z]], device=device)  # H248: Y=0 (was -0.185)
    pB05_target_r = torch.tensor([[0.42, WAYPOINT_PHASE45_RIGHT[1], H171_STAGE_B05_Z]], device=device)  # H248: Y=0 (was 0.155)
    print(f"  Target: L=(0.38, {WAYPOINT_PHASE45_LEFT[1]:.3f}, {H171_STAGE_B05_Z}), R=(0.42, {WAYPOINT_PHASE45_RIGHT[1]:.3f}, {H171_STAGE_B05_Z})")
    pB05_pos_l, pB05_pos_r, pB05_quat_l, pB05_quat_r, _ = run_joint_space_motion_with_collection(
        pB05_target_l, pB05_target_r, H171_STAGE_B05_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H171 Stage B-0.5 (Right X=0.42 at Z=0.95)",
        max_velocity=1.5,
        force_adaptive_velocity=True  # H164: Enable Force R threshold-based velocity control
    )
    sB05_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sB05_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sB05_force_l, sB05_force_r = get_contact_force()
    print(f"  [H171 Stage B-0.5] L=({sB05_ee_l[0,0]:.3f}, {sB05_ee_l[0,1]:.3f}, {sB05_ee_l[0,2]:.3f}), R=({sB05_ee_r[0,0]:.3f}, {sB05_ee_r[0,1]:.3f}, {sB05_ee_r[0,2]:.3f})")
    print(f"  Force: L={sB05_force_l:.1f}N R={sB05_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H171 Stage B-0.5!")

    # H171 Stage B: Lower Z to 0.92 (X already extended in B-0.5)
    # H169: Reduced X from 0.50 to 0.45 to mitigate Force L spike (LL-2026-01-15-PHY-002)
    # H170: Further reduced X from 0.45 to 0.40 to avoid catenary tension critical point (LL-2026-01-15-PHY-003)
    # H171: Split motion - Z descent only in this stage (X already at 0.42 from B-0.5)
    # H171: X=0.42 is optimal balance between grip force retention and tension threshold (LL-2026-01-15-PHY-002/003/004)
    print("  Stage B: Lower Z to 0.92 (H248: Y=0)")
    H160_STAGE_B_Z = 0.92
    pB_target_l = torch.tensor([[0.38, WAYPOINT_PHASE45_LEFT[1], H160_STAGE_B_Z]], device=device)  # H248: Y=0 (was -0.15)
    pB_target_r = torch.tensor([[0.42, WAYPOINT_PHASE45_RIGHT[1], H160_STAGE_B_Z]], device=device)  # H248: Y=0 (was 0.13)
    print(f"  Target: L=(0.38, {WAYPOINT_PHASE45_LEFT[1]:.3f}, {H160_STAGE_B_Z}), R=(0.42, {WAYPOINT_PHASE45_RIGHT[1]:.3f}, {H160_STAGE_B_Z})")
    # H164: Force R threshold-based dynamic velocity control
    # Root cause: LL-2026-01-15-NAN-001 - Right arm extension causes Force R +78% spike (24.7N)
    # Solution: Monitor Force R, reduce velocity when > 20N, restore when < 15N
    # Also: Force L > 100N safety abort to prevent physics collapse
    pB_pos_l, pB_pos_r, pB_quat_l, pB_quat_r, _ = run_joint_space_motion_with_collection(
        pB_target_l, pB_target_r, H171_STAGE_B_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H171 Stage B (Z descent to 0.92)",  # H171: Now Z descent only
        max_velocity=1.5,  # H163: Base velocity (H164 may reduce to VEL_REDUCED dynamically)
        force_adaptive_velocity=True  # H164: Enable Force R threshold-based velocity control
    )
    sB_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sB_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sB_force_l, sB_force_r = get_contact_force()
    print(f"  [H171 Stage B] L=({sB_ee_l[0,0]:.3f}, {sB_ee_l[0,1]:.3f}, {sB_ee_l[0,2]:.3f}), R=({sB_ee_r[0,0]:.3f}, {sB_ee_r[0,1]:.3f}, {sB_ee_r[0,2]:.3f})")
    print(f"  Force: L={sB_force_l:.1f}N R={sB_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H171 Stage B!")

    # H185 Stage B.5: 3-way split for X transition (was single stage in H172-H183)
    # Purpose: Distribute Force R spike across smaller increments
    # Reference: LL-2026-01-16-PHY-012, LL-2026-01-16-PHY-013, LL-2026-01-16-PHY-014
    # - H181/H184 showed Force R spike 140.9N and grip loss at step 94
    # - Single 0.06m X movement causes excessive cable tension
    # Split: B.5a (X 0.42→0.44) → B.5b (X 0.44→0.46) → B.5c (X 0.46→0.48)
    print("  Stage B.5: H185 3-way split (X: 0.42→0.44→0.46→0.48)")

    # Stage B.5a: First increment (X: 0.42→0.44)
    H185_STAGE_B5A_Z = 0.917
    H185_STAGE_B5A_STEPS = 133
    pB5a_target_l = torch.tensor([[0.373, WAYPOINT_PHASE45_LEFT[1], H185_STAGE_B5A_Z]], device=device)  # H248: Y=0 (was -0.143)
    pB5a_target_r = torch.tensor([[0.44, WAYPOINT_PHASE45_RIGHT[1], H185_STAGE_B5A_Z]], device=device)  # H248: Y=0 (was 0.127)
    print(f"  Stage B.5a: L=(0.373, {WAYPOINT_PHASE45_LEFT[1]:.3f}, {H185_STAGE_B5A_Z}), R=(0.44, {WAYPOINT_PHASE45_RIGHT[1]:.3f}, {H185_STAGE_B5A_Z})")
    pB5a_pos_l, pB5a_pos_r, pB5a_quat_l, pB5a_quat_r, _ = run_joint_space_motion_with_collection(
        pB5a_target_l, pB5a_target_r, H185_STAGE_B5A_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H185 Stage B.5a (X: 0.42→0.44)",
        max_velocity=1.5,
        force_adaptive_velocity=True
    )
    sB5a_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sB5a_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sB5a_force_l, sB5a_force_r = get_contact_force()
    print(f"  [H185 B.5a] L=({sB5a_ee_l[0,0]:.3f}, {sB5a_ee_l[0,1]:.3f}, {sB5a_ee_l[0,2]:.3f}), R=({sB5a_ee_r[0,0]:.3f}, {sB5a_ee_r[0,1]:.3f}, {sB5a_ee_r[0,2]:.3f})")
    print(f"  Force: L={sB5a_force_l:.1f}N R={sB5a_force_r:.1f}N")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H185 Stage B.5a!")

    # H188→H189: Stabilization between Stage B.5a and B.5b
    # Purpose: Allow physics state to settle before X=0.44→0.46 movement
    # Reference: LL-2026-01-23-PHY-001 (Force L spike 3547.1N at step 69)
    # H189: Use hold_position() to ensure gripper control is maintained
    # Previous H188 v2 lacked gripper control causing immediate grip loss (Force=0.0N at step 0)
    H189_STABILIZATION_STEPS = 50
    print(f"  [H189] Stage B.5a→B.5b stabilization ({H189_STABILIZATION_STEPS} steps) using hold_position()...")
    pre_stab_force_l, pre_stab_force_r = get_contact_force()
    print(f"    [H189] Pre-stabilization force: L={pre_stab_force_l:.1f}N R={pre_stab_force_r:.1f}N")
    hold_position(num_steps=H189_STABILIZATION_STEPS, gripper_val=GRIPPER_CLOSE)
    post_stab_force_l, post_stab_force_r = get_contact_force()
    print(f"    [H189] Post-stabilization force: L={post_stab_force_l:.1f}N R={post_stab_force_r:.1f}N")
    # H189: Verify grip maintained after stabilization
    if post_stab_force_l < 5.0 or post_stab_force_r < 5.0:
        print(f"  [H189 WARNING] Grip may have weakened during stabilization: L={post_stab_force_l:.1f}N R={post_stab_force_r:.1f}N")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H189 stabilization!")

    # H200: Stage B.5b split into Part 1 + mid-stabilization + Part 2
    # Purpose: Suppress Force spike at B.5b step 38 (Force L=287.2N in v147_fullcycle_f5)
    # Reference: LL-2026-01-23-PHY-001, v147_fullcycle_f5 log analysis
    # Pattern: Same as H191/H192 (split X movement with mid-stabilization)
    H185_STAGE_B5B_Z = 0.913

    # Get current position (B.5a end) for interpolation
    b5b_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    b5b_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # Final B.5b target positions
    pB5b_final_l = torch.tensor([[0.367, WAYPOINT_PHASE45_LEFT[1], H185_STAGE_B5B_Z]], device=device)  # H248: Y=0 (was -0.137)
    pB5b_final_r = torch.tensor([[0.46, WAYPOINT_PHASE45_RIGHT[1], H185_STAGE_B5B_Z]], device=device)  # H248: Y=0 (was 0.123)

    # H200: Calculate intermediate target at X_R=0.45 (midpoint)
    # Left arm Y position is interpolated proportionally
    interp_ratio_b5b = (H200_B5B_PART1_X_R - 0.44) / (0.46 - 0.44)  # 0.45-0.44 / 0.46-0.44 = 0.5
    pB5b_mid_l = b5b_start_l + interp_ratio_b5b * (pB5b_final_l - b5b_start_l)
    pB5b_mid_r = torch.tensor([[H200_B5B_PART1_X_R, WAYPOINT_PHASE45_RIGHT[1], H185_STAGE_B5B_Z]], device=device)  # H248: Y=0 (was 0.125)

    # H200 Part 1: Move to intermediate position (X_R: 0.44→0.45)
    print(f"  [H200] Stage B.5b Part 1: {H200_B5B_PART1_STEPS} steps (X_R: 0.44→{H200_B5B_PART1_X_R})")
    print(f"    Target (mid): L=({pB5b_mid_l[0,0]:.3f}, {pB5b_mid_l[0,1]:.3f}, {pB5b_mid_l[0,2]:.3f}), R=({pB5b_mid_r[0,0]:.3f}, {pB5b_mid_r[0,1]:.3f}, {pB5b_mid_r[0,2]:.3f})")
    pB5b_p1_pos_l, pB5b_p1_pos_r, pB5b_p1_quat_l, pB5b_p1_quat_r, _ = run_joint_space_motion_with_collection(
        pB5b_mid_l, pB5b_mid_r, H200_B5B_PART1_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H200 Stage B.5b Part 1 (X_R: 0.44→0.45)",
        max_velocity=1.5,
        force_adaptive_velocity=True
    )
    b5b_p1_force_l, b5b_p1_force_r = get_contact_force()
    b5b_p1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    b5b_p1_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"    [H200] Part 1 complete: Force L={b5b_p1_force_l:.1f}N R={b5b_p1_force_r:.1f}N")
    print(f"    EE: L=({b5b_p1_ee_l[0,0]:.3f}, {b5b_p1_ee_l[0,1]:.3f}, {b5b_p1_ee_l[0,2]:.3f}), R=({b5b_p1_ee_r[0,0]:.3f}, {b5b_p1_ee_r[0,1]:.3f}, {b5b_p1_ee_r[0,2]:.3f})")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H200 B.5b Part 1!")

    # H200: Mid-B.5b Stabilization (30 steps)
    # Purpose: Allow physics state to settle before second half of X movement
    print(f"  [H200] Mid-B.5b stabilization ({H200_B5B_MID_STABILIZE_STEPS} steps)...")
    h200_pre_stab_force_l, h200_pre_stab_force_r = get_contact_force()
    print(f"    [H200] Pre-stabilization: Force L={h200_pre_stab_force_l:.1f}N R={h200_pre_stab_force_r:.1f}N")
    hold_position(num_steps=H200_B5B_MID_STABILIZE_STEPS, gripper_val=GRIPPER_CLOSE)
    h200_post_stab_force_l, h200_post_stab_force_r = get_contact_force()
    print(f"    [H200] Post-stabilization: Force L={h200_post_stab_force_l:.1f}N R={h200_post_stab_force_r:.1f}N")

    if h200_post_stab_force_l < 5.0:
        print(f"  [H200 WARNING] Left grip weak after mid-B.5b stabilization: Force L={h200_post_stab_force_l:.1f}N")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H200 mid-B.5b stabilization!")

    # H200 Part 2: Move to final B.5b position (X_R: 0.45→0.46)
    print(f"  [H200] Stage B.5b Part 2: {H200_B5B_PART2_STEPS} steps (X_R: {H200_B5B_PART1_X_R}→0.46)")
    print(f"    Target (final): L=({pB5b_final_l[0,0]:.3f}, {pB5b_final_l[0,1]:.3f}, {pB5b_final_l[0,2]:.3f}), R=({pB5b_final_r[0,0]:.3f}, {pB5b_final_r[0,1]:.3f}, {pB5b_final_r[0,2]:.3f})")
    # H200: Receive abort_flag as 5th return value
    pB5b_p2_pos_l, pB5b_p2_pos_r, pB5b_p2_quat_l, pB5b_p2_quat_r, b5b_p2_abort = run_joint_space_motion_with_collection(
        pB5b_final_l, pB5b_final_r, H200_B5B_PART2_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H200 Stage B.5b Part 2 (X_R: 0.45→0.46)",
        max_velocity=1.5,
        force_adaptive_velocity=True
    )
    sB5b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sB5b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sB5b_force_l, sB5b_force_r = get_contact_force()
    print(f"  [H200 B.5b] Final: L=({sB5b_ee_l[0,0]:.3f}, {sB5b_ee_l[0,1]:.3f}, {sB5b_ee_l[0,2]:.3f}), R=({sB5b_ee_r[0,0]:.3f}, {sB5b_ee_r[0,1]:.3f}, {sB5b_ee_r[0,2]:.3f})")
    print(f"  Force: L={sB5b_force_l:.1f}N R={sB5b_force_r:.1f}N")
    if b5b_p2_abort:
        print(f"  [H200] Stage B.5b Part 2 ABORTED - abort_flag=True")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H200 Stage B.5b Part 2!")

    # H190: Stabilization between Stage B.5b and B.5c
    # H200: SKIP stabilization if ABORT occurred (abort_flag=True)
    # Root cause: High tension (287.2N) + hold_position() → Force collapse → NaN
    # Evidence: LL-2026-01-25-FORCE-002, log L1696-L1714
    H190_B5C_STABILIZATION_STEPS = 30
    if b5b_p2_abort:
        print(f"  [H200] SKIPPING H190 stabilization: abort_flag=True (prevent physics collapse)")
        print(f"  [H200] Reason: Stabilization after ABORT causes Force collapse → NaN")
    else:
        print(f"  [H190] Stage B.5b→B.5c stabilization ({H190_B5C_STABILIZATION_STEPS} steps)...")
        pre_b5c_force_l, pre_b5c_force_r = get_contact_force()
        pre_b5c_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        print(f"    [H190] Pre-B.5c: Force L={pre_b5c_force_l:.1f}N R={pre_b5c_force_r:.1f}N, EE_L=({pre_b5c_ee_l[0,0]:.3f}, {pre_b5c_ee_l[0,1]:.3f}, {pre_b5c_ee_l[0,2]:.3f})")
        hold_position(num_steps=H190_B5C_STABILIZATION_STEPS, gripper_val=GRIPPER_CLOSE)
        post_b5c_force_l, post_b5c_force_r = get_contact_force()
        post_b5c_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
        print(f"    [H190] Post-B.5c stab: Force L={post_b5c_force_l:.1f}N R={post_b5c_force_r:.1f}N, EE_L=({post_b5c_ee_l[0,0]:.3f}, {post_b5c_ee_l[0,1]:.3f}, {post_b5c_ee_l[0,2]:.3f})")
        if post_b5c_force_l < 5.0:
            print(f"  [H190 WARNING] Left grip weak after B.5b→B.5c stabilization: Force L={post_b5c_force_l:.1f}N")

        if not check_cable_nan():
            print("  [ERROR] Cable NaN after H190 B.5b→B.5c stabilization!")

    # Stage B.5c: Final increment (X: 0.46→0.48)
    # H191: Split B.5c into 2 parts with mid-stabilization at step 36
    # Reference: LL-2026-01-23-FORCE-001 (Force spike L=13305.8N at step 36)
    H185_STAGE_B5C_Z = 0.91

    # Get current position (B.5b end) for interpolation
    b5c_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    b5c_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # Final target positions
    pB5c_final_l = torch.tensor([[0.36, WAYPOINT_PHASE45_LEFT[1], H185_STAGE_B5C_Z]], device=device)  # H248: Y=0 (was -0.13)
    pB5c_final_r = torch.tensor([[0.48, WAYPOINT_PHASE45_RIGHT[1], H185_STAGE_B5C_Z]], device=device)  # H248: Y=0 (was 0.12)

    # H191: Calculate intermediate target at step 36/134 (≈27% of the way)
    interp_ratio = H191_B5C_PART1_STEPS / (H191_B5C_PART1_STEPS + H191_B5C_PART2_STEPS)  # 36/134 ≈ 0.269
    pB5c_mid_l = b5c_start_l + interp_ratio * (pB5c_final_l - b5c_start_l)
    pB5c_mid_r = b5c_start_r + interp_ratio * (pB5c_final_r - b5c_start_r)

    # H191 Part 1: Move to intermediate position (step 36)
    print(f"  [H191] Stage B.5c Part 1: {H191_B5C_PART1_STEPS} steps (before stabilization)")
    print(f"    Target (mid): L=({pB5c_mid_l[0,0]:.3f}, {pB5c_mid_l[0,1]:.3f}, {pB5c_mid_l[0,2]:.3f}), R=({pB5c_mid_r[0,0]:.3f}, {pB5c_mid_r[0,1]:.3f}, {pB5c_mid_r[0,2]:.3f})")
    pB5c_p1_pos_l, pB5c_p1_pos_r, pB5c_p1_quat_l, pB5c_p1_quat_r, _ = run_joint_space_motion_with_collection(
        pB5c_mid_l, pB5c_mid_r, H191_B5C_PART1_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H191 Stage B.5c Part 1 (pre-stabilize)",
        max_velocity=1.5,
        force_adaptive_velocity=True
    )
    p1_force_l, p1_force_r = get_contact_force()
    print(f"    [H191] Part 1 complete: Force L={p1_force_l:.1f}N R={p1_force_r:.1f}N")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H191 B.5c Part 1!")

    # H191: Mid-B.5c Stabilization (30 steps)
    # Purpose: Prevent Force spike at step 36 by allowing physics to settle
    print(f"  [H191] Mid-B.5c stabilization ({H191_B5C_MID_STABILIZE_STEPS} steps)...")
    pre_stab_force_l, pre_stab_force_r = get_contact_force()
    pre_stab_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    print(f"    [H191] Pre-stabilization: Force L={pre_stab_force_l:.1f}N R={pre_stab_force_r:.1f}N")
    hold_position(num_steps=H191_B5C_MID_STABILIZE_STEPS, gripper_val=GRIPPER_CLOSE)
    post_stab_force_l, post_stab_force_r = get_contact_force()
    post_stab_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    print(f"    [H191] Post-stabilization: Force L={post_stab_force_l:.1f}N R={post_stab_force_r:.1f}N")

    if post_stab_force_l < 5.0:
        print(f"  [H191 WARNING] Left grip weak after mid-stabilization: Force L={post_stab_force_l:.1f}N")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H191 mid-B.5c stabilization!")

    # H192: Part 2 split into Part 2A + mid-stabilization + Part 2B
    # Reference: LL-2026-01-23-FORCE-001/002 - Force spike at Part 2 step 26
    # Solution: Split Part 2 (98 steps) to insert stabilization after step 49

    # Get current position after H191 Part 1 stabilization for Part 2 interpolation
    p2_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p2_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # Calculate Part 2A target (halfway through Part 2, 49/98 = 50%)
    p2_interp_ratio = H192_B5C_PART2A_STEPS / (H192_B5C_PART2A_STEPS + H192_B5C_PART2B_STEPS)  # 49/98 = 0.5
    pB5c_p2a_target_l = p2_start_l + p2_interp_ratio * (pB5c_final_l - p2_start_l)
    pB5c_p2a_target_r = p2_start_r + p2_interp_ratio * (pB5c_final_r - p2_start_r)

    # H192 Part 2A: First half of Part 2 (49 steps)
    print(f"  [H192] Stage B.5c Part 2A: {H192_B5C_PART2A_STEPS} steps (first half)")
    print(f"    Target (Part 2A): L=({pB5c_p2a_target_l[0,0]:.3f}, {pB5c_p2a_target_l[0,1]:.3f}, {pB5c_p2a_target_l[0,2]:.3f}), R=({pB5c_p2a_target_r[0,0]:.3f}, {pB5c_p2a_target_r[0,1]:.3f}, {pB5c_p2a_target_r[0,2]:.3f})")
    pB5c_p2a_pos_l, pB5c_p2a_pos_r, pB5c_p2a_quat_l, pB5c_p2a_quat_r, _ = run_joint_space_motion_with_collection(
        pB5c_p2a_target_l, pB5c_p2a_target_r, H192_B5C_PART2A_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H192 Stage B.5c Part 2A (first half)",
        max_velocity=1.5,
        force_adaptive_velocity=True
    )
    p2a_force_l, p2a_force_r = get_contact_force()
    print(f"    [H192] Part 2A complete: Force L={p2a_force_l:.1f}N R={p2a_force_r:.1f}N")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H192 B.5c Part 2A!")

    # H192: Part 2 Mid-Stabilization (30 steps)
    # Purpose: Prevent Force spike at Part 2 step 26 (which is within Part 2A)
    # by allowing physics to settle before Part 2B
    print(f"  [H192] Part 2 mid-stabilization ({H192_B5C_PART2_MID_STABILIZE_STEPS} steps)...")
    p2_pre_stab_force_l, p2_pre_stab_force_r = get_contact_force()
    print(f"    [H192] Pre-stabilization: Force L={p2_pre_stab_force_l:.1f}N R={p2_pre_stab_force_r:.1f}N")
    hold_position(num_steps=H192_B5C_PART2_MID_STABILIZE_STEPS, gripper_val=GRIPPER_CLOSE)
    p2_post_stab_force_l, p2_post_stab_force_r = get_contact_force()
    print(f"    [H192] Post-stabilization: Force L={p2_post_stab_force_l:.1f}N R={p2_post_stab_force_r:.1f}N")

    if p2_post_stab_force_l < 5.0:
        print(f"  [H192 WARNING] Left grip weak after Part 2 mid-stabilization: Force L={p2_post_stab_force_l:.1f}N")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H192 Part 2 mid-stabilization!")

    # H192 Part 2B: Second half of Part 2 (49 steps) to final position
    # H193: Proportional follow - Left arm X follows Right arm X movement
    p2b_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p2b_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # Calculate Right arm X movement during Part 2B
    right_x_movement = pB5c_final_r[0, 0] - p2b_start_r[0, 0]

    # H193: Left arm follows 60% of Right arm X movement (only if movement exceeds threshold)
    if abs(right_x_movement) > H193_MIN_THRESHOLD_CM / 100.0:  # Convert cm to m
        left_x_follow = right_x_movement * H193_LEFT_FOLLOW_RATIO
        pB5c_final_l_h193 = pB5c_final_l.clone()
        pB5c_final_l_h193[0, 0] = pB5c_final_l[0, 0] + left_x_follow
        print(f"  [H193] Proportional follow: Right X movement={right_x_movement*100:.2f}cm, Left X follow={left_x_follow*100:.2f}cm ({H193_LEFT_FOLLOW_RATIO*100:.0f}%)")
        print(f"    Original L target X: {pB5c_final_l[0,0]:.4f} → Adjusted: {pB5c_final_l_h193[0,0]:.4f}")
    else:
        pB5c_final_l_h193 = pB5c_final_l
        print(f"  [H193] Proportional follow: Right X movement={right_x_movement*100:.2f}cm < threshold {H193_MIN_THRESHOLD_CM}cm, skipped")

    print(f"  [H192] Stage B.5c Part 2B: {H192_B5C_PART2B_STEPS} steps (to final position)")
    print(f"    Target (final): L=({pB5c_final_l_h193[0,0]:.3f}, {pB5c_final_l_h193[0,1]:.3f}, {pB5c_final_l_h193[0,2]:.3f}), R=({pB5c_final_r[0,0]:.3f}, {pB5c_final_r[0,1]:.3f}, {pB5c_final_r[0,2]:.3f})")
    pB5c_pos_l, pB5c_pos_r, pB5c_quat_l, pB5c_quat_r, _ = run_joint_space_motion_with_collection(
        pB5c_final_l_h193, pB5c_final_r, H192_B5C_PART2B_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H193 Stage B.5c Part 2B (proportional follow)",
        max_velocity=1.5,
        force_adaptive_velocity=True
    )
    sB5_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sB5_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sB5_force_l, sB5_force_r = get_contact_force()
    print(f"  [H191 B.5c Complete] L=({sB5_ee_l[0,0]:.3f}, {sB5_ee_l[0,1]:.3f}, {sB5_ee_l[0,2]:.3f}), R=({sB5_ee_r[0,0]:.3f}, {sB5_ee_r[0,1]:.3f}, {sB5_ee_r[0,2]:.3f})")
    print(f"  Force: L={sB5_force_l:.1f}N R={sB5_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    # H190: Grip loss detection after B.5c - flag for Phase 5 guard
    # H214: Skip grip loss check when cable is disabled (Force=0.0N is expected)
    h190_grip_loss_detected = False
    if not H160_DISABLE_CABLE and (sB5_force_l < 5.0 or sB5_force_r < 5.0):
        print(f"  [H190 ALERT] Grip loss after B.5c: Force L={sB5_force_l:.1f}N R={sB5_force_r:.1f}N (threshold: 5.0N)")
        h190_grip_loss_detected = True

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H191 Stage B.5c!")

    # ===========================================================================
    # H261: Stage C Intermediate Waypoints (IK Fix for Gate-R PASS)
    # Purpose: Reduce per-step joint change from 66.4° to ~22° by 3-step path
    # Reference: EP-H261-B2 (EVIDENCE_PACKS.md:L4644-L4729)
    # ===========================================================================

    print("=" * 60)
    print("  [H261] Stage C Intermediate Waypoints (IK Fix)")
    print("=" * 60)

    # Get current position for waypoint calculation
    h261_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    h261_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    print(f"  [H261] Start position: L=({h261_start_l[0,0]:.3f}, {h261_start_l[0,1]:.3f}, {h261_start_l[0,2]:.3f}), R=({h261_start_r[0,0]:.3f}, {h261_start_r[0,1]:.3f}, {h261_start_r[0,2]:.3f})")

    # H262: Calculate Stage C1 target dynamically for waypoint computation
    # (Same calculation as L4780-4794, but done here before WP calculation)
    H160_STAGE_C1_Z_FOR_WP = 0.90
    h262_c1_base_target_l = torch.tensor([[0.36, -0.14, H160_STAGE_C1_Z_FOR_WP]], device=device)
    h262_c1_target_r = torch.tensor([[0.49, 0.12, H160_STAGE_C1_Z_FOR_WP]], device=device)
    # H262: Apply H194 proportional follow for Left arm
    h262_c1_right_x_movement = h262_c1_target_r[0, 0] - h261_start_r[0, 0]
    if abs(h262_c1_right_x_movement) > H193_MIN_THRESHOLD_CM / 100.0:
        h262_c1_left_x_follow = h262_c1_right_x_movement * H193_LEFT_FOLLOW_RATIO
        h262_c1_target_l = h262_c1_base_target_l.clone()
        h262_c1_target_l[0, 0] = h262_c1_base_target_l[0, 0] + h262_c1_left_x_follow
    else:
        h262_c1_target_l = h262_c1_base_target_l
    print(f"  [H262] C1 target (for WP calc): L=({h262_c1_target_l[0,0]:.3f}, {h262_c1_target_l[0,1]:.3f}, {h262_c1_target_l[0,2]:.3f}), R=({h262_c1_target_r[0,0]:.3f}, {h262_c1_target_r[0,1]:.3f}, {h262_c1_target_r[0,2]:.3f})")

    # --- H261 WP1 (33%): First intermediate waypoint ---
    # H262: Dynamic waypoint calculation (replaces fixed coordinates)
    h261_wp1_target_l = h261_start_l + 0.33 * (h262_c1_target_l - h261_start_l)
    h261_wp1_target_r = h261_start_r + 0.33 * (h262_c1_target_r - h261_start_r)
    print(f"  [H262] WP1 (33%): Target L=({h261_wp1_target_l[0,0]:.3f}, {h261_wp1_target_l[0,1]:.3f}, {h261_wp1_target_l[0,2]:.3f}), R=({h261_wp1_target_r[0,0]:.3f}, {h261_wp1_target_r[0,1]:.3f}, {h261_wp1_target_r[0,2]:.3f})")

    h261_wp1_pos_l, h261_wp1_pos_r, h261_wp1_quat_l, h261_wp1_quat_r, _ = run_joint_space_motion_with_collection(
        h261_wp1_target_l, h261_wp1_target_r, H261_WP1_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H261 WP1 (33%)",
        force_adaptive_velocity=True,
        target_quat_wxyz=GRIPPER_ROTATED_90_QUAT_WXYZ  # H259: 90° Z-rotation maintained
    )
    h261_wp1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    h261_wp1_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    h261_wp1_force_l, h261_wp1_force_r = get_contact_force()
    print(f"  [H261 WP1] L=({h261_wp1_ee_l[0,0]:.3f}, {h261_wp1_ee_l[0,1]:.3f}, {h261_wp1_ee_l[0,2]:.3f}), R=({h261_wp1_ee_r[0,0]:.3f}, {h261_wp1_ee_r[0,1]:.3f}, {h261_wp1_ee_r[0,2]:.3f})")
    print(f"  Force: L={h261_wp1_force_l:.1f}N R={h261_wp1_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H261 WP1!")

    # H261 WP1 Stabilization
    print(f"  [H261] WP1 Stabilization: {H261_WP_STABILIZE_STEPS} steps")
    for stab_step in range(H261_WP_STABILIZE_STEPS):
        v199_watchdog_start()
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        v199_watchdog_stop()
    h261_wp1_stab_force_l, h261_wp1_stab_force_r = get_contact_force()
    print(f"  [H261 WP1 Stabilized] Force: L={h261_wp1_stab_force_l:.1f}N R={h261_wp1_stab_force_r:.1f}N")

    # --- H261 WP2 (66%): Second intermediate waypoint ---
    # H262: Dynamic waypoint calculation (replaces fixed coordinates)
    h261_wp2_target_l = h261_start_l + 0.66 * (h262_c1_target_l - h261_start_l)
    h261_wp2_target_r = h261_start_r + 0.66 * (h262_c1_target_r - h261_start_r)
    print(f"  [H262] WP2 (66%): Target L=({h261_wp2_target_l[0,0]:.3f}, {h261_wp2_target_l[0,1]:.3f}, {h261_wp2_target_l[0,2]:.3f}), R=({h261_wp2_target_r[0,0]:.3f}, {h261_wp2_target_r[0,1]:.3f}, {h261_wp2_target_r[0,2]:.3f})")

    h261_wp2_pos_l, h261_wp2_pos_r, h261_wp2_quat_l, h261_wp2_quat_r, _ = run_joint_space_motion_with_collection(
        h261_wp2_target_l, h261_wp2_target_r, H261_WP2_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H261 WP2 (66%)",
        force_adaptive_velocity=True,
        target_quat_wxyz=GRIPPER_ROTATED_90_QUAT_WXYZ  # H259: 90° Z-rotation maintained
    )
    h261_wp2_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    h261_wp2_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    h261_wp2_force_l, h261_wp2_force_r = get_contact_force()
    print(f"  [H261 WP2] L=({h261_wp2_ee_l[0,0]:.3f}, {h261_wp2_ee_l[0,1]:.3f}, {h261_wp2_ee_l[0,2]:.3f}), R=({h261_wp2_ee_r[0,0]:.3f}, {h261_wp2_ee_r[0,1]:.3f}, {h261_wp2_ee_r[0,2]:.3f})")
    print(f"  Force: L={h261_wp2_force_l:.1f}N R={h261_wp2_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H261 WP2!")

    # H261 WP2 Stabilization
    print(f"  [H261] WP2 Stabilization: {H261_WP_STABILIZE_STEPS} steps")
    for stab_step in range(H261_WP_STABILIZE_STEPS):
        v199_watchdog_start()
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        v199_watchdog_stop()
    h261_wp2_stab_force_l, h261_wp2_stab_force_r = get_contact_force()
    print(f"  [H261 WP2 Stabilized] Force: L={h261_wp2_stab_force_l:.1f}N R={h261_wp2_stab_force_r:.1f}N")

    print("=" * 60)
    print("  [H261] Intermediate Waypoints Complete - Proceeding to Stage C1")
    print("=" * 60)

    # H176 Stage C1: Intermediate position - Right X=0.49 (split from 0.38→0.50)
    # Purpose: Split large X movement into 2 stages to reduce left-end stress
    # Reference: LL-2026-01-15-PHY-008 (Stage C step 190/600 NaN, Force R/L=2.4)
    # H194: Apply proportional_follow to Stage C1 (same as H193 Part 2B)
    H177_STAGE_C1_STEPS = 600  # H178: 600 steps per sub-stage (PHY-009 recommendation)
    print("  Stage C1: Intermediate position - Right X=0.49 (H177: PHY-009 recommendation)")
    H160_STAGE_C1_Z = 0.90

    # H194: Get current position for proportional_follow calculation
    c1_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    c1_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # H194: Base target coordinates
    pC1_base_target_l = torch.tensor([[0.36, -0.14, H160_STAGE_C1_Z]], device=device)
    pC1_target_r = torch.tensor([[0.49, 0.12, H160_STAGE_C1_Z]], device=device)

    # H194: Calculate Right arm X movement during Stage C1
    c1_right_x_movement = pC1_target_r[0, 0] - c1_start_r[0, 0]

    # H194: Left arm follows 60% of Right arm X movement (proportional_follow)
    if abs(c1_right_x_movement) > H193_MIN_THRESHOLD_CM / 100.0:
        c1_left_x_follow = c1_right_x_movement * H193_LEFT_FOLLOW_RATIO
        pC1_target_l = pC1_base_target_l.clone()
        pC1_target_l[0, 0] = pC1_base_target_l[0, 0] + c1_left_x_follow
        print(f"  [H194] Stage C1 proportional follow: Right X movement={c1_right_x_movement*100:.2f}cm, Left X follow={c1_left_x_follow*100:.2f}cm ({H193_LEFT_FOLLOW_RATIO*100:.0f}%)")
        print(f"    Original L target X: {pC1_base_target_l[0,0]:.4f} → Adjusted: {pC1_target_l[0,0]:.4f}")
    else:
        pC1_target_l = pC1_base_target_l
        print(f"  [H194] Stage C1 proportional follow: Right X movement={c1_right_x_movement*100:.2f}cm < threshold {H193_MIN_THRESHOLD_CM}cm, skipped")

    print(f"  Target: L=({pC1_target_l[0,0]:.3f}, {pC1_target_l[0,1]:.3f}, {H160_STAGE_C1_Z}), R=({pC1_target_r[0,0]:.3f}, {pC1_target_r[0,1]:.3f}, {H160_STAGE_C1_Z})")
    pC1_pos_l, pC1_pos_r, pC1_quat_l, pC1_quat_r, _ = run_joint_space_motion_with_collection(
        pC1_target_l, pC1_target_r, H177_STAGE_C1_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name="H177 Stage C1 (Right X=0.49, PHY-009)",
        force_adaptive_velocity=True,  # H179: Enable Force R monitoring (PHY-010)
        target_quat_wxyz=GRIPPER_ROTATED_90_QUAT_WXYZ  # H259: 90° Z-rotation for hook draping
    )
    sC1_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sC1_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sC1_force_l, sC1_force_r = get_contact_force()
    print(f"  [H176 Stage C1] L=({sC1_ee_l[0,0]:.3f}, {sC1_ee_l[0,1]:.3f}, {sC1_ee_l[0,2]:.3f}), R=({sC1_ee_r[0,0]:.3f}, {sC1_ee_r[0,1]:.3f}, {sC1_ee_r[0,2]:.3f})")
    print(f"  Force: L={sC1_force_l:.1f}N R={sC1_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H176 Stage C1!")

    # H176 Stage C2: Final Stage C position - Right X controlled by H270 constant
    # Continues from C1 (X=0.49) to final (H270_STAGE_CD_RIGHT_TARGET_X)
    # H194: Apply proportional_follow to Stage C2 (same as H193 Part 2B)
    H176_STAGE_C2_STEPS = 400  # H176: 400 steps per sub-stage
    print(f"  Stage C2: Final position - Right X={H270_STAGE_CD_RIGHT_TARGET_X:.2f} (H176/H270)")
    H160_STAGE_C2_Z = 0.90

    # H194: Get current position for proportional_follow calculation
    c2_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    c2_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # H194: Base target coordinates
    pC2_base_target_l = torch.tensor([[0.35, -0.12, H160_STAGE_C2_Z]], device=device)
    pC2_target_r = torch.tensor([[H270_STAGE_CD_RIGHT_TARGET_X, 0.11, H160_STAGE_C2_Z]], device=device)

    # H194: Calculate Right arm X movement during Stage C2
    c2_right_x_movement = pC2_target_r[0, 0] - c2_start_r[0, 0]

    # H194: Left arm follows 60% of Right arm X movement (proportional_follow)
    if abs(c2_right_x_movement) > H193_MIN_THRESHOLD_CM / 100.0:
        c2_left_x_follow = c2_right_x_movement * H193_LEFT_FOLLOW_RATIO
        pC2_target_l = pC2_base_target_l.clone()
        pC2_target_l[0, 0] = pC2_base_target_l[0, 0] + c2_left_x_follow
        print(f"  [H194] Stage C2 proportional follow: Right X movement={c2_right_x_movement*100:.2f}cm, Left X follow={c2_left_x_follow*100:.2f}cm ({H193_LEFT_FOLLOW_RATIO*100:.0f}%)")
        print(f"    Original L target X: {pC2_base_target_l[0,0]:.4f} → Adjusted: {pC2_target_l[0,0]:.4f}")
    else:
        pC2_target_l = pC2_base_target_l
        print(f"  [H194] Stage C2 proportional follow: Right X movement={c2_right_x_movement*100:.2f}cm < threshold {H193_MIN_THRESHOLD_CM}cm, skipped")

    print(f"  Target: L=({pC2_target_l[0,0]:.3f}, {pC2_target_l[0,1]:.3f}, {H160_STAGE_C2_Z}), R=({pC2_target_r[0,0]:.3f}, {pC2_target_r[0,1]:.3f}, {H160_STAGE_C2_Z})")
    pC2_pos_l, pC2_pos_r, pC2_quat_l, pC2_quat_r, _ = run_joint_space_motion_with_collection(
        pC2_target_l, pC2_target_r, H176_STAGE_C2_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name=f"H176 Stage C2 (Right X={H270_STAGE_CD_RIGHT_TARGET_X:.2f})",
        force_adaptive_velocity=True,  # H179: Enable Force R monitoring (PHY-010)
        target_quat_wxyz=GRIPPER_ROTATED_90_QUAT_WXYZ  # H259: 90° Z-rotation for hook draping
    )
    sC_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    sC_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sC_force_l, sC_force_r = get_contact_force()
    print(f"  [H176 Stage C2] L=({sC_ee_l[0,0]:.3f}, {sC_ee_l[0,1]:.3f}, {sC_ee_l[0,2]:.3f}), R=({sC_ee_r[0,0]:.3f}, {sC_ee_r[0,1]:.3f}, {sC_ee_r[0,2]:.3f})")
    print(f"  Force: L={sC_force_l:.1f}N R={sC_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H176 Stage C2!")

    # H172 Stage D: Final position - Z=0.88, Right X controlled by H270 constant
    # H172: X=0.50 provides margin=9.9° (LL-2026-01-15-IK-019)
    # H270: single-variable experiment uses X=0.48 for Stage C2→D consistency
    # H194: Apply proportional_follow to Stage D (same as H193 Part 2B)
    print(f"  Stage D: Final position - Right to X={H270_STAGE_CD_RIGHT_TARGET_X:.2f} at Z=0.88 (H172/H270)")
    H160_STAGE_D_Z = 0.88

    # H194: Get current position for proportional_follow calculation
    d_start_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    d_start_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()

    # H194: Base target coordinates
    pD_base_target_l = torch.tensor([[0.33, WAYPOINT_PHASE45_LEFT[1], H160_STAGE_D_Z]], device=device)  # H248: Y=0 (was -0.10)
    pD_target_r = torch.tensor([[H270_STAGE_CD_RIGHT_TARGET_X, WAYPOINT_PHASE45_RIGHT[1], H160_STAGE_D_Z]], device=device)  # H248: Y=0 (was 0.10)

    # H194: Calculate Right arm X movement during Stage D
    d_right_x_movement = pD_target_r[0, 0] - d_start_r[0, 0]

    # H194: Left arm follows 60% of Right arm X movement (proportional_follow)
    if abs(d_right_x_movement) > H193_MIN_THRESHOLD_CM / 100.0:
        d_left_x_follow = d_right_x_movement * H193_LEFT_FOLLOW_RATIO
        pD_target_l = pD_base_target_l.clone()
        pD_target_l[0, 0] = pD_base_target_l[0, 0] + d_left_x_follow
        print(f"  [H194] Stage D proportional follow: Right X movement={d_right_x_movement*100:.2f}cm, Left X follow={d_left_x_follow*100:.2f}cm ({H193_LEFT_FOLLOW_RATIO*100:.0f}%)")
        print(f"    Original L target X: {pD_base_target_l[0,0]:.4f} → Adjusted: {pD_target_l[0,0]:.4f}")
    else:
        pD_target_l = pD_base_target_l
        print(f"  [H194] Stage D proportional follow: Right X movement={d_right_x_movement*100:.2f}cm < threshold {H193_MIN_THRESHOLD_CM}cm, skipped")

    print(f"  Target: L=({pD_target_l[0,0]:.3f}, {pD_target_l[0,1]:.3f}, {H160_STAGE_D_Z}), R=({pD_target_r[0,0]:.3f}, {pD_target_r[0,1]:.3f}, {H160_STAGE_D_Z})")
    p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r, _ = run_joint_space_motion_with_collection(
        pD_target_l, pD_target_r, H160_STAGE_STEPS, GRIPPER_CLOSE, phase=4,
        stage_name=f"H172 Stage D (Right X={H270_STAGE_CD_RIGHT_TARGET_X:.2f} final)",
        force_adaptive_velocity=True,  # H180: Enable Force R monitoring (PHY-011)
        target_quat_wxyz=GRIPPER_ROTATED_90_QUAT_WXYZ  # H259: 90° Z-rotation for hook draping
    )

    # Log final EE positions with contact force
    final_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    final_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    sD_force_l, sD_force_r = get_contact_force()
    print(f"  [H160 Stage D] L=({final_ee_l[0,0]:.3f}, {final_ee_l[0,1]:.3f}, {final_ee_l[0,2]:.3f}), R=({final_ee_r[0,0]:.3f}, {final_ee_r[0,1]:.3f}, {final_ee_r[0,2]:.3f})")
    print(f"  Force: L={sD_force_l:.1f}N R={sD_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
    print(f"  H160 Stage D Complete: L=({final_ee_l[0,0]:.3f}, {final_ee_l[0,1]:.3f}, {final_ee_l[0,2]:.3f})")
    print(f"                         R=({final_ee_r[0,0]:.3f}, {final_ee_r[0,1]:.3f}, {final_ee_r[0,2]:.3f})")

    # Check cable NaN
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after H160 Stage D!")

    # Stabilization after H160 trajectory
    print("  [H160] Holding for stabilization (30 steps)...")
    hold_position(30, gripper_val=GRIPPER_CLOSE)

    # H190: Skip Phase 5 if grip loss detected (NaN prevention)
    if h190_grip_loss_detected:
        print("  [H190 ABORT] Skipping Phase 5 due to grip loss in Stage B.5c")
        print("  [H190] This prevents NaN from propagating. Fix grip loss first.")
        # Log final state before early exit
        abort_force_l, abort_force_r = get_contact_force()
        print(f"  [H190] Abort state: Force L={abort_force_l:.1f}N R={abort_force_r:.1f}N, cable_Z: {get_cable_z_str()}")
        return False

    # ============================================================
    # GATE-R: Rotation check before Phase 5 (v24.82)
    # ============================================================
    if ENABLE_GATE_SYSTEM and GATE_R_ENABLED:
        from scipy.spatial.transform import Rotation as R

        # Get current EE quaternion (after Stage D with 90° rotation)
        gate_r_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
        gate_r_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

        # Use left arm quaternion for rotation check (both should have same rotation)
        # Quaternion format: Isaac Lab uses (w, x, y, z)
        q_current_wxyz = (gate_r_quat_l[0, 0].item(), gate_r_quat_l[0, 1].item(),
                          gate_r_quat_l[0, 2].item(), gate_r_quat_l[0, 3].item())

        # Pre-rotation quaternion (GRIPPER_DOWN)
        q_pre_wxyz = GRIPPER_DOWN_QUAT_WXYZ

        # Convert to scipy format (x, y, z, w)
        q_pre_xyzw = np.array([q_pre_wxyz[1], q_pre_wxyz[2], q_pre_wxyz[3], q_pre_wxyz[0]])
        q_cur_xyzw = np.array([q_current_wxyz[1], q_current_wxyz[2], q_current_wxyz[3], q_current_wxyz[0]])

        r_pre = R.from_quat(q_pre_xyzw)
        r_cur = R.from_quat(q_cur_xyzw)
        r_delta = r_cur * r_pre.inv()
        delta_deg = np.degrees(r_delta.magnitude())

        r_ok = abs(delta_deg - 90) <= GATE_R_ROT_TOL_DEG

        log_gate_eval("Gate-R", "4.5c", r_ok,
                      {"delta_rot_deg": delta_deg, "q_current": q_current_wxyz},
                      {"target_deg": 90, "tolerance_deg": GATE_R_ROT_TOL_DEG})

        if not r_ok:
            print(f"[GATE-R] FAILED: delta_rot={delta_deg:.1f}° (target=90°±{GATE_R_ROT_TOL_DEG}°)")
            finalize_video()  # v24.30: Save video before exit
            return early_exit("Gate-R", "4.5c",
                             {"delta_rot_deg": delta_deg, "target_deg": 90},
                             "FAIL")
        else:
            print(f"[GATE-R] PASSED: delta_rot={delta_deg:.1f}° (target=90°±{GATE_R_ROT_TOL_DEG}°)")

    # ============================================================
    # PHASE 5: H160 - Low Z trajectory for hook approach
    # ============================================================
    # H160: Use low Z (0.89-0.90) instead of high Z (1.04-1.09)
    # Right arm at X=0.70 requires Z≤0.90 for safe IK margin (LL-2026-01-14-IK-016)
    print("\n[Phase 5] H160: Above hook using low Z trajectory...")
    print(f"  [H160] Using Z=0.89→0.90 instead of Z=1.04→1.09")
    print(f"  [H160] Right arm at X=0.70, Z=0.90 has IK margin≈8.1°")

    # H160 Phase 5 waypoint overrides (role swap + low Z)
    H160_PHASE5_L = (0.33, -0.10)  # Left stays back
    H160_PHASE5_R = (0.50, 0.10)   # H178: Right at X=0.50 (HOOK_X per CLAUDE.md)

    # H120: Stabilization before Phase 5 to reduce transition jump
    # H187: Extended stabilization 50→150 steps to prevent Force spike at Phase 5 start
    print("  [H187] Phase 4→5 transition stabilization (150 steps)...")
    for _ in range(150):
        # Hold current position target
        current_joints_l = robot_left.data.joint_pos[0].unsqueeze(0).clone()
        current_joints_r = robot_right.data.joint_pos[0].unsqueeze(0).clone()
        robot_left.set_joint_position_target(current_joints_l)
        robot_right.set_joint_position_target(current_joints_r)
        robot_left.write_data_to_sim()
        robot_right.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get current EE positions after H160 Stage D
    p45_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p45_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p45_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p45_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Log Phase 5 start contact force
    p5_start_force_l, p5_start_force_r = get_contact_force()
    print(f"  [P5 Start] Contact: L={p5_start_force_l:.1f}N, R={p5_start_force_r:.1f}N, cable_Z: {get_cable_z_str()}")

    # Phase 5a: First Z rise (0.88 → 0.89) - H160 low Z trajectory
    print("  --- Phase 5a: H160 Z rise (0.88 → 0.89) ---")
    H160_PHASE5A_Z = 0.89
    p5a_target_l = torch.tensor([[H160_PHASE5_L[0], H160_PHASE5_L[1], H160_PHASE5A_Z]], device=device)
    p5a_target_r = torch.tensor([[H160_PHASE5_R[0], H160_PHASE5_R[1], H160_PHASE5A_Z]], device=device)
    print(f"  Target: L=({p5a_target_l[0,0]:.3f}, {p5a_target_l[0,1]:.3f}, {p5a_target_l[0,2]:.3f})")
    print(f"          R=({p5a_target_r[0,0]:.3f}, {p5a_target_r[0,1]:.3f}, {p5a_target_r[0,2]:.3f})")

    # H120: Increase steps to reduce per-step change (150->300)
    PHASE5A_STEPS = 300
    p5a_pos_l, p5a_pos_r, p5a_quat_l, p5a_quat_r = run_diff_ik_motion_with_collection(
        p45_pos_l, p45_pos_r, p45_quat_l, p45_quat_r,
        p5a_target_l, p5a_target_r, PHASE5A_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5a completion
    s5a_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s5a_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5a Complete: L=({s5a_ee_l[0,0]:.3f}, {s5a_ee_l[0,1]:.3f}, {s5a_ee_l[0,2]:.3f})")
    print(f"                     R=({s5a_ee_r[0,0]:.3f}, {s5a_ee_r[0,1]:.3f}, {s5a_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5a
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5a!")

    # Stabilization (50 steps) - H220: reduced from 100 to prevent excessive relaxation
    print("  [Stabilization] 50 steps (H220)...")
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 5b: Second Z rise (0.89 → 0.90) - H160 above hook position
    print("  --- Phase 5b: H160 Z rise (0.89 → 0.90) - above hook ---")
    # Get current positions after stabilization
    p5a_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p5a_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p5a_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p5a_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    H160_PHASE5B_Z = 0.90  # Above hook (HOOK_Z = 0.90)
    p5_target_l = torch.tensor([[H160_PHASE5_L[0], H160_PHASE5_L[1], H160_PHASE5B_Z]], device=device)
    p5_target_r = torch.tensor([[H160_PHASE5_R[0], H160_PHASE5_R[1], H160_PHASE5B_Z]], device=device)
    print(f"  Target: L=({p5_target_l[0,0]:.3f}, {p5_target_l[0,1]:.3f}, {p5_target_l[0,2]:.3f})")
    print(f"          R=({p5_target_r[0,0]:.3f}, {p5_target_r[0,1]:.3f}, {p5_target_r[0,2]:.3f})")

    # H120: Increase steps to reduce per-step change (150->300)
    PHASE5B_STEPS = 300
    p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r = run_diff_ik_motion_with_collection(
        p5a_pos_l, p5a_pos_r, p5a_quat_l, p5a_quat_r,
        p5_target_l, p5_target_r, PHASE5B_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5b completion
    s5b_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s5b_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5b Complete: L=({s5b_ee_l[0,0]:.3f}, {s5b_ee_l[0,1]:.3f}, {s5b_ee_l[0,2]:.3f})")
    print(f"                     R=({s5b_ee_r[0,0]:.3f}, {s5b_ee_r[0,1]:.3f}, {s5b_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5b
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5b!")

    # ============================================================
    # PHASE 5.5: H160 - Simplified low Z descent for hook placement
    # ============================================================
    # H160: Start at Z=0.90 (end of Phase 5b), descend to Z=0.85 (hook level)
    # Much simpler than original (5cm descent vs 24cm descent)
    print("\n[Phase 5.5] H160: Lower onto hook (simplified low Z)...")
    print(f"  [H160] Z=0.90 → Z=0.85 (5cm descent, vs original 24cm)")

    # H160 Phase 5.5 waypoint overrides
    H160_PHASE55_L = (0.33, -0.10)  # Left stays back
    H160_PHASE55_R = (0.50, 0.10)   # H178: Right at X=0.50 (HOOK_X per CLAUDE.md)

    # Get current EE positions (after Phase 5b at Z=0.90)
    p5_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p5_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p5_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p5_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    # Phase 5.5a: First Z descent (0.90 → 0.88)
    print("  --- Phase 5.5a: H160 Z descent (0.90 → 0.88) ---")
    H160_PHASE55A_Z = 0.88
    p55a_target_l = torch.tensor([[H160_PHASE55_L[0], H160_PHASE55_L[1], H160_PHASE55A_Z]], device=device)
    p55a_target_r = torch.tensor([[H160_PHASE55_R[0], H160_PHASE55_R[1], H160_PHASE55A_Z]], device=device)
    print(f"  Target: L=({p55a_target_l[0,0]:.3f}, {p55a_target_l[0,1]:.3f}, {p55a_target_l[0,2]:.3f})")
    print(f"          R=({p55a_target_r[0,0]:.3f}, {p55a_target_r[0,1]:.3f}, {p55a_target_r[0,2]:.3f})")

    PHASE55A_STEPS = 150
    p55a_pos_l, p55a_pos_r, p55a_quat_l, p55a_quat_r = run_diff_ik_motion_with_collection(
        p5_pos_l, p5_pos_r, p5_quat_l, p5_quat_r,
        p55a_target_l, p55a_target_r, PHASE55A_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5a completion
    s55a_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55a_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5a Complete: L=({s55a_ee_l[0,0]:.3f}, {s55a_ee_l[0,1]:.3f}, {s55a_ee_l[0,2]:.3f})")
    print(f"                       R=({s55a_ee_r[0,0]:.3f}, {s55a_ee_r[0,1]:.3f}, {s55a_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5a
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5a!")

    # Stabilization (50 steps)
    print("  [Stabilization] 50 steps...")
    for _ in range(50):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Phase 5.5b: Final descent to hook level (0.88 → 0.85)
    print("  --- Phase 5.5b: H160 hook level descent (0.88 → 0.85) ---")
    # Get current positions after stabilization
    p55a_pos_l = robot_left.data.body_pos_w[:, jacobian_body_left].clone()
    p55a_pos_r = robot_right.data.body_pos_w[:, jacobian_body_right].clone()
    p55a_quat_l = robot_left.data.body_quat_w[:, jacobian_body_left].clone()
    p55a_quat_r = robot_right.data.body_quat_w[:, jacobian_body_right].clone()

    H160_PHASE55B_Z = 0.85  # Hook level (HOOK_Z = 0.90, cable placed below)
    p55b_target_l = torch.tensor([[H160_PHASE55_L[0], H160_PHASE55_L[1], H160_PHASE55B_Z]], device=device)
    p55b_target_r = torch.tensor([[H160_PHASE55_R[0], H160_PHASE55_R[1], H160_PHASE55B_Z]], device=device)
    print(f"  Target: L=({p55b_target_l[0,0]:.3f}, {p55b_target_l[0,1]:.3f}, {p55b_target_l[0,2]:.3f})")
    print(f"          R=({p55b_target_r[0,0]:.3f}, {p55b_target_r[0,1]:.3f}, {p55b_target_r[0,2]:.3f})")

    PHASE55B_STEPS = 150
    p55c_pos_l, p55c_pos_r, p55c_quat_l, p55c_quat_r = run_diff_ik_motion_with_collection(
        p55a_pos_l, p55a_pos_r, p55a_quat_l, p55a_quat_r,
        p55b_target_l, p55b_target_r, PHASE55B_STEPS, GRIPPER_CLOSE, phase=5
    )

    # Log Phase 5.5b completion
    s55c_ee_l = robot_left.data.body_pos_w[:, jacobian_body_left]
    s55c_ee_r = robot_right.data.body_pos_w[:, jacobian_body_right]
    print(f"  Phase 5.5b Complete: L=({s55c_ee_l[0,0]:.3f}, {s55c_ee_l[0,1]:.3f}, {s55c_ee_l[0,2]:.3f})")
    print(f"                       R=({s55c_ee_r[0,0]:.3f}, {s55c_ee_r[0,1]:.3f}, {s55c_ee_r[0,2]:.3f})")

    # Check cable NaN after Phase 5.5b
    if not check_cable_nan():
        print("  [ERROR] Cable NaN after Phase 5.5b!")

    # Short stabilization before release
    print("  [Stabilization] 20 steps before release...")
    for _ in range(20):
        sim.step()
        scene.update(sim.get_physics_dt())

    # ============================================================
    # GATE-H: Hook proximity check before Phase 6 (v24.82)
    # ============================================================
    if ENABLE_GATE_SYSTEM and GATE_H_ENABLED:
        # H260: Skip Gate-H when no cable (PG0 kinematics test)
        if H239_NO_CABLE_SPAWN or cable is None:
            print("[GATE-H] SKIPPED (no cable, PG0 mode)")
            h_ok = True
        else:
            # Get cable center position (average of all segments)
            cable_pos_all = cable.data.body_pos_w[0].cpu().numpy()  # [N_segments, 3]
            cable_center = cable_pos_all.mean(axis=0)

            # Hook position
            hook_pos = np.array([HOOK_X, HOOK_Y, HOOK_Z])

            # Calculate cable-hook distance
            cable_hook_dist = np.linalg.norm(cable_center - hook_pos)

            h_ok = cable_hook_dist < GATE_H_CABLE_HOOK_DIST_MAX

            log_gate_eval("Gate-H", "5.5c", h_ok,
                          {"cable_hook_dist": cable_hook_dist,
                           "cable_center": cable_center.tolist(),
                           "hook_pos": hook_pos.tolist()},
                          {"cable_hook_dist_max": GATE_H_CABLE_HOOK_DIST_MAX})

            if not h_ok:
                print(f"[GATE-H] FAILED: cable_hook_dist={cable_hook_dist*100:.1f}cm > {GATE_H_CABLE_HOOK_DIST_MAX*100:.1f}cm")
                # Gate-H failure at Phase 5.5c is PARTIAL_SUCCESS (reached late stage)
                finalize_video()  # v24.30: Save video before exit
                return early_exit("Gate-H", "5.5c",
                                 {"cable_hook_dist": cable_hook_dist},
                                 "PARTIAL_SUCCESS")
            else:
                print(f"[GATE-H] PASSED: cable_hook_dist={cable_hook_dist*100:.1f}cm < {GATE_H_CABLE_HOOK_DIST_MAX*100:.1f}cm")

    # ============================================================
    # PHASE 6: RELEASE AND RETREAT (from actual current position)
    # ============================================================
    print("\n[Phase 6] Release and retreat...")

    # Get actual joint positions after Phase 5.5 Diff IK motion
    p55_actual_left = robot_left.data.joint_pos[0, :7].cpu().numpy().tolist()
    p55_actual_right = robot_right.data.joint_pos[0, :7].cpu().numpy().tolist()
    print(f"  Actual joints after Phase 5.5: Left[0]={p55_actual_left[0]:.3f}, Right[0]={p55_actual_right[0]:.3f}")

    # Stabilize at current position
    for i in range(RELEASE_STABILIZE_STEPS):
        set_robot_joints(robot_left, p55_actual_left, GRIPPER_CLOSE)
        set_robot_joints(robot_right, p55_actual_right, GRIPPER_CLOSE)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, GRIPPER_CLOSE, GRIPPER_CLOSE)

    # Release gripper gradually
    for i in range(RELEASE_GRIPPER_STEPS):
        alpha = (i + 1) / RELEASE_GRIPPER_STEPS
        gripper_val = GRIPPER_CLOSE + alpha * (GRIPPER_OPEN - GRIPPER_CLOSE)
        set_robot_joints(robot_left, p55_actual_left, gripper_val)
        set_robot_joints(robot_right, p55_actual_right, gripper_val)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, gripper_val, gripper_val)

    # Retreat: Current position -> Phase 7 (Home) via joint interpolation
    for step in range(PHASE55_TO_6_STEPS + POST_RETREAT_STEPS):
        alpha = (step + 1) / (PHASE55_TO_6_STEPS + POST_RETREAT_STEPS)
        left_joints = [p55 + alpha * (p7 - p55) for p55, p7 in zip(p55_actual_left, PHASE7_LEFT_JOINTS)]
        right_joints = [p55 + alpha * (p7 - p55) for p55, p7 in zip(p55_actual_right, PHASE7_RIGHT_JOINTS)]
        set_robot_joints(robot_left, left_joints, GRIPPER_OPEN)
        set_robot_joints(robot_right, right_joints, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if step % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(6, GRIPPER_OPEN, GRIPPER_OPEN)

    # ============================================================
    # PHASE 7: HOME RETURN (Joint interpolation - already at home from Phase 6)
    # ============================================================
    print("\n[Phase 7] Home return...")

    # Stabilize at home
    for i in range(100):
        set_robot_joints(robot_left, PHASE7_LEFT_JOINTS, GRIPPER_OPEN)
        set_robot_joints(robot_right, PHASE7_RIGHT_JOINTS, GRIPPER_OPEN)
        sim.step()
        scene.update(sim.get_physics_dt())
        if i % FRAME_COLLECT_INTERVAL == 0:
            collector.collect_step(7, GRIPPER_OPEN, GRIPPER_OPEN)

    print("  Home position reached")

    # ============================================================
    # PHASE 8: CYCLE RESET
    # ============================================================
    print("\n[Phase 8] Cycle reset...")
    # H160: Skip cable reset when cable is disabled
    if H160_DISABLE_CABLE:
        print("  [H160] Cable reset SKIPPED (cable disabled)")
        reset_success = True
    else:
        reset_success = reset_cable_to_initial()
        if reset_success:
            print("  [OK] Cable reset complete")
        else:
            print("  [WARNING] Cable reset had issues, but continuing")

    # Save cycle data
    collector.save_cycle(cycle_idx)

    return True


# ============================================================
# MAIN LOOP (v71: skip strategy + guaranteed partial H5 save on failure)
# ============================================================
success_count = 0
total_retries = 0

cycle_idx = 0
while cycle_idx < args.num_cycles:
    retry_count = 0

    while retry_count <= MAX_RETRIES:
        print(f"\n{'='*80}")
        print(f"[Cycle {cycle_idx}/{args.num_cycles}] Starting... (retry={retry_count})")
        print(f"{'='*80}")

        try:
            result = run_cycle(cycle_idx)
            # H227: Handle dict return from early exit
            if isinstance(result, dict) and result.get("status") == "H227_EARLY_EXIT":
                print(f"\n[H227] Phase {result['phase_reached']} early exit successful")
                print(f"  Cable grasped: {result['cable_grasped']}")
                success_count += 1
                # Force loop exit after early exit (no more cycles)
                cycle_idx = args.num_cycles
                break
            # H228: Handle Phase 3 Start early exit
            elif isinstance(result, dict) and result.get("status") == "H228_EARLY_EXIT":
                print(f"\n[H228] Phase 3 early exit successful after {result['lift_steps_completed']} lift steps")
                print(f"  Elapsed: {result['elapsed_seconds']:.1f}s")
                print(f"  EE L: {result['ee_pos_l']}")
                print(f"  EE R: {result['ee_pos_r']}")
                success_count += 1
                # Force loop exit after early exit (no more cycles)
                cycle_idx = args.num_cycles
                break
            elif result:
                success_count += 1
            # Cycle completed (success or graceful failure)
            break

        except NaNDetectedException as e:
            print(f"\n[ERROR] NaN detected at {e.location}")

            # v71: Save partial H5 for video analysis (even on early failure)
            partial_file = collector.save_partial_cycle(
                cycle_idx,
                failure_reason=f"NaN at {e.location}"
            )
            if partial_file:
                print(f"[Save] Partial data saved: {partial_file}")

            retry_count += 1
            total_retries += 1

            if retry_count > MAX_RETRIES:
                print(f"[FATAL] Max retries ({MAX_RETRIES}) exceeded. Skipping cycle {cycle_idx}.")
            else:
                print(f"[RETRY] Restarting cycle (attempt {retry_count}/{MAX_RETRIES})")
                # Reset scene for retry
                sim.reset()
                for _ in range(10):
                    sim.step()
                continue

    cycle_idx += 1

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("DATA COLLECTION SUMMARY (v71 - Guaranteed Partial H5 Save)")
print("=" * 70)
print(f"\nCycles completed: {success_count}/{args.num_cycles}")
print(f"Total retries: {total_retries}")
print(f"Output directory: {args.output_dir}")

# List saved files (v71: separate complete and partial)
all_h5_files = [f for f in os.listdir(args.output_dir) if f.endswith('.h5')]
complete_files = [f for f in all_h5_files if '_partial' not in f]
partial_files = [f for f in all_h5_files if '_partial' in f]

print(f"\nComplete files: {len(complete_files)}")
for f in sorted(complete_files):
    filepath = os.path.join(args.output_dir, f)
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  - {f} ({size_mb:.1f} MB)")

if partial_files:
    print(f"\nPartial files (failed cycles - for debugging): {len(partial_files)}")
    for f in sorted(partial_files):
        filepath = os.path.join(args.output_dir, f)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        # Read failure reason from H5
        try:
            with h5py.File(filepath, 'r') as h5f:
                reason = h5f.attrs.get('failure_reason', 'unknown')
                last_phase = h5f.attrs.get('last_phase', -1)
                n_steps = h5f.attrs.get('num_steps', 0)
            print(f"  - {f} ({size_mb:.1f} MB) [Phase {last_phase}, {n_steps} steps] {reason}")
        except Exception:
            print(f"  - {f} ({size_mb:.1f} MB)")

# v24.30: Video finalization is handled by atexit.register(finalize_video)
# This explicit call ensures video is saved even on normal exit
# The finalize_video function is idempotent (safe to call multiple times)
finalize_video()

print("\n" + "=" * 70)
print("DATA COLLECTION COMPLETE")
print("=" * 70)

# Guard against shutdown hang in replicator/close.
def _safe_close(app, timeout_s: float = 30.0) -> None:
    import threading

    err = {}

    def _close():
        try:
            app.close()
        except Exception as exc:
            err["exc"] = exc

    t = threading.Thread(target=_close, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        print(f"[WARN] simulation_app.close timed out after {timeout_s}s; skipping shutdown.")
        return
    if "exc" in err:
        print(f"[WARN] simulation_app.close raised: {err['exc']}")

_safe_close(simulation_app)
