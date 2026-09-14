# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Revise a pinned native with real TE headers and OP020 screw installation."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hand_line_review_geometry as geo
from allocation_product import empty, tube
from build_hand_line_review_v01 import animate_curve, animate_positions
from continuous_common import ROOT, action_world, digest, write_json
from header_review_primitives import box, cylinder

DATA = ROOT / "data/header_review_v03"
BASE_SHA = "313f3a30301afbdb4d7bc16a8b028fb0ebf62b9d953b6450efe81c13c34e7471"
OFFSETS = (-0.052, 0.072)
BAYS = ((-0.0339, 0, 0.0339), (-0.01695, 0.01695))
BOLTS = ((-0.05005, -0.01695, 0.01695, 0.05005), (-0.0331, 0, 0.0331))


def remove_group(root):
    for obj in reversed(list(root.children_recursive)):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)


def retime_previous_actions():
    count = 0
    for action in bpy.data.actions:
        for curve in action.fcurves:
            values = {}
            for attribute in ("co", "handle_left", "handle_right"):
                value = np.empty((len(curve.keyframe_points), 2), dtype=np.float32)
                curve.keyframe_points.foreach_get(attribute, value.ravel())
                values[attribute] = value
            moved = values["co"][:, 0] >= 781
            count += int(moved.sum())
            for attribute, value in values.items():
                value[moved, 0] += 780
                curve.keyframe_points.foreach_set(attribute, value.ravel())
            curve.update()
    return count


def header_templates(rows, mats):
    templates = []
    for row in rows:
        mesh = bpy.data.meshes.new("TE_" + row["part_number"] + "_official_STEP")
        mesh.from_pydata(row["vertices"], [], row["faces"])
        mesh.update()
        for key in ("orange", "steel", "rubber"):
            mesh.materials.append(mats[key])
        mesh.polygons.foreach_set("material_index", row["face_material"])
        templates.append(mesh)
    return templates


def header(name, index, templates, parent=None):
    obj = bpy.data.objects.new(name, templates[index])
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj["source_part_number"] = ("2103340-1", "2103346-2")[index]
    obj["source_geometry"] = "official TE STEP, rigid transform only; outer header without inner contact housing"
    return obj


def rounded_corner_patch(name, x, z, sx, sz, parent, mat):
    # Material outside a quarter-circle cutout, extruded through a 3 mm wall.
    radius = 0.0044
    points = [(x + sx * radius, z + sz * radius)]
    for angle in np.linspace(0, math.pi / 2, 13):
        points.append((x + sx * radius * math.cos(angle), z + sz * radius * math.sin(angle)))
    vertices = [(a, y, b) for y in (-0.003, 0) for a, b in points]
    n = len(points)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def front_wall(body, mats):
    wall = empty(body.name + "_TE_mount_wall", body)
    wall.location = (0, -0.077, 0)
    low, high = 0.046 - 0.00675, 0.046 + 0.00675
    for bottom, top in ((0, low), (high, 0.08629)):
        box(wall.name + "_band", (0.254, 0.003, top - bottom), (0, -0.0015, (bottom + top) / 2), mats["case"], wall, 0)
    centers = [offset + x for offset, bays in zip(OFFSETS, BAYS, strict=True) for x in bays]
    stops = [-0.127]
    for x in centers:
        stops.extend((x - 0.0114, x + 0.0114))
    stops.append(0.127)
    for left, right in zip(stops[::2], stops[1::2], strict=True):
        box(
            wall.name + "_pier",
            (right - left, 0.003, high - low),
            ((left + right) / 2, -0.0015, 0.046),
            mats["case"],
            wall,
            0,
        )
    for x in centers:
        for sx in (-1, 1):
            for sz in (-1, 1):
                rounded_corner_patch(
                    wall.name + "_R4_4", x + sx * 0.007, 0.046 + sz * 0.00235, sx, sz, wall, mats["case"]
                )


