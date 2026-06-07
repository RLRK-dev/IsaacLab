#!/usr/bin/env python3
"""M2 MPPI regression test (ctxverify-test).

Validates M2 dual-arm MPPI demo generation pipeline against F.3 v2 criteria.
Standalone script — no pytest dependency.

Tests:
  1. Import smoke (M2 modules, action_dim=6, dual-arm constants)
  2. SSOT alignment (success_threshold, cable segments, EE body offsets)
  3. 1-episode smoke run (dual-arm scene + rollout + HDF5)
  4. F.3 v2 condition 1: MPPI ON success rate >= 80% (AND: both arms)
  5. F.3 v2 condition 2: MPPI OFF success rate = 0%
  6. F.3 v2 condition 3: gap closure >= 100% (both arms independently)

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs \
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/test_mppi_m2_regression.py \
        --device cuda:0
"""

import argparse
import os
import sys
import tempfile
import time


def test_1_import_smoke():
    """Test 1: Import smoke — M2 modules and constants."""
    from mpc_config import MPPIConfig
    from generate_demos_mppi_m2 import (
        sample_action_sequences,
        mppi_weights,
        MppiIKSolver,
        build_mppi_scene,
        compute_cable_endpoint_pos,
        get_ee_positions_dual,
        mppi_generate_demos,
        M2_ACTION_DIM,
        RIGHT_EE_BODY_OFFSET,
    )
    cfg = MPPIConfig()
    assert cfg.K == 256, f"K={cfg.K}, expected 256"
    assert cfg.H == 32, f"H={cfg.H}, expected 32"
    assert M2_ACTION_DIM == 6, f"M2_ACTION_DIM={M2_ACTION_DIM}, expected 6"
    assert RIGHT_EE_BODY_OFFSET == 15, \
        f"RIGHT_EE_BODY_OFFSET={RIGHT_EE_BODY_OFFSET}, expected 15"
    return True


def test_2_ssot_alignment():
    """Test 2: SSOT alignment checks for M2."""
    from mpc_config import MPPIConfig
    from task_config import CABLE_SEGMENTS
    from test_newton_clip_routing import FRANKA_NUM_JOINTS, EE_BODY_OFFSET
    from generate_demos_mppi_m2 import M2_ACTION_DIM, RIGHT_EE_BODY_OFFSET

    cfg = MPPIConfig()

    checks = [
        ("success_threshold_m", cfg.success_threshold_m, 0.08,
         "SSOT: dual_arm_msa_config.py:177"),
        ("pos_action_scale", cfg.pos_action_scale, 0.015,
         "SSOT: newton_approach_cable_env.py:326"),
        ("CABLE_SEGMENTS", CABLE_SEGMENTS, 40,
         "SSOT: task_config.py:70"),
        ("FRANKA_NUM_JOINTS", FRANKA_NUM_JOINTS, 9,
         "SSOT: test_newton_clip_routing.py:85"),
        ("EE_BODY_OFFSET", EE_BODY_OFFSET, 6,
         "SSOT: test_newton_clip_routing.py:86"),
        ("RIGHT_EE_BODY_OFFSET", RIGHT_EE_BODY_OFFSET,
         FRANKA_NUM_JOINTS + EE_BODY_OFFSET,
         "Derived: FRANKA_NUM_JOINTS + EE_BODY_OFFSET = 15"),
        ("M2_ACTION_DIM", M2_ACTION_DIM, 6,
         "DEFINE I1: left pos 3D + right pos 3D"),
    ]

    all_ok = True
    for name, actual, expected, source in checks:
        if isinstance(actual, float):
            ok = abs(actual - expected) < 1e-9
        else:
            ok = actual == expected
        if not ok:
            print(f"  FAIL: {name} = {actual}, expected {expected} ({source})")
            all_ok = False
        else:
            print(f"  OK: {name} = {actual} ({source})")

    return all_ok


def test_3_smoke_1ep(device):
    """Test 3: 1-episode smoke run (32 steps for speed)."""
    from mpc_config import MPPIConfig
    from generate_demos_mppi_m2 import mppi_generate_demos, M2_ACTION_DIM

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.action_dim = M2_ACTION_DIM
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
        assert len(d["dist_left"]) > 0, "Empty left distance trajectory"
        assert len(d["dist_right"]) > 0, "Empty right distance trajectory"
        assert len(d["left_ee_pos"]) == len(d["actions"]), \
            f"left_ee_pos/actions length mismatch"
        assert len(d["right_ee_pos"]) == len(d["actions"]), \
            f"right_ee_pos/actions length mismatch"
        assert d["actions"].shape[1] == M2_ACTION_DIM, \
            f"action_dim={d['actions'].shape[1]}, expected {M2_ACTION_DIM}"
        assert os.path.exists(csv_path), "Diagnostic CSV not written"
        print(f"  1 episode: {d['steps']} steps, "
              f"final_dist_L={d['dist_left'][-1]:.4f}m, "
              f"final_dist_R={d['dist_right'][-1]:.4f}m, "
              f"success={d['success']}")

    return True


