# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw a comparison-only rear grip using the preserved TE inner-housing mesh."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import trimesh
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image

ROOT = Path(__file__).resolve().parent
REF = ROOT.parents[1] / "eval_runs/ur15_jb_harness_revision_20260907"
CAD = REF / "data/hvjb_photo_cad_v01.json.gz"
DRAWING = REF / "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf"
INSTRUCTION = REF / "references/connector_correction_20260915/te_408_32095_instruction.pdf"
INPUTS = REF / "data/hvjb_header_interface_inputs_v01.json"
PLAN = ROOT.parent / "hvjb-hand-plan-v01-20260920/data/hand_plan.json"
PRIOR = ROOT.parent / "hvjb-header-retention-v01-20260921/output/retention_review.json"
STYLE = ROOT.parent / "hvjb-hand-plan-v01-20260920/draw_plan.py"
NAME = "内側ハウジングの把持候補と指の退避_v01_20260921"
PINS = {
    CAD: "1ac417baa3ff67ae8bc3ed5c32ac91cfb778a2effbd1e1a19d24900066c38f32",
    DRAWING: "23aff5f20acb75d87a63bf3a1aa0c076a8ab43b30c83914cfc8e5c9b41788ffa",
    INSTRUCTION: "cd13cd856b679e2683f7672f079bd4c99ff87ac2e361d3da73700e12c12fa63d",
}

spec = importlib.util.spec_from_file_location("inner_grasp_style", STYLE)
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)
text, box, rect, arrow = BASE.text, BASE.box, BASE.rect, BASE.arrow
INK, BLUE, DARK, MUTED = BASE.INK, BASE.BLUE, BASE.DARK, BASE.MUTED
PALE, CREAM, GOLD, TEAL = BASE.PALE, BASE.CREAM, BASE.GOLD, BASE.TEAL
ORANGE, METAL = BASE.ORANGE, BASE.METAL


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_data():
    """Read exact meshes and retain nominal section observations in SI units."""
    for path, expected in PINS.items():
        assert sha(path) == expected, path
    cad = json.loads(gzip.decompress(CAD.read_bytes()))
    records = {}
    for number in ("2103245-1", "2103245-4", "2103245-5", "2103245-6"):
        row = cad[number]
        mesh = trimesh.Trimesh(vertices=row["vertices"], faces=row["faces"], process=False)
        sections = []
        for source_z in (-0.002, -0.020, -0.030, -0.0326, -0.033, -0.035, -0.040, -0.042):
            lines = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, source_z])
            assert len(lines), (number, source_z)
            points = lines.reshape(-1, 3)
            sections.append(
                {
                    "source_z_m": source_z,
                    "segment_count": len(lines),
                    "xy_min_m": points[:, :2].min(axis=0).tolist(),
                    "xy_max_m": points[:, :2].max(axis=0).tolist(),
                }
            )
        records[number] = {
            "key": row["key"],
            "vertex_count": len(mesh.vertices),
            "face_count": len(mesh.faces),
            "source_bounds_m": mesh.bounds.tolist(),
            "aabb_extents_m": mesh.extents.tolist(),
            "nominal_plane_sections": sections,
        }
    return cad, records


def display_mesh(row):
    """Apply a proper axis permutation; rear is left and the nose is right."""
    vertices = np.asarray(row["vertices"], dtype=float) * 1000
    # Source Z=0 is the insertion nose; Z=-42.6 mm is the wire-entry rear.
    result = vertices[:, [2, 0, 1]].copy()
    result[:, 0] += 42.6
    return result, np.asarray(row["faces"], dtype=int)


def mesh_colors(vertices, faces):
    centers = vertices[faces].mean(axis=1)
    colors = np.tile(to_rgb("#b4c5cf"), (len(faces), 1))
    # Broad visual-region overlays, not measured contact patches or CAD edits.
    colors[centers[:, 0] < 7.8] = to_rgb(TEAL)
    colors[(centers[:, 0] >= 8.4) & (centers[:, 0] <= 10.2)] = to_rgb(ORANGE)
    triangle = vertices[faces]
    normal = np.cross(triangle[:, 1] - triangle[:, 0], triangle[:, 2] - triangle[:, 0])
    length = np.linalg.norm(normal, axis=1)
    normal /= np.maximum(length[:, None], 1e-15)
    light = np.array([0.25, -0.5, 0.83])
    brightness = 0.60 + 0.40 * np.abs(normal @ (light / np.linalg.norm(light)))
    return np.clip(colors * brightness[:, None], 0, 1)


