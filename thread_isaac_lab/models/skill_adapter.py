# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""THREAD Skill Adapters with LoRA.

Skill-specific adapters on top of a frozen base actor (RSL-RL ActorCritic).
Each adapter is a lightweight module that modifies the base policy's behavior.

Architecture:
    [Base Actor backbone (frozen)] → latent (128D)
    [Base Actor head (frozen)]     → base_action (12D)
    [SkillAdapter (trainable)]     → action adjustment (12D)
    final_action = base_action + adjustment

    Critic and std are skill-specific (not shared).

Supported RL skills:
    - approach_cable: Approach cable with both arms (finger OPEN)
    - clamp: Close fingers to grasp cable
    - insert_into_clip: Push held cable into clip groove
    - unclamp: Open fingers to release cable from groove
    - aerial_regrasp: Approach cable mid-air for re-grasp

Scripted skills (TransportToClip, ReClamp, HalfUnclampRelease, ClipConfirm)
are handled by the Orchestrator and do not use SkillType.

Usage:
    runner = OnPolicyRunner(env, train_cfg, log_dir, device)
    apply_skill_adapter(runner, base_model_path, SkillType.INSERT_INTO_CLIP)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import torch
import torch.nn as nn
from torch import optim
from torch.distributions import Normal


class SkillType(Enum):
    """Supported RL skill types for 5-clip cable routing.

    Scripted skills (TransportToClip, ReClamp, HalfUnclampRelease, ClipConfirm)
    are handled directly by the Orchestrator and do not need SkillType entries.
    """

    APPROACH_CABLE = "approach_cable"
    CLAMP = "clamp"
    CLAMP_R = "clamp_r"
    CLAMP_L = "clamp_l"
    INSERT_INTO_CLIP = "insert_into_clip"
    UNCLAMP = "unclamp"
    AERIAL_REGRASP = "aerial_regrasp"


@dataclass
class SkillAdapterConfig:
    """Configuration for Skill Adapter."""

    # Base dimensions (RSL-RL ActorCritic 128-128 MLP)
    fusion_dim: int = 128
    action_dim: int = 12

    # LoRA parameters
    lora_rank: int = 8
    lora_alpha: float = 1.0
    lora_dropout: float = 0.0

    # Skill embedding
    use_skill_embedding: bool = True
    skill_embedding_dim: int = 16

    # Residual connection
    use_residual: bool = True

    # Extra obs dims beyond base model input (auto-detected by apply_skill_adapter)
    extra_obs_dim: int = 0

    # Env action dim (when env has more actions than base, e.g. 14D = 12D EE + 2D finger)
    env_action_dim: int = 0  # 0 = same as action_dim


class LoRALayer(nn.Module):
    """Low-Rank Adaptation layer.

    Output = (alpha/r) * (x @ A^T @ B^T)
    B initialized to zero → initial output is zero.
    """

    def __init__(self, input_dim: int, output_dim: int, rank: int = 8, alpha: float = 1.0, dropout: float = 0.0):
        super().__init__()
        self.lora_A = nn.Parameter(torch.randn(rank, input_dim) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(output_dim, rank))
        self.scaling = alpha / rank
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.dropout(x)
        return (x @ self.lora_A.T @ self.lora_B.T) * self.scaling


