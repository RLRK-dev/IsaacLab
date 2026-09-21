# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Integrate accepted work locations with the existing line and hand-role plan."""

from __future__ import annotations

import copy
import csv
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
OUT = ROOT / "output"
W, H = 1600, 1100
FONT = "HeiseiKakuGo-W5"
INK, BLUE, GREEN, GOLD, GRAY = "#183749", "#226b97", "#26745c", "#a75a13", "#526976"
DRAWN = []
NAME = "HVJB_ライン全体と動画用工程表_v03_20260921"

# These are explanatory views, not new trajectories, factory precedence or durations.
SCENES = [
    (
        "S01",
        ["D00"],
        "供給",
        "20枠から空筐体をパレットへ",
        "XYZ / H06筐体",
        "筐体を支持・位置決めしてからハンド開放",
        "4-11",
    ),
    (
        "S02",
        ["D01", "D81"],
        "準備",
        "線材・端末準備、部品・ボルト補給",
        "準備・補給設備",
        "入荷済み範囲、空容器回収の仕事を残す",
        "該当単独場面なし",
    ),
    (
        "S03",
        ["D10", "D11"],
        "外・A",
        "下板部品の保持中固定・局所配線",
        "A主腕 + 共用補助※ / T-A",
        "接触器・リレー・抵抗等。自由端の案内を継続",
        "11-22",
    ),
    (
        "S04",
        ["D20", "D21"],
        "外・B",
        "補機ヒューズ板側の組付け・配線締結",
        "B主腕 + 共用補助※ / T-B",
        "板側締結を完了。反対端の接続は別に扱う",
        "11-22",
    ),
    (
        "S05",
        ["D12", "D22"],
        "外・C入口",
        "A/Bユニットと自由端を別々に受け渡す",
        "A/B主腕 → C主腕 / 支持",
        "案内役の占有と次の支持先を示す",
        "22-35",
    ),
    (
        "S06",
        ["D30"],
        "外・C",
        "板合わせ・保持中の板間ねじ固定",
        "C主腕 H07 / F-C / T-C",
        "採用済み仮手順。実物の固定点は未確認",
        "35-40",
    ),
    (
        "S07",
        ["D31"],
        "外・C",
        "支持を残して搬送把持へ切り替える",
        "C主腕 H07 → H06ユニット",
        "支持F-Cと自由端案内を維持して持ち替える",
        "35-40",
    ),
    (
        "S08",
        ["D40"],
        "外 → 内",
        "まとめたユニットを筐体に搭載する",
        "C主腕 / C専用補助",
        "本体の支持引継ぎ後も自由端案内を続ける",
        "40-48",
    ),
    (
        "S09",
        ["D42"],
        "内・C",
        "搭載後の内部工具作業を別場面で示す",
        "対象・手先未特定 / T-C",
        "隠れたねじを追加せず、未特定箇所を表示",
        "40-48に統合された表現",
    ),
    (
        "S10",
        ["D45"],
        "側壁・C",
        "内側ハウジングと線を開口へ通す",
        "H05内側 / C専用補助※",
        "通した後の外側支持を引き継ぐまで保持",
        "48-55",
    ),
    (
        "S11",
        ["D50"],
        "側壁・C",
        "外側ヘッダーの設置・ねじ固定",
        "H05外側 / 内側保持役※ / T-C",
        "外側取得と内側保持を同じ手に重ねない",
        "48-55",
    ),
    (
        "S12",
        ["D60"],
        "内・C",
        "バスバー・丸端子等を保持して締結",
        "H03 / 補助H04※ / T-C",
        "導体と線を別に保持。主ヒューズは工程未確定",
        "55-62",
    ),
    (
        "S13",
        ["D61"],
        "C・位置未定",
        "残るLV/HVIL・不可視端末を別管理",
        "個別の対象・手先を照合",
        "未追跡の端末を、接続済みとして描かない",
        "該当単独場面なし",
    ),
    (
        "S14",
        ["D70", "D71"],
        "後工程",
        "シール・蓋・必要検査を示す",
        "H07カバー候補 / 検査設備",
        "内部の残接続を省かない。検査との順序は未定",
        "62-69",
    ),
    (
        "S15",
        ["D81"],
        "同段復路",
        "完成品を載せたパレットを供給側へ戻す",
        "1段コンベア",
        "同じ高さ・経路を逆方向へ戻す",
        "69-74",
    ),
    (
        "S16",
        ["D80"],
        "元の収納枠",
        "同じXYZで元の空き枠へ完成品を戻す",
        "XYZ / H06筐体",
        "XYZの保持確認後、パレット保持を解放",
        "74-82",
    ),
]

