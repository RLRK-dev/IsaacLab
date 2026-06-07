"""
壁設置ロボット用の初期姿勢（ジョイント角度）を探索
目標: EEがケーブル上空 (X≈0.35, Y≈±0.15, Z≈0.90) に来る姿勢
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True
args.enable_cameras = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

import torch
import numpy as np
from isaaclab.scene import InteractiveScene
import isaaclab.sim as sim_utils

from envs.dual_arm_cfg import DualArmSceneCfg

def main():
    # シーン設定
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = 1

    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]

    device = robot_left.device

    # EEボディインデックス
    body_ids, _ = robot_left.find_bodies("panda_hand")
    ee_body_idx = body_ids[0]

    # 目標EE位置（ケーブル上空）
    # ケーブル: X=0.55, Y=-0.125〜+0.125, Z=0.755
    # 目標:    X=0.55, Y=±0.125, Z=0.90 (15cm上空)
    target_left_ee = torch.tensor([0.55, -0.125, 0.90], device=device)
    target_right_ee = torch.tensor([0.55, 0.125, 0.90], device=device)

    print("=" * 60)
    print("壁設置ロボット用 初期姿勢探索")
    print("=" * 60)
    print(f"目標 Left EE:  {target_left_ee.cpu().tolist()}")
    print(f"目標 Right EE: {target_right_ee.cpu().tolist()}")

    # 試すジョイント角度のバリエーション
    # Panda: joint1=ベース回転, joint2=肩, joint3=上腕回転, joint4=肘, joint5=前腕回転, joint6=手首, joint7=手首回転

    # 壁設置ロボットでアームをテーブル上（後方）に向けるには:
    # - joint1: ベースを内側に回転 (左: +, 右: -)
    # - joint2: 肩を上に (負の値)
    # - joint4: 肘を曲げる (負の値、-0.5〜-2.5)
    # - joint6: 手首を調整

    test_configs = [
        # [joint1, joint2, joint3, joint4, joint5, joint6, joint7]
        # 肩を後ろに、肘を深く曲げる
        {"name": "config_1", "joints": [0.5, -1.5, 0.0, -2.5, 0.0, 1.0, 0.785]},
        {"name": "config_2", "joints": [0.3, -1.2, 0.0, -2.2, 0.0, 1.2, 0.785]},
        {"name": "config_3", "joints": [0.4, -1.0, 0.0, -2.0, 0.0, 1.5, 0.785]},
        {"name": "config_4", "joints": [0.6, -1.3, 0.0, -2.3, 0.0, 0.8, 0.785]},
        {"name": "config_5", "joints": [0.7, -1.4, 0.0, -2.4, 0.0, 0.6, 0.785]},
        # より内向き
        {"name": "config_6", "joints": [0.8, -1.5, 0.0, -2.5, 0.0, 0.5, 0.785]},
        {"name": "config_7", "joints": [1.0, -1.2, 0.0, -2.0, 0.0, 1.0, 0.785]},
        {"name": "config_8", "joints": [0.9, -1.6, 0.0, -2.6, 0.0, 0.4, 0.785]},
    ]

    best_config = None
    best_dist = float('inf')

    for config in test_configs:
        name = config["name"]
        joints = config["joints"]

        # 左アーム（joint1を正に）
        left_joints = torch.tensor([joints], device=device, dtype=torch.float32)
        left_joints = torch.cat([left_joints, torch.tensor([[0.04, 0.04]], device=device)], dim=-1)

        # 右アーム（joint1を負に）
        right_joints = torch.tensor([joints], device=device, dtype=torch.float32)
        right_joints[0, 0] = -joints[0]  # joint1を反転
        right_joints = torch.cat([right_joints, torch.tensor([[0.04, 0.04]], device=device)], dim=-1)

        # ジョイント位置を設定（9DoF: 7関節 + 2グリッパー）
        robot_left.write_joint_state_to_sim(left_joints, torch.zeros_like(left_joints))
        robot_right.write_joint_state_to_sim(right_joints, torch.zeros_like(right_joints))

        # シミュレーションステップ
        for _ in range(30):
            scene.write_data_to_sim()
            sim.step()
            scene.update(sim.get_physics_dt())

        # EE位置取得
        left_ee = robot_left.data.body_pos_w[0, ee_body_idx, :]
        right_ee = robot_right.data.body_pos_w[0, ee_body_idx, :]

        # 距離計算
        left_dist = torch.norm(left_ee - target_left_ee).item()
        right_dist = torch.norm(right_ee - target_right_ee).item()
        total_dist = left_dist + right_dist

        print(f"\n{name}:")
        print(f"  Joints: {joints}")
        print(f"  Left EE:  {left_ee.cpu().tolist()} (dist: {left_dist:.3f}m)")
        print(f"  Right EE: {right_ee.cpu().tolist()} (dist: {right_dist:.3f}m)")
        print(f"  Total dist: {total_dist:.3f}m")

        if total_dist < best_dist:
            best_dist = total_dist
            best_config = config.copy()
            best_config["left_ee"] = left_ee.cpu().tolist()
            best_config["right_ee"] = right_ee.cpu().tolist()

    print("\n" + "=" * 60)
    print("最良の設定:")
    print("=" * 60)
    print(f"Config: {best_config['name']}")
    print(f"Joints: {best_config['joints']}")
    print(f"Left EE:  {best_config['left_ee']}")
    print(f"Right EE: {best_config['right_ee']}")
    print(f"Total dist: {best_dist:.3f}m")

    print("\n" + "=" * 60)
    print("collect_goal_images.py への修正:")
    print("=" * 60)
    joints = best_config['joints']
    print(f"""
# reset_arms_to_ready_position() 内のジョイント角度を以下に変更:
ready_joint_pos = torch.tensor([
    [{joints[0]}, {joints[1]}, {joints[2]}, {joints[3]}, {joints[4]}, {joints[5]}, {joints[6]}, 0.04, 0.04]
], device=self.device)

# 左アーム
left_joint_pos = ready_joint_pos.clone()
# joint1は既に正の値（内向き）

# 右アーム（joint1を反転）
right_joint_pos = ready_joint_pos.clone()
right_joint_pos[0, 0] = -{joints[0]}
""")

    # Robust exit: close with timeout, then force exit
    import threading
    import os

    def force_exit():
        print("[EXIT] Forcing exit after timeout...")
        os._exit(0)

    # Start a timer to force exit after 10 seconds
    exit_timer = threading.Timer(10.0, force_exit)
    exit_timer.daemon = True
    exit_timer.start()

    try:
        simulation_app.close()
    except Exception as e:
        print(f"[EXIT] close() failed: {e}")

    exit_timer.cancel()
    os._exit(0)  # Force clean exit

if __name__ == "__main__":
    main()
