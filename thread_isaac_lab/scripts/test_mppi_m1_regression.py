#!/usr/bin/env python3
"""M1 MPPI regression test (ctxverify-test).

Validates M1 MPPI demo generation pipeline against F.3 v2 criteria.
Standalone script — no pytest dependency.

Tests:
  1. Import smoke (MPPIConfig, generate_demos_mppi modules)
  2. MPPIConfig SSOT alignment (success_threshold, pos/rot scale, newton_dt, substeps)
  3. 1-episode smoke run (scene build + rollout + HDF5 output)
  4. F.3 v2 condition 1: MPPI ON success rate = 5/5
  5. F.3 v2 condition 2: MPPI OFF success rate = 0/5
  6. F.3 v2 condition 3: gap closure >= 100%

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs \
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/test_mppi_m1_regression.py \
        --device cuda:0
"""

import argparse
import os
import sys
import tempfile
import time


def test_1_import_smoke():
    """Test 1: Import smoke."""
    from mpc_config import MPPIConfig
    from generate_demos_mppi import (
        sample_action_sequences,
        mppi_weights,
        mppi_generate_demos,
    )
    cfg = MPPIConfig()
    assert cfg.K == 256, f"K={cfg.K}, expected 256"
    assert cfg.H == 32, f"H={cfg.H}, expected 32"
    return True


def test_2_ssot_alignment():
    """Test 2: MPPIConfig defaults match env SSOT values."""
    from mpc_config import MPPIConfig
    cfg = MPPIConfig()

    checks = [
        ("success_threshold_m", cfg.success_threshold_m, 0.08,
         "SSOT: dual_arm_msa_config.py:177"),
        ("pos_action_scale", cfg.pos_action_scale, 0.015,
         "SSOT: newton_approach_cable_env.py:326"),
        ("rot_action_scale", cfg.rot_action_scale, 0.05,
         "SSOT: newton_approach_cable_env.py:327"),
        ("newton_dt", cfg.newton_dt, 1.0 / 480.0,
         "SSOT: newton_approach_cable_env.py:67"),
        ("sim_substeps", cfg.sim_substeps, 4,
         "SSOT: newton_approach_cable_env.py:68"),
    ]

    all_ok = True
    for name, actual, expected, source in checks:
        if abs(actual - expected) > 1e-9:
            print(f"  FAIL: {name} = {actual}, expected {expected} ({source})")
            all_ok = False
        else:
            print(f"  OK: {name} = {actual} ({source})")

    return all_ok


def test_3_smoke_1ep(device):
    """Test 3: 1-episode smoke run (short horizon for speed)."""
    from mpc_config import MPPIConfig
    from generate_demos_mppi import mppi_generate_demos

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.device = device

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "smoke.csv")
        demos = mppi_generate_demos(
            cfg, device,
            max_steps=32,
            n_demos=1,
            seed=42,
            diag_csv_path=csv_path,
        )

        assert len(demos) == 1, f"Expected 1 demo, got {len(demos)}"
        d = demos[0]
        assert len(d["distance"]) > 0, "Empty distance trajectory"
        assert len(d["ee_pos"]) == len(d["actions"]), \
            f"ee_pos/actions length mismatch: {len(d['ee_pos'])} vs {len(d['actions'])}"
        assert os.path.exists(csv_path), "Diagnostic CSV not written"
        print(f"  1 episode: {d['steps']} steps, final_dist={d['distance'][-1]:.4f}m, "
              f"success={d['success']}")

    return True


