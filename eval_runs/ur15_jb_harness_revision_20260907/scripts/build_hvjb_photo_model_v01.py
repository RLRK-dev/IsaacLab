# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build an isolated, explicitly partial photo correspondence model [m]."""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allocation_product import empty, material, tube
from build_header_review_v03 import BAYS, BOLTS, OFFSETS, front_wall, header, header_templates, main_port_outline, screw
from continuous_common import digest
from header_review_primitives import box, cylinder

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "UR15_JB_photo_correspondence_v01_p02.blend"
PREVIEW = ROOT / "previews/hvjb_photo_v01_p02"
CAD = ROOT / "data/hvjb_photo_cad_v01.json.gz"
CATALOG = ROOT / "data/hvjb_photo_correspondence_v01.json"
PINNED = ROOT / "UR15_JB_initial_hands_v03_p03.blend"
PINNED_SHA = "2b828f98402cc95033ed62a380cdea0fb04f95bb31cae0d525b98357cd870614"


def xy(point):
    return ((point[0] - 790) / 4200, (535 - point[1]) / 4200)


def palette():
    rows = {
        "case": ((0.016, 0.021, 0.024), 0.35),
        "dark": ((0.035, 0.040, 0.044), 0.2),
        "rubber": ((0.021, 0.025, 0.029), 0),
        "steel": ((0.56, 0.58, 0.56), 0.85),
        "orange": ((0.95, 0.21, 0.015), 0.0),
        "white": ((0.88, 0.88, 0.82), 0),
        "ivory": ((0.79, 0.80, 0.67), 0),
        "translucent": ((0.33, 0.43, 0.32), 0),
        "pink": ((0.65, 0.018, 0.11), 0),
        "blue": ((0.025, 0.28, 0.63), 0),
        "black": ((0.012, 0.016, 0.02), 0),
    }
    return {name: material("Photo_" + name, color, metal, 0.32) for name, (color, metal) in rows.items()}


def feature(row):
    root = empty(row["model_id"])
    root["photo_feature_id"] = row["id"]
    root["name_ja"] = row.get("name_ja", row.get("description_ja", ""))
    root["geometry_basis"] = "photo estimated display envelope; unpublished manufacturing dimensions"
    root["photo_correspondence_complete"] = False
    root["source_photo"] = "Ampere DSC02860-1"
    return root


def block_rect(root, row, mats, top, depth, color="dark", inset=0):
    x, y, width, height = row["rect_px"]
    px, py = xy((x + width / 2, y + height / 2))
    return box(
        root.name + "_outline",
        (width / 4200 - inset, height / 4200 - inset, depth),
        (px, py, top - depth / 2),
        mats[color],
        root,
        0.0008,
    )


def ring(name, center, radius, width, mat, parent):
    points = [
        (center[0] + radius * math.cos(a), center[1] + radius * math.sin(a), center[2])
        for a in np.linspace(0, 2 * math.pi, 65)
    ]
    return tube(name, points, width, mat, parent)


def case(root, mats):
    root["overall_public_envelope_m"] = [0.29210, 0.16000, 0.09229]
    root["wall_and_boss_details"] = "photo estimate, not machining geometry"
    box("Photo_case_floor", (0.260, 0.160, 0.005), (0, 0, 0.0025), mats["case"], root)
    for x in (-0.138025, 0.138025):
        box("Photo_case_mount_flange", (0.01605, 0.160, 0.006), (x, 0, 0.003), mats["case"], root)
        for y in (-0.066675, 0.066675):
            ring("Photo_mount_pilot", (x, y, 0.0062), 0.0024, 0.0005, mats["steel"], root)
    front_wall(root, mats)
    box("Photo_case_back", (0.254, 0.003, 0.08629), (0, 0.0785, 0.043145), mats["case"], root)
    for side in (-1, 1):
        # Open band for the main port outline; machining fit is not determined.
        for bottom, top in ((0, 0.025), (0.067, 0.08629)):
            box(
                "Photo_main_wall_band",
                (0.003, 0.16, top - bottom),
                (side * 0.1285, 0, (top + bottom) / 2),
                mats["case"],
                root,
            )
        for y in (-0.059, 0.059):
            box("Photo_main_wall_side", (0.003, 0.042, 0.042), (side * 0.1285, y, 0.046), mats["case"], root)
        for y in (-0.057, 0.057):
            cylinder("Photo_lid_boss", 0.0066, 0.074, (side * 0.117, y, 0.042), mats["case"], root)
            cylinder("Photo_lid_boss_recess", 0.0052, 0.0003, (side * 0.117, y, 0.0792), mats["black"], root)
            ring("Photo_lid_boss_rim", (side * 0.117, y, 0.0794), 0.0059, 0.0004, mats["steel"], root)
    root["lid"] = "not present in the open reference photo; retained as unresolved coverage item"


