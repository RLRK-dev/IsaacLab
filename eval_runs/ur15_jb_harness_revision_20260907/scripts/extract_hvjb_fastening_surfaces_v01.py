# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read manufacturer analytical planes/cylinders and compare unchanged tessellation [m]."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import trimesh
from prepare_hvjb_fastening_cad_v01 import _digest, _read_step

ROOT = Path(__file__).resolve().parents[1]


def _signature(scene: trimesh.Scene) -> dict:
    chunks = []
    for node in scene.graph.nodes_geometry:
        matrix, key = scene.graph.get(node)
        mesh = scene.geometry[key]
        assert isinstance(mesh, trimesh.Trimesh)
        assert np.array_equal(matrix, np.eye(4)), "This reader expects the observed identity CAD placements"
        chunks.append(np.asarray(mesh.triangles, dtype="<f4"))
    triangles = np.concatenate(chunks)
    assert np.isfinite(triangles).all()
    triangles[triangles == 0] = 0  # Normalize signed zero, without rounding coordinates.
    corners = triangles.view(np.dtype([(axis, "<f4") for axis in "xyz"])).reshape(-1, 3)
    corners.sort(axis=1, order=list("xyz"), kind="stable")
    fields = [f"v{index}" for index in range(9)]
    rows = corners.view("<f4").reshape(-1, 9).view(np.dtype([(field, "<f4") for field in fields])).reshape(-1)
    rows.sort(order=fields, kind="stable")
    return {"triangles": len(rows), "unoriented_triangle_position_sha256": hashlib.sha256(rows.tobytes()).hexdigest()}


def _surface_rows(scene: trimesh.Scene) -> tuple[list[dict], list[dict]]:
    rows = []
    coverage = []
    for node in sorted(scene.graph.nodes_geometry):
        matrix, key = scene.graph.get(node)
        assert np.array_equal(matrix, np.eye(4))
        mesh = scene.geometry[key]
        mapped = "brep_index" in mesh.face_attributes
        coverage.append({"node": node, "triangles": len(mesh.faces), "has_face_mapping": mapped})
        if not mapped:
            continue
        primitives = mesh.metadata["cascadio"]["brep_primitives"]
        indices = np.asarray(mesh.face_attributes["brep_index"], dtype=np.int64)
        assert len(indices) == len(mesh.faces)
        ordered = np.argsort(indices, kind="stable")
        unique, starts, counts = np.unique(indices[ordered], return_index=True, return_counts=True)
        for index, start, count in zip(unique, starts, counts, strict=True):
            primitive = primitives[int(index)]
            if primitive is None:
                continue
            kind = type(primitive).__name__.lower()
            assert kind in {"plane", "cylinder"}
            values = asdict(primitive)
            triangles = ordered[start : start + count]
            vertices = mesh.vertices[np.unique(mesh.faces[triangles])]
            relative = vertices - values["origin"]
            if kind == "plane":
                residual = np.abs(relative @ np.asarray(values["normal"]))
            else:
                axis = np.asarray(values["axis"])
                axial = relative @ axis
                radial = relative - axial[:, None] * axis
                residual = np.abs(np.linalg.norm(radial, axis=1) - values["radius"])
            rows.append(
                {
                    "node": node,
                    "type": kind,
                    "primitive": values,
                    "triangles": int(count),
                    "tessellated_area_m2": float(mesh.area_faces[triangles].sum()),
                    "bounds_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
                    "maximum_vertex_surface_residual_m": float(residual.max()),
                }
            )
    assert rows
    return rows, coverage


