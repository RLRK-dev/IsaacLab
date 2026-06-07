#!/usr/bin/env python3
"""
Franka Panda 壁設置時の可動範囲解析

機能:
1. DHパラメータによるForward Kinematics計算
2. 関節限界内での全到達可能点をサンプリング
3. 壁設置回転（Y軸+90°）を適用
4. 3D/2D可視化とPNG保存
5. ケーブル位置候補の到達可能性判定
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from itertools import product
import os

# ============================================================================
# Franka Panda パラメータ
# ============================================================================

# Modified DH パラメータ [a, d, alpha, theta_offset]
# 参考: https://frankaemika.github.io/docs/control_parameters.html
DH_PARAMS = [
    [0.0,     0.333,   0.0,        0.0],      # joint1
    [0.0,     0.0,    -np.pi/2,    0.0],      # joint2
    [0.0,     0.316,   np.pi/2,    0.0],      # joint3
    [0.0825,  0.0,     np.pi/2,    0.0],      # joint4
    [-0.0825, 0.384,  -np.pi/2,    0.0],      # joint5
    [0.0,     0.0,     np.pi/2,    0.0],      # joint6
    [0.088,   0.0,     np.pi/2,    0.0],      # joint7
]

# フランジからEE（グリッパー先端）までのオフセット
FLANGE_TO_EE = 0.1123  # panda_hand + finger offset

# 関節限界 (radians)
JOINT_LIMITS = [
    [-2.8973, 2.8973],   # joint1
    [-1.7628, 1.7628],   # joint2 ← 制限が厳しい
    [-2.8973, 2.8973],   # joint3
    [-3.0718, -0.0698],  # joint4
    [-2.8973, 2.8973],   # joint5
    [-0.0175, 3.7525],   # joint6
    [-2.8973, 2.8973],   # joint7
]

# ロボットベース位置（壁設置）
LEFT_ARM_BASE = np.array([-0.10, -0.30, 1.00])
RIGHT_ARM_BASE = np.array([-0.10, +0.30, 1.00])

# 壁設置回転 (Y軸+90°) - クォータニオン (w, x, y, z)
# ロボットが+X方向を向く
WALL_MOUNT_QUAT = [0.7071, 0.0, 0.7071, 0.0]

# Z断面高さ（ケーブル把持領域）
Z_SLICE_HEIGHTS = [0.755, 0.80, 0.85]
Z_SLICE_TOLERANCE = 0.03  # ±3cm

# ケーブル位置候補
CABLE_CANDIDATES = {
    "Y軸レイアウト": {"x": 0.40, "y_range": [-0.30, 0.30], "z": 0.755},
    "X軸(現在)": {"x_range": [-0.07, 0.48], "y": 0.0, "z": 0.755},
    "X軸(移動後)": {"x_range": [0.03, 0.58], "y": 0.0, "z": 0.755},
}


# ============================================================================
# Forward Kinematics
# ============================================================================

def dh_transform(a, d, alpha, theta):
    """Modified DH変換行列を計算"""
    ct = np.cos(theta)
    st = np.sin(theta)
    ca = np.cos(alpha)
    sa = np.sin(alpha)

    return np.array([
        [ct,      -st,      0,      a],
        [st*ca,   ct*ca,   -sa,   -sa*d],
        [st*sa,   ct*sa,    ca,    ca*d],
        [0,       0,        0,      1]
    ])


def quat_to_rotation_matrix(quat):
    """クォータニオン (w, x, y, z) から回転行列を計算"""
    w, x, y, z = quat

    return np.array([
        [1 - 2*y*y - 2*z*z,     2*x*y - 2*z*w,       2*x*z + 2*y*w],
        [2*x*y + 2*z*w,         1 - 2*x*x - 2*z*z,   2*y*z - 2*x*w],
        [2*x*z - 2*y*w,         2*y*z + 2*x*w,       1 - 2*x*x - 2*y*y]
    ])


def forward_kinematics(joint_angles, include_ee_offset=True):
    """
    DHパラメータからEE位置を計算（ロボットローカル座標系）

    Args:
        joint_angles: 7関節の角度 [rad]
        include_ee_offset: EEオフセットを含めるか

    Returns:
        EE位置 (x, y, z) in ロボットローカル座標系
    """
    T = np.eye(4)

    for i, (params, theta) in enumerate(zip(DH_PARAMS, joint_angles)):
        a, d, alpha, theta_offset = params
        T_i = dh_transform(a, d, alpha, theta + theta_offset)
        T = T @ T_i

    # フランジ位置
    pos = T[:3, 3]

    if include_ee_offset:
        # EEオフセット（Z方向）を追加
        ee_offset = T[:3, :3] @ np.array([0, 0, FLANGE_TO_EE])
        pos = pos + ee_offset

    return pos


def transform_to_world(local_pos, base_pos, base_quat):
    """
    ロボットローカル座標系からワールド座標系へ変換

    壁設置時:
    - ロボットのローカル+Z → ワールド+X
    - ロボットのローカル+X → ワールド-Z (下向き)
    """
    R = quat_to_rotation_matrix(base_quat)
    world_pos = R @ local_pos + base_pos
    return world_pos


# ============================================================================
# ワークスペースサンプリング
# ============================================================================

def sample_workspace(base_pos, base_quat, n_samples_per_joint=6):
    """
    ワークスペースをサンプリングして到達可能点を計算

    Args:
        base_pos: ロボットベース位置 [x, y, z]
        base_quat: ベースクォータニオン [w, x, y, z]
        n_samples_per_joint: 各関節のサンプル数

    Returns:
        到達可能点のリスト [(x, y, z), ...]
    """
    points = []

    # 各関節のサンプル値を生成
    joint_samples = []
    for i, (low, high) in enumerate(JOINT_LIMITS):
        samples = np.linspace(low, high, n_samples_per_joint)
        joint_samples.append(samples)

    # 計算量を減らすため、一部の関節を粗くサンプリング
    # joint2, joint4, joint6 は制限が厳しいので細かく
    n_total = n_samples_per_joint ** 7
    print(f"  サンプリング開始: {n_samples_per_joint}^7 = {n_total:,} 点")

    count = 0
    for q1, q2, q3, q4, q5, q6, q7 in product(*joint_samples):
        joint_angles = [q1, q2, q3, q4, q5, q6, q7]

        # Forward Kinematics（ローカル座標系）
        local_pos = forward_kinematics(joint_angles)

        # ワールド座標系へ変換
        world_pos = transform_to_world(local_pos, base_pos, base_quat)

        points.append(world_pos)
        count += 1

        if count % 100000 == 0:
            print(f"    進捗: {count:,}/{n_total:,} ({100*count/n_total:.1f}%)")

    return np.array(points)


# ============================================================================
# 可視化
# ============================================================================

def plot_3d_workspace(left_points, right_points, save_path):
    """3Dワークスペースをプロット"""
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # サンプリング（点が多すぎる場合）
    max_points = 50000
    if len(left_points) > max_points:
        idx = np.random.choice(len(left_points), max_points, replace=False)
        left_plot = left_points[idx]
    else:
        left_plot = left_points

    if len(right_points) > max_points:
        idx = np.random.choice(len(right_points), max_points, replace=False)
        right_plot = right_points[idx]
    else:
        right_plot = right_points

    # 左アーム（青）
    ax.scatter(left_plot[:, 0], left_plot[:, 1], left_plot[:, 2],
               c='blue', alpha=0.1, s=1, label='Left Arm')

    # 右アーム（赤）
    ax.scatter(right_plot[:, 0], right_plot[:, 1], right_plot[:, 2],
               c='red', alpha=0.1, s=1, label='Right Arm')

    # ロボットベース位置
    ax.scatter(*LEFT_ARM_BASE, c='blue', s=100, marker='^', label='Left Base')
    ax.scatter(*RIGHT_ARM_BASE, c='red', s=100, marker='^', label='Right Base')

    # テーブル面（Z=0.75）
    table_x = np.linspace(-0.2, 0.8, 10)
    table_y = np.linspace(-0.5, 0.5, 10)
    table_X, table_Y = np.meshgrid(table_x, table_y)
    table_Z = np.ones_like(table_X) * 0.75
    ax.plot_surface(table_X, table_Y, table_Z, alpha=0.2, color='gray')

    # ケーブル位置候補
    for name, params in CABLE_CANDIDATES.items():
        if 'x_range' in params:
            x = np.linspace(params['x_range'][0], params['x_range'][1], 20)
            y = np.ones_like(x) * params['y']
            z = np.ones_like(x) * params['z']
        else:
            y = np.linspace(params['y_range'][0], params['y_range'][1], 20)
            x = np.ones_like(y) * params['x']
            z = np.ones_like(y) * params['z']
        ax.plot(x, y, z, linewidth=3, label=name)

    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title('Franka Panda Reachable Workspace (Wall-Mounted)')
    ax.legend(loc='upper left')

    # 視点調整
    ax.view_init(elev=20, azim=-60)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"  保存: {save_path}")
    plt.close()


def plot_xy_slices(left_points, right_points, z_heights, save_path):
    """特定Z高さでのXY断面をプロット"""
    fig, axes = plt.subplots(1, len(z_heights), figsize=(6*len(z_heights), 6))

    for ax, z_target in zip(axes, z_heights):
        # Z高さ付近の点を抽出
        left_mask = np.abs(left_points[:, 2] - z_target) < Z_SLICE_TOLERANCE
        right_mask = np.abs(right_points[:, 2] - z_target) < Z_SLICE_TOLERANCE

        left_slice = left_points[left_mask]
        right_slice = right_points[right_mask]

        # プロット
        if len(left_slice) > 0:
            ax.scatter(left_slice[:, 0], left_slice[:, 1],
                      c='blue', alpha=0.2, s=2, label='Left Arm')
        if len(right_slice) > 0:
            ax.scatter(right_slice[:, 0], right_slice[:, 1],
                      c='red', alpha=0.2, s=2, label='Right Arm')

        # 両アームの重なり（緑）
        if len(left_slice) > 0 and len(right_slice) > 0:
            # 簡易的な重なり検出（グリッド化）
            grid_res = 0.02  # 2cm グリッド
            left_grid = set()
            for p in left_slice:
                gx, gy = int(p[0]/grid_res), int(p[1]/grid_res)
                left_grid.add((gx, gy))

            overlap_points = []
            for p in right_slice:
                gx, gy = int(p[0]/grid_res), int(p[1]/grid_res)
                if (gx, gy) in left_grid:
                    overlap_points.append(p)

            if overlap_points:
                overlap = np.array(overlap_points)
                ax.scatter(overlap[:, 0], overlap[:, 1],
                          c='green', alpha=0.3, s=3, label='Both Arms')

        # ケーブル位置候補をオーバーレイ
        colors = ['purple', 'orange', 'cyan']
        for i, (name, params) in enumerate(CABLE_CANDIDATES.items()):
            if 'x_range' in params:
                x = np.linspace(params['x_range'][0], params['x_range'][1], 50)
                y = np.ones_like(x) * params['y']
            else:
                y = np.linspace(params['y_range'][0], params['y_range'][1], 50)
                x = np.ones_like(y) * params['x']
            ax.plot(x, y, linewidth=3, color=colors[i], label=name)

        # ロボットベース位置
        ax.scatter(LEFT_ARM_BASE[0], LEFT_ARM_BASE[1],
                  c='blue', s=100, marker='^', edgecolors='black', zorder=5)
        ax.scatter(RIGHT_ARM_BASE[0], RIGHT_ARM_BASE[1],
                  c='red', s=100, marker='^', edgecolors='black', zorder=5)

        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        ax.set_title(f'XY Slice at Z = {z_target:.3f}m (±{Z_SLICE_TOLERANCE*100:.0f}cm)')
        ax.legend(loc='upper left', fontsize=8)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.3, 0.9)
        ax.set_ylim(-0.6, 0.6)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"  保存: {save_path}")
    plt.close()


# ============================================================================
# 到達可能性判定
# ============================================================================

def check_reachability(points, target_x, target_y, target_z, tolerance=0.03):
    """特定の点が到達可能かチェック"""
    distances = np.sqrt(
        (points[:, 0] - target_x)**2 +
        (points[:, 1] - target_y)**2 +
        (points[:, 2] - target_z)**2
    )
    return np.min(distances) < tolerance


def analyze_cable_candidates(left_points, right_points):
    """各ケーブル位置候補の到達可能性を分析"""
    print("\n" + "="*60)
    print("ケーブル位置候補の到達可能性分析")
    print("="*60)

    results = {}

    for name, params in CABLE_CANDIDATES.items():
        print(f"\n【{name}】")

        z = params.get('z', 0.755)

        if 'x_range' in params:
            # X軸レイアウト
            x_range = params['x_range']
            y = params['y']

            # 左端（X最小）
            left_end_x = x_range[0]
            left_end_reachable = check_reachability(left_points, left_end_x, y, z)

            # 右端（X最大）
            right_end_x = x_range[1]
            right_end_reachable = check_reachability(right_points, right_end_x, y, z)

            print(f"  位置: X={x_range[0]:.2f}〜{x_range[1]:.2f}, Y={y:.2f}, Z={z:.3f}")
            print(f"  左端 (X={left_end_x:.2f}): {'✅ 到達可能' if left_end_reachable else '❌ 到達不可'} (左アーム)")
            print(f"  右端 (X={right_end_x:.2f}): {'✅ 到達可能' if right_end_reachable else '❌ 到達不可'} (右アーム)")

            # 中間点のチェック
            mid_x = (x_range[0] + x_range[1]) / 2
            mid_left = check_reachability(left_points, mid_x, y, z)
            mid_right = check_reachability(right_points, mid_x, y, z)
            print(f"  中央 (X={mid_x:.2f}): 左{'✅' if mid_left else '❌'} 右{'✅' if mid_right else '❌'}")

            results[name] = {
                'left_end': left_end_reachable,
                'right_end': right_end_reachable,
                'both_ends': left_end_reachable and right_end_reachable
            }

        else:
            # Y軸レイアウト
            x = params['x']
            y_range = params['y_range']

            # 左端（Y最小）
            left_end_y = y_range[0]
            left_end_reachable = check_reachability(left_points, x, left_end_y, z)

            # 右端（Y最大）
            right_end_y = y_range[1]
            right_end_reachable = check_reachability(right_points, x, right_end_y, z)

            print(f"  位置: X={x:.2f}, Y={y_range[0]:.2f}〜{y_range[1]:.2f}, Z={z:.3f}")
            print(f"  左端 (Y={left_end_y:.2f}): {'✅ 到達可能' if left_end_reachable else '❌ 到達不可'} (左アーム)")
            print(f"  右端 (Y={right_end_y:.2f}): {'✅ 到達可能' if right_end_reachable else '❌ 到達不可'} (右アーム)")

            results[name] = {
                'left_end': left_end_reachable,
                'right_end': right_end_reachable,
                'both_ends': left_end_reachable and right_end_reachable
            }

        # 総合判定
        if results[name]['both_ends']:
            print(f"  → ✅ この配置は両端とも到達可能！")
        else:
            print(f"  → ❌ この配置は一部到達不可")

    return results


def compute_bounds(points, name):
    """到達可能領域の境界を計算"""
    print(f"\n【{name}】到達可能領域:")
    print(f"  X: {points[:, 0].min():.3f} 〜 {points[:, 0].max():.3f} m")
    print(f"  Y: {points[:, 1].min():.3f} 〜 {points[:, 1].max():.3f} m")
    print(f"  Z: {points[:, 2].min():.3f} 〜 {points[:, 2].max():.3f} m")

    return {
        'x_min': points[:, 0].min(),
        'x_max': points[:, 0].max(),
        'y_min': points[:, 1].min(),
        'y_max': points[:, 1].max(),
        'z_min': points[:, 2].min(),
        'z_max': points[:, 2].max(),
    }


# ============================================================================
# メイン
# ============================================================================

def main():
    print("="*60)
    print("Franka Panda 壁設置時の可動範囲解析")
    print("="*60)

    # 出力ディレクトリ
    output_dir = "/home/rlrk/IsaacLab/data"
    os.makedirs(output_dir, exist_ok=True)

    # サンプル数（計算時間とのバランス）
    # 6^7 = 279,936 点 → 約1-2分
    n_samples = 6

    print(f"\n[1] 左アームのワークスペース計算...")
    print(f"  ベース位置: {LEFT_ARM_BASE}")
    left_points = sample_workspace(LEFT_ARM_BASE, WALL_MOUNT_QUAT, n_samples)
    left_bounds = compute_bounds(left_points, "左アーム")

    print(f"\n[2] 右アームのワークスペース計算...")
    print(f"  ベース位置: {RIGHT_ARM_BASE}")
    right_points = sample_workspace(RIGHT_ARM_BASE, WALL_MOUNT_QUAT, n_samples)
    right_bounds = compute_bounds(right_points, "右アーム")

    print(f"\n[3] 3Dプロット作成...")
    plot_3d_workspace(
        left_points, right_points,
        os.path.join(output_dir, "reachability_3d.png")
    )

    print(f"\n[4] XY断面プロット作成...")
    plot_xy_slices(
        left_points, right_points, Z_SLICE_HEIGHTS,
        os.path.join(output_dir, "reachability_xy_slices.png")
    )

    print(f"\n[5] ケーブル位置候補の到達可能性分析...")
    results = analyze_cable_candidates(left_points, right_points)

    # 推奨配置
    print("\n" + "="*60)
    print("推奨配置")
    print("="*60)

    for name, result in results.items():
        if result['both_ends']:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}")

    print("\n完了!")


if __name__ == "__main__":
    main()
