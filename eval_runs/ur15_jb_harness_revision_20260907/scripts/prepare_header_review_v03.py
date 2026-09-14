# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Prepare official header tessellations and a new OP020 review path [m, s].

The renderer needs only the baked mesh/motion files. Optional cascadio is used
once for public STEP conversion, outside the IsaacLab environment. Geometry and
authored motion do not establish holding force or fastening quality.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import prepare_hand_line_review_v01 as reuse
import trimesh
from hand_line_review_motion import between, track, transform
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references/connector_correction_20260915"
DATA = ROOT / "data/header_review_v03"
BASE_NATIVE_SHA = "313f3a30301afbdb4d7bc16a8b028fb0ebf62b9d953b6450efe81c13c34e7471"
END_FRAME = 2820
OFFSET_FRAMES = 780
HEADER_X = (-0.052, 0.072)
HEADER_WIDTH = (0.1132, 0.0793)
HEADER_BOLT_X = ((-0.05005, -0.01695, 0.01695, 0.05005), (-0.0331, 0, 0.0331))
HEADER_BAY_X = ((-0.0339, 0, 0.0339), (-0.01695, 0.01695))
SEATS = (np.array((2.4 + HEADER_X[0], -0.08, 0.879)), np.array((2.4 + HEADER_X[1], -0.08, 0.879)))
PICKS = (np.array((2.13, 0.32, 1.01)), np.array((2.45, 0.32, 1.01)))


def converted_meshes():
    """Read official public outer-header STEP surfaces without scaling them."""
    import cascadio  # Optional one-time conversion tool; absent from render dependencies.

    rows, provenance = [], []
    for index, part in enumerate(("2103340-1", "2103346-2")):
        stem = "te_" + part.replace("-", "_")
        archive = REF / (stem + "_step.zip")
        with zipfile.ZipFile(archive) as stream:
            names = stream.namelist()
            assert len(names) == 1 and Path(names[0]).name == names[0]
            raw = stream.read(names[0])
        step = REF / names[0]
        step.write_bytes(raw)
        glb = REF / (stem + ".glb")
        glb.write_bytes(cascadio.to_glb_bytes(raw, tol_linear=0.02, tol_angular=0.2, include_materials=True))
        scene = trimesh.load(glb, force="scene", process=False)
        meshes, annotations = [], []
        for node in scene.graph.nodes_geometry:
            matrix, key = scene.graph.get(node)
            geometry = scene.geometry[key]
            if not isinstance(geometry, trimesh.Trimesh):
                annotations.append({"node": node, "type": type(geometry).__name__})
                continue
            mesh = geometry.copy()
            mesh.apply_transform(matrix)
            meshes.append(mesh)
        mesh = trimesh.util.concatenate(meshes)
        # GLB is SI. Turn X-right/Y-up/front-Z into X-right/Y-inward/Z-up.
        # The common flange device-side datum is source Z=-31.10 mm.
        datum = transform((0, -0.0311, 0), (math.pi / 2, 0, 0))
        mesh.apply_transform(datum)
        assert abs(mesh.extents[0] - HEADER_WIDTH[index]) < 1e-7
        assert abs(mesh.extents[2] - 0.0406) < 1e-7
        centers = mesh.triangles_center
        # Presentation colors only: CAD has a single merged surface shell.
        face_material = np.zeros(len(mesh.faces), dtype=np.int32)
        for x in HEADER_BAY_X[index]:
            inner = (abs(centers[:, 0] - x) < 0.0138) & (abs(centers[:, 2]) < 0.00935)
            inner &= (centers[:, 1] < -0.001) & (centers[:, 1] > -0.0304)
            face_material[inner] = 1
        face_material[(centers[:, 1] > -0.00005) & (centers[:, 1] < 0.0011)] = 2
        rows.append(
            {
                "part_number": part,
                "vertices": mesh.vertices.tolist(),
                "faces": mesh.faces.tolist(),
                "face_material": face_material.tolist(),
            }
        )
        provenance.append(
            {
                "part_number": part,
                "product_url": "https://www.te.com/en/product-" + part + ".html",
                "step_name": step.name,
                "step_sha256": reuse.sha(step),
                "archive_sha256": reuse.sha(archive),
                "glb_sha256": reuse.sha(glb),
                "bounds_m": mesh.bounds.tolist(),
                "triangles": len(mesh.faces),
                "ignored_non_surface_annotations": annotations,
                "geometry_scale": 1.0,
                "glb_to_header_datum": datum.tolist(),
            }
        )
    return rows, {"cascadio_version": cascadio.__version__, "linear_deflection_mm": 0.02, "sources": provenance}


