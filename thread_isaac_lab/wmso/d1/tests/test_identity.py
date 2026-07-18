# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for WMSO D1 content-hash identity utilities (pinned-hash reproduction + fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thread_isaac_lab.wmso.d1 import identity as I
from thread_isaac_lab.wmso.d1.contracts import AssociationStrength, PolicyFamily

_REPO_ROOT = Path(__file__).resolve().parents[4]
_APPROACH_DIR = _REPO_ROOT / "thread_isaac_lab/data/rl_approach_cable_A_w256_20260409_073409"
_SUMMARY = _APPROACH_DIR / "summary.json"

# Design v4.1.1 / manifest pinned values.
_FINETUNE_CFG = "1977e04691912dbef1b2d4bc3527272ec82456af3451fc80ff8445747bdd5594"
_RAW_SUMMARY = "d280ea973c025d0bb5bade56eb0466bb2f4078e9ac287e2c8cd0453d59e2c620"
_SCRIPTED_CLOSURE = "318c4da40ec1c0f63e1befa0ec81450e6c1df17458dee8eae3bddaa26da37f53"
_WAIT_CLOSURE = "37c6f936ba6ad32648b047e1ed0c7199b562e1b33a6098b7e5a57676b9be0b56"


def test_canonical_json_is_deterministic_and_sorted():
    a = I.canonical_json({"b": 1, "a": 2})
    b = I.canonical_json({"a": 2, "b": 1})
    assert a == b == b'{"a":2,"b":1}'


@pytest.mark.skipif(not _SUMMARY.is_file(), reason="DAPG summary artifact not present")
def test_finetune_cfg_hash_reproduces_pinned_value():
    summary = json.loads(_SUMMARY.read_text())
    assert I.finetune_cfg_hash(summary) == _FINETUNE_CFG


@pytest.mark.skipif(not _SUMMARY.is_file(), reason="DAPG summary artifact not present")
def test_finetune_cfg_hash_excludes_bc_losses_outcome():
    summary = json.loads(_SUMMARY.read_text())
    mutated = json.loads(_SUMMARY.read_text())
    # bc_losses is an outcome; perturbing it must NOT change the config identity.
    if isinstance(mutated.get("dapg"), dict):
        mutated["dapg"]["bc_losses"] = "PERTURBED"
    assert I.finetune_cfg_hash(mutated) == I.finetune_cfg_hash(summary)


@pytest.mark.skipif(not _SUMMARY.is_file(), reason="DAPG summary artifact not present")
def test_sha256_file_reproduces_raw_summary_hash():
    assert I.sha256_file(_SUMMARY) == _RAW_SUMMARY


def test_sha256_file_fails_closed_on_absent():
    with pytest.raises(FileNotFoundError):
        I.sha256_file(_REPO_ROOT / "thread_isaac_lab/wmso/d1/__DOES_NOT_EXIST__.bin")


@pytest.mark.skipif(
    not all((_REPO_ROOT / m).is_file() for m in I.SCRIPTED_CLOSURE_MEMBERS),
    reason="scripted source-closure members not present",
)
def test_source_closure_reproduces_pinned_and_is_order_independent():
    assert I.source_closure_sha256(I.SCRIPTED_CLOSURE_MEMBERS, _REPO_ROOT) == _SCRIPTED_CLOSURE
    assert I.source_closure_sha256(I.WAIT_CLOSURE_MEMBERS, _REPO_ROOT) == _WAIT_CLOSURE
    reordered = tuple(reversed(I.SCRIPTED_CLOSURE_MEMBERS))
    assert I.source_closure_sha256(reordered, _REPO_ROOT) == _SCRIPTED_CLOSURE
    # WAIT closure strictly contains SCRIPTED, so its aggregate must differ.
    assert _WAIT_CLOSURE != _SCRIPTED_CLOSURE


def test_source_closure_fails_closed_on_missing_member():
    with pytest.raises(FileNotFoundError):
        I.source_closure_sha256(("thread_isaac_lab/__NOPE__.py",), _REPO_ROOT)


def test_scripted_and_wait_identities_are_distinct_per_skill():
    a = I.scripted_identity("TRANSPORT", "transport_to_clip", _REPO_ROOT)
    b = I.scripted_identity("RECLAMP_L", "reclamp_left", _REPO_ROOT)
    # Same source closure, different skill_id + qualname => distinct keys (pN B4).
    assert a.source_closure_sha256 == b.source_closure_sha256
    assert (a.skill_id, a.callable_qualname) != (b.skill_id, b.callable_qualname)


@pytest.mark.skipif(not _SUMMARY.is_file(), reason="artifacts not present")
def test_learned_identity_bc_rl_and_rl_only():
    final = _APPROACH_DIR / "model_best.pt"
    base = _REPO_ROOT / "thread_isaac_lab/data/base_model_mixed_20260404_190016.pt"
    if not (final.is_file() and base.is_file()):
        pytest.skip("checkpoints not present")
    bc_rl = I.learned_identity_from_files(
        final_policy_path=final,
        family=PolicyFamily.BC_RL,
        base_ckpt_path=base,
        finetune_summary_path=_SUMMARY,
        association_strength=AssociationStrength.RECORDED_PATH_CONFIG_COLOCATION,
    )
    assert bc_rl.train_time_crypto_bound is False
    assert bc_rl.lineage.base_ckpt_hash is not None
    assert bc_rl.lineage.finetune_cfg_hash == _FINETUNE_CFG

    model9 = _REPO_ROOT / "thread_isaac_lab/logs/rsl_rl/insert_clip_20260325_235722/model_9.pt"
    if not model9.is_file():
        pytest.skip("RL-only checkpoint not present")
    rl_only = I.learned_identity_from_files(
        final_policy_path=model9,
        family=PolicyFamily.PPO,
        association_strength=AssociationStrength.NOT_APPLICABLE_RL_ONLY,
    )
    assert rl_only.lineage.base_ckpt_hash is None
    assert rl_only.lineage.finetune_cfg_hash is None
