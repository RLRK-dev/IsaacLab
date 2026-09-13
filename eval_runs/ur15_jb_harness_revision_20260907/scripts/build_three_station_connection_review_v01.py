# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Package the proposed connection-group allocation across three stations."""

import argparse
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

from build_hand_function_review_v01 import file_sha256

REVISION = Path(__file__).resolve().parents[1]
CONFIG = "data/three_station_connection_groups_v01.json"
TEMPLATE = "scripts/three_station_connection_viewer_v01.html"
DOCUMENT = "analysis/three_station_connection_groups_v01.md"
PAGE = "3ST接続群分担_v01.html"


def check_transcription(config: dict) -> dict:
    """Check document identifiers and pin coverage, not electrical correctness."""
    stations = {station["id"] for station in config["station_candidates"]}
    groups = config["connection_groups"]
    if stations != {"A", "B", "C"} or len(groups) != 13 or len({group["id"] for group in groups}) != 13:
        raise ValueError("Expected three station candidates and thirteen distinct explanation groups")
    counts = Counter(group["station_candidate"] for group in groups)
    if counts != {"B": 3, "C": 10}:
        raise ValueError("Unexpected connection-group allocation")
    pins = [pin for group in groups for pin in group["lv_pins"]]
    if len(pins) != len(set(pins)) or sorted(pins + config["lv_reserved_pins"]) != list(range(1, 13)):
        raise ValueError("Duplicate or missing LV pin entry")
    if config["lv_reserved_pins"] != [6, 12]:
        raise ValueError("Reserved pins differ from the cited drawing")
    if any(group[key] is not None for group in groups for key in ("physical_cable_count", "fastener_count")):
        raise ValueError("Unpublished physical counts must remain unknown")
    if config["station_arm_counts_selected"] or config["physical_acceptance_verdict"] is not None:
        raise ValueError("This document does not select station hardware or judge physical validity")
    return {
        "station_candidates": sorted(stations),
        "explanation_group_counts": dict(counts),
        "lv_function_pins": sorted(pins),
        "lv_reserved_pins": config["lv_reserved_pins"],
        "physical_cable_and_fastener_counts_unknown": True,
        "scope": "document transcription and identifier checks only",
    }


def main() -> None:
    """Write a fresh offline page and render the cited PDF pages for inspection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    config = json.loads((REVISION / CONFIG).read_text())
    checks = check_transcription(config)
    sources = config["sources"]
    for key in ("pdf", "photo"):
        if file_sha256(REVISION / sources[key]) != sources[f"{key}_sha256"]:
            raise ValueError(f"Reference {key} SHA mismatch")
    paths = [
        CONFIG,
        TEMPLATE,
        DOCUMENT,
        "scripts/build_three_station_connection_review_v01.py",
        "scripts/build_hand_function_review_v01.py",
        sources["pdf"],
        sources["photo"],
        sources["prior_workflow"],
    ]
    before = {name: file_sha256(REVISION / name) for name in paths}
    template = (REVISION / TEMPLATE).read_text()
    if template.count("__REVIEW_DATA__") != 1:
        raise ValueError("Expected one data placeholder")
    output.mkdir(parents=True)
    for name in paths:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REVISION / name, destination)
    (output / "images").mkdir()
    command = [
        "pdftoppm",
        "-f",
        "2",
        "-l",
        "4",
        "-scale-to",
        "2200",
        "-png",
        str(output / sources["pdf"]),
        str(output / "images/ampere_reference"),
    ]
    rendered = subprocess.run(command, check=True, capture_output=True, text=True, timeout=90)
    illustrations = [f"images/ampere_reference-{page}.png" for page in (2, 3, 4)]
    if not all((output / name).is_file() for name in illustrations):
        raise RuntimeError("Missing rendered reference page")
    packed = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
    page = output / PAGE
    page.write_text(template.replace("__REVIEW_DATA__", packed))
    shutil.copy2(REVISION / DOCUMENT, output / "3ST接続群分担_v01.md")
    if before != {name: file_sha256(REVISION / name) for name in paths}:
        raise RuntimeError("Input changed during packaging")
    audit = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "input_sha256": before,
        "inputs_unchanged": True,
        "page_sha256": file_sha256(page),
        "reference_image_sha256": {name: file_sha256(output / name) for name in illustrations},
        "pdf_render_stdout": rendered.stdout,
        "pdf_render_stderr": rendered.stderr,
        "document_checks": checks,
        "station_allocation_is_proposed": True,
        "scene_loaded": False,
        "arm_motion_created": False,
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (output / "audit").mkdir()
    (output / "audit/three_station_connection_build_v01.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps({"page": str(page), "document_checks": checks}, ensure_ascii=False))
    print("THREE_STATION_CONNECTION_REVIEW_DONE")


if __name__ == "__main__":
    main()
