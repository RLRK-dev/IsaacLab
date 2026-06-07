#!/usr/bin/env python3
"""
Y字フック + ケーブル（ロボットが掴める長さ）v4
Cable runs in Y direction (between robot arms), ~40cm total length
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

import numpy as np
import time
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

import isaaclab.sim as sim_utils
from thread_isaac_lab.configs.task_config import PHYSICS_DT


def create_y_hook_usd(base_path, hook_base_pos, stem_length=0.08, arm_length=0.05,
                       arm_angle=45.0, radius=0.008, color=(0.3, 0.6, 1.0)):
    """Create Y-hook using USD."""
    stage = omni.usd.get_context().get_stage()

    hook_root = f"{base_path}/y_hook"
    UsdGeom.Xform.Define(stage, hook_root)

    angle_rad = np.radians(arm_angle)
    stem_top_z = hook_base_pos[2] + stem_length
    arm_offset_x = (arm_length / 2) * np.sin(angle_rad)
    arm_offset_z = (arm_length / 2) * np.cos(angle_rad)

    # Stem
    stem_path = f"{hook_root}/stem"
    stem = UsdGeom.Cylinder.Define(stage, stem_path)
    stem.GetRadiusAttr().Set(radius)
    stem.GetHeightAttr().Set(stem_length)
    stem.GetAxisAttr().Set("Z")

    stem_xform = UsdGeom.Xformable(stem)
    stem_xform.AddTranslateOp().Set(Gf.Vec3d(
        hook_base_pos[0], hook_base_pos[1], hook_base_pos[2] + stem_length / 2
    ))

    UsdPhysics.RigidBodyAPI.Apply(stem.GetPrim())
    stem.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(stem.GetPrim())
    stem.GetDisplayColorAttr().Set([color])

    # Left arm
    left_path = f"{hook_root}/arm_left"
    left_arm = UsdGeom.Cylinder.Define(stage, left_path)
    left_arm.GetRadiusAttr().Set(radius)
    left_arm.GetHeightAttr().Set(arm_length)
    left_arm.GetAxisAttr().Set("Z")

    left_xform = UsdGeom.Xformable(left_arm)
    left_xform.AddTranslateOp().Set(Gf.Vec3d(
        hook_base_pos[0] - arm_offset_x, hook_base_pos[1], stem_top_z + arm_offset_z
    ))
    left_xform.AddRotateYOp().Set(-arm_angle)

    UsdPhysics.RigidBodyAPI.Apply(left_arm.GetPrim())
    left_arm.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(left_arm.GetPrim())
    left_arm.GetDisplayColorAttr().Set([color])

    # Right arm
    right_path = f"{hook_root}/arm_right"
    right_arm = UsdGeom.Cylinder.Define(stage, right_path)
    right_arm.GetRadiusAttr().Set(radius)
    right_arm.GetHeightAttr().Set(arm_length)
    right_arm.GetAxisAttr().Set("Z")

    right_xform = UsdGeom.Xformable(right_arm)
    right_xform.AddTranslateOp().Set(Gf.Vec3d(
        hook_base_pos[0] + arm_offset_x, hook_base_pos[1], stem_top_z + arm_offset_z
    ))
    right_xform.AddRotateYOp().Set(arm_angle)

    UsdPhysics.RigidBodyAPI.Apply(right_arm.GetPrim())
    right_arm.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(right_arm.GetPrim())
    right_arm.GetDisplayColorAttr().Set([color])

    v_valley_pos = np.array([hook_base_pos[0], hook_base_pos[1], stem_top_z])

    print(f"[Y-Hook] Created at {hook_base_pos}")
    print(f"  V-valley at z={stem_top_z:.3f}m")

    return v_valley_pos


def create_long_cable_on_v(base_path, v_valley_pos, table_z, num_segments=24,
                            cable_total_length=0.40, segment_radius=0.006,
                            color=(1.0, 0.5, 0.0)):
    """
    Create long cable (~40cm) that robots can grasp.
    Cable runs in Y direction (between the two robot arms).
    Center draped over Y-hook V, ends hang down to table level.
    """
    stage = omni.usd.get_context().get_stage()

    cable_root = f"{base_path}/cable_goal"
    UsdGeom.Xform.Define(stage, cable_root)

    segment_paths = []

    for i in range(num_segments):
        t = i / (num_segments - 1)  # 0 to 1

        # Y direction: from left robot (-Y) to right robot (+Y)
        y = v_valley_pos[1] + (t - 0.5) * cable_total_length

        # X: at hook center
        x = v_valley_pos[0]

        # Z: catenary-like curve
        # Center at V-valley, ends hang down toward table
        dist_from_center = abs(t - 0.5) * 2  # 0 at center, 1 at ends

        if dist_from_center < 0.2:
            # Center: at V-valley height
            z = v_valley_pos[2] + 0.01
        elif dist_from_center < 0.5:
            # Rising over Y-hook arms
            rise = (dist_from_center - 0.2) / 0.3
            z = v_valley_pos[2] + 0.01 + rise * 0.03
        else:
            # Falling down toward table
            fall = (dist_from_center - 0.5) / 0.5
            peak_z = v_valley_pos[2] + 0.04
            end_z = table_z + 0.03  # 3cm above table
            z = peak_z - fall * (peak_z - end_z)

        seg_pos = Gf.Vec3d(x, y, z)

        seg_path = f"{cable_root}/seg_{i:02d}"
        sphere = UsdGeom.Sphere.Define(stage, seg_path)
        sphere.GetRadiusAttr().Set(segment_radius)

        xform = UsdGeom.Xformable(sphere)
        xform.AddTranslateOp().Set(seg_pos)

        UsdPhysics.RigidBodyAPI.Apply(sphere.GetPrim())
        sphere.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
        UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
        sphere.GetDisplayColorAttr().Set([color])

        segment_paths.append(seg_path)

    y_min = v_valley_pos[1] - cable_total_length / 2
    y_max = v_valley_pos[1] + cable_total_length / 2

    print(f"[Cable] {num_segments} segments, ~{cable_total_length*100:.0f}cm total")
    print(f"  Y range: {y_min:.2f}m to {y_max:.2f}m")
    print(f"  Ends at z ≈ {table_z + 0.03:.2f}m (robot grasp height)")

    return segment_paths


def create_table_usd(base_path, pos, size=(0.6, 0.8, 0.03), color=(0.85, 0.8, 0.7)):
    """Create table."""
    stage = omni.usd.get_context().get_stage()

    table_path = f"{base_path}/table"
    cube = UsdGeom.Cube.Define(stage, table_path)

    xform = UsdGeom.Xformable(cube)
    xform.AddTranslateOp().Set(Gf.Vec3d(pos[0], pos[1], pos[2]))
    xform.AddScaleOp().Set(Gf.Vec3f(size[0], size[1], size[2]))

    UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
    cube.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    cube.GetDisplayColorAttr().Set([color])

    print(f"[Table] Created at {pos}, size {size}")

    return table_path


def main():
    print("\n" + "=" * 60)
    print("Y-HOOK GOAL STATE v4")
    print("Long cable (~40cm) for robot grasping")
    print("Cable runs in Y direction (between robot arms)")
    print("=" * 60)

    # Setup
    print("\n[Status] Setting up simulation...")
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)

    # Camera view from side
    sim.set_camera_view(
        eye=(1.0, -0.5, 0.9),
        target=(0.5, 0.0, 0.55)
    )

    # Ground
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/ground", ground_cfg)

    # Light
    light_cfg = sim_utils.DomeLightCfg(intensity=1500.0)
    light_cfg.func("/World/DomeLight", light_cfg)

    base_path = "/World/envs/env_0"

    # Table
    print("[Status] Creating table...")
    table_z = 0.50
    create_table_usd(base_path, (0.5, 0.0, table_z))

    # Y-Hook
    print("[Status] Creating Y-hook...")
    hook_base_pos = np.array([0.5, 0.0, table_z + 0.015])
    v_valley_pos = create_y_hook_usd(
        base_path,
        hook_base_pos,
        stem_length=0.08,
        arm_length=0.05,
        arm_angle=45.0,
        radius=0.008,
        color=(0.3, 0.6, 1.0)
    )

    # Long cable
    print("[Status] Creating cable...")
    create_long_cable_on_v(
        base_path,
        v_valley_pos,
        table_z,
        num_segments=24,
        cable_total_length=0.40,
        segment_radius=0.006,
        color=(1.0, 0.5, 0.0)
    )

    # Reset
    print("[Status] Starting simulation...")
    sim.reset()

    print("\n" + "=" * 60)
    print("GOAL STATE v4 DISPLAYED!")
    print("")
    print("Top view:")
    print("")
    print("  [Left Robot]")
    print("       |")
    print("       |  ← Cable end (Y ≈ -0.2m)")
    print("       |")
    print("     ╲ | ╱   ← Y-hook")
    print("      ╲|╱")
    print("       |")
    print("       |  ← Cable end (Y ≈ +0.2m)")
    print("       |")
    print("  [Right Robot]")
    print("")
    print("Cable: 40cm total, ends at grasp height")
    print("")
    print("Close window to exit.")
    print("=" * 60 + "\n")

    # Run
    step = 0
    while simulation_app.is_running():
        sim.step()
        step += 1

        if step % 1200 == 0:
            print(f"[Step {step}] Running...")


if __name__ == "__main__":
    main()
    simulation_app.close()
