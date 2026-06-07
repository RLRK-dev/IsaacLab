#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Cascade C synthetic dataset generator — Track 1 (controlled failure injection).

Generates ~400 synthetic samples for fine-tuning the Nemotron Mini 4B fault
classifier (Cascade C, ``LL-Cascade-C-Nemotron-Design.md`` §3 + §4). 5 failure
modes (F1-F5) × 4 skills (AC / IC / AR / Grip) per the Qwen design §4.2 Track 1
inheritance map (model-agnostic). F4 is Grip-only; AC/IC/AR/Grip cover F1/F2/F3/F5.

Output (CPU-only, no env step required):
    data/cascade_c_dataset_v0/
        dataset.jsonl                  # 400 samples (one JSON per line)
        manifest.json                  # generation metadata + seed + thresholds
        coverage_distribution.json     # F1-F7 × skill counts (F6/F7 = 0, deferred)
        schema_validation.json         # per-sample schema PASS/FAIL audit

Usage:
    python thread_isaac_lab/scripts/cascade_c_dataset_gen.py \
        --output data/cascade_c_dataset_v0 --seed 0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", "configs"))

from task_config import (  # noqa: E402
    CABLE_RADIUS,
    K_CLAMP,
    T_ALIGN,
    T_DIST,
    T_DIST_APPROACH,
    T_FINGER,
)

# ---------------------------------------------------------------------------
# Constants — orchestrator-side (read-only mirror; SSOT is routing_orchestrator)
# ---------------------------------------------------------------------------
MAX_RETRY = 3  # routing_orchestrator.py:859
MAX_ROLLBACK_DEPTH = 3  # routing_orchestrator.py:860
DEFAULT_RL_MAX_STEPS = 240  # AC/IC/AR per-skill default; Grip clamp is shorter

SKILLS_4 = ["ApproachCable", "InsertIntoClip", "AerialRegrasp", "Clamp"]
SKILL_ABBREV = {
    "ApproachCable": "AC",
    "InsertIntoClip": "IC",
    "AerialRegrasp": "AR",
    "Clamp": "Grip",
}

# Failure mode F1-F5 buckets (F4 Grip-only); F6/F7 deferred per Qwen §4.2
FAILURE_MODES_TRACK1 = ["F1", "F2", "F3", "F4", "F5"]
F4_SKILL_ALLOWLIST = {"Clamp"}  # Grip-only per Qwen §4.2

# Per-bucket sample counts: 20 each except F4_Grip = 80 (covers F4_AC/IC/AR=0)
SAMPLES_PER_BUCKET_DEFAULT = 20
SAMPLES_PER_BUCKET_F4_GRIP = 80
TARGET_TOTAL_SAMPLES = 400  # 4 modes × 4 skills × 20 + 1 F4_Grip × 80

VERDICT_VALUES = ["OK", "PRE_FAIL_DETECTED", "OOD_HIGH", "RECOVERY_PROPOSE"]
SCHEMA_VERSION = "cascade_c_v0_2026-05-03"


# ---------------------------------------------------------------------------
# Sample structure
# ---------------------------------------------------------------------------
@dataclass
class SampleInput:
    obs: dict
    log_per_world: dict
    extras: dict
    context: dict


@dataclass
class RecommendedAction:
    skill_override: str | None
    retry_seed_override: int | None
    scripted_fallback: bool
    rollback_depth_hint: int


@dataclass
class ExpectedOutput:
    verdict: str
    confidence: float
    failure_mode: str
    recommended_action: RecommendedAction
    reasoning: str


@dataclass
class Sample:
    sample_id: str
    track: str
    skill: str
    failure_mode_gt: str
    input: SampleInput
    expected_output: ExpectedOutput


