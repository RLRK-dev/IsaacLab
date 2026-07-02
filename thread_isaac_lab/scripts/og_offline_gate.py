# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""E15 CP3 OG offline gate (post-train / pre-sim, mandatory; B_BC_BUILD_SPEC.md §10 E15 v2.2).

Measures decode(policy(obs))-vs-waypoint fidelity + closed-loop stability WITHOUT any sim (policy forward
+ affine decode only), then emits a phase-scoped GO / STOP / BLOCKED_FOR_USER verdict. A STOP forbids the
GPU rollout (CP4/CP5). This pass implements OG-a (static decode fidelity, the first-order gate); OG-b /
OG-b' / OG-c are added only if OG-a does not already STOP (any-STOP-wins makes them moot on a STOP).

Deployed decode path (must match the CP4 runner): a = policy.actor(obs) MEAN -> clamp[-1,1] -> per-phase
affine decode (route_demo_to_bc._abs_decode). No solver / mujoco / newton import.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

VERDICT_CRITICAL = ("C1_SEAT", "C1_PIN", "C2_REGRASP", "C2_DUAL_SEAT", "C2_SETTLE")
SEAT_Z_AXES = (2, 5)  # Rz, Lz (the 0.5mm seat knife-edge axes -> tightest bar)
GUARD2_M = 0.015  # guard-2 rate-limit: per-arm ||tgt - ee_now|| > 15mm fires
STOP_MM = 5.0  # verdict-critical p95 STOP bar
SEATZ_GO_RMSE_MM = 1.0  # verdict-critical seat-z RMSE GO bar
SWEEP_REL = 0.025  # sweep relative bar 2.5% of box span

# --- E15 v3.1 §3.2/§3.3/§3.4 phase-anchor classes + bands (og改修 items 1-4) ---
DR_MOVABLE = ("GRASP_HOVER", "GRASP_DESCEND", "GRASP_CLOSE", "LIFT")  # the only phases this cable-XY DR moves
CABLE_ANCHORED = ("C2_REGRASP",)  # moving target -> (b)-pair signature, NOT a uniform gamma_perp bar
L_HELD_PHASES = ("L_HALF_UNCLAMP", "R_UNCLAMP_RISE", "GUIDE_C2", "C2_REGRASP")  # holder = L (item 2)
GPERP_GO, GPERP_STOP = 0.5, 0.9  # gamma_perp band (movable / clip-anchored informative)
PAIR_SEG_LO, PAIR_SEG_HI = 0.8, 1.2  # (b)-pair seg-following gain PASS band (item 1)
PAIR_EE_PASS, PAIR_EE_STOP = 0.3, 0.9  # (b)-pair ee-only gain PASS / STOP (item 1)
NULL_BEAT_MARGIN = 0.15  # DR must beat the 13x-replicate null by >= this (abs, §3.4 item 4)


def _phase_class(name):
    """§3.4: MOVABLE (DR-moved, gamma_perp GO gate) / CABLE (moving target, (b)-pair) / DECOUPLED (informative)."""
    if name in DR_MOVABLE:
        return "movable"
    if name in CABLE_ANCHORED:
        return "cable"
    return "decoupled"


def _holder_axes(phase_name):
    """Item (2): the seg co-moves with the HOLDING arm's ee axes. L-held phases -> L axes (3,4,5); else R (0,1,2)."""
    return (3, 4, 5) if phase_name in L_HELD_PHASES else (0, 1, 2)


def _phase_verdict_cell(phase_name, ax, rmse_mm, p95_mm, box_mm):
    """Return (verdict, bar_mm) for one (phase, axis) cell per the E15 v2.2 phase-scoped bars."""
    if phase_name in VERDICT_CRITICAL:
        if p95_mm > STOP_MM:
            return "STOP", STOP_MM
        if ax in SEAT_Z_AXES:  # seat-z: tight GO (<=1mm RMSE); 1mm<RMSE<=5mm p95 -> MIDDLE
            return ("GO", SEATZ_GO_RMSE_MM) if rmse_mm <= SEATZ_GO_RMSE_MM else ("MIDDLE", SEATZ_GO_RMSE_MM)
        return "GO", STOP_MM  # non-seat-z verdict-critical (reach window): p95<=5mm = GO
    bar = max(STOP_MM, SWEEP_REL * box_mm)  # sweep: relative bar (unscoped 5mm false-STOPs big HOVER box)
    return ("GO" if p95_mm <= bar else "STOP"), bar


