#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Retarget the two OP020 arms to continuous connector poses in SI units."""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "op010_base/scripts"))
import op010_revision as revision  # noqa: E402
from probe_op010_grasp import pad_information  # noqa: E402

R = revision.R
PROFILE = json.loads((ROOT / "data/op020_motion_profile.json").read_text())
PARAMETERS = PROFILE["parameters"]
GRASP = 5.800
SEAT = 18.600
RELEASE = R.STATION_PHASES[1]["release"]
OPEN_END = RELEASE + 0.65
RETREAT_END = 22.6
FOLD_START = 7.12
FOLD_END = 9.2
TURN_END = 12.76
UNFOLD_END = 14.3
CX, CY = 0.9, -2.85
STOCK_X = 1.908199429512024
STOCK_Z = 0.7604363560676575
STOCK_HALF_SPAN = 0.31875741481781
SEATED_X = 0.336
CLOSED_ANGLE = brentq(lambda a: pad_information(a)[0] - 0.068, 0, 0.8)
OPEN_ANGLE = brentq(lambda a: pad_information(a)[0] - 0.080, 0, 0.8)
WAIT_SEEDS = {
    "left": np.array(
        [
            -2.222106845507049,
            -0.15723531107434258,
            1.1543720361150016,
            -0.4732598843394917,
            1.5397675956009889,
            -2.544034101944204,
        ]
    ),
    "right": np.array(
        [
            2.222106845507011,
            3.298827964662903,
            -1.1543720361209202,
            3.6148525379364305,
            -1.5397675956010013,
            2.5440341019439208,
        ]
    ),
}
PART_FROM_TOOL = {side: np.asarray(value) for side, value in PROFILE["part_from_tool"].items()}


def motion_time(seconds: float) -> float:
    """Map playback time [s] to the shared, monotonic held-motion time [s].

    Args:
        seconds: Playback time [s]. Pass playback time to the other public motion
            helpers; they call this mapping internally. Cable routing can use
            this result to follow the same geometric path.

    Returns:
        Profile time [s], unchanged outside the fold interval.
    """
    if not FOLD_START < seconds < FOLD_END:
        return float(seconds)
    phase = (seconds - FOLD_START) / (FOLD_END - FOLD_START)
    return float(seconds + PARAMETERS["fold_time_warp_s"] * np.sin(2 * np.pi * phase))


def _cell_rotation_root_at_motion_time(seconds: float) -> np.ndarray:
    """Evaluate the rotation root [m] at an already mapped profile time [s]."""
    pose = R.cell_rotation_root(1, float(np.clip(seconds, GRASP, RETREAT_END))).copy()
    initial_yaw = R.CELL_LAYOUT[1][2]
    pose[:3, :3] = R.rotate_z(2 * initial_yaw)[:3, :3] @ pose[:3, :3].T
    phase = (seconds - FOLD_START) / (FOLD_END - FOLD_START)
    bump = (
        np.radians(PARAMETERS["fold_yaw_bump_deg"])
        * R.smootherstep(phase / (0.7 / 1.55))
        * (1 - R.smootherstep((phase - 1.0 / 1.55) / (0.55 / 1.55)))
    )
    pose[:3, :3] = R.rotate_z(bump)[:3, :3] @ pose[:3, :3]
    return pose


def cell_rotation_root(seconds: float) -> np.ndarray:
    """Return OP020 rotation-only root [m] at playback time [s]."""
    return _cell_rotation_root_at_motion_time(motion_time(seconds))


def cell_root(seconds: float) -> np.ndarray:
    """Return OP020 lifted root [m] at playback time [s], mapped exactly once."""
    profile_seconds = motion_time(seconds)
    pose = R.cell_root(1, float(np.clip(profile_seconds, GRASP, RETREAT_END))).copy()
    pose[:3, :3] = _cell_rotation_root_at_motion_time(profile_seconds)[:3, :3]
    return pose


