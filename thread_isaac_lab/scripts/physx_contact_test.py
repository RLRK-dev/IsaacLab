#!/usr/bin/env python3
"""physx_contact_test.py — Minimal reproduction of PhysX N-dependency bug.

Setup: Two kinematic rigid boxes ("fingers") close on a cable resting on a table.
No robot arm — pure PhysX collision test.

Measures:
  - Cable segment Z positions (displacement = contact detected)
  - Contact force via net_forces_w (if available)

Sweeps over PhysX solver configurations to isolate root cause.

Usage:
    python physx_contact_test.py --device cuda:0 --num_envs 1 --headless
    python physx_contact_test.py --device cuda:0 --num_envs 10 --headless
    python physx_contact_test.py --sweep --device cuda:0 --headless
"""

from __future__ import annotations

import argparse
import json
import os
import time

# --- Parse CLI before Isaac Sim init ---
parser = argparse.ArgumentParser(description="PhysX N-dependency contact test")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--settle_steps", type=int, default=500,
                    help="Steps to settle scene before close")
parser.add_argument("--close_steps", type=int, default=200,
                    help="Steps for finger close")
parser.add_argument("--measure_steps", type=int, default=100,
                    help="Steps to measure contact after close")
parser.add_argument("--finger_gap_target", type=float, default=0.014,
                    help="Target gap center-to-center (m). Inner gap = this - 5mm. Cable dia=10mm.")
parser.add_argument("--output_dir", type=str, default="data/physx_contact_tests")

# PhysX overrides
parser.add_argument("--solver_type", type=int, default=1,
                    help="0=PGS, 1=TGS (default)")
parser.add_argument("--pos_iter", type=int, default=32,
                    help="Solver position iterations")
parser.add_argument("--vel_iter", type=int, default=4,
                    help="Solver velocity iterations")
parser.add_argument("--cable_pos_iter", type=int, default=8,
                    help="Cable solver position iterations")
parser.add_argument("--cable_vel_iter", type=int, default=1,
                    help="Cable solver velocity iterations")
parser.add_argument("--enable_ccd", action="store_true", default=False)
parser.add_argument("--contact_last", action="store_true", default=False,
                    help="solve_articulation_contact_last")
parser.add_argument("--contact_offset", type=float, default=None,
                    help="Override contact_offset for fingers+cable (m)")
parser.add_argument("--rest_offset", type=float, default=None,
                    help="Override rest_offset for fingers+cable (m)")
parser.add_argument("--collision_stack_mult", type=int, default=1,
                    help="Multiply gpu_collision_stack_size by this")
parser.add_argument("--enhanced_determinism", action="store_true", default=False)
parser.add_argument("--max_depenetration_vel", type=float, default=5.0,
                    help="Max depenetration velocity (m/s)")

# Sweep mode
parser.add_argument("--sweep", action="store_true", default=False,
                    help="Generate sweep shell script (then exit)")

# Isaac Sim args
from isaaclab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# --- Post-init imports ---
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg, AssetBaseCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.sim import SimulationCfg, PhysxCfg
from isaaclab.sim.spawners import UsdFileCfg
from isaaclab.utils import configclass
from thread_isaac_lab.configs.task_config import PHYSICS_DT

CABLE_USD = "/home/rlrk/IsaacLab/source/extensions/isaaclab_tasks_thread/data/cable/spherical_cable_v17_highdamp.usd"

# Table and cable geometry
TABLE_HEIGHT = 0.75
CABLE_RADIUS = 0.005  # 5mm radius
CABLE_SEG_LEN = 0.06  # 60mm per segment
NUM_CABLE_SEGS = 10

# Finger geometry: thin pads to isolate contact
FINGER_WIDTH = 0.005   # 5mm wide (X, closing direction)
FINGER_DEPTH = 0.02    # 20mm deep (Y, along cable)
FINGER_HEIGHT = 0.04   # 40mm tall (Z)
FINGER_SIZE = (FINGER_WIDTH, FINGER_DEPTH, FINGER_HEIGHT)
FINGER_START_GAP = 0.030  # 30mm center-to-center (inner gap = 25mm >> 10mm cable)


