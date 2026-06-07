"""Newton 20-Clip IK Reachability Test

Generates a randomized 20-clip layout with varied positions and groove
orientations, then tests:
  1. Dual-arm IK reachability for each clip
  2. Cable bend feasibility between consecutive clips (min bend radius)

No cable, no physics — pure FK model + IK solve.

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_20clip_reachability.py
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_20clip_reachability.py --seed 99
"""

import argparse
import json
import math
import os
import time

import numpy as np
import newton

from newton_routing_utils import (
    # Constants
    FRANKA_NUM_JOINTS, EE_BODY_OFFSET, GRIP_OFFSET,
    WS_X_MIN, WS_X_MAX, WS_Y_MIN, WS_Y_MAX,
    R_MIN_BEND, CABLE_DIAMETER, MAX_GROOVE_DEVIATION_DEG,
    # Functions
    build_fk_model, init_fk_state,
    solve_ik_dual, eval_ik_errors,
    generate_positions, compute_route_order, assign_groove_angles,
    analyze_bends, cable_path_length,
    NumpyEncoder,
)
from task_config import TABLE_HEIGHT, EE_TO_FINGERTIP  # noqa: E402 (already on sys.path via utils)

# ---------------------------------------------------------------------------
# Script-specific constants
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:1")
IK_ITERATIONS = 150      # More iterations for reachability test (vs 100 for routing)
IK_STEP_SIZE = 1.0
IK_ERR_THRESHOLD_MM = 8.0   # max position error per arm
GRASP_Z = TABLE_HEIGHT + EE_TO_FINGERTIP


