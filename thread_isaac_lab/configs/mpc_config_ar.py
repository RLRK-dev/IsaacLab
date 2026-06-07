# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""AR-specific MPPI configuration for aerial-regrasp demo generation."""

from dataclasses import dataclass

from thread_isaac_lab.configs.mpc_config import MPPIConfig


@dataclass
class MPPIConfigAR(MPPIConfig):
    """MPPI config for aerial-regrasp demo generation on Newton VBD.

    Overrides the M3 base :class:`MPPIConfig` with AR-tight success
    thresholds and re-asserts action scales matching
    ``newton_aerial_regrasp_env``. Used by
    ``scripts/generate_demos_mppi_m3_ar.py`` (Phase 6, M3 AR-compat).
    """

    # AR success thresholds (SSOT: task_config.py:153 T_DIST_APPROACH [m], :154 T_ALIGN [rad]).
    success_threshold_m: float = 0.012
    success_threshold_rad: float = 0.1745

    # AR action scales (SSOT: newton_aerial_regrasp_env.py:156 POS_ACTION_SCALE [m/step], :157 ROT_ACTION_SCALE [rad/step]).
    pos_action_scale: float = 0.015
    rot_action_scale: float = 0.05

    # Dual-arm full pose: R(pos3 + rot3) + L(pos3 + rot3) (SSOT: newton_aerial_regrasp_env.py:29-32).
    action_dim: int = 12

    # Phase 0 (2026-04-21) R1: AR cost scale (ori weight in max cost formula).
    # Default = T_DIST_APPROACH / T_ALIGN = 0.012 / 0.1745 ≈ 0.0688.
    # Phase 0 sweep values: 0.15 / 0.20 / 0.30 (boost ori cost contribution 2-4x).
    ar_cost_scale: float = 0.0688


def get_default_mppi_ar_config() -> MPPIConfigAR:
    """Get default MPPI configuration for AR demo generation."""
    return MPPIConfigAR()
