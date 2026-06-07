#!/usr/bin/env python3
"""Debug environment API for Isaac Lab 2.3.0"""

from __future__ import annotations
import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# Now import
import gymnasium as gym
import isaaclab_tasks
from isaaclab_tasks.utils import parse_env_cfg

print("=" * 60)
print("Debug: Isaac Lab 2.3.0 Environment API")
print("=" * 60)

task_name = "Isaac-Cartpole-v0"
device = "cuda:0"

# Create env config
env_cfg = parse_env_cfg(task_name, num_envs=4, device=device)
env = gym.make(task_name, cfg=env_cfg)

print(f"\n1. env type: {type(env)}")
print(f"2. env.unwrapped type: {type(env.unwrapped)}")

# Check observation space
obs_space = env.observation_space
print(f"\n3. observation_space type: {type(obs_space)}")
print(f"   observation_space: {obs_space}")

# Check action space
act_space = env.action_space
print(f"\n4. action_space type: {type(act_space)}")
print(f"   action_space: {act_space}")

# Get dims from unwrapped
unwrapped = env.unwrapped
print(f"\n5. Checking unwrapped attributes:")

# Try different ways to get obs dims
if hasattr(unwrapped, 'num_obs'):
    print(f"   unwrapped.num_obs: {unwrapped.num_obs}")
if hasattr(unwrapped, 'num_actions'):
    print(f"   unwrapped.num_actions: {unwrapped.num_actions}")
if hasattr(unwrapped, 'observation_manager'):
    om = unwrapped.observation_manager
    print(f"   observation_manager: {om}")
    if hasattr(om, 'group_obs_dim'):
        print(f"   group_obs_dim: {om.group_obs_dim}")
if hasattr(unwrapped, 'cfg'):
    print(f"   cfg type: {type(unwrapped.cfg)}")

# Try reset to get actual observation
print(f"\n6. Trying env.reset()...")
obs, info = env.reset()
print(f"   obs type: {type(obs)}")
if isinstance(obs, dict):
    for k, v in obs.items():
        print(f"   obs['{k}']: shape={v.shape}, dtype={v.dtype}")
else:
    print(f"   obs shape: {obs.shape}")

env.close()
simulation_app.close()
print("\nDone!")
