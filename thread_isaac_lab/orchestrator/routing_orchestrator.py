# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Routing Orchestrator for 5-clip dual-arm cable routing.

Chains RL skills and scripted skills to route a cable through 5 clips.
Handles observation/action transforms (clip-relative, mirror) per clip.

Design doc: thread-vault/07-Design/RL-Routing-Design.md §14.

Routing sequence:
    C1:     AC -> Clamp -> Transport -> IC -> Unclamp
    C2-C5:  Unclamp -> Rise -> ReClamp/L -> AR -> Transport -> IC(mirror)

World-count contract (Phase 5-1b C5):
    :class:`RoutingOrchestrator` is designed for **single-world execution**
    (``num_envs == 1``). The snapshot/restore cascade, ``clip_status``
    bookkeeping, and the (deferred) recovery engine all assume a scalar
    STEP index. Multi-world routing is deferred to Phase 5-2+, which will
    require: per-world STEP index tensor, per-world snapshot indexing, and
    a divergent-done-worlds strategy (see spec §14 future work).

Termination and timeouts contract (Phase 5-1b C9):
    When the (deferred) recovery engine maps an env outcome to a
    :class:`~thread_isaac_lab.skills.scripted_skills.SkillResult`, it
    MUST NOT set ``extras["time_outs"] = True`` for orchestrator-initiated
    truncations (CABLE_DROP / EXPLOSION / FAIL). Only the env's
    ``MAX_EPISODE_STEPS`` boundary may set ``time_outs``. This preserves
    the invariant required by prohibited.md ("timeouts 汚染禁止") so that
    RSL-RL PPO value bootstrapping does not fire on terminal states.
    Violating this invariant previously caused value_loss to explode
    105x (see vault log 2026-04-08 BUG-1).
