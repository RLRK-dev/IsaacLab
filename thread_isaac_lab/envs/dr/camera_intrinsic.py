# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""D4 camera intrinsic jitter skeleton (Tier 0a).

Approach (LL-Vision-DR-Design.md §2.1):
    - FOV: 45° baseline ± 5° (range 40-50°)
    - Principal point: ± 5 [px] translation from image center
    - k1 distortion coefficient sampled from {-0.05, 0.0, 0.05}
    - Per-episode camera ray rebuild at reset (cheap, ~ms per episode, R-DR-5)

Integration entry:
    The intended impl-phase wiring point is the wrist camera ray rebuild
    inside ``thread_isaac_lab.envs.wrist_camera_manager`` (lines 90-104,
    ``compute_pinhole_camera_rays``). This skeleton does NOT import the
    camera manager — wiring is deferred to impl spawn to keep the module
    self-contained during prep design.

Status:
    Stub only (body raises NotImplementedError).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

    from thread_isaac_lab.configs.vision_dr_config import VisionDRConfig


class CameraIntrinsicJitter:
    """Per-episode FOV / principal / distortion jitter (D4, Tier 0a).

    Args:
        config: shared :class:`VisionDRConfig` (uses ``d4_fov_jitter_deg``,
            ``d4_principal_jitter_px``, ``d4_distortion_set``).
        num_envs: vectorized env count.
        device: torch device.
    """

    def __init__(self, config: VisionDRConfig, num_envs: int, device: str | torch.device) -> None:
        self._config = config
        self._num_envs = num_envs
        self._device = device

    def sample_per_env(self, env_ids: torch.Tensor) -> None:
        """Sample (fov_deg, principal_offset, k1) for each reset env.

        Args:
            env_ids: indices of envs being reset, shape ``[num_reset]``, int64.
        """
        raise NotImplementedError(
            "Impl-phase: uniform sample fov in [45-5, 45+5] [deg]; "
            "uniform sample principal offset in [-5, 5] [px] (x and y independent); "
            "discrete sample k1 from d4_distortion_set."
        )

    def rebuild_camera_rays(self, env_ids: torch.Tensor) -> None:
        """Rebuild per-env pinhole camera rays with jittered intrinsics.

        Args:
            env_ids: env indices being reset, shape ``[num_reset]``, int64.
        """
        raise NotImplementedError(
            "Impl-phase: extend WristCameraManager with update_intrinsics(fov_deg, "
            "principal_offset, distortion_k1); call compute_pinhole_camera_rays per env. "
            "(LL-Vision-DR-Design.md §4.4: ~15 LoC extension on wrist_camera_manager.py)"
        )
