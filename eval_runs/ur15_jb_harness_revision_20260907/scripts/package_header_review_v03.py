# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Deliver one process movie with the pinned revised native and source records."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from package_hand_line_review_v01 import digest, review_page

ROOT = Path(__file__).resolve().parents[1]
VIDEO = "UR15_JB_OP010_OP030_split_process_headers_v03_review"


def page(native_name):
    html = review_page().replace("UR15_JB_OP010_OP030_split_process_hands_v02_review", VIDEO)
    html = html.replace("UR15_JB_initial_hands_v02.blend", native_name)
    html = html.replace(
        "<title>OP010〜OP030 初期ハンド・動作レビュー</title>", "<title>OP010〜OP030 ヘッダー修正 v03</title>"
    )
    html = html.replace("OP010〜OP030 ハンド・動作レビュー", "OP020 ヘッダー取付・ねじ固定 v03")
    html = html.replace(
        "OP010：XYZ直交3軸・20個収納。単腕と双腕を作業に合わせて配置した初期版です。",
        "OP020をTE公式CADの3口＋2口ヘッダーへ変更。単腕で保持し、設備側の工具でM4ねじを固定します。",
    )
    html = html.replace('data-time="26">0:26', 'data-time="52">0:52')
    html = html.replace('data-time="40">0:40', 'data-time="66">1:06')
    html = html.replace('data-time="54">0:54', 'data-time="80">1:20')
    html = html.replace("0:12 OP020・単腕", "0:12 OP020・ヘッダー取付")
    html = html.replace("video.duration||68", "video.duration||94")
    html = html.replace(
        '<p class="note">', '<p><a href="header_installed.png">ヘッダーの確認画像</a></p><p class="note">', 1
    )
    return html.replace(
        "内部の配置・部品寸法と工具取付部は初期値です。",
        "TE外部ヘッダーは公式CADです。主電源側は写真による外観再現、制御コネクタは仮モデルです。"
        "内部ハウジング・接点の組付けはこのOP020に含みません。工具・指先の取付部は初期値です。",
    )


def package(output, revision, render_folder):
    if output.exists():
        raise FileExistsError(output)
    stem = "header_review_v03_" + revision
    report = json.loads((ROOT / ("audit/" + VIDEO + "_video.json")).read_text())
    build = json.loads((ROOT / ("audit/" + stem + "_build.json")).read_text())
    probe = json.loads((ROOT / ("audit/" + stem + "_probe.json")).read_text())
    native = ROOT / build["native"]
    assert digest(native) == report["native_sha256"] == probe["native_sha256"]
    assert report["generated_mp4_count"] == 1 and not report["generated_raw_mp4"]
    inputs = {
        ROOT / (VIDEO + ".mp4"): Path(VIDEO + ".mp4"),
        native: Path(native.name),
        ROOT / "analysis/header_review_v03.md": Path("README.md"),
        ROOT / ("previews/" + render_folder + "/process_01431.png"): Path("header_installed.png"),
    }
    patterns = [
        "scripts/*header_review_v03.py",
        "scripts/header_review_primitives.py",
        "audit/header_review_v03_primitive_reuse.json",
        "audit/header_review_v03_prepare.json",
        "audit/header_review_v03_reference_files.json",
        "audit/" + stem + "_*.json",
        "audit/" + VIDEO + "_video.json",
        "audit/" + render_folder + "_render.log",
        "data/header_review_v03/*",
        "data/" + stem + "_presentation.json",
        "previews/" + render_folder + "/manifest.json",
        "references/connector_correction_20260915/te_*.pdf",
        "references/connector_correction_20260915/te_*_step.zip",
        "references/connector_correction_20260915/ampere_external.jpg",
    ]
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file():
                inputs[path] = path.relative_to(ROOT)
    output.mkdir(parents=True)
    records = []
    for source, relative in inputs.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        identity = digest(source)
        assert digest(target) == identity
        records.append({"file": str(relative), "sha256": identity, "bytes": target.stat().st_size})
    page_path = output / "review.html"
    page_path.write_text(page(native.name), encoding="utf-8")
    records.append({"file": page_path.name, "sha256": digest(page_path), "bytes": page_path.stat().st_size})
    assert len(list(output.rglob("*.mp4"))) == 1
    manifest = {
        "files": records,
        "mp4_count": 1,
        "native_sha256": digest(native),
        "video_sha256": digest(ROOT / (VIDEO + ".mp4")),
        "physical_validity_verdict": None,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "audit/header_review_v03_delivery.json").write_text(
        json.dumps({"delivery": str(output), **manifest}, ensure_ascii=False, indent=2) + "\n"
    )
    print("HEADER_DELIVERY_COMPLETE", output, len(records), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--revision", default="p03")
    parser.add_argument("--render_folder", default="header_review_final_v03")
    args = parser.parse_args()
    package(args.output_dir, args.revision, args.render_folder)
