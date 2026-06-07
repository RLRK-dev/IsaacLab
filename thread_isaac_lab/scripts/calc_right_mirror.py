#!/usr/bin/env python3
"""
Franka Panda Y-mirror: compute RIGHT arm joints from LEFT arm confirmed joints.
Uses ACTUAL URDF joint origins (not DH parameters).

URDF: panda_independent_fingers.urdf
Joint origins (rpy, xyz) and axis from URDF:
  J1: rpy(0,0,0)       xyz(0, 0, 0.333)        axis(0,0,1)
  J2: rpy(-π/2,0,0)    xyz(0, 0, 0)             axis(0,0,1)
  J3: rpy(π/2,0,0)     xyz(0, -0.316, 0)        axis(0,0,1)
  J4: rpy(π/2,0,0)     xyz(0.0825, 0, 0)        axis(0,0,1)
  J5: rpy(-π/2,0,0)    xyz(-0.0825, 0.384, 0)   axis(0,0,1)
  J6: rpy(π/2,0,0)     xyz(0, 0, 0)             axis(0,0,1)
  J7: rpy(π/2,0,0)     xyz(0.088, 0, 0)         axis(0,0,1)
  J8(fixed): rpy(0,0,0) xyz(0, 0, 0.107)
  Hand(fixed): rpy(0, 0, -π/4) xyz(0, 0, 0)
"""

import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
import json, os

# URDF joint origin transforms
# Each entry: (rpy, xyz)
JOINT_ORIGINS = [
    ([0, 0, 0],              [0, 0, 0.333]),       # J1
    ([-np.pi/2, 0, 0],       [0, 0, 0]),           # J2
    ([np.pi/2, 0, 0],        [0, -0.316, 0]),      # J3
    ([np.pi/2, 0, 0],        [0.0825, 0, 0]),      # J4
    ([-np.pi/2, 0, 0],       [-0.0825, 0.384, 0]), # J5
    ([np.pi/2, 0, 0],        [0, 0, 0]),           # J6
    ([np.pi/2, 0, 0],        [0.088, 0, 0]),       # J7
]
# Fixed joints after J7
FIXED_ORIGINS = [
    ([0, 0, 0],              [0, 0, 0.107]),       # J8 (link8)
    ([0, 0, -np.pi/4],       [0, 0, 0]),           # hand_joint
]

# Joint limits from URDF
J_MIN = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
J_MAX = np.array([ 2.8973,  1.7628,  2.8973, -0.0698,  2.8973,  3.7525,  2.8973])


def rpy_to_matrix(rpy):
    """RPY (roll, pitch, yaw) → 3x3 rotation matrix. URDF convention: R = Rz(yaw) * Ry(pitch) * Rx(roll)."""
    return Rotation.from_euler('xyz', rpy).as_matrix()


def make_transform(R, t):
    """Create 4x4 homogeneous transform from 3x3 rotation and 3-vector translation."""
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def rot_z(theta):
    """Rotation about Z axis."""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def fk(joints):
    """Forward kinematics using URDF joint origins. Returns 4x4 transform of panda_hand in base frame."""
    T = np.eye(4)
    for i in range(7):
        rpy, xyz = JOINT_ORIGINS[i]
        T_origin = make_transform(rpy_to_matrix(rpy), xyz)
        T_rot = make_transform(rot_z(joints[i]), [0, 0, 0])
        T = T @ T_origin @ T_rot
    # Fixed joints
    for rpy, xyz in FIXED_ORIGINS:
        T_fixed = make_transform(rpy_to_matrix(rpy), xyz)
        T = T @ T_fixed
    return T


def rotmat_to_quat_wxyz(R):
    q_xyzw = Rotation.from_matrix(R).as_quat()
    return np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])


def mirror_pose_y(T):
    """Mirror 4x4 pose across Y=0 (XZ plane)."""
    M = np.diag([1.0, -1.0, 1.0])
    T_mirror = np.eye(4)
    T_mirror[:3, :3] = M @ T[:3, :3] @ M
    T_mirror[:3, 3] = M @ T[:3, 3]
    return T_mirror


