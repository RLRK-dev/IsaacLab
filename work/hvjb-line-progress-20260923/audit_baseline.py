# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check restored source and delivered evidence without changing earlier artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PACKAGES = (
    "hvjb-assembly-location-v01-20260921",
    "hvjb-line-process-v03-20260921",
    "hvjb-line-video-v03-20260921",
    "hvjb-after-process-v01-20260921",
    "hvjb-test-plug-v01-20260921",
)


def sha(path: Path) -> str:
    """Return the SHA-256 of an existing artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def delivered_checks() -> list[dict]:
    """Compare each delivery to its recorded identity and any restored source."""
    rows = []
    for package in PACKAGES:
        path = ROOT.parent / package / "delivery_manifest.json"
        manifest = json.loads(path.read_text())
        destination = Path(manifest["destination"])
        for record in manifest["files"]:
            actual = destination / record["delivered_file"]
            source = REPO / record["source"]
            actual_sha = sha(actual)
            assert actual_sha == record["sha256"], actual
            assert actual.stat().st_size == record["bytes"], actual
            source_sha = sha(source) if source.is_file() else None
            if source_sha is not None:
                assert source_sha == actual_sha, source
            rows.append(
                {
                    "package": package,
                    "manifest": str(path.relative_to(REPO)),
                    "delivered_file": str(actual),
                    "expected_sha256": record["sha256"],
                    "observed_sha256": actual_sha,
                    "restored_source": str(source.relative_to(REPO)),
                    "restored_source_sha256": source_sha,
                    "source_absence_note": None if source_sha else "Large delivery-only artifact; original preserved.",
                }
            )
    return rows


def model_checks() -> dict:
    """Verify the previously saved complete display mesh archives."""
    directory = ROOT.parent / "hvjb-inner-installed-access-v01-20260921/data"
    manifest_path = directory / "product_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    archives = []
    for row in manifest["archives"]:
        path = directory / row["file"]
        actual = sha(path)
        assert actual == row["sha256"], path
        archives.append({"file": str(path.relative_to(REPO)), "sha256": actual})
    feature_count = len(manifest["features"])
    mesh_count = sum(len(row["meshes"]) for row in manifest["features"].values())
    assert feature_count == manifest["feature_count"] == 92
    assert mesh_count == manifest["mesh_count"] == 465
    return {
        "manifest_sha256": sha(manifest_path),
        "feature_count": feature_count,
        "mesh_count": mesh_count,
        "archives": archives,
        "scope": "Saved display geometry identity, not assembly completeness or physical validation.",
    }


def main() -> None:
    """Write one immutable baseline receipt for this continuation."""
    output = ROOT / "audit/baseline.json"
    assert not output.exists(), output
    deliveries = delivered_checks()
    model = model_checks()
    plan_path = ROOT.parent / "hvjb-line-process-v03-20260921/output/line_process_plan.json"
    plan = json.loads(plan_path.read_text())
    ids = [row["id"] for row in plan["cards"]]
    operations = sorted({row["operation"] for row in plan["cards"]})
    assert len(set(ids)) == len(ids) == 20
    assert len(operations) == 12
    assert set(ids) == {task for scene in plan["scenes"] for task in scene["tasks"]}
    report = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "base_commit": "91a1002bc6b92fb8122ea88e287e4164af431f46",
        "deliveries": deliveries,
        "delivery_files_compared": len(deliveries),
        "product_display": model,
        "plan_sha256": sha(plan_path),
        "work_ids": ids,
        "source_operations": operations,
        "coverage": plan["preserved_location_coverage"],
        "role_selection": plan["selected_role_allocation"],
        "logistics": {key: value for key, value in plan["logistics"].items() if key != "illustrative_snapshots"},
        "original_artifacts_modified": False,
        "formal_physical_validity_verdict": None,
        "script_sha256": sha(Path(__file__)),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"BASELINE_IDENTITY_COMPLETE deliveries={len(deliveries)} features=92 meshes=465 jobs=20 operations=12")


if __name__ == "__main__":
    main()
