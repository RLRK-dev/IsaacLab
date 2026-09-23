# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bundle one v05b movie and the previously delivered whole-line review material."""

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PREVIOUS = Path("/home/rlrk/Downloads/HVJB_ライン全体レビュー_v05_20260923")
VIDEO = WORK / "hvjb-line-video-v05b-20260923"
LOGISTICS = WORK / "hvjb-logistics-review-v01-20260923"
MOVIE = "HVJB_line_split_process_concept_v05b_review.mp4"
OLD_MOVIE = "HVJB_line_split_process_concept_v05_review.mp4"
spec = importlib.util.spec_from_file_location(
    "v05_bundle_helpers", WORK / "hvjb-review-page-v05-20260923/build_bundle.py"
)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
sha, copy, snapshot = helper.sha, helper.copy, helper.snapshot


def inherited_files(out, before):
    excluded = {
        OLD_MOVIE,
        "index.html",
        "index_v04_1.html",
        "index_v04_2.html",
        "index_v05_1.html",
        "review_manifest.json",
        "page_qa_receipt.json",
        "動画と図の開き方.md",
    }
    names = []
    for name in before:
        if name in excluded or name.startswith(("video_data/", "video_audit/", "video_stills/")):
            continue
        copy(PREVIOUS / name, out / name)
        names.append(name)
    return names


def entry(out):
    page = (PREVIOUS / "index_v05_1.html").read_text()
    assert page.count(OLD_MOVIE) == 2 and page.count("</header>") == 1
    page = page.replace(OLD_MOVIE, MOVIE)
    page = page.replace("レビュー v05.1</title>", "レビュー v05b</title>")
    page = page.replace("ラインの流れを動画v05で確認", "ラインの流れを動画v05bで確認")
    old = "写真対応の部品モデルを継承し、v05では手先表示の切替とS12の画角を修正しました。"
    new = "写真対応モデルとv05の動作を継承。v05bでは旧搬出XYZ等の表示を整理し、共用ストッカの物流図を加えました。"
    assert page.count(old) == 1
    page = page.replace(old, new)
    link = (
        '<p><a class="text-link" href="logistics_review/index.html">20共用区画・同じXYZ・1段往復を6場面で見る</a></p>'
    )
    page = page.replace("</header>", link + "\n</header>")
    (out / "index.html").write_text(page)
    for name in ("index_v04_1.html", "index_v04_2.html", "index_v05_1.html"):
        (out / name).write_text(
            '<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0;url=index.html">'
            '<title>全体レビューv05bへ</title><p><a href="index.html">全体レビューv05bを開く</a></p></html>\n'
        )


def updated_video(out):
    readback = json.loads((VIDEO / "audit/video_readback.json").read_text())
    visual = json.loads((VIDEO / "audit/video_review_receipt.json").read_text())
    assert readback["video_sha256"] == visual["video_sha256"] == sha(VIDEO / MOVIE)
    assert visual["scene_stills_inspected"] == 36 and visual["distinct_scenes_inspected"] == 18
    copy(VIDEO / MOVIE, out / MOVIE)
    plan = json.loads((VIDEO / "data/concept_v05b.json").read_text())
    for scene in plan["scenes"]:
        index = int((scene["start_s"] + 0.62 * (scene["stop_s"] - scene["start_s"])) * 15)
        row = next(row for row in readback["samples"] if row["source_sample_index"] == index)
        copy(VIDEO / row["decoded_png"], out / "video_stills" / f"{scene['id']}.png")
    for row in readback["samples"]:
        copy(VIDEO / row["decoded_png"], out / "video_audit" / row["decoded_png"])
    for path in (VIDEO / "audit").glob("*.json"):
        copy(path, out / "video_audit" / path.name)
    for name in ("concept_v05b.json", "concept_display_v05_reused.npz"):
        copy(VIDEO / "data" / name, out / "video_data" / name)
    copy(VIDEO / "README.md", out / "video_audit/動画v05b.md")
    copy(VIDEO / "REVIEW_SCOPE.md", out / "video_audit/表示整理の範囲.md")
    for name in ("display_v05_delta.json", "correction_verification.json", "手先表示の修正記録.md"):
        copy(PREVIOUS / "video_audit" / name, out / "video_audit/history_v05" / name)
    return readback["video_sha256"]


def main():
    out = ROOT / "output"
    out.mkdir(exist_ok=False)
    before = snapshot(PREVIOUS)
    inherited = inherited_files(out, before)
    entry(out)
    video_sha = updated_video(out)
    for path in sorted((LOGISTICS / "output").rglob("*")):
        if path.is_file():
            copy(path, out / "logistics_review" / path.relative_to(LOGISTICS / "output"))
    (out / "動画と図の開き方.md").write_text(
        "# ライン全体レビュー v05b\n\n"
        "`index.html`を開いてください。119秒の工程レビュー動画は1本です。\n"
        "20仕事、92写真特徴、6ページの工程図、8系統・12用途の手先図、3STの役割図、\n"
        "11部品群、20共用区画と往復物流の図をこの入口から確認できます。\n\n"
        "v05bでは、旧構成の別置き搬出XYZ等を表示から除きました。\n"
        "供給と完成品収納は同じXYZ、パレットは1段往復、完成品は筐体を出した01区画へ戻します。\n"
        "保存された動作行列とカメラはv05と同じです。元資料は上書きしていません。\n\n"
        "左の図解動作は92項目の全組立動作ではありません。内部の未特定工具作業、主ヒューズの工程、\n"
        "LV/HVIL端子、蓋・検査の詳細は未確定のまま表示しています。実機成立の判定は行っていません。\n"
    )
    after = snapshot(out)
    assert all(after[name] == before[name] for name in inherited)
    assert snapshot(PREVIOUS) == before
    movies = sorted(name for name in after if name.endswith(".mp4"))
    assert movies == [MOVIE]
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "file_count": len(after),
        "files": [
            {"path": name, "sha256": digest, "bytes": (out / name).stat().st_size} for name, digest in after.items()
        ],
        "mp4_files": movies,
        "video_sha256": video_sha,
        "inherited_files_unchanged": inherited,
        "previous_folder_files_unchanged": len(before),
        "previous_entry_sha256": before["index_v05_1.html"],
        "browser_ui_observed": False,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    (out / "review_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"V05B_BUNDLE_COMPLETE files={len(after) + 1} inherited={len(inherited)} mp4=1")


if __name__ == "__main__":
    main()