def hand_profile(payload, urdf):
    """Fit an initial pair of offset tips to the two flange side faces [m]."""
    hand = payload["hands"]["H05"]
    anchor = np.array(hand["anchor_to_flange"])
    # Keep original hardware outside the case; dedicated tips reach its flange.
    anchor[1, 3] -= 0.060
    q_three = 0.25
    first_fk = reuse.fingers._gripper_fk(urdf, q_three)
    first_link = anchor @ first_fk["left_left_inner_finger"]
    q_two = brentq(
        lambda q: (anchor @ reuse.fingers._gripper_fk(urdf, q)["left_left_inner_finger"])[0, 3]
        - first_link[0, 3]
        - (HEADER_WIDTH[0] - HEADER_WIDTH[1]) / 2,
        0.25,
        0.8,
    )
    q_open_two = brentq(
        lambda q: (anchor @ reuse.fingers._gripper_fk(urdf, q)["left_left_inner_finger"])[0, 3]
        - first_link[0, 3]
        - (HEADER_WIDTH[0] - HEADER_WIDTH[1]) / 2
        + 0.007,
        0.25,
        q_two,
    )
    q_open = [0.15, q_open_two]
    objects = {name: row for name, row in hand["objects"].items() if row["category"] == "hardware"}
    for side, sign in zip(reuse.fingers.SIDES, (-1, 1), strict=True):
        link = side + "_inner_finger"
        first = anchor @ first_fk[link]
        # The flange side faces remain clear of the +/-13.75 mm bolt rows.
        parts = []
        for dimensions, position in (
            ((0.004, 0.008, 0.066), (sign * 0.0606, -0.0045, 0.029)),
            ((0.014, 0.072, 0.010), (sign * 0.0566, -0.031, 0.064)),
        ):
            mesh = trimesh.creation.box(dimensions)
            mesh.apply_translation(position)
            parts.append(mesh)
        carrier = trimesh.util.concatenate(parts)
        carrier.apply_transform(np.linalg.inv(first))
        objects[side + "_header_carrier"] = {
            **reuse.serialize_mesh(carrier, (35, 127, 168, 255)),
            "link": link,
            "local": np.eye(4).tolist(),
            "category": "insert",
        }
        pad = trimesh.creation.box((0.002, 0.005, 0.010))
        pad.apply_translation((sign * 0.0576, -0.003, 0))
        pad.apply_transform(np.linalg.inv(first))
        objects[side + "_header_pad"] = {
            **reuse.serialize_mesh(pad, (26, 98, 107, 255)),
            "link": link,
            "local": np.eye(4).tolist(),
            "category": "contact_pad",
        }
    return {
        "objects": objects,
        "anchor_to_flange": anchor.tolist(),
        "q_closed": [q_three, q_two],
        "q_open": q_open,
        "link_reference_z_m": first_link[2, 3],
        "fixed_tip_geometry": True,
    }


