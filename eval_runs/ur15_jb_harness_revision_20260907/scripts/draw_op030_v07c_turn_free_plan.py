# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.

# SPDX-License-Identifier: BSD-3-Clause

"""Draw A in plan, so the turn question can be seen rather than read [m].

The argument in ``OP030_v07_双腕構成_検算.md`` §5 is entirely about which side of one line
things stand on, which is a picture. Two panels, same plan, one difference: where the two
product parts sit on the pallet, and whether the yoke turns.

Every coordinate is read out of ``audit/op030_v07c_turn_free_transport.json`` and
``audit/op030_v07c_dual_arm_configuration.json`` rather than typed here, so the figure cannot
drift from the checks it illustrates. Re-run it after either check changes.

    python3 scripts/draw_op030_v07c_turn_free_plan.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TURN_FREE = ROOT / "audit/op030_v07c_turn_free_transport.json"
DUAL_ARM = ROOT / "audit/op030_v07c_dual_arm_configuration.json"
FIGURE = ROOT / "analysis/op030_v07c_turn_free_plan.svg"

# Plan view: X to the right, Y up. The drawn window covers the pallet through the far seat.
SCALE = 280.0
X_MIN, Y_MAX = -2.35, -1.30
LEFT, TOP, RIGHT, BOTTOM = 70, 46, 120, 34
WIDE, HIGH = 2.70, 0.85
PANEL_W = LEFT + int(WIDE * SCALE) + RIGHT
PANEL_H = TOP + int(HIGH * SCALE) + BOTTOM
GAP = 26
# One hue for the parts and the reach to them, one for the turn. Both read on either ground.
PART = "#d94f4f"
TURN = "#4f7fd9"


def sx(x: float) -> float:
    """Return the drawing x for a world X [m]."""
    return LEFT + (x - X_MIN) * SCALE


def sy(y: float, top: float) -> float:
    """Return the drawing y for a world Y [m], inside the panel starting at `top`."""
    return top + TOP + (Y_MAX - y) * SCALE


def panel(top: float, title: str, occupied: dict, turning: bool, data: dict, column: dict) -> list[str]:
    """Return one plan panel: the pallet, the yoke, and the reach to the two parts."""
    geometry = data["geometry"]
    centre_x, centre_y = geometry["cell_centre_xy_m"]
    slot_x0, slot_dx, slot_y0, slot_dy, _ = data["read_from"]["constants"]["slot_position"]["numbers"]
    columns = geometry["pallet"]["columns"]
    withdrawal = data["read_from"]["constants"]["withdrawal"]["numbers"][0]
    deck_low, deck_high = data["mirroring_the_nests"]["pallet_deck_y_span_m"]
    shoulders = geometry["shoulders"]
    turned = geometry["shoulders_after_a_half_turn"]
    out = [f'<text x="{LEFT - 10}" y="{top + 26}" font-size="15" font-weight="600">{title}</text>']

    # The pallet deck and every one of its twenty slots.
    deck_x0, deck_x1 = sx(slot_x0 - 0.06), sx(slot_x0 + 3 * slot_dx + 0.06)
    out.append(
        f'<rect x="{deck_x0:.1f}" y="{sy(deck_high, top):.1f}" width="{deck_x1 - deck_x0:.1f}"'
        f' height="{(deck_high - deck_low) * SCALE:.1f}" fill="none" stroke="currentColor"'
        ' stroke-width="1" opacity="0.45" rx="3"/>'
    )
    for index in range(20):
        row, column_index = divmod(index, columns)
        x, y = slot_x0 + row * slot_dx, slot_y0 + column_index * slot_dy
        held = next((name for name, slot in occupied.items() if slot == index), None)
        fill = PART if held else "none"
        out.append(
            f'<rect x="{sx(x) - 7:.1f}" y="{sy(y, top) - 7:.1f}" width="14" height="14" rx="2"'
            f' fill="{fill}" stroke="currentColor" stroke-width="1"'
            f' opacity="{1.0 if held else 0.35}"/>'
        )
        if held:
            out.append(
                f'<text x="{sx(x):.1f}" y="{sy(y, top) - 12:.1f}" font-size="11" text-anchor="middle"'
                f' fill="{PART}" font-weight="600">{held}・スロット{index}</text>'
            )
    out.append(
        f'<text x="{(deck_x0 + deck_x1) / 2:.1f}" y="{sy(deck_low, top) + 15:.1f}" font-size="11"'
        ' text-anchor="middle" opacity="0.7">供給パレット 20 スロット・120 mm ピッチ</text>'
    )

    # The centre line every claim in the section is about.
    out.append(
        f'<line x1="{LEFT - 14}" y1="{sy(centre_y, top):.1f}" x2="{PANEL_W - RIGHT + 40}"'
        f' y2="{sy(centre_y, top):.1f}" stroke="currentColor" stroke-width="1"'
        ' stroke-dasharray="7 5" opacity="0.55"/>'
    )
    out.append(
        f'<text x="{PANEL_W - RIGHT + 46}" y="{sy(centre_y, top) + 4:.1f}" font-size="11"'
        f' opacity="0.75">セル中心 Y={centre_y:.2f}</text>'
    )

    # The column, and the two shoulders standing on it.
    out.append(
        f'<rect x="{sx(column["low_m"][0]):.1f}" y="{sy(column["high_m"][1], top):.1f}"'
        f' width="{(column["high_m"][0] - column["low_m"][0]) * SCALE:.1f}"'
        f' height="{(column["high_m"][1] - column["low_m"][1]) * SCALE:.1f}" fill="none"'
        ' stroke="currentColor" stroke-width="1" opacity="0.4" rx="3"/>'
    )
    out.append(
        f'<text x="{sx(centre_x):.1f}" y="{sy(column["low_m"][1], top) + 15:.1f}" font-size="11"'
        ' text-anchor="middle" opacity="0.7">支柱（1 セル 1 本）</text>'
    )

    picking = turned["right"] if turning else shoulders["right"]
    tooled = turned["left"] if turning else shoulders["left"]
    if turning:
        # The yoke swinging a half turn about the cell centre, carrying both arms.
        for start, stop in ((shoulders["right"], turned["right"]), (shoulders["left"], turned["left"])):
            x, y0, y1 = sx(centre_x), sy(start[1], top), sy(stop[1], top)
            out.append(
                f'<path d="M {x:.1f},{y0:.1f} C {x - 92:.1f},{y0:.1f} {x - 92:.1f},{y1:.1f} {x:.1f},{y1:.1f}"'
                f' fill="none" stroke="{TURN}" stroke-width="1.6" marker-end="url(#tip)"/>'
            )
            out.append(
                f'<circle cx="{x:.1f}" cy="{y0:.1f}" r="5" fill="none" stroke="{TURN}"'
                ' stroke-width="1.4" stroke-dasharray="3 3"/>'
            )
        out.append(
            f'<text x="{sx(centre_x) - 96:.1f}" y="{sy(centre_y, top) - 8:.1f}" font-size="12"'
            f' text-anchor="end" fill="{TURN}" font-weight="600">ヨーク旋回 180°</text>'
        )
        out.append(
            f'<text x="{sx(centre_x) - 96:.1f}" y="{sy(centre_y, top) + 9:.1f}" font-size="11"'
            f' text-anchor="end" fill="{TURN}">2 本とも動く・6.0 s ×2</text>'
        )
    out.append(f'<circle cx="{sx(centre_x):.1f}" cy="{sy(centre_y, top):.1f}" r="3.5" fill="currentColor"/>')
    for label, point in (("拾う腕", picking), ("工具腕（M4）", tooled)):
        out.append(
            f'<circle cx="{sx(point[0]):.1f}" cy="{sy(point[1], top):.1f}" r="7" fill="none"'
            ' stroke="currentColor" stroke-width="2"/>'
        )
        out.append(f'<text x="{sx(point[0]) + 13:.1f}" y="{sy(point[1], top) + 4:.1f}" font-size="12">{label}</text>')

    # The reach from the picking shoulder to each part, once the kit is drawn out.
    for name, slot in occupied.items():
        row, column_index = divmod(slot, columns)
        part = (slot_x0 + row * slot_dx + withdrawal, slot_y0 + column_index * slot_dy)
        reach = ((picking[0] - part[0]) ** 2 + (picking[1] - part[1]) ** 2 + (picking[2] - 1.0) ** 2) ** 0.5
        out.append(
            f'<line x1="{sx(picking[0]):.1f}" y1="{sy(picking[1], top):.1f}" x2="{sx(part[0]):.1f}"'
            f' y2="{sy(part[1], top):.1f}" stroke="{PART}" stroke-width="1.5" stroke-dasharray="5 4"/>'
        )
        out.append(
            f'<circle cx="{sx(part[0]):.1f}" cy="{sy(part[1], top):.1f}" r="5" fill="none"'
            f' stroke="{PART}" stroke-width="1.6"/>'
        )
        if name == "T01":
            mid_x = (sx(picking[0]) + sx(part[0])) / 2
            out.append(
                f'<text x="{mid_x:.1f}" y="{sy(part[1], top) - 10:.1f}" font-size="12"'
                f' text-anchor="middle" fill="{PART}" font-weight="600">{reach:.3f} m</text>'
            )
    out.append(
        f'<text x="{sx(slot_x0 + withdrawal):.1f}" y="{sy(deck_low, top) + 30:.1f}" font-size="11"'
        f' text-anchor="middle" opacity="0.7">↑ 引出し +{withdrawal:.2f} m 後の位置</text>'
    )

    # The seats, which are further out than the pallet is. The arm seats from its normal pose --
    # it has turned back by then -- so this is always measured from the un-turned shoulder.
    seating = shoulders["right"]
    for name, seat in geometry["seats"].items():
        out.append(
            f'<circle cx="{sx(seat[0]):.1f}" cy="{sy(seat[1], top):.1f}" r="4" fill="currentColor" opacity="0.7"/>'
        )
    far = max(geometry["seats"].values(), key=lambda seat: seat[0])
    far_reach = ((seating[0] - far[0]) ** 2 + (seating[1] - far[1]) ** 2 + (seating[2] - far[2]) ** 2) ** 0.5
    out.append(
        f'<line x1="{sx(seating[0]):.1f}" y1="{sy(seating[1], top):.1f}" x2="{sx(far[0]):.1f}"'
        f' y2="{sy(far[1], top):.1f}" stroke="currentColor" stroke-width="1.2" opacity="0.5"/>'
    )
    out.append(
        f'<text x="{sx(far[0]) + 10:.1f}" y="{sy(far[1], top) - 6:.1f}" font-size="12"'
        f' font-weight="600">遠い座 {far_reach:.3f} m</text>'
    )
    out.append(
        f'<text x="{sx(far[0]) + 10:.1f}" y="{sy(far[1], top) + 11:.1f}" font-size="11"'
        ' opacity="0.75">すでに使っている距離</text>'
    )
    out.append(
        f'<line x1="{sx(0.0):.1f}" y1="{top + TOP - 6}" x2="{sx(0.0):.1f}" y2="{top + TOP + HIGH * SCALE + 6:.1f}"'
        ' stroke="currentColor" stroke-width="1" stroke-dasharray="3 4" opacity="0.35"/>'
    )
    out.append(
        f'<text x="{sx(0.0):.1f}" y="{top + TOP + HIGH * SCALE + 20:.1f}" font-size="11"'
        ' text-anchor="middle" opacity="0.7">製品 X=0</text>'
    )
    return out


def main() -> int:
    data = json.loads(TURN_FREE.read_text())
    column = json.loads(DUAL_ARM.read_text())["mounting"]["A"]["column"]["chosen"]
    held = data["geometry"]["pallet"]["slots_holding_the_two_parts"]
    mirror = data["mirroring_the_nests"]["mirror_lands_on_slot"]
    cost = data["what_the_turn_costs"]

    height = PANEL_H * 2 + GAP
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PANEL_W} {height}" width="{PANEL_W}"'
        f' role="img" aria-label="OP030-A の平面図。供給パレットの 20 スロットのうち製品 2 個が'
        "セル中心より工具腕側のスロット 5・6 に置かれているため、拾う腕を連れてくるのに"
        'ヨークを 180° 旋回している。鏡映位置のスロット 9・8 に置けば旋回は要らない。"'
        ' style="max-width:100%;height:auto">',
        '<defs><marker id="tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"'
        f' orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{TURN}"/></marker></defs>',
    ]
    parts += panel(0, "① 現状 — 部品はスロット 5・6（工具腕の側）。だから旋回する", held, True, data, column)
    parts += panel(
        PANEL_H + GAP,
        f"② 案 — 部品を鏡映スロット {mirror['T01']}・{mirror['T02']}（拾う腕の側）へ。旋回しない",
        {name: mirror[name] for name in held},
        False,
        data,
        column,
    )
    parts.append(
        f'<text x="{LEFT - 10}" y="{PANEL_H + GAP - 8}" font-size="11" opacity="0.75">'
        f"旋回 {cost['seconds_each']}s ×{cost['turns_per_cycle']} = A バンク {cost['a_bank_s']}s の"
        f"{cost['share_of_a_bank']:.1%}</text>"
    )
    parts.append("</svg>")
    FIGURE.write_text("\n".join(parts) + "\n")
    print(f"wrote {FIGURE.relative_to(ROOT)}  ({PANEL_W}x{height})")
    print(f"  ① parts in slots {list(held.values())}, yoke turns")
    print(f"  ② parts in slots {[mirror[name] for name in held]}, no turn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
