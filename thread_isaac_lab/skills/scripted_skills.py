# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Scripted skills for 43-STEP cable routing orchestrator.

Four scripted skills that handle non-RL steps in the routing pipeline:
  - TransportToClip: IK waypoint movement (Home, Lift, Transport, Descend)
  - ReClamp: Left finger full clamp (0.006 → 0.002)
  - HalfUnclampRelease: L half-open (→0.006) + R full-open (→0.04)
  - ClipConfirm: Wait and verify cable seated in groove

All skills use newton_routing_utils as the low-level interface.
Designed for use by RoutingOrchestrator (§14 RL-Routing-Design.md).
"""

from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Path setup: configs/ and scripts/ (for newton_routing_utils)
# ---------------------------------------------------------------------------
_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_config_dir = os.environ.get("THREAD_CONFIG_DIR", os.path.join(_base_dir, "configs"))
_scripts_dir = os.path.join(_base_dir, "scripts")
for _p in (_config_dir, _scripts_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from task_config import (  # noqa: E402
    CLIP_POSITIONS,
    FINGER_CLOSE_POS,
    FINGER_HALF_OPEN_POS,
    FINGER_OPEN_POS,
    GRIP_HALF_SPAN,
    PUSH_Z,
    TABLE_HEIGHT,
)

# GROOVE_CHECK_RADIUS lives in newton_routing_utils which unconditionally
# imports ``newton``. To keep skills/scripted_skills.py importable from
# environments without Newton (e.g. the orchestrator unit-test harness in
# ``env_isaaclab``), we delay this import until ``clip_confirm`` actually
# needs it (Phase 5-1b C2 unblock, 2026-04-25).


# ---------------------------------------------------------------------------
# Height constants (§2 RL-Routing-Design.md)
# ---------------------------------------------------------------------------
ROUTING_RISE_Z = TABLE_HEIGHT + 0.270  # 1.07: routing clip上空
REST_RISE_Z = TABLE_HEIGHT + 0.250  # 1.05: REST clip上空
HOME_Z = TABLE_HEIGHT + 0.320  # 1.12: Home高度


# ---------------------------------------------------------------------------
# SkillResult (shared with orchestrator; moved to skills.result in Phase 5-1b C2)
# ---------------------------------------------------------------------------
from .result import SkillResult  # noqa: E402, F401 — re-export for BC


# ---------------------------------------------------------------------------
# Waypoint computation helpers
# ---------------------------------------------------------------------------
def _clip_xy(clip_index: int) -> tuple[float, float]:
    """Get clip XY from CLIP_POSITIONS (0-indexed, C1=0)."""
    return CLIP_POSITIONS[clip_index][0], CLIP_POSITIONS[clip_index][1]


def _hand_positions_for_clip(clip_index: int) -> tuple[float, float, float, float]:
    """Compute L/R hand Y positions for a clip.

    Returns (l_x, l_y, r_x, r_y).
    """
    cx, cy = _clip_xy(clip_index)
    return cx, cy - GRIP_HALF_SPAN, cx, cy + GRIP_HALF_SPAN


def _rise_target(x: float, y: float, z: float | None = None) -> tuple[float, float, float]:
    """Create a target position at routing rise height."""
    return (x, y, z if z is not None else ROUTING_RISE_Z)


def _push_target(x: float, y: float) -> tuple[float, float, float]:
    """Create a target position at push/grasp height."""
    return (x, y, PUSH_Z)


# ---------------------------------------------------------------------------
# TransportToClip
# ---------------------------------------------------------------------------
def transport_to_clip(
    model,
    state,
    scene_info,
    solver,
    contacts,
    target_left: tuple[float, float, float],
    target_right: tuple[float, float, float],
    label: str = "TRANSPORT",
    converge_mm: float = 5.0,
) -> tuple[object, SkillResult]:
    """Move both arms to target positions via IK waypoint.

    Wraps newton_routing_utils.ik_move_both. Fingers unchanged.

    Args:
        model: Newton model.
        state: Current physics state.
        scene_info: Scene dict from build_scene.
        solver: VBD solver.
        contacts: Contact model.
        target_left: (x, y, z) for left EE.
        target_right: (x, y, z) for right EE.
        label: Log label.
        converge_mm: Convergence threshold [mm].

    Returns:
        (state, SkillResult).
    """
    # Import here to avoid circular dependency at module load
    from newton_routing_utils import ik_move_both

    state, success = ik_move_both(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=target_left,
        target_right=target_right,
        label=label,
        converge_mm=converge_mm,
    )
    if not success:
        return state, SkillResult.FAIL
    return state, SkillResult.SUCCESS


# ---------------------------------------------------------------------------
# Convenience wrappers for common TransportToClip patterns
# ---------------------------------------------------------------------------
def transport_home(model, state, scene_info, solver, contacts) -> tuple[object, SkillResult]:
    """Move both arms to home position (STEP 1, 43)."""
    home_l = (0.0, -0.10, HOME_Z)
    home_r = (0.0, 0.10, HOME_Z)
    return transport_to_clip(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=home_l,
        target_right=home_r,
        label="HOME",
    )


def transport_above_clip(
    model,
    state,
    scene_info,
    solver,
    contacts,
    clip_index: int,
    label: str = "ABOVE_CLIP",
) -> tuple[object, SkillResult]:
    """Move both arms above a clip at routing rise height.

    Convenience wrapper for approach from far (STEP 6,11,19,27,35).
    Target = clip hand positions at ROUTING_RISE_Z.
    """
    lx, ly, rx, ry = _hand_positions_for_clip(clip_index)
    return transport_to_clip(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=_rise_target(lx, ly),
        target_right=_rise_target(rx, ry),
        label=label,
    )


def transport_lift(
    model,
    state,
    scene_info,
    solver,
    contacts,
    clip_index: int,
    label: str = "LIFT",
) -> tuple[object, SkillResult]:
    """Lift both arms from push height to rise height after insertion.

    Convenience wrapper for post-insertion rise (STEP 10,18,26,34,42).
    Target = same as transport_above_clip. Phase A lift (STEP 5) uses
    transport_to_clip() directly with REST_CLIP coordinates.
    """
    lx, ly, rx, ry = _hand_positions_for_clip(clip_index)
    return transport_to_clip(
        model,
        state,
        scene_info,
        solver,
        contacts,
        target_left=_rise_target(lx, ly),
        target_right=_rise_target(rx, ry),
        label=label,
    )


# ---------------------------------------------------------------------------
# ReClamp(L) — left finger full clamp
# ---------------------------------------------------------------------------
def reclamp_left(
    model,
    state,
    scene_info,
    solver,
    contacts,
    n_steps: int | None = None,
    label: str = "RECLAMP_L",
) -> tuple[object, SkillResult]:
    """Re-clamp left finger from half-open (0.006) to full close (0.002).

    STEP 12, 20, 28, 36. Right finger unchanged.

    Args:
        model: Newton model.
        state: Current physics state.
        scene_info: Scene dict.
        solver: VBD solver.
        contacts: Contact model.
        n_steps: Physics frames for interpolation. Default: FINGER_CLOSE_STEPS.
        label: Log label.

    Returns:
        (state, SkillResult).
    """
    from newton_routing_utils import interpolate_fingers

    state = interpolate_fingers(
        model,
        state,
        scene_info,
        solver,
        contacts,
        left_target=FINGER_CLOSE_POS,
        right_target=None,  # keep current
        n_steps=n_steps,
        label=label,
    )
    return state, SkillResult.SUCCESS


# ---------------------------------------------------------------------------
# HalfUnclampRelease — L half-open + R full-open
# ---------------------------------------------------------------------------
def half_unclamp_release(
    model,
    state,
    scene_info,
    solver,
    contacts,
    n_steps: int | None = None,
    label: str = "HALF_UNCLAMP",
) -> tuple[object, SkillResult]:
    """Half-open left finger (→0.006) and fully open right (→0.04).

    STEP 8, 17, 25, 33, 41.

    Args:
        model: Newton model.
        state: Current physics state.
        scene_info: Scene dict.
        solver: VBD solver.
        contacts: Contact model.
        n_steps: Physics frames for interpolation. Default: FINGER_CLOSE_STEPS.
        label: Log label.

    Returns:
        (state, SkillResult).
    """
    from newton_routing_utils import interpolate_fingers

    state = interpolate_fingers(
        model,
        state,
        scene_info,
        solver,
        contacts,
        left_target=FINGER_HALF_OPEN_POS,
        right_target=FINGER_OPEN_POS,
        n_steps=n_steps,
        label=label,
    )
    return state, SkillResult.SUCCESS


# ---------------------------------------------------------------------------
# ClipConfirm — verify cable seated in groove
# ---------------------------------------------------------------------------
def clip_confirm(
    model,
    state,
    scene_info,
    solver,
    contacts,
    clip_index: int,
    settle_steps: int = 50,
    min_bodies_in_groove: int = 2,
    label: str = "CLIP_CONFIRM",
) -> tuple[object, SkillResult]:
    """Wait and verify cable is seated in clip groove.

    STEP 9, 16, 24, 32, 40.

    Args:
        model: Newton model.
        state: Current physics state.
        scene_info: Scene dict.
        solver: VBD solver.
        contacts: Contact model.
        clip_index: Which clip to check (0-indexed, C1=0).
        settle_steps: Physics frames to wait for settle.
        min_bodies_in_groove: Minimum cable bodies required in groove.
        label: Log label.

    Returns:
        (state, SkillResult). FAIL if insufficient bodies in groove after settle.
    """
    from newton_routing_utils import (
        GROOVE_CHECK_RADIUS,
        check_groove_insertion,
        hold_position,
    )

    state = hold_position(model, state, scene_info, solver, contacts, settle_steps)

    cx, cy = _clip_xy(clip_index)
    bodies_in_groove, min_dist_mm, _, _ = check_groove_insertion(
        state,
        scene_info,
        cx,
        cy,
        groove_radius=GROOVE_CHECK_RADIUS,
    )
    print(f"  [{label}] C{clip_index + 1}: {bodies_in_groove} bodies in groove, min_dist={min_dist_mm:.1f}mm")

    if bodies_in_groove >= min_bodies_in_groove:
        return state, SkillResult.SUCCESS
    return state, SkillResult.FAIL
