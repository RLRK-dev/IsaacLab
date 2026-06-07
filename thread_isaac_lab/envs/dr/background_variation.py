# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""D6 background variation skeleton (Tier 1).

Approach (LL-Vision-DR-Design.md §2.2 + LL-Vision-DR-Tier1-D6-Design.md §2):
    - 10 preset clutter scenes (default; reducible to 5 via OQ-DR-2)
    - Per-env preset selection at episode reset
    - Isaac Lab ``AssetBaseCfg`` USD asset load for clutter geometry
      (see ``isaaclab.assets.AssetBaseCfg``)
    - Tier 1 follows Tier 0 PASS gate (D1-D5 mandatory; see design memo §3.1)

Integration entry:
    The Tier 1 impl-phase wiring point is the per-env scene assembly hook
    inside the dual-arm Newton env at episode reset. This skeleton does NOT
    import the env file — wiring is deferred to Tier 1 impl spawn to keep
    the module self-contained during prep design.

Why module separate from D2 / D3 (texture / cable color):
    D2 / D3 use offline pre-rendered dataset variants (texture asset bundle).
    D6 uses runtime ``AssetBaseCfg`` instantiation in the env scene graph
    (different lifecycle: spawned at scene build, not loaded from cached frames).
    Co-locating with D2 / D3 would conflate two distinct asset pipelines.

Wrist FOV constraint (LL-Vision-DR-Tier1-D6-Design.md §6 R-DR-T1-1):
    Both wrist cameras observe at z ~1.6 m looking down. Background clutter
    must occupy the visible portion of that FOV — assets placed entirely
    outside the wrist cone yield zero DR signal. Tier 1 impl phase asset
    placement is constrained by this geometry; skeleton does NOT import
    ``wrist_camera_manager`` (constraint is design-time, not runtime).

Status:
    Skeleton only (body raises NotImplementedError). Impl-phase responsibilities:
        1. sample preset index per env at episode reset
        2. resolve preset name → USD asset path (via Isaac Lab asset registry)
        3. instantiate ``AssetBaseCfg`` into env scene at the resolved pose
        4. clean up old clutter assets between episodes (avoid scene leak)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

    from thread_isaac_lab.configs.vision_dr_config import VisionDRConfig


class BackgroundVariation:
    """Per-episode background clutter variation (D6, Tier 1).

    Args:
        config: shared :class:`VisionDRConfig` (uses ``d6_background_presets`` and
            ``d6_background_preset_count``).
        num_envs: vectorized env count (per-env independent preset selection).
        device: torch device for selection-index tensor.
    """

    def __init__(self, config: VisionDRConfig, num_envs: int, device: str | torch.device) -> None:
        self._config = config
        self._num_envs = num_envs
        self._device = device

    def sample_per_env(self, env_ids: torch.Tensor) -> None:
        """Sample background preset index for each reset env.

        Args:
            env_ids: indices of envs being reset, shape ``[num_reset]``, int64.

        Notes:
            Discrete uniform sample from
            ``config.d6_background_presets[: config.d6_background_preset_count]``.
            The slice supports the OQ-DR-2 reduction path (10 → 5) without
            mutating the preset list.
        """
        raise NotImplementedError(
            "Impl-phase: discrete uniform sample preset index in "
            "[0, d6_background_preset_count) per env; persist on self for "
            "subsequent load_clutter_assets / apply_to_scene calls."
        )

    def load_clutter_assets(self, env_ids: torch.Tensor) -> None:
        """Resolve preset name → USD asset and prepare ``AssetBaseCfg`` per env.

        Args:
            env_ids: env indices being reset, shape ``[num_reset]``, int64.

        Notes:
            Impl-phase responsibility: maintain a preset-name → USD-path
            registry (proposed location: ``thread_isaac_lab/configs/dr_assets.py``
            keyed by ``D6_BACKGROUND_PRESETS`` entries). Use Isaac Lab
            :class:`isaaclab.assets.AssetBaseCfg` (verified at
            ``source/isaaclab/isaaclab/assets/asset_base_cfg.py:16``) to
            describe each clutter scene before scene-graph attachment.
        """
        raise NotImplementedError(
            "Impl-phase: load preset USD per env via AssetBaseCfg(usd_path=..., "
            "init_state=AssetBaseCfg.InitialStateCfg(pos=...)); see "
            "isaaclab.scene.interactive_scene_cfg lines 62-65 for canonical usage."
        )

    def apply_to_scene(self, env_ids: torch.Tensor) -> None:
        """Attach loaded clutter assets to the per-env scene at episode start.

        Args:
            env_ids: env indices being reset, shape ``[num_reset]``, int64.

        Notes:
            Old clutter from prior episode must be detached / hidden first
            (avoid scene leak). Wrist FOV constraint (see module docstring):
            asset poses must place geometry inside the wrist cone for the
            randomization to produce signal.
        """
        raise NotImplementedError(
            "Impl-phase: detach prior episode's clutter; attach new AssetBaseCfg "
            "per env at pose chosen to remain in wrist FOV (z ~1.6 m down-look). "
            "No env file modification beyond the explicit reset hook (TOUCH FORBIDDEN "
            "newton_*_env.py beyond the documented hook point)."
        )
