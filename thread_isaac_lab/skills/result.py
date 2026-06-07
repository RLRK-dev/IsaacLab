# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""SkillResult enum — newton-free, imported by orchestrator + scripted_skills.

Split out of :mod:`scripted_skills` (Phase 5-1b C2) so the orchestrator
test harness can import :class:`SkillResult` without pulling in
``newton_routing_utils`` (which requires Newton to be installed).
"""

from __future__ import annotations

from enum import Enum


class SkillResult(Enum):
    """Outcome of a skill execution."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    FAIL = "fail"
    CABLE_DROP = "cable_drop"
    EXPLOSION = "explosion"
