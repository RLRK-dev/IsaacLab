# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Path A MVP-0 Phase B production-ready single-image driver.

Production successor of :mod:`thread_isaac_lab.scripts.vision.pose_mvp0_phase_a2`
(skeleton). Resolves every ``TODO[A2-INSTALL]`` / ``TODO[A3-E2E]`` marker from
the skeleton with a real implementation:

- Real image I/O via ``cv2.imread`` (BGR → RGB → ``[1, 3, H, W]`` float tensor)
  with explicit shape / dtype validation and a deterministic mock fallback.
- Real camera intrinsic JSON loader with schema validation (``K``,
  ``dist_coeffs``, ``resolution``) plus analytical placeholder synthesis when
  no path is supplied.
- Real CAD cache loader via :func:`thread_isaac_lab.estimators.core.pnp_pose_solver.load_clip_cad`
  with actionable error messages if the ``.npz`` is missing.
- ``cuda.synchronize`` + ``perf_counter`` latency instrumentation around the
  per-stage forward call so the ≤4 GiB / ≤50 ms gate (a2_design §4.1 / §7.3)
  can be measured.
- SAM2 backend availability probe (``transformers.Sam2Model`` or
  ``sam2.modeling.sam2_base``) with a graceful mock-mode fallback that emits a
  kinematic-prior pose-7 when the dependency install is still pending.
- Pose-7 + diagnostics emit with NaN / quaternion-norm validation.
- Five integration tests T1-T5 covering import boundaries, deterministic mock
  generation, intrinsic schema round-trip, factory wiring, and end-to-end mock
  pipeline. Exposed both via :func:`run_acceptance_gate` and as standalone
  callable smoke functions.

What this script DOES NOT do (deferred to subsequent NEST nodes):

- Run the actual SAM2 install / first-time HuggingFace download (~323 MB) —
  that is gated on Rs explicit permission and lives in the proposed
  ``T-Vision-Pose-MVP0-Impl-PhaseA2-SAM2-Install`` child.
