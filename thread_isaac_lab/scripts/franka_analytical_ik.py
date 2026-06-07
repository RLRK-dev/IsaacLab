#!/usr/bin/env python3
"""
Analytical Franka Panda Inverse Kinematics

Python implementation of He & Liu's analytical IK solution.
Original C++: https://github.com/ffall007/franka_analytical_ik

Reference:
    He, Y., & Liu, S. (2020). Analytical inverse kinematics for Franka Emika Panda
    - a geometrical approach.

Key features:
    - q7 (joint 7) as redundant parameter
    - Returns up to 4 solutions
    - Exact closed-form solution (no iteration)
    - Much faster than numerical IK
"""

import json
import subprocess
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

from thread_isaac_lab.configs.task_config import (
    GRIPPER_DOWN_QUAT_WXYZ,
    ROBOT_BASE_QUAT_WXYZ,
    GEOFIK_RUNNER_PATH,
    GEOFIK_Q7_MIN,
    GEOFIK_Q7_MAX,
    GEOFIK_Q7_STEPS,
)

# ============================================================
# Franka Panda Kinematics Constants
# ============================================================

# DH Parameters
D1 = 0.3330
D3 = 0.3160
D5 = 0.3840
D7E = 0.2104  # Flange to EE (includes Franka hand)
A4 = 0.0825
A7 = 0.0880

# Derived constants
LL24 = A4**2 + D3**2  # 0.10666225
LL46 = A4**2 + D5**2  # 0.15426225
L24 = np.sqrt(LL24)   # 0.326591870689
L46 = np.sqrt(LL46)   # 0.392762332715

THETA_H46 = np.arctan2(D5, A4)     # 1.35916951803
THETA_342 = np.arctan2(D3, A4)     # 1.31542071191
THETA_46H = np.arctan2(A4, D5)     # 0.211626808766

# Joint limits (radians)
Q_MIN = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
Q_MAX = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])


@dataclass
class IKSolution:
    """Single IK solution"""
    joints: np.ndarray  # 7 joint angles in radians
    valid: bool
    margin_deg: float  # Minimum margin from joint limits


