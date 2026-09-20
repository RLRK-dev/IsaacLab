# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Draw the reviewed line's task and hand-change correspondence, with no dimensional design."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/hvjb-hand-plan-mpl")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data/hand_plan.json").read_text())
FONT = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BOLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
matplotlib.rcParams["pdf.fonttype"] = 3
matplotlib.rcParams["axes.unicode_minus"] = False
INK, MUTED, BLUE = "#18364a", "#5d727e", "#276f98"
TEAL, ORANGE, GOLD, RED = "#168b83", "#ea964d", "#976415", "#b04443"
PALE, CREAM, METAL, DARK = "#eef5f8", "#fff6e6", "#c9d4d9", "#495a65"
WIDTH, HEIGHT = 1600, 1100
PAGE_LOG = []


def text(ax, x, y, value, size=12, color=INK, bold=False, align="left", va="center"):
    """Add Japanese text using the existing review font."""
    return ax.text(
        x,
        y,
        value,
        fontsize=size,
        fontproperties=BOLD if bold else FONT,
        color=color,
        ha=align,
        va=va,
        linespacing=1.5,
        zorder=6,
    )


def box(ax, x, y, w, h, fill=PALE, color=BLUE, dashed=False, radius=9):
    """Draw a schematic panel."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            fc=fill,
            ec=color,
            lw=1.4,
            linestyle="--" if dashed else "-",
            zorder=1,
        )
    )


def rect(ax, x, y, w, h, color=METAL, edge=None):
    """Draw dimensionless material or a marker."""
    ax.add_patch(Rectangle((x, y), w, h, fc=color, ec=edge or color, lw=1.4, zorder=3))


def arrow(ax, start, end, color=BLUE, dashed=False, both=False):
    """Draw process direction, without implying a trajectory."""
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="<->" if both else "-|>",
            mutation_scale=16,
            lw=1.9,
            color=color,
            linestyle="--" if dashed else "-",
            zorder=4,
        )
    )


def sheet(number, title, subtitle):
    """Start an A3 landscape page."""
    fig = plt.figure(figsize=(16.54, 11.69), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, WIDTH), ylim=(HEIGHT, 0))
    ax.axis("off")
    text(ax, 50, 48, title, 24, bold=True)
    text(ax, 50, 94, subtitle, 12, MUTED)
    text(ax, 1550, 45, f"HAND / PROCESS  {number:02d}", 10, MUTED, align="right")
    rect(ax, 50, 123, 1500, 35, PALE)
    text(ax, 66, 140, "確認済み：5腕の役割・XYZ・1段往復・20枠共用　／　今回：手先と受渡しの対応案", 11, BLUE)
    ax.plot([50, 1550], [1005, 1005], color="#cbd8df", lw=1)
    text(
        ax,
        50,
        1030,
        "無寸法の工程図。矢印は工程順の説明で、実機軌道・所要時間・保持成立の判定ではありません。",
        10,
        MUTED,
    )
    text(
        ax,
        50,
        1062,
        "根拠：既存20仕事・S5_AB・受渡し比較・H01-H08仕様。旧記録を保存し、最新の物流指示を上書き適用。",
        9,
        MUTED,
    )
    text(ax, 1550, 1080, "2026-09-20 / v01", 9, MUTED, align="right")
    return fig, ax


def save(pdf, fig, name):
    """Write a PDF page and its standalone image; record text containment."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    page = fig.bbox
    overflow = []
    for ax in fig.axes:
        for label in ax.texts:
            bounds = label.get_window_extent(renderer)
            if bounds.x0 < page.x0 or bounds.y0 < page.y0 or bounds.x1 > page.x1 or bounds.y1 > page.y1:
                overflow.append(label.get_text())
    assert not overflow, overflow
    pdf.savefig(fig)
    path = ROOT / f"output/png/{len(PAGE_LOG) + 1:02d}_{name}.png"
    fig.savefig(path, dpi=150)
    PAGE_LOG.append(
        {"page": len(PAGE_LOG) + 1, "name": name, "png": str(path.relative_to(ROOT)), "page_text_overflow": []}
    )
    plt.close(fig)


def label_box(ax, x, y, w, h, title, body, uncertain=False):
    """Draw a process box with explicit status."""
    box(ax, x, y, w, h, CREAM if uncertain else PALE, GOLD if uncertain else BLUE, uncertain)
    text(ax, x + 17, y + 29, title, 13, GOLD if uncertain else BLUE, True)
    text(ax, x + 17, y + 63, body, 11, va="top")


