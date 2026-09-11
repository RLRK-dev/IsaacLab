# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encode process PNGs directly into one labelled review MP4, without a raw MP4."""

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

from encode_op030_v02 import captions_write, render_log_read, run
from encode_review_video import digest

ROOT = Path(__file__).resolve().parents[1]


def collect_frames(folders: list[str], plan_path: Path) -> tuple[dict, dict, list[dict], dict]:
    """Verify native-to-PNG mapping and the saved process camera at every sample."""
    plan = json.loads(plan_path.read_text())
    native_sha = digest(ROOT / plan["native"])
    assert plan["native_sha256"] == native_sha
    assert plan["motion_sha256"] == digest(ROOT / "data" / plan["motion"])
    records, manifests, settings = {}, [], None
    for name in folders:
        if Path(name).name != name:
            raise ValueError("Each render folder must be one relative directory name")
        folder = ROOT / "previews" / name
        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        log, complete, overflow = render_log_read(ROOT / "audit" / (name + "_render.log"))
        assert complete and not overflow and manifest["complete"]
        assert manifest["native_sha256"] == native_sha and manifest["native_frame_end"] == plan["frame_end"]
        assert manifest["output_fps"] == 15 and manifest["shot_plan_sha256"] == digest(plan_path)
        assert manifest["renderer_sha256"] == digest(ROOT / "scripts/render_op030_v02.py")
        settings = manifest["settings"] if settings is None else settings
        assert settings == manifest["settings"]
        manifests.append(
            dict(
                path=str(manifest_path.relative_to(ROOT)),
                sha256=digest(manifest_path),
                render_log=str(log.relative_to(ROOT)),
                render_log_sha256=digest(log),
            )
        )
        for row in manifest["images"]:
            assert row["view"] == "process" and row["frame"] not in records
            expected = next(
                shot["camera"] for shot in plan["ranges"] if shot["first_frame"] <= row["frame"] <= shot["last_frame"]
            )
            assert row["camera"] == expected and digest(folder / row["file"]) == row["sha256"]
            records[row["frame"]] = dict(row, png=folder / row["file"])
    assert sorted(records) == list(range(1, plan["frame_end"] + 1, 2))
    return plan, records, manifests, settings


def encode(plan_path: Path, folders: list[str], basename: str) -> Path:
    """Create one reviewed MP4 with complete decode validation [s]."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+_split_process_[A-Za-z0-9_-]+_review", basename):
        raise ValueError("Expected a *_split_process_*_review basename without an extension")
    output = ROOT / (basename + ".mp4")
    captions = ROOT / "data" / (basename + ".ass")
    report_path = ROOT / "audit" / (basename + "_video.json")
    if any(path.exists() for path in (output, captions, report_path)):
        raise FileExistsError("Keep existing videos and observations unchanged; choose a new version")
    plan, records, manifests, settings = collect_frames(folders, plan_path)
    mapping = [
        dict(native_frame=frame, camera=row["camera"], png_sha256=row["sha256"])
        for frame, row in sorted(records.items())
    ]
    duration = len(mapping) / 15
    captions_write(captions, plan, duration)
    with tempfile.TemporaryDirectory(prefix="process_review_", dir=ROOT / "previews") as temporary:
        sequence = Path(temporary)
        for index, row in enumerate((row for _, row in sorted(records.items())), 1):
            (sequence / f"{index:05d}.png").symlink_to(row["png"].resolve())
        pending = sequence / output.name
        # Subtitle compositing happens while reading PNGs; no raw-video intermediate is created.
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                "15",
                "-i",
                str(sequence / "%05d.png"),
                "-frames:v",
                str(len(mapping)),
                "-vf",
                f"subtitles=filename='{captions}'",
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
                str(pending),
            ]
        )
        metadata = json.loads(
            run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-count_frames",
                    "-show_streams",
                    "-show_format",
                    "-of",
                    "json",
                    str(pending),
                ]
            ).stdout
        )
        stream = next(item for item in metadata["streams"] if item["codec_type"] == "video")
        assert int(stream["nb_read_frames"]) == len(mapping) and stream["r_frame_rate"] == "15/1"
        assert (stream["width"], stream["height"]) == (settings["width"], settings["height"])
        assert abs(float(metadata["format"]["duration"]) - duration) < 0.02
        decoded = run(
            [
                "ffmpeg",
                "-hide_banner",
                "-xerror",
                "-threads",
                "2",
                "-i",
                str(pending),
                "-vf",
                "blackdetect=d=0.05:pic_th=0.995:pix_th=0.02",
                "-f",
                "null",
                "-",
            ]
        )
        black = [line for line in decoded.stderr.splitlines() if "black_start:" in line]
        assert not black, black
        if output.exists():
            raise FileExistsError(output)
        shutil.move(pending, output)
    metadata["format"]["filename"] = str(output)
    report = dict(
        native_sha256=plan["native_sha256"],
        motion_sha256=plan["motion_sha256"],
        presentation_sha256=digest(plan_path),
        encoder_sha256=digest(Path(__file__)),
        frame_count=len(mapping),
        duration_s=duration,
        mapping=mapping,
        videos={
            output.name: dict(
                sha256=digest(output), metadata=metadata, full_decode_exit_code=0, full_black_intervals=[]
            )
        },
        source_manifests=manifests,
        render_settings=settings,
        generated_mp4_count=1,
        generated_raw_mp4=False,
        generated_wide_video=False,
        formal_physical_validity_verdict=None,
    )
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PROCESS_REVIEW_ONLY_ENCODED", output.name, len(mapping), duration, flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folders", nargs="+", required=True)
    parser.add_argument("--plan", required=True, help="Saved process shot plan filename under data/")
    parser.add_argument("--basename", required=True, help="Versioned *_split_process_*_review output stem")
    options = parser.parse_args()
    if Path(options.plan).name != options.plan:
        raise ValueError("The shot plan must be one filename under data/")
    encode(ROOT / "data" / options.plan, options.folders, options.basename)


if __name__ == "__main__":
    main()
