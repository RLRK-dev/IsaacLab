# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read back saved tool envelopes and preserve input/artifact identities."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from build_hvjb_fastening_cad_reference_v01 import _write_json
from probe_hvjb_header_hand_access_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = [
    "analysis/hvjb_header_tool_envelope_v01.md",
    "data/hvjb_header_tool_envelope_v01.json",
    "data/hvjb_header_tool_envelope_display_v01.json",
    "scripts/probe_hvjb_header_tool_envelope_v01.py",
    "scripts/build_hvjb_header_tool_envelope_v01.py",
    "scripts/hvjb_header_tool_envelope_v01.html",
    "scripts/check_hvjb_header_tool_envelope_v01.mjs",
    "scripts/check_hvjb_header_tool_envelope_readback_v01.py",
    "audit/hvjb_header_tool_envelope_v01.json",
    "audit/hvjb_header_tool_envelope_v01_stdout.txt",
    "audit/hvjb_header_tool_envelope_figure_v01_stdout.txt",
    "audit/hvjb_header_tool_envelope_browser_v01.json",
    "audit/hvjb_header_tool_envelope_browser_v01_stdout.txt",
]


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def check_execution(record: dict, display: dict, browser: dict) -> None:
    assert record["script_sha256"] == digest(ROOT / "scripts/probe_hvjb_header_tool_envelope_v01.py")
    assert display["builder_sha256"] == digest(ROOT / "scripts/build_hvjb_header_tool_envelope_v01.py")
    assert display["template_sha256"] == digest(ROOT / "scripts/hvjb_header_tool_envelope_v01.html")
    assert display["record_sha256"] == browser["record_sha256"] == digest(ROOT / display["record"])
    assert browser["display_sha256"] == digest(ROOT / "data/hvjb_header_tool_envelope_display_v01.json")
    assert len(record["registration_comparisons"]) == browser["numeric_tool_comparisons"] == 1428
    assert len(browser["numeric_states"]) == 714 and len(browser["layout_states"]) == 336
    assert browser["javascript_errors"] == []
    logs = (
        ("audit/hvjb_header_tool_envelope_v01_stdout.txt", "HEADER_TOOL_ENVELOPE_COMPLETE"),
        ("audit/hvjb_header_tool_envelope_figure_v01_stdout.txt", "HEADER_TOOL_ENVELOPE_FIGURE_COMPLETE"),
        ("audit/hvjb_header_tool_envelope_browser_v01_stdout.txt", "HEADER_TOOL_ENVELOPE_BROWSER_OK"),
    )
    for name, marker in logs:
        text = (ROOT / name).read_text()
        assert marker in text and "Traceback" not in text and "AssertionError" not in text, name
    for name, expected in browser["screenshots"].items():
        assert digest(ROOT / "previews/hvjb_header_tool_envelope_browser_v01" / name) == expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists(), "Keep the previous readback"
    record = read_json("audit/hvjb_header_tool_envelope_v01.json")
    display = read_json("data/hvjb_header_tool_envelope_display_v01.json")
    browser = read_json("audit/hvjb_header_tool_envelope_browser_v01.json")
    pins = record["source_input_sha256_after"]
    actual = {name: digest(ROOT / name) for name in pins}
    assert actual == pins == record["source_input_sha256_before"] == display["source_input_sha256_after"]
    check_execution(record, display, browser)
    matrix_checks = {}
    for name, tool in record["tools"].items():
        matrix = np.asarray(tool["datum"]["source_to_query_matrix"])
        error = float(np.max(abs(matrix[:3, :3] @ matrix[:3, :3].T - np.eye(3))))
        determinant = float(np.linalg.det(matrix[:3, :3]))
        assert error < 1e-12 and abs(determinant - 1) < 1e-12
        assert tool["source_triangles"] == tool["source_triangles_observed"]
        matrix_checks[name] = {"orthogonality_residual": error, "determinant": determinant}
    tasks, selection = read_json("data/hvjb_task_occupancy_v01.json"), read_json("data/hvjb_robot_selection_v01.json")
    assert len(tasks["cards"]) == 20 and len(tasks["targets"]) == 92
    assert selection["selected_plan"] == "S5_AB"
    hand = read_json(record["settings"]["hand_observation"])
    assert sum(len(row["axes"]) for row in hand["models"]) == 14
    path = Path(display["output_html"])
    assert digest(path) == display["output_html_sha256"] and path.stat().st_size < 1_000_000
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "input_sha256_current": actual,
        "inputs_match": True,
        "artifacts_sha256": {name: digest(ROOT / name) for name in ARTIFACTS},
        "scripts_match_executed_versions": True,
        "matrix_checks": matrix_checks,
        "source_feature_count": len(tasks["targets"]),
        "workcard_count": len(tasks["cards"]),
        "selected_plan": selection["selected_plan"],
        "header_axis_count": 14,
        "numeric_tool_comparisons": 1428,
        "browser_layout_states": 336,
        "javascript_errors": 0,
        "visually_inspected_screenshots": [
            "736_light_P16_2_0.png",
            "320_dark_P16_2_40.png",
            "320_dark_P17_14_100.png",
        ],
        "diagram": {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size},
        "geometry_or_motion_modified": False,
        "native_opened": False,
        "native_saved": False,
        "selected_tool_configuration": None,
        "selected_axial_registration_m": None,
        "physical_acceptance_verdict": None,
    }
    _write_json(args.output_json, result)
    assert json.loads(args.output_json.read_text()) == result
    print("HEADER_TOOL_ENVELOPE_READBACK_COMPLETE", args.output_json, flush=True)


if __name__ == "__main__":
    main()
