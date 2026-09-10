# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Provisional supported-harness process tooling, dimensions in metres."""

from __future__ import annotations

import math

import allocation_product as primitives
import bpy
import numpy as np
from allocation_product import empty, material, tube
from jb_harness import FREE_FRAME, PORT_FRAME, PORT_ORIGIN, WIRE_RADIUS, connector, frame_object, route_paths
from transparent_enclosure import box


def cylinder(name, radius, depth, location, mat, parent=None, rotation=(0, 0, 0), vertices=32):
    """Create a cylinder without full-scene operators [m, rad]."""
    angles = np.arange(vertices) * 2 * math.pi / vertices
    coordinates = [(radius * math.cos(a), radius * math.sin(a), z) for z in (-depth / 2, depth / 2) for a in angles]
    faces = [(i, (i + 1) % vertices, (i + 1) % vertices + vertices, i + vertices) for i in range(vertices)]
    faces.extend((tuple(reversed(range(vertices))), tuple(range(vertices, 2 * vertices))))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(coordinates, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent, obj.location, obj.rotation_euler = parent, location, rotation
    for polygon in mesh.polygons[:vertices]:
        polygon.use_smooth = True
    return obj


# The product builder already owns the geometry definitions. Use the same
# primitives through direct mesh construction for this large native scene.
primitives.box, primitives.cylinder = box, cylinder


def materials():
    return {
        "blue": material("OP020_reusable_tooling_blue", (0.075, 0.24, 0.32), 0.35, 0.38),
        "black": material("OP020_soft_nest", (0.040, 0.058, 0.066), 0.0, 0.55),
        "metal": material("OP020_stock_aluminium", (0.60, 0.64, 0.67), 0.70, 0.31),
        "white": material("OP020_stock_white", (0.73, 0.77, 0.78), 0.22, 0.36),
        "orange": material("JB_HV_orange", (0.78, 0.175, 0.025), 0.06, 0.39),
    }


def operating_connector(name, parent, rotation, location, *, cap=False):
    """Build the published closed envelope with room for the lever to rotate [m]."""
    plug = connector(name, parent, rotation, location, cap=cap)
    shell = bpy.data.objects[name + "_backshell"]
    shell.scale.z = 0.0373 / 0.0493
    shell.location.z = 0.03165
    lever = bpy.data.objects[name + "_lever"]
    lever.location.z = 0.0563
    black = materials()["black"]
    box(name + "_CPA_track", (0.022, 0.036, 0.004), (0, -0.017, 0.0533), black, plug, 0.0006)
    for x in (-0.012, 0.012):
        box(name + f"_CPA_guide{x}", (0.004, 0.036, 0.009), (x, -0.017, 0.0548), black, plug, 0.0006)
    plug["revision"] = "OP020 operable envelope proxy; no vendor CAD or force qualification"
    return plug


def harness(name):
    """Create one persistent two-wire assembly; cap A is tracked separately [m]."""
    root = empty(name)
    root["assembly_uid"] = name
    root["wire_count"] = 2
    paths, free = route_paths()
    for i, points in enumerate(paths):
        obj = tube(name + f"_wire_{i + 1}", points, WIRE_RADIUS, materials()["orange"], root)
        obj["centerline_length_m"] = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
    a = operating_connector(name + "_A_JB", root, PORT_FRAME, PORT_ORIGIN)
    b = operating_connector(name + "_B_vehicle", root, FREE_FRAME, free, cap=True)
    root["end_A"] = "JB-side connection only"
    root["end_B"] = "vehicle end remains capped"
    return root, a, b


def protective_cap(name):
    """Create the removable cap and its physical finger tab [m]."""
    root = empty(name)
    black = materials()["black"]
    box(name + "_face", (0.063, 0.039, 0.0014), (0, 0, -0.0007), black, root, 0.0005)
    box(name + "_pull_extension", (0.018, 0.051, 0.002), (0, -0.0445, -0.0003), black, root)
    box(name + "_pull_tab", (0.018, 0.008, 0.0104), (0, -0.070, 0.0045), black, root)
    root["ownership"] = "manufacturing protection; recovered before mating"
    return root


def lever_clip(name):
    """Create a removable lever-operating shoe, recovered by the support tray [m]."""
    root = empty(name)
    blue = materials()["blue"]
    # The shoe slips over the bridge from its outward (+Z) side. Its extended
    # tongue gives the existing fingers access beyond the lever cheek.
    box(name + "_shoe_back", (0.025, 0.019, 0.003), (0.0435, 0.049, 0.0095), blue, root, 0.0005)
    for y in (0.041, 0.057):
        box(name + f"_spring_wall{y}", (0.025, 0.003, 0.018), (0.0435, y, 0.002), blue, root, 0.0004)
    box(name + "_gripping_tongue", (0.050, 0.010, 0.012), (0.080, 0.049, 0), blue, root, 0.0007)
    root["ownership"] = "removable process tool, not a vehicle component"
    root["qualification"] = "fit/retention/lever-force pending engineering; geometric proposal"
    return root


def support_tray(name):
    """Create an open 360-by-700-mm support frame with releasable cable pads [m]."""
    root = empty(name)
    mats = materials()
    box(name + "_long_rail-0.0925", (0.010, 0.530, 0.015), (-0.340, 0.025, -0.0925), mats["blue"], root)
    box(name + "_upper_end_rail", (0.010, 0.152, 0.015), (-0.340, 0.216, 0.2525), mats["blue"], root)
    for y in (-0.195, 0.145, 0.2825):
        box(name + f"_rib{y}", (0.010, 0.015, 0.360), (-0.340, y, 0.080), mats["blue"], root)
    # A reachable 40-mm grip handle, beyond the cable path and the rack end.
    box(name + "_handle", (0.055, 0.040, 0.035), (-0.340, 0.365, 0.090), mats["blue"], root)
    box(name + "_handle_stem", (0.015, 0.024, 0.070), (-0.320, 0.365, 0.1425), mats["metal"], root)
    box(name + "_handle_bridge", (0.020, 0.130, 0.012), (-0.320, 0.325, 0.180), mats["metal"], root)
    # The second handle supports the empty return with both arms. Its bridge
    # connects to the end rib while leaving the recovered lever shoe accessible.
    box(name + "_left_return_handle", (0.022, 0.040, 0.030), (-0.340, -0.150, 0.340), mats["blue"], root)
    box(name + "_left_handle_stem", (0.012, 0.012, 0.055), (-0.340, -0.150, 0.3025), mats["metal"], root)
    box(name + "_left_handle_bridge", (0.010, 0.340, 0.015), (-0.340, 0.010, 0.275), mats["metal"], root)
    box(name + "_left_handle_rib_join", (0.010, 0.016, 0.030), (-0.340, 0.145, 0.265), mats["metal"], root)
    moving = []
    paths, free = route_paths()
    # Each jaw pair supports both wires. The front jaw slides above the pair
    # before the tray withdraws; it never swings inward into the JB sidewall.
    for pad_index, fraction in enumerate((0.40, 0.56, 0.90)):
        index = int(fraction * (len(paths[0]) - 1))
        point = (paths[0][index] + paths[1][index]) / 2
        height = point[2] + 0.0925
        box(
            name + f"_clamp_frame_post_{pad_index}",
            (0.010, 0.012, height),
            (-0.340, point[1], -0.0925 + height / 2),
            mats["blue"],
            root,
        )
        pad_root = empty(name + f"_paired_pad_{pad_index}", root)
        frame_object(pad_root, np.eye(3), point)
        box(pad_root.name + "_back_pad", (0.008, 0.020, 0.044), (-WIRE_RADIUS - 0.004, 0, 0), mats["black"], pad_root)
        slide = empty(pad_root.name + "_slide", pad_root)
        reach = WIRE_RADIUS + 0.004
        box(pad_root.name + "_moving_pad", (0.008, 0.020, 0.044), (reach, 0, 0), mats["black"], slide)
        moving.append(slide)
        stem_length = point[0] - WIRE_RADIUS - 0.008 + 0.335
        box(
            pad_root.name + "_stem",
            (stem_length, 0.014, 0.018),
            (-WIRE_RADIUS - 0.008 - stem_length / 2, 0, 0),
            mats["blue"],
            pad_root,
        )
        cylinder(pad_root.name + "_clamp_body", 0.009, 0.050, (-0.045, 0, 0.025), mats["metal"], pad_root)
        cylinder(pad_root.name + "_clamp_rod", 0.004, 0.082, (-0.045, 0, -0.016), mats["metal"], slide)
        box(pad_root.name + "_clamp_arm", (0.006, 0.020, 0.030), (reach + 0.005, 0, 0.014), mats["blue"], slide)
        box(
            pad_root.name + "_clamp_bridge",
            (reach + 0.051, 0.014, 0.006),
            ((reach - 0.039) / 2, 0, 0.028),
            mats["blue"],
            slide,
        )
    # Connector supports stay behind the sockets, leaving the mating faces open.
    for suffix, frame, origin in (("A", PORT_FRAME, PORT_ORIGIN), ("B", FREE_FRAME, free)):
        support = empty(name + f"_plug_{suffix}_nest", root)
        frame_object(support, frame, origin)
        if suffix == "A":
            box(support.name + "_heel", (0.011, 0.035, 0.006), (-0.2815, -0.250, -0.028), mats["black"], root)
            box(support.name + "_stem", (0.012, 0.012, 0.057), (-0.285, -0.2325, -0.0025), mats["metal"], root)
            continue
        box(support.name + "_heel", (0.028, 0.012, 0.005), (0, 0.010, 0.0528), mats["black"], support)
        box(support.name + "_stem", (0.018, 0.012, 0.0297), (0, 0.010, 0.07015), mats["metal"], support)
        box(support.name + "_back", (0.018, 0.106, 0.010), (0, -0.040, 0.090), mats["blue"], support)
    box(name + "_A_nest_frame_bridge", (0.060, 0.012, 0.012), (-0.3125, -0.2325, 0.025), mats["blue"], root)
    box(name + "_A_nest_rib_join", (0.010, 0.050, 0.014), (-0.340, -0.213, 0.025), mats["blue"], root)
    box(name + "_B_nest_frame_post", (0.010, 0.016, 0.1125), (-0.337, free[1] - 0.040, -0.03625), mats["blue"], root)
    box(name + "_B_nest_frame_bridge", (0.018, 0.018, 0.012), (-0.343, free[1] - 0.040, 0.014), mats["blue"], root)
    slide = empty(name + "_tool_recovery_slide", root)
    slide.location.y = 0.20
    box(name + "_tool_recovery_rail", (0.012, 0.370, 0.012), (-0.340, -0.035, 0.100), mats["metal"], root)
    box(name + "_tool_recovery_carriage", (0.020, 0.026, 0.020), (-0.340, -0.220, 0.100), mats["blue"], slide)
    box(name + "_tool_recovery_insertion_rail", (0.095, 0.018, 0.012), (-0.3775, -0.220, 0.100), mats["metal"], slide)
    insertion = empty(name + "_tool_recovery_insertion", slide)
    box(name + "_tool_recovery_frame_bridge", (0.026, 0.180, 0.012), (-0.352, -0.300, 0.100), mats["blue"], insertion)
    box(name + "_tool_recovery_post", (0.014, 0.014, 0.066), (-0.365, -0.378, 0.070), mats["metal"], insertion)
    # The clip is caught only after the lever is closed and CPA locked. Its
    # U-shaped opening allows removal with the tray in the outward direction.
    clip_center = PORT_ORIGIN + PORT_FRAME @ np.array([0.078, 0.027, 0.0563])
    box(
        name + "_tool_recovery_body",
        (0.025, 0.044, 0.044),
        (-0.365, clip_center[1], clip_center[2]),
        mats["metal"],
        insertion,
    )
    recovery = []
    for sign in (-1, 1):
        obj = box(
            name + f"_tool_recovery_jaw_{sign}",
            (0.049, 0.030, 0.006),
            (-0.330, clip_center[1], clip_center[2] + sign * 0.022),
            mats["blue"],
            insertion,
        )
        recovery.append((obj, sign, float(clip_center[2])))
    root["ownership"] = "reusable support tray; lifted with harness support, recovered empty with both arms"
    root["empty_return_grip_centers_m"] = [[-0.340, -0.150, 0.340], [-0.340, 0.365, 0.090]]
    root["outer_frame_m"] = [0.360, 0.700, 0.010]
    root["power_interface"] = "clamp service coupler and controls require engineering definition"
    return root, moving, recovery


def magazine():
    """Create ten shelf supports and a separate upper empty-tray receiver [m]."""
    root = empty("OP020_ten_tray_magazine")
    mats = materials()
    cx, cy = 1.98, -2.85
    for x in (cx - 0.20, cx + 0.20):
        for y in (cy - 0.37, cy + 0.37):
            box(root.name + f"_post_{x}_{y}", (0.025, 0.025, 1.08), (x, y, 0.54), mats["metal"], root)
            box(root.name + f"_foot_{x}_{y}", (0.09, 0.09, 0.012), (x, y, 0.006), mats["metal"], root)
    for level in range(10):
        height = 0.12 + 0.110 * level
        for x in (1.80, 2.00):
            box(root.name + f"_shelf_{level}_{x}", (0.018, 0.66, 0.010), (x, cy, height - 0.012), mats["metal"], root)
    for x in (1.60, 1.80):
        box(root.name + f"_pickup_slide_{x}", (0.016, 0.660, 0.014), (x, cy, 1.096), mats["metal"], root)
    receiver = []
    for y in (cy - 0.135, cy + 0.205):
        box(root.name + f"_return_post_{y}", (0.035, 0.035, 1.266), (2.335, y, 0.633), mats["metal"], root)
        box(root.name + f"_return_hinge_bracket_{y}", (0.070, 0.045, 0.028), (2.315, y, 1.266), mats["metal"], root)
        cylinder(
            root.name + f"_return_hinge_{y}", 0.018, 0.050, (2.30, y, 1.266), mats["black"], root, (math.pi / 2, 0, 0)
        )
        pivot = empty(root.name + f"_return_pivot_{y}", root)
        pivot.location = (2.30, y, 1.266)
        pivot.rotation_euler.y = -math.pi / 2
        box(pivot.name + "_folding_arm", (0.800, 0.020, 0.014), (-0.400, 0, 0), mats["metal"], pivot)
        for x in (-0.740, -0.460):
            box(pivot.name + f"_support_seat{x}", (0.050, 0.035, 0.050), (x, 0, 0.032), mats["black"], pivot)
        receiver.append(pivot)
    root["capacity"] = 10
    root["continuous_supply_scope"] = (
        "one selected top tray and empty receiver modeled; ten-cycle selector control remains separate"
    )
    return root, receiver
