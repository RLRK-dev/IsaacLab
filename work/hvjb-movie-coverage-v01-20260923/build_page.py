# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Show exact job-to-scene coverage without inferring completed physical work."""

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
LINE = WORK / "hvjb-line-progress-20260923/data/line_review_data.json"
PLAN = WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json"
PREVIOUS = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05b_20260923")
MOVIE = "HVJB_line_split_process_concept_v05b_review.mp4"
MOVIE_SHA = "65ed3f0f861370c55e3d09de5b6d5d17889aea14d1394de757aba7cf2360ba03"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
INK, MUTED, TEAL, GOLD = "#183b4d", "#536975", "#168773", "#aa701f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def escape(value):
    return html.escape(str(value), quote=True)


def clock(seconds):
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def coverage():
    line = json.loads(LINE.read_text())
    plan = json.loads(PLAN.read_text())
    assert sha(PREVIOUS / MOVIE) == MOVIE_SHA
    assert sha(LINE) == "55948e4d2603b4ebe1ccd30160c89baa990623ad96eedc515c17583bac4bb440"
    assert [row["id"] for row in line["jobs"]] == plan["tasks_preserved"]
    scenes = [row for row in plan["scenes"] if row.get("tasks")]
    assert len(scenes) == 16
    jobs = []
    for original in line["jobs"]:
        related = [row for row in scenes if original["id"] in row["tasks"]]
        assert original["scene_ids"] == [row["id"] for row in related], original["id"]
        assert related, original["id"]
        static = [row["id"] for row in related if row["id"] in plan["static_task_scenes"]]
        moving = [row["id"] for row in related if row["id"] not in plan["static_task_scenes"]]
        mode = "模式動作＋静止説明" if static and moving else "模式動作" if moving else "静止説明のみ"
        jobs.append(
            {
                "job_unmodified": original,
                "scenes_unmodified": related,
                "static_scene_ids": static,
                "schematic_motion_scene_ids": moving,
                "display_kind_ja": mode,
                "physical_completion_verdict": None,
            }
        )
    static_only = [row["job_unmodified"]["id"] for row in jobs if not row["schematic_motion_scene_ids"]]
    assert static_only == ["D01", "D42", "D61", "D70", "D71"]
    return {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "line_source_sha256": sha(LINE),
        "video_plan_sha256": sha(PLAN),
        "video_sha256": MOVIE_SHA,
        "video_filename": MOVIE,
        "jobs": jobs,
        "static_only_jobs": static_only,
        "source_static_task_scenes": plan["static_task_scenes"],
        "job_count": len(jobs),
        "process_scene_count": len(scenes),
        "total_scene_count": len(plan["scenes"]),
        "schematic_motion_job_count": len(jobs) - len(static_only),
        "physical_acceptance_verdict": None,
        "new_video": False,
    }


def label(draw, position, value, size=26, color=INK):
    font = ImageFont.truetype(FONT, size)
    box = draw.textbbox(position, value, font=font)
    assert 0 <= box[0] <= box[2] <= 2000 and 0 <= box[1] <= box[3] <= 1590, (value, box)
    draw.text(position, value, font=font, fill=color)


def diagram(data, output):
    picture = Image.new("RGB", (2000, 1590), "#f1f5f7")
    draw = ImageDraw.Draw(picture)
    label(draw, (40, 25), "20の仕事 × 動画の16工程場面", 48)
    label(draw, (42, 94), "動画v05b：119秒 ／ 表示時間は実タクトではありません", 29, MUTED)
    columns = (48, 196, 680, 1045, 1420)
    for x, value in zip(columns, ("仕事", "作業", "場所", "動画の場面・時刻", "表し方"), strict=True):
        label(draw, (x, 172), value, 27)
    for index, row in enumerate(data["jobs"]):
        y = 226 + 60 * index
        draw.rectangle((32, y - 2, 1968, y + 54), fill="white" if index % 2 == 0 else "#e9f0f4")
        job = row["job_unmodified"]
        scenes = row["scenes_unmodified"]
        if len(scenes) == 1:
            scene = scenes[0]
            time = f"{scene['id']}  {clock(scene['start_s'])}–{clock(scene['stop_s'])}"
        else:
            time = " / ".join(f"{s['id']} {clock(s['start_s'])}" for s in scenes)
        values = (job["id"], job["title_ja"], job["location_ja"], time, row["display_kind_ja"])
        for column, (x, value) in enumerate(zip(columns, values, strict=True)):
            color = (TEAL if row["schematic_motion_scene_ids"] else GOLD) if column == 4 else INK
            label(draw, (x, y + 7), value, 25, color)
    label(
        draw,
        (42, 1462),
        "模式動作：役割と大まかな動きの図解。全ねじ・全線の組立完了や実機成立を示すものではありません。",
        27,
    )
    label(
        draw,
        (42, 1511),
        "静止説明：未具体化の仕事を明示。D81は復路を動作表示し、回収・補給は静止説明として残しています。",
        26,
        MUTED,
    )
    picture.save(output / "coverage.png")


