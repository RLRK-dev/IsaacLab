# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""OP030 detailed components and provisional assembly tooling [m, rad]."""

import json
import math

import bpy
import numpy as np
from allocation_product import empty, material, tube
from continuous_common import ROOT
from mathutils import Matrix
from op020_jb_geometry import box, cylinder, materials
from op030_definition import (
    DOCK_Y,
    J1_X,
    J1_Y,
    J1_Z,
    M6_DOCK_Y,
    M6_EXTENSION,
    TERMINAL_X,
    TERMINAL_Y,
    lug_frame,
    nut_supply_xy,
    wire_route,
)


def mesh_object(name, vertices, faces, mat, parent=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def ring(
    name, inner, outer, height, center, mat, parent=None, *, hex_outer=False, hex_inner=False, opening_half_angle=0.0
):
    """Create a true through-bore, with optional hexagonal boundaries [m]."""
    segments = 72
    angles = (
        np.linspace(opening_half_angle, 2 * np.pi - opening_half_angle, segments)
        if opening_half_angle
        else np.arange(segments) * 2 * np.pi / segments
    )
    coordinates = []
    for z in (-height / 2, height / 2):
        for radius, is_hex in ((inner, hex_inner), (outer, hex_outer)):
            radii = (
                radius / np.cos((angles + np.pi / 6) % (np.pi / 3) - np.pi / 6) if is_hex else np.full(segments, radius)
            )
            coordinates.extend([(r * math.cos(a), r * math.sin(a), z) for a, r in zip(angles, radii, strict=True)])
    faces = []
    for i in range(segments - bool(opening_half_angle)):
        j = (i + 1) % segments
        faces.extend(
            (
                (i, j, segments + j, segments + i),
                (2 * segments + i, 3 * segments + i, 3 * segments + j, 2 * segments + j),
                (i, 2 * segments + i, 2 * segments + j, j),
                (segments + i, segments + j, 3 * segments + j, 3 * segments + i),
            )
        )
    if opening_half_angle:
        faces.extend(
            (
                (0, segments, 3 * segments, 2 * segments),
                (segments - 1, 3 * segments - 1, 4 * segments - 1, 2 * segments - 1),
            )
        )
    obj = mesh_object(name, coordinates, faces, mat, parent)
    obj.location = center
    return obj


def thread_stud(name, diameter, pitch, length, mat, parent):
    """Create a visible helical external profile; no contact-force claim [m]."""
    segments = 48
    layers = int(round(length / pitch * 12)) + 1
    vertices = []
    for z in np.linspace(0, length, layers):
        for angle in np.arange(segments) * 2 * np.pi / segments:
            phase = (z / pitch - angle / (2 * np.pi)) % 1
            radius = diameter / 2 - 0.50 * pitch * (1 - abs(2 * phase - 1))
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
    faces = [
        (
            k * segments + i,
            k * segments + (i + 1) % segments,
            (k + 1) * segments + (i + 1) % segments,
            (k + 1) * segments + i,
        )
        for k in range(layers - 1)
        for i in range(segments)
    ]
    faces.extend((tuple(reversed(range(segments))), tuple(range((layers - 1) * segments, layers * segments))))
    obj = mesh_object(name, vertices, faces, mat, parent)
    obj["nominal_diameter_m"], obj["pitch_m"] = diameter, pitch
    obj["thread_scope"] = "external appearance; nut bore is a clearance envelope, no thread contact model"
    return obj


def nut(name, size, parent=None):
    """Build a bored nut and washer as one tracked fastening set [m]."""
    diameter, pitch, across_flats, height, washer_d, washer_h = {
        "M4": (0.004, 0.0007, 0.007, 0.0032, 0.009, 0.0008),
        "M6": (0.006, 0.001, 0.010, 0.005, 0.012, 0.0016),
        "M14": (0.014, 0.002, 0.022, 0.011, 0.028, 0.0025),
    }[size]
    root = empty(name, parent)
    metal = materials()["metal"]
    ring(name + "_washer", diameter / 2 + 0.0003, washer_d / 2, washer_h, (0, 0, washer_h / 2), metal, root)
    ring(
        name + "_hex",
        diameter / 2 + 0.00012,
        across_flats / 2,
        height,
        (0, 0, washer_h + height / 2),
        metal,
        root,
        hex_outer=True,
    )
    root["thread"], root["pitch_m"], root["across_flats_m"] = size, pitch, across_flats
    root["bore_scope"] = "clearance envelope; driven pitch/rotation is kinematic, not torque/contact simulation"
    return root


def vendor_lug(name, part, parent):
    """Reuse the full vendor tessellation with rigid axes and mm-to-m conversion."""
    saved = json.loads((ROOT / "inputs/op030_reference" / f"Klauke_{part}.json").read_text())
    v = np.asarray(saved["vertices"])
    if part == "6R14":
        vertices = np.column_stack((v[:, 0] + 45, -v[:, 2], v[:, 1] + 8)) / 1000
    elif part == "46R6":
        vertices = np.column_stack((-v[:, 2], -v[:, 0], v[:, 1] + 1.9)) / 1000
    else:
        raise ValueError(part)
    obj = mesh_object(
        name, vertices.tolist(), saved["faces"], material("OP030_tinned_copper", (0.65, 0.66, 0.64), 0.80, 0.29), parent
    )
    for face in obj.data.polygons:
        face.use_smooth = True
    obj["vendor_part"] = part
    obj["source_sha256"] = saved["source_sha256"]
    obj["geometry_reuse"] = "All vendor vertices and faces; rigid orientation and mm-to-m conversion only"
    return obj


def terminal(number):
    """Build the support and separate electrical stud at the retained XY [m]."""
    root = empty(f"OP030_T{number:02d}_UID001")
    mats = materials()
    # Root is the bottom of the 16-mm insulating disc, at product Z = 12 mm.
    box(root.name + "_mount_center", (0.052, 0.056, 0.006), (0, 0, -0.003), mats["black"], root, 0.0005)
    for sign in (-1, 1):
        ring(root.name + f"_mount_ear{sign}", 0.0023, 0.008, 0.006, (0, sign * 0.034, -0.003), mats["black"], root)
        box(root.name + f"_ear_bridge{sign}", (0.016, 0.008, 0.006), (0, sign * 0.028, -0.003), mats["black"], root, 0)
    cylinder(root.name + "_insulator", 0.026, 0.016, (0, 0, 0.008), mats["black"], root, vertices=72)
    # Contrasting molded seating marks are physical material geometry, not a QC verdict.
    for x in (-0.0261, 0.0261):
        box(root.name + f"_grip_mark{x}", (0.0002, 0.014, 0.007), (x, 0, 0.008), mats["blue"], root, 0)
    ring(root.name + "_contact_boss", 0.0065, 0.012, 0.004, (0, 0, 0.016), mats["metal"], root)
    stud = thread_stud(root.name + "_M14_stud", 0.014, 0.002, 0.028, mats["metal"], root)
    stud.location.z = 0.014
    root["part_uid"] = root.name
    root["insulator_diameter_m"], root["insulator_height_m"] = 0.052, 0.016
    root["xy_reused_m"] = [TERMINAL_X[number - 1], TERMINAL_Y]
    # Molded two-sided saddle prevents the lug barrel following the nut's
    # rotation. It supports only the terminated end; OP060 still adds routing clamps.
    sign = 1 if number == 1 else -1
    for y in (-0.0098, 0.0098):
        box(root.name + f"_lug_key{y}", (0.010, 0.0032, 0.014), (sign * 0.047, y, 0.023), mats["black"], root, 0.0003)
        box(root.name + f"_key_root{y}", (0.050, 0.0032, 0.008), (sign * 0.026, y, 0.012), mats["black"], root, 0.0003)
    box(root.name + "_barrel_seat", (0.010, 0.0164, 0.002), (sign * 0.047, 0, 0.017), mats["black"], root, 0)
    return root


def support_receivers(product):
    """Add explicit preinstalled support studs to the inherited B03 plate [m]."""
    root = empty("OP030_B03_preinstalled_mount_studs", product)
    metal = materials()["metal"]
    for number, x in enumerate(TERMINAL_X, 1):
        for sign in (-1, 1):
            p = empty(f"OP030_T{number:02d}_receiver_{sign}", root)
            p.location = (x, TERMINAL_Y + sign * 0.034, 0.004)
            # Low welded base meets the retained plate top; anti-rotation is
            # supplied by the two spaced studs, not by a single round pedestal.
            cylinder(p.name + "_weld_base", 0.0055, 0.003, (0, 0, 0.0015), metal, p)
            stud = thread_stud(p.name + "_M4", 0.004, 0.0007, 0.013, metal, p)
            stud.location.z = 0.003
    root["process_scope"] = "B03 supplied with weld studs; welding upstream is not animated here"
    return root


def rear_header(product):
    """Add two conductive M6 rear studs while retaining original mating pins [m]."""
    root = empty("OP030_J1_rear_power_connections", product)
    metal, black = materials()["metal"], materials()["black"]
    rotation = (0, math.pi / 2, 0)
    for number, y in enumerate(J1_Y, 1):
        collar = ring(
            root.name + f"_P{number}_insulator",
            0.00405,
            0.0105,
            J1_X + 0.231,
            ((J1_X - 0.231) / 2, y, J1_Z),
            black,
            root,
        )
        collar.rotation_euler = rotation
        cylinder(
            root.name + f"_P{number}_pin_extension",
            0.004,
            J1_X + 0.227,
            ((J1_X - 0.227) / 2, y, J1_Z),
            metal,
            root,
            rotation,
        )
        pin = thread_stud(root.name + f"_P{number}_M6x14", 0.006, 0.001, 0.014, metal, root)
        pin.location, pin.rotation_euler = (J1_X, y, J1_Z), rotation
    root["reference"] = "TE 2141227 drawing M6x14 and 114-94153 rear connection/load guidance"  # codespell:ignore te
    root["definition_status"] = "concept rear detail; not vendor header CAD or a released electrical design"
    root["rear_face_delta_for_cover_locator_clearance_m"] = 0.012
    return root


def internal_wire(number):
    """Build one persistent preterminated wire and two manufacturer lugs [m]."""
    root = empty(f"OP030_H03_{number}_UID001")
    route = wire_route(number)
    cable = tube(root.name + "_insulation", route, 0.007, materials()["orange"], root)
    cable["drawn_centerline_length_m"] = float(np.linalg.norm(np.diff(route, axis=0), axis=1).sum())
    copper = material("OP030_stranded_copper", (0.55, 0.30, 0.10), 0.76, 0.3)
    for end, part in (("J1", "46R6"), ("T", "6R14")):
        frame = empty(root.name + "_" + end, root)
        frame.matrix_basis = Matrix(lug_frame(number, end).tolist())
        vendor_lug(frame.name + "_" + part, part, frame)
        if end == "J1":
            cylinder(frame.name + "_conductor_in_barrel", 0.00399, 0.019, (0.020, 0, 0.019), copper, frame)
            sleeve = ring(
                frame.name + "_heatshrink", 0.00702, 0.008, 0.023, (0.020, 0, 0.022), materials()["black"], frame
            )
        else:
            cylinder(
                frame.name + "_conductor_in_barrel",
                0.00399,
                0.019,
                (0.0375, 0, 0.008),
                copper,
                frame,
                (0, math.pi / 2, 0),
            )
            sleeve = ring(
                frame.name + "_heatshrink", 0.00702, 0.008, 0.023, (0.039, 0, 0.008), materials()["black"], frame
            )
            sleeve.rotation_euler.y = math.pi / 2
        sleeve["scope"] = "prefabricated wire insulation; crimp deformation and pull test not simulated"
    root["assembly_uid"] = root.name
    root["connection"] = f"J1 rear P{number} to T{number:02d}"
    root["wire_section_geometry_candidate_mm2"] = 50
    root["wire_outer_diameter_candidate_m"] = 0.014
    root["definition_status"] = "packaging and motion candidate; cable product, ampacity and crimp process unselected"
    return root


def nutrunner(name, size):
    """Create a grippable cordless spindle and genuinely open socket [m]."""
    root = empty(name)
    mats = materials()
    across_flats = {"M4": 0.007, "M6": 0.010, "M14": 0.022}[size]
    radius = {"M4": 0.006, "M6": 0.008, "M14": 0.016}[size]
    spin = empty(name + "_spindle", root)
    ring(
        name + "_socket", across_flats / 2 + 0.00015, radius, 0.024, (0, 0, 0.012), mats["metal"], spin, hex_inner=True
    )
    if size == "M6":
        # A right-angle gear head lets the vertical motor stay above the rim.
        # The socket still approaches exactly along the horizontal M6 axis.
        box(name + "_angle_head", (0.028, 0.022, 0.018), (0.003, 0, 0.033), mats["metal"], root, 0.002)
        cylinder(name + "_shaft", 0.006, 0.168, (0.098, 0, 0.033), mats["metal"], root, (0, math.pi / 2, 0))
        box(name + "_drive", (0.100, 0.042, 0.042), (0.232, 0, 0.033), mats["white"], root, 0.004)
        box(name + "_battery", (0.065, 0.043, 0.040), (0.235, 0.0435, 0.033), mats["black"], root, 0.003)
        box(name + "_handle", (0.090, 0.042, 0.027), (0.327, 0, 0.033), mats["black"], root, 0.002)
        for sign in (-1, 1):
            box(
                name + f"_grip_flat{sign}",
                (0.036, 0.003, 0.027),
                (0.340, sign * 0.0225, 0.033),
                mats["black"],
                root,
                0.0003,
            )
        for obj in list(root.children):
            if obj != spin:
                obj.location.z += M6_EXTENSION
        cylinder(name + "_socket_extension", 0.005, M6_EXTENSION, (0, 0, 0.024 + M6_EXTENSION / 2), mats["metal"], spin)
        root["grip_contact_local_m"] = [0.340, 0, 0.033 + M6_EXTENSION]
        root["socket_extension_length_m"] = M6_EXTENSION
        root["grip_width_m"] = 0.048
        root["scope"] = "provisional cordless right-angle spindle; public angle-head architecture, no selected tool"
        return root, spin
    cylinder(name + "_shaft", 0.005, 0.156, (0, 0, 0.102), mats["metal"], spin)
    box(name + "_drive", (0.042, 0.042, 0.100), (0, 0, 0.230), mats["white"], root, 0.004)
    cylinder(name + "_nose", 0.012, 0.024, (0, 0, 0.180), mats["metal"], root)
    box(name + "_battery", (0.043, 0.040, 0.065), (0.0435, 0, 0.235), mats["black"], root, 0.003)
    box(name + "_handle", (0.042, 0.027, 0.090), (0, 0, 0.327), mats["black"], root, 0.002)
    for sign in (-1, 1):
        box(name + f"_grip_flat{sign}", (0.003, 0.027, 0.036), (sign * 0.0225, 0, 0.340), mats["black"], root, 0.0003)
    root["grip_contact_local_m"] = [0, 0, 0.340]
    root["grip_width_m"] = 0.048
    root["scope"] = "provisional cordless spindle envelope; no selected tool/torque result"
    return root, spin


def tool_stand():
    """Support three separate spindles near the working side of OP030 [m]."""
    root = empty("OP030_tool_dock")
    mats = materials()
    box(root.name + "_foot", (0.20, 0.27, 0.015), (-0.54, DOCK_Y, 0.0075), mats["metal"], root)
    box(root.name + "_post", (0.050, 0.050, 0.62), (-0.54, DOCK_Y, 0.325), mats["white"], root)
    box(root.name + "_plate", (0.32, 0.35, 0.010), (-0.54, DOCK_Y - 0.04, 0.640), mats["metal"], root)
    locations = {}
    for i, size in enumerate(("M4", "M6", "M14")):
        p = np.array([-0.65 + i * 0.11, DOCK_Y, 0.660])
        if size == "M6":
            p[1] = M6_DOCK_Y
        # Separate upper seats support the drive shoulder, leaving the socket
        # below and the grip flats above accessible.
        # The M14 socket has a 16 mm outer radius and must pass through this
        # motor support when the tool is lifted out of the dock.
        seat_radius = 0.017 if size in ("M6", "M14") else 0.0125
        ring(
            root.name + "_seat_" + size,
            seat_radius,
            0.026,
            0.010,
            p + (0, 0, 0.175),
            mats["blue"],
            root,
            opening_half_angle=0.50 if size == "M6" else 0.0,
        )
        for y in (-0.031, 0.031):
            box(root.name + f"_seat_leg_{size}_{y}", (0.012, 0.012, 0.185), p + (0, y, 0.0775), mats["metal"], root)
        locations[size] = p
    return root, locations


def split_positioner_rollers():
    """Provide the existing lift platen with a central roller opening [m]."""
    changed = {}
    for suffix in ("p00", "p01"):
        obj = bpy.data.objects["source_0004_m0004_" + suffix]
        original = obj.data
        points = np.asarray([v.co[:] for v in original.vertices])
        labels = np.rint((points[:, 1] + 3.45) / 0.115).astype(int)
        vertices, faces, selected = [], [], []
        for label in np.unique(labels):
            ids = np.flatnonzero(labels == label)
            subset = points[ids]
            remap = {int(old): new for new, old in enumerate(ids)}
            polygons = [tuple(remap[v] for v in p.vertices) for p in original.polygons if p.vertices[0] in remap]
            center_y = float((subset[:, 1].max() + subset[:, 1].min()) / 2)
            split = abs(center_y + 1.70) < 0.175
            if split:
                selected.append(center_y)
            for half in (-1, 1) if split else (0,):
                p = subset.copy()
                if half:
                    lower, upper = p[:, 0].min(), p[:, 0].max()
                    start, stop = (lower, -0.185) if half == -1 else (0.185, upper)
                    p[:, 0] = start + (p[:, 0] - lower) / (upper - lower) * (stop - start)
                offset = len(vertices)
                vertices.extend(p.tolist())
                faces.extend(tuple(v + offset for v in face) for face in polygons)
        mesh = bpy.data.meshes.new(original.name + "_OP030_split")
        mesh.from_pydata(vertices, [], faces)
        for mat in original.materials:
            mesh.materials.append(mat)
        for p in mesh.polygons:
            p.use_smooth = True
        obj.data = mesh
        obj["OP030_center_opening_m"] = 0.370
        obj["OP030_split_roller_centers_y_m"] = selected
        changed[obj.name] = selected
    return changed


def open_positioner_catch_panel():
    """Open the nonstructural catch sheet beneath the existing positioner [m]."""
    obj = bpy.data.objects["source_0006_m0006_p00"]
    data = obj.data
    p = np.array([v.co[:] for v in data.vertices])
    lower, upper = p.min(0), p.max(0)
    origin = np.linalg.inv(np.asarray(obj.matrix_world)) @ [0, -1.70, 0.3075, 1]
    x0, x1 = origin[0] - 0.185, origin[0] + 0.185
    y0, y1 = origin[1] - 0.175, origin[1] + 0.175
    regions = [
        (lower[0], x0, lower[1], upper[1]),
        (x1, upper[0], lower[1], upper[1]),
        (x0, x1, lower[1], y0),
        (x0, x1, y1, upper[1]),
    ]
    vertices, faces = [], []
    cube_faces = ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5))
    for a, b, c, d in regions:
        start = len(vertices)
        vertices.extend([(x, y, z) for x in (a, b) for y in (c, d) for z in (lower[2], upper[2])])
        faces.extend(tuple(start + i for i in face) for face in cube_faces)
    mesh = bpy.data.meshes.new(data.name + "_positioner_opening")
    mesh.from_pydata(vertices, [], faces)
    for mat in data.materials:
        mesh.materials.append(mat)
    obj.data = mesh
    obj["OP030_positioner_opening_m"] = [0.370, 0.350]