def contactor(root, mats):
    x, y = xy((851, 648))
    box(root.name + "_base", (0.057, 0.055, 0.004), (x, y, 0.013), mats["dark"], root)
    cylinder(root.name + "_round_body", 0.0275, 0.044, (x, y, 0.038), mats["dark"], root, vertices=96)
    cylinder(root.name + "_top", 0.0275, 0.004, (x, y, 0.062), mats["rubber"], root, vertices=96)
    ring(root.name + "_top_rim", (x, y, 0.064), 0.0269, 0.001, mats["dark"], root)
    for angle in np.linspace(0, 2 * math.pi, 64, endpoint=False):
        rib = box(
            root.name + "_rim_rib",
            (0.001, 0.0024, 0.002),
            (x + 0.027 * math.cos(angle), y + 0.027 * math.sin(angle), 0.063),
            mats["dark"],
            root,
            0.0002,
        )
        rib.rotation_euler.z = angle + math.pi / 2
    for px, py in ((678, 649), (1027, 644)):
        tx, ty = xy((px, py))
        box(root.name + "_power_terminal_base", (0.025, 0.030, 0.022), (tx, ty, 0.026), mats["dark"], root)
        cylinder(root.name + "_power_stud_outline", 0.0043, 0.008, (tx, ty, 0.043), mats["steel"], root)
    root["manufacturer_marking"] = "GIGAVAC EPIC visible; exact orderable part not identified"


def fuse(root, row, mats):
    x, y, width, height = row["rect_px"]
    px, py = xy((x + width / 2, y + height / 2))
    length, radius = width / 4200, 0.006
    cylinder(root.name + "_body", radius, length * 0.72, (px, py, 0.059), mats["white"], root, (0, math.pi / 2, 0))
    for side in (-1, 1):
        cx = px + side * length * 0.43
        cylinder(
            root.name + "_end_cap",
            radius * 1.01,
            length * 0.18,
            (cx, py, 0.059),
            mats["steel"],
            root,
            (0, math.pi / 2, 0),
        )
        box(root.name + "_visible_clip_region", (0.007, 0.008, 0.003), (cx, py, 0.052), mats["steel"], root, 0.001)
    root["rating"] = "unassigned; do not infer electrical branch from this placement"


def relay(root, row, mats):
    block_rect(root, row, mats, 0.048, 0.022, "dark", inset=0.006)
    block_rect(root, row, mats, 0.027, 0.004, "black")


def ordinary(root, row, mats):
    settings = {
        "rear_rail": (0.062, 0.010, "steel"),
        "central_cover": (0.061, 0.0025, "dark"),
        "bus_left_upper": (0.042, 0.003, "steel"),
        "bus_right_upper": (0.042, 0.003, "steel"),
        "bus_left_lower": (0.030, 0.003, "steel"),
        "bus_right_lower": (0.038, 0.003, "steel"),
        "bus_front": (0.026, 0.003, "steel"),
        "relay_terminal": (0.057, 0.009, row.get("render_color", "ivory")),
    }
    top, depth, color = settings[row["profile"]]
    block_rect(root, row, mats, top, depth, color)


def ports(rows, roots, mats, outer, inner):
    for index, identifier in enumerate(("P16", "P17")):
        parent = roots[identifier]
        parent["geometry_basis"] = "official TE STEP rigid transform; material appearance from photo"
        part = header(parent.name + "_official_CAD", index, outer, parent)
        part.location = (OFFSETS[index], -0.08, 0.046)
        for x in BOLTS[index]:
            for z in (-0.01375, 0.01375):
                fastener = screw(parent.name + "_mount_M4", mats, parent)
                fastener.location = (OFFSETS[index] + x, -0.0892, 0.046 + z)
                fastener["basis"] = "TE mounting drawing; screw envelope, not selected supplier part"
    for identifier, side in (("P14", -1), ("P15", 1)):
        main = main_port_outline(roots[identifier].name + "_photo", mats, roots[identifier])
        main.location, main.rotation_euler.z = (side * 0.13, 0, 0.047), side * math.pi / 2
    lv = roots["P18"]
    lv.location = (*xy((425, 190)), 0.045)
    box(lv.name + "_mount", (0.023, 0.004, 0.028), (0, -0.002, 0), mats["dark"], lv)
    box(lv.name + "_photo_outline", (0.019, 0.020, 0.024), (0, 0.010, 0), mats["dark"], lv, 0.003)
    centers = [offset + x for offset, bays in zip(OFFSETS, BAYS, strict=True) for x in bays]
    for row in rows:
        if row["profile"] != "inner_header":
            continue
        mesh = bpy.data.meshes.new(row["model_id"] + "_official_STEP")
        source = inner[row["part_number"]]
        mesh.from_pydata(source["vertices"], [], source["faces"])
        mesh.materials.append(mats["orange"])
        obj = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.parent = roots[row["id"]]
        obj.rotation_euler.x = math.pi / 2
        obj.location = (centers[row["bay"]], -0.08 - 0.0311, 0.046)
        obj["part_number"] = row["part_number"]
        obj.parent["geometry_basis"] = "official STEP, no scale; common CAD nose datum and v03 outer wall datum"
        obj.parent["seating_and_contacts"] = "rigid display registration only; contacts and locking not evaluated"


