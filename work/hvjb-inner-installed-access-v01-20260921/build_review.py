# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw installed hand comparisons while preserving incomplete display wires."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import probe_access as A
import trimesh
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import to_rgb

ROOT = Path(__file__).resolve().parent
G = A.G
sys.modules["geometry"] = G
spec = importlib.util.spec_from_file_location("retained_access_renderer", A.T.PREVIOUS / "build_review.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
B = R.B
R.OUTPUT = A.OUTPUT
R.FIGURES = ROOT / "figures"
R.NAME = "内側ハウジングのハンド本体・配線・退避比較_v01_20260921"
text, box, arrow = B.text, B.box, B.arrow
COLORS = {
    "pad": B.TEAL,
    "carrier": B.BLUE,
    "thrust": B.ORANGE,
    "trial_stem": B.BLUE,
    "trial_shoe": B.BLUE,
    "catalogue_envelope": "#4a5c67",
}


def rows_for(product, keys):
    result = []
    for key in keys:
        color = B.ORANGE if key.startswith("W") else "#9baeb8"
        if key == "P01":
            color = "#bdc9cd"
        if key == "P02":
            color = "#64717a"
        for row in product[key]["meshes"]:
            result.append((np.asarray(row["vertices"]), np.asarray(row["faces"]), color))
    return result


def hand_rows(parts):
    return [(p["mesh"].vertices, p["mesh"].faces, COLORS[p["kind"]]) for p in parts]


def mesh_view(rows, name, view, figsize=(11, 7)):
    triangles, colors = [], []
    light = np.array([0.25, -0.45, 0.86])
    for vertices, faces, color in rows:
        tri = vertices[faces] * 1000
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
        shade = 0.55 + 0.45 * abs(normals @ light)
        triangles.append(tri)
        colors.append(np.clip(np.asarray(to_rgb(color)) * shade[:, None], 0, 1))
    triangles, colors = np.concatenate(triangles), np.concatenate(colors)
    view = np.asarray(view, dtype=float)
    view /= np.linalg.norm(view)
    right = np.cross([0, 0, 1], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    projected = np.stack((triangles @ right, triangles @ up), axis=-1)
    order = np.argsort(triangles.mean(1) @ view)
    fig, ax = B.plt.subplots(figsize=figsize, facecolor="white")
    ax.add_collection(PolyCollection(projected[order], facecolors=colors[order], edgecolors="none"))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.margins(0.05)
    ax.axis("off")
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    R.write_figure(fig, name)


def opening_cut(product, parts, origin, opening, name):
    fig, ax = B.plt.subplots(figsize=(5, 4), facecolor="white")
    selected = A.pose(parts, opening=opening)
    for piece in selected:
        if piece["kind"] in ("catalogue_envelope", "trial_shoe"):
            continue
        lines = trimesh.intersections.mesh_plane(piece["mesh"], [0, 1, 0], [0, -0.070, 0])
        if not len(lines):
            continue
        xy = np.unique((lines.reshape(-1, 3) - origin)[:, [0, 2]] * 1000, axis=0)
        center = xy.mean(0)
        xy = xy[np.argsort(np.arctan2(xy[:, 1] - center[1], xy[:, 0] - center[0]))]
        ax.fill(xy[:, 0], xy[:, 1], color=COLORS[piece["kind"]], lw=0)
    for row in product["I04"]["meshes"]:
        housing = G.mesh(row)
        lines = trimesh.intersections.mesh_plane(housing, [0, 1, 0], [0, -0.070, 0])
        xy = (lines - origin)[:, :, [0, 2]] * 1000
        ax.add_collection(LineCollection(xy, colors=B.INK, linewidths=1.3))
    for side in (-1, 1):
        arrow(ax, (side * 14, 10), (side * 14, 19), B.BLUE)
    text(ax, 0, -7, f"左右各 {opening * 1000:.0f} mm開く", 11, B.BLUE, True, align="center")
    ax.set(xlim=(-20, 20), ylim=(-10, 22))
    ax.set_aspect("equal")
    ax.axis("off")
    R.write_figure(fig, name)


def back_view(product, parts, origin):
    fig, ax = B.plt.subplots(figsize=(5, 4), facecolor="white")
    for key in ("I04", "WI41", "WI42"):
        color = "#d6dfe3" if key == "I04" else B.ORANGE
        for vertices, faces, _ in rows_for(product, [key]):
            xy = (vertices - origin)[:, :2] * 1000
            ax.add_collection(PolyCollection(xy[faces], facecolors=color, edgecolors="none"))
    for state, alpha in ((A.pose(parts, opening=0.002), 0.15), (A.pose(parts, opening=0.002, back=0.008), 0.8)):
        for piece in state:
            if piece["kind"] not in ("pad", "carrier", "thrust"):
                continue
            xy = (piece["mesh"].vertices - origin)[:, :2] * 1000
            ax.add_collection(
                PolyCollection(
                    xy[piece["mesh"].faces], facecolors=COLORS[piece["kind"]], edgecolors="none", alpha=alpha
                )
            )
    arrow(ax, (16, 43), (16, 51), B.RED)
    text(ax, -18, 55.5, "WI41", 10, B.RED, True)
    ax.set(xlim=(-21, 21), ylim=(27, 59))
    ax.set_aspect("equal")
    ax.axis("off")
    R.write_figure(fig, "back_wire")


def wire_overview(product):
    fig, ax = B.plt.subplots(figsize=(13, 4), facecolor="white")
    for key in [f"I0{i}" for i in range(1, 6)] + [k for k in product if k.startswith("WI")]:
        color = B.ORANGE if key.startswith("WI") else "#b8c9d2"
        for vertices, faces, _ in rows_for(product, [key]):
            ax.add_collection(PolyCollection(vertices[faces, :2] * 1000, facecolors=color, edgecolors="none"))
    for i, x in enumerate((-85.9, -52, -18.1, 55.05, 88.95), 1):
        text(ax, x, -117, f"I0{i}", 12, B.INK, True, align="center")
    ax.axhline(-68.5, color=B.MUTED, lw=0.8, ls="--")
    text(ax, -18.1, -59, "I03：保存された\n出口線なし", 10, B.GOLD, align="center")
    text(ax, 18, -71.5, "CAD後端", 10, B.MUTED)
    text(ax, -106, -45, "橙：写真から作った可視区間（実線径・奥行きは未確定）", 11, B.ORANGE)
    ax.set(xlim=(-113, 116), ylim=(-120, -42))
    ax.set_aspect("equal")
    ax.axis("off")
    R.write_figure(fig, "wire_coverage")


def page(number, title, subtitle):
    fig = B.plt.figure(figsize=(16.54, 11.69), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, 1600), ylim=(1100, 0))
    ax.axis("off")
    text(ax, 50, 52, title, 24, bold=True)
    text(ax, 50, 100, subtitle, 11.4, B.MUTED)
    text(ax, 1550, 49, f"INSTALLED ACCESS  {number:02d}", 9.5, B.MUTED, align="right")
    box(ax, 50, 128, 1500, 44, B.PALE, "#d1dfe6", radius=4)
    text(
        ax,
        68,
        150,
        "保存された製品表示モデル92項目・465メッシュとの比較。実配線、把持力、嵌合完了は未確定です。",
        11,
        B.BLUE,
    )
    ax.plot([50, 1550], [1024, 1024], color="#cbd8df", lw=1)
    text(
        ax,
        50,
        1050,
        "根拠：TE内外CAD、保存製品v03_p03、DH PGE-5-26公称寸法。メーカーCADと写真推定形状を区別。",
        9.5,
        B.MUTED,
    )
    text(
        ax,
        50,
        1080,
        "補助的な幾何観測。実機の接触・把持・配線変形・荷重・公差・アーム軌道の成立判定ではありません。",
        9.5,
        B.MUTED,
    )
    text(ax, 1550, 1080, "2026-09-21 / 5腕・20仕事を維持", 9, B.MUTED, align="right")
    return fig, ax


def hand_page():
    fig, ax = page(
        1,
        "ハンド本体を筐体の上へ置く比較",
        "前回の指先を小型平行ハンドへつなぐ案。PGE-5-26は既存の比較候補で、採用機種ではありません。",
    )
    box(ax, 50, 202, 925, 530, "white", "#d1dfe6")
    text(ax, 72, 234, "I04への配置例：本体は上、指先は筐体内", 14, B.BLUE, True)
    R.image_panel(fig, "installed_oblique", 64, 268, 897, 411)
    text(ax, 72, 703, "グレー：保存製品　橙：表示配線　濃灰：本体外形　青／緑：比較指", 10.5)
    box(ax, 1000, 202, 550, 530, "white", "#d1dfe6")
    text(ax, 1022, 234, "追加するのは左右の接続部", 14, B.BLUE, True)
    R.image_panel(fig, "hand_only", 1008, 260, 534, 376)
    text(ax, 1022, 673, "本体 55×26×95 mm：公称外形\n指の支持部と取付座：今回の比較形状", 11, B.MUTED)
    box(ax, 50, 758, 730, 228, B.PALE, "#d1dfe6")
    text(ax, 72, 792, "引き継ぐもの", 15, B.BLUE, True)
    text(
        ax,
        72,
        835,
        "後端を囲う2本指と、樹脂縁を押す面を維持。\n"
        "本体の爪間隔は図示で6.75 mm、4 mmずつ開くと14.75 mm。\n"
        "上へ伸ばす支持部の範囲は44 mmという比較値。\n"
        "既存のケーブル保持用40 mm後退・15度仕様とは別です。",
        11.6,
        va="top",
    )
    box(ax, 810, 758, 740, 228, B.CREAM, B.GOLD)
    text(ax, 832, 792, "まだ形状へ含めていないもの", 15, B.GOLD, True)
    text(
        ax,
        832,
        835,
        "本体の電気配線、アーム取付部、締結ねじ・ピン。\nPGE本体は既存の公称箱形状で、完全なメーカーCADではない。\n指の剛性・許容張り出し、樹脂縁の許容荷重も未確認。\nこの配置だけで機種適合を決めない。",
        11.6,
        va="top",
    )
    return fig


def release_page(observation):
    fig, ax = page(
        2,
        "退避方向を変えると、重なる相手が変わる",
        "指と本体の並進で占有する全領域を、保存された部品表面と照合。端点だけを比較した結果ではありません。",
    )
    panels = [
        (50, "back_wire", "各2 mm開く → 後方へ8 mm", "I04・I05で表示配線と重なる", B.RED),
        (560, "open2_cut", "各2 mm開く → 上へ50 mm", "5口とも下側の指がハウジングに重なる", B.RED),
        (1070, "open4_cut", "各4 mm開く → 上へ50 mm", "保存表面の領域内切出しは0件", B.TEAL),
    ]
    for x, image, title, caption, color in panels:
        box(ax, x, 202, 480, 411, "white", "#d1dfe6")
        text(ax, x + 20, 235, title, 12.2, B.BLUE, True)
        R.image_panel(fig, image, x + 10, 267, 460, 268)
        text(ax, x + 20, 576, caption, 10.5, color, True)
    text(
        ax,
        50,
        639,
        "左：指先付近の上面図。中央・右：I04後端の断面図。本体・取付座は拡大図の外。矢印は比較方向。",
        10.5,
        B.MUTED,
    )
    box(ax, 50, 665, 1500, 212, B.PALE, "#d1dfe6")
    columns = [72, 382, 752, 1172]
    for x, label in zip(columns, ("対象", "2 mm開放 → 後方", "2 mm開放 → 上方", "4 mm開放 → 上方"), strict=True):
        text(ax, x, 695, label, 12, B.BLUE, True)
    for index, row in enumerate(observation["bays"]):
        y = 734 + index * 28
        text(ax, columns[0], y, row["id"], 11.5)
        for x, name in zip(
            columns[1:],
            ("back_8_after_open_2_sweep", "lift_50_after_open_2_sweep", "lift_50_after_open_4_sweep"),
            strict=True,
        ):
            features = row["comparisons"][name]["positive_surface_features"]
            text(ax, x, y, "、".join(features) if features else "切出し0件", 11.5, B.RED if features else B.INK)
    box(ax, 50, 903, 1500, 90, B.CREAM, B.GOLD)
    text(ax, 72, 931, "4 mm開放＋上方退避を、次の配置検討に使う比較候補として残す。", 14, B.GOLD, True)
    text(
        ax,
        72,
        969,
        "保持解除後に部品が残る条件、実配線の占有範囲、指の荷重が揃うまでは、実行軌道や受入条件にはしません。",
        11.6,
    )
    return fig


def wire_page(observation):
    fig, ax = page(
        3,
        "実配線を含む確認には、出口まわりの整合が必要",
        "既存の表示線は写真の可視区間です。CADの穴との間を、推測した線で勝手につながないようにしています。",
    )
    box(ax, 50, 202, 1500, 401, "white", "#d1dfe6")
    R.image_panel(fig, "wire_coverage", 72, 214, 1456, 375)
    box(ax, 50, 627, 640, 260, B.PALE, "#d1dfe6")
    text(ax, 72, 660, "CAD後端と表示線の軸方向の空き", 14, B.BLUE, True)
    for i, key in enumerate(("I01", "I02", "I03", "I04", "I05")):
        gaps = [
            r["wire_min_y_minus_housing_rear_y_m"] * 1000
            for r in observation["wire_coverage"]["observations"]
            if r["nearby_inner"] == key
        ]
        label = f"{min(gaps):.3f} - {max(gaps):.3f} mm" if gaps else "対応する保存線なし"
        text(ax, 72, 704 + i * 31, key, 11.5)
        text(ax, 220, 704 + i * 31, label, 11.5)
    box(ax, 720, 627, 830, 260, B.CREAM, B.GOLD)
    text(ax, 742, 660, "この表は、実物にすき間があるという意味ではない", 14, B.GOLD, True)
    text(
        ax,
        742,
        708,
        "表示線は外径3 mmの仮形状。各穴・端子への接続先は未確定。\n"
        "I03の出口線、隠れた経路、HVIL線を含めた占有範囲が足りない。\n"
        "そのため、表面の重なり0件を「電線を避けられる」とは扱えない。\n"
        "接続部と配線の対応を先にそろえ、同じ指形状で再確認する。",
        11.7,
        va="top",
    )
    box(ax, 50, 913, 1500, 80, "white", "#d1dfe6")
    text(
        ax,
        72,
        953,
        "今回の到達点：本体配置と退避方向の比較まで。5腕・20仕事・1段往復パレットの工程構成は維持。",
        12.5,
        B.BLUE,
        True,
    )
    return fig


def main():
    R.FIGURES.mkdir(parents=True, exist_ok=True)
    (A.OUTPUT / "pdf").mkdir(parents=True, exist_ok=True)
    observation = json.loads((A.OUTPUT / "installed_access_observations.json").read_text())
    assert observation["script_sha256"] == A.P.sha(ROOT / "probe_access.py")
    product, manifest = A.P.load_product()
    pge = json.loads(A.gzip.decompress((A.P.DATA / "hvjb_pge_finger_v01_meshes.json.gz").read_bytes()))
    inners, _, _, _ = G.load_sources()
    parts, mapping = A.build_hand(inners["2103245-4"], product["I04"], pge)
    origin = np.array(mapping["inner_origin_world_m"])
    mesh_view(rows_for(product, list(product)) + hand_rows(parts), "installed_oblique", [0.7, -1.7, 1.5])
    mesh_view(rows_for(product, ["I04"]) + hand_rows(parts), "hand_only", [0.6, 1.7, 0.6], (5, 7))
    opening_cut(product, parts, origin, 0.002, "open2_cut")
    opening_cut(product, parts, origin, 0.004, "open4_cut")
    back_view(product, parts, origin)
    wire_overview(product)
    path, pages = R.save_pages([hand_page(), release_page(observation), wire_page(observation)])
    result = {
        "pdf": str(path.relative_to(ROOT)),
        "sha256": A.P.sha(path),
        "pages": pages,
        "renderer_sha256": A.P.sha(Path(__file__)),
        "observation_sha256": A.P.sha(A.OUTPUT / "installed_access_observations.json"),
        "product_input_sha256": manifest["parent_sha256"],
        "reused_renderer_sha256": A.P.sha(A.T.PREVIOUS / "build_review.py"),
    }
    (A.OUTPUT / "document_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("INSTALLED_ACCESS_PDF_COMPLETE", path, flush=True)


if __name__ == "__main__":
    main()
