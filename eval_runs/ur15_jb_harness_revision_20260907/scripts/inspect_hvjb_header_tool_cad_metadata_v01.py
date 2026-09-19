# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Inventory explicit metadata in pinned example STEP files and prepare unresolved configuration questions."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from analyze_hvjb_header_tool_configuration_v01 import ROOT, _read, _sha
from check_hvjb_header_tool_tip_sources_v01 import _protected
from prepare_hvjb_ses2001_cad_v01 import _step

SETTINGS = "data/hvjb_header_tool_cad_metadata_v01.json"
ARTIFACTS = [
    SETTINGS,
    "analysis/hvjb_header_tool_configuration_request_v01.md",
    "scripts/inspect_hvjb_header_tool_cad_metadata_v01.py",
]


def _metadata(raw: bytes, kinds: list[str]) -> dict:
    simple = re.findall(rb"(?m)^#\d+\s*=\s*([A-Z][A-Z0-9_]*)\s*\(", raw)
    counts = Counter(value.decode("ascii") for value in simple)
    pattern = rb"(?m)^#(\d+)\s*=\s*(" + b"|".join(kind.encode("ascii") for kind in kinds) + rb")\s*\(.*?;"
    records = []
    for match in re.finditer(pattern, raw, re.DOTALL):
        records.append(
            {
                "entity_id": int(match.group(1)),
                "type": match.group(2).decode("ascii"),
                "record": match.group(0).decode("latin1"),
            }
        )
    assert len(records) == sum(counts[kind] for kind in kinds)
    return {
        "scope": "Pinned-file simple declarations and selected raw metadata records, not a general STEP/BOM parser",
        "simple_entity_counts": dict(sorted(counts.items())),
        "selected_metadata_counts": {kind: counts[kind] for kind in kinds},
        "selected_metadata_records": records,
        "explicit_bit_product_identified": None,
        "bit_geometry_presence": None,
        "mount_to_engagement_transform": None,
    }


def _request(settings: dict) -> dict:
    hand = _read(settings["source_records"]["hand"])
    screws = _read(settings["source_records"]["screw_conditions"])
    headers = []
    for model in hand["models"]:
        headers.append(
            {
                "part_id": model["feature_id"],
                "part_number": model["part_number"],
                "mounting_screw_count": len(model["axes"]),
                "saved_axes": [
                    {
                        "screw_name": axis["screw_name"],
                        "local_xz_m": axis["nominal_local_xz_m"],
                        "saved_hand_frame": axis["pose"]["frame"],
                    }
                    for axis in model["axes"]
                ],
            }
        )
    assert sum(row["mounting_screw_count"] for row in headers) == 14
    assert screws["selected_fastener"] is None
    assert all(row["answer"] is None for row in settings["questions"])
    return {
        "scope": (
            "Source-backed configuration questions; no submitted inquiry, equipment selection or acceptance criteria"
        ),
        "headers": headers,
        "te_published_conditions": screws["te_conditions"],
        "te_sources": [row for row in screws["sources"] if row["id"].startswith("TE_")],
        "candidate_screws_are_unselected": all(not row["selected"] for row in screws["catalog_examples"]),
        "questions": settings["questions"],
        "actual_configuration": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_json", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output_json.exists(), "Preserve previous observation"
    settings = _read(SETTINGS)
    before = _protected(settings)
    assert all(path in before for path in settings["reuse"])
    models = {}
    header_files = {}
    header_directory = ROOT / settings["header_directory"]
    header_directory.mkdir(parents=True, exist_ok=False)
    for source in settings["sources"]:
        raw, archive = _step({"sources": [source]})
        assert archive["step_entry"] == source["step_entry"]
        assert archive["step_sha256"] == source["step_sha256"]
        header = archive.pop("step_header").encode("latin1")
        header_path = header_directory / (source["step_entry"] + ".header.txt")
        with header_path.open("xb") as stream:
            stream.write(header)
        assert header_path.read_bytes() == header
        header_name = str(header_path.relative_to(ROOT))
        header_files[header_name] = _sha(header_name)
        archive["step_header_file"] = header_name
        archive["step_header_sha256"] = header_files[header_name]
        archive["step_header_storage"] = "Original bytes, including line endings, in a separate reference text file"
        record = _metadata(raw, settings["metadata_entity_types"])
        models[source["model"]] = {"source": archive, **record}
        counts = record["selected_metadata_counts"]
        print(
            source["model"],
            "PRODUCT",
            counts["PRODUCT"],
            "MANIFOLD_SOLID_BREP",
            counts["MANIFOLD_SOLID_BREP"],
            "NEXT_ASSEMBLY_USAGE_OCCURRENCE",
            counts["NEXT_ASSEMBLY_USAGE_OCCURRENCE"],
            flush=True,
        )
    request = _request(settings)
    after = {path: _sha(path) for path in before}
    assert before == after
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "models": models,
        "configuration_request": request,
        "input_sha256_before": before,
        "input_sha256_current": after,
        "inputs_match": True,
        "artifacts_sha256": {path: _sha(path) for path in ARTIFACTS},
        "source_derivatives_sha256": header_files,
        "geometry_or_motion_modified": False,
        "cad_converted": False,
        "bundled_executables_extracted_or_run": False,
        "native_opened": False,
        "native_saved": False,
        "selected_tool_configuration": None,
        "selected_axial_registration_m": None,
        "physical_acceptance_verdict": None,
    }
    with args.output_json.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    assert json.loads(args.output_json.read_text()) == result
    print(f"Protected inputs unchanged: {len(before)}; configuration request contains 14 saved header axes")
    print("HEADER_TOOL_CAD_METADATA_COMPLETE", args.output_json, flush=True)


if __name__ == "__main__":
    main()
