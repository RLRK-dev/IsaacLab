# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw the comparison-only rear-rim pusher and its geometric limits."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import rear_thrust as T
from matplotlib.collections import LineCollection, PolyCollection

G = T.G
sys.modules["geometry"] = G
spec = importlib.util.spec_from_file_location("retained_tip_renderer", T.PREVIOUS / "build_review.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
B = R.B
ROOT = T.ROOT
NAME = "内側ハウジング後端の押し面比較_v01_20260921"
R.NAME, R.OUTPUT, R.FIGURES = NAME, T.OUTPUT, ROOT / "figures"
text, box, arrow = B.text, B.box, B.arrow


def render_rim(housing, pieces):
    fig, ax = B.plt.subplots(figsize=(9, 5), facecolor="white")
    pushing = [piece for piece in pieces if piece["name"] == "thrust"]
    flat = T.rear_faces(housing)
    for piece in pushing:
        polygon = piece["mesh"].vertices[:4, :2] * 1000
        ax.fill(polygon[:, 0], polygon[:, 1], color="#f9e1c9", lw=0)
    ax.add_collection(PolyCollection(flat[:, :, :2] * 1000, facecolors="#afbec6", edgecolors="none"))
    patches = T.xy_projection_patches(flat, pushing)
    ax.add_collection(PolyCollection([p[:, :2] * 1000 for p in patches], facecolors=B.ORANGE, edgecolors="none"))
    for loop in T.cavity_loops(housing):
        closed = np.vstack([loop, loop[0]])
        ax.add_collection(LineCollection([closed[:, :2] * 1000], colors=B.INK, linewidths=0.8))
    text(ax, 0, 7.5, "電線が出る側から見た図", 13, B.INK, True, align="center")
    text(ax, 0, -6.6, "橙：樹脂縁と押し面の重なり　各 約2.74 mm²", 11, B.ORANGE, True, align="center")
    text(ax, 0, -9.0, "穴の輪郭：後端から0.0005 mm内側のCAD断面", 9, B.MUTED, align="center")
    for sign in (-1, 1):
        arrow(ax, (sign * 13, 0), (sign * 9.0, 0), B.ORANGE)
    ax.set(xlim=(-16, 16), ylim=(-11, 10))
    ax.set_aspect("equal")
    ax.axis("off")
    R.write_figure(fig, "rear_rim")


def page(number, title, subtitle):
    fig = B.plt.figure(figsize=(16.54, 11.69), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, 1600), ylim=(1100, 0))
    ax.axis("off")
    text(ax, 50, 52, title, 24, bold=True)
    text(ax, 50, 100, subtitle, 11.5, B.MUTED)
    text(ax, 1550, 49, f"REAR THRUST  {number:02d}", 10, B.MUTED, align="right")
    box(ax, 50, 128, 1500, 44, B.PALE, "#d1dfe6", radius=4)
    text(
        ax, 68, 150, "比較形状です。TEの部品CADは変更せず、製作寸法・把持力・アーム動作は確定していません。", 11, B.BLUE
    )
    ax.plot([50, 1550], [1024, 1024], color="#cbd8df", lw=1)
    text(
        ax, 50, 1050, "出典：TE 2103245 Rev A1・2103340 Rev A2・2103346 Rev A3・408-32095 Rev B、保存CAD", 9.5, B.MUTED
    )
    text(
        ax,
        50,
        1080,
        "補助的な幾何比較。許容荷重・実電線・公差・変形・ハンド本体・嵌合保持の成立は未評価。",
        9.5,
        B.MUTED,
    )
    text(ax, 1550, 1080, "2026-09-21 / 5腕・20仕事は維持", 9, B.MUTED, align="right")
    return fig, ax


def shape_page():
    fig, ax = page(
        1,
        "後端の樹脂縁を押す面を、保持指へ追加",
        "前回の後端保持案に、軸方向の押し面を加える比較。電線そのものを押す構成にはしません。",
    )
    box(ax, 50, 202, 815, 445, "white", "#d1dfe6")
    text(ax, 72, 235, "全体形状：左右の指へ小さな段を追加", 14, B.BLUE, True)
    R.image_panel(fig, "trial_oblique", 63, 267, 790, 310)
    text(ax, 72, 614, "灰：内側ハウジング　緑：保持パッド　青：支持部　橙：押し面", 10.8)
    box(ax, 892, 202, 658, 445, "white", "#d1dfe6")
    text(ax, 914, 235, "押すのは穴の周囲にある樹脂の縁", 14, B.BLUE, True)
    R.image_panel(fig, "rear_rim", 904, 260, 634, 359)
    cards = [
        (
            50,
            "保持する面",
            B.TEAL,
            "後端外周を囲うパッドを維持。\n軸方向の帯幅は3.1 mm。\n"
            "0.1 mmの表示逃げを残すため、\nこの図は把持成立を示さない。",
        ),
        (
            560,
            "押す面",
            B.ORANGE,
            "後端に段を付け、樹脂縁へ当てる。\n穴の中央は開いたままにする。\n"
            "CAD上の重なりは左右合計\n約5.48 mm²。荷重時の面積とは別。",
        ),
        (
            1070,
            "電線出口との関係",
            B.BLUE,
            "図の穴断面と押し面の投影は\n重なり0 mm²（5口とも同じ）。\n"
            "実電線が曲がって指に当たるかは、\n実装した配線形状で別に確認する。",
        ),
    ]
    for x, title, color, body in cards:
        box(ax, x, 674, 480, 205, B.PALE, "#d1dfe6")
        text(ax, x + 20, 707, title, 15, color, True)
        text(ax, x + 20, 746, body, 11.6, va="top")
    box(ax, 50, 904, 1500, 90, B.CREAM, B.GOLD)
    text(ax, 72, 932, "縁が細いため、押し面の存在だけで採用は決められません。", 14, B.GOLD, True)
    text(ax, 72, 969, "後端樹脂縁の許容荷重と必要挿入力は未確認。今回追加した段の寸法は、比較用として保存します。", 12)
    return fig


