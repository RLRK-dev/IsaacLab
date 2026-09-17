# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Record the drawing sources and unchanged baselines for the PGE mounting concept."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from audit_hvjb_compact_hand_v01 import _sha


def main() -> None:
    """Check source identity and save a new observation without loading a scene."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    spec_path = args.source_root / "data/hvjb_pge_mount_v01.json"
    spec = json.loads(spec_path.read_text())
    previous = spec["previous_comparison"]
    previous_path = args.source_root / previous["path"]
    if _sha(previous_path) != previous["sha256"]:
        raise AssertionError("Previous comparison changed")
    baseline = json.loads(previous_path.read_text())["pinned"]
    before = {name: _sha(args.source_root / name) for name in baseline}
    if before != baseline:
        raise AssertionError("A pinned baseline changed")
    sources = []
    for source in spec["sources"]:
        path = args.source_root / source["local_path"]
        observed = _sha(path)
        if observed != source["sha256"]:
            raise AssertionError(f"Drawing source changed: {path}")
        sources.append({**source, "observed_sha256": observed, "bytes": path.stat().st_size})
    selection = json.loads((args.source_root / "data/hvjb_robot_selection_v01.json").read_text())
    tasks = json.loads((args.source_root / "data/hvjb_task_occupancy_v01.json").read_text())
    after = {name: _sha(args.source_root / name) for name in baseline}
    if before != after:
        raise AssertionError("A baseline changed during source recording")
    result = {
        "observed_at": datetime.now(UTC).isoformat(),
        "auditor_sha256": _sha(Path(__file__)),
        "spec_sha256": _sha(spec_path),
        "previous_comparison_sha256": _sha(previous_path),
        "baseline_before": before,
        "baseline_after": after,
        "baseline_unchanged": before == after,
        "sources": sources,
        "selected_plan": selection["selected_plan"],
        "selected_assembly_arm_count": selection["selected_assembly_arm_count"],
        "workcard_count": len(tasks["cards"]),
        "interface": spec["interface"],
        "interface_basis": "Manual transcription from inspected PDF; not specimen measurement or manufacturer CAD",
        "manufacturing_release": False,
        "formal_physical_verdict": None,
        "scope": "File identity and source transcription only; no force, trajectory or physical classification",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    if json.loads(args.output.read_text()) != result:
        raise AssertionError("Audit readback differs")
    print(f"PGE_MOUNT_RECORDED sources={len(sources)} baseline_unchanged={before == after}")


if __name__ == "__main__":
    main()
