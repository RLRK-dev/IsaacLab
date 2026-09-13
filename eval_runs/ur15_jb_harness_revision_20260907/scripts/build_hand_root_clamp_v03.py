# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Extend the saved hand to a 40 mm initial setback and add root cable pads [m]."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path

import build_hand_body_setback_v01 as setback
import build_hand_fingertip_concepts_v01 as base
import numpy as np
import trimesh


def _profile(candidate, sign, axis_z, half_angle):
    wire = setback._world(candidate, "comparison_wire", "near")
    ring = wire[np.abs(wire[:, 1] - wire[:, 1].min()) < 1e-9][:, [0, 2]]
    radial = np.linalg.norm(ring - [0, axis_z], axis=1)
    radius = float(radial.max())
    ring = ring[radial > radius / 2]
    angles = np.arctan2(ring[:, 1] - axis_z, sign * ring[:, 0])
    ring = ring[np.abs(angles) <= np.deg2rad(half_angle) + 1e-6]
    ring = ring[np.argsort(ring[:, 1])]
    assert len(ring) >= 3
    return ring, radius


def _attach(candidate, mesh, carrier_name, suffix):
    name = carrier_name.removesuffix("_carrier") + suffix
    matrix = np.asarray(candidate["states"]["near"]["transforms"][carrier_name])
    local = mesh.copy()
    local.vertices = (mesh.vertices - matrix[:3, 3]) @ matrix[:3, :3]
    obj = base._serialize(local, "insert")
    # Preserve the sampled wire facets without rounding them to a new profile.
    obj["vertices"] = local.vertices.tolist()
    obj["group"] = "root_clamp"
    candidate["objects"][name] = obj
    for state in candidate["states"].values():
        state["transforms"][name] = copy.deepcopy(state["transforms"][carrier_name])
    return name


def _root_parts(candidate, config, settings):
    spec = settings["root_clamp"]
    y = config["mechanism"]["root_y_m"] + settings["initial_setback_m"]
    axis_z = config["target"]["seat_z_m"] + config["target"]["raw_barrel_axis_above_seat_m"]
    half = spec["contact_length_m"] / 2
    records = []
    carriers = [name for name in candidate["objects"] if name.endswith("_carrier")]
    for carrier in carriers:
        sign = np.sign(setback._world(candidate, carrier, "near")[:, 0].mean())
        ring, radius = _profile(candidate, sign, axis_z, spec["groove_half_angle_deg"])
        back = sign * spec["pad_back_plane_abs_x_m"]
        boundary = [*map(tuple, ring), (back, ring[-1, 1]), (back, ring[0, 1])]
        pad = base._profile_prism(boundary, "Y", y - half, y + half, "pad")
        pad.visual.vertex_colors = spec["pad_color_rgba"]
        outer = sign * spec["backing_outer_abs_x_m"]
        backing = base._box(
            (abs(outer - back), 2 * half, float(np.ptp(ring[:, 1]))),
            ((back + outer) / 2, y, float(np.mean(ring[[0, -1], 1]))),
            "insert",
        )
        for mesh in (pad, backing):
            assert mesh.is_watertight and mesh.is_winding_consistent
            assert float(mesh.area_faces.min()) > 0
        pad_name = _attach(candidate, pad, carrier, "_root_cable_pad")
        backing_name = _attach(candidate, backing, carrier, "_root_cable_backing")
        records.append(
            {
                "carrier": carrier,
                "pad": pad_name,
                "backing": backing_name,
                "sign_x": float(sign),
                "profile_points_near_xz_m": ring.tolist(),
                "reference_wire_radius_m": radius,
                "contact_y_range_m": [y - half, y + half],
                "crown_near_m": [float(sign * radius), y, axis_z],
                "crown_pad_thickness_m": abs(back) - radius,
                "new_meshes_closed_with_nonzero_faces": True,
            }
        )
    return records


def _contact_samples(record):
    ring = np.asarray(record["profile_points_near_xz_m"])
    # Include facet centers, not just points on the ideal circular perimeter.
    profile = np.vstack((ring, (ring[:-1] + ring[1:]) / 2))
    low, high = record["contact_y_range_m"]
    return np.array([(x, y, z) for y in (low, (low + high) / 2, high) for x, z in profile])


def _observe_root(candidate, records):
    wire_obj = candidate["objects"]["comparison_wire"]
    wire = trimesh.Trimesh(setback._world(candidate, "comparison_wire", "near"), wire_obj["faces"], process=False)
    result = {}
    for state_name, state in candidate["states"].items():
        rows, crowns = [], []
        for record in records:
            name = record["pad"]
            matrix = np.asarray(candidate["states"]["near"]["transforms"][name])
            current = np.asarray(state["transforms"][name])
            points = np.vstack((_contact_samples(record), record["crown_near_m"]))
            local = (points - matrix[:3, 3]) @ matrix[:3, :3]
            world = local @ current[:3, :3].T + current[:3, 3]
            crowns.append(world[-1])
            _, distances, _ = trimesh.proximity.closest_point_naive(wire, world[:-1])
            rows.append(
                {
                    "pad": name,
                    "sample_count": len(distances),
                    "unsigned_sample_to_wire_surface_min_m": float(distances.min()),
                    "unsigned_sample_to_wire_surface_max_m": float(distances.max()),
                    "crown_world_m": world[-1].tolist(),
                }
            )
        result[state_name] = {
            "pads": rows,
            "crown_to_crown_distance_m": float(np.linalg.norm(crowns[1] - crowns[0])),
        }
    return result


