"""THREAD Base Policy with World Model Encoder.

This module implements the base policy network that uses the pre-trained
World Model encoder as a frozen feature extractor. The policy network
is trained on top of these features.

Architecture:
    [World Model Encoders (frozen)] -> latent (352D)
        Visual: 256D (64+64+128)
        Proprio: 64D
        Task: 32D
    [Policy Network (trainable)] -> action (18D)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

# Add path for importing World Model components
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@dataclass
class BasePolicyConfig:
    """Configuration for Base Policy."""

    # World Model dimensions (from DualArmWorldModelConfig)
    hand_feature_dim: int = 64
    overhead_feature_dim: int = 128
    proprio_dim: int = 42  # Left 21 + Right 21
    task_state_dim: int = 17  # Task state (cable_pos, hook_pos, ee_pos, distances)
    action_dim: int = 18   # Left 9 + Right 9

    # Latent dimensions
    visual_latent_dim: int = 256  # 64 + 64 + 128 from visual encoders
    proprio_latent_dim: int = 64
    task_latent_dim: int = 32

    # Fusion dimension (352D = 256 visual + 64 proprio + 32 task)
    fusion_dim: int = 352

    # Policy network
    policy_hidden_dims: Tuple[int, ...] = (512, 256)

    # Value network
    value_hidden_dims: Tuple[int, ...] = (512, 256)

    # Activation
    activation: str = "relu"

    # Whether to freeze World Model encoder
    freeze_encoder: bool = True


class WorldModelEncoder(nn.Module):
    """Encoder from World Model that extracts fused features from multi-modal inputs.

    This wraps the visual, proprioceptive, and task encoders from DualArmWorldModel.
    Output: 352D latent (256 visual + 64 proprio + 32 task)
    """

    def __init__(self, config: BasePolicyConfig):
        super().__init__()
        self.config = config

        # Visual encoders (same architecture as DualArmAutoencoder)
        self.left_hand_encoder = self._build_hand_encoder(config.hand_feature_dim)
        self.right_hand_encoder = self._build_hand_encoder(config.hand_feature_dim)
        self.overhead_encoder = self._build_overhead_encoder(config.overhead_feature_dim)

        # Proprio encoder (same as DualArmWorldModel) -> 64D
        self.proprio_encoder = nn.Sequential(
            nn.Linear(config.proprio_dim, 64),
            nn.ReLU(),
            nn.Linear(64, config.proprio_latent_dim),
        )

        # Task state encoder (17D -> 32D)
        self.task_encoder = nn.Sequential(
            nn.Linear(config.task_state_dim, 32),
            nn.ReLU(),
            nn.Linear(32, config.task_latent_dim),
        )

        # Fusion: visual (256) + proprio (64) + task (32) = 352D
        # Visual: hand_feature_dim*2 + overhead_feature_dim = 64+64+128 = 256
        visual_dim = config.hand_feature_dim * 2 + config.overhead_feature_dim
        total_feature_dim = visual_dim + config.proprio_latent_dim + config.task_latent_dim
        self.fusion = nn.Sequential(
            nn.Linear(total_feature_dim, config.fusion_dim),
            nn.ReLU(),
            nn.Linear(config.fusion_dim, config.fusion_dim),
        )

    def _build_hand_encoder(self, feature_dim: int) -> nn.Module:
        """Build hand camera encoder (224x224 -> feature_dim)."""
        return nn.Sequential(
            nn.Conv2d(3, 32, 4, stride=2, padding=1),   # 224 -> 112
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 4, stride=2, padding=1),  # 112 -> 56
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 4, stride=2, padding=1), # 56 -> 28
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 4, stride=2, padding=1), # 28 -> 14
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 4, stride=2, padding=1), # 14 -> 7
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(256, feature_dim),
        )

    def _build_overhead_encoder(self, feature_dim: int) -> nn.Module:
        """Build overhead camera encoder (480x640 -> feature_dim)."""
        return nn.Sequential(
            nn.Conv2d(3, 32, 4, stride=2, padding=1),   # 480x640 -> 240x320
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 4, stride=2, padding=1),  # 240x320 -> 120x160
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 4, stride=2, padding=1), # 120x160 -> 60x80
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 4, stride=2, padding=1), # 60x80 -> 30x40
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 4, stride=2, padding=1), # 30x40 -> 15x20
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(256, feature_dim),
        )

    def forward(
        self,
        left_hand_img: torch.Tensor,
        right_hand_img: torch.Tensor,
        overhead_img: torch.Tensor,
        proprio: torch.Tensor,
        task_state: torch.Tensor,
    ) -> torch.Tensor:
        """Extract fused features from multi-modal inputs.

        Args:
            left_hand_img: Left hand camera image [B, 3, 224, 224]
            right_hand_img: Right hand camera image [B, 3, 224, 224]
            overhead_img: Overhead camera image [B, 3, 480, 640]
            proprio: Proprioceptive state [B, 42]
            task_state: Task state [B, 17]

        Returns:
            Fused latent features [B, 352] (256 visual + 64 proprio + 32 task)
        """
        # Visual encoding -> 256D (64 + 64 + 128)
        left_z = self.left_hand_encoder(left_hand_img)
        right_z = self.right_hand_encoder(right_hand_img)
        overhead_z = self.overhead_encoder(overhead_img)

        # Proprio encoding -> 64D
        proprio_z = self.proprio_encoder(proprio)

        # Task encoding -> 32D
        task_z = self.task_encoder(task_state)

        # Concatenate all features: 256 + 64 + 32 = 352D
        features = torch.cat([left_z, right_z, overhead_z, proprio_z, task_z], dim=-1)

        # Fuse
        latent = self.fusion(features)
        return latent

    def load_from_world_model(self, checkpoint_path: str, device: torch.device = None):
        """Load encoder weights from a World Model checkpoint.

        Args:
            checkpoint_path: Path to the World Model checkpoint (phase1 or phase2)
            device: Device to load the model on

        Supports both:
        - Phase 1 checkpoint (DualArmAutoencoder): visual encoders only
        - Phase 2 checkpoint (DualArmWorldModel): visual + proprio encoders + fusion
        """
        if device is None:
            device = next(self.parameters()).device

        # Import DualArmWorldModelConfig to enable pickle unpickling
        # The checkpoint contains this class in its saved config
        try:
            from train_dual_arm_wm import DualArmWorldModelConfig
        except ImportError:
            # Define a minimal version if import fails
            @dataclass
            class DualArmWorldModelConfig:
                hand_img_size: int = 224
                overhead_height: int = 480
                overhead_width: int = 640
                hand_feature_dim: int = 64
                overhead_feature_dim: int = 128
                proprio_dim: int = 42
                task_state_dim: int = 17
                action_dim: int = 18
                visual_latent_dim: int = 256
                proprio_latent_dim: int = 64
                task_latent_dim: int = 32
                fusion_dim: int = 352  # 256 + 64 + 32
                num_attention_heads: int = 4
                num_transformer_layers: int = 2
                learning_rate: float = 1e-3
                batch_size: int = 32
                num_epochs: int = 100

        # Register class in __main__ module for pickle
        import sys
        if '__main__' in sys.modules:
            sys.modules['__main__'].DualArmWorldModelConfig = DualArmWorldModelConfig

        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        state_dict = checkpoint.get("model_state_dict", checkpoint)

        # Detect checkpoint type by checking for phase2-only keys
        has_proprio_encoder = any("proprio_encoder" in k for k in state_dict.keys())
        has_fusion = any("fusion" in k for k in state_dict.keys())
        is_phase2 = has_proprio_encoder and has_fusion

        print(f"[WorldModelEncoder] Detected {'Phase 2' if is_phase2 else 'Phase 1'} checkpoint")

        loaded_keys = []
        my_state = self.state_dict()

        # Visual encoder mapping
        # Phase 1: left_hand_encoder.encoder.X -> left_hand_encoder.X
        # Phase 2: left_hand_encoder.encoder.X -> left_hand_encoder.X (same)
        visual_encoders = ["left_hand_encoder", "right_hand_encoder", "overhead_encoder"]

        for encoder_name in visual_encoders:
            for key, value in state_dict.items():
                if key.startswith(f"{encoder_name}.encoder."):
                    # Map from Autoencoder/WorldModel key to our key
                    # e.g., "left_hand_encoder.encoder.0.weight" -> "left_hand_encoder.0.weight"
                    new_key = key.replace(f"{encoder_name}.encoder.", f"{encoder_name}.")
                    if new_key in my_state and my_state[new_key].shape == value.shape:
                        my_state[new_key].copy_(value)
                        loaded_keys.append(new_key)

        # Phase 2 additional components (proprio_encoder, task_encoder, fusion)
        if is_phase2:
            for key, value in state_dict.items():
                if key.startswith("proprio_encoder.") or key.startswith("task_encoder.") or key.startswith("fusion."):
                    if key in my_state and my_state[key].shape == value.shape:
                        my_state[key].copy_(value)
                        loaded_keys.append(key)

        print(f"[WorldModelEncoder] Loaded {len(loaded_keys)} parameters from {checkpoint_path}")
        if loaded_keys:
            print(f"[WorldModelEncoder] Sample loaded keys: {loaded_keys[:5]}...")

        # Check for task_encoder loading
        has_task_encoder = any("task_encoder" in k for k in loaded_keys)
        if is_phase2 and not has_task_encoder:
            print("[WorldModelEncoder] Warning: task_encoder not found in checkpoint")


class PolicyNetwork(nn.Module):
    """Policy network that maps latent features to actions."""

    def __init__(self, config: BasePolicyConfig):
        super().__init__()
        self.config = config

        # Build MLP
        layers = []
        input_dim = config.fusion_dim
        for hidden_dim in config.policy_hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
            ])
            input_dim = hidden_dim

        # Output layer (action mean)
        layers.append(nn.Linear(input_dim, config.action_dim))

        self.mlp = nn.Sequential(*layers)

        # Learnable log std
        self.log_std = nn.Parameter(torch.zeros(config.action_dim))

    def forward(self, latent: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            latent: Fused latent features [B, fusion_dim]

        Returns:
            action_mean: Action mean [B, action_dim]
            action_std: Action std [B, action_dim]
        """
        action_mean = self.mlp(latent)
        action_std = self.log_std.exp().expand_as(action_mean)
        return action_mean, action_std


