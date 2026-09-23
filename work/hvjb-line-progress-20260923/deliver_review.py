# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Copy the reviewed booklet into a new delivery directory and verify every byte."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DEFAULT_DESTINATION = Path("/home/rlrk/Downloads/HVJB_ライン全体と組立場所_v04_20260923")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_to_deliver() -> list[Path]:
    files = [
        ROOT / "README.md",
        ROOT / "connector_followup.md",
        ROOT / "qa_receipt.json",
        ROOT / "output/document_audit.json",
        ROOT / "audit/baseline.json",
        ROOT / "audit/product_final_views.json",
    ]
    for directory in ("data", "output/pdf", "output/pages", "figures/product_final"):
        files.extend(sorted(path for path in (ROOT / directory).iterdir() if path.is_file()))
    assert len({str(path) for path in files}) == len(files)
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    destination = args.destination
    temporary = destination.with_name(f".{destination.name}.partial")
    record = ROOT / "delivery_manifest.json"
    assert not destination.exists(), destination
    assert not temporary.exists(), temporary
    assert not record.exists(), record
    qa = json.loads((ROOT / "qa_receipt.json").read_text())
    assert sha(ROOT / "output/pdf/HVJB_ライン全体と組立場所_v04_20260923.pdf") == qa["pdf_sha256"]
    files = files_to_deliver()
    manifest = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "destination": str(destination),
        "files": [
            {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files
        ],
        "overwrote_existing_delivery": False,
        "formal_physical_validity_verdict": None,
    }
    temporary.mkdir()
    for source, row in zip(files, manifest["files"], strict=True):
        target = temporary / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert sha(target) == row["sha256"], target
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (temporary / "delivery_manifest.json").write_text(manifest_text)
    temporary.rename(destination)
    for row in manifest["files"]:
        assert sha(destination / row["path"]) == row["sha256"], row["path"]
    with record.open("x") as stream:
        stream.write(manifest_text)
    print(f"DELIVERY_READBACK_COMPLETE files={len(files)} destination={destination}")


if __name__ == "__main__":
    main()
