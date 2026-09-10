# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode complete source-timed frames and separately label a review movie."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 15


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ass_time(value: float) -> str:
    centiseconds = round(value * 100)
    return (
        f"{centiseconds // 360000}:{centiseconds // 6000 % 60:02}:{centiseconds // 100 % 60:02}.{centiseconds % 100:02}"
    )


def encode():
    native_sha = digest(ROOT / "UR15_JB_line_enclosed_v02.blend")
    selected = {}
    for folder in (f"op010_bars_removed_{index}" for index in range(1, 5)):
        manifest = json.loads((ROOT / "audit" / (folder + "_manifest.json")).read_text())
        assert manifest["source_sha256"] == native_sha, folder
        for index, (frame, view) in enumerate(manifest["source_frame_mapping"], 1):
            source = ROOT / "previews" / folder / f"{index:04d}.png"
            assert source.is_file(), f"Missing rendered frame: {source}"
            assert frame not in selected, frame
            selected[frame] = {"source": source, "view": view, "grasp_override": manifest["grasp_camera_override"]}
    assert sorted(selected) == list(range(1, 789, 2))
    sequence = ROOT / "previews/op010_final_sequence"
    sequence.mkdir(exist_ok=True)
    mapping = []
    for index, (frame, record) in enumerate(sorted(selected.items()), 1):
        link = sequence / f"{index:04d}.png"
        if link.is_symlink():
            assert link.resolve() == record["source"].resolve()
        elif link.exists():
            raise RuntimeError(f"Refuse to replace an unrelated sequence file: {link}")
        else:
            link.symlink_to(record["source"])
        mapping.append(
            {
                "output_frame": index,
                "source_frame_30fps": frame,
                "png": str(record["source"].relative_to(ROOT)),
                "png_sha256": digest(record["source"]),
                "view": record["view"],
                "grasp_camera_override": record["grasp_override"],
            }
        )
    # The page poster must show the final carrier and the final render state.
    shutil.copyfile(selected[595]["source"], ROOT / "previews/op010_events/0595.png")
    raw = ROOT / "UR15_OP010_enclosed_raw_v02.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(sequence / "%04d.png"),
            "-frames:v",
            str(len(selected)),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(raw),
        ],
        check=True,
    )
    end_motion = 3 + len(selected) / FPS
    subtitles = ROOT / "data/review_titles.ass"
    style_fields = (
        "Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding"
    )
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 960
PlayResY: 540
WrapStyle: 0

[V4+ Styles]
Format: {style_fields}
Style: Main,Noto Sans CJK JP,21,&H00FFFFFF,&H00FFFFFF,&H901C2D36,&H901C2D36,0,0,0,0,100,100,0,0,3,8,0,2,20,20,14,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    labels = [
        (0, 3, "透明カバー配置・OP010確認版\\N全景のOP020以降は元工程の参考表示"),
        (3, 3 + 264 / 30, "OP010｜筐体を取得  ―  カバー内側から撮影"),
        (3 + 264 / 30, 3 + 438 / 30, "OP010｜パレットへ移送"),
        (3 + 438 / 30, 3 + 700 / 30, "OP010｜治具上へ着座・解放  ―  治具はパレットに先載せ"),
        (3 + 700 / 30, end_motion, "OP010｜退避  ―  工程動作の確認アニメーション"),
        (end_motion, end_motion + 3, "完成品形状の配置案｜JB側を接続・車両側は保護して保持"),
        (end_motion + 3, end_motion + 6, "ラック収納の配置案｜ハーネスを残した6台の完成品"),
    ]
    subtitles.write_text(
        header + "".join(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Main,,0,0,0,,{label}\n" for a, b, label in labels)
    )
    output = ROOT / "UR15_OP010_enclosed_review_v02.mp4"
    commands = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    commands += ["-loop", "1", "-framerate", str(FPS), "-t", "3", "-i", str(ROOT / "previews/enclosure_full_line.png")]
    commands += ["-i", str(raw)]
    for filename in ("02_Line_finished_product.png", "03_Finished_rack.png"):
        commands += ["-loop", "1", "-framerate", str(FPS), "-t", "3", "-i", str(ROOT / "previews" / filename)]
    filters = [
        f"[{index}:v]scale=960:540:force_original_aspect_ratio=decrease,"
        f"pad=960:540:(ow-iw)/2:(oh-ih)/2:color=0xEDF2F4,setsar=1,fps=15,setpts=PTS-STARTPTS[v{index}]"
        for index in range(4)
    ]
    filters += [f"[v0][v1][v2][v3]concat=n=4:v=1:a=0,subtitles=filename='{subtitles}'[review]"]
    commands += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[review]",
        "-frames:v",
        str(len(selected) + 135),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(commands, check=True)
    report = {
        "native_sha256": native_sha,
        "source_fps": 30,
        "output_fps": FPS,
        "native_frame_count": 788,
        "raw_frame_count": len(selected),
        "raw_duration_s": len(selected) / FPS,
        "review_frame_count": len(selected) + 135,
        "review_duration_s": (len(selected) + 135) / FPS,
        "raw_video_sha256": digest(raw),
        "review_video_sha256": digest(output),
        "source_frame_mapping": mapping,
        "scope": "OP010 motion and static design views; downstream motion is retained source reference",
        "formal_physical_validity_verdict": None,
    }
    (ROOT / "audit/video_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("REVIEW_MOVIE_ENCODED", output, report["review_duration_s"], flush=True)


if __name__ == "__main__":
    encode()
