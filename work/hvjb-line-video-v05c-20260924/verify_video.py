# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Read the encoded composition and extract each scene, local phase and chapter boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
STEM = "HVJB_line_split_process_concept_v05c_review"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_samples(plan: dict) -> list[int]:
    times = [row["start_s"] + 0.62 * (row["stop_s"] - row["start_s"]) for row in plan["scenes"]]
    times += [3.6, 4.2]
    for start in (119, 129):
        times += [start + offset for offset in (0.5, 2.7, 5, 7.2, 9.5)]
    for start in (139, 147):
        times += [start + offset for offset in (0.7, 2.5, 4.8, 7.3)]
    indices = {int(time * 15) for time in times}
    for chapter in plan["chapters"][1:]:
        boundary = round(chapter["start_s"] * 15)
        indices.update((boundary - 1, boundary))
    indices.add(2327)
    return sorted(indices)


def contacts(rows: list[dict]) -> list[dict]:
    output = ROOT / "decoded_contacts"
    output.mkdir()
    font = ImageFont.truetype(FONT, 21)
    result = []
    for start in range(0, len(rows), 6):
        sheet = Image.new("RGB", (1920, 1176), "#F2F6F8")
        draw = ImageDraw.Draw(sheet)
        for tile, row in enumerate(rows[start : start + 6]):
            x, y = tile % 3 * 640, tile // 3 * 588
            draw.text(
                (x + 10, y + 12),
                f"{row['chapter']} / {row['feature_id']} / {row['video_s']:.3f} s",
                font=font,
                fill="#173B4D",
            )
            with Image.open(ROOT / row["decoded_png"]) as image:
                sheet.paste(image.resize((640, 360), Image.Resampling.LANCZOS), (x, y + 49))
            draw.text((x + 10, y + 425), f"source frame: {row['source_saved_frame']}", font=font, fill="#526C78")
            draw.text((x + 10, y + 461), row["display_kind"], font=font, fill="#526C78")
        file = output / f"contact-{start // 6 + 1:02d}.png"
        sheet.save(file)
        result.append({"path": str(file.relative_to(ROOT)), "sha256": sha(file)})
    return result


def main() -> None:
    report_path, images_path = ROOT / "audit/video_readback.json", ROOT / "decoded_stills"
    assert not report_path.exists() and not images_path.exists()
    plan = json.loads((ROOT / "data/concept_v05c.json").read_text())
    manifest = json.loads((ROOT / "previews/concept_v05c/manifest.json").read_text())
    encoded = json.loads((ROOT / "audit" / f"{STEM}_video.json").read_text())
    movie = ROOT / f"{STEM}.mp4"
    record = encoded["videos"][movie.name]
    assert sha(movie) == record["sha256"]
    assert encoded["frame_count"] == len(manifest["images"]) == 2328 and encoded["duration_s"] == 155.2
    assert (
        encoded["generated_mp4_count"] == 1 and not encoded["generated_raw_mp4"] and not encoded["generated_wide_video"]
    )
    assert record["full_decode_exit_code"] == 0 and not record["full_black_intervals"]
    assert manifest["complete"] and len(set(plan["tasks_preserved"])) == 20
    assert encoded["presentation_sha256"] == sha(ROOT / "data/concept_v05c.json")
    assert manifest["renderer_sha256"] == sha(ROOT / "assemble_frames.py")
    counts = Counter(row["chapter"] for row in manifest["images"])
    assert counts == {"MAIN": 1785, "H06_loading": 150, "H06_pickup": 150, "H05_P16": 120, "H05_P17": 123}
    for chapter in plan["chapters"]:
        first, last = round(chapter["start_s"] * 15), round(chapter["stop_s"] * 15)
        assert {row["chapter"] for row in manifest["images"][first:last]} == {chapter["id"]}
    indices = selected_samples(plan)
    expression = "+".join(f"eq(n\\,{index})" for index in indices)
    images_path.mkdir()
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(movie),
        "-vf",
        "select=" + expression,
        "-fps_mode",
        "vfr",
        "-frames:v",
        str(len(indices)),
        str(images_path / "frame-%02d.png"),
    ]
    decoded = subprocess.run(command, check=True, capture_output=True, text=True)
    assert len(list(images_path.glob("frame-*.png"))) == len(indices)
    rows = []
    for number, index in enumerate(indices, 1):
        row = manifest["images"][index]
        file = images_path / f"frame-{number:02d}.png"
        source = ROOT / "previews/concept_v05c" / row["file"]
        assert sha(source) == row["sha256"]
        original = np.asarray(Image.open(source).convert("RGB"), dtype=np.int16)
        result = np.asarray(Image.open(file).convert("RGB"), dtype=np.int16)
        assert original.shape == result.shape == (1080, 1920, 3)
        rows.append(
            {
                "chapter": row["chapter"],
                "feature_id": row["feature_id"],
                "video_sample_index": index,
                "video_s": index / 15,
                "source_saved_frame": row["saved_frame"],
                "display_kind": row["display_kind"],
                "decoded_png": str(file.relative_to(ROOT)),
                "decoded_png_sha256": sha(file),
                "source_png_sha256": sha(source),
                "mean_absolute_rgb_difference": float(abs(original - result).mean()),
            }
        )
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "video_sha256": sha(movie),
        "frame_count": 2328,
        "fps": 15,
        "duration_s": 155.2,
        "size_px": [1920, 1080],
        "chapter_counts": dict(counts),
        "jobs_retained": plan["tasks_preserved"],
        "full_decode_exit_code": 0,
        "full_black_intervals": [],
        "sample_extraction_command": command,
        "sample_extraction_stderr": decoded.stderr,
        "samples": rows,
        "contacts": contacts(rows),
        "visual_inspection_recorded_separately": True,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"V05C_VIDEO_READBACK frames=2328 seconds=155.2 samples={len(indices)} chapters=5 jobs=20", flush=True)


if __name__ == "__main__":
    main()
