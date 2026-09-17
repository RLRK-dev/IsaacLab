# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record the unchanged example CAD's mounting-plane triangles and boundaries [m]."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from build_hvjb_fastening_cad_reference_v01 import _write_json
from prepare_hvjb_fastening_cad_v01 import _digest
from render_hvjb_fastening_cad_v01 import _tool_parts

ROOT = Path(__file__).resolve().parents[1]
DATUM = "data/hvjb_fastening_datum_v01.json"
SUPPLEMENT = "references/hvjb_fastening_cad_20260917/additional_info_SES.pdf"
SUPPLEMENT_SHA = "0b529f27167cb96896ddf99210c76a0b75dcb26a102301876681755305214466"


def _empty_band(triangles: np.ndarray, transverse: int) -> dict:
    """Observe the empty interval across all selected triangles, not just their vertices [m]."""
    lower = triangles[:, :, transverse].min(axis=1)
    upper = triangles[:, :, transverse].max(axis=1)
    negative, positive = upper < 0, lower > 0
    crossing = ~(negative | positive)
    edges = None
    if negative.any() and positive.any() and not crossing.any():
        edges = [float(upper[negative].max()), float(lower[positive].min())]
    return {
        "negative_triangles": int(negative.sum()),
        "positive_triangles": int(positive.sum()),
        "triangles_touching_or_crossing_zero": int(crossing.sum()),
        "edges_m": edges,
        "width_m": None if edges is None else edges[1] - edges[0],
        "scope": "Empty transverse band in the selected planar triangles; not full-solid or tool clearance",
    }


