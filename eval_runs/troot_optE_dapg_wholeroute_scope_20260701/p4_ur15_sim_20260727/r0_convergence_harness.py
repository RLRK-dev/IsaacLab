# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""R0 -- does the existing control class converge on UR15-B's targets?  Convergence only; static class.

Authority: Rs1 (the human), 2026-09-14, Q1 verbatim 「認可する。p0が作り、pZが独立に検証・実行する。」 with the scope
「物理ステップを進めず、実行副作用のあるdriverをimportしない静的検査に限定します。収束確認と、衝突・把持・動的追従の
成立は区別します。」  Spec = P11_UR15B_CONTROLLER_DESIGN_20260913.md section 10 (row R0), 11, 17.1 @ dc090f7753;
pre-registration = pZ PZ_R0_CONVERGENCE_LEG_PREREG_20260916.md rows 1-11 + 1' @ 642a9162f0.  Written by p0; executed
and judged by pZ (p0 runs py_compile only).

WHAT THIS IS.  The wired driver's per-arm 6D damped-least-squares solver -- `solve_ik` and everything it calls on the
kinematic path (`pinch`, `pinch_jac`, `wrist_jac`, `sigma_min`, `_measure_axfix`, `_wrap`, `_rdes`, `pose_menu`) -- is
copied below VERBATIM from the landed driver blob 84a372439c59 (commit 96e9ece175; the same statements are byte-identical
in the D4 blob d2bc133e1320 @ 3370f7a872, the pre-registration's base).  Copy fidelity = AST equality after N1-N3, checked
outside this file (the record section names the check).  The ONE permitted rebinding (prereg row 1) is the set of module
globals those functions read: `m`, `d`, `AXFIX`, `QADR`, `VADR`, `PAD`, `TOOLB`, `SIDES`, `LIM` and the spec constants
are bound per side to a COMPOSED model built by `ur15_gripper_mirror_acceptance.build_side` (one arm + its ko hand on its
mount, C-2 constants, no column, no cable, no other arm), and the scene-dependent helpers the solver calls after a
candidate has converged are STUBS that report "nothing within the search radius" -- vacuous by construction, because the
composed model contains nothing to be near.  Nothing in this file steps physics: the copied loop calls mj_kinematics /
mj_comPos / mj_forward only, and `mujoco.mj_step` is wrapped by a counter that the report prints (must read 0).

WHAT IT DECIDES.  Per target row (the L and R columns of the driver's STEP table, rows 2-18) and per side, whether
`solve_ik` returns a converged pose under the wired test (`pe <= 0.002 m` and `re <= re_max`, tested inside the copied
function), with the wired defaults `tries=None` (full menu, twice), `iters=300`, `re_max=0.05`, `near=None`, `other=None`
and ONE fixed seed shared by both sides so candidate index k draws the same random restart on L and on R.  The bar
(section 10 R0): rows where L converges and R does not = 0; R converged = 0 -> section 11 STOP-and-report.  Negative
control (prereg row 8): the R rows solved on the L model must differ from the R run on >= 1 row, else the leg is dead.

WHAT IT DOES NOT SHOW.  「収束のみ／衝突・把持・動的追従は未証明」 -- collision avoidance, grasp, dynamic tracking and the
mast/furniture/other-arm clearances are NOT measured here (those are the authorized run, #69, with pB/pC).  Stop-cause
tag on every report line: {instrument calibration stop / controller non-convergence / other}.

Targets.  STEP rows 6-18 resolve from ur15_cell_spec constants exactly as the driver writes them (C1, C2, GRIP_HALF_SPAN,
Z_RISE_ROUTE, Z_SEAT = seat_z(FLOAT_Z), RX_MID = mean(C1[0], C2[0])).  Rows 2-5 use GL/GR, which the driver measures
from the settled cable at run time (the "re-measured after the approach" line), so they are taken from the C-2 run
record (_gen/dod_c2_20260810/run.log :93, sha256 04599b84e34be51e...; the 0.22/45 record :94 prints the same numbers):
GL = (0.0986, 0.28, 0.9488), GR = (0.1886, 0.28, 0.951), rounded by that print to 1e-4 m -- below the 2e-3 m
convergence bar, and stated as record-sourced, not literal.
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
    ARM_CLEARANCE, ARM_DECIDE_CUTOFF, C1, C2, FLOAT_Z, GRIP_HALF_SPAN, LIMS, SIGMA_FLOOR, SIGMA_GOOD, SIGMA_PENALTY,
    Z_RISE_REST, Z_RISE_ROUTE, seat_z,
)
import ur15_gripper_mirror_acceptance as _acc  # noqa: E402  build_side @ b7a5e39ecf (composed model, C-2 constants)

# ---- mj_step counter: the static-class witness (prereg row 2a) ----------------------------------------------------
_MJ_STEP_CALLS = 0
_mj_step_orig = mujoco.mj_step


def _mj_step_counted(*a, **k):
    global _MJ_STEP_CALLS
    _MJ_STEP_CALLS += 1
    return _mj_step_orig(*a, **k)


mujoco.mj_step = _mj_step_counted

# ---- the rebinding: module globals the copied functions read, bound per side before each solve ---------------------
LIM = np.array(LIMS)
SIDES = dict(_spec.SIDES)          # {"L": -1.0, "R": +1.0}; narrowed to one side while that side's model is bound
m = d = None                       # the composed model / data of the side being solved
QADR = VADR = PAD = TOOLB = AXFIX = None
CLEARANCE_REPORT = {}
LAST_CLEAR = {}
_DEPTH_AUDIT = {"cand_evals": 0, "rej_total": 0, "rej_flagged": 0, "sign_checked": 0, "sign_ghost": 0,
                "sign_missed": 0, "_ret_pair": None, "_ret_flagged": False,
                "decider": {"n": 0, "mult": {}, "any": {}, "sole": {},
                            "flagged": {"n": 0, "mult": {}, "any": {}, "sole": {}}}}


# ---- stubs: the scene-dependent helpers, vacuous by construction (no column, cable, table or other arm here) --------
def touching(t, dd):
    """Wired: the bodies the arm is in contact with.  Composed model: nothing to touch but itself -> none."""
    return []


def column_gap(t, dd=None, want_who=False, cutoff=None):
    """Wired: signed gap to the mast.  Composed model: no mast -> beyond the search radius."""
    return (None, None) if want_who else None


def path_mast_min(t, sc, q_from, q_to, cutoff=None):
    return (None, None)


def _never(name):
    def f(*a, **k):
        raise RuntimeError(f"{name} was called: this branch needs other= or an env flag, neither is set in R0")
    return f


arm_pair_min = _never("arm_pair_min")
furniture_gap = _never("furniture_gap")
path_arm_min = _never("path_arm_min")
path_furniture_min = _never("path_furniture_min")


# ==== VERBATIM COPIES from the landed driver blob 84a372439c59 (AST-equal; do not edit here) ========================
def pinch(t, dd=None):
    dd = dd if dd is not None else d
    return 0.5 * (np.array(dd.xpos[PAD[t][0]]) + np.array(dd.xpos[PAD[t][1]]))


def pinch_jac(t):
    """Translational Jacobian of the pinch point, plus the rotational Jacobian of the tool."""
    Js = []
    for b in PAD[t]:
        jp = np.zeros((3, m.nv))
        mujoco.mj_jacBody(m, d, jp, None, b)
        Js.append(jp[:, VADR[t]])
    jr = np.zeros((3, m.nv))
    mujoco.mj_jacBody(m, d, None, jr, TOOLB[t])
    return 0.5 * (Js[0] + Js[1]), jr[:, VADR[t]]


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


def sigma_min(t, dd=None):
    """Smallest singular value of that Jacobian.  Near zero means the arm has lost a direction --
    a singularity -- and the servo command for a small tool motion becomes a huge joint motion."""
    return float(np.linalg.svd(wrist_jac(t, dd), compute_uv=False)[-1])


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

# ==== end of the verbatim copies ====================================================================================


def _bind(t, model, data):
    """Bind the copied functions' globals to one side's composed model (the one permitted rebinding)."""
    global m, d, QADR, VADR, PAD, TOOLB, AXFIX, SIDES
    m, d = model, data
    J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
    QADR = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"a_{j}")] for j in J6]}
    VADR = {t: [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"a_{j}")] for j in J6]}
    PAD = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"g_{s}_pad") for s in ("left", "right")]}
    TOOLB = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "g_base")}
    assert all(v >= 0 for v in [*QADR[t], *VADR[t], *PAD[t], TOOLB[t]]), "composed-model name lookup failed"
    SIDES = {t: _spec.SIDES[t]}
    AXFIX = _measure_axfix()          # the copied function, on this model's own throwaway data (seed :600, fingers 0)
    d.qpos[:] = 0.0
    mujoco.mj_forward(m, d)


