# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Join existing job, feature, hand and location records for one visual review."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OUT = ROOT / "data"
SOURCES = {
    "process": WORK / "hvjb-line-process-v03-20260921/output/line_process_plan.json",
    "ports": WORK / "hvjb-port-connection-map-v01-20260921/output/port_connection_map.json",
    "after_process": WORK / "hvjb-after-process-v01-20260921/output/after_process_review.json",
    "test_plug": WORK / "hvjb-test-plug-v01-20260921/output/test_plug_review.json",
    "location": WORK / "hvjb-assembly-location-v01-20260921/output/assembly_location.json",
    "product": WORK / "hvjb-inner-installed-access-v01-20260921/data/product_manifest.json",
}
COLORS = {"A": "#296DB3", "B": "#9E478F", "C": "#198772", "LOGISTICS": "#47758A", "OPEN": "#A7610F"}
SCENE_VIEW = {
    "S01": "case",
    "S02": "wires_display_only",
    "S03": "outside_A",
    "S04": "outside_B",
    "S05": "product",
    "S06": "product",
    "S07": "product",
    "S08": "case",
    "S09": "product",
    "S10": "internal_housings",
    "S11": "external_headers",
    "S12": "after_insertion_bus",
    "S13": "main_and_lv_unassigned",
    "S14": "main_and_lv_unassigned",
    "S15": "product",
    "S16": "case",
}
LOCATION_GROUP = {
    "outside_supply": "LOGISTICS",
    "outside_prep": "OPEN",
    "outside_A": "A",
    "outside_B": "B",
    "outside_transfer": "C",
    "outside_C": "C",
    "insertion": "C",
    "inside_C": "C",
    "wall_crossing": "C",
    "wall_interface": "C",
    "late_interface_unresolved": "OPEN",
    "top_closure": "OPEN",
    "inspection": "OPEN",
    "outside_output": "LOGISTICS",
    "outside_logistics": "LOGISTICS",
}
OPEN_ITEMS = [
    ("Q01", "線材・端末の準備範囲", ["D01", "D81"], "加工済み入荷とライン内加工の境界・補給方法"),
    ("Q02", "主ヒューズP22と被覆P08", ["D20", "D21", "D60"], "箱外／箱内の所属・支持関係・共締め・取付順"),
    ("Q03", "搭載後の箱内工具対象", ["D42"], "先端が隠れた作業点。具体的なねじ・本数・積層"),
    ("Q04", "自由端を渡す相手", ["D12", "D22", "D31", "D40", "D45", "D50"], "各端末の個体・所属・必要な保持数"),
    ("Q05", "LV/HVILと主接続の細部", ["D60", "D61"], "物理端点・接続順・主口／LV口の固有部品"),
    ("Q06", "蓋・シールと試験", ["D70", "D71"], "順序・支持・試験接続口・条件・時間・装置分担"),
    ("Q07", "機種・手先交換・工具", ["D10", "D20", "D31", "D50", "D60"], "ロボット機種・交換方法・締付工具は未選定"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, payload) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def job_rows(plan: dict) -> list[dict]:
    targets = plan["preserved_hand_plan"]["preserved"]["targets"]
    rows = []
    for card in plan["cards"]:
        rows.append(
            {
                "id": card["id"],
                "operation": card["operation"],
                "title_ja": card["title_ja"],
                "location": card["location_record"]["location"],
                "location_ja": card["location_record"]["location_ja"],
                "group": LOCATION_GROUP[card["location_record"]["location"]],
                "primary_ja": card["primary_label_ja"],
                "hands_ja": card["current_hand_display_ja"],
                "assistance_ja": card["assistance_label_ja"],
                "transfer_ja": card["transfer_ja"],
                "unresolved_ja": card["unresolved_ja"],
                "scene_ids": card["scene_ids"],
                "review_feature_ids": [row["id"] for row in targets if card["id"] in row["review_task_ids"]],
                "feature_assignment_kind": "existing_review_candidates_not_selected_physical_operations",
            }
        )
    return rows


def export_csv(rows: list[dict], targets: list[dict]) -> None:
    with (OUT / "20仕事_場所_担当_引継ぎ.csv").open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["仕事", "元工程", "作業場所", "内容", "主担当", "手先用途", "補助", "引継ぎ", "未確定"])
        for row in rows:
            writer.writerow(
                [
                    row["id"],
                    row["operation"],
                    row["location_ja"],
                    row["title_ja"],
                    row["primary_ja"],
                    row["hands_ja"],
                    row["assistance_ja"],
                    row["transfer_ja"],
                    row["unresolved_ja"],
                ]
            )
    with (OUT / "92項目_既存工程候補との対応.csv").open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["写真特徴ID", "名称", "既存の部品群", "検討先の仕事", "区分", "未確定"])
        for target in targets:
            writer.writerow(
                [
                    target["id"],
                    target["name_ja"],
                    target["group_name_ja"],
                    " / ".join(target["review_task_ids"]),
                    "工程検討先。採用済み物理施工ではない",
                    target["unresolved_ja"],
                ]
            )


