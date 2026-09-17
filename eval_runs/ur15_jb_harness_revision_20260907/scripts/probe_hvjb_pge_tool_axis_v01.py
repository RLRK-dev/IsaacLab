# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Observe axis-to-surface distances [m] on the unchanged isolated PGE sample."""

import argparse
import gzip
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from export_hvjb_pge_finger_v01 import _color_key
from probe_hand_tool_access_v01 import _analytic_checks, _slab_nearest

PINS = {
    "data/hvjb_pge_finger_v01_meshes.json.gz": "c9171a968fd38b263099b21627a31fe37cab61a5e98b8d494ea3a38abfef4570",
    "data/hand_tool_interface_inputs_v01.json": "91f6a2fbb150c5ae29b7b921044f47f7ea98694e24026b290023d7676cbee392",
    "data/hvjb_robot_selection_v01.json": "ad1d0fc6ad2f0c9d36f4d9839faf559ce80aa9ffb4965174facef944f1a58db8",
    "data/hvjb_task_occupancy_v01.json": "4da5b53687b05cd2cd1d294cf57121abde6ee9d04b19ed0a37ef2fb2a4d79df9",
    "scripts/probe_hand_tool_access_v01.py": "55456e6d55f84931bcc3f502e77372414a6efa2578e27970d5620f176c53417c",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _triangles(candidate: dict, state: str, axis: list[float]) -> tuple[np.ndarray, list[str], list[dict]]:
    surfaces, names, rows = [], [], []
    for name, obj in candidate["objects"].items():
        if obj["category"] not in {"hardware", "insert", "pad"}:
            continue
        matrix = np.asarray(candidate["states"][state]["transforms"][name])
        world = np.asarray(obj["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3]
        world[:, :2] -= axis
        triangles = world[np.asarray(obj["faces"])]
        surfaces.append(triangles)
        names.extend([name] * len(triangles))
        rows.append({"name": name, "category": obj["category"], "triangles": len(triangles)})
    return np.concatenate(surfaces), names, rows


def _observe(candidate: dict, frame: dict) -> dict:
    seat = frame["terminal_seat_z_m"]
    geometry = {state: _triangles(candidate, state, frame["tool_axis_xy_m"]) for state in candidate["states"]}
    top = max(float(item[0][:, :, 2].max()) for item in geometry.values())
    bands = {"tip": [seat + 0.0038, seat + 0.0538], "upper": [seat + 0.0538, top]}
    result = {}
    for state, (triangles, names, objects) in geometry.items():
        measured = {}
        for name, limits in bands.items():
            row = _slab_nearest(triangles, names, limits)
            row["z_above_reference_seat_m"] = [height - seat for height in limits]
            measured[name] = row
        step = 0.002
        boundaries = np.arange(math.ceil((top - seat) / step) + 1) * step + seat
        profile = []
        for lower, upper in zip(boundaries[:-1], boundaries[1:], strict=True):
            profile.append(
                {
                    "z_above_reference_seat_m": [lower - seat, upper - seat],
                    **_slab_nearest(triangles, names, [lower, upper]),
                }
            )
        result[state] = {"objects": objects, "bands": measured, "profile": profile}
    return {"states": result, "hand_top_z_m": top, "profile_bin_height_m": 0.002}


def _viewer(candidate: dict, report: dict) -> dict:
    objects = {}
    identity = np.eye(4).tolist()
    for name, obj in candidate["objects"].items():
        if candidate["states"]["contour"]["transforms"][name] != identity:
            raise AssertionError("The inherited viewer needs contour geometry already in world coordinates")
        expected_open = np.eye(4)
        expected_open[0, 3] = obj["side"] * candidate["states"]["open"]["opening_per_jaw_m"]
        if not np.array_equal(candidate["states"]["open"]["transforms"][name], expected_open):
            raise AssertionError("The displayed opening differs from the measured saved matrix")
        objects[name] = {
            "vertices": obj["vertices"],
            "faces": obj["faces"],
            "side": obj["side"],
            "color_key": _color_key(name, obj["category"]),
        }
    return {
        "objects": objects,
        "opening_m": candidate["states"]["open"]["opening_per_jaw_m"],
        "frame": report["reference_frame"],
        "measurements": report["measurements"],
    }


def main() -> None:
    """Write new observations and a comparison view without editing any input scene."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_root", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists():
        raise FileExistsError(args.output_directory)
    root = args.source_root
    compact = json.loads((root / "data/hvjb_compact_hand_v01.json").read_text())
    pins = {**compact["pinned"], **PINS}
    before = {name: _sha(root / name) for name in pins}
    if before != pins:
        raise AssertionError("A pinned input changed")
    payload = json.loads(gzip.decompress((root / "data/hvjb_pge_finger_v01_meshes.json.gz").read_bytes()))
    source_snapshot = json.dumps(payload, sort_keys=True)
    candidate = payload["candidates"]["PGE_SAMPLE"]
    interface = json.loads((root / "data/hand_tool_interface_inputs_v01.json").read_text())
    work = json.loads((root / "data/hvjb_task_occupancy_v01.json").read_text())
    frame = interface["reference_frame"]
    if frame["tool_reference_axis_world"] != [0, 0, 1]:
        raise AssertionError("The reused horizontal-distance method requires a vertical reference axis")
    if payload["reference_target"]["seat_z_m"] != frame["terminal_seat_z_m"]:
        raise AssertionError("Reference seat mismatch")
    checks = _analytic_checks()
    observed = _observe(candidate, frame)
    for state in observed["states"].values():
        if len(state["objects"]) != 17 or sum(obj["category"] == "pad" for obj in state["objects"]) != 4:
            raise AssertionError("The saved hand's object coverage changed")
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Unchanged nominal PGE sample; horizontal axis-to-hand distance, not complete-tool clearance",
        "reference_frame": frame,
        "reference_target": payload["reference_target"],
        "measurements": observed,
        "method": "Existing exact triangle Z-band clipping followed by XY axis distance and a 3D witness",
        "bands_are": "Observation ranges inherited from the older hand comparison, not selected tool dimensions",
        "included_categories": ["hardware", "insert", "pad"],
        "excluded_reference_objects": payload["settings"]["reference_objects"],
        "scene_obstacles_included": False,
        "source_geometry_and_states_unchanged": source_snapshot == json.dumps(payload, sort_keys=True),
        "analytic_checks": checks,
        "selected_role_plan": "S5_AB",
        "all_task_ids": [row["id"] for row in work["cards"]],
        "workcard_D60": next(row for row in work["cards"] if row["id"] == "D60"),
        "product_overlay": "Deferred: 15.2 mm reference sleeve and 5.6 mm photo-display sleeve are different proxies",
        "complete_tool_geometry": None,
        "allowable_tool_diameter_m": None,
        "required_clearance_m": None,
        "physical_acceptance_verdict": None,
    }
    after = {name: _sha(root / name) for name in pins}
    if before != after or not report["source_geometry_and_states_unchanged"]:
        raise AssertionError("Read-only observation changed an input")
    report["input_sha256_before"] = before
    report["input_sha256_after"] = after
    report["probe_sha256"] = _sha(Path(__file__))
    template = Path(__file__).with_name("hvjb_pge_tool_axis_v01.html").read_text()
    html = template.replace(
        "__MODEL_DATA__", json.dumps(_viewer(candidate, report), ensure_ascii=False, separators=(",", ":"))
    )
    if len(html.encode()) >= 1_000_000:
        raise AssertionError("Visualization exceeds one MB")
    args.output_directory.mkdir(parents=True)
    path = args.output_directory / "tool-axis-distance.html"
    path.write_text(html)
    report["fragment_sha256"] = _sha(path)
    report_path = args.output_directory / "observations.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if json.loads(report_path.read_text()) != report:
        raise AssertionError("Observation JSON changed on readback")
    for state, data in observed["states"].items():
        print(state, json.dumps(data["bands"], ensure_ascii=False))
    print("PGE_AXIS_OBSERVED input_unchanged=True objects_per_state=17 pads=4 analytic_checks=5")


if __name__ == "__main__":
    main()
