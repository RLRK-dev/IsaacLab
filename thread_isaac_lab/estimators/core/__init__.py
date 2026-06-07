# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Estimator core sub-package.

R6 module boundary: this package MUST NOT import newton, env, or
WristCameraManager. Enforced by AST lint test
(``tests/test_estimator_module_boundary.py``) per v3.2 Appendix H §H.3.
"""

# Intentionally minimal — no imports from newton / env / wrist_camera_manager.
