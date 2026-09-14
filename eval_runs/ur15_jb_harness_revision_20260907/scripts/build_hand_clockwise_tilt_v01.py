# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tilt the existing black mechanism while preserving near-pose pad contacts [m]."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _transform(points, matrix):
    return np.asarray(points) @ matrix[:3, :3].T + matrix[:3, 3]


def _rotation(source, recipe, source_name, settings):
    frames = [
        np.array(source["states"]["near"]["transforms"][f"{side}_carrier"])
        @ np.array(recipe["operations"][f"{source_name}/{side}"]["mount_frame"])
        for side in ("left_left", "left_right")
    ]
    pivot = np.mean([frame[:3, 3] for frame in frames], axis=0)
    angle = np.deg2rad(settings["signed_rotation_deg"])
    cosine, sine = np.cos(angle), np.sin(angle)
    rotation = np.array([[1, 0, 0], [0, cosine, -sine], [0, sine, cosine]])
    matrix = np.eye(4)
    matrix[:3, :3], matrix[:3, 3] = rotation, pivot - rotation @ pivot
    return matrix, pivot


def _pieces(row, old_frame, new_frame):
    import build_hand_fingertip_concepts_v01 as base

    pieces, seats = [], []
    for index, bounds in enumerate(np.array(row["primitive_bounds_mount_m"])):
        mesh = base._box(bounds[:, 1] - bounds[:, 0], bounds.mean(axis=1), "insert")
        vertices = np.array(mesh.vertices)
        if index in (2, 3):
            key = "front_seat_n_coefficients" if index == 2 else "pad_seat_n_coefficients"
            selected = np.abs(vertices[:, 2] - bounds[2, 1]) < 1e-10
            vertices[selected, 2] = np.c_[vertices[selected, :2], np.ones(selected.sum())] @ row[key]
            seats.append({"piece": index, "corners_world_m": _transform(vertices[selected], old_frame).tolist()})
        # Only the plate follows the black finger. Rail and both pad supports
        # retain their original near world surfaces, then join the rotated plate.
        if index:
            vertices = _transform(_transform(vertices, old_frame), np.linalg.inv(new_frame))
        pieces.append({"vertices": vertices.tolist(), "faces": mesh.faces.tolist()})
    return pieces, seats


def _prepare(payload, recipe, settings):
    result, operations, records = copy.deepcopy(payload), {}, {}
    for name, source_name in settings["candidates"].items():
        source = payload["candidates"][source_name]
        candidate = copy.deepcopy(source)
        rotation, pivot = _rotation(source, recipe, source_name, settings)
        for state, snapshot in candidate["states"].items():
            delta = rotation.copy()
            if state == "clear":
                lift = np.eye(4)
                lift[2, 3] = settings["clear_reference_world_z_displacement_m"]
                delta = lift @ rotation @ np.linalg.inv(lift)
            for key, obj in candidate["objects"].items():
                if obj["category"] in ("hardware", "insert"):
                    snapshot["transforms"][key] = (delta @ np.array(snapshot["transforms"][key])).tolist()
        for key, obj in candidate["objects"].items():
            if obj["category"] == "insert" and not key.endswith("_carrier"):
                old = np.array(source["states"]["near"]["transforms"][key])
                new = np.array(candidate["states"]["near"]["transforms"][key])
                obj["vertices"] = _transform(_transform(obj["vertices"], old), np.linalg.inv(new)).tolist()
        seats = []
        for side in ("left_left", "left_right"):
            row = copy.deepcopy(recipe["operations"][f"{source_name}/{side}"])
            mount = np.array(row["mount_frame"])
            carrier = f"{side}_carrier"
            old_frame = np.array(source["states"]["near"]["transforms"][carrier]) @ mount
            new_frame = np.array(candidate["states"]["near"]["transforms"][carrier]) @ mount
            pieces, samples = _pieces(row, old_frame, new_frame)
            operations[f"{name}/{side}"] = {"pieces": pieces, "mount_frame": row["mount_frame"], "holes": row["holes"]}
            seats.extend({**sample, "carrier": carrier} for sample in samples)
        result["candidates"][name] = candidate
        records[name] = {"source_candidate": source_name, "pivot_world_m": pivot.tolist(), "pad_seats": seats}
    result["clockwise_tilt_settings"] = settings
    result["config"]["status"] = "0/15 degree static hand comparison; unchanged near pad contact locations"
    return result, operations, records


