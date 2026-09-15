# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Extend the photo inventory using source-specific observations, not inferred nets."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "f11765ce6b142d49701bab3108b383176c638dfd933d83f57d0c3ed0f76bb27b"
FUSES = {
    "P05": {"column": 0, "level": 0, "rect": [550, 453, 365, 124], "label": "Littelfuse / HEV", "current": None},
    "P06": {"column": 1, "level": 0, "rect": [1150, 405, 380, 126], "label": "Littelfuse / HEV 30A", "current": 30},
    "P19": {
        "column": 0,
        "level": 1,
        "rect": [555, 565, 360, 110],
        "label": "SCHURTER / 20A（系列文字は判読保留）",
        "current": 20,
    },
    "P20": {
        "column": 1,
        "level": 1,
        "rect": [1155, 520, 340, 117],
        "label": "SCHURTER / 20A（系列文字は判読保留）",
        "current": 20,
    },
    "P21": {"column": 0, "level": 2, "rect": [560, 674, 350, 108], "label": "Littelfuse / HEV 10A", "current": 10},
}


def new_part(identifier, label, profile, photo, rect, note):
    return {
        "id": identifier,
        "model_id": "REF_" + identifier,
        "name_ja": label,
        "profile": profile,
        "photo": photo,
        "rect_px": rect,
        "note_ja": note,
        "part_number": None,
        "physical_bom_quantity": None,
        "manufacturing_dimensions_m": None,
    }


def parts(data):
    rows = {row["id"]: row for row in data["parts"]}
    rows["P07"].update(
        name_ja="後方の補機ヒューズ取付板・上端",
        profile="fuse_panel",
        note_ja="動画内の拡大写真で左3段・右2段を確認。板の全輪郭・材質・厚さ・支持方法は未確定。",
    )
    rows["P08"].update(
        name_ja="主ヒューズ上の黒い被覆",
        note_ja="公式解説の指示位置と円筒ヒューズに対応する被覆。材質・断面寸法・固定方法は未確定。",
    )
    for identifier, fuse in FUSES.items():
        if identifier not in rows:
            row = new_part(
                identifier,
                f"補機ヒューズ・{'左' if fuse['column'] == 0 else '右'}側の{fuse['level'] + 1}段目",
                "fuse",
                "fuse_detail",
                fuse["rect"],
                "",
            )
            data["parts"].append(row)
            rows[identifier] = row
        row = rows[identifier]
        row.setdefault("observations", {})["fuse_detail"] = {"rect_px": fuse["rect"]}
        row["display_fuse_column"] = fuse["column"]
        row["display_fuse_level"] = fuse["level"]
        row["observed_marking"] = fuse["label"]
        row["observed_current_a"] = fuse["current"]
        row["electrical_branch"] = None
        row["note_ja"] = (
            "公式映像35秒の挿入写真で本体・両端キャップを識別。表示文字: "
            + fuse["label"]
            + "。注文品番・各接続口への実配線は未確定。P05の電流値を帯色から補完しない。"
        )
    main = new_part(
        "P22",
        "中央被覆内の主ヒューズ本体",
        "main_fuse",
        "overview",
        [690, 351, 313, 165],
        "2024年公式解説68秒の指示位置と72秒の単体例から対応。胴・平板端子は表示推定、注文品番は未特定。",
    )
    main["observations"] = {
        "overview": {"rect_px": main["rect_px"]},
        "main_pointer": {"rect_px": [825, 364, 403, 156]},
        "main_sample": {"rect_px": [802, 599, 155, 74]},
    }
    main["identity_basis"] = "manufacturer explanation and pointer; exact sample-to-installed order code unresolved"
    data["parts"].append(main)
    for i, (joint, end) in enumerate(
        (
            ("J09", [315, 690]),
            ("J10", [391, 693]),
            ("J11", [449, 701]),
            ("J12", [639, 780]),
            ("J13", [702, 777]),
            ("J14", [524, 282]),
            ("J17", [1155, 252]),
        )
    ):
        j = next(j for j in data["visible_fastener_features"] if j["id"] == joint)
        x, y = j["center_px"]
        rect = [min(x, end[0]) - 12, min(y, end[1]) - 12, abs(x - end[0]) + 24, abs(y - end[1]) + 24]
        row = new_part(
            f"L{i + 1:02d}",
            f"{joint}近傍の丸端子・黒い端末被覆",
            "lug_sleeve",
            "overview",
            rect,
            "金属環と被覆の可視外形を追加。線の遠端・端子品番・被覆材質・共締めの全積層は未確定。",
        )
        row.update(joint=joint, sleeve_direction_px=end, observations={"overview": {"rect_px": rect}})
        data["parts"].append(row)
    for row in data["parts"]:
        row.setdefault("observations", {row["photo"]: {"rect_px": row["rect_px"]}})
    for identifier in ("P09", "P10"):
        rows[identifier]["note_ja"] = (
            "詳細写真にある端子側の受け面と縦板を表示。v01の平板直方体を修正。隠れた曲げ・部品境界は未確定。"
        )


