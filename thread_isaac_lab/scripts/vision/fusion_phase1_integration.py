# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Late Fusion Phase 1 baseline integration entry (env-independent actual logic).

T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Integration (T-ROOT-COORD#s11
2026-05-05). Sister to ``fusion_phase1_baseline.py`` (skeleton with
NotImplementedError stubs); this module implements the env-independent
parts of the Phase 1 baseline pipeline so that downstream consumers
(Phase 2 §8 ablation matrix C-1 cell, Phase 3 §2 Variant A starting point)
can be served as soon as actual measurements are dropped into the output
directory by ``CC-L1A-Phase-5-4-Baseline-Measurement``.

Scope
-----

Actual logic (this module):

- ``run_aggregate`` — post-execution aggregation pipeline (env-independent).
- ``_bootstrap_ci`` — bootstrap CI 95% (numpy resample 1000 per design memo §4.2).
- ``_compute_per_clip_distribution`` — per-clip mean + bootstrap CI + uniformity.
- ``_aggregate_bit_identical_verdicts`` — worst-case verdict aggregation.
- ``_decide_bit_identical_verdict`` — per-skill decision matrix (PASS/WARN/FAIL).
- ``export_phase2_ablation_c1_supply`` — Phase 2 §8 C-1 cell JSON serialization.
- ``export_phase3_variant_a_starting_point`` — Phase 3 §2 Variant A ckpt pin.
- ``_load_per_eval_metrics`` / ``_validate_per_eval_schema`` — JSON IO + schema check.
- ``run_bit_identical_gate`` (dry-run) / ``run_main_baseline`` (dry-run) —
  subprocess invocation pattern print (no actual execution).

Dry-run stub (this module):

- Subprocess invocation patterns are printed via ``--dry-run`` flag for
  wall-budget validation; actual subprocess execution remains deferred to
  ``CC-L1A-Phase-5-4-Baseline-Measurement``.

Out-of-scope (deferred to actual measurement task):

- Actual ``subprocess.run`` execution of ``eval_skill.py`` / migration script.
- Actual checkpoint I/O (``torch.load`` + ``state_dict`` zero-init verification).
- Env file modification.
- Migration script implementation (separate impl-phase script).

R6 boundary discipline
----------------------

- This script lives in ``scripts/vision/`` (R6 outer layer; CLI entry).
- Module-scope imports: stdlib only (``argparse``, ``json``, ``sys``, ``time``,
  ``pathlib``, ``dataclasses``, ``statistics``).
- Lazy imports inside entry functions: ``numpy`` for bootstrap CI.
- Does NOT import ``thread_isaac_lab.estimators.*`` (Variant Z1 boundary).
- Does NOT import ``thread_isaac_lab.envs.*`` (env file改変禁止).
- Does NOT import ``torch`` (env-dependent ckpt I/O is deferred).

Cross-references
----------------

Design memo cross-refs (line numbers refer to LL-Vision-Fusion-Phase1-Baseline.md):

- §3.3 (line 202) — Eval orchestration CLI signature
- §4.1 (line 232) — Per-skill per-mode per-seed SR + output schema
- §4.2 (line 258) — Bootstrap CI 95% computation (numpy pseudocode)
- §4.3 (line 297) — Per-clip-index SR distribution
- §4.4 (line 319) — Z1 vs Z2 bit-identical decision matrix
- §5.2 (line 350) — Phase 2 §8 ablation C-1 cell substitution
- §5.3 (line 379) — Phase 3 Variant A baseline starting point linkage
- §7.3 (line 488) — Aggregation post-execution
- §8.2 (line 525) — Bit-identical gate aggregation (worst-case)
- §10.1 (line 562) — Phase 2 §8 C-1 supply schema
- §10.2 (line 572) — Phase 3 Variant A starting point schema

