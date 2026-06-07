#!/usr/bin/env python3
"""
Isaac Sim FK Verification Script

Verify all Phase joint angles by applying them to the robot in Isaac Sim
and checking if the EE position matches the expected waypoint.

Uses existing dual_arm_cfg.py configuration for proper robot setup.

T1タスク: 2026-01-02
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
sys.path.insert(0, "/home/rlrk/IsaacLab")

import argparse
import numpy as np

# Isaac Sim app launch
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="FK Verification for all phases")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Isaac Lab imports
import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.assets import ArticulationCfg, Articulation
from isaaclab.utils import configclass

# Import project configurations
from thread_isaac_lab.envs.dual_arm_cfg import LeftFrankaCfg, RightFrankaCfg

# Project imports
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    # Phase 1
    WAYPOINT_PHASE1_LEFT,
    WAYPOINT_PHASE1_RIGHT,
    LEFT_ARM_INIT_JOINTS,
    RIGHT_ARM_INIT_JOINTS,
    # Phase 2
    WAYPOINT_PHASE2_LEFT,
    WAYPOINT_PHASE2_RIGHT,
    PHASE2_LEFT_JOINTS,
    PHASE2_RIGHT_JOINTS,
    # Phase 3
    WAYPOINT_PHASE3_LEFT,
    WAYPOINT_PHASE3_RIGHT,
    PHASE3_LEFT_JOINTS,
    PHASE3_RIGHT_JOINTS,
    # Phase 4
    WAYPOINT_PHASE4_LEFT,
    WAYPOINT_PHASE4_RIGHT,
    PHASE4_LEFT_JOINTS,
    PHASE4_RIGHT_JOINTS,
    # Phase 4.5
    WAYPOINT_PHASE45_LEFT,
    WAYPOINT_PHASE45_RIGHT,
    PHASE45_LEFT_JOINTS,
    PHASE45_RIGHT_JOINTS,
    # Phase 5
    WAYPOINT_PHASE5_LEFT,
    WAYPOINT_PHASE5_RIGHT,
    PHASE5_LEFT_JOINTS,
    PHASE5_RIGHT_JOINTS,
    # Gripper
    GRIPPER_OPEN,
)

# Z offset compensation for Isaac Sim (EE frame offset)
Z_OFFSET = 0.1034


@configclass
class FKVerifySceneCfg(InteractiveSceneCfg):
    """Scene configuration for FK verification using project's robot configs."""

    # Left robot - use project configuration
    robot_left: ArticulationCfg = LeftFrankaCfg()

    # Right robot - use project configuration
    robot_right: ArticulationCfg = RightFrankaCfg()


def get_ee_position(robot: Articulation, body_name: str = "panda_hand") -> np.ndarray:
    """Get end-effector position from robot."""
    body_ids = robot.find_bodies(body_name)[0]
    body_state = robot.data.body_state_w[:, body_ids, :3]  # [env, body, xyz]
    return body_state[0, 0].cpu().numpy()  # First env, first body


def verify_phase(phase_name: str, robot_left: Articulation, robot_right: Articulation,
                 left_joints: list, right_joints: list,
                 left_waypoint: tuple, right_waypoint: tuple,
                 sim) -> dict:
    """Verify a single phase."""
    print(f"\n{'=' * 60}")
    print(f"{phase_name}")
    print(f"{'=' * 60}")

    # Expected EE positions (with Z offset for Isaac Sim)
    expected_left = np.array([left_waypoint[0], left_waypoint[1], left_waypoint[2] + Z_OFFSET])
    expected_right = np.array([right_waypoint[0], right_waypoint[1], right_waypoint[2] + Z_OFFSET])

    print(f"Expected Left EE:  ({expected_left[0]:.3f}, {expected_left[1]:.3f}, {expected_left[2]:.3f})")
    print(f"Expected Right EE: ({expected_right[0]:.3f}, {expected_right[1]:.3f}, {expected_right[2]:.3f})")

    # Prepare joint positions (7 arm joints + 2 gripper joints)
    left_joint_pos = torch.tensor([left_joints + [GRIPPER_OPEN, GRIPPER_OPEN]], dtype=torch.float32, device="cuda")
    right_joint_pos = torch.tensor([right_joints + [GRIPPER_OPEN, GRIPPER_OPEN]], dtype=torch.float32, device="cuda")

    # Apply joint positions using teleportation
    robot_left.write_joint_state_to_sim(left_joint_pos, torch.zeros_like(left_joint_pos))
    robot_right.write_joint_state_to_sim(right_joint_pos, torch.zeros_like(right_joint_pos))

    # Step simulation to let physics settle
    for _ in range(50):
        sim.step()

    # Update robot state
    robot_left.update(sim.get_physics_dt())
    robot_right.update(sim.get_physics_dt())

    # Get actual EE positions
    actual_left = get_ee_position(robot_left)
    actual_right = get_ee_position(robot_right)

    print(f"Actual Left EE:    ({actual_left[0]:.3f}, {actual_left[1]:.3f}, {actual_left[2]:.3f})")
    print(f"Actual Right EE:   ({actual_right[0]:.3f}, {actual_right[1]:.3f}, {actual_right[2]:.3f})")

    # Calculate errors
    error_left = np.linalg.norm(actual_left - expected_left)
    error_right = np.linalg.norm(actual_right - expected_right)

    print(f"\nError: Left = {error_left * 100:.2f} cm, Right = {error_right * 100:.2f} cm")

    status = "OK" if error_left < 0.02 and error_right < 0.02 else "FAILED"
    print(f"Status: {status}")

    return {
        "phase": phase_name,
        "expected_left": expected_left,
        "expected_right": expected_right,
        "actual_left": actual_left,
        "actual_right": actual_right,
        "error_left_cm": error_left * 100,
        "error_right_cm": error_right * 100,
        "status": status,
    }