def render_meshes(row):
    """Reuse source triangles for two orthographic views and one oblique view."""
    vertices, faces = display_mesh(row)
    colors = mesh_colors(vertices, faces)
    triangle = vertices[faces]
    for label, coordinates, depth in (("top", (0, 1), 2), ("rear", (1, 2), 0)):
        fig, ax = BASE.plt.subplots(figsize=(9, 5), facecolor="white")
        order = np.argsort(triangle[:, :, depth].mean(axis=1))
        if label == "rear":
            order = order[::-1]
        projected = triangle[:, :, coordinates]
        ax.add_collection(PolyCollection(projected[order], facecolors=colors[order], edgecolors="none"))
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.margins(0.09)
        ax.axis("off")
        fig.savefig(ROOT / f"figures/{label}.png", dpi=180, bbox_inches="tight", pad_inches=0.05)
        BASE.plt.close(fig)
    fig = BASE.plt.figure(figsize=(10, 6), facecolor="white")
    ax = fig.add_subplot(111, projection="3d", proj_type="ortho")
    ax.add_collection3d(Poly3DCollection(triangle, facecolors=colors, edgecolors="none"))
    ax.set(xlim=(-2, 45), ylim=(-13, 13), zlim=(-8, 8))
    ax.set_box_aspect((47, 26, 16))
    ax.view_init(elev=24, azim=-120)
    ax.axis("off")
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    fig.savefig(ROOT / "figures/oblique.png", dpi=180, bbox_inches="tight", pad_inches=0.02)
    BASE.plt.close(fig)


def render_grip_section(row):
    """Overlay dimensionless U-pocket symbols on the unmodified CAD section."""
    mesh = trimesh.Trimesh(vertices=row["vertices"], faces=row["faces"], process=False)
    lines = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, -0.042]) * 1000
    fig, ax = BASE.plt.subplots(figsize=(9, 4.5), facecolor="white")
    for sign in (-1, 1):
        # Drawing-only stock outside the two hollow wire-entry extensions.
        x = 8.375 if sign == 1 else -11.6
        rect(ax, x, -5.4, 3.225, 10.8, DARK)
        for y in (-5.4, 3.325):
            rect(ax, 5.6 if sign == 1 else -8.375, y, 2.775, 2.075, DARK)
        rect(ax, 8.375 if sign == 1 else -9.375, -3.325, 1, 6.65, TEAL)
        for y in (-4.325, 3.325):
            rect(ax, 5.6 if sign == 1 else -8.375, y, 2.775, 1, TEAL)
        arrow(ax, (sign * 15, 0), (sign * 12.2, 0), BLUE)
    ax.add_collection(LineCollection(lines[:, :, :2], colors=ORANGE, linewidths=1.6, zorder=5))
    ax.set(xlim=(-17, 17), ylim=(-9, 9))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    fig.savefig(ROOT / "figures/section_grip.png", dpi=180, bbox_inches="tight", pad_inches=0.02)
    BASE.plt.close(fig)


def page(number, title, subtitle):
    fig = BASE.plt.figure(figsize=(16.54, 11.69), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, 1600), ylim=(1100, 0))
    ax.axis("off")
    text(ax, 50, 51, title, 24, bold=True)
    text(ax, 50, 100, subtitle, 11.5, MUTED)
    text(ax, 1550, 48, f"INNER GRIP  {number:02d}", 10, MUTED, align="right")
    box(ax, 50, 128, 1500, 44, PALE, "#d1dfe6", radius=4)
    text(ax, 68, 150, "H05の専用2本指を比較。後端の外形を保持し、電線の穴・嵌合部・キーを押さえない構成。", 11, BLUE)
    ax.plot([50, 1550], [1025, 1025], color="#cbd8df", lw=1)
    text(
        ax,
        50,
        1053,
        "部品形状は保存CAD。指・矢印は比較模式図。把持力・変形・通過・実機成立の判定は含みません。",
        9.5,
        MUTED,
    )
    text(ax, 1550, 1080, "2026-09-21 / D45・D50 / 5腕・20仕事を維持", 9, MUTED, align="right")
    return fig, ax


def image_panel(fig, name, x, y, width, height):
    axis = fig.add_axes((x / 1600, 1 - (y + height) / 1100, width / 1600, height / 1100))
    with Image.open(ROOT / f"figures/{name}.png") as source:
        axis.imshow(source)
    axis.axis("off")


