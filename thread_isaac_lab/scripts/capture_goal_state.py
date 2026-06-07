#!/usr/bin/env python3
"""Capture goal state images from simulation.

シミュレーションGUIでゴール状態を手動設定し、
カメラ画像を保存するスクリプト。

使用方法:
1. シミュレーションを起動（--headlessなし）
2. GUIでロボット/ケーブル/フックを手動配置
3. キー入力でスクリーンショット撮影

キーバインド:
  1-6: 各スキルのゴール画像を保存
  r: 環境リセット
  q: 終了
"""

import argparse
import sys
from pathlib import Path

# Parse arguments before Isaac Lab
parser = argparse.ArgumentParser(description="Capture goal state images")
parser.add_argument("--save_dir", type=str, default="goal_images")
parser.add_argument("--cameras", type=str, nargs='+',
                    default=['front_left', 'front_right', 'back'])

# AppLauncher args
from omni.isaac.lab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Force headless=False for GUI
args_cli.headless = False
args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Isaac Lab imports
import torch
import omni.isaac.lab.sim as sim_utils
from omni.isaac.lab.envs import ManagerBasedRLEnv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from thread_isaac_lab.envs.dual_arm_flex_env_cfg import DualArmFlexEnvCfg

SKILLS = {
    "1": ("bimanual_reach", "両手がケーブル両端に到達"),
    "2": ("bimanual_grasp", "両手でケーブル両端を把持"),
    "3": ("bimanual_lift", "ケーブルを持ち上げ"),
    "4": ("bimanual_transport", "ケーブル中央をフック付近へ"),
    "5": ("bimanual_hang", "ケーブルをフックに掛ける"),
    "6": ("bimanual_release", "グリッパーを開いて離す"),
}


def save_goal_images(env, skill_name: str, save_dir: str, cameras: list):
    """Save current camera images as goal images."""
    import torchvision.transforms as T
    from PIL import Image
    
    save_path = Path(save_dir) / skill_name
    save_path.mkdir(parents=True, exist_ok=True)
    
    obs = env.observation_manager.compute()
    
    for cam in cameras:
        key = f"{cam}_img"
        if key in obs:
            img = obs[key][0].cpu()
            
            # Save as tensor
            torch.save(img, save_path / f"{cam}.pt")
            
            # Save as PNG
            if img.dim() == 3 and img.shape[0] == 3:
                pil_img = T.ToPILImage()(img)
                pil_img.save(save_path / f"{cam}.png")
    
    print(f"[Saved] {skill_name} to {save_path}")


def main():
    print("\n" + "=" * 60)
    print("Goal State Capture Tool")
    print("=" * 60)
    print("\nキーバインド:")
    for key, (skill, desc) in SKILLS.items():
        print(f"  {key}: {skill} - {desc}")
    print("  r: リセット")
    print("  q: 終了")
    print("=" * 60)
    
    # Create environment
    env_cfg = DualArmFlexEnvCfg()
    env_cfg.scene.num_envs = 1
    env = ManagerBasedRLEnv(cfg=env_cfg)
    
    print("\n[Ready] Use simulation GUI to set goal states")
    print("[Ready] Press number keys to capture images")
    
    try:
        while simulation_app.is_running():
            # Step simulation
            env.step(torch.zeros(1, 18, device=env.device))
            
            # Check keyboard input (from stdin for now)
            # Note: In full implementation, use Omniverse keyboard callbacks
            import select
            if select.select([sys.stdin], [], [], 0.0)[0]:
                key = sys.stdin.readline().strip()
                
                if key in SKILLS:
                    skill_name, desc = SKILLS[key]
                    print(f"\n[Capture] {skill_name}: {desc}")
                    save_goal_images(env, skill_name, args_cli.save_dir, args_cli.cameras)
                elif key == 'r':
                    print("\n[Reset] Resetting environment...")
                    env.reset()
                elif key == 'q':
                    print("\n[Exit] Closing...")
                    break
    finally:
        env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
