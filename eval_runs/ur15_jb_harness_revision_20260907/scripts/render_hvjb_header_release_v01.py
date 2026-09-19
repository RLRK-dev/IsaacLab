# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Render every saved H05 release sample as process PNGs [m, rad, s]."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyrender
from PIL import Image
from render_hvjb_header_workpiece_v01 import ROOT, _geometry, _look_at, _mesh, _read, _sha

OBSERVATION = "audit/hvjb_header_release_v01.json"
PLAN = "data/hvjb_header_release_v01_presentation.json"
CAMERA = "H05_saved_release_process"
LABELS = {"held": "保持位置", "opening": "指を開く", "upward_withdrawal": "開放後に上へ退避"}


def _hand_parts(hand: dict, bank, model: dict, sample: dict) -> list:
    index = sample["bank_index"]
    translation = np.asarray(model["derived_translation_m"])
    parts = []
    for name, row in hand["objects"].items():
        matrix = bank["OP020_hand_" + name][index]
        vertices = np.asarray(row["vertices"]) @ matrix[:3, :3].T + matrix[:3, 3] + translation
        parts.append(_mesh({"vertices": vertices, "faces": row["faces"]}, row["category"]))
    points = np.concatenate([part.vertices for part in parts])
    assert np.max(abs(np.array([points.min(axis=0), points.max(axis=0)]) - sample["hand_bounds_product_m"])) < 1e-10
    assert sum(len(part.faces) for part in parts) == model["hand_triangles"]
    assert int(bank["frames"][index]) == sample["saved_frame"]
    assert float(bank["time_s"][index]) == sample["saved_time_s"]
    assert float(bank["gripper_q"][index]) == sample["gripper_q_rad"]
    return parts


def _context(product: dict, feature: str) -> list:
    parts = []
    for identifier in ("P01", "P16", "P17"):
        for row in product[identifier]["meshes"]:
            if identifier == "P01":
                category = "case"
            elif "official_CAD" not in row["name"]:
                category = "screw"
            else:
                category = "header" if identifier == feature else "neighbor"
            parts.append(_mesh(row, category))
    return parts


