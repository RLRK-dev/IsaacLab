#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Solve shared-frame stocker10 animation with reused UR15 FK/IK [m, rad]."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "inputs/v01_source"
sys.path.insert(0, str(SOURCE / "scripts"))
import op020_motion as source_motion  # noqa: E402
from probe_op010_grasp import PoseCapture  # noqa: E402

R = source_motion.R
SIDES = ("left", "right")
NODE_IDS = np.asarray([565, 566, *range(959, 998), *range(999, 1038)])
NODE_LOOKUP = {int(node): index for index, node in enumerate(NODE_IDS)}
GRASP = 2.8
RELEASE = source_motion.RELEASE
TOP_Z = 1.32
CARRY_RADIUS = 0.95
CARRY_Z = 1.50
PART_FROM_TOOL = source_motion.PART_FROM_TOOL
TOOL_FROM_PART = {side: np.linalg.inv(value) for side, value in PART_FROM_TOOL.items()}
JOINT_LIMITS = np.radians([360, 360, 180, 360, 360, 360])
VELOCITY_LIMITS = np.radians([180, 180, 240, 300, 300, 300])
MOTION_PATH = ROOT / "data/stocker10_motion.npz"
POSE_PACK_PATH = ROOT / "data/stocker10_pose_pack.npz"
CHECKS_PATH = ROOT / "audit/stocker10_motion_checks.json"


def _weight(seconds: float, start: float, end: float) -> float:
    return float(R.smootherstep((seconds - start) / (end - start)))


