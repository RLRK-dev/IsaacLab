# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse endpoint-following wire basis with an in-plane bend mode [m].

The OP020 vertical-only correction cannot shorten the pre-shaped OP030 U bend
when one end is seated first. The added mode flattens that existing bend
towards its own endpoint chord. This is geometry, not a rod/contact solver.
"""

import numpy as np
from direct_cable import basis
from scipy.optimize import brentq


def flatten_basis(points):
    distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    u = distance / distance[-1]
    chord = points[0] * (1 - u[:, None]) + points[-1] * u[:, None]
    return basis(points)[1, :, None] * (chord - points)


def coefficients(points, root, end, rest):
    """Preserve both endpoint frames and the sampled centerline length [m]."""
    masks = basis(points)
    relative = np.linalg.inv(root) @ end @ np.linalg.inv(rest)
    rotation, delta = relative[:3, :3] - np.eye(3), relative[:3, 3]
    bent = points + masks[0, :, None] * (points @ rotation.T + delta)
    correction = flatten_basis(points)
    target = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()

    def residual(amplitude):
        return np.linalg.norm(np.diff(bent + amplitude * correction, axis=0), axis=1).sum() - target

    if abs(residual(0)) < 1e-11:
        amplitude = 0.0
    else:
        grid = np.linspace(-1.2, 1.2, 97)
        values = [residual(x) for x in grid]
        roots = [
            brentq(residual, a, b, xtol=1e-12)
            for a, b, x, y in zip(grid[:-1], grid[1:], values[:-1], values[1:], strict=True)
            if x * y < 0
        ]
        if not roots:
            raise RuntimeError("No fixed-length OP030 shape in the bounded bend family")
        amplitude = min(roots, key=abs)
    return np.r_[rotation.ravel(), delta, np.zeros(4), amplitude]


def points_at(points, values):
    end, middle = basis(points)
    return (
        points
        + end[:, None] * (points @ values[:9].reshape(3, 3).T + values[9:12])
        + middle[:, None] * values[12:15]
        + middle[:, None] * (0, 0, values[15])
        + flatten_basis(points) * values[16]
    )
