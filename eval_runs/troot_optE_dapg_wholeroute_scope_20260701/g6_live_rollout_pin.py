# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""g6_live rollout (FM1) -- authorize_clip_pin live integration on the route env (cuda:0, mujoco-CPU stepping).

SINGLE-EPISODE, world_count=1 (the current firing path is world-0, once-per-lifetime, FF-replay; a multi-episode
run would re-count episode-1's never-cleared weld -- pre-check Finding 1). Validates the pin-wiring change on the
real substrate:
  * FM-E (regression): the clip-only authorizer ACCEPTS the legitimate C1 onset seat LIVE -- no crash on
    NotInAnyRouteClip / BrokenSelector. (Recorded onset seat [0.3499,0.1459,0.8287] is well inside C1; this run
    reports the LIVE onset seat dx/dy vs C1 -- the 16x-softer env C1 clip could diverge from the producer.)
  * piece 4: audit_pin_anchors runs at episode-end (guarded by route_c1_pin) without raising.
  * FM1 (coupling): with the pin holding C1, c1_retained (a hard G6 conjunct in File A) becomes reachable
    (C1 clip 16x soft / ~52.87mm escape; pin-less it never latches). Reports whether c1_retained EVER latched
    and the max G-latch reached (state read PRE-step so a done-reset never masks the terminal value).

REPLAY rollout (feedforward, zero residual): no training, no regenerated demos (FM2); c1_retention reads
cable_pos (physics), not obs, so the File-A obs-contract change is orthogonal. Physics validity of the seat is
the separate Rs human-GT (route-level anchor, LEDGER:55/57); this is the mechanism/reachability leg only.

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/g6_live_rollout_pin.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
_TIL = _EVAL.parent.parent / "thread_isaac_lab"
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
assert _CVD == "0", f"g6_live rollout runs the as-coded substrate on cuda:0 ONLY; got {_CVD!r}"

import newton_route_env as nre  # noqa: E402
import numpy as np  # noqa: E402
import route_env_config as rc  # noqa: E402
import torch  # noqa: E402
import warp as wp  # noqa: E402

GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"
OUT = _EVAL / "g6_live_rollout_pin_result.json"


def _patched_wire_c1_pin_from_recording(self):
    """TEST-HARNESS override (source UNCHANGED): derive pin onset/seat from the RAW npz, not the prepared bank.

    The env's ``_wire_c1_pin_from_recording`` reads ``self._route._recording`` (= ``_prepare_recording`` output,
    a phase state-bank that STRIPS pin_active/pin_eqid/pinned_body), so route_c1_pin=True crashes at init
    (newton_route_env.py:1678). That is a PRE-EXISTING (d2) recording-plumbing bug, orthogonal to authorize_clip_pin
    (which is at :1722, downstream). This harness patch reproduces the source logic VERBATIM but sources the pin
    fields from the raw recording so the live rollout can exercise the authorizer. step_f still comes from the
    prepared recording (present there). Surfaced as a (d2)-scaffold follow-up; NOT fixed in source (scope + the
    :1694 path is a LEDGER:52 do-not-touch confound control).
    """
    self._pin_onset_frame = None
    self._pin_seat_seg = None
    self._route_rec_step_f = None
    if not self._route_c1_pin:
        return
    self._route_rec_step_f = np.asarray(self._route._recording["step_f"]).ravel()
    raw = np.load(str(GOLDEN_NPZ), allow_pickle=True)  # <-- raw recording carries the pin fields
    pin = np.asarray(raw["pin_active"]).ravel()
    on = np.nonzero(pin > 0)[0]
    if on.size == 0:
        raise ValueError("route_c1_pin=True but the recording never pinned")
    self._pin_onset_frame = int(on[0])
    eqid = np.unique(np.asarray(raw["pin_eqid"]).ravel()[pin > 0])
    body = np.unique(np.asarray(raw["pinned_body"]).ravel()[pin > 0])
    if eqid.size != 1 or body.size != 1:
        raise ValueError(f"recording pins more than one eq/body (eq={eqid.tolist()}, body={body.tolist()})")
    seat_seg = int(eqid[0])
    n_cable = len(self._cable_bodies[0])
    if not 0 <= seat_seg < n_cable:
        raise ValueError(f"derived seat segment {seat_seg} outside this env's cable (0..{n_cable - 1})")
    self._pin_seat_seg = seat_seg
    print(f"[g6_live PATCH] pin armed from RAW npz: onset frame {self._pin_onset_frame}, seat segment {seat_seg} "
          f"(producer eq {int(eqid[0])} / body {int(body[0])})")


def main():
    assert GOLDEN_NPZ.exists(), f"golden recording missing: {GOLDEN_NPZ}"
    # harness patch: source's (d2) pin-wiring reads the prepared bank (no pin fields); read the raw npz instead.
    nre.NewtonRouteEnv._wire_c1_pin_from_recording = _patched_wire_c1_pin_from_recording
    print(f"[g6_live] building route env (route_c1_pin=True, feedforward, cuda:0) recording={GOLDEN_NPZ.name}")
    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(GOLDEN_NPZ),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
            "route_c1_pin": True,  # <-- clip-only pin ON: exercises authorize_clip_pin + audit_pin_anchors
        },
    )
    env.reset()
    cable_ids = env._cable_bodies[0]
    zero = torch.zeros((1, 6), dtype=torch.float32)

    result = {
        "pin_onset_frame": int(env._pin_onset_frame) if env._pin_onset_frame is not None else None,
        "pin_seat_seg": int(env._pin_seat_seg) if env._pin_seat_seg is not None else None,
        "pin_fired": False, "pin_fire_step": None, "pin_witness": None,
        "onset_seat_world": None, "onset_seat_dx_c1_mm": None, "onset_seat_dy_c1_mm": None,
        "authorizer_raise": None, "audit_raise": None, "other_raise": None, "early_done": None,
        "c1_retained_ever": False, "g_latched_max": [0, 0, 0, 0, 0, 0],
        "final_c1_z_mm": None, "final_flank_mm": None, "max_phase": -1, "steps_run": 0,
    }

    def _read_state():
        wp.synchronize()
        cp = env._state_0.body_q.numpy()[cable_ids, :3]
        z_c1, flank = env._c1_retention_m(cp)
        return {
            "z_c1_mm": round(float(z_c1) * 1e3, 2), "flank_mm": round(float(flank) * 1e3, 2),
            "c1_retained": bool(z_c1 < 0.840 and flank < 0.840),
            "g_latched": [int(x) for x in np.asarray(env._g_latched[0]).tolist()],
            "phase": int(env._route_phase_id[0]),
        }

    last = _read_state()
    t = 0
    try:
        while t < env.MAX_EPISODE_STEPS:
            last = _read_state()  # state ENTERING step t -- captured before any done-reset masks it
            result["c1_retained_ever"] = result["c1_retained_ever"] or last["c1_retained"]
            result["g_latched_max"] = [max(a, b) for a, b in zip(result["g_latched_max"], last["g_latched"])]
            result["max_phase"] = max(result["max_phase"], last["phase"])
            _, _, dones, _ = env.step(zero)  # exercises _maybe_activate_c1_pin -> authorize_clip_pin + audit
            result["steps_run"] = t + 1
            if env._c1_pin_witness is not None and not result["pin_fired"]:
                result["pin_fired"] = True
                result["pin_fire_step"] = t
                w = env._c1_pin_witness
                result["pin_witness"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in w.items()}
                sw = w.get("seat_world")
                if sw is not None:
                    result["onset_seat_world"] = [round(float(x), 4) for x in sw]
                    result["onset_seat_dx_c1_mm"] = round(abs(float(sw[0]) - rc.ROUTE_C1_XY[0]) * 1e3, 2)
                    result["onset_seat_dy_c1_mm"] = round(abs(float(sw[1]) - rc.ROUTE_C1_XY[1]) * 1e3, 2)
                print(f"[g6_live] PIN FIRED at RL step {t}: {result['pin_witness']}")
            if bool(dones[0]):
                result["early_done"] = t
                print(f"[g6_live] episode done at t={t} (terminal pre-reset state held in `last`)")
                break
            t += 1
    except Exception as e:  # noqa: BLE001
        name = type(e).__name__
        if name in ("NotInAnyRouteClip", "BrokenSelector"):
            result["authorizer_raise"] = f"{name}: {str(e)[:150]}"
            print(f"[g6_live] AUTHORIZER RAISED (FM-E regression!): {result['authorizer_raise']}")
        elif name == "AssertionError" and "pin anchor audit" in str(e):
            result["audit_raise"] = str(e)[:150]
            print(f"[g6_live] AUDIT RAISED: {result['audit_raise']}")
        else:
            result["other_raise"] = f"{name}: {str(e)[:200]}"
            print(f"[g6_live] OTHER RAISE: {result['other_raise']}")

    result["final_c1_z_mm"] = last["z_c1_mm"]
    result["final_flank_mm"] = last["flank_mm"]

    # verdicts: FM-E = authorizer accepted the live onset (fired, no authorizer raise); FM1 = pin -> c1_retained
    result["FM_E_authorizer_accepts_onset"] = bool(result["pin_fired"] and result["authorizer_raise"] is None)
    result["FM1_c1_retained_reachable"] = bool(
        result["pin_fired"] and result["audit_raise"] is None and result["c1_retained_ever"]
    )

    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\n[g6_live] pin_fired={result['pin_fired']}@{result['pin_fire_step']} "
          f"onset_dx={result['onset_seat_dx_c1_mm']}mm dy={result['onset_seat_dy_c1_mm']}mm | "
          f"authorizer_raise={result['authorizer_raise']} audit_raise={result['audit_raise']}")
    print(f"[g6_live] c1_retained_ever={result['c1_retained_ever']} g_latched_max={result['g_latched_max']} "
          f"max_phase={result['max_phase']} early_done={result['early_done']} steps={result['steps_run']}")
    print(f"[g6_live] FM-E(authorizer accepts onset)={result['FM_E_authorizer_accepts_onset']} | "
          f"FM1(c1_retained reachable)={result['FM1_c1_retained_reachable']}  -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
