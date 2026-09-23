# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Create readable side-by-side group sheets from the saved render images."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
INK = "#233746"


def font(size):
    return ImageFont.truetype(str(FONT), size)


def wrapped(draw, text, x, y, width, size=25, color=INK):
    line = ""
    lines = []
    for char in text:
        if char == "\n" or draw.textlength(line + char, font=font(size)) > width:
            lines.append(line)
            line = "" if char == "\n" else char
        else:
            line += char
    lines.append(line)
    for line in lines:
        draw.text((x, y), line, font=font(size), fill=color)
        y += size * 1.55
    return y


def sheet(group, path):
    canvas = Image.new("RGB", (2000, 1280), "#f4f7f9")
    draw = ImageDraw.Draw(canvas)
    accent = group["display_color"]
    draw.rectangle((0, 0, 2000, 12), fill=accent)
    draw.text((46, 30), "HVJB / 部品群と組立場所", font=font(23), fill="#596c79")
    draw.text((46, 75), group["display_title_ja"], font=font(48), fill=accent)
    draw.text((46, 146), group["display_note_ja"], font=font(26), fill=INK)
    labels = ("完成品の中の位置（着色）", "この部品群だけ（元の相対位置）")
    for index, kind in enumerate(("context", "isolated")):
        x = 46 + index * 984
        draw.rounded_rectangle((x, 208, x + 938, 929), radius=12, fill="white")
        draw.text((x + 18, 221), labels[index], font=font(27), fill=INK)
        source = ROOT / "render_v01/figures" / f"{group['id']}_oblique_{kind}.png"
        image = Image.open(source).convert("RGB")
        image.thumbnail((920, 635), Image.Resampling.LANCZOS)
        canvas.paste(image, (x + (938 - image.width) // 2, 282))
    draw.text((46, 952), f"{group['name_ja']}：写真特徴 {len(group['feature_ids'])} 項目", font=font(28), fill=accent)
    y = wrapped(draw, " / ".join(group["feature_ids"]), 46, 1000, 1870, 24)
    y = wrapped(draw, "未確定：" + group["source_group_unmodified"]["unresolved_ja"], 46, y + 13, 1870, 25)
    assert y < 1160, (group["id"], y)
    draw.line((46, 1170, 1954, 1170), fill="#c9d4da", width=2)
    draw.text(
        (46, 1188),
        "完成写真に対応づけた保存モデル。中間工程の姿勢・加工図・実物の完全BOMを示す図ではありません。",
        font=font(23),
        fill="#596c79",
    )
    draw.text(
        (46, 1228),
        "図の拡大率は左右で異なります。主ヒューズの所属、配線の両端、固定点などの未確定事項を保持。",
        font=font(22),
        fill="#596c79",
    )
    canvas.save(path)


def contacts(files, target):
    for start in range(0, len(files), 4):
        canvas = Image.new("RGB", (1500, 1040), "#e8edf1")
        draw = ImageDraw.Draw(canvas)
        for index, path in enumerate(files[start : start + 4]):
            x, y = (index % 2) * 750, (index // 2) * 520
            image = Image.open(path).convert("RGB")
            image.thumbnail((735, 480), Image.Resampling.LANCZOS)
            canvas.paste(image, (x + 6, y + 6))
            draw.text((x + 8, y + 489), path.name, font=font(16), fill=INK)
        canvas.save(target / f"contact-{start // 4 + 1}.png")


def main():
    data = json.loads((ROOT / "data/group_review.json").read_text())
    output = ROOT / "sheets"
    output.mkdir(exist_ok=False)
    for group in data["groups"]:
        sheet(group, output / (group["id"] + ".png"))
    contact_dir = ROOT / "contacts"
    contact_dir.mkdir(exist_ok=False)
    contacts(sorted(output.glob("*.png")), contact_dir)
    render_contacts = ROOT / "render_contacts"
    render_contacts.mkdir(exist_ok=False)
    contacts(sorted((ROOT / "render_v01/figures").glob("*.png")), render_contacts)
    manifest = {
        "sheet_count": 11,
        "source_render_count": 44,
        "font_sha256": hashlib.sha256(FONT.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "files": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(output.glob("*.png"))
        },
    }
    (ROOT / "sheet_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("GROUP_SHEETS_COMPLETE sheets=11 source_renders=44", flush=True)


if __name__ == "__main__":
    main()
