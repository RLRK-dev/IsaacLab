# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Measure a cable's run length from its mesh alone, so the survey's march has something to
check against [m].

The survey walks a ball through the tube and reports 2.8008 m. A length taken from the mesh
was quoted at 2.8027 m and lived only in a message, so the two could not be compared from a
checkout. This puts the mesh side on disk.

Three lengths are taken here and none of them marches:

* Pappus. For a tube swept along a path, the volume is the section area times the path length
  and the outer area is the section perimeter times the same length, both exactly, so the two
  together give the length and the section without assuming either. The section is a sixteen
  sided polygon, which is checked below rather than assumed, and the ends are flat caps.
* The ring centroids. The mesh is rings of sixteen vertices, and the centre of each ring sits
  on the axis. The polyline through them is the axis, sampled every 60 mm, and its length is a
  slight underestimate by the chord of each bend.
* The survey's own figure, copied from its report for comparison.

Whether the vertices really fall into rings of sixteen in index order is tested, not assumed:
every group must be flat to within a tenth of a millimetre and round to within a hundredth.

Run: ``blender --background --python scripts/measure_op030_v07c_cable_mesh.py``

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

SOURCE = ROOT / "analysis/op030_v07c_stagger_both_sides.blend"
SOURCE_SHA = "4e7c5b0d8b00b904c618dac757cf4c97c88de620898e7c7dcca0c3b0eb46ea51"
SURVEY = ROOT / "audit/op030_v07c_routing_survey.json"
REPORT = ROOT / "audit/op030_v07c_cable_mesh_check.json"

# The two cables the survey reports crossing, and one that crosses nothing, so the check covers
# a copy and an original and is not read as being about the crossings.
SUBJECTS = (
    "source_0693_m0120_p04",
    "OP030_S1R__source_0693_m0120_p04",
    "OP030_S3R__OP030C__source_0693_m0120_p04",
    "source_0681_m0108_p04",
    "source_0705_m0132_p04",
)
RING_VERTICES = 16
FLATNESS_M = 1e-4
ROUNDNESS_M = 1e-2


def area_and_volume(vertices: np.ndarray, faces: np.ndarray) -> tuple[float, float]:
    """Return the mesh's outer area [m^2] and the volume it encloses [m^3]."""
    a, b, c = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    area = float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())
    volume = float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0))
    return area, volume


def boundary_edges(vertices: np.ndarray, faces: np.ndarray) -> int:
    """Return how many edges belong to one face only. A closed mesh has none."""
    _, index = np.unique(np.round(vertices, 6), axis=0, return_inverse=True)
    used: dict[tuple[int, int], int] = {}
    for triangle in index[faces]:
        for first, second in ((0, 1), (1, 2), (2, 0)):
            key = (min(triangle[first], triangle[second]), max(triangle[first], triangle[second]))
            used[key] = used.get(key, 0) + 1
    return sum(1 for count in used.values() if count == 1)


def solve_pappus(area: float, volume: float, sides: int) -> tuple[float, float]:
    """Return the section's circumradius [m] and the path length [m] for a capped tube."""

    def section(radius: float) -> float:
        return (sides / 2) * radius**2 * float(np.sin(2 * np.pi / sides))

    def perimeter(radius: float) -> float:
        return 2 * sides * radius * float(np.sin(np.pi / sides))

    def residual(radius: float) -> float:
        return perimeter(radius) * volume / section(radius) + 2 * section(radius) - area

    # The wall term falls with the radius and the cap term rises, so the residual is positive at
    # both ends and the tube's own root is the first sign change. Scan for it rather than guess a
    # bracket: a wrong bracket would find the second root, which is a tube as short as it is thick.
    grid = np.geomspace(1e-4, 1.0, 400)
    signs = [residual(float(r)) for r in grid]
    crossings = [i for i in range(len(grid) - 1) if signs[i] > 0 >= signs[i + 1]]
    assert crossings, "the tube's area and volume do not bracket a section"
    low, high = float(grid[crossings[0]]), float(grid[crossings[0] + 1])
    for _ in range(200):
        middle = 0.5 * (low + high)
        low, high = (middle, high) if residual(middle) > 0 else (low, middle)
    radius = 0.5 * (low + high)
    return float(radius), float(volume / section(radius))