Skeleton cross-references (sister wave-7 #16 deliverable):

- ``thread_isaac_lab/scripts/vision/fusion_phase1_baseline.py`` — interface
  contract pin (lazy import + NotImplementedError stubs); this integration
  script mirrors the skeleton's CLI + dataclass schema exactly.
- ``thread-vault/T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Skeleton/interface.md``
  — public API surface contract; this script's exported names match.

Phase: INTEGRATION (T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Integration).
Actual measurement execution remains deferred to ``CC-L1A-Phase-5-4-Baseline-Measurement``.

Usage
-----

    # Step 1: dry-run bit-identical smoke gate (prints subprocess pattern)
    python thread_isaac_lab/scripts/vision/fusion_phase1_integration.py \\
        --mode bit-identical-gate \\
        --skills ac,ic_approach,ic_insert,ar,grip_clamp,clamp_r \\
        --output-dir data/test_baseline_phase1/ \\
        --dry-run

    # Step 2: dry-run main baseline measurement (prints subprocess pattern)
    python thread_isaac_lab/scripts/vision/fusion_phase1_integration.py \\
        --mode main \\
        --variant z2 \\
        --output-dir data/test_baseline_phase1/ \\
        --dry-run

    # Step 3: aggregation post-execution (real logic; requires per-cell
    # RUN_METRICS.json files in <output_dir>/main/<skill>/<mode>/<seed>/)
    python thread_isaac_lab/scripts/vision/fusion_phase1_integration.py \\
        --mode aggregate \\
        --output-dir data/test_baseline_phase1/

Output structure
----------------

    data/test_baseline_phase1/
    ├── bit_identical_gate/
    │   └── <skill>/<seed>/Z<1|2>/RUN_METRICS.json     # per-cell, written
    │                                                   # by eval_skill.py
    │                                                   # subprocess (impl phase)
    ├── main/
    │   └── <skill>/<mode>/<seed>/RUN_METRICS.json     # per-cell (impl phase)
    └── aggregate/
        ├── per_skill_summary.json                     # bootstrap CI 95% (this module)
        ├── per_clip_distribution.json                 # per-clip distribution (this module)
        ├── bit_identical_gate_verdict.json            # gate verdicts (this module)
        ├── baseline_summary.json                      # cross-skill summary (this module)
        ├── phase2_c1_supply.json                      # Phase 2 §8 C-1 cell supply (this module)
        └── phase3_variant_a_starting_point.json       # Phase 3 §2 Variant A pin (this module)
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Module-scope imports are stdlib only. ``numpy`` is imported lazily inside
# ``_bootstrap_ci`` to keep ``import fusion_phase1_integration`` fast and
# avoid forcing numpy into environments that only need schema validation.


# ---------------------------------------------------------------------------
# Constants — mirror of skeleton (TOUCH FORBIDDEN: skeleton is input only;
# values duplicated here to keep this module independent of skeleton import)
# ---------------------------------------------------------------------------

#: Supported skills per design memo §3.1 (mirrors skeleton _SUPPORTED_SKILLS).
SUPPORTED_SKILLS = (
    "ac",
    "ic_approach",
    "ic_insert",
    "ar",
    "grip_clamp",
    "clamp_r",
)

#: Per-skill base trained checkpoint (45D, Variant Z1) per design memo §3.1.
CHECKPOINT_PATHS_45D = {
    "ac": "checkpoints/AC/v23-baseline-45D/",
    "ic_approach": "checkpoints/IC/v26-baseline-45D/",
    "ic_insert": "checkpoints/IC/v26-baseline-45D/",
    "ar": "checkpoints/AR/v29-baseline-45D/",
    "grip_clamp": "checkpoints/Grip-CLAMP/v16-baseline-45D/",
    "clamp_r": "checkpoints/CLAMP-R/baseline-45D/",
}

#: Per-skill post-migration 50D zero-init checkpoint (Variant Z2).
CHECKPOINT_PATHS_50D = {
    "ac": "checkpoints/AC/v23-baseline-50D-zero-init/",
    "ic_approach": "checkpoints/IC/v26-baseline-50D-zero-init/",
    "ic_insert": "checkpoints/IC/v26-baseline-50D-zero-init/",
    "ar": "checkpoints/AR/v29-baseline-50D-zero-init/",
    "grip_clamp": "checkpoints/Grip-CLAMP/v16-baseline-50D-zero-init/",
    "clamp_r": "checkpoints/CLAMP-R/baseline-50D-zero-init/",
}

#: Bit-identical gate decision thresholds (design memo §4.4).
BIT_IDENTICAL_GATE_PASS_THRESHOLD_PP = 0.5  # delta < 0.5pp → PASS
BIT_IDENTICAL_GATE_WARN_THRESHOLD_PP = 1.0  # 0.5-1.0pp → WARN; ≥1.0pp → FAIL

#: Bootstrap CI 95% defaults (design memo §4.2).
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_CI_LEVEL = 0.95

#: Seed-fragile detection threshold per CC4 v3.2 §H reproducibility convention.
SEED_FRAGILE_THRESHOLD_PP_SQUARED = 25.0  # variance threshold = (5pp)² = 25 pp²

#: Default measurement parameters (design memo §6.1 + §7.1).
DEFAULT_NUM_EPS_PER_SEED = 10
DEFAULT_NUM_CLIPS = 5
DEFAULT_SEEDS = (0, 1, 2, 3, 4)
DEFAULT_EVAL_MODES = ("det", "stoch")

#: Bootstrap CI deterministic RNG seed (matches Master Verdict Aggregator v2 convention).
BOOTSTRAP_RNG_SEED = 42

#: RUN_METRICS.json schema_v1 + Phase 1 baseline extension required keys.
PER_EVAL_REQUIRED_KEYS = (
    "phase",
    "variant",
    "skill",
    "mode",
    "seed",
    "num_eps",
    "successes",
    "sr",
    "per_clip_sr",
    "wall_clock_sec",
    "checkpoint",
)


# ---------------------------------------------------------------------------
# Output schema dataclasses — mirror of skeleton (1:1 mapping per
# T-Vision-Fusion-Impl-Phase-1-Baseline-Actual-Impl-Skeleton/interface.md §3)
# ---------------------------------------------------------------------------


@dataclass
class PerEvalRunMetrics:
    """Per-eval (skill, variant, mode, seed) RUN_METRICS schema (design memo §4.1).

    Mirrors :class:`fusion_phase1_baseline.PerEvalRunMetrics`.
    """

    phase: str
    variant: str
    skill: str
    mode: str
    seed: int
    num_eps: int
    successes: int
    sr: float
    per_clip_sr: list[float]
    wall_clock_sec: float
    checkpoint: str


@dataclass
class PerSkillAggregate:
    """Per-skill per-mode aggregated bootstrap CI 95% (design memo §4.2)."""

    skill: str
    mode: str
    variant: str
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
    """Per-clip-index SR distribution (design memo §4.3)."""

    skill: str
    mode: str
    variant: str
    per_clip_sr_mean: list[float]
    per_clip_sr_ci_lower_95: list[float]
    per_clip_sr_ci_upper_95: list[float]
    clip_uniformity: float


@dataclass
class BitIdenticalGateVerdict:
    """Z1 vs Z2 bit-identical smoke gate verdict (design memo §4.4 + §8)."""

    skill: str
    z1_sr: float
    z2_sr: float
    delta_pp: float
    verdict: str  # "PASS" | "WARN" | "FAIL"


@dataclass
class CrossSkillBaselineSummary:
    """Cross-skill aggregation for Phase 2 §8 ablation C-1 supply (design memo §10.1)."""

    per_skill_aggregates: dict = field(default_factory=dict)
    per_skill_clip_distributions: dict = field(default_factory=dict)
    bit_identical_gate_verdicts: dict = field(default_factory=dict)
    gate_overall_verdict: str = "PENDING"
    variant_a_starting_point: dict = field(default_factory=dict)
    wall_clock_total_sec: float = 0.0
    run_id: str = ""


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------


def build_argparser() -> argparse.ArgumentParser:
    """Build CLI parser; mirrors skeleton interface (3 modes + dry-run flag)."""
    parser = argparse.ArgumentParser(
        prog="fusion_phase1_integration",
        description=(
            "Late Fusion Phase 1 baseline integration entry. Implements "
            "env-independent post-processing (bootstrap CI, Phase 2/3 export, "
            "verdict aggregation) and dry-run subprocess invocation patterns. "
            "Actual execution deferred to CC-L1A-Phase-5-4-Baseline-Measurement."
        ),
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=("bit-identical-gate", "main", "aggregate"),
        required=True,
        help="bit-identical-gate (dry-run + decision logic), main (dry-run), aggregate (real)",
    )
    parser.add_argument(
        "--skills",
        type=str,
        default=",".join(SUPPORTED_SKILLS),
        help=f"Comma-separated skill list (subset of {','.join(SUPPORTED_SKILLS)})",
    )
    parser.add_argument(
        "--variant",
        type=str,
        choices=("z1", "z2"),
        default="z2",
        help="Baseline variant: 'z2' (50D zero-init bit-identical, primary)",
    )
    parser.add_argument(
        "--eval-modes",
        type=str,
        default=",".join(DEFAULT_EVAL_MODES),
        help="Comma-separated eval modes",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default=",".join(str(s) for s in DEFAULT_SEEDS),
        help="Comma-separated seed list",
    )
    parser.add_argument(
        "--num-eps-per-seed",
        type=int,
        default=DEFAULT_NUM_EPS_PER_SEED,
        help=f"Episodes per (skill, mode, seed) cell. Default: {DEFAULT_NUM_EPS_PER_SEED}",
    )
    parser.add_argument(
        "--num-clips",
        type=int,
        default=DEFAULT_NUM_CLIPS,
        help=f"Clip count for 1-clip ablation. Default: {DEFAULT_NUM_CLIPS}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/test_baseline_phase1"),
        help="Output root directory",
    )
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("checkpoints"),
        help="Checkpoint root directory",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help="CUDA device for eval_skill.py subprocess invocation",
    )
    parser.add_argument(
        "--no-vision-flag-name",
        type=str,
        default="--no-vision",
        help="CLI flag name for eval_skill.py (impl-phase add)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned subprocess invocations without executing",
    )
    parser.add_argument(
        "--bootstrap-resamples",
        type=int,
        default=BOOTSTRAP_RESAMPLES,
        help=f"Bootstrap resample count. Default: {BOOTSTRAP_RESAMPLES}",
    )
    parser.add_argument(
        "--bootstrap-ci-level",
        type=float,
        default=BOOTSTRAP_CI_LEVEL,
        help=f"Bootstrap CI level. Default: {BOOTSTRAP_CI_LEVEL}",
    )

    return parser


