# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Reuse first-unit hand displays for the next unit and remove header display drift."""

import sys
from pathlib import Path

import numpy as np

OLD = Path(__file__).resolve().parent.parent / "hvjb-line-video-v03-20260921"
sys.path.insert(0, str(OLD))
import render_process as old  # noqa: E402

sample = old.base.sample


def next_a(model, source_t):
    if not 29 <= source_t < 44:
        return None
    home = np.array([-1.65, 1.1, 1.5])
    unit = model.unit_origin(model.a_next)
    target = unit + [0, 0, 0.045]
    if source_t < 32:
        # The first-unit 20.5..22 approach/open/close pattern, mapped to 29..32.
        point = sample(source_t, [(29, home), (31, target)])
        gap = float(sample(source_t, [(29, 0.24), (30, 0.78), (31, 0.78), (32, 0.62)]))
    elif source_t <= 43:
        point, gap = target, 0.62
    else:
        # Reuse the first-unit 27.7..29 release pattern within the old 43..44 departure.
        phase = 27.7 + (source_t - 43) * 1.3
        point = sample(phase, [(27.7, target), (28, target), (28.4, unit + [0, 0, 0.45]), (29, home)])
        gap = float(sample(phase, [(27.7, 0.62), (28, 0.78), (28.4, 0.78), (29, 0.24)]))
    model.oriented_hand("A", point, gap)
    return "A_next_unit_display"


def next_b(model, source_t):
    if not 36 <= source_t < 48:
        return None
    home = np.array([1.65, 1.1, 1.5])
    panel = model.unit_origin(model.b_next)
    target = panel + [0.20, 0, 0.16]
    if source_t < 38:
        # Reuse the first panel's 10.8..12 approach and turn within 36..38.
        phase = 10.8 + (source_t - 36) * 0.6
        point = sample(phase, [(10.8, home), (11.7, target)])
        gap = float(sample(phase, [(10.8, 0.20), (11.7, 0.20), (12, 0.048)]))
        yaw = float(sample(phase, [(10.8, 0), (11.7, np.pi / 2)]))
    elif source_t <= 47:
        point, gap, yaw = target, 0.048, np.pi / 2
    else:
        # Reuse the first panel's 34.5..36 release inside the old 47..48 departure.
        phase = 34.5 + (source_t - 47) * 1.5
        point = sample(phase, [(34.5, target), (35, target), (35.4, target + [0, 0, 0.4]), (36, home)])
        gap = float(sample(phase, [(34.5, 0.048), (35, 0.20)]))
        yaw = float(sample(phase, [(34.5, np.pi / 2), (35.4, np.pi / 2), (36, 0)]))
    model.oriented_hand("B", point, gap, yaw)
    return "B_next_panel_display"


def header_c(model, source_t):
    if not 50 <= source_t < 55:
        return None
    header = model.unit_origin(model.header)
    home = np.array([-0.80, -1.90, 1.62])
    point = sample(source_t, [(50, header), (54, header), (54.5, header), (55, home)])
    left, right = [model.scene.get_pose(node)[:3, 3] for node in model.arms["C主"]["hand"][1:3]]
    gap = float(np.linalg.norm(left - right) - 0.032)
    model.oriented_hand("C主", point, gap)
    return "C_header_follow_display"


def apply(model, source_t):
    actions = {}
    for role, action in (
        ("A", next_a(model, source_t)),
        ("B", next_b(model, source_t)),
        ("C主", header_c(model, source_t)),
    ):
        if action:
            actions[role] = action
    return actions
