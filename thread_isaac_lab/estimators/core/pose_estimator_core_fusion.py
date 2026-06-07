# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Late Fusion composition entry skeleton (T-Vision-Fusion L1.A.4 §5.1).

Composition over inheritance: composes :class:`PoseEstimatorCoreV2` (Pose
alt path; clip 7D) + :class:`CableStateSolver` (cable seg positions + conf)
+ :class:`FusionAggregator` (Stage 2 PoseEstimate14D 再構成) into a single
forward entry that returns a :class:`FusionCoreOutput`.

R6 module boundary: imports restricted to ``thread_isaac_lab.estimators.*``.
NO ``newton``, NO ``thread_isaac_lab.envs.*``. Verified mechanically by
``tests/test_estimator_module_boundary.py`` AST lint (impl-phase add).

Phase: SKELETON PREP (T-Vision-Fusion-Impl-Phase-0-Skeleton, T-ROOT-COORD#s11
2026-05-04). Implementation deferred to ``CC-L1A-Phase-5-4-Impl`` (4-cascade
trigger; see ``thread-vault/T-Vision-Fusion/state.md`` §11.2). Every compute
method raises :class:`NotImplementedError`.

Design memo cross-refs (line numbers refer to LL-Vision-Fusion-Design.md):

- §3.1 (line 287) — 5-stage pipeline diagram (Stage 1a Pose + 1b CableState
  parallel → Stage 2 FusionAggregator → Stage 3 ObsAssembler → Stage 4
  policy migration → Stage 5 AC fine-tune)
- §5.1 (line 614) — composition entry spec (~80 LoC impl target)
- §5.4 (line 720) — existing estimator core integration table
- §5.3 (line 702) — import-lint test extension (R6 enforcement)

Existing assets reused (per §5.4 integration table):

- :class:`PoseEstimatorCoreV2` (``estimators/core/pose_estimator_core_v2.py``)
  — Pose alt path Stage 0+1+2+3 orchestrator (skeleton prep 2026-05-03)
- :class:`CableStateSolver` (``estimators/cable_state.py``) — Hybrid PCA +
  Cosserat 5-stage solver (skeleton prep 2026-05-04)
- :class:`FusionAggregator` (``estimators/aggregator.py``) — Stage 2
  (本 sibling skeleton, 2026-05-04)
- :class:`EstimatorInputs` (``estimators/types.py``) — input boundary; uses
  existing ``routing_target_seg_idx`` (single, primary right-arm per §4.5;
  L-arm split deferred to MVP-4+)

Stage 1a/1b parallelism (latency optimization, §5.1 line 685):

    stream_pose = torch.cuda.Stream()
    stream_cable = torch.cuda.Stream()
    with torch.cuda.stream(stream_pose):
        pose_out = self._pose.forward(inputs)
    with torch.cuda.stream(stream_cable):
        cable_state = self._cable(cloud, prev)
    torch.cuda.synchronize()  # safety barrier before Stage 2

Impl phase fills in ``forward()`` body; skeleton today raises.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch

from thread_isaac_lab.estimators.aggregator import (
    FusionAggregator,
    PoseCoreV2Output,
)
from thread_isaac_lab.estimators.cable_state import CableStateSolver
from thread_isaac_lab.estimators.core.pose_estimator_core_v2 import PoseEstimatorCoreV2
from thread_isaac_lab.estimators.types import CableState40, EstimatorInputs


@dataclass
class FusionCoreOutput:
    """Composite forward output: 14D pose + regime + diagnostics (§5.1 contract).

    Attributes:
        pose_14d: ``[B, 14]`` float32 PoseEstimate14D contract (CC4 v3.2 §3.2)
        regime: ``[B]`` int64 ∈ ``{0, 1, 2, 3}`` per-batch most-restrictive
            regime (§3.3 table; ``REGIME_FAIL_CLOSED=3``, etc.)
        conf_fusion: ``[B]`` float32 ∈ ``[0, 1]`` aggregated confidence
            (§2.5.4 min × edge_penalty)
        pose_v2_output: full :class:`PoseCoreV2Output` retained for
            diagnostics + downstream eval (G-V1 leaf integration sanity)
        cable_state: full :class:`CableState40` retained for diagnostics +
            downstream eval (G-V3 PoseEstimate14D 再構成 correctness)
        diagnostics: free-form dict for stage-specific telemetry
            (per-stream timing, NaN counts, etc.)
    """

    pose_14d: torch.Tensor
    regime: torch.Tensor
    conf_fusion: torch.Tensor
    pose_v2_output: PoseCoreV2Output
    cable_state: CableState40
    diagnostics: dict = field(default_factory=dict)


