# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Measure the cable runs and the air hardware, so routing can be decided on numbers [m].

Work 4 has to reroute two cable runs that cross their neighbours' and give each new cell its
own air set. Neither can be settled from geometry alone: a bend radius, a support pitch and a
separation are properties of the real cable and the real pipe, and this model carries none of
them. What the model does carry is what the existing runs already do, and that is worth
having before anyone proposes a number.

So this measures rather than decides. For every cable it walks a centre line through the
mesh, which gives the run its length, its thickness, the tightest radius it already turns,
and where its two ends sit and point. For every sampled point it reports the nearest solid
that is not the cable itself, which is the room a new route would have to work in. Where two
runs cross it reports the position along each, so a reroute knows which part of the run to
move. And it lists the air hardware v06 built for B, since the three new cells need the same
set and the spec describes it only in prose.

Points are scattered over the triangles first, then a ball marches through them. Marching the
vertices alone does not work on this geometry: the cable's straight floor section carries no
vertex between its two ends, a gap of 1.095 m, and no ball small enough to follow a 56 mm tube
can cross it. Against a tube built the same way the vertex march returned one point and no
length at all, and sampling the surface returns 1.905 m against a true 1.893 m, with the
section within half a percent.

Cables are chosen by size rather than by name. Their part happens to end in _p04, but that
suffix only means "the fifth part of an imported group" and matches 177 objects where fifteen
are cables.

It does not recover the bend radius, and that was measured rather than assumed. A perfectly
straight tube comes back as a 0.149 m bend, which is squarely inside the range a real bend
would occupy, and smoothing or widening the window raises the reading and the floor together.
So no bend radius is reported here at all. Quoting one would have been worse than quoting
nothing, because a number in a report gets used.

Names are never taken apart. Blender truncates at 63 characters and eleven S2L copies lost
their tails, so a copy's origin is read from ``split_source_name``.

Run: ``blender --background --python scripts/probe_op030_v07c_routing_survey.py``

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
from build_op030_split_v04 import _world_vertices  # noqa: E402
from build_op030_stagger_static_v06 import digest, geometry  # noqa: E402

SOURCE = ROOT / "analysis/op030_v07c_stagger_both_sides.blend"
SOURCE_SHA = "4e7c5b0d8b00b904c618dac757cf4c97c88de620898e7c7dcca0c3b0eb46ea51"
REPORT = ROOT / "audit/op030_v07c_routing_survey.json"

