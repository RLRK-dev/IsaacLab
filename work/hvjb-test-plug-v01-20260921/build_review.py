# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Illustrate external test-plug interfaces without selecting test hardware."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
NAME = "HVJB_試験プラグの接続解除と担当比較_v01_20260921"
PORTS = ROOT.parent / "hvjb-port-connection-map-v01-20260921/output/port_connection_map.json"
PLAN = ROOT.parent / "hvjb-line-process-v03-20260921/output/line_process_plan.json"
PREVIOUS = ROOT.parent / "hvjb-after-process-v01-20260921/output/after_process_review.json"
VIDEO = ROOT.parent / "hvjb-line-video-v03-20260921/delivery_manifest.json"
DRAWING = ROOT.parent / "hvjb-line-process-v03-20260921/build_review.py"
SOURCE_RECORD = ROOT / "data/sources.json"
TE_PRODUCT = "https://www.te.com/en/product-4-2103177-1.html"
SPEC = importlib.util.spec_from_file_location("line_drawing", DRAWING)
assert SPEC is not None and SPEC.loader is not None
DRAW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRAW)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def title(c, page, heading, subtitle):
    DRAW.text(c, 48, 62, heading, 34)
    DRAW.text(c, 48, 103, subtitle, 20, DRAW.GRAY)
    DRAW.line(c, 48, 126, 1552, 126, DRAW.BLUE, 2)
    DRAW.text(c, 48, 1064, "HVJB | D71の補足 | 2026-09-21 | 部品・機構・動作の採用前の比較", 17, DRAW.GRAY)
    DRAW.text(c, 1490, 1064, f"{page} / 2", 17, DRAW.GRAY)


def arrow(c, x1, y, x2, color=DRAW.BLUE):
    DRAW.line(c, x1, y, x2, y, color, 3)
    direction = 1 if x2 > x1 else -1
    DRAW.line(c, x2 - direction * 9, y - 6, x2, y, color, 3)
    DRAW.line(c, x2 - direction * 9, y + 6, x2, y, color, 3)


def source_link(c, x, y, label, url):
    DRAW.text(c, x, y, label, 17, DRAW.BLUE)
    width = pdfmetrics.stringWidth(label, DRAW.FONT, 17)
    c.linkURL(url, (x, DRAW.H - y - 4, x + width, DRAW.H - y + 20), relative=0)


