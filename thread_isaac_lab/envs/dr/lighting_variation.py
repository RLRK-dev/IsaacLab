# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""D1 lighting variation skeleton (Tier 0c).

Approach: post-render multiplicative RGB scaling + color-temperature warp.
Per-episode lighting is drawn from preset sets defined in
:class:`thread_isaac_lab.configs.vision_dr_config.VisionDRConfig`
(``d1_intensity_set`` and ``d1_color_temp_set``).

Why post-render (not Newton scene-light edit):
    Newton ``default_light`` lifecycle requires scene rebuild for runtime intensity
    change (LL-Vision-DR-Design.md §2.1, ``wrist_camera_manager.py:93-94``).
    Multiplicative scaling on the rendered RGB tensor matches the calibrated
    Tier 0c protocol cheaply.

Status:
    Skeleton only (body raises NotImplementedError). Impl-phase responsibility:
        1. sample (intensity, color_temp) per env at episode reset
        2. apply scale + Planck-locus chromatic shift on rgb_tensor post-render
        3. preserve depth tensor (depth is unaffected by lighting)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

    from thread_isaac_lab.configs.vision_dr_config import VisionDRConfig


class LightingVariation:
    """Post-render RGB scaling + color-temperature warp (D1, Tier 0c).

    Args:
        config: shared :class:`VisionDRConfig` (uses ``d1_intensity_set`` and
            ``d1_color_temp_set``).
        num_envs: vectorized env count (per-env independent sample).
        device: torch device for scaling tensors (matches camera output device).
    """

    def __init__(self, config: VisionDRConfig, num_envs: int, device: str | torch.device) -> None:
        self._config = config
        self._num_envs = num_envs
        self._device = device

    def sample_per_env(self, env_ids: torch.Tensor) -> None:
        """Sample (intensity, color_temp) for each reset env.

        Args:
            env_ids: indices of envs being reset, shape ``[num_reset]``, int64.
        """
        raise NotImplementedError("Impl-phase: random.choice from preset sets per env.")

    def apply(self, rgb_tensor: torch.Tensor) -> torch.Tensor:
        """Apply intensity + color-temp warp to rendered RGB.

        Args:
            rgb_tensor: rendered RGB, shape ``[num_envs, H, W, 3]``, float in [0, 1].

        Returns:
            Warped RGB, same shape and dtype.
        """
        raise NotImplementedError(
            "Impl-phase: per-env multiplicative scale + Planck-locus chromatic shift; "
            "ensure clamp to [0, 1] post-multiplication."
        )
