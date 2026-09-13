# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare local upper-edge reliefs on the retained D40 fingertip plate [m]."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

import build_hand_fingertip_concepts_v01 as base
import build_hand_mount_interface_v02 as mount_builder
import numpy as np
import trimesh


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _edit_plate(original, frame, relief, settings):
    result = copy.deepcopy(original)
    points = np.asarray(original["vertices"])
    local = (points - frame[:3, 3]) @ frame[:3, :3]
    corner = np.flatnonzero(
        np.abs(local[:, 1] - settings["source_upper_edge_v_m"]) < settings["source_feature_identity_tolerance_m"]
    )
    assert len(corner) == 4, "Source upper edge no longer has the expected four corners"
    assert np.ptp(local[corner, 0]) < 0.01400001 and np.ptp(local[corner, 2]) < 0.00400001
    untouched = np.ones(len(points), dtype=bool)
    untouched[corner] = False
    assert local[untouched, 1].min() > local[corner, 1].max() + relief
    edited = points.copy()
    # Only the four upper corners move. No remeshing or reserialization of other vertices.
    for index in corner:
        edited[index] += frame[:3, 1] * relief
        result["vertices"][int(index)] = edited[index].tolist()
    assert result["faces"] == original["faces"] and result["color"] == original["color"]
    assert np.array_equal(edited[untouched], points[untouched])
    before_mesh = trimesh.Trimesh(points, original["faces"], process=False)
    after_mesh = trimesh.Trimesh(edited, result["faces"], process=False)
    old_degenerate = np.flatnonzero(before_mesh.area_faces == 0).tolist()
    new_degenerate = np.flatnonzero(after_mesh.area_faces == 0).tolist()
    assert new_degenerate == old_degenerate, "Relief changed the source degenerate-face set"
    new_local = (edited - frame[:3, 3]) @ frame[:3, :3]
    top_faces = np.flatnonzero(np.isin(original["faces"], corner).all(axis=1)).tolist()
    touched_faces = np.flatnonzero(np.isin(original["faces"], corner).any(axis=1)).tolist()
    assert len(top_faces) == 2, "Unrecognized upper-face topology"
    displacement = edited[corner] - points[corner]
    return result, {
        "relief_m": relief,
        "edited_corner_indices": corner.tolist() if relief else [],
        "upper_corner_indices": corner.tolist(),
        "upper_face_indices": top_faces,
        "adjacent_face_indices": touched_faces,
        "corner_displacements_local_m": displacement.tolist(),
        "unmodified_vertex_count": int(untouched.sum()) if relief else len(points),
        "unchanged_vertices_identical": True,
        "faces_and_color_identical": True,
        "source_upper_v_range_m": [float(local[corner, 1].min()), float(local[corner, 1].max())],
        "new_upper_v_range_m": [float(new_local[corner, 1].min()), float(new_local[corner, 1].max())],
        "upper_edge_to_nearest_remaining_vertex_v_m": float(local[untouched, 1].min() - new_local[corner, 1].max()),
        "nearest_remaining_vertex_indices": np.flatnonzero(
            np.abs(local[:, 1] - local[untouched, 1].min()) < settings["source_feature_identity_tolerance_m"]
        ).tolist(),
        "plate_height_m": float(local[:, 1].max() - new_local[corner, 1].min()),
        "removed_nominal_contact_face_area_m2": 0.014 * relief,
        "removed_nominal_volume_m3": 0.014 * 0.004 * relief,
        "observed_mesh_volume_difference_m3": float(before_mesh.volume - after_mesh.volume),
        "watertight_edges": bool(after_mesh.is_watertight),
        "winding_consistent": bool(after_mesh.is_winding_consistent),
        "zero_area_faces_retained": new_degenerate,
    }


