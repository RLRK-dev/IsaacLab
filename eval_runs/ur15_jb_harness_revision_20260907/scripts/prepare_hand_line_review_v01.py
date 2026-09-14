# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse real UR15/2F geometry and solve initial review flange paths [m, rad]."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import math
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import build_hand_fingertip_concepts_v01 as fingers
import hand_line_review_motion as motion
import numpy as np
import trimesh
from prepare_hand_working_default_v01 import load_working_default

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path("/home/rlrk/IsaacLab/eval_runs/ur15_jb_harness_revision_20260907")
ORIGINAL = ROOT / "inputs/v02_source/inputs/v01_source/op010_base/original/render_ur15_line.py"
ASSETS = Path("/home/rlrk/src/ur15-line-render/assets")
URDF = (
    MAIN
    / "inputs/v02_source/inputs/v01_source/inputs/UR15_monocular_camera_v01/source"
    / "ur15-dual-arm-cell/ur15-dual-arm-cell.urdf"
)
OUTPUT = ROOT / "data/hand_line_review_v01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_module():
    spec = importlib.util.spec_from_file_location("hand_line_source_ur15", ORIGINAL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def serialize_mesh(mesh, color=None):
    if color is None:
        material = getattr(mesh.visual, "material", None)
        color = getattr(material, "diffuse", None)
        if color is None:
            color = getattr(material, "main_color", None)
        if color is None:
            visual = mesh.visual if hasattr(mesh.visual, "vertex_colors") else mesh.visual.to_color()
            color = np.asarray(visual.vertex_colors)[0]
    color = np.asarray(color).reshape(-1)[:4]
    if len(color) == 3:
        color = np.r_[color, 255]
    return {
        "vertices": np.asarray(mesh.vertices).tolist(),
        "faces": np.asarray(mesh.faces).tolist(),
        "color": color.astype(int).tolist(),
    }


def robot_meshes(robot):
    result, inputs = {}, {}
    for link, filename in robot.MESHES.items():
        path = ASSETS / "Universal_Robots_ROS2_Description/meshes/ur15/visual" / filename
        inputs[str(path)] = sha(path)
        scene = trimesh.load(path, force="scene", process=False)
        for index, node in enumerate(scene.graph.nodes_geometry):
            matrix, name = scene.graph.get(node)
            row = serialize_mesh(scene.geometry[name])
            row["uv"] = np.asarray(scene.geometry[name].visual.uv).tolist()
            row["normals"] = np.asarray(scene.geometry[name].vertex_normals).tolist()
            row["texture"] = str(path.parent / "UR15_DIFF_8bit_2K.jpg")
            row["is_cap"] = "pad" in name.lower()
            inputs[row["texture"]] = sha(Path(row["texture"]))
            row["link"] = link
            row["local"] = (robot.VISUAL_OFFSETS[link] @ matrix).tolist()
            result[f"{link}_{index}"] = row
    return result, inputs


def hand_link(name):
    if name.startswith("hardware_"):
        return name.removeprefix("hardware_").rsplit("_", 1)[0]
    side = "left_left" if name.startswith("left_left") else "left_right"
    return side + "_inner_finger"


def calibration(candidate, urdf):
    near = candidate["states"]["near"]
    root = np.asarray(near["transforms"]["hardware_left_gripper_base_0"])
    frames = fingers._gripper_fk(urdf, near["joint_q_rad"])
    objects = {}
    for name, obj in candidate["objects"].items():
        if obj["category"] not in {"hardware", "insert"}:
            continue
        link = hand_link(name)
        local = np.linalg.inv(root @ frames[link]) @ np.asarray(near["transforms"][name])
        objects[name] = {**obj, "link": link, "local": local.tolist()}
    errors = []
    for state, snapshot in candidate["states"].items():
        frames = fingers._gripper_fk(urdf, snapshot["joint_q_rad"])
        lift = motion.transform((0, 0, snapshot["root_lift_m"]))
        for name, obj in objects.items():
            reconstructed = lift @ root @ frames[obj["link"]] @ np.asarray(obj["local"])
            errors.append(float(np.max(np.abs(reconstructed - snapshot["transforms"][name]))))
    # Numerical identity of reused snapshots is an implementation check only.
    if max(errors) > 1e-7:
        raise ValueError(f"Gripper kinematics do not recover source states: {max(errors)}")
    return {
        "objects": objects,
        "anchor_to_flange": root.tolist(),
        "q_closed": near["joint_q_rad"],
        "q_open": candidate["states"]["open"]["joint_q_rad"],
        "source_states_max_matrix_difference": max(errors),
    }


def compact_connector_candidate(config, urdf, hardware):
    settings = {
        **config,
        "release_extra_half_opening_m": 0.003,
        "A": {**config["A"], "target_radius_m": 0.014, "back_plane_x_m": 0.022},
    }
    candidate = fingers._candidate(settings, "A", urdf, hardware)
    root = np.asarray(candidate["states"]["near"]["transforms"]["hardware_left_gripper_base_0"])
    frames = fingers._gripper_fk(urdf, candidate["states"]["near"]["joint_q_rad"])
    # Opposed flat pads with two locating cheeks, no underside hook.
    for side, sign in zip(fingers.SIDES, (-1, 1), strict=True):
        components = [trimesh.creation.box((0.004, 0.026, 0.022))]
        components[0].apply_translation((sign * 0.016, 0, 0))
        for y in (-0.014, 0.014):
            cheek = trimesh.creation.box((0.007, 0.002, 0.022))
            cheek.apply_translation((sign * 0.0145, y, 0))
            components.append(cheek)
        mesh = trimesh.util.concatenate(components)
        link = side + "_inner_finger"
        mesh.apply_transform(np.linalg.inv(root @ frames[link]))
        name = side + "_contour_contact"
        candidate["objects"][name] = {**serialize_mesh(mesh, (35, 127, 168, 255)), "category": "insert"}
    # Keep the target-facing pockets at their original contact positions while
    # moving the bulky source linkage above adjacent connector bodies.
    lift = motion.transform((0, 0, 0.035))
    closed = candidate["states"]["near"]["transforms"]
    for name, row in candidate["objects"].items():
        if row["category"] != "insert":
            continue
        old = np.asarray(closed[name])
        if name.endswith("insert_carrier"):
            sign = -1 if name.startswith("left_left") else 1
            mesh = trimesh.creation.box((0.003, 0.020, 0.043))
            mesh.apply_translation((sign * 0.0215, 0, 0.015))
        else:
            mesh = trimesh.Trimesh(row["vertices"], row["faces"], process=False)
            mesh.apply_transform(old)
        mesh.apply_transform(np.linalg.inv(lift @ old))
        row["vertices"], row["faces"] = mesh.vertices.tolist(), mesh.faces.tolist()
    for snapshot in candidate["states"].values():
        for name, row in candidate["objects"].items():
            if row["category"] in {"hardware", "insert"}:
                snapshot["transforms"][name] = (lift @ snapshot["transforms"][name]).tolist()
    return candidate


def extended_round_candidate(config, urdf, hardware):
    """Keep the contour contact and add an initial straight 50 mm extension."""
    candidate = fingers._candidate(config, "A", urdf, hardware)
    lift = motion.transform((0, 0, 0.05))
    closed = candidate["states"]["near"]["transforms"]
    for name, row in candidate["objects"].items():
        if row["category"] != "insert":
            continue
        old = np.array(closed[name])
        if name.endswith("insert_carrier"):
            sign = -1 if name.startswith("left_left") else 1
            mesh = trimesh.creation.box((0.003, 0.020, 0.050))
            mesh.apply_translation((sign * 0.0325, 0, 0.037))
            mesh.apply_transform(np.linalg.inv(lift @ old))
        else:
            mesh = trimesh.Trimesh(row["vertices"], row["faces"], process=False)
            mesh.apply_transform(old)
            mesh.apply_translation((0, 0, 0.010))
            mesh.apply_transform(np.linalg.inv(lift @ old))
        row["vertices"], row["faces"] = np.asarray(mesh.vertices).tolist(), mesh.faces.tolist()
    for snapshot in candidate["states"].values():
        for name, row in candidate["objects"].items():
            if row["category"] in {"hardware", "insert"}:
                snapshot["transforms"][name] = (lift @ snapshot["transforms"][name]).tolist()
    # Tilt this round-part mechanism sideways to leave both Y-side bolt axes
    # open. The target and near contour contacts remain fixed. This H01
    # provisional lateral tilt does not change the selected T050 hand.
    turn = motion.transform(rpy=(0, math.radians(15), 0))
    old_near = candidate["states"]["near"]["transforms"]
    for name, row in candidate["objects"].items():
        if row["category"] != "insert":
            continue
        old = np.array(old_near[name])
        points = np.array(row["vertices"]) @ old[:3, :3].T + old[:3, 3]
        if name.endswith("insert_carrier"):
            weight = np.clip((points[:, 2] - 0.016) / 0.046, 0, 1)[:, None]
            points = points * (1 - weight) + (points @ turn[:3, :3].T) * weight
        inverse = np.linalg.inv(turn @ old)
        row["vertices"] = (points @ inverse[:3, :3].T + inverse[:3, 3]).tolist()
    for snapshot in candidate["states"].values():
        vertical = motion.transform((0, 0, snapshot["root_lift_m"]))
        delta = vertical @ turn @ np.linalg.inv(vertical)
        for name, row in candidate["objects"].items():
            if row["category"] in {"hardware", "insert"}:
                snapshot["transforms"][name] = (delta @ snapshot["transforms"][name]).tolist()
    return candidate


def hands():
    urdf = ET.parse(URDF).getroot()
    payload, provenance = load_working_default()
    config = json.loads((ROOT / "data/hand_fingertip_concepts_v01.json").read_text())
    config["A"]["tool_center_y_m"] = 0.045
    hardware, inputs = fingers._reuse_meshes(
        urdf, ASSETS / "robotiq/robotiq_2f_85_gripper_visualization", fingers._gripper_fk(urdf, 0)
    )
    candidates = {
        "H01": extended_round_candidate(config, urdf, hardware),
        "H04": payload["candidates"]["T050"],
        "H05": compact_connector_candidate(config, urdf, hardware),
    }
    result = {name: calibration(candidate, urdf) for name, candidate in candidates.items()}
    targets = {
        name: {
            key: {**row, "local": candidate["states"]["near"]["transforms"][key]}
            for key, row in candidate["objects"].items()
            if row["category"] == "target"
        }
        for name, candidate in candidates.items()
    }
    return urdf, result, targets, provenance, {str(path): sha(path) for path in [*inputs, URDF]}


def bases():
    # Reuse the established +/-45 degree dual mounting; new station transforms
    # put A and B on opposite conveyor sides. Positions are review parameters.
    values = {"OP020": motion.transform((2.40, 0.91, 0.75)), "C": motion.transform((9.60, -0.91, 0.75))}
    for prefix, x, side in (("A", 4.8, -1), ("B", motion.B_ROBOT_X, 1)):
        for suffix, offset in (
            ("hold" if prefix == "A" else "left", -0.26),
            ("tool" if prefix == "A" else "right", 0.26),
        ):
            values[prefix + "_" + suffix] = motion.transform(
                (x + offset, side * 0.82, 1.38), (0, math.copysign(math.pi / 4, offset), 0)
            )
    return values


def segment_distance(a0, a1, b0, b1):
    """Return finite-segment distance for coarse trajectory branch ranking [m]."""
    u, v, w = a1 - a0, b1 - b0, a0 - b0
    aa, bb, cc, dd, ee = u @ u, u @ v, v @ v, u @ w, v @ w
    denom = aa * cc - bb * bb
    s = np.clip((bb * ee - cc * dd) / denom, 0, 1) if denom > 1e-12 else 0.0
    t = np.clip((bb * s + ee) / max(cc, 1e-12), 0, 1)
    s = np.clip((bb * t - dd) / max(aa, 1e-12), 0, 1)
    return float(np.linalg.norm(w + s * u - t * v))


def arm_segments(robot, base, q):
    frames, _ = robot.forward(base, q)
    points = [frames[name][:3, 3] for name in ("upper_arm", "forearm", "wrist_1", "wrist_2", "wrist_3")]
    return [(a, b, r) for a, b, r in zip(points[:-1], points[1:], (0.073, 0.066, 0.060, 0.052), strict=True)]


def branch_cost(robot, base, q, name):
    frames, _ = robot.forward(base, q)
    elbow = frames["forearm"][:3, 3]
    shoulder = frames["upper_arm"][:3, 3]
    side = -1 if name.endswith(("hold", "left")) else 1
    cost = 0.15 * np.linalg.norm(q) + max(0, 0.95 - elbow[2]) * 20
    if name.startswith(("A_", "B_")):
        # Encourage the two elbows to stay on their own side of the column.
        cost += max(0, 0.15 - side * (elbow[0] - base[0, 3])) * 20
        center = 4.8 if name.startswith("A_") else motion.B_ROBOT_X
        column = (np.array((center, base[1, 3], 0.50)), np.array((center, base[1, 3], 1.37)))
        for a, b, radius in arm_segments(robot, base, q)[1:]:
            gap = segment_distance(a, b, *column) - radius - 0.12
            cost += max(0, 0.035 - gap) * 200
    cost += max(0, 0.06 - abs(elbow[1] - shoulder[1]))
    return cost


def initial_candidates(source, base, target, name):
    rows = []
    for q0 in (0, math.pi / 2, -math.pi / 2, math.pi):
        for q2 in (-1.6, 1.6):
            for wrist in (-math.pi / 2, math.pi / 2):
                seed = np.array((q0, -0.8, q2, -1.1, wrist, 0))
                q, residual = source.solve_tool_pose(base, target[:3, 3], seed, orientation=target[:3, :3])
                q = (q + math.pi) % (2 * math.pi) - math.pi
                if residual < 1e-5 and not any(np.linalg.norm(q - row[1]) < 1e-3 for row in rows):
                    rows.append((branch_cost(source.UR15, base, q, name), q))
    if not rows:
        raise ValueError(f"No accurate initial inverse-kinematics solution for {name}")
    return sorted(rows, key=lambda row: row[0])


def select_pair_paths(source, mounting, roots):
    config = json.loads((ROOT / "data/hand_line_review_v01.json").read_text())
    recorded = config.get("initial_joint_seeds_rad")
    if recorded is not None and len(recorded) == 4:
        selected = {name: np.asarray(recorded[name], dtype=float) for name in ("A_hold", "A_tool", "B_left", "B_right")}
        if any(q.shape != (6,) or not np.isfinite(q).all() for q in selected.values()):
            raise ValueError("Invalid recorded initial joint seeds")
        return selected, {"basis": "Saved-native branch surface comparison; all output paths are solved again"}
    selected, observations = {}, {}
    times = 26 + np.linspace(0, 13.93333333, 71)
    for first, second in (("A_hold", "A_tool"), ("B_left", "B_right")):
        if recorded is not None and first in recorded and second in recorded:
            selected.update({first: np.array(recorded[first]), second: np.array(recorded[second])})
            observations[first + "/" + second] = {"basis": "Saved-native branch comparison"}
            continue
        candidates = {}
        for name in (first, second):
            target = motion.robot_targets(26.0, roots)[0][name]
            candidates[name] = []
            for rank, initial in initial_candidates(source, mounting[name], target, name):
                previous, segments, body_gap = initial.copy(), [], math.inf
                valid = True
                for time in times:
                    pose = motion.robot_targets(time, roots)[0][name]
                    q, residual = source.solve_tool_pose(
                        mounting[name], pose[:3, 3], previous, orientation=pose[:3, :3]
                    )
                    if residual > 1e-4:
                        valid = False
                        break
                    previous = previous + (q - previous + math.pi) % (2 * math.pi) - math.pi
                    arms = arm_segments(source.UR15, mounting[name], previous)
                    segments.append(arms)
                    link_poses, _ = source.UR15.forward(mounting[name], previous)
                    body_gap = min(body_gap, float(link_poses["forearm"][2, 3]) - 1.10)
                    if name == "A_hold":
                        tip = motion.a_state(time)[3]
                        shaft = (tip + (0, 0, 0.025), tip + (0, 0, 0.45))
                        body_gap = min(
                            body_gap, *(segment_distance(a, b, *shaft) - radius - 0.02 for a, b, radius in arms)
                        )
                    if name.startswith("B_"):
                        for spindle_index in range(2):
                            tip = motion.b_tool_position(time, spindle_index)
                            shaft = (tip + (0, 0, 0.015), tip + (0, 0, 0.36))
                            body_gap = min(
                                body_gap,
                                *(segment_distance(a, b, *shaft) - radius - 0.027 for a, b, radius in arms),
                            )
                    x = 4.8 if name.startswith("A_") else motion.B_ROBOT_X
                    column = (np.array((x, mounting[name][1, 3], 0.50)), np.array((x, mounting[name][1, 3], 1.31)))
                    body_gap = min(
                        body_gap, *(segment_distance(a, b, *column) - radius - 0.12 for a, b, radius in arms[1:])
                    )
                if valid:
                    candidates[name].append((initial, segments, body_gap, rank))
        pairs = []
        for i, a in enumerate(candidates[first]):
            for j, b in enumerate(candidates[second]):
                gap = min(
                    segment_distance(a0, a1, b0, b1) - ar - br
                    for aa, bb in zip(a[1], b[1], strict=True)
                    for a0, a1, ar in aa
                    for b0, b1, br in bb
                )
                score = min(gap, a[2], b[2])
                pairs.append((score, gap, i, j))
        if not pairs:
            raise ValueError(f"No complete branch pair for {first}/{second}")
        score, gap, i, j = max(pairs)
        selected[first], selected[second] = candidates[first][i][0], candidates[second][j][0]
        observations[first + "/" + second] = {
            "candidate_pairs": len(pairs),
            "sample_count": len(times),
            "selected_coarse_arm_gap_m": gap,
            "selected_min_coarse_gap_m": score,
        }
        print("HAND_LINE_PAIR_SELECTED", first, second, observations[first + "/" + second], flush=True)
    return selected, observations


def select_single_paths(source, mounting, roots):
    """Rank complete single-arm paths by elbow height above supply fixtures."""
    selected, observations = {}, {}
    for name, start in (("OP020", 12), ("C", 26)):
        initial_target = motion.robot_targets(start, roots)[0][name]
        ranked = []
        for rank, initial in initial_candidates(source, mounting[name], initial_target, name):
            previous, lowest, valid = initial.copy(), math.inf, True
            for time in start + np.linspace(0, 13.9333333, 71):
                target = motion.robot_targets(time, roots)[0][name]
                q, residual = source.solve_tool_pose(
                    mounting[name], target[:3, 3], previous, orientation=target[:3, :3]
                )
                if residual > 1e-4:
                    valid = False
                    break
                previous += (q - previous + math.pi) % (2 * math.pi) - math.pi
                poses, _ = source.UR15.forward(mounting[name], previous)
                lowest = min(lowest, poses["forearm"][2, 3], poses["wrist_1"][2, 3])
            if valid:
                ranked.append((lowest, -rank, initial))
        if not ranked:
            raise ValueError(f"No complete single-arm path for {name}")
        best = max(ranked, key=lambda row: row[:2])
        selected[name] = best[2]
        observations[name] = {"complete_candidates": len(ranked), "minimum_elbow_or_wrist_origin_z_m": best[0]}
        print("HAND_LINE_SINGLE_SELECTED", name, observations[name], flush=True)
    return selected, observations


def prepare_motion(source, urdf, hand_data):
    roots = {key: np.array(row["anchor_to_flange"]) for key, row in hand_data.items()}
    mounting = bases()
    pair_initials, branch_observations = select_pair_paths(source, mounting, roots)
    single_initials, single_observations = select_single_paths(source, mounting, roots)
    pair_initials.update(single_initials)
    branch_observations.update(single_observations)
    # A native key every second frame matches the delivered 15 Hz samples.
    frame_numbers = np.arange(1, motion.FRAMES + 1, 2)
    times = (frame_numbers - 1) / 30
    names = list(mounting)
    bank = {"frames": frame_numbers, "time_s": times}
    report = {}
    kind = {"OP020": "H05", "A_hold": "H01", "B_left": "H04", "B_right": "H04", "C": "H05"}
    for name in names:
        records, targets, joints, errors = [], [], [], []
        previous = None
        for index, seconds in enumerate(times):
            target = motion.robot_targets(seconds, roots)[0][name]
            if previous is None or (name.startswith(("A_", "B_")) or name == "C") and index in (600, 810):
                previous = (
                    pair_initials[name].copy()
                    if name in pair_initials
                    else initial_candidates(source, mounting[name], target, name)[0][1]
                )
            q, residual = source.solve_tool_pose(mounting[name], target[:3, 3], previous, orientation=target[:3, :3])
            # Keep the continuous representative of each revolute coordinate.
            q = previous + (q - previous + math.pi) % (2 * math.pi) - math.pi
            poses, flange = source.UR15.forward(mounting[name], q)
            position_error = np.linalg.norm(flange[:3, 3] - target[:3, 3])
            if residual > 1e-4:
                raise ValueError(f"Unreached flange {name} frame={frame_numbers[index]} residual={residual}")
            records.append(np.array([poses[link] for link in ("base", *source.UR15.LINKS)]))
            targets.append(flange)
            joints.append(q)
            errors.append(position_error)
            previous = q
        bank[name + "_links"] = np.array(records)
        bank[name + "_flange"] = np.array(targets)
        bank[name + "_joints"] = np.array(joints)
        steps = np.abs(np.diff(joints, axis=0))
        continuous = np.ones(len(steps), dtype=bool)
        if name.startswith(("A_", "B_")) or name == "C":
            continuous[[599, 809]] = False
        report[name] = {
            "flange_position_max_error_m": float(max(errors)),
            "sampled_joint_step_max_rad_including_edit_cuts": float(steps.max()),
            "sampled_joint_step_max_rad_excluding_edit_cuts": float(steps[continuous].max()),
            "joint_min_rad": np.min(joints, axis=0).tolist(),
            "joint_max_rad": np.max(joints, axis=0).tolist(),
        }
        if name in kind:
            hand = hand_data[kind[name]]
            length, angle = motion.B_MOUNTS.get(name, (0, 0))
            mount = motion.transform((0, 0, length), (0, 0, -angle))
            hand_flanges = np.asarray(targets) @ mount
            bank[name + "_hand_flange"] = hand_flanges
            for objname, row in hand["objects"].items():
                transforms = []
                for seconds, flange in zip(times, hand_flanges, strict=True):
                    grip = motion.robot_targets(seconds, roots)[1][name]
                    q = hand["q_open"] * (1 - grip) + hand["q_closed"] * grip
                    transforms.append(flange @ fingers._gripper_fk(urdf, q)[row["link"]] @ row["local"])
                bank[name + "_hand_" + objname] = np.asarray(transforms)
        print("HAND_LINE_ARM_SOLVED", name, report[name], flush=True)
    minimums = {}
    for first, second in (("A_hold", "A_tool"), ("B_left", "B_right")):
        samples = []
        for index in range(len(times)):
            a = arm_segments(source.UR15, mounting[first], bank[first + "_joints"][index])
            b = arm_segments(source.UR15, mounting[second], bank[second + "_joints"][index])
            samples.append(min(segment_distance(x0, x1, y0, y1) - xr - yr for x0, x1, xr in a for y0, y1, yr in b))
        closest = int(np.argmin(samples))
        minimums[first + "/" + second] = {
            "coarse_capsule_gap_m": samples[closest],
            "frame": int(frame_numbers[closest]),
            "not_mesh_or_physical_verdict": True,
        }
    return bank, report, minimums, mounting, branch_observations


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = source_module()
    robot, inputs = robot_meshes(source.UR15)
    urdf, hand_data, targets, provenance, hand_inputs = hands()
    inputs.update(hand_inputs)
    inputs[str(ORIGINAL)] = sha(ORIGINAL)
    bank, solved, coarse, mounting, branches = prepare_motion(source, urdf, hand_data)
    np.savez_compressed(OUTPUT / "motion.npz", **bank)
    payload = {
        "robot": robot,
        "hands": hand_data,
        "targets": targets,
        "bases": {key: value.tolist() for key, value in mounting.items()},
    }
    with gzip.open(OUTPUT / "meshes.json.gz", "wt", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))
    report = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "input_sha256": inputs,
        "implementation_sha256": {
            str(path.relative_to(ROOT)): sha(path)
            for path in (
                Path(__file__),
                ROOT / "scripts/hand_line_review_motion.py",
                ROOT / "data/hand_line_review_v01.json",
            )
        },
        "source_use": (
            "UR15 forward kinematics, inverse kinematics and official visual meshes only; "
            "no old video or old assembly timing"
        ),
        "hand_default": provenance,
        "hand_state_reconstruction": {k: v["source_states_max_matrix_difference"] for k, v in hand_data.items()},
        "flange_observations": solved,
        "coarse_branch_observations": coarse,
        "pair_search": branches,
        "motion_sha256": sha(OUTPUT / "motion.npz"),
        "mesh_sha256": sha(OUTPUT / "meshes.json.gz"),
        "formal_physical_validity_verdict": None,
    }
    path = ROOT / "audit/hand_line_review_v01_prepare.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("HAND_LINE_PREPARED", path, coarse, flush=True)


if __name__ == "__main__":
    main()
