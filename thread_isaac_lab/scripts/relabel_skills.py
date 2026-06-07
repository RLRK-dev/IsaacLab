#!/usr/bin/env python3
"""
Skill C/D success segment labeling for THREAD project.
Re-labels existing demo data to extract valid training segments.
"""

import argparse
import json
import h5py
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from thread_isaac_lab.configs.task_config import HOOK_X, HOOK_Y, HOOK_Z

# ============================================================
# Constants - SSOT: task_config.py (H211: import from SSOT)
# ============================================================
HOOK_POS = np.array([HOOK_X, HOOK_Y, HOOK_Z])
# HOOK_X is already imported from task_config.py

# Configuration (B0 curriculum / B2 production)
CFG = {
    # Skill C: Move near hook
    "C_thresh": 0.05,        # curriculum: 0.05, production: 0.03
    "C_k": 10,               # consecutive steps required
    "C_std_k": 10,           # rolling std window
    "C_std_thresh": 0.01,    # stability threshold (m)

    # Skill D: Hook placement
    "D_eps_x": 0.002,        # crossing hysteresis (2mm)
    "D_pre_dist": 0.06,      # crossing valid if dist < this (6cm)
    "D_dwell_thresh": 0.03,  # curriculum: 0.03, production: 0.02
    "D_dwell_steps": 15,
    "D_retain_steps": 30,
    "D_inside_margin": 0.0,  # seg must be past hook_x by this margin

    # Valid data gate
    "force_min": 1.0,        # grip loss threshold (N)
    "force_max": 100.0,      # force spike threshold (N)
    "ee_vel_max": 0.2,       # EE velocity limit (m/s)
}

# ============================================================
# Helper functions
# ============================================================
def extract_segments(task_state: np.ndarray) -> np.ndarray:
    """Extract 10 cable segments (3D positions) from task_state[0:30]."""
    return task_state[0:30].reshape(10, 3)


def seg5_hook_dist(task_state: np.ndarray) -> float:
    """Get cable_hook_dist from task_state[39] (seg5 to hook)."""
    return float(task_state[39])


def target_hook_dist(segments: np.ndarray, mode: str = "seg5_neighbors") -> float:
    """
    Compute distance from target cable segment to hook.
    mode='seg5_neighbors': min of seg4, seg5, seg6 (recommended)
    mode='min_all': min of all segments
    """
    if mode == "seg5_neighbors":
        idxs = [4, 5, 6]
        dists = np.linalg.norm(segments[idxs] - HOOK_POS, axis=1)
        return float(np.min(dists))
    else:
        dists = np.linalg.norm(segments - HOOK_POS, axis=1)
        return float(np.min(dists))


