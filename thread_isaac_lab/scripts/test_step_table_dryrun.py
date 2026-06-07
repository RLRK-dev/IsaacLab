# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dry-run validation for skills/ package (step_table + scripted_skills + snapshot).

Executes all 43 STEPs from the step_table without cable physics:
  - SCRIPTED Transport: ik_move_both (actual IK + physics)
  - SCRIPTED ReClamp/HalfUnclamp: interpolate_fingers (actual finger movement)
  - RL steps: hold_position dummy (50 steps)
  - WAIT ClipConfirm: dummy PASS (no cable to check)

Validates:
  1. Step table coordinates are IK-reachable
  2. Scripted skills execute without error
  3. SnapshotManager save/restore works
  4. 43-step flow is coherent end-to-end

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_step_table_dryrun.py
"""

import os
import sys
import time

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# skills/ package
_skills_dir = os.path.join(_SCRIPT_DIR, "..")
if _skills_dir not in sys.path:
    sys.path.insert(0, _skills_dir)

from skills.step_table import STEP_TABLE, StepType, SkillName  # noqa: E402
from skills.scripted_skills import (  # noqa: E402
    SkillResult,
    transport_to_clip,
    reclamp_left,
    half_unclamp_release,
)
from skills.snapshot import SnapshotManager  # noqa: E402

from newton_routing_utils import (  # noqa: E402
    TABLE_HEIGHT,
    build_fk_model, init_fk_state,
    build_scene, settle_scene,
    hold_position,
    NJMAX,
)
from task_config import CLIP_POSITIONS, REST_CLIP_X  # noqa: E402

DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0
GRAVITY = -9.81
VBD_ITERATIONS = 20

# REST clips for cable support
REST_CLIPS = [
    (0.15,  0.20, TABLE_HEIGHT),
    (0.15,  0.00, TABLE_HEIGHT),
    (0.15, -0.20, TABLE_HEIGHT),
]


def run_dryrun():
    """Execute 43-step dry-run and report results."""
    wp.init()
    wp.set_device(DEVICE)

    print(f"[DRY-RUN] 43-step skills/ package validation (device={DEVICE})")
    print(f"[DRY-RUN] Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"[DRY-RUN] No cable — IK + scripted skills only\n")

    # Build FK model
    fk_model = build_fk_model(DEVICE, gravity=GRAVITY)
    fk_state = init_fk_state(fk_model, finger_open=True)

    # Clip positions: 5 routing + 3 rest
    clip_positions_3d = [(cx, cy, TABLE_HEIGHT) for cx, cy in CLIP_POSITIONS]
    all_clips = clip_positions_3d + REST_CLIPS

    # Build scene (no cable)
    scene_info = build_scene(
        device=DEVICE, clip_positions=all_clips,
        fk_model=fk_model, fk_state=fk_state,
        use_cable=False, gravity=GRAVITY,
    )
    model = scene_info["model"]
    state = model.state()
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control
    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)

    # Brief settle
    print("[DRY-RUN] Settling (0.5s)...")
    state = settle_scene(model, state, scene_info, solver, contacts,
                         duration_s=0.5, dt=DT)

    # Snapshot manager
    snap_mgr = SnapshotManager()
    results = []
    t_start = time.time()

    print(f"\n{'='*70}")
    print(f"  EXECUTING 43 STEPs")
    print(f"{'='*70}\n")

    for step_def in STEP_TABLE:
        sid = step_def.step_id
        stype = step_def.step_type
        skill = step_def.skill
        desc = step_def.description

        print(f"--- STEP {sid:2d} [{stype.value}] {skill.value:<25s} {desc}")

        # Save snapshot before execution
        snap_mgr.save(
            step_id=sid,
            state_0=state,
            fk_state=fk_state,
            clip_status=[False] * 5,
            ik_target_l=step_def.target_left,
            ik_target_r=step_def.target_right,
        )

        result = SkillResult.SUCCESS
        detail = ""

        if stype == StepType.SCRIPTED:
            if skill == SkillName.TRANSPORT:
                if step_def.target_left is None or step_def.target_right is None:
                    detail = "NO_TARGET (skip)"
                    result = SkillResult.SUCCESS
                else:
                    state, result = transport_to_clip(
                        model, state, scene_info, solver, contacts,
                        target_left=step_def.target_left,
                        target_right=step_def.target_right,
                        label=f"S{sid}",
                    )
                    detail = f"→ L={step_def.target_left} R={step_def.target_right}"

            elif skill == SkillName.RECLAMP_L:
                state, result = reclamp_left(
                    model, state, scene_info, solver, contacts,
                    label=f"S{sid}_RECLAMP",
                )
                detail = "L finger → 0.002"

            elif skill == SkillName.HALF_UNCLAMP_RELEASE:
                state, result = half_unclamp_release(
                    model, state, scene_info, solver, contacts,
                    label=f"S{sid}_HALF_UNCLAMP",
                )
                detail = "L→0.006, R→0.04"

        elif stype == StepType.RL:
            # Dummy: hold position briefly
            state = hold_position(model, state, scene_info, solver, contacts, 50)
            result = SkillResult.SUCCESS
            detail = "DUMMY (hold 50 steps)"

        elif stype == StepType.WAIT:
            # Dummy: no cable to check
            state = hold_position(model, state, scene_info, solver, contacts, 30)
            result = SkillResult.SUCCESS
            detail = "DUMMY (no cable)"

        status = "PASS" if result == SkillResult.SUCCESS else "FAIL"
        results.append({
            "step": sid,
            "type": stype.value,
            "skill": skill.value,
            "result": result.value,
            "status": status,
            "detail": detail,
        })
        print(f"    → {status} {detail}\n")

        if result == SkillResult.FAIL:
            print(f"  [ABORT] STEP {sid} FAILED — stopping dry-run")
            break

    elapsed = time.time() - t_start

    # Summary
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_total = len(results)

    print(f"\n{'='*70}")
    print(f"  RESULTS: {n_pass}/{n_total} PASS, {n_fail} FAIL ({elapsed:.1f}s)")
    print(f"  Snapshots saved: {snap_mgr.saved_steps}")
    print(f"{'='*70}")

    # Test snapshot restore (to STEP 1)
    if snap_mgr.has(1):
        print(f"\n[SNAPSHOT] Testing restore to STEP 1...")
        snap = snap_mgr.restore(
            step_id=1,
            state_0=state,
            fk_state=fk_state,
            fk_model=fk_model,
        )
        print(f"  Restored: finger_l={snap.finger_l:.4f}, finger_r={snap.finger_r:.4f}")
        print(f"  ik_target_l={snap.ik_target_l}")
        print(f"  ik_target_r={snap.ik_target_r}")
        print(f"  clip_status={snap.clip_status}")
        print(f"  [SNAPSHOT] Restore OK")

    # Test restore to mid-point (STEP 20 if available)
    mid_step = 20
    if snap_mgr.has(mid_step):
        print(f"\n[SNAPSHOT] Testing restore to STEP {mid_step}...")
        snap = snap_mgr.restore(
            step_id=mid_step,
            state_0=state,
            fk_state=fk_state,
            fk_model=fk_model,
        )
        print(f"  Restored: finger_l={snap.finger_l:.4f}, finger_r={snap.finger_r:.4f}")
        print(f"  [SNAPSHOT] Restore OK")

    overall = "PASS" if n_fail == 0 else "FAIL"
    print(f"\n[DRY-RUN] Overall: {overall}")
    return n_fail == 0


if __name__ == "__main__":
    success = run_dryrun()
    sys.exit(0 if success else 1)
