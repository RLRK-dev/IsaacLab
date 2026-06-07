#!/usr/bin/env python3
"""
Create SphericalJoint Cable USD v4
==================================

v4: Ultra-high damping for stability
- 20 segments x 3cm = 60cm total (Y-axis layout)
- DriveAPI damping: 50.0 (50x higher than v3's 1.0)
- Solver iterations: 64/16 (doubled from v3)
- Mass: 50g per segment

Purpose: Fix cable drift issue where cable moves during arm approach.
"""

import argparse
from isaaclab.app import AppLauncher

# Parse arguments
parser = argparse.ArgumentParser(description="Create SphericalJoint Cable USD v4")
parser.add_argument("--damping", type=float, default=50.0, help="DriveAPI damping value")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True  # Force headless mode

# Launch Isaac Sim
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Now we can import pxr
from pxr import Usd, UsdGeom, UsdPhysics, Gf, Sdf, PhysxSchema
import os

# Cable parameters (same as v3)
NUM_SEGMENTS = 20
SEGMENT_LENGTH = 0.03  # 3cm per segment
SEGMENT_RADIUS = 0.005  # 5mm radius
TOTAL_LENGTH = NUM_SEGMENTS * SEGMENT_LENGTH  # 60cm total

# v4: Ultra-stable parameters
SEGMENT_MASS = 0.05  # 50g per segment
CONE_ANGLE_LIMIT = 30.0  # degrees
SOLVER_POS_ITER = 64  # 2x from v3's 32
SOLVER_VEL_ITER = 16  # 2x from v3's 8
JOINT_DAMPING = args_cli.damping  # DriveAPI damping (default 50.0, was 1.0 in v3)

OUTPUT_PATH = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v4.usd"


def create_spherical_cable_usd(output_path: str):
    """Create a flexible cable USD with SphericalJoints and high damping."""

    print("=" * 60)
    print("Creating SphericalJoint Cable USD v4 (Ultra-Stable)")
    print("=" * 60)
    print(f"  Segments: {NUM_SEGMENTS}")
    print(f"  Segment length: {SEGMENT_LENGTH * 100:.1f} cm")
    print(f"  Segment radius: {SEGMENT_RADIUS * 1000:.1f} mm")
    print(f"  Segment mass: {SEGMENT_MASS * 1000:.0f} g")
    print(f"  Cone angle limit: {CONE_ANGLE_LIMIT}°")
    print(f"  Solver iterations: pos={SOLVER_POS_ITER}, vel={SOLVER_VEL_ITER}")
    print(f"  DriveAPI damping: {JOINT_DAMPING}")
    print(f"  Total length: {TOTAL_LENGTH * 100:.1f} cm")
    print(f"  Output: {output_path}")
    print()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Remove existing file if present
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"  Removed existing file: {output_path}")

    # Create new stage
    stage = Usd.Stage.CreateNew(output_path)

    # Set up axis and units
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Create root Xform
    cable_prim = stage.DefinePrim("/Cable", "Xform")
    stage.SetDefaultPrim(cable_prim)

    # Apply ArticulationRootAPI to the root
    UsdPhysics.ArticulationRootAPI.Apply(cable_prim)

    # Apply PhysxArticulationAPI for better simulation
    physx_art = PhysxSchema.PhysxArticulationAPI.Apply(cable_prim)
    physx_art.GetEnabledSelfCollisionsAttr().Set(False)
    physx_art.GetSolverPositionIterationCountAttr().Set(SOLVER_POS_ITER)
    physx_art.GetSolverVelocityIterationCountAttr().Set(SOLVER_VEL_ITER)

    prev_path = None

    for i in range(NUM_SEGMENTS):
        seg_name = f"seg_{i}"
        seg_path = f"/Cable/{seg_name}"

        # Create capsule geometry
        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(SEGMENT_RADIUS)
        capsule.GetHeightAttr().Set(SEGMENT_LENGTH)
        capsule.GetAxisAttr().Set("Z")  # Cable extends along Z axis

        # Set color (orange for v4)
        capsule.GetDisplayColorAttr().Set([(1.0, 0.4, 0.0)])

        # Position the segment
        xform = UsdGeom.Xformable(capsule)
        translate_op = xform.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(0, 0, i * SEGMENT_LENGTH))

        # Apply RigidBodyAPI
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(capsule.GetPrim())

        # Apply MassAPI
        mass_api = UsdPhysics.MassAPI.Apply(capsule.GetPrim())
        mass_api.GetMassAttr().Set(SEGMENT_MASS)

        # Apply CollisionAPI
        UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())

        # Create SphericalJoint to connect to previous segment
        if prev_path is not None:
            joint_name = f"joint_{i-1}_{i}"
            joint_path = f"/Cable/{joint_name}"

            # Create SphericalJoint (ball-and-socket joint, 3 DOF rotation)
            joint = UsdPhysics.SphericalJoint.Define(stage, joint_path)

            # Connect bodies
            joint.GetBody0Rel().SetTargets([Sdf.Path(prev_path)])
            joint.GetBody1Rel().SetTargets([Sdf.Path(seg_path)])

            # Set local positions (at the ends of capsules)
            joint.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, SEGMENT_LENGTH / 2))
            joint.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -SEGMENT_LENGTH / 2))

            # Set rotation limits (cone angle in degrees)
            joint.GetConeAngle0LimitAttr().Set(CONE_ANGLE_LIMIT)
            joint.GetConeAngle1LimitAttr().Set(CONE_ANGLE_LIMIT)

            # Apply PhysxJointAPI for damping
            physx_joint = PhysxSchema.PhysxJointAPI.Apply(joint.GetPrim())

            # Apply DriveAPI for angular damping on the cone axis
            # For SphericalJoint, we use "rotX", "rotY", "rotZ" or "angular"
            # Using UsdPhysics.DriveAPI with "angular" for general angular damping
            drive_api = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "angular")
            drive_api.GetTypeAttr().Set("force")  # Force-based drive
            drive_api.GetDampingAttr().Set(JOINT_DAMPING)  # High damping
            drive_api.GetStiffnessAttr().Set(0.0)  # No spring, just damping

            # Also apply LimitAPI for additional constraint stability
            limit_api = PhysxSchema.PhysxLimitAPI.Apply(joint.GetPrim(), "cone")
            limit_api.GetStiffnessAttr().Set(0.0)
            limit_api.GetDampingAttr().Set(JOINT_DAMPING)  # Additional damping

        prev_path = seg_path

    # Print segment summary
    print(f"  Created {NUM_SEGMENTS} segments with {NUM_SEGMENTS - 1} SphericalJoints")

    # Save the stage
    stage.Save()

    print()
    print(f"Successfully created: {output_path}")
    print("=" * 60)

    return output_path


