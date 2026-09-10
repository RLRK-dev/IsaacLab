# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Retime split ST A and inspect every original-FK frame against actual meshes [m, rad, s]."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_fk_fast import chain_for
from op030_motion import SIDES
from op030_split_a_plan import PlanningContext
from op030_split_support_motion import build_sequence
from op030_split_tools import driver_flange_to_tcp
from replay_op030_motion import path_sample, path_timing
from scipy.spatial.transform import Rotation
from solve_op030_motion import LIMITS, NODE_IDS, R


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Replay:
    """Follow the accepted constrained branches and exact free polylines [m, rad, s]."""

    def __init__(self, connected, velocity_cap, acceleration_cap):
        self.connected_file = Path(connected)
        self.record = json.loads(self.connected_file.read_text())
        assert self.record["connected"]
        assert digest(self.record["branch_report"]) == self.record["branch_report_sha256"]
        assert digest(self.record["mesh_file"]) == self.record["mesh_sha256"]
        self.branch_report = json.loads(Path(self.record["branch_report"]).read_text())
        self.section_rows = self.branch_report["sections"]
        self.data_file = ROOT / "analysis" / (self.connected_file.stem + ".npz")
        with np.load(self.data_file) as saved:
            self.data = {key: saved[key].copy() for key in saved.files}
        self.sequence = build_sequence()
        self.free_paths = [dict(row) for row in self.record["free_paths"]]
        for row in self.free_paths:
            row["path"] = np.asarray(row["path"])
            row["knots"] = path_timing(row["path"], velocity_cap, acceleration_cap)
        self.velocity_cap, self.acceleration_cap = velocity_cap, acceleration_cap
        self.authored = np.array([phase["start"] for phase in self.sequence.phases] + [self.sequence.time])

    def sample(self, time):
        """Solve exact constrained TCPs; sample only screened free joint segments [m, rad, s]."""
        target = self.sequence.evaluate(float(time))
        joints, errors, free = [], [], []
        for arm, name in enumerate(SIDES):
            group = next(
                (
                    row
                    for row in self.free_paths
                    if row["arm"] == arm and row["start"] - 1e-9 <= time <= row["stop"] + 1e-9
                ),
                None,
            )
            if group:
                u = np.clip((time - group["start"]) / (group["stop"] - group["start"]), 0, 1)
                q = path_sample(group["path"], group["knots"], u)
                error = 0.0
            else:
                section = next(
                    row
                    for row in self.section_rows
                    if row["arm"] == arm and row["start"] - 1e-7 <= time <= row["stop"] + 1e-7
                )
                key = section["section"]
                stamps = self.data[f"section_{key}_times"]
                values = self.data[f"section_{key}_joints"]
                seed = np.array([np.interp(time, stamps, values[:, joint]) for joint in range(6)])
                base = target["root"] @ R.yoke_base_pose(name)
                q, error = chain_for(tuple(base.ravel())).solve_continuous(target["tools"][arm], seed)
            joints.append(q)
            errors.append(error)
            free.append(group is not None)
        return np.asarray(joints), np.asarray(errors), np.asarray(free), target

    def timing(self):
        """Allocate per-phase time from a dense author-time derivative survey [s]."""
        stamps = np.unique(np.round(np.r_[np.arange(0, self.sequence.time, 1 / 30), self.authored], 9))
        values, residuals = [], []
        for index, stamp in enumerate(stamps):
            joints, errors, _, _ = self.sample(stamp)
            values.append(joints)
            residuals.append(errors)
            if index % 600 == 0:
                print("SPLIT_A_TIMING_SURVEY", index, len(stamps), float(stamp), flush=True)
        values = np.asarray(values)
        assert np.max(residuals) < 1e-5, "A dense constrained target has no local IK solution"
        assert np.all(abs(values) <= LIMITS + 1e-7), "Dense timing survey exceeds retained URDF limits"
        velocity = np.gradient(values, stamps, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, stamps, axis=0, edge_order=2)
        scales = np.ones(len(self.authored) - 1)
        for index, phase in enumerate(self.sequence.phases):
            use = (stamps >= phase["start"] - 1e-8) & (stamps <= phase["stop"] + 1e-8)
            scales[index] = max(
                1.0,
                1.25 * abs(velocity[use]).max() / self.velocity_cap,
                np.sqrt(1.25 * abs(acceleration[use]).max() / self.acceleration_cap),
            )
        for group in self.free_paths:
            scale = max(
                max(scales[group["phases"]]),
                group["knots"][-1] / (group["stop"] - group["start"]),
            )
            scales[group["phases"]] = scale
        return scales, dict(
            samples=len(stamps),
            maximum_ik_residual=float(np.max(residuals)),
            peak_author_joint_velocity_rad_s=float(abs(velocity).max()),
            peak_author_joint_acceleration_rad_s2=float(abs(acceleration).max()),
            stopped_free_path_timing="Existing replay_op030_motion.path_timing/path_sample",
        )

    def retimed(self, scales):
        """Return exact 30 fps display times and their author-time map [s]."""
        boundaries = np.r_[0.0, np.cumsum(np.diff(self.authored) * scales)]
        duration = np.ceil(boundaries[-1] * 30) / 30
        stamps = np.arange(int(round(duration * 30)) + 1) / 30
        authored = np.interp(stamps, boundaries, self.authored)
        return stamps, authored, boundaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--connected", type=Path, default=ROOT / "audit/op030_split_a_integrated_connected.json")
    parser.add_argument("--output", default="op030_split_a_motion_v03")
    parser.add_argument("--velocity_cap", type=float, default=1.2)
    parser.add_argument("--acceleration_cap", type=float, default=2.0)
    args = parser.parse_args()
    assert 0 < args.velocity_cap <= np.pi and args.acceleration_cap > 0
    began = datetime.now().astimezone().isoformat()
    source_names = (
        "op030_split_a_replay.py",
        "op030_split_a_plan.py",
        "op030_split_a_connect.py",
        "op030_split_support_motion.py",
        "op030_split_fastening_motion.py",
        "op030_split_tools.py",
        "op030_fk_fast.py",
        "solve_op030_motion.py",
        "replay_op030_motion.py",
        "op030_split_ac_meshes.py",
    )
    source_hashes = {name: digest(ROOT / "scripts" / name) for name in source_names}
    replay = Replay(args.connected, args.velocity_cap, args.acceleration_cap)
    scales, timing = replay.timing()
    # One preliminary dense playback can only enlarge the existing timing.
    # This finite correction addresses the sampled derivative at phase joins.
    retiming_records = []
    for attempt in range(2):
        times, author_times, boundaries = replay.retimed(scales)
        joints = np.asarray([replay.sample(time)[0] for time in author_times])
        velocity = np.gradient(joints, times, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
        peak_v, peak_a = float(abs(velocity).max()), float(abs(acceleration).max())
        retiming_records.append(
            dict(attempt=attempt, samples=len(times), peak_velocity_rad_s=peak_v, peak_acceleration_rad_s2=peak_a)
        )
        print("SPLIT_A_RETIME", attempt, len(times), peak_v, peak_a, flush=True)
        if peak_v <= args.velocity_cap and peak_a <= args.acceleration_cap:
            break
        if attempt == 1:
            raise RuntimeError("A review speed caps remain exceeded after one finite timing correction")
        scales *= max(1.05 * peak_v / args.velocity_cap, np.sqrt(1.05 * peak_a / args.acceleration_cap), 1.0)

    context = PlanningContext(replay.record["mesh_file"])
    names = sorted(replay.sequence.objects)
    rows, failures, hits = [], [], []
    for index, (clock, authored, q) in enumerate(zip(times, author_times, joints, strict=True)):
        target, phase, _, _ = context.state(float(authored))
        score, pairs = context.query(float(authored), q, override_free=True)
        free = np.array(
            [
                any(
                    group["arm"] == arm and group["start"] - 1e-9 <= authored <= group["stop"] + 1e-9
                    for group in replay.free_paths
                )
                for arm in (0, 1)
            ]
        )
        actual, captures, errors = [], {577: target["root"], 578: target["root"]}, []
        objects = {name: matrix.copy() for name, matrix in target["objects"].items()}
        for arm, side in enumerate(SIDES):
            robot, capture = context.robots[side]
            matrix = robot.update(q[arm], float(target["grips"][arm]))
            captures.update(capture.poses)
            actual.append(matrix.copy())
            goal = target["tools"][arm]
            position = float(np.linalg.norm(matrix[:3, 3] - goal[:3, 3]))
            angle = float(np.linalg.norm(Rotation.from_matrix(matrix[:3, :3] @ goal[:3, :3].T).as_rotvec()))
            errors.append([0.0, 0.0] if free[arm] else [position, angle])
            if not free[arm] and max(position, angle) > 1e-5:
                failures.append(
                    dict(
                        frame=index + 1,
                        time_s=float(clock),
                        author_time_s=float(authored),
                        arm=arm,
                        position_error_m=position,
                        orientation_error_rad=angle,
                    )
                )
            if arm in context.sequence.driver_sizes:
                driver = context.sequence.driver_names[arm]
                objects[driver] = matrix @ driver_flange_to_tcp(context.sequence.driver_sizes[arm])
                if free[arm]:
                    correction = matrix @ np.linalg.inv(goal)
                    for uid, (owner, _) in phase["before"]["driven_nuts"].items():
                        if owner == driver:
                            objects[uid] = correction @ objects[uid]
        if score:
            hits.append(
                dict(
                    frame=index + 1,
                    time_s=float(clock),
                    author_time_s=float(authored),
                    phase=phase["label"],
                    pairs=pairs,
                )
            )
        rows.append(
            dict(
                tools=actual,
                grips=target["grips"],
                errors=errors,
                free_joint_motion=free,
                spindle_angles=target["spindle_angles"],
                poses=[captures[int(node)].copy() for node in NODE_IDS],
                object_poses=[objects[name] for name in names],
            )
        )
        if index % 300 == 0:
            print(
                "SPLIT_A_DENSE_FK_FCL", index, len(times), round(float(clock), 2), len(failures), len(hits), flush=True
            )
    arrays = {key: np.asarray([row[key] for row in rows]) for key in rows[0]}
    output = ROOT / "data" / (args.output + ".npz")
    np.savez_compressed(
        output,
        times=times,
        author_times=author_times,
        frames=np.arange(len(times)) + 1,
        joints=joints,
        node_ids=NODE_IDS,
        object_names=names,
        **arrays,
    )
    unchanged = {name: digest(ROOT / "scripts" / name) for name in source_names} == source_hashes
    report = dict(
        observed_at=began,
        completed_at=datetime.now().astimezone().isoformat(),
        candidate=str(output),
        candidate_sha256=digest(output),
        connected=str(args.connected),
        connected_sha256=digest(args.connected),
        mesh_file=replay.record["mesh_file"],
        mesh_sha256=replay.record["mesh_sha256"],
        source_sha256=source_hashes,
        sources_unchanged_during_replay=unchanged,
        frames=len(times),
        fps=30,
        duration_s=float(times[-1]),
        authored_duration_s=float(replay.sequence.time),
        timing_survey=timing,
        timing_corrections=retiming_records,
        author_boundaries=replay.authored.tolist(),
        display_boundaries=boundaries.tolist(),
        phases=[
            dict(label=phase["label"], start=phase["start"], stop=phase["stop"]) for phase in replay.sequence.phases
        ],
        failures=failures,
        fcl_hits=hits,
        maximum_fk_errors=arrays["errors"].max(axis=(0, 1)).tolist(),
        peak_joint_velocity_rad_s=float(abs(velocity).max()),
        peak_joint_acceleration_rad_s2=float(abs(acceleration).max()),
        review_caps=dict(velocity_rad_s=args.velocity_cap, acceleration_rad_s2=args.acceleration_cap),
        max_abs_joint_rad=abs(joints).max(axis=0).tolist(),
        urdf_joint_limits_rad=LIMITS.tolist(),
        logical_driver_object_scope=(
            "OP030A_driver_M4 object poses denote actual socket TCP, not the native flange-parented root pose."
        ),
        identity_scope=(
            "Same 20 support UIDs, two installed supports, four original M4 queue UIDs, remaining eight bolts retained."
        ),
        fcl_scope=(
            "Every saved original-FK frame. Exact held-support/right precision-tip interface exceptions only, "
            "same rigid actors and adjacent robot links excluded. "
            "Surface intersections are auxiliary geometric observations."
        ),
        formal_physical_validity_verdict=None,
    )
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("SPLIT_A_REPLAY_COMPLETE", len(times), len(failures), len(hits), str(output), flush=True)
    assert unchanged, "A replay source file changed while generating the saved trajectory"
    assert not failures and not hits, "A saved replay has unresolved FK or actual-mesh intersections"


if __name__ == "__main__":
    main()
