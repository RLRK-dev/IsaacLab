# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Ask whether the room sweep's 5 mm step could have stepped over anything [m].

The sweep slides each cable in 5 mm steps and looks for overlap at each position, so a part it
meets over a shorter distance than that could fall between two positions and never be seen.

What decides this is not how thin a part is. A thin plate standing across the path is met over
a band as long as the plate is thick plus the cable is wide, and the cable is 56 mm across, so
a 3 mm plate is still met over some 59 mm of travel. What can be stepped over is a meeting that
is short, which is a property of the pair and of the direction, not of either part alone. A
part grazing the cable's shoulder can do it however thick the part is.

So the meeting itself is measured. The same sweep is repeated at 1 mm and every distance at
which each neighbour is met is recorded, which gives the band of travel over which that
neighbour is in contact. A band shorter than the coarse step is one the coarse sweep could
have missed, and the shortest band found is the margin the 5 mm step was running on.

The thickness the review asked for is reported as well, for each neighbour along each of the
three directions, since it is the part of the question that can be answered without a sweep.

Run: ``blender --background --python scripts/check_op030_v07c_cable_room_step.py``

Read-only. The scene is never saved and world matrices are compared before and after.
A geometric observation at its recorded timestamp, not a physical-validity verdict.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_op030_stagger_static_v06 import digest, geometry  # noqa: E402

SOURCE = ROOT / "analysis/op030_v07c_stagger_both_sides.blend"
SOURCE_SHA = "4e7c5b0d8b00b904c618dac757cf4c97c88de620898e7c7dcca0c3b0eb46ea51"
SWEEP = ROOT / "audit/op030_v07c_cable_room_sweep.json"
REPORT = ROOT / "audit/op030_v07c_cable_room_step_check.json"

COARSE_STEP_M = 0.005
FINE_STEP_M = 0.001
REACH_M = 0.500
AXIS_OF = {"+X": 0, "-X": 0, "+Z": 2}


def tree_of(vertices: np.ndarray, faces: np.ndarray) -> BVHTree:
    """Return a BVH over the triangles as given."""
    return BVHTree.FromPolygons(
        [tuple(v) for v in vertices.tolist()], [tuple(f) for f in faces.tolist()], all_triangles=True
    )


