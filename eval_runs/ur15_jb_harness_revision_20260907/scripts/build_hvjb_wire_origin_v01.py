# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package observed wire fragments without inventing occluded electrical connections."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_assist_handoff_v01 import PINNED as ROLE_PINNED
from build_hvjb_assist_handoff_v01 import SELECTION, WORK
from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json
from build_hvjb_unitization_review_v01 import PINNED, PROCESS, inspect_export

STEM = "hvjb_wire_origin_v01"
INPUT = "data/hvjb_wire_origin_inputs_v01.json"
PAGE = f"scripts/{STEM}.html"
CATALOG = "data/hvjb_photo_correspondence_v03_p01.json"
PDF = "references/op040_real_products_20260912/ampere_hvjb_5_400_v1_1.pdf"
EVIDENCE = "data/hvjb_wire_origin_evidence_v01.json"
EXTRA_PINS = {
    EVIDENCE: "6355b90ecf7d0fe52579771db23655df37aae661770f0fcf6f7754c0e747d1a6",
    "data/hvjb_join_transition_v01.json": "934c2d887a6733e405c6714eecbc9c1cbce468890237af632ce3e2104b087794",
    "data/hvjb_video_evidence_v02.json": "a199df6888bef22ce53de4686d9d5fe120ecab26d53888e1000b62f3b779ef7f",
    PDF: "643648bcea77b4d7c37c65d073664f746f68689952da2d5ce932e3d10bd5a9e1",
}


def validate_annotations(report: dict) -> None:
    """Check image references [px] and preserve unresolved endpoint identities."""
    views = {row["id"]: row for row in report["views"]}
    traces = {row["id"]: row for row in report["traces"]}
    assert len(views) == 5 and len(traces) == 4
    for view in views.values():
        assert set(view["trace_ids"]) <= traces.keys()
        width, height = view["frame"]["size_px"]
        x, y, w, h = view["focus_px"]
        assert 0 <= x < x + w <= width and 0 <= y < y + h <= height
        for marker in view["markers"]:
            assert all(0 <= p < n for p, n in zip(marker["xy_px"], [width, height], strict=True))
        for identifier in view["trace_ids"]:
            trace = traces[identifier]
            assert trace["view"] == view["id"]
            for segment in trace["segments_px"]:
                assert len(segment) >= 2
                assert all(0 <= p < n for xy in segment for p, n in zip(xy, [width, height], strict=True))
            for key in ("physical_from_id", "physical_to_id", "electrical_group_id", "photo_wire_id"):
                assert trace[key] is None
    assert not traces["B87_FRONT"]["segments_px"], "Do not bridge the unresolved crossing"
    assert not report["complete_wire_inventory"] and not report["confirmed_video_to_photo_wires"]
    assert not report["selected_grasp_poses"] and report["physical_acceptance_verdict"] is None


