# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""OP030 provisional assembly coordinates and reused wire-lug CAD [m, rad]."""

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CX, CY, JB_Z = -0.9, -1.7, 0.5345
LIFT = 0.350
DOCK_Y = -2.50
M6_EXTENSION = 0.120
M6_DOCK_Y = DOCK_Y - 0.100
M6_DOCK_X = -0.507 + M6_EXTENSION
NUT_ROWS_Y = (DOCK_Y - 0.15, DOCK_Y - 0.225)
WIRE_RADIUS = 0.007
TERMINAL_X = (-0.16, 0.16)
TERMINAL_Y = -0.145
TERMINAL_Z = 0.013
LUG_Z = 0.031
J1_X = -0.211
J1_Y = (-0.3115, -0.2885)
J1_Z = 0.012
J1_LUG_ROT = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]], dtype=float)


def nut_supply_xy(index):
    """Leave a clear horizontal socket entry before each M6 washer [m]."""
    if index in (4, 6):
        return -1.00, DOCK_Y - 0.15 - 0.075 * ((index - 4) // 2)
    return -0.73 + (index % 4) * 0.070, NUT_ROWS_Y[index // 4]


def pose(rotation=None, location=None):
    """Return a rigid transform [m]."""
    out = np.eye(4)
    if rotation is not None:
        out[:3, :3] = rotation
    if location is not None:
        out[:3, 3] = location
    return out


def product_frame(y=CY, lift=0.0):
    return pose(np.diag([-1.0, -1.0, 1.0]), (0, y, JB_Z + lift))


def lug_frame(number, end):
    """Return each lug's final product-local seating face and hole axis [m]."""
    if end == "J1":
        return pose(J1_LUG_ROT, (J1_X, J1_Y[number - 1], J1_Z))
    rotation = np.eye(3) if number == 1 else np.diag([-1.0, -1.0, 1.0])
    return pose(rotation, (TERMINAL_X[number - 1], TERMINAL_Y, LUG_Z))


def wire_route(number):
    """Return explicit tangent-continuous planar route with smooth height [m].

    The radius is a packaging candidate, not a released cable specification.
    Barrel entrances are taken directly from the unscaled CAD meshes.
    """
    start = np.array([J1_X + 0.0285, J1_Y[number - 1], 0.032])
    end = np.array([-0.115 if number == 1 else 0.115, -0.145, LUG_Z + 0.008])
    if number == 1:
        radius = 0.08325
        x = -0.065
        a = np.column_stack((np.linspace(start[0], x, 49), np.full(49, start[1])))
        angle = np.linspace(-np.pi / 2, np.pi / 2, 121)
        b = np.column_stack((x + radius * np.cos(angle), start[1] + radius + radius * np.sin(angle)))
        c = np.column_stack((np.linspace(x, end[0], 25), np.full(25, end[1])))
        xy = np.vstack((a, b[1:], c[1:]))
        top = 0.050
    else:
        radius = 0.07175
        x = -0.12
        a = np.column_stack((np.linspace(start[0], x, 33), np.full(33, start[1])))
        angle = np.linspace(-np.pi / 2, 0, 61)
        b = np.column_stack((x + radius * np.cos(angle), start[1] + radius + radius * np.sin(angle)))
        angle = np.linspace(np.pi, np.pi / 2, 61)
        c = np.column_stack((x + 2 * radius + radius * np.cos(angle), start[1] + radius + radius * np.sin(angle)))
        d = np.column_stack((np.linspace(x + 2 * radius, end[0], 41), np.full(41, end[1])))
        xy = np.vstack((a, b[1:], c[1:], d[1:]))
        top = 0.030
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
    u = arc / arc[-1]
    # Endpoint tangents are horizontal, matching both CAD barrel axes.
    w = u**3 * (10 - 15 * u + 6 * u**2)
    z = start[2] * (1 - w) + end[2] * w
    if number == 1:
        rise = np.clip(u / 0.40, 0, 1)
        fall = np.clip((u - 0.75) / 0.25, 0, 1)
        rise = rise**3 * (10 - 15 * rise + 6 * rise**2)
        fall = fall**3 * (10 - 15 * fall + 6 * fall**2)
        z = start[2] + (top - start[2]) * rise + (end[2] - top) * fall
    else:
        z += (top - (start[2] + end[2]) / 2) * np.sin(np.pi * u) ** 2
    return np.column_stack((xy, z))