# ---------------------------------------------------------------------------
# Reachability test
# ---------------------------------------------------------------------------
def test_clip(fk_model, fk_state, cx, cy, theta, home_jq):
    """Test reachability for one clip. Tries both L/R assignments."""
    dx = GRIP_OFFSET * math.cos(theta)
    dy = GRIP_OFFSET * math.sin(theta)

    configs = [
        ("A", (cx - dx, cy - dy, GRASP_Z), (cx + dx, cy + dy, GRASP_Z)),
        ("B", (cx + dx, cy + dy, GRASP_Z), (cx - dx, cy - dy, GRASP_Z)),
    ]
    best = None
    for label, left, right in configs:
        fk_state.joint_q.assign(home_jq)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        jq, cost = solve_ik_dual(fk_model, fk_state, left, right, DEVICE,
                                 iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
        el, er = eval_ik_errors(fk_model, fk_state, jq, left, right)
        me = max(el, er)
        if best is None or me < best["max_err"]:
            best = dict(config=label, cost=cost, err_l=el, err_r=er, max_err=me,
                        grip_l=left[:2], grip_r=right[:2])
    best["reachable"] = best["max_err"] < IK_ERR_THRESHOLD_MM
    return best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-clips", type=int, default=20)
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    print(f"[20CLIP-IK] Device={DEVICE}, seed={args.seed}")
    print(f"[20CLIP-IK] Workspace X=[{WS_X_MIN},{WS_X_MAX}] Y=[{WS_Y_MIN},{WS_Y_MAX}]")
    print(f"[20CLIP-IK] GRASP_Z={GRASP_Z:.3f}, GRIP_OFFSET={GRIP_OFFSET*1000:.0f}mm")
    print(f"[20CLIP-IK] R_MIN_BEND={R_MIN_BEND*1000:.0f}mm, "
          f"MAX_GROOVE_DEV={MAX_GROOVE_DEVIATION_DEG:.0f}°")
    print()

    # FK model
    print("[BUILD] FK model...")
    fk_model = build_fk_model(DEVICE)
    fk_state = init_fk_state(fk_model, finger_open=False)
    home_jq = fk_state.joint_q.numpy().copy()
    print(f"  bodies={fk_model.body_count}, joints={fk_model.joint_count}")

    # --- Layout generation ---
    print(f"\n[LAYOUT] Generating {args.n_clips} clips (seed={args.seed})...")
    positions = generate_positions(args.n_clips, args.seed)
    route = compute_route_order(positions)
    thetas = assign_groove_angles(positions, route, args.seed)
    clips = [(positions[i][0], positions[i][1], thetas[i]) for i in range(len(positions))]
    path_len = cable_path_length(positions, route)
    print(f"  {len(clips)} clips, cable path = {path_len*1000:.0f}mm")

    # --- Bend analysis ---
    print(f"\n[BEND] Cable bend feasibility (R_min={R_MIN_BEND*1000:.0f}mm)...")
    segments = analyze_bends(positions, thetas, route)
    bend_pass = sum(1 for s in segments if s["feasible"])
    bend_fail = len(segments) - bend_pass

    print(f"  {'Seg':>3} {'From':>4}{'->':>2}{'To':>3} {'Dist':>6} "
          f"{'Exit°':>5} {'Entr°':>5} {'Tot°':>5} {'Arc':>6} {'':>4}")
    print(f"  {'—'*3} {'—'*4}{'  ':>2}{'—'*3} {'—'*6} "
          f"{'—'*5} {'—'*5} {'—'*5} {'—'*6} {'—'*4}")
    for j, s in enumerate(segments):
        tag = "OK" if s["feasible"] else "NG"
        print(f"  {j:3d}  C{s['from']:02d}->C{s['to']:02d} "
              f"{s['dist_mm']:5.0f}  {s['exit_bend_deg']:5.1f} "
              f"{s['entry_bend_deg']:5.1f} {s['total_bend_deg']:5.1f} "
              f"{s['arc_needed_mm']:5.0f}  {tag:>4}")
    print(f"  Bend: {bend_pass}/{len(segments)} segments feasible")

    # --- IK test ---
    print(f"\n[IK] Testing {len(clips)} clips...")
    hdr = (f"  {'#':>2} {'X':>6} {'Y':>7} {'theta':>5} {'Cfg':>3} "
           f"{'ErrL':>6} {'ErrR':>6} {'Max':>6} {'Cost':>9} {'':>4}")
    print(hdr)
    print(f"  {'—'*2} {'—'*6} {'—'*7} {'—'*5} {'—'*3} "
          f"{'—'*6} {'—'*6} {'—'*6} {'—'*9} {'—'*4}")

    results = []
    t0 = time.time()
    for i, (cx, cy, th) in enumerate(clips):
        r = test_clip(fk_model, fk_state, cx, cy, th, home_jq)
        r["id"] = i
        r["x"] = round(cx, 4)
        r["y"] = round(cy, 4)
        r["theta_deg"] = round(math.degrees(th), 1)
        results.append(r)
        tag = "OK" if r["reachable"] else "NG"
        print(f"  {i:2d} {cx:6.3f} {cy:7.3f} {r['theta_deg']:5.1f} "
              f"  {r['config']} {r['err_l']:6.1f} {r['err_r']:6.1f} {r['max_err']:6.1f} "
              f"{r['cost']:9.5f} {tag:>4}")
    elapsed = time.time() - t0

    ik_pass = sum(1 for r in results if r["reachable"])
    ik_fail = len(results) - ik_pass

    # --- Summary ---
    print(f"\n{'='*65}")
    print(f"  IK reachability : {ik_pass}/{len(clips)} clips")
    print(f"  Bend feasibility: {bend_pass}/{len(segments)} segments")
    all_ok = ik_fail == 0 and bend_fail == 0
    print(f"  OVERALL         : {'PASS' if all_ok else 'FAIL'}  ({elapsed:.1f}s)")
    print(f"{'='*65}")

    if ik_fail > 0:
        print(f"\n  IK NG clips:")
        for r in results:
            if not r["reachable"]:
                print(f"    C{r['id']:02d} ({r['x']:.3f}, {r['y']:.3f}) "
                      f"theta={r['theta_deg']:.0f} max_err={r['max_err']:.1f}mm")

    if bend_fail > 0:
        print(f"\n  Bend NG segments:")
        for s in segments:
            if not s["feasible"]:
                print(f"    C{s['from']:02d}->C{s['to']:02d}: dist={s['dist_mm']:.0f}mm "
                      f"total_bend={s['total_bend_deg']:.0f} "
                      f"arc={s['arc_needed_mm']:.0f}mm")

    # Route visualization
    print(f"\n  Cable route (nearest-neighbor):")
    for j, idx in enumerate(route):
        cx, cy = positions[idx]
        th = thetas[idx]
        ik_ok = results[idx]["reachable"]
        if j < len(route) - 1:
            ni = route[j + 1]
            s = segments[j]
            d = s["dist_mm"]
            bend_ok = s["feasible"]
            ik_m = "+" if ik_ok else "X"
            bend_m = "" if bend_ok else " [BEND-NG]"
            print(f"    {ik_m} C{idx:02d} ({cx:.3f},{cy:+.3f}) "
                  f"theta={math.degrees(th):+4.0f}"
                  f"  —{d:4.0f}mm{bend_m}->  C{ni:02d}")
        else:
            ik_m = "+" if ik_ok else "X"
            print(f"    {ik_m} C{idx:02d} ({cx:.3f},{cy:+.3f}) "
                  f"theta={math.degrees(th):+4.0f}")

    cable_with_slack = path_len * 1.2
    seg_15 = int(cable_with_slack / 0.015)
    seg_20 = int(cable_with_slack / 0.020)
    print(f"    Path: {path_len*1000:.0f}mm (+20% slack = {cable_with_slack*1000:.0f}mm)")
    print(f"    Segments: ~{seg_20} @20mm, ~{seg_15} @15mm")

    # --- Save ---
    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/newton_20clip_ik_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    out = {
        "test": "newton_20clip_ik_reachability",
        "device": DEVICE,
        "seed": args.seed,
        "overall": "PASS" if all_ok else "FAIL",
        "ik_pass": f"{ik_pass}/{len(clips)}",
        "bend_pass": f"{bend_pass}/{len(segments)}",
        "elapsed_s": round(elapsed, 1),
        "params": {
            "workspace_x": [WS_X_MIN, WS_X_MAX],
            "workspace_y": [WS_Y_MIN, WS_Y_MAX],
            "grasp_z": GRASP_Z,
            "grip_offset_mm": GRIP_OFFSET * 1000,
            "ik_threshold_mm": IK_ERR_THRESHOLD_MM,
            "r_min_bend_mm": R_MIN_BEND * 1000,
            "max_groove_deviation_deg": MAX_GROOVE_DEVIATION_DEG,
            "cable_diameter_mm": CABLE_DIAMETER * 1000,
        },
        "clips": [
            {"id": i, "x": round(positions[i][0], 4),
             "y": round(positions[i][1], 4),
             "theta_deg": round(math.degrees(thetas[i]), 1)}
            for i in range(len(positions))
        ],
        "route_order": route,
        "cable_path_mm": round(path_len * 1000, 1),
        "ik_results": [
            {k: v for k, v in r.items() if k not in ("grip_l", "grip_r")}
            for r in results
        ],
        "bend_results": segments,
    }
    mp = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(mp, "w") as f:
        json.dump(out, f, indent=2, cls=NumpyEncoder)
    print(f"\n  Metrics: {mp}")


if __name__ == "__main__":
    main()
