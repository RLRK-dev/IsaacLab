#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""M3 MPPI regression test (ctxverify-test M3).

Validates M3 dual-arm 12D full-pose MPPI demo generation pipeline against
F.3 v2 extended criteria (S1-S8 + determinism) per DEFINE v6.3.2 + plan v2.2.

Tests:
  1. Import smoke (M3 modules, action_dim=12, 3 quat constants, MppiIKSolverM3)
  2. SSOT alignment (success_threshold_m/rad, cost_scale runtime, T_ALIGN)
  3. 1-episode smoke run (12D action, quat unit-norm, dist_pos/ori trajectories)
  4. F.3 v2 S3 combined success rate >= 60% (calibration gate per DEFINE v6.2 N1)
  5. F.3 v2 S4 MPPI OFF = 0% baseline
  6. Gap closure: S5 (pos) >= 100% both arms; S6 (ori) report
  7. Cable L/R endpoint geometric consistency (mean symmetry, Y-axis reflection)
  8. Bit-exact determinism (two runs same seed → np.array_equal across key arrays)

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs:thread_isaac_lab/envs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/test_mppi_m3_regression.py \\
        --device cuda:0

References:
    DEFINE: memory/project_mppi_m3_define.md (v6.3.2)
    Plan:   memory/project_mppi_m3_plan_v2_2.md (v2.2)