def joints(rows, roots, mats):
    elevations = {
        "P02": 0.048,
        "P09": 0.042,
        "P10": 0.042,
        "P11": 0.030,
        "P12": 0.038,
        "P13": 0.027,
        "P05": 0.064,
        "P06": 0.064,
    }
    for row in rows:
        parent, identifier = row["feature_parent"], row["id"]
        z = elevations[parent]
        small = identifier in ("J03", "J04")
        radius = 0.0035 if small else 0.0045
        x, y = xy(row["center_px"])
        root = roots[identifier]
        cylinder(root.name + "_washer", radius * 1.18, 0.001, (x, y, z), mats["steel"], root)
        cylinder(root.name + "_head", radius, 0.0025, (x, y, z + 0.0018), mats["steel"], root, vertices=6)
        cylinder(root.name + "_recess", radius * 0.43, 0.0002, (x, y, z + 0.0032), mats["dark"], root, vertices=6)


def smooth_trace(points):
    extended = [points[0], *points, points[-1]]
    result = []
    for i in range(1, len(extended) - 2):
        a, b, c, d = np.asarray(extended[i - 1 : i + 3], dtype=float)
        for t in np.linspace(0, 1, 9, endpoint=False):
            result.append(
                (
                    0.5
                    * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t**3)
                ).tolist()
            )
    return [*result, points[-1]]


def wires(rows, roots, mats):
    for row in rows:
        identifier = row["id"]
        z = 0.054
        if identifier in ("W01", "W02", "W03"):
            z = 0.064
        elif identifier in ("W04", "W05", "W06", "W07"):
            z = 0.031
        elif identifier in ("W11", "W12", "W13", "W14"):
            z = 0.065
        elif identifier.startswith("WI"):
            z = 0.046
        points = [[*xy(point), z] for point in row["polyline_px"]]
        root = roots[identifier]
        tube(
            root.name + "_visible_trace",
            smooth_trace(points),
            row["display_diameter_m"] / 2,
            mats[row["display_color"]],
            root,
        )
        root["electrical_connection"] = "unresolved; open endpoints are intentional at photo occlusions"
        root["depth_and_diameter"] = "display estimate; not measured cable length or bend radius"