def ease(seconds: float, start: float, end: float) -> float:
    """Return a quintic interpolation weight for times [s]."""
    return R.smootherstep((seconds - start) / (end - start))


def folded_target(seconds: float, side: str) -> tuple[np.ndarray, np.ndarray]:
    """Return the held tool target [m] and nominal folding joints [rad]."""
    profile_seconds = motion_time(seconds)
    start = np.asarray(PROFILE["extraction_end_joints_rad"][side])
    folded = np.asarray(PROFILE["fold_target_joints_rad"][side])
    if seconds <= TURN_END:
        phase = (profile_seconds - FOLD_START) / (FOLD_END - FOLD_START)
        weights = np.full(6, R.smootherstep(phase))
        if side == "right":
            weights[1] = R.smootherstep(phase / (1 - PARAMETERS["right_shoulder_first"]))
        joints = start + (folded - start) * weights
    else:
        phase = np.clip((profile_seconds - TURN_END) / (UNFOLD_END - TURN_END), 0, 1)
        if side == "left":
            phase = np.clip(phase / (1 - PARAMETERS["left_unfold_lead"]), 0, 1)
        weight = phase**2 * (3 - 2 * phase)
        goal = np.asarray(PROFILE["unfold_goal_joints_rad"][side])
        joints = folded + (goal - folded) * weight
    base = cell_root(seconds) @ R.yoke_base_pose(side)
    _, desired = R.UR15.forward(base, joints)
    if side == "right":
        weight = ease(profile_seconds, 7.4, 7.85) * (1 - ease(profile_seconds, 8.3, 8.75))
        desired[0, 3] += PARAMETERS["right_tool_x_detour_m"] * weight
    return desired, joints


def part_pose(seconds: float, side: str) -> np.ndarray:
    """Return the connector world pose [m] up to release."""
    sign = -1 if side == "left" else 1
    if seconds <= GRASP:
        return R.transform((STOCK_X, CY + sign * STOCK_HALF_SPAN, STOCK_Z))
    if seconds < FOLD_START:
        lift = ease(seconds, GRASP, 6.17)
        retract = ease(seconds, 6.17, 6.62)
        raise_clear = ease(seconds, 6.62, FOLD_START)
        # Clear the fixed rack's upper inner rail before returning above it.
        # Only reference 6.17..7.12 s changes; the folding endpoint is retained.
        rack_clear_x = 1.800
        return_above_rail = ease(seconds, 7.02, FOLD_START)
        return R.transform(
            (
                STOCK_X
                + (rack_clear_x - STOCK_X) * retract
                + (PARAMETERS["extraction_x_m"] - rack_clear_x) * return_above_rail,
                CY + sign * STOCK_HALF_SPAN,
                STOCK_Z + 0.030 * lift + (PARAMETERS["extraction_z_m"] - STOCK_Z - 0.030) * raise_clear,
            )
        )
    if seconds <= UNFOLD_END:
        tool, _ = folded_target(seconds, side)
        return tool @ PART_FROM_TOOL[side]
    approach = ease(seconds, UNFOLD_END, 15.4)
    half_span = 0.360 + (0.300 - 0.360) * ease(seconds, 16.2, 16.8)
    x = 0.500 + (0.370 - 0.500) * ease(seconds, 15.4, 16.2)
    align = ease(seconds, 16.8, 17.4)
    x += (SEATED_X + 0.016 - 0.370) * align
    z = 1.05 + (revision.FINAL_Z + R.clamp_lift(seconds) + 0.012 + 0.008 - 1.05) * approach
    z -= 0.008 * align
    x -= 0.016 * ease(seconds, 17.6, SEAT)
    return R.transform((x, CY - sign * half_span, z), rpy=(0, 0, np.pi))


