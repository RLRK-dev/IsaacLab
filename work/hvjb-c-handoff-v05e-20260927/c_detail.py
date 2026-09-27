# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Explain C support roles using saved poses, with arm links hidden only in the detail view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from build_motion import ROOT, WORK, load_module, sha, write
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
STEPS = [
    (
        32,
        38,
        6,
        "A側の本体をF-Cへ",
        "A主担当 → F-C",
        "受入れ準備",
        "自由端の引継ぎを検討",
        "D12｜本体と自由端を別々に引き継ぐ。",
        "実際の受渡し順と支持形状は未確定。",
    ),
    (
        38,
        44,
        8,
        "B側の板を合流",
        "F-C＋板の保持担当",
        "板を受けて位置を保つ",
        "案内役をC側へ引継ぐ",
        "D22 → D30｜下板の支持と板保持を分担する。",
        "映像は代表順。全自由端の受渡しは未確定。",
    ),
    (
        44,
        50,
        6,
        "板保持を続けて工具退避",
        "F-C",
        "板の相対姿勢を保持",
        "自由端案内を継続",
        "D30｜工具が上へ戻る間も、板を保持する。",
        "板間固定の実ねじ点・荷重受容は未確定。",
    ),
    (
        50,
        50.85,
        3,
        "① 位置を保って指を開く",
        "F-C（支持を残す）",
        "板保持を開放",
        "自由端案内を継続",
        "D31｜工具退避後に開く。指を開く間、手先位置を保つ。",
        "F-Cの支持形状・保持検出は未確定。",
    ),
    (
        50.85,
        51.9,
        3,
        "② 指を開いたまま上昇",
        "F-C（支持を残す）",
        "直上へ退避",
        "自由端案内を継続",
        "D31｜先に上方へ離し、その後で向きを変える表示。",
        "同じ手先で兼用するか、交換するかは未確定。",
    ),
    (
        51.9,
        52.5,
        4,
        "③ 上方で向き・開き幅を変更",
        "F-C（支持を残す）",
        "搬送把持へ切替える表示",
        "自由端案内を継続",
        "D31｜上方の姿勢で搬送把持へ切り替える。",
        "H07 → ユニット用手先：実際の切替方式は未確定。",
    ),
    (
        52.5,
        53.9,
        4,
        "④ 開いた指を把持位置へ下ろす",
        "F-C（支持を残す）",
        "搬送把持位置へ接近",
        "自由端案内を継続",
        "D31｜開いたまま下降し、把持位置へ合わせる。",
        "ユニット用の把持面と爪形状は未確定。",
    ),
    (
        53.9,
        55,
        3,
        "⑤ 搬送把持を開始",
        "F-C＋C主担当",
        "位置を保って閉じる",
        "自由端案内を継続",
        "D31 → D40｜搬送保持を開始してからユニットを上げる。",
        "保持確認は必要な手順。検出済み信号の表示ではない。",
    ),
    (
        55,
        61.6,
        7,
        "本体と自由端を分担して搬送",
        "C主担当",
        "ユニット本体を搬送",
        "線・端末を別に案内",
        "D40｜ユニット本体と自由端の担当を分けて筐体へ運ぶ。",
        "代表線の描画。全端末を一つの手で保持する仕様ではない。",
    ),
    (
        61.6,
        62.04,
        3,
        "筐体側の受けへ支持を渡す",
        "C主担当 → 筐体側の受け",
        "着座位置で保持",
        "自由端案内を継続",
        "D40｜筐体側の支持へ引き継いでから搬送指を開く。",
        "受け・着座・保持確認の実装は未確定。",
    ),
    (
        62.04,
        63,
        4,
        "搬送指を開いて上方へ退避",
        "筐体側の受け",
        "開放 → 上方退避",
        "自由端案内を継続",
        "D40｜主担当の指を抜いても、自由端の案内は続ける。",
        "指の抜けと周囲の干渉は、実形状での確認が残る。",
    ),
    (
        63,
        64,
        3,
        "搭載後も自由端の担当を残す",
        "筐体側の受け",
        "後続作業へ引継ぎ",
        "自動的に空き扱いにしない",
        "D40 → D42｜自由端が次の支持へ移るまで担当を確保。",
        "未特定の筐体内作業は、施工動作を表示しない。",
    ),
]


def samples() -> list[dict]:
    result = []
    for step, (start, stop, duration, *_rest) in enumerate(STEPS):
        indices = np.rint(np.linspace(start * 15, stop * 15, duration * 15, endpoint=False)).astype(int)
        result.extend({"step": step, "source_index": int(index)} for index in indices)
    assert len(result) == 810
    return result


def text(draw, xy: tuple[int, int], value: str, size: int, fill="#173B4D") -> None:
    font = ImageFont.truetype(FONT, size)
    box = draw.textbbox(xy, value, font=font)
    assert box[0] >= 0 and box[1] >= 0 and box[2] <= 1896 and box[3] <= 1070, (value, box)
    draw.text(xy, value, font=font, fill=fill)


