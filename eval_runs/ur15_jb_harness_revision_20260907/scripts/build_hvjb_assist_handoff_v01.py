# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Illustrate selected auxiliary-arm reservations using the preserved workcards."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_robot_sharing_v01 import WORK_DIRECTORY, WORK_FILES

STEM = "hvjb_assist_handoff_v01"
INPUT = "data/hvjb_assist_handoff_inputs_v01.json"
PAGE = "scripts/hvjb_assist_handoff_v01.html"
SELECTION = "data/hvjb_robot_selection_v01.json"
WORK = "data/hvjb_task_occupancy_v01.json"
PINNED = {
    SELECTION: "ad1d0fc6ad2f0c9d36f4d9839faf559ce80aa9ffb4965174facef944f1a58db8",
    WORK: "4da5b53687b05cd2cd1d294cf57121abde6ee9d04b19ed0a37ef2fb2a4d79df9",
}


def prepare(inputs: dict, selection: dict, work: dict) -> dict:
    """Map every existing auxiliary task and retain the original holding text."""
    assert selection["selected_plan"] == inputs["selected_plan"] == "S5_AB"
    cards = {row["id"]: row for row in work["cards"]}
    assert len(cards) == 20
    mapping = selection["role_to_unit"]
    groups = []
    for index, roles in enumerate(selection["assist_groups"], 1):
        rows = [card for card in cards.values() if set(card["task"]["conditional"]) & set(roles)]
        groups.append({"unit": f"ASSIST_{index}", "roles": roles, "cards": copy.deepcopy(rows)})
    assert [row["id"] for row in groups[0]["cards"]] == ["D11", "D12", "D21", "D22"]
    assert [row["id"] for row in groups[1]["cards"]] == [s["task"] for s in inputs["c_sequence"]]
    assert all(mapping[role] == group["unit"] for group in groups for role in group["roles"])
    assert len({p["id"] for p in inputs["phases"]}) == len(inputs["phases"]) == 7
    for phase in inputs["phases"]:
        assert phase["owner"] in (None, "first", "second")
        assert set(phase["source_tasks"]) <= set(cards)
    intervals = [{**copy.deepcopy(row), "unit": mapping[row["resource"]]} for row in work["cross_task_reservations"]]
    guide = next(row for row in intervals if row["resource"] == "X-C")
    assert guide["tasks"] == [s["task"] for s in inputs["c_sequence"] if s["continuity"] == "reserved_until_handoff"]
    report = copy.deepcopy(inputs)
    report.update(
        {
            "revision": STEM,
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "selection": selection,
            "assist_groups": groups,
            "cross_task_reservations": intervals,
            "all_tasks": [copy.deepcopy(card["task"]) for card in cards.values()],
            "source_rules_ja": work["rules_ja"],
        }
    )
    return report


def package(directory: Path, report: dict) -> dict:
    """Write diagrams and copy the unchanged task evidence into one local package."""
    directory.mkdir(parents=True, exist_ok=False)
    page = (ROOT / PAGE).read_text()
    assert page.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    (directory / "review.html").write_text(page.replace("__PAYLOAD__", payload))
    write_new_json(directory / "review_data.json", report)
    shutil.copy2(ROOT / SELECTION, directory / "selection.json")
    shutil.copy2(ROOT / f"analysis/{STEM}.md", directory / "notes.md")
    copies = {}
    (directory / "workcards").mkdir()
    for name in WORK_FILES:
        source, target = WORK_DIRECTORY / name, directory / "workcards" / name
        before = digest(source)
        shutil.copy2(source, target)
        assert before == digest(source) == digest(target)
        copies[name] = before
    assert copies["review_data.json"] == PINNED[WORK]
    with (directory / "補助腕の保持区間.csv").open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["腕", "仕事", "対象作業", "開始", "保持継続", "終了区切り", "共用時の注意", "未確定"])
        for group in report["assist_groups"]:
            for card in group["cards"]:
                writer.writerow(
                    [group["unit"], card["id"], card["task"]["work_ja"]]
                    + [card[key] for key in ("start_ja", "keep_ja", "end_ja", "reuse_ja", "missing_ja")]
                )
    return {"page_sha256": digest(directory / "review.html"), "copied_workcards_sha256": copies}


def main() -> None:
    """Publish an explanatory handoff view, without generating robot control."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_補助腕の保持と受渡し_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists()
    assert not any((ROOT / f"{folder}/{STEM}.json").exists() for folder in ("data", "audit"))
    before = {name: digest(ROOT / name) for name in PINNED}
    assert before == PINNED
    before.update({name: digest(ROOT / name) for name in (INPUT, PAGE, f"analysis/{STEM}.md")})
    report = prepare(read_json(INPUT), read_json(SELECTION), read_json(WORK))
    delivery = package(args.output_dir, report)
    after = {name: digest(ROOT / name) for name in before}
    assert before == after
    write_new_json(ROOT / f"data/{STEM}.json", report)
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "assist_task_counts": {g["unit"]: len(g["cards"]) for g in report["assist_groups"]},
        "all_task_count": len(report["all_tasks"]),
        "role_sequences_are_examples_not_timed_schedules": True,
        **delivery,
    }
    write_new_json(ROOT / f"audit/{STEM}.json", audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("ASSIST_HANDOFF_OK plan=S5_AB phases=7 assist_tasks=4/7 all_tasks=20 source_unchanged=True", flush=True)
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
