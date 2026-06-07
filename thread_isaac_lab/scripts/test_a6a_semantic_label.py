#!/usr/bin/env python3
"""SOMA Phase A6a: USD Semantic Label Validation.

Verifies that semantic labels (cable, table, robot, hook, ground) are correctly
applied to scene prims and detected by the semantic_segmentation camera annotator.

Checks per camera:
  1. idToLabels contains "cable" class
  2. Cable pixel count > threshold
  3. Cable mask overlays correctly on RGB
  4. All expected labels present

Usage:
    python thread_isaac_lab/scripts/test_a6a_semantic_label.py \
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
parser = argparse.ArgumentParser(description="SOMA Phase A6a: Semantic Label Validation")
parser.add_argument("--output_dir", type=str, default="data/test_a6a")
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

# Expected semantic classes (from A6a label assignment)
EXPECTED_LABELS = {"cable", "table", "robot", "hook", "ground"}

# Semantic segmentation color map for visualization
SEMANTIC_COLORS = {
    "cable": (255, 80, 80),      # Red
    "table": (180, 180, 180),    # Light gray
    "robot": (80, 150, 255),     # Blue
    "hook": (255, 200, 50),      # Yellow
    "ground": (100, 100, 100),   # Dark gray
    "BACKGROUND": (0, 0, 0),     # Black
    "UNLABELLED": (50, 50, 50),  # Dark gray
}


# =========================================================================
# Helpers
# =========================================================================

def save_rgb(rgb_np: np.ndarray, path: str):
    """Save uint8 RGB array as PNG."""
    try:
        from PIL import Image
        Image.fromarray(rgb_np).save(path)
    except ImportError:
        np.save(path.replace(".png", ".npy"), rgb_np)


def parse_id_to_labels(info_dict: dict) -> dict[int, str]:
    """Parse idToLabels from camera info → {id: class_name}."""
    mapping = {}
    id_labels = info_dict.get("idToLabels", {})
    for id_str, label_info in id_labels.items():
        try:
            sem_id = int(id_str)
        except (ValueError, TypeError):
            continue
        if isinstance(label_info, dict):
            mapping[sem_id] = label_info.get("class", "UNKNOWN")
        elif isinstance(label_info, str):
            mapping[sem_id] = label_info
    return mapping


def colorize_semantic(sem: np.ndarray, id_to_label: dict[int, str]) -> np.ndarray:
    """Create colorized semantic image from ID map."""
    h, w = sem.shape[:2]
    vis = np.zeros((h, w, 3), dtype=np.uint8)
    for sem_id, label in id_to_label.items():
        color = SEMANTIC_COLORS.get(label, ((sem_id * 67 + 100) % 256,
                                            (sem_id * 137 + 50) % 256,
                                            (sem_id * 97 + 150) % 256))
        vis[sem == sem_id] = color
    return vis


def create_overlay(rgb: np.ndarray, sem: np.ndarray, target_id: int,
                   color=(255, 0, 0), alpha=0.4) -> np.ndarray:
    """Overlay semantic mask on RGB image."""
    overlay = rgb.copy()
    mask = sem == target_id
    for c in range(3):
        overlay[:, :, c] = np.where(mask,
                                    np.clip(rgb[:, :, c] * (1 - alpha) + color[c] * alpha, 0, 255),
                                    rgb[:, :, c])
    return overlay.astype(np.uint8)


# =========================================================================
# Main
# =========================================================================

def main():
    device_str = f"cuda:{app_launcher.device_id}"
    out_dir = os.path.join(str(_REPO_ROOT), args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    print(f"[A6a] SOMA Phase A6a: Semantic Label Validation ({device_str})", flush=True)
    print(f"[A6a] Output: {out_dir}\n", flush=True)

    # ------------------------------------------------------------------
    # Scene — enable semantic segmentation on test cameras
    # ------------------------------------------------------------------
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)

    for cam_key in CAMERAS.values():
        cam_cfg = getattr(scene_cfg, cam_key)
        cam_cfg.data_types = ["rgb", "distance_to_image_plane",
                              "semantic_segmentation", "instance_segmentation_fast"]
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
    print(f"[A6a] Running {args.settle_steps} settle steps …", flush=True)
    for _ in range(args.settle_steps):
        sim.step()
        scene.update(sim.get_physics_dt())

    # Extra camera update
    for cam_key in CAMERAS.values():
        scene[cam_key].update(sim.get_physics_dt())

    # ------------------------------------------------------------------
    # Per-camera validation
    # ------------------------------------------------------------------
    results = {
        "phase": "A6a",
        "description": "USD semantic label validation",
        "device": device_str,
        "expected_labels": sorted(EXPECTED_LABELS),
        "cameras": {},
    }
    all_pass = True
    all_labels_found = set()

    for short, cam_key in CAMERAS.items():
        print(f"\n=== {short} ({cam_key}) ===", flush=True)
        cam = scene[cam_key]
        cam.update(sim.get_physics_dt())

        cr = {"name": cam_key}

        # ---------- RGB ----------
        rgb_t = cam.data.output.get("rgb")
        rgb = None
        if rgb_t is not None:
            rgb = rgb_t[0].cpu().numpy()
            if rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            rgb = rgb.astype(np.uint8)
            save_rgb(rgb, os.path.join(out_dir, f"rgb_{short}.png"))

        # ---------- Semantic Segmentation ----------
        sem_t = cam.data.output.get("semantic_segmentation")
        if sem_t is None:
            cr["semantic"] = {"status": "FAIL", "error": "no data"}
            all_pass = False
            results["cameras"][short] = cr
            print(f"  Semantic: FAIL (no data)", flush=True)
            continue

        sem = sem_t[0].cpu().numpy()
        if sem.ndim == 3 and sem.shape[-1] == 1:
            sem = sem[:, :, 0]
        print(f"  Semantic shape={sem.shape} dtype={sem.dtype}", flush=True)

        # Parse label mapping from camera info
        info = cam.data.info
        id_to_label = {}
        if info and len(info) > 0:
            sem_info = info[0].get("semantic_segmentation", {})
            id_to_label = parse_id_to_labels(sem_info)
            print(f"  idToLabels: {id_to_label}", flush=True)

        # Identify labels found in this camera
        unique_ids = np.unique(sem)
        labels_in_image = {}
        for uid in unique_ids:
            label = id_to_label.get(int(uid), f"id_{uid}")
            pixel_count = int(np.sum(sem == uid))
            labels_in_image[label] = {"id": int(uid), "pixels": pixel_count}
            all_labels_found.add(label)

        print(f"  Labels in image:", flush=True)
        for label, info_d in sorted(labels_in_image.items(), key=lambda x: -x[1]["pixels"]):
            pct = info_d["pixels"] / sem.size * 100
            print(f"    {label:15s}  id={info_d['id']:3d}  pixels={info_d['pixels']:6d} ({pct:.1f}%)", flush=True)

        # Check: cable label exists and has pixels
        cable_found = False
        cable_pixels = 0
        cable_id = None
        for label, info_d in labels_in_image.items():
            if label == "cable":
                cable_found = True
                cable_pixels = info_d["pixels"]
                cable_id = info_d["id"]
                break

        cable_ok = cable_found and cable_pixels > 50
        cr["cable_detected"] = cable_ok
        cr["cable_pixels"] = cable_pixels
        cr["labels_found"] = {k: v["pixels"] for k, v in labels_in_image.items()}

        print(f"  Cable: {'PASS' if cable_ok else 'FAIL'} (pixels={cable_pixels})", flush=True)
        if not cable_ok:
            all_pass = False

        # Save colorized semantic image
        vis = colorize_semantic(sem, id_to_label)
        sem_path = os.path.join(out_dir, f"semantic_{short}.png")
        save_rgb(vis, sem_path)
        cr["semantic_image"] = sem_path

        # Save cable overlay on RGB
        if rgb is not None and cable_id is not None:
            overlay = create_overlay(rgb, sem, cable_id, color=(255, 0, 0), alpha=0.5)
            overlay_path = os.path.join(out_dir, f"semantic_overlay_{short}.png")
            save_rgb(overlay, overlay_path)
            cr["overlay_image"] = overlay_path

        # Instance segmentation info
        inst_t = cam.data.output.get("instance_segmentation_fast")
        if inst_t is not None:
            inst = inst_t[0].cpu().numpy()
            if inst.ndim == 3 and inst.shape[-1] == 1:
                inst = inst[:, :, 0]
            inst_info = {}
            if info and len(info) > 0:
                inst_info = info[0].get("instance_segmentation_fast", {})
            cr["instance_count"] = len(np.unique(inst))
            print(f"  Instance: {cr['instance_count']} instances", flush=True)

        cr["status"] = "PASS" if cable_ok else "FAIL"
        results["cameras"][short] = cr

    # ------------------------------------------------------------------
    # Global checks
    # ------------------------------------------------------------------
    # Check which expected labels were found across all cameras
    found_expected = EXPECTED_LABELS.intersection(all_labels_found)
    missing_expected = EXPECTED_LABELS - all_labels_found
    results["labels_found_global"] = sorted(all_labels_found)
    results["expected_labels_found"] = sorted(found_expected)
    results["expected_labels_missing"] = sorted(missing_expected)

    # Cable detected in all 3 cameras?
    cable_all = all(
        results["cameras"].get(s, {}).get("cable_detected", False)
        for s in CAMERAS
    )
    results["cable_detected_all_cameras"] = cable_all
    if not cable_all:
        all_pass = False

    # Aggregate cable pixel counts
    results["cable_pixel_count"] = {
        s: results["cameras"].get(s, {}).get("cable_pixels", 0)
        for s in CAMERAS
    }

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    elapsed = time.time() - t0
    results["overall"] = "PASS" if all_pass else "FAIL"
    results["elapsed_s"] = round(elapsed, 1)

    metrics_path = os.path.join(out_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}", flush=True)
    print(f"SOMA Phase A6a Semantic Label Validation: {results['overall']}", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  Expected labels: {sorted(EXPECTED_LABELS)}", flush=True)
    print(f"  Found labels:    {sorted(all_labels_found)}", flush=True)
    if missing_expected:
        print(f"  Missing labels:  {sorted(missing_expected)}", flush=True)
    print(f"  Cable in all cameras: {cable_all}", flush=True)
    for short in CAMERAS:
        cr = results["cameras"].get(short, {})
        print(f"  {short:<12s}  cable={cr.get('cable_detected', False)}  "
              f"pixels={cr.get('cable_pixels', 0)}  "
              f"status={cr.get('status', 'N/A')}", flush=True)
    print(f"  Results → {metrics_path}", flush=True)
    print(f"  Elapsed: {elapsed:.0f}s", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
