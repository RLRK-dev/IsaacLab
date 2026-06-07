# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Grip-specific MPPI configuration for Clamp demo generation.

Per `m3_grip_design.md` (2026-04-22 initial / 2026-04-24 §6-3 rev) with rs
approval of CC recommendations for open questions §6 #2-5:
- Phase 0 tuning budget: S3 > 50% → production (AC pattern)
- pos_action_scale: Option B **0.020**, Option A **0.025** (2026-04-24 update
  per AC T9_F α-2 precedent, ``project_ac_pos_scale_finding.md``)
- warm_start: 不要 (P0 既に cable-proximal)
- Terminal steps: MPPI H*replan = 100 (env max と整合)

Two finger control modes supported (rs decision 2026-04-22 "両方試す"):
- Option B: scripted finger close + 12D EE MPPI (MVP)
- Option A: 14D MPPI (12D EE + 2D finger_cmd) + finger cost term

Used by ``scripts/generate_demos_mppi_m3_grip.py`` (G3 per design spec)
with ``--finger-mode {scripted|mppi}`` CLI flag.

SSOT references (task_config.py):
- ``T_DIST = 0.002`` (2mm): Clamp success pos threshold
- ``T_ALIGN = 0.1745`` (10°): Clamp success ori threshold
- ``T_FINGER = 0.012`` (12mm): Clamp finger opening threshold
- ``K_CLAMP = 5``: sustained steps for success
- ``CLAMP_TERMINAL_STEPS = 100``: env max episode length
- ``FINGER_STEP_SIZE = 0.001`` (1mm): finger velocity
- ``FINGER_OPEN_POS = 0.04``: initial (per arm joint)
- ``FINGER_CLOSE_POS = 0.002``: min (per arm joint)
"""

from dataclasses import dataclass
from typing import Literal

from thread_isaac_lab.configs.mpc_config import MPPIConfig


@dataclass
class MPPIConfigGrip(MPPIConfig):
    """MPPI config for Clamp (Grip) demo generation on Newton VBD.

    Overrides base :class:`MPPIConfig` with Clamp-tight thresholds (2mm pos +
    10° ori + 12mm finger) + H/replan tuned for CLAMP_TERMINAL_STEPS=100.
    """

    # =============================================================================
    # Success thresholds (SSOT: task_config.py)
    # =============================================================================
    # Clamp: pos < T_DIST (2mm), ori < T_ALIGN (10°), finger < T_FINGER (12mm).
    # MPPI cost terminal evaluation uses pos/ori; finger_cost added separately
    # in Option A (finger-mode=mppi).
    success_threshold_m: float = 0.002  # T_DIST (SSOT: task_config.py:152)
    success_threshold_rad: float = 0.1745  # T_ALIGN (SSOT: task_config.py:154)
    success_threshold_finger_m: float = 0.012  # T_FINGER (SSOT: task_config.py:155)

    # =============================================================================
    # Action scales (updated 2026-04-24 per AC T9_F precedent, rs approved)
    # =============================================================================
    # Option B (scripted finger): pos 0.020. AC T9_F α-2 (project_ac_pos_scale_finding.md)
    # showed pos=0.015 plateaus at 30-50mm in 128 steps; 0.025 reached 9.6mm. Grip has
    # tighter T_DIST=2mm + shorter 100 steps, so per-step granularity dominates over
    # overshoot risk. Phase 0 sweep candidates: 0.020-0.030.
    # Option A (MPPI 14D): 0.025 for 14D exploration room + AC precedent headroom.
    # CLI --finger-mode selects which; defaults to Option B value here.
    pos_action_scale: float = 0.020  # [m/step] Option B default (2026-04-24 update; Option A helper → 0.025)
    rot_action_scale: float = 0.15  # [rad/step] AC R3 best (mpc_config_ac.py:40 precedent; base 0.05 override)

    # Dual-arm action: 12D EE for Option B (scripted finger), 14D for Option A (+ finger_cmd).
    # Actual value set by generator at runtime based on --finger-mode.
    # Default = 12 matches Option B (scripted).
    action_dim: int = 12

    # =============================================================================
    # MPPI horizon / replan (CC recommendation §6-5, env max 100 steps)
    # =============================================================================
    # H * replan_interval = effective MPPI execution budget per episode.
    # H=25, replan_interval=4 → 100 total env steps = CLAMP_TERMINAL_STEPS.
    # Base MPPIConfig has H=32 which would be 128 steps (overshoot env max 100).
    # Both H and replan_interval are mandated by m3_grip_design.md §6-5 as new
    # MPPIConfigGrip parameters; replan_interval is NEW in this config (not in
    # base MPPIConfig, AR, or AC configs).
    H: int = 25  # [steps] override base (32)
    replan_interval: int = 4  # [steps] new field; H*replan_interval = CLAMP_TERMINAL_STEPS (spec §6-5)

    # =============================================================================
    # Cost scale (§3.3 of m3_grip_design.md)
    # =============================================================================
    # GRIP_COST_SCALE = T_DIST / T_ALIGN = 0.002 / 0.1745 ≈ 0.01146.
    # Gives pos heavier weight than ori (tighter position tolerance).
    # Field name `m3_cost_scale` inherits AC precedent (mpc_config_ac.py:57).
    # Compare: mpc_config_ar.py:36 ar_cost_scale=0.0688 (T_DIST_APPROACH/T_ALIGN),
    #          mpc_config_ac.py:57 m3_cost_scale=0.30 (Phase 0 best, ori → 1.27°).
    # Phase 0 Grip cost sweep is out of G1 scope; defer to G7 task per spec §4.
    m3_cost_scale: float = 0.0115  # dimensionless; rounded from 0.01146 for clarity

    # =============================================================================
    # IK objective weights (updated 2026-04-24 2nd Debate CC6 condition B)
    # =============================================================================
    # Set to 0.5 to match env `newton_clamp_env.py:547,553` hardcoded weight.
    # Generator demos must produce IK solutions that env can replay (demo fidelity).
    # Prior 0.75 (inherited from AC Phase 0 R2 sweep) caused hidden env-demo IK
    # weight mismatch → NHA 2nd round CRITICAL-level finding.
    l_ori_ik_weight: float = 0.5
    r_ori_ik_weight: float = 0.5

    # =============================================================================
    # Warm-start (§6-4, CC recommendation: 不要)
    # =============================================================================
    # Grip P0 precondition already positions arms at GRASP_Z (cable-proximal).
    # warm_start_offset_m = 0.0 disables the scripted warm-start SLERP phase.
    # If empirical pos_err at step 0 > 5mm, re-enable with a small value.
    warm_start_offset_m: float = 0.0  # [m] override base 0.12 (Grip P0 already cable-proximal)

    # =============================================================================
    # Finger control (rs 決定 2026-04-22 "両方試す")
    # =============================================================================
    # Option A and Option B are parallel implementation targets per spec §3.2;
    # Phase 0 empirically chooses the primary per-success-rate comparison.
    # - Option B (scripted): finger_cmd = finger_close_rate (close) until
    #   opening < T_FINGER, then 0. action_dim=12 (MPPI samples 12D EE only).
    # - Option A (mppi): MPPI samples 14D (12D EE + 2D finger_cmd) with
    #   finger cost term weighted by finger_cost_weight.
    # Default = "scripted" as the MVP per spec §4 (G1→G6a→G6b ordering); use
    # `get_option_a_mppi_grip_config()` for Option A instance.
    finger_mode: Literal["scripted", "mppi"] = "scripted"

    # Scripted finger close rate (Option B only).
    # Ref: m3_grip_design.md §3.2 (rs 決定 2026-04-22 "両方試す")
    finger_close_rate: float = 1.0  # [-1, 1] dimensionless; +1 = full-speed close

    # Option A finger cost coefficient.
    # Ref: m3_grip_design.md §3.3 (cost function finger_gap term).
    # Placeholder 1.0; Phase 0 Option A sweep (G7) will tune.
    finger_cost_weight: float = 1.0  # dimensionless weight of finger_gap term

    # =============================================================================
    # Auto-derived (not overrides, just documentation)
    # =============================================================================
    # K=256 worlds, newton_dt=1/480, sim_substeps=4 (same as AC/AR)
    # world_count = K (inherited 256)

    def __post_init__(self) -> None:
        """Validate mode/action_dim consistency per spec §3.2.

        Raises:
            ValueError: if finger_mode and action_dim are inconsistent
                ("scripted" requires 12D EE-only, "mppi" requires 14D EE+finger_cmd).
        """
        if self.finger_mode == "scripted" and self.action_dim != 12:
            raise ValueError(
                f"finger_mode='scripted' (Option B) requires action_dim=12 "
                f"(12D EE MPPI; finger_cmd appended scripted); got action_dim={self.action_dim}. "
                f"Use get_option_a_mppi_grip_config() for 14D MPPI instead."
            )
        if self.finger_mode == "mppi" and self.action_dim != 14:
            raise ValueError(
                f"finger_mode='mppi' (Option A) requires action_dim=14 "
                f"(12D EE + 2D finger_cmd sampled); got action_dim={self.action_dim}."
            )


def get_default_mppi_grip_config() -> MPPIConfigGrip:
    """Get default MPPI configuration for Clamp demo generation (Option B scripted)."""
    return MPPIConfigGrip()


def get_option_a_mppi_grip_config() -> MPPIConfigGrip:
    """Get MPPI config for Option A (14D MPPI, finger-cmd sampled).

    Uses construction-time kwargs so ``__post_init__`` validates
    ``(finger_mode, action_dim)`` invariant (post-construction mutation would
    bypass validation).

    Updated 2026-04-24 (rs approved): pos_action_scale 0.020→0.025 per AC T9_F
    α-2 precedent (``project_ac_pos_scale_finding.md``). 14D exploration + tight
    T_DIST=2mm + 100 steps shorter need larger per-step granularity.
    """
    return MPPIConfigGrip(
        action_dim=14,  # 12D EE + 2D finger_cmd
        pos_action_scale=0.025,  # [m/step] larger step for 14D exploration (AC T9_F precedent)
        finger_mode="mppi",
    )