def _targets():
    """The STEP table's L and R columns, rows 2-18, as the driver builds them (see the module docstring)."""
    GL, GR = (0.0986, 0.28, 0.9488), (0.1886, 0.28, 0.951)          # record-sourced (dod_c2 run.log :93)
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


def _solve_rows(t, rows, col, seed, re_max):
    """One side over every row; converged := the wired test inside solve_ik (pe <= 0.002, re <= re_max)."""
    out = []
    for n, name, L, R in rows:
        tgt = L if col == "L" else R
        LAST_CLEAR.pop(t, None)
        try:
            q = solve_ik(t, tgt, tries=None, iters=300, seed=seed, near=None, other=None, re_max=re_max, label="R0")
            conv, n_conv = True, len(LAST_CLEAR.get(t, []))
        except RuntimeError as e:          # "no IK solution for ..." = no candidate passed the wired test
            if not str(e).startswith("no IK solution"):
                raise
            q, conv, n_conv = None, False, 0
        pe = re_ = None
        if q is not None:                  # re-evaluate the returned pose on a throwaway data, kinematics only
            sc = mujoco.MjData(m)
            for k, a in enumerate(QADR[t]):
                sc.qpos[a] = q[k]
            mujoco.mj_kinematics(m, sc)
            mujoco.mj_comPos(m, sc)
            pe = float(np.linalg.norm(tgt - pinch(t, sc)))
            re_ = None                     # the attitude that won is not returned by solve_ik; pe is re-checked, re is not
        out.append({"step": n, "name": name, "side": t, "column": col, "target": [float(v) for v in tgt],
                    "converged": conv, "n_converged_candidates": n_conv, "pe_recheck_m": pe,
                    "re_recheck": re_, "q": None if q is None else [float(v) for v in q],
                    "q_absmax": None if q is None else float(np.abs(q).max())})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="R0 convergence leg (static; convergence only)")
    ap.add_argument("--out", default=str(HERE / "_gen" / "r0_convergence"))
    ap.add_argument("--seed", type=int, default=1, help="one seed for every row and both sides (wired default 1)")
    ap.add_argument("--re-max", type=float, default=0.05, help="wired default at solve_ik's signature")
    args = ap.parse_args()
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    models = {"L": _acc.build_side("ur15_base.xml", _acc.KO_LEFT, _spec.SIDES["L"]),
              "R": _acc.build_side("ur15_base_mirrored.xml", _acc.KO_MIRROR, _spec.SIDES["R"])}
    rows = _targets()
    print(f"[r0] targets: {len(rows)} rows (2-18); L/R columns as the driver's STEP table; GL/GR record-sourced")
    for n, name, L, R in rows:
        print(f"[r0] row {n:2d} {name:10s} L={np.round(L, 4)} R={np.round(R, 4)}")
    res = {}
    for t in ("L", "R"):
        _bind(t, *models[t])
        print(f"[r0] side {t}: composed model nq={m.nq} nbody={m.nbody} ngeom={m.ngeom}; AXFIX rows c/s/a =")
        for k, lab in enumerate("csa"):
            print(f"[r0]   {lab} = [" + " ".join(f"{v:+.6f}" for v in AXFIX[t][k]) + "]")
        res[t] = _solve_rows(t, rows, t, args.seed, args.re_max)
    # negative control (prereg row 8): the R column on the L model
    _bind("L", *models["L"])
    neg = _solve_rows("L", rows, "R", args.seed, args.re_max)
    convL = [r["converged"] for r in res["L"]]; convR = [r["converged"] for r in res["R"]]
    convN = [r["converged"] for r in neg]
    l_not_r = [r["step"] for cl, cr, r in zip(convL, convR, res["R"]) if cl and not cr]
    r_not_l = [r["step"] for cl, cr, r in zip(convL, convR, res["R"]) if cr and not cl]
    neg_diff = [r["step"] for cr, cn, r in zip(convR, convN, neg) if cr != cn]
    stop = sum(convR) == 0
    summary = {
        "claim": "収束のみ／衝突・把持・動的追従は未証明 (convergence only; collision, grasp and dynamic tracking are not shown)",
        "stop_cause_tag": "controller non-convergence" if stop else "none",
        "rows": len(rows), "L_converged": sum(convL), "R_converged": sum(convR),
        "L_converges_R_not": l_not_r, "R_converges_L_not": r_not_l,
        "bar_L_not_R_must_be_0": len(l_not_r) == 0,
        "section_11_STOP_R_converged_0": stop,
        "negative_control_R_rows_on_L_model_differ_on_steps": neg_diff,
        "negative_control_alive": len(neg_diff) >= 1,
        "seed": args.seed, "re_max": args.re_max, "tries": None, "iters": 300,
        "mj_step_calls": _MJ_STEP_CALLS,
        "mounting": {"YOKE_SPREAD": float(_acc.acc.YOKE_SPREAD), "TILT_rad": float(_acc.acc.TILT),
                     "SHOULDER_HEIGHT": float(_acc.acc.SHOULDER_HEIGHT)},
        "env_overrides_set": {k: os.environ[k] for k in ("YOKE_SPREAD_OVERRIDE", "TILT_DEG_OVERRIDE") if k in os.environ},
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "elapsed_s": round(time.time() - t0, 3),
    }
    rec = {"summary": summary, "L": res["L"], "R": res["R"], "negative_control_R_on_L": neg}
    (out_dir / "R0_CONVERGENCE_REPORT.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print("[r0] " + " | ".join(f"{k}={v}" for k, v in summary.items() if k not in ("claim",)))
    print(f"[r0] {summary['claim']}")
    print(f"[r0] report -> {out_dir / 'R0_CONVERGENCE_REPORT.json'}")
    return 0 if (len(l_not_r) == 0 and not stop and len(neg_diff) >= 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
