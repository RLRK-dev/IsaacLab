# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bind visible fragments to estimated sleeve entrances in a static display [m]."""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_hvjb_photo_model_v01 as base
import build_hvjb_photo_model_v02 as previous
from allocation_product import tube
from build_hvjb_photo_catalog_v01 import digest
from header_review_primitives import box

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "UR15_JB_photo_correspondence_v03_p02.blend"
CATALOG = ROOT / "data/hvjb_photo_correspondence_v03_p01.json"
MESH = ROOT / "data/hvjb_photo_model_v03_p02.json.gz"
PREVIEW = ROOT / "previews/hvjb_photo_v03_p02"
PINNED = {
    **previous.PINNED,
    "UR15_JB_photo_correspondence_v02_p02.blend": "eaad0da7f4eea1098a420985e50989d1a3fe149596532cf5c4d8d1b701f5ba93",
    "UR15_JB_photo_correspondence_v03_p01.blend": "a3b3787535e82ca918fc44bef28f5fe3212fb4137969766b9f4fd41c4560b98c",
}


def clear_children(root):
    for obj in list(root.children_recursive):
        bpy.data.objects.remove(obj, do_unlink=True)


def terminal(root, row, mats):
    clear_children(root)
    x, y, width, height = row["rect_px"]
    root.location = (*base.xy((x + width / 2, y + height / 2)), 0.0525)
    dimensions = Vector((width / 4200, height / 4200, 0.009))
    opening = {"top": (2, 1), "north": (1, 1), "south": (1, -1), "west": (0, -1), "east": (0, 1)}
    axis, sign = opening[row["display_opening"]]
    thickness = 0.0007
    for face_axis in range(3):
        for face_sign in (-1, 1):
            if face_axis == axis and face_sign == sign:
                continue
            size, center = dimensions.copy(), Vector((0, 0, 0))
            size[face_axis] = thickness
            center[face_axis] = face_sign * (dimensions[face_axis] - thickness) / 2
            box(root.name + "_sleeve_wall", size, center, mats[row["render_color"]], root, 0.0002)
    ex, ey = base.xy(row["display_entry_px"])
    local = Vector((ex - root.location.x, ey - root.location.y, 0))
    local[axis] = sign * dimensions[axis] / 2
    normal = Vector((0, 0, 0))
    normal[axis] = sign
    root["display_wire_entry_local_m"] = list(local)
    root["display_wire_exit_direction"] = list(normal)
    root["display_opening"] = row["display_opening"]
    root["opening_basis"] = "visible exterior entrance; wall, depth and hidden contact are not manufacturing geometry"


def lug(root, row, joint, mats):
    clear_children(root)
    dx = row["sleeve_direction_px"][0] - joint["center_px"][0]
    dy = joint["center_px"][1] - row["sleeve_direction_px"][1]
    direction = Vector((dx, 0 if "fuse_side" in joint else dy, 0)).normalized()
    length = (abs(dx) if "fuse_side" in joint else math.hypot(dx, dy)) / 4200
    previous.annulus(root.name + "_visible_ring", (0, 0, -0.0009), 0.0057, 0.0025, 0.001, mats["steel"], root)
    tube(root.name + "_barrel", [direction * 0.0045, direction * (length * 0.65)], 0.0024, mats["steel"], root)
    tube(root.name + "_sleeve", [direction * (length * 0.42), direction * length], 0.0028, mats["rubber"], root)
    root["display_wire_entry_local_m"] = list(direction * length)
    root["display_wire_exit_direction"] = list(direction)
    root["sleeve_length_basis"] = "photo-projected display estimate; not an actual crimp or heat-shrink dimension"


def visible_wire(row, roots, mats):
    root = roots[row["id"]]
    clear_children(root)
    z = 0.054
    if row["id"] in {"W01", "W02", "W03"}:
        z = 0.063
    elif row["id"] in {"W04", "W05", "W06", "W07"}:
        z = 0.031
    elif row["id"] in {"W11", "W12", "W13", "W14"}:
        z = 0.065
    elif row["id"].startswith("WI"):
        z = 0.046
    top_entry = any(
        end.get("bind_display_geometry") and roots[end["feature_id"]].get("display_opening") == "top"
        for end in row["observed_trace_ends"]
    )
    if top_entry:
        z = 0.061
    points = [Vector((*base.xy(point), z)) for point in row["polyline_px"]]
    bindings = []
    for side, end in enumerate(row["observed_trace_ends"]):
        if not end.get("bind_display_geometry"):
            continue
        feature = roots[end["feature_id"]]
        anchor = feature.matrix_world @ Vector(feature["display_wire_entry_local_m"])
        normal = feature.matrix_world.to_3x3() @ Vector(feature["display_wire_exit_direction"])
        index = 0 if side == 0 else -1
        # Local entry transition is a display estimate; it is not a physically solved wire shape.
        delta = anchor - points[index]
        if top_entry:
            # Keep the exterior trace above the estimated sleeve rim until the vertical entry.
            delta.z = 0
        for distance in range(min(3, len(points))):
            i = distance if side == 0 else len(points) - 1 - distance
            points[i] += delta * (1 - distance / 3)
        points[index] = anchor
        points.insert(1 if side == 0 else len(points) - 1, anchor + normal * (0.004 if top_entry else 0.003))
        bindings.append({"wire_id": row["id"], "end": side, "feature_id": end["feature_id"], "anchor_m": list(anchor)})
    smoothed = base.smooth_trace(points)
    tube(root.name + "_visible_trace", smoothed, row["display_diameter_m"] / 2, mats[row["display_color"]], root)
    root["display_trace_start_m"], root["display_trace_end_m"] = smoothed[0], smoothed[-1]
    root["visible_exterior_entry_ids"] = json.dumps([r["feature_id"] for r in bindings])
    root["electrical_connection"] = "unresolved; entrance outline is not a metal-terminal/net assignment"
    root["hidden_continuation_created"] = False
    for binding in bindings:
        point = Vector(smoothed[0 if binding["end"] == 0 else -1])
        binding["display_centerline_to_estimated_entry_distance_m"] = (point - Vector(binding["anchor_m"])).length
    return bindings


