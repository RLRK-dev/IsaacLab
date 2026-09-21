# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Explain existing HVJB assembly locations without assigning unknown joints."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DATA = REPO / "eval_runs/ur15_jb_harness_revision_20260907/data"
OUT = ROOT / "output"
NAME = "HVJB_筐体内外の組立区分_v01_20260921"
PINS = {
    "hvjb_preassembly_process_v03.json": "5e9d7078d4e7ff9772f8561788b29a34b28165e3118559385dcc78faf28b64e7",
    "hvjb_robot_allocation_v01.json": "2e8516405684475d04fcf57938e7771c0283a5ab23cf482aa6fba4b718889dd9",
    "hvjb_task_occupancy_v01.json": "4da5b53687b05cd2cd1d294cf57121abde6ee9d04b19ed0a37ef2fb2a4d79df9",
    "hvjb_robot_selection_v01.json": "ad1d0fc6ad2f0c9d36f4d9839faf559ce80aa9ffb4965174facef944f1a58db8",
    "hvjb_unitization_decision_v01.json": "f28f0693cc48cf288b0c50846f3b23196cf11b02561ce1a8ef55528f8e45f6f6",
    "hvjb_photo_correspondence_v03_p01.json": "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
}
W, H = 1600, 1100
FONT = "HeiseiKakuGo-W5"
INK, MUTED = "#183749", "#526976"
BLUE, GREEN, ORANGE = "#226b97", "#26745c", "#a75a13"
TEXT = []

# Location is an overlay on existing jobs, not a newly selected physical joint.
TASKS = [
    ("D00", "SUPPLY", "空筐体の供給・パレット位置決め", "outside_supply", "供給位置", "ユーザー指定"),
    ("D01", "PREP", "切断・被覆除去・圧着・ハウジング端子挿入", "outside_prep", "筐体外・準備", "加工の供給範囲は未定"),
    ("D10", "A", "接触器・リレー・抵抗等の下板組付け", "outside_A", "筐体外・A", "外組み状態の観察"),
    ("D11", "A", "下板側で完結する配線の接続", "outside_A", "筐体外・A", "端点・共締めは要照合"),
    ("D12", "A → C", "下板ユニットと自由端の受渡し", "outside_transfer", "筐体外", "支持と案内を引継ぐ"),
    ("D20", "B", "補機ヒューズ板側の部品配置・固定", "outside_B", "筐体外・B", "個別保持方式は未定"),
    ("D21", "B", "ヒューズ板側の配線・端末締結", "outside_B", "筐体外・B", "反対端は残り得る"),
    ("D22", "B → C", "ヒューズ板ユニットと自由端の受渡し", "outside_transfer", "筐体外", "支持と案内を引継ぐ"),
    ("D30", "C", "下板とヒューズ板の位置合わせ・板間ねじ固定", "outside_C", "筐体外・C", "採用済み仮手順"),
    ("D31", "C", "工具退避・持ち替え・自由端の退避", "outside_C", "筐体外・C", "採用済み仮手順"),
    ("D40", "C", "まとめたユニットの搬送・筐体搭載", "insertion", "外 → 内", "同時搭載の観察"),
    ("D42", "C", "搭載後の内部工具作業・固定工程枠", "inside_C", "搭載後・内側", "工具先端の対象は未特定"),
    ("D45", "C", "内側ハウジングと線を側面開口へ通す", "wall_crossing", "内 → 開口 → 外", "開口通過後の状態観察"),
    (
        "D50",
        "C",
        "外側ヘッダー固定・主/LV口・内側端末対応",
        "wall_interface",
        "搭載後・側壁両側",
        "詳細な順序は一部未定",
    ),
    ("D60", "C", "バスバー・丸端子・共締め部材の残接続", "inside_C", "搭載後・内側", "各積層・線の対応は未定"),
    (
        "D61",
        "C",
        "残るLV/HVIL・不可視端末の接続",
        "late_interface_unresolved",
        "搭載後・位置要照合",
        "個別端末の内外は未定",
    ),
    ("D70", "AFTER", "シール・蓋の配置・保持・固定", "top_closure", "筐体上面", "検査との詳細順は未定"),
    ("D71", "AFTER", "検査接続・必要検査・結果記録", "inspection", "検査位置", "条件・受入値は新設しない"),
    (
        "D80",
        "AFTER",
        "完成品を筐体取り出し後の空き区画へ戻す",
        "outside_output",
        "共用20区画ストッカ",
        "ユーザーの後続指定",
    ),
    (
        "D81",
        "AFTER",
        "1段コンベアのパレット往復・回収・補給",
        "outside_logistics",
        "搬送・供給位置",
        "旧2段循環を継承しない",
    ),
]

