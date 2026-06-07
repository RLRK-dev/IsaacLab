# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stage 3 PnP+RANSAC 6DOF clip-pose recovery (alt path skeleton).

Implements the pose-recovery stage of the alternative pipeline defined in
``thread-vault/06-Knowledge/LL-Vision-Pose-Design.md`` §4. Consumes a 2D
keypoint set produced by Stage 2 plus a 3D model-vertex set parsed from the
clip CAD (``data/clip/routing_clip_v1.usd``), and emits a per-clip 7D pose
``(t_x, t_y, t_z, q_x, q_y, q_z, q_w)`` in the camera frame.

This module is a **skeleton**: ``cv2.solvePnPRansac`` and the keypoint
extraction primitives are functional, but the higher-level
:class:`PnpClipPoseSolver` orchestration is stubbed so it can be filled in by
the impl task once the SAM2 install path is authorized and Stage 2 keypoint
generation is wired up.

R6 module boundary: imports are restricted to numpy / opencv / torch and the
local ``estimators`` package. No ``newton`` / no env / no
``WristCameraManager`` imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import cv2
import numpy as np
import torch

# Design memo §4.5 default RANSAC hyper-parameters.
_DEFAULT_RANSAC_ITERATIONS = 200
_DEFAULT_REPROJECTION_ERROR_PX = 2.0
_DEFAULT_RANSAC_CONFIDENCE = 0.99
# Design memo §4.4 cardinality breakpoints for PnP variant selection.
_AP3P_MIN_N = 4  # exact at N == 4
_EPNP_MAX_N = 6
# Design memo §4.7 symmetric clip yaw convention.
_YAW_SYMMETRY_MOD = np.pi


class PnpVariant(Enum):
    """PnP solver variant selected by correspondence cardinality (§4.4).

    AP3P is exact for N == 4. EPnP is fast for small N. Iterative is the
    Levenberg-Marquardt non-linear refiner used for larger N. IPPE is the
    planar-degeneracy escape route for coplanar correspondences.
    """

    AP3P = "ap3p"
    EPNP = "epnp"
    ITERATIVE = "iterative"
    IPPE = "ippe"


@dataclass
class CameraCalibration:
    """Camera intrinsics + distortion bundle (§2.3 schema).

    Attributes:
        K: ``[3, 3]`` float intrinsic matrix [px units in fx, fy, cx, cy].
        dist_coeffs: ``[5]`` OpenCV-format distortion ``[k1, k2, p1, p2, k3]``.
            Sim default uses zeros (analytical pinhole, no lens distortion).
        resolution: ``(width, height)`` in pixels.
        source: free-form provenance tag, e.g. ``"analytical"``,
            ``"charuco_calibrated"``, etc.
    """

    K: np.ndarray
    dist_coeffs: np.ndarray
    resolution: tuple[int, int]
    source: str = "unspecified"


@dataclass
class ClipCadModel:
    """3D model-vertex set for one clip body (§4.1).

    Attributes:
        vertices: ``[V, 3]`` float vertices in the clip body frame [m].
        principal_axis: ``[3]`` unit vector along the longest geometric axis,
            cached from PCA over :attr:`vertices` for §4.7 yaw convention.
        source_path: filesystem path to the original USD file the cache was
            derived from. Used as a provenance check on load.
    """

    vertices: np.ndarray
    principal_axis: np.ndarray
    source_path: str


@dataclass
class Keypoints2D:
    """2D image-space keypoints for a single clip in a single frame.

    Attributes:
        points: ``[K, 2]`` float keypoints in pixels (subpixel-refined).
        method: which Stage 2 extractor produced these keypoints.
        confidence: per-keypoint scalar in [0, 1] for downstream weighting.
    """

    points: np.ndarray
    method: str  # "contour_polygon" | "good_features" | "min_area_rect"
    confidence: np.ndarray


