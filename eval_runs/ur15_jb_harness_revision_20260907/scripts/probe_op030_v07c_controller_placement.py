# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Find where each new cell's controller can stand, since it need not be mirrored [m].

The triangle probe settled the layout: of 118 box overlaps only two have surfaces that cross,
and both are a controller's long low p04 piece against the neighbouring station's. Everything
else passes, the air headers included, which were never touching at all.

A controller is a static cabinet joined to its cell by cable. Only the robot, its tools and
its supply have to be mirrored, because only they carry the kinematics. So the two contacts
are not interference to design around; they say the mirrored spot is taken and the cabinet
belongs somewhere else. The same cabinet is also what makes the cell envelope 2.41 m along Y
against a 2.3 m station pitch, so moving it inward settles both.

The question is whether the room exists. This slides each new cell's controller along Y and
measures the clearance at every step, against everything that stays and against the rest of
the mirrored cell, which will be standing there too. What comes back is the free intervals,
the smallest move that clears, and what limits each side.

The cabinet's p04 piece is not the cabinet. Every one of the twelve stations carries the same
0.538 x 1.956 x 0.193 plate and its robot pedestal stands on it, so the plate belongs to the
robot and mirrors with it. Sweeping it along with the cabinet is what made the first run find
no free position anywhere: the plate can never leave the pedestal standing on it. The plate is
therefore held at the mirrored position, treated as an obstacle to the cabinet, and asked a
different question -- how much of it would have to be cut away to clear what it lands on, and
whether the pedestal still stands wholly on what is left.

Nothing here decides the placement. It reports where a placement is possible.

Run: ``blender --background --python scripts/probe_op030_v07c_controller_placement.py``

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
from build_op030_stagger_static_v06 import digest  # noqa: E402
from probe_op030_v07c_mirror_clearance import (  # noqa: E402
    MIRRORS,
    SOURCE,
    SOURCE_SHA,
    box_of,
    covered_sets,
    hall_sized,
    mirror_box,
    moving_names,
    obstacles,
)

REPORT = ROOT / "audit/op030_v07c_controller_placement.json"

# The controller of each cell, by the name its parts carry.
CONTROLLERS = {"A": "source_0693", "B": "OP030B__source_0693", "C": "OP030C__source_0693"}
# p04 is grouped under the controller by the CAD import but is not part of the cabinet. It is
# the floor plate the robot pedestal stands on: every one of the twelve stations carries the
# same 0.538 x 1.956 x 0.193 plate, and the pedestal meets it at each. So it mirrors with the
# robot and cannot be carried around with the cabinet -- sweeping it together with the cabinet
# is what made the first run find no free position anywhere, since the plate can never leave
# the pedestal that stands on it.
FLOOR_PLATE_SUFFIX = "_p04"
# The robot pedestal, which the plate has to keep supporting after any trim.
PEDESTALS = {"A": "source_0576_m0050", "B": "OP030B__source_0576_m0050", "C": "OP030C__source_0576_m0050"}
# How far along Y the cabinet is allowed to travel, and how finely it is sampled.
TRAVEL_M = 2.000
STEP_M = 0.025
# An installation needs room to stand in, not just absence of contact.
MARGIN_M = 0.100
# Also reported, as the bare geometric limit.
TOUCH_M = 0.000


def boxes_of(names: list[str], station_y: float) -> tuple[list[str], list[tuple[np.ndarray, np.ndarray]]]:
    """Return the mirrored boxes of these objects, and the names they belong to [m].

    The names come back with the boxes because the two must stay aligned. Returning boxes
    alone and pairing them against the original list off by the objects that have no volume
    is what made the first run name the wrong limiting part.
    """
    kept, out = [], []
    for name in names:
        obj = bpy.data.objects.get(name)
        box = None if obj is None else box_of(obj)
        if box is None or hall_sized(*box):
            continue
        kept.append(name)
        out.append(mirror_box(*box, station_y))
    return kept, out


def clearance(box: tuple[np.ndarray, np.ndarray], lows: np.ndarray, highs: np.ndarray) -> tuple[float, int]:
    """Return the gap to the nearest of these boxes, negative when overlapping [m]."""
    separation = np.maximum(lows - box[1], box[0] - highs).max(axis=1)
    index = int(np.argmin(separation))
    return float(separation[index]), index


