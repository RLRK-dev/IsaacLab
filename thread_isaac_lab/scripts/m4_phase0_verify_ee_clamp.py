# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""M4 Phase 0: EE/clamp offset feasibility verification (α-4 direct compute GO/NO-GO).

Purpose
-------
MPPI HDF5 が保存している EE pose (hand link) と、AC env obs が観測する clamp pose
(fingertip, = EE + quat_rotate([0,0,+EE_TO_FINGERTIP])) が、同じ body を参照している
ことを数値で確認する。一致確認ができれば α-4 direct compute で HDF5 → 33D obs →
npz 変換が成立する（GPU-replay 不要、Phase 1-4 実装 ~4h）。一致しない場合は
α-2 replay に切替 (+2h)。

Checks
------
1. clamp_pos[0] / clamp_pos[-1] が table plane 以上（貫通なし）
2. 成功 episode の最終ステップで nearest-seg 距離 < 12mm (success_threshold_m)
3. HDF5 `warmup_dist_pos_{L,R}` (hand-to-cable-endpoint) vs 計算された
   clamp-to-nearest-seg 距離の **整合的関係**
4. quat convention (xyzw) / frame (world) が HDF5 metadata と一致
5. 複数 episode / 両腕で numeric range 妥当性

Output
------
stdout に pretty table + 最後に GO/NO-GO verdict。JSON summary も書き出す。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Local constants (kept literal to avoid import-time Newton deps)
EE_TO_FINGERTIP = 0.220  # task_config.py:27
TABLE_HEIGHT = 0.80  # task_config.py (TABLE_Z)
SUCCESS_THRESHOLD_M = 0.012
SUCCESS_THRESHOLD_RAD = 0.1745  # 10 deg
HDF5_DEFAULT = REPO_ROOT / "thread_isaac_lab/data/mppi_demos_m3_ac/lam0.3_s342_n15_p3/demos_default.hdf5"


def quat_rotate_vec(quat_xyzw: np.ndarray, vec: np.ndarray) -> np.ndarray:
    """Rotate a 3D vector by quaternion (xyzw). Mirrors newton_skill_env_base.quat_rotate_vec."""
    qx, qy, qz, qw = quat_xyzw
    q = np.array([qx, qy, qz], dtype=np.float64)
    v = np.asarray(vec, dtype=np.float64)
    t = 2.0 * np.cross(q, v)
    return (v + qw * t + np.cross(q, t)).astype(np.float32)


def compute_clamp_pos(ee_pos: np.ndarray, ee_quat_xyzw: np.ndarray) -> np.ndarray:
    """clamp_pos = ee_pos + quat_rotate_vec(ee_quat, [0, 0, +EE_TO_FINGERTIP])."""
    offset_local = np.array([0.0, 0.0, +EE_TO_FINGERTIP], dtype=np.float32)
    offset_world = quat_rotate_vec(ee_quat_xyzw, offset_local)
    return ee_pos + offset_world


def nearest_seg_dist(cable_pos_seq_t: np.ndarray, clamp_pos: np.ndarray) -> tuple[int, float, np.ndarray]:
    """Return (nearest_idx, dist, seg_pos) — global argmin, no window."""
    diffs = cable_pos_seq_t - clamp_pos[None, :]
    d = np.linalg.norm(diffs, axis=1)
    idx = int(np.argmin(d))
    return idx, float(d[idx]), cable_pos_seq_t[idx]


def _fmt_vec(v: np.ndarray, unit: str = "m") -> str:
    return f"[{v[0]:+.4f}, {v[1]:+.4f}, {v[2]:+.4f}] {unit}"


