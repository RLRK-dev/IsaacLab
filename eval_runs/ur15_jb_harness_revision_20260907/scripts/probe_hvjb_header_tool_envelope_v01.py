# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Observe full saved tool radial bounds [m] without choosing a fastening TCP."""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from build_hvjb_fastening_cad_reference_v01 import _write_json
from probe_hand_tool_access_v01 import _clip_polygon
from probe_hvjb_header_hand_access_v01 import digest, witness_error
from render_hvjb_fastening_cad_v01 import _tool_parts

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = "data/hvjb_header_tool_envelope_v01.json"


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def protected_inputs(settings: dict) -> dict[str, str]:
    previous = read_json(settings["previous_readback"])
    pins = {**previous["input_sha256_current"], **previous["artifacts_sha256"]}
    for name in (
        SETTINGS,
        settings["previous_readback"],
        settings["tools"],
        settings["hand_observation"],
        settings["hand_display"],
        settings["reused_clipping"],
        settings["reused_witness_validator"],
        settings["reused_tool_loader"],
    ):
        observed = digest(ROOT / name)
        assert name not in pins or pins[name] == observed, name
        pins[name] = observed
    actual = {name: digest(ROOT / name) for name in pins}
    assert actual == pins, "Protected input SHA mismatch"
    return actual


def farthest_in_band(triangles: np.ndarray, z_bounds: np.ndarray, limits: list[float]) -> tuple[dict, np.ndarray]:
    """Clip complete triangles to an axial interval and return maximum radial reach [m]."""
    lower, upper = limits
    selected = np.flatnonzero((z_bounds[:, 0] <= upper) & (z_bounds[:, 1] >= lower))
    full = selected[(z_bounds[selected, 0] >= lower) & (z_bounds[selected, 1] <= upper)]
    best = {"radius_m": None, "face_index": None, "witness_query_m": None}
    if len(full):
        squared = np.sum(triangles[full, :, :2] ** 2, axis=2)
        row, corner = np.unravel_index(int(squared.argmax()), squared.shape)
        index = int(full[row])
        best = {
            "radius_m": float(np.sqrt(squared[row, corner])),
            "face_index": index,
            "witness_query_m": triangles[index, corner].tolist(),
        }
    partial = selected[(z_bounds[selected, 0] < lower) | (z_bounds[selected, 1] > upper)]
    for index in partial:
        polygon = _clip_polygon(list(triangles[index]), lower, True)
        if polygon:
            polygon = _clip_polygon(polygon, upper, False)
        if not polygon:
            continue
        points = np.asarray(polygon)
        radii = np.linalg.norm(points[:, :2], axis=1)
        corner = int(radii.argmax())
        radius = float(radii[corner])
        if best["radius_m"] is None or radius > best["radius_m"]:
            best = {"radius_m": radius, "face_index": int(index), "witness_query_m": points[corner].tolist()}
    return best, selected


def analytic_checks() -> list[dict]:
    cases = [
        ("clipping_limits_farthest_edge", [[[1, 0, 0], [3, 0, 4], [1, 0, 4]]], [2, 3], 2.5),
        ("whole_triangle", [[[3, 4, 1], [0, 1, 1], [0, 0, 2]]], [0, 3], 5.0),
        ("boundary_point_retained", [[[2, 0, 2], [3, 0, 3], [3, 1, 3]]], [0, 2], 2.0),
        ("zero_area_point_retained", [[[2, 0, 1], [2, 0, 1], [2, 0, 1]]], [0, 2], 2.0),
        ("outside_interval", [[[2, 0, 1], [2, 0, 2], [3, 0, 2]]], [3, 4], None),
    ]
    result = []
    for name, coordinates, band, expected in cases:
        triangles = np.asarray(coordinates, dtype=float)
        bounds = np.column_stack((triangles[:, :, 2].min(axis=1), triangles[:, :, 2].max(axis=1)))
        observed, _ = farthest_in_band(triangles, bounds, band)
        radius = observed["radius_m"]
        assert radius is None if expected is None else abs(radius - expected) < 1e-12, (name, observed)
        result.append({"name": name, "expected_radius_m": expected, "observed": observed})
    return result


