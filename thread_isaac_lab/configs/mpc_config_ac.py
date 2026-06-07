# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""AC-specific MPPI configuration for ApproachCable demo generation.

Adapts MPPIConfigAR's pattern to AC skill (bimanual_reach retargeted at tight
RL Routing thresholds). Integrates Phase 0 (2026-04-21) validated parameters
that broke AR's ori plateau.

Created 2026-04-21 per m3_ac_design.md Option α-2 Step 1.
"""

from dataclasses import dataclass

from thread_isaac_lab.configs.mpc_config import MPPIConfig


@dataclass
class MPPIConfigAC(MPPIConfig):
    """MPPI config for ApproachCable demo generation on Newton VBD.

    Overrides base :class:`MPPIConfig` (0.08m bimanual_reach legacy) with
    RL Routing AC tight thresholds (12mm pos + 10deg ori) and Phase 0
    validated structural fix for ori convergence.

    Used by ``scripts/generate_demos_mppi_m3.py`` with
    ``--config-class MPPIConfigAC`` (Step 2 planned CLI arg) or by
    direct instantiation in a future M3-AC script.
    """

    # AC success thresholds (SSOT: task_config.py:153 T_DIST_APPROACH, :154 T_ALIGN).
    success_threshold_m: float = 0.012  # RL Routing AC spec
    success_threshold_rad: float = 0.1745  # 10 deg

    # AC action scales (tuned 2026-04-21 Phase 1 α-2 Step 4).
    # pos_action_scale 0.025 (vs base 0.015) validated by T9_F: 128 steps から 9.6/11.7 mm 到達、S3=100%.
    # 0.015 default では 128/256 steps どちらも 30-50mm で頭打ち (T6/T7/A'/E 全 FAIL)。
    pos_action_scale: float = 0.025  # T9_F validated (2026-04-21)
    rot_action_scale: float = 0.15   # Phase 0 R3 best (0.08-0.15 all PASS; 0.15 fastest ~18 steps vs ~33 at 0.08)

    # Dual-arm full pose: L(pos3+rot3) + R(pos3+rot3) per M3 convention.
    # NOTE: M3 uses L-first layout natively; convert to R-first in M4 or via
    # --output-layout flag for AC env compatibility.
    action_dim: int = 12

    # ==========================================================================
    # Phase 0 (2026-04-21) validated structural fix (R1)
    # ==========================================================================
    # AR Phase 0 breakthrough: manual cost_scale override breaks ori plateau.
    # F7 default (auto-derived 0.012/0.1745 = 0.0687) FAILed, 0.15 succeeds.
    #
    # For AC (same threshold pair as AR), same fix applies.
    # Phase 0 23-cell analysis: cost_scale range [0.15-0.30] all PASS (S3=100%),
    # but 0.30 gives BEST ori (best cell: cost=0.30/oriW=0.75/rot=0.15 → ori=1.27° pos=1.73mm).
    # Adopted 0.30 as default (highest cost = tightest ori convergence).
    m3_cost_scale: float = 0.30

    # Phase 0 (2026-04-21) R2 validated range: 0.75-1.5 all PASS, 0.75 sufficient.
    # IK objective weight for L/R orientation (default in M3 is 0.5).
    l_ori_ik_weight: float = 0.75
    r_ori_ik_weight: float = 0.75

    # AC warm-start offset: inherit M3 default 0.12m (T9 validated 2026-04-21).
    # Early T7/T8 diagnosis suggested 0.05m but T9 revealed true root cause was
    # pos_action_scale too small (0.015m/step). With pos 0.025m/step, M3 default
    # 0.12m offset converges 120→12mm in 112 steps. OFFSET=0.05m attempted and
    # caused IK reachability failure on R-arm (T8 divergence to 361mm).
    # NOTE: no override defined → base MPPIConfig.warm_start_offset_m=0.12 used.


def get_default_mppi_ac_config() -> MPPIConfigAC:
    """Get default MPPI configuration for AC demo generation."""
    return MPPIConfigAC()