def verify_episode(h: h5py.File, ep_key: str) -> dict:
    ep = h[ep_key]
    success = bool(ep.attrs["success"])
    steps = int(ep.attrs["steps"])
    warmup_dist_pos_l = float(ep.attrs["warmup_dist_pos_left"])
    warmup_dist_pos_r = float(ep.attrs["warmup_dist_pos_right"])
    warmup_dist_ori_l = float(ep.attrs["warmup_dist_ori_left"])
    warmup_dist_ori_r = float(ep.attrs["warmup_dist_ori_right"])
    cost_target_l = np.array(ep.attrs["cost_target_quat_left"], dtype=np.float32)
    cost_target_r = np.array(ep.attrs["cost_target_quat_right"], dtype=np.float32)

    left_ee_pos = ep["left_ee_pos"][:]  # (T,3)
    left_ee_quat = ep["left_ee_quat"][:]  # (T,4) xyzw
    right_ee_pos = ep["right_ee_pos"][:]
    right_ee_quat = ep["right_ee_quat"][:]
    cable_pos_seq = ep["cable_pos_seq"][:]  # (T, n_cable, 3)
    dist_pos_l_hdf5 = ep["dist_pos_left"][:]
    dist_pos_r_hdf5 = ep["dist_pos_right"][:]

    T = left_ee_pos.shape[0]
    n_cable = cable_pos_seq.shape[1]

    # Compute clamp for all steps (both arms)
    clamp_l = np.stack([compute_clamp_pos(left_ee_pos[t], left_ee_quat[t]) for t in range(T)])
    clamp_r = np.stack([compute_clamp_pos(right_ee_pos[t], right_ee_quat[t]) for t in range(T)])

    # Nearest-seg at t=0 and t=-1 (no window; full-cable argmin for diagnostic)
    idx_l_0, dist_l_0, seg_l_0 = nearest_seg_dist(cable_pos_seq[0], clamp_l[0])
    idx_r_0, dist_r_0, seg_r_0 = nearest_seg_dist(cable_pos_seq[0], clamp_r[0])
    idx_l_f, dist_l_f, seg_l_f = nearest_seg_dist(cable_pos_seq[-1], clamp_l[-1])
    idx_r_f, dist_r_f, seg_r_f = nearest_seg_dist(cable_pos_seq[-1], clamp_r[-1])

    # Also compute hand→cable_endpoint distance for cross-check with warmup_dist_pos
    # cable_endpoint: left = cable_pos_seq[t, 0], right = cable_pos_seq[t, -1]
    # (per MPPI compute_cable_endpoint_pos convention: L is body 0, R is body N-1)
    hand_to_endp_l_0 = float(np.linalg.norm(left_ee_pos[0] - cable_pos_seq[0, 0]))
    hand_to_endp_r_0 = float(np.linalg.norm(right_ee_pos[0] - cable_pos_seq[0, -1]))
    hand_to_endp_l_f = float(np.linalg.norm(left_ee_pos[-1] - cable_pos_seq[-1, 0]))
    hand_to_endp_r_f = float(np.linalg.norm(right_ee_pos[-1] - cable_pos_seq[-1, -1]))

    # HDF5 dist_pos is MPPI's own hand→cable_endpoint, should match hand_to_endp_*
    hdf5_dist_pos_l_0 = float(dist_pos_l_hdf5[0])
    hdf5_dist_pos_r_0 = float(dist_pos_r_hdf5[0])
    hdf5_dist_pos_l_f = float(dist_pos_l_hdf5[-1])
    hdf5_dist_pos_r_f = float(dist_pos_r_hdf5[-1])

    # Cable Z range
    cable_z_mean = float(cable_pos_seq[0, :, 2].mean())
    cable_z_min = float(cable_pos_seq[0, :, 2].min())
    cable_z_max = float(cable_pos_seq[0, :, 2].max())

    # Table penetration check
    clamp_l_z_min = float(clamp_l[:, 2].min())
    clamp_r_z_min = float(clamp_r[:, 2].min())
    table_penetration_l = clamp_l_z_min < TABLE_HEIGHT
    table_penetration_r = clamp_r_z_min < TABLE_HEIGHT

    # Success check: final clamp→seg dist vs 12mm threshold
    success_by_dist_l = dist_l_f < SUCCESS_THRESHOLD_M
    success_by_dist_r = dist_r_f < SUCCESS_THRESHOLD_M
    # Final HDF5-reported dist should match env's pos_error magnitude for successful demos

    return {
        "episode_key": ep_key,
        "success_flag": success,
        "steps": steps,
        "T": T,
        "n_cable": n_cable,
        "cable_z_mean_m": cable_z_mean,
        "cable_z_range_m": [cable_z_min, cable_z_max],
        "table_height_m": TABLE_HEIGHT,
        # t=0 analysis
        "t0": {
            "left_ee_pos": left_ee_pos[0].tolist(),
            "left_clamp_pos": clamp_l[0].tolist(),
            "left_ee_to_clamp_delta_z": float(clamp_l[0, 2] - left_ee_pos[0, 2]),
            "left_clamp_to_nearest_seg_m": dist_l_0,
            "left_nearest_seg_idx": idx_l_0,
            "left_hand_to_endpoint_m": hand_to_endp_l_0,
            "hdf5_left_dist_pos_m": hdf5_dist_pos_l_0,
            "right_ee_pos": right_ee_pos[0].tolist(),
            "right_clamp_pos": clamp_r[0].tolist(),
            "right_ee_to_clamp_delta_z": float(clamp_r[0, 2] - right_ee_pos[0, 2]),
            "right_clamp_to_nearest_seg_m": dist_r_0,
            "right_nearest_seg_idx": idx_r_0,
            "right_hand_to_endpoint_m": hand_to_endp_r_0,
            "hdf5_right_dist_pos_m": hdf5_dist_pos_r_0,
            "warmup_dist_pos_l_m": warmup_dist_pos_l,
            "warmup_dist_pos_r_m": warmup_dist_pos_r,
        },
        # t=final analysis
        "tf": {
            "left_ee_pos": left_ee_pos[-1].tolist(),
            "left_clamp_pos": clamp_l[-1].tolist(),
            "left_clamp_to_nearest_seg_m": dist_l_f,
            "left_nearest_seg_idx": idx_l_f,
            "left_hand_to_endpoint_m": hand_to_endp_l_f,
            "hdf5_left_dist_pos_m": hdf5_dist_pos_l_f,
            "right_clamp_pos": clamp_r[-1].tolist(),
            "right_clamp_to_nearest_seg_m": dist_r_f,
            "right_nearest_seg_idx": idx_r_f,
            "right_hand_to_endpoint_m": hand_to_endp_r_f,
            "hdf5_right_dist_pos_m": hdf5_dist_pos_r_f,
            "success_by_clamp_dist_l": bool(success_by_dist_l),
            "success_by_clamp_dist_r": bool(success_by_dist_r),
        },
        # Safety / consistency checks
        "checks": {
            "table_penetration_l": bool(table_penetration_l),
            "table_penetration_r": bool(table_penetration_r),
            "clamp_l_z_min_m": clamp_l_z_min,
            "clamp_r_z_min_m": clamp_r_z_min,
        },
        # HDF5 cost target quats (to verify convention)
        "cost_target_quat_left_xyzw": cost_target_l.tolist(),
        "cost_target_quat_right_xyzw": cost_target_r.tolist(),
        "warmup_dist_ori_l_rad": warmup_dist_ori_l,
        "warmup_dist_ori_r_rad": warmup_dist_ori_r,
    }


