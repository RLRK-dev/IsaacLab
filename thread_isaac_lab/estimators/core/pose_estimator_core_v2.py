# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Phase 5-4 alt-path estimator core: Stage 0 + Stage 1 SAM2 + Stage 2 keypoints + Stage 3 PnP.

Implements the orchestrator prescribed by ``thread-vault/06-Knowledge/LL-Vision-Pose-Design.md``
§1.2: drop-in V2 of :class:`thread_isaac_lab.estimators.core.pose_estimator_core.PoseEstimatorCorePhase1`
that reuses the same R6 boundary (PoseEstimatorInputAdapter + EstimatorInputs)
but swaps Stage 1 (LightUNet) for :class:`Sam2Segmenter` and Stage 3 (Stage 2-4
deferred placeholder) for :class:`PnpClipPoseSolver`.

This module is a **skeleton**: Stage 1 forward and Stage 3 correspondence
both raise :class:`NotImplementedError` until SAM2 install lands and the
nominal-pose projection wiring is added by the impl task. Stage 2 keypoint
extraction (:func:`extract_keypoints_from_mask`) and Stage 3 RANSAC solve
(:meth:`PnpClipPoseSolver.solve`) are already functional in the upstream
modules, so the orchestration logic is fully expressed and only the gated
boundary methods raise.

Design memo cross-refs:

- §1.1 — 3-stage pipeline (Stage 1 SAM2 → Stage 2 keypoints → Stage 3 PnP).
- §1.2 — R6 module boundary (reuses :class:`PoseEstimatorInputAdapter`).
- §3.2 — Bbox prompt strategy (kinematic ROI from :func:`compute_roi_boxes`).
- §3.3 — Offline benchmark inference mode (MVP-3 scope).
- §4.6 — Pose pack into the 14D contract; this V2 fills the clip 7D slot
  only and leaves the cable target-segment 7D slot for L1.A.2.
- §5 — MVP roadmap (this skeleton sits in MVP-0 deliverable scope).

R6 module boundary: imports are restricted to
``thread_isaac_lab.estimators.*``. No ``newton`` / no
``thread_isaac_lab.envs.*`` imports — enforced by AST lint test
``tests/test_estimator_module_boundary.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from thread_isaac_lab.estimators.core.pnp_pose_solver import (
    ClipPoseEstimate,
    Keypoints2D,
    PnpClipPoseSolver,
    PoseRegime,
    extract_keypoints_from_mask,
)
from thread_isaac_lab.estimators.core.roi_prior import CameraIntrinsics, compute_roi_boxes
from thread_isaac_lab.estimators.core.sam2_segmenter import (
    PromptKind,
    Sam2Output,
    Sam2Prompt,
    Sam2Segmenter,
    SegmentRegime,
)
from thread_isaac_lab.estimators.types import EstimatorInputs, enforce_input_boundary

# Default keypoint extraction method per §4.2 row 1 (clip-corner direct mapping).
_DEFAULT_KEYPOINT_METHOD = "contour_polygon"


@dataclass
class CoreOutputV2:
    """V2 estimator forward output (Stage 0 + 1 + 2 + 3).

    Attributes:
        roi_bbox: ``[B, 1, 4]`` Stage 0 bbox prior in pixels
            ``(x_min, y_min, x_max, y_max)`` from :func:`compute_roi_boxes`.
        sam2_output: Stage 1 :class:`Sam2Output` containing per-frame mask
            tensors and per-frame :class:`SegmentRegime`.
        keypoints_per_batch: list of length ``B`` with each entry the Stage 2
            :class:`Keypoints2D` extracted from the best SAM2 mask. Empty
            keypoint sets propagate as ``Keypoints2D`` with zero-row points.
        pose_per_batch: list of length ``B`` with the Stage 3
            :class:`ClipPoseEstimate`. ``regime`` is :class:`PoseRegime.ACCEPT`
            on RANSAC convergence and :class:`PoseRegime.FALLBACK` otherwise.
        seg_regime_per_batch: list of length ``B`` mirroring ``sam2_output.regime``
            for caller-side downstream gating.
        diagnostics: free-form dict for stage-specific debug telemetry.
    """

    roi_bbox: torch.Tensor
    sam2_output: Sam2Output
    keypoints_per_batch: list[Keypoints2D]
    pose_per_batch: list[ClipPoseEstimate]
    seg_regime_per_batch: list[SegmentRegime]
    diagnostics: dict = field(default_factory=dict)


