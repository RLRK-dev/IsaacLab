# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Measure how far each crossing cable could be moved before it meets something [m].

Work 4 has to separate two pairs of cable runs. How far to move them and in which direction is
not decided here: a bend radius, a support pitch and a required separation belong to the real
cable. What can be measured is the room. Each cable is slid in 5 mm steps up to half a metre
along +X, -X and +Z, and the first thing it meets is reported with the distance to it.

Two kinds of neighbour would otherwise end the sweep at the first step and mean nothing by it.

The cabinet and pedestal the cable is attached to move with it, so they are set aside -- but by
measurement, not by name: a part is treated as an attachment when it is already touching the
cable, within a millimetre, and its name ends in one of the fittings' suffixes. Guessing from
the name alone would have been wrong here, since one of the four cables is attached to a part
from an entirely different source group.

The air main's boxes are 0.95 by 1.82 by 3.12 m, far larger than the pipe inside them, so a box
test has the cable meeting them immediately while no triangle of either touches. Everything
here is judged by triangles. The air main is also reported separately, so the answer can be
read either with it or without it.

Every neighbour's closest approach to the cable where it stands is reported as well, which is
what the sweep cannot say: a part 3 mm to the side does not stop a move along X.

Run: ``blender --background --python scripts/sweep_op030_v07c_cable_room.py``

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
SURVEY = ROOT / "audit/op030_v07c_routing_survey.json"
# The scene as it was before the three cells were copied into it, used at the end to ask whether
# a contact found in the candidate was already there.
BEFORE = ROOT / "analysis/op030_v07c_support_repair.blend"
BEFORE_SHA = "1091683a5d15072e46553b487a30d58a21050bf40515f0d09b9d4d879c01ecce"
REPORT = ROOT / "audit/op030_v07c_cable_room_sweep.json"

# The four runs that cross: the two copies and the two they cross.
CABLES = (
    "OP030_S1R__source_0693_m0120_p04",
    "source_0681_m0108_p04",
    "OP030_S3R__OP030C__source_0693_m0120_p04",
    "source_0705_m0132_p04",
)
DIRECTIONS = {"+X": (1.0, 0.0, 0.0), "-X": (-1.0, 0.0, 0.0), "+Z": (0.0, 0.0, 1.0)}
STEP_M = 0.005
REACH_M = 0.500
ROOM_MARKS_M = (0.100, 0.200)
# A part already touching the cable this closely, whose name ends in a fitting's suffix, is
# taken to be what the cable is attached to.
ATTACHED_M = 0.001
FITTING_SUFFIXES = ("_p00", "_p01", "_p03", "_p05")
# Measuring every vertex of a neighbour against the cable is the exact thing to do and a slow
# one on a part with a hundred thousand of them. Above this many the neighbour's vertices are
# thinned evenly; the cable's own are always measured in full, and the figure stays what it was,
# an upper bound.
VERTEX_CAP = 4000
# The air main, whose box is far larger than the pipe in it.
AIR_MAIN = ("source_0779", "source_0780")


def box_of(obj: bpy.types.Object) -> tuple[np.ndarray, np.ndarray] | None:
    """Return an object's world axis-aligned box, or None if it has no geometry [m]."""
    if obj.type not in {"MESH", "CURVE"}:
        return None
    vertices = getattr(obj.data, "vertices", None)
    if vertices is None or not len(vertices):
        return None
    world, faces = geometry(obj)
    if not len(world) or not len(faces):
        return None
    return world.min(0), world.max(0)


def tree_of(vertices: np.ndarray, faces: np.ndarray) -> BVHTree:
    """Return a BVH over the triangles as given."""
    return BVHTree.FromPolygons(
        [tuple(v) for v in vertices.tolist()], [tuple(f) for f in faces.tolist()], all_triangles=True
    )