# ---------------------------------------------------------------------------
# Failure-mode injection logic (deterministic, per Qwen §4.2)
# ---------------------------------------------------------------------------
def _baseline_log_per_world(skill: str, rng: random.Random) -> dict:
    """Return a near-success baseline log_per_world (used as anchor, then perturbed)."""
    if skill == "Clamp":
        # Grip near-success: dist <= T_DIST, finger <= T_FINGER, ori <= T_ALIGN
        return {
            "explosion": [False],
            "success": [False],
            "dist_pos_l": [rng.uniform(0.5 * T_DIST, 0.95 * T_DIST)],
            "dist_pos_r": [rng.uniform(0.5 * T_DIST, 0.95 * T_DIST)],
            "dist_ori_l": [rng.uniform(0.3 * T_ALIGN, 0.9 * T_ALIGN)],
            "dist_ori_r": [rng.uniform(0.3 * T_ALIGN, 0.9 * T_ALIGN)],
            "finger_l": [rng.uniform(0.3 * T_FINGER, 0.9 * T_FINGER)],
            "finger_r": [rng.uniform(0.3 * T_FINGER, 0.9 * T_FINGER)],
        }
    # AC / IC / AR: looser pos tolerance, finger usually OPEN (~T_FINGER * 3)
    open_finger = max(T_FINGER * 3.0, 0.04)
    return {
        "explosion": [False],
        "success": [False],
        "dist_pos_l": [rng.uniform(0.3 * T_DIST_APPROACH, 0.9 * T_DIST_APPROACH)],
        "dist_pos_r": [rng.uniform(0.3 * T_DIST_APPROACH, 0.9 * T_DIST_APPROACH)],
        "dist_ori_l": [rng.uniform(0.3 * T_ALIGN, 0.9 * T_ALIGN)],
        "dist_ori_r": [rng.uniform(0.3 * T_ALIGN, 0.9 * T_ALIGN)],
        "finger_l": [open_finger * rng.uniform(0.9, 1.1)],
        "finger_r": [open_finger * rng.uniform(0.9, 1.1)],
    }


def _baseline_obs(skill: str, rng: random.Random) -> dict:
    """Return summarized obs dict (proprio subset relevant for fault classification)."""
    return {
        "ee_pos_l": [rng.gauss(0.3, 0.02), rng.gauss(-0.11, 0.02), rng.gauss(1.02, 0.02)],
        "ee_pos_r": [rng.gauss(0.3, 0.02), rng.gauss(0.01, 0.02), rng.gauss(1.02, 0.02)],
        "ee_quat_l": [0.0, 0.0, 0.0, 1.0],  # identity (placeholder; A1 may extend)
        "ee_quat_r": [0.0, 0.0, 0.0, 1.0],
        "joint_vel_norm_l": rng.uniform(0.01, 0.5),
        "joint_vel_norm_r": rng.uniform(0.01, 0.5),
        "step_progress": rng.uniform(0.1, 0.95),
    }


def inject_F1_explosion(obs: dict, lpw: dict, extras: dict, rng: random.Random) -> None:
    """F1: NaN cascade / dist > 1.0 m physics breakdown.

    Source: ``derive_skill_result`` line 411 (explosion flag is OR'd).
    Synthetic signal: log_per_world['explosion'][0] = True + extreme dist values.
    """
    lpw["explosion"][0] = True
    arm_idx = rng.choice(["l", "r"])
    lpw[f"dist_pos_{arm_idx}"][0] = rng.uniform(1.0, 5.0)
    obs[f"joint_vel_norm_{arm_idx}"] = rng.uniform(20.0, 100.0)


def inject_F2_cable_drop(obs: dict, lpw: dict, extras: dict, rng: random.Random) -> None:
    """F2: cable Z drop / grasp loss (proposed key, currently subsumed by FAIL).

    Source: design memo §5.4 "F2 cable drop → CABLE_DROP → rollback (env extras
    key 未実装、現状 FAIL に subsume per L391-394)". Synthetic key proposed:
    log_per_world['cable_drop'][0] = True + cable_z below table.
    """
    lpw["cable_drop"] = [True]
    lpw["cable_z_world"] = [rng.uniform(0.2, 0.7)]  # below table (TABLE_HEIGHT≈0.8)
    # finger may have opened during drop
    lpw["finger_l"][0] = rng.uniform(T_FINGER * 1.5, T_FINGER * 5)
    lpw["finger_r"][0] = rng.uniform(T_FINGER * 1.5, T_FINGER * 5)