# A cable is chosen by its size, not by its name. Every station's cabinet-to-pedestal cable
# measures the same, and the first version picked objects whose name ended in _p04: that is
# only "the fifth part of an imported group" and caught 177 objects where 15 are cables.
CABLE_SIZE_M = (0.193, 0.538, 1.956)
CABLE_SIZE_TOLERANCE_M = 0.002
# The air hardware v06 built and moved for B, named in section 7.1 of the v07c spec.
AIR_PREFIXES = (
    "Split_bay_1__source_0779",
    "Split_bay_2__source_0779",
    "Split_bay_1__source_0780",
    "Split_bay_2__source_0780",
    "Split_bay_1__source_0782",
    "Split_bay_2__source_0782",
)
# Marching the centre line. The cable measures about 56 mm across, and these three were not
# guessed: they are what made the estimator agree with circles of known radius. A smaller ball
# makes the march collapse -- at 0.035 m it wandered 148 m along a 0.126 m arc.
BALL_M = 0.045
# The step was 0.012 and that inflated length. Each step carries a little lateral wander, and
# at 0.012 m there are enough of them to add 13% to a straight tube while a gentle arc came out
# right, so the error depended on the mesh rather than on the shape. At 0.030 m the same three
# test shapes land within 2.5% of each other: straight -1.9%, a slack loop -0.8%, an arc -2.3%.
STEP_M = 0.030
MAX_STEPS = 9000
# Points are scattered over the triangles at about this spacing before marching. Marching the
# vertices alone does not work here: the cable's straight floor section has no vertex between
# its ends, a gap of 1.095 m, and no ball small enough to follow the tube can cross it. On a
# tube built that way the vertex march produced one point and a length of 0.000 m.
SURFACE_SPACING_M = 0.006
SURFACE_SEED = 0
# Thickness is measured against this many of those points, which is plenty and keeps the
# distance matrix small.
THICKNESS_SAMPLES = 3000
# The march stops if it comes back this close to where it has already been, having walked at
# least this many steps since. A cable with a slack loop runs back alongside itself, the ball
# sees the outgoing tube as the way ahead, and the walk retraces it: ten of the fifteen runs
# came back as 5.648 m, exactly twice the 2.823 m the other five reported. The two legs of the
# slack loop itself stand further apart than this, so the loop survives and the hop does not.
FOLD_M = 0.060
# How far back along the walk to look for that return, as a distance rather than a step count,
# so it does not change meaning when the step does.
FOLD_LOOKBACK_M = 0.240
# Terminations are not clearance. A cable touches its own cabinet where it leaves and its own
# pedestal where it lands, and fourteen of fifteen runs reported one of those at 0.1 to 0.4 mm
# as their tightest point. The clearance that matters is the route between them, so this much
# is trimmed from each end before the tightest is taken.
TERMINAL_TRIM_M = 0.150
# Smoothing passes before measuring. The march jitters.
SMOOTHING_PASSES = 2
# What the centre line returned for the radius of circles of known radius, at these constants,
# including a straight tube whose true radius is infinite. A straight run reads 0.149 m, which
# sits inside the range a real bend would occupy, so the two cannot be told apart and no bend
# radius is reported. Widening the window only raises the floor with the reading.
LENGTH_CALIBRATION = {
    "straight 1.500, dense mesh": -0.013,
    "straight 1.500, coarse mesh": -0.010,
    "arc R=0.500, 0.785": -0.010,
    "slack loop 2.421": -0.002,
    "sparse tube 1.893, 1.095 m vertex gap, end curving away": -0.000,
    "note": "fractional error at the shipped constants, on tubes of 56 mm section",
}
CURVATURE_CALIBRATION = {
    "vertex_march": {"straight (infinite)": 0.149, "0.500": 0.494, "0.300": 0.296, "0.150": 0.150},
    "surface_sampled": {"straight (infinite)": 0.072, "0.300": 0.095, "0.150": 0.123},
    "verdict": (
        "not measurable by this method. A straight tube reads as a bend inside the range a real "
        "bend occupies, before and after the sampling fix, so no radius is reported"
    ),
}
# The implied diameter runs about a tenth low against a tube of known section, because the
# centre line wanders inside the true axis. Reported as approximate, not as a dimension.
DIAMETER_CALIBRATION = {
    "true_m": 0.056,
    "measured_m": 0.060,
    "note": "about 7% high at the 0.030 m step, which cuts corners; a size, not a dimension",
}
# Obstacles further than this from a run are not part of its routing problem.
NEIGHBOURHOOD_M = 0.500
# Report the run's clearance at no more than this many points, evenly spaced.
CLEARANCE_SAMPLES = 200
# Two runs count as crossing where their centre lines come within this of each other.
CROSSING_M = 0.100
# Where two runs meet, how much of the first stays within each of these of the second. One
# cable diameter is 0.056 m, so the last of them is "touching along their length".
CO_RUN_LIMITS_M = (0.003, 0.010, 0.056)
HALL_FOOTPRINT_M = 8.0


def source_name(obj: bpy.types.Object) -> str:
    """Return the name this object was copied from. Never parse the object's own name."""
    stamped = obj.get("split_source_name")
    return str(stamped) if stamped else obj.name


