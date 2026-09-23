# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw a whole-line guide linked to the preserved product and job inventory."""

from __future__ import annotations

import argparse
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
NAME = "HVJB_ライン全体と組立場所_v04_20260923"
HELPER = ROOT.parent / "hvjb-line-process-v03-20260921/build_review.py"
SPEC = importlib.util.spec_from_file_location("preserved_drawing", HELPER)
assert SPEC is not None and SPEC.loader is not None
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)
W, H = D.W, D.H
A, B, C, GOLD, INK, GRAY = "#296DB3", "#9E478F", "#198772", "#A7610F", D.INK, D.GRAY
PALE = {A: "#edf4fb", B: "#f8eff6", C: "#eef7f4", GOLD: "#fff5e8", GRAY: "#f3f6f8"}
PAGES = 6


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(c, x, y, value, size=20, color=INK):
    D.text(c, x, y, value, size, color)


def wrapped(c, x, y, value, width, size=19, color=INK):
    lines = []
    for paragraph in value.split("\n"):
        current = ""
        for char in paragraph:
            if current and pdfmetrics.stringWidth(current + char, D.FONT, size) > width:
                lines.append(current)
                current = ""
            current += char
        lines.append(current)
    text(c, x, y, "\n".join(lines), size, color)
    return y + len(lines) * size * 1.36


def card(c, x, y, width, height, color=C):
    D.box(c, x, y, width, height, fill=PALE[color], stroke="#d4e0e5")
    D.line(c, x + 10, y + 10, x + 10, y + height - 10, color, 4)


def picture(c, name, x, y, width, height):
    path = ROOT / "figures/product_final" / (name + ".png")
    c.drawImage(str(path), x, H - y - height, width, height, preserveAspectRatio=True, anchor="c", mask="auto")


def heading(c, page, title, subtitle):
    text(c, 48, 60, title, 31)
    text(c, 48, 104, subtitle, 19, GRAY)
    D.line(c, 48, 127, 1552, 127, "#b6cbd6", 1)
    D.line(c, 48, 1035, 1552, 1035, "#c7d7de", 1)
    text(
        c, 48, 1061, "工程・担当の説明図。寸法、実機軌道、実タクト、物理的な成立を確定する図ではありません。", 15, GRAY
    )
    text(c, 48, 1078, "既存20仕事・92写真特徴を継承 / 元資料と詳細対応は同梱CSV・JSON / 2026-09-23", 13, GRAY)
    text(c, 1494, 1078, f"{page}/{PAGES}", 13, GRAY)


def stock(c):
    card(c, 48, 191, 278, 643, GRAY)
    text(c, 72, 230, "OP010 / 供給・収納", 23, C)
    text(c, 72, 273, "同じXYZを共用", 25)
    text(c, 72, 307, "H06：筐体用", 21)
    for row in range(5):
        for col in range(4):
            index = row * 4 + col + 1
            x, y = 74 + col * 53, 342 + row * 53
            D.box(c, x, y, 42, 42, fill="#c9e9dc" if index == 1 else "#ffffff", stroke="#bbcdd6")
            text(c, x + 7, y + 28, f"{index:02d}", 19, C if index == 1 else GRAY)
    text(c, 73, 642, "20区画の共用ストッカ", 21)
    wrapped(c, 73, 686, "空筐体を取り出した枠を空けておき、同じ製品の完成品を戻す。", 220, 21)
    text(c, 73, 799, "筐体 ⇄ パレット", 23, C)


def assembly_station(c, x, code, title, view, body, hands, color):
    card(c, x, 191, 443, 313, color)
    text(c, x + 28, 233, f"{code}  {title}", 27, color)
    picture(c, view, x + 16, 253, 233, 184)
    wrapped(c, x + 250, 281, body, 172, 20)
    text(c, x + 29, 460, hands, 20, color)
    D.arm(c, x + 369, 470, color)
    text(c, x + 29, 489, "主担当 1腕 + 据置工具", 17, GRAY)


