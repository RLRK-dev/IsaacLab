#!/usr/bin/env python3
"""SOMA Phase C: Obs space ablation analysis (18D/22D/24D).

Analyzes existing h5 data to compare observation modes:
- 18D: joint_pos(14) + cable_midpoint(3) + tension(1)
- 22D: + ee_pos_error(2) + force_derivative(2)
- 24D: + grip_effort(2)

Metrics per mode:
- Per-dim statistics (mean, std, min, max, p5, p95)
- Correlation matrix (effective rank via singular values)
- SNR estimate (inter-phase variance / intra-phase variance)
- Per-phase variance structure

Usage:
    python thread_isaac_lab/scripts/analyze_obs_ablation.py \
        --h5 data/heuristic_logs/obs24d_stats.h5
"""

import argparse
import os
import sys

import h5py
import numpy as np

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from thread_isaac_lab.configs.task_config import OBS_MODES, OBS_NORMALIZATION, OBS_SPEC


def load_h5(path: str):
    """Load obs data from h5 file."""
    with h5py.File(path, "r") as f:
        obs = f["obs"][:]  # (N, 24)
        phase = f["phase"][:] if "phase" in f else None
        step = f["step"][:] if "step" in f else None
        episode = f["episode"][:] if "episode" in f else None
    return obs, phase, step, episode


def dim_names(end: int):
    """Get dimension names for first `end` dims."""
    names = []
    for name, spec in OBS_SPEC.items():
        if spec["start"] < end:
            dim = min(spec["end"], end) - spec["start"]
            if dim == 1:
                names.append(name)
            else:
                for i in range(dim):
                    names.append(f"{name}[{i}]")
    return names


def effective_rank(cov: np.ndarray) -> float:
    """Effective rank from eigenvalues of covariance matrix (Roy & Vetterli 2007)."""
    eigvals = np.linalg.eigvalsh(cov)
    eigvals = eigvals[eigvals > 1e-12]
    if len(eigvals) == 0:
        return 0.0
    p = eigvals / eigvals.sum()
    entropy = -np.sum(p * np.log(p))
    return np.exp(entropy)


def snr_per_dim(obs: np.ndarray, phase: np.ndarray) -> np.ndarray:
    """SNR = inter-phase variance / intra-phase variance per dim."""
    unique_phases = np.unique(phase)
    D = obs.shape[1]
    grand_mean = obs.mean(axis=0)
    inter_var = np.zeros(D)
    intra_var = np.zeros(D)
    total_n = 0
    for ph in unique_phases:
        mask = phase == ph
        n = mask.sum()
        if n < 2:
            continue
        group = obs[mask]
        group_mean = group.mean(axis=0)
        inter_var += n * (group_mean - grand_mean) ** 2
        intra_var += group.var(axis=0, ddof=1) * (n - 1)
        total_n += n
    # Avoid div by zero
    intra_var = np.maximum(intra_var, 1e-12)
    return inter_var / intra_var


def analyze_mode(obs_full: np.ndarray, phase: np.ndarray, mode: str):
    """Run full analysis for one obs mode."""
    cfg = OBS_MODES[mode]
    end = cfg["end"]
    obs = obs_full[:, :end]
    N, D = obs.shape
    names = dim_names(end)

    result = {"mode": mode, "dim": D, "N": N}

    # Per-dim statistics
    stats = {}
    for i in range(D):
        col = obs[:, i]
        stats[names[i]] = {
            "mean": float(np.mean(col)),
            "std": float(np.std(col)),
            "min": float(np.min(col)),
            "max": float(np.max(col)),
            "p5": float(np.percentile(col, 5)),
            "p95": float(np.percentile(col, 95)),
        }
    result["dim_stats"] = stats

    # Correlation matrix & effective rank
    cov = np.cov(obs.T)
    corr = np.corrcoef(obs.T)
    result["effective_rank"] = float(effective_rank(cov))
    result["corr_matrix"] = corr.tolist()

    # SNR
    if phase is not None:
        snr = snr_per_dim(obs, phase)
        result["snr_per_dim"] = {names[i]: float(snr[i]) for i in range(D)}
        result["snr_mean"] = float(snr.mean())
    else:
        result["snr_per_dim"] = {}
        result["snr_mean"] = 0.0

    # Overall std mean
    stds = np.array([stats[n]["std"] for n in names])
    result["obs_std_mean"] = float(stds.mean())

    # Normalized obs stats (apply scale/offset)
    scale = np.array(OBS_NORMALIZATION["scale"][:end])
    offset = np.array(OBS_NORMALIZATION["offset"][:end])
    obs_norm = obs * scale + offset
    norm_stds = obs_norm.std(axis=0)
    result["norm_std_mean"] = float(norm_stds.mean())

    # Per-phase variance structure
    if phase is not None:
        phase_var = {}
        for ph in np.unique(phase):
            mask = phase == ph
            if mask.sum() < 2:
                continue
            pv = obs[mask].var(axis=0)
            phase_var[f"phase_{ph:.2f}"] = float(pv.mean())
        result["phase_variance"] = phase_var

    return result


