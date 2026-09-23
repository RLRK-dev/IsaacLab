# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare saved panel-hand display states with the same camera in each pair."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import probe_panel as probe
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(probe.PREVIOUS))
spec = importlib.util.spec_from_file_location("prior_comparison_renderer", probe.PREVIOUS / "render_comparisons.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)

CASES = [
    ("B_first", 315, ["B"], ["b_unit"], "B：先行のヒューズ板"),
    ("B_next", 825, ["B"], ["b_next"], "B：次のヒューズ板"),
    ("C_approach", 637, ["B", "C主"], ["b_unit"], "BからC：受取り接近"),
    ("BC_transfer", 650, ["B", "C主"], ["b_unit"], "BからC：両側で保持する表示"),
    ("C_panel", 690, ["C主"], ["b_unit"], "C：板の位置合わせ"),
    ("C_regrip", 757, ["C主"], ["b_unit", "a_unit"], "C：一式の搬送へ手先を切替え"),
]


def main():
    output = probe.ROOT / "comparisons"
    assert not output.exists()
    delta = json.loads((probe.ROOT / "audit/panel_display_delta.json").read_text())
    new = probe.ROOT / delta["output_bank"]
    assert probe.sha(new) == delta["output_sha256"]
    assert probe.sha(probe.BANK) == delta["input_sha256"][str(probe.BANK)]
    with np.load(probe.BANK, allow_pickle=False) as saved:
        before, times = saved["matrices"], saved["time_s"]
    with np.load(new, allow_pickle=False) as saved:
        after = saved["matrices"]
    model = probe.fix.old.Model()
    renderer = probe.fix.old.base.pyrender.OffscreenRenderer(*compare.SIZE)
    fonts = {size: ImageFont.truetype(probe.fix.old.base.FONT, size) for size in (23, 26, 34)}
    rows = []
    output.mkdir()
    try:
        for key, index, roles, groups, title in CASES:
            names = {
                role + suffix for role in roles for suffix in ("_palm", "_left_finger", "_right_finger", "_carrier")
            }
            parts = {model.dynamic.index(node) for group in groups for node, _ in getattr(model, group)}
            columns = [i for i, name in enumerate(model.names) if i in parts or name in names]
            pictures, camera = compare.render_pair(model, renderer, columns, [before[index], after[index]])
            image = Image.new("RGB", (1800, 850), "#F2F6F8")
            draw = ImageDraw.Draw(image)
            draw.text((30, 18), f"{title}　動画 {times[index]:.2f} 秒", font=fonts[34], fill="#173B4D")
            for pos, label, picture in (
                (30, "相対位置をそろえた段階", pictures[0]),
                (900, "追加修正：板の上部に手先を表示", pictures[1]),
            ):
                draw.text((pos, 79), label, font=fonts[26], fill="#173B4D")
                image.paste(picture, (pos, 120))
            draw.text(
                (30, 798),
                "手先と対象だけの模式比較。部品・カメラは前後で同一。実寸・実把持面・把持力の判定ではありません。",
                font=fonts[23],
                fill="#526C78",
            )
            path = output / f"{key}_{index:04d}.png"
            image.save(path)
            rows.append(
                {
                    "file": path.name,
                    "sha256": probe.sha(path),
                    "sample": index,
                    "video_s": float(times[index]),
                    "columns": columns,
                    "camera": camera,
                }
            )
            print("PANEL_COMPARE_PNG", path.name, flush=True)
    finally:
        renderer.delete()
    report = {
        "input_bank_sha256": probe.sha(probe.BANK),
        "output_bank_sha256": probe.sha(new),
        "script_sha256": probe.sha(Path(__file__)),
        "renderer_sha256": probe.sha(probe.PREVIOUS / "render_comparisons.py"),
        "images": rows,
        "physical_acceptance_verdict": None,
    }
    (output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"PANEL_COMPARISONS_COMPLETE images={len(rows)}", flush=True)


if __name__ == "__main__":
    main()
