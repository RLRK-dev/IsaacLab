# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Record visible wire entrances without promoting them to electrical endpoints."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/hvjb_photo_correspondence_v03_p01.json"
NOTES = ROOT / "data/hvjb_wire_observations_v03.json"


def terminal_regions(data, notes):
    parts = {row["id"]: row for row in data["parts"]}
    for identifier, region in notes["terminal_regions"].items():
        row = parts[identifier]
        row["rect_px"] = region["rect_px"]
        row["observations"] = {
            "overview": {"rect_px": region["rect_px"]},
            "detail": {"rect_px": region["detail_rect"]},
        }
        row["display_entry_px"] = region["entry_px"]
        row["display_opening"] = region["opening"]
        row["note_ja"] = (
            "原本に合わせて外装位置・線の入口を訂正。開口を持つ外装を表示する。"
            "外装の識別は金属コンタクト・リレー極番号・PC/放電の機能対応を確定しない。"
        )
    parts["I03"]["observations"]["overview"]["visibility"] = "occluded_expected_region"
    parts["I03"]["photo_visibility"] = "occluded; expected region only, not traced outer contour"
    parts["I03"]["note_ja"] = (
        "キーEの必要部品を公式CADで配置。指定写真では当該入口が隠れ、破線は推定所在。"
        "前版の一律生成線WI31/WI32を可視一覧から退役。接点・線・端子の必要数は維持。"
    )


def unknown_end(point):
    return {
        "feature_id": None,
        "evidence": "trace_stops; no visible terminal assigned",
        "label_ja": "追跡終了・先は未確認",
        "point_px": point,
        "metal_terminal_id": None,
        "cavity_number": None,
        "electrical_node": None,
    }


def entry_end(point, feature, bound):
    return {
        "feature_id": feature,
        "evidence": "visible_exterior_entry; hidden metal contact unresolved",
        "label_ja": "見える入口・端末外装: " + feature,
        "point_px": point,
        "metal_terminal_id": None,
        "cavity_number": None,
        "electrical_node": None,
        "bind_display_geometry": bound,
    }


def wire_rows(data, notes):
    data["retired_visible_wire_segments"] = [
        {"id": identifier, "reason_ja": "5口へ一律生成した短線。指定写真の当該口で可視根拠を確認できない。"}
        for identifier in notes["retired_visible_ids"]
    ]
    wires = [r for r in data["visible_wire_segments"] if r["id"] not in notes["retired_visible_ids"]]
    lookup = {row["id"]: row for row in wires}
    for identifier, trace in notes["traces"].items():
        if identifier not in lookup:
            row = {
                "id": identifier,
                "model_id": "REF_" + identifier,
                "photo": "overview",
                "display_diameter_m": trace["diameter"],
                "display_color": "orange",
                "name_ja": trace["name_ja"],
                "physical_endpoints": [None, None],
                "electrical_group": None,
                "nearby_features": [None, None],
                "occluded_continuation_resolved": False,
            }
            wires.append(row)
            lookup[identifier] = row
        row = lookup[identifier]
        row["polyline_px"] = trace["points"]
        row["name_ja"] = trace.get("name_ja", row["name_ja"])
        row["observations"] = {"overview": {"polyline_px": trace["points"]}}
        if "detail_points" in trace:
            row["observations"]["detail"] = {"polyline_px": trace["detail_points"]}
    for identifier, points in notes["port_entry_traces"].items():
        lookup[identifier]["polyline_px"] = points
        lookup[identifier]["observations"] = {"overview": {"polyline_px": points}}
    for row in wires:
        identifier, points = row["id"], row["polyline_px"]
        row["observed_trace_ends"] = [unknown_end(points[0]), unknown_end(points[-1])]
        trace = notes["traces"].get(identifier)
        if trace:
            side, feature = trace["entry"]
            row["observed_trace_ends"][side] = entry_end(points[0 if side == 0 else -1], feature, True)
        elif identifier in notes["port_entry_traces"]:
            row["observed_trace_ends"][0] = entry_end(points[0], "I0" + identifier[2], False)
        reviewed = trace is not None or identifier in notes["port_entry_traces"]
        row["trace_review_state"] = "rechecked_visible_fragment" if reviewed else "inherited_fragment_not_rechecked"
        row["note_ja"] = (
            "v03で原本の可視区間を再照合。" if reviewed else "前版の区間を保持。今回の端末照合は未実施。"
        ) + "入口の外装対応と電気端子の対応を分離。隠れた先・端子品番・極番号は未確定。"
        row["physical_endpoints"] = [None, None]
        row["electrical_group"] = None
    data["visible_wire_segments"] = wires
    data["candidate_continuations"] = notes["candidate_continuations"]