def table_row(row):
    job = row["job_unmodified"]
    buttons = "".join(
        f'<button type="button" data-scene="{scene["id"]}" data-seek="{scene["start_s"]}">'
        f"{scene['id']}　{clock(scene['start_s'])}–{clock(scene['stop_s'])}</button><br>"
        for scene in row["scenes_unmodified"]
    )
    mode_class = "mode" if row["schematic_motion_scene_ids"] else "mode static"
    return (
        f'<tr id="{job["id"]}"><td><a href="../hand_review/index.html#job-{job["id"]}">'
        f"{job['id']} {escape(job['title_ja'])}</a><br>{escape(job['location_ja'])}</td>"
        f'<td><span class="{mode_class}">{row["display_kind_ja"]}</span><br>{buttons}</td>'
        f"<td>主担当：{escape(job['primary_ja'])}<br>手先：{escape(job['hands_ja'])}"
        f"<br>補助：{escape(job['assistance_ja'])}</td>"
        f"<td>{escape(job['unresolved_ja'])}</td></tr>"
    )


def document(data):
    rows = "".join(table_row(row) for row in data["jobs"])
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>HVJB 20仕事と動画の対応</title><link rel="stylesheet" href="coverage.css"></head><body><main>'
        '<nav><a href="../index_v05b_2.html">← 全体レビュー</a><a href="../public_review/index.html">公開映像の根拠</a>'
        '<a href="../hand_review/index.html">フィンガと仕事の対応</a></nav>'
        "<h1>20仕事のうち、動画でどこまで示しているか</h1>"
        '<p class="intro">20仕事すべてに対応場面があります。大まかな動作を見せる仕事と、'
        "詳細が決まっておらず静止説明で残した仕事を分けました。全組立動作の完成率を表す表ではありません。</p>"
        '<div class="counts"><p><b>20仕事</b>すべてに動画の対応場面あり</p>'
        "<p><b>15仕事</b>模式動作の場面あり</p><p><b>5仕事</b>静止説明のみ</p></div>"
        f'<video controls preload="metadata" src="../{MOVIE}"></video>'
        '<p id="movie-position" class="minor" aria-live="polite">下の場面ボタンで、その開始位置へ移動します。</p>'
        '<p class="minor">既存の119秒の動画v05bを再利用しています。新しい動画ファイルはありません。</p>'
        '<figure><a href="coverage.png"><img src="coverage.png" width="2000" height="1590"'
        ' alt="20仕事、動画場面、場所、模式動作と静止説明の対応図"></a></figure>'
        '<div class="note">線材準備D01、未特定の内部工具作業D42、LV/HVIL接続D61、蓋・シールD70、'
        "検査D71は静止説明です。回収・補給を含むD81は、パレットの復路だけを動作で示しています。</div>"
        "<h2>仕事ごとの照合先と、残る未確定事項</h2>"
        "<p>手先欄は比較候補を含みます。仕事名を選ぶと、既存の詳細図との対応を確認できます。</p>"
        '<div class="table-wrap"><table><thead><tr><th>仕事・場所</th><th>表し方・動画の位置</th>'
        f"<th>現在の担当・手先の記載</th><th>既存の未確定事項</th></tr></thead><tbody>{rows}</tbody></table></div>"
        "<footer><p>92項目の完成写真との照合図は、92件の組立動作を意味しません。"
        "隠れた固定点や線の両端を補って動作完成とする判定は行っていません。</p>"
        '<p><a href="coverage_data.json">20仕事と場面の対応データ</a> ／ <a href="README.md">照合方法</a></p>'
        '</footer></main><script src="coverage.js"></script></body></html>\n'
    )


def main():
    data = coverage()
    output = ROOT / "output"
    output.mkdir(exist_ok=False)
    write_json(output / "coverage_data.json", data)
    diagram(data, output)
    (output / "index.html").write_text(document(data), encoding="utf-8")
    for name in ("README.md", "coverage.css", "coverage.js"):
        shutil.copy2(ROOT / name, output / name)
    entry = (PREVIOUS / "index_v05b_1.html").read_text()
    assert entry.count("</header>") == 1
    entry = entry.replace("レビュー v05b.1</title>", "レビュー v05b.2</title>")
    addition = (
        '<p><a class="text-link" href="coverage_review/index.html">20仕事と動画場面・未具体化の仕事を一覧で見る</a></p>'
    )
    (ROOT / "entry").mkdir(exist_ok=False)
    (ROOT / "entry/index_v05b_2.html").write_text(entry.replace("</header>", addition + "\n</header>"))
    write_json(
        output / "coverage_manifest.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "files": [
                {"path": str(path.relative_to(output)), "sha256": sha(path), "bytes": path.stat().st_size}
                for path in sorted(output.rglob("*"))
                if path.is_file()
            ],
            "entry_sha256": sha(ROOT / "entry/index_v05b_2.html"),
            "source_file_hashes": {path.name: sha(path) for path in sorted(ROOT.iterdir()) if path.is_file()},
        },
    )
    print("JOB_MOVIE_COVERAGE jobs=20 process_scenes=16 schematic_jobs=15 static_only_jobs=5 new_videos=0", flush=True)


if __name__ == "__main__":
    main()
