# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""R0 -- does the existing control class converge on UR15-B's targets?  Convergence only; static class.

Authority: Rs1 (the human), 2026-09-14, Q1 verbatim 「認可する。p0が作り、pZが独立に検証・実行する。」 with the scope
「物理ステップを進めず、実行副作用のあるdriverをimportしない静的検査に限定します。収束確認と、衝突・把持・動的追従の
成立は区別します。」  Spec = P11_UR15B_CONTROLLER_DESIGN_20260913.md section 10 (row R0), 11, 17.1, 17.6 condition (i),
17.7 (targets' source) @ 7427c1764c; pre-registration = pZ PZ_R0_CONVERGENCE_LEG_PREREG_20260916.md rows 1-11 + 1' with
addenda 2-4.  Written by p0; executed and judged by pZ (p0 runs py_compile only).  Follow-ups of the chain court
(kickoff 09-16 item 16): (a) the whole 14-function closure is copied, nothing is stubbed; (b) rows 2-5 bind to the
grasp targets as section 17.7 decides them (see Targets), the settled run-time values are solved as extra reported rows.

WHAT THIS IS.  The wired driver's per-arm 6D damped-least-squares solver and every function it reaches --
`solve_ik -> pose_menu, _wrap, _rdes, pinch, touching, sigma_min -> wrist_jac, column_gap, path_mast_min, arm_pair_min,
path_arm_min, furniture_gap, path_furniture_min` (the closure of pZ's addendum 2 item 1) -- is copied below VERBATIM
from the landed driver blob 84a372439c59 (commit 96e9ece175; the same statements are byte-identical in the D4 blob
d2bc133e1320 @ 3370f7a872, the pre-registration's base), together with the driver's own rules for `ARMB`
(`_own_bodies`), `AXFIX` (`_measure_axfix`) and the grasp targets (`cable_at`).  Copy fidelity = AST equality with a
negative control (one literal changed reads unequal; section 17.6 condition (i)), checked outside this file (the record
section names the check).  The ONE permitted rebinding (prereg row 1 / 1', 30 module globals per addendum 3) is the set
of module globals that closure reads: they are bound per side to a COMPOSED model built by
`ur15_gripper_mirror_acceptance.build_side` (one arm + its ko hand on its mount, C-2 constants, no column, no cable,
no table, no other arm).  Where the driver's rule is model-free its assignment is pasted verbatim (`LIM`, `_MASTNAMES`,
`GRASP_CENTRE_X`, the three mutable dicts); where it reads the model it is evaluated verbatim on the composed model
inside `_bind` (`GNAME`, `ARMG`, `FURNG`, `COLG`, `COLFREE`); where it names the driver's bodies by side prefix (`QADR`,
`VADR`, `PAD`, `TOOLB` by `{t}_`/`{t}g_`, `ARMB` by `_own_bodies(f"{t}_") | _own_bodies(f"{t}g_")`) the same rule is
applied with the composed model's prefixes `a_`/`g_`.  On this model `FURNG` and `COLG` come out EMPTY by the driver's
own comprehensions (no saddle/table geoms, no mast geom names), so `column_gap`/`path_mast_min` run and find nothing;
`touching` runs on the contacts of the composed model; `arm_pair_min`/`path_arm_min` are behind `other is not None`,
`furniture_gap`/`path_furniture_min` behind the env switches `FURNITURE`/`ARM_PATH`, none of which this file sets.
Nothing in this file steps physics: the copied loop calls mj_kinematics / mj_comPos / mj_forward only, the cell dump is
read at its initial state with mj_forward only, and `mujoco.mj_step` is wrapped by a counter that the report prints
(must read 0).

WHAT IT DECIDES.  Per target row (the L and R columns of the driver's STEP table, rows 2-18) and per side, whether
`solve_ik` returns a converged pose under the wired test (`pe <= 0.002 m` and `re <= re_max`, tested inside the copied
function), with the wired defaults `tries=None` (full menu, twice), `iters=300`, `re_max=0.05`, `near=None`, `other=None`,
`quiet=True` (gates prints only), ONE fixed seed shared by both sides, and the arm started at the spec's `HOME_POSE`
(fingers 0), the start pZ's instrument used.  The bar (section 10 R0): rows where L converges and R does not = 0;
R converged = 0 -> section 11 STOP-and-report.  Negative control (prereg row 8): the R rows solved on the L model,
recorded whether or not it differs (pZ addendum 3 measured that it does not fire).

WHAT IT DOES NOT SHOW.  「収束のみ／衝突・把持・動的追従は未証明」 -- collision avoidance, grasp, dynamic tracking and the
mast/furniture/other-arm clearances are NOT measured here (those are the authorized run, #69, with pB/pC); and per pZ
addendum 3, convergence does not discriminate a correct UR15-B from the rotated copy -- that is the static legs' work.
Stop-cause tag on every row: {none, controller non-convergence, instrument calibration stop, other}.

Targets (section 17.7, p11's decision).  STEP rows 6-18 resolve from ur15_cell_spec constants exactly as the driver
writes them (C1, C2, GRIP_HALF_SPAN, Z_RISE_ROUTE, Z_SEAT = seat_z(FLOAT_Z), RX_MID = mean(C1[0], C2[0])).  Rows 2-5 use
GL/GR, which the driver measures on the live cable: at run time STEPS commands the `:2812-2813` form -- x, y, z all =
the centre of the cable link nearest the commanded x (`cable_at`, :1221), NOT the `:1241` form (commanded x).  BINDING
value here = the driver's own `cable_at` evaluated on the emitted cell's rest state (the dump `_steps_cell_full.xml`
written by the driver at import, :446; loaded, `mj_forward` at its initial state, before any settle) -- path (b-1) --
cross-checked against the closed form from cell constants -- path (b-2): link i rests at
c_i = (x0 + (i + 1/2) * CABLE_SEG, REST_Y, REST_TOP + CABLE_R) with x0 = -CABLE_SEG * CABLE_N / 2 (:336-:337), and
i = argmin |c_i.x - (GRASP_CENTRE_X -/+ GRIP_HALF_SPAN)|.  The two paths must agree to <= 1e-9 in value and in link
number, else the instrument STOPS (tag 「instrument calibration stop」, exit 2) -- a mismatch would mean the dump is not
the cell the constants describe.  Expected by section 17.7: GL = (0.1125, 0.28, 0.954) (cab27), GR = (0.1875, 0.28,
0.954) (cab32); both paths, the link numbers, the effective GRASP_CENTRE_X / WORK_ROW_DY and the dump's sha256 are
printed.  REPORTED, outside the denominator: the settled run-time values of the C-2 run record (path (a); the U0 run,
_gen/dod_c2_20260810/run.log :93 「re-measured after the approach」, sha256 04599b84e34be51ec906662f0d92aa8349eae833034c3a7e8d070d6c808b8868, driver c737f6974e at
that time) GL = (0.0986, 0.28, 0.9488), GR = (0.1886, 0.28, 0.951), solved as four extra rows per side tagged
「settled example (U0)」, with the settle offset (a) - (b) printed per side in three components.
R0-ii (section 17.8 (b), p11's decision; a row of R0, not a substitute for R1/R1').  Prediction from the identity joint
map (section 5 D1) with per-side AXFIX (section 6 D2): solving the mirror image Mx*p = (-x, y, z) of an L target on the
right side gives q_R == q_L on a correct UR15-B when seed, start and attitude index are the same.  Form: for every row
r in 2..18 (targets = section 17.7's L column and its mirror MxL) and every attitude index k in 0..len(pose_menu)-1,
the SAME call `solve_ik(t, tgt, tries=None, iters=300, seed=<seed>, near=None, warm=None, other=None, pose_only=k,
quiet=True)` (menu pinned to one attitude -> n_try = 2) on L with L_COL[r] and on R with MxL[r]; a pair (r, k) is
IDENTICAL iff both sides converge and max|q_R - q_L| < 1e-6 rad.  Models on the right: B (mirrored arm + mirrored ko,
sign +1), and the two negative controls RC (stock arm + stock ko on the right mount, sign +1) and NH (mirrored arm +
stock ko), the three of pZ's instrument.  Bar: (1) RC and NH show 0 identical pairs (else the row has no discriminating
power and is reported invalid); (2) on B every row has >= 1 identical k; (3) on B the count of (both converge and not
identical) is reported (prediction 0; > 0 is a finding for p11, not a section 11 STOP).  The unsharpened form
(tries=None without pose_only; pZ measured 5/17 identical rows on B) is reported alongside.  Mx = diag(-1, 1, 1) is
interpreted in the composed one-arm model's frame; the map and both targets are printed.  Not shown by this row: reach
of the real R targets (rows 2-18 show that), mounting correctness (R1/R2), collision/grasp/dynamics.

"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ur15_cell_spec as _spec  # noqa: E402
from ur15_cell_spec import (  # noqa: E402
    ARM_CLEARANCE, ARM_DECIDE_CUTOFF, ARM_PAIR_CUTOFF, C1, C2, CABLE_N, CABLE_R, CABLE_SEG, COLUMN_R, FLOAT_Z,
    GRIP_HALF_SPAN, HOME_POSE, LIMS, REST_TOP, REST_Y, SIGMA_FLOOR, SIGMA_GOOD, SIGMA_PENALTY, Z_RISE_REST, Z_RISE_ROUTE,
    seat_z,
)
import ur15_gripper_mirror_acceptance as _acc  # noqa: E402  build_side @ b7a5e39ecf (composed model, C-2 constants)

U0_SETTLED = {"GL": (0.0986, 0.28, 0.9488), "GR": (0.1886, 0.28, 0.951), "links": ("cab26", "cab32"),
              "source": "_gen/dod_c2_20260810/run.log :93 (sha256 04599b84e34be51ec906662f0d92aa8349eae833034c3a7e8d070d6c808b8868), the driver's "
                        "'re-measured after the approach' print (:2825 @ 84a372439c59; driver c737f6974e at the run), "
                        "rounded to 1e-4 by that print; reported, outside the denominator"}
U0_ROWS = {2: "cable上空へ", 3: "cableへ下降", 4: "cable把持", 5: "持ち上げ"}

# ---- mj_step counter: the static-class witness (prereg row 2a) ----------------------------------------------------
_MJ_STEP_CALLS = 0
_mj_step_orig = mujoco.mj_step


def _mj_step_counted(*a, **k):
    global _MJ_STEP_CALLS
    _MJ_STEP_CALLS += 1
    return _mj_step_orig(*a, **k)


mujoco.mj_step = _mj_step_counted

# ---- the rebinding (prereg row 1/1', 30 globals): model-free rules pasted verbatim from the driver ------------------
_MASTNAMES = ("stem", "foot", "crown", "stereo_head")
LIM = np.array(LIMS)
CLEARANCE_REPORT = {}
LAST_CLEAR = {}
_DEPTH_AUDIT = {"calls": 0, "checked": 0, "neg": 0, "below_lower": 0, "seg_disagree": 0,
                "seg_over": 0, "seg_under": 0, "by_caller": {}, "pairs": {}, "type_pairs": {},
                "chan": {}, "chan_viol": {}, "rows": [],
                "type_all": {}, "repaired": 0, "repair_zero": 0, "repair_signed": 0,
                "unrepairable": 0, "bound_informative": 0, "last_flagged": False,
                "cand_evals": 0, "rej_total": 0, "rej_flagged": 0,
                # ⭐ p18 §837 / p5: the DECIDER counter, on the mechanism that settled the counts
                # pair.  `_blame` counts rejections AGAINST A PART and the mast test runs whether
                # or not the candidate was already decided, so a ranking built on it over-counts.
                # This tallies per CANDIDATE, untruncated: "sole" is one candidate one vote and
                # carries no ordering convention; "mult" says how often a sole cause even exists.
                # ⭐ (b) p18 ordering ruling 20260804-1430: the same tally, restricted to the
                # candidates whose far-arm rejection was decided by a call the floors had FLAGGED.
                # Without this split the flagged subset's sole-cause count has to be assumed equal
                # to the whole set's, and "about 12 would flip" was exactly that assumption wearing
                # a number.  ⚠ The bit is set at the far-arm test only -- the mast, furniture and
                # path tests make their own distance calls and are not tracked -- so a candidate
                # counted UNFLAGGED here may still have been rejected by a flagged call elsewhere.
                "decider": {"n": 0, "sole": {}, "any": {}, "mult": {},
                            "flagged": {"n": 0, "sole": {}, "any": {}, "mult": {}}},
                "seg_under_contact": 0, "seg_under_narrow": 0,
                "sign_checked": 0, "sign_ghost": 0, "sign_missed": 0}
GRASP_CENTRE_X = float(os.environ.get("GRASP_CENTRE_X", C1[0]))

SIDES = dict(_spec.SIDES)          # {"L": -1.0, "R": +1.0}; narrowed to one side while that side's model is bound
m = d = None                       # the composed model / data of the side being solved (the dump's while targets are read)
QADR = VADR = PAD = TOOLB = AXFIX = None
GNAME = ARMB = ARMG = FURNG = COLG = COLFREE = None
CAB = None                         # the dump's cable link bodies (driver :454), bound only while the targets are read


# ==== VERBATIM COPIES from the landed driver blob 84a372439c59 (AST-equal; do not edit here) ========================
def solve_ik(t, tgt, tries=26, iters=300, seed=1, near=None, quiet=False, warm=None, other=None, re_max=0.05, wide=False, pose_only=None, pose_rd=None, label="start-pose"):
    """Damped least-squares IK for position AND tool orientation on scratch MjData.  Keeps every
    solution that converges, wraps it to the nearest branch, drops the ones that would sit in
    collision, and returns the one closest to `near` (so the servo move stays short)."""
    sc = mujoco.MjData(m)
    _clear_dropped = 0
    _blame, _blame_eg, _phase = {}, {}, []          # what each rejected candidate was rejected AGAINST, by name
    _col_dropped = 0
    _path_dropped = 0
    _worst_path = (1e9, None)
    # Where the arm actually is when this solve runs -- the start of every candidate's move.
    _q_now = np.array([d.qpos[a] for a in QADR[t]])
    if other is not None:
        for t2 in SIDES:
            if t2 != t:
                for k, a in enumerate(QADR[t2]):
                    sc.qpos[a] = other[k]
    rg = np.random.default_rng(seed)
    cands = []
    sgn = -1.0 if t == "L" else 1.0   # each arm tips AWAY from the other
    POSES = pose_menu(t, wide)
    if pose_rd is not None:
        # An explicit (yaw, roll) rather than a menu entry.  Rs, on the second hand: it is only
        # just clamping -- adjust the attitude.  The coarse menu steps roll by 0.25 rad, which is
        # 14 degrees of tilt on a mouth 10 mm tall, so the ladder below is what "adjust" needs.
        POSES = [(sgn * pose_rd[0], sgn * pose_rd[1])]   # p5 -167: the sign is on both, see above
    elif pose_only is not None:
        # Both hands must present the ko the same way to the cable.  Fixing the menu entry and
        # letting only `sgn` differ makes the two solutions mirror images: same yaw, same roll
        # magnitude, tipped away from each other.  Left free, the two arms picked unrelated
        # branches -- 20.1 deg of roll on one and 34.4 on the other -- and only one could seat the
        # cable in its slot.
        POSES = [POSES[pose_only % len(POSES)]]
    # p11 -147 (C): before deciding whether the clearance and the ranking really compete, find out
    # whether the answer is just thin sampling.  Measured: the menu holds 65 attitudes and tries
    # was 44, so the search did not complete ONE pass over it -- twenty-one attitudes were never
    # tried at all, and "the best surviving candidate was worse" was said about a sample that had
    # not seen the whole menu.  None means every attitude twice: once for coverage, twice so each
    # gets a second seed.  Not a round number; the menu's own length.
    n_try = tries if tries is not None else 2 * len(POSES)
    for _try in range(n_try):
        # ⭐ (b) p5 -283, simplified to one number: violations per candidate EVALUATION, so k and p
        # never have to be separated and the leak is quoted in the unit decisions are made in.
        _DEPTH_AUDIT["cand_evals"] += 1
        RD = _rdes(*POSES[_try % len(POSES)])
        # warm-start EVERY tool pose from the previous waypoint before trying random
        # restarts, else the solver keeps handing back a different branch each STEP
        if warm is not None and pose_only is not None:
            # With the menu pinned to one entry there is only ever one warm try, and the other
            # restarts came back from random joint space -- same fingertip, wildly different arm,
            # which is exactly the asymmetry this is meant to remove.  Stay near the warm pose and
            # perturb, so every candidate is the same branch.
            q = np.asarray(warm) + (0.0 if _try == 0 else rg.normal(0.0, 0.06, 6))
        elif warm is not None and _try < len(POSES):
            q = np.asarray(warm)
        else:
            q = rg.uniform(LIM[:, 0], LIM[:, 1])
        for k, a in enumerate(QADR[t]):
            sc.qpos[a] = q[k]
        for _ in range(iters):
            # ⛔ kinematics only, NOT mj_forward.  Two reasons, and the first is a crash:
            # mj_forward here segfaults at spread 0.340 / tilt 30 -- deterministic, 37 s, three
            # runs of three, with a finite in-limits joint vector (checked), so the fault is in
            # the collision stage on an INTERMEDIATE pose.  Nothing in this loop reads contacts:
            # mj_jacBody wants cdof, pinch() and xmat want kinematics, and `touching` runs after
            # convergence on a full mj_forward at :1483.  Second, collision detection was running
            # 240 tries x 300 iterations per arm per round for nothing.
            # ⚠ Verified result-identical before adoption: SEGFAULT_AT_SPREAD0340_TILT30_20260802.md
            mujoco.mj_kinematics(m, sc)
            mujoco.mj_comPos(m, sc)
            Js = []
            for b in PAD[t]:
                jp = np.zeros((3, m.nv))
                mujoco.mj_jacBody(m, sc, jp, None, b)
                Js.append(jp[:, VADR[t]])
            jr = np.zeros((3, m.nv))
            mujoco.mj_jacBody(m, sc, None, jr, TOOLB[t])
            Rt = np.array(sc.xmat[TOOLB[t]]).reshape(3, 3)
            ep = tgt - pinch(t, sc)
            er = Rotation.from_matrix((RD @ AXFIX[t]) @ Rt.T).as_rotvec()
            J = np.vstack([0.5 * (Js[0] + Js[1]), 0.6 * jr[:, VADR[t]]])
            e = np.concatenate([ep, 0.6 * er])
            dq = 0.5 * (J.T @ np.linalg.solve(J @ J.T + 0.05**2 * np.eye(6), e))
            n = float(np.linalg.norm(dq))
            if n > 0.15:
                dq *= 0.15 / n
            qc = np.clip(np.array([sc.qpos[a] for a in QADR[t]]) + dq, LIM[:, 0], LIM[:, 1])
            for k, a in enumerate(QADR[t]):
                sc.qpos[a] = qc[k]
        mujoco.mj_forward(m, sc)
        pe = float(np.linalg.norm(tgt - pinch(t, sc)))
        Rt = np.array(sc.xmat[TOOLB[t]]).reshape(3, 3)
        re_ = float(np.linalg.norm(Rotation.from_matrix((RD @ AXFIX[t]) @ Rt.T).as_rotvec()))
        if pe > 0.002 or re_ > re_max:
            continue
        qw = _wrap(np.array([sc.qpos[a] for a in QADR[t]]))
        # ⭐ UNWRAP_SOLVE -- the same arm, the short way round, decided BEFORE the path tests.
        # _wrap puts the answer in a principal range; the ramp then drives linearly from `near` to
        # that number, which for a base joint near +/-pi means almost a full turn the wrong way.
        # Applying the unwrap AFTER the solve (UNWRAP_START) cannot help: the candidates whose
        # WRAPPED path collides are already discarded, so the shorter path never gets tested.
        # Here the shift happens first, so every path test below sees the path the arm will take.
        # ⛔ Only where the shifted value stays inside the joint's range.
        if os.environ.get("UNWRAP_SOLVE") and near is not None:
            _ref = np.asarray(near, float)
            for _j in range(6):
                _k = round((_ref[_j] - qw[_j]) / (2 * math.pi))
                if _k:
                    _c = qw[_j] + _k * 2 * math.pi
                    if LIM[_j, 0] <= _c <= LIM[_j, 1]:
                        qw[_j] = _c
        for k, a in enumerate(QADR[t]):
            sc.qpos[a] = qw[k]
        mujoco.mj_forward(m, sc)
        if float(np.linalg.norm(tgt - pinch(t, sc))) > 0.002:
            continue
        # Rs, 2026-07-28, approving the change this had been waiting for: do not choose a pose
        # that comes within a set distance of the other arm.  Contact was the only test before,
        # and "not touching" covers a millimetre as happily as a metre -- which is how a pose
        # resting on the far arm's forearm kept being selected and reported as clear.
        # ⚠ Only when the far arm is IN this scratch data.  With other=None there is nothing to
        # measure against, and a clearance of "no other arm" would read as infinite -- so the
        # near-miss test says so rather than passing silently.
        hit = bool(touching(t, sc))
        _by_clearance = False
        _blame0 = dict(_blame)
        _cand_flagged = False
        near_far_arm = None
        if other is not None:
            # p11 -146: this loop only ever asks whether anything is under the clearance, so it
            # can search a radius just wider than the clearance instead of the reporting radius.
            # Nothing it DECIDES changes -- a pair beyond the small radius is beyond the clearance
            # by construction -- and the far pairs stop being measured.  The reported minimum
            # still uses the wide radius, because that one is read as a distance.
            near_far_arm = arm_pair_min(sc, t, "R" if t == "L" else "L",
                                        cutoff=ARM_DECIDE_CUTOFF)
            # ⭐ (d2) p5 -285: the selector has already run mj_forward on this scratch and
            # arm_pair_min over it, so the contact list and the winning pair are both in hand and
            # this costs no distance call.  A scalar asserting contact where the solver records none
            # is a ghost; clearance asserted over a pair the solver IS contacting is a miss.
            # ⚠ Two limits, noted rather than hidden: contacts only exist inside the margin band, and
            # the list is per geom pair while the minimum is one pair, so this bounds neither way.
            _rp = _DEPTH_AUDIT.get("_ret_pair")
            if _rp is not None and near_far_arm is not None:
                _DEPTH_AUDIT["sign_checked"] += 1
                _incon = any((sc.contact.geom1[_i], sc.contact.geom2[_i]) in
                             (_rp, (_rp[1], _rp[0])) for _i in range(sc.ncon))
                if near_far_arm <= 0.0 and not _incon:
                    _DEPTH_AUDIT["sign_ghost"] += 1
                elif near_far_arm > 0.0 and _incon:
                    _DEPTH_AUDIT["sign_missed"] += 1
            if near_far_arm is not None and near_far_arm < ARM_CLEARANCE:
                # ⭐ (a) The measurement p6 asked for: not "how many candidates COULD have been
                # dropped wrongly" -- that bound is vacuous at 1,444 pairs per call -- but how many
                # WERE dropped by a call the floors had already flagged.
                _DEPTH_AUDIT["rej_total"] += 1
                if _DEPTH_AUDIT.get("_ret_flagged"):
                    _DEPTH_AUDIT["rej_flagged"] += 1
                    _cand_flagged = True
                hit = True
                _clear_dropped += 1
                _by_clearance = True
                _blame["the other arm"] = _blame.get("the other arm", 0) + 1
            # ⛔ ARM_PATH: the same test ALONG the move, which the mast has had since 07-28 and the
            # other arm never did.  Default OFF because it changes what counts as clear, and every
            # count measured before 2026-08-02 was taken without it.
            elif os.environ.get("FURNITURE"):
                # ⛔ The saddles and the table, at the pose.  Third obstacle class; same shape as
                # the first two, found the same way -- by the arm arriving in contact with
                # something the selector had never been told about.
                _fg, _fw = furniture_gap(t, sc, want_who=True, cutoff=ARM_DECIDE_CUTOFF)
                if _fg is not None and _fg < ARM_CLEARANCE:
                    hit = True
                    _clear_dropped += 1
                    _by_clearance = True
                    _blame["the furniture"] = _blame.get("the furniture", 0) + 1
                    _blame_eg.setdefault("the furniture", _fw)
                elif near is not None and os.environ.get("ARM_PATH"):
                    # ⛔ And ALONG the move.  I added the furniture at the pose only -- repeating,
                    # within the hour, the exact defect I had just diagnosed for the other arm.
                    # The pose test rejected nothing and the arm still arrived touching a saddle,
                    # which is the same sentence a third time.
                    _fp, _fpw = path_furniture_min(t, sc, near, qw, cutoff=ARM_DECIDE_CUTOFF)
                    if _fp is not None and _fp < ARM_CLEARANCE:
                        hit = True
                        _clear_dropped += 1
                        _by_clearance = True
                        _blame["the furniture ON THE WAY"] = \
                            _blame.get("the furniture ON THE WAY", 0) + 1
                        _blame_eg.setdefault("the furniture ON THE WAY", _fpw)
            if not hit and near is not None and os.environ.get("ARM_PATH"):
                _pg, _pw = path_arm_min(t, sc, near, qw, cutoff=ARM_DECIDE_CUTOFF)
                if _pg is not None and _pg < ARM_CLEARANCE:
                    hit = True
                    _clear_dropped += 1
                    _by_clearance = True
                    # ⛔ ONE key, not one per sample.  Keying by the full "who at i/n" string
                    # splits the tally into dozens of singletons, every one of which falls below
                    # the printed cut -- so the cause fires, rejects everything, and appears
                    # nowhere in the summary.  An instrument reporting a fault to nobody, again.
                    _k9 = "the other arm ON THE WAY"
                    _blame[_k9] = _blame.get(_k9, 0) + 1
                    _blame_eg.setdefault(_k9, _pw)
                    # ⛔ The phase, kept separately.  Keying the tally once made the cause visible
                    # and made its DISTRIBUTION invisible -- and the distribution is the whole
                    # diagnostic (does the early peak shrink and the late one remain?).  It cannot
                    # be read back out of a single key, so it is accumulated rather than inferred.
                    _mm9 = re.search(r" at (\d+)/(\d+) along the move", _pw or "")
                    if _mm9:
                        _phase.append(int(_mm9.group(1)) / int(_mm9.group(2)))
        # Rs, 2026-07-28, watching the run: "the left hand is slamming into the cylinder."  The
        # mast was never in this filter.  It was MEASURED every step and printed as "column gap",
        # and it read negative at EIGHT steps of thirteen -- nine counting the one that read
        # exactly zero -- while the selection went on choosing those poses: an instrument
        # reporting a fault to nobody.  (I first wrote ten, from memory of the printout rather
        # than from a count of it; p18 counted the banked trace.  The steps are 3, 4, 5, 6, 11,
        # 12, 13, 14 at -0.6 mm and 10 at -0.0.)  So the mast is now tested exactly
        # where the far arm is tested, and by the same rule Rs approved for the far arm.
        # ⚠ Unconditional, unlike the far arm: the mast is always in the scene, so there is no
        # case where it is absent from the scratch data and nothing to measure.
        # The distance is the same one -- a cable diameter, the smallest thing that has to fit
        # between two parts of this machine.  Reusing it rather than inventing a second number is
        # a design call and is flagged as one; it is not derived that the two should be equal.
        # The decision only ever asks whether anything is under the clearance, so it searches a
        # radius just wider than the clearance -- p11's cutoff split, the same one the far-arm test
        # takes.  Nothing it decides changes; the far pairs stop being measured.
        # ⭐ p5 -170(3): name the part.  The rejection already knows what it is rejecting against,
        # and the answer picks the branch of an open Rs decision -- the yoke or the column say
        # "mounting geometry", the other arm or the table say "clip placement".  So the
        # counterpart comes out with the count instead of being inferred from it.
        _cg, _cw = column_gap(t, sc, want_who=True, cutoff=ARM_DECIDE_CUTOFF)
        if _cg is not None and _cg < ARM_CLEARANCE:
            hit = True
            _col_dropped += 1
            _blame[_cw or "mast"] = _blame.get(_cw or "mast", 0) + 1
        else:
            # ⛔ And the same distance along the WAY there.  The endpoint test passed every one of
            # the right arm's candidates at STEP3 and the arm still ended 0.6 mm inside the stem:
            # the forearm crosses the mast mid-move, jams, and the pose is never reached.  A
            # candidate whose path goes through the mast is not a candidate.
            _pg, _pw = path_mast_min(t, sc, _q_now, qw, cutoff=ARM_DECIDE_CUTOFF)
            if _pg is not None and _pg < ARM_CLEARANCE:
                hit = True
                _path_dropped += 1
                _blame[f"{_pw or 'mast'} (on the way)"] = \
                    _blame.get(f"{_pw or 'mast'} (on the way)", 0) + 1
                if _pg < _worst_path[0]:
                    _worst_path = (_pg, _pw)
        # Manipulability of this candidate.  The solver had no notion of a singularity at all --
        # it ranked candidates by position error and by staying near the previous pose, so a
        # configuration that has lost a direction could win, and did: Rs saw two runs in a row
        # swing around through one.  Rejecting those is the missing criterion, not a workaround.
        for _k, _a in enumerate(QADR[t]):
            sc.qpos[_a] = qw[_k]
        mujoco.mj_forward(m, sc)
        sv = sigma_min(t, sc)
        if hit:
            _why = tuple(sorted(k for k, v in _blame.items() if v > _blame0.get(k, 0)))
            _dec = _DEPTH_AUDIT["decider"]
            # ⭐ (b): the flagged subset gets the SAME arithmetic, into its own dicts.  The whole-set
            # rows are computed exactly as before -- the subset is an addition, never a filter --
            # so a run's existing decider rows have to come out byte-identical, and that is the
            # control this change is checked by.
            for _tally in ((_dec, _dec["flagged"]) if _cand_flagged else (_dec,)):
                _tally["n"] += 1
                _tally["mult"][len(_why)] = _tally["mult"].get(len(_why), 0) + 1
                for _wk in _why:
                    _tally["any"][_wk] = _tally["any"].get(_wk, 0) + 1
                if len(_why) == 1:
                    _tally["sole"][_why[0]] = _tally["sole"].get(_why[0], 0) + 1
        cands.append((qw, pe, re_, hit, abs(POSES[_try % len(POSES)][1]), sv, near_far_arm,
                      _by_clearance))
    # ⛔ The fallback below is a SILENT one, and it makes two opposite worlds print the same
    # number: "every candidate cleared" and "not one candidate cleared, so all of them were put
    # back" both leave len(free) == len(cands).  t42's left arm printed 6 solved / 6 collision-free
    # and then arrived inside the crown -- which is exactly what the second world looks like from
    # outside.  pB -515 found it; the comment at the print below fixed this same shape one level
    # up and stopped there.  The strict count is kept so the two can never share a number again.
    _strict = [c for c in cands if not c[3]]
    # ⭐ The clear set itself, kept so the all-pairs interleave can be read off the poses
    # this solve actually cleared -- rather than re-deriving them somewhere else.
    LAST_CLEAR[t] = [np.asarray(c[0]) for c in _strict]
    _fell_back = not _strict
    free = _strict or cands
    if not free:
        raise RuntimeError(f"no IK solution for {t} at {tgt}")
    # ⛔ NOT gated on `quiet`.  pB -516(a): the disclosure reached one of the four solve sites,
    # and the three it missed are the ones that run quiet -- including the per-step solve that
    # produced the mast jam this whole line of work started from.  A fault report that only
    # speaks when the caller asked for chatter is a fault report nobody hears.  The counts stay
    # quiet; the "none of them cleared" line does not.
    if _fell_back:
        print(f"[steps] ⛔ {label} IK {t}: NOT ONE of {len(cands)} candidates cleared the "
              f"clearance or its path, so all {len(cands)} were put back and the choice below is "
              f"made among poses that were all rejected -- read the next line's 'collision-free' "
              f"as 'none'")
    if not quiet and _blame:
        # One line, named parts, because the answer decides which of two options is even on the
        # table.  ⚠ The counts sum to more than the candidate count when a pose is rejected on
        # more than one test; each entry is "rejections against this part", not "poses".
        _b = ", ".join(f"{k} x{v}" + (f" (e.g. {_blame_eg[k]})" if k in _blame_eg else "")
                       for k, v in sorted(_blame.items(), key=lambda kv: -kv[1]))
        if _phase:
            _h = [sum(1 for v in _phase if lo <= v < lo + 0.2) for lo in (0, .2, .4, .6, .8)]
            print(f"[steps] {label} IK {t}: arm-path violation phase (0 = start of the move, "
                  f"1 = the pose): " + "  ".join(f"{lo:.1f}-{lo+0.2:.1f}: {c}"
                                                 for lo, c in zip((0, .2, .4, .6, .8), _h))
                  + f"   n={len(_phase)}")
        print(f"[steps] {label} IK {t}: rejected against -- {_b}"
              f"   (parts named; the crown and stem/foot are the mounting, 'the other arm' is not)")
    # ⛔ p6's rule, applied where it was still broken: a disclosure protects its subject only
    # while they share a gate.  The fallback disclosure is un-gated and the REASON is inside
    # `if not quiet`, so a quiet solve says "not one candidate cleared" 107 times and never once
    # says what rejected them.  A fallback is exactly when the reason is needed, so it prints
    # whenever the solve fell back, quiet or not.
    # ⚠ Restored to indent 4 here (2026-08-03): `82e845e80c` inserted this block INSIDE the
    # `if not quiet and _blame:` body above, which both ended that body early and left `if _phase:`
    # with a 12-space body and an 8-space sibling -- the file has not parsed since 23:56 on 08-02.
    if _fell_back and quiet and _blame:
        print(f"[steps] {label} IK {t}: (fell back) rejected against -- "
              + ", ".join(f"{k} x{v}" + (f" (e.g. {_blame_eg[k]})" if k in _blame_eg else "")
                          for k, v in sorted(_blame.items(), key=lambda kv: -kv[1])[:6]))
    well = [c for c in free if c[5] >= SIGMA_FLOOR] or free   # drop the near-singular ones
    ref = np.zeros(6) if near is None else np.asarray(near)
    near_only = [c for c in well if np.abs(c[0] - ref).max() <= 1.2] or \
                [c for c in well if np.abs(c[0] - ref).max() <= 2.2]
    pool = near_only or well
    # The singularity now RANKS, which is what the note beside SIGMA_FLOOR promised and never did.
    # A candidate that has lost a direction pays for it; none is forbidden, so the solver cannot be
    # starved the way the hard floor starved it.
    def _cost(c):
        _short = max(0.0, SIGMA_GOOD - c[5]) / SIGMA_GOOD      # 0 when well conditioned, ->1 at 0
        return 2.0 * c[4] + float(np.linalg.norm(c[0] - ref)) + SIGMA_PENALTY * _short
    # p11 -154, and it separates two things the earlier pair was mixing.  The winner is chosen by
    # _cost, not by conditioning, so the set the selector COULD have chosen from may hold a better
    # conditioned pose than the one it took.  Printing the best in that set beside the winner's
    # says which of two different problems this is: the filter removing good candidates, or the
    # cost passing over a good survivor.  If the best survivor is about as good as the best the
    # filter dropped, the filter took nothing and the competition is inside the ranking.
    _pool_sv = max(c[5] for c in pool)
    _winc = min(pool, key=_cost)
    q, pe, re_, hit, roll, sv, nfa, _bc = _winc

    # ⭐ p6 -296, accepted: the SAME juxtaposition for the other two cost terms.  Only the
    # conditioning term was shown beside the pool's best, so a winner that lost on roll or on
    # distance-from-reference looked identical to one that lost on nothing.
    # ⛔ Why this is worth a line: the cost is roll + distance + conditioning, and NONE of the
    # three contains a clearance quantity.  The repair changes which candidates are in the pool
    # and cannot change how the pool is ranked -- so anything read downstream of this choice
    # measures the ranking, not the filter.  That is derived; this prints what would measure it.
    # Print only, no term added, no candidate re-ranked.
    def _cost_terms(c):
        return (2.0 * c[4],
                float(np.linalg.norm(c[0] - ref)),
                SIGMA_PENALTY * (max(0.0, SIGMA_GOOD - c[5]) / SIGMA_GOOD))
    if _fell_back or not quiet:
        _wt = _cost_terms(_winc)
        _bt = tuple(min(_cost_terms(c)[_i] for c in pool) for _i in range(3))
        # ⛔ The pool SIZE goes on the same line, and it is not decoration.  Of the first 22 lines
        # this printed, 15 sat on a pool the fallback had reduced to two, where "the winner is also
        # the pool's best on every term" cannot come out any other way -- a comparison that cannot
        # differ is not a comparison.  Read the pair only where the size makes it able to speak.
        print(f"[steps] {label} IK {t}: cost terms over a pool of {len(pool)}, winner vs the "
              f"pool's best on each -- roll {_wt[0]:.4f}/{_bt[0]:.4f}  "
              f"near {_wt[1]:.4f}/{_bt[1]:.4f}  cond {_wt[2]:.4f}/{_bt[2]:.4f}  "
              f"(winner total {sum(_wt):.4f}; ⛔ no term here is a clearance, so the filter cannot "
              f"move this ranking{'; ⚠ pool of 1 -- this line cannot differ' if len(pool) < 2 else ''})")
    # p11 -139: the conditioning of the candidates the clearance threw away is already computed --
    # sv is taken for every candidate, including the rejected ones, and then dropped on the floor.
    # Printing the best of them beside the winner's turns that into the one comparison that is
    # actually controlled: same state, same candidate set, the only difference being the filter.
    # Across runs it would not be, because four other things changed.
    # ⛔ pB -516(d): this read c[7], which is "dropped by the ARM test", while the sentence it
    # feeds names the mast rejections in the same breath.  A candidate the mast removed was not
    # counted as dropped at all, so "best dropped" could report the conditioning of a set that
    # excluded most of what was actually thrown away.  c[3] is "rejected by anything".
    _drop_sv = [c[5] for c in cands if c[3]]
    # p11 -152, one field: is there any pose with room, or is this step's target the problem?
    # ⚠ The literal maximum is NOT available and saying so is the point.  The decision loop
    # searches a radius of twice the clearance, so a candidate with plenty of room comes back as
    # None -- "further than 16 mm", not a distance.  Reporting a max over the ones that ARE inside
    # that radius would be a maximum over the crowded candidates only, which is the opposite of
    # what the question asks.  So the count of candidates that cleared the whole search radius is
    # what goes out: many of them means poses with room exist, which is the one-sided refutation
    # p11 wants, and it is stronger than a max because it does not depend on where they sit.
    _roomy = sum(1 for c in cands if c[6] is None)
    _inside = [c[6] for c in cands if c[6] is not None]
    # p5 -137 / p11 -138, prints (1) and (3): say how many candidates the clearance removed -- the
    # same instrument as the floor's "how many did it remove", for the same reason -- and what
    # clearance the pose that WON was predicted to have.  A rejection count of zero and a rejection
    # count of forty look identical from a pose alone.
    CLEARANCE_REPORT[t] = (_clear_dropped, len(cands), nfa, sv,
                           max(_drop_sv) if _drop_sv else None,
                           _roomy, max(_inside) if _inside else None, _pool_sv,
                           _col_dropped, _path_dropped, _worst_path)
    if not quiet:
        # ⛔ This line used to report len(well) as "away from a singularity", beside len(free) as
        # "collision-free".  With the floor at zero those are the SAME candidates -- sigma is never
        # negative, so the comparison keeps everything -- and printing one number under two names
        # said a filter had run when none had.  It was wording left over from the hard floor after
        # the floor itself was withdrawn (p11 -120(1) found it; I had written it).  So the count
        # printed now is how many the floor actually removed, which is zero while it is zero and
        # cannot be read as a second filter.  The singularity ranks; it does not exclude.
        print(f"[steps] {label} IK {t}: {len(cands)} solved / {len(_strict)} collision-free"
              f"{f' (⛔ 0 -- all {len(cands)} put back)' if _fell_back else ''} / "
              f"floor {SIGMA_FLOOR:.2f} removed {len(free) - len(well)} of them (it ranks, it does "
              f"not exclude), chosen pos {pe*1000:5.2f} mm "
              f"roll {math.degrees(roll):4.1f} deg sigma_min {sv:.4f} |q|max={np.abs(q).max():.2f} rad")
        # ⭐ The winning joint vector itself.  Everything downstream is a property of THIS pose,
        # and the line named its cost, its roll and its conditioning but not the pose -- so
        # nothing that used it could be reproduced without re-running the solve.
        # ⭐ Every survivor, not only the winner.  p5 §31 asks whether any CLEAR pose avoids the
        # mount-to-mount line, which cannot be asked of a set that was never printed.
        for _k, _c in enumerate(_strict[:40]):
            print(f"[steps] {label} IK {t}: clear #{_k}: q = [" +
                  " ".join(f"{v:+.6f}" for v in _c[0]) + f"] sigma {_c[5]:.4f}")
        if len(_strict) > 40:
            print(f"[steps] {label} IK {t}: ({len(_strict) - 40} further clear poses not printed)")
        print(f"[steps] {label} IK {t}: chosen q = [" +
              " ".join(f"{v:+.6f}" for v in q) + "] rad")
    return q


def pose_menu(t, wide=False):
    """The attitude menu for arm `t`, as (yaw, roll) pairs.

    ⭐ p5 -167: the sign belongs on the YAW as well as the roll.  Rolling exists to let two arms
    share an 88 mm span without their wrists meeting, which is a statement about the PAIR -- and a
    menu that mirrors one and not the other hands the two arms attitudes that are not mirror
    images of each other the moment the yaw is non-zero.
    ⚠ An entry INDEX therefore names a different attitude on the right arm than it did before the
    sign was added; a right-arm pose recorded as an index has to be re-read as a value.

    ⛔ Lifted out of solve_ik so it can be PRINTED without running a solve.  The change above was
    reported as demonstrated on the strength of a trace line reading yaw +0.15 where it had read
    -0.15 -- and p6 was right that a plus-minus symmetric set prints that either way, so the line
    was no evidence at all.  The menu itself is the evidence, and now it can be shown.
    """
    sgn = -1.0 if t == "L" else 1.0
    menu = [(0.0, sgn * r) for r in (0.0, 0.35, 0.6, 0.85, 1.1)] + \
           [(sgn * y, sgn * r) for r in (0.35, 0.6, 0.85) for y in (0.3, -0.3)]
    if wide:  # per-STEP waypoints get a bigger pose menu so a CONTINUOUS branch survives
        menu = menu + [(sgn * y, sgn * r)
                       for r in (0.2, 0.5, 0.75, 1.0) for y in (0.15, -0.15, 0.5, -0.5)]
    return menu


def _wrap(q):
    q = q.copy()
    for k in range(6):
        while q[k] > math.pi and q[k] - 2 * math.pi >= LIM[k, 0]:
            q[k] -= 2 * math.pi
        while q[k] < -math.pi and q[k] + 2 * math.pi <= LIM[k, 1]:
            q[k] += 2 * math.pi
    return q


def _rdes(yaw, roll=0.0):
    """Closing axis across the cable, approach down; `yaw` spins the tool about the vertical and
    `roll` tips it about the closing axis, which walks the WRIST outboard while the pinch stays
    put.  Rolling is what lets two arms share an 88 mm span without their wrists meeting."""
    base = Rotation.from_euler("z", yaw) * Rotation.from_euler("z", math.pi / 2.0)
    return (base * Rotation.from_euler("y", roll)).as_matrix()


def pinch(t, dd=None):
    dd = dd if dd is not None else d
    return 0.5 * (np.array(dd.xpos[PAD[t][0]]) + np.array(dd.xpos[PAD[t][1]]))


def touching(t, dd):
    """What this arm is in contact with, other than itself."""
    out = set()
    for i in range(dd.ncon):
        g1, g2 = dd.contact[i].geom1, dd.contact[i].geom2
        a1, a2 = g1 in ARMG[t], g2 in ARMG[t]
        if a1 != a2:
            other = g2 if a1 else g1
            near = g1 if a1 else g2
            ob = m.geom_bodyid[other]
            # p18 -622(6): the near side used to be dropped, so a contact could be reported without
            # saying which of THIS arm's parts made it -- and the open question about STEP13 is
            # precisely whether a claw plate is one of them.  Both ends are named now.
            out.add(f"{mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, ob) or GNAME[other]}"
                    f" (via {GNAME[near]})")
    return out


def sigma_min(t, dd=None):
    """Smallest singular value of that Jacobian.  Near zero means the arm has lost a direction --
    a singularity -- and the servo command for a small tool motion becomes a huge joint motion."""
    return float(np.linalg.svd(wrist_jac(t, dd), compute_uv=False)[-1])


def wrist_jac(t, dd=None):
    """The 6x6 tool Jacobian of arm `t`: translation of the pinch stacked on tool rotation."""
    dd = dd if dd is not None else d
    Js = []
    for b in PAD[t]:
        jp = np.zeros((3, m.nv))
        mujoco.mj_jacBody(m, dd, jp, None, b)
        Js.append(jp[:, VADR[t]])
    jr = np.zeros((3, m.nv))
    mujoco.mj_jacBody(m, dd, None, jr, TOOLB[t])
    return np.vstack([0.5 * (Js[0] + Js[1]), jr[:, VADR[t]]])


def column_gap(t, dd=None, want_who=False, cutoff=None):
    """Closest signed distance from this arm's geoms to the yoke mast [m].  Negative means the arm
    is inside the mast.  mj_geomDistance is a geometry query, so it reports this whether or not the
    pair can collide.

    Rs, 2026-07-28, watching the run: "the left hand is slamming into the cylinder" -- so the name
    of the part comes out with the number.  Twenty runs reported this as a bare figure, and a bare
    figure cannot say whether a hand arrived or a mount never left.  (It was the arm: pB refuted
    the mount reading from the trace itself -- a permanent overlap cannot read +387.5 mm at one
    step -- and the named reading confirms a link that moves.)"""
    dd = dd if dd is not None else d
    best, who = 1e9, None
    for g in COLFREE[t]:
        for c in COLG:
            # Same exact prefilter as the arm-to-arm query, and here for the same reason: this
            # runs for every IK candidate of every solve, and the unfiltered form is what once
            # made a run take hours.  Two geoms cannot be closer than the gap between their
            # bounding spheres, so a pair already past the cutoff cannot lower the minimum.
            if cutoff is not None and (
                    float(np.linalg.norm(dd.geom_xpos[g] - dd.geom_xpos[c]))
                    - m.geom_rbound[g] - m.geom_rbound[c]) >= cutoff:
                continue
            d_ = mujoco.mj_geomDistance(m, dd, g, c, 1.0, None)
            if d_ < best:
                best, who = d_, f"{GNAME[g]} vs {GNAME[c]}"
    # ⛔ None, not the cutoff, when nothing is in range -- the cutoff wearing a distance's clothes
    # is the failure this instrument already had once, at the arm-to-arm surface.
    # ⛔ Metres, like the arm-to-arm query, so that BOTH gaps format through gap_mm and nothing
    # multiplies one of them by a thousand at a call site.  This used to return mm, and the mixed
    # pair of units is what put a bare "* 1000" in four different places.
    if best > 1e8:
        return (None, None) if want_who else None
    return (best, who) if want_who else best


def path_mast_min(t, sc, q_from, q_to, cutoff=None):
    """Smallest mast gap reached anywhere ALONG the joint-space move from q_from to q_to [m].

    The endpoint test cannot see this, and the run showed exactly that: at STEP3 the mast rejected
    none of the right arm's candidates -- every commanded pose was clear -- and the arm still ended
    up 0.6 mm inside the stem, because the FOREARM sweeps through the mast on the way there and
    jams.  Joint 1 then sits at its whole 433 N.m pushing on the column and arrives 92 degrees
    short.  A pose the arm never reaches is not made safe by being clear.

    Sample count is derived, not chosen: it is the travel of the fastest-moving geom divided by the
    mast's own radius, so no sample-to-sample step can carry a part clean through the obstacle.
    ⚠ That bounds tunnelling THROUGH the mast; it does not promise to catch a graze that begins and
    ends between two samples.  The bound is the obstacle's size because the obstacle is what is
    being tunnelled through -- nothing here is tuned.

    ⛔ Writes into `sc` and leaves it at q_to, which is where every caller wants it anyway.  Uses
    mj_kinematics rather than mj_forward: this needs geom poses, not contacts, and the full solve
    would cost far more for nothing.
    """
    q_from, q_to = np.asarray(q_from, float), np.asarray(q_to, float)
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_from[_k]
    mujoco.mj_kinematics(m, sc)
    p0 = np.asarray(sc.geom_xpos)[COLFREE[t]].copy()
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_to[_k]
    mujoco.mj_kinematics(m, sc)
    travel = float(np.linalg.norm(np.asarray(sc.geom_xpos)[COLFREE[t]] - p0, axis=1).max())
    n = max(1, int(math.ceil(travel / COLUMN_R)))
    best, who = 1e9, None
    for i in range(1, n):        # the two ends are tested by the caller's own endpoint reading
        q = q_from + (q_to - q_from) * (i / n)
        for _k, _a in enumerate(QADR[t]):
            sc.qpos[_a] = q[_k]
        mujoco.mj_kinematics(m, sc)
        g_, w_ = column_gap(t, sc, want_who=True, cutoff=cutoff)
        if g_ is not None and g_ < best:
            best, who = g_, f"{w_} at {i}/{n} along the move"
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_to[_k]
    mujoco.mj_kinematics(m, sc)
    return (None, None) if best > 1e8 else (best, who)


def arm_pair_min(dd, ta="L", tb="R", want_who=False, cutoff=None):
    """Smallest signed distance between any geom of arm `ta` and any of arm `tb` [m].

    ⚠ Written this way for speed, and the speed matters: the naive form is 38x38 = 1444 distance
    calls, and it runs for every IK candidate of every solve.  It made a run take hours.

    The prefilter is exact rather than approximate.  Two geoms cannot be closer than the gap
    between their bounding spheres, so any pair whose centres are farther apart than
    cutoff + rbound + rbound is already past the cutoff and cannot lower the minimum.  Those are
    dropped by one vectorised comparison, and only the survivors are measured properly.  The
    answer is identical to the exhaustive form; only the work is smaller.
    """
    # ARMG holds sets -- numpy cannot index with one, and the first run said so immediately.
    _DEPTH_AUDIT["_ret_flagged"] = False
    _DEPTH_AUDIT["_ret_pair"] = None
    cut = ARM_PAIR_CUTOFF if cutoff is None else cutoff
    ga, gb = np.fromiter(sorted(ARMG[ta]), int), np.fromiter(sorted(ARMG[tb]), int)
    pa = np.asarray(dd.geom_xpos)[ga]
    pb = np.asarray(dd.geom_xpos)[gb]
    ra = np.asarray(m.geom_rbound)[ga]
    rb = np.asarray(m.geom_rbound)[gb]
    sep = np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2) - ra[:, None] - rb[None, :]
    # ⛔ None, not the cutoff, when nothing is within range.  Returning the cutoff made the report
    # read "+176.0 mm" with an empty pair name, which is the cutoff wearing a distance's clothes --
    # the same saturation the claw-tip reading has, and the same way of hiding it.  A caller that
    # wants a number for a comparison can substitute one knowingly; the reader gets told.
    best, who = None, ""
    for ia, ib in zip(*np.where(sep < cut)):
        dv = mujoco.mj_geomDistance(m, dd, int(ga[ia]), int(gb[ib]), cut, None)
        if dv >= cut:
            continue
        # The bound check used to sit here.  It moved to the wrapper installed beside _DEPTH_AUDIT,
        # because here it saw arm-against-arm only -- one of the six functions that ask this
        # question, and not the one p18's ruling 20260803-1173 names (the mast).  See there.
        if best is None or dv < best:
            best = dv
            # ⭐ p6 via p18 20260803-1232: the MINIMUM is what the clearance test compares, so the
            # only call whose contamination can flip a candidate is the one that produced it.
            _DEPTH_AUDIT["_ret_flagged"] = _DEPTH_AUDIT["last_flagged"]
            _DEPTH_AUDIT["_ret_pair"] = (int(ga[ia]), int(gb[ib]))
            if want_who:
                who = (f"{mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(ga[ia])) or ga[ia]}"
                       f" <-> {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(gb[ib])) or gb[ib]}")
    return (best, who) if want_who else best


def path_arm_min(t, sc, q_from, q_to, cutoff=None):
    """Smallest gap to the OTHER ARM reached anywhere along the joint-space move [m].

    ⛔ This did not exist, and the same docstring one function up says why it had to.  The mast got
    a path test because "the FOREARM sweeps through the mast on the way there and jams ... a pose
    the arm never reaches is not made safe by being clear".  The other arm never got one: it was
    tested at the candidate pose and nowhere else.

    Measured consequence, 2026-08-02: both arms sweep about 250 degrees from home to their start
    poses, pass through each other on the way, and arrive in contact -- the right arm 53 degrees
    short of its own command.  The tracking gate then requires each arm to be within 5.18 mrad of
    that command, so it never opens and every STEP reports 0.0% held on every tick.  Endpoint-clear
    poses, no clear way to reach them.

    Sample count derived the same way as the mast's, with the other arm's own smallest bounding
    radius as the obstacle size, so no sample-to-sample step can carry a part clean through it.
    ⚠ Same limit as the mast's: it bounds tunnelling, not a graze between two samples.
    """
    tb = "R" if t == "L" else "L"
    q_from, q_to = np.asarray(q_from, float), np.asarray(q_to, float)
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_from[_k]
    mujoco.mj_kinematics(m, sc)
    _mine = np.fromiter(sorted(ARMG[t]), int)
    p0 = np.asarray(sc.geom_xpos)[_mine].copy()
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_to[_k]
    mujoco.mj_kinematics(m, sc)
    travel = float(np.linalg.norm(np.asarray(sc.geom_xpos)[_mine] - p0, axis=1).max())
    _r = float(np.asarray(m.geom_rbound)[np.fromiter(sorted(ARMG[tb]), int)].min())
    n = max(1, int(math.ceil(travel / max(_r, 1e-4))))
    best, who = 1e9, None
    for i in range(1, n):        # the ends are the caller's own endpoint reading
        q = q_from + (q_to - q_from) * (i / n)
        for _k, _a in enumerate(QADR[t]):
            sc.qpos[_a] = q[_k]
        mujoco.mj_kinematics(m, sc)
        g_, w_ = arm_pair_min(sc, t, tb, want_who=True, cutoff=cutoff)
        if g_ is not None and g_ < best:
            best, who = g_, f"{w_} at {i}/{n} along the move"
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_to[_k]
    mujoco.mj_kinematics(m, sc)
    return (None, None) if best > 1e8 else (best, who)


def furniture_gap(t, dd, want_who=False, cutoff=None):
    """Smallest distance from arm `t` to the saddles and the table [m], or None if nothing near."""
    cut = ARM_DECIDE_CUTOFF if cutoff is None else cutoff
    best, who = None, ""
    ga = np.fromiter(sorted(ARMG[t]), int)
    for gb in FURNG:
        for gaa in ga:
            v = mujoco.mj_geomDistance(m, dd, int(gaa), int(gb), cut, None)
            if v < cut and (best is None or v < best):
                best = v
                who = (f"{GNAME[gaa]} vs "
                       f"{mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, gb)}")
    return (best, who) if want_who else best


def path_furniture_min(t, sc, q_from, q_to, cutoff=None):
    """Smallest gap to the saddles and table anywhere along the move [m]. Same form as the others."""
    q_from, q_to = np.asarray(q_from, float), np.asarray(q_to, float)
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_from[_k]
    mujoco.mj_kinematics(m, sc)
    _mine = np.fromiter(sorted(ARMG[t]), int)
    p0 = np.asarray(sc.geom_xpos)[_mine].copy()
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_to[_k]
    mujoco.mj_kinematics(m, sc)
    travel = float(np.linalg.norm(np.asarray(sc.geom_xpos)[_mine] - p0, axis=1).max())
    _r = float(np.asarray(m.geom_rbound)[np.fromiter(FURNG, int)].min()) if FURNG else 0.05
    n = max(1, int(math.ceil(travel / max(_r, 1e-4))))
    best, who = 1e9, None
    for i in range(1, n):
        q = q_from + (q_to - q_from) * (i / n)
        for _k, _a in enumerate(QADR[t]):
            sc.qpos[_a] = q[_k]
        mujoco.mj_kinematics(m, sc)
        g_, w_ = furniture_gap(t, sc, want_who=True, cutoff=cutoff)
        if g_ is not None and g_ < best:
            best, who = g_, f"{w_} at {i}/{n} along the move"
    for _k, _a in enumerate(QADR[t]):
        sc.qpos[_a] = q_to[_k]
    mujoco.mj_kinematics(m, sc)
    return (None, None) if best > 1e8 else (best, who)


def _own_bodies(prefix):
    """Bodies belonging to one arm, by ancestry -- the URDF geoms are UNNAMED, so a name-prefix
    test silently matches nothing.  Walk the body tree instead."""
    out = set()
    for b in range(m.nbody):
        nb = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or ""
        if nb.startswith(prefix):
            out.add(b)
    changed = True
    while changed:
        changed = False
        for b in range(m.nbody):
            if b not in out and m.body_parentid[b] in out:
                out.add(b)
                changed = True
    return out


def _measure_axfix():
    """Measure, per arm, where the closing axis and the approach axis sit in the tool's own frame.
    Measured on a throwaway MjData; the live state is never touched."""
    sc = mujoco.MjData(m)
    for t in SIDES:
        for k, a in enumerate(QADR[t]):
            sc.qpos[a] = [0.0, -1.2, 1.0, -1.4, -1.57, 0.0][k]
    mujoco.mj_forward(m, sc)
    out = {}
    for t in SIDES:
        pl, pr = np.array(sc.xpos[PAD[t][0]]), np.array(sc.xpos[PAD[t][1]])
        c_w = (pr - pl) / max(np.linalg.norm(pr - pl), 1e-9)
        pinch_w = 0.5 * (pl + pr)
        a_w = np.array(sc.xpos[TOOLB[t]]) - pinch_w
        a_w = a_w / max(np.linalg.norm(a_w), 1e-9)
        Rt = np.array(sc.xmat[TOOLB[t]]).reshape(3, 3)
        c_l, a_l = Rt.T @ c_w, Rt.T @ a_w
        s_l = np.cross(a_l, c_l)
        out[t] = np.column_stack([c_l, s_l, a_l]).T  # B_local^T
    return out


def cable_at(x):
    """Centre of the cable link nearest this x.  A link's body origin is the START of its capsule,
    so the material sits half a segment further along the link's own x axis -- targeting the origin
    misses by ~15 mm."""
    C = np.array([np.array(d.xpos[b]) + np.array(d.xmat[b]).reshape(3, 3) @ np.array([CABLE_SEG / 2, 0, 0])
                  for b in CAB])
    i = int(np.argmin(np.abs(C[:, 0] - x)))
    return C[i], i

# ==== end of the verbatim copies ====================================================================================


class InstrumentStop(RuntimeError):
    """The harness cannot calibrate its own targets (section 17.7): reported as 「instrument calibration stop」."""


def _grasp_targets(dump_path):
    """Rows 2-5 grasp targets by the two paths of section 17.7; STOP unless they agree to <= 1e-9 and in link number."""
    global m, d, CAB
    x_cmd = {"L": GRASP_CENTRE_X - GRIP_HALF_SPAN, "R": GRASP_CENTRE_X + GRIP_HALF_SPAN}     # the driver's :1241 x
    # (b-2) closed form from the cell constants (driver :336-:337 placement, one link per CABLE_SEG along +x)
    x0 = -CABLE_SEG * CABLE_N / 2.0
    z0 = REST_TOP + CABLE_R
    centres = np.array([[x0 + (i + 0.5) * CABLE_SEG, REST_Y, z0] for i in range(CABLE_N)])
    closed = {}
    for t, xc in x_cmd.items():
        i = int(np.argmin(np.abs(centres[:, 0] - xc)))
        closed[t] = (centres[i].copy(), i)
    # (b-1) the driver's own cable_at on the emitted cell's rest state (mj_forward at the dump's initial state)
    dump_path = Path(dump_path)
    if not dump_path.is_file():
        raise InstrumentStop(f"cell dump absent: {dump_path} (pass --dump; the driver writes it at import, :446)")
    dump_sha = hashlib.sha256(dump_path.read_bytes()).hexdigest()
    try:
        md = mujoco.MjModel.from_xml_path(str(dump_path))
    except Exception as e:  # noqa: BLE001
        raise InstrumentStop(f"cell dump unloadable: {dump_path}: {e}") from e
    dd = mujoco.MjData(md)
    mujoco.mj_forward(md, dd)
    m, d = md, dd
    CAB = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"cab{i}") for i in range(CABLE_N)]

    if len(CAB) != CABLE_N or min(CAB) < 0:
        raise InstrumentStop(f"dump cable bodies cab0..cab{CABLE_N - 1} not all present: {CAB}")
    measured = {t: cable_at(xc) for t, xc in x_cmd.items()}                      # (C[i], i) per side, :2812 form
    m = d = CAB = None
    src = {"form": ":2812-2813 (x/y/z = centre of the nearest cable link), section 17.7",
           "x_commanded_1241_form": {t: float(v) for t, v in x_cmd.items()},
           "GRASP_CENTRE_X": float(GRASP_CENTRE_X), "GRASP_CENTRE_X_env_set": "GRASP_CENTRE_X" in os.environ,
           "WORK_ROW_DY": float(_spec.WORK_ROW_DY), "WORK_ROW_DY_env_set": "WORK_ROW_DY" in os.environ,
           "REST_Y": float(REST_Y), "z0_REST_TOP_plus_CABLE_R": float(z0), "x0": float(x0),
           "CABLE_SEG": float(CABLE_SEG), "CABLE_N": int(CABLE_N),
           "dump": str(dump_path), "dump_sha256": dump_sha,
           "path_b1_driver_cable_at_on_dump": {t: {"link": f"cab{i}", "xyz": [float(v) for v in c]} for t, (c, i) in measured.items()},
           "path_b2_closed_form": {t: {"link": f"cab{i}", "xyz": [float(v) for v in c]} for t, (c, i) in closed.items()},
           "reported_settled_U0": U0_SETTLED}
    worst = max(float(np.abs(measured[t][0] - closed[t][0]).max()) for t in x_cmd)
    links_equal = all(measured[t][1] == closed[t][1] for t in x_cmd)
    src["paths_max_abs_diff_m"] = worst; src["paths_links_equal"] = links_equal
    if worst > 1e-9 or not links_equal:
        raise InstrumentStop(f"section 17.7 paths disagree: max |b1 - b2| = {worst:.3e} m, links equal = {links_equal}: {src}")
    GL = (float(measured["L"][0][0]), float(measured["L"][0][1]), float(measured["L"][0][2]))   # the :2812 form
    GR = (float(measured["R"][0][0]), float(measured["R"][0][1]), float(measured["R"][0][2]))   # the :2813 form
    src["GL"], src["GR"] = list(GL), list(GR)
    src["settle_offset_a_minus_b"] = {"L": [float(a - b) for a, b in zip(U0_SETTLED["GL"], GL)],
                                      "R": [float(a - b) for a, b in zip(U0_SETTLED["GR"], GR)]}
    return GL, GR, src


def _bind(t, model, data):
    """Bind the closure's globals to one side's composed model (the one permitted rebinding)."""
    global m, d, SIDES, QADR, VADR, PAD, TOOLB, AXFIX, GNAME, ARMB, ARMG, FURNG, COLG, COLFREE
    m, d = model, data
    SIDES = {t: _spec.SIDES[t]}
    J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
    # the driver's rules :451-:453/:471 with the composed prefixes (`a_` arm joints, `g_` hand bodies)
    QADR = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"a_{j}")] for j in J6] for t in SIDES}
    VADR = {t: [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"a_{j}")] for j in J6] for t in SIDES}
    PAD = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"g_{s}_pad") for s in ("left", "right")] for t in SIDES}
    TOOLB = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "g_base") for t in SIDES}
    assert all(v >= 0 for v in [*QADR[t], *VADR[t], *PAD[t], TOOLB[t]]), "composed-model name lookup failed"
    # the driver's rule :499 with the composed prefixes (pZ addendum 3 (b))
    ARMB = {t: _own_bodies("a_") | _own_bodies("g_") for t in SIDES}
    # the driver's own assignments, verbatim, evaluated on the composed model
    GNAME = {g: (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g)
                 or f"g{g} on {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.geom_bodyid[g]) or 'an unnamed body'}")
             for g in range(m.ngeom)}
    ARMG = {t: {g for g in range(m.ngeom) if m.geom_bodyid[g] in ARMB[t]} for t in SIDES}
    FURNG = [g for g in range(m.ngeom)
             if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").startswith(("S", "table_"))
             and (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "")[1:2].isdigit()
             or (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "") == "table_top"]
    COLG = [g for g in (mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) for n in _MASTNAMES)
            if g >= 0]
    COLFREE = {t: sorted(ARMG[t]) for t in SIDES}

    AXFIX = _measure_axfix()          # the copied rule (seed :600, fingers 0, throwaway data)
    for k, a in enumerate(QADR[t]):   # start pose = the spec's HOME_POSE (where the arms wait), as pZ's instrument
        d.qpos[a] = HOME_POSE[k]
    mujoco.mj_forward(m, d)


