# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render lossless saved features in context and in isolation for visual lookup."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import pyrender
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parent
PRODUCT = ROOT.parent / "hvjb-inner-installed-access-v01-20260921"
DOCUMENT = ROOT.parent / "hvjb-line-progress-20260923"
HELPER = Path("/home/rlrk/src/ur15-line-render/render_ur15_line.py")
WIDTH, HEIGHT = 960, 660
GRAY = (0.73, 0.77, 0.79, 1.0)
SELECTED = (0.06, 0.43, 0.71, 1.0)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def geometry_digest(product: dict) -> str:
    digest = hashlib.sha256()
    for feature_id, row in product.items():
        digest.update(feature_id.encode())
        for mesh in row["meshes"]:
            for key in ("vertices", "faces"):
                array = np.ascontiguousarray(mesh[key])
                digest.update(str((array.shape, array.dtype)).encode())
                digest.update(array.tobytes())
    return digest.hexdigest()


def add_mesh(world, data, color, name):
    surface = trimesh.Trimesh(vertices=data["vertices"], faces=data["faces"], process=False)
    material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=color, roughnessFactor=0.75, metallicFactor=0.05, doubleSided=True
    )
    mesh = pyrender.Mesh.from_trimesh(surface, material=material, smooth=False)
    return world.add(mesh, name=name)


def new_world(look, pose, span):
    world = pyrender.Scene(bg_color=(1.0, 1.0, 1.0, 1.0), ambient_light=(0.5, 0.5, 0.5))
    world.add(pyrender.OrthographicCamera(xmag=span * WIDTH / HEIGHT, ymag=span, znear=0.00001, zfar=10.0), pose=pose)
    for intensity, point in ((2.3, [0.6, -0.6, 1.2]), (1.2, [-0.5, 0.3, 1.0])):
        light = pyrender.DirectionalLight(color=np.ones(3), intensity=intensity)
        world.add(light, pose=look.look_at(np.asarray(point), np.array([0, 0, 0.035])))
    return world


def isolated_world(look, feature_id, row):
    vertices = np.concatenate([mesh["vertices"] for mesh in row["meshes"]])
    minimum, maximum = vertices.min(0), vertices.max(0)
    center = (minimum + maximum) / 2
    distance = max(float((maximum - minimum).max()) * 4, 0.06)
    direction = np.array([0.38, -0.52, 0.80])
    direction /= np.linalg.norm(direction)
    pose = look.look_at(center + direction * distance, center)
    projected = (vertices - center) @ pose[:3, :3]
    extent = np.max(np.abs(projected[:, :2]), axis=0)
    span = max(extent[1], extent[0] * HEIGHT / WIDTH, 0.0001) * 1.17
    world = new_world(look, pose, float(span))
    for mesh in row["meshes"]:
        add_mesh(world, mesh, mesh["color"], feature_id)
    return world, pose, float(span)


