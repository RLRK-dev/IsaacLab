# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Move the static front grasp to the terminal-side black covering [m]."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


def _profile(candidate, settings, sign, axis_z):
    import build_hand_body_setback_v01 as setback

    vertices = setback._world(candidate, settings["source_sleeve_object"], "near")
    ring = vertices[np.abs(vertices[:, 1] - vertices[:, 1].min()) < 1e-9][:, [0, 2]]
    radius = np.linalg.norm(ring - [0, axis_z], axis=1)
    # Serialized coordinates round the outer radius by about 1 nm. Separate the
    # annulus's two rings at their largest radial gap instead of dropping facets
    # with an equality test against the single farthest vertex.
    ordered = np.sort(radius)
    split = int(np.argmax(np.diff(ordered)))
    ring = ring[radius > (ordered[split] + ordered[split + 1]) / 2]
    assert len(ring) == 96, "Unexpected source outer ring"
    outer = float(np.abs(ring[:, 0]).max())
    angles = np.arctan2(ring[:, 1] - axis_z, sign * ring[:, 0])
    ring = ring[np.abs(angles) <= np.deg2rad(settings["groove_half_angle_deg"]) + 1e-6]
    ring = ring[np.argsort(ring[:, 1])]
    assert len(ring) == 25, "Unexpected source sleeve facets"
    return ring, outer


def _prepare(payload, recipe, settings):
    import build_hand_fingertip_concepts_v01 as base
    import build_hand_root_clamp_v03 as root
    import build_hand_terminal_concepts_v01 as terminal

    result, operations, contacts = copy.deepcopy(payload), {}, {}
    result["candidates"] = {}
    axis_z = payload["config"]["target"]["seat_z_m"] + payload["config"]["target"]["raw_barrel_axis_above_seat_m"]
    low, high = settings["front_contact_y_range_m"]
    for name, source in settings["candidates"].items():
        candidate = copy.deepcopy(payload["candidates"][source])
        contacts[name] = []
        for side, sign in (("left_left", -1), ("left_right", 1)):
            carrier, removed = f"{side}_carrier", f"{side}_edge_contour"
            candidate["objects"].pop(removed)
            for state in candidate["states"].values():
                state["transforms"].pop(removed)
            ring, radius = _profile(candidate, settings, sign, axis_z)
            back = sign * settings["front_pad_back_abs_x_m"]
            boundary = [*map(tuple, ring), (back, ring[-1, 1]), (back, ring[0, 1])]
            pad = base._profile_prism(boundary, "Y", low, high, "pad")
            pad.visual.vertex_colors = settings["pad_color_rgba"]
            pad_name = root._attach(candidate, pad, carrier, "_sleeve_pad")
            candidate["objects"][pad_name]["group"] = "front_sleeve_clamp"
            row = copy.deepcopy(recipe["operations"][f"{source}/{side}"])
            frame = np.array(row["mount_frame"])
            matrix = np.array(candidate["states"]["near"]["transforms"][carrier])
            world_frame = matrix @ frame
            seat = np.array([(back, y, z) for y in (low, high) for z in ring[[0, -1], 1]])
            uvn = (seat - world_frame[:3, 3]) @ world_frame[:3, :3]
            coefficients = np.linalg.lstsq(np.c_[uvn[:, :2], np.ones(4)], uvn[:, 2], rcond=None)[0]
            bounds = np.array(row["primitive_bounds_mount_m"])
            rail = np.array(settings["rail_u_left_m"])
            bounds[1, 0] = rail if side == "left_left" else -rail[::-1]
            bounds[2] = np.array(
                [
                    [uvn[:, 0].min(), uvn[:, 0].max()],
                    [uvn[:, 1].min(), uvn[:, 1].max()],
                    [0.0035, settings["front_support_n_max_m"]],
                ]
            )
            union = terminal._box_union([base._box(b[:, 1] - b[:, 0], b.mean(axis=1), "insert") for b in bounds])
            assert union.is_watertight and union.is_winding_consistent
            row["body"] = {"vertices": union.vertices.tolist(), "faces": union.faces.tolist()}
            row["primitive_bounds_mount_m"] = bounds.tolist()
            row["front_seat_n_coefficients"] = coefficients.tolist()
            row["front_support_n_max_m"] = settings["front_support_n_max_m"]
            operations[f"{name}/{side}"] = row
            contacts[name].append(
                {
                    "pad": pad_name,
                    "side": side,
                    "carrier": carrier,
                    "profile_points_near_xz_m": ring.tolist(),
                    "reference_radius_m": radius,
                    "contact_y_range_m": [low, high],
                    "seat_corners_world_m": seat.tolist(),
                    "crown_near_m": [sign * radius, (low + high) / 2, axis_z],
                    "crown_pad_thickness_m": abs(back) - radius,
                }
            )
        result["candidates"][name] = candidate
    result["front_sleeve_clamp_settings"] = settings
    result["config"]["active_front_clamp"] = settings
    result["config"]["status"] = "Black-sleeve front grasp with retained root jacket pads; static comparison"
    result["config"]["insert"]["edge_profile_basis"] = "Historical metal-edge contours removed; use active_front_clamp"
    return result, operations, contacts


