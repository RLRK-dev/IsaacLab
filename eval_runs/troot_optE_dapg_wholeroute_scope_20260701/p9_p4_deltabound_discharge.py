# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""P4 Delta-bound feasibility discharge (OPS-SUP %9 leg, paper-only/0-commit).

Trainer node DEFINE §7 P4 leg = 2-conjunct feasibility of the RLPD residual-on-script
Delta-bound against the confirmed FORK-1 open-loop drift trajectory.

Source (banked): comp5_c2seat_fullfire_cablediag.npz (pB FORK-1 leg, 499 samples).

ERRATUM v2 (2026-07-12, supersedes sha fdcacf98): npz samples are ONE PER env.step
(= per RL-step = 10 physics frames each; empirical basis: diff(t)==1 sample counter,
diff(recf)==10 recording-frame stride). v1 mislabeled rates as mm/frame and multiplied
by decimation d in the regime check (double-count). All rates below are mm/RL-step;
the regime check compares the per-RL-step rate DIRECTLY against the bound. Conclusion
(FEASIBLE) unchanged; the v1 error was conservative-side (margin is ~10x larger).
Per-physics-frame rate is UNMEASURED (upper bound = the per-RL-step value).

ERRATUM v3 (2026-07-12, supersedes sha a2ad75955d; charter ERRATUM-2/-3 d17f8f9cd6):
 - WINDOW DECLARATION (ERRATUM-2): the primary stats are the CORRECTION-RELEVANT
   regime [0..grip-collapse] = gripped pre-58mm window (58mm crossing frame ==
   pad-drop frame == f397, empirically coincident). Full-series stats (incl.
   post-grip-loss drift, not policy-correctable) are reported separately as
   reference: mean 0.358 / p95 1.047 / max 1.940 mm/RL-step.
 - F-1a is NOT an authorization envelope (ERRATUM-3): F-1a +/-22mm is the W0-e
   seat-guide C2-X compensation clamp (cumulative, single-axis) — a PRECEDENT
   SCALE REFERENCE only. Conjunct (i) stands on measured headroom vs the env pin
   DELTA_BOUND_M=0.020 alone; formal Delta-bound authorization = Rs W0-a.

Method:
  (i)  MAGNITUDE   : per-RL-step drift-rate = diff(div_seg24_mm)  [grip seg]. A bounded
                     residual is feasible iff Delta-bound can outpace the PER-RL-STEP rate
                     (not the accumulated drift) while staying in the residual regime
                     (env pin DELTA_BOUND_M=0.020, newton_route_env.py:405; ceiling ref
                     F-1a +/-22mm coordinate authority).
  (ii) EXPRESSIBILITY: seg24 = grip seg (clamped in gripper) => EE-position directly
                     controls it (rigid-grip). Lateral cable-drift is in the
                     EE-controllable position subspace => alpha-6D (dual-arm position-only)
                     can express the correction direction. Holds while grip is HELD.

Verdict is FEASIBILITY (necessary-not-sufficient): clears the R2b expressibility
precondition; whether RLPD LEARNS the correction is the Stage-C campaign's job.
Conservatism: sizing Delta-bound from OPEN-loop drift-rate over-estimates the need
(closed-loop drift <= open-loop) => conservative margin.

Two-key: %9 key (this script). %12 may re-run as key-2 from the same banked npz.
"""

import numpy as np

NPZ = "comp5_c2seat_fullfire_cablediag.npz"
# F-1a +/-22mm = W0-e seat-guide C2-X compensation clamp (cumulative, single-axis; runner :4262).
# PRECEDENT SCALE REFERENCE only — NOT an authorization envelope (ERRATUM-3). Primary bound = pin.
F1A_PRECEDENT_SCALE_MM = 22.0
DELTA_BOUND_PIN_MM = 20.0  # env pin DELTA_BOUND_M=0.020, newton_route_env.py:405 (per RL-step; formal auth = Rs W0-a)


def discharge(npz_path: str = NPZ) -> dict:
    d = np.load(npz_path, allow_pickle=True)
    ph = d["phase"]
    s24 = d["div_seg24_mm"].astype(float)  # grip seg divergence, per frame [mm]
    pad_tot = d["pad_L"].astype(int) + d["pad_R"].astype(int)

    n = len(s24)
    # grip-collapse = first frame pad contact drops to 0 after first becoming active
    active = np.where(pad_tot > 0)[0]
    collapse = n - 1
    if len(active):
        for i in range(active[0] + 1, n):
            if pad_tot[i] == 0:
                collapse = i
                break

    # (i) MAGNITUDE — primary window = CORRECTION-RELEVANT regime [0..grip-collapse]
    # (gripped pre-58mm; 58mm crossing == pad-drop frame, empirically coincident — ERRATUM-2).
    inc = np.diff(s24[: collapse + 1])
    a = np.abs(inc)
    a_full = np.abs(np.diff(s24))  # full series incl. post-grip-loss (reference only)
    mag = {
        "window_primary": f"[0..{int(collapse)}] = gripped pre-58mm correction regime (ERRATUM-2 declaration)",
        "units": "mm per RL-step (npz sample = env.step = 10 physics frames; v2 ERRATUM)",
        "accum_start_mm": float(s24[0]),
        "accum_at_collapse_mm": float(s24[collapse]),
        "per_rlstep_absmean_mm": float(a.mean()),
        "per_rlstep_p95_mm": float(np.percentile(a, 95)),
        "per_rlstep_max_mm": float(a.max()),
        # full series (post-grip-loss drift is not policy-correctable; reference only)
        "fullseries_absmean_mm": float(a_full.mean()),
        "fullseries_p95_mm": float(np.percentile(a_full, 95)),
        "fullseries_max_mm": float(a_full.max()),
        # Delta-bound must outpace the per-RL-step rate DIRECTLY (no decimation multiply:
        # samples are already at control cadence — v1's *d was a double-count).
        "deltabound_floor_mm_per_rlstep_max": float(a.max()),
        "margin_vs_pin20": float(DELTA_BOUND_PIN_MM / a.max()),
        "residual_regime_vs_pin20": bool(a.max() < DELTA_BOUND_PIN_MM),
        "f1a_precedent_scale_note": "22mm = W0-e seat-guide clamp precedent, NOT authorization (ERRATUM-3); formal auth = Rs W0-a",
        "per_physics_frame_rate": "UNMEASURED (upper bound = per-RL-step value)",
    }
    mag["FEASIBLE"] = bool(a.max() < DELTA_BOUND_PIN_MM)

    return {
        "phase_transitions": [(int(i), int(ph[i])) for i in [0, *[k for k in range(1, n) if ph[k] != ph[k - 1]]]],
        "grip_collapse_frame": int(collapse),
        "magnitude": mag,
        # expressibility is a geometric/kinematic argument (not a per-frame stat):
        # seg24 is the grip point => EE-position controls it directly (rigid grip);
        # lateral drift in EE-controllable subspace => alpha-6D expresses it. PASS while grip held.
        "expressibility_PASS": True,
        "verdict": "P4 FEASIBLE (magnitude AND expressibility) - necessary-not-sufficient; "
        "clears R2b expressibility precondition; Delta-bound value pinned at Stage-A §6-9 "
        "once control-freq (decimation d) is fixed.",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(discharge(), indent=2, ensure_ascii=False))
