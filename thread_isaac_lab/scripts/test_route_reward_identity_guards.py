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
        "FM3 regression: no-crossing collapsed to a numeric zero in the obs channel"
    )
    dx, _ = env._seat_metrics(cable, nre._C1_XY)
    assert dx == env._SEAT_MISS_DX_M, "the identity instrument must return the MISS sentinel with no crossing"
    assert not env._c1_escape_after_seat(dx, c1_latched=False), "pre-G3 no-crossing must remain valid en-route"
    assert env._c1_escape_after_seat(dx, c1_latched=True), "post-G3 no-crossing must fail closed as escape"


def _i3_fail_open_fixture() -> np.ndarray:
    """Identity window has no C1Y crossing; a stray inside the 60mm drop bar is the only crossing.

    Pre-I3 the global guard saw the stray (dev +20mm < 60mm) and returned escape=False while the routed
    seat was gone -- a fail-open episode burn (gate-2 leg-3 finding 3, fixture a).
    """
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 0] = 0.370
    cable[:, 1] = 0.300
    cable[:, 2] = 0.829
    cable[5] = (0.370, 0.160, 0.829)  # stray: +20mm dev, outside the groove, inside the 60mm bar
    cable[6] = (0.370, 0.140, 0.829)
    return cable


def test_i3_lost_identity_crossing_escapes_despite_stray() -> None:
    env = _env_with_pin_segment()
    dx, _ = env._seat_metrics(_i3_fail_open_fixture(), nre._C1_XY)
    assert dx == env._SEAT_MISS_DX_M, "the stray must not satisfy the identity instrument"
    assert env._c1_escape_after_seat(dx, c1_latched=True), (
        "I3 regression: identity crossing lost but escape did not fire (fail-open episode burn)"
    )


def _i3_false_escape_fixture() -> np.ndarray:
    """Routed identity crossing in-lateral but out of z-band; a stray IN-band at +70mm dev (> 60mm bar).

    The pre-I3 global picker preferred the in-band stray (lexsort in-band primary) -> |70mm| > 60mm ->
    a false escape -10 against a legitimate state (gate-2 leg-3 finding 3, fixture b). The stray sits on
    segments outside the identity window {pin-1, pin}.
    """
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 0] = 0.370
    cable[:, 1] = 0.300
    cable[:, 2] = 0.900
    cable[27] = (0.350, 0.160, 0.900)  # routed crossing: dx=0, z out of band
    cable[28] = (0.350, 0.140, 0.900)
    cable[5] = (0.420, 0.160, 0.829)  # stray: +70mm dev, in z-band
    cable[6] = (0.420, 0.140, 0.829)
    return cable


def test_i3_stray_cannot_fake_escape() -> None:
    env = _env_with_pin_segment()
    dx, _ = env._seat_metrics(_i3_false_escape_fixture(), nre._C1_XY)
    assert dx <= 0.001, "the identity crossing is in-lateral"
    assert not env._c1_escape_after_seat(dx, c1_latched=True), (
        "I3 regression: an in-band stray at 70mm faked a lateral escape (false -10 termination)"
    )


def _c2_feed_drape_fixture() -> np.ndarray:
    """Routed side crosses C2Y 60mm outside the groove; the FEED-side free span drapes through it.

    Both spans are Y-monotone from the pin, so pre-I4 the walk admitted the feed side and the in-groove
    drape was credited as seated (gate-2 leg-3 finding 4).
    """
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 2] = 0.829
    for node in range(28):
        cable[node, 0] = 0.460  # routed side: 60mm outside C2X
        cable[node, 1] = 0.1575 - (27 - node) * 0.015  # crosses C2Y mid-segment 16
    for node in range(28, 40):
        cable[node, 0] = 0.400  # feed side: in-groove x
        cable[node, 1] = 0.1425 - (node - 27) * 0.015  # crosses C2Y mid-segment 36
    return cable


def test_i4_c2_feed_side_drape_rejected() -> None:
    env = _env_with_pin_segment()
    dx, z_cross = env._seat_metrics(_c2_feed_drape_fixture(), nre._C2_XY)
    assert not env._seated_in_groove(dx, z_cross), (
        "I4 regression: a feed-side drape through the C2 groove was credited as seated"
    )


def _c2_tail_return_fixture() -> np.ndarray:
    """The BELOW-pin excess tail re-crosses C2Y after the routed crossing (both on the routed side).

    Real-data shape (16/81 grid cells, e.g. cell_x0_y-5 final straddles {7, 20}): the Y-monotone walk --
    not the side constant -- is what rejects the tail's RETURN crossing; this pins the walk load-bearing.
    """
    cable = np.zeros((40, 3), dtype=np.float64)
    cable[:, 0] = 0.400
    cable[:, 2] = 0.829
    for node in range(12, 28):
        cable[node, 1] = 0.1425 - (27 - node) * 0.015  # pin 27 down to node 12: monotone, crosses at seg 17
    for node in range(12):
        cable[node, 1] = -0.0825 + (12 - node) * 0.015  # tail returns UP across C2Y: crosses at seg 6
    return cable


