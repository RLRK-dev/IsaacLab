# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Author one supported harness cycle with reused UR15 FK/IK [m, rad, s]."""

from __future__ import annotations

import argparse
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation, Slerp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "inputs/v02_source/scripts"))
import stocker10_motion as original  # noqa: E402
from jb_harness import PORT_FRAME, PORT_ORIGIN  # noqa: E402

R = original.R
FPS, DURATION = 30, 68.0
CX, CY, JB_Z = 0.9, -2.85, 0.5345
TOP_TRAY_Z = 1.11
RETURN_LATERAL_EXTRA = 0.04
SIDES = ("left", "right")
NODE_IDS = np.asarray([565, 566, *range(959, 997), *range(999, 1037)])
NODE_LOOKUP = {int(n): i for i, n in enumerate(NODE_IDS)}
HANDLE = np.array([-0.340, 0.365, 0.090])
LEFT_RETURN_HANDLE = np.array([-0.340, -0.150, 0.340])
GRIP_CONTACT = np.array([0.015, 0.0, 0.0065])
CAP_CONTACT = np.array([0.0, -0.070, 0.0045])
CPA_CLOSED = np.array([0.0, -0.024, 0.0588])
LEVER_PIVOT = np.array([0.0, -0.022, 0.0563])
LEVER_GRIP = np.array([0.078, 0.049, 0.0])
GRIP_ROTATION = Rotation.from_euler("y", -110, degrees=True).as_matrix()
MATING_GRIP_ROTATION = Rotation.from_euler("y", -116, degrees=True).as_matrix()
LEFT_RETURN_ROTATION = Rotation.from_euler("y", 100, degrees=True).as_matrix()
RIGHT_GRIP_ROTATION = Rotation.from_euler("y", 150, degrees=True).as_matrix()
# Retain the complete screened IK branch, including wrist orientation [rad].
# An elbow-sign filter alone also admits a flipped wrist that crosses the tray.
RIGHT_INITIAL_JOINTS = np.array(
    [-0.9270844134, -0.1879507504, 1.7578319625, -2.2042152329, 2.5023692044, -1.2471308662]
)
LEFT_LEVER_STANDOFF = np.array([0.10, 0.15, 0.10])
SMALL_ROTATION = np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], dtype=float)
CAP_ROTATION = Rotation.from_euler("x", 90, degrees=True).as_matrix() @ SMALL_ROTATION
SMALL_ROTATION = Rotation.from_euler("x", 30, degrees=True).as_matrix() @ SMALL_ROTATION
LEVER_ROTATION = Rotation.from_euler("y", -90, degrees=True).as_matrix()
STOCK = None
FREE_TRANSITS = ((17.8, 20), (26, 28), (29.5, 30.5), (33.5, 35.1), (39.5, 40.5), (43.5, 44.5), (47, 47.7))
REFERENCE = ROOT / "data/op020_operation_reference_v09.npz"
PHASES = [
    (0, "10段供給・上段へ接近"),
    (2, "接続端と支持トレーを把持"),
    (3, "支持トレーごと引き上げ"),
    (5, "支えたままセルを旋回"),
    (13, "JB前へ移動・姿勢を合わせる"),
    (17, "トレー支持へ移管"),
    (19, "JB端の保護キャップを把持"),
    (21, "保護キャップを抜く"),
    (23, "保護キャップを回収受けへ"),
    (26, "二次ロックCPAを解除"),
    (29, "係止爪の解除位置へ移動（押下機構は要詳細化）"),
    (30, "レバーを把持して開く"),
    (34, "接続端を持ち直す"),
    (36, "JB側へ位置合わせ・予備嵌合"),
    (39, "開いたレバーを持ち直す"),
    (41, "レバーを閉じて嵌合"),
    (44, "CPAを閉じる"),
    (46, "ケーブルと自由端をF01へ移管"),
    (47, "左手で回収用ハンドルを把持"),
    (48, "両腕で空の支持トレーを引き抜く"),
    (51, "両腕保持で空トレー回収位置へ"),
    (62, "両腕で空トレーを回収受けへ置く"),
    (66, "着座後に両手を解放・退避"),
]


