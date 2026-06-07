# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Convert M3-AC DA-MPPI HDF5 demos to AC-compatible npz for DAPG BC (Option β: α-4 direct compute).

Adapted from `convert_m3_to_ar_demos.py` (AR version).

Key differences vs AR script
----------------------------
- Input HDF5 already has ``action_layout = R-first`` (M3-AC generator default with
  ``--output-layout r-first``). AR script expected L-first and remapped; we
  VERIFY R-first via metadata and pass-through without remap.
- Multi-HDF5 input (repeat ``--input``) to aggregate the 4 M3-AC seed pools.
- AC obs [0:42] is byte-for-byte identical to AR obs [0:42] (both use
  ``_compute_obs_batch`` with ``compute_clamp_pos`` + ``find_nearest_cable_point``
  + ``compute_hand_quat_for_cable`` + ``CLIP1_POS/QUAT``), so ``_compute_obs_step``
  is reused unchanged.

Rationale (Option β parallel run)
---------------------------------
CC Debate (2026-04-21) determined that Option B (α-2 replay) was implemented
before α-4 (design doc §9b MVP). AR production artifact
``aerial_regrasp_demos_v14_45d.npz`` was generated via the same α-4 formula and
is in active DAPG training. This script produces the AC-side α-4 counterpart for
empirical BC-loss comparison with the α-2 replay output
``approach_cable_demos_mppi_v1.npz``.

Usage
-----
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/convert_m3_to_ac_demos.py \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s342_n15_p3/demos_default.hdf5 \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s42_p3/demos_default.hdf5 \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s142_p3/demos_default.hdf5 \
        --input thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s242_p3/demos_default.hdf5 \
        --output thread_isaac_lab/data/bc_demos/approach_cable_demos_mppi_v1_a4.npz
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
from task_config import CLIP1_X, CLIP1_Y, CLIP1_Z, FINGER_OPEN_POS  # noqa: E402

CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z], dtype=np.float32)
CLIP1_QUAT_XYZW = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

# AC env obs = 42D + 3-zero pad = 45D
OBS_DIM = 45
ACTION_DIM = 12


