# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Draw dimensionless role diagrams from the preserved sharing examples."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
INK = "#233447"
MUTED = "#586d80"
COLORS = {"A": "#286db3", "B": "#9e478f", "C": "#198773"}
SOFT = {"A": "#edf4fc", "B": "#faf0f8", "C": "#edf8f4"}
GOLD = "#946111"
RED = "#b13638"


class Diagram:
    """Small SVG writer with measured label-width checks in display pixels."""

    def __init__(self, width=1400, height=850):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"',
            f' width="{width}" height="{height}" role="img">',
            '<rect width="100%" height="100%" fill="#f4f7fa"/>',
        ]
        self.labels = []

    def rect(self, x, y, w, h, color, stroke="none", radius=16):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}"'
            f' fill="{color}" stroke="{stroke}" stroke-width="2"/>'
        )

    def text(self, x, y, value, size=24, color=INK, max_width=1300, bold=False):
        font = ImageFont.truetype(FONT, size)
        width = font.getlength(value)
        assert width <= max_width, (value, width, max_width)
        self.labels.append({"text": value, "x": x, "baseline_y": y, "width": width, "maximum_width": max_width})
        weight = 700 if bold else 400
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="Noto Sans CJK JP, sans-serif"'
            f' font-size="{size}" font-weight="{weight}" fill="{color}">{escape(value)}</text>'
        )

    def line(self, points, color, dashed=False, width=5):
        dash = ' stroke-dasharray="9 7"' if dashed else ""
        formatted = " ".join(f"{x},{y}" for x, y in points)
        self.parts.append(
            f'<polyline points="{formatted}" fill="none" stroke="{color}"'
            f' stroke-width="{width}" stroke-linejoin="round"{dash}/>'
        )

    def save(self, path):
        path.write_text("\n".join([*self.parts, "</svg>"]) + "\n", encoding="utf-8")
        return self.labels


def cell(diagram, key, x, needed):
    color = COLORS[key]
    name = {"A": "下板側ユニット", "B": "ヒューズ板側ユニット", "C": "合流・搭載・残接続"}[key]
    jobs = {"A": "D10 / D11 / D12", "B": "D20 / D21 / D22", "C": "D30〜D61"}[key]
    lot = "次の一式の部材" if key in ("A", "B") else "前の一式"
    diagram.rect(x, 267, 408, 361, "white", color)
    diagram.text(x + 24, 310, f"ST {key}", 30, color, 360, bold=True)
    diagram.text(x + 24, 352, name, 25, INK, 360)
    diagram.rect(x + 24, 375, 360, 67, SOFT[key])
    diagram.text(x + 42, 418, f"主担当 {key}：1腕", 26, color, 324, bold=True)
    diagram.text(x + 24, 484, "補助の独立保持が必要" if needed else "補助不要の作業と仮定", 24, INK, 360)
    diagram.text(x + 24, 525, "共用補助を使う" if key in ("A", "B") else "C専用補助を使う", 22, color, 360)
    if not needed:
        diagram.rect(x + 16, 497, 376, 43, "white", radius=0)
        diagram.text(x + 24, 525, "保持解除を指示する表示ではない", 19, MUTED, 360)
    diagram.text(x + 24, 569, lot, 22, INK, 360, bold=True)
    diagram.text(x + 24, 608, jobs, 19, MUTED, 360)


def scenario_diagram(row):
    d = Diagram()
    needed = {key: f"X-{key}" in row["active_assists"] for key in ("A", "B", "C")}
    conflict = bool(row["duplicate_assignments"])
    d.text(40, 54, "3STと5腕の役割分担", 32, INK, 900, bold=True)
    d.text(40, 90, "無寸法の役割図。A/Bで次の部材、Cで前の一式を扱う説明例。", 23, MUTED, 1300)
    shared = (
        "AとBが同じ1腕を要求"
        if conflict
        else "Aを補助"
        if needed["A"]
        else "Bを補助"
        if needed["B"]
        else "要求なしの例"
    )
    d.rect(222, 116, 500, 98, "#fff2e1", RED if conflict else GOLD)
    d.text(246, 151, "A/B共用補助：1腕", 25, GOLD, 452, bold=True)
    d.text(246, 190, shared, 25, RED if conflict else INK, 452)
    d.rect(952, 116, 408, 98, SOFT["C"], COLORS["C"])
    d.text(976, 151, "C専用補助：1腕", 25, COLORS["C"], 360, bold=True)
    d.text(976, 190, "Cを補助" if needed["C"] else "要求なしの例", 25, INK, 360)
    for key, x in (("A", 40), ("B", 496), ("C", 952)):
        origin = (472 if key != "C" else 1156, 214)
        destination = (x + 204, 262)
        color = (RED if conflict and key != "C" else COLORS[key]) if needed[key] else "#c5d0db"
        d.line([origin, (destination[0], 237), destination], color, not needed[key])
        cell(d, key, x, needed[key])
    d.rect(40, 651, 1320, 131, "#fff0ed" if conflict else "#eaf0f5")
    d.text(64, 691, row["title_ja"], 26, RED if conflict else INK, 1272, bold=True)
    if conflict:
        d.text(64, 731, "共用補助の保持開始を同時には割り当てない。前の支持引継ぎ・退避後に次へ。", 25, RED, 1272)
        d.text(64, 764, "保持中の腕を途中で離す方法は、この分担に含めない。", 21, MUTED, 1272)
    else:
        d.text(64, 731, "この担当ID表では同じ補助腕への要求が重ならない。", 25, INK, 1272)
        d.text(64, 764, "到達・移動・支持・工具まで含む同時運転の成立を示すものではない。", 21, MUTED, 1272)
    d.text(40, 824, "5腕は組立の役割数。XYZ、工具、供給、検査、回収などを含む設備台数ではありません。", 22, MUTED, 1320)
    return d


