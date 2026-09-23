# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Show each preserved product group with and without its surroundings."""

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
from PIL import Image

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
ATLAS = WORK / "hvjb-feature-atlas-v01-20260923/render_atlas.py"
PRODUCT = WORK / "hvjb-inner-installed-access-v01-20260921"
LOOK_PATH = Path("/home/rlrk/src/ur15-line-render/render_ur15_line.py")
DIRECTIONS = {"oblique": [0.38, -0.52, 0.80], "front": [0.02, -1.0, 0.40]}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def framed_pose(look, vertices, direction):
    center = (vertices.min(0) + vertices.max(0)) / 2
    unit = np.asarray(direction, dtype=float)
    unit /= np.linalg.norm(unit)
    pose = look.look_at(center + unit * 1.2, center)
    projected = (vertices - center) @ pose[:3, :3]
    extents = np.max(np.abs(projected[:, :2]), axis=0)
    span = max(extents[1], extents[0] * 660 / 960, 0.001) * 1.17
    return pose, float(span)


def render_one(atlas, look, renderer, product, group, direction, isolated, target):
    keys = set(group["feature_ids"])
    included = {key: row for key, row in product.items() if not isolated or key in keys}
    vertices = np.concatenate([mesh["vertices"] for row in included.values() for mesh in row["meshes"]])
    pose, span = framed_pose(look, vertices, DIRECTIONS[direction])
    world = atlas.new_world(look, pose, span)
    nodes = {}
    tint = tuple(int(group["display_color"][start : start + 2], 16) / 255 for start in (1, 3, 5)) + (1.0,)
    for key, row in included.items():
        for mesh in row["meshes"]:
            color = mesh["color"] if isolated else tint if key in keys else atlas.GRAY
            node = atlas.add_mesh(world, mesh, color, key)
            nodes[node] = key
    rgb, depth = renderer.render(world)
    assert np.isfinite(depth).all() and np.count_nonzero(depth) > 0
    kind = "isolated" if isolated else "context"
    path = target / f"{group['id']}_{direction}_{kind}.png"
    Image.fromarray(rgb).save(path)
    id_order = list(included)
    segmentation_map = {node: np.array([id_order.index(key) + 1, 0, 0], dtype=np.uint8) for node, key in nodes.items()}
    segmentation, seg_depth = renderer.render(world, flags=pyrender.RenderFlags.SEG, seg_node_map=segmentation_map)
    visible = {
        key: int(np.count_nonzero((segmentation[:, :, 0] == id_order.index(key) + 1) & (seg_depth > 0)))
        for key in group["feature_ids"]
    }
    return {
        "group_id": group["id"],
        "direction": direction,
        "kind": kind,
        "file": path.name,
        "sha256": sha(path),
        "feature_ids_included": list(included),
        "mesh_count": len(nodes),
        "selected_feature_visible_pixels": visible,
        "camera_matrix": pose.tolist(),
        "orthographic_half_height_model_m": span,
        "view_is_not_intermediate_assembly_state": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_name", default="render_v01")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    output = ROOT / args.output_name
    assert not output.exists(), output
    atlas = module(ATLAS, "preserved_feature_atlas")
    look = module(LOOK_PATH, "preserved_group_look")
    loader = module(PRODUCT / "prepare_inputs.py", "preserved_group_product")
    source = json.loads((ROOT / "data/group_review.json").read_text())
    product, manifest = loader.load_product()
    assert len(product) == 92 and sum(len(row["meshes"]) for row in product.values()) == 465
    before = atlas.geometry_digest(product)
    output.mkdir()
    figures = output / "figures"
    figures.mkdir()
    renderer = pyrender.OffscreenRenderer(960, 660)
    records = []
    try:
        for group in source["groups"]:
            for direction in DIRECTIONS:
                for isolated in (False, True):
                    records.append(render_one(atlas, look, renderer, product, group, direction, isolated, figures))
            print("GROUP_RENDER", group["id"], len(group["feature_ids"]), len(records), flush=True)
    finally:
        renderer.delete()
    assert atlas.geometry_digest(product) == before
    loader.load_product()
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "renders": records,
        "images": len(records),
        "product_geometry_digest_before_and_after": before,
        "source_geometry_unchanged": True,
        "product_parent_sha256": manifest["parent_sha256"],
        "source_identity": {
            str(path): sha(path)
            for path in (ATLAS, LOOK_PATH, PRODUCT / "prepare_inputs.py", ROOT / "data/group_review.json")
        },
        "script_sha256": sha(Path(__file__)),
        "formal_physical_validity_verdict": None,
    }
    (output / "render_receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("GROUP_RENDER_COMPLETE images=44 product_geometry_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
