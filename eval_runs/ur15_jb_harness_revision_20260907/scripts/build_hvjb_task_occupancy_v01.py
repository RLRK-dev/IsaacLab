# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Publish target traceability and holding workcards without calculating robot counts."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import FEATURE_COLLECTIONS, ROOT, digest, read_json, write_new_json
from build_hvjb_robot_allocation_v01 import PINNED, validate

INPUT = "data/hvjb_task_occupancy_inputs_v01.json"
ALLOCATION = "data/hvjb_robot_allocation_v01.json"
CATALOG = "data/hvjb_photo_correspondence_v03_p01.json"
REPORT = "data/hvjb_task_occupancy_v01.json"
AUDIT = "audit/hvjb_task_occupancy_v01.json"
PAGE = "scripts/hvjb_task_occupancy_review_v01.html"


def target_rows(inputs: dict, process: dict, catalog: dict) -> list[dict]:
    """Keep every observed feature, its unresolved interfaces and candidate review destinations."""
    correspondence = {row["id"]: row for row in process["feature_correspondence"]}
    assert set(inputs["group_review_tasks"]) == {row["group"] for row in correspondence.values()}
    rows = []
    for collection in FEATURE_COLLECTIONS:
        for source in catalog[collection]:
            record = copy.deepcopy(correspondence[source["id"]])
            group = record["group"]
            review = inputs["group_review_tasks"][group]
            parent = source.get("feature_parent")
            if parent:
                parent_group = correspondence[parent]["group"]
                review = inputs["fastener_parent_review_tasks"].get(parent_group, review)
            record.update(
                {
                    "collection": collection,
                    "review_task_ids": review,
                    "selected_task_id": None,
                    "feature_parent": parent,
                    "observed_trace_ends": source.get("observed_trace_ends", []),
                    "physical_endpoints": source.get("physical_endpoints"),
                    "electrical_group": source.get("electrical_group"),
                    "joint_stack": source.get("joint_stack"),
                    "fastener_specification": source.get("fastener_specification"),
                    "model_id": source["model_id"],
                }
            )
            rows.append(record)
    assert len(rows) == len(correspondence) == len({row["id"] for row in rows})
    return rows


def prepare(inputs: dict, allocation: dict, process: dict, catalog: dict) -> dict:
    """Cross-check existing roles and prepare the non-timed review data."""
    allocation_checks = validate(allocation, process)
    tasks = {row["id"]: row for row in allocation["tasks"]}
    hands = read_json("data/hand_provisional_spec_v01.json")["profiles"]
    hand_ids = {row["id"] for row in hands}
    entities = {row["id"]: row for row in process["observed_entities"]}
    cards = inputs["task_cards"]
    assert len(cards) == len(tasks) and {row["id"] for row in cards} == set(tasks)
    targets = target_rows(inputs, process, catalog)
    for row in targets:
        assert row["review_task_ids"] and set(row["review_task_ids"]) <= set(tasks)
        assert row["selected_task_id"] is None and row["physical_operation_selected"] is None
    for card in cards:
        assert set(card["hands"]) <= hand_ids and set(card["entities"]) <= set(entities)
        for key in ("start_ja", "keep_ja", "end_ja", "reuse_ja", "missing_ja"):
            assert card[key]
    for reservation in inputs["cross_task_reservations"]:
        for task_id in reservation["tasks"]:
            task = tasks[task_id]
            assert reservation["resource"] in task["primary"] + task["other"] + task["conditional"]
    headers = []
    for identifier in ("P16", "P17"):
        mounting = copy.deepcopy(catalog["documented_header_mounting"][identifier])
        headers.append(
            {
                "feature_id": identifier,
                "task_id": "D50",
                "mounting": mounting,
                "holding_role": "R-C",
                "tool_role": "T-C",
                "hand_candidate": "H05",
                "hole_order": None,
                "fastening_conditions": None,
                "duration_s": None,
                "note_ja": "一つのヘッダーを締結・工具退避まで保持する比較。穴数は動作時間や工具台数ではない。",
            }
        )
    assert catalog["lv_pin_map"]["6"] == catalog["lv_pin_map"]["12"] == "Reserved"
    assert all(catalog[key] == value for key, value in process["preserved_catalog_fields"].items())
    return {
        "revision": "hvjb_task_occupancy_v01",
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "scope_ja": inputs["scope_ja"],
        "rules_ja": inputs["rules_ja"],
        "resources": allocation["resources"],
        "hands": hands,
        "cards": [dict(card, task=tasks[card["id"]]) for card in cards],
        "targets": targets,
        "observed_entities": list(entities.values()),
        "header_jobs": headers,
        "cross_task_reservations": inputs["cross_task_reservations"],
        "simultaneous_groups": allocation["simultaneous_groups"],
        "sharing_candidates": allocation["sharing_candidates"],
        "required_functions": catalog["required_functions"],
        "electrical_groups": catalog["electrical_groups"],
        "lv_pin_map": catalog["lv_pin_map"],
        "assembly_dependencies": catalog["assembly_dependencies"],
        "process_precedence": process["process_precedence"],
        "allocation_checks": allocation_checks,
        "task_durations_s": None,
        "minimum_robot_count": None,
        "physical_acceptance_verdict": None,
    }