# ---------------------------------------------------------------------------
# Mode 1: bit-identical gate (dry-run + decision logic; design memo §4.4 + §8)
# ---------------------------------------------------------------------------


def _decide_bit_identical_verdict(z1_sr: float, z2_sr: float, skill: str) -> BitIdenticalGateVerdict:
    """Per-skill decision matrix per design memo §4.4.

    Decision rule:

    - delta < 0.5pp → PASS
    - 0.5pp ≤ delta < 1.0pp → WARN (Rs review trigger; OQ-B6)
    - delta ≥ 1.0pp → FAIL (CC4 v3.2 §3 Appendix E.5 violation;
      ``CC-L1A-Migration-Debug`` trigger)

    Args:
        z1_sr: Variant Z1 SR (5 ep × 1 seed) ∈ [0, 1].
        z2_sr: Variant Z2 SR (5 ep × 1 seed) ∈ [0, 1].
        skill: skill name for the verdict.

    Returns:
        BitIdenticalGateVerdict with delta_pp + verdict computed.
    """
    delta_pp = abs(z1_sr - z2_sr) * 100.0

    if delta_pp < BIT_IDENTICAL_GATE_PASS_THRESHOLD_PP:
        verdict = "PASS"
    elif delta_pp < BIT_IDENTICAL_GATE_WARN_THRESHOLD_PP:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    return BitIdenticalGateVerdict(
        skill=skill,
        z1_sr=z1_sr,
        z2_sr=z2_sr,
        delta_pp=delta_pp,
        verdict=verdict,
    )


def _aggregate_bit_identical_verdicts(
    per_skill_verdicts: dict[str, BitIdenticalGateVerdict],
) -> str:
    """Worst-case aggregation across skills (design memo §8.2).

    Ordering: FAIL > WARN > PASS. Any skill FAIL → overall FAIL; else any
    WARN → overall WARN; else PASS. Empty input returns "PENDING".
    """
    if not per_skill_verdicts:
        return "PENDING"

    verdicts = [v.verdict for v in per_skill_verdicts.values()]
    if "FAIL" in verdicts:
        return "FAIL"
    if "WARN" in verdicts:
        return "WARN"
    return "PASS"