def operation(seconds, index):
    """Return header position, release state and authored fastening schedule."""
    start, seat_time, fasten_time = (0, 6.2, 6.8) if index == 0 else (18.0, 24.8, 25.5)
    count = len(HEADER_BOLT_X[index]) * 2
    done = fasten_time + count
    pick, seat = PICKS[index], SEATS[index]
    position = track(
        seconds,
        (
            (start, pick + (0, 0, 0.15)),
            (start + 1.2, pick),
            (start + 2.0, pick),
            (start + 3.0, pick + (0, 0, 0.15)),
            (seat_time - 1.2, seat + (0, -0.075, 0.10)),
            (seat_time - 0.45, seat + (0, -0.020, 0)),
            (seat_time, seat),
            (done + 0.65, seat),
            (done + 1.8, seat + (0, 0, 0.16)),
        ),
    )
    close = between(seconds, start + 1.2, start + 1.8)
    close *= 1 - between(seconds, done + 0.15, done + 0.65)
    payload = pick if seconds < start + 1.8 else position if seconds < done + 0.15 else seat
    return position, close, payload


def bolt_schedule():
    records = []
    for index in range(2):
        xs = HEADER_BOLT_X[index]
        # Alternate opposite sides. This is an authored display order, not a
        # claimed manufacturer tightening sequence or real takt.
        ordering = [(xs[i], z) for i in range(len(xs)) for z in (-0.01375, 0.01375)]
        for number, (x, z) in enumerate(ordering):
            start = (6.8 if index == 0 else 25.5) + number
            tip = SEATS[index] + (x, -0.0092, z)
            records.append({"header": index, "start": start, "stop": start + 1, "tip": tip.tolist()})
    return records


def driver_position(seconds):
    records = bolt_schedule()
    keys = [(0, (2.28, -0.30, 0.96))]
    for record in records:
        tip = np.array(record["tip"])
        start = record["start"]
        keys.extend(
            (
                (start - 0.2, tip + (0, -0.055, 0)),
                (start + 0.05, tip),
                (start + 0.60, tip),
                (start + 0.78, tip + (0, -0.055, 0)),
            )
        )
    keys.append((33.0, (2.28, -0.30, 0.96)))
    return track(seconds, keys)