def overview(c):
    heading(
        c,
        1,
        "箱外でA/Bを組み、Cでまとめて筐体へ搭載する",
        "工程の位置・部品群・5腕の役割を同じ色で対応。A/B/Cは既存の担当区分です。",
    )
    stock(c)
    assembly_station(
        c, 359, "A", "下板の外組み", "outside_A", "接触器・リレー・抵抗等\n下板側の配線", "H01/H02 → H04等", A
    )
    assembly_station(
        c, 829, "B", "ヒューズ板の外組み", "outside_B", "補機ヒューズ板\n板側の配線端末を締結", "H02/H08 → H04等", B
    )
    card(c, 442, 535, 745, 86, GOLD)
    text(c, 466, 570, "A/B共用補助：1腕", 23, GOLD)
    text(c, 466, 603, "必要な保持を分担。保持中に別のセルへ移らない。", 20)
    D.arrow(c, 403, 504, 403, 652, A)
    D.arrow(c, 1228, 504, 1228, 652, B)
    card(c, 359, 660, 913, 174, C)
    text(c, 382, 698, "C  主担当1腕 + 専用補助1腕", 27, C)
    steps = ["箱外で板合わせ", "支持上で持ち替え", "一体で筐体へ搭載", "側壁・内部の\n残接続"]
    for index, label in enumerate(steps):
        x = 382 + index * 221
        D.box(c, x, 720, 197, 78, fill="#ffffff")
        wrapped(c, x + 13, 751, label, 170, 21, C)
        if index < 3:
            D.arrow(c, x + 200, 758, x + 217, 758, C)
    text(c, 382, 823, "本体の支持と、線・端末の案内は別に引き継ぐ。", 18, GRAY)
    card(c, 1305, 191, 247, 643, GOLD)
    text(c, 1329, 234, "準備・後工程", 25, GOLD)
    wrapped(c, 1329, 285, "部品・線材・端末の準備\nボルト供給・空容器回収", 194, 21)
    D.line(c, 1329, 422, 1529, 422, GOLD, 1)
    wrapped(c, 1329, 469, "シール・蓋\n試験への接続\n試験・記録\n解除・支持引継ぎ", 194, 22)
    wrapped(c, 1329, 655, "入荷範囲、蓋と試験の順、担当設備は未確定。", 194, 20, GOLD)
    D.arrow(c, 1276, 745, 1296, 745, C)
    D.arrow(c, 330, 745, 350, 745, C)
    card(c, 48, 873, 1504, 111, C)
    text(c, 73, 912, "コンベアは1段。パレットは同じ高さ・同じ経路を往復", 26, C)
    D.arrow(c, 606, 955, 1517, 955, C)
    D.arrow(c, 1517, 955, 606, 955, C)
    text(c, 73, 956, "往路：空筐体 / 復路：完成品", 21)
    text(c, 48, 1016, "5腕は組立役の数です。XYZ・締付工具・供給・搬送・検査を含む設備台数ではありません。", 19, GRAY)
    c.showPage()


