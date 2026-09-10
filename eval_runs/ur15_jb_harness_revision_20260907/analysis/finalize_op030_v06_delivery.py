# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Finish the v06 document and delivery only after both actual encoders finish."""

import argparse
import hashlib
import json
import runpy
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
NATIVE_SHA = "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"
DOCUMENT = ROOT / "OP030_三ST工程・部品確認書_v06.md"
DRAFT_SHA = "20877104a155f6da48c77b226825de7563216e9e77999aa68561eafa5cc4003f"
PACKAGE = "UR15_JB_OP030_20260910_v06"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one frozen document passage: {before[:100]}")
    return text.replace(before, after, 1)


def finalize_document(videos: dict) -> None:
    """Insert actual video observations without changing the mechanical evidence."""
    if digest(DOCUMENT) != DRAFT_SHA:
        raise ValueError("The camera-final draft changed before its video update")
    backup = ROOT / "analysis/op030_v06_document_before_encode.md"
    if backup.exists():
        raise FileExistsError(backup)
    text = DOCUMENT.read_text()
    measured = videos["measured_duration_s"]
    if len(set(measured.values())) != 1:
        raise ValueError("The four actual video durations differ")
    duration = next(iter(measured.values()))
    observed = datetime.now().astimezone().isoformat()
    text = replace_once(
        text,
        "# OP030の3ST分割：工程・部品確認書 v06（カメラ確定版・動画未生成）",
        "# OP030の3ST分割：工程・部品確認書 v06（千鳥配置・動画生成版）\n\n"
        f"動画記録の確認時刻: {observed}。根拠: 保存ファイルとエンコーダの全編デコード記録。",
    )
    text = replace_once(
        text,
        "全動画は未生成である。",
        f"工程映像と固定全景、それぞれの説明付き／説明なしの計4動画を生成し、"
        f"各7,031フレーム・15 fps・実測{duration:.3f}秒と全編デコード正常を確認した。",
    )
    text = replace_once(
        text,
        "| 4動画 | 全動画は未生成。各7,031サンプル／15 fps／468.733333秒は予定値 | "
        "全デコード・実測時間・動画SHA・ブラウザー確認を生成後に追記 |",
        f"| 4動画 | 各7,031フレーム／15 fps／実測{duration:.3f}秒。全編デコード終了0、全画面黒区間なし。"
        "工程1280×720／全景960×540 | `audit/UR15_JB_OP030_split_process_v06_video.json`、"
        "`audit/UR15_JB_OP030_split_wide_v06_video.json` |",
    )
    text = replace_once(
        text,
        "保存nativeの30 fpsは先頭フレーム1から末尾14062まで468.7秒である。"
        "動画はフレーム1,3,…,14061の7,031サンプルを15 fpsで出力する予定なので、"
        "符号化後の計算上の時間は468.733333秒となる。動画の実測時間・全デコード結果・SHAはまだない。"
        "静止画の確認やnative保存の成功を動画完成の根拠にはしない。",
        "保存nativeの30 fpsは先頭フレーム1から末尾14062まで468.7秒である。"
        "動画はフレーム1,3,…,14061の7,031サンプルを15 fpsで符号化した。"
        f"サンプル数からの計算値は468.733333秒、4ファイルのFFprobe実測は各{duration:.3f}秒。"
        "すべてのフレームをデコードし、説明あり・なしの双方で検査を完了した。"
        "動画の検査結果は元nativeと全PNGの対応を含むエンコーダ記録、および実ファイルSHAで固定する。",
    )
    table = [
        "## 動画ファイルの照合",
        "",
        "工程／固定全景の各映像に、説明付き版と説明なし版を用意した。4本とも同じ時系列を収録する。",
        "",
        "| 動画ファイル | 画素数 | 実測秒 | SHA256 |",
        "| --- | --- | --- | --- |",
    ]
    for name, record in videos["videos"].items():
        table.append(
            f"| [{name}]({name}) | {record['width']}×{record['height']} | "
            f"{record['duration_s']:.3f} | `{record['sha256']}` |"
        )
    table.extend(["", "| エンコーダ記録 | SHA256 |", "| --- | --- |"])
    for record in videos["reports"].values():
        table.append(f"| `{record['path']}` | `{record['sha256']}` |")
    table.extend(
        [
            "",
            "この確認書と動画を固定した後、確認ページの再生・全160章への移動・相対リンクを検査し、"
            "配布フォルダーとZIPの全ファイルSHAを照合する。結果は別の納品記録に残す。"
            "動画のデコード正常を、実機での物理成立や正式審査の完了とは扱わない。",
            "",
        ]
    )
    text = replace_once(
        text,
        "動画を生成した後に、実測時間・全デコード・動画SHA・ブラウザー配布確認の結果を追記する。"
        "補助幾何確認・native保存・隔離再ベイクの完了を、v06の全動画・配布確認の完了へ拡大しない。",
        "\n".join(table),
    )
    shutil.copy2(DOCUMENT, backup)
    temporary = DOCUMENT.with_suffix(".md.tmp")
    temporary.write_text(text)
    temporary.replace(DOCUMENT)
    print("OP030_V06_DOCUMENT_VIDEO_RECORDS_WRITTEN", digest(DOCUMENT), flush=True)


