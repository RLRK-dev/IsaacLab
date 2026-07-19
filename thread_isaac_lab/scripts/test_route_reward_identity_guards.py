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
import route_env_config as rc  # noqa: E402
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
    # (d-a): a full witness (the trigger populates fire_step/fired_at_frame/dwell_count/seat_world) plus the
    # mismatch counter the extended clear reads; the clear also snapshots _last_pin_record before the weld is
    # destroyed. eq_id 3 vs the tests' fired sets makes these clears show a (harmless) class 2/3 mismatch.
    env._c1_pin_witness = {
        "eq_id": 3,
        "fire_step": 246,
        "fired_at_frame": 2468,
        "dwell_count": 3,
        "seat_world": [0.35, 0.15, 0.83064],
    }
    env._pin_seat_seg = 27
    env._pin_onset_frame = 2544
    env._route_rec_step_f = "identity-sentinel"
    env._pin_mismatch_total = 0
    env._c1_pin_dwell = 3

    class _Stub:
        pass

    solver = _Stub()
    solver.mj_model = object()
    mjd = _Stub()
    mjd.eq_active = np.zeros(8, dtype=np.int64)
    solver.mj_data = mjd
    env._solver = solver
    return env


def test_clear_c1_pin_raises_on_any_audited_fired() -> None:
    """c6 fail-loud semantics (Rs 2026-07-19): pin FIRING is removed, so an audited fired eq at the
    episode boundary is evidence of a surviving upstream kinematic writer -- the boundary must
    RAISE, never silently disarm (a clean-up write would mask the violation and would itself be
    the last eq_active writer). Audit still runs FIRST; eq state must be left untouched as
    evidence. Migrated from test_clear_c1_pin_clears_all_audited_fired (pN c6-reverify B2)."""
    env = _env_for_clear()
    env._solver.mj_data.eq_active[[3, 5, 7]] = 1
    seen_at_audit = {}
    real_audit = rex.audit_pin_anchors

    def _fake_audit(mjm, mjd):
        seen_at_audit["pre"] = mjd.eq_active.copy()
        return (3, 7)

    rex.audit_pin_anchors = _fake_audit
    try:
        try:
            env._clear_c1_pin([0])
            raise AssertionError("an audited fired eq must raise (pin firing is removed)")
        except RuntimeError as e:
            assert "pin firing is REMOVED" in str(e) and "[3, 7]" in str(e)
    finally:
        rex.audit_pin_anchors = real_audit
    assert list(seen_at_audit["pre"][[3, 5, 7]]) == [1, 1, 1], "audit must run BEFORE the verdict"
    assert list(env._solver.mj_data.eq_active[[3, 5, 7]]) == [1, 1, 1], (
        "the boundary must NOT write eq_active (evidence preserved, no disarm)"
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


# test_clear_c1_pin_readback_failure_raises: RETIRED (pN c6-reverify B2 per-test disposition).
# It asserted the disarm WRITE's readback (GPU-inert-mirror class); c6 removed the write entirely
# (boundary raises on any fired eq), so there is no readback surface left to test. The fired-eq
# raise path is covered by test_clear_c1_pin_raises_on_any_audited_fired. Historical body:
# git a004f2ce66 and earlier.


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


# --- (d-a) live-geometric trigger unit legs (prereg PIN_D_TRIGGER v0.6 sec 5 / sec 5a) --------------------------


class _FakeSolver:
    """A plain solver stand-in that accepts attribute assignment (for a seeded ``_route_clip_capture_cache``)."""


class _FakeBodyQ:
    def __init__(self, arr: np.ndarray):
        self._arr = arr

    def numpy(self) -> np.ndarray:
        return self._arr


class _FakeState0:
    def __init__(self, arr: np.ndarray):
        self.body_q = _FakeBodyQ(arr)


def _env_for_trigger(seat_seg: int = 27, seat_xyz=(0.35, 0.15, 0.8306)):
    """Stub env exercising the REAL ``_maybe_activate_c1_pin`` with monkeypatched capture/authorizer.

    ``rex.clip_capture_check`` / ``rex.authorize_clip_pin`` are replaced per test; this fixture only wires the env
    state the method reads: the flag, the witness latch, the identity ordinal, the dwell counter, the body_q
    snapshot source, and the episode clock. Returns ``(env, bq, seat_body)`` so a test can poison the source.
    """
    env = object.__new__(nre.NewtonRouteEnv)
    env._route_c1_pin = True
    env._c1_pin_witness = None
    env._pin_seat_seg = seat_seg
    env._c1_pin_dwell = 0
    env._route_rec_step_f = np.arange(4000, dtype=np.int64)  # step_f[t] == t (fired_at_frame bookkeeping only)
    env._cable_bodies = [np.arange(10, 50, dtype=int)]  # 40 cable body ids; the seat body carries the target world
    seat_body = int(env._cable_bodies[0][seat_seg])
    bq = np.zeros((64, 7), dtype=np.float64)
    bq[seat_body, :3] = seat_xyz
    env._state_0 = _FakeState0(bq)
    env._solver = _FakeSolver()
    env.episode_length_buf = np.array([246], dtype=np.int64)  # episode-relative fire_step source
    return env, bq, seat_body


def test_pin_da_capture_check_exists_and_shares_cache() -> None:
    """L-C(d): clip_capture_check exists and consumes the SAME memoized clip cache the authorizer reads (identity)."""
    assert hasattr(rex, "clip_capture_check"), "the (d-a) trigger's capture helper must exist"
    solver = _FakeSolver()
    solver._route_clip_capture_cache = ((0.35, 0.15, (1, 2, 3, 4, 5), 0.015), (0.40, 0.0, (6, 7, 8, 9, 10), 0.015))
    assert rex.clip_capture_check(solver, (0.35, 0.15, 0.829)) is True, "in-volume C1 seat is captured"
    assert rex.clip_capture_check(solver, (0.9, 0.9, 0.829)) is False, "a far point is not captured"
    assert rex._clip_capture_cache(solver) is solver._route_clip_capture_cache, "the cache is memoized (identity)"


def test_pin_da_dwell_reset_on_gap() -> None:
    """L-C(d)(i): K-1 True frames then a False frame resets the dwell; firing needs K FRESH consecutive frames."""
    env, _bq, _sb = _env_for_trigger()
    seq = iter([True] * (rc.PIN_TRIGGER_DWELL_K - 1) + [False] + [True] * rc.PIN_TRIGGER_DWELL_K)
    fired = {"n": 0}

    def _auth(solver, sb, sw):
        fired["n"] += 1
        return {"eq_id": 4, "seat_world": [float(x) for x in sw]}

    real_check, real_auth = rex.clip_capture_check, rex.authorize_clip_pin
    rex.clip_capture_check = lambda solver, sw: next(seq)
    rex.authorize_clip_pin = _auth
    try:
        for _f in range(rc.PIN_TRIGGER_DWELL_K - 1):
            env._maybe_activate_c1_pin([0], _f)
        assert env._c1_pin_dwell == rc.PIN_TRIGGER_DWELL_K - 1 and env._c1_pin_witness is None
        env._maybe_activate_c1_pin([0], 100)  # the gap frame
        assert env._c1_pin_dwell == 0, "a single gap must reset the dwell counter"
        for _f in range(rc.PIN_TRIGGER_DWELL_K):
            env._maybe_activate_c1_pin([0], 200 + _f)
        assert fired["n"] == 1 and env._c1_pin_witness is not None, "fires only after re-accumulating K"
    finally:
        rex.clip_capture_check, rex.authorize_clip_pin = real_check, real_auth


def test_pin_da_fire_once_at_k_consecutive() -> None:
    """L-C(d)(ii): K consecutive (capture AND depth) frames fire exactly once; the witness latch blocks re-fire."""
    env, _bq, _sb = _env_for_trigger()
    fired = {"n": 0}

    def _auth(solver, sb, sw):
        fired["n"] += 1
        return {"eq_id": 4, "seat_world": [float(x) for x in sw]}

    real_check, real_auth = rex.clip_capture_check, rex.authorize_clip_pin
    rex.clip_capture_check = lambda solver, sw: True
    rex.authorize_clip_pin = _auth
    try:
        for _f in range(rc.PIN_TRIGGER_DWELL_K - 1):
            env._maybe_activate_c1_pin([0], _f)
            assert env._c1_pin_witness is None, "must not fire before K consecutive frames"
        env._maybe_activate_c1_pin([0], rc.PIN_TRIGGER_DWELL_K - 1)  # the K-th frame
        assert env._c1_pin_witness is not None and fired["n"] == 1, "fire exactly at K"
        assert env._c1_pin_witness["fire_step"] == 246, "fire_step is episode-relative (episode_length_buf)"
        assert env._c1_pin_witness["dwell_count"] == rc.PIN_TRIGGER_DWELL_K
        env._maybe_activate_c1_pin([0], rc.PIN_TRIGGER_DWELL_K)  # a further frame
        assert fired["n"] == 1, "fire-once: the witness latch blocks a second authorize"
    finally:
        rex.clip_capture_check, rex.authorize_clip_pin = real_check, real_auth


def test_pin_da_depth_leg_gates_fire() -> None:
    """L-C(d)(vii): captured but ABOVE Z_FIRE_DEPTH_M never fires; dropping to the bar makes it accumulate + fire."""
    env, bq, seat_body = _env_for_trigger(seat_xyz=(0.35, 0.15, rc.Z_FIRE_DEPTH_M + 0.004))  # rim height
    real_check, real_auth = rex.clip_capture_check, rex.authorize_clip_pin
    rex.clip_capture_check = lambda solver, sw: True
    rex.authorize_clip_pin = lambda solver, sb, sw: {"eq_id": 4, "seat_world": [float(x) for x in sw]}
    try:
        for _f in range(rc.PIN_TRIGGER_DWELL_K + 2):
            env._maybe_activate_c1_pin([0], _f)
        assert env._c1_pin_witness is None and env._c1_pin_dwell == 0, "above the depth bar the pin must not fire"
        bq[seat_body, 2] = rc.Z_FIRE_DEPTH_M  # drop to the bar
        for _f in range(rc.PIN_TRIGGER_DWELL_K):
            env._maybe_activate_c1_pin([0], 100 + _f)
        assert env._c1_pin_witness is not None, "at/below the depth bar (with capture) it fires"
    finally:
        rex.clip_capture_check, rex.authorize_clip_pin = real_check, real_auth


def test_pin_da_identity_none_no_eval() -> None:
    """L-C(d)(iv): _pin_seat_seg None short-circuits before any capture evaluation (fail-closed, no fire)."""
    env, _bq, _sb = _env_for_trigger()
    env._pin_seat_seg = None
    seen = {"check": 0}

    def _check(solver, sw):
        seen["check"] += 1
        return True

    real_check = rex.clip_capture_check
    rex.clip_capture_check = _check
    try:
        for _f in range(rc.PIN_TRIGGER_DWELL_K + 1):
            env._maybe_activate_c1_pin([0], _f)
        assert seen["check"] == 0 and env._c1_pin_witness is None, "identity None must not even evaluate capture"
    finally:
        rex.clip_capture_check = real_check


def test_pin_da_fire_target_is_identity_body() -> None:
    """L-C(d)(v): the body handed to the authorizer is EXACTLY the identity seat body (cable_bodies[0][seg])."""
    seg = 27
    env, _bq, seat_body = _env_for_trigger(seat_seg=seg)
    got = {}

    def _auth(solver, sb, sw):
        got["seat_body"] = sb
        return {"eq_id": 4, "seat_world": [float(x) for x in sw]}

    real_check, real_auth = rex.clip_capture_check, rex.authorize_clip_pin
    rex.clip_capture_check = lambda solver, sw: True
    rex.authorize_clip_pin = _auth
    try:
        for _f in range(rc.PIN_TRIGGER_DWELL_K):
            env._maybe_activate_c1_pin([0], _f)
        assert got["seat_body"] == seat_body == int(env._cable_bodies[0][seg]), "fire target must be the identity body"
    finally:
        rex.clip_capture_check, rex.authorize_clip_pin = real_check, real_auth


def test_pin_da_same_snapshot_poison() -> None:
    """L-C(d)(vi): the authorizer receives the K-reaching snapshot, not a re-read (same-snapshot, sec 2-6a).

    The check double POISONS the body_q source on the K-reaching frame, AFTER the trigger has copied the seat. A
    re-reading trigger would then hand the authorizer the poisoned value; this impl copies once and passes that
    copy to both, so the authorizer must see the PRE-poison position (a value-only assert could not fail).
    """
    orig_xyz = (0.35, 0.15, 0.8306)
    env, bq, seat_body = _env_for_trigger(seat_xyz=orig_xyz)
    state = {"n": 0}
    got = {}

    def _check(solver, sw):
        state["n"] += 1
        if state["n"] == rc.PIN_TRIGGER_DWELL_K:  # poison AFTER this frame's snapshot was taken
            bq[seat_body, :3] = (9.9, 9.9, 9.9)
        return True

    def _auth(solver, sb, sw):
        got["sw"] = np.asarray(sw, dtype=np.float64).copy()
        return {"eq_id": 4, "seat_world": [float(x) for x in sw]}

    real_check, real_auth = rex.clip_capture_check, rex.authorize_clip_pin
    rex.clip_capture_check, rex.authorize_clip_pin = _check, _auth
    try:
        for _f in range(rc.PIN_TRIGGER_DWELL_K):
            env._maybe_activate_c1_pin([0], _f)
        assert "sw" in got and np.allclose(got["sw"], orig_xyz), (
            "authorizer must receive the pre-poison K-reaching snapshot (a re-read would deliver 9.9)"
        )
    finally:
        rex.clip_capture_check, rex.authorize_clip_pin = real_check, real_auth


def test_pin_da_check_quiet_outside_volume() -> None:
    """L-C2: capture False every frame -> no raise, no fire, dwell pinned at 0 (quiet return, not an exception)."""
    env, _bq, _sb = _env_for_trigger()
    real_check = rex.clip_capture_check
    rex.clip_capture_check = lambda solver, sw: False
    try:
        for _f in range(20):
            env._maybe_activate_c1_pin([0], _f)  # must not raise
        assert env._c1_pin_witness is None and env._c1_pin_dwell == 0
    finally:
        rex.clip_capture_check = real_check


def test_pin_da_broken_selector_raises_in_check() -> None:
    """L-C2: a cached clip whose count is outside {5,6} makes clip_capture_check raise BrokenSelector (sec 2-6b-ii)."""
    solver = _FakeSolver()
    solver._route_clip_capture_cache = ((0.35, 0.15, (1, 2, 3), 0.015), (0.40, 0.0, (6, 7, 8, 9, 10), 0.015))
    try:
        rex.clip_capture_check(solver, (0.35, 0.15, 0.829))
        raise AssertionError("a broken cached clip count must raise BrokenSelector")
    except rex.BrokenSelector as e:
        assert "has 3" in str(e), "the tripwire must name the wrong count"


def test_pin_da_mjm_none_flag_on_raises() -> None:
    """L-C2 (sec 2-6-iii): clip_capture_check on a solver with no CPU model raises RuntimeError (fail-loud)."""

    class _NoModel:
        mj_model = None
        mj_data = None

    try:
        rex.clip_capture_check(_NoModel(), (0.35, 0.15, 0.829))
        raise AssertionError("a solver with no mj_model must raise (never a silent no-fire)")
    except RuntimeError as e:
        assert "no mj_model" in str(e)


def test_pin_da_mismatch_class_fixtures() -> None:
    """L-I: witness<->fired classes 1 (bypass), 2 (divergence), 3 (concurrent) are detected; agreement = 0."""
    env = _env_for_clear()
    env._c1_pin_witness = None
    assert env._pin_mismatch_class((5,)) == 1, "eq fired, no witness = class 1 bypass"
    assert env._pin_mismatch_class(()) == 0, "nothing fired, no witness = agreement"
    env._c1_pin_witness = {"eq_id": 3}
    assert env._pin_mismatch_class((5, 6)) == 2, "witness eq not in fired = class 2 divergence"
    assert env._pin_mismatch_class(()) == 2, "witness present, weld vanished = class 2"
    assert env._pin_mismatch_class((3, 6)) == 3, "witness eq fired + a second pin = class 3 concurrent"
    assert env._pin_mismatch_class((3,)) == 0, "witness eq is the only fired pin = agreement"


def test_pin_da_n1n7_semantics_unchanged() -> None:
    """Invariance (baseline AND landed): clip_capture_predicate keeps its P1/P2 accept + N1-N4 reject legs.

    The (d-a) refactor extracts a shared cache but does NOT touch clip_capture_predicate, so these legs are
    invariant by construction. Full N5-N7 mechanism invariance is re-verified by re-running the controls script
    (L-C2, needs a built scene); this pins the pure-predicate core both the trigger and the authorizer consume.
    """
    c1x, c1y = rc.ROUTE_C1_XY
    lat, ylo, yhi, yw = rc.SEAT_LAT_BAR_M, rc.SEAT_Z_LO_M, rc.SEAT_Z_HI_M, 0.015
    cases = [
        ((c1x, c1y, 0.82968), True),  # P1 golden seat
        ((c1x, c1y, 0.830), True),  # P2 arch float
        ((c1x, c1y, 0.8809), False),  # N1 aerial 880.9mm
        ((c1x, c1y, 0.816), False),  # N2 under the clip
        ((c1x + 0.004, c1y, 0.829), False),  # N3 lateral 4mm > 3.5mm
        ((c1x, c1y + 0.020, 0.829), False),  # N4 domain 20mm > 15mm
    ]
    for seat, expect in cases:
        ok, _ = rex.clip_capture_predicate(seat, c1x, c1y, lat, yw, ylo, yhi)
        assert ok is expect, f"predicate leg changed for {seat}: got {ok}, want {expect}"


def test_pin_da_reasons_payload_content() -> None:
    """Invariance (baseline AND landed): NotInAnyRouteClip carries the per-clip failing-leg reasons (CC6-7).

    A type / accept-reject-only check would let a reasons-payload regression through; both versions build this
    exception with the per-clip reason list, so this pins the payload content directly.
    """
    exc = rex.NotInAnyRouteClip(
        (0.30, 0.05, 0.81),
        rc.ROUTE_CLIP_CENTERS,
        ["(0.35, 0.15):lateral |dx|=50.00>3.50mm", "(0.4, 0.0):domain"],
    )
    msg = str(exc)
    assert "lateral |dx|=50" in msg and "domain" in msg, "per-clip reasons must appear in the message"
    assert "INVARIANT #5" in msg, "the clip-only authorization must be named"


def test_pin_da_audit_independent_rescan() -> None:
    """Invariance: audit_pin_anchors stays a solver-cache-INDEPENDENT live rescan (sec 2-6b).

    The audit takes ``(mjm, mjd)`` -- not the solver -- so it CANNOT read the solver clip cache; it rescans via
    clip_geoms_at on every reset. That independence is the design value (a who-wrote-it-agnostic witness that does
    not trust the fire path's cache). On baseline the cache does not exist (trivially holds); on landed this pins
    that the audit was not 'helpfully' switched onto the cache.
    """
    import inspect

    params = list(inspect.signature(rex.audit_pin_anchors).parameters)
    assert params == ["mjm", "mjd"], f"audit must take (mjm, mjd), not the solver/cache: got {params}"
    src = inspect.getsource(rex.audit_pin_anchors)
    assert "_route_clip_capture_cache" not in src and "clip_capture_check" not in src, (
        "the audit must not consume the fire-path cache/check -- it rescans live (independence, sec 2-6b)"
    )
    assert "clip_geoms_at" in src, "the audit must rescan clip geoms live"


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
    test_pin_da_capture_check_exists_and_shares_cache()
    test_pin_da_dwell_reset_on_gap()
    test_pin_da_fire_once_at_k_consecutive()
    test_pin_da_depth_leg_gates_fire()
    test_pin_da_identity_none_no_eval()
    test_pin_da_fire_target_is_identity_body()
    test_pin_da_same_snapshot_poison()
    test_pin_da_check_quiet_outside_volume()
    test_pin_da_broken_selector_raises_in_check()
    test_pin_da_mjm_none_flag_on_raises()
    test_pin_da_mismatch_class_fixtures()
    test_pin_da_n1n7_semantics_unchanged()
    test_pin_da_reasons_payload_content()
    test_pin_da_audit_independent_rescan()
    print(
        "ALL PASS: FM4 C1/C2 identity + FM3 no-crossing + recording pin-field preservation "
        "+ I3 same-instrument escape (fail-open/false-escape closed) + I4 routed-side (feed-drape/"
        "tail-return rejected) + sentinel>bar + obs-only crossing_x_dev + (a)(b) clear lifecycle "
        "(model-state authority / guards / readback) + pin-witness raise branches + (d-a) live-geometric "
        "trigger (dwell/depth/fire-once/identity/target/same-snapshot/quiet/broken-selector/mjm-none/"
        "mismatch classes) + N1-N7 predicate + reasons payload + audit cache-independence"
    )


if __name__ == "__main__":
    main()
