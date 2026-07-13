# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B3a leg 3: is the captured ``joint_qd`` the solver's END-OF-FRAME velocity? (+ identifiability table)

WHY (5-panel CC4-F4): the captured ``joint_qd`` has NO independent ground truth elsewhere in the leg set --
the recording carries positions only (that is the premise of the capture). The spec names three ways it could
be wrong and still pass every other B3a check: "a qd read from the wrong state buffer, at the WRONG SUBSTEP,
or with a permuted/transposed layout".

WHY THE FIRST VERSION OF THIS LEG WAS UNFIT (measured, 2026-07-13). It compared the capture against a central
finite difference of the recorded positions with a 20% relative bar. Three defects:
  1. SENSITIVITY: ``physics_step`` runs SIM_SUBSTEPS(=10) substeps per recorded frame (route_executor.py:827),
     so ANY position difference returns a frame-MEAN velocity, never the end-of-frame value. Where the cable's
     velocity slews fast -- kappa := |qd[f]-qd[f-1]| / |qd[f]| = 0.92 at k=2 and 1.81 at k=3 -- the estimator's
     own bias swamps the signal, and central/backward/trapezoid/3-tap ALL fail together on CORRECT data.
  2. BLIND TO THE NAMED HAZARD: a 1-substep-early read moves a frame-level FD by only ~kappa/10 (1.6% at k=1),
     which a 20% bar cannot see. The leg could not detect the very thing it was commissioned to detect.
  3. BLIND TO SCALE: it never constrained the amplitude.

THIS VERSION. Semi-implicit Euler over S substeps of SIM_DT = DT/S gives, for an integrated coord,
    bwd[f] := (q[f]-q[f-1])/DT = mean_j(v_j),  v_j = velocity after substep j  (v_0 = end of frame f-1)
