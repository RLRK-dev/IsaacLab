# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build an integral root-pad support while retaining D40 contact surfaces [m]."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _prepare(payload, settings, mount):
    import build_hand_fingertip_concepts_v01 as base
    import build_hand_terminal_concepts_v01 as terminal

    frame = np.asarray(mount["mount_frame_local"])
    operations = {}
    for name, source in settings["candidates"].items():
        candidate = payload["candidates"][source]
        for side in ("left_left", "left_right"):
            vertices = np.asarray(candidate["objects"][f"{side}_root_cable_backing"]["vertices"])
            local = (vertices - frame[:3, 3]) @ frame[:3, :3]
            seat = local[local[:, 2] > np.mean(local[:, 2])]
            coefficients = np.linalg.lstsq(np.c_[seat[:, :2], np.ones(4)], seat[:, 2], rcond=None)[0]
            bounds = []
            for feature in ("plate", "rail", "front"):
                u = np.array(settings[f"{feature}_u_m" if feature == "plate" else f"{feature}_u_left_m"])
                if feature != "plate" and side == "left_right":
                    u = -u[::-1]
                v = np.array(settings[f"{feature}_v_m"])
                if feature == "plate":
                    v[0] += 0.00025 if name == "J025" else 0.0005
                bounds.append(np.array([u, v, settings[f"{feature}_n_m"]]))
            support = np.array(
                [
                    [local[:, 0].min(), local[:, 0].max()],
                    [local[:, 1].min(), local[:, 1].max()],
                    [settings["plate_n_m"][1] - settings["construction_overlap_m"], 0.007],
                ]
            )
            bounds.append(support)
            pieces = [base._box(row[:, 1] - row[:, 0], row.mean(axis=1), "insert") for row in bounds]
            union = terminal._box_union(pieces)
            assert union.is_watertight and union.is_winding_consistent
            operations[f"{name}/{side}"] = {
                "body": {"vertices": union.vertices.tolist(), "faces": union.faces.tolist()},
                "mount_frame": mount["mount_frame_local"],
                "holes": [
                    {
                        "role": hole["role"],
                        "center": ((np.asarray(hole["center_local_m"]) - frame[:3, 3]) @ frame[:3, :3]).tolist(),
                    }
                    for hole in mount["holes"]
                ],
                "primitive_bounds_mount_m": [row.tolist() for row in bounds],
                "pad_seat_n_coefficients": coefficients.tolist(),
            }
    return operations


def _boolean_mode(directory):
    import bpy

    data = json.loads((directory / "support_boolean_inputs_v01.json").read_text())
    output = {}
    for name, row in data["operations"].items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = row["body"]
        mesh = bpy.data.meshes.new("integral_body")
        mesh.from_pydata((np.asarray(obj["vertices"]) * 1000).tolist(), [], obj["faces"])
        mesh.update()
        body = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(body)
        bpy.context.view_layer.objects.active = body

        def boolean(other, operation):
            modifier = body.modifiers.new(operation, "BOOLEAN")
            modifier.solver, modifier.operation, modifier.object = "EXACT", operation, other
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(other, do_unlink=True)

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
            cutter = bpy.context.object
            bpy.context.view_layer.objects.active = body
            boolean(cutter, "DIFFERENCE")
        modifier = body.modifiers.new("triangle_export", "TRIANGULATE")
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        vertices = np.array([list(vertex.co) for vertex in body.data.vertices]) / 1000
        selected = np.abs(vertices[:, 2] - 0.007) < 1e-8
        vertices[selected, 2] = np.c_[vertices[selected, :2], np.ones(selected.sum())] @ row["pad_seat_n_coefficients"]
        frame = np.array(row["mount_frame"])
        vertices = vertices @ frame[:3, :3].T + frame[:3, 3]
        output[name] = {
            "vertices": vertices.tolist(),
            "faces": [list(face.vertices) for face in body.data.polygons],
        }
        print(f"SUPPORT_BOOLEAN_DONE {name} vertices={len(body.data.vertices)}", flush=True)
    _write(directory / "support_boolean_meshes_v01.json", output)


def _ray_distances(triangles, origin, direction):
    first, second = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    cross = np.cross(np.broadcast_to(direction, second.shape), second)
    determinant = np.einsum("ij,ij->i", first, cross)
    nonparallel = np.abs(determinant) > 1e-18
    inv = np.zeros_like(determinant)
    inv[nonparallel] = 1 / determinant[nonparallel]
    offset = origin - triangles[:, 0]
    u = np.einsum("ij,ij->i", offset, cross) * inv
    q = np.cross(offset, first)
    v = q @ direction * inv
    t = np.einsum("ij,ij->i", second, q) * inv
    valid = nonparallel & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0)
    return sorted(float(x) for x in t[valid])


