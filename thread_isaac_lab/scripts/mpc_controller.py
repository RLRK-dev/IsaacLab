#!/usr/bin/env python3
"""MPC Controller using CEM (Cross-Entropy Method) with learned dynamics model.

Receding-horizon planning: at each step, plan T steps ahead using the dynamics
model, execute only the first action, then re-plan from the new state.

The BC policy provides warm-start action sequences for CEM initialization.

Usage (standalone test):
    python thread_isaac_lab/scripts/mpc_controller.py --device cuda:1

Integration with POC script:
    --backend dual_mpc  (in poc_single_arm_redball_gpt.py)
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn

# Import model definitions
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from train_bc_dynamics import DualBCPolicy, DualDynamicsModel, load_all_dual_episodes


@dataclass
class CEMConfig:
    """Configuration for CEM-based MPC."""

    horizon: int = 5           # Planning horizon T
    n_candidates: int = 200    # Number of action sequence candidates
    n_elite: int = 20          # Number of elite candidates (top 10%)
    n_iterations: int = 5      # CEM iterations per planning step
    action_dim: int = 6        # 3 (left) + 3 (right)
    action_clip: float = 0.05  # Per-axis action clamp (matches POC delta clip)
    init_std: float = 0.02     # Initial std around BC mean
    min_std: float = 0.003     # Minimum std (prevents collapse)
    reach_threshold: float = 0.05  # Reach bonus threshold (meters)
    reach_bonus: float = 10.0  # Bonus for both arms reaching
    gamma: float = 1.0         # No discount within short horizon


class CEMMPCController:
    """CEM-based Model Predictive Controller for dual-arm reaching."""

    def __init__(
        self,
        dynamics: DualDynamicsModel,
        bc_policy: DualBCPolicy,
        config: CEMConfig | None = None,
        device: torch.device | str = "cuda:1",
    ):
        self.config = config or CEMConfig()
        self.device = torch.device(device)

        # Dynamics model (frozen, used for rollout evaluation)
        self.dynamics = dynamics.to(self.device)
        self.dynamics.eval()
        for p in self.dynamics.parameters():
            p.requires_grad = False

        # BC policy (frozen, used for warm-start)
        self.bc_policy = bc_policy.to(self.device)
        self.bc_policy.eval()
        for p in self.bc_policy.parameters():
            p.requires_grad = False

        # Warm-start: carry over the shifted plan from previous step
        self._prev_mean: torch.Tensor | None = None  # (T, 6)

        # Timing stats
        self._plan_times: list[float] = []

    def reset(self):
        """Reset the controller state (call at episode start)."""
        self._prev_mean = None
        self._plan_times = []

    # Debug: set to True to print per-step diagnostics
    debug_verbose: bool = False
    # Store last prediction for post-step comparison
    _debug_pred_next: np.ndarray | None = None
    _debug_action: np.ndarray | None = None
    _debug_step_count: int = 0

    @property
    def mean_plan_time_ms(self) -> float:
        if not self._plan_times:
            return 0.0
        return np.mean(self._plan_times) * 1000

    @torch.no_grad()
    def get_action(
        self,
        left_ee: np.ndarray,
        right_ee: np.ndarray,
        ball_pos: np.ndarray,
        phase: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Plan with CEM and return the first action (left_delta, right_delta).

        Args:
            left_ee: (3,) current left EE position
            right_ee: (3,) current right EE position
            ball_pos: (3,) ball/target position
            phase: 0 or 1 (Phase A or B)

        Returns:
            left_delta: (3,) clipped action for left arm
            right_delta: (3,) clipped action for right arm
        """
        t_start = time.perf_counter()
        cfg = self.config
        T = cfg.horizon
        N = cfg.n_candidates
        D = cfg.action_dim

        # Convert to tensors
        left_ee_t = torch.tensor(left_ee[:3], dtype=torch.float32, device=self.device)
        right_ee_t = torch.tensor(right_ee[:3], dtype=torch.float32, device=self.device)
        ball_t = torch.tensor(ball_pos[:3], dtype=torch.float32, device=self.device)
        phase_t = torch.tensor([float(phase)], dtype=torch.float32, device=self.device)

        # --- Generate BC warm-start (mean action sequence) ---
        bc_mean = self._generate_bc_sequence(left_ee_t, right_ee_t, ball_t, phase_t)
        # bc_mean: (T, 6)

        # --- Initialize CEM distribution ---
        if self._prev_mean is not None:
            # Shift previous plan: drop first action, repeat last
            mean = torch.cat([self._prev_mean[1:], self._prev_mean[-1:]], dim=0)
            # Blend with BC: 70% shifted prev, 30% BC
            mean = 0.7 * mean + 0.3 * bc_mean
        else:
            mean = bc_mean

        std = torch.full((T, D), cfg.init_std, device=self.device)

        # --- CEM iterations (0 = BC passthrough) ---
        best_action_seq = mean.clone()
        best_reward = -float("inf")
        _cem_iter_stats = []  # per-iteration diagnostics

        for cem_iter in range(cfg.n_iterations):
            # Sample N candidate action sequences: (N, T, D)
            noise = torch.randn(N, T, D, device=self.device) * std.unsqueeze(0)
            candidates = mean.unsqueeze(0) + noise  # (N, T, D)
            candidates = torch.clamp(candidates, -cfg.action_clip, cfg.action_clip)

            # Evaluate all candidates via dynamics rollout
            rewards = self._evaluate_candidates(
                candidates, left_ee_t, right_ee_t, ball_t, phase_t
            )  # (N,)

            # Select elite
            elite_idx = torch.topk(rewards, cfg.n_elite, dim=0).indices
            elite = candidates[elite_idx]  # (n_elite, T, D)

            # Collect per-iteration stats before updating
            _iter_stat = {
                "iter": cem_iter,
                "mean_reward": rewards.mean().item(),
                "elite_reward": rewards[elite_idx].mean().item(),
                "best_reward": rewards.max().item(),
                "std_L": std[0, :3].cpu().numpy().tolist(),
                "std_R": std[0, 3:].cpu().numpy().tolist(),
                "mean_std": std.mean().item(),
                "mean_first_L": mean[0, :3].cpu().numpy().tolist(),
                "mean_first_R": mean[0, 3:].cpu().numpy().tolist(),
            }
            _cem_iter_stats.append(_iter_stat)

            # Update distribution
            mean = elite.mean(dim=0)  # (T, D)
            std = elite.std(dim=0).clamp(min=cfg.min_std)  # (T, D)

            # Track best
            iter_best_idx = rewards.argmax()
            if rewards[iter_best_idx] > best_reward:
                best_reward = rewards[iter_best_idx].item()
                best_action_seq = candidates[iter_best_idx].clone()

        # Save plan for warm-start next step
        self._prev_mean = best_action_seq.clone()

        # Extract first action
        first_action = best_action_seq[0].cpu().numpy()  # (6,)
        left_delta = np.clip(first_action[:3], -cfg.action_clip, cfg.action_clip)
        right_delta = np.clip(first_action[3:], -cfg.action_clip, cfg.action_clip)

        elapsed = time.perf_counter() - t_start
        self._plan_times.append(elapsed)

        # Debug output
        if self.debug_verbose:
            self._debug_step_count += 1
            # BC warm-start for comparison
            bc_first = bc_mean[0].cpu().numpy()
            bc_L_mag = np.linalg.norm(bc_first[:3])
            bc_R_mag = np.linalg.norm(bc_first[3:])
            cem_L_mag = np.linalg.norm(left_delta)
            cem_R_mag = np.linalg.norm(right_delta)
            bc_cem_L_diff = np.linalg.norm(left_delta - bc_first[:3])
            bc_cem_R_diff = np.linalg.norm(right_delta - bc_first[3:])
            # Dynamics prediction for chosen action
            dyn_inp = torch.cat([left_ee_t, right_ee_t,
                                 torch.tensor(left_delta, dtype=torch.float32, device=self.device),
                                 torch.tensor(right_delta, dtype=torch.float32, device=self.device)]).unsqueeze(0)
            pred_next = self.dynamics.predict_next(dyn_inp).squeeze(0).cpu().numpy()
            self._debug_pred_next = pred_next.copy()
            self._debug_action = np.concatenate([left_delta, right_delta])

            # Demo action stats reference
            demo_L_mean, demo_R_mean, demo_L_max = 0.02273, 0.00712, 0.087

            print(f"\n[MPC_DBG] step={self._debug_step_count} phase={phase}")
            print(f"  sim_state: L_ee={left_ee[:3].tolist()} R_ee={right_ee[:3].tolist()}")
            print(f"  ball_pos:  {ball_pos[:3].tolist()}")
            print(f"  --- BC vs CEM action comparison ---")
            print(f"  bc_action:  L={bc_first[:3].tolist()} R={bc_first[3:].tolist()}")
            print(f"  cem_action: L={left_delta.tolist()} R={right_delta.tolist()}")
            print(f"  |bc_L|={bc_L_mag:.5f}  |bc_R|={bc_R_mag:.5f}")
            print(f"  |cem_L|={cem_L_mag:.5f} |cem_R|={cem_R_mag:.5f}")
            print(f"  |cem-bc| diff: L={bc_cem_L_diff:.5f} R={bc_cem_R_diff:.5f}")
            print(f"  demo ref: L_mean={demo_L_mean:.5f} R_mean={demo_R_mean:.5f} L_max={demo_L_max:.3f}")
            cem_L_in_dist = "IN-DIST" if cem_L_mag <= demo_L_max * 1.2 else f"OUT-OF-DIST ({cem_L_mag/demo_L_max:.1f}x max)"
            cem_R_in_dist = "IN-DIST" if cem_R_mag <= demo_L_max * 1.2 else f"OUT-OF-DIST ({cem_R_mag/demo_L_max:.1f}x max)"
            print(f"  dist check: L={cem_L_in_dist}  R={cem_R_in_dist}")
            print(f"  --- CEM iteration stats (std/reward evolution) ---")
            for s in _cem_iter_stats:
                print(f"    iter={s['iter']}: mean_std={s['mean_std']:.5f} "
                      f"mean_rew={s['mean_reward']:.4f} elite_rew={s['elite_reward']:.4f} best_rew={s['best_reward']:.4f}")
                print(f"      std_L={[f'{v:.5f}' for v in s['std_L']]} std_R={[f'{v:.5f}' for v in s['std_R']]}")
            print(f"  dyn_pred:  next_L={pred_next[:3].tolist()} next_R={pred_next[3:].tolist()}")
            print(f"  cem_reward: {best_reward:.4f}  plan_ms={elapsed*1000:.1f}")

        return left_delta, right_delta

    def _generate_bc_sequence(
        self,
        left_ee: torch.Tensor,
        right_ee: torch.Tensor,
        ball: torch.Tensor,
        phase: torch.Tensor,
    ) -> torch.Tensor:
        """Generate a T-step action sequence using the BC policy autoregressively.

        Uses the dynamics model to predict next states, then queries BC again.

        Returns:
            actions: (T, 6)
        """
        T = self.config.horizon
        actions = []

        le = left_ee.clone()
        re = right_ee.clone()

        for t in range(T):
            # Query BC
            inp = torch.cat([le, re, ball, phase]).unsqueeze(0)  # (1, 10)
            act = self.bc_policy(inp).squeeze(0)  # (6,)
            act = torch.clamp(act, -self.config.action_clip, self.config.action_clip)
            actions.append(act)

            # Predict next state with dynamics
            dyn_inp = torch.cat([le, re, act[:3], act[3:]]).unsqueeze(0)  # (1, 12)
            next_state = self.dynamics.predict_next(dyn_inp).squeeze(0)  # (6,)
            le = next_state[:3]
            re = next_state[3:]

        return torch.stack(actions)  # (T, 6)

    def _evaluate_candidates(
        self,
        candidates: torch.Tensor,
        left_ee: torch.Tensor,
        right_ee: torch.Tensor,
        ball: torch.Tensor,
        phase: torch.Tensor,
    ) -> torch.Tensor:
        """Evaluate N action sequences via dynamics rollout.

        Args:
            candidates: (N, T, D) action sequences
            left_ee: (3,) initial left EE
            right_ee: (3,) initial right EE
            ball: (3,) ball position
            phase: (1,) phase

        Returns:
            rewards: (N,) cumulative reward per candidate
        """
        cfg = self.config
        N, T, D = candidates.shape

        # Broadcast initial state to (N, 3)
        le = left_ee.unsqueeze(0).expand(N, -1).clone()   # (N, 3)
        re = right_ee.unsqueeze(0).expand(N, -1).clone()  # (N, 3)
        ball_n = ball.unsqueeze(0).expand(N, -1)           # (N, 3)

        # Compute targets (constant)
        left_target = ball_n + torch.tensor([0.0, -0.04, 0.0], device=self.device)
        right_target = ball_n + torch.tensor([0.0, +0.04, 0.0], device=self.device)

        cumulative_reward = torch.zeros(N, device=self.device)

        for t in range(T):
            action_t = candidates[:, t, :]  # (N, 6)
            left_act = action_t[:, :3]
            right_act = action_t[:, 3:]

            # Dynamics rollout
            dyn_input = torch.cat([le, re, left_act, right_act], dim=-1)  # (N, 12)
            next_state = self.dynamics.predict_next(dyn_input)  # (N, 6)
            le = next_state[:, :3]
            re = next_state[:, 3:]

            # Per-step reward
            left_dist = torch.norm(le - left_target, dim=-1)
            right_dist = torch.norm(re - right_target, dim=-1)
            step_reward = -(left_dist + right_dist)

            # Terminal bonus at last step
            if t == T - 1:
                both_reached = (left_dist < cfg.reach_threshold) & (
                    right_dist < cfg.reach_threshold
                )
                step_reward = step_reward + cfg.reach_bonus * both_reached.float()

            cumulative_reward = cumulative_reward + (cfg.gamma ** t) * step_reward

        return cumulative_reward