def surface_points(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Scatter points across the triangles so a long flat face is not a gap [m].

    Area-weighted, with the vertices kept as well. On a tube whose 1.5 m straight section has
    rings only at its two ends -- which is how the real cable is built -- marching the vertices
    found one point and no length, and this recovers 1.905 m against a true 1.893 m.
    """
    generator = np.random.default_rng(SURFACE_SEED)
    triangles = vertices[faces]
    first, second, third = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    area = 0.5 * np.linalg.norm(np.cross(second - first, third - first), axis=1)
    counts = np.maximum(1, np.ceil(area / (SURFACE_SPACING_M * SURFACE_SPACING_M)).astype(int))
    cloud = [vertices]
    for index, count in enumerate(counts):
        u, v = generator.random(count), generator.random(count)
        outside = u + v > 1.0
        u[outside], v[outside] = 1.0 - u[outside], 1.0 - v[outside]
        cloud.append(
            first[index] + np.outer(u, second[index] - first[index]) + np.outer(v, third[index] - first[index])
        )
    return np.vstack(cloud)


def is_cable(low: np.ndarray, high: np.ndarray) -> bool:
    """Return whether a box is one of the cabinet-to-pedestal cables [m]."""
    return bool(np.allclose(np.sort(high - low), np.sort(CABLE_SIZE_M), atol=CABLE_SIZE_TOLERANCE_M))


def box_of(obj: bpy.types.Object) -> tuple[np.ndarray, np.ndarray] | None:
    """Return an object's world box, or None when it has no usable volume [m]."""
    if obj.type not in {"MESH", "CURVE"}:
        return None
    vertices = getattr(obj.data, "vertices", None)
    if vertices is None or not len(vertices):
        return None
    world = _world_vertices(obj)
    low, high = world.min(0), world.max(0)
    if max(high[0] - low[0], high[1] - low[1]) > HALL_FOOTPRINT_M:
        return None
    return low, high


def centre_line(points: np.ndarray) -> np.ndarray:
    """March a centre line through a tube of points, from one end to the other [m].

    Each step looks at the points within a ball a little ahead and keeps only those in front
    of where it already stands, then moves to their centroid. Taking the whole ball instead
    averages in the tube behind and the march stalls: on a quarter circle of radius 0.500 m it
    crawled, reported 1.950 m of run against a true 0.785 m, and read the curve as 0.001 m.
    """
    spread = points - points.mean(0)
    axis = np.linalg.svd(spread, full_matrices=False)[2][0]
    start = points[np.argmin(spread @ axis)]
    ball = points[np.linalg.norm(points - start, axis=1) <= BALL_M]
    position = ball.mean(0) if len(ball) else start
    # Set off along the tube as it lies at this end, not along the cloud's principal axis. The
    # two need not agree: on a run that ends in a bend, the end points across the axis, and
    # stepping along the axis walks straight out of the tube. That is what returned a length of
    # zero on a tube whose far end curved away. The sign is the one with more of the tube ahead.
    local = ball - ball.mean(0) if len(ball) > 2 else spread
    direction = np.linalg.svd(local, full_matrices=False)[2][0]
    ahead_counts = [
        len(points[np.linalg.norm(points - (position + sign * direction * STEP_M), axis=1) <= BALL_M])
        for sign in (1.0, -1.0)
    ]
    direction = direction * (1.0 if ahead_counts[0] >= ahead_counts[1] else -1.0)
    line = [position]
    for _ in range(MAX_STEPS):
        ahead = position + direction * STEP_M
        ball = points[np.linalg.norm(points - ahead, axis=1) <= BALL_M]
        if len(ball) < 3:
            break
        forward = ball[(ball - position) @ direction > 0.5 * STEP_M]
        if len(forward) < 3:
            break
        centre = forward.mean(0)
        step = centre - position
        length = float(np.linalg.norm(step))
        if length < 1e-6:
            break
        # Look back over distance actually walked, not over a count of steps. A step is usually
        # shorter than its nominal size, so counting steps looked back less far than intended
        # and the guard fired on a straight tube, cutting it to nothing.
        travelled = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(np.asarray(line), axis=0), axis=1))])
        behind = np.asarray(line)[travelled <= travelled[-1] - FOLD_LOOKBACK_M]
        if len(behind) and np.min(np.linalg.norm(behind - centre, axis=1)) < FOLD_M:
            break
        direction = step / length
        position = centre
        line.append(position)
    return np.asarray(line)


def arc_lengths(line: np.ndarray) -> np.ndarray:
    """Return the distance along the polyline to each of its points [m]."""
    if len(line) < 2:
        return np.zeros(len(line))
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))])