def sweep(
    controller: list[tuple[np.ndarray, np.ndarray]], lows: np.ndarray, highs: np.ndarray, names: list[str]
) -> list[dict]:
    """Measure the controller's clearance at every offset along Y [m]."""
    steps = int(round(TRAVEL_M / STEP_M))
    rows = []
    for step in range(-steps, steps + 1):
        offset = round(step * STEP_M, 4)
        shift = np.array([0.0, offset, 0.0])
        worst, limiting = None, None
        for low, high in controller:
            gap, index = clearance((low + shift, high + shift), lows, highs)
            if worst is None or gap < worst:
                worst, limiting = gap, names[index]
        rows.append(dict(offset_m=offset, clearance_m=worst, limited_by=limiting))
    return rows


def intervals(rows: list[dict], threshold: float) -> list[dict]:
    """Return the contiguous offset ranges that hold at least this clearance [m]."""
    spans, start, last = [], None, None
    for row in rows:
        if row["clearance_m"] >= threshold:
            start = row["offset_m"] if start is None else start
            last = row["offset_m"]
        elif start is not None:
            spans.append(dict(from_m=start, to_m=last))
            start = None
    if start is not None:
        spans.append(dict(from_m=start, to_m=last))
    return spans


def smallest_move(rows: list[dict], threshold: float) -> dict | None:
    """Return the offset of least travel that holds the threshold [m]."""
    allowed = [row for row in rows if row["clearance_m"] >= threshold]
    if not allowed:
        return None
    return min(allowed, key=lambda row: (abs(row["offset_m"]), -row["clearance_m"]))


