# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerate conditional role-sharing conflicts without inventing a measured schedule."""

from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_robot_allocation_v01 import PINNED, validate

INPUT = "data/hvjb_robot_sharing_inputs_v01.json"
ALLOCATION = "data/hvjb_robot_allocation_v01.json"
WORK = "data/hvjb_task_occupancy_v01.json"
REPORT = "data/hvjb_robot_sharing_v01.json"
AUDIT = "audit/hvjb_robot_sharing_v01.json"
NOTES = "analysis/hvjb_robot_sharing_v01.md"
PAGE = "scripts/hvjb_robot_sharing_review_v01.html"
WORK_DIRECTORY = Path("/home/rlrk/Downloads/THREAD_HVJB_仕事と保持区間_v01_20260916")
WORK_FILES = (
    "review.html",
    "review_data.json",
    "allocation.json",
    "catalog.json",
    "process_v03.json",
    "notes.md",
    "audit.json",
    "仕事と保持区間.csv",
    "対象の照合先.csv",
)


def partitions(items: tuple) -> list[tuple]:
    """Enumerate all set partitions so no two-role sharing choice is silently omitted."""
    if not items:
        return [()]
    result = []
    for groups in partitions(items[1:]):
        result.append(((items[0],), *groups))
        for index, group in enumerate(groups):
            result.append((*groups[:index], (items[0], *group), *groups[index + 1 :]))
    return result


def canonical(groups: list | tuple) -> tuple:
    """Normalize partition ordering without changing its assignments."""
    return tuple(sorted(tuple(sorted(group)) for group in groups))


def sharing_scenarios(primary: list[str], assists: list[str], mapping: dict) -> list[dict]:
    """List role-ID duplicates for every auxiliary-role subset, with all main roles occupied."""
    rows = []
    for count in range(len(assists) + 1):
        for subset in itertools.combinations(assists, count):
            active = primary + list(subset)
            occupied = defaultdict(list)
            for role in active:
                occupied[mapping[role]].append(role)
            duplicates = {unit: roles for unit, roles in occupied.items() if len(roles) > 1}
            rows.append(
                {
                    "id": "".join(role[-1] for role in subset) or "NONE",
                    "active_assists": list(subset),
                    "active_roles": active,
                    "unit_assignments": dict(occupied),
                    "duplicate_assignments": duplicates,
                }
            )
    return rows


def build_plan(plan: dict, allocation: dict, work: dict, primary: list[str], assists: list[str]) -> dict:
    """Map each source task and continuous reservation into one candidate grouping."""
    mapping = {role: f"ARM_{role[-1]}" for role in primary}
    for index, group in enumerate(plan["assist_groups"], start=1):
        mapping.update({role: f"ASSIST_{index}" for role in group})
    mapped_tasks = []
    for task in allocation["tasks"]:
        row = {key: task[key] for key in ("id", "operation", "cell", "work_ja")}
        for field in ("primary", "other", "conditional"):
            row[field] = [{"role": role, "unit": mapping.get(role, role)} for role in task[field]]
            assert [item["role"] for item in row[field]] == task[field]
        mapped_tasks.append(row)
    exclusions = []
    for group in allocation["simultaneous_groups"]:
        units = [mapping.get(role, role) for role in group["distinct_resources"]]
        assert len(units) == len(set(units)), f"{plan['id']} merges roles in {group['id']}"
        exclusions.append(dict(group, mapped_distinct_units=units))
    reservations = [dict(row, mapped_unit=mapping[row["resource"]]) for row in work["cross_task_reservations"]]
    scenarios = sharing_scenarios(primary, assists, mapping)
    return dict(
        plan,
        role_to_unit=mapping,
        arm_slots=len(set(mapping.values())),
        tasks=mapped_tasks,
        source_simultaneous_groups=exclusions,
        cross_task_reservations=reservations,
        scenarios=scenarios,
        conflict_scenario_ids=[row["id"] for row in scenarios if row["duplicate_assignments"]],
    )


def prepare(inputs: dict, allocation: dict, work: dict) -> dict:
    """Check the five partitions, source preservation and conditional comparison scope."""
    validate(allocation, read_json(allocation["source_process"]))
    assert [row["task"] for row in work["cards"]] == allocation["tasks"]
    primary = [row["id"] for row in allocation["resources"] if row["category"] == "articulated_primary_slot"]
    assists = [row["id"] for row in allocation["resources"] if row["category"] == "unallocated_assist_role"]
    expected = {canonical(groups) for groups in partitions(tuple(assists))}
    provided = [canonical(plan["assist_groups"]) for plan in inputs["plans"]]
    assert len(provided) == len(set(provided)) and set(provided) == expected
    for plan in inputs["plans"]:
        flattened = [role for group in plan["assist_groups"] for role in group]
        assert sorted(flattened) == sorted(assists) and all(plan["assist_groups"])
    for key in ("selected_plan", "selected_robot_count", "minimum_robot_count", "physical_acceptance_verdict"):
        assert inputs[key] is None
    plans = [build_plan(plan, allocation, work, primary, assists) for plan in inputs["plans"]]
    return dict(
        inputs,
        revision="hvjb_robot_sharing_v01",
        observed_at=datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        primary_roles=primary,
        assist_roles=assists,
        plans=plans,
        resources=allocation["resources"],
        remaining_equipment=[row for row in allocation["resources"] if row["id"] not in primary + assists],
        accounting_fields=allocation["accounting_fields"],
        task_count=len(allocation["tasks"]),
        schedules_generated=False,
        time_values_s=None,
        extra_independent_roles=None,
    )