def pose(rotation=None, location=None):
    out = np.eye(4)
    if rotation is not None:
        out[:3, :3] = rotation
    if location is not None:
        out[:3, 3] = location
    return out


def weight(t, a, b):
    x = float(np.clip((t - a) / (b - a), 0, 1))
    return x**3 * (10 - 15 * x + 6 * x * x)


def mix(a, b, w):
    w = float(np.clip(w, 0, 1))
    if w == 0:
        return a.copy()
    if w == 1:
        return b.copy()
    rotation = Slerp([0, 1], Rotation.from_matrix(np.array([a[:3, :3], b[:3, :3]])))(w).as_matrix()
    return pose(rotation, a[:3, 3] * (1 - w) + b[:3, 3] * w)


@lru_cache(maxsize=64)
def grip_angle(gap):
    return float(brentq(lambda a: original.source_motion.pad_information(a)[0] - gap, 0, 0.8))


def tool_for(frame, contact, orientation, gap):
    angle = grip_angle(gap)
    mid = original.source_motion.pad_information(angle)[1]
    rotation = frame[:3, :3] @ orientation
    xyz = frame[:3, :3] @ contact + frame[:3, 3] - rotation @ mid
    return pose(rotation, xyz), angle / 0.8


def retract(tool, distance):
    result = tool.copy()
    result[:3, 3] -= tool[:3, :3][:, 2] * distance
    return result


def tray_frame(t):
    stock = pose(Rotation.from_euler("y", -90, degrees=True).as_matrix(), (1.78, CY + 0.06, TOP_TRAY_Z + 0.338))
    if t <= 5:
        out = stock.copy()
        out[2, 3] += 0.22 * weight(t, 3, 5)
        return out
    if t <= 13:
        angle = -math.pi * weight(t, 5, 13)
        turn = Rotation.from_euler("z", angle).as_matrix()
        center = np.array([CX, CY, 0])
        lift = stock.copy()
        lift[2, 3] += 0.22
        return pose(turn @ stock[:3, :3], center + turn @ (lift[:3, 3] - center))
    target = pose(Rotation.from_euler("z", 180, degrees=True).as_matrix(), (0.110, CY, JB_Z + 0.28))
    if t <= 15.5:
        raised = target.copy()
        raised[2, 3] += 0.40
        return mix(tray_frame(13), raised, weight(t, 13, 15.5))
    if t <= 17:
        return mix(tray_frame(15.5), target, weight(t, 15.5, 17))
    if t <= 48:
        target[2, 3] -= 0.28 * weight(t, 36, 37.5)
        target[0, 3] = 0.110 - 0.096 * weight(t, 37.5, 39) - 0.014 * weight(t, 41, 43)
        return target
    if t <= 51:
        out = tray_frame(48)
        out[0, 3] += 0.060 * weight(t, 48, 49) + RETURN_LATERAL_EXTRA * weight(t, 50, 51)
        out[2, 3] += 0.35 * weight(t, 49, 50)
        return out
    if t <= 54:
        return mix(tray_frame(51), tray_frame(13), weight(t, 51, 54))
    if t <= 62:
        angle = -math.pi * (1 - weight(t, 54, 62))
        turn = Rotation.from_euler("z", angle).as_matrix()
        center = np.array([CX, CY, 0])
        lift = stock.copy()
        lift[2, 3] += 0.22
        return pose(turn @ stock[:3, :3], center + turn @ (lift[:3, 3] - center))
    destination = pose(stock[:3, :3], (1.78, CY + 0.06, 1.868))
    if t <= 65:
        return mix(tray_frame(62), destination, weight(t, 62, 65))
    out = destination.copy()
    out[2, 3] -= 0.20 * weight(t, 65, 66)
    return out


def harness_frame(t):
    return tray_frame(min(t, 48.0))


def a_frame(t):
    return harness_frame(t) @ pose(PORT_FRAME, PORT_ORIGIN)