def grip(ax, x, y, width=85, height=44, opened=False, color=BLUE):
    """Draw a two-finger role symbol, not a manufactured hand."""
    gap = 17 if opened else 2
    rect(ax, x - width / 2 - gap - 9, y, 9, height, color)
    rect(ax, x + width / 2 + gap, y, 9, height, color)
    if not opened:
        rect(ax, x - width / 2 - 2, y + 9, 4, height - 18, TEAL)
        rect(ax, x + width / 2 - 2, y + 9, 4, height - 18, TEAL)


def body_and_support(ax, x, y, held=True, support=True, lifted=False):
    """Show independent body and fixture roles without assuming contact faces."""
    work_y = y - 35 if lifted else y
    rect(ax, x - 56, work_y, 112, 20, METAL, DARK)
    rect(ax, x - 25, work_y - 53, 55, 53, METAL, DARK)
    if support:
        rect(ax, x - 83, y + 31, 166, 15, DARK)
        for offset in (-43, 43):
            rect(ax, x + offset - 7, y + 21, 14, 10, TEAL)
    if held:
        if lifted:
            grip(ax, x, work_y - 3, 112, 26)
        else:
            grip(ax, x + 2.5, work_y - 57, 55, 49)


def overview(pdf):
    """Map every reviewed role to its target-dependent hand families."""
    fig, ax = sheet(
        1, "どの腕が、どの手先を使うか", "H番号は用途の系統。複数の手先を同時に装着する意味ではありません。"
    )
    rows = [
        ("OP010 XYZ", "供給・収納", ["H06 筐体", "空筐体を供給", "同じ段で完成品が戻る", "H06 同じ枠へ収納"]),
        ("A 主腕", "下板側", ["H01 / H02 本体", "H04 / H05 配線", "H06 下板搬送を比較", "Cへ支持を引継ぐ"]),
        ("B 主腕", "ヒューズ板側", ["H02 / H08 本体", "H04 / H05 配線", "H07 板搬送を比較", "Cへ支持を引継ぐ"]),
        ("共用補助", "A / B 用", ["H04 / H05 Aを補助", "引継ぎ → 開放・退避", "必要な交換・移動", "H04 / H05 Bを補助"]),
        ("C 主腕", "合流・組込み", ["H07 板保持 → H06搬送", "H05 内側 → 外側", "H03等 残接続", "H07 蓋を比較"]),
        (
            "C 専用補助",
            "保持・線案内",
            ["H04 / H05 対象に対応", "搭載中も保持・案内", "引出し・接続中も継続", "引継ぎ後にのみ開放"],
        ),
    ]
    x_positions = [267, 595, 923, 1251]
    for index, (role, sub, actions) in enumerate(rows):
        y = 192 + index * 99
        box(ax, 50, y, 190, 77, BLUE, BLUE)
        text(ax, 67, y + 25, role, 14, "white", True)
        text(ax, 67, y + 53, sub, 10, "white")
        for column, (x, action) in enumerate(zip(x_positions, actions, strict=True)):
            box(ax, x, y, 296, 77, CREAM if "比較" in action else PALE, GOLD if "比較" in action else BLUE)
            text(ax, x + 148, y + 38, action, 11.3, align="center")
            if column < 3:
                arrow(ax, (x + 297, y + 38), (x + 325, y + 38))
    box(ax, 50, 815, 740, 150)
    text(ax, 70, 845, "工具は独立して動く", 15, BLUE, True)
    text(
        ax,
        70,
        895,
        "A/B/Cの据置工具群が、部品を保持している間に締付け。\nボルト供給も工具側。該当する大小同時締結は2主軸を残す。",
        12,
    )
    box(ax, 815, 815, 735, 150, CREAM, GOLD, True)
    text(ax, 835, 845, "手先切替の機構は、まだ選定していない", 15, GOLD, True)
    text(
        ax,
        835,
        895,
        "輪郭の兼用・交換式爪・手先一式交換を今後比較。\nH06筐体用とH06ユニット用、H05内側と外側は互換未確認。",
        12,
    )
    save(pdf, fig, "役割と手先")