def _print_eval_skill_invocation_pattern(
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
) -> None:
    """Print eval_skill.py subprocess invocation pattern for dry-run mode."""
    cmd_parts = [
        "CUDA_VISIBLE_DEVICES=2",
        "python",
        "thread_isaac_lab/scripts/eval_skill.py",
        f"--skill {skill}",
        f"--eval-mode {eval_mode}",
        f"--seed {seed}",
        f"--num-eps {num_eps}",
        no_vision_flag_name,
        f"--variant {variant}",
        f"--checkpoint {checkpoint}",
        f"--output-dir {output_dir}",
        f"--device {device}",
    ]
    if clip_idx is not None:
        cmd_parts.append(f"--clip-idx {clip_idx}")

    print(" \\\n    ".join(cmd_parts))


def _print_migration_invocation_pattern(skill: str, z1_ckpt: Path, z2_ckpt: Path) -> None:
    """Print migrate_first_layer_45_to_50.py subprocess invocation pattern."""
    cmd_parts = [
        "python",
        "thread_isaac_lab/scripts/migrate_first_layer_45_to_50.py",
        f"--source-checkpoint {z1_ckpt}",
        f"--target-checkpoint {z2_ckpt}",
        "--base-obs-dim 45",
        "--augmented-obs-dim 50",
    ]
    print(" \\\n    ".join(cmd_parts))


def run_bit_identical_gate(
    skills: list[str],
    output_dir: Path,
    checkpoint_root: Path,
    device: str,
    no_vision_flag_name: str,
    dry_run: bool = False,
) -> dict[str, BitIdenticalGateVerdict]:
    """Pre-execution Z1 vs Z2 bit-identical smoke gate orchestration.

    In dry-run mode, prints the subprocess invocation patterns (migration +
    eval_skill.py for both Z1 and Z2 variants per skill) and returns an
    empty verdict dict. Actual subprocess execution is deferred to
    ``CC-L1A-Phase-5-4-Baseline-Measurement``.

    Args:
        skills: list of skill names.
        output_dir: output root directory.
        checkpoint_root: checkpoint root directory.
        device: CUDA device for eval_skill.py.
        no_vision_flag_name: CLI flag name (default ``--no-vision``).
        dry_run: if True, print invocations without executing.

    Returns:
        dict mapping skill → BitIdenticalGateVerdict (empty in dry-run mode).

    Raises:
        NotImplementedError: when dry_run=False (actual subprocess execution
            is deferred to CC-L1A-Phase-5-4-Baseline-Measurement).
    """
    if not dry_run:
        raise NotImplementedError(
            "run_bit_identical_gate: actual subprocess execution deferred to "
            "CC-L1A-Phase-5-4-Baseline-Measurement. "
            "Use --dry-run to print subprocess invocation patterns. "
            "See LL-Vision-Fusion-Phase1-Baseline.md §4.4 + §8."
        )

    print(f"# === Dry-run: bit-identical-gate ({len(skills)} skills) ===", flush=True)
    print(f"# Output: {output_dir}/bit_identical_gate/", flush=True)
    print(f"# Checkpoint root: {checkpoint_root}", flush=True)
    print(f"# Device: {device}", flush=True)
    print("", flush=True)

    for skill in skills:
        z1_ckpt = checkpoint_root / CHECKPOINT_PATHS_45D[skill].split("/", 1)[1]
        z2_ckpt = checkpoint_root / CHECKPOINT_PATHS_50D[skill].split("/", 1)[1]

        print(f"# --- {skill} ---", flush=True)
        print("# Step 1: migrate Z1 → Z2", flush=True)
        _print_migration_invocation_pattern(skill, z1_ckpt, z2_ckpt)
        print("", flush=True)

        for variant, ckpt in (("z1", z1_ckpt), ("z2", z2_ckpt)):
            cell_out = output_dir / "bit_identical_gate" / skill / "0" / f"Z{variant[1]}"
            print(f"# Step 2: eval Variant {variant.upper()} (5 ep × seed 0)", flush=True)
            _print_eval_skill_invocation_pattern(
                skill=skill,
                eval_mode="det",
                seed=0,
                num_eps=5,
                variant=variant,
                checkpoint=ckpt,
                output_dir=cell_out,
                device=device,
                no_vision_flag_name=no_vision_flag_name,
            )
            print("", flush=True)

    return {}


# ---------------------------------------------------------------------------
# Mode 2: main baseline measurement (dry-run only; design memo §6.1 + §7.1)
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
    """Main baseline measurement orchestration (dry-run only in this module).

    In dry-run mode, prints the per-cell subprocess invocation patterns
    (skills × modes × seeds × clips) and returns an empty list. Wall-budget
    estimate (per design memo §6.1): ~12-15h GPU on cuda:2 sequential
    per-skill stratified order (AC → IC → AR → Grip-CLAMP → CLAMP-R).

    Returns:
        empty list in dry-run mode.

    Raises:
        NotImplementedError: when dry_run=False.
    """
    if not dry_run:
        raise NotImplementedError(
            "run_main_baseline: actual subprocess execution deferred to "
            "CC-L1A-Phase-5-4-Baseline-Measurement. "
            "Use --dry-run to print subprocess invocation patterns. "
            "See LL-Vision-Fusion-Phase1-Baseline.md §6.1 + §7.1."
        )

    total_cells = len(skills) * len(eval_modes) * len(seeds)
    print(
        f"# === Dry-run: main baseline measurement (variant={variant}, "
        f"{total_cells} cells) ===",
        flush=True,
    )
    print(f"# Output: {output_dir}/main/", flush=True)
    print(f"# Wall budget: ~12-15h GPU (cuda:2 sequential, design memo §6.1)", flush=True)
    print("", flush=True)

    ckpt_table = CHECKPOINT_PATHS_50D if variant == "z2" else CHECKPOINT_PATHS_45D

    for skill in skills:
        ckpt = checkpoint_root / ckpt_table[skill].split("/", 1)[1]
        print(f"# --- skill={skill} (ckpt={ckpt}) ---", flush=True)
        for eval_mode in eval_modes:
            for seed in seeds:
                cell_out = output_dir / "main" / skill / eval_mode / str(seed)
                _print_eval_skill_invocation_pattern(
                    skill=skill,
                    eval_mode=eval_mode,
                    seed=seed,
                    num_eps=num_eps_per_seed,
                    variant=variant,
                    checkpoint=ckpt,
                    output_dir=cell_out,
                    device=device,
                    no_vision_flag_name=no_vision_flag_name,
                )
                print("", flush=True)

    return []


