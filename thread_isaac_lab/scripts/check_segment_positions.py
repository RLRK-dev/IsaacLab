#!/usr/bin/env python3
"""
Check cable segment positions for X-axis cable layout (Plan A).
This script confirms which segment is at which end of the cable.
"""

import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Check Cable Segment Positions")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Post-launch imports
import torch
from isaaclab.scene import InteractiveScene
from isaaclab.sim import SimulationCfg, SimulationContext
from envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.configs.task_config import PHYSICS_DT

def main():
    """Main function to check segment positions."""

    # Create simulation context
    sim_cfg = SimulationCfg(dt=PHYSICS_DT, device="cuda:0")
    sim = SimulationContext(sim_cfg)

    # Create scene
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)
    scene = InteractiveScene(scene_cfg)

    # Reset simulation
    sim.reset()

    # Warm up
    print("\n[Setup] Warming up simulation...")
    for _ in range(100):
        sim.step()
    scene.update(sim.get_physics_dt())

    # Get cable reference
    cable = scene["cable"]

    # Get segment positions
    cable_pos = cable.data.body_pos_w[0]  # [num_bodies, 3]
    num_segments = cable_pos.shape[0]

    print("\n" + "=" * 70)
    print("CABLE SEGMENT POSITIONS (Plan A: X-axis layout)")
    print("=" * 70)
    print(f"\nNumber of segments: {num_segments}")
    print(f"Cable center position (from config): X=0.35, Y=0.0, Z={0.75 + 0.03:.3f}")
    print("\n" + "-" * 70)
    print(f"{'Seg':>4} | {'X':>10} | {'Y':>10} | {'Z':>10} | Notes")
    print("-" * 70)

    # Find min/max X positions
    min_x_idx = torch.argmin(cable_pos[:, 0]).item()
    max_x_idx = torch.argmax(cable_pos[:, 0]).item()

    for i in range(num_segments):
        pos = cable_pos[i].cpu()
        notes = ""
        if i == min_x_idx:
            notes = "<-- MIN X (left end)"
        elif i == max_x_idx:
            notes = "<-- MAX X (right end)"
        print(f"{i:>4} | {pos[0]:>10.4f} | {pos[1]:>10.4f} | {pos[2]:>10.4f} | {notes}")

    print("-" * 70)

    # Summary
    left_pos = cable_pos[min_x_idx].cpu()
    right_pos = cable_pos[max_x_idx].cpu()
    cable_length = torch.sqrt(torch.sum((cable_pos[max_x_idx] - cable_pos[min_x_idx])**2)).item()

    print(f"\n[SUMMARY]")
    print(f"  LEFT_CLAMP_SEGMENT  = {min_x_idx}  (X={left_pos[0]:.4f}, Y={left_pos[1]:.4f})")
    print(f"  RIGHT_CLAMP_SEGMENT = {max_x_idx}  (X={right_pos[0]:.4f}, Y={right_pos[1]:.4f})")
    print(f"  Cable span: {cable_length:.4f}m")

    # Check robot positions
    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]

    left_base = robot_left.data.root_pos_w[0].cpu()
    right_base = robot_right.data.root_pos_w[0].cpu()

    print(f"\n[ROBOT POSITIONS]")
    print(f"  Left robot base:  X={left_base[0]:.4f}, Y={left_base[1]:.4f}, Z={left_base[2]:.4f}")
    print(f"  Right robot base: X={right_base[0]:.4f}, Y={right_base[1]:.4f}, Z={right_base[2]:.4f}")

    # Check hook position
    hook_stem = scene["hook_stem"]
    hook_pos = hook_stem.data.root_pos_w[0].cpu()
    print(f"\n[HOOK POSITION]")
    print(f"  Hook stem: X={hook_pos[0]:.4f}, Y={hook_pos[1]:.4f}, Z={hook_pos[2]:.4f}")

    print("\n" + "=" * 70)
    print("RECOMMENDED collect_goal_images.py SETTINGS:")
    print("=" * 70)
    print(f"  LEFT_CLAMP_SEGMENT = {min_x_idx}")
    print(f"  RIGHT_CLAMP_SEGMENT = {max_x_idx}")
    print("=" * 70 + "\n")

    # Clean exit
    import threading
    import os

    def force_exit():
        os._exit(0)

    exit_timer = threading.Timer(5.0, force_exit)
    exit_timer.daemon = True
    exit_timer.start()

    try:
        simulation_app.close()
    except:
        pass

    exit_timer.cancel()
    os._exit(0)


if __name__ == "__main__":
    main()