Fitting  bwd = a*qd[f-1] + b*qd[f]  over ALL frames x coords yields three ORTHOGONAL statistics:
    gain     g = a + b            -> 1.000 (bwd is a convex combination of the frame's endpoint velocities);
                                     reads SCALE and SIGN errors directly (alpha_hat = 1/g).
    substep  m_hat = S*((S+1)/(2S) + 1 - b/g) = 15.5 - 10*(b/g) for S=10  -> 10 = the LAST substep.
                                     This reads the capture's substep index from frame-resolution data, at
                                     zero extra GPU cost -- the hazard the old bar was blind to.
    fit      R^2                  -> reads LAYOUT errors (permutation / wrong buffer): the model stops
                                     explaining the data at all.
The identifiability table below runs the SAME estimator against every named wrong-bank and shows which
statistic rejects it (spec sec 17 ERRATUM-E col ii: a bar whose negative control cannot fail is not a bar).

CHANNELS. gripper = servo-driven and smooth: the 2-endpoint model is exact (R^2=1.000, g=1.000), so the
GAIN BAR IS SITED HERE. cable = contact-rich and non-monotone WITHIN a frame, so its frame-mean can fall
outside the endpoint interval and its gain carries a measured ~-1.9% intrinsic bias -- reported, NOT used as
a scale bar. That costs nothing TODAY because the capture copies ONE contiguous buffer with no per-slice
arithmetic (``BankCapture.sample``: a single ``state.joint_qd.numpy()``), so a scale error is necessarily
GLOBAL and the gripper catches it.

BUT THAT IS A PREMISE, NOT A LAW (%12, spec sec 18 F-5 (4)): if the capture ever slices per group, a
GROUP-LOCAL scale error would sail past a gripper-only gain bar. So the cable gain is also carried as a DRIFT
TRIPWIRE (``G_CABLE_BAND``) around its measured intrinsic value -- not a scale bar, but a guard that any
*change* in the cable channel's gain surfaces instead of hiding.

ARM coords are excluded: the substrate overwrites arm joint_q from FK and zeroes arm joint_qd at the start of
EVERY substep (route_executor.py:838-846), which is why bank v2 banks arm_qd = 0 as EXACT, not as a compromise.

Run: /home/rlrk/env_isaaclab7/bin/python eval_runs/.../w1_b3a_dod_legs/leg3_qd_substep_readout.py <capture.npz>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_EVAL = Path(__file__).resolve().parent.parent
_REPO = _EVAL.parent.parent
_TIL = _REPO / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import route_executor as rex  # noqa: E402

GOLDEN = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = Path(__file__).resolve().parent / "leg3_qd_substep_readout.json"

S = int(rex.SIM_SUBSTEPS)
C_PRED = (S + 1) / (2 * S)  # 0.55 for S=10: the frame-mean's interpolation weight on the END velocity
M_BAND = (S - 0.5, S + 0.5)  # the capture must be the LAST substep, resolved to +-0.5 substep
G_TOL = 0.005  # gripper only (R^2=1.000 there): rejects a +-2% scale error at ~4x the bar, both directions
R2_FLOOR = {"gripper": 0.90, "cable_hinge": 0.50}
# Cable-gain DRIFT tripwire (spec sec18 F-5 (4)): the cable channel has a measured -1.9% intrinsic bias from
# its non-monotone within-frame profile, so this is NOT a scale bar -- it is a guard that a future per-group
# capture slice (which would let a group-local scale error past the gripper-only gain bar) cannot land silently.
G_CABLE_BAND = (0.95, 1.01)


def _fit(qq, dd, dt):
    """LSQ  bwd = a*qd[f-1] + b*qd[f].  Returns (gain, m_hat, R2) or None when qd has no content."""
    bwd = (qq[1:] - qq[:-1]) / dt
    X = np.stack([dd[:-1].ravel(), dd[1:].ravel()], axis=1)
    y = bwd.ravel()
    if float(np.abs(X).max()) < 1e-15:
        return None  # a null bank has no regressors at all -> REJECT
    ab, *_ = np.linalg.lstsq(X, y, rcond=None)
    g = float(ab[0] + ab[1])
    r2 = 1.0 - float(((y - X @ ab) ** 2).sum()) / max(float((y**2).sum()), 1e-30)
    m = S * (C_PRED + 1.0 - float(ab[1]) / g) if abs(g) > 1e-9 else float("nan")
    return g, m, r2


def _judge(ch, fit):
    """Which statistic(s) reject this bank? Empty list = accepted."""
    if fit is None:
        return ["degenerate"]
    g, m, r2 = fit
    bad = []
    if ch == "gripper" and not abs(g - 1.0) <= G_TOL:
        bad.append("gain")  # the SCALE bar (bias-free channel)
    if ch == "cable_hinge" and not (G_CABLE_BAND[0] <= g <= G_CABLE_BAND[1]):
        bad.append("cable_gain_drift")  # NOT a scale bar -- the per-group-slice tripwire (spec sec18 F-5 (4))
    if not (M_BAND[0] <= m <= M_BAND[1]):
        bad.append("substep")
    if not r2 >= R2_FLOOR[ch]:
        bad.append("R2")
    return bad


def main():
    cap_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "bank_capture.npz"
    if not cap_path.is_file():
        print(f"[leg3] SKIP (capture absent: {cap_path})")
        return 0
    cap, rec = np.load(cap_path, allow_pickle=True), np.load(GOLDEN, allow_pickle=True)
    dt, na = float(rex.DT), int(rex._N_ARM_JOINTS)
    q = np.asarray(rec["arm_q"], dtype=np.float64)
    qd = np.asarray(cap["joint_qd"], dtype=np.float64)
    capq = np.asarray(cap["joint_q"], dtype=np.float64)

    # --- anchor: the capture and the recorder sample the SAME post-step state at the SAME index (EXACT) ---
    align = float(np.abs(capq - q).max())
    print(f"[leg3] frame alignment  L_inf(capture.joint_q - recording.arm_q) = {align:.3e}  over {q.shape[0]} frames")

    chans = {
        "cable_hinge": (slice(na + 7, None), slice(na + 6, None)),  # skip the free-root (7 coords / 6 dofs)
        "gripper": (sorted(rex._GRIPPER_COORDS_LOCAL),) * 2,
    }
    real, rows = {}, []
    for ch, (cq, cd) in chans.items():
        fit = _fit(q[:, cq], qd[:, cd], dt)
        real[ch] = fit
        g, m, r2 = fit
        bad = _judge(ch, fit)
        print(
            f"[leg3] REAL {ch:12s} gain={g:7.4f}  substep m_hat={m:5.2f} (pred {S})  R2={r2:6.4f}  -> "
            f"{'ACCEPT' if not bad else 'REJECT ' + ','.join(bad)}"
        )
        rows.append({"channel": ch, "gain": round(g, 4), "m_hat": round(m, 2), "r2": round(r2, 4), "reject": bad})

    # --- identifiability (ERRATUM-E col ii): every named wrong-bank must be rejected by >=1 statistic ---
    cq, cd = chans["cable_hinge"]
    qq_c, dd_c = q[:, cq], qd[:, cd]
    gq, gd = q[:, chans["gripper"][0]], qd[:, chans["gripper"][1]]
    delta = np.zeros_like(dd_c)
    delta[1:] = dd_c[1:] - dd_c[:-1]
    gdelta = np.zeros_like(gd)
    gdelta[1:] = gd[1:] - gd[:-1]
    rng = np.random.default_rng(0)
    perm = rng.permutation(dd_c.shape[1])
    # (cable variant, gripper variant, expected-accept). The wrong-bank each row names is what it rejects.
    cases = [
        ("REAL (the bank under test)", dd_c, gd, True),
        ("WRONG-SUBSTEP m=9 (1 early)", dd_c - 0.1 * delta, gd - 0.1 * gdelta, False),
        ("WRONG-SUBSTEP m=8 (2 early)", dd_c - 0.2 * delta, gd - 0.2 * gdelta, False),
        ("NULL bank (qd := 0)", np.zeros_like(dd_c), np.zeros_like(gd), False),
        ("SIGN-FLIP (qd := -qd)", -dd_c, -gd, False),
        ("SCALE x1.02", 1.02 * dd_c, 1.02 * gd, False),
        ("SCALE x0.98 (opposite sign)", 0.98 * dd_c, 0.98 * gd, False),
        ("PERMUTED coords", dd_c[:, perm], gd, False),
        ("FRAME-SHIFT (qd[f-1])", np.roll(dd_c, 1, axis=0), np.roll(gd, 1, axis=0), False),
    ]
    print(f"[leg3] identifiability: gain |g-1|<={G_TOL} (gripper) / substep m in {M_BAND} / R2 >= {R2_FLOOR}")
    ident, all_ok = [], True
    for name, cx, gx, expect in cases:
        bad_c = _judge("cable_hinge", _fit(qq_c, cx, dt))
        bad_g = _judge("gripper", _fit(gq, gx, dt))
        accepted = not (bad_c or bad_g)
        ok = accepted == expect
        all_ok = all_ok and ok
        by = "accepted" if accepted else "rejected by " + ",".join(sorted(set(bad_c + bad_g)))
        print(f"[leg3]   {name:30s} -> {by:38s} {'OK' if ok else '<-- MISS'}")
        ident.append(
            {"bank": name, "expect_accept": expect, "accepted": accepted, "rejected_by": bad_c + bad_g, "ok": ok}
        )

    verdict = align == 0.0 and not rows[0]["reject"] and not rows[1]["reject"] and all_ok
    OUT.write_text(
        json.dumps(
            {
                "what": "W1-B3a leg3: is the captured joint_qd the solver's END-OF-FRAME velocity?",
                "method": "LSQ bwd=a*qd[f-1]+b*qd[f] -> gain (scale/sign) / substep index (timing) / R2 (layout)",
                "sim_substeps": S,
                "frame_alignment_Linf": align,
                "bars": {"gain_tol_gripper": G_TOL, "substep_band": list(M_BAND), "r2_floor": R2_FLOOR},
                "real": rows,
                "identifiability": ident,
                "PASS": bool(verdict),
            },
            indent=1,
        )
    )
    print(f"[leg3] {'PASS' if verdict else 'FAIL'} -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