"""

from __future__ import annotations

import os
import sys
from enum import Enum

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "configs"))
from task_config import (
    CLIP_POSITIONS,
    FINGER_STEP_SIZE,
    GROOVE_CENTER_Z,
    K_CLAMP,
    T_ALIGN,
    T_DIST,
    T_FINGER,
    TABLE_HEIGHT,
)

from ..models.skill_adapter import MultiSkillActorCritic, SkillType
from ..skills.result import SkillResult
from ..skills.snapshot import SnapshotManager, StateSnapshot
from ..skills.step_table import SkillName
from ..transforms.skill_transforms import mirror_action, mirror_obs, to_clip_relative

# ---------------------------------------------------------------------------
# Phase 5-1b C1: SkillName → SkillType resolution (A1 dispatch prerequisite)
# ---------------------------------------------------------------------------

# Static SkillName → SkillType map. Scripted/wait skills map to None (handled
# by scripted dispatch). The bimanual CLAMP at STEP 4 uses :attr:`SkillType.CLAMP`;
# the C2-C5 R-arm-only CLAMP at STEPs 13/21/29/37 resolves to
# :attr:`SkillType.CLAMP_R` via :func:`resolve_skill_type`.
_SKILL_NAME_TO_TYPE: dict[SkillName, SkillType | None] = {
    SkillName.APPROACH_CABLE: SkillType.APPROACH_CABLE,
    SkillName.CLAMP: SkillType.CLAMP,
    SkillName.INSERT_INTO_CLIP: SkillType.INSERT_INTO_CLIP,
    SkillName.UNCLAMP: SkillType.UNCLAMP,
    SkillName.AERIAL_REGRASP: SkillType.AERIAL_REGRASP,
    SkillName.TRANSPORT: None,
    SkillName.RECLAMP_L: None,
    SkillName.HALF_UNCLAMP_RELEASE: None,
    SkillName.CLIP_CONFIRM: None,
}

# STEPs at which SkillName.CLAMP refers to R-arm-only CLAMP (C2-C5 regrasp)
# rather than bimanual CLAMP (STEP 4 / Phase A initial grasp).
#
# Per :func:`step_table._build_clip_routing` (step_table.py:152-179), each
# C2-C5 routing block is an 8-STEP pattern starting at ``step_offset``
# (offsets 11/19/27/35), with the RL CLAMP at ``step_offset + 3``
# (= STEPs 14/22/30/38). The previous value ``{13, 21, 29, 37}`` was an
# off-by-one referencing the AERIAL_REGRASP STEPs (``step_offset + 2``);
# under that constant ``SkillType.CLAMP_R`` was never dispatched at runtime
# because at AR STEPs the SkillName is ``AERIAL_REGRASP`` (so the CLAMP
# branch in :func:`resolve_skill_type` short-circuited). See
# ``memory/project_orchestrator_clamp_r_off_by_one_bug.md`` and
# ``memory/project_clamp_r_audit_result_2026-04-25.md`` (Blocker B1).
_R_ARM_ONLY_CLAMP_STEPS: frozenset[int] = frozenset({14, 22, 30, 38})


def resolve_skill_type(skill: SkillName, step_id: int) -> SkillType | None:
    """Map a :class:`SkillName` to the RL :class:`SkillType` for a given STEP.

    Args:
        skill: STEP table skill identifier.
        step_id: 1..43 routing STEP id (used for context-sensitive CLAMP).

    Returns:
        The matching :class:`SkillType`, or ``None`` for scripted/wait
        skills that the orchestrator dispatches via scripted helpers.
    """
    if skill == SkillName.CLAMP and step_id in _R_ARM_ONLY_CLAMP_STEPS:
        return SkillType.CLAMP_R
    return _SKILL_NAME_TO_TYPE.get(skill)


# ---------------------------------------------------------------------------
# Phase 5-1b C4: Per-skill env action_dim matrix (A1 dispatch prerequisite)
# ---------------------------------------------------------------------------

# Env-side ``num_actions`` per RL skill (source grep 2026-04-25):
#   APPROACH_CABLE : 12  (newton_approach_cable_env.py:216)
#   AERIAL_REGRASP : 12  (newton_aerial_regrasp_env.py:241)
#   INSERT_INTO_CLIP: 12 (newton_insert_clip_env.py:247)
#   CLAMP / CLAMP_R / CLAMP_L: 14 (newton_clamp_env.py:197 — 12D EE + 2D finger)
#   UNCLAMP        : 4   (newton_unclamp_env.py:232 — finger-only; spec §14.7
#                          classifies Unclamp as scripted, so orchestrator should
#                          NOT dispatch it as RL. The entry is retained because
#                          :class:`SkillType.UNCLAMP` is still referenced by
#                          ``train_unclamp.py`` and related tests.)
#
# Spec §14.6 calls for a unified 12D action across all RL skills, but the
# current env files have not been aligned. Until the envs are refactored
# (Phase 5-2+ scope), the orchestrator zero-pads the 12D policy output to
# fit the env's ``num_actions``.
_ENV_ACTION_DIM_BY_SKILL_TYPE: dict[SkillType, int] = {
    SkillType.APPROACH_CABLE: 12,
    SkillType.CLAMP: 14,
    SkillType.CLAMP_R: 14,
    SkillType.CLAMP_L: 14,
    SkillType.INSERT_INTO_CLIP: 12,
    SkillType.UNCLAMP: 4,
    SkillType.AERIAL_REGRASP: 12,
}


def env_action_dim_for(skill: SkillType) -> int:
    """Return the env-side ``num_actions`` expected for an RL skill."""
    return _ENV_ACTION_DIM_BY_SKILL_TYPE[skill]


def expand_action_for_env(action_12d: torch.Tensor, skill: SkillType) -> torch.Tensor:
    """Zero-pad a 12D policy action to the env's ``num_actions`` for ``skill``.

    The orchestrator policy always emits a 12D action (spec §14.6). For
    envs whose ``num_actions`` exceeds 12 (e.g. CLAMP's 14D = 12 EE + 2
    finger), the extra channels are zero-padded; the env's internal
    finger auto-close logic supplies the real finger commands.

    Attempting to expand for :attr:`SkillType.UNCLAMP` raises
    :class:`ValueError` because Unclamp is scripted per spec §14.7 and
    must be dispatched via the scripted path rather than RL.

    Args:
        action_12d: Policy output, shape ``[..., 12]``.
        skill: Target RL skill.

    Returns:
        Action tensor of shape ``[..., env_num_actions]``.

    Raises:
        ValueError: For :attr:`SkillType.UNCLAMP` or unexpected dims.
    """
    if skill == SkillType.UNCLAMP:
        raise ValueError(
            "UNCLAMP is scripted per spec §14.7; orchestrator must not "
            "dispatch it as RL. Use scripted_skills.half_unclamp_release "
            "(RECLAMP_L / HALF_UNCLAMP_RELEASE scripted path)."
        )

    if action_12d.shape[-1] != 12:
        raise ValueError(f"expand_action_for_env expects a 12D action, got shape {tuple(action_12d.shape)}.")

    target_dim = env_action_dim_for(skill)
    if target_dim == 12:
        return action_12d
    if target_dim == 14:
        pad_shape = (*action_12d.shape[:-1], 2)
        pad = torch.zeros(pad_shape, dtype=action_12d.dtype, device=action_12d.device)
        return torch.cat([action_12d, pad], dim=-1)

    raise ValueError(
        f"Unsupported env_action_dim={target_dim} for skill {skill}. "
        "Update _ENV_ACTION_DIM_BY_SKILL_TYPE after an env refactor."
    )


def policy_action_to_env_action(
    policy_action: torch.Tensor,
    *,
    skill: SkillType,
    env_action_dim: int,
    policy_action_dim: int | None = None,
) -> torch.Tensor:
    """Map policy action output to the exact environment action dimension.

    Native matching dimensions pass through unchanged. Existing CLAMP adapter
    policies retain the legacy 12D-to-14D padding behavior. All other
    mismatches fail hard so chain-context evaluation cannot silently measure a
    padded or truncated proxy.
    """

    if policy_action.ndim < 1:
        raise ValueError("policy_action must have at least one dimension.")

    observed_policy_dim = int(policy_action.shape[-1])
    expected_policy_dim = observed_policy_dim if policy_action_dim is None else int(policy_action_dim)
    if observed_policy_dim != expected_policy_dim:
        raise ValueError(
            f"Policy action shape has {observed_policy_dim} dims but policy_action_dim={expected_policy_dim}."
        )

    env_action_dim = int(env_action_dim)
    if expected_policy_dim == env_action_dim:
        return policy_action

    if expected_policy_dim == 12 and env_action_dim == 14 and skill in (
        SkillType.CLAMP,
        SkillType.CLAMP_R,
        SkillType.CLAMP_L,
    ):
        return expand_action_for_env(policy_action, skill)

    raise ValueError(
        f"Unsupported action dimension mapping for {skill.value}: "
        f"policy_dim={expected_policy_dim}, env_dim={env_action_dim}."
    )


# ---------------------------------------------------------------------------
# Phase 5-1b extension (Audit B2): R-arm-only L-arm action mask
# ---------------------------------------------------------------------------

# Skills that drive only the R arm; the L arm is held in a pre-clamped state
# (e.g. post-RECLAMP_L at C2-C5 STEP {14, 22, 30, 38}) and must not be
# disturbed by policy output.
#
# :attr:`SkillType.CLAMP_L` is intentionally NOT included: per
# ``project_orchestration_design.md`` H2 the L-arm RECLAMP is scripted via
# ``RECLAMP_L`` (``scripted_skills.reclamp_left``), not RL, so
# :attr:`SkillType.CLAMP_L` is never dispatched from the orchestrator. If a
# future Phase 5-X invokes CLAMP_L, extend this set together with the
# corresponding mask logic (would need to zero ``[..., 0:6]`` instead of
# ``[..., 6:12]``).
_L_ARM_MASK_SKILLS: frozenset[SkillType] = frozenset({SkillType.CLAMP_R})


def mask_l_arm_action_if_needed(action: torch.Tensor, skill: SkillType) -> torch.Tensor:
    """Zero L-arm EE channels ``[..., 6:12]`` for R-arm-only RL skills.

    The grip env's :meth:`_apply_actions_batch`
    (``newton_grip_env.py:1428-1531``) applies ``action[..., 6:12]`` to
    the L-arm EE target unconditionally when ``dual_arm=True``. Audit
    Blocker B2 (see ``memory/project_clamp_r_audit_result_2026-04-25.md``)
    flagged that nothing in the orchestrator or env masks these channels
    for :attr:`SkillType.CLAMP_R`, so a CLAMP_R policy output can drive
    the L arm away from the post-RECLAMP_L grip and break the routing
    handoff.

    This helper applies the mask in the orchestrator's hot path (called
    after :func:`expand_action_for_env` and before ``env.step``), so the
    env API stays unchanged.

    Args:
        action: Action tensor post-:func:`expand_action_for_env`, shape
            ``[..., env_num_actions]``. For CLAMP_R this is 14D
            (``[0:6]`` R EE, ``[6:12]`` L EE, ``[12]`` R finger pad,
            ``[13]`` L finger pad).
        skill: The dispatched RL skill.

    Returns:
        For skills in :data:`_L_ARM_MASK_SKILLS` a new tensor with
        ``[..., 6:12]`` zeroed (other channels preserved). Otherwise the
        input tensor is returned unchanged (no clone, no allocation).
    """
    if skill not in _L_ARM_MASK_SKILLS:
        return action
    masked = action.clone()
    masked[..., 6:12] = 0.0
    return masked


# ---------------------------------------------------------------------------
# Phase 5-1b extension (Audit B6): Scripted finger close for CLAMP*
# ---------------------------------------------------------------------------

# Skills that drive a CLAMP-style finger close. Both bimanual CLAMP (STEP 4,
# R + L) and R-arm-only CLAMP_R (C2-C5 STEPs 14/22/30/38, R only) require
# scripted finger commands because :func:`expand_action_for_env` zero-pads
# the policy's 12D output to 14D, leaving ``action[..., 12]`` (R finger pad)
# at 0. The grip env's dual-arm explicit-finger branch
# (``newton_grip_env.py:1565-1574``) interprets that 0 as "no finger delta",
# so the R finger stays at ``FINGER_OPEN_POS`` and ``clamp_r_ok`` (which
# requires ``finger_r < CLAMP_FINGER_THRESH = T_FINGER = 12 mm`` per
# ``newton_grip_env.py:1174-1178``) can never fire. See
# ``memory/project_clamp_r_b6_finger_deadlock_2026-04-25.md`` for the full
# trace and F1-F4 trade-off (F3 selected by Rs Item 1 batch decision
# 2026-04-25; see ``memory/project_phase5_3_batch_decisions_2026-04-25.md``).
#
# .. note::
#     This is a **runtime-only** scripted shortcut. The policy never learns
#     finger control via PPO under F3 because BC supervision sets
#     ``action[..., 12:14] = 0`` and F3 overrides the policy's output at
#     dispatch time only — the policy gradient on those channels stays at
#     init noise. Long-term, finger control should move to the policy via
#     per-skill 14D adapter (F1) or skill_adapter wrapper (F4). Reopen
#     this design after Phase 5-3 completes and CLAMP wet-run S3
#     stabilizes; remove :func:`apply_finger_close_if_needed` once policy
#     outputs include finger pads natively.
_FINGER_SCRIPT_SKILLS: frozenset[SkillType] = frozenset({SkillType.CLAMP, SkillType.CLAMP_R})

# Threshold (per-arm two-joint sum) below which the scripted close stops
# emitting positive commands. Set 2 mm below ``T_FINGER`` (= 12 mm) so the
# strict ``finger_r < T_FINGER`` success comparison fires deterministically:
# the env decreases the finger sum by ``2 * FINGER_CMD_SCALE = 2 mm`` per
# RL step (1 mm/joint × 2 joints), so a target of 10 mm leaves a one-step
# margin past the threshold rather than landing exactly on it.
_FINGER_CLOSE_TARGET: float = T_FINGER - 2.0 * FINGER_STEP_SIZE  # 0.010 m

# Close-cmd magnitude. The env's explicit-finger branch applies
# ``joint_new = joint - cmd * FINGER_CMD_SCALE``, so cmd = +1.0 closes by
# ``FINGER_CMD_SCALE = FINGER_STEP_SIZE = 1 mm`` per joint per step.
# Mirrors MPPI demo generator Option B
# (``generate_demos_mppi_m3_grip.py:786-805``).
_FINGER_CLOSE_CMD: float = 1.0

# Obs-tensor indices for finger openings under
# :meth:`NewtonGripEnv._compute_obs_dual_arm` (45D layout).
# See ``newton_grip_env.py:1071`` (R) and ``newton_grip_env.py:1074`` (L).
# Both expose ``fk_jq[FRANKA_NUM_JOINTS+7] + fk_jq[FRANKA_NUM_JOINTS+8]``
# (R) and ``fk_jq[7] + fk_jq[8]`` (L), matching the success-condition
# convention in :meth:`NewtonGripEnv._compute_rewards_clamp` line 1143-1144.
_GRIP_OBS_R_FINGER_IDX: int = 7
_GRIP_OBS_L_FINGER_IDX: int = 15


def apply_finger_close_if_needed(
    action: torch.Tensor,
    skill: SkillType,
    obs: torch.Tensor | None,
) -> torch.Tensor:
    """Override CLAMP* finger pad commands with a scripted close.

    F3 fixes the runtime R-finger close mechanism. Full CLAMP_R success at
    STEPs 14/22/30/38 still requires Blockers B4 (per-clip target seg
    refresh) and B5 (per-arm success path). For STEP 4 (bimanual CLAMP),
    F3 alone restores the success path. **F3 is necessary but not
    sufficient for B6.**

    Reads finger opening from the env observation tensor at
    :data:`_GRIP_OBS_R_FINGER_IDX` / :data:`_GRIP_OBS_L_FINGER_IDX` rather
    than via an env getter — keeps the env file untouched (CC#3 Option D
    TOUCH FORBIDDEN strict compliance preserved).

    Args:
        action: Action tensor post-:func:`mask_l_arm_action_if_needed`,
            shape ``[..., 14]`` for CLAMP* envs.
        skill: Dispatched RL skill.
        obs: Env observation tensor. For dual_arm grip env this is the
            45D tensor whose indices 7 and 15 hold the per-arm finger
            openings (sum of two finger joints). ``None`` is tolerated
            for non-Newton callers (unit tests without env state) — the
            function returns the input action unchanged in that case.

    Returns:
        For ``skill ∈ {CLAMP, CLAMP_R}``, an action tensor with the
        finger pads overridden according to the scripted close logic.
        For other skills the input is returned unchanged (identity, no
        clone).

    Raises:
        AssertionError: If ``skill`` is in :data:`_FINGER_SCRIPT_SKILLS`
            but ``action.shape[-1] != 14`` (catches per-arm 6D config
            errors before they manifest as :class:`IndexError`).
    """
    if skill not in _FINGER_SCRIPT_SKILLS:
        return action
    if obs is None:
        return action

    assert action.shape[-1] == 14, (
        f"apply_finger_close_if_needed expects dual_arm 14D action, got shape {tuple(action.shape)}"
    )

    out = action.clone()

    # R finger: always scripted-closed for CLAMP*.
    r_opening = float(obs[0, _GRIP_OBS_R_FINGER_IDX])
    out[..., 12] = _FINGER_CLOSE_CMD if r_opening > _FINGER_CLOSE_TARGET else 0.0

    # L finger: only for bimanual CLAMP. CLAMP_R leaves ``action[..., 13]``
    # at the zero-padded value, preserving the post-RECLAMP_L finger
    # position.
    if skill == SkillType.CLAMP:
        l_opening = float(obs[0, _GRIP_OBS_L_FINGER_IDX])
        out[..., 13] = _FINGER_CLOSE_CMD if l_opening > _FINGER_CLOSE_TARGET else 0.0

    return out


# ---------------------------------------------------------------------------
# Phase 5-1b C2: env.step outcome → SkillResult helper (A1 dispatch prerequisite)
# ---------------------------------------------------------------------------


def derive_skill_result(
    dones,
    extras: dict,
    world_idx: int = 0,
) -> SkillResult | None:
    """Map a single world's env.step outcome to a :class:`SkillResult`.

    The orchestrator runs under the single-world contract (Phase 5-1b C5),
    so ``world_idx`` defaults to 0. This helper consumes the RSL-RL VecEnv
    4-tuple ``(obs, rewards, dones, extras)`` produced by the THREAD Newton
    envs (signature confirmed in ``newton_approach_cable_env.py:1863``,
    ``newton_aerial_regrasp_env.py:1424``, ``newton_clamp_env.py:1115``,
    ``newton_insert_clip_env.py:1562``).

    The envs already enforce the timeouts contract (Phase 5-1b C9 +
    prohibited.md "timeouts 汚染禁止"): ``extras["time_outs"]`` excludes
    success and explosion (see e.g. AC env line 1581 P3 fix). This helper
    consumes the sanitized signal directly.

    CABLE_DROP is not exposed as a dedicated extras key by the current
    envs and is currently subsumed by :attr:`SkillResult.FAIL`. Adding
    a dedicated cable-Z-drop check is deferred to A2 (Phase 5-1b
    Cluster G) when recovery routing requires the distinction.

    Args:
        dones: Tensor / array of shape ``[num_envs]`` with done flags.
        extras: env.step extras dict.
        world_idx: 0-indexed world; default 0 for single-world routing.

    Returns:
        :class:`SkillResult` when the world has terminated; ``None`` when
        the episode is still in progress (caller continues the rollout).
    """
    done_flag = int(dones[world_idx]) if hasattr(dones, "__getitem__") else int(dones)
    if done_flag == 0:
        return None

    log_per_world = extras.get("log_per_world", {})
    explosion_arr = log_per_world.get("explosion")
    if explosion_arr is not None and bool(explosion_arr[world_idx]):
        return SkillResult.EXPLOSION

    success_arr = log_per_world.get("success")
    if success_arr is not None and bool(success_arr[world_idx]):
        return SkillResult.SUCCESS

    time_outs = extras.get("time_outs")
    if time_outs is not None and int(time_outs[world_idx]) == 1:
        return SkillResult.TIMEOUT

    return SkillResult.FAIL


# ---------------------------------------------------------------------------
# Phase C4 B5: per-arm SUCCESS path (orch-side override of env bilateral AND)
# ---------------------------------------------------------------------------
#
# CLAMP_R standalone (Phase 5-3 STEPs 14/22/30/38) needs per-arm SUCCESS
# detection. Env L1184 is hardcoded `if clamp_r_ok and clamp_l_ok:` with
# no skill_type / dual_arm conditional, so CLAMP_R-only episodes can never
# satisfy env's bilateral AND -> :func:`derive_skill_result` always returns
# TIMEOUT or FAIL for CLAMP_R standalone.
#
# This section provides the orch-side bypass:
#   * :class:`_PerArmClampTracker` — per-episode R-arm sustain counter
#   * :func:`derive_clamp_r_skill_result` — per-arm SkillResult derivation
#   * dispatch in :meth:`RoutingOrchestrator._run_rl_episode`
#
# env file UNCHANGED (CC#3 Option D TOUCH FORBIDDEN strict compliance).

_CLAMP_R_PER_ARM_SUCCESS_CONTRACT = (
    "CLAMP_R per-arm SUCCESS contract (Phase C4 B5):\n"
    "  - extras['log_per_world']['success'] is the env's bilateral AND outcome (legacy).\n"
    "  - For CLAMP_R skill SUCCESS verdict, callers (eval_skill.py / Phase C5\n"
    "    DAPG demo collector / orchestrator) MUST consume the verdict returned\n"
    "    by `derive_clamp_r_skill_result`, NOT the env's bilateral AND signal.\n"
    "  - Demo collectors copying the IC pattern (collect_insert_clip_demos.py\n"
    "    consumes log_per_world['success']) MUST be updated for CLAMP_R."
)


class _PerArmClampTracker:
    """Per-episode R-arm sustain counter for orch-side CLAMP_R success.

    Bypasses :class:`NewtonGripEnv`'s hardcoded bilateral AND
    (``clamp_r_ok and clamp_l_ok`` at ``newton_grip_env.py:1184``) by tracking
    the R-arm criterion locally. Uses the same thresholds (``T_DIST``,
    ``T_ALIGN``, ``T_FINGER``, ``K_CLAMP``) imported from :mod:`task_config`
    to keep the SSOT chain intact; an env-attribute tripwire in
    :meth:`RoutingOrchestrator._run_rl_episode` enforces the identity.

    Lifecycle:
        Instance is per-episode (created in
        :meth:`RoutingOrchestrator._run_rl_episode`). :meth:`update` is
        called once per :meth:`env.step` with the post-step
        ``log_per_world`` and returns ``True`` once the R-arm criterion has
        held for ``K_CLAMP`` consecutive steps. Caller is responsible for
        ``env.reset()`` between episodes (existing pattern; orch-side
        SUCCESS does not trigger env auto-reset because the env's done flag
        is not set).

    RUNTIME_ONLY_SCOPE:
        Instantiated only from :meth:`RoutingOrchestrator._run_rl_episode`.
        Training-time reward computation in
        :meth:`NewtonGripEnv._compute_rewards_clamp` uses the env's
        bilateral AND directly; this fix has no PPO/DAPG impact since the
        env file is unchanged.

    Sunset trigger (ALL must hold to retire this class):
        1. :meth:`NewtonGripEnv._compute_rewards_clamp` accepts a
           ``skill_type`` kwarg and respects per-arm AND for
           CLAMP_R / CLAMP_L.
        2. Integration test ``test_env_per_arm_clamp_success`` PASS.
        3. Phase 5-3 v2 short-term gate (2-clip 60% per
           ``project_phase5_3_batch_decisions_2026-04-25`` Item 0
           S2'+S4') PASSED.

    Hardcoded R-arm only (CLAMP_L extension would require a ``hand``
    arg + suffix logic; deferred to keep the current task scope tight).
    """

    def __init__(self) -> None:
        self._sustain: int = 0

    def update(self, log_per_world: dict, world_idx: int = 0) -> bool:
        """Read post-step R-arm metrics and update the sustain counter.

        Args:
            log_per_world: ``extras["log_per_world"]`` from
                :meth:`NewtonGripEnv.step`. Required keys for R-arm:
                ``dist_pos_r`` [m], ``dist_ori_r`` [rad], ``finger_r``
                [m, sum of two finger joints]. Per-world arrays of shape
                ``[num_envs]``.
            world_idx: 0-indexed world. The orchestrator runs under the
                Phase 5-1b C5 single-world contract, so ``world_idx`` is
                expected to be ``0``; values ``>= 0`` are accepted for
                forward-compat.

        Returns:
            ``True`` if the R-arm criterion has held for ``K_CLAMP``
            consecutive steps, ``False`` otherwise. Returns ``False`` and
            resets the sustain counter on missing keys / out-of-bounds
            indices / non-numeric values (defensive: the env contract is
            stable today but evolves).

        Raises:
            ValueError: if ``world_idx < 0``.
        """
        if world_idx < 0:
            raise ValueError(f"world_idx must be >= 0, got {world_idx}")

        try:
            dist_pos = float(log_per_world["dist_pos_r"][world_idx])
            dist_ori = float(log_per_world["dist_ori_r"][world_idx])
            finger = float(log_per_world["finger_r"][world_idx])
        except (KeyError, IndexError, TypeError, ValueError):
            self._sustain = 0
            return False

        ok = dist_pos < T_DIST and dist_ori < T_ALIGN and finger < T_FINGER
        self._sustain = self._sustain + 1 if ok else 0
        return self._sustain >= K_CLAMP


def derive_clamp_r_skill_result(
    dones,
    extras: dict,
    tracker: _PerArmClampTracker,
    world_idx: int = 0,
) -> SkillResult | None:
    """Map a CLAMP_R env.step outcome to a :class:`SkillResult`.

    Per-arm variant of :func:`derive_skill_result` for CLAMP_R standalone
    (Phase 5-3 STEPs 14/22/30/38). Bypasses the env's bilateral AND
    (``newton_grip_env.py:1184``) by computing per-arm SUCCESS via the
    supplied ``tracker``. Explosion is preserved from the env's OR'd
    signal (``dist_pos_r > 1.0 m or dist_pos_l > 1.0 m``) and acts as a
    terminal physics gate.

    Decision order:
        1. **EXPLOSION**: env's OR'd explosion flag, checked first so
           that an L-arm physics breakdown during CLAMP_R standalone
           overrides any per-arm SUCCESS that might otherwise fire on
           the same step. This is intentionally conservative: for Phase
           C5 demo collection, an L-arm explosion mid-episode is a
           physics failure, not a CLAMP_R success.
        2. **own_success**: ``tracker.update`` returns ``True`` when the
           R-arm criterion has held ``K_CLAMP`` steps. Returns
           :attr:`SkillResult.SUCCESS`.
        3. **env's done flag**: when neither explosion nor own_success
           fires, fall back to env's done semantics. ``time_outs`` ->
           :attr:`SkillResult.TIMEOUT`; otherwise
           :attr:`SkillResult.FAIL`.
           **No bilateral SUCCESS fallback** — env's
           ``log_per_world['success']`` is the bilateral AND outcome
           and is intentionally NOT consulted (per CRIT #3 contract:
           orch verdict canonical for CLAMP_R).

    Time-coincident edge cases:
        * own_success AND time_outs same step -> SUCCESS (Step 2 wins,
          aligned with env's L1197 ``done = success or timeout``: the
          env would also emit success=True at the same step).
        * own_success AND env's bilateral SUCCESS same step -> SUCCESS
          via Step 2 (tracker R-only fires <= env's bilateral, since
          R∧L ⇒ R; tracker reaches sustain >= K_CLAMP no later than env).

    env-touch compliance:
        Reads only ``extras['log_per_world']`` and ``extras['time_outs']``
        (read-only). Does not call ``env.reset`` or write env state.
        Caller is responsible for ``env.reset()`` between routing
        episodes (existing pattern).

    Args:
        dones: Tensor / array of shape ``[num_envs]`` with done flags.
        extras: ``env.step`` extras dict containing ``log_per_world`` and
            (optionally) ``time_outs``.
        tracker: Per-episode :class:`_PerArmClampTracker` instance. The
            caller must reuse the same instance across all
            :meth:`env.step` calls within a single episode.
        world_idx: 0-indexed world; default 0 for single-world routing.

    Returns:
        :class:`SkillResult` when the world has terminated;
        ``None`` while the episode is still in progress.
    """
    log_per_world = extras.get("log_per_world", {})

    # 1. EXPLOSION first (defensive against malformed explosion array)
    explosion_arr = log_per_world.get("explosion")
    if explosion_arr is not None:
        try:
            if bool(explosion_arr[world_idx]):
                return SkillResult.EXPLOSION
        except (IndexError, TypeError):
            pass  # treat as no-explosion when the array is degenerate

    # 2. Per-arm own_success (replaces env's bilateral AND for CLAMP_R)
    if tracker.update(log_per_world, world_idx):
        return SkillResult.SUCCESS

    # 3. env's done flag handles TIMEOUT / FAIL (no bilateral fallback)
    done_flag = int(dones[world_idx]) if hasattr(dones, "__getitem__") else int(dones)
    if done_flag == 0:
        return None

    time_outs = extras.get("time_outs")
    if time_outs is not None and int(time_outs[world_idx]) == 1:
        return SkillResult.TIMEOUT

    return SkillResult.FAIL


# Env attribute names that must equal the corresponding ``task_config``
# constants for the orch-side CLAMP_R criterion to match the env's
# bilateral AND inputs. Checked at the start of CLAMP_R episodes by
# :meth:`RoutingOrchestrator._run_rl_episode` (read-only access; env
# file UNCHANGED, mirrors the F3 obs-reading precedent).
_CLAMP_R_ENV_TRIPWIRE: tuple[tuple[str, float | int], ...] = (
    ("CLAMP_DIST_THRESH", T_DIST),
    ("CLAMP_ORI_THRESH", T_ALIGN),
    ("CLAMP_FINGER_THRESH", T_FINGER),
    ("CLAMP_SUSTAIN", K_CLAMP),
)


def _verify_clamp_r_env_ssot(env) -> None:
    """Verify env class attributes match task_config constants for CLAMP_R.

    Production :class:`NewtonGripEnv` aliases its class attributes to
    ``task_config`` constants (env L218-221), so the orch-side per-arm
    criterion uses the same thresholds as the env's bilateral AND. This
    tripwire raises if the chain has drifted (e.g., a future per-world
    domain-randomization patch overrides ``CLAMP_DIST_THRESH``). Read-only
    access; env file is not touched.

    Mock test envs (e.g., the ``FixedPolicy`` env in
    ``test_orchestrator_transforms.py``) typically do not expose these
    attributes — the tripwire skips when the env is not a
    ``NewtonGripEnv`` so unit tests can stub the dispatch layer without
    setting up the full env contract.

    Args:
        env: The orchestrator's env handle.

    Raises:
        RuntimeError: when ``env`` is a ``NewtonGripEnv`` and any tripwire
            attribute is missing or differs from its ``task_config``
            counterpart.
    """
    if type(env).__name__ != "NewtonGripEnv":
        return  # mock test env — skip strict tripwire
    for attr_name, expected in _CLAMP_R_ENV_TRIPWIRE:
        if not hasattr(env, attr_name):
            raise RuntimeError(
                f"NewtonGripEnv missing required CLAMP_R SSOT attr {attr_name!r}; "
                "task_config and env class attributes have diverged."
            )
        actual = getattr(env, attr_name)
        if actual != expected:
            raise RuntimeError(
                f"CLAMP_R SSOT drift: env.{attr_name}={actual!r} != "
                f"task_config={expected!r}. Update env class attribute or "
                "task_config to restore identity."
            )


class RoutingPhase(Enum):
    """Phases within a single clip routing."""

    APPROACH_CABLE = "approach_cable"  # C1 only
    CLAMP = "clamp"  # C1 only (post-AC)
    TRANSPORT = "transport"  # Scripted: move to clip
    INSERT_INTO_CLIP = "insert_into_clip"  # All clips
    UNCLAMP = "unclamp"  # Scripted: between clips
    RISE = "rise"  # Scripted: C2-C5
    RECLAMP = "reclamp"  # Scripted: C2-C5 (LEFT re-grip)
    AERIAL_REGRASP = "aerial_regrasp"  # C2-C5 (RIGHT approach)


# Clip index -> which arm is at +Y side during IC push
# C1: RIGHT at +Y (first-clip Y-symmetric placement)
# C2-C5: LEFT at +Y (direction-based, routing goes -Y)
_CLIP_PLUS_Y_ARM = {0: "R", 1: "L", 2: "L", 3: "L", 4: "L"}


class RoutingOrchestrator:
    """Orchestrates RL + scripted skills for 5-clip cable routing.

    Responsibilities:
        1. Skill sequencing per clip (C1 vs C2-C5 patterns)
        2. Observation transforms: clip-relative + mirror
        3. Action un-transforms: un-mirror
        4. Clip position management
    """

    def __init__(
        self,
        policy: MultiSkillActorCritic,
        device: str = "cuda:0",
        *,
        env=None,
        model=None,
        state_0=None,
        fk_state=None,
        fk_model=None,
        scene_info=None,
        solver=None,
        contacts=None,
    ):
        self.policy = policy
        self.device = device

        # Precompute clip positions as tensors.
        # IC env puts GROOVE_CENTER_Z (0.809) in obs[23:26]; AR env puts TABLE_HEIGHT (0.800).
        # Skill-dependent Z ensures clip-relative transform zeroes out correctly.
        self.clip_positions_ic = []
        self.clip_positions_ar = []
        for cx, cy in CLIP_POSITIONS:
            self.clip_positions_ic.append(torch.tensor([cx, cy, GROOVE_CENTER_Z], dtype=torch.float32, device=device))
            self.clip_positions_ar.append(torch.tensor([cx, cy, TABLE_HEIGHT], dtype=torch.float32, device=device))

        self.current_clip_idx: int = 0
        self.current_phase: RoutingPhase | None = None

        # Phase 5-1 Opt B: snapshot cascade foundation (A3 only).
        # A1 (execute_skill dispatch) and A2 (recovery engine) deferred to Phase 5-1b
        # pending resolution of 14 CRITICALs from 5-CC Debate 2026-04-25
        # (SKILL_NAME_TO_TYPE, MSA loader, env.step signature, num_actions matrix,
        #  multi-world model, VBD body_q_prev capture, etc.).
        self.env = env
        self.model = model
        self.state_0 = state_0
        self.fk_state = fk_state
        self.fk_model = fk_model
        self.scene_info = scene_info
        self.solver = solver
        self.contacts = contacts
        self.clip_status: list[bool] = [False] * 5
        self._snapshot_mgr = SnapshotManager()

        # Phase 5-1b C5: single-world contract. If an env was supplied, assert
        # it runs a single world. Multi-world routing is a Phase 5-2+ concern
        # (see module docstring).
        if env is not None:
            num_envs = getattr(env, "num_envs", None)
            if num_envs is not None and num_envs != 1:
                raise ValueError(
                    f"RoutingOrchestrator requires num_envs == 1 (got {num_envs}). "
                    "Multi-world routing is deferred to Phase 5-2+. See module "
                    "docstring for the world-count contract."
                )

    def _needs_clip_relative(self, skill: SkillType) -> bool:
        """Whether this skill needs clip-relative transform."""
        return skill in (SkillType.AERIAL_REGRASP, SkillType.INSERT_INTO_CLIP)

    def _needs_mirror(self, skill: SkillType, clip_idx: int) -> bool:
        """Whether this skill+clip combo needs Y-mirror."""
        return skill == SkillType.INSERT_INTO_CLIP and _CLIP_PLUS_Y_ARM.get(clip_idx) == "L"

    def get_action(
        self,
        obs: torch.Tensor,
        skill: SkillType,
        clip_idx: int,
    ) -> torch.Tensor:
        """Get action from policy with appropriate transforms.

        Full pipeline for IC at C2-C5:
            obs -> clip_relative -> mirror -> policy -> un-mirror -> action

        Args:
            obs: (N, 42) world-frame observation.
            skill: Which RL skill to execute.
            clip_idx: 0-indexed clip (0=C1, 4=C5).

        Returns:
            (N, 12) world-frame action.
        """
        if skill == SkillType.INSERT_INTO_CLIP:
            clip_pos = self.clip_positions_ic[clip_idx]
        else:
            clip_pos = self.clip_positions_ar[clip_idx]
        do_cr = self._needs_clip_relative(skill)
        do_mirror = self._needs_mirror(skill, clip_idx)

        # Transform obs
        transformed = obs
        if do_cr:
            transformed = to_clip_relative(transformed, clip_pos)
        if do_mirror:
            transformed = mirror_obs(transformed)

        # Forward through policy
        self.policy.set_skill(skill)
        action = self.policy.act_inference(transformed)

        # Un-transform action
        if do_mirror:
            action = mirror_action(action)

        return action

    def get_c1_sequence(self) -> list[RoutingPhase]:
        """Return the skill sequence for first clip (C1)."""
        return [
            RoutingPhase.APPROACH_CABLE,
            RoutingPhase.CLAMP,
            RoutingPhase.TRANSPORT,
            RoutingPhase.INSERT_INTO_CLIP,
            RoutingPhase.UNCLAMP,
        ]

    def get_cn_sequence(self) -> list[RoutingPhase]:
        """Return the skill sequence for subsequent clips (C2-C5)."""
        return [
            RoutingPhase.UNCLAMP,
            RoutingPhase.RISE,
            RoutingPhase.RECLAMP,
            RoutingPhase.AERIAL_REGRASP,
            RoutingPhase.TRANSPORT,
            RoutingPhase.INSERT_INTO_CLIP,
        ]

    def phase_to_skill_type(self, phase: RoutingPhase) -> SkillType | None:
        """Map routing phase to RL SkillType (None = scripted)."""
        mapping = {
            RoutingPhase.APPROACH_CABLE: SkillType.APPROACH_CABLE,
            RoutingPhase.CLAMP: SkillType.CLAMP,
            RoutingPhase.INSERT_INTO_CLIP: SkillType.INSERT_INTO_CLIP,
            RoutingPhase.AERIAL_REGRASP: SkillType.AERIAL_REGRASP,
        }
        return mapping.get(phase)

    def is_scripted(self, phase: RoutingPhase) -> bool:
        """Whether this phase is handled by scripted control."""
        return self.phase_to_skill_type(phase) is None

    # ------------------------------------------------------------------
    # Phase 5-1b Cluster F (A1): execute_skill dispatch + RL/scripted/wait helpers
    # ------------------------------------------------------------------

    # Default cap on physics steps executed inside a single RL skill episode
    # when the env does not terminate (FAIL path). Matches spec §14.4.
    DEFAULT_RL_MAX_STEPS: int = 200

    # Phase 5-1b Cluster G (A2) recovery-engine parameters (spec §14.5).
    MAX_RETRY: int = 3
    MAX_ROLLBACK_DEPTH: int = 3

    def execute_skill(
        self,
        step_id: int,
        max_rl_steps: int | None = None,
    ) -> SkillResult:
        """Dispatch a single routing STEP to the appropriate sub-executor.

        Per spec §14.4, a STEP is either an RL episode (``StepType.RL``),
        a scripted IK waypoint / finger command (``StepType.SCRIPTED``),
        or a ``ClipConfirm`` wait (``StepType.WAIT``).

        This is the Phase 5-1b **A1** entry point. The accompanying A2
        recovery engine (Cluster G) wraps this in retry / rollback /
        abort logic.

        Args:
            step_id: Routing STEP id (1..43).
            max_rl_steps: Max env.step iterations for RL episodes. Defaults
                to :attr:`DEFAULT_RL_MAX_STEPS`.

        Returns:
            :class:`SkillResult` reflecting the STEP outcome.
        """
        # Lazy import — step_table pulls in scripted_skills which lazily
        # imports Newton, but the env_isaaclab test path never reaches it.
        from ..skills.step_table import STEP_BY_ID, StepType

        step_def = STEP_BY_ID[step_id]
        stype = step_def.step_type

        if stype == StepType.RL:
            max_steps = max_rl_steps if max_rl_steps is not None else self.DEFAULT_RL_MAX_STEPS
            return self._run_rl_episode(step_def, max_steps=max_steps)
        if stype == StepType.SCRIPTED:
            return self._run_scripted(step_def)
        if stype == StepType.WAIT:
            return self._run_wait(step_def)
        raise ValueError(f"Unknown StepType {stype!r} at STEP {step_id}")

    def _run_rl_episode(self, step_def, max_steps: int) -> SkillResult:
        """Roll out the current RL skill in the env until terminal or timeout."""
        if self.env is None or self.policy is None:
            raise RuntimeError("_run_rl_episode requires env and policy to be set at __init__.")

        skill_type = resolve_skill_type(step_def.skill, step_def.step_id)
        if skill_type is None:
            raise ValueError(
                f"STEP {step_def.step_id} has skill {step_def.skill} with "
                "StepType.RL but no SkillType mapping. Check resolve_skill_type."
            )

        clip_idx = step_def.clip_index if step_def.clip_index is not None else self.current_clip_idx
        self.policy.set_skill(skill_type)

        # Phase C4 B5: CLAMP_R uses the orch-side per-arm SUCCESS path. The
        # env's bilateral AND (``clamp_r_ok and clamp_l_ok`` at
        # ``newton_grip_env.py:1184``) cannot fire for R-arm-only episodes,
        # so :func:`derive_skill_result` would always return TIMEOUT/FAIL
        # for CLAMP_R. Other skills keep the standard derive_skill_result.
        tracker: _PerArmClampTracker | None = None
        if skill_type == SkillType.CLAMP_R:
            _verify_clamp_r_env_ssot(self.env)
            tracker = _PerArmClampTracker()

        for _ in range(max_steps):
            obs, _obs_extras = self.env.get_observations()
            policy_action = self.get_action(obs, skill_type, clip_idx)
            action_dim_for = getattr(self.policy, "action_dim_for", None)
            if callable(action_dim_for):
                try:
                    policy_action_dim = int(action_dim_for(skill_type))
                except TypeError:
                    policy_action_dim = int(action_dim_for(skill_type.value))
            else:
                policy_action_dim = int(policy_action.shape[-1])
            env_action_dim = int(getattr(self.env, "num_actions", env_action_dim_for(skill_type)))
            action = policy_action_to_env_action(
                policy_action,
                skill=skill_type,
                env_action_dim=env_action_dim,
                policy_action_dim=policy_action_dim,
            )
            action = mask_l_arm_action_if_needed(action, skill_type)
            action = apply_finger_close_if_needed(action, skill_type, obs)
            _obs, _rewards, dones, extras = self.env.step(action)
            if tracker is not None:
                result = derive_clamp_r_skill_result(dones, extras, tracker, world_idx=0)
            else:
                result = derive_skill_result(dones, extras)
            if result is not None:
                return result

        # Env kept emitting done=0 for the full window — treat as TIMEOUT so
        # the recovery engine's Retry path can kick in without polluting
        # extras["time_outs"] (Phase 5-1b C9).
        return SkillResult.TIMEOUT

    def _run_scripted(self, step_def) -> SkillResult:
        """Dispatch scripted STEP to the corresponding scripted_skills helper."""
        from ..skills.scripted_skills import (
            half_unclamp_release,
            reclamp_left,
            transport_to_clip,
        )
        from ..skills.step_table import SkillName

        self._require_newton_context("_run_scripted")

        skill = step_def.skill
        if skill == SkillName.TRANSPORT:
            if step_def.target_left is None or step_def.target_right is None:
                raise ValueError(f"STEP {step_def.step_id} TRANSPORT requires target_left/target_right.")
            state, result = transport_to_clip(
                self.model,
                self.state_0,
                self.scene_info,
                self.solver,
                self.contacts,
                target_left=step_def.target_left,
                target_right=step_def.target_right,
                label=f"S{step_def.step_id:02d}-TRANSPORT",
            )
            self.state_0 = state
            return result
        if skill == SkillName.RECLAMP_L:
            state, result = reclamp_left(
                self.model,
                self.state_0,
                self.scene_info,
                self.solver,
                self.contacts,
                label=f"S{step_def.step_id:02d}-RECLAMP_L",
            )
            self.state_0 = state
            return result
        if skill == SkillName.HALF_UNCLAMP_RELEASE:
            state, result = half_unclamp_release(
                self.model,
                self.state_0,
                self.scene_info,
                self.solver,
                self.contacts,
                label=f"S{step_def.step_id:02d}-HALF_UNCLAMP",
            )
            self.state_0 = state
            return result
        raise ValueError(f"Scripted dispatch unimplemented for {skill} at STEP {step_def.step_id}")

    def _is_scripted_step(self, step_id: int) -> bool:
        """True if STEP ``step_id`` is SCRIPTED / WAIT (not RL)."""
        from ..skills.step_table import STEP_BY_ID, StepType

        return STEP_BY_ID[step_id].step_type != StepType.RL

    def execute_step(
        self,
        step_id: int,
        max_rl_steps: int | None = None,
        retry_seed: int | None = None,
    ) -> SkillResult:
        """Execute one routing STEP with Phase 5-1b Cluster G recovery.

        Wraps :meth:`execute_skill` with the retry/rollback/abort engine
        of spec §14.5:

        * SUCCESS → return immediately.
        * EXPLOSION → abort (no retry, no rollback) per spec.
        * CABLE_DROP → rollback.
        * TIMEOUT / FAIL:
            - RL STEP → retry up to :attr:`MAX_RETRY` (C7 seed perturbation
              per attempt); if still failing, rollback.
            - SCRIPTED / WAIT STEP → deterministic, retrying is useless
              (C12), go straight to rollback.

        The rollback path (:meth:`_rollback`) walks back up to
        :attr:`MAX_ROLLBACK_DEPTH` STEPs and re-executes forward.
        Snapshots taken during the re-execution MUST NOT overwrite the
        anchor snapshots captured on the original forward pass (C8); this
        is naturally preserved because :meth:`execute_step` captures
        snapshots and :meth:`_rollback` only calls :meth:`execute_skill`
        (which does not save).

        Args:
            step_id: 1..43 routing STEP id.
            max_rl_steps: Optional override for the RL episode cap.
            retry_seed: Optional base seed for :mod:`torch.manual_seed`
                on retry attempts (C14); when ``None`` we fall back to
                ``step_id`` to keep rollback trajectories reproducible.

        Returns:
            :class:`SkillResult` capturing the terminal outcome of the
            STEP, including after any retries or rollbacks.
        """
        # Capture the anchor snapshot once, only when Newton context is set
        # (non-Newton unit tests call execute_skill directly).
        if self.state_0 is not None and self.fk_state is not None and self.fk_model is not None:
            if not self._snapshot_mgr.has(step_id):
                self.capture_snapshot(step_id)

        scripted = self._is_scripted_step(step_id)
        base_seed = retry_seed if retry_seed is not None else step_id

        for attempt in range(self.MAX_RETRY + 1):
            if attempt > 0:
                # C7: seed perturbation for deterministic-act_inference retries.
                # Without this, retry-from-same-snapshot matches the AC v21
                # catastrophic-collapse resume pattern (prohibited.md).
                # This is a best-effort mitigation — a complete fix likely
                # requires switching to stochastic ``policy.act`` on retry.
                torch.manual_seed(base_seed * 1000 + attempt)

            result = self.execute_skill(step_id, max_rl_steps=max_rl_steps)

            if result == SkillResult.SUCCESS:
                return result
            if result == SkillResult.EXPLOSION:
                # Abort: do NOT retry / rollback through an exploded state.
                return result
            if result == SkillResult.CABLE_DROP:
                break  # Rollback path below.
            if scripted:
                # C12: scripted STEP failure is deterministic, skip retries.
                break
            # RL TIMEOUT / FAIL: restore and retry.
            if self._snapshot_mgr.has(step_id) and self.state_0 is not None:
                self.restore_snapshot(step_id)

        return self._rollback(failed_step_id=step_id, max_rl_steps=max_rl_steps)

    # Phase 5-1b Cluster H (C13): Per-skill BC P0 tolerance region hook.
    #
    # Rationale (CC5 past-failure-replay): rollback re-execution may rewind
    # physics into a state outside the training BC P0 distribution for the
    # skill about to be invoked. Running a BC-trained policy on an OOD P0
    # tends to produce low-success trajectories while still burning GPU.
    #
    # Phase 5-1b ships only the extension point: callers populate
    # :attr:`bc_p0_region_check` with a function ``(skill_type, state_0,
    # clip_status, step_id) -> bool`` that returns False when the state
    # is known to be OOD. The default always accepts (no-op) because the
    # per-skill BC P0 statistics are not yet available; Phase 5-2+ can
    # plug in measured distributions (see ``project_ac_pos_scale_finding``
    # and ``LL-ApproachCable-BugHistory`` for AC's P0 range).
    def bc_p0_region_check(  # noqa: D401 — default-deny hook stub
        self,
        skill_type: SkillType,
        step_id: int,
    ) -> bool:
        """Return True if the current state is within the skill's BC P0.

        Override (or patch) this method to gate rollback re-execution on
        an OOD check. Default accepts every state.
        """
        return True

    def _rollback(
        self,
        failed_step_id: int,
        max_rl_steps: int | None = None,
    ) -> SkillResult:
        """Walk back up to :attr:`MAX_ROLLBACK_DEPTH` STEPs and re-execute forward.

        On each depth, ``restore_snapshot`` rewinds physics to STEP
        ``failed_step_id - depth`` and :meth:`execute_skill` is called
        per STEP from the rewound target up to the original failed STEP.
        If any re-execution produces SUCCESS for the whole range, we
        return SUCCESS; otherwise we increment ``depth`` until
        :attr:`MAX_ROLLBACK_DEPTH` is exhausted, at which point the
        caller receives :attr:`SkillResult.CABLE_DROP` to signal that
        the routing cannot recover from this point.
        """
        if self.state_0 is None or self.fk_state is None:
            # Unit-test path: no physics context to actually rewind.
            return SkillResult.CABLE_DROP

        for depth in range(1, self.MAX_ROLLBACK_DEPTH + 1):
            target = failed_step_id - depth
            if target < 1 or not self._snapshot_mgr.has(target):
                return SkillResult.CABLE_DROP

            self.restore_snapshot(target)
            all_ok = True
            for sid in range(target, failed_step_id + 1):
                # Phase 5-1b C13: BC P0 region gate before every RL re-execution.
                from ..skills.step_table import STEP_BY_ID, StepType

                sd = STEP_BY_ID[sid]
                if sd.step_type == StepType.RL:
                    skill_type = resolve_skill_type(sd.skill, sid)
                    if skill_type is not None and not self.bc_p0_region_check(skill_type, sid):
                        # State is outside the skill's BC P0 distribution;
                        # re-executing would almost certainly fail, skip to
                        # a deeper rollback.
                        all_ok = False
                        break

                r = self.execute_skill(sid, max_rl_steps=max_rl_steps)
                if r == SkillResult.EXPLOSION:
                    return r  # abort rollback
                if r != SkillResult.SUCCESS:
                    all_ok = False
                    break
            if all_ok:
                return SkillResult.SUCCESS

        return SkillResult.CABLE_DROP

    def _run_wait(self, step_def) -> SkillResult:
        """Dispatch WAIT STEP to clip_confirm + track clip_status on success."""
        from ..skills.scripted_skills import clip_confirm
        from ..skills.step_table import SkillName

        self._require_newton_context("_run_wait")

        if step_def.skill != SkillName.CLIP_CONFIRM:
            raise ValueError(f"Unexpected WAIT skill {step_def.skill} at STEP {step_def.step_id}")
        if step_def.clip_index is None:
            raise ValueError(f"CLIP_CONFIRM at STEP {step_def.step_id} requires clip_index.")

        state, result = clip_confirm(
            self.model,
            self.state_0,
            self.scene_info,
            self.solver,
            self.contacts,
            clip_index=step_def.clip_index,
            label=f"S{step_def.step_id:02d}-CLIP_CONFIRM",
        )
        self.state_0 = state
        if result == SkillResult.SUCCESS:
            # Mark the clip as fixed; rollback that crosses this point will
            # re-read the bookkeeping via restore_snapshot (C2 write-back).
            self.clip_status[step_def.clip_index] = True
        return result

    # ------------------------------------------------------------------
    # Phase 5-1 Opt B + Phase 5-1b C6: Snapshot cascade (A3)
    #
    # C6 (2026-04-25) extended :meth:`SnapshotManager.restore` to overwrite
    # ``solver.body_q_prev`` with the restored ``body_q``, preventing the
    # VBD velocity-spike failure mode (see snapshot.py:restore docstring).
    # This aligns with the canonical reset pattern in
    # :func:`restore_world_body_state` from
    # :mod:`thread_isaac_lab.envs.newton_skill_env_base`.
    #
    # Remaining Phase 5-1b TODO for recovery (A2) wiring:
    # - env-side counters not persisted by SnapshotManager:
    #   ``episode_length_buf``, cumulative reward trackers, contact pair list
    # - if orchestrator ever runs under multi-world, the single-snapshot-per-
    #   STEP layout covers all worlds atomically; divergent per-world rollback
    #   is a Phase 5-2+ concern (see module docstring C5).
    # ------------------------------------------------------------------
    def _require_newton_context(self, op: str) -> None:
        """Guard for ops that need the full Newton context."""
        missing = [name for name in ("state_0", "fk_state", "fk_model") if getattr(self, name) is None]
        if missing:
            raise RuntimeError(
                f"{op} requires Newton context attributes to be set at __init__ "
                f"(missing: {', '.join(missing)}). Pass model/state_0/fk_state/fk_model "
                "as kwargs when constructing RoutingOrchestrator for routing execution."
            )

    def capture_snapshot(
        self,
        step_id: int,
        ik_target_l: tuple[float, float, float] | None = None,
        ik_target_r: tuple[float, float, float] | None = None,
        fk_jq_indices: tuple[int, int, int, int] = (7, 8, 16, 17),
    ) -> None:
        """Save the current physics state keyed by STEP id.

        Args:
            step_id: 1..43 routing STEP identifier.
            ik_target_l: Current left IK target (x, y, z) or ``None``.
            ik_target_r: Current right IK target (x, y, z) or ``None``.
            fk_jq_indices: Joint indices for L/R finger positions.
        """
        self._require_newton_context("capture_snapshot")
        self._snapshot_mgr.save(
            step_id=step_id,
            state_0=self.state_0,
            fk_state=self.fk_state,
            clip_status=self.clip_status,
            ik_target_l=ik_target_l,
            ik_target_r=ik_target_r,
            fk_jq_indices=fk_jq_indices,
        )

    def restore_snapshot(self, step_id: int) -> StateSnapshot:
        """Restore physics state to a saved snapshot and sync ``clip_status``.

        Forwards ``self.solver`` (when set) to :meth:`SnapshotManager.restore`
        so the VBD ``body_q_prev`` is aligned with the restored ``body_q``
        (Phase 5-1b C6). Env-side counters that the snapshot does not
        persist (e.g. ``episode_length_buf``, cumulative reward trackers)
        are still the caller's responsibility.

        Args:
            step_id: STEP identifier to restore.

        Returns:
            The restored :class:`StateSnapshot`.
        """
        self._require_newton_context("restore_snapshot")
        snap = self._snapshot_mgr.restore(
            step_id=step_id,
            state_0=self.state_0,
            fk_state=self.fk_state,
            fk_model=self.fk_model,
            solver=self.solver,
        )
        # Debate C2 fix: write clip_status back to the orchestrator so that a
        # rollback observes the clip state at snapshot time.
        self.clip_status = list(snap.clip_status)
        return snap

    def clear_snapshots(self) -> None:
        """Drop every saved snapshot (e.g. at episode boundary)."""
        self._snapshot_mgr.clear()

    @property
    def saved_snapshot_steps(self) -> list[int]:
        """STEP ids that currently have a saved snapshot, sorted ascending."""
        return self._snapshot_mgr.saved_steps