def product_mapping(c):
    heading(
        c,
        2,
        "完成時の製品モデルから、どこを扱う工程か追う",
        "色は既存の工程検討先。灰色は周辺部品で、箱内で組む順番を表した図ではありません。",
    )
    panels = [
        (
            "A / 接触器・リレーの表示例",
            "outside_A",
            A,
            "P02 / P03 / P04",
            "抵抗等も外組み工程に含む。写真で見えない形状は補完しない。",
        ),
        (
            "B / 補機ヒューズ板",
            "outside_B",
            B,
            "P05 / P06 / P07 / P19-P21",
            "板側の配線端末は箱外で締結。反対端の接続とは分ける。",
        ),
        (
            "C / 後付け導体の表示例",
            "after_insertion_bus",
            C,
            "P09-P13",
            "導体・丸端子・共締めの残接続。\n個別の積層は未確定。",
        ),
        (
            "C / 外側ヘッダー",
            "external_headers",
            C,
            "P16：3口 / P17：2口",
            "OP020の設置・ねじ固定。内側ハウジングや試験プラグとは別部品。",
        ),
        (
            "未確定 / 主ヒューズ",
            "main_fuse_unassigned",
            GOLD,
            "P08：被覆 / P22：主ヒューズ",
            "補機ヒューズ5個と一括しない。所属・支持・取付順が未確定。",
        ),
        (
            "未確定 / 主口・LVの細部",
            "main_and_lv_unassigned",
            GOLD,
            "P14 / P15 / P18",
            "機能は台帳に保持。固有部品・物理端末・試験相手側は未確定。",
        ),
    ]
    for index, (title, image, color, ids, body) in enumerate(panels):
        x, y = 48 + index % 3 * 508, 167 + index // 3 * 418
        card(c, x, y, 488, 398, color)
        text(c, x + 24, y + 37, title, 23, color)
        picture(c, image, x + 18, y + 51, 452, 233)
        text(c, x + 24, y + 306, ids, 19, color)
        wrapped(c, x + 24, y + 340, body, 440, 19)
    text(
        c,
        48,
        1020,
        "表示モデル92項目を保持。見えない実配線・製造BOM・完成写真と映像の同一製造版は未確定です。",
        18,
        GRAY,
    )
    c.showPage()


def support_symbol(c, x, y, kind):
    D.box(c, x + 15, y + 100, 255, 18, fill="#aebfc7")
    if kind == "port":
        D.box(c, x + 133, y + 20, 16, 80, fill="#7d939e")
        D.box(c, x + 75, y + 52, 48, 32, fill="#bcdad2")
        D.box(c, x + 168, y + 41, 62, 49, fill="#f4b66d")
        D.arrow(c, x + 112, y + 20, x + 189, y + 20, C)
        text(c, x + 39, y + 148, "内側保持", 17, C)
        text(c, x + 178, y + 148, "外側保持", 17, GOLD)
        return
    D.box(c, x + 44, y + 75, 160, 19, fill="#b4d1e8")
    if kind in {"join", "grip", "insert"}:
        D.box(c, x + 176, y + 31, 20, 47, fill="#ddb3d3")
    if kind in {"join", "tool", "release"}:
        D.line(c, x + 102, y + 8, x + 102, y + 67, GRAY, 7)
    D.line(c, x + 46, y + 34, x + 46, y + 70, C, 7)
    D.line(c, x + 201, y + 34, x + 201, y + 70, C, 7)
    if kind == "release":
        D.arrow(c, x + 31, y + 57, x + 31, y + 5, C)
        D.arrow(c, x + 220, y + 57, x + 220, y + 5, C)
    elif kind == "insert":
        D.arrow(c, x + 239, y + 3, x + 239, y + 90, C)
    elif kind == "tool":
        text(c, x + 122, y + 45, "?", 28, GOLD)
    elif kind == "grip":
        D.arrow(c, x + 44, y + 130, x + 202, y + 130, C)
    else:
        D.line(c, x + 202, y + 60, x + 268, y + 20, GOLD, 5)


