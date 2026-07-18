# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Content-hash identity utilities for WMSO D1 (read-only over existing artifacts).

All identities are pinned by ``hashlib.sha256`` content hashes of on-disk artifacts, reusing the
same primitive the surface-C route trainer already records (``ckpt_sha256``). No file is written,
no policy is loaded, no training is launched. Two derived hashes are frozen by the design v4.1.1:

* :func:`finetune_cfg_hash` — a canonical sorted-JSON projection over the exact DAPG ``summary.json``
  training-input keys (excluding the outcome ``dapg.bc_losses``).
* :func:`source_closure_sha256` — a deterministic aggregate over an enumerated closure of source +
  config files (a single whole-file hash is not a complete executable identity).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .contracts import (
    AssociationStrength,
    HandoffStartContext,
    LearnedIdentity,
    Lineage,
    PolicyFamily,
    ScriptedIdentity,
    WaitIdentity,
    is_hex64,
)

# Exact projection key set for the BC+RL finetune-config hash (design v4.1.1 §5 / pN R2).
FINETUNE_CFG_TOPLEVEL_KEYS: tuple[str, ...] = (
    "experiment",
    "framework",
    "base_model",
    "lora_rank",
    "world_count",
    "max_iterations",
    "num_steps_per_env",
    "device",
    "ppo",
    "env_config",
)
FINETUNE_CFG_CONVERGENCE_KEYS: tuple[str, ...] = ("metric", "mode", "patience", "min_iterations", "delta")

# Enumerated source-closure members (design v4.1.1 §8 / pN R3). Repo-relative paths.
SCRIPTED_CLOSURE_MEMBERS: tuple[str, ...] = (
    "thread_isaac_lab/skills/scripted_skills.py",
    "thread_isaac_lab/skills/result.py",
    "thread_isaac_lab/scripts/newton_routing_utils.py",
    "thread_isaac_lab/configs/task_config.py",
    "thread_isaac_lab/skills/step_table.py",
)
WAIT_CLOSURE_MEMBERS: tuple[str, ...] = SCRIPTED_CLOSURE_MEMBERS + (
    "thread_isaac_lab/orchestrator/routing_orchestrator.py",
)


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase 64-hex sha256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Return the lowercase 64-hex sha256 of the file at ``path``.

    Raises:
        FileNotFoundError: if the file is absent (fail-closed; never silently pins a missing file).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"cannot hash absent artifact: {p}")
    return sha256_bytes(p.read_bytes())