def query_frame(source: dict, parts: list) -> tuple[np.ndarray, dict]:
    """Construct an axis-relative readout frame from recorded source coordinates [m]."""
    observation = source["observation"]
    source_to_observation = np.asarray(observation.get("source_to_observation_matrix", np.eye(4)))
    source_point = np.linalg.inv(source_to_observation) @ np.r_[observation["axis_point_m"], 1]
    axis = source_to_observation[:3, :3].T @ np.asarray(observation["axis_direction"])
    axis /= np.linalg.norm(axis)
    display_rotation = np.asarray(source["render"]["source_to_display_matrix"])[:3, :3]
    if (display_rotation @ axis)[0] < 0:
        axis *= -1
    first = display_rotation[1] - axis * np.dot(display_rotation[1], axis)
    first /= np.linalg.norm(first)
    second = np.cross(axis, first)
    matrix = np.eye(4)
    matrix[:3, :3] = np.vstack((first, second, axis))
    matrix[:3, 3] = -matrix[:3, :3] @ source_point[:3]
    vertices = np.concatenate([part.vertices for part in parts])
    before = vertices @ matrix[:3, :3].T + matrix[:3, 3]
    leading = float(before[:, 2].min())
    matrix[2, 3] -= leading
    assert np.max(abs(matrix[:3, :3] @ matrix[:3, :3].T - np.eye(3))) < 1e-12
    assert abs(np.linalg.det(matrix[:3, :3]) - 1) < 1e-12
    return matrix, {
        "source_axis_point_m": source_point[:3].tolist(),
        "source_axis_toward_rear": axis.tolist(),
        "leading_projection_from_source_axis_point_m": leading,
        "source_to_query_matrix": matrix.tolist(),
        "query_coordinates": "u/v perpendicular to the source axis; s from the complete saved CAD's leading end",
        "leading_end_is_fastening_tcp": False,
    }


def observe_tool(name: str, source: dict, settings: dict) -> dict:
    assert digest(ROOT / source["source_glb_file"]) == source["source_glb_sha256"]
    parts = _tool_parts(ROOT / source["source_glb_file"])
    assert len(parts) == source["surface_nodes"]
    assert sum(len(part.faces) for part in parts) == source["triangles"]
    matrix, datum = query_frame(source, parts)
    original = np.concatenate([part.triangles for part in parts])
    triangles = original @ matrix[:3, :3].T + matrix[:3, 3]
    limits = np.column_stack((triangles[:, :, 2].min(axis=1), triangles[:, :, 2].max(axis=1)))
    step, tolerance = settings["profile_bin_depth_m"], settings["numeric_comparison_tolerance_m"]
    first = math.floor(min(settings["profile_lower_depth_m"], float(limits[:, 0].min())) / step)
    last = math.ceil(float(limits[:, 1].max()) / step)
    boundaries = np.arange(first, last + 1, dtype=float) * step
    offsets = np.r_[0, np.cumsum([len(part.faces) for part in parts])]
    seen = np.zeros(len(triangles), dtype=bool)
    profile = []
    for i, (lower, upper) in enumerate(zip(boundaries[:-1], boundaries[1:], strict=True)):
        band = [float(lower), float(upper)]
        row, selected = farthest_in_band(triangles, limits, band)
        seen[selected] = True
        index = row.pop("face_index")
        if index is not None:
            witness = np.asarray(row["witness_query_m"])
            part = int(np.searchsorted(offsets, index, side="right") - 1)
            error = witness_error(triangles[index], witness)
            assert error < tolerance, (name, i, error)
            assert lower - tolerance <= witness[2] <= upper + tolerance
            assert abs(np.linalg.norm(witness[:2]) - row["radius_m"]) < tolerance
            source_witness = (witness - matrix[:3, 3]) @ matrix[:3, :3]
            source_error = witness_error(original[index], source_witness)
            assert source_error < tolerance, (name, i, source_error)
            row.update(
                surface_part_index=part,
                source_face_index=int(index - offsets[part]),
                witness_source_m=source_witness.tolist(),
                witness_on_triangle_error_m=error,
                source_witness_on_triangle_error_m=source_error,
            )
        profile.append({"depth_range_m": band, "intersecting_source_triangles": len(selected), **row})
        if i % 100 == 0:
            print("TOOL_RADIAL_BIN", name, i + 1, "of", len(boundaries) - 1, flush=True)
    assert seen.all(), "Every saved source triangle must participate, including degenerates"
    vertex_maximum = float(np.linalg.norm(triangles[:, :, :2], axis=2).max())
    maximum = max(row["radius_m"] for row in profile if row["radius_m"] is not None)
    assert abs(vertex_maximum - maximum) < tolerance
    print("TOOL_RADIAL_COMPLETE", name, "bins", len(profile), "maximum_radius_m", maximum, flush=True)
    return {
        "source_glb_file": source["source_glb_file"],
        "source_glb_sha256": source["source_glb_sha256"],
        "source_triangles": len(triangles),
        "source_surface_parts": len(parts),
        "surface_part_order": "sorted(scene.graph.nodes_geometry), reused _tool_parts",
        "zero_area_source_triangles": sum(int(np.count_nonzero(part.area_faces == 0)) for part in parts),
        "source_triangles_observed": int(seen.sum()),
        "datum": datum,
        "whole_depth_range_m": [float(limits[:, 0].min()), float(limits[:, 1].max())],
        "whole_maximum_radius_m": maximum,
        "whole_vertex_maximum_radius_m": vertex_maximum,
        "profile": profile,
    }


