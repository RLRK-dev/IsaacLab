# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Phase 1 segmenter: light U-Net for MVP-0A 3-class output.

Per PROPOSE v2 narrowed scope:
  - C=1 wrist_L only (v3 §7.1 literal、CC6 MISSED-4)
  - 3 sigmoid output channels per pixel: cable / gripper / static
    (Phase 0 dataset GT availability — clip class has 0 pixels in AC wrist views)
  - ~1.5-3M params target (CC3-1 raised from 2M)
  - fp16 inference compatible (CC3-12 cast handled via AMP autocast)

R6 module boundary: this module MUST NOT import newton, env, or
WristCameraManager. Tested by tests/test_estimator_module_boundary.py
(v3.2 Appendix H §H.3 AST lint).
"""

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class SegmenterDiagnostics:
    """Stage 1 diagnostic outputs (CC5-4: NOT consumed by Stage 2-4 placeholders)."""

    seg_confidence_raw: torch.Tensor   # [B] scalar per frame, max-class probability mean
    pred_class_distribution: torch.Tensor  # [B, num_classes] mean prob per class


def _conv_block(in_ch: int, out_ch: int) -> nn.Sequential:
    """Conv-BN-ReLU x 2 block."""
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class LightUNet(nn.Module):
    """Light U-Net for 128x128 RGB+depth → multi-class sigmoid mask.

    Architecture:
      - Encoder: 4 conv blocks with downsampling (32 → 64 → 128 → 192 channels)
      - Bottleneck: 192 → 256
      - Decoder: 4 transposed conv blocks with skip connections
      - Output head: 1x1 conv to num_classes (sigmoid via training loss)
    """

    def __init__(self, in_channels: int = 4, num_classes: int = 3):
        """Args:
            in_channels: 4 = RGB(3) + depth(1)
            num_classes: 3 = cable + gripper + static
        """
        super().__init__()
        self.num_classes = num_classes
        # Encoder
        self.enc1 = _conv_block(in_channels, 32)
        self.enc2 = _conv_block(32, 64)
        self.enc3 = _conv_block(64, 128)
        self.enc4 = _conv_block(128, 192)
        # Bottleneck
        self.bottleneck = _conv_block(192, 256)
        # Decoder (transposed conv)
        self.up4 = nn.ConvTranspose2d(256, 192, 2, stride=2)
        self.dec4 = _conv_block(192 + 192, 192)
        self.up3 = nn.ConvTranspose2d(192, 128, 2, stride=2)
        self.dec3 = _conv_block(128 + 128, 128)
        self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec2 = _conv_block(64 + 64, 64)
        self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec1 = _conv_block(32 + 32, 32)
        # Head
        self.head = nn.Conv2d(32, num_classes, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Args:
            x: [B, 4, 128, 128] (RGB + depth, normalized)
        Returns:
            logits [B, num_classes, 128, 128] (apply sigmoid for prob)
        """
        # Encoder
        e1 = self.enc1(x)
        e2 = self.enc2(F.max_pool2d(e1, 2))
        e3 = self.enc3(F.max_pool2d(e2, 2))
        e4 = self.enc4(F.max_pool2d(e3, 2))
        # Bottleneck
        b = self.bottleneck(F.max_pool2d(e4, 2))
        # Decoder
        d4 = self.dec4(torch.cat([self.up4(b), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def dice_loss(pred_prob: torch.Tensor, gt_mask: torch.Tensor, eps: float = 1.0) -> torch.Tensor:
    """Dice loss per channel, averaged.

    Args:
        pred_prob: [B, C, H, W] sigmoid probabilities in [0, 1]
        gt_mask: [B, C, H, W] binary 0/1
    """
    inter = (pred_prob * gt_mask).sum(dim=(0, 2, 3))
    union = pred_prob.sum(dim=(0, 2, 3)) + gt_mask.sum(dim=(0, 2, 3))
    return (1 - (2 * inter + eps) / (union + eps)).mean()


def focal_bce_loss(pred_logits: torch.Tensor, gt_mask: torch.Tensor,
                   gamma: float = 2.0, alpha: float = 0.25) -> torch.Tensor:
    """Focal BCE for class-imbalanced segmentation."""
    bce = F.binary_cross_entropy_with_logits(pred_logits, gt_mask, reduction="none")
    pt = torch.exp(-bce)
    focal = alpha * ((1 - pt) ** gamma) * bce
    return focal.mean()


def combined_loss(pred_logits: torch.Tensor, gt_mask: torch.Tensor) -> dict:
    """Per v3 §5.2: dice + focal."""
    pred_prob = torch.sigmoid(pred_logits)
    dl = dice_loss(pred_prob, gt_mask)
    fl = focal_bce_loss(pred_logits, gt_mask)
    return {
        "loss": dl + fl,
        "dice": dl.detach(),
        "focal": fl.detach(),
    }


def per_class_iou(pred_prob: torch.Tensor, gt_mask: torch.Tensor,
                  threshold: float = 0.5) -> torch.Tensor:
    """Returns [C] IoU per class for the batch."""
    pred_bin = (pred_prob > threshold).float()
    inter = (pred_bin * gt_mask).sum(dim=(0, 2, 3))
    union = ((pred_bin + gt_mask) > 0).float().sum(dim=(0, 2, 3))
    return (inter + 1e-6) / (union + 1e-6)
