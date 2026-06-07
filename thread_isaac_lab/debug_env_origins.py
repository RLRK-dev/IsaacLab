#!/usr/bin/env python3
"""
Debug script: Verify env_origins and asset positions
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Debug env_origins")
parser.add_argument("--num_envs", type=int, default=4)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

print("=" * 60)
print("Debug: env_origins and asset positions")
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

    # Step a few times to let physics settle
    for _ in range(10):
        env.step(torch.zeros(args.num_envs, 8, device="cuda:0"))

    print(f"\n[2/2] Checking coordinates...")
    print("=" * 60)

    # Get scene components
    scene = env.scene
    robot = scene["robot"]
    cable = scene["cable"]
    hook = scene["hook"]

    # Get env_origins
    env_origins = scene.env_origins
    print(f"\nenv_origins shape: {env_origins.shape}")
    print(f"env_origins:\n{env_origins}")

    # Get world positions
    print("\n--- World Coordinates ---")

    ee_pos_w = robot.data.body_pos_w[:, -1, :]
    cable_pos_w = cable.data.root_pos_w
    hook_pos_w = hook.data.root_pos_w
    robot_base_w = robot.data.root_pos_w

    print(f"\nRobot base (world):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({robot_base_w[i, 0]:.3f}, {robot_base_w[i, 1]:.3f}, {robot_base_w[i, 2]:.3f})")

    print(f"\nEE position (world):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({ee_pos_w[i, 0]:.3f}, {ee_pos_w[i, 1]:.3f}, {ee_pos_w[i, 2]:.3f})")

    print(f"\nCable position (world):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({cable_pos_w[i, 0]:.3f}, {cable_pos_w[i, 1]:.3f}, {cable_pos_w[i, 2]:.3f})")

    print(f"\nHook position (world):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({hook_pos_w[i, 0]:.3f}, {hook_pos_w[i, 1]:.3f}, {hook_pos_w[i, 2]:.3f})")

    # Get local positions (subtract env_origins)
    print("\n--- Local Coordinates (world - env_origins) ---")

    ee_pos_local = ee_pos_w - env_origins
    cable_pos_local = cable_pos_w - env_origins
    hook_pos_local = hook_pos_w - env_origins

    print(f"\nEE position (local):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({ee_pos_local[i, 0]:.3f}, {ee_pos_local[i, 1]:.3f}, {ee_pos_local[i, 2]:.3f})")

    print(f"\nCable position (local):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({cable_pos_local[i, 0]:.3f}, {cable_pos_local[i, 1]:.3f}, {cable_pos_local[i, 2]:.3f})")

    print(f"\nHook position (local):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: ({hook_pos_local[i, 0]:.3f}, {hook_pos_local[i, 1]:.3f}, {hook_pos_local[i, 2]:.3f})")

    # Calculate distances
    print("\n--- Distances ---")

    ee_to_cable = torch.norm(ee_pos_w - cable_pos_w, dim=-1)
    ee_to_cable_local = torch.norm(ee_pos_local - cable_pos_local, dim=-1)

    print(f"\nEE to Cable distance (world coords):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: {ee_to_cable[i]:.3f} m")

    print(f"\nEE to Cable distance (local coords - should be same!):")
    for i in range(args.num_envs):
        print(f"  env[{i}]: {ee_to_cable_local[i]:.3f} m")

    # Check if assets are ordered correctly
    print("\n--- Asset Count Check ---")
    print(f"Robot num_instances: {robot.num_instances}")
    print(f"Cable num_instances: {cable.num_instances}")
    print(f"Hook num_instances: {hook.num_instances}")

    print("\n" + "=" * 60)
    print("[完了] デバッグ情報の出力が完了しました")
    print("=" * 60)

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
