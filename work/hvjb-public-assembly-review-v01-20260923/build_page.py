# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Attach pinned public stills to existing outside/inside assembly observations."""

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
WORK = ROOT.parent
REPO = ROOT.parents[1]
REFERENCE_ROOT = Path("/home/rlrk/IsaacLab-op040/eval_runs/ur15_jb_harness_revision_20260907")
CATALOG = REPO / "eval_runs/ur15_jb_harness_revision_20260907/data/hvjb_preassembly_process_v03.json"
LOCATION = WORK / "hvjb-assembly-location-v01-20260921/output/assembly_location.json"
PREVIOUS = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05b_20260923")
CATALOG_SHA = "5e9d7078d4e7ff9772f8561788b29a34b28165e3118559385dcc78faf28b64e7"
LOCATION_SHA = "f72dcbf515f4d4db5bef63dbd973ddf4eebeb974213297e3296b1748f127a3f6"
MOVIE = "HVJB_line_split_process_concept_v05b_review.mp4"
MOVIE_SHA = "65ed3f0f861370c55e3d09de5b6d5d17889aea14d1394de757aba7cf2360ba03"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FRAME_JOBS = {
    "plate_024": ("D10", "D11", "D20", "D21"),
    "plate_050": ("D20", "D21"),
    "plate_146": ("D40",),
    "plate_154": ("D40", "D45"),
    "plate_158": ("D42",),
    "plate_170": ("D45", "D50"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def escape(value):
    return html.escape(str(value), quote=True)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_data():
    assert sha(CATALOG) == CATALOG_SHA
    assert sha(LOCATION) == LOCATION_SHA
    catalog = json.loads(CATALOG.read_text())["source_video_evidence"]
    location = json.loads(LOCATION.read_text())
    source = location["source_video"]
    assert source == catalog["sources"]["assembly_20250607"]
    assert sha(REFERENCE_ROOT / source["file"]) == source["sha256"]
    frames = []
    for key, jobs in FRAME_JOBS.items():
        observed = next(row for row in location["source_video_observations"] if row["frame"] == key)
        recorded = catalog["frames"][key]
        path = REFERENCE_ROOT / recorded["file"]
        assert sha(path) == recorded["sha256"], path
        assert observed["source_url"] == recorded["url"]
        frames.append(
            {
                "id": key,
                "source_frame_unmodified": recorded,
                "observation_unmodified": observed,
                "related_jobs_unmodified": [row for row in location["task_locations"] if row["id"] in jobs],
                "display_image": f"figures/{key}.png",
                "display_size_px": [1200, 675],
                "display_transform": "Full-frame uniform LANCZOS resize, 1920x1080 to 1200x675; no crop or drawing",
                "markers_layer": "Separate SVG overlay from unchanged existing image coordinates; not grasp points",
            }
        )
    return {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_video_unmodified": source,
        "catalog_sha256": CATALOG_SHA,
        "location_sha256": LOCATION_SHA,
        "frames": frames,
        "all_jobs_unmodified": location["task_locations"],
        "new_work_assignment": False,
        "new_process_movie": False,
        "formal_physical_verdict": None,
    }


def marker_layer(observation):
    marks = []
    for marker in observation["markers"]:
        x, y = marker["xy_px"]
        assert 0 <= x < 1920 and 0 <= y < 1080
        marks.append(
            f'<g><circle cx="{x}" cy="{y}" r="23" fill="#fff0bc" stroke="#723e00" stroke-width="4"/>'
            f'<text x="{x}" y="{y + 1}" text-anchor="middle" dominant-baseline="middle"'
            f' fill="#663700" font-size="28" font-weight="700">{escape(marker["label"])}</text></g>'
        )
    return '<svg viewBox="0 0 1920 1080" aria-hidden="true">' + "".join(marks) + "</svg>"


def frame_card(frame):
    row = frame["observation_unmodified"]
    legend = "".join(f"<li><b>{escape(mark['label'])}</b> {escape(mark['text_ja'])}</li>" for mark in row["markers"])
    jobs = "".join(
        f'<a href="../hand_review/index.html#job-{job["id"]}">{job["id"]}：{escape(job["work_ja"])}</a>'
        for job in frame["related_jobs_unmodified"]
    )
    return (
        f'<article class="card" id="{frame["id"]}"><h2>{escape(row["time_ja"])}</h2>'
        f'<a class="frame" href="{frame["display_image"]}" aria-label="元画像の全画面縮小表示を開く">'
        f'<img src="{frame["display_image"]}" width="1200" height="675" loading="lazy"'
        f' alt="Ampere EV公開組立映像：{escape(row["time_ja"])}">{marker_layer(row)}</a>'
        f'<ul class="legend">{legend}</ul>'
        '<div class="columns"><section class="observation"><h3>画像・映像の既存観察</h3>'
        f'<p>{escape(row["observation_ja"])}</p></section><section class="limit"><h3>この場面で決まらないこと</h3>'
        f"<p>{escape(row['limit_ja'])}</p></section></div>"
        f'<p><a href="{escape(row["source_url"])}">公式映像のこの時刻を開く</a></p>'
        f'<div class="jobs">ライン案で照合する仕事（その全動作がこの画像に映る意味ではありません）<br>{jobs}</div>'
        "</article>"
    )


def document(data):
    links = "".join(
        f'<a href="#{row["id"]}">{escape(row["observation_unmodified"]["time_ja"])}</a>' for row in data["frames"]
    )
    body = (
        '<nav><a href="../index_v05b_1.html">← 全体レビュー</a>'
        '<a href="../unit_review/index.html">部品群の図</a><a href="figures/six_scenes.png">6場面の一覧画像</a></nav>'
        "<h1>公開組立映像で見る、筐体の外と内の作業</h1>"
        '<p class="intro">筐体外で下板側・補機ヒューズ板側を組み、まとめて搭載した後にも内部作業が残ります。'
        "下の6場面から、現在の工程表と部品群の図へ対応を追えます。</p>"
        '<div class="flow"><div><strong>外：下板側・補機ヒューズ板側</strong>'
        "<small>0:24 / 0:50 — 台上で別々に扱う</small>"
        "</div><div><strong>外 → 内：まとめて搭載</strong><small>2:26 — 板同士の実物固定具は見えない</small>"
        "</div><div><strong>搭載後：工具作業・端末引出し</strong>"
        "<small>2:34 / 2:38 / 2:50 — 未接続端が残る</small></div></div>"
        '<div class="note"><strong>「まとめて搭載」と「板同士の締結完了」は別です。</strong>'
        "<p>D30/D31の板合わせ・持ち替えは、現在採用している仮手順です。映像では固定作業・固定具が隠れており、"
        "その締結位置や支持方法までは定まりません。D42も工具対象を未特定のまま残しています。</p></div>"
        '<p class="minor">出典：Ampere EV「ASSEMBLY! EV High Voltage Junction Box」（2025-06-07）。'
        "完成写真のモデルと同一製造版であることは未確認です。3ST分担・ロボットの台数はライン案であり、"
        "この手作業映像がその構成を実証しているわけではありません。</p>"
        f'<div class="jump">{links}</div>'
        '<input id="markers" type="checkbox" checked> <label for="markers">既存記録の対象番号を表示</label>'
        '<p class="minor">画像を選ぶと番号のない縮小元画像が開きます。番号は把持点・加工位置ではありません。</p>'
        '<div class="cards">' + "".join(frame_card(frame) for frame in data["frames"]) + "</div>"
        "<details open><summary>補機ヒューズの外組みと、搭載後に残す仕事</summary>"
        "<p>現在のライン案では補機ヒューズ板側の締結をBの筐体外作業へ割り付けています。"
        "搭載後には、別の内部工具作業、側壁へ通す端末、残る電気接続を確保します。"
        "主ヒューズP22・被覆P08の取付工程は、補機ヒューズと一括して確定していません。</p>"
        "<p>映像に映らない工程を省略したり、工具が入る場面だけで全ねじの締結を確認済みにしたりはしません。"
        "線ごとの両端、隠れた積層・締付条件は、既存の未確定事項として残します。</p></details>"
        '<footer><p><a href="evidence_data.json">観察と元データの対応</a> ／ <a href="README.md">読み方</a></p>'
        '<p class="minor">2026-09-23作成。元画像はSHA照合後、全画面を等比縮小しています。'
        "形状・動作の変更、把持成立・締結品質の判定は行っていません。</p></footer>"
    )
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>HVJB 公開映像と筐体内外の作業</title><link rel="stylesheet" href="evidence.css">'
        f"</head><body><main>{body}</main></body></html>\n"
    )


def contact(data, output):
    canvas = Image.new("RGB", (1260, 1430), "#f1f5f7")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 27)
    small = ImageFont.truetype(FONT, 21)
    draw.text((25, 20), "公開組立映像：筐体外の組立から、搭載後の作業へ", font=font, fill="#183b4d")
    for index, row in enumerate(data["frames"]):
        x = 20 + (index % 2) * 620
        y = 90 + (index // 2) * 435
        label = row["observation_unmodified"]["time_ja"]
        draw.text((x, y), label, font=small, fill="#183b4d")
        with Image.open(output / row["display_image"]) as source:
            canvas.paste(source.resize((600, 338), Image.Resampling.LANCZOS), (x, y + 45))
    draw.text(
        (25, 1390), "出典：Ampere EV / 2025-06-07　各場面の観察・限界は確認ページに記載", font=small, fill="#536975"
    )
    canvas.save(output / "figures/six_scenes.png")


def entry():
    assert sha(PREVIOUS / MOVIE) == MOVIE_SHA
    text = (PREVIOUS / "index.html").read_text()
    assert text.count("</header>") == 1 and text.count(MOVIE) == 2
    text = text.replace("レビュー v05b</title>", "レビュー v05b.1</title>")
    link = (
        '<p><a class="text-link" href="public_review/index.html">'
        "公開組立映像の6場面と、筐体外・内の仕事を照合する</a></p>"
    )
    (ROOT / "entry").mkdir(exist_ok=False)
    (ROOT / "entry/index_v05b_1.html").write_text(text.replace("</header>", link + "\n</header>"))


def main():
    data = source_data()
    output = ROOT / "output"
    (output / "figures").mkdir(parents=True, exist_ok=False)
    for row in data["frames"]:
        path = REFERENCE_ROOT / row["source_frame_unmodified"]["file"]
        with Image.open(path) as source:
            assert list(source.size) == row["source_frame_unmodified"]["size_px"]
            source.convert("RGB").resize((1200, 675), Image.Resampling.LANCZOS).save(output / row["display_image"])
        row["display_image_sha256"] = sha(output / row["display_image"])
    write_json(output / "evidence_data.json", data)
    (output / "index.html").write_text(document(data), encoding="utf-8")
    for name in ("README.md", "evidence.css"):
        shutil.copy2(ROOT / name, output / name)
    contact(data, output)
    entry()
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "files": [
            {"path": str(path.relative_to(output)), "sha256": sha(path), "bytes": path.stat().st_size}
            for path in sorted(output.rglob("*"))
            if path.is_file()
        ],
        "source_file_hashes": {path.name: sha(path) for path in sorted(ROOT.iterdir()) if path.is_file()},
        "entry_sha256": sha(ROOT / "entry/index_v05b_1.html"),
        "source_video_sha256_after": sha(REFERENCE_ROOT / data["source_video_unmodified"]["file"]),
    }
    assert manifest["source_video_sha256_after"] == data["source_video_unmodified"]["sha256"]
    write_json(output / "evidence_manifest.json", manifest)
    print("PUBLIC_ASSEMBLY_PAGE_READY frames=6 unchanged_observations=6 new_videos=0", flush=True)


if __name__ == "__main__":
    main()
