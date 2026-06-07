# thread_isaac_lab/models/mpc_controller.py
"""
CEM-based Model Predictive Controller using World Model.

This controller uses Cross-Entropy Method (CEM) to optimize action sequences
by rolling out trajectories through the learned World Model.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass

import sys
sys.path.insert(0, "/home/rlrk/IsaacLab")

from thread_isaac_lab.models.world_model_4cam import WorldModel4Cam, WorldModel4CamConfig
from thread_isaac_lab.configs.mpc_config import (
    MPCConfig,
    get_phase_costs,
    TaskStateIndices,
    ProprioIndices,
    ActionIndices,
)


@dataclass
class Observation:
    """Structured observation for MPC planning."""
    front_left_img: torch.Tensor   # [B, 3, 256, 256]
    front_right_img: torch.Tensor  # [B, 3, 256, 256]
    back_img: torch.Tensor         # [B, 3, 256, 256]
    overhead_img: torch.Tensor     # [B, 3, 256, 256]
    proprio: torch.Tensor          # [B, 34]
    task_state: torch.Tensor       # [B, 44]


class MPCController:
    """CEM-based Model Predictive Controller.

    Uses the trained World Model to predict future states and optimizes
    action sequences using Cross-Entropy Method.
    """

    def __init__(self, config: MPCConfig, world_model: Optional[WorldModel4Cam] = None):
        """Initialize MPC Controller.

        Args:
            config: MPC configuration
            world_model: Pre-loaded world model (optional, will load if not provided)
        """
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else "cpu")

        # Load world model if not provided
        if world_model is None:
            self.world_model = self._load_world_model(config.world_model_path)
        else:
            self.world_model = world_model

        self.world_model.to(self.device)
        self.world_model.eval()

        # CEM state
        self.action_mean = None
        self.action_std = None

        # Cache for warm starting
        self._prev_action_seq = None

        print(f"[MPCController] Initialized with horizon={config.horizon}, "
              f"candidates={config.num_candidates}, elite_ratio={config.elite_ratio}")

    def _load_world_model(self, path: str) -> WorldModel4Cam:
        """Load trained world model from checkpoint."""
        print(f"[MPCController] Loading world model from {path}")

        # Add module alias for pickle compatibility
        import sys
        import thread_isaac_lab.models.world_model_4cam as wm_module
        sys.modules['models'] = sys.modules.get('thread_isaac_lab.models', wm_module)
        sys.modules['models.world_model_4cam'] = wm_module

        config = WorldModel4CamConfig()
        model = WorldModel4Cam(config)

        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        model.load_state_dict(state_dict)

        print(f"[MPCController] World model loaded successfully")
        return model

    def reset(self):
        """Reset CEM state for new episode."""
        self.action_mean = None
        self.action_std = None
        self._prev_action_seq = None

    def plan(
        self,
        obs: Observation,
        phase: int,
        target: Optional[Dict[str, float]] = None,
    ) -> torch.Tensor:
        """Plan optimal action using CEM optimization.

        Args:
            obs: Current observation
            phase: Current phase (for cost function selection)
            target: Optional target values for cost computation

        Returns:
            best_action: Optimal first action [action_dim]
        """
        with torch.no_grad():
            # Get cost weights for current phase
            cost_weights = get_phase_costs(phase)

            # Initialize action distribution
            if self.action_mean is None:
                self._init_action_distribution()
            else:
                # Warm start: shift previous solution
                self._shift_action_distribution()

            # CEM iterations
            for cem_iter in range(self.config.cem_iterations):
                # Sample action sequences [num_candidates, horizon, action_dim]
                action_sequences = self._sample_actions()

                # Evaluate all candidates
                costs = self._evaluate_candidates(
                    obs, action_sequences, cost_weights, phase, target
                )

                # Select elite samples
                elite_indices = self._select_elites(costs)
                elite_actions = action_sequences[elite_indices]

                # Update distribution
                self._update_distribution(elite_actions)

            # Return mean of first action
            best_action = self.action_mean[0].clone()

            # Cache for warm starting
            self._prev_action_seq = self.action_mean.clone()

            return best_action

    def _init_action_distribution(self):
        """Initialize action distribution for CEM."""
        horizon = self.config.horizon
        action_dim = self.config.action_dim

        # Start with zero mean (no movement)
        self.action_mean = torch.zeros(horizon, action_dim, device=self.device)

        # Initialize with moderate variance
        self.action_std = torch.ones(horizon, action_dim, device=self.device) * 0.02

        # Set different std for gripper actions (should be more stable)
        gripper_indices = ActionIndices.ALL_GRIPPERS
        self.action_std[:, gripper_indices] = 0.005

    def _shift_action_distribution(self):
        """Shift action distribution for warm starting."""
        # Shift by one timestep
        self.action_mean = torch.roll(self.action_mean, shifts=-1, dims=0)
        # Fill last with zero (no movement)
        self.action_mean[-1] = 0

        # Maintain std but slightly increase for exploration
        self.action_std = self.action_std * 1.1
        self.action_std = torch.clamp(self.action_std, min=0.005, max=0.05)

    def _sample_actions(self) -> torch.Tensor:
        """Sample action sequences from current distribution.

        Returns:
            action_sequences: [num_candidates, horizon, action_dim]
        """
        num_candidates = self.config.num_candidates
        horizon = self.config.horizon
        action_dim = self.config.action_dim

        # Sample from Gaussian
        noise = torch.randn(
            num_candidates, horizon, action_dim, device=self.device
        )
        actions = self.action_mean.unsqueeze(0) + noise * self.action_std.unsqueeze(0)

        # Clip to action bounds
        actions = self._clip_actions(actions)

        return actions

    def _clip_actions(self, actions: torch.Tensor) -> torch.Tensor:
        """Clip actions to valid bounds."""
        # Clip joint actions
        joint_indices = ActionIndices.ALL_JOINTS
        actions[..., joint_indices] = torch.clamp(
            actions[..., joint_indices],
            self.config.action_low,
            self.config.action_high
        )

        # Clip gripper actions
        gripper_indices = ActionIndices.ALL_GRIPPERS
        actions[..., gripper_indices] = torch.clamp(
            actions[..., gripper_indices],
            self.config.gripper_action_low,
            self.config.gripper_action_high
        )

        return actions

    def _evaluate_candidates(
        self,
        obs: Observation,
        action_sequences: torch.Tensor,
        cost_weights: Dict[str, float],
        phase: int,
        target: Optional[Dict[str, float]] = None,
    ) -> torch.Tensor:
        """Evaluate all action sequence candidates.

        Args:
            obs: Current observation
            action_sequences: [num_candidates, horizon, action_dim]
            cost_weights: Phase-specific cost weights
            phase: Current phase
            target: Optional target values

        Returns:
            costs: [num_candidates] total cost for each candidate
        """
        num_candidates = action_sequences.shape[0]
        horizon = action_sequences.shape[1]

        # Expand observation for all candidates
        obs_expanded = self._expand_observation(obs, num_candidates)

        # Initialize total costs
        total_costs = torch.zeros(num_candidates, device=self.device)

        # Current state (will be updated during rollout)
        current_proprio = obs_expanded.proprio.clone()
        current_task_state = obs_expanded.task_state.clone()

        # Rollout through horizon
        for t in range(horizon):
            action = action_sequences[:, t]  # [num_candidates, action_dim]

            # Predict next state using world model
            with torch.no_grad():
                pred = self.world_model(
                    obs_expanded.front_left_img,
                    obs_expanded.front_right_img,
                    obs_expanded.back_img,
                    obs_expanded.overhead_img,
                    current_proprio,
                    current_task_state,
                    action,
                )

            next_proprio = pred["pred_proprio"]
            next_task_state = pred["pred_task_state"]

            # Compute step cost
            step_cost = self._compute_step_cost(
                current_proprio,
                current_task_state,
                action,
                next_proprio,
                next_task_state,
                cost_weights,
                phase,
                target,
            )

            # Apply discount
            discount = self.config.gamma ** t
            total_costs += discount * step_cost

            # Update state for next step
            current_proprio = next_proprio
            current_task_state = next_task_state

        return total_costs

    def _expand_observation(self, obs: Observation, num_candidates: int) -> Observation:
        """Expand observation to batch size for parallel evaluation."""
        return Observation(
            front_left_img=obs.front_left_img.expand(num_candidates, -1, -1, -1),
            front_right_img=obs.front_right_img.expand(num_candidates, -1, -1, -1),
            back_img=obs.back_img.expand(num_candidates, -1, -1, -1),
            overhead_img=obs.overhead_img.expand(num_candidates, -1, -1, -1),
            proprio=obs.proprio.expand(num_candidates, -1),
            task_state=obs.task_state.expand(num_candidates, -1),
        )

    def _compute_step_cost(
        self,
        proprio: torch.Tensor,
        task_state: torch.Tensor,
        action: torch.Tensor,
        next_proprio: torch.Tensor,
        next_task_state: torch.Tensor,
        cost_weights: Dict[str, float],
        phase: int,
        target: Optional[Dict[str, float]] = None,
    ) -> torch.Tensor:
        """Compute cost for a single step.

        Args:
            proprio: Current proprioception [B, 34]
            task_state: Current task state [B, 44]
            action: Action taken [B, 18]
            next_proprio: Predicted next proprio [B, 34]
            next_task_state: Predicted next task state [B, 44]
            cost_weights: Cost weight dictionary
            phase: Current phase
            target: Optional target values

        Returns:
            cost: [B] cost for each candidate
        """
        batch_size = proprio.shape[0]
        cost = torch.zeros(batch_size, device=self.device)

        # Phase 3: Lift - maximize cable Z
        if phase == 3:
            cost += self._compute_lift_cost(
                task_state, next_task_state, action, cost_weights
            )

        # Phase 4: Hook approach
        elif phase == 4:
            cost += self._compute_hook_approach_cost(
                task_state, next_task_state, proprio, next_proprio, cost_weights
            )

        # Phase 5: Hook placement
        elif phase == 5:
            cost += self._compute_hook_placement_cost(
                task_state, next_task_state, cost_weights, target
            )

        # Generic costs (applicable to all phases)
        cost += self._compute_generic_costs(proprio, action, cost_weights)

        return cost

    def _compute_lift_cost(
        self,
        task_state: torch.Tensor,
        next_task_state: torch.Tensor,
        action: torch.Tensor,
        cost_weights: Dict[str, float],
    ) -> torch.Tensor:
        """Compute cost for Phase 3 Lift.

        Goal: Maximize cable Z position (lift the cable up).
        """
        batch_size = task_state.shape[0]
        cost = torch.zeros(batch_size, device=self.device)

        # Cable Z position (using cable segments)
        # Task state structure: cable_segments (60D) + hook_pos (3D) + ee_pos (6D) + distances (5D)
        # But task_state is 44D, so it's likely compressed
        # Estimate cable center Z from indices 8-11 (center segment area)

        # Current cable Z (average of relevant indices)
        cable_z_indices = [8, 11, 14]  # Approximate Z positions in task state
        current_cable_z = task_state[:, cable_z_indices].mean(dim=1)
        next_cable_z = next_task_state[:, cable_z_indices].mean(dim=1)

        # Reward for increasing Z (negative cost)
        if "cable_z" in cost_weights:
            cable_z_change = next_cable_z - current_cable_z
            cost += cost_weights["cable_z"] * (-cable_z_change)  # Negative because higher is better

        # Reward for upward velocity
        if "cable_z_velocity" in cost_weights:
            velocity = next_cable_z - current_cable_z
            cost += cost_weights["cable_z_velocity"] * (-velocity)

        return cost

    def _compute_hook_approach_cost(
        self,
        task_state: torch.Tensor,
        next_task_state: torch.Tensor,
        proprio: torch.Tensor,
        next_proprio: torch.Tensor,
        cost_weights: Dict[str, float],
    ) -> torch.Tensor:
        """Compute cost for Phase 4 Hook Approach.

        Goal: Move cable toward hook while maintaining height.
        """
        batch_size = task_state.shape[0]
        cost = torch.zeros(batch_size, device=self.device)

        # Hook position from task state (indices 30-33)
        hook_start = TaskStateIndices.HOOK_POS_START
        hook_end = TaskStateIndices.HOOK_POS_END
        hook_pos = task_state[:, hook_start:hook_end]

        # Cable center position (estimate)
        cable_center = task_state[:, 9:12]  # Approximate
        next_cable_center = next_task_state[:, 9:12]

        # Distance to hook
        if "hook_distance" in cost_weights:
            current_dist = torch.norm(cable_center - hook_pos, dim=1)
            next_dist = torch.norm(next_cable_center - hook_pos, dim=1)
            cost += cost_weights["hook_distance"] * next_dist

        return cost

    def _compute_hook_placement_cost(
        self,
        task_state: torch.Tensor,
        next_task_state: torch.Tensor,
        cost_weights: Dict[str, float],
        target: Optional[Dict[str, float]] = None,
    ) -> torch.Tensor:
        """Compute cost for Phase 5 Hook Placement.

        Goal: Position cable directly above hook center.
        """
        batch_size = task_state.shape[0]
        cost = torch.zeros(batch_size, device=self.device)

        # Hook alignment (XY distance to hook center)
        hook_start = TaskStateIndices.HOOK_POS_START
        hook_xy = task_state[:, hook_start:hook_start+2]  # Hook X, Y

        cable_center_xy = task_state[:, 9:11]
        next_cable_center_xy = next_task_state[:, 9:11]

        if "hook_alignment" in cost_weights:
            alignment_error = torch.norm(next_cable_center_xy - hook_xy, dim=1)
            cost += cost_weights["hook_alignment"] * alignment_error

        return cost

    def _compute_generic_costs(
        self,
        proprio: torch.Tensor,
        action: torch.Tensor,
        cost_weights: Dict[str, float],
    ) -> torch.Tensor:
        """Compute generic costs applicable to all phases."""
        batch_size = proprio.shape[0]
        cost = torch.zeros(batch_size, device=self.device)

        # Joint smoothness (penalize large velocity)
        if "joint_smoothness" in cost_weights:
            # Use joint velocities from proprio
            left_vel = proprio[:, ProprioIndices.LEFT_JOINT_VEL]
            right_vel = proprio[:, ProprioIndices.RIGHT_JOINT_VEL]
            velocity_magnitude = torch.norm(left_vel, dim=1) + torch.norm(right_vel, dim=1)
            cost += cost_weights["joint_smoothness"] * velocity_magnitude

        # Action magnitude (penalize large actions)
        if "action_magnitude" in cost_weights:
            action_norm = torch.norm(action, dim=1)
            cost += cost_weights["action_magnitude"] * action_norm

        return cost

    def _select_elites(self, costs: torch.Tensor) -> torch.Tensor:
        """Select elite samples based on costs.

        Args:
            costs: [num_candidates] costs for each candidate

        Returns:
            elite_indices: Indices of elite samples
        """
        num_elites = int(self.config.num_candidates * self.config.elite_ratio)

        # Select samples with lowest cost
        _, elite_indices = torch.topk(costs, num_elites, largest=False)

        return elite_indices

    def _update_distribution(self, elite_actions: torch.Tensor):
        """Update action distribution based on elite samples.

        Args:
            elite_actions: [num_elites, horizon, action_dim]
        """
        # Update mean
        self.action_mean = elite_actions.mean(dim=0)

        # Update std with minimum for exploration
        self.action_std = elite_actions.std(dim=0)
        self.action_std = torch.clamp(self.action_std, min=0.005)

    def get_action_statistics(self) -> Dict[str, float]:
        """Get statistics about current action distribution."""
        if self.action_mean is None:
            return {}

        return {
            "mean_action_norm": self.action_mean.norm().item(),
            "mean_std": self.action_std.mean().item(),
            "max_std": self.action_std.max().item(),
        }


def create_mpc_controller(
    config: Optional[MPCConfig] = None,
    world_model_path: Optional[str] = None,
) -> MPCController:
    """Factory function to create MPC controller.

    Args:
        config: Optional MPC configuration
        world_model_path: Optional path to world model checkpoint

    Returns:
        Initialized MPC controller
    """
    if config is None:
        config = MPCConfig()

    if world_model_path is not None:
        config.world_model_path = world_model_path

    return MPCController(config)