def _compute_obs_step(ee_l_pos, ee_l_quat, ee_r_pos, ee_r_quat, cable_pos):
    """Reconstruct AC env 42D obs for one timestep (zero pad to 45D by caller).

    Layout (matches newton_approach_cable_env.py _compute_obs_batch lines 1236-1281):
      [0:3]   clamp_r_pos (fingertip via compute_clamp_pos)
      [3:7]   clamp_r_quat (xyzw, w>=0)
      [7]     r_finger_opening (= 2 * FINGER_OPEN_POS during approach)
      [8:11]  clamp_l_pos
      [11:15] clamp_l_quat
      [15]    l_finger_opening
      [16:19] seg_pos_r (R-arm nearest point on cable piecewise-linear)
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


def convert(
    input_paths: list[str],
    output_path: str,
    success_only: bool = True,
    strict_dist_filter: float | None = None,
) -> None:
    obs_list: list[np.ndarray] = []
    act_list: list[np.ndarray] = []
    ep_lens: list[int] = []
    ep_success: list[bool] = []
    ep_keys_taken: list[str] = []
    n_skipped = 0
    n_strict_reject = 0  # Option C' strict_dist_filter reject count
    n_total_episodes = 0

    for input_path in input_paths:
        with h5py.File(input_path, "r") as f:
            meta = f["metadata"]
            layout = meta.attrs["action_layout"]
            if layout != "R-first":
                raise ValueError(
                    f"{input_path}: action_layout={layout!r} — this script requires R-first "
                    "(M3-AC native). For L-first M3 HDF5 use convert_m3_to_ar_demos.py."
                )
            meta_pos_scale = float(meta.attrs.get("pos_action_scale", np.nan))
            meta_rot_scale = float(meta.attrs.get("rot_action_scale", np.nan))
            m3_version = meta.attrs.get("m3_version", "unknown")
            print(
                f"[CONV] Input: {input_path}  (m3_version={m3_version}, "
                f"pos_scale={meta_pos_scale}, rot_scale={meta_rot_scale})"
            )

            episode_names = sorted(
                [k for k in f.keys() if k.startswith("episode_")],
                key=lambda s: int(s.split("_")[1]),
            )
            n_total_episodes += len(episode_names)
            print(f"[CONV]   episodes: {len(episode_names)}")

            for ep_name in episode_names:
                g = f[ep_name]
                if "cable_pos_seq" not in g:
                    print(f"[CONV]   WARN {ep_name}: missing cable_pos_seq — SKIP")
                    n_skipped += 1
                    continue
                success = bool(g.attrs.get("success", False))
                if success_only and not success:
                    n_skipped += 1
                    continue

                # Option C' (2026-04-25): strict final-dist filter for BC quality.
                # Rejects episodes whose last-step max-arm dist exceeds threshold
                # (pre-check Issue #CC4-10: default MPPI success threshold 80mm is
                # looser than AC T_DIST=12mm, so strict filter tightens BC targets).
                if strict_dist_filter is not None:
                    if "dist_pos_left" not in g or "dist_pos_right" not in g:
                        print(f"[CONV]   WARN {ep_name}: missing dist_pos_left/right — SKIP (strict filter on)")
                        n_skipped += 1
                        continue
                    final_dl = float(g["dist_pos_left"][()][-1])
                    final_dr = float(g["dist_pos_right"][()][-1])
                    if max(final_dl, final_dr) > strict_dist_filter:
                        print(
                            f"[CONV]   {ep_name}: strict filter REJECT "
                            f"(final L={final_dl*1000:.1f}mm R={final_dr*1000:.1f}mm > "
                            f"{strict_dist_filter*1000:.1f}mm)"
                        )
                        n_skipped += 1
                        n_strict_reject += 1
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
                        f"[CONV]   WARN {ep_name}: length mismatch "
                        f"L={ee_l_pos.shape[0]} R={ee_r_pos.shape[0]} "
                        f"act={actions.shape[0]} cable={cable_pos_seq.shape[0]} — SKIP"
                    )
                    n_skipped += 1
                    continue
                if T < 2:
                    print(f"[CONV]   {ep_name}: T={T} < 2 — SKIP (need ≥2 steps for BC pairing)")
                    n_skipped += 1
                    continue

                # BC pairing (inherited from AR converter):
                #   HDF5 ee_pos[t] is the POST-physics state produced by action[t]
                #   (applied from ee_pos[t-1]). For BC we want pre-action state:
                #     obs_bc[i] = reconstruct(ee_pos[i])   (post-state of step i)
                #     act_bc[i] = action[i+1]              (action taken FROM that state)
                #   Pairs: i in [0..T-2] → (T-1) per episode. First action dropped.
                n_pairs = T - 1
                ep_obs = np.zeros((n_pairs, OBS_DIM), dtype=np.float32)
                for i in range(n_pairs):
                    obs42 = _compute_obs_step(ee_l_pos[i], ee_l_quat[i], ee_r_pos[i], ee_r_quat[i], cable_pos_seq[i])
                    ep_obs[i, :42] = obs42
                    # ep_obs[i, 42:45] left as zero pad

                ep_act = actions[1:T].astype(np.float32)  # R-first native, no remap

                # NaN/inf sanity (CC Debate CC2/CC3 concern)
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
    act_sat = float(np.mean(np.abs(act_all) > 0.99))
    l_rms = float(np.sqrt(np.mean(act_all[:, 6:12] ** 2)))
    r_rms = float(np.sqrt(np.mean(act_all[:, 0:6] ** 2)))
    obs_mean = obs_all.mean(axis=0)
    obs_std = obs_all.std(axis=0)
    pos_err_r_rms = float(np.sqrt(np.mean(np.sum(obs_all[:, 33:36] ** 2, axis=1))))

    print("\n=== VALIDATION ===")
    print(f"  total transitions: {total}")
    print(f"  episodes kept: {len(ep_lens)} / {n_total_episodes} (skipped {n_skipped})")
    if strict_dist_filter is not None:
        print(
            f"  strict_dist_filter: {strict_dist_filter*1000:.1f}mm, "
            f"rejected {n_strict_reject} eps by this filter"
        )
    print(f"  obs shape: {obs_all.shape}  act shape: {act_all.shape}")
    print(f"  action saturation (|a|>0.99): {act_sat:.3%}  (gate <10%)")
    print(f"  R-arm action RMS: {r_rms:.3f}")
    print(f"  L-arm action RMS: {l_rms:.3f}")
    print(f"  obs[0] (clamp_r_x) mean/std: {obs_mean[0]:.3f} / {obs_std[0]:.3f}")
    print(f"  obs[2] (clamp_r_z) mean/std: {obs_mean[2]:.3f} / {obs_std[2]:.3f}")
    print(f"  obs[8] (clamp_l_x) mean/std: {obs_mean[8]:.3f} / {obs_std[8]:.3f}")
    print(f"  obs[23] (clip_x) mean/std: {obs_mean[23]:.3f} / {obs_std[23]:.3f}")
    print(f"  obs[33:36] pos_err_r RMS magnitude: {pos_err_r_rms:.4f} m")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    np.savez(
        output_path,
        obs=obs_all.astype(np.float32),
        actions=act_all.astype(np.float32),
        episode_lengths=ep_lens_arr,
        episode_success=ep_success_arr,
        source="m3_ac_a4_direct_v1 (strategy=α-4 direct compute from HDF5 EE/cable + env formulas)",
    )
    print(f"\n[CONV] Saved → {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=str,
        action="append",
        required=True,
        help="M3-AC HDF5 path with cable_pos_seq (repeat for multi-file aggregation)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="thread_isaac_lab/data/bc_demos/approach_cable_demos_mppi_v1_a4.npz",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include failed episodes (default: success-only, matches AR pattern)",
    )
    parser.add_argument(
        "--strict-dist-filter",
        type=float,
        default=None,
        help=(
            "Option C' (2026-04-25): Skip episodes whose final dist "
            "max(dist_pos_left[-1], dist_pos_right[-1]) exceeds this threshold [m]. "
            "Recommended 0.015 (T_DIST_APPROACH 0.012 + 3mm margin) for AC BC quality. "
            "Default None (no extra filter beyond success_only)."
        ),
    )
    args = parser.parse_args()
    convert(
        args.input,
        args.output,
        success_only=not args.all,
        strict_dist_filter=args.strict_dist_filter,
    )


if __name__ == "__main__":
    main()
