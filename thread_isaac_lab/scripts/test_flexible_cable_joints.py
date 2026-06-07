#!/usr/bin/env python3
"""
Test Flexible Cable with Joint Connections
===========================================

Cable segments connected by D6Joints for realistic flexibility.
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
from isaaclab.sim import SimulationContext
from thread_isaac_lab.configs.task_config import PHYSICS_DT

# Cable parameters
NUM_SEGMENTS = 10
SEGMENT_LENGTH = 0.03  # 3cm per segment
SEGMENT_RADIUS = 0.006  # 6mm radius
SEGMENT_MASS = 0.003    # 3g per segment

# Hook parameters
HOOK_VERTICAL = 0.08
HOOK_HORIZONTAL = 0.04
HOOK_RADIUS = 0.005


def create_cable_with_joints():
    """Create cable segments connected by D6 joints"""
    from pxr import UsdGeom, UsdPhysics, Gf, Sdf
    import omni.usd

    stage = omni.usd.get_context().get_stage()

    # Create cable root
    cable_root = UsdGeom.Xform.Define(stage, "/World/cable")

    prev_prim_path = None

    for i in range(NUM_SEGMENTS):
        seg_path = f"/World/cable/seg_{i:02d}"
        x_pos = 0.4 + i * SEGMENT_LENGTH

        # Create capsule
        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(SEGMENT_RADIUS)
        capsule.GetHeightAttr().Set(SEGMENT_LENGTH)
        capsule.GetAxisAttr().Set("X")

        # Set position
        xform = UsdGeom.Xformable(capsule)
        xform.AddTranslateOp().Set(Gf.Vec3d(x_pos, 0, 0.5))

        # Add rigid body physics
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(capsule.GetPrim())

        # Add mass
        mass_api = UsdPhysics.MassAPI.Apply(capsule.GetPrim())
        mass_api.GetMassAttr().Set(SEGMENT_MASS)

        # Add collision
        UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())

        # Set color (orange)
        capsule.GetDisplayColorAttr().Set([(1.0, 0.4, 0.0)])

        # Create D6 joint to previous segment
        if prev_prim_path is not None:
            joint_path = f"/World/cable/joint_{i-1:02d}_{i:02d}"
            joint = UsdPhysics.Joint.Define(stage, joint_path)

            # Connect bodies
            joint.GetBody0Rel().SetTargets([Sdf.Path(prev_prim_path)])
            joint.GetBody1Rel().SetTargets([Sdf.Path(seg_path)])

            # Joint positions (at the connection point)
            joint.GetLocalPos0Attr().Set(Gf.Vec3f(SEGMENT_LENGTH/2, 0, 0))
            joint.GetLocalPos1Attr().Set(Gf.Vec3f(-SEGMENT_LENGTH/2, 0, 0))

            # Add D6 joint for flexibility
            d6_joint = UsdPhysics.LimitAPI.Apply(joint.GetPrim(), "rotX")
            d6_joint.GetLowAttr().Set(-30.0)
            d6_joint.GetHighAttr().Set(30.0)

            d6_joint_y = UsdPhysics.LimitAPI.Apply(joint.GetPrim(), "rotY")
            d6_joint_y.GetLowAttr().Set(-30.0)
            d6_joint_y.GetHighAttr().Set(30.0)

            d6_joint_z = UsdPhysics.LimitAPI.Apply(joint.GetPrim(), "rotZ")
            d6_joint_z.GetLowAttr().Set(-30.0)
            d6_joint_z.GetHighAttr().Set(30.0)

        prev_prim_path = seg_path

    print(f"[Cable] Created {NUM_SEGMENTS} segments with joints", flush=True)
    return cable_root


def create_l_hook():
    """Create L-shaped hook"""
    from pxr import UsdGeom, UsdPhysics, Gf
    import omni.usd

    stage = omni.usd.get_context().get_stage()

    # Vertical part
    vert_path = "/World/hook_vertical"
    vert = UsdGeom.Cylinder.Define(stage, vert_path)
    vert.GetRadiusAttr().Set(HOOK_RADIUS)
    vert.GetHeightAttr().Set(HOOK_VERTICAL)
    vert.GetAxisAttr().Set("Z")

    xform_v = UsdGeom.Xformable(vert)
    xform_v.AddTranslateOp().Set(Gf.Vec3d(0.7, 0.0, 0.5 + HOOK_VERTICAL/2))

    rigid_v = UsdPhysics.RigidBodyAPI.Apply(vert.GetPrim())
    rigid_v.GetKinematicEnabledAttr().Set(True)
    UsdPhysics.CollisionAPI.Apply(vert.GetPrim())
    vert.GetDisplayColorAttr().Set([(0.2, 0.4, 0.8)])

    # Horizontal part
    horiz_path = "/World/hook_horizontal"
    horiz = UsdGeom.Cylinder.Define(stage, horiz_path)
    horiz.GetRadiusAttr().Set(HOOK_RADIUS)
    horiz.GetHeightAttr().Set(HOOK_HORIZONTAL)
    horiz.GetAxisAttr().Set("Y")

    xform_h = UsdGeom.Xformable(horiz)
    xform_h.AddTranslateOp().Set(Gf.Vec3d(0.7, 0.0, 0.5 + HOOK_VERTICAL))

    rigid_h = UsdPhysics.RigidBodyAPI.Apply(horiz.GetPrim())
    rigid_h.GetKinematicEnabledAttr().Set(True)
    UsdPhysics.CollisionAPI.Apply(horiz.GetPrim())
    horiz.GetDisplayColorAttr().Set([(0.2, 0.4, 0.8)])

    print("[Hook] Created L-shape hook", flush=True)


def main():
    print("\n" + "="*50, flush=True)
    print("FLEXIBLE CABLE WITH JOINTS TEST", flush=True)
    print("="*50, flush=True)

    # Setup simulation
    print("\n[Status] Setting up simulation...", flush=True)
    sim_cfg = sim_utils.SimulationCfg(device="cuda:0", dt=PHYSICS_DT)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(
        eye=(1.0, -0.5, 1.0),
        target=(0.5, 0.0, 0.5)
    )

    # Spawn ground plane
    print("[Status] Spawning ground plane...", flush=True)
    ground_cfg = sim_utils.GroundPlaneCfg(size=(10.0, 10.0))
    ground_cfg.func("/World/ground", ground_cfg)

    # Spawn dome light
    print("[Status] Spawning dome light...", flush=True)
    light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(1.0, 1.0, 1.0))
    light_cfg.func("/World/dome_light", light_cfg)

    # Create cable with joints
    print("[Status] Creating cable with joints...", flush=True)
    create_cable_with_joints()

    # Create L-hook
    print("[Status] Creating L-hook...", flush=True)
    create_l_hook()

    print("[Status] Starting simulation...", flush=True)
    sim.reset()
    print("[Status] Simulation started!", flush=True)

    print(f"\n[Cable] {NUM_SEGMENTS} segments connected by joints", flush=True)
    print(f"  Total length: {NUM_SEGMENTS * SEGMENT_LENGTH * 100:.0f} cm", flush=True)
    print(f"  Joint flexibility: ±30 degrees", flush=True)

    print("\n" + "="*50, flush=True)
    print("Simulation running. Close window to exit.", flush=True)
    print("="*50 + "\n", flush=True)

    step = 0
    while simulation_app.is_running():
        sim.step()
        step += 1

        if step % 500 == 0:
            print(f"[Step {step}] Running...", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
