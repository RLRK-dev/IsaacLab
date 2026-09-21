# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Cross-reference public port labels and pins without inventing physical wiring."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
RUN = REPO / "eval_runs/ur15_jb_harness_revision_20260907"
PREVIOUS = ROOT.parent / "hvjb-inner-wire-exit-v01-20260921"
CATALOG = RUN / "data/hvjb_photo_correspondence_v03_p01.json"
INTERFACE = PREVIOUS / "output/public_interface.json"
AMPERE = Path("/home/rlrk/IsaacLab-op040") / RUN.relative_to(REPO)
DATASHEET = AMPERE / "references/op040_real_products_20260912/ampere_hvjb_5_400_v1_1.pdf"
PHOTO = ROOT / "references/ampere_closed_front.jpg"
OVERVIEW = ROOT / "references/ampere_product_photo_1.jpg"
OUTPUT = ROOT / "output"
NAME = "HVJB_5口の用途・極性と未追跡配線_v01_20260921"
PINS = {
    CATALOG: "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    INTERFACE: "ff5615bb515985ef07cc3c1f43b2cd58884e87b4461bf262d06d65c2f706f3fe",
    DATASHEET: "643648bcea77b4d7c37c65d073664f746f68689952da2d5ce932e3d10bd5a9e1",
    PHOTO: "29f551a4b836bbfddb8833cca0f4dcacf64e43e2bd4aab86910fdc28955bcd82",
    OVERVIEW: "5724681b4bef4399f0799751a62577e48ef9b7fd3d6ed5b56d85fd95924937ad",
}
FUNCTIONS = ("Heater 1", "AC", "Heater 2", "Charger", "DC-DC")
FUSES_A = (20, 30, 20, 30, 10)
KEYS = ("A", "D", "E", "D", "F")
PHOTO_CENTERS_X = (355, 431, 507, 650, 725)
FONT = "HeiseiKakuGo-W5"
W, H = 1600, 1100
INK, BLUE, MUTED = "#183749", "#256a90", "#536b78"
PLUS, MINUS, HVIL = "#aa4e17", "#256a90", "#855693"
TEXT_RECORDS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def collect():
    for path, expected in PINS.items():
        assert sha(path) == expected, path
    old = json.loads(INTERFACE.read_text())
    for source in old["sources"]:
        assert sha(REPO / source["path"]) == source["sha256"]
    catalog = json.loads(CATALOG.read_text())
    parts = {p["id"]: p for p in catalog["parts"]}
    groups = {g["id"]: g for g in catalog["electrical_groups"]}
    result = copy.deepcopy(old)
    result.update(
        {
            "recorded_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "status": "public_label_pin_cross_reference_not_complete_physical_netlist",
            "basis": [*old["basis"], "Ampere DSC02840 front labels and HVJB-5-400 V1.1 p.2-4"],
            "builder_sha256": sha(Path(__file__)),
            "previous_public_interface_sha256": sha(INTERFACE),
            "photo_catalog_sha256": sha(CATALOG),
            "confirmed_physical_wire_to_cavity_bindings": [],
            "physical_aux_fuses": copy.deepcopy(catalog["physical_aux_fuses"]),
            "preserved_catalog": {
                "photo_features": sum(
                    len(catalog[k]) for k in ("parts", "visible_wire_segments", "visible_fastener_features")
                ),
                "required_functions": copy.deepcopy(catalog["required_functions"]),
                "electrical_groups": copy.deepcopy(catalog["electrical_groups"]),
                "lv_pin_map": copy.deepcopy(catalog["lv_pin_map"]),
            },
            "new_source_records": [
                {
                    "id": "AMPERE_CLOSED_FRONT",
                    "url": "https://ampereev.com/wp-content/uploads/2022/05/DSC02840-1024x683.jpg",
                    "local_path": str(PHOTO.relative_to(ROOT)),
                    "sha256": sha(PHOTO),
                    "source_size_px": [1024, 683],
                    "observation": "Five front labels above the 3+2 bays, read left to right.",
                    "observed_labels": ["HEATER 1", "AC", "HEATER 2", "CHARGER", "DC/DC"],
                    "label_centers_px": [[x, 423] for x in PHOTO_CENTERS_X],
                    "pixels_modified": False,
                },
                {
                    "id": "AMPERE_V11",
                    "url": "https://help.ampereev.com/hc/en-us/article_attachments/31292430639639",
                    "local_path": str(DATASHEET),
                    "sha256": sha(DATASHEET),
                    "pages": {"branch_fuses": 2, "power_pin_polarity": 3, "LV_pins": 4},
                    "current_download_same_bytes_observed": True,
                },
            ],
            "limits": [
                "Model bay correspondence combines public exterior positions, header keying and the saved catalog.",
                "It is not proof of the exact individual unit, hidden wiring or an as-built manufacturing revision.",
                "Branch fuse rating is a circuit requirement, not a rating assigned to an observed physical fuse body.",
                "Cavity role does not identify the nearby visible WI segment, bolt, ring terminal or joint stack.",
                "HVIL cavities 3/4 retain unknown loop order and in/out assignments.",
                "No saved CAD, hand, motion, dimension, physical verdict or acceptance criterion is changed.",
            ],
        }
    )
    for index, bay in enumerate(result["bays"]):
        part = parts[bay["id"]]
        group_id = f"EC{index + 4:02d}"
        assert groups[group_id]["name_ja"] == f"補機：{FUNCTIONS[index]}"
        assert part["bay"] == index and part["part_number"] == bay["housing_part_number"]
        wire_ids = sorted(w["id"] for w in catalog["visible_wire_segments"] if w["id"].startswith(f"WI{index + 1}"))
        bay.update(
            {
                "position_left_to_right_in_public_front_view": index + 1,
                "header_model_id": "P16" if index < 3 else "P17",
                "header_part_number": parts["P16" if index < 3 else "P17"]["part_number"],
                "header_local_bay_number": index + 1 if index < 3 else index - 2,
                "key": KEYS[index],
                "published_function": FUNCTIONS[index],
                "logical_electrical_group_id": group_id,
                "published_branch_fuse_a": FUSES_A[index],
                "function_mapping_basis": "Inference matching public front labels to the saved 3+2 bay order.",
                "physical_fuse_photo_id": None,
                "physical_joint_ids": None,
                "visible_entry_segment_ids": wire_ids,
                "visible_entry_is_pin_assignment": False,
                "physical_wire_pair_complete": False,
            }
        )
        for slot in bay["required_interfaces"]:
            number = slot["cavity_number_in_drawing"]
            slot["documented_electrical_role"] = {1: "HV+", 2: "HV-", 3: "HVIL", 4: "HVIL"}[number]
            slot["position_in_published_mating_view"] = {1: "left", 2: "right"}.get(number)
            slot["documented_role_basis"] = "AMPERE_V11 p.3" if number in (1, 2) else "TE 408-32095 Figure 1/5"
            slot["HVIL_in_or_out"] = None
            assert slot["photo_wire_id"] is None and slot["electrical_node"] is None
    assert result["preserved_catalog"]["photo_features"] == 92
    assert len(result["preserved_catalog"]["electrical_groups"]) == 13
    assert len(result["preserved_catalog"]["required_functions"]) == 17
    assert len(result["preserved_catalog"]["lv_pin_map"]) == 12
    assert sum(len(b["required_interfaces"]) for b in result["bays"]) == 20
    assert result["bays"][2]["visible_entry_segment_ids"] == []
    assert sum(len(b["visible_entry_segment_ids"]) for b in result["bays"]) == 8
    assert result["physical_aux_fuses"]["port_assignment_complete"] is False
    return result


