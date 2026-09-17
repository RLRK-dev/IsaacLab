# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build an isolated, replaceable-dimension PGE finger sample [m], not an arm motion."""

import argparse
import copy
import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import trimesh
from audit_hvjb_compact_hand_v01 import _sha
from build_hand_fingertip_concepts_v01 import _box, _profile_prism, _serialize
from prepare_hand_working_default_v01 import load_working_default


def _world(mesh: trimesh.Trimesh, matrix: np.ndarray) -> trimesh.Trimesh:
    result = mesh.copy()
    result.apply_transform(matrix)
    return result


def _pad(radius: float, band: list[float], axis_z: float, thickness: float, half_angle: float) -> trimesh.Trimesh:
    angle = np.linspace(-np.deg2rad(half_angle), np.deg2rad(half_angle), 25)
    boundary = list(zip(radius * np.cos(angle), axis_z + radius * np.sin(angle), strict=True))
    boundary.extend(((radius + thickness, boundary[-1][1]), (radius + thickness, boundary[0][1])))
    return _profile_prism(boundary, "Y", *band, "pad")


def _beam_between(first: np.ndarray, second: np.ndarray, width: float, depth: float) -> trimesh.Trimesh:
    delta = second - first
    mesh = _box([width, depth, np.linalg.norm(delta)], [0, 0, 0], "insert")
    frame = trimesh.geometry.align_vectors([0, 0, 1], delta)
    frame[:3, 3] = (first + second) / 2
    mesh.apply_transform(frame)
    return mesh


def _build_hand(settings: dict, target: dict) -> tuple[dict, dict]:
    c = {key: np.asarray(value) / 1000 for key, value in settings["catalogue_geometry_mm"].items()}
    t = {key: np.asarray(value) / 1000 for key, value in settings["trial_geometry_mm"].items()}
    axis_z = target["seat_z_m"] + target["raw_barrel_axis_above_seat_m"]
    frame = trimesh.transformations.rotation_matrix(-np.deg2rad(settings["clockwise_tilt_deg"]), [1, 0, 0])
    frame[:3, 3] = [0, t["body_datum_y"], axis_z + t["body_datum_above_reference_wire_axis"]]
    parts = {}

    def add(name: str, mesh: trimesh.Trimesh, category: str, side: int = 0) -> None:
        obj = _serialize(mesh, category)
        obj["side"] = side
        obj["rigid_finger"] = side if category in {"insert", "pad"} else 0
        parts[name] = obj

    body_low = c["exposed_jaw_height"]
    add(
        "PGE_nominal_body_envelope",
        _world(
            _box(
                [c["body_width"], c["body_depth"], c["total_axial_length"] - body_low],
                [0, 0, (c["total_axial_length"] + body_low) / 2],
                "hardware",
            ),
            frame,
        ),
        "hardware",
    )
    radii = {"front": target["sleeve_outer_radius_m"], "root": target["wire_radius_m"]}
    rail_z = axis_z + t["rail_center_above_wire_axis"]
    shoe_width = c["jaw_face"]
    jaw_x = (t["jaw_gap_at_contour_match"] + shoe_width) / 2
    carrier_x = radii["front"] + t["pad_crown_thickness"] + t["carrier_thickness"] / 2
    for side, prefix in ((-1, "left"), (1, "right")):
        mirror = np.diag([side, 1, 1, 1])
        jaw = _world(_box([shoe_width, shoe_width, body_low], [jaw_x, 0, body_low / 2], "hardware"), frame)
        add(f"{prefix}_moving_jaw_envelope", _world(jaw, mirror), "hardware", side)
        shoe = _world(
            _box(
                [shoe_width, shoe_width, t["mounting_shoe_thickness"]],
                [jaw_x, 0, -t["mounting_shoe_thickness"] / 2],
                "insert",
            ),
            frame,
        )
        add(f"{prefix}_mounting_shoe", _world(shoe, mirror), "insert", side)
        start = (frame @ [carrier_x, 0, -t["mounting_shoe_thickness"] / 2, 1])[:3]
        end = np.array([carrier_x, t["body_datum_y"] - 0.006, rail_z])
        neck = _beam_between(start, end, t["carrier_thickness"], t["stem_yz_width"])
        add(f"{prefix}_offset_neck", _world(neck, mirror), "insert", side)
        low, high = t["front_band_y"][0], t["root_band_y"][1]
        rail = _box(
            [t["carrier_thickness"], high - low, t["rail_height"]], [carrier_x, (low + high) / 2, rail_z], "insert"
        )
        add(f"{prefix}_carrier_rail", _world(rail, mirror), "insert", side)
        for name, radius in radii.items():
            band = t[f"{name}_band_y"]
            pad = _pad(radius, band, axis_z, t["pad_crown_thickness"], settings["groove_half_angle_deg"])
            pad.visual.vertex_colors = [30, 152, 121, 255]
            add(f"{prefix}_{name}_pad", _world(pad, mirror), "pad", side)
            back = radius + t["pad_crown_thickness"]
            outer = carrier_x + t["carrier_thickness"] / 2
            bottom = axis_z - radius * np.sin(np.deg2rad(settings["groove_half_angle_deg"]))
            top = rail_z - t["rail_height"] / 2
            support = _box(
                [outer - back, band[1] - band[0], top - bottom],
                [(outer + back) / 2, band.mean(), (top + bottom) / 2],
                "insert",
            )
            add(f"{prefix}_{name}_pad_seat", _world(support, mirror), "insert", side)
    return parts, {"body_datum_world_m": frame.tolist(), "reference_wire_axis_z_m": axis_z}