def smooth_line(line: np.ndarray) -> np.ndarray:
    """Return the centre line with its marching jitter averaged out [m]."""
    out = line.copy()
    for _ in range(SMOOTHING_PASSES):
        if len(out) < 3:
            break
        out = np.vstack([out[:1], (out[:-2] + out[1:-1] + out[2:]) / 3.0, out[-1:]])
    return out


def run_length(line: np.ndarray) -> float:
    """Return the length of a polyline [m]. The steps are not all the nominal size.

    Taken from the same cumulative sum the arc lengths use, so a run does not read two ways in
    one report: summing the steps separately differed in the sixteenth digit.
    """
    return float(arc_lengths(line)[-1]) if len(line) >= 2 else 0.0


def thickness(points: np.ndarray, line: np.ndarray) -> dict:
    """Return how far the surface sits from the centre line [m]."""
    if not len(line):
        return dict(samples=0)
    distances = np.linalg.norm(points[:, None, :] - line[None, :, :], axis=2).min(axis=1)
    return dict(
        samples=int(len(points)),
        mean_radius_m=float(distances.mean()),
        max_radius_m=float(distances.max()),
        implied_diameter_m=float(2.0 * distances.mean()),
    )


def neighbourhood(obj: bpy.types.Object, low: np.ndarray, high: np.ndarray) -> list[tuple[str, BVHTree]]:
    """Return a BVH for every solid standing near this run, the run itself excluded."""
    trees = []
    for other in bpy.context.scene.objects:
        if other is obj:
            continue
        box = box_of(other)
        if box is None:
            continue
        if np.any(box[0] - high > NEIGHBOURHOOD_M) or np.any(low - box[1] > NEIGHBOURHOOD_M):
            continue
        vertices, faces = geometry(other)
        if not len(faces):
            continue
        trees.append(
            (
                other.name,
                BVHTree.FromPolygons(
                    [tuple(v) for v in vertices.tolist()], [tuple(f) for f in faces.tolist()], all_triangles=True
                ),
            )
        )
    return trees


