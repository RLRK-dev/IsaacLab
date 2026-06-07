# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Late Fusion Phase 1 baseline measurement entry skeleton (no-fusion / vision-off).

T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Skeleton (T-ROOT-COORD#s11
2026-05-05). Entry script skeleton for Phase 1 baseline measurement reference
establishment per ``thread-vault/06-Knowledge/LL-Vision-Fusion-Phase1-Baseline.md``
(~700 lines). This module locks the public CLI surface + dataclass schema +
entry function signatures; implementation is deferred to a separate task
(`CC-L1A-Phase-5-4-Baseline-Measurement`).

R6 boundary discipline:

- This script is in ``scripts/vision/`` (R6 outer layer; CLI entry script).
- Imports restricted to: ``argparse``, ``json``, ``pathlib``, ``dataclasses``,
  ``subprocess``, ``numpy``, ``torch``, plus stdlib helpers.
- Does NOT import ``thread_isaac_lab.estimators.*`` (no-fusion path bypasses
  the entire Fusion estimator stack per design memo §2.1 Variant Z1
  boundary preservation).
- Does NOT import ``thread_isaac_lab.envs.*`` (env file改変禁止 per
  T-Vision-Fusion/state.md §4 + this leaf's TOUCH FORBIDDEN list).
- Does NOT modify ``thread_isaac_lab/scripts/eval_skill.py`` directly;
  invokes it as a subprocess with the ``--no-vision`` flag (impl-phase
  flag add per design memo §3.3 + this leaf's interface contract).

Design memo cross-refs (line numbers refer to LL-Vision-Fusion-Phase1-Baseline.md):

- §0 (line 12) — Executive summary: 4-axis backward-fill Variant Z1+Z2 +
  baseline metric definition + Phase 2/3 differential + eval protocol
- §2.1 (line 96) — Variant Z1 (45D no-vision baseline) architecture spec
- §2.2 (line 127) — Variant Z2 (50D zero-init bit-identical baseline) spec
- §3.1 (line 184) — Per-skill baseline policy specification (5 skills)
- §3.3 (line 202) — Eval orchestration CLI signature
- §4.1 (line 232) — Per-skill per-mode per-seed SR + output schema
- §4.2 (line 258) — Bootstrap CI 95% computation
- §4.3 (line 297) — Per-clip-index SR distribution
- §4.4 (line 319) — Z1 vs Z2 bit-identical gate
- §5.2 (line 350) — Phase 2 §8 ablation matrix C-1 cell substitution
- §5.3 (line 379) — Phase 3 Variant A baseline starting point linkage
- §6.1 (line 408) — Eval orchestration wall budget breakdown
- §7 (line 458) — Per-skill measurement matrix (5 skills × 2 modes × 5 seeds)
- §8 (line 501) — Bit-identical baseline gate execution protocol
- §10 (line 558) — Integration with downstream consumers

Phase: SKELETON (T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Skeleton).
Implementation deferred to ``CC-L1A-Phase-5-4-Baseline-Measurement`` (a
separate CC session triggered after this skeleton + interface doc commit).
Every compute method raises :class:`NotImplementedError`.

Usage (impl phase; raises NotImplementedError today):

    # Step 1: bit-identical smoke gate (~50 min pre-execution)
    python thread_isaac_lab/scripts/vision/fusion_phase1_baseline.py \\
        --mode bit-identical-gate \\
        --skills ac,ic_approach,ic_insert,ar,grip_clamp,clamp_r \\
        --output-dir data/test_baseline_phase1/

    # Step 2: main baseline measurement (Z2 primary, Z1 fallback)
    python thread_isaac_lab/scripts/vision/fusion_phase1_baseline.py \\
        --mode main \\
        --skills ac,ic_approach,ic_insert,ar,grip_clamp,clamp_r \\
        --variant z2 \\
        --eval-modes det,stoch \\
        --seeds 0,1,2,3,4 \\
        --num-eps-per-seed 10 \\
        --num-clips 5 \\
        --output-dir data/test_baseline_phase1/

    # Step 3: aggregation post-execution
    python thread_isaac_lab/scripts/vision/fusion_phase1_baseline.py \\
        --mode aggregate \\
        --output-dir data/test_baseline_phase1/

Existing assets reused (subprocess stub):

- ``thread_isaac_lab/scripts/eval_skill.py`` — unified policy eval entry;
  invoked via subprocess with ``--no-vision`` flag (impl-phase flag add).
- ``thread_isaac_lab/scripts/migrate_first_layer_45_to_50.py`` (planned;
  not yet implemented) — CC4 v3.2 §3 Appendix E.5 zero-init migration
  script; invoked via subprocess.

Output structure:

    data/test_baseline_phase1/
    ├── bit_identical_gate/
    │   └── <skill>/<seed>/Z<1|2>/RUN_METRICS.json
    ├── main/
    │   └── <skill>/<mode>/<seed>/RUN_METRICS.json
    ├── aggregate/
    │   ├── per_skill_summary.json    # per-skill bootstrap CI 95% aggregation
    │   ├── per_clip_distribution.json  # per-clip-index SR distribution
    │   ├── bit_identical_gate_verdict.json  # gate PASS/WARN/FAIL summary
    │   └── baseline_summary.json  # cross-skill aggregation (Phase 2 §8 C-1 supply)
    └── logs/
        └── fusion_phase1_baseline_<run_id>.log
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# stdlib-only at module scope; numpy/torch/subprocess imported lazily inside
# entry functions to keep skeleton import smoke-test fast.


# ---------------------------------------------------------------------------
# CLI signature constants (design memo §3.3 + interface contract)
# ---------------------------------------------------------------------------

#: Supported skills per design memo §3.1 (5 skills × 2 modes × 5 seeds = 50 cells).
#: ``ic_approach`` and ``ic_insert`` are eval_skill.py SKILL_REGISTRY entries
#: per ``thread_isaac_lab/scripts/eval_skill.py`` lines 71-145.
_SUPPORTED_SKILLS = (
    "ac",
    "ic_approach",
    "ic_insert",
    "ar",
    "grip_clamp",
    "clamp_r",
)

#: Per-skill base trained checkpoint (45D, Variant Z1) per design memo §3.1
#: table line 184. Paths are illustrative; actual checkpoint paths are
#: resolved via ``--checkpoint-root`` CLI flag (impl phase).
_CHECKPOINT_PATHS_45D = {
    "ac": "checkpoints/AC/v23-baseline-45D/",
    "ic_approach": "checkpoints/IC/v26-baseline-45D/",
    "ic_insert": "checkpoints/IC/v26-baseline-45D/",
    "ar": "checkpoints/AR/v29-baseline-45D/",
    "grip_clamp": "checkpoints/Grip-CLAMP/v16-baseline-45D/",
    "clamp_r": "checkpoints/CLAMP-R/baseline-45D/",
}

#: Per-skill post-migration 50D zero-init checkpoint (Variant Z2) per
#: design memo §3.1 table. Generated by ``migrate_first_layer_45_to_50``
#: subprocess invocation per §3.2.
_CHECKPOINT_PATHS_50D = {
    "ac": "checkpoints/AC/v23-baseline-50D-zero-init/",
    "ic_approach": "checkpoints/IC/v26-baseline-50D-zero-init/",
    "ic_insert": "checkpoints/IC/v26-baseline-50D-zero-init/",
    "ar": "checkpoints/AR/v29-baseline-50D-zero-init/",
    "grip_clamp": "checkpoints/Grip-CLAMP/v16-baseline-50D-zero-init/",
    "clamp_r": "checkpoints/CLAMP-R/baseline-50D-zero-init/",
}

#: Bit-identical gate tolerance per design memo §4.4 decision matrix.
_BIT_IDENTICAL_GATE_PASS_THRESHOLD_PP = 0.5  # < 0.5pp → PASS
_BIT_IDENTICAL_GATE_WARN_THRESHOLD_PP = 1.0  # 0.5-1.0pp → WARN; ≥1.0pp → FAIL

#: Bootstrap CI 95% resample count per design memo §4.2.
_BOOTSTRAP_RESAMPLES = 1000
_BOOTSTRAP_CI_LEVEL = 0.95

#: Default seed-fragile detection threshold per design memo §4.2 (CC4 v3.2 §H
#: reproducibility convention). Used to flag policies whose per-seed SR
#: variance exceeds 5pp; consumed by Phase 2 ablation matrix downstream.
_SEED_FRAGILE_THRESHOLD_PP = 5.0

#: Default per-skill measurement defaults per design memo §6.1 + §7.1.
_DEFAULT_NUM_EPS_PER_SEED = 10
_DEFAULT_NUM_CLIPS = 5
_DEFAULT_SEEDS = (0, 1, 2, 3, 4)
_DEFAULT_EVAL_MODES = ("det", "stoch")


# ---------------------------------------------------------------------------
# Output schema dataclasses (design memo §4.1 + §4.2 + §4.3)
# ---------------------------------------------------------------------------


@dataclass
class PerEvalRunMetrics:
    """Per-eval (skill, variant, mode, seed) RUN_METRICS schema (design memo §4.1).

    Output target: ``data/test_baseline_phase1/main/<skill>/<mode>/<seed>/RUN_METRICS.json``.
    Schema validated against existing ``schema_v1`` + Phase 1 baseline
    extension fields (``variant``, ``per_clip_sr``, ``bit_identical_passed``).

    Attributes:
        phase: literal "phase1_baseline" (schema discriminator)
        variant: "z1" (45D no-vision) | "z2" (50D zero-init bit-identical)
        skill: one of :data:`_SUPPORTED_SKILLS`
        mode: "det" (deterministic) | "stoch" (stochastic policy)
        seed: integer per-seed identifier
        num_eps: total episodes for this (skill, mode, seed) cell
        successes: count of episodes where success_condition == True
        sr: float ∈ [0, 1] = successes / num_eps
        per_clip_sr: 5-element list of per-clip SR (clip 1..5; design memo §4.3)
        wall_clock_sec: elapsed wall time in seconds
        checkpoint: path to checkpoint used (relative to repo root)
    """

    phase: str  # literal "phase1_baseline"
    variant: str  # "z1" | "z2"
    skill: str
    mode: str  # "det" | "stoch"
    seed: int
    num_eps: int
    successes: int
    sr: float
    per_clip_sr: list[float]  # length-5 list (per-clip SR for clips 1-5)
    wall_clock_sec: float
    checkpoint: str


@dataclass
class PerSkillAggregate:
    """Per-skill per-mode aggregated bootstrap CI 95% (design memo §4.2).

    Output target: ``data/test_baseline_phase1/aggregate/per_skill_summary.json``.

    Attributes:
        skill: one of :data:`_SUPPORTED_SKILLS`
        mode: "det" | "stoch"
        variant: "z1" | "z2"
        n_seeds: number of seeds aggregated (default 5)
        n_eps_per_seed: episodes per seed (default 10)
        n_total_eps: total episodes = n_seeds × n_eps_per_seed
        sr_mean: bootstrap-resampled mean SR
        sr_ci_lower_95: lower 2.5 percentile of bootstrap distribution
        sr_ci_upper_95: upper 97.5 percentile of bootstrap distribution
        sr_per_seed: per-seed SR (length n_seeds)
        seed_variance: variance of sr_per_seed in pp²
        seed_fragile: True if seed_variance > _SEED_FRAGILE_THRESHOLD_PP²
            (CC4 v3.2 §H reproducibility convention)
    """

    skill: str
    mode: str  # "det" | "stoch"
    variant: str  # "z1" | "z2"
    n_seeds: int
    n_eps_per_seed: int
    n_total_eps: int
    sr_mean: float
    sr_ci_lower_95: float
    sr_ci_upper_95: float
    sr_per_seed: list[float]
    seed_variance: float
    seed_fragile: bool


@dataclass
class PerClipDistribution:
    """Per-clip-index SR distribution (design memo §4.3).

    Output target: ``data/test_baseline_phase1/aggregate/per_clip_distribution.json``.

    Used by Phase 2 §8 G-V14 6-cell + G-V15 20-cell ablation matrix C-1
    baseline cell substitution + Phase 3 Variant A starting point pinning.

    Attributes:
        skill: one of :data:`_SUPPORTED_SKILLS`
        mode: "det" | "stoch"
        variant: "z1" | "z2"
        per_clip_sr_mean: 5-element list of per-clip SR mean (clips 1-5)
        per_clip_sr_ci_lower_95: 5-element list of bootstrap CI lower
        per_clip_sr_ci_upper_95: 5-element list of bootstrap CI upper
        clip_uniformity: std dev of per_clip_sr_mean / mean SR (uniformity index)
    """

    skill: str
    mode: str  # "det" | "stoch"
    variant: str  # "z1" | "z2"
    per_clip_sr_mean: list[float]
    per_clip_sr_ci_lower_95: list[float]
    per_clip_sr_ci_upper_95: list[float]
    clip_uniformity: float


@dataclass
class BitIdenticalGateVerdict:
    """Z1 vs Z2 bit-identical smoke gate verdict (design memo §4.4 + §8).

    Output target: ``data/test_baseline_phase1/aggregate/bit_identical_gate_verdict.json``.

    Per-skill smoke (5 ep × 1 seed × Z1 vs Z2) → SR delta computation.
    Decision matrix per design memo §4.4:

    - delta < 0.5pp → PASS (main measurement OK)
    - 0.5pp ≤ delta < 1.0pp → WARN (Rs review trigger, OQ-B6)
    - delta ≥ 1.0pp → FAIL (CC4 v3.2 §3 Appendix E.5 zero-init invariant
      violation; main measurement halt; ``CC-L1A-Migration-Debug`` trigger)

    Attributes:
        skill: one of :data:`_SUPPORTED_SKILLS`
        z1_sr: SR from Variant Z1 smoke (5 ep × 1 seed)
        z2_sr: SR from Variant Z2 smoke (5 ep × 1 seed)
        delta_pp: |z1_sr - z2_sr| × 100
        verdict: "PASS" | "WARN" | "FAIL"
    """

    skill: str
    z1_sr: float
    z2_sr: float
    delta_pp: float
    verdict: str  # "PASS" | "WARN" | "FAIL"


@dataclass
class CrossSkillBaselineSummary:
    """Cross-skill aggregation for Phase 2 §8 ablation C-1 supply (design memo §10.1).

    Output target: ``data/test_baseline_phase1/aggregate/baseline_summary.json``.

    Substitutes the placeholder SR (silent baseline 推測値) in Phase 2 §8
    5-skill ablation matrix C-1 cell for vision integration delta:
    ``delta_<modality>_<skill> = C-<modality>_<skill>_SR - C-1_<skill>_SR``.

    Also serves as Phase 3 §2 Variant A baseline starting point pin
    (Variant A = Z2 by construction per design memo §5.3).

    Attributes:
        per_skill_aggregates: dict mapping skill → {"det": PerSkillAggregate,
            "stoch": PerSkillAggregate}
        per_skill_clip_distributions: dict mapping skill → {"det":
            PerClipDistribution, "stoch": PerClipDistribution}
        bit_identical_gate_verdicts: dict mapping skill →
            BitIdenticalGateVerdict
        gate_overall_verdict: "PASS" | "WARN" | "FAIL" (worst-case across
            per-skill verdicts)
        variant_a_starting_point: dict mapping skill → Z2 ckpt path
            (consumed by Phase 3 §2 Variant A starting point pinning)
        wall_clock_total_sec: total elapsed wall time across all measurements
        run_id: timestamp identifier (YYYYMMDD_HHMMSS)
    """

    per_skill_aggregates: dict = field(default_factory=dict)
    per_skill_clip_distributions: dict = field(default_factory=dict)
    bit_identical_gate_verdicts: dict = field(default_factory=dict)
    gate_overall_verdict: str = "PENDING"
    variant_a_starting_point: dict = field(default_factory=dict)
    wall_clock_total_sec: float = 0.0
    run_id: str = ""


# ---------------------------------------------------------------------------
# CLI argument parser (design memo §3.3 + interface contract)
# ---------------------------------------------------------------------------


def build_argparser() -> argparse.ArgumentParser:
    """Build CLI parser per design memo §3.3 + interface contract.

    Returns:
        argparse.ArgumentParser with the following modes:

        - ``--mode bit-identical-gate`` — pre-execution smoke gate (~50 min,
          5 skills × 10 min, 5 ep × 1 seed × Z1 vs Z2 per skill)
        - ``--mode main`` — main baseline measurement (Z2 primary, ~12-15h
          GPU on cuda:2 sequential per-skill stratified)
        - ``--mode aggregate`` — post-execution aggregation (per-skill
          bootstrap CI 95% + per-clip distribution + cross-skill summary)

        See :func:`main` for invocation flow.
    """
    parser = argparse.ArgumentParser(
        prog="fusion_phase1_baseline",
        description=(
            "Late Fusion Phase 1 baseline measurement entry "
            "(no-fusion / vision-off baseline reference establishment). "
            "Skeleton stub; impl pending CC-L1A-Phase-5-4-Baseline-Measurement."
        ),
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=("bit-identical-gate", "main", "aggregate"),
        required=True,
        help=(
            "Execution mode: 'bit-identical-gate' for pre-execution smoke "
            "(~50 min); 'main' for main baseline measurement "
            "(~12-15h GPU); 'aggregate' for post-execution aggregation."
        ),
    )

    parser.add_argument(
        "--skills",
        type=str,
        default=",".join(_SUPPORTED_SKILLS),
        help=(
            "Comma-separated skill list (subset of "
            f"{','.join(_SUPPORTED_SKILLS)}). Default: all 5 skills."
        ),
    )

    parser.add_argument(
        "--variant",
        type=str,
        choices=("z1", "z2"),
        default="z2",
        help=(
            "Baseline variant: 'z1' (45D no-vision) | 'z2' (50D zero-init "
            "bit-identical, primary). Used by 'main' mode only; "
            "'bit-identical-gate' mode runs both Z1+Z2 by design."
        ),
    )

    parser.add_argument(
        "--eval-modes",
        type=str,
        default=",".join(_DEFAULT_EVAL_MODES),
        help=(
            "Comma-separated eval modes: 'det' (deterministic) | 'stoch' "
            "(stochastic). Default: both."
        ),
    )

    parser.add_argument(
        "--seeds",
        type=str,
        default=",".join(str(s) for s in _DEFAULT_SEEDS),
        help=(
            "Comma-separated seed list (default: 0,1,2,3,4 = 5 seeds for "
            "bootstrap CI 95% per design memo §4.2)."
        ),
    )

    parser.add_argument(
        "--num-eps-per-seed",
        type=int,
        default=_DEFAULT_NUM_EPS_PER_SEED,
        help=(
            f"Episodes per (skill, mode, seed) cell. "
            f"Default: {_DEFAULT_NUM_EPS_PER_SEED} (5 seeds × 10 ep × 5 clips "
            "= 250 ep per (skill, mode))."
        ),
    )

    parser.add_argument(
        "--num-clips",
        type=int,
        default=_DEFAULT_NUM_CLIPS,
        help=(
            f"Clip count for 1-clip ablation (default: {_DEFAULT_NUM_CLIPS}). "
            "Requires T-L1-B Phase 5-3 multi-clip orchestrator ready."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/test_baseline_phase1"),
        help="Output root directory. Default: data/test_baseline_phase1/",
    )

    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("checkpoints"),
        help="Checkpoint root directory. Default: checkpoints/",
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help=(
            "CUDA device for eval_skill.py subprocess invocation. Default: "
            "cuda:0 (env_isaaclab6 venv with CUDA_VISIBLE_DEVICES=2)."
        ),
    )

    parser.add_argument(
        "--no-vision-flag-name",
        type=str,
        default="--no-vision",
        help=(
            "CLI flag to disable vision pipeline in eval_skill.py "
            "subprocess (impl-phase add). Default: --no-vision."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print planned subprocess invocations without executing. "
            "Used by 'main' mode for wall budget validation pre-execution."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# Mode 1: bit-identical gate (design memo §4.4 + §8)
# ---------------------------------------------------------------------------


def run_bit_identical_gate(
    skills: list[str],
    output_dir: Path,
    checkpoint_root: Path,
    device: str,
    no_vision_flag_name: str,
    dry_run: bool = False,
) -> dict[str, BitIdenticalGateVerdict]:
    """Pre-execution Z1 vs Z2 bit-identical smoke gate (design memo §8.1).

    Execution protocol (~50 min total, 5 skills × 10 min each):

    1. Variant Z1 ckpt verification (per-skill 1 ep eval-det smoke)
    2. Variant Z2 generation (per-skill ``migrate_first_layer_45_to_50``
       subprocess execution)
    3. Variant Z2 ckpt verification (per-skill 1 ep eval-det smoke + first
       layer weight inspection ``weight[:, 45:50] == 0`` strict equality)
    4. Bit-identical smoke: per-skill 5 ep × 1 seed × Z1 vs Z2 → SR delta
    5. Decision per §4.4 decision matrix (PASS / WARN / FAIL)

    Args:
        skills: list of skill names (subset of :data:`_SUPPORTED_SKILLS`)
        output_dir: output root directory (verdict written to
            ``<output_dir>/aggregate/bit_identical_gate_verdict.json``)
        checkpoint_root: checkpoint root directory
        device: CUDA device for eval_skill.py subprocess
        no_vision_flag_name: CLI flag name (default ``--no-vision``)
        dry_run: if True, print planned invocations without executing

    Returns:
        dict mapping skill → :class:`BitIdenticalGateVerdict`

    Raises:
        NotImplementedError: skeleton stub. Impl pending
            ``CC-L1A-Phase-5-4-Baseline-Measurement``. See
            ``LL-Vision-Fusion-Phase1-Baseline.md`` §4.4 + §8 for impl spec.
    """
    raise NotImplementedError(
        "run_bit_identical_gate: skeleton stub. "
        "Impl pending CC-L1A-Phase-5-4-Baseline-Measurement. "
        "See LL-Vision-Fusion-Phase1-Baseline.md §4.4 (line 319) + §8 "
        "(line 501) for impl spec."
    )


def _invoke_migration_script(
    skill: str,
    z1_ckpt: Path,
    z2_ckpt: Path,
    dry_run: bool = False,
) -> None:
    """Invoke ``migrate_first_layer_45_to_50`` subprocess (design memo §3.2).

    CC4 v3.2 §3 Appendix E.5 zero-init invariant: forall obs ∈ 45D obs space,
    Z2.policy(pad_zero(obs)) ≡ Z1.policy(obs) within ϵ tolerance.

    Args:
        skill: one of :data:`_SUPPORTED_SKILLS`
        z1_ckpt: source 45D checkpoint path
        z2_ckpt: destination 50D zero-init checkpoint path
        dry_run: if True, print planned invocation without executing

    Raises:
        NotImplementedError: skeleton stub. Impl pending; subprocess
            invocation of ``thread_isaac_lab/scripts/migrate_first_layer_45_to_50.py``
            (a separate script, not yet implemented per design memo §1.4
            boundary discipline).
    """
    raise NotImplementedError(
        "_invoke_migration_script: skeleton stub. "
        "Impl pending; subprocess invocation of "
        "thread_isaac_lab/scripts/migrate_first_layer_45_to_50.py "
        "(separate script, see LL-Vision-Fusion-Phase1-Baseline.md §3.2 "
        "for spec). CC4 v3.2 §3 Appendix E.5 zero-init invariant must hold."
    )


def _verify_z2_first_layer_zero_init(
    z2_ckpt: Path,
    base_obs_dim: int = 45,
    augmented_obs_dim: int = 50,
) -> bool:
    """Strict equality check: ``weight[:, 45:50] == 0`` (design memo §3.2 step 3).

    Per CC4 v3.2 §3 Appendix E.5 zero-init invariant, the first layer weight
    matrix [augmented_obs_dim, hidden] must have columns
    [base_obs_dim:augmented_obs_dim] = 0 strictly.

    Args:
        z2_ckpt: 50D zero-init checkpoint path
        base_obs_dim: pre-migration obs dim (default 45)
        augmented_obs_dim: post-migration obs dim (default 50)

    Returns:
        True iff weight[:, base_obs_dim:augmented_obs_dim] == 0 strictly.

    Raises:
        NotImplementedError: skeleton stub. Impl loads checkpoint via
            ``torch.load`` + inspects ``policy.state_dict()`` keys per
            actor-critic structure.
    """
    raise NotImplementedError(
        "_verify_z2_first_layer_zero_init: skeleton stub. "
        "Impl loads checkpoint via torch.load + inspects first layer weight "
        "shape [50, hidden] with strict zero-equality on columns [45:50]. "
        "See LL-Vision-Fusion-Phase1-Baseline.md §3.2 step 3."
    )


# ---------------------------------------------------------------------------
# Mode 2: main baseline measurement (design memo §6 + §7)
# ---------------------------------------------------------------------------


def run_main_baseline(
    skills: list[str],
    variant: str,
    eval_modes: list[str],
    seeds: list[int],
    num_eps_per_seed: int,
    num_clips: int,
    output_dir: Path,
    checkpoint_root: Path,
    device: str,
    no_vision_flag_name: str,
    dry_run: bool = False,
) -> list[PerEvalRunMetrics]:
    """Main baseline measurement orchestration (design memo §6.1 + §7.1).

    Wall budget: ~12-15h GPU on cuda:2 sequential per-skill stratified order
    (AC → IC → AR → Grip-CLAMP → CLAMP-R per OQ-B7).

    Per-skill per-mode per-seed eval invocation (design memo §3.3 CLI):

        CUDA_VISIBLE_DEVICES=2 python eval_skill.py \\
            --skill <skill> --eval-mode <det|stoch> --seed <seed> \\
            --num-eps <num_eps_per_seed> --no-vision \\
            --variant <z1|z2> --checkpoint <ckpt_path>

    Per-clip-index 1-clip ablation: env reset 経で current_clip_idx を
    per-eval で fix (5-clip chain 単一 clip eval). Requires T-L1-B Phase 5-3
    multi-clip orchestrator ready (external blocker per design memo §6.3
    note).

    Args:
        skills: list of skill names (stratified order applied)
        variant: "z1" | "z2" (Z2 primary per gate PASS)
        eval_modes: list of "det" / "stoch"
        seeds: list of seed integers
        num_eps_per_seed: episodes per (skill, mode, seed) cell
        num_clips: clip count for 1-clip ablation
        output_dir: output root directory
        checkpoint_root: checkpoint root directory
        device: CUDA device for eval_skill.py subprocess
        no_vision_flag_name: CLI flag name (default ``--no-vision``)
        dry_run: if True, print planned invocations without executing

    Returns:
        list of :class:`PerEvalRunMetrics` (one per (skill, mode, seed) cell)

    Raises:
        NotImplementedError: skeleton stub. Impl pending
            ``CC-L1A-Phase-5-4-Baseline-Measurement``. See
            ``LL-Vision-Fusion-Phase1-Baseline.md`` §6 + §7 for impl spec.
    """
    raise NotImplementedError(
        "run_main_baseline: skeleton stub. "
        "Impl pending CC-L1A-Phase-5-4-Baseline-Measurement. "
        "See LL-Vision-Fusion-Phase1-Baseline.md §6.1 (line 408) + §7.1 "
        "(line 458) for impl spec."
    )


def _invoke_eval_skill_subprocess(
    skill: str,
    eval_mode: str,
    seed: int,
    num_eps: int,
    variant: str,
    checkpoint: Path,
    output_dir: Path,
    device: str,
    no_vision_flag_name: str,
    clip_idx: int | None = None,
    dry_run: bool = False,
) -> PerEvalRunMetrics:
    """Invoke ``eval_skill.py`` subprocess with ``--no-vision`` flag (design memo §3.3).

    Subprocess invocation pattern:

        subprocess.run([
            "python", "thread_isaac_lab/scripts/eval_skill.py",
            "--skill", skill,
            "--eval-mode", eval_mode,
            "--seed", str(seed),
            "--num-eps", str(num_eps),
            no_vision_flag_name,
            "--variant", variant,
            "--checkpoint", str(checkpoint),
            "--output-dir", str(output_dir),
            "--device", device,
            *(["--clip-idx", str(clip_idx)] if clip_idx is not None else []),
        ], check=True)

    Args:
        skill: one of :data:`_SUPPORTED_SKILLS`
        eval_mode: "det" | "stoch"
        seed: integer seed
        num_eps: episodes for this cell
        variant: "z1" | "z2"
        checkpoint: checkpoint path
        output_dir: per-cell output directory
            (``<output_dir>/<skill>/<mode>/<seed>/``)
        device: CUDA device
        no_vision_flag_name: CLI flag name (default ``--no-vision``;
            impl-phase add to eval_skill.py)
        clip_idx: optional clip index for 1-clip ablation (1..5; if None,
            full 5-clip eval)
        dry_run: if True, print invocation without executing

    Returns:
        :class:`PerEvalRunMetrics` parsed from
        ``<output_dir>/<skill>/<mode>/<seed>/RUN_METRICS.json``

    Raises:
        NotImplementedError: skeleton stub. Impl-phase fills in subprocess
            invocation + RUN_METRICS.json schema validation + parse to
            :class:`PerEvalRunMetrics`. ``--no-vision`` and ``--variant``
            and ``--clip-idx`` flag adds to eval_skill.py are separate
            impl-phase scope (per OQ-IS-2).
    """
    raise NotImplementedError(
        "_invoke_eval_skill_subprocess: skeleton stub. "
        "Impl invokes thread_isaac_lab/scripts/eval_skill.py subprocess "
        "with --no-vision flag (impl-phase flag add per OQ-IS-2). "
        "See LL-Vision-Fusion-Phase1-Baseline.md §3.3 (line 202) for "
        "subprocess invocation spec."
    )


# ---------------------------------------------------------------------------
# Mode 3: aggregation (design memo §4.2 + §4.3 + §7.3 + §10)
# ---------------------------------------------------------------------------


def run_aggregate(
    output_dir: Path,
    bootstrap_resamples: int = _BOOTSTRAP_RESAMPLES,
    bootstrap_ci_level: float = _BOOTSTRAP_CI_LEVEL,
) -> CrossSkillBaselineSummary:
    """Post-execution aggregation orchestration (design memo §4.2 + §7.3 + §10).

    Steps:

    1. Discover per-eval RUN_METRICS.json files in ``<output_dir>/main/``
    2. Per-skill per-mode aggregation: bootstrap CI 95% (resample 1000)
    3. Per-clip-index distribution: clip uniformity computation
    4. Bit-identical gate verdict aggregation (gate_overall_verdict)
    5. Variant A starting point pinning (Z2 ckpt → Phase 3 §2 reference)
    6. Cross-skill aggregation: write ``baseline_summary.json``

    Args:
        output_dir: output root directory (must contain ``main/`` and
            optionally ``bit_identical_gate/`` subdirectories)
        bootstrap_resamples: bootstrap resample count (default 1000)
        bootstrap_ci_level: CI level (default 0.95)

    Returns:
        :class:`CrossSkillBaselineSummary` written to
        ``<output_dir>/aggregate/baseline_summary.json``

    Raises:
        NotImplementedError: skeleton stub. Impl pending
            ``CC-L1A-Phase-5-4-Baseline-Measurement``.
    """
    raise NotImplementedError(
        "run_aggregate: skeleton stub. "
        "Impl pending CC-L1A-Phase-5-4-Baseline-Measurement. "
        "See LL-Vision-Fusion-Phase1-Baseline.md §4.2 (line 258) + §7.3 "
        "(line 488) + §10 (line 558) for impl spec."
    )


def _bootstrap_ci(
    successes_per_seed: list[int],
    num_eps_per_seed: int,
    n_resamples: int = _BOOTSTRAP_RESAMPLES,
    ci_level: float = _BOOTSTRAP_CI_LEVEL,
) -> tuple[float, float, float]:
    """Bootstrap CI 95% computation (design memo §4.2 pseudocode).

    Aggregates per-seed successes into a single 50-ep population, then
    bootstraps ``n_resamples`` times to estimate SR mean + CI.

    Args:
        successes_per_seed: list of integer success counts (length n_seeds)
        num_eps_per_seed: episodes per seed (default 10)
        n_resamples: bootstrap resample count (default 1000)
        ci_level: CI level (default 0.95)

    Returns:
        Tuple of (sr_mean, ci_lower, ci_upper) all in [0, 1].

    Raises:
        NotImplementedError: skeleton stub. Impl uses ``numpy.random.choice``
            with replace=True on flattened binary outcomes (design memo §4.2).
    """
    raise NotImplementedError(
        "_bootstrap_ci: skeleton stub. "
        "Impl per LL-Vision-Fusion-Phase1-Baseline.md §4.2 pseudocode "
        "(line 263): np.concatenate per-seed binary outcomes, "
        "np.random.choice resample, np.percentile for CI bounds."
    )


def _compute_per_clip_distribution(
    per_eval_metrics: list[PerEvalRunMetrics],
    skill: str,
    mode: str,
    variant: str,
) -> PerClipDistribution:
    """Per-clip-index SR distribution computation (design memo §4.3).

    Aggregates per-eval ``per_clip_sr`` lists across seeds into per-clip
    mean + bootstrap CI 95% + clip uniformity index.

    Args:
        per_eval_metrics: list of :class:`PerEvalRunMetrics` for this cell
        skill: one of :data:`_SUPPORTED_SKILLS`
        mode: "det" | "stoch"
        variant: "z1" | "z2"

    Returns:
        :class:`PerClipDistribution` with per-clip mean + CI + uniformity.

    Raises:
        NotImplementedError: skeleton stub.
    """
    raise NotImplementedError(
        "_compute_per_clip_distribution: skeleton stub. "
        "Impl per LL-Vision-Fusion-Phase1-Baseline.md §4.3 (line 297). "
        "Aggregates per_clip_sr across seeds, computes per-clip mean + CI, "
        "clip_uniformity = std(per_clip_sr_mean) / mean(per_clip_sr_mean)."
    )


def _aggregate_bit_identical_verdicts(
    per_skill_verdicts: dict[str, BitIdenticalGateVerdict],
) -> str:
    """Aggregate per-skill bit-identical gate verdicts to overall (design memo §8).

    Worst-case aggregation: any skill FAIL → overall FAIL; else any WARN
    → overall WARN; else PASS.

    Args:
        per_skill_verdicts: dict mapping skill → :class:`BitIdenticalGateVerdict`

    Returns:
        "PASS" | "WARN" | "FAIL"

    Raises:
        NotImplementedError: skeleton stub.
    """
    raise NotImplementedError(
        "_aggregate_bit_identical_verdicts: skeleton stub. "
        "Impl per LL-Vision-Fusion-Phase1-Baseline.md §8.2 + §4.4 decision "
        "matrix. Worst-case aggregation across skills."
    )


# ---------------------------------------------------------------------------
# Phase 2/3 integration stubs (design memo §5.2 + §5.3 + §10)
# ---------------------------------------------------------------------------


def export_phase2_ablation_c1_supply(
    summary: CrossSkillBaselineSummary,
    output_path: Path,
) -> None:
    """Export Phase 2 §8 ablation matrix C-1 baseline cell supply (design memo §5.2 + §10.1).

    Substitutes the placeholder SR (silent baseline 推測値) in Phase 2 §8
    5-skill ablation matrix C-1 cell. Output schema per design memo §5.2:

        {
            "AC C-1 SR": <det aggregated SR>,
            "IC_approach C-1 SR": <det aggregated SR>,
            "IC_insert C-1 SR": <det aggregated SR>,
            "AR C-1 SR": <det aggregated SR>,
            "Grip-CLAMP C-1 SR": <det aggregated SR>,
            "CLAMP-R C-1 SR": <det aggregated SR>,  // or null per OQ-B2
        }

    Vision integration delta (Phase 2 design memo internal computation,
    not in this skeleton scope):
    ``delta_<modality>_<skill> = C-<modality>_<skill>_SR - C-1_<skill>_SR``

    Args:
        summary: :class:`CrossSkillBaselineSummary` from :func:`run_aggregate`
        output_path: target JSON path
            (``<output_dir>/aggregate/phase2_c1_supply.json``)

    Raises:
        NotImplementedError: skeleton stub. Impl-phase scope (per design
            memo §1.4 boundary discipline; downstream consumer Phase 2 design
            memo internal computation).
    """
    raise NotImplementedError(
        "export_phase2_ablation_c1_supply: skeleton stub. "
        "Impl per LL-Vision-Fusion-Phase1-Baseline.md §5.2 (line 350) + "
        "§10.1 (line 562). Substitutes Phase 2 §8 C-1 cell placeholder SR."
    )


def export_phase3_variant_a_starting_point(
    summary: CrossSkillBaselineSummary,
    output_path: Path,
) -> None:
    """Export Phase 3 §2 Variant A baseline starting point pin (design memo §5.3 + §10.2).

    Variant A = Z2 by construction (pure concat passthrough = 50D zero-init
    bit-identical baseline). Output schema:

        {
            "AC Variant A ckpt": "<Z2 ckpt path>",
            "IC_approach Variant A ckpt": "<Z2 ckpt path>",
            ...
            "AC Variant A SR det": <z2 det aggregated SR>,
            "AC Variant A SR stoch": <z2 stoch aggregated SR>,
            ...
        }

    MVP-4+ Variant promotion gate (Variant B/C/D/E ≥ Variant A baseline
    floor) consumes this output (Phase 3 design memo internal, not in this
    skeleton scope).

    Args:
        summary: :class:`CrossSkillBaselineSummary` from :func:`run_aggregate`
        output_path: target JSON path
            (``<output_dir>/aggregate/phase3_variant_a_starting_point.json``)

    Raises:
        NotImplementedError: skeleton stub. Impl-phase scope (per design
            memo §1.4 boundary discipline).
    """
    raise NotImplementedError(
        "export_phase3_variant_a_starting_point: skeleton stub. "
        "Impl per LL-Vision-Fusion-Phase1-Baseline.md §5.3 (line 379) + "
        "§10.2 (line 572). Variant A = Z2 by construction; ckpt pinning "
        "for MVP-4+ promotion gate."
    )


# ---------------------------------------------------------------------------
# Main entry (skeleton dispatch)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Main entry: dispatch to mode-specific orchestration (design memo §3.3).

    Skeleton dispatch flow:

    - ``--mode bit-identical-gate`` → :func:`run_bit_identical_gate`
    - ``--mode main`` → :func:`run_main_baseline` →
      :func:`export_phase2_ablation_c1_supply` +
      :func:`export_phase3_variant_a_starting_point`
    - ``--mode aggregate`` → :func:`run_aggregate` →
      :func:`export_phase2_ablation_c1_supply` +
      :func:`export_phase3_variant_a_starting_point`

    Args:
        argv: optional CLI argument list (default: ``sys.argv[1:]``)

    Returns:
        0 on success; non-zero on failure (e.g., bit-identical gate FAIL,
        wall budget overshoot, schema validation FAIL).

    Raises:
        NotImplementedError: skeleton stub for all entry function calls;
            argparse + dispatch logic functional but mode-specific runs
            raise per their respective NotImplementedError.
    """
    parser = build_argparser()
    args = parser.parse_args(argv)

    skills = [s.strip() for s in args.skills.split(",") if s.strip()]
    eval_modes = [m.strip() for m in args.eval_modes.split(",") if m.strip()]
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]

    # Validate skill list
    for skill in skills:
        if skill not in _SUPPORTED_SKILLS:
            print(
                f"ERROR: unsupported skill '{skill}'; "
                f"supported: {','.join(_SUPPORTED_SKILLS)}",
                file=sys.stderr,
            )
            return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d_%H%M%S")

    if args.mode == "bit-identical-gate":
        verdicts = run_bit_identical_gate(
            skills=skills,
            output_dir=args.output_dir,
            checkpoint_root=args.checkpoint_root,
            device=args.device,
            no_vision_flag_name=args.no_vision_flag_name,
            dry_run=args.dry_run,
        )
        # Stub: write verdict JSON
        verdict_path = args.output_dir / "aggregate" / "bit_identical_gate_verdict.json"
        verdict_path.parent.mkdir(parents=True, exist_ok=True)
        # Impl phase: serialize verdicts to JSON
        return 0

    elif args.mode == "main":
        per_eval_metrics = run_main_baseline(
            skills=skills,
            variant=args.variant,
            eval_modes=eval_modes,
            seeds=seeds,
            num_eps_per_seed=args.num_eps_per_seed,
            num_clips=args.num_clips,
            output_dir=args.output_dir,
            checkpoint_root=args.checkpoint_root,
            device=args.device,
            no_vision_flag_name=args.no_vision_flag_name,
            dry_run=args.dry_run,
        )
        # Stub: per-eval RUN_METRICS already written by subprocess
        return 0

    elif args.mode == "aggregate":
        summary = run_aggregate(args.output_dir)
        export_phase2_ablation_c1_supply(
            summary,
            args.output_dir / "aggregate" / "phase2_c1_supply.json",
        )
        export_phase3_variant_a_starting_point(
            summary,
            args.output_dir / "aggregate" / "phase3_variant_a_starting_point.json",
        )
        return 0

    else:
        # argparse choices guard prevents this branch
        print(f"ERROR: unknown mode '{args.mode}'", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
