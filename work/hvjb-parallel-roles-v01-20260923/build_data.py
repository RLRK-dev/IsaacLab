# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Preserve the selected sharing-plan examples for an explanatory diagram."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
HISTORICAL = Path(
    "/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907/data/hvjb_robot_sharing_v01.json"
)
CURRENT = ROOT.parent / "hvjb-line-progress-20260923/data/line_review_data.json"
EXPECTED = {
    "historical": "7888693db9b5cd0314b7acecb6c0fa09ab7c207e43c2391fbfbf642833b99b90",
    "current": "55948e4d2603b4ebe1ccd30160c89baa990623ad96eedc515c17583bac4bb440",
}
NAMES = {
    "NONE": "どのセルも補助不要と仮定",
    "A": "Aだけに補助が必要",
    "B": "Bだけに補助が必要",
    "C": "Cだけに補助が必要",
    "AB": "AとBに補助が必要",
    "AC": "AとCに補助が必要",
    "BC": "BとCに補助が必要",
    "ABC": "A・B・Cに補助が必要",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    out = ROOT / "data"
    out.mkdir(exist_ok=False)
    for key, path in (("historical", HISTORICAL), ("current", CURRENT)):
        assert sha(path) == EXPECTED[key], path
    historical = json.loads(HISTORICAL.read_text())
    current = json.loads(CURRENT.read_text())
    selected = current["role_selection_unmodified"]
    plan = next(row for row in historical["plans"] if row["id"] == selected["selected_plan"])
    assert selected["selected_plan"] == "S5_AB"
    assert selected["role_to_unit"] == plan["role_to_unit"]
    assert len(plan["scenarios"]) == 8
    assert len(current["jobs"]) == 20
    assert current["logistics_unmodified"]["deck_count"] == 1
    scenarios = []
    for original in plan["scenarios"]:
        row = dict(original)
        row["title_ja"] = NAMES[row["id"]]
        row["diagram"] = "figures/" + row["id"] + ".svg"
        row["png"] = "figures/" + row["id"] + ".png"
        row["note_ja"] = (
            "A/B共用補助への同時要求。どちらかの保持開始を、前の支持引継ぎと退避の後へ置く。"
            if row["duplicate_assignments"]
            else "この役割表では同じ補助腕への重複なし。到達・移動・支持・工具を含む同時運転は未確認。"
        )
        scenarios.append(row)
    result = {
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "scope": "Display of eight inherited independent cases, not a timed schedule or controller",
        "default_scenario": "AC",
        "scenarios": scenarios,
        "role_selection_unmodified": selected,
        "logistics_unmodified": current["logistics_unmodified"],
        "jobs_unmodified": current["jobs"],
        "cross_task_reservations_unmodified": plan["cross_task_reservations"],
        "same_arm_request_overlap_cases": plan["conflict_scenario_ids"],
        "source_identity": {
            "historical": {"path": str(HISTORICAL), "sha256": EXPECTED["historical"]},
            "current": {"path": str(CURRENT), "sha256": EXPECTED["current"]},
        },
        "time_values_s": None,
        "motion_generated": False,
        "new_physical_assignment": None,
        "physical_acceptance_verdict": None,
    }
    (out / "historical_sharing_source.json").write_bytes(HISTORICAL.read_bytes())
    write(out / "parallel_review_data.json", result)
    print("PARALLEL_DATA_READY scenarios=8 jobs=20 plan=S5_AB overlap=AB,ABC", flush=True)


if __name__ == "__main__":
    main()