def test_i4_below_pin_tail_return_rejected_by_walk() -> None:
    env = _env_with_pin_segment()
    segs = env._seat_identity_segments(_c2_tail_return_fixture(), nre._C2_XY)
    assert 17 in segs, "the Y-monotone routed crossing segment must remain admitted"
    assert 6 not in segs, (
        "I4/FM4 regression: the tail's non-monotone RETURN crossing (below-pin side) must be walk-rejected"
    )


def test_escape_sentinel_exceeds_drop_bar() -> None:
    """The MISS sentinel must stay above the lateral drop bar or the crossing-lost escape leg dies."""
    assert nre.NewtonRouteEnv._SEAT_MISS_DX_M > nre.NewtonRouteEnv.DROP_LATERAL_DEV_MAX_M


def test_crossing_x_dev_is_obs_only() -> None:
    """I3 standing guard: the global (identity-unrestricted) crossing may feed obs [57] ONLY.

    Any reward/termination consumer reopens the gate-2 leg-3 finding-3 seam (ruling sec S3.1 requires
    zero such consumers).
    """
    import inspect

    for fn in (nre.NewtonRouteEnv._compute_rewards_dones_batch, nre.NewtonRouteEnv._c1_escape_after_seat):
        src = inspect.getsource(fn)
        assert "_crossing_x_dev" not in src, f"_crossing_x_dev consumed in {fn.__name__} (reward/done path)"


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


def _env_for_clear(world_count: int = 1):
    """Stub env for the ``_clear_c1_pin`` decision logic (the audit itself is monkeypatched per test).

    The stub solver deliberately has NO ``world_count`` attribute -- the B1 premise: the guard must
    read the env-authoritative ``_world_count``, never a solver getattr default (which is fail-open).
    """
    env = object.__new__(nre.NewtonRouteEnv)
    env._world_count = world_count
    env._c1_pin_witness = {"eq_id": 3}
    env._pin_seat_seg = 27
    env._pin_onset_frame = 2544
    env._route_rec_step_f = "identity-sentinel"

    class _Stub:
        pass

    solver = _Stub()
    solver.mj_model = object()
    mjd = _Stub()
    mjd.eq_active = np.zeros(8, dtype=np.int64)
    solver.mj_data = mjd
    env._solver = solver
    return env


def test_clear_c1_pin_clears_all_audited_fired() -> None:
    """L-C: the clear set is EXACTLY the audit's verified fired tuple, and the audit runs first.

    eq 5 is fired but withheld from the fake audit's return: the helper must clear only what the
    selector judged (model-state authority = the audit is the single selector; the real audit
    returns every fired candidate -- that integration is the probe's L-C4 leg).
    """
    env = _env_for_clear()
    env._solver.mj_data.eq_active[[3, 5, 7]] = 1
    seen_at_audit = {}
    real_audit = rex.audit_pin_anchors

    def _fake_audit(mjm, mjd):
        seen_at_audit["pre_clear"] = mjd.eq_active.copy()
        return (3, 7)

    rex.audit_pin_anchors = _fake_audit
    try:
        env._clear_c1_pin([0])
    finally:
        rex.audit_pin_anchors = real_audit
    assert list(seen_at_audit["pre_clear"][[3, 5, 7]]) == [1, 1, 1], "audit must run BEFORE any clear"
    expected = np.zeros(8, dtype=np.int64)
    expected[5] = 1
    assert np.array_equal(env._solver.mj_data.eq_active, expected), (
        "the returned fired set must be cleared and ONLY that set (adjacent state untouched)"
    )
    assert env._c1_pin_witness is None, "(a): the witness must reset per episode"
    assert (env._pin_seat_seg, env._pin_onset_frame, env._route_rec_step_f) == (27, 2544, "identity-sentinel"), (
        "identity is recording-derived and must NEVER be cleared (sec 21.11.1 coupling note)"
    )


def test_clear_c1_pin_guards() -> None:
    """L-C: 0-not-in-env_ids no-ops regardless of wc; wc!=1 with world 0 raises (env-authoritative)."""
    env = _env_for_clear(world_count=4)
    called = []
    real_audit = rex.audit_pin_anchors
    rex.audit_pin_anchors = lambda mjm, mjd: called.append(1) or ()
    try:
        # subset reset without world 0 -> out of scope, silent, even at wc=4 (the whole-config
        # wc>1 loudness is owned by the make_solver tripwire, not this helper).
        env._clear_c1_pin([1, 2])
        assert called == [] and env._c1_pin_witness is not None, "no world-0: helper must not touch anything"
        # wc=4 + world 0 -> RuntimeError from the env count; the stub solver has NO world_count
        # attribute, so a solver-getattr guard would silently pass here (pN B1 leg).
        assert not hasattr(env._solver, "world_count")
        try:
            env._clear_c1_pin([0, 1])
            raise AssertionError("wc=4 with world 0 in the reset must raise")
        except RuntimeError as e:
            assert "world_count==1" in str(e)
        assert called == [], "the wc guard must fire before the audit"
    finally:
        rex.audit_pin_anchors = real_audit