def joints(data):
    mapping = {
        "J14": ("P05", -1, [481, 499]),
        "J15": ("P05", 1, [982, 473]),
        "J16": ("P06", -1, [1090, 452]),
        "J17": ("P06", 1, [1549, 418]),
        "J18": ("P19", -1, [481, 592]),
        "J19": ("P19", 1, [982, 576]),
        "J20": ("P20", -1, [1090, 555]),
        "J21": ("P20", 1, [1549, 515]),
        "J22": ("P21", -1, [481, 690]),
        "J23": ("P21", 1, [982, 685]),
    }
    lookup = {r["id"]: r for r in data["visible_fastener_features"]}
    for identifier, (fuse, side, point) in mapping.items():
        if identifier not in lookup:
            row = {
                "id": identifier,
                "model_id": "REF_" + identifier,
                "feature_parent": fuse,
                "photo": "fuse_detail",
                "center_px": point,
                "fastener_specification": None,
                "joint_stack": None,
                "observations": {},
            }
            data["visible_fastener_features"].append(row)
            lookup[identifier] = row
        row = lookup[identifier]
        row["observations"]["fuse_detail"] = {"center_px": point}
        row["fuse_side"] = side
    for row in data["visible_fastener_features"]:
        row["display_head_form"] = "hex_nut_on_stud" if row["id"] in {"J01", "J02"} else "round_socket_head"
        row["description_ja"] = (
            "可視外形: "
            + ("スタッドと六角ナット" if row["id"] in {"J01", "J02"} else "丸い頭部と六角穴")
            + "。規格・寸法・裏側・共締めは未確定。ヒューズ板上の締結軸を板面の法線へ修正。"
        )