def support_sequence(c):
    heading(
        c,
        3,
        "Cで支持が途切れないよう、本体と自由端を別に追う",
        "下の図は保持の役割を表す記号です。爪形状・ねじ位置・許容荷重を決めた図ではありません。",
    )
    rows = [
        ("1  A/Bから受ける", "D12 / D22", "handoff", "本体は受けへ。自由端は次の案内役へ渡してから前の保持を解除。"),
        ("2  箱外で板間固定", "D30", "join", "C主腕が板を保持し、工具で固定する採用済み仮手順。実物の接合点は未確認。"),
        ("3  支持上で持ち替え", "D31", "grip", "受けの支持と端末案内を残す。板用H07からユニット用H06へ切替を比較。"),
        ("4  一体で筐体へ搭載", "D40", "insert", "C主腕は本体、C補助は自由端を扱う。筐体側へ本体の支持を渡して開放。"),
        ("5  内側工具作業", "D42", "tool", "映像で先端が隠れた工程。対象未特定のまま残し、ねじを描き足さない。"),
        (
            "6  開口・ヘッダー",
            "D45 / D50",
            "port",
            "内側端末と外側ヘッダーは別の手で扱う。工具退避まで外側保持を続ける。",
        ),
        (
            "7  導体・端末の接続",
            "D60 / D61",
            "join",
            "導体とケーブルを保持して締結。各線の端点・積層は個別に照合する。",
        ),
        (
            "8  工具退避・開放",
            "対象の締結終了後",
            "release",
            "工具が抜けてから指を開く。該当する両腕は同時に上昇。残る自由端は保持継続。",
        ),
    ]
    for index, (title, ids, symbol, body) in enumerate(rows):
        x, y = 48 + index % 4 * 382, 167 + index // 4 * 393
        card(c, x, y, 358, 369, C)
        text(c, x + 22, y + 38, title, 23, C)
        text(c, x + 22, y + 70, ids, 18, GRAY)
        support_symbol(c, x + 30, y + 81, symbol)
        wrapped(c, x + 22, y + 271, body, 307, 20)
    card(c, 48, 969, 1504, 52, GOLD)
    text(
        c,
        71,
        1002,
        "1つの手で全端末を持てるとは未確認です。自由端ごとの個体・支持先・必要な保持数を残しています。",
        20,
        GOLD,
    )
    c.showPage()