def verify_usd(usd_path: str):
    """Verify the created USD file."""
    print("\nVerifying USD file...")

    stage = Usd.Stage.Open(usd_path)
    if not stage:
        print("  ERROR: Could not open USD file")
        return False

    # Check for articulation root
    root = stage.GetDefaultPrim()
    has_articulation = root.HasAPI(UsdPhysics.ArticulationRootAPI)
    print(f"  ArticulationRootAPI: {'Yes' if has_articulation else 'No'}")

    # Count segments and joints
    segments = []
    joints = []

    for prim in stage.Traverse():
        if prim.GetTypeName() == "Capsule":
            segments.append(prim.GetPath())
        if "Joint" in prim.GetTypeName():
            joints.append(prim.GetPath())

    print(f"  Segments: {len(segments)}")
    print(f"  Joints: {len(joints)}")

    # Check joint types and damping
    spherical_count = 0
    drive_count = 0
    for joint_path in joints:
        joint_prim = stage.GetPrimAtPath(joint_path)
        if joint_prim.GetTypeName() == "PhysicsSphericalJoint":
            spherical_count += 1
            # Check DriveAPI
            if joint_prim.HasAPI(UsdPhysics.DriveAPI):
                drive_count += 1

    print(f"  SphericalJoints: {spherical_count}")
    print(f"  Joints with DriveAPI: {drive_count}")

    if spherical_count == NUM_SEGMENTS - 1:
        print("\n  [OK] All joints are SphericalJoints!")
        if drive_count == spherical_count:
            print(f"  [OK] All joints have DriveAPI damping = {JOINT_DAMPING}")
        return True
    else:
        print(f"\n  [WARN] Expected {NUM_SEGMENTS - 1} SphericalJoints")
        return False


if __name__ == "__main__":
    try:
        output = create_spherical_cable_usd(OUTPUT_PATH)
        verify_usd(output)
    finally:
        simulation_app.close()
