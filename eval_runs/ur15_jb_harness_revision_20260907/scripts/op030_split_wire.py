# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Straight supply and fixed-length two-ended bending geometry [m, rad].

This module reuses the OP030 final centerlines, lug coordinate systems and
unscaled manufacturer tessellations. The old endpoint/correction basis cannot
reliably unfold the U route all the way to a straight wire. Here each existing
polyline segment retains its own length while its unwrapped heading and pitch
are varied. This is an authored geometric path, not a rod/contact simulation.
"""

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from op030_definition import ROOT, WIRE_RADIUS, lug_frame, pose, wire_route
from op030_split_top_entry import ConnectionMode, j1_lug_frame, j1_lug_mesh, j1_lug_part, top_entry_spec


def _smooth(value: float) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError("progress must be between zero and one")
    return value**3 * (10.0 - 15.0 * value + 6.0 * value**2)


def _rz(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)))


def _transform(points: np.ndarray, frame: np.ndarray) -> np.ndarray:
    return points @ frame[:3, :3].T + frame[:3, 3]


def _tangent_frame(tangent: np.ndarray) -> np.ndarray:
    x = tangent / np.linalg.norm(tangent)
    y = np.cross((0.0, 0.0, 1.0), x)
    y /= np.linalg.norm(y)
    return np.column_stack((x, y, np.cross(x, y)))


def lug_mesh(part: str) -> tuple[np.ndarray, list[list[int]]]:
    """Return unchanged manufacturer lug geometry in existing OP030 axes [m].

    Args:
        part: Existing reference part, ``46R6``, ``6R6`` or ``6R14``.

    Returns:
        Vertices [m] and the original polygon index lists.
    """
    if part == "6R6":
        return j1_lug_mesh("top_entry")
    data = json.loads((ROOT / "inputs/op030_reference" / f"Klauke_{part}.json").read_text())
    v = np.asarray(data["vertices"], dtype=float)
    if part == "6R14":
        vertices = np.column_stack((v[:, 0] + 45, -v[:, 2], v[:, 1] + 8)) / 1000
    elif part == "46R6":
        vertices = np.column_stack((-v[:, 2], -v[:, 0], v[:, 1] + 1.9)) / 1000
    else:
        raise ValueError(part)
    return vertices, data["faces"]


def wire_route_top_entry(number: int) -> np.ndarray:
    """Retain the route's bends and T end, with the adopted J1 inlet [m].

    The first straight section is shortened by the measured 20 mm J1 inset.
    The retained height law is evaluated over the new planar arclength. The
    resulting visible insulation length defines both stock and installed
    geometry; it is not a released conductor cutting or crimp specification.
    """
    points = wire_route(number)
    spec = top_entry_spec()
    start = _transform(np.asarray(spec["lug_entrance_local_m"])[None], j1_lug_frame(number, "top_entry"))[0]
    count = 49 if number == 1 else 33
    if not start[0] < points[count - 1, 0]:
        raise ValueError("The J1 inlet must precede the retained first bend")
    if not np.isclose(start[1], points[0, 1]):
        raise ValueError("The retained route requires the original J1 lateral coordinate")
    points[:count, 0] = np.linspace(start[0], points[count - 1, 0], count)
    arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points[:, :2], axis=0), axis=1))]
    u = arc / arc[-1]
    end_z = points[-1, 2]
    if number == 1:
        rise = np.clip(u / 0.40, 0, 1)
        fall = np.clip((u - 0.75) / 0.25, 0, 1)
        rise = rise**3 * (10 - 15 * rise + 6 * rise**2)
        fall = fall**3 * (10 - 15 * fall + 6 * fall**2)
        points[:, 2] = start[2] + (0.050 - start[2]) * rise + (end_z - 0.050) * fall
    else:
        w = u**3 * (10 - 15 * u + 6 * u**2)
        points[:, 2] = start[2] * (1 - w) + end_z * w
        points[:, 2] += (0.030 - (start[2] + end_z) / 2) * np.sin(np.pi * u) ** 2
    return points


@dataclass(frozen=True)
class WireShape:
    """One geometric state; coordinates [m] and rigid transforms [m]."""

    centerline: np.ndarray
    lug_frames: dict[str, np.ndarray]
    grasp_frames: dict[str, np.ndarray]
    progress: float


class WireBend:
    """Interpolate an existing wire from straight to its final route [m].

    Args:
        number: Existing H03 wire number, one or two.
        grasp_offset: Arclength from each insulation endpoint [m]. This is a
            geometric contact-point candidate, not a validated grasp design.
        connection_mode: Retained rear entry or the separate top-entry prototype.
    """

    def __init__(self, number: int, grasp_offset: float = 0.030, *, connection_mode: ConnectionMode = "rear_entry"):
        if number not in (1, 2):
            raise ValueError("Only H03-1 and H03-2 have reference geometry")
        self.number = number
        self.connection_mode = connection_mode
        self.final_points = wire_route_top_entry(number) if connection_mode == "top_entry" else wire_route(number)
        segments = np.diff(self.final_points, axis=0)
        self.lengths = np.linalg.norm(segments, axis=1)
        self.arc = np.r_[0.0, np.cumsum(self.lengths)]
        self.length = float(self.arc[-1])
        if not 0.0 < grasp_offset < self.length / 2:
            raise ValueError("grasp_offset must lie between an end and the midpoint")
        self.grasp_offset = grasp_offset
        self.heading = np.unwrap(np.arctan2(segments[:, 1], segments[:, 0]))
        self.pitch = np.arctan2(segments[:, 2], np.linalg.norm(segments[:, :2], axis=1))
        self.final_center = (self.final_points[0] + self.final_points[-1]) / 2
        self.final_frames = {end: lug_frame(number, end) for end in ("J1", "T")}
        self.final_frames["J1"] = j1_lug_frame(number, connection_mode)
        self.barrel_points = {
            end: _transform(point[None], np.linalg.inv(self.final_frames[end]))[0]
            for end, point in zip(("J1", "T"), self.final_points[[0, -1]], strict=True)
        }
        # Both CAD barrel entrances are horizontal. Finite polyline endpoint
        # chords have tiny pitch residuals, reported separately by validation.
        self.endpoint_heading = {"J1": 0.0, "T": np.pi if number == 1 else 0.0}
        self._lug_vertices = {
            end: lug_mesh(part)[0] for end, part in (("J1", j1_lug_part(connection_mode)), ("T", "6R14"))
        }

    def sample(
        self,
        progress: float,
        center: np.ndarray | tuple[float, float, float] | None = None,
        rotation: np.ndarray | None = None,
    ) -> WireShape:
        """Return a straight-to-installed shape with both endpoints moving.

        Args:
            progress: Normalized time, zero for straight and one for installed.
                A quintic time law gives zero endpoint velocity and acceleration
                at each boundary when the center and rotation remain fixed.
            center: Desired midpoint of the two insulation endpoints [m].
                Defaults to their midpoint in the existing product frame.
            rotation: Proper rotation applied about that midpoint. Defaults to
                identity; the final default shape exactly reuses ``wire_route``.

        Returns:
            Fixed-count centerline [m], two rigid CAD lug frames [m], and two
            moving grasp frames [m]. A grasp frame's X axis follows the wire
            from J1 toward T, Z is its local upward normal; the robot adapter
            must choose the gripper's opening axis and approach orientation.
        """
        q = _smooth(float(progress))
        rotation = np.eye(3) if rotation is None else np.asarray(rotation, dtype=float)
        center = self.final_center if center is None else np.asarray(center, dtype=float)
        if rotation.shape != (3, 3) or center.shape != (3,):
            raise ValueError("center must have shape (3,) and rotation (3, 3)")
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-8) or np.linalg.det(rotation) < 0.999999:
            raise ValueError("rotation must be a proper orthonormal matrix")
        heading, pitch = q * self.heading, q * self.pitch
        tangents = np.column_stack((np.cos(pitch) * np.cos(heading), np.cos(pitch) * np.sin(heading), np.sin(pitch)))
        integrated = np.vstack((np.zeros(3), np.cumsum(self.lengths[:, None] * tangents, axis=0)))
        points = (integrated - integrated[-1] / 2) @ rotation.T + center
        frames = {}
        for end, index in (("J1", 0), ("T", -1)):
            r = rotation @ _rz((q - 1) * self.endpoint_heading[end]) @ self.final_frames[end][:3, :3]
            frames[end] = pose(r, points[index] - r @ self.barrel_points[end])
        grasp_frames = {}
        for end, distance in (("J1", self.grasp_offset), ("T", self.length - self.grasp_offset)):
            index = min(np.searchsorted(self.arc, distance, side="right") - 1, len(self.lengths) - 1)
            alpha = (distance - self.arc[index]) / self.lengths[index]
            p = (1 - alpha) * points[index] + alpha * points[index + 1]
            grasp_frames[end] = pose(rotation @ _tangent_frame(tangents[index]), p)
        return WireShape(points, frames, grasp_frames, progress)

    def assembly_vertices(self, shape: WireShape) -> np.ndarray:
        """Return the centerline and rigid CAD lug vertices for bounds [m].

        The centerline has no thickness in this array. Add the wire radius when
        defining a support tray envelope. Existing sleeves require their own
        clearance; this does not define a conductor cut length.
        """
        return np.vstack(
            (shape.centerline, *(_transform(self._lug_vertices[end], shape.lug_frames[end]) for end in ("J1", "T")))
        )

    def assembly_bounds(self, shape: WireShape) -> np.ndarray:
        """Return conservative full assembly axis-aligned bounds [m].

        Includes unchanged CAD lugs, insulation radius and the existing rigid
        heatshrink sleeves. The conductor cylinders lie inside these envelopes.
        Tube end caps are overbounded by a radius in every coordinate direction.
        """
        vertices = self.assembly_vertices(shape)
        low = np.minimum(vertices.min(axis=0), shape.centerline.min(axis=0) - WIRE_RADIUS)
        high = np.maximum(vertices.max(axis=0), shape.centerline.max(axis=0) + WIRE_RADIUS)
        j1_center, j1_axis = (0.020, 0.0, 0.022), (0.0, 0.0, 1.0)
        if self.connection_mode == "top_entry":
            j1_center, j1_axis = top_entry_spec()["heatshrink_center_local_m"], (1.0, 0.0, 0.0)
        for end, local_center, local_axis in (
            ("J1", j1_center, j1_axis),
            ("T", (0.039, 0.0, 0.008), (1.0, 0.0, 0.0)),
        ):
            frame = shape.lug_frames[end]
            center = _transform(np.asarray(local_center)[None], frame)[0]
            axis = frame[:3, :3] @ np.asarray(local_axis)
            radius = 0.008 * np.sqrt(np.maximum(0.0, 1 - axis**2))
            extent = 0.0115 * abs(axis) + radius
            low, high = np.minimum(low, center - extent), np.maximum(high, center + extent)
        return np.stack((low, high))

    def material_frame(self, shape: WireShape, distance: float) -> np.ndarray:
        """Return a moving material-point frame at insulation arclength [m].

        Args:
            shape: State returned by :meth:`sample`.
            distance: Fixed material arclength from the J1 insulation end [m].

        Returns:
            Rigid frame [m] with X along J1-to-T tangent. The Z reference is
            transported from the shape's J1 grasp-frame normal. A robot adapter
            may apply a fixed local rotation to reproduce its final grip roll.
        """
        if not 0 <= distance <= self.length:
            raise ValueError("distance must lie on the insulation centerline")
        index = min(np.searchsorted(self.arc, distance, side="right") - 1, len(self.lengths) - 1)
        alpha = (distance - self.arc[index]) / self.lengths[index]
        a, b = shape.centerline[index : index + 2]
        x = (b - a) / np.linalg.norm(b - a)
        z = shape.grasp_frames["J1"][:3, 2].copy()
        z -= np.dot(z, x) * x
        z /= np.linalg.norm(z)
        return pose(np.column_stack((x, np.cross(z, x), z)), (1 - alpha) * a + alpha * b)

    def tube_mesh(self, shape: WireShape, sides: int = 16) -> tuple[np.ndarray, np.ndarray]:
        """Return fixed-topology tube vertices [m] and quad faces.

        Args:
            shape: State returned by :meth:`sample`.
            sides: Constant cross-section vertex count; at least eight.

        Returns:
            Vertices [m] and quad index array. End rings remain open so the
            existing rigid barrel/sleeve parts provide the visual termination.
        """
        if sides < 8:
            raise ValueError("At least eight radial sides are required")
        points = shape.centerline
        segment_tangents = np.diff(points, axis=0)
        segment_tangents /= np.linalg.norm(segment_tangents, axis=1)[:, None]
        tangents = np.vstack((segment_tangents[0], segment_tangents[:-1] + segment_tangents[1:], segment_tangents[-1]))
        tangents /= np.linalg.norm(tangents, axis=1)[:, None]
        # Parallel transport avoids flips when a planar U passes through pi.
        normals = np.empty_like(tangents)
        first = shape.grasp_frames["J1"][:3, 2]
        normals[0] = first - np.dot(first, tangents[0]) * tangents[0]
        normals[0] /= np.linalg.norm(normals[0])
        for i in range(1, len(points)):
            a, b = tangents[i - 1], tangents[i]
            v = np.cross(a, b)
            c = np.dot(a, b)
            previous = normals[i - 1]
            normals[i] = previous + np.cross(v, previous) + np.cross(v, np.cross(v, previous)) / (1 + c)
            normals[i] -= np.dot(normals[i], b) * b
            normals[i] /= np.linalg.norm(normals[i])
        binormals = np.cross(tangents, normals)
        angles = np.arange(sides) * 2 * np.pi / sides
        offsets = WIRE_RADIUS * (
            np.cos(angles)[None, :, None] * normals[:, None] + np.sin(angles)[None, :, None] * binormals[:, None]
        )
        vertices = (points[:, None] + offsets).reshape(-1, 3)
        row = np.arange(len(points) - 1)[:, None] * sides
        column = np.arange(sides)[None]
        faces = np.stack(
            (row + column, row + (column + 1) % sides, row + sides + (column + 1) % sides, row + sides + column),
            axis=-1,
        )
        return vertices, faces.reshape(-1, 4)


def supply_layout(
    counts: tuple[int, int] = (5, 5),
    pitch: float = 0.065,
    center: np.ndarray | tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: np.ndarray | None = None,
    *,
    connection_mode: ConnectionMode = "rear_entry",
) -> list[dict]:
    """Arrange straight wires side by side, lengths along local X [m].

    Args:
        counts: H03-1 and H03-2 quantities. The default is five of each, ten
            total; this is a configurable allocation candidate.
        pitch: Row center spacing [m]. The provisional 65 mm pitch leaves
            space between the CAD lugs; robot/gripper clearance is separate.
        center: Midpoint of the row array and wire endpoints [m].
        rotation: Proper rotation of the entire row array.
        connection_mode: Select the same inlet and wire lengths as the work station.

    Returns:
        Records containing stable part IDs, row indices and ``WireShape``.
    """
    if len(counts) != 2 or any(not isinstance(count, int) or count < 0 for count in counts) or sum(counts) < 1:
        raise ValueError("counts must be two nonnegative integers with a nonzero sum")
    if pitch <= 2 * WIRE_RADIUS:
        raise ValueError("row pitch must exceed the wire diameter")
    rotation = np.eye(3) if rotation is None else np.asarray(rotation, dtype=float)
    center = np.asarray(center, dtype=float)
    result = []
    for number, count in enumerate(counts, start=1):
        bend = WireBend(number, connection_mode=connection_mode)
        for index in range(count):
            row = len(result)
            offset = rotation @ np.array((0.0, (row - (sum(counts) - 1) / 2) * pitch, 0.0))
            result.append(
                {
                    "uid": f"OP030B_H03_{number}_UID{index + 1:03d}",
                    "number": number,
                    "row": row,
                    "shape": bend.sample(0.0, center + offset, rotation),
                }
            )
    return result


def _bend_radius(points: np.ndarray) -> float:
    a, b = np.diff(points, axis=0)[:-1], np.diff(points, axis=0)[1:]
    cross = np.linalg.norm(np.cross(a, b), axis=1)
    numerator = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) * np.linalg.norm(a + b, axis=1)
    curved = cross > 1e-14
    return float(np.min(numerator[curved] / (2 * cross[curved]))) if curved.any() else float("inf")


def _nonlocal_clearance(points: np.ndarray, arc: np.ndarray) -> float:
    # Pairwise segment distance, excluding local neighbors less than four
    # tube radii apart in material arclength. This is not an obstacle check.
    indices = np.arange(len(points) - 1)
    i, j = np.meshgrid(indices, indices, indexing="ij")
    mask = (j > i) & ((arc[j] - arc[i + 1]) > 4 * WIRE_RADIUS)
    i, j = i[mask], j[mask]
    p, q = points[i], points[j]
    u, v = points[i + 1] - p, points[j + 1] - q
    w = p - q
    a, b, c = np.sum(u * u, axis=1), np.sum(u * v, axis=1), np.sum(v * v, axis=1)
    d, e = np.sum(u * w, axis=1), np.sum(v * w, axis=1)
    denominator = a * c - b * b
    s = np.zeros_like(a)
    nonparallel = denominator > 1e-24
    s[nonparallel] = (b * e - c * d)[nonparallel] / denominator[nonparallel]
    t = (b * s + e) / c
    interior = nonparallel & (s >= 0) & (s <= 1) & (t >= 0) & (t <= 1)
    interior_distance = np.linalg.norm(w + s[:, None] * u - t[:, None] * v, axis=1)
    interior_distance[~interior] = np.inf
    distances = [interior_distance]
    for endpoint in (0.0, 1.0):
        t = np.clip((b * endpoint + e) / c, 0, 1)
        distances.append(np.linalg.norm(w + endpoint * u - t[:, None] * v, axis=1))
        s = np.clip((b * endpoint - d) / a, 0, 1)
        distances.append(np.linalg.norm(w + s[:, None] * u - endpoint * v, axis=1))
    distance = np.minimum.reduce(distances)
    return float(distance.min() - 2 * WIRE_RADIUS)


def validate(samples: int = 401, connection_mode: ConnectionMode = "rear_entry") -> dict:
    """Measure geometric invariants over the full bend family [m, rad].

    Args:
        samples: Uniform normalized-time samples, including both boundaries.

    Returns:
        Auxiliary geometric results. No material limits or physical verdict.
    """
    if samples < 3:
        raise ValueError("At least three progress samples are required")
    output = {"sample_count_per_wire": samples, "geometry_only": True, "formal_physical_verdict": None, "wires": {}}
    crossing = np.array(((-0.1, -0.1, 0), (0.1, 0.1, 0), (-0.1, 0.1, 0), (0.1, -0.1, 0)))
    crossing_arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(crossing, axis=0), axis=1))]
    assert abs(_nonlocal_clearance(crossing, crossing_arc) + 2 * WIRE_RADIUS) < 1e-12
    output["known_crossing_self_distance_rejected"] = True
    for number in (1, 2):
        bend = WireBend(number, connection_mode=connection_mode)
        errors = {
            "maximum_segment_length_error_m": 0.0,
            "maximum_centerline_length_error_m": 0.0,
            "maximum_barrel_attachment_gap_m": 0.0,
            "minimum_centerline_bend_radius_m": float("inf"),
            "minimum_nonlocal_tube_clearance_m": float("inf"),
            "maximum_endpoint_tangent_mismatch_rad": 0.0,
        }
        reference_faces = None
        for progress in np.linspace(0.0, 1.0, samples):
            shape = bend.sample(float(progress))
            lengths = np.linalg.norm(np.diff(shape.centerline, axis=0), axis=1)
            errors["maximum_segment_length_error_m"] = max(
                errors["maximum_segment_length_error_m"], float(abs(lengths - bend.lengths).max())
            )
            errors["maximum_centerline_length_error_m"] = max(
                errors["maximum_centerline_length_error_m"], abs(float(lengths.sum()) - bend.length)
            )
            errors["minimum_centerline_bend_radius_m"] = min(
                errors["minimum_centerline_bend_radius_m"], _bend_radius(shape.centerline)
            )
            errors["minimum_nonlocal_tube_clearance_m"] = min(
                errors["minimum_nonlocal_tube_clearance_m"], _nonlocal_clearance(shape.centerline, bend.arc)
            )
            for end, index, segment in (("J1", 0, 0), ("T", -1, -1)):
                actual = _transform(bend.barrel_points[end][None], shape.lug_frames[end])[0]
                errors["maximum_barrel_attachment_gap_m"] = max(
                    errors["maximum_barrel_attachment_gap_m"], float(np.linalg.norm(actual - shape.centerline[index]))
                )
                tangent = np.diff(shape.centerline, axis=0)[segment] / lengths[segment]
                ideal = _rz(_smooth(float(progress)) * bend.endpoint_heading[end])[:, 0]
                angle = np.arctan2(np.linalg.norm(np.cross(tangent, ideal)), np.dot(tangent, ideal))
                errors["maximum_endpoint_tangent_mismatch_rad"] = max(
                    errors["maximum_endpoint_tangent_mismatch_rad"], float(angle)
                )
            if progress in (0, 0.5, 1):
                vertices, faces = bend.tube_mesh(shape)
                assert np.isfinite(vertices).all()
                if reference_faces is None:
                    reference_faces = faces
                assert np.array_equal(faces, reference_faces)
        straight, installed = bend.sample(0.0), bend.sample(1.0)
        assert np.max(abs(straight.centerline[:, 1:] - straight.centerline[0, 1:])) < 1e-12
        assert np.max(abs(installed.centerline - bend.final_points)) < 1e-12
        assert all(np.max(abs(installed.lug_frames[end] - bend.final_frames[end])) < 1e-12 for end in ("J1", "T"))
        assert errors["maximum_segment_length_error_m"] < 1e-12
        assert errors["maximum_barrel_attachment_gap_m"] < 1e-12
        assert errors["minimum_centerline_bend_radius_m"] > WIRE_RADIUS
        assert errors["minimum_nonlocal_tube_clearance_m"] > 0
        rotated = bend.sample(0.43, (0.1, -0.2, 0.3), _rz(0.65))
        unrotated = bend.sample(0.43)
        expected = (unrotated.centerline - bend.final_center) @ _rz(0.65).T + (0.1, -0.2, 0.3)
        assert np.max(abs(rotated.centerline - expected)) < 1e-12
        naive = (straight.centerline + installed.centerline) / 2
        naive_error = abs(float(np.linalg.norm(np.diff(naive, axis=0), axis=1).sum()) - bend.length)
        assert naive_error > 0.005, "Control case must expose Cartesian interpolation shrinkage"
        vertices = bend.assembly_vertices(straight)
        output["wires"][str(number)] = {
            **errors,
            "centerline_length_m": bend.length,
            "centerline_vertex_count": len(bend.final_points),
            "grasp_offset_from_insulation_end_m": bend.grasp_offset,
            "straight_cad_and_centerline_bounds_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
            "straight_cad_and_centerline_extents_m": np.ptp(vertices, axis=0).tolist(),
            "straight_full_assembly_bounds_m": bend.assembly_bounds(straight).tolist(),
            "naive_cartesian_midpoint_length_error_m": naive_error,
            "local_self_distance_exclusion_arc_m": 4 * WIRE_RADIUS,
            "boundary_velocity_and_acceleration": "Analytically zero for fixed center/rotation by quintic time law",
        }
    layout = supply_layout(connection_mode=connection_mode)
    boxes = [WireBend(row["number"], connection_mode=connection_mode).assembly_vertices(row["shape"]) for row in layout]
    full_bounds = [
        WireBend(row["number"], connection_mode=connection_mode).assembly_bounds(row["shape"]) for row in layout
    ]
    vertices = np.vstack(boxes)
    output["supply_default"] = {
        "counts_by_type": [5, 5],
        "total": 10,
        "row_pitch_m": 0.065,
        "cad_and_centerline_bounds_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
        "cad_and_centerline_extents_m": np.ptp(vertices, axis=0).tolist(),
        "minimum_adjacent_row_bounds_gap_m": min(
            float(b[:, 1].min() - a[:, 1].max()) for a, b in zip(boxes[:-1], boxes[1:], strict=True)
        ),
        "uid_count": len({row["uid"] for row in layout}),
        "full_assembly_bounds_m": [np.min(full_bounds, axis=0)[0].tolist(), np.max(full_bounds, axis=0)[1].tolist()],
        "minimum_adjacent_full_bounds_gap_m": min(
            float(b[0, 1] - a[1, 1]) for a, b in zip(full_bounds[:-1], full_bounds[1:], strict=True)
        ),
        "allocation_status": "5+5 provisional; configurable",
    }
    output["limitations"] = [
        "Geometry only; no rod forces, material bending limit, crimp deformation, grasp friction "
        "or robot collision verdict.",
        "Full assembly bounds include tube and sleeves conservatively; add fixture/manipulator clearance separately.",
        "Full wire conductor cut length cannot be inferred by adding lug AABB sizes to visible centerline length.",
        "Fixed interpolation topology does not itself validate swept surfaces or continuous robot motion.",
    ]
    output["source_hashes"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            Path(__file__),
            ROOT / "scripts/op030_definition.py",
            ROOT / "inputs/op030_reference/Klauke_46R6.json",
            ROOT / "inputs/op030_reference/Klauke_6R14.json",
        )
    }
    output["passed"] = True
    if connection_mode == "top_entry":
        output["connection_mode"] = connection_mode
        output["connection_spec"] = top_entry_spec()
        for name in ("scripts/op030_split_top_entry.py", "inputs/op030_reference/Klauke_6R6.json"):
            output["source_hashes"][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for number in (1, 2):
            old = float(np.linalg.norm(np.diff(wire_route(number), axis=0), axis=1).sum())
            output["wires"][str(number)]["previous_centerline_length_m"] = old
            output["wires"][str(number)]["centerline_length_delta_m"] = (
                output["wires"][str(number)]["centerline_length_m"] - old
            )
    return output


def main() -> None:
    """Write the geometric audit and reusable representative centerlines."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=401)
    parser.add_argument("--output", type=Path, default=ROOT / "audit/op030_split_wire_geometry.json")
    parser.add_argument("--connection_mode", choices=("rear_entry", "top_entry"), default="rear_entry")
    parser.add_argument("--shapes_output", type=Path)
    args = parser.parse_args()
    if args.connection_mode == "top_entry" and args.output.name == "op030_split_wire_geometry.json":
        parser.error("Top-entry geometry requires a separate --output file")
    result = validate(args.samples, args.connection_mode)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    arrays = {}
    for number in (1, 2):
        bend = WireBend(number, connection_mode=args.connection_mode)
        shapes = [bend.sample(float(p)) for p in np.linspace(0.0, 1.0, 101)]
        arrays[f"wire_{number}_points"] = np.array([shape.centerline for shape in shapes])
        arrays[f"wire_{number}_lug_frames"] = np.array(
            [[shape.lug_frames[end] for end in ("J1", "T")] for shape in shapes]
        )
        arrays[f"wire_{number}_grasp_frames"] = np.array(
            [[shape.grasp_frames[end] for end in ("J1", "T")] for shape in shapes]
        )
    shapes_output = args.shapes_output or ROOT / "analysis" / (
        "split_wire_top_entry_shapes.npz" if args.connection_mode == "top_entry" else "split_wire_shapes.npz"
    )
    np.savez_compressed(shapes_output, progress=np.linspace(0.0, 1.0, 101), **arrays)
    print("OP030_SPLIT_WIRE_GEOMETRY_COMPLETE", json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
