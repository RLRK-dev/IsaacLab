# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""D2 texture + D3 cable color variation skeleton (Tier 0b).

Approach (LL-Vision-DR-Design.md §2.1):
    - D2 texture: 5 preset material variations
      (mat_smooth / mat_matte / mat_glossy / mat_scratched / mat_dirty).
      Per-episode swap via offline pre-rendered dataset variants — Newton
      material rebuild per episode is prohibitive (R-DR-1).
    - D3 cable color: 5 preset RGB triples applied via Newton model body shape
      color override; sim-default monochromatic → randomized at episode reset.

Why two classes in one module:
    Both dims share the offline pre-render dataset access path (texture asset
    bundle + cable shape body lookup), so co-locating their dataset I/O reduces
    duplicate cache wiring at impl phase.

Status:
    Skeleton only (bodies raise NotImplementedError). Impl-phase responsibilities:
        D2: dataset-variant selector (offline pre-render lookup) keyed by env_id
        D3: Newton body color override (per-segment RGB application path)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

    from thread_isaac_lab.configs.vision_dr_config import VisionDRConfig


class MaterialVariation:
    """D2 texture preset variation (Tier 0b).

    Backed by offline pre-rendered dataset variants (5 material presets).
    Per-episode selection avoids Newton material rebuild (R-DR-1).

    Args:
        config: shared :class:`VisionDRConfig` (uses ``d2_material_presets``).
        num_envs: vectorized env count.
        device: torch device for selection index tensor.
    """

    def __init__(self, config: VisionDRConfig, num_envs: int, device: str | torch.device) -> None:
        self._config = config
        self._num_envs = num_envs
        self._device = device

    def sample_per_env(self, env_ids: torch.Tensor) -> None:
        """Sample material preset index for each reset env.

        Args:
            env_ids: indices of envs being reset, shape ``[num_reset]``, int64.
        """
        raise NotImplementedError("Impl-phase: random.choice from d2_material_presets per env.")

    def select_dataset_variant(self, env_ids: torch.Tensor) -> torch.Tensor:
        """Map env preset index to dataset-variant index for offline pre-render lookup.

        Args:
            env_ids: env indices, shape ``[num_envs]``, int64.

        Returns:
            Dataset-variant index per env, shape ``[num_envs]``, int64.
        """
        raise NotImplementedError(
            "Impl-phase: lookup table from preset string -> dataset variant id; "
            "consume by Tier 0b dataset loader (T-Vision-CableState shared re-render)."
        )


class CableColorOverride:
    """D3 cable color variation (Tier 0b).

    Applies one of 5 preset RGB triples (linear sRGB, [0, 1]) to the cable
    body shape via Newton body color override at episode reset.

    Args:
        config: shared :class:`VisionDRConfig` (uses ``d3_cable_color_presets``).
        num_envs: vectorized env count.
        device: torch device for color tensor.
    """

    def __init__(self, config: VisionDRConfig, num_envs: int, device: str | torch.device) -> None:
        self._config = config
        self._num_envs = num_envs
        self._device = device

    def sample_per_env(self, env_ids: torch.Tensor) -> None:
        """Sample cable color preset for each reset env.

        Args:
            env_ids: indices of envs being reset, shape ``[num_reset]``, int64.
        """
        raise NotImplementedError("Impl-phase: random.choice from d3_cable_color_presets per env.")

    def apply_to_cable_shape(self, env_ids: torch.Tensor) -> None:
        """Apply sampled RGB to the cable body shape via Newton API.

        Args:
            env_ids: env indices being reset, shape ``[num_reset]``, int64.

        Notes:
            Newton body color override is a per-shape (not per-segment) call —
            apply once per cable body across all 40 segments
            (LL-Vision-DR-Design.md §9.3, ``task_config.py:70-71`` ``CABLE_SEGMENTS=40``;
            this skeleton does not import task_config).
        """
        raise NotImplementedError(
            "Impl-phase: Newton model body shape color set call; "
            "verify all CABLE_SEGMENTS share the override (single body, multi-shape)."
        )
