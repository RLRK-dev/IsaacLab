# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Document public tester evidence and preserve unresolved process interfaces."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
NAME = "HVJB_後工程の役割と未確定工程_v01_20260921"
PLAN = ROOT.parent / "hvjb-line-process-v03-20260921/output/line_process_plan.json"
LOCATION = ROOT.parent / "hvjb-assembly-location-v01-20260921/output/assembly_location.json"
VIDEO = ROOT.parent / "hvjb-line-video-v03-20260921/delivery_manifest.json"
DRAWING = ROOT.parent / "hvjb-line-process-v03-20260921/build_review.py"
ARTICLE = "https://ampereev.com/ampere-evs-hvjb-tester/"
PRODUCT = "https://help.ampereev.com/hc/en-us/articles/31292470232087-High-Voltage-Junction-Box-HVJB-5-400"

SPEC = importlib.util.spec_from_file_location("line_drawing", DRAWING)
assert SPEC is not None and SPEC.loader is not None
DRAW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRAW)

SOURCES = [
    {
        "id": "AMPERE_TESTER_2024",
        "url": ARTICLE,
        "title": "Ampere EV's High Voltage Junction Box Tester",
        "published_date": "2024-06-27",
        "accessed_date": "2026-09-21",
        "basis": "Official article body read with the web tool; no tester video observation.",
        "paraphrase_ja": "専用治具でリレー・接触器・抵抗等の電力と動作順序を確認。梱包前に行う複数検証の一つ。",
        "not_established_ja": "全検査項目、合否値、蓋との順序、自動接続機構、対象製造版との一致。",
    },
    {
        "id": "AMPERE_PRODUCT",
        "url": PRODUCT,
        "accessed_date": "2026-09-21",
        "basis": "Official product-page body read with the web tool.",
        "paraphrase_ja": "ダイカストアルミのIP67筐体、各コネクタのHVIL等を説明。",
        "not_established_ja": "IP67記載から量産時の気密試験方法・合否値を決めない。",
    },
]

