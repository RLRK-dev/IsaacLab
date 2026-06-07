#!/usr/bin/env python3
"""
Goal State Visualization
========================
Displays flexible cable hanging on hook (goal state for the task).
"""
import argparse
import sys
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=1)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# GUI display (not headless)
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch
import time
import omni.usd
from pxr import UsdGeom, Gf

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from envs.dual_arm_flex_env_cfg import (
    DualArmFlexCableSceneCfg,
    NUM_CABLE_SEGMENTS,
    CABLE_SEGMENT_LENGTH,
    TABLE_HEIGHT,
)
from envs.flexible_cable_utils import create_flexible_cable
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def set_cable_on_hook(stage, cable_paths, hook_pos):
    """Position cable segments in U-shape around hook.

    Args:
        stage: USD stage
        cable_paths: List of cable segment prim paths
        hook_pos: Hook position (x, y, z)
    """
    print(f"\n[Goal State] Positioning cable on hook at {hook_pos}")

    num_segments = len(cable_paths)

    # U-shape configuration around hook
    # Cable hangs down on both sides of the hook
    for i, path in enumerate(cable_paths):
        prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            print(f"  Warning: Segment {i} not found at {path}")
            continue

        # Calculate U-shape position
        # Segments 0-4: left side (descending)
        # Segment 5: bottom of U (at hook)
        # Segments 6-9: right side (ascending)

        progress = i / (num_segments - 1)  # 0 to 1

        if i < num_segments // 2:
            # Left side - descending
            x_offset = -0.08 + i * 0.015
            y_offset = -0.02
            z_offset = 0.12 - i * 0.025
        elif i == num_segments // 2:
            # Bottom of U - at hook level
            x_offset = 0.0
            y_offset = 0.0
            z_offset = 0.0
        else:
            # Right side - ascending
            mirror_i = num_segments - 1 - i
            x_offset = -0.08 + mirror_i * 0.015
            y_offset = 0.02
            z_offset = 0.12 - mirror_i * 0.025

        new_pos = Gf.Vec3d(
            hook_pos[0] + x_offset,
            hook_pos[1] + y_offset,
            hook_pos[2] + z_offset
        )

        # Set position via xform
        xform = UsdGeom.Xformable(prim)
        xform_ops = xform.GetOrderedXformOps()

        # Clear existing transforms and set new position
        xform.ClearXformOpOrder()
        translate_op = xform.AddTranslateOp()
        translate_op.Set(new_pos)

        print(f"  Segment {i}: ({new_pos[0]:.3f}, {new_pos[1]:.3f}, {new_pos[2]:.3f})")


def main():
    print("\n" + "="*60)
    print("GOAL STATE VISUALIZATION")
    print("Flexible cable hanging on hook")
    print("="*60)

    # Setup simulation
    print("\n[Status] Setting up simulation...")
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(1.2, -0.8, 1.2),
        target=(0.6, 0.0, 0.85)
    )

    # Create scene
    print("[Status] Creating scene...")
    cfg = DualArmFlexCableSceneCfg()
    cfg.num_envs = args_cli.num_envs
    scene = InteractiveScene(cfg)

    # Add flexible cable
    print("[Status] Adding flexible cable...")
    cable_paths = create_flexible_cable(
        base_path="/World/envs/env_0",
        cable_name="flexible_cable",
        start_pos=(0.35, 0.0, TABLE_HEIGHT + 0.02),
        num_segments=NUM_CABLE_SEGMENTS,
        segment_length=CABLE_SEGMENT_LENGTH,
        segment_radius=0.006,
        color=(1.0, 0.4, 0.0),  # Orange
    )
    print(f"[Status] Created {len(cable_paths)} cable segments")

    # Get stage for USD manipulation
    stage = omni.usd.get_context().get_stage()

    # Start simulation
    print("[Status] Starting simulation...")
    sim.reset()

    # Get hook position
    hook = scene["hook_vertical"]
    hook_pos_tensor = hook.data.root_pos_w[0]
    hook_pos = (
        float(hook_pos_tensor[0].cpu()),
        float(hook_pos_tensor[1].cpu()),
        float(hook_pos_tensor[2].cpu()) + 0.05  # Slightly above hook base
    )

    print(f"\n[Info] Hook position: {hook_pos}")

    # Position cable on hook (goal state)
    set_cable_on_hook(stage, cable_paths, hook_pos)

    # Let physics settle
    print("\n[Status] Letting physics settle...")
    for _ in range(120):  # 1 second at 120Hz
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

    print("\n" + "="*60)
    print("GOAL STATE DISPLAYED!")
    print("This shows the cable successfully hanging on the hook.")
    print("")
    print("Scene contents:")
    print("  - 2x Franka Panda robots (dual arm)")
    print("  - Table (80x100cm)")
    print(f"  - {NUM_CABLE_SEGMENTS}-segment flexible cable (orange)")
    print("  - L-shaped hook (blue)")
    print("")
    print("Close window to exit.")
    print("="*60 + "\n")

    # Keep running for visualization
    step = 0
    while simulation_app.is_running():
        scene.write_data_to_sim()
        sim.step()
        scene.update(sim.get_physics_dt())

        step += 1
        if step % 600 == 0:
            # Print status every 5 seconds
            left_arm = scene["robot_left"]
            right_arm = scene["robot_right"]

            left_ee_idx = left_arm.find_bodies("panda_hand")[0][0]
            right_ee_idx = right_arm.find_bodies("panda_hand")[0][0]

            left_pos = left_arm.data.body_pos_w[0, left_ee_idx].cpu().numpy()
            right_pos = right_arm.data.body_pos_w[0, right_ee_idx].cpu().numpy()

            print(f"[Step {step}] Left EE: ({left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f}), "
                  f"Right EE: ({right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f})")


if __name__ == "__main__":
    main()
    simulation_app.close()