def geometry_page():
    fig, ax = page(
        1,
        "内側ハウジングは、後端を囲ってつばを押す案",
        "TE 2103245-1（KEY A）を表示。部品の接続形状を変えず、交換指先の接触候補を分ける。",
    )
    box(ax, 50, 200, 760, 445, "white", "#d1dfe6")
    text(ax, 72, 231, "後端の口元断面と2本指の配置（比較）", 16, BLUE, True)
    image_panel(fig, "section_grip", 65, 269, 730, 287)
    text(ax, 74, 568, "橙：CAD断面　緑：接触候補　黒：指の支持部", 10.8, MUTED)
    text(ax, 74, 606, "穴を開けたまま外形を囲う。指厚・すき間・角の逃げは未寸法化。", 10.8)
    box(ax, 840, 200, 710, 445, "white", "#d1dfe6")
    text(ax, 862, 231, "上から見た形状", 16, BLUE, True)
    image_panel(fig, "top", 856, 283, 678, 280)
    text(ax, 899, 583, "電線側", 11.5, TEAL, True)
    text(ax, 1492, 583, "挿入側", 11.5, BLUE, True, "right")
    arrow(ax, (1070, 585), (1365, 585), BLUE)
    text(ax, 862, 618, "CAD全長42.6 mm。図面の参考長さ32.40 mmとは範囲が異なります。", 10, MUTED)

    rows = [
        (
            50,
            "① 後端の樹脂外周",
            TEAL,
            "対向する指に専用のくぼみを設ける。\n複数面で向きを支え、電線の出口は開ける。\n口元の壁は薄く、押付荷重は別途必要。",
        ),
        (
            560,
            "② つばの後面",
            ORANGE,
            "指先の段付き面を当てる比較。\n挿入力はこの面へ伝え、電線を押さない。\nつばの許容荷重は今回の資料では未確認。",
        ),
        (
            1070,
            "③ 長い差込み部・キー",
            BLUE,
            "外側ヘッダーへ入る部分。\nここへ指を回す案は避けて比較する。\n4種類のキーを同じ向きと見なさない。",
        ),
    ]
    for x, title, color, body in rows:
        box(ax, x, 674, 480, 205, PALE, "#d1dfe6")
        text(ax, x + 20, 709, title, 16, color, True)
        text(ax, x + 20, 750, body, 11.4, va="top")
    box(ax, 50, 904, 1500, 86, CREAM, GOLD)
    text(ax, 70, 928, "部品の対応", 12, GOLD, True)
    text(
        ax,
        70,
        961,
        "P16：I01=A / I02=D / I03=E　　P17：I04=D / I05=F。後端保持の候補は共通化を比較し、キー識別は残す。",
        11.4,
    )
    text(
        ax,
        50,
        1006,
        "出典：TE 2103245 Rev A1、保存2103245-1/-4/-5/-6 CAD、408-32095 Rev B。URL・SHAは同梱JSON。",
        9.7,
        MUTED,
    )
    return fig


def schematic(ax, x, y, scale=1.0, opened=False):
    """Draw a dimensionless top-view rear pocket with an axial shoulder."""

    def r(px, py, w, h, color, edge=None):
        rect(ax, x + px * scale, y + py * scale, w * scale, h * scale, color, edge)

    # Rear on the left, nose on the right. Twin wire exits remain open.
    for offset in (-22, 22):
        ax.plot([x - 40 * scale, x + 45 * scale], [y + offset * scale] * 2, color=ORANGE, lw=3)
        r(45, offset - 13, 94, 26, "#82bcb2", TEAL)
    r(139, -49, 14, 98, ORANGE)
    r(153, -35, 212, 70, METAL, DARK)
    shift = 31 if opened else 0
    for side in (-1, 1):
        center = side * (46 + shift)
        r(56, center - 10, 75, 20, DARK)
        contact_y = center + (5 if side == -1 else -11)
        r(61, contact_y, 65, 6, TEAL)
        # Shoulder is behind the flange; no forward hook across the mating side.
        r(130, center - 10, 9, 20, TEAL)
    return (x + 100 * scale, y - (46 + shift) * scale), (x + 100 * scale, y + (46 + shift) * scale)