class PoseRegime(Enum):
    """Per-clip pose-output regime, mirroring §3.4 segmentation regime.

    ``ACCEPT`` is the nominal RANSAC-converged path. ``FALLBACK`` is taken
    when keypoint cardinality drops below 4 and Stage 2 emitted a
    centroid-only proxy. ``FAIL_CLOSED`` propagates upstream regime failure.
    """

    ACCEPT = "accept"
    FALLBACK = "fallback"
    FAIL_CLOSED = "fail_closed"


@dataclass
class ClipPoseEstimate:
    """Per-clip pose recovery output.

    Attributes:
        translation: ``[3]`` float clip body origin in the camera frame [m].
        quat_xyzw: ``[4]`` quaternion ``(qx, qy, qz, qw)``; matches the rest
            of the codebase including Newton ``body_q`` packing order.
        inlier_count: number of RANSAC inliers retained after refinement.
        regime: see :class:`PoseRegime`.
        reproj_error_px: mean reprojection error of inliers in pixels;
            useful for §6 R-9 fallback decision logging.
    """

    translation: np.ndarray
    quat_xyzw: np.ndarray
    inlier_count: int
    regime: PoseRegime
    reproj_error_px: float = float("nan")


def select_pnp_variant(num_correspondences: int, coplanar: bool = False) -> PnpVariant:
    """Select PnP variant by correspondence cardinality (design memo §4.4).

    Args:
        num_correspondences: number of validated 2D-3D point pairs.
        coplanar: ``True`` if the 3D points are detected to be coplanar
            (PCA on vertex set with smallest eigenvalue ≈ 0). Forces IPPE.

    Returns:
        the chosen :class:`PnpVariant`.

    Raises:
        ValueError: if ``num_correspondences < 4`` (PnP is undetermined).
    """
    if num_correspondences < _AP3P_MIN_N:
        raise ValueError(f"PnP requires >= 4 correspondences, got {num_correspondences}")
    if coplanar:
        return PnpVariant.IPPE
    if num_correspondences == _AP3P_MIN_N:
        return PnpVariant.AP3P
    if num_correspondences <= _EPNP_MAX_N:
        return PnpVariant.EPNP
    return PnpVariant.ITERATIVE


def _variant_to_cv2_flag(variant: PnpVariant) -> int:
    return {
        PnpVariant.AP3P: cv2.SOLVEPNP_AP3P,
        PnpVariant.EPNP: cv2.SOLVEPNP_EPNP,
        PnpVariant.ITERATIVE: cv2.SOLVEPNP_ITERATIVE,
        PnpVariant.IPPE: cv2.SOLVEPNP_IPPE,
    }[variant]


def rodrigues_to_quat_xyzw(rvec: np.ndarray) -> np.ndarray:
    """Convert a Rodrigues rotation vector to ``(qx, qy, qz, qw)``.

    Args:
        rvec: ``[3]`` or ``[3, 1]`` axis-angle vector.

    Returns:
        ``[4]`` quaternion in xyzw order, matching the codebase convention.
    """
    R, _ = cv2.Rodrigues(rvec)
    return rotation_matrix_to_quat_xyzw(R)


