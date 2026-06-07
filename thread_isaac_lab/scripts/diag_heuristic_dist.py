#!/usr/bin/env python3
"""diag_heuristic_dist.py -- Measure heuristic coarse approach distances.

Runs 4 seeds × 10 targets = 40 episodes with ONLY the heuristic coarse
approach (no RL), measuring post-approach fingertip-to-target distances.

Reports per-episode distances, phase transition info, and statistics.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from datetime import datetime

import numpy as np

_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# CLI (before AppLauncher)
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Diagnose heuristic coarse approach distances.")
parser.add_argument("--num_envs", type=int, default=32)
parser.add_argument("--eval_seeds", type=int, nargs="+", default=[101, 102, 103, 104])
parser.add_argument("--eval_targets", type=int, default=10)
parser.add_argument("--env_spacing", type=float, default=3.0)
parser.add_argument("--output_dir", type=str, default="")

from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Post-AppLauncher imports
# ---------------------------------------------------------------------------

import torch
import isaaclab.sim as sim_utils
from isaaclab.scene import InteractiveScene
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.utils import configclass

from thread_isaac_lab.envs.dual_arm_cfg import DualArmSceneCfg
from thread_isaac_lab.scripts.dual_arm_ik_utils import (
from thread_isaac_lab.configs.task_config import PHYSICS_DT
    BASE_QUAT, BASE_X, BASE_Z,
    BENT_JOINTS,
    DUAL_LEFT_BASE_Y, DUAL_RIGHT_BASE_Y,
    FINGERTIP_OFFSET, GRIPPER_OPEN,
    apply_joints_batch,
    check_arm_separation_batch,
    compute_dual_targets_batch,
    ee_to_fingertip_batch,
    fingertip_to_ee_batch,
    jt_ik_step_6dof_batch,
    make_targets_per_env,
)

# ---------------------------------------------------------------------------
# Constants (same as train_fine_rl.py)
# ---------------------------------------------------------------------------

COARSE_DIST_M = 0.10
HEUR_JT_ALPHA = 10.0
HEUR_JT_ALPHA_ORI = 3.0
HEUR_ORI_ENABLE_DIST = 0.10
HEUR_CLIP_RAD = 0.02
HEUR_HOLD_STEPS = 96
HEUR_TRANS_DELTA_CLIP = 0.05
HEUR_APPROACH_SLOWDOWN = 0.10
HEUR_COLLISION_MIN_DIST = 0.15
STANDOFF_DIST_Y = 0.15

# ---------------------------------------------------------------------------
# Minimal DirectRLEnv for diagnostics (no RL, just scene + heuristic)
# ---------------------------------------------------------------------------

@configclass
class DiagEnvCfg(DirectRLEnvCfg):
    decimation: int = 16
    episode_length_s: float = 10.0
    observation_space: int = 12
    action_space: int = 6
    sim: sim_utils.SimulationCfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT,
        render_interval=16,
    )
    scene: DualArmSceneCfg = DualArmSceneCfg(num_envs=32, env_spacing=3.0)


class DiagEnv(DirectRLEnv):
    """Minimal env for heuristic diagnostics -- no RL stepping needed."""

    cfg: DiagEnvCfg

    def __init__(self, cfg: DiagEnvCfg, **kwargs):
        super().__init__(cfg, **kwargs)

        N = self.num_envs
        dev = self.device

        self.robot_left = self.scene["robot_left"]
        self.robot_right = self.scene["robot_right"]

        self._relocate_robot_bases()

        self._hand_body_left, _ = self.robot_left.find_bodies("panda_hand")
        self._hand_body_left = self._hand_body_left[0]
        self._hand_body_right, _ = self.robot_right.find_bodies("panda_hand")
        self._hand_body_right = self._hand_body_right[0]
        self._jac_body_left = self._hand_body_left - 1
        self._jac_body_right = self._hand_body_right - 1

        self._ball_pos = torch.zeros(N, 3, device=dev)
        self._left_ft_target = torch.zeros(N, 3, device=dev)
        self._right_ft_target = torch.zeros(N, 3, device=dev)
        self._actions = torch.zeros(N, 6, device=dev)

        print(f"[DIAG] Initialized: {N} envs, device={dev}")
        print(f"[DIAG] IK bodies: L_hand={self._hand_body_left} R_hand={self._hand_body_right}")

    def _relocate_robot_bases(self):
        N = self.num_envs
        dev = self.device

        left_pose = torch.zeros(N, 7, dtype=torch.float32, device=dev)
        left_pose[:, 0] = BASE_X
        left_pose[:, 1] = DUAL_LEFT_BASE_Y
        left_pose[:, 2] = BASE_Z
        left_pose[:, 3:7] = torch.tensor(BASE_QUAT, device=dev)

        right_pose = torch.zeros(N, 7, dtype=torch.float32, device=dev)
        right_pose[:, 0] = BASE_X
        right_pose[:, 1] = DUAL_RIGHT_BASE_Y
        right_pose[:, 2] = BASE_Z
        right_pose[:, 3:7] = torch.tensor(BASE_QUAT, device=dev)

        self.robot_left.write_root_pose_to_sim(left_pose)
        self.robot_right.write_root_pose_to_sim(right_pose)

        print("[DIAG] Relocating robot bases and settling (50 steps)...")
        for i in range(50):
            self.scene.write_data_to_sim()
            self.sim.step(render=False)
            self.scene.update(dt=self.physics_dt)
        print("[DIAG] Base positions settled.")

    def _setup_scene(self):
        pass

    def _pre_physics_step(self, actions):
        self._actions = actions

    def _apply_action(self):
        pass

    def _get_observations(self):
        return {"policy": torch.zeros(self.num_envs, 12, device=self.device)}

    def _get_rewards(self):
        return torch.zeros(self.num_envs, device=self.device)

    def _get_dones(self):
        return torch.zeros(self.num_envs, dtype=torch.bool, device=self.device), \
               torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

    def _reset_idx(self, env_ids):
        pass

    def teleport_to_bent_elbow(self, env_ids: torch.Tensor):
        bent = torch.tensor(BENT_JOINTS, device=self.device, dtype=torch.float32)
        for robot in [self.robot_left, self.robot_right]:
            pos = robot.data.joint_pos.clone()
            vel = robot.data.joint_vel.clone()
            pos[env_ids, :7] = bent
            pos[env_ids, 7] = GRIPPER_OPEN
            pos[env_ids, 8] = GRIPPER_OPEN
            vel[env_ids] = 0.0
            robot.write_joint_state_to_sim(pos, vel)

    def settle_physics(self, steps: int):
        for i in range(steps):
            self.scene.write_data_to_sim()
            self.sim.step(render=False)
            self.scene.update(dt=self.physics_dt)


# ---------------------------------------------------------------------------
# Heuristic with detailed logging
# ---------------------------------------------------------------------------

def run_heuristic_with_logging(env: DiagEnv, env_ids: torch.Tensor):
    """Run heuristic and return detailed diagnostics."""
    N = env.num_envs
    dev = env.device
    max_macros = 80
    target_dist = COARSE_DIST_M

    phase = torch.zeros(N, dtype=torch.long, device=dev)
    phase[:] = 2
    phase[env_ids] = 0

    left_standoff_ft = env._ball_pos.clone()
    left_standoff_ft[:, 1] -= STANDOFF_DIST_Y

    right_hold_ft = torch.zeros(N, 3, device=dev)

    phase_ab_macro = -1
    total_macros = 0
    dist_l_at_ab = -1.0
    dist_r_at_ab = -1.0

    for macro in range(max_macros):
        in_phase_a = (phase == 0)
        in_phase_b = (phase == 1)
        active = in_phase_a | in_phase_b

        if not active.any():
            break

        total_macros = macro + 1

        ee_pos_l = env.robot_left.data.body_pose_w[:, env._hand_body_left, :3]
        ee_quat_l = env.robot_left.data.body_quat_w[:, env._hand_body_left, :]
        ee_pos_r = env.robot_right.data.body_pose_w[:, env._hand_body_right, :3]
        ee_quat_r = env.robot_right.data.body_quat_w[:, env._hand_body_right, :]

        ft_l = ee_to_fingertip_batch(ee_pos_l, ee_quat_l)
        ft_r = ee_to_fingertip_batch(ee_pos_r, ee_quat_r)

        # Phase A → B: right FT reaches target
        right_ft_err = torch.norm(ft_r - env._right_ft_target, dim=-1)
        phase_a_done = in_phase_a & (right_ft_err < target_dist)
        if phase_a_done.any() and phase_ab_macro == -1:
            phase_ab_macro = macro
            left_ft_err_at_ab = torch.norm(ft_l - env._left_ft_target, dim=-1)
            dist_l_at_ab = left_ft_err_at_ab[0].item()
            dist_r_at_ab = right_ft_err[0].item()
        if phase_a_done.any():
            phase[phase_a_done] = 1
            right_hold_ft[phase_a_done] = ft_r[phase_a_done].clone()

        # Phase B → done: left FT reaches target
        left_ft_err = torch.norm(ft_l - env._left_ft_target, dim=-1)
        phase_b_done = in_phase_b & (left_ft_err < target_dist)
        if phase_b_done.any():
            phase[phase_b_done] = 2

        in_phase_a = (phase == 0)
        in_phase_b = (phase == 1)
        active = in_phase_a | in_phase_b

        if not active.any():
            break

        # Compute FT command targets
        left_ft_cmd = torch.where(
            in_phase_a.unsqueeze(-1).expand_as(left_standoff_ft),
            left_standoff_ft, env._left_ft_target,
        )
        right_ft_cmd = torch.where(
            in_phase_a.unsqueeze(-1).expand_as(env._right_ft_target),
            env._right_ft_target, right_hold_ft,
        )

        ee_target_l = fingertip_to_ee_batch(left_ft_cmd, ee_quat_l)
        ee_target_r = fingertip_to_ee_batch(right_ft_cmd, ee_quat_r)

        delta_l = (ee_target_l - ee_pos_l).clamp(-HEUR_TRANS_DELTA_CLIP, HEUR_TRANS_DELTA_CLIP)
        delta_r = (ee_target_r - ee_pos_r).clamp(-HEUR_TRANS_DELTA_CLIP, HEUR_TRANS_DELTA_CLIP)

        # Slowdown
        left_ft_err_cmd = torch.norm(left_ft_cmd - ft_l, dim=-1)
        right_ft_err_cmd = torch.norm(right_ft_cmd - ft_r, dim=-1)
        slow_l = (left_ft_err_cmd < HEUR_APPROACH_SLOWDOWN).unsqueeze(-1)
        slow_r = (right_ft_err_cmd < HEUR_APPROACH_SLOWDOWN).unsqueeze(-1)
        delta_l = torch.where(slow_l.expand_as(delta_l), delta_l * 0.5, delta_l)
        delta_r = torch.where(slow_r.expand_as(delta_r), delta_r * 0.5, delta_r)

        # Collision avoidance
        _, col_scale = check_arm_separation_batch(ee_pos_l, ee_pos_r, HEUR_COLLISION_MIN_DIST)
        col_scale_3d = col_scale.unsqueeze(-1)
        delta_l = delta_l * col_scale_3d
        delta_r = delta_r * col_scale_3d

        cmd_l = ee_pos_l + delta_l
        cmd_r = ee_pos_r + delta_r

        left_ori_mask = in_phase_b
        right_ori_mask = in_phase_a | in_phase_b

        # Inner IK loop
        for _ in range(HEUR_HOLD_STEPS):
            ik_l, nan_l = jt_ik_step_6dof_batch(
                env.robot_left, env._jac_body_left, env._hand_body_left,
                cmd_l, env._ball_pos, left_ori_mask,
                HEUR_JT_ALPHA, HEUR_JT_ALPHA_ORI, HEUR_ORI_ENABLE_DIST,
                HEUR_CLIP_RAD, dev,
            )
            if ik_l is not None:
                apply_joints_batch(env.robot_left, ik_l, active & ~nan_l)
            ik_r, nan_r = jt_ik_step_6dof_batch(
                env.robot_right, env._jac_body_right, env._hand_body_right,
                cmd_r, env._ball_pos, right_ori_mask,
                HEUR_JT_ALPHA, HEUR_JT_ALPHA_ORI, HEUR_ORI_ENABLE_DIST,
                HEUR_CLIP_RAD, dev,
            )
            if ik_r is not None:
                apply_joints_batch(env.robot_right, ik_r, active & ~nan_r)

            env.scene.write_data_to_sim()
            env.sim.step(render=False)
            env.scene.update(dt=env.physics_dt)

    # Final distances (env 0)
    ee_pos_l = env.robot_left.data.body_pose_w[0, env._hand_body_left, :3]
    ee_quat_l = env.robot_left.data.body_quat_w[0, env._hand_body_left, :]
    ee_pos_r = env.robot_right.data.body_pose_w[0, env._hand_body_right, :3]
    ee_quat_r = env.robot_right.data.body_quat_w[0, env._hand_body_right, :]

    ft_l = ee_to_fingertip_batch(ee_pos_l.unsqueeze(0), ee_quat_l.unsqueeze(0))[0]
    ft_r = ee_to_fingertip_batch(ee_pos_r.unsqueeze(0), ee_quat_r.unsqueeze(0))[0]

    final_dist_l = torch.norm(ft_l - env._left_ft_target[0]).item()
    final_dist_r = torch.norm(ft_r - env._right_ft_target[0]).item()

    err_l = (ft_l - env._left_ft_target[0]).cpu().numpy()
    err_r = (ft_r - env._right_ft_target[0]).cpu().numpy()

    # Also read final FT positions for debugging
    ft_l_pos = ft_l.cpu().numpy()
    ft_r_pos = ft_r.cpu().numpy()

    return {
        "phase_ab_macro": phase_ab_macro,
        "total_macros": total_macros,
        "final_dist_l": final_dist_l,
        "final_dist_r": final_dist_r,
        "dist_l_at_ab": dist_l_at_ab,
        "dist_r_at_ab": dist_r_at_ab,
        "err_l_xyz": err_l.tolist(),
        "err_r_xyz": err_r.tolist(),
        "final_ft_l": ft_l_pos.tolist(),
        "final_ft_r": ft_r_pos.tolist(),
        "final_phase": int(phase[0].item()),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    N = args.num_envs
    dev_str = f"cuda:{app_launcher.device_id}"

    if args.output_dir:
        output_dir = args.output_dir
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = str(_REPO_ROOT / "data" / f"diag_heuristic_{ts}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"[DIAG] Output: {output_dir}")
    print(f"[DIAG] Device: {dev_str}")
    print(f"[DIAG] num_envs={N}")

    env_cfg = DiagEnvCfg()
    env_cfg.scene.num_envs = N
    env_cfg.scene.env_spacing = args.env_spacing
    env_cfg.sim.device = dev_str

    # Disable cameras
    env_cfg.scene.front_left_camera = None
    env_cfg.scene.front_right_camera = None
    env_cfg.scene.back_camera = None
    env_cfg.scene.overhead_camera = None
    env_cfg.scene.front_center_camera = None

    env = DiagEnv(cfg=env_cfg)

    seeds = args.eval_seeds
    num_targets = args.eval_targets
    total_eval = len(seeds) * num_targets

    results = []
    all_ids = torch.arange(N, device=dev_str)

    print(f"\n[DIAG] Running {total_eval} episodes ({len(seeds)} seeds x {num_targets} targets)")
    print(f"[DIAG] Heuristic params: max_macros=80, hold_steps={HEUR_HOLD_STEPS}, coarse_dist={COARSE_DIST_M}m")
    print(f"[DIAG] JT_ALPHA={HEUR_JT_ALPHA}, STANDOFF_Y={STANDOFF_DIST_Y}, COLLISION_MIN={HEUR_COLLISION_MIN_DIST}")
    print()

    eval_idx = 0
    t_total = time.time()

    with torch.inference_mode():
        for si, seed in enumerate(seeds):
            targets = make_targets_per_env(1, num_targets, seed)[0]

            for tidx, target_np in enumerate(targets):
                eval_idx += 1
                t0 = time.time()

                # Set target for all envs
                ball = torch.tensor(target_np, device=dev_str).unsqueeze(0).expand(N, 3)
                env._ball_pos[:] = ball
                left_ft, right_ft = compute_dual_targets_batch(ball)
                env._left_ft_target[:] = left_ft
                env._right_ft_target[:] = right_ft

                # Teleport + settle
                env.teleport_to_bent_elbow(all_ids)
                env.settle_physics(20)

                # Run heuristic with logging
                info = run_heuristic_with_logging(env, all_ids)
                dt = time.time() - t0

                info["seed"] = seed
                info["target_idx"] = tidx
                info["target_xyz"] = target_np.tolist()
                info["left_ft_target"] = left_ft[0].cpu().numpy().tolist()
                info["right_ft_target"] = right_ft[0].cpu().numpy().tolist()
                info["elapsed_s"] = dt
                results.append(info)

                phase_str = ["A-stuck", "B-stuck", "done"][info["final_phase"]]
                ab_str = f"AB@{info['phase_ab_macro']}" if info["phase_ab_macro"] >= 0 else "noAB"
                print(
                    f"  [{eval_idx}/{total_eval}] seed={seed} t={tidx} "
                    f"dL={info['final_dist_l']*100:.2f}cm dR={info['final_dist_r']*100:.2f}cm "
                    f"macros={info['total_macros']} {ab_str} phase={phase_str} "
                    f"errL=[{info['err_l_xyz'][0]*100:+.1f},{info['err_l_xyz'][1]*100:+.1f},{info['err_l_xyz'][2]*100:+.1f}]cm "
                    f"({dt:.1f}s)",
                    flush=True,
                )

    total_time = time.time() - t_total

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------
    dL = [r["final_dist_l"] * 100 for r in results]
    dR = [r["final_dist_r"] * 100 for r in results]
    macros = [r["total_macros"] for r in results]
    ab_macros = [r["phase_ab_macro"] for r in results if r["phase_ab_macro"] >= 0]

    def stats(vals):
        v = sorted(vals)
        n = len(v)
        return {
            "mean": float(np.mean(v)),
            "std": float(np.std(v)),
            "min": float(np.min(v)),
            "max": float(np.max(v)),
            "median": float(np.median(v)),
            "p10": float(v[max(0, int(n * 0.1))]),
            "p90": float(v[min(n - 1, int(n * 0.9))]),
            "pct_lt_10cm": float(sum(1 for x in v if x < 10.0) / n * 100),
            "pct_lt_5cm": float(sum(1 for x in v if x < 5.0) / n * 100),
        }

    stats_l = stats(dL)
    stats_r = stats(dR)

    print("\n" + "=" * 80)
    print("HEURISTIC COARSE APPROACH DIAGNOSTICS")
    print("=" * 80)
    print(f"Total time: {total_time:.0f}s ({total_time/60:.1f}min)")

    print(f"\n{'='*40}")
    print(f" LEFT ARM (fingertip → target)")
    print(f"{'='*40}")
    print(f"  mean:   {stats_l['mean']:.2f}cm")
    print(f"  std:    {stats_l['std']:.2f}cm")
    print(f"  min:    {stats_l['min']:.2f}cm")
    print(f"  max:    {stats_l['max']:.2f}cm")
    print(f"  median: {stats_l['median']:.2f}cm")
    print(f"  p10:    {stats_l['p10']:.2f}cm")
    print(f"  p90:    {stats_l['p90']:.2f}cm")
    print(f"  <10cm:  {stats_l['pct_lt_10cm']:.1f}%")
    print(f"  <5cm:   {stats_l['pct_lt_5cm']:.1f}%")

    print(f"\n{'='*40}")
    print(f" RIGHT ARM (fingertip → target)")
    print(f"{'='*40}")
    print(f"  mean:   {stats_r['mean']:.2f}cm")
    print(f"  std:    {stats_r['std']:.2f}cm")
    print(f"  min:    {stats_r['min']:.2f}cm")
    print(f"  max:    {stats_r['max']:.2f}cm")
    print(f"  median: {stats_r['median']:.2f}cm")
    print(f"  p10:    {stats_r['p10']:.2f}cm")
    print(f"  p90:    {stats_r['p90']:.2f}cm")
    print(f"  <10cm:  {stats_r['pct_lt_10cm']:.1f}%")
    print(f"  <5cm:   {stats_r['pct_lt_5cm']:.1f}%")

    print(f"\n{'='*40}")
    print(f" MACRO STEPS")
    print(f"{'='*40}")
    print(f"  Total macros: mean={np.mean(macros):.1f} min={min(macros)} max={max(macros)}")
    if ab_macros:
        print(f"  A→B transition: mean={np.mean(ab_macros):.1f} min={min(ab_macros)} max={max(ab_macros)}")
    else:
        print(f"  A→B transition: NONE (all stuck in Phase A!)")

    phases = [r["final_phase"] for r in results]
    print(f"\n{'='*40}")
    print(f" PHASE COMPLETION")
    print(f"{'='*40}")
    print(f"  Phase A stuck: {phases.count(0)}/{len(phases)}")
    print(f"  Phase B stuck: {phases.count(1)}/{len(phases)}")
    print(f"  Done (A+B):    {phases.count(2)}/{len(phases)}")

    # Per-component error breakdown
    err_l_x = [abs(r["err_l_xyz"][0]) * 100 for r in results]
    err_l_y = [abs(r["err_l_xyz"][1]) * 100 for r in results]
    err_l_z = [abs(r["err_l_xyz"][2]) * 100 for r in results]
    err_l_x_signed = [r["err_l_xyz"][0] * 100 for r in results]
    err_l_y_signed = [r["err_l_xyz"][1] * 100 for r in results]
    err_l_z_signed = [r["err_l_xyz"][2] * 100 for r in results]

    print(f"\n{'='*40}")
    print(f" LEFT ARM ERROR BREAKDOWN")
    print(f"{'='*40}")
    print(f"  |X|: mean={np.mean(err_l_x):.2f} std={np.std(err_l_x):.2f} max={max(err_l_x):.2f}cm")
    print(f"  |Y|: mean={np.mean(err_l_y):.2f} std={np.std(err_l_y):.2f} max={max(err_l_y):.2f}cm")
    print(f"  |Z|: mean={np.mean(err_l_z):.2f} std={np.std(err_l_z):.2f} max={max(err_l_z):.2f}cm")
    print(f"  signed X: mean={np.mean(err_l_x_signed):+.2f}cm (>0 = too far +X)")
    print(f"  signed Y: mean={np.mean(err_l_y_signed):+.2f}cm (>0 = too far +Y)")
    print(f"  signed Z: mean={np.mean(err_l_z_signed):+.2f}cm (>0 = too high)")

    err_r_x = [abs(r["err_r_xyz"][0]) * 100 for r in results]
    err_r_y = [abs(r["err_r_xyz"][1]) * 100 for r in results]
    err_r_z = [abs(r["err_r_xyz"][2]) * 100 for r in results]
    err_r_x_signed = [r["err_r_xyz"][0] * 100 for r in results]
    err_r_y_signed = [r["err_r_xyz"][1] * 100 for r in results]
    err_r_z_signed = [r["err_r_xyz"][2] * 100 for r in results]

    print(f"\n{'='*40}")
    print(f" RIGHT ARM ERROR BREAKDOWN")
    print(f"{'='*40}")
    print(f"  |X|: mean={np.mean(err_r_x):.2f} std={np.std(err_r_x):.2f} max={max(err_r_x):.2f}cm")
    print(f"  |Y|: mean={np.mean(err_r_y):.2f} std={np.std(err_r_y):.2f} max={max(err_r_y):.2f}cm")
    print(f"  |Z|: mean={np.mean(err_r_z):.2f} std={np.std(err_r_z):.2f} max={max(err_r_z):.2f}cm")
    print(f"  signed X: mean={np.mean(err_r_x_signed):+.2f}cm")
    print(f"  signed Y: mean={np.mean(err_r_y_signed):+.2f}cm")
    print(f"  signed Z: mean={np.mean(err_r_z_signed):+.2f}cm")

    # At-transition distances
    ab_dl = [r["dist_l_at_ab"] * 100 for r in results if r["dist_l_at_ab"] >= 0]
    ab_dr = [r["dist_r_at_ab"] * 100 for r in results if r["dist_r_at_ab"] >= 0]
    if ab_dl:
        print(f"\n{'='*40}")
        print(f" DISTANCES AT A→B TRANSITION")
        print(f"{'='*40}")
        print(f"  Left FT→target:  mean={np.mean(ab_dl):.2f}cm min={min(ab_dl):.2f}cm max={max(ab_dl):.2f}cm")
        print(f"  Right FT→target: mean={np.mean(ab_dr):.2f}cm min={min(ab_dr):.2f}cm max={max(ab_dr):.2f}cm")

    # Per-episode table
    print(f"\n{'='*80}")
    print(f" PER-EPISODE DETAIL")
    print(f"{'='*80}")
    print(f"{'Ep':>3} {'Seed':>4} {'T':>2} {'dL(cm)':>7} {'dR(cm)':>7} {'Macros':>6} {'AB@':>4} {'Phase':>7} "
          f"{'errL_X':>7} {'errL_Y':>7} {'errL_Z':>7}")
    for i, r in enumerate(results):
        ab = str(r["phase_ab_macro"]) if r["phase_ab_macro"] >= 0 else "-"
        ph = ["A-stk", "B-stk", "done"][r["final_phase"]]
        print(f"{i+1:3d} {r['seed']:4d} {r['target_idx']:2d} "
              f"{r['final_dist_l']*100:7.2f} {r['final_dist_r']*100:7.2f} "
              f"{r['total_macros']:6d} {ab:>4} {ph:>7} "
              f"{r['err_l_xyz'][0]*100:+7.2f} {r['err_l_xyz'][1]*100:+7.2f} {r['err_l_xyz'][2]*100:+7.2f}")

    # Save JSON
    json_path = os.path.join(output_dir, "diag_results.json")
    summary = {
        "config": {
            "num_envs": N,
            "seeds": seeds,
            "num_targets": num_targets,
            "max_macros": 80,
            "hold_steps": HEUR_HOLD_STEPS,
            "coarse_dist_m": COARSE_DIST_M,
            "jt_alpha": HEUR_JT_ALPHA,
            "standoff_dist_y": STANDOFF_DIST_Y,
            "collision_min_dist": HEUR_COLLISION_MIN_DIST,
        },
        "stats_left_cm": stats_l,
        "stats_right_cm": stats_r,
        "total_time_s": total_time,
        "per_episode": results,
    }
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n[DIAG] JSON saved: {json_path}")

    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
