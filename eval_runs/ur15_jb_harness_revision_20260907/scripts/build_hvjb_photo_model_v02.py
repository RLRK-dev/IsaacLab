# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build a static evidence-linked interior; unpublished dimensions remain estimates [m]."""

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
import build_hvjb_photo_model_v01 as base
from allocation_product import empty, material, tube
from build_hvjb_photo_catalog_v01 import digest
from header_review_primitives import box, cylinder

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "UR15_JB_photo_correspondence_v02_p02.blend"
CATALOG = ROOT / "data/hvjb_photo_correspondence_v02_p02.json"
MESH = ROOT / "data/hvjb_photo_model_v02_p02.json.gz"
PREVIEW = ROOT / "previews/hvjb_photo_v02_p02"
PINNED = {
    "UR15_JB_photo_correspondence_v01_p02.blend": "f8c8b9fe3e8503cb2cdc21b4dc1dd0b3d7e547b7bbf0573a415be569f77cad8c",
    "UR15_JB_initial_hands_v03_p03.blend": "2b828f98402cc95033ed62a380cdea0fb04f95bb31cae0d525b98357cd870614",
}
FUSE_MOUNTS = ((-0.0492857, 0.0054762), (0.0192857, 0.0716667))


def mesh_object(name, vertices, faces, mat, parent):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def annulus(name, center, outer, inner, depth, mat, parent):
    vertices = []
    for z in (-depth / 2, depth / 2):
        for radius in (outer, inner):
            vertices.extend(
                (radius * math.cos(a), radius * math.sin(a), z) for a in np.linspace(0, math.tau, 48, endpoint=False)
            )
    faces = []
    for i in range(48):
        j = (i + 1) % 48
        faces.extend(
            (
                (i, j, j + 96, i + 96),
                (i + 48, i + 144, j + 144, j + 48),
                (i, i + 48, j + 48, j),
                (i + 96, j + 96, j + 144, i + 144),
            )
        )
    obj = mesh_object(name, vertices, faces, mat, parent)
    obj.location = center
    return obj


def contactor(root, mats):
    base.contactor(root, mats)
    x, y = base.xy((851, 648))
    for angle in np.linspace(0, math.tau, 64, endpoint=False):
        obj = box(
            root.name + "_vertical_rib",
            (0.0008, 0.0014, 0.034),
            (x + 0.0274 * math.cos(angle), y + 0.0274 * math.sin(angle), 0.043),
            mats["dark"],
            root,
            0.0002,
        )
        obj.rotation_euler.z = angle + math.pi / 2


def fuse_location(row):
    a, b = FUSE_MOUNTS[row["display_fuse_column"]]
    return ((a + b) / 2, 0.057, 0.063 - 0.017 * row["display_fuse_level"])


def auxiliary_fuse(root, row, mats):
    x, y, z = fuse_location(row)
    length, radius = 0.039, 0.0052
    cylinder(root.name + "_ceramic_outline", radius, length, (x, y, z), mats["white"], root, (0, math.pi / 2, 0))
    for side in (-1, 1):
        cx = x + side * (length / 2 - 0.0036)
        cylinder(root.name + "_cap", radius * 1.02, 0.0072, (cx, y, z), mats["steel"], root, (0, math.pi / 2, 0))
        # Visible spring wrap only; the supplier's clip drawing is not available.
        points = [(cx, y + 0.0055 * math.cos(a), z + 0.0055 * math.sin(a)) for a in np.linspace(-2.5, 2.5, 36)]
        tube(root.name + "_spring_clip_outline", points, 0.0008, mats["steel"], root)
        box(root.name + "_clip_back", (0.009, 0.0015, 0.011), (cx, 0.0635, z), mats["steel"], root, 0.0004)
    band = "red" if row["id"] == "P21" else "yellow" if row["display_fuse_level"] else "green"
    cylinder(
        root.name + "_visible_label_band",
        radius * 1.015,
        0.0016,
        (x + 0.003, y, z),
        mats[band],
        root,
        (0, math.pi / 2, 0),
    )
    root["observed_marking"] = row["observed_marking"]
    root["electrical_port_assignment"] = "unresolved; color does not establish circuit assignment"


def fuse_panel(root, mats):
    box(root.name + "_backing_outline", (0.141, 0.004, 0.061), (0.012, 0.067, 0.045), mats["dark"], root, 0.0007)
    root["support"] = "plate outline estimated; material, fastener stack and support path unresolved"


def cover(root, mats):
    cx, cy = base.xy((843, 435))
    vertices = []
    for x in (cx - 0.0295, cx + 0.0295):
        for radius in (0.0200, 0.0212):
            vertices.extend(
                (x, cy + radius * math.cos(a), 0.041 + radius * math.sin(a)) for a in np.linspace(0, math.pi, 49)
            )
    faces = []
    for i in range(48):
        faces.extend(
            (
                (i, i + 1, i + 99, i + 98),
                (i + 49, i + 147, i + 148, i + 50),
                (i, i + 49, i + 50, i + 1),
                (i + 98, i + 99, i + 148, i + 147),
            )
        )
    faces.extend(((0, 98, 147, 49), (48, 97, 195, 146)))
    mesh_object(root.name + "_curved_cover_outline", vertices, faces, mats["rubber"], root)