def _observe(source: dict) -> dict:
    observation = source["observation"]
    normal = observation["plane_normal_index"]
    longitudinal = observation["query_hint"]["long_axis"]
    transverse = 3 - normal - longitudinal
    tolerance = observation["coordinate_match_tolerance_m"]
    plane = observation["plane_coordinate_m"]
    parts = _tool_parts(ROOT / source["source_glb_file"])
    assert len(parts) == source["surface_nodes"]
    assert sum(len(mesh.faces) for mesh in parts) == source["triangles"]
    selected, all_triangles = [], []
    for part_index, mesh in enumerate(parts):
        residual = np.max(np.abs(mesh.triangles[:, :, normal] - plane), axis=1)
        indices = np.flatnonzero(residual <= tolerance)
        if not len(indices):
            continue
        triangles = mesh.triangles[indices]
        outline = mesh.outline(face_ids=indices, process=False)
        boundaries = []
        for entity in outline.entities:
            assert type(entity).__name__ == "Line", type(entity).__name__
            vertices = outline.vertices[entity.points]
            boundaries.append(
                {
                    "entity_type": "Line",
                    "closed": bool(entity.points[0] == entity.points[-1]),
                    "vertices_m": vertices.tolist(),
                    "bounds_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
                    "function": None,
                }
            )
        selected.append(
            {
                "load_part_index": part_index,
                "triangle_indices": indices.tolist(),
                "triangles_m": triangles.tolist(),
                "area_m2": float(mesh.area_faces[indices].sum()),
                "maximum_plane_residual_m": float(residual[indices].max()),
                "boundaries": boundaries,
            }
        )
        all_triangles.append(triangles)
    combined = np.concatenate(all_triangles)
    points = combined.reshape(-1, 3)
    assert len(combined) == sum(row["triangles"] for row in observation["plane_candidates"])
    return {
        "source_glb_file": source["source_glb_file"],
        "source_glb_sha256": source["source_glb_sha256"],
        "source_surface_nodes": len(parts),
        "source_triangles": source["triangles"],
        "plane_coordinate_m": plane,
        "normal_index": normal,
        "longitudinal_index": longitudinal,
        "transverse_index": transverse,
        "coordinate_match_tolerance_m": tolerance,
        "tolerance_purpose": "Reuse the prior coordinate identity query; not a physical tolerance",
        "selected_triangles": len(combined),
        "selected_area_m2": sum(row["area_m2"] for row in selected),
        "bounds_m": [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
        "boundary_paths": sum(len(row["boundaries"]) for row in selected),
        "open_boundary_paths": sum(not b["closed"] for row in selected for b in row["boundaries"]),
        "empty_band": _empty_band(combined, transverse),
        "face_sets": selected,
        "mounting_bolt_pattern": None,
        "thread_sizes": None,
        "fastening_tcp": None,
        "bit_stroke_m": None,
    }


def _display(model: str, row: dict) -> dict:
    axes = [row["longitudinal_index"], row["transverse_index"]]
    bounds = np.asarray(row["bounds_m"])[:, axes] * 1000
    # View choice only: SEV's mounting patches do not span its longitudinal midpoint.
    center = 72.0 if model == "SEV2001" else float(bounds[:, 0].mean())
    return {
        "axis_labels": ["XYZ"[index] for index in axes],
        "bounds_mm": bounds.tolist(),
        "detail_bounds_mm": [center - 35, center + 35],
        "triangles_mm": [
            (np.asarray(triangle)[:, axes] * 1000).tolist()
            for faces in row["face_sets"]
            for triangle in faces["triangles_m"]
        ],
        "boundaries_mm": [
            (np.asarray(boundary["vertices_m"])[:, axes] * 1000).tolist()
            for faces in row["face_sets"]
            for boundary in faces["boundaries"]
        ],
        "gap_edges_mm": None
        if row["empty_band"]["edges_m"] is None
        else [value * 1000 for value in row["empty_band"]["edges_m"]],
        "gap_mm": None if row["empty_band"]["width_m"] is None else row["empty_band"]["width_m"] * 1000,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_html", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, default=ROOT / "data/hvjb_fastening_mount_faces_v01.json")
    args = parser.parse_args()
    assert not args.output_html.exists() and not args.output_json.exists(), "Output already exists"
    datum_path = ROOT / DATUM
    datum = json.loads(datum_path.read_text())
    pins = {
        **datum["input_sha256_after"],
        DATUM: _digest(datum_path),
        "data/hvjb_fastening_cad_v01.json": datum["baseline_sha256"],
        SUPPLEMENT: SUPPLEMENT_SHA,
        **{row["source_glb_file"]: row["source_glb_sha256"] for row in datum["models"].values()},
    }
    before = {name: _digest(ROOT / name) for name in pins}
    assert before == pins, "Input SHA mismatch"
    models = {}
    for model, source in datum["models"].items():
        models[model] = _observe(source)
        row = models[model]
        print(
            "MOUNT_FACE_OBSERVED",
            model,
            json.dumps({key: row[key] for key in ("selected_triangles", "boundary_paths", "empty_band")}),
            flush=True,
        )
    template = ROOT / "scripts/hvjb_fastening_mount_faces_v01.html"
    display = {model: _display(model, row) for model, row in models.items()}
    markup = template.read_text().replace("__MODEL_DATA__", json.dumps(display, separators=(",", ":")))
    assert "__MODEL_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    assert args.output_html.read_text() == markup
    after = {name: _digest(ROOT / name) for name in pins}
    assert after == before
    record = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Selected coplanar CAD triangles and raw boundaries; no mounting design or physical verdict",
        "method": "Original colored GLB, process=False, existing plane query, Trimesh.outline(face_ids, process=False)",
        "geometry_modified": False,
        "boundary_classification": "None: closed contours do not establish bolt holes, thread size or through-depth",
        "index_scope": "Part indices describe this load only; source GLB hash and saved coordinates identify geometry",
        "models": models,
        "display": display,
        "official_sources": {
            "ses_supplement": {
                "file": SUPPLEMENT,
                "sha256": SUPPLEMENT_SHA,
                "source_index_url": "https://www.stoeger.com/de/downloads.html",
                "archive": "references/hvjb_fastening_cad_20260917/ses1601_step.zip",
                "pages_read": [1, 2],
                "observations": [
                    "SES: support over the full mounting surface; minimum three screws and a key-plate",
                    "Key-groove tolerance designation F8 with +0.013 / +0.035 mm deviations",
                    "F8 is a tolerance designation; the 8 mm planar gap is a separate CAD observation",
                    "No selected screw size or hole pitch; no transfer of SES instructions to SEM or SEV",
                ],
            },
            "motion_definitions": {
                "headstroke": "https://www.stoeger.com/en/headstroke.html",
                "feed_stroke": "https://www.stoeger.com/en/feed-stroke.html",
                "bit_stroke": "https://www.stoeger.com/en/automatic-bit-stroke.html",
                "observed_on": "2026-09-17",
                "finding": "Head stroke equals feed stroke; bit stroke is separate and has no selected numeric value",
            },
        },
        "input_sha256_before": before,
        "input_sha256_after": after,
        "template_sha256": _digest(template),
        "inline_html": {"path": str(args.output_html.resolve()), "sha256": _digest(args.output_html)},
        "selected_tool_configuration": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(args.output_json, record)
    print("MOUNT_FACE_COMPLETE", args.output_json, args.output_html, flush=True)


if __name__ == "__main__":
    main()
