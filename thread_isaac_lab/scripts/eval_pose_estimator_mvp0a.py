# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0A Phase 1 evaluator + measured benchmark.

Loads trained LightUNet checkpoint, runs eval on Phase 0 dataset val split,
measures per-class mIoU + ROI recall + latency p50/p99 + peak VRAM.

Reports vs PROPOSE v2 / v3 §7.1 / OQ-1b gate criteria.

Usage::

    CUDA_VISIBLE_DEVICES=1 /home/rlrk/env_isaaclab6/bin/python \
        thread_isaac_lab/scripts/eval_pose_estimator_mvp0a.py \
        --dataset-dir /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset \
        --checkpoint /home/rlrk/IsaacLab/data/mvp0a_phase1_train/best.pt \
        --output-report /home/rlrk/IsaacLab/data/mvp0a_phase1_train/mvp0a_benchmark.json \
        --device cuda:0
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from torch.utils.data import DataLoader

_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _repo)

from estimators.core.segmenter import LightUNet, per_class_iou, count_params
from estimators.types import PHASE1_OUTPUT_CLASSES, class_legend

# Reuse Phase0Dataset from train_segmenter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_segmenter import Phase0Dataset, split_frame_ids


# MVP-0A Phase 1 narrowed gates per PROPOSE v2 (3-class subset)
PHASE1_GATES = {
    1: {"name": "cable", "mIoU": 0.80, "roi_recall": 0.95},
    3: {"name": "gripper_finger", "mIoU": 0.65},
    5: {"name": "other_static", "mIoU": 0.50},
}
LATENCY_GATE_P50_MS = 20.0  # v3 §7.1 / OQ-1b (C=1 narrowed scope)
LATENCY_GATE_P99_MS = 35.0
VRAM_GATE_INFERENCE_GIB = 3.0


