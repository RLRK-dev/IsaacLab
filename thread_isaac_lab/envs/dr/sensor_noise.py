# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""D5 sensor noise injection skeleton (Tier 0a).

Approach (LL-Vision-DR-Design.md §2.1):
    - Depth additive Gaussian σ = 3 [mm] @ 1 [m]
    - Depth per-pixel dropout 5% (cable-region floor preserved per R-DR-4)
    - Color additive Gaussian σ = 0.02 channel-wise
    - Chromatic shift ± 2 [px]

Integration entry:
    Torch-level injection on already-rendered tensors after the wrist camera
    manager update step (so depth ground truth and rendered color are consumed
    after randomization). This skeleton does NOT import the camera manager —
    wiring is deferred to impl spawn.

Cable preservation (R-DR-4):
    Depth dropout must preserve the cable region ("cable preservation floor")
    so the policy still receives signal where the task-critical asset lives.
    Impl-phase responsibility: a cable-region mask gate before applying dropout.

Status:
    Stub only (body raises NotImplementedError).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

    from thread_isaac_lab.configs.vision_dr_config import VisionDRConfig


class SensorNoise:
    """Depth + color noise injection (D5, Tier 0a).

    Args:
        config: shared :class:`VisionDRConfig` (uses ``d5_depth_sigma_m``,
            ``d5_depth_dropout``, ``d5_color_sigma``, ``d5_chromatic_shift_px``).
        num_envs: vectorized env count.
        device: torch device.
    """

    def __init__(self, config: VisionDRConfig, num_envs: int, device: str | torch.device) -> None:
        self._config = config
        self._num_envs = num_envs
        self._device = device

    def apply_depth(
        self,
        depth_tensor: torch.Tensor,
        cable_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Apply additive Gaussian + dropout to depth.

        Args:
            depth_tensor: ground-truth depth, shape ``[num_envs, H, W]``, float [m].
            cable_mask: per-pixel cable-region mask, shape ``[num_envs, H, W]``, bool.
                When provided, dropout is suppressed inside the mask (R-DR-4).

        Returns:
            Noised depth, same shape and dtype.
        """
        raise NotImplementedError(
            "Impl-phase: depth + N(0, d5_depth_sigma_m) [m]; "
            "Bernoulli dropout at d5_depth_dropout, masked-out outside cable_mask."
        )

    def apply_color(self, rgb_tensor: torch.Tensor) -> torch.Tensor:
        """Apply additive Gaussian + chromatic shift to RGB.

        Args:
            rgb_tensor: rendered RGB, shape ``[num_envs, H, W, 3]``, float in [0, 1].

        Returns:
            Noised RGB, same shape and dtype, clamped to [0, 1].
        """
        raise NotImplementedError(
            "Impl-phase: rgb + N(0, d5_color_sigma) per channel; "
            "per-channel translate ±d5_chromatic_shift_px [px]; clamp to [0, 1]."
        )
