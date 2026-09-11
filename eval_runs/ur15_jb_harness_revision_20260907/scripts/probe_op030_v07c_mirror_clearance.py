# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Ask whether the three mirror destinations are free to build in [m].

The completeness probe counted what stands near each base and found the three empty bases
are not empty: 2,241 objects near S1R, mostly OP020, and OP040's robots near S3R. That count
was taken from object centres, so it says things are nearby, not that they are in the way.

This measures the thing that decides it. Each member of a cell's moving set is mirrored by
``M(y0): (x, y) -> (-x, 2*y0 - y)``, which maps a world box to a world box because it is a
half turn about a vertical axis, and the mirrored box is tested against every object that is
not moving. What comes back is the list of obstacles the copy would be built inside of.

The moving set is the work 1 selection plus the cell's own supply, added by prefix because
the completeness probe measured A's 72 feeder objects and C's 120 carried at zero. Transport
and fixtures are not in it: the conveyor, the lift and the sensors are the line, the mirrored
cell works over the same line, and v06 kept them in place for that reason.

Box overlap is an upper bound on interference, not interference. Two boxes can overlap while
the shapes inside them miss each other, which is common for an arm. A clash here means look,
not stop.

Members whose box is taller than a cell are listed, because one stray vertex stretches a box
until it overlaps in Z with everything and leaves XY deciding alone. Members skipped for
being hall-sized are listed too, so nothing leaves the measurement silently.

A candidate here is not automatically fatal. The cells straddle the conveyor by design, so an
obstacle that is line hardware is expected. An obstacle owned by OP020 or OP040 is not.

Run: ``blender --background --python scripts/probe_op030_v07c_mirror_clearance.py``

Read-only. The scene is never saved and world transforms are compared before and after.
A geometric observation at its recorded timestamp, not a physical-validity verdict.
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
REPORT = ROOT / "audit/op030_v07c_mirror_clearance.json"

# Each cell, the base it is copied to, and the station centre line it is mirrored across.
MIRRORS = {"A": ("S1R", -1.700), "B": ("S2L", 0.600), "C": ("S3R", 2.900)}
# The cell's own supply, which the work 1 mapping does not reach for A and C.
SUPPLY_PREFIXES = {"A": ("OP030A_feeder",), "B": ("OP030B_wire_supply",), "C": ("OP030C_feeder",)}
# Supply that sits on the pallet and belongs to A alone. Reported, not moved: whether each
# cell needs its own is a question about the process, not about geometry.
PALLET_SUPPLY = ("OP030_supply_kit", "OP030_supply_fixed", "source_0587")
# A pair becomes a candidate when the gap between the boxes is smaller than this, overlap
# included. The first version required a 50 mm overlap on every axis instead, which made the
# threshold a filter: shallow overlaps and near misses were dropped before anything looked at
# the shapes, so a real contact under 50 mm of box overlap could not be found. The band is
# generous on purpose -- boxes are only a bound, and the triangle stage decides.
CANDIDATE_BAND_M = 0.050
# Anything this wide is the floor or the hall, and is not an obstacle to a cell.
HALL_FOOTPRINT_M = 8.0
WORST_LISTED = 15
# A cell is about 2.5 m tall. A member taller than this is reported, because one stray vertex
# stretches a box until it overlaps in Z with everything and leaves XY deciding alone.
SUSPECT_Z_M = 3.000


def box_of(obj: bpy.types.Object) -> tuple[np.ndarray, np.ndarray] | None:
    """Return an object's world axis-aligned box, or None when it has no volume [m]."""
    if obj.type not in {"MESH", "CURVE"}:
        return None
    vertices = getattr(obj.data, "vertices", None)
    if vertices is None or not len(vertices):
        return None
    world = _world_vertices(obj)
    return world.min(0), world.max(0)


def hall_sized(low: np.ndarray, high: np.ndarray) -> bool:
    """Return whether a box is the floor or the hall rather than a piece of equipment."""
    return max(high[0] - low[0], high[1] - low[1]) > HALL_FOOTPRINT_M