def test_456_f3v2(device):
    """Tests 4-6: F.3 v2 full evaluation (5 episodes ON + 5 OFF)."""
    from mpc_config import MPPIConfig
    from generate_demos_mppi import mppi_generate_demos
    import numpy as np

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.device = device

    with tempfile.TemporaryDirectory() as tmpdir:
        # MPPI ON
        print("\n  --- MPPI ON (lambda=0.3, 5 episodes) ---")
        csv_on = os.path.join(tmpdir, "on.csv")
        demos_on = mppi_generate_demos(
            cfg, device,
            max_steps=128,
            n_demos=5,
            seed=42,
            diag_csv_path=csv_on,
        )

        n_success_on = sum(1 for d in demos_on if d["success"])
        dists_on = [d["distance"][-1] for d in demos_on]
        mean_dist_on = float(np.mean(dists_on))

        print(f"\n  ON results: {n_success_on}/5 success, "
              f"mean_dist={mean_dist_on:.4f}m, "
              f"dists={[round(d, 4) for d in dists_on]}")

        # MPPI OFF (baseline)
        print("\n  --- MPPI OFF (baseline, 5 episodes) ---")
        csv_off = os.path.join(tmpdir, "off.csv")
        demos_off = mppi_generate_demos(
            cfg, device,
            max_steps=128,
            n_demos=5,
            seed=42,
            no_mppi=True,
            diag_csv_path=csv_off,
        )

        n_success_off = sum(1 for d in demos_off if d["success"])
        dists_off = [d["distance"][-1] for d in demos_off]
        mean_dist_off = float(np.mean(dists_off))

        print(f"\n  OFF results: {n_success_off}/5 success, "
              f"mean_dist={mean_dist_off:.4f}m")

    # F.3 v2 evaluation
    print("\n  === F.3 v2 Evaluation ===")
    results = {}

    # Condition 1: MPPI ON success >= 80%
    c1_pass = n_success_on == 5
    results["c1"] = c1_pass
    print(f"  Cond 1 (ON success >= 80%): {n_success_on}/5 = "
          f"{n_success_on/5*100:.0f}% {'PASS' if c1_pass else 'FAIL'}")

    # Condition 2: MPPI OFF success = 0%
    c2_pass = n_success_off == 0
    results["c2"] = c2_pass
    print(f"  Cond 2 (OFF success = 0%):  {n_success_off}/5 = "
          f"{n_success_off/5*100:.0f}% {'PASS' if c2_pass else 'FAIL'}")

    # Condition 3: gap closure >= 100%
    gap_needed = mean_dist_off - cfg.success_threshold_m
    gap_closed = mean_dist_off - mean_dist_on
    if gap_needed > 0:
        gap_closure = gap_closed / gap_needed
    else:
        gap_closure = 0.0
    c3_pass = gap_closure >= 1.0
    results["c3"] = c3_pass
    print(f"  Cond 3 (gap closure >= 100%): "
          f"({mean_dist_off:.4f} - {mean_dist_on:.4f}) / "
          f"({mean_dist_off:.4f} - {cfg.success_threshold_m}) = "
          f"{gap_closure*100:.1f}% {'PASS' if c3_pass else 'FAIL'}")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser(description="M1 MPPI regression test")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--skip-full", action="store_true",
                        help="Skip full F.3 v2 test (tests 4-6), run smoke only")
    args = parser.parse_args()

    print("=" * 60)
    print("  M1 MPPI Regression Test (ctxverify-test)")
    print("=" * 60)

    results = {}
    t_start = time.perf_counter()

    # Test 1: Import smoke
    print("\n[Test 1] Import smoke...")
    try:
        results["t1"] = test_1_import_smoke()
        print("  PASS")
    except Exception as e:
        print(f"  FAIL: {e}")
        results["t1"] = False

    # Test 2: SSOT alignment
    print("\n[Test 2] SSOT alignment...")
    try:
        results["t2"] = test_2_ssot_alignment()
        print(f"  {'PASS' if results['t2'] else 'FAIL'}")
    except Exception as e:
        print(f"  FAIL: {e}")
        results["t2"] = False

    if not results.get("t1") or not results.get("t2"):
        print("\n[ABORT] Tests 1-2 failed, skipping GPU tests.")
        _print_summary(results, t_start)
        sys.exit(1)

    # Test 3: 1-episode smoke
    print("\n[Test 3] 1-episode smoke run...")
    import warp as wp
    wp.init()
    wp.set_device(args.device)

    try:
        results["t3"] = test_3_smoke_1ep(args.device)
        print(f"  {'PASS' if results['t3'] else 'FAIL'}")
    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        results["t3"] = False

    if not results.get("t3"):
        print("\n[ABORT] Test 3 failed, skipping F.3 v2 tests.")
        _print_summary(results, t_start)
        sys.exit(1)

    if args.skip_full:
        print("\n[SKIP] Tests 4-6 (--skip-full)")
        _print_summary(results, t_start)
        sys.exit(0 if all(results.values()) else 1)

    # Tests 4-6: F.3 v2
    print("\n[Tests 4-6] F.3 v2 full evaluation...")
    try:
        results["t456"] = test_456_f3v2(args.device)
        print(f"\n  {'PASS' if results['t456'] else 'FAIL'}")
    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        results["t456"] = False

    _print_summary(results, t_start)
    sys.exit(0 if all(results.values()) else 1)


def _print_summary(results, t_start):
    elapsed = time.perf_counter() - t_start
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    n_pass = sum(1 for v in results.values() if v)
    n_total = len(results)
    verdict = "ALL PASS" if n_pass == n_total else f"{n_total - n_pass} FAIL"
    print(f"\n  {verdict} ({n_pass}/{n_total}) in {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
