"""dual_arm_ik_utils.py -- Shared constants and batch IK utilities for dual-arm scripts.

Extracted from poc_dual_arm_vectorized.py so that other scripts (e.g. train_fine_rl.py)
can import without triggering argparse/AppLauncher side effects.

All functions are pure torch / numpy with no module-level side effects.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FINGERTIP_OFFSET = 0.1123  # panda_hand -> fingertip (m)
BALL_RADIUS = 0.03
APPROACH_MARGIN = 0.01
GRIPPER_OPEN = 0.04

# Franka "ready" bent-elbow joints (non-singular)
BENT_JOINTS = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]

# Dual base positions
DUAL_LEFT_BASE_Y = -0.55
DUAL_RIGHT_BASE_Y = +0.55
BASE_X = 0.2467
BASE_Z = 1.265
BASE_QUAT = [0.7071, 0.0, 0.7071, 0.0]  # (w, x, y, z)

# Target generation center
DUAL_CENTER = np.array([0.75, 0.00, 1.05], dtype=np.float32)


# ---------------------------------------------------------------------------
# Batched math utilities
# ---------------------------------------------------------------------------

def quat_rotate_vec_batch(q_wxyz: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Rotate vec by quaternion.  q_wxyz: (N, 4), vec: (N, 3) -> (N, 3)."""
    w = q_wxyz[:, 0:1]
    xyz = q_wxyz[:, 1:4]
    t = 2.0 * torch.cross(xyz, vec, dim=-1)
    return vec + w * t + torch.cross(xyz, t, dim=-1)


def ee_to_fingertip_batch(ee_pos: torch.Tensor, ee_quat_wxyz: torch.Tensor,
                          offset: float = FINGERTIP_OFFSET) -> torch.Tensor:
    """Compute fingertip positions.  (N, 3) each -> (N, 3)."""
    z_local = torch.zeros_like(ee_pos)
    z_local[:, 2] = offset
    z_world = quat_rotate_vec_batch(ee_quat_wxyz, z_local)
    return ee_pos + z_world


def fingertip_to_ee_batch(ft_pos: torch.Tensor, ee_quat_wxyz: torch.Tensor,
                          offset: float = FINGERTIP_OFFSET) -> torch.Tensor:
    """Convert fingertip target to EE target.  (N, 3) each -> (N, 3)."""
    z_local = torch.zeros_like(ft_pos)
    z_local[:, 2] = offset
    z_world = quat_rotate_vec_batch(ee_quat_wxyz, z_local)
    return ft_pos - z_world


def compute_desired_orientation_batch(ball_pos: torch.Tensor,
                                      ee_pos: torch.Tensor) -> torch.Tensor:
    """Compute desired gripper quaternion so +Z points EE->ball.  (N,3) -> (N,4) wxyz."""
    N = ball_pos.shape[0]
    device = ball_pos.device

    desired_z = ball_pos - ee_pos  # (N, 3)
    nz = torch.norm(desired_z, dim=-1, keepdim=True).clamp(min=1e-8)
    desired_z = desired_z / nz

    world_up = torch.tensor([0.0, 0.0, 1.0], device=device).expand(N, 3).clone()
    # Where desired_z is nearly parallel to world_up, use X-axis instead
    parallel_mask = (torch.abs(torch.sum(desired_z * world_up, dim=-1)) > 0.99)
    world_up[parallel_mask] = torch.tensor([1.0, 0.0, 0.0], device=device)

    desired_x = torch.cross(world_up, desired_z, dim=-1)
    nx = torch.norm(desired_x, dim=-1, keepdim=True).clamp(min=1e-8)
    desired_x = desired_x / nx

    desired_y = torch.cross(desired_z, desired_x, dim=-1)

    # Rotation matrix to quaternion (batch)
    R = torch.stack([desired_x, desired_y, desired_z], dim=-1)  # (N, 3, 3)
    return _rotation_matrix_to_quat_batch(R)


