# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Extend the process correspondence with source-separated plate observations."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import build_hvjb_preassembly_review_v01 as base

ROOT = base.ROOT
DELTA = "data/hvjb_preassembly_delta_v02.json"
OUTPUT = "data/hvjb_preassembly_process_v02.json"
AUDIT = "audit/hvjb_preassembly_review_v02.json"
PLATE_EVIDENCE_SHA = "2802f20de9ae1265da26830b6abb2995017b0bf71f311cfeabf4425ffd6945ce"


def update_by_id(rows: list[dict], changes: list[dict]) -> None:
    """Apply explicit amendments without dropping the unaffected source fields."""
    by_id = {row["id"]: row for row in rows}
    assert len(by_id) == len(rows), "Duplicate IDs before amendment"
    for amendment in changes:
        assert amendment["id"] in by_id, amendment["id"]
        by_id[amendment["id"]].update(copy.deepcopy(amendment))


def verify_links(report: dict, catalog: dict) -> None:
    """Check observation references and a cycle-free, explicitly partial process graph."""
    frames = report["source_video_evidence"]["frames"]
    entity_ids = {row["id"] for row in report["observed_entities"]}
    feature_ids = {row["id"] for key in base.FEATURE_COLLECTIONS for row in catalog[key]}
    assert len(entity_ids) == len(report["observed_entities"])
    assert not entity_ids & feature_ids, "Video-only entities must not replace photo IDs"
    for entity in report["observed_entities"]:
        assert set(entity["candidate_photo_ids"]) <= feature_ids
        assert set(entity["evidence_frames"]) <= frames.keys()
        assert entity["confirmed_photo_id"] is None
    for observation in report["observations"]:
        width, height = frames[observation["frame"]]["size_px"]
        for marker in observation["markers"]:
            x, y = marker["xy_px"]
            assert 0 <= x < width and 0 <= y < height
            assert marker["entity"] is None or marker["entity"] in entity_ids
    for relation in report["assembly_relations"]:
        assert relation["from"] in entity_ids and relation["to"] in entity_ids
        assert relation["mechanical_joint"] is None
    operations = {row["id"] for row in report["operations"]}
    predecessors = {identifier: set() for identifier in operations}
    for edge in report["process_precedence"]:
        assert edge["from"] in operations and edge["to"] in operations
        predecessors[edge["to"]].add(edge["from"])
    while predecessors:
        ready = {key for key, value in predecessors.items() if not value}
        assert ready, "Cyclic process correspondence"
        predecessors = {key: value - ready for key, value in predecessors.items() if key not in ready}


def prepare() -> tuple[dict, dict, dict]:
    """Preserve all prior feature/electrical records while attaching the new evidence."""
    delta = base.read_json(DELTA)
    report = copy.deepcopy(base.read_json(delta["base_input"]))
    catalog = base.read_json(base.CATALOG)
    prior_evidence = base.read_json(base.EVIDENCE)
    plate = base.read_json(delta["evidence_index"])
    assert base.digest(ROOT / delta["evidence_index"]) == PLATE_EVIDENCE_SHA
    assert plate["source"]["sha256"] == prior_evidence["sources"]["assembly_20250607"]["sha256"]
    for key, value in delta.items():
        if key not in {"base_input", "cell_updates", "operation_updates", "operation_insertions", "interface_updates"}:
            report[key] = copy.deepcopy(value)
    update_by_id(report["cells"], delta["cell_updates"])
    update_by_id(report["operations"], delta["operation_updates"])
    update_by_id(report["open_interfaces"], delta["interface_updates"])
    for addition in delta["operation_insertions"]:
        index = next(i for i, row in enumerate(report["operations"]) if row["id"] == addition["after"])
        report["operations"].insert(index + 1, copy.deepcopy(addition["operation"]))
    evidence = copy.deepcopy(prior_evidence)
    for frame in plate["frames"]:
        key = f"plate_{frame['requested_seek_s']:03d}"
        assert key not in evidence["frames"]
        evidence["frames"][key] = copy.deepcopy(frame)
    report["source_video_evidence"] = evidence
    report["source_plate_evidence"] = copy.deepcopy(plate)
    report["source_video"] = copy.deepcopy(plate["source"])
    report["source_catalog"] = {"file": base.CATALOG, "sha256": base.PINNED[base.CATALOG]}
    report["feature_correspondence"] = base.feature_correspondence(report, catalog)
    report["preserved_catalog_fields"] = {key: copy.deepcopy(catalog[key]) for key in base.PRESERVED_FIELDS}
    report["coverage_note_ja"] = "写真の92特徴を保持。映像の6観察対象は別台帳であり、98部品や全BOMとはしない。"
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    expected = dict(base.PINNED)
    expected[plate["source"]["file"]] = plate["source"]["sha256"]
    for frame in plate["frames"]:
        expected[frame["file"]] = frame["sha256"]
    for observation in report["observations"]:
        frame = evidence["frames"][observation["frame"]]
        expected[frame["file"]] = frame["sha256"]
        observation["local_image"] = f"evidence/{Path(frame['file']).name}"
        observation["source_url"] = f"{plate['source']['url']}&t={frame['requested_seek_s']}s"
    before = {relative: base.digest(ROOT / relative) for relative in expected}
    assert expected == before, "Source identity mismatch"
    report["source_files_sha256"] = before
    verify_links(report, catalog)
    return report, catalog, before


