# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Phase 1 narrowed estimator core: Stage 0 + Stage 1 only.

Per v3.2 Appendix H + Round 2 v2.1 patch:

- F9 / NHA-aligned: this class is named :class:`PoseEstimatorCorePhase1` and
  has **no** ``stage2``/``stage3``/``stage4`` methods. Callers attempting
  Stage 2-4 raise :class:`AttributeError` naturally — no premature
  abstraction.
- F2 / CC2.C3 / CC3.C1: ``target_segment_prior`` and ``clip_prior`` are
  computed via vectorized :func:`torch.nn.functional.one_hot` /
  :func:`max_pool1d` (no Python ``for w in range(W)`` loops, no
  ``.item()`` syncs).
- F10: :class:`CameraIntrinsics` is a required ``__init__`` arg.
- CC5.C7: device + dtype guards on ``routing_target_seg_idx``.

R6 module boundary: imports are restricted to
``thread_isaac_lab.estimators.*`` — no ``newton`` / no env imports.
"""

from dataclasses import dataclass

import torch
import torch.nn.functional as F

from thread_isaac_lab.estimators.core.roi_prior import CameraIntrinsics, compute_roi_boxes
from thread_isaac_lab.estimators.core.segmenter import LightUNet, SegmenterDiagnostics
from thread_isaac_lab.estimators.core.self_occlusion import compute_self_occlusion_mask
from thread_isaac_lab.estimators.types import EstimatorInputs, enforce_input_boundary

_NUM_CABLE_SEGMENTS = 40
_NUM_CLIPS = 5
_CLIP_TARGET_PRIOR = 0.7
_CLIP_OTHER_PRIOR = 0.075


@dataclass
class Stage0Output:
    """Stage 0 outputs — kinematic prior."""

    roi_l: torch.Tensor  # [B, 1, 4]
    self_occlusion_mask_l: torch.Tensor  # [B, 1, H, W_img] uint8
    target_segment_prior: torch.Tensor  # [B, 40] float32 in [0, 1]
    clip_prior: torch.Tensor  # [B, 5] float32, sums to ~1


@dataclass
class CoreOutputPhase1:
    """Phase 1 estimator output — Stage 0 + Stage 1 only."""

    seg_logits: torch.Tensor  # [B, 3, H, W_img]
    stage0: Stage0Output
    diagnostics: SegmenterDiagnostics


class PoseEstimatorCorePhase1:
    """Phase 1 estimator core: Stage 0 (vectorized) + Stage 1 (LightUNet).

    Stage 2-4 methods are intentionally absent (NHA + CC2.C5 fix). Calling
    ``core.stage2(...)`` raises :class:`AttributeError`, which is the
    explicit signal that Stage 2-4 belong to MVP-1+ and have not yet
    been implemented.
    """

    def __init__(self, segmenter: LightUNet, intrinsics: CameraIntrinsics) -> None:
        self._segmenter = segmenter
        self._intrinsics = intrinsics

    @enforce_input_boundary
    def forward(self, inputs: EstimatorInputs) -> CoreOutputPhase1:
        """Run Stage 0 + Stage 1 forward pass.

        Args:
            inputs: see :class:`EstimatorInputs`. ``routing_target_seg_idx``
                must be ``torch.long`` and on the same device as ``rgb_l``.

        Returns:
            :class:`CoreOutputPhase1`.
        """
        target_seg = inputs.routing_target_seg_idx
        if target_seg.device != inputs.rgb_l.device:
            raise RuntimeError(
                f"routing_target_seg_idx device {target_seg.device} != rgb_l device {inputs.rgb_l.device}"
            )
        if target_seg.dtype != torch.long:
            raise TypeError(f"routing_target_seg_idx dtype {target_seg.dtype} != torch.long")

        # Stage 0 — projection-based ROI + finger self-occlusion.
        roi_l = compute_roi_boxes(
            inputs.wrist_camera_pose_l,
            inputs.routing_target_clip_idx,
            self._intrinsics,
        )
        self_mask = compute_self_occlusion_mask(
            inputs.wrist_camera_pose_l,
            inputs.finger_positions,
            self._intrinsics,
        )

        # Stage 0 — vectorized priors (F2: no Python per-world loop).
        seg_one = F.one_hot(target_seg, _NUM_CABLE_SEGMENTS).float()  # [B, 40]
        # ±1 dilate via max_pool1d kernel=3 stride=1 padding=1.
        seg_dilated = F.max_pool1d(seg_one.unsqueeze(1), kernel_size=3, stride=1, padding=1).squeeze(1)
        clip_one = F.one_hot(inputs.routing_target_clip_idx, _NUM_CLIPS).float()
        clip_prior = clip_one * (_CLIP_TARGET_PRIOR - _CLIP_OTHER_PRIOR) + _CLIP_OTHER_PRIOR

        stage0 = Stage0Output(
            roi_l=roi_l,
            self_occlusion_mask_l=self_mask,
            target_segment_prior=seg_dilated,
            clip_prior=clip_prior,
        )

        # Stage 1 — segmentation forward.
        x = torch.cat([inputs.rgb_l, inputs.depth_l], dim=1)
        seg_logits = self._segmenter(x)
        prob = torch.sigmoid(seg_logits)
        diagnostics = SegmenterDiagnostics(
            seg_confidence_raw=prob.max(dim=1).values.mean(dim=(1, 2)),
            pred_class_distribution=prob.mean(dim=(2, 3)),
        )

        return CoreOutputPhase1(seg_logits=seg_logits, stage0=stage0, diagnostics=diagnostics)
