# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Replay accepted paths with dense FK and explicit review speed limits [m, rad, s]."""

import argparse
import hashlib
import json
from datetime import datetime

import numpy as np
from direct_cable import basis
from op020_jb_motion import weight
from op030_cable import coefficients, flatten_basis
from op030_definition import ROOT, lug_frame, wire_route
from op030_motion import SIDES, build_sequence, evaluate_phase, transit_actors
from scipy.spatial.transform import Rotation
from solve_op030_motion import LIMITS, NODE_IDS, R, capture_robots, continuous_pose


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_timing(waypoints, velocity_cap, acceleration_cap):
    """Allocate time to each stopped quintic segment [s]."""
    delta = np.max(abs(np.diff(waypoints, axis=0)), axis=1)
    durations = 1.10 * np.maximum(1.875 * delta / velocity_cap, np.sqrt(10 / np.sqrt(3) * delta / acceleration_cap))
    return np.r_[0.0, np.cumsum(np.maximum(durations, 2 / 30))]


def path_sample(waypoints, knots, u):
    """Reuse the exact screened joint polyline, stopping at every corner [rad]."""
    clock = np.clip(u, 0.0, 1.0) * knots[-1]
    index = max(0, min(len(waypoints) - 2, int(np.searchsorted(knots, clock, side="right")) - 1))
    local = np.clip((clock - knots[index]) / (knots[index + 1] - knots[index]), 0, 1)
    local = local**3 * (10 - 15 * local + 6 * local * local)
    return waypoints[index] * (1 - local) + waypoints[index + 1] * local


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--retime", action="store_true")
    parser.add_argument("--timing_reference", help="Dense earlier timing measurements; only increase phase durations")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--velocity_cap", type=float, default=1.2)
    parser.add_argument("--acceleration_cap", type=float, default=2.0)
    args = parser.parse_args()
    began = datetime.now().astimezone().isoformat()
    source_paths = [
        ROOT / "scripts" / name
        for name in (
            "replay_op030_motion.py",
            "solve_op030_motion.py",
            "op030_motion.py",
            "op030_definition.py",
            "op030_cable.py",
            "op030_fk_fast.py",
        )
    ]
    source_paths.append(ROOT / "data/op030_tool_paths_v02.json")
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    reference_path = ROOT / "data" / args.reference
    previous = json.loads((ROOT / "audit" / (reference_path.stem + ".json")).read_text())
    if not args.diagnostic:
        assert not previous["failures"], "The reference contains unresolved paths"
        assert all(p["maximum_residual"] < 1e-5 for p in previous.get("branch_sections", []))
        actual_screen = json.loads((ROOT / "audit" / (reference_path.stem + "_fcl_inspection.json")).read_text())
        assert actual_screen["candidate_sha256"] == digest(reference_path)
        assert actual_screen["mesh_export_sha256"] == previous["provenance"]["mesh_export"]["output_sha256"]
        assert not actual_screen["hits"], "Actual saved poses or carried tools still intersect"
        # A branch preference can reference the other arm's previous candidate.
        # Gate on the complete current trajectory, not that superseded forecast.
    with np.load(reference_path) as saved:
        reference = {k: saved[k].copy() for k in saved.files}
    # These are visualization caps below the retained URDF velocity limits;
    # acceleration/torque limits of a selected controller are not represented.
    assert 0 < args.velocity_cap <= np.pi and args.acceleration_cap > 0
    sequence = build_sequence()
    if not args.diagnostic:
        for path in (
            "scripts/op030_motion.py",
            "scripts/op030_definition.py",
            "scripts/op030_cable.py",
            "data/op030_tool_paths_v02.json",
        ):
            assert previous["provenance"]["sources"][path] == source_hashes[path], (
                "Motion definition changed after reference generation: " + path
            )
    authored = np.array([p["start"] for p in sequence.phases] + [sequence.time])
    assert len(previous["phases"]) == len(sequence.phases)
    assert [p["label"] for p in previous["phases"]] == [p["label"] for p in sequence.phases]
    assert np.allclose(authored, [p["start"] for p in previous["phases"]] + [previous["phases"][-1]["stop"]], atol=1e-7)
    reference_author = reference.get("author_times", reference["times"])
    assert abs(reference_author[-1] - sequence.time) < 1e-7, "Reference is only a partial sequence"
    scales = np.ones(len(sequence.phases))
    if args.retime:
        unique = np.r_[True, np.diff(reference["times"]) > 1e-7]
        rt, rq = reference["times"][unique], reference["joints"][unique]
        velocity = np.gradient(rq, rt, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, rt, axis=0, edge_order=2)
        ra = reference_author[unique]
        for i, phase in enumerate(sequence.phases):
            selected = (ra >= phase["start"] - 1e-7) & (ra <= phase["stop"] + 1e-7)
            peak_v = float(np.max(abs(velocity[selected])))
            peak_a = float(np.max(abs(acceleration[selected])))
            old_duration = np.interp(phase["stop"], ra, rt) - np.interp(phase["start"], ra, rt)
            scales[i] = (
                old_duration
                / (phase["stop"] - phase["start"])
                * max(1.0, 1.25 * peak_v / args.velocity_cap, np.sqrt(1.25 * peak_a / args.acceleration_cap))
            )
    display = np.r_[0, np.cumsum(np.diff(authored) * scales)]
    timing_reference_sha = None
    if args.timing_reference:
        assert args.retime
        timing_path = ROOT / "data" / args.timing_reference
        timing_meta = json.loads((ROOT / "audit" / (timing_path.stem + ".json")).read_text())
        assert [p["label"] for p in timing_meta["phases"]] == [p["label"] for p in sequence.phases]
        with np.load(timing_path) as timing:
            rt, ra, rq = timing["times"], timing.get("author_times", timing["times"]), timing["joints"]
            velocity = np.gradient(rq, rt, axis=0, edge_order=2)
            acceleration = np.gradient(velocity, rt, axis=0, edge_order=2)
            for index, phase in enumerate(sequence.phases):
                selected = (ra >= phase["start"] - 1e-7) & (ra <= phase["stop"] + 1e-7)
                peak_v, peak_a = float(abs(velocity[selected]).max()), float(abs(acceleration[selected]).max())
                ratio = (np.interp(phase["stop"], ra, rt) - np.interp(phase["start"], ra, rt)) / (
                    phase["stop"] - phase["start"]
                )
                measured = ratio * max(
                    1.0, 1.08 * peak_v / args.velocity_cap, np.sqrt(1.08 * peak_a / args.acceleration_cap)
                )
                scales[index] = max(scales[index], measured)
        timing_reference_sha = digest(timing_path)
        display = np.r_[0, np.cumsum(np.diff(authored) * scales)]
    free_paths = {
        (p["phase_index"], SIDES.index(p["side"])): np.array(p["waypoints"]) for p in previous["free_joint_paths"]
    }
    path_knots = {
        key: path_timing(points, args.velocity_cap, args.acceleration_cap) for key, points in free_paths.items()
    }
    for (phase_index, side), knots in path_knots.items():
        scales[phase_index] = max(scales[phase_index], knots[-1] / np.diff(authored)[phase_index])
    display = np.r_[0, np.cumsum(np.diff(authored) * scales)]
    # A whole video frame is retained at the final state.
    duration = np.ceil(display[-1] * 30) / 30
    times = np.arange(int(round(duration * 30)) + 1) / 30
    author_times = np.interp(times, display, authored)
    robots = capture_robots()
    seed = reference["joints"][0].copy()
    names = sorted(sequence.objects)
    rows, failures, phase_index = [], [], 0
    for i, (clock, t) in enumerate(zip(times, author_times, strict=True)):
        while phase_index + 1 < len(sequence.phases) and t > sequence.phases[phase_index]["stop"] + 1e-7:
            phase_index += 1
        phase = sequence.phases[phase_index]
        target = evaluate_phase(phase, t)
        captures, joints, tools, errors, actual_errors, free_flags = {}, [], [], [], [], []
        for side, name in enumerate(SIDES):
            base = target["root"] @ R.yoke_base_pose(name)
            goal = target["tools"][side]
            free = (phase_index, side) in free_paths
            if free:
                u = np.clip((t - phase["start"]) / (phase["stop"] - phase["start"]), 0, 1)
                q = path_sample(free_paths[phase_index, side], path_knots[phase_index, side], u)
                residual = 0.0
            else:
                if i == 0:
                    seed[side] = np.array(
                        [np.interp(t, reference_author, reference["joints"][:, side, k]) for k in range(6)]
                    )
                q, residual = continuous_pose(base, goal[:3, 3], seed[side], orientation=goal[:3, :3])
            robot, capture = robots[name]
            robot.base_pose = base
            actual = robot.update(q, float(target["grips"][side]))
            if free:
                correction = actual @ np.linalg.inv(goal)
                for actor in transit_actors(phase, side):
                    target["objects"][actor] = correction @ target["objects"][actor]
            pe = float(np.linalg.norm(actual[:3, 3] - goal[:3, 3]))
            re = float(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ goal[:3, :3].T).as_rotvec()))
            actual_errors.append([pe, re])
            if free:
                pe, re = 0.0, 0.0
            if max(pe, re) > 1e-5 or np.any(abs(q) > LIMITS + 1e-7):
                failures.append(
                    dict(
                        time=float(clock),
                        author_time=float(t),
                        side=name,
                        phase=phase["label"],
                        position_error_m=pe,
                        rotation_error_rad=re,
                    )
                )
            if i and not free and np.max(abs(q - seed[side])) > 1.0:
                failures.append(
                    dict(
                        time=float(clock),
                        author_time=float(t),
                        side=name,
                        phase=phase["label"],
                        error="Large joint discontinuity during Cartesian motion",
                        joint_delta_rad=(q - seed[side]).tolist(),
                    )
                )
            seed[side] = q
            joints.append(q)
            tools.append(actual)
            errors.append([pe, re])
            free_flags.append(free)
            captures.update(capture.poses)
        captures.update({577: target["root"], 578: target["root"]})
        spins = [
            sum(
                p["spin"]["radians"] * weight(t, p["start"], p["stop"])
                for p in sequence.phases
                if p["spin"] and p["spin"]["tool"] == "OP030_driver_" + size and t >= p["start"]
            )
            for size in ("M4", "M6", "M14")
        ]
        row = dict(
            joints=joints,
            tools=tools,
            errors=errors,
            actual_cartesian_errors=actual_errors,
            free_joint_motion=free_flags,
            grips=target["grips"],
            spindle_angles=spins,
            poses=[captures[int(node)] for node in NODE_IDS],
            object_poses=[target["objects"][name] for name in names],
        )
        for number in (1, 2):
            root_name = f"OP030_H03_{number}_UID001"
            row[f"wire_coefficients_{number}"] = coefficients(
                wire_route(number),
                target["objects"][root_name],
                target["objects"][root_name + "_T"],
                lug_frame(number, "T"),
            )
        rows.append(row)
        if i % 300 == 0:
            print("OP030_DENSE_REPLAY", round(clock, 2), round(t, 2), len(failures), flush=True)
    arrays = {key: np.asarray([row[key] for row in rows]) for key in rows[0]}
    for number in (1, 2):
        arrays[f"wire_points_{number}"] = wire_route(number)
        arrays[f"wire_masks_{number}"] = basis(wire_route(number))
        arrays[f"wire_flatten_{number}"] = flatten_basis(wire_route(number))
    velocity = np.gradient(arrays["joints"], times, axis=0, edge_order=2)
    acceleration = np.gradient(velocity, times, axis=0, edge_order=2)
    np.savez_compressed(
        ROOT / "data" / (args.output + ".npz"),
        times=times,
        author_times=author_times,
        frames=np.arange(len(times)) + 1,
        node_ids=NODE_IDS,
        object_names=names,
        **arrays,
    )
    provenance = dict(previous["provenance"])
    provenance.update(started_at=began, replay_reference_sha256=digest(reference_path))
    if timing_reference_sha:
        provenance["timing_reference_sha256"] = timing_reference_sha
    assert source_hashes == {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    provenance["sources"] = source_hashes
    report = dict(
        failures=failures,
        samples=len(times),
        duration_s=float(duration),
        phases=previous["phases"],
        free_joint_paths=previous["free_joint_paths"],
        provenance=provenance,
        max_errors=arrays["errors"].max(axis=(0, 1)).tolist(),
        max_joint_abs_rad=abs(arrays["joints"]).max(axis=0).tolist(),
        peak_joint_velocity_rad_s=abs(velocity).max(axis=0).tolist(),
        peak_joint_acceleration_rad_s2=abs(acceleration).max(axis=0).tolist(),
        review_caps=dict(velocity_rad_s=args.velocity_cap, acceleration_rad_s2=args.acceleration_cap),
        retimed=args.retime,
        author_boundaries=authored.tolist(),
        display_boundaries=display.tolist(),
        geometry_and_dynamics_not_validated=True,
    )
    (ROOT / "audit" / (args.output + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "OP030_DENSE_COMPLETE",
        len(times),
        len(failures),
        float(abs(velocity).max()),
        float(abs(acceleration).max()),
        flush=True,
    )
    assert not failures


if __name__ == "__main__":
    main()