def _finish_geometry(geometry, operations):
    for key, obj in geometry.items():
        row = operations[key]
        frame = np.array(row["mount_frame"])
        points = (np.array(obj["vertices"]) - frame[:3, 3]) @ frame[:3, :3]
        selected = np.abs(points[:, 2] - row["front_support_n_max_m"]) < 1e-8
        assert selected.sum() >= 4
        points[selected, 2] = np.c_[points[selected, :2], np.ones(selected.sum())] @ row["front_seat_n_coefficients"]
        obj["vertices"] = (points @ frame[:3, :3].T + frame[:3, 3]).tolist()


def _contact_observations(candidate, contacts, settings):
    import build_hand_body_setback_v01 as setback
    import build_hand_root_clamp_v03 as root
    import trimesh

    obj = candidate["objects"][settings["source_sleeve_object"]]
    sleeve = trimesh.Trimesh(
        setback._world(candidate, settings["source_sleeve_object"], "near") * 1000, obj["faces"], process=False
    )
    result = {}
    for state, snapshot in candidate["states"].items():
        observations, crowns = [], []
        for row in contacts:
            matrix = np.array(candidate["states"]["near"]["transforms"][row["pad"]])
            current = np.array(snapshot["transforms"][row["pad"]])
            points = np.vstack([root._contact_samples(row), row["crown_near_m"]])
            local = (points - matrix[:3, 3]) @ matrix[:3, :3]
            world = local @ current[:3, :3].T + current[:3, 3]
            crowns.append(world[-1])
            _, distance, _ = trimesh.proximity.closest_point_naive(sleeve, world[:-1] * 1000)
            observations.append(
                {
                    "pad": row["pad"],
                    "sample_count": len(distance),
                    "unsigned_surface_min_m": float(distance.min() / 1000),
                    "unsigned_surface_max_m": float(distance.max() / 1000),
                    "crown_world_m": world[-1].tolist(),
                }
            )
        result[state] = {
            "pads": observations,
            "crown_to_crown_distance_m": float(np.linalg.norm(crowns[1] - crowns[0])),
        }
    return result


def _body_observations(candidate, rows):
    import build_hand_body_setback_v01 as setback
    import trimesh

    result = {}
    for row in rows:
        key = row["carrier"]
        obj = candidate["objects"][key]
        mesh = trimesh.Trimesh(setback._world(candidate, key, "near"), obj["faces"], process=False)
        components = trimesh.graph.connected_components(
            mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1
        )
        assert mesh.is_watertight and mesh.is_winding_consistent and len(components) == 1
        assert mesh.area_faces.min() > 0
        mesh.apply_scale(1000)
        seat = np.array(row["seat_corners_world_m"])
        samples = np.vstack([seat, seat.mean(axis=0), (seat + seat.mean(axis=0)) / 2])
        _, distance, _ = trimesh.proximity.closest_point_naive(mesh, samples * 1000)
        assert distance.max() / 1000 < 1e-7
        result[key] = {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "closed": True,
            "components": len(components),
            "zero_area_faces": 0,
            "front_pad_seat_sample_max_difference_m": float(distance.max() / 1000),
        }
    return result


