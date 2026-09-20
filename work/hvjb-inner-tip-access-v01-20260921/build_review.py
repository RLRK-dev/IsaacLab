# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw source-CAD fingertip comparisons and their static access observations."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import geometry as G
import numpy as np
import trimesh
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import to_rgb
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
FIGURES = ROOT / "figures"
NAME = "内側ハウジング指先の3D比較と開放空間_v01_20260921"
STYLE = ROOT.parent / "hvjb-hand-plan-v01-20260920/draw_plan.py"
spec = importlib.util.spec_from_file_location("tip_access_style", STYLE)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
text, box, rect, arrow = B.text, B.box, B.rect, B.arrow
INK, BLUE, MUTED, TEAL, ORANGE, RED = B.INK, B.BLUE, B.MUTED, B.TEAL, B.ORANGE, B.RED
COLORS = {"pad": TEAL, "carrier": BLUE, "thrust": ORANGE}


def write_figure(fig, name):
    fig.savefig(FIGURES / (name + ".png"), dpi=170, bbox_inches="tight", pad_inches=0.04)
    B.plt.close(fig)


def render_oblique(housing, pieces):
    triangles, colors = [], []
    for solid, color in [(housing, "#b9c7ce"), *((p["mesh"], COLORS[p["name"]]) for p in pieces)]:
        points = solid.vertices[:, [2, 0, 1]] * 1000
        points[:, 0] += 42.6
        tri = points[solid.faces]
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
        light = np.array([0.2, -0.5, 0.84])
        shade = 0.52 + 0.48 * abs(normals @ light)
        colors.extend(np.clip(np.asarray(to_rgb(color)) * shade[:, None], 0, 1))
        triangles.extend(tri)
    triangles = np.asarray(triangles)
    view = np.array([-1.2, -2.0, 1.0])
    view /= np.linalg.norm(view)
    right = np.cross([0, 0, 1], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    projected = np.stack((triangles @ right, triangles @ up), axis=-1)
    order = np.argsort(triangles.mean(axis=1) @ view)
    fig, ax = B.plt.subplots(figsize=(11, 6), facecolor="white")
    ax.add_collection(PolyCollection(projected[order], facecolors=np.asarray(colors)[order], edgecolors="none"))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.margins(0.08)
    ax.axis("off")
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    write_figure(fig, "trial_oblique")


def render_rear_section(housing, pieces):
    fig, ax = B.plt.subplots(figsize=(8, 5), facecolor="white")
    source_z = G.CONFIG["source_section_z_m"]
    for piece in pieces:
        if piece["name"] != "thrust":
            poly = piece["mesh"].vertices[:4, :2] * 1000
            ax.fill(poly[:, 0], poly[:, 1], color=COLORS[piece["name"]], lw=0)
    lines = trimesh.intersections.mesh_plane(housing, [0, 0, 1], [0, 0, source_z])
    ax.add_collection(LineCollection(lines[:, :, :2] * 1000, colors=INK, linewidths=1.3))
    for sign in (-1, 1):
        arrow(ax, (sign * 16, 0), (sign * 12, 0), BLUE)
    arrow(ax, (-11.375, -8), (11.375, -8), MUTED, both=True)
    text(ax, 0, -9.8, "閉じた指先全幅 22.75 mm", 11, MUTED, align="center")
    ax.set(xlim=(-18, 18), ylim=(-12, 10))
    ax.set_aspect("equal")
    ax.axis("off")
    write_figure(fig, "rear_section")


def clip_segment(a, b, planes):
    normals, limits = planes
    lower, upper = 0.0, 1.0
    for normal, limit in zip(normals, limits, strict=True):
        origin, rate = normal @ a - limit, normal @ (b - a)
        if abs(rate) < 1e-14:
            if origin > 0:
                return None
        elif rate > 0:
            upper = min(upper, -origin / rate)
        else:
            lower = max(lower, -origin / rate)
    if upper - lower <= 1e-10:
        return None
    return np.array([a + lower * (b - a), a + upper * (b - a)])


def cut_xy(points):
    """Display header-local axial Y horizontally and transverse X vertically [mm]."""
    points = np.asarray(points)
    return np.stack((-points[..., 2] - 0.0311, points[..., 0]), axis=-1) * 1000


def render_cut(housing, header, pieces, name):
    fig, ax = B.plt.subplots(figsize=(9, 7), facecolor="white")
    for y in (-18, 11.4):
        rect(ax, 0, y, 3, 6.6, "#d4dadd")
    header_lines = trimesh.intersections.mesh_plane(header, [0, 1, 0], [0, 0, 0])
    inner_lines = trimesh.intersections.mesh_plane(housing, [0, 1, 0], [0, 0, 0])
    for piece in pieces:
        section = trimesh.intersections.mesh_plane(piece["mesh"], [0, 1, 0], [0, 0, 0])
        if not len(section):
            continue
        points = np.unique(cut_xy(section.reshape(-1, 3)), axis=0)
        center = points.mean(0)
        points = points[np.argsort(np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0]))]
        ax.fill(points[:, 0], points[:, 1], color=COLORS[piece["name"]], alpha=0.85, lw=0)
    ax.add_collection(LineCollection(cut_xy(inner_lines), colors="#869aa6", linewidths=1.2))
    ax.add_collection(LineCollection(cut_xy(header_lines), colors="#b16b2f", linewidths=1.2))
    overlaps = []
    for piece in pieces:
        for a, b in header_lines:
            section = clip_segment(a, b, piece["planes"])
            if section is not None:
                overlaps.append(cut_xy(section))
    if overlaps:
        ax.add_collection(LineCollection(overlaps, colors=RED, linewidths=3.3))
    ax.axvline(7.55, color=MUTED, lw=1, ls="--")
    text(ax, -1.2, 16.3, "外側", 11, MUTED, align="center")
    text(ax, 17, 16.3, "筐体内側", 11, MUTED, align="center")
    text(ax, 1.5, -16, "壁 3 mm（表示仮定）", 9.5, MUTED, align="center")
    ax.set(xlim=(-4, 25), ylim=(-18, 18))
    ax.set_aspect("equal")
    ax.axis("off")
    write_figure(fig, name)