def _targets(GL, GR):
    """The STEP table's L and R columns, rows 2-18, as the driver builds them (see the module docstring)."""
    Z_SEAT = seat_z(FLOAT_Z)
    LX1, RX1 = C1[0] - GRIP_HALF_SPAN, C1[0] + GRIP_HALF_SPAN
    LX2, RX2 = C2[0] - GRIP_HALF_SPAN, C2[0] + GRIP_HALF_SPAN
    RX_MID = float(np.mean([C1[0], C2[0]]))
    rows = [
        (2, "cable上空へ", (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST)),
        (3, "cableへ下降", GL, GR),
        (4, "cable把持", GL, GR),
        (5, "持ち上げ", (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST)),
        (6, "C1上空へ搬送", (LX1, C1[1], Z_RISE_ROUTE), (RX1, C1[1], Z_RISE_ROUTE)),
        (7, "C1へ押し込み", (LX1, C1[1], Z_SEAT), (RX1, C1[1], Z_SEAT)),
        (8, "誘導ハンド半保持", (LX1, C1[1], Z_SEAT), (RX1, C1[1], Z_SEAT)),
        (9, "C1がcable固定", (LX1, C1[1], Z_SEAT), (RX1, C1[1], Z_SEAT)),
        (10, "C1から上昇", (LX1, C1[1], Z_RISE_ROUTE), (RX1, C1[1], Z_RISE_ROUTE)),
        (11, "C2上空へ", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE)),
        (12, "左クランプ", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE)),
        (13, "右がcable再把持へ", (LX2, C2[1], Z_RISE_ROUTE), (RX_MID, C2[1], Z_RISE_ROUTE)),
        (14, "両手クランプ", (LX2, C2[1], Z_RISE_ROUTE), (RX_MID, C2[1], Z_RISE_ROUTE)),
        (15, "C2へ押し込み", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT)),
        (16, "C2固定", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT)),
        (17, "解放", (LX2, C2[1], Z_SEAT), (RX2, C2[1], Z_SEAT)),
        (18, "上昇", (LX2, C2[1], Z_RISE_ROUTE), (RX2, C2[1], Z_RISE_ROUTE)),
    ]
    return [(n, name, np.array(L, float), np.array(R, float)) for n, name, L, R in rows]


