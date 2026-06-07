#!/usr/bin/env python3
"""Debug cable loading and position."""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from envs.dual_arm_cfg import DualArmSceneCfg, TABLE_HEIGHT

print("\n" + "="*60)
print("Cable Debug Script")
print("="*60)

# Setup
scene_cfg = DualArmSceneCfg()
scene_cfg.num_envs = 1

sim_cfg = sim_utils.SimulationCfg(dt=1/60.0)
sim = sim_utils.SimulationContext(sim_cfg)
sim.set_camera_view([1.5, 0.0, 1.5], [0.4, 0.0, 0.85])

print(f"\nTABLE_HEIGHT: {TABLE_HEIGHT}")
print(f"Expected cable Z: {TABLE_HEIGHT + 0.02}")

scene = InteractiveScene(scene_cfg)
sim.reset()

# Run a few steps
for _ in range(30):
    sim.step()
scene.update(sim.get_physics_dt())

# Check cable
print("\n--- Cable Info ---")
cable = scene["cable"]
print(f"Cable type: {type(cable)}")
print(f"Cable prim path: {cable.cfg.prim_path}")

# Check if it's an Articulation
if hasattr(cable.data, 'body_pos_w'):
    body_pos = cable.data.body_pos_w[0]
    print(f"\nCable has {body_pos.shape[0]} bodies")
    print(f"Body positions:")
    for i, pos in enumerate(body_pos):
        print(f"  Body {i}: {pos.cpu().tolist()}")
    
    print(f"\nCable root pos: {cable.data.root_pos_w[0].cpu().tolist()}")
    print(f"Cable root quat: {cable.data.root_quat_w[0].cpu().tolist()}")
else:
    print(f"Root pos: {cable.data.root_pos_w[0].cpu().tolist()}")
    print(f"Root quat: {cable.data.root_quat_w[0].cpu().tolist()}")

# Check hook for reference
print("\n--- Hook Info ---")
hook = scene["hook_stem"]
print(f"Hook pos: {hook.data.root_pos_w[0].cpu().tolist()}")

# Wait a bit more
for _ in range(100):
    scene.write_data_to_sim()
    sim.step()
    scene.update(sim.get_physics_dt())

print("\n--- After 100 more steps ---")
if hasattr(cable.data, 'body_pos_w'):
    body_pos = cable.data.body_pos_w[0]
    print(f"Cable body 0 (base): {body_pos[0].cpu().tolist()}")
    print(f"Cable body 9 (tip): {body_pos[9].cpu().tolist()}")

print("\n" + "="*60)
simulation_app.close()