def compute_roi_recall(pred_prob, gt_mask, threshold=0.5):
    """ROI recall = pixels of true class correctly predicted / pixels of true class."""
    pred_bin = (pred_prob > threshold).float()
    tp = (pred_bin * gt_mask).sum(dim=(0, 2, 3))
    fn = ((1 - pred_bin) * gt_mask).sum(dim=(0, 2, 3))
    return (tp / (tp + fn + 1e-6)).cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    ap.add_argument("--checkpoint", default="/home/rlrk/IsaacLab/data/mvp0a_phase1_train/best.pt")
    ap.add_argument("--output-report",
                    default="/home/rlrk/IsaacLab/data/mvp0a_phase1_train/mvp0a_benchmark.json")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--latency-iters", type=int, default=200,
                    help="Iterations for latency benchmark (B=batch-size)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--camera-idx", type=int, default=0, choices=[0, 1],
                    help="Camera index to evaluate. 0/1 maps to wrist_camera_manager.py:84-86 "
                         "self._cameras[0]=body offset 6, [1]=body offset 15. "
                         "(MVP-0B fact-finding: measures wrist_R generalization gap with --camera-idx 1.)")
    ap.add_argument("--skip-latency", action="store_true",
                    help="Skip latency benchmark (faster runs for fact-finding sweeps).")
    args = ap.parse_args()

    device = torch.device(args.device)

    # Load metadata + LUT
    with open(os.path.join(args.dataset_dir, "metadata.json")) as f:
        meta = json.load(f)
    lut = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY", "shape_class_lut.npz"))["lut"]

    train_fids, val_fids = split_frame_ids(meta, train_frac=0.8, seed=args.seed)
    val_ds = Phase0Dataset(args.dataset_dir, val_fids, lut, dr=False, camera_idx=args.camera_idx)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=0, pin_memory=True)
    print(f"[eval] val: {len(val_ds)} images (camera_idx={args.camera_idx})")

    # Load model
    ckpt = torch.load(args.checkpoint, map_location=device)
    model = LightUNet(in_channels=4, num_classes=len(PHASE1_OUTPUT_CLASSES)).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    n_params = count_params(model)
    print(f"[eval] LightUNet params={n_params:,} ({n_params/1e6:.2f} M)")
    print(f"[eval] checkpoint: epoch={ckpt.get('epoch')} best_val_mIoU={ckpt.get('best_val_mIoU', 'N/A')}")

    # Quality eval
    iou_per_class_sum = torch.zeros(len(PHASE1_OUTPUT_CLASSES), device=device)
    roi_recall_sum = torch.zeros(len(PHASE1_OUTPUT_CLASSES), device=device)
    n_batches = 0
    with torch.no_grad():
        for x, gt in val_loader:
            x = x.to(device, non_blocking=True)
            gt = gt.to(device, non_blocking=True)
            logits = model(x)
            prob = torch.sigmoid(logits)
            iou_per_class_sum += per_class_iou(prob, gt)
            recall = torch.tensor(compute_roi_recall(prob, gt), device=device)
            roi_recall_sum += recall
            n_batches += 1
    ious = (iou_per_class_sum / n_batches).cpu().numpy()
    recalls = (roi_recall_sum / n_batches).cpu().numpy()

    # Latency benchmark (fp16 inference) on cuda:2
    p50 = -1.0
    p99 = -1.0
    mean_ms = -1.0
    peak_mem_gib = -1.0
    if not args.skip_latency:
        print(f"[eval] Latency benchmark fp16: B={args.batch_size}, iters={args.latency_iters}")
        model_fp16 = model.half()
        dummy = torch.randn(args.batch_size, 4, 128, 128, device=device, dtype=torch.float16)
        # Warmup
        for _ in range(20):
            with torch.no_grad():
                _ = model_fp16(dummy)
        torch.cuda.synchronize()

        # Time per iter
        timings_ms = []
        torch.cuda.reset_peak_memory_stats()
        for _ in range(args.latency_iters):
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            with torch.no_grad():
                _ = model_fp16(dummy)
            torch.cuda.synchronize()
            timings_ms.append((time.perf_counter() - t0) * 1000)
        p50 = float(np.percentile(timings_ms, 50))
        p99 = float(np.percentile(timings_ms, 99))
        mean_ms = float(np.mean(timings_ms))
        peak_mem_gib = torch.cuda.max_memory_allocated(device) / (1024 ** 3)
    else:
        print(f"[eval] --skip-latency: latency benchmark skipped (fact-finding mode)")

    # Build report
    report = {
        "checkpoint_path": args.checkpoint,
        "checkpoint_epoch": int(ckpt.get("epoch", -1)),
        "checkpoint_best_val_mIoU": float(ckpt.get("best_val_mIoU", -1)),
        "n_params": int(n_params),
        "n_params_M": float(n_params / 1e6),
        "val_set_size": int(len(val_ds)),
        "camera_idx": int(args.camera_idx),
        "per_class_results": {},
        "latency_fp16": {
            "batch_size": int(args.batch_size),
            "iters": int(args.latency_iters),
            "p50_ms": p50,
            "p99_ms": p99,
            "mean_ms": mean_ms,
            "skipped": bool(args.skip_latency),
        },
        "vram_inference_peak_gib": float(peak_mem_gib),
        "gate_eval": {},
        "config": vars(args),
    }
    for ci, class_id in enumerate(PHASE1_OUTPUT_CLASSES):
        gate = PHASE1_GATES[class_id]
        miou = float(ious[ci])
        recall = float(recalls[ci])
        report["per_class_results"][gate["name"]] = {
            "class_id": int(class_id),
            "mIoU": miou,
            "ROI_recall": recall,
            "gate_mIoU": gate["mIoU"],
            "gate_ROI_recall": gate.get("roi_recall", None),
            "PASSED_mIoU": miou > gate["mIoU"],
            "PASSED_recall": recall > gate.get("roi_recall", 0.0) if gate.get("roi_recall") else None,
        }

    if not args.skip_latency:
        report["gate_eval"]["latency_p50_ms_lt_20"] = p50 < LATENCY_GATE_P50_MS
        report["gate_eval"]["latency_p99_ms_lt_35"] = p99 < LATENCY_GATE_P99_MS
        report["gate_eval"]["vram_inference_lt_3GiB"] = peak_mem_gib < VRAM_GATE_INFERENCE_GIB
    for ci, class_id in enumerate(PHASE1_OUTPUT_CLASSES):
        gate_name = PHASE1_GATES[class_id]["name"]
        report["gate_eval"][f"{gate_name}_mIoU_passed"] = report["per_class_results"][gate_name]["PASSED_mIoU"]

    os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
    with open(args.output_report, "w") as f:
        json.dump(report, f, indent=2)

    # Print
    print(f"\n[eval] === MVP-0A Phase 1 Benchmark Report ===")
    print(f"  Model: LightUNet 4-ch input, {n_params/1e6:.2f} M params, fp16 inference")
    print(f"  Val set: {len(val_ds)} frames (camera_idx={args.camera_idx})")
    print(f"\n  --- Quality (mIoU per class, gate per PROPOSE v2) ---")
    for ci, class_id in enumerate(PHASE1_OUTPUT_CLASSES):
        gate = PHASE1_GATES[class_id]
        miou = float(ious[ci])
        recall = float(recalls[ci])
        marker_iou = "PASS" if miou > gate["mIoU"] else "FAIL"
        roi_str = f" ROI_recall={recall:.4f}" if gate.get("roi_recall") else ""
        print(f"  {gate['name']:>16} mIoU={miou:.4f} (gate>{gate['mIoU']:.2f}) [{marker_iou}]{roi_str}")
    if not args.skip_latency:
        print(f"\n  --- Latency (B={args.batch_size}, fp16, cuda:2 solo) ---")
        print(f"  p50 = {p50:6.2f} ms (gate < {LATENCY_GATE_P50_MS}, "
              f"{'PASS' if p50 < LATENCY_GATE_P50_MS else 'FAIL'})")
        print(f"  p99 = {p99:6.2f} ms (gate < {LATENCY_GATE_P99_MS}, "
              f"{'PASS' if p99 < LATENCY_GATE_P99_MS else 'FAIL'})")
        print(f"  mean= {mean_ms:6.2f} ms")
        print(f"\n  --- VRAM ---")
        print(f"  Peak inference (fp16) = {peak_mem_gib:.3f} GiB "
              f"(gate < {VRAM_GATE_INFERENCE_GIB} GiB, "
              f"{'PASS' if peak_mem_gib < VRAM_GATE_INFERENCE_GIB else 'FAIL'})")
    print(f"\n[eval] Report: {args.output_report}")


if __name__ == "__main__":
    main()
