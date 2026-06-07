#!/usr/bin/env python3
"""SOMA Phase A6b: Color-based Cable Segmentation + GT Accuracy Comparison.

Vision Pipeline Stage 1 (WHAT) first implementation: HSV color filter for
cable detection, compared against GT semantic segmentation mask (A6a).

Checks per camera:
  1. GT mask from semantic annotator ("cable" label)
  2. Color mask from HSV filter on RGB
  3. IoU, Precision, Recall between GT and color mask
  4. Overlay visualization (GT=green, color=red, overlap=yellow)
  5. Connected component stats for cable shape analysis

Usage:
    python thread_isaac_lab/scripts/test_a6b_color_seg.py \
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
parser = argparse.ArgumentParser(description="SOMA Phase A6b: Color Segmentation vs GT")
parser.add_argument("--output_dir", type=str, default="data/test_a6b")
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
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Cameras to test
CAMERAS = {
    "overhead": "overhead_camera",
    "front_left": "front_left_camera",
    "front_right": "front_right_camera",
}

# HSV parameters for cable detection (derived from A6a image sampling)
# Cable color: yellow, HSV ≈ H=29-31, S=31-140, V=172-238
HSV_PARAMS = {
    "h_min": 20,
    "h_max": 40,
    "s_min": 25,
    "v_min": 150,
}

# Morphology kernel size
MORPH_KERNEL = 3


# =========================================================================
# Helpers
# =========================================================================

def save_rgb(img: np.ndarray, path: str):
    """Save uint8 image as PNG."""
    try:
        from PIL import Image
        if img.ndim == 2:
            Image.fromarray(img, mode="L").save(path)
        else:
            Image.fromarray(img).save(path)
    except ImportError:
        np.save(path.replace(".png", ".npy"), img)


def parse_id_to_labels(info_dict: dict) -> dict[int, str]:
    """Parse idToLabels from camera info → {id: class_name}."""
    mapping = {}
    for id_str, label_info in info_dict.get("idToLabels", {}).items():
        try:
            sem_id = int(id_str)
        except (ValueError, TypeError):
            continue
        if isinstance(label_info, dict):
            mapping[sem_id] = label_info.get("class", "UNKNOWN")
        elif isinstance(label_info, str):
            mapping[sem_id] = label_info
    return mapping


def get_cable_gt_mask(sem: np.ndarray, id_to_label: dict[int, str]) -> np.ndarray:
    """Extract binary mask for 'cable' label from semantic segmentation."""
    cable_ids = [sid for sid, label in id_to_label.items() if label == "cable"]
    mask = np.zeros(sem.shape[:2], dtype=np.uint8)
    for cid in cable_ids:
        mask[sem == cid] = 255
    return mask


def detect_cable_color(rgb: np.ndarray, params: dict) -> np.ndarray:
    """Detect cable via HSV color filter + morphology.

    Uses closing only (no opening) to preserve thin cable features (~1px
    in overhead camera). Opening would destroy sub-kernel-width structures.
    """
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    lower = np.array([params["h_min"], params["s_min"], params["v_min"]])
    upper = np.array([params["h_max"], 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # Closing only: fill small gaps in cable detection.
    # No opening — cable is 1-2px wide in overhead and would be erased.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL, MORPH_KERNEL))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


def compute_iou_metrics(gt: np.ndarray, pred: np.ndarray) -> dict:
    """Compute IoU, Precision, Recall between binary masks (255=positive)."""
    gt_b = gt > 127
    pred_b = pred > 127

    intersection = np.sum(gt_b & pred_b)
    union = np.sum(gt_b | pred_b)
    gt_area = np.sum(gt_b)
    pred_area = np.sum(pred_b)

    iou = float(intersection / max(union, 1))
    precision = float(intersection / max(pred_area, 1))
    recall = float(intersection / max(gt_area, 1))

    return {
        "iou": round(iou, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "intersection": int(intersection),
        "gt_area": int(gt_area),
        "pred_area": int(pred_area),
    }


def create_comparison_overlay(rgb: np.ndarray, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """Create overlay: GT=green, pred=red, overlap=yellow on RGB."""
    overlay = rgb.copy().astype(np.float32)
    gt_b = gt > 127
    pred_b = pred > 127
    both = gt_b & pred_b
    gt_only = gt_b & ~pred_b
    pred_only = pred_b & ~gt_b

    alpha = 0.5
    # GT only → green
    overlay[gt_only, 1] = np.clip(overlay[gt_only, 1] * (1 - alpha) + 255 * alpha, 0, 255)
    # Pred only → red
    overlay[pred_only, 0] = np.clip(overlay[pred_only, 0] * (1 - alpha) + 255 * alpha, 0, 255)
    # Both → yellow
    overlay[both, 0] = np.clip(overlay[both, 0] * (1 - alpha) + 255 * alpha, 0, 255)
    overlay[both, 1] = np.clip(overlay[both, 1] * (1 - alpha) + 255 * alpha, 0, 255)

    return overlay.astype(np.uint8)


def analyze_components(mask: np.ndarray) -> dict:
    """Connected component analysis on binary mask."""
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    components = []
    for i in range(1, n_labels):  # skip background (0)
        area = int(stats[i, cv2.CC_STAT_AREA])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        cx, cy = float(centroids[i, 0]), float(centroids[i, 1])
        aspect = round(max(w, h) / max(min(w, h), 1), 2)
        components.append({
            "area": area, "width": w, "height": h,
            "aspect_ratio": aspect, "centroid": [round(cx, 1), round(cy, 1)],
        })
    components.sort(key=lambda c: -c["area"])
    return {
        "n_components": n_labels - 1,
        "total_area": sum(c["area"] for c in components),
        "largest": components[0] if components else None,
        "components": components[:5],  # top 5 by area
    }


# =========================================================================
# Main
# =========================================================================

def main():
    device_str = f"cuda:{app_launcher.device_id}"
    out_dir = os.path.join(str(_REPO_ROOT), args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    print(f"[A6b] SOMA Phase A6b: Color Segmentation vs GT ({device_str})", flush=True)
    print(f"[A6b] HSV params: {HSV_PARAMS}", flush=True)
    print(f"[A6b] Output: {out_dir}\n", flush=True)

    # ------------------------------------------------------------------
    # Scene — same as A6a
    # ------------------------------------------------------------------
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)

    for cam_key in CAMERAS.values():
        cam_cfg = getattr(scene_cfg, cam_key)
        cam_cfg.data_types = ["rgb", "distance_to_image_plane",
                              "semantic_segmentation"]
        cam_cfg.colorize_semantic_segmentation = False
        cam_cfg.colorize_instance_id_segmentation = False
        cam_cfg.colorize_instance_segmentation = False

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
    print(f"[A6b] Running {args.settle_steps} settle steps …", flush=True)
    for _ in range(args.settle_steps):
        sim.step()
        scene.update(sim.get_physics_dt())

    for cam_key in CAMERAS.values():
        scene[cam_key].update(sim.get_physics_dt())

    # ------------------------------------------------------------------
    # Per-camera analysis
    # ------------------------------------------------------------------
    results = {
        "phase": "A6b",
        "description": "Color-based cable segmentation vs GT semantic mask",
        "device": device_str,
        "hsv_params": HSV_PARAMS,
        "cameras": {},
        "iou": {},
        "precision": {},
        "recall": {},
        "cable_area_px": {},
        "gt_area_px": {},
    }
    all_pass = True
    iou_values = []

    for short, cam_key in CAMERAS.items():
        print(f"\n=== {short} ({cam_key}) ===", flush=True)
        cam = scene[cam_key]
        cam.update(sim.get_physics_dt())

        cr = {"name": cam_key}

        # ---------- RGB ----------
        rgb_t = cam.data.output.get("rgb")
        if rgb_t is None:
            cr["status"] = "FAIL"
            cr["error"] = "no RGB"
            results["cameras"][short] = cr
            all_pass = False
            continue

        rgb = rgb_t[0].cpu().numpy()
        if rgb.shape[-1] == 4:
            rgb = rgb[:, :, :3]
        rgb = rgb.astype(np.uint8)
        save_rgb(rgb, os.path.join(out_dir, f"rgb_{short}.png"))

        # ---------- Step 1: GT mask ----------
        sem_t = cam.data.output.get("semantic_segmentation")
        if sem_t is None:
            cr["status"] = "FAIL"
            cr["error"] = "no semantic data"
            results["cameras"][short] = cr
            all_pass = False
            continue

        sem = sem_t[0].cpu().numpy()
        if sem.ndim == 3 and sem.shape[-1] == 1:
            sem = sem[:, :, 0]

        info = cam.data.info
        id_to_label = {}
        if info and len(info) > 0:
            sem_info = info[0].get("semantic_segmentation", {})
            id_to_label = parse_id_to_labels(sem_info)

        gt_mask = get_cable_gt_mask(sem, id_to_label)
        gt_px = int(np.sum(gt_mask > 127))
        save_rgb(gt_mask, os.path.join(out_dir, f"gt_mask_{short}.png"))
        print(f"  GT cable mask: {gt_px} pixels", flush=True)

        # ---------- Step 2: Color mask ----------
        color_mask = detect_cable_color(rgb, HSV_PARAMS)
        color_px = int(np.sum(color_mask > 127))
        save_rgb(color_mask, os.path.join(out_dir, f"color_mask_{short}.png"))
        print(f"  Color mask:    {color_px} pixels", flush=True)

        # ---------- Step 3: IoU metrics ----------
        metrics = compute_iou_metrics(gt_mask, color_mask)
        print(f"  IoU={metrics['iou']:.4f}  Precision={metrics['precision']:.4f}  "
              f"Recall={metrics['recall']:.4f}", flush=True)

        results["iou"][short] = metrics["iou"]
        results["precision"][short] = metrics["precision"]
        results["recall"][short] = metrics["recall"]
        results["cable_area_px"][short] = color_px
        results["gt_area_px"][short] = gt_px
        iou_values.append(metrics["iou"])

        # ---------- Step 4: Overlay ----------
        overlay = create_comparison_overlay(rgb, gt_mask, color_mask)
        save_rgb(overlay, os.path.join(out_dir, f"overlay_{short}.png"))

        # ---------- Step 5: Component analysis ----------
        comp = analyze_components(color_mask)
        print(f"  Components: {comp['n_components']} total, "
              f"largest={comp['largest']['area'] if comp['largest'] else 0}px", flush=True)
        if comp["largest"]:
            print(f"    aspect_ratio={comp['largest']['aspect_ratio']}, "
                  f"size={comp['largest']['width']}x{comp['largest']['height']}", flush=True)

        cr.update({
            "status": "PASS" if metrics["iou"] >= 0.5 else "FAIL",
            "metrics": metrics,
            "components": comp,
        })
        results["cameras"][short] = cr

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    mean_iou = float(np.mean(iou_values)) if iou_values else 0.0
    results["iou"]["mean"] = round(mean_iou, 4)
    results["precision"]["mean"] = round(
        float(np.mean([results["precision"][s] for s in CAMERAS if s in results["precision"]])), 4
    ) if results["precision"] else 0.0
    results["recall"]["mean"] = round(
        float(np.mean([results["recall"][s] for s in CAMERAS if s in results["recall"]])), 4
    ) if results["recall"] else 0.0

    # Pass criterion: mean IoU >= 0.7
    overall_pass = mean_iou >= 0.7
    if not overall_pass:
        all_pass = False

    elapsed = time.time() - t0
    results["overall"] = "PASS" if overall_pass else "FAIL"
    results["elapsed_s"] = round(elapsed, 1)

    metrics_path = os.path.join(out_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}", flush=True)
    print(f"SOMA Phase A6b Color Segmentation: {results['overall']}", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  Mean IoU:       {mean_iou:.4f} (threshold: 0.70)", flush=True)
    print(f"  Mean Precision: {results['precision']['mean']:.4f}", flush=True)
    print(f"  Mean Recall:    {results['recall']['mean']:.4f}", flush=True)
    for short in CAMERAS:
        iou = results["iou"].get(short, 0)
        prec = results["precision"].get(short, 0)
        rec = results["recall"].get(short, 0)
        gt = results["gt_area_px"].get(short, 0)
        pred = results["cable_area_px"].get(short, 0)
        print(f"  {short:<12s}  IoU={iou:.4f}  P={prec:.4f}  R={rec:.4f}  "
              f"GT={gt}px  Color={pred}px", flush=True)
    print(f"  Results → {metrics_path}", flush=True)
    print(f"  Elapsed: {elapsed:.0f}s", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
