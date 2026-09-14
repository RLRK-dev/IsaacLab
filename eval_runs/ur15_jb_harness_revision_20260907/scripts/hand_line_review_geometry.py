# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Initial compact-line fixtures and public-envelope housing geometry [m]."""

from __future__ import annotations

import math

import bpy
import numpy as np
from allocation_product import box, cylinder, empty, material, tube
from mathutils import Vector


def palette():
    values = {
        "white": ((0.73, 0.78, 0.81), 0.10, 0.37),
        "steel": ((0.44, 0.51, 0.56), 0.80, 0.26),
        "dark": ((0.035, 0.047, 0.058), 0.18, 0.37),
        "rubber": ((0.027, 0.035, 0.041), 0.0, 0.62),
        "blue": ((0.065, 0.31, 0.47), 0.23, 0.35),
        "pad": ((0.035, 0.24, 0.27), 0.05, 0.5),
        "orange": ((0.84, 0.22, 0.022), 0.06, 0.37),
        "copper": ((0.56, 0.30, 0.12), 0.78, 0.3),
        "floor": ((0.44, 0.50, 0.53), 0.03, 0.63),
        "yellow": ((0.76, 0.51, 0.08), 0.1, 0.5),
        "green": ((0.10, 0.49, 0.32), 0.0, 0.28),
        "glass": ((0.04, 0.14, 0.18), 0.35, 0.16),
    }
    return {key: material("initial_" + key, *row) for key, row in values.items()}


def beam(name, first, second, width, mat, parent=None):
    a, b = Vector(first), Vector(second)
    obj = box(name, (width, width, (b - a).length), (a + b) / 2, mat, parent, 0.002)
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return obj


