# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package late connection observations and an unselected holding-role comparison."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_assist_handoff_v01 import PINNED as ROLE_PINNED
from build_hvjb_assist_handoff_v01 import SELECTION, WORK
from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_unitization_review_v01 import PINNED, PROCESS, inspect_export

STEM = "hvjb_final_connection_v01"
INPUT = "data/hvjb_final_connection_inputs_v01.json"
EVIDENCE = "data/hvjb_final_connection_evidence_v01.json"
CATALOG = "data/hvjb_photo_correspondence_v03_p01.json"
PAGE = f"scripts/{STEM}.html"


def validate_observations(report: dict) -> None:
    """Check image locations [px] without assigning hidden wire or bolt identities."""
    views = {view["id"]: view for view in report["views"]}
    assert len(views) == 7 and len(report["frames"]) == 17
    for view in views.values():
        width, height = view["frame"]["size_px"]
        x, y, w, h = view["focus_px"]
        assert 0 <= x < x + w <= width and 0 <= y < y + h <= height
        for marker in view["markers"]:
            assert all(0 <= p < n for p, n in zip(marker["xy_px"], [width, height], strict=True))
    joints = report["joint_observations"]
    assert [joint["id"] for joint in joints] == ["J1", "J2", "J3"]
    for joint in joints:
        assert joint["id"] in {marker["id"] for marker in views[joint["view"]]["markers"]}
        for key in (
            "physical_wire_ids",
            "electrical_group_ids",
            "photo_feature_ids",
            "complete_joint_stack",
            "fastener_count",
            "release_condition",
        ):
            assert joint[key] is None
    assert report["holding_comparison"]["task"] == "D60"
    assert report["holding_comparison"]["status"] == "unselected_role_comparison_not_controller"
    assert [role["id"] for role in report["holding_comparison"]["roles"]] == [
        "ARM_C",
        "ASSIST_2",
        "ASSIST_1",
        "T-C",
    ]
    assert not report["complete_wire_inventory"] and not report["confirmed_video_to_photo_wires"]
    assert not report["selected_grasp_poses"] and report["acceptance_thresholds"] is None
    assert report["physical_acceptance_verdict"] is None


def prepare() -> tuple[dict, dict]:
    """Read original frames and preserve all catalog fields and source workcards."""
    pins = {
        **PINNED,
        **ROLE_PINNED,
        EVIDENCE: "d9381d8c9080331793e8e5e9c0e388306379ef777b9fb5e48904c8dd21993b79",
    }
    before = {path: digest(ROOT / path) for path in pins}
    assert before == pins, "A pinned input changed"
    report, evidence = copy.deepcopy(read_json(INPUT)), read_json(EVIDENCE)
    report["source"] = evidence["source"]
    source = report["source"]
    before[source["file"]] = digest(ROOT / source["file"])
    assert before[source["file"]] == source["sha256"]
    report["frames"] = copy.deepcopy(evidence["frames"])
    for frame in report["frames"]:
        before[frame["file"]] = digest(ROOT / frame["file"])
        assert before[frame["file"]] == frame["sha256"]
        frame["local_image"] = "evidence/" + Path(frame["file"]).name
    for view in report["views"]:
        view["frame"] = next(f for f in report["frames"] if f["requested_seek_s"] == view["second"])
    validate_observations(report)
    report["selection"] = read_json(SELECTION)
    assert report["selected_arm_count"] == report["selection"]["selected_assembly_arm_count"] == 5
    assert report["selected_plan"] == report["selection"]["selected_plan"] == "S5_AB"
    report["all_source_task_ids"] = [row["id"] for row in read_json(WORK)["cards"]]
    catalog, process = read_json(CATALOG), read_json(PROCESS)
    assert all(catalog[key] == value for key, value in process["preserved_catalog_fields"].items())
    report["preserved_counts"] = {
        "photo_features": inspect_export()["export_feature_count"],
        "required_functions": len(catalog["required_functions"]),
        "electrical_groups": len(catalog["electrical_groups"]),
        "lv_pins": len(catalog["lv_pin_map"]),
        "source_tasks": len(set(report["all_source_task_ids"])),
    }
    assert list(report["preserved_counts"].values()) == [92, 17, 13, 12, 20]
    for path in (INPUT, PAGE, f"analysis/{STEM}.md"):
        before[path] = digest(ROOT / path)
    report["revision"] = STEM
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    return report, before


def package(directory: Path, report: dict) -> dict:
    """Create an offline page with unchanged source images and complete workcards."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    paths = {frame["file"]: frame["local_image"] for frame in report["frames"]}
    paths.update(
        {
            CATALOG: "catalog.json",
            WORK: "all_workcards.json",
            SELECTION: "selection.json",
            EVIDENCE: "evidence_index.json",
            "data/hand_provisional_spec_v01.json": "hand_families.json",
            f"analysis/{STEM}.md": "notes.md",
        }
    )
    copied = {}
    for relative, target in paths.items():
        shutil.copy2(ROOT / relative, directory / target)
        assert digest(ROOT / relative) == digest(directory / target)
        copied[target] = digest(directory / target)
    write_new_json(directory / "review_data.json", report)
    template = (ROOT / PAGE).read_text()
    assert template.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False).replace("<", "\\u003c")
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    return {"copied_sha256": copied, "page_sha256": digest(directory / "review.html")}


def main() -> None:
    """Publish source observations without changing native scenes or robot motion."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_最終接続と保持_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists()
    assert not any((ROOT / f"{folder}/{STEM}.json").exists() for folder in ("data", "audit"))
    report, before = prepare()
    packaged = package(args.output_dir, report)
    after = {path: digest(ROOT / path) for path in before}
    assert before == after, "Source changed during packaging"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        **packaged,
        "preserved_counts": report["preserved_counts"],
        "observed_joint_locations": len(report["joint_observations"]),
        "complete_wire_inventory": False,
        "final_individual_connections_resolved": False,
        "assistant_release_instant_resolved": False,
        "holding_comparison_selected": False,
        "model_written": False,
        "movie_created": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / f"data/{STEM}.json", report)
    write_new_json(ROOT / f"audit/{STEM}.json", audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("FINAL_CONNECTION_OK views=7 joint_locations=3 frames=17 selected_arms=5 source_tasks=20 unchanged=True")
    print(args.output_dir / "review.html")


if __name__ == "__main__":
    main()
