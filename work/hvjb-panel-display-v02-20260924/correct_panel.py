# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Adjust only panel-hand symbols to the free upper band of the schematic board."""

import numpy as np
import probe_panel as probe

sample = probe.fix.old.base.sample


def hand_state(model, role):
    palm, left, right, _ = [model.scene.get_pose(node) for node in model.arms[role]["hand"]]
    point = palm[:3, 3] - palm[:3, :3] @ [0, 0, 0.18]
    gap = float(np.linalg.norm(left[:3, 3] - right[:3, 3]) - 0.032)
    yaw = float(np.arctan2(palm[1, 0], palm[0, 0]))
    return point, gap, yaw


def shift_b(model, source_t, height):
    if not 10.8 <= source_t < 48:
        return False
    if source_t < 36:
        weight = float(sample(source_t, [(10.8, 0), (11.7, 1), (34.5, 1), (36, 0)]))
    else:
        weight = float(sample(source_t, [(36, 0), (37.5, 1), (47, 1), (48, 0)]))
    if not weight:
        return False
    point, gap, yaw = hand_state(model, "B")
    point[2] += weight * (height - 0.16)
    model.oriented_hand("B", point, gap, yaw)
    return True


def shift_c(model, source_t, height):
    if not 32 <= source_t < 38.6:
        return False
    if source_t < 38:
        home = np.array([-0.80, -1.90, 1.62])
        panel = model.unit_origin(model.b_unit)
        target = panel + [-0.20, 0, height]
        point = sample(source_t, [(32, home), (33.5, target)])
        gap = float(sample(source_t, [(32, 0.20), (33.5, 0.20), (34, 0.048)]))
        yaw = float(sample(source_t, [(32, 0), (33.5, np.pi / 2)]))
    else:
        point, gap, yaw = hand_state(model, "C主")
        point[2] += float(sample(source_t, [(38, height - 0.16), (38.6, 0)]))
    model.oriented_hand("C主", point, gap, yaw)
    return True


def apply(model, source_t, height):
    actions = {}
    if shift_b(model, source_t, height):
        actions["B"] = "B_panel_symbol_upper_band"
    if shift_c(model, source_t, height):
        actions["C主"] = "C_panel_receive_and_release_symbol"
    return actions
