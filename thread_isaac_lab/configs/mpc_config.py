# thread_isaac_lab/configs/mpc_config.py
"""
MPC Configuration Parameters for Model-Based Control.

This configuration defines parameters for:
- CEM-based MPC using the trained World Model (MPCConfig)
- Pure MPPI demo trajectory generation on Newton VBD (MPPIConfig)
"""

from dataclasses import dataclass, field
from typing import Dict, Any

# =============================================================================
# MPC Core Parameters
# =============================================================================

@dataclass
class MPCConfig:
    """Configuration for CEM-based MPC Controller."""

    # Planning horizon
    horizon: int = 10              # Number of steps to plan ahead

    # CEM optimization parameters
    num_candidates: int = 500      # Number of action sequences to sample
    elite_ratio: float = 0.1       # Top 10% used for next iteration
    cem_iterations: int = 3        # Number of CEM refinement iterations

    # Action space
    action_dim: int = 18           # 9 (left) + 9 (right)

    # Action bounds (joint delta per step)
    action_low: float = -0.05      # -0.05 rad/step (~3 degrees)
    action_high: float = 0.05      # +0.05 rad/step (~3 degrees)

    # Gripper action bounds (indices 7, 8 for left; 16, 17 for right)
    gripper_action_low: float = -0.01   # Gripper delta
    gripper_action_high: float = 0.01

    # Device
    device: str = "cuda"

    # Model paths
    world_model_path: str = "checkpoints/world_model_4cam/phase2_best.pt"

    # Discount factor for future rewards
    gamma: float = 0.99

    # Temperature for sampling (lower = more deterministic)
    temperature: float = 1.0


# =============================================================================
# MPPI Demo Generation Parameters (Newton VBD)
# =============================================================================

@dataclass
class MPPIConfig:
    """Pure MPPI for automatic demo trajectory generation on Newton VBD.

    Single-pass softmax weighted mean per planning step (no CEM iteration).
    Actions in [-1, 1] normalized space, scaled by env's POS/ROT_ACTION_SCALE.
    """

    # --- Sampling ---
    K: int = 256
    H: int = 32

    # --- MPPI core ---
    # Higher = more exploitative (concentrates weight on low-cost samples)
    temperature_lambda: float = 0.5  # tuned in M1 Step 2.5 (cost_range=2.99, eff_K~10-20)

    # --- Noise (in [-1, 1] normalized action space) ---
    noise_sigma: float = 0.2  # tentative, 0.2 * 0.015 = 3mm physical
    noise_correlation: float = 0.5  # tentative, temporal smoothing

    # --- Action space ---
    # M1: single-arm position-only (3D). M2: dual-arm position-only (6D). M3+: dual-arm full pose (12D).
    action_dim: int = 3
    # SSOT: newton_approach_cable_env.py:326-327
    pos_action_scale: float = 0.015  # [m/step]
    rot_action_scale: float = 0.05  # [rad/step] axis-angle (unused in M1)

    # --- Success ---
    # SSOT: dual_arm_msa_config.py:177
    success_threshold_m: float = 0.08
    # SSOT: task_config.py:154 T_ALIGN (M3 orientation threshold, 10°)
    success_threshold_rad: float = 0.1745

    # --- Newton physics ---
    # SSOT: newton_approach_cable_env.py:67-68
    newton_dt: float = 1.0 / 480.0
    sim_substeps: int = 4  # RL_SIM_SUBSTEPS (not init SIM_SUBSTEPS=10)
    world_count: int = 256  # = K (1 sample/world)

    # --- Warm-start (scripted IK pre-MPPI phase) ---
    # Distance [m] from cable endpoint at warm-start end. MPPI converges from here.
    # M2/M3 default 0.12m sized for 0.08m bimanual_reach threshold. Override per skill.
    warm_start_offset_m: float = 0.12

    # --- Device ---
    device: str = "cuda:0"

    # --- Output ---
    hdf5_dir: str = "data/mppi_demos"
    max_episodes: int = 50


# =============================================================================
# Phase-Specific Cost Weights
# =============================================================================

