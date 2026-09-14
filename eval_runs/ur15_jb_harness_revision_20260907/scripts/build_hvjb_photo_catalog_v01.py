# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Inventory observed photo features independently of electrical requirements."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = ROOT / "references/op040_real_products_20260912"
SUPPORT = "https://help.ampereev.com/hc/en-us/articles/31292470232087-High-Voltage-Junction-Box-HVJB-5-400"
PDF_URL = "https://help.ampereev.com/hc/en-us/article_attachments/31292430639639"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def observed_parts():
    # Rectangles are manually located on DSC02860-1, not manufacturing dimensions.
    rows = [
        (
            "P01",
            "黒い筐体・四隅の蓋ねじボス",
            "case",
            [211, 201, 1160, 708],
            "筐体外形は公開図。内部加工・ボス詳細は未公開。",
        ),
        (
            "P02",
            "GIGAVAC表示の主接触器",
            "contactor",
            [621, 509, 466, 266],
            "製品機能と写真は対応。GX14は候補に留め、末尾仕様は未同定。",
        ),
        ("P03", "写真上側の角形リレー本体", "relay", [453, 291, 142, 142], "プリチャージ／放電のどちらかは未対応。"),
        ("P04", "写真下側の角形リレー本体", "relay", [432, 494, 160, 171], "プリチャージ／放電のどちらかは未対応。"),
        (
            "P05",
            "上部左の筒状ヒューズ",
            "fuse",
            [621, 269, 184, 84],
            "胴と両端が見える。補機系統・電流値への割当は未確定。",
        ),
        (
            "P06",
            "上部右の筒状ヒューズ",
            "fuse",
            [897, 267, 183, 79],
            "胴と両端が見える。補機系統・電流値への割当は未確定。",
        ),
        (
            "P07",
            "後方の細長い灰色部材",
            "rear_rail",
            [556, 216, 585, 55],
            "見える外形を記録。抵抗・保持部との機能対応は未確定。",
        ),
        (
            "P08",
            "中央の黒い幅広部材",
            "central_cover",
            [718, 343, 250, 193],
            "見える外形を記録。カバーか絶縁部か、下側の部品は未確定。",
        ),
        (
            "P09",
            "左主端子から内側へ延びる板状導体",
            "bus_left_upper",
            [348, 414, 374, 105],
            "中央で隠れる。右側導体との一体性は未確定。",
        ),
        (
            "P10",
            "右主端子から内側へ延びる板状導体",
            "bus_right_upper",
            [963, 383, 242, 151],
            "中央で隠れる。左側導体との一体性は未確定。",
        ),
        (
            "P11",
            "左下主端子付近の板状導体",
            "bus_left_lower",
            [345, 576, 97, 160],
            "下側の接続部と重なる。製造部品としての分割は未確定。",
        ),
        (
            "P12",
            "接触器右端子と右下主端子間の板状導体",
            "bus_right_lower",
            [1002, 564, 214, 104],
            "板と2か所の締結点が見える。座金・端子の積層は未確定。",
        ),
        (
            "P13",
            "前方の複数ねじ付き板状導体",
            "bus_front",
            [354, 697, 326, 63],
            "丸端子が重なる。導体の裏側と他部材との境界は未確定。",
        ),
        (
            "P14",
            "左側の主2極ハウジング",
            "main_left",
            [137, 418, 218, 269],
            "Amphenol表示の公開図と外観に対応。詳細型式・寸法は未確定。",
        ),
        (
            "P15",
            "右側の主2極ハウジング",
            "main_right",
            [1237, 413, 187, 273],
            "Amphenol表示の公開図と外観に対応。詳細型式・寸法は未確定。",
        ),
        (
            "P16",
            "前面3口外部ヘッダー",
            "header_three",
            [322, 855, 485, 158],
            "2103340-1公式CAD。キーA/D/Eを公開図へ照合。",
        ),
        ("P17", "前面2口外部ヘッダー", "header_two", [920, 852, 314, 161], "2103346-2公式CAD。キーD/Fを公開図へ照合。"),
        (
            "P18",
            "奥側の黒い低圧12極ハウジング",
            "lv_header",
            [377, 123, 94, 89],
            "公開図は12極。メーカー・キー・品番は未確定。",
        ),
    ]
    parts = []
    for part_id, name, profile, rect, note in rows:
        parts.append({"id": part_id, "name_ja": name, "profile": profile, "rect_px": rect, "note_ja": note})
    for i, (part, key, x) in enumerate(((1, "A", 415), (4, "D", 570), (5, "E", 715), (4, "D", 1008), (6, "F", 1150))):
        parts.append(
            {
                "id": f"I{i + 1:02d}",
                "name_ja": f"補機口{i + 1}の内側ハウジング（キー{key}）",
                "profile": "inner_header",
                "rect_px": [x - 35, 789, 81, 72],
                "part_number": f"2103245-{part}",
                "bay": i,
                "note_ja": "外部ハウジングと別部品。公式CADを使用。圧着端子・シールの全構成は未確定。",
            }
        )
    for relay, rectangles in (
        ("P03", [[470, 291, 53, 44], [510, 369, 44, 44], [537, 321, 46, 58], [487, 318, 40, 59]]),
        ("P04", [[443, 538, 44, 69], [545, 523, 43, 70], [476, 508, 63, 48], [486, 604, 61, 41]]),
    ):
        for i, rect in enumerate(rectangles):
            parts.append(
                {
                    "id": f"T{relay[-1]}{i + 1}",
                    "name_ja": f"{relay}上面の差込端末外装{i + 1}",
                    "profile": "relay_terminal",
                    "rect_px": rect,
                    "relay": relay,
                    "render_color": "translucent" if i < 2 else "ivory",
                    "note_ja": "外装を各1個ずつ記録。金属端子・絶縁外装の品番、極性、係合条件は未確定。",
                }
            )
    for part in parts:
        part["model_id"] = "REF_" + part["id"]
        part["photo"] = "overview"
        part["manufacturing_dimensions_m"] = None
        part["part_number"] = {"P16": "2103340-1", "P17": "2103346-2"}.get(part["id"], part.get("part_number"))
        part["physical_bom_quantity"] = None
    return parts


