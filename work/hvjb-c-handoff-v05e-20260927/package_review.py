# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package one review movie and visible stills, leaving all previous deliveries untouched."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from build_motion import ROOT, sha, write
from PIL import Image, ImageDraw, ImageFont

MOVIE = "HVJB_line_split_process_concept_v05e_review.mp4"


def copy(source: Path, target: Path) -> None:
    assert not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert sha(source) == sha(target)


def figures(output: Path) -> list[dict]:
    detail = json.loads((ROOT / "previews/detail/manifest.json").read_text())
    selected = []
    for step in range(12):
        rows = [row for row in detail["images"] if row["step"] == step]
        row = rows[len(rows) // 2]
        source = ROOT / "previews/detail" / row["file"]
        assert sha(source) == row["sha256"]
        copy(source, output / "figures" / f"{step + 1:02d}.png")
        selected.append(row)
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 23)
    for page, filename in enumerate(("01_C工程_受渡しと持ち替え.jpg", "02_C工程_把持と筐体搭載.jpg")):
        sheet = Image.new("RGB", (1920, 1770), "#E9F0F4")
        draw = ImageDraw.Draw(sheet)
        for cell, row in enumerate(selected[page * 6 : page * 6 + 6]):
            x, y = cell % 2 * 960, cell // 2 * 590
            frame = Image.open(output / "figures" / f"{row['step'] + 1:02d}.png")
            sheet.paste(frame.resize((960, 540), Image.Resampling.LANCZOS), (x, y))
            draw.text(
                (x + 18, y + 551),
                f"C工程 {row['step'] + 1:02d} / 主工程 {row['source_index'] / 15:.2f} 秒",
                fill="#173B4D",
                font=font,
            )
        sheet.save(output / filename, quality=92)
    return selected


def main() -> None:
    output = ROOT / "delivery"
    assert not output.exists()
    report = json.loads((ROOT / "audit" / (MOVIE.removesuffix(".mp4") + "_video.json")).read_text())
    assert report["generated_mp4_count"] == 1 and not report["generated_raw_mp4"]
    assert not report["generated_wide_video"]
    assert sha(ROOT / MOVIE) == report["videos"][MOVIE]["sha256"]
    output.mkdir()
    copy(ROOT / MOVIE, output / MOVIE)
    selected = figures(output)
    bundle = json.loads((ROOT / "data/video_source_bundle.json").read_text())
    buttons = []
    for row in bundle["C_detail_steps"]:
        seconds = row["start_s"]
        label = html.escape(row["label_ja"])
        buttons.append(
            f'<button data-seek="{seconds}"><span>{row["step"]:02d} / '
            f"{int(seconds) // 60}:{int(seconds) % 60:02d}</span>{label}</button>"
        )
    template = (ROOT / "review_template.html").read_text()
    assert template.count("__STEP_BUTTONS__") == 1
    (output / "index.html").write_text(template.replace("__STEP_BUTTONS__", "\n".join(buttons)))
    for name in ("README.md", "SCOPE.md", "RETRY_DELTA.md"):
        copy(ROOT / name, output / name)
    for source in (ROOT / "audit").glob("*.json"):
        copy(source, output / "audit" / source.name)
    for name in ("concept_v05e.npz", "concept_v05e.json", "video_source_bundle.json"):
        copy(ROOT / "data" / name, output / "data" / name)
    for source in ROOT.glob("*.py"):
        copy(source, output / "scripts" / source.name)
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    for source in ROOT.glob("*.log"):
        # Preserve raw logs in the task folder; these text copies only remove terminal control codes.
        clean = re.sub(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|[@-_])", "", source.read_text()).replace("\r", "")
        target = logs / (source.stem + ".txt")
        assert not target.exists()
        target.write_text("\n".join(line.rstrip() for line in clean.splitlines()).strip() + "\n")
        copy(target, output / "logs" / target.name)
    write(ROOT / "audit/selected_figures.json", {"selected_source_frames": selected})
    copy(ROOT / "audit/selected_figures.json", output / "audit/selected_figures.json")
    files = [
        {"path": str(path.relative_to(output)), "sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(output.rglob("*"))
        if path.is_file()
    ]
    write(output / "manifest.json", {"files": files, "mp4_count": 1, "physical_acceptance_verdict": None})
    print(f"C_REVIEW_PACKAGED files={len(files)} mp4=1 frames=3138 duration=209.2", flush=True)


if __name__ == "__main__":
    main()