def screw(name, mats, parent=None):
    # Customer-supplied M4: review outline, no selected manufacturer/thread fit.
    # An 8.6 mm flange remains within TE's 8.7 mm head limit.
    root = empty(name, parent)
    cylinder(name + "_head", 0.0043, 0.0037, (0, 0.00185, 0), mats["steel"], root, (math.pi / 2, 0, 0), vertices=48)
    cylinder(name + "_shank", 0.002, 0.010, (0, 0.0087, 0), mats["steel"], root, (math.pi / 2, 0, 0), vertices=24)
    cylinder(
        name + "_drive_recess", 0.0017, 0.0001, (0, -0.00006, 0), mats["dark"], root, (math.pi / 2, 0, 0), vertices=6
    )
    return root


def replace_product_headers(templates, mats):
    roots = [o for o in bpy.context.scene.objects if o.get("stock_index") or o.name.endswith("_distinct_workpiece")]
    records = []
    for body in roots:
        for obj in list(body.children_recursive):
            case_names = ("housing_bottom", "housing_mount_flange", "housing_back", "main_port_wall")
            if obj.type == "MESH" and any(k in obj.name for k in case_names):
                obj.data = obj.data.copy()
                obj.data.materials.clear()
                obj.data.materials.append(mats["case"])
            if "front_port_wall" in obj.name and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        for obj in list(body.children):
            if "_aux_port_" in obj.name:
                remove_group(obj)
            elif "_main_port_" in obj.name:
                side = -1 if obj.name.endswith("_-1") else 1
                remove_group(obj)
                main = main_port_outline(body.name + "_main_two_pole_" + str(side), mats, body)
                main.location, main.rotation_euler.z = (side * 0.130, 0, 0.047), side * math.pi / 2
        front_wall(body, mats)
        if body.name.endswith("_distinct_workpiece") and not body.name.startswith("OP020"):
            for index in range(2):
                obj = header(body.name + "_TE_header_" + str(index), index, templates, body)
                obj.location = (OFFSETS[index], -0.08, 0.046)
                for x in BOLTS[index]:
                    for z in (-0.01375, 0.01375):
                        fastener = screw(obj.name + "_M4", mats, body)
                        fastener.location = (OFFSETS[index] + x, -0.0892, 0.046 + z)
        records.append(body.name)
    return records


def main_port_outline(name, mats, parent):
    """Reproduce the public capped two-pole outline with unselected dimensions."""
    root = empty(name, parent)
    root["reference"] = "Ampere DSC02840 / DSC02860 / DSC02878 official photographs"
    root["geometry_basis"] = "photo outline only; Amphenol exact part number and dimensions unresolved"
    box(name + "_metal_flange", (0.070, 0.003, 0.048), (0, -0.0015, 0), mats["steel"], root, 0.004)
    for x in (-0.0158, 0.0158):
        cylinder(
            name + "_metal_shell", 0.0145, 0.012, (x, -0.008, 0), mats["steel"], root, (math.pi / 2, 0, 0), vertices=64
        )
        cylinder(
            name + "_white_shipping_cap",
            0.0125,
            0.0025,
            (x, -0.015, 0),
            mats["white"],
            root,
            (math.pi / 2, 0, 0),
            vertices=64,
        )
        box(name + "_cap_tab", (0.004, 0.002, 0.004), (x, -0.015, -0.012), mats["white"], root, 0.001)
    for x in (-0.028, 0.028):
        for z in (-0.017, 0.017):
            cylinder(
                name + "_mount_head_outline",
                0.0035,
                0.002,
                (x, -0.004, z),
                mats["steel"],
                root,
                (math.pi / 2, 0, 0),
                vertices=32,
            )
    return root


