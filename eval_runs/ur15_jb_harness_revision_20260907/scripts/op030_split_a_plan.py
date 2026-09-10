# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Select ST A continuous IK branches against the new native triangles [m, rad]."""

import argparse
import hashlib
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import chain_for
from op030_motion import SIDES
from op030_split_support_motion import build_sequence
from op030_split_tools import driver_flange_to_tcp
from scipy.spatial.transform import Rotation
from solve_op030_motion import R, capture_robots


class PlanningContext:
    """Set exact FK poses and persistent actor targets for a collision query."""

    def __init__(self, mesh_file):
        from op030_split_ac_meshes import BranchMeshes

        self.sequence = build_sequence()
        self.screen = BranchMeshes(mesh_file=mesh_file)
        self.robots = capture_robots()
        self.driver_records = json.loads(Path(mesh_file).with_suffix(".json").read_text())["fixed_tools"]

    @lru_cache(maxsize=512)
    def state(self, time):
        seq = self.sequence
        phase = next((p for p in seq.phases if time <= p["stop"] + 1e-8), seq.phases[-1])
        target = seq.evaluate(time)
        held = phase["before"]["holds"].get(1)
        grasp = []
        if held:
            grasp = [held[0]]
        elif "把持" in phase["label"]:
            for number in (1, 2):
                if f"T{number:02d}" in phase["label"]:
                    grasp = [f"OP030_T{number:02d}_UID001"]
        extra = list(grasp) if held else []
        extra.extend(phase["before"]["driven_nuts"])
        return target, phase, tuple(grasp), tuple(extra)

    def query(self, time, joints, *, side=None, hide_other=False, override_free=False):
        target, phase, grasp, extra = self.state(time)
        if hide_other:
            extra = tuple(
                name
                for name in extra
                if (side == 1 and name in grasp) or (side == 0 and name in phase["before"]["driven_nuts"])
            )
        self.screen.set_poses(target["objects"])
        self.screen.set_poses({577: target["root"], 578: target["root"]})
        for arm, name in enumerate(SIDES):
            robot, capture = self.robots[name]
            robot.base_pose = target["root"] @ R.yoke_base_pose(name)
            actual = robot.update(joints[arm], float(target["grips"][arm]))
            poses = capture.poses
            if hide_other and arm != side:
                poses = {key: value.copy() for key, value in poses.items()}
                for value in poses.values():
                    value[2, 3] += 100
            self.screen.set_poses(poses)
            if arm in self.sequence.driver_sizes:
                size = self.sequence.driver_sizes[arm]
                tcp = actual @ driver_flange_to_tcp(size)
                rotation = np.eye(4)
                rotation[:3, :3] = Rotation.from_euler("z", target["spindle_angles"][arm]).as_matrix()
                spindle = tcp @ rotation
                if hide_other and arm != side:
                    spindle[2, 3] += 100
                self.screen.set_poses({self.driver_records["OP030A_" + size]["spindle"]: spindle})
            if override_free and target["free"][arm]:
                goal = target["tools"][arm]
                for uid, (driver, relative) in phase["before"]["driven_nuts"].items():
                    if self.sequence.driver_names.get(arm) == driver:
                        self.screen.set_poses({uid: actual @ np.linalg.inv(goal) @ target["objects"][uid]})
        score = self.screen.score(side, extra_actors=extra, grasp_actors=grasp)
        return score, list(self.screen.last_pairs)


def interpolate_branch(data, section, branch, time):
    times = data[f"section_{section}_times"]
    values = data[branch["array_key"]]
    return np.array([np.interp(time, times, values[:, joint]) for joint in range(6)])


def unique_branches(section, data):
    result = []
    for row in section["branches"]:
        if not row["feasible"]:
            continue
        values = data[row["array_key"]]
        if any(
            np.max(abs(np.sin(values) - np.sin(data[old["array_key"]]))) < 1e-4
            and np.max(abs(np.cos(values) - np.cos(data[old["array_key"]]))) < 1e-4
            for old in result
        ):
            continue
        result.append(row)
    return result