def _u0_rows():
    """Path (a): rows 2-5 at the settled U0 values -- solved and reported, outside the denominator (section 17.7)."""
    GL, GR = U0_SETTLED["GL"], U0_SETTLED["GR"]
    rows = [(2, (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST)), (3, GL, GR), (4, GL, GR),
            (5, (GL[0], GL[1], Z_RISE_REST), (GR[0], GR[1], Z_RISE_REST))]
    return [(n, U0_ROWS[n], np.array(L, float), np.array(R, float)) for n, L, R in rows]


def _solve_rows(t, rows, col, seed, re_max, tag_rows="", in_denominator=True):
    """One side over every row; converged := the wired test inside solve_ik (pe <= 0.002, re <= re_max)."""
    out = []
    for n, name, L, R in rows:
        tgt = L if col == "L" else R
        LAST_CLEAR.pop(t, None)
        CLEARANCE_REPORT.pop(t, None)
        q, conv, tag, note = None, False, "none", ""
        try:
            q = solve_ik(t, tgt, tries=None, iters=300, seed=seed, near=None, other=None, re_max=re_max, quiet=True)
            conv = True
        except RuntimeError as e:          # "no IK solution for ..." (:2339) = no candidate passed the wired test
            if str(e).startswith("no IK solution"):
                tag, note = "controller non-convergence", str(e)
            else:
                tag, note = "other", f"RuntimeError: {e}"
        except AssertionError as e:        # a calibration raise inside the copied closure = instrument stop
            tag, note = "instrument calibration stop", f"AssertionError: {e}"
        pe = None
        if q is not None:                  # re-evaluate the returned pose on a throwaway data, kinematics only
            sc = mujoco.MjData(m)
            for k, a in enumerate(QADR[t]):
                sc.qpos[a] = q[k]
            mujoco.mj_kinematics(m, sc)
            mujoco.mj_comPos(m, sc)
            pe = float(np.linalg.norm(tgt - pinch(t, sc)))
        cr = CLEARANCE_REPORT.get(t)
        out.append({"step": n, "name": name, "side": t, "column": col, "row_tag": tag_rows, "in_denominator": in_denominator,
                    "target": [float(v) for v in tgt],
                    "converged": conv, "stop_cause_tag": tag, "note": note,
                    "n_converged_candidates": len(LAST_CLEAR.get(t, [])),
                    "n_candidates_total": None if cr is None else int(cr[1]),
                    "pe_recheck_m": pe,
                    "re_recheck": None,    # the attitude that won is not returned by solve_ik; pe is re-checked, re is not
                    "q": None if q is None else [float(v) for v in q],
                    "q_absmax": None if q is None else float(np.abs(q).max())})
    return out