def _decode_at(policy, torch, device, obs_rows, ph_rows, affine, _abs_decode):
    """Deployed decode of a batch of (possibly perturbed) obs rows: a=actor(obs) MEAN -> clamp -> affine decode.

    Returns (tgt[N,6] float64, clamped[N] bool). clamped[i]=True if any axis of the raw actor output left [-1,1].
    """
    with torch.no_grad():
        a = policy.actor(torch.as_tensor(obs_rows, dtype=torch.float32, device=device)).cpu().numpy().astype(np.float64)
    clamped = (np.abs(a) > 1.0).any(axis=1)
    tgt = _abs_decode(np.clip(a, -1.0, 1.0), ph_rows.astype(int), affine)
    return tgt, clamped


def og_b(
    policy, torch, device, obs, ph, wp_true, affine, _abs_decode, phases13, scales_m=(0.002, 0.010), grasp_close=2
):
    """OG-b co-moving gain probe (E15 v2.1/2.2): per-step ee(+seg post-grasp) Jacobian -> tangent gamma_par /
    transverse gamma_perp (worst-case singular value on the tangent-orthogonal subspace). gamma_par~1 = benign;
    dwell (||dwp||<0.1mm) -> gamma_perp := total gain (no carve-out). clamp-active steps = gain-unmeasurable
    (excluded from the gate). Seg co-moves with the R-arm axes post-grasp (documented choice). Two scales."""
    n = obs.shape[0]
    dwp = np.zeros((n, 6))
    dwp[:-1] = wp_true[1:] - wp_true[:-1]
    dwp[-1] = dwp[-2]
    tnorm = np.linalg.norm(dwp, axis=1)
    results = {}
    for scale in scales_m:
        per_step = []
        for t in range(n):
            p = int(ph[t])
            co_seg = p >= grasp_close
            hax = _holder_axes(phases13[p])  # item (2): seg co-moves with the HOLDING arm's ee axes
            plus = np.tile(obs[t], (6, 1))
            minus = np.tile(obs[t], (6, 1))
            for ax in range(6):
                plus[ax, ax] += scale
                minus[ax, ax] -= scale
                if co_seg and ax in hax:  # seg (obs[6:9]) co-moves with the holding arm's axis (item 2)
                    plus[ax, 6 + (ax % 3)] += scale
                    minus[ax, 6 + (ax % 3)] -= scale
            tgt_p, cl_p = _decode_at(policy, torch, device, plus, np.full(6, p), affine, _abs_decode)
            tgt_m, cl_m = _decode_at(policy, torch, device, minus, np.full(6, p), affine, _abs_decode)
            jac = (tgt_p - tgt_m).T / (2.0 * scale)  # [6 tgt-dims, 6 ee-axes] = d tgt / d ee
            clamped = bool(cl_p.any() or cl_m.any())
            if tnorm[t] < 1e-4:  # dwell: no tangent carve-out
                gperp = float(np.linalg.svd(jac, compute_uv=False)[0])
                gpar, is_dwell = gperp, True
            else:
                that = dwp[t] / tnorm[t]
                gpar = float(np.linalg.norm(jac @ that))
                gperp = float(np.linalg.svd(jac @ (np.eye(6) - np.outer(that, that)), compute_uv=False)[0])
                is_dwell = False
            per_step.append((p, gpar, gperp, clamped, is_dwell))
        agg = {}
        for p in range(affine.shape[0]):
            rows = [r for r in per_step if r[0] == p]
            meas = [r for r in rows if not r[3]]
            if meas:
                agg[phases13[p]] = {
                    "n": len(rows),
                    "n_measurable": len(meas),
                    "dwell": bool(rows[0][4]),
                    "gamma_par_mean": round(float(np.mean([r[1] for r in meas])), 3),
                    "gamma_perp_mean": round(float(np.mean([r[2] for r in meas])), 3),
                    "gamma_perp_max": round(float(np.max([r[2] for r in meas])), 3),
                }
            else:
                agg[phases13[p]] = {"n": len(rows), "n_measurable": 0, "note": "all clamp-active -> unmeasurable"}
        results[f"{int(scale * 1000)}mm"] = agg
    return results


