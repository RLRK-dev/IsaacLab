# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package a unitization role comparison without changing source geometry or motion."""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json

INPUT = "data/hvjb_unitization_roles_v01.json"
PROCESS = "data/hvjb_preassembly_process_v03.json"
MODEL = "data/hvjb_photo_model_v03_p03.json.gz"
AUDIT = "audit/hvjb_unitization_review_v01.json"
PINNED = {
    PROCESS: "5e9d7078d4e7ff9772f8561788b29a34b28165e3118559385dcc78faf28b64e7",
    MODEL: "6687b12ec1b3db24babf75f8fef1b6f6bc123c288b713824b9763d9214553ba6",
    "data/hvjb_unitization_decision_v01.json": "f28f0693cc48cf288b0c50846f3b23196cf11b02561ce1a8ef55528f8e45f6f6",
    "data/hvjb_photo_correspondence_v03_p01.json": "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    "data/hvjb_plate_evidence_v01.json": "2802f20de9ae1265da26830b6abb2995017b0bf71f311cfeabf4425ffd6945ce",
    "data/hand_provisional_spec_v01.json": "0ed18d28e261b73ae1fd3beb1686ad4c2b55071974d9b8708e358b79efa8b799",
    "UR15_JB_photo_correspondence_v03_p03.blend": "5205d3aa2c2b99f7df6f538d17b3d3ca36ba8208c546858ee8ec8a5a3564a282",
}


def validate_roles(report: dict, decision: dict) -> None:
    """Check diagram references and declared coverage; this does not evaluate contact physics."""
    steps = {row["id"] for row in decision["steps"]}
    actors = {row["id"] for row in report["actors"]}
    states = report["states"]
    assert len({row["id"] for row in states}) == len(states)
    assert {row["step"] for row in states} == steps
    for row in states:
        active = set(row["active"])
        assert active <= actors
        assert row["base_support"] and set(row["base_support"]) <= active
        assert row["panel_support"] and set(row["panel_support"]) <= active | {"joined_base", "upstream_rest"}
        assert "joined_base" not in row["panel_support"] or row["joined_assumption"]
        assert row["before_release_ja"]
    for key in (
        "selected_robot_count",
        "selected_grasp_surfaces",
        "acceptance_thresholds",
        "physical_acceptance_verdict",
    ):
        assert report[key] is None


def inspect_export() -> dict:
    """Observe the preserved display export; all vertex coordinates are in [m]."""
    with gzip.open(ROOT / MODEL, "rt") as stream:
        model = json.load(stream)
    panel = model["P07"]
    vertices = [vertex for mesh in panel["meshes"] for vertex in mesh["vertices"]]
    minimum = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    maximum = [max(vertex[axis] for vertex in vertices) for axis in range(3)]
    return {
        "basis": "saved display-mesh export, not manufacturing CAD",
        "export_feature_count": len(model),
        "export_has_v25_base_plate_id": "V25_BASE_PLATE" in model,
        "case_mesh_names": [mesh["name"] for mesh in model["P01"]["meshes"]],
        "panel_basis": panel["basis"],
        "panel_mesh_names": [mesh["name"] for mesh in panel["meshes"]],
        "panel_display_aabb_min_m": minimum,
        "panel_display_aabb_max_m": maximum,
        "panel_display_aabb_size_m": [b - a for a, b in zip(minimum, maximum, strict=True)],
        "manufacturing_dimensions_m": None,
    }


def prepare() -> tuple[dict, dict]:
    """Resolve the comparison to the approved procedure and byte-preserved source frames."""
    before = {relative: digest(ROOT / relative) for relative in PINNED}
    assert before == PINNED, "A pinned input changed"
    report = copy.deepcopy(read_json(INPUT))
    decision = read_json(report["procedure"])
    validate_roles(report, decision)
    report["adopted_steps"] = decision["steps"]
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    report["model_observations"] = inspect_export()
    evidence = read_json("data/hvjb_plate_evidence_v01.json")
    source = evidence["source"]
    before[source["file"]] = digest(ROOT / source["file"])
    assert before[source["file"]] == source["sha256"]
    for view in report["evidence_views"]:
        frame = next(row for row in evidence["frames"] if row["requested_seek_s"] == view["second"])
        before[frame["file"]] = digest(ROOT / frame["file"])
        assert before[frame["file"]] == frame["sha256"]
        view["frame"] = frame
        view["local_image"] = "evidence/" + Path(frame["file"]).name
        for marker in view["markers"]:
            assert all(0 <= p < size for p, size in zip(marker["xy_px"], frame["size_px"], strict=True))
    catalog = read_json("data/hvjb_photo_correspondence_v03_p01.json")
    process = read_json(PROCESS)
    assert all(catalog[key] == value for key, value in process["preserved_catalog_fields"].items())
    for relative in (INPUT, "analysis/hvjb_unitization_roles_v01.md", "scripts/hvjb_unitization_review_v01.html"):
        before[relative] = digest(ROOT / relative)
    return report, before


def package(directory: Path, report: dict) -> list[dict]:
    """Create a self-contained review with unedited source images and a scale-free diagram."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    sources = {view["frame"]["file"]: view["local_image"] for view in report["evidence_views"]}
    sources.update(
        {
            INPUT: "role_inputs.json",
            PROCESS: "process_v03.json",
            report["procedure"]: "adopted_procedure.json",
            "data/hand_provisional_spec_v01.json": "hand_families.json",
            "analysis/hvjb_unitization_roles_v01.md": "notes.md",
        }
    )
    copied = []
    for relative, target in sources.items():
        source, destination = ROOT / relative, directory / target
        shutil.copy2(source, destination)
        assert digest(source) == digest(destination)
        copied.append({"source": relative, "file": target, "sha256": digest(destination)})
    write_new_json(directory / "review_data.json", report)
    template = (ROOT / "scripts/hvjb_unitization_review_v01.html").read_text()
    assert template.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    return copied


def main() -> None:
    """Verify old artifacts and save one new comparison folder and its audit."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_支持と受渡し_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists() and not (ROOT / AUDIT).exists(), "Refusing to overwrite existing results"
    report, before = prepare()
    copied = package(args.output_dir, report)
    after = {relative: digest(ROOT / relative) for relative in before}
    assert before == after, "A preserved input changed"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "source_sha256_before": before,
        "source_sha256_after": after,
        "copied": copied,
        "generated_page_sha256": digest(args.output_dir / "review.html"),
        "review_data_sha256": digest(args.output_dir / "review_data.json"),
        "adopted_step_count": len(report["adopted_steps"]),
        "comparison_state_count": len(report["states"]),
        "declared_role_references_valid": True,
        "role_check_scope": "diagram bookkeeping only; support and grip capacity not evaluated",
        "model_observations": report["model_observations"],
        "catalog_preserved_in_process": True,
        "model_written": False,
        "motion_created": False,
        "movie_created": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("UNITIZATION_REVIEW_OK adopted_steps=5 comparison_states=9 sources_unchanged=True", flush=True)
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