def replace_robot(hand, bank):
    names = ("base", "shoulder", "upper_arm", "forearm", "wrist_1", "wrist_2", "wrist_3")
    for index, link in enumerate(names):
        action_world(bpy.data.objects["OP020__" + link], bank["OP020_links"][:, index], bank["frames"])
    action_world(bpy.data.objects["OP020__flange"], bank["OP020_flange"], bank["frames"])
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith("OP020__hand__"):
            bpy.data.objects.remove(obj, do_unlink=True)
    materials = {}
    for name, row in hand["objects"].items():
        obj = geo.mesh_object("OP020__hand__" + name, row, materials)
        obj["arm"], obj["hand_profile"], obj["contact_role"] = "OP020", "H05_TE_flange_v03", row["category"]
        action_world(obj, bank["OP020_hand_" + name], bank["frames"])


def build_station(templates, bank, schedule, mats):
    old_names = (
        "OP020_rigid_connector_supply",
        "OP020_stock_connector_",
        "OP020_stock_nest",
        "OP020_pick_nest",
        "OP020_handled_connector",
        "OP020_fixed_pusher_",
        "OP020_active_push_rod",
        "OP020_push_",
    )
    old_objects = [o.name for o in bpy.context.scene.objects if o.name.startswith(old_names)]
    for name in old_objects:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            remove_group(obj)
    geo.fixture_table("OP020_header_supply", (2.29, 0.32), (0.59, 0.28), 0.978, mats)
    for index in range(2):
        obj = header("OP020_handled_TE_" + str(index), index, templates)
        animate_positions(obj, bank[f"header_{index}_position"], bank["frames"])
        pick = bank[f"header_{index}_position"][0]
        for x in (-0.023, 0.023):
            box("OP020_header_pick_support", (0.012, 0.015, 0.012), pick + (x, -0.002, -0.0263), mats["blue"])
        for y in (0.405,):
            stock = header("OP020_TE_supply_spare_" + str(index), index, templates)
            stock.location = (pick[0], y, pick[2])
            for x in (-0.023, 0.023):
                box(
                    "OP020_header_spare_support",
                    (0.012, 0.015, 0.012),
                    (pick[0] + x, y - 0.002, pick[2] - 0.0263),
                    mats["blue"],
                )
    # One holding arm plus a fixed XYZ screwdriving unit; no second robot.
    geo.fixture_table("OP020_driver_base", (2.40, -0.50), (0.60, 0.34), 0.705, mats)
    for x in (2.11, 2.69):
        box("OP020_driver_X_support", (0.026, 0.10, 0.085), (x, -0.60, 0.758), mats["white"])
    for y in (-0.63, -0.57):
        geo.beam("OP020_driver_X_rail", (2.09, y, 0.797), (2.71, y, 0.797), 0.020, mats["steel"])
    carriage = empty("OP020_driver_X_carriage")
    box(carriage.name + "_plate", (0.11, 0.14, 0.014), (0, -0.60, 0.806), mats["white"], carriage)
    box("OP020_driver_Z_slide", (0.065, 0.050, 0.23), (0, -0.64, 0.926), mats["white"], carriage)
    animate_positions(carriage, [(p[0], 0, 0) for p in bank["driver_position"]], bank["frames"])
    z_stage = empty("OP020_driver_Z_carriage")
    box("OP020_driver_Y_rail", (0.045, 0.39, 0.025), (0, -0.48, -0.045), mats["steel"], z_stage)
    box("OP020_driver_Z_block", (0.08, 0.035, 0.065), (0, -0.614, 0), mats["blue"], z_stage)
    animate_positions(z_stage, [(p[0], 0, p[2]) for p in bank["driver_position"]], bank["frames"])
    tool = empty("OP020_screwdriver")
    # +Y is the fastening direction. The 90 mm bit leaves the header face visible.
    cylinder("OP020_screwdriver_motor", 0.018, 0.20, (0, -0.195, 0), mats["white"], tool, (math.pi / 2, 0, 0))
    cylinder("OP020_screwdriver_nose", 0.007, 0.012, (0, -0.091, 0), mats["steel"], tool, (math.pi / 2, 0, 0))
    cylinder(
        "OP020_screwdriver_bit", 0.0015, 0.092, (0, -0.043, 0), mats["steel"], tool, (math.pi / 2, 0, 0), vertices=6
    )
    box("OP020_screwdriver_mount", (0.060, 0.080, 0.020), (0, -0.18, -0.030), mats["dark"], tool)
    animate_positions(tool, bank["driver_position"], bank["frames"])
    geo.feeder("OP020_M4_screw_feeder", (1.98, -0.57), 0.96, mats)
    hose_points = []
    for p in bank["driver_position"]:
        end = p + (-0.007, -0.085, 0)
        hose_points.append(
            [(1.98, -0.57, 0.99), (2.0, -0.47, 1.11), (2.18, -0.50, 1.09), end + (-0.03, -0.06, 0.025), end]
        )
    hose = tube("OP020_M4_feed_hose", hose_points[0], 0.0045, mats["dark"])
    animate_curve(hose, np.array(hose_points), bank["frames"])
    for index, entry in enumerate(schedule):
        bolt = screw(f"OP020_M4_{index + 1:02d}", mats)
        seat = np.array(entry["tip"])
        positions = []
        angles = []
        for t, p in zip(bank["time_s"] - 12, bank["driver_position"], strict=True):
            positions.append(p if t < entry["start"] + 0.60 else seat)
            angles.append(min(max((t - entry["start"] - 0.05) / 0.55, 0), 1) * 4 * math.pi)
        poses = np.repeat(np.eye(4)[None], len(positions), axis=0)
        poses[:, :3, 3] = positions
        for j, angle in enumerate(angles):
            c, s = math.cos(angle), math.sin(angle)
            poses[j, :3, :3] = ((c, 0, s), (0, 1, 0), (-s, 0, c))
        action_world(bolt, poses, bank["frames"])
        show_time = 0 if index == 0 else schedule[index - 1]["start"] + 0.8
        for mesh in bolt.children:
            mesh.hide_render = mesh.hide_viewport = True
            mesh.keyframe_insert("hide_render", frame=1)
            mesh.keyframe_insert("hide_viewport", frame=1)
            mesh.hide_render = mesh.hide_viewport = False
            mesh.keyframe_insert("hide_render", frame=(12 + show_time) * 30 + 1)
            mesh.keyframe_insert("hide_viewport", frame=(12 + show_time) * 30 + 1)