def label(c, x, y, text, size=18, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont(FONT, size)
    for index, line in enumerate(text.split("\n")):
        baseline = H - y - index * size * 1.45
        width = pdfmetrics.stringWidth(line, FONT, size)
        assert x >= 0 and x + width <= W - 30 and baseline > 20, line
        c.drawString(x, baseline, line)
        TEXT_RECORDS.append({"text": line, "x": x, "baseline": baseline, "width": width})


def box(c, x, y, w, h, fill="#f3f7fa", edge="#cedde4"):
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor(edge))
    c.setLineWidth(1)
    c.roundRect(x, H - y - h, w, h, 8, fill=1, stroke=1)


def line(c, x1, y1, x2, y2, color=BLUE, width=2, dashed=False):
    c.saveState()
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(width)
    if dashed:
        c.setDash(6, 4)
    c.line(x1, H - y1, x2, H - y2)
    c.restoreState()


def image(c, path, x, y, w):
    with Image.open(path) as source:
        height = w * source.height / source.width
    c.drawImage(str(path), x, H - y - height, w, height)
    return height


def header(c, page, title, subtitle):
    label(c, 55, 65, title, 30)
    label(c, 55, 105, subtitle, 17, MUTED)
    label(c, 1380, 58, f"PORT MAP  {page:02d}", 13, MUTED)
    line(c, 55, 1030, 1545, 1030, "#cedde4", 1)
    label(c, 55, 1055, "根拠：Ampere公式外観写真・HVJB-5-400 V1.1、TE 2103245 A1 / 408-32095 B、保存台帳。", 12, MUTED)
    label(
        c,
        55,
        1078,
        "公開資料と保存モデルの対応図。実物の全配線・製造BOM・組立成立を確定したものではありません。",
        12,
        MUTED,
    )
    label(c, 1385, 1078, "2026-09-21", 12, MUTED)


