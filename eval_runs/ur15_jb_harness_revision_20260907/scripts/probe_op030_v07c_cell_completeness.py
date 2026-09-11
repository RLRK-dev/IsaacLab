# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Ask what stands at each cell that the copy would not carry [m].

Work 3 duplicates A, B and C onto the three empty bases. The selection says what gets
copied; it does not say whether that is the whole cell. This asks the complement: of
everything standing at a cell, what is neither in that cell's selection nor in the 76
objects v06 deliberately left in place.

The question this exists to answer is A's supply. B's 420 include its own wire supply as
b_only hardware, 194 objects with no counterpart anywhere else. A's M4 feeder and C's M6 and
M14 feeders are the same kind of thing, and nothing in the mapped selection guarantees they
come along -- the mapping starts from B's names, and B has no M4 feeder. If they fall
outside, S1R gets a robot with nothing to pick from, and work 2's repair never reaches it.

Each object is assigned to the nearest of the six v07c bases, so nothing is counted at two
cells and anything standing at an empty base shows up there instead of being absorbed by a
neighbour.

Reads the repaired candidate, not the delivered native, because that is what work 3 copies.

Run: ``blender --background --python scripts/probe_op030_v07c_cell_completeness.py``

Read-only. The scene is never saved and world transforms are compared before and after.
A structural observation at its recorded timestamp, not a physical-validity verdict.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_split_v04 import _world_vertices  # noqa: E402
from build_op030_stagger_static_v06 import digest  # noqa: E402

SOURCE = ROOT / "analysis/op030_v07c_support_repair.blend"
SOURCE_SHA = "1091683a5d15072e46553b487a30d58a21050bf40515f0d09b9d4d879c01ecce"
SELECTION = ROOT / "analysis/op030_v07c_cell_selection.json"
MANIFEST = ROOT / "audit/op030_stagger_static_v06.json"
MANIFEST_SHA = "bc82917686f8292bf081bdefa2922dbc6851733552eea390c1b725c2cd8b9f8f"
REPORT = ROOT / "audit/op030_v07c_cell_completeness.json"

# The six v07c bases. Every object is assigned to whichever is nearest.
CELL_BASES = {
    "S1L": (-0.900, -1.700),
    "S1R": (0.900, -1.700),
    "S2L": (-0.900, 0.600),
    "S2R": (0.900, 0.600),
    "S3L": (-0.900, 2.900),
    "S3R": (0.900, 2.900),
}
# Which existing cell stands at which base, and which base it is copied to.
HOMES = {"A": ("S1L", "S1R"), "B": ("S2R", "S2L"), "C": ("S3L", "S3R")}
# Beyond this an object belongs to the hall, not to any cell.
CELL_RADIUS = 2.500
# The supply equipment each cell works from. Reported by name because it is the open question.
SUPPLY_PREFIXES = {"A": ("OP030A_feeder",), "B": ("OP030B_wire_supply",), "C": ("OP030C_feeder",)}
# Anything this wide is the floor or the hall, not cell equipment.
HALL_FOOTPRINT_M = 8.0


def centre_of(obj: bpy.types.Object) -> tuple[float, float] | None:
    """Return an object's world XY centre, from its geometry where it has any [m]."""
    if obj.type in {"MESH", "CURVE"} and getattr(obj.data, "vertices", None) and len(obj.data.vertices):
        world = _world_vertices(obj)
        low, high = world.min(0), world.max(0)
        if max(high[0] - low[0], high[1] - low[1]) > HALL_FOOTPRINT_M:
            return None
        return (float((low[0] + high[0]) / 2), float((low[1] + high[1]) / 2))
    translation = np.asarray(obj.matrix_world)[:3, 3]
    return (float(translation[0]), float(translation[1]))


def nearest_base(xy: tuple[float, float]) -> tuple[str, float]:
    """Return the nearest v07c base and the distance to it [m]."""
    distances = {label: float(np.hypot(xy[0] - base[0], xy[1] - base[1])) for label, base in CELL_BASES.items()}
    label = min(distances, key=distances.get)
    return label, distances[label]