def _camera(observation: dict, product: dict) -> tuple[np.ndarray, float]:
    """Fit all observed hand bounds and context to one fixed camera; padding is display-only [m]."""
    arrays = [np.asarray(row["vertices"]) for key in ("P01", "P16", "P17") for row in product[key]["meshes"]]
    for model in observation["models"]:
        for sample in model["samples"]:
            bounds = np.asarray(sample["hand_bounds_product_m"])
            arrays.append(
                np.array([[bounds[x, 0], bounds[y, 1], bounds[z, 2]] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
            )
    points = np.concatenate(arrays)
    focus = (points.min(axis=0) + points.max(axis=0)) / 2
    matrix = _look_at(focus + np.array([0.35, -1.0, 0.3]), focus)
    projected = (points - focus) @ matrix[:3, :3]
    xmag = 1.15 * max(float(abs(projected[:, 0]).max()), float(abs(projected[:, 1]).max()) * 1280 / 720)
    return matrix, xmag


def _render_all(directory: Path, observation: dict, product: dict, source: dict) -> tuple[list, dict]:
    matrix, xmag = _camera(observation, product)
    renderer = pyrender.OffscreenRenderer(1280, 720)
    images = []
    try:
        with np.load(ROOT / observation["workpiece_settings"]["motion_bank"], allow_pickle=False) as bank:
            for model in observation["models"]:
                feature = model["feature_id"]
                scene = pyrender.Scene(bg_color=[0.955, 0.971, 0.980, 1], ambient_light=[0.48] * 3)
                for part in _context(product, feature):
                    scene.add(pyrender.Mesh.from_trimesh(part, smooth=False))
                scene.add(
                    pyrender.OrthographicCamera(xmag=xmag, ymag=xmag * 720 / 1280, znear=0.01, zfar=5), pose=matrix
                )
                for offset, intensity in (([0.3, -1.1, 1.3], 3.0), ([-0.7, -0.6, 0.4], 1.3)):
                    scene.add(
                        pyrender.DirectionalLight(color=np.ones(3), intensity=intensity),
                        pose=_look_at(np.asarray(offset), np.array([0, 0, 0.15])),
                    )
                for sample in model["samples"]:
                    nodes = [
                        scene.add(pyrender.Mesh.from_trimesh(part, smooth=False))
                        for part in _hand_parts(source["hand"], bank, model, sample)
                    ]
                    color, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
                    assert np.isfinite(depth).all() and np.count_nonzero(depth) > 0
                    filename = f"{feature}_{sample['saved_frame']:04d}.png"
                    Image.fromarray(color).save(directory / filename)
                    images.append(
                        {
                            "feature_id": feature,
                            "saved_frame": sample["saved_frame"],
                            "saved_bank_index": sample["bank_index"],
                            "saved_time_s": sample["saved_time_s"],
                            "source_phase": sample["source_phase"],
                            "file": filename,
                            "sha256": _sha(directory / filename),
                            "foreground_pixels": int(np.count_nonzero(depth)),
                        }
                    )
                    for node in nodes:
                        scene.remove_node(node)
                    print("HEADER_RELEASE_PNG", feature, sample["saved_frame"], flush=True)
    finally:
        renderer.delete()
    return images, {"matrix_world": matrix.tolist(), "horizontal_span_m": 2 * xmag}


def _sequence(images: list, settings: dict) -> tuple[list, list]:
    repeat = round(1 / settings["review_playback_rate"])
    pause = round(settings["review_endpoint_pause_s"] * 15)
    sequence, phases = [], []
    for feature in ("P16", "P17"):
        group = [row for row in images if row["feature_id"] == feature]
        entries = [(group[0], "pause_before")] * pause
        entries.extend((row, "saved_sample") for row in group for _ in range(repeat))
        entries.extend([(group[-1], "pause_after")] * pause)
        for row, segment in entries:
            label = LABELS[row["source_phase"]]
            if segment != "saved_sample":
                label = "開始姿勢（静止表示）" if segment == "pause_before" else "退避後（静止表示）"
            label = f"{'3口' if feature == 'P16' else '2口'}ヘッダー｜{label}｜保存姿勢を0.5倍速表示"
            index = len(sequence)
            if not phases or phases[-1]["label"] != label:
                phases.append({"start_s": index / 15, "stop_s": (index + 1) / 15, "label": label})
            else:
                phases[-1]["stop_s"] = (index + 1) / 15
            sequence.append(dict(row, view="process", frame=index * 2 + 1, camera=CAMERA, display_segment=segment))
    return sequence, phases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.output_directory.resolve()
    assert not directory.exists() and not (ROOT / PLAN).exists()
    report = _read(OBSERVATION)
    pins = report["input_sha256_current"] | {OBSERVATION: _sha(ROOT / OBSERVATION)}
    for path in (
        "scripts/render_hvjb_header_release_v01.py",
        "scripts/encode_process_review_video.py",
        "scripts/collect_saved_geometry_review.py",
        "scripts/encode_op030_v02.py",
        "data/video_delivery_policy.json",
    ):
        pins[path] = _sha(ROOT / path)
    assert all(_sha(ROOT / path) == sha for path, sha in pins.items())
    directory.mkdir(parents=True, exist_ok=False)
    settings = report["workpiece_settings"]
    images, camera = _render_all(
        directory, report, _geometry(settings["product_meshes"]), _geometry(settings["hand_meshes"])
    )
    sequence, phases = _sequence(images, report["settings"])
    after = {path: _sha(ROOT / path) for path in pins}
    assert after == pins
    expected = [
        {key: row[key] for key in ("feature_id", "saved_frame", "saved_bank_index", "saved_time_s")} for row in images
    ]
    plan = {
        "source_kind": "saved_geometry_samples",
        "native": None,
        "native_sha256": None,
        "motion": settings["motion_bank"].removeprefix("data/"),
        "motion_sha256": pins[settings["motion_bank"]],
        "input_sha256": pins,
        "renderer": "scripts/render_hvjb_header_release_v01.py",
        "camera": CAMERA,
        "frame_end": len(sequence) * 2,
        "expected_source_samples": expected,
        "repeat_each_source_sample": 2,
        "scope_caption": "H05 開放・退避の局所確認｜工具・腕・配線は対象外／実機成立は未判定",
        "phase_prefix": "",
        "phases": phases,
    }
    with (ROOT / PLAN).open("x") as stream:
        json.dump(plan, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    manifest = {
        "observed_at": datetime.now(UTC).isoformat(),
        "source_kind": plan["source_kind"],
        "complete": True,
        "output_fps": 15,
        "settings": {"width": 1280, "height": 720, "camera": camera},
        "shot_plan_sha256": _sha(ROOT / PLAN),
        "renderer_sha256": pins[plan["renderer"]],
        "input_sha256_current": after,
        "images": sequence,
        "unique_source_sample_count": len(images),
        "source_motion_recomputed": False,
        "source_geometry_modified": False,
        "native_saved": False,
        "physical_acceptance_verdict": None,
    }
    with (directory / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("HEADER_RELEASE_PROCESS_PNGS_COMPLETE", len(images), len(sequence), directory, flush=True)


if __name__ == "__main__":
    main()