def render_shoulder(housing):
    centers = housing.triangles_center
    selected = (abs(centers[:, 2] + 0.0339) < 1e-8) & (housing.face_normals[:, 2] < -0.99)
    fig, ax = B.plt.subplots(figsize=(8, 4), facecolor="white")
    ax.add_collection(
        PolyCollection(housing.triangles[selected, :, :2] * 1000, facecolors="#c9d4d9", edgecolors="none")
    )
    for x in (-10.4, 9.4):
        ax.add_patch(B.Rectangle((x, -0.8), 1, 1.6, fc=ORANGE, ec=RED, alpha=0.7, lw=1.5))
    ax.set(xlim=(-13, 13), ylim=(-7, 7))
    ax.set_aspect("equal")
    ax.axis("off")
    write_figure(fig, "shoulder")


def page(number, title, subtitle):
    fig = B.plt.figure(figsize=(16.54, 11.69), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, 1600), ylim=(1100, 0))
    ax.axis("off")
    text(ax, 50, 52, title, 24, bold=True)
    text(ax, 50, 100, subtitle, 11.5, MUTED)
    text(ax, 1550, 49, f"TIP ACCESS  {number:02d}", 10, MUTED, align="right")
    box(ax, 50, 128, 1500, 44, B.PALE, "#d1dfe6", radius=4)
    text(
        ax, 68, 150, "部品CADは変更せず、専用2本指を比較。指先寸法・把持力・軌道の採用はまだ行っていません。", 11, BLUE
    )
    ax.plot([50, 1550], [1024, 1024], color="#cbd8df", lw=1)
    text(ax, 50, 1050, "補助的な静止幾何観測。電線・ハンド本体・公差・荷重・変形・ロック成立は含まない。", 10, MUTED)
    text(ax, 50, 1080, "根拠：TE保存CAD・2103245 Rev A1・2103340 Rev A2・2103346 Rev A3・408-32095 Rev B", 9, MUTED)
    text(ax, 1550, 1080, "2026-09-21 / 5腕・20仕事は維持", 9, MUTED, align="right")
    return fig, ax


def image_panel(fig, name, x, y, width, height):
    ax = fig.add_axes((x / 1600, 1 - (y + height) / 1100, width / 1600, height / 1100))
    with Image.open(FIGURES / (name + ".png")) as source:
        ax.imshow(source)
    ax.axis("off")


