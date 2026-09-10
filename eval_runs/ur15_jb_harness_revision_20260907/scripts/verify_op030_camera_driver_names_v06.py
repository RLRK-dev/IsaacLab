# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Supplement native equivalence with driver variable names and raw Cycles settings."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_op030_camera_delta_v06 import digest, plain, settings


def read(path: Path) -> dict:
    """Read driver symbols and persistent rendering values without evaluating motion."""
    bpy.ops.wm.open_mainfile(filepath=str(path))
    owners = []
    for name in (
        "objects",
        "meshes",
        "shape_keys",
        "curves",
        "materials",
        "worlds",
        "scenes",
        "node_groups",
        "cameras",
        "lights",
    ):
        owners.extend(getattr(bpy.data, name))
    for block in [*bpy.data.materials, *bpy.data.worlds, *bpy.data.scenes]:
        tree = getattr(block, "node_tree", None)
        if tree:
            owners.append(tree)
    records = {}
    for owner in owners:
        animation = getattr(owner, "animation_data", None)
        if not animation:
            continue
        for curve in animation.drivers:
            key = f"{owner.bl_rna.identifier}/{owner.name}/{curve.data_path}/{curve.array_index}"
            record = dict(
                driver=settings(curve.driver),
                variables=[
                    dict(
                        name=variable.name,
                        type=variable.type,
                        targets=[settings(target) for target in variable.targets],
                    )
                    for variable in curve.driver.variables
                ],
            )
            if key in records and records[key] != record:
                raise ValueError("Duplicate inconsistent driver owner")
            records[key] = record
    return dict(drivers=records, raw_scene_cycles=plain(dict(bpy.context.scene.cycles.items())))


def main() -> None:
    """Compare definitions in the two saved natives and preserve the raw observation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if args.output.exists():
        raise FileExistsError(args.output)
    original, final = read(args.original), read(args.final)
    same = original == final
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        original=str(args.original.resolve()),
        original_sha256=digest(args.original),
        final=str(args.final.resolve()),
        final_sha256=digest(args.final),
        driver_count=len(original["drivers"]),
        driver_variable_count=sum(len(row["variables"]) for row in original["drivers"].values()),
        exact_equality=same,
        original_values=original,
        final_values=final,
        source_sha256=digest(Path(__file__)),
        reason="The general RNA settings reader omits name fields. Driver symbols are semantically relevant, "
        "so verify those names explicitly. Raw Cycles properties also preserve device-dependent enum values.",
        formal_physical_validity_verdict=None,
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not same:
        raise SystemExit("CAMERA_DELTA_DRIVER_SYMBOLS_CHANGED")
    print("CAMERA_DELTA_DRIVER_NAMES_COMPLETE", report["driver_count"], report["driver_variable_count"], flush=True)


if __name__ == "__main__":
    main()
