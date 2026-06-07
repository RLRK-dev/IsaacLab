#!/usr/bin/env python3
"""
Test script for Stage 4: Cross-Attention Fusion

Tests the CrossAttentionFusion and CrossAttentionVideoEncoder modules
that replace simple concatenation with attention-based camera fusion.
"""

import torch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.world_model_with_task import (
    CrossAttentionFusion,
    CrossAttentionVideoEncoder,
    WorldModelWithTask,
    WorldModelWithTaskConfig
)


def test_cross_attention_fusion():
    """Test CrossAttentionFusion module."""
    print("=" * 60)
    print("Test 1: CrossAttentionFusion")
    print("=" * 60)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    fusion = CrossAttentionFusion(
        camera_dim=64,
        num_cameras=5,
        num_heads=4,
        num_layers=2
    ).to(device)

    # Create dummy camera features
    batch_size = 2
    camera_features = {
        'front': torch.randn(batch_size, 64, device=device),
        'left': torch.randn(batch_size, 64, device=device),
        'right': torch.randn(batch_size, 64, device=device),
        'back': torch.randn(batch_size, 64, device=device),
        'overhead': torch.randn(batch_size, 64, device=device),
    }

    # Forward pass
    fused = fusion(camera_features)

    print(f"Input: 5 cameras x (B={batch_size}, 64)")
    print(f"Output shape: {fused.shape}")
    print(f"Expected: ({batch_size}, 320)")
    print(f"Parameters: {sum(p.numel() for p in fusion.parameters()):,}")

    assert fused.shape == (batch_size, 320), f"Shape mismatch: {fused.shape}"
    print("[PASS] CrossAttentionFusion test passed")


def test_cross_attention_video_encoder():
    """Test CrossAttentionVideoEncoder module."""
    print("\n" + "=" * 60)
    print("Test 2: CrossAttentionVideoEncoder")
    print("=" * 60)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    encoder = CrossAttentionVideoEncoder(
        out_dim=320,
        camera_dim=64
    ).to(device)

    # Create dummy images
    batch_size = 2
    images = {
        'front': torch.randn(batch_size, 3, 256, 256, device=device),
        'left': torch.randn(batch_size, 3, 256, 256, device=device),
        'right': torch.randn(batch_size, 3, 256, 256, device=device),
        'back': torch.randn(batch_size, 3, 256, 256, device=device),
        'overhead': torch.randn(batch_size, 3, 256, 256, device=device),
    }

    # Forward pass
    visual_features = encoder(images)

    print(f"Input: 5 cameras x (B={batch_size}, 3, 256, 256)")
    print(f"Output shape: {visual_features.shape}")
    print(f"Expected: ({batch_size}, 320)")
    print(f"Parameters: {sum(p.numel() for p in encoder.parameters()):,}")

    assert visual_features.shape == (batch_size, 320), f"Shape mismatch"
    print("[PASS] CrossAttentionVideoEncoder test passed")


def test_world_model_with_cross_attention():
    """Test WorldModelWithTask with cross-attention enabled."""
    print("\n" + "=" * 60)
    print("Test 3: WorldModelWithTask (Cross-Attention Mode)")
    print("=" * 60)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Create config with cross-attention enabled
    config = WorldModelWithTaskConfig(
        use_cross_attention=True,
        cross_attention_heads=4,
        cross_attention_layers=2,
    )

    model = WorldModelWithTask(config).to(device)

    # Create dummy inputs
    batch_size = 2
    front_img = torch.randn(batch_size, 3, 256, 256, device=device)
    left_img = torch.randn(batch_size, 3, 256, 256, device=device)
    right_img = torch.randn(batch_size, 3, 256, 256, device=device)
    back_img = torch.randn(batch_size, 3, 256, 256, device=device)
    overhead_img = torch.randn(batch_size, 3, 256, 256, device=device)
    proprio = torch.randn(batch_size, 34, device=device)
    task_state = torch.randn(batch_size, 44, device=device)
    action = torch.randn(batch_size, 18, device=device)

    # Forward pass
    model.eval()
    with torch.no_grad():
        outputs = model(
            front_img, left_img, right_img, back_img, overhead_img,
            proprio, task_state, action
        )

    print(f"Model configuration:")
    print(f"  use_cross_attention: {model.use_cross_attention}")
    print(f"  cross_attention_encoder: {model.cross_attention_encoder is not None}")
    print(f"  front_encoder: {model.front_encoder is not None}")

    print(f"\nOutputs:")
    print(f"  pred_proprio: {outputs['pred_proprio'].shape}")
    print(f"  pred_task_state: {outputs['pred_task_state'].shape}")
    print(f"  pred_reward: {outputs['pred_reward'].shape}")

    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nTotal parameters: {total_params:,}")

    print("[PASS] WorldModelWithTask cross-attention test passed")