def main_fuse(root, mats):
    cx, cy = base.xy((843, 435))
    cylinder(root.name + "_body_outline", 0.018, 0.050, (cx, cy, 0.041), mats["white"], root, (0, math.pi / 2, 0))
    for side in (-1, 1):
        cylinder(
            root.name + "_end_outline",
            0.0182,
            0.005,
            (cx + side * 0.027, cy, 0.041),
            mats["steel"],
            root,
            (0, math.pi / 2, 0),
        )
        box(
            root.name + "_flat_terminal_outline",
            (0.024, 0.020, 0.003),
            (cx + side * 0.040, cy, 0.041),
            mats["steel"],
            root,
            0.0005,
        )
    root["hidden_geometry"] = "manufacturer's displayed cylindrical sample; installed order code not confirmed"


def bent_bar(root, row, mats):
    left = row["id"] == "P09"
    x = -0.059 if left else 0.074
    length = 0.081 if left else 0.053
    y = 0.0235 if left else 0.0305
    # Represent the exposed vertical sheet and terminal foot; no hidden electrical continuity claim.
    box(root.name + "_upright_visible_sheet", (length, 0.003, 0.023), (x, y, 0.0435), mats["steel"], root, 0.0004)
    tx, ty = base.xy((394, 489) if left else (1170, 490))
    box(root.name + "_terminal_foot", (0.022, 0.026, 0.003), (tx, ty + 0.003, 0.032), mats["steel"], root, 0.0005)
    box(root.name + "_foot_bend", (0.022, 0.003, 0.012), (tx, y, 0.036), mats["steel"], root, 0.0005)
    root["continuity"] = "exposed sheet regions only; hidden bend and main-fuse joint stack unresolved"


def joint_transform(row, parts):
    if "fuse_side" in row:
        fuse = parts[row["feature_parent"]]
        x = FUSE_MOUNTS[fuse["display_fuse_column"]][int(row["fuse_side"] > 0)]
        return (x, 0.0595, fuse_location(fuse)[2]), (math.pi / 2, 0, 0)
    z = {"P02": 0.048, "P09": 0.034, "P10": 0.034, "P11": 0.030, "P12": 0.038, "P13": 0.029}
    return (*base.xy(row["center_px"]), z[row["feature_parent"]]), (0, 0, 0)


def socket_head(root, mats, radius):
    cylinder(root.name + "_washer", radius * 1.18, 0.0008, (0, 0, 0), mats["steel"], root)
    # A rounded cap with an actual open six-sided recess, rather than a hex head with painted dot.
    levels = [(radius, 0.0005), (radius * 0.98, 0.0013), (radius * 0.85, 0.0025), (radius * 0.66, 0.0033)]
    vertices = []
    for r, z in levels:
        vertices.extend((r * math.cos(a), r * math.sin(a), z) for a in np.linspace(0, math.tau, 48, endpoint=False))
    for z in (0.0033, 0.0014):
        for i in range(48):
            side, t = divmod(i, 8)
            a, b = side * math.tau / 6, (side + 1) * math.tau / 6
            vertices.append(
                (
                    radius * 0.44 * ((1 - t / 8) * math.cos(a) + t / 8 * math.cos(b)),
                    radius * 0.44 * ((1 - t / 8) * math.sin(a) + t / 8 * math.sin(b)),
                    z,
                )
            )
    faces = []
    for layer in range(5):
        for i in range(48):
            j = (i + 1) % 48
            faces.append((layer * 48 + i, layer * 48 + j, (layer + 1) * 48 + j, (layer + 1) * 48 + i))
    faces.append(tuple(range(240, 288)))
    mesh_object(root.name + "_round_socket_head", vertices, faces, mats["steel"], root)


def joints(rows, roots, parts, mats):
    for row in rows:
        root = roots[row["id"]]
        root.location, root.rotation_euler = joint_transform(row, parts)
        if row["display_head_form"] == "hex_nut_on_stud":
            cylinder(root.name + "_washer", 0.006, 0.001, (0, 0, 0), mats["steel"], root)
            cylinder(root.name + "_hex_nut", 0.005, 0.004, (0, 0, 0.0025), mats["steel"], root, vertices=6)
            cylinder(root.name + "_exposed_stud", 0.003, 0.006, (0, 0, 0.006), mats["steel"], root)
        else:
            socket_head(root, mats, 0.0031 if row["id"] in {"J03", "J04"} else 0.0044)


def lugs(rows, roots, all_joints, parts, mats):
    for row in rows:
        if row["profile"] != "lug_sleeve":
            continue
        root, joint = roots[row["id"]], all_joints[row["joint"]]
        loc, rot = joint_transform(joint, parts)
        root.location, root.rotation_euler = loc, rot
        annulus(root.name + "_visible_ring", (0, 0, -0.0009), 0.0057, 0.0025, 0.001, mats["steel"], root)
        dx = row["sleeve_direction_px"][0] - joint["center_px"][0]
        dy = joint["center_px"][1] - row["sleeve_direction_px"][1]
        direction = Vector((dx, 0 if "fuse_side" in joint else dy, 0)).normalized()
        tube(root.name + "_crimp_barrel", [direction * 0.0045, direction * 0.011], 0.0024, mats["steel"], root)
        tube(root.name + "_black_sleeve", [direction * 0.007, direction * 0.020], 0.0028, mats["rubber"], root)