def _measure_body(original, obj, side, mount, settings):
    import trimesh

    mesh = trimesh.Trimesh(obj["vertices"], obj["faces"], process=False)
    components = trimesh.graph.connected_components(mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1)
    assert mesh.is_watertight and mesh.is_winding_consistent and len(components) == 1
    assert mesh.volume > 0
    frame = np.asarray(mount["mount_frame_local"])
    old_points = np.asarray(original["objects"][f"{side}_carrier"]["vertices"])
    old_local = (old_points - frame[:3, 3]) @ frame[:3, :3]
    backing = np.asarray(original["objects"][f"{side}_root_cable_backing"]["vertices"])
    backing_local = (backing - frame[:3, 3]) @ frame[:3, :3]
    # The library's fixed dot-product epsilon loses edge detail at metre scale.
    # Evaluate the same distance in mm, then return SI; do not change its epsilon.
    scaled_mesh = mesh.copy()
    scaled_mesh.apply_scale(1000)

    def distances_m(points):
        _, distances, _ = trimesh.proximity.closest_point_naive(scaled_mesh, np.asarray(points) * 1000)
        return distances / 1000

    # Sample the unchanged pad-seat rectangle, including its edges and centre.
    nearest_side = backing_local[:, 2] > np.mean(backing_local[:, 2])
    seat = backing[nearest_side]
    seat_center = seat.mean(axis=0)
    seat_samples = np.vstack([seat, seat_center, (seat + seat_center) / 2])
    seat_distances = distances_m(seat_samples)
    holes = {}
    normal = frame[:3, 2]
    for hole in mount["holes"]:
        center = np.asarray(hole["center_local_m"])
        hole_uv = (center - frame[:3, 3]) @ frame[:3, :3]
        radii = np.linalg.norm(old_local[:, :2] - hole_uv[:2], axis=1)
        rim = np.abs(radii - settings["nominal_bore_diameter_m"] / 2) < 1e-7
        assert rim.sum() >= 128, "Expected source bore rims missing"
        distances = distances_m(old_points[rim])
        # Rebuilding in the common mounting frame removes the old rail's micron
        # axial protrusion. Record that actual change; only radial/axis identity
        # is compared at the new body's defined mouth, mid-depth and bore end.
        projected = []
        for depth in (0.0, 0.002, settings["preserved_bore_depth_from_mount_face_m"]):
            points = old_local[rim].copy()
            points[:, 2] = depth
            projected.extend(points @ frame[:3, :3].T + frame[:3, 3])
        projected_distances = distances_m(projected)
        hits = _ray_distances(mesh.triangles, center - normal * 0.001, normal)
        hits = [value - 0.001 for value in hits if value <= 0.021]
        holes[hole["role"]] = {
            "rim_samples": int(rim.sum()),
            "source_rim_to_new_surface_max_m": float(distances.max()),
            "source_rim_n_bounds_m": [float(old_local[rim, 2].min()), float(old_local[rim, 2].max())],
            "source_uv_at_canonical_depths_samples": len(projected),
            "source_uv_at_canonical_depths_max_difference_m": float(projected_distances.max()),
            "canonical_depths_m": [0.0, 0.002, settings["preserved_bore_depth_from_mount_face_m"]],
            "axis_first_surface_n_m": min(hits) if hits else None,
            "ray_origin_n_m": -0.001,
            "ray_limit_n_m": 0.020,
        }
    assert (
        max(row["source_uv_at_canonical_depths_max_difference_m"] for row in holes.values())
        < settings["numerical_surface_comparison_tolerance_m"]
    )
    assert float(seat_distances.max()) < settings["numerical_surface_comparison_tolerance_m"]
    bore_depth = holes["screw_upper"]["axis_first_surface_n_m"]
    assert bore_depth is not None
    old_mesh = trimesh.Trimesh(old_points, original["objects"][f"{side}_carrier"]["faces"], process=False)
    external_samples = np.vstack([old_points, old_mesh.triangles_center])
    external_local = (external_samples - frame[:3, 3]) @ frame[:3, :3]
    covered = np.all(
        (external_local[:, :2] >= backing_local[:, :2].min(axis=0))
        & (external_local[:, :2] <= backing_local[:, :2].max(axis=0)),
        axis=1,
    ) & (external_local[:, 2] >= settings["plate_n_m"][1] - settings["construction_overlap_m"])
    external_distances = distances_m(external_samples[~covered])
    return {
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
        "connected_components": len(components),
        "closed_edge_topology": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "strict_zero_area_faces": np.flatnonzero(mesh.area_faces == 0).tolist(),
        "volume_m3": float(mesh.volume),
        "holes": holes,
        "surface_distance_method": "trimesh closest_point_naive on mm-scaled copies; returned in metres",
        "source_carrier_external_vertex_and_face_center_samples": int((~covered).sum()),
        "source_carrier_samples_covered_by_new_support": int(covered.sum()),
        "source_carrier_external_sample_to_new_surface_max_m": float(external_distances.max()),
        "pad_seat_samples": len(seat_samples),
        "pad_seat_surface_max_difference_m": float(seat_distances.max()),
        "bore_end_to_pad_seat_n_min_m": float(backing_local[nearest_side, 2].min() - bore_depth),
        "bore_end_to_pad_seat_n_max_m": float(backing_local[nearest_side, 2].max() - bore_depth),
    }


