# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Env-side wrappers (composition pattern; no env-file modification).

Per CLAUDE.md / state.md §4 禁止事項: ``env file 改変禁止``. Wrappers in
this package compose existing env classes via dependency injection and
extend obs / reward / step behavior non-invasively.

Phase 5-4 deliverables (T-Vision-Fusion L1.A.4):

- :mod:`vision_obs_assembler` — 45D → 50D Late Fusion obs assembler
  (skeleton; impl pending ``CC-L1A-Phase-5-4-Impl``)

R6 boundary: this layer is env-aware (reads env-computed 45D obs +
ee_pos derivation), so cannot live in ``estimators/``. One-way import
from ``estimators/`` only — wrappers consume estimator output, never
the other way.
"""
