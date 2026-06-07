#!/usr/bin/env python3
"""
Create Routing Clip USD v1
===========================

Wire harness routing clip - static body fixed to table surface.
V-shaped guide funnels cable into U-shaped groove for retention.

Cross-section (front view):
    \\         /     <- V-guide opening
     \\       /
      \\     /       <- V angle: 60 deg
       |   |        <- U-groove (cable retention)
       |   |
       |___|        <- groove bottom (semicircle)
      [base]        <- pedestal (table mount)

Dimensions from CLAUDE.md spec.
"""

import argparse
import math
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Create Routing Clip USD v1")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Gf, Sdf, PhysxSchema, Vt
import os
import numpy as np

# Clip parameters (meters)
V_ANGLE_DEG = 60.0        # V-guide opening angle
V_OPENING_WIDTH = 0.030   # 30mm top opening width
GROOVE_INNER_D = 0.012    # 12mm U-groove inner diameter
GROOVE_DEPTH = 0.015      # 15mm U-groove depth
GUIDE_HEIGHT = 0.010      # 10mm V-guide height
BASE_WIDTH = 0.040        # 40mm pedestal width
BASE_DEPTH = 0.030        # 30mm pedestal depth (Y-axis, cable direction) — finger clearance
BASE_HEIGHT = 0.005       # 5mm pedestal height
TOTAL_HEIGHT = BASE_HEIGHT + GROOVE_DEPTH + GUIDE_HEIGHT  # 30mm
WALL_THICKNESS = 0.003    # 3mm wall thickness

# Physics
STATIC_FRICTION = 0.8
DYNAMIC_FRICTION = 0.6
RESTITUTION = 0.0

OUTPUT_PATH = "/home/rlrk/IsaacLab/data/clip/routing_clip_v1.usd"


