# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Length-preserving cable shape proposal; no material/contact simulation [m]."""

import numpy as np
from scipy.optimize import brentq


def smooth_array(x):
    x = np.clip(x, 0, 1)
    return x**3 * (10 - 15 * x + 6 * x * x)


def basis(points):
    distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    s = distances / distances[-1]
    end = smooth_array((s - 0.48) / 0.44)
    middle = np.sin(np.pi * np.clip((s - 0.08) / 0.84, 0, 1)) ** 2
    return np.array([end, middle])


def coefficients(points, masks, harness, b_target, b_rest, air, outward_bow=0.0):
    relative = np.linalg.inv(harness) @ b_target @ np.linalg.inv(b_rest)
    rotation = relative[:3, :3] - np.eye(3)
    delta = relative[:3, 3]
    sag = harness[:3, :3].T @ np.array([0, 0, -0.040 * air])
    sag[0] += outward_bow
    deformed = points + masks[0, :, None] * (points @ rotation.T + delta) + masks[1, :, None] * sag
    target = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
    direction = masks[1, :, None] * np.array([0, 0, 1])

    def difference(amplitude):
        return np.linalg.norm(np.diff(deformed + direction * amplitude, axis=0), axis=1).sum() - target

    if abs(difference(0)) < 1e-12:
        amplitude = 0.0
    else:
        grid = np.linspace(-0.24, 0.32, 113)
        values = [difference(x) for x in grid]
        intervals = [
            (a, b) for a, b, x, y in zip(grid[:-1], grid[1:], values[:-1], values[1:], strict=True) if x * y <= 0
        ]
        if not intervals:
            raise RuntimeError("No cable-length-preserving shape in the bounded family")
        roots = [brentq(difference, a, b, xtol=1e-12) for a, b in intervals]
        # The upper root connects to the undeformed supply shape. Selecting the
        # smallest absolute root switches between different loop shapes in flight.
        amplitude = max(roots)
    return np.r_[rotation.ravel(), delta, sag, amplitude]
