# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Late Fusion aggregator skeleton (T-Vision-Fusion L1.A.4 sub-task 1).

PoseEstimate14D 再構成 + regime aggregation + confidence aggregation per
``thread-vault/06-Knowledge/LL-Vision-Fusion-Design.md`` §3.2 + §3.3 + §3.4:

- :class:`PoseEstimate14D`     — output dataclass (CC4 v3.2 §3.2 contract:
  ``[seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]``)
- :class:`FusionAggregatorConfig` — frozen design parameters (§3.2 detail)
- :class:`FusionAggregator`    — Stage 2 of 5-stage pipeline (§3.1)
  - :meth:`aggregate`          — main entry, returns 14D + RegimeState
  - :meth:`_derive_regime`     — cable target conf → regime (§3.3 thresholds)
  - :meth:`_most_restrictive`  — pairwise priority order (§3.3 table)
- :func:`compute_seg_quat_from_tangent` — tangent-based seg quat (§2.5.2)

Phase: SKELETON PREP (T-Vision-Fusion-Impl-Phase-0-Skeleton, T-ROOT-COORD#s11
2026-05-04). Implementation deferred to ``CC-L1A-Phase-5-4-Impl`` (T-Vision-Fusion
state.md §11.2 4-cascade trigger). Every compute method raises
:class:`NotImplementedError` at this stage; this module exists to lock the
public boundary surface (R6) and the integration contract.

R6 module boundary: imports restricted to ``thread_isaac_lab.estimators.*``
+ ``torch``. NO ``newton``, NO ``thread_isaac_lab.envs.*``. Verified
mechanically by ``tests/test_estimator_module_boundary.py`` AST lint
(impl-phase add).

Design memo cross-refs (line numbers refer to LL-Vision-Fusion-Design.md):

- §2.4 (line 173) — 50D obs structure (Fusion provides 14D + 12D + 4D + 1D)
- §2.5.1 (line 192) — PoseEstimate14D 再構成 (concat clip + cable seg)
- §2.5.2 (line 207) — seg_quat from tangent (clamp [1, 38] + edge_penalty 0.5)
- §2.5.3 (line 226) — regime aggregation (most-restrictive priority)
- §2.5.4 (line 247) — confidence aggregation (min × edge_penalty)
- §3.2 (line 356) — FusionAggregator class spec (~60 LoC impl target)
- §3.3 (line 419) — RegimeState aggregation table
- §3.4 (line 435) — Confidence rationale (bottleneck principle)
- §3.5 (line 449) — Bit-identical baseline preservation (E.5 invariant)

Existing assets reused (per design memo §1.5):

- :class:`thread_isaac_lab.estimators.types.CableState40` — cable state input
  (positions [B, 40, 3] + confidences [B, 40], from CableStateSolver Stage E)
- ``thread_isaac_lab/configs/task_config.py:70-75`` cable physical params
  (``CABLE_SEGMENTS=40``, mirrored as ``_NUM_CABLE_SEGMENTS=40`` below;
  TOUCH FORBIDDEN, SSOT remains task_config.py)
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from thread_isaac_lab.estimators.types import CableState40

# ---------------------------------------------------------------------------
# Constants mirrored from task_config.py (TOUCH FORBIDDEN; SSOT remains there).
# Drift detection: impl phase adds a unit-test that re-imports task_config and
# asserts equality (out of R6 scope for this skeleton; tests/ side concern).
# ---------------------------------------------------------------------------
_NUM_CABLE_SEGMENTS = 40  # mirrors CABLE_SEGMENTS

# Regime ordinals (design memo §3.3 priority order; lower index = higher trust).
REGIME_ACCEPT = 0
REGIME_PREDICT_TEMPORAL = 1
REGIME_FALLBACK = 2
REGIME_FAIL_CLOSED = 3


@dataclass
class PoseEstimate14D:
    """Late Fusion output: PoseEstimate14D + per-batch confidence (§3.2 contract).

    Per CC4 v3.2 §3.2 + LL-Vision-Pose-Design.md §4.6 + design memo §2.5.1:
    ``[seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]``. The ``conf``
    field carries the §2.5.4 aggregated confidence (min × edge_penalty) and
    is consumed by the env wrapper to populate ``obs[49]`` (§4.3).

    Attributes:
        pose_14d: ``[B, 14]`` float32, world-frame (env ``bq`` 基準).
            Layout per CC4 v3.2 §3.2:

            * ``[:, 0:3]``    seg_pos_w  — cable target segment position
            * ``[:, 3:7]``    seg_quat_w_xyzw — tangent-derived (§2.5.2)
            * ``[:, 7:10]``   clip_pos_w  — Pose CoreV2 PnP tvec
            * ``[:, 10:14]``  clip_quat_w_xyzw — Pose CoreV2 cv2.Rodrigues
        conf: ``[B]`` float32 ∈ ``[0, 1]`` aggregated confidence (§2.5.4
            min × edge_penalty). Raw pass-through to ``obs[49]`` per CC4
            v3.2 §15 ε-variance prohibition (E.5 invariant).
    """

    pose_14d: torch.Tensor
    conf: torch.Tensor


