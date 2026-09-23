# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bundle the reviewed video, diagrams and feature atlas as a local review page."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT.parent / "hvjb-line-progress-20260923"
VIDEO = ROOT.parent / "hvjb-line-video-v04-20260923"
ATLAS = ROOT.parent / "hvjb-feature-atlas-v01-20260923"
PHOTO = ROOT.parent / "hvjb-port-connection-map-v01-20260921/references/ampere_product_photo_1.jpg"
PHOTO_SHA = "5724681b4bef4399f0799751a62577e48ef9b7fd3d6ed5b56d85fd95924937ad"
MOVIE = "HVJB_line_split_process_concept_v04_review.mp4"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def copy_checked(source: Path, destination: Path, expected: str | None = None) -> None:
    assert source.is_file() and not destination.exists(), (source, destination)
    checksum = sha(source)
    if expected is not None:
        assert checksum == expected, source
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert sha(destination) == checksum


def collect_data(data, plan, atlas):
    features = []
    for row in atlas["features"]:
        record = dict(row["existing_review_record"])
        assert record["physical_operation_selected"] is None
        record.update(
            context_image="feature_atlas/figures/" + row["context"]["file"],
            isolated_image="feature_atlas/figures/" + row["isolated"]["file"],
            context_selected_visible_pixels=row["context_selected_visible_pixels"],
        )
        features.append(record)
    scenes = []
    for row in plan["scenes"]:
        scenes.append(
            {
                "id": row["id"],
                "start_s": row["start_s"],
                "stop_s": row["stop_s"],
                "title_ja": row.get("title_ja", "ライン全体の案内"),
                "hold_or_limit_ja": row.get("hold_or_limit_ja", "20区画共用ストッカ・1段往復・5腕の役割"),
            }
        )
    assert len(features) == len({row["id"] for row in features}) == 92
    assert len(data["jobs"]) == 20 and len(scenes) == 18
    scene_ids = {row["id"] for row in scenes}
    feature_ids = {row["id"] for row in features}
    for job in data["jobs"]:
        assert set(job["scene_ids"]) <= scene_ids
        assert set(job["review_feature_ids"]) <= feature_ids
    return {"jobs": data["jobs"], "features": features, "scenes": scenes, "duration_s": 119}


def copy_document(out: Path):
    delivery = read(DOCUMENT / "delivery_manifest.json")
    for row in delivery["files"]:
        copy_checked(DOCUMENT / row["path"], out / row["path"], row["sha256"])
    copy_checked(DOCUMENT / "delivery_manifest.json", out / "delivery_manifest.json")


def copy_video(out: Path):
    visual = read(VIDEO / "audit/video_review_receipt.json")
    readback = read(VIDEO / "audit/video_readback.json")
    assert visual["video_sha256"] == readback["video_sha256"]
    assert visual["scene_stills_inspected"] == 18
    copy_checked(VIDEO / MOVIE, out / MOVIE, visual["video_sha256"])
    for row in readback["samples"]:
        copy_checked(
            VIDEO / row["decoded_png"], out / "video_stills" / f"{row['scene']}.png", row["decoded_png_sha256"]
        )
    for name in ("concept_v04.json", "concept_v03_reused.npz"):
        copy_checked(VIDEO / "data" / name, out / "video_data" / name)
    for name in (
        "video_readback.json",
        "video_review_receipt.json",
        "encoder_dependency_receipt.json",
        "HVJB_line_split_process_concept_v04_review_video.json",
    ):
        copy_checked(VIDEO / "audit" / name, out / "video_audit" / name)
    copy_checked(VIDEO / "previews/concept_v04/manifest.json", out / "video_audit/process_png_manifest.json")


def copy_atlas(out: Path, atlas: dict):
    qa = read(ATLAS / "qa_receipt.json")
    assert qa["atlas_sha256"] == sha(ATLAS / "output/atlas.json")
    assert qa["images_read_back"] == 184
    for row in atlas["features"]:
        for kind in ("context", "isolated"):
            source = ATLAS / "output/figures" / row[kind]["file"]
            copy_checked(source, out / "feature_atlas/figures" / source.name, row[kind]["sha256"])
    copy_checked(ATLAS / "output/atlas.json", out / "feature_atlas/atlas.json")
    copy_checked(ATLAS / "qa_receipt.json", out / "feature_atlas/qa_receipt.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    out = args.output_dir
    assert not out.exists(), out
    data = read(DOCUMENT / "data/line_review_data.json")
    plan = read(VIDEO / "data/concept_v04.json")
    atlas = read(ATLAS / "output/atlas.json")
    assert sha(PHOTO) == PHOTO_SHA
    payload = collect_data(data, plan, atlas)
    html = (ROOT / "page.html").read_text()
    assert html.count("__REVIEW_DATA__") == 1
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    out.mkdir(parents=True)
    copy_document(out)
    copy_video(out)
    copy_atlas(out, atlas)
    copy_checked(PHOTO, out / "review_resources/reference_photo.jpg", PHOTO_SHA)
    for name in ("review.css", "review.js"):
        copy_checked(ROOT / name, out / name)
    (out / "index.html").write_text(html.replace("__REVIEW_DATA__", encoded))
    instructions = """# 動画と図の開き方

`index.html`をブラウザで開いてください。インターネット接続なしでも、動画・図・部品対応を確認できます。

- 全体動画：119秒の工程確認。場面を選ぶと、その時点で一時停止します。
- 20仕事：場所、主担当、手先、支持の引継ぎ、未確定点と、対応する動画・部品。
- 92項目の部品対応：完成状態内の位置と単体図。青が選択対象。単体図の拡大率は個別です。
- 図解6ページ：工程全体、部品群、Cの支持引継ぎ、20仕事、3ST並行、後工程。

動画は`HVJB_line_split_process_concept_v04_review.mp4`の1種類です。
v03の模式動作を再利用して、部品照合図と説明を追加しました。実機軌道・実タクトの再現ではありません。
公開写真の92特徴は全実部品や不可視配線を含む完全BOMではありません。
以前の6ページ資料は同じバイトのまま同梱し、動画と操作ページを追加しています。
"""
    (out / "動画と図の開き方.md").write_text(instructions)
    files = [
        {"path": str(path.relative_to(out)), "sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "files": files,
        "file_count": len(files),
        "mp4_files": [row["path"] for row in files if row["path"].endswith(".mp4")],
        "document_delivery_manifest_sha256": sha(DOCUMENT / "delivery_manifest.json"),
        "video_sha256": sha(VIDEO / MOVIE),
        "atlas_sha256": sha(ATLAS / "output/atlas.json"),
        "data_sha256": sha(DOCUMENT / "data/line_review_data.json"),
        "reference_photo_sha256": PHOTO_SHA,
        "template_sha256": sha(ROOT / "page.html"),
        "builder_sha256": sha(Path(__file__)),
        "physical_acceptance_verdict": None,
    }
    assert manifest["mp4_files"] == [MOVIE]
    (out / "review_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"REVIEW_PAGE_BUILT files={len(files)} jobs=20 features=92 scenes=18 mp4=1", flush=True)


if __name__ == "__main__":
    main()