def access_page(observations):
    fig, ax = page(
        2,
        "開く空間と、手を離す順番を分けて確認",
        "I02の中央断面。部品を静止させた表示位置で、指先だけを左右各2 mm開き、その後8 mm後退させる比較。",
    )
    for x, name, title in [
        (50, "rear_closed", "① 後端を囲い、樹脂縁へ押し面を当てる"),
        (815, "rear_open", "② 部品を残したまま、左右に指を開く"),
    ]:
        box(ax, x, 202, 735, 401, "white", "#d1dfe6")
        text(ax, x + 20, 236, title, 13, B.BLUE, True)
        R.image_panel(fig, name, x + 10, 257, 715, 320)
    text(ax, 50, 627, "茶：外側ヘッダー　灰：内側ハウジング　色付き：比較指先　破線：ヘッダー後端の目安", 10.5, B.MUTED)
    box(ax, 50, 651, 695, 224, "white", "#d1dfe6")
    text(ax, 70, 677, "5口での指先とヘッダーの軸方向距離", 14, B.BLUE, True)
    text(ax, 70, 712, "接続口 / キー", 11, B.MUTED)
    text(ax, 470, 712, "公称CAD包絡間隔", 11, B.MUTED)
    for index, row in enumerate(observations["bays"]):
        gap = row["release_comparison"]["whole_header_axial_aabb_separation_m"] * 1000
        text(ax, 70, 742 + 25 * index, f"{row['id']}   {row['header']} / {row['key']}", 11)
        text(ax, 470, 742 + 25 * index, f"{gap:.3f} mm", 11, B.BLUE)
    box(ax, 774, 651, 776, 224, B.PALE, "#d1dfe6")
    text(ax, 794, 678, "この間隔が説明する範囲", 14, B.BLUE, True)
    text(
        ax,
        794,
        718,
        "指の開放・後退の全区間は、両端位置の包絡内に入る。\n保存ヘッダーと壁に対しては、その包絡が離れている。\nただし、内外部品の位置は既存モデルの表示配置。\n実物の嵌合位置・公差を確認した安全余裕ではない。",
        11.7,
        va="top",
    )
    steps = [
        (50, "押し込み", "樹脂縁を押す案"),
        (430, "嵌合後の保持を確認", "確認方法・条件は未確定"),
        (810, "指を開く", "部品を残すことが前提"),
        (1190, "指を後退", "アーム軌道は別に検討"),
    ]
    for index, (x, title, body) in enumerate(steps):
        box(ax, x, 904, 360, 88, B.CREAM if index == 1 else B.PALE, B.GOLD if index == 1 else "#d1dfe6")
        text(ax, x + 15, 932, title, 13, B.GOLD if index == 1 else B.BLUE, True)
        text(ax, x + 15, 970, body, 10.5)
        if index < 3:
            arrow(ax, (x + 361, 948), (x + 379, 948))
    return fig


def main():
    R.FIGURES.mkdir(parents=True, exist_ok=True)
    (T.OUTPUT / "pdf").mkdir(parents=True, exist_ok=True)
    observations = json.loads((T.OUTPUT / "rear_thrust_observations.json").read_text())
    assert observations["geometry_script_sha256"] == G.sha(ROOT / "rear_thrust.py")
    inners, headers, _, _ = G.load_sources()
    housing = G.mesh(inners["2103245-1"])
    pieces = T.make_tips(housing)
    R.render_oblique(housing, pieces)
    render_rim(housing, pieces)
    header = G.header_in_inner_frame(G.mesh(headers["2103340-1"]), 0)
    d_housing = G.mesh(inners["2103245-4"])
    R.render_cut(d_housing, header, pieces, "rear_closed")
    R.render_cut(d_housing, header, [G.moved_piece(piece, opening=0.002) for piece in pieces], "rear_open")
    path, pages = R.save_pages([shape_page(), access_page(observations)])
    record = {
        "pdf": str(path.relative_to(ROOT)),
        "sha256": G.sha(path),
        "pages": pages,
        "observation_json_sha256": G.sha(T.OUTPUT / "rear_thrust_observations.json"),
        "renderer_sha256": G.sha(Path(__file__)),
        "reused_renderer_sha256": G.sha(T.PREVIOUS / "build_review.py"),
        "style_sha256": G.sha(R.STYLE),
    }
    (T.OUTPUT / "document_audit.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print("REAR_THRUST_PDF_COMPLETE", path, flush=True)


if __name__ == "__main__":
    main()
