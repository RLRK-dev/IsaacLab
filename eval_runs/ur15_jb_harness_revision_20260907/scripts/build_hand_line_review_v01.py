# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build a new native initial-hand process review without changing v06 [m, s]."""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hand_line_review_geometry as geo
import hand_line_review_motion as motion
from allocation_product import box, cylinder, empty, tube
from continuous_common import ROOT, action_world, digest, write_json

DATA = ROOT / "data/hand_line_review_v01"
NATIVE = ROOT / "UR15_JB_initial_hands_v02.blend"
MATERIALS = {}


def animate_positions(obj, positions, frames, angles=None):
    poses = np.repeat(np.eye(4)[None], len(positions), axis=0)
    poses[:, :3, 3] = positions
    if angles is not None:
        for pose, angle in zip(poses, angles, strict=True):
            pose[:3, :3] = motion.transform(rpy=(0, 0, angle))[:3, :3]
    action_world(obj, poses, frames)


def build_robots(payload, bank, mats):
    parts = {}
    links = ("base", "shoulder", "upper_arm", "forearm", "wrist_1", "wrist_2", "wrist_3")
    hand_kinds = {"OP020": "H05", "A_hold": "H01", "B_left": "H04", "B_right": "H04", "C": "H05"}
    geometry_data = {}
    for name, row in payload["robot"].items():
        obj = geo.mesh_object("reusable_ur15_" + name, row, MATERIALS)
        geometry_data[name] = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
    for name, mounting in payload["bases"].items():
        group = []
        for index, link in enumerate(links):
            frame = empty(name + "__" + link)
            frame["role"] = "robot_link"
            action_world(frame, bank[name + "_links"][:, index], bank["frames"])
            for key, row in payload["robot"].items():
                if row["link"] != link:
                    continue
                obj = bpy.data.objects.new(name + "__" + key, geometry_data[key])
                bpy.context.collection.objects.link(obj)
                obj.parent, obj.matrix_basis = frame, Matrix(row["local"])
                obj["arm"] = name
                obj["robot_link"] = link
                group.append(obj.name)
        flange = empty(name + "__flange")
        action_world(flange, bank[name + "_flange"], bank["frames"])
        camera_mount = flange
        if name.startswith("B_"):
            camera_mount = empty(name + "__hand_flange")
            action_world(camera_mount, bank[name + "_hand_flange"], bank["frames"])
            length = motion.B_MOUNTS[name][0]
            adapter = cylinder(name + "_flange_extension", 0.025, length, (0, 0, length / 2), mats["steel"], flange)
            adapter["arm"] = name
            for z in (0.005, length - 0.005):
                collar = cylinder(name + "_extension_flange", 0.0315, 0.010, (0, 0, z), mats["dark"], flange)
                collar["arm"] = name
        geo.onhand_camera(name + "_monocular", mats, camera_mount)
        if name in hand_kinds:
            for key, row in payload["hands"][hand_kinds[name]]["objects"].items():
                obj = geo.mesh_object(name + "__hand__" + key, row, MATERIALS)
                action_world(obj, bank[name + "_hand_" + key], bank["frames"])
                obj["arm"], obj["hand_profile"] = name, hand_kinds[name]
                obj["contact_role"] = row["category"]
                group.append(obj.name)
        parts[name] = group
    geo.robot_pedestal("OP020_single", 2.4, 0.91, False, mats)
    geo.robot_pedestal("OP030_A_dual", 4.8, -0.82, True, mats)
    geo.robot_pedestal("OP030_B_dual", motion.B_ROBOT_X, 0.82, True, mats)
    geo.robot_pedestal("OP030_C_single_sample", 9.6, -0.91, False, mats)
    return parts


def body_group(template, name, position, mats, stage):
    body = geo.clone_group(template, name)
    body.location = position
    if stage >= 2:
        geo.add_ports(body, mats, omit_front_last=stage == 2)
    if stage >= 3:
        geo.internals(body, mats, include_contactor=stage >= 4, include_wire=False)
    return body


