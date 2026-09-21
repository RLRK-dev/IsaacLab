# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Document conditional fuse assignments while retaining unresolved physical wires."""

from __future__ import annotations

import copy
import hashlib
import itertools
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
CATALOG = REPO / "eval_runs/ur15_jb_harness_revision_20260907/data/hvjb_photo_correspondence_v03_p01.json"
PREVIOUS = ROOT.parent / "hvjb-port-connection-map-v01-20260921/output/port_connection_map.json"
OUT = ROOT / "output"
NAME = "HVJB_ヒューズ対応候補と配線追跡_v01_20260921"
FUSES = ("P05", "P06", "P19", "P20", "P21")
PINS = {
    CATALOG: "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    PREVIOUS: "60049f203971fbb629d98daafcf738989787081dc4a9619d2fd366f9683d55a5",
}
W, H = 1600, 1100
FONT = "HeiseiKakuGo-W5"
INK, BLUE, MUTED, AMBER = "#183749", "#256a90", "#536b78", "#a45e14"
TEXT = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def collect():
    for path, expected in PINS.items():
        assert sha(path) == expected, path
    sources = json.loads((ROOT / "references/source_identity.json").read_text())
    for record in sources:
        assert sha(ROOT / record["file"]) == record["sha256"]
    catalog = json.loads(CATALOG.read_text())
    previous = json.loads(PREVIOUS.read_text())
    parts = {p["id"]: p for p in catalog["parts"]}
    ratings = {key: parts[key]["observed_current_a"] for key in FUSES}
    assert ratings == {"P05": None, "P06": 30, "P19": 20, "P20": 20, "P21": 10}
    ports = {b["id"]: b for b in previous["bays"]}
    candidates = []
    for permutation in itertools.permutations(ports):
        pairing = dict(zip(FUSES, permutation, strict=True))
        if all(ratings[f] is None or ratings[f] == ports[p]["published_branch_fuse_a"] for f, p in pairing.items()):
            candidates.append(pairing)
    # The enumeration follows a stated hypothesis, not a physical acceptance rule.
    assert len(candidates) == 4 and len({json.dumps(c, sort_keys=True) for c in candidates}) == 4
    allowed = {f: sorted({c[f] for c in candidates}) for f in FUSES}
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "builder_sha256": sha(Path(__file__)),
        "photo_catalog_sha256": sha(CATALOG),
        "previous_port_map_sha256": sha(PREVIOUS),
        "status": "conditional_correspondence_only_not_physical_netlist",
        "sources": sources,
        "conditional_analysis": {
            "hypotheses": [
                "These five photo fuse bodies implement exactly the five auxiliary branches in Ampere V1.1.",
                "There is one fuse per branch and the photographed installed ratings match the circuit ratings.",
                "Prior inferred public-label-to-model-bay correspondence applies to the target photo configuration.",
            ],
            "hypotheses_verified_for_exact_unit": False,
            "observed_fuse_ratings_a": ratings,
            "published_branch_ratings_a": {p: b["published_branch_fuse_a"] for p, b in ports.items()},
            "one_to_one_assignments": candidates,
            "allowed_ports_by_fuse_under_hypotheses": allowed,
            "implied_unread_fuse_rating_a_under_hypotheses": {"P05": 30},
            "implied_rating_is_observed_marking": False,
            "actual_connections_confirmed": [],
        },
        "preserved_port_map": copy.deepcopy(previous),
        "preserved_visible_wire_segments": copy.deepcopy(catalog["visible_wire_segments"]),
        "preserved_candidate_continuations": copy.deepcopy(catalog["candidate_continuations"]),
        "source_video_frame_observations": [
            {"second": 62, "observation": "Bench wiring present; hands obscure panel-side endpoints."},
            {"second": 70, "observation": "Inserted product photograph, not continuous bench wiring evidence."},
            {"second": 78, "observation": "Inserted closed-lid photograph; internal paths not visible."},
            {
                "second": 86,
                "observation": "Hands, body and crossings obscure individual endpoints; handwritten label not mapped.",
            },
        ],
        "new_confirmed_wire_to_fuse_bindings": [],
        "new_confirmed_wire_to_cavity_bindings": [],
        "limits": [
            "P21 to I05 is a conditional rating-compatible singleton, not an observed wire connection.",
            "P05 stays unread; its implied 30 A is not written into the photo observations.",
            "Neither color, proximity, an edited shot nor circuit-node equivalence identifies a physical wire.",
            "2025 bench entities and handwritten labels are not assigned to 2022 photo IDs.",
            "W04-WI52 and W05-WI42 remain candidates; the occluded portions are not drawn.",
            "I03 wiring remains unobserved while all required interfaces remain in the inventory.",
            "No source model, hand, control, motion, manufacturing parameter or acceptance criterion is changed.",
        ],
        "prior_art": {
            "keywords": ["HVJB", "ヒューズ", "配線対応", "接続図"],
            "exit_code": 0,
            "findings": 9,
            "blockers": 0,
        },
        "physical_verdict": None,
    }
    assert result["preserved_port_map"] == previous
    assert result["preserved_visible_wire_segments"] == catalog["visible_wire_segments"]
    assert len(result["preserved_visible_wire_segments"]) == 27
    assert previous["preserved_catalog"]["photo_features"] == 92
    assert sum(len(b["required_interfaces"]) for b in previous["bays"]) == 20
    for bay in result["preserved_port_map"]["bays"]:
        assert bay["physical_fuse_photo_id"] is None
        for slot in bay["required_interfaces"]:
            assert slot["photo_wire_id"] is None and slot["electrical_node"] is None
    return result


