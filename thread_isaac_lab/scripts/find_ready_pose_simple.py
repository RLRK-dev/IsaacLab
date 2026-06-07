"""
壁設置ロボット用の初期姿勢（ジョイント角度）を探索
カメラなし版 - ロボットのみをスポーン
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.headless = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import numpy as np
from isaaclab.assets import Articulation, ArticulationCfg
import isaaclab.sim as sim_utils
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# Panda robot configuration
@configclass
class PandaArmCfg(ArticulationCfg):
    prim_path = "{ENV_NS}/Robot"
    spawn = sim_utils.UsdFileCfg(
        usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Robots/Franka/franka_panda_sensor.usd",
        activate_contact_sensors=False,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=0,
        ),
    )
    init_state = ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        rot=(1.0, 0.0, 0.0, 0.0),
        joint_pos={"panda_joint[1-7]": 0.0, "panda_finger_joint.*": 0.04},
    )

def main():
    # シミュレーション設定
    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0, render_interval=1)
    sim = sim_utils.SimulationContext(sim_cfg)

    # Ground plane
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/ground", ground_cfg)

    # 壁設置ロボット設定
    # X=-0.05 (壁), Z=1.10 (高さ), Y軸+90°回転
    ARM_X_POS = 0.0  # ベース位置
    ARM_Z_POS = 1.10
    ARM_Y_OFFSET = 0.20  # 左右間隔

    # Y軸+90°回転 (w, x, y, z)
    wall_rot = (0.7071, 0.0, 0.7071, 0.0)

    # 左アーム設定
    left_cfg = PandaArmCfg()
    left_cfg.prim_path = "/World/RobotLeft"
    left_cfg.spawn.func(
        prim_path=left_cfg.prim_path,
        cfg=left_cfg.spawn,
        translation=(ARM_X_POS, -ARM_Y_OFFSET, ARM_Z_POS),
        orientation=wall_rot,
    )

    # 右アーム設定
    right_cfg = PandaArmCfg()
    right_cfg.prim_path = "/World/RobotRight"
    right_cfg.spawn.func(
        prim_path=right_cfg.prim_path,
        cfg=right_cfg.spawn,
        translation=(ARM_X_POS, ARM_Y_OFFSET, ARM_Z_POS),
        orientation=wall_rot,
    )

    # シミュレーション開始
    sim.reset()

    # ロボット作成
    robot_left = Articulation(left_cfg)
    robot_right = Articulation(right_cfg)

    # 初期化
    sim.step()
    robot_left.update(sim.get_physics_dt())
    robot_right.update(sim.get_physics_dt())

    device = robot_left.device

    # EEボディインデックス
    body_ids, _ = robot_left.find_bodies("panda_hand")
    ee_body_idx = body_ids[0]

    # 目標EE位置（ケーブル上空）
    target_left_ee = torch.tensor([0.35, -0.15, 0.90], device=device)
    target_right_ee = torch.tensor([0.35, 0.10, 0.90], device=device)

    print("=" * 60)
    print("壁設置ロボット用 初期姿勢探索")
    print("=" * 60)
    print(f"目標 Left EE:  {target_left_ee.cpu().tolist()}")
    print(f"目標 Right EE: {target_right_ee.cpu().tolist()}")

    # Franka Pandaの関節限界
    JOINT_LIMITS = {
        'lower': np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973]),
        'upper': np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])
    }

    # 試すジョイント角度のバリエーション
    test_configs = [
        {"name": "config_1", "joints": [0.5, -1.5, 0.0, -2.5, 0.0, 1.0, 0.785]},
        {"name": "config_2", "joints": [0.3, -1.2, 0.0, -2.2, 0.0, 1.2, 0.785]},
        {"name": "config_3", "joints": [0.4, -1.0, 0.0, -2.0, 0.0, 1.5, 0.785]},
        {"name": "config_4", "joints": [0.6, -1.3, 0.0, -2.3, 0.0, 0.8, 0.785]},
        {"name": "config_5", "joints": [0.7, -1.4, 0.0, -2.4, 0.0, 0.6, 0.785]},
        {"name": "config_6", "joints": [0.8, -1.5, 0.0, -2.5, 0.0, 0.5, 0.785]},
        {"name": "config_7", "joints": [1.0, -1.2, 0.0, -2.0, 0.0, 1.0, 0.785]},
        {"name": "config_8", "joints": [0.9, -1.6, 0.0, -2.6, 0.0, 0.4, 0.785]},
        # 追加の候補
        {"name": "config_9", "joints": [0.4, -0.8, 0.0, -1.8, 0.0, 1.2, 0.785]},
        {"name": "config_10", "joints": [0.6, -1.0, 0.0, -1.5, 0.0, 0.8, 0.785]},
        {"name": "config_11", "joints": [0.3, -0.5, 0.0, -2.0, 0.0, 1.8, 0.785]},
        {"name": "config_12", "joints": [0.5, -0.7, 0.0, -1.8, 0.0, 1.5, 0.785]},
    ]

    best_config = None
    best_dist = float('inf')

    for config in test_configs:
        name = config["name"]
        joints = config["joints"]

        # 関節マージンを計算
        margins = []
        for j, angle in enumerate(joints):
            margin_low = angle - JOINT_LIMITS['lower'][j]
            margin_high = JOINT_LIMITS['upper'][j] - angle
            margins.append(min(margin_low, margin_high))
        min_margin = min(margins)
        margin_deg = np.degrees(min_margin)

        # 左アーム（joint1を正に）
        left_joints = torch.tensor([joints + [0.04, 0.04]], device=device, dtype=torch.float32)

        # 右アーム（joint1を負に）
        right_joints = torch.tensor([joints + [0.04, 0.04]], device=device, dtype=torch.float32)
        right_joints[0, 0] = -joints[0]  # joint1を反転

        # ジョイント位置を設定
        robot_left.write_joint_state_to_sim(left_joints, torch.zeros_like(left_joints))
        robot_right.write_joint_state_to_sim(right_joints, torch.zeros_like(right_joints))

        # シミュレーションステップ
        for _ in range(30):
            robot_left.write_data_to_sim()
            robot_right.write_data_to_sim()
            sim.step()
            robot_left.update(sim.get_physics_dt())
            robot_right.update(sim.get_physics_dt())

        # EE位置取得
        left_ee = robot_left.data.body_pos_w[0, ee_body_idx, :]
        right_ee = robot_right.data.body_pos_w[0, ee_body_idx, :]

        # 距離計算
        left_dist = torch.norm(left_ee - target_left_ee).item()
        right_dist = torch.norm(right_ee - target_right_ee).item()
        total_dist = left_dist + right_dist

        print(f"\n{name}:")
        print(f"  Joints: {joints}")
        print(f"  Left EE:  [{left_ee[0].item():.3f}, {left_ee[1].item():.3f}, {left_ee[2].item():.3f}] (dist: {left_dist:.3f}m)")
        print(f"  Right EE: [{right_ee[0].item():.3f}, {right_ee[1].item():.3f}, {right_ee[2].item():.3f}] (dist: {right_dist:.3f}m)")
        print(f"  Total dist: {total_dist:.3f}m, Min margin: {margin_deg:.1f}°")

        # マージンが十分あるものの中で最小距離を選択
        if total_dist < best_dist and min_margin > 0.2:  # 約11°以上のマージン
            best_dist = total_dist
            best_config = config.copy()
            best_config["left_ee"] = [left_ee[0].item(), left_ee[1].item(), left_ee[2].item()]
            best_config["right_ee"] = [right_ee[0].item(), right_ee[1].item(), right_ee[2].item()]
            best_config["min_margin"] = margin_deg

    print("\n" + "=" * 60)
    print("最良の設定:")
    print("=" * 60)
    if best_config:
        print(f"Config: {best_config['name']}")
        print(f"Joints: {best_config['joints']}")
        print(f"Left EE:  {best_config['left_ee']}")
        print(f"Right EE: {best_config['right_ee']}")
        print(f"Total dist: {best_dist:.3f}m")
        print(f"Min margin: {best_config['min_margin']:.1f}°")

        joints = best_config['joints']
        print(f"\n--- collect_goal_images.py への適用 ---")
        print(f"""
ready_joint_pos = torch.tensor([
    [{joints[0]}, {joints[1]}, {joints[2]}, {joints[3]}, {joints[4]}, {joints[5]}, {joints[6]}, 0.04, 0.04]
], device=self.device)

# 左アーム: そのまま使用
left_joint_pos = ready_joint_pos.clone()

# 右アーム: joint1を反転
right_joint_pos = ready_joint_pos.clone()
right_joint_pos[0, 0] = -{joints[0]}
""")
    else:
        print("適切な候補が見つかりませんでした。探索範囲を広げてください。")

    simulation_app.close()

if __name__ == "__main__":
    main()