def document(data):
    lines = [
        "# 写真・部品・可視配線の照合 v03",
        "",
        "公式写真 [DSC02860-1](https://ampereev.com/wp-content/uploads/2022/05/DSC02860-1.jpg) と",
        "[DSC02864](https://ampereev.com/wp-content/uploads/2022/05/DSC02864.jpg) の可視区間を追加照合。",
        "入口外装の対応を電気端子の確定と分ける。完全な実配線表・製造BOMではない。",
        "",
        "## 写真の線と端末入口",
        "",
        "| 区間 | 対象 | 端1 | 端2 | 今回の読取り |",
        "|---|---|---|---|---|",
    ]
    for row in data["visible_wire_segments"]:
        ends = row["observed_trace_ends"]
        status = "再照合" if row["trace_review_state"].startswith("rechecked") else "前版保持・今回は未照合"
        lines.append(f"| {row['id']} | {row['name_ja']} | {ends[0]['label_ja']} | {ends[1]['label_ja']} | {status} |")
    lines.extend(
        [
            "",
            "## 描き足していない接続",
            "",
            "W04→WI52、W05→WI42は視覚的な続きの候補。重なる区間の同一線・金属端末は未確認。",
            "隠れた橋渡しを作らず、候補ボタンで両区間を並べて表示する。極性やヒューズ系統は割り当てない。",
            "",
            "## 訂正と未完了",
            "",
            "- T31〜T44の8外装を原本へ合わせ直し、開口と可視線入口を表示。金属端子の新規型式採用はしない。",
            "- WI31/WI32は一律生成の短線だったため可視一覧から退役。I03は資料/CADによる必要部品として保持。",
            "- 補機電力10コンタクト/HVIL10コンタクトの必要数は不変。退役は部品の省略ではない。",
            "- 外装入口と線端の表示位置合わせは写真推定。線長・最小曲げ半径・CAD係合・導通の測定ではない。",
            "- 主/補機端子、抵抗位置、PC/放電リレー割当、HVIL順序、共締め、シール、支持は依然未確定。",
            "- 新たな工程動作・動画を作成しない。旧版を保全する。正式物理妥当性はV12独立経路。",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    notes = json.loads(NOTES.read_text())
    source = ROOT / notes["source_catalog"]
    assert digest(source) == notes["source_catalog_sha256"]
    data = json.loads(source.read_text())
    data.update(
        revision="v03",
        observed_at=datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        previous_catalog_sha256=digest(source),
        wire_observations_sha256=digest(NOTES),
    )
    terminal_regions(data, notes)
    wire_rows(data, notes)
    data["remaining_visual_coverage"] = [
        "線入口20か所は外装までの対応。内部金属端子・極番号・遠端の確定とは別。",
        "WI31/WI32を可視一覧から退役。I03の破線は資料上必要な部品の推定所在。",
        "継承した7区間は今回の端末照合未実施。交差束・隠れた続き・全端末は追跡未完了。",
    ]
    rows = data["parts"] + data["visible_fastener_features"] + data["visible_wire_segments"]
    identifiers = {row["id"] for row in rows}
    assert len(rows) == len(identifiers)
    entries = [end for row in data["visible_wire_segments"] for end in row["observed_trace_ends"] if end["feature_id"]]
    assert all(end["feature_id"] in identifiers for end in entries)
    assert all(row["physical_endpoints"] == [None, None] for row in data["visible_wire_segments"])
    assert all(not candidate["adopted"] for candidate in data["candidate_continuations"])
    for row in rows:
        for view, observation in row["observations"].items():
            assert view in data["photos"]
            for point in observation.get("polyline_px", []):
                assert all(
                    0 <= value < bound for value, bound in zip(point, data["photos"][view]["size_px"], strict=True)
                )
    assert digest(source) == notes["source_catalog_sha256"]
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "analysis/hvjb_photo_correspondence_v03.md").write_text(document(data))
    report = {
        "catalog_sha256": digest(OUTPUT),
        "previous_catalog_unchanged": True,
        "feature_count": len(rows),
        "part_features": len(data["parts"]),
        "fastener_features": len(data["visible_fastener_features"]),
        "wire_segments": len(data["visible_wire_segments"]),
        "visible_exterior_entry_observations": len(entries),
        "display_entry_bindings": sum(end["bind_display_geometry"] for end in entries),
        "retired_visible_ids": notes["retired_visible_ids"],
        "electrical_groups": len(data["electrical_groups"]),
        "lv_positions": len(data["lv_pin_map"]),
        "required_functions": len(data["required_functions"]),
        "all_physical_connections_resolved": False,
        "all_visible_features_traced": False,
        "motion_created": False,
        "formal_verdict": None,
    }
    (ROOT / "audit/hvjb_photo_catalog_v03_p01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PHOTO_CATALOG_CREATED", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
