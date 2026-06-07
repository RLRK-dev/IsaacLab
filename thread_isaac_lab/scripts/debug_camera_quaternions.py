#!/usr/bin/env python3
"""
カメラ四元数の正確な計算
Isaac Lab: カメラ+Y軸が視線方向
"""
import numpy as np
from scipy.spatial.transform import Rotation as R

def look_at_quaternion(camera_pos, target_pos, up=(0, 0, 1)):
    """
    カメラ位置からターゲットを見る四元数を計算
    Isaac Lab: +Y軸がカメラの視線方向

    Returns: (w, x, y, z) quaternion
    """
    camera_pos = np.array(camera_pos)
    target_pos = np.array(target_pos)
    up = np.array(up)

    # 視線方向（正規化）
    forward = target_pos - camera_pos
    forward = forward / np.linalg.norm(forward)

    # カメラのローカル軸を計算
    # +Y = forward (視線方向)
    # +X = right
    # +Z = up (カメラの上方向)

    # rightベクトル = forward × up
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        # forward と up が平行の場合（真下を見る場合など）
        # 適当なrightを選ぶ
        right = np.array([1, 0, 0])
    right = right / np.linalg.norm(right)

    # 真のupベクトル = right × forward
    camera_up = np.cross(right, forward)
    camera_up = camera_up / np.linalg.norm(camera_up)

    # 回転行列を構築（列がローカル軸）
    # カメラ座標系: +X=right, +Y=forward, +Z=up
    rotation_matrix = np.column_stack([right, forward, camera_up])

    # 行列から四元数へ
    rot = R.from_matrix(rotation_matrix)
    quat = rot.as_quat()  # [x, y, z, w] scipy形式

    # (w, x, y, z)形式に変換
    w, x, y, z = quat[3], quat[0], quat[1], quat[2]

    # wを正に正規化
    if w < 0:
        w, x, y, z = -w, -x, -y, -z

    return (w, x, y, z)


def verify_quaternion(quat, camera_pos, target_pos):
    """四元数が正しくターゲットを向いているか検証"""
    # scipy形式に変換
    w, x, y, z = quat
    rot = R.from_quat([x, y, z, w])

    # +Y軸を回転
    y_axis = np.array([0, 1, 0])
    forward = rot.apply(y_axis)

    # 期待される方向
    expected = np.array(target_pos) - np.array(camera_pos)
    expected = expected / np.linalg.norm(expected)

    # 内積（1に近いほど正確）
    dot = np.dot(forward, expected)

    return dot, forward


print("=" * 60)
print("カメラ四元数の計算")
print("=" * 60)
print()

# ターゲット: テーブル中心上
target = (0.4, 0.0, 0.85)
print(f"ターゲット: {target}")
print()

# 4カメラの位置
cameras = {
    'front_left': (0.6, -0.25, 1.1),
    'front_right': (0.6, 0.25, 1.1),
    'back': (0.0, 0.0, 1.1),
    'overhead': (0.4, 0.0, 1.6),
}

print("計算結果:")
print("-" * 60)

for name, pos in cameras.items():
    quat = look_at_quaternion(pos, target)
    dot, forward = verify_quaternion(quat, pos, target)

    print(f"\n{name}:")
    print(f"  位置: {pos}")
    print(f"  四元数 (w,x,y,z): ({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f})")
    print(f"  検証: dot={dot:.4f} (1.0=完璧)")
    print(f"  視線方向: ({forward[0]:.3f}, {forward[1]:.3f}, {forward[2]:.3f})")

    # 期待される視線方向
    expected = np.array(target) - np.array(pos)
    expected = expected / np.linalg.norm(expected)
    print(f"  期待方向: ({expected[0]:.3f}, {expected[1]:.3f}, {expected[2]:.3f})")

print()
print("=" * 60)
print("dual_arm_cfg.py にコピーする形式:")
print("=" * 60)

for name, pos in cameras.items():
    quat = look_at_quaternion(pos, target)
    print(f"\n# {name}")
    print(f"pos={pos},")
    print(f"rot=({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f}),")
