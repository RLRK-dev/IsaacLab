# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Build a process correspondence from preserved observations, without moving meshes."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_photo_catalog_v01 import digest

ROOT = Path(__file__).resolve().parents[1]
STEM = "hvjb_preassembly"
CATALOG = "data/hvjb_photo_correspondence_v03_p01.json"
EVIDENCE = "data/hvjb_video_evidence_v02.json"
INPUT = f"data/{STEM}_inputs_v01.json"
OUTPUT = f"data/{STEM}_process_v01.json"
AUDIT = f"audit/{STEM}_review_v01.json"
PINNED = {
    CATALOG: "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    "UR15_JB_photo_correspondence_v03_p02.blend": ("3da72f4c042936da0e168b71977fe09dbb1c2057eb5d0da30b215522a8ef004d"),
}
FEATURE_COLLECTIONS = ("parts", "visible_fastener_features", "visible_wire_segments")
PRESERVED_FIELDS = (
    *FEATURE_COLLECTIONS,
    "required_functions",
    "electrical_groups",
    "lv_pin_map",
    "assembly_dependencies",
    "documented_header_mounting",
    "unresolved",
    "remaining_visual_coverage",
    "retired_visible_wire_segments",
    "candidate_continuations",
    "all_physical_connections_resolved",
    "all_visible_features_traced",
)


def read_json(relative: str) -> dict:
    """Read an existing local JSON input."""
    return json.loads((ROOT / relative).read_text())


def write_new_json(path: Path, value: dict) -> None:
    """Write a new JSON artifact, refusing to replace an existing revision."""
    with path.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def feature_correspondence(inputs: dict, catalog: dict) -> list[dict]:
    """List every registered feature once without assigning unknown physical joints."""
    source = {row["id"]: row for key in FEATURE_COLLECTIONS for row in catalog[key]}
    expected_count = sum(len(catalog[key]) for key in FEATURE_COLLECTIONS)
    assert len(source) == expected_count, "Duplicate source feature IDs"
    result = []
    for group in inputs["feature_groups"]:
        ids = group.get("ids")
        if ids is None:
            ids = [row["id"] for row in catalog[group["catalog_collection"]]]
        for identifier in ids:
            row = source[identifier]
            result.append(
                {
                    "id": identifier,
                    "name_ja": row.get("name_ja", f"可視締結特徴 {identifier}"),
                    "group": group["id"],
                    "group_name_ja": group["name_ja"],
                    "candidate_cells": group["cells"],
                    "basis_ja": group["basis_ja"],
                    "unresolved_ja": group["unresolved_ja"],
                    "physical_operation_selected": None,
                }
            )
    assigned = [row["id"] for row in result]
    assert len(set(assigned)) == len(assigned), "A feature was assigned twice"
    assert set(assigned) == set(source), "Missing or invented feature ID"
    valid_cells = {row["id"] for row in inputs["cells"]} | {"SUPPLY", "PREP", "AFTER"}
    assert all(set(row["candidate_cells"]) <= valid_cells for row in result)
    assert len({row["id"] for row in inputs["operations"]}) == len(inputs["operations"])
    return result


def prepare() -> tuple[dict, dict, dict]:
    """Verify evidence identities and assemble a non-geometric correspondence."""
    inputs, catalog, evidence = read_json(INPUT), read_json(CATALOG), read_json(EVIDENCE)
    expected = dict(PINNED)
    video = evidence["sources"]["assembly_20250607"]
    expected[video["file"]] = video["sha256"]
    for observation in inputs["observations"]:
        frame = evidence["frames"][observation["frame"]]
        expected[frame["file"]] = frame["sha256"]
    identities = {relative: digest(ROOT / relative) for relative in expected}
    assert identities == expected, "A preserved source differs from the evidence record"
    report = copy.deepcopy(inputs)
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    report["source_catalog"] = {"file": CATALOG, "sha256": expected[CATALOG]}
    report["source_video"] = copy.deepcopy(video)
    report["source_video_evidence"] = copy.deepcopy(evidence)
    report["feature_correspondence"] = feature_correspondence(inputs, catalog)
    report["preserved_catalog_fields"] = {key: copy.deepcopy(catalog[key]) for key in PRESERVED_FIELDS}
    report["coverage_note_ja"] = "登録IDを照合欄へ網羅した数。全BOM・全配線・工程設計の完了率ではない。"
    report["source_files_sha256"] = identities
    for observation in report["observations"]:
        frame = evidence["frames"][observation["frame"]]
        observation["local_image"] = f"evidence/{Path(frame['file']).name}"
        observation["source_url"] = f"{video['url']}&t={frame['requested_seek_s']}s"
    return report, catalog, identities