def lever_angle(t):
    return math.radians(80) * weight(t, 31, 33) * (1 - weight(t, 41, 43))


def cpa_position(t):
    return CPA_CLOSED + np.array([0, 0.012 * weight(t, 28, 29) * (1 - weight(t, 45, 46)), 0])


def cap_frame(t):
    if t <= 21:
        return a_frame(t)
    removed = a_frame(21) @ pose(location=(0, 0, -0.025))
    if t < 23:
        return mix(a_frame(21), removed, weight(t, 21, 23))
    deposit = pose(removed[:3, :3], (0.45, CY + 0.85, 0.91))
    raised = removed.copy()
    raised[0, 3] += 0.15
    above = deposit.copy()
    above[2, 3] += 0.12
    above[0, 3] += 0.15
    outside = deposit.copy()
    outside[0, 3] += 0.15
    if t <= 23.5:
        return mix(removed, raised, weight(t, 23, 23.5))
    if t <= 24:
        return mix(raised, above, weight(t, 23.5, 24))
    if t <= 24.5:
        return mix(above, outside, weight(t, 24, 24.5))
    return mix(outside, deposit, weight(t, 24.5, 25))


def left_target(t):
    a = a_frame(t)
    grab_rotation = GRIP_ROTATION if t < 30 else MATING_GRIP_ROTATION
    grab, closed = tool_for(a, GRIP_CONTACT, grab_rotation, 0.037)
    if t <= 3:
        gap = 0.080 - 0.043 * weight(t, 2, 3)
        tool, grip = tool_for(a, GRIP_CONTACT, GRIP_ROTATION, gap)
        return retract(tool, 0.10 * (1 - weight(t, 0, 2))), grip
    if t <= 17:
        return grab, closed
    cap_tool, cap_grip = tool_for(cap_frame(t), CAP_CONTACT, CAP_ROTATION, 0.018)
    if t <= 19:
        # Release locally before opening further away from the adjacent wires.
        gap = 0.050 + 0.034 * weight(t, 17.8, 18.2)
        opened = grip_angle(round(gap, 8)) / 0.8
        if t <= 17.8:
            target = retract(grab, 0.10 * weight(t, 17.2, 17.8))
        else:
            target = mix(retract(grab, 0.10), retract(cap_tool, 0.065), weight(t, 17.8, 19))
        return target, closed * (1 - weight(t, 17, 17.3)) + opened * weight(t, 17, 17.3)
    if t <= 21:
        return mix(retract(cap_tool, 0.065), cap_tool, weight(t, 19, 20)), cap_grip * weight(t, 20, 21)
    if t <= 25:
        return cap_tool, cap_grip
    cpa_tool, cpa_grip = tool_for(a, cpa_position(t), SMALL_ROTATION, 0.018)
    if t <= 28:
        start = tool_for(cap_frame(25), CAP_CONTACT, CAP_ROTATION, 0.018)[0]
        released = grip_angle(0.026) / 0.8
        if t <= 26:
            grip = cap_grip + (released - cap_grip) * weight(t, 25, 25.2)
            return retract(start, 0.10 * weight(t, 25.2, 26)), grip
        grip = released * (1 - weight(t, 26, 26.5)) + cpa_grip * weight(t, 27.4, 28)
        return mix(retract(start, 0.10), cpa_tool, weight(t, 26, 28)), grip
    if t <= 29:
        return cpa_tool, cpa_grip
    lever_frame = a @ pose(Rotation.from_euler("x", lever_angle(t)).as_matrix(), LEVER_PIVOT)
    lever_tool, lever_grip = tool_for(lever_frame, LEVER_GRIP, LEVER_ROTATION, 0.010)
    if t <= 31:
        if t <= 29.5:
            return retract(cpa_tool, 0.04 * weight(t, 29, 29.5)), cpa_grip * (1 - weight(t, 29, 29.5))
        return mix(retract(cpa_tool, 0.04), lever_tool, weight(t, 29.5, 30.5)), lever_grip * weight(t, 30.5, 31)
    if t <= 33:
        return lever_tool, lever_grip
    if t <= 36:
        if t <= 34:
            return retract(lever_tool, 0.035 * weight(t, 33, 34)), lever_grip * (1 - weight(t, 33, 33.5))
        approach_grip = grip_angle(0.050) / 0.8
        if t < 35.1:
            target = mix(retract(lever_tool, 0.035), retract(grab, 0.12), weight(t, 34, 35.1))
        else:
            target = retract(grab, 0.12 * (1 - weight(t, 35.1, 35.6)))
        grip = approach_grip * weight(t, 34.4, 35.1)
        grip += (closed - approach_grip) * weight(t, 35.6, 36)
        return target, grip
    if t <= 39:
        return grab, closed
    if t <= 41:
        if t <= 39.5:
            return retract(grab, 0.04 * weight(t, 39, 39.5)), closed * (1 - weight(t, 39, 39.5))
        return mix(retract(grab, 0.04), lever_tool, weight(t, 39.5, 40.5)), lever_grip * weight(t, 40.5, 41)
    if t <= 43:
        return lever_tool, lever_grip
    if t <= 45:
        released = grip_angle(0.022) / 0.8
        if t <= 43.5:
            grip = lever_grip + (released - lever_grip) * weight(t, 43, 43.2)
            return retract(lever_tool, 0.04 * weight(t, 43.2, 43.5)), grip
        approach = grip_angle(0.026) / 0.8
        grip = released + (approach - released) * weight(t, 43.5, 44)
        grip += (cpa_grip - approach) * weight(t, 44.5, 45)
        return mix(retract(lever_tool, 0.04), cpa_tool, weight(t, 43.5, 44.5)), grip
    if t <= 46:
        return cpa_tool, cpa_grip
    released = grip_angle(0.026) / 0.8
    if 46 < t <= 47:
        grip = cpa_grip + (released - cpa_grip) * weight(t, 46, 46.2)
        return retract(cpa_tool, 0.10 * weight(t, 46, 47)), grip
    gap = 0.026 + 0.054 * weight(t, 47, 47.3) - 0.040 * weight(t, 47.7, 48) + 0.040 * weight(t, 66, 67)
    target, grip = tool_for(tray_frame(t), LEFT_RETURN_HANDLE, LEFT_RETURN_ROTATION, round(gap, 8))
    return retract(target, 0.04 * weight(t, 67, 68)), grip


