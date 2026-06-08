#!/usr/bin/env python3
"""Diagnose Unclamp env step-1 instant death.

Instruments the first RL step to find where NaN/explosion originates:
  - Cable positions before/after physics step
  - Per-substep cable min/max Z
  - dist_pos, dist_ori before explosion check
  - Finger spring forces
"""
import os, sys, math
import numpy as np
import torch
import warp as wp

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)

from newton_unclamp_env import (
    NewtonUnclampEnv, _find_nearest_cable_point, _normalize_quat_w_positive,
    _quat_distance, GROOVE_CENTER_Z, CLIP1_X, CLIP1_Y,
    FINGER_SPRING_KE, FINGER_SPRING_KD,
    RL_SIM_SUBSTEPS, RL_SIM_DT,
)
from cable_orientation_utils import compute_hand_quat_for_cable


def main():
    device = os.environ.get("NEWTON_DEVICE", "cuda:0")
    env = NewtonUnclampEnv(world_count=2, device=device)
    obs, _ = env.reset()
    print(f"\n{'='*60}")
    print("POST-RESET STATE")
    print(f"{'='*60}")

    wp.synchronize()
    bq = env._state_0.body_q.numpy()
    bqd = env._state_0.body_qd.numpy()
    prev = env._solver.body_q_prev.numpy()

    for w in range(env._world_count):
        cb = env._cable_bodies[w]
        cable_pos = bq[cb, :3]
        cable_vel = bqd[cb, 3:6]  # linear velocity
        print(f"\n--- World {w} ---")
        print(f"  Cable Z  min={cable_pos[:,2].min():.6f}  max={cable_pos[:,2].max():.6f}  "
              f"mean={cable_pos[:,2].mean():.6f}")
        print(f"  Cable vel norm max={np.linalg.norm(cable_vel, axis=1).max():.6f}")
        print(f"  Cable NaN? {np.any(np.isnan(cable_pos))}")
        # body_q_prev consistency
        prev_cable = prev[cb, :3]
        delta = np.linalg.norm(cable_pos - prev_cable, axis=1)
        print(f"  body_q vs body_q_prev delta max={delta.max():.6f}")
        # groove seg indices
        gsi = env._groove_seg_indices[w]
        print(f"  groove_seg_indices={gsi.tolist()}")
        # nearest cable point to groove center
        seg_pos, seg_tangent, seg_dist = _find_nearest_cable_point(
            cable_pos, env.GROOVE_CENTER_POS, gsi)
        print(f"  seg_pos={seg_pos}  dist={seg_dist:.6f}")
        seg_quat = _normalize_quat_w_positive(
            compute_hand_quat_for_cable(seg_tangent))
        dist_ori = _quat_distance(seg_quat, env.GROOVE_TARGET_QUAT)
        print(f"  dist_ori={dist_ori:.6f}")

    # =========================================================================
    # MANUAL STEP: instrument the physics
    # =========================================================================
    print(f"\n{'='*60}")
    print("MANUAL STEP (action=[0.5, 0, 0, 0])")
    print(f"{'='*60}")

    N = env._world_count
    actions = torch.zeros(N, 4, device=device)
    actions[:, 0] = 0.5  # finger open

    # Replicate what _apply_actions_batch does, with instrumentation
    actions_np = actions.cpu().numpy()
    finger_delta = np.maximum(actions_np[:, 0], 0.0) * env.FINGER_ACTION_SCALE
    l_pos_delta = actions_np[:, 1:4] * env.POS_ACTION_SCALE

    from newton_unclamp_env import (
        FRANKA_NUM_JOINTS, FINGER_HALF_OPEN_POS, FINGER_OPEN_POS,
        ROBOT_BODY_COUNT, ROBOT_BODIES_PER_ARM,
        FINGER_LOCAL, IK_ITERATIONS_RL, IK_STEP_SIZE,
        GRASP_Z, LIFT_Z, EE_BODY_OFFSET,
    )
    from newton_skill_env_base import eval_fk_batched

    fk_coord_count = env._fk_model.joint_coord_count
    finger_mask = np.ones(fk_coord_count, dtype=bool)
    # Franka-legacy finger indices, NOT UR5e-swapped (S2); port for UR5e (see S2_DEFERRED_OBLIGATIONS.md)
    for fc in (7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8):
        finger_mask[fc] = False

    jq_starts = np.array(env._per_world_fk_jq[:N])
    print(f"\njq_starts NaN? {np.any(np.isnan(jq_starts))}")
    print(f"jq_starts finger j7/j8: {jq_starts[0, 7]:.6f}, {jq_starts[0, 8]:.6f}")

    for w in range(N):
        new_target = env._finger_target_left[w] + finger_delta[w]
        new_target = np.clip(new_target, FINGER_HALF_OPEN_POS, FINGER_OPEN_POS)
        env._finger_target_left[w] = new_target
        jq_starts[w, 7] = new_target
        jq_starts[w, 8] = new_target
        jq_starts[w, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
        jq_starts[w, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

    targets_left = np.zeros((N, 3))
    targets_right = np.zeros((N, 3))
    for w in range(N):
        target_l = env._ee_target_left[w].copy() + l_pos_delta[w]
        target_l[2] = np.clip(target_l[2], GRASP_Z, LIFT_Z + 0.05)
        targets_left[w] = target_l
        env._ee_target_left[w] = target_l.copy()
        targets_right[w] = env._ee_target_right[w].copy()

    print(f"EE target left: {targets_left[0]}")
    print(f"EE target right: {targets_right[0]}")

    # IK solve
    env._ik_obj_pos_left.set_target_positions(
        wp.array([wp.vec3(*t) for t in targets_left],
                 dtype=wp.vec3, device=device))
    env._ik_obj_pos_right.set_target_positions(
        wp.array([wp.vec3(*t) for t in targets_right],
                 dtype=wp.vec3, device=device))
    env._ik_jq_in.assign(jq_starts)
    env._ik_solver_batch.step(env._ik_jq_in, env._ik_jq_out,
                               iterations=IK_ITERATIONS_RL,
                               step_size=IK_STEP_SIZE)
    jq_targets = env._ik_jq_out.numpy()

    nan_mask = np.any(np.isnan(jq_targets), axis=1)
    print(f"IK NaN worlds: {np.where(nan_mask)[0].tolist()}")
    if np.any(nan_mask):
        jq_targets[nan_mask] = jq_starts[nan_mask]

    for w in range(N):
        jq_targets[w, 7] = jq_starts[w, 7]
        jq_targets[w, 8] = jq_starts[w, 8]
        jq_targets[w, FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
        jq_targets[w, FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

    jq_diff = np.linalg.norm(jq_targets - jq_starts, axis=1)
    print(f"IK jq delta norm: {jq_diff}")

    # Physics stepping with instrumentation
    print(f"\n--- Physics Steps ({env.PHYSICS_STEPS_PER_RL} × {RL_SIM_SUBSTEPS} substeps) ---")

    for step in range(env.PHYSICS_STEPS_PER_RL):
        t = min((step + 1) / env.PHYSICS_STEPS_PER_RL, 1.0)

        jq_interp_all = jq_starts.copy()
        jq_interp_all[:, finger_mask] = (
            jq_starts[:, finger_mask]
            + (jq_targets[:, finger_mask] - jq_starts[:, finger_mask]) * t
        )
        for fc in (7, 8, FRANKA_NUM_JOINTS + 7, FRANKA_NUM_JOINTS + 8):
            jq_interp_all[:, fc] = (
                env._per_world_fk_jq[:N, fc]
                + (jq_targets[:, fc] - env._per_world_fk_jq[:N, fc]) * t
            )

        # FK
        env._batch_fk_jq.assign(jq_interp_all)
        eval_fk_batched(env._fk_model, env._batch_fk_jq,
                        env._batch_fk_jqd,
                        env._batch_fk_body_q, env._batch_fk_body_qd)
        batch_bq = env._batch_fk_body_q.numpy()[:, :ROBOT_BODY_COUNT]

        # Broadcast FK
        phys_bq = env._state_0.body_q.numpy()
        for w in range(N):
            ws = env._bws[w]
            for bi in range(ROBOT_BODY_COUNT):
                if (ws + bi) not in env._finger_set:
                    phys_bq[ws + bi] = batch_bq[w, bi]
        env._state_0.body_q.assign(phys_bq)

        # Substeps
        for sub in range(RL_SIM_SUBSTEPS):
            env._state_0.clear_forces()
            env._apply_finger_spring(batch_bq, N)

            # Check finger spring forces
            if step == 0 and sub == 0:
                body_f = env._state_0.body_f.numpy()
                for w in range(N):
                    ws = env._bws[w]
                    for arm_off in [0, ROBOT_BODIES_PER_ARM]:
                        for lf in FINGER_LOCAL:
                            bi = ws + arm_off + lf
                            f = body_f[bi, 3:6]
                            if np.linalg.norm(f) > 0.01:
                                print(f"  Finger spring w={w} arm={arm_off} lf={lf}: F={f}")

            env._model.collide(env._state_0, env._contacts)
            env._solver.step(env._state_0, env._state_1, env._control,
                              env._contacts, RL_SIM_DT)
            env._state_0, env._state_1 = env._state_1, env._state_0

        # Post-step cable check
        wp.synchronize()
        bq_now = env._state_0.body_q.numpy()
        for w in range(N):
            cb = env._cable_bodies[w]
            cpos = bq_now[cb, :3]
            has_nan = np.any(np.isnan(cpos))
            z_min, z_max = cpos[:, 2].min(), cpos[:, 2].max()
            if step == 0 or has_nan or step == env.PHYSICS_STEPS_PER_RL - 1:
                print(f"  step={step} w={w}: cable Z=[{z_min:.4f}, {z_max:.4f}]  "
                      f"NaN={has_nan}")

    # Save final fk
    for w in range(N):
        env._per_world_fk_jq[w] = jq_targets[w].copy()

    # =========================================================================
    # REWARD COMPUTATION
    # =========================================================================
    print(f"\n{'='*60}")
    print("REWARD COMPUTATION (manual)")
    print(f"{'='*60}")

    wp.synchronize()
    bq_final = env._state_0.body_q.numpy()

    for w in range(N):
        cb = env._cable_bodies[w]
        cable_pos = bq_final[cb, :3]
        gsi = env._groove_seg_indices[w]
        print(f"\n--- World {w} ---")
        print(f"  Cable Z  min={cable_pos[:,2].min():.6f}  max={cable_pos[:,2].max():.6f}")
        print(f"  Cable NaN? {np.any(np.isnan(cable_pos))}")

        seg_pos, seg_tangent, seg_nearest_dist = _find_nearest_cable_point(
            cable_pos, env.GROOVE_CENTER_POS, gsi)
        seg_quat = _normalize_quat_w_positive(
            compute_hand_quat_for_cable(seg_tangent))
        dist_pos = float(np.linalg.norm(seg_pos - env.GROOVE_CENTER_POS))
        dist_ori = _quat_distance(seg_quat, env.GROOVE_TARGET_QUAT)

        print(f"  seg_pos={seg_pos}  seg_tangent={seg_tangent}")
        print(f"  dist_pos={dist_pos:.6f}  NaN={math.isnan(dist_pos)}")
        print(f"  dist_ori={dist_ori:.6f}  NaN={math.isnan(dist_ori)}")
        print(f"  explosion={dist_pos > env.EXPLOSION_DIST_THRESH or math.isnan(dist_pos)}")

        # Drop check
        grip_center = gsi[len(gsi) // 2]
        grip_lo = max(0, grip_center - 5)
        grip_hi = min(len(cable_pos), grip_center + 6)
        min_grip_z = float(np.min(cable_pos[grip_lo:grip_hi, 2]))
        print(f"  min_grip_z={min_grip_z:.6f}  DROP_Z_THRESH={env.DROP_Z_THRESH:.6f}  "
              f"dropped={min_grip_z < env.DROP_Z_THRESH}")

        # Scores
        fk_jq = env._per_world_fk_jq[w]
        finger_opening = fk_jq[7] + fk_jq[8]
        from newton_unclamp_env import HALF_OPEN_SUM, FULL_OPEN_SUM
        score_finger = np.clip(
            (finger_opening - HALF_OPEN_SUM) / (FULL_OPEN_SUM - HALF_OPEN_SUM),
            0.0, 1.0)
        score_seated_pos = math.exp(-dist_pos / env.RANGE_SEATED) if not math.isnan(dist_pos) else float('nan')
        score_seated_ori = math.exp(-dist_ori / env.RANGE_ORI) if not math.isnan(dist_ori) else float('nan')
        print(f"  score_finger={score_finger:.6f}  score_seated_pos={score_seated_pos:.6f}  "
              f"score_seated_ori={score_seated_ori:.6f}")

    env.close()
    print(f"\n{'='*60}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