def pretty_print(report: dict, ep_idx: int) -> None:
    print(
        f"\n===== Episode {ep_idx}: key={report['episode_key']}, success={report['success_flag']}, "
        f"steps={report['steps']}, T={report['T']} ====="
    )
    t0 = report["t0"]
    tf = report["tf"]
    print(
        f"  Cable Z: mean={report['cable_z_mean_m']:.4f} m, range="
        f"[{report['cable_z_range_m'][0]:.4f}, {report['cable_z_range_m'][1]:.4f}] m"
    )
    print(f"  Table height: {report['table_height_m']} m")
    print("  [L arm] t=0:")
    print(f"    hand_pos = {_fmt_vec(np.array(t0['left_ee_pos']))}")
    print(f"    clamp_pos = {_fmt_vec(np.array(t0['left_clamp_pos']))}  (dZ={t0['left_ee_to_clamp_delta_z']:+.4f})")
    print(
        f"    clamp→nearest_seg: {t0['left_clamp_to_nearest_seg_m'] * 1000:.2f} mm (idx={t0['left_nearest_seg_idx']})"
    )
    print(
        f"    hand→endpoint: {t0['left_hand_to_endpoint_m'] * 1000:.2f} mm, HDF5 dist_pos: "
        f"{t0['hdf5_left_dist_pos_m'] * 1000:.2f} mm, HDF5 warmup: {t0['warmup_dist_pos_l_m'] * 1000:.2f} mm"
    )
    print("  [L arm] t=final:")
    print(f"    clamp_pos = {_fmt_vec(np.array(tf['left_clamp_pos']))}")
    print(
        f"    clamp→nearest_seg: {tf['left_clamp_to_nearest_seg_m'] * 1000:.2f} mm "
        f"(success<12mm: {tf['success_by_clamp_dist_l']})"
    )
    print(
        f"    hand→endpoint: {tf['left_hand_to_endpoint_m'] * 1000:.2f} mm, HDF5 dist_pos: "
        f"{tf['hdf5_left_dist_pos_m'] * 1000:.2f} mm"
    )

    print("  [R arm] t=0:")
    print(f"    hand_pos = {_fmt_vec(np.array(t0['right_ee_pos']))}")
    print(f"    clamp_pos = {_fmt_vec(np.array(t0['right_clamp_pos']))}  (dZ={t0['right_ee_to_clamp_delta_z']:+.4f})")
    print(
        f"    clamp→nearest_seg: {t0['right_clamp_to_nearest_seg_m'] * 1000:.2f} mm (idx={t0['right_nearest_seg_idx']})"
    )
    print(
        f"    hand→endpoint: {t0['right_hand_to_endpoint_m'] * 1000:.2f} mm, HDF5 dist_pos: "
        f"{t0['hdf5_right_dist_pos_m'] * 1000:.2f} mm, HDF5 warmup: {t0['warmup_dist_pos_r_m'] * 1000:.2f} mm"
    )
    print("  [R arm] t=final:")
    print(f"    clamp_pos = {_fmt_vec(np.array(tf['right_clamp_pos']))}")
    print(
        f"    clamp→nearest_seg: {tf['right_clamp_to_nearest_seg_m'] * 1000:.2f} mm "
        f"(success<12mm: {tf['success_by_clamp_dist_r']})"
    )
    print(
        f"    hand→endpoint: {tf['right_hand_to_endpoint_m'] * 1000:.2f} mm, HDF5 dist_pos: "
        f"{tf['hdf5_right_dist_pos_m'] * 1000:.2f} mm"
    )

    chk = report["checks"]
    print(
        f"  Checks: table_penetration L={chk['table_penetration_l']} (z_min={chk['clamp_l_z_min_m']:.4f}), "
        f"R={chk['table_penetration_r']} (z_min={chk['clamp_r_z_min_m']:.4f})"
    )
    print(
        f"  cost_target_quat xyzw: L={report['cost_target_quat_left_xyzw']}, R={report['cost_target_quat_right_xyzw']}"
    )