def pallet_lift():
    """Refine the existing OP030 lift-and-clamp under its original platen [m].

    Two scissor stages are a packaging candidate for the required 350-mm
    working stroke, not a selected load-rated lifting module.
    """
    fixed = empty("OP030_lift_fixed")
    carriage = empty("OP030_lift_carriage")
    mats = materials()
    platen = bpy.data.objects["source_0684"]
    world = platen.matrix_world.copy()
    platen.parent = carriage
    platen.matrix_basis = world
    # The original source contains long pins crossing a solid plate above its
    # blind bushes. Keep their diameters and shorten only the pilot projection.
    pins = bpy.data.objects["source_0684_m0111_p01"]
    for vertex in pins.data.vertices:
        vertex.co.z = 0.0065 + (vertex.co.z - 0.0065) * (0.045 - 0.0065) / (0.077 - 0.0065)
    for old_name in ("source_0683_m0110_p02", "source_0683_m0110_p03"):
        old_guide = bpy.data.objects.get(old_name)
        if old_guide:
            bpy.data.objects.remove(old_guide, do_unlink=True)
    # Retire the obsolete guide collars and place the four case fasteners
    # outside the new slider tracks, on the same retained case lid.
    for x in (-0.18, 0.18):
        for y in (-1.855, -1.545):
            cylinder(f"OP030_lift_case_bolt_{x}_{y}", 0.007, 0.008, (x, y, 0.280), mats["metal"], fixed, vertices=6)
    for y in (-1.815, -1.585):
        box(f"OP030_lift_seating_pad_{y}", (0.260, 0.030, 0.0235), (0, y, 0.42975), mats["black"], carriage, 0)
    split_positioner_rollers()
    open_positioner_catch_panel()

    def driver(obj, path, index, expression):
        curve = obj.driver_add(path, index)
        d = curve.driver
        var = d.variables.new()
        var.name, var.type = "z", "SINGLE_PROP"
        var.targets[0].id, var.targets[0].data_path = carriage, "location[2]"
        d.expression = expression

    for x in (-0.14, 0.14):
        for stage in (0, 1):
            # Stagger the two folding stages laterally. Their plates must
            # interleave at the lowered transfer height, not occupy one plane.
            stage_x = x * (1 - stage * 0.044 / 0.14)
            for sign in (-1, 1):
                arm = box(
                    f"OP030_lift_link_{x}_{stage}_{sign}",
                    (0.016, 0.020, 0.30),
                    (stage_x + sign * 0.0105, -1.70, 0),
                    mats["metal"],
                    fixed,
                    0.002,
                )
                driver(arm, "location", 2, f".291 + {stage + 0.5} * (.075 + z) / 2")
                driver(arm, "rotation_euler", 0, f"{sign} * acos((.075 + z) / .60)")
            pin = cylinder(
                f"OP030_lift_pivot_{x}_{stage}",
                0.014,
                0.041,
                (stage_x, -1.70, 0),
                mats["black"],
                fixed,
                (0, math.pi / 2, 0),
            )
            driver(pin, "location", 2, f".291 + {stage + 0.5} * (.075 + z) / 2")
        for sign in (-1, 1):
            pin = cylinder(
                f"OP030_lift_interstage_pin_{x}_{sign}",
                0.006,
                0.079,
                (x * 0.118 / 0.14, 0, 0),
                mats["metal"],
                fixed,
                (0, math.pi / 2, 0),
            )
            driver(pin, "location", 1, f"-1.70 + {sign} * sqrt(.09 - ((.075 + z) / 2)**2) / 2")
            driver(pin, "location", 2, ".291 + (.075 + z) / 2")
        for level in (0, 2):
            parent = fixed if level == 0 else carriage
            z = 0.291 if level == 0 else 0.366
            track_x = x if level == 0 else x * 0.096 / 0.14
            for sign in (-1, 1):
                slider = box(
                    f"OP030_lift_slider_{x}_{level}_{sign}",
                    (0.040, 0.030, 0.012),
                    (track_x, 0, z),
                    mats["blue"],
                    parent,
                    0.001,
                )
                driver(slider, "location", 1, f"-1.70 + {sign} * sqrt(.09 - ((.075 + z) / 2)**2) / 2")
            # Open guide shoulders retain each slider without a solid rail
            # passing through its motion path.
            for side in (-1, 1):
                box(
                    f"OP030_lift_track_{x}_{level}_{side}",
                    (0.005, 0.34, 0.010),
                    (track_x + side * 0.0228, -1.70, z),
                    mats["metal"],
                    parent,
                    0.001,
                )
                box(
                    f"OP030_lift_track_web_{x}_{level}_{side}",
                    (0.005, 0.28, 0.011 if level == 0 else 0.006),
                    (track_x + side * 0.0228, -1.70, 0.2805 if level == 0 else 0.374),
                    mats["metal"],
                    parent,
                    0,
                )
    fixed["reference"] = "Original station_hardware_03 case/platen/bushes; custom two-stage linkage packaging"
    carriage["stroke_m"] = 0.350
    carriage["pallet_plate_contact_z_m"] = 0.4415
    return fixed, carriage


