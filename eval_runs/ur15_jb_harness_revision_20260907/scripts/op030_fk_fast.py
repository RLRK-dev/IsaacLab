# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Cache the original UR15 chain constants for repeated planner IK [m, rad]."""

from functools import lru_cache

import numpy as np
from op020_jb_motion import original
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

R = original.R
LIMITS = np.radians([360, 360, 180, 360, 360, 360])


@lru_cache(maxsize=512)
def chain_for(base_values):
    return Chain(np.asarray(base_values).reshape(4, 4))


class Chain:
    """Original UR15 transforms with a geometric Jacobian; no geometry changes."""

    def __init__(self, base):
        self.base = base @ R.transform(rpy=(0, 0, np.pi))
        self.constants = [R.transform(xyz, rpy) for xyz, rpy in R.UR15.KINEMATICS]
        self.last = R.transform(rpy=(0, -np.pi / 2, -np.pi / 2)) @ R.transform(rpy=(np.pi / 2, 0, np.pi / 2))

    def forward(self, joints):
        result = self.base.copy()
        origins, axes = [], []
        for q, fixed in zip(joints, self.constants, strict=True):
            result = result @ fixed
            origins.append(result[:3, 3].copy())
            axes.append(result[:3, 2].copy())
            turn = np.eye(4)
            c, s = np.cos(q), np.sin(q)
            turn[:2, :2] = [[c, -s], [s, c]]
            result = result @ turn
        result = result @ self.last
        jacobian = np.vstack((np.cross(axes, result[:3, 3] - origins).T, np.asarray(axes).T))
        return result, jacobian

    def residual(self, joints, target):
        result, jacobian = self.forward(joints)
        turn = Rotation.from_matrix(result[:3, :3] @ target[:3, :3].T).as_rotvec()
        x, y, z = turn
        skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
        angle = np.linalg.norm(turn)
        factor = 1 / 12 if angle < 1e-5 else (1 - 0.5 * angle / np.tan(0.5 * angle)) / angle**2
        inverse = np.eye(3) - 0.5 * skew + factor * (skew @ skew)
        jacobian[:3] *= 4
        jacobian[3:] = inverse @ jacobian[3:]
        return np.r_[4 * (result[:3, 3] - target[:3, 3]), turn], jacobian

    def solve(self, target, seed, max_nfev=35):
        start = np.clip(seed, -LIMITS + 1e-6, LIMITS - 1e-6)
        solution = least_squares(
            lambda q: self.residual(q, target)[0],
            start,
            jac=lambda q: self.residual(q, target)[1],
            bounds=(-LIMITS + 1e-7, LIMITS - 1e-7),
            max_nfev=max_nfev,
            ftol=1e-8,
            xtol=1e-8,
            gtol=1e-8,
        )
        return solution.x, float(np.linalg.norm(solution.fun))

    def solve_continuous(self, target, seed):
        solution = least_squares(
            lambda q: self.residual(q, target)[0], np.asarray(seed), jac=lambda q: self.residual(q, target)[1]
        )
        q = seed + np.arctan2(np.sin(solution.x - seed), np.cos(solution.x - seed))
        return q, float(np.linalg.norm(self.residual(q, target)[0]))
