# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare saved hand and official terminal-wrist surfaces without designing motion."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import trimesh
from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from prepare_hand_working_default_v01 import load_working_default
from probe_hand_tool_access_v01 import _analytic_checks, _slab_nearest, _world_hand
from scipy.spatial import ConvexHull

STEM = "hvjb_local_access_v01"
INPUT = f"data/{STEM}_inputs.json"
REFERENCE = ROOT / "references/hvjb_local_access_20260917"
MODEL = "data/hvjb_photo_model_v03_p03.json.gz"
CATALOG = "data/hvjb_photo_correspondence_v03_p01.json"
STATE_LABELS = {"near": "保持", "early": "開放初期", "open": "開放", "clear": "25 mm上方の保存姿勢"}


def _bounds(vertices):
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    return {"min_m": low.tolist(), "max_m": high.tolist(), "size_m": (high - low).tolist()}


def _outline(vertices, columns):
    """Project an object's convex envelope for display, never for distance tests."""
    points = np.unique(vertices[:, columns], axis=0)
    return points[ConvexHull(points).vertices].tolist()


def _wrist_mesh(arm):
    source = REFERENCE / "ur_description"
    yaml = (source / f"config/{arm}/visual_parameters.yaml").read_text()
    # Only read the six scalar fields in this pinned file; do not add a YAML dependency.
    block = yaml.split("  wrist_3:", 1)[1].split("    mesh_offset:", 1)[1]
    offset = {}
    for key in ("x", "y", "z", "roll", "pitch", "yaw"):
        value = re.search(rf"(?m)^      {key}: (.+)$", block).group(1)
        offset[key] = np.deg2rad(float(value[9:])) if value.startswith("!degrees ") else float(value)
    rotation = trimesh.transformations.euler_matrix
    visual = rotation(*(offset[key] for key in ("roll", "pitch", "yaw")))
    visual[:3, 3] = [offset[key] for key in ("x", "y", "z")]
    macro = (source / "urdf/ur_macro.xacro").read_text()
    assert 'xyz="0 0 0" rpy="0 ${-pi/2.0} ${-pi/2.0}"' in macro
    assert 'xyz="0 0 0" rpy="${pi/2.0} 0 ${pi/2.0}"' in macro
    link_to_tool = rotation(0, -np.pi / 2, -np.pi / 2) @ rotation(np.pi / 2, 0, np.pi / 2)
    scene = trimesh.load(source / f"meshes/{arm}/visual/wrist3.dae", force="scene", process=False)
    mesh = scene.to_geometry()  # Includes every COLLADA node transform and its unit scale.
    mesh.apply_transform(np.linalg.inv(link_to_tool) @ visual)
    return {
        "arm": arm,
        "scope": "wrist_3 visual mesh only; no wrist_1/2, adapter, cable or robot pose",
        "frame": "official tool0; XY perpendicular to tool axis, Z axial",
        "mesh_offset_m_rad": offset,
        "visual_to_tool0": (np.linalg.inv(link_to_tool) @ visual).tolist(),
        "scene_node_transforms": scene.graph.to_flattened(),
        "vertices": len(mesh.vertices),
        "triangles": len(mesh.faces),
        "bounds": _bounds(mesh.vertices),
        "front_xy_m": _outline(mesh.vertices, [0, 1]),
        "side_xz_m": _outline(mesh.vertices, [0, 2]),
    }