def screen_branches(context, report, data):
    results = []
    for index, section in enumerate(report["sections"]):
        times = data[f"section_{index}_times"]
        arm = section["arm"]
        branches = []
        for row in unique_branches(section, data):
            values = data[row["array_key"]]
            failures = []
            for time, q in zip(times, values, strict=True):
                both = np.zeros((2, 6))
                both[arm] = q
                score, pairs = context.query(float(time), both, side=arm, hide_other=True)
                if score:
                    failures.append(dict(time=float(time), pairs=pairs))
                    # A failed branch cannot be selected. Keep a bounded
                    # sample of evidence without repeating every same hit.
                    if len(failures) >= 3:
                        break
            branches.append(dict(**row, mesh_clear=not failures, mesh_failures=failures))
        entry = dict(
            section=index,
            arm=arm,
            start=section["start"],
            stop=section["stop"],
            branches=branches,
            clear_count=sum(row["mesh_clear"] for row in branches),
        )
        results.append(entry)
        print("SPLIT_A_NATIVE_BRANCH", index, entry["clear_count"], "/", len(branches), flush=True)
    return results


def compatibility(context, sections, data):
    """Screen every overlapping pair of already individually clear branches."""
    records = []
    for left in (section for section in sections if section["arm"] == 0):
        for right in (section for section in sections if section["arm"] == 1):
            begin, end = max(left["start"], right["start"]), min(left["stop"], right["stop"])
            if end < begin:
                continue
            times = np.unique(np.r_[np.arange(begin, end, 0.5), end])
            for a in (branch for branch in left["branches"] if branch["mesh_clear"]):
                for b in (branch for branch in right["branches"] if branch["mesh_clear"]):
                    failure = None
                    for time in times:
                        both = []
                        target = context.sequence.evaluate(time)
                        for arm, section, branch in ((0, left, a), (1, right, b)):
                            seed = interpolate_branch(data, section["section"], branch, time)
                            base = target["root"] @ R.yoke_base_pose(SIDES[arm])
                            q, error = chain_for(tuple(base.ravel())).solve_continuous(target["tools"][arm], seed)
                            if error > 1e-5:
                                raise RuntimeError("Continuous branch interpolation did not recover its target")
                            both.append(q)
                        score, pairs = context.query(float(time), both)
                        if score:
                            failure = dict(time=float(time), pairs=pairs)
                            break
                    records.append(
                        dict(
                            left_section=left["section"],
                            right_section=right["section"],
                            left=a["array_key"],
                            right=b["array_key"],
                            compatible=failure is None,
                            failure=failure,
                        )
                    )
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh_file", default=str(ROOT / "data/op030_split_a_meshes.npz"))
    parser.add_argument("--output", type=Path, default=ROOT / "audit/op030_split_a_native_branches.json")
    args = parser.parse_args()
    context = PlanningContext(args.mesh_file)
    report = json.loads((ROOT / "audit/op030_split_a_branches.json").read_text())
    with np.load(ROOT / "analysis/op030_split_a_branches.npz") as saved:
        data = {key: saved[key].copy() for key in saved.files}
    sections = screen_branches(context, report, data)
    pairs = compatibility(context, sections, data) if all(section["clear_count"] for section in sections) else []
    result = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        mesh_file=args.mesh_file,
        mesh_sha256=hashlib.sha256(Path(args.mesh_file).read_bytes()).hexdigest(),
        sections=sections,
        compatibility=pairs,
        all_sections_have_individually_clear_branch=all(section["clear_count"] for section in sections),
        scope="Native triangle constrained-branch screening; free transits and complete native frames not yet checked",
    )
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("SPLIT_A_NATIVE_BRANCHES_COMPLETE", result["all_sections_have_individually_clear_branch"], flush=True)


if __name__ == "__main__":
    main()