def supply_kit():
    """Refine the existing stocker with one guided, withdrawable assembly kit [m]."""
    fixed = empty("OP030_supply_fixed")
    kit = empty("OP030_supply_kit")
    mats = materials()
    # Native frame p00 has open mechanisms up to z=0.79844, not a solid
    # shelf at z=0.730. Join the four retained posts with two crossmembers
    # and support the new mechanism on a plate above those old mechanisms.
    for y in (-2.13, -1.27):
        box(f"OP030_supply_base_crossmember_{y}", (0.280, 0.0272, 0.030), (-2.085, y, 0.785), mats["metal"], fixed)
    box("OP030_supply_base_plate", (0.280, 0.860, 0.008), (-2.085, -1.70, 0.804), mats["metal"], fixed)
    for y in (-2.075, -1.325):
        box(f"OP030_supply_guide_floor_{y}", (0.50, 0.048, 0.004), (-2.01, y, 0.886), mats["metal"], fixed)
        box(f"OP030_supply_guide_bearing_strip_{y}", (0.50, 0.030, 0.003), (-2.01, y, 0.8895), mats["black"], fixed)
        for sign in (-1, 1):
            box(
                f"OP030_supply_guide_side_{y}_{sign}",
                (0.50, 0.004, 0.028),
                (-2.01, y + sign * 0.022, 0.900),
                mats["metal"],
                fixed,
            )
            box(
                f"OP030_supply_guide_lip_{y}_{sign}",
                (0.50, 0.011, 0.003),
                (-2.01, y + sign * 0.0145, 0.9125),
                mats["metal"],
                fixed,
            )
        box(f"OP030_supply_moving_bar_{y}", (0.50, 0.027, 0.018), (-2.01, y, 0.900), mats["blue"], kit)
        box(f"OP030_supply_moving_neck_{y}", (0.36, 0.014, 0.0195), (-2.01, y, 0.91875), mats["blue"], kit)
        # Feet connect the fixed channels to the retained stocker's shelf level.
        for x in (-2.20, -1.98):
            box(f"OP030_supply_riser_{x}_{y}", (0.025, 0.048, 0.076), (x, y, 0.846), mats["metal"], fixed)
    box("OP030_supply_kit_plate", (0.46, 0.80, 0.010), (-2.02, -1.70, 0.9335), mats["white"], kit)
    for number in (1, 2):
        location = np.array([-2.08, -1.95 + (number - 1) * 0.11, 1.00])
        top = location[2] - 0.006
        box(
            f"OP030_supply_T{number:02d}_nest",
            (0.044, 0.050, top - 0.9385),
            (location[0], location[1], (0.9385 + top) / 2),
            mats["black"],
            kit,
        )
        origin = np.array([-1.83, -1.70 + (-0.07 if number == 1 else 0.30), 1.00])
        route = wire_route(number)
        for index in (20, 90, 165):
            point = origin + route[index]
            tangent = route[index + 1] - route[index - 1]
            tangent /= np.linalg.norm(tangent)
            up = np.array([0.0, 0.0, 1.0]) - tangent * tangent[2]
            up /= np.linalg.norm(up)
            axis = np.cross(tangent, up)
            axis /= np.linalg.norm(axis)
            center = point - up * 0.0115
            name = f"OP030_supply_H{number}_saddle_{index}"
            saddle = cylinder(name, 0.0045, 0.022, center, mats["black"], kit)
            rotation = np.column_stack((tangent, up, axis))
            saddle.rotation_mode = "QUATERNION"
            saddle.rotation_quaternion = Matrix(rotation.tolist()).to_quaternion()
            box(
                name + "_post",
                (0.012, 0.012, center[2] - 0.9385),
                (center[0], center[1], (center[2] + 0.9385) / 2),
                mats["blue"],
                kit,
            )
    fixed["scope"] = "Existing stocker frame retained; one 340-mm sliding kit, future replenishment not animated"
    kit["capacity_this_review"] = "T01, T02, H03-1, H03-2, one assembly kit"
    supply_drive(fixed, kit)
    return fixed, kit


