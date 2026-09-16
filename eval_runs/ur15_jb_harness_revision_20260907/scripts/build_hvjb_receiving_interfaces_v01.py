# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bind receiving roles to existing evidence and hand families without choosing grasp poses."""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_assist_handoff_v01 import PINNED as ROLE_PINNED
from build_hvjb_assist_handoff_v01 import SELECTION, WORK
from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_unitization_review_v01 import MODEL, PINNED, PROCESS

STEM = "hvjb_receiving_interfaces_v01"
INPUT = "data/hvjb_receiving_interfaces_inputs_v01.json"
PAGE = f"scripts/{STEM}.html"
HANDS = "data/hand_provisional_spec_v01.json"
EVIDENCE = "data/hvjb_plate_evidence_v01.json"


def model_record(identifier: str, model: dict) -> dict:
    """Read saved display-mesh bounds [m], without inferring manufacturing or grasp dimensions."""
    row = model[identifier]
    vertices = [vertex for mesh in row["meshes"] for vertex in mesh["vertices"]]
    minimum = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    maximum = [max(vertex[axis] for vertex in vertices) for axis in range(3)]
    return {
        "id": identifier,
        "basis": row["basis"],
        "mesh_names": [mesh["name"] for mesh in row["meshes"]],
        "display_aabb_min_m": minimum,
        "display_aabb_max_m": maximum,
        "display_aabb_size_m": [high - low for low, high in zip(minimum, maximum, strict=True)],
        "selected_contact_surfaces": None,
        "world_grasp_pose_m_rad": None,
    }


def resolve_target(target: dict, process: dict, profiles: dict, model: dict) -> None:
    """Attach existing entity records and image markers; do not convert pixels into grasp coordinates."""
    entity = next(row for row in process["observed_entities"] if row["id"] == target["entity"])
    assert entity["confirmed_photo_id"] is None and entity["source_model_object"] is None
    target["entity_record"] = copy.deepcopy(entity)
    target["hand_family"] = copy.deepcopy(profiles[target["profile"]])
    target["model_candidates"] = [model_record(identifier, model) for identifier in entity["candidate_photo_ids"]]
    target["view_data"] = []
    for second in target["views"]:
        observation = next(row for row in process["observations"] if row["frame"] == f"plate_{second:03d}")
        target["view_data"].append(
            {
                "second": second,
                "source_frame": observation["frame"],
                "markers": [copy.deepcopy(m) for m in observation["markers"] if m["entity"] == entity["id"]],
                "observation_ja": observation["observation_ja"],
                "limit_ja": observation["limit_ja"],
            }
        )
    assert target["default_view"] in target["views"]
    assert target["selected_contact_surfaces"] is None and target["world_grasp_pose_m_rad"] is None


def prepare() -> tuple[dict, dict]:
    """Resolve four target classes to byte-preserved source records and mesh observations."""
    pins = {**PINNED, **ROLE_PINNED}
    before = {relative: digest(ROOT / relative) for relative in pins}
    assert before == pins, "A pinned input changed"
    report, process, hands = copy.deepcopy(read_json(INPUT)), read_json(PROCESS), read_json(HANDS)
    with gzip.open(ROOT / MODEL, "rt") as stream:
        model = json.load(stream)
    assert len(model) == 92 and "V25_BASE_PLATE" not in model
    assert [row["id"] for row in report["targets"]] == ["BASE", "PANEL", "INNER", "RING"]
    profiles = {row["id"]: row for row in hands["profiles"]}
    for target in report["targets"]:
        resolve_target(target, process, profiles, model)
    report["selection"] = read_json(SELECTION)
    assert report["selection"]["selected_assembly_arm_count"] == report["selected_arm_count"] == 5
    report["all_source_task_ids"] = [row["id"] for row in read_json(WORK)["cards"]]
    assert len(set(report["all_source_task_ids"])) == 20
    evidence = read_json(EVIDENCE)
    report["source"] = evidence["source"]
    before[evidence["source"]["file"]] = digest(ROOT / evidence["source"]["file"])
    assert before[evidence["source"]["file"]] == evidence["source"]["sha256"]
    report["frames"] = {}
    for second in sorted({second for target in report["targets"] for second in target["views"]}):
        frame = copy.deepcopy(next(row for row in evidence["frames"] if row["requested_seek_s"] == second))
        before[frame["file"]] = digest(ROOT / frame["file"])
        assert before[frame["file"]] == frame["sha256"]
        frame["local_image"] = "evidence/" + Path(frame["file"]).name
        report["frames"][str(second)] = frame
    for target in report["targets"]:
        for view in target["view_data"]:
            size = report["frames"][str(view["second"])]["size_px"]
            for marker in view["markers"]:
                assert all(0 <= p < limit for p, limit in zip(marker["xy_px"], size, strict=True))
    for relative in (INPUT, PAGE, f"analysis/{STEM}.md"):
        before[relative] = digest(ROOT / relative)
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    report["revision"] = STEM
    report["model_feature_count"] = len(model)
    report["export_has_v25_base_plate_id"] = False
    return report, before


def package(directory: Path, report: dict) -> dict:
    """Save one offline review and the original source images in a new folder."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    paths = {frame["file"]: frame["local_image"] for frame in report["frames"].values()}
    paths.update(
        {
            PROCESS: "process_v03.json",
            HANDS: "hand_families.json",
            SELECTION: "selection.json",
            WORK: "all_workcards.json",
            f"analysis/{STEM}.md": "notes.md",
        }
    )
    copied = {}
    for relative, target in paths.items():
        source, destination = ROOT / relative, directory / target
        shutil.copy2(source, destination)
        assert digest(source) == digest(destination)
        copied[target] = digest(destination)
    write_new_json(directory / "review_data.json", report)
    template = (ROOT / PAGE).read_text()
    assert template.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False).replace("<", "\\u003c")
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    return {"copied_sha256": copied, "page_sha256": digest(directory / "review.html")}


def main() -> None:
    """Write a correspondence only; no native, grasp geometry or motion is modified."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_受渡し対象と手先_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists()
    assert not any((ROOT / f"{folder}/{STEM}.json").exists() for folder in ("data", "audit"))
    report, before = prepare()
    package_report = package(args.output_dir, report)
    after = {relative: digest(ROOT / relative) for relative in before}
    assert before == after, "Source changed during packaging"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        **package_report,
        "model_feature_count": report["model_feature_count"],
        "source_task_count": len(report["all_source_task_ids"]),
        "target_candidate_ids": {
            row["id"]: [candidate["id"] for candidate in row["model_candidates"]] for row in report["targets"]
        },
        "export_has_v25_base_plate_id": report["export_has_v25_base_plate_id"],
        "confirmed_video_to_photo_ids": [],
        "selected_grasp_poses": [],
        "model_written": False,
        "movie_created": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / f"data/{STEM}.json", report)
    write_new_json(ROOT / f"audit/{STEM}.json", audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("RECEIVING_INTERFACES_OK targets=4 frames=4 selected_arms=5 source_tasks=20 sources_unchanged=True")
    print(args.output_dir / "review.html")


if __name__ == "__main__":
    main()
