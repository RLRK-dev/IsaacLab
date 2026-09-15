# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe saved display-mesh overlaps; no physical/contact acceptance [m]."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "audit/hvjb_photo_entry_display_v03.json"


def tree(row):
    vertices, faces = [], []
    for mesh in row["meshes"]:
        offset = len(vertices)
        vertices.extend(mesh["vertices"])
        faces.extend([index + offset for index in face] for face in mesh["faces"])
    # Same existing BVH API and epsilon as save_hand_body_setback_v01.py.
    return BVHTree.FromPolygons(vertices, faces, all_triangles=True, epsilon=0.0)


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    catalog = json.loads((ROOT / "data/hvjb_photo_correspondence_v03_p01.json").read_text())
    pairs = [
        (row["id"], end["feature_id"])
        for row in catalog["visible_wire_segments"]
        for end in row["observed_trace_ends"]
        if end.get("bind_display_geometry") and end["feature_id"].startswith("T")
    ]
    records = []
    for revision in ("p01", "p02"):
        source = ROOT / f"data/hvjb_photo_model_v03_{revision}.json.gz"
        before = digest(source)
        geometry = json.loads(gzip.decompress(source.read_bytes()))
        overlaps = [
            {
                "wire": wire,
                "sleeve": sleeve,
                "overlapping_triangle_pairs": len(tree(geometry[wire]).overlap(tree(geometry[sleeve]))),
            }
            for wire, sleeve in pairs
        ]
        assert digest(source) == before
        records.append({"revision": revision, "geometry_sha256": before, "pairs": overlaps})
    report = {
        "scope": "saved display wire versus estimated sleeve surfaces; excludes all other geometry and containment",
        "epsilon_m": 0.0,
        "reused_api": "save_hand_body_setback_v01.py: BVHTree.FromPolygons and overlap",
        "revisions": records,
        "formal_physical_verdict": None,
        "real_grasp_or_fastening_evaluated": False,
        "source_geometry_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("DISPLAY_ENTRY_SURFACES", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