def nearest_gap(tree_a, points_a, tree_b, points_b) -> float:
    """Return the smaller of the two vertex-to-surface measurements, an upper bound [m]."""
    best = None
    for tree, points in ((tree_b, points_a), (tree_a, points_b)):
        if len(points) > VERTEX_CAP:
            points = points[:: max(1, len(points) // VERTEX_CAP)]
        for point in points:
            _, _, _, distance = tree.find_nearest(tuple(point))
            if distance is not None and (best is None or distance < best):
                best = float(distance)
    return float("inf") if best is None else best


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Sweep each crossing cable three ways and write down what it meets and how far off."""
    assert digest(SOURCE) == SOURCE_SHA, "Sweep the six-cell candidate"
    assert not REPORT.exists(), "Preserve the existing sweep"
    survey = json.loads(SURVEY.read_text())
    assert survey["source_sha256"] == SOURCE_SHA, "The survey is of a different scene"

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    boxes = {}
    for obj in bpy.context.scene.objects:
        box = box_of(obj)
        if box is not None:
            boxes[obj.name] = box

    cables = {}
    for name in CABLES:
        vertices, faces = geometry(bpy.data.objects[name])
        low, high = vertices.min(0), vertices.max(0)
        cable_tree = tree_of(vertices, faces)

        # Anything whose box comes within reach of the cable once it has been slid its full way.
        reach_low = low - REACH_M
        reach_high = high + REACH_M
        candidates = {}
        for other, (other_low, other_high) in boxes.items():
            if other == name:
                continue
            if np.any(other_low > reach_high) or np.any(reach_low > other_high):
                continue
            other_vertices, other_faces = geometry(bpy.data.objects[other])
            candidates[other] = dict(
                low=other_low,
                high=other_high,
                tree=tree_of(other_vertices, other_faces),
                vertices=other_vertices,
            )

        neighbours = {}
        for other, entry in candidates.items():
            gap = nearest_gap(cable_tree, vertices, entry["tree"], entry["vertices"])
            # A part the cable is already in contact with before it moves is not something the
            # cable meets by moving. The floor it rests on, the fittings that hold it and the
            # run it already crosses would otherwise all be met at the first 5 mm step and the
            # sweep would report nothing but them.
            entry["gap"] = gap
            entry["already_touching"] = bool(cable_tree.overlap(entry["tree"]))
            entry["attached"] = bool(gap <= ATTACHED_M and other.endswith(FITTING_SUFFIXES))
            entry["air_main"] = any(part in other for part in AIR_MAIN)
            neighbours[other] = dict(
                closest_gap_m=None if gap == float("inf") else gap,
                already_touching=entry["already_touching"],
                attached=entry["attached"],
                air_main=entry["air_main"],
            )

        # The parts the cable is held by belong to its own fittings and to the pedestal's, and
        # both move with it. Which source groups those are is read off the attachments that were
        # measured, not guessed: one of the four cables is held by a group that is not its own.
        own_group = name.rsplit("_p", 1)[0]
        attached_groups = sorted(
            {own_group} | {other.rsplit("_p", 1)[0] for other, entry in candidates.items() if entry["attached"]}
        )

        def of_an_attached_group(other: str) -> bool:
            return other.endswith(FITTING_SUFFIXES) and any(
                other.rsplit("_p", 1)[0] == group for group in attached_groups
            )

        sweeps = {}
        for label, axis in DIRECTIONS.items():
            step_vector = np.asarray(axis) * STEP_M
            met = {}
            outstanding = {other for other, entry in candidates.items() if not entry["already_touching"]}
            for index in range(1, int(round(REACH_M / STEP_M)) + 1):
                if not outstanding:
                    break
                moved = vertices + step_vector * index
                moved_low, moved_high = moved.min(0), moved.max(0)
                near = [
                    other
                    for other in outstanding
                    if not np.any(candidates[other]["low"] > moved_high)
                    and not np.any(moved_low > candidates[other]["high"])
                ]
                if not near:
                    continue
                moved_tree = tree_of(moved, faces)
                for other in near:
                    if moved_tree.overlap(candidates[other]["tree"]):
                        met[other] = float(STEP_M * index)
                        outstanding.discard(other)
            order = sorted(met.items(), key=lambda row: (row[1], row[0]))
            policies = {
                "everything_it_meets": lambda other: True,
                "without_the_air_main": lambda other: not candidates[other]["air_main"],
                "without_the_air_main_or_what_holds_it": (
                    lambda other: not candidates[other]["air_main"] and not of_an_attached_group(other)
                ),
            }
            row = dict(
                step_m=STEP_M,
                swept_to_m=REACH_M,
                met=[dict(name=other, at_m=distance) for other, distance in order],
            )
            for policy, keep in policies.items():
                first = next(((other, distance) for other, distance in order if keep(other)), None)
                # Put the clearance back on the step grid. Taking one step off the first contact
                # in binary gives 0.09999999999999999 for a run that is clear to exactly 100 mm,
                # and asking whether that is 100 mm answers no.
                clear = REACH_M if first is None else round((first[1] - STEP_M) / STEP_M) * STEP_M
                row[policy] = dict(
                    first_met=None if first is None else first[0],
                    first_met_at_m=None if first is None else first[1],
                    clear_to_at_least_m=clear,
                    **{f"room_for_{int(mark * 1000)}mm": bool(clear + 1e-9 >= mark) for mark in ROOM_MARKS_M},
                )
            sweeps[label] = row
            loose = row["without_the_air_main_or_what_holds_it"]
            print(
                f"    {label}: clear to {loose['clear_to_at_least_m']:.3f} m, then"
                f" {loose['first_met'] or 'nothing within 0.5 m'}"
                f"   (counting what holds it: {row['without_the_air_main']['first_met'] or 'nothing'}"
                f" at {row['without_the_air_main']['first_met_at_m']})"
            )

        tight = sorted(
            ((row["closest_gap_m"], other) for other, row in neighbours.items() if row["closest_gap_m"] is not None),
        )
        cables[name] = dict(
            box_m=[low.tolist(), high.tolist()],
            run_length_m=survey["cables"][name]["run_length_m"],
            candidates=len(candidates),
            attached=sorted(other for other, row in neighbours.items() if row["attached"]),
            attached_groups=attached_groups,
            already_touching=sorted(other for other, row in neighbours.items() if row["already_touching"]),
            air_main_candidates=sorted(other for other, row in neighbours.items() if row["air_main"]),
            sweeps=sweeps,
            neighbours=dict(sorted(neighbours.items())),
            closest_five=[dict(name=other, closest_gap_m=gap) for gap, other in tight[:5]],
        )
        print(
            f"  {name}: {len(candidates)} neighbours, already touching"
            f" {cables[name]['already_touching']}, attached {cables[name]['attached']}"
        )

    after = transforms()
    unchanged = before == after

    # Four of the contacts the sweep set aside are between parts that work 3 never touched. Ask
    # the scene as it stood before the copies whether they were already like that, so a contact
    # is not read as something this work caused.
    already = sorted({(name, other) for name, row in cables.items() for other in row["already_touching"]})
    assert digest(BEFORE) == BEFORE_SHA, "The scene from before the copies is not the one built from"
    bpy.ops.wm.open_mainfile(filepath=str(BEFORE))
    bpy.context.scene.frame_set(1)
    before_before = transforms()
    was_already = []
    trees = {}
    for first, second in already:
        present = [part for part in (first, second) if part in bpy.data.objects]
        if len(present) < 2:
            was_already.append(
                dict(pair=[first, second], in_the_earlier_scene=False, missing=sorted({first, second} - set(present)))
            )
            continue
        for part in (first, second):
            if part not in trees:
                trees[part] = geometry(bpy.data.objects[part])
        first_vertices, first_faces = trees[first]
        second_vertices, second_faces = trees[second]
        first_tree, second_tree = tree_of(first_vertices, first_faces), tree_of(second_vertices, second_faces)
        was_already.append(
            dict(
                pair=[first, second],
                in_the_earlier_scene=True,
                touching_there=bool(first_tree.overlap(second_tree)),
                closest_gap_there_m=nearest_gap(first_tree, first_vertices, second_tree, second_vertices),
            )
        )
    after_before = transforms()
    for row in was_already:
        if row["in_the_earlier_scene"]:
            print(
                f"  before the copies: {row['pair'][0][:38]} x {row['pair'][1][:38]}"
                f" touching {row['touching_there']} at {row['closest_gap_there_m']:.6f} m"
            )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                scope="How far each crossing cable can be slid before it meets something",
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                read_from=dict(survey=str(SURVEY.relative_to(ROOT)), survey_sha256=digest(SURVEY)),
                method=dict(
                    step_m=STEP_M,
                    swept_to_m=REACH_M,
                    directions=DIRECTIONS,
                    contact="triangle overlap on evaluated meshes, never boxes",
                    boxes_used_only_to="choose which neighbours to test at each step",
                    attachment=(
                        f"already within {ATTACHED_M} m of the cable and named with one of"
                        f" {list(FITTING_SUFFIXES)}; measured, not guessed from the name"
                    ),
                    set_aside_from_the_sweep=(
                        "every part whose triangles already meet the cable where it stands, which is"
                        " what the cable rests on and is held by, and the run it already crosses"
                    ),
                    neighbour_vertex_cap=VERTEX_CAP,
                    policies=dict(
                        everything_it_meets="every part the cable reaches, in the order it reaches them",
                        without_the_air_main="the air main set aside, its box being far larger than its pipe",
                        without_the_air_main_or_what_holds_it=(
                            "also the fittings of every source group the cable is attached to, which move with it"
                        ),
                    ),
                    air_main=(
                        f"objects whose name carries {list(AIR_MAIN)} are reported both ways, because their"
                        " boxes are far larger than the pipe inside them"
                    ),
                    closest_gap="the smaller of the two vertex-to-surface measurements, an upper bound",
                ),
                what_this_does_not_give=[
                    "how far the cable should move, which is a required separation and belongs to the real cable",
                    "the bend radius a moved run would need",
                    "whether the cable can reach its fittings after a move: the ends are held and do not slide",
                    "room along Y or downward, which was not asked for",
                    "room for a route that is not a straight slide",
                    "any judgement of whether a move is acceptable",
                ],
                cables=cables,
                contacts_before_the_copies=dict(
                    scene=str(BEFORE.relative_to(ROOT)),
                    scene_sha256=BEFORE_SHA,
                    why="so a contact found in the candidate is not read as something work 3 caused",
                    pairs=was_already,
                    world_transforms_unchanged=before_before == after_before,
                ),
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                formal_physical_validity_verdict=None,
            ),
            indent=1,
        )
        + "\n"
    )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
