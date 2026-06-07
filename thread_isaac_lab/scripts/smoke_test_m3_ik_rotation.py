#!/usr/bin/env python3
"""M3 G1 smoke test: IKObjectiveRotation K=256 batched + MppiIKSolverM3 full solve.

TEMPORARY: MppiIKSolverM3 class is defined inline for F2 G1 smoke test.
Will be moved to F3 (generate_demos_mppi_m3.py) canonical location in Phase 3.

Refactor checklist at F3 implementation:
  1. Move class to F3 canonical location (generate_demos_mppi_m3.py)
  2. Delete inline definition in F2 (this file)
  3. Add import in F2: from generate_demos_mppi_m3 import MppiIKSolverM3
  4. Grep check: class name unique across codebase (no duplicates)
  5. Attribute name consistency check: obj_L_ori, obj_R_ori, obj_L_pos, obj_R_pos, obj_jlimit
     (F2 Step 2-3 reference these attributes via ik_solver.obj_L_ori;
      F3 canonical class must match attribute names exactly)

Spec: DEFINE v6.3.2 §[CHANGE Gate Preconditions] G1:
  Step 1: Init IKObjectiveRotation (link_offset_rotation=wp.quat_identity())
  Step 2: Set single tile (identity quat, K=256)
  Step 3: Set per-world normalized unit quat (K=256)
  Step 4: MppiIKSolverM3 full solve (5 obj, 30 iter, realistic target)
  Step 5: Performance < 10s

Pass criteria (all MUST):
  P1: No TypeError/ValueError/Warp kernel error/NaN/inf
  P2: jq_solved.shape == (K, joint_coord_count); mean pos_residual < 0.005m
      AND mean ori_residual < 0.05 rad (both arms AND)
  P3: wall-clock < 10s

Usage:
    cd ~/IsaacLab
    PYTHONPATH=$PYTHONPATH:thread_isaac_lab/scripts:thread_isaac_lab/configs \\
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/smoke_test_m3_ik_rotation.py \\
        --device cuda:1
"""

import argparse
import math
import os
import sys
import time

import numpy as np
import warp as wp
import newton
from newton.ik import (
    IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit,
)
from newton._src.sim.ik.ik_common import eval_fk_batched

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))

from test_newton_clip_routing import build_fk_model, FRANKA_NUM_JOINTS, EE_BODY_OFFSET
from generate_demos_mppi_m2 import IK_ITERATIONS, IK_STEP_SIZE, RIGHT_EE_BODY_OFFSET

K = 256
POS_THR_M = 0.005   # 5mm
ORI_THR_RAD = 0.05  # ~2.86°
WALL_CLOCK_LIMIT_S = 10.0


# =========================================================================
# Helper utilities (local)
# =========================================================================

def _quat_from_axis_angle(axis, angle):
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / np.linalg.norm(axis)
    half = angle / 2.0
    s = math.sin(half)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, math.cos(half)],
                    dtype=np.float32)


def _quat_distance(q1, q2):
    dot = float(np.dot(q1, q2))
    dot = min(1.0, max(-1.0, abs(dot)))
    return 2.0 * math.acos(dot)


# =========================================================================
# MppiIKSolverM3 (TEMPORARY inline; see header)
# =========================================================================

