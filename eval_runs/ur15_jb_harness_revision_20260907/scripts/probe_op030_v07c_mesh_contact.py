# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Decide the box overlaps at triangle level, so the layout question can be settled [m].

The clearance probe compares axis-aligned boxes, which is an upper bound: two boxes overlap
whenever the shapes inside them might touch, and for an arm they usually do not. It found
118 box overlaps, and one of them decides something -- S3R against OP040's left robot, 13
overlaps, deepest 0.162 m. A box overlap there is not a reason to move a robot.

So this takes every pair the box stage produces and asks the exact question of the triangles,
through the same BVH Blender uses for its own collision queries. A pair either has triangles
that cross, or it has a shortest distance and no contact. Both are reported.

The candidate pairs are recomputed here rather than read back, so this stands on its own and
cannot drift from a stale report. It shares the moving-set rule, the mirror and the box stage
with ``probe_op030_v07c_mirror_clearance.py`` by importing them.

Nearest distance is measured from one shape's vertices to the other shape's surface, so it is
an upper bound on the true surface-to-surface gap. It is reported to rank pairs, not to
certify a clearance.

Run: ``blender --background --python scripts/probe_op030_v07c_mesh_contact.py``

Read-only. The scene is never saved and world transforms are compared before and after.
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
from probe_op030_v07c_mirror_clearance import (  # noqa: E402
    MIRRORS,
    SOURCE,
    SOURCE_SHA,
    box_of,
    clashes,
    covered_sets,
    hall_sized,
    mirror_box,
    moving_names,
    obstacles,
    top_ancestor,
)

REPORT = ROOT / "audit/op030_v07c_mesh_contact.json"
# Pairs further apart than this are not worth listing once they are known not to touch.
REPORTED_GAP_M = 1.000


def mirrored_geometry(obj: bpy.types.Object, station_y: float) -> tuple[np.ndarray, np.ndarray]:
    """Return the object's evaluated triangles after M(y0) [m]."""
    vertices, faces = geometry(obj)
    mirrored = vertices.copy()
    mirrored[:, 0] = -mirrored[:, 0]
    mirrored[:, 1] = 2.0 * station_y - mirrored[:, 1]
    return mirrored, faces


def tree_of(vertices: np.ndarray, faces: np.ndarray) -> BVHTree | None:
    """Return a BVH over world triangles, or None when there are none."""
    if not len(faces):
        return None
    return BVHTree.FromPolygons(
        [tuple(v) for v in vertices.tolist()], [tuple(f) for f in faces.tolist()], all_triangles=True
    )


def nearest_gap(tree: BVHTree, vertices: np.ndarray) -> float | None:
    """Return the shortest distance from these vertices to that surface [m]."""
    best = None
    for vertex in vertices.tolist():
        _, _, _, distance = tree.find_nearest(vertex)
        if distance is not None and (best is None or distance < best):
            best = float(distance)
    return best


def candidates(cell: str, covered: set[str]) -> tuple[list[dict], dict]:
    """Return the box-stage pairs for one cell, recomputed from the scene."""
    destination, station_y = MIRRORS[cell]
    moving = moving_names(cell, covered)
    names = set(moving["names"])
    obstacle_names, lows, highs = obstacles(names)
    rows = []
    for name in sorted(names):
        obj = bpy.data.objects.get(name)
        box = None if obj is None else box_of(obj)
        if box is None or hall_sized(*box):
            continue
        mirrored = mirror_box(*box, station_y)
        hit, depth = clashes(mirrored[0], mirrored[1], lows, highs)
        rows.extend(
            dict(moving=name, obstacle=obstacle_names[index], box_depth_m=float(value))
            for index, value in zip(hit, depth)
        )
    return rows, dict(destination=destination, station_y_m=station_y, moving_count=len(names))


