# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw a two-page source-grounded exit comparison; dimensions are observations [m]."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import probe_exit as E
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "figures"
OUTPUT = E.OUTPUT
NAME = "内側ハウジングの4つの配線出口と指の退避_v01_20260921"
spec = importlib.util.spec_from_file_location("saved_installed_renderer", E.PREVIOUS / "build_review.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
B = R.B
R.R.FIGURES = FIGURES
FONT = "HeiseiKakuGo-W5"
W, H = 1600, 1100
INK, BLUE, TEAL, PURPLE = "#183749", "#256a90", "#117b83", "#8b5a98"
MUTED, ORANGE, RED = "#536b78", "#e8893d", "#b74338"
TEXT_RECORDS = []


def label(c, x, y, text, size=16, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont(FONT, size)
    for index, line in enumerate(text.split("\n")):
        baseline = H - y - index * size * 1.5
        width = pdfmetrics.stringWidth(line, FONT, size)
        assert x >= 0 and x + width <= W and 0 < baseline < H, line
        c.drawString(x, baseline, line)
        TEXT_RECORDS.append({"text": line, "x": x, "baseline": baseline, "width": width})


def box(c, x, y, w, h, color="#f3f7fa", edge="#cedde4"):
    c.setFillColor(HexColor(color))
    c.setStrokeColor(HexColor(edge))
    c.setLineWidth(1)
    c.roundRect(x, H - y - h, w, h, 8, stroke=1, fill=1)


def picture(c, name, x, y, w, h):
    c.drawImage(str(FIGURES / f"{name}.png"), x, H - y - h, w, h, preserveAspectRatio=True, anchor="c", mask="auto")


def source_detail(c, path, x, y, w, h):
    # Unchanged embedded photograph extracted from Figure 5, PDF object 70 0.
    c.drawImage(str(path), x, H - y - h, w, h, preserveAspectRatio=True, anchor="c")


def header(c, number, title, subtitle):
    label(c, 55, 65, title, 30)
    label(c, 55, 104, subtitle, 15, MUTED)
    label(c, 1350, 57, f"WIRE EXIT  {number:02d}", 14, MUTED)
    c.setStrokeColor(HexColor("#ccd9e1"))
    c.line(55, 80, 1545, 80)
    label(c, 55, 1048, "根拠：TE 2103245 Rev A1・408-32095 Rev B、保存CAD、前回のハンド比較。", 12, MUTED)
    label(
        c,
        55,
        1078,
        "補助的な幾何観測。実配線の再現、把持・荷重・ロック・ロボット動作の成立判定ではありません。",
        12,
        MUTED,
    )
    label(c, 1370, 1078, "2026-09-21", 12, MUTED)


def projection_figure(regions, parts, origin, name):
    fig, ax = B.plt.subplots(figsize=(8, 6), facecolor="white")
    for part in E.projected_parts(parts, origin):
        xy = part["outline"] * 1000
        color = TEAL if part["kind"] == "pad" else BLUE
        ax.fill(xy[:, 0], xy[:, 1], color=color, alpha=0.6, lw=0)
    for region in regions:
        loop = np.asarray(region["projection_polygon_m"]) * 1000
        color = PURPLE if region["id"].startswith("HVIL") else ORANGE
        ax.fill(loop[:, 0], loop[:, 1], facecolor=color, edgecolor=color, lw=1.5, alpha=0.55)
    ax.set(xlim=(-20, 20), ylim=(-10, 20))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    R.R.write_figure(fig, name)


def page_one(c, source_png):
    header(
        c, 1, "配線出口は、電力2口＋HVIL 2口", "中央の2口も指先の比較へ含める。写真の橙線だけを全配線として扱わない。"
    )
    box(c, 55, 135, 1490, 65)
    label(
        c,
        77,
        174,
        "5つの内側ハウジング：電力10接点＋HVIL 10接点。電線の全経路・本数が確定した意味ではありません。",
        18,
        BLUE,
    )
    box(c, 55, 225, 690, 475, "#ffffff")
    label(c, 78, 265, "TE公式組立説明書：電線側の面", 21, BLUE)
    source_detail(c, source_png, 85, 295, 630, 265)
    label(c, 90, 600, "左右の大口：電力接点用／中央の小口2つ：HVIL用", 17)
    label(c, 90, 632, "図面の口番号：左2・右1・中央上3・中央下4。", 17)
    label(c, 90, 669, "408-32095 p.3 Figure 5（PDF内の原画像を抽出）。", 13, MUTED)
    box(c, 775, 225, 770, 475, "#ffffff")
    label(c, 798, 265, "閉じた指と出口の投影範囲", 21, BLUE)
    picture(c, "closed", 805, 282, 710, 330)
    label(c, 805, 639, "青／緑：指・支持部　橙：電力2口　紫：中央2口の一括範囲", 16)
    label(c, 805, 671, "紫は電線形状や、2個の穴の個別寸法ではありません。", 15, MUTED)
    box(c, 55, 725, 720, 267)
    label(c, 77, 768, "公開資料で対応が取れるところ", 22, BLUE)
    label(
        c,
        77,
        811,
        "電力：MCP 2.8 接点 ×2。\nHVIL：MQS 接点 ×2。\n"
        "各接点を内側ハウジングへ挿入・保持確認した後、\n"
        "内側ハウジングを外側ヘッダーへ挿入する。",
        19,
    )
    box(c, 800, 725, 745, 267, "#fff8ed", "#ae721d")
    label(c, 822, 768, "まだ対応を決めないところ", 22, "#976214")
    label(
        c,
        822,
        811,
        "写真のWI線 → 穴番号・極性・行き先。\n"
        "採用接点・電線径、HVILの周回順、出口からの曲がり。\n"
        "メーカー手順の保持確認を、そのままロボットの\n"
        "判定信号や力のしきい値へ変換しない。",
        19,
    )
    c.showPage()


def page_two(c, observation):
    header(
        c,
        2,
        "4 mm開放案は、出口の軸方向領域も空ける",
        "出口の輪郭を軸方向へ延ばす仮想比較。曲がる電線の経路を新たに作ったものではない。",
    )
    box(c, 55, 135, 1490, 65)
    label(
        c,
        77,
        175,
        "手本体・支持部・指の全並進範囲を投影して照合。図は先端付近の拡大で、本体は表示範囲外です。",
        18,
        BLUE,
    )
    for x, image, title, caption, color in (
        (55, "lift2", "各2 mm開放 → 上へ50 mm", "電力2口の仮想領域と投影が重なる", RED),
        (815, "lift4", "各4 mm開放 → 上へ50 mm", "電力2口・中央2口の範囲とも重なり0", TEAL),
    ):
        box(c, x, 225, 730, 397, "#ffffff")
        label(c, x + 23, 265, title, 22, BLUE)
        picture(c, image, x + 23, 280, 684, 276)
        label(c, x + 23, 599, caption, 18, color)
    box(c, 55, 646, 1490, 142)
    label(c, 77, 686, "5口とも同じ観測", 22, BLUE)
    for x, title, value in (
        (440, "閉じた位置", "3領域とも重なり0"),
        (790, "0 → 各4 mm開放", "全中間位置で重なり0"),
        (1145, "各4 mm開放 → 上方50 mm", "全中間位置で重なり0"),
    ):
        label(c, x, 686, title, 17, BLUE)
        label(c, x, 730, value, 18)
    label(c, 77, 766, "3領域＝左右の電力2口＋中央HVIL 2口をまとめた1領域。中央2口を省略していません。", 16, MUTED)
    box(c, 55, 812, 1490, 180, "#fff8ed", "#ae721d")
    label(c, 77, 854, "残るのは「出口から先」の対応と形状", 22, "#976214")
    label(
        c,
        77,
        897,
        "実物の端末対応、被覆径、曲がり、束ね方を入れてから再確認する。現行のWI表示片はその代用にしない。\n"
        "I03の出口線、HVILの経路、隠れた接続を省略せず未確定欄に保持する。指の荷重・残留保持も未確認。\n"
        "今回の4 mm・50 mmは比較値。指の製作寸法、採用機種、アーム軌道、実機の非干渉は確定していない。",
        18,
    )
    c.showPage()
    assert len(observation["bays"]) == 5


def main():
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    observation = json.loads((OUTPUT / "exit_projection_observations.json").read_text())
    assert E.A.P.sha(ROOT / "probe_exit.py") == observation["script_sha256"]
    product, inners, settings, pge = E.read_inputs()
    aperture = settings["apertures"][0]
    parts, mapping = E.A.build_hand(inners[aperture["part_number"]], product[aperture["id"]], pge)
    origin = np.asarray(mapping["inner_origin_world_m"])
    regions = observation["bays"][0]["regions"]
    states = E.comparison_states(parts)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for image, state in (
        ("closed", "closed"),
        ("lift2", "lift_0_to_50_after_open_2"),
        ("lift4", "lift_0_to_50_after_open_4"),
    ):
        projection_figure(regions, states[state], origin, image)
    temp = ROOT / "tmp/pdfs"
    temp.mkdir(parents=True, exist_ok=True)
    extracted = temp / "instruction_3-002.png"
    subprocess.run(
        [
            "pdfimages",
            "-f",
            "3",
            "-l",
            "3",
            "-png",
            str(E.INSTRUCTION),
            str(temp / "instruction_3"),
        ],
        check=True,
    )
    assert E.A.P.sha(extracted) == "354413c3a8fdb7938b76ef9b68d6a246e92c7347cd591fafb9ba0bfffdbdaf7e"
    with Image.open(extracted) as image:
        assert image.size == (255, 146)
    source_png = FIGURES / "te_figure5_wire_end.png"
    shutil.copyfile(extracted, source_png)
    pdf = OUTPUT / "pdf" / (NAME + ".pdf")
    pdf.parent.mkdir(exist_ok=True)
    document = canvas.Canvas(str(pdf), pagesize=(W, H), pageCompression=1)
    document.setTitle(NAME)
    document.setAuthor("HVJB engineering review")
    page_one(document, source_png)
    page_two(document, observation)
    document.save()
    result = {
        "pdf": str(pdf.relative_to(ROOT)),
        "pdf_sha256": E.A.P.sha(pdf),
        "renderer_sha256": E.A.P.sha(Path(__file__)),
        "observations_sha256": E.A.P.sha(OUTPUT / "exit_projection_observations.json"),
        "text_records_inside_page": len(TEXT_RECORDS),
        "pages": 2,
        "source_pdf_sha256": E.A.P.sha(E.INSTRUCTION),
        "source_image": {"page": 3, "image_index": 2, "pdf_object": "70 0", "pixels": [255, 146]},
        "source_png_sha256": E.A.P.sha(source_png),
        "physical_verdict": None,
    }
    (OUTPUT / "document_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("WIRE_EXIT_PDF_COMPLETE", pdf, flush=True)


if __name__ == "__main__":
    main()