def mirror_box(low: np.ndarray, high: np.ndarray, station_y: float) -> tuple[np.ndarray, np.ndarray]:
    """Return the box M(y0) maps this box to. A half turn keeps boxes boxes [m]."""
    mirrored_low = np.array([-high[0], 2.0 * station_y - high[1], low[2]])
    mirrored_high = np.array([-low[0], 2.0 * station_y - low[1], high[2]])
    return mirrored_low, mirrored_high


def top_ancestor(obj: bpy.types.Object) -> str:
    """Return the name of the root this object hangs from, as its owner."""
    while obj.parent is not None:
        obj = obj.parent
    return obj.name


def moving_names(cell: str, covered: set[str]) -> dict:
    """Return the names a cell would carry, and where each came from."""
    supply = sorted(obj.name for obj in bpy.data.objects if obj.name.startswith(SUPPLY_PREFIXES[cell]))
    added = [name for name in supply if name not in covered]
    return dict(
        selection_count=len(covered),
        supply_count=len(supply),
        supply_added_count=len(added),
        supply_added=added,
        names=sorted(covered | set(supply)),
    )


def covered_sets() -> tuple[dict[str, set[str]], dict]:
    """Return each cell's work 1 selection and what it was read from."""
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
    )
    return covered, read_from


def obstacles(exclude: set[str]) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Return every object that is not moving, with its world box [m]."""
    names, lows, highs = [], [], []
    for obj in bpy.context.scene.objects:
        if obj.name in exclude:
            continue
        box = box_of(obj)
        if box is None or hall_sized(*box):
            continue
        names.append(obj.name)
        lows.append(box[0])
        highs.append(box[1])
    return names, np.array(lows), np.array(highs)


def clashes(low: np.ndarray, high: np.ndarray, lows: np.ndarray, highs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the obstacles within the band, and the signed gap to each [m].

    The gap is negative when the boxes overlap, and its size is then the overlap on the
    axis that overlaps least -- the distance one of them would have to move to separate.
    """
    separation = np.maximum(lows - high, low - highs).max(axis=1)
    hit = np.flatnonzero(separation < CANDIDATE_BAND_M)
    return hit, separation[hit]


def envelope(boxes: list[tuple[np.ndarray, np.ndarray]]) -> dict:
    """Return the combined box of a set of boxes [m]."""
    lows = np.array([box[0] for box in boxes])
    highs = np.array([box[1] for box in boxes])
    return dict(low_m=lows.min(0).tolist(), high_m=highs.max(0).tolist(), member_count=len(boxes))