class PoseEstimatorCoreV2:
    """Stage 0 + 1 + 2 + 3 orchestrator for the Charuco/SAM2/PnP alt path.

    Args:
        sam2: configured :class:`Sam2Segmenter` for Stage 1; ``forward`` is
            still NotImplementedError until SAM2 install lands, but the wrapper
            instance can be constructed up-front so the rest of the wiring is
            exercised by unit tests.
        pnp_solver: :class:`PnpClipPoseSolver` carrying the
            :class:`CameraCalibration` and :class:`ClipCadModel` for the clip
            being tracked.
        intrinsics: :class:`CameraIntrinsics` for Stage 0 ROI projection.
        keypoint_method: Stage 2 extractor key; see
            :func:`extract_keypoints_from_mask`. Defaults to
            ``"contour_polygon"`` (design memo §4.2 row 1).
    """

    def __init__(
        self,
        sam2: Sam2Segmenter,
        pnp_solver: PnpClipPoseSolver,
        intrinsics: CameraIntrinsics,
        *,
        keypoint_method: str = _DEFAULT_KEYPOINT_METHOD,
    ) -> None:
        self._sam2 = sam2
        self._pnp_solver = pnp_solver
        self._intrinsics = intrinsics
        self._keypoint_method = keypoint_method

    def _build_bbox_prompts(self, roi_bbox: torch.Tensor) -> list[Sam2Prompt]:
        """Pack Stage 0 ROI boxes into per-batch :class:`Sam2Prompt` list.

        Args:
            roi_bbox: ``[B, 1, 4]`` from :func:`compute_roi_boxes`. Frames with
                a ``(0, 0, 0, 0)`` row (clip behind camera) are still emitted
                — Stage 1 will degrade to FAIL_CLOSED naturally on empty mask.

        Returns:
            length-B list of :class:`Sam2Prompt` objects with
            :attr:`PromptKind.BBOX` and the per-frame bbox tensor reshaped to
            ``[1, 4]`` to match the SAM2 wrapper expectation.
        """
        prompts: list[Sam2Prompt] = []
        bbox_squeezed = roi_bbox.squeeze(1)  # [B, 4]
        for b in range(bbox_squeezed.shape[0]):
            prompts.append(
                Sam2Prompt(
                    kind=PromptKind.BBOX,
                    bbox=bbox_squeezed[b : b + 1],  # [1, 4] view, no copy
                )
            )
        return prompts

    @staticmethod
    def _select_best_mask(sam2_output: Sam2Output) -> torch.Tensor:
        """Pick the highest-IoU mask per batch element.

        SAM2 emits ``[B, num_masks, H, W]`` with ``num_masks`` typically 3
        (multimask_output). The :attr:`Sam2Output.iou_scores` field holds the
        model-predicted quality per channel; we argmax along ``num_masks``.

        Args:
            sam2_output: Stage 1 :class:`Sam2Output` from the SAM2 forward.

        Returns:
            ``[B, H, W]`` float tensor with the best-scoring mask per frame
            (still a sigmoid probability, not yet binarised).
        """
        # iou_scores: [B, num_masks]; masks: [B, num_masks, H, W]
        best_idx = sam2_output.iou_scores.argmax(dim=1)  # [B]
        b_indices = torch.arange(sam2_output.masks.shape[0], device=sam2_output.masks.device)
        return sam2_output.masks[b_indices, best_idx]  # [B, H, W]

    def _extract_keypoints(self, best_mask: torch.Tensor) -> list[Keypoints2D]:
        """Run Stage 2 over the per-batch best mask.

        Args:
            best_mask: ``[B, H, W]`` sigmoid mask from :meth:`_select_best_mask`.

        Returns:
            length-B list of :class:`Keypoints2D`. Empty keypoint sets are
            kept (downstream PnP solve emits :class:`PoseRegime.FALLBACK`).
        """
        out: list[Keypoints2D] = []
        # SAM2 mask is GPU; keypoint extraction uses cv2 → numpy CPU path. The
        # transfer is intentional: Stage 2 is offline-only per design memo §3.3.
        binary = (best_mask > 0.5).detach().cpu().numpy().astype(np.uint8)
        for b in range(binary.shape[0]):
            kps = extract_keypoints_from_mask(binary[b], method=self._keypoint_method)
            out.append(kps)
        return out

    def _solve_pose_per_batch(
        self,
        keypoints_per_batch: list[Keypoints2D],
        kinematic_prior_pose7_per_batch: torch.Tensor,
    ) -> list[ClipPoseEstimate]:
        """Run Stage 3 PnP over the per-batch keypoints.

        Args:
            keypoints_per_batch: length-B list from :meth:`_extract_keypoints`.
            kinematic_prior_pose7_per_batch: ``[B, 7]`` clip pose priors in
                the camera frame, used by
                :meth:`PnpClipPoseSolver.establish_correspondence` for the
                §4.3 nominal projection pairing.

        Returns:
            length-B list of :class:`ClipPoseEstimate`. Until the impl task
            wires up correspondence, this raises
            :class:`NotImplementedError` from
            :meth:`PnpClipPoseSolver.establish_correspondence` for the first
            non-empty keypoint batch element.
        """
        out: list[ClipPoseEstimate] = []
        prior_np = kinematic_prior_pose7_per_batch.detach().cpu().numpy()
        for b, kps in enumerate(keypoints_per_batch):
            if kps.points.shape[0] < 4:
                # Stage 3 fallback per §4.2 row 3 + §8 R-9.
                out.append(
                    ClipPoseEstimate(
                        translation=np.zeros(3, dtype=np.float64),
                        quat_xyzw=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64),
                        inlier_count=0,
                        regime=PoseRegime.FALLBACK,
                    )
                )
                continue
            obj_pts, img_pts = self._pnp_solver.establish_correspondence(kps, prior_np[b])
            out.append(self._pnp_solver.solve(obj_pts, img_pts))
        return out

    @enforce_input_boundary
    def forward(
        self,
        inputs: EstimatorInputs,
        kinematic_prior_pose7: torch.Tensor,
    ) -> CoreOutputV2:
        """Run Stage 0 + Stage 1 + Stage 2 + Stage 3 for the routing target clip.

        Args:
            inputs: see :class:`EstimatorInputs`. Single-camera (wrist_L) MVP-3
                scope per design memo §0.3; multi-cam Phase 2 fields are
                ignored at this stage.
            kinematic_prior_pose7: ``[B, 7]`` env-side prior on the routing
                target clip pose in the camera frame, used as the §4.3
                projection seed for Stage 3 correspondence.

        Returns:
            :class:`CoreOutputV2` with all four stage tensors / lists.

        Raises:
            NotImplementedError: until SAM2 install lands (Stage 1) and the
                §4.3 nominal-pose projection helper is wired in
                :meth:`PnpClipPoseSolver.establish_correspondence` (Stage 3).
        """
        # Stage 0 — kinematic ROI bbox.
        roi_bbox = compute_roi_boxes(
            inputs.wrist_camera_pose_l,
            inputs.routing_target_clip_idx,
            self._intrinsics,
        )
        # Stage 1 — SAM2 zero-shot segmentation.
        prompts = self._build_bbox_prompts(roi_bbox)
        sam2_output = self._sam2.forward(inputs.rgb_l, prompts)  # NotImplementedError until SAM2 install
        # Stage 2 — keypoint extraction from best mask.
        best_mask = self._select_best_mask(sam2_output)
        keypoints_per_batch = self._extract_keypoints(best_mask)
        # Stage 3 — PnP+RANSAC pose recovery.
        pose_per_batch = self._solve_pose_per_batch(keypoints_per_batch, kinematic_prior_pose7)

        return CoreOutputV2(
            roi_bbox=roi_bbox,
            sam2_output=sam2_output,
            keypoints_per_batch=keypoints_per_batch,
            pose_per_batch=pose_per_batch,
            seg_regime_per_batch=list(sam2_output.regime),
            diagnostics={"keypoint_method": self._keypoint_method},
        )

    @staticmethod
    def to_pose14d(
        clip_pose: ClipPoseEstimate,
        segment_pose7: torch.Tensor | None = None,
        device: str | torch.device = "cpu",
    ) -> torch.Tensor:
        """Pack a :class:`ClipPoseEstimate` into the 14D contract slot.

        Per design memo §4.6, ``PoseEstimate14D`` is laid out as
        ``[seg_pos(3), seg_quat(4), clip_pos(3), clip_quat(4)]``. This V2
        fills the clip 7D slot only — the cable target-segment 7D slot is
        owned by L1.A.2 (T-Vision-CableState) and must be supplied by the
        caller via :paramref:`segment_pose7`.

        Args:
            clip_pose: Stage 3 :class:`ClipPoseEstimate` for the routing target
                clip in the camera frame.
            segment_pose7: optional ``[7]`` ``(t, q_xyzw)`` cable target
                segment pose. Set to zeros when L1.A.2 is not yet wired.
            device: target torch device.

        Returns:
            ``[14]`` float32 tensor matching the design memo §4.6 contract.
        """
        clip_pose7 = _pose7_from_estimate(clip_pose)
        if segment_pose7 is None:
            segment_pose7 = torch.zeros(7, dtype=torch.float32)
        return torch.cat([segment_pose7.to(torch.float32), clip_pose7], dim=0).to(device)


def _pose7_from_estimate(estimate: ClipPoseEstimate) -> torch.Tensor:
    """Local helper to convert a :class:`ClipPoseEstimate` to a ``[7]`` tensor.

    Mirrors :meth:`PnpClipPoseSolver.to_pose7_torch` but skips the device move
    so :meth:`PoseEstimatorCoreV2.to_pose14d` can do a single concat + transfer.

    Args:
        estimate: Stage 3 :class:`ClipPoseEstimate`.

    Returns:
        CPU ``[7]`` float32 tensor ``(t_xyz, q_xyzw)``.
    """
    pose7 = np.concatenate([estimate.translation, estimate.quat_xyzw], axis=0).astype(np.float32)
    return torch.from_numpy(pose7)