@dataclass
class PhaseCostConfig:
    """Cost function weights for each phase."""

    # Phase 3: Lift - maximize cable Z position
    phase3_lift: Dict[str, float] = field(default_factory=lambda: {
        "cable_z": -10.0,           # Negative because we want to maximize Z
        "cable_z_velocity": -2.0,   # Reward upward velocity
        "grasp_contact": 5.0,       # Penalty for losing contact
        "joint_smoothness": 0.1,    # Small penalty for jerky motions
        "action_magnitude": 0.01,   # Small penalty for large actions
    })

    # Phase 4: Hook Approach - minimize distance to hook
    phase4_hook_approach: Dict[str, float] = field(default_factory=lambda: {
        "hook_distance": 10.0,      # Minimize distance to hook
        "cable_height": -1.0,       # Maintain height
        "grasp_contact": 5.0,
        "joint_smoothness": 0.1,
    })

    # Phase 5: Hook Placement - position cable over hook
    phase5_hook_placement: Dict[str, float] = field(default_factory=lambda: {
        "hook_alignment": 10.0,     # Align cable with hook center
        "cable_height": 5.0,        # Target height above hook
        "grasp_contact": 5.0,
        "joint_smoothness": 0.1,
    })

    # Generic manipulation (default)
    generic: Dict[str, float] = field(default_factory=lambda: {
        "task_progress": -1.0,      # Minimize negative progress
        "joint_smoothness": 0.1,
        "action_magnitude": 0.01,
    })


# =============================================================================
# Task State Indices (from collect_demo_data.py)
# =============================================================================

class TaskStateIndices:
    """Indices for accessing task state components.

    Task state dimension: 44
    - Cable segments: 20 * 3 = 60 (but compressed to key positions)
    - Hook position: 3
    - Distances: variable
    """

    # Cable segment positions (3D each)
    # Assumes first 20*3=60 entries are cable segment XYZ
    # But based on demo data, task_state is 44D
    # Likely structure:
    #   - cable_center_segments: ~30D (10 key segments * 3)
    #   - hook_pos: 3D
    #   - ee_positions: 6D (left 3 + right 3)
    #   - distances: 5D

    # For Phase 3 Lift, we care about cable Z positions
    # Cable center is around index 10-12 (center segment)
    CABLE_CENTER_Z = 11  # Approximate - needs verification

    # Hook position
    HOOK_POS_START = 30
    HOOK_POS_END = 33

    # End-effector positions in task state
    LEFT_EE_START = 33
    LEFT_EE_END = 36
    RIGHT_EE_START = 36
    RIGHT_EE_END = 39

    # Distances
    DISTANCES_START = 39
    DISTANCES_END = 44


# =============================================================================
# Proprio State Indices
# =============================================================================

class ProprioIndices:
    """Indices for accessing proprioception components.

    Proprio dimension: 34
    - Left arm: 7 joint pos + 7 joint vel + 3 EE pos = 17
    - Right arm: 7 joint pos + 7 joint vel + 3 EE pos = 17
    """

    # Left arm
    LEFT_JOINT_POS = slice(0, 7)
    LEFT_JOINT_VEL = slice(7, 14)
    LEFT_EE_POS = slice(14, 17)

    # Right arm
    RIGHT_JOINT_POS = slice(17, 24)
    RIGHT_JOINT_VEL = slice(24, 31)
    RIGHT_EE_POS = slice(31, 34)

    # All joint positions
    ALL_JOINT_POS = [0, 1, 2, 3, 4, 5, 6, 17, 18, 19, 20, 21, 22, 23]


# =============================================================================
# Action Indices
# =============================================================================

class ActionIndices:
    """Indices for accessing action components.

    Action dimension: 18
    - Left arm: 7 joint + 2 gripper = 9
    - Right arm: 7 joint + 2 gripper = 9
    """

    # Left arm
    LEFT_JOINTS = slice(0, 7)
    LEFT_GRIPPER = slice(7, 9)

    # Right arm
    RIGHT_JOINTS = slice(9, 16)
    RIGHT_GRIPPER = slice(16, 18)

    # All joints (excluding grippers)
    ALL_JOINTS = list(range(7)) + list(range(9, 16))

    # All grippers
    ALL_GRIPPERS = [7, 8, 16, 17]


# =============================================================================
# Default Configuration
# =============================================================================

def get_default_mpc_config() -> MPCConfig:
    """Get default MPC configuration."""
    return MPCConfig()


def get_default_mppi_config() -> MPPIConfig:
    """Get default MPPI configuration for Newton VBD demo generation."""
    return MPPIConfig()


def get_phase_costs(phase: int) -> Dict[str, float]:
    """Get cost weights for a specific phase."""
    cost_config = PhaseCostConfig()

    phase_costs = {
        3: cost_config.phase3_lift,
        4: cost_config.phase4_hook_approach,
        5: cost_config.phase5_hook_placement,
    }

    return phase_costs.get(phase, cost_config.generic)