def union(boxes: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the box enclosing these boxes [m]."""
    if not boxes:
        return None
    return np.array([box[0] for box in boxes]).min(0), np.array([box[1] for box in boxes]).max(0)


def plate_fit(
    plate: tuple[np.ndarray, np.ndarray],
    pedestal: tuple[np.ndarray, np.ndarray] | None,
    lows: np.ndarray,
    highs: np.ndarray,
    names: list[str],
) -> list[dict]:
    """Ask what a mirrored floor plate would have to give up to clear what it lands on [m].

    The plate carries the pedestal, so it cannot move. It can be shortened. For each thing it
    lands on, this gives the two ways to cut it back along Y and whether the pedestal still
    stands wholly on what is left.
    """
    low, high = plate
    separation = np.maximum(lows - high, low - highs).max(axis=1)
    rows = []
    for index in np.flatnonzero(separation < 0):
        obstacle_low, obstacle_high = lows[index], highs[index]
        options = []
        for label, new_low, new_high in (
            ("cut_back_the_high_end", low[1], float(obstacle_low[1])),
            ("cut_back_the_low_end", float(obstacle_high[1]), high[1]),
        ):
            remaining = float(new_high) - float(new_low)
            if remaining <= 0:
                options.append(dict(option=label, remaining_length_m=remaining, pedestal_supported=False))
                continue
            margin = None
            if pedestal is not None:
                margin = float(min(pedestal[0][1] - new_low, new_high - pedestal[1][1]))
            options.append(
                dict(
                    option=label,
                    cut_m=float(high[1] - new_high if label.endswith("high_end") else new_low - low[1]),
                    remaining_length_m=remaining,
                    pedestal_supported=None if margin is None else bool(margin >= 0.0),
                    pedestal_margin_m=margin,
                )
            )
        rows.append(
            dict(
                obstacle=names[index],
                overlap_y_m=float(min(high[1], obstacle_high[1]) - max(low[1], obstacle_low[1])),
                obstacle_y_m=[float(obstacle_low[1]), float(obstacle_high[1])],
                options=options,
            )
        )
    return sorted(rows, key=lambda row: -row["overlap_y_m"])


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Sweep each new cell's controller along Y and report where it fits."""
    assert digest(SOURCE) == SOURCE_SHA, "Probe the repaired candidate work 3 copies"
    assert not REPORT.exists(), "Preserve the existing report"
    covered, read_from = covered_sets()

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cells = {}
    for cell, (destination, station_y) in MIRRORS.items():
        moving = set(moving_names(cell, covered[cell])["names"])
        prefix = CONTROLLERS[cell]
        grouped = sorted(name for name in moving if name.startswith(prefix))
        plate = [name for name in grouped if name.endswith(FLOOR_PLATE_SUFFIX)]
        cabinet = [name for name in grouped if name not in set(plate)]
        # The plate stays at the mirrored position with the robot, so it is an obstacle to the
        # cabinet like anything else standing there.
        rest = sorted((moving - set(cabinet)) | set(plate))
        static_names, static_lows, static_highs = obstacles(moving)
        rest_names, rest_boxes = boxes_of(rest, station_y)
        lows = np.vstack([static_lows, np.array([box[0] for box in rest_boxes])])
        highs = np.vstack([static_highs, np.array([box[1] for box in rest_boxes])])
        names = static_names + [f"(mirrored own cell) {name}" for name in rest_names]
        cabinet_names, cabinet_boxes = boxes_of(cabinet, station_y)
        controller_boxes = cabinet_boxes
        rows = sweep(controller_boxes, lows, highs, names)
        at_mirror = next(row for row in rows if row["offset_m"] == 0.0)
        plate_names, plate_boxes = boxes_of(plate, station_y)
        pedestal_names = sorted(name for name in moving if name.startswith(PEDESTALS[cell]))
        _, pedestal_boxes = boxes_of(pedestal_names, station_y)
        plate_box, pedestal_box = union(plate_boxes), union(pedestal_boxes)
        cells[cell] = dict(
            destination=destination,
            station_y_m=station_y,
            controller_prefix=prefix,
            cabinet_parts=len(cabinet_boxes),
            cabinet_names=cabinet_names,
            floor_plate_names=plate,
            floor_plate_note="mirrored with the robot, not swept; it is the pedestal's base",
            floor_plate=dict(
                parts=plate_names,
                mirrored_box_m=None if plate_box is None else [plate_box[0].tolist(), plate_box[1].tolist()],
                pedestal_parts=len(pedestal_boxes),
                pedestal_mirrored_box_m=(
                    None if pedestal_box is None else [pedestal_box[0].tolist(), pedestal_box[1].tolist()]
                ),
                lands_on=(
                    []
                    if plate_box is None
                    else plate_fit(plate_box, pedestal_box, static_lows, static_highs, static_names)
                ),
            ),
            obstacle_count=len(names),
            at_mirrored_position=at_mirror,
            free_intervals_touch=intervals(rows, TOUCH_M),
            free_intervals_margin=intervals(rows, MARGIN_M),
            smallest_move_touch=smallest_move(rows, TOUCH_M),
            smallest_move_margin=smallest_move(rows, MARGIN_M),
            sweep=rows,
        )

    after = transforms()
    unchanged = after == before
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                read_from=read_from,
                travel_m=TRAVEL_M,
                step_m=STEP_M,
                margin_m=MARGIN_M,
                rule=(
                    "the controller is static and cable-tied to its cell, so it need not be "
                    "mirrored; only the robot, its tools and its supply carry the kinematics"
                ),
                measured_against="everything that stays, plus the mirrored boxes of the rest of the same cell",
                cells=cells,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only sweep of each new cell's controller along Y",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    assert unchanged, "The probe must not move anything"
    for cell, row in cells.items():
        mirror = row["at_mirrored_position"]
        print(
            f"  {cell} -> {row['destination']}: cabinet parts={row['cabinet_parts']} "
            f"at mirror clearance={mirror['clearance_m']:.3f} limited by {mirror['limited_by']}"
        )
        for landing in row["floor_plate"]["lands_on"]:
            best = max(
                (option for option in landing["options"] if option.get("pedestal_supported")),
                key=lambda option: option["remaining_length_m"],
                default=None,
            )
            summary = (
                "no cut keeps the pedestal on the plate"
                if best is None
                else (
                    f"cut {best['cut_m']:.3f} m, {best['remaining_length_m']:.3f} m left, "
                    f"pedestal margin {best['pedestal_margin_m']:.3f} m"
                )
            )
            print(f"    plate lands on {landing['obstacle']} over {landing['overlap_y_m']:.3f} m: {summary}")
        for label in ("touch", "margin"):
            move = row[f"smallest_move_{label}"]
            spans = row[f"free_intervals_{label}"]
            if move is None:
                print(f"    {label}: nowhere within {TRAVEL_M} m")
                continue
            print(
                f"    {label}: move {move['offset_m']:+.3f} m gives {move['clearance_m']:.3f} m; "
                f"free {[(span['from_m'], span['to_m']) for span in spans]}"
            )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