def covered_sets() -> tuple[dict[str, set[str]], set[str], dict]:
    """Return each cell's selection, the fixed set, and what they were read from."""
    report = json.loads(SELECTION.read_text())
    binding = json.loads(MANIFEST.read_text())["stagger_v06"]
    covered = {"B": set(binding["moved_objects"])}
    for label in ("A", "C"):
        row = report["targets"][label]
        covered[label] = {entry["name"] for entry in row["selection"]} | set(row["structure"]["closure_brings_extra"])
    read_from = dict(
        selection=str(SELECTION.relative_to(ROOT)),
        selection_sha256=digest(SELECTION),
        selection_observed_at=report["observed_at"],
        manifest=str(MANIFEST.relative_to(ROOT)),
        manifest_sha256=MANIFEST_SHA,
        counts={label: len(names) for label, names in covered.items()},
    )
    return covered, set(binding["fixed_line_objects"]), read_from


def supply_status(cell: str, covered: set[str]) -> dict:
    """Report whether the cell's own supply equipment is inside its selection."""
    prefixes = SUPPLY_PREFIXES[cell]
    members = sorted(obj.name for obj in bpy.data.objects if obj.name.startswith(prefixes))
    inside = [name for name in members if name in covered]
    return dict(
        prefixes=list(prefixes),
        member_count=len(members),
        carried_count=len(inside),
        complete=bool(members) and len(inside) == len(members),
        not_carried=[name for name in members if name not in covered],
    )


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Report, per cell, what the copy would carry and what it would leave behind."""
    assert digest(SOURCE) == SOURCE_SHA, "Probe the repaired candidate work 3 copies"
    assert SELECTION.exists(), f"Missing the work 1 selection: {SELECTION}"
    assert MANIFEST.exists(), f"Local working material missing: {MANIFEST}"
    assert digest(MANIFEST) == MANIFEST_SHA, "Read the v06 static manifest"
    assert not REPORT.exists(), "Preserve the existing report"
    covered, fixed, read_from = covered_sets()

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    at_base: dict[str, list[dict]] = {label: [] for label in CELL_BASES}
    hall = []
    for obj in bpy.context.scene.objects:
        xy = centre_of(obj)
        if xy is None:
            hall.append(obj.name)
            continue
        label, distance = nearest_base(xy)
        if distance > CELL_RADIUS:
            hall.append(obj.name)
            continue
        at_base[label].append(dict(name=obj.name, type=obj.type, distance_m=distance, centre_xy_m=list(xy)))

    cells = {}
    for cell, (home, destination) in HOMES.items():
        rows = sorted(at_base[home], key=lambda row: row["distance_m"])
        carried = [row for row in rows if row["name"] in covered[cell]]
        stays = [row for row in rows if row["name"] in fixed and row["name"] not in covered[cell]]
        left = [row for row in rows if row["name"] not in covered[cell] and row["name"] not in fixed]
        cells[cell] = dict(
            home_base=home,
            copied_to=destination,
            standing_here=len(rows),
            carried_count=len(carried),
            line_hardware_count=len(stays),
            left_behind_count=len(left),
            supply=supply_status(cell, covered[cell]),
            left_behind=left,
            line_hardware=[row["name"] for row in stays],
        )

    empty = {
        label: sorted(row["name"] for row in at_base[label])
        for label in CELL_BASES
        if label not in {home for home, _ in HOMES.values()}
    }

    after = transforms()
    unchanged = after == before
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                read_from=read_from,
                cell_radius_m=CELL_RADIUS,
                hall_footprint_m=HALL_FOOTPRINT_M,
                assignment="each object goes to the nearest of the six v07c bases",
                cells=cells,
                standing_at_empty_bases=empty,
                hall_object_count=len(hall),
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only completeness check of the per-cell duplication sets",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    assert unchanged, "The probe must not move anything"
    for cell, row in cells.items():
        print(
            f"  {cell} at {row['home_base']} -> {row['copied_to']}: standing={row['standing_here']} "
            f"carried={row['carried_count']} line={row['line_hardware_count']} left={row['left_behind_count']}"
        )
        supply = row["supply"]
        print(f"    supply {supply['prefixes']}: {supply['carried_count']}/{supply['member_count']} carried")
    for label, names in empty.items():
        print(f"  {label} (empty base): {len(names)} objects standing")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
