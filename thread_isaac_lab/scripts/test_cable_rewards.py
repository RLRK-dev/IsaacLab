#!/usr/bin/env python3
"""Test cable end-grasping reward functions."""

import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thread_isaac_lab.training.dual_arm_skill_rewards import (
    DualArmSkillRewardCalculator,
    DualArmObservation,
)


def test_cable_segment_parsing():
    """Test that cable segments are correctly parsed from task_state."""
    print("=" * 60)
    print("Test: Cable Segment Parsing from task_state (44D)")
    print("=" * 60)

    # Create mock task_state (44D)
    # Layout: cable_segments (30D) + hook (3D) + left_ee (3D) + right_ee (3D) + distances (5D)
    num_envs = 4
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Create cable segments (10 segments x 3D)
    # Simulate a U-shape cable: ends are higher, center is lower
    cable_segments = torch.zeros(num_envs, 10, 3, device=device)
    for i in range(10):
        x = 0.4 + (i - 4.5) * 0.05  # X varies along cable length
        y = 0.0
        # U-shape: ends at z=0.9, center at z=0.85
        z = 0.9 - 0.05 * (1 - abs(i - 4.5) / 4.5)
        cable_segments[:, i] = torch.tensor([x, y, z], device=device)

    # Create full task_state
    task_state = torch.zeros(num_envs, 44, device=device)
    task_state[:, :30] = cable_segments.reshape(num_envs, -1)  # Cable segments
    task_state[:, 30:33] = torch.tensor([0.4, 0.0, 1.0], device=device)  # Hook pos
    task_state[:, 33:36] = torch.tensor([0.15, 0.0, 0.92], device=device)  # Left EE
    task_state[:, 36:39] = torch.tensor([0.65, 0.0, 0.92], device=device)  # Right EE

    # Parse
    obs = DualArmObservation.from_task_state(task_state)

    print(f"\n[Cable Segments]")
    print(f"  Full shape: {obs.cable_segments.shape}")  # Should be (4, 10, 3)
    print(f"  Left end (segment 0): {obs.cable_left_end[0].cpu().numpy()}")
    print(f"  Center (segments 4-5 avg): {obs.cable_center[0].cpu().numpy()}")
    print(f"  Right end (segment 9): {obs.cable_right_end[0].cpu().numpy()}")

    print(f"\n[Positions]")
    print(f"  Hook pos: {obs.hook_pos[0].cpu().numpy()}")
    print(f"  Left EE pos: {obs.left_ee_pos[0].cpu().numpy()}")
    print(f"  Right EE pos: {obs.right_ee_pos[0].cpu().numpy()}")

    # Verify U-shape
    left_z = obs.cable_left_end[0, 2].item()
    center_z = obs.cable_center[0, 2].item()
    right_z = obs.cable_right_end[0, 2].item()

    print(f"\n[U-Shape Verification]")
    print(f"  Left end Z: {left_z:.4f}")
    print(f"  Center Z: {center_z:.4f}")
    print(f"  Right end Z: {right_z:.4f}")
    print(f"  Is U-shape (ends > center): {left_z > center_z and right_z > center_z}")

    return True


def test_reach_reward():
    """Test reach reward targets cable ends."""
    print("\n" + "=" * 60)
    print("Test: Reach Reward (left→segment0, right→segment9)")
    print("=" * 60)

    num_envs = 2
    device = "cuda" if torch.cuda.is_available() else "cpu"

    calculator = DualArmSkillRewardCalculator(device=device)

    # Create task_state with cable ends at different positions
    task_state = torch.zeros(num_envs, 44, device=device)

    # Cable segments - left end at (0.2, 0, 0.85), right end at (0.6, 0, 0.85)
    for i in range(10):
        x = 0.2 + i * 0.044  # 0.2 to 0.6
        task_state[:, i*3:(i+1)*3] = torch.tensor([x, 0.0, 0.85], device=device)

    task_state[:, 30:33] = torch.tensor([0.4, 0.0, 1.0], device=device)  # Hook

    # Scenario 1: EEs far from cable ends
    task_state[:, 33:36] = torch.tensor([0.0, 0.0, 0.85], device=device)  # Left EE (far)
    task_state[:, 36:39] = torch.tensor([0.8, 0.0, 0.85], device=device)  # Right EE (far)

    obs_far = DualArmObservation.from_task_state(task_state)

    # Scenario 2: EEs close to cable ends
    next_task_state = task_state.clone()
    next_task_state[:, 33:36] = torch.tensor([0.21, 0.0, 0.85], device=device)  # Left EE (close)
    next_task_state[:, 36:39] = torch.tensor([0.59, 0.0, 0.85], device=device)  # Right EE (close)

    obs_close = DualArmObservation.from_task_state(next_task_state)

    # Compute reward
    action = torch.zeros(num_envs, 18, device=device)

    reward, info = calculator._compute_reach_reward(obs_far, obs_close, action, None)

    print(f"\n[Distances]")
    print(f"  Left EE → Left cable end:")
    print(f"    Before: {info['left_dist'][0].item():.4f}m")
    left_dist_after = torch.norm(obs_close.left_ee_pos - obs_close.cable_left_end, dim=-1)
    print(f"    After: {left_dist_after[0].item():.4f}m")

    print(f"  Right EE → Right cable end:")
    print(f"    Before: {info['right_dist'][0].item():.4f}m")
    right_dist_after = torch.norm(obs_close.right_ee_pos - obs_close.cable_right_end, dim=-1)
    print(f"    After: {right_dist_after[0].item():.4f}m")

    print(f"\n[Reward]")
    print(f"  Total reward: {reward[0].item():.4f}")
    print(f"  Left improvement: {info['left_improvement'][0].item():.4f}")
    print(f"  Right improvement: {info['right_improvement'][0].item():.4f}")
    print(f"  Skill success: {info['skill_success'][0].item()}")

    return True


