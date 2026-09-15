# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Index public Ampere videos and extract unaltered evidence frames [s]."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "references/hvjb_assembly_followup_20260915"
OUTPUT = ROOT / "data/hvjb_video_evidence_v02.json"


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    sources, frames = {}, {}
    for name, identifier, date in (
        ("assembly_20250607", "Sm_D-vmNYqc", "20250607"),
        ("explanation_20240201", "oXPIRNZ4xcs", "20240201"),
    ):
        path = REFERENCE / (name + ".mp4")
        info_path = REFERENCE / (name + ".info.json")
        info = json.loads(info_path.read_text())
        assert info["id"] == identifier and info["upload_date"] == date
        assert info["channel_id"] == "UCCix5q2N5Oykrvzke4WS17Q"
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        stream = json.loads(probe.stdout)["streams"][0]
        sources[name] = {
            "title": info["title"],
            "url": info["webpage_url"],
            "channel": info["channel"],
            "upload_date": date,
            "file": str(path.relative_to(ROOT)),
            "sha256": digest(path),
            "metadata_sha256": digest(info_path),
            "size_px": [stream["width"], stream["height"]],
            "duration_s": float(stream["duration"]),
            "frame_rate": stream["avg_frame_rate"],
            "automatic_caption_role": "navigation aid only; not a verified transcription or part-number source",
        }
    for identifier, name, seconds, label in (
        ("fuse_detail", "assembly_20250607", 35, "挿入写真：後方の補機ヒューズ5個"),
        ("main_pointer", "explanation_20240201", 68, "指定写真上の主ヒューズ付近を指す公式解説"),
        ("main_sample", "explanation_20240201", 72, "主ヒューズ説明時の円筒胴・両端平板端子"),
        ("subassembly", "assembly_20250607", 24, "2025年の組立例：抵抗と接触器の下板"),
        ("panel_wiring", "assembly_20250607", 50, "2025年の組立例：箱外でヒューズ板へ配線"),
        ("insert_plate", "assembly_20250607", 145, "2025年の組立例：内部サブアセンブリを箱へ挿入"),
        ("crimp", "assembly_20250607", 103, "2025年の組立例：配線端末の準備"),
        ("busbars", "assembly_20250607", 237, "2025年の組立例：別体バスバーを後から取り付け"),
    ):
        target = REFERENCE / (identifier + ".png")
        if target.exists():
            raise FileExistsError(target)
        command = [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(seconds),
            "-i",
            str(REFERENCE / (name + ".mp4")),
            "-frames:v",
            "1",
            str(target),
        ]
        subprocess.run(command, check=True)
        frames[identifier] = {
            "file": str(target.relative_to(ROOT)),
            "sha256": digest(target),
            "source": name,
            "requested_seek_s": seconds,
            "timestamp_basis": "ffmpeg accurate seek; first decoded display frame at/after requested time",
            "size_px": sources[name]["size_px"],
            "label_ja": label,
            "pixel_transform": "none; decoded full frame, no crop or generative edit",
        }
    data = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "sources": sources,
        "frames": frames,
        "revision_boundary_ja": (
            "挿入写真は指定写真の接触器・中央被覆・バスバー・補機板と外観を照合。"
            "2025年の実作業映像は同一製造版との確認がなく、抵抗配置・配線経路を旧写真へ転記しない。"
        ),
        "source_video_delivery": False,
        "new_process_movie_created": False,
        "formal_physical_verdict": None,
    }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("VIDEO_EVIDENCE_INDEXED", len(sources), len(frames), digest(OUTPUT), flush=True)


if __name__ == "__main__":
    main()