def page_one(c, data):
    header(
        c,
        1,
        "5つの補機口の用途を、モデルIDへ対応",
        "蓋の用途表示と3口＋2口の並びを照合。各ヒューズ実体への割当とは分けて記録する。",
    )
    box(c, 55, 140, 780, 625, "#ffffff")
    label(c, 78, 183, "公式の蓋付き写真：前面から見た並び", 22, BLUE)
    image(c, PHOTO, 73, 205, 744)
    scale = 744 / 1024
    for i, x in enumerate(PHOTO_CENTERS_X):
        px = 73 + x * scale
        line(c, px, 205 + 587 * scale, px, 677)
        label(c, px - 19, 703, f"I0{i + 1}", 17, BLUE)
    label(c, 79, 742, "I番号はモデル側のID。写真原本の画素は変更していません。", 16, MUTED)
    box(c, 860, 140, 685, 625, "#ffffff")
    label(c, 883, 183, "公開配置に基づく対応表", 22, BLUE)
    label(c, 883, 228, "ID / Key", 17, MUTED)
    label(c, 1054, 228, "用途表示", 17, MUTED)
    label(c, 1305, 228, "回路のヒューズ", 17, MUTED)
    for i, bay in enumerate(data["bays"]):
        y = 272 + i * 66
        label(c, 883, y, f"{bay['id']} / {bay['key']}", 22)
        label(c, 1054, y, bay["published_function"], 22)
        label(c, 1340, y, f"{bay['published_branch_fuse_a']} A", 22)
        line(c, 883, y + 22, 1520, y + 22, "#dce5e9", 1)
    label(c, 883, 617, "I01〜I03：P16 / 2103340-1（A・D・E）\nI04〜I05：P17 / 2103346-2（D・F）", 19)
    label(c, 883, 696, "用途：公式写真の表示から照合。\n電流値：V1.1 p.2の各回路から照合。", 17, MUTED)
    box(c, 55, 790, 1490, 215, "#fff8ed", "#ae721d")
    label(c, 78, 833, "ここまで対応できたもの／残っているもの", 23, "#976214")
    label(c, 78, 878, "対応済み：公開外観の各口 → I01〜I05 → 用途・回路上の電流値。", 22)
    label(c, 78, 923, "未対応：各口 → 写真のヒューズ実体 P05 / P06 / P19 / P20 / P21 → ねじ・端子・線の全経路。", 21)
    label(
        c,
        78,
        972,
        "同じ製品資料の外観位置による照合です。個体・内部製造版・隠れた配線の同一性を証明するものではありません。",
        16,
        MUTED,
    )
    c.showPage()