class ValueNetwork(nn.Module):
    """Value network that estimates state value from latent features."""

    def __init__(self, config: BasePolicyConfig):
        super().__init__()
        self.config = config

        # Build MLP
        layers = []
        input_dim = config.fusion_dim
        for hidden_dim in config.value_hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
            ])
            input_dim = hidden_dim

        # Output layer (value)
        layers.append(nn.Linear(input_dim, 1))

        self.mlp = nn.Sequential(*layers)

    def forward(self, latent: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            latent: Fused latent features [B, fusion_dim]

        Returns:
            value: State value [B, 1]
        """
        return self.mlp(latent)


class BasePolicy(nn.Module):
    """THREAD Base Policy with World Model Encoder.

    This policy uses the pre-trained World Model encoder as a frozen
    feature extractor, and trains a policy network on top.
    """

    def __init__(self, config: BasePolicyConfig):
        super().__init__()
        self.config = config

        # World Model encoder (can be frozen)
        self.encoder = WorldModelEncoder(config)

        # Policy and value networks
        self.policy = PolicyNetwork(config)
        self.value = ValueNetwork(config)

        # Freeze encoder if specified
        if config.freeze_encoder:
            self.freeze_encoder()

    def freeze_encoder(self):
        """Freeze the World Model encoder parameters."""
        for param in self.encoder.parameters():
            param.requires_grad = False
        print("[BasePolicy] Encoder frozen")

    def unfreeze_encoder(self):
        """Unfreeze the World Model encoder parameters."""
        for param in self.encoder.parameters():
            param.requires_grad = True
        print("[BasePolicy] Encoder unfrozen")

    def load_encoder(self, checkpoint_path: str, device: torch.device = None):
        """Load encoder weights from World Model checkpoint."""
        self.encoder.load_from_world_model(checkpoint_path, device)

    def forward(
        self,
        left_hand_img: torch.Tensor,
        right_hand_img: torch.Tensor,
        overhead_img: torch.Tensor,
        proprio: torch.Tensor,
        task_state: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """Forward pass.

        Args:
            left_hand_img: Left hand camera image [B, 3, 224, 224]
            right_hand_img: Right hand camera image [B, 3, 224, 224]
            overhead_img: Overhead camera image [B, 3, 480, 640]
            proprio: Proprioceptive state [B, 42]
            task_state: Task state [B, 17]

        Returns:
            Dictionary with action_mean, action_std, value, latent
        """
        # Extract features (352D)
        latent = self.encoder(left_hand_img, right_hand_img, overhead_img, proprio, task_state)

        # Policy forward
        action_mean, action_std = self.policy(latent)

        # Value forward
        value = self.value(latent)

        return {
            "action_mean": action_mean,
            "action_std": action_std,
            "value": value,
            "latent": latent,
        }

    def get_action(
        self,
        left_hand_img: torch.Tensor,
        right_hand_img: torch.Tensor,
        overhead_img: torch.Tensor,
        proprio: torch.Tensor,
        task_state: torch.Tensor,
        deterministic: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Get action from policy.

        Args:
            left_hand_img, right_hand_img, overhead_img, proprio, task_state: Observations
            deterministic: If True, return mean action

        Returns:
            action: Sampled or mean action [B, action_dim]
            log_prob: Log probability of action [B]
            value: State value [B, 1]
        """
        output = self.forward(left_hand_img, right_hand_img, overhead_img, proprio, task_state)

        action_mean = output["action_mean"]
        action_std = output["action_std"]
        value = output["value"]

        if deterministic:
            action = action_mean
            log_prob = torch.zeros(action.shape[0], device=action.device)
        else:
            # Sample from Gaussian
            dist = torch.distributions.Normal(action_mean, action_std)
            action = dist.sample()
            log_prob = dist.log_prob(action).sum(dim=-1)

        return action, log_prob, value

    def evaluate_actions(
        self,
        left_hand_img: torch.Tensor,
        right_hand_img: torch.Tensor,
        overhead_img: torch.Tensor,
        proprio: torch.Tensor,
        task_state: torch.Tensor,
        actions: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Evaluate actions for PPO update.

        Args:
            Observations (including task_state) and actions to evaluate

        Returns:
            log_prob: Log probability of actions [B]
            entropy: Entropy of policy [B]
            value: State value [B, 1]
        """
        output = self.forward(left_hand_img, right_hand_img, overhead_img, proprio, task_state)

        action_mean = output["action_mean"]
        action_std = output["action_std"]
        value = output["value"]

        dist = torch.distributions.Normal(action_mean, action_std)
        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return log_prob, entropy, value

    def get_latent(
        self,
        left_hand_img: torch.Tensor,
        right_hand_img: torch.Tensor,
        overhead_img: torch.Tensor,
        proprio: torch.Tensor,
        task_state: torch.Tensor,
    ) -> torch.Tensor:
        """Get latent features from encoder (for skill adapter).

        Args:
            Observations including task_state

        Returns:
            latent: Fused latent features [B, 352]
        """
        return self.encoder(left_hand_img, right_hand_img, overhead_img, proprio, task_state)


def create_base_policy(
    world_model_path: Optional[str] = None,
    freeze_encoder: bool = True,
    device: torch.device = None,
) -> BasePolicy:
    """Factory function to create a BasePolicy.

    Args:
        world_model_path: Path to World Model checkpoint to load encoder from
        freeze_encoder: Whether to freeze the encoder
        device: Device to put the model on

    Returns:
        Initialized BasePolicy
    """
    config = BasePolicyConfig(freeze_encoder=freeze_encoder)
    policy = BasePolicy(config)

    if device is not None:
        policy = policy.to(device)

    if world_model_path is not None:
        policy.load_encoder(world_model_path, device)

    return policy