@lru_cache(maxsize=8)
def reference_motion():
    with np.load(REFERENCE) as data:
        return data["times"].copy(), data["joints"].copy()


@lru_cache(maxsize=8192)
def reference_left_solution(t):
    """Solve a Cartesian endpoint from the prior continuous wrist branch [rad]."""
    times, joints = reference_motion()
    q = np.array([np.interp(t, times, joints[:, axis]) for axis in range(6)])
    desired = left_target(t)[0]
    base = cell_frame(t) @ R.yoke_base_pose("left")
    result, residual = R.solve_tool_pose(base, desired[:3, 3], q, orientation=desired[:3, :3])
    result += np.round((q - result) / (2 * math.pi)) * 2 * math.pi
    if residual > 1e-5:
        raise RuntimeError(f"Reference endpoint does not solve at {t}: {residual}")
    return result


def free_transit(t):
    return next(((a, b) for a, b in FREE_TRANSITS if a < t < b), None)


@lru_cache(maxsize=64)
def reference_standoff(t):
    """Solve an unloaded hand waypoint above and outside the fixture [m, rad]."""
    q = reference_left_solution(t)
    desired = left_target(t)[0].copy()
    offset = [0.10, 0.15, 0.10] if t in (33.5, 35.1) else [0.25, 0, 0.20]
    if t in (29.5, 30.5, 47, 47.7):
        offset = LEFT_LEVER_STANDOFF
    desired[:3, 3] += np.array(offset)
    base = cell_frame(t) @ R.yoke_base_pose("left")
    result, error = R.solve_tool_pose(base, desired[:3, 3], q, orientation=desired[:3, :3])
    result += np.round((q - result) / (2 * math.pi)) * 2 * math.pi
    if error > 1e-5:
        raise RuntimeError(f"Unloaded standoff is unreachable at {t}: {error}")
    return result