@lru_cache(maxsize=4096)
def target(seconds: float, side: str) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """Return tool pose [m], normalized grip, source joints [rad], base pose [m]."""
    seconds = float(np.clip(seconds, 0, RETREAT_END))
    seed = WAIT_SEEDS[side].copy()
    base = cell_root(seconds) @ R.yoke_base_pose(side)
    if FOLD_START <= seconds <= UNFOLD_END:
        desired, seed = folded_target(seconds, side)
        return desired, CLOSED_ANGLE / 0.8, seed, base
    if seconds > UNFOLD_END:
        seed = np.asarray(PROFILE["unfold_goal_joints_rad"][side])
    closing = ease(seconds, 5.0, GRASP)
    opening = ease(seconds, RELEASE, OPEN_END)
    angle = OPEN_ANGLE + (CLOSED_ANGLE - OPEN_ANGLE) * closing * (1 - opening)
    _, pad_mid = pad_information(angle)
    part = part_pose(min(seconds, RELEASE), side)
    # Keep a fixed part-to-hand transform throughout transport. The local
    # upper-rear shell patch clears the wrist and the conveyor guide rail.
    lean = np.radians(-45)
    rotation = part[:3, :3] @ Rotation.from_euler("y", lean).as_matrix() @ Rotation.from_euler("x", np.pi).as_matrix()
    if side == "left":
        # Swap the two pad sides around the same tool axis. This presents the
        # existing onhand camera on the nose side and clears the rear cable.
        rotation = rotation @ Rotation.from_euler("z", np.pi).as_matrix()
    desired = part.copy()
    desired[:3, :3] = rotation
    desired[:3, 3] += part[:3, :3] @ np.array((-0.025, 0, 0.028))
    desired[:3, 3] -= rotation @ pad_mid
    desired[2, 3] += 0.12 * (1 - ease(seconds, 4.2, 5.0))
    pull = ease(seconds, OPEN_END, 21.0)
    separate = ease(seconds, 21.0, RETREAT_END)
    desired[0, 3] += 0.12 * pull
    desired[1, 3] += (1 if side == "left" else -1) * 0.08 * separate
    desired[2, 3] += 0.12 * pull + 0.13 * separate
    return desired, angle / 0.8, seed, base