def compare_registration(tools: dict, hand: dict, settings: dict) -> list[dict]:
    """Compare recorded radial bounds at explicitly hypothetical translations [m]."""
    parameters, step = settings["comparison_translation_m"], settings["profile_bin_depth_m"]
    first = round(parameters["minimum"] / step)
    last = round(parameters["maximum"] / step)
    assert parameters["step"] == step and parameters["selected_value"] is None
    output = []
    for header in hand["models"]:
        for axis in header["axes"]:
            bands = axis["profile"]
            for name, tool in tools.items():
                lookup = {round(row["depth_range_m"][0] / step): row for row in tool["profile"]}
                for shift in range(first, last + 1):
                    matches = []
                    for i, band in enumerate(bands):
                        lower, upper = band["depth_range_m"]
                        index = round(lower / step)
                        assert abs(lower - index * step) < 1e-10 and abs(upper - lower - step) < 1e-10
                        tool_band = lookup.get(index - shift)
                        hand_radius = band["all"]["radius_to_surface_m"]
                        radius = None if tool_band is None else tool_band["radius_m"]
                        if hand_radius is not None and radius is not None:
                            matches.append((hand_radius - radius, i, tool_band["depth_range_m"]))
                    nearest = min(matches) if matches else None
                    output.append(
                        {
                            "feature_id": header["feature_id"],
                            "screw_name": axis["screw_name"],
                            "nominal_index": axis["nominal_index"],
                            "frame": axis["pose"]["frame"],
                            "tool": name,
                            "hypothetical_cad_leading_position_m": shift * step,
                            "compared_bins": len(matches),
                            "minimum_radial_bound_difference_m": None if nearest is None else nearest[0],
                            "hand_bin_index": None if nearest is None else nearest[1],
                            "tool_bin_range_m": None if nearest is None else nearest[2],
                        }
                    )
    assert len(output) == 14 * len(tools) * (last - first + 1)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists(), "Keep prior observations"
    settings = read_json(SETTINGS)
    before = protected_inputs(settings)
    checks = analytic_checks()
    sources, hand = read_json(settings["tools"]), read_json(settings["hand_observation"])
    tools = {name: observe_tool(name, sources["models"][name], settings) for name in ("SES2001", "SEV2001")}
    comparisons = compare_registration(tools, hand, settings)
    after = {name: digest(ROOT / name) for name in before}
    assert after == before
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": settings["scope"],
        "settings": settings,
        "analytic_checks": checks,
        "tools": tools,
        "registration_comparisons": comparisons,
        "source_input_sha256_before": before,
        "source_input_sha256_after": after,
        "script_sha256": digest(Path(__file__)),
        "hand_measurement_recomputed": False,
        "native_opened": False,
        "native_saved": False,
        "motion_recomputed": False,
        "geometry_modified": False,
        "selected_tool_configuration": None,
        "selected_axial_registration_m": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(args.output_json, report)
    assert read_json(str(args.output_json.resolve().relative_to(ROOT))) == report
    print("HEADER_TOOL_ENVELOPE_COMPLETE", args.output_json, "comparisons", len(comparisons), flush=True)


if __name__ == "__main__":
    main()