def ab_sequence(pdf):
    """Show two-hand jobs and supported primary-hand changes."""
    fig, ax = sheet(
        2,
        "A / B：保持を終えてから、手先と担当を切り替える",
        "AはD10-D12、BはD20-D22。共用補助のA優先・B優先は未選定です。",
    )
    for x, tag, main_hand in [
        (50, "A：下板側", "H01 / H02 → H04 / H05 → H06系"),
        (818, "B：ヒューズ板側", "H02 / H08 → H04 / H05 → H07系"),
    ]:
        box(ax, x, 190, 732, 105)
        text(ax, x + 20, 220, tag + "  主腕1つ", 16, BLUE, True)
        text(ax, x + 20, 262, main_hand, 14)
    text(ax, 50, 335, "両端を独立に持つ接続の例", 17, bold=True)
    sequence = [
        ("1  同時クランプ", "主腕＋共用補助で\nそれぞれの対象を保持"),
        ("2  保持中に締付け", "腕は保持を継続\n据置工具が締付け"),
        ("3  工具退避・引継ぎ", "残る自由端があれば\n案内先へ渡すまで保持"),
        ("4  同時上昇・退避", "解除できる両腕対象は\n同時に退避"),
    ]
    for index, (title, body) in enumerate(sequence):
        x = 50 + index * 385
        label_box(ax, x, 375, 345, 138, title, body)
        if index < 3:
            arrow(ax, (x + 345, 444), (x + 381, 444))
    box(ax, 50, 550, 1500, 115, CREAM, GOLD, True)
    text(ax, 70, 580, "補助腕の切替はこの後", 15, GOLD, True)
    text(
        ax, 70, 624, "Aの未接続端を持ったままBへ移らない。引継ぎ・開放・退避・必要な手先交換・移動も占有に含める。", 13
    )
    text(ax, 50, 712, "主腕の部品用 → 搬送用の切替", 17, bold=True)
    for index, (title, body) in enumerate(
        [
            ("部品用の保持を完了", "部品の締結と工具退避\n残る自由端は別担当で保持"),
            ("F-A / F-Bへ支持", "本体を支持に残す\n主腕が開放・退避"),
            ("搬送用の把持へ", "手先の切替を行う区間\n搬送把持後にユニットを運ぶ"),
        ]
    ):
        x = 50 + index * 515
        label_box(ax, x, 755, 470, 159, title, body, uncertain=index > 0)
        if index < 2:
            arrow(ax, (x + 472, 832), (x + 507, 832))
    text(ax, 50, 958, "支持面・実際の搬送爪・交換方式は未定。締付工具をフィンガでつかむ工程は追加しません。", 12, MUTED)
    save(pdf, fig, "A_Bの保持と切替")


def c_body(pdf):
    """Explain the supported C regrip already present in the adopted process."""
    fig, ax = sheet(
        3,
        "C：板を持つ手から、ユニットを運ぶ手へ",
        "D30 → D31 → D40。板間固定が荷重を受けられ、支持を渡せることを前提とする比較です。",
    )
    stages = [
        ("1  板合わせ・固定", "H07系で板を保持\n下板はF-Cで支持", True, False),
        ("2  工具を退避", "板保持を続ける\n締結直後に手を離さない", True, False),
        ("3  支持上で持ち替え", "F-Cが本体を支持\nH07系からH06系へ切替", False, False),
        ("4  一体搬送", "H06系で本体を把持\n自由端は別の担当が案内", True, True),
    ]
    for index, (title, body, held, lifted) in enumerate(stages):
        x = 50 + index * 385
        box(ax, x, 198, 345, 360)
        text(ax, x + 17, 230, title, 15, BLUE, True)
        body_and_support(ax, x + 172, 381, held=held, lifted=lifted)
        text(ax, x + 17, 495, body, 12)
        if index < 3:
            arrow(ax, (x + 348, 375), (x + 382, 375))
    box(ax, 50, 590, 1500, 94, "#eaf6f2", TEAL)
    text(ax, 70, 620, "C専用補助：本体の持ち替え中も、必要な自由端を案内・保持する", 15, TEAL, True)
    text(
        ax,
        70,
        655,
        "複数の独立した案内が残る場合は、A/B共用補助の付き添いを比較。1つの手で全端末を持てるとはしない。",
        11.5,
    )
    label_box(
        ax,
        50,
        730,
        700,
        174,
        "5  筐体へ降ろし、受けへ支持を渡す",
        "搬送指は受けへ荷重を渡してから開く。\n手が抜ける側方の空間も必要。\n下板の代わりに筐体底面を取り外す構成にはしない。",
    )
    label_box(
        ax,
        800,
        730,
        750,
        174,
        "今回まだ決めていないもの",
        "板の把持許容面、支持面、板間の実接合部、\nH07系・H06系の実際の爪、交換機構、\n自由端の個体と引継ぎ先。",
        uncertain=True,
    )
    text(
        ax,
        50,
        954,
        "図の台・指は既存の役割を示す記号で、形状や寸法の採用ではありません。支持中の持ち替えもC主腕を占有します。",
        11.5,
        MUTED,
    )
    save(pdf, fig, "Cの支持と持ち替え")