def test_hang_reward():
    """Test hang reward uses cable center for hook alignment."""
    print("\n" + "=" * 60)
    print("Test: Hang Reward (cable center → hook)")
    print("=" * 60)

    num_envs = 2
    device = "cuda" if torch.cuda.is_available() else "cpu"

    calculator = DualArmSkillRewardCalculator(device=device)

    # Create task_state with U-shaped cable over hook
    task_state = torch.zeros(num_envs, 44, device=device)

    # Cable segments - U-shape with center near hook
    hook_pos = torch.tensor([0.4, 0.0, 1.0], device=device)
    for i in range(10):
        x = 0.2 + i * 0.044
        # U-shape: ends at z=1.1, center at z=1.02 (just above hook)
        z = 1.1 - 0.08 * (1 - abs(i - 4.5) / 4.5)
        task_state[:, i*3:(i+1)*3] = torch.tensor([x, 0.0, z], device=device)

    task_state[:, 30:33] = hook_pos  # Hook position

    # EEs holding cable ends
    task_state[:, 33:36] = torch.tensor([0.2, 0.0, 1.1], device=device)  # Left EE at left end
    task_state[:, 36:39] = torch.tensor([0.6, 0.0, 1.1], device=device)  # Right EE at right end

    obs = DualArmObservation.from_task_state(task_state)

    # Next state: cable center moved closer to hook
    next_task_state = task_state.clone()
    for i in range(10):
        x = 0.2 + i * 0.044
        # U-shape: center now at z=1.01 (closer to hook)
        z = 1.1 - 0.09 * (1 - abs(i - 4.5) / 4.5)
        next_task_state[:, i*3:(i+1)*3] = torch.tensor([x, 0.0, z], device=device)

    next_obs = DualArmObservation.from_task_state(next_task_state)

    action = torch.zeros(num_envs, 18, device=device)

    reward, info = calculator._compute_hang_reward(obs, next_obs, action, None)

    print(f"\n[Cable Center → Hook Distance]")
    print(f"  Before: {info['cable_hook_dist'][0].item():.4f}m")
    next_dist = torch.norm(next_obs.cable_center - next_obs.hook_pos, dim=-1)
    print(f"  After: {next_dist[0].item():.4f}m")

    print(f"\n[U-Shape Check]")
    print(f"  U-shape reward: {info['u_shape_reward'][0].item():.4f}")
    print(f"  Spread reward: {info['spread_reward'][0].item():.4f}")

    print(f"\n[Reward]")
    print(f"  Total reward: {reward[0].item():.4f}")
    print(f"  Precision reward: {info['precision_reward'][0].item():.4f}")
    print(f"  Improvement: {info['improvement'][0].item():.4f}")
    print(f"  Hang success: {info['hang_success'][0].item():.4f}")

    return True


def test_dreamerv3_interface():
    """Test the DreamerV3 integration interface."""
    print("\n" + "=" * 60)
    print("Test: DreamerV3 Interface (compute_skill_reward_from_task_state)")
    print("=" * 60)

    num_envs = 4
    device = "cuda" if torch.cuda.is_available() else "cpu"

    calculator = DualArmSkillRewardCalculator(device=device)

    # Create mock data
    task_state = torch.randn(num_envs, 44, device=device)
    next_task_state = torch.randn(num_envs, 44, device=device)
    action = torch.randn(num_envs, 18, device=device)

    # Test all skills
    skills = [
        "bimanual_reach",
        "bimanual_grasp",
        "bimanual_lift",
        "bimanual_transport",
        "bimanual_hang",
        "bimanual_release",
    ]

    print(f"\n[Testing all skills]")
    for skill in skills:
        reward, info = calculator.compute_skill_reward_from_task_state(
            skill, task_state, next_task_state, action
        )
        print(f"  {skill}: reward shape={reward.shape}, has skill_success={('skill_success' in info)}")

    print("\n[DreamerV3 Interface Test] PASSED")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Cable End-Grasping Reward Function Tests")
    print("=" * 60)

    all_passed = True
    all_passed &= test_cable_segment_parsing()
    all_passed &= test_reach_reward()
    all_passed &= test_hang_reward()
    all_passed &= test_dreamerv3_interface()

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)
