# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage 1 SAM2 zero-shot segmentation backend (alt path skeleton).

Drop-in replacement for :class:`thread_isaac_lab.estimators.core.segmenter.LightUNet`
in the alternative pose-estimation path defined in
``thread-vault/06-Knowledge/LL-Vision-Pose-Design.md`` §3.

This module is a **skeleton**: actual SAM2 inference requires either
``pip install sam2`` plus a checkpoint download, or ``pip install transformers``
plus HuggingFace hub download. Both paths require Rs permission per the
2026-05-03 ★ directive (autonomous full authority + external dl gate).

R6 module boundary: this module MUST NOT import newton, env, or
WristCameraManager. Enforced by AST lint test
(``tests/test_estimator_module_boundary.py``) per v3.2 Appendix H §H.3.
The lazy SAM2 import is wrapped so that a missing dependency does not break
package import for callers that only need the type stubs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    pass


class PromptKind(Enum):
    """Prompt source for SAM2 zero-shot segmentation (design memo §3.2).

    Bbox is the recommended primary prompt; Point is auxiliary refinement;
    Mask is for temporal smoothing in the §3.4 state machine.
    """

    BBOX = "bbox"
    POINT = "point"
    MASK = "mask"


class InferenceMode(Enum):
    """Inference latency regime (design memo §3.3).

    Only ``OFFLINE_BENCHMARK`` is in MVP-3 scope. ``ASYNC`` and ``DISTILLED`` are
    placeholders for MVP-4+ trigger nodes.
    """

    OFFLINE_BENCHMARK = "offline_benchmark"
    ASYNC = "async"
    DISTILLED = "distilled"


class Sam2Backend(Enum):
    """SAM2 install / load path selection.

    ``FACEBOOKRESEARCH`` uses the official ``sam2`` PyPI package + direct
    checkpoint download from ``dl.fbaipublicfiles.com`` (design memo §3.5).
    ``HUGGINGFACE`` uses ``transformers.Sam2Model.from_pretrained`` which
    avoids the SAM2_BUILD_CUDA extension build issue and downloads the model
    via HuggingFace hub on first access.
    """

    FACEBOOKRESEARCH = "facebookresearch"
    HUGGINGFACE = "huggingface"


@dataclass
class Sam2Config:
    """SAM2 wrapper configuration.

    Attributes:
        backend: install / load path; see :class:`Sam2Backend`.
        variant: model size identifier. ``"hiera_base_plus"`` (~80 M params,
            ~323 MB safetensors via HF) is the design-memo §3.1 default.
        checkpoint_path: filesystem path to the ``.pt`` checkpoint when
            ``backend == FACEBOOKRESEARCH``. Ignored for HUGGINGFACE.
        hf_repo: HuggingFace repo id when ``backend == HUGGINGFACE``. Defaults
            to ``"facebook/sam2.1-hiera-base-plus"`` (transformers ≥4.45 path).
        device: target torch device for both image preprocessing and the
            model forward pass.
        confidence_threshold_high: ``T_high`` for the §3.4 ACCEPT regime.
        confidence_threshold_predict: ``T_predict`` for the PREDICT_TEMPORAL
            regime (FAIL_CLOSED below this).
        inference_mode: latency regime selector; see :class:`InferenceMode`.
    """

    backend: Sam2Backend = Sam2Backend.HUGGINGFACE
    variant: str = "hiera_base_plus"
    checkpoint_path: str | None = None
    hf_repo: str = "facebook/sam2.1-hiera-base-plus"
    device: str = "cuda:0"
    confidence_threshold_high: float = 0.85
    confidence_threshold_predict: float = 0.5
    inference_mode: InferenceMode = InferenceMode.OFFLINE_BENCHMARK


@dataclass
class Sam2Prompt:
    """Per-image prompt bundle (Bbox primary; Point auxiliary; Mask temporal).

    Convention: coordinates are in pixel space of the **input image** to
    :meth:`Sam2Segmenter.forward`, before any internal upsample to the
    SAM2 native 1024×1024 resolution.

    Attributes:
        kind: which prompt channel is the primary signal for this call.
        bbox: ``[B, 4]`` tensor ``(x_min, y_min, x_max, y_max)`` in pixels.
        points: ``[B, K, 2]`` tensor ``(x, y)`` in pixels (K may be 0).
        point_labels: ``[B, K]`` int tensor ``{0, 1}`` (0 = negative click,
            1 = positive click).
        prior_mask: ``[B, 1, H, W]`` float tensor in [0, 1] for temporal
            re-prompting; ``None`` when no prior mask exists.
    """

    kind: PromptKind
    bbox: torch.Tensor | None = None
    points: torch.Tensor | None = None
    point_labels: torch.Tensor | None = None
    prior_mask: torch.Tensor | None = None


class SegmentRegime(Enum):
    """Per-frame regime decision after temporal smoothing (design memo §3.4).

    Mirrors the CC4 v3.2 §5.6 state machine so downstream consumers can stay
    on the same ``policy_update_mask`` contract regardless of which Stage 1
    backend (LightUNet vs SAM2) produced the mask.
    """

    ACCEPT = "accept"
    PREDICT_TEMPORAL = "predict_temporal"
    FALLBACK = "fallback"
    FAIL_CLOSED = "fail_closed"