def presentation(native):
    original = json.loads((ROOT / "data/hand_line_review_v01_presentation.json").read_text())
    ranges = [r.copy() for r in original["ranges"] if r["last_frame"] <= 360]
    shots = [
        (12, 17, "header_supply"),
        (17, 18.8, "header_cell"),
        (18.8, 26.8, "header_three_fastening"),
        (26.8, 30, "header_cell"),
        (30, 34.8, "header_supply"),
        (34.8, 37.5, "header_cell"),
        (37.5, 43.5, "header_two_fastening"),
        (43.5, 46, "header_cell"),
        (46, 52, "header_result"),
    ]
    ranges.extend(
        {"first_frame": round(a * 30) + 1, "last_frame": round(b * 30), "camera": camera} for a, b, camera in shots
    )
    for row in original["ranges"]:
        if row["first_frame"] >= 781:
            ranges.append({**row, "first_frame": row["first_frame"] + 780, "last_frame": row["last_frame"] + 780})
    phases = [r.copy() for r in original["phases"] if r["stop_s"] <= 12]
    labels = [
        (12, 18.2, "OP020｜3口ヘッダーを単腕で取り出し・筐体へ着座"),
        (18.2, 26.8, "OP020｜保持を継続し、設備側の工具でM4ねじ8本を固定"),
        (26.8, 30, "OP020｜8本の固定後に開放・次のヘッダーへ"),
        (30, 36.8, "OP020｜2口ヘッダーを取り出し・筐体へ着座"),
        (36.8, 43.5, "OP020｜保持を継続し、M4ねじ6本を固定"),
        (43.5, 46, "OP020｜固定後に開放・工具とハンドを退避"),
        (46, 52, "OP020｜筐体側外部ヘッダーの取付完了｜内部ハウジングは別工程"),
    ]
    phases.extend({"start_s": a, "stop_s": b, "label": label} for a, b, label in labels)
    phases.extend(
        {**r, "start_s": r["start_s"] + 26, "stop_s": r["stop_s"] + 26}
        for r in original["phases"]
        if r["start_s"] >= 26
    )
    cameras = {
        "header_supply": ((2.93, -0.64, 1.78), (2.29, 0.22, 1.16), 59),
        "header_cell": ((3.14, -1.34, 1.95), (2.38, -0.01, 1.16), 55),
        "header_three_fastening": ((2.16, -0.40, 1.06), (2.348, -0.080, 0.895), 58),
        "header_two_fastening": ((2.70, -0.40, 1.06), (2.472, -0.080, 0.895), 62),
        "header_result": ((2.50, -0.53, 1.17), (2.40, -0.048, 0.894), 62),
    }
    for name, (eye, target, lens) in cameras.items():
        geo.camera(name, eye, target, lens)
    return {
        **original,
        "native": native.name,
        "native_sha256": None,
        "motion": "header_review_v03/motion.npz",
        "motion_sha256": digest(DATA / "motion.npz"),
        "frame_end": 2820,
        "ranges": ranges,
        "phases": phases,
        "scope_caption": "EVジャンクションボックス｜OP020ヘッダー修正・初期動作確認",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="p01")
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    native = ROOT / ("UR15_JB_initial_hands_v03_" + options.revision + ".blend")
    assert not native.exists(), native
    baseline = ROOT / "UR15_JB_initial_hands_v02.blend"
    assert digest(baseline) == BASE_SHA
    payload = json.loads(gzip.decompress((DATA / "meshes.json.gz").read_bytes()))
    provenance = json.loads((ROOT / "audit/header_review_v03_prepare.json").read_text())
    bank = np.load(DATA / "motion.npz")
    bpy.ops.wm.open_mainfile(filepath=str(baseline))
    print("HEADER_BUILD_STAGE", "baseline loaded", flush=True)
    scene = bpy.context.scene
    count = retime_previous_actions()
    print("HEADER_BUILD_STAGE", "retimed", count, flush=True)
    # Existing fixture helpers keep their dimensions and material settings.
    # Supply only the equivalent data-block constructors for this build.
    geo.box, geo.cylinder = box, cylinder
    mats = geo.palette()
    mats["case"] = geo.material("Ampere_public_black_case", (0.035, 0.042, 0.047), 0.25, 0.35)
    templates = header_templates(payload["headers"], mats)
    bodies = replace_product_headers(templates, mats)
    print("HEADER_BUILD_STAGE", "product shapes updated", flush=True)
    replace_robot(payload["hand"], bank)
    print("HEADER_BUILD_STAGE", "robot updated", flush=True)
    build_station(templates, bank, provenance["display_bolt_schedule"], mats)
    print("HEADER_BUILD_STAGE", "station built", flush=True)
    scene.frame_end = 2820
    scene["OP020_revision"] = "TE official 3/2-bay outer headers; single arm holds while fixed XYZ unit fastens M4"
    plan = presentation(native)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    plan["native_sha256"] = digest(native)
    stem = "header_review_v03_" + options.revision
    write_json(ROOT / ("data/" + stem + "_presentation.json"), plan)
    report = {
        "native": native.name,
        "native_sha256": digest(native),
        "baseline_native_sha256": BASE_SHA,
        "updated_housing_count": len(bodies),
        "updated_housing_roots": bodies,
        "retimed_keyframes": count,
        "other_process_time_offset_s": 26,
        "mesh_inputs_sha256": digest(DATA / "meshes.json.gz"),
        "motion_sha256": digest(DATA / "motion.npz"),
        "builder_sha256": digest(Path(__file__)),
        "m4_total": 14,
        "physical_acceptance_verdict": None,
    }
    write_json(ROOT / ("audit/" + stem + "_build.json"), report)
    assert digest(baseline) == BASE_SHA
    print("HEADER_NATIVE_BUILT", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