def pose_error(joints, T_target):
    """Position + orientation error for IK, with joint-limit avoidance."""
    T = fk(joints)
    pos_err = np.linalg.norm(T[:3, 3] - T_target[:3, 3])
    R_err = T[:3, :3].T @ T_target[:3, :3]
    trace = np.clip(np.trace(R_err), -1.0, 3.0)
    angle = np.arccos(np.clip((trace - 1.0) / 2.0, -1.0, 1.0))
    # Joint-limit avoidance: penalize joints near limits
    margin = 0.15  # rad (~8.6 deg) desired margin
    limit_penalty = 0.0
    for i in range(7):
        range_i = J_MAX[i] - J_MIN[i]
        center_i = (J_MAX[i] + J_MIN[i]) / 2.0
        # Normalized distance from center: 0 at center, 1 at limit
        norm_dist = abs(joints[i] - center_i) / (range_i / 2.0)
        if norm_dist > 0.9:  # Only penalize when >90% toward limit
            limit_penalty += (norm_dist - 0.9) ** 2 * 500.0
    return pos_err * 1000.0 + angle * 50.0 + limit_penalty


def ik_solve(T_target, q_init, max_attempts=100):
    """Numerical IK with multiple seeds."""
    best_result = None
    best_cost = float('inf')

    for attempt in range(max_attempts):
        if attempt == 0:
            q0 = q_init.copy()
        elif attempt < 10:
            q0 = q_init + np.random.randn(7) * 0.3
        else:
            q0 = q_init + np.random.randn(7) * (0.3 + attempt * 0.02)
        q0 = np.clip(q0, J_MIN, J_MAX)

        result = minimize(
            pose_error, q0, args=(T_target,),
            method='L-BFGS-B',
            bounds=list(zip(J_MIN, J_MAX)),
            options={'maxiter': 10000, 'ftol': 1e-15, 'gtol': 1e-12},
        )

        if result.fun < best_cost:
            best_cost = result.fun
            best_result = result

        T_check = fk(best_result.x)
        pos_err_mm = np.linalg.norm(T_check[:3, 3] - T_target[:3, 3]) * 1000
        R_err = T_check[:3, :3].T @ T_target[:3, :3]
        ori_err_deg = np.degrees(np.arccos(np.clip((np.trace(R_err) - 1) / 2, -1, 1)))
        if pos_err_mm < 0.01 and ori_err_deg < 0.1:
            print(f"  Converged at attempt {attempt}: pos={pos_err_mm:.4f}mm, ori={ori_err_deg:.4f}deg")
            break

        if attempt % 20 == 0:
            print(f"  Attempt {attempt}: best pos={pos_err_mm:.4f}mm, ori={ori_err_deg:.4f}deg")

    return best_result


def world_ee(joints, base_pos, base_quat_wxyz):
    """Compute EE position in world frame given joints and robot base pose."""
    T_local = fk(joints)
    # Base rotation
    q_xyzw = [base_quat_wxyz[1], base_quat_wxyz[2], base_quat_wxyz[3], base_quat_wxyz[0]]
    R_base = Rotation.from_quat(q_xyzw).as_matrix()
    T_base = make_transform(R_base, base_pos)
    T_world = T_base @ T_local
    return T_world[:3, 3], rotmat_to_quat_wxyz(T_world[:3, :3])


