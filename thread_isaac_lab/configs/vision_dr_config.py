# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Vision Domain Randomization config SSOT (skeleton, prep design phase).

DR-only parameters (D1-D8 taxonomy + tier flags + curriculum thresholds).
Cable / clip / robot geometry SSOT remains ``thread_isaac_lab.configs.task_config``;
this module is disjoint and only owns DR-specific values.

References:
    - LL-Vision-DR-Design.md §4.3 (verbatim dataclass outline, lines 174-200)
    - LL-Vision-DR-Design.md §2.1 (D1-D5 parameter ranges)
    - LL-Vision-DR-Design.md §2.3 + §2.4 (D7-D8 Tier 2 OUT-OF-SCOPE + D8 promote trigger)
    - LL-Vision-DR-Impl-8DimMap.md (impl entry-point map)

Status:
    Skeleton (prep design phase, T-Vision-DR-Impl-Phase0-PrepDesign).
    Field shapes / defaults are authoritative (impl phase copies verbatim).
    Wiring into envs is deferred to impl spawn (T-Vision-Pose + T-Vision-CableState ready trigger).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# D1 lighting preset sets (Tier 0c, design memo §2.1)
D1_INTENSITY_DEFAULT: tuple[float, ...] = (0.5, 0.75, 1.0, 1.5, 2.0)
D1_COLOR_TEMP_DEFAULT: tuple[int, ...] = (3000, 4000, 5000, 6000, 6500)  # [K]

# D2 texture preset names (Tier 0b, design memo §2.1)
D2_MATERIAL_PRESETS: tuple[str, ...] = (
    "mat_smooth",
    "mat_matte",
    "mat_glossy",
    "mat_scratched",
    "mat_dirty",
)

# D3 cable color preset RGB (Tier 0b, design memo §2.1; values in [0, 1] linear sRGB)
D3_CABLE_COLOR_PRESETS: tuple[tuple[float, float, float], ...] = (
    (0.05, 0.05, 0.05),  # near-black
    (0.70, 0.10, 0.10),  # red
    (0.10, 0.10, 0.70),  # blue
    (0.70, 0.70, 0.10),  # yellow
    (0.50, 0.50, 0.50),  # neutral grey (custom user-spec slot)
)

# D6 background variation preset names (Tier 1, design memo §2.2 + Phase 1 LL-Vision-DR-Tier1-D6-Design.md §2)
# Names are identifiers consumed by Isaac Lab AssetBaseCfg load at impl phase.
# 10 preset count per design memo §2.2; reducible to 5 via d6_background_preset_count (OQ-DR-2).
D6_BACKGROUND_PRESETS: tuple[str, ...] = (
    "bg_empty_baseline",  # no clutter baseline (sim default reference)
    "bg_wall_back",  # vertical wall behind work area
    "bg_wall_side",  # side wall
    "bg_monitor_lcd",  # LCD monitor beside work area
    "bg_additional_table",  # second table beside work area
    "bg_shelf_unit",  # storage shelf with random objects
    "bg_cable_pile",  # extra cables piled aside
    "bg_paper_stack",  # papers / manuals stack
    "bg_toolbox",  # closed toolbox on table edge
    "bg_equipment_rack",  # generic lab equipment rack
)

TierLabel = Literal["0a", "0b", "0c", "1"]


@dataclass
class VisionDRConfig:
    """Vision DR config (8-dim taxonomy + tier flags + curriculum thresholds).

    Tier-gated activation flags enforce the curriculum order
    (Tier 0a → 0b → 0c → 1) defined in LL-Vision-DR-Design.md §3.1.
    Defaults reflect Tier 0a (D4 + D5 only) for warm-up.
    """

    # --- Tier selector -------------------------------------------------
    tier: TierLabel = "0a"

    # --- Enable flags (gated by tier; impl-phase logic in DRCurriculum) -
    enable_d1_lighting: bool = False  # Tier 0c+
    enable_d2_texture: bool = False  # Tier 0b+
    enable_d3_cable_color: bool = False  # Tier 0b+
    enable_d4_intrinsic: bool = True  # Tier 0a+
    enable_d5_noise: bool = True  # Tier 0a+
    enable_d6_background: bool = False  # Tier 1+

    # --- Tier 2 reserved flags (OUT-OF-SCOPE, L1.F.1 trigger) ---------
    # See LL-Vision-DR-Design.md §2.3. Kept as fields so the impl map and the
    # D8 promote trigger (§2.4) can reference them without a future schema bump.
    enable_d7_motion_blur: bool = False  # OUT-OF-SCOPE (Tier 2)
    enable_d8_occlusion: bool = False  # OUT-OF-SCOPE (Tier 2); promote candidate per §2.4

    # --- D1 lighting parameter ranges (Tier 0c) ------------------------
    d1_intensity_set: tuple[float, ...] = field(default_factory=lambda: tuple(D1_INTENSITY_DEFAULT))
    d1_color_temp_set: tuple[int, ...] = field(default_factory=lambda: tuple(D1_COLOR_TEMP_DEFAULT))

    # --- D2 + D3 preset references (Tier 0b; not jittered, sampled) ----
    d2_material_presets: tuple[str, ...] = field(default_factory=lambda: tuple(D2_MATERIAL_PRESETS))
    d3_cable_color_presets: tuple[tuple[float, float, float], ...] = field(
        default_factory=lambda: tuple(D3_CABLE_COLOR_PRESETS)
    )

    # --- D4 camera intrinsic ranges (Tier 0a) --------------------------
    d4_fov_jitter_deg: float = 5.0  # ± [deg]
    d4_principal_jitter_px: int = 5  # ± [px]
    d4_distortion_set: tuple[float, ...] = (-0.05, 0.0, 0.05)  # k1 coefficient

    # --- D5 sensor noise ranges (Tier 0a) ------------------------------
    d5_depth_sigma_m: float = 0.003  # depth additive Gaussian σ [m]
    d5_depth_dropout: float = 0.05  # per-pixel dropout [unitless, 0..1]
    d5_color_sigma: float = 0.02  # RGB additive Gaussian σ [unitless, 0..1]
    d5_chromatic_shift_px: int = 2  # ± [px]

    # --- D6 background variation (Tier 1) ------------------------------
    d6_background_preset_count: int = 10  # number of clutter scenes used; reduction to 5 = OQ-DR-2
    d6_background_presets: tuple[str, ...] = field(default_factory=lambda: tuple(D6_BACKGROUND_PRESETS))

    # --- Curriculum thresholds (LL-Vision-DR-Design.md §3.2) -----------
    plateau_window_iters: int = 100_000  # plateau detection window [iter]
    plateau_eps: float = 0.01  # plateau Δ tolerance [pp / 100k iters]
    plateau_consecutive: int = 2  # consecutive windows required to advance
    value_loss_explode_ratio: float = 3.0  # rollback trigger vs baseline (CC4 v3.2 E.6)

    def __post_init__(self) -> None:
        """Tier-flag consistency check (Tier 2 fields must remain disabled by default).

        Impl phase: extend with full tier→enable gating sanity (raise on illegal combos).
        """
        if self.enable_d7_motion_blur or self.enable_d8_occlusion:
            # D7/D8 are OUT-OF-SCOPE for this leaf goal. Enabling them requires an
            # explicit D8 promote trigger evaluation (LL-Vision-DR-Design.md §2.4).
            raise NotImplementedError(
                "D7/D8 are Tier 2 OUT-OF-SCOPE for T-Vision-DR leaf goal. "
                "Enabling requires §2.4 promote trigger evaluation; impl in a separate task."
            )
