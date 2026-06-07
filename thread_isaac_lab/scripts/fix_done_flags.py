#!/usr/bin/env python3
"""Fix done flags in existing h5 data files.

The original data collection didn't set done=True at episode boundaries.
This script adds the correct done flags based on known episode structure.

Episode structure:
- num_envs = 16
- max_steps = 100 per episode
- samples_per_episode = 16 * 100 = 1600

For each episode, the last step (samples indices 1584-1599 within the episode)
should have done=True for all environments.
"""

import os
import argparse
import glob
import h5py
import numpy as np


def fix_done_flags(input_dir: str, output_dir: str, num_envs: int = 16, max_steps: int = 100):
    """Fix done flags in h5 files.

    Args:
        input_dir: Directory containing original h5 files
        output_dir: Directory to save fixed h5 files
        num_envs: Number of parallel environments used during collection
        max_steps: Steps per episode during collection
    """
    os.makedirs(output_dir, exist_ok=True)

    samples_per_episode = num_envs * max_steps
    print(f"[Config] num_envs={num_envs}, max_steps={max_steps}")
    print(f"[Config] samples_per_episode={samples_per_episode}")

    input_files = sorted(glob.glob(os.path.join(input_dir, "*.h5")))
    print(f"[Files] Found {len(input_files)} files to process")

    total_fixed = 0

    for file_idx, input_path in enumerate(input_files):
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, filename)

        print(f"\n[{file_idx+1}/{len(input_files)}] Processing {filename}...")

        with h5py.File(input_path, 'r') as f_in:
            num_samples = f_in['proprio'].shape[0]
            num_episodes = num_samples // samples_per_episode

            print(f"  Samples: {num_samples}, Episodes: {num_episodes}")

            # Create new done array
            done = np.zeros(num_samples, dtype=bool)

            # Set done=True for last step of each episode (all envs)
            for ep in range(num_episodes):
                # Last step indices for this episode
                # Episode starts at ep * samples_per_episode
                # Last step is at (ep + 1) * samples_per_episode - num_envs
                last_step_start = (ep + 1) * samples_per_episode - num_envs
                last_step_end = (ep + 1) * samples_per_episode
                done[last_step_start:last_step_end] = True

            # Handle remaining samples (partial episode at end)
            remaining = num_samples % samples_per_episode
            if remaining > 0:
                print(f"  Warning: {remaining} samples don't fit in complete episodes")

            fixed_count = done.sum()
            total_fixed += fixed_count
            print(f"  Setting done=True for {fixed_count} samples ({num_episodes} episode ends × {num_envs} envs)")

            # Copy file with fixed done flags
            with h5py.File(output_path, 'w') as f_out:
                # Copy all datasets
                for key in f_in.keys():
                    if key == 'done':
                        # Use our fixed done array
                        f_out.create_dataset('done', data=done, dtype=bool)
                    else:
                        # Copy original data
                        f_out.create_dataset(key, data=f_in[key][:], dtype=f_in[key].dtype)

                # Copy attributes
                for attr_name, attr_value in f_in.attrs.items():
                    f_out.attrs[attr_name] = attr_value

        print(f"  Saved to {output_path}")

    print(f"\n[Done] Fixed {total_fixed} done flags across {len(input_files)} files")
    print(f"[Output] Files saved to {output_dir}")


def verify_done_flags(data_dir: str, num_envs: int = 16, max_steps: int = 100):
    """Verify done flags are correctly set."""
    samples_per_episode = num_envs * max_steps

    files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))

    print(f"\n[Verify] Checking {len(files)} files...")

    for file_path in files[:2]:  # Check first 2 files
        print(f"\n  Checking {os.path.basename(file_path)}...")

        with h5py.File(file_path, 'r') as f:
            done = f['done'][:]
            num_samples = len(done)
            num_episodes = num_samples // samples_per_episode

            print(f"    Samples: {num_samples}, Episodes: {num_episodes}")
            print(f"    done=True count: {done.sum()}")
            print(f"    Expected: {num_episodes * num_envs}")

            # Check first few episode boundaries
            for ep in range(min(3, num_episodes)):
                last_step_start = (ep + 1) * samples_per_episode - num_envs
                last_step_end = (ep + 1) * samples_per_episode

                ep_done = done[last_step_start:last_step_end]
                print(f"    Episode {ep} end (idx {last_step_start}-{last_step_end-1}): all done={ep_done.all()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix done flags in h5 data files")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory with h5 files")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for fixed files")
    parser.add_argument("--num_envs", type=int, default=16, help="Number of parallel envs used during collection")
    parser.add_argument("--max_steps", type=int, default=100, help="Steps per episode during collection")
    parser.add_argument("--verify", action="store_true", help="Verify done flags after fixing")

    args = parser.parse_args()

    fix_done_flags(args.input_dir, args.output_dir, args.num_envs, args.max_steps)

    if args.verify:
        verify_done_flags(args.output_dir, args.num_envs, args.max_steps)
