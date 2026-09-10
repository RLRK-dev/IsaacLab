# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Reuse established timing and audit every C frame against the updated native."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_definition import ROOT
from op030_motion import SIDES
from op030_split_a_replay import Replay as ReplayBase
from op030_split_top_entry_motion import top_entry_c_sequence
from scipy.spatial.transform import Rotation
from solve_op030_motion import LIMITS, NODE_IDS
from split_tools_c_top_entry_plan import PlanningContext


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target_signature(sequence):
    """Digest every phase boundary/midpoint robot constraint, excluding clip geometry."""
    value = hashlib.sha256()
    for phase in sequence.phases:
        value.update(phase["label"].encode())
        for t in (phase["start"], (phase["start"] + phase["stop"]) / 2, phase["stop"]):
            state = sequence.evaluate(t)
            value.update(np.asarray([t], dtype=np.float64).tobytes())
            for key in ("root", "tools", "grips", "free"):
                value.update(np.asarray(state[key]).tobytes())
    return value.hexdigest()


class Replay(ReplayBase):
    """Share the existing constrained/free sampling and stopped path timing."""

    def __init__(self, connected, velocity_cap, acceleration_cap, mesh_file):
        super().__init__(connected, velocity_cap, acceleration_cap)
        self.sequence = top_entry_c_sequence(Path(mesh_file))
        self.authored = np.array([p["start"] for p in self.sequence.phases] + [self.sequence.time])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--connected", type=Path, default=ROOT / "audit/split_tools_c_top_entry_connected.json")
    parser.add_argument(
        "--verification_mesh", type=Path, default=ROOT / "data/op030_split_c_top_entry_clip_v02_meshes.npz"
    )
    parser.add_argument("--output", default="op030_split_c_motion_v03")
    parser.add_argument("--velocity_cap", type=float, default=1.2)
    parser.add_argument("--acceleration_cap", type=float, default=2.0)
    parser.add_argument("--timing_cache", type=Path, default=ROOT / "analysis/split_tools_c_top_entry_timing.npz")
    parser.add_argument("--timing_only", action="store_true")
    args = parser.parse_args()
    if not args.verification_mesh.exists():
        raise FileNotFoundError("Updated clip actual-mesh export is required for final C playback")
    source_names = (
        "split_tools_c_top_entry_replay.py",
        "split_tools_c_top_entry_plan.py",
        "split_tools_c_top_entry_connect.py",
        "op030_split_top_entry_motion.py",
        "op030_split_top_entry.py",
        "op030_split_fastening_motion.py",
        "op030_split_tools.py",
        "op030_split_a_replay.py",
        "op030_split_a_connect.py",
        "op030_split_a_plan.py",
        "op030_fk_fast.py",
        "solve_op030_motion.py",
        "replay_op030_motion.py",
        "op030_split_ac_meshes.py",
    )
    source_hashes = {name: digest(ROOT / "scripts" / name) for name in source_names}
    verification_hashes = {
        str(path): digest(path) for path in (args.verification_mesh, args.verification_mesh.with_suffix(".json"))
    }
    began = datetime.now().astimezone().isoformat()
    replay = Replay(args.connected, args.velocity_cap, args.acceleration_cap, args.verification_mesh)
    signature = target_signature(replay.sequence)
    if args.timing_cache.exists():
        with np.load(args.timing_cache) as cache:
            assert str(cache["connected_sha256"]) == digest(args.connected)
            assert str(cache["target_signature"]) == signature
            assert np.allclose(cache["caps"], [args.velocity_cap, args.acceleration_cap])
            times, author_times, boundaries, joints = [
                cache[key].copy() for key in ("times", "author_times", "boundaries", "joints")
            ]
            timing = json.loads(str(cache["timing"]))
            corrections = json.loads(str(cache["corrections"]))
        print("SPLIT_C_REUSE_TIMING", len(times), flush=True)
    else:
        scales, timing = replay.timing()
        corrections = []
        for attempt in range(2):
            times, author_times, boundaries = replay.retimed(scales)
            joints = np.asarray([replay.sample(t)[0] for t in author_times])
            velocity = np.gradient(joints, times, axis=0, edge_order=2)
            acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
            peak_v, peak_a = float(abs(velocity).max()), float(abs(acceleration).max())
            corrections.append(
                dict(attempt=attempt, frames=len(times), peak_velocity_rad_s=peak_v, peak_acceleration_rad_s2=peak_a)
            )
            print("SPLIT_C_RETIME", attempt, len(times), peak_v, peak_a, flush=True)
            if peak_v <= args.velocity_cap and peak_a <= args.acceleration_cap:
                break
            if attempt == 1:
                raise RuntimeError("Finite playback timing correction did not meet review speed caps")
            scales *= max(1.05 * peak_v / args.velocity_cap, np.sqrt(1.05 * peak_a / args.acceleration_cap), 1.0)
        np.savez_compressed(
            args.timing_cache,
            times=times,
            author_times=author_times,
            boundaries=boundaries,
            joints=joints,
            timing=json.dumps(timing),
            corrections=json.dumps(corrections),
            connected_sha256=digest(args.connected),
            target_signature=signature,
            caps=[args.velocity_cap, args.acceleration_cap],
        )
    if args.timing_only:
        print("SPLIT_C_TIMING_ONLY_COMPLETE", str(args.timing_cache), flush=True)
        return
    velocity = np.gradient(joints, times, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
    context = PlanningContext(args.verification_mesh)
    names = sorted(replay.sequence.objects)
    rows, failures, hits = [], [], []
    for index, (clock, authored, q) in enumerate(zip(times, author_times, joints, strict=True)):
        target, phase, _, _ = context.state(float(authored))
        score, pairs = context.query(float(authored), q, override_free=True)
        free = np.array(
            [
                any(g["arm"] == arm and g["start"] - 1e-9 <= authored <= g["stop"] + 1e-9 for g in replay.free_paths)
                for arm in (0, 1)
            ]
        )
        captures = {577: target["root"], 578: target["root"]}
        objects = {name: matrix.copy() for name, matrix in target["objects"].items()}
        actual, errors = [], []
        for arm, side in enumerate(SIDES):
            robot, capture = context.robots[side]
            matrix = robot.update(q[arm], 0.0)
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
                        arm=arm,
                        position_error_m=position,
                        orientation_error_rad=angle,
                    )
                )
            driver = context.sequence.driver_names[arm]
            calibration = np.asarray(
                context.driver_records["OP030C_" + context.sequence.driver_sizes[arm]]["flange_to_tcp"]
            )
            objects[driver] = matrix @ calibration
            if free[arm]:
                for uid, (owner, _) in phase["before"]["driven_nuts"].items():
                    if owner == driver:
                        objects[uid] = matrix @ np.linalg.inv(goal) @ objects[uid]
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
                clips=[target["clips"][n] for n in (1, 2)],
                poses=[captures[int(node)].copy() for node in NODE_IDS],
                object_poses=[objects[name] for name in names],
            )
        )
        if index % 300 == 0:
            print(
                "SPLIT_C_DENSE_FK_FCL", index, len(times), round(float(clock), 2), len(failures), len(hits), flush=True
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
    verification_unchanged = {path: digest(path) for path in verification_hashes} == verification_hashes
    report = dict(
        observed_at=began,
        completed_at=datetime.now().astimezone().isoformat(),
        candidate=str(output),
        candidate_sha256=digest(output),
        factory="op030_split_top_entry_motion:top_entry_c_sequence",
        connected=str(args.connected),
        connected_sha256=digest(args.connected),
        planning_mesh=replay.record["mesh_file"],
        planning_mesh_sha256=replay.record["mesh_sha256"],
        verification_mesh=str(args.verification_mesh),
        verification_mesh_sha256=digest(args.verification_mesh),
        verification_input_sha256=verification_hashes,
        verification_inputs_unchanged_during_replay=verification_unchanged,
        source_sha256=source_hashes,
        sources_unchanged_during_replay=unchanged,
        frames=len(times),
        fps=30,
        duration_s=float(times[-1]),
        authored_duration_s=float(replay.sequence.time),
        timing_survey=timing,
        timing_corrections=corrections,
        author_boundaries=replay.authored.tolist(),
        display_boundaries=boundaries.tolist(),
        phases=[dict(label=p["label"], start=p["start"], stop=p["stop"]) for p in replay.sequence.phases],
        failures=failures,
        fcl_hits=hits,
        maximum_fk_errors=arrays["errors"].max(axis=(0, 1)).tolist(),
        peak_joint_velocity_rad_s=float(abs(velocity).max()),
        peak_joint_acceleration_rad_s2=float(abs(acceleration).max()),
        max_abs_joint_rad=abs(joints).max(axis=0).tolist(),
        urdf_joint_limits_rad=LIMITS.tolist(),
        measured_seating_contacts=list(context.contact_records.values()),
        identity_scope="Two persistent M6 and two M14 queue UIDs; remaining finite supply retained. "
        "Both installed B wire UIDs remain unchanged.",
        logical_driver_object_scope="Driver object poses are actual socket TCP; native driver roots stay parented "
        "to actual FK tool0. Spindle angles are separate native local rotations.",
        fcl_scope="Every saved30Hz original FK frame against updated native triangles, with measured actual "
        "washer seating interfaces only. Static clip construction is separately reviewed. No force/torque result.",
        formal_physical_validity_verdict=None,
    )
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    print("SPLIT_C_REPLAY_COMPLETE", len(times), len(failures), len(hits), str(output), flush=True)
    assert unchanged, "Replay sources changed while generating C bank"
    assert verification_unchanged, "Verification geometry or calibration changed while generating C bank"
    assert not failures and not hits, "C bank has unresolved FK or actual-mesh intersections"


if __name__ == "__main__":
    main()
