# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Solve OP030 with the unchanged UR15 FK/IK and actual gripper geometry [m, rad]."""

import argparse
import hashlib
import json
from datetime import datetime
from functools import lru_cache

import numpy as np
from direct_cable import basis
from op020_jb_motion import original
from op030_cable import coefficients, flatten_basis
from op030_definition import CX, CY, ROOT, lug_frame, wire_route
from op030_motion import SIDES, build_sequence, evaluate_phase, is_joint_transit, transit_actors
from scipy.spatial.transform import Rotation

R = original.R
NODE_IDS = np.array([577, 578, *range(1046, 1084), *range(1086, 1124)])
LIMITS = np.radians([360, 360, 180, 360, 360, 360])


def bounded_pose(base, position, seed, *, orientation):
    """Reuse the original FK/residual, adding the existing URDF joint bounds [rad]."""
    start = np.array(seed, dtype=float)
    outside = abs(start) >= LIMITS - 1e-6
    start[outside] = np.arctan2(np.sin(start[outside]), np.cos(start[outside]))
    start = np.clip(start, -LIMITS + 1e-6, LIMITS - 1e-6)

    from op030_fk_fast import chain_for

    target = np.eye(4)
    target[:3, :3], target[:3, 3] = orientation, position
    return chain_for(tuple(base.ravel())).solve(target, start, max_nfev=None)


def nearest_turn(q, seed):
    """Keep equivalent angle representatives near the preceding sample [rad]."""
    close = seed + np.arctan2(np.sin(q - seed), np.cos(q - seed))
    use = np.abs(close) < LIMITS - 1e-6
    return np.where(use, close, q)


def continuous_pose(base, position, seed, *, orientation):
    """Follow one local branch; the complete section is then checked against limits."""
    from op030_fk_fast import chain_for

    target = np.eye(4)
    target[:3, :3], target[:3, 3] = orientation, position
    return chain_for(tuple(base.ravel())).solve_continuous(target, seed)


@lru_cache(maxsize=1)
def capture_robots():
    """Reuse the original URDF FK and this station's unmodified visual offsets."""
    source = ROOT / "inputs/v02_source/inputs/v01_source"
    scene = json.loads((source / "data/scene_with_controllers.json").read_text())
    with np.load(source / "data/motion_with_camera_clearance.npz") as saved:
        initial = saved["poses"][0].copy()
    result = {}
    for side in SIDES:
        capture = original.PoseCapture()
        robot = R.UR15.__new__(R.UR15)
        robot.scene = capture
        robot.base_pose = R.cell_root(2, 0) @ R.yoke_base_pose(side)
        q, _ = R.motion_at(0, side, 2)
        links, _ = R.UR15.forward(robot.base_pose, q)
        robot.visuals, robot.gripper_visuals = [], []
        for node in scene["nodes"]:
            if node["equipment"] != "robot_OP030_" + side:
                continue
            prefix, _, name = node["name"].partition(":")
            if prefix == "2f85":
                robot.gripper_visuals.append(R.RobotVisual(node["id"], name, np.eye(4)))
            elif prefix in links:
                local = np.linalg.inv(links[prefix]) @ initial[node["id"]]
                robot.visuals.append(R.RobotVisual(node["id"], prefix, local))
        result[side] = robot, capture
    return result


def torso_penalty(base, q):
    """Auxiliary branch preference; final collision screen uses complete meshes."""
    links, _ = R.UR15.forward(base, q)
    centers = [links[name][:3, 3] for name in ("upper_arm", "forearm", "wrist_1", "wrist_2", "wrist_3")]
    points = np.vstack([np.linspace(a, b, 8) for a, b in zip(centers[:-1], centers[1:], strict=True)])
    radial = np.linalg.norm(points[:, :2] - [CX, CY], axis=1)
    active = (points[:, 2] > 0.50) & (points[:, 2] < 1.8)
    return float(np.maximum(0.28 - radial[active], 0).sum()) * 100