def camera_scene():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1440, 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Photo review environment")
    scene.world.color = (0.04, 0.04, 0.04)
    scene.view_settings.view_transform = "AgX"
    scene.render.film_transparent = True
    for name, loc, power, size in (("Key", (0.1, -0.2, 0.5), 4, 0.45), ("Fill", (-0.3, 0.2, 0.4), 2.5, 0.35)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.size = power, size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector((0, 0, 0.035)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    for name, loc in (("top", (0, -0.0001, 0.65)), ("oblique", (0.31, -0.34, 0.43))):
        data = bpy.data.cameras.new(name)
        data.type, data.ortho_scale, data.clip_start, data.clip_end = "ORTHO", 0.42, 0.001, 10
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector((0, -0.009, 0.035)) - obj.location).to_track_quat("-Z", "Y").to_euler()
        if name == "top":
            obj.rotation_euler = (0, 0, 0)
    scene.camera = bpy.data.objects["top"]


def export_geometry(roots):
    evaluated = bpy.context.evaluated_depsgraph_get()
    result = {}
    for identifier, root in roots.items():
        parts = []
        for obj in root.children_recursive:
            if obj.type not in {"MESH", "CURVE"}:
                continue
            obj_eval = obj.evaluated_get(evaluated)
            mesh = obj_eval.to_mesh()
            mesh.calc_loop_triangles()
            vertices = [list(obj.matrix_world @ v.co) for v in mesh.vertices]
            for index, mat in enumerate(mesh.materials):
                faces = [list(t.vertices) for t in mesh.loop_triangles if t.material_index == index]
                if not faces:
                    continue
                color = mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value[:]
                parts.append({"name": obj.name, "vertices": vertices, "faces": faces, "color": list(color)})
            obj_eval.to_mesh_clear()
        result[identifier] = {"model_id": root.name, "basis": root["geometry_basis"], "meshes": parts}
    return result


def main():
    if OUTPUT.exists():
        raise FileExistsError("Preserve this static revision; select a new output revision for changes")
    assert digest(PINNED) == PINNED_SHA
    catalog = json.loads(CATALOG.read_text())
    outer_data = json.loads(gzip.decompress((ROOT / "data/header_review_v03/meshes.json.gz").read_bytes()))
    inner_data = json.loads(gzip.decompress(CAD.read_bytes()))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = palette()
    rows = catalog["parts"] + catalog["visible_fastener_features"] + catalog["visible_wire_segments"]
    roots = {row["id"]: feature(row) for row in rows}
    templates = header_templates(outer_data["headers"], mats)
    skip = {"header_three", "header_two", "inner_header", "main_left", "main_right", "lv_header"}
    functions = {
        "case": lambda root, row: case(root, mats),
        "contactor": lambda root, row: contactor(root, mats),
        "fuse": lambda root, row: fuse(root, row, mats),
        "relay": lambda root, row: relay(root, row, mats),
    }
    for row in catalog["parts"]:
        if row["profile"] in skip:
            continue
        functions.get(row["profile"], lambda root, row: ordinary(root, row, mats))(roots[row["id"]], row)
    ports(catalog["parts"], roots, mats, templates, inner_data)
    joints(catalog["visible_fastener_features"], roots, mats)
    wires(catalog["visible_wire_segments"], roots, mats)
    for row in catalog["required_functions"]:
        if not row["matched_photo_ids"]:
            obj = empty("UNLOCATED_" + row["id"])
            obj["name_ja"], obj["required_quantity"] = row["name_ja"], row["quantity"]
            obj["placement"] = "not located in public photos; no substitute geometry"
    scene = bpy.context.scene
    scene["scope"] = "Partial static correspondence; internal topology incomplete; no motion acceptance"
    scene["catalog_sha256"] = digest(CATALOG)
    scene.frame_start = scene.frame_end = 1
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1
    camera_scene()
    bpy.context.view_layer.update()
    geometry = export_geometry(roots)
    assert set(geometry) == {row["id"] for row in rows}
    assert all(row["meshes"] for row in geometry.values())
    assert len(bpy.data.actions) == 0
    out_mesh = ROOT / "data/hvjb_photo_model_v01_p02.json.gz"
    out_mesh.write_bytes(gzip.compress(json.dumps(geometry, separators=(",", ":")).encode(), mtime=0))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    reopened = {o["photo_feature_id"]: o for o in bpy.context.scene.objects if "photo_feature_id" in o}
    assert set(reopened) == set(roots)
    assert all(o.scale == Vector((1, 1, 1)) for o in reopened.values())
    assert len(bpy.data.actions) == 0
    assert digest(PINNED) == PINNED_SHA
    bpy.context.view_layer.update()
    assert export_geometry(reopened) == geometry
    audit = {
        "native": str(OUTPUT.relative_to(ROOT)),
        "native_sha256": digest(OUTPUT),
        "catalog_sha256": digest(CATALOG),
        "inner_cad_sha256": digest(CAD),
        "mesh_sha256": digest(out_mesh),
        "photo_ids_in_catalog_and_saved_scene": sorted(reopened),
        "id_bijection": True,
        "saved_world_meshes_exactly_equal": True,
        "saved_feature_roots": len(reopened),
        "animation_actions": 0,
        "old_v03_unchanged": True,
        "old_v03_sha256": digest(PINNED),
        "unlocated_required_ids": [r["id"] for r in catalog["required_functions"] if not r["matched_photo_ids"]],
        "full_photo_or_bom_coverage": False,
        "physical_net_correspondence_complete": False,
        "geometry_basis": "TE source shapes rigid only; other outlines/positions/heights/diameters estimated",
        "formal_physical_verdict": None,
    }
    (ROOT / "audit/hvjb_photo_model_v01_p02.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    PREVIEW.mkdir(parents=True, exist_ok=False)
    for name in ("top", "oblique"):
        bpy.context.scene.camera = bpy.data.objects[name]
        bpy.context.scene.render.filepath = str(PREVIEW / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    print("STATIC_PHOTO_MODEL_SAVED", json.dumps(audit, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