# ---------------------------------------------------------------------------
# Mode 3: aggregation (actual env-independent logic; design memo §4.2 + §7.3)
# ---------------------------------------------------------------------------


def _validate_per_eval_schema(metrics: dict, source_path: Path) -> None:
    """Validate that a parsed RUN_METRICS.json dict has all required keys."""
    missing = [k for k in PER_EVAL_REQUIRED_KEYS if k not in metrics]
    if missing:
        raise ValueError(
            f"RUN_METRICS.json at {source_path} missing keys: {missing}. "
            f"Expected schema: {PER_EVAL_REQUIRED_KEYS}"
        )

    if metrics["phase"] != "phase1_baseline":
        raise ValueError(
            f"RUN_METRICS.json at {source_path} has phase='{metrics['phase']}'; "
            f"expected 'phase1_baseline'."
        )

    per_clip_sr = metrics["per_clip_sr"]
    if not isinstance(per_clip_sr, list) or len(per_clip_sr) != DEFAULT_NUM_CLIPS:
        raise ValueError(
            f"RUN_METRICS.json at {source_path} per_clip_sr must be length-"
            f"{DEFAULT_NUM_CLIPS} list; got {per_clip_sr!r}"
        )


def _load_per_eval_metrics(metrics_path: Path) -> PerEvalRunMetrics:
    """Load and parse a per-cell RUN_METRICS.json into a PerEvalRunMetrics."""
    with metrics_path.open("r") as fh:
        data = json.load(fh)

    _validate_per_eval_schema(data, metrics_path)

    return PerEvalRunMetrics(
        phase=data["phase"],
        variant=data["variant"],
        skill=data["skill"],
        mode=data["mode"],
        seed=int(data["seed"]),
        num_eps=int(data["num_eps"]),
        successes=int(data["successes"]),
        sr=float(data["sr"]),
        per_clip_sr=[float(x) for x in data["per_clip_sr"]],
        wall_clock_sec=float(data["wall_clock_sec"]),
        checkpoint=str(data["checkpoint"]),
    )


def _bootstrap_ci(
    successes_per_seed: list[int],
    num_eps_per_seed: int,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    ci_level: float = BOOTSTRAP_CI_LEVEL,
    rng_seed: int = BOOTSTRAP_RNG_SEED,
) -> tuple[float, float, float]:
    """Bootstrap CI (default 95%) over per-seed binary outcomes.

    Per design memo §4.2 pseudocode: concatenate per-seed binary outcomes
    into a single population, then resample with replacement and take
    quantiles. Uses ``numpy.random.default_rng(seed)`` for determinism
    (matches Master Verdict Aggregator v2 convention).

    Args:
        successes_per_seed: list of integer success counts (length n_seeds).
        num_eps_per_seed: episodes per seed (default 10).
        n_resamples: bootstrap resample count.
        ci_level: CI level (default 0.95).
        rng_seed: deterministic RNG seed for reproducibility.

    Returns:
        Tuple of (sr_mean, ci_lower, ci_upper) all in [0, 1].
    """
    import numpy as np

    if not successes_per_seed:
        return (0.0, 0.0, 0.0)

    # Build flattened binary outcomes: 1 for success, 0 for failure, per ep.
    outcomes: list[int] = []
    for s in successes_per_seed:
        outcomes.extend([1] * int(s))
        outcomes.extend([0] * (num_eps_per_seed - int(s)))

    if not outcomes:
        return (0.0, 0.0, 0.0)

    arr = np.array(outcomes, dtype=np.int64)
    rng = np.random.default_rng(rng_seed)

    n = arr.shape[0]
    resampled_means = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        resampled_means[i] = arr[idx].mean()

    alpha = 1.0 - ci_level
    lower_q = (alpha / 2.0) * 100.0
    upper_q = (1.0 - alpha / 2.0) * 100.0

    sr_mean = float(np.mean(resampled_means))
    ci_lower = float(np.percentile(resampled_means, lower_q))
    ci_upper = float(np.percentile(resampled_means, upper_q))

    return (sr_mean, ci_lower, ci_upper)


def _per_seed_variance_pp_squared(sr_per_seed: list[float]) -> float:
    """Compute per-seed SR variance in pp² (CC4 v3.2 §H reproducibility convention)."""
    if len(sr_per_seed) < 2:
        return 0.0
    sr_pp = [s * 100.0 for s in sr_per_seed]
    return float(statistics.variance(sr_pp))


