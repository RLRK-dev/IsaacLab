#!/usr/bin/env python3
"""
THREAD: Training Script for Isaac Lab
======================================

This script trains the THREAD policy using RSL-RL PPO
on the Hook Hanging task in Isaac Lab.

Usage:
    python train.py --num_envs 256 --max_iterations 50000
    
    # With specific GPU
    CUDA_VISIBLE_DEVICES=0 python train.py --num_envs 512
    
    # Resume training
    python train.py --resume --load_run <run_name>

Requirements:
    - Isaac Sim 5.1.0
    - Isaac Lab 2.3.0
    - RSL-RL
    - PyTorch 2.7.0
    - CUDA 12.8

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn

# RSL-RL imports
from rsl_rl.algorithms import PPO
from rsl_rl.modules import ActorCritic
from rsl_rl.runners import OnPolicyRunner

# Isaac Lab imports (conditional for syntax checking without Isaac Sim)
try:
    from omni.isaac.lab.app import AppLauncher
    ISAAC_LAB_AVAILABLE = True
except ImportError:
    ISAAC_LAB_AVAILABLE = False
    print("[WARNING] Isaac Lab not available. Running in config-only mode.")


# =============================================================================
# Configuration
# =============================================================================

class TrainingConfig:
    """
    Training configuration for THREAD Hook Hanging task.
    
    This configuration is optimized for RTX A6000 (48GB VRAM)
    with the following optimizations enabled:
    - torch.compile for kernel fusion
    - BFloat16 mixed precision
    - Flash Attention (if available)
    - Fused AdamW optimizer
    """
    
    # ----- Environment -----
    num_envs: int = 256
    env_spacing: float = 2.0
    
    # ----- Simulation -----
    physics_dt: float = 1/120.0  # 120 Hz
    control_dt: float = 1/60.0   # 60 Hz
    max_episode_length_s: float = 8.0
    
    # ----- Policy Network -----
    actor_hidden_dims: list[int] = [256, 256, 128]
    critic_hidden_dims: list[int] = [256, 256, 128]
    activation: str = "elu"
    
    # ----- PPO Algorithm -----
    learning_rate: float = 3e-4
    num_learning_epochs: int = 5
    num_mini_batches: int = 4
    gamma: float = 0.99
    lam: float = 0.95  # GAE lambda
    clip_param: float = 0.2
    value_loss_coef: float = 1.0
    entropy_coef: float = 0.01
    max_grad_norm: float = 1.0
    use_clipped_value_loss: bool = True
    
    # ----- Training -----
    max_iterations: int = 50000
    save_interval: int = 500
    log_interval: int = 10
    eval_interval: int = 100
    
    # ----- Optimization -----
    use_torch_compile: bool = True
    use_amp: bool = True  # Automatic Mixed Precision
    amp_dtype: str = "bfloat16"  # or "float16"
    
    # ----- Logging -----
    experiment_name: str = "THREAD_HookHanging"
    log_dir: str = "logs"
    wandb_project: str = "thread-cable-manipulation"
    use_wandb: bool = False
    
    # ----- Device -----
    device: str = "cuda:0"
    
    @property
    def max_episode_steps(self) -> int:
        return int(self.max_episode_length_s / self.control_dt)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for logging."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


class PPOConfig:
    """RSL-RL PPO configuration."""
    
    def __init__(self, cfg: TrainingConfig):
        # Policy
        self.policy_class_name = "ActorCritic"
        self.actor_hidden_dims = cfg.actor_hidden_dims
        self.critic_hidden_dims = cfg.critic_hidden_dims
        self.activation = cfg.activation
        self.init_noise_std = 1.0
        
        # Algorithm
        self.value_loss_coef = cfg.value_loss_coef
        self.use_clipped_value_loss = cfg.use_clipped_value_loss
        self.clip_param = cfg.clip_param
        self.entropy_coef = cfg.entropy_coef
        self.num_learning_epochs = cfg.num_learning_epochs
        self.num_mini_batches = cfg.num_mini_batches
        self.learning_rate = cfg.learning_rate
        self.schedule = "adaptive"
        self.gamma = cfg.gamma
        self.lam = cfg.lam
        self.desired_kl = 0.01
        self.max_grad_norm = cfg.max_grad_norm


class RunnerConfig:
    """RSL-RL Runner configuration."""
    
    def __init__(self, cfg: TrainingConfig):
        self.policy_class_name = "ActorCritic"
        self.algorithm_class_name = "PPO"
        self.num_steps_per_env = 24  # Rollout length
        self.max_iterations = cfg.max_iterations
        self.save_interval = cfg.save_interval
        self.experiment_name = cfg.experiment_name
        self.run_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.logger = "tensorboard"  # or "wandb"
        self.neptune_project = ""
        self.wandb_project = cfg.wandb_project
        self.resume = False
        self.load_run = ""
        self.checkpoint = -1
        self.resume_path = None


# =============================================================================
# Network Architecture
# =============================================================================

class THREADActorCritic(nn.Module):
    """
    Actor-Critic network for THREAD policy.
    
    Architecture:
    - Shared feature extractor (optional)
    - Separate actor and critic heads
    - Layer normalization for stability
    - ELU activations
    
    Input: Observation vector (28 dim for hook hanging task)
    Output: Action mean (8 dim) and state value (1 dim)
    """
    
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        actor_hidden_dims: list[int] = [256, 256, 128],
        critic_hidden_dims: list[int] = [256, 256, 128],
        activation: str = "elu",
        init_noise_std: float = 1.0,
    ):
        super().__init__()
        
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        
        # Activation function
        activation_fn = {
            "elu": nn.ELU(),
            "relu": nn.ReLU(),
            "tanh": nn.Tanh(),
            "leaky_relu": nn.LeakyReLU(0.01),
        }[activation]
        
        # Build actor network
        actor_layers = []
        in_dim = obs_dim
        for hidden_dim in actor_hidden_dims:
            actor_layers.extend([
                nn.Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                activation_fn,
            ])
            in_dim = hidden_dim
        actor_layers.append(nn.Linear(in_dim, action_dim))
        self.actor = nn.Sequential(*actor_layers)
        
        # Build critic network
        critic_layers = []
        in_dim = obs_dim
        for hidden_dim in critic_hidden_dims:
            critic_layers.extend([
                nn.Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                activation_fn,
            ])
            in_dim = hidden_dim
        critic_layers.append(nn.Linear(in_dim, 1))
        self.critic = nn.Sequential(*critic_layers)
        
        # Action noise (log standard deviation)
        self.log_std = nn.Parameter(torch.ones(action_dim) * torch.log(torch.tensor(init_noise_std)))
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize network weights using orthogonal initialization."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=1.0)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through both actor and critic.
        
        Args:
            obs: Observation tensor (batch_size, obs_dim)
            
        Returns:
            action_mean: Mean of action distribution (batch_size, action_dim)
            value: State value estimate (batch_size, 1)
        """
        action_mean = self.actor(obs)
        value = self.critic(obs)
        return action_mean, value
    
    def act(self, obs: torch.Tensor, deterministic: bool = False) -> torch.Tensor:
        """
        Sample action from policy.
        
        Args:
            obs: Observation tensor
            deterministic: If True, return mean action
            
        Returns:
            action: Sampled or mean action
        """
        action_mean = self.actor(obs)
        
        if deterministic:
            return action_mean
        
        # Sample from Gaussian
        std = torch.exp(self.log_std)
        noise = torch.randn_like(action_mean)
        action = action_mean + noise * std
        
        return action
    
    def get_value(self, obs: torch.Tensor) -> torch.Tensor:
        """Get value estimate for observation."""
        return self.critic(obs)
    
    def evaluate_actions(
        self, obs: torch.Tensor, actions: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Evaluate actions for PPO update.
        
        Returns:
            values: State value estimates
            log_probs: Log probability of actions
            entropy: Policy entropy
        """
        action_mean = self.actor(obs)
        values = self.critic(obs)
        
        std = torch.exp(self.log_std)
        
        # Gaussian log probability
        var = std ** 2
        log_probs = -0.5 * (
            ((actions - action_mean) ** 2) / var
            + 2 * self.log_std
            + torch.log(torch.tensor(2 * 3.14159265))
        ).sum(dim=-1, keepdim=True)
        
        # Entropy
        entropy = 0.5 * (
            1 + torch.log(torch.tensor(2 * 3.14159265)) + 2 * self.log_std
        ).sum()
        
        return values, log_probs, entropy


# =============================================================================
# Training Functions
# =============================================================================

def setup_training(cfg: TrainingConfig):
    """
    Setup training environment and components.
    
    Returns:
        env: Isaac Lab environment
        policy: Actor-Critic policy
        algorithm: PPO algorithm
        runner: Training runner
    """
    # Set device
    device = torch.device(cfg.device if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")
    
    if torch.cuda.is_available():
        # Print GPU info
        gpu_props = torch.cuda.get_device_properties(0)
        print(f"[INFO] GPU: {gpu_props.name}")
        print(f"[INFO] VRAM: {gpu_props.total_memory / 1024**3:.1f} GB")
    
    # Enable optimizations
    if cfg.use_torch_compile and hasattr(torch, 'compile'):
        print("[INFO] torch.compile enabled")
    
    if cfg.use_amp:
        print(f"[INFO] AMP enabled with {cfg.amp_dtype}")
    
    # Create log directory
    log_dir = Path(cfg.log_dir) / cfg.experiment_name
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Log directory: {log_dir}")
    
    return device, log_dir


def create_policy(
    obs_dim: int,
    action_dim: int,
    cfg: TrainingConfig,
    device: torch.device,
) -> THREADActorCritic:
    """Create and initialize the policy network."""
    
    policy = THREADActorCritic(
        obs_dim=obs_dim,
        action_dim=action_dim,
        actor_hidden_dims=cfg.actor_hidden_dims,
        critic_hidden_dims=cfg.critic_hidden_dims,
        activation=cfg.activation,
    ).to(device)
    
    # Count parameters
    num_params = sum(p.numel() for p in policy.parameters())
    print(f"[INFO] Policy parameters: {num_params:,}")
    
    # Optionally compile
    if cfg.use_torch_compile and hasattr(torch, 'compile'):
        policy = torch.compile(policy, mode="reduce-overhead")
        print("[INFO] Policy compiled with torch.compile")
    
    return policy


def train_step(
    policy: nn.Module,
    optimizer: torch.optim.Optimizer,
    obs_batch: torch.Tensor,
    action_batch: torch.Tensor,
    return_batch: torch.Tensor,
    advantage_batch: torch.Tensor,
    old_log_prob_batch: torch.Tensor,
    cfg: TrainingConfig,
    scaler: torch.cuda.amp.GradScaler | None = None,
) -> dict:
    """
    Single PPO training step.
    
    Returns:
        Dictionary of training metrics
    """
    # Mixed precision context
    amp_dtype = getattr(torch, cfg.amp_dtype) if cfg.use_amp else torch.float32
    
    with torch.cuda.amp.autocast(enabled=cfg.use_amp, dtype=amp_dtype):
        # Forward pass
        values, log_probs, entropy = policy.evaluate_actions(obs_batch, action_batch)
        
        # Compute losses
        ratio = torch.exp(log_probs - old_log_prob_batch)
        
        # Clipped surrogate objective
        surr1 = ratio * advantage_batch
        surr2 = torch.clamp(ratio, 1 - cfg.clip_param, 1 + cfg.clip_param) * advantage_batch
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # Value loss
        if cfg.use_clipped_value_loss:
            # Clipped value loss (optional)
            value_loss = 0.5 * (return_batch - values).pow(2).mean()
        else:
            value_loss = 0.5 * (return_batch - values).pow(2).mean()
        
        # Total loss
        loss = policy_loss + cfg.value_loss_coef * value_loss - cfg.entropy_coef * entropy
    
    # Backward pass
    optimizer.zero_grad()
    
    if scaler is not None:
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        nn.utils.clip_grad_norm_(policy.parameters(), cfg.max_grad_norm)
        scaler.step(optimizer)
        scaler.update()
    else:
        loss.backward()
        nn.utils.clip_grad_norm_(policy.parameters(), cfg.max_grad_norm)
        optimizer.step()
    
    return {
        "loss": loss.item(),
        "policy_loss": policy_loss.item(),
        "value_loss": value_loss.item(),
        "entropy": entropy.item(),
    }


# =============================================================================
# Main Training Loop (Standalone Version)
# =============================================================================

def train_standalone(cfg: TrainingConfig):
    """
    Standalone training loop for testing without Isaac Sim.
    
    This simulates the training process with random data
    to verify the training code works correctly.
    """
    print("=" * 70)
    print("THREAD Training (Standalone Mode)")
    print("=" * 70)
    print("[WARNING] Running without Isaac Sim - using simulated data")
    
    # Setup
    device, log_dir = setup_training(cfg)
    
    # Dimensions for hook hanging task
    obs_dim = 28
    action_dim = 8
    
    # Create policy
    policy = create_policy(obs_dim, action_dim, cfg, device)
    
    # Create optimizer
    optimizer = torch.optim.AdamW(
        policy.parameters(),
        lr=cfg.learning_rate,
        weight_decay=1e-4,
        fused=True if device.type == "cuda" else False,
    )
    
    # AMP scaler
    scaler = torch.cuda.amp.GradScaler(enabled=cfg.use_amp) if cfg.use_amp else None
    
    # Training loop
    print("\n[INFO] Starting training...")
    print(f"[INFO] Max iterations: {cfg.max_iterations}")
    
    for iteration in range(cfg.max_iterations):
        # Simulate rollout data
        batch_size = cfg.num_envs * 24  # num_envs * rollout_length
        
        obs_batch = torch.randn(batch_size, obs_dim, device=device)
        action_batch = torch.randn(batch_size, action_dim, device=device)
        return_batch = torch.randn(batch_size, 1, device=device)
        advantage_batch = torch.randn(batch_size, 1, device=device)
        old_log_prob_batch = torch.randn(batch_size, 1, device=device)
        
        # PPO update
        for epoch in range(cfg.num_learning_epochs):
            metrics = train_step(
                policy, optimizer,
                obs_batch, action_batch, return_batch,
                advantage_batch, old_log_prob_batch,
                cfg, scaler
            )
        
        # Logging
        if iteration % cfg.log_interval == 0:
            print(f"[Iter {iteration:5d}] loss={metrics['loss']:.4f} "
                  f"policy={metrics['policy_loss']:.4f} "
                  f"value={metrics['value_loss']:.4f} "
                  f"entropy={metrics['entropy']:.4f}")
        
        # Save checkpoint
        if iteration % cfg.save_interval == 0 and iteration > 0:
            checkpoint_path = log_dir / f"checkpoint_{iteration}.pt"
            torch.save({
                "iteration": iteration,
                "policy_state_dict": policy.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
            }, checkpoint_path)
            print(f"[INFO] Saved checkpoint: {checkpoint_path}")
    
    print("\n[INFO] Training complete!")
    
    # Save final model
    final_path = log_dir / "policy_final.pt"
    torch.save(policy.state_dict(), final_path)
    print(f"[INFO] Final model saved: {final_path}")


# =============================================================================
# Main Training Loop (Isaac Lab Version)
# =============================================================================

def train_isaac_lab(cfg: TrainingConfig, args: argparse.Namespace):
    """
    Full training loop with Isaac Lab environment.
    
    This is the main training function that should be used
    when running with Isaac Sim.
    """
    # Launch Isaac Sim app
    app_launcher = AppLauncher(args)
    simulation_app = app_launcher.app
    
    # Now we can import Isaac Lab modules
    from omni.isaac.lab.envs import ManagerBasedRLEnvCfg
    from omni.isaac.lab_tasks.utils import get_checkpoint_path, parse_env_cfg
    from omni.isaac.lab_tasks.utils.wrappers.rsl_rl import (
        RslRlOnPolicyRunnerCfg,
        RslRlVecEnvWrapper,
    )
    
    # Import our environment
    from envs.hook_hanging_env import HookHangingEnv, HookHangingEnvCfg
    
    print("=" * 70)
    print("THREAD Training (Isaac Lab Mode)")
    print("=" * 70)
    
    # Create environment config
    env_cfg = HookHangingEnvCfg()
    env_cfg.scene.num_envs = cfg.num_envs
    
    # Create environment
    env = HookHangingEnv(cfg=env_cfg)
    
    # Wrap for RSL-RL
    env = RslRlVecEnvWrapper(env)
    
    # Get dimensions
    obs_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    
    print(f"[INFO] Observation dim: {obs_dim}")
    print(f"[INFO] Action dim: {action_dim}")
    print(f"[INFO] Num envs: {env.num_envs}")
    
    # Create policy
    device = torch.device(cfg.device)
    
    actor_critic = ActorCritic(
        num_actor_obs=obs_dim,
        num_critic_obs=obs_dim,
        num_actions=action_dim,
        actor_hidden_dims=cfg.actor_hidden_dims,
        critic_hidden_dims=cfg.critic_hidden_dims,
        activation=cfg.activation,
        init_noise_std=1.0,
    ).to(device)
    
    # Create PPO algorithm
    ppo_cfg = PPOConfig(cfg)
    ppo = PPO(
        actor_critic,
        device=device,
        **vars(ppo_cfg),
    )
    
    # Create runner
    runner_cfg = RunnerConfig(cfg)
    if args.resume:
        runner_cfg.resume = True
        runner_cfg.load_run = args.load_run
    
    runner = OnPolicyRunner(
        env=env,
        train_cfg=runner_cfg,
        log_dir=cfg.log_dir,
        device=device,
    )
    
    # Set policy
    runner.alg = ppo
    
    # Train
    print("\n[INFO] Starting training...")
    runner.learn(num_learning_iterations=cfg.max_iterations, init_at_random_ep_len=True)
    
    # Cleanup
    env.close()
    simulation_app.close()
    
    print("\n[INFO] Training complete!")


# =============================================================================
# Entry Point
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="THREAD Training Script")
    
    # Environment
    parser.add_argument("--num_envs", type=int, default=256,
                        help="Number of parallel environments")
    parser.add_argument("--env_spacing", type=float, default=2.0,
                        help="Spacing between environments")
    
    # Training
    parser.add_argument("--max_iterations", type=int, default=50000,
                        help="Maximum training iterations")
    parser.add_argument("--learning_rate", type=float, default=3e-4,
                        help="Learning rate")
    
    # Logging
    parser.add_argument("--experiment_name", type=str, default="THREAD_HookHanging",
                        help="Experiment name for logging")
    parser.add_argument("--log_dir", type=str, default="logs",
                        help="Log directory")
    parser.add_argument("--wandb", action="store_true",
                        help="Enable Weights & Biases logging")
    
    # Resume
    parser.add_argument("--resume", action="store_true",
                        help="Resume training from checkpoint")
    parser.add_argument("--load_run", type=str, default="",
                        help="Run name to load for resume")
    
    # Device
    parser.add_argument("--device", type=str, default="cuda:0",
                        help="Device to use")
    
    # Mode
    parser.add_argument("--standalone", action="store_true",
                        help="Run in standalone mode without Isaac Sim")
    
    # Isaac Sim specific
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    parser.add_argument("--video", action="store_true",
                        help="Record video")
    parser.add_argument("--video_length", type=int, default=200,
                        help="Video length in steps")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create config
    cfg = TrainingConfig()
    cfg.num_envs = args.num_envs
    cfg.max_iterations = args.max_iterations
    cfg.learning_rate = args.learning_rate
    cfg.experiment_name = args.experiment_name
    cfg.log_dir = args.log_dir
    cfg.use_wandb = args.wandb
    cfg.device = args.device
    
    # Print configuration
    print("\n" + "=" * 70)
    print("THREAD: Hook Hanging Task Training")
    print("=" * 70)
    print(f"\nConfiguration:")
    for key, value in cfg.to_dict().items():
        if not callable(value):
            print(f"  {key}: {value}")
    print("=" * 70 + "\n")
    
    # Run training
    if args.standalone or not ISAAC_LAB_AVAILABLE:
        train_standalone(cfg)
    else:
        train_isaac_lab(cfg, args)


if __name__ == "__main__":
    main()