# The three text columns distinguish preassembly from installation and certainty.
PARTS = [
    (
        "下板側の本体部品\nP02/P03/P04・抵抗機能",
        "A：下板へ配置・機械固定。\n下板側で完結する配線を接続。",
        "ユニットとして搭載。\n他部材との残接続はCへ。",
        "外組み状態を観察。\n同一版・固定点は未確認。",
    ),
    (
        "補機ヒューズ板・5個\nP07 / P05/P06/P19/P20/P21",
        "B：板側の部品を組み、\n板側配線端末を締結する。",
        "組んだ板を搭載。\n配線の反対端は残り得る。",
        "外組み配線を観察。\n本体保持方式は未確定。",
    ),
    (
        "下板とヒューズ板の接合",
        "C：位置合わせ → 保持 →\n板間ねじ固定 → 自由端退避。",
        "接合済みの扱いで\n2ユニットをまとめて入れる。",
        "ユーザー採用の仮手順。\n実物接合具・ねじ詳細は未確認。",
    ),
    (
        "ユニットと筐体の固定",
        "筐体へ入れる前には\n筐体との固定を行わない。",
        "C内側：搭載後の固定工程枠。\n工具先端の対象は未特定。",
        "2:38に箱内工具を観察。\n固定点・本数を推定しない。",
    ),
    (
        "内側ハウジング\nI01-I05・電力/HVIL端子",
        "準備：線材加工・圧着・\nハウジングへの端子挿入。",
        "C：側面開口へ通し、\n外側ヘッダーへ組み付ける。",
        "個々の線の所属・端点と\n端末操作の詳細は未定。",
    ),
    (
        "外側ヘッダー\nP16：3口 / P17：2口",
        "別部品として準備。\n内側ハウジングと区別。",
        "C側壁外側：設置・ねじ固定。\n内側端末の保持も必要。",
        "搭載後の取付を観察。\nM4穴8点 / 6点を別管理。",
    ),
    (
        "主接続口・LV口\nP14/P15/P18",
        "接続口と端末を準備。\n詳細な取付方式は未確定。",
        "Cの側壁接口作業に残す。\n内側接続との引継ぎを分離。",
        "型式・固定法の未確認部分を\n補機ヘッダーで代用しない。",
    ),
    (
        "バスバー・剛体導体\nP09-P13の対応候補",
        "部材を準備。A/Bでの\n共締め予定点を先に本締めしない。",
        "C内側：残る導体・丸端子等を\nそろえて保持中に締結。",
        "3:57以降の作業を観察。\n部品境界・積層は未確定。",
    ),
    (
        "リレー端末・LV/HVIL\nT31-T44等・必須機能",
        "A/B内で完結できる分を先組み。\nどの端末かは個別照合が必要。",
        "C：残る接続を完了する枠。\n各端末の内外位置は未確定。",
        "回路図だけで物理線・\n組付け回数を決めない。",
    ),
    (
        "配線・丸端子・ねじ頭特徴\nW群 / L01-L07 / 締結特徴",
        "線の片端・固定点ごとに\nA/Bで完了する接続を分ける。",
        "反対端・最終共締めをCへ。\n未接続端の保持は継続する。",
        "27区間は27本ではない。\n23特徴は全ねじ数ではない。",
    ),
    (
        "主ヒューズ・黒い被覆\nP22 / P08",
        "取付工程は未確定。\n補機ヒューズの外組みと別扱い。",
        "B先組みかC搭載後か、\n支持・導体積層の照合を残す。",
        "完成位置は対応済み。\n工程所属は決めつけない。",
    ),
    (
        "シール・蓋・検査",
        "部品・検査設備を準備。",
        "筐体上面の閉鎖と必要検査。\n詳細な前後順・条件は未定。",
        "残接続と検査を省かず、\n蓋を置くだけで完了にしない。",
    ),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def collect():
    for name, digest in PINS.items():
        assert sha(DATA / name) == digest, name
    inputs = {name: json.loads((DATA / name).read_text()) for name in PINS}
    process = inputs["hvjb_preassembly_process_v03.json"]
    allocation = inputs["hvjb_robot_allocation_v01.json"]
    occupancy = inputs["hvjb_task_occupancy_v01.json"]
    catalog = inputs["hvjb_photo_correspondence_v03_p01.json"]
    selection = inputs["hvjb_robot_selection_v01.json"]
    source_tasks = {row["id"]: row for row in allocation["tasks"]}
    assert len(TASKS) == len(source_tasks) == len({row[0] for row in TASKS}) == 20
    assert {row[0] for row in TASKS} == set(source_tasks)
    assert selection["selected_plan"] == "S5_AB"
    assert [len(catalog[k]) for k in ("parts", "visible_wire_segments", "visible_fastener_features")] == [42, 27, 23]
    assert [len(catalog[k]) for k in ("required_functions", "electrical_groups", "lv_pin_map")] == [17, 13, 12]
    rows = []
    for task_id, cell, description, location, location_ja, limit in TASKS:
        source = source_tasks[task_id]
        rows.append(
            {
                "id": task_id,
                "operation": source["operation"],
                "display_cell": cell,
                "work_ja": description,
                "location": location,
                "location_ja": location_ja,
                "basis_or_limit_ja": limit,
                "physical_joint_assignment": None,
                "source_task": copy.deepcopy(source),
            }
        )
    result = {
        "revision": "hvjb_assembly_location_v01",
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "status": "clarification_of_existing_process_and_user_decisions",
        "builder_sha256": sha(Path(__file__)),
        "source_sha256": PINS,
        "source_video": copy.deepcopy(process["source_video"]),
        "source_video_observations": copy.deepcopy(process["observations"]),
        "revision_boundary_ja": process["revision_boundary_ja"],
        "unitization_decision": copy.deepcopy(inputs["hvjb_unitization_decision_v01.json"]),
        "selected_arm_roles": copy.deepcopy(selection),
        "part_and_joint_location_table": [
            dict(
                zip(
                    ("target_ja", "before_installation_ja", "after_installation_ja", "basis_or_limit_ja"),
                    row,
                    strict=True,
                )
            )
            for row in PARTS
        ],
        "task_locations": rows,
        "preserved_source_workcards": copy.deepcopy(occupancy["cards"]),
        "preserved_feature_groups": copy.deepcopy(process["feature_groups"]),
        "preserved_photo_catalog": copy.deepcopy(catalog),
        "current_logistics_overlay": {
            "basis": "later_explicit_user_directives_in_session",
            "directives_ja": [
                "3軸直交へ変更する",
                "コンベアは1段にしてパレットは往復させる。ストッカは完成品もおけるようにする（筐体が取り出された空き領域に完成品を置く）",
            ],
            "op010": "XYZ Cartesian; 20 shared empty-case / finished-product slots",
            "conveyor": "single-level reciprocating pallet conveyor; no work-station pallet lift",
            "historical_fields_superseded": [
                "O80.details_ja two-level return",
                "E-RETURN.role_ja two-level circulation",
            ],
            "logistics_hardware_count_selected": None,
            "note_ja": "引用元の旧2段記述は歴史として保存。現在の工程図へ転記しない。",
        },
        "unresolved": {
            "main_fuse_P22_and_cover_P08_assembly_stage": None,
            "O42_hidden_tool_target": None,
            "individual_LV_HVIL_endpoint_locations": None,
            "individual_wire_to_fuse_or_bolt_assignment": None,
            "joint_stacks_fastener_positions_torques": None,
            "new_confirmed_physical_connections": [],
        },
        "coverage": {
            "tasks": 20,
            "operations": 12,
            "photo_features": 92,
            "functions": 17,
            "circuit_groups": 13,
            "lv_pins": 12,
        },
        "prior_art": {
            "keywords": ["HVJB", "外組み", "筐体搭載", "工程分担"],
            "exit_code": 0,
            "findings": 0,
            "blockers": 0,
        },
        "source_scene_modified": False,
        "motion_created": False,
        "physical_acceptance_verdict": None,
    }
    assert len({row["operation"] for row in rows}) == 12
    assert result["preserved_source_workcards"] == occupancy["cards"]
    assert result["preserved_photo_catalog"] == catalog
    return result


def text(c, x, y, value, size=18, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont(FONT, size)
    for index, row in enumerate(value.split("\n")):
        baseline = H - y - index * size * 1.35
        width = pdfmetrics.stringWidth(row, FONT, size)
        assert x >= 0 and x + width < W - 30 and 20 < baseline < H, row
        c.drawString(x, baseline, row)
        TEXT.append({"page": c.getPageNumber(), "text": row, "x": x, "baseline": baseline, "width": width})


def box(c, x, y, width, height, fill="#f1f6f9", stroke="#d5e2e8"):
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor(stroke))
    c.roundRect(x, H - y - height, width, height, 8, fill=1, stroke=1)


def line(c, x1, y1, x2, y2, color=MUTED, width=2):
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(width)
    c.line(x1, H - y1, x2, H - y2)


def down(c, x, y1, y2, color=MUTED):
    line(c, x, y1, x, y2, color, 3)
    line(c, x, y2, x - 7, y2 - 11, color, 3)
    line(c, x, y2, x + 7, y2 - 11, color, 3)


def header(c, page, title, subtitle):
    text(c, 55, 60, title, 31)
    text(c, 55, 100, subtitle, 18, MUTED)
    text(c, 1450, 57, f"{page} / 3", 17, MUTED)
    line(c, 55, 1030, 1545, 1030, "#d5e2e8", 1)
    text(
        c, 55, 1054, "既存工程とユーザー採用手順の区分。2022年完成写真と2025年組立映像の同一製造版は未確認。", 13, MUTED
    )
    text(c, 55, 1077, "工程の整理であり、実物の全締結仕様・自動組立の成立を確定した資料ではありません。", 12, MUTED)
    text(c, 1405, 1077, "2026-09-21", 12, MUTED)


def page_one(c):
    header(
        c,
        1,
        "筐体外でユニット化 → まとめて搭載 → 残接続",
        "補機ヒューズ板側の配線締結は筐体外。搭載後の内部接続と、側壁の外側から行う作業を区別します。",
    )
    text(c, 55, 150, "筐体外 / 搭載前", 24, BLUE)
    box(c, 55, 175, 700, 174)
    box(c, 845, 175, 700, 174)
    text(c, 80, 213, "A：下板側ユニット", 27, BLUE)
    text(
        c,
        80,
        256,
        "接触器・リレー・抵抗等を下板へ組み付ける。\n下板側で完結する配線を接続する。\n未接続の反対端は、保持・案内を引き継ぐ。",
        21,
    )
    text(c, 870, 213, "B：補機ヒューズ板側ユニット", 27, BLUE)
    text(
        c,
        870,
        256,
        "板側の部品を組み、板側配線端末を締結する。\n筐体へ入れてから同じ箇所を締め直す工程ではない。\n主ヒューズの取付工程は別途未確定。",
        21,
    )
    line(c, 405, 349, 405, 380)
    line(c, 1195, 349, 1195, 380)
    line(c, 405, 380, 1195, 380)
    down(c, 800, 380, 408)
    box(c, 300, 413, 1000, 118)
    text(c, 325, 450, "Cの前半も筐体外：2ユニットをまとめる", 26, BLUE)
    text(c, 325, 490, "下板を支持 → ヒューズ板を合わせる → 保持中に板間ねじ固定 → 自由端をよける", 20)
    text(c, 325, 517, "ユーザー採用の仮手順。実物の接合具・ねじ位置・本数・締付条件は未確認。", 16, MUTED)
    down(c, 800, 531, 567)
    box(c, 390, 573, 820, 95, "#e9f3ec")
    text(c, 415, 610, "搭載：まとめたユニットを筐体へ入れる", 26, GREEN)
    text(c, 415, 646, "本体の支持と自由端の案内を継続。筐体底面P01は可搬下板ではない。", 18)
    line(c, 800, 668, 800, 692)
    line(c, 410, 692, 1190, 692)
    down(c, 410, 692, 720, GREEN)
    down(c, 1190, 692, 720, ORANGE)
    box(c, 55, 726, 710, 192, "#edf6f1")
    box(c, 835, 726, 710, 192, "#fff4e8")
    text(c, 80, 765, "搭載後：筐体内で行う作業", 26, GREEN)
    text(
        c,
        80,
        808,
        "ユニットの筐体固定工程枠（個別固定点は未特定）。\nバスバー・丸端子等の残る接続と共締め。\nLV/HVILの残接続は端末ごとに位置を照合する。",
        20,
    )
    text(c, 80, 898, "板側の締結と、配線の反対端の締結を混同しない。", 17, GREEN)
    text(c, 860, 765, "搭載後：側壁をまたぐ作業", 26, ORANGE)
    text(
        c,
        860,
        808,
        "内側ハウジング・線を側面開口へ通す。\n外側ヘッダーを側壁外側から設置・ねじ固定する。\n内側端末の保持・組付けも引き継ぐ。",
        20,
    )
    text(c, 860, 898, "この2枠は場所の区分。並列実行の指定ではない。", 17, ORANGE)
    box(c, 55, 947, 1490, 65, "#f5f5f5")
    text(c, 80, 974, "残接続 → シール・蓋 / 必要検査 → 完成品を20区画ストッカの空き領域へ戻す", 21)
    text(c, 80, 1001, "蓋と検査の詳細順は未定。A/B/Cの担当区分は維持し、1段の往復パレット搬送とする。", 16, MUTED)
    c.showPage()


def page_two(c):
    header(
        c,
        2,
        "部品・接続箇所ごとの区分",
        "ケーブル全体ではなく「どちらの端を、いつ接続するか」で分けます。写真IDは参照先であり製造BOMではありません。",
    )
    xs = (55, 375, 785, 1195)
    widths = (315, 405, 405, 350)
    titles = ("対象", "筐体外・搭載前", "搭載後・作業位置", "根拠 / 未確定事項")
    for x, width, title in zip(xs, widths, titles, strict=True):
        box(c, x, 141, width, 45, "#e3edf2")
        text(c, x + 12, 171, title, 21)
    for i, row in enumerate(PARTS):
        y = 192 + i * 62
        fill = "#fff4e8" if i == 10 else ("#f2f7f9" if i % 2 == 0 else "#ffffff")
        for x, width, value in zip(xs, widths, row, strict=True):
            box(c, x, y, width, 58, fill)
            for subline in value.split("\n"):
                assert pdfmetrics.stringWidth(subline, FONT, 16) < width - 20, subline
            text(c, x + 12, y + 24, value, 16)
    text(
        c,
        55,
        965,
        "主ヒューズP22・被覆P08の取付工程、個々のLV/HVIL端末、箱内工具の隠れた固定点は未確定のまま残します。",
        19,
        ORANGE,
    )
    text(
        c,
        55,
        1000,
        "写真92特徴・必須17機能・13回路群・LV12極をJSONへ原文保持。見えない部品や接続を削除していません。",
        17,
        MUTED,
    )
    c.showPage()


def page_three(c, data):
    header(
        c,
        3,
        "既存20仕事を、作業場所で対応させる",
        "A/B/Cは担当セル。Cには筐体外・内側・側壁の作業が含まれます。O番号は工程整理IDであり、ラインのOP番号とは別です。",
    )
    xs = (55, 195, 335, 1030, 1290)
    widths = (135, 135, 690, 255, 255)
    for x, width, title in zip(
        xs, widths, ("仕事 / 工程", "担当", "仕事の内容", "作業場所", "根拠・注意点"), strict=True
    ):
        box(c, x, 132, width, 37, "#e3edf2")
        text(c, x + 8, 157, title, 17)
    for i, row in enumerate(data["task_locations"]):
        y = 174 + i * 34
        values = (
            f"{row['id']} / {row['operation']}",
            row["display_cell"],
            row["work_ja"],
            row["location_ja"],
            row["basis_or_limit_ja"],
        )
        for x, width, value in zip(xs, widths, values, strict=True):
            box(c, x, y, width, 31, "#f3f7f9" if i % 2 == 0 else "#ffffff")
            assert pdfmetrics.stringWidth(value, FONT, 15) < width - 14, value
            text(c, x + 8, y + 22, value, 15)
    text(c, 55, 885, "根拠：Ampere公式組立映像の保存観察 + 2026-09-16採用のユニット化手順 + 後続の搬送指定", 19)
    text(
        c,
        55,
        918,
        "0:24 下板外組み / 0:50 ヒューズ板配線 / 2:26 一体搭載 / 2:38 箱内工具 / 2:50 開口通過 / 3:57 バスバー",
        17,
        MUTED,
    )
    text(c, 55, 947, "公式映像：ASSEMBLY! EV High Voltage Junction Box（Ampere EV、2025-06-07）", 17, BLUE)
    c.linkURL("https://www.youtube.com/watch?v=Sm_D-vmNYqc", (55, H - 951, 1230, H - 930), relative=0)
    text(c, 55, 976, "5腕分担：主担当A/B/C + A/B共用補助 + C専用補助。自由端の支持引継ぎまで補助を解放しない。", 17)
    text(
        c,
        55,
        1006,
        "保存元6ファイルのSHAと全20仕事・写真台帳を同梱JSONに保持。元モデル・指・軌道・動画は変更していません。",
        16,
        MUTED,
    )
    c.showPage()


def main():
    (OUT / "pdf").mkdir(parents=True, exist_ok=True)
    data = collect()
    write_json(OUT / "assembly_location.json", data)
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    path = OUT / "pdf" / f"{NAME}.pdf"
    c = canvas.Canvas(str(path), pagesize=(W, H))
    c.setTitle("HVJB：筐体内外の組立区分")
    page_one(c)
    page_two(c)
    page_three(c, data)
    c.save()
    write_json(
        OUT / "document_audit.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "builder_sha256": sha(Path(__file__)),
            "pdf_sha256": sha(path),
            "json_sha256": sha(OUT / "assembly_location.json"),
            "page_count": 3,
            "coverage": data["coverage"],
            "drawn_text": TEXT,
            "physical_acceptance_verdict": None,
        },
    )
    print("ASSEMBLY_LOCATION_COMPLETE pages=3 tasks=20 operations=12 photo_features=92")
    print(f"PDF SHA256 {sha(path)}")


if __name__ == "__main__":
    main()
