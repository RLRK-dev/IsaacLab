# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Package source observations without modifying the HVJB model or process plan."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_hvjb_preassembly_review_v01 import ROOT, digest, read_json, write_new_json

INPUT = "data/hvjb_join_observations_v01.json"
AUDIT = "audit/hvjb_join_delivery_v01.json"
PINNED = {
    "data/hvjb_photo_correspondence_v03_p01.json": "6c5b7cb9bab859a33c8f5d5cd5429ce9f06fb0951b8a8fa4ae2a31ad99052ca0",
    "data/hvjb_preassembly_process_v02.json": "643f75e175518552d290816b402291496e9bb7f21db97385d81180acc9cfe83d",
    "data/hvjb_join_evidence_v01.json": "f3b521551d166341bfbd5f6891fd0e6bf3cf3699bb4677adc1a4a35e717d885a",
    "data/hvjb_join_transition_v01.json": "934c2d887a6733e405c6714eecbc9c1cbce468890237af632ce3e2104b087794",
    "data/hvjb_plate_evidence_v01.json": "2802f20de9ae1265da26830b6abb2995017b0bf71f311cfeabf4425ffd6945ce",
    "UR15_JB_photo_correspondence_v03_p03.blend": "5205d3aa2c2b99f7df6f538d17b3d3ca36ba8208c546858ee8ec8a5a3564a282",
}


def prepare() -> tuple[dict, dict]:
    """Resolve each observation to preserved source pixels and record the input hashes."""
    report = copy.deepcopy(read_json(INPUT))
    expected = dict(PINNED)
    evidence = {}
    for label, relative in (
        ("sequence", "data/hvjb_join_evidence_v01.json"),
        ("transition", "data/hvjb_join_transition_v01.json"),
        ("plate", "data/hvjb_plate_evidence_v01.json"),
    ):
        index = read_json(relative)
        expected[index["source"]["file"]] = index["source"]["sha256"]
        for source in index["frames"]:
            if label == "plate" and source["requested_seek_s"] not in (146, 158):
                continue
            row = copy.deepcopy(source)
            row["source_url"] = index["source"]["url"] + f"&t={int(row['requested_seek_s'])}s"
            row["source_type"] = "video_frame"
            row["local_image"] = "evidence/" + Path(row["file"]).name
            evidence[f"{label}:{row['requested_seek_s']}"] = row
            expected[row["file"]] = row["sha256"]
    photo = copy.deepcopy(read_json("data/hvjb_join_transition_v01.json")["photo"])
    photo.update(source_type="product_photo_2022", source_url=photo["url"])
    photo["local_image"] = "evidence/" + Path(photo["file"]).name
    evidence["photo:detail"] = photo
    expected[photo["file"]] = photo["sha256"]
    report["evidence"] = evidence
    for item in report["observations"]:
        source = evidence[item["evidence"]]
        width, height = source["size_px"]
        for marker in item["markers"]:
            assert 0 <= marker["xy_px"][0] < width and 0 <= marker["xy_px"][1] < height
    report["archive_keys"] = [key for key in evidence if not key.startswith("plate:")]
    before = {relative: digest(ROOT / relative) for relative in expected}
    assert before == expected, "An input differs from its recorded source"
    catalog = read_json("data/hvjb_photo_correspondence_v03_p01.json")
    previous = read_json("data/hvjb_preassembly_process_v02.json")
    preserved = previous["preserved_catalog_fields"]
    assert all(catalog[key] == value for key, value in preserved.items())
    assert all(item["native_object"] is None for item in report["unmapped_attachment_features"])
    report["observed_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    report["preserved_catalog_counts"] = {
        "parts": len(catalog["parts"]),
        "visible_fastener_features": len(catalog["visible_fastener_features"]),
        "visible_wire_segments": len(catalog["visible_wire_segments"]),
        "required_functions": len(catalog["required_functions"]),
        "electrical_groups": len(catalog["electrical_groups"]),
        "lv_pins": len(catalog["lv_pin_map"]),
    }
    return report, before


def package(directory: Path, report: dict) -> list[dict]:
    """Copy untouched evidence to a new offline review folder."""
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "evidence").mkdir()
    sources = {row["file"]: row["local_image"] for row in report["evidence"].values()}
    sources.update(
        {
            INPUT: "observation_inputs.json",
            "data/hvjb_join_evidence_v01.json": "sequence_evidence.json",
            "data/hvjb_join_transition_v01.json": "transition_evidence.json",
            "analysis/hvjb_join_followup_v01.md": "notes.md",
        }
    )
    copied = []
    for relative, target in sources.items():
        source, destination = ROOT / relative, directory / target
        shutil.copy2(source, destination)
        assert digest(source) == digest(destination), target
        copied.append({"source": relative, "file": target, "sha256": digest(destination)})
    write_new_json(directory / "observations.json", report)
    template = (ROOT / "scripts/hvjb_join_review_v01.html").read_text()
    assert template.count("__PAYLOAD__") == 1
    payload = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    (directory / "review.html").write_text(template.replace("__PAYLOAD__", payload))
    return copied


def main() -> None:
    """Keep the input model and previous process correspondence byte-identical."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir", type=Path, default=Path("/home/rlrk/Downloads/THREAD_HVJB_板間接合の確認_v01_20260916")
    )
    args = parser.parse_args()
    assert not args.output_dir.exists() and not (ROOT / AUDIT).exists(), "Refusing to overwrite a prior result"
    report, before = prepare()
    copied = package(args.output_dir, report)
    after = {relative: digest(ROOT / relative) for relative in before}
    assert before == after, "A preserved source changed"
    audit = {
        "observed_at": report["observed_at"],
        "directory": str(args.output_dir),
        "source_sha256_before": before,
        "source_sha256_after": after,
        "copied": copied,
        "generated_page_sha256": digest(args.output_dir / "review.html"),
        "observations_json_sha256": digest(args.output_dir / "observations.json"),
        "preserved_catalog_counts": report["preserved_catalog_counts"],
        "prior_catalog_fields_equal": True,
        "review_observations": len(report["observations"]),
        "new_video_frames": 23,
        "reused_video_frames": 2,
        "new_product_photos": 1,
        "unmapped_attachment_observations": len(report["unmapped_attachment_features"]),
        "model_written": False,
        "movie_created": False,
        "physical_acceptance_verdict": None,
    }
    write_new_json(ROOT / AUDIT, audit)
    write_new_json(args.output_dir / "audit.json", audit)
    print("HVJB_JOIN_REVIEW_OK observations=6 source_hashes_unchanged=True model_written=False", flush=True)
    print(args.output_dir / "review.html", flush=True)


if __name__ == "__main__":
    main()