OPEN_ROWS = [
    {
        "scene": "S02",
        "tasks": ["D01", "D81"],
        "known_ja": "端末準備と部品・ボルト供給の仕事は残る。",
        "unknown_ja": "加工済み入荷の範囲、補給単位・容器・供給点。",
        "next_ja": "加工する対象と購入する完成端末を分けて、供給状態を対応する。",
    },
    {
        "scene": "S09",
        "tasks": ["D42"],
        "known_ja": "既存観察に搭載後の筐体内工具作業がある。",
        "unknown_ja": "工具先端の対象、ねじの位置・数・積層。",
        "next_ja": "固定相手を特定する資料が必要。見えないねじを追加しない。",
    },
    {
        "scene": "S13",
        "tasks": ["D61"],
        "known_ja": "LV/HVILの機能と、残る端末の接続仕事を保持。",
        "unknown_ja": "各物理線の両端、極・端子、HVILの実配線順。",
        "next_ja": "接続群の数を線数・動作回数に変換せず、端末ごとに照合する。",
    },
    {
        "scene": "S14",
        "tasks": ["D70", "D71"],
        "known_ja": "今回：専用の機能検査治具に関する公式説明を確認。",
        "unknown_ja": "蓋・シールとの順序、対象口、条件・合否値・所要時間。",
        "next_ja": "試験接続の保持・解除を、既存内側ハウジング保持と分ける。",
    },
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def title(c, number, heading, subtitle):
    DRAW.text(c, 48, 62, heading, 34)
    DRAW.text(c, 48, 104, subtitle, 19, DRAW.GRAY)
    DRAW.line(c, 48, 126, 1552, 126, DRAW.BLUE, 2)
    DRAW.text(
        c, 48, 1064, "HVJB | 全体工程v03の補足 | 2026-09-21 | 機器・軌道・受入条件の確定ではありません", 16, DRAW.GRAY
    )
    DRAW.text(c, 1495, 1064, str(number) + " / 2", 16, DRAW.GRAY)


def step(c, x, heading, body, color, width=350):
    DRAW.box(c, x, 365, width, 155, fill=color)
    DRAW.text(c, x + 18, 400, heading, 22)
    DRAW.text(c, x + 18, 442, body, 17)


def page_one(c):
    title(
        c,
        1,
        "検査は設備へ分担し、ロボットの仕事を前後に分ける",
        "公開資料で確認できた部分と、このラインでの分担候補を区別します。",
    )
    DRAW.box(c, 48, 153, 1504, 150, fill="#e8f4ef")
    DRAW.text(c, 72, 189, "公式資料で確認できたこと", 23, DRAW.GREEN)
    DRAW.text(c, 72, 231, "Ampere EVは専用治具で、リレー・接触器・抵抗等の電力と動作順序を検査しています。", 22)
    DRAW.text(
        c,
        72,
        271,
        "梱包前の検査で、同社が行う複数検証の一つです。全検査の仕様や蓋との順序はこの記事だけでは決まりません。",
        19,
    )
    DRAW.text(c, 48, 341, "D71の作業分担候補（設備の支持が成立する場合）", 24, DRAW.BLUE)
    step(c, 48, "1  ワークを支持", "パレット／検査治具が支持\n支持を引き継いでから手を離す", "#edf5f8")
    step(c, 436, "2  試験コネクタ接続", "ロボットまたは専用接近軸\n保持・挿入・ロックを分担", "#edf5f8")
    step(c, 824, "3  設備で検査", "E-TESTが検査を担当\nロボットの兼務は条件付き", "#e8f4ef")
    step(c, 1212, "4  解除・退避", "試験接続を外す\nワーク支持は継続", "#edf5f8", 340)
    for x in (398, 786, 1174):
        DRAW.line(c, x + 3, 445, x + 29, 445, DRAW.BLUE, 3)
        DRAW.line(c, x + 21, 439, x + 29, 445, DRAW.BLUE, 3)
        DRAW.line(c, x + 21, 451, x + 29, 445, DRAW.BLUE, 3)
    DRAW.box(c, 48, 551, 732, 184, fill="#fff4df")
    DRAW.text(c, 70, 586, "ロボットを空き扱いにできる条件", 22, DRAW.GOLD)
    DRAW.text(
        c,
        70,
        628,
        "・本体・配線の支持を設備へ引き継げている\n・腕が支持や接続維持を担当する間は占有を残す\n・検査時間や次ワークとの重なりは未計測",
        20,
    )
    DRAW.box(c, 804, 551, 748, 184, fill="#fff4df")
    DRAW.text(c, 826, 586, "試験プラグの把持は別用途", 22, DRAW.GOLD)
    DRAW.text(
        c,
        826,
        628,
        "内側ハウジングH05／外側ヘッダーH05とは区別。\n試験プラグの持つ面、ラッチ解除、抜去方向を照合。\n指・腕・直交軸の新しい採用はまだ行いません。",
        20,
    )
    DRAW.text(c, 48, 779, "蓋・シール D70 と 機能検査 D71 は、前後を決めずに工程へ残す", 24)
    for x, heading in (
        (48, "D70：シール・蓋の配置と固定"),
        (574, "D71：試験接続・機能検査・解除"),
        (1100, "後工程完了後：同じ枠へ収納"),
    ):
        DRAW.box(c, x, 804, 452, 83)
        DRAW.text(c, x + 16, 840, heading, 20)
        if x < 1000:
            DRAW.text(c, x + 16, 870, "この2工程の相対順序は未確定", 16, DRAW.GRAY)
        else:
            DRAW.text(c, x + 16, 870, "1段往復パレット＋共用XYZを継承", 16, DRAW.GRAY)
    DRAW.text(c, 48, 928, "出典：Ampere EV “High Voltage Junction Box Tester” (2024-06-27)", 17, DRAW.GRAY)
    DRAW.text(c, 48, 958, ARTICLE, 17, DRAW.BLUE)
    c.linkURL(ARTICLE, (48, DRAW.H - 964, 850, DRAW.H - 936), relative=0)
    DRAW.text(
        c,
        48,
        996,
        "分担図は既存D71の具体化候補。実物テスタの自動接続機構やロボット台数を示す図ではありません。",
        18,
        DRAW.GRAY,
    )
    c.showPage()


def page_two(c):
    title(
        c,
        2,
        "未確定だった場面を、次に確認する対象へ分ける",
        "新しく埋まったのは検査治具の用途です。隠れた接続や締結点を補っていません。",
    )
    DRAW.text(c, 64, 172, "場面 / 仕事", 20, DRAW.BLUE)
    DRAW.text(c, 300, 172, "分かっていること / 残る不足 / 次の照合", 20, DRAW.BLUE)
    for i, row in enumerate(OPEN_ROWS):
        y = 194 + 152 * i
        DRAW.box(c, 48, y, 1504, 135, fill="#edf5f8" if i < 3 else "#e8f4ef")
        DRAW.text(c, 70, y + 40, row["scene"], 27)
        DRAW.text(c, 70, y + 80, " / ".join(row["tasks"]), 18)
        DRAW.text(c, 300, y + 32, row["known_ja"], 21, DRAW.GREEN)
        DRAW.text(c, 300, y + 72, "未確定：" + row["unknown_ja"], 19)
        DRAW.text(c, 300, y + 110, "次の照合：" + row["next_ja"], 19, DRAW.GRAY)
    DRAW.box(c, 48, 821, 1504, 106, fill="#fff4df")
    DRAW.text(c, 70, 854, "主ヒューズP22・被覆P08の取付工程は引き続き未確定", 23, DRAW.GOLD)
    DRAW.text(
        c,
        70,
        894,
        "補機ヒューズ板側の筐体外組立と一括しません。写真2022年・テスタ記事2024年・組立映像2025年の同一版も未確認です。",
        19,
    )
    DRAW.text(
        c,
        48,
        967,
        "継承：5腕の役割／20仕事／12元工程／20枠共用ストッカ／XYZ／1段往復パレット。新しい受入値は設定しません。",
        19,
    )
    DRAW.text(
        c,
        48,
        1007,
        "元の工程表・動画v03は保全。今回の資料は、未確定工程の具体化と担当検討のための補足です。",
        18,
        DRAW.GRAY,
    )
    c.showPage()


def main():
    assert not OUT.exists(), "Refusing to overwrite an existing review."
    original_paths = (PLAN, LOCATION, VIDEO, DRAWING)
    pins = {str(path): sha(path) for path in original_paths}
    plan = json.loads(PLAN.read_text())
    location = json.loads(LOCATION.read_text())
    video = json.loads(VIDEO.read_text())
    assert len(plan["cards"]) == 20 and len({row["operation"] for row in plan["cards"]}) == 12
    for row in OPEN_ROWS:
        scene = next(scene for scene in plan["scenes"] if scene["id"] == row["scene"])
        assert scene["tasks"] == row["tasks"]
    data = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_identity": pins,
        "sources": SOURCES,
        "existing_video_sha256": video["files"][0]["sha256"],
        "source_video_or_process_modified": False,
        "public_evidence_added": ["AMPERE_TESTER_2024"],
        "unresolved_scene_review": OPEN_ROWS,
        "preserved_open_interfaces": location["unresolved"],
        "preserved_selected_arm_roles": plan["selected_role_allocation"],
        "coverage": {"tasks": 20, "original_operations": 12, "video_scenes": 16},
        "D71_role_breakdown_proposal": [
            "workpiece_support",
            "test_connection",
            "equipment_test",
            "disconnect_and_retreat",
        ],
        "D70_D71_relative_order": None,
        "robot_release_condition_ja": "本体・配線・接続維持の必要な支持を設備へ引き継げる場合に限って兼務を比較。",
        "test_conditions_acceptance_values_and_durations": None,
        "specific_test_connector_or_end_effector": None,
        "new_equipment_selection": False,
        "new_motion_or_video_created": False,
        "formal_physical_validity_verdict": None,
    }
    (OUT / "pdf").mkdir(parents=True)
    (OUT / "pages").mkdir()
    pdfmetrics.registerFont(UnicodeCIDFont(DRAW.FONT))
    pdf = OUT / "pdf" / (NAME + ".pdf")
    c = canvas.Canvas(str(pdf), pagesize=(DRAW.W, DRAW.H))
    c.setTitle(NAME)
    page_one(c)
    page_two(c)
    c.save()
    payload = OUT / "after_process_review.json"
    payload.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    assert all(sha(path) == pins[str(path)] for path in original_paths)
    audit = {
        "builder_sha256": sha(Path(__file__)),
        "pdf_sha256": sha(pdf),
        "json_sha256": sha(payload),
        "sources_unchanged": True,
        "drawn_text": DRAW.DRAWN,
        "pages": 2,
        "source_pins": pins,
    }
    (OUT / "document_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print("AFTER_PROCESS_REVIEW_COMPLETE pages=2 tasks=20 operations=12 source_pins_unchanged=4")


if __name__ == "__main__":
    main()
