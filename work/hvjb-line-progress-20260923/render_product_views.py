# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render the saved complete product with explanatory task highlights."""

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
HELPER = Path("/home/rlrk/src/ur15-line-render/render_ur15_line.py")
WIDTH, HEIGHT = 1600, 1100
COLORS = {
    "A": (0.16, 0.43, 0.70, 1.0),
    "B": (0.62, 0.28, 0.56, 1.0),
    "C": (0.10, 0.53, 0.45, 1.0),
    "UNKNOWN": (0.88, 0.53, 0.13, 1.0),
    "GRAY": (0.71, 0.75, 0.77, 1.0),
}
VIEWS = [
    ("product", None, None),
    ("outside_A", ["P02", "P03", "P04"], "A"),
    ("outside_B", ["P05", "P06", "P07", "P19", "P20", "P21"], "B"),
    ("after_insertion_bus", ["P09", "P10", "P11", "P12", "P13"], "C"),
    ("external_headers", ["P16", "P17"], "C"),
    ("internal_housings", ["I01", "I02", "I03", "I04", "I05"], "C"),
    ("case", ["P01"], "C"),
    ("main_fuse_unassigned", ["P08", "P22"], "UNKNOWN"),
    ("main_and_lv_unassigned", ["P14", "P15", "P18"], "UNKNOWN"),
    ("wires_display_only", "WIRES", "UNKNOWN"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def material(color):
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=color,
        roughnessFactor=0.75,
        metallicFactor=0.05,
        doubleSided=True,
    )


def scene(product, selected, accent, pose):
    world = pyrender.Scene(bg_color=(1.0, 1.0, 1.0, 1.0), ambient_light=(0.5, 0.5, 0.5))
    keys = {key for key in product if key.startswith("W")} if selected == "WIRES" else set(selected or [])
    for key, row in product.items():
        for mesh in row["meshes"]:
            color = mesh["color"] if selected is None else COLORS[accent] if key in keys else COLORS["GRAY"]
            surface = trimesh.Trimesh(vertices=mesh["vertices"], faces=mesh["faces"], process=False)
            world.add(pyrender.Mesh.from_trimesh(surface, material=material(color), smooth=False), name=key)
    camera = pyrender.OrthographicCamera(xmag=0.190 * WIDTH / HEIGHT, ymag=0.190, znear=0.001, zfar=5.0)
    world.add(camera, pose=pose)
    for intensity, point in ((2.3, [0.6, -0.6, 1.2]), (1.2, [-0.5, 0.3, 1.0])):
        light_pose = LOOK.look_at(np.asarray(point), np.array([0, 0, 0.035]))
        world.add(pyrender.DirectionalLight(color=np.ones(3), intensity=intensity), pose=light_pose)
    return world, sorted(keys)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_name", default="product_final")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    out = ROOT / "figures" / args.output_name
    assert not out.exists(), out
    loader = module(PRODUCT / "prepare_inputs.py", "preserved_product_loader")
    product, manifest = loader.load_product()
    assert len(product) == 92
    global LOOK
    LOOK = module(HELPER, "preserved_line_render_helpers")
    vertices = np.concatenate([mesh["vertices"] for row in product.values() for mesh in row["meshes"]])
    center = (vertices.min(0) + vertices.max(0)) / 2
    pose = LOOK.look_at(center + np.array([0.38, -0.52, 0.80]), center)
    renderer = pyrender.OffscreenRenderer(WIDTH, HEIGHT)
    out.mkdir(parents=True)
    rows = []
    try:
        for name, selected, accent in VIEWS:
            world, highlighted = scene(product, selected, accent, pose)
            rgb, depth = renderer.render(world, flags=pyrender.RenderFlags.RGBA)
            path = out / (name + ".png")
            Image.fromarray(rgb).save(path)
            rows.append(
                {
                    "name": name,
                    "file": str(path.relative_to(ROOT)),
                    "sha256": sha(path),
                    "highlighted_features": highlighted,
                    "included_feature_count": len(product),
                    "included_mesh_count": sum(len(row["meshes"]) for row in product.values()),
                    "visible_pixels": int(np.count_nonzero(depth)),
                }
            )
            print("PRODUCT_VIEW_COMPLETE", name, flush=True)
    finally:
        renderer.delete()
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "views": rows,
        "manifest_sha256": sha(PRODUCT / "data/product_manifest.json"),
        "parent_product_sha256": manifest["parent_sha256"],
        "loader_sha256": sha(PRODUCT / "prepare_inputs.py"),
        "render_helper_sha256": sha(HELPER),
        "script_sha256": sha(Path(__file__)),
        "camera_matrix": pose.tolist(),
        "product_bounds_m": [vertices.min(0).tolist(), vertices.max(0).tolist()],
        "geometry_modified": False,
        "mesh_subset_removed": False,
        "highlight_basis": "Existing group candidates, not a new part-by-part operation selection.",
        "scope": "Completed-product display configuration; not intermediate assembly geometry or a complete BOM.",
        "physical_validity_verdict": None,
    }
    (ROOT / "audit" / (args.output_name + "_views.json")).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
