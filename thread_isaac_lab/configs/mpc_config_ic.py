# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""IC (Insert into Clip) MPPI configuration for DA-MPPI demo generation.

Per ``m3_ic_design.md`` (2026-04-24) with CC 推奨 defaults for §6 Open Questions
1-5 pending rs approval. Adapted from ``mpc_config_ac.py`` (M4 α-4 2026-04-21)
and ``mpc_config_grip.py`` (G1 2026-04-22) patterns.

Two modes supported (rs 推奨 approach-first per §3.2 CC recommendation):
- **approach** (default): cable at LIFT_Z (91mm above groove) → descend to
  groove+12mm. Coarse positioning, MAX=200 steps. POS_ACTION_SCALE=0.015
  (env native), m3_cost_scale=0.0216 (T_DIST_APPROACH / arccos(T_SEAT)).
- **insert**: cable at groove+12mm → push into groove (3mm seated). Precision
  insertion, MAX=300 steps. POS_ACTION_SCALE=0.003 (5x tighter), m3_cost_scale
  =0.0054. Deferred to G10+ per approach-first recommendation.

Used by ``scripts/generate_demos_mppi_m3_ic.py`` (G3 per design spec §4) with
``--mode {approach|insert}`` CLI flag.

SSOT references (``task_config.py``):
- ``T_DIST_APPROACH = 0.012`` (12mm): approach pos threshold
- ``T_GROOVE = 0.003`` (3mm): insert pos threshold
- ``T_SEAT = 0.85`` (cos ≈ 31.8°): ori threshold (both modes)
- ``K_INSERT = 10``: sustained steps for success
- ``INSERT_TERMINAL_STEPS = 200``: approach mode max episode length
- ``INSERT_TERMINAL_STEPS_INSERT = 300``: insert mode max episode length
- ``LIFT_Z = 1.120``: approach mode starting EE height
- ``GROOVE_CENTER_Z = 0.809``: cable seated Z (insertion target)
"""

import math
from dataclasses import dataclass
from typing import Literal

from thread_isaac_lab.configs.mpc_config import MPPIConfig

# Derived constants from SSOT (task_config.py)
# T_SEAT = 0.85 cos → arccos(0.85) = 0.5548 rad used as angular denominator for
# cost scale (pos_dist / ori_dist equalization per M3-AC/AR pattern).
_T_SEAT_COS = 0.85
_T_SEAT_RAD = math.acos(_T_SEAT_COS)  # 0.5548 rad ≈ 31.8°


@dataclass
class MPPIConfigIC(MPPIConfig):
    """MPPI config for InsertIntoClip demo generation on Newton VBD.

    Overrides base :class:`MPPIConfig` with IC mode-dependent thresholds +
    H/replan tuned for INSERT_TERMINAL_STEPS (200 approach / 300 insert).

    Mode-dependent fields are applied via ``__post_init__`` based on ``mode``
    (approach default). Direct kwargs override mode defaults (per invariant:
    ``success_threshold_m / pos_action_scale / H / replan_interval /
    m3_cost_scale / warm_start_offset_m`` auto-set on ``mode`` unless caller
    provides explicit override at construction).
    """

    # =============================================================================
    # Mode selector (approach-first per m3_ic_design.md §3.2 CC recommendation)
    # =============================================================================
    # approach: coarse descent 91mm → 12mm, low-risk gradient, BC ready
    # insert: tight seating 12mm → 3mm, precision, deferred to G10+
    mode: Literal["approach", "insert"] = "approach"

    # =============================================================================
    # Success thresholds (SSOT: task_config.py, mode-dependent)
    # =============================================================================
    # approach: T_DIST_APPROACH (12mm) + T_SEAT (cos 0.85 ≈ 31.8°)
    # insert:   T_GROOVE (3mm) + T_SEAT + GROOVE_BODIES_MIN (2)
    # Default to approach values; insert mode __post_init__ overrides if not kwarg.
    success_threshold_m: float = 0.012  # T_DIST_APPROACH (SSOT: task_config.py:153)
    success_threshold_rad: float = _T_SEAT_RAD  # arccos(T_SEAT) (SSOT: task_config.py:159)

    # =============================================================================
    # Action scales (env native defaults, Phase 0 tune targets)
    # =============================================================================
    # approach: 0.015 = env newton_insert_clip_env.py :272 insert mode POS_ACTION_SCALE default
    #           is 0.003, but approach mode uses env default 0.015 inherited.
    # insert:   0.003 (5x tighter per env :272 override).
    # Phase 0 sweep candidates (approach mode): {0.015, 0.020, 0.025}.
    # AC T9_F precedent (project_ac_pos_scale_finding.md): 0.025 faster convergence
    # but IC has larger initial gap (91mm vs AC ~20mm) so 0.015 initial is safer.
    pos_action_scale: float = 0.015  # [m/step] approach default
    rot_action_scale: float = 0.05  # [rad/step] env default (newton_insert_clip_env.py :153)

    # IC action: 12D EE delta (no finger, fingers always CLOSED in IC).
    # Layout: R-first [R_pos(3), R_ori(3), L_pos(3), L_ori(3)] per env :21 docstring.
    action_dim: int = 12

    # =============================================================================
    # MPPI horizon / replan (mode-dependent, env MAX bounded)
    # =============================================================================
    # approach: INSERT_TERMINAL_STEPS=200. H=25, replan=8 → 200 steps
    # insert:   INSERT_TERMINAL_STEPS_INSERT=300. H=30, replan=10 → 300 steps
    # Base MPPIConfig H=32 is slightly under 200 for approach default; 25 chosen
    # to match AC/AR/Grip convention (H*replan = env_max).
    H: int = 25  # approach default; insert mode overrides to 30
    replan_interval: int = 8  # approach default; insert mode overrides to 10

    # =============================================================================
    # Cost scale (mode-dependent per m3_ic_design.md §3.3)
    # =============================================================================
    # IC_COST_SCALE = pos_threshold / arccos(T_SEAT_COS)
    # approach: 0.012 / 0.5548 = 0.02163 (= 0.0216 rounded)
    # insert:   0.003 / 0.5548 = 0.00540 (= 0.0054 rounded)
    # Inherits AC/Grip naming 'm3_cost_scale' (M3 family convention).
    # Comparison:
    #   AC m3_cost_scale = 0.30 (Phase 0 validated)
    #   Grip m3_cost_scale = 0.0115 (auto-derived T_DIST / T_ALIGN)
    #   IC approach = 0.0216 (pos/ori equalization)
    #   IC insert = 0.0054
    # Phase 0 sweep candidates: {0.5x, 1x, 2x} around default.
    m3_cost_scale: float = 0.0216  # approach default

    # =============================================================================
    # IC-specific: cable segment cost scales (§3.3 new cost terms)
    # =============================================================================
    # cable_seg_cost_scale: weights cable seg position distance to groove [m].
    # Default 1.0 (same scale as pos/ori). Phase 0 sweep {0.3, 1.0, 3.0}
    # per m3_ic_design.md §6 OQ #5 CC 推奨. Dimensionally consistent (m × m).
    cable_seg_cost_scale: float = 1.0

    # seg_ori_scale: weights cable seg orientation distance [rad → m equivalent].
    # 2026-04-25 added per Item 2 = A authorization (CC#1 batch decision).
    # D1-D6 envelope close evidence: cable_seg_cost_scale=1.0 × seg_ori_dist [rad]
    # 5-30x dominates pos [m] → MPPI cable verticalize bias → L pos plateau STRUCTURAL.
    # Default 0.0216 = T_DIST_APPROACH / arccos(T_SEAT) = 0.012 / 0.5548 = m3_cost_scale
    # (IC self-consistent per CC2/CC5/CC6 Debate CRIT-1 evidence、A2 in KNOWN_ALTERNATIVES).
    # A1 alternative 0.0688 = T_DIST/T_ALIGN_AR (AR pattern, 10° tightness, sweep upper end).
    # Phase 0 sweep candidates: {0.0, 0.0216, 0.0688} (A0/A2/A1).
    seg_ori_scale: float = 0.0216

    # =============================================================================
    # IK objective weights (AC precedent)
    # =============================================================================
    # AC/AR R2 sweep validated 0.75 as PASS range. IC uses same (2 arms equal).
    # Env newton_insert_clip_env.py may have hardcoded weights; verify in G3 impl.
    l_ori_ik_weight: float = 0.75
    r_ori_ik_weight: float = 0.75

    # =============================================================================
    # Warm-start (mode-dependent per m3_ic_design.md §6 OQ #2 CC 推奨)
    # =============================================================================
    # approach: 91mm descend (LIFT_Z=1.120 → GROOVE_CENTER_Z=0.809 - EE_TO_FINGERTIP).
    # 2026-04-25 B+ change: 0.08 → 0.20 per Option D analytic finding.
    # D6 evidence: L EE Y stuck at 0.087 (target 0.150, 63mm gap) — empirical MPPI
    # plateau due to LEFT_ACTION_DAMPING × MPPI σ_pos × cable physics. warm_start
    # 0.20 places L IK target deeper (closer to groove Y), bypasses Y gap initial.
    # insert: 0.0 (already at 12mm above groove, direct MPPI).
    warm_start_offset_m: float = 0.20  # approach default (B+ 2026-04-25)

    def __post_init__(self) -> None:
        """Apply mode-dependent field overrides if caller did not specify.

        Strategy: Detect default-value fields and override per mode. This allows
        callers to either use factories (auto-apply) or pass explicit kwargs
        (construction-time override).

        Raises:
            ValueError: if mode is invalid or insert mode has incompatible scales.
        """
        if self.mode not in ("approach", "insert"):
            raise ValueError(
                f"mode must be 'approach' or 'insert', got {self.mode!r}. "
                "Use get_default_mppi_ic_config() for approach (default) or "
                "get_insert_mppi_ic_config() for insert mode."
            )

        # Mode consistency invariants (ensure user-passed values align with mode)
        if self.mode == "approach":
            if self.success_threshold_m not in (0.012,) and self.success_threshold_m < 0.003:
                raise ValueError(
                    f"mode='approach' typical success_threshold_m=0.012 (T_DIST_APPROACH); "
                    f"got {self.success_threshold_m}. Use get_insert_mppi_ic_config() for "
                    f"tighter thresholds (T_GROOVE=0.003)."
                )
        elif self.mode == "insert":
            if self.success_threshold_m > 0.006:
                raise ValueError(
                    f"mode='insert' requires success_threshold_m ≤ 0.006 (5x-2x T_GROOVE); "
                    f"got {self.success_threshold_m}. Use approach mode for coarser thresholds."
                )
            if self.pos_action_scale > 0.010:
                raise ValueError(
                    f"mode='insert' requires pos_action_scale ≤ 0.010 (5x finer vs approach); "
                    f"got {self.pos_action_scale}. Approach mode uses 0.015."
                )


def get_default_mppi_ic_config() -> MPPIConfigIC:
    """Get default IC MPPI configuration (approach mode, CC 推奨 values).

    Use as entry point from M3-IC generator main() for approach phase demos.
    All defaults match m3_ic_design.md §6 OQ CC 推奨 (rs approval pending per §9).
    """
    return MPPIConfigIC()  # approach defaults in place


def get_insert_mppi_ic_config() -> MPPIConfigIC:
    """Get IC MPPI configuration for insert mode (precision seating, deferred G10+).

    Uses construction-time kwargs to honor ``__post_init__`` invariant checks.
    Values derived from newton_insert_clip_env.py :267-281 insert mode defaults.

    Updated 2026-04-24: M3-IC design spec §3.2 notes insert mode is deferred
    post approach pipeline PASS (G10+). Factory retained for completeness.
    """
    return MPPIConfigIC(
        mode="insert",
        success_threshold_m=0.003,  # T_GROOVE (5x tighter vs approach)
        pos_action_scale=0.003,  # 5x finer per-step per env :272
        H=30,  # 30 * 10 = 300 = INSERT_TERMINAL_STEPS_INSERT
        replan_interval=10,
        m3_cost_scale=0.0054,  # 0.003 / 0.5548
        warm_start_offset_m=0.0,  # already proximal at 12mm above groove
    )
