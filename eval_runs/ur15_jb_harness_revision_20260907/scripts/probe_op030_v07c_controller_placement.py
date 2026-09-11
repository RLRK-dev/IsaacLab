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
# How far along Y the cabinet is allowed to travel, and how finely it is sampled.
TRAVEL_M = 2.000
STEP_M = 0.025
# An installation needs room to stand in, not just absence of contact.
MARGIN_M = 0.100
# Also reported, as the bare geometric limit.
TOUCH_M = 0.000


def boxes_of(names: list[str], station_y: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return the mirrored boxes of these objects, skipping what has no volume [m]."""
    out = []
    for name in names:
        obj = bpy.data.objects.get(name)
        box = None if obj is None else box_of(obj)
        if box is None or hall_sized(*box):
            continue
        out.append(mirror_box(*box, station_y))
    return out


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
        controller = sorted(name for name in moving if name.startswith(prefix))
        rest = sorted(moving - set(controller))
        static_names, static_lows, static_highs = obstacles(moving)
        rest_boxes = boxes_of(rest, station_y)
        lows = np.vstack([static_lows, np.array([box[0] for box in rest_boxes])])
        highs = np.vstack([static_highs, np.array([box[1] for box in rest_boxes])])
        names = static_names + [f"(mirrored own cell) {name}" for name in rest]
        controller_boxes = boxes_of(controller, station_y)
        rows = sweep(controller_boxes, lows, highs, names)
        at_mirror = next(row for row in rows if row["offset_m"] == 0.0)
        cells[cell] = dict(
            destination=destination,
            station_y_m=station_y,
            controller_prefix=prefix,
            controller_parts=len(controller_boxes),
            controller_names=controller,
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
            f"  {cell} -> {row['destination']}: parts={row['controller_parts']} "
            f"at mirror clearance={mirror['clearance_m']:.3f} limited by {mirror['limited_by']}"
        )
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
