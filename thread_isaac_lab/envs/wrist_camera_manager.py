# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Wrist camera manager for Newton RL envs.

Encapsulates SensorTiledCamera lifecycle: sensor init, buffer allocation,
per-step transform computation from body_q, rendering, and Warp→torch
tensor conversion.

Phase 2 of visual obs pipeline. Phase 3 adds frozen encoder on top.
"""

import math

import numpy as np
import torch
import warp as wp
from scipy.spatial.transform import Rotation as _ScipyRotation
from task_config import EE_BODY_OFFSET, FRANKA_NUM_JOINTS

# Robot body layout (UR5e+Robotiq, Newton collapsed joints)

# Camera offsets verified for FRANKA body 6 (link7) frame; UR5e wrist_3 (EE body 5) re-verify at camera/S6
# Source: test_newton_clip_routing.py:125-126
DEFAULT_LOCAL_POS = np.array([0.05, 0.05, 0.10])
DEFAULT_LOCAL_TARGET = np.array([0.0, 0.0, 0.17])

DEFAULT_RESOLUTION = 128
DEFAULT_FOV_DEG = 45.0


def _look_at_quat(pos, target):
    """Compute quaternion (xyzw) for camera looking from pos at target."""
    forward = target - pos
    forward = forward / (np.linalg.norm(forward) + 1e-8)
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up)
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-6:
        up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, up)
        right_norm = np.linalg.norm(right)
    right = right / right_norm
    up = np.cross(right, forward)
    rot_mat = np.stack([right, up, -forward], axis=1)
    return _ScipyRotation.from_matrix(rot_mat).as_quat()  # (x, y, z, w)


class WristCameraManager:
    """Manages SensorTiledCamera for Newton RL envs.

    Creates 2 wrist cameras (L/R) attached to the wrist-EE (wrist_3) bodies,
    renders RGB-D each step, and exposes results as torch tensors.
    """

    def __init__(
        self,
        model,
        bws,
        world_count,
        device,
        resolution=DEFAULT_RESOLUTION,
        fov_deg=DEFAULT_FOV_DEG,
        enable_color=True,
        enable_depth=True,
    ):
        """Initialize camera sensor and allocate buffers.

        Args:
            model: Finalized Newton Model (env._model).
            bws: Body world start indices, numpy array (env._bws).
            world_count: Number of parallel worlds.
            device: Device string (e.g. "cuda:0").
            resolution: Square image resolution (default 128).
            fov_deg: Vertical FOV in degrees (default 45).
            enable_color: Allocate color buffer.
            enable_depth: Allocate depth buffer.
        """
        from newton.sensors import SensorTiledCamera

        self._world_count = world_count
        self._bws = bws
        self._device = device
        self._resolution = resolution
        self._camera_count = 2  # L + R wrist

        # Camera definitions: (body_offset, local_pos, local_target)
        self._cameras = [
            (EE_BODY_OFFSET, DEFAULT_LOCAL_POS.copy(), DEFAULT_LOCAL_TARGET.copy()),
            (FRANKA_NUM_JOINTS + EE_BODY_OFFSET, DEFAULT_LOCAL_POS.copy(), DEFAULT_LOCAL_TARGET.copy()),
        ]

        # Create sensor
        self._sensor = SensorTiledCamera(
            model=model,
            config=SensorTiledCamera.Config(
                default_light=True,
                default_light_shadows=False,
                colors_per_shape=True,
                backface_culling=True,
            ),
        )

        # Pre-compute camera rays
        fov_list = [math.radians(fov_deg)] * self._camera_count
        self._camera_rays = self._sensor.compute_pinhole_camera_rays(resolution, resolution, fov_list)

        # Allocate output buffers
        W, H = resolution, resolution
        self._depth_buf = None
        self._color_buf = None
        if enable_depth:
            self._depth_buf = self._sensor.create_depth_image_output(W, H, self._camera_count)
        if enable_color:
            self._color_buf = self._sensor.create_color_image_output(W, H, self._camera_count)

    def update(self, state_0):
        """Compute camera transforms from body_q and render.

        Call after auto-reset, before _compute_obs_batch.

        Args:
            state_0: Newton State with current body_q.
        """
        wp.synchronize()
        bq = state_0.body_q.numpy()
        tf_list = []

        for body_offset, local_pos, local_target in self._cameras:
            cam_world_tfs = []
            for w in range(self._world_count):
                bws = self._bws[w]
                body_idx = bws + body_offset
                body_tf = bq[body_idx]
                hand_pos = body_tf[:3]
                hand_quat = body_tf[3:7]

                r = _ScipyRotation.from_quat([hand_quat[0], hand_quat[1], hand_quat[2], hand_quat[3]])
                cam_pos = hand_pos + r.apply(local_pos)
                cam_target = hand_pos + r.apply(local_target)

                cam_quat = _look_at_quat(cam_pos, cam_target)
                cam_world_tfs.append(
                    wp.transformf(
                        wp.vec3f(float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2])),
                        wp.quatf(float(cam_quat[0]), float(cam_quat[1]), float(cam_quat[2]), float(cam_quat[3])),
                    )
                )
            tf_list.append(cam_world_tfs)

        cam_tf_array = wp.array(tf_list, dtype=wp.transformf)

        self._sensor.update(
            state_0,
            cam_tf_array,
            self._camera_rays,
            color_image=self._color_buf,
            depth_image=self._depth_buf,
        )

    @property
    def depth_tensor(self) -> torch.Tensor | None:
        """Depth as torch.Tensor [world_count, cam_count, H, W] float32.

        Zero-copy GPU view — overwritten on next update(). Clone if persistence needed.
        Camera index: 0=Left, 1=Right.
        """
        if self._depth_buf is None:
            return None
        return wp.to_torch(self._depth_buf)

    @property
    def color_tensor(self) -> torch.Tensor | None:
        """Color as torch.Tensor [world_count, cam_count, H, W] uint32.

        Zero-copy GPU view — overwritten on next update(). Clone if persistence needed.
        Camera index: 0=Left, 1=Right. Returns None if color buffer not allocated.
        """
        if self._color_buf is None:
            return None
        return wp.to_torch(self._color_buf)

    @property
    def rgb_tensor(self) -> torch.Tensor | None:
        """RGB as torch.Tensor [world_count, cam_count, 3, H, W] float32 in [0, 1].

        Unpacks uint32 RGBA to float32 RGB. Allocates new memory each call.
        Camera index: 0=Left, 1=Right. Returns None if color buffer not allocated.
        """
        if self._color_buf is None:
            return None
        raw = wp.to_torch(self._color_buf)  # [W, C, H, W_px] uint32
        shape = raw.shape
        # Reinterpret uint32 as 4 bytes per pixel (R, G, B, A in little-endian)
        bytes_4ch = raw.contiguous().view(torch.uint8).reshape(*shape, 4)
        r = bytes_4ch[..., 0].float() / 255.0  # [W, C, H, W_px]
        g = bytes_4ch[..., 1].float() / 255.0
        b = bytes_4ch[..., 2].float() / 255.0
        # Stack to [W, C, 3, H, W_px] — channel-first for conv nets
        return torch.stack([r, g, b], dim=2)

    @property
    def camera_count(self) -> int:
        return self._camera_count

    @property
    def resolution(self) -> int:
        return self._resolution


# ===========================================================================
# 3-cam variant for T-Vision-CableState L1.A.2 (Phase 1)
#
# Per ``thread-vault/06-Knowledge/LL-Vision-CableState-Design.md`` §4.3 the
# cable-state pipeline benefits from a third world-fixed overhead camera in
# addition to the existing wrist L/R pair (EXP-046 precedent: 3-cam merged
# error 3.92 mm vs single front-cam 80 mm Y-bias). This subclass adds that
# overhead camera as a body-frame-independent view; design memo §4.3 256²
# overhead at FOV 60° is deferred to Phase 2+ because the underlying
# :class:`newton.sensors.SensorTiledCamera` shares a single resolution across
# all rays — Phase 1 keeps 128² across all 3 cameras and accepts per-cam FOV
# only.
# ===========================================================================


# Default overhead camera config — design memo §4.3.
DEFAULT_OVERHEAD_POS = np.array([0.3, 0.0, 1.6])  # world-fixed, above table
DEFAULT_OVERHEAD_TARGET = np.array([0.3, 0.0, 0.8])  # look-at table center
DEFAULT_OVERHEAD_FOV_DEG = 60.0  # wider than wrist (45°) for full table coverage


class CableStateCameraManager(WristCameraManager):
    """3-cam variant: 2× wrist (body-anchored) + 1× overhead (world-fixed).

    Adds a static world-fixed overhead camera to the existing wrist L/R pair.
    The overhead pose does not depend on ``state_0.body_q`` and is precomputed
    once at construction time — only the wrist transforms are re-derived each
    :meth:`update` call.

    Camera index:
        0 — left wrist (body-anchored)
        1 — right wrist (body-anchored)
        2 — overhead (world-fixed)

    Args:
        model: Finalized Newton Model (env._model).
        bws: Body world start indices (env._bws).
        world_count: Number of parallel worlds.
        device: Device string.
        resolution: Square image resolution shared across all 3 cams. Phase 1
            keeps the existing 128² wrist default; design memo §4.3 256²
            overhead refactor is deferred (per-cam resolution requires
            splitting into 2 :class:`SensorTiledCamera` instances).
        fov_deg: Wrist FOV in degrees (default 45° per existing baseline).
        enable_color: Allocate color buffer.
        enable_depth: Allocate depth buffer.
        overhead_pos: Overhead camera position in world frame. Default
            ``(0.3, 0.0, 1.6)``.
        overhead_target: Overhead look-at point in world frame. Default
            ``(0.3, 0.0, 0.8)`` (table center).
        overhead_fov_deg: Overhead FOV in degrees. Default 60° (design memo
            §4.3).

    Backward compat: this subclass does not modify
    :class:`WristCameraManager`; existing 2-cam callers continue to work.
    """

    def __init__(
        self,
        model,
        bws,
        world_count,
        device,
        resolution=DEFAULT_RESOLUTION,
        fov_deg=DEFAULT_FOV_DEG,
        enable_color=True,
        enable_depth=True,
        overhead_pos: np.ndarray = DEFAULT_OVERHEAD_POS,
        overhead_target: np.ndarray = DEFAULT_OVERHEAD_TARGET,
        overhead_fov_deg: float = DEFAULT_OVERHEAD_FOV_DEG,
    ):
        # Imported lazily to mirror the parent's localized newton import.
        from newton.sensors import SensorTiledCamera

        self._world_count = world_count
        self._bws = bws
        self._device = device
        self._resolution = resolution
        self._camera_count = 3  # L wrist + R wrist + overhead

        # Camera spec: ``(body_offset, pos, target)`` — body_offset == None
        # is the sentinel for a world-fixed camera. The wrist entries match
        # the parent constructor's defaults to ensure index parity (0=L, 1=R).
        self._cameras = [
            (EE_BODY_OFFSET, DEFAULT_LOCAL_POS.copy(), DEFAULT_LOCAL_TARGET.copy()),
            (FRANKA_NUM_JOINTS + EE_BODY_OFFSET, DEFAULT_LOCAL_POS.copy(), DEFAULT_LOCAL_TARGET.copy()),
            (
                None,
                np.asarray(overhead_pos, dtype=np.float64).copy(),
                np.asarray(overhead_target, dtype=np.float64).copy(),
            ),
        ]

        # Precompute the overhead world-fixed transform once — it is constant.
        oh_pos = self._cameras[2][1]
        oh_target = self._cameras[2][2]
        self._overhead_quat = _look_at_quat(oh_pos, oh_target)
        self._overhead_pos = oh_pos
        self._overhead_fov_deg = float(overhead_fov_deg)

        # Sensor and ray setup — per-camera FOV list (wrist matches default,
        # overhead uses its own FOV).
        self._sensor = SensorTiledCamera(
            model=model,
            config=SensorTiledCamera.Config(
                default_light=True,
                default_light_shadows=False,
                colors_per_shape=True,
                backface_culling=True,
            ),
        )
        fov_list = [math.radians(fov_deg)] * 2 + [math.radians(self._overhead_fov_deg)]
        self._camera_rays = self._sensor.compute_pinhole_camera_rays(resolution, resolution, fov_list)

        # Output buffers.
        W, H = resolution, resolution
        self._depth_buf = None
        self._color_buf = None
        if enable_depth:
            self._depth_buf = self._sensor.create_depth_image_output(W, H, self._camera_count)
        if enable_color:
            self._color_buf = self._sensor.create_color_image_output(W, H, self._camera_count)

    def update(self, state_0):
        """Compute camera transforms (per-body for wrists, static for overhead)
        and render all 3 cameras.

        The wrist branch is identical to the parent's per-body computation.
        The overhead branch is a constant transform broadcast across worlds.
        """
        wp.synchronize()
        bq = state_0.body_q.numpy()
        tf_list = []

        for body_offset, pos, target in self._cameras:
            cam_world_tfs = []
            if body_offset is None:
                # World-fixed: same transform for every world.
                cam_pos = pos
                cam_quat = self._overhead_quat
                wp_tf = wp.transformf(
                    wp.vec3f(float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2])),
                    wp.quatf(
                        float(cam_quat[0]),
                        float(cam_quat[1]),
                        float(cam_quat[2]),
                        float(cam_quat[3]),
                    ),
                )
                cam_world_tfs = [wp_tf for _ in range(self._world_count)]
            else:
                for w in range(self._world_count):
                    bws = self._bws[w]
                    body_idx = bws + body_offset
                    body_tf = bq[body_idx]
                    hand_pos = body_tf[:3]
                    hand_quat = body_tf[3:7]

                    r = _ScipyRotation.from_quat([hand_quat[0], hand_quat[1], hand_quat[2], hand_quat[3]])
                    cam_pos = hand_pos + r.apply(pos)
                    cam_target = hand_pos + r.apply(target)

                    cam_quat = _look_at_quat(cam_pos, cam_target)
                    cam_world_tfs.append(
                        wp.transformf(
                            wp.vec3f(float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2])),
                            wp.quatf(
                                float(cam_quat[0]),
                                float(cam_quat[1]),
                                float(cam_quat[2]),
                                float(cam_quat[3]),
                            ),
                        )
                    )
            tf_list.append(cam_world_tfs)

        cam_tf_array = wp.array(tf_list, dtype=wp.transformf)

        self._sensor.update(
            state_0,
            cam_tf_array,
            self._camera_rays,
            color_image=self._color_buf,
            depth_image=self._depth_buf,
        )