def requirements(data):
    for row in data["required_functions"]:
        if row["id"] == "REQ_MAIN_FUSE":
            row["matched_photo_ids"] = ["P22"]
            row["note_ja"] = "中央被覆内へ位置対応。単体例の胴・端子形状を表示推定。注文品番・固定積層は未確定。"
        elif row["id"].startswith("REQ_AF"):
            row["location_candidates"] = list(FUSES)
            row["note_ja"] = (
                "物理5個はP05/P06/P19/P20/P21で確認。各補機口までの線を追い切れておらず、系統割当は未確定。"
            )
        elif row["id"] in {"REQ_PC_RES", "REQ_D_RES"}:
            row["note_ja"] = "2025年組立品で2個の所在が見える。指定2022年写真への同一版・位置対応は未確定。"
    for identifier, name, quantity, note in (
        (
            "REQ_AUX_POWER_CONTACTS",
            "補機内側の電力コンタクト",
            10,
            "各口2個。MCP 2.8、線径/嵌合先に対応する注文品番は未選定。",
        ),
        ("REQ_AUX_HVIL_CONTACTS", "補機内側のHVILコンタクト", 10, "各口2個。MQS、回路順序・注文品番は未確定。"),
    ):
        data["required_functions"].append(
            {
                "id": identifier,
                "name_ja": name,
                "quantity": quantity,
                "matched_photo_ids": [],
                "note_ja": note,
                "basis": "TE 408-32095 Rev B, Figures 1/3 and assembly sections",
                "not_located_is_not_omitted": True,
            }
        )
    data["assembly_dependencies"] = [
        {
            "id": "AD01",
            "name_ja": "切断・被覆除去・適合端子の圧着",
            "basis": "TE 408-32095 / 2025 video 87-129 s",
            "complete": False,
            "missing_ja": "線種・長さ・端子注文品番・加工条件",
        },
        {
            "id": "AD02",
            "name_ja": "内側ハウジングへ電力2端子＋HVIL2端子を挿入・保持確認",
            "basis": "TE 408-32095",
            "complete": False,
            "missing_ja": "端子の現物CAD、全線の端末対応",
        },
        {
            "id": "AD03",
            "name_ja": "キーを合わせて内側ハウジングを外側へ挿入",
            "basis": "TE 408-32095",
            "complete": False,
            "missing_ja": "ラッチ着座・抜去と工具進入の確認",
        },
        {
            "id": "AD04",
            "name_ja": "ヒューズ板で5系統を配線・締結してから箱内へ設置する組立例",
            "basis": "2025 video 28-87, 142-153 s",
            "complete": False,
            "missing_ja": "採用版の板寸法・配線先・把持対象・締結仕様。自動化工程順としては未確定",
        },
        {
            "id": "AD05",
            "name_ja": "主/補機/LV/HVIL接続、導通・検査、蓋とシール",
            "basis": "Ampere V1.1 / 2025 video",
            "complete": False,
            "missing_ja": "実配線図・共締め・検査仕様・蓋の部品構成",
        },
    ]