CARDS = [
    (
        "1  ユニット受渡し",
        "D12 / D22 · 筐体外",
        "本体 → 支持F-C / C主腕",
        "自由端 → 次の案内役",
        "本体と端末は別々に引き継ぐ。\n補助のB→C同行は比較案のまま。",
        "A/BからCへ",
    ),
    (
        "2  板間ねじ固定",
        "D30 · 筐体外",
        "C主腕 H07：ヒューズ板保持",
        "F-C：下板支持 / T-C：締付",
        "姿勢を保って板間を固定する採用済み仮手順。\n接合具・ねじ位置・本数は未確認。",
        "保持しながら締結",
    ),
    (
        "3  搬送用に持ち替え",
        "D31 · 筐体外",
        "H07板保持 → H06ユニット搬送",
        "F-Cの支持 / 自由端案内を継続",
        "H06筐体用とは別の用途・接触面。\n自動交換器や交換方法は未選定。",
        "支持 → 把持 → 開放",
    ),
    (
        "4  まとめて筐体搭載",
        "D40 · 外から内へ",
        "C主腕：ユニット本体",
        "C専用補助：自由端案内",
        "筐体内の支持へ荷重を渡し、指を開いて退避。\n内部受け形状と退避経路は未確定。",
        "本体と線を別に扱う",
    ),
    (
        "5  箱内工具作業",
        "D42 · 搭載後の内側",
        "T-C：箱内へ工具接近",
        "対象保持 / 自由端案内を残す",
        "映像では工具先端が隠れている。\n特定の下板ねじとして動作を埋めない。",
        "対象未特定を明示",
    ),
    (
        "6  開口通過とヘッダー",
        "D45 / D50 · 側壁",
        "H05内側：端末保持 → 支持引継ぎ",
        "H05外側：ヘッダー保持 / T-C",
        "内側端末を持った手で外側ヘッダーを取らない。\n全対象の締結と工具退避まで外側保持。",
        "内側保持と外側取得を分担",
    ),
    (
        "7  残る接続・共締め",
        "D60 / D61 · 主に内側",
        "H03：導体 / H04：線の保持候補",
        "T-C：部材をそろえて締結",
        "主ヒューズ、LV/HVIL個別端末は未確定。\n残る自由端があれば案内役の占有を残す。",
        "工具退避 → 指の開放・退避",
    ),
    (
        "8  後工程と回収",
        "D70 / D71 / D81 / D80",
        "蓋・シール / 必要検査",
        "完成品パレット → 供給XYZ",
        "元のストッカ枠へ戻し、空パレットは供給側へ。\n蓋と検査の詳細順・設備分担は未確定。",
        "パレット保持 → XYZ把持",
    ),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def collect():
    provenance = json.loads((ROOT / "inputs/source_identity.json").read_text())
    for row in provenance:
        assert sha(ROOT / "inputs" / row["file"]) == row["sha256"], row["file"]
    hands = json.loads((ROOT / "inputs/hand_plan.json").read_text())
    location = json.loads((ROOT / "inputs" / provenance[-1]["file"]).read_text())
    video = json.loads((ROOT / "inputs/concept_v02.json").read_text())
    assert hands["selected_role_allocation"]["selected_plan"] == "S5_AB"
    assert hands["logistics"]["deck_count"] == 1 and hands["logistics"]["shared_stock_slots"] == 20
    by_id = {row["id"]: row for row in hands["cards"]}
    loc_id = {row["id"]: row for row in location["task_locations"]}
    assert len(by_id) == len(loc_id) == 20 and by_id.keys() == loc_id.keys()
    assert {key for scene in SCENES for key in scene[1]} == by_id.keys()
    scenes = []
    for identifier, tasks, place, title, actors, hold, old_window in SCENES:
        scenes.append(
            {
                "id": identifier,
                "tasks": tasks,
                "place_ja": place,
                "title_ja": title,
                "actors_ja": actors,
                "hold_or_limit_ja": hold,
                "previous_video_navigation_ja": old_window,
                "new_duration_s": None,
                "trajectory": None,
                "sequence_kind": "explanatory_storyboard_not_factory_schedule",
            }
        )
    rows = []
    for card in hands["cards"]:
        identifier = card["id"]
        row = copy.deepcopy(card)
        row["location_record"] = copy.deepcopy(loc_id[identifier])
        row["scene_ids"] = [scene["id"] for scene in scenes if identifier in scene["tasks"]]
        row["current_hand_display_ja"] = card["hands_label_ja"]
        if identifier == "D60":
            row["current_hand_display_ja"] = "H03 / 補助H04候補。H08主ヒューズの工程は未確定"
        elif identifier == "D61":
            row["current_hand_display_ja"] = "対象別に照合（元H05候補）。端末の内外位置は未確定"
        rows.append(row)
    result = {
        "revision": "hvjb_line_process_v03_20260921",
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "builder_sha256": sha(Path(__file__)),
        "source_identity": provenance,
        "scope_ja": "既存ライン図・手先計画へ、確認済みの筐体内外区分を反映。動画用の場面表まで。",
        "roles": copy.deepcopy(hands["resources"]),
        "selected_role_allocation": copy.deepcopy(hands["selected_role_allocation"]),
        "logistics": copy.deepcopy(hands["logistics"]),
        "cards": rows,
        "scenes": scenes,
        "preserved_hand_plan": copy.deepcopy(hands),
        "preserved_location_coverage": copy.deepcopy(location["coverage"]),
        "previous_video_phases_unmodified": copy.deepcopy(video["phases"]),
        "source_video_note_ja": "旧v02の秒は探索用。新動画の秒数、機械動作時間、タクトではない。",
        "ordering_limits_ja": [
            "S03/S04はA/Bの担当区分。補助を必要とする同時要求は把持開始前に調整する。",
            "A/Bの別ワーク処理は方針。共用補助のC同行・待ちを無視して連続並行を保証しない。",
            "S05のA/B受渡し順、S12/S13の各端末順、S14の蓋と検査の詳細順は未選定。",
            "S02/S15のD81は補給・回収と復路の別表示。同じ仕事を新しい2仕事へ数え直さない。",
        ],
        "preserved_open_interfaces": copy.deepcopy(location["unresolved"]),
        "new_robot_or_fixture_selected": False,
        "motion_created": False,
        "new_video_created": False,
        "physical_acceptance_verdict": None,
    }
    assert len({row["operation"] for row in rows}) == 12
    assert result["preserved_hand_plan"] == hands
    return result


def text(c, x, y, value, size=18, color=INK):
    c.setFont(FONT, size)
    c.setFillColor(HexColor(color))
    for i, part in enumerate(value.split("\n")):
        baseline = H - y - i * size * 1.36
        width = pdfmetrics.stringWidth(part, FONT, size)
        assert x >= 0 and x + width < W - 28 and baseline > 18, part
        c.drawString(x, baseline, part)
        DRAWN.append({"page": c.getPageNumber(), "text": part, "x": x, "baseline": baseline, "width": width})


def box(c, x, y, width, height, fill="#edf5f8", stroke="#ccdce5"):
    c.setLineWidth(1.2)
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor(stroke))
    c.roundRect(x, H - y - height, width, height, 8, fill=1, stroke=1)


