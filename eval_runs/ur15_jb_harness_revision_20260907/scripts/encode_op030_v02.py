# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode a complete OP030 render with separate raw and captioned files [s]."""

import argparse
import gzip
import json
import subprocess
from pathlib import Path

from encode_review_video import ass_time, digest

ROOT = Path(__file__).resolve().parent.parent


def run(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def render_log_read(path: Path) -> tuple[Path, bool, bool]:
    """Return the log path and completion/overflow flags from a text stream.

    Prefer an existing plain log. If it is absent, read its gzip counterpart,
    including concatenated members, without holding the expanded log in RAM.
    """
    if not path.is_file() and path.suffix != ".gz":
        path = path.with_suffix(path.suffix + ".gz")
    opener = gzip.open if path.suffix == ".gz" else open
    complete, overflow = False, False
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            complete |= "OP030_RENDER_COMPLETE" in line
            overflow |= "Shadow buffer full" in line
    return path, complete, overflow


def captions_write(path, plan, duration):
    fields = (
        "Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding"
    )
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: {fields}
Style: Main,Noto Sans CJK JP,22,&H00FFFFFF,&H00FFFFFF,&H901C2D36,&H901C2D36,0,0,0,0,100,100,0,0,3,6,0,2,22,22,18,1
Style: Scope,Noto Sans CJK JP,17,&H00FFFFFF,&H00FFFFFF,&H901C2D36,&H901C2D36,0,0,0,0,100,100,0,0,3,4,0,8,12,12,12,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    scope_caption = plan.get("scope_caption", "EV用ジャンクションボックス｜OP030 端子支持部・内部配線｜動作検討モデル")
    labels = [(0, duration, "Scope", scope_caption)]
    for p in plan["phases"]:
        stop = duration if p is plan["phases"][-1] else p["stop_s"]
        labels.append((p["start_s"], stop, "Main", plan.get("phase_prefix", "OP030｜") + p["label"]))
    path.write_text(
        header
        + "".join(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},{style},,0,0,0,,{label}\n" for a, b, style, label in labels)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folders", nargs="+", required=True)
    parser.add_argument("--view", choices=("process", "wide"), required=True)
    parser.add_argument("--plan", default="op030_presentation_v02.json")
    parser.add_argument("--basename", help="Optional output stem for a separately versioned motion bank")
    args = parser.parse_args()
    plan_path = ROOT / "data" / args.plan
    plan = json.loads(plan_path.read_text())
    native_sha = digest(ROOT / plan["native"])
    assert plan["native_sha256"] == native_sha
    assert plan["motion_sha256"] == digest(ROOT / "data" / plan["motion"])
    records, manifests, settings = {}, [], None
    for folder in args.folders:
        directory = ROOT / "previews" / folder
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        log_path, complete, overflow = render_log_read(ROOT / "audit" / (folder + "_render.log"))
        assert complete and not overflow
        assert manifest["native_sha256"] == native_sha and manifest["complete"]
        assert manifest["native_frame_end"] == plan["frame_end"] and manifest["output_fps"] == 15
        if args.view == "process":
            assert manifest["shot_plan_sha256"] == digest(plan_path)
        assert manifest["renderer_sha256"] == digest(ROOT / "scripts/render_op030_v02.py")
        if settings is None:
            settings = manifest["settings"]
        assert settings == manifest["settings"]
        manifests.append(
            dict(
                path=str(manifest_path.relative_to(ROOT)),
                sha256=digest(manifest_path),
                render_log=str(log_path.relative_to(ROOT)),
                render_log_sha256=digest(log_path),
            )
        )
        for row in manifest["images"]:
            assert row["view"] == args.view and row["frame"] not in records
            png = directory / row["file"]
            assert digest(png) == row["sha256"]
            if args.view == "process":
                expected = next(
                    p["camera"] for p in plan["ranges"] if p["first_frame"] <= row["frame"] <= p["last_frame"]
                )
                assert row["camera"] == expected
            records[row["frame"]] = dict(row, png=png)
    assert sorted(records) == list(range(1, plan["frame_end"] + 1, 2)), "Incomplete native timeline"
    basename = args.basename or "UR15_JB_OP030_" + args.view + "_v02"
    if Path(basename).name != basename:
        raise ValueError("The output basename must be one filename stem")
    sequence = ROOT / "previews" / (basename + "_sequence")
    sequence.mkdir(exist_ok=True)
    mapping = []
    for number, (frame, row) in enumerate(sorted(records.items()), 1):
        link = sequence / f"{number:05d}.png"
        if link.exists():
            assert link.is_symlink() and link.resolve() == row["png"].resolve()
        else:
            link.symlink_to(row["png"])
        mapping.append(dict(native_frame=frame, camera=row["camera"], png_sha256=row["sha256"]))
    raw, review = ROOT / (basename + "_raw.mp4"), ROOT / (basename + "_review.mp4")
    common = [
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        "4",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
    ]
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            "15",
            "-i",
            str(sequence / "%05d.png"),
            "-frames:v",
            str(len(mapping)),
            *common,
            str(raw),
        ]
    )
    duration = len(mapping) / 15
    captions = ROOT / "data" / (basename + ".ass")
    captions_write(captions, plan, duration)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(raw),
            "-vf",
            f"subtitles=filename='{captions}'",
            *common,
            str(review),
        ]
    )
    videos = {}
    for video in (raw, review):
        metadata = json.loads(
            run(
                ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(video)]
            ).stdout
        )
        stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
        assert int(stream["nb_read_frames"]) == len(mapping) and stream["r_frame_rate"] == "15/1"
        assert stream["width"] == settings["width"] and stream["height"] == settings["height"]
        assert abs(float(metadata["format"]["duration"]) - duration) < 0.02
        decoded = run(
            [
                "ffmpeg",
                "-hide_banner",
                "-xerror",
                "-threads",
                "2",
                "-i",
                str(video),
                "-vf",
                "blackdetect=d=0.05:pic_th=0.995:pix_th=0.02",
                "-f",
                "null",
                "-",
            ]
        )
        black = [line for line in decoded.stderr.splitlines() if "black_start:" in line]
        assert not black, black
        videos[video.name] = dict(
            sha256=digest(video), metadata=metadata, full_decode_exit_code=0, full_black_intervals=black
        )
    result = dict(
        native_sha256=native_sha,
        motion_sha256=plan["motion_sha256"],
        presentation_sha256=digest(plan_path),
        frame_count=len(mapping),
        duration_s=duration,
        videos=videos,
        mapping=mapping,
        source_manifests=manifests,
        render_settings=settings,
        formal_physical_validity_verdict=None,
        scope="One complete OP030 assembly, every second native frame; no force, electrical or cycle-time verdict",
    )
    (ROOT / "audit" / (basename + "_video.json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("OP030_VIDEO_ENCODED", basename, len(mapping), duration, flush=True)


if __name__ == "__main__":
    main()
