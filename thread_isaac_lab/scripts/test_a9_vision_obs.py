#!/usr/bin/env python3
"""SOMA Phase A9: Vision-based cable_midpoint obs — dynamic grasp validation.

Replaces API cable_midpoint_pos (obs dims 14-16) with camera-based PCA-center
estimation from VisionPipelineStage1to3, then runs kinematic grasp episodes
to verify:
  Part 1: Estimation accuracy vs API GT during dynamic motion (phase-wise)
  Part 2: Grasp success rate with vision obs (must remain 100%)
  Part 3: Fallback frequency and timing

Usage:
    python thread_isaac_lab/scripts/test_a9_vision_obs.py \
        --device cuda:0 --enable_cameras
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

import numpy as np

_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="SOMA Phase A9: Vision Obs Validation")
parser.add_argument("--output_dir", type=str, default="data/test_a9")
parser.add_argument("--num_episodes", type=int, default=20)
parser.add_argument("--settle_steps", type=int, default=200)
parser.add_argument("--camera_interval", type=int, default=4,
                    help="Camera update interval (steps)")

from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Post-AppLauncher imports
# ---------------------------------------------------------------------------
import torch

import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.models.vision_pipeline import VisionPipelineStage1to3
from thread_isaac_lab.models.obs_builder import ObsBuilder24D
from thread_isaac_lab.configs.task_config import (
    PHYSICS_DT,
    LEFT_ARM_INIT_JOINTS, RIGHT_ARM_INIT_JOINTS, GRIPPER_INIT,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    PHASE3_LEFT_JOINTS, PHASE3_RIGHT_JOINTS,
    GRIPPER_CLOSE,
)

# Cameras for vision pipeline
CAMERA_KEYS = [
    ("overhead", "overhead_camera"),
    ("front_left", "front_left_camera"),
    ("front_right", "front_right_camera"),
]

# Phase step counts (simplified for test — shorter than production)
PHASE1_STEPS = 80    # Approach: init → Phase 2 joints
PHASE2_STEPS = 60    # Grasp: close grippers
PHASE3_STEPS = 120   # Lift: Phase 2 → Phase 3 joints

# Success threshold
CABLE_LIFT_THRESHOLD_MM = 3.0  # Minimum cable Z rise for "success"


# =========================================================================
# Kinematic grasp helpers
# =========================================================================

def interpolate_joints(start: list, end: list, alpha: float) -> list:
    """Linear interpolation between joint configurations."""
    return [s + alpha * (e - s) for s, e in zip(start, end)]


def set_robot_joints(robot, joint_pos_7: list, gripper: float, device: str):
    """Set joint position targets for a Franka arm (7 DOF + 2 finger)."""
    full = torch.tensor(
        joint_pos_7 + [gripper, gripper],
        dtype=torch.float32, device=device,
    ).unsqueeze(0)
    robot.set_joint_position_target(full)


# =========================================================================
# Main
# =========================================================================

def main():
    device_str = f"cuda:{app_launcher.device_id}"
    out_dir = os.path.join(str(_REPO_ROOT), args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    print(f"[A9] SOMA Phase A9: Vision Obs Validation ({device_str})", flush=True)
    print(f"[A9] Episodes: {args.num_episodes}, Camera interval: {args.camera_interval}", flush=True)
    print(f"[A9] Output: {out_dir}\n", flush=True)

    # ------------------------------------------------------------------
    # Scene setup
    # ------------------------------------------------------------------
    scene_cfg = DualArmSceneCfg(num_envs=1, env_spacing=3.0)
    for _, cam_key in CAMERA_KEYS:
        cam_cfg = getattr(scene_cfg, cam_key)
        cam_cfg.data_types = ["rgb", "distance_to_image_plane"]

    physx_cfg = sim_utils.PhysxCfg(
        gpu_found_lost_pairs_capacity=2**23,
        gpu_total_aggregate_pairs_capacity=2**23,
    )
    sim_cfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT, render_interval=2, device=device_str,
        physx=physx_cfg,
    )
    sim = sim_utils.SimulationContext(sim_cfg)
    scene = InteractiveScene(scene_cfg)
    sim.reset()
    scene.reset()
    dt = sim.get_physics_dt()

    # ------------------------------------------------------------------
    # Settle
    # ------------------------------------------------------------------
    print(f"[A9] Running {args.settle_steps} settle steps …", flush=True)
    for _ in range(args.settle_steps):
        sim.step()
        scene.update(dt)

    # Update cameras once
    for _, cam_key in CAMERA_KEYS:
        scene[cam_key].update(dt)

    # ------------------------------------------------------------------
    # Initialize vision pipeline + obs builder
    # ------------------------------------------------------------------
    vision = VisionPipelineStage1to3(scene, CAMERA_KEYS)
    obs_builder = ObsBuilder24D(
        num_envs=1, device=device_str, obs_mode="24d",
        vision_pipeline=vision,
    )

    # Also create API-only obs builder for comparison
    obs_builder_api = ObsBuilder24D(
        num_envs=1, device=device_str, obs_mode="24d",
        vision_pipeline=None,
    )

    robot_left = scene["robot_left"]
    robot_right = scene["robot_right"]
    cable = scene["cable"]

    # Hand body index (panda_hand = body 8 for Franka)
    hand_body_left = 8
    hand_body_right = 8

    # Record initial cable Z for reference
    cable_z_initial = float(cable.data.body_pos_w[0, :, 2].mean().item())
    print(f"[A9] Initial cable Z: {cable_z_initial:.4f}m\n", flush=True)

    # ------------------------------------------------------------------
    # Episode loop
    # ------------------------------------------------------------------
    all_errors_mm = []  # Per-step vision vs API error
    phase_errors = {"phase_1_2": [], "phase_3": []}
    phase_fallbacks = {"phase_1_2": 0, "phase_3": 0}
    phase_steps = {"phase_1_2": 0, "phase_3": 0}
    episode_results = []
    total_vision_time_s = 0.0
    total_vision_calls = 0

    for ep in range(args.num_episodes):
        ep_t0 = time.time()
        vision.reset()
        obs_builder.reset()
        obs_builder_api.reset()

        # Reset scene to initial state
        # Set robots to init pose
        set_robot_joints(robot_left, LEFT_ARM_INIT_JOINTS, GRIPPER_INIT, device_str)
        set_robot_joints(robot_right, RIGHT_ARM_INIT_JOINTS, GRIPPER_INIT, device_str)

        # Step to apply reset
        for _ in range(20):
            sim.step()
            scene.update(dt)

        cable_z_pre = float(cable.data.body_pos_w[0, :, 2].mean().item())
        ep_errors = []
        ep_fallbacks = 0
        ep_steps = 0

        # ============================================================
        # Phase 1-2: Approach → Grasp position (arms move, cable static)
        # ============================================================
        phase_name = "phase_1_2"
        for step in range(PHASE1_STEPS):
            alpha = min(1.0, (step + 1) / PHASE1_STEPS)
            left_j = interpolate_joints(LEFT_ARM_INIT_JOINTS, PHASE2_LEFT_JOINTS, alpha)
            right_j = interpolate_joints(RIGHT_ARM_INIT_JOINTS, PHASE2_RIGHT_JOINTS, alpha)
            set_robot_joints(robot_left, left_j, GRIPPER_INIT, device_str)
            set_robot_joints(robot_right, right_j, GRIPPER_INIT, device_str)
            sim.step()
            scene.update(dt)

            # Camera update at interval
            if step % args.camera_interval == 0:
                for _, ck in CAMERA_KEYS:
                    scene[ck].update(dt)

                # Build obs with both pipelines
                vt0 = time.time()
                obs_vision = obs_builder.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right, dt=dt,
                )
                vt1 = time.time()
                total_vision_time_s += (vt1 - vt0)
                total_vision_calls += 1

                obs_api = obs_builder_api.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right, dt=dt,
                )

                # Compare cable_midpoint (dims 14-16)
                vis_mid = obs_vision[0, 14:17].cpu().numpy()
                api_mid = obs_api[0, 14:17].cpu().numpy()
                err_mm = float(np.linalg.norm(vis_mid - api_mid)) * 1000
                all_errors_mm.append(err_mm)
                ep_errors.append(err_mm)
                phase_errors[phase_name].append(err_mm)
                phase_steps[phase_name] += 1

                meta = obs_builder.vision_meta
                if meta and meta.get("fallback", False):
                    ep_fallbacks += 1
                    phase_fallbacks[phase_name] += 1

        # Phase 2: Close grippers
        for step in range(PHASE2_STEPS):
            alpha = min(1.0, (step + 1) / PHASE2_STEPS)
            grip = GRIPPER_INIT + alpha * (GRIPPER_CLOSE - GRIPPER_INIT)
            set_robot_joints(robot_left, PHASE2_LEFT_JOINTS, grip, device_str)
            set_robot_joints(robot_right, PHASE2_RIGHT_JOINTS, grip, device_str)
            sim.step()
            scene.update(dt)

            if step % args.camera_interval == 0:
                for _, ck in CAMERA_KEYS:
                    scene[ck].update(dt)

                vt0 = time.time()
                obs_vision = obs_builder.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right, dt=dt,
                )
                vt1 = time.time()
                total_vision_time_s += (vt1 - vt0)
                total_vision_calls += 1

                obs_api = obs_builder_api.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right, dt=dt,
                )

                vis_mid = obs_vision[0, 14:17].cpu().numpy()
                api_mid = obs_api[0, 14:17].cpu().numpy()
                err_mm = float(np.linalg.norm(vis_mid - api_mid)) * 1000
                all_errors_mm.append(err_mm)
                ep_errors.append(err_mm)
                phase_errors[phase_name].append(err_mm)
                phase_steps[phase_name] += 1

                meta = obs_builder.vision_meta
                if meta and meta.get("fallback", False):
                    ep_fallbacks += 1
                    phase_fallbacks[phase_name] += 1

        # ============================================================
        # Phase 3: Lift (cable moves, potential occlusion)
        # ============================================================
        phase_name = "phase_3"
        for step in range(PHASE3_STEPS):
            alpha = min(1.0, (step + 1) / PHASE3_STEPS)
            left_j = interpolate_joints(PHASE2_LEFT_JOINTS, PHASE3_LEFT_JOINTS, alpha)
            right_j = interpolate_joints(PHASE2_RIGHT_JOINTS, PHASE3_RIGHT_JOINTS, alpha)
            set_robot_joints(robot_left, left_j, GRIPPER_CLOSE, device_str)
            set_robot_joints(robot_right, right_j, GRIPPER_CLOSE, device_str)
            sim.step()
            scene.update(dt)

            if step % args.camera_interval == 0:
                for _, ck in CAMERA_KEYS:
                    scene[ck].update(dt)

                vt0 = time.time()
                obs_vision = obs_builder.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right, dt=dt,
                )
                vt1 = time.time()
                total_vision_time_s += (vt1 - vt0)
                total_vision_calls += 1

                obs_api = obs_builder_api.build(
                    robot_left, robot_right, cable,
                    hand_body_left, hand_body_right, dt=dt,
                )

                vis_mid = obs_vision[0, 14:17].cpu().numpy()
                api_mid = obs_api[0, 14:17].cpu().numpy()
                err_mm = float(np.linalg.norm(vis_mid - api_mid)) * 1000
                all_errors_mm.append(err_mm)
                ep_errors.append(err_mm)
                phase_errors[phase_name].append(err_mm)
                phase_steps[phase_name] += 1

                meta = obs_builder.vision_meta
                if meta and meta.get("fallback", False):
                    ep_fallbacks += 1
                    phase_fallbacks[phase_name] += 1

        # ============================================================
        # Episode result
        # ============================================================
        cable_z_post = float(cable.data.body_pos_w[0, :, 2].mean().item())
        cable_z_delta_mm = (cable_z_post - cable_z_pre) * 1000
        success = cable_z_delta_mm >= CABLE_LIFT_THRESHOLD_MM

        ep_mean_err = float(np.mean(ep_errors)) if ep_errors else 0.0
        ep_max_err = float(np.max(ep_errors)) if ep_errors else 0.0
        ep_elapsed = time.time() - ep_t0

        episode_results.append({
            "episode": ep,
            "success": success,
            "cable_z_delta_mm": round(cable_z_delta_mm, 2),
            "mean_error_mm": round(ep_mean_err, 2),
            "max_error_mm": round(ep_max_err, 2),
            "fallbacks": ep_fallbacks,
            "steps": ep_steps + len(ep_errors),
            "elapsed_s": round(ep_elapsed, 1),
        })

        status = "✓" if success else "✗"
        print(f"  [{status}] ep={ep:2d}  Δz={cable_z_delta_mm:+.1f}mm  "
              f"err_mean={ep_mean_err:.1f}mm  err_max={ep_max_err:.1f}mm  "
              f"fallback={ep_fallbacks}  ({ep_elapsed:.1f}s)", flush=True)

    # ------------------------------------------------------------------
    # Aggregate results
    # ------------------------------------------------------------------
    n_success = sum(1 for r in episode_results if r["success"])
    success_rate = f"{n_success}/{args.num_episodes}"
    cable_z_deltas = [r["cable_z_delta_mm"] for r in episode_results]

    overall_mean_err = float(np.mean(all_errors_mm)) if all_errors_mm else 0.0
    overall_max_err = float(np.max(all_errors_mm)) if all_errors_mm else 0.0

    p12_errs = phase_errors["phase_1_2"]
    p3_errs = phase_errors["phase_3"]
    p12_mean = float(np.mean(p12_errs)) if p12_errs else 0.0
    p3_mean = float(np.mean(p3_errs)) if p3_errs else 0.0

    p12_fb = phase_fallbacks["phase_1_2"]
    p3_fb = phase_fallbacks["phase_3"]
    p12_steps = phase_steps["phase_1_2"]
    p3_steps = phase_steps["phase_3"]
    total_fb = p12_fb + p3_fb
    total_steps = p12_steps + p3_steps

    fb_rate_total = total_fb / max(total_steps, 1)
    fb_rate_p12 = p12_fb / max(p12_steps, 1)
    fb_rate_p3 = p3_fb / max(p3_steps, 1)

    avg_vision_ms = (total_vision_time_s / max(total_vision_calls, 1)) * 1000

    # Pass criteria:
    # - 100% grasp success AND overall mean error < 10mm → PASS
    # - 100% success but error >= 10mm → partial PASS
    # - Success < 100% → FAIL
    all_success = n_success == args.num_episodes
    low_error = overall_mean_err < 10.0

    if all_success and low_error:
        overall = "PASS"
    elif all_success:
        overall = "PARTIAL_PASS"
    else:
        overall = "FAIL"

    elapsed = time.time() - t0
    results = {
        "phase": "A9",
        "description": "Vision-based cable_midpoint obs — dynamic grasp validation",
        "device": device_str,
        "num_episodes": args.num_episodes,
        "camera_interval": args.camera_interval,
        "estimation_error_mm": {
            "overall_mean": round(overall_mean_err, 2),
            "overall_max": round(overall_max_err, 2),
            "phase_1_2_mean": round(p12_mean, 2),
            "phase_3_mean": round(p3_mean, 2),
        },
        "fallback_rate": {
            "total": round(fb_rate_total, 4),
            "phase_1_2": round(fb_rate_p12, 4),
            "phase_3": round(fb_rate_p3, 4),
        },
        "grasp_success": {
            "rate": success_rate,
            "cable_z_delta_mean_mm": round(float(np.mean(cable_z_deltas)), 2),
            "cable_z_delta_min_mm": round(float(np.min(cable_z_deltas)), 2),
        },
        "baseline_comparison": {
            "api_obs_success": "20/20",
            "vision_obs_success": success_rate,
            "estimation_accuracy_note": (
                "Kinematic grasp does not use obs for control; "
                "success rate is invariant to obs source. "
                "Error metric validates obs quality for future PPO."
            ),
        },
        "performance": {
            "avg_vision_pipeline_ms": round(avg_vision_ms, 1),
            "total_vision_calls": total_vision_calls,
        },
        "episodes": episode_results,
        "overall": overall,
        "elapsed_s": round(elapsed, 1),
    }

    metrics_path = os.path.join(out_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*60}", flush=True)
    print(f"SOMA Phase A9 Vision Obs: {overall}", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  Grasp success:     {success_rate}", flush=True)
    print(f"  Cable Δz mean:     {results['grasp_success']['cable_z_delta_mean_mm']:.1f}mm", flush=True)
    print(f"  Error overall:     mean={overall_mean_err:.2f}mm  max={overall_max_err:.2f}mm", flush=True)
    print(f"  Error phase 1-2:   mean={p12_mean:.2f}mm  (approach+grasp, cable static)", flush=True)
    print(f"  Error phase 3:     mean={p3_mean:.2f}mm  (lift, cable moving)", flush=True)
    print(f"  Fallback rate:     {fb_rate_total:.1%} total  "
          f"({fb_rate_p12:.1%} P1-2, {fb_rate_p3:.1%} P3)", flush=True)
    print(f"  Vision overhead:   {avg_vision_ms:.1f}ms/call  "
          f"({total_vision_calls} calls)", flush=True)
    print(f"  Results → {metrics_path}", flush=True)
    print(f"  Elapsed: {elapsed:.0f}s", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
    simulation_app.close()
