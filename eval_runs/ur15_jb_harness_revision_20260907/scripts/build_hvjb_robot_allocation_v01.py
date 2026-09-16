# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package task allocation and check references without claiming a minimum robot count."""

from __future__ import annotations

import argparse
import csv
import itertools
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json

INPUT = "data/hvjb_robot_allocation_v01.json"
NOTES = "analysis/cell_robot_allocation_v02.md"
AUDIT = "audit/hvjb_robot_allocation_v01.json"
PINNED = {
    "data/hvjb_preassembly_process_v03.json": "5e9d7078d4e7ff9772f8561788b29a34b28165e3118559385dcc78faf28b64e7",
    "data/hvjb_unitization_roles_v01.json": "7282ac79494d7704c7a88b48627b1d8cc72db0a883395d864ab1142454a3e802",
    "data/hand_provisional_spec_v01.json": "0ed18d28e261b73ae1fd3beb1686ad4c2b55071974d9b8708e358b79efa8b799",
    "data/hvjb_photo_correspondence_v03_p01.json": "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    "UR15_JB_photo_correspondence_v03_p03.blend": "5205d3aa2c2b99f7df6f538d17b3d3ca36ba8208c546858ee8ec8a5a3564a282",
}


def validate(report: dict, process: dict) -> dict:
    """Check task/resource references and record simultaneous-role exclusions, not physical feasibility."""
    resources = {row["id"]: row for row in report["resources"]}
    tasks = {row["id"]: row for row in report["tasks"]}
    operations = {row["id"]: row for row in process["operations"]}
    assert len(resources) == len(report["resources"]), "Duplicate resource IDs"
    assert len(tasks) == len(report["tasks"]), "Duplicate task IDs"
    assert {row["operation"] for row in tasks.values()} == set(operations), "Missing or invented operation"
    for row in tasks.values():
        assert row["cell"] == operations[row["operation"]]["cell"]
        assert row["primary"]
        listed = row["primary"] + row["other"] + row["conditional"]
        assert len(listed) == len(set(listed)) and set(listed) <= set(resources)
    exclusions = []
    for group in report["simultaneous_groups"]:
        assert group["tasks"] and set(group["tasks"]) <= set(tasks)
        roles = group["distinct_resources"]
        assert len(roles) == len(set(roles)) and set(roles) <= set(resources)
        for task_id in group["tasks"]:
            task = tasks[task_id]
            assert set(roles) <= set(task["primary"] + task["other"] + task["conditional"])
        for pair in itertools.combinations(roles, 2):
            exclusions.append({"roles": list(pair), "condition_ja": group["condition_ja"]})
    for candidate in report["sharing_candidates"]:
        assert set(candidate["resources"]) <= set(resources)
    for key in ("selected_robot_count", "minimum_robot_count", "task_durations_s", "target_cycle_s"):
        assert report[key] is None
    assert report["physical_acceptance_verdict"] is None
    roles = read_json("data/hvjb_unitization_roles_v01.json")
    overlap = [s["id"] for s in roles["states"] if {"panel_hand", "unit_hand"} <= set(s["active"])]
    return {
        "source_operation_ids": list(operations),
        "covered_operation_ids": sorted({row["operation"] for row in tasks.values()}),
        "task_count": len(tasks),
        "simultaneous_group_count": len(report["simultaneous_groups"]),
        "reference_integrity": True,
        "same_single_actuator_exclusions_during_overlap": exclusions,
        "unitization_panel_and_carry_role_overlap_states": overlap,
        "overlap_scope": "Only the prior 9 diagram states; not measured timing or physical handover",
        "primary_candidate_slots": [
            key for key, row in resources.items() if row["category"] == "articulated_primary_slot"
        ],
        "unallocated_assist_roles": [
            key for key, row in resources.items() if row["category"] == "unallocated_assist_role"
        ],
        "installed_robot_count": None,
        "minimum_robot_count": None,
        "source_video_timestamps_used_as_durations": False,
    }


def package(directory: Path, report: dict) -> list[dict]:
    """Create a new review folder with readable notes, full inputs and a task table."""
    directory.mkdir(parents=True, exist_ok=False)
    sources = {
        NOTES: "割当案.md",
        INPUT: "allocation.json",
        report["source_process"]: "process_v03.json",
        "data/hvjb_unitization_roles_v01.json": "unitization_roles.json",
    }
    copied = []
    for relative, target in sources.items():
        destination = directory / target
        shutil.copy2(ROOT / relative, destination)
        assert digest(ROOT / relative) == digest(destination)
        copied.append({"source": relative, "file": target, "sha256": digest(destination)})
    names = {row["id"]: row["name_ja"] for row in report["resources"]}
    with (directory / "仕事別割当.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["仕事ID", "工程ID", "セル", "仕事", "主担当", "別設備", "必要時の追加役", "兼務・集約の扱い"])
        for row in report["tasks"]:
            assignments = [
                " / ".join(f"{key}: {names[key]}" for key in row[field])
                for field in ("primary", "other", "conditional")
            ]
            writer.writerow([row["id"], row["operation"], row["cell"], row["work_ja"], *assignments, row["sharing_ja"]])
    return copied


def main() -> None:
    """Preserve source process and geometry while publishing the allocation comparison."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_ロボット集約案_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists() and not (ROOT / AUDIT).exists(), "Refusing to overwrite existing results"
    before = {relative: digest(ROOT / relative) for relative in PINNED}
    assert before == PINNED, "A pinned input changed"
    report = read_json(INPUT)
    process = read_json(report["source_process"])
    observations = validate(report, process)
    catalog = read_json("data/hvjb_photo_correspondence_v03_p01.json")
    assert all(catalog[key] == value for key, value in process["preserved_catalog_fields"].items())
    before.update({relative: digest(ROOT / relative) for relative in (INPUT, NOTES)})
    copied = package(args.output_dir, report)
    after = {relative: digest(ROOT / relative) for relative in before}
    assert before == after, "An input changed"
    audit = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "copied": copied,
        "task_csv_sha256": digest(args.output_dir / "仕事別割当.csv"),
        "observations": observations,
        "source_catalog_fields_preserved": True,
        "mechanism_or_motion_changed": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print(
        f"ROBOT_ALLOCATION_OK operations={len(observations['covered_operation_ids'])} "
        f"tasks={observations['task_count']} references_valid=True minimum_robot_count=unresolved",
        flush=True,
    )
    print(args.output_dir / "割当案.md", flush=True)


if __name__ == "__main__":
    main()