def line(c, x1, y1, x2, y2, color=BLUE, width=2):
    c.setLineWidth(width)
    c.setStrokeColor(HexColor(color))
    c.line(x1, H - y1, x2, H - y2)


def arrow(c, x1, y1, x2, y2, color=BLUE):
    line(c, x1, y1, x2, y2, color, 2.5)
    if x1 == x2:
        d = 1 if y2 > y1 else -1
        line(c, x2 - 6, y2 - 10 * d, x2, y2, color, 2.5)
        line(c, x2 + 6, y2 - 10 * d, x2, y2, color, 2.5)
    else:
        d = 1 if x2 > x1 else -1
        line(c, x2 - 10 * d, y2 - 6, x2, y2, color, 2.5)
        line(c, x2 - 10 * d, y2 + 6, x2, y2, color, 2.5)


def arm(c, x, y, color=BLUE):
    # Reuse the previous overview's generic role symbol, with no reach dimensions.
    points = [(x, y), (x - 12, y - 27), (x + 12, y - 49), (x + 35, y - 30)]
    for a, b in zip(points, points[1:]):
        line(c, *a, *b, color, 5)
    c.setFillColor(HexColor("#ffffff"))
    c.setStrokeColor(HexColor(color))
    for px, py in points[:-1]:
        c.circle(px, H - py, 5, stroke=1, fill=1)
    line(c, x - 18, y + 7, x + 18, y + 7, color, 5)