def operation_page():
    fig, ax = page(
        2,
        "開口を通す動きと、ヘッダーへ差し込む動きを分ける",
        "候補の指先は後端側に置く。通過中の包絡、保持の引継ぎ、開放後の退避を別々に照合する。",
    )
    box(ax, 50, 200, 735, 446, "white", "#d1dfe6")
    text(ax, 74, 233, "D45 / 筐体壁の開口を通す", 17, BLUE, True)
    text(ax, 74, 272, "先端を先行させ、後端の形状保持を続ける比較。", 11.6)
    schematic(ax, 143, 410, 1.05)
    rect(ax, 577, 312, 15, 45, DARK)
    rect(ax, 577, 465, 15, 69, DARK)
    arrow(ax, (603, 412), (713, 412), BLUE)
    text(ax, 586, 559, "筐体壁（開口は模式表示）", 10.5, MUTED, align="center")
    text(
        ax,
        74,
        589,
        "指を含む後端も壁の近くまで来る。\n部品単体の余白0.2 / 0.3 mmから、指の通過可否は言えない。",
        11.2,
        GOLD,
        va="top",
    )

    box(ax, 815, 200, 735, 446, "white", "#d1dfe6")
    text(ax, 839, 233, "D50 / 外側ヘッダーへ挿入", 17, BLUE, True)
    text(ax, 839, 272, "C補助：内側を保持　／　C主腕：外側を保持する比較。", 11.6)
    box(ax, 1290, 333, 209, 156, "#fff2e3", ORANGE, radius=4)
    text(ax, 1395, 515, "外側ヘッダー", 11, ORANGE, True, "center")
    schematic(ax, 900, 410, 0.96)
    arrow(ax, (1243, 410), (1355, 410), BLUE)
    text(
        ax,
        839,
        589,
        "キーを合わせ、つばの後面で押す。\nTEのクリック記載と、自動機の検出・開放条件は別に残す。",
        11.2,
        GOLD,
        va="top",
    )

    box(ax, 50, 675, 735, 311, PALE, "#d1dfe6")
    text(ax, 74, 707, "指の開放・退避の候補", 16, BLUE, True)
    top, bottom = schematic(ax, 168, 838, 0.85, opened=True)
    arrow(ax, (top[0], top[1] + 10), (top[0], top[1] - 34), TEAL)
    arrow(ax, (bottom[0], bottom[1] - 10), (bottom[0], bottom[1] + 34), TEAL)
    arrow(ax, (143, 838), (80, 838), BLUE)
    text(ax, 587, 784, "① 左右へ開く\n② 電線側へ戻す", 13, BLUE, True, va="top")
    text(ax, 74, 953, "部品の支持先へ引き継げた後。周囲の線・壁・隣口を含む退避は未検証。", 10.5, MUTED)

    box(ax, 815, 675, 735, 311, CREAM, GOLD)
    text(ax, 839, 707, "次に寸法化する範囲", 16, GOLD, True)
    text(
        ax,
        839,
        752,
        "・後端のくぼみと段付き受け面を交換指先として具体化\n"
        "・指＋部品＋実電線で、壁・外側ヘッダー・隣口を照合\n"
        "・現在案内している配線を誰へ引き継ぐかを対応づける\n"
        "・開放を指令する条件と、許容する把持・挿入力を残す",
        11.5,
        va="top",
    )
    text(ax, 839, 947, "新しい腕・上押さえ・保持治具の追加を意味しません。", 10.5, GOLD)
    text(
        ax,
        50,
        1006,
        "模式図の隙間・指厚は製作寸法ではありません。フランジ締結と内側ハウジングのロックの前後関係は未選定。",
        9.7,
        MUTED,
    )
    return fig


