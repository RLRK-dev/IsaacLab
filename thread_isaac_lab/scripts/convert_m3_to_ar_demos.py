# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Convert M3/M3-AR DA-MPPI HDF5 demos to AR-compatible npz for DAPG BC.

Auto-detects action layout via /metadata group:
- M3 (legacy generate_demos_mppi_m3.py): no /metadata or layout="L-first" →
  applies L→R remap to match AR env layout.
- M3-AR (generate_demos_mppi_m3_ar.py): /metadata.action_layout="R-first" →
  pass-through, no remap.

Reconstructs AR env 45D obs (42 + 3 zero pad) from per-step ee pose +
cable body positions + constants (α-4 direct compute strategy per
m4_converter_design.md §9b). Final 12D action is R-first to match
newton_aerial_regrasp_env.py:29-32.

Usage (M3-AR commit cell, Phase β closure 2026-04-25):
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/convert_m3_to_ar_demos.py \\
        --input data/mppi_demos_m3_ar/phase1_sweep/demos_p0_cost0.3_ow0.75_rot0.15.hdf5 \\
        --output thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_mppi_v1_a4.npz

Usage (legacy M3 HDF5, L-first remap):
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/convert_m3_to_ar_demos.py \\
        --input data/mppi_demos_m3/demos_default.hdf5 \\
        --output thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_v15_mppi.npz
