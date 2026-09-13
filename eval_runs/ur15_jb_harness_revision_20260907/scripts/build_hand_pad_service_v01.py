# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Observe retained D40 mounting access and prepare isolated service views [m]."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
from datetime import datetime
from pathlib import Path

import build_hand_body_setback_v01 as setback
import build_hand_mount_interface_v02 as mounting
import numpy as np
import probe_hand_tool_access_v01 as access

SIDES = ("left_left", "left_right")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _frame(candidate, mount, state, side):
    transform = np.asarray(candidate["states"][state]["transforms"][f"{side}_carrier"])
    basis = transform[:3, :3] @ np.asarray(mount["mount_frame_local"])[:3, :3]
    assert np.max(np.abs(basis.T @ basis - np.eye(3))) < 1e-10
    return transform, basis


def _groups(candidate):
    objects = candidate["objects"]
    groups = {
        "hardware": [name for name, obj in objects.items() if obj["category"] == "hardware"],
        "carriers": [name for name in objects if name.endswith("_carrier")],
        "root_parts": [name for name, obj in objects.items() if obj.get("group") == "root_clamp"],
        "all_hand": [name for name, obj in objects.items() if obj["category"] in ("hardware", "insert")],
    }
    groups.update({name: [name] for name in groups["root_parts"]})
    return groups


def _axis_observation(candidate, state, origin, basis, names, band):
    triangles, face_names = [], []
    for name in names:
        world = setback._world(candidate, name, state)
        aligned = (world - origin) @ basis
        tri = aligned[np.asarray(candidate["objects"][name]["faces"])]
        triangles.append(tri)
        face_names.extend([name] * len(tri))
    result = access._slab_nearest(np.concatenate(triangles), face_names, band)
    if result["witness_m"] is not None:
        result["witness_world_m"] = (np.asarray(result["witness_m"]) @ basis.T + origin).tolist()
    result["objects_considered"] = names
    return result


def _axes(candidate, mount, settings):
    groups = _groups(candidate)
    records = {}
    key_radius = settings["tool_comparison"]["hex_across_flats_m"] / math.sqrt(3)
    for state in candidate["states"]:
        records[state] = {}
        for side in SIDES:
            transform, basis = _frame(candidate, mount, state, side)
            rows = {}
            for hole in mount["holes"]:
                if hole["role"] == "index":
                    continue
                origin = transform[:3, :3] @ hole["center_local_m"] + transform[:3, 3]
                row = {"origin_world_m": origin.tolist(), "outward_normal_world": basis[:, 2].tolist(), "bands": {}}
                for direction, band in settings["tool_axial_bands_from_mount_face_m"].items():
                    observation = {
                        group: _axis_observation(candidate, state, origin, basis, names, band)
                        for group, names in groups.items()
                    }
                    radius = observation["all_hand"]["radius_to_surface_m"]
                    row["bands"][direction] = {
                        "limits_from_mount_face_m": band,
                        "groups": observation,
                        "radius_minus_hex_envelope_m": None if radius is None else radius - key_radius,
                    }
                rows[hole["role"]] = row
            records[state][side] = rows
    return records


def _service_definition(candidate, mount, settings):
    state = settings["service"]["base_state"]
    result = {}
    for side in SIDES:
        _, basis = _frame(candidate, mount, state, side)
        names = [
            name for name, obj in candidate["objects"].items() if obj["category"] == "insert" and name.startswith(side)
        ]
        assert len(names) == 4
        result[side] = {"moving_objects": names, "direction_world": basis[:, 2].tolist()}
    return result


def _native_payload(payload, definitions, settings):
    result = copy.deepcopy(payload)
    candidate = result["candidates"][settings["source_candidate"]]
    original = candidate["states"][settings["service"]["base_state"]]
    distance = settings["service"]["offsets_m"][-1]
    for side, definition in definitions.items():
        state = copy.deepcopy(original)
        delta = np.asarray(definition["direction_world"]) * distance
        for name in definition["moving_objects"]:
            matrix = np.asarray(state["transforms"][name])
            matrix[:3, 3] += delta
            state["transforms"][name] = matrix.tolist()
        state["diagnostic_service_only"] = True
        state["hidden_reference_objects"] = True
        candidate["states"][f"service_{side}"] = state
    return result


def build(source: Path, config_path: Path, mount_settings: Path, directory: Path) -> None:
    """Write a separate service study while retaining input geometry and poses."""
    settings = json.loads(config_path.read_text())
    assert _sha(source) == settings["source_mesh_sha256"], "D40 source SHA mismatch"
    assert _sha(mount_settings) == settings["mount_settings_sha256"], "Mount settings SHA mismatch"
    payload = json.loads(source.read_text())
    before = json.dumps(payload, sort_keys=True)
    candidate = payload["candidates"][settings["source_candidate"]]
    mount = mounting._mount_interface(
        candidate["objects"]["hardware_left_right_inner_finger_0"], json.loads(mount_settings.read_text())
    )
    observations = _axes(candidate, mount, settings)
    definitions = _service_definition(candidate, mount, settings)
    native = _native_payload(payload, definitions, settings)
    assert before == json.dumps(payload, sort_keys=True)
    assert _sha(source) == settings["source_mesh_sha256"]
    changed = native["candidates"][settings["source_candidate"]]
    assert candidate["objects"] == changed["objects"]
    assert all(value == changed["states"][key] for key, value in candidate["states"].items())
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "settings": settings,
        "input_sha256": {"mesh": _sha(source), "settings": _sha(config_path), "mount_settings": _sha(mount_settings)},
        "source_file_unchanged": True,
        "all_original_objects_and_four_states_unchanged": True,
        "original_mesh_count_excluding_guides": sum(o["category"] != "guide" for o in candidate["objects"].values()),
        "mount_interface": mount,
        "projection_analytic_checks": access._analytic_checks(),
        "hex_circumscribed_radius_m": settings["tool_comparison"]["hex_across_flats_m"] / math.sqrt(3),
        "tool_axes": observations,
        "service_definitions": definitions,
        "measurement_method": "Triangle surfaces clipped axially and projected radially around measured mounting axes",
        "limitations": [
            "Surface distance only; no signed volume or solid containment classification",
            "Includes all hand surfaces; excludes removed workpiece, screws, indexing pin and complete tool handle",
            "Four saved gripper poses, not continuous loaded opening or an arm path",
            "Standard 2 mm hex key reference and illustrative 50 mm shaft extent, not an actual selected tool",
            "Custom pad-to-support attachment, screw length, engagement, index pin and strength remain unset",
        ],
        "physical_acceptance_verdict": None,
    }
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "inputs").mkdir()
    (directory / "data").mkdir()
    shutil.copy2(source, directory / "inputs/hand_root_clamp_meshes_v03.json")
    shutil.copy2(config_path, directory / "data/hand_pad_service_v01.json")
    shutil.copy2(mount_settings, directory / "data/hand_mount_interface_v02.json")
    _write(directory / "hand_pad_service_observations_v01.json", report)
    _write(directory / "hand_pad_service_meshes_v01.json", native)
    template = Path(__file__).with_name("hand_pad_service_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(payload, separators=(",", ":")))
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (directory / "根元パッドの交換と取付_v01.html").write_text(page)
    print(
        json.dumps({"source_unchanged": True, "service_definitions": definitions, "tool_axes": observations}, indent=2)
    )
    print("HAND_PAD_SERVICE_BUILD_DONE", flush=True)


def main() -> None:
    """Read the pinned D40 sample and emit a new service-view directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--mount_settings", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.config, args.mount_settings, args.directory)


if __name__ == "__main__":
    main()