def c_ends(pdf):
    """Expose the occupied-hand conflict instead of hiding it in a transition."""
    fig, ax = sheet(
        4,
        "C：内側端末の保持を、途中で消さない",
        "D45 → D50 と D60。受ける相手が決まるまでは、両手が自由になった場面へ飛ばしません。",
    )
    text(ax, 50, 197, "内側端末 → 外側ヘッダー", 18, bold=True)
    label_box(
        ax,
        50,
        240,
        430,
        180,
        "D45  内側を開口から引き出す",
        "C主腕：H05内側で端末を保持\nC補助：必要な線を案内\n開口を通っただけでは放置しない。",
    )
    arrow(ax, (485, 330), (566, 330))
    label_box(
        ax,
        575,
        240,
        450,
        180,
        "支持の引継ぎが必要",
        "C主腕が内側端末を持ったまま、\n同じ手で外側ヘッダーは取れない。\n誰が内側を受けるかを解く。",
        uncertain=True,
    )
    arrow(ax, (1030, 330), (1111, 330), GOLD, dashed=True)
    label_box(
        ax,
        1120,
        240,
        430,
        180,
        "D50  外側ヘッダーを固定",
        "C主腕：H05外側でヘッダー保持\n別の担当：必要な内側保持\nT-C：ねじ締付け",
        uncertain=True,
    )
    box(ax, 50, 451, 1500, 135, CREAM, GOLD, True)
    text(ax, 70, 481, "既存2補助腕の中で比較する", 15, GOLD, True)
    text(
        ax,
        70,
        533,
        "C補助が内側端末を受けるなら、それまで案内していた線の支持を先に引き継ぐ。\nA/B共用補助が残る線を案内する案では、その間A/Bの新たな補助作業は待つ。到達・把持面・線数は未確定。",
        12,
    )
    text(ax, 50, 628, "D60：剛体部材と丸端子付き線を同時に保持する比較", 17, bold=True)
    label_box(ax, 50, 668, 450, 163, "C主腕  H03等", "バスバー等の剛体部材を保持\n穴・接続面・工具通路を空ける")
    label_box(ax, 550, 668, 450, 163, "C補助  H04", "線の黒被覆側を保持\n金属端子をつかまない")
    label_box(ax, 1050, 668, 500, 163, "据置工具 T-C", "必要な部材が保持された状態で締結\n該当する大小同時対象は2主軸")
    box(ax, 50, 862, 1500, 104, CREAM, GOLD, True)
    text(ax, 70, 891, "さらに別の自由端に案内が必要なら、共用補助の付き添いを比較する", 14, GOLD, True)
    text(
        ax,
        70,
        934,
        "既存の保持を解決してから次をつかむ。追加腕・上押さえ・青い保持機構を採用した図ではありません。",
        12,
    )
    save(pdf, fig, "Cの端末引継ぎ")


def stock(ax, x, y, state):
    """Draw the same twenty slots in each explanatory stock snapshot."""
    for row in range(5):
        for col in range(4):
            slot = row * 4 + col + 1
            fill = PALE
            if slot == 1:
                fill = {"empty_enclosure": PALE, "reserved_vacant": "white", "finished_product": "#bce1d1"}[state]
            box(
                ax,
                x + col * 57,
                y + row * 45,
                49,
                36,
                fill,
                TEAL if slot == 1 else BLUE,
                state == "reserved_vacant" and slot == 1,
                3,
            )
            text(ax, x + col * 57 + 24.5, y + row * 45 + 18, f"{slot:02}", 11, align="center")


