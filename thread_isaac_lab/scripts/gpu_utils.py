"""GPU auto-selection and training utilities for THREAD training scripts.

Usage in train_*.py:
    from gpu_utils import resolve_device, snapshot_env_config
    args.device = resolve_device(args.device)
    os.environ["NEWTON_DEVICE"] = args.device
    ...
    summary["env_config"] = snapshot_env_config(env)
"""

import os
import subprocess
import re


def resolve_device(device: str, max_procs: int = 2) -> str:
    """Resolve device string, handling 'auto' by selecting the least loaded GPU.

    Args:
        device: 'auto' or 'cuda:N'. If not 'auto', returned as-is.
        max_procs: Maximum training processes per GPU.

    Returns:
        'cuda:N' string for the selected GPU.

    Raises:
        RuntimeError: If all GPUs are at capacity.
    """
    if device != "auto":
        return device

    script = os.path.join(os.path.dirname(__file__), "select_gpu.sh")
    result = subprocess.run(
        ["bash", script],
        capture_output=True, text=True,
        env={**os.environ, "MAX_PROCS_PER_GPU": str(max_procs)},
    )

    # stderr has the diagnostic log, print it
    if result.stderr:
        print(result.stderr.rstrip())

    if result.returncode != 0:
        raise RuntimeError(
            f"GPU auto-selection failed (all GPUs at capacity, max {max_procs} procs each)"
        )

    selected = result.stdout.strip()
    if not re.match(r"^cuda:\d+$", selected):
        raise RuntimeError(f"select_gpu.sh returned unexpected output: {selected!r}")

    return selected


# --- Env config attributes to record in summary.json ---
_ENV_CONFIG_ATTRS = [
    # Action scaling
    "POS_ACTION_SCALE", "ROT_ACTION_SCALE",
    "ADAPTIVE_POS_SCALE", "FINE_THRESHOLD", "MIN_POS_SCALE",
    # Episode
    "MAX_EPISODE_STEPS", "PHYSICS_STEPS_PER_RL",
    "EXPLOSION_DIST_THRESH",
    # Observation / cable
    "GRIP_SEG_WINDOW", "INIT_XY_NOISE",
    # Reward
    "REWARD_MODE",
    "EPS_POS", "EPS_POS_COARSE", "EPS_ORI",
    "W_POS", "W_ORI",
    "RANGE_POS", "RANGE_ORI",
    "PROGRESS_SCALE", "PROGRESS_W_POS", "PROGRESS_W_ORI", "PROGRESS_W_COUPLED",
    "R_STEP_BONUS", "R_TASK_BONUS", "R_PENALTY",
    # Finger / success thresholds
    "FINGER_CLOSE_POS_THRESH", "FINGER_CLOSE_ORI_THRESH",
    "CLAMP_DIST_THRESH", "CLAMP_ORI_THRESH",
    # IC-specific
    "W_GROOVE", "GROOVE_BODIES_NORM", "GROOVE_CHECK_RADIUS",
    "R_DROP", "DROP_Z_THRESH",
    "SEATED_POS_THRESH", "SEATED_ORI_THRESH", "SUSTAIN_STEPS", "MIN_GROOVE_BODIES",
    # AR-specific
    "R_DROP_PENALTY", "CABLE_DROP_Z_THRESH",
    "TARGET_EMA_ALPHA",
    "CLOSE_ACTION_DAMPING", "ORI_GATE_POS_THRESH", "ORI_GATE_ORI_THRESH",
    "C5_SUSTAIN_STEPS",
    "W_TAIL", "THRESH_WARN",
]


def snapshot_env_config(env) -> dict:
    """Capture env class-level parameters for summary.json reproducibility.

    Returns a dict of {attr: value} for all known config attributes that exist on env.
    """
    cfg = {}
    for attr in _ENV_CONFIG_ATTRS:
        if hasattr(env, attr):
            val = getattr(env, attr)
            # Convert non-serializable types
            if hasattr(val, "item"):
                val = val.item()
            cfg[attr] = val
    return cfg
