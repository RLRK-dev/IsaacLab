# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Measure the two crossings from the meshes, without the survey's centre line [m].

The survey walks a ball along each tube and reports where two runs come closest. This takes
the same distance a second way: around the point the survey reports, the surface of each cable
is sampled, a straight axis is fitted to the points inside a window by their principal
direction, and the distance between those two axes is measured. Nothing here marches, and
nothing here reads the survey except the place to look and the figure to print beside.

Three windows are used rather than one. The fitted axis is straight and the cable is not, so a
longer window buys points at the cost of bending the thing being fitted, and the spread across
the three is the honest width of the answer. The angle between the two axes is reported with
it, because it says how sharply the answer falls away from the crossing: at a degree or two
the two runs lie along each other and a single position means little.

Vertices are not used. This cable carries none over a whole metre of its straight floor
section, so points are scattered over the triangles first.

Run: ``blender --background --python scripts/measure_op030_v07c_crossing_local_axis.py``

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
REPORT = ROOT / "audit/op030_v07c_crossing_local_axis.json"

# Points are scattered over the triangles at about this spacing, which puts a thousand or more
# of them in the smallest window.
SURFACE_SPACING_M = 0.004
SURFACE_SEED = 0
# The same measurement is repeated with these seeds as well. Where two axes all but coincide,
# their distance is a small difference of two fitted lines and it moves with the draw: quoting
# it to three figures would be quoting the random number generator, so the spread is reported.
SEEDS = (0, 1, 2, 3, 4)
# The windows the axis is fitted in, measured from the point the survey reports.
WINDOWS_M = (0.060, 0.100, 0.150)
MIN_POINTS = 100


def scatter(vertices: np.ndarray, faces: np.ndarray, seed: int = SURFACE_SEED) -> np.ndarray:
    """Return points spread over the triangles at about SURFACE_SPACING_M, area weighted."""
    a, b, c = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    areas = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    counts = np.maximum(1, np.round(areas / SURFACE_SPACING_M**2).astype(int))
    rng = np.random.default_rng(seed)
    index = np.repeat(np.arange(len(faces)), counts)
    first = rng.random((len(index), 1))
    second = rng.random((len(index), 1))
    outside = (first + second) > 1.0
    first[outside], second[outside] = 1.0 - first[outside], 1.0 - second[outside]
    return a[index] + first * (b[index] - a[index]) + second * (c[index] - a[index])