def rolling_std(x: np.ndarray, k: int) -> np.ndarray:
    """Compute rolling standard deviation with window k."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float32)
    for t in range(k - 1, n):
        out[t] = np.std(x[t - k + 1 : t + 1])
    return out


def find_intervals(mask: np.ndarray, min_len: int) -> List[Tuple[int, int]]:
    """Find contiguous True intervals of at least min_len."""
    n = len(mask)
    intervals = []
    i = 0
    while i < n:
        if mask[i]:
            start = i
            while i < n and mask[i]:
                i += 1
            end = i
            if end - start >= min_len:
                intervals.append((start, end))
        else:
            i += 1
    return intervals


# ============================================================
# Valid data gate
# ============================================================
def compute_valid_mask(obs_list: List[Dict], cfg: Dict = CFG) -> Tuple[np.ndarray, List[str]]:
    """
    Compute validity mask based on SSOT valid_data_gate.
    Returns: (valid_mask, fail_reasons per step)
    """
    n = len(obs_list)
    valid = np.ones(n, dtype=bool)
    fail_reasons = ["" for _ in range(n)]

    for t, obs in enumerate(obs_list):
        ts = obs.get("task_state")
        if ts is None:
            valid[t] = False
            fail_reasons[t] = "no_task_state"
            continue

        # no_nan
        if not np.isfinite(ts).all():
            valid[t] = False
            fail_reasons[t] = "nan_in_task_state"
            continue

        # no_grip_loss: force_L > 1N AND force_R > 1N
        force_l = obs.get("force_L", obs.get("force_l", None))
        force_r = obs.get("force_R", obs.get("force_r", None))
        if force_l is not None and force_r is not None:
            if not (force_l > cfg["force_min"] and force_r > cfg["force_min"]):
                valid[t] = False
                fail_reasons[t] = f"grip_loss:L={force_l:.1f},R={force_r:.1f}"
                continue

        # no_force_spike: force < 100N
        if force_l is not None and force_r is not None:
            if not (force_l < cfg["force_max"] and force_r < cfg["force_max"]):
                valid[t] = False
                fail_reasons[t] = f"force_spike:L={force_l:.1f},R={force_r:.1f}"
                continue

        # ee_velocity_stable (if available)
        v_ee = obs.get("v_ee", obs.get("ee_vel", None))
        if v_ee is not None:
            v_norm = np.linalg.norm(np.array(v_ee))
            if v_norm >= cfg["ee_vel_max"]:
                valid[t] = False
                fail_reasons[t] = f"ee_vel_high:{v_norm:.3f}"
                continue

    return valid, fail_reasons


# ============================================================
# Skill C labeling
# ============================================================
def label_skill_c(obs_list: List[Dict], cfg: Dict = CFG) -> Dict[str, Any]:
    """
    Label Skill C (Move near hook) success intervals.
    Returns dict with intervals and diagnostics.
    """
    n = len(obs_list)
    valid, fail_reasons = compute_valid_mask(obs_list, cfg)

    # Compute distances
    dist = np.zeros(n, dtype=np.float32)
    for t, obs in enumerate(obs_list):
        ts = obs.get("task_state")
        if ts is not None and len(ts) >= 30:
            segs = extract_segments(ts)
            dist[t] = target_hook_dist(segs, mode="seg5_neighbors")
        else:
            dist[t] = np.inf

    # Rolling std for stability
    dist_std = rolling_std(dist, cfg["C_std_k"])

    # Success mask: dist < thresh AND std < thresh AND valid
    success_mask = (
        (dist < cfg["C_thresh"])
        & np.isfinite(dist_std)
        & (dist_std < cfg["C_std_thresh"])
        & valid
    )

    intervals = find_intervals(success_mask, cfg["C_k"])

    return {
        "intervals": intervals,
        "total_success_steps": sum(e - s for s, e in intervals),
        "diagnostics": {
            "min_dist": float(np.min(dist)) if n > 0 else None,
            "valid_rate": float(np.mean(valid)),
            "dist_below_thresh_rate": float(np.mean(dist < cfg["C_thresh"])),
        },
    }


# ============================================================
# Skill D labeling
# ============================================================
def label_skill_d(obs_list: List[Dict], cfg: Dict = CFG) -> Dict[str, Any]:
    """
    Label Skill D (Hook placement) success intervals.
    Returns dict with intervals and diagnostics.
    """
    n = len(obs_list)
    if n < 2:
        return {"intervals": [], "total_success_steps": 0, "diagnostics": {}}

    valid, fail_reasons = compute_valid_mask(obs_list, cfg)

    # Precompute arrays
    seg_x = np.zeros((n, 10), dtype=np.float32)
    dist_target = np.zeros(n, dtype=np.float32)

    for t, obs in enumerate(obs_list):
        ts = obs.get("task_state")
        if ts is not None and len(ts) >= 40:
            segs = extract_segments(ts)
            seg_x[t] = segs[:, 0]
            dist_target[t] = seg5_hook_dist(ts)
        else:
            seg_x[t] = np.inf
            dist_target[t] = np.inf

    seg5_x = seg_x[:, 5]
    intervals = []
    crossing_events = []

    t = 1
    while t < n:
        # Crossing detection with hysteresis (seg5 only for precision)
        prev_dx = seg5_x[t - 1] - HOOK_X
        curr_dx = seg5_x[t] - HOOK_X
        crossed = (prev_dx > cfg["D_eps_x"]) and (curr_dx < -cfg["D_eps_x"])

        # Additional: must be near hook and valid
        near_hook = dist_target[t] < cfg["D_pre_dist"]
        crossed = crossed and near_hook and valid[t - 1] and valid[t]

        if not crossed:
            t += 1
            continue

        cross_time = t
        crossing_events.append(cross_time)

        # Dwell: check dwell_steps after crossing
        end_dwell = cross_time + cfg["D_dwell_steps"]
        if end_dwell >= n:
            break

        dwell_window = np.arange(cross_time, end_dwell)

        dwell_ok = (
            np.all(dist_target[dwell_window] < cfg["D_dwell_thresh"])
            and np.all(seg5_x[dwell_window] < (HOOK_X - cfg["D_inside_margin"]))
            and np.all(valid[dwell_window])
        )

        if not dwell_ok:
            t += 1
            continue

        # Retention: check retain_steps after dwell
        end_retain = end_dwell + cfg["D_retain_steps"]
        if end_retain >= n:
            break

        retain_window = np.arange(end_dwell, end_retain)

        retain_ok = (
            np.all(dist_target[retain_window] < cfg["D_dwell_thresh"])
            and np.all(seg5_x[retain_window] < (HOOK_X - cfg["D_inside_margin"]))
            and np.all(valid[retain_window])
        )

        if retain_ok:
            intervals.append((cross_time, end_retain))
            t = end_retain  # skip to avoid duplicate detection
        else:
            t += 1

    return {
        "intervals": intervals,
        "total_success_steps": sum(e - s for s, e in intervals),
        "diagnostics": {
            "crossing_events": len(crossing_events),
            "valid_rate": float(np.mean(valid)),
            "min_dist_target": float(np.min(dist_target)) if n > 0 else None,
        },
    }


# ============================================================
# H5 file loading
# ============================================================
def load_h5_file(filepath: Path) -> List[Dict]:
    """Load H5 demo file and return list of obs dicts."""
    obs_list = []
    with h5py.File(filepath, "r") as f:
        # Adapt to your H5 structure
        n_steps = f["task_state"].shape[0] if "task_state" in f else 0
        for t in range(n_steps):
            obs = {}
            if "task_state" in f:
                obs["task_state"] = f["task_state"][t]
            if "force_L" in f:
                obs["force_L"] = float(f["force_L"][t])
            elif "force_l" in f:
                obs["force_L"] = float(f["force_l"][t])
            if "force_R" in f:
                obs["force_R"] = float(f["force_R"][t])
            elif "force_r" in f:
                obs["force_R"] = float(f["force_r"][t])
            if "ee_vel" in f:
                obs["v_ee"] = f["ee_vel"][t]
            obs_list.append(obs)
    return obs_list


# ============================================================
# Sanity check
# ============================================================
def run_sanity_check(obs_list: List[Dict]) -> Dict[str, Any]:
    """
    Sanity check: verify seg5 is correct target and crossing direction.
    """
    n = len(obs_list)
    if n == 0:
        return {"error": "empty obs_list"}

    seg5_dists = []
    min_dists = []
    seg5_x_vals = []

    for obs in obs_list:
        ts = obs.get("task_state")
        if ts is None or len(ts) < 40:
            continue
        segs = extract_segments(ts)
        seg5_dist = np.linalg.norm(segs[5] - HOOK_POS)
        min_dist = np.min(np.linalg.norm(segs - HOOK_POS, axis=1))
        seg5_dists.append(seg5_dist)
        min_dists.append(min_dist)
        seg5_x_vals.append(segs[5, 0])

    seg5_dists = np.array(seg5_dists)
    min_dists = np.array(min_dists)
    seg5_x_vals = np.array(seg5_x_vals)

    # Correlation: seg5_dist vs min_dist
    if len(seg5_dists) > 10:
        corr = np.corrcoef(seg5_dists, min_dists)[0, 1]
    else:
        corr = None

    # Check if seg5 ever crosses hook_x
    crosses_hook = np.any(seg5_x_vals < HOOK_X)

    return {
        "n_steps": len(seg5_dists),
        "seg5_min_dist_correlation": float(corr) if corr else None,
        "seg5_min_dist": float(np.min(seg5_dists)) if len(seg5_dists) > 0 else None,
        "overall_min_dist": float(np.min(min_dists)) if len(min_dists) > 0 else None,
        "seg5_ever_crosses_hook_x": bool(crosses_hook),
        "seg5_x_range": [float(np.min(seg5_x_vals)), float(np.max(seg5_x_vals))]
        if len(seg5_x_vals) > 0
        else None,
        "hook_x": HOOK_X,
    }


# ============================================================
# Main relabeling
# ============================================================
def relabel_dataset(input_dir: Path, output_path: Path, sanity_check: bool = False, recursive: bool = False):
    """Relabel all H5 files in input_dir.

    Args:
        input_dir: Directory containing H5 demo files
        output_path: Output JSON path
        sanity_check: Run sanity check on each file
        recursive: If True, scan subdirectories recursively
    """
    if recursive:
        h5_files = sorted(input_dir.rglob("*.h5")) + sorted(input_dir.rglob("*.hdf5"))
    else:
        h5_files = sorted(input_dir.glob("*.h5")) + sorted(input_dir.glob("*.hdf5"))

    if not h5_files:
        print(f"No H5 files found in {input_dir}")
        return

    results = {
        "config": CFG,
        "files": [],
        "summary": {
            "total_files": len(h5_files),
            "skill_c_segments": 0,
            "skill_d_segments": 0,
            "skill_c_total_steps": 0,
            "skill_d_total_steps": 0,
        },
        "gate_fail_distribution": {},
    }

    for h5_file in h5_files:
        print(f"Processing: {h5_file.name}")

        try:
            obs_list = load_h5_file(h5_file)
        except Exception as e:
            print(f"  Error loading: {e}")
            results["files"].append({"file": str(h5_file), "error": str(e)})
            continue

        if sanity_check:
            sanity = run_sanity_check(obs_list)
            print(f"  Sanity check: {sanity}")

        # Label skills
        c_result = label_skill_c(obs_list)
        d_result = label_skill_d(obs_list)

        # Collect gate fail reasons
        valid, fail_reasons = compute_valid_mask(obs_list)
        for reason in fail_reasons:
            if reason:
                key = reason.split(":")[0]  # e.g., "grip_loss"
                results["gate_fail_distribution"][key] = (
                    results["gate_fail_distribution"].get(key, 0) + 1
                )

        file_result = {
            "file": str(h5_file),
            "n_steps": len(obs_list),
            "skill_c": c_result,
            "skill_d": d_result,
        }

        if sanity_check:
            file_result["sanity_check"] = run_sanity_check(obs_list)

        results["files"].append(file_result)

        # Update summary
        results["summary"]["skill_c_segments"] += len(c_result["intervals"])
        results["summary"]["skill_d_segments"] += len(d_result["intervals"])
        results["summary"]["skill_c_total_steps"] += c_result["total_success_steps"]
        results["summary"]["skill_d_total_steps"] += d_result["total_success_steps"]

        print(
            f"  Skill C: {len(c_result['intervals'])} intervals, "
            f"{c_result['total_success_steps']} steps"
        )
        print(
            f"  Skill D: {len(d_result['intervals'])} intervals, "
            f"{d_result['total_success_steps']} steps"
        )

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== Summary ===")
    print(f"Total files: {results['summary']['total_files']}")
    print(f"Skill C segments: {results['summary']['skill_c_segments']}")
    print(f"Skill D segments: {results['summary']['skill_d_segments']}")
    print(f"Skill C total steps: {results['summary']['skill_c_total_steps']}")
    print(f"Skill D total steps: {results['summary']['skill_d_total_steps']}")
    print(f"Gate fail distribution: {results['gate_fail_distribution']}")
    print(f"\nResults saved to: {output_path}")


# ============================================================
# Entry point
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Relabel demo data for Skill C/D")
    parser.add_argument(
        "--input_dir",
        type=Path,
        default=Path("data/demo_data_v1"),
        help="Directory containing H5 demo files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/relabel_results.json"),
        help="Output JSON path",
    )
    parser.add_argument(
        "--sanity_check",
        action="store_true",
        help="Run sanity check on first few files",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subdirectories recursively for H5 files",
    )
    args = parser.parse_args()

    relabel_dataset(args.input_dir, args.output, args.sanity_check, args.recursive)


if __name__ == "__main__":
    main()