def build(args: argparse.Namespace) -> None:
    """Build separate sleeve-contact models and auxiliary records [m]."""
    import build_hand_body_setback_v01 as setback
    import build_hand_fingertip_concepts_v01 as base
    import build_hand_support_integration_v01 as support
    import probe_hand_tool_access_v01 as probe

    settings = json.loads(args.config.read_text())
    assert base._digest(args.source) == settings["source_sha256"]
    assert base._digest(args.recipe) == settings["recipe_sha256"]
    original = json.loads(args.source.read_text())
    recipe = json.loads(args.recipe.read_text())
    output, operations, contacts = _prepare(original, recipe, settings)
    args.directory.mkdir(parents=True, exist_ok=False)
    support._write(
        args.directory / "support_boolean_inputs_v01.json", {"settings": recipe["settings"], "operations": operations}
    )
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
    _finish_geometry(geometry, operations)
    records = {}
    tool_settings = {
        "tool_lower_z_above_seat_m": [0.0038, 0.0538],
        "tool_upper_z_above_seat_m": [0.0538, 0.1888769757245636],
    }
    seat = output["config"]["target"]["seat_z_m"]
    for name, candidate in output["candidates"].items():
        source = original["candidates"][settings["candidates"][name]]
        for side in ("left_left", "left_right"):
            candidate["objects"][f"{side}_carrier"].update(geometry[f"{name}/{side}"])
        for key, obj in source["objects"].items():
            if key.endswith(("_carrier", "_edge_contour")):
                continue
            assert candidate["objects"][key] == obj, key
        for state, snapshot in candidate["states"].items():
            assert snapshot["joint_q_rad"] == source["states"][state]["joint_q_rad"]
            for key, matrix in snapshot["transforms"].items():
                old_key = key.removesuffix("_sleeve_pad") + "_carrier" if key.endswith("_sleeve_pad") else key
                assert matrix == source["states"][state]["transforms"][old_key]
        clearances = {}
        for label, model in (("old", source), ("new", candidate)):
            triangles, names, _ = probe._world_hand(model, "near", [0, 0])
            clearances[label] = probe._slab_nearest(triangles, names, [seat, seat + 0.0538])
        records[name] = {
            "contacts": contacts[name],
            "contact_observations": _contact_observations(candidate, contacts[name], settings),
            "body_topology": _body_observations(candidate, contacts[name]),
            "near_tool_band_comparison": clearances,
            "tool_surface_observations": setback._measure(candidate, tool_settings, seat),
            "glb": base._export_glb(candidate, args.directory / f"hand_sleeve_{name}_v01.glb"),
        }
    support._write(args.directory / "hand_sleeve_clamp_meshes_v01.json", output)
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "settings": settings,
        "source_sha256": base._digest(args.source),
        "candidates": records,
        "hardware_root_pads_targets_and_poses_preserved": True,
        "metal_edge_contacts_removed": True,
        "material_force_sleeve_slip_and_terminal_location_validated": False,
        "physical_acceptance_verdict": None,
        "arm_motion_created": False,
        "video_created": False,
    }
    support._write(args.directory / "hand_sleeve_clamp_observations_v01.json", report)
    template = Path(__file__).with_name("hand_sleeve_clamp_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(output, separators=(",", ":")))
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (args.directory / "黒被覆側クランプ_v01.html").write_text(page)
    assert base._digest(args.source) == settings["source_sha256"]
    assert base._digest(args.recipe) == settings["recipe_sha256"]
    print(
        json.dumps(
            {
                name: {k: row[k] for k in ("contact_observations", "body_topology", "near_tool_band_comparison")}
                for name, row in records.items()
            },
            indent=2,
        )
    )
    print("HAND_SLEEVE_CLAMP_BUILD_DONE", flush=True)


def main() -> None:
    """Read a fixed source and write a new static sleeve-grasp comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boolean_mode", action="store_true")
    for name in ("source", "recipe", "config", "blender", "directory"):
        parser.add_argument(f"--{name}", type=Path, required=name == "directory")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None)
    if args.boolean_mode:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import build_hand_support_integration_v01 as support

        support._boolean_mode(args.directory)
    else:
        if any(getattr(args, name) is None for name in ("source", "recipe", "config", "blender")):
            parser.error("--source, --recipe, --config and --blender are required")
        build(args)


if __name__ == "__main__":
    main()