def group_clashes(rows: list[dict]) -> list[dict]:
    """Collapse per-object candidates into one row per obstacle owner."""
    owners: dict[str, dict] = {}
    for row in rows:
        owner = owners.setdefault(
            row["obstacle_owner"],
            dict(
                owner=row["obstacle_owner"],
                obstacle_count=0,
                overlapping_count=0,
                deepest_m=0.0,
                closest_gap_m=None,
                moving=set(),
            ),
        )
        owner["obstacle_count"] += 1
        owner["overlapping_count"] += int(row["overlapping"])
        owner["deepest_m"] = max(owner["deepest_m"], row["depth_m"])
        if owner["closest_gap_m"] is None or row["gap_m"] < owner["closest_gap_m"]:
            owner["closest_gap_m"] = row["gap_m"]
        owner["moving"].add(row["moving"])
    for owner in owners.values():
        owner["moving_count"] = len(owner.pop("moving"))
    return sorted(owners.values(), key=lambda row: (-row["deepest_m"], -row["obstacle_count"]))


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Mirror each cell's set and report what already stands where it would go."""
    assert digest(SOURCE) == SOURCE_SHA, "Probe the repaired candidate work 3 copies"
    assert MANIFEST.exists() and digest(MANIFEST) == MANIFEST_SHA, "Read the v06 static manifest"
    assert not REPORT.exists(), "Preserve the existing report"
    covered, read_from = covered_sets()

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cells = {}
    for cell, (destination, station_y) in MIRRORS.items():
        moving = moving_names(cell, covered[cell])
        names = set(moving["names"])
        obstacle_names, lows, highs = obstacles(names)
        source_boxes, mirrored_boxes, rows = [], [], []
        no_geometry, hall_skipped, tall = [], [], []
        for name in sorted(names):
            obj = bpy.data.objects.get(name)
            box = None if obj is None else box_of(obj)
            if box is None:
                no_geometry.append(name)
                continue
            if hall_sized(*box):
                hall_skipped.append(name)
                continue
            extent = float(box[1][2] - box[0][2])
            if extent > SUSPECT_Z_M:
                tall.append(dict(name=name, z_low_m=float(box[0][2]), z_high_m=float(box[1][2]), z_extent_m=extent))
            source_boxes.append(box)
            mirrored = mirror_box(*box, station_y)
            mirrored_boxes.append(mirrored)
            hit, gaps = clashes(mirrored[0], mirrored[1], lows, highs)
            for index, value in zip(hit, gaps):
                obstacle = bpy.data.objects[obstacle_names[index]]
                rows.append(
                    dict(
                        moving=name,
                        obstacle=obstacle.name,
                        obstacle_owner=top_ancestor(obstacle),
                        gap_m=float(value),
                        depth_m=float(max(0.0, -value)),
                        overlapping=bool(value < 0.0),
                    )
                )
        worst = sorted(rows, key=lambda row: row["gap_m"])[:WORST_LISTED]
        cells[cell] = dict(
            destination=destination,
            station_y_m=station_y,
            mirror_rule=f"M({station_y}): (x, y) -> (-x, {2.0 * station_y:.3f} - y)",
            moving=dict(moving, names=len(moving["names"])),
            measured_members=len(source_boxes),
            without_geometry=len(no_geometry),
            hall_sized_skipped=hall_skipped,
            tall_members=sorted(tall, key=lambda row: -row["z_extent_m"])[:WORST_LISTED],
            source_envelope=envelope(source_boxes) if source_boxes else None,
            mirrored_envelope=envelope(mirrored_boxes) if mirrored_boxes else None,
            candidate_count=len(rows),
            overlapping_count=sum(row["overlapping"] for row in rows),
            clashing_moving_members=len({row["moving"] for row in rows if row["overlapping"]}),
            by_owner=group_clashes(rows),
            worst=worst,
        )

    pallet = {
        prefix: sorted(obj.name for obj in bpy.data.objects if obj.name.startswith(prefix)) for prefix in PALLET_SUPPLY
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
                candidate_band_m=CANDIDATE_BAND_M,
                hall_footprint_m=HALL_FOOTPRINT_M,
                moving_set_rule="work 1 selection plus the cell's own supply by prefix; line hardware stays",
                cells=cells,
                pallet_supply_on_a_only={prefix: len(names) for prefix, names in pallet.items()},
                pallet_supply_names=pallet,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only box clearance of each mirrored cell against what already stands there",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    assert unchanged, "The probe must not move anything"
    for cell, row in cells.items():
        moving = row["moving"]
        print(
            f"  {cell} -> {row['destination']}: moving={moving['names']} "
            f"(selection {moving['selection_count']} + supply added {moving['supply_added_count']}) "
            f"candidates={row['candidate_count']} overlapping={row['overlapping_count']} "
            f"members_hit={row['clashing_moving_members']}"
        )
        for owner in row["by_owner"][:5]:
            print(
                f"    {owner['owner']}: {owner['obstacle_count']} obstacles "
                f"({owner['overlapping_count']} overlapping), deepest {owner['deepest_m']:.3f} m, "
                f"closest gap {owner['closest_gap_m']:.3f} m, hits {owner['moving_count']} moving"
            )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
