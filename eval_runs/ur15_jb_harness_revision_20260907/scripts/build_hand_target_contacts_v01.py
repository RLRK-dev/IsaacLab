# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bundle an offline, photograph-based hand-interface review without model edits."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(data_path: Path, photo_directory: Path, current_pdf: Path, output_directory: Path) -> dict:
    """Package proposed contact interfaces and preserve image pixel coordinates."""
    data = json.loads(data_path.read_text())
    pdf_sha = _digest(current_pdf)
    if pdf_sha != data["sources"]["datasheet_sha256"]:
        raise ValueError("Public PDF differs from the recorded reference; review the source before using it.")
    photos = {}
    sources = []
    for name, source in data["photos"].items():
        path = photo_directory / source["file"]
        actual = _digest(path)
        if actual != source["sha256"]:
            raise ValueError(f"Photograph differs from the recorded source: {path}")
        photos[name] = "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        sources.append({"photo": name, "file": str(path), "url": source["url"], "sha256": actual})
    ids = [target["id"] for target in data["targets"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate contact target IDs")
    for target in data["targets"]:
        width, height = data["photos"][target["photo"]]["size_px"]
        for x, y, box_width, box_height in target["regions_px"]:
            if not (0 <= x < x + box_width <= width and 0 <= y < y + box_height <= height):
                raise ValueError(f"Photograph region is outside the original image: {target['id']}")
    template_path = Path(__file__).with_name("hand_target_contacts_viewer_v01.html")
    html = template_path.read_text().replace("__CONTACT_DATA__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__PHOTO_DATA__", json.dumps(photos))
    output_directory.mkdir(parents=True, exist_ok=False)
    page = output_directory / "把持対象対応_v01.html"
    page.write_text(html)
    (output_directory / "hand_target_contacts_v01.json").write_bytes(data_path.read_bytes())
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "scope": "public-source correspondence and proposed hand interfaces, no physical verdict",
        "source_photos": sources,
        "current_public_pdf": {"path": str(current_pdf), "sha256": pdf_sha, "matches_recorded_pdf": True},
        "data_sha256": _digest(data_path),
        "template_sha256": _digest(template_path),
        "page_sha256": _digest(page),
        "target_ids": ids,
        "image_regions_inside_source_bounds": True,
        "manufacturer_part_numbers_filled": [t["id"] for t in data["targets"] if t["part_number"] is not None],
        "physical_acceptance_verdict": None,
        "model_or_video_created": False,
    }
    (output_directory / "hand_target_contacts_sources_v01.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    return report


def main() -> None:
    """Read reference paths and create a new offline review folder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--photo_directory", type=Path, required=True)
    parser.add_argument("--current_pdf", type=Path, required=True)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.data, args.photo_directory, args.current_pdf, args.output_directory)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("HAND_TARGET_CONTACTS_REVIEW_CREATED")


if __name__ == "__main__":
    main()
