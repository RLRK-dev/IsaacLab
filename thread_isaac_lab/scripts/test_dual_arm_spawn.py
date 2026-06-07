#!/usr/bin/env python3
# Copyright (c) 2024-2025, THREAD Project
# SPDX-License-Identifier: BSD-3-Clause
"""Test script for Dual Arm Scene Spawning.

This script tests that the dual arm scene spawns correctly:
- 2x Franka Panda robots (left and right)
- Cable
- Hook
- Table

Usage:
    cd /home/rlrk/IsaacLab
    source env_isaaclab/bin/activate
    CUDA_VISIBLE_DEVICES=0 python thread_isaac_lab/scripts/test_dual_arm_spawn.py --num_envs 4 --headless
"""

import argparse
import sys
import os

# Add thread_isaac_lab to path
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test dual arm scene spawning.")
parser.add_argument("--num_envs", type=int, default=4, help="Number of environments")
parser.add_argument("--steps", type=int, default=100, help="Number of simulation steps")

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Use GPU 0 (A4000) by default if not specified
if args_cli.device is None:
    args_cli.device = "cuda:0"

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Import after AppLauncher
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.scene import InteractiveScene

# Import dual arm configuration
from envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def main():
    """Main function to test dual arm spawning."""
    print("\n" + "=" * 70)
    print("DUAL ARM SCENE SPAWN TEST")
    print("=" * 70)

    # Get device
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"\n[Device] {device}")

    # Create scene configuration
    cfg = DualArmSceneCfg()
    cfg.num_envs = args_cli.num_envs
    cfg.env_spacing = 3.0

    # Remove cameras from config for this test (memory saving)
    # We'll test without cameras on A4000
    delattr(cfg, 'overhead_camera')
    delattr(cfg, 'left_wrist_camera')
    delattr(cfg, 'right_wrist_camera')

    print(f"\n[Scene Configuration]")
    print(f"  Num environments: {cfg.num_envs}")
    print(f"  Env spacing: {cfg.env_spacing}m")

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(
        device=device,
        dt=PHYSICS_DT,
        render_interval=1,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(3.0, 3.0, 2.5), target=(0.0, 0.0, 0.5))

    # Create scene
    print("\n[Status] Creating scene...")
    scene = InteractiveScene(cfg)

    print("\n[Status] Starting simulation...")
    sim.reset()

    # Get assets from scene
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    table = scene["table"]
    hook = scene["hook"]
    cable = scene["cable"]

    print("\n[Assets Created]")
    print(f"  robot_left: {type(robot_left).__name__}")
    print(f"  robot_right: {type(robot_right).__name__}")
    print(f"  table: {type(table).__name__}")
    print(f"  hook: {type(hook).__name__}")
    print(f"  cable: {type(cable).__name__}")

    # Print initial positions
    print("\n[Initial Asset Positions (Env 0)]")

    # Robot positions
    if hasattr(robot_left, 'data') and hasattr(robot_left.data, 'root_pos_w'):
        left_pos = robot_left.data.root_pos_w[0].cpu().numpy()
        print(f"  Robot Left:  ({left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f})")

    if hasattr(robot_right, 'data') and hasattr(robot_right.data, 'root_pos_w'):
        right_pos = robot_right.data.root_pos_w[0].cpu().numpy()
        print(f"  Robot Right: ({right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f})")

    # Table position
    if hasattr(table, 'data') and hasattr(table.data, 'root_pos_w'):
        table_pos = table.data.root_pos_w[0].cpu().numpy()
        print(f"  Table:       ({table_pos[0]:.3f}, {table_pos[1]:.3f}, {table_pos[2]:.3f})")

    # Hook position
    if hasattr(hook, 'data') and hasattr(hook.data, 'root_pos_w'):
        hook_pos = hook.data.root_pos_w[0].cpu().numpy()
        print(f"  Hook:        ({hook_pos[0]:.3f}, {hook_pos[1]:.3f}, {hook_pos[2]:.3f})")

    # Cable position
    if hasattr(cable, 'data') and hasattr(cable.data, 'root_pos_w'):
        cable_pos = cable.data.root_pos_w[0].cpu().numpy()
        print(f"  Cable:       ({cable_pos[0]:.3f}, {cable_pos[1]:.3f}, {cable_pos[2]:.3f})")

    # Print robot joint info
    print("\n[Robot Joint Info]")
    if hasattr(robot_left, 'data') and hasattr(robot_left.data, 'joint_pos'):
        num_joints = robot_left.data.joint_pos.shape[1]
        print(f"  Left arm joints: {num_joints}")
        joint_pos = robot_left.data.joint_pos[0].cpu().numpy()
        print(f"  Left arm joint positions (first 7): {joint_pos[:7]}")

    if hasattr(robot_right, 'data') and hasattr(robot_right.data, 'joint_pos'):
        joint_pos = robot_right.data.joint_pos[0].cpu().numpy()
        print(f"  Right arm joint positions (first 7): {joint_pos[:7]}")

    # Run simulation steps
    print(f"\n[Status] Running {args_cli.steps} simulation steps...")
    for step in range(args_cli.steps):
        # Write zero effort to joints (let them settle)
        if hasattr(robot_left, 'set_joint_effort_target'):
            robot_left.set_joint_effort_target(torch.zeros(args_cli.num_envs, 9, device=device))
        if hasattr(robot_right, 'set_joint_effort_target'):
            robot_right.set_joint_effort_target(torch.zeros(args_cli.num_envs, 9, device=device))

        # Step simulation
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        if step % 50 == 0:
            print(f"  Step {step}/{args_cli.steps}")

    # Print final positions
    print("\n[Final Asset Positions (Env 0)]")

    if hasattr(robot_left, 'data') and hasattr(robot_left.data, 'root_pos_w'):
        left_pos = robot_left.data.root_pos_w[0].cpu().numpy()
        print(f"  Robot Left:  ({left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f})")

    if hasattr(robot_right, 'data') and hasattr(robot_right.data, 'root_pos_w'):
        right_pos = robot_right.data.root_pos_w[0].cpu().numpy()
        print(f"  Robot Right: ({right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f})")

    if hasattr(hook, 'data') and hasattr(hook.data, 'root_pos_w'):
        hook_pos = hook.data.root_pos_w[0].cpu().numpy()
        print(f"  Hook:        ({hook_pos[0]:.3f}, {hook_pos[1]:.3f}, {hook_pos[2]:.3f})")

    if hasattr(cable, 'data') and hasattr(cable.data, 'root_pos_w'):
        cable_pos = cable.data.root_pos_w[0].cpu().numpy()
        print(f"  Cable:       ({cable_pos[0]:.3f}, {cable_pos[1]:.3f}, {cable_pos[2]:.3f})")

    # Memory usage
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"\n[GPU Memory]")
        print(f"  Allocated: {allocated:.2f} GB")
        print(f"  Reserved: {reserved:.2f} GB")

    print("\n" + "=" * 70)
    print("DUAL ARM SPAWN TEST COMPLETED!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
    simulation_app.close()