def _convert(source: dict, output: Path, cascadio, reuse: Path | None) -> tuple[dict, list[dict]]:
    model = source["model"]
    raw, _ = _read_step(model.lower())
    assert hashlib.sha256(raw).hexdigest() == source["step_sha256"]
    if reuse is None:
        glb = cascadio.to_glb_bytes(
            raw,
            tol_linear=0.02,
            tol_angular=0.2,
            include_materials=True,
            include_brep=True,
            brep_types={"plane", "cylinder"},
        )
        path = output / f"{model.lower()}_surfaces.glb"
        with path.open("xb") as stream:
            stream.write(glb)
    else:
        path = reuse.resolve()
        path.relative_to(ROOT)
    analytical_sha = _digest(path)
    print("ANALYTICAL_CAD_SAVED", model, flush=True)
    scene = trimesh.load(path, force="scene", process=False)
    original_path = ROOT / source["glb_file"]
    assert _digest(original_path) == source["glb_sha256"]
    original = trimesh.load(original_path, force="scene", process=False)
    current_signature, original_signature = _signature(scene), _signature(original)
    unchanged = current_signature == original_signature
    assert unchanged, "Analytical export changed the full set of triangle positions"
    rows, coverage = _surface_rows(scene)
    counts = dict(Counter(row["type"] for row in rows))
    result = {
        "model": model,
        "original_glb_file": source["glb_file"],
        "original_glb_sha256": source["glb_sha256"],
        "analytical_glb_file": str(path.relative_to(ROOT)),
        "analytical_glb_sha256": analytical_sha,
        "reused_saved_analytical_export": reuse is not None,
        "triangle_positions_equal": unchanged,
        "current_triangle_signature": current_signature,
        "original_triangle_signature": original_signature,
        "surface_nodes": len(scene.graph.nodes_geometry),
        "triangles": sum(len(mesh.faces) for mesh in scene.geometry.values()),
        "analytical_surface_counts": counts,
        "face_mapping_coverage": coverage,
        "triangles_with_face_mapping": sum(row["triangles"] for row in coverage if row["has_face_mapping"]),
        "triangles_without_face_mapping": sum(row["triangles"] for row in coverage if not row["has_face_mapping"]),
        "maximum_vertex_surface_residual_m": max(row["maximum_vertex_surface_residual_m"] for row in rows),
    }
    print("ANALYTICAL_SURFACES", json.dumps(result), flush=True)
    assert _digest(original_path) == source["glb_sha256"]
    assert _digest(path) == analytical_sha
    return result, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converter_path", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    parser.add_argument("--reuse_ses_glb", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.converter_path))
    import cascadio

    baseline = ROOT / "data/hvjb_fastening_cad_v01.json"
    baseline_sha = _digest(baseline)
    previous = json.loads(baseline.read_text())
    pins = previous["conversion"]["input_sha256_after"]
    for name, expected in pins.items():
        assert _digest(ROOT / name) == expected, name
    output = args.output_directory.resolve()
    output.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    reports, surfaces = [], {}
    for source in previous["conversion"]["sources"]:
        reuse = args.reuse_ses_glb if source["model"] == "SES1601" else None
        report, rows = _convert(source, output, cascadio, reuse)
        reports.append(report)
        surfaces[source["model"]] = rows
    destination = output / "surfaces.json.gz"
    destination.write_bytes(gzip.compress(json.dumps(surfaces, separators=(",", ":")).encode(), mtime=0))
    assert json.loads(gzip.decompress(destination.read_bytes())) == json.loads(json.dumps(surfaces))
    after = {name: _digest(ROOT / name) for name in pins}
    assert after == pins and _digest(baseline) == baseline_sha
    record = {
        "observed_at": datetime.now(UTC).isoformat(),
        "baseline_sha256": baseline_sha,
        "converter_version": cascadio.__version__,
        "delta": "Read only supplied face mappings; explicitly count unmapped triangles; retain full geometry",
        "mapping_scope": "Partial analytical mapping, not complete CAD surface coverage",
        "triangle_comparison": (
            "All unordered triangle positions at original GLB float32 precision; no rounding; winding excluded"
        ),
        "surface_records_file": str(destination.relative_to(ROOT)),
        "surface_records_sha256": _digest(destination),
        "models": reports,
        "input_sha256_before": pins,
        "input_sha256_after": after,
        "physical_acceptance_verdict": None,
    }
    path = output / "surface_extraction.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(path.read_text()) == record
    print("FASTENING_SURFACE_EXTRACTION_COMPLETE", path, flush=True)


if __name__ == "__main__":
    main()