def inject_F3_timeout(obs: dict, lpw: dict, extras: dict, rng: random.Random) -> None:
    """F3: max_steps reached without success.

    Source: derive_skill_result line 418-420 (time_outs == 1, success False).
    Synthetic signal: extras['time_outs'][0] = 1 + obs.step_progress = 1.0.
    """
    extras["time_outs"] = [1]
    obs["step_progress"] = 1.0
    # dist may be close to threshold but not satisfying for K_CLAMP sustain
    lpw["dist_pos_l"][0] = rng.uniform(T_DIST_APPROACH * 0.4, T_DIST_APPROACH * 1.5)
    lpw["dist_pos_r"][0] = rng.uniform(T_DIST_APPROACH * 0.4, T_DIST_APPROACH * 1.5)


def inject_F4_partial_success(obs: dict, lpw: dict, extras: dict, rng: random.Random) -> None:
    """F4: clamp_r_ok=True, clamp_l_ok=False (or vice versa).

    Source: Qwen §4.2 "F4 partial success (Grip-CLAMP only) | clamp_r_ok=True /
    clamp_l_ok=False fixed obs | Grip | 80". Synthetic: one arm satisfies all 3
    Clamp criteria (T_DIST, T_ALIGN, T_FINGER) for K_CLAMP sustain, the other
    fails at least one criterion.

    Half R-only / half L-only for distribution coverage.
    """
    r_only = rng.random() < 0.5  # 50/50 for R-only vs L-only

    if r_only:
        # R-arm: all 3 satisfied
        lpw["dist_pos_r"][0] = rng.uniform(0.0, 0.95 * T_DIST)
        lpw["dist_ori_r"][0] = rng.uniform(0.0, 0.9 * T_ALIGN)
        lpw["finger_r"][0] = rng.uniform(0.5 * T_FINGER, 0.95 * T_FINGER)
        # L-arm: at least one fails
        which_fail = rng.choice(["pos", "ori", "finger"])
        if which_fail == "pos":
            lpw["dist_pos_l"][0] = rng.uniform(2 * T_DIST, 5 * T_DIST)
        elif which_fail == "ori":
            lpw["dist_ori_l"][0] = rng.uniform(1.2 * T_ALIGN, 3 * T_ALIGN)
        else:
            lpw["finger_l"][0] = rng.uniform(1.2 * T_FINGER, 3 * T_FINGER)
        lpw["partial_arm"] = "R"
    else:
        # L-arm: all 3 satisfied
        lpw["dist_pos_l"][0] = rng.uniform(0.0, 0.95 * T_DIST)
        lpw["dist_ori_l"][0] = rng.uniform(0.0, 0.9 * T_ALIGN)
        lpw["finger_l"][0] = rng.uniform(0.5 * T_FINGER, 0.95 * T_FINGER)
        which_fail = rng.choice(["pos", "ori", "finger"])
        if which_fail == "pos":
            lpw["dist_pos_r"][0] = rng.uniform(2 * T_DIST, 5 * T_DIST)
        elif which_fail == "ori":
            lpw["dist_ori_r"][0] = rng.uniform(1.2 * T_ALIGN, 3 * T_ALIGN)
        else:
            lpw["finger_r"][0] = rng.uniform(1.2 * T_FINGER, 3 * T_FINGER)
        lpw["partial_arm"] = "L"