class MppiIKSolverM3:
    """TEMPORARY inline for F2 G1 smoke test. See header refactor checklist.

    M3 extension of M2 MppiIKSolver: 5 objectives (L_pos, L_ori, R_pos, R_ori, jlimit).
    """

    def __init__(self, fk_model, K=256, device="cuda:0"):
        self.K = K
        self.device = device
        self.fk_model = fk_model

        self.obj_L_pos = IKObjectivePosition(
            link_index=EE_BODY_OFFSET,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(K, dtype=wp.vec3, device=device),
            weight=1.0,
        )
        self.obj_L_ori = IKObjectiveRotation(
            link_index=EE_BODY_OFFSET,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.zeros(K, dtype=wp.vec4, device=device),
            weight=0.5,
        )
        self.obj_R_pos = IKObjectivePosition(
            link_index=RIGHT_EE_BODY_OFFSET,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.zeros(K, dtype=wp.vec3, device=device),
            weight=1.0,
        )
        self.obj_R_ori = IKObjectiveRotation(
            link_index=RIGHT_EE_BODY_OFFSET,
            link_offset_rotation=wp.quat_identity(),
            target_rotations=wp.zeros(K, dtype=wp.vec4, device=device),
            weight=0.5,
        )
        self.obj_jlimit = IKObjectiveJointLimit(
            joint_limit_lower=fk_model.joint_limit_lower,
            joint_limit_upper=fk_model.joint_limit_upper,
            weight=10.0,
        )

        self.solver = IKSolver(
            fk_model, n_problems=K,
            objectives=[
                self.obj_L_pos, self.obj_L_ori,
                self.obj_R_pos, self.obj_R_ori,
                self.obj_jlimit,
            ],
        )

        coord = fk_model.joint_coord_count
        self.jq_in = wp.zeros((K, coord), dtype=float, device=device)
        self.jq_out = wp.zeros((K, coord), dtype=float, device=device)

    def solve(self, target_L_pos, target_L_quat, target_R_pos, target_R_quat,
              jq_starts):
        """5-obj IK. target_*_pos: (K,3) float32. target_*_quat: (K,4) float32 xyzw."""
        self.obj_L_pos.set_target_positions(
            wp.array(target_L_pos.astype(np.float32), dtype=wp.vec3,
                     device=self.device))
        self.obj_L_ori.set_target_rotations(
            wp.array(target_L_quat.astype(np.float32), dtype=wp.vec4,
                     device=self.device))
        self.obj_R_pos.set_target_positions(
            wp.array(target_R_pos.astype(np.float32), dtype=wp.vec3,
                     device=self.device))
        self.obj_R_ori.set_target_rotations(
            wp.array(target_R_quat.astype(np.float32), dtype=wp.vec4,
                     device=self.device))
        self.jq_in.assign(jq_starts.astype(np.float64))
        self.solver.step(self.jq_in, self.jq_out,
                         iterations=IK_ITERATIONS, step_size=IK_STEP_SIZE)
        return self.jq_out.numpy()


# =========================================================================
# G1 Test sequence
# =========================================================================

def _eval_fk_home_ee_pose(fk_model, device):
    """Evaluate home-pose FK and return (L_pos, L_quat, R_pos, R_quat) for world 0.

    Returns np.float32 arrays: L_pos (3,), L_quat (4,) xyzw, R_pos (3,), R_quat (4,).
    """
    coord = fk_model.joint_coord_count
    dof = fk_model.joint_dof_count
    body_count = fk_model.body_count
    jq_home_wp = wp.zeros((1, coord), dtype=float, device=device)
    jqd_wp = wp.zeros((1, dof), dtype=float, device=device)
    body_q_wp = wp.zeros((1, body_count), dtype=wp.transform, device=device)
    body_qd_wp = wp.zeros((1, body_count), dtype=wp.spatial_vector, device=device)
    eval_fk_batched(fk_model, jq_home_wp, jqd_wp, body_q_wp, body_qd_wp)
    body_q_np = body_q_wp.numpy()  # dtype=wp.transform (7 float)
    # wp.transform: 7 floats per body = (px, py, pz, qx, qy, qz, qw)
    flat = body_q_np.view(np.float32).reshape(body_count, 7)
    return (flat[EE_BODY_OFFSET, :3].copy(),
            flat[EE_BODY_OFFSET, 3:7].copy(),
            flat[RIGHT_EE_BODY_OFFSET, :3].copy(),
            flat[RIGHT_EE_BODY_OFFSET, 3:7].copy())


def _eval_fk_batched_residuals(fk_model, jq_solved, K, device):
    """Evaluate FK for K solved jq, extract EE pose. Returns arrays shape (K,3) / (K,4)."""
    coord = fk_model.joint_coord_count
    dof = fk_model.joint_dof_count
    body_count = fk_model.body_count
    jq_wp = wp.array(jq_solved.astype(np.float64), dtype=float, device=device)
    jqd_wp = wp.zeros((K, dof), dtype=float, device=device)
    body_q_wp = wp.zeros((K, body_count), dtype=wp.transform, device=device)
    body_qd_wp = wp.zeros((K, body_count), dtype=wp.spatial_vector, device=device)
    eval_fk_batched(fk_model, jq_wp, jqd_wp, body_q_wp, body_qd_wp)
    body_q_np = body_q_wp.numpy()  # (K, body_count) dtype=wp.transform
    flat = body_q_np.view(np.float32).reshape(K, body_count, 7)
    return (flat[:, EE_BODY_OFFSET, :3].copy(),
            flat[:, EE_BODY_OFFSET, 3:7].copy(),
            flat[:, RIGHT_EE_BODY_OFFSET, :3].copy(),
            flat[:, RIGHT_EE_BODY_OFFSET, 3:7].copy())


