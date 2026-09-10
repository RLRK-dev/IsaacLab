# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Choose a continuous IK branch over a complete grasp-to-release section."""

import json
from difflib import SequenceMatcher

import numpy as np
from op030_motion import SIDES, evaluate_phase, is_joint_transit

LIMITS = np.radians([360, 360, 180, 360, 360, 360]) - 1e-6


def is_free(phase, side):
    return is_joint_transit(phase, side)


class BranchChoice:
    """Prioritize discrete whole-section clearance over a local IK branch swap."""

    def __init__(self, sequence, screen, robots, reference, fk, solve):
        self.sequence, self.screen, self.robots = sequence, screen, robots
        self.fk, self.solve = fk, solve
        with np.load(reference) as data:
            self.reference_times = data["times"].copy()
            self.reference_joints = data["joints"].copy()
        previous = json.loads((reference.parent.parent / "audit" / (reference.stem + ".json")).read_text())["phases"]
        matches = SequenceMatcher(
            None, [p["label"] for p in sequence.phases], [p["label"] for p in previous], autojunk=False
        ).get_matching_blocks()
        anchors = {}
        for new, old, count in matches:
            for k in range(count):
                for key in ("start", "stop"):
                    anchors[sequence.phases[new + k][key]] = previous[old + k][key]
        self.reference_time_mapping = np.asarray(sorted(anchors.items()))
        self.predictions = {0: [], 1: []}
        self.reports = []

    def prediction(self, side, time):
        for times, joints in reversed(self.predictions[side]):
            if times[0] - 1e-8 <= time <= times[-1] + 1e-8:
                return np.array([np.interp(time, times, joints[:, i]) for i in range(6)])
        return None

    def reference(self, side, time):
        predicted = self.prediction(side, time)
        if predicted is not None:
            return predicted
        mapped = np.interp(time, self.reference_time_mapping[:, 0], self.reference_time_mapping[:, 1])
        return np.array([np.interp(mapped, self.reference_times, self.reference_joints[:, side, i]) for i in range(6)])

    def pick(self, phase_index, side, options):
        start = self.sequence.phases[phase_index]["stop"]
        stop_index = phase_index + 1
        while stop_index < len(self.sequence.phases) and not is_free(self.sequence.phases[stop_index], side):
            stop_index += 1
        stop = self.sequence.phases[min(stop_index, len(self.sequence.phases) - 1)]["start"]
        selected = self.sequence.phases[phase_index:stop_index]
        samples = [start, stop]
        for phase in selected:
            moving = not np.allclose(phase["before"]["hands"], phase["after"]["hands"], atol=1e-8, rtol=0) or bool(
                phase["turn"]
            )
            step = 0.125 if "M6" in str(phase["before"]["holds"].get(side)) else 0.25
            samples.extend(np.arange(max(start, phase["start"]), min(stop, phase["stop"]), step if moving else 1.0))
            samples.extend([max(start, phase["start"]), min(stop, phase["stop"])])
        times = np.unique(np.round(samples, 9))
        times = times[times >= start - 1e-7]
        targets = []
        index = phase_index
        for t in times:
            while index + 1 < len(self.sequence.phases) and t > self.sequence.phases[index]["stop"] + 1e-7:
                index += 1
            targets.append(evaluate_phase(self.sequence.phases[index], t))
        unique = []
        for option in sorted(options, key=lambda x: x[0]):
            if all(
                np.linalg.norm(np.arctan2(np.sin(option[1] - old[1]), np.cos(option[1] - old[1]))) > 0.02
                for old in unique
            ):
                unique.append(option)
        results = []
        for cost, initial, error in unique:
            q = initial.copy()
            joints, collisions, max_error = [], 0.0, error
            worst_time = float(start)
            for t, target in zip(times, targets, strict=True):
                base = target["root"] @ self.fk.yoke_base_pose(SIDES[side])
                goal = target["tools"][side]
                q, residual = self.solve(base, goal[:3, 3], q, orientation=goal[:3, :3])
                if residual > max_error:
                    max_error, worst_time = residual, float(t)
                self.screen.set_poses(target["objects"])
                self.screen.set_poses({576: self.screen.fixed_base, 577: target["root"], 578: target["root"]})
                for arm in (1 - side, side):
                    robot, capture = self.robots[SIDES[arm]]
                    robot.base_pose = target["root"] @ self.fk.yoke_base_pose(SIDES[arm])
                    robot.update(q if arm == side else self.reference(arm, t), float(target["grips"][arm]))
                    self.screen.set_poses(capture.poses)
                collisions += self.screen.score(side)
                joints.append(q.copy())
            joints = np.asarray(joints)
            shifts = np.zeros(6)
            for joint in range(6):
                lower = int(np.ceil((-LIMITS[joint] - joints[:, joint].min()) / (2 * np.pi)))
                upper = int(np.floor((LIMITS[joint] - joints[:, joint].max()) / (2 * np.pi)))
                if lower > upper:
                    max_error = max(max_error, 1.0)
                else:
                    # Choose the equivalent whole-section winding with the
                    # greatest remaining joint travel. Keeping an initial -270
                    # degree wrist angle previously ended near the -360 limit
                    # and forced a long, obstructed unwind after releasing.
                    candidates = range(lower, upper + 1)
                    initial_shift = min(candidates, key=abs)
                    current_max = max(
                        abs(joints[:, joint].min() + 2 * np.pi * initial_shift),
                        abs(joints[:, joint].max() + 2 * np.pi * initial_shift),
                    )
                    if self.sequence.phases[phase_index]["label"].endswith("／進入") and current_max > LIMITS[
                        joint
                    ] - np.radians(10):
                        selected_shift = min(
                            candidates,
                            key=lambda k: max(
                                abs(joints[:, joint].min() + 2 * np.pi * k), abs(joints[:, joint].max() + 2 * np.pi * k)
                            ),
                        )
                    else:
                        selected_shift = initial_shift
                    shifts[joint] = 2 * np.pi * selected_shift
            joints += shifts
            results.append(
                (
                    1e6 * max_error + collisions + cost + 0.01 * np.linalg.norm(shifts),
                    initial + shifts,
                    error,
                    joints,
                    collisions,
                    max_error,
                    worst_time,
                )
            )
        self.alternatives = sorted(results, key=lambda row: row[0])
        winner = self.alternatives[0]
        self.last_times = times
        self.predictions[side].append((times, winner[3]))
        report = dict(
            phase_index=phase_index,
            side=SIDES[side],
            start_s=float(start),
            stop_s=float(stop),
            branches=len(results),
            collision_score=float(winner[4]),
            maximum_residual=float(winner[5]),
            maximum_residual_author_time=float(winner[6]),
        )
        self.reports.append(report)
        print("OP030_BRANCH_SECTION", report, flush=True)
        return winner[0], winner[1], winner[2]

    def select_alternative(self, index, side):
        """Retain the complete-section prediction for a reachable alternative."""
        winner = self.alternatives[index]
        self.predictions[side][-1] = (self.last_times, winner[3])
        self.reports[-1].update(
            collision_score=float(winner[4]), maximum_residual=float(winner[5]), selected_alternative=index
        )
