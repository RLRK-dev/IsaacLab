# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe source CAD axes/planes [m] and render the unchanged manufacturer assemblies."""

from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyrender
from build_hvjb_fastening_cad_reference_v01 import _sha, _write_json
from PIL import Image
from prepare_hvjb_fastening_cad_v01 import _digest
from render_hvjb_fastening_cad_v01 import _add_parts, _look_at, _tool_parts

ROOT = Path(__file__).resolve().parents[1]
# Coordinate hints identify drawing-corresponding surfaces; they are not clearance limits.
HINTS = {
    "SES1601": {"long_axis": 1, "mount_axis": 2, "axis_point_m": [0, 0, -0.042]},
    "SEM2001": {"long_axis": 0, "mount_axis": 2, "axis_point_m": [0, 0, 0.058]},
    "SEV2001": {"long_axis": 2, "mount_axis": 1, "axis_point_m": [0, 0.080, 0]},
}
ROTATIONS = {
    "SES1601": [[0, 1, 0], [1, 0, 0], [0, 0, -1]],
    "SEM2001": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "SEV2001": [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],
}
VIEWS = {
    "whole": {"pixels": [1200, 400], "x_m": [-0.045, 1.195]},
    "front": {"pixels": [960, 520], "x_m": [-0.040, 0.720]},
}


