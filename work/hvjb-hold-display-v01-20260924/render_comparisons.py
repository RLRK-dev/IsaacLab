# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Render saved before/after hand symbols with identical fitted cameras per pair."""

import json
from itertools import product
from pathlib import Path

import correct_holds as fix
import numpy as np
import probe_holds as probe
from PIL import Image, ImageDraw, ImageFont

SIZE = (870, 660)
CASES = [
    ("A_next", "A", "base_next", [619, 652, 720], "A：次の下板ユニット"),
    ("B_next", "B", "panel_next", [750, 825, 855], "B：次のヒューズ板"),
    ("C_header", "C主", "header", [1150, 1175, 1195], "C：外側ヘッダー"),
]


def corners(mesh):
    return np.array(list(product(*mesh.bounds.T.tolist())))


def fitted_camera(model, columns, matrices):
    points = np.concatenate(
        [
            corners(model.dynamic[col].mesh) @ poses[col, :3, :3].T + poses[col, :3, 3]
            for poses in matrices
            for col in columns
        ]
    )
    focus = (points.min(0) + points.max(0)) / 2
    matrix = fix.old.base.look_at(focus + [2.0, -3.0, 2.4], focus)
    xy = ((points - focus) @ matrix[:3, :3])[:, :2]
    # Same fixed-envelope projection method as H06 view_frame(), with dimensionless input.
    span = 1.12 * max(abs(xy[:, 0]).max(), abs(xy[:, 1]).max() * SIZE[0] / SIZE[1])
    bounds = xy / [span, span * SIZE[1] / SIZE[0]]
    assert abs(bounds).max() < 1
    return matrix, float(span), [bounds.min(0).tolist(), bounds.max(0).tolist()]


def render_pair(model, renderer, columns, states):
    matrix, span, bounds = fitted_camera(model, columns, states)
    scene = fix.old.base.pyrender.Scene(bg_color=(0.95, 0.97, 0.98, 1), ambient_light=(0.5, 0.5, 0.5))
    scene.add(
        fix.old.base.pyrender.OrthographicCamera(xmag=span, ymag=span * SIZE[1] / SIZE[0], znear=0.01, zfar=30),
        pose=matrix,
    )
    for offset, intensity in (([-4, -5, 9], 1.8), ([5, 3, 7], 0.7)):
        scene.add(
            fix.old.base.pyrender.DirectionalLight(color=np.ones(3), intensity=intensity),
            pose=fix.old.base.look_at(offset, [0, 0, 0]),
        )
    nodes = {col: scene.add(model.dynamic[col].mesh, pose=states[0][col]) for col in columns}
    pictures = []
    for poses in states:
        for col, node in nodes.items():
            scene.set_pose(node, poses[col])
        color, depth = renderer.render(scene)
        assert np.isfinite(depth).all() and np.count_nonzero(depth) > 100
        pictures.append(Image.fromarray(color).convert("RGB"))
    return pictures, {"matrix": matrix.tolist(), "xmag_display_units": span, "projected_bounds": bounds}


def main():
    output = probe.ROOT / "comparisons"
    assert not output.exists()
    delta = json.loads((probe.ROOT / "audit/hold_display_delta.json").read_text())
    new = probe.ROOT / delta["output_bank"]
    assert probe.sha(probe.BANK) == probe.BANK_SHA and probe.sha(new) == delta["output_sha256"]
    with np.load(probe.BANK, allow_pickle=False) as saved:
        before, times = saved["matrices"], saved["time_s"]
    with np.load(new, allow_pickle=False) as saved:
        after = saved["matrices"]
    model = fix.old.Model()
    renderer = fix.old.base.pyrender.OffscreenRenderer(*SIZE)
    fonts = {size: ImageFont.truetype(fix.old.base.FONT, size) for size in (23, 26, 34)}
    rows = []
    output.mkdir()
    try:
        for key, hand, target, indices, title in CASES:
            columns = [
                i
                for i, name in enumerate(model.names)
                if name.startswith(target)
                or name in {hand + suffix for suffix in ("_palm", "_left_finger", "_right_finger", "_carrier")}
            ]
            for index in indices:
                pictures, camera = render_pair(model, renderer, columns, [before[index], after[index]])
                image = Image.new("RGB", (1800, 850), "#F2F6F8")
                draw = ImageDraw.Draw(image)
                draw.text((30, 18), f"{title}　動画 {times[index]:.2f} 秒", font=fonts[34], fill="#173B4D")
                for pos, label, picture in (
                    (30, "修正前", pictures[0]),
                    (900, "修正後：既存の保持位置・向きへ統一", pictures[1]),
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
                print("HOLD_COMPARE_PNG", path.name, flush=True)
    finally:
        renderer.delete()
    report = {
        "input_bank_sha256": probe.BANK_SHA,
        "output_bank_sha256": probe.sha(new),
        "script_sha256": probe.sha(Path(__file__)),
        "images": rows,
        "physical_acceptance_verdict": None,
    }
    (output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("HOLD_COMPARISONS_COMPLETE images=9", flush=True)


if __name__ == "__main__":
    main()
