# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Frozen visual encoder for wrist camera observations.

Phase 3 of visual obs pipeline: frozen ResNet-18 backbone with trainable
projection layer. Produces compact feature vectors from RGB images.
"""

import torch
import torch.nn as nn
import torchvision.models as models


# ImageNet normalization constants
_IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406])
_IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225])


class FrozenResNetEncoder(nn.Module):
    """Frozen ResNet-18 backbone with trainable projection.

    Backbone weights are frozen (ImageNet pretrained). Only the final
    Linear projection layer is trainable, mapping 512-D avgpool features
    to a compact representation.

    Input: [B, 3, H, W] float32 RGB in [0, 1].
    Output: [B, out_dim] float32 features.
    """

    def __init__(self, out_dim: int = 64):
        super().__init__()
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        # Keep conv layers + bn + relu + maxpool + layer1-4 (drop avgpool, fc)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.avgpool = nn.AdaptiveAvgPool2d(1)

        # Freeze backbone + avgpool
        for p in self.backbone.parameters():
            p.requires_grad = False

        # Trainable projection: 512 -> out_dim
        self.projection = nn.Linear(512, out_dim)

        # Register ImageNet normalization buffers (move with .to(device))
        self.register_buffer("_mean", _IMAGENET_MEAN.view(1, 3, 1, 1))
        self.register_buffer("_std", _IMAGENET_STD.view(1, 3, 1, 1))

    def forward(self, rgb: torch.Tensor) -> torch.Tensor:
        """Encode RGB images to compact feature vectors.

        Args:
            rgb: [B, 3, H, W] float32, range [0, 1].

        Returns:
            [B, out_dim] float32 feature vectors.
        """
        x = (rgb - self._mean) / self._std
        with torch.no_grad():
            x = self.backbone(x)
            x = self.avgpool(x).flatten(1)  # [B, 512]
        return self.projection(x)  # [B, out_dim]

    def trainable_parameters(self):
        """Return only trainable parameters (projection layer)."""
        return self.projection.parameters()
