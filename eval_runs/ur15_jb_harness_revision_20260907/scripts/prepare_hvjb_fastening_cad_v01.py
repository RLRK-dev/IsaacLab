# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read manufacturer example STEP assemblies without changing their geometry [m]."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "references/hvjb_fastening_cad_20260917"
ARCHIVES = {
    "ses1601": "eeb96824a5cde6c4e950469782402ff7e53be57cfaf56905d9029dd2afb0da9a",
    "sem2001": "29caf5365ad405e43e0c9bb0564bbf0eacbf1e0f707fc55f0ddd169d6c40bfc1",
    "sev2001": "496e379adc1b40d9d397212bac643878d0946abaa8597e5cd65a6838a5dfe85a",
}


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read_step(stem: str) -> tuple[bytes, dict]:
    archive_path = REFERENCE / f"{stem}_step.zip"
    assert _digest(archive_path) == ARCHIVES[stem], archive_path
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries if entry.filename.lower().endswith(".stp")]
        assert len(names) == 1
        raw = archive.read(names[0])
        metadata = {
            "archive": str(archive_path.relative_to(ROOT)),
            "archive_sha256": ARCHIVES[stem],
            "archive_entries": [{"name": entry.filename, "bytes": entry.file_size} for entry in entries],
            "step_entry": names[0],
            "step_sha256": hashlib.sha256(raw).hexdigest(),
            "step_header": raw.partition(b"DATA;")[0].decode("latin1"),
            "declared_length_units": sorted(set(re.findall(rb"SI_UNIT\([^;]*METRE[^;]*", raw))),
        }
    metadata["declared_length_units"] = [value.decode("ascii") for value in metadata["declared_length_units"]]
    assert raw.startswith(b"ISO-10303-21;")
    return raw, metadata


def _scene_records(scene: trimesh.Scene) -> tuple[list[dict], list[dict]]:
    records, ignored = [], []
    for node in sorted(scene.graph.nodes_geometry):
        matrix, name = scene.graph.get(node)
        source = scene.geometry[name]
        if not isinstance(source, trimesh.Trimesh):
            ignored.append({"node": node, "geometry": name, "type": type(source).__name__})
            continue
        mesh = source.copy()
        mesh.apply_transform(matrix)
        assert np.isfinite(mesh.vertices).all()
        assert len(mesh.vertices) and len(mesh.faces)
        assert mesh.faces.min() >= 0 and mesh.faces.max() < len(mesh.vertices)
        visual = source.visual
        color_source = visual.material if visual.kind == "texture" else visual
        color = np.asarray(color_source.main_color, dtype=np.uint8).tolist()
        records.append(
            {
                "node": node,
                "geometry": name,
                "source_matrix": np.asarray(matrix).tolist(),
                "vertices": len(mesh.vertices),
                "triangles": len(mesh.faces),
                "visual_kind": visual.kind,
                "color_rgba": color,
                "bounds_m": mesh.bounds.tolist(),
                "zero_area_triangles": int(np.count_nonzero(mesh.area_faces == 0)),
            }
        )
    assert records
    return records, ignored


def _convert(stem: str, output: Path, converter, reuse_ses: Path | None) -> tuple[dict, dict]:
    raw, metadata = _read_step(stem)
    glb_path = output / f"{stem}.glb"
    if stem == "ses1601" and reuse_ses is not None:
        assert _digest(reuse_ses) == "9c4089004527c8872adbf1bf65c400e74554c979101d29c22aedf49cd81ecaaf"
        glb = reuse_ses.read_bytes()
        metadata["reused_glb_from_first_attempt"] = str(reuse_ses.relative_to(ROOT))
    else:
        glb = converter.to_glb_bytes(raw, tol_linear=0.02, tol_angular=0.2, include_materials=True)
    assert glb.startswith(b"glTF")
    glb_path.write_bytes(glb)
    scene = trimesh.load(glb_path, force="scene", process=False)
    records, ignored = _scene_records(scene)
    bounds = np.asarray([record["bounds_m"] for record in records])
    full_bounds = np.asarray([bounds[:, 0].min(axis=0), bounds[:, 1].max(axis=0)])
    metadata.update(
        {
            "model": stem.upper(),
            "glb_file": str(glb_path.relative_to(ROOT)),
            "glb_sha256": _digest(glb_path),
            "bounds_m": full_bounds.tolist(),
            "extents_m": (full_bounds[1] - full_bounds[0]).tolist(),
            "surface_nodes": len(records),
            "triangles": sum(record["triangles"] for record in records),
            "zero_area_triangles": sum(record["zero_area_triangles"] for record in records),
            "ignored_non_surface_nodes": ignored,
            "geometry_scale_after_conversion": 1.0,
            "source_pose_changed": False,
            "mechanism_opening_reconstructed": False,
            "selected_for_ampere": False,
        }
    )
    assert _digest(REFERENCE / f"{stem}_step.zip") == ARCHIVES[stem]
    print(stem.upper(), json.dumps({key: metadata[key] for key in ("surface_nodes", "triangles", "bounds_m")}))
    return {"objects": records}, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converter_path", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    parser.add_argument("--reuse_ses_glb", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.converter_path))
    import cascadio

    output = args.output_directory.resolve()
    output.relative_to(ROOT)
    record = json.loads((ROOT / "data/hvjb_tool_wire_sources_v01.json").read_text())
    pins = record["input_sha256_after"]
    for name, expected in pins.items():
        assert _digest(ROOT / name) == expected, name
    output.mkdir(parents=True, exist_ok=False)
    meshes, sources = {}, []
    for stem in ARCHIVES:
        cache = args.reuse_ses_glb.resolve() if args.reuse_ses_glb else None
        meshes[stem], metadata = _convert(stem, output, cascadio, cache)
        sources.append(metadata)
    mesh_path = output / "manufacturer_object_records.json.gz"
    mesh_path.write_bytes(gzip.compress(json.dumps(meshes, separators=(",", ":")).encode(), mtime=0))
    assert json.loads(gzip.decompress(mesh_path.read_bytes())) == meshes
    for name, expected in pins.items():
        assert _digest(ROOT / name) == expected, name
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "converter": "cascadio",
        "version": cascadio.__version__,
        "reused_workflow": "prepare_hvjb_photo_cad_v01.py: cascadio, saved node transforms, SI GLB",
        "linear_deflection_mm": 0.02,
        "angular_deflection_rad": 0.2,
        "object_records_file": str(mesh_path.relative_to(ROOT)),
        "object_records_sha256": _digest(mesh_path),
        "sources": sources,
        "input_sha256_before": pins,
        "input_sha256_after": {name: _digest(ROOT / name) for name in pins},
        "selected_role_plan": record["selected_role_plan"],
        "workcard_ids": record["workcard_ids"],
        "physical_acceptance_verdict": None,
        "note": "Manufacturer example assemblies in their saved poses; no custom motion, repair or fit verdict.",
    }
    report_path = output / "conversion.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(report_path.read_text()) == report
    print("MANUFACTURER_CAD_CONVERSION_COMPLETE", report_path, flush=True)


if __name__ == "__main__":
    main()