def _assemble(payload, settings, mount, geometry):
    result, reports = copy.deepcopy(payload), {}
    result["candidates"] = {}
    for name, source in settings["candidates"].items():
        original = payload["candidates"][source]
        candidate, rows = copy.deepcopy(original), {}
        for side in ("left_left", "left_right"):
            key, backing = f"{side}_carrier", f"{side}_root_cable_backing"
            candidate["objects"][key].update(geometry[f"{name}/{side}"])
            candidate["objects"][key]["integrated_from"] = [key, backing]
            candidate["objects"].pop(backing)
            for state in candidate["states"].values():
                state["transforms"].pop(backing)
            rows[side] = _measure_body(original, candidate["objects"][key], side, mount, settings)
        for key, obj in candidate["objects"].items():
            if not key.endswith("_carrier"):
                assert obj == original["objects"][key], key
            for state, snapshot in candidate["states"].items():
                assert snapshot["transforms"][key] == original["states"][state]["transforms"][key]
                assert snapshot["joint_q_rad"] == original["states"][state]["joint_q_rad"]
        result["candidates"][name] = candidate
        reports[name] = {"source_candidate": source, "body_observations": rows}
    result["support_integration_settings"] = settings
    return result, reports


def _observe(candidate, mount, service_settings, mount_settings, seat):
    import build_hand_body_setback_v01 as setback
    import build_hand_pad_service_v01 as service

    definitions = {}
    for side in service.SIDES:
        _, basis = service._frame(candidate, mount, "open", side)
        names = [
            key for key, obj in candidate["objects"].items() if obj["category"] == "insert" and key.startswith(side)
        ]
        assert len(names) == 3
        definitions[side] = {"moving_objects": names, "direction_world": basis[:, 2].tolist()}
    return {
        "service_definitions": definitions,
        "outer_screw_tool_axes": {
            state: {side: {hole: row["bands"]["outside"] for hole, row in rows.items()} for side, rows in sides.items()}
            for state, sides in service._axes(candidate, mount, service_settings).items()
        },
        "fastening_tool_surface_observations": setback._measure(candidate, mount_settings, seat),
    }


def build(args):
    import build_hand_fingertip_concepts_v01 as base
    import build_hand_mount_interface_v02 as mounting

    settings = json.loads(args.config.read_text())
    data = args.config.parent
    assert _sha(args.source) == settings["source_sha256"], "Relief source changed"
    for name, key in [
        ("hand_mount_interface_v02", "mount_settings_sha256"),
        ("hand_pad_service_v01", "service_settings_sha256"),
    ]:
        assert _sha(data / f"{name}.json") == settings[key]
    payload = json.loads(args.source.read_text())
    mount_settings = json.loads((data / "hand_mount_interface_v02.json").read_text())
    service_settings = json.loads((data / "hand_pad_service_v01.json").read_text())
    mount = mounting._mount_interface(
        payload["candidates"]["R025"]["objects"]["hardware_left_right_inner_finger_0"], mount_settings
    )
    args.directory.mkdir(parents=True, exist_ok=False)
    operations = _prepare(payload, settings, mount)
    _write(args.directory / "support_boolean_inputs_v01.json", {"settings": settings, "operations": operations})
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
    geometry = json.loads((args.directory / "support_boolean_meshes_v01.json").read_text())
    output, rows = _assemble(payload, settings, mount, geometry)
    for name, candidate in output["candidates"].items():
        rows[name].update(
            _observe(candidate, mount, service_settings, mount_settings, payload["config"]["target"]["seat_z_m"])
        )
        rows[name]["glb"] = base._export_glb(candidate, args.directory / f"hand_support_{name}_v01.glb")
    mesh_path = args.directory / "hand_support_integration_meshes_v01.json"
    _write(mesh_path, output)
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": _sha(args.source),
        "mesh_payload_sha256": _sha(mesh_path),
        "settings": settings,
        "mount": mount,
        "candidates": rows,
        "service_settings": service_settings["service"],
        "unchanged_hardware_contacts_colors_and_remaining_transforms": True,
        "changed_body_topology_is_not_vertex_identity": True,
        "pad_to_support_joint_selected": False,
        "physical_acceptance_verdict": None,
        "arm_motion_created": False,
        "video_created": False,
    }
    _write(args.directory / "hand_support_integration_observations_v01.json", report)
    template = Path(__file__).with_name("hand_support_integration_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(output, separators=(",", ":")))
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (args.directory / "根元支持部の一体化_v01.html").write_text(page)
    assert _sha(args.source) == settings["source_sha256"]
    print(json.dumps({name: row["body_observations"] for name, row in rows.items()}, indent=2), flush=True)
    print("HAND_SUPPORT_INTEGRATION_BUILD_DONE", flush=True)


def main() -> None:
    """Build a new static support comparison using the existing Boolean pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boolean_mode", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument(
        "--config", type=Path, default=Path(__file__).resolve().parents[1] / "data/hand_support_integration_v01.json"
    )
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    args = parser.parse_args(argv)
    if args.boolean_mode:
        _boolean_mode(args.directory)
    else:
        if args.source is None or args.blender is None:
            parser.error("--source and --blender are required outside --boolean_mode")
        build(args)


if __name__ == "__main__":
    main()
