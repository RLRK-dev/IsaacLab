#!/usr/bin/env python3
"""Generate goal images by scripting robot/cable positions.

各スキルのゴール状態をプログラムで設定し、
カメラ画像を自動撮影する。
"""

import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--save_dir", type=str, default="goal_images")
parser.add_argument("--headless", action="store_true")

from omni.isaac.lab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import numpy as np
import torchvision.transforms as T
from PIL import Image
from omni.isaac.lab.envs import ManagerBasedRLEnv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from thread_isaac_lab.envs.dual_arm_flex_env_cfg import DualArmFlexEnvCfg


def save_images(env, skill_name: str, save_dir: str, cameras: list):
    """Save camera images."""
    save_path = Path(save_dir) / skill_name
    save_path.mkdir(parents=True, exist_ok=True)
    
    obs = env.observation_manager.compute()
    
    for cam in cameras:
        key = f"{cam}_img"
        if key in obs:
            img = obs[key][0].cpu()
            torch.save(img, save_path / f"{cam}.pt")
            
            if img.dim() == 3 and img.shape[0] == 3:
                pil_img = T.ToPILImage()(img)
                pil_img.save(save_path / f"{cam}.png")
    
    print(f"  [Saved] {skill_name}")


def run_to_goal_state(env, skill_name: str, steps: int = 100):
    """Run environment towards a goal state."""
    device = env.device
    
    # Get current state
    obs = env.observation_manager.compute()
    
    # Simple scripted actions for each skill
    # Note: These are approximate - real goals may need tuning
    
    if skill_name == "bimanual_reach":
        # Move hands toward cable ends
        # Left arm moves toward cable left end, right toward right end
        for _ in range(steps):
            action = torch.zeros(1, 18, device=device)
            # Move arms downward and toward center
            action[0, 2] = -0.1   # Left arm down
            action[0, 11] = -0.1  # Right arm down
            env.step(action)
    
    elif skill_name == "bimanual_grasp":
        # Close grippers after reaching
        for _ in range(steps):
            action = torch.zeros(1, 18, device=device)
            action[0, 7:9] = -1.0   # Close left gripper
            action[0, 16:18] = -1.0  # Close right gripper
            env.step(action)
    
    elif skill_name == "bimanual_lift":
        # Lift arms up
        for _ in range(steps):
            action = torch.zeros(1, 18, device=device)
            action[0, 2] = 0.2   # Left arm up
            action[0, 11] = 0.2  # Right arm up
            env.step(action)
    
    elif skill_name == "bimanual_transport":
        # Move toward hook position
        for _ in range(steps):
            action = torch.zeros(1, 18, device=device)
            action[0, 0] = 0.1   # Left arm forward
            action[0, 9] = 0.1   # Right arm forward
            env.step(action)
    
    elif skill_name == "bimanual_hang":
        # Lower cable onto hook
        for _ in range(steps):
            action = torch.zeros(1, 18, device=device)
            action[0, 2] = -0.05  # Slight down
            action[0, 11] = -0.05
            env.step(action)
    
    elif skill_name == "bimanual_release":
        # Open grippers
        for _ in range(steps):
            action = torch.zeros(1, 18, device=device)
            action[0, 7:9] = 1.0   # Open left gripper
            action[0, 16:18] = 1.0  # Open right gripper
            env.step(action)
    
    # Let simulation settle
    for _ in range(20):
        env.step(torch.zeros(1, 18, device=device))


def main():
    print("\n" + "=" * 60)
    print("Goal Image Generation")
    print("=" * 60)
    
    save_dir = args_cli.save_dir
    cameras = ['front_left', 'front_right', 'back']
    
    # Create environment
    env_cfg = DualArmFlexEnvCfg()
    env_cfg.scene.num_envs = 1
    env = ManagerBasedRLEnv(cfg=env_cfg)
    
    skills = [
        "bimanual_reach",
        "bimanual_grasp",
        "bimanual_lift",
        "bimanual_transport",
        "bimanual_hang",
        "bimanual_release",
    ]
    
    print(f"\nGenerating goal images for {len(skills)} skills...")
    print(f"Save directory: {save_dir}")
    
    for skill in skills:
        print(f"\n[{skill}]")
        
        # Reset environment
        env.reset()
        
        # Run to approximate goal state
        print(f"  Running to goal state...")
        run_to_goal_state(env, skill, steps=50)
        
        # Save images
        save_images(env, skill, save_dir, cameras)
    
    print("\n" + "=" * 60)
    print("Goal image generation complete!")
    print(f"Images saved to: {save_dir}")
    print("\nNote: These are approximate goal states from scripted actions.")
    print("For best results, manually verify and adjust if needed.")
    print("=" * 60)
    
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