def motion_bank(hand, payload, urdf):
    source = reuse.source_module()
    mount = np.array(payload["bases"]["OP020"])
    anchor = np.array(hand["anchor_to_flange"])
    frames = np.arange(1, END_FRAME + 1, 2)
    times = (frames - 1) / 30
    bank = {"frames": frames, "time_s": times}
    targets, commands, payloads = [], [], [[], []]
    for seconds in times:
        t = np.clip(seconds - 12, 0, 40)
        index = 0 if t < 18 else 1
        p, grip, _ = operation(t, index)
        # Bridge between completed first pickup and the second without a cut.
        if 16.6 < t < 18:
            p = track(t, ((16.6, SEATS[0] + (0, 0, 0.16)), (18, PICKS[1] + (0, 0, 0.15))))
        opened = hand["q_open"][0] + (hand["q_open"][1] - hand["q_open"][0]) * between(t, 16.6, 18)
        q = opened + (hand["q_closed"][index] - opened) * grip
        delta_z = (
            hand["link_reference_z_m"] - (anchor @ reuse.fingers._gripper_fk(urdf, q)["left_left_inner_finger"])[2, 3]
        )
        targets.append(transform(p + (0, 0, delta_z)) @ anchor)
        commands.append(q)
        for j in range(2):
            payloads[j].append(operation(t, j)[2])
    candidates = reuse.initial_candidates(source, mount, targets[0], "OP020")
    ranking = []
    for rank, initial in candidates:
        previous, min_z, valid = initial.copy(), math.inf, True
        for target in targets[::20]:
            q, residual = source.solve_tool_pose(mount, target[:3, 3], previous, orientation=target[:3, :3])
            if residual > 1e-4:
                valid = False
                break
            previous += (q - previous + math.pi) % (2 * math.pi) - math.pi
            links, _ = source.UR15.forward(mount, previous)
            min_z = min(min_z, links["forearm"][2, 3], links["wrist_1"][2, 3])
        if valid:
            ranking.append((min_z, -rank, initial))
    assert ranking, "No complete OP020 flange path"
    previous = max(ranking, key=lambda row: row[:2])[2]
    poses, flanges, joints, errors = [], [], [], []
    for target in targets:
        q, residual = source.solve_tool_pose(mount, target[:3, 3], previous, orientation=target[:3, :3])
        q = previous + (q - previous + math.pi) % (2 * math.pi) - math.pi
        if residual > 1e-4:
            raise ValueError(f"OP020 flange residual {residual}")
        links, flange = source.UR15.forward(mount, q)
        poses.append([links[name] for name in ("base", *source.UR15.LINKS)])
        flanges.append(flange)
        joints.append(q)
        errors.append(float(residual))
        previous = q
    bank["OP020_links"], bank["OP020_flange"] = np.array(poses), np.array(flanges)
    bank["OP020_joints"], bank["gripper_q"] = np.array(joints), np.array(commands)
    for name, row in hand["objects"].items():
        bank["OP020_hand_" + name] = np.array(
            [
                flange @ reuse.fingers._gripper_fk(urdf, q)[row["link"]] @ row["local"]
                for flange, q in zip(flanges, commands, strict=True)
            ]
        )
    for index in range(2):
        bank[f"header_{index}_position"] = np.array(payloads[index])
    bank["driver_position"] = np.array([driver_position(np.clip(t - 12, 0, 40)) for t in times])
    return bank, {
        "max_ik_residual": max(errors),
        "complete_ik_candidates": len(ranking),
        "max_sampled_joint_step_rad": float(abs(np.diff(joints, axis=0)).max()),
    }


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    assert reuse.sha(ROOT / "UR15_JB_initial_hands_v02.blend") == BASE_NATIVE_SHA
    rows, provenance = converted_meshes()
    payload = json.loads(gzip.decompress((ROOT / "data/hand_line_review_v01/meshes.json.gz").read_bytes()))
    urdf = ET.parse(reuse.URDF).getroot()
    hand = hand_profile(payload, urdf)
    bank, observations = motion_bank(hand, payload, urdf)
    (DATA / "meshes.json.gz").write_bytes(gzip.compress(json.dumps({"headers": rows, "hand": hand}).encode(), mtime=0))
    np.savez_compressed(DATA / "motion.npz", **bank)
    report = {
        "baseline_native_sha256": BASE_NATIVE_SHA,
        "official_cad": provenance,
        "header_bay_keys": [["A", "D", "E"], ["D", "F"]],
        "header_flange_widths_m": list(HEADER_WIDTH),
        "m4_count_by_header": [8, 6],
        "display_bolt_schedule": bolt_schedule(),
        "op020_task": "outer header installation and M4 fastening; internal contact housings are a later operation",
        "user_selection": "筐体側ヘッダーの設置・ねじ固定",
        "hand_q_closed_rad": hand["q_closed"],
        "hand_q_open_rad": hand["q_open"],
        "machine_and_grip_dimensions": "initial review geometry, not selected manufacturing specifications",
        "color_assignment": "presentation only; not source STEP material properties",
        "motion_observations": observations,
        "frame_end": END_FRAME,
        "source_files": {str(p.relative_to(ROOT)): reuse.sha(p) for p in (Path(__file__),)},
        "mesh_sha256": reuse.sha(DATA / "meshes.json.gz"),
        "motion_sha256": reuse.sha(DATA / "motion.npz"),
        "physical_validity_verdict": None,
    }
    (ROOT / "audit/header_review_v03_prepare.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("HEADER_REVIEW_PREPARED", json.dumps(observations), flush=True)


if __name__ == "__main__":
    if "/tmp/ur15-cad-tools" not in sys.path:
        sys.path.insert(0, "/tmp/ur15-cad-tools")
    main()