def main():
    """Main function for FK verification."""
    print("=" * 70)
    print("Isaac Sim FK Verification - All Phases")
    print("=" * 70)
    print(f"\nZ offset compensation: {Z_OFFSET:.4f} m")
    print(f"ROBOT_LEFT_BASE:  {ROBOT_LEFT_BASE}")
    print(f"ROBOT_RIGHT_BASE: {ROBOT_RIGHT_BASE}")

    # Create simulation context
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, render_interval=1)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([2.0, 2.0, 2.0], [0.3, 0.0, 0.8])

    # Create scene with robots
    scene_cfg = FKVerifySceneCfg(num_envs=1, env_spacing=2.0)

    # Override prim_path to remove {ENV_REGEX_NS}
    scene_cfg.robot_left.prim_path = "/World/envs/env_0/Robot_Left"
    scene_cfg.robot_right.prim_path = "/World/envs/env_0/Robot_Right"

    scene = InteractiveScene(scene_cfg)

    # Play simulation
    sim.reset()
    scene.reset()

    # Define phases to verify
    phases = [
        ("Phase 1", LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS,
         WAYPOINT_PHASE1_LEFT, WAYPOINT_PHASE1_RIGHT),
        ("Phase 2", PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
         WAYPOINT_PHASE2_LEFT, WAYPOINT_PHASE2_RIGHT),
        ("Phase 3", PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
         WAYPOINT_PHASE3_LEFT, WAYPOINT_PHASE3_RIGHT),
        ("Phase 4", PHASE4_LEFT_JOINTS, PHASE4_RIGHT_JOINTS,
         WAYPOINT_PHASE4_LEFT, WAYPOINT_PHASE4_RIGHT),
        ("Phase 4.5", PHASE45_LEFT_JOINTS, PHASE45_RIGHT_JOINTS,
         WAYPOINT_PHASE45_LEFT, WAYPOINT_PHASE45_RIGHT),
        ("Phase 5", PHASE5_LEFT_JOINTS, PHASE5_RIGHT_JOINTS,
         WAYPOINT_PHASE5_LEFT, WAYPOINT_PHASE5_RIGHT),
    ]

    results = []

    for phase_name, left_joints, right_joints, left_wp, right_wp in phases:
        result = verify_phase(
            phase_name,
            scene["robot_left"],
            scene["robot_right"],
            list(left_joints),
            list(right_joints),
            left_wp,
            right_wp,
            sim
        )
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_ok = True
    print(f"\n{'Phase':<12} {'Left Error':>12} {'Right Error':>12} {'Status':>10}")
    print("-" * 50)

    for r in results:
        status_icon = "OK" if r["status"] == "OK" else "NG"
        print(f"{r['phase']:<12} {r['error_left_cm']:>10.2f} cm {r['error_right_cm']:>10.2f} cm {status_icon:>10}")
        if r["status"] != "OK":
            all_ok = False

    print("-" * 50)
    if all_ok:
        print("\n[SUCCESS] All phases verified - EE errors < 2cm")
    else:
        print("\n[FAILED] Some phases have EE errors >= 2cm")

    # Cleanup
    simulation_app.close()

    return all_ok, results


if __name__ == "__main__":
    success, results = main()
    sys.exit(0 if success else 1)
