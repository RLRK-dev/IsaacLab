# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render equal-scale reference assemblies and the saved PGE hand [m]."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyrender
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ROTATIONS = {
    "SES1601": [[0, 1, 0], [1, 0, 0], [0, 0, -1]],
    "SEM2001": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
    "SEV2001": [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],
    "PGE": [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
}
VIEWS = {
    "whole": {"pixels": [1200, 500], "x_m": [-0.035, 1.205], "target_z_m": -0.070},
    "front": {"pixels": [960, 800], "x_m": [-0.035, 0.525], "target_z_m": -0.070},
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _look_at(eye: np.ndarray, target: np.ndarray) -> np.ndarray:
    # Reuse the existing offline renderer's look_at calculation, without its line/motion configuration.
    camera_z = eye - target
    camera_z /= np.linalg.norm(camera_z)
    camera_x = np.cross([0.0, 0.0, 1.0], camera_z)
    camera_x /= np.linalg.norm(camera_x)
    camera_y = np.cross(camera_z, camera_x)
    result = np.eye(4)
    result[:3, :3] = np.column_stack((camera_x, camera_y, camera_z))
    result[:3, 3] = eye
    return result


def _presentation_transform(parts: list[trimesh.Trimesh], name: str, z_center: float = 0) -> np.ndarray:
    angle = np.deg2rad(12.0)
    tilt = np.array([[1, 0, 0], [0, np.cos(angle), -np.sin(angle)], [0, np.sin(angle), np.cos(angle)]])
    rotation = tilt @ np.asarray(ROTATIONS[name])
    assert np.allclose(rotation.T @ rotation, np.eye(3)) and np.linalg.det(rotation) > 0
    vertices = np.concatenate([part.vertices @ rotation.T for part in parts])
    lower, upper = vertices.min(axis=0), vertices.max(axis=0)
    result = np.eye(4)
    result[:3, :3] = rotation
    result[:3, 3] = [-lower[0], -(lower[1] + upper[1]) / 2, z_center - (lower[2] + upper[2]) / 2]
    return result


def _tool_parts(path: Path) -> list[trimesh.Trimesh]:
    scene = trimesh.load(path, force="scene", process=False)
    result = []
    for node in sorted(scene.graph.nodes_geometry):
        matrix, key = scene.graph.get(node)
        mesh = scene.geometry[key].copy()
        assert isinstance(mesh, trimesh.Trimesh)
        mesh.apply_transform(matrix)
        result.append(mesh)
    return result


def _hand_parts() -> list[trimesh.Trimesh]:
    raw = json.loads(gzip.decompress((ROOT / "data/hvjb_pge_finger_v01_meshes.json.gz").read_bytes()))
    candidate = raw["candidates"]["PGE_SAMPLE"]
    result = []
    for name, row in candidate["objects"].items():
        mesh = trimesh.Trimesh(vertices=row["vertices"], faces=row["faces"], process=False)
        mesh.apply_transform(np.asarray(candidate["states"]["contour"]["transforms"][name]))
        category = row["category"]
        if category == "pad":
            color = [32, 127, 183, 255]
        elif category == "insert":
            color = [126, 166, 186, 255]
        elif name == "comparison_wire":
            color = [227, 122, 38, 255]
        elif name == "illustrative_sleeve":
            color = [46, 51, 57, 255]
        else:
            color = [130, 140, 150, 255]
        mesh.visual.vertex_colors = color
        result.append(mesh)
    assert len(result) == 21
    return result


def _add_parts(scene: pyrender.Scene, parts: list[trimesh.Trimesh], matrix: np.ndarray) -> np.ndarray:
    bounds = []
    for part in parts:
        scene.add(pyrender.Mesh.from_trimesh(part, smooth=True), pose=matrix)
        vertices = part.vertices @ matrix[:3, :3].T + matrix[:3, 3]
        bounds.append([vertices.min(axis=0), vertices.max(axis=0)])
    values = np.asarray(bounds)
    return np.array([values[:, 0].min(axis=0), values[:, 1].max(axis=0)])


def _render_views(scene: pyrender.Scene, directory: Path, name: str, bounds: np.ndarray) -> list[dict]:
    rows = []
    for view, settings in VIEWS.items():
        width, height = settings["pixels"]
        xmin, xmax = settings["x_m"]
        xmag = (xmax - xmin) / 2
        ymag = xmag * height / width
        target = np.array([(xmin + xmax) / 2, 0, settings["target_z_m"]])
        camera = pyrender.OrthographicCamera(xmag=xmag, ymag=ymag, znear=0.01, zfar=5.0)
        nodes = [scene.add(camera, pose=_look_at(target + [0, -2, 0], target))]
        for offset, intensity in (([0.4, -1.2, 1.5], 3.4), ([-0.6, -1.0, 0.4], 1.6)):
            light = pyrender.DirectionalLight(color=np.ones(3), intensity=intensity)
            nodes.append(scene.add(light, pose=_look_at(target + offset, target)))
        if view == "whole":
            assert bounds[0, 0] >= xmin and bounds[1, 0] <= xmax
            assert bounds[0, 2] >= target[2] - ymag and bounds[1, 2] <= target[2] + ymag
        renderer = pyrender.OffscreenRenderer(width, height)
        try:
            color, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
            assert np.isfinite(depth).all() and np.count_nonzero(depth) > 0
            path = directory / f"{name.lower()}_{view}.png"
            Image.fromarray(color).save(path)
        finally:
            renderer.delete()
            for node in nodes:
                scene.remove_node(node)
        rows.append(
            {
                "file": path.name,
                "sha256": _sha(path),
                "view": view,
                **settings,
                "vertical_span_m": 2 * ymag,
                "foreground_pixels": int(np.count_nonzero(depth)),
            }
        )
        print("REFERENCE_FRAME", name, view, flush=True)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversion", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.conversion.read_text())
    for name, expected in report["input_sha256_after"].items():
        assert _sha(ROOT / name) == expected
    args.output_directory.mkdir(parents=True, exist_ok=False)
    hands = _hand_parts()
    hand_matrix = _presentation_transform(hands, "PGE", -0.220)
    results = []
    for row in report["sources"]:
        path = ROOT / row["glb_file"]
        assert _sha(path) == row["glb_sha256"]
        parts = _tool_parts(path)
        assert sum(len(part.faces) for part in parts) == row["triangles"]
        matrix = _presentation_transform(parts, row["model"])
        scene = pyrender.Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.40, 0.40, 0.40])
        tool_bounds = _add_parts(scene, parts, matrix)
        hand_bounds = _add_parts(scene, hands, hand_matrix)
        bounds = np.array([np.minimum(tool_bounds[0], hand_bounds[0]), np.maximum(tool_bounds[1], hand_bounds[1])])
        frames = _render_views(scene, args.output_directory, row["model"], bounds)
        assert _sha(path) == row["glb_sha256"]
        results.append(
            {
                "model": row["model"],
                "source_glb_sha256": row["glb_sha256"],
                "display_matrix": matrix.tolist(),
                "tool_display_bounds_m": tool_bounds.tolist(),
                "hand_display_matrix": hand_matrix.tolist(),
                "hand_display_bounds_m": hand_bounds.tolist(),
                "surface_nodes": len(parts),
                "triangles": row["triangles"],
                "frames": frames,
            }
        )
    after = {name: _sha(ROOT / name) for name in report["input_sha256_after"]}
    assert after == report["input_sha256_after"]
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "frames": results,
        "input_sha256_after": after,
        "hand_objects": len(hands),
        "simplification": False,
        "presentation": "Rigid left-bound alignment and equal scale only; not installation or engagement poses",
        "physical_acceptance_verdict": None,
    }
    path = args.output_directory / "render_audit.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(path.read_text()) == result
    print("FASTENING_CAD_REFERENCE_FRAMES_COMPLETE", path, flush=True)


if __name__ == "__main__":
    main()