def page_one(c, ports, sources):
    title(
        c,
        1,
        "試験用に触るのは、筐体の外側の接続口",
        "今回の照合は前面の補機5口。主電力2口・LV1口の着脱方法は別に確認します。",
    )
    DRAW.box(c, 48, 153, 1504, 86, fill="#e8f4ef")
    DRAW.text(c, 72, 189, "組立用の内側ハウジング／外側ヘッダーと、検査用プラグは別部品です。", 25, DRAW.GREEN)
    DRAW.text(
        c, 72, 220, "D71で必要な接続を検討するための口一覧です。全8口を接続する試験仕様を決めたものではありません。", 18
    )

    DRAW.text(c, 48, 280, "前面を外から見る：既存対応表の3口＋2口", 24, DRAW.BLUE)
    DRAW.box(c, 48, 306, 866, 274, fill="#f6f8fa")
    DRAW.box(c, 944, 306, 608, 274, fill="#f6f8fa")
    DRAW.text(c, 70, 342, "P16  /  2103340-1", 23)
    DRAW.text(c, 966, 342, "P17  /  2103346-2", 23)
    positions = [74, 354, 634, 974, 1254]
    for x, port in zip(positions, ports, strict=True):
        DRAW.box(c, x, 363, 248, 174, fill="#fff0df", stroke="#d0a36d")
        DRAW.text(c, x + 18, 400, port["function"], 23)
        DRAW.text(c, x + 18, 443, "キー " + port["key"], 26, DRAW.GOLD)
        DRAW.text(c, x + 18, 480, "既存の対応口：" + port["model_bay_id"], 18)
        DRAW.text(c, x + 18, 514, "プラグ採用品番：未定", 17, DRAW.GRAY)
    DRAW.text(c, 70, 564, "I01～I05は既存内側ハウジングのID。ここでは同じ接続口への対応に使用。", 17, DRAW.GRAY)
    DRAW.text(
        c, 48, 610, "用途とIDの対応は、公開写真のラベル・公式図面・既存モデルの並びを照合した推定です。", 20, DRAW.GRAY
    )

    DRAW.box(c, 48, 646, 732, 216)
    DRAW.text(c, 70, 682, "TE HVA280のプラグ候補群", 24, DRAW.BLUE)
    DRAW.text(c, 70, 722, "4-2103177-x：指で操作する型／CPA付き\n5-2103177-x：指で操作する型／CPAなし", 21)
    DRAW.text(c, 70, 791, "末尾 x：A=1、D=4、E=5、F=6", 21)
    DRAW.text(c, 70, 830, "工具操作型も存在。図面上の区別であり、採用ではありません。", 18, DRAW.GRAY)
    DRAW.box(c, 804, 646, 748, 216, fill="#fff4df")
    DRAW.text(c, 826, 682, "まだ決まっていないもの", 24, DRAW.GOLD)
    DRAW.text(
        c,
        826,
        722,
        "・試験プラグ一式の型式、線・端子・HVIL構成\n・CPAの採否と操作方法、挿抜の繰返し条件\n・主電力P14/P15、LV12極P18の相手側品番",
        21,
    )
    DRAW.text(c, 826, 830, "キーが合うだけでは、試験ハーネス全体の適合は確定しません。", 18, DRAW.GRAY)
    DRAW.text(c, 48, 913, "CPAは嵌合保証用の追加ロック。次頁の二段ラッチ解除とは区別して扱います。", 22)
    DRAW.text(c, 48, 950, "OP020の外側ヘッダー設置・ねじ固定は維持。検査用プラグを取り付ける工程へ置き換えません。", 20)
    source_link(c, 48, 1002, "出典：Ampere HVJB-5-400 V1.1 p.3–4", sources["AMPERE_V11"]["url"])
    source_link(c, 710, 1002, "TE 2103177 Rev B3：型式・キー・ラッチの区別", sources["TE_DRAWING"]["url"])
    c.showPage()


def grip_sketch(c):
    """Draw functional roles, without claiming dimensions or gripping surfaces."""
    DRAW.box(c, 48, 257, 690, 280, fill="#f6f8fa")
    DRAW.text(c, 66, 287, "役割を示す模式図：指先形状・接触面の寸法は未決定", 18, DRAW.GRAY)
    DRAW.box(c, 94, 351, 37, 131, fill="#8b9ba3")
    DRAW.box(c, 131, 370, 141, 93, fill="#a8b6bf")
    DRAW.box(c, 272, 367, 260, 99, fill="#f5aa60", stroke="#b87737")
    DRAW.text(c, 309, 426, "プラグ本体", 22)
    DRAW.line(c, 532, 403, 690, 403, DRAW.GOLD, 8)
    DRAW.line(c, 532, 430, 690, 430, DRAW.GOLD, 8)
    DRAW.box(c, 322, 353, 62, 18, fill="#77adce")
    DRAW.box(c, 322, 463, 62, 18, fill="#77adce")
    DRAW.box(c, 428, 350, 54, 18, fill="#b6c76c")
    DRAW.line(c, 452, 302, 452, 340, DRAW.GREEN, 4)
    DRAW.line(c, 444, 332, 452, 341, DRAW.GREEN, 3)
    DRAW.line(c, 460, 332, 452, 341, DRAW.GREEN, 3)
    DRAW.text(c, 474, 325, "ラッチ操作を別機能に", 18, DRAW.GREEN)
    DRAW.text(c, 68, 514, "筐体側を支持", 18)
    DRAW.text(c, 284, 514, "形状に沿う保持部", 18, DRAW.BLUE)
    DRAW.text(c, 537, 514, "線には引張力を掛けない", 16, DRAW.GRAY)
    arrow(c, 532, 454, 639)