def fasteners():
    points = [
        ("P02", 678, 649),
        ("P02", 1027, 644),
        ("P02", 751, 559),
        ("P02", 944, 744),
        ("P09", 394, 489),
        ("P10", 1170, 490),
        ("P11", 389, 608),
        ("P12", 1162, 605),
        ("P13", 377, 738),
        ("P13", 434, 734),
        ("P13", 509, 730),
        ("P13", 575, 735),
        ("P13", 635, 735),
        ("P05", 583, 276),
        ("P05", 813, 277),
        ("P06", 871, 278),
        ("P06", 1091, 278),
    ]
    return [
        {
            "id": f"J{i + 1:02d}",
            "feature_parent": parent,
            "center_px": [x, y],
            "photo": "overview",
            "model_id": f"REF_J{i + 1:02d}",
            "description_ja": "写真に見えるねじ頭／ナット位置。ねじ径・長さ・裏側・共締め構成は未確定。",
            "fastener_specification": None,
            "joint_stack": None,
        }
        for i, (parent, x, y) in enumerate(points)
    ]


def wire_segments():
    # Visible portions only: a hidden end must never be silently joined to a guessed terminal.
    rows = [
        (
            "W01",
            "上側左・太い橙線",
            [[344, 344], [348, 292], [371, 265], [405, 269], [459, 281], [526, 282], [557, 278]],
            0.0048,
            "orange",
            [None, "J14"],
        ),
        (
            "W02",
            "上側左・細い橙線",
            [[337, 407], [339, 352], [355, 311], [389, 295], [451, 290], [506, 288]],
            0.0025,
            "orange",
            [None, None],
        ),
        (
            "W03",
            "上側右の橙線",
            [[1125, 268], [1169, 253], [1210, 231], [1222, 235], [1232, 277], [1238, 375]],
            0.0048,
            "orange",
            ["J17", None],
        ),
        (
            "W04",
            "前方の長い橙線・上側",
            [[643, 739], [690, 759], [768, 790], [856, 795], [974, 789], [1081, 756], [1207, 722], [1260, 715]],
            0.0032,
            "orange",
            ["J13", None],
        ),
        (
            "W05",
            "前方の長い橙線・下側",
            [[579, 739], [652, 780], [727, 812], [794, 820], [893, 807], [988, 788], [1093, 770]],
            0.0032,
            "orange",
            ["J12", None],
        ),
        (
            "W06",
            "左下の折返し橙線",
            [[366, 690], [334, 672], [303, 679], [292, 704], [317, 727], [374, 744]],
            0.0032,
            "orange",
            [None, "J09"],
        ),
        (
            "W07",
            "左下の内側橙線",
            [[354, 659], [315, 659], [293, 680], [304, 695], [346, 708], [397, 739]],
            0.0025,
            "orange",
            [None, None],
        ),
        (
            "W08",
            "下側リレー左の橙線",
            [[457, 575], [456, 544], [457, 506], [466, 499], [479, 499]],
            0.0018,
            "orange",
            ["T41", None],
        ),
        (
            "W09",
            "下側リレー横断の橙線",
            [[470, 518], [494, 530], [527, 549], [553, 574]],
            0.0018,
            "orange",
            [None, "T42"],
        ),
        (
            "W10",
            "下側リレー右側から延びる橙線",
            [[551, 606], [577, 594], [605, 588], [622, 592]],
            0.0025,
            "orange",
            ["T44", None],
        ),
        (
            "W11",
            "中央束の桃色線",
            [[564, 515], [637, 516], [706, 494], [755, 491], [801, 506], [863, 529]],
            0.0017,
            "pink",
            [None, None],
        ),
        (
            "W12",
            "中央束の青色線",
            [[576, 520], [642, 521], [711, 502], [757, 505], [811, 526], [869, 538]],
            0.0017,
            "blue",
            [None, None],
        ),
        ("W13", "中央束の白色線", [[676, 517], [719, 537], [757, 537], [803, 538]], 0.0016, "ivory", [None, None]),
        (
            "W14",
            "中央束の黒色線",
            [[332, 437], [382, 467], [445, 490], [555, 491], [642, 511], [713, 528], [787, 526]],
            0.0020,
            "black",
            [None, None],
        ),
    ]
    wires = []
    for wire_id, label, points, diameter, color, adjacent in rows:
        wires.append(
            {
                "id": wire_id,
                "name_ja": label,
                "photo": "overview",
                "polyline_px": points,
                "display_diameter_m": diameter,
                "display_color": color,
                "nearby_features": adjacent,
                "model_id": "REF_" + wire_id,
                "physical_endpoints": [None, None],
                "electrical_group": None,
                "occluded_continuation_resolved": False,
                "note_ja": "可視区間の手動トレース。近傍部品への電気接続を確定せず、隠れた続きは描かない。",
            }
        )
    for index, x in enumerate((416, 570, 714, 1010, 1153)):
        for side, dx in enumerate((-9, 12)):
            wire_id = f"WI{index + 1}{side + 1}"
            wires.append(
                {
                    "id": wire_id,
                    "name_ja": f"補機口{index + 1}内側の線出口{side + 1}",
                    "photo": "overview",
                    "polyline_px": [[x + dx, 834], [x + dx, 815], [x + dx + 2, 797]],
                    "display_diameter_m": 0.003,
                    "display_color": "orange",
                    "nearby_features": [f"I{index + 1:02d}", None],
                    "model_id": "REF_" + wire_id,
                    "physical_endpoints": [None, None],
                    "electrical_group": None,
                    "occluded_continuation_resolved": False,
                    "note_ja": "見える2本の出口。裏面視点の左右から1番/2番の極性を推定せず、端子品番も未選定。",
                }
            )
    return wires