def _observe(candidate: dict, frame: np.ndarray) -> dict:
    observations = {}
    fit = candidate["states"]["contour"]["transforms"]
    opened = candidate["states"]["open"]["transforms"]
    for side in (-1, 1):
        names = [name for name, obj in candidate["objects"].items() if obj.get("rigid_finger") == side]
        deltas = {name: (np.array(opened[name])[:3, 3] - np.array(fit[name])[:3, 3]).tolist() for name in names}
        if len({tuple(row) for row in deltas.values()}) != 1:
            raise AssertionError("Parts of one rigid finger have different displacements")
        points = np.concatenate([np.array(candidate["objects"][name]["vertices"]) for name in names])
        local = trimesh.transform_points(points, np.linalg.inv(frame))
        observations[str(side)] = {
            "parts": names,
            "opening_displacements_m": deltas,
            "finger_bounds_body_datum_m": [local.min(axis=0).tolist(), local.max(axis=0).tolist()],
            "finger_extent_m": np.ptp(local, axis=0).tolist(),
            "maximum_projection_below_jaw_face_m": float(-local[:, 2].min()),
            "projection_is_not_manufacturer_allowable_length": True,
        }
    return observations


def main() -> None:
    """Save new geometry and source evidence, leaving prior models unchanged."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_root", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists():
        raise FileExistsError(args.output_directory)
    config_path = args.source_root / "data/hvjb_pge_finger_v01.json"
    settings = json.loads(config_path.read_text())
    compact = json.loads((args.source_root / "data/hvjb_compact_hand_v01.json").read_text())
    pins = {**settings["pinned"], **compact["pinned"]}
    before = {name: _sha(args.source_root / name) for name in pins}
    if before != pins:
        raise AssertionError("A pinned input changed")
    old, provenance = load_working_default(source_directory=args.source_root / settings["legacy_source_directory"])
    original = old["candidates"]["T050"]
    target = old["config"]["target"]
    parts, geometry = _build_hand(settings, target)
    for name in settings["reference_objects"]:
        parts[name] = copy.deepcopy(original["objects"][name])
        parts[name]["side"] = 0
        parts[name]["rigid_finger"] = 0
    t = settings["trial_geometry_mm"]
    delta = (t["jaw_gap_at_open_display"] - t["jaw_gap_at_contour_match"]) / 2000
    states = {}
    for state, opening in (("contour", 0), ("open", delta)):
        transforms = {}
        for name, obj in parts.items():
            matrix = np.eye(4)
            matrix[0, 3] = obj["side"] * opening
            if name in settings["reference_objects"]:
                matrix = np.array(original["states"]["near"]["transforms"][name])
            transforms[name] = matrix.tolist()
        states[state] = {"transforms": transforms, "opening_per_jaw_m": opening}
    candidate = {"objects": parts, "states": states}
    observation = _observe(candidate, np.array(geometry["body_datum_world_m"]))
    payload = {
        "units": "m",
        "settings": settings,
        "reference_target": target,
        "geometry": geometry,
        "candidates": {"PGE_SAMPLE": candidate},
        "physical_verdict": None,
    }
    args.output_directory.mkdir(parents=True)
    mesh_path = args.output_directory / "hvjb_pge_finger_v01_meshes.json.gz"
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    mesh_path.write_bytes(gzip.compress(raw, mtime=0))
    if json.loads(gzip.decompress(mesh_path.read_bytes())) != payload:
        raise AssertionError("Saved geometry differs on readback")
    scene = trimesh.Scene()
    for name, obj in parts.items():
        mesh = trimesh.Trimesh(obj["vertices"], obj["faces"], process=False)
        mesh.visual.vertex_colors = obj["color"]
        scene.add_geometry(mesh, node_name=name, transform=states["contour"]["transforms"][name])
    glb_path = args.output_directory / "hvjb_pge_finger_v01.glb"
    glb_path.write_bytes(scene.export(file_type="glb"))
    after = {name: _sha(args.source_root / name) for name in pins}
    if before != after:
        raise AssertionError("A baseline changed during generation")
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "builder_sha256": _sha(Path(__file__)),
        "config_sha256": _sha(config_path),
        "baseline_before": before,
        "baseline_after": after,
        "legacy_resolution": provenance,
        "baseline_unchanged": True,
        "unchanged_reference_objects": settings["reference_objects"],
        "finger_observations": observation,
        "objects": len(parts),
        "finger_count": 2,
        "pad_count": 4,
        "actuator_count": 1,
        "mesh_sha256": _sha(mesh_path),
        "glb_sha256": _sha(glb_path),
        "json_readback_identical": True,
        "scope": "Constructed sample geometry and discrete translations; no physical or manufacturing verdict",
        "physical_verdict": None,
    }
    (args.output_directory / "hvjb_pge_finger_v01_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"PGE_FINGER_SAMPLE_BUILT objects={len(parts)} pads=4 baseline_unchanged=True")
    print(json.dumps({key: row["maximum_projection_below_jaw_face_m"] for key, row in observation.items()}))


if __name__ == "__main__":
    main()
