#!/usr/bin/env python3
"""
Flexible Cable Utilities
========================

Functions to create joint-connected cable segments for realistic cable simulation.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf, Sdf


# Cable parameters
DEFAULT_NUM_SEGMENTS = 20
DEFAULT_SEGMENT_LENGTH = 0.03  # 3cm
DEFAULT_SEGMENT_RADIUS = 0.006  # 6mm
DEFAULT_SEGMENT_MASS = 0.003   # 3g
DEFAULT_JOINT_ANGLE_LIMIT = 30.0  # degrees


def create_flexible_cable(
    base_path: str = "/World/envs/env_0",
    cable_name: str = "cable",
    start_pos: tuple = (0.35, 0.0, 0.77),
    num_segments: int = DEFAULT_NUM_SEGMENTS,
    segment_length: float = DEFAULT_SEGMENT_LENGTH,
    segment_radius: float = DEFAULT_SEGMENT_RADIUS,
    segment_mass: float = DEFAULT_SEGMENT_MASS,
    joint_angle_limit: float = DEFAULT_JOINT_ANGLE_LIMIT,
    color: tuple = (1.0, 0.4, 0.0),  # Orange
):
    """
    Create a flexible cable with joint-connected segments.

    Args:
        base_path: Base USD path for the environment
        cable_name: Name for the cable group
        start_pos: Starting position (x, y, z) of the first segment
        num_segments: Number of cable segments
        segment_length: Length of each segment (meters)
        segment_radius: Radius of each segment (meters)
        segment_mass: Mass of each segment (kg)
        joint_angle_limit: Maximum joint angle in degrees
        color: RGB color tuple (0-1 range)

    Returns:
        List of segment prim paths
    """
    stage = omni.usd.get_context().get_stage()

    cable_root_path = f"{base_path}/{cable_name}"
    cable_root = UsdGeom.Xform.Define(stage, cable_root_path)

    segment_paths = []
    prev_path = None

    for i in range(num_segments):
        seg_path = f"{cable_root_path}/seg_{i:02d}"

        # Calculate position (segments along X axis)
        x_pos = start_pos[0] + i * segment_length
        y_pos = start_pos[1]
        z_pos = start_pos[2]

        # Create capsule geometry
        capsule = UsdGeom.Capsule.Define(stage, seg_path)
        capsule.GetRadiusAttr().Set(segment_radius)
        capsule.GetHeightAttr().Set(segment_length)
        capsule.GetAxisAttr().Set("X")

        # Set position
        xform = UsdGeom.Xformable(capsule)
        xform.AddTranslateOp().Set(Gf.Vec3d(x_pos, y_pos, z_pos))

        # Add rigid body physics
        prim = capsule.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)

        # Add mass
        mass_api = UsdPhysics.MassAPI.Apply(prim)
        mass_api.GetMassAttr().Set(segment_mass)

        # Add collision
        UsdPhysics.CollisionAPI.Apply(prim)

        # Set color
        capsule.GetDisplayColorAttr().Set([color])

        segment_paths.append(seg_path)

        # Create joint to previous segment
        if prev_path is not None:
            joint_path = f"{cable_root_path}/joint_{i-1:02d}_{i:02d}"

            # Create spherical joint for flexibility
            joint = UsdPhysics.SphericalJoint.Define(stage, joint_path)

            # Connect bodies
            joint.GetBody0Rel().SetTargets([Sdf.Path(prev_path)])
            joint.GetBody1Rel().SetTargets([Sdf.Path(seg_path)])

            # Set local positions at connection points
            joint.GetLocalPos0Attr().Set(Gf.Vec3f(segment_length/2, 0, 0))
            joint.GetLocalPos1Attr().Set(Gf.Vec3f(-segment_length/2, 0, 0))

            # Set cone angle limits for flexibility
            joint.GetConeAngle0LimitAttr().Set(joint_angle_limit)
            joint.GetConeAngle1LimitAttr().Set(joint_angle_limit)

        prev_path = seg_path

    return segment_paths


def create_l_hook(
    base_path: str = "/World/envs/env_0",
    hook_name: str = "hook",
    position: tuple = (0.5, 0.0, 0.90),
    vertical_length: float = 0.08,
    horizontal_length: float = 0.04,
    radius: float = 0.005,
    color: tuple = (0.2, 0.4, 0.8),  # Blue
):
    """
    Create an L-shaped hook.

    Args:
        base_path: Base USD path
        hook_name: Name for the hook
        position: Base position (x, y, z)
        vertical_length: Length of vertical part
        horizontal_length: Length of horizontal part
        radius: Radius of the hook cylinders
        color: RGB color tuple

    Returns:
        Tuple of (vertical_path, horizontal_path)
    """
    stage = omni.usd.get_context().get_stage()

    # Vertical part
    vert_path = f"{base_path}/{hook_name}_vertical"
    vert = UsdGeom.Cylinder.Define(stage, vert_path)
    vert.GetRadiusAttr().Set(radius)
    vert.GetHeightAttr().Set(vertical_length)
    vert.GetAxisAttr().Set("Z")

    xform_v = UsdGeom.Xformable(vert)
    xform_v.AddTranslateOp().Set(Gf.Vec3d(
        position[0],
        position[1],
        position[2] + vertical_length/2
    ))

    rigid_v = UsdPhysics.RigidBodyAPI.Apply(vert.GetPrim())
    rigid_v.GetKinematicEnabledAttr().Set(True)
    UsdPhysics.CollisionAPI.Apply(vert.GetPrim())
    vert.GetDisplayColorAttr().Set([color])

    # Horizontal part
    horiz_path = f"{base_path}/{hook_name}_horizontal"
    horiz = UsdGeom.Cylinder.Define(stage, horiz_path)
    horiz.GetRadiusAttr().Set(radius)
    horiz.GetHeightAttr().Set(horizontal_length)
    horiz.GetAxisAttr().Set("Y")

    xform_h = UsdGeom.Xformable(horiz)
    xform_h.AddTranslateOp().Set(Gf.Vec3d(
        position[0],
        position[1],
        position[2] + vertical_length
    ))

    rigid_h = UsdPhysics.RigidBodyAPI.Apply(horiz.GetPrim())
    rigid_h.GetKinematicEnabledAttr().Set(True)
    UsdPhysics.CollisionAPI.Apply(horiz.GetPrim())
    horiz.GetDisplayColorAttr().Set([color])

    return (vert_path, horiz_path)


def get_cable_segment_positions(stage, segment_paths: list) -> list:
    """
    Get world positions of cable segments.

    Args:
        stage: USD stage
        segment_paths: List of segment prim paths

    Returns:
        List of (x, y, z) positions
    """
    positions = []
    for path in segment_paths:
        prim = stage.GetPrimAtPath(path)
        if prim.IsValid():
            xform = UsdGeom.Xformable(prim)
            local_xform = xform.GetLocalTransformation()
            pos = local_xform.ExtractTranslation()
            positions.append((pos[0], pos[1], pos[2]))
    return positions


if __name__ == "__main__":
    print("Flexible Cable Utilities")
    print(f"  Default segments: {DEFAULT_NUM_SEGMENTS}")
    print(f"  Segment length: {DEFAULT_SEGMENT_LENGTH*100:.1f} cm")
    print(f"  Total length: {DEFAULT_NUM_SEGMENTS * DEFAULT_SEGMENT_LENGTH * 100:.0f} cm")
    print(f"  Segment radius: {DEFAULT_SEGMENT_RADIUS*1000:.1f} mm")
    print(f"  Joint flexibility: ±{DEFAULT_JOINT_ANGLE_LIMIT}°")