def build_op010(template, bank, mats):
    geo.fixture_table("OP010_stock_20", (-0.18, -0.99), (1.71, 0.92), 0.813, mats)
    parts = []
    for row in range(4):
        for col in range(5):
            name = f"OP010_stock_body_{row * 5 + col + 1:02d}"
            position = motion.stock_position(row, col)
            body = body_group(template, name, position, mats, 1)
            body["stock_index"] = row * 5 + col + 1
            parts.append(body)
            for x in (-0.112, 0.112):
                box(name + "_support", (0.025, 0.135, 0.012), position + (x, 0, -0.006), mats["blue"])
    frames, times = bank["frames"], bank["time_s"]
    states = [motion.op010_state(t) for t in times]
    animate_positions(parts[0], [s[2] for s in states], frames)
    y_stage, x_stage, z_stage, jaws = geo.xyz_gantry(mats)
    animate_positions(y_stage, [(0, s[0][1], 0) for s in states], frames)
    animate_positions(x_stage, [(s[0][0], s[0][1], 0) for s in states], frames)
    animate_positions(z_stage, [s[0] for s in states], frames)
    for sign, jaw in zip((-1, 1), jaws, strict=True):
        animate_positions(jaw, [(0, sign * (0.090 + 0.022 * (1 - s[1])), 0) for s in states], frames)
    return [obj.name for obj in parts]


def build_op020(bank, mats):
    geo.fixture_table("OP020_rigid_connector_supply", (2.12, 0.38), (0.32, 0.26), 0.956, mats)
    for i in range(5):
        unit = geo.connector("OP020_stock_connector_" + str(i), mats)
        unit.location = (2.02 + i * 0.05, 0.46, 0.978)
        box("OP020_stock_nest", (0.012, 0.012, 0.010), (unit.location.x, 0.46, 0.961), mats["blue"])
    box("OP020_pick_nest", (0.012, 0.012, 0.010), (2.12, 0.38, 0.961), mats["blue"])
    handled = geo.connector("OP020_handled_connector", mats)
    states = [motion.op020_state(t) for t in bank["time_s"]]
    animate_positions(handled, [s[2] for s in states], bank["frames"])
    for side in (-1, 1):
        # Retain two independent fixed push systems; only the front sample
        # is animated here. Other connection operations are not certified.
        name = "OP020_fixed_pusher_" + str(side)
        y = -0.33 if side == -1 else 0.30
        cylinder(
            name + "_body",
            0.025,
            0.10,
            (2.496, y, motion.BODY_BOTTOM + 0.046),
            mats["white"],
            rotation=(math.pi / 2, 0, 0),
        )
        beam = geo.beam(name + "_stand", (2.496, y, 0.55), (2.496, y, motion.BODY_BOTTOM + 0.046), 0.04, mats["steel"])
        beam["fixed_axis"] = "Y"
    rod = empty("OP020_active_push_rod")
    # The 176 mm rod keeps its rear end inside the cylinder over the 46 mm
    # stroke. The front face follows the connector's rear plane at y - 13 mm.
    cylinder("OP020_push_rod_mesh", 0.006, 0.176, (0, 0, 0), mats["steel"], rod, (math.pi / 2, 0, 0))
    box("OP020_push_face", (0.016, 0.006, 0.016), (0, 0.091, 0), mats["pad"], rod)
    animate_positions(rod, [(2.496, -0.252 + 0.046 * s[3], motion.BODY_BOTTOM + 0.046) for s in states], bank["frames"])


def source_targets(name, rows):
    root = empty(name)
    for key, row in rows.items():
        obj = geo.mesh_object(name + "__" + key, row, MATERIALS, root)
        obj.matrix_basis = Matrix(row["local"])
    return root


