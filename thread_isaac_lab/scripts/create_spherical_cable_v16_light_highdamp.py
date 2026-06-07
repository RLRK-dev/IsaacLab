#!/usr/bin/env python3
"""
Create SphericalJoint Cable USD v16 - Light + High Damping
============================================================

v16: Combines light mass (10g/seg) with high damping (40.0)

Rationale:
- v13 (10g/seg, damping=10): NaN at Step 32 - damping too low
- v14 (100g/seg, damping=40): Cycle 1 success, Cycle 2 NaN at Step 333 - mass ratio 71:1 too high
- v15 (100g/seg, damping=60): NaN at Step 31 - over-damped, made worse
- v16 (10g/seg, damping=40): Combines low mass ratio (7:1) with proven damping

PhysX Solver Limitation:
- Mass ratio > 10:1 causes convergence issues
- Current: 100g/seg / 14g gripper = 71:1 (7x over limit)
- v16: 10g/seg / 14g gripper = 7:1 (within limit)
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Create SphericalJoint Cable USD v16")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdGeom, UsdPhysics, Gf, Sdf, PhysxSchema
import os

# Cable parameters
NUM_SEGMENTS = 20
SEGMENT_LENGTH = 0.03  # 3cm per segment
SEGMENT_RADIUS = 0.005  # 5mm radius
TOTAL_LENGTH = NUM_SEGMENTS * SEGMENT_LENGTH  # 60cm total

# v16: Light mass + High damping
SEGMENT_MASS = 0.01  # 10g per segment (same as v13, 1/10 of v14)
CONE_ANGLE_LIMIT = 30.0  # degrees (same as v9_mid)
SOLVER_POS_ITER = 128  # Keep high solver iterations
SOLVER_VEL_ITER = 32

# HIGH DAMPING - same as v14
LINEAR_DAMPING = 40.0   # Same as v14 (proven stable with higher mass)
ANGULAR_DAMPING = 40.0  # Same as v14

OUTPUT_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v16_light_highdamp.usd"


def create_cable_usd(output_path: str):
    """Create a light + high-damping cable USD for maximum stability."""

    print("=" * 60)
    print("Creating SphericalJoint Cable USD v16 (Light + High Damping)")
    print("=" * 60)
    print(f"  Segments: {NUM_SEGMENTS}")
    print(f"  Segment length: {SEGMENT_LENGTH * 100:.1f} cm")
    print(f"  Segment radius: {SEGMENT_RADIUS * 1000:.1f} mm")
    print(f"  Segment mass: {SEGMENT_MASS * 1000:.0f} g (1/10 of v14)")
    print(f"  Total cable mass: {SEGMENT_MASS * NUM_SEGMENTS * 1000:.0f} g")
    print(f"  Mass ratio vs gripper (28g): {SEGMENT_MASS * 1000 / 14:.1f}:1")
    print(f"  Cone angle limit: {CONE_ANGLE_LIMIT}° (same as v9_mid)")
    print(f"  Solver iterations: pos={SOLVER_POS_ITER}, vel={SOLVER_VEL_ITER}")
    print(f"  Linear damping: {LINEAR_DAMPING} (same as v14)")
    print(f"  Angular damping: {ANGULAR_DAMPING} (same as v14)")
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

        # Cyan color for v16 (light + high damping)
        capsule.GetDisplayColorAttr().Set([(0.2, 0.8, 0.9)])

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