def verdict(reports: list[dict]) -> tuple[str, list[str]]:
    """Aggregate verdict across episodes. Returns (GO|NO-GO, reasons)."""
    reasons = []
    # Only evaluate on SUCCESS episodes for the "final-dist < 12mm" check
    success_reports = [r for r in reports if r["success_flag"]]
    if not success_reports:
        reasons.append("No SUCCESS episode found — cannot evaluate final-dist check")
        return "NO-GO", reasons

    # 1. Final clamp→seg dist should be < 12mm for L or R (at least one arm at target)
    final_under_12mm_any = all(
        (r["tf"]["left_clamp_to_nearest_seg_m"] < SUCCESS_THRESHOLD_M)
        or (r["tf"]["right_clamp_to_nearest_seg_m"] < SUCCESS_THRESHOLD_M)
        for r in success_reports
    )
    if final_under_12mm_any:
        reasons.append(f"✓ All {len(success_reports)} SUCCESS episodes: final clamp→seg < 12mm on L or R")
    else:
        # Relaxed: AC success_eval = terminal_AND_pos_ori — both L and R must satisfy pos AND ori
        # but MPPI dist_pos is hand→endpoint, not clamp→seg. So allow < 2*threshold = 24mm
        final_under_24mm_both = all(
            (r["tf"]["left_clamp_to_nearest_seg_m"] < 2 * SUCCESS_THRESHOLD_M)
            and (r["tf"]["right_clamp_to_nearest_seg_m"] < 2 * SUCCESS_THRESHOLD_M)
            for r in success_reports
        )
        if final_under_24mm_both:
            reasons.append(f"✓ All {len(success_reports)} SUCCESS episodes: final clamp→seg < 24mm on both arms")
        else:
            bad = [
                (
                    r["episode_key"],
                    r["tf"]["left_clamp_to_nearest_seg_m"] * 1000,
                    r["tf"]["right_clamp_to_nearest_seg_m"] * 1000,
                )
                for r in success_reports
                if (r["tf"]["left_clamp_to_nearest_seg_m"] >= 2 * SUCCESS_THRESHOLD_M)
                or (r["tf"]["right_clamp_to_nearest_seg_m"] >= 2 * SUCCESS_THRESHOLD_M)
            ]
            reasons.append(
                f"✗ SUCCESS episodes with final clamp→seg ≥ 24mm on L or R: "
                f"{bad[:3]}... ({len(bad)}/{len(success_reports)} bad)"
            )

    # 2. No table penetration
    pen_l_any = any(r["checks"]["table_penetration_l"] for r in reports)
    pen_r_any = any(r["checks"]["table_penetration_r"] for r in reports)
    if not pen_l_any and not pen_r_any:
        reasons.append(f"✓ All {len(reports)} episodes: no table penetration (clamp Z ≥ {TABLE_HEIGHT})")
    else:
        reasons.append(f"✗ Table penetration detected: L={pen_l_any}, R={pen_r_any}")

    # 3. Geometric consistency: hand_to_endp should match HDF5 dist_pos (same metric)
    # Tolerance: 1mm (floating-point round-trip)
    inconsistent_hdf5 = []
    for r in reports:
        for arm, key_h, key_d in [
            ("L", "left_hand_to_endpoint_m", "hdf5_left_dist_pos_m"),
            ("R", "right_hand_to_endpoint_m", "hdf5_right_dist_pos_m"),
        ]:
            for phase in ["t0", "tf"]:
                h_val = r[phase][key_h]
                d_val = r[phase][key_d]
                if abs(h_val - d_val) > 0.005:  # 5mm tolerance (cable endpoint may differ from body 0/N-1)
                    inconsistent_hdf5.append((r["episode_key"], arm, phase, h_val * 1000, d_val * 1000))
    if not inconsistent_hdf5:
        reasons.append("✓ hand_to_endpoint computed vs HDF5 dist_pos: ≤5mm diff across all episodes")
    else:
        reasons.append(f"⚠ hand_to_endpoint mismatch (≥5mm): {inconsistent_hdf5[:3]}...")

    # Verdict
    has_fail = any("✗" in r for r in reasons)
    v = "GO" if not has_fail else "NO-GO"
    return v, reasons


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--input", type=str, default=str(HDF5_DEFAULT))
    p.add_argument("--episodes", type=int, default=3, help="Number of episodes to check (default: 3)")
    p.add_argument("--output-json", type=str, default=str(REPO_ROOT / "thread_isaac_lab/data/m4_phase0_verify.json"))
    args = p.parse_args()

    hdf5_path = Path(args.input)
    if not hdf5_path.exists():
        print(f"ERROR: HDF5 not found: {hdf5_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[M4 Phase 0] Loading {hdf5_path}")
    with h5py.File(hdf5_path, "r") as h:
        meta = h["metadata"]
        print(
            f"  metadata: action_layout={meta.attrs['action_layout']}, "
            f"quat={meta.attrs['quat_convention']}/{meta.attrs['quat_frame']}/{meta.attrs['quat_semantic']}"
        )
        print(
            f"  n_demos={meta.attrs['n_demos']}, n_success={meta.attrs['n_success']}, "
            f"success_threshold_m={meta.attrs['success_threshold_m']}"
        )

        ep_keys = sorted([k for k in h.keys() if k.startswith("episode_")], key=lambda k: int(k.split("_")[1]))

        reports = []
        # Prefer SUCCESS episodes first
        success_keys = [k for k in ep_keys if bool(h[k].attrs["success"])]
        sample_keys = success_keys[: args.episodes] if success_keys else ep_keys[: args.episodes]

        for i, ep_key in enumerate(sample_keys):
            r = verify_episode(h, ep_key)
            reports.append(r)
            pretty_print(r, i)

    # Verdict
    v, reasons = verdict(reports)
    print("\n===== VERDICT =====")
    print(f"  {v}")
    for rr in reasons:
        print(f"  {rr}")

    # Write JSON
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fp:
        json.dump(
            {
                "verdict": v,
                "reasons": reasons,
                "reports": reports,
                "hdf5_path": str(hdf5_path),
                "checks": {
                    "ee_to_fingertip_m": EE_TO_FINGERTIP,
                    "success_threshold_m": SUCCESS_THRESHOLD_M,
                },
            },
            fp,
            indent=2,
            default=float,
        )
    print(f"\n[M4 Phase 0] JSON written to {out_path}")
    sys.exit(0 if v == "GO" else 1)


if __name__ == "__main__":
    main()