def write_csv(directory: Path, report: dict, work: dict) -> None:
    """Write the complete symbolic comparison and an unfilled measurement worksheet."""
    with (directory / "同時担当の比較.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["案", "腕枠数", "同時に必要な補助役", "重なる腕と役", "解釈"])
        for plan in report["plans"]:
            for row in plan["scenarios"]:
                writer.writerow(
                    [
                        plan["id"],
                        plan["arm_slots"],
                        "/".join(row["active_assists"]),
                        json.dumps(row["duplicate_assignments"], ensure_ascii=False),
                        "仮定した一場面のID照合。運転成立は未判定",
                    ]
                )
    with (directory / "兼務の確認入力.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "仕事ID",
                "仕事",
                "担当候補",
                "未確定の対象",
                "測定する役",
                "実接続ID",
                "開始イベント",
                "終了イベント",
                "把持開始から開放退避まで_s",
                "次役への手先交換_s",
                "次役への移動_s",
                "開始前待ち_s",
                "開始前の支持",
                "受け側支持と引継ぎ",
                "到達と全外形の確認",
                "必要な独立役の数",
                "測定根拠",
            ]
        )
        for card in work["cards"]:
            task = card["task"]
            candidates = task["primary"] + task["conditional"]
            writer.writerow([card["id"], task["work_ja"], "/".join(candidates), card["missing_ja"]] + [""] * 13)


def package(directory: Path, report: dict, work: dict) -> dict:
    """Create a new standalone comparison and preserve the preceding workcard review."""
    directory.mkdir(parents=True, exist_ok=False)
    write_new_json(directory / "review_data.json", report)
    payload = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    page = (ROOT / PAGE).read_text()
    assert page.count("__PAYLOAD__") == 1
    (directory / "review.html").write_text(page.replace("__PAYLOAD__", payload))
    shutil.copy2(ROOT / NOTES, directory / "notes.md")
    (directory / "workcards").mkdir()
    copied = {}
    for name in WORK_FILES:
        source = WORK_DIRECTORY / name
        before = digest(source)
        target = directory / "workcards" / name
        shutil.copy2(source, target)
        assert before == digest(source) == digest(target)
        copied[name] = before
    previous = json.loads((directory / "workcards" / "audit.json").read_text())
    assert copied["review.html"] == previous["page_sha256"]
    assert copied["review_data.json"] == digest(ROOT / WORK)
    write_csv(directory, report, work)
    return {
        "page_sha256": digest(directory / "review.html"),
        "copied_workcards_sha256": copied,
        "csv_sha256": {name: digest(directory / name) for name in ("同時担当の比較.csv", "兼務の確認入力.csv")},
    }


def main() -> None:
    """Publish conditional sharing alternatives while preserving the prior artifacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_ロボット共用比較_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists() and not any((ROOT / name).exists() for name in (REPORT, AUDIT))
    pinned = copy.deepcopy(PINNED)
    pinned.update(
        {
            ALLOCATION: "2e8516405684475d04fcf57938e7771c0283a5ab23cf482aa6fba4b718889dd9",
            WORK: "4da5b53687b05cd2cd1d294cf57121abde6ee9d04b19ed0a37ef2fb2a4d79df9",
        }
    )
    before = {name: digest(ROOT / name) for name in pinned}
    assert before == pinned, "Preserved input changed"
    before.update({name: digest(ROOT / name) for name in (INPUT, PAGE, NOTES)})
    work = read_json(WORK)
    report = prepare(read_json(INPUT), read_json(ALLOCATION), work)
    write_new_json(ROOT / REPORT, report)
    delivery = package(args.output_dir, report, work)
    after = {name: digest(ROOT / name) for name in before}
    assert before == after, "An input changed"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "report_sha256": digest(ROOT / REPORT),
        **delivery,
        "task_count_per_plan": report["task_count"],
        "scenario_count": sum(len(plan["scenarios"]) for plan in report["plans"]),
        "conflict_scenarios": {plan["id"]: plan["conflict_scenario_ids"] for plan in report["plans"]},
        "all_assist_partitions_included": True,
        "measured_cycle_or_physical_verdict": None,
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print(f"ROBOT_SHARING_OK plans={len(report['plans'])} cases={audit['scenario_count']} tasks_each=20", flush=True)
    print(json.dumps(audit["conflict_scenarios"]), flush=True)
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