def clearance_along(line: np.ndarray, trees: list[tuple[str, BVHTree]]) -> dict:
    """Return the nearest solid along the route, with the terminations trimmed off [m]."""
    if not len(line) or not trees:
        return dict(sampled=0, tightest_m=None)
    along = arc_lengths(line)
    interior = (along >= TERMINAL_TRIM_M) & (along <= along[-1] - TERMINAL_TRIM_M)
    line = line[interior] if interior.sum() >= 2 else line
    step = max(1, len(line) // CLEARANCE_SAMPLES)
    samples = []
    for index in range(0, len(line), step):
        point = line[index].tolist()
        best_name, best = None, None
        for name, tree in trees:
            _, _, _, distance = tree.find_nearest(point)
            if distance is not None and (best is None or distance < best):
                best_name, best = name, float(distance)
        if best is not None:
            samples.append(dict(index=index, at_m=line[index].tolist(), nearest=best_name, distance_m=best))
    tightest = min(samples, key=lambda row: row["distance_m"]) if samples else None
    return dict(
        sampled=len(samples),
        tightest=tightest,
        tightest_m=None if tightest is None else tightest["distance_m"],
    )


def segment_gap(
    first_start: np.ndarray, first_end: np.ndarray, second_start: np.ndarray, second_end: np.ndarray
) -> tuple[float, float, float]:
    """Return the gap between two segments and where along each it falls [m].

    Between segments, not between their end points. Sampled at 38 mm the closest approach of
    two runs usually falls between samples, and comparing points alone moved a crossing that
    is 0.020 m apart to 0.237 m on a coarse pair. This is exact for polylines whatever the
    step, which is what took the crossings from 0.0035 m to their real 0.0014 and 0.0104 m.
    """
    u, v, w = first_end - first_start, second_end - second_start, first_start - second_start
    a, b, c = float(u @ u), float(u @ v), float(v @ v)
    d, e = float(u @ w), float(v @ w)
    denominator = a * c - b * b
    if denominator > 1e-15:
        along_second = float(np.clip((a * e - b * d) / denominator, 0.0, 1.0))
    else:
        along_second = float(np.clip(e / c, 0.0, 1.0)) if c > 1e-15 else 0.0
    # A clamp on one segment moves the nearest point on the other, so settle each in turn.
    along_first = float(np.clip((b * along_second - d) / a, 0.0, 1.0)) if a > 1e-15 else 0.0
    along_second = float(np.clip((b * along_first + e) / c, 0.0, 1.0)) if c > 1e-15 else 0.0
    gap = float(np.linalg.norm((first_start + along_first * u) - (second_start + along_second * v)))
    return gap, along_first, along_second


def closest_approach(first: np.ndarray, second: np.ndarray) -> dict | None:
    """Return the closest approach of two centre lines, taken segment by segment [m]."""
    if len(first) < 2 or len(second) < 2:
        return None
    first_along, second_along = arc_lengths(first), arc_lengths(second)
    best = None
    for i in range(len(first) - 1):
        for j in range(len(second) - 1):
            gap, s, t = segment_gap(first[i], first[i + 1], second[j], second[j + 1])
            if best is None or gap < best["gap_m"]:
                point = first[i] + s * (first[i + 1] - first[i])
                best = dict(
                    gap_m=gap,
                    at_m=point.tolist(),
                    along_first_m=float(first_along[i] + s * (first_along[i + 1] - first_along[i])),
                    along_second_m=float(second_along[j] + t * (second_along[j + 1] - second_along[j])),
                    first_length_m=float(first_along[-1]),
                    second_length_m=float(second_along[-1]),
                )
    return best


def co_run(first: np.ndarray, second: np.ndarray, limits: tuple[float, ...]) -> list[dict]:
    """Return how much of the first run stays within each distance of the second [m].

    Two runs that meet at 53 micrometres are not crossing at a point. Measured in slabs the
    axes here stay inside a diameter of each other for about 0.75 m and inside 3 mm for about
    0.35 m, which is why the reported point of closest approach moved by 0.35 m when the
    measurement changed and the gap barely did. What work 4 has to separate is a length.
    """
    if len(first) < 2 or len(second) < 2:
        return []
    along = arc_lengths(first)
    gaps = np.array(
        [min(segment_gap(point, point, second[j], second[j + 1])[0] for j in range(len(second) - 1)) for point in first]
    )
    out = []
    for limit in limits:
        inside = gaps < limit
        if not inside.any():
            out.append(dict(within_m=limit, extent_m=0.0, from_m=None, to_m=None))
            continue
        covered = float(np.diff(along)[inside[:-1] | inside[1:]].sum())
        out.append(
            dict(
                within_m=limit,
                extent_m=covered,
                from_m=float(along[inside].min()),
                to_m=float(along[inside].max()),
                closest_m=float(gaps.min()),
            )
        )
    return out


def crossings(lines: dict[str, np.ndarray]) -> list[dict]:
    """Return where two runs come within the crossing distance of each other [m]."""
    found = []
    names = sorted(lines)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            best = closest_approach(lines[first], lines[second])
            if best is None or best["gap_m"] > CROSSING_M:
                continue
            found.append(
                dict(
                    runs=[first, second],
                    **best,
                    co_run=co_run(lines[first], lines[second], CO_RUN_LIMITS_M),
                )
            )
    return sorted(found, key=lambda row: row["gap_m"])


def transforms() -> dict[str, list]:
    """Return every object's world matrix so the read-only claim can be checked [m]."""
    return {o.name: np.asarray(o.matrix_world).tolist() for o in bpy.context.scene.objects}


def main() -> None:
    """Survey every cable run and the air hardware, and write what routing would need."""
    assert digest(SOURCE) == SOURCE_SHA, "Survey the six-cell candidate"
    assert not REPORT.exists(), "Preserve the existing survey"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    before = transforms()

    cables, lines, rejected = {}, {}, 0
    for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        box = box_of(obj)
        if box is None:
            continue
        if not is_cable(*box):
            rejected += 1
            continue
        vertices, faces = geometry(obj)
        points = surface_points(vertices, faces)
        line = smooth_line(centre_line(points))
        lines[obj.name] = line
        cables[obj.name] = dict(
            source=source_name(obj),
            box_m=[box[0].tolist(), box[1].tolist()],
            centre_line_points=len(line),
            run_length_m=run_length(line),
            ends=dict(
                start_m=line[0].tolist() if len(line) else None,
                end_m=line[-1].tolist() if len(line) else None,
                start_direction=(line[1] - line[0]).tolist() if len(line) > 1 else None,
                end_direction=(line[-1] - line[-2]).tolist() if len(line) > 1 else None,
            ),
            thickness=thickness(points[:: max(1, len(points) // THICKNESS_SAMPLES)], line),
            surface_points=len(points),
            clearance=clearance_along(line, neighbourhood(obj, *box)),
            terminal_trim_m=TERMINAL_TRIM_M,
            ends_separation_m=float(np.linalg.norm(line[-1] - line[0])) if len(line) > 1 else 0.0,
        )

    air = {}
    for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        if not obj.name.startswith(AIR_PREFIXES):
            continue
        box = box_of(obj)
        if box is None:
            continue
        air[obj.name] = dict(
            source=source_name(obj),
            size_m=(box[1] - box[0]).tolist(),
            box_m=[box[0].tolist(), box[1].tolist()],
            parent=obj.parent.name if obj.parent else None,
        )

    after = transforms()
    unchanged = after == before
    REPORT.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source=str(SOURCE.relative_to(ROOT)),
                source_sha256=SOURCE_SHA,
                method=dict(
                    centre_line="march a ball along the tube and step to its centroid",
                    surface_spacing_m=SURFACE_SPACING_M,
                    ball_m=BALL_M,
                    fold_m=FOLD_M,
                    terminal_trim_m=TERMINAL_TRIM_M,
                    step_m=STEP_M,
                    smoothing_passes=SMOOTHING_PASSES,
                    length_calibration_fraction=LENGTH_CALIBRATION,
                    curvature_calibration_m=CURVATURE_CALIBRATION,
                    diameter_calibration_m=DIAMETER_CALIBRATION,
                    neighbourhood_m=NEIGHBOURHOOD_M,
                    crossing_m=CROSSING_M,
                    crossing_measured="segment to segment, so the gap does not depend on the step",
                    co_run_limits_m=list(CO_RUN_LIMITS_M),
                ),
                what_this_does_not_give=[
                    "the cable's allowed bend radius, which belongs to the real cable",
                    "the bend radius the model already uses: measured and found not measurable",
                    "clearance at the terminations, which is contact by design and is trimmed away",
                    "support pitch and fixing points",
                    "required separation from other services",
                    "the pipe inside the air hardware's boxes",
                ],
                cable_count=len(cables),
                objects_measured_and_rejected=rejected,
                cable_rule=f"box sorted to {CABLE_SIZE_M} within {CABLE_SIZE_TOLERANCE_M} m",
                cables=cables,
                crossings=crossings(lines),
                air_hardware_count=len(air),
                air_hardware=air,
                scene_world_transforms_unchanged=unchanged,
                saved_scene=False,
                scope="Read-only survey of cable runs and air hardware on the six-cell candidate",
                formal_physical_validity_verdict=None,
            ),
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    assert unchanged, "The survey must not move anything"
    for name, row in cables.items():
        clear = row["clearance"]["tightest_m"]
        print(
            f"  {name[:56]:56s} length {row['run_length_m']:.2f} m  "
            f"dia ~{row['thickness'].get('implied_diameter_m', 0):.3f} m  "
            f"clearance {'-' if clear is None else f'{clear:.3f}'} m"
        )
    for row in crossings(lines):
        print(
            f"  crossing {row['gap_m']:.3f} m: {row['runs'][0][:34]} at {row['along_first_m']:.2f} m "
            f"x {row['runs'][1][:34]} at {row['along_second_m']:.2f} m"
        )
    print(f"air hardware: {len(air)} objects")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
