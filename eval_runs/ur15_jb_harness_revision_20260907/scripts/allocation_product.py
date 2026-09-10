# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Provisional product packaging shared by station and rack review models.

Dimensions are in metres. Electrical topology, connector rating, fastener
preload and cable material limits are not specified by this geometry model.
"""

from __future__ import annotations

import math

import bpy
import numpy as np
from continuous_common import clone_mesh_children
from mathutils import Matrix

CABLE_LENGTH = 0.900
CABLE_RADIUS = 0.014
CABLE_BEND_RADIUS = 0.140
CABLE_X = -0.295
CABLE_EXIT_Z = 0.052
COVER_SIZE = (0.532, 0.752, 0.018)


def material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def empty(name, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def box(name, dimensions, location, mat, parent=None, bevel=0.0015):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    obj.scale = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    obj.location = location
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Machined edge", "BEVEL")
        mod.width = min(bevel, min(dimensions) / 3)
        mod.segments = 3
    return obj


def cylinder(name, radius, depth, location, mat, parent=None, rotation=(0, 0, 0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("Edge radius", "BEVEL")
    mod.width = min(0.001, depth / 5)
    mod.segments = 2
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def tube(name, points, radius, mat, parent=None):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 4
    data.use_fill_caps = True
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for vertex, point in zip(spline.points, points, strict=True):
        vertex.co = (*point, 1)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    data.materials.append(mat)
    return obj


def locator_receiver(name, x, y, mat, parent):
    """Create a through-bored locating sleeve and its wall-mounted ledge [m]."""
    segments = 64
    vertices = [
        (x + radius * math.cos(a), y + radius * math.sin(a), z)
        for z in (0.041, 0.055)
        for radius in (0.0035, 0.0075)
        for a in np.linspace(0, 2 * math.pi, segments, endpoint=False)
    ]
    faces = []
    for index in range(segments):
        after = (index + 1) % segments
        for a, b, c, d in (
            (index, after, segments + after, segments + index),
            (
                2 * segments + index,
                3 * segments + index,
                3 * segments + after,
                2 * segments + after,
            ),
            (index, 2 * segments + index, 2 * segments + after, after),
            (
                segments + index,
                segments + after,
                3 * segments + after,
                3 * segments + index,
            ),
        ):
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    box(
        name + "_ledge",
        (0.027, 0.020, 0.006),
        (x + math.copysign(0.006, x), y, 0.038),
        mat,
        parent,
    )
    return obj


def cable_centerline() -> np.ndarray:
    """Return a rounded inverted U, analytic length 0.900 [m].

    The provisional corner radius is 0.140 [m]; this is not a manufacturer's
    permitted bend radius. Straight and circular sections share tangents.
    """
    r = CABLE_BEND_RADIUS
    span = 0.600
    height = (CABLE_LENGTH - span + (4 - math.pi) * r) / 2
    leg = height - r
    yz = [(y, z) for y, z in ((-span / 2, 0), (-span / 2, leg))]
    for angle in np.linspace(math.pi, math.pi / 2, 97)[1:]:
        yz.append((-span / 2 + r + r * math.cos(angle), leg + r * math.sin(angle)))
    yz.append((span / 2 - r, height))
    for angle in np.linspace(math.pi / 2, 0, 97)[1:]:
        yz.append((span / 2 - r + r * math.cos(angle), leg + r * math.sin(angle)))
    yz.append((span / 2, 0))
    return np.array([(CABLE_X, y, CABLE_EXIT_Z + z) for y, z in yz])


def build_product(template, name: str, stage: int = 8):
    """Build a packaging review assembly through a station number, without motion."""
    product = empty(name)
    product["product_revision"] = "allocation_packaging_v01"
    product["packaging_variant"] = "closed" if stage >= 7 else "open"
    product["process_completion"] = "NOT_IMPLEMENTED"
    product["electrical_result"] = "NOT_DEFINED"
    product["motion_validation"] = "NOT_PERFORMED"
    housing = clone_mesh_children(template, name + "_B01_B02_B03")
    housing.parent = product
    housing.matrix_basis = Matrix.Identity(4)
    white = material("allocation_satin_white", (0.77, 0.78, 0.79), 0.06, 0.42)
    steel = material("allocation_stainless", (0.50, 0.53, 0.56), 0.82, 0.36)
    orange = material("allocation_hv_orange", (0.78, 0.20, 0.055), 0.06, 0.40)
    rubber = material("allocation_insulator", (0.025, 0.03, 0.035), 0.0, 0.58)
    blue = material("allocation_locator_blue", (0.08, 0.32, 0.46), 0.08, 0.42)

    line = cable_centerline()
    top = float(line[:, 2].max())
    # Two product-mounted support towers transfer with the housing. These are
    # explicitly additional preassembled B04 parts, not invisible pallet fixtures.
    for number, y in enumerate((-0.13, 0.13), 1):
        p = f"{name}_B04_support_{number}"
        box(p + "_foot", (0.067, 0.036, 0.006), (-0.2815, y, 0.024), steel, product)
        box(
            p + "_tower",
            (0.008, 0.028, top - 0.028),
            (-0.280, y, (top + 0.012) / 2),
            steel,
            product,
        )
        # Open saddle contacts the underside, with open access from above.
        angles = np.linspace(math.pi, 2 * math.pi, 49)
        points = [(CABLE_X + 0.016 * math.cos(a), y, top + 0.016 * math.sin(a)) for a in angles]
        tube(p + "_saddle", points, 0.002, rubber, product)
        for yy in (y - 0.010, y + 0.010):
            cylinder(
                p + f"_mount_{yy:.3f}",
                0.0035,
                0.004,
                (-0.258, yy, 0.029),
                steel,
                product,
                vertices=6,
            )
    if stage >= 2:
        cable = tube(name + "_E01_cable_900mm", line, CABLE_RADIUS, orange, product)
        cable["centerline_length_m"] = CABLE_LENGTH
        cable["bend_radius_provisional_m"] = CABLE_BEND_RADIUS
        cable["assembly_id"] = name + "/E01"
        for number, y in enumerate((-0.30, 0.30), 1):
            plug = empty(f"{name}_E01_plug_{number}", product)
            plug["configuration"] = "custom_90_degree_packaging_only"
            # Preserve the original receiver axis. The shell is a new provisional
            # envelope; do not present it as a scaled commercial connector.
            box(
                plug.name + "_shell",
                (0.046, 0.068, 0.064),
                (-0.288, y, 0.012),
                orange,
                plug,
                0.005,
            )
            box(
                plug.name + "_front",
                (0.009, 0.074, 0.072),
                (-0.269, y, 0.012),
                rubber,
                plug,
                0.002,
            )
            cylinder(
                plug.name + "_boot",
                0.017,
                0.018,
                (CABLE_X, y, CABLE_EXIT_Z - 0.009),
                rubber,
                plug,
            )
            box(
                plug.name + "_lock",
                (0.018, 0.016, 0.009),
                (-0.293, y, -0.024),
                rubber,
                plug,
            )
    for x in (-0.22, 0.22):
        for y in (-0.315, 0.315):
            locator_receiver(f"{name}_B05_locator_receiver{x}_{y}", x, y, steel, product)
    # Preserve undefined circuit topology: terminals have placement candidates,
    # but there are no invented electrically connected rods or test results.
    if stage >= 3:
        for number, x in enumerate((-0.16, 0.16), 1):
            p = f"{name}_E02_terminal_{number}"
            cylinder(p + "_insulator", 0.026, 0.016, (x, -0.145, 0.012), rubber, product)
            cylinder(p + "_stud", 0.007, 0.028, (x, -0.145, 0.032), steel, product)
            cylinder(
                p + "_nut",
                0.012,
                0.007,
                (x, -0.145, 0.0425),
                steel,
                product,
                vertices=6,
            )
    if stage >= 7:
        cover = empty(name + "_C01_cover", product)
        cover["four_original_corner_bolts"] = "replaced_by_underside_locators; closure by two latches"
        box(cover.name + "_plate", COVER_SIZE, (0, 0, 0.068), white, cover, 0.005)
        # A real perimeter gasket, not the original solid slab under the lid.
        for x in (-0.242, 0.242):
            box(
                cover.name + f"_seal_x{x}",
                (0.008, 0.700, 0.004),
                (x, 0, 0.057),
                rubber,
                cover,
                0.001,
            )
        for y in (-0.346, 0.346):
            box(
                cover.name + f"_seal_y{y}",
                (0.476, 0.008, 0.004),
                (0, y, 0.057),
                rubber,
                cover,
                0.001,
            )
        for x in (-0.16, -0.08, 0.08, 0.16):
            box(
                cover.name + f"_rib{x}",
                (0.012, 0.58, 0.006),
                (x, 0, 0.080),
                white,
                cover,
            )
        for x in (-0.18, 0.18):
            # Contact pads for opposing gripper fingers, attached to real bosses.
            box(
                cover.name + f"_grip_boss{x}",
                (0.032, 0.055, 0.028),
                (x, 0, 0.091),
                white,
                cover,
            )
            for yy in (-0.0275, 0.0275):
                box(
                    cover.name + f"_grip_pad{x}_{yy}",
                    (0.030, 0.003, 0.016),
                    (x, yy, 0.094),
                    rubber,
                    cover,
                )
        box(
            cover.name + "_label_pad",
            (0.13, 0.09, 0.002),
            (0, 0.19, 0.078),
            white,
            cover,
        )
        for x in (-0.22, 0.22):
            for y in (-0.315, 0.315):
                cylinder(
                    cover.name + f"_locator{x}_{y}",
                    0.003,
                    0.012,
                    (x, y, 0.053),
                    blue,
                    cover,
                )
    if stage >= 8:
        for number, y in enumerate((-0.37, 0.37), 1):
            p = f"{name}_C02_latch_{number}"
            box(p + "_base", (0.060, 0.012, 0.034), (0, y, 0.032), steel, product)
            box(
                p + "_lever",
                (0.025, 0.014, 0.047),
                (0, y + math.copysign(0.011, y), 0.039),
                rubber,
                product,
            )
            cylinder(
                p + "_pivot",
                0.004,
                0.037,
                (0, y, 0.027),
                steel,
                product,
                (0, math.pi / 2, 0),
            )
            for x in (-0.021, 0.021):
                cylinder(
                    p + f"_fastener{x}",
                    0.0035,
                    0.004,
                    (x, y + math.copysign(0.008, y), 0.031),
                    steel,
                    product,
                    (math.pi / 2, 0, 0),
                    6,
                )
            box(p + "_receiver", (0.048, 0.012, 0.006), (0, y, 0.077), steel, product)
            hook = [
                (-0.028, y, 0.034),
                (-0.028, y, 0.0825),
                (0.028, y, 0.0825),
                (0.028, y, 0.034),
            ]
            tube(p + "_bail", hook, 0.0025, steel, product)
    return product


def packaging_metrics() -> dict:
    points = cable_centerline()
    measured = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
    bounds = np.array((points.min(axis=0) - CABLE_RADIUS, points.max(axis=0) + CABLE_RADIUS))
    height = float(bounds[1, 2] + 0.055)
    return {
        "analytic_cable_length_m": CABLE_LENGTH,
        "polyline_cable_length_m": measured,
        "cable_bounds_product_frame_m": bounds.tolist(),
        "provisional_bend_radius_m": CABLE_BEND_RADIUS,
        "minimum_bend_radius_specification": None,
        "cable_to_pallet_edge_clearance_m": 0.320 - float(np.abs(bounds[:, 0]).max()),
        "housing_flange_m": [0.545, 0.765],
        "cover_outer_m": list(COVER_SIZE),
        "rack_pitch_m": 0.380,
        "rack_plate_thickness_m": 0.030,
        "assembly_height_estimate_m": height,
        "shelf_vertical_clearance_estimate_m": 0.350 - height,
        "rack_storage": {
            "shelves": 3,
            "per_shelf": 2,
            "vertical_stacking": 1,
            "capacity": 6,
            "yaw_deg": 90,
        },
        "status": "provisional_packaging; not a complete electrically defined product",
    }
