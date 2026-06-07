#!/usr/bin/env python3
"""
Calculate correct camera quaternions for dual_arm_cfg.py
Based on finding: world convention uses +X as forward
"""
import numpy as np
from scipy.spatial.transform import Rotation as R

def look_at_euler(cam_pos, target):
    """
    Calculate Euler angles (roll, pitch, yaw) for camera to look at target
    Assuming world convention where +X is forward
    """
    dx = target[0] - cam_pos[0]
    dy = target[1] - cam_pos[1]
    dz = target[2] - cam_pos[2]

    # Yaw: rotation around Z to align +X with target direction (in XY plane)
    yaw = np.degrees(np.arctan2(dy, dx))

    # Horizontal distance
    dist_xy = np.sqrt(dx**2 + dy**2)

    # Pitch: rotation around Y (after yaw) to look down/up
    pitch = np.degrees(np.arctan2(-dz, dist_xy))  # negative because positive pitch looks up

    roll = 0

    return roll, pitch, yaw

def euler_to_quat_wxyz(roll, pitch, yaw):
    """Convert Euler angles (degrees) to quaternion (w, x, y, z)"""
    rot = R.from_euler('xyz', [roll, pitch, yaw], degrees=True)
    q = rot.as_quat()  # [x, y, z, w]
    w, x, y, z = q[3], q[0], q[1], q[2]
    if w < 0:
        w, x, y, z = -w, -x, -y, -z
    return (w, x, y, z)

# Target
TARGET = (0.4, 0.0, 0.85)

# Camera positions
cameras = {
    'front_left': (0.6, -0.25, 1.1),
    'front_right': (0.6, 0.25, 1.1),
    'back': (0.0, 0.0, 1.1),
    'overhead': (0.4, 0.0, 1.6),
}

print("=" * 70)
print("CORRECT CAMERA QUATERNIONS FOR dual_arm_cfg.py")
print("=" * 70)
print(f"\nTarget: {TARGET}")
print(f"Convention: world (camera +X is forward)")
print()

for name, pos in cameras.items():
    roll, pitch, yaw = look_at_euler(pos, TARGET)
    quat = euler_to_quat_wxyz(roll, pitch, yaw)

    print(f"\n{name}:")
    print(f"  Position: {pos}")
    print(f"  Euler (roll, pitch, yaw): ({roll:.1f}°, {pitch:.1f}°, {yaw:.1f}°)")
    print(f"  Quaternion (w, x, y, z): ({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f})")

print("\n" + "=" * 70)
print("COPY TO dual_arm_cfg.py:")
print("=" * 70)

for name, pos in cameras.items():
    roll, pitch, yaw = look_at_euler(pos, TARGET)
    quat = euler_to_quat_wxyz(roll, pitch, yaw)

    print(f"""
# {name.replace('_', ' ').title()} Camera
offset: CameraCfg.OffsetCfg = CameraCfg.OffsetCfg(
    pos={pos},
    rot=({quat[0]:.4f}, {quat[1]:.4f}, {quat[2]:.4f}, {quat[3]:.4f}),
    convention="world",
)""")
