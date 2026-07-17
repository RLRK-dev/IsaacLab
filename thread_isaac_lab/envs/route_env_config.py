# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Config + contract surface for the env7 whole-route env-core (:class:`NewtonRouteEnv`).

This module holds ONLY (a) structure -- the 62D observation index map and the route-executor
interface contract -- and (b) the new parameters that are specific to the whole-route env-core and
do NOT belong to the task_config SSOT. It is the builder/converter/trainer contract for the C1->C2
whole-route DAPG env (mujoco-ko substrate, Newton 1.2.1 SolverMuJoCo, UR5ex2 + Robotiq koshape).

[!] SSOT DISCIPLINE (build plan sec 1:10, CRITICAL): every existing numeric value lives in
``task_config.py`` and is IMPORT-ONLY here -- referenced as ``task_config.NAME``, never duplicated.
A route param is defined here ONLY when it has no task_config home (a whole-route addition). An
import-time guard at the bottom asserts route-owned names do not shadow task_config SSOT names.

Obs 62D layout (build plan sec 1 obs row, spec v1.5g Rs 30d0066f0c) -- see the ``OBS_*`` map below::

    [0:42]  base proprio (mirror of newton_approach_cable_mujoco_env [0:42]; [16:19] REDEFINED)
    [42:48] phase one-hot(6)          [48]    held cable z            [49]  seated-seg d (scalar)
    [50]    within-phase progress     [51:53] next-clip xy            [53:55] per-arm contact flag
    [55:57] per-arm IK residual       [57]    crossing-x deviation    [58:60] axis-resolved seat
    [60:62] C1-retention (z_c1, flank-max)                            TOTAL = 62