def geometry_page():
    fig, ax = page(
        1,
        "後端を囲う2本指を、CAD形状に合わせて3D化",
        "前回の模式図を寸法付きの比較形状にした段階。完成したハンドの設計図ではありません。",
    )
    box(ax, 50, 201, 905, 469, "white", "#d1dfe6")
    text(ax, 72, 232, "灰：TE内側ハウジング　／　色付き：追加した指先", 14, BLUE, True)
    image_panel(fig, "trial_oblique", 60, 270, 883, 305)
    text(ax, 80, 617, "電線側の後端を囲う。前方のキーと差込み部はそのまま。", 11.5)
    box(ax, 985, 201, 565, 469, "white", "#d1dfe6")
    text(ax, 1007, 232, "後端の横断面と閉じた指先", 14, BLUE, True)
    image_panel(fig, "rear_section", 994, 270, 545, 315)
    text(ax, 1007, 625, "CAD Z=−40 mm断面。内部空洞は推定補完しない。", 10.3, MUTED)
    rows = [
        (
            50,
            "緑：輪郭に沿うパッド",
            TEAL,
            "後端の外周を複数面で囲う。\n0.1 mmのすき間は図示用で、\n把持力や閉じ量を表すものではない。",
        ),
        (
            560,
            "青：パッドを支える部分",
            BLUE,
            "接触帯の軸方向長さは4.5 mm。\n外周から最大3.0 mmの厚さを\n置いた比較。取付具はまだ含まない。",
        ),
        (
            1070,
            "橙：つばを押す段付き面",
            ORANGE,
            "1.0 × 1.6 mmの面を左右に配置。\n電線ではなく樹脂のつばへ\n押す力を伝える案として調べる。",
        ),
    ]
    for x, title, color, body in rows:
        box(ax, x, 699, 480, 205, B.PALE, "#d1dfe6")
        text(ax, x + 20, 732, title, 15, color, True)
        text(ax, x + 20, 779, body, 11.8, va="top")
    box(ax, 50, 928, 1500, 66, B.CREAM, B.GOLD)
    text(
        ax,
        70,
        960,
        "3D化すると外側ヘッダーとの重なりが見つかったため、2ページ目で位置関係を示します。",
        12.5,
        B.GOLD,
        True,
    )
    return fig


def overlap_page(observations):
    fig, ax = page(
        2,
        "その位置で指を開くと、ヘッダーと筐体壁に重なる",
        "中央のI02（KEY D）の中心断面。内外ハウジングの位置は既存表示モデルを継承し、実測嵌合位置とは区別。",
    )
    for x, name, title in ((50, "cut_closed", "① 閉じた比較位置"), (570, "cut_open", "② 左右へ各2 mm開いた比較位置")):
        box(ax, x, 200, 490, 496, "white", "#d1dfe6")
        text(ax, x + 18, 233, title, 14, BLUE, True)
        image_panel(fig, name, x + 10, 258, 470, 388)
        text(ax, x + 18, 672, "赤い線：指先体積に入ったヘッダー断面", 10.2, RED)
    box(ax, 1090, 200, 460, 496, B.PALE, "#d1dfe6")
    text(ax, 1110, 233, "断面の読み方", 15, BLUE, True)
    text(
        ax,
        1110,
        283,
        "茶：外側ヘッダーのCAD断面\n灰線：内側ハウジングのCAD断面\n灰帯：筐体壁の表示範囲\n緑・青・橙：追加した指先",
        11.5,
        va="top",
    )
    text(
        ax,
        1110,
        422,
        "閉じた位置でも青い支持部と\n橙の段付き面がヘッダーに重なる。\n"
        "開くと段付き面は壁の開口外へ\n最大1.00 mm出る（I02）。",
        12,
        RED,
        va="top",
    )
    text(
        ax,
        1110,
        570,
        "破線はヘッダー全体の後端位置\n約7.55 mm。中心断面上の\n局所面そのものではありません。",
        10.4,
        MUTED,
        va="top",
    )
    box(ax, 50, 723, 680, 257, "white", "#d1dfe6")
    text(ax, 69, 755, "つば押し面も左右同じには支えられない", 14, BLUE, True)
    image_panel(fig, "shoulder", 67, 775, 317, 173)
    shoulders = observations["bays"][0]["flat_shoulder"]["sides"]
    values = [r["cad_flat_face_under_thrust_rectangle_m2"] * 1e6 for r in shoulders]
    text(
        ax,
        404,
        804,
        f"矩形面：各1.600 mm²\nCAD面がある範囲：\n左 {values[0]:.3f} / 右 {values[1]:.3f} mm²",
        11.3,
        va="top",
    )
    text(ax, 405, 924, "荷重下の接触面積ではない。", 10, MUTED)
    box(ax, 760, 723, 790, 257, B.CREAM, B.GOLD)
    text(ax, 780, 755, "後退した終点だけでは、動作は決まらない", 15, B.GOLD, True)
    text(
        ax,
        780,
        806,
        "8 mm後退してから開いた静止位置では、今回の切出しは0件。\n"
        "ただし、閉じて保持したまま後退すれば部品も引いてしまいます。\n"
        "開放の途中・ハウジングの残留保持・電線の動きは未確認です。",
        12,
        va="top",
    )
    text(ax, 780, 931, "「後退→開く」を完成した退避手順として採用していません。", 11, B.GOLD)
    return fig