def compute_joint_margin(joints: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Compute margin from joint limits for each joint.

    Returns:
        min_margin_deg: Minimum margin across all joints (degrees)
        margins_deg: Per-joint margins (degrees)
    """
    margins = np.minimum(
        np.abs(joints - Q_MIN),
        np.abs(Q_MAX - joints)
    )
    margins_deg = np.degrees(margins)
    return float(np.min(margins_deg)), margins_deg


def forward_kinematics(joints: np.ndarray) -> np.ndarray:
    """
    Compute forward kinematics for Franka Panda.

    Uses Modified DH convention matching Franka official documentation.

    Args:
        joints: 7 joint angles in radians

    Returns:
        T: 4x4 transformation matrix from base to EE
    """
    # Modified DH transformation matrix
    # Reference: Franka official documentation, Peter Corke RTB
    def mdh_matrix(a, d, alpha, theta):
        """Modified DH transformation matrix."""
        ct, st = np.cos(theta), np.sin(theta)
        ca, sa = np.cos(alpha), np.sin(alpha)
        return np.array([
            [ct,           -st,          0,       a],
            [st * ca,      ct * ca,     -sa,     -sa * d],
            [st * sa,      ct * sa,      ca,      ca * d],
            [0,            0,            0,       1]
        ])

    # Franka DH parameters (modified DH convention)
    # Reference: He & Liu analytical IK paper
    # D7E = 0.2104 = 0.107 (flange) + 0.1034 (EE offset) - 0.088 (a7 already in joint 7)
    # Note: No -45deg rotation to match IK solver's EE frame definition
    # [a, d, alpha, theta]
    dh_params = [
        [0,      0.333,  0,        joints[0]],
        [0,      0,     -np.pi/2,  joints[1]],
        [0,      0.316,  np.pi/2,  joints[2]],
        [0.0825, 0,      np.pi/2,  joints[3]],
        [-0.0825, 0.384, -np.pi/2, joints[4]],
        [0,      0,      np.pi/2,  joints[5]],
        [0.088,  0,      np.pi/2,  joints[6]],
        [0,      D7E,    0,        0],           # EE frame (D7E = 0.2104)
    ]

    T = np.eye(4)
    for a, d, alpha, theta in dh_params:
        T = T @ mdh_matrix(a, d, alpha, theta)

    return T


def quat_to_rot_matrix(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    n = np.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    if n == 0:
        return np.eye(3)
    qw, qx, qy, qz = qw / n, qx / n, qy / n, qz / n
    return np.array([
        [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw),     2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw),     1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw),     2 * (qy * qz + qx * qw),     1 - 2 * (qx * qx + qy * qy)],
    ])


def geofik_solutions_with_base(
    target_pos: np.ndarray,
    target_quat: np.ndarray,
    base_pos: np.ndarray,
    base_quat: np.ndarray,
    arm: Optional[str] = None,
    runner_path: str = GEOFIK_RUNNER_PATH,
    q7_min: float = GEOFIK_Q7_MIN,
    q7_max: float = GEOFIK_Q7_MAX,
    q7_steps: int = GEOFIK_Q7_STEPS,
) -> List[IKSolution]:
    """Call GeoFIK runner (stdin/stdout JSON) and return IKSolution list."""
    if not runner_path:
        return []

    R_target = quat_to_rot_matrix(*target_quat)
    payload = {
        "position": target_pos.tolist(),
        "rotation_matrix": R_target.reshape(-1).tolist(),
        "base_position": base_pos.tolist(),
        "base_quat": base_quat.tolist(),
        "method": "q7",
        "q7_min": q7_min,
        "q7_max": q7_max,
        "q7_steps": int(q7_steps),
    }
    if arm:
        payload["arm"] = arm

    try:
        print(
            "[GeoFIK DEBUG] payload:",
            json.dumps(
                {
                    "position": payload["position"],
                    "rotation_matrix": payload["rotation_matrix"],
                    "base_position": payload["base_position"],
                    "base_quat": payload["base_quat"],
                    "method": payload["method"],
                    "q7_min": payload["q7_min"],
                    "q7_max": payload["q7_max"],
                    "q7_steps": payload["q7_steps"],
                    "arm": payload.get("arm"),
                }
            ),
        )
        proc = subprocess.run(
            [runner_path],
            input=json.dumps(payload).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=2.0,
        )
    except Exception:
        print("[GeoFIK DEBUG] runner exception")
        return []
    if proc.returncode != 0:
        print(
            "[GeoFIK DEBUG] runner failed:",
            f"returncode={proc.returncode}",
            f"stderr={proc.stderr.decode('utf-8', errors='ignore')[:400]}",
        )
        return []
    try:
        out = json.loads(proc.stdout.decode("utf-8"))
    except json.JSONDecodeError:
        print(
            "[GeoFIK DEBUG] JSON decode failed:",
            proc.stdout.decode("utf-8", errors="ignore")[:400],
        )
        return []

    sols = []
    for q in out.get("solutions", []):
        joints = np.array(q, dtype=float)
        margin, _ = compute_joint_margin(joints)
        sols.append(IKSolution(joints=joints, valid=True, margin_deg=margin))
    print("[GeoFIK DEBUG] num_solutions:", len(sols))
    return sols


def franka_IK_EE(O_T_EE: np.ndarray, q7: float,
                 q_actual: Optional[np.ndarray] = None) -> List[IKSolution]:
    """
    Analytical inverse kinematics for Franka Panda.

    Args:
        O_T_EE: 4x4 transformation matrix from base to end-effector
        q7: Value for joint 7 (redundant parameter)
        q_actual: Current joint configuration (for singularity handling)

    Returns:
        List of up to 4 IKSolution objects
    """
    if q_actual is None:
        q_actual = np.array([0, 0, 0, -np.pi/2, 0, np.pi/2, 0])

    solutions = []

    # Check q7 limits
    if q7 <= Q_MIN[6] or q7 >= Q_MAX[6]:
        return solutions

    # Extract rotation and position from transformation matrix
    R_EE = O_T_EE[:3, :3]
    z_EE = O_T_EE[:3, 2]
    p_EE = O_T_EE[:3, 3]

    # Compute p_7 (joint 7 position)
    p_7 = p_EE - D7E * z_EE

    # Compute x_6 direction
    x_EE_6 = np.array([np.cos(q7 - np.pi/4), -np.sin(q7 - np.pi/4), 0.0])
    x_6 = R_EE @ x_EE_6
    x_6 = x_6 / np.linalg.norm(x_6)

    # Compute p_6 (joint 6 position)
    p_6 = p_7 - A7 * x_6

    # Compute q4
    p_2 = np.array([0.0, 0.0, D1])
    V26 = p_6 - p_2

    LL26 = np.dot(V26, V26)
    L26 = np.sqrt(LL26)

    # Check triangle inequality
    if L24 + L46 < L26 or L24 + L26 < L46 or L26 + L46 < L24:
        return solutions

    theta246 = np.arccos((LL24 + LL46 - LL26) / (2.0 * L24 * L46))
    q4 = theta246 + THETA_H46 + THETA_342 - 2.0 * np.pi

    if q4 <= Q_MIN[3] or q4 >= Q_MAX[3]:
        return solutions

    # Compute q6 candidates
    theta462 = np.arccos((LL26 + LL46 - LL24) / (2.0 * L26 * L46))
    theta26H = THETA_46H + theta462
    D26 = -L26 * np.cos(theta26H)

    Z_6 = np.cross(z_EE, x_6)
    Y_6 = np.cross(Z_6, x_6)

    R_6 = np.column_stack([
        x_6,
        Y_6 / np.linalg.norm(Y_6),
        Z_6 / np.linalg.norm(Z_6)
    ])

    V_6_62 = R_6.T @ (-V26)

    Phi6 = np.arctan2(V_6_62[1], V_6_62[0])
    denom = np.sqrt(V_6_62[0]**2 + V_6_62[1]**2)
    if denom < 1e-10:
        return solutions

    sin_arg = D26 / denom
    if abs(sin_arg) > 1.0:
        return solutions
    Theta6 = np.arcsin(sin_arg)

    q6_candidates = [
        np.pi - Theta6 - Phi6,  # Case 0
        Theta6 - Phi6,          # Case 1
    ]

    # Adjust q6 to be within limits
    for i in range(2):
        if q6_candidates[i] <= Q_MIN[5]:
            q6_candidates[i] += 2.0 * np.pi
        elif q6_candidates[i] >= Q_MAX[5]:
            q6_candidates[i] -= 2.0 * np.pi

    # For each q6 candidate, compute remaining joints
    thetaP26 = 3.0 * np.pi / 2 - theta462 - theta246 - THETA_342
    thetaP = np.pi - thetaP26 - theta26H
    LP6 = L26 * np.sin(thetaP26) / np.sin(thetaP)

    for q6_idx, q6 in enumerate(q6_candidates):
        if q6 <= Q_MIN[5] or q6 >= Q_MAX[5]:
            continue

        # Compute z_5 direction
        z_6_5 = np.array([np.sin(q6), np.cos(q6), 0.0])
        z_5 = R_6 @ z_6_5

        # Compute V2P
        V2P = p_6 - LP6 * z_5 - p_2
        L2P = np.linalg.norm(V2P)

        # Compute q1, q2 candidates
        if abs(V2P[2] / L2P) > 0.999:
            # Singularity case
            q1_candidates = [q_actual[0]]
            q2_candidates = [0.0]
        else:
            q1_base = np.arctan2(V2P[1], V2P[0])
            q2_base = np.arccos(V2P[2] / L2P)

            q1_candidates = [q1_base, q1_base + np.pi if q1_base < 0 else q1_base - np.pi]
            q2_candidates = [q2_base, -q2_base]

        for q1_idx in range(len(q1_candidates)):
            q1 = q1_candidates[q1_idx]
            q2 = q2_candidates[min(q1_idx, len(q2_candidates)-1)]

            # Check joint limits
            if q1 <= Q_MIN[0] or q1 >= Q_MAX[0]:
                continue
            if q2 <= Q_MIN[1] or q2 >= Q_MAX[1]:
                continue

            # Compute q3
            z_3 = V2P / L2P
            Y_3 = -np.cross(V26, V2P)
            if np.linalg.norm(Y_3) < 1e-10:
                continue
            y_3 = Y_3 / np.linalg.norm(Y_3)
            x_3 = np.cross(y_3, z_3)

            c1, s1 = np.cos(q1), np.sin(q1)
            R_1 = np.array([
                [c1, -s1, 0],
                [s1, c1, 0],
                [0, 0, 1]
            ])

            c2, s2 = np.cos(q2), np.sin(q2)
            R_1_2 = np.array([
                [c2, -s2, 0],
                [0, 0, 1],
                [-s2, -c2, 0]
            ])

            R_2 = R_1 @ R_1_2
            x_2_3 = R_2.T @ x_3
            q3 = np.arctan2(x_2_3[2], x_2_3[0])

            if q3 <= Q_MIN[2] or q3 >= Q_MAX[2]:
                continue

            # Compute q5
            VH4 = p_2 + D3 * z_3 + A4 * x_3 - p_6 + D5 * z_5

            c6, s6 = np.cos(q6), np.sin(q6)
            R_5_6 = np.array([
                [c6, -s6, 0],
                [0, 0, -1],
                [s6, c6, 0]
            ])
            R_5 = R_6 @ R_5_6.T
            V_5_H4 = R_5.T @ VH4

            q5 = -np.arctan2(V_5_H4[1], V_5_H4[0])

            if q5 <= Q_MIN[4] or q5 >= Q_MAX[4]:
                continue

            # Valid solution found
            joints = np.array([q1, q2, q3, q4, q5, q6, q7])
            margin, _ = compute_joint_margin(joints)

            solutions.append(IKSolution(
                joints=joints,
                valid=True,
                margin_deg=margin
            ))

    return solutions


def franka_IK_EE_with_base(target_pos: np.ndarray, target_quat: np.ndarray,
                           base_pos: np.ndarray, base_quat: np.ndarray,
                           q7: float = 0.785,
                           q_actual: Optional[np.ndarray] = None) -> List[IKSolution]:
    """
    Analytical IK with robot base transformation.

    Args:
        target_pos: Target EE position in world frame (3,)
        target_quat: Target EE orientation as quaternion (w,x,y,z)
        base_pos: Robot base position in world frame (3,)
        base_quat: Robot base orientation as quaternion (w,x,y,z)
        q7: Value for joint 7 (redundant parameter)
        q_actual: Current joint configuration

    Returns:
        List of IKSolution objects
    """
    from scipy.spatial.transform import Rotation as R

    # Convert quaternions to rotation matrices
    # Note: scipy uses (x,y,z,w) format
    R_base = R.from_quat([base_quat[1], base_quat[2], base_quat[3], base_quat[0]]).as_matrix()
    R_target = R.from_quat([target_quat[1], target_quat[2], target_quat[3], target_quat[0]]).as_matrix()

    # Build transformation matrices
    T_base = np.eye(4)
    T_base[:3, :3] = R_base
    T_base[:3, 3] = base_pos

    T_target_world = np.eye(4)
    T_target_world[:3, :3] = R_target
    T_target_world[:3, 3] = target_pos

    # Transform target to robot base frame
    T_base_inv = np.eye(4)
    T_base_inv[:3, :3] = R_base.T
    T_base_inv[:3, 3] = -R_base.T @ base_pos

    O_T_EE = T_base_inv @ T_target_world

    return franka_IK_EE(O_T_EE, q7, q_actual)


def solve_ik_best(target_pos: np.ndarray, base_pos: np.ndarray,
                  base_quat: np.ndarray,
                  target_quat: Optional[np.ndarray] = None,
                  q7_range: Tuple[float, float] = (-2.8, 2.8),
                  q7_steps: int = 20) -> Tuple[bool, Optional[np.ndarray], float]:
    """
    Find best IK solution by searching over q7.

    Args:
        target_pos: Target EE position in world frame
        base_pos: Robot base position
        base_quat: Robot base orientation (w,x,y,z)
        target_quat: Target EE orientation (w,x,y,z), default: pointing down (-Z)
        q7_range: Range for q7 search
        q7_steps: Number of q7 values to try

    Returns:
        success: Whether a valid solution was found
        joints: Best joint angles (7,) or None
        margin_deg: Joint margin in degrees
    """
    if target_quat is None:
        # Gripper down, fingers open in X direction (X180° + Z90°)
        target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)  # (w,x,y,z) from task_config

    best_solution = None
    best_margin = -1.0

    for q7 in np.linspace(q7_range[0], q7_range[1], q7_steps):
        solutions = franka_IK_EE_with_base(
            target_pos, target_quat, base_pos, base_quat, q7
        )

        for sol in solutions:
            if sol.valid and sol.margin_deg > best_margin:
                best_margin = sol.margin_deg
                best_solution = sol.joints.copy()

    if best_solution is not None:
        return True, best_solution, best_margin
    else:
        return False, None, 0.0


def solve_ik_best_near_current(
    target_pos: np.ndarray,
    base_pos: np.ndarray,
    base_quat: np.ndarray,
    current_joints: np.ndarray,
    target_quat: Optional[np.ndarray] = None,
    q7_range: Tuple[float, float] = (-2.8, 2.8),
    q7_steps: int = 20,
    min_margin_deg: float = 5.0,
    j3_min_deg: Optional[float] = None,
    j3_max_deg: Optional[float] = None,
    max_joint_change_deg: Optional[float] = None,
    use_geofik: bool = False,
    arm: Optional[str] = None
) -> Tuple[bool, Optional[np.ndarray], float, float]:
    """
    Find best IK solution preferring configurations near current joints.

    H080: Instead of maximizing margin, minimize distance from current joints
    while maintaining minimum margin threshold.

    H115: Added J3 constraint to prevent elbow boundary issues.
          Added max_joint_change_deg to prevent IK flip.

    Args:
        target_pos: Target EE position in world frame
        base_pos: Robot base position
        base_quat: Robot base orientation (w,x,y,z)
        current_joints: Current joint configuration (7,) - CRITICAL for avoiding elbow flip
        target_quat: Target EE orientation (w,x,y,z)
        q7_range: Range for q7 search
        q7_steps: Number of q7 values to try
        min_margin_deg: Minimum acceptable margin from joint limits
        j3_min_deg: Minimum J3 angle in degrees (H115: elbow constraint)
        j3_max_deg: Maximum J3 angle in degrees (H115: elbow constraint)
        max_joint_change_deg: Maximum allowed joint change per step (H115: IK flip prevention)

    Returns:
        success: Whether a valid solution was found
        joints: Best joint angles (7,) or None
        margin_deg: Joint margin in degrees
        distance_deg: Max joint distance from current config in degrees
    """
    if target_quat is None:
        target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)

    # Stage 1: Look for solutions with margin >= min_margin_deg
    best_solution = None
    best_margin = 0.0
    best_distance = float('inf')

    # Stage 2 fallback: Track closest solution regardless of margin
    fallback_solution = None
    fallback_margin = 0.0
    fallback_distance = float('inf')

    if use_geofik:
        sol_iter = geofik_solutions_with_base(
            target_pos, target_quat, base_pos, base_quat, arm=arm,
            q7_min=q7_range[0], q7_max=q7_range[1], q7_steps=q7_steps,
        )
    else:
        sol_iter = []
        for q7 in np.linspace(q7_range[0], q7_range[1], q7_steps):
            sols = franka_IK_EE_with_base(
                target_pos, target_quat, base_pos, base_quat, q7
            )
            sol_iter.extend(sols)

    # Debug counters for why solutions are rejected
    if use_geofik:
        total = 0
        valid = 0
        j3_reject = 0
        max_change_reject = 0
        margin_ok = 0

    for sol in sol_iter:
        if use_geofik:
            total += 1
        if sol.valid:
            if use_geofik:
                valid += 1
            # Calculate max joint distance from current config
            distance_rad = np.max(np.abs(sol.joints - current_joints))
            distance_deg = np.degrees(distance_rad)

            # H115: J3 constraint check (elbow boundary prevention)
            if j3_min_deg is not None and j3_max_deg is not None:
                j3_deg = np.degrees(sol.joints[2])  # J3 is index 2
                if not (j3_min_deg <= j3_deg <= j3_max_deg):
                    if use_geofik:
                        j3_reject += 1
                    continue  # Skip solutions outside J3 constraint

            # H115: Max joint change check (IK flip prevention)
            if max_joint_change_deg is not None:
                if distance_deg > max_joint_change_deg:
                    if use_geofik:
                        max_change_reject += 1
                    continue  # Skip solutions with too large joint change

            # Stage 1: Solutions with sufficient margin
            if sol.margin_deg >= min_margin_deg:
                if use_geofik:
                    margin_ok += 1
                # H110: J3 sign preservation to avoid elbow flip
                current_j3_sign = np.sign(current_joints[2])  # J3 is index 2
                sol_j3_sign = np.sign(sol.joints[2])

                # Prefer solutions with same J3 sign (avoid elbow flip)
                # If current_j3 is 0, allow any sign
                if current_j3_sign == 0 or sol_j3_sign == current_j3_sign:
                    if distance_deg < best_distance:
                        best_distance = distance_deg
                        best_margin = sol.margin_deg
                        best_solution = sol.joints.copy()

            # Stage 2 fallback: Track valid solution closest to current
            # H117: Also apply max_joint_change constraint to fallback
                if distance_deg < fallback_distance:
                    # H117: Skip if exceeds max_joint_change (even for fallback)
                    if max_joint_change_deg is not None and distance_deg > max_joint_change_deg:
                        continue  # Skip solutions with too large joint change
                    fallback_distance = distance_deg
                    fallback_margin = sol.margin_deg
                    fallback_solution = sol.joints.copy()

    if use_geofik:
        print(
            "[GeoFIK DEBUG] filter_summary:",
            f"total={total}",
            f"valid={valid}",
            f"j3_reject={j3_reject}",
            f"max_change_reject={max_change_reject}",
            f"margin_ok={margin_ok}",
            f"best_found={best_solution is not None}",
            f"fallback_found={fallback_solution is not None}",
        )

    # Return best solution with sufficient margin, or fallback to closest solution
    if best_solution is not None:
        return True, best_solution, best_margin, best_distance
    elif fallback_solution is not None:
        # Fallback: use closest solution even if margin < min_margin_deg
        return True, fallback_solution, fallback_margin, fallback_distance
    else:
        return False, None, 0.0, float('inf')


# ============================================================
# Test
# ============================================================

def test_analytical_ik():
    """Test the analytical IK implementation."""
    print("=" * 60)
    print("Analytical IK Test")
    print("=" * 60)

    # Test configuration - using task_config values
    base_pos = np.array([0.35, -0.3333, 1.1667])  # Note: test values, not production
    base_quat = np.array(ROBOT_BASE_QUAT_WXYZ)  # Y+90 deg from task_config

    target_pos = np.array([0.30, -0.285, 0.905])
    target_quat = np.array(GRIPPER_DOWN_QUAT_WXYZ)  # Gripper down from task_config

    print(f"\nBase position: {base_pos}")
    print(f"Base quaternion: {base_quat}")
    print(f"Target position: {target_pos}")

    # Search for best solution
    success, joints, margin = solve_ik_best(
        target_pos, base_pos, base_quat, target_quat,
        q7_range=(-2.5, 2.5), q7_steps=50
    )

    if success:
        print(f"\n[SUCCESS] Solution found!")
        print(f"  Margin: {margin:.1f} deg")
        print(f"  Joints (rad): {joints}")
        print(f"  Joints (deg): {np.degrees(joints)}")

        # Verify with forward kinematics (approximate)
        from scipy.spatial.transform import Rotation as R

        # This is a simplified FK check
        print(f"\n  Verification pending (FK implementation needed)")
    else:
        print("\n[FAILED] No valid solution found")

    return success, joints, margin


if __name__ == "__main__":
    test_analytical_ik()