def og_bprime(
    policy,
    torch,
    device,
    obs,
    ph,
    wp_true,
    affine,
    _abs_decode,
    phases13,
    target_phases,
    n_iter=5,
    pert_m=0.005,
    grasp_close=2,
):
    """OG-b' closed-loop contraction probe (E15 v2.2): x_{k+1}=decode(pi(obs(x_k))) from wp_demo +-5mm x 3 orthogonal
    (seg co-moving, phase fixed). Metric = TRANSVERSE distance to the demo path for moving phases, fixed-point
    distance for dwell (||dwp||<0.1mm). healthy = contracts within n_iter; integrator = parallel-transport."""
    n = obs.shape[0]
    dwp = np.zeros((n, 6))
    dwp[:-1] = wp_true[1:] - wp_true[:-1]
    dwp[-1] = dwp[-2]
    out = {}
    for p in target_phases:
        rows = np.where(ph == p)[0]
        if rows.size == 0:
            continue
        t = int(rows[len(rows) // 2])
        base_obs, wpd = obs[t].copy(), wp_true[t].copy()
        co_seg = p >= grasp_close
        hoff = 3 if phases13[p] in L_HELD_PHASES else 0  # item (2): perturb + co-move the HOLDING arm
        moving = np.linalg.norm(dwp[t]) >= 1e-4
        that = (dwp[t] / np.linalg.norm(dwp[t])) if moving else None

        def _metric(x, that=that):
            dx = x - wpd
            if that is not None:  # transverse component only (healthy moving phase advances ALONG the path)
                dx = dx - np.dot(dx, that) * that
            return float(np.linalg.norm(dx))

        trajs = []
        for ax in range(3):  # holder-arm x/y/z, +- => 6 orthogonal starts (item 2)
            for sgn in (1.0, -1.0):
                d = np.zeros(6)
                d[hoff + ax] = sgn * pert_m
                x = wpd + d
                hist = [_metric(x)]
                for _ in range(n_iter):
                    o = base_obs.copy()
                    o[0:6] = x
                    if co_seg:
                        o[6:9] = base_obs[6:9] + (x[hoff : hoff + 3] - wpd[hoff : hoff + 3])
                    with torch.no_grad():
                        a = (
                            policy.actor(torch.as_tensor(o[None, :], dtype=torch.float32, device=device))
                            .cpu()
                            .numpy()[0]
                        )
                    x = _abs_decode(np.clip(a.astype(np.float64), -1.0, 1.0)[None, :], np.array([p]), affine)[0]
                    hist.append(_metric(x))
                trajs.append(hist)
        traj = np.array(trajs)  # [6, n_iter+1] transverse (or fixed-point) distances [m]
        out[phases13[p]] = {
            "metric": "transverse" if moving else "fixed_point",
            "start_dist_mm": round(float(traj[:, 0].mean()) * 1000, 3),
            "final_dist_mm_mean": round(float(traj[:, -1].mean()) * 1000, 3),
            "final_dist_mm_max": round(float(traj[:, -1].max()) * 1000, 3),
            "contracted": bool(np.all(traj[:, -1] < traj[:, 0])),
            "iter_mm_mean": [round(float(traj[:, k].mean()) * 1000, 3) for k in range(traj.shape[1])],
        }
    return out


def og_c(policy, torch, device, obs_demo, ph, affine, _abs_decode, b0a_obs_path):
    """OG-c empirical-gain regression (E15 v2.1): on the B0a real closed-loop obs, regress decode-target drift vs
    ee-obs drift (both vs the demo). slope~1 = integrator (target follows the realized drift); slope~0 = restoring."""
    if not os.path.exists(b0a_obs_path):
        return {"note": "b0a obs_series.npy NOT found", "path": b0a_obs_path}
    obs_real = np.load(b0a_obs_path).astype(np.float64)
    m = min(obs_real.shape[0], obs_demo.shape[0])
    obs_real, obs_d, ph2 = obs_real[:m], obs_demo[:m], ph[:m]
    tgt_real, _ = _decode_at(policy, torch, device, obs_real, ph2, affine, _abs_decode)
    tgt_demo, _ = _decode_at(policy, torch, device, obs_d, ph2, affine, _abs_decode)
    obs_dev = np.linalg.norm(obs_real[:, 0:6] - obs_d[:, 0:6], axis=1)
    dec_dev = np.linalg.norm(tgt_real - tgt_demo, axis=1)
    slope, intercept = np.linalg.lstsq(np.vstack([obs_dev, np.ones(m)]).T, dec_dev, rcond=None)[0]
    return {
        "empirical_gain_slope": round(float(slope), 4),
        "intercept_mm": round(float(intercept) * 1000, 3),
        "obs_dev_max_mm": round(float(obs_dev.max()) * 1000, 2),
        "dec_dev_max_mm": round(float(dec_dev.max()) * 1000, 2),
        "note": "slope~1 = integrator (target follows realized drift); slope~0 = restoring",
    }


def og_b_pair(policy, torch, device, obs, ph, affine, _abs_decode, phase_idx, scale_m=0.002):
    """Item (1): cable-anchored (b)-pair for C2_REGRASP (R = acting arm, L = holder). A single gamma_perp is
    WRONG-SIGNED here (correct cable-following shows as ~1). Two gains via central differences:
      seg-following = |d(R target)/d(cable move)| where the cable move perturbs {L-ee(3:6) + seg(6:9)} together
        -> ~1 = R tracks the L-held cable;
      ee-only = |d(R target)/d(R-ee(0:3))| with the cable (seg) FIXED -> ~0 = restores to the cable (no self-drift).
    Averaged over the 3 axes then the phase steps. PASS = seg in [0.8,1.2] AND ee-only <= 0.3; ee-only >= 0.9 = STOP."""
    rows = np.where(ph == phase_idx)[0]
    if rows.size == 0:
        return {"note": "phase absent", "verdict": "unmeasurable"}
    seg_gains, ee_gains = [], []
    for t in rows:
        base = obs[t]
        pert = []  # 12 rows: cable-move (3 axes +/-) then ee-only (3 axes +/-)
        for k in range(3):  # cable move: L-ee(3+k) + seg(6+k) together
            pp, mm = base.copy(), base.copy()
            for d in (3 + k, 6 + k):
                pp[d] += scale_m
                mm[d] -= scale_m
            pert += [pp, mm]
        for k in range(3):  # ee-only: R-ee(0+k), seg fixed
            pp, mm = base.copy(), base.copy()
            pp[k] += scale_m
            mm[k] -= scale_m
            pert += [pp, mm]
        tgt, _ = _decode_at(policy, torch, device, np.array(pert), np.full(12, phase_idx), affine, _abs_decode)
        sg = [abs(tgt[2 * k][k] - tgt[2 * k + 1][k]) / (2.0 * scale_m) for k in range(3)]  # R tgt axis-k resp
        eg = [abs(tgt[6 + 2 * k][k] - tgt[6 + 2 * k + 1][k]) / (2.0 * scale_m) for k in range(3)]
        seg_gains.append(float(np.mean(sg)))
        ee_gains.append(float(np.mean(eg)))
    seg_follow, ee_only = float(np.mean(seg_gains)), float(np.mean(ee_gains))
    if PAIR_SEG_LO <= seg_follow <= PAIR_SEG_HI and ee_only <= PAIR_EE_PASS:
        verdict = "PASS"
    elif ee_only >= PAIR_EE_STOP:
        verdict = "STOP"
    else:
        verdict = "MIDDLE"
    return {
        "seg_following_gain": round(seg_follow, 3),
        "ee_only_gain": round(ee_only, 3),
        "verdict": verdict,
        "n_steps": int(rows.size),
        "bands": {"seg_PASS": [PAIR_SEG_LO, PAIR_SEG_HI], "ee_PASS_le": PAIR_EE_PASS, "ee_STOP_ge": PAIR_EE_STOP},
    }


def main():
    ap = argparse.ArgumentParser(description="E15 CP3 OG offline gate (OG-a[/b/b'/c]) -> GO/STOP/BLOCKED verdict")
    ap.add_argument("--dataset-abs", required=True, help="bc_dataset_abs.npz (obs, abs labels, meta.abs_affine)")
    ap.add_argument("--policy", required=True, help="policy_abs.pt (RSL-RL {model_state_dict})")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument(
        "--full", action="store_true", help="also run OG-b/b'/c (co-moving gain + contraction + regression)"
    )
    ap.add_argument("--b0a-obs", default="", help="b0a_full/obs_series.npy for OG-c regression (empty -> skip)")
    ap.add_argument(
        "--null-og", default="", help="null (13x-replicate) og_gate.json for the null-beat precondition (§3.4 item 4)"
    )
    ap.add_argument(
        "--carried-stops",
        default="",
        help="comma-sep DECOUPLED phase names whose STOP is n=1-carried -> informative (§3.4)",
    )
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import torch  # noqa: PLC0415
    from bc_pretrain import build_actor_critic  # noqa: PLC0415
    from route_demo_to_bc import ABS_AXIS_NAMES, PHASES13, _abs_decode  # noqa: PLC0415

    z = np.load(args.dataset_abs, allow_pickle=True)
    obs = z["obs"].astype(np.float64)  # [T, 12+n_phases] (25=13-schema / 27=15-schema)
    labels = z["actions"].astype(np.float64)  # [T,6] abs labels
    meta = json.loads(str(z["meta"]))
    affine = np.asarray(meta["abs_affine"], np.float64)  # [n_phases,6,2]
    n_phases = affine.shape[0]  # 13 (B0/B1) or 15 (B2 schema-v2) -- item (4)
    obs_dim = obs.shape[1]  # 12 continuous + n_phases one-hot
    PHASES = tuple(meta.get("phase_names") or PHASES13)  # schema-agnostic phase names (item 4/8)
    ph = np.argmax(obs[:, 12 : 12 + n_phases], axis=1).astype(int)  # phase per control step (one-hot argmax)
    wp_true = _abs_decode(labels, ph, affine)  # [T,6] true next EE targets (round-trip exact)
    ee_now = obs[:, 0:6]  # ee_r(0:3), ee_l(3:6)

    # --- deployed decode path: a = policy.actor(obs) MEAN -> clamp -> per-phase affine decode ---
    policy = build_actor_critic(obs_dim, 6, (128, 128), args.device)
    policy.load_state_dict(torch.load(args.policy, map_location=args.device)["model_state_dict"])
    policy.eval()
    with torch.no_grad():
        a_pred = policy.actor(torch.as_tensor(obs, dtype=torch.float32, device=args.device)).cpu().numpy()
    a_pred = a_pred.astype(np.float64)
    a_clamp = np.clip(a_pred, -1.0, 1.0)
    clamp_counts = [int((np.abs(a_pred[:, ax]) > 1.0).sum()) for ax in range(6)]  # per-axis off-manifold diag
    tgt_pred = _abs_decode(a_clamp, ph, affine)  # [770,6]
    err_mm = (tgt_pred - wp_true) * 1000.0  # [770,6]

    # --- OG-a per-phase x per-axis table + phase-scoped verdict ---
    table, stops, middles = [], [], []
    for p in range(n_phases):
        idx = np.where(ph == p)[0]
        rmse = np.sqrt((err_mm[idx] ** 2).mean(axis=0))
        p95 = np.percentile(np.abs(err_mm[idx]), 95, axis=0)
        for ax in range(6):
            box_mm = (affine[p, ax, 1] - affine[p, ax, 0]) * 1000.0
            verdict, bar = _phase_verdict_cell(PHASES[p], ax, float(rmse[ax]), float(p95[ax]), box_mm)
            cell = {
                "phase": PHASES[p],
                "axis": ABS_AXIS_NAMES[ax],
                "n": int(idx.size),
                "rmse_mm": round(float(rmse[ax]), 3),
                "p95_mm": round(float(p95[ax]), 3),
                "box_mm": round(box_mm, 2),
                "bar_mm": round(bar, 3),
                "verdict_critical": PHASES[p] in VERDICT_CRITICAL,
                "cell_verdict": verdict,
            }
            table.append(cell)
            if verdict == "STOP":
                stops.append(cell)
            elif verdict == "MIDDLE":
                middles.append(cell)

    # --- boundary jumps: |a_pred| jump across the 12 phase transitions ---
    trans = np.where(np.diff(ph) != 0)[0]
    boundary_jumps = [
        {
            "at_step": int(t),
            "from": PHASES[ph[t]],
            "to": PHASES[ph[t + 1]],
            "max_da": round(float(np.abs(a_pred[t + 1] - a_pred[t]).max()), 4),
        }
        for t in trans
    ]

    # --- expected guard-2 fire set: per-arm ||tgt_pred - ee_now|| > 15mm ---
    d_r = np.linalg.norm(tgt_pred[:, 0:3] - ee_now[:, 0:3], axis=1)
    d_l = np.linalg.norm(tgt_pred[:, 3:6] - ee_now[:, 3:6], axis=1)
    g2_fires = {
        "R": [int(i) for i in np.where(d_r > GUARD2_M)[0]],
        "L": [int(i) for i in np.where(d_l > GUARD2_M)[0]],
        "R_max_mm": round(float(d_r.max()) * 1000.0, 2),
        "L_max_mm": round(float(d_l.max()) * 1000.0, 2),
    }

    # --- OG-b/b'/c (E15 required legs; --full) + residual-cell targeting (%12 CP3-A instruction b) ---
    residual_cells = [c for c in stops if not c["verdict_critical"]] + middles  # sweep-STOP + seat-z MIDDLE
    residual_phases = sorted({c["phase"] for c in residual_cells})
    og_b_res = og_bp_res = og_c_res = None
    ogb_gate = {}
    if args.full:
        og_b_res = og_b(policy, torch, args.device, obs, ph, wp_true, affine, _abs_decode, PHASES)
        target_idx = sorted(
            {PHASES.index(p) for p in VERDICT_CRITICAL if p in PHASES}
            | {PHASES.index(p) for p in residual_phases if p in PHASES}
        )
        og_bp_res = og_bprime(policy, torch, args.device, obs, ph, wp_true, affine, _abs_decode, PHASES, target_idx)
        og_c_res = (
            og_c(policy, torch, args.device, obs, ph, affine, _abs_decode, args.b0a_obs)
            if args.b0a_obs
            else {"note": "skipped (no --b0a-obs)"}
        )
        # item (1)+(4): anchor-class dispatch over {movable 0-3} ∪ {cable C2_REGRASP} ∪ {decoupled informative}
        prim = og_b_res.get("2mm", {})  # OG-b primary 2mm scale (all phases; item 4 surfaces movable {0-3})
        pair_res = og_b_pair(policy, torch, args.device, obs, ph, affine, _abs_decode, PHASES.index("C2_REGRASP"))
        for p in range(n_phases):
            name = PHASES[p]
            cls = _phase_class(name)
            if cls == "cable":  # item (1): (b)-pair, NOT gamma_perp (wrong-signed for a moving target)
                cell = {"PASS": "GO", "STOP": "STOP", "MIDDLE": "MIDDLE"}.get(pair_res.get("verdict"), "unmeasurable")
                ogb_gate[name] = {"class": "cable", "gate": cell, "pair": pair_res}
            else:  # movable = GO-gating / decoupled = informative: gamma_perp band
                gp = prim.get(name, {}).get("gamma_perp_mean")
                band = (
                    "unmeasurable"
                    if gp is None
                    else ("STOP" if gp >= GPERP_STOP else ("GO" if gp <= GPERP_GO else "MIDDLE"))
                )
                ogb_gate[name] = {"class": cls, "gate": band, "gamma_perp_mean": gp}

    # --- null-beat precondition (§3.4 item 4): DR must beat the 13x-replicate null by >= margin (abs) ---
    def _beat_metric(gate):  # worst-demo gamma_perp over movable {0-3} + C2_REGRASP ee-only gain (lower = better)
        vals = [
            v["gamma_perp_mean"]
            for v in gate.values()
            if v.get("class") == "movable" and v.get("gamma_perp_mean") is not None
        ]
        cab = next((v for v in gate.values() if v.get("class") == "cable"), None)
        if cab and cab.get("pair", {}).get("ee_only_gain") is not None:
            vals.append(cab["pair"]["ee_only_gain"])
        return round(max(vals), 4) if vals else None

    dr_metric = _beat_metric(ogb_gate) if ogb_gate else None
    null_metric = null_beat = None
    if args.null_og and os.path.exists(args.null_og):
        with open(args.null_og) as fh:
            null_metric = _beat_metric(json.load(fh).get("ogb_anchor_gate", {}))
        if dr_metric is not None and null_metric is not None:
            null_beat = round(null_metric - dr_metric, 4)  # >0 = DR improves (lower worst-gain) vs null

    # --- combined gate: §3.3 pre-declared verdict table (item 3, 3-priority; decoupled middle EXEMPT) ---
    carried = {s.strip() for s in args.carried_stops.split(",") if s.strip()}
    oga_verdict = "STOP" if stops else "GO"  # STOP = hard decode fault; seat-z MIDDLE = decoupled-informative (§3.3)

    def _noncarried_stop(n, v):  # decoupled carried-STOP -> informative; every other STOP counts
        return v["gate"] == "STOP" and not (v["class"] == "decoupled" and n in carried)

    ogb_stop = any(_noncarried_stop(n, v) for n, v in ogb_gate.items())
    movable = {n: v for n, v in ogb_gate.items() if v["class"] == "movable"}
    cable_v = next((v for v in ogb_gate.values() if v["class"] == "cable"), None)
    movable_all_go = bool(movable) and all(v["gate"] == "GO" for v in movable.values())
    pair_pass = cable_v is not None and cable_v["gate"] == "GO"
    null_beat_ok = null_beat is not None and null_beat >= NULL_BEAT_MARGIN
    go_conditions = {
        "oga_no_stop": not stops,
        "movable_all_GO": movable_all_go,
        "cable_pair_PASS": pair_pass,
        "null_beat_ge_margin": null_beat_ok,
    }
    if stops or ogb_stop:  # priority 1: any non-carried STOP -> STOP
        overall = "STOP"
    elif all(go_conditions.values()):  # priority 2: GO
        overall = "GO"
    else:  # priority 3: BLOCKED_FOR_USER (decoupled middles EXEMPT by construction)
        overall = "BLOCKED_FOR_USER"
    if not ogb_gate:
        ogb_verdict = "not_run"
    elif ogb_stop:
        ogb_verdict = "STOP"
    elif movable_all_go and pair_pass:
        ogb_verdict = "GO"
    else:
        ogb_verdict = "BLOCKED_FOR_USER"
    out = {
        "og_pass": "OG-a+b+bprime+c" if args.full else "OG-a",
        "overall_verdict": overall,
        "oga_verdict": oga_verdict,
        "ogb_verdict": ogb_verdict,
        "overall_note": "STOP/BLOCKED -> no GPU (HOLD, spec:154). §3.3 3-priority verdict table (v3.1): "
        "non-carried STOP -> STOP / GO iff movable-all-GO & cable-pair-PASS & null-beat>=margin / else BLOCKED; "
        "decoupled middles EXEMPT. OG-b'/c = closed-loop characterization.",
        "verdict_table": {
            "go_conditions": go_conditions,
            "null_beat": null_beat,
            "null_beat_margin": NULL_BEAT_MARGIN,
            "dr_worst_metric": dr_metric,
            "null_worst_metric": null_metric,
            "carried_stops": sorted(carried),
        },
        "n_stop_cells": len(stops),
        "n_middle_cells": len(middles),
        "residual_phases": residual_phases,
        "ogb_anchor_gate": ogb_gate,
        "og_b": og_b_res,
        "og_bprime": og_bp_res,
        "og_c": og_c_res,
        "stops": stops,
        "middles": middles,
        "per_axis_clamp_counts": dict(zip(ABS_AXIS_NAMES, clamp_counts)),
        "boundary_jumps": boundary_jumps,
        "guard2_expected_fires": {
            "R_count": len(g2_fires["R"]),
            "L_count": len(g2_fires["L"]),
            "R_max_mm": g2_fires["R_max_mm"],
            "L_max_mm": g2_fires["L_max_mm"],
        },
        "table": table,
        "provenance": {
            "dataset_abs": os.path.basename(args.dataset_abs),
            "policy": os.path.basename(args.policy),
            "action_repr": meta.get("action_repr"),
        },
    }
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "og_gate.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    # --- human table (verdict-critical rows first) ---
    print("=== OG-a decode-mm RMSE (verdict-critical phases) ===")
    print(f"{'phase':16s}{'axis':5s}{'n':>4s}{'rmse_mm':>10s}{'p95_mm':>10s}{'bar_mm':>9s}  verdict")
    for c in table:
        if c["verdict_critical"]:
            print(
                f"{c['phase']:16s}{c['axis']:5s}{c['n']:>4d}{c['rmse_mm']:>10.3f}{c['p95_mm']:>10.3f}"
                f"{c['bar_mm']:>9.2f}  {c['cell_verdict']}"
            )
    print(f"\nper-axis clamp counts (off-manifold): {dict(zip(ABS_AXIS_NAMES, clamp_counts))}")
    print(
        f"guard-2 expected fires: R={len(g2_fires['R'])} (max {g2_fires['R_max_mm']}mm) / "
        f"L={len(g2_fires['L'])} (max {g2_fires['L_max_mm']}mm)"
    )
    print(f"boundary max|da|: {max((b['max_da'] for b in boundary_jumps), default=0):.4f}")
    print(f"\n=== OG-a verdict: {oga_verdict} ===  (STOP cells={len(stops)}, MIDDLE cells={len(middles)})")
    if stops:
        print("  worst STOP cells:")
        for c in sorted(stops, key=lambda x: -x["p95_mm"])[:8]:
            print(f"    {c['phase']}/{c['axis']}: p95={c['p95_mm']}mm rmse={c['rmse_mm']}mm (bar {c['bar_mm']}mm)")
    if args.full:
        print("\n=== OG-b anchor-class gate (2mm; movable=GO-gating γ⊥ / cable=(b)-pair / decoupled=informative) ===")
        for name, v in ogb_gate.items():
            if v["class"] == "cable":
                pr = v["pair"]
                print(
                    f"  {name:14s} [cable   ] seg_follow={pr.get('seg_following_gain', '?')} "
                    f"ee_only={pr.get('ee_only_gain', '?')} -> {v['gate']} (pair={pr.get('verdict', '?')})"
                )
            else:
                print(f"  {name:14s} [{v['class']:8s}] gamma_perp={v.get('gamma_perp_mean', '?')} -> {v['gate']}")
        print(f"  verdict-table GO conditions: {go_conditions} | null_beat={null_beat} (>= {NULL_BEAT_MARGIN}?)")
        print("\n=== OG-b' contraction (verdict-critical + residual; contracts within 5 iters?) ===")
        for pn, r in (og_bp_res or {}).items():
            print(
                f"  {pn:14s} [{r['metric']:11s}] start={r['start_dist_mm']}mm -> "
                f"final_mean={r['final_dist_mm_mean']}mm (max {r['final_dist_mm_max']}) contracted={r['contracted']}"
            )
        print(f"\n=== OG-c empirical gain (b0a real closed-loop): {og_c_res} ===")
    print(f"\n=== CP3 COMBINED OVERALL: {overall} ===  (OG-a={oga_verdict}, OG-b={ogb_verdict})")


if __name__ == "__main__":
    main()
