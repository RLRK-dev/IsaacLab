# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build Unclamp precondition cache.

Constructs the initial state for Unclamp RL training:
- Cable seated in groove at C1
- Left arm at push height, fingers at HALF_OPEN
- Right arm at push height, fingers at OPEN
- VBD settled (cable-clip contact stabilized)

The env also has a built-in synthetic fallback, but this script produces
a higher-quality precondition with longer settling.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/build_unclamp_precondition.py \
        --world-count 256 --device cuda:0
"""

import argparse
import os
import sys

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD
from newton.ik import IKSolver, IKObjectivePosition, IKObjectiveRotation, IKObjectiveJointLimit

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _script_dir)

from newton_skill_env_base import (
    build_fk_and_init,
    build_multiworld_scene,
    solve_ik_single,
    broadcast_fk_to_all_worlds,
    physics_step,
    hold_position,
    save_precondition_cache,
    ROBOT_BODY_COUNT, ROBOT_BODIES_PER_ARM,
    DT, SIM_DT, SIM_SUBSTEPS, VBD_ITERATIONS,
    IK_ITERATIONS_INIT, IK_STEP_SIZE,
    FINGER_JOINT_INDICES,
)
from test_newton_clip_routing import (
    build_fk_model, FRANKA_NUM_JOINTS, EE_BODY_OFFSET, GRAVITY,
)
from task_config import (
    TABLE_HEIGHT, PUSH_Z, CLIP_BASE_HEIGHT,
    CABLE_SEGMENTS, CABLE_SEG_LEN, CABLE_RADIUS,
    CLIP1_X, CLIP1_Y, GROOVE_CENTER_Z,
    FINGER_OPEN_POS, FINGER_HALF_OPEN_POS,
    GRIP_HALF_SPAN, SETTLE_STEPS,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-count", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--settle-frames", type=int, default=300)
    args = parser.parse_args()

    device = args.device
    os.environ["NEWTON_DEVICE"] = device
    import test_newton_clip_routing as _tncr
    _tncr.DEVICE = device
    world_count = args.world_count

    if args.output is None:
        cache_dir = os.path.join(_env_dir, "..", "data", "rl_unclamp_cache")
        os.makedirs(cache_dir, exist_ok=True)
        args.output = os.path.join(cache_dir, f"unclamp_w{world_count}.npz")

    print(f"[BuildUC] worlds={world_count}, device={device}")
    print(f"[BuildUC] output={args.output}")

    # Build FK with L=HALF_OPEN, R=OPEN
    fk_model, fk_state, fk_jq = build_fk_and_init(
        left_finger_pos=FINGER_HALF_OPEN_POS,
        right_finger_pos=FINGER_OPEN_POS,
        device=device,
    )

    # IK: both arms at push height near clip
    target_left = wp.vec3(CLIP1_X, CLIP1_Y - GRIP_HALF_SPAN, PUSH_Z)
    target_right = wp.vec3(CLIP1_X, CLIP1_Y + GRIP_HALF_SPAN, PUSH_Z)
    jq_solved = solve_ik_single(fk_model, fk_state, target_left, target_right,
                                device)
    if np.any(np.isnan(jq_solved)):
        raise RuntimeError("[BuildUC] IK failed (NaN)")

    # Preserve finger positions
    # Franka-legacy finger indices, NOT UR5e-swapped (S2); port for UR5e (see S2_DEFERRED_OBLIGATIONS.md)
    jq_solved[7] = FINGER_HALF_OPEN_POS
    jq_solved[8] = FINGER_HALF_OPEN_POS
    jq_solved[FRANKA_NUM_JOINTS + 7] = FINGER_OPEN_POS
    jq_solved[FRANKA_NUM_JOINTS + 8] = FINGER_OPEN_POS

    fk_state.joint_q.assign(jq_solved)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # Build multi-world scene (with clip, no support clips)
    scene = build_multiworld_scene(fk_model, fk_state, world_count, device,
                                   add_support_clips=False)
    broadcast_fk_to_all_worlds(fk_state, scene["state_0"], scene["bws"],
                               world_count)

    # Teleport cable into groove
    print("[BuildUC] Teleporting cable into groove...")
    wp.synchronize()
    bq = scene["state_0"].body_q.numpy()
    cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
    cable_y_start = CLIP1_Y - cable_half_len

    for w in range(world_count):
        for i, bi in enumerate(scene["cable_bodies"][w]):
            seg_y = cable_y_start + i * CABLE_SEG_LEN
            bq[bi, 0] = CLIP1_X
            bq[bi, 1] = seg_y
            bq[bi, 2] = GROOVE_CENTER_Z
            bq[bi, 3:7] = [0.0, 0.0, 0.0, 1.0]
    scene["state_0"].body_q.assign(bq)

    # Zero velocities
    bqd = scene["state_0"].body_qd.numpy()
    for w in range(world_count):
        for bi in scene["cable_bodies"][w]:
            bqd[bi, :] = 0.0
    scene["state_0"].body_qd.assign(bqd)
    scene["solver"].body_q_prev.assign(bq)

    # Settle physics
    print(f"[BuildUC] Settling ({args.settle_frames} frames)...")
    state_0, state_1 = scene["state_0"], scene["state_1"]
    for _ in range(args.settle_frames):
        broadcast_fk_to_all_worlds(fk_state, state_0, scene["bws"],
                                   world_count)
        state_0, state_1 = physics_step(
            scene["model"], scene["solver"], state_0, state_1,
            scene["control"], scene["contacts"],
        )
    scene["state_0"], scene["state_1"] = state_0, state_1

    # Verify
    wp.synchronize()
    bq = state_0.body_q.numpy()
    cable_z = np.mean(bq[scene["cable_bodies"][0], 2])
    print(f"[BuildUC] Post-settle cable Z: {cable_z:.4f} "
          f"(groove: {GROOVE_CENTER_Z:.4f}, "
          f"delta: {(cable_z - GROOVE_CENTER_Z)*1000:.1f}mm)")

    # Save cache
    save_precondition_cache(args.output, scene, fk_state, world_count)
    print(f"[BuildUC] Done: {args.output}")


if __name__ == "__main__":
    main()
