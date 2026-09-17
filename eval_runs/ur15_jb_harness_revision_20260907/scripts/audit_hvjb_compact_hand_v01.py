# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Record source identities for a catalogue and schematic comparison, without loading a scene."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    """Read pinned inputs and write one new audit; no physical criterion is applied."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_root", type=Path, required=True)
    parser.add_argument("--package_root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    spec_path = args.package_root / "data/hvjb_compact_hand_v01.json"
    spec = json.loads(spec_path.read_text())
    before = {name: _sha(args.source_root / name) for name in spec["pinned"]}
    if before != spec["pinned"]:
        raise AssertionError("A pinned baseline file differs")
    selection = json.loads((args.source_root / "data/hvjb_robot_selection_v01.json").read_text())
    tasks = json.loads((args.source_root / "data/hvjb_task_occupancy_v01.json").read_text())
    source_refs = {}
    reference_root = args.package_root / "references/hvjb_compact_hand_20260917"
    if not reference_root.is_dir():
        reference_root = args.package_root / "references"
    for path in sorted(reference_root.glob("*")):
        if path.is_file():
            source_refs[path.name] = {"bytes": path.stat().st_size, "sha256": _sha(path)}
    after = {name: _sha(args.source_root / name) for name in before}
    if before != after:
        raise AssertionError("Baseline file changed during this observation")
    report = {
        "observed_at": datetime.now(UTC).isoformat(),
        "auditor_sha256": _sha(Path(__file__)),
        "spec_sha256": _sha(spec_path),
        "baseline_before": before,
        "baseline_after": after,
        "baseline_unchanged": before == after,
        "selected_plan": selection["selected_plan"],
        "selected_assembly_arm_count": selection["selected_assembly_arm_count"],
        "workcard_count": len(tasks["cards"]),
        "references": source_refs,
        "candidate_count": len(spec["candidates"]),
        "formal_physical_verdict": None,
        "scope": "File identity and source recording only; schematic geometry is not a physical measurement",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    if json.loads(args.output.read_text()) != report:
        raise AssertionError("Audit readback differs")
    print(f"COMPACT_HAND_RECORDED candidates={len(spec['candidates'])} baseline_unchanged={before == after}")


if __name__ == "__main__":
    main()
