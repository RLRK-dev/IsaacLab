# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Convert public inner-header STEP geometry for an isolated product review."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references/hvjb_photo_inventory_20260915"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converter_path", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.converter_path))
    import cascadio

    output = ROOT / "data/hvjb_photo_cad_v01.json.gz"
    report_path = ROOT / "audit/hvjb_photo_cad_v01.json"
    if output.exists() or report_path.exists():
        raise FileExistsError("Preserve existing conversions; use a new revision")
    meshes, sources = {}, []
    for suffix, key in ((1, "A"), (4, "D"), (5, "E"), (6, "F")):
        part = f"2103245-{suffix}"
        archive = REF / f"te_2103245_{suffix}_step.zip"
        with zipfile.ZipFile(archive) as stream:
            names = stream.namelist()
            assert len(names) == 1 and Path(names[0]).name == names[0]
            content = stream.read(names[0])
        step = REF / names[0]
        step.write_bytes(content)
        glb = REF / f"te_2103245_{suffix}.glb"
        glb.write_bytes(cascadio.to_glb_bytes(content, tol_linear=0.02, tol_angular=0.2, include_materials=True))
        scene = trimesh.load(glb, force="scene", process=False)
        pieces, ignored = [], []
        for node in scene.graph.nodes_geometry:
            matrix, name = scene.graph.get(node)
            item = scene.geometry[name]
            if not isinstance(item, trimesh.Trimesh):
                ignored.append({"node": node, "type": type(item).__name__})
                continue
            mesh = item.copy()
            mesh.apply_transform(matrix)
            pieces.append(mesh)
        mesh = trimesh.util.concatenate(pieces)
        meshes[part] = {"vertices": mesh.vertices.tolist(), "faces": mesh.faces.tolist(), "key": key}
        row = {
            "part_number": part,
            "key": key,
            "product_url": f"https://www.te.com/en/product-{part}.html",
            "step_file": str(step.relative_to(ROOT)),
            "step_sha256": digest(step),
            "archive_sha256": digest(archive),
            "glb_sha256": digest(glb),
            "bounds_m": mesh.bounds.tolist(),
            "triangles": len(mesh.faces),
            "ignored_non_surface_annotations": ignored,
        }
        sources.append(row)
        print("INNER_HEADER", part, mesh.bounds.tolist(), len(mesh.faces), flush=True)
    output.write_bytes(gzip.compress(json.dumps(meshes, separators=(",", ":")).encode(), mtime=0))
    report = {
        "converter": "cascadio",
        "version": cascadio.__version__,
        "linear_deflection_mm": 0.02,
        "angular_deflection_rad": 0.2,
        "output": str(output.relative_to(ROOT)),
        "output_sha256": digest(output),
        "source_drawings": {"te_2103245_drawing.pdf": digest(REF / "te_2103245_drawing.pdf")},
        "sources": sources,
        "note": (
            "Unscaled SI surfaces. Installed datum and contact/terminal selections require separate correspondence."
        ),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PHOTO_CAD_PREPARED", output, flush=True)


if __name__ == "__main__":
    main()
