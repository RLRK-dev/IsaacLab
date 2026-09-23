# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Compose complete main-process PNGs and preserved local views for one review encoding."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OLD = WORK / "hvjb-line-video-v05b-20260923"
H06 = WORK / "hvjb-h06-motion-review-v01-20260924"
H05 = WORK / "hvjb-h05-motion-review-v01-20260924"
FIX = WORK / "hvjb-xyz-display-v01-20260924"
FONT = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
NAME = "concept_v05c"
CAMERA = "identified_main_process_and_fixed_local_comparison_views"
CHAPTERS = [
    {"id": "MAIN", "start_s": 0, "stop_s": 119, "label_ja": "ライン全体・20仕事"},
    {"id": "H06_loading", "start_s": 119, "stop_s": 129, "label_ja": "H06 空筐体の載置と開放"},
    {"id": "H06_pickup", "start_s": 129, "stop_s": 139, "label_ja": "H06 再把持と取出し"},
    {"id": "H05_P16", "start_s": 139, "stop_s": 147, "label_ja": "H05 3口ヘッダーの開放・退避"},
    {"id": "H05_P17", "start_s": 147, "stop_s": 155.2, "label_ja": "H05 2口ヘッダーの開放・退避"},
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, data: dict) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def add_main_labels(path: Path, output: Path, time_s: float, plan: dict) -> None:
    image = Image.open(path).convert("RGB")
    assert image.size == (1920, 1080)
    draw = ImageDraw.Draw(image)
    phase = next(row for row in plan["phases"] if row["start_s"] <= time_s < row["stop_s"])
    lines = [
        ((28, 17), "HVJB 全体工程 v05c｜左：模式動作 / 右：完成状態の部品照合図 / 後半に把持・受渡しの拡大章", 24),
        ((30, 1029), phase["label"], 26),
    ]
    for position, text, size in lines:
        font = ImageFont.truetype(str(FONT), size)
        bounds = draw.textbbox(position, text, font=font)
        assert 0 <= bounds[0] < bounds[2] < 1920 and 0 <= bounds[1] < bounds[3] < 1072
        draw.text(position, text, font=font, fill="#173B4D")
    image.save(output)


def frame_record(identity: dict, target: Path, number: int, source: Path, chapter: str, kind: str) -> dict:
    return {
        **identity,
        "frame": number * 2 + 1,
        "file": target.name,
        "view": "process",
        "camera": CAMERA,
        "sha256": sha(target),
        "display_segment": "saved_sample",
        "display_kind": kind,
        "chapter": chapter,
        "upstream_png": str(source),
        "upstream_png_sha256": sha(source),
    }


def main_frames(directory: Path, original: dict, changed: dict, plan: dict) -> list[dict]:
    replacements = {row["original_sample_index"]: row for row in changed["images"]}
    assert len(original["images"]) == 1785 and len(replacements) == 23
    records = []
    for index, row in enumerate(original["images"]):
        replacement = replacements.get(index)
        selected = replacement or row
        source = (ROOT / "changed_pngs" if replacement else OLD / "previews/concept_v05b") / selected["file"]
        assert sha(source) == selected["sha256"]
        target = directory / f"{index + 1:05d}.png"
        add_main_labels(source, target, index / 15, plan)
        identity = {key: row[key] for key in ("feature_id", "saved_frame", "saved_bank_index", "saved_time_s")}
        records.append(frame_record(identity, target, index, source, "MAIN", "corrected" if replacement else "reused"))
        if index % 150 == 0 or index == 1784:
            print(f"V05C_MAIN_COMPOSE {index + 1}/1785", flush=True)
    return records


def append_h06(records: list[dict], directory: Path, manifest: dict) -> None:
    assert len(manifest["images"]) == 300
    for source_index, row in enumerate(manifest["images"]):
        source = H06 / "output/process" / row["file"]
        assert sha(source) == row["sha256"]
        target = directory / f"{len(records) + 1:05d}.png"
        os.link(source, target)
        feature = "H06_" + row["operation"]
        identity = {
            "feature_id": feature,
            "saved_frame": row["local_frame"],
            "saved_bank_index": source_index,
            "saved_time_s": row["local_time_s"],
        }
        records.append(frame_record(identity, target, len(records), source, feature, "existing_state_interpolation"))


