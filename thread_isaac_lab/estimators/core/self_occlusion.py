# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage 0: self-occlusion mask — Warp kernel projecting fingers into camera.

Per v3 §5.1 (Warp kernel mandate). Per v2.1 patch P3/F8: fingers are
**received pre-sliced** from :class:`KinematicsProvider.finger_positions`
(``[B, 2, 3]``) — no FK is recomputed inside core (CC2.C4 / CC3.C3 fix).

R6 module boundary: imports from ``thread_isaac_lab.estimators.*`` only —
no ``newton`` / no env imports.
"""

import torch
import warp as wp

from thread_isaac_lab.estimators.input_adapter import _split_pose7


@wp.kernel
def _project_finger_kernel(
    cam_xyz: wp.array(dtype=wp.vec3),
    cam_quat: wp.array(dtype=wp.vec4),
    finger_l: wp.array(dtype=wp.vec3),
    finger_r: wp.array(dtype=wp.vec3),
    finger_radius: float,
    fx: float,
    fy: float,
    cx: float,
    cy: float,
    H: int,
    W_img: int,
    out_mask_flat: wp.array2d(dtype=wp.uint8),
):
    b = wp.tid()
    cam_p = cam_xyz[b]
    q = cam_quat[b]
    qxyz = wp.vec3(-q[0], -q[1], -q[2])

    # Process both fingers per world.
    for finger_id in range(2):
        if finger_id == 0:
            f_world = finger_l[b]
        else:
            f_world = finger_r[b]

        delta = f_world - cam_p
        t = wp.vec3(
            2.0 * (qxyz[1] * delta[2] - qxyz[2] * delta[1]),
            2.0 * (qxyz[2] * delta[0] - qxyz[0] * delta[2]),
            2.0 * (qxyz[0] * delta[1] - qxyz[1] * delta[0]),
        )
        p_cam = wp.vec3(
            delta[0] + q[3] * t[0] + (qxyz[1] * t[2] - qxyz[2] * t[1]),
            delta[1] + q[3] * t[1] + (qxyz[2] * t[0] - qxyz[0] * t[2]),
            delta[2] + q[3] * t[2] + (qxyz[0] * t[1] - qxyz[1] * t[0]),
        )

        if p_cam[2] > 0.001:
            u_center = fx * (p_cam[0] / p_cam[2]) + cx
            v_center = fy * (p_cam[1] / p_cam[2]) + cy
            radius_px = (fx * finger_radius) / p_cam[2]

            u_min = int(wp.max(u_center - radius_px, 0.0))
            v_min = int(wp.max(v_center - radius_px, 0.0))
            u_max = int(wp.min(u_center + radius_px, float(W_img - 1)))
            v_max = int(wp.min(v_center + radius_px, float(H - 1)))

            for v in range(v_min, v_max + 1):
                for u in range(u_min, u_max + 1):
                    flat_idx = v * W_img + u
                    out_mask_flat[b, flat_idx] = wp.uint8(1)


def compute_self_occlusion_mask(
    wrist_camera_pose_l: torch.Tensor,
    finger_positions: torch.Tensor,
    intrinsics,
    finger_radius: float = 0.012,
) -> torch.Tensor:
    """Compute per-world self-occlusion mask (1 = pixel occluded by self).

    Args:
        wrist_camera_pose_l: ``[B, 7]`` (px py pz qx qy qz qw).
        finger_positions: ``[B, 2, 3]`` world xyz for (left, right) fingertips.
        intrinsics: :class:`CameraIntrinsics` (placeholder rejected).
        finger_radius: physical fingertip radius in meters.

    Returns:
        ``[B, 1, H, W_img]`` ``torch.uint8`` mask.
    """
    if finger_positions.shape[1:] != (2, 3):
        raise ValueError(f"Expected finger_positions [B, 2, 3], got shape {tuple(finger_positions.shape)}")
    B = wrist_camera_pose_l.shape[0]
    device = wrist_camera_pose_l.device

    cam_xyz, cam_quat = _split_pose7(wrist_camera_pose_l)
    finger_l = finger_positions[:, 0, :].contiguous()
    finger_r = finger_positions[:, 1, :].contiguous()

    out_flat = torch.zeros(B, intrinsics.H * intrinsics.W_img, dtype=torch.uint8, device=device)

    wp.launch(
        _project_finger_kernel,
        dim=B,
        inputs=[
            wp.from_torch(cam_xyz, dtype=wp.vec3),
            wp.from_torch(cam_quat, dtype=wp.vec4),
            wp.from_torch(finger_l, dtype=wp.vec3),
            wp.from_torch(finger_r, dtype=wp.vec3),
            float(finger_radius),
            float(intrinsics.fx),
            float(intrinsics.fy),
            float(intrinsics.cx),
            float(intrinsics.cy),
            int(intrinsics.H),
            int(intrinsics.W_img),
        ],
        outputs=[wp.from_torch(out_flat)],
        device=str(device),
    )
    return out_flat.view(B, 1, intrinsics.H, intrinsics.W_img)
