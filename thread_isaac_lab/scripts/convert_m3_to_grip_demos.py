# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Convert M3-Grip DA-MPPI HDF5 demos to Grip-compatible npz for DAPG BC.

Adapted from ``convert_m3_to_ac_demos.py`` (AC M4 α-4 direct compute) with
Grip-specific extensions for:

- 14D R-first action (vs AC 12D): env ``newton_clamp_env.py:28-34`` native
  layout ``[0:3] R_pos, [3:6] R_ori, [6:9] L_pos, [9:12] L_ori, [12] R_finger, [13] L_finger``.
- Finger opening from stored HDF5 datasets (vs AC constant ``2*FINGER_OPEN_POS``):
  ``finger_opening_R`` → ``obs[7]``, ``finger_opening_L`` → ``obs[15]`` per env
  ``newton_clamp_env.py:702-703`` convention ``opening = jq[7] + jq[8]``.
- Source metadata ``m3_grip_option_b_scripted_v1`` (Option B default; Option A
  deferred per ``memory/project_g3b_option_a_deferred.md``).

Grip env obs (42D + 3 zero pad = 45D) byte-for-byte reconstructable from stored
EE poses + cable_pos_seq + finger_opening_* + CLIP1 constants (same structure
as AC obs, except finger_opening entries use actual values).

Usage
-----
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/convert_m3_to_grip_demos.py \\
        --input thread_isaac_lab/data/mppi_demos_m3_grip/demos_default.hdf5 \\
        --output thread_isaac_lab/data/bc_demos/grip_clamp_demos_mppi_v1.npz

Multi-file aggregation supported via repeat ``--input``.
"""

from __future__ import annotations

import argparse
import os
import sys

import h5py
import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_D, "..", "envs"))
sys.path.insert(0, os.path.join(_D, "..", "configs"))

from cable_orientation_utils import compute_hand_quat_for_cable  # noqa: E402
from newton_skill_env_base import (  # noqa: E402
    compute_clamp_pos,
    compute_ori_error_axis_angle,
    find_nearest_cable_point,
    normalize_quat_w_positive,
)
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z  # noqa: E402

CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

# Grip env obs = 42D + 3-zero pad = 45D (matches newton_clamp_env.py :11-26)
OBS_DIM = 45
# Grip R-first 14D action: 12D EE delta + 2D finger_cmd (env :28-34)
ACTION_DIM = 14


def _compute_obs_step_grip(
    ee_l_pos: np.ndarray,
    ee_l_quat: np.ndarray,
    ee_r_pos: np.ndarray,
    ee_r_quat: np.ndarray,
    cable_pos: np.ndarray,
    l_finger_opening: float,
    r_finger_opening: float,
) -> np.ndarray:
    """Reconstruct Grip env 42D obs for one timestep (zero pad to 45D by caller).

    Layout mirrors ``newton_clamp_env.py`` docstring (lines 11-26) and matches
    env ``_compute_obs_batch`` byte-for-byte except finger_opening entries use
    stored values instead of AC's constant ``2*FINGER_OPEN_POS``:

      [0:3]   clamp_r_pos (fingertip via compute_clamp_pos)
      [3:7]   clamp_r_quat (xyzw, w>=0)
      [7]     r_finger_opening (j7 + j8, from HDF5 stored value)
      [8:11]  clamp_l_pos
      [11:15] clamp_l_quat
      [15]    l_finger_opening
      [16:19] seg_pos_r (R-arm nearest point on cable)
      [19:23] seg_quat_r (hand-down quat from cable tangent at seg_r, w>=0)
      [23:26] CLIP1_POS (constant)
      [26:30] CLIP1_QUAT_XYZW (constant = identity)
      [30:33] ori_error_aa_r (axis-angle from clamp_r_quat to seg_quat_r)
      [33:36] pos_error_r (= clamp_r_pos - seg_pos_r)
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

    obs = np.zeros(42, dtype=np.float32)
    obs[0:3] = clamp_r_pos
    obs[3:7] = ee_r_quat.astype(np.float32)
    obs[7] = np.float32(r_finger_opening)
    obs[8:11] = clamp_l_pos
    obs[11:15] = ee_l_quat.astype(np.float32)
    obs[15] = np.float32(l_finger_opening)
    obs[16:19] = seg_pos_r
    obs[19:23] = seg_quat_r
    obs[23:26] = CLIP1_POS
    obs[26:30] = CLIP1_QUAT_XYZW
    obs[30:33] = ori_err_r
    obs[33:36] = pos_err_r
    obs[36:39] = ori_err_l
    obs[39:42] = pos_err_l
    return obs


