#!/usr/bin/env python3
"""Automatically capture goal images by setting robot joint positions."""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--save_dir", type=str, default="/home/rlrk/ClaudeCode")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
import torchvision.transforms as T
from pathlib import Path
from PIL import Image

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from envs.dual_arm_cfg import DualArmSceneCfg


def save_images(scene, skill_name: str, save_dir: str):
    """Save camera images."""
    cameras = ['front_left', 'front_right', 'back']
    save_path = Path(save_dir) / skill_name
    save_path.mkdir(parents=True, exist_ok=True)

    for cam_name in cameras:
        cam_key = f"{cam_name}_camera"
        try:
            camera = scene[cam_key]
            camera.update(dt=0.0)

            # Get RGB image
            img_data = camera.data.output["rgb"][0]  # (H, W, 4) RGBA
            img = img_data[:, :, :3].cpu()  # RGB only

            # Convert to (C, H, W)
            img = img.permute(2, 0, 1).float() / 255.0

            torch.save(img, save_path / f"{cam_name}.pt")

            try:
                pil_img = T.ToPILImage()(img)
                pil_img.save(save_path / f"{cam_name}.png")
                print(f"    Saved: {cam_name}.png")
            except Exception as e:
                print(f"    PNG save error: {e}")
        except KeyError:
            print(f"    Camera {cam_key} not found in scene")


def main():
    print("\n" + "=" * 60)
    print("Auto Goal Image Capture")
    print("=" * 60)

    save_dir = args_cli.save_dir

    # Initialize simulation FIRST
    sim_cfg = sim_utils.SimulationCfg(dt=0.01)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([2.5, 2.5, 2.5], [0.0, 0.0, 0.0])

    # Create scene AFTER simulation context
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)
    
    # Play simulation
    sim.reset()
    scene.reset()
    
    print(f"Save directory: {save_dir}")

    # Get robots (left and right)
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    num_joints_left = robot_left.num_joints
    num_joints_right = robot_right.num_joints
    print(f"Robot joints: left={num_joints_left}, right={num_joints_right}")
    
    # Define goal joint configurations
    # Franka Panda has 7 arm joints + 2 gripper joints per arm
    # Joint order may vary - adjust based on your URDF
    
    # Home position
    home = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]  # 7 DOF arm
    
    goals = {
        "bimanual_reach": {
            "left": [0.4, -0.5, 0.0, -1.8, 0.0, 1.3, 0.785],
            "right": [-0.4, -0.5, 0.0, -1.8, 0.0, 1.3, -0.785],
            "left_grip": 0.04, "right_grip": 0.04,  # Open
        },
        "bimanual_grasp": {
            "left": [0.4, -0.5, 0.0, -1.8, 0.0, 1.3, 0.785],
            "right": [-0.4, -0.5, 0.0, -1.8, 0.0, 1.3, -0.785],
            "left_grip": 0.0, "right_grip": 0.0,  # Closed
        },
        "bimanual_lift": {
            "left": [0.4, -0.8, 0.0, -1.5, 0.0, 1.0, 0.785],
            "right": [-0.4, -0.8, 0.0, -1.5, 0.0, 1.0, -0.785],
            "left_grip": 0.0, "right_grip": 0.0,
        },
        "bimanual_transport": {
            "left": [0.6, -0.7, 0.0, -1.6, 0.0, 1.1, 0.785],
            "right": [-0.6, -0.7, 0.0, -1.6, 0.0, 1.1, -0.785],
            "left_grip": 0.0, "right_grip": 0.0,
        },
        "bimanual_hang": {
            "left": [0.6, -0.6, 0.0, -1.7, 0.0, 1.2, 0.785],
            "right": [-0.6, -0.6, 0.0, -1.7, 0.0, 1.2, -0.785],
            "left_grip": 0.0, "right_grip": 0.0,
        },
        "bimanual_release": {
            "left": [0.6, -0.6, 0.0, -1.7, 0.0, 1.2, 0.785],
            "right": [-0.6, -0.6, 0.0, -1.7, 0.0, 1.2, -0.785],
            "left_grip": 0.04, "right_grip": 0.04,  # Open
        },
    }
    
    device = sim.device

    for skill_name, config in goals.items():
        print(f"\n[{skill_name}]")

        # Reset scene
        scene.reset()

        # Build joint positions for left robot (9 joints: 7 arm + 2 gripper)
        left_joint_pos = torch.zeros(1, num_joints_left, device=device)
        left_joint_vel = torch.zeros(1, num_joints_left, device=device)
        left_joints = torch.tensor(config["left"], device=device)
        left_joint_pos[0, 0:7] = left_joints
        left_joint_pos[0, 7] = config["left_grip"]
        left_joint_pos[0, 8] = config["left_grip"]

        # Build joint positions for right robot (9 joints: 7 arm + 2 gripper)
        right_joint_pos = torch.zeros(1, num_joints_right, device=device)
        right_joint_vel = torch.zeros(1, num_joints_right, device=device)
        right_joints = torch.tensor(config["right"], device=device)
        right_joint_pos[0, 0:7] = right_joints
        right_joint_pos[0, 7] = config["right_grip"]
        right_joint_pos[0, 8] = config["right_grip"]

        # Apply joint state to both robots
        robot_left.write_joint_state_to_sim(left_joint_pos, left_joint_vel)
        robot_right.write_joint_state_to_sim(right_joint_pos, right_joint_vel)
        
        # Step simulation to settle
        print("  Settling physics...")
        for _ in range(200):
            sim.step()
            scene.update(sim.cfg.dt)
        
        # Capture images
        print("  Capturing images...")
        save_images(scene, skill_name, save_dir)
    
    print("\n" + "=" * 60)
    print("Goal images captured!")
    print(f"Saved to: {save_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
    simulation_app.close()