"""

import argparse
import os
import sys
import tempfile
import time

# =============================================================================
# Test 1 — Import smoke (M3 modules + constants + MppiIKSolverM3 class)
# =============================================================================


def test_1_import_smoke():
    """Test 1: M3 module import + action_dim=12 + class presence."""
    from generate_demos_mppi_m3 import (
        DRIFT_THRESHOLD_RAD,
        DRIFT_VIOLATION_RATE_LIMIT,
        M3_ACTION_DIM,
        M3_ACTION_LAYOUT,
        M3_COST_METHOD,
        M3_COST_SCALE,
        M3_QUAT_CONVENTION,
        M3_QUAT_FRAME,
        M3_QUAT_SEMANTIC,
        M3_VERSION,
        MppiIKSolverM3,
        compute_cost_targets_from_cable,
        get_ee_poses_dual,
        mppi_generate_demos_m3,
        rollout_and_cost_m3,
        save_demos_hdf5_m3,
        save_run_metrics_json,
        slerp_numpy,
        warm_start_approach_m3,
    )
    from mpc_config import MPPIConfig

    cfg = MPPIConfig()
    assert M3_ACTION_DIM == 12, f"M3_ACTION_DIM={M3_ACTION_DIM}, expected 12"
    assert M3_ACTION_LAYOUT == "L-first", f"layout={M3_ACTION_LAYOUT}"
    assert M3_COST_METHOD == "C", f"method={M3_COST_METHOD}"
    assert M3_QUAT_CONVENTION == "xyzw", f"quat={M3_QUAT_CONVENTION}"
    assert M3_QUAT_FRAME == "world", f"frame={M3_QUAT_FRAME}"
    assert M3_QUAT_SEMANTIC == "achieved_fk", f"semantic={M3_QUAT_SEMANTIC}"
    assert M3_VERSION == "v6.3.2", f"version={M3_VERSION}"
    # Cost scale must be runtime-computed from thresholds (CC2-#2 fix)
    expected_scale = 0.08 / 0.1745
    assert abs(M3_COST_SCALE - expected_scale) < 1e-9, (
        f"M3_COST_SCALE={M3_COST_SCALE}, expected {expected_scale} (runtime)"
    )
    assert cfg.K == 256, f"K={cfg.K}"
    assert cfg.H == 32, f"H={cfg.H}"
    # Callables
    for fn in (
        compute_cost_targets_from_cable,
        get_ee_poses_dual,
        mppi_generate_demos_m3,
        rollout_and_cost_m3,
        save_demos_hdf5_m3,
        save_run_metrics_json,
        slerp_numpy,
        warm_start_approach_m3,
    ):
        assert callable(fn), f"{fn.__name__} not callable"
    assert isinstance(MppiIKSolverM3, type), "MppiIKSolverM3 not a class"
    print(
        f"  M3_ACTION_DIM={M3_ACTION_DIM}, M3_VERSION={M3_VERSION}, "
        f"M3_COST_SCALE={M3_COST_SCALE:.6f}, "
        f"DRIFT_THR={DRIFT_THRESHOLD_RAD}, "
        f"DRIFT_LIMIT={DRIFT_VIOLATION_RATE_LIMIT}"
    )
    return True


# =============================================================================
# Test 2 — SSOT alignment (MPPIConfig + task_config + M3 constants)
# =============================================================================


def test_2_ssot_alignment():
    """Test 2: SSOT alignment — M3 vs MPPIConfig/task_config/test_newton_clip_routing."""
    from generate_demos_mppi_m3 import (
        DRIFT_THRESHOLD_RAD,
        M3_ACTION_DIM,
        M3_COST_SCALE,
    )
    from mpc_config import MPPIConfig
    from task_config import CABLE_SEGMENTS, T_ALIGN
    from test_newton_clip_routing import EE_BODY_OFFSET, FRANKA_NUM_JOINTS

    cfg = MPPIConfig()

    checks = [
        ("success_threshold_m", cfg.success_threshold_m, 0.08, "SSOT: mpc_config.py:86 MPPIConfig.success_threshold_m"),
        (
            "success_threshold_rad",
            cfg.success_threshold_rad,
            0.1745,
            "SSOT: mpc_config.py:88 MPPIConfig.success_threshold_rad (F1 EDIT)",
        ),
        ("pos_action_scale", cfg.pos_action_scale, 0.015, "SSOT: mpc_config.py:81 / newton_approach_cable_env.py:326"),
        ("rot_action_scale", cfg.rot_action_scale, 0.05, "SSOT: mpc_config.py:82 / newton_approach_cable_env.py:327"),
        (
            "T_ALIGN",
            T_ALIGN,
            cfg.success_threshold_rad,
            "SSOT: task_config.py:154 T_ALIGN == MPPIConfig.success_threshold_rad",
        ),
        ("CABLE_SEGMENTS", CABLE_SEGMENTS, 40, "SSOT: task_config.py:70"),
        ("FRANKA_NUM_JOINTS", FRANKA_NUM_JOINTS, 9, "SSOT: test_newton_clip_routing.py"),
        ("EE_BODY_OFFSET", EE_BODY_OFFSET, 6, "SSOT: test_newton_clip_routing.py"),
        ("M3_ACTION_DIM", M3_ACTION_DIM, 12, "DEFINE v6.3.2 I1: L_pos(3) + L_ori(3) + R_pos(3) + R_ori(3)"),
        (
            "M3_COST_SCALE = pos_thr/ori_thr",
            M3_COST_SCALE,
            cfg.success_threshold_m / cfg.success_threshold_rad,
            "DEFINE v6.3.2 P2 (success-boundary equivalence, runtime)",
        ),
        ("DRIFT_THRESHOLD_RAD", DRIFT_THRESHOLD_RAD, 0.05, "DEFINE v6.3.2 [RUN] M1 (~ori_thr/3)"),
    ]

    all_ok = True
    for name, actual, expected, source in checks:
        if isinstance(actual, float):
            ok = abs(actual - expected) < 1e-6
        else:
            ok = actual == expected
        mark = "OK" if ok else "FAIL"
        print(f"  {mark}: {name} = {actual} (expected {expected}) — {source}")
        if not ok:
            all_ok = False
    return all_ok


# =============================================================================
# Test 3 — 1-episode smoke run (12D action + quat unit-norm + trajectories)
# =============================================================================


def test_3_smoke_1ep(device):
    """Test 3: 1-episode smoke run (32 steps, 12D + quat validity)."""
    import numpy as np
    from generate_demos_mppi_m3 import M3_ACTION_DIM, mppi_generate_demos_m3
    from mpc_config import MPPIConfig

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.action_dim = M3_ACTION_DIM
    cfg.device = device

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "smoke.csv")
        demos, drifts, drifts_ep_max, cable_L_mean, cable_R_mean = mppi_generate_demos_m3(
            cfg,
            device,
            max_steps=32,
            n_demos=1,
            seed=42,
            diag_csv_path=csv_path,
        )
        csv_exists = os.path.exists(csv_path)

    assert len(demos) == 1, f"Expected 1 demo, got {len(demos)}"
    d = demos[0]
    # Trajectory shape consistency
    T = len(d["actions"])
    for key in (
        "left_ee_pos",
        "right_ee_pos",
        "left_ee_quat",
        "right_ee_quat",
        "dist_pos_left",
        "dist_pos_right",
        "dist_ori_left",
        "dist_ori_right",
    ):
        assert len(d[key]) == T, f"{key} length {len(d[key])} != {T}"
    # Action shape
    assert d["actions"].shape == (T, M3_ACTION_DIM), f"actions shape {d['actions'].shape} != ({T}, {M3_ACTION_DIM})"
    # Quat unit-norm (tolerance 1e-3 for float32 + normalize_w_positive)
    for qkey in ("left_ee_quat", "right_ee_quat"):
        norms = np.linalg.norm(d[qkey], axis=1)
        assert np.allclose(norms, 1.0, atol=1e-3), f"{qkey} not unit-norm: min={norms.min()}, max={norms.max()}"
    # Diag CSV was written during the run (existence checked inside tmpdir)
    assert csv_exists, "Diagnostic CSV not written"
    # Drift arrays populated (MPPI ON = at least some plans)
    assert len(drifts) >= 1, "drifts empty for MPPI ON 32-step run"
    assert len(drifts_ep_max) == 1, f"drifts_per_episode_max len={len(drifts_ep_max)}, expected 1"
    # Cable endpoint means populated
    assert cable_L_mean is not None and cable_L_mean.shape == (3,)
    assert cable_R_mean is not None and cable_R_mean.shape == (3,)
    print(
        f"  1 episode: {d['steps']} steps, "
        f"pos_L={d['dist_pos_left'][-1]:.4f}m pos_R={d['dist_pos_right'][-1]:.4f}m "
        f"ori_L={d['dist_ori_left'][-1]:.3f}rad ori_R={d['dist_ori_right'][-1]:.3f}rad "
        f"success={d['success']}  plans={len(drifts)}"
    )
    return True


# =============================================================================
# Tests 4-5 — F.3 v2 extended: S3 combined >= 60% (calibration) + S4 OFF = 0%
# =============================================================================


def test_45_f3v2_combined(device):
    """Tests 4-5: S3 combined >= 60% (ON, 5ep) + S4 = 0% (OFF, 5ep)."""

    from generate_demos_mppi_m3 import (
        _MPPI_ORI_THR_RAD,
        M3_ACTION_DIM,
        mppi_generate_demos_m3,
    )
    from mpc_config import MPPIConfig

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.action_dim = M3_ACTION_DIM
    cfg.device = device
    pos_thr = cfg.success_threshold_m
    ori_thr = _MPPI_ORI_THR_RAD

    with tempfile.TemporaryDirectory() as tmpdir:
        # MPPI ON (5 episodes)
        print("\n  --- MPPI ON (lambda=0.3, 5 episodes) ---")
        csv_on = os.path.join(tmpdir, "on.csv")
        demos_on, _, _, _, _ = mppi_generate_demos_m3(
            cfg,
            device,
            max_steps=128,
            n_demos=5,
            seed=42,
            diag_csv_path=csv_on,
        )
        n_succ_on = sum(1 for d in demos_on if d["success"])
        s3_on = n_succ_on / 5
        print(f"  ON: {n_succ_on}/5 combined success, S3={s3_on:.0%}")

        # MPPI OFF (5 episodes, S4 baseline)
        print("\n  --- MPPI OFF (warm-start terminal only, 5 episodes) ---")
        csv_off = os.path.join(tmpdir, "off.csv")
        demos_off, _, _, _, _ = mppi_generate_demos_m3(
            cfg,
            device,
            max_steps=128,
            n_demos=5,
            seed=42,
            no_mppi=True,
            diag_csv_path=csv_off,
        )
        n_succ_off = sum(1 for d in demos_off if d["success"])
        s4_off = n_succ_off / 5
        print(f"  OFF: {n_succ_off}/5 terminal success, S4={s4_off:.0%}")

    # Test 4: S3 combined >= 60% (DEFINE v6.2 N1 calibration gate)
    c4 = s3_on >= 0.60
    print(f"\n  Test 4 (S3 combined >= 60%): {s3_on:.0%} {'PASS' if c4 else 'FAIL (BLOCKED_FOR_USER triggered)'}")

    # Test 5: S4 MPPI OFF = 0%
    c5 = s4_off == 0.0
    print(f"  Test 5 (S4 OFF = 0%):         {s4_off:.0%} {'PASS' if c5 else 'FAIL'}")

    return c4 and c5, {
        "demos_on": demos_on,
        "demos_off": demos_off,
        "pos_thr": pos_thr,
        "ori_thr": ori_thr,
    }


# =============================================================================
# Test 6 — Gap closure: S5 (pos) >= 100% both arms, S6 (ori) report
# =============================================================================


def test_6_gap_closure(f45_data):
    """Test 6: S5 pos gap closure >= 100% both arms independently; S6 ori report."""
    import numpy as np

    demos_on = f45_data["demos_on"]
    demos_off = f45_data["demos_off"]
    pos_thr = f45_data["pos_thr"]
    ori_thr = f45_data["ori_thr"]

    pL_on = np.mean([d["dist_pos_left"][-1] for d in demos_on])
    pR_on = np.mean([d["dist_pos_right"][-1] for d in demos_on])
    pL_off = np.mean([d["dist_pos_left"][-1] for d in demos_off])
    pR_off = np.mean([d["dist_pos_right"][-1] for d in demos_off])
    oL_on = np.mean([d["dist_ori_left"][-1] for d in demos_on])
    oR_on = np.mean([d["dist_ori_right"][-1] for d in demos_on])
    oL_off = np.mean([d["dist_ori_left"][-1] for d in demos_off])
    oR_off = np.mean([d["dist_ori_right"][-1] for d in demos_off])

    def closure(off, on, thr):
        need = off - thr
        closed = off - on
        return closed / need if need > 0 else 0.0

    s5_L = closure(pL_off, pL_on, pos_thr)
    s5_R = closure(pR_off, pR_on, pos_thr)
    s6_L = closure(oL_off, oL_on, ori_thr)
    s6_R = closure(oR_off, oR_on, ori_thr)

    print(f"  S5 LEFT  pos: off={pL_off:.4f}m on={pL_on:.4f}m thr={pos_thr}m → {s5_L * 100:.1f}%")
    print(f"  S5 RIGHT pos: off={pR_off:.4f}m on={pR_on:.4f}m thr={pos_thr}m → {s5_R * 100:.1f}%")
    print(f"  S6 LEFT  ori: off={oL_off:.3f} on={oL_on:.3f} thr={ori_thr} → {s6_L * 100:.1f}% (REPORT)")
    print(f"  S6 RIGHT ori: off={oR_off:.3f} on={oR_on:.3f} thr={ori_thr} → {s6_R * 100:.1f}% (REPORT)")

    # S5 MUST per DEFINE v6.3.2; S6 SHOULD (report only)
    s5_ok = s5_L >= 1.0 and s5_R >= 1.0
    print(f"  Test 6 (S5 pos gap >= 100% both arms): {'PASS' if s5_ok else 'FAIL'}")
    return s5_ok


# =============================================================================
# Test 7 — Cable L/R endpoint geometric consistency (Y-reflection)
# =============================================================================


def test_7_cable_geometry(device):
    """Test 7: cable_L_endpoint_mean vs cable_R_endpoint_mean L/R symmetry."""

    from generate_demos_mppi_m3 import M3_ACTION_DIM, mppi_generate_demos_m3
    from mpc_config import MPPIConfig

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.action_dim = M3_ACTION_DIM
    cfg.device = device

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "geom.csv")
        _, _, _, cable_L_mean, cable_R_mean = mppi_generate_demos_m3(
            cfg,
            device,
            max_steps=32,
            n_demos=2,
            seed=42,
            no_mppi=True,  # Fast: warm-start only + no MPPI loop
            diag_csv_path=csv_path,
        )

    assert cable_L_mean is not None and cable_R_mean is not None, "Cable endpoint means missing"
    assert cable_L_mean.shape == (3,) and cable_R_mean.shape == (3,)

    # Cable extends along Y-axis. Seg 0 (L) and seg last (R) should be on
    # opposite sides of the cable midpoint along Y.
    dy = cable_R_mean[1] - cable_L_mean[1]
    # X and Z should be approximately equal (cable aligned to Y)
    dx = abs(cable_R_mean[1 - 1] - cable_L_mean[1 - 1])  # X
    dz = abs(cable_R_mean[2] - cable_L_mean[2])

    # Expected cable length ≈ CABLE_SEGMENTS * CABLE_SEG_LEN; Y diff should
    # equal that length (positive)
    from task_config import CABLE_SEG_LEN, CABLE_SEGMENTS

    expected_dy = CABLE_SEGMENTS * CABLE_SEG_LEN

    print(f"  cable_L_mean={cable_L_mean}")
    print(f"  cable_R_mean={cable_R_mean}")
    print(f"  dy={dy:.4f}m (expected ~{expected_dy:.4f}m) dx={dx:.4f}m dz={dz:.4f}m")

    # Geometric checks (loose tolerance for warm-start cable deformation)
    tol = 0.03  # 30mm tolerance
    dy_ok = abs(dy - expected_dy) < tol
    dxdz_ok = dx < tol and dz < tol

    print(f"  Test 7a (|dy - expected| < {tol}): {'PASS' if dy_ok else 'FAIL'}")
    print(f"  Test 7b (dx,dz < {tol}): {'PASS' if dxdz_ok else 'FAIL'}")

    return dy_ok and dxdz_ok


# =============================================================================
# Test 8 — Bit-exact determinism (two runs same seed)
# =============================================================================


def test_8_determinism(device):
    """Test 8: two runs with same seed → np.array_equal across key arrays."""
    import numpy as np
    from generate_demos_mppi_m3 import M3_ACTION_DIM, mppi_generate_demos_m3
    from mpc_config import MPPIConfig

    cfg = MPPIConfig()
    cfg.temperature_lambda = 0.3
    cfg.noise_sigma = 0.2
    cfg.action_dim = M3_ACTION_DIM
    cfg.device = device

    def run_once(tmpdir, tag):
        csv_path = os.path.join(tmpdir, f"det_{tag}.csv")
        demos, drifts, ep_max, cL, cR = mppi_generate_demos_m3(
            cfg,
            device,
            max_steps=32,
            n_demos=1,
            seed=42,
            diag_csv_path=csv_path,
        )
        return demos[0], drifts, ep_max, cL, cR

    with tempfile.TemporaryDirectory() as tmpdir:
        d1, drifts1, ep1, cL1, cR1 = run_once(tmpdir, "a")
        d2, drifts2, ep2, cL2, cR2 = run_once(tmpdir, "b")

    # Key arrays: must be identical (bit-exact)
    keys = (
        "left_ee_pos",
        "right_ee_pos",
        "left_ee_quat",
        "right_ee_quat",
        "actions",
        "dist_pos_left",
        "dist_pos_right",
        "dist_ori_left",
        "dist_ori_right",
    )
    all_ok = True
    for k in keys:
        eq = np.array_equal(d1[k], d2[k])
        print(f"  {k}: {'EXACT' if eq else 'MISMATCH'} (shape={d1[k].shape}, dtype={d1[k].dtype})")
        if not eq:
            # Quantify mismatch for debugging
            diff = np.abs(d1[k].astype(np.float64) - d2[k].astype(np.float64))
            print(f"    max|diff|={diff.max():.3e}, mean|diff|={diff.mean():.3e}")
            all_ok = False

    # Scalars
    assert d1["success"] == d2["success"], "success mismatch"
    assert d1["steps"] == d2["steps"], "steps mismatch"
    # Cable means (runtime-computed)
    if not np.array_equal(cL1, cL2):
        print(f"  cable_L_mean MISMATCH: {cL1} vs {cL2}")
        all_ok = False
    if not np.array_equal(cR1, cR2):
        print(f"  cable_R_mean MISMATCH: {cR1} vs {cR2}")
        all_ok = False

    print(f"  Test 8 (bit-exact determinism across {len(keys)} arrays + cable means): {'PASS' if all_ok else 'FAIL'}")
    return all_ok


# =============================================================================
# Main — test orchestration
# =============================================================================


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


def main():
    parser = argparse.ArgumentParser(description="M3 MPPI regression test")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--skip-full", action="store_true", help="Skip GPU-heavy tests (4-7), keep 1/2/3/8")
    parser.add_argument("--skip-det", action="store_true", help="Skip determinism test (8)")
    args = parser.parse_args()

    print("=" * 60)
    print("  M3 MPPI Regression Test (ctxverify-test M3)")
    print("=" * 60)

    results = {}
    t_start = time.perf_counter()

    print("\n[Test 1] Import smoke...")
    try:
        results["t1"] = test_1_import_smoke()
        print(f"  {'PASS' if results['t1'] else 'FAIL'}")
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

    import warp as wp

    wp.init()
    wp.set_device(args.device)

    print("\n[Test 3] 1-episode smoke run (12D + quat unit-norm)...")
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

    if not args.skip_full:
        print("\n[Tests 4-5] F.3 v2 S3 combined >= 60% + S4 OFF = 0%...")
        f45_data = None
        try:
            passed, f45_data = test_45_f3v2_combined(args.device)
            results["t45"] = passed
            print(f"  {'PASS' if passed else 'FAIL'}")
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback

            traceback.print_exc()
            results["t45"] = False

        if f45_data is not None:
            print("\n[Test 6] Gap closure (S5 pos MUST, S6 ori REPORT)...")
            try:
                results["t6"] = test_6_gap_closure(f45_data)
                print(f"  {'PASS' if results['t6'] else 'FAIL'}")
            except Exception as e:
                print(f"  FAIL: {e}")
                import traceback

                traceback.print_exc()
                results["t6"] = False

        print("\n[Test 7] Cable L/R endpoint geometric consistency...")
        try:
            results["t7"] = test_7_cable_geometry(args.device)
            print(f"  {'PASS' if results['t7'] else 'FAIL'}")
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback

            traceback.print_exc()
            results["t7"] = False
    else:
        print("\n[SKIP] Tests 4-7 (--skip-full)")

    if not args.skip_det:
        print("\n[Test 8] Bit-exact determinism...")
        try:
            results["t8"] = test_8_determinism(args.device)
            print(f"  {'PASS' if results['t8'] else 'FAIL'}")
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback

            traceback.print_exc()
            results["t8"] = False
    else:
        print("\n[SKIP] Test 8 (--skip-det)")

    _print_summary(results, t_start)
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