MX = np.array([-1.0, 1.0, 1.0])            # section 17.8: the mirror map diag(-1, 1, 1), composed-model frame
R0II_TOL_RAD = 1e-6


def _solve_one(t, tgt, seed, re_max, pose_only=None):
    """One solve in the wired form (section 17.8 call); returns (q or None, stop-cause tag, note)."""
    LAST_CLEAR.pop(t, None)
    CLEARANCE_REPORT.pop(t, None)
    try:
        q = solve_ik(t, tgt, tries=None, iters=300, seed=seed, near=None, warm=None, other=None, re_max=re_max,
                     pose_only=pose_only, quiet=True)
        return np.asarray(q, float), "none", ""
    except RuntimeError as e:
        if str(e).startswith("no IK solution"):
            return None, "controller non-convergence", str(e)
        return None, "other", f"RuntimeError: {e}"
    except AssertionError as e:
        return None, "instrument calibration stop", f"AssertionError: {e}"


def _r0ii(models_R, model_L, rows, seed, re_max, qL_unsharpened):
    """Section 17.8 (b): the mirrored-target identity row, sharpened by pose_only=k, on B and the controls RC/NH."""
    K = len(pose_menu("L"))
    assert K == len(pose_menu("R")), "menu length differs between sides"
    L_rows = [(n, name, L, L * MX) for n, name, L, _R in rows]          # (row, name, L_COL, MxL)
    # L side: sharpened sweep on the correct L model (the unsharpened L solutions come from the main leg)
    _bind("L", *model_L)
    qL = {}
    for n, name, L, _ in L_rows:
        for k in range(K):
            qL[(n, k)] = _solve_one("L", L, seed, re_max, pose_only=k)
    out = {"Mx": MX.tolist(), "menu_len": K, "seed": seed, "re_max": re_max, "tol_rad": R0II_TOL_RAD,
           "targets": [{"step": n, "name": name, "L": L.tolist(), "MxL": M.tolist()} for n, name, L, M in L_rows],
           "L_sharpened_converged_pairs": sum(1 for v in qL.values() if v[0] is not None),
           "models": {}}
    for mname, md in models_R.items():
        _bind("R", *md)
        ident, both_not_ident, both, pairs, uns_ident = [], [], 0, [], []
        for n, name, L, M in L_rows:
            for k in range(K):
                qR, tag, note = _solve_one("R", M, seed, re_max, pose_only=k)
                qLk = qL[(n, k)][0]
                dq = None if (qR is None or qLk is None) else float(np.abs(qR - qLk).max())
                if dq is not None:
                    both += 1
                    if dq < R0II_TOL_RAD:
                        ident.append((n, k))
                    else:
                        both_not_ident.append((n, k, dq))
                pairs.append({"step": n, "k": k, "L_converged": qLk is not None, "R_converged": qR is not None,
                              "R_tag": tag, "max_abs_dq_rad": dq})
            # unsharpened form (tries=None, no pose_only) at MxL, against the main leg's L solution
            qRu, tagu, _ = _solve_one("R", M, seed, re_max, pose_only=None)
            qLu = qL_unsharpened.get(n)
            if qRu is not None and qLu is not None and float(np.abs(qRu - qLu).max()) < R0II_TOL_RAD:
                uns_ident.append(n)
        rows_with = sorted({n for n, _ in ident}); rows_without = [n for n, *_ in L_rows if n not in rows_with]
        out["models"][mname] = {
            "identical_pairs": ident, "identical_count": len(ident),
            "both_converged_pairs": both, "both_converged_not_identical": both_not_ident,
            "rows_with_identical_k": rows_with, "rows_without_identical_k": rows_without,
            "unsharpened_identical_rows": uns_ident, "pairs": pairs}
        print(f"[r0-ii] model {mname}: identical (r,k) = {len(ident)} of {both} both-converged pairs "
              f"({len(L_rows)} rows x {K} k); rows with >= 1 identical k = {len(rows_with)}/{len(L_rows)}; "
              f"both-converged-not-identical = {len(both_not_ident)}; unsharpened identical rows = {len(uns_ident)}/{len(L_rows)}")
    B, RC, NH = (out["models"].get(x, {}) for x in ("B", "RC", "NH"))
    out["bar"] = {
        "controls_RC_NH_identical_0": RC.get("identical_count", -1) == 0 and NH.get("identical_count", -1) == 0,
        "B_every_row_has_identical_k": len(B.get("rows_without_identical_k", [1])) == 0,
        "B_both_converged_not_identical_count": len(B.get("both_converged_not_identical", [])),
        "row_valid": RC.get("identical_count", -1) == 0 and NH.get("identical_count", -1) == 0,
        "claim": "鏡像同一性（solver 経路）のみ／実 R target への到達・取付の正しさ（R1/R2）・衝突・把持・動的追従は示さない",
    }
    print(f"[r0-ii] bar: {out['bar']}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="R0 convergence leg (static; convergence only)")
    ap.add_argument("--out", default=str(HERE / "_gen" / "r0_convergence"))
    ap.add_argument("--dump", default=str(HERE / "_gen" / "_steps_cell_full.xml"),
                    help="the emitted cell (driver :446), read at its initial state for path (b-1) of section 17.7")
    ap.add_argument("--seed", type=int, default=1, help="one seed for every row and both sides (wired default 1)")
    ap.add_argument("--re-max", type=float, default=0.05, help="wired default at solve_ik's signature")
    args = ap.parse_args()
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    claim = "収束のみ／衝突・把持・動的追従は未証明 (convergence only; collision, grasp and dynamic tracking are not shown)"
    try:
        GL, GR, source = _grasp_targets(args.dump)
    except InstrumentStop as e:
        rec = {"summary": {"claim": claim, "stop_cause_tags_seen": ["instrument calibration stop"],
                           "instrument_stop": str(e), "mj_step_calls": _MJ_STEP_CALLS}}
        (out_dir / "R0_CONVERGENCE_REPORT.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
        print(f"[r0] ⛔ instrument calibration stop (section 17.7 targets): {e}")
        print(f"[r0] {claim}")
        return 2
    print(f"[r0] rows 2-5 targets (section 17.7, :2812 form): GL={GL} GR={GR}; paths agree to "
          f"{source['paths_max_abs_diff_m']:.3e} m, links {source['path_b1_driver_cable_at_on_dump']['L']['link']}/"
          f"{source['path_b1_driver_cable_at_on_dump']['R']['link']}; dump sha256 {source['dump_sha256']}")
    print(f"[r0] effective GRASP_CENTRE_X={source['GRASP_CENTRE_X']} (env set: {source['GRASP_CENTRE_X_env_set']}), "
          f"WORK_ROW_DY={source['WORK_ROW_DY']} (env set: {source['WORK_ROW_DY_env_set']})")
    print(f"[r0] settle offset (a) - (b) [m]: L={source['settle_offset_a_minus_b']['L']} R={source['settle_offset_a_minus_b']['R']}"
          f"  (a = {U0_SETTLED['source']})")
    models = {"L": _acc.build_side("ur15_base.xml", _acc.KO_LEFT, _spec.SIDES["L"]),
              "R": _acc.build_side("ur15_base_mirrored.xml", _acc.KO_MIRROR, _spec.SIDES["R"])}
    # R0-ii negative controls (section 17.8, pZ's instrument): RC = stock arm + stock ko on the right mount (sign +1),
    # NH = mirrored arm + stock ko
    models_r0ii = {"B": None, "RC": _acc.build_side("ur15_base.xml", _acc.KO_LEFT, _spec.SIDES["R"]),
                   "NH": _acc.build_side("ur15_base_mirrored.xml", _acc.KO_LEFT, _spec.SIDES["R"])}
    rows, u0 = _targets(GL, GR), _u0_rows()
    print(f"[r0] targets: {len(rows)} rows (2-18) in the denominator; {len(u0)} extra U0 rows reported")
    for n, name, L, R in rows:
        print(f"[r0] row {n:2d} {name:10s} L={np.round(L, 6)} R={np.round(R, 6)}")
    res, resu0, branches = {}, {}, {}
    for t in ("L", "R"):
        _bind(t, *models[t])
        branches[t] = {"COLG": len(COLG), "FURNG": len(FURNG), "ARMG": len(ARMG[t]), "COLFREE": len(COLFREE[t]),
                       "FURNITURE_env": bool(os.environ.get("FURNITURE")), "ARM_PATH_env": bool(os.environ.get("ARM_PATH")),
                       "other": None, "near": None}
        print(f"[r0] side {t}: composed model nq={m.nq} nbody={m.nbody} ngeom={m.ngeom}; {branches[t]}; AXFIX rows c/s/a =")
        for k, lab in enumerate("csa"):
            print(f"[r0]   {lab} = [" + " ".join(f"{v:+.6f}" for v in AXFIX[t][k]) + "]")
        res[t] = _solve_rows(t, rows, t, args.seed, args.re_max)
        resu0[t] = _solve_rows(t, u0, t, args.seed, args.re_max, tag_rows="settled example (U0)", in_denominator=False)
    # negative control (prereg row 8): the R column on the L model
    _bind("L", *models["L"])
    neg = _solve_rows("L", rows, "R", args.seed, args.re_max, tag_rows="negative control: R targets on the L model", in_denominator=False)
    # R0-ii (section 17.8 (b)): mirrored L targets, pose_only=k sweep, on B and the controls RC / NH
    models_r0ii["B"] = models["R"]
    qL_uns = {r["step"]: (None if r["q"] is None else np.asarray(r["q"], float)) for r in res["L"]}
    r0ii = _r0ii(models_r0ii, models["L"], rows, args.seed, args.re_max, qL_uns)
    convL = [r["converged"] for r in res["L"]]; convR = [r["converged"] for r in res["R"]]
    convN = [r["converged"] for r in neg]
    l_not_r = [r["step"] for cl, cr, r in zip(convL, convR, res["R"]) if cl and not cr]
    r_not_l = [r["step"] for cl, cr, r in zip(convL, convR, res["R"]) if cr and not cl]
    neg_diff = [r["step"] for cr, cn, r in zip(convR, convN, neg) if cr != cn]
    stop = sum(convR) == 0
    tags = sorted({r["stop_cause_tag"] for blk in (res["L"], res["R"], neg, resu0["L"], resu0["R"]) for r in blk} - {"none"})
    summary = {
        "claim": claim,
        "stop_cause_tags_seen": tags,
        "section_11_STOP_R_converged_0": stop,
        "rows": len(rows), "L_converged": sum(convL), "R_converged": sum(convR),
        "L_converges_R_not": l_not_r, "R_converges_L_not": r_not_l,
        "bar_L_not_R_must_be_0": len(l_not_r) == 0,
        "negative_control_R_rows_on_L_model_differ_on_steps": neg_diff,
        "negative_control_fired": len(neg_diff) >= 1,
        "U0_settled_rows_reported": {t: {r["step"]: r["converged"] for r in resu0[t]} for t in ("L", "R")},
        "R0ii_bar": r0ii["bar"],
        "R0ii_counts": {mn: {k: v for k, v in mv.items() if k != "pairs"} for mn, mv in r0ii["models"].items()},
        "seed": args.seed, "re_max": args.re_max, "tries": None, "iters": 300, "quiet": True, "start_pose": list(HOME_POSE),
        "branches_on_composed_model": branches,
        "mj_step_calls": _MJ_STEP_CALLS,
        "mounting": {"YOKE_SPREAD": float(_acc.acc.YOKE_SPREAD), "TILT_rad": float(_acc.acc.TILT),
                     "SHOULDER_HEIGHT": float(_acc.acc.SHOULDER_HEIGHT)},
        "env_overrides_set": {k: os.environ[k] for k in ("YOKE_SPREAD_OVERRIDE", "TILT_DEG_OVERRIDE", "WORK_ROW_DY",
                                                         "GRASP_CENTRE_X", "FURNITURE", "ARM_PATH") if k in os.environ},
        "targets_source": source,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "elapsed_s": round(time.time() - t0, 3),
    }
    rec = {"summary": summary, "L": res["L"], "R": res["R"], "U0_settled_L": resu0["L"], "U0_settled_R": resu0["R"],
           "negative_control_R_on_L": neg, "R0ii": r0ii}
    (out_dir / "R0_CONVERGENCE_REPORT.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print("[r0] " + " | ".join(f"{k}={v}" for k, v in summary.items() if k not in ("claim", "targets_source", "branches_on_composed_model", "R0ii_counts")))
    print(f"[r0] {claim}")
    print(f"[r0] report -> {out_dir / 'R0_CONVERGENCE_REPORT.json'}")
    return 0 if (len(l_not_r) == 0 and not stop) else 1


if __name__ == "__main__":
    raise SystemExit(main())
