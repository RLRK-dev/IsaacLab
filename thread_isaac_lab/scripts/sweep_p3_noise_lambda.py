# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""T-IC-Phase-A-P3 Phase 1: noise_sigma × temperature_lambda 9-cell MPPI sweep.

State.md grid {0.1, 0.2, 0.3} × {0.3, 0.5, 1.0}. CC#3 Option D: env / cost
field / warm_start UNCHANGED; sweep targets MPPIConfig base fields only.
"""

import argparse
import csv
import json
import math
import os
import sys
import time

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import numpy as np
import warp as wp

from thread_isaac_lab.configs.mpc_config_ic import get_default_mppi_ic_config
from generate_demos_mppi_m3_insert_clip import (
    INSERT_TERMINAL_STEPS,
    mppi_generate_demos_ic,
    save_demos_hdf5_ic,
    save_run_metrics_ic,
)

NAN_CASCADE_LIMIT = 2  # Rs directive 2026-05-03 abort criterion (≥2 ep)


def _persist(path: str, payload: dict) -> None:
    """Atomic JSON write (tempfile + replace)."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="T-IC-Phase-A-P3 Phase 1 sweep")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--world-count", type=int, default=128, help="K_MPPI per cell")
    parser.add_argument("--n-demos", type=int, default=5, help="Episodes per cell")
    parser.add_argument("--seed", type=int, default=42, help="Same seed for all cells")
    parser.add_argument("--sigmas", type=str, default="0.1,0.2,0.3", help="state.md grid")
    parser.add_argument("--lambdas", type=str, default="0.3,0.5,1.0", help="state.md grid")
    parser.add_argument("--output-dir", type=str, default="data/sweep_p3_noise_lambda")
    parser.add_argument("--pos-action-scale", type=float, default=0.020, help="IC-CRIT-1 default")
    args = parser.parse_args()

    sigmas = [float(x) for x in args.sigmas.split(",")]
    lambdas = [float(x) for x in args.lambdas.split(",")]
    cells = [(s, lam) for s in sigmas for lam in lambdas]
    n_cells = len(cells)

    os.makedirs(args.output_dir, exist_ok=True)
    summary_path = os.path.join(args.output_dir, "sweep_summary.json")

    wp.init()
    wp.set_device(args.device)

    print(f"\n{'=' * 78}\n  T-IC-Phase-A-P3 Phase 1 — {n_cells} cells")
    print(f"  sigmas={sigmas}  lambdas={lambdas}  K={args.world_count}  n_demos={args.n_demos}")
    print(f"  seed={args.seed}  pos_action_scale={args.pos_action_scale}")
    print(f"  output_dir={args.output_dir}  device={args.device}\n{'=' * 78}\n", flush=True)

    sweep_results: list[dict] = []
    abort_reason: str | None = None

    for cell_idx, (sigma, lam) in enumerate(cells):
        cell_id = f"sigma{sigma:.2f}_lam{lam:.2f}"
        print(f"\n{'#' * 78}\n  Cell {cell_idx + 1}/{n_cells}: {cell_id}\n{'#' * 78}\n", flush=True)

        # Factory + override (preserves SSOT). CC#3 Option D: cable_seg_cost_scale,
        # seg_ori_scale, warm_start_offset_m left at factory defaults (UNCHANGED).
        cfg = get_default_mppi_ic_config()
        cfg.noise_sigma = sigma
        cfg.temperature_lambda = lam
        cfg.K = args.world_count
        cfg.device = args.device
        cfg.pos_action_scale = args.pos_action_scale

        print(f"[CFG] sigma={cfg.noise_sigma}  lam={cfg.temperature_lambda}  K={cfg.K}  "
              f"pos={cfg.pos_action_scale}  cable_seg={cfg.cable_seg_cost_scale}  "
              f"seg_ori={cfg.seg_ori_scale}  warm_start={cfg.warm_start_offset_m}", flush=True)

        diag_csv = os.path.join(args.output_dir, f"diag_{cell_id}.csv")
        h5_path = os.path.join(args.output_dir, f"demos_{cell_id}.hdf5")
        cell_metrics_dir = os.path.join(args.output_dir, f"metrics_{cell_id}")

        t0 = time.perf_counter()
        try:
            demos, drifts, drifts_per_ep_max, cable_L_list, cable_R_list = mppi_generate_demos_ic(
                cfg, args.device, max_steps=INSERT_TERMINAL_STEPS, n_demos=args.n_demos,
                seed=args.seed, mode="approach", diag_csv_path=diag_csv,
            )
        except Exception as exc:
            abort_reason = f"Cell {cell_id} exception: {exc!r}"
            print(f"[ABORT] {abort_reason}", flush=True)
            break
        elapsed = time.perf_counter() - t0

        cable_L_mean = np.mean(cable_L_list, axis=0).astype(np.float32) if cable_L_list else None
        cable_R_mean = np.mean(cable_R_list, axis=0).astype(np.float32) if cable_R_list else None
        save_demos_hdf5_ic(demos, cfg, h5_path, "on", "approach",
                           cable_L_endpoint_mean=cable_L_mean, cable_R_endpoint_mean=cable_R_mean)
        metrics = save_run_metrics_ic(demos, drifts, drifts_per_ep_max, elapsed, cfg,
                                      cell_metrics_dir, "approach")

        n_success = sum(1 for d in demos if d["success"])
        cell_result = {
            "cell_idx": cell_idx, "cell_id": cell_id,
            "noise_sigma": sigma, "temperature_lambda": lam,
            "n_demos": len(demos), "n_success": n_success,
            "S1_pos": metrics["S1_pos_success_rate"],
            "S2_ori": metrics["S2_ori_success_rate"],
            "S3_combined": metrics["S3_combined_rate"],
            "drift_max_L_deg": math.degrees(metrics["tangent_drift"]["left"].get("max", 0.0)),
            "drift_max_R_deg": math.degrees(metrics["tangent_drift"]["right"].get("max", 0.0)),
            "drift_violation_rate": metrics["drift_violation"]["violation_rate"],
            "wall_clock_s": round(elapsed, 1),
            "h5_path": h5_path, "diag_csv": diag_csv, "metrics_dir": cell_metrics_dir,
        }
        sweep_results.append(cell_result)
        print(f"\n[CELL {cell_id}] S1={cell_result['S1_pos']:.1%}  S2={cell_result['S2_ori']:.1%}  "
              f"S3={cell_result['S3_combined']:.1%}  succ={n_success}/{len(demos)}  "
              f"t={elapsed:.1f}s", flush=True)

        # Persist intermediate (kill-safe artifact).
        _persist(summary_path, {
            "task": "T-IC-Phase-A-P3 Phase 1",
            "spec": {"sigmas": sigmas, "lambdas": lambdas, "world_count": args.world_count,
                     "n_demos": args.n_demos, "seed": args.seed,
                     "pos_action_scale": args.pos_action_scale,
                     "max_steps": INSERT_TERMINAL_STEPS, "mode": "approach"},
            "abort_reason": abort_reason,
            "n_cells_completed": len(sweep_results), "results": sweep_results,
        })

        # NaN cascade abort (Rs directive 2026-05-03 NAN_CASCADE_LIMIT=2).
        nan_count = 0
        for d in demos:
            for k in ("max_seg_dist_groove", "max_pos_L", "max_pos_R", "max_m3_ori_L", "max_m3_ori_R"):
                v = d.get(k)
                if v is not None and isinstance(v, float) and math.isnan(v):
                    nan_count += 1
                    break
        if nan_count >= NAN_CASCADE_LIMIT:
            abort_reason = f"NaN cascade ≥{NAN_CASCADE_LIMIT} at cell {cell_id} (count={nan_count})"
            print(f"[ABORT] {abort_reason}", flush=True)
            break

    # Final persist + table.
    _persist(summary_path, {
        "task": "T-IC-Phase-A-P3 Phase 1",
        "spec": {"sigmas": sigmas, "lambdas": lambdas, "world_count": args.world_count,
                 "n_demos": args.n_demos, "seed": args.seed,
                 "pos_action_scale": args.pos_action_scale,
                 "max_steps": INSERT_TERMINAL_STEPS, "mode": "approach"},
        "abort_reason": abort_reason,
        "n_cells_completed": len(sweep_results), "results": sweep_results,
    })

    print(f"\n{'=' * 78}\n  RESULTS ({len(sweep_results)}/{n_cells} cells)\n{'=' * 78}")
    print(f"  {'sigma':>5} {'lam':>5} {'n_d':>4} {'succ':>4} {'S1':>6} {'S2':>6} {'S3':>6} "
          f"{'dL°':>5} {'dR°':>5} {'t_s':>7}")
    for r in sweep_results:
        print(f"  {r['noise_sigma']:>5.2f} {r['temperature_lambda']:>5.2f} "
              f"{r['n_demos']:>4d} {r['n_success']:>4d} "
              f"{r['S1_pos']:>5.1%} {r['S2_ori']:>5.1%} {r['S3_combined']:>5.1%} "
              f"{r['drift_max_L_deg']:>5.1f} {r['drift_max_R_deg']:>5.1f} {r['wall_clock_s']:>7.1f}")

    if sweep_results:
        sweep_csv = os.path.join(args.output_dir, "sweep_results.csv")
        with open(sweep_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sweep_results[0].keys()))
            w.writeheader()
            w.writerows(sweep_results)
        print(f"\n[CSV] {sweep_csv}", flush=True)

    if abort_reason:
        sys.exit(2)
    if not sweep_results:
        print("\n[ERROR] No cells completed.", flush=True)
        sys.exit(1)

    best = max(sweep_results, key=lambda r: r["S3_combined"])
    print(f"\n[BEST CELL] {best['cell_id']}  S3={best['S3_combined']:.1%}  "
          f"S1={best['S1_pos']:.1%}  S2={best['S2_ori']:.1%}", flush=True)
    print("  → Phase 2 trigger: replicate × 5 seeds × full retrain+eval (state.md §5 PASS).")


if __name__ == "__main__":
    main()
