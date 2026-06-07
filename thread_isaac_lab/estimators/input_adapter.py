# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Pose estimator input adapter — env-side bridge to estimator core (R6 boundary).

Per v3.2 Appendix H + Round 2 v2.1 patch P3:

- ``CameraProvider`` and ``KinematicsProvider`` are narrow Protocols exposing
  pre-sliced tensors only. They do **not** expose Newton ``body_q`` or body
  indexing. Env-side adapters (MVP-0B scope) implement these Protocols.
- ``_split_pose7`` is the canonical helper to split a 7-vector
  ``(px, py, pz, qx, qy, qz, qw)`` into (xyz, quat-xyzw) tensors.
- ``PoseEstimatorInputAdapter.assemble`` returns a step_id fingerprint
  alongside ``EstimatorInputs`` for v3 §5.1 frame-alignment verification.

R6 module boundary: this module imports from
``thread_isaac_lab.estimators.types`` only — never from ``newton`` or any
``thread_isaac_lab.envs.*``.
"""

from typing import Protocol

import torch

from thread_isaac_lab.estimators.types import EstimatorInputs


class CameraProvider(Protocol):
    """Minimal camera tensor interface (no SensorTiledCamera direct exposure)."""

    @property
    def rgb_l(self) -> torch.Tensor:
        """[B, 3, H, W_img] RGB normalized to [0, 1]."""
        ...

    @property
    def depth_l(self) -> torch.Tensor:
        """[B, 1, H, W_img] depth in meters."""
        ...


class KinematicsProvider(Protocol):
    """Pre-sliced robot kinematics — no Newton body_q or body_index leak (v2.1 P3)."""

    @property
    def wrist_pose_l(self) -> torch.Tensor:
        """[B, 7] (px py pz qx qy qz qw) for the wrist_L body, env-side derived."""
        ...

    @property
    def finger_positions(self) -> torch.Tensor:
        """[B, 2, 3] world xyz for (left, right) fingertips, env-side derived."""
        ...

    @property
    def joint_state(self) -> torch.Tensor:
        """[B, J] arm joint positions (and optionally velocities)."""
        ...


def _split_pose7(pose7: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Split a pose7 tensor into (xyz, quat-xyzw) contiguous tensors.

    Convention: ``[px, py, pz, qx, qy, qz, qw]`` (matches Newton ``body_q``).

    Args:
        pose7: [..., 7] tensor with the documented packing order.

    Returns:
        ``(xyz, quat)`` where ``xyz`` is ``[..., 3]`` and ``quat`` is
        ``[..., 4]`` (xyzw). Both are :meth:`torch.Tensor.contiguous` so they
        can be safely passed to :func:`warp.from_torch` without silent copies.

    Raises:
        ValueError: if the last dimension is not 7.
    """
    if pose7.shape[-1] != 7:
        raise ValueError(f"Expected last dim 7 (px py pz qx qy qz qw), got shape {tuple(pose7.shape)}")
    return pose7[..., :3].contiguous(), pose7[..., 3:7].contiguous()


class PoseEstimatorInputAdapter:
    """Bridges (CameraProvider, KinematicsProvider) -> :class:`EstimatorInputs`.

    The single boundary that bridges env-side tensors to estimator core inputs
    (see v3.2 Appendix H.5 sim-to-real rationale: in real deployment, the
    Provider implementations swap to RealSense + robot joint reader without
    touching :class:`PoseEstimatorCorePhase1`).
    """

    def __init__(self, camera: CameraProvider, kinematics: KinematicsProvider) -> None:
        self._cam = camera
        self._kinematics = kinematics

    def assemble(
        self,
        routing_target_seg_idx: torch.Tensor,
        routing_target_clip_idx: torch.Tensor,
        step_id: int,
    ) -> tuple[EstimatorInputs, int]:
        """Assemble :class:`EstimatorInputs` and return a step_id fingerprint.

        ``step_id`` is a monotonic integer that the caller uses to verify
        frame alignment between the camera render snapshot and the kinematics
        snapshot (v3 §5.1 frame-alignment contract).

        Args:
            routing_target_seg_idx: [B] long, target cable segment per world.
            routing_target_clip_idx: [B] long, target clip per world.
            step_id: monotonic snapshot fingerprint.

        Returns:
            ``(EstimatorInputs, step_id)``.
        """
        return (
            EstimatorInputs(
                rgb_l=self._cam.rgb_l,
                depth_l=self._cam.depth_l,
                joint_state=self._kinematics.joint_state,
                wrist_camera_pose_l=self._kinematics.wrist_pose_l,
                finger_positions=self._kinematics.finger_positions,
                routing_target_seg_idx=routing_target_seg_idx,
                routing_target_clip_idx=routing_target_clip_idx,
            ),
            step_id,
        )
