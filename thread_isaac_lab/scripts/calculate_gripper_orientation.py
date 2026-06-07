"""
壁設置ロボット用のグリッパー姿勢を計算

問題:
- ロボットベースはY軸+90°回転（壁設置）
- グリッパーをワールド座標系で下向き(-Z)にしたい
- 指がケーブル（Y軸方向に配置）を挟めるようにしたい

Isaac Sim座標系:
- +X: 前方
- +Y: 左
- +Z: 上
"""

from scipy.spatial.transform import Rotation as R
import numpy as np

print("=" * 60)
print("壁設置ロボット用グリッパー姿勢の計算")
print("=" * 60)

# ロボットベースの回転（Y軸+90°）
robot_base_rot = R.from_euler('y', 90, degrees=True)
print(f"\nロボットベース回転 (Y+90°):")
print(f"  quat (xyzw): {robot_base_rot.as_quat()}")

# Pandaグリッパーのデフォルト姿勢
# - グリッパーはアームの先端から+Z方向（ローカル）を向いている
# - 指の開閉方向はローカルY軸

print("\n" + "-" * 60)
print("目標: グリッパーをワールド-Z方向（下向き）に向ける")
print("-" * 60)

# 方法1: ワールド座標系で直接指定
# グリッパーを下向きにする = X軸周りに180°回転
gripper_down_world = R.from_euler('x', 180, degrees=True)

# 指をY軸方向に向ける（ケーブルがY軸に沿っている場合）
# Z軸回転なし
final_rot_method1 = gripper_down_world
quat_xyzw = final_rot_method1.as_quat()
quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
print(f"\n方法1: X軸180°のみ")
print(f"  quat (wxyz): [{quat_wxyz[0]:.4f}, {quat_wxyz[1]:.4f}, {quat_wxyz[2]:.4f}, {quat_wxyz[3]:.4f}]")
print(f"  Euler (xyz, deg): {final_rot_method1.as_euler('xyz', degrees=True)}")

# 方法2: X軸180° + Z軸-90°（指をX軸方向に）
gripper_down = R.from_euler('x', 180, degrees=True)
finger_align = R.from_euler('z', -90, degrees=True)
final_rot_method2 = gripper_down * finger_align
quat_xyzw = final_rot_method2.as_quat()
quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
print(f"\n方法2: X軸180° + Z軸-90°（現在の設定）")
print(f"  quat (wxyz): [{quat_wxyz[0]:.4f}, {quat_wxyz[1]:.4f}, {quat_wxyz[2]:.4f}, {quat_wxyz[3]:.4f}]")
print(f"  Euler (xyz, deg): {final_rot_method2.as_euler('xyz', degrees=True)}")

# 方法3: 壁設置を考慮した計算
# 壁設置ロボットでは、ベースのローカルZ軸がワールド+X方向を向いている
# グリッパーをワールド-Z方向に向けるには...
print(f"\n方法3: 壁設置ロボット用の補正計算")

# ワールド座標系での目標姿勢（グリッパーが下向き、指がY軸方向）
# グリッパーの先端（ローカル+Z）をワールド-Z方向に向ける
# これはX軸周りに180°回転
target_world = R.from_euler('x', 180, degrees=True)

# ただし、IKコントローラはワールド座標系で目標姿勢を受け取るので、
# ロボットベースの回転は関係ない（IKが内部で処理する）
print(f"  IKターゲット（ワールド座標系）: X軸180°回転")
quat_xyzw = target_world.as_quat()
quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
print(f"  quat (wxyz): [{quat_wxyz[0]:.4f}, {quat_wxyz[1]:.4f}, {quat_wxyz[2]:.4f}, {quat_wxyz[3]:.4f}]")

# 方法4: ケーブルがX軸方向に配置されている場合
print(f"\n方法4: ケーブルがX軸方向の場合（Z軸-90°追加）")
target_x_cable = R.from_euler('xz', [180, -90], degrees=True)
quat_xyzw = target_x_cable.as_quat()
quat_wxyz = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]
print(f"  quat (wxyz): [{quat_wxyz[0]:.4f}, {quat_wxyz[1]:.4f}, {quat_wxyz[2]:.4f}, {quat_wxyz[3]:.4f}]")

print("\n" + "=" * 60)
print("結論")
print("=" * 60)
print("""
ケーブルの配置方向に応じて選択:
- ケーブルがY軸方向 → 方法1 (X軸180°のみ)
- ケーブルがX軸方向 → 方法4 (X軸180° + Z軸-90°)

現在のケーブル位置から判断:
  Cable: X=0.225, Y=-0.05
  ケーブルセグメントはY方向に並んでいる可能性が高い
  
推奨: 方法1（X軸180°のみ）をまず試す
""")

# 最終的な推奨値を出力
print("\n" + "=" * 60)
print("collect_goal_images.py への推奨修正")
print("=" * 60)
print("""
# 変更前（現在）
base_rot = R.from_euler('x', 180, degrees=True)
z_rot = R.from_euler('z', -90, degrees=True)
final_rot = base_rot * z_rot

# 変更後（推奨）
# まずシンプルに下向きのみで試す
final_rot = R.from_euler('x', 180, degrees=True)

# もし指の向きが合わない場合はZ軸回転を調整
# final_rot = R.from_euler('xz', [180, -90], degrees=True)  # 指をX軸方向
# final_rot = R.from_euler('xz', [180, 90], degrees=True)   # 指を-X軸方向
""")
