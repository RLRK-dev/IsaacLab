# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record saved-native surface intersections and fixed heights [m].

These sampled mesh observations are not physical-validity acceptance and do
not replace continuous collision, load, grasp or fastening verification.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from continuous_common import ROOT, digest, write_json


def surface(objects, depsgraph):
    vertices, faces, owners = [], [], []
    for obj in objects:
        if obj.type not in {"MESH", "CURVE"}:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        offset = len(vertices)
        points = np.array([v.co[:] for v in mesh.vertices])
        if not len(points):
            evaluated.to_mesh_clear()
            continue
        matrix = np.array(evaluated.matrix_world)
        points = points @ matrix[:3, :3].T + matrix[:3, 3]
        vertices.extend(map(Vector, points))
        for polygon in mesh.polygons:
            faces.append(tuple(offset + vertex for vertex in polygon.vertices))
            owners.append(obj.name)
        evaluated.to_mesh_clear()
    if not vertices:
        return None
    bounds = np.array(vertices)
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False), owners, bounds.min(0), bounds.max(0)


def arm_objects(name, distal=False):
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.get("arm") == name:
            if distal and obj.get("robot_link") in {"base", "shoulder"}:
                continue
            rows.append(obj)
        elif (
            obj.name.startswith(name + "_monocular")
            or name == "A_tool"
            and obj.name.startswith("A_permanently_mounted_driver")
        ):
            rows.append(obj)
    return rows


def compare(left, right):
    if left is None or right is None:
        return []
    if np.any(left[2] > right[3]) or np.any(right[2] > left[3]):
        return []
    return sorted({(left[1][a], right[1][b]) for a, b in left[0].overlap(right[0])})


def main():
    native = ROOT / "UR15_JB_initial_hands_v02.blend"
    identity = digest(native)
    bpy.ops.wm.open_mainfile(filepath=str(native))
    scene = bpy.context.scene
    groups = {name: arm_objects(name) for name in ("OP020", "A_hold", "A_tool", "B_left", "B_right", "C")}
    pairs = [("A_hold", "A_tool"), ("B_left", "B_right")]
    groups["OP010_hand"] = [o for o in scene.objects if o.name.startswith("H06_")]
    groups["OP010_stock_and_table"] = [
        o
        for o in scene.objects
        if o.name.startswith(("OP010_stock_body_", "OP010_stock_20")) and not o.name.startswith("OP010_stock_body_01")
    ]
    pairs.append(("OP010_hand", "OP010_stock_and_table"))
    for cell, names in (("A", ("A_hold", "A_tool")), ("B", ("B_left", "B_right"))):
        column = cell + "_column"
        groups[column] = [
            o for o in scene.objects if o.name in {f"OP030_{cell}_dual_column", f"OP030_{cell}_dual_lower"}
        ]
        for name in names:
            groups[name + "_distal"] = arm_objects(name, True)
            pairs.append((name + "_distal", column))
    groups["A_work_fixture"] = [
        o
        for o in scene.objects
        if o.name.startswith("A_twenty_component_tray") or o.name.startswith("A_distinct_workpiece__")
    ]
    groups["B_work_fixture"] = [
        o
        for o in scene.objects
        if o.name.startswith("B_ten_parallel_wire_tray") or o.name.startswith("B_distinct_workpiece__")
    ]
    for name, fixture in (("A_hold", "A_work_fixture"), ("B_left", "B_work_fixture"), ("B_right", "B_work_fixture")):
        pairs.append((name, fixture))
    groups["B_tools_and_stock"] = [
        o
        for o in scene.objects
        if o.name.startswith(("B_stock_wire_", "B_wire_mid_support_", "B_equipment_driver_", "B_tool_"))
    ]
    groups["C_work_fixture"] = [
        o
        for o in scene.objects
        if o.name.startswith(
            (
                "C_distinct_workpiece",
                "C_retained_B_",
                "C_control_connector_supply",
                "C_stock_control_",
                "C_fixed_control_receiver",
            )
        )
    ]
    groups["OP020_work_fixture"] = [
        o
        for o in scene.objects
        if o.name.startswith(("OP020_distinct_workpiece", "OP020_rigid_connector_supply", "OP020_stock_connector_"))
    ]
    groups["OP020_pusher"] = [o for o in scene.objects if o.name.startswith(("OP020_push_", "OP020_fixed_pusher_"))]
    pairs.extend(
        (
            ("B_left", "B_tools_and_stock"),
            ("B_right", "B_tools_and_stock"),
            ("C", "C_work_fixture"),
            ("OP020", "OP020_work_fixture"),
            ("OP020", "OP020_pusher"),
        )
    )
    times = sorted(set([*range(781, 1200, 14), 829, 901, 973, 1015, 1101, 1111, 1135, 1155, 1185]))
    times = sorted(set(times + list(range(361, 780, 14)) + list(range(1, 360, 14))))
    intersections = {a + "/" + b: [] for a, b in pairs}
    for index, frame in enumerate(times):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        surfaces = {name: surface(objects, depsgraph) for name, objects in groups.items()}
        for a, b in pairs:
            active = 0 if a == "OP010_hand" else 1 if a == "OP020" else 2
            interval = 0 if frame < 361 else 1 if frame < 781 else 2
            if active != interval:
                continue
            hits = compare(surfaces[a], surfaces[b])
            if hits:
                intersections[a + "/" + b].append({"frame": frame, "object_pairs": hits})
        if index % 10 == 0:
            print("HAND_LINE_SURFACE_SAMPLE", frame, flush=True)
    heights = {}
    for frame in (1, 251, 631, 991, 1471, 1881, 2039):
        scene.frame_set(frame)
        heights[str(frame)] = {
            o.name: float(o.matrix_world.translation.z) for o in scene.objects if o.name.endswith("_work_pallet")
        }
    pusher_contact = []
    for frame in range(625, 662, 3):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        face = scene.objects["OP020_push_face"]
        shell = scene.objects["OP020_handled_connector_shell"]
        face_bounds = [face.matrix_world @ Vector(v) for v in face.bound_box]
        shell_bounds = [shell.matrix_world @ Vector(v) for v in shell.bound_box]
        pusher_contact.append(
            {
                "frame": frame,
                "connector_rear_y_m": min(v.y for v in shell_bounds),
                "pusher_front_y_m": max(v.y for v in face_bounds),
                "signed_gap_y_m": min(v.y for v in shell_bounds) - max(v.y for v in face_bounds),
            }
        )
    assert digest(native) == identity
    report = {
        "native_sha256": identity,
        "native_read_only": True,
        "sampled_frames": times,
        "method": "Evaluated mesh/curve triangle surface BVH overlap; no containment or continuous-path verdict",
        "surface_intersections": intersections,
        "pallet_origin_heights_m": heights,
        "op020_pusher_contact_during_feed": pusher_contact,
        "physical_acceptance_verdict": None,
    }
    write_json(ROOT / "audit/hand_line_review_v01_surface_probe.json", report)
    print("HAND_LINE_SURFACE_COMPLETE", json.dumps({k: len(v) for k, v in intersections.items()}), flush=True)


if __name__ == "__main__":
    main()