def package(directory: Path, report: dict) -> list[dict]:
    """Package full unchanged source frames and a separate HTML annotation layer."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    paths = {
        DELTA: "revision_inputs.json",
        OUTPUT: "process_correspondence.json",
        "data/hvjb_plate_evidence_v01.json": "plate_evidence.json",
        "analysis/hvjb_preassembly_process_v02.md": "process_notes.md",
        "references/op040_real_products_20260912/ampere_product_photo_1.jpg": "evidence/target_photo_2022.jpg",
    }
    for frame in report["source_plate_evidence"]["frames"]:
        paths[frame["file"]] = f"evidence/{Path(frame['file']).name}"
    for observation in report["observations"]:
        frame = report["source_video_evidence"]["frames"][observation["frame"]]
        paths[frame["file"]] = observation["local_image"]
    copied = []
    for relative, target in paths.items():
        source, destination = ROOT / relative, directory / target
        shutil.copy2(source, destination)
        assert base.digest(source) == base.digest(destination), target
        copied.append({"source": relative, "file": target, "sha256": base.digest(destination)})
    template = (ROOT / "scripts/hvjb_preassembly_review_v02.html").read_text()
    payload = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    assert template.count("__PAYLOAD__") == 1
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    (directory / "README.txt").write_text(
        "HVJB 外組み工程 v02：下板・ヒューズ板と端末引出し\n"
        "review.html を開くと、元映像の場面と観察台帳・工程の対応を確認できます。\n"
        "画像上の番号は表示用。元画像は無加工です。実寸・加工輪郭・把持点ではありません。\n"
        "2022年写真92特徴と、2025年映像の観察対象を別台帳にしています。\n"
        "板同士の固定法、箱内工具の作業点、自由端の自動保持仕様は未確定。\n"
        "旧native・動画は変更していません。工程動作や物理妥当性の判定を含みません。\n"
    )
    return copied


def main() -> None:
    """Build a new revision, refusing to overwrite any existing delivery."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_外組み工程_v02_20260916")
    )
    args = parser.parse_args()
    for path in (ROOT / OUTPUT, ROOT / AUDIT, args.output_dir):
        assert not path.exists(), f"Refusing to overwrite {path}"
    report, catalog, before = prepare()
    base.write_new_json(ROOT / OUTPUT, report)
    copied = package(args.output_dir, report)
    after = {relative: base.digest(ROOT / relative) for relative in before}
    assert before == after, "A source changed while packaging"
    assert all(report["preserved_catalog_fields"][key] == catalog[key] for key in base.PRESERVED_FIELDS)
    audit = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(args.output_dir),
        "registered_feature_counts": {key: len(catalog[key]) for key in base.FEATURE_COLLECTIONS},
        "feature_reference_rows": len(report["feature_correspondence"]),
        "all_preserved_catalog_fields_equal": True,
        "observed_entity_rows_separate_from_photo_bom": len(report["observed_entities"]),
        "review_observations": len(report["observations"]),
        "extracted_plate_frames": len(report["source_plate_evidence"]["frames"]),
        "operation_rows": len(report["operations"]),
        "process_graph_acyclic": True,
        "source_hashes_before": before,
        "source_hashes_after": after,
        "copied_inputs": copied,
        "generated_page_sha256": base.digest(args.output_dir / "review.html"),
        "process_json_sha256": base.digest(ROOT / OUTPUT),
        "source_model_written": False,
        "geometry_created": False,
        "movie_created": False,
        "physical_acceptance_verdict": None,
    }
    base.write_new_json(ROOT / AUDIT, audit)
    base.write_new_json(args.output_dir / "audit.json", audit)
    print(
        "PREASSEMBLY_V02",
        f"photo_features={audit['feature_reference_rows']}",
        f"video_entities={audit['observed_entity_rows_separate_from_photo_bom']}",
        f"operations={audit['operation_rows']}",
        "sources_unchanged=True geometry_created=False movie_created=False",
        flush=True,
    )
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