@dataclass
class Sam2Output:
    """Stage 1 SAM2 segmenter output.

    Attributes:
        masks: ``[B, num_masks, H, W]`` sigmoid probabilities in [0, 1].
            ``num_masks`` follows SAM2's multimask_output (default 3).
        iou_scores: ``[B, num_masks]`` model-predicted mask quality scores.
        confidence: ``[B]`` per-frame max IoU score, used for §3.4 regime
            classification.
        regime: per-frame :class:`SegmentRegime`, length B.
    """

    masks: torch.Tensor
    iou_scores: torch.Tensor
    confidence: torch.Tensor
    regime: list[SegmentRegime] = field(default_factory=list)


class Sam2Segmenter:
    """Zero-shot SAM2 backend for Stage 1 segmentation (alt path).

    Skeleton scope: import lazy-loaded to keep the package importable even
    when SAM2 dependencies are absent. ``forward`` raises
    :class:`NotImplementedError` until the dependency-install task lands;
    callers can still construct the instance and inspect :attr:`config`.

    Args:
        config: see :class:`Sam2Config`.

    Raises:
        ModuleNotFoundError: if :meth:`forward` is invoked while neither
            ``sam2`` nor ``transformers`` is importable in the active venv.
    """

    def __init__(self, config: Sam2Config) -> None:
        self.config = config
        self._model: Any | None = None
        self._processor: Any | None = None

    def _lazy_load(self) -> None:
        """Import the SAM2 backend on first :meth:`forward` call.

        Defers heavy imports until inference is actually needed. The two
        supported install paths are mutually exclusive — the active
        :attr:`Sam2Config.backend` selects which.
        """
        if self._model is not None:
            return
        if self.config.backend is Sam2Backend.HUGGINGFACE:
            self._lazy_load_huggingface()
        elif self.config.backend is Sam2Backend.FACEBOOKRESEARCH:
            self._lazy_load_facebookresearch()
        else:
            raise ValueError(f"Unknown Sam2Backend: {self.config.backend}")

    def _lazy_load_huggingface(self) -> None:
        raise NotImplementedError(
            "SAM2 HuggingFace path requires `pip install transformers` (≥4.45)"
            " plus first-time HF hub download. Both gated on Rs permission per"
            " 2026-05-03 ★ directive — see report attached to the prep dispatch."
        )

    def _lazy_load_facebookresearch(self) -> None:
        raise NotImplementedError(
            "SAM2 facebookresearch path requires `pip install sam2` plus the"
            " sam2_hiera_base_plus.pt checkpoint download (~323 MB). Both gated"
            " on Rs permission per 2026-05-03 ★ directive."
        )

    def forward(self, rgb: torch.Tensor, prompts: list[Sam2Prompt]) -> Sam2Output:
        """Run SAM2 zero-shot segmentation on a batch of frames.

        Args:
            rgb: ``[B, 3, H, W]`` float tensor in [0, 1] on
                :attr:`Sam2Config.device`. The wrapper upsamples internally
                to SAM2's native 1024×1024 input and downsamples mask output
                back to ``H × W`` (lossy per design memo §3.1).
            prompts: list of length ``B`` with per-frame :class:`Sam2Prompt`.
                Mixed prompt kinds across the batch are supported; the
                wrapper dispatches per kind internally.

        Returns:
            :class:`Sam2Output` with sigmoid masks, IoU scores, confidence
            scalar, and per-frame :class:`SegmentRegime`.

        Raises:
            NotImplementedError: until the SAM2 install task completes.
        """
        self._lazy_load()  # raises NotImplementedError in skeleton phase
        raise NotImplementedError(
            "Sam2Segmenter.forward: implementation pending SAM2 install task."
            " See LL-Vision-Pose-Design.md §3 and the prep-dispatch report."
        )

    def classify_regime(self, confidence: torch.Tensor) -> list[SegmentRegime]:
        """Map per-frame confidence to :class:`SegmentRegime` (§3.4).

        Args:
            confidence: ``[B]`` float tensor in [0, 1].

        Returns:
            length-B list of regimes. ``ACCEPT`` if conf > T_high; ``FAIL_CLOSED``
            if conf < T_predict; ``PREDICT_TEMPORAL`` between. ``FALLBACK`` is
            reserved for downstream Stage 2 keypoint-cardinality failures and
            is not produced here.
        """
        t_high = self.config.confidence_threshold_high
        t_predict = self.config.confidence_threshold_predict
        out: list[SegmentRegime] = []
        for c in confidence.detach().cpu().tolist():
            if c > t_high:
                out.append(SegmentRegime.ACCEPT)
            elif c < t_predict:
                out.append(SegmentRegime.FAIL_CLOSED)
            else:
                out.append(SegmentRegime.PREDICT_TEMPORAL)
        return out