def run_g1(device):
    t0 = time.perf_counter()
    print(f"[G1] M3 IKObjectiveRotation K={K} + MppiIKSolverM3 full solve")
    print(f"[G1] Device: {device}\n")

    # ---- Step 1: Standalone IKObjectiveRotation init (TypeError check) ----
    # Note: Newton 1.13 IKObjectiveRotation requires set_batch_layout() from
    # IKSolver before manipulation; Steps 2-3 therefore use the solver-wrapped
    # objectives (see DEFINE v6.3.2 G1 Implementation Note 2026-04-18 addendum).
    print(f"[Step 1] Standalone init IKObjectiveRotation (link_index={EE_BODY_OFFSET}, K={K})")
    _standalone_obj_rot = IKObjectiveRotation(
        link_index=EE_BODY_OFFSET,
        link_offset_rotation=wp.quat_identity(),
        target_rotations=wp.zeros(K, dtype=wp.vec4, device=device),
        weight=0.5,
    )
    print("  OK: standalone init (3 args incl link_offset_rotation; no TypeError)")

    # ---- Build MppiIKSolverM3 (IKSolver ctor runs set_batch_layout) ----
    print("\n[Build] fk_model + MppiIKSolverM3 (set_batch_layout completed)")
    fk_model = build_fk_model(device=device)
    ik_solver = MppiIKSolverM3(fk_model, K=K, device=device)
    obj_rot = ik_solver.obj_L_ori  # solver-wrapped; batch_layout assigned

    # ---- Step 2: Set single tile via solver-wrapped obj ----
    print(f"\n[Step 2] Set single tile via ik_solver.obj_L_ori (identity, K={K})")
    identity_quat = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    tiled = np.tile(identity_quat[None], (K, 1))
    obj_rot.set_target_rotations(wp.array(tiled, dtype=wp.vec4, device=device))
    print(f"  OK: tile shape={tiled.shape}, dtype={tiled.dtype}")

    # ---- Step 3: Set per-world normalized unit quat via solver-wrapped obj ----
    print(f"\n[Step 3] Set per-world normalized unit quat via ik_solver.obj_L_ori (K={K})")
    rng = np.random.default_rng(42)
    q_pw = rng.standard_normal((K, 4)).astype(np.float32)
    q_pw /= np.linalg.norm(q_pw, axis=1, keepdims=True)
    obj_rot.set_target_rotations(wp.array(q_pw, dtype=wp.vec4, device=device))
    norms = np.linalg.norm(q_pw, axis=1)
    print(f"  OK: per-world shape={q_pw.shape}, "
          f"norm range=[{norms.min():.6f}, {norms.max():.6f}]")
    assert norms.min() > 0.999 and norms.max() < 1.001, \
        "per-world quats not unit-normalized"

    # ---- Step 4: MppiIKSolverM3 full solve (ik_solver already constructed) ----
    print("\n[Step 4] MppiIKSolverM3 full solve (5 obj, 30 iter, realistic target)")

    # Use home-pose FK for reachable targets (small delta for convergence)
    hL_pos, hL_quat, hR_pos, hR_quat = _eval_fk_home_ee_pose(fk_model, device)
    print(f"  home L_pos={hL_pos}, R_pos={hR_pos}")

    # Small ori target: 0.2 rad about Y (≈ 11.46°), applied to home quat
    small_rot = _quat_from_axis_angle([0, 1, 0], 0.2)

    def _quat_mul_xyzw(q1, q2):
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2
        return np.array([
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        ], dtype=np.float32)

    target_L_quat_single = _quat_mul_xyzw(small_rot, hL_quat)
    target_R_quat_single = _quat_mul_xyzw(small_rot, hR_quat)
    # Small pos target: home + 2cm X (within workspace)
    pos_delta = np.array([0.02, 0.0, 0.0], dtype=np.float32)

    target_L_pos = np.tile((hL_pos + pos_delta)[None], (K, 1))
    target_R_pos = np.tile((hR_pos + pos_delta)[None], (K, 1))
    target_L_quat = np.tile(target_L_quat_single[None], (K, 1))
    target_R_quat = np.tile(target_R_quat_single[None], (K, 1))

    coord = fk_model.joint_coord_count
    jq_home = np.zeros((K, coord), dtype=np.float64)

    t_solve_start = time.perf_counter()
    jq_solved = ik_solver.solve(
        target_L_pos, target_L_quat,
        target_R_pos, target_R_quat,
        jq_home,
    )
    t_solve_end = time.perf_counter()

    assert jq_solved.shape == (K, coord), \
        f"jq_solved shape {jq_solved.shape} != ({K}, {coord})"
    assert np.isfinite(jq_solved).all(), "jq_solved contains NaN or inf"
    print(f"  OK: jq_solved shape={jq_solved.shape}, all finite")
    print(f"  IK solve wall-clock: {t_solve_end - t_solve_start:.2f}s")

    # ---- FK eval to compute residuals ----
    L_pos_fk, L_quat_fk, R_pos_fk, R_quat_fk = _eval_fk_batched_residuals(
        fk_model, jq_solved, K, device)

    pos_err_L = np.linalg.norm(L_pos_fk - target_L_pos, axis=1)
    pos_err_R = np.linalg.norm(R_pos_fk - target_R_pos, axis=1)
    ori_err_L = np.array([_quat_distance(L_quat_fk[k], target_L_quat[k])
                          for k in range(K)])
    ori_err_R = np.array([_quat_distance(R_quat_fk[k], target_R_quat[k])
                          for k in range(K)])

    mean_pos_L = float(pos_err_L.mean())
    mean_pos_R = float(pos_err_R.mean())
    mean_ori_L = float(ori_err_L.mean())
    mean_ori_R = float(ori_err_R.mean())

    print(f"  residuals: pos L={mean_pos_L * 1000:.2f}mm R={mean_pos_R * 1000:.2f}mm "
          f"ori L={math.degrees(mean_ori_L):.2f}° R={math.degrees(mean_ori_R):.2f}°")

    # ---- Step 5: Performance ----
    t_total = time.perf_counter() - t0
    print(f"\n[Step 5] Total wall-clock: {t_total:.2f}s")

    # ---- Verdict ----
    pass_p1 = True  # no exception = P1 OK
    pass_p2_pos = mean_pos_L < POS_THR_M and mean_pos_R < POS_THR_M
    pass_p2_ori = mean_ori_L < ORI_THR_RAD and mean_ori_R < ORI_THR_RAD
    pass_p2 = pass_p2_pos and pass_p2_ori
    pass_p3 = t_total < WALL_CLOCK_LIMIT_S

    print("\n" + "=" * 60)
    print("  G1 Smoke Test Summary")
    print("=" * 60)
    print(f"  P1 (no error, all finite):   {'PASS' if pass_p1 else 'FAIL'}")
    print(f"  P2 pos (<{POS_THR_M*1000:.1f}mm 両腕 AND):  L={mean_pos_L*1000:.2f}mm "
          f"R={mean_pos_R*1000:.2f}mm  {'PASS' if pass_p2_pos else 'FAIL'}")
    print(f"  P2 ori (<{math.degrees(ORI_THR_RAD):.2f}° 両腕 AND):  L={math.degrees(mean_ori_L):.2f}° "
          f"R={math.degrees(mean_ori_R):.2f}°  {'PASS' if pass_p2_ori else 'FAIL'}")
    print(f"  P2 overall:                  {'PASS' if pass_p2 else 'FAIL'}")
    print(f"  P3 (wall-clock<{WALL_CLOCK_LIMIT_S:.0f}s):      "
          f"{t_total:.2f}s  {'PASS' if pass_p3 else 'FAIL'}")
    all_pass = pass_p1 and pass_p2 and pass_p3
    verdict = "ALL PASS" if all_pass else "FAIL"
    print(f"\n  G1 Verdict: {verdict}")
    print("=" * 60)

    return all_pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda:0",
                        help="Warp device (default: cuda:0)")
    args = parser.parse_args()

    wp.init()
    wp.set_device(args.device)

    try:
        ok = run_g1(args.device)
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"\n[G1] EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