class SkillAdapter(nn.Module):
    """Skill-specific adapter using LoRA + MLP + gating.

    Takes latent from base policy backbone and base action from head,
    produces an action adjustment that is added to base_action.
    """

    def __init__(self, config: SkillAdapterConfig, skill_type: SkillType):
        super().__init__()
        self.config = config
        self.skill_type = skill_type

        # Skill embedding
        if config.use_skill_embedding:
            num_skills = len(SkillType)
            self.skill_embedding = nn.Embedding(num_skills, config.skill_embedding_dim)
            adapter_input_dim = config.fusion_dim + config.skill_embedding_dim + config.extra_obs_dim
        else:
            self.skill_embedding = None
            adapter_input_dim = config.fusion_dim + config.extra_obs_dim

        # Output action dim (env may have more actions than base, e.g. +2 finger cmds)
        out_action_dim = config.env_action_dim if config.env_action_dim > 0 else config.action_dim

        # LoRA path
        self.lora_policy = LoRALayer(
            input_dim=adapter_input_dim,
            output_dim=out_action_dim,
            rank=config.lora_rank,
            alpha=config.lora_alpha,
            dropout=config.lora_dropout,
        )

        # MLP path (extra capacity)
        self.skill_mlp = nn.Sequential(
            nn.Linear(adapter_input_dim, config.lora_rank * 2),
            nn.ReLU(),
            nn.Linear(config.lora_rank * 2, out_action_dim),
        )

        # Gate to blend LoRA and MLP paths
        self.gate = nn.Sequential(
            nn.Linear(adapter_input_dim, 1),
            nn.Sigmoid(),
        )

        # Zero-init MLP output for clean start
        nn.init.zeros_(self.skill_mlp[-1].weight)
        nn.init.zeros_(self.skill_mlp[-1].bias)

    def get_skill_index(self) -> int:
        return list(SkillType).index(self.skill_type)

    def forward(
        self, latent: torch.Tensor, base_action: torch.Tensor, extra_obs: torch.Tensor | None = None
    ) -> torch.Tensor:
        batch_size = latent.shape[0]

        if self.skill_embedding is not None:
            skill_idx = torch.full((batch_size,), self.get_skill_index(), device=latent.device, dtype=torch.long)
            skill_emb = self.skill_embedding(skill_idx)
            adapter_input = torch.cat([latent, skill_emb], dim=-1)
        else:
            adapter_input = latent

        if extra_obs is not None:
            adapter_input = torch.cat([adapter_input, extra_obs], dim=-1)

        lora_adj = self.lora_policy(adapter_input)
        mlp_adj = self.skill_mlp(adapter_input)
        gate = self.gate(adapter_input)
        total_adj = lora_adj + gate * mlp_adj

        if self.config.use_residual:
            if total_adj.shape[-1] > base_action.shape[-1]:
                # Pad base_action with zeros for extra dims (e.g. finger cmds)
                pad = torch.zeros(
                    base_action.shape[0], total_adj.shape[-1] - base_action.shape[-1], device=base_action.device
                )
                base_action = torch.cat([base_action, pad], dim=-1)
            return base_action + total_adj
        return total_adj


# ---------------------------------------------------------------------------
# RSL-RL compatible policy with skill adapter
# ---------------------------------------------------------------------------


class _ActorProxy:
    """Proxy to provide policy.actor(obs) and policy.actor.parameters() interface."""

    def __init__(self, policy: SkillAdaptedActorCritic):
        self._policy = policy

    def __call__(self, obs: torch.Tensor) -> torch.Tensor:
        return self._policy._get_adapted_action(obs)

    def parameters(self):
        # Only return adapter parameters, NOT critic or std.
        # BC optimizer should update the adapter (action output) only.
        return self._policy.adapter.parameters()


class SkillAdaptedActorCritic(nn.Module):
    """RSL-RL ActorCritic with frozen base + trainable skill adapter.

    Implements the same interface as rsl_rl.modules.ActorCritic so it can be
    used as a drop-in replacement in OnPolicyRunner / PPO.

    Structure:
        base_backbone (frozen):  obs → latent  (layers 0-3 of actor)
        base_head (frozen):      latent → base_action (layer 4 of actor)
        adapter (trainable):     (latent, base_action) → adapted_action
        skill_critic (trainable): obs → value
        std (trainable):         exploration noise
    """

    def __init__(
        self,
        base_actor: nn.Sequential,
        skill_type: SkillType,
        num_critic_obs: int,
        adapter_config: SkillAdapterConfig | None = None,
        base_obs_dim: int | None = None,
    ):
        super().__init__()

        if adapter_config is None:
            adapter_config = SkillAdapterConfig()

        # Split base actor into backbone and head
        # actor: [Linear, ELU, Linear, ELU, Linear] → backbone=[0:4], head=[4]
        self.base_backbone = nn.Sequential(*list(base_actor.children())[:-1])
        self.base_head = list(base_actor.children())[-1]
        for p in self.base_backbone.parameters():
            p.requires_grad = False
        for p in self.base_head.parameters():
            p.requires_grad = False

        # Obs dimension: base model may accept fewer dims than env provides
        self.base_obs_dim = base_obs_dim or base_actor[0].in_features

        # Skill adapter
        self.adapter = SkillAdapter(adapter_config, skill_type)

        # Skill-specific critic (independent from base)
        self.critic = nn.Sequential(
            nn.Linear(num_critic_obs, adapter_config.fusion_dim),
            nn.ELU(),
            nn.Linear(adapter_config.fusion_dim, adapter_config.fusion_dim),
            nn.ELU(),
            nn.Linear(adapter_config.fusion_dim, 1),
        )

        # Action noise (use env_action_dim if set, else action_dim)
        std_dim = adapter_config.env_action_dim if adapter_config.env_action_dim > 0 else adapter_config.action_dim
        self.std = nn.Parameter(0.5 * torch.ones(std_dim))
        self.distribution: Normal | None = None
        Normal.set_default_validate_args(False)

        # RSL-RL compatible actor proxy (for BC loss: policy.actor(obs), policy.actor.parameters())
        self.actor = _ActorProxy(self)

    def _get_adapted_action(self, observations: torch.Tensor) -> torch.Tensor:
        base_obs = observations[:, : self.base_obs_dim]
        extra_obs = observations[:, self.base_obs_dim :] if observations.shape[-1] > self.base_obs_dim else None
        with torch.no_grad():
            latent = self.base_backbone(base_obs)
            base_action = self.base_head(latent)
        return self.adapter(latent, base_action, extra_obs=extra_obs)

    # --- RSL-RL ActorCritic interface ---

    is_recurrent = False

    def reset(self, dones=None):
        pass

    def forward(self):
        raise NotImplementedError

    @property
    def action_mean(self):
        return self.distribution.mean

    @property
    def action_std(self):
        return self.distribution.stddev

    @property
    def entropy(self):
        return self.distribution.entropy().sum(dim=-1)

    def update_distribution(self, observations):
        mean = self._get_adapted_action(observations)
        std = torch.nan_to_num(self.std, nan=0.1).clamp(min=1e-6).expand_as(mean)
        self.distribution = Normal(mean, std)

    def act(self, observations, **kwargs):
        self.update_distribution(observations)
        return self.distribution.sample()

    def get_actions_log_prob(self, actions):
        return self.distribution.log_prob(actions).sum(dim=-1)

    def act_inference(self, observations):
        return self._get_adapted_action(observations)

    def evaluate(self, critic_observations, **kwargs):
        return self.critic(critic_observations)