def _rotation_matrix_to_quat_batch(R: torch.Tensor) -> torch.Tensor:
    """Convert (N, 3, 3) rotation matrices to (N, 4) quaternions (w,x,y,z)."""
    N = R.shape[0]
    q = torch.zeros(N, 4, device=R.device, dtype=R.dtype)

    trace = R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2]

    # Case 1: trace > 0
    mask1 = trace > 0
    if mask1.any():
        s = 0.5 / torch.sqrt(trace[mask1] + 1.0)
        q[mask1, 0] = 0.25 / s
        q[mask1, 1] = (R[mask1, 2, 1] - R[mask1, 1, 2]) * s
        q[mask1, 2] = (R[mask1, 0, 2] - R[mask1, 2, 0]) * s
        q[mask1, 3] = (R[mask1, 1, 0] - R[mask1, 0, 1]) * s

    # Case 2: R[0,0] is largest diagonal
    mask2 = (~mask1) & (R[:, 0, 0] > R[:, 1, 1]) & (R[:, 0, 0] > R[:, 2, 2])
    if mask2.any():
        s = 2.0 * torch.sqrt(1.0 + R[mask2, 0, 0] - R[mask2, 1, 1] - R[mask2, 2, 2])
        q[mask2, 0] = (R[mask2, 2, 1] - R[mask2, 1, 2]) / s
        q[mask2, 1] = 0.25 * s
        q[mask2, 2] = (R[mask2, 0, 1] + R[mask2, 1, 0]) / s
        q[mask2, 3] = (R[mask2, 0, 2] + R[mask2, 2, 0]) / s

    # Case 3: R[1,1] is largest diagonal
    mask3 = (~mask1) & (~mask2) & (R[:, 1, 1] > R[:, 2, 2])
    if mask3.any():
        s = 2.0 * torch.sqrt(1.0 + R[mask3, 1, 1] - R[mask3, 0, 0] - R[mask3, 2, 2])
        q[mask3, 0] = (R[mask3, 0, 2] - R[mask3, 2, 0]) / s
        q[mask3, 1] = (R[mask3, 0, 1] + R[mask3, 1, 0]) / s
        q[mask3, 2] = 0.25 * s
        q[mask3, 3] = (R[mask3, 1, 2] + R[mask3, 2, 1]) / s

    # Case 4: R[2,2] is largest diagonal
    mask4 = (~mask1) & (~mask2) & (~mask3)
    if mask4.any():
        s = 2.0 * torch.sqrt(1.0 + R[mask4, 2, 2] - R[mask4, 0, 0] - R[mask4, 1, 1])
        q[mask4, 0] = (R[mask4, 1, 0] - R[mask4, 0, 1]) / s
        q[mask4, 1] = (R[mask4, 0, 2] + R[mask4, 2, 0]) / s
        q[mask4, 2] = (R[mask4, 1, 2] + R[mask4, 2, 1]) / s
        q[mask4, 3] = 0.25 * s

    # Normalize
    q = q / torch.norm(q, dim=-1, keepdim=True).clamp(min=1e-8)
    return q


def orientation_error_axis_angle_batch(desired_wxyz: torch.Tensor,
                                       current_wxyz: torch.Tensor) -> torch.Tensor:
    """Compute orientation error as axis-angle.  (N,4), (N,4) -> (N,3)."""
    # q_err = desired * conj(current)
    conj_current = current_wxyz.clone()
    conj_current[:, 1:4] = -conj_current[:, 1:4]

    # Quaternion multiply: desired * conj(current)
    q_err = _quat_multiply_batch(desired_wxyz, conj_current)

    # Ensure w > 0 for shortest path
    neg_w = q_err[:, 0] < 0
    q_err[neg_w] = -q_err[neg_w]

    # Axis-angle: 2 * arccos(w) * axis
    w = q_err[:, 0].clamp(-1.0, 1.0)
    angle = 2.0 * torch.acos(w)  # (N,)
    sin_half = torch.sqrt(1.0 - w * w).clamp(min=1e-8)
    axis = q_err[:, 1:4] / sin_half.unsqueeze(-1)

    return axis * angle.unsqueeze(-1)  # (N, 3)


def _quat_multiply_batch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Multiply quaternions (w,x,y,z).  (N,4), (N,4) -> (N,4)."""
    aw, ax, ay, az = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    bw, bx, by, bz = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    return torch.stack([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ], dim=-1)


# ---------------------------------------------------------------------------
# Target generation
# ---------------------------------------------------------------------------

def make_targets_per_env(num_envs: int, num_targets: int,
                         seed_start: int) -> list[list[np.ndarray]]:
    """Generate targets for each environment with different seeds.

    Returns: list of length num_envs, each element is a list of num_targets
             np.ndarray targets of shape (3,).
    """
    all_targets: list[list[np.ndarray]] = []
    for env_i in range(num_envs):
        seed = seed_start + env_i
        rng = np.random.RandomState(seed)
        targets: list[np.ndarray] = []
        target_range = 0.05
        min_dist_m = 0.02
        max_attempts = num_targets * 50
        attempts = 0
        while len(targets) < num_targets and attempts < max_attempts:
            dx = rng.uniform(-0.03, 0.03)
            dy = rng.uniform(-target_range, target_range)
            dz = rng.uniform(-target_range, target_range)
            candidate = np.array([
                DUAL_CENTER[0] + dx,
                DUAL_CENTER[1] + dy,
                DUAL_CENTER[2] + dz,
            ], dtype=np.float32)
            too_close = any(np.linalg.norm(candidate - e) < min_dist_m for e in targets)
            if not too_close:
                targets.append(candidate)
            attempts += 1
        all_targets.append(targets)
    return all_targets


def compute_dual_targets_batch(ball_pos: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute left and right FINGERTIP targets from ball positions.

    ball_pos: (N, 3) -> left_ft: (N, 3), right_ft: (N, 3)
    Y-axis approach: left from Y-, right from Y+.
    """
    grasp_offset = BALL_RADIUS + APPROACH_MARGIN  # 0.04
    left_ft = ball_pos.clone()
    left_ft[:, 1] -= grasp_offset
    right_ft = ball_pos.clone()
    right_ft[:, 1] += grasp_offset
    return left_ft, right_ft