def package(directory: Path, report: dict) -> list[dict]:
    """Copy source observations and create the offline process review page."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    copied = []
    paths = {
        INPUT: "inputs.json",
        OUTPUT: "process_correspondence.json",
        f"analysis/{STEM}_process_v01.md": "process_notes.md",
        "references/op040_real_products_20260912/ampere_product_photo_1.jpg": "evidence/target_photo_2022.jpg",
    }
    for observation in report["observations"]:
        frame = report["source_video_evidence"]["frames"][observation["frame"]]
        paths[frame["file"]] = observation["local_image"]
    for relative, target in paths.items():
        source, destination = ROOT / relative, directory / target
        shutil.copy2(source, destination)
        assert digest(source) == digest(destination), target
        copied.append({"source": relative, "file": target, "sha256": digest(destination)})
    template = (ROOT / f"scripts/{STEM}_review_v01.html").read_text()
    payload = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    assert template.count("__PAYLOAD__") == 1
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    (directory / "README.txt").write_text(
        "HVJB 外組み工程の照合 v01\nreview.html をブラウザーで開いてください。\n"
        "公式の外組み・筐体搭載・後付けの場面と、3セルの比較案です。\n"
        "92特徴の参照、17必須機能区分、13接続群、LV12極を継承しています。全BOMの完成ではありません。\n"
        "下板、板同士の結合、自由端受渡し、実端末等の未確定事項を残しています。\n"
        "旧native・動画は変更していません。新たな工程動画や物理成立判定は含みません。\n"
    )
    return copied


def main() -> None:
    """Build one new process review without overwriting earlier files."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("/home/rlrk/Downloads/THREAD_HVJB_外組み工程_v01_20260916"),
    )
    args = parser.parse_args()
    for path in (ROOT / OUTPUT, ROOT / AUDIT, args.output_dir):
        assert not path.exists(), f"Refusing to overwrite {path}"
    report, catalog, before = prepare()
    write_new_json(ROOT / OUTPUT, report)
    copied = package(args.output_dir, report)
    after = {relative: digest(ROOT / relative) for relative in before}
    assert before == after, "A source changed while creating the process review"
    preserved = report["preserved_catalog_fields"]
    assert all(preserved[key] == catalog[key] for key in PRESERVED_FIELDS)
    counts = {key: len(catalog[key]) for key in FEATURE_COLLECTIONS}
    audit = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "directory": str(args.output_dir),
        "registered_feature_counts": counts,
        "feature_reference_rows": len(report["feature_correspondence"]),
        "source_feature_id_set_matches": True,
        "all_preserved_catalog_fields_equal": True,
        "required_function_rows": len(preserved["required_functions"]),
        "electrical_group_rows": len(preserved["electrical_groups"]),
        "lv_pin_rows": len(preserved["lv_pin_map"]),
        "operation_rows": len(report["operations"]),
        "source_hashes_before": before,
        "source_hashes_after": after,
        "copied_inputs": copied,
        "generated_page_sha256": digest(args.output_dir / "review.html"),
        "process_json_sha256": digest(ROOT / OUTPUT),
        "source_model_written": False,
        "movie_created": False,
        "full_bom_or_process_completion_claim": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print(
        "PREASSEMBLY_REVIEW",
        f"features={audit['feature_reference_rows']}",
        f"requirements={audit['required_function_rows']}",
        f"groups={audit['electrical_group_rows']}",
        f"pins={audit['lv_pin_rows']}",
        "sources_unchanged=True",
        "movie_created=False",
        flush=True,
    )
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
