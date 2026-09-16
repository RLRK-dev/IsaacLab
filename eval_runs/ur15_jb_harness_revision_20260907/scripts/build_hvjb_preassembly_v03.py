# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record the user-adopted unitization procedure separately from source observations."""

from __future__ import annotations

import copy
from datetime import datetime
from zoneinfo import ZoneInfo

import build_hvjb_preassembly_review_v01 as base
from build_hvjb_preassembly_review_v02 import update_by_id, verify_links

INPUT = "data/hvjb_unitization_decision_v01.json"
PREVIOUS = "data/hvjb_preassembly_process_v02.json"
OUTPUT = "data/hvjb_preassembly_process_v03.json"
AUDIT = "audit/hvjb_preassembly_v03.json"
EXPECTED = {
    PREVIOUS: "643f75e175518552d290816b402291496e9bb7f21db97385d81180acc9cfe83d",
    base.CATALOG: "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    "UR15_JB_photo_correspondence_v03_p03.blend": "5205d3aa2c2b99f7df6f538d17b3d3ca36ba8208c546858ee8ec8a5a3564a282",
}


def amend(report: dict, decision: dict) -> None:
    """Apply the approved sequence without treating it as newly observed factory behavior."""
    report.update(
        revision="v03",
        title_ja="HVJB：ユーザー採用のユニット化手順",
        observed_at=datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        base_input=PREVIOUS,
        adopted_procedure=copy.deepcopy(decision),
        change_summary_ja=["ユーザー指定により箱外の位置決め・姿勢合わせ・ねじ固定・端末退避・同時搭載を採用。"],
        workflow_ja=(
            "筐体供給・線材準備 → A：下板外組み ／ B：ヒューズ板外組み → "
            "箱外の位置決め・姿勢合わせ・保持中ねじ固定・端末退避 → 一体搭載 → "
            "筐体固定・開口引出し・ヘッダー・バスバー・残接続 → 蓋・検査・払出し"
        ),
    )
    for operation_id in ("O30", "O40"):
        steps = [row for row in decision["steps"] if row["parent_operation"] == operation_id]
        update_by_id(
            report["operations"],
            [
                {
                    "id": operation_id,
                    "stage_ja": "箱外でユニット化" if operation_id == "O30" else "まとめたユニットを筐体搭載",
                    "details_ja": " → ".join(row["name_ja"] for row in steps),
                    "basis_ja": "2026-09-16のユーザー採用手順。実物のねじ固定作業は未確認。",
                    "adoption_status": decision["status"],
                    "procedure_steps": copy.deepcopy(steps),
                    "seconds": None,
                    "source_observation_reference_s": 146,
                }
            ],
        )
    update_by_id(
        report["cells"],
        [
            {
                "id": "C",
                "work_ja": (
                    "A/B側を箱外で位置合わせし、保持中にねじ固定・端末退避後、一体で筐体搭載。後の固定・接続を残す。"
                ),
                "open_ja": (
                    "支持形状、ねじ位置・本数・規格・トルク、自由端案内、保持役、筐体固定点、最終共締め・LV/HVIL。"
                ),
            }
        ],
    )
    update_by_id(
        report["open_interfaces"],
        [
            {
                "id": "U03",
                "next_ja": (
                    "箱外の位置決めから同時搭載までの5段階はユーザー採用済み。支持形状・固定点・ねじ仕様を具体化する。"
                ),
                "procedure_status": decision["status"],
            }
        ],
    )
    update_by_id(
        report["handoff_roles"],
        [
            {
                "id": "HIF01",
                "tool_ja": "採用手順では姿勢を保持しながらねじ固定する。固定箇所と工具仕様は未設定。",
                "open_ja": "支持形状・固定点・把持面・ねじ仕様・荷重・引継ぎ位置。",
            }
        ],
    )
    for edge in report["process_precedence"]:
        if (edge["from"], edge["to"]) == ("O30", "O40"):
            edge["basis"] = "user_adopted_procedure_20260916; actual_factory_joint_unobserved"


def main() -> None:
    """Write new process and audit files, keeping the previous sources untouched."""
    assert all(not (base.ROOT / name).exists() for name in (OUTPUT, AUDIT))
    before = {name: base.digest(base.ROOT / name) for name in EXPECTED}
    assert before == EXPECTED
    previous = base.read_json(PREVIOUS)
    report = copy.deepcopy(previous)
    decision = base.read_json(INPUT)
    catalog = base.read_json(base.CATALOG)
    amend(report, decision)
    verify_links(report, catalog)
    preserved = (
        "preserved_catalog_fields",
        "feature_correspondence",
        "observations",
        "observed_entities",
        "assembly_relations",
        "source_video_evidence",
        "source_plate_evidence",
    )
    assert all(report[key] == previous[key] for key in preserved)
    assert all(report["preserved_catalog_fields"][key] == catalog[key] for key in base.PRESERVED_FIELDS)
    base.write_new_json(base.ROOT / OUTPUT, report)
    after = {name: base.digest(base.ROOT / name) for name in EXPECTED}
    assert before == after
    base.write_new_json(
        base.ROOT / AUDIT,
        {
            "recorded_at": report["observed_at"],
            "user_decision_sha256": base.digest(base.ROOT / INPUT),
            "output": OUTPUT,
            "output_sha256": base.digest(base.ROOT / OUTPUT),
            "source_hashes_before": before,
            "source_hashes_after": after,
            "preserved_fields_exact": list(preserved),
            "adopted_steps": [row["id"] for row in decision["steps"]],
            "process_graph_acyclic": True,
            "geometry_created": False,
            "motion_created": False,
            "movie_created": False,
            "physical_acceptance_verdict": None,
        },
    )
    print("HVJB_PREASSEMBLY_V03 adopted_steps=5 observations_unchanged=True sources_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