def required_functions():
    rows = [
        ("REQ_K", "主接触器", 1, ["P02"], "写真の本体へ対応。電力端子・制御・補助接点を別に管理。"),
        ("REQ_PC_RLY", "プリチャージリレー", 1, [], "写真のP03/P04のどちらかは未特定。"),
        ("REQ_D_RLY", "放電リレー", 1, [], "写真のP03/P04のどちらかは未特定。"),
        ("REQ_PC_RES", "プリチャージ抵抗", 1, [], "存在は公式記載。写真位置・端末方式は未特定。"),
        ("REQ_D_RES", "放電抵抗", 1, [], "存在は公式記載。写真位置・端末方式は未特定。"),
        ("REQ_MAIN_FUSE", "主400 Aヒューズ", 1, [], "存在は公式記載。写真中の本体位置・固定形式は未特定。"),
    ]
    for i, (function, current) in enumerate(
        (("Heater 1", 20), ("AC", 30), ("Heater 2", 20), ("Charger", 30), ("DC-DC", 10))
    ):
        rows.append(
            (
                f"REQ_AF{i + 1}",
                f"補機{function}・{current} Aヒューズ",
                1,
                [],
                "P05/P06を含むが、5個の所在と系統別対応は未完了。",
            )
        )
    requirements = [
        {
            "id": identifier,
            "name_ja": name,
            "quantity": quantity,
            "matched_photo_ids": matched,
            "note_ja": note,
            "basis": "Ampere V1.1 pages 1-2",
            "not_located_is_not_omitted": True,
        }
        for identifier, name, quantity, matched, note in rows
    ]
    requirements.extend(
        [
            {
                "id": "REQ_MAIN_PORTS",
                "name_ja": "主2極接続口",
                "quantity": 2,
                "matched_photo_ids": ["P14", "P15"],
                "basis": "Ampere V1.1 pages 2-3",
            },
            {
                "id": "REQ_AUX_PORTS",
                "name_ja": "補機2極接続口",
                "quantity": 5,
                "matched_photo_ids": ["P16", "P17"],
                "basis": "3+2 functional bays, not five outer housings",
            },
            {
                "id": "REQ_INNER",
                "name_ja": "補機内側ハウジング",
                "quantity": 5,
                "matched_photo_ids": [f"I{i:02d}" for i in range(1, 6)],
                "basis": "Photo and TE 408-32095 / 2103245",
            },
            {
                "id": "REQ_LV",
                "name_ja": "低圧12極接続口",
                "quantity": 1,
                "matched_photo_ids": ["P18"],
                "basis": "Ampere V1.1 pages 2,4",
            },
        ]
    )
    return requirements


