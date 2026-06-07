# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MVP-0A Phase 1 segmenter training (PROPOSE v2 narrowed).

Trains LightUNet on Phase 0 dataset (data/mvp0a_phase0_dataset/) with:
  - C=1 wrist_L only (CC6 MISSED-4)
  - 3-class output: cable / gripper / static
  - Dice + Focal BCE loss (v3 §5.2)
  - AMP autocast for VRAM savings (CC3-13)
  - Divergence detection: abort if val mIoU MA degrades >20% × 3 epochs (CC4-2 ハードストップ rule)
  - Checkpoint resume validity check (CC4-2)
  - Sensor-side DR only (CC5-5: lighting/exposure/noise on RGB; clip pose DR deferred)

Usage::

    CUDA_VISIBLE_DEVICES=1 /home/rlrk/env_isaaclab6/bin/python \
        thread_isaac_lab/scripts/train_segmenter.py \
        --dataset-dir /home/rlrk/IsaacLab/data/mvp0a_phase0_dataset \
        --output-dir /home/rlrk/IsaacLab/data/mvp0a_phase1_train \
        --epochs 30 --batch-size 8 --lr 1e-3 --device cuda:0
"""

import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _repo)

from estimators.core.segmenter import LightUNet, combined_loss, per_class_iou, count_params
from estimators.types import PHASE1_OUTPUT_CLASSES


def rgba_uint32_to_rgb_float(rgba_u32: np.ndarray) -> np.ndarray:
    """uint32 RGBA → float32 RGB in [0, 1]."""
    raw = rgba_u32.view(np.uint8).reshape(*rgba_u32.shape, 4)
    return raw[..., :3].astype(np.float32) / 255.0


def derive_class_map(shape_idx: np.ndarray, lut: np.ndarray) -> np.ndarray:
    NO_HIT = np.uint32(0xFFFFFFFF)
    bg_mask = shape_idx == NO_HIT
    safe_idx = np.where(bg_mask, np.uint32(0), shape_idx)
    safe_idx = np.minimum(safe_idx, np.uint32(lut.shape[0] - 1))
    cls = lut[safe_idx]
    cls[bg_mask] = 0
    return cls


class Phase0Dataset(Dataset):
    """Per-world-per-camera (R or L) frame from Phase 0 dataset.

    NOTE Phase 1 narrowed scope = wrist_L only (camera index 0). Camera 1
    (wrist_R) is dropped per v3 §7.1 literal MVP-0A.
    """

    def __init__(self, dataset_dir, frame_ids, lut, dr=True, camera_idx=0,
                 noise_sigma=0.02, brightness_jitter=0.1):
        self.dataset_dir = dataset_dir
        self.frame_ids = frame_ids
        self.lut = lut
        self.dr = dr
        self.camera_idx = camera_idx  # 0 = wrist_L
        self.noise_sigma = noise_sigma
        self.brightness_jitter = brightness_jitter
        # Each entry = (frame_id, world_idx) pair
        self.items = []
        for fid in frame_ids:
            for w in range(4):  # world_count = 4 from Phase 0 prep
                self.items.append((fid, w))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        fid, w = self.items[idx]
        rgb = np.load(os.path.join(self.dataset_dir, "RGB", f"{fid}_rgb.npz"))["color"]
        depth = np.load(os.path.join(self.dataset_dir, "DEPTH", f"{fid}_depth.npz"))["depth"]
        shape_idx = np.load(os.path.join(self.dataset_dir, "LABELS_ONLY",
                                         f"{fid}_label.npz"))["shape_idx"]
        rgb_f = rgba_uint32_to_rgb_float(rgb[w, self.camera_idx])  # (H, W, 3)
        depth_f = depth[w, self.camera_idx].astype(np.float32)     # (H, W)
        cls_map = derive_class_map(shape_idx[w, self.camera_idx], self.lut)  # (H, W)

        # Sensor-side DR (CC5-5): brightness jitter + Gaussian noise on RGB only
        if self.dr:
            if random.random() < 0.5:
                rgb_f = np.clip(rgb_f + random.uniform(-self.brightness_jitter,
                                                        self.brightness_jitter), 0, 1)
            if random.random() < 0.5:
                rgb_f = np.clip(rgb_f + np.random.randn(*rgb_f.shape).astype(np.float32) * self.noise_sigma, 0, 1)

        # Stack: 4 channels = RGB(3) + depth(1, normalized to [0,1] via /3.0 cap)
        rgb_chw = np.transpose(rgb_f, (2, 0, 1))  # (3, H, W)
        depth_norm = np.clip(depth_f / 3.0, 0, 1)[None, :, :]  # (1, H, W)
        x = np.concatenate([rgb_chw, depth_norm], axis=0)  # (4, H, W)

        # Multi-class binary masks
        gt_masks = np.zeros((len(PHASE1_OUTPUT_CLASSES), cls_map.shape[0], cls_map.shape[1]),
                            dtype=np.float32)
        for ci, class_id in enumerate(PHASE1_OUTPUT_CLASSES):
            gt_masks[ci] = (cls_map == class_id).astype(np.float32)

        return torch.from_numpy(x), torch.from_numpy(gt_masks)


def split_frame_ids(meta, train_frac=0.8, seed=42):
    """Split by reset_idx (analog of v3.1 Appendix F (seed, world_idx) split)."""
    fids = sorted(set(f["frame_id"] for f in meta["frames"]))
    rng = random.Random(seed)
    rng.shuffle(fids)
    n_train = int(len(fids) * train_frac)
    return fids[:n_train], fids[n_train:]


def evaluate(model, loader, device):
    model.eval()
    iou_per_class_sum = torch.zeros(len(PHASE1_OUTPUT_CLASSES), device=device)
    n_batches = 0
    with torch.no_grad():
        for x, gt in loader:
            x = x.to(device, non_blocking=True)
            gt = gt.to(device, non_blocking=True)
            logits = model(x)
            prob = torch.sigmoid(logits)
            iou_per_class_sum += per_class_iou(prob, gt)
            n_batches += 1
    return (iou_per_class_sum / max(n_batches, 1)).cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase0_dataset")
    ap.add_argument("--output-dir", default="/home/rlrk/IsaacLab/data/mvp0a_phase1_train")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--resume", default=None, help="Resume from checkpoint")
    ap.add_argument("--divergence-window", type=int, default=3,
                    help="Consecutive epochs of >20%% mIoU degrade triggering abort (CC4-2)")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)

    device = torch.device(args.device)
    print(f"[train] device={device}, batch={args.batch_size}, epochs={args.epochs}")

    # Load metadata + LUT
    with open(os.path.join(args.dataset_dir, "metadata.json")) as f:
        meta = json.load(f)
    lut = np.load(os.path.join(args.dataset_dir, "LABELS_ONLY", "shape_class_lut.npz"))["lut"]
    print(f"[train] dataset frames={len(meta['frames'])}, lut shapes={lut.shape[0]}")

    train_fids, val_fids = split_frame_ids(meta, train_frac=0.8, seed=args.seed)
    print(f"[train] split: train_frame_ids={len(train_fids)}, val_frame_ids={len(val_fids)} "
          f"(camera_idx=0 wrist_L only)")

    train_ds = Phase0Dataset(args.dataset_dir, train_fids, lut, dr=True, camera_idx=0)
    val_ds = Phase0Dataset(args.dataset_dir, val_fids, lut, dr=False, camera_idx=0)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, pin_memory=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=True)

    # Model
    model = LightUNet(in_channels=4, num_classes=len(PHASE1_OUTPUT_CLASSES)).to(device)
    n_params = count_params(model)
    print(f"[train] LightUNet params={n_params:,} ({n_params / 1e6:.2f} M)")

    # CC4-2: resume validity check
    best_val_mIoU = 0.0
    start_epoch = 0
    if args.resume and os.path.exists(args.resume):
        ckpt = torch.load(args.resume, map_location=device)
        model.load_state_dict(ckpt["model"])
        ckpt_best = ckpt.get("best_val_mIoU", 0.0)
        # Quick val check before resume
        print(f"[train] resume from {args.resume} (ckpt_best_val_mIoU={ckpt_best:.4f}); "
              f"validating before resume...")
        ious_now = evaluate(model, val_loader, device)
        mIoU_now = float(ious_now.mean())
        print(f"[train] post-resume val mIoU={mIoU_now:.4f}; ckpt best={ckpt_best:.4f}")
        if mIoU_now < ckpt_best * 0.5:
            raise RuntimeError(f"Resume validity check FAIL: val mIoU {mIoU_now:.4f} "
                               f"< 0.5×best ({ckpt_best:.4f}). prohibited.md "
                               f"§崩壊 checkpoint resume禁止. Fresh-start required.")
        best_val_mIoU = ckpt_best
        start_epoch = ckpt.get("epoch", 0) + 1
        print(f"[train] resume validity PASS, continuing from epoch {start_epoch}")

    optim = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scaler = torch.amp.GradScaler("cuda")

    # CC4-2 divergence detection state
    val_mIoU_history = []
    consec_degrades = 0

    log = []
    t_start = time.perf_counter()

    for epoch in range(start_epoch, args.epochs):
        model.train()
        loss_sum = 0.0
        dice_sum = 0.0
        focal_sum = 0.0
        n = 0
        t_e = time.perf_counter()
        for x, gt in train_loader:
            x = x.to(device, non_blocking=True)
            gt = gt.to(device, non_blocking=True)
            optim.zero_grad()
            with torch.amp.autocast("cuda"):
                logits = model(x)
                losses = combined_loss(logits, gt)
            scaler.scale(losses["loss"]).backward()
            scaler.step(optim)
            scaler.update()
            loss_sum += float(losses["loss"].detach())
            dice_sum += float(losses["dice"])
            focal_sum += float(losses["focal"])
            n += 1
        train_loss = loss_sum / max(n, 1)
        ep_time = time.perf_counter() - t_e

        # Val
        ious = evaluate(model, val_loader, device)
        val_mIoU = float(ious.mean())
        val_mIoU_history.append(val_mIoU)

        # CC4-2: divergence detection
        diverged = False
        if len(val_mIoU_history) >= args.divergence_window + 1:
            recent = val_mIoU_history[-args.divergence_window:]
            past_best_outside_window = max(val_mIoU_history[:-args.divergence_window])
            if all(v < past_best_outside_window * 0.8 for v in recent):
                diverged = True
                consec_degrades = args.divergence_window

        # Track best + save
        is_best = val_mIoU > best_val_mIoU
        if is_best:
            best_val_mIoU = val_mIoU
            torch.save({
                "model": model.state_dict(),
                "epoch": epoch,
                "best_val_mIoU": best_val_mIoU,
                "val_mIoU_history": val_mIoU_history,
                "n_params": n_params,
            }, os.path.join(args.output_dir, "best.pt"))

        epoch_log = {
            "epoch": int(epoch),
            "train_loss": float(train_loss),
            "train_dice": float(dice_sum / max(n, 1)),
            "train_focal": float(focal_sum / max(n, 1)),
            "val_per_class_iou": [float(x) for x in ious.tolist()],
            "val_mIoU": val_mIoU,
            "best_val_mIoU": best_val_mIoU,
            "epoch_seconds": float(ep_time),
        }
        log.append(epoch_log)
        print(f"[train] ep {epoch:3d} | loss={train_loss:.4f} (dice={epoch_log['train_dice']:.3f} "
              f"focal={epoch_log['train_focal']:.3f}) | val mIoU={val_mIoU:.4f} (cable={ious[0]:.3f} "
              f"gripper={ious[1]:.3f} static={ious[2]:.3f}) | best={best_val_mIoU:.4f} | "
              f"{ep_time:.1f}s {'*BEST*' if is_best else ''}")

        if diverged:
            print(f"[train][CC4-2 DIVERGENCE] {args.divergence_window} consec epochs <80% past best — ABORT")
            break

    total = time.perf_counter() - t_start
    print(f"\n[train] DONE total={total:.1f}s, best val mIoU={best_val_mIoU:.4f}")
    with open(os.path.join(args.output_dir, "train_log.json"), "w") as f:
        json.dump({
            "config": vars(args),
            "n_params": n_params,
            "best_val_mIoU": best_val_mIoU,
            "log": log,
            "total_seconds": float(total),
        }, f, indent=2)
    print(f"[train] log: {os.path.join(args.output_dir, 'train_log.json')}")
    print(f"[train] best ckpt: {os.path.join(args.output_dir, 'best.pt')}")


if __name__ == "__main__":
    main()