def main() -> None:
    assert not OUT.exists(), OUT
    payloads = {key: json.loads(path.read_text()) for key, path in SOURCES.items()}
    baseline = json.loads((ROOT / "audit/baseline.json").read_text())
    plan = payloads["process"]
    assert sha(SOURCES["process"]) == baseline["plan_sha256"]
    assert plan["selected_role_allocation"]["selected_plan"] == "S5_AB"
    targets = plan["preserved_hand_plan"]["preserved"]["targets"]
    assert {row["id"] for row in targets} == set(payloads["product"]["features"])
    jobs = job_rows(plan)
    assert len(jobs) == 20 and len(targets) == 92
    assert all(row["review_task_ids"] for row in targets)
    scenes = []
    for row in plan["scenes"]:
        scenes.append({**row, "product_view": SCENE_VIEW[row["id"]], "product_view_is_completed_configuration": True})
    result = {
        "revision": "hvjb_line_visual_review_v04_20260923",
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "colors": COLORS,
        "jobs": jobs,
        "scenes": scenes,
        "feature_review_candidates": targets,
        "role_selection_unmodified": plan["selected_role_allocation"],
        "logistics_unmodified": plan["logistics"],
        "c_support_reservations_unmodified": plan["preserved_hand_plan"]["c_reservation"],
        "open_interfaces_unmodified": plan["preserved_hand_plan"]["open_interfaces"],
        "coverage": plan["preserved_location_coverage"],
        "open_items_for_navigation": [
            {"id": key, "title_ja": title, "task_ids": tasks, "unresolved_ja": issue}
            for key, title, tasks, issue in OPEN_ITEMS
        ],
        "cpa_followup": {
            "source": "TE 408-32095 Rev B (2013-11-06), pp.4-6",
            "source_url": "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=408-32095&DocType=Specification+Or+Standard&PartCntxt=2103245-1",
            "source_sha256": "cd13cd856b679e2683f7672f079bd4c99ff87ac2e361d3da73700e12c12fa63d",
            "general_closing_direction": "toward_header_after_full_mating",
            "general_opening_direction": "away_from_header_before_primary_latch_operation",
            "scope_ja": "一般操作の追加読取。試験ハーネス採用・操作量・自動治具の仕様確定ではない。",
            "selected_part_number": None,
            "selected_actuation_stroke_m": None,
        },
        "source_identity": [
            {"name": name, "path": str(path.relative_to(ROOT.parents[1])), "sha256": sha(path)}
            for name, path in SOURCES.items()
        ],
        "existing_document_or_motion_modified": False,
        "new_physical_operation_selection": None,
        "new_equipment_selection": None,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    OUT.mkdir(parents=True)
    save(OUT / "line_review_data.json", result)
    export_csv(jobs, targets)
    print("LINE_REVIEW_DATA_COMPLETE jobs=20 source_operations=12 photo_features=92 selected_arm_roles=5")


if __name__ == "__main__":
    main()
