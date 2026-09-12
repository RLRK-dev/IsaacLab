# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Draw the two choices side by side: how many arms, and what holds them up [m].

Two figures, both fed from ``audit/op030_v07c_arm_count_and_mounting.json`` so neither can
drift from the check.

``op030_v07c_arm_count.svg`` is four panels, one per arm count, in plan. Each shows the work
the arms have to share -- two supports 320 mm apart, each with two bolts 68 mm apart -- and
where the shoulders would have to stand to serve it. The point of the set is what changes:
one arm cannot hold and drive at once, two is what A and B require, three splits the two bolts
of one support, four splits the two supports. Only the last one touches the bottleneck.

``op030_v07c_mounting.svg`` is an elevation, because the mounting question is vertical. It
draws the measured stack -- floor, product, arms, the service run, the lighting, the ceiling
underside at 7.200 -- and puts each mounting option against it. The service run's box is
hatched rather than solid: it is known to be much larger than the pipe inside it.

Read-only drawing. Positions and spans; no reachability, no stiffness, no safety.

    python3 scripts/draw_op030_v07c_arm_count_and_mounting.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "audit/op030_v07c_arm_count_and_mounting.json"
ARM_FIGURE = ROOT / "analysis/op030_v07c_arm_count.svg"
MOUNT_FIGURE = ROOT / "analysis/op030_v07c_mounting.svg"

INK = "#16181d"
HOLD = "#c0392b"
DRIVE = "#1f6f8b"
NOTE = "#7a7f87"
FONT = "IPAGothic, Noto Sans JP, Hiragino Sans, sans-serif"


