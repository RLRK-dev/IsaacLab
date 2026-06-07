#!/usr/bin/env python3
"""
Create SphericalJoint Cable USD v16_halfseg - Half Segment Count
================================================================

v16_halfseg: Reduced segment count for PhysX stability (H240)
- Based on v16_b0 parameters
- Reduced segments: 20 → 10
- Increased segment length: 3cm → 6cm (maintain 60cm total)
- Damping: 60.0 (standard, not B0's 80.0)

Purpose: Reduce PhysX computational load to prevent Phase 3 hang
Evidence: EP-H240-B (H239 diagnostic showed cable causes Phase 3 hang)
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Create SphericalJoint Cable USD v16_halfseg")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdGeom, UsdPhysics, Gf, Sdf, PhysxSchema
import os

# Cable parameters (H240: half segment count)
NUM_SEGMENTS = 10          # Reduced from 20 to 10 (50% reduction)
SEGMENT_LENGTH = 0.06      # 6cm per segment (doubled to maintain 60cm total)
SEGMENT_RADIUS = 0.005     # 5mm radius (unchanged)
TOTAL_LENGTH = NUM_SEGMENTS * SEGMENT_LENGTH  # 60cm total (unchanged)

# Mass and joint parameters (unchanged from v15/v16)
SEGMENT_MASS = 0.1         # 100g per segment
CONE_ANGLE_LIMIT = 30.0    # degrees
SOLVER_POS_ITER = 128      # Keep high solver iterations
SOLVER_VEL_ITER = 32

# Damping - standard values (not B0's elevated values)
LINEAR_DAMPING = 60.0      # Standard (v15 level)
ANGULAR_DAMPING = 60.0     # Standard (v15 level)

OUTPUT_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v16_halfseg.usd"


def create_cable_usd(output_path: str):
    """Create a half-segment cable USD for reduced PhysX load."""

    print("=" * 60)
    print("Creating SphericalJoint Cable USD v16_halfseg (H240)")
    print("=" * 60)
    print(f"  Segments: {NUM_SEGMENTS} (reduced from 20)")
    print(f"  Segment length: {SEGMENT_LENGTH * 100:.1f} cm (doubled from 3cm)")
    print(f"  Segment radius: {SEGMENT_RADIUS * 1000:.1f} mm")
    print(f"  Segment mass: {SEGMENT_MASS * 1000:.0f} g")
    print(f"  Total cable mass: {SEGMENT_MASS * NUM_SEGMENTS * 1000:.0f} g")
    print(f"  Cone angle limit: {CONE_ANGLE_LIMIT}°")
    print(f"  Solver iterations: pos={SOLVER_POS_ITER}, vel={SOLVER_VEL_ITER}")
    print(f"  Linear damping: {LINEAR_DAMPING}")
    print(f"  Angular damping: {ANGULAR_DAMPING}")
    print(f"  Total length: {TOTAL_LENGTH * 100:.1f} cm")
    print()
    print(f"  Output: {output_path}")
    print()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"  Removed existing file: {output_path}")

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    cable_prim = stage.DefinePrim("/Cable", "Xform")
    stage.SetDefaultPrim(cable_prim)

    UsdPhysics.ArticulationRootAPI.Apply(cable_prim)

    physx_art = PhysxSchema.PhysxArticulationAPI.Apply(cable_prim)
    physx_art.GetEnabledSelfCollisionsAttr().Set(False)
    physx_art.GetSolverPositionIterationCountAttr().Set(SOLVER_POS_ITER)
    physx_art.GetSolverVelocityIterationCountAttr().Set(SOLVER_VEL_ITER)

    prev_path = None

    for i in range(NUM_SEGMENTS):
        seg_name = f"seg_{i}"
        seg_path = f"/Cable/{seg_name}"

        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(SEGMENT_RADIUS)
        capsule.GetHeightAttr().Set(SEGMENT_LENGTH)
        capsule.GetAxisAttr().Set("Z")

        # Orange color for v16_halfseg (distinct from other versions)
        capsule.GetDisplayColorAttr().Set([(0.9, 0.5, 0.2)])

        xform = UsdGeom.Xformable(capsule)
        translate_op = xform.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(0, 0, i * SEGMENT_LENGTH))

        rigid_api = UsdPhysics.RigidBodyAPI.Apply(capsule.GetPrim())

        physx_rigid = PhysxSchema.PhysxRigidBodyAPI.Apply(capsule.GetPrim())
        physx_rigid.GetLinearDampingAttr().Set(LINEAR_DAMPING)
        physx_rigid.GetAngularDampingAttr().Set(ANGULAR_DAMPING)
        physx_rigid.GetEnableGyroscopicForcesAttr().Set(True)

        mass_api = UsdPhysics.MassAPI.Apply(capsule.GetPrim())
        mass_api.GetMassAttr().Set(SEGMENT_MASS)

        UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())

        if prev_path is not None:
            joint_name = f"joint_{i-1}_{i}"
            joint_path = f"/Cable/{joint_name}"

            joint = UsdPhysics.SphericalJoint.Define(stage, joint_path)
            joint.GetBody0Rel().SetTargets([Sdf.Path(prev_path)])
            joint.GetBody1Rel().SetTargets([Sdf.Path(seg_path)])
            joint.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, SEGMENT_LENGTH / 2))
            joint.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -SEGMENT_LENGTH / 2))
            joint.GetConeAngle0LimitAttr().Set(CONE_ANGLE_LIMIT)
            joint.GetConeAngle1LimitAttr().Set(CONE_ANGLE_LIMIT)

            PhysxSchema.PhysxJointAPI.Apply(joint.GetPrim())

        prev_path = seg_path

    print(f"  Created {NUM_SEGMENTS} segments with {NUM_SEGMENTS - 1} SphericalJoints")

    stage.Save()

    print()
    print(f"Successfully created: {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    try:
        create_cable_usd(OUTPUT_PATH)
    finally:
        simulation_app.close()