def supply_drive(fixed, kit):
    """Show a hollow cylinder and rod connected to the guided kit [m]."""
    mats = materials()
    name = "OP030_supply_actuator"
    y, z = -2.00, 0.850
    barrel = ring(name + "_barrel", 0.016, 0.019, 0.400, (-2.055, y, z), mats["metal"], fixed)
    barrel.rotation_euler.y = math.pi / 2
    cylinder(name + "_rear_cap", 0.022, 0.020, (-2.265, y, z), mats["black"], fixed, (0, math.pi / 2, 0))
    cap = ring(name + "_rod_cap", 0.0061, 0.022, 0.020, (-1.845, y, z), mats["black"], fixed)
    cap.rotation_euler.y = math.pi / 2
    cylinder(name + "_rod", 0.006, 0.446, (-2.023, y, z), mats["metal"], kit, (0, math.pi / 2, 0))
    cylinder(name + "_piston", 0.0158, 0.012, (-2.240, y, z), mats["black"], kit, (0, math.pi / 2, 0))
    box(name + "_kit_clevis", (0.020, 0.020, 0.081), (-1.800, y, 0.888), mats["metal"], kit, 0.001)
    for x in (-2.20, -1.975):
        clamp = ring(name + f"_mount_ring{x}", 0.019, 0.024, 0.012, (x, y, z), mats["black"], fixed)
        clamp.rotation_euler.y = math.pi / 2
        box(name + f"_mount_foot{x}", (0.035, 0.045, 0.018), (x, y, 0.817), mats["metal"], fixed, 0.001)
    tube(
        name + "_supply_hose",
        [
            (-2.36, -2.03, 0.930),
            (-2.36, -2.00, 0.930),
            (-2.34, -1.98, 0.850),
            (-2.29, -1.98, 0.850),
            (-2.265, -1.978, 0.850),
        ],
        0.003,
        mats["black"],
        fixed,
    )
    fixed["actuator_bore_m"] = 0.032
    fixed["actuator_commanded_stroke_m"] = 0.340
    fixed["actuator_scope"] = (
        "Round cylinder packaging using retained primitive conventions; "
        "pressure, force and catalog selection unverified"
    )


