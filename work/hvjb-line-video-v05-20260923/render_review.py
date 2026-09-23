# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Render corrected schematic samples; reuse identical v04 engineering PNGs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
V04 = ROOT.parent / "hvjb-line-video-v04-20260923"
CORRECTION = ROOT.parent / "hvjb-display-continuity-v01-20260923"
spec = importlib.util.spec_from_file_location("v04_composition", V04 / "render_review.py")
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)


def preview_indices(plan):
    selections = {
        "S03": (11.2, 11.7, 12.1, 12.5, 13.1),
        "S04": (20.5, 21.1, 21.5, 21.9),
        "S05": (27.65, 27.9, 28.25, 28.8, 29, 34.4, 34.8),
        "S06": (35.2, 35.7, 36),
        "S12": (55, 55.4, 55.8, 56.1, 56.4),
    }
    result = []
    for row in plan["scenes"]:
        for source_t in selections.get(row["id"], ()):
            begin, end = row["source_clock"]
            video_t = row["start_s"] + (source_t - begin) / (end - begin) * (row["stop_s"] - row["start_s"])
            result.append(round(video_t * 15))
    return np.array(sorted(set(result)))


def prepare(name, preview):
    delta_path = CORRECTION / "audit/display_v05_delta.json"
    delta = json.loads(delta_path.read_text())
    framing_path = ROOT / "audit/camera_framing.json"
    framing = json.loads(framing_path.read_text())
    assert framing["source_sha256"] == delta["output_bank_sha256"]
    bank = ROOT / "data/concept_display_v05_framed.npz"
    assert view.sha(bank) == framing["output_sha256"]
    old_plan = json.loads((V04 / "data/concept_v04.json").read_text())
    indices = preview_indices(old_plan) if preview else np.arange(1785)
    plan = dict(old_plan)
    plan.update(
        authored_motion_kind="v03_schematic_with_six_local_display_transition_corrections",
        motion=bank.name,
        motion_sha256=view.sha(bank),
        renderer=str(Path(__file__)),
        frame_end=len(indices) * 2,
        expected_source_samples=[dict(old_plan["expected_source_samples"][int(index)]) for index in indices],
        scope_caption="HVJB 全体工程 v05｜左：模式動作 / 右：完成状態の部品照合図 / 実機仕様・実タクトは未確定",
        output_name=name,
        preview_only=preview,
        saved_geometry_or_motion_modified=True,
        product_geometry_and_motion_modified=False,
        correction_receipt_sha256=view.sha(delta_path),
        framing_receipt_sha256=view.sha(framing_path),
    )
    extra_sources = [
        Path(__file__),
        V04 / "render_review.py",
        V04 / "previews/concept_v04/manifest.json",
        CORRECTION / "correct_display.py",
        CORRECTION / "audit/correction_verification.json",
        delta_path,
        framing_path,
        ROOT / "prepare_camera.py",
        bank,
    ]
    plan["input_sha256"] = {**old_plan["input_sha256"], **{str(path): view.sha(path) for path in extra_sources}}
    return bank, plan, indices


def render(bank, plan, indices, directory):
    with np.load(bank, allow_pickle=False) as saved:
        matrices, cameras, spans, times, names = [
            saved[key] for key in ("matrices", "camera", "span", "time_s", "object_names")
        ]
    with np.load(V04 / "data/concept_v03_reused.npz", allow_pickle=False) as saved:
        unchanged = np.all(matrices == saved["matrices"], axis=(1, 2, 3)) & (spans == saved["span"])
        assert np.array_equal(cameras, saved["camera"])
        assert np.array_equal(times, saved["time_s"]) and np.array_equal(names, saved["object_names"])
    old_manifest = json.loads((V04 / "previews/concept_v04/manifest.json").read_text())
    model = view.old.Model()
    assert model.names == names.tolist()
    composition = view.Composition(json.loads((view.DOCUMENT / "data/line_review_data.json").read_text()))
    renderer = view.old.base.pyrender.OffscreenRenderer(view.old.WIDTH, view.old.HEIGHT)
    rows, reused = [], 0
    try:
        for number, index in enumerate(indices):
            png = directory / f"{number + 1:05d}.png"
            if unchanged[index]:
                source = V04 / "previews/concept_v04" / old_manifest["images"][index]["file"]
                assert view.sha(source) == old_manifest["images"][index]["sha256"]
                shutil.copy2(source, png)
                reused += 1
            else:
                for node, pose in zip(model.dynamic, matrices[index], strict=True):
                    model.scene.set_pose(node, pose)
                model.scene.set_pose(model.camera, cameras[index])
                model.camera.camera.xmag = spans[index]
                model.camera.camera.ymag = spans[index] * view.old.HEIGHT / view.old.WIDTH
                color, depth = renderer.render(model.scene)
                assert np.isfinite(depth).all() and np.count_nonzero(depth) > 1000
                points = {name: matrices[index, model.names.index(name + "_palm"), :3, 3] for name in model.arms}
                composition.compose(color, float(times[index]), cameras[index], spans[index], points).save(png)
            rows.append(
                dict(
                    plan["expected_source_samples"][number],
                    view="process",
                    frame=number * 2 + 1,
                    camera=plan["camera"],
                    file=png.name,
                    sha256=view.sha(png),
                    display_segment="saved_sample",
                    original_sample_index=int(index),
                    unchanged_v04_png_reused=bool(unchanged[index]),
                )
            )
            if number % 60 == 0 or number == len(indices) - 1:
                print(f"V05_PROCESS_PNG {number + 1}/{len(indices)} reused={reused}", flush=True)
    finally:
        renderer.delete()
    return rows, reused, len(composition.text_bounds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output_name", default="concept_v05")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    directory = ROOT / "previews" / args.output_name
    plan_path = ROOT / "data" / f"{args.output_name}.json"
    assert not directory.exists() and not plan_path.exists()
    for folder in ("data", "previews", "audit"):
        (ROOT / folder).mkdir(exist_ok=True)
    bank, plan, indices = prepare(args.output_name, args.preview)
    for path, digest in plan["input_sha256"].items():
        assert view.sha(Path(path)) == digest, path
    view.save(plan_path, plan)
    directory.mkdir()
    rows, reused, text_count = render(bank, plan, indices, directory)
    for path, digest in plan["input_sha256"].items():
        assert view.sha(Path(path)) == digest, path
    view.save(
        directory / "manifest.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "complete": True,
            "source_kind": plan["source_kind"],
            "output_fps": 15,
            "settings": {"width": 1920, "height": 1080},
            "shot_plan_sha256": view.sha(plan_path),
            "renderer_sha256": view.sha(Path(__file__)),
            "input_sha256_current": plan["input_sha256"],
            "images": rows,
            "unchanged_pngs_reused": reused,
            "rerendered_pngs": len(rows) - reused,
            "text_elements_checked": text_count,
            "physical_acceptance_verdict": None,
        },
    )
    print(f"V05_PROCESS_COMPLETE frames={len(rows)} rendered={len(rows) - reused} reused={reused}")


if __name__ == "__main__":
    main()