def _service_definitions(candidate, mount):
    definitions = {}
    for side in ("left_left", "left_right"):
        matrix = np.asarray(candidate["states"]["open"]["transforms"][f"{side}_carrier"])
        direction = matrix[:3, :3] @ np.asarray(mount["face_normal_local"])
        definitions[side] = {
            "moving_objects": [
                name
                for name, obj in candidate["objects"].items()
                if obj["category"] == "insert" and name.startswith(side)
            ],
            "direction_world": direction.tolist(),
        }
        assert len(definitions[side]["moving_objects"]) == 4
    return definitions


def _build(payload, settings, mount):
    original = payload["candidates"][settings["source_candidate"]]
    frame = np.asarray(mount["mount_frame_local"])
    output, observations = copy.deepcopy(payload), {}
    output["candidates"] = {}
    for name, relief in settings["reliefs_m"].items():
        candidate, changes = copy.deepcopy(original), {}
        for side in ("left_left", "left_right"):
            key = f"{side}_carrier"
            candidate["objects"][key], changes[side] = _edit_plate(original["objects"][key], frame, relief, settings)
        unchanged = [key for key in original["objects"] if not key.endswith("_carrier")]
        assert all(original["objects"][key] == candidate["objects"][key] for key in unchanged)
        assert candidate["states"] == original["states"]
        if not relief:
            assert candidate == original, "Baseline changed"
        output["candidates"][name] = candidate
        observations[name] = {
            "relief_m": relief,
            "carriers": changes,
            "unchanged_objects": unchanged,
            "saved_states_identical": True,
            "original_hardware_and_contact_meshes_identical": True,
        }
    output["mount_relief_settings"] = settings
    return output, observations


def main() -> None:
    """Write fresh comparison payloads and exact preservation observations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path(__file__).resolve().parents[1] / "data/hand_mount_relief_v01.json"
    )
    args = parser.parse_args()
    settings = json.loads(args.config.read_text())
    data = args.config.parent
    mount_path = data / "hand_mount_interface_v02.json"
    assert _sha(args.source) == settings["source_mesh_sha256"], "D40 source changed"
    assert _sha(mount_path) == settings["mount_settings_sha256"], "Mount source measurement settings changed"
    payload = json.loads(args.source.read_text())
    original = payload["candidates"][settings["source_candidate"]]
    mount = mount_builder._mount_interface(
        original["objects"]["hardware_left_right_inner_finger_0"], json.loads(mount_path.read_text())
    )
    output, changes = _build(payload, settings, mount)
    args.directory.mkdir(parents=True, exist_ok=False)
    mesh_path = args.directory / "hand_mount_relief_meshes_v01.json"
    _write(mesh_path, output)
    glb = {}
    for name, candidate in output["candidates"].items():
        glb[name] = base._export_glb(candidate, args.directory / f"hand_mount_relief_{name}_v01.glb")
    service_settings = json.loads((data / settings["service_source"]).read_text())
    report = {
        "recorded_at": datetime.now().astimezone().isoformat(),
        "source_sha256": _sha(args.source),
        "mesh_payload_sha256": _sha(mesh_path),
        "settings": settings,
        "mount": mount,
        "candidates": changes,
        "glb_readback": glb,
        "service_definitions": _service_definitions(original, mount),
        "service_settings": service_settings["service"],
        "scope": "Four original static poses; only four blue carrier corners per side modified",
        "contact_compliance_changed": False,
        "fasteners_and_index_pin_modelled": False,
        "physical_acceptance_verdict": None,
        "video_created": False,
        "arm_motion_created": False,
    }
    _write(args.directory / "hand_mount_relief_observations_v01.json", report)
    template = Path(__file__).with_name("hand_mount_relief_viewer_v01.html").read_text()
    page = template.replace("__MESH_PAYLOAD__", json.dumps(output, separators=(",", ":")))
    page = page.replace("__OBSERVATION_PAYLOAD__", json.dumps(report, separators=(",", ":")))
    (args.directory / "取付上端の逃げ比較_v01.html").write_text(page)
    assert _sha(args.source) == settings["source_mesh_sha256"]
    print(json.dumps(changes, ensure_ascii=False, indent=2), flush=True)
    print("HAND_MOUNT_RELIEF_BUILD_DONE", flush=True)


if __name__ == "__main__":
    main()