def handoff_diagram():
    d = Diagram(1400, 480)
    d.text(40, 52, "共用補助が次のセルへ移るまで", 32, INK, 1320, bold=True)
    d.text(40, 91, "A→B / B→Aのどちらも同じ扱い。秒数・移動経路・支持面は未選定。", 23, MUTED, 1320)
    steps = [
        ("前の仕事で保持", ["保持を継続。", "次の要求は開始待ち。"]),
        ("次の支持先へ渡す", ["台・治具・次の保持役。", "具体的な支持先は要確認。"]),
        ("指を開放・退避", ["支持の引継ぎ後に開く。", "指の抜け方も要確認。"]),
        ("交換・移動", ["必要な手先交換と移動。", "次の把持はまだ始めない。"]),
        ("次のセルで保持", ["前の手順が終わってから、", "新しい対象を保持する。"]),
    ]
    for i, (title, lines) in enumerate(steps):
        x = 40 + i * 268
        d.rect(x, 128, 248, 234, "white", GOLD)
        d.rect(x + 17, 144, 43, 42, "#fff2e1", radius=8)
        d.text(x + 30, 175, str(i + 1), 24, GOLD, 30, bold=True)
        d.text(x + 17, 227, title, 23, INK, 216, bold=True)
        for j, text in enumerate(lines):
            d.text(x + 17, 282 + j * 32, text, 17, MUTED, 216)
        if i < 4:
            d.line([(x + 250, 245), (x + 263, 245)], GOLD, width=3)
    d.text(40, 410, "時間は未測定です。引継ぎ・退避・交換・移動を、後で個別に計上します。", 24, INK, 1320)
    d.text(40, 452, "相手の支持が成立したとする条件・信号・力の値を、この説明図から新しく定めません。", 22, MUTED, 1320)
    return d


def reservation_diagram():
    d = Diagram(1400, 550)
    d.text(40, 52, "C補助は、搭載が終わっただけでは空きにならない", 32, INK, 1320, bold=True)
    d.text(40, 91, "既存の継続予約 D31→D40→D42→D45→D50。自由端ごとに次の支持先まで追う。", 23, MUTED, 1320)
    labels = [
        ("D31", "持ち替え"),
        ("D40", "筐体搭載"),
        ("D42", "箱内工具"),
        ("D45", "開口引出し"),
        ("D50", "外側ヘッダー"),
    ]
    for i, (job, label) in enumerate(labels):
        x = 40 + 268 * i
        d.rect(x, 130, 248, 110, SOFT["C"], COLORS["C"])
        d.text(x + 18, 171, job, 27, COLORS["C"], 212, bold=True)
        d.text(x + 18, 214, label, 25, INK, 212)
    d.rect(40, 270, 1320, 79, COLORS["C"])
    d.text(65, 320, "C専用補助：次の支持先へ引き継ぐまで、案内担当の占有を残す", 27, "white", 1270, bold=True)
    d.text(40, 394, "全区間で同じ腕が必須と確定した意味ではありません。", 24, INK, 1320)
    d.text(
        40,
        436,
        "D60 / D61にも対象別の支持確認が残ります。複数の自由端を1つの手で扱えるとは未確認です。",
        23,
        MUTED,
        1320,
    )
    d.text(40, 490, "A/B共用補助のC同行は未採用。Cへ貸し出して不足を埋めた図にはしていません。", 23, MUTED, 1320)
    return d


def main():
    data = json.loads((ROOT / "data/parallel_review_data.json").read_text())
    out = ROOT / "figures"
    out.mkdir(exist_ok=False)
    labels = {}
    for row in data["scenarios"]:
        labels[row["id"]] = scenario_diagram(row).save(out / (row["id"] + ".svg"))
    labels["handoff"] = handoff_diagram().save(out / "handoff.svg")
    labels["reservation"] = reservation_diagram().save(out / "reservation.svg")
    (ROOT / "label_geometry.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n")
    print("PARALLEL_DIAGRAMS_READY 8 cases + 2 support diagrams", flush=True)


if __name__ == "__main__":
    main()