def text(c, x, y, value, size=18, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont(FONT, size)
    for index, row in enumerate(value.split("\n")):
        baseline = H - y - index * size * 1.45
        width = pdfmetrics.stringWidth(row, FONT, size)
        assert x >= 0 and x + width < W - 30 and 20 < baseline < H, row
        c.drawString(x, baseline, row)
        TEXT.append({"text": row, "x": x, "baseline": baseline, "width": width})


def box(c, x, y, width, height, fill="#f2f7fa"):
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor("#d7e2e8"))
    c.roundRect(x, H - y - height, width, height, 8, fill=1, stroke=1)


def line(c, x1, y1, x2, y2, color=BLUE, width=2):
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(width)
    c.line(x1, H - y1, x2, H - y2)


def picture(c, name, x, y, width):
    path = ROOT / "references" / name
    with Image.open(path) as im:
        height = width * im.height / im.width
    c.drawImage(str(path), x, H - y - height, width, height)
    return height


def header(c, number, title, subtitle):
    text(c, 55, 62, title, 30)
    text(c, 55, 102, subtitle, 17, MUTED)
    text(c, 1420, 55, f"TRACE {number:02d}", 13, MUTED)
    line(c, 55, 1030, 1545, 1030, "#d7e2e8", 1)
    text(
        c,
        55,
        1053,
        "資料：Ampere公式写真 DSC02861-1 / DSC02860-1、HVJB-5-400 V1.1、公式組立映像、保存台帳。",
        12,
        MUTED,
    )
    text(c, 55, 1078, "写真の補助観察と仮定付きの対応整理。実配線・製造仕様・把持や組立の成立は未確定。", 12, MUTED)
    text(c, 1400, 1078, "2026-09-21", 12, MUTED)


def page_one(c, data):
    header(
        c,
        1,
        "ヒューズと補機5口：対応候補は4通り",
        "5個の実体が公開回路の5系統へ一対一に対応し、定格が一致すると仮定した場合。実配線の確定ではありません。",
    )
    picture(c, "fuse_panel.jpg", 55, 138, 820)
    text(c, 55, 710, "左列：上 P05（定格未読） / 中 P19（20 A） / 下 P21（10 A）", 17)
    text(c, 55, 740, "右列：上 P06（30 A） / 下 P20（20 A）", 17)
    text(c, 55, 777, "印字の読取りは既存台帳を継承。帯色からP05の定格を補っていません。", 15, MUTED)
    c.linkURL("https://ampereev.com/wp-content/uploads/2022/05/DSC02861-1.jpg", (55, H - 685, 875, H - 138), relative=0)
    text(c, 930, 161, "定格と一対一対応から残る候補", 23)
    columns = (930, 1095, 1185, 1275, 1365, 1455)
    for x, label in zip(columns, ("写真上の実体", "I01", "I02", "I03", "I04", "I05"), strict=True):
        text(c, x + 6, 210, label, 17)
    for row, fuse in enumerate(FUSES):
        y = 226 + row * 60
        box(c, 930, y, 610, 54)
        text(c, 943, y + 34, fuse, 20)
        observed = data["conditional_analysis"]["observed_fuse_ratings_a"][fuse]
        text(c, 1007, y + 34, "未読" if observed is None else f"{observed} A", 17, MUTED)
        for idx in range(5):
            if f"I{idx + 1:02d}" in data["conditional_analysis"]["allowed_ports_by_fuse_under_hypotheses"][fuse]:
                text(c, columns[idx + 1] + 8, y + 34, "候補", 17, AMBER)
    text(c, 930, 565, "I01 Heater 1 / I02 AC / I03 Heater 2", 17)
    text(c, 930, 598, "I04 Charger / I05 DC-DC", 17)
    box(c, 930, 628, 610, 165, "#fff7e9")
    text(c, 948, 659, "P21→I05も、定格による条件付きの対応です。", 19, AMBER)
    text(c, 948, 699, "P05の30 Aは仮定からの帰結。印字確認ではありません。", 16)
    text(c, 948, 733, "20 A同士、30 A同士の入替えを写真だけでは解消できず、", 16)
    text(c, 948, 767, "ヒューズから各口までの接続線は未確定です。", 16)
    text(c, 55, 841, "4つの候補を全て保持（採用案なし）", 22)
    headings = ("候補", *FUSES)
    xs = (70, 300, 540, 780, 1020, 1260)
    for x, heading in zip(xs, headings, strict=True):
        text(c, x, 878, heading, 17, MUTED)
    for n, mapping in enumerate(data["conditional_analysis"]["one_to_one_assignments"]):
        y = 910 + n * 29
        for x, value in zip(xs, (f"{n + 1}", *(mapping[f] for f in FUSES)), strict=True):
            text(c, x, y, value, 17)
    c.showPage()