def test_456_f3v2(device):
    """Tests 4-6: F.3 v2 full evaluation (5 episodes ON + 5 OFF, dual-arm)."""
    from mpc_config import MPPIConfig
    from generate_demos_mppi_m2 import mppi_generate_demos, M2_ACTION_DIM
    import numpy as np

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.action_dim = M2_ACTION_DIM
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

        threshold = cfg.success_threshold_m
        n_success_on = sum(1 for d in demos_on if d["success"])
        dists_l_on = [d["dist_left"][-1] for d in demos_on]
        dists_r_on = [d["dist_right"][-1] for d in demos_on]
        mean_dist_l_on = float(np.mean(dists_l_on))
        mean_dist_r_on = float(np.mean(dists_r_on))

        print(f"\n  ON results: {n_success_on}/5 success")
        print(f"    dist_L={[round(d, 4) for d in dists_l_on]}")
        print(f"    dist_R={[round(d, 4) for d in dists_r_on]}")

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
        dists_l_off = [d["dist_left"][-1] for d in demos_off]
        dists_r_off = [d["dist_right"][-1] for d in demos_off]
        mean_dist_l_off = float(np.mean(dists_l_off))
        mean_dist_r_off = float(np.mean(dists_r_off))

        print(f"\n  OFF results: {n_success_off}/5 success")
        print(f"    dist_L={[round(d, 4) for d in dists_l_off]}")
        print(f"    dist_R={[round(d, 4) for d in dists_r_off]}")

    print("\n  === F.3 v2 Evaluation (M2 dual-arm) ===")
    results = {}

    # Condition 1: MPPI ON success >= 80% (AND condition)
    c1_pass = n_success_on >= 4
    results["c1"] = c1_pass
    print(f"  Cond 1 (ON success >= 80%): {n_success_on}/5 = "
          f"{n_success_on/5*100:.0f}% {'PASS' if c1_pass else 'FAIL'}")

    # Condition 2: MPPI OFF success = 0%
    c2_pass = n_success_off == 0
    results["c2"] = c2_pass
    print(f"  Cond 2 (OFF success = 0%):  {n_success_off}/5 = "
          f"{n_success_off/5*100:.0f}% {'PASS' if c2_pass else 'FAIL'}")

    # Condition 3: gap closure >= 100% (both arms independently)
    gap_l_needed = mean_dist_l_off - threshold
    gap_r_needed = mean_dist_r_off - threshold
    gap_l_closed = mean_dist_l_off - mean_dist_l_on
    gap_r_closed = mean_dist_r_off - mean_dist_r_on

    gap_closure_l = gap_l_closed / gap_l_needed if gap_l_needed > 0 else 0.0
    gap_closure_r = gap_r_closed / gap_r_needed if gap_r_needed > 0 else 0.0
    c3_pass = gap_closure_l >= 1.0 and gap_closure_r >= 1.0
    results["c3"] = c3_pass
    print(f"  Cond 3 (gap closure >= 100%):")
    print(f"    LEFT:  ({mean_dist_l_off:.4f} - {mean_dist_l_on:.4f}) / "
          f"({mean_dist_l_off:.4f} - {threshold}) = {gap_closure_l*100:.1f}% "
          f"{'PASS' if gap_closure_l >= 1.0 else 'FAIL'}")
    print(f"    RIGHT: ({mean_dist_r_off:.4f} - {mean_dist_r_on:.4f}) / "
          f"({mean_dist_r_off:.4f} - {threshold}) = {gap_closure_r*100:.1f}% "
          f"{'PASS' if gap_closure_r >= 1.0 else 'FAIL'}")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser(description="M2 MPPI regression test")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--skip-full", action="store_true",
                        help="Skip full F.3 v2 test (tests 4-6)")
    args = parser.parse_args()

    print("=" * 60)
    print("  M2 MPPI Regression Test (ctxverify-test)")
    print("=" * 60)

    results = {}
    t_start = time.perf_counter()

    print("\n[Test 1] Import smoke...")
    try:
        results["t1"] = test_1_import_smoke()
        print("  PASS")
    except Exception as e:
        print(f"  FAIL: {e}")
        results["t1"] = False

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

    print("\n[Test 3] 1-episode smoke run (dual-arm)...")
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

    print("\n[Tests 4-6] F.3 v2 full evaluation (dual-arm)...")
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