def convert(input_paths: list[str], output_path: str, success_only: bool = True) -> None:
    obs_list: list[np.ndarray] = []
    act_list: list[np.ndarray] = []
    ep_lens: list[int] = []
    ep_success: list[bool] = []
    ep_keys_taken: list[str] = []
    n_skipped = 0
    n_total_episodes = 0
    # B3-β r_arm_only auto-detect across input(s); first-input attr seeds source_label.
    detected_single_arm: str = "none"
    detected_generator_variant: str = "bimanual_v3_envstep"

    for input_path in input_paths:
        with h5py.File(input_path, "r") as f:
            meta = f["metadata"]
            layout = meta.attrs["action_layout"]
            if layout != "R-first":
                raise ValueError(
                    f"{input_path}: action_layout={layout!r} — Grip generator expects R-first "
                    "(env newton_clamp_env.py:28-34 native). HDF5 may be from wrong generator."
                )
            hdf5_action_dim = int(meta.attrs.get("hdf5_action_dim", -1))
            if hdf5_action_dim != ACTION_DIM:
                raise ValueError(
                    f"{input_path}: hdf5_action_dim={hdf5_action_dim} != expected {ACTION_DIM} "
                    "(14D R-first EE+finger). HDF5 may be from wrong generator or version."
                )
            finger_mode = meta.attrs.get("finger_mode", "unknown")
            generator = meta.attrs.get("generator", "unknown")
            grip_version = meta.attrs.get("grip_version", "unknown")
            meta_pos_scale = float(meta.attrs.get("mppi_pos_action_scale", np.nan))
            meta_rot_scale = float(meta.attrs.get("mppi_rot_action_scale", np.nan))
            # B3-β: auto-detect r_arm_only via single_arm attr (h5py byte→str cast for safety, CC4-5 lens)
            sa = meta.attrs.get("single_arm", "none")
            single_arm_str = sa.decode() if isinstance(sa, bytes) else str(sa)
            gv = meta.attrs.get("generator_variant", "bimanual_v3_envstep")
            generator_variant_str = gv.decode() if isinstance(gv, bytes) else str(gv)
            if single_arm_str != "none":
                detected_single_arm = single_arm_str
                detected_generator_variant = generator_variant_str
            print(
                f"[CONV] Input: {input_path}  (generator={generator}, grip_version={grip_version}, "
                f"finger_mode={finger_mode}, pos_scale={meta_pos_scale}, rot_scale={meta_rot_scale}, "
                f"single_arm={single_arm_str})"
            )

            episode_names = sorted(
                [k for k in f.keys() if k.startswith("episode_")],
                key=lambda s: int(s.split("_")[1]),
            )
            n_total_episodes += len(episode_names)
            print(f"[CONV]   episodes: {len(episode_names)}")

            for ep_name in episode_names:
                g = f[ep_name]
                missing_keys = [
                    k
                    for k in (
                        "cable_pos_seq",
                        "finger_opening_L",
                        "finger_opening_R",
                        "left_ee_pos",
                        "left_ee_quat",
                        "right_ee_pos",
                        "right_ee_quat",
                        "action_delta",
                    )
                    if k not in g
                ]
                if missing_keys:
                    print(f"[CONV]   WARN {ep_name}: missing dataset(s) {missing_keys} — SKIP")
                    n_skipped += 1
                    continue
                success = bool(g.attrs.get("success", False))
                if success_only and not success:
                    n_skipped += 1
                    continue

                ee_l_pos = g["left_ee_pos"][()]
                ee_r_pos = g["right_ee_pos"][()]
                ee_l_quat = g["left_ee_quat"][()]
                ee_r_quat = g["right_ee_quat"][()]
                actions = g["action_delta"][()]
                cable_pos_seq = g["cable_pos_seq"][()]
                finger_opening_L = g["finger_opening_L"][()]
                finger_opening_R = g["finger_opening_R"][()]

                T = ee_l_pos.shape[0]
                shapes_match = (
                    ee_r_pos.shape[0]
                    == T
                    == actions.shape[0]
                    == cable_pos_seq.shape[0]
                    == finger_opening_L.shape[0]
                    == finger_opening_R.shape[0]
                )
                if not shapes_match:
                    print(
                        f"[CONV]   WARN {ep_name}: length mismatch "
                        f"L={ee_l_pos.shape[0]} R={ee_r_pos.shape[0]} "
                        f"act={actions.shape[0]} cable={cable_pos_seq.shape[0]} "
                        f"fL={finger_opening_L.shape[0]} fR={finger_opening_R.shape[0]} — SKIP"
                    )
                    n_skipped += 1
                    continue
                if T < 2:
                    print(f"[CONV]   {ep_name}: T={T} < 2 — SKIP (need ≥2 steps for BC pairing)")
                    n_skipped += 1
                    continue
                if actions.shape[1] != ACTION_DIM:
                    print(f"[CONV]   WARN {ep_name}: action shape[1]={actions.shape[1]} != {ACTION_DIM} — SKIP")
                    n_skipped += 1
                    continue

                # BC pairing (inherited from AR / AC converter):
                #   HDF5 ee_pos[t] is the POST-physics state produced by action[t]
                #   (applied from ee_pos[t-1]). For BC we want pre-action state:
                #     obs_bc[i] = reconstruct(ee_pos[i])   (post-state of step i)
                #     act_bc[i] = action[i+1]              (action taken FROM that state)
                #   Pairs: i in [0..T-2] → (T-1) per episode. First action dropped.
                n_pairs = T - 1
                ep_obs = np.zeros((n_pairs, OBS_DIM), dtype=np.float32)
                for i in range(n_pairs):
                    obs42 = _compute_obs_step_grip(
                        ee_l_pos[i],
                        ee_l_quat[i],
                        ee_r_pos[i],
                        ee_r_quat[i],
                        cable_pos_seq[i],
                        float(finger_opening_L[i]),
                        float(finger_opening_R[i]),
                    )
                    ep_obs[i, :42] = obs42
                    # ep_obs[i, 42:45] left as zero pad

                ep_act = actions[1:T].astype(np.float32)  # R-first native, no remap

                # NaN/inf sanity (CC Debate precedent: AR / AC converters)
                if not np.isfinite(ep_obs).all():
                    bad = int((~np.isfinite(ep_obs)).sum())
                    print(f"[CONV]   WARN {ep_name}: {bad} non-finite values in obs — SKIP")
                    n_skipped += 1
                    continue
                if not np.isfinite(ep_act).all():
                    bad = int((~np.isfinite(ep_act)).sum())
                    print(f"[CONV]   WARN {ep_name}: {bad} non-finite values in act — SKIP")
                    n_skipped += 1
                    continue

                obs_list.append(ep_obs)
                act_list.append(ep_act)
                ep_lens.append(n_pairs)
                ep_success.append(success)
                ep_keys_taken.append(f"{os.path.basename(os.path.dirname(input_path))}/{ep_name}")
                print(f"[CONV]   {ep_name}: T={T} pairs={n_pairs} success={success}")

    if not obs_list:
        raise RuntimeError(f"No usable episodes after filtering. Skipped={n_skipped}/{n_total_episodes}")

    obs_all = np.concatenate(obs_list, axis=0)
    act_all = np.concatenate(act_list, axis=0)
    ep_lens_arr = np.array(ep_lens, dtype=np.int64)
    ep_success_arr = np.array(ep_success, dtype=bool)

    # Validation gates
    total = obs_all.shape[0]
    act_sat = float(np.mean(np.abs(act_all[:, :12]) > 0.99))  # EE saturation (exclude fingers)
    finger_sat = float(np.mean(np.abs(act_all[:, 12:14]) > 0.99))
    r_rms = float(np.sqrt(np.mean(act_all[:, 0:6] ** 2)))
    l_rms = float(np.sqrt(np.mean(act_all[:, 6:12] ** 2)))
    finger_rms = float(np.sqrt(np.mean(act_all[:, 12:14] ** 2)))
    obs_mean = obs_all.mean(axis=0)
    obs_std = obs_all.std(axis=0)
    r_finger_open_mean = float(obs_mean[7])
    l_finger_open_mean = float(obs_mean[15])
    pos_err_r_rms = float(np.sqrt(np.mean(np.sum(obs_all[:, 33:36] ** 2, axis=1))))

    print("\n=== VALIDATION ===")
    print(f"  total transitions: {total}")
    print(f"  episodes kept: {len(ep_lens)} / {n_total_episodes} (skipped {n_skipped})")
    print(f"  obs shape: {obs_all.shape}  act shape: {act_all.shape}")
    print(f"  EE action saturation (|a|>0.99): {act_sat:.3%}  (gate <10%)")
    print(f"  Finger action saturation (|a|>0.99): {finger_sat:.3%}  (scripted: expect high)")
    print(f"  R-arm EE action RMS: {r_rms:.3f}")
    print(f"  L-arm EE action RMS: {l_rms:.3f}")
    print(f"  Finger action RMS: {finger_rms:.3f}")
    print(f"  obs[0] (clamp_r_x) mean/std: {obs_mean[0]:.3f} / {obs_std[0]:.3f}")
    print(f"  obs[2] (clamp_r_z) mean/std: {obs_mean[2]:.3f} / {obs_std[2]:.3f}")
    print(f"  obs[7] (r_finger_opening) mean/std: {r_finger_open_mean:.4f} / {obs_std[7]:.4f} m")
    print(f"  obs[15] (l_finger_opening) mean/std: {l_finger_open_mean:.4f} / {obs_std[15]:.4f} m")
    print(f"  obs[23] (clip_x) mean/std: {obs_mean[23]:.3f} / {obs_std[23]:.3f}")
    print(f"  obs[33:36] pos_err_r RMS magnitude: {pos_err_r_rms:.4f} m")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    # B3-β: source_label switch via auto-detected single_arm attr (CC4-5 lens)
    if detected_single_arm == "R":
        source_label = (
            f"m3_grip_r_only_v1 (strategy=B3-beta scripted MPPI rollout, "
            f"L frozen via preamble + execution zeroing; generator_variant={detected_generator_variant})"
        )
    else:
        source_label = (
            "m3_grip_option_b_scripted_v1 (strategy=α-4 direct compute "
            "from HDF5 EE/cable/finger_opening + env formulas)"
        )
    np.savez(
        output_path,
        obs=obs_all.astype(np.float32),
        actions=act_all.astype(np.float32),
        episode_lengths=ep_lens_arr,
        episode_success=ep_success_arr,
        source=source_label,
    )
    print(f"\n[CONV] Saved → {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=str,
        action="append",
        required=True,
        help="M3-Grip HDF5 path with cable_pos_seq + finger_opening_* (repeat for multi-file aggregation)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="thread_isaac_lab/data/bc_demos/grip_clamp_demos_mppi_v1.npz",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include failed episodes (default: success-only, matches AR/AC pattern)",
    )
    args = parser.parse_args()
    convert(args.input, args.output, success_only=not args.all)


if __name__ == "__main__":
    main()
