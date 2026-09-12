# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Carry the v06 inventory's equipment tags and outer sizes into a file small enough to commit.

Several figures the documents quote are read from ``op040_stagger_layout_inventory.json``,
which is 10.5 MB and has never been committed, so from a fresh checkout there is nothing behind
them. The whole file will not fit under the size hook. What the documents actually use is three
columns: the object's name, the equipment it belongs to, and how big it is. Those are taken
here for every object that carries an equipment tag, which is 5581 of 9570 and covers every
object the documents name.

The inventory is not in the repository. Its path and its digest are recorded, and the digest is
checked against the ``inventory_sha256`` the v06 geometry record pinned, so this extract can be
tied to the file it came from even though that file is somewhere else.

Nothing here is rounded: the bounds are copied as they were written.

Run: ``python3 scripts/extract_op030_v06_equipment_ids.py``

Reads two files and writes one. No Blender, no scene.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The working folder the v06 delivery was built in. These two files stayed there.
WORKING = Path("/home/rlrk/IsaacLab/eval_runs/ur15_jb_harness_revision_20260907")
INVENTORY = WORKING / "analysis/op040_stagger_layout_inventory.json"
GEOMETRY = WORKING / "audit/op030_stagger_static_v06_geometry.json"
REPORT = ROOT / "audit/op030_v06_equipment_ids.json"


def digest(path: Path) -> str:
    """Return a file's SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Write the three columns, with the provenance of the file they were read from."""
    if REPORT.exists():
        print(f"{REPORT.relative_to(ROOT)} exists already; move it aside first")
        return 1
    for path in (INVENTORY, GEOMETRY):
        if not path.exists():
            print(f"{path} is not here. It is off the repository and has to be found first.")
            return 1

    inventory_sha = digest(INVENTORY)
    geometry = json.loads(GEOMETRY.read_text())
    pinned = geometry.get("inventory_sha256")

    objects = json.loads(INVENTORY.read_text())["objects"]
    rows, by_equipment = {}, {}
    for name, entry in sorted(objects.items()):
        equipment = entry.get("equipment_id")
        own = entry.get("own_equipment_id")
        if not equipment and not own:
            continue
        row = dict(equipment_id=equipment, own_equipment_id=own, type=entry.get("type"))
        bounds = entry.get("bounds_world_m")
        if bounds:
            low, high = bounds
            row["bounds_world_m"] = bounds
            row["size_m"] = [high[axis] - low[axis] for axis in range(3)]
        rows[name] = row
        if equipment:
            by_equipment[equipment] = by_equipment.get(equipment, 0) + 1

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                scope="Equipment tag and outer size per object, taken from the v06 layout inventory",
                read_from=dict(
                    inventory=str(INVENTORY),
                    inventory_sha256=inventory_sha,
                    inventory_observed_at=json.loads(INVENTORY.read_text()).get("observed_at"),
                    inventory_is_not_committed=True,
                    geometry_record=str(GEOMETRY),
                    geometry_record_sha256=digest(GEOMETRY),
                    inventory_sha256_pinned_by_the_geometry_record=pinned,
                    pinned_digest_agrees=pinned == inventory_sha,
                ),
                method=dict(
                    kept="every object carrying an equipment_id or an own_equipment_id",
                    columns=["equipment_id", "own_equipment_id", "type", "bounds_world_m", "size_m"],
                    rounding="none; the bounds are copied as the inventory wrote them",
                ),
                what_this_does_not_give=[
                    "the objects without an equipment tag, which the inventory still holds",
                    "parents, world matrices and the rest of the inventory's columns",
                    "anything the inventory did not already record",
                ],
                object_count=len(rows),
                objects_in_the_inventory=len(objects),
                equipment_counts=dict(sorted(by_equipment.items())),
                objects=rows,
            ),
            indent=1,
        )
        + "\n"
    )
    size = REPORT.stat().st_size / 1024
    print(f"  {len(rows)} of {len(objects)} objects carry an equipment tag")
    print(f"  inventory sha256 {inventory_sha}")
    print(f"  the geometry record pinned {pinned}: {'same file' if pinned == inventory_sha else 'A DIFFERENT FILE'}")
    print(f"  {len(by_equipment)} distinct equipment ids")
    print(f"report: {REPORT.relative_to(ROOT)} ({size:.0f} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