def comparison_page(observations):
    fig, ax = page(
        3,
        "後端側に寄せる比較では、押す面を別に考える必要がある",
        "比較B：接触帯を最後端側の3.1 mmへ移し、つばまで延びる段付き面を外した形状。採用寸法ではありません。",
    )
    box(ax, 50, 200, 610, 515, "white", "#d1dfe6")
    text(ax, 70, 233, "比較B：I02の中心断面", 15, BLUE, True)
    image_panel(fig, "cut_rear", 62, 260, 585, 390)
    text(ax, 70, 683, "後端側の指先。つばを押す橙の面は含まない。", 11, MUTED)
    box(ax, 690, 200, 860, 515, "white", "#d1dfe6")
    text(ax, 710, 233, "5か所を同じ条件で照合", 15, BLUE, True)
    columns = [(716, "接続口"), (885, "元案：重なる面※"), (1108, "比較B※"), (1282, "公称投影余白")]
    for x, title in columns:
        text(ax, x, 294, title, 11, MUTED, True)
    for i, bay in enumerate(observations["bays"]):
        y = 342 + 49 * i
        initial = bay["states"][0]
        rear = bay["states"][3]
        count = initial["outer_header_surface_in_tip_volumes"]["unique_source_triangles_with_positive_clipped_area"]
        bcount = rear["outer_header_surface_in_tip_volumes"]["unique_source_triangles_with_positive_clipped_area"]
        margin = -initial["aperture"]["max_signed_projected_distance_to_nominal_aperture_m"] * 1000
        for x, content in zip(
            [716, 930, 1140, 1320],
            [f"{bay['id']} / {bay['key']}", str(count), str(bcount), f"{margin:.3f} mm"],
            strict=True,
        ):
            text(ax, x, y, content, 12)
    text(
        ax,
        710,
        614,
        "※指先体積に面積を持って入る外側ヘッダーの三角形数。\n0件は全面的な非干渉保証ではない。電線・ハンド本体は対象外。",
        10.5,
        MUTED,
        va="top",
    )
    text(ax, 710, 682, "隣の内側ハウジングとのX区間余白：開いた指先で最小9.325 mm。", 10.5, MUTED)
    box(ax, 50, 744, 730, 246, B.PALE, "#d1dfe6")
    text(ax, 71, 778, "形状比較で分かったこと", 15, BLUE, True)
    text(
        ax,
        71,
        826,
        "後端へ寄せると、保存ヘッダー表面との重なりは今回0件。\n"
        "ただし閉じた指先の開口への投影余白は変わりません。\n"
        "約0.025 mmを製造・位置決めの許容値にはできません。",
        12,
        va="top",
    )
    box(ax, 810, 744, 740, 246, B.CREAM, B.GOLD)
    text(ax, 830, 778, "次の設計対象", 15, B.GOLD, True)
    text(
        ax,
        830,
        826,
        "後端を囲う保持と、軸方向に押す面を両立させる形状。\n短い樹脂部の荷重・電線出口・開放中の保持も確認する。\nこの比較だけでアーム軌道や把持成立を確定しない。",
        12,
        va="top",
    )
    return fig


def save_pages(figures):
    records = []
    path = OUTPUT / "pdf" / (NAME + ".pdf")
    with B.PdfPages(
        path, metadata={"Title": NAME, "Subject": "Source CAD and comparison-only static fingertip geometry"}
    ) as pdf:
        for index, fig in enumerate(figures, 1):
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            overflow = []
            for ax in fig.axes:
                for label in ax.texts:
                    bounds = label.get_window_extent(renderer)
                    if not fig.bbox.contains(bounds.x0, bounds.y0) or not fig.bbox.contains(bounds.x1, bounds.y1):
                        overflow.append(label.get_text())
            assert not overflow, overflow
            pdf.savefig(fig)
            records.append({"page": index, "text_outside_page": overflow})
            B.plt.close(fig)
    return path, records


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "pdf").mkdir(parents=True, exist_ok=True)
    observations = json.loads((OUTPUT / "tip_access_observations.json").read_text())
    inners, headers, _, _ = G.load_sources()
    housing = G.mesh(inners["2103245-1"])
    pieces, _ = G.build_tips(housing)
    render_oblique(housing, pieces)
    render_rear_section(housing, pieces)
    render_shoulder(housing)
    d_housing = G.mesh(inners["2103245-4"])
    header = G.header_in_inner_frame(G.mesh(headers["2103340-1"]), 0)
    render_cut(d_housing, header, pieces, "cut_closed")
    render_cut(d_housing, header, [G.moved_piece(p, opening=0.002) for p in pieces], "cut_open")
    render_cut(d_housing, header, G.rear_only_tips(pieces), "cut_rear")
    path, pages = save_pages([geometry_page(), overlap_page(observations), comparison_page(observations)])
    (OUTPUT / "document_audit.json").write_text(
        json.dumps(
            {
                "pdf": str(path.relative_to(ROOT)),
                "sha256": G.sha(path),
                "pages": pages,
                "observation_json_sha256": G.sha(OUTPUT / "tip_access_observations.json"),
                "renderer_sha256": G.sha(Path(__file__)),
            },
            indent=2,
        )
        + "\n"
    )
    print("TIP_ACCESS_PDF_COMPLETE", path)


if __name__ == "__main__":
    main()