def record(records, pins):
    prior = json.loads(PRIOR.read_text())
    inputs = json.loads(INPUTS.read_text())
    assert prior["source_job_count_preserved"] == 20
    return {
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "scope": "Comparison-only rear contour pocket and axial shoulder; no selected manufacture or motion",
        "source_sha256": pins,
        "source_job_count_preserved": 20,
        "cards_unmodified": prior["cards_unmodified"],
        "headers_unmodified": prior["headers_unmodified"],
        "apertures_unmodified": inputs["apertures"],
        "housing_geometry": records,
        "coordinate_note": "Source Z=0 nose, negative Z towards wire-entry rear. Display (u,v,w)=(Z+0.0426,X,Y).",
        "drawn_candidate": {
            "finger_count": 2,
            "family": "H05 inner housing; not the external-header H05 contour",
            "positioning": "Contour pocket at outer surfaces of wire-entry rear extensions",
            "insertion_load_path": "Stepped finger face onto rear face of housing collar",
            "avoided_regions": ["wire bores", "long insertion body", "key and locking features"],
            "release_illustration": "Open transversely then withdraw towards wires after support handoff",
            "allowed_clamp_force_N": None,
            "allowed_insertion_force_N": None,
            "selected_finger_dimensions_m": None,
            "selected": False,
        },
        "visual_region_note": "Color masks are illustrative region annotations, not contact-patch extraction.",
        "grip_section_note": (
            "Source Z=-0.042 m section near the rear mouth. "
            "Finger overlays are dimensionless explanatory symbols, not a selected axial contact position or "
            "manufactured contours; corner relief and tolerances are not specified. "
            "The stored mesh has only external loops at Z=-0.040 m; this drawing does not assert full cavity fidelity."
        ),
        "section_method": (
            "Exact plane-triangle intersections of the stored triangulation; no vertex-band absence inference"
        ),
        "cad_dimensions_note": "Complete CAD AABB length 0.0426 m differs from drawing reference length 0.0324 m.",
        "diagnostic_note": (
            "Initial read-only vertex-band reduction hit an empty band. "
            "Replaced by plane-triangle sections; no input changes."
        ),
        "reuse": (
            "Reused saved official CAD, official Rev A1 drawing, Rev B instruction, "
            "hand-plan graphic style and D45/D50 records."
        ),
        "custom_reason": (
            "Existing H05 external-header fingers target a different part. "
            "Only a comparison diagram is authored for the inner housing."
        ),
        "official_sources_checked": [
            {
                "url": "https://www.te.com/en/product-2103245-1.html",
                "note": "Drawing Rev A1 and instruction Rev B listed",
            },
            {
                "url": "https://www.te.com/en/product-2103245-6.html",
                "note": "Without strain relief; no clamp-load specification on inspected page",
            },
        ],
        "unresolved": [
            "Allowed rear-shell and collar loading and deformation",
            "Full finger/part/wire envelope through case wall and outer header",
            "Grasp-specific clearance to adjacent bays and retained wiring",
            "C assistant availability after prior wire-guidance handoff",
            "Detection of completed inner latch and selected flange fastening order",
        ],
        "native_changed": False,
        "new_robot_motion": False,
        "new_video": False,
        "new_collision_measurement": False,
        "new_manufactured_finger_mesh": False,
        "physical_acceptance_verdict": None,
    }


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output_root",
        type=Path,
        default=ROOT,
        help="Fresh directory for regeneration; delivered output is protected.",
    )
    args = parser.parse_args()
    ROOT = args.output_root.resolve()
    assert not (ROOT / "audit/delivery.json").exists(), "Preserve delivered version."
    for directory in ("figures", "audit", "output/pdf", "output/pages"):
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    paths = [CAD, DRAWING, INSTRUCTION, INPUTS, PRIOR, PLAN, STYLE]
    pins = {str(path): sha(path) for path in paths}
    cad, records = source_data()
    render_meshes(cad["2103245-1"])
    render_grip_section(cad["2103245-1"])
    data = record(records, pins)
    output = ROOT / "output/pdf" / (NAME + ".pdf")
    checks = []
    with BASE.PdfPages(output) as pdf:
        pdf.infodict().update(Title=NAME, Subject="Official inner-housing geometry and comparison grip", Author="")
        for number, fig in enumerate((geometry_page(), operation_page()), 1):
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            overflow = []
            for axis in fig.axes:
                for label in axis.texts:
                    bb = label.get_window_extent(renderer)
                    if not fig.bbox.contains(bb.x0, bb.y0) or not fig.bbox.contains(bb.x1, bb.y1):
                        overflow.append(label.get_text())
            assert not overflow, overflow
            checks.append({"page": number, "page_text_overflow": overflow})
            pdf.savefig(fig)
            BASE.plt.close(fig)
    for path, expected in pins.items():
        assert sha(Path(path)) == expected, path
    (ROOT / "output/inner_grasp_review.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "audit/authoring.json").write_text(json.dumps(checks, indent=2) + "\n")
    print("PDF_CREATED", output)
    print("SOURCE_PINS_UNCHANGED", len(pins))
    print("INNER_GRASP_REVIEW_DONE")


if __name__ == "__main__":
    main()
