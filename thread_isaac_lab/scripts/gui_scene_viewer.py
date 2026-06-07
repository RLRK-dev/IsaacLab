#!/usr/bin/env python3
"""
Isaac Sim GUI でシーンを表示
カメラ位置を視覚的に確認できる
"""
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", default=False)
args, _ = parser.parse_known_args()

print("[START] GUI Scene Viewer")

from isaaclab.app import AppLauncher
app_launcher = AppLauncher(headless=args.headless, enable_cameras=True)
simulation_app = app_launcher.app

import torch
import numpy as np
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")
from envs.dual_arm_cfg import DualArmSceneCfg

print("[SETUP] Creating scene...")

scene_cfg = DualArmSceneCfg()
scene_cfg.num_envs = 1

sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
sim = sim_utils.SimulationContext(sim_cfg)

# Set a good viewing angle for the main viewport
sim.set_camera_view(
    eye=[1.5, 1.5, 1.5],  # Camera position
    target=[0.4, 0.0, 0.75]  # Looking at table center
)

scene = InteractiveScene(scene_cfg)
sim.reset()

print("[SETUP] Scene created. Running simulation loop...")
print()
print("="*60)
print("GUI Controls:")
print("  - Use mouse to rotate/pan/zoom the viewport")
print("  - Press ESC to close")
print("  - Check Stage panel for object hierarchy")
print("="*60)
print()

# Run simulation
step = 0
while simulation_app.is_running():
    sim.step()
    scene.update(dt=sim.get_physics_dt())
    step += 1

    if step % 100 == 0:
        print(f"Step {step}...")

print("[DONE] Closing...")
simulation_app.close()