def page_two(c, data):
    header(
        c,
        2,
        "可視区間をつなぎ足さず、配線の未確定箇所を残す",
        "既存W04 / W05の可視区間を表示。線が隠れる先と、内側ハウジングの穴番号は未確定です。",
    )
    scale = 850 / 1620
    picture(c, "overview.jpg", 55, 139, 850)
    for identifier, color in (("W04", "#1d998d"), ("W05", "#286fd3")):
        segment = next(w for w in data["preserved_visible_wire_segments"] if w["id"] == identifier)
        points = [(55 + p[0] * scale, 139 + p[1] * scale) for p in segment["polyline_px"]]
        for a, b in itertools.pairwise(points):
            line(c, *a, *b, color, 3)
        end = points[-1]
        line(c, end[0] - 6, end[1] - 6, end[0] + 6, end[1] + 6, color, 3)
        line(c, end[0] - 6, end[1] + 6, end[0] + 6, end[1] - 6, color, 3)
    text(c, 55, 738, "緑 W04（L05側） / 青 W05（L04側） / ×は保存済み追跡の終了位置", 16)
    text(c, 55, 770, "原画像は無加工。注釈は別レイヤー、座標は画素位置であり設計寸法ではありません。", 14, MUTED)
    c.linkURL("https://ampereev.com/wp-content/uploads/2022/05/DSC02860-1.jpg", (55, H - 706, 905, H - 139), relative=0)
    box(c, 947, 139, 595, 293)
    text(c, 969, 175, "写真で残る二つの続き候補", 23)
    text(c, 969, 224, "W04  …  WI52（I05外装入口）", 20, "#1d998d")
    text(c, 969, 263, "W05  …  WI42（I04外装入口）", 20, "#286fd3")
    text(c, 969, 307, "重なる区間で同じ線と確定できないため、", 18)
    text(c, 969, 341, "つなぐ線・極番号・ヒューズIDは追加しません。", 18)
    text(c, 969, 390, "I03の見えない線も、必要接点20個も省略しません。", 16, MUTED)
    text(c, 950, 478, "今回追加した映像の読取り", 23)
    rows = (
        ("62秒", "板側の端点が手で隠れる。自由端も残る。"),
        ("70秒", "製品写真への切替。連続した配線追跡ではない。"),
        ("78秒", "蓋付き写真。内部経路は見えない。"),
        ("86秒", "手・身体・線の交差で個別端点が隠れる。"),
    )
    for idx, (when, observation) in enumerate(rows):
        y = 524 + idx * 46
        text(c, 953, y, when, 18, BLUE)
        text(c, 1030, y, observation, 16)
    text(c, 950, 735, "2025年の手書き番号を2022年写真のIDへ転用しません。", 16, AMBER)
    c.linkURL("https://www.youtube.com/watch?v=Sm_D-vmNYqc", (947, H - 752, 1542, H - 459), relative=0)
    box(c, 55, 815, 1490, 180)
    text(c, 76, 852, "残る情報：各口までの連続した経路、端子の極番号、共締めの積層、HVILの接続順序", 23)
    text(c, 76, 897, "定格で絞った候補を、把持位置・線長・組付け順の確定値には使いません。", 19)
    text(c, 76, 934, "写真92特徴・必須17機能・13回路群・LV12極を保持。今回の追加で確定した実接続はありません。", 18)
    text(
        c, 76, 971, "別添：62秒 / 86秒の無加工フレーム、候補4通りのJSON、出典・ハッシュ・未確定項目の記録。", 16, MUTED
    )
    c.showPage()


def main():
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    result = collect()
    data_path = OUT / "fuse_wire_trace.json"
    write_json(data_path, result)
    pdf_path = OUT / "pdf" / (NAME + ".pdf")
    pdf_path.parent.mkdir(exist_ok=True)
    document = canvas.Canvas(str(pdf_path), pagesize=(W, H), pageCompression=1)
    document.setTitle(NAME)
    page_one(document, result)
    page_two(document, result)
    document.save()
    for path, expected in PINS.items():
        assert sha(path) == expected
    for record in result["sources"]:
        assert sha(ROOT / record["file"]) == record["sha256"]
    write_json(
        OUT / "document_audit.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "script_sha256": sha(Path(__file__)),
            "data_sha256": sha(data_path),
            "pdf_path": str(pdf_path.relative_to(ROOT)),
            "pdf_sha256": sha(pdf_path),
            "pages": 2,
            "text_records_inside_page": len(TEXT),
            "conditional_assignments": 4,
            "new_confirmed_physical_connections": 0,
            "previous_port_map_preserved_exactly": True,
            "source_files_unchanged": True,
            "physical_verdict": None,
        },
    )
    print("FUSE_WIRE_TRACE_COMPLETE", pdf_path, sha(pdf_path), flush=True)


if __name__ == "__main__":
    main()
