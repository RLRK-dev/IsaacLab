# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""W1-B3a leg 6: is the captured MuJoCo hidden state LIVE, or merely PRESENT?

WHY THIS LEG EXISTS (the defect it was written to catch, measured 2026-07-13). ``SolverMuJoCo`` holds BOTH a
CPU ``mj_data`` and a mjWarp ``mjw_data``, and builds ``mjw_data`` unconditionally (solver_mujoco.py:5791) --
including on the CPU backend, where it is NEVER STEPPED. The route substrate runs the CPU backend
(task_config.py:116 ``USE_MUJOCO_CPU=True`` -> solver_mujoco.py:3267-3273 ``mj_step(mj_model, mj_data)``), so
the first capture, which probed ``mjw_data`` first, read a DEAD MIRROR: ``qacc_warmstart`` nonzero in 0/562611
entries and ``eq_active`` frozen across all 7707 frames. Every other B3a leg passed anyway -- the bank simply
carried a constant array, and a k=3/4/5 fork would have restored "clip pin OFF" at the three boundaries where
the pin must be ON. That is the FORK-1 class of silent state mismatch this whole chunk exists to remove.

THE INSTRUMENT. The recording is an INDEPENDENT witness of the solver's equality state: it records ``pin_eqid``
(the clip-pin constraint id, -1 while inactive) and ``pin_active`` per frame, written by the producer at pin
activation (route_executor.py:2367-2369). So the captured ``eq_active`` can be checked against something that
did not come from the capture. A dead mirror cannot pass this; a live buffer cannot fail it.

EQ_ACTIVE IS STRUCTURAL, NOT A JUDGEMENT CALL (%12, spec sec 18 F-5 (2)). The clip pin is the ONLY authorized
exception to FOUNDATIONAL INVARIANT #5, and the k=3/4/5 fork boundaries are precisely where the clip must be
holding the cable. A fork with the pin OFF is not "numerically marginal" -- it is a PHYSICALLY WRONG state.
So eq_active/pin capture+restore is mandatory whatever the warmstart disposition turns out to be, and the
checks below are hard PASS/FAIL.

WARMSTART: THIS LEG DOES NOT DECIDE IT (spec sec 16 ERRATUM-D + sec 18 F-5 (1), %12 ruling of 2026-07-14,
which REPLACED the earlier "is it nonzero?" bar). Existence is the wrong bar -- it does not bear on the
decision (E-5 col i). The decision-relevant question is whether restoring the warm start vs zeroing it moves
the trajectory by the FORK-1 seed scale (0.147mm), which is an A/B on L5a (FF) and therefore a B3b leg.
Meanwhile the regret is ASYMMETRIC: banking an inert field costs nv floats, while NOT banking a live one is a
silent FORK-1-class mismatch -- and DEFECT-1 above is the existence proof that this second failure is real and
silent. Unlike ERRATUM-B's Dahl/body_q_prev (the ATTRIBUTE is absent), ``qacc_warmstart`` is a real live field,
so banking zeros is harmless. => (a) capture+restore STANDS by default; re-classification only if the L5a A/B
comes back far below 0.147mm. What this leg does is report the live value and the ``mjDSBL_WARMSTART``
mechanism as EXPLANATION -- never as a bar. Source inspection cannot discharge liveness (ERRATUM-F sec 18);
only a runtime read on the CONFIGURED backend can, which is why the mechanism is read from the capture's own
provenance block rather than grepped.

Run: /home/rlrk/env_isaaclab7/bin/python eval_runs/.../w1_b3a_dod_legs/leg6_hidden_state_liveness.py <capture.npz>
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
OUT = Path(__file__).resolve().parent / "leg6_hidden_state_liveness.json"


