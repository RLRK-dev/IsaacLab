# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package the second static review without delivering an additional movie."""

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
OUTPUT = Path("/home/rlrk/Downloads/THREAD_HVJB_写真部品照合_v02_20260915")


def copy(source, relative):
    target = OUTPUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert digest(source) == digest(target)


def make_page():
    catalog = json.loads((ROOT / "data/hvjb_photo_correspondence_v02_p02.json").read_text())
    geometry = json.loads(gzip.decompress((ROOT / "data/hvjb_photo_model_v02_p02.json.gz").read_bytes()))
    for row in geometry.values():
        for mesh in row["meshes"]:
            mesh["vertices"] = [[round(x, 6) for x in vertex] for vertex in mesh["vertices"]]
    payload = json.dumps({"catalog": catalog, "geometry": geometry}, ensure_ascii=False, separators=(",", ":"))
    page = (
        (ROOT / "scripts/hvjb_photo_review_v02.html")
        .read_text()
        .replace("__PAYLOAD__", payload.replace("<", "\\u003c"))
    )
    for name in [f"ampere_product_photo_{i}.jpg" for i in (1, 2, 3)] + ["ampere_hvjb_5_400_current_v1_1.pdf"]:
        page = page.replace("references/" + name, "references/op040_real_products_20260912/" + name)
    page = page.replace(
        "references/te_408_32095_instruction.pdf",
        "references/connector_correction_20260915/te_408_32095_instruction.pdf",
    )
    return page.replace(
        "references/te_2103245_drawing.pdf", "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf"
    )


def manifest():
    # All content is generated in this dedicated directory. The original videos remain in references in the worktree.
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
    data = {
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(OUTPUT),
        "files": records,
        "motion_created": False,
        "complete_product_reconstruction": False,
        "movie_files": [],
        "viewer_vertex_rounding_m": 0.000001,
        "copy_hashes_equal": True,
    }
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    (OUTPUT / "manifest.json").write_text(text)
    (ROOT / "audit/hvjb_photo_delivery_v02.json").write_text(text)
    print("PHOTO_REVIEW_PACKAGED", OUTPUT, len(records), flush=True)


def create():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    names = [
        "UR15_JB_photo_correspondence_v02_p02.blend",
        "data/hvjb_photo_correspondence_v02_p02.json",
        "data/hvjb_photo_correspondence_v01.json",
        "data/hvjb_video_evidence_v02.json",
        "data/hvjb_photo_model_v02_p02.json.gz",
        "data/hvjb_photo_cad_v01.json.gz",
        "data/header_review_v03/meshes.json.gz",
        "analysis/hvjb_photo_correspondence_v02.md",
        "analysis/hvjb_photo_execution_v02.md",
        "audit/hvjb_photo_catalog_v02_p02.json",
        "audit/hvjb_photo_model_v02_p02.json",
        "scripts/collect_hvjb_video_evidence_v02.py",
        "scripts/build_hvjb_photo_catalog_v02.py",
        "scripts/build_hvjb_photo_model_v02.py",
        "scripts/package_hvjb_photo_review_v02.py",
        "scripts/hvjb_photo_review_v02.html",
        "scripts/check_hvjb_photo_review_v02.mjs",
        "scripts/build_hvjb_photo_catalog_v01.py",
        "scripts/build_hvjb_photo_model_v01.py",
        "references/op040_real_products_20260912/ampere_hvjb_5_400_current_v1_1.pdf",
        "references/connector_correction_20260915/te_408_32095_instruction.pdf",
        "references/connector_correction_20260915/te_2103340_drawing.pdf",
        "references/connector_correction_20260915/te_2103346_drawing.pdf",
        "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf",
    ]
    catalog = json.loads((ROOT / "data/hvjb_photo_correspondence_v02_p02.json").read_text())
    names.extend(row["file"] for row in catalog["photos"].values())
    for name in names:
        copy(ROOT / name, name)
    for view in ("top", "oblique", "uncovered"):
        copy(ROOT / f"previews/hvjb_photo_v02_p02/{view}.png", f"previews/{view}.png")
    for name in ("hvjb_video_evidence_v02", "hvjb_photo_catalog_v02_p02", "hvjb_photo_model_v02_p02"):
        copy(Path("/tmp") / (name + ".log"), "audit/" + name + ".log")
    (OUTPUT / "review.html").write_text(make_page())
    (OUTPUT / "README.txt").write_text(
        "写真・内部構成の照合 v02\n\nreview.html をブラウザーで開いてください。\n"
        "補機ヒューズを5個へ補完し、主ヒューズと被覆、立上りバスバー、端末被覆等を修正しました。\n"
        "参照欄を切り替えると公式映像の該当場面も確認できます。新しい動画は生成・配布していません。\n"
        "筐体と中央被覆を非表示にして、隠れる3段目や主ヒューズ本体を確認できます。\n"
        "89IDは登録した照合特徴の数で、全BOM部品数ではありません。\n"
        "配線の両端、抵抗の旧写真内の位置、共締め・端子・HVIL経路等は未確定です。\n"
        "完全再現・製造図・締結品質・把持安定性・物理妥当性の判定ではありません。\n"
        "TE以外の内部寸法は表示用推定で、工程動作の確定値へは転用していません。\n"
        "2025年の実作業品と指定写真の同一製造版は未確認です。別版の配線を旧写真へ転記していません。\n"
        "nativeは保存読戻し済み。ビューアー頂点は表示用に1µmへ丸めています。\n"
        "ソース再実行には同ブランチの既存ヘルパー・保全入力が必要です。成果物は旧版と別名です。\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize", action="store_true", help="Include completed UI checks and refresh own manifest")
    args = parser.parse_args()
    if not args.finalize:
        create()
    else:
        assert (OUTPUT / "review.html").is_file()
        copy(ROOT / "audit/hvjb_photo_browser_v02.json", "audit/hvjb_photo_browser_v02.json")
        copy(ROOT / "analysis/hvjb_photo_execution_v02.md", "analysis/hvjb_photo_execution_v02.md")
    manifest()


if __name__ == "__main__":
    main()
