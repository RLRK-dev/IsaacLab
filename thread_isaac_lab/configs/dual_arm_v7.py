#!/usr/bin/env python3
"""
THREAD Dual Arm v7 Configuration
=================================

Changes from v6:
1. ARM_X_POS: 0.35 → 0.42 (even closer to cable at 0.5)
2. approach_reward std: 1.0 → 0.3 (steeper gradient near cable)
3. close_reward weight: 0.15 → 0.30 (stronger incentive for close proximity)

Expected improvements:
- EE-Cable distance: 0.26m (v6) → <0.1m (v7)
- close_bonus should now fire (EE < 0.1m)
- grasp_ready_bonus may fire (EE < 0.05m)

Usage:
    Apply these changes to dual_arm_cfg.py and train_dual_arm.py before running v7.
"""

# =============================================================================
# v7 Robot Position Configuration
# =============================================================================

# Robot base positions - v7: Much closer to cable
ARM_Y_OFFSET_V7 = 0.18  # Reduced from 0.20 (v6) for tighter arm separation
ARM_X_POS_V7 = 0.42     # Increased from 0.35 (v6), closer to cable at 0.5

# Cable position (unchanged)
CABLE_X = 0.5
CABLE_Y = 0.0

# Initial distance from EE to cable (approximate)
# With v7 positions, initial EE-Cable distance should be ~0.15m vs ~0.26m in v6

# =============================================================================
# v7 Reward Configuration
# =============================================================================

REWARD_CONFIG_V7 = {
    # Approach reward - v7: steeper gradient for close distances
    "approach": {
        "std": 0.3,       # v6: 1.0 → v7: 0.3 (3x steeper)
        "weight": 0.80,   # Same as v6
    },

    # Close bonus - v7: stronger incentive
    "close_bonus": {
        "threshold": 0.1,  # Fire when EE < 0.1m
        "value": 3.0,      # v6: 2.0 → v7: 3.0 (+50%)
        "weight": 0.30,    # v6: 0.15 → v7: 0.30 (2x)
    },

    # Grasp ready bonus
    "grasp_ready_bonus": {
        "threshold": 0.05,  # Fire when EE < 0.05m
        "value": 7.0,       # v6: 5.0 → v7: 7.0 (+40%)
        "weight": 0.20,     # v6: 0.10 → v7: 0.20 (2x)
    },

    # Gripper reward (unchanged from v6)
    "gripper": {
        "threshold": 0.08,  # Close gripper when EE < 0.08m
        "weight": 0.10,
    },

    # Task reward (hook proximity, unchanged)
    "task": {
        "std": 2.0,
        "weight": 0.05,
    },

    # Arm coordination (unchanged)
    "arm_coordination": {
        "target_separation": 0.1,  # Target separation when grasping
        "std": 1.0,
        "weight": 0.10,
    },

    # Action penalty (unchanged)
    "action_penalty": {
        "weight": 0.01,
    },
}

# =============================================================================
# v7 Joint Configuration (more extended pose)
# =============================================================================

LEFT_ARM_JOINTS_V7 = {
    "panda_joint1": 0.15,  # Slightly less rotation (v6: 0.2)
    "panda_joint2": 0.1,   # Slightly up (v6: 0.0)
    "panda_joint3": 0.0,
    "panda_joint4": -1.3,  # Less bent elbow (v6: -1.5)
    "panda_joint5": 0.0,
    "panda_joint6": 1.4,   # Adjusted wrist (v6: 1.5)
    "panda_joint7": 0.785,
    "panda_finger_joint1": 0.04,
    "panda_finger_joint2": 0.04,
}

RIGHT_ARM_JOINTS_V7 = {
    "panda_joint1": -0.15,  # Mirror of left
    "panda_joint2": 0.1,
    "panda_joint3": 0.0,
    "panda_joint4": -1.3,
    "panda_joint5": 0.0,
    "panda_joint6": 1.4,
    "panda_joint7": 0.785,
    "panda_finger_joint1": 0.04,
    "panda_finger_joint2": 0.04,
}

# =============================================================================
# v7 Training Configuration
# =============================================================================

TRAINING_CONFIG_V7 = {
    "num_envs": 512,
    "max_iterations": 5000,
    "experiment_name": "thread_dual_arm_v7",
    "seed": 42,

    # PPO parameters (same as v6)
    "learning_rate": 1e-3,
    "discount_factor": 0.99,
    "entropy_coeff": 0.01,
    "clip_ratio": 0.2,
}

# =============================================================================
# Summary
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("THREAD Dual Arm v7 Configuration")
    print("=" * 70)

    print("\n[Robot Positions]")
    print(f"  ARM_X_POS: 0.35 (v6) → {ARM_X_POS_V7} (v7)")
    print(f"  ARM_Y_OFFSET: 0.20 (v6) → {ARM_Y_OFFSET_V7} (v7)")
    print(f"  Expected initial EE-Cable distance: ~0.15m (vs ~0.26m in v6)")

    print("\n[Reward Changes]")
    print(f"  approach_reward std: 1.0 (v6) → {REWARD_CONFIG_V7['approach']['std']} (v7)")
    print(f"  close_bonus weight: 0.15 (v6) → {REWARD_CONFIG_V7['close_bonus']['weight']} (v7)")
    print(f"  grasp_ready_bonus weight: 0.10 (v6) → {REWARD_CONFIG_V7['grasp_ready_bonus']['weight']} (v7)")

    print("\n[Expected Improvements]")
    print("  - EE-Cable distance: 0.26m → <0.1m")
    print("  - close_bonus activation: No → Yes")
    print("  - grasp_ready_bonus activation: No → Possibly")

    print("\n" + "=" * 70)