class MultiSkillActorCritic(nn.Module):
    """RSL-RL compatible policy with switchable skill adapters.

    One frozen base backbone + N skill adapters. Use set_skill() to switch.
    For Phase 5 skill chaining.
    """

    def __init__(
        self,
        base_actor: nn.Sequential,
        num_critic_obs: int,
        adapter_config: SkillAdapterConfig | None = None,
        skills: list[SkillType] | None = None,
        base_obs_dim: int | None = None,
    ):
        super().__init__()

        if adapter_config is None:
            adapter_config = SkillAdapterConfig()
        if skills is None:
            skills = list(SkillType)

        # Frozen base
        self.base_backbone = nn.Sequential(*list(base_actor.children())[:-1])
        self.base_head = list(base_actor.children())[-1]
        for p in self.base_backbone.parameters():
            p.requires_grad = False
        for p in self.base_head.parameters():
            p.requires_grad = False

        # Obs dimension
        self.base_obs_dim = base_obs_dim or base_actor[0].in_features

        # Per-skill adapters and critics
        self.adapters = nn.ModuleDict({s.value: SkillAdapter(adapter_config, s) for s in skills})
        self.critics = nn.ModuleDict(
            {
                s.value: nn.Sequential(
                    nn.Linear(num_critic_obs, adapter_config.fusion_dim),
                    nn.ELU(),
                    nn.Linear(adapter_config.fusion_dim, adapter_config.fusion_dim),
                    nn.ELU(),
                    nn.Linear(adapter_config.fusion_dim, 1),
                )
                for s in skills
            }
        )

        self.std = nn.Parameter(0.5 * torch.ones(adapter_config.action_dim))
        self.distribution: Normal | None = None
        self.current_skill: SkillType | None = None
        Normal.set_default_validate_args(False)

    def set_skill(self, skill: SkillType):
        self.current_skill = skill

    def _get_adapted_action(self, observations: torch.Tensor, skill: SkillType | None = None) -> torch.Tensor:
        if skill is None:
            skill = self.current_skill
        assert skill is not None, "No skill set"
        base_obs = observations[:, : self.base_obs_dim]
        extra_obs = observations[:, self.base_obs_dim :] if observations.shape[-1] > self.base_obs_dim else None
        with torch.no_grad():
            latent = self.base_backbone(base_obs)
            base_action = self.base_head(latent)
        return self.adapters[skill.value](latent, base_action, extra_obs=extra_obs)

    # --- RSL-RL interface ---

    is_recurrent = False

    def reset(self, dones=None):
        pass

    def forward(self):
        raise NotImplementedError

    @property
    def action_mean(self):
        return self.distribution.mean

    @property
    def action_std(self):
        return self.distribution.stddev

    @property
    def entropy(self):
        return self.distribution.entropy().sum(dim=-1)

    def update_distribution(self, observations):
        mean = self._get_adapted_action(observations)
        std = torch.nan_to_num(self.std, nan=0.1).clamp(min=1e-6).expand_as(mean)
        self.distribution = Normal(mean, std)

    def act(self, observations, **kwargs):
        self.update_distribution(observations)
        return self.distribution.sample()

    def get_actions_log_prob(self, actions):
        return self.distribution.log_prob(actions).sum(dim=-1)

    def act_inference(self, observations):
        return self._get_adapted_action(observations)

    def evaluate(self, critic_observations, **kwargs):
        skill = self.current_skill
        assert skill is not None, "No skill set"
        return self.critics[skill.value](critic_observations)

    def save_adapter(self, skill: SkillType, path: str):
        """Save a single skill's adapter + critic weights."""
        state = {
            "adapter": self.adapters[skill.value].state_dict(),
            "critic": self.critics[skill.value].state_dict(),
            "std": self.std.data,
            "skill": skill.value,
        }
        torch.save(state, path)

    def load_adapter(self, skill: SkillType, path: str):
        """Load a single skill's adapter + critic weights."""
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        self.adapters[skill.value].load_state_dict(ckpt["adapter"])
        self.critics[skill.value].load_state_dict(ckpt["critic"])
        if "std" in ckpt:
            self.std.data.copy_(ckpt["std"])