Grounding: spec ``P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md`` (v1.5h) + build plan
``BUILD_PLAN_ENVCORE_COORD_20260706.md`` (sec 1/sec 12) + artifacts ``P2_REWARD_ARTIFACTS_W0C_DRAFT``.
"""

# --- SSOT import (import-only; robust to both package-path and env-sys.path import contexts) ------
try:
    from thread_isaac_lab.configs import task_config
except ImportError:  # imported via the env's sys.path (configs/ inserted as a top-level dir)
    import os as _os
    import sys as _sys

    _cfg_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "configs")
    if _cfg_dir not in _sys.path:
        _sys.path.insert(0, _cfg_dir)
    import task_config

# =====================================================================================================
# Observation 62D index map (a CONTRACT document -- unambiguous slices for builder/converter/trainer)
# =====================================================================================================
OBS_DIM = 62
N_ROUTE_PHASES = 6  # G1..G6 (N5: hardcoded 6-phase; N-clip repeat scheme is a future doc)

OBS_BASE = slice(0, 42)  # base proprio (mirror of the AC base obs block)
# Redefined/annotated semantics WITHIN the base block (see NewtonRouteEnv._compute_obs):
OBS_BASE_TARGET_SEG = slice(16, 19)  # CC2-CH5: lane-matched regrasp target (NOT argmin find_nearest)
OBS_BASE_R_POS_ERR = slice(33, 36)  # pre-computed pos-err ([warn] GROVE r12 ABSENT-IN-CODE until build-verified)
OBS_BASE_L_POS_ERR = slice(39, 42)
OBS_PHASE_ONEHOT = slice(42, 48)  # argmax(earned); base-scripted phase_id is the SOURCE (CC2-CH4)
OBS_HELD_CABLE_Z = 48  # [m] held cable z (op-rule 21 lift input)
OBS_SEATED_SEG_D = 49  # [m] phase-active clip seated-seg distance (base-scripted phase_id pin, CC2-CH4)
OBS_WITHIN_PHASE = 50  # [0,1] within-phase progress scalar (Markov aid, CC2-2)
OBS_NEXT_CLIP_XY = slice(51, 53)  # [m] next-clip XY (whole-route / 5-clip forward-compat, N5 scope)
OBS_PER_ARM_CONTACT = slice(53, 55)  # (R, L) contact flag -- telemetry/assertion ONLY, NOT a gate input (NEW-A)
OBS_R_CONTACT = 53
OBS_L_CONTACT = 54
OBS_PER_ARM_IK_RESID = slice(55, 57)  # [m] (R, L) IK residual magnitude
OBS_R_IK_RESID = 55
OBS_L_IK_RESID = 56
OBS_CROSSING_X_DEV = 57  # [m] near-clip crossing-x deviation (H-drape variable)
OBS_AXIS_SEAT = slice(58, 60)  # axis-resolved seat: [58] z-gap [m], [59] lateral [m]
OBS_SEAT_ZGAP = 58
OBS_SEAT_LATERAL = 59
OBS_C1_RETENTION = slice(60, 62)  # C1-retention live inputs (v1.5g), in SI [m] -- see unit note below
OBS_C1_REGION_Z = 60  # [m] C1-region cable z  (c1_retained_final input; < 0.840 required)
OBS_C1_FLANK_MAX_Z = 61  # [m] C1 flank-max cable z (c1_retained_final input; < 0.840 required)
# UNIT NOTE: [60]/[61] are stored in SI [m] (like every other obs dim) -- NOT mm. c1_retained_final is
# PREDICATE-equivalent to recount_strict_v2 (z < 0.840 m == z < 840 mm); only the storage/compare unit is m.

# =====================================================================================================
# New whole-route env params (build plan sec 12 CC5-1/CC5-5; NO task_config home -> defined here)
# =====================================================================================================
# hold-span = the ACHIEVED dual-grip arm separation (~92.4mm), coupled to the collision-sphere floor --
# NOT the commanded 88mm (= 2*task_config.GRIP_HALF_SPAN). Provenance: task_config.py:243 ("achieved
# sep 92.4mm") + :246 ("cable hold-span = the achieved sep (~92mm)"), coupled to COLLISION_SPHERE_RADII
# (task_config.py:244). NEW measured param; DoD10 RE-MEASURES it (validate, do not trust the constant).
HOLD_SPAN_ACHIEVED = 0.0924  # [m] achieved dual-grip EE-EE / cable hold-span
COMMANDED_SPAN = 2.0 * task_config.GRIP_HALF_SPAN  # [m] 0.088 commanded (structural INVARIANT#2), import-only

# route seat-sustain window. == task_config.K_INSERT (10) by design (InsertIntoClip seat sustain), but
# defined here (not aliased) because task_config.py is untouched and the route horizon differs.
K_ROUTE_SEAT = 10  # RL steps the C2 groove+settle predicate must hold for G6 (cf task_config.K_INSERT)

# --- W1-B2 HOLD calibration constants (Stage-A spec v0.8.1 sec 4.2; numbers = Rs W0-a adoption) --------
# All four are PROVISIONAL: derived from the single comp5 residual==0 trace (n=1). Re-derivation clauses:
# HOLD_THRESH / HOLD_RESUME come with the spec sec 8 per-cell/per-seed safe-side legs (B7); MAX_HOLD_STEPS
# is PROVISIONAL-UNMEASURED (spec sec 4.2 MED-6) -- re-derived from the B7 bounded-delta-injection probe,
# final numbers = Rs. Units: mm on the div_grip metric (spec sec 4.2), steps = RL steps.
HOLD_THRESH_MM = 15.0  # div_grip > thresh (strict) fires HOLD; healthy-domain max 10.56mm, ramp hits 15 at t343
HOLD_RESUME_MM = 12.0  # resume when div <= 12 (thresh - 3mm hysteresis > 2.84mm handover sawtooth)
HOLD_RESUME_K = 3  # ... OR K consecutive in-band (<= HOLD_THRESH_MM) steps (chatter/limit-cycle guard)
MAX_HOLD_STEPS = 24  # informative-only event above this hold_count; NO terminate (spec sec 4.2)

# whole-route horizon. Split from task_config.GRASP_TERMINAL_STEPS(200)/INSERT_TERMINAL_STEPS(200):
# C1->C2 is ~771 RL steps (canonical T=7707 frames / cadence 10) -> 900 (x1.17 margin, MED7). Defined
# here (not in task_config) to keep task_config.py untouched; DoD4 re-measures the horizon under DR.
ROUTE_TERMINAL_STEPS = 900  # max episode length; time_outs fires ONLY on reaching this

# =====================================================================================================
# Reward constants (build plan reward row / spec:68 / artifacts G1-G6). Sparse-primary, latched.
# =====================================================================================================
G_PHASE_BONUS = 5.0  # +5 for each of G1..G5 (latched-monotonic, fire-once, never-revoked)
G6_TASK_BONUS = 200.0  # +200 terminal SUCCESS (G6)
TIME_PENALTY = -0.01  # per RL step
TERM_PENALTY = -10.0  # explosion / drop terminate
# op-rule 22 budget: 5*5 + 200 = 225 positive vs 0.01*900 + 10 = 19 worst penalty -> ratio 1:11.8 (healthy).

# c1_retained_final low-wall threshold [m] (LOW_WALL_TOP): z_c1 < 0.840 and flank_max < 0.840.
# == 840mm (recount LOW_WALL_TOP, p9_recount_strict_v2.py:107 / recount_strict_v2.py:25,63-64); stored/
# compared in SI meters for obs-dim unit consistency (predicate-equivalent to the mm form).
C1_RETAINED_LOW_WALL_TOP_M = 0.840
C1_FLANK_WINDOW_M = 0.010  # |y - C1Y| <= 10mm flank window (recount FLANK_W / FLANK_WIN_M)

# c2_seated_honest = groove-membership + settle (NOT raw d<3mm alone -- CC2-CH2 claw-pin gameable).
# Mirrors the runner producer test_newton_clip_routing.py:4970-4971:
#   c2_in_groove := |cable_z_at_c2 - groove_z| <= C2_SETTLE_Z_TOL_MM
#   c2_seated_honest := (cable<->C2-wall dist <= C2_WALL_SEAT_TOL_MM) and c2_in_groove
# groove_z / seat-dist read task_config.GROOVE_CENTER_Z / task_config.T_GROOVE (import-only).
C2_SETTLE_Z_TOL_MM = 3.0  # settle band around groove-center z (runner :4970, |d| <= 3.0 mm)
C2_WALL_SEAT_TOL_MM = 0.5  # groove-wall seat distance (runner :4971, <= 0.5 mm)

# span-monitor tolerance around HOLD_SPAN_ACHIEVED (informative tier; cable 8mm retention physics, CC3-CH1).
HOLD_SPAN_TOL_M = 0.008

# =====================================================================================================
# C1->C2 route-scope GEOMETRY block (%12 systematic pin 2026-07-06). Values = canonical route env_gates
# VERBATIM (route_demo_raw_meta.json env_gates / resolved_clip_*_xy + route_c2_pin.json). The whole-route
# (C1->C2) work uses these route env-gate OVERRIDES, NOT the task_config 5-clip-array defaults. task_config
# stays UNTOUCHED (SSOT). The env-core mirrors these for BOTH (a) the seat/groove PREDICATE constant
# (ROUTE_GROOVE_Z) AND (b) the built C1 clip SCENE geometry (clip z += ROUTE_CLIP_FLOAT_Z) -- else a live
# episode drifts from the route (%12 flag: a built C1 20mm low breaks c1_retained's 840 bar / G3 seat vs
# scene). The sync-guard DoD asserts these == a canonical meta (drift tripwire). Reconciliation with the
# task_config 5-clip defaults is parked for Rs batch review.
# =====================================================================================================
ROUTE_C1_XY = (0.35, 0.150)  # [m] meta CLIP_X/CLIP_Y = resolved_clip_c1_xy (== task_config CLIP_POSITIONS[0]; no drift)
ROUTE_C2_XY = (0.40, 0.000)  # [m] meta CLIP2_X/CLIP2_Y = resolved_clip_c2_xy (Rs 07-05; != task_config (0.40, 0.075))
# Authorized route-clip centres -- the ONLY (cx, cy) [m] the clip-retention pin may anchor at (RS71 §0 INVARIANT
# #5 clip-only, Rs 2026-07-15; design RLENV_PIN_DESIGN_VTDESIGN_20260715 §15.1). ``authorize_clip_pin`` IMPORTS
# this set rather than taking a centre argument, so "clip only" is a mechanism, not caller discipline: a support
# jig (x=0.30, the cable's initial straight-pose fixture) is NOT here, so a frame-0 seat in one cannot be
# authorized (design §14.1). 5-clip generalisation = extend THIS one tuple; the geom-count assert then RAISEs
# until the scene actually builds that clip (deferral is mechanical, design §15.2).
ROUTE_CLIP_CENTERS = (ROUTE_C1_XY, ROUTE_C2_XY)
# C2-bound cable side from the C1 pin node, in cable-INDEX direction (-1: lower indices carry to C2; +1:
# higher). A route DESIGN constant (1 bit, frame/DR-invariant), NOT a runtime estimate and NOT an N-hop
# count (ruling REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING sec S3.2): the step-table fixes which cable end
# the route carries to C2. Structurally forced by (i) the cable build direction=(0,1,0) with node 0 = the
# low-Y end (newton_skill_env_base.py _build_cable) and (ii) ROUTE_C2_XY[1]=0.000 < ROUTE_C1_XY[1]=0.150
# above -- i.e. side = sign(C2Y - C1Y) under the Y-ascending build. Grounded empirically: all 313 canonical
# C2-seated frames select crossing segment 16 < pin 27, and the full 81-cell grid (per-cell pin seat node
# 25..34) has ZERO feed-side C2Y straddles in any frame (gate2_rerun_i3i4_probe leg C). The seat identity
# walk (_seat_identity_segments) admits only this side, so a feed-side free span draping through the C2
# groove can never be credited as seated (gate-2 leg-3 finding 4). Any FUTURE route (C3-C5 / other-end
# routing) must re-ground its own side constant and re-run the probe positive control; N-clip
# generalisation needs a per-hop side map (this constant is single-hop C1->C2 scope).
ROUTE_C2_SIDE_FROM_PIN = -1
ROUTE_CLIP_FLOAT_Z = 0.020  # [m] meta CLIP_FLOAT_Z: routing clips float 20mm above the table (SPACER-supported)
# Route seat/groove z = task_config base groove + float (== route_c2_pin.json groove_z_mm 829). Used by the
# seat/groove predicate (_seat_metrics) AND the built clip z; the two MUST agree (%12 build+predicate flag).
ROUTE_GROOVE_Z = task_config.GROOVE_CENTER_Z + ROUTE_CLIP_FLOAT_Z  # 0.809 + 0.020 = 0.829

# Seat-predicate bars (reward-design 2 interp fix; ruling REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING sec 2/sec 11).
# DERIVED from the built V-groove clip geometry (newton_skill_env_base.py _v_groove_clip_parts: lower walls at
# x = +/-0.009 with half-width hx 0.0015 -> inner face at |x| = 0.0075; lower-wall top - base-plate top =
# 0.020 - 0.005 = 0.015) + CABLE_RADIUS + ROUTE_GROOVE_Z. NOT from CLIP_GROOVE_INNER_RADIUS (the stale datum
# behind the old T_GROOVE=3mm). Same derivation as route_executor.py:3039/:3072/:3073 (lat_bar/z_hi/z_lo off
# the model), kept as route-scope config so the RL env does not touch the producer file.
# Seated (cable centre geometrically inside the groove) := |dx_at_y=clip_y| <= SEAT_LAT_BAR_M
#   and SEAT_Z_LO_M < z_cross < SEAT_Z_HI_M.
_GROOVE_WALL_INNER_M = 0.0075  # lower-wall inner face |x| (clip parts: 0.009 - hx 0.0015)
_GROOVE_WALL_HEIGHT_M = 0.015  # lower-wall top - base-plate top (clip parts: 0.020 - 0.005)
SEAT_LAT_BAR_M = _GROOVE_WALL_INNER_M - task_config.CABLE_RADIUS  # 0.0035 (3.5mm): cable centre max off-axis, in-groove
SEAT_Z_LO_M = ROUTE_GROOVE_Z - 2.0 * task_config.CABLE_RADIUS  # 0.821: floor_top - R; below this = cable under the clip
SEAT_Z_HI_M = SEAT_Z_LO_M + _GROOVE_WALL_HEIGHT_M  # 0.836: wall_top - R; above this = cable over the rim

# (d-a) live-geometric pin trigger (charter sec 8.10.1 / sec 8.11.2; prereg PIN_D_TRIGGER v0.6). The FF-branch pin
# fires when the identity cable body DWELLS in a route clip's capture volume AT DEPTH for K consecutive physics
# frames, replacing the (a)(b) recorded-onset replay. Route-invariant, frozen.
PIN_TRIGGER_DWELL_K = 3  # consecutive physics frames of (capture AND depth) required before the pin fires
# Fire only when the seat has descended to z <= groove datum + CABLE_RADIUS/2. A rim-height catch (~835.7mm) leaves
# only ~0.3mm to the retention ceiling (SEAT_Z_HI_M 836mm) and the eq elastic-restores out of the groove (charter
# sec 8.11.2 REVISE); this depth gate keeps >=5mm retention margin. Existing constants only -- no new literal.
Z_FIRE_DEPTH_M = ROUTE_GROOVE_Z + task_config.CABLE_RADIUS / 2.0  # 0.829 + 0.002 = 0.831

# =====================================================================================================
# Route-executor interface contract v1 (build plan sec 6 + sec 12 CC5-2; PINNED)
# =====================================================================================================
ROUTE_MODE_NOMINAL = "nominal"  # stub: fixed nominal per-step target (env-core skeleton smoke)
ROUTE_MODE_RECORDED_REPLAY = "recorded_replay"  # replay recorded canonical per-step targets (DoD 3/6/10/9a/13)


class RouteInterfaceV1:
    """Contract the whole-route env-core expects from the route-executor (the NEXT staged component).

    The env-core owns obs/action/reward/termination; the route-executor owns the phase clock and the
    per-step ABSOLUTE base target (fork-(iv) 6D abs-target, LEDGER ADOPTED). The env-core alpha-6D
    residual is a per-step OFFSET added to ``target_6d`` (non-accumulating). At the env-core stage the
    route is a STUB (fixed nominal target); the real route-executor (``_run_mujoco_grasp_route``, a
    locked-runner monolith) connects next.

    Single-source rule (CC5-2): ``is_dual_grip_window`` MUST come from the base grip-schedule via this
    interface -- the env-core must NOT re-derive a phase->window table (that reintroduces the G3-gap =
    a second drift door). The (b') projection gate reads this boolean ALONE (grip-schedule, fail-safe);
    the both-arm contact obs [53:55] is telemetry, NOT a gate input (NEW-A fail-OPEN fix).
    """

    def reset_to_phase(self, k: int, world_ids: list[int] | None = None) -> None:
        """Fork to phase ``k``'s precomputed state-bank (spec sec 2-F2 (b); interface v2, Stage-A §4.1 H6).

        Args:
            k: phase index in ``[0, N_ROUTE_PHASES)`` to fork to. Stub = no-op record.
            world_ids: worlds to fork (v2, W1-B1). ``None`` = ALL worlds — byte-identical to the v1
                scalar-``k`` contract (additive extension, not a breaking change). A list restores only
                those worlds' banked tiles (per-world curriculum fork; consumer = the env done-reset).
        """
        raise NotImplementedError

    def step_target(self, t: int) -> tuple:
        """Return the per-step route packet for RL step ``t``.

        Args:
            t: RL step index within the episode.

        Returns:
            A 4-tuple ``(target_6d, phase_id, per_arm_grip_2vec, is_dual_grip_window)``:
              target_6d: absolute base EE targets ``[R_xyz, L_xyz]`` [m], shape [6] (non-accumulating).
              phase_id: current phase index in ``[0, N_ROUTE_PHASES)`` (base-owned G1..G6 clock).
              per_arm_grip_2vec: scripted per-arm grip command ``(R, L)`` (close/open servo predicate).
              is_dual_grip_window: base-script-sourced bool -- the SOLE (b') projection gate input.
        """
        raise NotImplementedError

    def query(self, t_episode: int, world_id: int, live_state_view: dict) -> tuple:
        """Oracle query (interface v2, W1-B2; Stage-A spec v0.8.1 sec 4.3): the trainer-facing packet.

        Read-only: the ONLY side effect anywhere in the oracle is the sync_state update, and that happens
        in the separate post-physics update (not here) -- query never advances a clock, never fires or
        resumes HOLD, never writes physics/control state.

        Args:
            t_episode: episode-clock step (telemetry; the packet is computed at the env-owned route_t
                carried in ``live_state_view`` -- the route clock is single-source, spec sec 4.1).
            world_id: world index.
            live_state_view: env-supplied per-world view; required keys ``route_t`` (int). (Cable state /
                G1-latch flow through the post-physics sync update, not through query.)

        Returns:
            A 6-tuple ``(target_6d, phase_id, per_arm_grip_2vec, is_dual_grip_window, validity_mask,
            sync_state)``:
              target_6d / phase_id / per_arm_grip_2vec / is_dual_grip_window: as :meth:`step_target`;
                under HOLD the grip-derived fields evaluate at the frozen chunk END frame (sec 4.2 N3).
              validity_mask: per-phase state-blind mask [float32 scalar for the CURRENT phase] -- 1.0
                where the base target is cable-state-derived, 0.0 for frozen-waypoint phases; consumed
                trainer-side only (weighting), never changes env behavior.
              sync_state: dict ``{"mode": "MARCH"|"HOLD", "hold_count": int, "div_grip": float [mm],
                "route_t": int}``.
        """
        raise NotImplementedError


# =====================================================================================================
# SSOT discipline guard: route-owned param names must NOT shadow task_config SSOT names (import-time)
# =====================================================================================================
_ROUTE_OWNED_PARAM_NAMES = {
    "HOLD_SPAN_ACHIEVED",
    "K_ROUTE_SEAT",
    "ROUTE_TERMINAL_STEPS",
    "G_PHASE_BONUS",
    "G6_TASK_BONUS",
    "TIME_PENALTY",
    "TERM_PENALTY",
    "C1_RETAINED_LOW_WALL_TOP_M",
    "C1_FLANK_WINDOW_M",
    "C2_SETTLE_Z_TOL_MM",
    "C2_WALL_SEAT_TOL_MM",
    "HOLD_SPAN_TOL_M",
    "ROUTE_C1_XY",
    "ROUTE_C2_XY",
    "ROUTE_CLIP_CENTERS",
    "ROUTE_CLIP_FLOAT_Z",
    "ROUTE_GROOVE_Z",
    "SEAT_LAT_BAR_M",
    "SEAT_Z_LO_M",
    "SEAT_Z_HI_M",
    "PIN_TRIGGER_DWELL_K",
    "Z_FIRE_DEPTH_M",
    "HOLD_THRESH_MM",
    "HOLD_RESUME_MM",
    "HOLD_RESUME_K",
    "MAX_HOLD_STEPS",
}
_COLLIDING = {n for n in _ROUTE_OWNED_PARAM_NAMES if hasattr(task_config, n)}
assert not _COLLIDING, (
    f"route_env_config route-owned params collide with task_config SSOT names {_COLLIDING}: "
    "rename here or import from task_config (numeric params are single-home in task_config.py)."
)