def electrical_groups():
    previous = json.loads((ROOT / "data/three_station_connection_groups_v01.json").read_text())
    groups = []
    for group in previous["connection_groups"]:
        groups.append(
            {
                "id": group["id"],
                "name_ja": group["name_ja"],
                "basis_ja": group["public_basis_ja"],
                "datasheet_pages": group["pages"],
                "lv_pins": group["lv_pins"],
                "physical_wires": None,
                "fastener_count": None,
                "photo_to_physical_net_complete": False,
            }
        )
    return groups


def document(data):
    text = [
        "# Ampere写真・部品・接続とモデルの対応 v01",
        "",
        "2026-09-15。内部構成の照合を工程動作より先に行う。",
        "",
        "## 状態",
        "",
        "公開資料で位置・接続を特定できた範囲と、未特定の範囲を残した静止再構成用台帳。",
        "完全な製造BOM・全配線図・実機成立の証明ではない。未特定部品を別の仮部品で埋めない。",
        "部品欄のP/I/Tは写真の識別対象、Jは見える締結特徴、Wは可視線区間。総数を製造部品数としない。",
        "",
        "## 写真の識別対象",
        "",
        "| ID | 対象 | 対応・未確認点 |",
        "|---|---|---|",
    ]
    text.extend(f"| {p['id']} | {p['name_ja']} | {p['note_ja']} |" for p in data["parts"])
    text.extend(
        [
            "",
            "## 写真だけでは所在を埋められない部品も全数管理",
            "",
            "| ID | 公開構成 | 数 | 対応先 |",
            "|---|---|---:|---|",
        ]
    )
    for row in data["required_functions"]:
        matched = ", ".join(row["matched_photo_ids"]) or "未特定"
        text.append(f"| {row['id']} | {row['name_ja']} | {row['quantity']} | {matched} |")
    text.extend(
        [
            "",
            "## 接続の扱い",
            "",
            "EC01〜EC13の全接続群を引き継ぐ。主回路、プリチャージ、放電、補機5系統、接触器駆動、",
            "リレー2系統駆動、接触器フィードバック、HVILを含む。群数は実配線本数ではない。",
            "可視線は途中で隠れた位置で止め、近くのねじへ勝手につながない。線色だけから極性を割り当てない。",
            "補機5口の各正負、LVの全12位置（うち6/12はReserved）を落とさず、物理経路は別に照合する。",
            "HVILの各口を通る順番、裏側の端末、共締めの順番、圧着・シール品番は未確定。",
            "",
            "## v03から取り下げる内容",
            "",
            "- 仮のオレンジ制御ブロックと受けを、実部品の嵌合として扱ったOP030-C。",
            "- サンプルS字線・2本の端子台を、写真の実配線として扱うこと。",
            "- 写真と違う位置の汎用リレー・白い直方体ヒューズ・抵抗・丸形部品の組付け。",
            "",
            "v03以下は保全。新しい静止モデルの推定寸法・未確定接続をアーム目標へ自動転用しない。",
            "工程順・把持対象・締結/差込方式は部品の対応を確定してから割り付ける。旧14秒を実タクトにしない。",
            "",
            "## 根拠",
            "",
            f"- [Ampere公式記事]({SUPPORT})、[公式V1.1]({PDF_URL})。",
            "- DSC02860-1（指定写真）、DSC02864（接続部詳細）、DSC02878（高さ・別角度）。",
            "- TE 2103340/2103346/2103245の公式図面・STEP、408-32095。",
            "- GX14、MX150、KLKDの公開例は探索候補であり、Ampere採用品として確定しない。",
            "",
            "静止形状の位置・高さ・太さのうち公開寸法のないものは表示用推定。写真の遠近・高さの差を含み、",
            "製作寸法、公差、締結品質、把持安定性、連続干渉の判定ではない。正式な物理判定はV12独立経路。",
            "",
        ]
    )
    text.extend(["## 全接続群", "", "| ID | 内容 | 実配線との対応 |", "|---|---|---|"])
    text.extend(f"| {row['id']} | {row['name_ja']} | 未完了 |" for row in data["electrical_groups"])
    text.extend(["", "## LV12位置", "", "| ピン | 公開図の名称 |", "|---|---|"])
    text.extend(f"| {pin} | {name} |" for pin, name in data["lv_pin_map"].items())
    text.extend(["", "## 未対応箇所", ""])
    text.extend("- " + item for item in data["unresolved"])
    text.extend(["", "## 可視部分の未完了項目", ""])
    text.extend("- " + item for item in data["remaining_visual_coverage"])
    text.append("")
    return "\n".join(text)


