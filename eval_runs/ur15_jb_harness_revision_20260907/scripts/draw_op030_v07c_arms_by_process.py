# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Draw which process each arm count suits, with the line's own answer on top [-].

One figure. The strip across the top is the line as built -- ten stations, the arms each
carries, and whether it takes parts at all. Underneath is the ladder: how many points a job
needs held or acted on at the same moment, and the arm count that follows. The two rows the
line has built are marked as such; the two it has not are marked as not a person's shape.

Fed from ``audit/op030_v07c_arms_by_process.json`` so it cannot drift from the check.

    python3 scripts/draw_op030_v07c_arms_by_process.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "audit/op030_v07c_arms_by_process.json"
FIGURE = ROOT / "analysis/op030_v07c_arms_by_process.svg"

INK = "#16181d"
NOTE = "#7a7f87"
BUILT = "#1f6f8b"
UNBUILT = "#b9770e"
OP030 = "#c0392b"
FONT = "IPAGothic, Noto Sans JP, Hiragino Sans, sans-serif"


def arm_glyph(x: float, y: float, count: int, colour: str) -> list[str]:
    """Return `count` small circles standing for arms, centred on x."""
    out = []
    for index in range(count):
        cx = x + (index - (count - 1) / 2) * 13
        out.append(f'<circle cx="{cx:.1f}" cy="{y}" r="5" fill="none" stroke="{colour}" stroke-width="2"/>')
    return out


def main() -> int:
    data = json.loads(DATA.read_text())
    stations = data["the_line_as_built"]["stations"]
    ladder = data["ladder"]

    width, height = 1120, 660
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}"'
        f' height="{height}" font-family="{FONT}" role="img"'
        ' aria-label="ラインは 8 工程が双腕、検査 2 工程が単腕、3 本以上は無い。'
        '同時に確定させる点の数が腕数を決める。">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="30" y="36" font-size="18" font-weight="700" fill="{INK}">'
        "腕数と工程 — 人手に代わる、という前提で</text>",
        f'<text x="30" y="58" font-size="12.5" fill="{NOTE}">'
        "決めているのは「その工程で同時に確定させないといけない点の数」。人は 2 本しか持たない</text>",
    ]

    # The line as built.
    out.append(
        f'<text x="30" y="96" font-size="14" font-weight="700" fill="{INK}">ラインの実装（既に答えが出ている）</text>'
    )
    strip_y, step = 128, 104
    for index, row in enumerate(stations):
        cx = 74 + index * step
        colour = OP030 if row["station"] == "OP030" else BUILT
        out.append(
            f'<rect x="{cx - 44}" y="{strip_y - 26}" width="88" height="72" rx="6" fill="none"'
            f' stroke="{colour}" stroke-width="{2 if row["station"] == "OP030" else 1}" opacity="0.75"/>'
        )
        out.append(
            f'<text x="{cx}" y="{strip_y - 8}" font-size="12" text-anchor="middle"'
            f' font-weight="{700 if row["station"] == "OP030" else 400}" fill="{colour}">{row["station"]}</text>'
        )
        out += arm_glyph(cx, strip_y + 12, row["arm_count"], colour)
        out.append(
            f'<text x="{cx}" y="{strip_y + 38}" font-size="10.5" text-anchor="middle" fill="{NOTE}">'
            f"{'部品を取る' if row['takes_parts'] else '取らない'}</text>"
        )
    out.append(
        f'<text x="30" y="{strip_y + 74}" font-size="12" fill="{INK}">'
        "→ <tspan font-weight='700'>双腕 8 工程・単腕 2 工程・3 本以上は 0</tspan>。"
        "単腕の 2 工程はストッカも操作盤も無い＝検査</text>"
    )

    # The ladder.
    top = strip_y + 116
    out.append(f'<text x="30" y="{top}" font-size="14" font-weight="700" fill="{INK}">同時に確定させる点 → 腕数</text>')
    head_y = top + 30
    for label, x in (("工程の性格", 40), ("腕", 336), ("人との対応", 404), ("適する工程", 640)):
        out.append(f'<text x="{x}" y="{head_y}" font-size="11.5" font-weight="700" fill="{NOTE}">{label}</text>')
    out.append(
        f'<line x1="30" y1="{head_y + 8}" x2="{width - 30}" y2="{head_y + 8}" stroke="{NOTE}" stroke-width="1"/>'
    )

    row_y = head_y + 34
    for step_row in ladder:
        colour = BUILT if step_row["on_the_line"] else UNBUILT
        out.append(f'<text x="40" y="{row_y}" font-size="12.5" fill="{INK}">{step_row["points"]}</text>')
        out += arm_glyph(348, row_y - 4, step_row["arms"], colour)
        out.append(f'<text x="404" y="{row_y}" font-size="12" fill="{colour}">{step_row["person"]}</text>')
        out.append(f'<text x="640" y="{row_y}" font-size="12" fill="{INK}">{step_row["suits"]}</text>')
        out.append(f'<text x="640" y="{row_y + 17}" font-size="11" fill="{NOTE}">{step_row["example"]}</text>')
        out.append(
            f'<line x1="30" y1="{row_y + 27}" x2="{width - 30}" y2="{row_y + 27}" stroke="{NOTE}"'
            ' stroke-width="0.6" opacity="0.4"/>'
        )
        row_y += 54

    out.append(
        f'<text x="30" y="{row_y + 6}" font-size="12.5" fill="{OP030}" font-weight="700">'
        "OP030 の内訳：A は押さえ＋締結、B はケーブル両端 — どちらも人の両手仕事。</text>"
    )
    out.append(
        f'<text x="30" y="{row_y + 26}" font-size="12.5" fill="{OP030}">'
        "C だけは違う — 2 本目は「もう一方の手」ではなく「工具を持ち替えないための手」。"
        "だから分けても失うものが最も少ない</text>"
    )
    out.append("</svg>")
    FIGURE.write_text("\n".join(out) + "\n")
    print(f"wrote {FIGURE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