def _aggregate_per_skill(
    per_eval_metrics: list[PerEvalRunMetrics],
    skill: str,
    mode: str,
    variant: str,
    n_eps_per_seed: int,
    n_resamples: int,
    ci_level: float,
) -> PerSkillAggregate:
    """Aggregate per-eval metrics into per-skill bootstrap CI 95% summary."""
    cell = [
        m for m in per_eval_metrics
        if m.skill == skill and m.mode == mode and m.variant == variant
    ]
    if not cell:
        return PerSkillAggregate(
            skill=skill,
            mode=mode,
            variant=variant,
            n_seeds=0,
            n_eps_per_seed=n_eps_per_seed,
            n_total_eps=0,
            sr_mean=0.0,
            sr_ci_lower_95=0.0,
            sr_ci_upper_95=0.0,
            sr_per_seed=[],
            seed_variance=0.0,
            seed_fragile=False,
        )

    cell_sorted = sorted(cell, key=lambda m: m.seed)
    successes_per_seed = [m.successes for m in cell_sorted]
    sr_per_seed = [m.sr for m in cell_sorted]

    sr_mean, ci_lower, ci_upper = _bootstrap_ci(
        successes_per_seed=successes_per_seed,
        num_eps_per_seed=n_eps_per_seed,
        n_resamples=n_resamples,
        ci_level=ci_level,
    )
    seed_variance = _per_seed_variance_pp_squared(sr_per_seed)
    seed_fragile = seed_variance > SEED_FRAGILE_THRESHOLD_PP_SQUARED

    return PerSkillAggregate(
        skill=skill,
        mode=mode,
        variant=variant,
        n_seeds=len(cell_sorted),
        n_eps_per_seed=n_eps_per_seed,
        n_total_eps=len(cell_sorted) * n_eps_per_seed,
        sr_mean=sr_mean,
        sr_ci_lower_95=ci_lower,
        sr_ci_upper_95=ci_upper,
        sr_per_seed=sr_per_seed,
        seed_variance=seed_variance,
        seed_fragile=seed_fragile,
    )


def _compute_per_clip_distribution(
    per_eval_metrics: list[PerEvalRunMetrics],
    skill: str,
    mode: str,
    variant: str,
) -> PerClipDistribution:
    """Per-clip-index SR distribution (design memo §4.3).

    Aggregates per-eval ``per_clip_sr`` lists across seeds into per-clip
    mean + per-clip CI 95% (using normal approx over per-seed values) +
    clip uniformity index = std(per_clip_mean) / mean(per_clip_mean).
    """
    cell = [
        m for m in per_eval_metrics
        if m.skill == skill and m.mode == mode and m.variant == variant
    ]
    if not cell:
        return PerClipDistribution(
            skill=skill,
            mode=mode,
            variant=variant,
            per_clip_sr_mean=[0.0] * DEFAULT_NUM_CLIPS,
            per_clip_sr_ci_lower_95=[0.0] * DEFAULT_NUM_CLIPS,
            per_clip_sr_ci_upper_95=[0.0] * DEFAULT_NUM_CLIPS,
            clip_uniformity=0.0,
        )

    n_clips = len(cell[0].per_clip_sr)
    per_clip_mean: list[float] = []
    per_clip_ci_lower: list[float] = []
    per_clip_ci_upper: list[float] = []

    for clip_idx in range(n_clips):
        seed_values = [m.per_clip_sr[clip_idx] for m in cell]
        mean_val = sum(seed_values) / len(seed_values)
        per_clip_mean.append(mean_val)

        # Normal-approx CI (sufficient for clip-level reporting; bootstrap is
        # used at the per-skill aggregate level per design memo §4.2 step 1).
        if len(seed_values) >= 2:
            std_val = statistics.stdev(seed_values)
            half_width = 1.96 * std_val / math.sqrt(len(seed_values))
        else:
            half_width = 0.0
        per_clip_ci_lower.append(max(0.0, mean_val - half_width))
        per_clip_ci_upper.append(min(1.0, mean_val + half_width))

    grand_mean = sum(per_clip_mean) / len(per_clip_mean) if per_clip_mean else 0.0
    if grand_mean > 0.0 and len(per_clip_mean) >= 2:
        clip_std = statistics.stdev(per_clip_mean)
        clip_uniformity = float(clip_std / grand_mean)
    else:
        clip_uniformity = 0.0

    return PerClipDistribution(
        skill=skill,
        mode=mode,
        variant=variant,
        per_clip_sr_mean=per_clip_mean,
        per_clip_sr_ci_lower_95=per_clip_ci_lower,
        per_clip_sr_ci_upper_95=per_clip_ci_upper,
        clip_uniformity=clip_uniformity,
    )


def _discover_per_eval_metrics_files(main_root: Path) -> list[Path]:
    """Recursively find RUN_METRICS.json files under ``<output_dir>/main/``."""
    if not main_root.exists():
        return []
    return sorted(main_root.rglob("RUN_METRICS.json"))


def _discover_bit_identical_metrics_files(gate_root: Path) -> list[Path]:
    """Recursively find RUN_METRICS.json files under ``<output_dir>/bit_identical_gate/``."""
    if not gate_root.exists():
        return []
    return sorted(gate_root.rglob("RUN_METRICS.json"))