def principal_axis(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return a point on the fitted axis and its unit direction."""
    centre = points.mean(0)
    direction = np.linalg.svd(points - centre, full_matrices=False)[2][0]
    return centre, direction / np.linalg.norm(direction)


def axis_distance(first_point, first_direction, second_point, second_direction) -> float:
    """Return the distance between two straight axes [m], parallel ones included."""
    normal = np.cross(first_direction, second_direction)
    length = float(np.linalg.norm(normal))
    if length < 1e-9:
        return float(np.linalg.norm(np.cross(second_point - first_point, first_direction)))
    return float(abs((second_point - first_point) @ normal) / length)


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Measure each crossing the survey reports a second way, and write both figures down."""
    assert digest(SOURCE) == SOURCE_SHA, "Measure the six-cell candidate"
    assert not REPORT.exists(), "Preserve the existing measurement"
    survey = json.loads(SURVEY.read_text())
    assert survey["source_sha256"] == SOURCE_SHA, "The survey is of a different scene"

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    clouds: dict[str, np.ndarray] = {}
    crossings = []
    for row in survey["crossings"]:
        first, second = row["runs"]
        at = np.asarray(row["at_m"])
        for name in (first, second):
            if name not in clouds:
                clouds[name] = scatter(*geometry(bpy.data.objects[name]))
        windows = []
        for window in WINDOWS_M:
            fitted = {}
            for name in (first, second):
                near = clouds[name][np.linalg.norm(clouds[name] - at, axis=1) <= window]
                if len(near) < MIN_POINTS:
                    fitted[name] = None
                    continue
                centre, direction = principal_axis(near)
                fitted[name] = dict(points=int(len(near)), centre=centre, direction=direction)
            if any(value is None for value in fitted.values()):
                windows.append(dict(window_m=window, measured=False, why="too few surface points"))
                continue
            gap = axis_distance(
                fitted[first]["centre"],
                fitted[first]["direction"],
                fitted[second]["centre"],
                fitted[second]["direction"],
            )
            angle = float(
                np.degrees(np.arccos(min(1.0, abs(float(fitted[first]["direction"] @ fitted[second]["direction"])))))
            )
            windows.append(
                dict(
                    window_m=window,
                    measured=True,
                    axis_gap_m=gap,
                    angle_between_axes_deg=angle,
                    centre_separation_m=float(np.linalg.norm(fitted[first]["centre"] - fitted[second]["centre"])),
                    points={name: fitted[name]["points"] for name in (first, second)},
                    axes={
                        name: dict(
                            through_m=fitted[name]["centre"].tolist(), direction=fitted[name]["direction"].tolist()
                        )
                        for name in (first, second)
                    },
                )
            )
        # Repeat the whole fit on fresh draws, so the report carries how much the draw is worth.
        by_seed = {}
        for seed in SEEDS:
            drawn = {name: scatter(*geometry(bpy.data.objects[name]), seed=seed) for name in (first, second)}
            per_window = []
            for window in WINDOWS_M:
                axes = []
                for name in (first, second):
                    near = drawn[name][np.linalg.norm(drawn[name] - at, axis=1) <= window]
                    axes.append(None if len(near) < MIN_POINTS else principal_axis(near))
                if any(axis is None for axis in axes):
                    continue
                per_window.append(axis_distance(axes[0][0], axes[0][1], axes[1][0], axes[1][1]))
            by_seed[str(seed)] = per_window
        spread = [gap for gaps in by_seed.values() for gap in gaps]

        measured = [w["axis_gap_m"] for w in windows if w.get("measured")]
        crossings.append(
            dict(
                runs=[first, second],
                at_m=row["at_m"],
                survey_gap_m=row["gap_m"],
                survey_along_first_m=row["along_first_m"],
                survey_along_second_m=row["along_second_m"],
                axis_gap_range_m=[min(measured), max(measured)] if measured else None,
                angle_range_deg=[
                    min(w["angle_between_axes_deg"] for w in windows if w.get("measured")),
                    max(w["angle_between_axes_deg"] for w in windows if w.get("measured")),
                ]
                if measured
                else None,
                windows=windows,
                over_seeds=dict(
                    seeds=list(SEEDS),
                    axis_gap_by_seed_m=by_seed,
                    axis_gap_range_m=[min(spread), max(spread)] if spread else None,
                    note="one method, five draws and three windows; the digits belong to the draw",
                ),
            )
        )

    after = transforms()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                scope="The survey's crossings measured again from the meshes, without its centre line",
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                survey=str(SURVEY.relative_to(ROOT)),
                survey_sha256=digest(SURVEY),
                survey_observed_at=survey["observed_at"],
                method=dict(
                    surface_spacing_m=SURFACE_SPACING_M,
                    surface_seed=SURFACE_SEED,
                    windows_m=list(WINDOWS_M),
                    axis="the principal direction of the surface points inside the window",
                    gap="the distance between the two fitted straight axes",
                    why_three_windows="the fit is straight and the cable is not, so the spread is the answer's width",
                    minimum_points=MIN_POINTS,
                    seeds=list(SEEDS),
                ),
                what_this_does_not_give=[
                    "where along either run the closest approach falls: the axis fitted here is straight",
                    "how far the two runs stay together, which the survey's co_run measures",
                    "a surface to surface distance: at these gaps the two tubes overlap",
                    "this distance to three figures: it moves with the draw, so the range is the answer",
                    "any judgement of whether the crossing is acceptable",
                ],
                crossings=crossings,
                scene_world_transforms_unchanged=before == after,
                saved_scene=False,
                formal_physical_validity_verdict=None,
            ),
            indent=1,
        )
        + "\n"
    )
    for row in crossings:
        low, high = row["axis_gap_range_m"]
        wide = row["over_seeds"]["axis_gap_range_m"]
        print(
            f"  {row['runs'][0][:38]:38s} x {row['runs'][1][:26]:26s}"
            f"  axes {low * 1000:.3f}-{high * 1000:.3f} mm at seed {SURFACE_SEED}"
            f", {wide[0] * 1000:.3f}-{wide[1] * 1000:.3f} mm over {len(SEEDS)} draws"
            f"  survey {row['survey_gap_m'] * 1000:.3f} mm"
            f"  angle {row['angle_range_deg'][0]:.2f}-{row['angle_range_deg'][1]:.2f} deg"
        )
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