def page_two(c, sources):
    title(
        c,
        2,
        "保持・ロック操作・引抜きを、別の働きとして扱う",
        "二段解除は公式の操作例。自動化には、採用型のラッチ／CPAと実際の接近空間の照合が必要です。",
    )
    DRAW.box(c, 48, 151, 1504, 77, fill="#e8f4ef")
    DRAW.text(c, 70, 184, "接続：向きを合わせて挿入し、完全嵌合とロックを確認する。", 24, DRAW.GREEN)
    DRAW.text(
        c, 70, 213, "自動判別の方法・力・ストローク・時間は未設定。音だけでロック成立と判定する動作にはしません。", 18
    )
    grip_sketch(c)
    DRAW.box(c, 766, 257, 786, 280)
    DRAW.text(c, 788, 294, "既存の保持方針を試験プラグにも適用する案", 23, DRAW.BLUE)
    DRAW.text(
        c,
        788,
        337,
        "・本体輪郭に沿う受けで、手の中の向きを決める\n・挿抜方向の力を受ける面と、押さえる面を分ける\n・ラッチ／CPAと指の開閉・退避の空間を空ける\n・検査中の本体と線の支持を設備へ引き継ぐ",
        21,
    )
    DRAW.text(
        c,
        788,
        486,
        "従来のH05指先を、そのまま使えるとは未確認です。\n保持指の本数・ロック操作子数・腕数は、それぞれ別に決めます。",
        18,
        DRAW.GRAY,
    )
    DRAW.text(c, 48, 576, "解除の操作例（TE 114-13259 §3.10 / 408-78078 §7）", 23, DRAW.BLUE)
    steps = [
        ("1  最初のラッチ", "本体を保持し、\nフレキシブルラッチを操作"),
        ("2  中間位置まで戻す", "公式の目安：約4.5 mm\nHVILは開、HV端子は接触中"),
        ("3  次のラッチ", "フローティングラッチを\n操作する"),
        ("4  抜去・収納", "本体を引き抜き、\n支持先へ戻して開放"),
    ]
    for i, (heading, body) in enumerate(steps):
        x = 48 + i * 388
        width = 350 if i < 3 else 340
        DRAW.box(c, x, 595, width, 121, fill="#fff4df" if i == 1 else "#edf5f8")
        DRAW.text(c, x + 16, 629, heading, 23)
        DRAW.text(c, x + 16, 665, body, 19)
        if i < 3:
            arrow(c, x + 353, 652, x + 381)
    DRAW.text(
        c,
        48,
        750,
        "CPA付き型の解除は別途照合。4.5 mmは中間位置の説明値で、全抜去量・設計公差ではありません。",
        19,
        DRAW.GOLD,
    )
    DRAW.text(c, 48, 783, "HVIL開と無電圧は別状態です。試験停止・抜去許可は検査設備側の仕様として残します。", 19)
    for x, heading, body in [
        (
            48,
            "比較A：既存腕＋専用指先",
            "腕が位置合わせ・挿抜、操作部がロック解除。\n兼務先との競合と、手先の持替え・退避を確認。",
        ),
        (
            816,
            "比較B：固定の接続機構",
            "案内に沿う挿抜軸＋ロック操作部。\n口位置差・支持・許容ずれを確認し、必要軸数を決める。",
        ),
    ]:
        DRAW.box(c, x, 815, 736, 124, fill="#f6f8fa")
        DRAW.text(c, x + 18, 850, heading, 23)
        DRAW.text(c, x + 18, 890, body, 19)
    DRAW.text(c, 48, 974, "既存5腕の役割は維持。追加腕・5口同時挿抜・試験条件・蓋との順序は未採用／未確定です。", 20)
    source_link(c, 48, 1014, "出典：TE 114-13259 Rev G3 p.9–10", sources["TE_APPLICATION"]["url"])
    source_link(c, 730, 1014, "TE 408-78078 Rev C2 p.10–11（日本語）", sources["TE_JAPANESE"]["url"])
    c.showPage()


