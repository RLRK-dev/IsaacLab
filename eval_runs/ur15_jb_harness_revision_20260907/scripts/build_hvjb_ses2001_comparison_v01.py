# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compare two saved screw-tool examples at equal scale using source CAD datums [m]."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import build_hvjb_fastening_datum_v01 as datum
import numpy as np
from build_hvjb_fastening_cad_reference_v01 import _write_json
from prepare_hvjb_fastening_cad_v01 import _digest
from prepare_hvjb_ses2001_cad_v01 import _step
from render_hvjb_fastening_cad_v01 import _tool_parts

ROOT = Path(__file__).resolve().parents[1]


def _entity(text: str, number: str) -> str:
    matches = re.findall(rf"^#{number}\s*=\s*(.*?);", text, flags=re.MULTILINE | re.DOTALL)
    assert len(matches) == 1, number
    return matches[0]


def _triplet(text: str, kind: str) -> np.ndarray:
    assert text.startswith(kind + "("), text
    match = re.search(r",\s*\(([^()]*)\)\s*\)\s*$", text)
    assert match, text
    result = np.asarray([float(value) for value in match.group(1).split(",")])
    assert result.shape == (3,) and np.isfinite(result).all()
    return result


def _step_witness(text: str, number: str, kind: str) -> dict:
    # Bounded transcription of four identified entities, not a general STEP interpreter.
    surface = _entity(text, number)
    assert surface.startswith(kind + "("), surface
    placement_id = re.findall(r"#(\d+)", surface)[0]
    placement = _entity(text, placement_id)
    assert placement.startswith("AXIS2_PLACEMENT_3D("), placement
    refs = re.findall(r"#(\d+)", placement)
    assert len(refs) == 3  # This source explicitly supplies both directions.
    definitions = {key: _entity(text, key) for key in refs}
    origin = _triplet(definitions[refs[0]], "CARTESIAN_POINT") * 0.001
    axis = _triplet(definitions[refs[1]], "DIRECTION")
    reference = _triplet(definitions[refs[2]], "DIRECTION")
    assert abs(np.linalg.norm(axis) - 1) < 1e-10
    result = {
        "entity": number,
        "kind": kind,
        "definitions": {number: surface, placement_id: placement, **definitions},
        "origin_m": origin.tolist(),
        "direction": axis.tolist(),
        "reference_direction": reference.tolist(),
        "source_length_unit": "mm",
    }
    if kind == "CYLINDRICAL_SURFACE":
        result["radius_m"] = float(surface.rsplit(",", 1)[1].rstrip(")")) * 0.001
    return result