def inject_F5_ood(obs: dict, lpw: dict, extras: dict, rng: random.Random) -> None:
    """F5: OOD policy / BC P0 region 外.

    Source: Qwen §4.2 "F5 OOD policy | obs に Gaussian noise (σ=2x training σ)
    inject". Synthetic: dist values >2σ outside training range, joint_vel high.
    """
    sigma_mult = rng.uniform(2.5, 4.0)
    lpw["dist_pos_l"][0] = T_DIST_APPROACH * sigma_mult * rng.uniform(0.8, 1.2)
    lpw["dist_pos_r"][0] = T_DIST_APPROACH * sigma_mult * rng.uniform(0.8, 1.2)
    obs["joint_vel_norm_l"] = rng.uniform(2.0, 8.0)
    obs["joint_vel_norm_r"] = rng.uniform(2.0, 8.0)
    # OOD ee position: cable region drift > 5 cm
    obs["ee_pos_l"][0] += rng.gauss(0.0, 0.10)
    obs["ee_pos_r"][0] += rng.gauss(0.0, 0.10)


_INJECTORS = {
    "F1": inject_F1_explosion,
    "F2": inject_F2_cable_drop,
    "F3": inject_F3_timeout,
    "F4": inject_F4_partial_success,
    "F5": inject_F5_ood,
}


# ---------------------------------------------------------------------------
# Verdict generation (ground-truth labels, deterministic per failure mode)
# ---------------------------------------------------------------------------
def make_expected_verdict(failure_mode: str, skill: str, rng: random.Random) -> ExpectedOutput:
    """Deterministic ground-truth verdict per (failure_mode, skill) bucket."""
    if failure_mode == "F1":
        return ExpectedOutput(
            verdict="PRE_FAIL_DETECTED",
            confidence=round(rng.uniform(0.95, 0.99), 3),
            failure_mode="F1",
            recommended_action=RecommendedAction(
                skill_override=None,
                retry_seed_override=None,
                scripted_fallback=False,
                rollback_depth_hint=rng.choice([2, 3]),
            ),
            reasoning=(
                f"Explosion flag asserted in log_per_world; dist_pos exceeds 1.0 m "
                f"safety bound. Physics breakdown imminent during {skill}; abort "
                f"current attempt and rollback to a stable pre-grasp state."
            ),
        )
    if failure_mode == "F2":
        return ExpectedOutput(
            verdict="PRE_FAIL_DETECTED",
            confidence=round(rng.uniform(0.92, 0.97), 3),
            failure_mode="F2",
            recommended_action=RecommendedAction(
                skill_override=None,
                retry_seed_override=None,
                scripted_fallback=False,
                rollback_depth_hint=rng.choice([1, 2]),
            ),
            reasoning=(
                f"Cable Z below table plane (cable_drop flag) and fingers wider "
                f"than 1.5×T_FINGER → grasp lost during {skill}. Rollback to "
                f"prior grasp-stable STEP and re-establish bilateral clamp."
            ),
        )
    if failure_mode == "F3":
        return ExpectedOutput(
            verdict="RECOVERY_PROPOSE",
            confidence=round(rng.uniform(0.85, 0.95), 3),
            failure_mode="F3",
            recommended_action=RecommendedAction(
                skill_override=None,
                retry_seed_override=rng.randint(1, 10_000),
                scripted_fallback=False,
                rollback_depth_hint=0,
            ),
            reasoning=(
                f"time_outs flag set with success=False during {skill}; max "
                f"episode steps reached without satisfying skill criterion. "
                f"Retry with seed perturbation (orchestrator MAX_RETRY=3, C7 path)."
            ),
        )
    if failure_mode == "F4":
        partial = "R-only" if rng.random() < 0.5 else "L-only"
        return ExpectedOutput(
            verdict="RECOVERY_PROPOSE",
            confidence=round(rng.uniform(0.88, 0.95), 3),
            failure_mode="F4",
            recommended_action=RecommendedAction(
                skill_override=None,
                retry_seed_override=None,
                scripted_fallback=True,
                rollback_depth_hint=1,
            ),
            reasoning=(
                f"Bilateral AND failed but {partial} clamp criterion satisfied "
                f"(dist<T_DIST, ori<T_ALIGN, finger<T_FINGER). Per-arm tracker "
                f"path applies; scripted_fallback (HalfUnclamp+Release) reduces "
                f"asymmetry before next CLAMP attempt."
            ),
        )
    # F5
    return ExpectedOutput(
        verdict="OOD_HIGH",
        confidence=round(rng.uniform(0.75, 0.90), 3),
        failure_mode="F5",
        recommended_action=RecommendedAction(
            skill_override=None,
            retry_seed_override=None,
            scripted_fallback=True,
            rollback_depth_hint=1,
        ),
        reasoning=(
            f"obs dist_pos and joint_vel_norm exceed 2σ training range "
            f"(BC P0 region 外); {skill} policy unlikely to converge. "
            f"Rollback 1 STEP and prefer scripted recovery path."
        ),
    )


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------
def generate_sample(
    failure_mode: str,
    skill: str,
    sample_idx: int,
    rng: random.Random,
) -> Sample:
    """Generate a single synthetic sample with injected failure mode."""
    obs = _baseline_obs(skill, rng)
    lpw = _baseline_log_per_world(skill, rng)
    extras = {"time_outs": [0]}

    _INJECTORS[failure_mode](obs, lpw, extras, rng)

    skill_abbrev = SKILL_ABBREV[skill]
    sample_id = f"{failure_mode}_{skill_abbrev}_{sample_idx:03d}"

    return Sample(
        sample_id=sample_id,
        track="synthetic",
        skill=skill,
        failure_mode_gt=failure_mode,
        input=SampleInput(
            obs=obs,
            log_per_world=lpw,
            extras=extras,
            context={
                "skill_name": skill,
                "step_id": _representative_step_id(skill, rng),
                "attempt": rng.randint(1, MAX_RETRY),
                "max_retry": MAX_RETRY,
                "max_episode_steps": DEFAULT_RL_MAX_STEPS,
                "thresholds": {
                    "T_DIST": T_DIST,
                    "T_DIST_APPROACH": T_DIST_APPROACH,
                    "T_ALIGN": T_ALIGN,
                    "T_FINGER": T_FINGER,
                    "K_CLAMP": K_CLAMP,
                    "CABLE_RADIUS": CABLE_RADIUS,
                },
            },
        ),
        expected_output=make_expected_verdict(failure_mode, skill, rng),
    )


