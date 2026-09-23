# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Repair schematic hand-display transitions without creating a robot trajectory."""

import sys
from pathlib import Path

import numpy as np

OLD = Path(__file__).resolve().parent.parent / "hvjb-line-video-v03-20260921"
sys.path.insert(0, str(OLD))
import render_process as old  # noqa: E402

sample = old.base.sample


def correct_a(model, source_t):
    """Use the existing pickup time and unit-holding pose for A's display."""
    home = np.array([-1.65, 1.1, 1.5])
    unit = model.unit_origin(model.a_unit)
    target = unit + [0, 0, 0.045]
    if 12.2 <= source_t < 13.5:
        # The old part started rising at 12.2 while the old hand waited until 12.5.
        part = model.scene.get_pose(model.part_a)[:3, 3]
        model.arm("A", part, 0.15)
        return "A_pickup_attachment"
    if 20.5 <= source_t < 22:
        start_gap = float(sample(20.5, [(19.7, 0.24), (21.5, 0.15)]))
        point = sample(source_t, [(20.5, home), (21.5, target)])
        gap = float(sample(source_t, [(20.5, start_gap), (21, 0.78), (21.5, 0.78), (22, 0.62)]))
        model.oriented_hand("A", point, gap)
        return "A_unit_approach"
    if 27.7 <= source_t < 29:
        # Reuse the 0.78 open display and 0.45 rise already used for this unit in S08.
        point = sample(source_t, [(27.7, target), (28, target), (28.4, unit + [0, 0, 0.45]), (29, home)])
        gap = float(sample(source_t, [(27.7, 0.62), (28, 0.78), (28.4, 0.78), (29, 0.24)]))
        model.oriented_hand("A", point, gap)
        return "A_unit_release"
    return None


def correct_b(model, source_t):
    """Turn the existing panel hand before pickup and open before returning home."""
    home = np.array([1.65, 1.1, 1.5])
    panel = model.unit_origin(model.b_unit)
    target = panel + [0.20, 0, 0.16]
    if 10.8 <= source_t < 12:
        point = sample(source_t, [(10.8, home), (11.7, target)])
        gap = float(sample(source_t, [(10.8, 0.20), (11.7, 0.20), (12, 0.048)]))
        yaw = float(sample(source_t, [(10.8, 0), (11.7, np.pi / 2)]))
        model.oriented_hand("B", point, gap, yaw)
        return "B_panel_approach"
    if 34.5 < source_t < 36:
        point = sample(source_t, [(34.5, target), (35, target), (35.4, target + [0, 0, 0.4]), (36, home)])
        gap = float(sample(source_t, [(34.5, 0.048), (35, 0.20)]))
        yaw = float(sample(source_t, [(34.5, np.pi / 2), (35.4, np.pi / 2), (36, 0)]))
        model.oriented_hand("B", point, gap, yaw)
        return "B_panel_release"
    return None


def correct_c(model, source_t, scene_id):
    """Turn the existing H03 symbol during approach rather than in one frame."""
    if scene_id == "S12" and 55 <= source_t < 56.3:
        point = model.scene.get_pose(model.arms["C主"]["hand"][0])[:3, 3] - [0, 0, 0.18]
        gap = float(sample(source_t, [(54.5, 0.35), (55.8, 0.22), (56.3, 0.083)]))
        yaw = float(sample(source_t, [(55, 0), (55.8, np.pi / 2)]))
        model.oriented_hand("C主", point, gap, yaw)
        return "C_busbar_approach"
    return None


def apply(model, source_t, scene_id):
    """Return the roles touched by display-only corrections at this sample."""
    applied = {}
    for name, action in (
        ("A", correct_a(model, source_t)),
        ("B", correct_b(model, source_t)),
        ("C主", correct_c(model, source_t, scene_id)),
    ):
        if action is not None:
            applied[name] = action
    return applied