def build_a(payload, bank, mats):
    geo.fixture_table("A_twenty_component_tray", (4.34, -0.33), (0.36, 0.29), 0.972, mats)
    rows = payload["targets"]["H01"]
    held = source_targets("A_handled_round_component", rows)
    states = [motion.a_state(t) for t in bank["time_s"]]
    animate_positions(held, [s[2] for s in states], bank["frames"])
    for i in range(20):
        if i == 0:
            continue
        item = source_targets("A_stock_component_" + str(i + 1), rows)
        item.location = (4.47 - i % 5 * 0.067, -0.43 + i // 5 * 0.067, 0.978)
    geo.feeder("A_bolt_supply", (5.07, -0.23), 1.025, mats)
    tool = geo.spindle("A_permanently_mounted_driver", mats, length=0.48)
    animate_positions(tool, [s[3] for s in states], bank["frames"])
    # Endpoint-attached illustrative feed hose; no hose-load or slack model.
    hose_samples = []
    for state in states:
        end = state[3] + (0.017, 0, 0.373)
        hose_samples.append([(5.07, -0.20, 1.02), (5.26, -0.25, 1.40), (5.26, -0.25, 1.83), end + (0.12, 0, 0.10), end])
    hose = tube("A_bolt_feed_hose", hose_samples[0], 0.008, mats["dark"])
    animate_curve(hose, np.asarray(hose_samples), bank["frames"])
    bolt_roots = []
    for sign in (-1, 1):
        bolt = empty("A_fastener_" + str(sign))
        cylinder(bolt.name + "_head", 0.0047, 0.004, (0, 0, 0), mats["steel"], bolt, vertices=6)
        cylinder(bolt.name + "_shank", 0.0025, 0.013, (0, 0, -0.0085), mats["steel"], bolt, vertices=24)
        positions = []
        for t, state in zip(bank["time_s"], states, strict=True):
            local = motion.cycle_time(t)
            seat = np.array((4.745, sign * 0.045, motion.PART_Z + 0.002))
            done = 7.7 if sign == -1 else 10.6
            positions.append(state[3] - (0, 0, 0.002) if local < done else seat - (0, 0, 0.002))
        start, stop = (6.7, 7.7) if sign == -1 else (9.1, 10.6)
        angles = [4 * math.pi * motion.between(motion.cycle_time(t), start, stop) for t in bank["time_s"]]
        animate_positions(bolt, positions, bank["frames"], angles)
        # Only one bolt is shown in the nose at a time; the feeder advances
        # the next bolt during the intervening free move.
        if sign == 1:
            for obj in bolt.children:
                for t in (0, 26, 40, 54):
                    obj.hide_render = True
                    obj.keyframe_insert("hide_render", frame=t * 30 + 1)
                    obj.hide_render = False
                    obj.keyframe_insert("hide_render", frame=(t + 8) * 30 + 1)
        bolt_roots.append(bolt.name)
    return bolt_roots


def hermite(first, last, first_direction, last_direction, handle):
    u = np.linspace(0, 1, 49)[:, None]
    return (
        (2 * u**3 - 3 * u**2 + 1) * first
        + (u**3 - 2 * u**2 + u) * first_direction * handle
        + (-2 * u**3 + 3 * u**2) * last
        + (u**3 - u**2) * last_direction * handle
    )


def cable_points(poses):
    first = np.array(poses[0]) @ (0, 0.087, -0.006, 1)
    last = np.array(poses[1]) @ (0, 0.087, -0.006, 1)
    d0, d1 = poses[0][:3, 1], -poses[1][:3, 1]
    # The straight stock has 0.400 m between lug centers. Its middle segment
    # is 0.226 m after the two unchanged 87 mm source endpoint sections.
    length = 0.226
    lo, hi = 0.0, 0.8
    for _ in range(34):
        handle = (lo + hi) / 2
        pts = hermite(first[:3], last[:3], d0, d1, handle)
        if np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() > length:
            hi = handle
        else:
            lo = handle
    return hermite(first[:3], last[:3], d0, d1, (lo + hi) / 2)


def animate_curve(obj, samples, frames):
    curve = obj.data
    action = bpy.data.actions.new(obj.name + "_prescribed_shape")
    curve.animation_data_create()
    curve.animation_data.action = action
    if action.slots:
        curve.animation_data.action_slot = action.slots[0]
    for point in range(samples.shape[1]):
        for coordinate in range(3):
            values = samples[:, point, coordinate]
            if np.ptp(values) < 1e-9:
                continue
            track = action.fcurves.new(f"splines[0].points[{point}].co", index=coordinate)
            track.keyframe_points.add(len(frames))
            track.keyframe_points.foreach_set("co", np.c_[frames, values].astype(np.float32).ravel())
            for key in track.keyframe_points:
                key.interpolation = "LINEAR"
    if action.slots:
        curve.animation_data.action_slot = action.slots[0]


def build_b(payload, bank, mats):
    geo.fixture_table("B_ten_parallel_wire_tray", (7.12, 0.414), (0.48, 0.54), 0.996, mats)
    endpoint_rows = {key: row for key, row in payload["targets"]["H04"].items() if key != "illustrative_busbar_coupon"}
    for index in range(10):
        for x in (7.10, 7.14):
            box(
                f"B_wire_mid_support_{index}_{x}", (0.015, 0.026, 0.016), (x, 0.18 + index * 0.052, 1.004), mats["blue"]
            )
    for index in range(1, 10):
        y = 0.18 + index * 0.052
        for side, x in enumerate((6.92, 7.32)):
            part = source_targets(f"B_stock_wire_{index + 1}_end_{side}", endpoint_rows)
            part.location, part.rotation_euler.z = (x, y, 1.025), -math.pi / 2 if side == 0 else math.pi / 2
        tube(f"B_stock_wire_{index + 1}_middle", [(7.007, y, 1.019), (7.233, y, 1.019)], 0.007, mats["orange"])
    states = [motion.cable_frames(t) for t in bank["time_s"]]
    for index in range(2):
        part = source_targets("B_handled_endpoint_" + str(index), endpoint_rows)
        action_world(part, np.array([state[2][index] for state in states]), bank["frames"])
        tool = geo.spindle("B_equipment_driver_" + str(index), mats)
        endpoint = np.array((7.115, -0.045, motion.CABLE_Z)) if index == 0 else np.array((7.285, 0.045, motion.CABLE_Z))
        tool_positions = [motion.b_tool_position(t, index) for t in bank["time_s"]]
        animate_positions(tool, tool_positions, bank["frames"])
        # Each equipment spindle parks outboard on X before Z insertion.
        # These are provisional machine slides, independently of robot arms.
        side = -1 if index == 0 else 1
        outboard = endpoint[0] + side * (0.34 if index == 0 else 0.51)
        geo.beam(
            f"B_tool_column_{index}", (outboard, endpoint[1], 0.05), (outboard, endpoint[1], 1.20), 0.045, mats["white"]
        )
        geo.beam(
            f"B_tool_x_rail_{index}",
            (outboard, endpoint[1], 1.20),
            (endpoint[0] + side * 0.045, endpoint[1], 1.20),
            0.027,
            mats["steel"],
        )
        slide = box(f"B_tool_z_slide_{index}", (0.025, 0.035, 0.20), (0, 0, 0), mats["white"])
        animate_positions(slide, [(p[0] + side * 0.045, p[1], 1.30) for p in tool_positions], bank["frames"])
        bracket = box(f"B_tool_drive_bracket_{index}", (0.048, 0.020, 0.018), (0, 0, 0), mats["steel"])
        animate_positions(bracket, [p + (side * 0.020, 0, 0.34) for p in tool_positions], bank["frames"])
        cylinder(f"B_tool_z_guide_rod_{index}", 0.004, 0.22, (side * 0.045, 0, 0.45), mats["steel"], tool)
        geo.feeder("B_bolt_feeder_" + str(index), (7.60 + 0.25 * index, -0.47), 1.04, mats)
        coupon = source_targets(
            "B_coupon_" + str(index),
            {"illustrative_busbar_coupon": payload["targets"]["H04"]["illustrative_busbar_coupon"]},
        )
        coupon.location = endpoint
        bolt = empty("B_bolt_" + str(index))
        cylinder(
            bolt.name + "_head", 0.005 if index == 0 else 0.0045, 0.004, (0, 0, 0), mats["steel"], bolt, vertices=6
        )
        positions = [
            motion.b_tool_position(t, index) - (0, 0, 0.002)
            if motion.cycle_time(t) < 10.2
            else endpoint + (0, 0, motion.LUG_PLATE_TOP_Z + 0.002)
            for t, s in zip(bank["time_s"], states, strict=True)
        ]
        angles = [4 * math.pi * motion.between(motion.cycle_time(t), 8.6, 10.2) for t in bank["time_s"]]
        animate_positions(bolt, positions, bank["frames"], angles)
    samples = np.array([cable_points(s[2]) for s in states])
    wire = tube("B_prescribed_wire_middle", samples[0], 0.007, mats["orange"])
    animate_curve(wire, samples, bank["frames"])
    lengths = np.linalg.norm(np.diff(samples, axis=1), axis=2).sum(axis=1)
    return {
        "middle_centerline_min_m": float(lengths.min()),
        "middle_centerline_max_m": float(lengths.max()),
        "endpoint_sections_each_m": 0.087,
        "source_lug_centers_straight_span_m": 0.400,
        "physical_deformation_model": False,
        "visible_stock_count_initial": 10,
    }


def build_c(payload, bank, mats):
    geo.fixture_table("C_control_connector_supply", (9.28, -0.40), (0.33, 0.25), 0.966, mats)
    for i in range(5):
        item = geo.connector("C_stock_control_" + str(i), mats)
        item.location = (9.16 + i * 0.06, -0.47, 0.988)
        box("C_stock_nest", (0.012, 0.012, 0.010), (item.location.x, -0.47, 0.971), mats["blue"])
    box("C_pick_nest", (0.012, 0.012, 0.010), (9.28, -0.40, 0.971), mats["blue"])
    item = geo.connector("C_handled_supported_control_connector", mats)
    states = [motion.c_state(t) for t in bank["time_s"]]
    animate_positions(item, [s[2] for s in states], bank["frames"])
    box("C_fixed_control_receiver", (0.034, 0.032, 0.019), (9.630, 0.025, motion.BODY_BOTTOM + 0.044), mats["dark"])
    # Cable end is supported in a broad open tray, not left floating. This
    # sample does not settle handling of all EC04-EC13 wiring groups.
    box("C_supported_lead_tray", (0.18, 0.10, 0.010), (9.29, -0.35, 0.968), mats["blue"])
    completed = motion.cable_frames(36.0)[2]
    rows = payload["targets"]["H04"]
    for index, pose in enumerate(completed):
        root = source_targets("C_retained_B_endpoint_" + str(index), rows)
        matrix = pose.copy()
        matrix[0, 3] += 2.4
        root.matrix_world = Matrix(matrix)
    points = cable_points(completed) + (2.4, 0, 0)
    tube("C_retained_B_wire", points, 0.007, mats["orange"])


def cameras_and_plan():
    settings = {
        "xyz_stock": ((1.20, -2.80, 2.80), (-0.23, -0.75, 1.15), 38),
        "xyz_place": ((0.53, -0.61, 1.26), (0, 0, 0.95), 55),
        "op020_supply": ((3.22, -0.99, 1.95), (2.35, 0.12, 1.19), 48),
        "op020_insert": ((2.81, -0.61, 1.18), (2.493, -0.09, 0.928), 62),
        "a_cell": ((5.77, 1.27, 2.08), (4.77, -0.23, 1.23), 50),
        "a_fastening": ((4.99, -0.38, 1.40), (4.745, 0, 0.93), 58),
        "b_stock": ((7.12, -0.29, 2.50), (7.12, 0.35, 1.12), 42),
        "b_cell": ((8.32, -1.47, 2.12), (7.12, 0.18, 1.18), 50),
        "b_fastening": ((7.56, 0.19, 1.27), (7.285, 0.040, 0.948), 59),
        "b_fastening_other": ((6.83, -0.43, 1.33), (7.16, -0.025, 0.971), 59),
        "c_cell": ((10.57, 1.12, 1.90), (9.50, -0.20, 1.16), 52),
        "c_insert": ((9.96, 0.37, 1.30), (9.63, 0.025, 0.96), 58),
    }
    for name, (eye, target, lens) in settings.items():
        geo.camera(name, eye, target, lens)
    shots = [
        (0, 6.7, "xyz_stock"),
        (6.7, 12, "xyz_place"),
        (12, 18.8, "op020_supply"),
        (18.8, 26, "op020_insert"),
        (26, 32, "a_cell"),
        (32, 37.1, "a_fastening"),
        (37.1, 40, "a_cell"),
        (40, 44, "b_stock"),
        (44, 47.2, "b_cell"),
        (47.2, 49.7, "b_fastening"),
        (49.7, 51.6, "b_fastening_other"),
        (51.6, 54, "b_cell"),
        (54, 60, "c_cell"),
        (60, 64, "c_insert"),
        (64, 68, "c_cell"),
    ]
    phases = [
        (0, 2.4, "OP010｜XYZ直交・20個ストッカ｜筐体を把持"),
        (2.4, 6.7, "OP010｜姿勢を保ったまま持上げ・XY移載"),
        (6.7, 9.6, "OP010｜コンベア上のパレットへ設置・開放"),
        (9.6, 12, "OP010｜ハンド退避｜パレットの昇降なし"),
        (12, 18.8, "OP020｜単腕で剛体コネクターを取り出し・位置合わせ"),
        (18.8, 22.2, "OP020｜探り動作の軌道例 → 設備側の押込み軸"),
        (22.2, 26, "OP020｜押込み後に開放・上昇"),
        (26, 31.8, "OP030-A｜部品設置とボルト準備を並行"),
        (31.8, 36.6, "OP030-A｜片腕で保持を続け、工具腕で締結"),
        (36.6, 40, "OP030-A｜開放後、両腕を同時に上昇"),
        (40, 43.8, "OP030-B｜10本の並列ストックから両端を同時把持"),
        (43.8, 47.2, "OP030-B｜両端搬送・曲線配置の幾何モデル"),
        (47.2, 51, "OP030-B｜黒被覆・根元を保持｜設備側2工具で同時締結"),
        (51, 54, "OP030-B｜工具退避 → 同時開放 → 両腕同時上昇"),
        (54, 62.8, "OP030-C｜単腕で扱える制御コネクターの代表動作"),
        (62.8, 68, "OP030-C｜嵌合・開放・退避｜他の接続群は別途検討"),
    ]
    return {
        "native": NATIVE.name,
        "native_sha256": None,
        "motion": "hand_line_review_v01/motion.npz",
        "motion_sha256": digest(DATA / "motion.npz"),
        "frame_end": motion.FRAMES,
        "scope_caption": "EVジャンクションボックス｜指先・動作の初期確認（内部は仮寸法）",
        "phase_prefix": "",
        "ranges": [{"first_frame": round(a * 30) + 1, "last_frame": round(b * 30), "camera": c} for a, b, c in shots],
        "phases": [{"start_s": a, "stop_s": b, "label": c} for a, b, c in phases],
    }


def main():
    with gzip.open(DATA / "meshes.json.gz", "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    bank = dict(np.load(DATA / "motion.npz"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "Initial_hand_process_review"
    scene.frame_start, scene.frame_end, scene.render.fps = 1, motion.FRAMES, 30
    scene.render.engine = "CYCLES"
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -0.9
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 720, 100
    mats = geo.palette()
    facility = geo.factory(mats)
    template = geo.housing_template(mats)
    stock = build_op010(template, bank, mats)
    for label, x in motion.CENTERS.items():
        geo.pallet(label + "_work_pallet", x, mats)
        if label != "OP010":
            stage = {"OP020": 2, "A": 3, "B": 4, "C": 5}[label]
            body_group(template, label + "_distinct_workpiece", (x, 0, motion.BODY_BOTTOM), mats, stage)
    for obj in list(template.children):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.objects.remove(template, do_unlink=True)
    robots = build_robots(payload, bank, mats)
    build_op020(bank, mats)
    build_a(payload, bank, mats)
    cable = build_b(payload, bank, mats)
    build_c(payload, bank, mats)
    scene["scope"] = "Representative hand/axis review, not complete production or electrical acceptance"
    scene["OP030_replay"] = "Same parallel representative cycle shown from A, B, C views on distinct workpieces"
    scene.frame_set(1)
    # Camera construction precedes the final saved-native identity.
    plan = cameras_and_plan()
    scene.camera = bpy.data.objects["Review_OP030_xyz_stock"]
    bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE), compress=True)
    plan["native_sha256"] = digest(NATIVE)
    write_json(ROOT / "data/hand_line_review_v01_presentation.json", plan)
    report = {
        "native": NATIVE.name,
        "native_sha256": plan["native_sha256"],
        "mesh_inputs_sha256": digest(DATA / "meshes.json.gz"),
        "motion_sha256": plan["motion_sha256"],
        "stock_body_count": len(stock),
        "stock_body_objects": stock,
        "op010_cartesian_axis_count": 3,
        "robot_mesh_objects": robots,
        "facility": facility,
        "cable": cable,
        "object_count": len(scene.objects),
        "physical_acceptance_verdict": None,
    }
    write_json(ROOT / "audit/hand_line_review_v01_build.json", report)
    print("HAND_LINE_NATIVE_BUILT", NATIVE, len(scene.objects), cable, flush=True)


if __name__ == "__main__":
    main()