def execute(script: str, arguments: list[str], log_name: str, marker: str) -> None:
    """Use the existing wrapper, requiring a real completion marker as well as exit status."""
    log = ROOT / "audit" / log_name
    command = [str(REPO / "isaaclab.sh"), "-p", str(ROOT / script), *arguments]
    print("DELIVERY_STEP_START", script, flush=True)
    with log.open("x") as stream:
        result = subprocess.run(command, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode or marker not in log.read_text():
        raise RuntimeError(f"Delivery step failed; inspect {log}")
    print("DELIVERY_STEP_COMPLETE", script, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native_sha256", required=True)
    parser.add_argument("--wait", action="store_true")
    options = parser.parse_args()
    if options.native_sha256 != NATIVE_SHA or digest(ROOT / "UR15_JB_OP030_split_v06.blend") != NATIVE_SHA:
        raise ValueError("Expected the explicitly pinned final native")
    encoder_log = ROOT / "audit/op030_split_encode_orchestrator_v06.log"
    while "SPLIT_BOTH_VIDEOS_ENCODED_V06" not in encoder_log.read_text():
        if (ROOT / "analysis/STOP_split_delivery_v06").exists():
            raise SystemExit("Cooperative delivery stop requested")
        if not options.wait:
            raise FileNotFoundError("Both final video encoders must complete first")
        time.sleep(15)
    helpers = runpy.run_path(str(ROOT / "analysis/prepare_op030_v06_document_evidence.py"))
    plan = read(ROOT / "data/op030_split_shots_v06.json")
    videos = helpers["video_records"](
        NATIVE_SHA,
        plan["motion_sha256"],
        digest(ROOT / "data/op030_split_shots_v06.json"),
        True,
    )
    helpers["render_source_records"](NATIVE_SHA, True)
    execute(
        "analysis/finalize_render_cache_v06.py",
        ["--native_sha256", NATIVE_SHA],
        "op030_v06_cache_finalize.log",
        "OP030_V06_RENDER_CACHE_FINALIZED",
    )
    finalize_document(videos)
    execute(
        "analysis/prepare_op030_v06_document_evidence.py",
        ["--require_videos"],
        "op030_v06_final_evidence.log",
        "V06_DOCUMENT_EVIDENCE_PREPARED",
    )
    selection = read(ROOT / "analysis/op030_v06_package_evidence.json")
    assert not selection["document"]["draft"] and selection["native_sha256"] == NATIVE_SHA
    execute(
        "scripts/package_op030_split_v06.py",
        ["--stage", "--evidence", *selection["evidence_paths"], "analysis/op030_v06_package_evidence.json"],
        "op030_v06_package_stage.log",
        '"stage_written": true',
    )
    execute(
        "scripts/verify_op030_delivery_v06.py",
        [],
        "op030_v06_browser_delivery.log",
        '"checks_succeeded": true',
    )
    execute(
        "scripts/deliver_op030_split_v06.py",
        ["--native_sha256", NATIVE_SHA],
        "op030_v06_downloads_delivery.log",
        "OP030_SPLIT_DELIVERY_V06_COMPLETE",
    )
    report = read(ROOT / "audit/op030_split_delivery_v06.json")
    assert report["native_sha256"] == NATIVE_SHA and all(report["checks"].values())
    assert all(row["matches_prior"] for row in report["previous_delivery_observation"].values())
    print("OP030_V06_DELIVERY_PIPELINE_COMPLETE", report["archive"], report["archive_sha256"], flush=True)


if __name__ == "__main__":
    main()