def rings(vertices: np.ndarray) -> dict:
    """Return the ring centroids and the evidence that the grouping is real, not assumed."""
    count = (len(vertices) - 2) // RING_VERTICES
    if count * RING_VERTICES + 2 != len(vertices):
        return dict(found=False, why=f"{len(vertices)} vertices is not {RING_VERTICES} per ring plus two caps")
    groups = vertices[:-2].reshape(count, RING_VERTICES, 3)
    flatness, roundness, centres = [], [], []
    for group in groups:
        centre = group.mean(0)
        normal = np.linalg.svd(group - centre, full_matrices=False)[2][2]
        flatness.append(float(np.abs((group - centre) @ normal).max()))
        radii = np.linalg.norm(group - centre, axis=1)
        roundness.append(float(radii.max() - radii.min()))
        centres.append(centre)
    centres = np.asarray(centres)
    steps = np.linalg.norm(np.diff(centres, axis=0), axis=1)
    return dict(
        found=bool(max(flatness) < FLATNESS_M and max(roundness) < ROUNDNESS_M),
        ring_count=int(count),
        vertices_per_ring=RING_VERTICES,
        worst_flatness_m=float(max(flatness)),
        worst_roundness_m=float(max(roundness)),
        mean_radius_m=float(np.linalg.norm(groups - groups.mean(1)[:, None, :], axis=2).mean()),
        spacing_m=dict(min=float(steps.min()), mean=float(steps.mean()), max=float(steps.max())),
        length_m=float(steps.sum()),
    )


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Measure each subject three ways and write what the survey's march can be judged against."""
    assert digest(SOURCE) == SOURCE_SHA, "Measure the six-cell candidate"
    assert not REPORT.exists(), "Preserve the existing measurement"
    survey = json.loads(SURVEY.read_text())
    assert survey["source_sha256"] == SOURCE_SHA, "The survey is of a different scene"

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cables = {}
    for name in SUBJECTS:
        obj = bpy.data.objects[name]
        vertices, faces = geometry(obj)
        area, volume = area_and_volume(vertices, faces)
        edges = boundary_edges(vertices, faces)
        radius, length = solve_pappus(area, volume, RING_VERTICES)
        ring = rings(vertices)
        marched = survey["cables"][name]["run_length_m"]
        cables[name] = dict(
            closed=edges == 0,
            boundary_edges=edges,
            vertex_count=int(len(vertices)),
            triangle_count=int(len(faces)),
            area_m2=area,
            volume_m3=volume,
            section_sides=RING_VERTICES,
            section_circumradius_m=radius,
            section_across_corners_m=2.0 * radius,
            section_across_flats_m=float(2.0 * radius * np.cos(np.pi / RING_VERTICES)),
            length_from_area_and_volume_m=length,
            rings=ring,
            length_from_ring_centres_m=ring.get("length_m"),
            survey_run_length_m=marched,
            survey_centre_line_points=survey["cables"][name]["centre_line_points"],
            survey_minus_pappus_fraction=float(marched / length - 1.0),
            survey_minus_rings_fraction=None if not ring.get("length_m") else float(marched / ring["length_m"] - 1.0),
        )

    after = transforms()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                scope="Cable run length taken from the mesh, to be compared with the survey's march",
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                survey=str(SURVEY.relative_to(ROOT)),
                survey_sha256=digest(SURVEY),
                survey_observed_at=survey["observed_at"],
                method=dict(
                    pappus=(
                        "volume = section area x path length and outer area = section perimeter x path length,"
                        " both exact for a swept section, solved together with two flat caps"
                    ),
                    ring_centres="the centroid of each ring of vertices lies on the axis; the polyline through them",
                    ring_grouping=(
                        f"vertices taken {RING_VERTICES} at a time in index order, then tested: each group flat to"
                        f" {FLATNESS_M} m and round to {ROUNDNESS_M} m, or the grouping is reported as not found"
                    ),
                    section_sides=RING_VERTICES,
                ),
                what_this_does_not_give=[
                    "which length the cable would have if it were laid straight",
                    "the section of the real cable, this being the model's",
                    "a bend radius: the ring spacing is 60 mm and says nothing finer",
                    "any judgement of whether the run is physically sound",
                ],
                cables=cables,
                scene_world_transforms_unchanged=before == after,
                saved_scene=False,
                formal_physical_validity_verdict=None,
            ),
            indent=1,
        )
        + "\n"
    )
    for name, row in cables.items():
        print(
            f"  {name:52s} closed {row['closed']}  area {row['area_m2']:.5f}  volume {row['volume_m3']:.6f}"
            f"  pappus {row['length_from_area_and_volume_m']:.4f}  rings {row['length_from_ring_centres_m']:.4f}"
            f"  survey {row['survey_run_length_m']:.4f}"
        )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
