"""
逆運動学（IK）を使って、ケーブル上空にEEを配置するジョイント角度を計算する

目標: EEを (X=0.50, Y=±0.20/0.25, Z=0.90) に配置するジョイント角度を見つける
方法: DifferentialIKを繰り返し適用して目標位置に収束させる
改良: 複数の初期姿勢を試して関節マージンが最も大きい解を選択
"""
import torch
import numpy as np
from scipy.spatial.transform import Rotation as R

# 目標EE位置（ケーブル上空）
# ロボット: X=-0.10, Y=±0.35, Z=1.50
# ケーブル: X=0.50, Y=[-0.20, +0.25], Z=0.755
# EE目標: X=0.50, Y=ケーブル端, Z=0.90（ケーブル上空15cm）
# Note: joint6 margin is only 5° - at physical limit of workspace
TARGET_LEFT_EE_POS = [0.50, -0.20, 0.90]
TARGET_RIGHT_EE_POS = [0.50, 0.25, 0.90]

# グリッパー下向き姿勢（X軸周りに180°回転）
TARGET_QUAT_WXYZ = [0.0, 0.707107, 0.707107, 0.0]  # w, x, y, z

# Franka Pandaの関節限界（ラジアン）
JOINT_LIMITS_LOWER = torch.tensor([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_LIMITS_UPPER = torch.tensor([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# 関節限界から少なくともこれだけ離れた解を探す（15度 = 0.262ラジアン）
MIN_JOINT_MARGIN_RAD = 0.262

def main():
    import sys
    sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

    from isaaclab.app import AppLauncher
    import argparse
    parser = argparse.ArgumentParser()
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args(["--headless", "--enable_cameras"])
    app_launcher = AppLauncher(args)
    simulation_app = app_launcher.app

    import isaaclab.sim as sim_utils
    from isaaclab.scene import InteractiveScene
    from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
    from envs.dual_arm_cfg import DualArmSceneCfg

    # シーン作成
    scene_cfg = DualArmSceneCfg()
    scene_cfg.num_envs = 1
    sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    device = robot_left.device

    # デバッグ: ロボットベース位置を表示
    print("\n[DEBUG] Robot Base Positions:")
    left_base = robot_left.data.root_pos_w[0].cpu().numpy()
    right_base = robot_right.data.root_pos_w[0].cpu().numpy()
    print(f"  Left base:  {left_base}")
    print(f"  Right base: {right_base}")

    # EEボディインデックスを取得
    body_ids, _ = robot_left.find_bodies("panda_hand")
    ee_body_idx = body_ids[0]

    # ジョイントインデックスを取得
    joint_ids, _ = robot_left.find_joints("panda_joint.*")
    arm_joint_ids = list(joint_ids)

    print("\n" + "="*70)
    print("IK Solver for Initial Ready Pose (Multi-Config Search)")
    print("="*70)
    print(f"Target Left EE:  {TARGET_LEFT_EE_POS}")
    print(f"Target Right EE: {TARGET_RIGHT_EE_POS}")
    print(f"Target Orientation (wxyz): {TARGET_QUAT_WXYZ}")
    print(f"Min joint margin required: {np.degrees(MIN_JOINT_MARGIN_RAD):.1f}°")
    print("="*70)

    # DifferentialIKコントローラを作成
    diff_ik_cfg = DifferentialIKControllerCfg(
        command_type="pose",
        use_relative_mode=False,
        ik_method="dls",
        ik_params={"lambda_val": 0.01},  # 小さい値で精度向上
    )

    # 左右のIKコントローラ
    ik_left = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)
    ik_right = DifferentialIKController(diff_ik_cfg, num_envs=1, device=device)

    # 目標姿勢を設定
    target_pos_left = torch.tensor([TARGET_LEFT_EE_POS], device=device)
    target_pos_right = torch.tensor([TARGET_RIGHT_EE_POS], device=device)
    target_quat = torch.tensor([TARGET_QUAT_WXYZ], device=device)

    # 複数の初期姿勢を生成（関節限界を避けるため）
    def generate_init_configs():
        """複数の初期関節構成を生成"""
        configs = []

        # 基本: 関節中央
        joint_mid = (JOINT_LIMITS_LOWER + JOINT_LIMITS_UPPER) / 2
        joint_mid[3] = -1.5  # 肘を曲げる
        joint_mid[5] = 1.5   # joint6を中央寄りに
        configs.append(("middle", joint_mid.clone()))

        # 変種1: joint6を低く（関節限界から遠く）
        v1 = joint_mid.clone()
        v1[5] = 1.0
        configs.append(("j6_low", v1))

        # 変種2: joint6を中程度
        v2 = joint_mid.clone()
        v2[5] = 2.0
        v2[3] = -2.0
        configs.append(("j6_mid_elbow_bent", v2))

        # 変種3: joint1を正に回転
        v3 = joint_mid.clone()
        v3[0] = 0.5
        v3[5] = 1.2
        configs.append(("j1_pos", v3))

        # 変種4: joint1を負に回転
        v4 = joint_mid.clone()
        v4[0] = -0.5
        v4[5] = 1.2
        configs.append(("j1_neg", v4))

        # 変種5: joint7をゼロに、joint6を高く
        v5 = joint_mid.clone()
        v5[6] = 0.0
        v5[5] = 2.5
        configs.append(("j7_zero_j6_high", v5))

        # 変種6: 肘を大きく曲げる
        v6 = joint_mid.clone()
        v6[3] = -2.5
        v6[5] = 2.0
        configs.append(("elbow_very_bent", v6))

        # 変種7: joint5を変更
        v7 = joint_mid.clone()
        v7[4] = 1.0
        v7[5] = 1.5
        configs.append(("j5_pos", v7))

        # 変種8: joint5を負に
        v8 = joint_mid.clone()
        v8[4] = -1.0
        v8[5] = 1.5
        configs.append(("j5_neg", v8))

        return configs

    init_configs = generate_init_configs()
    print(f"\nTrying {len(init_configs)} initial configurations...")

    # シミュレーションステップで安定化
    for _ in range(30):
        sim.step()
        scene.update(sim.get_physics_dt())

    # IKパラメータ
    max_iterations = 300
    convergence_threshold = 0.015  # 1.5cm

    def compute_min_margin(joint_pos):
        """関節限界からの最小マージンを計算"""
        margins = []
        for j, angle in enumerate(joint_pos):
            margin_low = angle - JOINT_LIMITS_LOWER[j].item()
            margin_high = JOINT_LIMITS_UPPER[j].item() - angle
            margins.append(min(margin_low, margin_high))
        return min(margins), margins

    def print_joint_margins(joint_pos, prefix=""):
        """関節マージンを表示"""
        _, margins = compute_min_margin(joint_pos)
        print(f"{prefix}Joint margins (deg):")
        for j, margin in enumerate(margins):
            margin_deg = np.degrees(margin)
            status = "⚠️ LOW" if margin_deg < 15 else "✓"
            print(f"  {prefix}  joint{j+1}: {margin_deg:6.1f}° {status}")

    # 結果を格納
    results = {}

    for arm_name, robot, ik_controller, target_pos in [
        ("Left", robot_left, ik_left, target_pos_left),
        ("Right", robot_right, ik_right, target_pos_right),
    ]:
        print(f"\n{'='*70}")
        print(f"[{arm_name} Arm] Solving IK with {len(init_configs)} initial configs...")
        print("="*70)

        best_overall_joints = None
        best_overall_margin = -float('inf')
        best_overall_distance = float('inf')
        best_config_name = None
        best_ee_pos = None

        for config_name, init_joints in init_configs:
            print(f"\n  [{config_name}] Testing...")

            # ロボットを初期位置にリセット
            init_joint_pos = torch.tensor([init_joints.tolist() + [0.04, 0.04]], device=device)
            robot.write_joint_state_to_sim(init_joint_pos, torch.zeros_like(init_joint_pos))
            robot.set_joint_position_target(init_joint_pos)

            for _ in range(10):
                sim.step()
                scene.update(sim.get_physics_dt())

            ik_controller.reset()

            best_joint_pos_this_config = None
            best_distance_this_config = float('inf')

            # IK反復
            for iteration in range(max_iterations):
                # 現在のEE位置を取得
                ee_pos = robot.data.body_pos_w[:, ee_body_idx, :]
                ee_quat = robot.data.body_quat_w[:, ee_body_idx, :]

                # 目標との距離
                distance = torch.norm(ee_pos - target_pos).item()

                if distance < best_distance_this_config:
                    best_distance_this_config = distance
                    best_joint_pos_this_config = robot.data.joint_pos[0, :7].cpu().numpy()

                if distance < convergence_threshold:
                    break

                # ヤコビアン取得
                jacobian = robot.root_physx_view.get_jacobians()[:, ee_body_idx - 1, :, arm_joint_ids]

                # 現在のジョイント位置
                current_joint_pos = robot.data.joint_pos[:, arm_joint_ids]

                # IKコマンドを設定
                ik_controller.set_command(
                    command=torch.cat([target_pos, target_quat], dim=-1),
                    ee_pos=ee_pos,
                    ee_quat=ee_quat,
                )

                # IK計算
                joint_pos_target = ik_controller.compute(
                    ee_pos=ee_pos,
                    ee_quat=ee_quat,
                    jacobian=jacobian,
                    joint_pos=current_joint_pos,
                )

                # ジョイント限界をクリップ
                joint_pos_target = torch.clamp(
                    joint_pos_target,
                    JOINT_LIMITS_LOWER.to(device),
                    JOINT_LIMITS_UPPER.to(device),
                )

                # ジョイント位置を適用
                full_joint_pos = robot.data.joint_pos.clone()
                full_joint_pos[:, arm_joint_ids] = joint_pos_target
                robot.write_joint_state_to_sim(full_joint_pos, torch.zeros_like(full_joint_pos))
                robot.set_joint_position_target(full_joint_pos)

                # シミュレーションステップ
                for _ in range(2):
                    sim.step()
                    scene.update(sim.get_physics_dt())

            # この設定の結果を評価
            if best_joint_pos_this_config is not None:
                min_margin, _ = compute_min_margin(best_joint_pos_this_config)
                final_ee = robot.data.body_pos_w[0, ee_body_idx].cpu().numpy()

                converged = best_distance_this_config < convergence_threshold
                status = "✓ CONVERGED" if converged else "✗ NOT CONVERGED"
                margin_status = "✓ GOOD" if min_margin > MIN_JOINT_MARGIN_RAD else "⚠️ LOW"

                print(f"    {status}, dist={best_distance_this_config:.4f}m, "
                      f"min_margin={np.degrees(min_margin):.1f}° {margin_status}")

                # 収束し、かつマージンが良い解を優先
                if converged:
                    # マージンが最良か、または同等マージンで距離が近い場合に更新
                    if min_margin > best_overall_margin or \
                       (min_margin > MIN_JOINT_MARGIN_RAD and min_margin >= best_overall_margin - 0.01 and best_distance_this_config < best_overall_distance):
                        best_overall_joints = best_joint_pos_this_config
                        best_overall_margin = min_margin
                        best_overall_distance = best_distance_this_config
                        best_config_name = config_name
                        best_ee_pos = final_ee.copy()
                        print(f"    ★ New best solution!")

        # アームの最終結果
        print(f"\n[{arm_name} Arm] Best Solution:")
        if best_overall_joints is not None:
            print(f"  Config:     {best_config_name}")
            print(f"  Target EE:  {target_pos[0].cpu().numpy()}")
            print(f"  Actual EE:  {best_ee_pos}")
            print(f"  Distance:   {best_overall_distance:.4f}m")
            print(f"  Min margin: {np.degrees(best_overall_margin):.1f}°")
            print_joint_margins(best_overall_joints, "  ")
            print(f"  Joint angles: {best_overall_joints.tolist()}")

            results[arm_name] = {
                'joint_pos': best_overall_joints,
                'ee_pos': best_ee_pos,
                'distance': best_overall_distance,
                'margin': best_overall_margin,
                'config': best_config_name,
            }
        else:
            print(f"  ❌ No valid solution found!")
            results[arm_name] = None

    # 結果サマリー
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    left_result = results.get("Left")
    right_result = results.get("Right")

    if left_result:
        print(f"Left Arm ({left_result['config']}):")
        print(f"  Joint angles: {left_result['joint_pos'].tolist()}")
        print(f"  EE position:  {left_result['ee_pos'].tolist()}")
        print(f"  Distance:     {left_result['distance']:.4f}m")
        print(f"  Min margin:   {np.degrees(left_result['margin']):.1f}°")
    else:
        print("Left Arm: NO VALID SOLUTION")

    if right_result:
        print(f"\nRight Arm ({right_result['config']}):")
        print(f"  Joint angles: {right_result['joint_pos'].tolist()}")
        print(f"  EE position:  {right_result['ee_pos'].tolist()}")
        print(f"  Distance:     {right_result['distance']:.4f}m")
        print(f"  Min margin:   {np.degrees(right_result['margin']):.1f}°")
    else:
        print("\nRight Arm: NO VALID SOLUTION")

    # 推奨コード
    if left_result and right_result:
        print("\n" + "="*70)
        print("RECOMMENDED CODE FOR reset_arms_to_ready_position():")
        print("="*70)
        print(f"""
    # IK-solved ready position for cable at X=0.50
    # Left: config={left_result['config']}, margin={np.degrees(left_result['margin']):.1f}°
    # Right: config={right_result['config']}, margin={np.degrees(right_result['margin']):.1f}°
    ready_joint_pos_left = torch.tensor([
        {left_result['joint_pos'].tolist() + [0.04, 0.04]}
    ], device=self.device)

    ready_joint_pos_right = torch.tensor([
        {right_result['joint_pos'].tolist() + [0.04, 0.04]}
    ], device=self.device)
    """)
        print("="*70)
    else:
        print("\n⚠️ Could not generate recommended code - missing solutions!")

    # Robust exit
    import threading
    import os

    def force_exit():
        print("[EXIT] Forcing exit after timeout...")
        os._exit(0)

    exit_timer = threading.Timer(10.0, force_exit)
    exit_timer.daemon = True
    exit_timer.start()

    try:
        simulation_app.close()
    except Exception as e:
        print(f"[EXIT] close() failed: {e}")

    exit_timer.cancel()
    os._exit(0)

if __name__ == "__main__":
    main()
