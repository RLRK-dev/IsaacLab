#!/usr/bin/env python3
"""
THREAD: Evaluation Script for Isaac Lab
========================================

This script evaluates trained THREAD policies on the Hook Hanging task.

Usage:
    # Basic evaluation
    python eval.py --checkpoint logs/THREAD_HookHanging/policy_final.pt
    
    # With video recording
    python eval.py --checkpoint logs/THREAD_HookHanging/policy_final.pt --video
    
    # Multiple episodes
    python eval.py --checkpoint logs/THREAD_HookHanging/policy_final.pt --num_episodes 100

Author: THREAD Research Team
Date: December 2025
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Sequence

import torch
import numpy as np

# Try to import Isaac Lab (optional for standalone testing)
try:
    from omni.isaac.lab.app import AppLauncher
    ISAAC_LAB_AVAILABLE = True
except ImportError:
    ISAAC_LAB_AVAILABLE = False


# =============================================================================
# Evaluation Configuration
# =============================================================================

class EvalConfig:
    """Evaluation configuration."""
    
    # Environment
    num_envs: int = 16  # Fewer envs for evaluation
    
    # Evaluation
    num_episodes: int = 100
    deterministic: bool = True  # Use mean action
    
    # Video
    record_video: bool = False
    video_fps: int = 30
    video_length: int = 500  # Max steps per video
    
    # Output
    output_dir: str = "eval_results"
    
    # Device
    device: str = "cuda:0"


# =============================================================================
# Metrics
# =============================================================================

class EpisodeMetrics:
    """Track metrics for a single episode."""
    
    def __init__(self):
        self.steps = 0
        self.total_reward = 0.0
        self.success = False
        
        # Phase completion tracking
        self.phases_completed = {
            "approach": False,
            "grasp": False,
            "lift": False,
            "move": False,
            "hang": False,
        }
        
        # Timing
        self.start_time = time.time()
        self.end_time = None
    
    def update(self, reward: float, info: dict):
        """Update metrics with step data."""
        self.steps += 1
        self.total_reward += reward
        
        # Update phase completion from info
        if "phase_completed" in info:
            for phase in info["phase_completed"]:
                self.phases_completed[phase] = True
    
    def finish(self, success: bool):
        """Mark episode as finished."""
        self.success = success
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """Episode duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def phases_completed_count(self) -> int:
        """Number of phases completed."""
        return sum(self.phases_completed.values())
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "steps": self.steps,
            "total_reward": self.total_reward,
            "success": self.success,
            "duration": self.duration,
            "phases_completed": self.phases_completed_count,
        }


class AggregateMetrics:
    """Aggregate metrics across multiple episodes."""
    
    def __init__(self):
        self.episodes: list[EpisodeMetrics] = []
    
    def add_episode(self, episode: EpisodeMetrics):
        """Add episode metrics."""
        self.episodes.append(episode)
    
    @property
    def num_episodes(self) -> int:
        return len(self.episodes)
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.num_episodes == 0:
            return 0.0
        return sum(ep.success for ep in self.episodes) / self.num_episodes * 100
    
    @property
    def mean_reward(self) -> float:
        """Mean total reward."""
        if self.num_episodes == 0:
            return 0.0
        return np.mean([ep.total_reward for ep in self.episodes])
    
    @property
    def mean_steps(self) -> float:
        """Mean episode steps."""
        if self.num_episodes == 0:
            return 0.0
        return np.mean([ep.steps for ep in self.episodes])
    
    @property
    def mean_duration(self) -> float:
        """Mean episode duration (seconds)."""
        if self.num_episodes == 0:
            return 0.0
        return np.mean([ep.duration for ep in self.episodes])
    
    @property
    def phase_completion_rates(self) -> dict[str, float]:
        """Phase completion rates as percentages."""
        if self.num_episodes == 0:
            return {}
        
        phases = ["approach", "grasp", "lift", "move", "hang"]
        rates = {}
        for phase in phases:
            completed = sum(ep.phases_completed[phase] for ep in self.episodes)
            rates[phase] = completed / self.num_episodes * 100
        return rates
    
    def print_summary(self):
        """Print evaluation summary."""
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        
        print(f"\nEpisodes: {self.num_episodes}")
        print(f"Success Rate: {self.success_rate:.1f}%")
        print(f"Mean Reward: {self.mean_reward:.2f}")
        print(f"Mean Steps: {self.mean_steps:.1f}")
        print(f"Mean Duration: {self.mean_duration:.2f}s")
        
        print("\nPhase Completion Rates:")
        for phase, rate in self.phase_completion_rates.items():
            print(f"  {phase.capitalize()}: {rate:.1f}%")
        
        # Success statistics
        successful_eps = [ep for ep in self.episodes if ep.success]
        if successful_eps:
            print(f"\nSuccessful Episodes:")
            print(f"  Mean Steps: {np.mean([ep.steps for ep in successful_eps]):.1f}")
            print(f"  Mean Reward: {np.mean([ep.total_reward for ep in successful_eps]):.2f}")
        
        print("\n" + "=" * 60)
    
    def save_results(self, path: str):
        """Save results to file."""
        import json
        
        results = {
            "num_episodes": self.num_episodes,
            "success_rate": self.success_rate,
            "mean_reward": self.mean_reward,
            "mean_steps": self.mean_steps,
            "phase_completion_rates": self.phase_completion_rates,
            "episodes": [ep.to_dict() for ep in self.episodes],
        }
        
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"[INFO] Results saved to: {path}")