def _build_clip_mesh(n_circle=16, n_depth=2):
    """Build clip mesh vertices and face indices.

    Strategy: extrude a 2D cross-section profile along Y-axis (cable direction).
    The cross-section is: base rect + U-groove walls + V-guide walls.
    We build the outer and inner profiles, then create a closed mesh.
    """
    groove_r = GROOVE_INNER_D / 2.0  # 6mm inner radius
    outer_r = groove_r + WALL_THICKNESS  # outer radius at groove
    half_v_top = V_OPENING_WIDTH / 2.0  # 15mm half-width at top

    # Build 2D cross-section points (XZ plane, right half, then mirror)
    # Going counterclockwise on the outer profile:
    # Start from base bottom-right, go up right wall, V-guide right, top,
    # then inner profile going back down

    # Key Z levels
    z_base_bot = 0.0
    z_base_top = BASE_HEIGHT
    z_groove_top = BASE_HEIGHT + GROOVE_DEPTH
    z_guide_top = TOTAL_HEIGHT

    # Outer profile (right half, bottom to top)
    outer_right = []
    # Base bottom-right
    outer_right.append((BASE_WIDTH / 2, z_base_bot))
    # Base top-right
    outer_right.append((BASE_WIDTH / 2, z_base_top))
    # Groove outer wall (right side) bottom
    outer_right.append((outer_r, z_base_top))
    # Groove outer wall (right side) top
    outer_right.append((outer_r, z_groove_top))
    # V-guide right side top
    outer_right.append((half_v_top, z_guide_top))

    # Inner profile (right half, top to bottom) — the groove cavity
    inner_right = []
    # V-guide inner right top (same as groove inner wall top)
    inner_right.append((groove_r, z_groove_top))
    # Groove inner wall right top
    # Groove inner wall right — semicircle bottom
    # Generate semicircle at bottom of groove
    n_semi = max(8, n_circle // 2)
    for j in range(n_semi + 1):
        angle = math.pi * j / n_semi  # 0 to pi (right to left)
        x = groove_r * math.cos(angle)
        z = z_base_top + groove_r - groove_r * math.sin(angle)
        inner_right.append((x, z))

    # Now build the full cross-section by mirroring
    # Left side is mirror of right side (negative X)

    # Full outer: left(mirrored, reversed) + right
    outer_left = [(-x, z) for x, z in reversed(outer_right)]
    # Full inner: right + left(mirrored, reversed)
    # inner_right goes from top-right down around semicircle to top-left(negative x)
    # The semicircle already crosses to negative x, so inner_right contains the full U

    # Build complete closed cross-section polygon (outer CCW, inner CW for hole)
    # For simplicity, we'll build the clip as a solid mesh by extruding the
    # cross-section outline and capping the ends.

    # Complete outline: outer right side up, across top-left, outer left side down,
    # base bottom, then we close it.
    # For the groove cavity: we subtract it later via the inner profile.

    # Simpler approach: build the cross-section as a single closed polygon
    # representing the solid material (outer minus inner cavity).

    # Let's trace the material boundary:
    # Start bottom-left of base, go clockwise:
    profile = []

    # Bottom of base (left to right)
    profile.append((-BASE_WIDTH / 2, z_base_bot))
    profile.append((BASE_WIDTH / 2, z_base_bot))

    # Right side up: base right wall
    profile.append((BASE_WIDTH / 2, z_base_top))

    # Step in to outer groove wall (right)
    profile.append((outer_r, z_base_top))

    # Right outer wall up to groove top
    profile.append((outer_r, z_groove_top))

    # V-guide right side up to top
    profile.append((half_v_top, z_guide_top))

    # -- Cross the opening at the top (this is open air, so we go to inner) --
    # V-guide inner right = groove_r at groove_top level
    # But the V-guide wall has thickness too. Let's model V-guide walls as solid:
    # The opening between the two V walls at the top = V_OPENING_WIDTH
    # The inner edges of V walls meet the groove inner walls at z_groove_top

    # Top of right V wall (outer edge) already placed at (half_v_top, z_guide_top)
    # Inner edge of right V wall at top:
    inner_v_half_top = half_v_top - WALL_THICKNESS / math.cos(math.radians(V_ANGLE_DEG / 2))
    # Clamp to groove_r minimum
    inner_v_half_top = max(inner_v_half_top, groove_r)

    profile.append((inner_v_half_top, z_guide_top))

    # Inner edge of right V wall at groove top
    profile.append((groove_r, z_groove_top))

    # Now trace the inner U-groove cavity (right side down, semicircle, left side up)
    for j in range(n_semi + 1):
        angle = math.pi * j / n_semi  # 0 to pi
        x = groove_r * math.cos(angle)
        z = z_base_top + groove_r - groove_r * math.sin(angle)
        profile.append((x, z))

    # Left inner groove wall up
    profile.append((-groove_r, z_groove_top))

    # Inner edge of left V wall at top
    profile.append((-inner_v_half_top, z_guide_top))

    # Outer edge of left V wall at top
    profile.append((-half_v_top, z_guide_top))

    # Left outer wall down from V top to groove top
    profile.append((-outer_r, z_groove_top))

    # Left outer groove wall down to base
    profile.append((-outer_r, z_base_top))

    # Step out to base left wall
    profile.append((-BASE_WIDTH / 2, z_base_top))

    # Close: left base wall down to start (already at bottom-left)
    # profile closes back to first point

    n_profile = len(profile)

    # Extrude along Y axis
    y_values = np.linspace(-BASE_DEPTH / 2, BASE_DEPTH / 2, n_depth)

    # Build vertices
    vertices = []
    for y in y_values:
        for x, z in profile:
            vertices.append(Gf.Vec3f(float(x), float(y), float(z)))

    n_verts_per_ring = n_profile

    # Build faces (quads between rings)
    face_vertex_counts = []
    face_vertex_indices = []

    for ring in range(n_depth - 1):
        base_curr = ring * n_verts_per_ring
        base_next = (ring + 1) * n_verts_per_ring
        for i in range(n_verts_per_ring):
            i_next = (i + 1) % n_verts_per_ring
            face_vertex_counts.append(4)
            face_vertex_indices.extend([
                base_curr + i,
                base_curr + i_next,
                base_next + i_next,
                base_next + i,
            ])

    # Cap faces (front and back)
    # Front cap (y = -BASE_DEPTH/2): polygon using first ring, wound CW when viewed from -Y
    face_vertex_counts.append(n_verts_per_ring)
    face_vertex_indices.extend(list(reversed(range(n_verts_per_ring))))

    # Back cap (y = +BASE_DEPTH/2): polygon using last ring
    last_base = (n_depth - 1) * n_verts_per_ring
    face_vertex_counts.append(n_verts_per_ring)
    face_vertex_indices.extend(list(range(last_base, last_base + n_verts_per_ring)))

    return vertices, face_vertex_counts, face_vertex_indices


def create_clip_usd(output_path: str):
    """Create routing clip USD."""

    print("=" * 60)
    print("Creating Routing Clip USD v1")
    print("=" * 60)
    print(f"  V-angle: {V_ANGLE_DEG}°")
    print(f"  V opening width: {V_OPENING_WIDTH * 1000:.0f} mm")
    print(f"  Groove inner diameter: {GROOVE_INNER_D * 1000:.0f} mm")
    print(f"  Groove depth: {GROOVE_DEPTH * 1000:.0f} mm")
    print(f"  Guide height: {GUIDE_HEIGHT * 1000:.0f} mm")
    print(f"  Total height: {TOTAL_HEIGHT * 1000:.0f} mm")
    print(f"  Base: {BASE_WIDTH * 1000:.0f} x {BASE_DEPTH * 1000:.0f} x {BASE_HEIGHT * 1000:.0f} mm")
    print(f"  Wall thickness: {WALL_THICKNESS * 1000:.0f} mm")
    print(f"  Friction: static={STATIC_FRICTION}, dynamic={DYNAMIC_FRICTION}")
    print(f"  Output: {output_path}")
    print()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"  Removed existing: {output_path}")

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Root xform
    clip_prim = stage.DefinePrim("/Clip", "Xform")
    stage.SetDefaultPrim(clip_prim)

    # Physics material
    mat_path = "/Clip/ClipMaterial"
    mat_prim = UsdShade.Material.Define(stage, mat_path)
    phys_mat = UsdPhysics.MaterialAPI.Apply(mat_prim.GetPrim())
    phys_mat.GetStaticFrictionAttr().Set(STATIC_FRICTION)
    phys_mat.GetDynamicFrictionAttr().Set(DYNAMIC_FRICTION)
    phys_mat.GetRestitutionAttr().Set(RESTITUTION)

    # Build mesh
    vertices, face_counts, face_indices = _build_clip_mesh(n_circle=16, n_depth=2)

    mesh_path = "/Clip/Body"
    mesh = UsdGeom.Mesh.Define(stage, mesh_path)
    mesh.GetPointsAttr().Set(Vt.Vec3fArray(vertices))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(face_counts))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(face_indices))
    mesh.GetSubdivisionSchemeAttr().Set("none")

    # Dark gray color
    mesh.GetDisplayColorAttr().Set([(0.3, 0.3, 0.35)])

    # Static collision body (no RigidBodyAPI = static)
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())

    # Mesh collision (accurate groove shape)
    mesh_collision = PhysxSchema.PhysxCollisionAPI.Apply(mesh.GetPrim())
    mesh_collision.GetContactOffsetAttr().Set(0.001)  # 1mm contact offset
    mesh_collision.GetRestOffsetAttr().Set(0.0005)     # 0.5mm rest offset

    # Use triangle mesh collision for static bodies
    PhysxSchema.PhysxTriangleMeshCollisionAPI.Apply(mesh.GetPrim())

    # Bind material
    bind_api = UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
    bind_api.Bind(mat_prim, UsdShade.Tokens.weakerThanDescendants, "physics")

    stage.Save()

    print(f"  Mesh: {len(vertices)} vertices, {len(face_counts)} faces")
    print()
    print(f"Successfully created: {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    try:
        create_clip_usd(OUTPUT_PATH)
    finally:
        simulation_app.close()
