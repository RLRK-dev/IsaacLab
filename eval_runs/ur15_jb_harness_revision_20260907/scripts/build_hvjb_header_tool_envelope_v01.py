# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Present saved radial bounds with unselected axial comparison offsets [m]."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from build_hvjb_fastening_cad_reference_v01 import _write_json
from probe_hvjb_header_hand_access_v01 import digest

ROOT = Path(__file__).resolve().parents[1]


def build_display(record: dict) -> dict:
    hand = json.loads((ROOT / record["settings"]["hand_observation"]).read_text())
    saved_display = json.loads((ROOT / record["settings"]["hand_display"]).read_text())["display"]
    headers = []
    for header, observed in zip(saved_display["headers"], hand["models"], strict=True):
        assert header["feature_id"] == observed["feature_id"]
        axes = []
        for shown, axis in zip(header["axes"], observed["axes"], strict=True):
            assert shown["frame"] == axis["pose"]["frame"]
            assert shown["axis_xz_mm"] == [v * 1000 for v in axis["nominal_local_xz_m"]]
            axes.append(
                {key: shown[key] for key in ("id", "number", "header_label", "axis_xz_mm", "frame")}
                | {
                    "screw_name": axis["screw_name"],
                    "nominal_index": axis["nominal_index"],
                    "profile": [
                        {
                            "depth_mm": [v * 1000 for v in row["depth_range_m"]],
                            "radius_mm": None
                            if row["all"]["radius_to_surface_m"] is None
                            else row["all"]["radius_to_surface_m"] * 1000,
                        }
                        for row in axis["profile"]
                    ],
                }
            )
        headers.append({key: value for key, value in header.items() if key != "axes"} | {"axes": axes})
    parameters = record["settings"]["comparison_translation_m"]
    return {
        "headers": headers,
        "aperture_height_mm": saved_display["aperture_height_mm"],
        "aperture_radius_mm": saved_display["aperture_radius_mm"],
        "bin_mm": record["settings"]["profile_bin_depth_m"] * 1000,
        "offset_mm": {key: parameters[key] * 1000 for key in ("minimum", "maximum", "step", "initial_display")},
        "adopted_offset_mm": None,
        "tools": {
            name: {
                "profile": [
                    {
                        "depth_mm": [v * 1000 for v in row["depth_range_m"]],
                        "radius_mm": None if row["radius_m"] is None else row["radius_m"] * 1000,
                    }
                    for row in tool["profile"]
                ],
                "source_triangles": tool["source_triangles"],
                "whole_maximum_radius_mm": tool["whole_maximum_radius_m"] * 1000,
            }
            for name, tool in record["tools"].items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, required=True)
    parser.add_argument("--output_html", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists() and not args.output_html.exists()
    record = json.loads(args.record.read_text())
    before = record["source_input_sha256_after"]
    assert {name: digest(ROOT / name) for name in before} == before
    display = build_display(record)
    assert sum(len(row["axes"]) for row in display["headers"]) == 14
    template = ROOT / "scripts/hvjb_header_tool_envelope_v01.html"
    markup = template.read_text().replace(
        "__ENVELOPE_DATA__", json.dumps(display, ensure_ascii=False, separators=(",", ":"))
    )
    assert "__ENVELOPE_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    assert args.output_html.read_text() == markup
    after = {name: digest(ROOT / name) for name in before}
    assert after == before
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Saved radial bounds and hypothetical registration, not a chosen TCP or 3D contact result",
        "record": str(args.record.resolve().relative_to(ROOT)),
        "record_sha256": digest(args.record),
        "template_sha256": digest(template),
        "builder_sha256": digest(Path(__file__)),
        "output_html": str(args.output_html),
        "output_html_sha256": digest(args.output_html),
        "output_html_bytes": len(markup.encode()),
        "display": display,
        "source_input_sha256_before": before,
        "source_input_sha256_after": after,
        "selected_tool_configuration": None,
        "selected_axial_registration_m": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(args.output_json, result)
    assert json.loads(args.output_json.read_text()) == result
    print("HEADER_TOOL_ENVELOPE_FIGURE_COMPLETE", args.output_html, len(markup.encode()), flush=True)


if __name__ == "__main__":
    main()
