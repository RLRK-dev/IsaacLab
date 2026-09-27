# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Assemble one process PNG sequence, preserving source identity for every output frame."""

from __future__ import annotations

import json
import os
from pathlib import Path

from build_motion import ROOT, WORK, load_module, sha, write
from c_detail import STEPS, text
from PIL import Image, ImageDraw

NAME = "concept_v05e"
IDENTITY = ("feature_id", "saved_frame", "saved_bank_index", "saved_time_s")


def main_labels(source: Path, target: Path, time: float, plan: dict) -> None:
    picture = Image.open(source).convert("RGB")
    assert picture.size == (1920, 1080)
    draw = ImageDraw.Draw(picture)
    text(draw, (28, 17), "HVJB 全体工程 v05e｜模式動作と完成状態の照合図｜後半：把持・受渡し・C持ち替えの説明", 24)
    phase = next(row for row in plan["phases"] if row["start_s"] <= time < row["stop_s"])
    label = phase["label"]
    if 50 <= time < 55:
        label = "C持ち替え｜" + next(row[3] for row in STEPS[3:8] if row[0] <= time < row[1])
    text(draw, (30, 1029), label, 26)
    picture.save(target)


def append_main(old, directory: Path, manifest: dict, plan: dict) -> list[dict]:
    records = []
    assert len(manifest["images"]) == 1785
    for index, row in enumerate(manifest["images"]):
        source = ROOT / "previews/main" / row["file"]
        assert sha(source) == row["sha256"]
        target = directory / f"{index + 1:05d}.png"
        main_labels(source, target, index / 15, plan)
        identity = {key: row[key] for key in IDENTITY}
        records.append(old.frame_record(identity, target, index, source, "MAIN", "v05e_saved_sample"))
        if index % 150 == 0:
            print(f"C_ASSEMBLE_MAIN {index + 1}/1785", flush=True)
    return records


def append_detail(old, records: list, directory: Path, manifest: dict) -> None:
    assert len(manifest["images"]) == 810
    for row in manifest["images"]:
        source = ROOT / "previews/detail" / row["file"]
        assert sha(source) == row["sha256"]
        target = directory / f"{len(records) + 1:05d}.png"
        os.link(source, target)
        identity = {key: row[key] for key in IDENTITY}
        record = old.frame_record(identity, target, len(records), source, "C_DETAIL", "saved_pose_explanation")
        records.append({**record, "detail_step": row["step"], "source_index": row["source_index"]})


def main() -> None:
    directory = ROOT / "previews" / NAME
    assert not directory.exists()
    old_path = WORK / "hvjb-line-video-v05c-20260924/assemble_frames.py"
    old = load_module("existing_frame_composition", old_path)
    old.H06, old.H05 = ROOT / "inputs/H06", ROOT / "inputs/H05"
    paths = {
        "main": ROOT / "previews/main/manifest.json",
        "H06": ROOT / "inputs/H06/output/process/manifest.json",
        "H05": ROOT / "inputs/H05/output/process/manifest.json",
        "detail": ROOT / "previews/detail/manifest.json",
    }
    manifests = {name: json.loads(path.read_text()) for name, path in paths.items()}
    pins = {}
    for manifest in manifests.values():
        pins.update(manifest.get("input_sha256", manifest.get("source_sha256", {})))
    plan_path = WORK / "hvjb-line-video-v05b-20260923/data/concept_v05b.json"
    extra = [*paths.values(), plan_path, old_path, Path(__file__), ROOT / "c_detail.py", ROOT / "render_local.py"]
    pins.update({str(path): sha(path) for path in extra})
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    plan = json.loads(plan_path.read_text())
    directory.mkdir()
    records = append_main(old, directory, manifests["main"], plan)
    old.append_h06(records, directory, manifests["H06"])
    old.append_h05(records, directory, manifests["H05"])
    append_detail(old, records, directory, manifests["detail"])
    assert len(records) == 3138
    chapters = [
        *old.CHAPTERS,
        {"id": "C_DETAIL", "start_s": 155.2, "stop_s": 209.2, "label_ja": "C工程の受渡し・持ち替え・搭載"},
    ]
    start = 155.2
    detail_steps = []
    for step, row in enumerate(STEPS):
        detail_steps.append({"step": step + 1, "start_s": start, "stop_s": start + row[2], "label_ja": row[3]})
        start += row[2]
    assert abs(start - 209.2) < 1e-9
    bundle = ROOT / "data/video_source_bundle.json"
    write(
        bundle,
        {
            "kind": "saved_main_and_local_display_sources",
            "sources": {name: {"path": str(path), "sha256": sha(path)} for name, path in paths.items()},
            "chapters": chapters,
            "C_detail_steps": detail_steps,
            "H05_display": "Unchanged saved poses; 3 repeats plus 18 extra first/last frames.",
            "H06_display": "Unchanged comparison endpoints and original display interpolation.",
            "C_detail_display": "Arm link/joint display nodes omitted; original camera and saved hand/product poses.",
            "physical_acceptance_verdict": None,
        },
    )
    pins[str(bundle)] = sha(bundle)
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    updated = {
        **plan,
        "motion": bundle.name,
        "motion_sha256": sha(bundle),
        "renderer": str(Path(__file__)),
        "input_sha256": pins,
        "expected_source_samples": [{key: row[key] for key in IDENTITY} for row in records],
        "frame_end": len(records) * 2,
        "camera": old.CAMERA,
        "scope_caption": "",
        "phases": [],
        "captions_baked_in_process_pngs": True,
        "chapters": chapters,
        "C_detail_steps": detail_steps,
        "preview_only": False,
        "output_name": NAME,
        "repeat_each_source_sample": 1,
        "authored_motion_kind": "v05e_c_regrip_display_and_existing_local_comparisons",
        "saved_geometry_or_motion_modified": True,
        "product_geometry_and_motion_modified": False,
        "motion_delta": str(ROOT / "audit/motion_delta.json"),
        "real_takt": False,
    }
    updated_plan = ROOT / "data" / f"{NAME}.json"
    write(updated_plan, updated)
    write(
        directory / "manifest.json",
        {
            "complete": True,
            "source_kind": "saved_geometry_samples",
            "output_fps": 15,
            "settings": {"width": 1920, "height": 1080},
            "shot_plan_sha256": sha(updated_plan),
            "renderer_sha256": sha(Path(__file__)),
            "input_sha256_current": pins,
            "images": records,
            "captions_baked_in_process_pngs": True,
            "frame_count": len(records),
            "physical_acceptance_verdict": None,
        },
    )
    print("C_ASSEMBLE_COMPLETE frames=3138 duration=209.2 main=1785 H06=300 H05=243 C_detail=810", flush=True)


if __name__ == "__main__":
    main()