def relocate_air_service():
    """Keep the existing FRL and drop pipe outside the kit's picking area [m]."""
    original = bpy.data.objects["source_0783"]
    original.location.x -= 0.94
    original.location.y -= 0.56
    root = empty("OP030_air_service_connections")
    mats = materials()
    tube(root.name + "_header_branch", [(-1.42, -2.10, 2.62), (-2.36, -2.10, 2.60)], 0.014, mats["metal"], root)
    box(root.name + "_stocker_mount", (0.045, 0.050, 0.025), (-2.2875, -2.10, 0.980), mats["metal"], root, 0.002)
    original["OP030_relocation_m"] = [-0.94, -0.56, 0.0]
    root["purpose"] = "Original air drop and FRL retained, outside the withdrawn assembly kit"
    return root


def nut_pockets():
    """Support eight individually tracked fastener sets before tool pickup [m]."""
    root = empty("OP030_fastener_supply")
    mats = materials()
    box(root.name + "_plate", (0.57, 0.28, 0.008), (-0.775, DOCK_Y - 0.265, 0.810), mats["white"], root)
    box(root.name + "_mount", (0.040, 0.11, 0.024), (-0.54, DOCK_Y - 0.205, 0.795), mats["metal"], root)
    box(root.name + "_support_post", (0.025, 0.025, 0.138), (-0.54, DOCK_Y - 0.185, 0.714), mats["metal"], root)
    cylinder(root.name + "_left_leg", 0.018, 0.786, (-1.00, DOCK_Y - 0.20, 0.413), mats["metal"], root)
    box(root.name + "_left_foot", (0.085, 0.10, 0.020), (-1.00, DOCK_Y - 0.20, 0.010), mats["metal"], root)
    for i in range(8):
        x, y = nut_supply_xy(i)
        if i in (4, 6):
            # Support the vertical M6 washer only; leave space beneath the
            # wider horizontal socket as it engages the hex nut.
            box(root.name + f"_seat_{i}", (0.0016, 0.012, 0.006), (x + 0.0008, y, 0.817), mats["black"], root, 0)
            box(root.name + f"_back_{i}", (0.002, 0.016, 0.020), (x - 0.001, y, 0.830), mats["black"], root, 0)
        else:
            box(root.name + f"_seat_{i}", (0.032, 0.036, 0.006), (x, y, 0.817), mats["black"], root)
    return root