def run_aggregate(
    output_dir: Path,
    bootstrap_resamples: int = BOOTSTRAP_RESAMPLES,
    bootstrap_ci_level: float = BOOTSTRAP_CI_LEVEL,
    n_eps_per_seed: int = DEFAULT_NUM_EPS_PER_SEED,
) -> CrossSkillBaselineSummary:
    """Post-execution aggregation pipeline (env-independent actual logic).

    Steps:

    1. Discover ``RUN_METRICS.json`` files under ``<output_dir>/main/``.
    2. Per-skill per-mode aggregation: bootstrap CI 95% (resample 1000).
    3. Per-clip-index distribution + uniformity.
    4. Bit-identical gate verdict aggregation (gate_overall_verdict).
    5. Variant A starting point pinning (Z2 ckpt → Phase 3 §2 reference).
    6. Cross-skill aggregation: write ``baseline_summary.json``.

    Args:
        output_dir: output root directory.
        bootstrap_resamples: bootstrap resample count.
        bootstrap_ci_level: CI level (default 0.95).
        n_eps_per_seed: episodes per seed (used for variance computation when
            successes_per_seed is the only available signal).

    Returns:
        CrossSkillBaselineSummary written to
        ``<output_dir>/aggregate/baseline_summary.json``.
    """
    main_root = output_dir / "main"
    aggregate_root = output_dir / "aggregate"
    aggregate_root.mkdir(parents=True, exist_ok=True)

    metrics_files = _discover_per_eval_metrics_files(main_root)
    per_eval_metrics: list[PerEvalRunMetrics] = []
    total_wall_clock = 0.0

    for path in metrics_files:
        try:
            metric = _load_per_eval_metrics(path)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"WARN: skipping {path}: {e}", file=sys.stderr)
            continue
        per_eval_metrics.append(metric)
        total_wall_clock += metric.wall_clock_sec

    discovered_skills = sorted({m.skill for m in per_eval_metrics})
    discovered_modes = sorted({m.mode for m in per_eval_metrics})
    discovered_variants = sorted({m.variant for m in per_eval_metrics})

    per_skill_aggregates: dict = {}
    per_skill_clip_distributions: dict = {}
    variant_a_starting_point: dict = {}

    for skill in discovered_skills:
        per_skill_aggregates[skill] = {}
        per_skill_clip_distributions[skill] = {}

        for mode in discovered_modes:
            for variant in discovered_variants:
                cell_metrics = [
                    m for m in per_eval_metrics
                    if m.skill == skill and m.mode == mode and m.variant == variant
                ]
                if not cell_metrics:
                    continue

                agg = _aggregate_per_skill(
                    per_eval_metrics=per_eval_metrics,
                    skill=skill,
                    mode=mode,
                    variant=variant,
                    n_eps_per_seed=n_eps_per_seed,
                    n_resamples=bootstrap_resamples,
                    ci_level=bootstrap_ci_level,
                )
                per_skill_aggregates[skill][f"{mode}_{variant}"] = asdict(agg)

                dist = _compute_per_clip_distribution(
                    per_eval_metrics=per_eval_metrics,
                    skill=skill,
                    mode=mode,
                    variant=variant,
                )
                per_skill_clip_distributions[skill][f"{mode}_{variant}"] = asdict(dist)

                if variant == "z2":
                    variant_a_starting_point[skill] = cell_metrics[0].checkpoint

    bit_identical_verdicts = _aggregate_bit_identical_from_files(output_dir / "bit_identical_gate")
    gate_overall_verdict = _aggregate_bit_identical_verdicts(bit_identical_verdicts)

    summary = CrossSkillBaselineSummary(
        per_skill_aggregates=per_skill_aggregates,
        per_skill_clip_distributions=per_skill_clip_distributions,
        bit_identical_gate_verdicts={k: asdict(v) for k, v in bit_identical_verdicts.items()},
        gate_overall_verdict=gate_overall_verdict,
        variant_a_starting_point=variant_a_starting_point,
        wall_clock_total_sec=total_wall_clock,
        run_id=time.strftime("%Y%m%d_%H%M%S"),
    )

    summary_path = aggregate_root / "baseline_summary.json"
    with summary_path.open("w") as fh:
        json.dump(asdict(summary), fh, indent=2, sort_keys=True)

    per_skill_path = aggregate_root / "per_skill_summary.json"
    with per_skill_path.open("w") as fh:
        json.dump(per_skill_aggregates, fh, indent=2, sort_keys=True)

    per_clip_path = aggregate_root / "per_clip_distribution.json"
    with per_clip_path.open("w") as fh:
        json.dump(per_skill_clip_distributions, fh, indent=2, sort_keys=True)

    verdict_path = aggregate_root / "bit_identical_gate_verdict.json"
    with verdict_path.open("w") as fh:
        json.dump(
            {
                "per_skill": {k: asdict(v) for k, v in bit_identical_verdicts.items()},
                "overall": gate_overall_verdict,
            },
            fh,
            indent=2,
            sort_keys=True,
        )

    return summary


def _aggregate_bit_identical_from_files(
    gate_root: Path,
) -> dict[str, BitIdenticalGateVerdict]:
    """Discover bit-identical-gate RUN_METRICS.json files and compute per-skill verdicts.

    Expects layout: ``<gate_root>/<skill>/<seed>/Z<1|2>/RUN_METRICS.json``.
    Computes per-skill SR for Z1 and Z2 (mean over discovered seeds, but in
    practice only seed 0 is run in the smoke gate per design memo §8) and
    invokes :func:`_decide_bit_identical_verdict` per skill.
    """
    if not gate_root.exists():
        return {}

    metrics_files = _discover_bit_identical_metrics_files(gate_root)
    by_skill_variant: dict[tuple[str, str], list[float]] = {}

    for path in metrics_files:
        try:
            with path.open("r") as fh:
                data = json.load(fh)
        except json.JSONDecodeError:
            continue

        skill = data.get("skill")
        variant = data.get("variant")
        sr = data.get("sr")
        if skill is None or variant is None or sr is None:
            continue

        by_skill_variant.setdefault((skill, variant), []).append(float(sr))

    skills_seen = {k[0] for k in by_skill_variant}
    verdicts: dict[str, BitIdenticalGateVerdict] = {}

    for skill in sorted(skills_seen):
        z1_values = by_skill_variant.get((skill, "z1"), [])
        z2_values = by_skill_variant.get((skill, "z2"), [])
        if not z1_values or not z2_values:
            continue
        z1_sr = sum(z1_values) / len(z1_values)
        z2_sr = sum(z2_values) / len(z2_values)
        verdicts[skill] = _decide_bit_identical_verdict(z1_sr, z2_sr, skill)

    return verdicts


# ---------------------------------------------------------------------------
# Phase 2/3 export (actual JSON serialization; design memo §5.2 + §5.3 + §10)
# ---------------------------------------------------------------------------


