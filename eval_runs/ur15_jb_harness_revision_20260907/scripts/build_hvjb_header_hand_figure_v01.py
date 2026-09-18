# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Present saved H05 screw-axis distances [m] without rerunning the geometry query."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from probe_hvjb_header_hand_access_v01 import ROOT, digest


def axis_display(axis: dict, feature: str, number: int) -> dict:
    nearest = axis["whole_span"]["all"]
    return {
        "id": f"{feature}_{number}",
        "number": number,
        "header_label": "3口" if feature == "P16" else "2口",
        "axis_xz_mm": [v * 1000 for v in axis["nominal_local_xz_m"]],
        "frame": axis["pose"]["frame"],
        "nearest": {
            "radius_mm": nearest["radius_to_surface_m"] * 1000,
            "category": nearest["category"],
            "object": nearest["object"],
            "witness_header_mm": [v * 1000 for v in nearest["witness_header_m"]],
        },
        "profile": [
            {
                "depth_mm": [v * 1000 for v in band["depth_range_m"]],
                "radius_mm": {
                    category: None if row["radius_to_surface_m"] is None else row["radius_to_surface_m"] * 1000
                    for category, row in band["categories"].items()
                },
            }
            for band in axis["profile"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_html", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, default=ROOT / "data/hvjb_header_hand_display_v01.json")
    args = parser.parse_args()
    assert not args.output_html.exists() and not args.output_json.exists(), "Preserve the existing figure"
    record_path = ROOT / "audit/hvjb_header_hand_access_v01.json"
    record = json.loads(record_path.read_text())
    assert all(digest(ROOT / path) == sha for path, sha in record["source_input_sha256_after"].items())
    settings = json.loads((ROOT / record["settings"]["header_settings"]).read_text())
    display = {
        "headers": [],
        "aperture_height_mm": settings["drawing_conditions"]["aperture_height_m"] * 1000,
        "aperture_radius_mm": settings["drawing_conditions"]["aperture_radius_m"] * 1000,
    }
    number = 1
    for spec, measured in zip(settings["headers"], record["models"], strict=True):
        axes = [axis_display(axis, spec["feature_id"], number + i) for i, axis in enumerate(measured["axes"])]
        display["headers"].append(
            {
                "feature_id": spec["feature_id"],
                "part_number": spec["part_number"],
                "label": "3口" if spec["feature_id"] == "P16" else "2口",
                "bay_x_mm": [v * 1000 for v in spec["bay_centers_x_m"]],
                "aperture_widths_mm": [v * 1000 for v in spec["aperture_widths_m"]],
                "axes": axes,
            }
        )
        number += len(axes)
    template = ROOT / "scripts/hvjb_header_hand_access_v01.html"
    markup = template.read_text().replace("__HEADER_HAND_DATA__", json.dumps(display, ensure_ascii=False))
    assert "__HEADER_HAND_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "record_sha256": digest(record_path),
        "template_sha256": digest(template),
        "builder_sha256": digest(Path(__file__)),
        "output_html": str(args.output_html),
        "output_html_sha256": digest(args.output_html),
        "display": display,
        "scope": (
            "Header-axis selection and saved interval-minimum surface distances; no tool selection or physical verdict"
        ),
    }
    with args.output_json.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == result and args.output_html.read_text() == markup
    print("HEADER_HAND_FIGURE_COMPLETE", args.output_html, len(markup.encode()), flush=True)


if __name__ == "__main__":
    main()