def _representative_step_id(skill: str, rng: random.Random) -> int:
    """Return a representative STEP id for the skill (for prompt context)."""
    if skill == "ApproachCable":
        return 3  # Phase A
    if skill == "InsertIntoClip":
        return rng.choice([7, 15, 23, 31, 39])  # C1-C5 insert positions
    if skill == "AerialRegrasp":
        return rng.choice([13, 21, 29, 37])  # C2-C5 aerial regrasp
    return rng.choice([4, 16, 24, 32, 40])  # Clamp at A or per-clip


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def validate_sample(sample: Sample) -> list[str]:
    """Return a list of validation errors; empty list means PASS."""
    errors: list[str] = []
    out = sample.expected_output

    if out.verdict not in VERDICT_VALUES:
        errors.append(f"verdict not in {VERDICT_VALUES}: {out.verdict}")
    if not (0.0 <= out.confidence <= 1.0):
        errors.append(f"confidence out of [0,1]: {out.confidence}")
    if out.failure_mode not in FAILURE_MODES_TRACK1 + ["F6", "F7", "OK"]:
        errors.append(f"failure_mode unexpected: {out.failure_mode}")
    if not 0 <= out.recommended_action.rollback_depth_hint <= MAX_ROLLBACK_DEPTH:
        errors.append(
            f"rollback_depth_hint out of [0,{MAX_ROLLBACK_DEPTH}]: {out.recommended_action.rollback_depth_hint}"
        )
    if not isinstance(out.recommended_action.scripted_fallback, bool):
        errors.append("scripted_fallback not bool")
    if out.recommended_action.skill_override is not None:
        if out.recommended_action.skill_override not in SKILLS_4 + [
            "ReClamp(L)",
            "TransportToClip",
            "HalfUnclamp+Release",
            "ClipConfirm",
        ]:
            errors.append(f"skill_override unknown: {out.recommended_action.skill_override}")
    if not isinstance(out.reasoning, str) or len(out.reasoning) < 10:
        errors.append("reasoning missing or too short")

    # Bucket-specific GT consistency (F1-F5)
    if sample.failure_mode_gt == "F4" and sample.skill not in F4_SKILL_ALLOWLIST:
        errors.append(f"F4 generated outside Grip allowlist: {sample.skill}")
    if sample.failure_mode_gt != out.failure_mode:
        errors.append(f"failure_mode_gt ({sample.failure_mode_gt}) != verdict.failure_mode ({out.failure_mode})")
    return errors