class PoseEstimatorCoreFusion:
    """Composition entry for Late Fusion: Pose CoreV2 + CableState + Aggregator.

    Per design memo §5.1 (line 614): composition over inheritance. Each
    sub-module is constructed externally and injected (DI pattern); this
    class only orchestrates Stage 1a + 1b + 2 forward.

    R6 boundary: ``estimators/`` 配下、no env / newton import (CC4 v3.2 §H.3
    import-lint test extension enforces).

    Args:
        pose_core_v2: configured :class:`PoseEstimatorCoreV2` (Pose alt path).
        cable_solver: configured :class:`CableStateSolver` (CableState §6.2).
        fusion_aggregator: configured :class:`FusionAggregator` (本 design §3.2).

    Example (impl phase usage; raises NotImplementedError today):

        >>> core = PoseEstimatorCoreFusion(pose_v2, cable_solver, agg)
        >>> output = core.forward(estimator_inputs)
        >>> output.pose_14d.shape  # [B, 14]
    """

    def __init__(
        self,
        pose_core_v2: PoseEstimatorCoreV2,
        cable_solver: CableStateSolver,
        fusion_aggregator: FusionAggregator,
    ) -> None:
        self._pose = pose_core_v2
        self._cable = cable_solver
        self._fusion = fusion_aggregator

    def forward(self, inputs: EstimatorInputs) -> FusionCoreOutput:
        """Run Stage 1a (Pose) + 1b (CableState) parallel + Stage 2 (Aggregator).

        Steps (design memo §5.1 lines 658-681):

        1. Stage 1a: ``self._pose.forward(inputs)`` → ``PoseCoreV2Output``
           (clip 7D + per-batch conf + regime). Internally orchestrates
           ROI prior → SAM2 mask → keypoint extract → PnP+RANSAC.
        2. Stage 1b: ``self._cable(cloud=self._build_cloud(inputs),
           prev=inputs.previous_cable_estimate)`` → ``CableState40``
           (positions [B, 40, 3] + confidences [B, 40]). Internally Stage
           A.3 → B (PCA) → C (DD-PINN) → D (Cosserat) → E (conf calib).
        3. Stage 2: ``self._fusion.aggregate(pose_out, cable_state,
           inputs.routing_target_seg_idx)`` → ``(PoseEstimate14D,
           regime_fusion)``. Default uses primary right arm per §4.5.

        Args:
            inputs: :class:`EstimatorInputs` (R6 boundary inputs only).

        Returns:
            :class:`FusionCoreOutput` with 14D pose + regime + conf + sub-
            module diagnostics.

        Raises:
            NotImplementedError: skeleton stub. Impl pending
                ``CC-L1A-Phase-5-4-Impl`` (4-cascade trigger).

        Notes:
            - Stage 1a/1b parallelism via ``torch.cuda.Stream`` (impl
              phase optimization; sequential fallback is correct but slow).
            - L-arm path (``target_seg_idx_l``) deferred to MVP-4+ per §4.5;
              skeleton uses single ``routing_target_seg_idx`` from existing
              :class:`EstimatorInputs`.
        """
        raise NotImplementedError(
            "PoseEstimatorCoreFusion.forward: skeleton stub. "
            "Impl pending CC-L1A-Phase-5-4-Impl. See LL-Vision-Fusion-Design.md "
            "§5.1 (line 614) for impl spec."
        )

    def _build_cloud(self, inputs: EstimatorInputs) -> torch.Tensor:
        """Internal helper: build merged 3-cam point cloud for CableState
        Stage A.3 (multi-cam fusion + voxel downsample).

        Per CableState §2.5.3: per-pixel back-projection + Stage A.3
        ``stage_a3_fuse_clouds`` merge wrist_l + wrist_r + overhead.

        Args:
            inputs: :class:`EstimatorInputs` with rgb_*, depth_*, camera
                pose, intrinsics fields populated.

        Returns:
            Merged ``[B, N, 3]`` (or ragged) point cloud tensor; exact
            shape per CableState §6.2 ``CableStateSolver`` API contract.

        Raises:
            NotImplementedError: skeleton stub. Impl phase delegates to
                :func:`thread_isaac_lab.estimators.cable_state.stage_a3_fuse_clouds`.
        """
        raise NotImplementedError(
            "PoseEstimatorCoreFusion._build_cloud: skeleton stub. "
            "Impl phase delegates to estimators.cable_state.stage_a3_fuse_clouds."
        )
