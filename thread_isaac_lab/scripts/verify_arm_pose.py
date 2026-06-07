"""
壁設置ロボットの初期姿勢を確認するスクリプト
アームがテーブルの上（Z > 0.75m）に来ているか検証
"""

import argparse
import sys
import os

# IsaacLab imports
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Verify wall-mounted arm pose")

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
from isaaclab.sim import SimulationContext, SimulationCfg

# Import environment config
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT
from isaaclab.scene import InteractiveScene

def main():
    print("=" * 60)
    print("壁設置ロボット姿勢検証")
    print("=" * 60)

    # Create simulation context
    sim_cfg = SimulationCfg(dt=1/60, device="cuda:0")
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[1.5, 0.0, 1.5], target=[0.4, 0.0, 0.85])

    # Create scene
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    # Play simulation
    sim.reset()

    # Run a few simulation steps
    for _ in range(10):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Get robot EE positions
    left_ee_pos = None
    right_ee_pos = None

    try:
        robot1 = scene["robot_1"]
        robot2 = scene["robot_2"]

        # Get panda_hand body index
        hand_idx = robot1.find_bodies("panda_hand")[0][0]

        # Get body positions
        left_ee_pos = robot1.data.body_pos_w[0, hand_idx].cpu().numpy()
        right_ee_pos = robot2.data.body_pos_w[0, hand_idx].cpu().numpy()
    except Exception as e:
        print(f"Articulation error: {e}")

    print("\n--- 初期EE位置 ---")

    if left_ee_pos is not None:
        print(f"Left EE:  X={left_ee_pos[0]:.3f}, Y={left_ee_pos[1]:.3f}, Z={left_ee_pos[2]:.3f}")
        if left_ee_pos[2] > TABLE_HEIGHT:
            print(f"  ✓ テーブル上 (Z > {TABLE_HEIGHT})")
        else:
            print(f"  ✗ テーブル下! (Z < {TABLE_HEIGHT})")

    if right_ee_pos is not None:
        print(f"Right EE: X={right_ee_pos[0]:.3f}, Y={right_ee_pos[1]:.3f}, Z={right_ee_pos[2]:.3f}")
        if right_ee_pos[2] > TABLE_HEIGHT:
            print(f"  ✓ テーブル上 (Z > {TABLE_HEIGHT})")
        else:
            print(f"  ✗ テーブル下! (Z < {TABLE_HEIGHT})")

    # Get joint positions
    print("\n--- ジョイント角度 ---")
    try:
        robot1 = scene["robot_1"]
        joint_pos = robot1.data.joint_pos[0, :7].cpu().numpy()
        joint_names = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"]
        for name, pos in zip(joint_names, joint_pos):
            print(f"  {name}: {np.degrees(pos):7.2f}° ({pos:.3f} rad)")
    except Exception as e:
        print(f"Joint position error: {e}")

    print("\n" + "=" * 60)

    # Keep simulation running for visual inspection if not headless
    if not args.headless:
        print("GUIで姿勢を確認中... (Ctrl+Cで終了)")
        try:
            while simulation_app.is_running():
                sim.step()
                scene.update(sim.get_physics_dt())
        except KeyboardInterrupt:
            print("\n終了")

if __name__ == "__main__":
    main()
