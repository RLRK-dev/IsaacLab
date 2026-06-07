# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dry-run IK verification for 39-step routing motion sequence.

Tests reachability and inter-arm collision clearance for the full
5-clip routing motion sequence. No cable, no physics — pure FK + IK.

Verifies:
  1. Both arms can reach every step's target positions (IK error < threshold)
  2. Forearm/wrist/EE links do not overlap (collision clearance > 0)
  3. For regrasp steps, tests both guide-hand assignments (L/R)

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_motion_sequence_dry_run.py
    # Use specific GPU:
    NEWTON_DEVICE=cuda:1 OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_motion_sequence_dry_run.py
"""

import json
import math
import os
import sys

import numpy as np

# Ensure script directory is on path for sibling imports
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import warp as wp  # noqa: E402
import newton  # noqa: E402

from newton_routing_utils import (  # noqa: E402
    FRANKA_NUM_JOINTS, EE_BODY_OFFSET, GRIP_OFFSET,
    COLLISION_SPHERE_RADII, COLLISION_PAIRS,
    build_fk_model, init_fk_state,
    solve_ik_dual, eval_ik_errors,
    assign_groove_angles,
)
from task_config import TABLE_HEIGHT, EE_TO_FINGERTIP, GRASP_X  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")

LIFT_Z = TABLE_HEIGHT + EE_TO_FINGERTIP + 0.100   # 1.120m (body6), fingertip 100mm above table
GRASP_Z = TABLE_HEIGHT + EE_TO_FINGERTIP           # 1.020m (body6), fingertip at table

# Home positions (safe rest, well separated)
HOME_LEFT = (0.10, -0.30, LIFT_Z)
HOME_RIGHT = (0.10, 0.30, LIFT_Z)

# S-curve 5-clip layout
CLIP_POSITIONS = [
    (0.33, 0.10),   # C0
    (0.38, 0.02),   # C1
    (0.42, -0.07),  # C2
    (0.38, -0.14),  # C3
    (0.32, -0.19),  # C4
]

IK_ERR_THRESHOLD_MM = 5.0
WARN_CLEARANCE_MM = 10.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def grip_positions(cx, cy, theta):
    """Left/right grip positions from clip center and groove angle.

    Assigns the grip with more negative Y to left arm (base Y=-0.35)
    and more positive Y to right arm (base Y=+0.35) to minimize reach.
    """
    dx = GRIP_OFFSET * math.cos(theta)
    dy = GRIP_OFFSET * math.sin(theta)
    g_a = (cx - dx, cy - dy)
    g_b = (cx + dx, cy + dy)
    # Assign by Y: smaller Y → left arm, larger Y → right arm
    if g_a[1] <= g_b[1]:
        return g_a, g_b  # left=g_a, right=g_b
    else:
        return g_b, g_a  # left=g_b, right=g_a


def regrasp_xy(prev_xy, next_xy):
    """Cable regrasp position: 60% from prev clip toward next clip."""
    px, py = prev_xy
    nx, ny = next_xy
    return (px + 0.6 * (nx - px), py + 0.6 * (ny - py))


def collision_clearance(fk_model, fk_state):
    """Min clearance (mm) between all cross-arm collision pairs. Returns (clearance, pair)."""
    bq = fk_state.body_q.numpy()
    best = float("inf")
    worst = None
    for l_loc, r_loc in COLLISION_PAIRS:
        l_idx = l_loc
        r_idx = r_loc + FRANKA_NUM_JOINTS
        d = float(np.linalg.norm(bq[l_idx][:3] - bq[r_idx][:3]))
        rl = COLLISION_SPHERE_RADII.get(l_loc, 0.030)
        rr = COLLISION_SPHERE_RADII.get(r_loc, 0.030)
        c = (d - rl - rr) * 1000.0
        if c < best:
            best = c
            worst = (l_loc, r_loc)
    return best, worst


def solve_and_eval(fk_model, fk_state, tgt_l, tgt_r, prev_jq):
    """Solve IK, evaluate errors and clearance. Returns dict."""
    fk_state.joint_q.assign(prev_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    jq, cost = solve_ik_dual(fk_model, fk_state, tgt_l, tgt_r, DEVICE,
                             iterations=150, collision_avoidance=True)
    err_l, err_r = eval_ik_errors(fk_model, fk_state, jq, tgt_l, tgt_r)
    clr, pair = collision_clearance(fk_model, fk_state)

    max_err = max(err_l, err_r)
    if max_err > IK_ERR_THRESHOLD_MM:
        status = "FAIL-IK"
    elif clr < 0:
        status = "FAIL-COL"
    elif clr < WARN_CLEARANCE_MM:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "jq": jq,
        "err_l": err_l, "err_r": err_r, "max_err": max_err,
        "clearance": clr, "pair": pair,
        "status": status, "cost": cost,
    }


# ---------------------------------------------------------------------------
# Motion sequence builder
# ---------------------------------------------------------------------------
def build_sequence(clips, thetas, cable_xy):
    """Build full motion sequence with action types for wet-run execution.

    Returns list of dicts, each with:
        step, desc, target_l, target_r, is_regrasp,
        action_type, clip_index, guide_hand
    """
    seq = []
    grips = [grip_positions(cx, cy, th) for (cx, cy), th in zip(clips, thetas)]

    cable_l = (cable_xy[0], cable_xy[1] - GRIP_OFFSET)
    cable_r = (cable_xy[0], cable_xy[1] + GRIP_OFFSET)

    def add(step, desc, tl, tr, action_type="ik_move",
            clip_index=None, guide_hand=None, regrasp=False):
        seq.append({
            "step": step, "desc": desc,
            "target_l": list(tl), "target_r": list(tr),
            "action_type": action_type,
            "clip_index": clip_index,
            "guide_hand": guide_hand,
            "is_regrasp": regrasp,
        })

    # --- Phase A: Initial Grasp (1-5) ---
    add(1, "Home (origin)", HOME_LEFT, HOME_RIGHT)
    add(2, "上昇点(cable)", (*cable_l, LIFT_Z), (*cable_r, LIFT_Z))
    add(3, "下降点(cable)", (*cable_l, GRASP_Z), (*cable_r, GRASP_Z))
    add(4, "下降点(cable)+clamp", (*cable_l, GRASP_Z), (*cable_r, GRASP_Z),
        action_type="grasp")
    add(5, "上昇点(cable)+lift", (*cable_l, LIFT_Z), (*cable_r, LIFT_Z))

    # --- Phase B: C0 routing (6-10) ---
    gl, gr = grips[0]
    add(6, "上昇点(C0)", (*gl, LIFT_Z), (*gr, LIFT_Z), clip_index=0)
    add(7, "下降点(C0)", (*gl, GRASP_Z), (*gr, GRASP_Z), clip_index=0)
    add(8, "下降点(C0) half-unclamp", (*gl, GRASP_Z), (*gr, GRASP_Z),
        action_type="half_release", clip_index=0, guide_hand="L")
    add(9, "下降点(C0) clip-clamp", (*gl, GRASP_Z), (*gr, GRASP_Z),
        action_type="clip_lock", clip_index=0)
    add(10, "上昇点(C0)", (*gl, LIFT_Z), (*gr, LIFT_Z),
        action_type="release_rise", clip_index=0, guide_hand="L")

    # --- Phase C+D: C1-C4 (11-38) ---
    s = 11
    for i in range(1, 5):
        gl, gr = grips[i]
        cx, cy = clips[i]
        px, py = clips[i - 1]

        # Regrasp position along cable between prev and current clip
        rx, ry = regrasp_xy((px, py), (cx, cy))
        rgl, rgr = grip_positions(rx, ry, thetas[i])

        # C: Transition — guide hand to HALF_OPEN per routing spec
        add(s,     f"上昇点(C{i}) both",     (*gl, LIFT_Z),  (*gr, LIFT_Z),
            action_type="guide_transition", clip_index=i, guide_hand="L")
        add(s + 1, f"C{i} L-guide R-regrasp", (*gl, LIFT_Z),  (*rgr, LIFT_Z),
            action_type="regrasp", clip_index=i, guide_hand="L", regrasp=True)
        add(s + 2, f"C{i} both clamp",        (*gl, LIFT_Z),  (*rgr, LIFT_Z),
            action_type="grasp", clip_index=i)

        # D: Clip routing — guide hand stays HALF_OPEN except last clip
        guide_for_release = "L" if i < 4 else None
        add(s + 3, f"下降点(C{i})",           (*gl, GRASP_Z), (*gr, GRASP_Z),
            clip_index=i)
        add(s + 4, f"下降点(C{i}) clip-clamp", (*gl, GRASP_Z), (*gr, GRASP_Z),
            action_type="clip_lock", clip_index=i)
        add(s + 5, f"下降点(C{i}) unclamp",   (*gl, GRASP_Z), (*gr, GRASP_Z),
            action_type="release", clip_index=i, guide_hand=guide_for_release)
        add(s + 6, f"上昇点(C{i})",           (*gl, LIFT_Z),  (*gr, LIFT_Z),
            clip_index=i)
        s += 7

    # --- Final: return home ---
    add(s, "Home (origin)", HOME_LEFT, HOME_RIGHT)

    return seq


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 90)
    print("  Motion Sequence Dry-Run: IK Reachability + Collision Check")
    print("=" * 90)

    wp.init()
    fk_model = build_fk_model(DEVICE)
    fk_state = init_fk_state(fk_model, finger_open=True)
    home_jq = fk_state.joint_q.numpy().copy()

    # Layout
    route = list(range(len(CLIP_POSITIONS)))
    thetas = assign_groove_angles(CLIP_POSITIONS, route, seed=42)

    print(f"\n[LAYOUT] S-curve 5-clip (GRIP_OFFSET={GRIP_OFFSET * 1000:.0f}mm):")
    for i, (cx, cy) in enumerate(CLIP_POSITIONS):
        gl, gr = grip_positions(cx, cy, thetas[i])
        print(f"  C{i}: ({cx:.2f}, {cy:+.2f})  θ={math.degrees(thetas[i]):+.0f}°"
              f"  L=({gl[0]:.3f},{gl[1]:+.3f})  R=({gr[0]:.3f},{gr[1]:+.3f})")

    cable_cx = GRASP_X
    cable_cy = float(np.mean([p[1] for p in CLIP_POSITIONS]))
    print(f"\n[CABLE] Center: ({cable_cx:.2f}, {cable_cy:+.3f})")
    print(f"[HEIGHT] LIFT_Z={LIFT_Z:.3f}m (body6), GRASP_Z={GRASP_Z:.3f}m (body6)")

    seq = build_sequence(CLIP_POSITIONS, thetas, (cable_cx, cable_cy))
    print(f"\n[SEQUENCE] {len(seq)} steps\n")

    hdr = (f"{'STEP':>4} {'Description':<28} {'ErrL':>6} {'ErrR':>6} {'MaxE':>6}"
           f" {'Clr':>6} {'Pair':>7} {'Status':>8}")
    print(hdr)
    print("-" * len(hdr))

    results = []
    prev_jq = home_jq.copy()
    n_pass = n_warn = n_fail = 0
    prev_targets = None
    last_good_jq = home_jq.copy()

    for step_info in seq:
        step_num = step_info["step"]
        desc = step_info["desc"]
        tgt_l = tuple(step_info["target_l"])
        tgt_r = tuple(step_info["target_r"])
        is_regrasp = step_info["is_regrasp"]
        action_type = step_info["action_type"]
        clip_index = step_info.get("clip_index")
        guide_hand = step_info.get("guide_hand")

        cur_targets = (tgt_l, tgt_r)

        # Skip redundant IK if targets unchanged (finger-only step)
        if prev_targets and cur_targets == prev_targets:
            r = results[-1].copy()
            r["step"] = step_num
            r["desc"] = desc
            r["action_type"] = action_type
            r["clip_index"] = clip_index
            r["guide_hand"] = guide_hand
            r["status"] = results[-1]["status"]
            results.append(r)
            pair = r.get("pair", (0, 0))
            pair_str = f"L{pair[0]}-R{pair[1]}" if pair else ""
            print(f"{step_num:>4} {desc:<28} {'(same targets — skipped)':>50}")
            if r["status"] == "PASS":
                n_pass += 1
            elif r["status"] == "WARN":
                n_warn += 1
            else:
                n_fail += 1
            continue

        # Try warm-start from previous solution AND from home, pick the better one
        r1 = solve_and_eval(fk_model, fk_state, tgt_l, tgt_r, prev_jq)
        r2 = solve_and_eval(fk_model, fk_state, tgt_l, tgt_r, home_jq)
        r = r1 if r1["max_err"] <= r2["max_err"] else r2

        pair_str = f"L{r['pair'][0]}-R{r['pair'][1]}" if r["pair"] else ""
        print(f"{step_num:>4} {desc:<28} {r['err_l']:>5.1f}mm {r['err_r']:>5.1f}mm"
              f" {r['max_err']:>5.1f}mm {r['clearance']:>5.0f}mm {pair_str:>7} {r['status']:>8}")

        # For regrasp steps, also test the mirror assignment (R-guide, L-regrasp)
        if is_regrasp:
            r_alt1 = solve_and_eval(fk_model, fk_state, tgt_r, tgt_l, prev_jq)
            r_alt2 = solve_and_eval(fk_model, fk_state, tgt_r, tgt_l, home_jq)
            r_alt = r_alt1 if r_alt1["max_err"] <= r_alt2["max_err"] else r_alt2
            desc_alt = desc.replace("L-guide R-regrasp", "R-guide L-regrasp")
            pair_alt = f"L{r_alt['pair'][0]}-R{r_alt['pair'][1]}" if r_alt["pair"] else ""
            print(f"{'':>4} {desc_alt:<28} {r_alt['err_l']:>5.1f}mm {r_alt['err_r']:>5.1f}mm"
                  f" {r_alt['max_err']:>5.1f}mm {r_alt['clearance']:>5.0f}mm"
                  f" {pair_alt:>7} {r_alt['status']:>8}")

            # Use whichever has lower max error (primary) then better clearance
            if r_alt["max_err"] < r["max_err"]:
                print(f"{'':>4}   → R-guide better (err {r_alt['max_err']:.1f} vs {r['max_err']:.1f}mm)")
                r = r_alt
                desc += " [R-guide better]"
                guide_hand = "R"
            elif r_alt["clearance"] > r["clearance"] and r_alt["max_err"] <= r["max_err"] * 1.1:
                print(f"{'':>4}   → R-guide better clearance"
                      f" ({r_alt['clearance']:.0f}mm vs {r['clearance']:.0f}mm)")
                r = r_alt
                desc += " [R-guide better]"
                guide_hand = "R"
            else:
                print(f"{'':>4}   → L-guide better"
                      f" (err {r['max_err']:.1f}mm, clr {r['clearance']:.0f}mm)")

        results.append({
            "step": step_num, "desc": desc,
            "target_l": list(tgt_l), "target_r": list(tgt_r),
            "action_type": action_type,
            "clip_index": clip_index,
            "guide_hand": guide_hand,
            "err_l_mm": round(r["err_l"], 2),
            "err_r_mm": round(r["err_r"], 2),
            "clearance_mm": round(r["clearance"], 1),
            "pair": list(r["pair"]) if r["pair"] else None,
            "status": r["status"],
        })

        if r["status"] == "PASS":
            n_pass += 1
        elif r["status"] == "WARN":
            n_warn += 1
        else:
            n_fail += 1

        prev_jq = r["jq"].copy()
        prev_targets = cur_targets

    # Summary
    print("\n" + "=" * 90)
    total = n_pass + n_warn + n_fail
    print(f"  SUMMARY: {n_pass} PASS / {n_warn} WARN / {n_fail} FAIL  ({total} steps)")
    if n_fail > 0:
        print("  FAIL steps:")
        for r in results:
            if "FAIL" in r["status"]:
                print(f"    STEP {r['step']}: {r['desc']} — {r['status']}"
                      f" (err={max(r['err_l_mm'], r['err_r_mm']):.1f}mm,"
                      f" clr={r['clearance_mm']:.0f}mm)")
    if n_warn > 0:
        print("  WARN steps (clearance < 10mm):")
        for r in results:
            if r["status"] == "WARN":
                print(f"    STEP {r['step']}: {r['desc']}"
                      f" — clr={r['clearance_mm']:.0f}mm pair=L{r['pair'][0]}-R{r['pair'][1]}")
    print("=" * 90)

    # Save v2 format
    out_dir = os.path.join(os.path.dirname(_SCRIPT_DIR), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "motion_sequence_dry_run.json")
    with open(out_path, "w") as f:
        json.dump({
            "version": 2,
            "layout": {
                "clip_positions": [list(p) for p in CLIP_POSITIONS],
                "groove_angles_rad": [float(thetas[i]) for i in range(len(thetas))],
                "grip_offset_m": GRIP_OFFSET,
                "cable_center": [cable_cx, cable_cy],
                "lift_z": LIFT_Z,
                "grasp_z": GRASP_Z,
            },
            "steps": results,
            "summary": {
                "total": total, "pass": n_pass, "warn": n_warn, "fail": n_fail,
            },
        }, f, indent=2)
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