def main():
    output = ROOT / "data/hvjb_photo_correspondence_v01.json"
    if output.exists():
        raise FileExistsError(output)
    parts, wires, joints = observed_parts(), wire_segments(), fasteners()
    ids = [r["id"] for r in parts + wires + joints]
    assert len(ids) == len(set(ids))
    assert all(j["feature_parent"] in ids for j in joints)
    assert all(p is None or p in ids for wire in wires for p in wire["nearby_features"])
    photos = {}
    for view, number, filename in (
        ("overview", 1, "DSC02860-1.jpg"),
        ("detail", 2, "DSC02864.jpg"),
        ("side", 3, "DSC02878.jpg"),
    ):
        path = PHOTOS / f"ampere_product_photo_{number}.jpg"
        photos[view] = {
            "file": str(path.relative_to(ROOT)),
            "url": "https://ampereev.com/wp-content/uploads/2022/05/" + filename,
            "sha256": digest(path),
            "size_px": [1620, 1080],
        }
    data = {
        "revision": "v01",
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "status": "partial_photo_correspondence_before_motion",
        "photo_basis": "overview",
        "photos": photos,
        "parts": parts,
        "visible_wire_segments": wires,
        "visible_fastener_features": joints,
        "required_functions": required_functions(),
        "electrical_groups": electrical_groups(),
        "lv_pin_map": {
            "1": "Contactor Feedback",
            "2": "Contactor 12V",
            "3": "Pre-Charge Relay 12V",
            "4": "Discharge Relay 12V",
            "5": "HVIL In",
            "6": "Reserved",
            "7": "Contactor Feedback",
            "8": "Contactor Ground",
            "9": "Pre-Charge Relay Ground",
            "10": "Discharge Relay Ground",
            "11": "HVIL Out",
            "12": "Reserved",
        },
        "display_coordinate_mapping": {
            "origin_px": [790, 535],
            "px_per_m": 4200,
            "axes": "photo right +X; photo up +Y; Z is estimated separately",
            "kind": "display_registration_only_not_photogrammetric_measurement",
        },
        "unresolved": [
            "主ヒューズ本体の場所・型式・固定方式。",
            "補機ヒューズ5個の全所在と各口への割当。見えるP05/P06の2個だけで済ませない。",
            "2個の抵抗の所在・端末・支持と、P07/P08の機能。",
            "上/下リレーのプリチャージ・放電対応と、各端末の実経路。",
            "主接触器・主2極ハウジング・LV12極ハウジングの正確な型式。",
            "金属導体の隠れた連続性・部品分割・ねじの共締め積層。",
            "各線の両端、圧着端子、シール、HVILの内部接続順。",
            "部品の高さ・厚さ・加工寸法・入荷サブアセンブリと支持状態。",
        ],
        "coverage_checklist": [
            "筐体・蓋・シール・ボス",
            "主接触器と電力/コイル/補助端末",
            "プリチャージと放電のリレー/抵抗",
            "主1+補機5ヒューズと保持部",
            "剛体バスバー・絶縁支持・カバー",
            "主2極×2・補機2極×5・LV12極",
            "内側ハウジング・金属端子・シール",
            "配線・丸端子・差込端末・熱収縮",
            "ねじ・ナット・座金・共締め",
            "完成品の蓋と表示",
        ],
        "motion_created": False,
        "all_physical_connections_resolved": False,
        "all_visible_features_traced": False,
        "remaining_visual_coverage": [
            "左奥・右奥の束と前方で交差する細線は、一本ごとの追跡が未完了。",
            "端子の金属部、熱収縮チューブ、支持部、座金を個別部品として分離する照合が未完了。",
            "配線の手動トレースは照合用下書き。写真の境界・隠れ位置を再確認する必要がある。",
        ],
        "documented_header_mounting": {
            "P16": {"hole_count": 8, "thread": "M4", "fastener_part_number": None},
            "P17": {"hole_count": 6, "thread": "M4", "fastener_part_number": None},
            "basis": "TE customer drawings; separate from visible interior fastener features",
        },
        "physical_acceptance_verdict": None,
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "analysis/hvjb_photo_correspondence_v01.md").write_text(document(data))
    audit = {
        "data_sha256": digest(output),
        "part_feature_count": len(parts),
        "visible_wire_segment_count": len(wires),
        "visible_fastener_feature_count": len(joints),
        "electrical_group_count": len(data["electrical_groups"]),
        "unlocated_required_items": [r["id"] for r in data["required_functions"] if not r["matched_photo_ids"]],
        "all_ids_unique": True,
        "dangling_feature_references": [],
        "formal_verdict": None,
    }
    (ROOT / "audit/hvjb_photo_catalog_v01.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print("PHOTO_CATALOG_CREATED", json.dumps(audit, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
