#!/usr/bin/env python3
"""
Debug script: Check cable indexing with 2048 environments
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Debug 2048 envs indexing")
parser.add_argument("--num_envs", type=int, default=2048)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

print("=" * 60)
print(f"Debug: Asset indexing with {args.num_envs} environments")
print("=" * 60)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch

sys.path.insert(0, str(Path(__file__).parent))

from envs.hook_hanging_env import HookHangingEnv, HookHangingEnvCfg


def main():
    print(f"\n[1/2] Creating environment with num_envs={args.num_envs}...")

    env_cfg = HookHangingEnvCfg()
    env_cfg.scene.num_envs = args.num_envs
    env_cfg.seed = 42

    env = HookHangingEnv(cfg=env_cfg)

    # Reset
    env.reset()

    # Step to settle physics
    for _ in range(5):
        env.step(torch.zeros(args.num_envs, 8, device="cuda:0"))

    print(f"\n[2/2] Checking asset indexing...")
    print("=" * 60)

    scene = env.scene
    robot = scene["robot"]
    cable = scene["cable"]
    hook = scene["hook"]
    env_origins = scene.env_origins

    # Print shapes
    print(f"\nTensor shapes:")
    print(f"  robot.data.body_pos_w: {robot.data.body_pos_w.shape}")
    print(f"  cable.data.root_pos_w: {cable.data.root_pos_w.shape}")
    print(f"  hook.data.root_pos_w: {hook.data.root_pos_w.shape}")
    print(f"  env_origins: {env_origins.shape}")

    print(f"\nInstance counts:")
    print(f"  robot.num_instances: {robot.num_instances}")
    print(f"  cable.num_instances: {cable.num_instances}")
    print(f"  hook.num_instances: {hook.num_instances}")

    # Print first few and last few positions
    ee_pos_w = robot.data.body_pos_w[:, -1, :]
    cable_pos_w = cable.data.root_pos_w
    hook_pos_w = hook.data.root_pos_w

    print(f"\n--- First 4 environments ---")
    for i in range(4):
        print(f"  env[{i}]: EE=({ee_pos_w[i, 0]:.2f}, {ee_pos_w[i, 1]:.2f}, {ee_pos_w[i, 2]:.2f}), "
              f"Cable=({cable_pos_w[i, 0]:.2f}, {cable_pos_w[i, 1]:.2f}, {cable_pos_w[i, 2]:.2f}), "
              f"Hook=({hook_pos_w[i, 0]:.2f}, {hook_pos_w[i, 1]:.2f}, {hook_pos_w[i, 2]:.2f})")

    print(f"\n--- Last 4 environments ---")
    for i in range(args.num_envs - 4, args.num_envs):
        print(f"  env[{i}]: EE=({ee_pos_w[i, 0]:.2f}, {ee_pos_w[i, 1]:.2f}, {ee_pos_w[i, 2]:.2f}), "
              f"Cable=({cable_pos_w[i, 0]:.2f}, {cable_pos_w[i, 1]:.2f}, {cable_pos_w[i, 2]:.2f}), "
              f"Hook=({hook_pos_w[i, 0]:.2f}, {hook_pos_w[i, 1]:.2f}, {hook_pos_w[i, 2]:.2f})")

    # Check if cable is at env_origins position
    print(f"\n--- env_origins (first 4) ---")
    for i in range(4):
        print(f"  env_origins[{i}]: ({env_origins[i, 0]:.2f}, {env_origins[i, 1]:.2f}, {env_origins[i, 2]:.2f})")

    # Calculate distances
    distance = torch.norm(cable_pos_w - ee_pos_w, dim=-1)
    print(f"\n--- Distance statistics ---")
    print(f"  mean: {distance.mean().item():.3f} m")
    print(f"  min:  {distance.min().item():.3f} m")
    print(f"  max:  {distance.max().item():.3f} m")
    print(f"  std:  {distance.std().item():.3f} m")

    # Check: is cable position constant across all envs?
    cable_spread = (cable_pos_w.max(dim=0)[0] - cable_pos_w.min(dim=0)[0])
    print(f"\n--- Cable position spread (max - min) ---")
    print(f"  X: {cable_spread[0].item():.3f} m")
    print(f"  Y: {cable_spread[1].item():.3f} m")
    print(f"  Z: {cable_spread[2].item():.3f} m")

    if cable_spread[0].item() < 1.0 and cable_spread[1].item() < 1.0:
        print("\n  [WARNING] Cable positions have very low spread - cable may not be properly replicated!")
    else:
        print("\n  [OK] Cable positions are spread across environments")

    print("\n" + "=" * 60)

    env.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulation_app.close()
