# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Map receiving-support examples to the selected arms without asserting physical support."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_assist_handoff_v01 import PINNED, SELECTION, WORK
from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_robot_sharing_v01 import WORK_DIRECTORY, WORK_FILES

STEM = "hvjb_receiving_support_v01"
INPUT = "data/hvjb_receiving_support_inputs_v01.json"
PAGE = f"scripts/{STEM}.html"
SUPPORT = "data/hvjb_unitization_roles_v01.json"


def observe_assignments(state: dict, arms: set[str]) -> dict:
    """Count missing and duplicate independent assignments, not forces or motion."""
    assigned = defaultdict(list)
    for target, owners in state["owners"].items():
        assert len(owners) == len(set(owners)), "Duplicate owner within one object"
        for actor in owners:
            assert actor in arms | {"F-C"}
            assigned[actor].append(target)
    duplicates = {actor: targets for actor, targets in assigned.items() if actor in arms and len(targets) > 1}
    assert set(state["busy_nonholding"]) <= arms - set(assigned)
    return {
        "assigned_objects": dict(assigned),
        "unassigned_targets": [target for target, owners in state["owners"].items() if not owners],
        "duplicate_independent_arm_roles": duplicates,
        "holding_arms": sorted(arms & set(assigned)),
        "shared_assistant_reserved": "ASSIST_1" in assigned or "ASSIST_1" in state["busy_nonholding"],
    }


def prepare(inputs: dict, selection: dict, work: dict, support: dict) -> dict:
    """Retain selected identities and distinguish examples from diagnostic counterexamples."""
    assert inputs["selected_plan"] == selection["selected_plan"] == "S5_AB"
    arms = set(selection["role_to_unit"].values())
    assert len(arms) == 5
    objects = {item["id"] for item in inputs["objects"]}
    cards = {item["id"]: item for item in work["cards"]}
    assert len(cards) == 20
    report = copy.deepcopy(inputs)
    assert len({s["id"] for s in report["states"]}) == len(report["states"]) == 8
    for state in report["states"]:
        assert set(state["owners"]) <= objects
        assert set(state["source_tasks"]) <= set(cards)
        state["observations"] = observe_assignments(state, arms)
        if state["type"] != "diagnostic_counterexample":
            assert not state["observations"]["unassigned_targets"]
            assert not state["observations"]["duplicate_independent_arm_roles"]
    by_id = {state["id"]: state for state in report["states"]}
    assert by_id["B_DOUBLE"]["observations"]["duplicate_independent_arm_roles"] == {"ASSIST_2": ["A_END", "B_END"]}
    assert by_id["B_DROP"]["observations"]["unassigned_targets"] == ["B_END"]
    assert by_id["B_KEEP"]["observations"]["holding_arms"] == ["ARM_C", "ASSIST_1", "ASSIST_2"]
    assert by_id["A_RETREAT"]["observations"]["shared_assistant_reserved"]
    report.update(
        {
            "revision": STEM,
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "selection": selection,
            "source_cards": [copy.deepcopy(cards[key]) for key in ("D12", "D22", "D30")],
            "source_interfaces": support["interfaces"],
            "all_source_task_ids": list(cards),
            "observation_scope_ja": "担当表の空欄・独立役の重複。実機把持、荷重支持、到達、周期の判定ではない。",
        }
    )
    return report


def package(directory: Path, report: dict) -> dict:
    """Bundle the new view and preserved source evidence in a new directory."""
    directory.mkdir(parents=True, exist_ok=False)
    page = (ROOT / PAGE).read_text()
    assert page.count("__PAYLOAD__") == 1
    (directory / "review.html").write_text(
        page.replace("__PAYLOAD__", json.dumps(report, ensure_ascii=False).replace("</", "<\\/"))
    )
    write_new_json(directory / "review_data.json", report)
    shutil.copy2(ROOT / f"analysis/{STEM}.md", directory / "notes.md")
    shutil.copy2(ROOT / SELECTION, directory / "selection.json")
    (directory / "workcards").mkdir()
    copies = {}
    for name in WORK_FILES:
        source, target = WORK_DIRECTORY / name, directory / "workcards" / name
        before = digest(source)
        shutil.copy2(source, target)
        assert before == digest(source) == digest(target)
        copies[name] = before
    assert copies["review_data.json"] == PINNED[WORK]
    return {"page_sha256": digest(directory / "review.html"), "copied_workcards_sha256": copies}


def main() -> None:
    """Publish role-accounting examples for the C receiving interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_C側の受渡し_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists()
    assert not any((ROOT / f"{folder}/{STEM}.json").exists() for folder in ("data", "audit"))
    pins = {**PINNED, SUPPORT: "7282ac79494d7704c7a88b48627b1d8cc72db0a883395d864ab1142454a3e802"}
    before = {name: digest(ROOT / name) for name in pins}
    assert before == pins
    before.update({name: digest(ROOT / name) for name in (INPUT, PAGE, f"analysis/{STEM}.md")})
    report = prepare(read_json(INPUT), read_json(SELECTION), read_json(WORK), read_json(SUPPORT))
    delivery = package(args.output_dir, report)
    after = {name: digest(ROOT / name) for name in before}
    assert before == after
    write_new_json(ROOT / f"data/{STEM}.json", report)
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "states": {state["id"]: state["observations"] for state in report["states"]},
        "source_task_count": len(report["all_source_task_ids"]),
        **delivery,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / f"audit/{STEM}.json", audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("RECEIVING_SUPPORT_OK states=8 selected_arms=5 source_tasks=20 bookkeeping_only=True", flush=True)
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