def compose(source: Path, target: Path, step_index: int, source_index: int) -> None:
    step = STEPS[step_index]
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    for rectangle in ((0, 0, 1919, 191), (1290, 192, 1919, 907), (0, 908, 1919, 1079)):
        draw.rectangle(rectangle, fill="#F2F6F8")
    text(draw, (28, 18), "HVJB v05e｜C工程の支持と持ち替えを段階ごとに再生", 26)
    text(draw, (28, 68), f"{step_index + 1:02d} / 12  {step[3]}", 36)
    for i in range(12):
        x = 28 + i * 156
        draw.rounded_rectangle((x, 137, x + 139, 177), 6, fill="#198772" if i == step_index else "#DDE8ED")
        text(draw, (x + 55, 141), f"{i + 1:02d}", 22, "white" if i == step_index else "#657984")
    draw.rectangle((36, 204, 805, 249), fill="#F2F6F8")
    text(draw, (47, 209), "手先・製品・支持台を表示（腕リンクは省略）", 24)
    text(draw, (1310, 208), "表示する役割分担", 28)
    for row, (label, value) in enumerate(zip(("本体の支持", "C主担当", "C専用補助"), step[4:7], strict=True)):
        y = 278 + row * 149
        draw.rounded_rectangle((1298, y, 1894, y + 128), 8, fill="white", outline="#CBDDE5", width=2)
        text(draw, (1316, y + 17), label, 23, "#637A85")
        text(draw, (1316, y + 63), value, 26, "#177F6D")
    text(draw, (1312, 766), "同じ保存姿勢を、説明用に時間配分。", 23)
    text(draw, (1312, 810), "実ロボットの速度・実タクトではない。", 23)
    text(draw, (1312, 854), f"主工程の {source_index / 15:.2f} 秒に対応", 23, "#637A85")
    draw.rounded_rectangle((25, 913, 1894, 1015), 8, fill="white", outline="#CBDDE5", width=2)
    text(draw, (44, 928), step[7], 27)
    text(draw, (44, 973), step[8], 25, "#637A85")
    text(draw, (30, 1033), "支持の分担と動きの説明。把持・締結品質・実機成立の判定ではありません。", 23, "#637A85")
    image.save(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    delta = json.loads((ROOT / "audit/motion_delta.json").read_text())
    bank = ROOT / "data/concept_v05e.npz"
    assert sha(bank) == delta["output_sha256"]
    pins = {**delta["input_sha256"], str(bank): sha(bank), str(Path(__file__)): sha(Path(__file__))}
    trace = WORK / "hvjb-handoff-trace-v01-20260927/overlay/data/handoff_trace_v01.json"
    pins[str(trace)] = sha(trace)
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    old = load_module("detail_existing_renderer", WORK / "hvjb-line-video-v05b-20260923/render_review.py")
    existing_model = old.Model
    omissions = []

    class DetailModel(existing_model):
        def __init__(self):
            super().__init__()
            for column, name in enumerate(self.names):
                if any(name.startswith(role + "_" + part) for role in self.arms for part in ("link_", "joint_")):
                    self.scene.remove_node(self.dynamic[column])
                    self.excluded_columns.append(column)
                    omissions.append(name)

    old.Model = DetailModel
    selected = samples()
    if args.preview:
        selected = [next(row for row in selected if row["step"] == i) for i in range(12)]
    indices = np.array(sorted({row["source_index"] for row in selected}))
    plan = json.loads((WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json").read_text())
    subset = {**plan, "expected_source_samples": [plan["expected_source_samples"][int(index)] for index in indices]}
    output = ROOT / "previews" / ("detail_preview" if args.preview else "detail")
    assert not output.exists()
    raw = output / "raw"
    raw.mkdir(parents=True)
    rows, _, text_count = old.render(bank, subset, indices, raw)
    by_index = {row["original_sample_index"]: row for row in rows}
    rendered = []
    for ordinal, selection in enumerate(selected):
        row = by_index[selection["source_index"]]
        path = output / f"{ordinal + 1:05d}.png"
        compose(raw / row["file"], path, selection["step"], selection["source_index"])
        rendered.append({**row, **selection, "file": path.name, "sha256": sha(path)})
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    write(
        output / "manifest.json",
        {
            "complete": True,
            "preview_only": args.preview,
            "input_sha256": pins,
            "images": rendered,
            "omitted_arm_link_and_joint_display_nodes": omissions,
            "existing_camera_unchanged": True,
            "product_and_hand_saved_poses_unchanged": True,
            "text_elements_checked_in_base": text_count,
            "physical_acceptance_verdict": None,
        },
    )
    print(f"C_DETAIL_COMPLETE unique_samples={len(rows)} frames={len(rendered)}", flush=True)


if __name__ == "__main__":
    main()
