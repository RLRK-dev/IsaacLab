# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Illustrate the existing sharing alternatives without changing the allocation."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_robot_sharing_v01 import REPORT, WORK_FILES

PAGE = "scripts/hvjb_robot_diagram_v02.html"
AUDIT = "audit/hvjb_robot_diagram_v02.json"
PREVIOUS = Path("/home/rlrk/Downloads/THREAD_HVJB_ロボット共用比較_v01_20260916")
DETAIL_FILES = ("review.html", "review_data.json", "notes.md", "同時担当の比較.csv", "兼務の確認入力.csv", "audit.json")


def main() -> None:
    """Package a new diagram page with an unchanged copy of its source comparison."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_ロボット分担図_v02_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists() and not (ROOT / AUDIT).exists(), "Output already exists"
    source_audit = read_json("audit/hvjb_robot_sharing_v01.json")
    assert digest(ROOT / REPORT) == source_audit["report_sha256"] == digest(PREVIOUS / "review_data.json")
    assert digest(PREVIOUS / "review.html") == source_audit["page_sha256"]
    before = {name: digest(ROOT / name) for name in (REPORT, PAGE)}
    report = read_json(REPORT)
    focus = [plan for plan in report["plans"] if plan["id"] in ("S4", "S5_AB")]
    assert [plan["arm_slots"] for plan in focus] == [4, 5]
    assert all(len(plan["tasks"]) == 20 and len(plan["scenarios"]) == 8 for plan in focus)
    page = (ROOT / PAGE).read_text()
    assert page.count("__PAYLOAD__") == 1
    args.output_dir.mkdir(parents=True)
    payload = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    (args.output_dir / "review.html").write_text(page.replace("__PAYLOAD__", payload))
    shutil.copy2(ROOT / REPORT, args.output_dir / "review_data.json")
    copies = {}
    sources = [(name, PREVIOUS / name) for name in DETAIL_FILES]
    sources.extend(("workcards/" + name, PREVIOUS / "workcards" / name) for name in WORK_FILES)
    for name, source in sources:
        target = args.output_dir / "details" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        prior = digest(source)
        shutil.copy2(source, target)
        assert prior == digest(source) == digest(target)
        copies[name] = prior
    after = {name: digest(ROOT / name) for name in before}
    assert before == after
    audit = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "page_sha256": digest(args.output_dir / "review.html"),
        "copied_detail_sha256": copies,
        "illustrated_plans": [plan["id"] for plan in focus],
        "source_plans_preserved": len(report["plans"]),
        "scope": "Role diagram only. Dashed connections are assignments, not arm trajectories or reachability.",
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("ROBOT_DIAGRAM_OK focus=S4/S5_AB source_plans=5 source_tasks_each=20", flush=True)
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
