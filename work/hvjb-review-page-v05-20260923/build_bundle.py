# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Bundle one updated review movie with the unchanged whole-line review material."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
PREVIOUS = Path("/home/rlrk/Downloads/HVJB_ライン全体と組立場所_v04_20260923")
VIDEO = ROOT.parent / "hvjb-line-video-v05-20260923"
CORRECTION = ROOT.parent / "hvjb-display-continuity-v01-20260923"
MOVIE = "HVJB_line_split_process_concept_v05_review.mp4"
OLD_MOVIE = "HVJB_line_split_process_concept_v04_review.mp4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source, destination):
    assert source.is_file() and not destination.exists(), destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert sha(source) == sha(destination)


def snapshot(folder):
    return {str(path.relative_to(folder)): sha(path) for path in sorted(folder.rglob("*")) if path.is_file()}


def inherited_files(out, before):
    excluded = {
        OLD_MOVIE,
        "index.html",
        "index_v04_1.html",
        "index_v04_2.html",
        "review_manifest.json",
        "page_qa_receipt.json",
        "動画と図の開き方.md",
    }
    inherited = []
    for name in before:
        if name in excluded or name.startswith(("video_data/", "video_audit/", "video_stills/")):
            continue
        copy(PREVIOUS / name, out / name)
        inherited.append(name)
    return inherited


def updated_page(out):
    source = PREVIOUS / "index_v04_2.html"
    page = source.read_text()
    assert page.count(OLD_MOVIE) == 2
    page = page.replace(OLD_MOVIE, MOVIE)
    page = page.replace("レビュー v04.2</title>", "レビュー v05</title>")
    page = page.replace("ラインの流れを動画で確認", "ラインの流れを動画v05で確認")
    old_note = "モデルの頂点・面とv03の保存動作は変更していません。"
    new_note = "写真対応の部品モデルを継承し、v05では手先表示の切替とS12の画角を修正しました。"
    assert page.count(old_note) == 1
    page = page.replace(old_note, new_note)
    (out / "index.html").write_text(page)
    for name in ("index_v04_1.html", "index_v04_2.html"):
        (out / name).write_text(
            '<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0;url=index.html">'
            '<title>全体レビューv05へ</title><p><a href="index.html">全体レビューv05を開く</a></p></html>\n'
        )


def updated_video(out):
    readback = json.loads((VIDEO / "audit/video_readback.json").read_text())
    visual = json.loads((VIDEO / "audit/video_review_receipt.json").read_text())
    assert readback["video_sha256"] == visual["video_sha256"] == sha(VIDEO / MOVIE)
    assert visual["scene_stills_inspected"] == 42 and visual["distinct_scenes_inspected"] == 18
    copy(VIDEO / MOVIE, out / MOVIE)
    plan = json.loads((VIDEO / "data/concept_v05.json").read_text())
    for scene in plan["scenes"]:
        index = int((scene["start_s"] + 0.62 * (scene["stop_s"] - scene["start_s"])) * 15)
        row = next(row for row in readback["samples"] if row["source_sample_index"] == index)
        copy(VIDEO / row["decoded_png"], out / "video_stills" / f"{scene['id']}.png")
    for row in readback["samples"]:
        copy(VIDEO / row["decoded_png"], out / "video_audit" / row["decoded_png"])
    for path in (VIDEO / "audit").glob("*.json"):
        copy(path, out / "video_audit" / path.name)
    for name in ("concept_v05.json", "concept_display_v05_framed.npz"):
        copy(VIDEO / "data" / name, out / "video_data" / name)
    for name in ("display_v05_delta.json", "correction_verification.json"):
        copy(CORRECTION / "audit" / name, out / "video_audit" / name)
    copy(CORRECTION / "README.md", out / "video_audit/手先表示の修正記録.md")
    copy(VIDEO / "README.md", out / "video_audit/動画v05.md")
    return readback["video_sha256"]


def main():
    out = ROOT / "output"
    out.mkdir(exist_ok=False)
    before = snapshot(PREVIOUS)
    inherited = inherited_files(out, before)
    updated_page(out)
    video_sha = updated_video(out)
    (out / "動画と図の開き方.md").write_text(
        "# ライン全体レビュー v05\n\n"
        "`index.html`を開いてください。全体動画v05、20仕事、92項目、6ページの図を切り替えられます。\n"
        "ページ上部から、8系統・12用途の手先図と、3STの共用補助の図へ進めます。\n\n"
        "動画は119秒の工程レビュー1本です。工程PNGから直接符号化しました。\n"
        "同梱のPDFと図はv04を継承しています。v05の変更は手先表示の6区間とS12の画角です。\n"
        "部品・工具・配線・パレットの保存姿勢、20仕事と92項目の対応は変更していません。\n\n"
        "未知の工程と部品型式は未確定のまま表示しています。把持力や実機成立の判定ではありません。\n"
    )
    after = snapshot(out)
    assert all(after[name] == before[name] for name in inherited)
    assert snapshot(PREVIOUS) == before
    mp4 = sorted(name for name in after if name.endswith(".mp4"))
    assert mp4 == [MOVIE]
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "file_count": len(after),
        "files": [
            {"path": name, "sha256": digest, "bytes": (out / name).stat().st_size} for name, digest in after.items()
        ],
        "mp4_files": mp4,
        "video_sha256": video_sha,
        "inherited_files_unchanged": inherited,
        "previous_folder_files_unchanged": len(before),
        "previous_entry_sha256": before["index_v04_2.html"],
        "browser_ui_observed": False,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    (out / "review_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"V05_BUNDLE_COMPLETE files={len(after) + 1} inherited={len(inherited)} mp4=1")


if __name__ == "__main__":
    main()
