# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Late Fusion obs assembler skeleton (T-Vision-Fusion L1.A.4 §4.1).

Env-side wrapper that takes env-computed 45D base obs + Fusion output
(:class:`PoseEstimate14D` + regime + conf) and assembles 50D augmented
obs per CC4 v3.2 §6.4 + design memo §2.4 layout:

- ``obs[0:8]``    env (proprio, unchanged)
- ``obs[8:16]``   env (proprio, unchanged; OBS_L_ARM_MASK_PROB applies)
- ``obs[16:30]``  Fusion PoseEstimate14D
- ``obs[30:42]``  Fusion recomputed error (vision-derived clip pose -
  ee_pos / ori_axis_angle)
- ``obs[42:45]``  env zero pad (unchanged; IC-compatible padding)
- ``obs[45:49]``  Fusion regime one-hot
- ``obs[49:50]``  Fusion confidence scalar

Boundary (state.md §4 禁止事項):

- This module does NOT modify ``newton_approach_cable_env.py`` or any other
  env file. Composition pattern: training entry script wraps env via
  ``VisionFusedEnvAdapter`` (separate module, MVP-4+ refactor candidate).
- This module IS env-aware (reads ``ee_pos_r/l``, ``current_clip_pos/quat``)
  → cannot live in ``estimators/`` (R6 violation).
- Imports ``thread_isaac_lab.estimators.*`` (one-way); estimators must not
  import this module (CC4 v3.2 §H.3 import-lint test enforces).

Phase: SKELETON PREP (T-Vision-Fusion-Impl-Phase-0-Skeleton, T-ROOT-COORD#s11
2026-05-04). Implementation deferred to ``CC-L1A-Phase-5-4-Impl`` (see
``thread-vault/T-Vision-Fusion/state.md`` §11.2 4-cascade trigger). Every
compute method raises :class:`NotImplementedError`.

Design memo cross-refs (line numbers refer to LL-Vision-Fusion-Design.md):

- §2.4 (line 173) — 50D obs structure table
- §2.5.5 (line 261) — recomputed error logic (clip_pos_w - ee_pos +
  ori_axis_angle)
- §3.2 (line 356) — FusionAggregator usage upstream
- §4.1 (line 466) — VisionObsAssembler class spec (~70 LoC impl target)
- §4.3 (line 555) — obs slot population rules + NaN/inf defense
- §4.4 (line 574) — R6 boundary discussion (why env wrapper not estimator)
- §4.5 (line 590) — ``target_seg_idx`` propagation (env-side computed,
  R6 OK)
- §6.3 (line 778) — G-V2 obs population correctness benchmark (skeleton
  validation gate)