# ---------------------------------------------------------------------------
# Top-level dataset build
# ---------------------------------------------------------------------------
def build_dataset(seed: int) -> tuple[list[Sample], dict, dict]:
    """Build the full Track-1 synthetic dataset.

    Returns:
        samples: list of ~400 samples
        coverage: per-(failure_mode, skill) count + F1-F7 totals
        validation: per-sample errors summary
    """
    master_rng = random.Random(seed)
    samples: list[Sample] = []
    coverage: dict[str, dict[str, int]] = {fm: {} for fm in ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]}
    for fm in coverage:
        for sk in SKILLS_4:
            coverage[fm][SKILL_ABBREV[sk]] = 0

    for failure_mode in FAILURE_MODES_TRACK1:
        for skill in SKILLS_4:
            if failure_mode == "F4" and skill not in F4_SKILL_ALLOWLIST:
                continue  # F4 Grip-only; AC/IC/AR contribute 0 (covered by F4_Grip=80)
            count = (
                SAMPLES_PER_BUCKET_F4_GRIP
                if failure_mode == "F4" and skill in F4_SKILL_ALLOWLIST
                else SAMPLES_PER_BUCKET_DEFAULT
            )
            # Per-bucket child RNG for reproducibility regardless of generation order.
            # hashlib (not builtin hash()) for cross-process stability — PYTHONHASHSEED
            # randomizes the builtin and breaks bit-identical regeneration.
            bucket_tag = f"{failure_mode}_{skill}".encode()
            bucket_hash = int.from_bytes(hashlib.sha256(bucket_tag).digest()[:4], "big")
            bucket_seed = master_rng.getrandbits(32) ^ bucket_hash
            bucket_rng = random.Random(bucket_seed)
            for i in range(count):
                samples.append(generate_sample(failure_mode, skill, i, bucket_rng))
                coverage[failure_mode][SKILL_ABBREV[skill]] += 1

    validation_summary = {
        "total_samples": len(samples),
        "pass_count": 0,
        "fail_count": 0,
        "errors_per_sample": {},
    }
    for sample in samples:
        errs = validate_sample(sample)
        if errs:
            validation_summary["fail_count"] += 1
            validation_summary["errors_per_sample"][sample.sample_id] = errs
        else:
            validation_summary["pass_count"] += 1

    return samples, coverage, validation_summary


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------
def _sample_to_jsonl_dict(sample: Sample) -> dict:
    """Convert dataclass to JSON-serializable dict (one line of JSONL)."""
    d = asdict(sample)
    # nested dataclasses already flattened by asdict
    return d