def _held_targets(seconds: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    initial = source_motion.cell_root(source_motion.GRASP).copy()
    lift = _weight(seconds, GRASP, 4.2)
    angle = -np.pi * _weight(seconds, 4.2, 11.8)
    radius = (source_motion.STOCK_X - source_motion.CX) * (1 - lift) + CARRY_RADIUS * lift
    height = TOP_Z + (CARRY_Z - TOP_Z) * lift
    half_span = source_motion.STOCK_HALF_SPAN
    center = np.array([source_motion.CX + radius * np.cos(angle), source_motion.CY + radius * np.sin(angle), height])
    if seconds > 11.8:
        blend = _weight(seconds, 11.8, 14.3)
        center = center * (1 - blend) + np.array([0.50, source_motion.CY, 1.05]) * blend
        half_span = half_span * (1 - blend) + 0.36 * blend
    turn = R.rotate_z(angle)
    lifted_root = initial.copy()
    lifted_root[:3, :3] = turn[:3, :3] @ initial[:3, :3]
    rotation_root = lifted_root.copy()
    rotation_root[2, 3] = 0.0
    shared = turn.copy()
    shared[:3, 3] = center
    parts = np.array([shared @ R.transform((0, sign * half_span, 0)) for sign in (-1, 1)])
    return rotation_root, lifted_root, parts


def targets_at(seconds: float) -> dict[str, np.ndarray]:
    """Return tool/part/root transforms [m] and normalized gripper openings.

    Args:
        seconds: Actual animation time [s], within [0, 787/30].

    Returns:
        World transforms for both tools and parts, rotation and lifted roots;
        grips are source-normalized opening angles, not gap distances.
    """
    seconds = float(seconds)
    if not np.isfinite(seconds) or not 0 <= seconds <= 787 / 30:
        raise ValueError("Time must be finite and within [0, 787/30] s")
    if seconds <= 14.3:
        rotation_root, lifted_root, parts = _held_targets(seconds)
        grips = np.full(2, source_motion.CLOSED_ANGLE / 0.8)
        tools = np.array([parts[index] @ TOOL_FROM_PART[side] for index, side in enumerate(SIDES)])
        if seconds < GRASP:
            for index, side in enumerate(SIDES):
                old_tool, grip, _, _ = source_motion.target(seconds + 3.0, side)
                tools[index] = old_tool.copy()
                tools[index, 2, 3] += TOP_Z - source_motion.STOCK_Z
                grips[index] = grip
    else:
        rotation_root = source_motion.cell_rotation_root(seconds)
        lifted_root = source_motion.cell_root(seconds)
        parts = np.array([source_motion.part_pose(min(seconds, RELEASE), side) for side in SIDES])
        old = [source_motion.target(seconds, side) for side in SIDES]
        tools = np.array([item[0] for item in old])
        grips = np.array([item[1] for item in old])
    return dict(rotation_root=rotation_root, lifted_root=lifted_root, parts=parts, tools=tools, grips=grips)


@lru_cache(maxsize=1)
def _capture_robots() -> dict[str, tuple[object, PoseCapture]]:
    scene = json.loads((SOURCE / "data/scene_with_controllers.json").read_text())
    with np.load(SOURCE / "data/motion_with_camera_clearance.npz", allow_pickle=False) as saved:
        initial = saved["poses"][0].copy()
    robots = {}
    for side in SIDES:
        capture = PoseCapture()
        robot = R.UR15.__new__(R.UR15)
        robot.scene = capture
        robot.base_pose = R.cell_root(1, 0) @ R.yoke_base_pose(side)
        original, _ = R.motion_at(0, side, 1)
        links, _ = R.UR15.forward(robot.base_pose, original)
        robot.visuals, robot.gripper_visuals = [], []
        for node in scene["nodes"]:
            if node["equipment"] != "robot_OP020_" + side:
                continue
            prefix, _, name = node["name"].partition(":")
            if prefix == "2f85":
                robot.gripper_visuals.append(R.RobotVisual(node["id"], name, np.eye(4)))
            elif prefix in links:
                local = np.linalg.inv(links[prefix]) @ initial[node["id"]]
                robot.visuals.append(R.RobotVisual(node["id"], prefix, local))
        robots[side] = robot, capture
    return robots


@lru_cache(maxsize=1)
def _saved_seeds() -> tuple[np.ndarray, np.ndarray] | None:
    if not MOTION_PATH.is_file():
        return None
    with np.load(MOTION_PATH, allow_pickle=False) as saved:
        return saved["times"].copy(), saved["joints"].copy()


def evaluate(seconds: float, seed_joints: np.ndarray | None = None) -> dict[str, np.ndarray | float | bool]:
    """Solve this geometric motion at a native or subframe time [s].

    Args:
        seconds: Actual animation time [s], within [0, 787/30].
        seed_joints: Optional previous left/right joints [rad], shape (2, 6).
            Otherwise reuse the preceding saved native solution when available.

    Returns:
        Joints [rad], grips, part/tool/root world transforms [m], and 80 source
        node transforms [m] in NODE_IDS order. Error fields use [m] and [rad].
        Carried plug poses are not hidden outside the held interval; callers
        apply supply/carried/product visibility at GRASP and RELEASE.
    """
    target = targets_at(seconds)
    if seed_joints is None:
        saved = _saved_seeds()
        if saved is not None:
            index = int(np.clip(np.searchsorted(saved[0], seconds, side="right") - 1, 0, len(saved[0]) - 1))
            seed_joints = saved[1][index]
        else:
            seed_joints = np.array([source_motion.PROFILE["extraction_end_joints_rad"][side] for side in SIDES])
    seed_joints = np.asarray(seed_joints, dtype=float)
    if seed_joints.shape != (2, 6) or not np.isfinite(seed_joints).all():
        raise ValueError("seed_joints must be finite with shape (2, 6) [rad]")
    poses = np.full((len(NODE_IDS), 4, 4), np.nan)
    poses[NODE_LOOKUP[565]] = target["rotation_root"]
    poses[NODE_LOOKUP[566]] = target["lifted_root"]
    joints, actual_tools, position_errors, rotation_errors = [], [], [], []
    robots = _capture_robots()
    for index, side in enumerate(SIDES):
        desired = target["tools"][index]
        base = target["lifted_root"] @ R.yoke_base_pose(side)
        q, residual = R.solve_tool_pose(base, desired[:3, 3], seed_joints[index], orientation=desired[:3, :3])
        q += np.round((seed_joints[index] - q) / (2 * np.pi)) * (2 * np.pi)
        robot, capture = robots[side]
        robot.base_pose = base
        actual = robot.update(q, target["grips"][index])
        for node, matrix in capture.poses.items():
            poses[NODE_LOOKUP[node]] = matrix
        attached = actual @ PART_FROM_TOOL[side]
        if GRASP <= seconds < RELEASE:
            target["parts"][index] = attached
        poses[NODE_LOOKUP[997 if side == "left" else 1037]] = target["parts"][index]
        joints.append(q)
        actual_tools.append(actual)
        position_errors.append(np.linalg.norm(actual[:3, 3] - desired[:3, 3]))
        rotation_errors.append(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ desired[:3, :3].T).as_rotvec()))
        if not np.isfinite(residual):
            raise RuntimeError("IK returned a non-finite residual")
    if not np.isfinite(poses).all():
        raise RuntimeError("Existing PoseCapture did not populate all requested nodes")
    return dict(
        **target,
        joints=np.asarray(joints),
        actual_tools=np.asarray(actual_tools),
        position_error_m=np.asarray(position_errors),
        rotation_error_rad=np.asarray(rotation_errors),
        poses=poses,
        held=GRASP <= seconds < RELEASE,
        seconds=float(seconds),
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Save all 788 native solutions and source visual poses [m, rad]."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--motion_path", type=Path, default=MOTION_PATH)
    parser.add_argument("--pose_pack_path", type=Path, default=POSE_PACK_PATH)
    parser.add_argument("--checks_path", type=Path, default=CHECKS_PATH)
    args = parser.parse_args()
    inputs = [
        Path(__file__),
        SOURCE / "scripts/op020_motion.py",
        SOURCE / "data/op020_motion_profile.json",
        SOURCE / "data/scene_with_controllers.json",
        SOURCE / "data/motion_with_camera_clearance.npz",
        SOURCE / "op010_base/scripts/op010_revision.py",
        SOURCE / "op010_base/scripts/probe_op010_grasp.py",
        SOURCE / "op010_base/original/render_ur15_line.py",
    ]
    before = {str(path.relative_to(ROOT)): _digest(path) for path in inputs}
    times = np.arange(788) / 30
    values = []
    seed = np.array([source_motion.PROFILE["extraction_end_joints_rad"][side] for side in SIDES])
    for frame, seconds in enumerate(times):
        result = evaluate(float(seconds), seed)
        values.append(result)
        seed = result["joints"]
        if frame % 120 == 0:
            print("STOCKER10_IK", frame + 1, float(seconds), float(result["position_error_m"].max()), flush=True)
    arrays = {
        name: np.asarray([row[name] for row in values])
        for name in ("joints", "grips", "parts", "poses", "position_error_m", "rotation_error_rad", "actual_tools")
    }
    arrays["rotation_roots"] = np.asarray([row["rotation_root"] for row in values])
    arrays["lifted_roots"] = np.asarray([row["lifted_root"] for row in values])
    arrays["held_mask"] = np.asarray([row["held"] for row in values])
    steps = np.abs(np.diff(arrays["joints"], axis=0))
    speeds = steps * 30
    ik_bad = (arrays["position_error_m"] > 1e-5) | (arrays["rotation_error_rad"] > 1e-5)
    limits_bad = np.abs(arrays["joints"]) > JOINT_LIMITS
    speed_bad = speeds > VELOCITY_LIMITS
    after = {str(path.relative_to(ROOT)): _digest(path) for path in inputs}
    if before != after:
        raise RuntimeError("An input changed during native motion generation")
    turn = (times >= 4.2) & (times <= 11.8)
    attachment_error = 0.0
    for index, side in enumerate(SIDES):
        actual_parts = arrays["actual_tools"][:, index] @ PART_FROM_TOOL[side]
        attachment_error = max(
            attachment_error,
            float(np.abs(actual_parts[arrays["held_mask"]] - arrays["parts"][arrays["held_mask"], index]).max()),
        )
    for path in (args.motion_path, args.pose_pack_path, args.checks_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    shared = dict(times=times, node_ids=NODE_IDS, input_sha256_json=np.asarray(json.dumps(before, sort_keys=True)))
    np.savez_compressed(args.motion_path, **shared, **arrays)
    np.savez_compressed(
        args.pose_pack_path,
        **shared,
        poses=arrays["poses"][None].astype(np.float32),
        joints=arrays["joints"][None],
        grips=arrays["grips"][None],
        held_mask=arrays["held_mask"],
        reference_times=times,
        rotation_roots=arrays["rotation_roots"],
        lifted_roots=arrays["lifted_roots"],
    )
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "scope": (
            "Source FK/IK feasibility and continuity for geometric animation; no collision or physical-validity verdict"
        ),
        "guard": {"keywords": ["OP020", "stocker10", "shared_frame", "full_cycle"], "exit_code": 0},
        "input_sha256": before,
        "source_inputs_unchanged": True,
        "motion_sha256": _digest(args.motion_path),
        "pose_pack_sha256": _digest(args.pose_pack_path),
        "frames": len(times),
        "fps": 30,
        "time_interval_s": [float(times[0]), float(times[-1])],
        "node_ids": NODE_IDS.tolist(),
        "pose_shape": list(arrays["poses"].shape),
        "kinematic_checks_succeeded": bool(not (ik_bad.any() or limits_bad.any() or speed_bad.any())),
        "ik_failure_count": int(ik_bad.sum()),
        "joint_limit_failure_count": int(limits_bad.sum()),
        "velocity_limit_failure_count": int(speed_bad.sum()),
        "max_position_error_m": float(arrays["position_error_m"].max()),
        "max_rotation_error_rad": float(arrays["rotation_error_rad"].max()),
        "max_joint_step_rad": float(steps.max()),
        "max_joint_speed_rad_s": speeds.max(axis=0).tolist(),
        "joint_limits_rad": JOINT_LIMITS.tolist(),
        "joint_velocity_limits_rad_s": VELOCITY_LIMITS.tolist(),
        "joint_min_rad": arrays["joints"].min(axis=0).tolist(),
        "joint_max_rad": arrays["joints"].max(axis=0).tolist(),
        "turn_joint_range_rad": np.ptp(arrays["joints"][turn], axis=0).tolist(),
        "held_tool_part_transform_max_abs_error": attachment_error,
        "phases_s": {
            "waiting_end": 1.2,
            "lowered": 2.0,
            "grasp": GRASP,
            "raised": 4.2,
            "turn_end": 11.8,
            "old_approach_join": 14.3,
            "seated": 18.6,
            "release": RELEASE,
            "opened": source_motion.OPEN_END,
            "retreat_stopped": source_motion.RETREAT_END,
        },
        "native_failure_indices": {
            "ik": np.argwhere(ik_bad).tolist(),
            "limits": np.argwhere(limits_bad).tolist(),
            "speed_intervals": np.argwhere(speed_bad).tolist(),
        },
        "limitations": [
            "Native 30 Hz FK/IK only; BVH, subframes, cable and force/contact physics unverified.",
            "Retreat uses the old tool targets and holds after 22.6 s; cyclic return to initial pose is not included.",
            "reference_times in pose pack equal actual times; do not apply the v01 fold playback clock.",
            "Carried node poses are unhidden throughout; caller controls stock/carry/product visibility.",
            "Other stations are absent from this 80-node delta and must keep their original motion.",
        ],
    }
    args.checks_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print("STOCKER10_COMPLETE", report["kinematic_checks_succeeded"], args.motion_path, flush=True)
    if not report["kinematic_checks_succeeded"]:
        raise RuntimeError(f"Native kinematic checks failed; see {args.checks_path}")


if __name__ == "__main__":
    main()