def bands(distances: list[float], step: float) -> list[dict]:
    """Return the runs of consecutive distances as bands of travel [m]."""
    out = []
    for distance in sorted(distances):
        if out and distance - out[-1]["to_m"] <= step * 1.5:
            out[-1]["to_m"] = distance
        else:
            out.append(dict(from_m=distance, to_m=distance))
    for band in out:
        band["length_m"] = band["to_m"] - band["from_m"] + step
    return out


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Measure every meeting's band of travel, and each neighbour's thickness, for the record."""
    assert digest(SOURCE) == SOURCE_SHA, "Check the six-cell candidate"
    assert not REPORT.exists(), "Preserve the existing check"
    sweep = json.loads(SWEEP.read_text())
    assert sweep["source_sha256"] == SOURCE_SHA, "The sweep is of a different scene"
    assert sweep["method"]["step_m"] == COARSE_STEP_M, "The sweep used a different step"

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cables, shortest_overall = {}, None
    for name, recorded in sweep["cables"].items():
        vertices, faces = geometry(bpy.data.objects[name])
        neighbours = {}
        for other, row in recorded["neighbours"].items():
            other_vertices, other_faces = geometry(bpy.data.objects[other])
            low, high = other_vertices.min(0), other_vertices.max(0)
            neighbours[other] = dict(
                low=low,
                high=high,
                tree=tree_of(other_vertices, other_faces),
                already_touching=row["already_touching"],
                thickness=(high - low).tolist(),
            )

        thin = {
            label: sorted(
                other for other, entry in neighbours.items() if entry["thickness"][AXIS_OF[label]] < COARSE_STEP_M
            )
            for label in AXIS_OF
        }
        thinnest = {
            label: min(entry["thickness"][AXIS_OF[label]] for entry in neighbours.values()) for label in AXIS_OF
        }

        directions = {}
        for label, axis in (("+X", (1.0, 0.0, 0.0)), ("-X", (-1.0, 0.0, 0.0)), ("+Z", (0.0, 0.0, 1.0))):
            step_vector = np.asarray(axis) * FINE_STEP_M
            met: dict[str, list[float]] = {}
            for index in range(1, int(round(REACH_M / FINE_STEP_M)) + 1):
                moved = vertices + step_vector * index
                moved_low, moved_high = moved.min(0), moved.max(0)
                near = [
                    other
                    for other, entry in neighbours.items()
                    if not entry["already_touching"]
                    and not np.any(entry["low"] > moved_high)
                    and not np.any(moved_low > entry["high"])
                ]
                if not near:
                    continue
                moved_tree = tree_of(moved, faces)
                for other in near:
                    if moved_tree.overlap(neighbours[other]["tree"]):
                        met.setdefault(other, []).append(float(FINE_STEP_M * index))
            rows = {}
            for other, distances in met.items():
                found = bands(distances, FINE_STEP_M)
                rows[other] = dict(
                    first_met_at_m=min(distances),
                    bands=found,
                    shortest_band_m=min(band["length_m"] for band in found),
                    could_be_stepped_over=bool(min(band["length_m"] for band in found) < COARSE_STEP_M),
                )
            shortest = min((row["shortest_band_m"] for row in rows.values()), default=None)
            if shortest is not None and (shortest_overall is None or shortest < shortest_overall):
                shortest_overall = shortest
            coarse = recorded["sweeps"][label]["everything_it_meets"]
            fine_first = min((row["first_met_at_m"] for row in rows.values()), default=None)
            fine_name = min(rows.items(), key=lambda row: row[1]["first_met_at_m"])[0] if rows else None
            directions[label] = dict(
                met=dict(sorted(rows.items())),
                shortest_band_m=shortest,
                any_could_be_stepped_over=any(row["could_be_stepped_over"] for row in rows.values()),
                first_met_at_1mm=dict(name=fine_name, at_m=fine_first),
                first_met_at_5mm=dict(name=coarse["first_met"], at_m=coarse["first_met_at_m"]),
                agrees_within_one_coarse_step=bool(
                    fine_first is None
                    and coarse["first_met_at_m"] is None
                    or (
                        fine_first is not None
                        and coarse["first_met_at_m"] is not None
                        and abs(coarse["first_met_at_m"] - fine_first) <= COARSE_STEP_M + 1e-9
                    )
                ),
            )
            print(
                f"    {label}: shortest meeting {shortest if shortest is None else round(shortest, 3)} m,"
                f" first at 1 mm {fine_name} @ {fine_first}, at 5 mm {coarse['first_met']}"
                f" @ {coarse['first_met_at_m']}"
            )

        cables[name] = dict(
            neighbours=len(neighbours),
            thinnest_neighbour_m=thinnest,
            neighbours_thinner_than_the_step=thin,
            directions=directions,
        )
        print(f"  {name}: {len(neighbours)} neighbours, thinnest along the sweep axes {thinnest}")

    after = transforms()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                scope="Whether the room sweep's step could have stepped over a neighbour",
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                read_from=dict(sweep=str(SWEEP.relative_to(ROOT)), sweep_sha256=digest(SWEEP)),
                method=dict(
                    coarse_step_m=COARSE_STEP_M,
                    fine_step_m=FINE_STEP_M,
                    swept_to_m=REACH_M,
                    what_decides_it=(
                        "the band of travel over which a neighbour is in contact, not its thickness:"
                        " a part is stepped over only when that band is shorter than the step"
                    ),
                    thickness_note=(
                        "thickness is reported because it was asked for; it bounds nothing on its own,"
                        " since the cable is 56 mm across and adds its own width to every meeting"
                    ),
                ),
                what_this_does_not_give=[
                    "anything about directions the sweep did not take",
                    "contact beyond 0.5 m of travel",
                    "a guarantee for a step finer than 1 mm, which was not tried",
                    "any judgement of whether the room found is enough",
                ],
                shortest_meeting_m=shortest_overall,
                shorter_than_the_coarse_step=bool(shortest_overall is not None and shortest_overall < COARSE_STEP_M),
                every_first_contact_agrees=all(
                    row["agrees_within_one_coarse_step"]
                    for cable in cables.values()
                    for row in cable["directions"].values()
                ),
                cables=cables,
                scene_world_transforms_unchanged=before == after,
                saved_scene=False,
                formal_physical_validity_verdict=None,
            ),
            indent=1,
        )
        + "\n"
    )
    print(f"  shortest meeting anywhere: {shortest_overall} m against a {COARSE_STEP_M} m step")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
