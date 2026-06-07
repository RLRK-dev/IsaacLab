#!/usr/bin/env python3
"""
Test Dual Arm Flexible Cable Environment
=========================================

Tests the new dual arm + flexible cable scene configuration.
"""
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

from envs.dual_arm_flex_env_cfg import (
    DualArmFlexCableSceneCfg,
    NUM_CABLE_SEGMENTS,
    CABLE_TOTAL_LENGTH,
    TABLE_HEIGHT,
    TASK_STATE_DIM,
)
from envs.flexible_cable_utils import create_flexible_cable, create_l_hook
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def main():
    print("\n" + "="*60, flush=True)
    print("DUAL ARM FLEXIBLE CABLE ENVIRONMENT TEST", flush=True)
    print("="*60, flush=True)

    print(f"\n[Config]", flush=True)
    print(f"  Cable segments: {NUM_CABLE_SEGMENTS}", flush=True)
    print(f"  Cable length: {CABLE_TOTAL_LENGTH*100:.0f} cm", flush=True)
    print(f"  Table height: {TABLE_HEIGHT*100:.0f} cm", flush=True)
    print(f"  Task state dim: {TASK_STATE_DIM}D", flush=True)

    # Setup simulation
    print("\n[Status] Setting up simulation...", flush=True)
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(1.5, -1.0, 1.5),
        target=(0.5, 0.0, 0.75)
    )

    # Create scene
    print("[Status] Creating scene...", flush=True)
    cfg = DualArmFlexCableSceneCfg()
    scene = InteractiveScene(cfg)
    print("[Status] Scene created", flush=True)

    # Add flexible cable with joints
    print("[Status] Adding flexible cable...", flush=True)
    cable_segments = create_flexible_cable(
        base_path="/World/envs/env_0",
        cable_name="flexible_cable",
        start_pos=(0.35, 0.0, TABLE_HEIGHT + 0.02),
        num_segments=NUM_CABLE_SEGMENTS,
        segment_length=0.025,
        segment_radius=0.006,
        color=(1.0, 0.4, 0.0),
    )
    print(f"[Status] Created {len(cable_segments)} cable segments", flush=True)

    # Start simulation
    print("[Status] Starting simulation...", flush=True)
    sim.reset()
    print("[Status] Simulation started!", flush=True)

    print("\n[Scene Summary]", flush=True)
    print("  - 2x Franka Panda robots", flush=True)
    print("  - Table (80x100cm)", flush=True)
    print(f"  - {NUM_CABLE_SEGMENTS}-segment flexible cable", flush=True)
    print("  - L-shaped hook", flush=True)
    print("  - 3x Cameras (left, right, overhead)", flush=True)

    print("\n" + "="*60, flush=True)
    print("Simulation running. Close window to exit.", flush=True)
    print("="*60 + "\n", flush=True)

    step = 0
    while simulation_app.is_running():
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        step += 1
        if step % 600 == 0:
            # Get robot positions
            left_arm = scene["robot_left"]
            right_arm = scene["robot_right"]

            left_ee_idx = left_arm.find_bodies("panda_hand")[0][0]
            right_ee_idx = right_arm.find_bodies("panda_hand")[0][0]

            left_pos = left_arm.data.body_pos_w[0, left_ee_idx].cpu().numpy()
            right_pos = right_arm.data.body_pos_w[0, right_ee_idx].cpu().numpy()

            print(f"[Step {step}]", flush=True)
            print(f"  Left EE:  ({left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f})", flush=True)
            print(f"  Right EE: ({right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f})", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
