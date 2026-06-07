#!/usr/bin/env python3
"""
Create SphericalJoint Cable USD v17_highdamp - High Damping
===========================================================

v17_highdamp: Increased damping for PhysX solver convergence (H241)
- Based on v16_halfseg parameters (10 segments)
- Damping increased: 60.0 → 100.0 (+66%)
- All other parameters unchanged

Purpose: Improve PhysX solver convergence during lift phase
Evidence: LL-2026-01-30-HANG-001 (PhysX solver convergence issue)
          EP-H241-B (damping increase hypothesis)
"""

import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Create SphericalJoint Cable USD v17_highdamp")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Gf, Sdf, PhysxSchema
import os

# Cable parameters (same as v16_halfseg)
NUM_SEGMENTS = 10          # 10 segments (same as v16_halfseg)
SEGMENT_LENGTH = 0.06      # 6cm per segment
SEGMENT_RADIUS = 0.005     # 5mm radius
TOTAL_LENGTH = NUM_SEGMENTS * SEGMENT_LENGTH  # 60cm total

# Mass and joint parameters (unchanged)
SEGMENT_MASS = 0.1         # 100g per segment
CONE_ANGLE_LIMIT = 30.0    # degrees
SOLVER_POS_ITER = 128      # Keep high solver iterations
SOLVER_VEL_ITER = 32

# H241: Increased damping for PhysX solver convergence
LINEAR_DAMPING = 100.0     # Increased from 60.0 (+66%)
ANGULAR_DAMPING = 100.0    # Increased from 60.0 (+66%)

# Friction (from task_config.py CABLE_STATIC/DYNAMIC_FRICTION)
STATIC_FRICTION = 0.8    # v22i: reverted to baseline
DYNAMIC_FRICTION = 0.6   # v22i: reverted
RESTITUTION = 0.0

OUTPUT_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v17_highdamp.usd"


def create_cable_usd(output_path: str):
    """Create a high-damping cable USD for improved PhysX convergence."""

    print("=" * 60)
    print("Creating SphericalJoint Cable USD v17_highdamp (H241)")
    print("=" * 60)
    print(f"  Segments: {NUM_SEGMENTS}")
    print(f"  Segment length: {SEGMENT_LENGTH * 100:.1f} cm")
    print(f"  Segment radius: {SEGMENT_RADIUS * 1000:.1f} mm")
    print(f"  Segment mass: {SEGMENT_MASS * 1000:.0f} g")
    print(f"  Total cable mass: {SEGMENT_MASS * NUM_SEGMENTS * 1000:.0f} g")
    print(f"  Cone angle limit: {CONE_ANGLE_LIMIT}°")
    print(f"  Solver iterations: pos={SOLVER_POS_ITER}, vel={SOLVER_VEL_ITER}")
    print(f"  Linear damping: {LINEAR_DAMPING} (increased from 60.0)")
    print(f"  Angular damping: {ANGULAR_DAMPING} (increased from 60.0)")
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

    # PhysicsMaterial for cable segments (shared)
    mat_path = "/Cable/CableMaterial"
    mat_prim = UsdShade.Material.Define(stage, mat_path)
    phys_mat = UsdPhysics.MaterialAPI.Apply(mat_prim.GetPrim())
    phys_mat.GetStaticFrictionAttr().Set(STATIC_FRICTION)
    phys_mat.GetDynamicFrictionAttr().Set(DYNAMIC_FRICTION)
    phys_mat.GetRestitutionAttr().Set(RESTITUTION)
    print(f"  PhysicsMaterial: static={STATIC_FRICTION} dynamic={DYNAMIC_FRICTION} restitution={RESTITUTION}")

    prev_path = None

    for i in range(NUM_SEGMENTS):
        seg_name = f"seg_{i}"
        seg_path = f"/Cable/{seg_name}"

        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(SEGMENT_RADIUS)
        capsule.GetHeightAttr().Set(SEGMENT_LENGTH)
        capsule.GetAxisAttr().Set("Z")

        # Yellow color for v17_highdamp (distinct from v16_halfseg orange)
        capsule.GetDisplayColorAttr().Set([(0.9, 0.9, 0.2)])

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

        # Bind PhysicsMaterial to segment
        bind_api = UsdShade.MaterialBindingAPI.Apply(capsule.GetPrim())
        bind_api.Bind(mat_prim, UsdShade.Tokens.weakerThanDescendants, "physics")

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
