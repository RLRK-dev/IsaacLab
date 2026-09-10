# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Recognize specified seating/gripping surfaces from actual relative geometry."""

import re

import numpy as np

TOLERANCE = 0.00005


def local_vertices(vertices, world, target_world):
    transform = np.linalg.inv(target_world) @ world
    return vertices @ transform[:3, :3].T + transform[:3, 3]


def expected_contact(first, second, first_vertices, second_vertices, first_world, second_world):
    """Return the measured interface if its intrusion is at most 0.05 mm."""
    a, b = first.name, second.name
    if not a.startswith("OP030_precision_") and b.startswith("OP030_precision_"):
        return expected_contact(second, first, second_vertices, first_vertices, second_world, first_world)
    if a.startswith("OP030_precision_") and a.endswith(("_tip", "_stem")):
        frame = second.parent
        if b.startswith("OP030_driver_") and "_grip_flat" in b:
            points = local_vertices(first_vertices, first_world, np.asarray(frame.matrix_world))
            axis = 1 if "_M6_" in b else 0
            sign = -1 if b.endswith("-1") else 1
            clearance = float(np.min(points[:, axis] * sign) - 0.024)
            if clearance >= -TOLERANCE:
                return dict(interface="tool grip flat", minimum_signed_clearance_m=clearance)
        if a.endswith("_tip") and b.startswith(("OP030_T01_UID001", "OP030_T02_UID001")) and b.endswith("_insulator"):
            points = local_vertices(first_vertices, first_world, np.asarray(frame.matrix_world))
            direction = points[:, :2].mean(0)
            direction /= np.linalg.norm(direction)
            clearance = float(np.min(points[:, :2] @ direction) - 0.026)
            if clearance >= -TOLERANCE:
                return dict(interface="terminal insulating disc grip", minimum_signed_clearance_m=clearance)
        if (
            a.startswith("OP030_precision_right_")
            and a.endswith("_tip")
            and b.startswith("OP030_H03_")
            and b.endswith("_J1_heatshrink")
        ):
            points = local_vertices(first_vertices, first_world, np.asarray(frame.matrix_world))
            sign = 1 if points[:, 1].mean() > 0 else -1
            clearance = float(np.min(points[:, 1] * sign) - 0.008)
            if clearance >= -TOLERANCE:
                return dict(interface="J1 heatshrink grip", minimum_signed_clearance_m=clearance)
        if (
            a.startswith("OP030_precision_left_")
            and a.endswith("_tip")
            and re.fullmatch(r"OP030_H03_[12]_UID001_insulation", b)
        ):
            end = first.users_scene[0].objects.get(b.removesuffix("_insulation") + "_T")
            if end is None:
                return None
            reference = np.asarray(end.matrix_world)
            pad = local_vertices(first_vertices, first_world, reference)
            if not (0.045 <= pad[:, 0].mean() <= 0.085 and abs(pad[:, 1].mean()) < 0.020):
                return None
            wire = local_vertices(second_vertices, second_world, reference)
            # Restrict the measurement to the T-side grip patch. The distant
            # return leg of the U-shaped wire is outside this pair's contact.
            patch = (
                (wire[:, 0] >= pad[:, 0].min() - TOLERANCE)
                & (wire[:, 0] <= pad[:, 0].max() + TOLERANCE)
                & (wire[:, 2] >= pad[:, 2].min() - TOLERANCE)
                & (wire[:, 2] <= pad[:, 2].max() + TOLERANCE)
                & (abs(wire[:, 1]) < 0.025)
            )
            if patch.any():
                sign = 1 if pad[:, 1].mean() > 0 else -1
                clearance = float((pad[:, 1] * sign).min() - (wire[patch, 1] * sign).max())
                if clearance >= -TOLERANCE:
                    return dict(
                        interface="T-side insulation grip",
                        minimum_signed_clearance_m=clearance,
                        measured_surface_vertices=int(patch.sum()),
                    )
    if a.endswith("_nut_washer") and re.fullmatch(r"OP030_H03_([12])_UID001_(J1|T)_(46R6|6R14)", b):
        return expected_contact(second, first, second_vertices, first_vertices, second_world, first_world)
    match = re.fullmatch(r"OP030_H03_([12])_UID001_(J1|T)_(46R6|6R14)", a)
    if match and b == f"OP030_H03_{match[1]}_{match[2]}_nut_washer":
        lug_world = np.asarray(first.parent.matrix_world)
        nut_world = np.asarray(second.parent.matrix_world)
        relative = np.linalg.inv(lug_world) @ nut_world
        thickness = 0.0038 if match[2] == "J1" else 0.0032
        if (
            np.linalg.norm(relative[:2, 3]) <= TOLERANCE
            and abs(relative[2, 3] - thickness) <= TOLERANCE
            and np.linalg.norm(relative[:3, 2] - [0, 0, 1]) <= 0.0001
        ):
            points = local_vertices(first_vertices, first_world, nut_world)
            radius = np.linalg.norm(points[:, :2], axis=1)
            inner, outer = (0.0033, 0.006) if match[2] == "J1" else (0.0073, 0.014)
            inside = (radius >= inner - TOLERANCE) & (radius <= outer + TOLERANCE)
            protrusion = float(points[inside, 2].max()) if inside.any() else float("inf")
            if protrusion <= TOLERANCE:
                return dict(
                    interface="washer on CAD lug seating face",
                    maximum_lug_protrusion_m=protrusion,
                    axial_seating_error_m=float(relative[2, 3] - thickness),
                )
    return None