# ---------------------------------------------------------------------------
# Phase 5-1b C3: MultiSkillActorCritic factory (A1 dispatch prerequisite)
# ---------------------------------------------------------------------------


def build_multi_skill_policy(
    base_model_path: str,
    adapter_paths: dict[SkillType, str] | None = None,
    adapter_config: SkillAdapterConfig | None = None,
    num_critic_obs: int | None = None,
    skills: list[SkillType] | None = None,
    device: str = "cpu",
) -> MultiSkillActorCritic:
    """Factory that builds a :class:`MultiSkillActorCritic` from checkpoints.

    Loads a frozen base actor, instantiates the multi-skill policy, and
    optionally populates individual skill adapters from per-skill
    checkpoints. Mirrors the loader pattern of :func:`apply_skill_adapter`
    but produces a standalone policy (no RSL-RL runner required) so the
    orchestrator can drive inference without a training harness.

    Args:
        base_model_path: Path to the base RSL-RL ActorCritic checkpoint
            (e.g. ``logs/gc_v31/model_200.pt``). The base actor is
            reconstructed from its ``model_state_dict`` and frozen.
        adapter_paths: Optional ``{SkillType: path}`` for per-skill adapter
            checkpoints previously saved by
            :meth:`MultiSkillActorCritic.save_adapter`. Unspecified skills
            retain freshly-initialised (near-zero) adapters.
        adapter_config: :class:`SkillAdapterConfig` (defaults to standard).
        num_critic_obs: Observation dim fed to each critic. Defaults to
            the base actor's input dim.
        skills: Skills to include. Defaults to all :class:`SkillType`
            members.
        device: Target device for the returned policy.

    Returns:
        A :class:`MultiSkillActorCritic` with the base frozen + any
        supplied adapters loaded, moved to ``device``.
    """
    ckpt = torch.load(base_model_path, map_location="cpu", weights_only=False)
    base_sd = ckpt["model_state_dict"]
    actor_sd = {k.replace("actor.", ""): v for k, v in base_sd.items() if k.startswith("actor.")}

    if "0.weight" not in actor_sd or "4.weight" not in actor_sd:
        raise ValueError(
            f"Base checkpoint {base_model_path} does not expose an RSL-RL "
            "3-layer ActorCritic structure (keys 0.weight / 2.weight / 4.weight)."
        )

    base_obs_dim = actor_sd["0.weight"].shape[1]
    hidden_dim = actor_sd["0.weight"].shape[0]
    base_action_dim = actor_sd["4.weight"].shape[0]

    base_actor = nn.Sequential(
        nn.Linear(base_obs_dim, hidden_dim),
        nn.ELU(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.ELU(),
        nn.Linear(hidden_dim, base_action_dim),
    )
    base_actor.load_state_dict(actor_sd)

    if adapter_config is None:
        adapter_config = SkillAdapterConfig()
    if num_critic_obs is None:
        num_critic_obs = base_obs_dim

    policy = MultiSkillActorCritic(
        base_actor=base_actor,
        num_critic_obs=num_critic_obs,
        adapter_config=adapter_config,
        skills=skills,
        base_obs_dim=base_obs_dim,
    ).to(device)

    if adapter_paths:
        for skill, path in adapter_paths.items():
            if skill.value not in policy.adapters:
                raise ValueError(
                    f"Adapter for {skill} requested but not present in "
                    f"MultiSkillActorCritic.adapters (skills={list(policy.adapters.keys())})."
                )
            policy.load_adapter(skill, path)

    return policy


# ---------------------------------------------------------------------------
# Integration with RSL-RL OnPolicyRunner
# ---------------------------------------------------------------------------


def apply_skill_adapter(
    runner, base_model_path: str, skill: SkillType, adapter_config: SkillAdapterConfig | None = None
):
    """Replace runner's policy with a SkillAdaptedActorCritic.

    Loads base actor from checkpoint, freezes it, creates skill adapter.

    Args:
        runner: RSL-RL OnPolicyRunner (already initialized).
        base_model_path: Path to base model checkpoint (e.g., GC v31 model_200.pt).
        skill: Which skill adapter to create.
        adapter_config: Adapter configuration (defaults to SkillAdapterConfig()).
    """
    old_policy = runner.alg.policy
    device = next(old_policy.parameters()).device
    num_critic_obs = old_policy.critic[0].in_features
    env_obs_dim = old_policy.actor[0].in_features

    # Load base actor weights
    ckpt = torch.load(base_model_path, map_location=device, weights_only=False)
    base_sd = ckpt["model_state_dict"]
    actor_sd = {k.replace("actor.", ""): v for k, v in base_sd.items() if k.startswith("actor.")}

    # Detect obs dimension mismatch between env and base model
    base_obs_dim = actor_sd["0.weight"].shape[1]
    extra_obs_dim = max(0, env_obs_dim - base_obs_dim)

    # Detect action dimension mismatch early (needed for base actor construction)
    base_action_dim = actor_sd["4.weight"].shape[0]
    env_action_dim = runner.env.num_actions
    action_mismatch = env_action_dim != base_action_dim

    if extra_obs_dim > 0 or action_mismatch:
        # Reconstruct base actor from checkpoint dims (obs and/or action mismatch)
        base_actor = nn.Sequential(
            nn.Linear(actor_sd["0.weight"].shape[1], actor_sd["0.weight"].shape[0]),
            nn.ELU(),
            nn.Linear(actor_sd["2.weight"].shape[1], actor_sd["2.weight"].shape[0]),
            nn.ELU(),
            nn.Linear(actor_sd["4.weight"].shape[1], actor_sd["4.weight"].shape[0]),
        )
        base_actor.load_state_dict(actor_sd)
        if extra_obs_dim > 0:
            print(f"[SkillAdapter] Obs split: env={env_obs_dim}D → base={base_obs_dim}D + extra={extra_obs_dim}D")
        if action_mismatch:
            print(
                f"[SkillAdapter] Action mismatch: base={base_action_dim}D, env={env_action_dim}D → rebuilt base actor"
            )
    else:
        old_policy.actor.load_state_dict(actor_sd)
        base_actor = old_policy.actor

    if adapter_config is None:
        adapter_config = SkillAdapterConfig()
    adapter_config.extra_obs_dim = extra_obs_dim

    # Set action extension if env needs more actions than base model
    if env_action_dim > base_action_dim:
        adapter_config.env_action_dim = env_action_dim
        print(f"[SkillAdapter] Action extend: base={base_action_dim}D → env={env_action_dim}D")

    # Create adapted policy
    policy = SkillAdaptedActorCritic(
        base_actor=base_actor,
        skill_type=skill,
        num_critic_obs=num_critic_obs,
        adapter_config=adapter_config,
        base_obs_dim=base_obs_dim,
    ).to(device)

    # Replace in runner
    runner.alg.policy = policy

    # Recreate optimizer with trainable params only
    trainable = [p for p in policy.parameters() if p.requires_grad]
    runner.alg.optimizer = optim.Adam(trainable, lr=runner.alg.learning_rate)

    # Report
    total = sum(p.numel() for p in policy.parameters())
    trainable_n = sum(p.numel() for p in trainable)
    frozen_n = total - trainable_n
    adapter_n = sum(p.numel() for p in policy.adapter.parameters())
    print(f"[SkillAdapter] Base: {base_model_path}")
    print(f"[SkillAdapter] Skill: {skill.value}")
    print(f"[SkillAdapter] Adapter params: {adapter_n}")
    pct = 100 * trainable_n / total
    print(f"[SkillAdapter] Total: {total}, trainable: {trainable_n} ({pct:.1f}%), frozen: {frozen_n}")