def _write_page(directory, payload, report):
    packed = json.dumps(payload, separators=(",", ":"))
    (directory / "hand_root_clamp_meshes_v03.json").write_text(packed + "\n")
    (directory / "hand_root_clamp_observations_v03.json").write_text(json.dumps(report, indent=2) + "\n")
    template = Path(__file__).with_name("hand_root_clamp_viewer_v03.html")
    page = template.read_text().replace("__MESH_PAYLOAD__", packed)
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (directory / "40mm後退と根元クランプ_v03.html").write_text(page)


def build(source: Path, config_path: Path, directory: Path) -> None:
    """Create a new static hand pack, preserving the source and terminal contacts."""
    settings = json.loads(config_path.read_text())
    source_sha = base._digest(source)
    assert source_sha == settings["source_mesh_sha256"], "Source SHA mismatch"
    payload = json.loads(source.read_text())
    original = payload["candidates"][settings["source_candidate"]]
    offset = settings["initial_setback_m"] - settings["source_setback_m"]
    candidate = setback._candidate(original, offset, settings)
    preservation = setback._preservation(original, candidate, offset, settings)
    parts = _root_parts(candidate, payload["config"], settings)
    contacts = _observe_root(candidate, parts)
    observed = setback._measure(candidate, settings, payload["config"]["target"]["seat_z_m"])
    directory.mkdir(parents=True, exist_ok=False)
    exported = base._export_glb(candidate, directory / "hand_root_clamp_D40_v03.glb")
    assert exported["mesh_count"] == exported["readback_mesh_count"]
    assert exported["readback_bounds_max_difference_m"] < 1e-7
    assert base._digest(source) == source_sha
    topology = {}
    for name, obj in candidate["objects"].items():
        if obj["category"] == "insert":
            mesh = trimesh.Trimesh(obj["vertices"], obj["faces"], process=False)
            topology[name] = {
                "closed_edge_topology": bool(mesh.is_watertight),
                "zero_area_faces": int(np.count_nonzero(mesh.area_faces == 0)),
            }
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "settings": settings,
        "source_sha256": source_sha,
        "source_file_unchanged": True,
        "config_sha256": base._digest(config_path),
        "candidates": {
            "D40": {
                "setback_m": settings["initial_setback_m"],
                "delta_from_source_m": offset,
                "preservation": preservation,
                "tool_surface_observations": observed,
                "root_parts": parts,
                "root_surface_samples": contacts,
                "insert_topology": topology,
                "glb": exported,
            }
        },
        "root_contact_method": "Unsigned distance from source-derived facet samples to the saved wire mesh",
        "pose_method": "All new root parts share the original carrier transforms in four saved poses",
        "same_actuator_dual_contact_force_distribution_confirmed": False,
        "terminal_contact_display_gap_m": payload["config"]["insert"]["edge_nominal_clearance_m"],
        "numerical_tolerances_are_acceptance_criteria": False,
        "continuous_motion_checked": False,
        "physical_acceptance_verdict": None,
    }
    config = copy.deepcopy(payload["config"])
    config["revision"] = "v03"
    config["status"] = "40 mm initial setback; static root-clamp comparison"
    config["mechanism"]["initial_setback_m"] = settings["initial_setback_m"]
    config["mechanism"]["mounting_basis"] = "v02 source-matched 2018 holes; screw engagement and strength unresolved"
    config["insert"]["guide_role"] = "Historical GUIDЕ geometry is absent; use active_root_clamp for v03"
    config["active_root_clamp"] = settings["root_clamp"]
    config["unresolved"] = [item for item in config["unresolved"] if "next station" not in item]
    config["unresolved"].append("Shared-actuator front/root force distribution while holding through fastening")
    _write_page(directory, {"config": config, "candidates": {"D40": candidate}}, report)
    (directory / "inputs").mkdir()
    shutil.copy2(source, directory / "inputs/hand_mount_interface_meshes_v02.json")
    print(json.dumps({"root_surface_samples": contacts, "insert_topology": topology}, indent=2), flush=True)
    print("HAND_ROOT_CLAMP_BUILD_DONE", flush=True)


def main() -> None:
    """Read the saved mounting model and emit a separate root-clamp comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.config, args.directory)


if __name__ == "__main__":
    main()
