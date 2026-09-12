# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Settle by ray whether the pairs whose boxes nest are really one inside the other.

Triangle overlap finds surfaces that cross. It cannot find a part that sits wholly inside
another, because then no triangle of either meets a triangle of the other, and 226 pairs in
the contact report have one box inside the other with no triangle crossing. Those are the ones
this settles.

A point is inside a closed mesh when a ray from it crosses the surface an odd number of times.
The count is taken by Moller-Trumbore against every triangle at once, so there is no marching
and no tolerance to tune, and it is repeated along several directions because a ray that grazes
an edge can be counted twice or not at all. The directions are fixed, not drawn, so the answer
is the same on every run; where they disagree the pair is reported as not unanimous.

The moving side is mirrored first, the same M(y0) the build applies, and the mirrored box is
compared against the one the contact report recorded, so a wrong mirror shows up as a number
rather than as a wrong verdict.

Two points are tested per pair: the centroid of the moving part, and one of its vertices, since
a centroid can fall outside a part that is concave. Whether the centroid is inside its own part
is reported for the same reason.

Run: ``blender --background --python scripts/check_op030_v07c_containment_rays.py``

Read-only. The scene is never saved and world matrices are compared before and after.
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
from build_op030_stagger_static_v06 import digest, geometry  # noqa: E402

CONTACT = ROOT / "audit/op030_v07c_mesh_contact.json"
REPORT = ROOT / "audit/op030_v07c_containment_rays.json"

# Fixed directions, so the answer does not move between runs. Seven of them, none along an axis
# and none parallel to another, which is what keeps a grazed edge from deciding a pair.
DIRECTIONS = np.array(
    [
        [0.5773502691896258, 0.5773502691896258, 0.5773502691896258],
        [-0.4364357804719848, 0.8728715609439696, 0.21821789023599236],
        [0.3015113445777636, -0.9045340337332909, 0.30151134457776363],
        [-0.6963106238227914, -0.5222329678670935, 0.4924345450507478],
        [0.8017837257372732, 0.2672612419124244, -0.5345224838248488],
        [-0.1690308509457033, 0.5070925528371099, -0.8451542547285166],
        [0.4082482904638631, -0.4082482904638631, -0.8164965809277261],
    ]
)
EPSILON = 1e-12


def mirror(y0: float) -> np.ndarray:
    """Return M(y0): (x, y, z) -> (-x, 2 y0 - y, z), as a 4x4 [m]."""
    matrix = np.eye(4)
    matrix[0, 0] = -1.0
    matrix[1, 1] = -1.0
    matrix[1, 3] = 2.0 * y0
    return matrix


def crossings(origin: np.ndarray, direction: np.ndarray, triangles: np.ndarray) -> int:
    """Return how many triangles the ray crosses, by Moller-Trumbore, all at once."""
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    first, second = b - a, c - a
    pivot = np.cross(direction, second)
    determinant = np.einsum("ij,ij->i", first, pivot)
    alive = np.abs(determinant) > EPSILON
    inverse = np.zeros_like(determinant)
    inverse[alive] = 1.0 / determinant[alive]
    offset = origin - a
    u = np.einsum("ij,ij->i", offset, pivot) * inverse
    alive &= (u >= 0.0) & (u <= 1.0)
    across = np.cross(offset, first)
    v = (across @ direction) * inverse
    alive &= (v >= 0.0) & (u + v <= 1.0)
    distance = np.einsum("ij,ij->i", second, across) * inverse
    return int(np.count_nonzero(alive & (distance > EPSILON)))


def parity_votes(point: np.ndarray, triangles: np.ndarray) -> tuple[int, int]:
    """Return how many directions say the point is inside, out of how many tried."""
    return sum(crossings(point, d, triangles) % 2 == 1 for d in DIRECTIONS), len(DIRECTIONS)


