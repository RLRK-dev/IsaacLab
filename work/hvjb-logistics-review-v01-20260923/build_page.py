# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Explain one reciprocal logistics cycle using existing saved-sample observations."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
VIDEO = ROOT.parent / "hvjb-line-video-v05b-20260923"
OUTPUT = ROOT / "output"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
INK, MUTED, TEAL, BLUE, GOLD = "#183B4D", "#526C78", "#168773", "#2C72AD", "#AD691C"
STATES = (
    ("開始", "01区画から筐体を取り出す", 0, "stock", 650, False),
    ("取出し", "同じXYZでパレットへ渡す", 72, "hand", 650, False),
    ("組立位置", "筐体を載せたまま工程へ", 1410, "pallet", 1020, False),
    ("復路", "同じ段で供給側へ戻る", 1560, "pallet", 1180, True),
    ("収納搬送", "同じXYZが完成品を受け取る", 1660, "hand", 650, True),
    ("収納完了", "空けていた01区画へ戻す", 1770, "stock", 650, True),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(draw, xy, value, size=26, color=INK):
    font = ImageFont.truetype(FONT, size)
    box = draw.textbbox(xy, value, font=font)
    assert 0 <= box[0] <= box[2] <= 1600 and 0 <= box[1] <= box[3] <= 1000, (value, box)
    draw.text(xy, value, font=font, fill=color)


def arrow(draw, a, b, color=TEAL, width=7):
    draw.line((*a, *b), fill=color, width=width)
    sign = 1 if b[0] > a[0] else -1
    draw.polygon([b, (b[0] - sign * 18, b[1] - 10), (b[0] - sign * 18, b[1] + 10)], fill=color)


def case(draw, center, complete, small=False):
    x, y = center
    w, h = (66, 42) if small else (126, 76)
    draw.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 6, fill=TEAL if complete else "#617B88")
    if not complete:
        draw.rectangle((x - w / 2 + 8, y - h / 2 + 8, x + w / 2 - 8, y + h / 2 - 8), fill="#DCE6EB")


def stock(draw, location, complete):
    text(draw, (58, 220), "20区画の共用ストッカ", 31)
    for row in range(5):
        for col in range(4):
            number = row * 4 + col + 1
            x, y = 110 + col * 112, 322 + row * 74
            is_first = number == 1
            fill = "#FFF0D9" if is_first else "#E4ECF1"
            draw.rounded_rectangle(
                (x - 48, y - 31, x + 48, y + 31), 6, fill=fill, outline=GOLD if is_first else "#BACCD5", width=3
            )
            if not is_first or location == "stock":
                case(draw, (x, y + 7), complete and is_first, small=True)
            text(draw, (x - 41, y - 31), f"{number:02d}", 17, GOLD if is_first else MUTED)
    caption = "01：完成品を収納" if complete and location == "stock" else "01：作業する筐体"
    if location != "stock":
        caption = "01：完成品が戻るまで空ける"
    text(draw, (58, 710), caption, 28, GOLD)
    text(draw, (58, 755), "残り19個は、この動画では静止", 24, MUTED)


def diagram(index, state):
    short, title, sample, location, pallet_x, complete = state
    image = Image.new("RGB", (1600, 1000), "#F2F6F8")
    draw = ImageDraw.Draw(image)
    text(draw, (46, 27), "同じXYZで供給と収納 ／ 1段のパレット往復", 39)
    text(draw, (46, 85), f"{index + 1} / 6　{title}", 32, TEAL)
    for offset, item in enumerate(STATES):
        x = 46 + offset * 255
        draw.rounded_rectangle((x, 145, x + 239, 194), 7, fill=TEAL if index == offset else "#E3ECF1")
        text(draw, (x + 13, 154), f"{offset + 1} {item[0]}", 23, "white" if index == offset else MUTED)
    stock(draw, location, complete)
    draw.rounded_rectangle((584, 276, 850, 367), 8, fill="#E7F1FA", outline=BLUE, width=3)
    text(draw, (610, 287), "供給・収納 XYZ", 27, BLUE)
    text(draw, (610, 328), "同じ1台を使用", 23, BLUE)
    text(draw, (925, 276), "C：合流・搭載", 28, TEAL)
    text(draw, (925, 319), "残接続へ", 25, MUTED)
    text(draw, (1300, 276), "後工程", 28, GOLD)
    text(draw, (1250, 319), "蓋・検査の方式は未定", 23, GOLD)
    draw.line((595, 617, 1504, 617), fill="#8CA6B3", width=21)
    for x in range(607, 1500, 45):
        draw.ellipse((x - 13, 603, x + 13, 629), fill="#D4E0E7", outline="#8CA6B3", width=2)
    for x in (625, 850, 1090, 1320, 1480):
        draw.line((x, 630, x, 681), fill="#8CA6B3", width=8)
    draw.rounded_rectangle((pallet_x - 80, 579, pallet_x + 80, 603), 4, fill="#768F9C")
    text(draw, (pallet_x - 74, 684), "パレット", 23, MUTED)
    if location == "pallet":
        case(draw, (pallet_x, 538), complete)
    if location == "hand":
        case(draw, (712, 444), complete)
        draw.line((655, 384, 655, 461), fill=BLUE, width=10)
        draw.line((769, 384, 769, 461), fill=BLUE, width=10)
    arrow(draw, (715, 737), (1460, 737), TEAL)
    text(draw, (978, 748), "往路", 24, TEAL)
    arrow(draw, (1460, 807), (715, 807), GOLD)
    text(draw, (978, 817), "復路：同じ段・同じ経路", 24, GOLD)
    text(draw, (605, 876), "パレットは工程上で持ち上げない", 27)
    text(
        draw, (46, 938), "1個の流れの図解。設備の寸法・支持面・20個連続処理の順序を定める図ではありません。", 24, MUTED
    )
    return image


