# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Plan both physical arms together with the retained OMPL toolchain [rad].

The original free-path helper fixes its state dimension to six. This adapter
keeps its limits, RRTConnect settings and discrete verification, but presents
both physical arms to every validity call. It does not merge arm-only paths.
"""

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
from op030_free_paths import LIMITS, ob, og

SOLVE_LIMIT_S = 25.0
INTERNAL_STEP_RAD = 0.005
FINAL_STEP_RAD = 0.0025


def plan_free_path_12d(
    start: np.ndarray,
    stop: np.ndarray,
    score: Callable[[np.ndarray], float],
) -> tuple[np.ndarray | None, dict]:
    """Return a simultaneously screened dual-arm path and auxiliary audit.

    Args:
        start: Physical left/right joint angles [rad], shape [2, 6].
        stop: Physical left/right joint angles [rad], shape [2, 6].
        score: Actual-mesh query receiving both arms [rad], shape [2, 6];
            zero means clear and any nonzero/nonfinite value rejects the state.

    Returns:
        Joint path [rad], shape [waypoint_count, 2, 6], or None, and a JSON-ready
        audit. Straight and final segment samples have 12D Euclidean spacing
        at most 0.0025 rad. OMPL gets one 25 s solve, followed by at most 0.5 s
        of simplification and discrete verification. Callback/verification
        time is additional. This is not a continuous or physical-validity verdict.
    """
    started = time.monotonic()
    start, stop = np.asarray(start, dtype=float), np.asarray(stop, dtype=float)
    limits = np.tile(LIMITS, 2)
    source = Path(__file__).with_name("op030_free_paths.py")
    record = dict(
        reused_source=str(source),
        reused_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        state_dimension=12,
        physical_arm_order=["left", "right"],
        joint_limits_rad=limits.reshape(2, 6).tolist(),
        solve_limit_s=SOLVE_LIMIT_S,
        maximum_solve_calls=1,
        solve_calls=0,
        internal_euclidean_step_rad=INTERNAL_STEP_RAD,
        final_euclidean_step_rad=FINAL_STEP_RAD,
        actual_score_calls=0,
        invalid_numeric_scores=0,
        direct_samples_checked=0,
        final_samples_checked=0,
        exact_solution=False,
        accepted=False,
        formal_physical_validity_verdict=None,
    )

    def finish(points: np.ndarray | None, reason: str) -> tuple[np.ndarray | None, dict]:
        record["reason"] = reason
        record["elapsed_wall_s"] = time.monotonic() - started
        record["accepted"] = points is not None
        if points is not None:
            record["waypoints"] = len(points)
            record["joint_path_length_rad"] = float(
                np.linalg.norm(np.diff(points.reshape(-1, 12), axis=0), axis=1).sum()
            )
        return points, record

    if start.shape != (2, 6) or stop.shape != (2, 6):
        return finish(None, "Expected physical-arm start/stop arrays with shape [2, 6]")
    if not np.all(np.isfinite(start)) or not np.all(np.isfinite(stop)):
        return finish(None, "Nonfinite endpoint joints")
    first, last = start.ravel(), stop.ravel()
    if np.any(abs(first) > limits) or np.any(abs(last) > limits):
        return finish(None, "Endpoint outside retained joint limits")

    def valid(flat: np.ndarray) -> bool:
        if not np.all(np.isfinite(flat)) or np.any(abs(flat) > limits):
            return False
        value = float(score(flat.reshape(2, 6).copy()))
        record["actual_score_calls"] += 1
        if not np.isfinite(value):
            record["invalid_numeric_scores"] += 1
        return bool(np.isfinite(value) and value == 0.0)

    first_clear, last_clear = valid(first), valid(last)
    record["endpoints_clear"] = [first_clear, last_clear]
    if not first_clear or not last_clear:
        return finish(None, "Start or goal failed the simultaneous actual-mesh query")
    direct_count = max(2, int(np.ceil(np.linalg.norm(last - first) / FINAL_STEP_RAD)) + 1)
    direct_clear = True
    for joints in np.linspace(first, last, direct_count):
        record["direct_samples_checked"] += 1
        if not valid(joints):
            direct_clear = False
            record["direct_rejected_q_rad"] = joints.reshape(2, 6).tolist()
            break
    if direct_clear:
        record["exact_solution"] = True
        record["final_samples_checked"] = direct_count
        record["solution_kind"] = "simultaneous_straight"
        return finish(np.array([start, stop]), "Direct 12D segment passed the final-spacing actual-mesh query")

    space = ob.RealVectorStateSpace(12)
    bounds = ob.RealVectorBounds(12)
    for index, limit in enumerate(limits):
        bounds.setLow(index, -float(limit))
        bounds.setHigh(index, float(limit))
    space.setBounds(bounds)
    space.setLongestValidSegmentFraction(INTERNAL_STEP_RAD / np.linalg.norm(2 * limits))
    setup = og.SimpleSetup(space)
    setup.setStateValidityChecker(lambda state: valid(np.array([state[index] for index in range(12)])))
    begin, end = space.allocState(), space.allocState()
    for index in range(12):
        begin[index], end[index] = float(first[index]), float(last[index])
    setup.setStartAndGoalStates(begin, end)
    planner = og.RRTConnect(setup.getSpaceInformation())
    planner.setRange(0.35)
    setup.setPlanner(planner)
    record["solve_calls"] = 1
    solve_started = time.monotonic()
    setup.solve(SOLVE_LIMIT_S)
    record["solve_wall_s"] = time.monotonic() - solve_started
    if not setup.getProblemDefinition().hasExactSolution():
        return finish(None, "No exact simultaneous OMPL path within the single 25 s solve")
    record["exact_solution"] = True
    setup.simplifySolution(0.5)
    path = np.array([[state[index] for index in range(12)] for state in setup.getSolutionPath().getStates()])
    if len(path) < 2 or np.max(abs(path[0] - first)) > 1e-8 or np.max(abs(path[-1] - last)) > 1e-8:
        return finish(None, "Exact OMPL path did not retain both requested endpoints")
    for index, (a, b) in enumerate(zip(path[:-1], path[1:], strict=True)):
        count = max(2, int(np.ceil(np.linalg.norm(b - a) / FINAL_STEP_RAD)) + 1)
        for joints in np.linspace(a, b, count):
            record["final_samples_checked"] += 1
            if not valid(joints):
                record["rejected_segment"] = index
                record["rejected_q_rad"] = joints.reshape(2, 6).tolist()
                record["rejected_path_rad"] = path.reshape(-1, 2, 6).tolist()
                return finish(None, "Final 0.0025 rad simultaneous actual-mesh query failed")
    record["solution_kind"] = "simultaneous_rrt_connect"
    return finish(path.reshape(-1, 2, 6), "Exact simultaneous OMPL path passed the final-spacing actual-mesh query")