# ---------------------------------------------------------------------------
# Collision avoidance
# ---------------------------------------------------------------------------

def check_arm_separation_batch(
    ee_left: torch.Tensor,   # (N, 3)
    ee_right: torch.Tensor,  # (N, 3)
    min_dist: float = 0.15,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Check distance between arms and return (distance, scale_factor).

    If arms are closer than min_dist, returns scale_factor < 1.0.
    Returns: (dist: (N,), scale: (N,))
    """
    dist = torch.norm(ee_left - ee_right, dim=-1)  # (N,)
    scale = torch.clamp(dist / min_dist, min=0.0, max=1.0)
    return dist, scale


# ---------------------------------------------------------------------------
# Batched IK
# ---------------------------------------------------------------------------

def jt_ik_step_6dof_batch(
    robot,
    jacobian_body: int,
    hand_body: int,
    cmd_pos_w: torch.Tensor,       # (N, 3)
    ball_pos: torch.Tensor,         # (N, 3)
    enable_ori_mask: torch.Tensor,  # (N,) bool
    jt_alpha: float,
    jt_alpha_ori: float,
    ori_enable_dist: float,
    clip_rad: float,
    device: torch.device,
) -> tuple[Optional[torch.Tensor], torch.Tensor]:
    """Batched 6-DOF Jacobian Transpose IK step.

    Returns (ik_target_joints: (N, 7), nan_mask: (N,) bool).
    ik_target_joints is None if ALL environments produced NaN.
    """
    N = cmd_pos_w.shape[0]
    joint_pos = robot.data.joint_pos[:, :7]  # (N, 7)
    jac_w = robot.root_physx_view.get_jacobians()[:, jacobian_body, :, :7]  # (N, 6, 7)
    ee_pos_w = robot.data.body_pose_w[:, hand_body, :3]  # (N, 3)
    ee_quat_w = robot.data.body_quat_w[:, hand_body, :]  # (N, 4)

    # Position error
    pos_error = cmd_pos_w - ee_pos_w  # (N, 3)
    pos_err_mag = torch.norm(pos_error, dim=-1)  # (N,)

    # Decide which envs use orientation control
    ori_active = enable_ori_mask & (pos_err_mag < ori_enable_dist)  # (N,)

    # Compute orientation error for envs that need it
    desired_quat = compute_desired_orientation_batch(ball_pos, ee_pos_w)  # (N, 4)
    ori_err_aa = orientation_error_axis_angle_batch(desired_quat, ee_quat_w)  # (N, 3)

    # Scale orientation gain based on distance
    ori_scale = torch.clamp(1.0 - pos_err_mag / ori_enable_dist, min=0.0)  # (N,)
    effective_alpha_ori = jt_alpha_ori * ori_scale  # (N,)

    # Build 6D error
    error_6d = torch.zeros(N, 6, device=device)
    error_6d[:, :3] = jt_alpha * pos_error
    # Only add orientation for envs with ori_active
    ori_contribution = effective_alpha_ori.unsqueeze(-1) * ori_err_aa  # (N, 3)
    error_6d[:, 3:6] = torch.where(
        ori_active.unsqueeze(-1).expand_as(ori_contribution),
        ori_contribution,
        torch.zeros_like(ori_contribution),
    )

    # dq = J^T @ error_6d
    J_full = jac_w[:, :6, :]  # (N, 6, 7)
    dq = torch.bmm(J_full.transpose(1, 2), error_6d.unsqueeze(2)).squeeze(2)  # (N, 7)

    # Check for NaN
    nan_mask = torch.any(torch.isnan(dq), dim=-1)  # (N,)

    # Clip
    dq_clipped = dq.clamp(-clip_rad, clip_rad)
    # Zero out NaN envs
    dq_clipped[nan_mask] = 0.0

    ik_targets = (joint_pos + dq_clipped).clone()
    return ik_targets, nan_mask


def apply_joints_batch(robot, ik_joints: torch.Tensor, action_mask: torch.Tensor):
    """Apply IK joint targets + open gripper for all envs.

    ik_joints: (N, 7)
    action_mask: (N,) bool -- only apply to envs where True
    """
    tgt = robot.data.joint_pos.clone()  # (N, n_joints)
    # Only update envs in the mask
    mask_expanded = action_mask.unsqueeze(-1)  # (N, 1)
    tgt[:, :7] = torch.where(mask_expanded.expand_as(tgt[:, :7]),
                              ik_joints, tgt[:, :7])
    if tgt.shape[1] >= 9:
        tgt[:, 7] = torch.where(action_mask, torch.full_like(tgt[:, 7], GRIPPER_OPEN), tgt[:, 7])
        tgt[:, 8] = torch.where(action_mask, torch.full_like(tgt[:, 8], GRIPPER_OPEN), tgt[:, 8])
    robot.set_joint_position_target(tgt)
    robot.write_data_to_sim()