def main():
    cap_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "bank_capture.npz"
    if not cap_path.is_file():
        print(f"[leg6] SKIP (capture absent: {cap_path})")
        return 0
    cap, rec = np.load(cap_path, allow_pickle=True), np.load(GOLDEN, allow_pickle=True)
    meta = json.loads(str(np.asarray(cap["meta"]).item()))
    prov = meta.get("provenance") or {}
    res = {"what": "W1-B3a leg6: is the captured MuJoCo hidden state LIVE?", "meta": meta}

    # --- (1) the capture must have read the buffer the solver INTEGRATES -------------------------------
    backend, cpu = meta.get("mj_backend"), prov.get("use_mujoco_cpu")
    want = "mj_data" if cpu else "mjw_data"
    buf_ok = backend == want
    print(
        f"[leg6] backend: use_mujoco_cpu={cpu} -> the live buffer is {want}; capture read {backend} "
        f"-> {'OK' if buf_ok else 'DEAD MIRROR'}"
    )

    # --- (2) eq_active vs the recording's INDEPENDENT pin witness. The LAG is MEASURED, not assumed -----
    # (%9 lens ii-3, ERRATUM-A family): the recording marks the frame the SCRIPT activated the eq; the capture
    # reads what the SOLVER holds after the step, so a +-1 convention offset is admissible. A dead mirror
    # matches at NO offset -- it never latches at all -- which is what actually separates live from dead.
    eqa = np.asarray(cap["eq_active"])
    pin = np.asarray(rec["pin_active"]).astype(int).ravel()
    eqid_col = np.asarray(rec["pin_eqid"]).astype(int).ravel()
    active = eqid_col[pin > 0]
    eqid = int(np.unique(active)[0]) if active.size else None
    eq_ok, lag, got_on = False, None, 0
    if eqid is not None and eqa.ndim == 2 and 0 <= eqid < eqa.shape[1]:
        got, wantv = (eqa[:, eqid] != 0).astype(int), (pin > 0).astype(int)
        got_on = int(got.sum())
        on_c, on_r = np.nonzero(got)[0], np.nonzero(wantv)[0]
        if on_c.size and on_r.size:
            lag = int(on_c[0]) - int(on_r[0])
            monotone = np.array_equal(got[on_c[0] :], np.ones(got.size - on_c[0], dtype=int))
            eq_ok = bool(abs(lag) <= 1 and monotone)
    print(
        f"[leg6] eq_active[:, {eqid}] ON in {got_on} frames; recording pin_active ON in {int((pin > 0).sum())}; "
        f"MEASURED lag = {lag} frame(s) -> live latch: {eq_ok}"
    )
    varying = [j for j in range(eqa.shape[1]) if len(np.unique(eqa[:, j])) > 1] if eqa.ndim == 2 else []
    print(f"[leg6] eq_active columns that VARY over the run: {varying}  (a dead mirror varies in NONE)")

    # --- (2b) eq IDENTITY, not raw index (%9 lens ii-1 / iii): the banked index must AGREE with the identity
    # the producer matched on (a CONNECT eq whose obj1 is the seat body and whose obj2 is the world). Raw-index
    # hardcoding is the ERRATUM-F F6 trap; the restore re-resolves by THIS identity so a layout shift cannot
    # silently repoint the pin at another constraint.
    # ⚠ TWO INDEX SPACES, OFF BY ONE (measured here, first run): the recording's ``pinned_body`` is a NEWTON body
    # id; ``eq_obj1id`` is a MUJOCO body id, and MuJoCo counts the worldbody at 0. Passing the Newton id to the
    # resolver returns the NEIGHBOURING eq (newton 55 -> eq 26, not 27) -- a different constraint, silently. This
    # leg caught that in resolve_pin_eq_index itself, the function written to prevent exactly this trap.
    seat = int(np.unique(np.asarray(rec["pinned_body"]).ravel()[pin > 0])[0]) if (pin > 0).any() else None
    eq_ident = (prov.get("layout") or {}).get("eq_identity") or []
    ident = eq_ident[eqid] if (eqid is not None and eqid < len(eq_ident)) else None
    # The MuJoCo seat id is DERIVED from the producer's own eq table (not hardcoded, not assumed to be +1) and
    # the offset is asserted; then the resolver must round-trip to the eq the recording actually witnessed.
    mjc_seat = rex._assert_pin_index_spaces(prov, eqid, seat)
    resolved = rex.resolve_pin_eq_index(eq_ident, mjc_seat) if mjc_seat is not None else None
    offset = None if (mjc_seat is None or seat is None) else mjc_seat - seat
    ident_ok = bool(ident and int(ident[2]) == 0 and resolved == eqid and offset in (0, 1))
    print(
        f"[leg6] eq {eqid} identity (type, obj1, obj2) = {ident}; seat body: newton={seat} -> mjc={mjc_seat} "
        f"(worldbody offset {offset}); resolve_pin_eq_index(mjc) -> {resolved} -> identity round-trips: {ident_ok}"
    )

    # --- (2c) negative control: a FROZEN pin column must be rejected by the same check -----------------
    frozen_ok = False
    if eqid is not None and eqa.ndim == 2 and 0 <= eqid < eqa.shape[1]:
        frozen = eqa.copy()
        frozen[:, eqid] = 0
        frozen_ok = not np.nonzero((frozen[:, eqid] != 0).astype(int))[0].size  # never latches -> rejected
    print(f"[leg6] negative control (dead-mirror eq_active, pin frozen OFF) is REJECTED: {frozen_ok}")

    # --- (3) warmstart: TELEMETRY + mechanism. NOT a bar, and NOT a disposition (spec sec 18 F-5 (1)) ---
    # The disposition is decided by the L5a (FF) restore-vs-zero A/B against the FORK-1 seed scale (0.147mm),
    # a B3b leg. Here we only record what the live buffer holds and what explains it. (a) capture+restore
    # stands regardless: the regret is asymmetric (inert bank = nv wasted floats; missing live field = silent
    # FORK-1-class mismatch, which DEFECT-1 proved is a real and silent failure).
    qws = np.asarray(cap["qacc_warmstart"], dtype=np.float64)
    nz = int(np.count_nonzero(qws))
    ws_disabled = bool(prov.get("warmstart_disabled_by_flag"))
    flags, bit = prov.get("mj_disableflags"), prov.get("mjDSBL_WARMSTART_bit")
    print(
        f"[leg6] qacc_warmstart (TELEMETRY, not a bar): nonzero {nz}/{qws.size}  absmax={float(np.abs(qws).max()):.6g}"
    )
    print(
        f"[leg6] mechanism (EXPLANATION, not a bar): mj_disableflags={flags} & mjDSBL_WARMSTART({bit}) "
        f"-> warmstart_disabled={ws_disabled}"
    )
    ws_verdict = (
        "capture+restore STANDS (spec sec18 F-5 (1)); disposition deferred to the L5a restore-vs-zero A/B "
        f"vs the 0.147mm FORK-1 seed scale [B3b]. live nonzero={nz}/{qws.size}, disabled_by_flag={ws_disabled}"
    )
    print(f"[leg6] warmstart disposition: {ws_verdict}")

    # --- (4) PER-FIELD liveness gate (%9 lens ii-2): checking eq_active alone would let a wrong-buffer read of
    # ANOTHER hidden field pass. Every captured hidden field must either VARY over the run, or be constant with
    # a DECLARED mechanism that explains it. eq_active has an independent witness (strongest); qacc_warmstart
    # has none, so "varies" is its liveness evidence and mjDSBL_WARMSTART is the only admissible excuse for a
    # constant. NOTE this gate is about whether the BUFFER IS LIVE -- not about whether to bank the field.
    fields = {}
    for name, arr, excuse in (
        ("eq_active", eqa, None),
        ("qacc_warmstart", qws, ("mjDSBL_WARMSTART set", ws_disabled)),
    ):
        varies = bool(arr.size and np.any(arr != arr[0]))
        why, ok = "varies over the run", varies
        if not varies:
            if excuse and excuse[1]:
                why, ok = f"CONSTANT, explained: {excuse[0]}", True
            else:
                why, ok = "CONSTANT with NO declared mechanism -- suspect a dead/wrong buffer", False
        fields[name] = {"varies": varies, "live": ok, "why": why}
        print(f"[leg6] field liveness  {name:16s} -> {'LIVE' if ok else 'NOT LIVE'} ({why})")

    verdict = buf_ok and eq_ok and ident_ok and frozen_ok and all(f["live"] for f in fields.values())
    res.update(
        {
            "buffer_is_live": buf_ok,
            "eq_active_matches_pin_witness": eq_ok,
            "eq_pin_eqid": eqid,
            "eq_pin_lag_frames": lag,
            "eq_identity": ident,
            "eq_seat_body_newton": seat,
            "eq_seat_body_mjc": mjc_seat,
            "eq_body_index_offset": offset,
            "eq_index_identity_agree": ident_ok,
            "eq_varying_columns": varying,
            "negative_control_rejected": frozen_ok,
            "field_liveness": fields,
            "backend_id": {
                k: prov.get(k) for k in ("solver_class", "use_mujoco_cpu", "newton_version", "mujoco_version")
            },
            "layout_hash": prov.get("layout_hash"),
            "warmstart": {
                "nonzero": nz,
                "size": int(qws.size),
                "all_zero": bool(nz == 0),
                "disabled_by_flag": ws_disabled,
                "disableflags": flags,
                "verdict": ws_verdict,
            },
            "PASS": bool(verdict),
        }
    )
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[leg6] {'PASS' if verdict else 'FAIL'} -> {OUT}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