def all_jobs(c, data):
    heading(
        c,
        4,
        "20仕事を、作業場所・手先・引継ぎに一対一で対応",
        "工程枠を残すことと、個々の施工が確定していることは別です。詳細は同梱の20仕事CSVで確認できます。",
    )
    hand_labels = {
        "D00": "H06 筐体",
        "D01": "加工・供給の仕様未定",
        "D10": "H01 / H02",
        "D11": "H04 / H05内側",
        "D12": "H06 下板用を比較",
        "D20": "H02 / H08",
        "D21": "H04 / H05内側",
        "D22": "H07 板用を比較",
        "D30": "H07 板用を比較",
        "D31": "H07 → H06ユニットを比較",
        "D40": "H06 ユニット用を比較",
        "D42": "対象・手先未特定",
        "D45": "H05 内側",
        "D50": "H05 外側",
        "D60": "H03 / 補助H04候補",
        "D61": "対象別に照合",
        "D70": "H07 カバー候補",
        "D71": "試験接続用は比較中",
        "D80": "H06 筐体",
        "D81": "容器用手先は未選定",
    }
    for index, row in enumerate(data["jobs"]):
        x, y = 48 + (index // 10) * 766, 159 + (index % 10) * 83
        color = data["colors"][row["group"]]
        card(c, x, y, 738, 76, color if color in PALE else GRAY)
        text(c, x + 22, y + 24, row["id"] + "  " + row["title_ja"], 21, color)
        text(c, x + 22, y + 47, row["location_ja"] + " / " + row["primary_ja"], 15)
        text(c, x + 425, y + 47, hand_labels[row["id"]], 15, GRAY)
        transfer = row["transfer_ja"]
        if pdfmetrics.stringWidth(transfer, D.FONT, 15) <= 689:
            text(c, x + 22, y + 68, transfer, 15, GRAY)
        else:
            text(c, x + 22, y + 68, "引継ぎの詳細：同梱CSVの " + row["id"], 15, GRAY)
    text(
        c,
        48,
        1020,
        "D81の補給・回収と復路は同じ仕事の別場面。工程・部品を数え直して省略や増設をしていません。",
        18,
        GRAY,
    )
    c.showPage()


def parallel_roles(c):
    heading(
        c,
        5,
        "3STの並行処理と、共用補助の占有を分けて考える",
        "説明用のある瞬間：Cは前の一式、A/Bは次の一式を準備。実時間の工程表・タクト算定ではありません。",
    )
    columns = [
        (48, "A：次の下板", A, "主腕 + 共用補助で\n必要な部品を保持", "共用補助がAを支援中の例"),
        (557, "B：次のヒューズ板", B, "主腕だけでできる準備\n補助が要る保持は開始待ち", "保持の同時要求は開始前に調整"),
        (1066, "C：前の一式", C, "主腕 + 専用補助で\n合流・搭載・残接続", "A/B共用補助のC同行は未採用"),
    ]
    for x, title, color, body, foot in columns:
        card(c, x, 171, 486, 248, color)
        text(c, x + 25, 213, title, 26, color)
        text(c, x + 25, 268, body, 23)
        D.arm(c, x + 408, 343, color)
        text(c, x + 25, 385, foot, 18, GRAY)
    card(c, 48, 454, 1504, 112, GOLD)
    text(c, 72, 494, "A/B共用補助は、前の支持引継ぎ・開放・退避・必要な交換を終えてから次の仕事へ。", 24, GOLD)
    text(c, 72, 533, "保持途中の兼務はしません。固定工具・ボルト供給・支持台の役割も、腕の数とは別に残します。", 21)
    text(c, 48, 621, "C補助の担当は、筐体への搭載終了だけでは終わらない", 26, C)
    labels = [
        ("D31", "持ち替え"),
        ("D40", "搭載"),
        ("D42", "箱内工具"),
        ("D45", "開口通過"),
        ("D50", "ヘッダー"),
        ("D60", "主接続"),
        ("D61", "LV/HVIL"),
    ]
    for index, (code, label) in enumerate(labels):
        x = 220 + index * 190
        D.box(c, x, 653, 177, 78, fill="#eef7f4" if index < 5 else "#fff5e8")
        text(c, x + 18, 683, code, 22, C if index < 5 else GOLD)
        text(c, x + 18, 715, label, 20)
    text(c, 48, 783, "C専用補助", 23, C)
    D.box(c, 220, 754, 937, 70, fill="#c8e7dc")
    text(c, 247, 798, "自由端の支持先へ引き継ぐまで占有を残す", 25, C)
    D.box(c, 1170, 754, 367, 70, fill="#fff0d7")
    text(c, 1191, 798, "残る端末ごとに必要性を確認", 20, GOLD)
    text(c, 220, 859, "各欄の幅は時間ではありません。全区間で同一の腕が必須と確定した意味でもありません。", 18, GRAY)
    card(c, 48, 902, 1504, 107, GRAY)
    text(c, 72, 940, "手先交換も仕事に含める", 24)
    text(c, 72, 980, "H06筐体用とユニット用、H05内側と外側は別用途。自動交換器・機種・実台数は未選定です。", 21)
    c.showPage()


def cpa_symbol(c, x, closing):
    D.box(c, x, 500, 142, 32, fill="#e7ad70")
    D.box(c, x + 145, 493, 21, 45, fill="#8299a4")
    D.box(c, x + (107 if closing else 43), 483, 30, 18, fill="#7cbfaa")
    if closing:
        D.arrow(c, x + 45, 475, x + 132, 475, C)
    else:
        D.arrow(c, x + 133, 475, x + 46, 475, GOLD)
    text(c, x, 551, "プラグ本体", 14, GRAY)
    text(c, x + 137, 551, "ヘッダー", 14, GRAY)
    text(c, x + 222, 494, "緑の小片：CPA", 17, GRAY)
    text(c, x + 222, 526, "一般操作の方向を示す記号図", 16, GRAY)


def after_process(c, data):
    heading(
        c,
        6,
        "後工程は「つなぐ・調べる・外す・戻す」を分けて残す",
        "D70の蓋・シールと、D71の試験は順序未定。ここでは必要な仕事と接続解除の一般操作を示します。",
    )
    phases = [
        ("支持を引き継ぐ", "本体と線を支える"),
        ("試験に接続", "口・相手側は要選定"),
        ("設備で試験・記録", "条件・合否値は未定"),
        ("解除して引き渡す", "本体を持って抜く"),
    ]
    for index, (title, body) in enumerate(phases):
        x = 48 + index * 383
        card(c, x, 166, 359, 124, C)
        text(c, x + 22, 208, title, 25, C)
        text(c, x + 22, 251, body, 20)
        if index < 3:
            D.arrow(c, x + 361, 229, x + 379, 229, C)
    text(c, 48, 337, "補機5口のHVA280：CPAの一般操作を公式資料で追加確認", 25, C)
    card(c, 48, 365, 717, 194, C)
    text(c, 74, 407, "接続後 / CPA付き型", 24, C)
    text(c, 74, 449, "完全嵌合後、CPAをヘッダー側へ押す。", 23)
    cpa_symbol(c, 99, closing=True)
    card(c, 789, 365, 763, 194, GOLD)
    text(c, 813, 407, "解除前 / CPA付き型", 24, GOLD)
    text(c, 813, 449, "電源無効化後、CPAを反対へ引いて開く。", 23)
    cpa_symbol(c, 841, closing=False)
    steps = ["主ラッチ操作", "中間停止まで引戻し", "副ラッチ操作", "本体を持って抜去"]
    for index, label in enumerate(steps):
        x = 48 + index * 383
        D.box(c, x, 588, 359, 71, fill="#f3f6f8")
        text(c, x + 22, 632, label, 24)
        if index < 3:
            D.arrow(c, x + 361, 624, x + 379, 624, GRAY)
    text(
        c,
        48,
        702,
        "ケーブルを引いて抜かない。CPA付き候補／CPAなし候補は比較のまま。主電力2口・LVは固有手順未確定。",
        20,
        GRAY,
    )
    text(c, 48, 746, "全体を進めながら、未確定の施工は残して追跡する", 26, GOLD)
    issues = [
        "加工・入荷の境界 / 主ヒューズP22・被覆P08の取付工程 / 箱内の隠れた工具対象",
        "自由端ごとの支持先と必要な保持数 / LV・HVILの個別物理端末 / 工具・手先交換",
        "蓋と試験の順序 / 試験接続口・条件・時間 / 既存腕と固定機構の分担",
    ]
    for index, issue in enumerate(issues):
        text(c, 71, 799 + index * 40, "・" + issue, 20)
    text(c, 48, 948, "出典：TE 408-32095 Rev B pp.4-6 / Ampere V1.1 / Ampere HVJB tester記事", 18, GRAY)
    label = "TE公式手順書を開く"
    text(c, 48, 993, label, 20, C)
    c.linkURL(data["cpa_followup"]["source_url"], (48, H - 1000, 290, H - 969), relative=0)
    text(c, 369, 993, "一般の手順を、自動化の操作量・力・検出しきい値に読み替えていません。", 20, GRAY)
    c.showPage()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    assert not out.exists(), out
    data_path = ROOT / "data/line_review_data.json"
    data = json.loads(data_path.read_text())
    figures = json.loads((ROOT / "audit/product_final_views.json").read_text())
    for row in figures["views"]:
        assert sha(ROOT / row["file"]) == row["sha256"]
    pdfmetrics.registerFont(UnicodeCIDFont(D.FONT))
    (out / "pdf").mkdir(parents=True)
    pdf_path = out / "pdf" / (NAME + ".pdf")
    c = canvas.Canvas(str(pdf_path), pagesize=(W, H), pageCompression=1)
    c.setTitle("HVJB ライン全体と組立場所 v04")
    c.setAuthor("RLRK")
    overview(c)
    product_mapping(c)
    support_sequence(c)
    all_jobs(c, data)
    parallel_roles(c)
    after_process(c, data)
    c.save()
    audit = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "pdf": str(pdf_path),
        "pdf_sha256": sha(pdf_path),
        "page_count": PAGES,
        "builder_sha256": sha(Path(__file__)),
        "drawing_helper_sha256": sha(HELPER),
        "data_sha256": sha(data_path),
        "product_figure_audit_sha256": sha(ROOT / "audit/product_final_views.json"),
        "text_geometry": D.DRAWN,
        "formal_physical_validity_verdict": None,
    }
    (out / "document_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print("LINE_VISUAL_GUIDE_COMPLETE", pdf_path, flush=True)


if __name__ == "__main__":
    main()