def build_scene_cfg(args) -> InteractiveSceneCfg:
    """Build scene with two kinematic finger-boxes and a cable on a table."""

    collision_props = sim_utils.CollisionPropertiesCfg(collision_enabled=True)
    if args.contact_offset is not None:
        collision_props.contact_offset = args.contact_offset
    if args.rest_offset is not None:
        collision_props.rest_offset = args.rest_offset

    # Cable rests on table at TABLE_HEIGHT. Cable center Z ≈ TABLE_HEIGHT + CABLE_RADIUS.
    # Fingers positioned at cable center height, straddling it.
    cable_center_z = TABLE_HEIGHT + CABLE_RADIUS + 0.002  # small gap for settling
    finger_z = cable_center_z  # fingers at same height as cable center

    # Cable extends in +Y from root position (after -90° X rotation).
    # Place cable root so that middle segment is at Y=0.
    cable_root_y = -NUM_CABLE_SEGS / 2 * CABLE_SEG_LEN  # ≈ -0.30

    @configclass
    class ContactTestSceneCfg(InteractiveSceneCfg):
        num_envs: int = args.num_envs
        env_spacing: float = 3.0

        ground = AssetBaseCfg(
            prim_path="/World/ground",
            spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
        )

        dome_light = AssetBaseCfg(
            prim_path="/World/DomeLight",
            spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0)),
        )

        # Table for cable support
        table: RigidObjectCfg = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/Table",
            spawn=sim_utils.CuboidCfg(
                size=(1.0, 1.0, 0.02),
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True, disable_gravity=True,
                ),
                collision_props=sim_utils.CollisionPropertiesCfg(collision_enabled=True),
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.0, dynamic_friction=1.0, restitution=0.0,
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(0.0, 0.0, TABLE_HEIGHT - 0.01),
            ),
        )

        # Left finger (kinematic box)
        finger_left: RigidObjectCfg = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/FingerLeft",
            spawn=sim_utils.CuboidCfg(
                size=FINGER_SIZE,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True, disable_gravity=True,
                ),
                collision_props=collision_props,
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.0, dynamic_friction=1.0, restitution=0.0,
                ),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.8, 0.2, 0.2),
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(-FINGER_START_GAP / 2, 0.0, finger_z),
            ),
        )

        # Right finger (kinematic box)
        finger_right: RigidObjectCfg = RigidObjectCfg(
            prim_path="{ENV_REGEX_NS}/FingerRight",
            spawn=sim_utils.CuboidCfg(
                size=FINGER_SIZE,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    kinematic_enabled=True, disable_gravity=True,
                ),
                collision_props=collision_props,
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.0, dynamic_friction=1.0, restitution=0.0,
                ),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.2, 0.2, 0.8),
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=(FINGER_START_GAP / 2, 0.0, finger_z),
            ),
        )

        # Cable
        cable: ArticulationCfg = ArticulationCfg(
            prim_path="{ENV_REGEX_NS}/Cable",
            spawn=UsdFileCfg(
                usd_path=CABLE_USD,
                activate_contact_sensors=False,
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                    enabled_self_collisions=False,
                    solver_position_iteration_count=args.cable_pos_iter,
                    solver_velocity_iteration_count=args.cable_vel_iter,
                ),
            ),
            init_state=ArticulationCfg.InitialStateCfg(
                pos=(0.0, cable_root_y, TABLE_HEIGHT + 0.02),
                rot=(0.7071, -0.7071, 0.0, 0.0),  # -90° X (extends in +Y)
            ),
            actuators={
                "cable_joints": ImplicitActuatorCfg(
                    joint_names_expr=[".*"],
                    stiffness=0.0, damping=5.0,
                ),
            },
        )

    return ContactTestSceneCfg()


