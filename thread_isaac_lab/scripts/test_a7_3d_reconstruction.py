#!/usr/bin/env python3
"""SOMA Phase A7: Vision Pipeline Stage 2-3 — 3D Reconstruction + cable_midpoint.

Stage 2 (WHERE): Back-project cable mask pixels to 3D via depth.
Stage 3 (HOW):   Estimate cable_midpoint from 3D point cloud.

Compares 3 estimation methods (mean, median, PCA-center) against API GT.

Usage:
    python thread_isaac_lab/scripts/test_a7_3d_reconstruction.py \
        --device cuda:0 --enable_cameras
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

import numpy as np

_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="SOMA Phase A7: 3D Reconstruction")
parser.add_argument("--output_dir", type=str, default="data/test_a7")
parser.add_argument("--settle_steps", type=int, default=200)

from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Post-AppLauncher imports
# ---------------------------------------------------------------------------
import cv2
import torch

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.scripts.camera_utils import pixel_to_world, _quat_to_rotation_matrix
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Cameras
CAMERAS = {
    "overhead": "overhead_camera",
    "front_left": "front_left_camera",
    "front_right": "front_right_camera",
}

# HSV parameters (from A6b: cable is yellow)
HSV_PARAMS = {"h_min": 20, "h_max": 40, "s_min": 25, "v_min": 150}

PASS_THRESHOLD_MM = 5.0


# =========================================================================
# Helpers
# =========================================================================

def save_rgb(img: np.ndarray, path: str):
    try:
        from PIL import Image
        if img.ndim == 2:
            Image.fromarray(img, mode="L").save(path)
        else:
            Image.fromarray(img).save(path)
    except ImportError:
        np.save(path.replace(".png", ".npy"), img)


def detect_cable_mask(rgb: np.ndarray) -> np.ndarray:
    """HSV color filter for cable (A6b params, closing only)."""
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([HSV_PARAMS["h_min"], HSV_PARAMS["s_min"], HSV_PARAMS["v_min"]])
    upper = np.array([HSV_PARAMS["h_max"], 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def backproject_mask(mask: np.ndarray, depth: np.ndarray,
                     K: np.ndarray, cam_pos: np.ndarray,
                     cam_quat_ros: np.ndarray) -> np.ndarray:
    """Back-project all masked pixels to 3D world coordinates.

    Returns (N, 3) array of world-frame points.
    """
    ys, xs = np.nonzero(mask > 127)
    if len(ys) == 0:
        return np.empty((0, 3), dtype=np.float32)

    # Get depth at each pixel
    depths = depth[ys, xs]
    valid = np.isfinite(depths) & (depths > 0) & (depths < 100)
    ys, xs, depths = ys[valid], xs[valid], depths[valid]

    if len(ys) == 0:
        return np.empty((0, 3), dtype=np.float32)

    # Vectorized back-projection
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]

    x_cam = (xs.astype(np.float64) - cx) * depths / fx
    y_cam = (ys.astype(np.float64) - cy) * depths / fy
    z_cam = depths.astype(np.float64)

    p_cam = np.stack([x_cam, y_cam, z_cam], axis=-1)  # (N, 3)
    R = _quat_to_rotation_matrix(cam_quat_ros)
    p_world = (R @ p_cam.T).T + cam_pos.astype(np.float64)

    return p_world.astype(np.float32)


def estimate_midpoint_mean(points: np.ndarray) -> np.ndarray:
    return points.mean(axis=0)


def estimate_midpoint_median(points: np.ndarray) -> np.ndarray:
    return np.median(points, axis=0)


def estimate_midpoint_pca_center(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """PCA: project onto 1st component, find midpoint of extremes.

    Returns (midpoint, direction_vector).
    """
    centroid = points.mean(axis=0)
    centered = points - centroid
    # SVD for PCA
    _, s, Vt = np.linalg.svd(centered, full_matrices=False)
    direction = Vt[0]  # first principal component
    projections = centered @ direction
    t_min, t_max = projections.min(), projections.max()
    t_mid = (t_min + t_max) / 2.0
    midpoint = centroid + t_mid * direction
    return midpoint.astype(np.float32), direction.astype(np.float32)


def world_to_pixel(point_3d, K, cam_pos, cam_quat_ros):
    """Project 3D world point to 2D pixel."""
    R = _quat_to_rotation_matrix(cam_quat_ros)
    p_cam = R.T @ (point_3d.astype(np.float64) - cam_pos.astype(np.float64))
    if p_cam[2] <= 0:
        return None
    u = float(K[0, 0] * p_cam[0] / p_cam[2] + K[0, 2])
    v = float(K[1, 1] * p_cam[1] / p_cam[2] + K[1, 2])
    return u, v


def draw_cross(img, u, v, color, size=7, thickness=2):
    """Draw a cross marker on image."""
    u, v = int(round(u)), int(round(v))
    h, w = img.shape[:2]
    for d in range(-size, size + 1):
        if 0 <= v < h and 0 <= u + d < w:
            img[v, u + d] = color
        if 0 <= v + d < h and 0 <= u < w:
            img[v + d, u] = color


# =========================================================================
# Main
# =========================================================================

def main():
    device_str = f"cuda:{app_launcher.device_id}"
    out_dir = os.path.join(str(_REPO_ROOT), args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    print(f"[A7] SOMA Phase A7: 3D Reconstruction ({device_str})", flush=True)
    print(f"[A7] Output: {out_dir}\n", flush=True)

    # ------------------------------------------------------------------
    # Scene
    # ------------------------------------------------------------------
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)
    for cam_key in CAMERAS.values():
        cam_cfg = getattr(scene_cfg, cam_key)
        cam_cfg.data_types = ["rgb", "distance_to_image_plane"]

    physx_cfg = sim_utils.PhysxCfg(
        gpu_found_lost_pairs_capacity=2**23,
        gpu_total_aggregate_pairs_capacity=2**23,
    )
    sim_cfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT, render_interval=2, device=device_str,
        physx=physx_cfg,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()
    scene.reset()

    # ------------------------------------------------------------------
    # Settle
    # ------------------------------------------------------------------
    print(f"[A7] Running {args.settle_steps} settle steps …", flush=True)
    for _ in range(args.settle_steps):
        sim.step()
        scene.update(sim.get_physics_dt())

    for cam_key in CAMERAS.values():
        scene[cam_key].update(sim.get_physics_dt())

    # ------------------------------------------------------------------
    # Ground truth cable midpoint
    # ------------------------------------------------------------------
    cable = scene["cable"]
    cable_pos = cable.data.body_pos_w[0].cpu().numpy()  # (n_bodies, 3)
    gt_mid = cable_pos.mean(axis=0).astype(np.float32)
    print(f"[A7] GT cable midpoint: ({gt_mid[0]:.4f}, {gt_mid[1]:.4f}, {gt_mid[2]:.4f})", flush=True)
    print(f"[A7] Cable bodies: {cable_pos.shape[0]}, "
          f"span Y=[{cable_pos[:,1].min():.4f}, {cable_pos[:,1].max():.4f}]\n", flush=True)

    # ------------------------------------------------------------------
    # Per-camera: mask → depth → 3D points
    # ------------------------------------------------------------------
    all_points = {}
    per_cam_estimates = {}
    results = {
        "phase": "A7",
        "description": "3D reconstruction + cable_midpoint estimation",
        "device": device_str,
        "gt_midpoint": gt_mid.tolist(),
        "cable_bodies": int(cable_pos.shape[0]),
        "point_count": {},
        "per_camera_error_mm": {},
        "cameras": {},
    }

    for short, cam_key in CAMERAS.items():
        print(f"=== {short} ({cam_key}) ===", flush=True)
        cam = scene[cam_key]
        cam.update(sim.get_physics_dt())

        # RGB
        rgb_t = cam.data.output.get("rgb")
        if rgb_t is None:
            print(f"  No RGB data", flush=True)
            continue
        rgb = rgb_t[0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        rgb = rgb.astype(np.uint8)

        # Depth
        dep_t = cam.data.output.get("distance_to_image_plane")
        if dep_t is None:
            print(f"  No depth data", flush=True)
            continue
        dep = dep_t[0].cpu().numpy()
        if dep.ndim == 3:
            dep = dep[:, :, 0]

        # Cable mask
        mask = detect_cable_mask(rgb)
        n_mask = int(np.sum(mask > 127))
        save_rgb(mask, os.path.join(out_dir, f"mask_{short}.png"))

        # Extrinsics
        cam_pos = cam.data.pos_w[0].cpu().numpy()
        cam_quat = cam.data.quat_w_ros[0].cpu().numpy()
        K = cam.data.intrinsic_matrices[0].cpu().numpy()

        # Back-project
        points = backproject_mask(mask, dep, K, cam_pos, cam_quat)
        n_pts = points.shape[0]
        all_points[short] = points
        results["point_count"][short] = n_pts

        if n_pts < 10:
            print(f"  mask={n_mask}px → {n_pts} 3D points (WARNING: too few)", flush=True)
            continue

        # Per-camera estimate (mean)
        est = points.mean(axis=0)
        err = float(np.linalg.norm(est - gt_mid)) * 1000
        per_cam_estimates[short] = est
        results["per_camera_error_mm"][f"{short}_mean"] = round(err, 2)
        results["cameras"][short] = {
            "mask_pixels": n_mask,
            "points_3d": n_pts,
            "estimate": est.tolist(),
            "error_mm": round(err, 2),
            "point_cloud_range": {
                "x": [round(float(points[:, 0].min()), 4), round(float(points[:, 0].max()), 4)],
                "y": [round(float(points[:, 1].min()), 4), round(float(points[:, 1].max()), 4)],
                "z": [round(float(points[:, 2].min()), 4), round(float(points[:, 2].max()), 4)],
            },
        }

        np.save(os.path.join(out_dir, f"point_cloud_{short}.npy"), points)
        print(f"  mask={n_mask}px → {n_pts} 3D points", flush=True)
        print(f"  range X=[{points[:,0].min():.4f},{points[:,0].max():.4f}] "
              f"Y=[{points[:,1].min():.4f},{points[:,1].max():.4f}] "
              f"Z=[{points[:,2].min():.4f},{points[:,2].max():.4f}]", flush=True)
        print(f"  estimate=({est[0]:.4f},{est[1]:.4f},{est[2]:.4f})  "
              f"error={err:.1f}mm", flush=True)

    # ------------------------------------------------------------------
    # Merge point clouds
    # ------------------------------------------------------------------
    merged_list = [pts for pts in all_points.values() if pts.shape[0] > 0]
    if not merged_list:
        print("\n[A7] FAIL: no 3D points from any camera", flush=True)
        results["overall"] = "FAIL"
        results["error"] = "no points"
        with open(os.path.join(out_dir, "RUN_METRICS.json"), "w") as f:
            json.dump(results, f, indent=2)
        return

    merged = np.concatenate(merged_list, axis=0)
    results["point_count"]["merged"] = merged.shape[0]
    np.save(os.path.join(out_dir, "point_cloud_merged.npy"), merged)
    print(f"\n[A7] Merged: {merged.shape[0]} points from {len(merged_list)} cameras", flush=True)

    # ------------------------------------------------------------------
    # Estimation methods
    # ------------------------------------------------------------------
    est_mean = estimate_midpoint_mean(merged)
    est_median = estimate_midpoint_median(merged)
    est_pca, pca_dir = estimate_midpoint_pca_center(merged)

    err_mean = float(np.linalg.norm(est_mean - gt_mid)) * 1000
    err_median = float(np.linalg.norm(est_median - gt_mid)) * 1000
    err_pca = float(np.linalg.norm(est_pca - gt_mid)) * 1000

    results["estimated_midpoint"] = {
        "mean": {"pos": est_mean.tolist(), "error_mm": round(err_mean, 2)},
        "median": {"pos": est_median.tolist(), "error_mm": round(err_median, 2)},
        "pca_center": {"pos": est_pca.tolist(), "error_mm": round(err_pca, 2)},
    }
    results["pca_direction"] = pca_dir.tolist()

    best_method = min(["mean", "median", "pca_center"],
                      key=lambda m: results["estimated_midpoint"][m]["error_mm"])
    best_err = results["estimated_midpoint"][best_method]["error_mm"]
    results["best_method"] = best_method
    results["best_error_mm"] = best_err
    results["pass_threshold_mm"] = PASS_THRESHOLD_MM

    print(f"\n--- Estimation Results ---", flush=True)
    for name, est, err in [("mean", est_mean, err_mean),
                            ("median", est_median, err_median),
                            ("pca_center", est_pca, err_pca)]:
        tag = " ← BEST" if name == best_method else ""
        print(f"  {name:12s}: ({est[0]:.4f},{est[1]:.4f},{est[2]:.4f})  "
              f"err={err:.2f}mm{tag}", flush=True)
    print(f"  GT:           ({gt_mid[0]:.4f},{gt_mid[1]:.4f},{gt_mid[2]:.4f})", flush=True)
    print(f"  PCA direction: ({pca_dir[0]:.4f},{pca_dir[1]:.4f},{pca_dir[2]:.4f})", flush=True)

    # ------------------------------------------------------------------
    # Overlay on overhead RGB
    # ------------------------------------------------------------------
    try:
        cam_oh = scene["overhead_camera"]
        cam_oh.update(sim.get_physics_dt())
        rgb_oh = cam_oh.data.output["rgb"][0].cpu().numpy()
        if rgb_oh.shape[-1] == 4:
            rgb_oh = rgb_oh[:, :, :3]
        rgb_oh = rgb_oh.astype(np.uint8)
        cam_pos_oh = cam_oh.data.pos_w[0].cpu().numpy()
        cam_quat_oh = cam_oh.data.quat_w_ros[0].cpu().numpy()
        K_oh = cam_oh.data.intrinsic_matrices[0].cpu().numpy()

        overlay = rgb_oh.copy()

        # GT → green cross
        proj_gt = world_to_pixel(gt_mid, K_oh, cam_pos_oh, cam_quat_oh)
        if proj_gt:
            draw_cross(overlay, proj_gt[0], proj_gt[1], (0, 255, 0), size=9)

        # Best estimate → red cross
        best_est = results["estimated_midpoint"][best_method]["pos"]
        proj_est = world_to_pixel(np.array(best_est, dtype=np.float32),
                                  K_oh, cam_pos_oh, cam_quat_oh)
        if proj_est:
            draw_cross(overlay, proj_est[0], proj_est[1], (255, 0, 0), size=9)

        # All 3 estimates as small markers
        colors = {"mean": (255, 100, 100), "median": (100, 100, 255), "pca_center": (255, 255, 0)}
        for name in ["mean", "median", "pca_center"]:
            est_pos = results["estimated_midpoint"][name]["pos"]
            proj = world_to_pixel(np.array(est_pos, dtype=np.float32),
                                  K_oh, cam_pos_oh, cam_quat_oh)
            if proj:
                draw_cross(overlay, proj[0], proj[1], colors[name], size=4)

        save_rgb(overlay, os.path.join(out_dir, "midpoint_overlay_overhead.png"))
    except Exception as e:
        print(f"  Overlay error: {e}", flush=True)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    overall_pass = best_err < PASS_THRESHOLD_MM
    elapsed = time.time() - t0
    results["overall"] = "PASS" if overall_pass else "FAIL"
    results["elapsed_s"] = round(elapsed, 1)

    metrics_path = os.path.join(out_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}", flush=True)
    print(f"SOMA Phase A7 3D Reconstruction: {results['overall']}", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  Best method:  {best_method}  error={best_err:.2f}mm  "
          f"(threshold: {PASS_THRESHOLD_MM}mm)", flush=True)
    print(f"  Points: {results['point_count']}", flush=True)
    for short in CAMERAS:
        err = results["per_camera_error_mm"].get(f"{short}_mean", "N/A")
        pts = results["point_count"].get(short, 0)
        print(f"    {short:<12s}  {pts} pts  err={err}mm", flush=True)
    print(f"  Results → {metrics_path}", flush=True)
    print(f"  Elapsed: {elapsed:.0f}s", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