def render_feature(renderer, full_world, node_map, product, look, feature_id, target):
    for key, nodes in node_map.items():
        for node in nodes:
            for primitive in node.mesh.primitives:
                primitive.material.baseColorFactor = SELECTED if key == feature_id else GRAY
    context_rgb, depth = renderer.render(full_world)
    assert np.isfinite(depth).all() and np.count_nonzero(depth) > 1000
    context_path = target / f"{feature_id}_context.png"
    Image.fromarray(context_rgb).save(context_path)
    segmentation_map = {
        node: np.array([255, 0, 0] if key == feature_id else [0, 0, 0], dtype=np.uint8)
        for key, nodes in node_map.items()
        for node in nodes
    }
    segmentation, segment_depth = renderer.render(
        full_world, flags=pyrender.RenderFlags.SEG, seg_node_map=segmentation_map
    )
    selected_mask = (
        (segmentation[:, :, 0] > 0) & (segmentation[:, :, 1] == 0) & (segmentation[:, :, 2] == 0) & (segment_depth > 0)
    )
    visible_pixels = int(np.count_nonzero(selected_mask))
    world, pose, span = isolated_world(look, feature_id, product[feature_id])
    isolated_rgb, isolated_depth = renderer.render(world)
    assert np.isfinite(isolated_depth).all() and np.count_nonzero(isolated_depth) > 50
    isolated_path = target / f"{feature_id}_isolated.png"
    Image.fromarray(isolated_rgb).save(isolated_path)
    return {
        "id": feature_id,
        "context": {"file": context_path.name, "sha256": sha(context_path), "features": 92, "meshes": 465},
        "isolated": {
            "file": isolated_path.name,
            "sha256": sha(isolated_path),
            "meshes": len(product[feature_id]["meshes"]),
            "camera_matrix": pose.tolist(),
            "orthographic_half_height_model_m": span,
            "visible_pixels": int(np.count_nonzero(isolated_depth)),
        },
        "context_selected_visible_pixels": visible_pixels,
        "context_occlusion_observation": "no selected-color pixels in this view" if visible_pixels == 0 else "visible",
        "source_basis": product[feature_id].get("basis"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=Path, default=ROOT / "output")
    parser.add_argument("--feature_ids", nargs="+")
    args = parser.parse_args()
    assert not args.output_dir.exists(), args.output_dir
    loader = module(PRODUCT / "prepare_inputs.py", "atlas_product_loader")
    product, manifest = loader.load_product()
    assert len(product) == 92 and sum(len(row["meshes"]) for row in product.values()) == 465
    data = json.loads((DOCUMENT / "data/line_review_data.json").read_text())
    records = {row["id"]: row for row in data["feature_review_candidates"]}
    assert set(product) == set(records)
    selected = args.feature_ids or list(product)
    assert len(selected) == len(set(selected)) and set(selected) <= set(product)
    before = geometry_digest(product)
    look = module(HELPER, "atlas_render_helpers")
    camera_record = json.loads((DOCUMENT / "audit/product_final_views.json").read_text())
    pose = np.array(camera_record["camera_matrix"])
    world = new_world(look, pose, 0.190)
    node_map = {key: [add_mesh(world, mesh, GRAY, key) for mesh in row["meshes"]] for key, row in product.items()}
    args.output_dir.mkdir(parents=True)
    figures = args.output_dir / "figures"
    figures.mkdir()
    renderer = pyrender.OffscreenRenderer(WIDTH, HEIGHT)
    result = []
    try:
        for index, feature_id in enumerate(selected):
            row = render_feature(renderer, world, node_map, product, look, feature_id, figures)
            row["existing_review_record"] = records[feature_id]
            result.append(row)
            print(f"FEATURE_ATLAS {index + 1}/{len(selected)} {feature_id}", flush=True)
    finally:
        renderer.delete()
    assert geometry_digest(product) == before
    payload = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "features": result,
        "feature_count": len(result),
        "images": len(result) * 2,
        "complete_92_feature_atlas": set(selected) == set(product),
        "source_model_geometry_unchanged": True,
        "geometry_arrays_sha256_before_and_after": before,
        "whole_product_mesh_count": 465,
        "context_camera_matrix": pose.tolist(),
        "context_orthographic_half_height_model_m": 0.190,
        "isolation_is_a_view_filter_not_a_disassembly_sequence": True,
        "physical_operation_selection": None,
        "formal_physical_validity_verdict": None,
        "source_identity": {
            "product_parent_sha256": manifest["parent_sha256"],
            "manifest_sha256": sha(PRODUCT / "data/product_manifest.json"),
            "loader_sha256": sha(PRODUCT / "prepare_inputs.py"),
            "review_data_sha256": sha(DOCUMENT / "data/line_review_data.json"),
            "helper_sha256": sha(HELPER),
            "script_sha256": sha(Path(__file__)),
        },
    }
    (args.output_dir / "atlas.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"FEATURE_ATLAS_COMPLETE features={len(result)} images={len(result) * 2} geometry_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