def transit_joint_pose(t, start, stop):
    """Retreat, change wrist orientation away from the part, then approach [rad]."""
    one = start + (stop - start) * 0.22
    two = start + (stop - start) * 0.78
    if t < one:
        q0, q1 = reference_left_solution(start), reference_standoff(start)
        w = weight(t, start, one)
    elif t < two:
        q0, q1 = reference_standoff(start), reference_standoff(stop)
        w = weight(t, one, two)
    else:
        q0, q1 = reference_standoff(stop), reference_left_solution(stop)
        w = weight(t, two, stop)
    guess = q0 * (1 - w) + q1 * w
    if t < one or t >= two:
        base = cell_frame(t) @ R.yoke_base_pose("left")
        p0 = R.UR15.forward(base, q0)[1]
        p1 = R.UR15.forward(base, q1)[1]
        target = mix(p0, p1, w)
        result, error = R.solve_tool_pose(base, target[:3, 3], guess, orientation=target[:3, :3])
        result += np.round((guess - result) / (2 * math.pi)) * (2 * math.pi)
        if error > 1e-5:
            raise RuntimeError(f"Unloaded approach does not solve at {t}: {error}")
        return result
    return guess


def clip_frame(t):
    """Return the removable lever tool pose, recovered with its tray [m]."""
    frame = a_frame(min(t, 48)) @ pose(Rotation.from_euler("x", lever_angle(min(t, 48))).as_matrix(), LEVER_PIVOT)
    if t > 48:
        frame = tray_frame(t) @ np.linalg.inv(tray_frame(48)) @ frame
    return frame


def right_target(t):
    # The original two-finger hand grips a 40-mm-wide handle on the reusable
    # support tray. Its fingers do not directly pinch the cable insulation.
    tray = tray_frame(t)
    orientation = RIGHT_GRIP_ROTATION
    gap = 0.080 - 0.040 * weight(t, 2, 3) + 0.040 * weight(t, 66, 67)
    target, grip = tool_for(tray, HANDLE, orientation, float(round(gap, 8)))
    clearance = 0.10 * (1 - weight(t, 0, 2)) + 0.12 * weight(t, 67, 68)
    return retract(target, clearance), grip