def canonical_json(obj: object) -> bytes:
    """Serialize ``obj`` to canonical UTF-8 JSON (sorted keys, no ASCII escaping, tight separators)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def finetune_cfg_hash(summary: dict) -> str:
    """Return the frozen BC+RL finetune-config hash for a DAPG ``summary.json`` dict.

    Projects the exact training-input keys (top-level + ``dapg`` minus the ``bc_losses`` outcome +
    the convergence subset), canonicalizes, and sha256s. Present-time input; NOT a train-time crypto
    proof.

    Args:
        summary: The parsed DAPG run ``summary.json``.

    Returns:
        The 64-hex sha256 of the canonical projection.
    """
    missing = [k for k in FINETUNE_CFG_TOPLEVEL_KEYS if k not in summary]
    if missing:
        raise ValueError(f"summary missing required finetune-cfg keys: {missing}")
    if not isinstance(summary.get("dapg"), dict):
        raise ValueError("summary.dapg must be a dict")
    if not isinstance(summary.get("convergence"), dict):
        raise ValueError("summary.convergence must be a dict")
    conv_missing = [k for k in FINETUNE_CFG_CONVERGENCE_KEYS if k not in summary["convergence"]]
    if conv_missing:
        raise ValueError(f"summary.convergence missing required keys: {conv_missing}")
    proj: dict = {k: summary[k] for k in FINETUNE_CFG_TOPLEVEL_KEYS}
    proj["dapg"] = {k: v for k, v in summary["dapg"].items() if k != "bc_losses"}
    proj["convergence"] = {k: summary["convergence"][k] for k in FINETUNE_CFG_CONVERGENCE_KEYS}
    return sha256_bytes(canonical_json(proj))


def source_closure_sha256(members: tuple[str, ...] | list[str], repo_root: str | Path) -> str:
    """Return the deterministic aggregate hash over an enumerated source/config closure.

    The aggregate is ``sha256("\\n".join(sorted("<repo_rel_path>:<file_sha256>")))``. Every member is
    hashed with its full repo-relative path; a missing member fails closed (raises).

    Args:
        members: Repo-relative paths of every closure member.
        repo_root: Repository root the members are relative to.

    Returns:
        The 64-hex sha256 of the sorted per-member ``path:sha`` aggregate.
    """
    root = Path(repo_root)
    entries = sorted(f"{rel}:{sha256_file(root / rel)}" for rel in members)
    return sha256_bytes("\n".join(entries).encode("utf-8"))


def scripted_identity(skill_id: str, callable_qualname: str, repo_root: str | Path) -> ScriptedIdentity:
    """Build a :class:`.ScriptedIdentity` pinned by ``skill_id`` + qualname + source-closure hash."""
    return ScriptedIdentity(
        skill_id=skill_id,
        callable_qualname=callable_qualname,
        source_closure_sha256=source_closure_sha256(SCRIPTED_CLOSURE_MEMBERS, repo_root),
    )


def wait_identity(skill_id: str, callable_qualname: str, repo_root: str | Path) -> WaitIdentity:
    """Build a :class:`.WaitIdentity` pinned by ``skill_id`` + qualname + WAIT source-closure hash."""
    return WaitIdentity(
        skill_id=skill_id,
        callable_qualname=callable_qualname,
        source_closure_sha256=source_closure_sha256(WAIT_CLOSURE_MEMBERS, repo_root),
    )


def learned_identity_from_files(
    *,
    final_policy_path: str | Path,
    family: PolicyFamily,
    base_ckpt_path: str | Path | None = None,
    finetune_summary_path: str | Path | None = None,
    association_strength: AssociationStrength,
) -> LearnedIdentity:
    """Build a :class:`.LearnedIdentity` by content-hashing on-disk artifacts (present-time, non-crypto).

    Args:
        final_policy_path: Path to the final policy checkpoint.
        family: Policy provenance family.
        base_ckpt_path: Path to the base BC checkpoint, or ``None`` for RL-only.
        finetune_summary_path: Path to the DAPG run ``summary.json`` (for the finetune-config hash),
            or ``None`` for RL-only.
        association_strength: The lineage association strength. ``NOT_APPLICABLE_RL_ONLY`` requires
            both base/finetune to be ``None``.

    Returns:
        A structurally validated learned identity with ``train_time_crypto_bound=False``.
    """
    final_hash = sha256_file(final_policy_path)
    base_hash: str | None = sha256_file(base_ckpt_path) if base_ckpt_path is not None else None
    finetune_hash: str | None = None
    if finetune_summary_path is not None:
        summary = json.loads(Path(finetune_summary_path).read_text())
        finetune_hash = finetune_cfg_hash(summary)
    lineage = Lineage(
        family=family,
        final_policy_hash=final_hash,
        base_ckpt_hash=base_hash,
        finetune_cfg_hash=finetune_hash,
    )
    return LearnedIdentity(
        policy_weight_hash=final_hash,
        lineage=lineage,
        train_time_crypto_bound=False,
        association_strength=association_strength,
    )


def make_initiation_context_hash(payload: object) -> str:
    """Return a canonical-JSON content hash for a handoff-start initiation context payload."""
    return sha256_bytes(canonical_json(payload))


def handoff_start_context(*, incoming_handoff_state_id: str | None, initiation_context: object) -> HandoffStartContext:
    """Build a typed :class:`.HandoffStartContext` from an initiation-context payload."""
    return HandoffStartContext(
        incoming_handoff_state_id=incoming_handoff_state_id,
        initiation_context_hash=make_initiation_context_hash(initiation_context),
    )


__all__ = [
    "FINETUNE_CFG_TOPLEVEL_KEYS",
    "FINETUNE_CFG_CONVERGENCE_KEYS",
    "SCRIPTED_CLOSURE_MEMBERS",
    "WAIT_CLOSURE_MEMBERS",
    "sha256_bytes",
    "sha256_file",
    "canonical_json",
    "finetune_cfg_hash",
    "source_closure_sha256",
    "scripted_identity",
    "wait_identity",
    "learned_identity_from_files",
    "make_initiation_context_hash",
    "handoff_start_context",
    "is_hex64",
]