def head(width: int, height: int, label: str) -> list[str]:
    """Return the root element and a white ground for a standalone figure."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"'
        f' width="{width}" height="{height}" font-family="{FONT}" role="img" aria-label="{label}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]


def arm_count_figure(data: dict) -> str:
    """Return four plan panels, one per arm count, over the same work."""
    work = data["the_work_the_arms_share"]
    seat_gap = work["two_supports_apart_in_x_m"]
    bolt_gap = work["two_bolts_of_one_support_apart_in_y_m"]
    pitch = work["shoulder_pitch_m"]
    minimum = data["minimum_simultaneous_arms"]

    cell_w, cell_h, cols = 460, 300, 2
    width, height = cell_w * cols + 40, cell_h * 2 + 70
    out = head(width, height, "腕数 1・2・3・4 の比較。作業点は支持部 2 個が 320 mm、1 個あたりボルト 2 本が 68 mm。")
    out.append(
        f'<text x="24" y="30" font-size="17" font-weight="700" fill="{INK}">'
        f"腕数の比較 — 作業点は固定：支持部 2 個 {seat_gap * 1000:.0f} mm、"
        f"1 個あたりボルト 2 本 {bolt_gap * 1000:.0f} mm</text>"
    )
    out.append(
        f'<text x="24" y="52" font-size="12" fill="{NOTE}">'
        f"同時に要る腕：A {minimum['A']}・B {minimum['B']}・C {minimum['C']}"
        f"（各工程のシーケンスから）／現行の肩ピッチ {pitch * 1000:.0f} mm</text>"
    )

    panels = [
        (
            "① 単腕",
            [
                "A：不可。押さえながら締結できない",
                "B：不可。ケーブル両端を同時に持てない",
                "C：可。M6→M14 を持ち替え/2 連工具",
            ],
            [("両用", 0.0, "both")],
            "A・B は治具か機構の追加が要る（制約 2 に抵触）。C のみ成立",
        ),
        (
            "② 双腕（現行）",
            ["A：押さえ 1・締結 1", "B：両端を 1 本ずつ", "C：M6 と M14、直列"],
            [("押さえ", 1.0, "hold"), ("締結", 1.42, "drive")],
            "A・B が要求する最小構成。1 個ずつ順に（T02→T01）",
        ),
        (
            "③ 3 腕",
            ["A：押さえ 1・締結 2 → ボルト 2 本を同時", "B：2 本で足り、1 本は他工程へ", "C：端子 2 本を同時にできる"],
            [("締結", 0.78, "drive"), ("押さえ", 1.28, "hold"), ("締結", 1.66, "drive")],
            f"締結 2 本が同じ支持部の {bolt_gap * 1000:.0f} mm に寄る。自己干渉は未計測",
        ),
        (
            "④ 4 腕",
            ["A：（押さえ＋締結）×2 → 支持部 2 個を同時", "B：2 本使用、2 本は待機", "C：M6/M14 × 2 端子を同時"],
            [("押さえ", -1.28, "hold"), ("締結", -0.86, "drive"), ("押さえ", 1.0, "hold"), ("締結", 1.42, "drive")],
            f"A の律速が半分になりうる唯一の案。肩 4 本は {pitch * 1000:.0f} mm の支柱に載らない",
        ),
    ]

    for index, (title, notes, shoulders, footer) in enumerate(panels):
        ox = 20 + (index % cols) * cell_w
        oy = 70 + (index // cols) * cell_h
        out.append(
            f'<rect x="{ox}" y="{oy}" width="{cell_w - 20}" height="{cell_h - 20}" fill="none"'
            f' stroke="{NOTE}" stroke-width="1" rx="6" opacity="0.5"/>'
        )
        out.append(f'<text x="{ox + 16}" y="{oy + 28}" font-size="15" font-weight="700" fill="{INK}">{title}</text>')
        for line, text in enumerate(notes):
            out.append(f'<text x="{ox + 16}" y="{oy + 50 + line * 17}" font-size="12" fill="{INK}">{text}</text>')

        # The work: two supports, two bolts each, drawn to one scale across all four panels.
        base_x, base_y, span = ox + 210, oy + 190, 150.0
        for sign, name in ((-1, "T02"), (1, "T01")):
            seat_x = base_x + sign * span / 2
            out.append(
                f'<rect x="{seat_x - 26:.1f}" y="{base_y - 13}" width="52" height="26" rx="3"'
                f' fill="none" stroke="{INK}" stroke-width="1.2"/>'
            )
            out.append(
                f'<text x="{seat_x:.1f}" y="{base_y + 30}" font-size="11" text-anchor="middle"'
                f' fill="{NOTE}">{name}</text>'
            )
            for bolt in (-1, 1):
                out.append(f'<circle cx="{seat_x + bolt * 11:.1f}" cy="{base_y}" r="3.5" fill="{INK}"/>')
        out.append(
            f'<line x1="{base_x - span / 2:.1f}" y1="{base_y + 44}" x2="{base_x + span / 2:.1f}"'
            f' y2="{base_y + 44}" stroke="{NOTE}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{base_x:.1f}" y="{base_y + 58}" font-size="11" text-anchor="middle"'
            f' fill="{NOTE}">{seat_gap * 1000:.0f} mm</text>'
        )

        # The shoulders this option needs, spaced at the drawn equivalent of the real pitch.
        step = span / 2
        for label, offset, kind in shoulders:
            colour = HOLD if kind == "hold" else DRIVE if kind == "drive" else INK
            cx = base_x + offset * step
            cy = oy + 118
            out.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="9" fill="none" stroke="{colour}" stroke-width="2.2"/>')
            out.append(
                f'<text x="{cx:.1f}" y="{cy - 15}" font-size="11" text-anchor="middle" fill="{colour}">{label}</text>'
            )
            out.append(
                f'<line x1="{cx:.1f}" y1="{cy + 10}" x2="{cx:.1f}" y2="{base_y - 16}" stroke="{colour}"'
                ' stroke-width="1.2" stroke-dasharray="4 4" opacity="0.8"/>'
            )
        out.append(f'<text x="{ox + 16}" y="{oy + cell_h - 34}" font-size="11.5" fill="{NOTE}">{footer}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def mounting_figure(data: dict) -> str:
    """Return an elevation of what is above the cell, with each mounting option against it."""
    bands = data["overhead"]["bands"]
    ceiling = data["ceiling_m"]["underside_z_m"]
    work = data["the_work_the_arms_share"]
    column_z = work["column_z_m"]
    shoulder_z = work["shoulder_height_m"]

    left, top, right, bottom = 96, 76, 330, 46
    scale = 86.0
    z_max = ceiling + 0.4
    width = left + int(5.2 * scale) + right
    height = top + int(z_max * scale) + bottom

    def px(x: float) -> float:
        return left + (x + 3.0) * scale

    def pz(z: float) -> float:
        return top + (z_max - z) * scale

    out = head(
        width,
        height,
        "OP030-A の立面図。腕の上に用力主管と照明があり、天井下端は 7.200 m。設置方法の候補を重ねてある。",
    )
    out.append(
        f'<text x="24" y="32" font-size="17" font-weight="700" fill="{INK}">'
        "設置方法 — セル上方に何があるか（立面・実測）</text>"
    )
    out.append(
        f'<text x="24" y="54" font-size="12" fill="{NOTE}">'
        "斜線＝箱が実物より大きいと分かっているもの（三角形接触 0 件）。空き帯は箱の外側という意味でしかない</text>"
    )
    out.append(
        '<defs><pattern id="coarse" width="8" height="8" patternUnits="userSpaceOnUse">'
        f'<path d="M0,8 L8,0" stroke="{NOTE}" stroke-width="1" opacity="0.6"/></pattern></defs>'
    )

    # Floor, ceiling, and the Z scale.
    out.append(
        f'<line x1="{px(-3.0):.1f}" y1="{pz(0):.1f}" x2="{px(2.2):.1f}" y2="{pz(0):.1f}"'
        f' stroke="{INK}" stroke-width="2"/>'
    )
    out.append(f'<text x="{px(-3.0):.1f}" y="{pz(0) + 18:.1f}" font-size="11" fill="{NOTE}">床 Z=0</text>')
    out.append(
        f'<rect x="{px(-3.0):.1f}" y="{pz(ceiling + 0.16):.1f}" width="{5.2 * scale:.1f}"'
        f' height="{0.16 * scale:.1f}" fill="{INK}" opacity="0.75"/>'
    )
    out.append(
        f'<text x="{px(2.2) + 8:.1f}" y="{pz(ceiling) + 4:.1f}" font-size="12"'
        f' fill="{INK}">天井下端 {ceiling:.3f}</text>'
    )
    for z in (1, 2, 3, 4, 5, 6, 7):
        out.append(
            f'<line x1="{px(-3.0) - 6:.1f}" y1="{pz(z):.1f}" x2="{px(-3.0):.1f}" y2="{pz(z):.1f}"'
            f' stroke="{NOTE}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{px(-3.0) - 10:.1f}" y="{pz(z) + 4:.1f}" font-size="10" text-anchor="end"'
            f' fill="{NOTE}">{z}</text>'
        )

    # What actually stands above the arms, band by band.
    for band in bands:
        low, high = band["z_m"]
        for blocked in band["blocked_x_m"]:
            x0, x1 = blocked["x_m"]
            coarse = blocked["any_box_is_coarse"]
            out.append(
                f'<rect x="{px(x0):.1f}" y="{pz(high):.1f}" width="{(x1 - x0) * scale:.1f}"'
                f' height="{(high - low) * scale:.1f}"'
                f' fill="{"url(#coarse)" if coarse else NOTE}" opacity="{0.9 if coarse else 0.35}"'
                f' stroke="{NOTE}" stroke-width="1"/>'
            )
        if not band["blocked_x_m"]:
            out.append(
                f'<text x="{px(-0.4):.1f}" y="{pz((low + high) / 2) + 4:.1f}" font-size="11"'
                f' text-anchor="middle" fill="{NOTE}">Z {low:.2f}–{high:.2f} 空き</text>'
            )

    # The cell itself.
    out.append(
        f'<rect x="{px(-1.07):.1f}" y="{pz(column_z[1]):.1f}" width="{0.425 * scale:.1f}"'
        f' height="{(column_z[1] - column_z[0]) * scale:.1f}" fill="{INK}" opacity="0.5"/>'
    )
    out.append(
        f'<circle cx="{px(-0.9):.1f}" cy="{pz(shoulder_z):.1f}" r="7" fill="none" stroke="{HOLD}" stroke-width="2.5"/>'
    )
    out.append(
        f'<text x="{px(-0.9) - 14:.1f}" y="{pz(shoulder_z) + 4:.1f}" font-size="11" text-anchor="end"'
        f' fill="{HOLD}">肩 {shoulder_z:.3f}</text>'
    )
    out.append(
        f'<rect x="{px(-0.35):.1f}" y="{pz(0.95):.1f}" width="{0.7 * scale:.1f}" height="{0.12 * scale:.1f}"'
        f' fill="{INK}" opacity="0.35"/>'
    )
    out.append(
        f'<text x="{px(0.0):.1f}" y="{pz(0.75):.1f}" font-size="11" text-anchor="middle" fill="{NOTE}">製品</text>'
    )

    # Each mounting option, drawn where it would actually have to come from.
    options = [
        ("① 床置き支柱（現行）", -0.9, 0.0, column_z[1], HOLD, "床面積 0.425×0.631 m を占める"),
        ("② 天井吊り", -0.72, ceiling, shoulder_z, "#7d3c98", "照明 4.03–5.73 を貫く。垂れ 5.7 m"),
        ("③ 門型（脚は外側・梁 3.6）", -1.85, 0.0, 3.6, DRIVE, "脚は空き帯 −2.19..−1.46 に立つ"),
        ("④ 用力架構から吊る", -1.08, 3.32, shoulder_z, "#b9770e", "既設の架構に載せる。箱は実物より大"),
    ]
    for label, x, z_from, z_to, colour, note in options:
        dashed = ' stroke-dasharray="8 5"' if label[0] in "②④" else ""
        out.append(
            f'<line x1="{px(x):.1f}" y1="{pz(z_from):.1f}" x2="{px(x):.1f}" y2="{pz(z_to):.1f}"'
            f' stroke="{colour}" stroke-width="3" opacity="0.85" stroke-linecap="round"{dashed}/>'
        )
    for x1, z1, x2, z2 in ((-1.85, 3.6, 1.5, 3.6), (1.5, 3.6, 1.5, 0.0)):
        out.append(
            f'<line x1="{px(x1):.1f}" y1="{pz(z1):.1f}" x2="{px(x2):.1f}" y2="{pz(z2):.1f}"'
            f' stroke="{DRIVE}" stroke-width="3" opacity="0.85"/>'
        )

    legend_x = px(2.2) + 8
    for line, (label, _, _, _, colour, note) in enumerate(options):
        y = top + 110 + line * 46
        out.append(
            f'<line x1="{legend_x}" y1="{y - 4}" x2="{legend_x + 26}" y2="{y - 4}" stroke="{colour}" stroke-width="3"/>'
        )
        out.append(f'<text x="{legend_x + 34}" y="{y}" font-size="12.5" font-weight="600" fill="{INK}">{label}</text>')
        out.append(f'<text x="{legend_x + 34}" y="{y + 17}" font-size="11" fill="{NOTE}">{note}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    data = json.loads(DATA.read_text())
    ARM_FIGURE.write_text(arm_count_figure(data))
    MOUNT_FIGURE.write_text(mounting_figure(data))
    print(f"wrote {ARM_FIGURE.relative_to(ROOT)}")
    print(f"wrote {MOUNT_FIGURE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