def build_data():
    inputs = (PORTS, PLAN, PREVIOUS, VIDEO, DRAWING, SOURCE_RECORD)
    pins = {str(path): sha(path) for path in inputs}
    ports = json.loads(PORTS.read_text())
    plan = json.loads(PLAN.read_text())
    previous = json.loads(PREVIOUS.read_text())
    sources = json.loads(SOURCE_RECORD.read_text())
    assert len(ports["bays"]) == 5
    assert len(plan["cards"]) == 20 and len({item["operation"] for item in plan["cards"]}) == 12
    assert previous["specific_test_connector_or_end_effector"] is None
    assert previous["D70_D71_relative_order"] is None
    key_suffix = {"A": 1, "D": 4, "E": 5, "F": 6}
    port_rows = [
        {
            "model_bay_id": row["id"],
            "model_id_denotes": "existing_internal_housing_not_external_test_plug",
            "header_model_id": row["header_model_id"],
            "header_part_number": row["header_part_number"],
            "key": row["key"],
            "function": row["published_function"],
            "function_mapping_basis": row["function_mapping_basis"],
            "finger_accessible_body_candidates": {
                "with_CPA": f"4-2103177-{key_suffix[row['key']]}",
                "without_CPA": f"5-2103177-{key_suffix[row['key']]}",
            },
            "candidates_are_complete_test_harness_BOM": False,
            "complete_mating_qualification": None,
            "selected_test_plug": None,
        }
        for row in ports["bays"]
    ]
    return {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "status": "source_backed_interface_review_and_unselected_allocation_comparison",
        "source_pins": pins,
        "sources": sources,
        "front_ports": port_rows,
        "all_external_interfaces": {"auxiliary_ports": 5, "main_power_ports": 2, "LV_12_way_ports": 1},
        "actual_test_connection_set": None,
        "main_and_LV_mating_part_numbers": None,
        "published_unmating_observation": {
            "source": "TE_APPLICATION §3.10.B p.9–10 / TE_JAPANESE §7 p.11",
            "sequence": ["flexible_latch", "intermediate_withdrawal", "floating_latch", "full_withdrawal"],
            "approximate_intermediate_travel_m": 0.0045,
            "intermediate_HVIL_state": "open",
            "intermediate_HV_terminals_state": "still_in_contact",
            "pull_on_cables": False,
            "automation_threshold_or_tolerance": None,
            "CPA_specific_sequence": None,
            "complete_automated_cycle_established": False,
        },
        "comparison_only": [
            "existing_arm_with_dedicated_contact_and_latch_features",
            "fixed_guided_connection_mechanism",
        ],
        "unselected": {
            "test_plug_assembly_and_contacts": None,
            "cable_and_HVIL_configuration": None,
            "CPA_variant": None,
            "fixture_CAD_and_contact_surfaces": None,
            "insertion_and_extraction_force": None,
            "full_stroke_and_alignment_tolerances": None,
            "finger_and_latch_actuator_counts": None,
            "mechanism_axis_and_added_robot_counts": None,
            "test_connection_durability_and_replacement_interval": None,
            "test_equipment_disconnect_permission": None,
        },
        "preserved_selected_arm_roles": plan["selected_role_allocation"],
        "coverage": {"tasks": 20, "original_operations": 12},
        "D70_D71_relative_order": None,
        "test_conditions_acceptance_values_and_durations": None,
        "source_video_sha256": json.loads(VIDEO.read_text())["files"][0]["sha256"],
        "source_process_or_video_modified": False,
        "new_motion_or_video_created": False,
        "new_robot_or_fixture_selected": False,
        "formal_physical_validity_verdict": None,
    }


def main():
    assert not OUT.exists(), "Refusing to overwrite an existing review."
    data = build_data()
    (OUT / "pdf").mkdir(parents=True)
    (OUT / "pages").mkdir()
    pdfmetrics.registerFont(UnicodeCIDFont(DRAW.FONT))
    pdf = OUT / "pdf" / (NAME + ".pdf")
    c = canvas.Canvas(str(pdf), pagesize=(DRAW.W, DRAW.H))
    c.setTitle(NAME)
    source_by_id = {row["id"]: row for row in data["sources"]}
    page_one(c, data["front_ports"], source_by_id)
    page_two(c, source_by_id)
    c.save()
    payload = OUT / "test_plug_review.json"
    payload.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    assert all(sha(Path(path)) == digest for path, digest in data["source_pins"].items())
    audit = {
        "builder_sha256": sha(Path(__file__)),
        "pdf_sha256": sha(pdf),
        "json_sha256": sha(payload),
        "pages": 2,
        "sources_unchanged": True,
        "source_pins": data["source_pins"],
        "drawn_text": DRAW.DRAWN,
    }
    (OUT / "document_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print("TEST_PLUG_REVIEW_COMPLETE pages=2 front_ports=5 source_pins_unchanged=6 selection=none")


if __name__ == "__main__":
    main()