def _ses_observation(parts: list, settings: dict) -> tuple[dict, list, np.ndarray]:
    raw, metadata = _step(settings)
    assert metadata["step_sha256"] == "9a0975d529b2f31f85f81e93dc792f94745b07ade8dcb04fd4a29008b9c5e853"
    text = raw.decode("latin1")
    assert metadata["declared_length_units"] == ["SI_UNIT(.MILLI.,.METRE.)\r\n)"]
    unsupported = re.findall(
        r"\b(?:ITEM_DEFINED_TRANSFORMATION|CARTESIAN_TRANSFORMATION_OPERATOR\w*|MAPPED_ITEM)\s*\(", text
    )
    assert not unsupported, "This bounded source-coordinate read does not interpret assembly transformations"
    cylinders = [_step_witness(text, number, "CYLINDRICAL_SURFACE") for number in ("63743", "63745")]
    planes = [_step_witness(text, number, "PLANE") for number in ("13153", "13169")]
    crossings = []
    for cylinder in cylinders:
        direction, origin = np.asarray(cylinder["direction"]), np.asarray(cylinder["origin_m"])
        assert abs(abs(direction[0]) - 1) < 1e-10
        crossing = origin - direction * origin[0] / direction[0]
        assert np.linalg.norm(crossing) < 1e-9
        crossings.append(crossing)
    for plane in planes:
        assert abs(abs(plane["direction"][2]) - 1) < 1e-10
        assert abs(plane["origin_m"][2] + 0.058) < 1e-9
    step_plane_z = planes[0]["origin_m"][2]
    stored_z = float(np.float32(step_plane_z))
    transform = np.eye(4)
    transform[2, 3] = -stored_z
    candidates, display_parts = [], []
    for index, original in enumerate(parts):
        mesh = original.copy()
        selected = np.all(original.triangles[:, :, 2] == stored_z, axis=1)
        mesh.apply_transform(transform)
        display_parts.append(mesh)
        if selected.any():
            points = mesh.triangles[selected].reshape(-1, 3)
            candidates.append(
                {
                    "surface_part_index": index,
                    "triangles": int(selected.sum()),
                    "tessellated_area_m2": float(mesh.area_faces[selected].sum()),
                    "bounds_m": [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
                    "maximum_coordinate_residual_m": float(np.abs(points[:, 2]).max()),
                }
            )
    assert candidates
    display_plane = max(candidates, key=lambda row: row["tessellated_area_m2"])
    point = crossings[0] + transform[:3, 3]
    observation = {
        "source_step_cylinders": cylinders,
        "source_step_planes": planes,
        "source_axis_crossings_m": [point.tolist() for point in crossings],
        "source_axis_to_plane_distance_m": abs(crossings[0][2] - step_plane_z),
        "source_plane_coordinate_m": step_plane_z,
        "stored_float32_plane_coordinate_m": stored_z,
        "float32_plane_rounding_m": stored_z - step_plane_z,
        "plane_selection": "Exact equality to the float32 representation of the STEP plane coordinate",
        "coordinate_match_tolerance_m": 1e-9,
        "axis_direction_match_tolerance": 1e-10,
        "matching_scope": "Identify source CAD coordinates; no physical clearance or acceptance threshold",
        "query_hint": {"long_axis": 0, "mount_axis": 2},
        "axis_point_m": point.tolist(),
        "axis_direction": cylinders[0]["direction"],
        "plane_coordinate_m": 0,
        "plane_normal_index": 2,
        "display_plane": display_plane,
        "plane_candidates": candidates,
        "axis_to_plane_distance_m": abs(point[2]),
        "source_to_observation_matrix": transform.tolist(),
        "source_cylinder_diameter_m": 2 * cylinders[0]["radius_m"],
        "cylinder_scope": "Selected source cylinders, not a maximum nose envelope or clearance diameter",
        "mounting_hole_pattern": None,
        "fastening_tcp": None,
        "bit_stroke_m": None,
    }
    return observation, display_parts, transform


def _render_models(conversion: dict, baseline: dict, settings: dict, output: Path) -> tuple[dict, dict]:
    sources = {"SES2001": conversion, "SEV2001": baseline["models"]["SEV2001"]}
    datum.ROTATIONS["SES2001"] = np.eye(3).tolist()
    datum.VIEWS.update(
        {
            "whole": {"pixels": [1200, 220], "x_m": [-0.045, 1.195]},
            "front": {"pixels": [1000, 380], "x_m": [-0.025, 0.525]},
        }
    )
    models, display = {}, {}
    for model, source in sources.items():
        name = source.get("glb_file", source.get("source_glb_file"))
        expected = source.get("glb_sha256", source.get("source_glb_sha256"))
        assert _digest(ROOT / name) == expected
        parts = _tool_parts(ROOT / name)
        assert len(parts) == source["surface_nodes"]
        assert sum(len(part.faces) for part in parts) == source["triangles"]
        if model == "SES2001":
            observation, parts, transform = _ses_observation(parts, settings)
        else:
            observation, transform = source["observation"], np.eye(4)
        rendered, frames = datum._render(parts, model, observation, output)
        rendered["source_to_display_matrix"] = (np.asarray(rendered["display_matrix"]) @ transform).tolist()
        models[model] = {
            "source_glb_file": name,
            "source_glb_sha256": expected,
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
        assert _digest(ROOT / name) == expected
        print("TOOL_DATUM", model, "axis_to_mount_mm", display[model]["distance_mm"], flush=True)
    return models, display


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_directory", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, required=True)
    parser.add_argument("--output_html", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.output_json, args.output_html, args.output_directory):
        assert not path.exists(), path
    conversion_path = ROOT / "audit/hvjb_ses2001_cad_v01.json"
    conversion = json.loads(conversion_path.read_text())
    before = conversion["input_sha256_after"].copy()
    for name in (
        str(conversion_path.relative_to(ROOT)),
        conversion["glb_file"],
        conversion["object_records_file"],
        conversion["surface_records_file"],
    ):
        before[name] = _digest(ROOT / name)
    assert {name: _digest(ROOT / name) for name in before} == before
    baseline = json.loads((ROOT / "data/hvjb_fastening_datum_v01.json").read_text())
    settings = json.loads((ROOT / "data/hvjb_ses2001_sources_v01.json").read_text())
    output = args.output_directory.resolve()
    output.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    models, display = _render_models(conversion, baseline, settings, output)
    template = ROOT / "scripts/hvjb_ses2001_comparison_v01.html"
    markup = template.read_text().replace("__MODEL_DATA__", json.dumps({"models": display}, separators=(",", ":")))
    assert "__MODEL_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    assert args.output_html.read_text() == markup
    after = {name: _digest(ROOT / name) for name in before}
    assert after == before
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Equal-scale source CAD comparison, not an installation pose or tool-to-hand clearance",
        "models": models,
        "script_sha256": _digest(Path(__file__)),
        "template_sha256": _digest(template),
        "inline_html": {"path": str(args.output_html), "sha256": _digest(args.output_html)},
        "input_sha256_before": before,
        "input_sha256_after": after,
        "native_opened": False,
        "native_saved": False,
        "motion_recomputed": False,
        "selected_tool_configuration": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(args.output_json, result)
    print("SES2001_COMPARISON_COMPLETE", args.output_html, flush=True)


if __name__ == "__main__":
    main()