# =============================================================================
# Evaluation Loop
# =============================================================================

def load_policy(checkpoint_path: str, device: torch.device):
    """Load trained policy from checkpoint."""
    from train import THREADActorCritic
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # Determine dimensions from checkpoint
    # This assumes checkpoint contains state_dict with known layer names
    if "policy_state_dict" in checkpoint:
        state_dict = checkpoint["policy_state_dict"]
    else:
        state_dict = checkpoint
    
    # Infer dimensions from first and last layers
    first_layer_weight = state_dict["actor.0.weight"]
    last_actor_weight = [v for k, v in state_dict.items() if "actor" in k and "weight" in k][-1]
    
    obs_dim = first_layer_weight.shape[1]
    action_dim = last_actor_weight.shape[0]
    
    print(f"[INFO] Inferred dimensions: obs={obs_dim}, action={action_dim}")
    
    # Create policy
    policy = THREADActorCritic(
        obs_dim=obs_dim,
        action_dim=action_dim,
    ).to(device)
    
    # Load weights
    policy.load_state_dict(state_dict)
    policy.eval()
    
    return policy


def evaluate_standalone(cfg: EvalConfig, checkpoint_path: str):
    """
    Standalone evaluation with simulated environment.
    
    Used for testing evaluation code without Isaac Sim.
    """
    print("=" * 60)
    print("THREAD Evaluation (Standalone Mode)")
    print("=" * 60)
    print("[WARNING] Running without Isaac Sim - using simulated data")
    
    device = torch.device(cfg.device if torch.cuda.is_available() else "cpu")
    
    # Create dummy policy
    from train import THREADActorCritic
    policy = THREADActorCritic(obs_dim=28, action_dim=8).to(device)
    policy.eval()
    
    # Metrics
    metrics = AggregateMetrics()
    
    # Simulated evaluation
    for ep in range(cfg.num_episodes):
        episode_metrics = EpisodeMetrics()
        
        # Simulate episode
        max_steps = 500
        for step in range(max_steps):
            # Random observation
            obs = torch.randn(1, 28, device=device)
            
            # Get action
            with torch.no_grad():
                action = policy.act(obs, deterministic=cfg.deterministic)
            
            # Simulate reward
            reward = np.random.randn() * 0.1
            episode_metrics.update(reward, {})
            
            # Random termination
            if np.random.rand() < 0.01:
                break
        
        # Random success
        success = np.random.rand() < 0.5
        episode_metrics.finish(success)
        metrics.add_episode(episode_metrics)
        
        if (ep + 1) % 10 == 0:
            print(f"Episode {ep + 1}/{cfg.num_episodes} - "
                  f"Current success rate: {metrics.success_rate:.1f}%")
    
    # Print results
    metrics.print_summary()
    
    # Save results
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.save_results(str(output_dir / "eval_results.json"))


