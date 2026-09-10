# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Use official OMPL RRTConnect for unconstrained joint transits [rad].

IsaacLab's available cuRobo adapter requires a live Isaac articulation and a
cuRobo installation; neither belongs to this retained Blender/FK pipeline.
OMPL 2.0.1 is an isolated planning tool, not an IsaacLab core dependency.
"""

import sys

import numpy as np

try:
    from ompl import base as ob
    from ompl import geometric as og
    from ompl import util as ou
except ImportError:
    sys.path.insert(0, "/tmp/ur15_op030_ompl")
    from ompl import base as ob
    from ompl import geometric as og
    from ompl import util as ou

ou.RNG.setSeed(830)
ou.setLogLevel(ou.LOG_WARN)
LIMITS = np.radians([360, 360, 180, 360, 360, 360]) - 1e-6


def plan_free_path(start, stop, score):
    """Return a discretely screened free path, or fail closed [rad]."""
    start_score, stop_score = score(start), score(stop)
    plan_free_path.last_debug = dict(start_score=start_score, stop_score=stop_score)
    if start_score > 0 or stop_score > 0:
        return None
    count = max(2, int(np.ceil(np.linalg.norm(stop - start) / 0.0025)) + 1)
    if all(score(q) == 0 for q in np.linspace(start, stop, count)):
        return np.array([start, stop])
    space = ob.RealVectorStateSpace(6)
    bounds = ob.RealVectorBounds(6)
    for i, limit in enumerate(LIMITS):
        bounds.setLow(i, -float(limit))
        bounds.setHigh(i, float(limit))
    space.setBounds(bounds)
    # Refine OMPL's internal screen below the original 0.025 rad spacing.
    # Thin fingertips can cross a surface between those earlier samples.
    space.setLongestValidSegmentFraction(0.005 / np.linalg.norm(2 * LIMITS))
    setup = og.SimpleSetup(space)
    setup.setStateValidityChecker(lambda state: score(np.array([state[i] for i in range(6)])) == 0)
    begin, end = space.allocState(), space.allocState()
    for i in range(6):
        begin[i], end[i] = float(start[i]), float(stop[i])
    setup.setStartAndGoalStates(begin, end)
    planner = og.RRTConnect(setup.getSpaceInformation())
    planner.setRange(0.35)
    setup.setPlanner(planner)
    setup.solve(25.0)
    if not setup.getProblemDefinition().hasExactSolution():
        plan_free_path.last_debug["reason"] = "No exact OMPL path within 25 seconds"
        return None
    setup.simplifySolution(0.5)
    path = np.array([[state[i] for i in range(6)] for state in setup.getSolutionPath().getStates()])
    for a, b in zip(path[:-1], path[1:], strict=True):
        steps = max(2, int(np.ceil(np.linalg.norm(b - a) / 0.0025)) + 1)
        for q in np.linspace(a, b, steps):
            if score(q) > 0:
                plan_free_path.last_debug.update(
                    reason="Final discrete path screen failed", rejected_path=path.tolist(), rejected_q=q.tolist()
                )
                return None
    return path
