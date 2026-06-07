# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Observation and action transforms for skill orchestration.

Implements clip-relative coordinate transform and Y-axis mirror for
handedness generalization across 5-clip routing.

Design doc: thread-vault/06-Knowledge/LL-Orchestration-Design.md

Obs layout (42D, xyzw quaternion convention):
    [0:3]   R clamp pos    [3:7]   R clamp quat    [7]   R finger
    [8:11]  L clamp pos    [11:15] L clamp quat    [15]  L finger
    [16:19] cable pos      [19:23] cable quat
    [23:26] clip pos       [26:30] clip quat
    [30:33] R ori error AA [33:36] R pos error
    [36:39] L ori error AA [39:42] L pos error

Action layout (12D):
    [0:3]  R pos delta     [3:6]  R rot delta (axis-angle)
    [6:9]  L pos delta     [9:12] L rot delta (axis-angle)
"""

import torch


def to_clip_relative(obs: torch.Tensor, clip_pos: torch.Tensor) -> torch.Tensor:
    """Convert absolute-position obs to clip-relative coordinates.

    Subtracts clip_pos from all position fields. Quaternions, finger openings,
    and error signals are unchanged (errors are already relative).

    Args:
        obs: (N, 42) observation tensor.
        clip_pos: (3,) or (N, 3) clip position in world frame [m].

    Returns:
        (N, 42) clip-relative observation.
    """
    out = obs.clone()
    if clip_pos.dim() == 1:
        clip_pos = clip_pos.unsqueeze(0)  # (1, 3) for broadcasting
    out[:, 0:3] -= clip_pos  # R arm pos
    out[:, 8:11] -= clip_pos  # L arm pos
    out[:, 16:19] -= clip_pos  # cable target pos
    out[:, 23:26] -= clip_pos  # clip pos -> ~[0,0,0]
    return out


def mirror_obs(obs: torch.Tensor) -> torch.Tensor:
    """Y-axis mirror + arm slot swap for InsertIntoClip at C2-C5.

    Makes LEFT-at-+Y configuration appear identical to RIGHT-at-+Y (C1)
    from the policy's perspective.

    Transforms applied:
        1. Arm slot swap: [0:8] <-> [8:16], [30:36] <-> [36:42]
        2. Y-negate all position Y components
        3. Y-mirror quaternions:  (qx,qy,qz,qw) -> (-qx,qy,-qz,qw)
        4. Y-mirror axis-angle:  (ax,ay,az) -> (-ax,ay,-az)
        5. Y-negate position error Y components

    Args:
        obs: (N, 42) observation tensor (should be clip-relative already).

    Returns:
        (N, 42) mirrored observation.
    """
    m = obs.clone()

    # 1. Arm slot swap
    m[:, 0:8] = obs[:, 8:16]
    m[:, 8:16] = obs[:, 0:8]
    m[:, 30:36] = obs[:, 36:42]
    m[:, 36:42] = obs[:, 30:36]

    # 2. Y-negate positions (index 1 in each pos block)
    m[:, 1] *= -1  # arm pos Y (was L, now in R slot)
    m[:, 9] *= -1  # arm pos Y (was R, now in L slot)
    m[:, 17] *= -1  # cable target pos Y
    m[:, 24] *= -1  # clip pos Y

    # 3. Y-mirror quaternions: negate qx and qz (xyzw convention)
    for qstart in (3, 11, 19, 26):
        m[:, qstart] *= -1  # qx
        m[:, qstart + 2] *= -1  # qz

    # 4. Y-mirror axis-angle errors: negate ax and az
    for aa_start in (30, 36):
        m[:, aa_start] *= -1  # ax
        m[:, aa_start + 2] *= -1  # az

    # 5. Y-negate position error Y components
    m[:, 34] *= -1  # R pos error Y (slot [33:36])
    m[:, 40] *= -1  # L pos error Y (slot [39:42])

    return m


def mirror_action(action: torch.Tensor) -> torch.Tensor:
    """Y-axis mirror + arm slot swap for 12D action output.

    Un-mirrors the policy output back to world-frame arm ordering.

    Args:
        action: (N, 12) action tensor from policy.

    Returns:
        (N, 12) world-frame action with original R/L arm ordering.
    """
    m = action.clone()

    # Arm slot swap: [0:6] <-> [6:12]
    m[:, 0:6] = action[:, 6:12]
    m[:, 6:12] = action[:, 0:6]

    # Y-negate position deltas (dy at index 1, 7)
    m[:, 1] *= -1
    m[:, 7] *= -1

    # Y-negate rotation deltas: rx and rz (indices 3,5 and 9,11)
    m[:, 3] *= -1
    m[:, 5] *= -1
    m[:, 9] *= -1
    m[:, 11] *= -1

    return m
