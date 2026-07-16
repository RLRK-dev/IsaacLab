# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression controls for whole-route reward identity and escape guards.

The controls cover reward-design gate-2 FM4 (a stray cable loop must not
satisfy C1/C2 seating) and FM3 (losing the C1 crossing after G3 must remain
observable as a fail-closed condition). They also pin the optional recording
fields needed to derive the canonical C1 seat-segment identity.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_THREAD_DIR = Path(__file__).resolve().parents[1]
_ENVS_DIR = _THREAD_DIR / "envs"
for _path in (str(_ENVS_DIR), str(_THREAD_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import newton_route_env as nre  # noqa: E402
import route_executor as rex  # noqa: E402


def _env_with_pin_segment(pin_segment: int = 27):
    env = object.__new__(nre.NewtonRouteEnv)
    env._pin_seat_seg = pin_segment
    return env


def _c1_stray_loop_fixture() -> np.ndarray:
    """Return a cable whose stray loop is seated while the pinned span is outside C1."""
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 0] = 0.370
    cable[:, 1] = 0.300
    cable[:, 2] = 0.829

    # Stray loop: an unrestricted min-dx search incorrectly selects this in-groove crossing.
    cable[5] = (0.350, 0.160, 0.829)
    cable[6] = (0.350, 0.140, 0.829)

    # Routed/pinned span: segment 27 crosses C1Y but remains 20 mm outside the groove.
    cable[27] = (0.370, 0.160, 0.829)
    cable[28] = (0.370, 0.140, 0.829)
    return cable


def _c2_stray_loop_fixture() -> np.ndarray:
    """Return a cable with an outside routed C2 span plus an inside disconnected loop."""
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 0] = 0.450
    cable[:, 1] = 0.300
    cable[:, 2] = 0.829

    # C1 pin node -> C2 crossing is Y-monotone, but the routed crossing is 50 mm outside C2.
    for node in range(17, 28):
        cable[node, 1] = -0.005 + 0.015 * (node - 17)

    # Disconnected loop crosses C2Y inside the groove; its path from the C1 pin reverses in Y.
    cable[5] = (0.400, 0.010, 0.829)
    cable[6] = (0.400, -0.010, 0.829)
    return cable


def test_fm4_c1_uses_pin_identity() -> None:
    env = _env_with_pin_segment()
    dx, z_cross = env._seat_metrics(_c1_stray_loop_fixture(), nre._C1_XY)
    assert not env._seated_in_groove(dx, z_cross), (
        "FM4 regression: a C1 stray loop outside the pin-segment window satisfied the seat predicate"
    )


def test_fm4_c2_requires_monotone_connection() -> None:
    env = _env_with_pin_segment()
    dx, z_cross = env._seat_metrics(_c2_stray_loop_fixture(), nre._C2_XY)
    assert not env._seated_in_groove(dx, z_cross), (
        "FM4 regression: a C2 stray loop not Y-monotone-connected to the C1 pin satisfied the seat predicate"
    )


def test_fm3_no_crossing_remains_visible() -> None:
    env = _env_with_pin_segment()
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 1] = 0.300  # never crosses C1Y=0.150
    assert env._crossing_x_dev(cable) is None, (
        "FM3 regression: no-crossing collapsed to a numeric zero, making post-G3 escape fail-open"
    )
    assert not env._c1_escape_after_seat(cable, c1_latched=False), "pre-G3 no-crossing must remain valid en-route"
    assert env._c1_escape_after_seat(cable, c1_latched=True), "post-G3 no-crossing must fail closed as escape"


def test_pin_identity_fields_survive_recording_prepare() -> None:
    n_frames = rex._REC_LAST_CTRL_FRAME + 1
    rec = {
        "ee_pos_r": np.zeros((n_frames, 3), dtype=np.float32),
        "ee_pos_l": np.zeros((n_frames, 3), dtype=np.float32),
        "grip_cmd": np.zeros((n_frames, 2), dtype=np.float32),
        "phase_id": np.zeros(n_frames, dtype=np.int64),
        "cable_xyz": np.zeros((n_frames, 40, 3), dtype=np.float32),
        "held_seg_l": np.zeros(n_frames, dtype=np.int64),
        "pin_active": np.zeros(n_frames, dtype=np.int64),
        "pin_eqid": np.full(n_frames, -1, dtype=np.int64),
        "pinned_body": np.full(n_frames, -1, dtype=np.int64),
    }
    rec["pin_active"][100:] = 1
    rec["pin_eqid"][100:] = 27
    rec["pinned_body"][100:] = 55
    prepared = rex._prepare_recording(rec)
    for key in ("pin_active", "pin_eqid", "pinned_body"):
        assert key in prepared and np.array_equal(prepared[key], rec[key]), (
            f"recording preparation dropped {key}; C1 identity/pin onset cannot be wired"
        )


def main() -> None:
    test_fm4_c1_uses_pin_identity()
    test_fm4_c2_requires_monotone_connection()
    test_fm3_no_crossing_remains_visible()
    test_pin_identity_fields_survive_recording_prepare()
    print("ALL PASS: FM4 C1/C2 identity + FM3 no-crossing + recording pin-field preservation")


if __name__ == "__main__":
    main()
