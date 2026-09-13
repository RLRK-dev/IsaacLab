# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Update the photograph-based hand roles for same-station held fastening."""

import argparse
import base64
import json
import shutil
from datetime import datetime
from pathlib import Path

from build_hand_function_review_v01 import file_sha256

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "data/hand_target_contacts_v02.json"
PRIOR = "data/hand_target_contacts_v01.json"
TEMPLATE = "scripts/hand_target_contacts_viewer_v02.html"
DOCUMENT = "analysis/hand_target_contacts_v02.md"
PAGE = "ハンド役割・把持対象対応_v02.html"
REFERENCE = "references/op040_real_products_20260912"


def check_records(data: dict, previous: dict, allocation: dict) -> dict:
    """Check references and unchanged photo annotations, not grasp capability."""
    targets = data["targets"]
    ids = [target["id"] for target in targets]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate target ID")
    previous_by_id = {target["id"]: target for target in previous["targets"]}
    cases = {case["id"] for case in data["operation_cases"]}
    stations = {station["id"] for station in allocation["station_candidates"]}
    prior_ids = []
    for target in targets:
        if not set(target["station_candidates"]) <= stations:
            raise ValueError(f"Unknown station: {target['id']}")
        if not set(target["operation_case_examples"]) <= cases:
            raise ValueError(f"Unknown operation case: {target['id']}")
        width, height = data["photos"][target["photo"]]["size_px"]
        for x, y, box_width, box_height in target["regions_px"]:
            if not (0 <= x < x + box_width <= width and 0 <= y < y + box_height <= height):
                raise ValueError(f"Photo rectangle outside source: {target['id']}")
        if target["legacy_id"]:
            prior = previous_by_id[target["legacy_id"]]
            if target["photo"] != prior["photo"] or target["regions_px"] != prior["regions_px"]:
                raise ValueError("Historical photo annotation changed")
            prior_ids.append(target["legacy_id"])
        if any(target[key] is not None for key in ("part_number", "manufacturing_dimensions_m", "required_force_n")):
            raise ValueError("This revision must not fill unpublished specifications")
    if set(prior_ids) != set(previous_by_id) or len(prior_ids) != len(previous_by_id):
        raise ValueError("Historical target correspondence is incomplete")
    return {
        "target_ids": ids,
        "prior_target_ids_preserved": prior_ids,
        "photo_rectangles_unchanged_for_prior_targets": True,
        "unlocated_target_ids": [target["id"] for target in targets if not target["regions_px"]],
        "station_candidate_targets": {
            station: [target["id"] for target in targets if station in target["station_candidates"]]
            for station in sorted(stations)
        },
        "operation_case_ids": sorted(cases),
        "unpublished_part_dimensions_and_force_remain_null": True,
        "scope": "document references and pixel bounds only",
    }


def main() -> None:
    """Build a fresh self-contained review package from existing references."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    data = json.loads((ROOT / CONFIG).read_text())
    if file_sha256(ROOT / data["allocation_source"]) != data["allocation_source_sha256"]:
        raise ValueError("Three-station proposal changed; review its mapping first")
    allocation = json.loads((ROOT / data["allocation_source"]).read_text())
    previous = json.loads((ROOT / PRIOR).read_text())
    observations = check_records(data, previous, allocation)
    pdf = f"{REFERENCE}/ampere_hvjb_5_400_current_v1_1.pdf"
    if file_sha256(ROOT / pdf) != data["sources"]["datasheet_sha256"]:
        raise ValueError("Public reference PDF changed")
    paths = [
        CONFIG,
        PRIOR,
        TEMPLATE,
        DOCUMENT,
        data["allocation_source"],
        data["sources"]["received_g3_g4"],
        pdf,
        "data/hand_held_fastening_v01.json",
        "analysis/three_station_connection_groups_v01.md",
        "scripts/build_hand_target_contacts_v02.py",
        "scripts/build_hand_function_review_v01.py",
    ]
    photos = {}
    for key, source in data["photos"].items():
        name = f"{REFERENCE}/{source['file']}"
        if file_sha256(ROOT / name) != source["sha256"]:
            raise ValueError(f"Public photo changed: {name}")
        paths.append(name)
        photos[key] = "data:image/jpeg;base64," + base64.b64encode((ROOT / name).read_bytes()).decode("ascii")
    before = {name: file_sha256(ROOT / name) for name in paths}
    template = (ROOT / TEMPLATE).read_text()
    if template.count("__CONTACT_DATA__") != 1 or template.count("__PHOTO_DATA__") != 1:
        raise ValueError("Expected one placeholder for each data payload")
    output.mkdir(parents=True)
    for name in paths:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    packed = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    page = output / PAGE
    page.write_text(template.replace("__CONTACT_DATA__", packed).replace("__PHOTO_DATA__", json.dumps(photos)))
    shutil.copy2(ROOT / DOCUMENT, output / "ハンド役割・把持対象対応_v02.md")
    if before != {name: file_sha256(ROOT / name) for name in paths}:
        raise RuntimeError("Source changed during packaging")
    audit = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "input_sha256": before,
        "inputs_unchanged": True,
        "page_sha256": file_sha256(page),
        "document_observations": observations,
        "arm_motion_created": False,
        "physical_acceptance_verdict": None,
    }
    (output / "audit").mkdir()
    (output / "audit/hand_target_contacts_build_v02.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps({"page": str(page), "document_observations": observations}, ensure_ascii=False))
    print("HAND_TARGET_CONTACTS_V02_CREATED")


if __name__ == "__main__":
    main()