def construct(catalog):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = base.palette()
    for color, rgb in {"green": (0.01, 0.42, 0.19), "yellow": (0.95, 0.72, 0.04), "red": (0.75, 0.02, 0.025)}.items():
        mats[color] = material("Photo_" + color, rgb, 0, 0.4)
    rows = catalog["parts"] + catalog["visible_fastener_features"] + catalog["visible_wire_segments"]
    roots = {row["id"]: base.feature(row) for row in rows}
    for row in rows:
        roots[row["id"]]["source_photo"] = row["photo"]
    parts = {row["id"]: row for row in catalog["parts"]}
    handlers = {
        "case": lambda r, p: base.case(r, mats),
        "contactor": lambda r, p: contactor(r, mats),
        "fuse": lambda r, p: auxiliary_fuse(r, p, mats),
        "fuse_panel": lambda r, p: fuse_panel(r, mats),
        "main_fuse": lambda r, p: main_fuse(r, mats),
        "central_cover": lambda r, p: cover(r, mats),
        "relay": lambda r, p: base.relay(r, p, mats),
        "bus_left_upper": lambda r, p: bent_bar(r, p, mats),
        "bus_right_upper": lambda r, p: bent_bar(r, p, mats),
    }
    skip = {"header_three", "header_two", "inner_header", "main_left", "main_right", "lv_header", "lug_sleeve"}
    for row in catalog["parts"]:
        if row["profile"] not in skip:
            handlers.get(row["profile"], lambda r, p: base.ordinary(r, p, mats))(roots[row["id"]], row)
    outer = json.loads(gzip.decompress((ROOT / "data/header_review_v03/meshes.json.gz").read_bytes()))
    inner = json.loads(gzip.decompress(base.CAD.read_bytes()))
    base.ports(catalog["parts"], roots, mats, base.header_templates(outer["headers"], mats), inner)
    joints(catalog["visible_fastener_features"], roots, parts, mats)
    lugs(catalog["parts"], roots, {j["id"]: j for j in catalog["visible_fastener_features"]}, parts, mats)
    base.wires(catalog["visible_wire_segments"], roots, mats)
    for row in catalog["required_functions"]:
        if not row["matched_photo_ids"]:
            obj = empty("UNRESOLVED_" + row["id"])
            obj["name_ja"], obj["required_quantity"] = row["name_ja"], row["quantity"]
            obj["unresolved"] = row.get("note_ja", "physical assignment unresolved")
    return roots


def main():
    if OUTPUT.exists() or MESH.exists() or PREVIEW.exists():
        raise FileExistsError("Preserve this static revision; use a new revision for any retry after saving")
    assert all(digest(ROOT / name) == sha for name, sha in PINNED.items())
    catalog = json.loads(CATALOG.read_text())
    roots = construct(catalog)
    scene = bpy.context.scene
    scene["scope"] = "Static v02; uncovered inventory improved; physical wiring correspondence remains incomplete"
    scene["catalog_sha256"] = digest(CATALOG)
    scene.frame_start = scene.frame_end = 1
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1
    base.camera_scene()
    bpy.context.view_layer.update()
    geometry = base.export_geometry(roots)
    assert all(row["meshes"] for row in geometry.values())
    assert len(bpy.data.actions) == 0
    MESH.write_bytes(gzip.compress(json.dumps(geometry, separators=(",", ":")).encode(), mtime=0))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    reopened = {o["photo_feature_id"]: o for o in bpy.context.scene.objects if "photo_feature_id" in o}
    bpy.context.view_layer.update()
    assert set(reopened) == set(roots) and base.export_geometry(reopened) == geometry
    assert all(o.scale == Vector((1, 1, 1)) for o in reopened.values())
    assert len(bpy.data.actions) == 0
    assert all(digest(ROOT / name) == sha for name, sha in PINNED.items())
    audit = {
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
        "aux_fuse_ids": catalog["physical_aux_fuses"]["photo_ids"],
        "main_fuse_id": "P22",
        "main_fuse_cover_id": "P08",
        "full_photo_or_bom_coverage": False,
        "physical_net_correspondence_complete": False,
        "formal_physical_verdict": None,
    }
    (ROOT / "audit/hvjb_photo_model_v02_p02.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    PREVIEW.mkdir()
    for name in ("top", "oblique", "uncovered"):
        bpy.context.scene.camera = bpy.data.objects["top" if name == "top" else "oblique"]
        if name == "uncovered":
            # View-only visibility; native remains fully assembled and has no animation.
            for identifier in ("P01", "P08"):
                for obj in reopened[identifier].children_recursive:
                    obj.hide_render = True
        bpy.context.scene.render.filepath = str(PREVIEW / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    print("STATIC_PHOTO_MODEL_SAVED", json.dumps(audit, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