"""

from __future__ import annotations

import torch

from thread_isaac_lab.estimators.aggregator import (
    FusionAggregator,
    FusionAggregatorConfig,
    PoseCoreV2Output,
)
from thread_isaac_lab.estimators.types import CableState40

# Layout constants per design memo §2.4 (line 173). Mirrored from CC4 v3.2
# §6.4; SSOT for 50D obs layout lives in PoseEstimation-Design-v3.2.md.
_OBS_DIM_BASE = 45  # env-computed base obs dim
_OBS_DIM_AUGMENTED = 50  # Late Fusion augmented obs dim
_OBS_SLICE_POSE_14D = (16, 30)  # PoseEstimate14D
_OBS_SLICE_RECOMPUTED_ERROR = (30, 42)  # vision-recomputed pos+ori error
_OBS_SLICE_ZERO_PAD = (42, 45)  # env zero pad (preserved unchanged)
_OBS_SLICE_REGIME_ONEHOT = (45, 49)  # 4D regime one-hot
_OBS_SLICE_CONF_SCALAR = (49, 50)  # 1D aggregated confidence

# Number of regime ordinals (must match aggregator.REGIME_* constants).
_NUM_REGIMES = 4


class VisionObsAssembler:
    """Assemble 50D vision-augmented obs from 45D base obs + Fusion output (§4.1).

    Composition pattern: stateless aggregator wrapped by env-adapter (e.g.,
    ``VisionFusedEnvAdapter`` impl-phase module). Holds a single
    :class:`FusionAggregator` instance + identity matrix for one-hot
    encoding cache.

    Args:
        fusion_config: :class:`FusionAggregatorConfig` (passed through to
            internal :class:`FusionAggregator`).

    Notes:
        - Stateless: no per-episode buffers; safe to share across envs.
        - One-hot encoding uses cached ``torch.eye(4)`` lookup table to
          avoid per-step allocation overhead (~0.1ms saved per step).
        - NaN/inf defense applied per design memo §4.3:
          ``torch.nan_to_num(pose_14d, nan=0.0, posinf=1e6, neginf=-1e6)``.
          FAIL_CLOSED regime carries forward ``previous_pose_estimate`` per
          CC4 v3.2 §5.6; if absent, zeros.
    """

    def __init__(self, fusion_config: FusionAggregatorConfig) -> None:
        self._aggregator = FusionAggregator(fusion_config)
        # ``torch.eye`` allocated lazily on first forward (device per input
        # tensor). Cache slot below; impl phase finalizes device handling.
        self._regime_one_hot_lookup: torch.Tensor | None = None

    def assemble_50d(
        self,
        obs_45d: torch.Tensor,
        pose_out: PoseCoreV2Output,
        cable_state: CableState40,
        target_seg_idx: torch.Tensor,
        current_clip_pos: torch.Tensor,
        current_clip_quat: torch.Tensor,
        ee_pos_r: torch.Tensor,
        ee_quat_r: torch.Tensor,
        ee_pos_l: torch.Tensor,
        ee_quat_l: torch.Tensor,
    ) -> torch.Tensor:
        """Assemble 50D obs per design memo §4.1 (lines 488-529).

        Steps:

        1. Run :class:`FusionAggregator` to get 14D pose + regime + conf.
        2. Populate ``obs[16:30]`` ← PoseEstimate14D (NaN/inf-safe per §4.3).
        3. Populate ``obs[30:42]`` ← :meth:`_recompute_error` output.
        4. Preserve ``obs[42:45]`` zero pad from base 45D obs.
        5. Populate ``obs[45:49]`` ← regime one-hot via cached identity LUT.
        6. Populate ``obs[49]`` ← aggregated confidence scalar.

        Args:
            obs_45d: ``[B, 45]`` env-computed base obs.
            pose_out: Pose CoreV2 output (Stage 1a result).
            cable_state: CableStateSolver output (Stage 1b result).
            target_seg_idx: ``[B]`` int64 active target segment (env-side
                ``_compute_target_seg_indices``; primary right arm).
            current_clip_pos: ``[B, 3]`` active target clip nominal pose
                (kept for diagnostics + multi-clip orchestrator usage).
            current_clip_quat: ``[B, 4]`` active target clip nominal ori.
            ee_pos_r: ``[B, 3]`` right end-effector world position.
            ee_quat_r: ``[B, 4]`` right end-effector world quat (xyzw).
            ee_pos_l: ``[B, 3]`` left end-effector world position.
            ee_quat_l: ``[B, 4]`` left end-effector world quat (xyzw).

        Returns:
            ``[B, 50]`` float32 augmented obs (CC4 v3.2 §6.4 layout).

        Raises:
            NotImplementedError: skeleton stub. Impl pending
                ``CC-L1A-Phase-5-4-Impl`` (see state.md §11.2).
        """
        raise NotImplementedError(
            "VisionObsAssembler.assemble_50d: skeleton stub. "
            "Impl pending CC-L1A-Phase-5-4-Impl. See LL-Vision-Fusion-Design.md "
            "§4.1 (line 466) for impl spec."
        )

    @staticmethod
    def _recompute_error(
        clip_pos_w: torch.Tensor,
        clip_quat_w: torch.Tensor,
        ee_pos_r: torch.Tensor,
        ee_quat_r: torch.Tensor,
        ee_pos_l: torch.Tensor,
        ee_quat_l: torch.Tensor,
    ) -> torch.Tensor:
        """Vision-derived recomputed error per §2.5.5 (line 263).

        Layout (12D):

        - ``[:, 0:3]``  pos_err_r = clip_pos_w - ee_pos_r
        - ``[:, 3:6]``  ori_err_r = ori_axis_angle(clip_quat_w, ee_quat_r)
        - ``[:, 6:9]``  pos_err_l = clip_pos_w - ee_pos_l
        - ``[:, 9:12]`` ori_err_l = ori_axis_angle(clip_quat_w, ee_quat_l)

        ``ori_axis_angle`` per Pose §4.7 yaw mod π convention (R-F12;
        OQ-F3 Rs disposition pending). Impl phase resolves via Pose CoreV2
        helper or new utility in ``estimators.geometry`` module.

        Args:
            clip_pos_w: ``[B, 3]`` vision-derived clip world position.
            clip_quat_w: ``[B, 4]`` vision-derived clip world quat (xyzw).
            ee_pos_r/l: ``[B, 3]`` end-effector world positions.
            ee_quat_r/l: ``[B, 4]`` end-effector world quats (xyzw).

        Returns:
            ``[B, 12]`` float32 recomputed error.

        Raises:
            NotImplementedError: skeleton stub.
        """
        raise NotImplementedError(
            "VisionObsAssembler._recompute_error: skeleton stub. "
            "Impl pending; see design memo §2.5.5 (line 263) for "
            "ori_axis_angle convention (Pose §4.7 yaw mod π OQ-F3 pending)."
        )
