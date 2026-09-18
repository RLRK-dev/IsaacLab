# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read the additional SES2001 example STEP, retaining its full tessellation [m]."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import trimesh
from analyze_hvjb_header_tool_configuration_v01 import _glb_content
from build_hvjb_fastening_cad_reference_v01 import _write_json
from extract_hvjb_fastening_surfaces_v01 import _surface_rows
from prepare_hvjb_fastening_cad_v01 import _digest, _scene_records

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = "data/hvjb_ses2001_sources_v01.json"


def _inputs(settings: dict) -> dict:
    previous = json.loads((ROOT / settings["previous_readback"]).read_text())
    pins = previous["input_sha256_current"].copy()
    for name, value in previous["artifacts_sha256"].items():
        assert name not in pins or pins[name] == value, name
        pins[name] = value
    for source in settings["sources"]:
        pins[source["file"]] = source["sha256"]
    helpers = [name for name in settings["reuse"].values() if name.startswith("scripts/")]
    paths = [SETTINGS, settings["previous_readback"], *helpers]
    for name in paths:
        pins.setdefault(name, _digest(ROOT / name))
    actual = {name: _digest(ROOT / name) for name in pins}
    assert actual == pins, [name for name in pins if actual[name] != pins[name]]
    return pins


def _step(settings: dict) -> tuple[bytes, dict]:
    source = next(row for row in settings["sources"] if row["file"].endswith(".zip"))
    with zipfile.ZipFile(ROOT / source["file"]) as archive:
        entries = archive.infolist()
        names = [row.filename for row in entries if row.filename.lower().endswith((".stp", ".step"))]
        assert len(names) == 1
        raw = archive.read(names[0])
    assert raw.startswith(b"ISO-10303-21;")
    metadata = {
        "archive": source,
        "archive_entries": [{"name": row.filename, "bytes": row.file_size} for row in entries],
        "step_entry": names[0],
        "step_sha256": hashlib.sha256(raw).hexdigest(),
        "step_header": raw.partition(b"DATA;")[0].decode("latin1"),
        "declared_length_units": [
            row.decode("ascii") for row in sorted(set(re.findall(rb"SI_UNIT\([^;]*METRE[^;]*", raw)))
        ],
    }
    return raw, metadata


def _compressed(path: Path, value: dict | list) -> str:
    with path.open("xb") as stream:
        stream.write(gzip.compress(json.dumps(value, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
    assert json.loads(gzip.decompress(path.read_bytes())) == json.loads(json.dumps(value))
    return _digest(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converter_path", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists(), args.output_json
    settings = json.loads((ROOT / SETTINGS).read_text())
    before = _inputs(settings)
    output = args.output_directory.resolve()
    output.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    raw, source = _step(settings)
    sys.path.insert(0, str(args.converter_path))
    import cascadio

    print("SES2001_STEP_VERIFIED", source["step_entry"], source["step_sha256"], flush=True)
    glb = cascadio.to_glb_bytes(
        raw,
        tol_linear=0.02,
        tol_angular=0.2,
        include_materials=True,
        include_brep=True,
        brep_types={"plane", "cylinder"},
    )
    path = output / "ses2001.glb"
    with path.open("xb") as stream:
        stream.write(glb)
    print("SES2001_GLB_SAVED", _digest(path), flush=True)
    scene = trimesh.load(path, force="scene", process=False)
    objects, ignored = _scene_records(scene)
    assert not ignored, ignored
    rows, coverage = _surface_rows(scene)
    bounds = np.asarray([row["bounds_m"] for row in objects])
    whole_bounds = np.asarray([bounds[:, 0].min(axis=0), bounds[:, 1].max(axis=0)])
    records_path, surfaces_path = output / "objects.json.gz", output / "surfaces.json.gz"
    objects_sha = _compressed(records_path, {"SES2001": {"objects": objects}})
    surfaces_sha = _compressed(surfaces_path, {"SES2001": rows})
    after = {name: _digest(ROOT / name) for name in before}
    assert after == before
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "model": "SES2001",
        "scope": "Full saved example pose; analytical mappings are partial; no geometry repair or mechanism motion",
        "script_sha256": _digest(Path(__file__)),
        "source": source,
        "converter": {"name": "cascadio", "version": cascadio.__version__},
        "linear_deflection_mm": 0.02,
        "angular_deflection_rad": 0.2,
        "glb_file": str(path.relative_to(ROOT)),
        "glb_sha256": _digest(path),
        "glb_content": _glb_content(str(path.relative_to(ROOT))),
        "geometry_scale_after_conversion": 1.0,
        "bounds_m": whole_bounds.tolist(),
        "extents_m": (whole_bounds[1] - whole_bounds[0]).tolist(),
        "surface_nodes": len(objects),
        "triangles": sum(row["triangles"] for row in objects),
        "zero_area_triangles": sum(row["zero_area_triangles"] for row in objects),
        "ignored_non_surface_nodes": ignored,
        "object_records_file": str(records_path.relative_to(ROOT)),
        "object_records_sha256": objects_sha,
        "surface_records_file": str(surfaces_path.relative_to(ROOT)),
        "surface_records_sha256": surfaces_sha,
        "analytical_surface_counts": dict(Counter(row["type"] for row in rows)),
        "face_mapping_coverage": coverage,
        "triangles_with_face_mapping": sum(row["triangles"] for row in coverage if row["has_face_mapping"]),
        "triangles_without_face_mapping": sum(row["triangles"] for row in coverage if not row["has_face_mapping"]),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "native_opened": False,
        "native_saved": False,
        "motion_recomputed": False,
        "selected_tool_configuration": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(args.output_json, result)
    print("SES2001_CAD_READ_COMPLETE", json.dumps({key: result[key] for key in ("extents_m", "triangles")}))


if __name__ == "__main__":
    main()