def load_mpc_controller(
    dynamics_path: str = "data/training_results_dual/dual_dynamics_model.pt",
    bc_policy_path: str = "data/training_results_dual/1seed/dual_bc_policy.pt",
    device: str = "cuda:1",
    config: CEMConfig | None = None,
) -> CEMMPCController:
    """Load dynamics model and BC policy, create MPC controller."""
    # Load dynamics
    dynamics = DualDynamicsModel()
    dynamics.load_state_dict(
        torch.load(dynamics_path, map_location="cpu", weights_only=True)
    )

    # Load BC policy
    bc_policy = DualBCPolicy()
    bc_policy.load_state_dict(
        torch.load(bc_policy_path, map_location="cpu", weights_only=True)
    )

    return CEMMPCController(
        dynamics=dynamics,
        bc_policy=bc_policy,
        config=config,
        device=device,
    )


# ---------------------------------------------------------------------------
# Standalone test: run MPC on a few demo initial states
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="MPC Controller standalone test")
    parser.add_argument("--device", type=str, default="cuda:1")
    parser.add_argument("--dynamics_path", type=str,
                        default="data/training_results_dual/dual_dynamics_model.pt")
    parser.add_argument("--bc_policy_path", type=str,
                        default="data/training_results_dual/1seed/dual_bc_policy.pt")
    parser.add_argument("--demo_dir", type=str, default="data/demos_dual")
    parser.add_argument("--n_test", type=int, default=50,
                        help="Number of episodes to test")
    parser.add_argument("--max_steps", type=int, default=50,
                        help="Max steps per episode")
    args = parser.parse_args()

    print(f"[MPC Test] device={args.device}")
    print(f"[MPC Test] dynamics={args.dynamics_path}")
    print(f"[MPC Test] bc_policy={args.bc_policy_path}")

    controller = load_mpc_controller(
        dynamics_path=args.dynamics_path,
        bc_policy_path=args.bc_policy_path,
        device=args.device,
    )

    print(f"[MPC Test] CEM config: T={controller.config.horizon} "
          f"N={controller.config.n_candidates} elite={controller.config.n_elite} "
          f"iter={controller.config.n_iterations} clip={controller.config.action_clip}")

    # Load demo initial states for testing
    episodes = load_all_dual_episodes(args.demo_dir)
    print(f"[MPC Test] Loaded {len(episodes)} episodes")

    # Load dynamics for offline rollout
    dynamics = DualDynamicsModel()
    dynamics.load_state_dict(
        torch.load(args.dynamics_path, map_location="cpu", weights_only=True)
    )
    dynamics.to(args.device)
    dynamics.eval()

    n_test = min(args.n_test, len(episodes))
    n_reached = 0
    total_plan_time = 0.0
    total_steps = 0

    for i in range(n_test):
        ep = episodes[i]
        left_ee = ep.left_ee_pos[0].copy()
        right_ee = ep.right_ee_pos[0].copy()
        ball_pos = ep.ball_pos[0].copy()
        phase = int(ep.phase[0])

        controller.reset()

        left_target = ball_pos.copy()
        left_target[1] -= 0.04
        right_target = ball_pos.copy()
        right_target[1] += 0.04

        reached = False
        for step in range(args.max_steps):
            left_delta, right_delta = controller.get_action(
                left_ee, right_ee, ball_pos, phase
            )

            # Apply action through dynamics model (offline simulation)
            with torch.no_grad():
                dyn_inp = torch.tensor(
                    np.concatenate([left_ee[:3], right_ee[:3], left_delta, right_delta]),
                    dtype=torch.float32, device=args.device,
                ).unsqueeze(0)
                next_state = dynamics.predict_next(dyn_inp).squeeze(0).cpu().numpy()

            left_ee = next_state[:3]
            right_ee = next_state[3:]
            total_steps += 1

            # Check reach
            left_dist = np.linalg.norm(left_ee - left_target)
            right_dist = np.linalg.norm(right_ee - right_target)
            if left_dist < 0.05 and right_dist < 0.05:
                reached = True
                break

        if reached:
            n_reached += 1

        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{n_test}] reached={reached} "
                  f"L={np.linalg.norm(left_ee - left_target)*100:.1f}cm "
                  f"R={np.linalg.norm(right_ee - right_target)*100:.1f}cm "
                  f"steps={step+1} "
                  f"plan_time={controller.mean_plan_time_ms:.1f}ms/step")

    print(f"\n{'='*60}")
    print(f"MPC OFFLINE TEST RESULTS")
    print(f"{'='*60}")
    print(f"  Reach rate: {n_reached}/{n_test} ({n_reached/n_test*100:.1f}%)")
    print(f"  Mean plan time: {controller.mean_plan_time_ms:.1f} ms/step")
    print(f"  Total steps: {total_steps}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
