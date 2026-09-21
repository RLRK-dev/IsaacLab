# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Animate the accepted process storyboard using the prior schematic display model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import legacy_model as base
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FPS = 15
WIDTH, HEIGHT = 1280, 720
STORY = json.loads((ROOT / "inputs/line_process_plan.json").read_text())
# Screen durations only. The source clock belongs to the old schematic, not a robot.
WINDOWS = [
    ("INTRO", 3, 0, 0),
    ("S01", 7, 4, 11),
    ("S02", 4, 11, 11),
    ("S03", 10, 11, 19.5),
    ("S04", 8, 19.5, 22),
    ("S05", 12, 22, 35),
    ("S06", 6, 35, 38),
    ("S07", 5, 38, 40),
    ("S08", 8, 40, 48),
    ("S09", 4, 48, 48),
    ("S10", 8, 48, 48),
    ("S11", 10, 49, 55),
    ("S12", 8, 55, 62),
    ("S13", 4, 62, 62),
    ("S14", 6, 62, 69),
    ("S15", 5, 69, 74),
    ("S16", 8, 74, 82),
    ("OUTRO", 3, 84, 84),
]
SCENES = []
clock = 0
for scene_id, duration, old_start, old_stop in WINDOWS:
    source = next((row for row in STORY["scenes"] if row["id"] == scene_id), {})
    SCENES.append(
        dict(
            source,
            id=scene_id,
            start_s=clock,
            stop_s=clock + duration,
            source_clock=[old_start, old_stop],
            screen_duration_s=duration,
        )
    )
    clock += duration