def rotation_matrix_to_quat_xyzw(R: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to ``(qx, qy, qz, qw)``.

    Numerically stable trace-based formulation; see Shoemake (1985). Output
    quaternion has positive ``qw`` to canonicalise the double-cover.
    """
    trace = float(R[0, 0] + R[1, 1] + R[2, 2])
    if trace > 0.0:
        s = 0.5 / np.sqrt(trace + 1.0)
        qw = 0.25 / s
        qx = (R[2, 1] - R[1, 2]) * s
        qy = (R[0, 2] - R[2, 0]) * s
        qz = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    quat = np.array([qx, qy, qz, qw], dtype=np.float64)
    if quat[3] < 0:
        quat = -quat
    return quat / np.linalg.norm(quat)


def yaw_error_mod_symmetry(yaw_pred: float, yaw_gt: float) -> float:
    """Symmetric yaw error, wrapped into ``[0, π / 2]`` for π-symmetric clips.

    Per design memo §4.7, ``routing_clip_v1.usd`` exhibits 180° yaw
    invariance, so we wrap the absolute error into a half period before
    comparing against thresholds.

    Args:
        yaw_pred: predicted yaw [rad].
        yaw_gt: ground-truth yaw [rad].

    Returns:
        yaw error in [0, π / 2] [rad].
    """
    raw = abs(yaw_pred - yaw_gt) % _YAW_SYMMETRY_MOD
    return min(raw, _YAW_SYMMETRY_MOD - raw)


def load_clip_cad(npz_path: str | Path, usd_source: str | None = None) -> ClipCadModel:
    """Load a cached clip CAD vertex set from ``.npz``.

    The cache is produced offline from the source USD via ``pxr.UsdGeom`` so
    that runtime never imports ``pxr``. Cache schema:

    - ``vertices``: ``[V, 3]`` float32 metric m, in clip body frame.
    - ``principal_axis``: ``[3]`` float32 unit vector from PCA over vertices.
    - ``source_path``: optional 0-d string array with the originating USD path.

    Args:
        npz_path: path to the cached ``.npz`` file.
        usd_source: optional override for the provenance tag stored on the
            returned :class:`ClipCadModel`.

    Returns:
        the :class:`ClipCadModel` reconstructed from the cache.

    Raises:
        FileNotFoundError: if ``npz_path`` does not exist.
        ValueError: if the cache is missing required keys.
    """
    path = Path(npz_path)
    if not path.exists():
        raise FileNotFoundError(f"Clip CAD cache not found: {path}")
    data = np.load(path, allow_pickle=False)
    if "vertices" not in data or "principal_axis" not in data:
        raise ValueError(f"Cache {path} missing keys (need 'vertices' and 'principal_axis')")
    source = usd_source if usd_source is not None else str(data.get("source_path", "unknown"))
    return ClipCadModel(
        vertices=data["vertices"].astype(np.float32),
        principal_axis=data["principal_axis"].astype(np.float32),
        source_path=source,
    )


def extract_keypoints_from_mask(
    mask: np.ndarray,
    *,
    method: str = "contour_polygon",
    epsilon_ratio: float = 0.01,
    max_corners: int = 12,
) -> Keypoints2D:
    """Stage 2 → Stage 3 bridge: 2D keypoint extraction from a binary mask.

    Implements the three §4.2 candidate methods. ``contour_polygon`` is the
    MVP-3 default since it directly captures clip geometric corners.

    Args:
        mask: ``[H, W]`` binary mask (uint8 or bool). Non-zero == clip pixel.
        method: ``"contour_polygon"`` | ``"good_features"`` | ``"min_area_rect"``.
        epsilon_ratio: contour-approx tolerance as a fraction of perimeter,
            forwarded to ``cv2.approxPolyDP`` when ``method`` is the polygon
            extractor. Smaller values keep more vertices.
        max_corners: cap for ``good_features`` keypoint count.

    Returns:
        :class:`Keypoints2D` with subpixel-refined coordinates and per-point
        confidence (constant 1.0 for the polygon path; from ``cornerSubPix``
        residual otherwise).

    Raises:
        ValueError: if ``method`` is not one of the documented options.
    """
    mask_u8 = (mask > 0).astype(np.uint8) * 255

    if method == "contour_polygon":
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return Keypoints2D(points=np.empty((0, 2), dtype=np.float32), method=method, confidence=np.empty(0))
        contour = max(contours, key=cv2.contourArea)
        epsilon = epsilon_ratio * cv2.arcLength(contour, closed=True)
        approx = cv2.approxPolyDP(contour, epsilon, closed=True).reshape(-1, 2).astype(np.float32)
        # Subpixel refine on grayscale mask (any image with edges would also work).
        if approx.shape[0] > 0:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            cv2.cornerSubPix(mask_u8, approx, (5, 5), (-1, -1), criteria)
        return Keypoints2D(
            points=approx,
            method=method,
            confidence=np.ones(approx.shape[0], dtype=np.float32),
        )

    if method == "good_features":
        gray = mask_u8
        corners = cv2.goodFeaturesToTrack(gray, maxCorners=max_corners, qualityLevel=0.01, minDistance=3, mask=mask_u8)
        if corners is None:
            return Keypoints2D(points=np.empty((0, 2), dtype=np.float32), method=method, confidence=np.empty(0))
        pts = corners.reshape(-1, 2).astype(np.float32)
        return Keypoints2D(points=pts, method=method, confidence=np.ones(pts.shape[0], dtype=np.float32))

    if method == "min_area_rect":
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return Keypoints2D(points=np.empty((0, 2), dtype=np.float32), method=method, confidence=np.empty(0))
        contour = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect).astype(np.float32)
        return Keypoints2D(points=box, method=method, confidence=np.ones(box.shape[0], dtype=np.float32))

    raise ValueError(
        f"Unknown extraction method: {method}. Valid: 'contour_polygon', 'good_features', 'min_area_rect'."
    )


class PnpClipPoseSolver:
    """Stage 3 PnP+RANSAC 6DOF clip-pose recovery wrapper.

    Skeleton scope: low-level OpenCV calls (:func:`cv2.solvePnPRansac`,
    :func:`cv2.solvePnPRefineLM`) are functional, but the
    correspondence-establishment loop (§4.3 nominal-pose projection +
    nearest-neighbour pairing) is stubbed for the impl task.

    Args:
        camera: :class:`CameraCalibration` describing the camera that
            captured the input frames. Sim default uses zero distortion.
        cad: :class:`ClipCadModel` for the clip whose pose is being recovered.
        ransac_iterations: max RANSAC iterations.
        reprojection_error_px: RANSAC inlier threshold in pixels.
        confidence: target RANSAC confidence in (0, 1).
    """

    def __init__(
        self,
        camera: CameraCalibration,
        cad: ClipCadModel,
        *,
        ransac_iterations: int = _DEFAULT_RANSAC_ITERATIONS,
        reprojection_error_px: float = _DEFAULT_REPROJECTION_ERROR_PX,
        confidence: float = _DEFAULT_RANSAC_CONFIDENCE,
    ) -> None:
        self.camera = camera
        self.cad = cad
        self.ransac_iterations = ransac_iterations
        self.reprojection_error_px = reprojection_error_px
        self.confidence = confidence

    def establish_correspondence(
        self,
        keypoints: Keypoints2D,
        kinematic_prior_pose7: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Pair Stage 2 2D keypoints with Stage 1 3D CAD vertices (§4.3).

        Projects the CAD vertex set into the camera frame using the
        kinematic prior pose, then runs nearest-neighbour matching against
        the 2D keypoints. False correspondences are accepted at this stage —
        RANSAC removes them downstream.

        Args:
            keypoints: Stage 2 :class:`Keypoints2D`.
            kinematic_prior_pose7: ``[7]`` ``(t_xyz, q_xyzw)`` clip pose
                prior in the camera frame, from env-side kinematics.

        Returns:
            tuple of ``(object_points_3d, image_points_2d)`` aligned by row
            for direct passing to :func:`cv2.solvePnPRansac`.

        Raises:
            NotImplementedError: skeleton phase. The full implementation is
                gated on the impl task being dispatched after Rs ★.
        """
        raise NotImplementedError(
            "PnpClipPoseSolver.establish_correspondence: implementation pending."
            " See LL-Vision-Pose-Design.md §4.3 — projection + nearest-neighbour."
        )

    def solve(
        self,
        object_points_3d: np.ndarray,
        image_points_2d: np.ndarray,
        *,
        coplanar: bool = False,
    ) -> ClipPoseEstimate:
        """Run RANSAC PnP + LM refinement on prepared correspondences.

        Args:
            object_points_3d: ``[N, 3]`` float32 vertices in the clip body
                frame [m].
            image_points_2d: ``[N, 2]`` float32 image-space keypoints [px].
            coplanar: forwarded to :func:`select_pnp_variant`; pass ``True``
                for clip features that lie in a single plane.

        Returns:
            :class:`ClipPoseEstimate`. ``regime`` is ``ACCEPT`` if RANSAC
            converged with ≥ 4 inliers; ``FALLBACK`` if the convergence
            condition fails (caller may then fall back to centroid + axis).
        """
        n = int(object_points_3d.shape[0])
        if n < 4 or image_points_2d.shape[0] != n:
            return ClipPoseEstimate(
                translation=np.zeros(3, dtype=np.float64),
                quat_xyzw=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64),
                inlier_count=0,
                regime=PoseRegime.FALLBACK,
            )

        variant = select_pnp_variant(n, coplanar=coplanar)
        flag = _variant_to_cv2_flag(variant)

        success, rvec, tvec, inliers = cv2.solvePnPRansac(
            objectPoints=object_points_3d.astype(np.float32),
            imagePoints=image_points_2d.astype(np.float32),
            cameraMatrix=self.camera.K.astype(np.float32),
            distCoeffs=self.camera.dist_coeffs.astype(np.float32),
            iterationsCount=self.ransac_iterations,
            reprojectionError=self.reprojection_error_px,
            confidence=self.confidence,
            flags=flag,
        )

        if not success or inliers is None or len(inliers) < 4:
            return ClipPoseEstimate(
                translation=np.zeros(3, dtype=np.float64),
                quat_xyzw=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64),
                inlier_count=0 if inliers is None else int(len(inliers)),
                regime=PoseRegime.FALLBACK,
            )

        inlier_idx = inliers.flatten()
        rvec, tvec = cv2.solvePnPRefineLM(
            object_points_3d[inlier_idx].astype(np.float32),
            image_points_2d[inlier_idx].astype(np.float32),
            self.camera.K.astype(np.float32),
            self.camera.dist_coeffs.astype(np.float32),
            rvec,
            tvec,
        )

        # Mean reprojection error on inliers for diagnostics.
        proj, _ = cv2.projectPoints(
            object_points_3d[inlier_idx].astype(np.float32),
            rvec,
            tvec,
            self.camera.K.astype(np.float32),
            self.camera.dist_coeffs.astype(np.float32),
        )
        residuals = np.linalg.norm(proj.reshape(-1, 2) - image_points_2d[inlier_idx], axis=1)
        reproj_err = float(residuals.mean()) if residuals.size > 0 else float("nan")

        return ClipPoseEstimate(
            translation=tvec.flatten().astype(np.float64),
            quat_xyzw=rodrigues_to_quat_xyzw(rvec),
            inlier_count=int(len(inliers)),
            regime=PoseRegime.ACCEPT,
            reproj_error_px=reproj_err,
        )

    def to_pose7_torch(self, estimate: ClipPoseEstimate, device: str | torch.device) -> torch.Tensor:
        """Pack a :class:`ClipPoseEstimate` into a ``[7]`` torch tensor.

        Convention: ``(t_x, t_y, t_z, q_x, q_y, q_z, q_w)``, matching
        Newton ``body_q`` packing and the rest of the codebase.

        Args:
            estimate: a :class:`ClipPoseEstimate` from :meth:`solve`.
            device: target torch device.

        Returns:
            ``[7]`` float32 tensor on ``device``.
        """
        pose7 = np.concatenate([estimate.translation, estimate.quat_xyzw], axis=0).astype(np.float32)
        return torch.from_numpy(pose7).to(device)
