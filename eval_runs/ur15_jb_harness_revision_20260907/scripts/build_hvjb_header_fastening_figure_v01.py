# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Present saved header observations without repeating the geometry query."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from probe_hvjb_header_fastening_v01 import INPUT, ROOT, digest


def display_screw(row: dict, header: dict, number: int) -> dict:
    origin = header["model_translation_m"][1]
    head, shaft = row["head_bounds_world_m"], row["shaft_bounds_world_m"]
    wall = row["front_wall_interval_world_y_m"]
    return {
        "id": f"{header['feature_id']}_{number}",
        "number": number,
        "header_label": "3口" if header["feature_id"] == "P16" else "2口",
        "world_xz_mm": [v * 1000 for v in row["axis_world_xz_m"]],
        "local_xz_mm": [v * 1000 for v in row["axis_local_xz_m"]],
        "nominal_xz_mm": [v * 1000 for v in row["nominal_local_xz_m"]],
        "axial_mm": {
            "head_front": (head[0][1] - origin) * 1000,
            "head_back": (head[1][1] - origin) * 1000,
            "cad_plane": row["nearest_parallel_plane_local_y_m"] * 1000,
            "wall_outer": (wall[0] - origin) * 1000,
            "wall_inner": (wall[1] - origin) * 1000,
            "tip": (shaft[1][1] - origin) * 1000,
        },
        "protrusion_mm": row["shaft_tip_minus_wall_inner_m"] * 1000,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_html", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, default=ROOT / "data/hvjb_header_fastening_display_v01.json")
    args = parser.parse_args()
    assert not args.output_html.exists() and not args.output_json.exists(), "Preserve previous figures"
    record_path = ROOT / "audit/hvjb_header_fastening_v01.json"
    record = json.loads(record_path.read_text())
    inputs = json.loads((ROOT / INPUT).read_text())
    assert all(digest(ROOT / path) == sha for path, sha in record["input_sha256_after"].items())
    payload = {
        "headers": [],
        "aperture_height_mm": inputs["drawing_conditions"]["aperture_height_m"] * 1000,
        "aperture_radius_mm": inputs["drawing_conditions"]["aperture_radius_m"] * 1000,
    }
    for spec, observed in zip(inputs["headers"], record["models"], strict=True):
        number = sum(len(h["screws"]) for h in payload["headers"])
        payload["headers"].append(
            {
                "feature_id": spec["feature_id"],
                "part_number": spec["part_number"],
                "label": "3口" if spec["feature_id"] == "P16" else "2口",
                "hole_x_mm": [v * 1000 for v in spec["hole_x_m"]],
                "hole_z_mm": [v * 1000 for v in spec["hole_z_m"]],
                "bay_x_mm": [v * 1000 for v in spec["bay_centers_x_m"]],
                "aperture_widths_mm": [v * 1000 for v in spec["aperture_widths_m"]],
                "screws": [display_screw(row, spec, number + i + 1) for i, row in enumerate(observed["screws"])],
            }
        )
    template = ROOT / "scripts/hvjb_header_fastening_v01.html"
    markup = template.read_text().replace("__HEADER_DATA__", json.dumps(payload, ensure_ascii=False))
    assert "__HEADER_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    assert args.output_html.read_text() == markup
    result = {
        "source_audit_sha256": digest(record_path),
        "input_sha256": digest(ROOT / INPUT),
        "template_sha256": digest(template),
        "html_path": str(args.output_html.resolve()),
        "html_sha256": digest(args.output_html),
        "display": payload,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == result
    print("HEADER_FIGURE_COMPLETE", args.output_html, flush=True)


if __name__ == "__main__":
    main()
