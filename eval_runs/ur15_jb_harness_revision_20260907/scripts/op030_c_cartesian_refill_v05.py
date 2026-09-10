# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Finite same-presenter Cartesian returns on a continuous C IK branch [m, rad]."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from op030_c_refill_v05 import refill_phases
from op030_definition import ROOT
from op030_fk_fast import LIMITS, chain_for
from op030_split_c_v04 import digest
from op030_split_c_v05 import combined_row, drive_phases, source_tracks
from op030_split_c_v05_check import Context
from scipy.spatial.transform import Rotation, Slerp
from solve_op030_motion import R


def trace(
    context: Context,
    control: dict,
    start_q: np.ndarray,
    arm: int,
    tcp_knots: list[np.ndarray],
    half_turn_sign: int | None = None,
) -> dict:
    """Trace a few rigid TCP waypoints at <=5 mm / <=2 degree samples [m, rad]."""
    side = "left" if arm == 0 else "right"
    chain = chain_for(tuple((control["poses"][0] @ R.yoke_base_pose(side)).ravel()))
    size = "M6" if arm == 0 else "M14"
    calibration = np.asarray(context.metadata["fixed_tools"]["OP030C_" + size]["flange_to_tcp"])
    inverse = np.linalg.inv(calibration)
    q = start_q.copy()
    rows, targets, maximum = [q.copy()], [tcp_knots[0]], 0.0
    for a, b in zip(tcp_knots[:-1], tcp_knots[1:], strict=True):
        angle = np.linalg.norm(Rotation.from_matrix(a[:3, :3].T @ b[:3, :3]).as_rotvec())
        steps = max(1, int(np.ceil(np.linalg.norm(b[:3, 3] - a[:3, 3]) / 0.005)), int(np.ceil(angle / np.deg2rad(2))))
        rotate = Slerp([0, 1], Rotation.from_matrix(np.asarray([a[:3, :3], b[:3, :3]])))
        for fraction in np.linspace(0, 1, steps + 1)[1:]:
            tcp = np.eye(4)
            tcp[:3, 3] = a[:3, 3] * (1 - fraction) + b[:3, 3] * fraction
            if half_turn_sign is not None and abs(angle - np.pi) < 1e-6:
                relative_axis = Rotation.from_matrix(a[:3, :3].T @ b[:3, :3]).as_rotvec() / angle
                if np.linalg.norm(relative_axis[:2]) > 1e-6:
                    raise ValueError("Explicit half-turn direction requires the common tool Z axis")
                tcp[:3, :3] = a[:3, :3] @ Rotation.from_euler("z", half_turn_sign * np.pi * fraction).as_matrix()
            else:
                tcp[:3, :3] = rotate(float(fraction)).as_matrix()
            value, residual = chain.solve_continuous(tcp @ inverse, q[arm])
            step = float(abs(value - q[arm]).max())
            maximum = max(maximum, residual)
            if residual > 1e-5 or np.any(abs(value) >= LIMITS) or step > 0.3:
                return dict(
                    passed=False,
                    failure="continuous_ik",
                    residual=residual,
                    step_rad=step,
                    within_limits=bool(np.all(abs(value) < LIMITS)),
                    tcp=tcp.tolist(),
                    checked_states=len(rows),
                    last_joints=q.tolist(),
                )
            q[arm] = value
            hits, _ = context.query(control, q)
            if hits:
                return dict(
                    passed=False,
                    failure="native_mesh",
                    pairs=hits,
                    tcp=tcp.tolist(),
                    checked_states=len(rows),
                    last_joints=q.tolist(),
                )
            rows.append(q.copy())
            targets.append(tcp.copy())
    return dict(
        passed=True,
        joints=np.asarray(rows).tolist(),
        tcp=np.asarray(targets).tolist(),
        checked_states=len(rows),
        maximum_ik_residual=maximum,
    )


def main() -> None:
    """Compare direct and two finite overhead lanes without moving any equipment [m]."""
    output = ROOT / "audit/op030_c_cartesian_refill_v05.json"
    if output.exists():
        raise FileExistsError(output)
    data, _, tracks = source_tracks()
    context = Context(data["object_names"])
    results = []
    for number in (2, 1):
        drive, refill = drive_phases(tracks, number), refill_phases(tracks, number)
        start = [drive[0][4]["stop_frame"], drive[1][3]["stop_frame"]]
        goal = [
            next(p["stop_frame"] for p in phases if p["label"].endswith("／固定工具を供給上方へ")) for phases in refill
        ]
        row = combined_row(data, tracks, *goal)
        q = combined_row(data, tracks, *start)["joints"].copy()
        records = []
        for arm, size in enumerate(("M6", "M14")):
            calibration = np.asarray(context.metadata["fixed_tools"]["OP030C_" + size]["flange_to_tcp"])
            side = "left" if arm == 0 else "right"
            chain = chain_for(tuple((row["poses"][0] @ R.yoke_base_pose(side)).ravel()))
            begin = chain.forward(q[arm])[0] @ calibration
            end = row["tools"][arm] @ calibration
            candidates = [("straight", [begin, end])]
            for clearance in (0.15, 0.30):
                a, b = begin.copy(), end.copy()
                a[2, 3] = b[2, 3] = max(begin[2, 3], end[2, 3]) + clearance
                candidates.append((f"overhead_{int(clearance * 1000)}mm", [begin, a, b, end]))
            selected = None
            for label, knots in candidates:
                result = trace(context, row, q, arm, knots)
                result.update(arm=arm, size=size, candidate=label)
                records.append(result)
                print("C_CARTESIAN_REFILL", number, size, label, result["passed"], result["checked_states"], flush=True)
                if result["passed"]:
                    q = np.asarray(result["joints"][-1])
                    selected = label
                    break
            if selected is None:
                break
        results.append(
            dict(
                number=number,
                start_local=start,
                goal_local=goal,
                records=records,
                complete=len({record["arm"] for record in records if record["passed"]}) == 2,
            )
        )
    output.write_text(
        json.dumps(
            dict(
                observed_at=datetime.now().astimezone().isoformat(),
                source_script_sha256=digest(Path(__file__)),
                mesh_sha256=digest(context.mesh_file),
                delta="Keep source work branch and move TCP through finite Cartesian lanes; "
                "do not force old positive-elbow feeder branch",
                records=results,
                geometry_modified=False,
                formal_physical_verdict=False,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
