#!/usr/bin/env python3
"""
Check Workspace Heights
=======================

Checks table, cable, and gripper heights to diagnose reachability issues.

Usage:
    CUDA_VISIBLE_DEVICES=1 python thread_isaac_lab/scripts/check_workspace_heights.py --headless
"""

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Check Workspace Heights")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.scene import InteractiveScene

# Import scene config
from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT, ARM_Z_POS
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def main():
    print("\n" + "=" * 70)
    print("WORKSPACE HEIGHT DIAGNOSTIC")
    print("=" * 70)

    # Print configured values
    print("\n[Configuration Values]")
    print(f"  TABLE_HEIGHT = {TABLE_HEIGHT:.3f} m")
    print(f"  ARM_Z_POS (robot base) = {ARM_Z_POS:.3f} m")
    print(f"  Table top surface = TABLE_HEIGHT - 0.01 = {TABLE_HEIGHT - 0.01:.3f} m")

    # Get cable initial position from config
    cfg = DualArmSceneCfg()
    cable_init_z = cfg.cable.init_state.pos[2]
    print(f"  Cable initial Z = {cable_init_z:.3f} m")
    print(f"  Cable initial pos = {cfg.cable.init_state.pos}")

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(1.5, 0.8, 1.2), target=(0.3, 0.0, 0.8))

    # Create scene with 1 env
    cfg.num_envs = 1
    scene = InteractiveScene(cfg)
    sim.reset()

    # Let simulation settle
    print("\n[Settling simulation for 300 steps...]")
    for _ in range(300):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get actual positions
    print("\n[Actual Positions After Settling]")

    # Cable positions
    cable: Articulation = scene["cable"]
    cable_body_pos = cable.data.body_pos_w[0]  # [num_bodies, 3]
    cable_z_values = cable_body_pos[:, 2].cpu().numpy()
    print(f"\n  Cable segment positions (Z):")
    for i, z in enumerate(cable_z_values):
        print(f"    seg_{i}: z = {z:.4f} m")
    print(f"  Cable Z range: {cable_z_values.min():.4f} - {cable_z_values.max():.4f} m")
    print(f"  Cable mean Z: {cable_z_values.mean():.4f} m")

    # Cable XY positions
    cable_xy_pos = cable_body_pos[:, :2].cpu().numpy()
    print(f"\n  Cable XY positions:")
    for i in range(len(cable_xy_pos)):
        print(f"    seg_{i}: ({cable_xy_pos[i, 0]:.4f}, {cable_xy_pos[i, 1]:.4f})")

    # Robot positions
    robot_left: Articulation = scene["robot_left"]
    robot_right: Articulation = scene["robot_right"]

    # Get EE positions (panda_hand frame)
    # Body indices: 0=panda_link0, ... 7=panda_link7, 8=panda_hand, 9=panda_leftfinger, 10=panda_rightfinger
    left_body_names = robot_left.data.body_names
    right_body_names = robot_right.data.body_names
    print(f"\n  Robot body names: {left_body_names}")

    # Find hand index
    hand_idx = None
    for i, name in enumerate(left_body_names):
        if "panda_hand" in name:
            hand_idx = i
            break

    if hand_idx is not None:
        left_ee_pos = robot_left.data.body_pos_w[0, hand_idx].cpu().numpy()
        right_ee_pos = robot_right.data.body_pos_w[0, hand_idx].cpu().numpy()
        print(f"\n  Left EE (panda_hand) position: ({left_ee_pos[0]:.4f}, {left_ee_pos[1]:.4f}, {left_ee_pos[2]:.4f})")
        print(f"  Right EE (panda_hand) position: ({right_ee_pos[0]:.4f}, {right_ee_pos[1]:.4f}, {right_ee_pos[2]:.4f})")

    # Get finger positions
    leftfinger_idx = None
    for i, name in enumerate(left_body_names):
        if "panda_leftfinger" in name:
            leftfinger_idx = i
            break

    if leftfinger_idx is not None:
        left_finger_pos = robot_left.data.body_pos_w[0, leftfinger_idx].cpu().numpy()
        right_finger_pos = robot_right.data.body_pos_w[0, leftfinger_idx].cpu().numpy()
        print(f"\n  Left Gripper (leftfinger) position: ({left_finger_pos[0]:.4f}, {left_finger_pos[1]:.4f}, {left_finger_pos[2]:.4f})")
        print(f"  Right Gripper (leftfinger) position: ({right_finger_pos[0]:.4f}, {right_finger_pos[1]:.4f}, {right_finger_pos[2]:.4f})")

    # Calculate distances
    print("\n[Distance Analysis]")

    # Distance from gripper to cable (closest segment)
    left_finger_tensor = torch.tensor(left_finger_pos, device="cuda:0")
    right_finger_tensor = torch.tensor(right_finger_pos, device="cuda:0")

    left_to_cable = torch.norm(cable_body_pos - left_finger_tensor, dim=1).cpu().numpy()
    right_to_cable = torch.norm(cable_body_pos - right_finger_tensor, dim=1).cpu().numpy()

    print(f"  Left gripper to cable segments:")
    for i, d in enumerate(left_to_cable):
        print(f"    seg_{i}: {d:.4f} m")
    print(f"  Closest: seg_{left_to_cable.argmin()} at {left_to_cable.min():.4f} m")

    print(f"\n  Right gripper to cable segments:")
    for i, d in enumerate(right_to_cable):
        print(f"    seg_{i}: {d:.4f} m")
    print(f"  Closest: seg_{right_to_cable.argmin()} at {right_to_cable.min():.4f} m")

    # Height difference
    print(f"\n[Height Differences]")
    if hand_idx is not None:
        left_ee_z = left_ee_pos[2]
        right_ee_z = right_ee_pos[2]
        cable_mean_z = cable_z_values.mean()

        print(f"  Left EE Z - Cable mean Z = {left_ee_z - cable_mean_z:.4f} m")
        print(f"  Right EE Z - Cable mean Z = {right_ee_z - cable_mean_z:.4f} m")
        print(f"  Table surface Z = {TABLE_HEIGHT - 0.01:.4f} m")
        print(f"  Left EE Z - Table Z = {left_ee_z - (TABLE_HEIGHT - 0.01):.4f} m")

    # Franka Panda workspace info
    print("\n[Franka Panda Workspace Reference]")
    print("  Max reach radius: ~0.855 m from base")
    print("  Typical Z range from base: -0.3 to +0.5 m")
    print(f"  With base at Z={ARM_Z_POS}:")
    print(f"    Estimated reachable Z: {ARM_Z_POS - 0.3:.2f} to {ARM_Z_POS + 0.5:.2f} m")
    print(f"    ({ARM_Z_POS - 0.3:.2f}m to {ARM_Z_POS + 0.5:.2f}m)")

    # Issue diagnosis
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)

    if hand_idx is not None and leftfinger_idx is not None:
        left_finger_z = left_finger_pos[2]
        cable_z = cable_z_values.mean()

        if left_finger_z > cable_z + 0.1:
            print(f"  [ISSUE] Gripper is {left_finger_z - cable_z:.3f}m ABOVE cable")
            print(f"          Gripper Z: {left_finger_z:.3f}m, Cable Z: {cable_z:.3f}m")
            print(f"  [SUGGESTION] Lower robot base or raise cable spawn height")
        elif left_finger_z < cable_z - 0.1:
            print(f"  [ISSUE] Gripper is {cable_z - left_finger_z:.3f}m BELOW cable")
            print(f"  [SUGGESTION] Raise robot base or lower cable spawn height")
        else:
            print(f"  [OK] Gripper and cable are at similar heights")
            print(f"       Gripper Z: {left_finger_z:.3f}m, Cable Z: {cable_z:.3f}m")

        # Check XY distance
        left_xy = np.array([left_finger_pos[0], left_finger_pos[1]])
        cable_xy_mean = cable_xy_pos.mean(axis=0)
        xy_dist = np.linalg.norm(left_xy - cable_xy_mean)

        print(f"\n  XY distance from left gripper to cable center: {xy_dist:.3f}m")
        if xy_dist > 0.3:
            print(f"  [WARN] XY distance may be too large for initial reach")

    print("=" * 70)

    simulation_app.close()


if __name__ == "__main__":
    main()