def append_h05(records: list[dict], directory: Path, manifest: dict) -> None:
    for feature, count in (("P16", 28), ("P17", 29)):
        rows = [row for row in manifest["images"] if row["feature"] == feature]
        assert len(rows) == count
        with np.load(H05 / "data" / f"{feature}_saved_release.npz", allow_pickle=False) as saved:
            times, indices = saved["source_time_s"], saved["bank_indices"]
        for index, row in enumerate(rows):
            source = H05 / "output/process" / row["file"]
            assert sha(source) == row["sha256"]
            identity = {
                "feature_id": "H05_" + feature,
                "saved_frame": row["saved_frame"],
                "saved_bank_index": int(indices[index]),
                "saved_time_s": float(times[index]),
            }
            repeats = 3 + (18 if index in (0, count - 1) else 0)
            for _ in range(repeats):
                target = directory / f"{len(records) + 1:05d}.png"
                os.link(source, target)
                records.append(
                    frame_record(identity, target, len(records), source, "H05_" + feature, "saved_pose_hold")
                )


def main() -> None:
    directory = ROOT / "previews" / NAME
    assert not directory.exists() and not (ROOT / "data").exists()
    plan_path = OLD / "data/concept_v05b.json"
    paths = {
        "main_manifest": OLD / "previews/concept_v05b/manifest.json",
        "corrected_manifest": ROOT / "changed_pngs/manifest.json",
        "H06_manifest": H06 / "output/process/manifest.json",
        "H05_manifest": H05 / "output/process/manifest.json",
        "H06_readback": H06 / "audit/sequence_readback.json",
        "H05_readback": H05 / "audit/release_readback.json",
        "display_delta": FIX / "audit/display_delta.json",
    }
    inputs = {name: read(path) for name, path in paths.items()}
    old_plan = read(plan_path)
    pins = {**old_plan["input_sha256"], **{str(path): sha(path) for path in paths.values()}}
    for name in ("corrected_manifest", "H06_manifest", "H05_manifest"):
        pins.update(inputs[name]["source_sha256"])
    pins.update({str(path): sha(path) for path in (plan_path, FONT, Path(__file__), ROOT / "REVIEW_SCOPE.md")})
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    directory.mkdir(parents=True)
    (ROOT / "data").mkdir()
    (ROOT / "audit").mkdir()
    records = main_frames(directory, inputs["main_manifest"], inputs["corrected_manifest"], old_plan)
    append_h06(records, directory, inputs["H06_manifest"])
    append_h05(records, directory, inputs["H05_manifest"])
    assert len(records) == 2328
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    bundle = ROOT / "data/video_source_bundle.json"
    write(
        bundle,
        {
            "kind": "identified_multiple_saved_sources_not_a_new_robot_motion_bank",
            "sources": {name: {"path": str(path), "sha256": sha(path)} for name, path in paths.items()},
            "chapters": CHAPTERS,
            "H05_display_repetition": "3 per pose plus 18 extra first/last frames, with no geometry interpolation",
            "H06_display_interpolation": "Existing comparison states, not a control trajectory",
        },
    )
    pins[str(bundle)] = sha(bundle)
    expected = [
        {key: row[key] for key in ("feature_id", "saved_frame", "saved_bank_index", "saved_time_s")} for row in records
    ]
    plan = {
        **old_plan,
        "motion": bundle.name,
        "motion_sha256": sha(bundle),
        "authored_motion_kind": "saved_main_and_local_comparison_views_with_explicit_display_repetitions",
        "renderer": str(Path(__file__)),
        "input_sha256": pins,
        "expected_source_samples": expected,
        "frame_end": 2 * len(records),
        "camera": CAMERA,
        "scope_caption": "",
        "phases": [],
        "captions_baked_in_process_pngs": True,
        "chapters": CHAPTERS,
        "preview_only": False,
        "output_name": NAME,
        "saved_geometry_or_motion_modified": True,
        "motion_delta": str(paths["display_delta"]),
        "product_geometry_and_motion_modified": False,
        "real_takt": False,
    }
    target_plan = ROOT / "data" / f"{NAME}.json"
    write(target_plan, plan)
    write(
        directory / "manifest.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "complete": True,
            "source_kind": "saved_geometry_samples",
            "output_fps": 15,
            "settings": {"width": 1920, "height": 1080},
            "shot_plan_sha256": sha(target_plan),
            "renderer_sha256": sha(Path(__file__)),
            "input_sha256_current": pins,
            "images": records,
            "captions_baked_in_process_pngs": True,
            "frame_count": len(records),
            "physical_acceptance_verdict": None,
        },
    )
    print("V05C_PROCESS_ASSEMBLED main=1785 H06=300 H05=243 total=2328 duration_s=155.2 videos_created=0", flush=True)


if __name__ == "__main__":
    main()
