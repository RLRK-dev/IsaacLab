"""obs_collector.py — Collects 24D obs statistics across grasp episodes.

Used by SOMA Phase B1 to gather min/max/mean/std/p5/p95/p99 statistics
for observation normalization and action clip width.
"""

import json
import os
from collections import defaultdict

import numpy as np
import torch

try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False


class ObsCollector:
    """Collects 24D observations at each step, tagged with phase and env info.

    Usage:
        collector = ObsCollector(obs_builder, all_env_origins, ...)
        # Inside grasp loop:
        collector.record(phase_id, step, env_idx, robot_left, robot_right, cable)
        # After all episodes:
        stats = collector.compute_stats()
        collector.save(output_dir)
    """

    # Phase name mapping for readable output
    PHASE_NAMES = {
        2.5: "P25_fine_position",
        2.9: "P29_ik_descent",
        2.95: "P295_xy_correct",
        2.99: "P299_wrist_rotation",
        2.995: "P2995_final_align",
        3.0: "P3_close",
        3.5: "P35_settle",
        4.0: "P4_lift",
    }

    def __init__(self, obs_builder, all_env_origins, hand_body_left, hand_body_right):
        self.obs_builder = obs_builder
        self.all_env_origins = all_env_origins
        self.hand_body_left = hand_body_left
        self.hand_body_right = hand_body_right
        # Storage: list of dicts per episode (env_idx)
        self._records = []  # flat list of (obs_24d, phase, step, env_idx, episode_idx)
        self._episode_count = 0
        self._current_episode = -1
        self._current_env_idx = -1
        self._prev_step = -1

    def start_episode(self, env_idx: int):
        """Call at the start of each grasp sequence for an env."""
        self._current_episode = self._episode_count
        self._current_env_idx = env_idx
        self._episode_count += 1
        self._prev_step = -1
        # Reset obs_builder state for clean force_derivative
        self.obs_builder.reset()

    def record(self, phase_id: float, step: int,
               robot_left, robot_right, cable):
        """Record one 24D observation snapshot.

        Args:
            phase_id: Current phase (2.5, 2.9, 2.95, 2.99, 2.995, 3.0, 3.5, 4.0)
            step: Step number within current phase
            robot_left, robot_right, cable: Isaac Lab articulations
        """
        # Compute elapsed steps since last record for force_derivative
        if self._prev_step < 0:
            elapsed = 1
        else:
            elapsed = max(step - self._prev_step, 1)
        self._prev_step = step

        obs = self.obs_builder.build(
            robot_left, robot_right, cable,
            self.hand_body_left, self.hand_body_right,
            env_origins=self.all_env_origins,
            sim_steps_elapsed=elapsed,
        )
        # Extract only the current env's observation
        obs_env = obs[self._current_env_idx].detach().cpu().numpy()

        self._records.append({
            'obs': obs_env,  # (24,)
            'phase': phase_id,
            'step': step,
            'env_idx': self._current_env_idx,
            'episode': self._current_episode,
        })

    def compute_stats(self) -> dict:
        """Compute statistics over all collected observations.

        Returns dict with:
            - 'overall': stats across all phases
            - 'per_phase': {phase_id: stats} for each phase
        Each stats dict has: min, max, mean, std, p5, p95, p99 (each shape (24,))
        """
        if not self._records:
            return {}

        all_obs = np.stack([r['obs'] for r in self._records])  # (T, 24)
        phases = np.array([r['phase'] for r in self._records])

        def _stats(arr):
            """Compute stats for (T, 24) array."""
            return {
                'min': arr.min(axis=0).tolist(),
                'max': arr.max(axis=0).tolist(),
                'mean': arr.mean(axis=0).tolist(),
                'std': arr.std(axis=0).tolist(),
                'p5': np.percentile(arr, 5, axis=0).tolist(),
                'p95': np.percentile(arr, 95, axis=0).tolist(),
                'p99': np.percentile(arr, 99, axis=0).tolist(),
                'count': int(arr.shape[0]),
            }

        result = {
            'overall': _stats(all_obs),
            'per_phase': {},
            'total_records': len(self._records),
            'total_episodes': self._episode_count,
        }

        # Per-phase stats
        unique_phases = sorted(set(phases.tolist()))
        for ph in unique_phases:
            mask = phases == ph
            ph_obs = all_obs[mask]
            ph_name = self.PHASE_NAMES.get(ph, f"P{ph}")
            result['per_phase'][ph_name] = _stats(ph_obs)

        return result

    def save(self, output_dir: str):
        """Save collected data to HDF5 and JSON summary."""
        os.makedirs(output_dir, exist_ok=True)

        stats = self.compute_stats()

        # --- JSON summary ---
        # Add dimension names for readability
        dim_names = [
            "left_j0", "left_j1", "left_j2", "left_j3", "left_j4", "left_j5", "left_j6",
            "right_j0", "right_j1", "right_j2", "right_j3", "right_j4", "right_j5", "right_j6",
            "cable_mid_x", "cable_mid_y", "cable_mid_z",
            "cable_tension",
            "ee_err_left", "ee_err_right",
            "force_deriv_left", "force_deriv_right",
            "grip_effort_left", "grip_effort_right",
        ]
        stats['dim_names'] = dim_names

        json_path = os.path.join(output_dir, 'obs24d_summary.json')
        with open(json_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"[B1] Saved obs24d_summary.json: {json_path}")

        # --- HDF5 ---
        if HAS_H5PY and self._records:
            h5_path = os.path.join(output_dir, 'obs24d_stats.h5')
            all_obs = np.stack([r['obs'] for r in self._records])
            phases = np.array([r['phase'] for r in self._records])
            steps = np.array([r['step'] for r in self._records])
            env_ids = np.array([r['env_idx'] for r in self._records])
            episodes = np.array([r['episode'] for r in self._records])

            with h5py.File(h5_path, 'w') as hf:
                hf.create_dataset('obs', data=all_obs, compression='gzip')
                hf.create_dataset('phase', data=phases)
                hf.create_dataset('step', data=steps)
                hf.create_dataset('env_idx', data=env_ids)
                hf.create_dataset('episode', data=episodes)
                hf.attrs['dim_names'] = dim_names
                hf.attrs['total_episodes'] = self._episode_count
            print(f"[B1] Saved obs24d_stats.h5: {h5_path} ({len(self._records)} records)")
        elif not HAS_H5PY:
            print("[B1] h5py not available, skipping HDF5 output")

        # --- Print summary table ---
        self._print_summary(stats)

        return stats

    def _print_summary(self, stats: dict):
        """Print formatted summary table."""
        dim_names = stats.get('dim_names', [f"d{i}" for i in range(24)])
        overall = stats['overall']

        print(f"\n[B1] === 24D Obs Statistics ({overall['count']} samples, "
              f"{stats['total_episodes']} episodes) ===")
        print(f"{'Dim':<20} {'min':>10} {'p5':>10} {'mean':>10} {'p95':>10} {'max':>10} {'std':>10}")
        print("-" * 90)
        for i, name in enumerate(dim_names):
            print(f"{name:<20} {overall['min'][i]:>10.4f} {overall['p5'][i]:>10.4f} "
                  f"{overall['mean'][i]:>10.4f} {overall['p95'][i]:>10.4f} "
                  f"{overall['max'][i]:>10.4f} {overall['std'][i]:>10.4f}")

        # Per-phase count
        print(f"\n[B1] Per-phase sample counts:")
        for ph_name, ph_stats in stats.get('per_phase', {}).items():
            print(f"  {ph_name}: {ph_stats['count']} samples")