def _hand_states(payload):
    candidate = payload["candidates"]["T050"]
    seat = payload["config"]["target"]["seat_z_m"]
    result = {}
    for state in candidate["states"]:
        triangles, names, _ = _world_hand(candidate, state, [0, 0])
        surfaces = []
        for name, obj in candidate["objects"].items():
            if obj["category"] == "guide":
                continue
            matrix = np.asarray(candidate["states"][state]["transforms"][name])
            world = np.asarray(obj["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3]
            surfaces.append(
                {
                    "name": name,
                    "category": obj["category"],
                    "color": obj["color"],
                    "bounds": _bounds(world),
                    "xy_m": _outline(world, [0, 1]),
                    "yz_m": _outline(world, [1, 2]),
                }
            )
        bands = []
        for relative in ([0.0038, 0.0538], [0.0538, 0.3678]):
            measured = _slab_nearest(triangles, names, np.asarray(relative) + seat)
            bands.append({"z_above_reference_seat_m": relative, **measured})
        result[state] = {
            "label_ja": STATE_LABELS[state],
            "bounds": _bounds(triangles.reshape(-1, 3)),
            "surfaces": surfaces,
            "tool_axis_to_hand": bands,
        }
    return result


def _product_observations(model, catalog):
    meshes = [(key, mesh) for key, part in model.items() for mesh in part["meshes"] if key != "P02"]
    rows = []
    for number in range(9, 14):
        joint = f"J{number:02d}"
        target = np.concatenate([mesh["vertices"] for mesh in model[joint]["meshes"]])
        axis = (target.min(axis=0) + target.max(axis=0)) / 2
        top = target[:, 2].max()
        surfaces, names = [], []
        for key, mesh in meshes:
            if key == joint:
                continue
            triangles = np.asarray(mesh["vertices"])[np.asarray(mesh["faces"])].copy()
            triangles[:, :, :2] -= axis[:2]
            surfaces.append(triangles)
            names.extend([key + "/" + mesh["name"]] * len(triangles))
        surfaces = np.concatenate(surfaces)
        bands = []
        for relative in ([0.0, 0.01], [0.01, 0.03], [0.03, 0.06]):
            measured = _slab_nearest(surfaces, names, np.asarray(relative) + top)
            bands.append({"z_above_display_head_top_m": relative, **measured})
        feature = next(row for row in catalog["visible_fastener_features"] if row["id"] == joint)
        rows.append(
            {
                "id": joint,
                "center_px": feature["center_px"],
                "axis_xy_m": axis[:2].tolist(),
                "display_head_top_m": float(top),
                "excluded_features": [joint, "P02"],
                "bands": bands,
            }
        )
    return rows


def prepare():
    settings = read_json(INPUT)
    before = {path: digest(ROOT / path) for path in settings["pinned"]}
    assert before == settings["pinned"], "Pinned input changed"
    for row in settings["ur_sources"]["files"]:
        raw = (ROOT / row["path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        assert blob == row["git_blob_sha1"]
    payload, hand_record = load_working_default(source_directory=REFERENCE / "hand_source")
    catalog = read_json(CATALOG)
    model = json.loads(gzip.decompress((ROOT / MODEL).read_bytes()))
    work = read_json("data/hvjb_task_occupancy_v01.json")
    selection = read_json("data/hvjb_robot_selection_v01.json")
    counts = [len(model), len(catalog["required_functions"]), len(catalog["electrical_groups"])]
    counts += [len(catalog["lv_pin_map"]), len(work["cards"])]
    assert counts == [92, 17, 13, 12, 20]
    assert selection["selected_plan"] == "S5_AB" and selection["selected_assembly_arm_count"] == 5
    result = {
        "revision": STEM,
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "scope": "read-only saved mesh observations and independent component size comparison",
        "wrists": {arm: _wrist_mesh(arm) for arm in ("ur15", "ur3e")},
        "hand": _hand_states(payload),
        "hand_source": hand_record,
        "hand_target": payload["config"]["target"],
        "product_row": _product_observations(model, catalog),
        "product_estimated_sleeve_diameter_m": 0.0056,
        "product_basis": "Photo-derived display geometry, not manufacturing dimensions or assembly state",
        "distance_definition": "horizontal axis-to-surface distance after exact triangle clipping to each Z band",
        "product_exclusions": "Only the target fastener and P02 lid; wires are not classified fixed or held",
        "display_definition": "Per-object projected convex outlines; exact triangles are used only for measurements",
        "analytic_geometry_checks": _analytic_checks(),
        "preserved_counts": counts,
        "all_task_ids": [row["id"] for row in work["cards"]],
        "selected_plan_preserved": "S5_AB",
        "sources": settings["sources"],
        "ur_sources": settings["ur_sources"],
        "arm_model_selected": None,
        "hand_pose_in_product_selected": None,
        "grasp_stability_measured": False,
        "complete_tool_envelope_present": False,
        "continuous_motion_created": False,
        "acceptance_thresholds": None,
        "physical_acceptance_verdict": None,
    }
    for name, row in result["wrists"].items():
        print(name, "wrist_3 tool0 XYZ spans [mm]", np.asarray(row["bounds"]["size_m"]) * 1000)
    for name, row in result["hand"].items():
        print(name, "hand XYZ spans [mm]", np.asarray(row["bounds"]["size_m"]) * 1000)
    for relative in (INPUT, f"scripts/build_{STEM}.py", f"scripts/{STEM}.html", f"analysis/{STEM}.md"):
        before[relative] = digest(ROOT / relative)
    return result, before


def package(directory, report):
    directory.mkdir(parents=True, exist_ok=False)
    photo = report["sources"]["photo"]
    frame = report["sources"]["video_frame"]
    paths = {
        photo["file"]: "product.jpg",
        frame["file"]: "assembly_242s.png",
        f"analysis/{STEM}.md": "notes.md",
        "data/hvjb_robot_selection_v01.json": "selection.json",
        "data/hvjb_task_occupancy_v01.json": "all_workcards.json",
        "references/hvjb_local_access_20260917/ur_description/LICENSE": "UR_Description_LICENSE.txt",
        "references/hvjb_local_access_20260917/ur_description/meshes/ur15/LICENSE.txt": "UR15_mesh_LICENSE.txt",
    }
    copied = {}
    for source, target in paths.items():
        shutil.copy2(ROOT / source, directory / target)
        copied[target] = digest(directory / target)
        assert copied[target] == digest(ROOT / source)
    template = (ROOT / f"scripts/{STEM}.html").read_text()
    assert template.count("__PAYLOAD__") == 1
    page = template.replace("__PAYLOAD__", json.dumps(report, ensure_ascii=False).replace("<", "\\u003c"))
    (directory / "review.html").write_text(page)
    write_new_json(directory / "measurements.json", report)
    assert read_json(directory / "measurements.json") == report
    return {"copied_sha256": copied, "page_sha256": digest(directory / "review.html")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    outputs = [ROOT / f"data/{STEM}.json", ROOT / f"audit/{STEM}.json", args.output_directory]
    for output in outputs:
        if output.exists():
            raise FileExistsError(output)
    report, before = prepare()
    delivery = package(args.output_directory, report)
    after = {path: digest(ROOT / path) for path in before}
    assert before == after, "Source changed during read-only observation"
    audit = {
        "observed_at": report["observed_at"],
        "output_directory": str(args.output_directory),
        "input_sha256": before,
        "input_files_unchanged": before == after,
        "source_hand_geometry_rebuilt": False,
        "preserved_counts": report["preserved_counts"],
        "geometry_checks": report["analytic_geometry_checks"],
        "serialized_measurement_readback_identical": True,
        "physical_acceptance_verdict": None,
        **delivery,
    }
    write_new_json(outputs[0], report)
    write_new_json(outputs[1], audit)
    write_new_json(args.output_directory / "audit.json", audit)
    print("LOCAL_ACCESS_REVIEW_READY", args.output_directory)


if __name__ == "__main__":
    main()
