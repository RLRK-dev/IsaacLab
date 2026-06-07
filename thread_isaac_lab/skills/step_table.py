# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""43-STEP routing table — maps each STEP to its skill and parameters.

Source: RL-Routing-Design.md §2.3 STEP→Skill Complete Mapping.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import Enum

_config_dir = os.environ.get(
    "THREAD_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"),
)
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)
from task_config import (  # noqa: E402
    CLIP_POSITIONS,
    GRIP_HALF_SPAN,
    REST_CLIP_X,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

from .scripted_skills import ROUTING_RISE_Z, REST_RISE_Z, HOME_Z, PUSH_Z  # noqa: E402


class SkillName(Enum):
    """All skill names (RL + scripted + wait)."""

    # RL skills
    APPROACH_CABLE = "ApproachCable"
    CLAMP = "Clamp"
    INSERT_INTO_CLIP = "InsertIntoClip"
    UNCLAMP = "Unclamp"
    AERIAL_REGRASP = "AerialRegrasp"

    # Scripted skills
    TRANSPORT = "TransportToClip"
    RECLAMP_L = "ReClamp(L)"
    HALF_UNCLAMP_RELEASE = "HalfUnclamp+Release"

    # Wait
    CLIP_CONFIRM = "ClipConfirm"


class StepType(Enum):
    RL = "RL"
    SCRIPTED = "S"
    WAIT = "W"


@dataclass
class StepDef:
    """Definition of a single routing STEP."""

    step_id: int
    skill: SkillName
    step_type: StepType
    clip_index: int | None = None      # 0-indexed (C1=0). None = no clip target
    target_left: tuple[float, float, float] | None = None
    target_right: tuple[float, float, float] | None = None
    l_finger: float | None = None      # target finger pos. None = keep current
    r_finger: float | None = None
    description: str = ""


# ---------------------------------------------------------------------------
# Waypoint helpers
# ---------------------------------------------------------------------------
def _clip_xy(ci: int) -> tuple[float, float]:
    return CLIP_POSITIONS[ci][0], CLIP_POSITIONS[ci][1]


def _hand_ys(ci: int) -> tuple[float, float]:
    """Return (l_y, r_y) for a clip."""
    _, cy = _clip_xy(ci)
    return cy - GRIP_HALF_SPAN, cy + GRIP_HALF_SPAN


def _rise(ci: int) -> tuple[tuple, tuple]:
    cx, cy = _clip_xy(ci)
    ly, ry = _hand_ys(ci)
    return (cx, ly, ROUTING_RISE_Z), (cx, ry, ROUTING_RISE_Z)


def _push(ci: int) -> tuple[tuple, tuple]:
    cx, cy = _clip_xy(ci)
    ly, ry = _hand_ys(ci)
    return (cx, ly, PUSH_Z), (cx, ry, PUSH_Z)


def _home() -> tuple[tuple, tuple]:
    return (0.0, -0.10, HOME_Z), (0.0, 0.10, HOME_Z)


# ---------------------------------------------------------------------------
# Table builder
# ---------------------------------------------------------------------------
def _build_phase_a() -> list[StepDef]:
    """Phase A: Initial grasp (STEP 1-5).

    Uses REST_CLIPS X=0.15 and rest rise Z=1.05 (not routing clip values).
    See RL-Routing-Design.md §2 Z値変更 notes.
    """
    h_l, h_r = _home()
    # Phase A: cable rests on REST clips (X=0.15). Hand Y matches C1 body 26/34.
    cable_above_l = (REST_CLIP_X, WIDE_LEFT_Y, REST_RISE_Z)
    cable_above_r = (REST_CLIP_X, WIDE_RIGHT_Y, REST_RISE_Z)

    return [
        StepDef(1, SkillName.TRANSPORT, StepType.SCRIPTED,
                target_left=h_l, target_right=h_r, description="Home位置"),
        StepDef(2, SkillName.TRANSPORT, StepType.SCRIPTED,
                target_left=cable_above_l, target_right=cable_above_r,
                description="ケーブル上空"),
        StepDef(3, SkillName.APPROACH_CABLE, StepType.RL,
                description="approach (finger OPEN)"),
        StepDef(4, SkillName.CLAMP, StepType.RL,
                description="L+R同時クランプ"),
        StepDef(5, SkillName.TRANSPORT, StepType.SCRIPTED,
                target_left=cable_above_l, target_right=cable_above_r,
                description="リフト"),
    ]


def _build_phase_b() -> list[StepDef]:
    """Phase B: C1 routing (STEP 6-10)."""
    ci = 0  # C1
    rise_l, rise_r = _rise(ci)
    push_l, push_r = _push(ci)
    return [
        StepDef(6, SkillName.TRANSPORT, StepType.SCRIPTED, clip_index=ci,
                target_left=rise_l, target_right=rise_r, description="C1上空搬送"),
        StepDef(7, SkillName.INSERT_INTO_CLIP, StepType.RL, clip_index=ci,
                description="C1 groove押込"),
        StepDef(8, SkillName.HALF_UNCLAMP_RELEASE, StepType.SCRIPTED, clip_index=ci,
                description="L半開放+R全開放"),
        StepDef(9, SkillName.CLIP_CONFIRM, StepType.WAIT, clip_index=ci,
                description="C1ラッチ確認"),
        StepDef(10, SkillName.TRANSPORT, StepType.SCRIPTED, clip_index=ci,
                target_left=rise_l, target_right=rise_r, description="C1上昇"),
    ]


def _build_clip_routing(ci: int, step_offset: int) -> list[StepDef]:
    """C2-C5 common pattern (8 STEP/clip).

    Args:
        ci: Clip index (1=C2, 2=C3, 3=C4, 4=C5).
        step_offset: First STEP number (11, 19, 27, 35).
    """
    rise_l, rise_r = _rise(ci)
    push_l, push_r = _push(ci)
    return [
        StepDef(step_offset + 0, SkillName.TRANSPORT, StepType.SCRIPTED, clip_index=ci,
                target_left=rise_l, target_right=rise_r, description=f"C{ci+1}上空移動"),
        StepDef(step_offset + 1, SkillName.RECLAMP_L, StepType.SCRIPTED, clip_index=ci,
                description="L再クランプ"),
        StepDef(step_offset + 2, SkillName.AERIAL_REGRASP, StepType.RL, clip_index=ci,
                description="R再把持approach"),
        StepDef(step_offset + 3, SkillName.CLAMP, StepType.RL, clip_index=ci,
                description="R把持"),
        StepDef(step_offset + 4, SkillName.INSERT_INTO_CLIP, StepType.RL, clip_index=ci,
                description="groove押込"),
        StepDef(step_offset + 5, SkillName.CLIP_CONFIRM, StepType.WAIT, clip_index=ci,
                description=f"C{ci+1}ラッチ確認"),
        StepDef(step_offset + 6, SkillName.HALF_UNCLAMP_RELEASE, StepType.SCRIPTED,
                clip_index=ci, description="L半開放+R全開放"),
        StepDef(step_offset + 7, SkillName.TRANSPORT, StepType.SCRIPTED, clip_index=ci,
                target_left=rise_l, target_right=rise_r, description="上昇"),
    ]


def _build_phase_e() -> list[StepDef]:
    """Phase E: Completion (STEP 43). L finger opens fully (0.006→0.04)."""
    h_l, h_r = _home()
    return [
        StepDef(43, SkillName.TRANSPORT, StepType.SCRIPTED,
                target_left=h_l, target_right=h_r,
                l_finger=0.04, description="Home復帰 + L finger open"),
    ]


def build_step_table() -> list[StepDef]:
    """Build the full 43-STEP routing table.

    Returns:
        List of 43 StepDef, ordered by step_id.
    """
    steps = []
    steps.extend(_build_phase_a())       # STEP 1-5
    steps.extend(_build_phase_b())       # STEP 6-10
    steps.extend(_build_clip_routing(1, 11))  # C2: STEP 11-18
    steps.extend(_build_clip_routing(2, 19))  # C3: STEP 19-26
    steps.extend(_build_clip_routing(3, 27))  # C4: STEP 27-34
    steps.extend(_build_clip_routing(4, 35))  # C5: STEP 35-42
    steps.extend(_build_phase_e())       # STEP 43

    assert len(steps) == 43, f"Expected 43 steps, got {len(steps)}"
    return steps


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
STEP_TABLE = build_step_table()
STEP_BY_ID = {s.step_id: s for s in STEP_TABLE}
