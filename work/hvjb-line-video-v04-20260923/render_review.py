# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Place saved schematic motion and completed-product references on one review canvas."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "hvjb-line-video-v03-20260921"
DOCUMENT = ROOT.parent / "hvjb-line-progress-20260923"
SOURCE_BANK = Path("/home/rlrk/Downloads/HVJB_ライン工程確認_v03_20260921/data/concept_v03.npz")
BANK_SHA = "52eede374a2d782aabf1cc2604801cc64e6f884b39060728c437631a8dca36dc"
sys.path.insert(0, str(OLD))
import render_process as old  # noqa: E402

WIDTH, HEIGHT, FPS = 1920, 1080, 15
VIEW_X, VIEW_Y, VIEW_W, VIEW_H = 24, 192, 1248, 702
FONT = old.base.FONT
INK, MUTED = "#173B4D", "#526C78"
COLORS = {"A": "#296DB3", "B": "#9E478F", "AB補助": "#665797", "C主": "#198772", "C補助": "#367A7B"}
GROUPS = [
    ("供給・20枠", {"INTRO", "S01"}),
    ("準備", {"S02"}),
    ("A/B 外組み", {"S03", "S04"}),
    ("C 合流", {"S05", "S06", "S07"}),
    ("筐体へ搭載", {"S08", "S09"}),
    ("側壁の接続", {"S10", "S11"}),
    ("残る接続", {"S12", "S13"}),
    ("後工程", {"S14"}),
    ("復路・収納", {"S15", "S16", "OUTRO"}),
]
VIEW_LABELS = {
    "product": ("完成状態の全体参照", "個々の自由端と保持数は未確定"),
    "case": ("筐体と周囲の部品", "XYZとパレットの支持を引き継ぐ"),
    "outside_A": ("青：Aで検討する部品群", "接触器・リレー・抵抗等"),
    "outside_B": ("紫：Bで検討する部品群", "補機ヒューズ板側の部品"),
    "after_insertion_bus": ("緑：搭載後の残接続", "バスバー・端子積層の検討先"),
    "external_headers": ("緑：外側ヘッダー", "OP020指定の設置・ねじ固定"),
    "internal_housings": ("緑：内側ハウジング", "側壁開口と外側支持への引継ぎ"),
    "main_and_lv_unassigned": ("橙：主電力口・LV口", "相手品番と固有の着脱は未確定"),
    "wires_display_only": ("橙：写真で追った線の区間", "隠れた部分を含む全配線ではない"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, data: dict) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


class Composition:
    """Draw only screen annotations; stored object matrices remain unchanged."""

    def __init__(self, data: dict):
        self.data = data
        self.fonts = {size: ImageFont.truetype(FONT, size) for size in (18, 21, 22, 23, 24, 25, 27, 30, 35)}
        self.figures = {
            path.stem: Image.open(path).convert("RGB").resize((564, 388), Image.Resampling.LANCZOS)
            for path in (DOCUMENT / "figures/product_final").glob("*.png")
        }
        self.scene_map = {row["id"]: row for row in data["scenes"]}
        self.text_bounds = []

    def text(self, draw, position, text, size=24, color=INK):
        bounds = draw.textbbox(position, text, font=self.fonts[size])
        assert bounds[0] >= 0 and bounds[1] >= 0 and bounds[2] <= WIDTH and bounds[3] <= HEIGHT, (text, bounds)
        draw.text(position, text, font=self.fonts[size], fill=color)
        self.text_bounds.append((text, bounds))

    def lines(self, draw, position, text, width, size=24, leading=33, max_lines=3, color=INK):
        line, lines = "", []
        for char in text:
            if char == "\n" or draw.textlength(line + char, font=self.fonts[size]) > width:
                lines.append(line)
                line = "" if char == "\n" else char
            else:
                line += char
        if line:
            lines.append(line)
        assert len(lines) <= max_lines, (text, lines)
        for index, line in enumerate(lines):
            self.text(draw, (position[0], position[1] + index * leading), line, size, color)

    def role_labels(self, draw, scene_id, camera, span, points):
        names = list(points) if scene_id in {"INTRO", "S03", "S05", "OUTRO"} else []
        if scene_id in {"S06", "S07", "S08", "S10", "S11", "S12"}:
            names = ["C主", "C補助"]
        if scene_id == "S04":
            names = ["B", "AB補助"]
        labels = {"A": "A 主担当", "B": "B 主担当", "AB補助": "A/B 共用補助", "C主": "C 主担当", "C補助": "C 専用補助"}
        occupied = []
        for name in names:
            local = (points[name] - camera[:3, 3]) @ camera[:3, :3]
            px = VIEW_X + VIEW_W / 2 + local[0] / (2 * span) * VIEW_W
            py = VIEW_Y + VIEW_H / 2 - local[1] / (2 * span) * VIEW_W
            if not (VIEW_X + 30 < px < VIEW_X + VIEW_W - 80 and VIEW_Y + 65 < py < VIEW_Y + VIEW_H - 70):
                continue
            label = labels[name]
            width = int(draw.textlength(label, font=self.fonts[22])) + 22
            x, y = min(VIEW_X + VIEW_W - width - 10, px + 38), max(VIEW_Y + 55, py - 54)
            for _ in range(6):
                if any(x < bx + bw and x + width > bx and abs(y - by) < 36 for bx, by, bw in occupied):
                    y += 38
            if y > VIEW_Y + VIEW_H - 40:
                continue
            occupied.append((x, y, width))
            draw.line((px, py, x, y + 15), fill=COLORS[name], width=2)
            draw.rounded_rectangle((x, y, x + width, y + 35), 5, fill="#F6FAFC", outline=COLORS[name], width=2)
            self.text(draw, (x + 11, y + 2), label, 22, COLORS[name])

    def header(self, draw, row):
        title = row.get("title_ja", "A/B外組み → Cで合流・搭載 → 残接続 → 同じ枠へ収納")
        place = row.get("place_ja", "ライン全体")
        self.text(draw, (28, 64), f"{row['id']}  |  {place}  |  {title}", 35)
        for index, (label, ids) in enumerate(GROUPS):
            x = 24 + index * 209
            active = row["id"] in ids
            draw.rounded_rectangle((x, 125, x + 197, 171), 6, fill="#198772" if active else "#EAF0F4")
            self.text(draw, (x + 14, 133), label, 23, "white" if active else MUTED)

    def product_panel(self, image, draw, row):
        detail = self.scene_map.get(row["id"], {})
        view = detail.get("product_view", "product")
        draw.rounded_rectangle((1292, 192, 1896, 894), 8, fill="white", outline="#CFDDE4", width=2)
        self.text(draw, (1312, 209), "照合：完成状態の保存モデル", 25)
        image.paste(self.figures[view], (1312, 254))
        label, note = VIEW_LABELS[view]
        if row["id"] == "S08":
            label, note = "緑：ユニットを搭載する筐体", "本体の搬送と自由端の案内を分担"
        self.text(draw, (1312, 662), label, 25, "#198772" if row["id"] not in old.STATIC_TASK_SCENES else "#A7610F")
        self.text(draw, (1312, 700), note, 22, MUTED)
        actors = row.get("actors_ja", "A・B・C主担当 / A/B共用補助 / C専用補助 / 供給XYZ")
        self.lines(draw, (1312, 750), actors, 557, 23, 32, 3)
        jobs = [job["id"] for job in self.data["jobs"] if row["id"] in job["scene_ids"]]
        self.text(draw, (1312, 854), "対応仕事：" + (" / ".join(jobs) if jobs else "全20仕事の案内"), 22, MUTED)

    def compose(self, color, t, camera, span, points):
        row = old.scene_at(t)
        image = Image.new("RGB", (WIDTH, HEIGHT), "#F2F6F8")
        raw = Image.fromarray(color).convert("RGB").resize((VIEW_W, VIEW_H), Image.Resampling.LANCZOS)
        image.paste(raw, (VIEW_X, VIEW_Y))
        draw = ImageDraw.Draw(image)
        self.header(draw, row)
        self.product_panel(image, draw, row)
        draw.rounded_rectangle((36, 204, 597, 246), 6, fill="#F4F8FA")
        self.text(draw, (48, 209), "動作：配置と手先移動の模式図", 25)
        if row["id"] in old.STATIC_TASK_SCENES:
            draw.rounded_rectangle((36, 260, 881, 306), 6, fill="#FFF0D9")
            self.text(draw, (49, 268), "未確定の作業：工程枠を表示し、施工動作は設定していません", 25, "#A7610F")
        self.role_labels(draw, row["id"], camera, span, points)
        notes = old.NOTES.get(
            row["id"],
            [
                "20仕事を16工程場面へ対応。3STは別の一式を並行して処理する方針です",
                "左は模式動作、右は完成状態の部品照合図です",
            ],
        )
        if row["id"] == "S08":
            notes = [
                "C主腕はユニットを搬送。C専用補助は自由端の支持先へ渡すまで担当を残します",
                "線は群の記号。1つの手で全端末を保持できるとは確認していません",
            ]
        draw.rounded_rectangle((24, 915, 1896, 1015), 8, fill="white", outline="#CFDDE4")
        for index, note in enumerate(notes):
            self.text(draw, (44, 928 + index * 40), note, 27)
        draw.rectangle((24, 1072, 1896, 1078), fill="#D4E0E7")
        draw.rectangle((24, 1072, 24 + 1872 * t / 119, 1078), fill="#198772")
        return image


def prepare_inputs() -> tuple[dict, Path, dict]:
    source_plan = json.loads((OLD / "data/concept_v03.json").read_text())
    assert source_plan["motion_sha256"] == BANK_SHA == sha(SOURCE_BANK)
    bank = ROOT / "data/concept_v03_reused.npz"
    if not bank.exists():
        shutil.copy2(SOURCE_BANK, bank)
    assert sha(bank) == BANK_SHA
    source_paths = [
        Path(__file__),
        OLD / "render_process.py",
        OLD / "legacy_model.py",
        OLD / "inputs/line_process_plan.json",
        OLD / "data/concept_v03.json",
        DOCUMENT / "data/line_review_data.json",
        DOCUMENT / "audit/product_final_views.json",
        Path("/home/rlrk/src/ur15-line-render/render_ur15_line.py"),
        Path(FONT),
        bank,
    ]
    source_paths.extend(sorted((DOCUMENT / "figures/product_final").glob("*.png")))
    pins = {str(path): sha(path) for path in source_paths}
    # The old temporary worktree was removed. Match the checked-in runtime copies by suffix and exact hash.
    for path in source_paths[1:4]:
        relative = str(path.relative_to(OLD))
        historical = [value for key, value in source_plan["input_sha256"].items() if key.endswith("/" + relative)]
        assert historical == [sha(path)], (path, historical)
    helper = "/home/rlrk/src/ur15-line-render/render_ur15_line.py"
    assert pins[helper] == source_plan["input_sha256"][helper]
    return source_plan, bank, pins


def make_plan(source_plan, bank, pins, indices, name, preview):
    samples = [dict(source_plan["expected_source_samples"][int(index)]) for index in indices]
    return {
        "source_kind": "saved_geometry_samples",
        "authored_motion_kind": "reused_v03_schematic_matrices_with_v04_reference_panel",
        "native": None,
        "native_sha256": None,
        "motion": bank.name,
        "motion_sha256": BANK_SHA,
        "input_sha256": pins,
        "renderer": str(Path(__file__)),
        "camera": "v03_saved_process_camera_v04_screen_layout",
        "frame_end": len(indices) * 2,
        "expected_source_samples": samples,
        "repeat_each_source_sample": 1,
        "scope_caption": "HVJB 全体工程 v04｜左：模式動作 / 右：完成状態の部品照合図 / 実機仕様・実タクトは未確定",
        "phase_prefix": "",
        "phases": source_plan["phases"],
        "scenes": source_plan["scenes"],
        "tasks_preserved": source_plan["tasks_preserved"],
        "static_task_scenes": source_plan["static_task_scenes"],
        "output_name": name,
        "preview_only": preview,
        "saved_geometry_or_motion_modified": False,
        "product_reference_configuration": "completed_saved_photo_model_not_intermediate_workpiece",
        "free_end_count_and_actual_retention": None,
        "robot_model_selected": False,
        "actual_takt_s": None,
        "physical_acceptance_verdict": None,
    }


def render_frames(model, bank, indices, directory, plan, composition):
    with np.load(bank, allow_pickle=False) as saved:
        matrices, cameras, spans, times, names = (
            saved[key] for key in ("matrices", "camera", "span", "time_s", "object_names")
        )
    assert names.tolist() == model.names and len(names) == 304
    assert matrices.shape == (1785, 304, 4, 4)
    assert np.allclose(times, np.arange(1785) / 15, atol=0, rtol=0)
    renderer = old.base.pyrender.OffscreenRenderer(old.WIDTH, old.HEIGHT)
    rows, cache = [], {}
    try:
        for number, index in enumerate(indices):
            key = hashlib.sha256(
                matrices[index].tobytes() + cameras[index].tobytes() + spans[index].tobytes()
            ).hexdigest()
            if key not in cache:
                for node, pose in zip(model.dynamic, matrices[index], strict=True):
                    model.scene.set_pose(node, pose)
                model.scene.set_pose(model.camera, cameras[index])
                model.camera.camera.xmag = spans[index]
                model.camera.camera.ymag = spans[index] * old.HEIGHT / old.WIDTH
                color, depth = renderer.render(model.scene)
                assert np.isfinite(depth).all() and np.count_nonzero(depth) > 1000
                cache = {key: color}
            points = {name: matrices[index, model.names.index(name + "_palm"), :3, 3] for name in model.arms}
            png = directory / f"{number + 1:05d}.png"
            composition.compose(cache[key], float(times[index]), cameras[index], spans[index], points).save(png)
            rows.append(
                dict(
                    plan["expected_source_samples"][number],
                    view="process",
                    frame=number * 2 + 1,
                    camera=plan["camera"],
                    file=png.name,
                    sha256=sha(png),
                    display_segment="saved_sample",
                    saved_matrix_camera_identity=key,
                )
            )
            if number % 90 == 0 or number == len(indices) - 1:
                print(f"V04_PROCESS_PNG {number + 1}/{len(indices)}", flush=True)
    finally:
        renderer.delete()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output_name", default="concept_v04")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    directory = ROOT / "previews" / args.output_name
    plan_path = ROOT / "data" / f"{args.output_name}.json"
    assert not directory.exists() and not plan_path.exists()
    for path in (ROOT / "data", ROOT / "audit", ROOT / "previews"):
        path.mkdir(exist_ok=True)
    source_plan, bank, pins = prepare_inputs()
    indices = (
        np.array([int((row["start_s"] + 0.62 * (row["stop_s"] - row["start_s"])) * FPS) for row in old.SCENES])
        if args.preview
        else np.arange(1785)
    )
    plan = make_plan(source_plan, bank, pins, indices, args.output_name, args.preview)
    save(plan_path, plan)
    directory.mkdir()
    composition = Composition(json.loads((DOCUMENT / "data/line_review_data.json").read_text()))
    rows = render_frames(old.Model(), bank, indices, directory, plan, composition)
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "complete": True,
        "source_kind": plan["source_kind"],
        "output_fps": FPS,
        "settings": {"width": WIDTH, "height": HEIGHT},
        "shot_plan_sha256": sha(plan_path),
        "renderer_sha256": sha(Path(__file__)),
        "input_sha256_current": pins,
        "images": rows,
        "text_elements_checked": len(composition.text_bounds),
        "saved_geometry_or_motion_modified": False,
        "physical_acceptance_verdict": None,
    }
    save(directory / "manifest.json", manifest)
    print(f"V04_PROCESS_COMPLETE frames={len(rows)} source_bank_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
