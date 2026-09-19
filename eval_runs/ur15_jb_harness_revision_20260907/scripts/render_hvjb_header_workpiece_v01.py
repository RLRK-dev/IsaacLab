# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render the saved header/workpiece observations [m] as isolated static reference views."""

from __future__ import annotations

import argparse
import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyrender
import trimesh
from PIL import Image
from render_hvjb_fastening_cad_v01 import ROOT, _look_at, _sha

OBSERVATION = "audit/hvjb_header_workpiece_v01.json"
COLORS = {
    "hardware": [69, 76, 84, 255],
    "insert": [64, 132, 169, 255],
    "contact_pad": [36, 151, 200, 255],
    "case": [191, 200, 206, 255],
    "header": [233, 135, 53, 255],
    "neighbor": [154, 161, 169, 255],
    "screw": [123, 132, 141, 255],
    "marked": [216, 49, 72, 255],
}


def _read(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def _geometry(path: str) -> dict:
    return json.loads(gzip.decompress((ROOT / path).read_bytes()))


def _mesh(row: dict, category: str, marked: list[int] | None = None) -> trimesh.Trimesh:
    result = trimesh.Trimesh(vertices=row["vertices"], faces=row["faces"], process=False)
    colors = np.tile(COLORS[category], (len(result.faces), 1))
    if marked:
        colors[marked] = COLORS["marked"]
    result.visual.face_colors = colors
    return result


def _parts(feature: str, report: dict, product: dict, source: dict, prior: dict) -> tuple:
    observation = next(row for row in report["poses"] if row["held_header"] == feature)
    pose = next(
        axis["pose"]
        for model in prior["models"]
        if model["feature_id"] == feature
        for axis in model["axes"]
        if axis["pose"]["frame"] == observation["saved_frame"]
    )
    translation = next(row["translation_m"] for row in report["header_mapping"] if row["feature_id"] == feature)
    parts, hand_points, pad_points = [], [], []
    for name, row in source["hand"]["objects"].items():
        matrix = np.asarray(pose["hand_object_world_matrices"][name])
        points = np.asarray(row["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3]
        points = points - pose["header_world_position_m"] + translation
        marked = sorted(
            {
                pair[0]
                for item in observation["pairs"]
                if item["hand_object"] == name
                for pair in item["triangle_pairs_hand_target"]
            }
        )
        parts.append((_mesh({"vertices": points, "faces": row["faces"]}, row["category"], marked), "hand"))
        hand_points.append(points)
        if marked:
            pad_points.append(points)
    bounds = np.concatenate(hand_points)
    assert (
        np.max(abs(np.array([bounds.min(axis=0), bounds.max(axis=0)]) - observation["hand_bounds_product_m"]))
        < report["settings"]["numeric_pose_tolerance_m"]
    )
    assert sum(len(part.faces) for part, kind in parts if kind == "hand") == observation["hand_triangles"]
    for identifier in ("P01", "P16", "P17"):
        for row in product[identifier]["meshes"]:
            official = "official_CAD" in row["name"]
            if identifier == "P01":
                category, kind = "case", "context"
            elif not official:
                category, kind = "screw", "context"
            else:
                category, kind = ("header", "held_header") if identifier == feature else ("neighbor", "context")
            parts.append((_mesh(row, category), kind))
    assert pad_points
    marked_bounds = np.concatenate(pad_points)
    return parts, marked_bounds.mean(axis=0), observation


def _render(parts: list, focus: np.ndarray, view: str, directory: Path, feature: str) -> dict:
    width, height = (1100, 900) if view == "whole" else (1000, 700)
    scene = pyrender.Scene(bg_color=[0.955, 0.971, 0.980, 1], ambient_light=[0.48, 0.48, 0.48])
    included = [(part, kind) for part, kind in parts if view == "whole" or kind != "context"]
    for part, _kind in included:
        scene.add(pyrender.Mesh.from_trimesh(part, smooth=False))
    if view == "whole":
        focus = np.array([0, -0.035, 0.115])
        offset, xmag = np.array([0.55, -1, 0.5]), 0.240
    else:
        offset, xmag = np.array([-1, -0.85, 0.55]), 0.025
    camera = pyrender.OrthographicCamera(xmag=xmag, ymag=xmag * height / width, znear=0.01, zfar=5)
    scene.add(camera, pose=_look_at(focus + offset, focus))
    for light_offset, intensity in (([0.3, -1.1, 1.3], 3.0), ([-0.7, -0.6, 0.4], 1.3)):
        scene.add(
            pyrender.DirectionalLight(color=np.ones(3), intensity=intensity), pose=_look_at(focus + light_offset, focus)
        )
    renderer = pyrender.OffscreenRenderer(width, height)
    path = directory / f"{feature.lower()}_{view}.png"
    try:
        color, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        assert np.isfinite(depth).all() and np.count_nonzero(depth) > 0
        Image.fromarray(color).save(path)
    finally:
        renderer.delete()
    print("HEADER_WORKPIECE_FRAME", feature, view, path, flush=True)
    return {
        "file": str(path.relative_to(ROOT)),
        "sha256": _sha(path),
        "view": view,
        "pixels": [width, height],
        "horizontal_span_m": 2 * xmag,
        "focus_m": focus.tolist(),
        "camera_offset_m": offset.tolist(),
        "objects_displayed": len(included),
        "triangles_displayed": sum(len(part.faces) for part, _kind in included),
        "foreground_pixels": int(np.count_nonzero(depth)),
        "omissions": [] if view == "whole" else ["case", "neighbor header", "display fasteners"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.output_directory.resolve()
    report = _read(OBSERVATION)
    pins = report["input_sha256_current"] | {OBSERVATION: _sha(ROOT / OBSERVATION)}
    pins["scripts/render_hvjb_fastening_cad_v01.py"] = _sha(ROOT / "scripts/render_hvjb_fastening_cad_v01.py")
    assert all(_sha(ROOT / name) == sha for name, sha in pins.items())
    directory.mkdir(parents=True, exist_ok=False)
    settings = report["settings"]
    product, source, prior = (
        _geometry(settings["product_meshes"]),
        _geometry(settings["hand_meshes"]),
        _read(settings["hand_observation"]),
    )
    frames = []
    for feature in ("P16", "P17"):
        parts, focus, observation = _parts(feature, report, product, source, prior)
        for view in ("whole", "pad"):
            frames.append(
                {
                    "feature_id": feature,
                    "saved_frame": observation["saved_frame"],
                    **_render(parts, focus, view, directory, feature),
                }
            )
    after = {name: _sha(ROOT / name) for name in pins}
    assert after == pins
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "frames": frames,
        "input_sha256_current": after,
        "renderer_script_sha256": _sha(Path(__file__)),
        "scope": (
            "Two representative saved poses; diagnostic colors mark returned hand triangles, not penetration depth"
        ),
        "continuous_motion_rendered": False,
        "source_geometry_modified": False,
        "native_opened": False,
        "native_saved": False,
        "video_generated": False,
        "physical_acceptance_verdict": None,
    }
    output = directory / "render_audit.json"
    with output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(output.read_text()) == result
    print("HEADER_WORKPIECE_STATIC_VIEWS_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
