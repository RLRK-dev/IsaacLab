# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package the static photo correspondence, preserving unresolved requirements."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("/home/rlrk/Downloads/THREAD_HVJB_写真部品照合_v01_20260915")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def copy_record(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert digest(source) == digest(target)
    return {
        "file": str(target.relative_to(OUTPUT)),
        "source": str(source),
        "sha256": digest(target),
        "bytes": target.stat().st_size,
    }


def make_page():
    catalog = json.loads((ROOT / "data/hvjb_photo_correspondence_v01.json").read_text())
    geometry = json.loads(gzip.decompress((ROOT / "data/hvjb_photo_model_v01_p02.json.gz").read_bytes()))
    for row in geometry.values():
        for mesh in row["meshes"]:
            mesh["vertices"] = [[round(v, 6) for v in vertex] for vertex in mesh["vertices"]]
    page = (ROOT / "scripts/hvjb_photo_review_v01.html").read_text()
    payload = json.dumps({"catalog": catalog, "geometry": geometry}, ensure_ascii=False, separators=(",", ":"))
    page = page.replace("__PAYLOAD__", payload.replace("<", "\\u003c")).replace("_v01_p01", "_v01_p02")
    for name in [f"ampere_product_photo_{i}.jpg" for i in (1, 2, 3)] + ["ampere_hvjb_5_400_current_v1_1.pdf"]:
        page = page.replace("references/" + name, "references/op040_real_products_20260912/" + name)
    page = page.replace(
        "references/te_408_32095_instruction.pdf",
        "references/connector_correction_20260915/te_408_32095_instruction.pdf",
    )
    return page.replace(
        "references/te_2103245_drawing.pdf", "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf"
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    names = [
        "UR15_JB_photo_correspondence_v01_p02.blend",
        "data/hvjb_photo_correspondence_v01.json",
        "data/hvjb_photo_model_v01_p02.json.gz",
        "data/hvjb_photo_cad_v01.json.gz",
        "data/header_review_v03/meshes.json.gz",
        "analysis/hvjb_photo_correspondence_v01.md",
        "audit/hvjb_photo_catalog_v01.json",
        "audit/hvjb_photo_cad_v01.json",
        "audit/hvjb_photo_model_v01_p02.json",
        "scripts/build_hvjb_photo_catalog_v01.py",
        "scripts/build_hvjb_photo_model_v01.py",
        "scripts/prepare_hvjb_photo_cad_v01.py",
        "scripts/package_hvjb_photo_review_v01.py",
        "scripts/check_hvjb_photo_review_v01.mjs",
        "scripts/hvjb_photo_review_v01.html",
        "references/op040_real_products_20260912/ampere_hvjb_5_400_current_v1_1.pdf",
        "references/connector_correction_20260915/te_408_32095_instruction.pdf",
        "references/connector_correction_20260915/te_2103340_drawing.pdf",
        "references/connector_correction_20260915/te_2103346_drawing.pdf",
        "references/hvjb_photo_inventory_20260915/te_2103245_drawing.pdf",
    ]
    names += [f"references/op040_real_products_20260912/ampere_product_photo_{i}.jpg" for i in (1, 2, 3)]
    names += [f"references/hvjb_photo_inventory_20260915/te_2103245_{i}_step.zip" for i in (1, 4, 5, 6)]
    names += [f"references/connector_correction_20260915/te_{number}_step.zip" for number in ("2103340_1", "2103346_2")]
    records = [copy_record(ROOT / name, OUTPUT / name) for name in names]
    for name in ("top", "oblique"):
        source = ROOT / f"previews/hvjb_photo_v01_p02/{name}.png"
        records.append(copy_record(source, OUTPUT / f"previews/{name}.png"))
    for filename, target in (
        ("hvjb_photo_model_v01_p01.log", "initial_build_error.log"),
        ("hvjb_photo_model_v01_p02.log", "static_model_build.log"),
    ):
        records.append(copy_record(Path("/tmp") / filename, OUTPUT / "audit" / target))
    page_path = OUTPUT / "review.html"
    page_path.write_text(make_page())
    records.append({"file": "review.html", "sha256": digest(page_path), "bytes": page_path.stat().st_size})
    readme = (
        "写真・内部構成の照合 v01\n\nreview.html をブラウザーで開いてください。\n"
        "静止モデルは写真との対応を確認する途中版です。全配線・全BOMの完成ではありません。\n"
        "未特定のヒューズ、抵抗、線の両端、圧着端子、共締め等を台帳へ残しています。\n"
        "Blenderと台帳の識別ID72個および保存前後のworldメッシュ一致を確認しました。\n"
        "これは全実物部品を72個と数えた結果ではありません。物理妥当性は未判定です。\n"
        "TE以外の内部寸法は写真からの表示用推定。ビューアー座標は表示用に1µmへ丸めています。\n"
        "主接触器等の実型式、隠れた構成が未確定のため工程動作・新動画はまだ作っていません。\n"
        "初回生成は空のWorld参照で停止。環境を作成して再実行しました。形状への変更ではありません。\n"
        "p02は上面カメラの向きと露出を修正。p01と旧v03以下は元の作業場所で保全しています。\n"
        "ソースの実行にはIsaacLabの同ブランチと既存ヘルパーが必要です。\n"
    )
    (OUTPUT / "README.txt").write_text(readme)
    records.append({"file": "README.txt", "sha256": digest(OUTPUT / "README.txt")})
    manifest = {
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(OUTPUT),
        "files": records,
        "motion_created": False,
        "complete_product_reconstruction": False,
        "copy_hashes_equal": True,
        "viewer_vertex_rounding_m": 0.000001,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "audit/hvjb_photo_delivery_v01.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("PHOTO_REVIEW_PACKAGED", OUTPUT, len(records), flush=True)


if __name__ == "__main__":
    main()