@dataclass
class FusionAggregatorConfig:
    """Aggregator configuration (design memo §3.2 detail).

    Default values reflect design memo §2.5 thresholds:

    - ``edge_seg_clamp_min/max=1, 38`` (§2.5.2 tangent computation needs
      neighbors on both sides; segments 0 and 39 fall back to clamped seg)
    - ``edge_penalty=0.5`` (§2.5.4 conservative aggregation for clamped seg)
    - ``regime_threshold_high=0.85, predict=0.5, fallback=0.3``
      (§3.3 table; cable_target_conf → regime)
    - ``force_accept_unit_conf=False`` (§6.1 G-V0 unit test mode; flips to
      True for bit-identical baseline verification only)
    """

    edge_seg_clamp_min: int = 1
    edge_seg_clamp_max: int = 38
    edge_penalty: float = 0.5
    regime_threshold_high: float = 0.85
    regime_threshold_predict: float = 0.5
    regime_threshold_fallback: float = 0.3
    force_accept_unit_conf: bool = False


@dataclass
class PoseCoreV2Output:
    """Pose alt path forward output contract (clip 7D only, §2.1 + Pose §4.6).

    Mirrors :class:`thread_isaac_lab.estimators.core.pose_estimator_core_v2.CoreOutputV2`
    aggregated form, but exposes only the FusionAggregator-relevant fields
    (clip pose + per-batch regime + conf). Stage 0/1/2 internal artifacts
    (ROI bbox, SAM2 mask, keypoints) live in :class:`CoreOutputV2`.

    Attributes:
        clip_pos_w: ``[B, 3]`` float32 [m] world-frame (PnP tvec)
        clip_quat_w_xyzw: ``[B, 4]`` float32 unit quat (xyzw)
        conf_pose: ``[B]`` float32 ∈ ``[0, 1]`` per-batch pose confidence
            (RANSAC inlier_count / N or SAM2 mask × inlier ratio)
        regime: ``[B]`` int64 ∈ ``{0, 1, 2, 3}`` per-batch regime ordinal
            (REGIME_ACCEPT=0 .. REGIME_FAIL_CLOSED=3)
    """

    clip_pos_w: torch.Tensor
    clip_quat_w_xyzw: torch.Tensor
    conf_pose: torch.Tensor
    regime: torch.Tensor


def compute_seg_quat_from_tangent(
    positions: torch.Tensor,
    target_seg_idx: torch.Tensor,
) -> torch.Tensor:
    """Compute cable segment quaternion from local tangent (§2.5.2).

    Per design memo §2.5.2 (line 207): tangent ``= positions[seg+1] -
    positions[seg-1]``, normalize, align local +x axis to tangent (twist
    convention from cable_target_axis). Twist about cable axis is
    unobservable (cylindrical symmetry); produces canonical zero-twist
    (right-hand rule with world +z auxiliary axis). Edge segments
    (target_seg_idx ∈ {0, 39}) clamp to [1, 38] before tangent — caller
    propagates edge case to ``edge_penalty=0.5`` (§2.5.4).

    Args:
        positions: ``[B, 40, 3]`` float32 [m] cable segment positions
            (CableState40.positions).
        target_seg_idx: ``[B]`` int64 active target segment index (env-side
            ``_compute_target_seg_indices``); clamping enforced internally.

    Returns:
        ``[B, 4]`` float32 unit quat (xyzw). NaN/inf-safe per design memo
        §4.3 (caller post-processes via ``torch.nan_to_num`` if needed).

    Raises:
        NotImplementedError: skeleton stub. Impl phase fills in
            tangent-to-quaternion canonical alignment (Rodriguez rotation
            matrix → xyzw quat). See ``CC-L1A-Phase-5-4-Impl`` task spec.
    """
    raise NotImplementedError(
        "compute_seg_quat_from_tangent: skeleton stub. "
        "Impl pending CC-L1A-Phase-5-4-Impl (4-cascade trigger; see "
        "thread-vault/T-Vision-Fusion/state.md §11.2)."
    )