def construct(catalog):
    roots = previous.construct(catalog)
    mats = base.palette()
    joints = {row["id"]: row for row in catalog["visible_fastener_features"]}
    for row in catalog["parts"]:
        if row["profile"] == "relay_terminal":
            terminal(roots[row["id"]], row, mats)
        elif row["profile"] == "lug_sleeve":
            lug(roots[row["id"]], row, joints[row["joint"]], mats)
    roots["I03"]["photo_visibility"] = "occluded_expected_region; required TE part, no observed wire stub"
    bpy.context.view_layer.update()
    bindings = [binding for row in catalog["visible_wire_segments"] for binding in visible_wire(row, roots, mats)]
    return roots, bindings


def main():
    if any(path.exists() for path in (OUTPUT, MESH, PREVIEW)):
        raise FileExistsError("Preserve saved revisions; use a new revision after saving")
    assert all(digest(ROOT / name) == sha for name, sha in PINNED.items())
    catalog = json.loads(CATALOG.read_text())
    roots, bindings = construct(catalog)
    scene = bpy.context.scene
    scene["scope"] = "Static v03: visible entrance alignment; physical wiring remains unresolved"
    scene["catalog_sha256"] = digest(CATALOG)
    scene.frame_start = scene.frame_end = 1
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1
    base.camera_scene()
    bpy.context.view_layer.update()
    geometry = base.export_geometry(roots)
    assert all(row["meshes"] for row in geometry.values()) and not bpy.data.actions
    MESH.write_bytes(gzip.compress(json.dumps(geometry, separators=(",", ":")).encode(), mtime=0))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    reopened = {o["photo_feature_id"]: o for o in bpy.context.scene.objects if "photo_feature_id" in o}
    bpy.context.view_layer.update()
    assert set(reopened) == set(roots) and base.export_geometry(reopened) == geometry
    assert all(o.scale == Vector((1, 1, 1)) for o in reopened.values())
    assert not bpy.data.actions
    for binding in bindings:
        wire, entry = reopened[binding["wire_id"]], reopened[binding["feature_id"]]
        anchor = entry.matrix_world @ Vector(entry["display_wire_entry_local_m"])
        field = "display_trace_start_m" if binding["end"] == 0 else "display_trace_end_m"
        binding["readback_display_endpoint_distance_m"] = (Vector(wire[field]) - anchor).length
    assert all(digest(ROOT / name) == sha for name, sha in PINNED.items())
    report = {
        "native": str(OUTPUT.relative_to(ROOT)),
        "native_sha256": digest(OUTPUT),
        "catalog_sha256": digest(CATALOG),
        "mesh_sha256": digest(MESH),
        "feature_count": len(roots),
        "id_bijection": True,
        "saved_world_meshes_exactly_equal": True,
        "feature_roots_unit_scale": True,
        "animation_actions": 0,
        "preserved_inputs": PINNED,
        "display_entry_bindings": bindings,
        "binding_scope": "display centerline versus estimated sleeve entrance; not metal contact or physical validity",
        "retired_ids_absent": all(row["id"] not in reopened for row in catalog["retired_visible_wire_segments"]),
        "full_photo_or_bom_coverage": False,
        "physical_net_correspondence_complete": False,
        "formal_physical_verdict": None,
    }
    (ROOT / "audit/hvjb_photo_model_v03_p02.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    PREVIEW.mkdir()
    for name in ("top", "oblique", "uncovered"):
        scene = bpy.context.scene
        scene.camera = bpy.data.objects["top" if name == "top" else "oblique"]
        if name == "uncovered":
            for identifier in ("P01", "P08"):
                for obj in reopened[identifier].children_recursive:
                    obj.hide_render = True
        scene.render.filepath = str(PREVIEW / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    print("STATIC_PHOTO_MODEL_SAVED", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
