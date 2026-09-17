# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package saved manufacturer reference frames without changing the source geometry."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "references/hvjb_fastening_cad_20260917"
DOWNLOAD = "https://www.stoeger.com/de/downloads.html?file=files/stoeger/downloads/CAD/"
FILES = {
    "ses1601.pdf": "SES/automatic_screwdriver_for_screws_SES1601_series.pdf",
    "ses1601_step.zip": "SES/3D_Step_file_automatic_screwdriver_for_screws_SES1601_series.zip",
    "sem2001.pdf": "SEM/2D_pdf_automatic_nutrunner_SEM2001_series.pdf",
    "sem2001_step.zip": "SEM/3D_Step_file_SEM2001_automatic_nutrunner.zip",
    "sev2001.pdf": "SEV/automatic_screwdriver_for_screws_with_vacuum_unit_SEV2001_series.pdf",
    "sev2001_step.zip": "SEV/3D_Step_file_SEV2001_automatic_screwdriver_for_screws_with_vacuum_unit.zip",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(path.read_text()) == value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversion", type=Path, required=True)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--output_html", type=Path, required=True)
    args = parser.parse_args()
    conversion = json.loads(args.conversion.read_text())
    rendered = json.loads((args.frames / "render_audit.json").read_text())
    assert conversion["input_sha256_after"] == rendered["input_sha256_after"]
    for name, expected in conversion["input_sha256_after"].items():
        assert _sha((ROOT / name).read_bytes()) == expected, name
    models, images = {}, {}
    for row in rendered["frames"]:
        model = row["model"]
        source = next(item for item in conversion["sources"] if item["model"] == model)
        assert source["glb_sha256"] == row["source_glb_sha256"]
        display, image_rows = {}, {}
        for frame in row["frames"]:
            raw = (args.frames / frame["file"]).read_bytes()
            assert _sha(raw) == frame["sha256"]
            with Image.open(io.BytesIO(raw)) as picture:
                assert list(picture.size) == frame["pixels"] and picture.mode == "RGBA"
                encoded = io.BytesIO()
                picture.save(encoded, format="WEBP", lossless=True, method=6)
            webp = encoded.getvalue()
            metadata = {
                "pixels": frame["pixels"],
                "x_m": frame["x_m"],
                "png_sha256": frame["sha256"],
                "webp_sha256": _sha(webp),
                "webp_bytes": len(webp),
            }
            display[frame["view"]] = {
                **metadata,
                "data_url": "data:image/webp;base64," + base64.b64encode(webp).decode(),
            }
            image_rows[frame["view"]] = metadata
        span = max(source["extents_m"]) * 1000
        models[model] = {"longitudinal_span_mm": span, "frames": display}
        images[model] = {"longitudinal_span_mm": span, "frames": image_rows}
    template = ROOT / "scripts/hvjb_fastening_cad_v01.html"
    markup = template.read_text().replace("__MODEL_DATA__", json.dumps({"models": models}, separators=(",", ":")))
    assert "__MODEL_DATA__" not in markup and len(markup.encode()) < 1_000_000
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    with args.output_html.open("x") as stream:
        stream.write(markup)
    downloads = []
    for name, url in FILES.items():
        path = REFERENCE / name
        raw = path.read_bytes()
        downloads.append(
            {"file": str(path.relative_to(ROOT)), "url": DOWNLOAD + url, "bytes": len(raw), "sha256": _sha(raw)}
        )
    extra = REFERENCE / "additional_info_SES.pdf"
    downloads.append(
        {
            "file": str(extra.relative_to(ROOT)),
            "source": "ses1601_step.zip / additional_info_SES.pdf",
            "bytes": extra.stat().st_size,
            "sha256": _sha(extra.read_bytes()),
        }
    )
    record = {
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": "Manufacturer example CAD and equal-scale reference display; no installation or clearance measurement",
        "downloads": downloads,
        "conversion": conversion,
        "render": rendered,
        "images": images,
        "inline_html": {"path": str(args.output_html), "sha256": _sha(markup.encode()), "bytes": len(markup.encode())},
        "template_sha256": _sha(template.read_bytes()),
        "reference_material_colors": True,
        "image_encoding": "lossless WebP from saved RGBA PNG",
        "selected_tool_configuration": None,
        "real_cable_finished_diameter_m": None,
        "engagement_alignment": None,
        "complete_feed_hose_routing": None,
        "jaw_opening_geometry": None,
        "physical_acceptance_verdict": None,
    }
    for name, expected in conversion["input_sha256_after"].items():
        assert _sha((ROOT / name).read_bytes()) == expected, name
    destination = ROOT / "data/hvjb_fastening_cad_v01.json"
    _write_json(destination, record)
    print("FASTENING_CAD_REFERENCE_COMPLETE", destination, "html_bytes", len(markup.encode()), flush=True)


if __name__ == "__main__":
    main()