def export_phase2_ablation_c1_supply(
    summary: CrossSkillBaselineSummary,
    output_path: Path,
) -> None:
    """Export Phase 2 §8 5-skill ablation matrix C-1 cell baseline supply.

    Output schema (design memo §5.2 + §10.1):

        {
            "phase": "phase1_baseline",
            "schema_version": "phase2_c1_supply_v1",
            "<skill> C-1 SR": <det aggregated SR>,
            ...
            "_meta": {
                "gate_overall_verdict": "PASS" | "WARN" | "FAIL" | "PENDING",
                "run_id": "<run_id>",
                "n_skills": <count>,
                "source": "fusion_phase1_integration"
            }
        }

    Empty det aggregates yield ``null`` for that skill (forward-compatible
    with OQ-B2 CLAMP-R inclusion uncertainty).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict = {
        "phase": "phase1_baseline",
        "schema_version": "phase2_c1_supply_v1",
    }

    n_skills_with_data = 0
    for skill, mode_variant_dict in summary.per_skill_aggregates.items():
        det_z2 = mode_variant_dict.get("det_z2")
        if det_z2 is not None:
            payload[f"{skill} C-1 SR"] = det_z2.get("sr_mean")
            n_skills_with_data += 1
        else:
            payload[f"{skill} C-1 SR"] = None

    payload["_meta"] = {
        "gate_overall_verdict": summary.gate_overall_verdict,
        "run_id": summary.run_id,
        "n_skills": n_skills_with_data,
        "source": "fusion_phase1_integration",
    }

    with output_path.open("w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)


def export_phase3_variant_a_starting_point(
    summary: CrossSkillBaselineSummary,
    output_path: Path,
) -> None:
    """Export Phase 3 §2 Variant A baseline starting point pin (design memo §5.3 + §10.2).

    Variant A = Z2 by construction (pure concat passthrough = 50D zero-init
    bit-identical baseline). Output schema:

        {
            "phase": "phase1_baseline",
            "schema_version": "phase3_variant_a_v1",
            "<skill>": {
                "ckpt": "<Z2 ckpt path>",
                "sr_det": <det aggregated SR>,
                "sr_stoch": <stoch aggregated SR>,
                "sr_ci_det_95": [<lower>, <upper>],
                "sr_ci_stoch_95": [<lower>, <upper>],
            },
            ...
            "_meta": {
                "gate_overall_verdict": "...",
                "run_id": "...",
                "source": "fusion_phase1_integration"
            }
        }
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict = {
        "phase": "phase1_baseline",
        "schema_version": "phase3_variant_a_v1",
    }

    for skill, mode_variant_dict in summary.per_skill_aggregates.items():
        ckpt = summary.variant_a_starting_point.get(skill)
        det_z2 = mode_variant_dict.get("det_z2")
        stoch_z2 = mode_variant_dict.get("stoch_z2")

        entry: dict = {"ckpt": ckpt}
        if det_z2 is not None:
            entry["sr_det"] = det_z2.get("sr_mean")
            entry["sr_ci_det_95"] = [
                det_z2.get("sr_ci_lower_95"),
                det_z2.get("sr_ci_upper_95"),
            ]
        else:
            entry["sr_det"] = None
            entry["sr_ci_det_95"] = [None, None]

        if stoch_z2 is not None:
            entry["sr_stoch"] = stoch_z2.get("sr_mean")
            entry["sr_ci_stoch_95"] = [
                stoch_z2.get("sr_ci_lower_95"),
                stoch_z2.get("sr_ci_upper_95"),
            ]
        else:
            entry["sr_stoch"] = None
            entry["sr_ci_stoch_95"] = [None, None]

        payload[skill] = entry

    payload["_meta"] = {
        "gate_overall_verdict": summary.gate_overall_verdict,
        "run_id": summary.run_id,
        "source": "fusion_phase1_integration",
    }

    with output_path.open("w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI dispatch entry."""
    parser = build_argparser()
    args = parser.parse_args(argv)

    skills = [s.strip() for s in args.skills.split(",") if s.strip()]
    eval_modes = [m.strip() for m in args.eval_modes.split(",") if m.strip()]
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]

    for skill in skills:
        if skill not in SUPPORTED_SKILLS:
            print(
                f"ERROR: unsupported skill '{skill}'; "
                f"supported: {','.join(SUPPORTED_SKILLS)}",
                file=sys.stderr,
            )
            return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "bit-identical-gate":
        run_bit_identical_gate(
            skills=skills,
            output_dir=args.output_dir,
            checkpoint_root=args.checkpoint_root,
            device=args.device,
            no_vision_flag_name=args.no_vision_flag_name,
            dry_run=args.dry_run,
        )
        return 0

    if args.mode == "main":
        run_main_baseline(
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
        return 0

    if args.mode == "aggregate":
        summary = run_aggregate(
            output_dir=args.output_dir,
            bootstrap_resamples=args.bootstrap_resamples,
            bootstrap_ci_level=args.bootstrap_ci_level,
            n_eps_per_seed=args.num_eps_per_seed,
        )
        aggregate_root = args.output_dir / "aggregate"
        export_phase2_ablation_c1_supply(
            summary=summary,
            output_path=aggregate_root / "phase2_c1_supply.json",
        )
        export_phase3_variant_a_starting_point(
            summary=summary,
            output_path=aggregate_root / "phase3_variant_a_starting_point.json",
        )
        print(
            f"# aggregate complete: {len(summary.per_skill_aggregates)} skills, "
            f"gate_overall_verdict={summary.gate_overall_verdict}, "
            f"run_id={summary.run_id}",
            flush=True,
        )
        return 0

    print(f"ERROR: unknown mode '{args.mode}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
