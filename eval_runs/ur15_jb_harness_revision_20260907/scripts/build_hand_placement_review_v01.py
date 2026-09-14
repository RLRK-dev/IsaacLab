# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build static hand-role diagrams and the unchanged selected cable-hand view."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from prepare_hand_working_default_v01 import load_working_default

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "data/hand_placement_review_v01.json"
PHOTO_ROOT = "references/op040_real_products_20260912"
PAGE = "工程別_把持位置と工具方向_v01.html"
MODEL_PAGE = "ケーブル保持3D_v01.html"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _read_inputs() -> tuple[dict, dict, dict]:
    config = _json(ROOT / CONFIG)
    for item in config["inputs"]:
        if _sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"Pinned input changed: {item['path']}")
    spec = _json(ROOT / config["inputs"][0]["path"])
    prior = _json(ROOT / config["inputs"][1]["path"])
    return config, spec, prior


def _check_mapping(config: dict, spec: dict) -> dict:
    targets = {row["target_id"] for row in spec["assignments"]}
    profiles = {row["id"] for row in spec["profiles"]}
    if len(targets) != len(spec["assignments"]) or len(profiles) != len(spec["profiles"]):
        raise ValueError("Duplicate target or profile ID")
    if not {f"F{i:02d}" for i in range(1, 11)} <= targets:
        raise ValueError("Existing target omitted")
    if set(config["station_targets"]) != {row["station_ref"] for row in spec["station_coverage"]}:
        raise ValueError("Station correspondence differs")
    for ids in config["station_targets"].values():
        if len(ids) != len(set(ids)) or not set(ids) <= targets:
            raise ValueError("Duplicate or unknown station target")
    schematic = ET.parse(ROOT / config["diagram"]["source_file"]).getroot()
    diagram_ids = [node.attrib["data-profile"] for node in schematic.iter() if "data-profile" in node.attrib]
    if set(diagram_ids) != profiles or len(diagram_ids) != len(profiles):
        raise ValueError("Diagram-to-profile mapping differs")
    return {"targets": sorted(targets), "profiles": sorted(profiles), "station_targets": config["station_targets"]}


def _photo_data(prior: dict, spec: dict) -> tuple[dict, dict, list[str]]:
    photos, paths = {}, []
    for key, row in prior["photos"].items():
        name = f"{PHOTO_ROOT}/{row['file']}"
        if _sha(ROOT / name) != row["sha256"]:
            raise ValueError(f"Photo changed: {name}")
        paths.append(name)
        photos[key] = {
            **row,
            "data_uri": "data:image/jpeg;base64," + base64.b64encode((ROOT / name).read_bytes()).decode(),
        }
    old = {row["id"]: row for row in prior["targets"]}
    target_photos = {}
    for target in spec["assignments"]:
        row = old.get(target["target_id"], {"photo": "overview", "regions_px": []})
        photo, boxes = row["photo"], row["regions_px"]
        width, height = photos[photo]["size_px"]
        if any(not (0 <= x < x + w <= width and 0 <= y < y + h <= height) for x, y, w, h in boxes):
            raise ValueError("Photo rectangle outside source")
        target_photos[target["target_id"]] = {
            "photo": photo,
            "regions_px": boxes,
            "note_ja": "公開写真の部材位置を参照。把持の許容面は別途確認します。",
        }
    return photos, target_photos, paths


def _substitute(template: str, replacements: dict[str, str]) -> str:
    for token, content in replacements.items():
        if template.count(token) != 1:
            raise ValueError(f"Expected one placeholder: {token}")
        template = template.replace(token, content)
    return template


