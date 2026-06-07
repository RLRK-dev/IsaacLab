#!/usr/bin/env python3
"""Find the correct j7 for RIGHT arm to achieve HAND_DOWN orientation.
j0-j6 from simple mirror, sweep j7 to minimize world-frame orientation error to HAND_DOWN."""

import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import minimize_scalar

# URDF joint origins
JOINT_ORIGINS = [
    ([0, 0, 0],              [0, 0, 0.333]),
    ([-np.pi/2, 0, 0],       [0, 0, 0]),
    ([np.pi/2, 0, 0],        [0, -0.316, 0]),
    ([np.pi/2, 0, 0],        [0.0825, 0, 0]),
    ([-np.pi/2, 0, 0],       [-0.0825, 0.384, 0]),
    ([np.pi/2, 0, 0],        [0, 0, 0]),
    ([np.pi/2, 0, 0],        [0.088, 0, 0]),
]
FIXED_ORIGINS = [
    ([0, 0, 0],              [0, 0, 0.107]),
    ([0, 0, -np.pi/4],       [0, 0, 0]),
]

def rpy_to_matrix(rpy):
    return Rotation.from_euler('xyz', rpy).as_matrix()

def make_transform(R, t):
    T = np.eye(4); T[:3,:3] = R; T[:3,3] = t; return T

def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def fk(joints):
    T = np.eye(4)
    for i in range(7):
        rpy, xyz = JOINT_ORIGINS[i]
        T = T @ make_transform(rpy_to_matrix(rpy), xyz) @ make_transform(rot_z(joints[i]), [0,0,0])
    for rpy, xyz in FIXED_ORIGINS:
        T = T @ make_transform(rpy_to_matrix(rpy), xyz)
    return T

def world_transform(joints, base_pos, base_quat_wxyz):
    T_local = fk(joints)
    q = base_quat_wxyz
    R = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
    T_base = make_transform(R, base_pos)
    return T_base @ T_local

# Right arm mirror joints (j0-j6 from simple mirror)
RIGHT_J0_6 = [-0.650477, 0.698145, -0.100584, -1.909314, 2.356371, 1.924273]
RIGHT_BASE = (0.2467, 0.5, 1.265)
BASE_QUAT = (0.7071, 0, 0.7071, 0)

# HAND_DOWN target: (0, 0.7071, 0.7071, 0) wxyz
HAND_DOWN_R = Rotation.from_quat([0.7071, 0.7071, 0.0, 0.0]).as_matrix()  # xyzw

def ori_error(j7):
    joints = RIGHT_J0_6 + [j7]
    T = world_transform(joints, RIGHT_BASE, BASE_QUAT)
    R_err = T[:3,:3].T @ HAND_DOWN_R
    trace = np.clip(np.trace(R_err), -1, 3)
    return np.degrees(np.arccos(np.clip((trace - 1) / 2, -1, 1)))

# Sweep j7 over valid range [-2.8973, 2.8973]
print("=== j7 sweep for RIGHT arm ===")
j7_range = np.linspace(-2.8973, 2.8973, 1000)
errors = [ori_error(j7) for j7 in j7_range]
best_idx = np.argmin(errors)
best_j7_coarse = j7_range[best_idx]
print(f"Coarse best: j7={best_j7_coarse:.4f}, ori_err={errors[best_idx]:.4f} deg")

# Fine optimization
result = minimize_scalar(ori_error, bounds=(best_j7_coarse - 0.1, best_j7_coarse + 0.1), method='bounded')
best_j7 = result.x
print(f"Fine best:   j7={best_j7:.6f}, ori_err={result.fun:.6f} deg")

# Verify
joints_right = RIGHT_J0_6 + [best_j7]
T = world_transform(joints_right, RIGHT_BASE, BASE_QUAT)
pos = T[:3, 3]
q = Rotation.from_matrix(T[:3,:3]).as_quat()  # xyzw
q_wxyz = [q[3], q[0], q[1], q[2]]

print(f"\n=== RIGHT ARM with corrected j7 ===")
print(f"Joints: [{', '.join(f'{j:.6f}' for j in joints_right)}]")
print(f"World EE: ({pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f})")
print(f"World quat(wxyz): ({q_wxyz[0]:.6f}, {q_wxyz[1]:.6f}, {q_wxyz[2]:.6f}, {q_wxyz[3]:.6f})")
print(f"HAND_DOWN target: (0.0, 0.7071, 0.7071, 0.0)")
print(f"Ori error: {result.fun:.4f} deg")

# Also verify LEFT arm for comparison
LEFT_JOINTS = [0.650477, 0.698145, 0.100584, -1.909314, -2.356371, 1.924273, 1.914357]
T_left = world_transform(LEFT_JOINTS, (0.2467, -0.5, 1.265), BASE_QUAT)
pos_left = T_left[:3, 3]
q_left = Rotation.from_matrix(T_left[:3,:3]).as_quat()
q_left_wxyz = [q_left[3], q_left[0], q_left[1], q_left[2]]
R_err_left = T_left[:3,:3].T @ HAND_DOWN_R
err_left = np.degrees(np.arccos(np.clip((np.trace(R_err_left) - 1) / 2, -1, 1)))
print(f"\n=== LEFT ARM (reference) ===")
print(f"World EE: ({pos_left[0]:.6f}, {pos_left[1]:.6f}, {pos_left[2]:.6f})")
print(f"World quat(wxyz): ({q_left_wxyz[0]:.6f}, {q_left_wxyz[1]:.6f}, {q_left_wxyz[2]:.6f}, {q_left_wxyz[3]:.6f})")
print(f"Ori error to HAND_DOWN: {err_left:.4f} deg")

# Check j7 is within limits
print(f"\nj7 = {best_j7:.6f} (limits: [-2.8973, 2.8973])")
print(f"Within limits: {-2.8973 <= best_j7 <= 2.8973}")

print(f"\n=== PASTE INTO task_config.py ===")
print(f"CLIP_APPROACH_RIGHT_JOINTS = [{', '.join(f'{j:.6f}' for j in joints_right)}]")