def logistics(pdf):
    """Carry the latest single-deck and shared-stock decision into the diagram."""
    fig, ax = sheet(
        5,
        "供給と完成品収納を、同じXYZ・同じ20枠で行う",
        "D00 / D80 / D81を最新指示へ更新。20個＋20個ではなく、20枠を共用します。",
    )
    titles = ["1  供給前", "2  01番から取出し", "3  完成品が戻る", "4  01番へ収納"]
    counts = ["空筐体20", "空筐体19＋予約空き1", "空筐体19＋予約空き1", "空筐体19＋完成品1"]
    for index, snap in enumerate(DATA["logistics"]["illustrative_snapshots"]):
        x = 50 + index * 385
        box(ax, x, 202, 345, 367)
        text(ax, x + 20, 234, titles[index], 15, BLUE, True)
        stock(ax, x + 61, 270, snap["slots"][0]["state"])
        text(ax, x + 172, 527, counts[index], 12, align="center")
        if index < 3:
            arrow(ax, (x + 348, 382), (x + 382, 382))
    box(ax, 50, 600, 330, 187)
    text(ax, 70, 632, "供給側 XYZ ＋ H06", 16, BLUE, True)
    text(ax, 70, 684, "往路：空筐体を載せる\n復路：完成品を取り出す", 13)
    text(ax, 70, 751, "01番はその製品用に空けておく", 11)
    rect(ax, 425, 697, 1125, 25, DARK)
    for x in range(439, 1540, 24):
        ax.add_patch(Circle((x, 709), 8, fc=METAL, ec=MUTED, zorder=4))
    rect(ax, 725, 666, 110, 24, METAL, BLUE)
    rect(ax, 739, 616, 82, 48, PALE, BLUE)
    text(ax, 780, 640, "製品", 12, align="center")
    arrow(ax, (448, 653), (672, 653), BLUE)
    text(ax, 552, 619, "往路：筐体を載せてCへ", 12, BLUE, align="center")
    arrow(ax, (1160, 653), (893, 653), TEAL)
    text(ax, 1045, 619, "復路：完成品を載せて戻る", 12, TEAL, align="center")
    text(ax, 1360, 652, "C・後工程側", 14, BLUE, True, align="center")
    text(ax, 984, 762, "同じローラ面・同じ高さを往復。下段・端部昇降は使わない。", 13, align="center")
    label_box(ax, 50, 828, 715, 145, "収納後", "空パレットは供給側で次の筐体を待つ。\nXYZは供給と収納を順次担当する。")
    label_box(
        ax,
        805,
        828,
        745,
        145,
        "台数・スケジュールは別途",
        "図は1枚のパレットの説明例。全体の枚数・通行順は未定。\n空容器回収・フィーダ補給・必要な両手搬送も別計上。",
        True,
    )
    save(pdf, fig, "1段往復と20枠")


def workcard_table(pdf):
    """Display all twenty jobs, including unresolved equipment and work."""
    fig, ax = sheet(
        6,
        "20工程とフィンガの対応表",
        "※は対象ごとに必要な独立保持・条件付きの担当。空欄や不明を、工程の省略に変えません。",
    )
    xs = [50, 135, 392, 575, 891, 1190, 1550]
    headers = ["ID", "工程", "主担当", "主担当側の手先", "独立保持・工具", "保持を終える／渡す区切り"]
    rect(ax, 50, 193, 1500, 45, BLUE)
    for index, header in enumerate(headers):
        text(ax, xs[index] + 9, 215, header, 10.5, "white", True)
    keys = ["id", "title_ja", "primary_label_ja", "hands_label_ja", "assistance_label_ja", "transfer_ja"]
    for row_index, card in enumerate(DATA["cards"]):
        y = 238 + row_index * 35.5
        rect(ax, 50, y, 1500, 35.5, PALE if row_index % 2 == 0 else "white")
        for col_index, key in enumerate(keys):
            label = text(
                ax, xs[col_index] + 9, y + 17.75, card[key], 9.4, TEAL if card["id"] in {"D00", "D80", "D81"} else INK
            )
            label.set_gid(f"cell:{row_index}:{col_index}")
    for x in xs:
        ax.plot([x, x], [193, 948], color="#cbd8df", lw=0.8, zorder=2)
    text(
        ax,
        50,
        975,
        "青緑の行：最新の物流指示を反映。詳細な未確定項目と旧記録は、同梱CSV・JSONに残しています。",
        11,
        TEAL,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for label in ax.texts:
        if not (label.get_gid() or "").startswith("cell:"):
            continue
        _, row, col = label.get_gid().split(":")
        right = ax.transData.transform((xs[int(col) + 1] - 5, 0))[0]
        assert label.get_window_extent(renderer).x1 < right, (row, col, label.get_text())
    save(pdf, fig, "20工程対応表")


def main():
    """Render the six-page review package."""
    path = ROOT / "output/pdf/HVJB_工程別フィンガ・受渡し図_v01_20260920.pdf"
    with PdfPages(path, metadata={"Title": "HVJB 工程別フィンガ・受渡し図 v01", "Author": "RLRK"}) as pdf:
        for draw in (overview, ab_sequence, c_body, c_ends, logistics, workcard_table):
            draw(pdf)
    (ROOT / "audit/pages.json").write_text(json.dumps(PAGE_LOG, ensure_ascii=False, indent=2) + "\n")
    print(path)
    print(f"pages={len(PAGE_LOG)}")


if __name__ == "__main__":
    main()
