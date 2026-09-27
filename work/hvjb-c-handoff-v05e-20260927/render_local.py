# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Restore exact local-view inputs and reuse the original H06/H05 PNG renderers."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from build_motion import ROOT, WORK, load_module, sha, write


def copy_exact(source: Path, target: Path, expected: str, records: list) -> None:
    assert sha(source) == expected, source
    target.parent.mkdir(exist_ok=True, parents=True)
    assert not target.exists(), target
    shutil.copy2(source, target)
    assert sha(target) == expected
    records.append({"source": str(source), "copy": str(target), "sha256": expected})


def restore() -> dict:
    records = []
    h06 = WORK / "hvjb-h06-motion-review-v01-20260924"
    h05 = WORK / "hvjb-h05-motion-review-v01-20260924"
    target06, target05 = ROOT / "inputs/H06", ROOT / "inputs/H05"
    identity06 = h06 / "source_identity.json"
    copy_exact(identity06, target06 / identity06.name, sha(identity06), records)
    for row in json.loads(identity06.read_text())["source_files"]:
        local = h06 / row["copy"]
        source = local if local.exists() else Path(row["source"])
        copy_exact(source, target06 / row["copy"], row["sha256"], records)
    identity05 = h05 / "data/release_identity.json"
    copy_exact(identity05, target05 / "data" / identity05.name, sha(identity05), records)
    record05 = json.loads(identity05.read_text())
    for path, digest in record05["source_sha256"].items():
        local = h05 / "sources" / Path(path).name
        source = local if local.exists() else Path(path)
        copy_exact(source, target05 / "sources" / Path(path).name, digest, records)
    for row in record05["models"]:
        copy_exact(h05 / row["derived_bank"], target05 / row["derived_bank"], row["derived_bank_sha256"], records)
    record = {"exact_input_copies": records, "physical_acceptance_verdict": None}
    write(ROOT / "audit/local_input_recovery.json", record)
    return record


def main() -> None:
    record = restore()
    for name, old_dir, script in (
        ("H06", "hvjb-h06-motion-review-v01-20260924", "render_sequence.py"),
        ("H05", "hvjb-h05-motion-review-v01-20260924", "render_release.py"),
    ):
        module = load_module("existing_" + name, WORK / old_dir / script)
        module.ROOT = ROOT / "inputs" / name
        sys.argv = [str(WORK / old_dir / script)]
        module.main()
    assert all(sha(Path(row["copy"])) == row["sha256"] for row in record["exact_input_copies"])
    print("C_LOCAL_RENDER_COMPLETE original_geometry_and_saved_samples_unchanged=True", flush=True)


if __name__ == "__main__":
    main()