def write_outputs(
    output_dir: Path,
    samples: list[Sample],
    coverage: dict,
    validation: dict,
    seed: int,
    elapsed_s: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. dataset.jsonl
    dataset_path = output_dir / "dataset.jsonl"
    with dataset_path.open("w") as f:
        for s in samples:
            f.write(json.dumps(_sample_to_jsonl_dict(s), separators=(",", ":")) + "\n")

    # SHA-256 for provenance
    h = hashlib.sha256()
    with dataset_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    dataset_sha256 = h.hexdigest()

    # 2. manifest.json
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_unix": time.time(),
        "generator_script": "thread_isaac_lab/scripts/cascade_c_dataset_gen.py",
        "design_memo": "thread_isaac_lab/thread-vault/06-Knowledge/LL-Cascade-C-Nemotron-Design.md",
        "design_memo_section": "§3 (Qwen §4.2 Track 1 inheritance)",
        "node_id": "T-WM-G2-A0",
        "track": "synthetic",
        "seed": seed,
        "elapsed_s": round(elapsed_s, 3),
        "total_samples": len(samples),
        "target_total": TARGET_TOTAL_SAMPLES,
        "skills_covered": SKILLS_4,
        "failure_modes_track1": FAILURE_MODES_TRACK1,
        "failure_modes_deferred": ["F6 (vision Phase 2)", "F7 (FAIL-subsumed)"],
        "thresholds_used": {
            "T_DIST": T_DIST,
            "T_DIST_APPROACH": T_DIST_APPROACH,
            "T_ALIGN": T_ALIGN,
            "T_FINGER": T_FINGER,
            "K_CLAMP": K_CLAMP,
            "CABLE_RADIUS": CABLE_RADIUS,
            "MAX_RETRY": MAX_RETRY,
            "MAX_ROLLBACK_DEPTH": MAX_ROLLBACK_DEPTH,
        },
        "dataset_sha256": dataset_sha256,
        "schema_fields": [
            "sample_id",
            "track",
            "skill",
            "failure_mode_gt",
            "input.obs",
            "input.log_per_world",
            "input.extras",
            "input.context",
            "expected_output.verdict",
            "expected_output.confidence",
            "expected_output.failure_mode",
            "expected_output.recommended_action",
            "expected_output.reasoning",
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # 3. coverage_distribution.json (F1-F7 × skill matrix)
    skill_totals = {sk: sum(coverage[fm][sk] for fm in coverage) for sk in [SKILL_ABBREV[s] for s in SKILLS_4]}
    fm_totals = {fm: sum(coverage[fm].values()) for fm in coverage}
    cov_report = {
        "matrix": coverage,
        "per_skill_totals": skill_totals,
        "per_failure_mode_totals": fm_totals,
        "grand_total": sum(fm_totals.values()),
        "notes": {
            "F4": "Grip-only (Qwen §4.2); AC/IC/AR show 0 by spec",
            "F6": "Cable slack — vision feature required, Phase 2 deferred",
            "F7": "Finger close fail — subsumed by SkillResult.FAIL in Cluster G",
        },
    }
    (output_dir / "coverage_distribution.json").write_text(json.dumps(cov_report, indent=2) + "\n")

    # 4. schema_validation.json
    (output_dir / "schema_validation.json").write_text(json.dumps(validation, indent=2) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cascade C Track-1 synthetic dataset generator")
    p.add_argument(
        "--output",
        type=Path,
        default=Path("data/cascade_c_dataset_v0"),
        help="Output directory (will be created)",
    )
    p.add_argument("--seed", type=int, default=0, help="Master RNG seed (default 0)")
    p.add_argument(
        "--target-total",
        type=int,
        default=TARGET_TOTAL_SAMPLES,
        help="Sanity check on total sample count (default 400)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    print(f"[cascade_c_dataset_gen] seed={args.seed} target={args.target_total}", flush=True)

    t0 = time.time()
    samples, coverage, validation = build_dataset(args.seed)
    elapsed = time.time() - t0

    if len(samples) != args.target_total:
        print(
            f"[FATAL] sample count mismatch: got {len(samples)}, expected {args.target_total}",
            file=sys.stderr,
            flush=True,
        )
        return 2
    if validation["fail_count"] > 0:
        print(
            f"[FATAL] schema validation failures: {validation['fail_count']}/{len(samples)}",
            file=sys.stderr,
            flush=True,
        )
        return 3

    write_outputs(args.output, samples, coverage, validation, args.seed, elapsed)
    print(
        f"[cascade_c_dataset_gen] wrote {len(samples)} samples to {args.output} "
        f"in {elapsed:.2f}s (PASS={validation['pass_count']}, "
        f"FAIL={validation['fail_count']})",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
