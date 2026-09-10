# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Transparent line enclosure appearance based on the user's factory references.

All dimensions [m]. This is a layout/appearance model, not a certified guarding
design. Door sensors are visual placeholders, not executable safety functions.
"""

from __future__ import annotations

import math

import bpy
import numpy as np
from allocation_product import cylinder, empty, material
from continuous_common import delete_tree

X_LIMIT = 2.90
Y_START, Y_END = -5.70, 10.00
HEIGHT = 3.60
PROFILE = 0.045
PANEL_THICKNESS = 0.006


def box(name, dimensions, location, mat, parent=None, bevel=0.0015):
    """Create a box without invoking operators on the entire animated line [m]."""
    x, y, z = np.asarray(dimensions) / 2
    vertices = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent, obj.location = parent, location
    if bevel:
        modifier = obj.modifiers.new("Edge radius", "BEVEL")
        modifier.width, modifier.segments = min(bevel, min(dimensions) / 3), 3
    return obj


def clear_material():
    """Create a solid transparent sheet shader; thickness is real geometry [m]."""
    mat = material("Enclosure_clear_panel", (0.985, 0.996, 1.0), 0, 0.012)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["IOR"].default_value = 1.49
    shader.inputs["Coat Weight"].default_value = 0
    mat["material_scope"] = "clear-sheet appearance, generic optical model; panel grade and strength not specified"
    return mat


def remove_perimeter_barriers():
    """Remove the two source rail assemblies explicitly replaced by the enclosure."""
    removed = []
    for node in (799, 800):
        obj = bpy.data.objects.get(f"source_{node:04d}")
        if obj is None:
            raise RuntimeError(f"Expected source perimeter barrier {node} is absent")
        removed.append({"source_node": node, "mesh_children_removed": len(obj.children_recursive)})
        delete_tree(obj)
    return removed


def remove_product_guide_bars():
    """Remove the two long foreground guide bars and their dedicated mounts [m]."""
    removed = []
    for node in (8, 9):
        obj = bpy.data.objects.get(f"source_{node:04d}")
        if obj is None:
            raise RuntimeError(f"Expected source product guide {node} is absent")
        removed.append({"source_node": node, "mesh_children_removed": len(obj.children_recursive)})
        delete_tree(obj)
    return removed


def add_service_apertures(panels, parent, trim, *, include_lighting=True):
    """Cut sheet apertures for the preserved source hangers and service rails [m]."""
    # Reuse the fixture coordinates in original/render_ur15_line.py:
    # add_line_lighting() and add_line_services(). Individual sheet boxes are
    # closed solids, so Blender's native exact Boolean can cut them directly.
    openings = []
    if include_lighting:
        for x in (-2.7, -0.9, 0.9, 2.7):
            for y in (-5.2, -1.2, 2.8, 6.8):
                openings.append(("lighting_hanger", (x, y, HEIGHT - 0.016), (0.032, 0.032, 0.10), 2))
            for y in (Y_START, Y_END):
                openings.append(("lighting_rail", (x, y, 3.42), (0.072, 0.10, 0.102), 1))
        for x in (-1.9, 1.9):
            for y in (Y_START, Y_END):
                openings.append(("lighting_fixture", (x, y, 3.29), (0.175, 0.10, 0.150), 1))
    for x in (-1.42, 1.42):
        openings.append(("air_header", (x, Y_START, 2.62), (0.080, 0.10, 0.080), 1))
    cutters, modified, record = [], set(), []
    bpy.context.view_layer.update()
    for index, (kind, center, dimensions, axis) in enumerate(openings):
        planar = [coordinate for coordinate in range(3) if coordinate != axis]
        matched = []
        for name in panels:
            obj = bpy.data.objects[name]
            local = np.asarray(center) - np.asarray(obj.location)
            half = np.asarray(obj.dimensions) / 2
            if abs(local[axis]) > half[axis] + 0.001:
                continue
            if all(abs(local[coordinate]) < half[coordinate] for coordinate in planar):
                matched.append(obj)
        assert len(matched) == 1, (kind, center, [obj.name for obj in matched])
        panel = matched[0]
        cutter = box(f"Enclosure_aperture_tool_{index}", dimensions, center, trim, parent, 0)
        cutter.hide_render = True
        modifier = panel.modifiers.new(f"Service aperture {index}", "BOOLEAN")
        modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
        cutters.append(cutter)
        modified.add(panel.name)
        # Four short, backed edge strips make the opening explicit. They sit
        # outside the cut boundary rather than occupying the equipment path.
        a, b = planar
        for coordinate, transverse in ((a, b), (b, a)):
            for sign in (-1, 1):
                location = np.asarray(center, dtype=float)
                location[coordinate] += sign * (dimensions[coordinate] / 2 + 0.003)
                sizes = np.full(3, 0.006)
                sizes[transverse] = dimensions[transverse] + 0.012
                sizes[axis] = 0.012
                box(f"Enclosure_aperture_trim_{index}_{coordinate}_{sign}", sizes, location, trim, parent, 0.0008)
        record.append({"kind": kind, "center_m": list(center), "opening_m": list(dimensions), "panel": panel.name})
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for name in sorted(modified):
        obj = bpy.data.objects[name]
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
        obj.modifiers.clear()
        obj.data = mesh
    for cutter in cutters:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return record


def apply_transparent_enclosure(scene):
    """Replace the two identified yellow perimeter rail assemblies with an enclosure [m]."""
    if bpy.data.objects.get("Transparent_line_enclosure"):
        raise RuntimeError("Enclosure already exists; rebuild from its declared input")
    removed = remove_perimeter_barriers()
    removed_guides = remove_product_guide_bars()
    root = empty("Transparent_line_enclosure")
    root["user_directive"] = "Transparent full-line cover replaces existing safety fence; 2026-09-07"
    root["reference"] = "User KUKA screenshots; item modular transparent machine enclosure principle"
    white = material("Enclosure_white_aluminium", (0.74, 0.77, 0.79), 0.38, 0.32)
    metal = material("Enclosure_brushed_edges", (0.42, 0.48, 0.53), 0.80, 0.32)
    black = material("Enclosure_dark_gasket", (0.045, 0.055, 0.065), 0, 0.52)
    glass = clear_material()
    panels, doors = [], []

    def member(name, dims, location):
        return box("Enclosure_" + name, dims, location, white, root, 0.0025)

    def panel(name, dims, location, parent=root):
        obj = box("Enclosure_clear_" + name, dims, location, glass, parent, 0.0006)
        obj["panel_thickness_m"] = PANEL_THICKNESS
        panels.append(obj.name)
        return obj

    # Main side bays follow the existing 2.30-m pitch of cells on each side.
    stations = [-4.0 + 1.15 * i for i in range(10)]
    for sign in (-1, 1):
        x = sign * X_LIMIT
        access = [y for i, y in enumerate(stations) if (i % 2 == 0) == (sign == -1)]
        divisions = sorted(set([Y_START, Y_END, 7.72, *[y + d for y in access for d in (-0.60, 0.60)]]))
        # Additional end-bay divisions keep the roof/window span bounded.
        divisions = sorted(set([*divisions, 8.85]))
        for index, y in enumerate(divisions):
            member(f"post_{sign}_{index}", (PROFILE, PROFILE, HEIGHT - 0.03), (x, y, HEIGHT / 2 + 0.015))
            box(f"Enclosure_foot_{sign}_{index}", (0.12, 0.12, 0.014), (x, y, 0.007), metal, root)
            for dx, dy in ((-0.036, -0.036), (0.036, 0.036)):
                cylinder(
                    f"Enclosure_anchor_{sign}_{index}_{dx}",
                    0.006,
                    0.008,
                    (x + dx, y + dy, 0.018),
                    metal,
                    root,
                    vertices=6,
                )
        for index, (a, b) in enumerate(zip(divisions[:-1], divisions[1:], strict=True)):
            center, width = (a + b) / 2, b - a - PROFILE
            is_door = any(abs(center - y) < 1e-7 and abs(b - a - 1.20) < 1e-7 for y in access)
            for z in (0.10, 2.24, HEIGHT - PROFILE / 2):
                member(f"side_rail_{sign}_{index}_{z}", (PROFILE, width, PROFILE), (x, center, z))
            member(f"kick_{sign}_{index}", (0.012, width, 0.13), (x, center, 0.165))
            if is_door:
                door = empty(f"Enclosure_service_door_{sign}_{index}", root)
                door["mechanism"] = "sliding service door; closed in operating scene"
                door["service_station_y_m"] = center
                for yy in (a + 0.044, b - 0.044):
                    box(door.name + f"_stile{yy}", (0.035, 0.032, 2.00), (x + sign * 0.020, yy, 1.23), white, door)
                for z in (0.245, 2.215):
                    box(
                        door.name + f"_rail{z}",
                        (0.035, width - 0.042, 0.032),
                        (x + sign * 0.020, center, z),
                        white,
                        door,
                    )
                panel(door.name, (PANEL_THICKNESS, width - 0.095, 1.928), (x + sign * 0.020, center, 1.230), door)
                # Guide track, rollers, external pull and an interlock housing.
                box(
                    door.name + "_upper_track",
                    (0.056, 2.26, 0.055),
                    (x + sign * 0.055, center + 0.55, 2.282),
                    metal,
                    root,
                )
                for yy in (a + 0.12, b - 0.12):
                    cylinder(
                        door.name + f"_guide_wheel{yy}",
                        0.015,
                        0.016,
                        (x + sign * 0.052, yy, 2.259),
                        black,
                        door,
                        (0, math.pi / 2, 0),
                    )
                handle_y = b - 0.14
                for z in (1.05, 1.23):
                    box(
                        door.name + f"_handle_foot{z}",
                        (0.065, 0.020, 0.020),
                        (x + sign * 0.060, handle_y, z),
                        metal,
                        door,
                    )
                box(door.name + "_handle", (0.023, 0.022, 0.20), (x + sign * 0.090, handle_y, 1.14), black, door)
                box(
                    door.name + "_interlock_body", (0.035, 0.06, 0.10), (x + sign * 0.051, b - 0.016, 1.45), black, root
                )
                doors.append(door.name)
            else:
                panel(f"side_{sign}_{index}", (PANEL_THICKNESS, width - 0.014, 2.00), (x, center, 1.23))
            panel(
                f"clerestory_{sign}_{index}",
                (PANEL_THICKNESS, width - 0.014, HEIGHT - 2.31),
                (x, center, (2.27 + HEIGHT - 0.04) / 2),
            )

    # End faces. The conveyor portal is an opening, not a transparent solid
    # through which the pallet appears to pass. The existing infeed sensors
    # are outside a short covered transition tunnel.
    for end_index, y in enumerate((Y_START, Y_END)):
        divisions = [-X_LIMIT, -1.65, -0.75, 0.75, 1.65, X_LIMIT]
        for x in divisions:
            member(f"end_post_{end_index}_{x}", (PROFILE, PROFILE, HEIGHT), (x, y, HEIGHT / 2))
        for index, (a, b) in enumerate(zip(divisions[:-1], divisions[1:], strict=True)):
            center, width = (a + b) / 2, b - a - PROFILE
            portal = end_index == 0 and a == -0.75 and b == 0.75
            rack_door = end_index == 1 and a == 1.65
            lower_z = 1.25 if portal else 2.25 if rack_door else 0.20
            panel(
                f"end_{end_index}_{index}",
                (width - 0.014, PANEL_THICKNESS, HEIGHT - 0.055 - lower_z),
                (center, y, (HEIGHT - 0.045 + lower_z) / 2),
            )
            for z in (lower_z, HEIGHT - 0.0225):
                member(f"end_rail_{end_index}_{index}_{z}", (width, PROFILE, PROFILE), (center, y, z))
            if not portal:
                member(f"end_kick_{end_index}_{index}", (width, 0.012, 0.13), (center, y, 0.10))
            if rack_door:
                for leaf_index, (left, right) in enumerate(((a + 0.028, center - 0.004), (center + 0.004, b - 0.028))):
                    leaf = empty(f"Enclosure_rack_door_{leaf_index}", root)
                    leaf["mechanism"] = "outward hinged rear service door; shown closed"
                    leaf_center = (left + right) / 2
                    for x in (left + 0.015, right - 0.015):
                        box(leaf.name + f"_stile{x}", (0.03, 0.035, 2.04), (x, y, 1.20), white, leaf)
                    for z in (0.195, 2.205):
                        box(leaf.name + f"_rail{z}", (right - left, 0.035, 0.03), (leaf_center, y, z), white, leaf)
                    panel(leaf.name, (right - left - 0.065, PANEL_THICKNESS, 1.965), (leaf_center, y, 1.20), leaf)
                    handle_x = center + (-0.075 if leaf_index == 0 else 0.075)
                    box(leaf.name + "_handle", (0.025, 0.055, 0.22), (handle_x, y + 0.045, 1.10), black, leaf)
                    hinge_x = left if leaf_index == 0 else right
                    for z in (0.40, 1.2, 2.0):
                        cylinder(leaf.name + f"_hinge{z}", 0.012, 0.06, (hinge_x, y + 0.022, z), metal, leaf)
                    doors.append(leaf.name)

    roof_y = np.linspace(Y_START, Y_END, 9)
    for y in roof_y:
        member(f"roof_cross_{y}", (2 * X_LIMIT, PROFILE, PROFILE), (0, y, HEIGHT - 0.0225))
    for x in (-0.96, 0.96):
        member(f"roof_spine_{x}", (PROFILE, Y_END - Y_START, PROFILE), (x, (Y_START + Y_END) / 2, HEIGHT - 0.0225))
    for index, (a, b) in enumerate(zip(roof_y[:-1], roof_y[1:], strict=True)):
        for bay, (c, d) in enumerate(zip((-X_LIMIT, -0.96, 0.96), (-0.96, 0.96, X_LIMIT), strict=True)):
            panel(
                f"roof_{index}_{bay}",
                (d - c - PROFILE - 0.014, b - a - PROFILE - 0.014, PANEL_THICKNESS),
                ((c + d) / 2, (a + b) / 2, HEIGHT - 0.016),
            )
    tunnel_end = -7.0
    for x in (-0.75, 0.75):
        panel(
            f"infeed_tunnel_side{x}",
            (PANEL_THICKNESS, Y_START - tunnel_end, 0.96),
            (x, (Y_START + tunnel_end) / 2, 0.74),
        )
        member(f"infeed_tunnel_top{x}", (PROFILE, Y_START - tunnel_end, PROFILE), (x, (Y_START + tunnel_end) / 2, 1.22))
    panel("infeed_tunnel_roof", (1.50, Y_START - tunnel_end, PANEL_THICKNESS), (0, (Y_START + tunnel_end) / 2, 1.24))
    apertures = add_service_apertures(panels, root, black)
    scene.cycles.transmission_bounces = 12
    scene.cycles.max_bounces = max(scene.cycles.max_bounces, 16)
    return {
        "removed_perimeter_barriers": removed,
        "removed_product_guide_bars_and_mounts": removed_guides,
        "enclosure_bounds_m": [[-X_LIMIT, Y_START, 0], [X_LIMIT, Y_END, HEIGHT]],
        "profile_visual_size_m": PROFILE,
        "panel_visual_thickness_m": PANEL_THICKNESS,
        "transparent_panel_count": len(panels),
        "service_door_count": len(doors),
        "service_apertures": apertures,
        "roof_covered": True,
        "conveyor_entry_tunnel_m": [1.50, Y_START - tunnel_end, 1.24],
        "reference_urls": [
            "https://www.item24.com/en-us/theme-world/mechanical-and-plant-engineering/machine-cabins/machine-enclosure"
        ],
        "appearance_reference": "Three KUKA screenshots supplied by user 2026-09-07",
        "scope": (
            "native appearance/layout; structure, safety functions, access clearances and certification not released"
        ),
    }
