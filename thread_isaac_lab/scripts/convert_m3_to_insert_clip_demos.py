# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Convert M3-IC DA-MPPI HDF5 demos to InsertIntoClip-compatible npz for DAPG BC.

Adapted from ``convert_m3_to_ac_demos.py`` (AC M4 α-4 direct compute) and
``convert_m3_to_grip_demos.py`` (Grip option B). Differs from both because IC
env stores a fully-populated 45D observation in groove-relative coordinates
(see ``newton_insert_clip_env.py:1111-1184``), and the M3-IC generator already
records this exact tensor in HDF5 ``episode_*/obs`` (``shape=(T, 45)``,
``dtype=float32``). We therefore *pass the HDF5 obs through directly* and
avoid re-computing it here, which both removes a bug surface and ensures the
training-time obs distribution exactly matches collection-time.

Differences vs AC/Grip converters
---------------------------------
- **Obs reconstruction skipped.** AC/Grip rebuild a 42D obs from stored EE
  poses + cable_pos_seq because their generators only store EE/cable. IC
  generator stores the env's native 45D obs as ``demo["obs"]``
  (``generate_demos_mppi_m3_insert_clip.py:1017,1109``). We read that array
  unchanged.
- **L1 quat fix not applied; explicit w>=0 normalization done in converter.**
  IC obs has quats at ``[3:7]`` (R clamp) and ``[10:14]`` (L clamp). The
  default ``train_common.py`` L1 fix indices ``[3, 11, 19, 26]`` are correct
  for AC/AR/Grip but **wrong** for IC (11 splits L_quat, 19 lands in the
  cable-groove orientation axis-angle, 26 lands in cable shape coordinates),
  so we bypass it. The IC env's ``extract_clamp_pose``
  (``newton_skill_env_base.py:267-310``) applies ``normalize_quat_w_positive``
  first, but its second step ``temporal_quat_consistency`` may flip the sign
  back to ``w<0`` near the ``w≈0`` singularity (180° rotation), leaking
  mixed-sign quats into the HDF5 obs (empirical: K=4 smoke ep0 50%, ep1
  5.5%). Since ``q ≡ -q`` in rotation algebra, we flip ``-q → q`` in
  ``_check_obs_finite_and_quats`` for both clamp quat slots. This matches
  the AC converter pattern (``convert_m3_to_ac_demos.py:89-90``), is
  mathematically lossless, and produces a deduplicated training distribution.
- **Action layout pass-through.** HDF5 stores R-first 12D actions
  (``IC_ACTION_LAYOUT="R-first"`` at ``generate_demos_mppi_m3_insert_clip.py:145``)
  matching IC env's native 12D action. No remap.
- **Per-mode handling.** M3-IC has approach + insert modes with different
  success thresholds (``IC_T_DIST_APPROACH=12mm`` vs ``IC_T_GROOVE=3mm``) and
  different terminal evaluations (terminal vs sustained-K10). We respect the
  ``mode`` metadata attribute and forward it through; success filtering uses
  the per-episode ``success`` flag, which is computed per-mode in the
  generator.

BC pairing convention (inherited from AR/AC converters)
-------------------------------------------------------
HDF5 ``obs[t]`` is the post-action state recorded after ``action_delta[t]``
was applied (``generate_demos_mppi_m3_insert_clip.py:993-1017``). For BC we
want pre-action state. Pairs:

  obs_bc[i] = obs[i]            # post-state of step i (= pre-state of step i+1)
  act_bc[i] = action_delta[i+1] # action taken FROM that state

This drops the first action (at ``i=0`` with no recorded prior obs) and
yields ``T-1`` pairs per episode. **Note**: the M3-IC generator pushes
``traj_obs.append(obs_np.copy())`` *after* ``traj_actions.append(...)`` so
in fact ``obs[t]`` and ``actions[t]`` are recorded in the same loop
iteration, making this the post-state of the *current* step. Pairing
``obs[i] -> actions[i+1]`` therefore matches AR/AC convention.