def panel(index, row):
    hidden = "" if index == 0 else " hidden"
    return (
        f'<section data-step="{index}"{hidden}><h2>{index + 1}. {html.escape(row["title_ja"])}</h2>'
        f'<a href="{row["diagram"]}"><img src="{row["diagram"]}" width="1600" height="1000" alt="物流の流れ"></a>'
        f"<details><summary>動画の対応場面を見る：{row['video_s']:.2f}秒</summary>"
        f'<img src="{row["frame"]}" width="1920" height="1080" alt="対応する工程PNG">'
        "<p>模式動作と完成品参照の画面。実機成立を確認した画像ではありません。</p></details></section>"
    )


def page(rows, all_states=False):
    buttons = (
        ""
        if all_states
        else '<nav aria-label="物流の段階">'
        + "".join(
            f'<button type="button" data-pick="{index}" aria-pressed="{str(index == 0).lower()}">'
            f"{index + 1} {html.escape(row['short_ja'])}</button>"
            for index, row in enumerate(rows)
        )
        + "</nav>"
    )
    panels = "".join(panel(index, row) for index, row in enumerate(rows))
    if all_states:
        panels = panels.replace(" hidden", "")
    return (
        '<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<title>20共用区画と1段往復 | HVJB</title><link rel="stylesheet" href="logistics.css">'
        '<body><header><a href="../index.html">全体レビューへ</a><h1>20共用区画と1段往復</h1>'
        "<p>筐体を取り出した01区画を空けておき、同じXYZで完成品を戻します。</p>"
        '<p><a href="all_states.html">6段階を続けて見る</a> ／ '
        '<a href="index.html">段階を切り替える</a></p></header><main>'
        + buttons
        + panels
        + "<section><h2>今回の動画で確認した範囲</h2>"
        "<p>保存された1785サンプルでは、1個の筐体が01区画から出て同じ区画へ戻っています。"
        "残り19個は静止し、パレットは一定の高さで往復しています。</p>"
        "<p>図解での支持の引継ぎは、詳細な受け面や把持力の検証を表しません。"
        "20個を繰り返し処理する制御、パレット枚数と通行順序は未確定です。</p>"
        "<p>v05bでは旧構成の別置き搬出XYZ・専用台・試験プローブの表示を除きました。"
        "蓋は完成品を表す復路以降だけに表示し、蓋締結・検査の工程枠は残しています。</p>"
        '<p><a href="observations.json">保存座標の観測記録</a> ／ '
        '<a href="../hand_review/index.html#job-D00">筐体の受渡し・ハンド対応</a> ／ '
        '<a href="../parallel_review/index.html">3STと共用補助の役割</a></p></section>'
        '</main><script src="logistics.js"></script></body></html>\n'
    )


def main():
    assert not OUTPUT.exists()
    observations = ROOT / "audit/logistics_observations.json"
    data = json.loads(observations.read_text())
    assert data["stock"]["active_case_starts_at_slot_01"] and data["stock"]["active_case_ends_at_slot_01"]
    assert len(data["stock"]["slots"]) == 20 and data["stock"]["inactive_stock_case_count"] == 19
    preview = VIDEO / "previews/concept_v05b_preview02"
    manifest = json.loads((preview / "manifest.json").read_text())
    assert manifest["complete"] and manifest["saved_bank_identical_to_v05"]
    by_sample = {row["original_sample_index"]: row for row in manifest["images"]}
    (OUTPUT / "figures").mkdir(parents=True)
    rows = []
    for index, state in enumerate(STATES):
        short, title, sample, location, pallet_x, complete = state
        name = f"figures/step-{index + 1}.png"
        diagram(index, state).save(OUTPUT / name)
        source = preview / by_sample[sample]["file"]
        assert sha(source) == by_sample[sample]["sha256"]
        frame = f"figures/frame-{index + 1}.png"
        shutil.copy2(source, OUTPUT / frame)
        rows.append(
            {
                "short_ja": short,
                "title_ja": title,
                "source_sample": sample,
                "video_s": sample / 15,
                "diagram": name,
                "frame": frame,
                "case_location_symbol": location,
                "completed_symbol": complete,
            }
        )
    for file in ("logistics.js", "logistics.css"):
        shutil.copy2(ROOT / file, OUTPUT / file)
    shutil.copy2(observations, OUTPUT / "observations.json")
    (OUTPUT / "index.html").write_text(page(rows))
    (OUTPUT / "all_states.html").write_text(page(rows, all_states=True))
    (OUTPUT / "data.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    receipt = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_observations_sha256": sha(observations),
        "preview_manifest_sha256": sha(preview / "manifest.json"),
        "states": rows,
        "source_unchanged": True,
        "actual_browser_review": False,
        "physical_acceptance_verdict": None,
        "files": {str(path.relative_to(OUTPUT)): sha(path) for path in sorted(OUTPUT.rglob("*")) if path.is_file()},
        "script_sha256": sha(Path(__file__)),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(f"LOGISTICS_PAGE_COMPLETE states={len(rows)} files={len(receipt['files']) + 1}")


if __name__ == "__main__":
    main()
