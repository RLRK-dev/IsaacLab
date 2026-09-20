# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Extract unchanged header triangles from the preserved review bundle."""

import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT_SHA = "8c0bbe8c60f0a78f8dcba56d76ed825d13d3f88dd67e9fd8cdeb932e88fa4130"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_root", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root / "data/header_review_v03/meshes.json.gz"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PARENT_SHA
    rows = json.loads(gzip.decompress(source.read_bytes()))["headers"]
    destination = ROOT / "data"
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for row in rows:
        path = destination / (row["part_number"] + ".json.gz")
        encoded = gzip.compress(json.dumps(row, separators=(",", ":")).encode(), mtime=0)
        path.write_bytes(encoded)
        assert json.loads(gzip.decompress(encoded)) == row
        records.append({"file": path.name, "sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)})
    for name in ("te_2103340_drawing.pdf", "te_2103346_drawing.pdf"):
        source_pdf = args.source_root / "references/connector_correction_20260915" / name
        shutil.copy2(source_pdf, destination / name)
        records.append({"file": name, "sha256": hashlib.sha256(source_pdf.read_bytes()).hexdigest()})
    (destination / "provenance.json").write_text(
        json.dumps(
            {
                "parent_file": str(source),
                "parent_sha256": PARENT_SHA,
                "unchanged_header_rows_only": True,
                "files": records,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
