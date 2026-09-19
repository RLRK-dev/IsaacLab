# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back the separate SES 20 / SEV 20 source record without modifying saved geometry."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from analyze_hvjb_header_tool_configuration_v01 import ROOT, _read, _sha

SETTINGS = "data/hvjb_header_tool_tip_sources_v01.json"
ARTIFACTS = [
    SETTINGS,
    "analysis/hvjb_header_tool_tip_sources_v01.md",
    "scripts/check_hvjb_header_tool_tip_sources_v01.py",
]


def _protected(settings: dict) -> dict[str, str]:
    previous = _read(settings["previous_readback"])
    expected = previous["input_sha256_current"].copy()
    for path, value in previous["artifacts_sha256"].items():
        assert path not in expected or expected[path] == value, path
        expected[path] = value
    expected[settings["previous_readback"]] = _sha(settings["previous_readback"])
    for source in settings["sources"]:
        path, value = source["file"], source["sha256"]
        assert path not in expected or expected[path] == value, path
        expected[path] = value
    actual = {path: _sha(path) for path in expected}
    assert actual == expected, [path for path in expected if actual[path] != expected[path]]
    return actual


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists(), "Preserve previous source readback"
    settings = _read(SETTINGS)
    before = _protected(settings)
    sources = {row["id"]: row for row in settings["sources"]}
    assert len(sources) == len(settings["sources"]) == 3
    derived_files = []
    for key in ("SES20_581105", "SEV20_581145"):
        source = sources[key]
        assert (ROOT / source["file"]).read_bytes().startswith(b"%PDF-")
        assert source["pages_visually_read"] == [1, 2]
        text = (ROOT / source["text_extract"]).read_text()
        assert source["printed_model"] in text and source["drawing_number"] in text
        derived_files.extend([source["text_extract"], *source["page_images"]])
    assert all(value is None for key, value in settings["handoff_to_configuration"].items() if not key.endswith("_ja"))
    assert settings["physical_acceptance_verdict"] is None and not settings["geometry_or_motion_modified"]
    tasks = _read("data/hvjb_task_occupancy_v01.json")
    selection = _read("data/hvjb_robot_selection_v01.json")
    hand = _read("audit/hvjb_header_hand_access_v01.json")
    assert len(tasks["cards"]) == 20 and len(tasks["targets"]) == 92
    assert selection["selected_plan"] == "S5_AB"
    assert sum(len(row["axes"]) for row in hand["models"]) == 14
    after = {path: _sha(path) for path in before}
    assert before == after
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "input_sha256_before": before,
        "input_sha256_current": after,
        "inputs_match": True,
        "artifacts_sha256": {path: _sha(path) for path in ARTIFACTS},
        "source_derivatives_sha256": {path: _sha(path) for path in derived_files},
        "manually_inspected_pdf_pages": {
            key: sources[key]["pages_visually_read"] for key in sources if key != "PRODUCT_OVERVIEW"
        },
        "manual_scope": (
            "Page inspection was performed by the executor; this script checks identity, not dimension interpretation"
        ),
        "workcard_count": len(tasks["cards"]),
        "source_feature_count": len(tasks["targets"]),
        "selected_plan": selection["selected_plan"],
        "header_axis_count": 14,
        "geometry_or_motion_modified": False,
        "native_opened": False,
        "native_saved": False,
        "selected_tool_configuration": None,
        "selected_axial_registration_m": None,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == result
    print(f"Protected inputs unchanged: {len(before)}; preserved: S5_AB / 20 cards / 92 targets / 14 axes")
    print("Separate new drawing sources: SES 20 581105 / SEV 20 581145; selected configuration/TCP: null")
    print("HEADER_TOOL_TIP_SOURCES_READBACK_COMPLETE", args.output_json, flush=True)


if __name__ == "__main__":
    main()
