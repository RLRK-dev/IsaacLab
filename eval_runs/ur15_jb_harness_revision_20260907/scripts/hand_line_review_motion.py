# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Initial review timing and target transforms [m, rad, s].

The cycle is prescribed geometry, without contact or cable dynamics. OP030
replays one parallel cycle from three station views on distinct workpieces.
"""

from __future__ import annotations

import math

import numpy as np

FPS = 30
FRAMES = 2040
BODY_BOTTOM = 0.833
PART_Z = BODY_BOTTOM + 0.016
CABLE_Z = BODY_BOTTOM + 0.064
B_ROBOT_X = 7.2
B_MOUNTS = {"B_left": (0.040, math.pi / 2), "B_right": (0.120, 3 * math.pi / 2)}
LUG_PLATE_TOP_Z = -0.014 + 0.0038
CENTERS = {"OP010": 0.0, "OP020": 2.4, "A": 4.8, "B": 7.2, "C": 9.6}


def transform(xyz=(0, 0, 0), rpy=(0, 0, 0)):
    """Return an XYZ Euler rigid transform [m, rad]."""
    x, y, z = rpy
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array(((1, 0, 0), (0, cx, -sx), (0, sx, cx)))
    ry = np.array(((cy, 0, sy), (0, 1, 0), (-sy, 0, cy)))
    rz = np.array(((cz, -sz, 0), (sz, cz, 0), (0, 0, 1)))
    value = np.eye(4)
    value[:3, :3], value[:3, 3] = rz @ ry @ rx, xyz
    return value


def smooth(value):
    """Return a clamped quintic transition with zero endpoint derivatives."""
    v = np.clip(value, 0.0, 1.0)
    return v * v * v * (10 + v * (-15 + 6 * v))


def between(time, start, stop):
    return float(smooth((time - start) / (stop - start)))


def track(time, keys):
    """Interpolate a sequence of position or scalar samples."""
    if time <= keys[0][0]:
        return np.asarray(keys[0][1], dtype=float)
    for (ta, a), (tb, b) in zip(keys[:-1], keys[1:], strict=True):
        if time <= tb:
            u = between(time, ta, tb)
            return np.asarray(a) * (1 - u) + np.asarray(b) * u
    return np.asarray(keys[-1][1], dtype=float)


def cycle_time(seconds):
    """Map three OP030 review shots onto the same 14 s cycle."""
    if seconds < 26:
        return 0.0
    return min((seconds - 26) % 14, 13.999)


def stock_position(row=0, column=0):
    return np.array((-0.18 + (column - 2) * 0.335, -0.99 + (row - 1.5) * 0.22, 0.825))


def op010_state(seconds):
    pick = stock_position(0, 0)
    place = np.array((0.0, 0.0, BODY_BOTTOM))
    high_pick, high_place = pick + (0, 0, 0.25), place + (0, 0, 0.25)
    high_pick[2] = high_place[2]
    position = track(
        seconds,
        (
            (0, high_pick),
            (1.6, pick),
            (2.8, pick),
            (4.4, high_pick),
            (6.8, high_place),
            (8.4, place),
            (9.8, place),
            (11.2, high_place),
        ),
    )
    grip = between(seconds, 1.6, 2.4) * (1 - between(seconds, 8.8, 9.6))
    payload = pick if seconds < 2.4 else position if seconds < 8.8 else place
    return position, grip, payload


def op020_state(seconds):
    t = max(0.0, min(seconds - 12, 14))
    pick = np.array((2.12, 0.38, 0.978))
    pre = np.array((2.496, -0.145, BODY_BOTTOM + 0.046))
    seat = pre + (0, 0.046, 0)
    position = track(
        t,
        (
            (0, pick + (0, 0, 0.16)),
            (1.8, pick),
            (2.6, pick),
            (3.8, pick + (0, 0, 0.16)),
            (5.8, pre + (0, 0, 0.14)),
            (7.0, pre),
            (8.8, pre),
            (10.0, seat),
            (10.8, seat),
            (12.4, seat + (0, 0, 0.16)),
        ),
    )
    # A small visible alignment search is an authored path, not force feedback.
    search = between(t, 7.0, 7.3) * (1 - between(t, 8.1, 8.5))
    position += search * np.array((0.002 * math.sin(9 * t), 0, 0.0015 * math.cos(9 * t)))
    grip = between(t, 1.8, 2.4) * (1 - between(t, 10.2, 10.8))
    payload = pick if t < 2.4 else position if t < 10.2 else seat
    return position, grip, payload, between(t, 8.8, 10.0) * (1 - between(t, 10.8, 12.0))


def a_state(seconds):
    t = cycle_time(seconds)
    pick = np.array((4.47, -0.43, 0.978))
    seat = np.array((4.745, 0.0, PART_Z))
    high = np.array((4.60, -0.22, 1.17))
    position = track(
        t,
        (
            (0, pick + (0, 0, 0.15)),
            (1.4, pick),
            (2.1, pick),
            (3.6, high),
            (4.8, seat + (0, 0, 0.14)),
            (5.8, seat),
            (11.1, seat),
            (12.2, seat + (0, 0, 0.17)),
        ),
    )
    grip = between(t, 1.4, 2.0) * (1 - between(t, 10.6, 11.1))
    payload = pick if t < 2.0 else position if t < 10.6 else seat
    feeder = np.array((5.07, -0.38, 1.025))
    first = seat + (0, -0.045, 0.002)
    second = seat + (0, 0.045, 0.002)
    tool = track(
        t,
        (
            (0, feeder + (0, 0, 0.12)),
            (1.4, feeder),
            (2.2, feeder),
            (3.8, feeder + (0, 0, 0.10)),
            (5.8, feeder + (0, 0, 0.10)),
            (6.3, first + (0, 0, 0.07)),
            (6.7, first),
            (7.7, first),
            (8.2, first + (0, 0, 0.23)),
            (8.6, second + (0, 0, 0.23)),
            (9.1, second),
            (11.1, second),
            (12.2, second + (0, 0, 0.17)),
        ),
    )
    return position, grip, payload, tool


def cable_frames(seconds):
    t = cycle_time(seconds)
    # The source lug and hand retain their dimensions. Opposing terminal
    # directions leave the mechanisms on separate sides of the compact case.
    stock = (np.array((6.92, 0.18, 1.025)), np.array((7.32, 0.18, 1.025)))
    final = (np.array((7.115, -0.045, CABLE_Z)), np.array((7.285, 0.045, CABLE_Z)))
    raised = (stock[0] + (0, 0, 0.12), stock[1] + (0, 0, 0.12))
    approach = (final[0] + (0, 0, 0.17), final[1] + (0, 0, 0.17))
    anchors = []
    for index in range(2):
        p = track(
            t,
            (
                (0, raised[index]),
                (1.6, stock[index]),
                (2.5, stock[index]),
                (3.8, raised[index]),
                (6.0, approach[index]),
                (7.2, final[index]),
                (11.6, final[index]),
                (12.8, final[index] + (0, 0, 0.20)),
            ),
        )
        angle0, angle1 = (-math.pi / 2, 0.0) if index == 0 else (math.pi / 2, math.pi)
        if index == 1:
            # A short lift after the simultaneous stock pickup separates the
            # wrist bodies during the turn. Both final release/lift times stay shared.
            p[2] += 0.040 * between(t, 3.8, 4.15) * (1 - between(t, 4.35, 5.1))
        angle = angle0 + (angle1 - angle0) * between(t, 3.8, 6.0)
        anchors.append(transform(p, (0, 0, angle)))
    grip = between(t, 1.6, 2.4) * (1 - between(t, 11.0, 11.6))
    payloads = []
    for i in range(2):
        if t < 2.4:
            pose = transform(stock[i], (0, 0, -math.pi / 2 if i == 0 else math.pi / 2))
        elif t >= 11.0:
            pose = transform(final[i], (0, 0, 0 if i == 0 else math.pi))
        else:
            pose = anchors[i].copy()
        payloads.append(pose)
    tool_feed = between(t, 7.2, 8.0) * (1 - between(t, 10.2, 11.0))
    return anchors, grip, payloads, tool_feed


def c_state(seconds):
    t = cycle_time(seconds)
    pick = np.array((9.28, -0.40, 0.988))
    seat = np.array((9.630, 0.025, BODY_BOTTOM + 0.066))
    position = track(
        t,
        (
            (0, pick + (0, 0, 0.17)),
            (1.7, pick),
            (2.4, pick),
            (3.7, pick + (0, 0, 0.17)),
            (5.5, seat + (0, 0, 0.13)),
            (7.0, seat + (0, 0, 0.014)),
            (8.8, seat),
            (9.8, seat),
            (11.5, seat + (0, 0, 0.17)),
        ),
    )
    grip = between(t, 1.7, 2.3) * (1 - between(t, 9.2, 9.8))
    payload = pick if t < 2.3 else position if t < 9.2 else seat
    return position, grip, payload


def b_tool_position(seconds, index):
    """Return a station spindle tip with outboard X parking and Z feed [m]."""
    t = cycle_time(seconds)
    endpoint = np.array((7.115, -0.045, CABLE_Z)) if index == 0 else np.array((7.285, 0.045, CABLE_Z))
    outboard = -0.28 if index == 0 else 0.45
    traverse = between(t, 7.2, 7.8) * (1 - between(t, 10.65, 11.0))
    feed = between(t, 7.8, 8.6) * (1 - between(t, 10.2, 10.65))
    return endpoint + (outboard * (1 - traverse), 0, LUG_PLATE_TOP_Z + 0.004 + 0.05 * (1 - feed))


def robot_targets(seconds, hand_roots):
    """Return six flange frames and the associated hand openings."""
    op020, g20, _, _ = op020_state(seconds)
    a, ga, _, tool = a_state(seconds)
    b, gb, _, _ = cable_frames(seconds)
    c, gc, _ = c_state(seconds)
    anchors = {"OP020": transform(op020), "A_hold": transform(a), "B_left": b[0], "B_right": b[1], "C": transform(c)}
    kinds = {"OP020": "H05", "A_hold": "H01", "B_left": "H04", "B_right": "H04", "C": "H05"}
    targets = {name: matrix @ hand_roots[kinds[name]] for name, matrix in anchors.items()}
    for name in ("B_left", "B_right"):
        length, angle = B_MOUNTS[name]
        targets[name] = targets[name] @ transform((0, 0, -length), (0, 0, angle))
    targets["A_tool"] = transform(tool + (0, 0, 0.48), (math.pi, 0, 0))
    return targets, {"OP020": g20, "A_hold": ga, "B_left": gb, "B_right": gb, "C": gc}, anchors