def cell_frame(t):
    yaw = -math.pi * weight(t, 5, 13) + math.pi * weight(t, 54, 62)
    return pose(Rotation.from_euler("z", yaw + math.pi / 2).as_matrix(), (CX, CY, 0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, default=1)
    args = parser.parse_args()
    times = np.arange(0, int(DURATION * FPS) + 1, args.step) / FPS
    robots = original._capture_robots()
    seed = np.asarray([original.source_motion.PROFILE["extraction_end_joints_rad"][s] for s in SIDES])
    candidates = ROOT / "audit/op020_ik_candidates.json"
    if candidates.exists():
        rows = json.loads(candidates.read_text())
        seed = np.asarray([next(row["q"] for row in rows if row["t"] == 0 and row["side"] == s) for s in SIDES])
        seed = np.arctan2(np.sin(seed), np.cos(seed))
    seed[1] = RIGHT_INITIAL_JOINTS
    rng = np.random.default_rng(90207)
    for j, side in enumerate(SIDES):
        desired = (left_target(0), right_target(0))[j][0]
        base = cell_frame(0) @ R.yoke_base_pose(side)
        options = []
        for start in [seed[j], *[rng.uniform(-math.pi, math.pi, 6) for _ in range(24)]]:
            q, residual = R.solve_tool_pose(base, desired[:3, 3], start, orientation=desired[:3, :3])
            q = np.arctan2(np.sin(q), np.cos(q))
            options.append((residual, float(np.linalg.norm(q - seed[j])), q))
        feasible = [item for item in options if item[0] < 1e-6]
        if side == "right":
            # Preserve both the elbow and wrist signs of the screened initial
            # solution, then select the solution nearest its complete seed.
            feasible = [item for item in feasible if item[2][2] > 0 and item[2][4] > 0]
            if not feasible:
                raise RuntimeError("The screened right-arm elbow branch is unavailable")
        seed[j] = min(feasible or options, key=lambda item: item[1] if feasible else item[0])[2]
    records, bad = [], []
    for index, t in enumerate(times):
        targets = [left_target(t), right_target(t)]
        root = cell_frame(t)
        visuals = np.full((len(NODE_IDS), 4, 4), np.nan)
        visuals[0], visuals[1] = root, root
        qs, errors, tools = [], [], []
        for j, side in enumerate(SIDES):
            desired, grip = targets[j]
            base = root @ R.yoke_base_pose(side)
            transit = free_transit(float(t)) if side == "left" else None
            if side == "left":
                if transit:
                    start, stop = transit
                    q = transit_joint_pose(t, start, stop)
                else:
                    q = reference_left_solution(float(t))
            else:
                q, error = R.solve_tool_pose(base, desired[:3, 3], seed[j], orientation=desired[:3, :3])
                q += np.round((seed[j] - q) / (2 * math.pi)) * 2 * math.pi
            robot, capture = robots[side]
            robot.base_pose = base
            actual = robot.update(q, grip)
            pe = 0.0 if transit else float(np.linalg.norm(actual[:3, 3] - desired[:3, 3]))
            re = (
                0.0
                if transit
                else float(np.linalg.norm(Rotation.from_matrix(actual[:3, :3] @ desired[:3, :3].T).as_rotvec()))
            )
            if pe > 1e-5 or re > 1e-5:
                bad.append([float(t), side, pe, re])
            for node, matrix in capture.poses.items():
                visuals[NODE_LOOKUP[node]] = matrix
            qs.append(q)
            errors.append([pe, re])
            tools.append(actual)
        seed = np.asarray(qs)
        records.append(
            dict(
                joints=seed,
                poses=visuals,
                tools=tools,
                errors=errors,
                grips=[item[1] for item in targets],
                tray=tray_frame(t),
                harness=harness_frame(t),
                cap=cap_frame(t),
                lever=lever_angle(t),
                cpa=cpa_position(t),
            )
        )
        records[-1]["clip"] = clip_frame(t)
        if index % 120 == 0:
            print("OP020_SINGLE_END_IK", index, float(t), "bad", len(bad), flush=True)
    arrays = {k: np.asarray([record[k] for record in records]) for k in records[0]}
    path = ROOT / "data" / ("op020_jb_motion.npz" if args.step == 1 else "op020_jb_probe.npz")
    np.savez_compressed(path, times=times, node_ids=NODE_IDS, **arrays)
    checks = {
        "scope": "Provisional kinematic authoring; no physical-validity verdict",
        "frames": len(times),
        "failures": bad,
        "max_position_error_m": float(arrays["errors"][:, :, 0].max()),
        "max_rotation_error_rad": float(arrays["errors"][:, :, 1].max()),
        "max_joint_step_rad": float(np.abs(np.diff(arrays["joints"], axis=0)).max()),
        "joint_min": arrays["joints"].min(axis=0).tolist(),
        "joint_max": arrays["joints"].max(axis=0).tolist(),
        "phases": PHASES,
        "left_free_joint_transits_s": FREE_TRANSITS,
        "right_elbow_branch": "positive elbow and wrist_2; complete screened initial seed retained",
        "right_initial_joints_rad": RIGHT_INITIAL_JOINTS.tolist(),
        "cartesian_error_scope": "Held/operating phases only; free transits use quintic joint interpolation",
    }
    (ROOT / "audit" / (path.stem + "_checks.json")).write_text(json.dumps(checks, ensure_ascii=False, indent=2))
    print("OP020_SINGLE_END_FINISHED", len(times), "bad", len(bad), flush=True)
    if bad:
        raise RuntimeError("New trajectory has unresolved inverse-kinematics targets")


if __name__ == "__main__":
    main()