def solve(
    probe: bool = False,
    *,
    actual_times: np.ndarray | None = None,
    reference_times: np.ndarray | None = None,
    actual_phases_s: dict[str, float] | None = None,
    report_path: Path | None = None,
    candidate_path: Path | None = None,
    accepted_path: Path | None = None,
    clock_provenance: dict[str, object] | None = None,
) -> None:
    """Solve reference targets and measure residuals [m, rad] at actual times [s].

    Args:
        probe: Keep the existing probe schedule and nonpromotion behavior.
        actual_times: Strictly increasing actual sample times [s]. None keeps
            the existing probe or full 30 Hz schedule.
        reference_times: Existing motion-API times [s], one per actual sample.
            None evaluates targets at actual_times without an added clock map.
        actual_phases_s: Complete event-time dictionary in actual seconds [s].
            None keeps the existing reference event dictionary.
        report_path: JSON report path. None keeps the existing filename.
        candidate_path: Candidate NPZ path. None keeps the existing filename.
        accepted_path: Accepted NPZ path for nonprobe runs. Custom nonprobe
            output paths require all three paths explicitly. Probe runs do
            not accept this argument. All paths None preserves the default
            candidate-to-accepted filename and promotion behavior.
        clock_provenance: JSON-serializable clock inputs and hashes. None
            preserves the existing report and NPZ metadata layout.
    """
    times = (
        np.array(
            [
                0,
                4.2,
                4.5,
                5.0,
                GRASP,
                6.17,
                6.62,
                FOLD_START,
                7.85,
                8.2,
                8.75,
                9.2,
                10.2,
                11.3,
                12.76,
                UNFOLD_END,
                15.4,
                16.8,
                17.6,
                SEAT,
                RELEASE,
                OPEN_END,
                21.5,
                22.6,
                23.4,
                24.25,
            ]
        )
        if probe
        else np.arange(788) / 30
    )
    if actual_times is not None:
        times = np.asarray(actual_times, dtype=float)
    reference_supplied = reference_times is not None
    reference_samples = np.asarray(reference_times, dtype=float) if reference_supplied else times
    for name, values in (("actual_times", times), ("reference_times", reference_samples)):
        if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
            raise ValueError(f"{name} must contain at least two finite sample times [s].")
        if np.any(np.diff(values) <= 0):
            raise ValueError(f"{name} must be strictly increasing [s].")
    if reference_samples.shape != times.shape:
        raise ValueError("Reference and actual time arrays must have equal shape.")
    if actual_phases_s is not None:
        if not actual_phases_s or not all(
            isinstance(name, str) and np.isfinite(value) for name, value in actual_phases_s.items()
        ):
            raise ValueError("Actual phase times must be a nonempty finite dictionary [s].")
    if clock_provenance is not None:
        json.dumps(clock_provenance, allow_nan=False)
    custom_paths = (report_path, candidate_path, accepted_path)
    if probe and accepted_path is not None:
        raise ValueError("Probe runs never promote an accepted file.")
    if not probe and any(path is not None for path in custom_paths) and any(path is None for path in custom_paths):
        raise ValueError("Custom nonprobe outputs require report, candidate, and accepted paths.")
    destination = (
        Path(report_path)
        if report_path is not None
        else ROOT / "audit" / ("op020_ik_probe.json" if probe else "op020_motion_checks.json")
    )
    candidate_destination = (
        Path(candidate_path)
        if candidate_path is not None
        else ROOT / "data" / ("op020_probe.npz" if probe else "op020_motion_candidate.npz")
    )
    accepted_destination = Path(accepted_path) if accepted_path is not None else ROOT / "data/op020_motion.npz"
    paths = [destination, candidate_destination] + ([] if probe else [accepted_destination])
    if len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("Report, candidate, and accepted outputs must have distinct paths.")
    joints = np.empty((len(times), 2, 6))
    grips = np.empty((len(times), 2))
    parts = np.empty((len(times), 2, 4, 4))
    errors, failed = [], []
    previous = {}
    for frame, seconds in enumerate(times):
        reference_seconds = float(reference_samples[frame])
        for side_index, side in enumerate(("left", "right")):
            desired, grip, original, base = target(reference_seconds, side)
            seeds = [previous.get(side, original), original]
            if FOLD_START <= reference_seconds <= UNFOLD_END:
                seeds.reverse()
            for elbow in (-1.2, 1.2):
                candidate = original.copy()
                candidate[2] = elbow
                seeds.append(candidate)
            best = None
            for seed in seeds:
                q, residual = R.solve_tool_pose(base, desired[:3, 3], seed, orientation=desired[:3, :3])
                if best is None or residual < best[1]:
                    best = q, residual
                if residual < 1e-6:
                    break
            q, _ = best
            if side in previous:
                q += np.round((previous[side] - q) / (2 * np.pi)) * (2 * np.pi)
            _, actual = R.UR15.forward(base, q)
            position_error = float(np.linalg.norm(actual[:3, 3] - desired[:3, 3]))
            rotation_error = float(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ desired[:3, :3].T).as_rotvec()))
            record = dict(
                frame=frame + 1,
                seconds=float(seconds),
                side=side,
                position_error_m=position_error,
                rotation_error_rad=rotation_error,
            )
            if reference_supplied:
                record["reference_seconds"] = reference_seconds
            errors.append(record)
            if position_error > 1e-5 or rotation_error > 1e-5:
                failed.append(record)
            else:
                previous[side] = q
            joints[frame, side_index], grips[frame, side_index] = q, grip
            parts[frame, side_index] = (
                actual @ PART_FROM_TOOL[side]
                if GRASP <= reference_seconds < RELEASE
                else part_pose(min(reference_seconds, RELEASE), side)
            )
        if probe or frame % 120 == 0:
            print(
                "OP020_IK",
                frame,
                "time",
                round(float(seconds), 3),
                "failed",
                len(failed),
                flush=True,
            )
    steps = np.abs(np.diff(joints, axis=0))
    limits = np.radians([360, 360, 180, 360, 360, 360])
    velocity_limits = np.radians([180, 180, 240, 300, 300, 300])
    speed = steps / np.diff(times)[:, None, None]
    roots = np.array([cell_rotation_root(float(seconds)) for seconds in reference_samples])
    yaw = np.unwrap(np.arctan2(roots[:, 1, 0], roots[:, 0, 0]))
    report = {
        "basis": "Original UR15 FK/IK and source 2F85 pad kinematics; geometry-only animation",
        "probe": probe,
        "frames": len(times),
        "failed_count": len(failed),
        "failures": failed,
        "max_position_error_m": max(r["position_error_m"] for r in errors),
        "max_rotation_error_rad": max(r["rotation_error_rad"] for r in errors),
        "max_frame_joint_step_rad": float(steps.max()),
        "joint_limits_exceeded": bool(np.any(np.abs(joints) > limits)),
        "joint_min_rad": joints.min(axis=0).tolist(),
        "joint_max_rad": joints.max(axis=0).tolist(),
        "max_joint_speed_rad_s": speed.max(axis=0).tolist(),
        "velocity_limits_exceeded": bool(np.any(speed > velocity_limits)),
        "body_yaw_max_speed_rad_s": float(np.max(np.abs(np.diff(yaw)) / np.diff(times))),
        "body_yaw_drive_speed_limit_verified": False,
        "fold_time_warp_amplitude_s": PARAMETERS["fold_time_warp_s"],
        "fold_time_warp_min_derivative": 1 - 2 * np.pi * abs(PARAMETERS["fold_time_warp_s"]) / (FOLD_END - FOLD_START),
        "right_tool_x_detour_m": PARAMETERS["right_tool_x_detour_m"],
        "phases_s": {
            "waiting_end": 4.2,
            "lowered": 5.0,
            "grasp": GRASP,
            **PROFILE["times_s"],
            "outside_guide_lowered": 15.4,
            "outside_sensor_aligned": 16.8,
            "alignment": 17.4,
            "insertion_start": 17.6,
            "seated": SEAT,
            "release": RELEASE,
            "opened": OPEN_END,
            "retreat_stopped": RETREAT_END,
        },
        "cyclic_home_return_included": False,
        "grip_width_m": 0.068,
        "open_width_m": 0.080,
        "records": errors if probe else [],
    }
    extra_arrays = {}
    if reference_supplied:
        extra_arrays["reference_times"] = reference_samples
        report["reference_time_start_s"] = float(reference_samples[0])
        report["reference_time_end_s"] = float(reference_samples[-1])
    if actual_phases_s is not None:
        report["reference_phases_s"] = report["phases_s"]
        report["phases_s"] = dict(actual_phases_s)
    if clock_provenance is not None:
        report["clock_provenance"] = clock_provenance
        extra_arrays["clock_provenance_json"] = np.asarray(json.dumps(clock_provenance, sort_keys=True))
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    np.savez_compressed(
        candidate_destination,
        joints=joints,
        grips=grips,
        times=times,
        parts=parts,
        **extra_arrays,
    )
    if failed or (
        not probe and (steps.max() > 0.2 or report["joint_limits_exceeded"] or report["velocity_limits_exceeded"])
    ):
        raise RuntimeError(f"OP020 motion candidate rejected; see {destination}")
    if not probe:
        candidate_destination.replace(accepted_destination)
    print("OP020_MOTION_COMPLETE", str(destination), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    solve(parser.parse_args().probe)