def run_test(args, label: str = "default") -> dict:
    """Run a single contact test. Returns results dict."""

    device = f"cuda:{app_launcher.device_id}" if app_launcher.device_id >= 0 else "cpu"
    N = args.num_envs

    print(f"\n{'='*70}")
    print(f"PhysX Contact Test: {label}")
    print(f"  N={N}, solver={['PGS','TGS'][args.solver_type]}, "
          f"pos_iter={args.pos_iter}, vel_iter={args.vel_iter}")
    print(f"  cable_pos_iter={args.cable_pos_iter}, cable_vel_iter={args.cable_vel_iter}")
    print(f"  CCD={args.enable_ccd}, contact_last={args.contact_last}")
    print(f"  contact_offset={args.contact_offset}, rest_offset={args.rest_offset}")
    print(f"  enhanced_determinism={args.enhanced_determinism}")
    print(f"  max_depenetration_vel={args.max_depenetration_vel}")
    print(f"  device={device}")
    print(f"{'='*70}")

    sim_cfg = SimulationCfg(
        device=device,
        dt=PHYSICS_DT,
        render_interval=1,
        physx=PhysxCfg(
            solver_type=args.solver_type,
            enable_ccd=args.enable_ccd,
            enable_enhanced_determinism=args.enhanced_determinism,
            solve_articulation_contact_last=args.contact_last,
            gpu_collision_stack_size=2**26 * args.collision_stack_mult,
        ),
    )
    sim = sim_utils.SimulationContext(sim_cfg)

    scene_cfg = build_scene_cfg(args)
    scene = InteractiveScene(scene_cfg)

    sim.reset()
    scene.reset()

    cable: Articulation = scene["cable"]
    finger_left: RigidObject = scene["finger_left"]
    finger_right: RigidObject = scene["finger_right"]

    env_origins = scene.env_origins  # (N, 3)

    # --- Phase 0: Verify positions ---
    print(f"\n--- Phase 0: Verify positions ---")
    cable_pos = cable.data.body_pos_w[:, :, :3]  # (N, num_seg, 3)
    num_seg = cable_pos.shape[1]
    mid_seg = num_seg // 2

    lf_pos = finger_left.data.body_pos_w[:, 0, :3]  # (N, 3)
    rf_pos = finger_right.data.body_pos_w[:, 0, :3]  # (N, 3)
    cable_mid = cable_pos[:, mid_seg, :]  # (N, 3)

    for i in range(min(N, 3)):
        print(f"  env{i}: L_finger=({lf_pos[i,0]:.4f}, {lf_pos[i,1]:.4f}, {lf_pos[i,2]:.4f}) "
              f"R_finger=({rf_pos[i,0]:.4f}, {rf_pos[i,1]:.4f}, {rf_pos[i,2]:.4f}) "
              f"cable_mid=({cable_mid[i,0]:.4f}, {cable_mid[i,1]:.4f}, {cable_mid[i,2]:.4f})")
    # Print all segment positions for env0
    if N >= 1:
        print(f"  Cable segments env0 (X, Y, Z):")
        for s in range(num_seg):
            sp = cable_pos[0, s]
            print(f"    seg{s}: ({sp[0]:.4f}, {sp[1]:.4f}, {sp[2]:.4f})")

    # --- Phase 1: Settle (cable rests on table, fingers open) ---
    print(f"\n--- Phase 1: Settle ({args.settle_steps} steps) ---")
    for step in range(args.settle_steps):
        sim.step()
        scene.update(sim_cfg.dt)

    # Record baseline
    cable_z_initial = cable.data.body_pos_w[:, :, 2].clone()  # (N, num_seg)
    lf_pos = finger_left.data.body_pos_w[:, 0, :3]
    rf_pos = finger_right.data.body_pos_w[:, 0, :3]
    cable_mid = cable.data.body_pos_w[:, mid_seg, :]
    finger_gap = (rf_pos[:, 0] - lf_pos[:, 0])  # X-axis gap (N,)

    print(f"  Cable Z (mean per env): {[f'{z:.4f}' for z in cable_z_initial.mean(dim=1).tolist()]}")
    print(f"  Finger gap: {[f'{g*1000:.1f}mm' for g in finger_gap.tolist()]}")
    for i in range(min(N, 3)):
        print(f"  env{i}: cable_mid=({cable_mid[i,0]:.4f}, {cable_mid[i,1]:.4f}, {cable_mid[i,2]:.4f}) "
              f"L_finger_x={lf_pos[i,0]:.4f} R_finger_x={rf_pos[i,0]:.4f}")

    # --- Phase 2: Close fingers (kinematic move toward each other) ---
    inner_start = FINGER_START_GAP - FINGER_WIDTH
    inner_target = args.finger_gap_target - FINGER_WIDTH
    print(f"\n--- Phase 2: Close fingers ({args.close_steps} steps) ---")
    print(f"  Center gap: {FINGER_START_GAP*1000:.0f}→{args.finger_gap_target*1000:.1f}mm")
    print(f"  Inner gap:  {inner_start*1000:.0f}→{inner_target*1000:.1f}mm (cable dia=10mm)")

    close_log = []
    start_half_gap = FINGER_START_GAP / 2
    target_half_gap = args.finger_gap_target / 2

    for step in range(args.close_steps):
        # Linear interpolation: reach target at 80% of steps
        t = min(1.0, (step + 1) / (args.close_steps * 0.8))
        half_gap = start_half_gap + (target_half_gap - start_half_gap) * t

        # Move fingers kinematically
        lf_target = finger_left.data.root_pos_w.clone()
        rf_target = finger_right.data.root_pos_w.clone()

        # Fingers close in X direction (left moves +X, right moves -X)
        # Use env_origins as base reference
        lf_target[:, 0] = env_origins[:, 0] - half_gap
        rf_target[:, 0] = env_origins[:, 0] + half_gap

        finger_left.write_root_pose_to_sim(
            torch.cat([lf_target, finger_left.data.root_quat_w], dim=-1))
        finger_right.write_root_pose_to_sim(
            torch.cat([rf_target, finger_right.data.root_quat_w], dim=-1))

        sim.step()
        scene.update(sim_cfg.dt)

        # Check for NaN (cable explosion)
        cable_z_now = cable.data.body_pos_w[:, :, 2]
        if torch.isnan(cable_z_now).any():
            print(f"  *** CABLE NaN at step {step}! gap={half_gap*2*1000:.1f}mm ***")
            break

        if step % 20 == 0 or step == args.close_steps - 1:
            fp_l = finger_left.data.body_pos_w[:, 0, 0]
            fp_r = finger_right.data.body_pos_w[:, 0, 0]
            fg = fp_r - fp_l  # (N,)
            cz_delta = (cable_z_now - cable_z_initial).abs().max(dim=1).values

            record = {
                "step": step,
                "half_gap": float(half_gap),
                "finger_gap_mm": (fg * 1000).tolist(),
                "cable_dz_max_mm": (cz_delta * 1000).tolist(),
            }
            close_log.append(record)
            if N <= 4:
                inner_gap = fg - FINGER_WIDTH
                print(f"  step={step:3d} inner_gap={[f'{g*1000:.1f}mm' for g in inner_gap.tolist()]} "
                      f"cable_dz_max={[f'{d:.2f}mm' for d in (cz_delta*1000).tolist()]}")

    # --- Phase 3: Hold and measure ---
    print(f"\n--- Phase 3: Hold closed ({args.measure_steps} steps) ---")
    for step in range(args.measure_steps):
        # Hold fingers at target position
        lf_target = finger_left.data.root_pos_w.clone()
        rf_target = finger_right.data.root_pos_w.clone()
        lf_target[:, 0] = env_origins[:, 0] - target_half_gap
        rf_target[:, 0] = env_origins[:, 0] + target_half_gap
        finger_left.write_root_pose_to_sim(
            torch.cat([lf_target, finger_left.data.root_quat_w], dim=-1))
        finger_right.write_root_pose_to_sim(
            torch.cat([rf_target, finger_right.data.root_quat_w], dim=-1))
        sim.step()
        scene.update(sim_cfg.dt)

    # --- Final measurements ---
    cable_z_final = cable.data.body_pos_w[:, :, 2].clone()
    cable_z_delta = (cable_z_final - cable_z_initial)  # (N, num_seg)
    cable_z_delta_mean = cable_z_delta.mean(dim=1)
    cable_z_delta_max = cable_z_delta.abs().max(dim=1).values

    # Contact detected = cable displaced > 0.5mm in any segment
    contact_detected = cable_z_delta.abs().max(dim=1).values > 0.0005

    # Also check X displacement (fingers push cable in X)
    cable_x_initial = cable.data.body_pos_w[:, :, 0].clone()
    # Re-read: we didn't save initial X. Use cable_z_initial's shape for reference.
    # Actually let's measure cable X displacement from initial cable root X = 0
    cable_x_final = cable.data.body_pos_w[:, :, 0]
    # Cable should be at X≈0 (env_origin X). Any X displacement = finger contact
    cable_x_offset = (cable_x_final - env_origins[:, 0:1]).abs()  # (N, num_seg)
    cable_x_max = cable_x_offset.max(dim=1).values

    # Final finger positions
    fp_l_final = finger_left.data.body_pos_w[:, 0, :]
    fp_r_final = finger_right.data.body_pos_w[:, 0, :]
    finger_gap_final = fp_r_final[:, 0] - fp_l_final[:, 0]

    print(f"\n{'='*70}")
    print(f"RESULTS: {label}")
    print(f"{'='*70}")
    for env_id in range(min(N, 10)):
        print(f"  env={env_id}: "
              f"gap={finger_gap_final[env_id]*1000:.1f}mm "
              f"cable_dz_mean={cable_z_delta_mean[env_id]*1000:.2f}mm "
              f"cable_dz_max={cable_z_delta_max[env_id]*1000:.2f}mm "
              f"cable_x_max={cable_x_max[env_id]*1000:.2f}mm "
              f"contact={'YES' if contact_detected[env_id] else 'NO'}")
        if N <= 4:
            segs = cable_z_delta[env_id] * 1000
            print(f"         seg_dz(mm): {[f'{s:.2f}' for s in segs.tolist()]}")

    n_contact = contact_detected.sum().item()
    print(f"\n  CONTACT: {n_contact}/{N} envs | "
          f"mean_dz={cable_z_delta_mean.mean()*1000:.2f}mm | "
          f"mean_gap={finger_gap_final.mean()*1000:.1f}mm")

    results = {
        "label": label,
        "num_envs": N,
        "device": device,
        "solver_type": ["PGS", "TGS"][args.solver_type],
        "pos_iter": args.pos_iter,
        "vel_iter": args.vel_iter,
        "cable_pos_iter": args.cable_pos_iter,
        "cable_vel_iter": args.cable_vel_iter,
        "enable_ccd": args.enable_ccd,
        "contact_last": args.contact_last,
        "contact_offset": args.contact_offset,
        "rest_offset": args.rest_offset,
        "enhanced_determinism": args.enhanced_determinism,
        "max_depenetration_vel": args.max_depenetration_vel,
        "collision_stack_mult": args.collision_stack_mult,
        "finger_gap_target": args.finger_gap_target,
        "settle_steps": args.settle_steps,
        "close_steps": args.close_steps,
        "measure_steps": args.measure_steps,
        "per_env": [],
    }

    for env_id in range(N):
        results["per_env"].append({
            "env_id": env_id,
            "finger_gap_final_mm": float(finger_gap_final[env_id] * 1000),
            "cable_z_delta_mean_mm": float(cable_z_delta_mean[env_id] * 1000),
            "cable_z_delta_max_mm": float(cable_z_delta_max[env_id] * 1000),
            "cable_x_max_mm": float(cable_x_max[env_id] * 1000),
            "cable_seg_dz_mm": (cable_z_delta[env_id] * 1000).tolist(),
            "contact_detected": bool(contact_detected[env_id]),
        })

    results["summary"] = {
        "contact_count": n_contact,
        "contact_ratio": n_contact / N,
        "mean_cable_dz_mm": float(cable_z_delta_mean.mean() * 1000),
        "mean_cable_x_max_mm": float(cable_x_max.mean() * 1000),
        "mean_finger_gap_mm": float(finger_gap_final.mean() * 1000),
    }
    results["close_log"] = close_log

    # Cleanup
    sim.clear_all_callbacks()
    sim.clear_instance()

    return results