def document(data):
    lines = [
        "# 写真・部品・接続の照合 v02",
        "",
        "2026-09-15。工程動作に先行する静止再構成の続き。",
        "",
        "## 今回確かめた範囲",
        "",
        "- Ampere公式組立映像35秒の挿入写真で、補機ヒューズが左3段・右2段にあることを確認。",
        "  上2個の下へP19/P20/P21を追加。系統別の線は追跡未完了なので5口への割当はまだ行わない。",
        "- 公式解説68秒が指定写真の主ヒューズ付近を指し、72秒で円筒胴・両端平板端子の単体例を提示。",
        "  P08の被覆とP22の内部本体を区別した。単体の注文品番と詳細寸法は未確定。",
        "- バスバーの立上り、接触器側面の縦リブ、丸ねじ頭/六角ナット、可視丸端子と黒い端末被覆を修正。",
        "- TE内側ハウジングは各口2電力＋2HVILコンタクト。5口分の必要数を別々に記録し、空の樹脂を完成ポートとしない。",
        "",
        "## 根拠の版を混ぜない",
        "",
        "[2025年組立映像](https://www.youtube.com/watch?v=Sm_D-vmNYqc)には抵抗2個を取り付けた下板が映る。",
        "ただし実作業中の製造版と2022年の指定写真が同一である証拠は得ていない。抵抗配置・配線経路を転記しない。",
        "映像の挿入写真、実作業部分、[2024年の解説](https://www.youtube.com/watch?v=oXPIRNZ4xcs)を分けて記録。",
        "自動字幕は探索用。端子やヒューズの品番を字幕から確定しない。",
        "",
        "## 部品等の対応",
        "",
        "| ID | 対象 | 根拠・未確認 |",
        "|---|---|---|",
    ]
    lines.extend(f"| {r['id']} | {r['name_ja']} | {r['note_ja']} |" for r in data["parts"])
    lines.extend(["", "## 必須構成と接続を省略しない", "", "| 項目 | 数 | 対応/未確認 |", "|---|---:|---|"])
    for row in data["required_functions"]:
        lines.append(f"| {row['name_ja']} | {row['quantity']} | {row.get('note_ja', row.get('basis', ''))} |")
    lines.extend(["", "## 動作へ進む前の未対応", ""])
    lines.extend("- " + value for value in data["unresolved"])
    lines.extend(["", "## 工程から落とさない処理", ""])
    lines.extend(f"- {r['id']} {r['name_ja']}。未確定: {r['missing_ja']}。" for r in data["assembly_dependencies"])
    lines.extend(
        [
            "",
            "## 測定と判定の範囲",
            "",
            "TE以外の寸法・内部高さ・線径・板厚・穴/被覆の外形は表示用推定。写真から製造寸法を求めたものではない。",
            "5個のヒューズが見つかったことと、5系統の配線が確定したことは別。共締め積層とHVIL順序も未確定。",
            "モデルIDの一対一対応は登録した特徴についての検査であり、全実部品を網羅した証明ではない。",
            "旧v01とv03以下は保全。新たな工程動作・動画は作らない。物理妥当性の正式判定はV12独立経路。",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    output = ROOT / "data/hvjb_photo_correspondence_v02_p02.json"
    if output.exists():
        raise FileExistsError(output)
    base = ROOT / "data/hvjb_photo_correspondence_v01.json"
    assert digest(base) == BASE_SHA
    data = json.loads(base.read_text())
    evidence = json.loads((ROOT / "data/hvjb_video_evidence_v02.json").read_text())
    for row in data["parts"] + data["visible_fastener_features"] + data["visible_wire_segments"]:
        row["observations"] = {row["photo"]: {k: row[k] for k in ("rect_px", "center_px", "polyline_px") if k in row}}
    data["revision"], data["observed_at"] = "v02", datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    data["previous_catalog_sha256"] = BASE_SHA
    data["video_evidence"] = evidence
    for key, row in evidence["frames"].items():
        data["photos"][key] = dict(row, url=evidence["sources"][row["source"]]["url"])
    parts(data)
    joints(data)
    requirements(data)
    data["physical_aux_fuses"] = {"observed_count": 5, "photo_ids": list(FUSES), "port_assignment_complete": False}
    data["unresolved"] = [
        "主ヒューズの注文品番・詳細寸法・取付部材・共締め積層。位置は中央被覆内へ対応済み。",
        "補機ヒューズ5個から5口への一対一配線。物理所在の確認は系統割当の完了ではない。",
        "2022年写真における抵抗2個の位置・支持・接続。2025年実作業品との同一版確認。",
        "P03/P04のプリチャージ・放電への対応と各端末の行き先。",
        "主接触器・主2極ハウジング・LV12極ハウジングの正確な型式。",
        "全可視/隠れ配線の両端、主/補機/LV/HVIL端子・シール、全口を通るHVIL順序。",
        "導体の隠れた連続性・部品分割・支持と締結積層。",
        "製造寸法・公差・線長・被覆と部品の支持状態。蓋・シールの詳細。",
    ]
    data["remaining_visual_coverage"] = [
        "左奥・右奥の束と交差する細線は一本ごとの追跡が未完了。",
        "丸端子と被覆7領域を追加したが、写真中の全端末・座金・支持を網羅した数量ではない。",
        "未見の金属コンタクトや内部抵抗を根拠のない形状・配線で埋めない。",
    ]
    all_rows = data["parts"] + data["visible_fastener_features"] + data["visible_wire_segments"]
    identifiers = [r["id"] for r in all_rows]
    assert len(identifiers) == len(set(identifiers))
    assert all(row["observations"] for row in all_rows)
    assert all(view in data["photos"] for row in all_rows for view in row["observations"])
    assert len(data["electrical_groups"]) == 13 and len(data["lv_pin_map"]) == 12
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "analysis/hvjb_photo_correspondence_v02.md").write_text(document(data))
    audit = {
        "catalog_sha256": digest(output),
        "previous_unchanged": digest(base) == BASE_SHA,
        "feature_count": len(identifiers),
        "part_features": len(data["parts"]),
        "fastener_features": len(data["visible_fastener_features"]),
        "wire_segments": len(data["visible_wire_segments"]),
        "aux_fuse_count": 5,
        "aux_fuse_to_port_assignment_complete": False,
        "required_functions": len(data["required_functions"]),
        "electrical_groups": 13,
        "lv_positions": 12,
        "all_physical_connections_resolved": False,
        "motion_created": False,
        "formal_verdict": None,
    }
    (ROOT / "audit/hvjb_photo_catalog_v02_p02.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print("PHOTO_CATALOG_CREATED", json.dumps(audit, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