def main():
    left_joints = np.array([0.650477, 0.698145, 0.100584, -1.909314, -2.356371, 1.924273, 1.914357])

    # FK for left arm (local frame)
    T_left = fk(left_joints)
    pos_left = T_left[:3, 3]
    quat_left = rotmat_to_quat_wxyz(T_left[:3, :3])

    print("=== LEFT ARM FK (local frame) ===")
    print(f"  Position: ({pos_left[0]:.6f}, {pos_left[1]:.6f}, {pos_left[2]:.6f})")
    print(f"  Quat(wxyz): ({quat_left[0]:.6f}, {quat_left[1]:.6f}, {quat_left[2]:.6f}, {quat_left[3]:.6f})")

    # Verify: compute world EE for left arm
    LEFT_BASE = (0.2467, -0.5, 1.265)
    RIGHT_BASE = (0.2467, 0.5, 1.265)
    BASE_QUAT = (0.7071, 0, 0.7071, 0)

    pos_world_left, quat_world_left = world_ee(left_joints, LEFT_BASE, BASE_QUAT)
    print(f"\n=== LEFT ARM WORLD EE ===")
    print(f"  Position: ({pos_world_left[0]:.6f}, {pos_world_left[1]:.6f}, {pos_world_left[2]:.6f})")
    print(f"  Expected: (~0.401, ~-0.105, ~0.764)")
    print(f"  Quat(wxyz): ({quat_world_left[0]:.6f}, {quat_world_left[1]:.6f}, {quat_world_left[2]:.6f}, {quat_world_left[3]:.6f})")

    # Also check simple mirror joints in world frame
    simple_mirror = left_joints.copy()
    simple_mirror[0] *= -1
    simple_mirror[2] *= -1
    simple_mirror[4] *= -1
    simple_mirror[6] *= -1
    pos_world_sm, quat_world_sm = world_ee(simple_mirror, RIGHT_BASE, BASE_QUAT)
    print(f"\n=== SIMPLE MIRROR WORLD EE (RIGHT base) ===")
    print(f"  Joints: [{', '.join(f'{j:.6f}' for j in simple_mirror)}]")
    print(f"  Position: ({pos_world_sm[0]:.6f}, {pos_world_sm[1]:.6f}, {pos_world_sm[2]:.6f})")
    print(f"  Expected: (~0.401, ~0.105, ~0.764)")

    # Mirror target in LOCAL frame
    T_right_target = mirror_pose_y(T_left)
    pos_right_local = T_right_target[:3, 3]
    quat_right_local = rotmat_to_quat_wxyz(T_right_target[:3, :3])

    print(f"\n=== MIRRORED TARGET (local frame) ===")
    print(f"  Position: ({pos_right_local[0]:.6f}, {pos_right_local[1]:.6f}, {pos_right_local[2]:.6f})")
    print(f"  Quat(wxyz): ({quat_right_local[0]:.6f}, {quat_right_local[1]:.6f}, {quat_right_local[2]:.6f}, {quat_right_local[3]:.6f})")

    # Verify mirrored target in world frame
    q_xyzw = [BASE_QUAT[1], BASE_QUAT[2], BASE_QUAT[3], BASE_QUAT[0]]
    R_base = Rotation.from_quat(q_xyzw).as_matrix()
    T_base_right = make_transform(R_base, RIGHT_BASE)
    T_world_target = T_base_right @ T_right_target
    print(f"  World target: ({T_world_target[0,3]:.6f}, {T_world_target[1,3]:.6f}, {T_world_target[2,3]:.6f})")

    # Numerical IK
    print(f"\n=== SOLVING IK FOR RIGHT ARM ===")
    # Try multiple seeds: simple mirror, left joints, random
    seeds = [
        simple_mirror.copy(),
        left_joints.copy(),
        np.zeros(7),
    ]

    np.random.seed(42)
    best_overall = None
    best_cost = float('inf')

    for seed_idx, seed in enumerate(seeds):
        seed = np.clip(seed, J_MIN, J_MAX)
        print(f"\n  --- Seed {seed_idx} ---")
        result = ik_solve(T_right_target, seed, max_attempts=50)
        if result.fun < best_cost:
            best_cost = result.fun
            best_overall = result

    right_joints = best_overall.x

    # Verify FK
    T_verify = fk(right_joints)
    pos_verify = T_verify[:3, 3]
    quat_verify = rotmat_to_quat_wxyz(T_verify[:3, :3])
    pos_err_mm = np.linalg.norm(pos_verify - pos_right_local) * 1000
    R_err = T_verify[:3, :3].T @ T_right_target[:3, :3]
    ori_err_deg = np.degrees(np.arccos(np.clip((np.trace(R_err) - 1) / 2, -1, 1)))

    # World frame verification
    pos_world_right, quat_world_right = world_ee(right_joints, RIGHT_BASE, BASE_QUAT)

    print(f"\n=== RIGHT ARM IK RESULT ===")
    print(f"  Joints: [{', '.join(f'{j:.6f}' for j in right_joints)}]")
    print(f"  Local  EE: ({pos_verify[0]:.6f}, {pos_verify[1]:.6f}, {pos_verify[2]:.6f})")
    print(f"  World  EE: ({pos_world_right[0]:.6f}, {pos_world_right[1]:.6f}, {pos_world_right[2]:.6f})")
    print(f"  World quat: ({quat_world_right[0]:.6f}, {quat_world_right[1]:.6f}, {quat_world_right[2]:.6f}, {quat_world_right[3]:.6f})")
    print(f"  FK pos error: {pos_err_mm:.4f} mm")
    print(f"  FK ori error: {ori_err_deg:.4f} deg")

    in_limits = np.all((right_joints >= J_MIN) & (right_joints <= J_MAX))
    print(f"  Within joint limits: {in_limits}")
    if not in_limits:
        for i in range(7):
            if right_joints[i] < J_MIN[i] or right_joints[i] > J_MAX[i]:
                print(f"    J{i}: {right_joints[i]:.6f} not in [{J_MIN[i]:.4f}, {J_MAX[i]:.4f}]")

    # Symmetry check
    print(f"\n=== SYMMETRY CHECK (world frame) ===")
    print(f"  Left  EE: X={pos_world_left[0]:.6f}, Y={pos_world_left[1]:.6f}, Z={pos_world_left[2]:.6f}")
    print(f"  Right EE: X={pos_world_right[0]:.6f}, Y={pos_world_right[1]:.6f}, Z={pos_world_right[2]:.6f}")
    mid_y = (pos_world_left[1] + pos_world_right[1]) / 2
    workspace_center_y = (LEFT_BASE[1] + RIGHT_BASE[1]) / 2
    print(f"  X diff: {abs(pos_world_left[0] - pos_world_right[0])*1000:.3f} mm")
    print(f"  Y midpoint: {mid_y:.6f} (workspace center: {workspace_center_y:.1f})")
    print(f"  Z diff: {abs(pos_world_left[2] - pos_world_right[2])*1000:.3f} mm")

    # Safety check
    z_world = pos_world_right[2]
    print(f"\n=== SAFETY CHECK ===")
    print(f"  World Z = {z_world:.4f} vs TABLE_HEIGHT = 0.75")
    print(f"  {'PASS' if z_world > 0.75 else 'FAIL'}: Z {'>' if z_world > 0.75 else '<'} 0.75")

    # Save
    output = {
        "left_joints": left_joints.tolist(),
        "left_world_ee": pos_world_left.tolist(),
        "right_joints": [round(j, 6) for j in right_joints.tolist()],
        "right_world_ee": pos_world_right.tolist(),
        "right_world_quat_wxyz": quat_world_right.tolist(),
        "fk_pos_err_mm": round(pos_err_mm, 4),
        "fk_ori_err_deg": round(ori_err_deg, 4),
        "within_joint_limits": bool(in_limits),
        "world_z_above_table": bool(z_world > 0.75),
        "task_config_line": f"CLIP_APPROACH_RIGHT_JOINTS = [{', '.join(f'{j:.6f}' for j in right_joints)}]",
    }
    out_path = "/home/rlrk/IsaacLab/data/calc_right_mirror.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {out_path}")
    print(f"\n=== PASTE INTO task_config.py ===")
    print(output["task_config_line"])


if __name__ == "__main__":
    main()
