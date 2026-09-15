# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Deliver the visible-entry static review; preserve all earlier deliveries."""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("/home/rlrk/Downloads/THREAD_HVJB_写真部品照合_v03_20260915")


def copy(source, relative):
    target = OUTPUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert digest(source) == digest(target)


def make_page():
    catalog = json.loads((ROOT / "data/hvjb_photo_correspondence_v03_p01.json").read_text())
    geometry = json.loads(gzip.decompress((ROOT / "data/hvjb_photo_model_v03_p02.json.gz").read_bytes()))
    for row in geometry.values():
        for mesh in row["meshes"]:
            mesh["vertices"] = [[round(x, 6) for x in vertex] for vertex in mesh["vertices"]]
    payload = json.dumps({"catalog": catalog, "geometry": geometry}, ensure_ascii=False, separators=(",", ":"))
    page = (
        (ROOT / "scripts/hvjb_photo_review_v03.html")
        .read_text()
        .replace("__PAYLOAD__", payload.replace("<", "\\u003c"))
    )
    for name in [f"ampere_product_photo_{i}.jpg" for i in (1, 2, 3)] + ["ampere_hvjb_5_400_current_v1_1.pdf"]:
        page = page.replace("references/" + name, "references/op040_real_products_20260912/" + name)
    return page.replace(
        "references/te_408_32095_instruction.pdf",
        "references/connector_correction_20260915/te_408_32095_instruction.pdf",
    ).replace("references/te_2103245_drawing.pdf", "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf")


def manifest():
    records = []
    for path in sorted(OUTPUT.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        assert path.suffix.lower() not in {".mp4", ".webm", ".mkv", ".mov"}
        relative = path.relative_to(OUTPUT)
        source = ROOT / relative
        if source.is_file():
            assert digest(source) == digest(path), str(relative)
        records.append({"file": str(relative), "sha256": digest(path), "bytes": path.stat().st_size})
    report = {
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(OUTPUT),
        "files": records,
        "motion_created": False,
        "complete_product_reconstruction": False,
        "movie_files": [],
        "viewer_vertex_rounding_m": 0.000001,
        "copy_hashes_equal": True,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (OUTPUT / "manifest.json").write_text(text)
    (ROOT / "audit/hvjb_photo_delivery_v03.json").write_text(text)
    print("PHOTO_REVIEW_PACKAGED", OUTPUT, len(records), flush=True)


def create():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    names = [
        "UR15_JB_photo_correspondence_v03_p02.blend",
        "data/hvjb_wire_observations_v03.json",
        "data/hvjb_photo_correspondence_v03_p01.json",
        "data/hvjb_photo_correspondence_v02_p02.json",
        "data/hvjb_video_evidence_v02.json",
        "data/hvjb_photo_model_v03_p02.json.gz",
        "data/hvjb_photo_cad_v01.json.gz",
        "data/header_review_v03/meshes.json.gz",
        "analysis/hvjb_photo_correspondence_v03.md",
        "analysis/hvjb_photo_execution_v03.md",
        "audit/hvjb_photo_catalog_v03_p01.json",
        "audit/hvjb_photo_model_v03_p02.json",
        "audit/hvjb_photo_entry_display_v03.json",
        "scripts/build_hvjb_photo_catalog_v03.py",
        "scripts/build_hvjb_photo_model_v03.py",
        "scripts/package_hvjb_photo_review_v03.py",
        "scripts/hvjb_photo_review_v03.html",
        "scripts/check_hvjb_photo_review_v03.mjs",
        "scripts/probe_hvjb_entry_display_v03.py",
        "scripts/build_hvjb_photo_catalog_v01.py",
        "scripts/build_hvjb_photo_model_v01.py",
        "scripts/build_hvjb_photo_model_v02.py",
        "references/op040_real_products_20260912/ampere_hvjb_5_400_current_v1_1.pdf",
        "references/connector_correction_20260915/te_408_32095_instruction.pdf",
        "references/connector_correction_20260915/te_2103340_drawing.pdf",
        "references/connector_correction_20260915/te_2103346_drawing.pdf",
        "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf",
    ]
    catalog = json.loads((ROOT / "data/hvjb_photo_correspondence_v03_p01.json").read_text())
    names.extend(row["file"] for row in catalog["photos"].values())
    for name in names:
        copy(ROOT / name, name)
    for view in ("top", "oblique", "uncovered"):
        copy(ROOT / f"previews/hvjb_photo_v03_p02/{view}.png", f"previews/{view}.png")
    for name in ("hvjb_photo_catalog_v03_p01", "hvjb_photo_model_v03_p02", "hvjb_photo_entry_display_v03"):
        copy(Path("/tmp") / (name + ".log"), "audit/" + name + ".log")
    (OUTPUT / "review.html").write_text(make_page())
    (OUTPUT / "README.txt").write_text(
        "写真・内部構成の照合 v03\n\nreview.htmlをブラウザーで開いてください。\n"
        "可視配線27区間、外装入口20か所を記録。12か所を静止モデルの表示用端末へ対応させました。\n"
        "写真は選択部分を拡大でき、線の両端を○（見える入口）/□（追跡終了）で示します。\n"
        "「線と入口部品だけ表示」と続きの候補2組を確認できます。隠れた続きは結線しません。\n"
        "リレー8端末の外装位置と開口を修正。根拠のないWI31/WI32を可視一覧から退役しました。\n"
        "必要コンタクト数は維持。写真で見えるものと資料による必要部品を分けています。\n"
        "92IDは登録特徴の数で、全BOM数ではありません。全配線の端子・極番号・抵抗位置は未確定です。\n"
        "内部寸法と入口合わせは表示用推定。製造図・把持安定性・締結品質・物理妥当性の判定ではありません。\n"
        "保存読戻し済み。新しい工程動作・動画は生成/配布していません。旧版は別名で保全しています。\n"
        "ソース再実行には同ブランチの既存ヘルパーと保全入力が必要です。\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--finalize", action="store_true", help="Include UI checks and refresh this revision's manifest"
    )
    args = parser.parse_args()
    if args.finalize:
        assert (OUTPUT / "review.html").is_file()
        copy(ROOT / "audit/hvjb_photo_browser_v03.json", "audit/hvjb_photo_browser_v03.json")
        copy(ROOT / "analysis/hvjb_photo_execution_v03.md", "analysis/hvjb_photo_execution_v03.md")
    else:
        create()
    manifest()


if __name__ == "__main__":
    main()