def csv_files(directory: Path, report: dict) -> dict:
    """Export task occupancy and individual source-feature review destinations."""
    cards = directory / "仕事と保持区間.csv"
    with cards.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "仕事ID",
                "セル",
                "仕事",
                "主担当",
                "追加役候補",
                "開始",
                "占有継続",
                "担当を終える区切り",
                "兼務候補",
                "未確定",
            ]
        )
        for row in report["cards"]:
            task = row["task"]
            writer.writerow(
                [row["id"], task["cell"], task["work_ja"], "/".join(task["primary"]), "/".join(task["conditional"])]
                + [row[key] for key in ("start_ja", "keep_ja", "end_ja", "reuse_ja", "missing_ja")]
            )
    features = directory / "対象の照合先.csv"
    with features.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["特徴ID", "対象", "種別", "写真上の親", "照合する仕事の候補", "採用した物理作業", "未確定"])
        for row in report["targets"]:
            writer.writerow(
                [
                    row["id"],
                    row["name_ja"],
                    row["collection"],
                    row["feature_parent"],
                    "/".join(row["review_task_ids"]),
                    "未確定",
                    row["unresolved_ja"],
                ]
            )
    return {file.name: digest(file) for file in (cards, features)}


def package(directory: Path, report: dict) -> dict:
    """Build a standalone local review with complete source records beside it."""
    directory.mkdir(parents=True, exist_ok=False)
    write_new_json(directory / "review_data.json", report)
    page = (ROOT / PAGE).read_text()
    assert page.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    (directory / "review.html").write_text(page.replace("__PAYLOAD__", payload))
    copies = {
        INPUT: "workcard_inputs.json",
        ALLOCATION: "allocation.json",
        CATALOG: "catalog.json",
        "data/hvjb_preassembly_process_v03.json": "process_v03.json",
        "analysis/hvjb_task_occupancy_v01.md": "notes.md",
    }
    for relative, name in copies.items():
        shutil.copy2(ROOT / relative, directory / name)
        assert digest(ROOT / relative) == digest(directory / name)
    return {"csv_sha256": csv_files(directory, report), "page_sha256": digest(directory / "review.html")}


def main() -> None:
    """Validate preserved inputs and publish the new task review without overwriting artifacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_仕事と保持区間_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists() and not any((ROOT / name).exists() for name in (REPORT, AUDIT))
    pinned = dict(PINNED, **{ALLOCATION: "2e8516405684475d04fcf57938e7771c0283a5ab23cf482aa6fba4b718889dd9"})
    before = {name: digest(ROOT / name) for name in pinned}
    assert before == pinned, "Preserved input identity changed"
    before.update({name: digest(ROOT / name) for name in (INPUT, PAGE, "analysis/hvjb_task_occupancy_v01.md")})
    allocation = read_json(ALLOCATION)
    report = prepare(read_json(INPUT), allocation, read_json(allocation["source_process"]), read_json(CATALOG))
    write_new_json(ROOT / REPORT, report)
    delivery = package(args.output_dir, report)
    after = {name: digest(ROOT / name) for name in before}
    assert before == after, "A source changed while packaging"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "report_sha256": digest(ROOT / REPORT),
        **delivery,
        "task_count": len(report["cards"]),
        "source_feature_count": len(report["targets"]),
        "required_function_count": len(report["required_functions"]),
        "electrical_group_count": len(report["electrical_groups"]),
        "header_documented_holes": {row["feature_id"]: row["mounting"]["hole_count"] for row in report["header_jobs"]},
        "source_reference_checks": "passed; not completeness of a manufacturing BOM or schedule",
        "motion_created": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print(
        f"TASK_OCCUPANCY_OK tasks={audit['task_count']} features={audit['source_feature_count']} "
        f"functions={audit['required_function_count']} electrical_groups={audit['electrical_group_count']} "
        f"header_holes={audit['header_documented_holes']} timing=unresolved",
        flush=True,
    )
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