def resolve(rows: list[dict], station_y: float) -> list[dict]:
    """Answer each candidate pair at triangle level."""
    trees: dict[str, BVHTree | None] = {}
    mirrored_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    resolved = []
    for row in rows:
        moving = bpy.data.objects[row["moving"]]
        obstacle = bpy.data.objects[row["obstacle"]]
        if row["moving"] not in mirrored_cache:
            mirrored_cache[row["moving"]] = mirrored_geometry(moving, station_y)
        vertices, faces = mirrored_cache[row["moving"]]
        moving_tree = trees.setdefault("m:" + row["moving"], tree_of(vertices, faces))
        obstacle_vertices, obstacle_faces = geometry(obstacle)
        obstacle_tree = trees.setdefault("o:" + row["obstacle"], tree_of(obstacle_vertices, obstacle_faces))
        if moving_tree is None or obstacle_tree is None:
            resolved.append(dict(row, contact=None, note="one side has no triangles"))
            continue
        overlap = moving_tree.overlap(obstacle_tree)
        gap = None if overlap else nearest_gap(obstacle_tree, vertices)
        resolved.append(
            dict(
                row,
                owner=top_ancestor(obstacle),
                contact=bool(overlap),
                triangle_pairs=len(overlap),
                nearest_m=gap,
            )
        )
    return resolved


def summarize(resolved: list[dict]) -> list[dict]:
    """Collapse resolved pairs into one row per obstacle owner."""
    owners: dict[str, dict] = {}
    for row in resolved:
        owner = owners.setdefault(
            row.get("owner", "unknown"),
            dict(owner=row.get("owner", "unknown"), pairs=0, contacts=0, triangle_pairs=0, nearest_m=None),
        )
        owner["pairs"] += 1
        owner["contacts"] += int(bool(row.get("contact")))
        owner["triangle_pairs"] += row.get("triangle_pairs", 0)
        gap = row.get("nearest_m")
        if gap is not None and (owner["nearest_m"] is None or gap < owner["nearest_m"]):
            owner["nearest_m"] = gap
    return sorted(owners.values(), key=lambda row: (-row["contacts"], -row["triangle_pairs"]))


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Resolve every box overlap at triangle level and report contact or gap."""
    assert digest(SOURCE) == SOURCE_SHA, "Probe the repaired candidate work 3 copies"
    assert not REPORT.exists(), "Preserve the existing report"
    covered, read_from = covered_sets()

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cells = {}
    for cell in MIRRORS:
        rows, meta = candidates(cell, covered[cell])
        resolved = resolve(rows, meta["station_y_m"])
        touching = [row for row in resolved if row.get("contact")]
        clear = sorted(
            (row for row in resolved if row.get("contact") is False and (row["nearest_m"] or 0) <= REPORTED_GAP_M),
            key=lambda row: row["nearest_m"] if row["nearest_m"] is not None else 1e9,
        )
        cells[cell] = dict(
            meta,
            candidate_pairs=len(rows),
            contact_pairs=len(touching),
            clear_pairs=len(resolved) - len(touching),
            by_owner=summarize(resolved),
            contacts=sorted(touching, key=lambda row: -row["triangle_pairs"]),
            closest_clear=clear[:20],
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
                method="box stage recomputed, then BVH triangle overlap on evaluated meshes",
                nearest_distance_note="vertex to surface, an upper bound on the true gap",
                reported_gap_m=REPORTED_GAP_M,
                cells=cells,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only triangle-level resolution of the mirrored cell clearances",
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
            f"  {cell} -> {row['destination']}: candidates={row['candidate_pairs']} "
            f"contact={row['contact_pairs']} clear={row['clear_pairs']}"
        )
        for owner in row["by_owner"]:
            gap = "-" if owner["nearest_m"] is None else f"{owner['nearest_m']:.3f}"
            print(
                f"    {owner['owner']}: pairs={owner['pairs']} contacts={owner['contacts']} "
                f"triangles={owner['triangle_pairs']} nearest={gap}"
            )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
