#!/usr/bin/env python3
"""Merge multiple HDF5 files into a single file.

This script combines h5 files from multiple data collection runs (e.g., part1, part2)
into a single combined h5 file for easier training.

Usage:
    python thread_isaac_lab/scripts/merge_h5_files.py \
        --input_dirs data/world_model_4cam_v1/part1 data/world_model_4cam_v1/part2 \
        --output_dir data/world_model_4cam_v1/combined \
        --samples_per_file 80000
"""

import argparse
import glob
import os
import h5py
import numpy as np
from datetime import datetime
from tqdm import tqdm


def get_dataset_keys(h5_file):
    """Get all dataset keys from an h5 file."""
    keys = []
    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            keys.append(name)
    h5_file.visititems(visitor)
    return keys


def merge_h5_files(input_dirs: list, output_dir: str, samples_per_file: int = 80000):
    """Merge h5 files from multiple directories."""

    os.makedirs(output_dir, exist_ok=True)

    # Find all h5 files
    all_files = []
    for input_dir in input_dirs:
        files = sorted(glob.glob(os.path.join(input_dir, "*.h5")))
        print(f"[Input] Found {len(files)} files in {input_dir}")
        all_files.extend(files)

    if not all_files:
        print("[Error] No h5 files found!")
        return

    print(f"[Total] {len(all_files)} files to merge")

    # Analyze first file to get structure
    with h5py.File(all_files[0], 'r') as f:
        dataset_keys = get_dataset_keys(f)
        print(f"[Structure] Datasets: {dataset_keys}")

        # Get data types and shapes
        dtypes = {}
        sample_shapes = {}
        for key in dataset_keys:
            dtypes[key] = f[key].dtype
            sample_shapes[key] = f[key].shape[1:] if len(f[key].shape) > 1 else ()
            print(f"  {key}: dtype={dtypes[key]}, sample_shape={sample_shapes[key]}")

    # Count total samples
    total_samples = 0
    file_sample_counts = []
    print("\n[Scanning] Counting samples...")
    for file_path in tqdm(all_files):
        with h5py.File(file_path, 'r') as f:
            n_samples = len(f[dataset_keys[0]])
            total_samples += n_samples
            file_sample_counts.append((file_path, n_samples))

    print(f"[Total] {total_samples} samples found")

    # Merge files
    output_batch_id = 0
    current_samples = 0
    buffers = {key: [] for key in dataset_keys}

    def save_batch():
        nonlocal output_batch_id, current_samples, buffers

        if current_samples == 0:
            return

        output_path = os.path.join(output_dir, f"wm_4cam_merged_{output_batch_id:04d}.h5")
        print(f"\n[Save] Writing {current_samples} samples to {output_path}")

        with h5py.File(output_path, 'w') as f:
            for key in dataset_keys:
                if dtypes[key] == h5py.special_dtype(vlen=np.uint8):
                    # Variable length data (JPEG images)
                    dt = h5py.special_dtype(vlen=np.uint8)
                    f.create_dataset(key, data=buffers[key], dtype=dt)
                else:
                    # Fixed size data
                    data = np.concatenate(buffers[key], axis=0)
                    f.create_dataset(key, data=data, dtype=dtypes[key])

            # Metadata
            f.attrs['num_cameras'] = 4
            f.attrs['camera_names'] = ['front_left', 'front_right', 'back', 'overhead']
            f.attrs['merged_from'] = [os.path.basename(fp) for fp, _ in file_sample_counts]
            f.attrs['timestamp'] = datetime.now().isoformat()

        output_batch_id += 1
        current_samples = 0
        buffers = {key: [] for key in dataset_keys}

    # Process files
    print("\n[Merging] Processing files...")
    for file_path, n_samples in tqdm(file_sample_counts):
        with h5py.File(file_path, 'r') as f:
            for key in dataset_keys:
                data = f[key][:]
                if dtypes[key] == h5py.special_dtype(vlen=np.uint8):
                    # Variable length - keep as list
                    buffers[key].extend(list(data))
                else:
                    # Fixed size - keep as array for concatenation
                    buffers[key].append(data)

            current_samples += n_samples

        # Save if we've accumulated enough samples
        if current_samples >= samples_per_file:
            save_batch()

    # Save remaining samples
    if current_samples > 0:
        save_batch()

    print(f"\n[Done] Created {output_batch_id} merged files in {output_dir}")
    print(f"[Summary] Total samples: {total_samples}")


def verify_merged_files(output_dir: str):
    """Verify the merged files."""
    files = sorted(glob.glob(os.path.join(output_dir, "*.h5")))
    print(f"\n[Verify] Checking {len(files)} merged files...")

    total_samples = 0
    for file_path in files:
        with h5py.File(file_path, 'r') as f:
            n_samples = len(f['proprio'])
            total_samples += n_samples
            print(f"  {os.path.basename(file_path)}: {n_samples} samples")

    print(f"[Total] {total_samples} samples in merged files")


def main():
    parser = argparse.ArgumentParser(description="Merge HDF5 files")
    parser.add_argument("--input_dirs", type=str, nargs='+', required=True,
                        help="Input directories containing h5 files")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Output directory for merged files")
    parser.add_argument("--samples_per_file", type=int, default=80000,
                        help="Maximum samples per output file")
    parser.add_argument("--verify", action="store_true",
                        help="Verify merged files after creation")
    args = parser.parse_args()

    merge_h5_files(args.input_dirs, args.output_dir, args.samples_per_file)

    if args.verify:
        verify_merged_files(args.output_dir)


if __name__ == "__main__":
    main()