def _packed(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _source_paths(config: dict, photo_paths: list[str]) -> list[str]:
    return [
        CONFIG,
        *(item["path"] for item in config["inputs"]),
        *photo_paths,
        config["diagram"]["source_file"],
        "scripts/hand_placement_viewer_v01.html",
        "scripts/hand_selected_model_viewer_v01.html",
        "scripts/build_hand_placement_review_v01.py",
        "scripts/prepare_hand_working_default_v01.py",
        "analysis/hand_placement_review_v01.md",
        "analysis/hand_provisional_spec_v01.md",
    ]


def _write_pages(output: Path, review: dict, selected: dict, config: dict) -> list[Path]:
    diagram = (ROOT / config["diagram"]["source_file"]).read_text()
    main_page = _substitute(
        (ROOT / "scripts/hand_placement_viewer_v01.html").read_text(),
        {"__SCHEMATIC_SVG__": diagram, "__REVIEW_DATA__": _packed(review)},
    )
    model_page = _substitute(
        (ROOT / "scripts/hand_selected_model_viewer_v01.html").read_text(),
        {"__MESH_PAYLOAD__": _packed(selected)},
    )
    (output / PAGE).write_text(main_page)
    (output / MODEL_PAGE).write_text(model_page)
    mesh = output / "data/hand_default_meshes_v01.json"
    mesh.write_text(json.dumps(selected, ensure_ascii=False, separators=(",", ":")))
    if _json(mesh)["candidates"] != selected["candidates"]:
        raise ValueError("Serialized candidate changed")
    return [output / PAGE, output / MODEL_PAGE, mesh]


def _copy_and_check(output: Path, paths: list[str], selected_record: dict) -> dict:
    before = {path: _sha(ROOT / path) for path in paths}
    for path in paths:
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
        if _sha(target) != before[path]:
            raise ValueError(f"Copy changed: {path}")
    glb = Path(selected_record["input_paths"]["glb"])
    shutil.copy2(glb, output / "hand_clockwise_tilt_T050_v01.glb")
    if _sha(output / "hand_clockwise_tilt_T050_v01.glb") != selected_record["input_sha256"]["glb"]:
        raise ValueError("GLB copy changed")
    for source, name in [
        ("analysis/hand_placement_review_v01.md", "把持位置確認_v01.md"),
        ("analysis/hand_provisional_spec_v01.md", "フィンガ仮仕様_v01.md"),
    ]:
        shutil.copy2(ROOT / source, output / name)
    if before != {path: _sha(ROOT / path) for path in paths}:
        raise ValueError("Source changed during copy")
    return before


def main() -> None:
    """Build a new static review package; selected geometry remains in [m]."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_directory", type=Path, required=True)
    parser.add_argument("--source_directory", type=Path)
    args = parser.parse_args()
    output = args.output_directory.resolve()
    if output.exists():
        raise FileExistsError(output)
    config, spec, prior = _read_inputs()
    mapping = _check_mapping(config, spec)
    photos, target_photos, photo_paths = _photo_data(prior, spec)
    selected, record = load_working_default(ROOT / config["inputs"][2]["path"], args.source_directory)
    review = {"spec": spec, "photos": photos, "target_photos": target_photos, **config}
    output.mkdir(parents=True)
    before = _copy_and_check(output, _source_paths(config, photo_paths), record)
    outputs = _write_pages(output, review, selected, config)
    for key, path in record["input_paths"].items():
        if _sha(Path(path)) != record["input_sha256"][key]:
            raise ValueError("Selected model source changed")
    audit = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "mapping": mapping,
        "source_sha256": before,
        "selected_model": record,
        "target_photo_annotations_preserved": True,
        "unlocated_targets": [key for key, row in target_photos.items() if not row["regions_px"]],
        "serialized_candidate_identical": True,
        "schematic_scale": "none",
        "source_inputs_unchanged": True,
        "output_sha256": {str(path.relative_to(output)): _sha(path) for path in outputs},
        "arm_motion_created": False,
        "video_created": False,
        "physical_acceptance_verdict": None,
    }
    (output / "audit").mkdir(exist_ok=True)
    (output / "audit/hand_placement_build_v01.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print("HAND_PLACEMENT_REVIEW_BUILT", str(output), flush=True)


if __name__ == "__main__":
    main()