DURATION = clock
STATIC_TASK_SCENES = {"S02", "S09", "S13", "S14"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def scene_at(t):
    return next(row for row in SCENES if row["start_s"] <= t < row["stop_s"])


def scene_clock(t, row):
    u = (t - row["start_s"]) / row["screen_duration_s"]
    a, b = row["source_clock"]
    return a + u * (b - a), u


class Model(base.Model):
    """Retain old display geometry; separate current scene roles from legacy motion."""

    def oriented_hand(self, name, target, gap, yaw=0):
        self.arm(name, target, gap)
        if not yaw:
            return
        rotation = base.transform((0, 0, 0), (0, 0, yaw))[:3, :3]
        for node in self.arms[name]["hand"]:
            pose = self.scene.get_pose(node)
            pose[:3, 3] = target + rotation @ (pose[:3, 3] - target)
            pose[:3, :3] = rotation @ pose[:3, :3]
            self.scene.set_pose(node, pose)

    def hide(self, nodes):
        for node in nodes:
            self.set(node, base.HIDDEN)

    def unit_origin(self, parts):
        node, offset = parts[0]
        return self.scene.get_pose(node)[:3, 3] - offset

    def transfer_overrides(self, source_t, scene_id, u):
        a = self.unit_origin(self.a_unit)
        b = self.unit_origin(self.b_unit)
        if 21.5 <= source_t < 27.7:
            self.oriented_hand("A", a + [0, 0, 0.045], 0.62)
        if 11.7 <= source_t <= 34.5:
            self.oriented_hand("B", b + [0.20, 0, 0.16], 0.048, np.pi / 2)
        if scene_id == "S06":
            self.oriented_hand("C主", b + [-0.20, 0, 0.16], 0.048, np.pi / 2)
        elif scene_id == "S07":
            target = base.sample(
                u,
                [(0, b + [-0.20, 0, 0.16]), (0.3, a + [0, 0, 0.65]), (0.7, a + [0, 0, 0.045]), (1, a + [0, 0, 0.045])],
            )
            gap = float(base.sample(u, [(0, 0.048), (0.15, 0.23), (0.35, 0.78), (0.7, 0.78), (0.9, 0.62)]))
            yaw = float(base.sample(u, [(0, np.pi / 2), (0.15, np.pi / 2), (0.55, 0)]))
            self.oriented_hand("C主", target, gap, yaw)
        elif scene_id == "S08":
            target = a + [0, 0, 0.045]
            if u > 0.90:
                target = base.sample(u, [(0.90, target), (0.95, a + [0, 0, 0.45]), (1, a + [-0.55, -0.20, 0.60])])
            gap = float(base.sample(u, [(0, 0.62), (0.88, 0.62), (0.90, 0.78)]))
            self.oriented_hand("C主", target, gap)

    def guide_overrides(self, source_t, scene_id, u):
        a = self.unit_origin(self.a_unit)
        b = self.unit_origin(self.b_unit)
        if source_t < 35:
            return
        # The unadopted AB-to-C accompaniment is deliberately absent.
        self.arm("AB補助", np.array([0, 1.75, 1.80]), 0.20)
        if scene_id in {"S06", "S07", "S08", "S09"}:
            guide = a + [-0.10, -0.02, 0.48]
            self.arm("C補助", guide, 0.24)
            self.cable(0, a + [-0.15, 0, 0.13], guide + [-0.06, 0, 0], 0.04)
            self.cable(1, b + [0.12, -0.08, 0.15], guide + [0.06, 0, 0], 0.04)
        elif scene_id == "S10":
            end = base.sample(
                u,
                [
                    (0, a + [-0.10, -0.02, 0.48]),
                    (0.30, (-0.17, -1.28, 1.02)),
                    (0.68, (-0.17, -1.51, 1.02)),
                    (1, (-0.17, -1.51, 1.02)),
                ],
            )
            self.cable(0, a + [-0.15, 0, 0.13], end, 0.035)
            self.cable(1, b + [0.12, -0.08, 0.15], b + [0.10, -0.02, 0.44], 0.035)
            self.arm("C補助", end, 0.085)
            self.arm("C主", np.array([-0.80, -1.90, 1.62]), 0.20)
        elif scene_id == "S11":
            end = np.array([-0.17, -1.38, 1.02])
            self.cable(0, a + [-0.15, 0, 0.13], end, 0.035)
            self.arm("C補助", end, 0.085)
            # Aim at the flange perimeter rather than the connector opening.
            body = self.scene.get_pose(self.tools["C"][0])[:3, 3]
            body[0], body[2] = -0.29, 1.082
            self.set(self.tools["C"][0], body, (np.pi / 2, 0, 0))
            self.set(self.tools["C"][1], body + [0, 0.28, 0], (np.pi / 2, 0, 0))
        elif scene_id == "S12":
            bar = self.scene.get_pose(self.busbar)[:3, 3]
            if 56.3 <= source_t <= 60.5:
                self.oriented_hand("C主", bar, 0.083, np.pi / 2)
            elif source_t > 60.5:
                rise = float(base.sample(source_t, [(60.5, 0), (61, 0), (62, 0.38)]))
                gap = float(base.sample(source_t, [(60.5, 0.085), (61, 0.22)]))
                self.oriented_hand("C主", np.array([-0.10, -1.20, 1.10 + rise]), gap, np.pi / 2)
                self.arm("C補助", np.array([0.10, -1.48, 1.14 + rise]), gap)
        elif scene_id == "S13":
            self.oriented_hand("C主", np.array([-0.10, -1.20, 1.48]), 0.22, np.pi / 2)
            self.arm("C補助", np.array([0.10, -1.48, 1.52]), 0.22)
        if scene_id == "S09":
            self.arm("C主", a + [-0.55, -0.20, 0.60], 0.78)
            self.tool("C", a + [0, 0, 0.38], 0)

    def camera_for(self, scene_id):
        views = {
            "INTRO": ((8, -14, 11), (-1.8, 0.4, 0.7), 7.5),
            "S01": ((-9, -8, 7), (-5.35, 0.6, 0.9), 3.95),
            "S02": ((5.5, -6.5, 6), (0, 1.0, 1.0), 3.55),
            "S03": ((5.5, -6.5, 6), (0, 1.0, 1.0), 3.55),
            "S04": ((4.8, -3.5, 5.0), (1.30, 0.85, 1.10), 1.65),
            "S05": ((5.2, -7.0, 5.6), (0, -0.2, 1.0), 3.15),
            "S06": ((3.3, -4.0, 4.5), (0, 0.4, 1.05), 1.30),
            "S07": ((3.3, -4.0, 4.5), (0, 0.4, 1.05), 1.45),
            "S08": ((5.2, -7.0, 5.6), (0, -0.2, 1.2), 2.90),
            "S09": ((2.8, -5.0, 5.8), (-0.05, -1.0, 1.1), 1.45),
            "S10": ((1.8, -4.0, 3.2), (-0.05, -1.25, 1.13), 1.10),
            "S11": ((2.2, -4.5, 3.1), (-0.12, -1.40, 1.10), 1.30),
            "S12": ((2.8, -5.0, 5.8), (-0.05, -1.0, 1.1), 1.30),
            "S13": ((2.8, -5.0, 5.8), (-0.05, -1.0, 1.1), 1.45),
            "S14": ((7.0, -6.0, 5.5), (2.65, -0.7, 0.9), 2.75),
            "S15": ((6, -13, 9), (-0.6, -0.4, 0.8), 5.9),
            "S16": ((-9, -8, 7), (-5.35, 0.6, 0.9), 3.95),
            "OUTRO": ((8, -14, 11), (-1.8, 0.4, 0.7), 7.5),
        }
        eye, target, span = views[scene_id]
        self.scene.set_pose(self.camera, base.look_at(eye, target))
        self.camera.camera.xmag = span
        self.camera.camera.ymag = span * HEIGHT / WIDTH
        return self.scene.get_pose(self.camera), span

    def animate_process(self, t):
        row = scene_at(t)
        source_t, u = scene_clock(t, row)
        super().animate(source_t)
        self.transfer_overrides(source_t, row["id"], u)
        self.guide_overrides(source_t, row["id"], u)
        # Unknown operations remain explicit slots, without fabricated fastening points.
        if row["id"] in {"S09", "S10", "S13"}:
            self.hide(self.tools["C"])
        if row["id"] == "S14":
            self.hide(self.out_hand + self.out_xyz + [self.probe, self.lid])
        camera, span = self.camera_for(row["id"])
        return camera, span


NOTES = {
    "S01": ["筐体 → パレットの支持へ引継ぎ → フィンガを開放", "01の枠は完成品が戻るまで空けておきます"],
    "S02": [
        "線材・端末の準備 / 部品・ボルト供給 / 空容器回収",
        "内製・購入の範囲と補給設備は未定：この場面は工程枠の説明",
    ],
    "S03": ["A/Bは並行。必要な共用補助は保持中に切り替えません", "接触器・リレー・抵抗と下板側の配線を筐体外で組立"],
    "S04": ["補機ヒューズ板側の締結は、筐体に入れる前に実施", "線の反対端の接続は別作業。主ヒューズの工程は未確定"],
    "S05": ["本体の受けと、自由端の案内を分けて引き継ぎます", "詳細な受け面・案内保持構成・A/Bの受渡し順は未確定"],
    "S06": ["下板を支持し、C主腕が板を保持したまま工具で固定", "採用済みの仮手順です。実物の固定点は未確認"],
    "S07": ["支持を残して H07板保持 → H06ユニット搬送候補へ", "持ち替え方式・把持面・板間接合の荷重受容は未確定"],
    "S08": ["C主腕：ユニット搬送 / C専用補助：自由端群の案内役", "線は群の記号。全端末をどう保持するかは未確定"],
    "S09": ["筐体搭載後に、内部の工具作業が残ります", "対象・固定点・ねじ数は未特定：締結動作は描いていません"],
    "S10": [
        "内側ハウジングを側壁開口へ通し、外側の支持へ引継ぎ",
        "代表端末のみを表示。別の自由端の保持と全通過経路は未確定",
    ],
    "S11": [
        "C主腕：外側H05 / C補助：内側端末 / 工具：フランジ締結",
        "内側ロックと全ねじの詳細順は未確定。1ヘッダーの代表動作",
    ],
    "S12": ["H03で導体、必要時H04でケーブルを別々に保持して締結", "主ヒューズP22・被覆P08の工程は未確定のままです"],
    "S13": ["残るLV/HVILは別管理：完了扱いにしません", "個々の端末・接続先・内外位置は未確定：接続動作は未表示"],
    "S14": ["シール・蓋・検査の工程枠を残します", "順序・設備分担は未確定。次の復路場面は後工程完了を仮定"],
    "S15": [
        "完成品を載せたパレットを、同じ段・同じ高さで逆方向へ",
        "この1枚は説明用。ライン全体の枚数・通行順は未選定",
    ],
    "S16": [
        "供給と同じXYZで完成品を取り出し、元の枠01へ収納",
        "ストッカは空筐体19枠＋完成品1枠。空パレットは供給側に残ります",
    ],
}


def role_labels(draw, row, camera, span, role_points):
    names = list(role_points) if row["id"] in {"INTRO", "S03", "S05", "OUTRO"} else []
    if row.get("place_ja", "").endswith("C") or row["id"] in {"S07", "S08", "S10", "S11", "S12"}:
        names = ["C主", "C補助"]
    if row["id"] == "S04":
        names = ["B"]
    used = []
    font = ImageFont.truetype(base.FONT, 16)
    labels = {"A": "A 主担当", "B": "B 主担当", "AB補助": "A/B 共用補助", "C主": "C 主担当", "C補助": "C 専用補助"}
    for name in names:
        point = role_points[name]
        local = (point - camera[:3, 3]) @ camera[:3, :3]
        px, py = WIDTH / 2 + local[0] / (2 * span) * WIDTH, HEIGHT / 2 - local[1] / (2 * span) * WIDTH
        if not (35 < px < WIDTH - 130 and 160 < py < 510):
            continue
        text = labels[name]
        width = int(draw.textlength(text, font=font)) + 16
        x, y = min(WIDTH - width - 20, px + 48), max(155, py - 64)
        for _ in range(5):
            if any(abs(y - other_y) < 30 and abs(x - other_x) < width for other_x, other_y in used):
                y += 30
        if y > 502:
            continue
        used.append((x, y))
        draw.line((px, py, x, y + 14), fill=(23, 72, 96), width=2)
        draw.rounded_rectangle((x, y, x + width, y + 28), 4, fill=(236, 246, 250), outline=(23, 72, 96))
        draw.text((x + 8, y + 2), text, font=font, fill=(23, 72, 96))


def label_image(color, t, camera, span, role_points):
    row = scene_at(t)
    scene_id = row["id"]
    image = Image.fromarray(color).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(base.FONT, 23)
    small = ImageFont.truetype(base.FONT, 18)
    title = row.get("title_ja", "A/Bの外組み → Cで合流・搭載 → 残接続 → 復路収納")
    place = row.get("place_ja", "ライン全体")
    draw.rounded_rectangle((16, 53, 1264, 137), 8, fill=(239, 246, 248))
    draw.text((30, 62), f"{scene_id}  |  {place}  |  {title}", font=font, fill=(26, 55, 73))
    draw.text(
        (30, 100),
        row.get("actors_ja", "主担当A・B・C ＋ A/B共用補助 ＋ C専用補助 ／ 供給XYZ"),
        font=small,
        fill=(38, 91, 121),
    )
    notes = NOTES.get(
        scene_id,
        [
            "20作業を16場面に対応。A/B/Cは別ワークを並行処理する方針",
            "概略の役割・移動を確認する動画です。形状・把持・速度は実機仕様ではありません",
        ],
    )
    if scene_id in STATIC_TASK_SCENES:
        draw.rounded_rectangle((25, 160, 640, 211), 8, fill=(255, 242, 212))
        draw.text((40, 171), "未確定の作業：工程枠の表示（動作未設定）", font=font, fill=(111, 74, 21))
    draw.rounded_rectangle((16, 538, 1264, 652), 8, fill=(240, 247, 250))
    for i, note in enumerate(notes):
        draw.text((31, 550 + i * 31), note, font=small, fill=(30, 59, 79))
    draw.text(
        (31, 618),
        "形状は簡略表示 / 線は配線群の記号 / 固定工具は比較案 / 動画時間は実タクトではありません",
        font=small,
        fill=(91, 104, 112),
    )
    role_labels(draw, row, camera, span, role_points)
    return image


def verify_originals():
    pins = json.loads((ROOT / "inputs/original_sources.json").read_text())
    for row in pins:
        assert sha(row["path"]) == row["sha256"], row["path"]
    return {row["path"]: row["sha256"] for row in pins}


def sample_scene(model, times, bank_path):
    matrices, cameras, spans = [], [], []
    for t in times:
        camera, span = model.animate_process(float(t))
        matrices.append([model.scene.get_pose(node) for node in model.dynamic])
        cameras.append(camera)
        spans.append(span)
    np.savez_compressed(
        bank_path,
        time_s=times,
        matrices=np.asarray(matrices),
        camera=np.asarray(cameras),
        span=spans,
        object_names=np.asarray(model.names),
    )


def render_saved(model, bank_path, directory, plan, plan_path, pins):
    renderer = base.pyrender.OffscreenRenderer(WIDTH, HEIGHT)
    rows = []
    try:
        with np.load(bank_path, allow_pickle=False) as saved:
            for i, t in enumerate(saved["time_s"]):
                for node, pose in zip(model.dynamic, saved["matrices"][i]):
                    model.scene.set_pose(node, pose)
                model.scene.set_pose(model.camera, saved["camera"][i])
                model.camera.camera.xmag = saved["span"][i]
                model.camera.camera.ymag = saved["span"][i] * HEIGHT / WIDTH
                color, depth = renderer.render(model.scene)
                assert np.isfinite(depth).all() and np.count_nonzero(depth) > 1000
                path = directory / f"{i + 1:05d}.png"
                role_points = {
                    name: saved["matrices"][i, model.names.index(name + "_palm"), :3, 3] for name in model.arms
                }
                label_image(color, float(t), saved["camera"][i], saved["span"][i], role_points).save(path)
                rows.append(
                    dict(
                        plan["expected_source_samples"][i],
                        view="process",
                        frame=i * 2 + 1,
                        camera=plan["camera"],
                        file=path.name,
                        sha256=sha(path),
                        display_segment="saved_sample",
                    )
                )
                if i % 60 == 0 or i == len(saved["time_s"]) - 1:
                    print("PROCESS_RENDER", i + 1, "/", len(saved["time_s"]), flush=True)
    finally:
        renderer.delete()
    assert all(sha(path) == digest for path, digest in pins.items())
    save(
        directory / "manifest.json",
        dict(
            complete=True,
            source_kind=plan["source_kind"],
            output_fps=FPS,
            settings=dict(width=WIDTH, height=HEIGHT),
            shot_plan_sha256=sha(plan_path),
            renderer_sha256=sha(__file__),
            input_sha256_current=pins,
            images=rows,
            physical_acceptance_verdict=None,
            authored_motion_kind=plan["authored_motion_kind"],
        ),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output_name", default="concept_v03")
    args = parser.parse_args()
    directory = ROOT / "previews" / args.output_name
    bank = ROOT / "data" / (args.output_name + ".npz")
    plan_path = ROOT / "data" / (args.output_name + ".json")
    assert not any(p.exists() for p in [directory, bank, plan_path])
    pins = verify_originals()
    for path in [Path(__file__), ROOT / "legacy_model.py", ROOT / "inputs/line_process_plan.json"]:
        pins[str(path)] = sha(path)
    directory.mkdir()
    times = (
        np.array([row["start_s"] + row["screen_duration_s"] * 0.62 for row in SCENES])
        if args.preview
        else np.arange(FPS * DURATION) / FPS
    )
    model = Model()
    sample_scene(model, times, bank)
    pins[str(bank)] = sha(bank)
    expected = [
        dict(feature_id=scene_at(float(t))["id"], saved_frame=i + 1, saved_bank_index=i, saved_time_s=float(t))
        for i, t in enumerate(times)
    ]
    plan = dict(
        source_kind="saved_geometry_samples",
        authored_motion_kind="illustrative_process_storyboard",
        native=None,
        native_sha256=None,
        motion=bank.name,
        motion_sha256=sha(bank),
        input_sha256=pins,
        renderer=str(Path(__file__)),
        camera="process_sequence_v03",
        frame_end=len(times) * 2,
        expected_source_samples=expected,
        repeat_each_source_sample=1,
        scope_caption="HVJB ライン工程確認 v03｜筐体内外と保持担当の説明用・実機動作の再現ではありません",
        phase_prefix="",
        phases=[
            dict(
                start_s=r["start_s"],
                stop_s=r["stop_s"],
                label=r.get("hold_or_limit_ja", "1段往復パレット / 20枠共用 / 主担当3腕と補助2腕"),
            )
            for r in SCENES
        ],
        scenes=SCENES,
        tasks_preserved=[r["id"] for r in STORY["cards"]],
        static_task_scenes=sorted(STATIC_TASK_SCENES),
        simplified_geometry=True,
        robot_model_selected=False,
        joint_trajectory=None,
        actual_takt_s=None,
        physical_acceptance_verdict=None,
        old_native_modified=False,
        AB_assist_accompaniment_adopted=False,
        free_end_count_and_actual_retention=None,
        conveyor_levels=1,
        pallet_return_same_level=True,
        stock_total_slots=20,
        vacated_slot_reused_for_finished="01",
    )
    save(plan_path, plan)
    print("PROCESS_SAVED", len(times), len(model.dynamic), flush=True)
    render_saved(model, bank, directory, plan, plan_path, pins)
    print("PROCESS_COMPLETE", args.output_name, flush=True)


if __name__ == "__main__":
    main()
