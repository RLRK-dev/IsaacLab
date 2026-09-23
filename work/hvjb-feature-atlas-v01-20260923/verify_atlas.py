# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read every atlas image and check saved feature vertices against each view frame."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import render_atlas as atlas
from PIL import Image

ROOT = Path(__file__).resolve().parent


def main() -> None:
    target = ROOT / "qa_receipt.json"
    assert not target.exists()
    path = ROOT / "output/atlas.json"
    data = json.loads(path.read_text())
    assert data["complete_92_feature_atlas"] and data["feature_count"] == 92 and data["images"] == 184
    assert data["source_identity"]["script_sha256"] == atlas.sha(ROOT / "render_atlas.py")
    loader = atlas.module(atlas.PRODUCT / "prepare_inputs.py", "atlas_readback_loader")
    product, _ = loader.load_product()
    assert atlas.geometry_digest(product) == data["geometry_arrays_sha256_before_and_after"]
    assert {row["id"] for row in data["features"]} == set(product)
    checks = []
    for row in data["features"]:
        for kind in ("context", "isolated"):
            image_path = ROOT / "output/figures" / row[kind]["file"]
            assert atlas.sha(image_path) == row[kind]["sha256"]
            with Image.open(image_path) as image:
                assert image.size == (960, 660)
                image.verify()
        vertices = np.concatenate([mesh["vertices"] for mesh in product[row["id"]]["meshes"]])
        pose = np.array(row["isolated"]["camera_matrix"])
        projected = (vertices - pose[:3, 3]) @ pose[:3, :3]
        half_y = row["isolated"]["orthographic_half_height_model_m"]
        half_x = half_y * 960 / 660
        assert np.max(np.abs(projected[:, 0])) < half_x
        assert np.max(np.abs(projected[:, 1])) < half_y
        assert np.all(projected[:, 2] < -0.00001) and np.all(projected[:, 2] > -10)
        checks.append({"id": row["id"], "all_isolated_vertices_inside_frame": True})
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "atlas_sha256": atlas.sha(path),
        "images_read_back": 184,
        "distinct_feature_ids": 92,
        "source_geometry_arrays_sha256": atlas.geometry_digest(product),
        "isolated_framing": checks,
        "context_features_without_selected_pixels": [
            row["id"] for row in data["features"] if row["context_selected_visible_pixels"] == 0
        ],
        "scope": "Image identity and display framing only. The fixed view can occlude features.",
        "physical_operation_selection": None,
        "formal_physical_validity_verdict": None,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("ATLAS_READBACK_COMPLETE images=184 features=92 isolated_views_framed=92", flush=True)


if __name__ == "__main__":
    main()