def triangles_of(obj: bpy.types.Object, transform: np.ndarray | None = None) -> np.ndarray:
    """Return the object's triangles in world space, optionally moved first [m]."""
    vertices, faces = geometry(obj)
    if transform is not None:
        vertices = vertices @ transform[:3, :3].T + transform[:3, 3]
    return vertices[faces]


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Test every nested pair by ray and write whether any part is really inside another."""
    assert not REPORT.exists(), "Preserve the existing check"
    contact = json.loads(CONTACT.read_text())
    source = ROOT / contact["source"]
    assert digest(source) == contact["source_sha256"], "The contact report is of a different scene"

    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.scene.frame_set(1)
    before = transforms()

    obstacles: dict[str, np.ndarray] = {}
    cells, worst_box_error = {}, 0.0
    for name, cell in contact["cells"].items():
        transform = mirror(cell["station_y_m"])
        pairs = []
        for row in cell["contained"]:
            if not row.get("one_box_inside_the_other"):
                continue
            moving = triangles_of(bpy.data.objects[row["moving"]], transform)
            if row["obstacle"] not in obstacles:
                obstacles[row["obstacle"]] = triangles_of(bpy.data.objects[row["obstacle"]])
            obstacle = obstacles[row["obstacle"]]

            points = moving.reshape(-1, 3)
            low, high = points.min(0), points.max(0)
            recorded = np.asarray(row["moving_box_m"])
            box_error = float(np.abs(np.vstack([low, high]) - recorded).max())
            worst_box_error = max(worst_box_error, box_error)

            centroid = points.mean(0)
            vertex = points[0]
            centroid_votes, tried = parity_votes(centroid, obstacle)
            vertex_votes, _ = parity_votes(vertex, obstacle)
            own_votes, _ = parity_votes(centroid, moving)
            pairs.append(
                dict(
                    moving=row["moving"],
                    obstacle=row["obstacle"],
                    owner=row["owner"],
                    inside_by_parity=bool(centroid_votes * 2 > tried),
                    directions_tested=tried,
                    inside_votes=int(centroid_votes),
                    unanimous=bool(centroid_votes in (0, tried)),
                    from_vertex=dict(
                        inside_by_parity=bool(vertex_votes * 2 > tried),
                        inside_votes=int(vertex_votes),
                        unanimous=bool(vertex_votes in (0, tried)),
                        at_m=vertex.tolist(),
                    ),
                    centroid_inside_its_own_part=bool(own_votes * 2 > tried),
                    centroid_own_votes=int(own_votes),
                    centroid_m=centroid.tolist(),
                    nearest_m=row.get("nearest_m"),
                    mirrored_box_matches_report_m=box_error,
                )
            )
        inside = [row for row in pairs if row["inside_by_parity"] or row["from_vertex"]["inside_by_parity"]]
        cells[name] = dict(
            destination=cell["destination"],
            station_y_m=cell["station_y_m"],
            mirror_rule=f"M({cell['station_y_m']}): (x, y) -> (-x, {2 * cell['station_y_m']:.3f} - y)",
            tested=len(pairs),
            inside_by_parity=len(inside),
            not_unanimous=sum(1 for row in pairs if not row["unanimous"]),
            centroid_outside_its_own_part=sum(1 for row in pairs if not row["centroid_inside_its_own_part"]),
            nearest_m=dict(
                min=min((row["nearest_m"] for row in pairs if row["nearest_m"] is not None), default=None),
                max=max((row["nearest_m"] for row in pairs if row["nearest_m"] is not None), default=None),
            ),
            pairs=pairs,
        )
        print(
            f"  cell {name} ({cell['destination']}): {len(pairs)} tested, inside {len(inside)},"
            f" split votes {cells[name]['not_unanimous']},"
            f" centroid outside its own part {cells[name]['centroid_outside_its_own_part']}"
        )

    after = transforms()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                scope="Whether the pairs whose boxes nest are one part inside another, settled by ray",
                source=contact["source"],
                source_sha256=contact["source_sha256"],
                read_from=dict(
                    contact=str(CONTACT.relative_to(ROOT)),
                    contact_sha256=digest(CONTACT),
                    contact_observed_at=contact["observed_at"],
                ),
                method=dict(
                    test="odd crossings of the obstacle's surface means inside",
                    intersection="Moller-Trumbore against every triangle at once",
                    directions=DIRECTIONS.tolist(),
                    directions_fixed="the same every run, so the answer does not move; disagreement is reported",
                    points="the centroid of the mirrored part, and one of its vertices",
                    mirror="the build's own M(y0), checked against the box the contact report recorded",
                    worst_mirrored_box_difference_m=worst_box_error,
                ),
                what_this_does_not_give=[
                    "whether the parts that are not inside each other are far enough apart",
                    "contact between surfaces, which the triangle stage already reports",
                    "anything about pairs whose boxes do not nest",
                    "any judgement of whether the layout is sound",
                ],
                total_tested=sum(row["tested"] for row in cells.values()),
                total_inside_by_parity=sum(row["inside_by_parity"] for row in cells.values()),
                cells=cells,
                scene_world_transforms_unchanged=before == after,
                saved_scene=False,
                formal_physical_validity_verdict=None,
            ),
            indent=1,
        )
        + "\n"
    )
    print(f"  worst mirrored box difference against the contact report: {worst_box_error:.3e} m")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
