#!/usr/bin/env python3
"""
Y字フック + ケーブル（V字部分に挟まった状態）
Y-Hook with Cable draped over V-section (Goal State)
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
    """Create Y-hook using USD primitives."""
    stage = omni.usd.get_context().get_stage()

    hook_root = f"{base_path}/y_hook"
    UsdGeom.Xform.Define(stage, hook_root)

    angle_rad = np.radians(arm_angle)
    stem_top_z = hook_base_pos[2] + stem_length
    arm_offset_x = (arm_length / 2) * np.sin(angle_rad)
    arm_offset_z = (arm_length / 2) * np.cos(angle_rad)

    # Stem (vertical)
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

    # Left arm (angled)
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

    # Right arm (angled)
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

    # V-valley position (where cable sits)
    v_valley_pos = np.array([hook_base_pos[0], hook_base_pos[1], stem_top_z])

    print(f"[Y-Hook] Created at base={hook_base_pos}")
    print(f"  Stem: {stem_length}m, Arms: {arm_length}m @ {arm_angle}°")
    print(f"  V-valley at z={stem_top_z:.3f}m")

    return v_valley_pos


def create_cable_on_v(base_path, v_valley_pos, num_segments=12,
                      segment_length=0.018, segment_radius=0.005,
                      color=(1.0, 0.5, 0.0)):
    """Create cable segments draped over Y-hook V-section.

    Cable shape: U-curve with center at V-valley, ends hanging down
    """
    stage = omni.usd.get_context().get_stage()

    cable_root = f"{base_path}/cable_goal"
    UsdGeom.Xform.Define(stage, cable_root)

    segment_paths = []

    for i in range(num_segments):
        t = i / (num_segments - 1)  # 0 to 1

        # X position: spread from left to right
        x_offset = (t - 0.5) * 0.10  # -0.05 to +0.05

        # Z position: U-shape (center high in V, ends hanging down)
        # Parabola: highest at t=0.5 (center), lowest at ends
        z_parabola = -4 * (t - 0.5) ** 2  # 0 at center, -1 at ends
        z_offset = z_parabola * 0.04  # Scale: 4cm drop at ends

        seg_pos = Gf.Vec3d(
            v_valley_pos[0] + x_offset,
            v_valley_pos[1],
            v_valley_pos[2] + z_offset + 0.005  # Slightly above valley
        )

        seg_path = f"{cable_root}/seg_{i:02d}"
        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(segment_radius)
        capsule.GetHeightAttr().Set(segment_length)
        capsule.GetAxisAttr().Set("X")  # Horizontal along X

        xform = UsdGeom.Xformable(capsule)
        xform.AddTranslateOp().Set(seg_pos)

        # Make kinematic for visualization
        UsdPhysics.RigidBodyAPI.Apply(capsule.GetPrim())
        capsule.GetPrim().GetAttribute("physics:kinematicEnabled").Set(True)
        UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())
        capsule.GetDisplayColorAttr().Set([color])

        segment_paths.append(seg_path)

    print(f"[Cable] Created {num_segments} segments in U-shape over V-valley")

    return segment_paths


def create_table_usd(base_path, pos, size=(0.6, 0.8, 0.03), color=(0.85, 0.8, 0.7)):
    """Create table using USD."""
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

    print(f"[Table] Created at {pos}")

    return table_path


def main():
    print("\n" + "=" * 60)
    print("Y-HOOK GOAL STATE VISUALIZATION")
    print("Cable draped over Y-hook V-section")
    print("=" * 60)

    # Setup simulation
    print("\n[Status] Setting up simulation...")
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(0.9, -0.5, 0.9),
        target=(0.5, 0.0, 0.6)
    )

    # Ground plane
    print("[Status] Creating ground...")
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/ground", ground_cfg)

    # Dome light
    light_cfg = sim_utils.DomeLightCfg(intensity=1500.0)
    light_cfg.func("/World/DomeLight", light_cfg)

    base_path = "/World/envs/env_0"

    # Table
    print("[Status] Creating table...")
    table_pos = (0.5, 0.0, 0.50)
    create_table_usd(base_path, table_pos)

    # Y-Hook (on table)
    print("[Status] Creating Y-hook...")
    hook_base_pos = np.array([0.5, 0.0, 0.515])  # Just above table
    v_valley_pos = create_y_hook_usd(
        base_path,
        hook_base_pos,
        stem_length=0.08,
        arm_length=0.05,
        arm_angle=45.0,
        radius=0.008,
        color=(0.3, 0.6, 1.0)
    )

    # Cable on V-section
    print("[Status] Creating cable in goal position...")
    create_cable_on_v(
        base_path,
        v_valley_pos,
        num_segments=12,
        segment_length=0.018,
        segment_radius=0.005,
        color=(1.0, 0.5, 0.0)
    )

    # Reset simulation
    print("[Status] Starting simulation...")
    sim.reset()

    print("\n" + "=" * 60)
    print("GOAL STATE DISPLAYED!")
    print("")
    print("Structure:")
    print("     ╲   ╱  ← Y-hook arms (45°)")
    print("      ╲ ╱")
    print("   ~~~~●~~~~  ← Cable draped in V-valley")
    print("       │")
    print("       │      ← Y-hook stem")
    print("  ═════════   ← Table")
    print("")
    print("  Blue: Y-hook")
    print("  Orange: Cable (goal position)")
    print("")
    print("Close window to exit.")
    print("=" * 60 + "\n")

    # Run simulation
    step = 0
    while simulation_app.is_running():
        sim.step()
        step += 1

        if step % 1200 == 0:
            print(f"[Step {step}] Simulation running...")


if __name__ == "__main__":
    main()
    simulation_app.close()