def header(c, page, title, subtitle):
    text(c, 55, 60, title, 30)
    text(c, 55, 100, subtitle, 17, GRAY)
    text(c, 1450, 57, f"{page} / 3", 17, GRAY)
    line(c, 55, 1032, 1545, 1032, "#ccdce5", 1)
    text(
        c,
        55,
        1054,
        "工程と役割の無寸法図。機種・実配置・関節軌道・所要時間・物理成立を確定する図ではありません。",
        13,
        GRAY,
    )
    text(
        c,
        55,
        1077,
        "資料：既存v02全体図・v01手先計画、支持引継ぎ図、筐体内外の組立区分。20仕事と未確定項目を保持。",
        12,
        GRAY,
    )
    text(c, 1410, 1077, "2026-09-21", 12, GRAY)


def overview(c):
    header(
        c,
        1,
        "ライン全体：外組みのA/Bと、合流・搭載のC",
        "A/B/Cは別ワークを並行処理する方針。補助の同時要求と引継ぎを考慮し、設備台数やタクトを省略計算しません。",
    )
    box(c, 55, 170, 255, 230)
    text(c, 75, 204, "部品・端末準備", 24)
    text(c, 75, 248, "線材加工・圧着\nハウジング端子挿入\n部品・ボルト供給", 21)
    text(c, 75, 365, "A/Bへ供給。加工範囲は未定", 15, GRAY)
    arrow(c, 310, 277, 337, 277)
    for x, name, body, hand, resource in [
        (345, "A｜下板の外組み", "接触器・リレー・抵抗等\n下板側で完結する配線", "H01/H02 → H04等", "主担当A：1腕"),
        (
            800,
            "B｜ヒューズ板の外組み",
            "補機ヒューズ板側の部品\n板側の配線端末を締結",
            "H02/H08 → H04等",
            "主担当B：1腕",
        ),
    ]:
        box(c, x, 170, 415, 230)
        text(c, x + 20, 204, name, 24, BLUE)
        text(c, x + 20, 248, body, 21)
        text(c, x + 20, 317, hand, 18)
        text(c, x + 20, 367, resource, 21, BLUE)
        arm(c, x + 335, 370)
    box(c, 1250, 170, 295, 230, "#fff4e8")
    text(c, 1270, 204, "A/B共用補助：1腕", 23, GOLD)
    text(c, 1270, 250, "必要な独立保持を担当\nH04 / H05等の候補\n保持中は別セルへ移らない", 18)
    text(c, 1270, 367, "補助の要求は開始前に調整", 16, GOLD)
    line(c, 553, 400, 553, 442)
    line(c, 1008, 400, 1008, 442)
    line(c, 553, 442, 1008, 442)
    arrow(c, 780, 442, 780, 475)
    text(c, 55, 145, "T-A / T-B / T-C：据置工具・ボルト供給を別計上。採用品番・軸数は未定。", 17, GRAY)
    box(c, 365, 480, 855, 360, "#f3f7f9")
    text(c, 385, 519, "C｜主担当1腕 ＋ 専用補助1腕", 27)
    for x, y, title, body, tint, col in [
        (385, 549, "搭載前：筐体外で結合", "板合わせ・保持中の板間ねじ固定\n支持を残して搬送把持へ", "#e8f1f8", BLUE),
        (810, 549, "搭載：一体で筐体へ", "ユニット本体と自由端を別々に扱う\n筐体側の支持へ引き継ぐ", "#eef6ef", GREEN),
        (385, 689, "搭載後：筐体内", "箱内工具作業・残る導体や端末接続\n未特定の締結点は別表示", "#eef6ef", GREEN),
        (810, 689, "搭載後：側壁", "開口通過・外側ヘッダー取付\n外側の保持と内側端末を分担", "#fff4e8", GOLD),
    ]:
        box(c, x, y, 390, 119, tint)
        text(c, x + 15, y + 34, title, 22, col)
        text(c, x + 15, y + 70, body, 17)
    text(c, 385, 829, "各枠は場所と役割の区分。詳細な見せ方は2・3ページ。", 15, GRAY)
    box(c, 55, 525, 275, 315)
    text(c, 75, 563, "OP010｜供給・収納", 23)
    text(c, 75, 603, "共用XYZ + H06筐体", 21, BLUE)
    for i in range(20):
        x, y = 77 + (i % 4) * 24, 641 + (i // 4) * 26
        box(c, x, y, 19, 17, "#c6e5d2" if i == 0 else "#ffffff")
    text(c, 190, 671, "20枠共用", 18)
    text(c, 190, 708, "元の空き枠へ\n完成品を戻す", 16, GREEN)
    text(c, 75, 802, "供給と収納は同じXYZ", 18)
    box(c, 1260, 525, 285, 315, "#fff4e8")
    text(c, 1280, 563, "後工程", 24)
    text(c, 1280, 610, "シール・蓋\n必要検査・記録\n完成品をパレットで返却", 20)
    text(c, 1280, 739, "蓋と検査の順・設備分担\n個別検査条件は未定", 17, GOLD)
    arrow(c, 330, 750, 359, 750)
    arrow(c, 1220, 750, 1254, 750)
    box(c, 55, 884, 1490, 91, "#edf6ef")
    text(c, 75, 915, "1段・同じ高さのパレット往復搬送", 23, GREEN)
    arrow(c, 650, 930, 1500, 930, GREEN)
    arrow(c, 1500, 930, 650, 930, GREEN)
    text(
        c,
        75,
        954,
        "往路：空筐体 / 復路：完成品を載せた同じパレット。図は経路の説明で、下段・第2搬送路はありません。",
        17,
    )
    text(
        c,
        55,
        1010,
        "主ヒューズP22・被覆P08、各LV/HVIL端末、内部固定点は未確定。補機ヒューズ板と一括して割り当てません。",
        18,
        GOLD,
    )
    c.showPage()


def handoffs(c):
    header(
        c,
        2,
        "Cで何を持ち続け、どこへ渡すか",
        "H番号は対象別の手先用途群です。同じH06でも、筐体用と内部ユニット搬送用の接触面は別に確認します。",
    )
    for i, (title, task, main, support, note, boundary) in enumerate(CARDS):
        x, y = 55 + (i % 2) * 770, 148 + (i // 2) * 208
        box(c, x, y, 720, 194, "#f1f6f9" if i < 4 else "#f1f6f2")
        text(c, x + 18, y + 33, title, 24)
        text(c, x + 360, y + 32, task, 16, GRAY)
        text(c, x + 18, y + 69, main, 19, BLUE)
        text(c, x + 18, y + 97, support, 19, GREEN)
        text(c, x + 18, y + 128, note, 16)
        line(c, x + 18, y + 168, x + 700, y + 168, "#ccdce5", 1)
        text(c, x + 18, y + 187, boundary, 15, GOLD)
    text(
        c,
        55,
        1000,
        "C専用補助は搭載完了だけで解放しません。保持の終了・手先切替・次の把持は、実際の支持引継ぎに対応させます。",
        17,
        GRAY,
    )
    c.showPage()


def storyboard(c, data):
    header(
        c,
        3,
        "動画用の場面表：内外の区分が伝わる16場面",
        "場面番号は説明順です。A/B並行処理、受渡し順、残接続や検査の詳細順序・新動画の時間は確定していません。",
    )
    columns = (55, 145, 390, 905, 1230)
    widths = (85, 240, 510, 320, 315)
    for x, width, title in zip(
        columns, widths, ("場面", "仕事 / 場所", "画面で示す作業", "担当・手先", "保持・未確定の表示"), strict=True
    ):
        box(c, x, 137, width, 39, "#e3edf2")
        text(c, x + 8, 164, title, 18)
    for i, row in enumerate(data["scenes"]):
        y = 181 + i * 48
        values = [
            row["id"],
            "/".join(row["tasks"]) + "\n" + row["place_ja"],
            row["title_ja"],
            row["actors_ja"],
            row["hold_or_limit_ja"],
        ]
        for x, width, value in zip(columns, widths, values, strict=True):
            box(c, x, y, width, 45, "#f3f7f9" if i % 2 == 0 else "#ffffff")
            parts = []
            for source_line in value.split("\n"):
                chunk = ""
                for char in source_line:
                    if pdfmetrics.stringWidth(chunk + char, FONT, 14) > width - 17:
                        parts.append(chunk)
                        chunk = char
                    else:
                        chunk += char
                parts.append(chunk)
            assert len(parts) <= 2, (row["id"], parts)
            text(c, x + 8, y + (19 if len(parts) > 1 else 28), "\n".join(parts), 14)
    text(
        c,
        55,
        983,
        "※必要な独立保持に使う候補。元の20仕事を全件対応し、D81の補給・回収と復路は別場面に表示しています。",
        17,
        GRAY,
    )
    text(
        c,
        55,
        1010,
        "主ヒューズや見えない接続の施工を創作せず未確定表示にする。新動画は工程PNGからreview.mp4の1種類のみ。",
        17,
        GOLD,
    )
    c.showPage()


def main():
    (OUT / "pdf").mkdir(parents=True, exist_ok=True)
    data = collect()
    save(OUT / "line_process_plan.json", data)
    with (OUT / "20仕事_場所と手先.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["仕事", "元工程", "場所", "主担当", "手先用途", "補助", "保持引継ぎ", "場面", "未確定"])
        for row in data["cards"]:
            writer.writerow(
                [
                    row["id"],
                    row["operation"],
                    row["location_record"]["location_ja"],
                    row["primary_label_ja"],
                    row["current_hand_display_ja"],
                    row["assistance_label_ja"],
                    row["transfer_ja"],
                    "/".join(row["scene_ids"]),
                    row["unresolved_ja"],
                ]
            )
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    pdf = OUT / "pdf" / f"{NAME}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    c.setTitle("HVJB ライン全体と動画用工程表 v03")
    overview(c)
    handoffs(c)
    storyboard(c, data)
    c.save()
    save(
        OUT / "document_audit.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "builder_sha256": sha(Path(__file__)),
            "pdf_sha256": sha(pdf),
            "plan_sha256": sha(OUT / "line_process_plan.json"),
            "csv_sha256": sha(OUT / "20仕事_場所と手先.csv"),
            "coverage": {"tasks": 20, "operations": 12, "scenes": 16},
            "drawn_text": DRAWN,
            "physical_acceptance_verdict": None,
        },
    )
    print("LINE_PROCESS_PLAN_COMPLETE pages=3 tasks=20 scenes=16")
    print(f"PDF SHA256 {sha(pdf)}")


if __name__ == "__main__":
    main()
