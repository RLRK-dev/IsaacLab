# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unclamp MPPI configuration for DA-MPPI demo generation.

Per ``m3_unclamp_design.md`` (2026-04-24) with CC 推奨 defaults for §6 Open
Questions 1-5 pending rs approval. Adapted from ``mpc_config_grip.py`` (G1
2026-04-22 + 2026-04-24) and ``mpc_config_ic.py`` (G1 2026-04-24) patterns.

Unclamp differs from Grip/IC/AC:
- **4D left-only action** (vs Grip 14D bimanual, IC 12D bimanual, AC 12D bimanual).
  Layout per env ``newton_unclamp_env.py:28-31``:
  ``[0] L finger Δopening × FINGER_STEP_SIZE, [1:4] L EE ΔXYZ × POS_ACTION_SCALE``
- **42D obs** unified with GC/Clamp/AR for SkillAdapter (vs IC 45D groove-relative).
- **Passive R arm** throughout episode (kinematic hold at initial pose).
- **Cost multiplicative** (finger × seated) + penalty terms (vs Grip/IC max-based).

Used by ``scripts/generate_demos_mppi_m3_unclamp.py`` (G3 per design spec §4).

SSOT references (``task_config.py``):
- ``T_GROOVE = 0.003`` (3mm): seated pos threshold
- ``T_SEAT = 0.85`` (cos ≈ 31.8°): seated ori threshold
- ``K_UNCLAMP = 5``: sustained steps for success
- ``UNCLAMP_TERMINAL_STEPS = 100``: max episode length
- ``FINGER_OPEN_POS = 0.04`` (40mm): finger fully open per joint
- ``FINGER_HALF_OPEN_POS = 0.006`` (6mm): half-open (P0 L finger starting pos per joint)
- ``FINGER_STEP_SIZE = 0.001`` (1mm/RL step)
"""

import math
from dataclasses import dataclass

from thread_isaac_lab.configs.mpc_config import MPPIConfig

# Derived: T_SEAT cos → arccos for angular cost denominator (same as IC)
_T_SEAT_COS = 0.85
_T_SEAT_RAD = math.acos(_T_SEAT_COS)  # 0.5548 rad ≈ 31.8°


@dataclass
class MPPIConfigUnclamp(MPPIConfig):
    """MPPI config for Unclamp demo generation on Newton VBD.

    Overrides base :class:`MPPIConfig` with Unclamp 4D action + multiplicative
    cost function (finger × seated) + H/replan tuned for UNCLAMP_TERMINAL_STEPS
    =100.
    """

    # =============================================================================
    # Success thresholds (SSOT: task_config.py)
    # =============================================================================
    # Unclamp success = finger_fully_open ∧ seated(T_GROOVE, T_SEAT, groove_bodies)
    # ∧ sustained(K_UNCLAMP=5). MPPI terminal eval uses pos/ori for seat + finger
    # opening for fully_open.
    success_threshold_m: float = 0.003  # T_GROOVE (SSOT: task_config.py:158)
    success_threshold_rad: float = _T_SEAT_RAD  # arccos(T_SEAT) (SSOT: task_config.py:159)
    # Finger success: opening_L >= 95% of 2 × FINGER_OPEN_POS = 0.076m (95% of 80mm).
    # Env check is opening_L ≈ FINGER_OPEN_POS × 2 (both joints at FULL_OPEN).
    success_threshold_finger_open_m: float = 0.076  # 0.95 × 2 × FINGER_OPEN_POS

    # =============================================================================
    # Action scales (env native, Phase 0 tune targets)
    # =============================================================================
    # L EE arm motion small (Unclamp does not require large EE travel, just
    # retreat from cable during finger open). Initial 0.01 = 10mm/step, smaller
    # than Grip approach (0.020) since bulk motion is not needed.
    pos_action_scale: float = 0.010  # [m/step] conservative, Phase 0 sweep {0.005, 0.010, 0.015}
    rot_action_scale: float = 0.05  # [rad/step] env default (small orientation change expected)

    # Unclamp 4D left-only action per env :28-31.
    # Layout: [finger_delta, L_pos_x, L_pos_y, L_pos_z]
    # Note: no rot component in env action; R arm passive.
    action_dim: int = 4

    # =============================================================================
    # MPPI horizon / replan (env UNCLAMP_TERMINAL_STEPS=100)
    # =============================================================================
    # H=20, replan=5 → 100 steps total = UNCLAMP_TERMINAL_STEPS.
    # Shorter H vs Grip H=25 since Unclamp task is simpler (finger open + small
    # retreat) and MPPI rollout doesn't need as long horizon.
    H: int = 20
    replan_interval: int = 5

    # =============================================================================
    # Cost scales (multiplicative + penalty per m3_unclamp_design.md §3.3)
    # =============================================================================
    # Base reward (maximize): r_finger_progress × r_seated
    # Added penalty terms (minimize):
    #   UNCLAMP_COST_SCALE × (pos_dist_L_seg + ori_dist_L_seg)  [tracking cost]
    #   CABLE_SEATED_COST_SCALE × (1 - r_seated)  [unseat catastrophe penalty]
    #
    # Phase 0 sweep candidates per §6 OQ:
    #   UNCLAMP_COST_SCALE {0.1, 0.5, 2.0}
    #   CABLE_SEATED_COST_SCALE {1.0, 5.0, 10.0}
    unclamp_cost_scale: float = 0.5  # tracking penalty weight
    cable_seated_cost_scale: float = 5.0  # unseat catastrophe weight
    # Inherit m3_cost_scale for tracking ori/pos equalization (reuse Grip/IC name)
    m3_cost_scale: float = 0.0054  # T_GROOVE / arccos(T_SEAT), same as IC insert mode

    # =============================================================================
    # Finger progress cost (Unclamp-specific)
    # =============================================================================
    # r_finger_progress = clip((opening_L - HALF_OPEN_SUM) / (FULL_OPEN_SUM - HALF_OPEN_SUM), 0, 1)
    # HALF_OPEN_SUM = 2 × FINGER_HALF_OPEN_POS = 0.012m
    # FULL_OPEN_SUM = 2 × FINGER_OPEN_POS = 0.080m
    # Rewards opening progress linearly from [HALF_OPEN, FULL_OPEN] range.
    finger_half_open_sum_m: float = 0.012  # 2 × FINGER_HALF_OPEN_POS=0.006
    finger_full_open_sum_m: float = 0.080  # 2 × FINGER_OPEN_POS=0.040

    # =============================================================================
    # IK objective weights (L arm only active; R passive)
    # =============================================================================
    # R arm passive → weight 0 (no ori objective).
    # L arm: default 0.5 (conservative for Unclamp which needs L finger + L EE only)
    l_ori_ik_weight: float = 0.5
    r_ori_ik_weight: float = 0.0  # passive

    # =============================================================================
    # Warm-start (P0 already proximal、direct MPPI)
    # =============================================================================
    # Unclamp P0: cable already in groove, L finger at HALF_OPEN. No warm-start
    # SLERP needed (0 descent, just finger open).
    warm_start_offset_m: float = 0.0

    def __post_init__(self) -> None:
        """Validate Unclamp-specific invariants.

        Raises:
            ValueError: if action_dim is not 4 (Unclamp left-only), or cost
                scale values are out of expected ranges.
        """
        if self.action_dim != 4:
            raise ValueError(
                f"Unclamp requires action_dim=4 (L finger_delta + L EE XYZ per env "
                f":28-31); got action_dim={self.action_dim}. "
                "Other action_dim values indicate config misuse (Grip=14, IC=12)."
            )
        if self.unclamp_cost_scale < 0 or self.unclamp_cost_scale > 10:
            raise ValueError(
                f"unclamp_cost_scale must be in [0, 10] range; got {self.unclamp_cost_scale}. "
                "Large values over-weight tracking vs finger progress."
            )
        if self.cable_seated_cost_scale < 0:
            raise ValueError(
                f"cable_seated_cost_scale must be ≥ 0; got {self.cable_seated_cost_scale}. "
                "Negative values reward unseating which defeats Unclamp purpose."
            )
        if self.finger_full_open_sum_m <= self.finger_half_open_sum_m:
            raise ValueError(
                f"finger_full_open_sum_m ({self.finger_full_open_sum_m}) must exceed "
                f"finger_half_open_sum_m ({self.finger_half_open_sum_m}). "
                "Unclamp progress requires full > half."
            )


def get_default_mppi_unclamp_config() -> MPPIConfigUnclamp:
    """Get default Unclamp MPPI configuration (CC 推奨 values).

    Use as entry point from M3-Unclamp generator main() for demo generation.
    All defaults match m3_unclamp_design.md §6 OQ CC 推奨 (rs approval pending per §9).
    """
    return MPPIConfigUnclamp()