def main():  # noqa: C901 -- Preserve the archived authoring routine in this source checkpoint.
    parser = argparse.ArgumentParser()
    parser.add_argument("--step_s", type=float, default=0.5)
    parser.add_argument("--output", default="op030_motion_probe_v02")
    parser.add_argument("--stop_s", type=float)
    parser.add_argument("--skip_cables", action="store_true")
    parser.add_argument("--branch_boxes", action="store_true")
    parser.add_argument("--plan_free_paths", action="store_true")
    parser.add_argument("--branch_meshes", action="store_true")
    parser.add_argument("--reference_motion")
    args = parser.parse_args()
    source_paths = [
        ROOT / "scripts" / name
        for name in (
            "solve_op030_motion.py",
            "op030_motion.py",
            "op030_definition.py",
            "op030_cable.py",
            "op030_branch_choice.py",
            "op030_branch_meshes.py",
            "op030_free_paths.py",
            "op030_fk_fast.py",
        )
    ]
    source_paths.append(ROOT / "data/op030_tool_paths_v02.json")
    provenance = dict(
        started_at=datetime.now().astimezone().isoformat(),
        sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
    )
    if args.branch_meshes:
        provenance["mesh_export"] = json.loads((ROOT / "audit/op030_branch_meshes_export.json").read_text())
        assert (
            hashlib.sha256((ROOT / "data/op030_branch_meshes.npz").read_bytes()).hexdigest()
            == provenance["mesh_export"]["output_sha256"]
        )
    sequence = build_sequence()
    duration = min(sequence.time, args.stop_s or sequence.time)
    times = np.unique(
        np.round(
            np.r_[
                np.arange(0, duration, args.step_s),
                duration,
                [p["start"] for p in sequence.phases if p["start"] <= duration],
                [p["stop"] for p in sequence.phases if p["stop"] <= duration],
            ],
            9,
        )
    )
    robots = capture_robots()
    screen = None
    if args.branch_meshes:
        from op030_branch_meshes import BranchMeshes

        screen = BranchMeshes()
    elif args.branch_boxes:
        from op030_branch_boxes import BranchBoxes

        screen = BranchBoxes()
    choice = None
    if args.reference_motion:
        assert screen is not None
        from op030_branch_choice import BranchChoice

        choice = BranchChoice(sequence, screen, robots, ROOT / "data" / args.reference_motion, R, continuous_pose)
    seed = np.array([R.motion_at(0, side, 2)[0] for side in SIDES])
    rng = np.random.default_rng(830)
    names = sorted(sequence.objects)
    phase_index = 0
    bad, rows = [], []
    free_phases = {}
    home_joints = None
    for i, t in enumerate(times):
        while phase_index + 1 < len(sequence.phases) and t > sequence.phases[phase_index]["stop"] + 1e-7:
            phase_index += 1
        phase = sequence.phases[phase_index]
        target = evaluate_phase(phase, t)
        q_rows, errors, tools, captures = [], [], [], {}
        actual_errors, free_flags = [], []
        if screen:
            screen.set_poses(target["objects"])
            screen.set_poses({576: screen.fixed_base, 577: target["root"], 578: target["root"]})
            for j, side in enumerate(SIDES):
                robots[side][0].base_pose = target["root"] @ R.yoke_base_pose(side)
                robots[side][0].update(seed[j], float(target["grips"][j]))
                screen.set_poses(robots[side][1].poses)
        for j, side in enumerate(SIDES):
            base = target["root"] @ R.yoke_base_pose(side)
            goal = target["tools"][j]
            free = is_joint_transit(phase, j)
            carried = transit_actors(phase, j) if free else ()
            held_relative = {name: np.linalg.inv(goal) @ target["objects"][name] for name in carried}

            def branch_cost(candidate):
                if screen is None:
                    return torso_penalty(base, candidate)
                robot, capture = robots[side]
                robot.base_pose = base
                actual = robot.update(candidate, float(target["grips"][j]))
                screen.set_poses(capture.poses)
                if carried:
                    screen.set_poses({name: actual @ relative for name, relative in held_relative.items()})
                return screen.score(j, carried) if carried else screen.score(j)

            predicted = choice.prediction(j, t) if choice and not free else None
            if i and not free:
                q, residual = continuous_pose(
                    base, goal[:3, 3], seed[j] if predicted is None else predicted, orientation=goal[:3, :3]
                )
            else:
                q, residual = bounded_pose(base, goal[:3, 3], seed[j], orientation=goal[:3, :3])
            if i == 0 or (free and residual > 1e-5):
                candidates = []
                for start in [seed[j], *rng.uniform(-np.pi, np.pi, (18, 6))]:
                    alt, err = bounded_pose(base, goal[:3, 3], start, orientation=goal[:3, :3])
                    alt = np.arctan2(np.sin(alt), np.cos(alt))
                    alt = nearest_turn(alt, seed[j])
                    if err < 1e-6:
                        cost = branch_cost(alt) + 0.01 * np.linalg.norm(alt - seed[j])
                        candidates.append((cost, alt, err))
                if candidates:
                    _, q, residual = min(candidates, key=lambda row: row[0])
            if free:
                key = (phase_index, j)
                if key not in free_phases:
                    final = evaluate_phase(phase, phase["stop"])["tools"][j]
                    options = []
                    for start in [seed[j], q, *rng.uniform(-np.pi, np.pi, (14, 6))]:
                        candidate, candidate_error = bounded_pose(base, final[:3, 3], start, orientation=final[:3, :3])
                        candidate = np.arctan2(np.sin(candidate), np.cos(candidate))
                        candidate = nearest_turn(candidate, seed[j])
                        if candidate_error < 1e-6:
                            cost = branch_cost(candidate) + 0.01 * np.linalg.norm(candidate - seed[j])
                            options.append((cost, candidate, candidate_error))
                    if phase["label"] == side + "／退避" and home_joints is not None:
                        # Return to the jointly clear pair established at frame
                        # one; independent IK branches for the same hand poses
                        # can put one parked elbow into the other parked arm.
                        candidate = nearest_turn(home_joints[j], seed[j])
                        _, actual_home = R.UR15.forward(base, candidate)
                        assert np.allclose(actual_home, final, atol=1e-6)
                        options = [(branch_cost(candidate), candidate, 0.0)]
                    if options:
                        if choice:
                            _, endpoint, err = choice.pick(phase_index, j, options)
                            screen.set_poses(target["objects"])
                            screen.set_poses({576: screen.fixed_base, 577: target["root"], 578: target["root"]})
                            for arm, arm_side in enumerate(SIDES):
                                robots[arm_side][0].base_pose = target["root"] @ R.yoke_base_pose(arm_side)
                                robots[arm_side][0].update(seed[arm], float(target["grips"][arm]))
                                screen.set_poses(robots[arm_side][1].poses)
                        else:
                            _, endpoint, err = min(options, key=lambda item: item[0])
                    else:
                        endpoint, err = bounded_pose(base, final[:3, 3], q, orientation=final[:3, :3])
                    waypoints = np.array([seed[j].copy(), endpoint])
                    if args.plan_free_paths and screen and err < 1e-6:
                        from op030_free_paths import plan_free_path

                        planned = plan_free_path(waypoints[0], endpoint, branch_cost)
                        attempts = [dict(alternative=0, **plan_free_path.last_debug)]
                        if planned is None and choice:
                            for alternative, candidate in enumerate(choice.alternatives[1:], start=1):
                                if candidate[4] > 0 or candidate[5] > 1e-5:
                                    continue
                                planned = plan_free_path(waypoints[0], candidate[1], branch_cost)
                                attempts.append(dict(alternative=alternative, **plan_free_path.last_debug))
                                if planned is not None:
                                    endpoint, err = candidate[1], candidate[2]
                                    choice.select_alternative(alternative, j)
                                    break
                        if planned is None:
                            bad.append(
                                dict(
                                    time=float(t),
                                    side=side,
                                    phase=phase["label"],
                                    error="No collision-screened free path",
                                    details=attempts,
                                )
                            )
                            print("OP030_FREE_PATH_FAILURE", bad[-1], flush=True)
                        else:
                            waypoints = planned
                    free_phases[key] = (waypoints, err)
                waypoints, error_q = free_phases[key]
                u = np.clip((t - phase["start"]) / (phase["stop"] - phase["start"]), 0, 1)
                u = u**3 * (10 - 15 * u + 6 * u * u)
                distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(waypoints, axis=0), axis=1))]
                segment = min(len(waypoints) - 2, int(np.searchsorted(distances, u * distances[-1], side="right")) - 1)
                segment = max(0, segment)
                local_u = np.clip(
                    (u * distances[-1] - distances[segment]) / max(distances[segment + 1] - distances[segment], 1e-9),
                    0,
                    1,
                )
                local_u = local_u**3 * (10 - 15 * local_u + 6 * local_u**2)
                q = waypoints[segment] * (1 - local_u) + waypoints[segment + 1] * local_u
                residual = error_q
            robot, capture = robots[side]
            robot.base_pose = base
            actual = robot.update(q, float(target["grips"][j]))
            if screen:
                screen.set_poses(capture.poses)
            if carried:
                carried_world = {name: actual @ relative for name, relative in held_relative.items()}
                target["objects"].update(carried_world)
                if screen:
                    screen.set_poses(carried_world)
            pe = float(np.linalg.norm(actual[:3, 3] - goal[:3, 3]))
            re = float(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ goal[:3, :3].T).as_rotvec()))
            actual_errors.append([pe, re])
            free_flags.append(free)
            if free and residual < 1e-6:
                # Unloaded transit is deliberately interpolated in joint space.
                # Its actual FK path is rendered and must be mesh-screened.
                pe, re = 0.0, 0.0
            if max(pe, re) > 1e-5:
                bad.append(
                    dict(time=float(t), side=side, phase=phase["label"], position_error_m=pe, rotation_error_rad=re)
                )
            if np.any(abs(q) > LIMITS + 1e-6):
                bad.append(
                    dict(
                        time=float(t),
                        side=side,
                        phase=phase["label"],
                        error="Joint position limit exceeded",
                        joints=q.tolist(),
                    )
                )
            q_rows.append(q)
            errors.append([pe, re])
            tools.append(actual)
            captures.update(capture.poses)
            seed[j] = q
        captures[577] = target["root"]
        captures[578] = target["root"]
        rotations = []
        for size in ("M4", "M6", "M14"):
            value = 0.0
            for p in sequence.phases:
                if p["spin"] and p["spin"]["tool"] == "OP030_driver_" + size and t >= p["start"]:
                    from op020_jb_motion import weight

                    value += p["spin"]["radians"] * weight(t, p["start"], p["stop"])
            rotations.append(value)
        row = dict(
            joints=q_rows,
            errors=errors,
            actual_cartesian_errors=actual_errors,
            free_joint_motion=free_flags,
            tools=tools,
            grips=target["grips"],
            spindle_angles=rotations,
            poses=[captures[int(node)] for node in NODE_IDS],
            object_poses=[target["objects"][name] for name in names],
        )
        if not args.skip_cables:
            for number in (1, 2):
                root_name = f"OP030_H03_{number}_UID001"
                try:
                    row[f"wire_coefficients_{number}"] = coefficients(
                        wire_route(number),
                        target["objects"][root_name],
                        target["objects"][root_name + "_T"],
                        lug_frame(number, "T"),
                    )
                except RuntimeError as exc:
                    bad.append(dict(time=float(t), phase=phase["label"], wire=number, error=str(exc)))
                    row[f"wire_coefficients_{number}"] = np.zeros(17)
        rows.append(row)
        if home_joints is None:
            home_joints = np.arctan2(np.sin(q_rows), np.cos(q_rows))
        if i % 50 == 0:
            print("OP030_SOLVE", round(t, 3), phase["label"], "unresolved", len(bad), flush=True)
    arrays = {key: np.asarray([row[key] for row in rows]) for key in rows[0]}
    for number in (1, 2):
        arrays[f"wire_points_{number}"] = wire_route(number)
        arrays[f"wire_masks_{number}"] = basis(wire_route(number))
        arrays[f"wire_flatten_{number}"] = flatten_basis(wire_route(number))
    # Keep the deliberate full-turn unwinds, including in coarse diagnostic
    # samples whose adjacent angle difference can exceed pi.
    for j in range(2):
        q = arrays["joints"][:, j]
        shift = np.round((q.max(0) + q.min(0)) / (4 * np.pi)) * 2 * np.pi
        q -= shift
        for key, (waypoints, error) in free_phases.items():
            if key[1] == j:
                waypoints -= shift
    np.savez_compressed(
        ROOT / "data" / f"{args.output}.npz",
        times=times,
        frames=times * 30 + 1,
        node_ids=NODE_IDS,
        object_names=names,
        **arrays,
    )
    report = dict(
        failures=bad,
        samples=len(times),
        duration_s=duration,
        phases=[{key: p[key] for key in ("start", "stop", "label")} for p in sequence.phases],
        max_errors=np.asarray(arrays["errors"]).max(axis=(0, 1)).tolist(),
        max_joint_abs_rad=np.abs(arrays["joints"]).max(axis=0).tolist(),
        geometry_and_dynamics_not_validated=True,
    )
    report["provenance"] = provenance
    report["free_joint_paths"] = [
        dict(phase_index=int(key[0]), side=SIDES[key[1]], waypoints=values[0].tolist(), endpoint_residual=values[1])
        for key, values in free_phases.items()
    ]
    if choice:
        report["branch_sections"] = choice.reports
    (ROOT / "audit" / f"{args.output}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OP030_SOLVE_COMPLETE", len(times), "unresolved", len(bad), flush=True)


if __name__ == "__main__":
    main()