def mesh_object(name, row, materials, parent=None):
    key = tuple(row["color"])
    if key not in materials:
        rgb = [max(0.018, (float(c) / 255) ** 2.2) for c in key[:3]]
        is_blue = rgb[2] > rgb[0] * 1.35
        materials[key] = material("source_color_" + "_".join(map(str, key[:3])), rgb, 0.15 if is_blue else 0.55, 0.36)
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(row["vertices"], [], row["faces"])
    mesh.update()
    if row.get("texture"):
        texture_key = (row["texture"], row["is_cap"])
        if texture_key not in materials:
            mat = material(
                "UR15_public_texture_" + str(row["is_cap"]), (1, 1, 1), 0.12 if row["is_cap"] else 0.65, 0.36
            )
            node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = bpy.data.images.load(row["texture"], check_existing=True)
            node.image.pack()
            mat.node_tree.links.new(node.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
            materials[texture_key] = mat
        mesh.materials.append(materials[texture_key])
        layer = mesh.uv_layers.new(name="Official_UV")
        uv = np.asarray(row["uv"])
        for loop in mesh.loops:
            layer.data[loop.index].uv = uv[loop.vertex_index]
        for face in mesh.polygons:
            face.use_smooth = True
        mesh.normals_split_custom_set_from_vertices(row["normals"])
    else:
        mesh.materials.append(materials[key])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    # Preserve hard boundaries in the source rather than smoothing across them.
    return obj


def clone_group(template, name):
    root = empty(name)
    for source in template.children:
        obj = bpy.data.objects.new(name + "__" + source.name, source.data)
        bpy.context.collection.objects.link(obj)
        obj.parent = root
        obj.matrix_basis = source.matrix_basis.copy()
        for modifier in source.modifiers:
            if modifier.type == "BEVEL":
                copied = obj.modifiers.new(modifier.name, "BEVEL")
                copied.width, copied.segments = modifier.width, modifier.segments
    return root


def rectangular_wall(name, width, depth, height, cutouts, mat, parent):
    """Build separate wall bands around rectangular port openings [m].

    Openings are initial manufacturing surrogates, not a vendor hole drawing.
    Explicit bands avoid the previous whole-housing Boolean failure.
    """
    low, high = 0.029, 0.064
    box(name + "_lower", (width, depth, low), (0, 0, low / 2), mat, parent, bevel=0)
    box(name + "_upper", (width, depth, height - high), (0, 0, (height + high) / 2), mat, parent, bevel=0)
    stops = [-width / 2]
    for center, half in cutouts:
        stops.extend((center - half, center + half))
    stops.append(width / 2)
    for i in range(0, len(stops) - 1, 2):
        a, b = stops[i : i + 2]
        if b > a:
            box(
                name + f"_pier_{i}",
                (b - a, depth, high - low),
                ((a + b) / 2, 0, (low + high) / 2),
                mat,
                parent,
                bevel=0,
            )


def housing_template(mats):
    root = empty("Public_envelope_housing_template")
    root["overall_public_envelope_m"] = [0.29210, 0.16000, 0.09229]
    root["internal_dimensions"] = "initial, unpublished; not manufacturing CAD"
    box("housing_bottom", (0.260, 0.160, 0.005), (0, 0, 0.0025), mats["white"], root)
    for x in (-0.138025, 0.138025):
        box("housing_mount_flange", (0.01605, 0.160, 0.006), (x, 0, 0.003), mats["white"], root)
        for y in (-0.066675, 0.066675):
            # The pilot is a visible dark recess, not a claimed through-drilled CAD hole.
            cylinder("housing_flange_pilot", 0.00245, 0.0005, (x, y, 0.0063), mats["dark"], root, vertices=24)
    front = empty("housing_front", root)
    front.location.y = -0.0785
    rectangular_wall(
        "front_port_wall",
        0.254,
        0.003,
        0.08629,
        [(x, 0.0115) for x in (-0.096, -0.048, 0, 0.048, 0.096)],
        mats["white"],
        front,
    )
    back = box("housing_back", (0.254, 0.003, 0.08629), (0, 0.0785, 0.043145), mats["white"], root)
    back["LV_opening"] = "omitted from this representative view"
    # Separate wall segments around each main HV port opening.
    for side in (-1, 1):
        wall = empty("housing_side", root)
        wall.location.x, wall.rotation_euler.z = side * 0.1285, math.pi / 2
        rectangular_wall("main_port_wall", 0.160, 0.003, 0.08629, [(0, 0.019)], mats["white"], wall)
    # Flatten the grouping so linked copies keep all wall bands.
    bpy.context.view_layer.update()
    for obj in list(root.children_recursive):
        if obj.type == "MESH" and obj.parent != root:
            matrix = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_basis = matrix
    for obj in list(root.children):
        if obj.type == "EMPTY":
            bpy.data.objects.remove(obj, do_unlink=True)
    return root


def connector(name, mats, parent=None, size=(0.028, 0.026, 0.024), main=False):
    root = empty(name, parent)
    box(name + "_shell", size, (0, 0, 0), mats["orange"], root, 0.002)
    box(name + "_shoulder", (size[0] + 0.008, 0.004, size[2] + 0.006), (0, size[1] / 2 - 0.002, 0), mats["dark"], root)
    cylinder(
        name + "_contact_recess",
        0.010 if main else 0.005,
        0.001,
        (0, -size[1] / 2 - 0.0007, 0),
        mats["dark"],
        root,
        (math.pi / 2, 0, 0),
    )
    box(name + "_latch", (0.008, 0.010, 0.003), (0, -0.003, size[2] / 2 + 0.0015), mats["dark"], root)
    return root


def add_ports(body, mats, omit_front_last=False):
    for index, x in enumerate((-0.096, -0.048, 0, 0.048, 0.096)):
        if omit_front_last and index == 4:
            continue
        port = connector(body.name + f"_aux_port_{index + 1}", mats, body)
        port.location = (x, -0.099, 0.046)
    for side in (-1, 1):
        port = connector(body.name + f"_main_port_{side}", mats, body, (0.042, 0.038, 0.037), True)
        port.location, port.rotation_euler.z = (side * 0.148, 0, 0.047), side * math.pi / 2


def internals(body, mats, include_contactor=False, include_wire=False):
    """Draw public major part counts with explicitly provisional positions."""
    box(body.name + "_insulating_base", (0.243, 0.144, 0.003), (0, 0, 0.007), mats["dark"], body)
    if include_contactor:
        cylinder(body.name + "_contactor", 0.025, 0.026, (-0.055, 0, 0.033), mats["dark"], body)
        cylinder(body.name + "_contactor_top", 0.025, 0.003, (-0.055, 0, 0.0475), mats["steel"], body)
        for y in (-0.045, 0.045):
            box(
                body.name + "_contactor_ear",
                (0.022, 0.031, 0.004),
                (-0.055, y - math.copysign(0.005, y), 0.022),
                mats["steel"],
                body,
            )
    for index, y in enumerate((-0.036, 0.033)):
        box(body.name + f"_relay_{index}", (0.026, 0.025, 0.024), (0.006, y, 0.023), mats["dark"], body)
        box(body.name + f"_resistor_{index}", (0.034, 0.009, 0.010), (0.044, y, 0.016), mats["white"], body)
    box(body.name + "_main_fuse", (0.074, 0.016, 0.014), (-0.064, 0.058, 0.019), mats["white"], body)
    for index in range(5):
        fuse = box(
            body.name + f"_aux_fuse_{index}",
            (0.010, 0.023, 0.013),
            (0.035 + index * 0.016, 0.006, 0.018),
            mats["white"],
            body,
        )
        fuse["rating_order_A"] = (20, 30, 20, 30, 10)[index]
    # Contact stack locations for the hand sample do not claim Ampere topology.
    for x, y in ((-0.085, -0.045), (0.085, 0.045)):
        cylinder(body.name + "_terminal_insulator", 0.011, 0.038, (x, y, 0.028), mats["dark"], body)
    if include_wire:
        tube(
            body.name + "_installed_connection_sample",
            [
                (-0.085, -0.008, 0.058),
                (-0.080, 0.025, 0.059),
                (-0.037, 0.028, 0.058),
                (0.033, -0.025, 0.058),
                (0.080, -0.025, 0.059),
                (0.085, 0.008, 0.058),
            ],
            0.007,
            mats["orange"],
            body,
        )


def pallet(name, center, mats):
    root = empty(name)
    root.location = (center, 0, 0.789)
    box(name + "_base", (0.40, 0.29, 0.026), (0, 0, 0.013), mats["steel"], root)
    box(name + "_plate", (0.38, 0.27, 0.006), (0, 0, 0.029), mats["dark"], root)
    for x in (-0.120, 0.120):
        for y in (-0.06, 0.06):
            box(name + "_support", (0.021, 0.019, 0.012), (x, y, 0.038), mats["blue"], root)
    for x in (-0.161, 0.161):
        cylinder(name + "_side_locator", 0.005, 0.021, (x, 0.06, 0.040), mats["dark"], root)
    root["station_lift"] = False
    return root


def fixture_table(name, center, size, top, mats):
    root = empty(name)
    root.location = (*center, 0)
    box(name + "_top", (*size, 0.025), (0, 0, top - 0.0125), mats["white"], root)
    for x in (-size[0] / 2 + 0.025, size[0] / 2 - 0.025):
        for y in (-size[1] / 2 + 0.025, size[1] / 2 - 0.025):
            beam(name + "_leg", (x, y, 0.075), (x, y, top - 0.025), 0.045, mats["steel"], root)
            cylinder(name + "_foot", 0.040, 0.025, (x, y, 0.055), mats["dark"], root)
    return root


def feeder(name, center, top, mats):
    root = empty(name)
    root.location = (*center, 0)
    box(name + "_pedestal", (0.20, 0.21, top - 0.18), (0, 0, (top - 0.18) / 2), mats["white"], root)
    box(name + "_hopper", (0.16, 0.15, 0.12), (0, 0.035, top - 0.08), mats["white"], root)
    box(name + "_window", (0.13, 0.008, 0.050), (0, -0.042, top - 0.066), mats["dark"], root)
    box(name + "_linear_feed_track", (0.028, 0.15, 0.018), (0, -0.09, top - 0.025), mats["blue"], root)
    cylinder(name + "_presenter", 0.014, 0.030, (0, -0.15, top - 0.015), mats["steel"], root)
    return root


def spindle(name, mats, parent=None, length=0.34):
    root = empty(name, parent)
    # Local origin is the tool tip. Upper body stays above the holding hand.
    cylinder(name + "_bit", 0.0028, 0.035, (0, 0, 0.0175), mats["steel"], root, vertices=24)
    shaft_length = length - 0.165
    cylinder(name + "_shaft", 0.0045, shaft_length, (0, 0, 0.035 + shaft_length / 2), mats["steel"], root, vertices=32)
    cylinder(name + "_feed_nose", 0.012, 0.046, (0, 0, length - 0.107), mats["white"], root)
    box(name + "_drive", (0.038, 0.042, 0.10), (0, 0, length - 0.038), mats["white"], root)
    box(name + "_motor_face", (0.021, 0.003, 0.045), (0, -0.023, length - 0.032), mats["dark"], root)
    cylinder(name + "_coupling", 0.036, 0.012, (0, 0, length), mats["steel"], root)
    return root


def onhand_camera(name, mats, parent):
    root = empty(name, parent)
    root.location = (0.070, 0, 0.065)
    root.rotation_euler = Vector((-0.070, 0, 0.105)).to_track_quat("Z", "Y").to_euler()
    box(name + "_body", (0.044, 0.032, 0.028), (0, 0, 0), mats["dark"], root)
    cylinder(name + "_lens", 0.008, 0.010, (0, 0, 0.019), mats["glass"], root)
    beam(name + "_bracket", (0.026, 0, 0.037), (0.070, 0, 0.065), 0.008, mats["steel"], parent)
    root["mount_basis"] = "user v0.1 provisional 70 mm lateral / 65 mm toward fingertip; not selected camera"
    return root


def robot_pedestal(name, x, y, dual, mats):
    root = empty(name)
    root.location = (x, y, 0)
    box(name + "_base", (0.46, 0.45, 0.045), (0, 0, 0.04), mats["steel"], root)
    for a in (-0.18, 0.18):
        for b in (-0.18, 0.18):
            cylinder(name + "_anchor", 0.012, 0.016, (a, b, 0.07), mats["dark"], root, vertices=6)
    if dual:
        cylinder(name + "_lower", 0.17, 0.34, (0, 0, 0.26), mats["dark"], root)
        cylinder(name + "_column", 0.12, 0.98, (0, 0, 0.88), mats["white"], root)
        for sign in (-1, 1):
            beam(name + "_yoke", (0, 0, 1.28), (sign * 0.26, 0, 1.38), 0.10, mats["white"], root)
        head = box(
            name + "_central_camera", (0.20, 0.060, 0.052), (0, -0.15 if y > 0 else 0.15, 1.31), mats["white"], root
        )
        for a in (-0.06, 0, 0.06):
            cylinder(name + "_central_lens", 0.017, 0.025, (a, head.location.y, 1.276), mats["glass"], root)
    else:
        box(name + "_column", (0.25, 0.25, 0.645), (0, 0, 0.39), mats["white"], root)
        cylinder(name + "_top", 0.13, 0.035, (0, 0, 0.7325), mats["steel"], root)
    controller_y = y + math.copysign(0.61, y)
    box(name + "_controller", (0.38, 0.22, 0.48), (x + 0.49, controller_y, 0.29), mats["white"])
    box(name + "_controller_display", (0.20, 0.006, 0.10), (x + 0.49, controller_y - 0.114, 0.38), mats["dark"])
    return root


def factory(mats):
    box("clean_floor", (20, 9, 0.05), (4.8, 0, -0.025), mats["floor"], bevel=0)
    for x in np.arange(-3, 14, 1.2):
        box("floor_joint", (0.002, 9, 0.0004), (x, 0, 0.0003), mats["steel"], bevel=0)
    for y in (-2.0, 2.0):
        box("floor_boundary", (14.4, 0.032, 0.0005), (4.8, y, 0.001), mats["yellow"], bevel=0)
    for z in (0.30, 0.789):
        for y in (-0.255, 0.255):
            box("conveyor_fixed_rail", (12.8, 0.055, 0.078), (4.8, y, z - 0.03), mats["white"])
        for x in np.arange(-1.55, 11.25, 0.09):
            cylinder(
                "conveyor_roller",
                0.023,
                0.455,
                (x, 0, z - 0.023),
                mats["steel"],
                rotation=(math.pi / 2, 0, 0),
                vertices=20,
            )
    for x in np.arange(-1.2, 11.2, 1.2):
        for y in (-0.28, 0.28):
            beam("conveyor_leg", (x, y, 0.05), (x, y, 0.76), 0.045, mats["steel"])
    for index, x in enumerate(np.arange(-0.6, 10.9, 1.8)):
        root = empty(f"return_empty_pallet_{index}")
        root.location = (x, 0, 0.30)
        box(root.name + "_plate", (0.40, 0.29, 0.032), (0, 0, 0.016), mats["steel"], root)
    # Frame-only enclosure: no transparent panels, front hand-height bar,
    # hanging station signs or round overhead lamps.
    for x in (-1.45, 1.2, 3.6, 6.0, 8.4, 10.85):
        for y in (-1.75, 1.75):
            beam("enclosure_post", (x, y, 0.05), (x, y, 2.38), 0.040, mats["steel"])
    for y in (-1.75, 1.75):
        for z in (0.08, 2.38):
            beam("enclosure_longitudinal", (-1.45, y, z), (10.85, y, z), 0.040, mats["steel"])
    for x in (-1.45, 10.85):
        beam("enclosure_upper_end", (x, -1.75, 2.38), (x, 1.75, 2.38), 0.040, mats["steel"])
    world = bpy.data.worlds.new("clean_ambient")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.50, 0.58, 0.67, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30
    bpy.context.scene.world = world
    for index, x in enumerate((-0.3, 2.4, 4.8, 7.2, 9.6)):
        for y in (-0.80, 0.80):
            box("outside_LED_housing", (1.60, 0.090, 0.036), (x, y, 2.63), mats["white"])
            lamp = bpy.data.lights.new(f"external_linear_LED_{index}_{y}", "AREA")
            lamp.shape, lamp.size, lamp.size_y, lamp.energy = "RECTANGLE", 1.50, 0.075, 180
            obj = bpy.data.objects.new(lamp.name, lamp)
            bpy.context.collection.objects.link(obj)
            obj.location = (x, y, 2.60)
            lamp.color = (0.88, 0.94, 1.0)
    return {
        "work_top_m": 0.789,
        "return_top_m": 0.30,
        "station_pallet_lift_m": 0,
        "return_loop_motion": "not demonstrated in these hand review clips",
        "transparent_panels": 0,
        "external_rectangular_LED_count": 10,
        "LED_energy_W_per_fixture": 180,
        "illuminance_lux": None,
    }


def xyz_gantry(mats):
    for x in (-1.20, 0.85):
        for y in (-1.67, 0.44):
            beam("XYZ_portal_leg", (x, y, 0.07), (x, y, 2.14), 0.060, mats["white"])
        beam("XYZ_Y_fixed_guide", (x, -1.67, 2.10), (x, 0.44, 2.10), 0.080, mats["steel"])
    y_stage = empty("OP010_Y_stage")
    box("XYZ_X_beam", (2.10, 0.090, 0.115), (-0.175, 0, 2.04), mats["white"], y_stage)
    box("XYZ_X_rail", (1.99, 0.012, 0.035), (-0.175, -0.055, 2.04), mats["steel"], y_stage)
    x_stage = empty("OP010_X_stage")
    box("XYZ_X_carriage", (0.18, 0.13, 0.17), (0, 0, 2.00), mats["dark"], x_stage)
    box("XYZ_Z_fixed_housing", (0.070, 0.070, 0.58), (0, 0, 1.81), mats["white"], x_stage)
    z_stage = empty("OP010_Z_stage")
    box("XYZ_Z_moving_rail", (0.045, 0.040, 0.56), (0, 0, 0.46), mats["steel"], z_stage)
    box("H06_wide_drive", (0.225, 0.085, 0.048), (0, 0, 0.190), mats["dark"], z_stage)
    box("H06_mount", (0.070, 0.065, 0.025), (0, 0, 0.225), mats["steel"], z_stage)
    jaws = []
    for sign in (-1, 1):
        jaw = empty(f"H06_jaw_{sign}", z_stage)
        box(jaw.name + "_slide", (0.22, 0.030, 0.020), (0, 0, 0.166), mats["steel"], jaw)
        box(jaw.name + "_finger", (0.215, 0.012, 0.093), (0, sign * 0.002, 0.115), mats["blue"], jaw)
        for x in (-0.085, 0.085):
            box(jaw.name + "_pad", (0.035, 0.006, 0.033), (x, -sign * 0.007, 0.070), mats["pad"], jaw)
        jaws.append(jaw)
    return y_stage, x_stage, z_stage, jaws


def camera(name, eye, target, lens=48):
    data = bpy.data.cameras.new("Review_OP030_" + name)
    obj = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = eye
    obj.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    data.lens, data.clip_start, data.clip_end = lens, 0.005, 200
    return obj