def run_sweep(args):
    """Generate sweep shell script."""

    sweep_configs = [
        # 1. Baseline: TGS, N=1 vs N=2 vs N=10
        {"label": "TGS_default_N1", "num_envs": 1},
        {"label": "TGS_default_N2", "num_envs": 2},
        {"label": "TGS_default_N4", "num_envs": 4},
        {"label": "TGS_default_N10", "num_envs": 10},

        # 2. solve_articulation_contact_last
        {"label": "TGS_CL_N1", "num_envs": 1, "contact_last": True},
        {"label": "TGS_CL_N10", "num_envs": 10, "contact_last": True},

        # 3. PGS solver
        {"label": "PGS_default_N1", "num_envs": 1, "solver_type": 0},
        {"label": "PGS_default_N10", "num_envs": 10, "solver_type": 0},

        # 4. High cable iterations
        {"label": "TGS_highcable_N1", "num_envs": 1,
         "cable_pos_iter": 32, "cable_vel_iter": 4},
        {"label": "TGS_highcable_N10", "num_envs": 10,
         "cable_pos_iter": 32, "cable_vel_iter": 4},

        # 5. CCD
        {"label": "TGS_CCD_N1", "num_envs": 1, "enable_ccd": True},
        {"label": "TGS_CCD_N10", "num_envs": 10, "enable_ccd": True},

        # 6. Contact offset
        {"label": "TGS_co5mm_N1", "num_envs": 1,
         "contact_offset": 0.005, "rest_offset": 0.002},
        {"label": "TGS_co5mm_N10", "num_envs": 10,
         "contact_offset": 0.005, "rest_offset": 0.002},

        # 7. Enhanced determinism
        {"label": "TGS_det_N1", "num_envs": 1, "enhanced_determinism": True},
        {"label": "TGS_det_N10", "num_envs": 10, "enhanced_determinism": True},

        # 8. Stack size x4
        {"label": "TGS_stack4x_N1", "num_envs": 1, "collision_stack_mult": 4},
        {"label": "TGS_stack4x_N10", "num_envs": 10, "collision_stack_mult": 4},

        # 9. Combined best
        {"label": "TGS_combined_N1", "num_envs": 1,
         "cable_pos_iter": 32, "cable_vel_iter": 4,
         "enable_ccd": True, "contact_last": True,
         "contact_offset": 0.005, "rest_offset": 0.002},
        {"label": "TGS_combined_N10", "num_envs": 10,
         "cable_pos_iter": 32, "cable_vel_iter": 4,
         "enable_ccd": True, "contact_last": True,
         "contact_offset": 0.005, "rest_offset": 0.002},

        # 10. Max depenetration vel 100
        {"label": "TGS_depen100_N1", "num_envs": 1, "max_depenetration_vel": 100.0},
        {"label": "TGS_depen100_N10", "num_envs": 10, "max_depenetration_vel": 100.0},
    ]

    script_path = os.path.join(args.output_dir, "run_sweep.sh")
    os.makedirs(args.output_dir, exist_ok=True)

    lines = ["#!/bin/bash",
             "# Auto-generated PhysX contact sweep",
             f"# {len(sweep_configs)} configurations",
             "set -e",
             "source env_isaaclab/bin/activate",
             ""]

    for cfg in sweep_configs:
        cmd_parts = [
            "PYTHONUNBUFFERED=1 python -u",
            "thread_isaac_lab/scripts/physx_contact_test.py",
            "--headless",
            f"--device {args.device}",
            f"--num_envs {cfg['num_envs']}",
            f"--solver_type {cfg.get('solver_type', 1)}",
            f"--pos_iter {cfg.get('pos_iter', 32)}",
            f"--vel_iter {cfg.get('vel_iter', 4)}",
            f"--cable_pos_iter {cfg.get('cable_pos_iter', 8)}",
            f"--cable_vel_iter {cfg.get('cable_vel_iter', 1)}",
            f"--output_dir {args.output_dir}",
        ]
        if cfg.get("enable_ccd"):
            cmd_parts.append("--enable_ccd")
        if cfg.get("contact_last"):
            cmd_parts.append("--contact_last")
        if cfg.get("enhanced_determinism"):
            cmd_parts.append("--enhanced_determinism")
        if cfg.get("contact_offset") is not None:
            cmd_parts.append(f"--contact_offset {cfg['contact_offset']}")
        if cfg.get("rest_offset") is not None:
            cmd_parts.append(f"--rest_offset {cfg['rest_offset']}")
        if cfg.get("collision_stack_mult", 1) > 1:
            cmd_parts.append(f"--collision_stack_mult {cfg['collision_stack_mult']}")
        if cfg.get("max_depenetration_vel", 5.0) != 5.0:
            cmd_parts.append(f"--max_depenetration_vel {cfg['max_depenetration_vel']}")

        cmd = " ".join(cmd_parts)
        lines.append(f'echo "\\n=== {cfg["label"]} ==="')
        lines.append(cmd)
        lines.append("")

    with open(script_path, "w") as f:
        f.write("\n".join(lines))
    os.chmod(script_path, 0o755)

    print(f"\nSweep script generated: {script_path}")
    print(f"  {len(sweep_configs)} configurations")
    print(f"  Run: bash {script_path}")

    return sweep_configs


def main():
    os.makedirs(args.output_dir, exist_ok=True)

    if args.sweep:
        run_sweep(args)
        return

    label = (f"{'PGS' if args.solver_type == 0 else 'TGS'}"
             f"_pi{args.pos_iter}_vi{args.vel_iter}"
             f"_cpi{args.cable_pos_iter}_cvi{args.cable_vel_iter}"
             f"_N{args.num_envs}")
    if args.enable_ccd:
        label += "_CCD"
    if args.contact_last:
        label += "_CL"
    if args.contact_offset is not None:
        label += f"_co{int(args.contact_offset*1000)}mm"
    if args.enhanced_determinism:
        label += "_det"

    t0 = time.time()
    results = run_test(args, label=label)
    elapsed = time.time() - t0
    results["elapsed_s"] = elapsed

    out_path = os.path.join(args.output_dir, f"{label}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {out_path} ({elapsed:.1f}s)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFATAL ERROR: {e}")
    finally:
        simulation_app.close()
