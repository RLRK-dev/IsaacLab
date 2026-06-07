# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage 0: ROI prior — Warp kernel projecting target clip nominal pose into camera frame.

Per v3 §5.1 (Warp kernel mandate, scipy CPU loop forbidden).

v2.1 patch:
- P1: ``CLIP_POSITIONS`` is shape ``[5, 2]`` (XY only); the Z column is built
  from ``TABLE_HEIGHT`` (task_config.py:20). We do **not** edit
  ``task_config.py`` (read-only SSOT).
- P10/F10: :class:`CameraIntrinsics` requires explicit values; the
  ``__post_init__`` rejects the historical placeholder
  ``fx=fy=100, cx=cy=64`` to prevent silent-wrong projections (CC5.C4).

R6 module boundary: imports from ``thread_isaac_lab.estimators.*`` and
``thread_isaac_lab.configs.task_config`` only — no ``newton`` / no env imports.
"""

from dataclasses import dataclass

import torch
import warp as wp

from thread_isaac_lab.configs.task_config import CLIP_POSITIONS, TABLE_HEIGHT
from thread_isaac_lab.estimators.input_adapter import _split_pose7


@dataclass
class CameraIntrinsics:
    """Pinhole camera intrinsics (must NOT use placeholder values; v2.1 P10)."""

    fx: float
    fy: float
    cx: float
    cy: float
    H: int
    W_img: int
    margin_px: int = 16

    def __post_init__(self) -> None:
        if self.fx == 100.0 and self.fy == 100.0 and self.cx == 64.0 and self.cy == 64.0:
            raise ValueError("CameraIntrinsics placeholder rejected; pass real WristTiledCameraCfg-derived values")


def _build_clip_world_3d(device: torch.device) -> torch.Tensor:
    """Build a ``[5, 3]`` clip world-position tensor.

    ``CLIP_POSITIONS`` is shape ``[5, 2]`` (XY); we append ``TABLE_HEIGHT`` as
    the Z column per ``task_config.py:94`` ("Z = TABLE_HEIGHT for all").
    """
    clip_xy = torch.tensor(CLIP_POSITIONS, dtype=torch.float32, device=device)
    clip_z = torch.full((clip_xy.shape[0], 1), TABLE_HEIGHT, dtype=torch.float32, device=device)
    return torch.cat([clip_xy, clip_z], dim=1)


@wp.kernel
def _project_clip_kernel(
    cam_xyz: wp.array(dtype=wp.vec3),
    cam_quat: wp.array(dtype=wp.vec4),
    clip_world: wp.array(dtype=wp.vec3),
    target_clip_idx: wp.array(dtype=wp.int32),
    fx: float,
    fy: float,
    cx: float,
    cy: float,
    H: int,
    W_img: int,
    margin_px: int,
    out_roi: wp.array(dtype=wp.vec4),
):
    b = wp.tid()
    ci = target_clip_idx[b]
    p_world = clip_world[ci]
    cam_p = cam_xyz[b]
    q = cam_quat[b]

    # World -> camera frame: rotate (p_world - cam_p) by conjugate of camera quat.
    delta = p_world - cam_p
    qxyz = wp.vec3(-q[0], -q[1], -q[2])
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
        u = fx * (p_cam[0] / p_cam[2]) + cx
        v = fy * (p_cam[1] / p_cam[2]) + cy
        u_min = wp.max(u - float(margin_px), 0.0)
        v_min = wp.max(v - float(margin_px), 0.0)
        u_max = wp.min(u + float(margin_px), float(W_img))
        v_max = wp.min(v + float(margin_px), float(H))
        out_roi[b] = wp.vec4(u_min, v_min, u_max, v_max)
    else:
        out_roi[b] = wp.vec4(0.0, 0.0, 0.0, 0.0)


def compute_roi_boxes(
    wrist_camera_pose_l: torch.Tensor,
    target_clip_idx: torch.Tensor,
    intrinsics: CameraIntrinsics,
) -> torch.Tensor:
    """Compute per-world ROI box for the routing target clip.

    Args:
        wrist_camera_pose_l: ``[B, 7]`` (px py pz qx qy qz qw).
        target_clip_idx: ``[B]`` long indices into ``CLIP_POSITIONS``.
        intrinsics: pinhole camera params (placeholder rejected).

    Returns:
        ``[B, 1, 4]`` ROI box ``(x_min, y_min, x_max, y_max)``.
    """
    B = wrist_camera_pose_l.shape[0]
    device = wrist_camera_pose_l.device

    cam_xyz, cam_quat = _split_pose7(wrist_camera_pose_l)
    clip_world = _build_clip_world_3d(device)
    target_clip_idx_i32 = target_clip_idx.to(torch.int32).contiguous()

    out_roi = torch.zeros(B, 4, dtype=torch.float32, device=device)

    wp.launch(
        _project_clip_kernel,
        dim=B,
        inputs=[
            wp.from_torch(cam_xyz, dtype=wp.vec3),
            wp.from_torch(cam_quat, dtype=wp.vec4),
            wp.from_torch(clip_world, dtype=wp.vec3),
            wp.from_torch(target_clip_idx_i32, dtype=wp.int32),
            float(intrinsics.fx),
            float(intrinsics.fy),
            float(intrinsics.cx),
            float(intrinsics.cy),
            int(intrinsics.H),
            int(intrinsics.W_img),
            int(intrinsics.margin_px),
        ],
        outputs=[wp.from_torch(out_roi, dtype=wp.vec4)],
        device=str(device),
    )
    return out_roi.view(B, 1, 4)
