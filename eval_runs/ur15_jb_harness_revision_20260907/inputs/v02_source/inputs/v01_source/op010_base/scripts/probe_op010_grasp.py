#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Inspect bounded housing-wall grasp candidates using the source robot FK."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "original"))
import render_ur15_line as R  # noqa: E402


class PoseCapture:
    """Collect source visual transforms without loading CAD meshes."""

    def __init__(self) -> None:
        self.poses: dict[str, np.ndarray] = {}

    def set_pose(self, node: str, pose: np.ndarray) -> None:
        self.poses[node] = np.asarray(pose).copy()


def pad_information(angle: float) -> tuple[float, np.ndarray]:
    """Return pad inner separation and midpoint in the tool frame [m]."""
    capture = PoseCapture()
    robot = R.UR15.__new__(R.UR15)
    robot.scene = capture
    robot.base_pose = np.eye(4)
    robot.visuals = []
    robot.gripper_visuals = [R.RobotVisual(side, side + "_pad", np.eye(4)) for side in ("left", "right")]
    tool = robot.update(np.zeros(6), angle / 0.8)
    centers = np.array([(np.linalg.inv(tool) @ capture.poses[side])[:3, 3] for side in ("left", "right")])
    return float(abs(centers[0, 1] - centers[1, 1]) - 0.00635), centers.mean(axis=0)


def main() -> None:
    closed = brentq(lambda angle: pad_information(angle)[0] - 0.024, 0.0, 0.8)
    _, pad_center = pad_information(closed)
    stock = R.stock_pick_points(0)[0]
    records = []
    for phase, seconds in (("stock", R.STOCK_GRASP), ("seat", R.STATION_PHASES[0]["seat"])):
        housing = (
            R.transform((stock[0], -4.0, stock[2]), rpy=(0, np.pi / 2, 0))
            if phase == "stock"
            else R.transform((0.0, -4.0, 0.5125 + R.clamp_lift(seconds)), rpy=(0, 0, np.pi))
        )
        for grip_x in (-0.10, 0.0, 0.10):
            for lean_deg in (-30, 0, 30):
                for side, sign in (("left", 1), ("right", -1)):
                    contact = np.array((grip_x, sign * 0.348, 0.024))
                    rotation = (
                        housing[:3, :3]
                        @ Rotation.from_euler("y", lean_deg, degrees=True).as_matrix()
                        @ Rotation.from_euler("x", np.pi).as_matrix()
                    )
                    target = (housing @ np.r_[contact, 1])[:3] - rotation @ pad_center
                    base = R.cell_root(0, seconds) @ R.yoke_base_pose(side)
                    original, _ = R.motion_at(seconds, side, 0)
                    seeds = [original.copy()]
                    for bend in (-1.2, 1.2):
                        seed = original.copy()
                        seed[2] = bend
                        seeds.append(seed)
                    best = None
                    for seed in seeds:
                        joints, weighted = R.solve_tool_pose(base, target, seed, orientation=rotation)
                        _, actual = R.UR15.forward(base, joints)
                        position_error = float(np.linalg.norm(actual[:3, 3] - target))
                        rotation_error = float(
                            np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ rotation.T).as_rotvec())
                        )
                        candidate = {
                            "phase": phase,
                            "side": side,
                            "grip_x_m": grip_x,
                            "lean_deg": lean_deg,
                            "position_error_m": position_error,
                            "rotation_error_rad": rotation_error,
                            "weighted_residual": weighted,
                            "joints_rad": joints.tolist(),
                            "target_m": target.tolist(),
                        }
                        if best is None or weighted < best["weighted_residual"]:
                            best = candidate
                        if position_error < 1e-6 and rotation_error < 1e-6:
                            break
                    records.append(best)
    report = {
        "purpose": "Bounded geometric animation-target probe, not a physical grasp verdict",
        "wall_thickness_m": 0.024,
        "closed_angle_rad": closed,
        "pad_midpoint_tool_m": pad_center.tolist(),
        "records": records,
    }
    (ROOT / "audit/grasp_candidates.json").write_text(json.dumps(report, indent=2) + "\n")
    for phase in ("stock", "seat"):
        for grip_x in (-0.10, 0.0, 0.10):
            for lean in (-30, 0, 30):
                group = [r for r in records if (r["phase"], r["grip_x_m"], r["lean_deg"]) == (phase, grip_x, lean)]
                print(
                    phase,
                    "grip_x",
                    grip_x,
                    "lean",
                    lean,
                    "max_pos_m",
                    f"{max(r['position_error_m'] for r in group):.6g}",
                    "max_rot_rad",
                    f"{max(r['rotation_error_rad'] for r in group):.6g}",
                    flush=True,
                )


if __name__ == "__main__":
    main()
