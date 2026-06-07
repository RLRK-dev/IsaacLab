# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0B fact-finding B: dataset audit for two-camera fusion adequacy.

Computes per-camera per-frame cable/gripper visibility (pixel count and ratio)
across the existing Phase 0 dataset, identifies "complementary occlusion"
frames where a class is visible in one camera but not the other.

Decides whether the existing 288-frame dataset is informative for two-view
fusion evaluation (per 5-CC Debate CC2 [3] / CC6 NHA #3 / NHA #8 challenges).

Usage::

    /home/rlrk/env_isaaclab6/bin/python \
        thread_isaac_lab/scripts/audit_mvp0b_dataset.py \
        --dataset-dir /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset \
        --output-report /tmp/mvp0b_factfind_dataset_audit.json
"""

import argparse
import json
import os
from collections import defaultdict

import numpy as np

# Class IDs from shape_class_lut (matches estimators/types.py:81-89).
CABLE_CLASS = 1
CLIP_CLASS = 2
GRIPPER_CLASS = 3
ARM_CLASS = 4
STATIC_CLASS = 5

VISIBILITY_PIXEL_THRESHOLD = 50  # frames with <50 pixels of class are "occluded"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    ap.add_argument("--output-report", default="/tmp/mvp0b_factfind_dataset_audit.json")
    args = ap.parse_args()

    labels_dir = os.path.join(args.dataset_dir, "LABELS_ONLY")
    lut = np.load(os.path.join(labels_dir, "shape_class_lut.npz"))["lut"]
    with open(os.path.join(args.dataset_dir, "metadata.json")) as f:
        meta = json.load(f)

    # Iterate label .npz files
    label_files = sorted(f for f in os.listdir(labels_dir) if f.endswith("_label.npz"))
    print(f"[audit] {len(label_files)} label files, world_count={meta['world_count']}, "
          f"camera_count={meta['camera_count']}, resolution={meta['resolution']}")

    # Per-(frame_id, world, camera): pixel counts per class
    per_view = []  # rows of dict
    NO_HIT = np.uint32(0xFFFFFFFF)

    for fname in label_files:
        frame_id = fname.replace("_label.npz", "")
        d = np.load(os.path.join(labels_dir, fname))
        shape_idx = d["shape_idx"]  # (W, C, H, W) uint32
        for w in range(shape_idx.shape[0]):
            for c in range(shape_idx.shape[1]):
                bg = shape_idx[w, c] == NO_HIT
                safe = np.where(bg, np.uint32(0), shape_idx[w, c])
                safe = np.minimum(safe, np.uint32(lut.shape[0] - 1))
                cls = lut[safe]
                cls[bg] = 0
                per_view.append({
                    "frame_id": frame_id,
                    "world": int(w),
                    "camera": int(c),
                    "cable_pixels": int((cls == CABLE_CLASS).sum()),
                    "clip_pixels": int((cls == CLIP_CLASS).sum()),
                    "gripper_pixels": int((cls == GRIPPER_CLASS).sum()),
                    "arm_pixels": int((cls == ARM_CLASS).sum()),
                    "static_pixels": int((cls == STATIC_CLASS).sum()),
                })

    # Group by (frame_id, world) → measure complementary occlusion
    by_scene = defaultdict(dict)
    for v in per_view:
        by_scene[(v["frame_id"], v["world"])][v["camera"]] = v

    complementary_cable = 0  # cable visible in one cam but not the other
    complementary_gripper = 0
    both_visible_cable = 0
    both_invisible_cable = 0
    cable_pixel_distribution = {0: [], 1: []}
    gripper_pixel_distribution = {0: [], 1: []}

    for (fid, w), cams in by_scene.items():
        if 0 not in cams or 1 not in cams:
            continue
        c0_cable = cams[0]["cable_pixels"]
        c1_cable = cams[1]["cable_pixels"]
        c0_grip = cams[0]["gripper_pixels"]
        c1_grip = cams[1]["gripper_pixels"]

        cable_pixel_distribution[0].append(c0_cable)
        cable_pixel_distribution[1].append(c1_cable)
        gripper_pixel_distribution[0].append(c0_grip)
        gripper_pixel_distribution[1].append(c1_grip)

        v0 = c0_cable >= VISIBILITY_PIXEL_THRESHOLD
        v1 = c1_cable >= VISIBILITY_PIXEL_THRESHOLD
        if v0 and not v1:
            complementary_cable += 1
        elif v1 and not v0:
            complementary_cable += 1
        elif v0 and v1:
            both_visible_cable += 1
        else:
            both_invisible_cable += 1

        g0 = c0_grip >= VISIBILITY_PIXEL_THRESHOLD
        g1 = c1_grip >= VISIBILITY_PIXEL_THRESHOLD
        if (g0 and not g1) or (g1 and not g0):
            complementary_gripper += 1

    total_scenes = len(by_scene)
    cable_pix_0 = np.array(cable_pixel_distribution[0])
    cable_pix_1 = np.array(cable_pixel_distribution[1])

    report = {
        "dataset_dir": args.dataset_dir,
        "label_files_count": len(label_files),
        "total_scenes": total_scenes,
        "world_count": int(meta["world_count"]),
        "camera_count": int(meta["camera_count"]),
        "visibility_threshold_pixels": VISIBILITY_PIXEL_THRESHOLD,
        "cable_visibility": {
            "both_cameras_visible": both_visible_cable,
            "complementary_visible": complementary_cable,
            "both_invisible": both_invisible_cable,
            "complementary_ratio": float(complementary_cable / max(total_scenes, 1)),
        },
        "gripper_visibility": {
            "complementary_visible": complementary_gripper,
            "complementary_ratio": float(complementary_gripper / max(total_scenes, 1)),
        },
        "cable_pixel_stats_camera0": {
            "mean": float(cable_pix_0.mean()),
            "median": float(np.median(cable_pix_0)),
            "min": int(cable_pix_0.min()),
            "max": int(cable_pix_0.max()),
            "std": float(cable_pix_0.std()),
        },
        "cable_pixel_stats_camera1": {
            "mean": float(cable_pix_1.mean()),
            "median": float(np.median(cable_pix_1)),
            "min": int(cable_pix_1.min()),
            "max": int(cable_pix_1.max()),
            "std": float(cable_pix_1.std()),
        },
        "fusion_informativeness_assessment": {
            "complementary_cable_count": complementary_cable,
            "complementary_cable_ratio": float(complementary_cable / max(total_scenes, 1)),
            "verdict": (
                "ADEQUATE" if complementary_cable >= 30
                else "MARGINAL" if complementary_cable >= 10
                else "INSUFFICIENT"
            ),
        },
    }

    os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
    with open(args.output_report, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[audit] === Dataset Audit Report ===")
    print(f"  Label files: {len(label_files)}, scenes: {total_scenes} (frame_id × world)")
    print(f"  Cable visibility:")
    print(f"    both cameras visible:        {both_visible_cable}")
    print(f"    complementary (one only):    {complementary_cable}")
    print(f"    both invisible:              {both_invisible_cable}")
    print(f"  Gripper complementary:         {complementary_gripper}")
    print(f"  Cable pixels camera_idx=0: mean={cable_pix_0.mean():.0f}, median={np.median(cable_pix_0):.0f}")
    print(f"  Cable pixels camera_idx=1: mean={cable_pix_1.mean():.0f}, median={np.median(cable_pix_1):.0f}")
    print(f"  Fusion informativeness: {report['fusion_informativeness_assessment']['verdict']}")
    print(f"\n[audit] Report: {args.output_report}")


if __name__ == "__main__":
    main()