def prepare() -> tuple[dict, dict]:
    """Resolve original frames, preserved records and source hashes."""
    pins = {**PINNED, **ROLE_PINNED, **EXTRA_PINS}
    before = {path: digest(ROOT / path) for path in pins}
    assert before == pins, "A pinned input changed"
    report = copy.deepcopy(read_json(INPUT))
    evidence = read_json(EVIDENCE)
    frames = copy.deepcopy(evidence["frames"])
    frames += [copy.deepcopy(read_json("data/hvjb_join_transition_v01.json")["frames"][0])]
    frames += [r for r in read_json("data/hvjb_plate_evidence_v01.json")["frames"] if r["requested_seek_s"] == 170]
    frames += [read_json("data/hvjb_video_evidence_v02.json")["frames"]["busbars"]]
    report["source"] = evidence["source"]
    source = report["source"]
    before[source["file"]] = digest(ROOT / source["file"])
    assert before[source["file"]] == source["sha256"]
    for frame in frames:
        before[frame["file"]] = digest(ROOT / frame["file"])
        assert before[frame["file"]] == frame["sha256"]
        frame["local_image"] = "evidence/" + Path(frame["file"]).name
        frame["url"] = source["url"] + f"&t={frame['requested_seek_s']}s"
    report["frames"] = frames
    for view in report["views"]:
        view["frame"] = next(f for f in frames if f["requested_seek_s"] == view["second"])
    validate_annotations(report)
    report["selection"] = read_json(SELECTION)
    assert report["selected_arm_count"] == report["selection"]["selected_assembly_arm_count"] == 5
    assert report["selected_plan"] == report["selection"]["selected_plan"] == "S5_AB"
    report["all_source_task_ids"] = [row["id"] for row in read_json(WORK)["cards"]]
    catalog, process = read_json(CATALOG), read_json(PROCESS)
    assert all(catalog[key] == value for key, value in process["preserved_catalog_fields"].items())
    report["preserved_counts"] = {
        "photo_features": inspect_export()["export_feature_count"],
        "required_functions": len(catalog["required_functions"]),
        "electrical_groups": len(catalog["electrical_groups"]),
        "lv_pins": len(catalog["lv_pin_map"]),
        "source_tasks": len(set(report["all_source_task_ids"])),
    }
    assert list(report["preserved_counts"].values()) == [92, 17, 13, 12, 20]
    report["electrical_groups"] = copy.deepcopy(catalog["electrical_groups"])
    for path in (INPUT, PAGE, f"analysis/{STEM}.md"):
        before[path] = digest(ROOT / path)
    report["revision"] = STEM
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    return report, before


def package(directory: Path, report: dict) -> dict:
    """Save a new offline review with original images and PDF page renderings."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    paths = {f["file"]: f["local_image"] for f in report["frames"]}
    paths.update(
        {
            PDF: "source_v1_1.pdf",
            CATALOG: "catalog.json",
            WORK: "all_workcards.json",
            SELECTION: "selection.json",
            f"analysis/{STEM}.md": "notes.md",
        }
    )
    copied = {}
    for relative, target in paths.items():
        shutil.copy2(ROOT / relative, directory / target)
        assert digest(ROOT / relative) == digest(directory / target)
        copied[target] = digest(directory / target)
    command = [
        "pdftoppm",
        "-f",
        "2",
        "-l",
        "3",
        "-scale-to",
        "1900",
        "-png",
        str(directory / "source_v1_1.pdf"),
        str(directory / "evidence/datasheet"),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    report["pdf_pages"] = [
        {
            "page": n,
            "local_image": f"evidence/datasheet-{n}.png",
            "sha256": digest(directory / f"evidence/datasheet-{n}.png"),
        }
        for n in (2, 3)
    ]
    write_new_json(directory / "review_data.json", report)
    template = (ROOT / PAGE).read_text()
    assert template.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False).replace("<", "\\u003c")
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    return {
        "copied_sha256": copied,
        "page_sha256": digest(directory / "review.html"),
        "pdf_render_command": command,
        "pdf_pages": report["pdf_pages"],
    }


def main() -> None:
    """Publish observations; leave native models and all source data unchanged."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_A_B配線の由来_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists()
    assert not any((ROOT / f"{folder}/{STEM}.json").exists() for folder in ("data", "audit"))
    report, before = prepare()
    packaged = package(args.output_dir, report)
    after = {path: digest(ROOT / path) for path in before}
    assert before == after, "Source changed during packaging"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "input_sha256_before": before,
        "input_sha256_after": after,
        **packaged,
        "preserved_counts": report["preserved_counts"],
        "trace_examples": len(report["traces"]),
        "complete_wire_inventory": False,
        "confirmed_video_to_photo_wires": [],
        "model_written": False,
        "movie_created": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / f"data/{STEM}.json", report)
    write_new_json(ROOT / f"audit/{STEM}.json", audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("WIRE_ORIGIN_OK views=5 trace_examples=4 frames=9 selected_arms=5 source_tasks=20 sources_unchanged=True")
    print(args.output_dir / "review.html")


if __name__ == "__main__":
    main()