def _boolean_mode(directory):
    import bpy

    data = json.loads((directory / "tilt_boolean_inputs_v01.json").read_text())
    output = {}
    for key, row in data["operations"].items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bodies = []
        for index, piece in enumerate(row["pieces"]):
            mesh = bpy.data.meshes.new(f"nominal_{index}")
            mesh.from_pydata((np.array(piece["vertices"]) * 1000).tolist(), [], piece["faces"])
            mesh.update()
            obj = bpy.data.objects.new(mesh.name, mesh)
            bpy.context.collection.objects.link(obj)
            bodies.append(obj)
        body = bodies[0]
        bpy.context.view_layer.objects.active = body

        def boolean(other, operation):
            modifier = body.modifiers.new(operation, "BOOLEAN")
            modifier.solver, modifier.operation, modifier.object = "EXACT", operation, other
            bpy.context.view_layer.objects.active = body
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(other, do_unlink=True)

        for obj in bodies[1:]:
            boolean(obj, "UNION")
        for hole in row["holes"]:
            stop = data["settings"]["preserved_bore_depth_from_mount_face_m"] * 1000
            if hole["role"] != "screw_upper":
                stop += 2
            start = -2.0
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=data["settings"]["cylinder_segments"],
                radius=data["settings"]["nominal_bore_diameter_m"] * 500,
                depth=stop - start,
                location=(hole["center"][0] * 1000, hole["center"][1] * 1000, (start + stop) / 2),
            )
            boolean(bpy.context.object, "DIFFERENCE")
        modifier = body.modifiers.new("triangle_export", "TRIANGULATE")
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        vertices = np.array([list(vertex.co) for vertex in body.data.vertices]) / 1000
        output[key] = {
            "vertices": _transform(vertices, np.array(row["mount_frame"])).tolist(),
            "faces": [list(face.vertices) for face in body.data.polygons],
        }
        print(f"TILT_BOOLEAN_DONE {key} vertices={len(vertices)}", flush=True)
    _write(directory / "tilt_boolean_meshes_v01.json", output)


def _invariants(source, candidate, settings):
    import build_hand_body_setback_v01 as setback

    hardware, pads, targets, clear = {}, {}, {}, {}
    for key, obj in candidate["objects"].items():
        if obj["category"] == "hardware":
            assert obj == source["objects"][key], key
            hardware[key] = True
        if obj["category"] in ("target", "guide"):
            assert obj == source["objects"][key]
            assert all(
                s["transforms"][key] == source["states"][k]["transforms"][key] for k, s in candidate["states"].items()
            )
            targets[key] = True
        if obj["category"] == "insert" and not key.endswith("_carrier"):
            change = np.linalg.norm(
                setback._world(source, key, "near") - setback._world(candidate, key, "near"), axis=1
            )
            assert change.max() < settings["numerical_world_comparison_tolerance_m"]
            assert obj["faces"] == source["objects"][key]["faces"]
            assert obj["color"] == source["objects"][key]["color"]
            pads[key] = float(change.max())
        if obj["category"] in ("hardware", "insert"):
            difference = setback._world(candidate, key, "clear") - setback._world(candidate, key, "open")
            error = np.linalg.norm(difference - [0, 0, settings["clear_reference_world_z_displacement_m"]], axis=1)
            assert error.max() < settings["numerical_world_comparison_tolerance_m"]
            clear[key] = float(error.max())
    for state in candidate["states"]:
        a, b = candidate["states"][state], source["states"][state]
        assert {k: v for k, v in a.items() if k != "transforms"} == {k: v for k, v in b.items() if k != "transforms"}
    base = "hardware_left_gripper_base_0"
    old, new = [np.array(c["states"]["near"]["transforms"][base]) for c in (source, candidate)]
    rotation = (new @ np.linalg.inv(old))[:3, :3]
    angle = float(np.rad2deg(np.arctan2(rotation[2, 1], rotation[1, 1])))
    assert abs(angle - settings["signed_rotation_deg"]) < 1e-9
    return {
        "hardware_objects_local_mesh_color_unchanged": hardware,
        "targets_and_guide_unchanged": targets,
        "near_pad_world_vertex_max_change_m": pads,
        "clear_minus_open_vertical_lift_max_error_m": clear,
        "saved_joint_metadata_unchanged": True,
        "signed_world_x_rotation_deg": angle,
    }


def _support_observations(candidate, record, operations, recipe, settings):
    import build_hand_body_setback_v01 as setback
    import trimesh

    result = {}
    for side in ("left_left", "left_right"):
        key = f"{side}_carrier"
        obj = candidate["objects"][key]
        mesh = trimesh.Trimesh(setback._world(candidate, key, "near") * 1000, obj["faces"], process=False)
        components = trimesh.graph.connected_components(
            mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1
        )
        assert mesh.is_watertight and mesh.is_winding_consistent and len(components) == 1 and mesh.area_faces.min() > 0
        seats = []
        for seat in record["pad_seats"]:
            if seat["carrier"] != key:
                continue
            points = np.array(seat["corners_world_m"])
            samples = np.vstack([points, points.mean(axis=0), (points + points.mean(axis=0)) / 2])
            _, distance, _ = trimesh.proximity.closest_point_naive(mesh, samples * 1000)
            assert distance.max() / 1000 < settings["numerical_surface_comparison_tolerance_m"]
            seats.append(
                {
                    "piece": seat["piece"],
                    "sample_count": len(samples),
                    "max_surface_difference_m": float(distance.max() / 1000),
                }
            )
        operation = operations[side]
        frame = np.array(candidate["states"]["near"]["transforms"][key]) @ np.array(operation["mount_frame"])
        radius = recipe["settings"]["nominal_bore_diameter_m"] / 2
        angles = (
            np.arange(recipe["settings"]["cylinder_segments"]) * 2 * np.pi / recipe["settings"]["cylinder_segments"]
        )
        holes = []
        for hole in operation["holes"]:
            points = np.array(
                [
                    [hole["center"][0] + radius * np.cos(a), hole["center"][1] + radius * np.sin(a), n]
                    for n in (0, 0.002, 0.004)
                    for a in angles
                ]
            )
            _, distance, _ = trimesh.proximity.closest_point_naive(mesh, _transform(points, frame) * 1000)
            assert distance.max() / 1000 < settings["numerical_surface_comparison_tolerance_m"]
            holes.append(
                {
                    "role": hole["role"],
                    "samples": len(points),
                    "nominal_rim_max_surface_difference_m": float(distance.max() / 1000),
                }
            )
        result[key] = {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "closed": True,
            "components": len(components),
            "strict_zero_area_faces": 0,
            "seats": seats,
            "holes": holes,
        }
    return result


