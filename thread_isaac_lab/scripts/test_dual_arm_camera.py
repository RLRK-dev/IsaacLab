#!/usr/bin/env python3
"""
Test script for Dual Arm Camera Environment.

Spawns the dual arm scene with 3 cameras and saves sample images.

Usage:
    cd /home/rlrk/IsaacLab
    source env_isaaclab/bin/activate
    CUDA_VISIBLE_DEVICES=0 OMNI_KIT_ALLOW_ROOT=1 python \
        thread_isaac_lab/scripts/test_dual_arm_camera.py --headless

Output:
    /tmp/dual_arm_left.png
    /tmp/dual_arm_right.png
    /tmp/dual_arm_overhead.png
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Test dual arm camera environment")
parser.add_argument("--num_envs", type=int, default=4, help="Number of environments")
parser.add_argument("--save_dir", type=str, default="/tmp", help="Directory to save images")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os
import torch
import numpy as np
from PIL import Image

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.assets import RigidObjectCfg

from tasks.hook_hanging.dual_arm_camera_env_cfg import DualArmCameraSceneCfg
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def save_camera_image(image_data: torch.Tensor, path: str, name: str):
    """Save camera image to file."""
    # image_data shape: (num_envs, H, W, C) or (H, W, C)
    if image_data.dim() == 4:
        # Take first environment
        img = image_data[0].cpu().numpy()
    else:
        img = image_data.cpu().numpy()

    # Convert to uint8
    if img.max() <= 1.0:
        img = (img * 255).astype(np.uint8)
    else:
        img = img.astype(np.uint8)

    # Save
    filepath = os.path.join(path, name)
    Image.fromarray(img).save(filepath)
    print(f"  Saved: {filepath} ({img.shape})")


def main():
    print("\n" + "=" * 60)
    print("DUAL ARM CAMERA ENVIRONMENT TEST")
    print("=" * 60)

    device = torch.device("cuda:0")

    # Create scene configuration
    cfg = DualArmCameraSceneCfg()
    cfg.num_envs = args_cli.num_envs
    cfg.env_spacing = 3.0

    print(f"\n[Config]")
    print(f"  Num environments: {cfg.num_envs}")
    print(f"  Save directory: {args_cli.save_dir}")

    # Setup simulation
    sim_cfg = sim_utils.SimulationCfg(
        device=str(device),
        dt=PHYSICS_DT,
        render_interval=1,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(eye=(2.0, 2.0, 2.0), target=(0.5, 0.0, 0.5))

    # Create scene
    print("\n[Status] Creating scene with cameras...")
    scene = InteractiveScene(cfg)

    print("[Status] Starting simulation...")
    sim.reset()

    # Run a few steps to let physics settle and cameras render
    print("[Status] Running simulation steps...")
    for i in range(120):
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())
        if (i + 1) % 30 == 0:
            print(f"  Step {i + 1}/120")

    # Get robot and object positions
    print("\n[Positions after simulation]")
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    hook = scene["hook"]
    cable = scene["cable"]

    left_ee_pos = robot_left.data.body_pos_w[:, 8, :]
    right_ee_pos = robot_right.data.body_pos_w[:, 8, :]
    hook_pos = hook.data.root_pos_w
    cable_pos = cable.data.root_pos_w

    print(f"  Left EE:  ({left_ee_pos[0,0]:.3f}, {left_ee_pos[0,1]:.3f}, {left_ee_pos[0,2]:.3f})")
    print(f"  Right EE: ({right_ee_pos[0,0]:.3f}, {right_ee_pos[0,1]:.3f}, {right_ee_pos[0,2]:.3f})")
    print(f"  Cable:    ({cable_pos[0,0]:.3f}, {cable_pos[0,1]:.3f}, {cable_pos[0,2]:.3f})")
    print(f"  Hook:     ({hook_pos[0,0]:.3f}, {hook_pos[0,1]:.3f}, {hook_pos[0,2]:.3f})")

    # Get camera images
    print("\n[Camera Images]")

    # Left wrist camera
    left_cam = scene["left_wrist_camera"]
    left_rgb = left_cam.data.output["rgb"]
    print(f"  Left wrist camera data shape: {left_rgb.shape}")
    save_camera_image(left_rgb, args_cli.save_dir, "dual_arm_left.png")

    # Right wrist camera
    right_cam = scene["right_wrist_camera"]
    right_rgb = right_cam.data.output["rgb"]
    print(f"  Right wrist camera data shape: {right_rgb.shape}")
    save_camera_image(right_rgb, args_cli.save_dir, "dual_arm_right.png")

    # Overhead camera
    overhead_cam = scene["overhead_camera"]
    overhead_rgb = overhead_cam.data.output["rgb"]
    print(f"  Overhead camera data shape: {overhead_rgb.shape}")
    save_camera_image(overhead_rgb, args_cli.save_dir, "dual_arm_overhead.png")

    # Print distances (take first environment for display)
    print("\n[Distances]")
    left_to_cable = torch.norm(left_ee_pos[0] - cable_pos[0], dim=-1).item()
    right_to_cable = torch.norm(right_ee_pos[0] - cable_pos[0], dim=-1).item()
    cable_to_hook = torch.norm(cable_pos[0] - hook_pos[0], dim=-1).item()
    ee_separation = torch.norm(left_ee_pos[0] - right_ee_pos[0], dim=-1).item()

    print(f"  Left EE to Cable:  {left_to_cable:.3f} m")
    print(f"  Right EE to Cable: {right_to_cable:.3f} m")
    print(f"  Cable to Hook:     {cable_to_hook:.3f} m")
    print(f"  EE Separation:     {ee_separation:.3f} m")

    # Camera info
    print("\n[Camera Info]")
    print(f"  Left wrist:  {left_cam.cfg.width}x{left_cam.cfg.height}")
    print(f"  Right wrist: {right_cam.cfg.width}x{right_cam.cfg.height}")
    print(f"  Overhead:    {overhead_cam.cfg.width}x{overhead_cam.cfg.height}")

    # Memory usage
    print("\n[GPU Memory]")
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        print(f"  Allocated: {allocated:.2f} GB")
        print(f"  Reserved:  {reserved:.2f} GB")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"\nImages saved to:")
    print(f"  {args_cli.save_dir}/dual_arm_left.png")
    print(f"  {args_cli.save_dir}/dual_arm_right.png")
    print(f"  {args_cli.save_dir}/dual_arm_overhead.png")


if __name__ == "__main__":
    main()
    simulation_app.close()
