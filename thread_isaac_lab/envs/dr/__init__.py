# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Vision Domain Randomization module skeletons (D1-D6 active, Tier 2 OUT-OF-SCOPE).

Module layout (LL-Vision-DR-Design.md §4.1, lines 145-158 + Phase 1 D6 addition):
    - lighting_variation   : D1 lighting (Tier 0c)
    - material_variation   : D2 texture + D3 cable color (Tier 0b)
    - camera_intrinsic     : D4 FOV / principal / distortion (Tier 0a)
    - sensor_noise         : D5 depth / color noise (Tier 0a)
    - background_variation : D6 background clutter (Tier 1)

Tier 2 dims (D7 motion blur, D8 self-occlusion) are OUT-OF-SCOPE for this leaf
(L1.F.1 trigger 経で別 task) — see LL-Vision-DR-Design.md §2.3 + §2.4.

Phase progression:
    Phase 0 (T-Vision-DR-Impl-Phase0-PrepDesign, 2026-05-04T03:25)
        D1-D5 skeleton + 8DimMap design memo
    Phase 1 (T-Vision-DR-Impl-Phase1-D6-Background-Design, 2026-05-04T03:50)
        D6 skeleton + Tier 0→1 transition spec + Tier 1 eval gate (LL-Vision-DR-Tier1-D6-Design.md)

Status:
    Skeleton only (prep design phase). All bodies raise NotImplementedError.
    Wiring into envs is deferred to impl spawn.
"""

from .background_variation import BackgroundVariation
from .camera_intrinsic import CameraIntrinsicJitter
from .lighting_variation import LightingVariation
from .material_variation import CableColorOverride, MaterialVariation
from .sensor_noise import SensorNoise

__all__ = [
    "BackgroundVariation",
    "CableColorOverride",
    "CameraIntrinsicJitter",
    "LightingVariation",
    "MaterialVariation",
    "SensorNoise",
]
