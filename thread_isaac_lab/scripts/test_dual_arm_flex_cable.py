#!/usr/bin/env python3
"""
Test Dual Arm with Flexible Cable
==================================

Dual Franka arms with joint-connected flexible cable.
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
from isaaclab.assets import Articulation, RigidObject
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils import configclass

# Import configurations
from envs.dual_arm_cfg import (
    LeftFrankaCfg,
    RightFrankaCfg,
    DualArmTableCfg,
    TABLE_HEIGHT,
)
from envs.flexible_cable_utils import create_flexible_cable, create_l_hook
from thread_isaac_lab.configs.task_config import PHYSICS_DT


@configclass
class DualArmFlexCableSceneCfg(InteractiveSceneCfg):
    """Dual arm scene with flexible cable added dynamically."""

    num_envs = 1
    env_spacing = 3.0

    # Robots
    robot_left: LeftFrankaCfg = LeftFrankaCfg()
    robot_right: RightFrankaCfg = RightFrankaCfg()

    # Table
    table: DualArmTableCfg = DualArmTableCfg()


def main():
    print("\n" + "="*60, flush=True)
    print("DUAL ARM WITH FLEXIBLE CABLE TEST", flush=True)
    print("="*60, flush=True)

    # Setup simulation
    print("\n[Status] Setting up simulation...", flush=True)
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(1.2, -0.8, 1.2),
        target=(0.4, 0.0, 0.75)
    )
    print("[Status] Simulation context created", flush=True)

    # Spawn ground plane
    print("[Status] Spawning ground plane...", flush=True)
    ground_cfg = sim_utils.GroundPlaneCfg(size=(100.0, 100.0))
    ground_cfg.func("/World/ground", ground_cfg)

    # Spawn dome light
    print("[Status] Spawning dome light...", flush=True)
    light_cfg = sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0))
    light_cfg.func("/World/DomeLight", light_cfg)

    # Create scene with robots and table
    print("[Status] Creating scene (robots + table)...", flush=True)
    cfg = DualArmFlexCableSceneCfg()
    scene = InteractiveScene(cfg)
    print("[Status] Scene created", flush=True)

    # Add flexible cable with joints
    print("[Status] Adding flexible cable with joints...", flush=True)
    cable_segments = create_flexible_cable(
        base_path="/World/envs/env_0",
        cable_name="flexible_cable",
        start_pos=(0.30, 0.0, TABLE_HEIGHT + 0.02),  # On table
        num_segments=10,
        segment_length=0.03,
        segment_radius=0.006,
        color=(1.0, 0.4, 0.0),  # Orange
    )
    print(f"[Status] Created {len(cable_segments)} cable segments", flush=True)

    # Add L-hook
    print("[Status] Adding L-hook...", flush=True)
    create_l_hook(
        base_path="/World/envs/env_0",
        hook_name="hook",
        position=(0.55, 0.0, TABLE_HEIGHT + 0.05),  # Above table
        vertical_length=0.10,
        horizontal_length=0.05,
        radius=0.006,
        color=(0.2, 0.4, 0.8),  # Blue
    )
    print("[Status] L-hook created", flush=True)

    # Start simulation
    print("[Status] Starting simulation...", flush=True)
    sim.reset()
    print("[Status] Simulation started!", flush=True)

    print("\n[Scene Summary]", flush=True)
    print("  - 2x Franka Panda robots (left/right)", flush=True)
    print("  - Table workspace", flush=True)
    print("  - 10-segment flexible cable (orange)", flush=True)
    print("  - L-shaped hook (blue)", flush=True)

    print("\n" + "="*60, flush=True)
    print("Simulation running. Close window to exit.", flush=True)
    print("="*60 + "\n", flush=True)

    step = 0
    while simulation_app.is_running():
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        step += 1
        if step % 600 == 0:  # Every 5 seconds at 120Hz
            # Get robot end-effector positions
            left_arm = scene["robot_left"]
            right_arm = scene["robot_right"]

            left_ee_idx = left_arm.find_bodies("panda_hand")[0][0]
            right_ee_idx = right_arm.find_bodies("panda_hand")[0][0]

            left_ee_pos = left_arm.data.body_pos_w[0, left_ee_idx].cpu().numpy()
            right_ee_pos = right_arm.data.body_pos_w[0, right_ee_idx].cpu().numpy()

            print(f"[Step {step}]", flush=True)
            print(f"  Left EE:  ({left_ee_pos[0]:.3f}, {left_ee_pos[1]:.3f}, {left_ee_pos[2]:.3f})", flush=True)
            print(f"  Right EE: ({right_ee_pos[0]:.3f}, {right_ee_pos[1]:.3f}, {right_ee_pos[2]:.3f})", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