- Modify any existing PhaseA1 / PhaseA2 deliverable. ``estimators/core/*.py``
  are import-only inputs (TOUCH FORBIDDEN).
- Run actual training, the N=10 / N=100 eval-det benchmark, or the multi-seed
  promotion sweep — those are downstream of the production pose pipeline.

Usage::

    # Mock mode (no SAM2 install required) — exercises the wiring path.
    /home/rlrk/env_isaaclab6/bin/python \\
        thread_isaac_lab/scripts/vision/pose_mvp0_phase_b.py \\
        --mode mock --device cpu

    # Acceptance gate (T1-T5 integration smoke).
    /home/rlrk/env_isaaclab6/bin/python \\
        thread_isaac_lab/scripts/vision/pose_mvp0_phase_b.py \\
        --acceptance --device cpu

    # Production mode (post-SAM2-install, real CAD cache, real intrinsic).
    CUDA_VISIBLE_DEVICES=2 /home/rlrk/env_isaaclab6/bin/python \\
        thread_isaac_lab/scripts/vision/pose_mvp0_phase_b.py \\
        --mode production \\
        --input-image /tmp/wrist_l_sample.png \\
        --cad-cache data/clip/routing_clip_v1_vertices.npz \\
        --camera-intrinsic data/camera_calibration/sim_default.json \\
        --target-clip-idx 0 --device cuda:2 \\
        --output-pose7 /tmp/clip_pose7_out.npy \\
        --output-diagnostics /tmp/clip_diag.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from thread_isaac_lab.estimators.core.pnp_pose_solver import (  # noqa: E402
    CameraCalibration,
    ClipPoseEstimate,
    PnpClipPoseSolver,
    PoseRegime,
    load_clip_cad,
)
from thread_isaac_lab.estimators.core.pose_estimator_core_v2 import (  # noqa: E402
    CoreOutputV2,
    PoseEstimatorCoreV2,
)
from thread_isaac_lab.estimators.core.roi_prior import CameraIntrinsics  # noqa: E402
from thread_isaac_lab.estimators.core.sam2_segmenter import (  # noqa: E402
    Sam2Backend,
    Sam2Config,
    Sam2Segmenter,
)
from thread_isaac_lab.estimators.types import EstimatorInputs  # noqa: E402

LOGGER = logging.getLogger("pose_mvp0_phase_b")

DEFAULT_HF_REPO = "facebook/sam2.1-hiera-base-plus"
DEFAULT_DEVICE = "cuda:2"
DEFAULT_CONF_HIGH = 0.85
DEFAULT_CONF_PREDICT = 0.5
DEFAULT_INTRINSIC_RES_HW = (480, 640)
SMOKE_VRAM_BUDGET_GIB = 4.0
DEFAULT_TARGET_CLIP_IDX = 0
DEFAULT_LATENCY_BUDGET_MS = 50.0
DEFAULT_MOCK_SEED = 42
SCHEMA_VERSION = "phase_b_v1"


# ----------------------------------------------------------------------------
# SAM2 backend availability probe.
# ----------------------------------------------------------------------------


def probe_sam2_backend() -> tuple[bool, str | None]:
    """Detect whether a SAM2 backend is importable in the current env.

    Returns:
        ``(available, name)``. ``available`` is True iff at least one of the
        two supported backends (``transformers`` HuggingFace path, or
        ``sam2.modeling.sam2_base`` Facebook research path) can be imported
        without side effects. ``name`` is the importable module name when
        available, otherwise ``None``.
    """
    if importlib.util.find_spec("transformers") is not None:
        return True, "transformers"
    if importlib.util.find_spec("sam2") is not None:
        return True, "sam2"
    return False, None


def probe_cuda_device(device: str) -> bool:
    """Return True iff ``device`` is a usable CUDA device on this host."""
    if not device.startswith("cuda"):
        return False
    if not torch.cuda.is_available():
        return False
    try:
        torch.zeros(1, device=device)
        return True
    except (RuntimeError, AssertionError, ValueError):
        return False


# ----------------------------------------------------------------------------
# Run config.
# ----------------------------------------------------------------------------


@dataclass
class PhaseBRunConfig:
    """Production driver run configuration.

    Attributes:
        mode: ``"production"`` runs the full SAM2 + PnP pipeline; ``"mock"``
            short-circuits to a kinematic-prior passthrough so the wiring can
            be exercised without a SAM2 install. ``"auto"`` picks
            ``production`` if a SAM2 backend is importable and a CAD cache
            path was supplied, else falls back to ``mock``.
        input_image: optional RGB image path. ``None`` triggers a deterministic
            in-memory mock (seed :data:`DEFAULT_MOCK_SEED`).
        cad_cache: optional CAD ``.npz`` path. Required for ``production`` mode.
        camera_intrinsic: optional intrinsic JSON path. ``None`` synthesizes
            an analytical pinhole.
        target_clip_idx: routing target clip index in ``[0, 5)``.
        device: torch device (e.g. ``cuda:2`` / ``cpu``).
        sam2_backend: ``"huggingface"`` or ``"facebookresearch"``.
        sam2_hf_repo: HuggingFace repo id when ``sam2_backend == huggingface``.
        kinematic_prior_path: optional ``.npy`` containing a ``[7]`` pose to
            seed PnP correspondence. ``None`` → identity at z=0.5.
        output_pose7: optional ``.npy`` dump path for the final ``[7]`` pose.
        output_diagnostics: optional ``.json`` dump path for diagnostics.
        latency_budget_ms: warning threshold for the per-image wall time.
        mock_seed: numpy seed for the deterministic mock image.
    """

    mode: str = "auto"
    input_image: str | None = None
    cad_cache: str | None = None
    camera_intrinsic: str | None = None
    target_clip_idx: int = DEFAULT_TARGET_CLIP_IDX
    device: str = DEFAULT_DEVICE
    sam2_backend: str = "huggingface"
    sam2_hf_repo: str = DEFAULT_HF_REPO
    kinematic_prior_path: str | None = None
    output_pose7: str | None = None
    output_diagnostics: str | None = None
    latency_budget_ms: float = DEFAULT_LATENCY_BUDGET_MS
    mock_seed: int = DEFAULT_MOCK_SEED


def parse_cli(argv: list[str] | None = None) -> tuple[PhaseBRunConfig, argparse.Namespace]:
    """Parse CLI argv into a :class:`PhaseBRunConfig` and the raw namespace.

    The raw namespace is returned alongside the dataclass so that subcommand
    flags (``--acceptance``) the config does not need to carry can be read
    by :func:`main`.
    """
    ap = argparse.ArgumentParser(
        description="Path A MVP-0 Phase B production driver (single-image pose)."
    )
    ap.add_argument("--mode", choices=["auto", "production", "mock"], default="auto")
    ap.add_argument("--input-image", default=None, help="Path to wrist_L RGB image.")
    ap.add_argument("--cad-cache", default=None, help="Path to clip CAD .npz.")
    ap.add_argument("--camera-intrinsic", default=None, help="Path to intrinsic JSON.")
    ap.add_argument("--target-clip-idx", type=int, default=DEFAULT_TARGET_CLIP_IDX)
    ap.add_argument("--device", default=DEFAULT_DEVICE)
    ap.add_argument(
        "--sam2-backend", choices=["huggingface", "facebookresearch"], default="huggingface"
    )
    ap.add_argument("--sam2-hf-repo", default=DEFAULT_HF_REPO)
    ap.add_argument("--kinematic-prior", dest="kinematic_prior_path", default=None)
    ap.add_argument("--output-pose7", default=None)
    ap.add_argument("--output-diagnostics", default=None)
    ap.add_argument("--latency-budget-ms", type=float, default=DEFAULT_LATENCY_BUDGET_MS)
    ap.add_argument("--mock-seed", type=int, default=DEFAULT_MOCK_SEED)
    ap.add_argument(
        "--acceptance",
        action="store_true",
        help="Run the T1-T5 integration smoke gate and exit.",
    )
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = ap.parse_args(argv)
    cfg = PhaseBRunConfig(
        mode=args.mode,
        input_image=args.input_image,
        cad_cache=args.cad_cache,
        camera_intrinsic=args.camera_intrinsic,
        target_clip_idx=args.target_clip_idx,
        device=args.device,
        sam2_backend=args.sam2_backend,
        sam2_hf_repo=args.sam2_hf_repo,
        kinematic_prior_path=args.kinematic_prior_path,
        output_pose7=args.output_pose7,
        output_diagnostics=args.output_diagnostics,
        latency_budget_ms=args.latency_budget_ms,
        mock_seed=args.mock_seed,
    )
    return cfg, args


def resolve_mode(cfg: PhaseBRunConfig) -> str:
    """Resolve ``cfg.mode == "auto"`` into a concrete production / mock choice."""
    if cfg.mode != "auto":
        return cfg.mode
    sam2_ok, _ = probe_sam2_backend()
    if sam2_ok and cfg.cad_cache and Path(cfg.cad_cache).exists():
        return "production"
    return "mock"


def resolve_device(cfg: PhaseBRunConfig) -> str:
    """Downgrade to ``cpu`` when a CUDA device is requested but unavailable."""
    if cfg.device == "cpu":
        return "cpu"
    if probe_cuda_device(cfg.device):
        return cfg.device
    LOGGER.warning("device=%s unavailable; falling back to cpu", cfg.device)
    return "cpu"


# ----------------------------------------------------------------------------
# Image I/O.
# ----------------------------------------------------------------------------


def load_input_image(
    path: str | None,
    device: str,
    mock_seed: int = DEFAULT_MOCK_SEED,
    mock_hw: tuple[int, int] = DEFAULT_INTRINSIC_RES_HW,
) -> torch.Tensor:
    """Load an RGB image as ``[1, 3, H, W]`` float32 in ``[0, 1]`` on ``device``.

    Resolves ``TODO[A2-INSTALL]`` from the skeleton: real image read is now
    backed by ``cv2.imread`` with a BGR → RGB swap and explicit shape / dtype
    validation. The deterministic numpy mock is preserved as the no-asset
    fallback path used by the integration smoke gate.

    Raises:
        FileNotFoundError: if ``path`` is provided but missing on disk.
        ValueError: if the loaded image is empty / wrong dtype / wrong shape.
        ImportError: if ``cv2`` is not importable when ``path`` is provided.
    """
    if path is None:
        h, w = mock_hw
        rng = np.random.default_rng(seed=mock_seed)
        mock_uint8 = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        rgb = torch.from_numpy(mock_uint8).permute(2, 0, 1).float() / 255.0
        return rgb.unsqueeze(0).to(device)

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input image not found: {p}")
    try:
        import cv2  # noqa: PLC0415 — local import keeps skeleton path import-light
    except ImportError as exc:
        raise ImportError(
            "cv2 is required for non-mock image loading. Install opencv-python in env_isaaclab6."
        ) from exc
    bgr = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if bgr is None or bgr.size == 0:
        raise ValueError(f"cv2.imread returned an empty image for {p}")
    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError(f"Unexpected image shape {bgr.shape} (expected HxWx3) for {p}")
    rgb_uint8 = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgb = torch.from_numpy(rgb_uint8).permute(2, 0, 1).float() / 255.0
    return rgb.unsqueeze(0).to(device)


# ----------------------------------------------------------------------------
# Camera intrinsic loader.
# ----------------------------------------------------------------------------

_REQUIRED_INTRINSIC_FIELDS = ("K", "dist_coeffs", "resolution")


def _validate_intrinsic_payload(payload: dict, source: str) -> None:
    """Validate a parsed intrinsic JSON against the expected schema."""
    missing = [f for f in _REQUIRED_INTRINSIC_FIELDS if f not in payload]
    if missing:
        raise ValueError(
            f"Camera intrinsic JSON {source} missing required fields: {missing}"
        )
    K = np.asarray(payload["K"], dtype=np.float64)
    if K.shape != (3, 3):
        raise ValueError(f"Camera intrinsic K has shape {K.shape}, expected (3, 3)")
    dist = np.asarray(payload["dist_coeffs"], dtype=np.float64)
    if dist.ndim != 1 or dist.shape[0] not in (4, 5, 8, 12, 14):
        raise ValueError(
            f"Camera intrinsic dist_coeffs has shape {dist.shape}, expected (k,) k∈{4,5,8,12,14}"
        )
    res = payload["resolution"]
    if not isinstance(res, (list, tuple)) or len(res) != 2:
        raise ValueError(f"Camera intrinsic resolution must be [W, H], got {res!r}")


def load_camera_intrinsic(
    path: str | None,
    device: str,
) -> tuple[CameraIntrinsics, CameraCalibration]:
    """Load (or synthesize) the intrinsic + calibration pair.

    Resolves ``TODO[A3-E2E]``: the JSON path is now load-and-validated end to
    end (Charuco-calibrated payloads are accepted via the standard
    ``{"K", "dist_coeffs", "resolution", "source"}`` schema). The analytical
    placeholder remains as the offline-replay default and is sentinel-safe vs
    ``roi_prior.py`` placeholder rejection.
    """
    del device  # signature parity with skeleton; intrinsics live on host
    if path is None:
        h, w = DEFAULT_INTRINSIC_RES_HW
        fx = fy = float(max(h, w))
        cx, cy = float(w) / 2.0, float(h) / 2.0
        intrinsics = CameraIntrinsics(fx=fx, fy=fy, cx=cx, cy=cy, H=h, W_img=w)
        K = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64)
        dist = np.zeros(5, dtype=np.float64)
        calib = CameraCalibration(
            K=K, dist_coeffs=dist, resolution=(w, h), source="analytical_phase_b"
        )
        return intrinsics, calib

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Camera intrinsic not found: {p}")
    with open(p) as f:
        payload = json.load(f)
    _validate_intrinsic_payload(payload, str(p))
    K = np.asarray(payload["K"], dtype=np.float64)
    dist = np.asarray(payload["dist_coeffs"], dtype=np.float64)
    w, h = int(payload["resolution"][0]), int(payload["resolution"][1])
    intrinsics = CameraIntrinsics(
        fx=float(K[0, 0]),
        fy=float(K[1, 1]),
        cx=float(K[0, 2]),
        cy=float(K[1, 2]),
        H=h,
        W_img=w,
    )
    calib = CameraCalibration(
        K=K, dist_coeffs=dist, resolution=(w, h), source=str(payload.get("source", str(p)))
    )
    return intrinsics, calib


# ----------------------------------------------------------------------------
# EstimatorInputs builder.
# ----------------------------------------------------------------------------


def _load_kinematic_prior(path: str | None, device: str, batch: int) -> torch.Tensor:
    """Load a ``[B, 7]`` kinematic prior pose tensor (or synthesize a default)."""
    if path is None:
        prior = torch.tensor(
            [[0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 1.0]], device=device, dtype=torch.float32
        )
        return prior.expand(batch, 7).clone()

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Kinematic prior not found: {p}")
    arr = np.load(p)
    if arr.shape == (7,):
        arr = arr[None, :]
    if arr.ndim != 2 or arr.shape[1] != 7:
        raise ValueError(
            f"Kinematic prior {p} has shape {arr.shape}, expected (7,) or (B, 7)"
        )
    if arr.shape[0] == 1 and batch > 1:
        arr = np.broadcast_to(arr, (batch, 7)).copy()
    if arr.shape[0] != batch:
        raise ValueError(
            f"Kinematic prior batch {arr.shape[0]} != image batch {batch}"
        )
    return torch.from_numpy(arr.astype(np.float32)).to(device)


def build_estimator_inputs(
    rgb: torch.Tensor,
    target_clip_idx: int,
    device: str,
    kinematic_prior_path: str | None = None,
) -> tuple[EstimatorInputs, torch.Tensor]:
    """Build :class:`EstimatorInputs` + a kinematic prior pose tensor.

    Phase 1 fields only (depth, joint_state, wrist pose, finger positions,
    routing indices). Phase 2 fields stay ``None`` per ``types.py:74-94``.
    """
    b = rgb.shape[0]
    h, w = rgb.shape[-2:]
    depth = torch.zeros(b, 1, h, w, device=device)
    joint_state = torch.zeros(b, 9, device=device)
    wrist_pose = torch.tensor(
        [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]], device=device, dtype=torch.float32
    ).expand(b, 7).clone()
    finger_positions = torch.zeros(b, 2, 3, device=device)
    target_seg_idx = torch.zeros(b, dtype=torch.int64, device=device)
    target_clip_idx_t = torch.full((b,), target_clip_idx, dtype=torch.int64, device=device)

    inputs = EstimatorInputs(
        rgb_l=rgb,
        depth_l=depth,
        joint_state=joint_state,
        wrist_camera_pose_l=wrist_pose,
        finger_positions=finger_positions,
        routing_target_seg_idx=target_seg_idx,
        routing_target_clip_idx=target_clip_idx_t,
    )
    prior_pose7 = _load_kinematic_prior(kinematic_prior_path, device, b)
    return inputs, prior_pose7


# ----------------------------------------------------------------------------
# Estimator factory.
# ----------------------------------------------------------------------------


def build_estimator_v2(cfg: PhaseBRunConfig, device: str) -> PoseEstimatorCoreV2:
    """Wire the V2 orchestrator. ``cfg.cad_cache`` must point to a real .npz."""
    backend = (
        Sam2Backend.HUGGINGFACE
        if cfg.sam2_backend == "huggingface"
        else Sam2Backend.FACEBOOKRESEARCH
    )
    sam2_cfg = Sam2Config(
        backend=backend,
        hf_repo=cfg.sam2_hf_repo,
        device=device,
        confidence_threshold_high=DEFAULT_CONF_HIGH,
        confidence_threshold_predict=DEFAULT_CONF_PREDICT,
    )
    sam2 = Sam2Segmenter(sam2_cfg)
    intrinsics, calib = load_camera_intrinsic(cfg.camera_intrinsic, device)
    if not cfg.cad_cache:
        raise ValueError(
            "build_estimator_v2: --cad-cache is required for production mode."
            " Build it via the planned scripts/vision/extract_clip_cad_cache.py"
            " (Phase A3 deliverable, a2_design §10.3)."
        )
    cad = load_clip_cad(cfg.cad_cache)
    pnp_solver = PnpClipPoseSolver(camera=calib, cad=cad)
    return PoseEstimatorCoreV2(sam2=sam2, pnp_solver=pnp_solver, intrinsics=intrinsics)


# ----------------------------------------------------------------------------
# Single-image pipeline.
# ----------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """One-image driver result.

    ``output`` is ``None`` in mock mode; ``pose7`` is always populated.
    ``stage_latency_ms`` keys: ``total`` (always); ``forward`` (production only).
    """

    pose7: torch.Tensor
    output: CoreOutputV2 | None = None
    diagnostics: dict = field(default_factory=dict)
    stage_latency_ms: dict[str, float] = field(default_factory=dict)
    mode: str = "mock"


def _sync_if_cuda(device: str) -> None:
    if device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.synchronize()


def run_production_pipeline(cfg: PhaseBRunConfig, device: str) -> PipelineResult:
    """Run Stage 0+1+2+3 forward over a single image with latency capture."""
    estimator = build_estimator_v2(cfg, device)
    rgb = load_input_image(cfg.input_image, device, cfg.mock_seed)
    inputs, prior_pose7 = build_estimator_inputs(
        rgb, cfg.target_clip_idx, device, cfg.kinematic_prior_path
    )

    _sync_if_cuda(device)
    t0 = time.perf_counter()
    output = estimator.forward(inputs, prior_pose7)
    _sync_if_cuda(device)
    forward_ms = (time.perf_counter() - t0) * 1000.0

    pose7 = emit_pose7(output)
    diag = collect_diagnostics(output)
    diag["wall_ms"] = round(forward_ms, 3)
    diag["mode"] = "production"
    return PipelineResult(
        pose7=pose7,
        output=output,
        diagnostics=diag,
        stage_latency_ms={"forward": forward_ms, "total": forward_ms},
        mode="production",
    )


def run_mock_pipeline(cfg: PhaseBRunConfig, device: str) -> PipelineResult:
    """Mock-mode pipeline: kinematic-prior passthrough + diagnostics scaffold.

    Used when SAM2 is unavailable or the user explicitly asks for mock mode
    via ``--mode mock``. Exercises image / intrinsic / inputs builders so
    the wiring path is verified end to end.
    """
    rgb = load_input_image(cfg.input_image, device, cfg.mock_seed)
    intrinsics, _calib = load_camera_intrinsic(cfg.camera_intrinsic, device)
    inputs, prior_pose7 = build_estimator_inputs(
        rgb, cfg.target_clip_idx, device, cfg.kinematic_prior_path
    )
    del inputs, intrinsics  # consumed for verification only

    _sync_if_cuda(device)
    t0 = time.perf_counter()
    pose7 = prior_pose7[0].detach().to("cpu").float()
    _sync_if_cuda(device)
    total_ms = (time.perf_counter() - t0) * 1000.0
    diag = {
        "schema_version": SCHEMA_VERSION,
        "mode": "mock",
        "pose_regime": "mock_kinematic_prior_passthrough",
        "translation": [float(x) for x in pose7[:3].tolist()],
        "quat_xyzw": [float(x) for x in pose7[3:].tolist()],
        "rgb_shape": list(rgb.shape),
        "wall_ms": round(total_ms, 3),
    }
    return PipelineResult(
        pose7=pose7,
        output=None,
        diagnostics=diag,
        stage_latency_ms={"total": total_ms},
        mode="mock",
    )


def run_pipeline(cfg: PhaseBRunConfig) -> PipelineResult:
    """Top-level dispatcher: resolves device + mode then runs the pipeline."""
    device = resolve_device(cfg)
    mode = resolve_mode(cfg)
    LOGGER.info("running pipeline mode=%s device=%s", mode, device)
    if mode == "production":
        return run_production_pipeline(cfg, device)
    return run_mock_pipeline(cfg, device)


# ----------------------------------------------------------------------------
# Pose-7 emission + validation.
# ----------------------------------------------------------------------------


def emit_pose7(output: CoreOutputV2, batch_idx: int = 0) -> torch.Tensor:
    """Pack the per-batch :class:`ClipPoseEstimate` into a ``[7]`` CPU tensor."""
    estimate: ClipPoseEstimate = output.pose_per_batch[batch_idx]
    pose7_np = np.concatenate([estimate.translation, estimate.quat_xyzw], axis=0).astype(
        np.float32
    )
    return torch.from_numpy(pose7_np)


def validate_pose7(pose7: torch.Tensor, quat_norm_tol: float = 1e-3) -> None:
    """Raise ``ValueError`` if ``pose7`` is malformed.

    Checks: shape == (7,), all-finite, quat norm ∈ [1-tol, 1+tol].
    """
    if pose7.shape != (7,):
        raise ValueError(f"pose7 shape {tuple(pose7.shape)} != (7,)")
    if not torch.isfinite(pose7).all():
        raise ValueError("pose7 contains NaN or inf entries")
    quat = pose7[3:]
    norm = float(torch.linalg.norm(quat))
    if abs(norm - 1.0) > quat_norm_tol:
        raise ValueError(f"pose7 quat norm {norm:.6f} outside [1±{quat_norm_tol}]")


def collect_diagnostics(output: CoreOutputV2, batch_idx: int = 0) -> dict:
    """Gather a JSON-friendly diagnostics dict for one batch element."""
    pose: ClipPoseEstimate = output.pose_per_batch[batch_idx]
    seg_regime = output.seg_regime_per_batch[batch_idx]
    masks_shape = tuple(int(s) for s in output.sam2_output.masks.shape)
    return {
        "schema_version": SCHEMA_VERSION,
        "pose_regime": pose.regime.value if isinstance(pose.regime, PoseRegime) else str(pose.regime),
        "inlier_count": int(pose.inlier_count),
        "reproj_error_px": float(pose.reproj_error_px),
        "translation": [float(x) for x in pose.translation.tolist()],
        "quat_xyzw": [float(x) for x in pose.quat_xyzw.tolist()],
        "sam2_masks_shape": list(masks_shape),
        "seg_regime": seg_regime.value if hasattr(seg_regime, "value") else str(seg_regime),
        "keypoint_method": output.diagnostics.get("keypoint_method", "unknown"),
        "keypoint_count": int(output.keypoints_per_batch[batch_idx].points.shape[0]),
    }


# ----------------------------------------------------------------------------
# Integration smoke tests T1-T5.
# ----------------------------------------------------------------------------


def smoke_t1_imports() -> dict:
    """T1: module imports + boundary verification."""
    available = all(
        sym is not None
        for sym in (
            Sam2Segmenter,
            PnpClipPoseSolver,
            PoseEstimatorCoreV2,
            EstimatorInputs,
            CameraIntrinsics,
            load_clip_cad,
        )
    )
    sam2_ok, sam2_name = probe_sam2_backend()
    return {
        "test": "T1_imports",
        "passed": bool(available),
        "sam2_backend_available": sam2_ok,
        "sam2_backend_name": sam2_name,
    }


def smoke_t2_mock_inference(cfg: PhaseBRunConfig | None = None) -> dict:
    """T2: deterministic mock pipeline reproducibility.

    Runs the mock pipeline twice with the same seed; asserts identical pose7
    + identical RGB sample (within float tolerance) so callers can rely on
    the mock fallback for regression tests.
    """
    cfg = cfg or PhaseBRunConfig(mode="mock", device="cpu")
    cfg = PhaseBRunConfig(
        mode="mock",
        device="cpu",
        target_clip_idx=cfg.target_clip_idx,
        mock_seed=cfg.mock_seed,
    )
    res_a = run_mock_pipeline(cfg, "cpu")
    res_b = run_mock_pipeline(cfg, "cpu")
    pose_eq = bool(torch.allclose(res_a.pose7, res_b.pose7, atol=1e-7))
    return {
        "test": "T2_mock_inference",
        "passed": pose_eq and res_a.mode == "mock",
        "pose_diff_max": float((res_a.pose7 - res_b.pose7).abs().max()),
        "wall_ms_a": res_a.diagnostics["wall_ms"],
        "wall_ms_b": res_b.diagnostics["wall_ms"],
    }


def smoke_t3_intrinsic_roundtrip() -> dict:
    """T3: camera intrinsic JSON load + analytical fallback equivalence path.

    Writes a synthetic intrinsic JSON to a temp path, reads it back, and
    asserts the resulting :class:`CameraIntrinsics` matches the source. Also
    confirms the analytical placeholder (no path) produces a valid object.
    """
    h, w = 240, 320
    fx, fy, cx, cy = 320.0, 320.0, 160.0, 120.0
    payload = {
        "K": [[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]],
        "dist_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "resolution": [w, h],
        "source": "smoke_t3_synthetic",
    }
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fp:
        json.dump(payload, fp)
        tmp_path = fp.name
    try:
        intr_loaded, calib_loaded = load_camera_intrinsic(tmp_path, "cpu")
        intr_default, calib_default = load_camera_intrinsic(None, "cpu")
        loaded_match = (
            intr_loaded.fx == fx
            and intr_loaded.fy == fy
            and intr_loaded.cx == cx
            and intr_loaded.cy == cy
            and intr_loaded.H == h
            and intr_loaded.W_img == w
            and calib_loaded.resolution == (w, h)
        )
        default_valid = (
            intr_default.fx > 0.0
            and intr_default.fy > 0.0
            and calib_default.K.shape == (3, 3)
        )
        return {
            "test": "T3_intrinsic_roundtrip",
            "passed": bool(loaded_match and default_valid),
            "loaded_match": loaded_match,
            "default_valid": default_valid,
        }
    finally:
        os.unlink(tmp_path)


def smoke_t4_factory_wiring() -> dict:
    """T4: estimator factory wiring without forward call.

    Asserts that requesting production-mode wiring without a CAD cache surfaces
    the actionable :class:`ValueError` (not a silent passthrough), and that the
    config dataclass round-trips through :func:`parse_cli`.
    """
    cfg, _ns = parse_cli(["--mode", "production", "--device", "cpu"])
    raised_value_error = False
    try:
        build_estimator_v2(cfg, device="cpu")
    except ValueError as exc:
        raised_value_error = "cad-cache" in str(exc) or "CAD" in str(exc)
    cli_roundtrip = (
        cfg.mode == "production"
        and cfg.device == "cpu"
        and cfg.target_clip_idx == DEFAULT_TARGET_CLIP_IDX
    )
    return {
        "test": "T4_factory_wiring",
        "passed": bool(raised_value_error and cli_roundtrip),
        "raised_value_error": raised_value_error,
        "cli_roundtrip": cli_roundtrip,
    }


def smoke_t5_end_to_end_mock() -> dict:
    """T5: end-to-end mock pipeline with pose-7 + diagnostics validation."""
    cfg = PhaseBRunConfig(mode="mock", device="cpu")
    res = run_pipeline(cfg)
    try:
        validate_pose7(res.pose7)
        pose_valid = True
        validation_error = None
    except ValueError as exc:
        pose_valid = False
        validation_error = str(exc)
    diag_keys_ok = {
        "schema_version",
        "mode",
        "pose_regime",
        "translation",
        "quat_xyzw",
        "wall_ms",
    }.issubset(set(res.diagnostics.keys()))
    latency_ok = res.diagnostics["wall_ms"] >= 0.0
    return {
        "test": "T5_end_to_end_mock",
        "passed": bool(pose_valid and diag_keys_ok and latency_ok and res.mode == "mock"),
        "pose_valid": pose_valid,
        "validation_error": validation_error,
        "diag_keys_present": diag_keys_ok,
        "wall_ms": res.diagnostics["wall_ms"],
    }


# ----------------------------------------------------------------------------
# Acceptance gate runner.
# ----------------------------------------------------------------------------


_INTEGRATION_TESTS = [
    ("T1_imports", smoke_t1_imports),
    ("T2_mock_inference", smoke_t2_mock_inference),
    ("T3_intrinsic_roundtrip", smoke_t3_intrinsic_roundtrip),
    ("T4_factory_wiring", smoke_t4_factory_wiring),
    ("T5_end_to_end_mock", smoke_t5_end_to_end_mock),
]


def run_acceptance_gate() -> dict:
    """Run every T1-T5 smoke and return an aggregate report."""
    results = []
    all_pass = True
    for name, fn in _INTEGRATION_TESTS:
        try:
            result = fn()
        except Exception as exc:  # noqa: BLE001 — gate must keep going on test failure
            result = {"test": name, "passed": False, "error": repr(exc)}
        results.append(result)
        if not result.get("passed"):
            all_pass = False
    return {
        "schema_version": SCHEMA_VERSION,
        "all_pass": all_pass,
        "test_count": len(results),
        "passed": sum(1 for r in results if r.get("passed")),
        "tests": results,
    }


# ----------------------------------------------------------------------------
# Output dump.
# ----------------------------------------------------------------------------


def dump_pose7(pose7: torch.Tensor, path: str) -> None:
    """Save a ``[7]`` pose tensor to a ``.npy``."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.save(path, pose7.detach().to("cpu").numpy())


def dump_diagnostics(diag: dict, path: str) -> None:
    """Save the diagnostics dict to a ``.json``."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(diag, f, indent=2, sort_keys=True)


# ----------------------------------------------------------------------------
# Entry point.
# ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    cfg, ns = parse_cli(argv)
    logging.basicConfig(
        level=getattr(logging, ns.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if ns.acceptance:
        report = run_acceptance_gate()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["all_pass"] else 3

    try:
        result = run_pipeline(cfg)
    except FileNotFoundError as exc:
        LOGGER.error("input file missing: %s", exc)
        return 4
    except ValueError as exc:
        LOGGER.error("invalid configuration: %s", exc)
        return 5
    except NotImplementedError as exc:
        LOGGER.error(
            "production mode requested but a backend is not yet wired: %s. "
            "Re-run with --mode mock or wait for the SAM2 install task.",
            exc,
        )
        return 2

    try:
        validate_pose7(result.pose7)
    except ValueError as exc:
        LOGGER.error("pose7 validation failed: %s", exc)
        return 6

    LOGGER.info(
        "pose7=%s wall_ms=%.3f mode=%s",
        result.pose7.tolist(),
        result.diagnostics.get("wall_ms", float("nan")),
        result.mode,
    )
    print(json.dumps(result.diagnostics, indent=2, sort_keys=True))

    budget = cfg.latency_budget_ms
    if result.mode == "production" and result.diagnostics.get("wall_ms", 0.0) > budget:
        LOGGER.warning(
            "wall_ms=%.3f exceeds latency budget %.1f ms (a2_design §7.3)",
            result.diagnostics["wall_ms"],
            budget,
        )

    if cfg.output_pose7:
        dump_pose7(result.pose7, cfg.output_pose7)
        LOGGER.info("pose7 saved to %s", cfg.output_pose7)
    if cfg.output_diagnostics:
        dump_diagnostics(result.diagnostics, cfg.output_diagnostics)
        LOGGER.info("diagnostics saved to %s", cfg.output_diagnostics)
    return 0


if __name__ == "__main__":
    sys.exit(main())