def print_comparison(results: list):
    """Print comparison table."""
    print("\n" + "=" * 80)
    print("SOMA Phase C: Observation Space Ablation Results")
    print("=" * 80)

    # Summary table
    header = f"{'Mode':<6} {'Dim':>4} {'EffRank':>8} {'SNR_mean':>9} {'std_mean':>9} {'norm_std':>9}"
    print(f"\n{header}")
    print("-" * len(header))
    for r in results:
        print(
            f"{r['mode']:<6} {r['dim']:>4} "
            f"{r['effective_rank']:>8.2f} "
            f"{r['snr_mean']:>9.3f} "
            f"{r['obs_std_mean']:>9.4f} "
            f"{r['norm_std_mean']:>9.4f}"
        )

    # Marginal value of added dims
    print("\n--- Marginal contribution of added dimensions ---")
    for i in range(1, len(results)):
        prev = results[i - 1]
        curr = results[i]
        added = curr["dim"] - prev["dim"]
        rank_delta = curr["effective_rank"] - prev["effective_rank"]
        snr_delta = curr["snr_mean"] - prev["snr_mean"]
        print(
            f"  {prev['mode']} → {curr['mode']}: "
            f"+{added} dims, "
            f"EffRank Δ={rank_delta:+.2f}, "
            f"SNR Δ={snr_delta:+.3f}"
        )

    # Per-dim SNR (for 24D — show all)
    r24 = [r for r in results if r["mode"] == "24d"][0]
    if r24["snr_per_dim"]:
        print("\n--- Per-dim SNR (24D, sorted descending) ---")
        snr_items = sorted(r24["snr_per_dim"].items(), key=lambda x: -x[1])
        for name, snr_val in snr_items:
            bar = "#" * min(int(snr_val * 2), 50)
            print(f"  {name:<28s} SNR={snr_val:>8.3f} {bar}")

    # Phase variance (24D)
    if "phase_variance" in r24:
        print("\n--- Per-phase mean variance (24D) ---")
        for phase, var in sorted(r24["phase_variance"].items()):
            print(f"  {phase}: {var:.6f}")


def main():
    parser = argparse.ArgumentParser(description="SOMA Phase C obs ablation analysis")
    parser.add_argument(
        "--h5",
        default="data/heuristic_logs/obs24d_stats.h5",
        help="Path to h5 file with obs data",
    )
    parser.add_argument(
        "--save_json",
        default="data/heuristic_logs/obs_ablation_results.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    if not os.path.exists(args.h5):
        print(f"ERROR: h5 file not found: {args.h5}")
        sys.exit(1)

    obs_full, phase, step, episode = load_h5(args.h5)
    print(f"Loaded {obs_full.shape[0]} samples × {obs_full.shape[1]}D from {args.h5}")
    if phase is not None:
        unique_phases = np.unique(phase)
        print(f"Phases: {unique_phases}")

    results = []
    for mode in ["18d", "22d", "24d"]:
        r = analyze_mode(obs_full, phase, mode)
        results.append(r)

    print_comparison(results)

    # Save JSON
    import json
    os.makedirs(os.path.dirname(args.save_json), exist_ok=True)
    with open(args.save_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {args.save_json}")


if __name__ == "__main__":
    main()