"""

import argparse
import os
import sys

import h5py
import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_D, "..", "envs"))
sys.path.insert(0, os.path.join(_D, "..", "configs"))

from newton_skill_env_base import (  # noqa: E402
    compute_clamp_pos,
    compute_ori_error_axis_angle,
    find_nearest_cable_point,
    normalize_quat_w_positive,
)
from cable_orientation_utils import compute_hand_quat_for_cable  # noqa: E402
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z, FINGER_OPEN_POS  # noqa: E402


CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

# AR env obs is 42D + 3-zero pad = 45D
OBS_DIM = 45
ACTION_DIM = 12


def _compute_obs_step(ee_l_pos, ee_l_quat, ee_r_pos, ee_r_quat, cable_pos):
    """Reconstruct AR env 42D obs for one timestep (zero pad to 45D by caller).

    Layout (matches newton_aerial_regrasp_env.py _compute_obs_batch):
      [0:3]   clamp_r_pos
      [3:7]   clamp_r_quat (xyzw, w>=0)
      [7]     r_finger_opening (2*FINGER_OPEN_POS during approach)
      [8:11]  clamp_l_pos
      [11:15] clamp_l_quat
      [15]    l_finger_opening
      [16:19] seg_pos (R-arm target on cable)
      [19:23] seg_quat
      [23:26] clip_pos (constant)
      [26:30] clip_quat (constant)
      [30:33] ori_error_aa_r
      [33:36] pos_error_r
      [36:39] ori_error_aa_l
      [39:42] pos_error_l
    """
    ee_r_quat = normalize_quat_w_positive(ee_r_quat)
    ee_l_quat = normalize_quat_w_positive(ee_l_quat)

    clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat).astype(np.float32)
    clamp_l_pos = compute_clamp_pos(ee_l_pos, ee_l_quat).astype(np.float32)

    n_cable = cable_pos.shape[0]
    all_idx = np.arange(n_cable, dtype=np.int32)

    seg_pos_r, seg_tangent_r, _ = find_nearest_cable_point(cable_pos, clamp_r_pos, all_idx)
    seg_pos_l, seg_tangent_l, _ = find_nearest_cable_point(cable_pos, clamp_l_pos, all_idx)

    seg_quat_r = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_r)).astype(np.float32)
    seg_quat_l = normalize_quat_w_positive(compute_hand_quat_for_cable(seg_tangent_l)).astype(np.float32)

    ori_err_r = compute_ori_error_axis_angle(ee_r_quat, seg_quat_r).astype(np.float32)
    ori_err_l = compute_ori_error_axis_angle(ee_l_quat, seg_quat_l).astype(np.float32)

    pos_err_r = (clamp_r_pos - seg_pos_r).astype(np.float32)
    pos_err_l = (clamp_l_pos - seg_pos_l).astype(np.float32)

    finger_open = np.float32(2.0 * FINGER_OPEN_POS)

    obs = np.zeros(42, dtype=np.float32)
    obs[0:3] = clamp_r_pos
    obs[3:7] = ee_r_quat.astype(np.float32)
    obs[7] = finger_open
    obs[8:11] = clamp_l_pos
    obs[11:15] = ee_l_quat.astype(np.float32)
    obs[15] = finger_open
    obs[16:19] = seg_pos_r
    obs[19:23] = seg_quat_r
    obs[23:26] = CLIP1_POS
    obs[26:30] = CLIP1_QUAT_XYZW
    obs[30:33] = ori_err_r
    obs[33:36] = pos_err_r
    obs[36:39] = ori_err_l
    obs[39:42] = pos_err_l
    return obs


def _remap_action_l_first_to_r_first(a_lfirst):
    """M3 L-first [L_pos, L_ori, R_pos, R_ori] → AR R-first [R_pos, R_ori, L_pos, L_ori]."""
    a = np.zeros_like(a_lfirst)
    a[..., 0:6] = a_lfirst[..., 6:12]
    a[..., 6:12] = a_lfirst[..., 0:6]
    return a


def convert(input_path: str, output_path: str, success_only: bool = True) -> None:
    with h5py.File(input_path, "r") as f:
        # Auto-detect action layout from /metadata (M3-AR R-first vs M3 legacy L-first).
        # M3 generator wrote no /metadata group → L-first default.
        # M3-AR generator writes /metadata with action_layout="R-first".
        layout = "L-first"
        generator_tag = "m3_legacy_l_first"
        if "metadata" in f:
            meta = f["metadata"].attrs
            layout = str(meta.get("action_layout", "L-first"))
            gen = str(meta.get("generator", "unknown"))
            ar_ver = str(meta.get("ar_version", "")).lstrip("v")
            generator_tag = f"{gen}_v{ar_ver}" if ar_ver else gen
        else:
            print("[CONV] WARN: no /metadata group, assuming L-first (legacy M3 HDF5)")

        episode_names = sorted(
            [k for k in f.keys() if k.startswith("episode_")],
            key=lambda s: int(s.split("_")[1]),
        )
        print(f"[CONV] Input: {input_path}")
        print(f"[CONV] Episodes found: {len(episode_names)}")
        print(f"[CONV] Action layout: {layout}, generator: {generator_tag}")

        obs_list = []
        act_list = []
        ep_lens = []
        ep_success = []
        n_skipped = 0
        for ep_name in episode_names:
            g = f[ep_name]
            if "cable_pos_seq" not in g:
                print(f"[CONV] WARN: {ep_name} missing cable_pos_seq — SKIP (re-run modified M3 generator)")
                n_skipped += 1
                continue
            success = bool(g.attrs.get("success", False))
            if success_only and not success:
                print(f"[CONV] {ep_name}: success=False — skipping")
                n_skipped += 1
                continue

            ee_l_pos = g["left_ee_pos"][()]
            ee_r_pos = g["right_ee_pos"][()]
            ee_l_quat = g["left_ee_quat"][()]
            ee_r_quat = g["right_ee_quat"][()]
            actions = g["action_delta"][()]
            cable_pos_seq = g["cable_pos_seq"][()]

            T = ee_l_pos.shape[0]
            if not (ee_r_pos.shape[0] == T == actions.shape[0] == cable_pos_seq.shape[0]):
                print(
                    f"[CONV] WARN {ep_name}: length mismatch "
                    f"L={ee_l_pos.shape[0]} R={ee_r_pos.shape[0]} "
                    f"act={actions.shape[0]} cable={cable_pos_seq.shape[0]} — SKIP"
                )
                n_skipped += 1
                continue
            if T < 2:
                print(f"[CONV] {ep_name}: T={T} < 2 — SKIP (need ≥2 steps for BC pairing)")
                n_skipped += 1
                continue

            # BUG 1 FIX: M3 HDF5 stores POST-physics ee_pos[t] paired with action[t]
            # that PRODUCED it from ee_pos[t-1]. For BC we need pre-action state:
            #   obs_bc[i] = reconstruct(ee_pos[i])       (post-state of step i)
            #   act_bc[i] = action[i+1]                  (action taken FROM that state)
            # Indices: i in [0..T-2] → (T-1) pairs per episode (first action discarded).
            n_pairs = T - 1
            ep_obs = np.zeros((n_pairs, OBS_DIM), dtype=np.float32)
            for i in range(n_pairs):
                obs42 = _compute_obs_step(
                    ee_l_pos[i], ee_l_quat[i], ee_r_pos[i], ee_r_quat[i], cable_pos_seq[i]
                )
                ep_obs[i, :42] = obs42
                # [42:45] are zero pad

            # Conditional remap: M3 (L-first) needs L→R remap; M3-AR (R-first native) pass-through.
            if layout in ("R-first", "r-first"):
                ep_act = actions[1:T].astype(np.float32)
            else:
                ep_act = _remap_action_l_first_to_r_first(actions[1:T]).astype(np.float32)
            obs_list.append(ep_obs)
            act_list.append(ep_act)
            ep_lens.append(n_pairs)
            ep_success.append(success)
            print(f"[CONV] {ep_name}: T={T} pairs={n_pairs} success={success} (BC off-by-one shift applied)")

        if not obs_list:
            raise RuntimeError(f"No usable episodes after filtering. Skipped={n_skipped}")

        obs_all = np.concatenate(obs_list, axis=0)
        act_all = np.concatenate(act_list, axis=0)
        ep_lens_arr = np.array(ep_lens, dtype=np.int64)

        # Validation gates
        total = obs_all.shape[0]
        act_sat = float(np.mean(np.abs(act_all) > 0.99))
        l_rms = float(np.sqrt(np.mean(act_all[:, 6:12] ** 2)))
        r_rms = float(np.sqrt(np.mean(act_all[:, 0:6] ** 2)))
        obs_mean = obs_all.mean(axis=0)
        obs_std = obs_all.std(axis=0)

        print("\n=== VALIDATION ===")
        print(f"  total transitions: {total}")
        print(f"  episodes kept: {len(ep_lens)} / {len(episode_names)} (skipped {n_skipped})")
        print(f"  obs shape: {obs_all.shape}  act shape: {act_all.shape}")
        print(f"  action saturation (|a|>0.99): {act_sat:.3%}  (gate <10%)")
        print(f"  R-arm action RMS: {r_rms:.3f}")
        print(f"  L-arm action RMS: {l_rms:.3f}")
        print(f"  obs[0] (clamp_r_x) mean/std: {obs_mean[0]:.3f} / {obs_std[0]:.3f}")
        print(f"  obs[8] (clamp_l_x) mean/std: {obs_mean[8]:.3f} / {obs_std[8]:.3f}")
        print(f"  obs[23] (clip_x) mean/std: {obs_mean[23]:.3f} / {obs_std[23]:.3f}")

        # Dynamic source field reflects detected generator + layout.
        source_str = (
            f"m3_ar_da_mppi_phase_beta_a4 (layout=R-first, generator={generator_tag})"
            if layout in ("R-first", "r-first")
            else f"m3_da_mppi_v6.3.2 (layout=L-first, generator={generator_tag}, remapped to R-first)"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        np.savez(
            output_path,
            obs=obs_all.astype(np.float32),
            actions=act_all.astype(np.float32),
            episode_lengths=ep_lens_arr,
            episode_success=np.array(ep_success, dtype=bool),
            source=source_str,
            lambda_val=0.3,
        )
        print(f"\n[CONV] Saved → {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Input M3 HDF5 with cable_pos_seq")
    parser.add_argument(
        "--output",
        type=str,
        default="thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_mppi_v1_a4.npz",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include failed episodes (default: success-only)",
    )
    args = parser.parse_args()
    convert(args.input, args.output, success_only=not args.all)


if __name__ == "__main__":
    main()