def test_clear_c1_pin_no_candidate_and_no_cpu_model() -> None:
    """L-C/(e): no active candidate = state no-op (audit still consulted); no mj_model = full no-op."""
    env = _env_for_clear()
    real_audit = rex.audit_pin_anchors
    rex.audit_pin_anchors = lambda mjm, mjd: ()
    try:
        env._clear_c1_pin([0])
        assert np.array_equal(env._solver.mj_data.eq_active, np.zeros(8, dtype=np.int64))
        assert env._c1_pin_witness is None, "(a) applies even when nothing fired"
        env2 = _env_for_clear()
        env2._solver.mj_model = None
        calls = []
        rex.audit_pin_anchors = lambda mjm, mjd: calls.append(1) or ()
        env2._clear_c1_pin([0])
        assert calls == [] and env2._c1_pin_witness is not None, "no CPU model: return before the audit"
    finally:
        rex.audit_pin_anchors = real_audit


def test_clear_c1_pin_readback_failure_raises() -> None:
    """L-C: a clear whose readback does not stick must die loud (the GPU-inert-mirror failure class)."""

    class _Sticky(np.ndarray):
        def __setitem__(self, key, value):  # a write that silently does not take
            return

    env = _env_for_clear()
    env._solver.mj_data.eq_active = np.ones(4, dtype=np.int64).view(_Sticky)
    real_audit = rex.audit_pin_anchors
    rex.audit_pin_anchors = lambda mjm, mjd: (2,)
    try:
        try:
            env._clear_c1_pin([0])
            raise AssertionError("an ignored eq_active write must raise on readback")
        except RuntimeError as e:
            assert "readback != 0" in str(e)
        assert env._c1_pin_witness is not None, "the witness must NOT be nulled on a failed clear"
    finally:
        rex.audit_pin_anchors = real_audit


def _pin_recording(n_frames: int) -> dict:
    """Minimal valid recording dict with a full pin witness (mirrors the V5 fixture shape)."""
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
    return rec


def test_prepare_recording_partial_pin_witness_raises() -> None:
    """L-C2: 2/3 pin keys must refuse -- a subset witness would derive identity from a broken contract."""
    rec = _pin_recording(rex._REC_LAST_CTRL_FRAME + 1)
    del rec["pinned_body"]
    try:
        rex._prepare_recording(rec)
        raise AssertionError("a partial pin witness must raise")
    except ValueError as e:
        assert "partial pin witness" in str(e) and "pinned_body" in str(e)


def test_prepare_recording_pin_frame_mismatch_raises() -> None:
    """L-C2: a pin field that is not one-per-frame must refuse (a silent ravel would shift the onset)."""
    rec = _pin_recording(rex._REC_LAST_CTRL_FRAME + 1)
    rec["pin_active"] = rec["pin_active"][:-1]
    try:
        rex._prepare_recording(rec)
        raise AssertionError("a pin-field frame-count mismatch must raise")
    except ValueError as e:
        assert "one value per frame" in str(e)


def test_prepare_recording_absent_pin_fields_pass_through() -> None:
    """L-C2: a recording with NO pin fields stays valid and prepares WITHOUT them (fail-closed identity)."""
    rec = _pin_recording(rex._REC_LAST_CTRL_FRAME + 1)
    for key in ("pin_active", "pin_eqid", "pinned_body"):
        del rec[key]
    prepared = rex._prepare_recording(rec)
    assert not any(key in prepared for key in ("pin_active", "pin_eqid", "pinned_body")), (
        "absent pin fields must stay absent (identity stays conservatively fail-closed)"
    )


def main() -> None:
    test_fm4_c1_uses_pin_identity()
    test_fm4_c2_requires_monotone_connection()
    test_fm3_no_crossing_remains_visible()
    test_pin_identity_fields_survive_recording_prepare()
    test_i3_lost_identity_crossing_escapes_despite_stray()
    test_i3_stray_cannot_fake_escape()
    test_i4_c2_feed_side_drape_rejected()
    test_i4_below_pin_tail_return_rejected_by_walk()
    test_escape_sentinel_exceeds_drop_bar()
    test_crossing_x_dev_is_obs_only()
    test_clear_c1_pin_clears_all_audited_fired()
    test_clear_c1_pin_guards()
    test_clear_c1_pin_no_candidate_and_no_cpu_model()
    test_clear_c1_pin_readback_failure_raises()
    test_prepare_recording_partial_pin_witness_raises()
    test_prepare_recording_pin_frame_mismatch_raises()
    test_prepare_recording_absent_pin_fields_pass_through()
    print(
        "ALL PASS: FM4 C1/C2 identity + FM3 no-crossing + recording pin-field preservation "
        "+ I3 same-instrument escape (fail-open/false-escape closed) + I4 routed-side (feed-drape/"
        "tail-return rejected) + sentinel>bar + obs-only crossing_x_dev + (a)(b) clear lifecycle "
        "(model-state authority / guards / readback) + pin-witness raise branches"
    )


if __name__ == "__main__":
    main()