Known limitation: cable-position fixedness
------------------------------------------
M3-IC env collects demos with cable in a fixed pose at reset (no XY
randomization). Demos collected here will not generalize to the
randomized-cable env if Option C' (CC#2 active) lands cable randomization
into IC. Production demo regeneration is the mitigation; this converter
itself is invariant to that change.

Usage
-----
    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/convert_m3_to_insert_clip_demos.py \\
        --input thread_isaac_lab/data/mppi_demos_m3_ic/lam0.3_seed42/demos_approach_default.hdf5 \\
        --input thread_isaac_lab/data/mppi_demos_m3_ic/lam0.3_seed142/demos_approach_default.hdf5 \\
        --output thread_isaac_lab/data/bc_demos/insert_clip_demos_mppi_v1_approach.npz \\
        --mode approach

Multi-file aggregation supported via repeat ``--input``.
"""

from __future__ import annotations

import argparse
import os

import h5py
import numpy as np

# IC env obs/action dims (newton_insert_clip_env.py :247, :1551).
OBS_DIM = 45
ACTION_DIM = 12

# Quat field starts in IC obs (env :1167-1171). [3:7]=R clamp, [10:14]=L clamp.
_IC_QUAT_STARTS = (3, 10)


def _check_obs_finite_and_quats(ep_obs: np.ndarray, ep_name: str) -> tuple[bool, str]:
    """Sanity check obs: finite values + flip negative-w quats in place.

    The IC env's ``extract_clamp_pose`` (``newton_skill_env_base.py:267-310``)
    applies ``normalize_quat_w_positive`` then ``temporal_quat_consistency``;
    the latter may flip the sign back to ``w<0`` when the rotation passes the
    ``w≈0`` (180°) singularity and ``-q`` is closer to the previous-frame
    quat. This leaks sign-flipped quats into ``obs[:, 3:7]`` (R clamp) and
    ``obs[:, 10:14]`` (L clamp). Since ``q ≡ -q`` for rotation (quaternion
    double cover), we flip ``-q → q`` in place to deduplicate the BC
    distribution (matches AC converter, ``convert_m3_to_ac_demos.py:89-90``).

    Returns ``(ok, msg)``. ``ok=False`` only on non-finite values. When
    ``msg`` is non-empty with ``ok=True`` it reports the flip count.
    Modifies ``ep_obs`` in place when ``w<0`` quats are found.
    """
    if not np.isfinite(ep_obs).all():
        bad = int((~np.isfinite(ep_obs)).sum())
        return False, f"{bad} non-finite values in obs"
    n_flipped_total = 0
    per_slot = []
    for qs in _IC_QUAT_STARTS:
        w = ep_obs[:, qs + 3]
        neg_mask = w < 0
        n_neg = int(neg_mask.sum())
        if n_neg > 0:
            ep_obs[neg_mask, qs:qs + 4] = -ep_obs[neg_mask, qs:qs + 4]
            n_flipped_total += n_neg
            per_slot.append(f"obs[:, {qs}:{qs + 4}]={n_neg}")
    if n_flipped_total > 0:
        return True, (
            f"flipped {n_flipped_total} quats to canonical w>=0 "
            f"({', '.join(per_slot)}; env temporal_quat_consistency artefact, q ≡ -q)"
        )
    return True, ""


def convert(
    input_paths: list[str],
    output_path: str,
    success_only: bool = True,
    strict_dist_filter: float | None = None,
    mode_filter: str | None = None,
) -> None:
    """Convert one or more M3-IC HDF5 files to a single npz.

    Args:
        input_paths: HDF5 paths from ``generate_demos_mppi_m3_insert_clip.py``.
        output_path: Output npz path; created if its directory does not exist.
        success_only: If True (default), keep only ``g.attrs["success"]==True``.
        strict_dist_filter: If not None, additionally require
            ``max(dist_pos_left[-1], dist_pos_right[-1], seg_dist_groove[-1]) <=``
            this threshold [m]. Use ``IC_T_DIST_APPROACH`` (12mm) +
            ~3mm margin = 0.015 for tighter BC quality. ``None`` = no extra
            filter beyond ``success_only``.
        mode_filter: If not None (one of ``"approach"``, ``"insert"``), reject
            episodes whose source HDF5 metadata ``mode`` does not match.
            Useful when aggregating mixed-mode files but emitting a
            mode-specific npz.
    """
    obs_list: list[np.ndarray] = []
    act_list: list[np.ndarray] = []
    ep_lens: list[int] = []
    ep_success: list[bool] = []
    ep_keys_taken: list[str] = []
    ep_modes: list[str] = []
    n_skipped = 0
    n_strict_reject = 0
    n_mode_reject = 0
    n_total_episodes = 0

    aggregated_metadata: dict = {}

    for input_path in input_paths:
        with h5py.File(input_path, "r") as f:
            meta = f["metadata"]
            layout = meta.attrs["action_layout"]
            if layout != "R-first":
                raise ValueError(
                    f"{input_path}: action_layout={layout!r} — IC converter requires R-first "
                    "(M3-IC native, see generate_demos_mppi_m3_insert_clip.py:145). "
                    "If you have an L-first IC HDF5, regenerate with the current generator."
                )
            file_mode = str(meta.attrs.get("mode", "unknown"))
            if mode_filter is not None and file_mode != mode_filter:
                print(
                    f"[CONV] Skipping {input_path}: mode={file_mode!r} != filter={mode_filter!r}"
                )
                continue

            ic_version = meta.attrs.get("ic_version", "unknown")
            architecture = meta.attrs.get("architecture", "unknown")
            mppi_pos_scale = float(meta.attrs.get("mppi_pos_action_scale", np.nan))
            mppi_rot_scale = float(meta.attrs.get("mppi_rot_action_scale", np.nan))
            print(
                f"[CONV] Input: {input_path}  (ic_version={ic_version}, "
                f"mode={file_mode}, pos_scale={mppi_pos_scale}, "
                f"rot_scale={mppi_rot_scale}, arch={architecture!r})"
            )

            # Capture metadata from first file for npz attrs (informational).
            if not aggregated_metadata:
                aggregated_metadata = {
                    "ic_version": ic_version,
                    "mode": file_mode,
                    "mppi_pos_action_scale": mppi_pos_scale,
                    "mppi_rot_action_scale": mppi_rot_scale,
                    "action_layout": layout,
                }

            episode_names = sorted(
                [k for k in f.keys() if k.startswith("episode_")],
                key=lambda s: int(s.split("_")[1]),
            )
            n_total_episodes += len(episode_names)
            print(f"[CONV]   episodes: {len(episode_names)} (mode={file_mode})")

            for ep_name in episode_names:
                g = f[ep_name]
                if "obs" not in g:
                    print(f"[CONV]   WARN {ep_name}: missing obs dataset — SKIP")
                    n_skipped += 1
                    continue
                if "action_delta" not in g:
                    print(f"[CONV]   WARN {ep_name}: missing action_delta — SKIP")
                    n_skipped += 1
                    continue
                success = bool(g.attrs.get("success", False))
                if success_only and not success:
                    n_skipped += 1
                    continue

                # Optional strict final-state filter (mirrors AC converter
                # Option C' protection vs loose generator success threshold).
                if strict_dist_filter is not None:
                    needed = ("dist_pos_left", "dist_pos_right", "seg_dist_groove")
                    missing = [k for k in needed if k not in g]
                    if missing:
                        print(
                            f"[CONV]   WARN {ep_name}: missing {missing} for strict filter — SKIP"
                        )
                        n_skipped += 1
                        continue
                    final_dl = float(g["dist_pos_left"][()][-1])
                    final_dr = float(g["dist_pos_right"][()][-1])
                    final_sg = float(g["seg_dist_groove"][()][-1])
                    worst = max(final_dl, final_dr, final_sg)
                    if worst > strict_dist_filter:
                        print(
                            f"[CONV]   {ep_name}: strict filter REJECT "
                            f"(L={final_dl * 1000:.1f}mm R={final_dr * 1000:.1f}mm "
                            f"seg={final_sg * 1000:.1f}mm > "
                            f"{strict_dist_filter * 1000:.1f}mm)"
                        )
                        n_skipped += 1
                        n_strict_reject += 1
                        continue

                # Pass-through obs (45D groove-relative, env-native).
                obs_full = np.asarray(g["obs"][()], dtype=np.float32)
                actions = np.asarray(g["action_delta"][()], dtype=np.float32)

                if obs_full.ndim != 2 or obs_full.shape[1] != OBS_DIM:
                    print(
                        f"[CONV]   WARN {ep_name}: obs shape {obs_full.shape} "
                        f"!= (T, {OBS_DIM}) — SKIP"
                    )
                    n_skipped += 1
                    continue
                if actions.ndim != 2 or actions.shape[1] != ACTION_DIM:
                    print(
                        f"[CONV]   WARN {ep_name}: action shape {actions.shape} "
                        f"!= (T, {ACTION_DIM}) — SKIP"
                    )
                    n_skipped += 1
                    continue
                T = obs_full.shape[0]
                if actions.shape[0] != T:
                    print(
                        f"[CONV]   WARN {ep_name}: length mismatch "
                        f"obs={T} act={actions.shape[0]} — SKIP"
                    )
                    n_skipped += 1
                    continue
                if T < 2:
                    print(f"[CONV]   {ep_name}: T={T} < 2 — SKIP (need >=2 for BC pairing)")
                    n_skipped += 1
                    continue

                # BC pairing (matches AC/AR convention). obs_bc = obs[0..T-2],
                # act_bc = actions[1..T-1]. n_pairs = T-1.
                n_pairs = T - 1
                ep_obs = obs_full[:n_pairs].astype(np.float32, copy=False)
                ep_act = actions[1:T].astype(np.float32, copy=False)

                ok, msg = _check_obs_finite_and_quats(ep_obs, ep_name)
                if not ok:
                    print(f"[CONV]   WARN {ep_name}: {msg} — SKIP")
                    n_skipped += 1
                    continue
                if msg:
                    print(f"[CONV]   {ep_name}: {msg}")
                if not np.isfinite(ep_act).all():
                    bad = int((~np.isfinite(ep_act)).sum())
                    print(f"[CONV]   WARN {ep_name}: {bad} non-finite values in act — SKIP")
                    n_skipped += 1
                    continue

                obs_list.append(ep_obs)
                act_list.append(ep_act)
                ep_lens.append(n_pairs)
                ep_success.append(success)
                ep_modes.append(file_mode)
                ep_keys_taken.append(
                    f"{os.path.basename(os.path.dirname(input_path))}/{ep_name}"
                )
                print(
                    f"[CONV]   {ep_name}: T={T} pairs={n_pairs} "
                    f"success={success} mode={file_mode}"
                )

    if mode_filter is not None and n_mode_reject > 0:
        print(f"[CONV] mode filter rejected {n_mode_reject} files (mode != {mode_filter!r})")

    if not obs_list:
        raise RuntimeError(
            f"No usable episodes after filtering. "
            f"Total scanned={n_total_episodes}, skipped={n_skipped} "
            f"(strict_reject={n_strict_reject})."
        )

    obs_all = np.concatenate(obs_list, axis=0)
    act_all = np.concatenate(act_list, axis=0)
    ep_lens_arr = np.array(ep_lens, dtype=np.int32)
    ep_success_arr = np.array(ep_success, dtype=bool)
    ep_modes_arr = np.array(ep_modes, dtype=object)

    # --- Validation gates --------------------------------------------------
    total = obs_all.shape[0]
    act_sat = float(np.mean(np.abs(act_all) > 0.99))
    # IC R-first 12D layout: [0:3] R_pos, [3:6] R_ori, [6:9] L_pos, [9:12] L_ori.
    r_rms = float(np.sqrt(np.mean(act_all[:, 0:6] ** 2)))
    l_rms = float(np.sqrt(np.mean(act_all[:, 6:12] ** 2)))
    obs_mean = obs_all.mean(axis=0)
    obs_std = obs_all.std(axis=0)
    # IC obs[14:17]=cable-groove pos error, [20]=scalar dist.
    cable_pos_err_rms = float(np.sqrt(np.mean(np.sum(obs_all[:, 14:17] ** 2, axis=1))))
    cable_dist_mean = float(obs_mean[20])
    r_clamp_dist_rms = float(np.sqrt(np.mean(np.sum(obs_all[:, 0:3] ** 2, axis=1))))
    l_clamp_dist_rms = float(np.sqrt(np.mean(np.sum(obs_all[:, 7:10] ** 2, axis=1))))

    print("\n=== VALIDATION ===")
    print(f"  total transitions: {total}")
    print(
        f"  episodes kept: {len(ep_lens)} / {n_total_episodes} "
        f"(skipped {n_skipped})"
    )
    if strict_dist_filter is not None:
        print(
            f"  strict_dist_filter: {strict_dist_filter * 1000:.1f}mm, "
            f"rejected {n_strict_reject} eps by this filter"
        )
    print(f"  obs shape: {obs_all.shape}  act shape: {act_all.shape}")
    print(f"  action saturation (|a|>0.99): {act_sat:.3%}  (gate <10%)")
    print(f"  R-arm action RMS [0:6]: {r_rms:.3f}")
    print(f"  L-arm action RMS [6:12]: {l_rms:.3f}")
    print(f"  obs[0:3] R clamp - groove RMS: {r_clamp_dist_rms:.4f} m")
    print(f"  obs[7:10] L clamp - groove RMS: {l_clamp_dist_rms:.4f} m")
    print(f"  obs[14:17] cable-groove err RMS: {cable_pos_err_rms:.4f} m")
    print(f"  obs[20] scalar dist mean: {cable_dist_mean:.4f} m")
    print(
        f"  obs[3:7] R quat mean: w_mean={obs_mean[6]:+.3f} "
        f"w_std={obs_std[6]:.3f} (expect w>=0)"
    )
    print(
        f"  obs[10:14] L quat mean: w_mean={obs_mean[13]:+.3f} "
        f"w_std={obs_std[13]:.3f} (expect w>=0)"
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    source_tag = (
        f"m3_ic_{aggregated_metadata.get('mode', 'unknown')}_v1 "
        f"(strategy=hdf5-obs-passthrough; ic_version="
        f"{aggregated_metadata.get('ic_version', 'unknown')})"
    )
    np.savez(
        output_path,
        obs=obs_all.astype(np.float32),
        actions=act_all.astype(np.float32),
        episode_lengths=ep_lens_arr,
        episode_success=ep_success_arr,
        # Optional metadata: not consumed by train_common, but useful for
        # downstream forensic checks (e.g. mode mix verification).
        episode_modes=ep_modes_arr,
        source=source_tag,
    )
    print(f"\n[CONV] Saved → {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=str,
        action="append",
        required=True,
        help=(
            "M3-IC HDF5 path with episode_*/obs and episode_*/action_delta "
            "(repeat for multi-file aggregation)"
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default="thread_isaac_lab/data/bc_demos/insert_clip_demos_mppi_v1_approach.npz",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include failed episodes (default: success-only, matches AR/AC pattern)",
    )
    parser.add_argument(
        "--strict-dist-filter",
        type=float,
        default=None,
        help=(
            "Skip episodes whose final dist max(dist_pos_left[-1], "
            "dist_pos_right[-1], seg_dist_groove[-1]) exceeds this threshold [m]. "
            "Recommended 0.015 (T_DIST_APPROACH 0.012 + 3mm margin) for "
            "approach-mode BC quality, or 0.005 for insert-mode "
            "(T_GROOVE 0.003 + 2mm). Default None (no extra filter)."
        ),
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=("approach", "insert"),
        help=(
            "If set, reject HDF5 files whose metadata.mode != this. Use to "
            "emit a mode-specific npz when aggregating mixed-mode files."
        ),
    )
    args = parser.parse_args()
    convert(
        args.input,
        args.output,
        success_only=not args.all,
        strict_dist_filter=args.strict_dist_filter,
        mode_filter=args.mode,
    )


if __name__ == "__main__":
    main()