def test_comparison():
    """Compare standard vs cross-attention models."""
    print("\n" + "=" * 60)
    print("Test 4: Standard vs Cross-Attention Comparison")
    print("=" * 60)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Standard model
    config_std = WorldModelWithTaskConfig(use_cross_attention=False)
    model_std = WorldModelWithTask(config_std).to(device)

    # Cross-attention model
    config_ca = WorldModelWithTaskConfig(use_cross_attention=True)
    model_ca = WorldModelWithTask(config_ca).to(device)

    params_std = sum(p.numel() for p in model_std.parameters())
    params_ca = sum(p.numel() for p in model_ca.parameters())

    print(f"Standard model parameters: {params_std:,}")
    print(f"Cross-attention model parameters: {params_ca:,}")
    print(f"Difference: {params_ca - params_std:,} ({(params_ca - params_std) / params_std * 100:.1f}%)")

    # Test inference speed
    import time

    batch_size = 4
    front_img = torch.randn(batch_size, 3, 256, 256, device=device)
    left_img = torch.randn(batch_size, 3, 256, 256, device=device)
    right_img = torch.randn(batch_size, 3, 256, 256, device=device)
    back_img = torch.randn(batch_size, 3, 256, 256, device=device)
    overhead_img = torch.randn(batch_size, 3, 256, 256, device=device)
    proprio = torch.randn(batch_size, 34, device=device)
    task_state = torch.randn(batch_size, 44, device=device)
    action = torch.randn(batch_size, 18, device=device)

    # Warmup
    for _ in range(3):
        with torch.no_grad():
            model_std(front_img, left_img, right_img, back_img, overhead_img, proprio, task_state, action)
            model_ca(front_img, left_img, right_img, back_img, overhead_img, proprio, task_state, action)

    torch.cuda.synchronize()

    # Time standard model
    start = time.time()
    for _ in range(10):
        with torch.no_grad():
            model_std(front_img, left_img, right_img, back_img, overhead_img, proprio, task_state, action)
    torch.cuda.synchronize()
    time_std = (time.time() - start) / 10

    # Time cross-attention model
    start = time.time()
    for _ in range(10):
        with torch.no_grad():
            model_ca(front_img, left_img, right_img, back_img, overhead_img, proprio, task_state, action)
    torch.cuda.synchronize()
    time_ca = (time.time() - start) / 10

    print(f"\nInference time (batch={batch_size}):")
    print(f"  Standard: {time_std * 1000:.2f} ms")
    print(f"  Cross-attention: {time_ca * 1000:.2f} ms")

    print("\n[PASS] Comparison test passed")


def test_attention_weights():
    """Analyze attention patterns."""
    print("\n" + "=" * 60)
    print("Test 5: Attention Weight Analysis")
    print("=" * 60)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    encoder = CrossAttentionVideoEncoder(out_dim=320, camera_dim=64).to(device)

    # Create dummy images with one camera having distinct pattern
    batch_size = 1
    images = {
        'front': torch.randn(batch_size, 3, 256, 256, device=device),
        'left': torch.randn(batch_size, 3, 256, 256, device=device),
        'right': torch.randn(batch_size, 3, 256, 256, device=device),
        'back': torch.zeros(batch_size, 3, 256, 256, device=device),  # Zero image (simulated occlusion)
        'overhead': torch.randn(batch_size, 3, 256, 256, device=device),
    }

    with torch.no_grad():
        output = encoder(images)

    print("Cross-attention enables information sharing between cameras")
    print("When 'back' camera is occluded (zero), other cameras can compensate")
    print(f"Output shape: {output.shape}")
    print(f"Output norm: {output.norm().item():.4f}")

    # Test with all cameras having same input
    same_img = torch.randn(batch_size, 3, 256, 256, device=device)
    images_same = {cam: same_img for cam in ['front', 'left', 'right', 'back', 'overhead']}

    with torch.no_grad():
        output_same = encoder(images_same)

    print(f"\nWith identical camera inputs:")
    print(f"Output norm: {output_same.norm().item():.4f}")

    print("\n[PASS] Attention analysis complete")


def main():
    print("=" * 60)
    print("Stage 4: Cross-Attention Fusion Tests")
    print("=" * 60)

    test_cross_attention_fusion()
    test_cross_attention_video_encoder()
    test_world_model_with_cross_attention()
    test_comparison()
    test_attention_weights()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == '__main__':
    main()