class FusionAggregator:
    """Stage 2 of Late Fusion pipeline: PoseEstimate14D + Regime + Conf.

    Composition entry: takes Pose CoreV2 output (clip 7D) + CableState
    Solver output (positions + confidences) + per-world ``target_seg_idx``,
    produces 14D pose + RegimeState + aggregated confidence.

    R6 boundary: this class is in ``estimators/`` (not ``envs/``); no env
    or newton import. Caller (env wrapper) handles obs slot assembly.

    Args:
        config: :class:`FusionAggregatorConfig` with §3.2 thresholds.

    Example (impl phase usage; raises NotImplementedError today):

        >>> agg = FusionAggregator(FusionAggregatorConfig())
        >>> pose_14d, regime = agg.aggregate(pose_out, cable_state, seg_idx)
    """

    def __init__(self, config: FusionAggregatorConfig) -> None:
        self._config = config

    def aggregate(
        self,
        pose_out: PoseCoreV2Output,
        cable_state: CableState40,
        target_seg_idx: torch.Tensor,
    ) -> tuple[PoseEstimate14D, torch.Tensor]:
        """Aggregate Pose + CableState → PoseEstimate14D + RegimeState (§3.2).

        Steps (design memo §3.2 lines 369-417):

        1. Clamp ``target_seg_idx`` to ``[edge_seg_clamp_min,
           edge_seg_clamp_max]`` (§2.5.2)
        2. Index ``cable_state.positions`` to get ``seg_pos_w`` ``[B, 3]``
        3. Compute ``seg_quat_w`` via :func:`compute_seg_quat_from_tangent`
        4. Concat with Pose CoreV2 ``clip_pos_w`` + ``clip_quat_w`` →
           ``pose_14d`` ``[B, 14]``
        5. Derive ``cable_target_regime`` from
           ``cable_state.confidences[b, seg_idx]`` (§2.5.3)
        6. Aggregate ``regime_fusion = max_priority(pose_regime,
           cable_regime)`` (most-restrictive)
        7. Aggregate ``conf_fusion = min(pose_conf, cable_target_conf)
           × edge_penalty`` (§2.5.4)
        8. If ``config.force_accept_unit_conf`` (G-V0 unit test mode):
           regime ← ACCEPT, conf ← 1.0 (§3.5 bit-identical preservation)

        Args:
            pose_out: Pose CoreV2 forward output (clip 7D).
            cable_state: CableStateSolver Stage E output (positions +
                confidences for all 40 segments).
            target_seg_idx: ``[B]`` int64 per-world active target segment
                (env-side ``_compute_target_seg_indices``; primary right
                arm per §4.5).

        Returns:
            (PoseEstimate14D, RegimeState ``[B]`` int64) tuple.

        Raises:
            NotImplementedError: skeleton stub.
        """
        raise NotImplementedError(
            "FusionAggregator.aggregate: skeleton stub. "
            "Impl pending CC-L1A-Phase-5-4-Impl. See LL-Vision-Fusion-Design.md "
            "§3.2 (line 356) for impl spec."
        )

    def _derive_regime(self, conf: torch.Tensor) -> torch.Tensor:
        """Cable target conf → regime ordinal (§2.5.3 thresholds).

        Args:
            conf: ``[B]`` float32 ∈ ``[0, 1]`` cable_target_conf
                (``cable_state.confidences[b, target_seg_idx]``).

        Returns:
            ``[B]`` int64 regime ordinal ∈ ``{0, 1, 2, 3}``.

        Raises:
            NotImplementedError: skeleton stub.
        """
        raise NotImplementedError(
            "FusionAggregator._derive_regime: skeleton stub. "
            "Impl pending; see design memo §2.5.3 thresholds (high=0.85, "
            "predict=0.5, fallback=0.3)."
        )

    def _most_restrictive(self, r1: torch.Tensor, r2: torch.Tensor) -> torch.Tensor:
        """Pairwise priority order (§3.3 table; FAIL_CLOSED > FALLBACK >
        PREDICT > ACCEPT).

        Args:
            r1: ``[B]`` int64 first regime.
            r2: ``[B]`` int64 second regime.

        Returns:
            ``[B]`` int64 ``max(r1, r2)`` per-element (since higher ordinal =
            more restrictive in our convention).

        Raises:
            NotImplementedError: skeleton stub. Impl can be ``torch.maximum(r1, r2)``.
        """
        raise NotImplementedError(
            "FusionAggregator._most_restrictive: skeleton stub. "
            "Impl phase: torch.maximum(r1, r2) per §3.3 priority table."
        )