def build(args: argparse.Namespace) -> None:
    """Build a separate static tilt model and auxiliary surface records [m]."""
    import build_hand_fingertip_concepts_v01 as base
    import probe_hand_fastening_reference_v01 as reference
    import probe_hand_tool_access_v01 as probe

    settings = json.loads(args.config.read_text())
    assert settings["rotation_axis_world"] == [1.0, 0.0, 0.0]
    assert settings["signed_rotation_deg"] == -settings["clockwise_angle_deg"]
    assert base._digest(args.source) == settings["source_sha256"]
    assert base._digest(args.recipe) == settings["recipe_sha256"]
    source, recipe = json.loads(args.source.read_text()), json.loads(args.recipe.read_text())
    output, operations, records = _prepare(source, recipe, settings)
    args.directory.mkdir(parents=True, exist_ok=False)
    _write(args.directory / "tilt_boolean_inputs_v01.json", {"settings": recipe["settings"], "operations": operations})
    command = [
        str(args.blender),
        "--background",
        "--python-exit-code",
        "1",
        "--python",
        str(Path(__file__).resolve()),
        "--",
        "--boolean_mode",
        "--directory",
        str(args.directory),
    ]
    with (args.directory / "boolean.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    geometry = json.loads((args.directory / "tilt_boolean_meshes_v01.json").read_text())
    for name, record in records.items():
        candidate = output["candidates"][name]
        for side in ("left_left", "left_right"):
            candidate["objects"][f"{side}_carrier"].update(geometry[f"{name}/{side}"])
        record["invariants"] = _invariants(source["candidates"][record["source_candidate"]], candidate, settings)
        record["supports"] = _support_observations(
            candidate, record, {s: operations[f"{name}/{s}"] for s in ("left_left", "left_right")}, recipe, settings
        )
        record["glb"] = base._export_glb(candidate, args.directory / f"hand_clockwise_tilt_{name}_v01.glb")
    mesh_path = args.directory / "hand_clockwise_tilt_meshes_v01.json"
    _write(mesh_path, output)
    tool_settings = json.loads(args.reference_config.read_text())
    tool_settings["source_sha256"] = base._digest(mesh_path)
    observation = probe._observe(output, tool_settings)
    seat = output["config"]["target"]["seat_z_m"]
    for name, candidate in output["candidates"].items():
        for state in candidate["states"]:
            triangles, names, _ = probe._world_hand(candidate, state, tool_settings["axis_xy_m"])
            observation["states"][name][state]["references"] = {
                key: reference._placements(
                    triangles, names, part, tool_settings["comparison_part_lower_heights_above_seat_m"], seat
                )
                for key, part in tool_settings["references"].items()
            }
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "settings": tool_settings,
        "tilt_settings": settings,
        "source_sha256": base._digest(args.source),
        "recipe_sha256": base._digest(args.recipe),
        "mesh_sha256": base._digest(mesh_path),
        "construction": records,
        "analytic_checks": probe._analytic_checks(),
        "observation": observation,
        "limits": (
            "Static surface observations; no complete tool/nose outline, "
            "holding-load result, assembly quality or arm path"
        ),
        "physical_acceptance_verdict": None,
    }
    _write(args.directory / "hand_clockwise_tilt_observations_v01.json", report)
    template = Path(__file__).with_name("hand_clockwise_tilt_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(output, separators=(",", ":"))).replace(
        "__OBSERVATION_PAYLOAD__", json.dumps(report, ensure_ascii=False, separators=(",", ":"))
    )
    (args.directory / "フィンガ15度傾斜_v01.html").write_text(page)
    assert (
        base._digest(args.source) == settings["source_sha256"]
        and base._digest(args.recipe) == settings["recipe_sha256"]
    )
    print("HAND_CLOCKWISE_TILT_DONE", flush=True)


def main() -> None:
    """Create a new static comparison directory; keep source packages intact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--recipe", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--reference_config", type=Path)
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--boolean_mode", action="store_true")
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(values)
    if args.boolean_mode:
        _boolean_mode(args.directory)
    else:
        build(args)


if __name__ == "__main__":
    main()