def _observe(model: str, parts: list, surfaces: list[dict]) -> dict:
    hint = HINTS[model]
    longitudinal, normal_index = hint["long_axis"], hint["mount_axis"]
    witnesses, planes = [], []
    for row in surfaces:
        if row["type"] != "cylinder":
            continue
        cylinder = row["primitive"]
        axis = np.asarray(cylinder["axis"])
        if abs(abs(axis[longitudinal]) - 1) > 1e-10:
            continue
        origin = np.asarray(cylinder["origin"])
        crossing = origin - axis * (origin[longitudinal] / axis[longitudinal])
        if np.linalg.norm(crossing - hint["axis_point_m"]) <= 1e-9:
            witnesses.append({**row, "axis_crossing_m": crossing.tolist()})
    assert witnesses, model
    representative = max(witnesses, key=lambda item: item["tessellated_area_m2"])
    for index, mesh in enumerate(parts):
        triangles = mesh.triangles
        selected = np.max(np.abs(triangles[:, :, normal_index]), axis=1) <= 1e-9
        if selected.any():
            points = triangles[selected].reshape(-1, 3)
            planes.append(
                {
                    "surface_part_index": index,
                    "triangles": int(selected.sum()),
                    "tessellated_area_m2": float(mesh.area_faces[selected].sum()),
                    "bounds_m": [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
                    "maximum_coordinate_residual_m": float(np.abs(points[:, normal_index]).max()),
                }
            )
    assert planes, model
    plane = max(planes, key=lambda item: item["tessellated_area_m2"])
    point = representative["axis_crossing_m"]
    return {
        "query_hint": hint,
        "coordinate_match_tolerance_m": 1e-9,
        "axis_direction_match_tolerance": 1e-10,
        "matching_tolerance_purpose": "Identify near-exact CAD coordinates; not physical clearance limits",
        "axis_point_m": point,
        "axis_direction": representative["primitive"]["axis"],
        "axis_witness_count": len(witnesses),
        "axis_witnesses": witnesses,
        "plane_coordinate_m": 0,
        "plane_normal_index": normal_index,
        "plane_candidates": planes,
        "display_plane": plane,
        "axis_to_plane_distance_m": abs(point[normal_index]),
        "mounting_hole_pattern": None,
        "fastening_tcp": None,
        "bit_stroke_m": None,
        "supply_hose_envelope": None,
    }


def _display_matrix(parts: list, model: str) -> np.ndarray:
    rotation = np.asarray(ROTATIONS[model], dtype=float)
    assert np.array_equal(rotation.T @ rotation, np.eye(3)) and np.linalg.det(rotation) == 1
    points = np.concatenate([part.vertices @ rotation.T for part in parts])
    lower, upper = points.min(axis=0), points.max(axis=0)
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = [-lower[0], -(lower[1] + upper[1]) / 2, -(lower[2] + upper[2]) / 2]
    return matrix


def _annotations(observation: dict, matrix: np.ndarray, bounds: np.ndarray) -> dict:
    axis = np.asarray(observation["axis_point_m"]) @ matrix[:3, :3].T + matrix[:3, 3]
    endpoints = np.tile(np.asarray(observation["axis_point_m"]), (2, 1))
    endpoints[:, observation["plane_normal_index"]] = 0
    longitudinal = observation["query_hint"]["long_axis"]
    endpoints[:, longitudinal] = np.asarray(observation["display_plane"]["bounds_m"])[:, longitudinal]
    projected = endpoints @ matrix[:3, :3].T + matrix[:3, 3]
    projected = projected[np.argsort(projected[:, 0])]
    dimension_x = float(projected[:, 0].mean())
    return {
        "axis_line_xz_m": [[-0.025, float(axis[2])], [float(bounds[1, 0] + 0.025), float(axis[2])]],
        "plane_line_xz_m": projected[:, [0, 2]].tolist(),
        "dimension_line_xz_m": [[dimension_x, float(axis[2])], [dimension_x, float(projected[0, 2])]],
        "plane_line_scope": "Longitudinal bounds of coplanar triangles; not a continuous contact-area claim",
    }


def _render(parts: list, model: str, observation: dict, output: Path) -> tuple[dict, dict]:
    matrix = _display_matrix(parts, model)
    scene = pyrender.Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.40, 0.40, 0.40])
    bounds = _add_parts(scene, parts, matrix)
    annotations = _annotations(observation, matrix, bounds)
    frames, display = {}, {}
    for view, settings in VIEWS.items():
        width, height = settings["pixels"]
        xmin, xmax = settings["x_m"]
        xmag = (xmax - xmin) / 2
        ymag = xmag * height / width
        target = np.array([(xmin + xmax) / 2, 0, 0])
        camera = pyrender.OrthographicCamera(xmag=xmag, ymag=ymag, znear=0.01, zfar=5)
        nodes = [scene.add(camera, pose=_look_at(target + [0, -2, 0], target))]
        for offset, intensity in (([0.4, -1.2, 1.5], 3.4), ([-0.6, -1.0, 0.4], 1.6)):
            light = pyrender.DirectionalLight(color=np.ones(3), intensity=intensity)
            nodes.append(scene.add(light, pose=_look_at(target + offset, target)))
        assert bounds[0, 2] >= -ymag and bounds[1, 2] <= ymag
        if view == "whole":
            assert bounds[0, 0] >= xmin and bounds[1, 0] <= xmax
        renderer = pyrender.OffscreenRenderer(width, height)
        try:
            color, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
            assert np.isfinite(depth).all() and np.count_nonzero(depth)
            path = output / f"{model.lower()}_{view}.png"
            with path.open("xb") as stream:
                Image.fromarray(color).save(stream, format="PNG")
            with Image.open(path) as picture:
                assert picture.size == (width, height) and picture.mode == "RGBA"
                encoded = io.BytesIO()
                picture.save(encoded, format="WEBP", lossless=True, exact=True, method=6)
            webp = encoded.getvalue()
            with Image.open(io.BytesIO(webp)) as decoded:
                assert np.array_equal(np.asarray(decoded), color)
        finally:
            renderer.delete()
            for node in nodes:
                scene.remove_node(node)
        frames[view] = {
            **settings,
            "z_m": [-ymag, ymag],
            "png_file": str(path.relative_to(ROOT)),
            "png_sha256": _digest(path),
            "webp_sha256": _sha(webp),
            "webp_bytes": len(webp),
            "foreground_pixels": int(np.count_nonzero(depth)),
        }
        display[view] = {**frames[view], "data_url": "data:image/webp;base64," + base64.b64encode(webp).decode()}
        print("DATUM_FRAME_SAVED", model, view, flush=True)
    return {
        "display_matrix": matrix.tolist(),
        "display_bounds_m": bounds.tolist(),
        "annotations": annotations,
        "frames": frames,
    }, display


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface_directory", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    parser.add_argument("--output_html", type=Path, required=True)
    args = parser.parse_args()
    baseline_path = ROOT / "data/hvjb_fastening_cad_v01.json"
    baseline_sha = _digest(baseline_path)
    baseline = json.loads(baseline_path.read_text())
    extraction_path = args.surface_directory / "surface_extraction.json"
    extraction_sha = _digest(extraction_path)
    extraction = json.loads(extraction_path.read_text())
    surface_path = ROOT / extraction["surface_records_file"]
    assert _digest(surface_path) == extraction["surface_records_sha256"]
    surfaces = json.loads(gzip.decompress(surface_path.read_bytes()))
    pins = baseline["conversion"]["input_sha256_after"]
    assert extraction["input_sha256_after"] == pins
    for name, expected in pins.items():
        assert _digest(ROOT / name) == expected, name
    output = args.output_directory.resolve()
    output.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    models, display = {}, {}
    for source in baseline["conversion"]["sources"]:
        model = source["model"]
        path = ROOT / source["glb_file"]
        assert _digest(path) == source["glb_sha256"]
        audit = next(row for row in extraction["models"] if row["model"] == model)
        assert audit["triangle_positions_equal"] and audit["original_glb_sha256"] == source["glb_sha256"]
        parts = _tool_parts(path)
        assert len(parts) == source["surface_nodes"] and sum(len(part.faces) for part in parts) == source["triangles"]
        observation = _observe(model, parts, surfaces[model])
        rendered, frames = _render(parts, model, observation, output)
        models[model] = {
            "source_glb_file": source["glb_file"],
            "source_glb_sha256": source["glb_sha256"],
            "surface_nodes": len(parts),
            "triangles": source["triangles"],
            "observation": observation,
            "render": rendered,
        }
        display[model] = {
            "distance_mm": observation["axis_to_plane_distance_m"] * 1000,
            "annotations": rendered["annotations"],
            "frames": frames,
        }
        assert _digest(path) == source["glb_sha256"]
        print("DATUM_OBSERVED", model, "distance_mm", display[model]["distance_mm"], flush=True)
    template = ROOT / "scripts/hvjb_fastening_datum_v01.html"
    markup = template.read_text().replace("__MODEL_DATA__", json.dumps({"models": display}, separators=(",", ":")))
    assert "__MODEL_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    assert args.output_html.read_text() == markup
    after = {name: _digest(ROOT / name) for name in pins}
    assert after == pins and _digest(baseline_path) == baseline_sha and _digest(extraction_path) == extraction_sha
    catalog = ROOT / "references/hvjb_fastening_datum_20260917/SES_SEM_1017_EN.pdf"
    record = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Drawing-corresponding source CAD axis and mounting-side plane; no fastening-pose or fit verdict",
        "baseline_sha256": baseline_sha,
        "surface_extraction_file": str(extraction_path.resolve().relative_to(ROOT)),
        "surface_extraction_sha256": extraction_sha,
        "catalog": {
            "file": str(catalog.relative_to(ROOT)),
            "sha256": _digest(catalog),
            "url": "https://www.stoeger.com/files/stoeger/downloads/Broschueren/SES_1017_END_ENG_web.pdf",
            "printed_date": "10/2017",
            "pages_read": [1, 2, 3, 4],
        },
        "models": models,
        "inline_html": {"path": str(args.output_html), "sha256": _digest(args.output_html)},
        "template_sha256": _digest(template),
        "input_sha256_before": pins,
        "input_sha256_after": after,
        "selected_tool_configuration": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(ROOT / "data/hvjb_fastening_datum_v01.json", record)
    print("FASTENING_DATUM_COMPLETE", args.output_html, flush=True)


if __name__ == "__main__":
    main()
