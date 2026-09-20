# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check artifact identities and copy this review to a new delivery directory."""

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    assert not args.destination.exists(), args.destination
    observations = json.loads((OUTPUT / "tip_access_observations.json").read_text())
    document = json.loads((OUTPUT / "document_audit.json").read_text())
    assert observations["producing_script_sha256"] == sha(ROOT / "geometry.py")
    assert document["renderer_sha256"] == sha(ROOT / "build_review.py")
    assert document["observation_json_sha256"] == sha(OUTPUT / "tip_access_observations.json")
    assert document["sha256"] == sha(ROOT / document["pdf"])
    for filename, key in (
        ("trial_tip_meshes.json.gz", "trial_tip_meshes_sha256"),
        ("rear_only_tip_meshes.json.gz", "rear_only_tip_meshes_sha256"),
    ):
        assert observations[key] == sha(OUTPUT / filename)
    assert "TIP_ACCESS_OBSERVATIONS_COMPLETE" in (OUTPUT / "geometry_run.log").read_text()
    assert "TIP_ACCESS_PDF_COMPLETE" in (OUTPUT / "render_run.log").read_text()
    pages = sorted((OUTPUT / "pages").glob("page-*.png"))
    assert len(pages) == len(document["pages"]) == 3
    rows = []
    for path in sorted(OUTPUT.rglob("*")):
        if path.is_file() and path.name != "delivery_manifest.json":
            rows.append({"file": str(path.relative_to(OUTPUT)), "sha256": sha(path), "bytes": path.stat().st_size})
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(args.destination),
        "pdf_pages_rendered_and_visually_inspected": 3,
        "visual_inspection_scope": "Document layout and plotted correspondence only; no physical acceptance.",
        "files": rows,
    }
    (OUTPUT / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    shutil.copytree(OUTPUT, args.destination)
    for row in rows:
        assert sha(args.destination / row["file"]) == row["sha256"]
    assert sha(args.destination / "delivery_manifest.json") == sha(OUTPUT / "delivery_manifest.json")
    print(
        json.dumps(
            {
                "destination": str(args.destination),
                "files": len(rows) + 1,
                "pdf_sha256": document["sha256"],
                "all_copied_files_match": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