def pin_view(c, x, y, wire_side):
    title = "電線側から見る" if wire_side else "外側の嵌合面から見る"
    label(c, x, y, title, 22, BLUE)
    box(c, x, y + 24, 635, 240, "#ffffff", "#a9bdc8")
    positions = [(2, "HV-", MINUS), (1, "HV+", PLUS)] if wire_side else [(1, "HV+", PLUS), (2, "HV-", MINUS)]
    for dx, (pin, role, color) in zip((42, 385), positions, strict=True):
        box(c, x + dx, y + 70, 205, 141, "#f4f8fa", color)
        label(c, x + dx + 65, y + 124, f"{pin}番", 29, color)
        label(c, x + dx + 62, y + 180, role, 29, color)
    if wire_side:
        label(c, x + 280, y + 111, "3", 22, HVIL)
        label(c, x + 280, y + 150, "4", 22, HVIL)
        label(c, x + 265, y + 190, "HVIL", 17, HVIL)
    else:
        label(c, x + 273, y + 149, "HVIL", 17, HVIL)
    label(c, x + 17, y + 245, "位置関係の模式図。形状・寸法・製作公差を表しません。", 14, MUTED)


def page_two(c, data):
    header(
        c,
        2,
        "左右ではなく、端子番号で配線を対応する",
        "嵌合面の1番＝HV＋・2番＝HV−。電線側から見た左右と取り違えない。",
    )
    pin_view(c, 78, 165, False)
    pin_view(c, 867, 165, True)
    label(c, 751, 308, "1 ↔ 1\n2 ↔ 2", 21, BLUE)
    box(c, 55, 455, 1490, 80)
    label(c, 78, 486, "5口共通：電力10接点の極性を台帳へ追加。中央HVIL 10接点は必要欄を保持。", 21, BLUE)
    label(c, 78, 518, "3番／4番のHVIL In・Out割当と内部周回順は未確定。LV側の5番＝In、11番＝Outとは分ける。", 18, HVIL)
    box(c, 55, 555, 1490, 266, "#ffffff")
    label(c, 78, 596, "写真で見える入口付近の線と、実端子番号の対応", 22, BLUE)
    for x, title in ((78, "モデル口"), (360, "既存写真で追えた短い区間"), (970, "残る対応")):
        label(c, x, 636, title, 17, MUTED)
    for i, bay in enumerate(data["bays"]):
        y = 672 + i * 29
        label(c, 78, y, f"{bay['id']} / {bay['published_function']}", 18)
        label(c, 360, y, "・".join(bay["visible_entry_segment_ids"]) or "未確認（必要部品・接点は保持）", 18)
        label(c, 970, y, "各線 → 穴番号 → 接続先・締結点", 18, MUTED)
    box(c, 55, 840, 1490, 165, "#fff8ed", "#ae721d")
    label(c, 78, 882, "次の形状確認に渡す入力", 22, "#976214")
    label(
        c,
        78,
        925,
        "口ごとの用途・極性は今回の台帳を使う。実線の径・曲がり・束ね方・支持と、各締結点の対応は追加確認する。",
        19,
    )
    label(
        c,
        78,
        962,
        "各4 mm開放→上方50 mmは比較案のまま。今回の端子対応を、曲がった実配線との非干渉確認へ読み替えない。",
        18,
    )
    c.showPage()


def main():
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    data = collect()
    OUTPUT.mkdir(exist_ok=True)
    write_json(OUTPUT / "port_connection_map.json", data)
    pdf = OUTPUT / "pdf" / (NAME + ".pdf")
    pdf.parent.mkdir(exist_ok=True)
    document = canvas.Canvas(str(pdf), pagesize=(W, H), pageCompression=1)
    document.setTitle(NAME)
    document.setAuthor("HVJB engineering review")
    page_one(document, data)
    page_two(document, data)
    document.save()
    assert all(sha(p) == expected for p, expected in PINS.items())
    write_json(
        OUTPUT / "document_audit.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "script_sha256": sha(Path(__file__)),
            "pdf_sha256": sha(pdf),
            "pdf_path": str(pdf.relative_to(ROOT)),
            "data_sha256": sha(OUTPUT / "port_connection_map.json"),
            "pages": 2,
            "text_records_inside_page": len(TEXT_RECORDS),
            "source_files_unchanged": True,
            "catalog_features_preserved": 92,
            "contacts_retained": 20,
            "physical_wire_connections_resolved": False,
            "physical_verdict": None,
        },
    )
    print("PORT_CONNECTION_MAP_COMPLETE", pdf, sha(pdf), flush=True)


if __name__ == "__main__":
    main()