def evaluate_isaac_lab(cfg: EvalConfig, checkpoint_path: str, args: argparse.Namespace):
    """
    Full evaluation with Isaac Lab environment.
    """
    # Launch Isaac Sim
    app_launcher = AppLauncher(args)
    simulation_app = app_launcher.app
    
    from omni.isaac.lab_tasks.utils.wrappers.rsl_rl import RslRlVecEnvWrapper
    from envs.hook_hanging_env import HookHangingEnv, HookHangingEnvCfg
    
    print("=" * 60)
    print("THREAD Evaluation (Isaac Lab Mode)")
    print("=" * 60)
    
    device = torch.device(cfg.device)
    
    # Create environment
    env_cfg = HookHangingEnvCfg()
    env_cfg.scene.num_envs = cfg.num_envs
    env = HookHangingEnv(cfg=env_cfg)
    env = RslRlVecEnvWrapper(env)
    
    # Load policy
    policy = load_policy(checkpoint_path, device)
    
    # Metrics
    metrics = AggregateMetrics()
    
    # Video recording setup
    if cfg.record_video:
        from omni.isaac.lab.utils.io import VideoRecorder
        video_recorder = VideoRecorder(
            output_dir=cfg.output_dir,
            fps=cfg.video_fps,
        )
    
    # Evaluation loop
    episodes_completed = 0
    episode_metrics = [EpisodeMetrics() for _ in range(cfg.num_envs)]
    
    obs = env.reset()
    
    while episodes_completed < cfg.num_episodes:
        # Get actions
        with torch.no_grad():
            obs_tensor = torch.as_tensor(obs, device=device, dtype=torch.float32)
            actions = policy.act(obs_tensor, deterministic=cfg.deterministic)
        
        # Step environment
        obs, rewards, dones, infos = env.step(actions.cpu().numpy())
        
        # Update metrics
        for i in range(cfg.num_envs):
            episode_metrics[i].update(rewards[i], infos[i] if isinstance(infos, list) else {})
            
            if dones[i]:
                # Check success
                success = infos[i].get("success", False) if isinstance(infos, list) else False
                episode_metrics[i].finish(success)
                
                metrics.add_episode(episode_metrics[i])
                episodes_completed += 1
                
                # Reset episode metrics
                episode_metrics[i] = EpisodeMetrics()
                
                if episodes_completed % 10 == 0:
                    print(f"Episode {episodes_completed}/{cfg.num_episodes} - "
                          f"Current success rate: {metrics.success_rate:.1f}%")
                
                if episodes_completed >= cfg.num_episodes:
                    break
        
        # Record video frame
        if cfg.record_video:
            video_recorder.add_frame()
    
    # Cleanup
    if cfg.record_video:
        video_recorder.save(f"eval_video_{episodes_completed}.mp4")
    
    env.close()
    simulation_app.close()
    
    # Print results
    metrics.print_summary()
    
    # Save results
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.save_results(str(output_dir / "eval_results.json"))


# =============================================================================
# Entry Point
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="THREAD Evaluation Script")
    
    # Checkpoint
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to policy checkpoint")
    
    # Environment
    parser.add_argument("--num_envs", type=int, default=16,
                        help="Number of parallel environments")
    
    # Evaluation
    parser.add_argument("--num_episodes", type=int, default=100,
                        help="Number of episodes to evaluate")
    parser.add_argument("--stochastic", action="store_true",
                        help="Use stochastic policy (sample actions)")
    
    # Video
    parser.add_argument("--video", action="store_true",
                        help="Record evaluation video")
    parser.add_argument("--video_fps", type=int, default=30,
                        help="Video FPS")
    
    # Output
    parser.add_argument("--output_dir", type=str, default="eval_results",
                        help="Output directory for results")
    
    # Device
    parser.add_argument("--device", type=str, default="cuda:0",
                        help="Device to use")
    
    # Mode
    parser.add_argument("--standalone", action="store_true",
                        help="Run in standalone mode without Isaac Sim")
    
    # Isaac Sim specific
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create config
    cfg = EvalConfig()
    cfg.num_envs = args.num_envs
    cfg.num_episodes = args.num_episodes
    cfg.deterministic = not args.stochastic
    cfg.record_video = args.video
    cfg.video_fps = args.video_fps
    cfg.output_dir = args.output_dir
    cfg.device = args.device
    
    # Print configuration
    print(f"\nCheckpoint: {args.checkpoint}")
    print(f"Num episodes: {cfg.num_episodes}")
    print(f"Deterministic: {cfg.deterministic}")
    print(f"Record video: {cfg.record_video}")
    print()
    
    # Run evaluation
    if args.standalone or not ISAAC_LAB_AVAILABLE:
        evaluate_standalone(cfg, args.checkpoint)
    else:
        evaluate_isaac_lab(cfg, args.checkpoint, args)


if __name__ == "__main__":
    main()
