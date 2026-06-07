#!/usr/bin/env python3
"""Plan and Visualize Trajectory for Clip Routing (P1-P11).

No Isaac Sim required — uses matplotlib + franka_analytical_ik only.
Computes all waypoints, checks IK feasibility, and generates 3D plots.
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from thread_isaac_lab.configs.task_config import (
    ROBOT_LEFT_BASE, ROBOT_RIGHT_BASE, ROBOT_BASE_QUAT_WXYZ,
    GRIPPER_DOWN_QUAT_WXYZ,
    PHASE2_LEFT_JOINTS, PHASE2_RIGHT_JOINTS,
    TABLE_HEIGHT,
    CABLE_X, CABLE_Z, CABLE_SEG17_Y, CABLE_SEG19_Y,
    CLIP1_X, CLIP1_Y, CLIP1_Z,
    CLIP2_X, CLIP2_Y, CLIP2_Z,
    FINGERTIP_OFFSET,
)
from thread_isaac_lab.scripts.franka_analytical_ik import (
    solve_ik_best, forward_kinematics,
)
from scipy.spatial.transform import Rotation as R

# ---------------------------------------------------------------------------
# Constants (mirrored from test_clip_routing.py)
# ---------------------------------------------------------------------------
CLIP_APPROACH_HEIGHT = 0.05
CLIP_PUSH_DEPTH = 0.020
CLIP_TOTAL_HEIGHT = 0.030  # base(5mm) + groove(15mm) + guide(10mm)
LIFT_Z = 0.070  # 70mm lift

CLIP1_POS = np.array([CLIP1_X, CLIP1_Y, CLIP1_Z])
CLIP2_POS = np.array([CLIP2_X, CLIP2_Y, CLIP2_Z])

# P1 (grasp) EE positions — computed from PHASE2 joints via FK
BASE_L = np.array(ROBOT_LEFT_BASE)
BASE_R = np.array(ROBOT_RIGHT_BASE)
QUAT_BASE = np.array(ROBOT_BASE_QUAT_WXYZ)
QUAT_GRIP = np.array(GRIPPER_DOWN_QUAT_WXYZ)


def fk(joints, base):
    """Forward kinematics: joint angles → world EE position."""
    T_base_ee = forward_kinematics(np.array(joints))
    quat_xyzw = [QUAT_BASE[1], QUAT_BASE[2], QUAT_BASE[3], QUAT_BASE[0]]
    R_base = R.from_quat(quat_xyzw).as_matrix()
    T_world = np.eye(4)
    T_world[:3, :3] = R_base
    T_world[:3, 3] = base
    T_world_ee = T_world @ T_base_ee
    return T_world_ee[:3, 3]


def check_ik(pos, base, label=""):
    """Check IK feasibility. Returns (success, margin_deg)."""
    ok, joints, margin = solve_ik_best(
        np.array(pos), np.array(base), QUAT_BASE, QUAT_GRIP, q7_steps=100
    )
    tag = f" [{label}]" if label else ""
    if ok:
        print(f"  IK OK{tag}: pos=({pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f}) margin={margin:.1f}°")
    else:
        print(f"  IK FAIL{tag}: pos=({pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f})")
    return ok, margin


def build_waypoints():
    """Build P1-P11 waypoint sequence for Left and Right EE.

    Returns list of (phase_label, ee_left, ee_right, description).
    """
    # P1: Grasp position (from FK of PHASE2 joints)
    p1_l = fk(PHASE2_LEFT_JOINTS, BASE_L)
    p1_r = fk(PHASE2_RIGHT_JOINTS, BASE_R)
    print(f"P1 (grasp) L=({p1_l[0]:.4f},{p1_l[1]:.4f},{p1_l[2]:.4f})")
    print(f"P1 (grasp) R=({p1_r[0]:.4f},{p1_r[1]:.4f},{p1_r[2]:.4f})")

    # P2: Lift +70mm
    p2_l = p1_l.copy(); p2_l[2] += LIFT_Z
    p2_r = p1_r.copy(); p2_r[2] += LIFT_Z

    # P3: Move to clip1 (midpoint shift, maintain arm separation)
    mid_p2 = (p2_l + p2_r) / 2.0
    dx = CLIP1_POS[0] - mid_p2[0]
    dy = CLIP1_POS[1] - mid_p2[1]
    target_z_p3 = CLIP1_POS[2] + CLIP_APPROACH_HEIGHT + 0.05
    p3_l = np.array([p2_l[0] + dx, p2_l[1] + dy, target_z_p3])
    p3_r = np.array([p2_r[0] + dx, p2_r[1] + dy, target_z_p3])

    # P4: Lower to clip1 V-guide level
    clip_top_z = CLIP1_POS[2] + CLIP_TOTAL_HEIGHT + 0.005
    p4_l = p3_l.copy(); p4_l[2] = clip_top_z
    p4_r = p3_r.copy(); p4_r[2] = clip_top_z

    # P5: Release RIGHT arm (LEFT holds, RIGHT retracts up slightly)
    p5_l = p4_l.copy()  # hold
    p5_r = p4_r.copy(); p5_r[2] += 0.03  # slight retract up

    # P6: RIGHT arm pushes at clip1 center
    clip1_groove_bottom_z = CLIP1_POS[2] + 0.005  # base_height
    push_target_z = clip1_groove_bottom_z + FINGERTIP_OFFSET + 0.005
    p6_l = p5_l.copy()  # hold
    p6_r_start = p5_r.copy()
    p6_r_end = np.array([CLIP1_POS[0], CLIP1_POS[1], push_target_z])

    # P7: Regrasp — RIGHT arm moves to clip2 approach, LEFT releases
    p7_l = p6_l.copy(); p7_l[2] += 0.03  # released, retract
    p7_r = np.array([CLIP2_POS[0], CLIP2_POS[1],
                     CLIP2_POS[2] + CLIP_APPROACH_HEIGHT + 0.05])

    # P8: Move to clip2 (RIGHT holds near clip2, LEFT moves to clip2 approach)
    # After regrasp, RIGHT is above clip2, LEFT needs to move too
    mid_p7 = (p7_l + p7_r) / 2.0
    dx2 = CLIP2_POS[0] - mid_p7[0]
    dy2 = CLIP2_POS[1] - mid_p7[1]
    target_z_p8 = CLIP2_POS[2] + CLIP_APPROACH_HEIGHT + 0.05
    p8_l = np.array([p7_l[0] + dx2, p7_l[1] + dy2, target_z_p8])
    p8_r = np.array([p7_r[0] + dx2, p7_r[1] + dy2, target_z_p8])

    # P9: Lower to clip2 V-guide level
    clip2_top_z = CLIP2_POS[2] + CLIP_TOTAL_HEIGHT + 0.005
    p9_l = p8_l.copy(); p9_l[2] = clip2_top_z
    p9_r = p8_r.copy(); p9_r[2] = clip2_top_z

    # P10: Release LEFT arm (RIGHT holds)
    p10_l = p9_l.copy(); p10_l[2] += 0.03
    p10_r = p9_r.copy()  # hold

    # P11: LEFT arm pushes at clip2 center
    clip2_groove_bottom_z = CLIP2_POS[2] + 0.005
    push2_target_z = clip2_groove_bottom_z + FINGERTIP_OFFSET + 0.005
    p11_l_end = np.array([CLIP2_POS[0], CLIP2_POS[1], push2_target_z])
    p11_r = p10_r.copy()  # hold

    waypoints = [
        ("P1", p1_l, p1_r, "Grasp"),
        ("P2", p2_l, p2_r, "Lift +70mm"),
        ("P3", p3_l, p3_r, "Move above Clip1"),
        ("P4", p4_l, p4_r, "Lower to Clip1"),
        ("P5", p5_l, p5_r, "Release R"),
        ("P6s", p6_l, p6_r_start, "Push start"),
        ("P6e", p6_l, p6_r_end, "Push end (R→Clip1)"),
        ("P7", p7_l, p7_r, "Regrasp (R→Clip2)"),
        ("P8", p8_l, p8_r, "Move above Clip2"),
        ("P9", p9_l, p9_r, "Lower to Clip2"),
        ("P10", p10_l, p10_r, "Release L"),
        ("P11", p11_l_end, p11_r, "Push end (L→Clip2)"),
    ]

    return waypoints


def check_all_ik(waypoints):
    """Check IK at every waypoint. Returns list of (label, l_ok, r_ok, l_margin, r_margin)."""
    results = []
    print("\n" + "=" * 60)
    print("IK Feasibility Check")
    print("=" * 60)
    for label, ee_l, ee_r, desc in waypoints:
        print(f"\n--- {label}: {desc} ---")
        l_ok, l_m = check_ik(ee_l, BASE_L, f"L {label}")
        r_ok, r_m = check_ik(ee_r, BASE_R, f"R {label}")
        results.append((label, l_ok, r_ok, l_m, r_m))
    return results


def interpolate_path(waypoints, n_interp=20):
    """Linear interpolation between consecutive waypoints."""
    left_path = []
    right_path = []
    labels_at = []  # (index, label)
    idx = 0
    for i, (label, ee_l, ee_r, desc) in enumerate(waypoints):
        if i == 0:
            left_path.append(ee_l)
            right_path.append(ee_r)
            labels_at.append((idx, label))
            idx += 1
        else:
            prev_l = waypoints[i - 1][1]
            prev_r = waypoints[i - 1][2]
            for t in np.linspace(0, 1, n_interp + 1)[1:]:
                left_path.append(prev_l + (ee_l - prev_l) * t)
                right_path.append(prev_r + (ee_r - prev_r) * t)
                idx += 1
            labels_at.append((idx - 1, label))

    return np.array(left_path), np.array(right_path), labels_at


def plot_all(waypoints, ik_results, output_dir):
    """Generate 3 trajectory plots."""
    os.makedirs(output_dir, exist_ok=True)

    left_path, right_path, labels_at = interpolate_path(waypoints, n_interp=15)

    # Waypoint markers
    wp_l = np.array([w[1] for w in waypoints])
    wp_r = np.array([w[2] for w in waypoints])
    wp_labels = [w[0] for w in waypoints]

    # IK fail markers
    fail_l = [wp_l[i] for i, (_, lok, _, _, _) in enumerate(ik_results) if not lok]
    fail_r = [wp_r[i] for i, (_, _, rok, _, _) in enumerate(ik_results) if not rok]

    # Cable initial position (10 segments along Y)
    cable_ys = np.linspace(CABLE_SEG17_Y, CABLE_SEG19_Y, 10)
    cable_xs = np.full_like(cable_ys, CABLE_X)
    cable_zs = np.full_like(cable_ys, CABLE_Z)

    # Table surface corners
    table_x = [0.0, 0.6, 0.6, 0.0, 0.0]
    table_y = [-0.6, -0.6, 0.6, 0.6, -0.6]
    table_z = [TABLE_HEIGHT] * 5

    # Colors for phases
    phase_colors = {
        "P1": "#2196F3", "P2": "#4CAF50", "P3": "#FF9800",
        "P4": "#E91E63", "P5": "#9C27B0", "P6s": "#795548",
        "P6e": "#795548", "P7": "#607D8B", "P8": "#FF5722",
        "P9": "#00BCD4", "P10": "#CDDC39", "P11": "#F44336",
    }

    # ===== (a) 3D Plot =====
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_title("Clip Routing Trajectory (3D)", fontsize=14, fontweight="bold")

    # Left path (blue), Right path (red)
    ax.plot(left_path[:, 0], left_path[:, 1], left_path[:, 2],
            "b-", linewidth=1.5, alpha=0.7, label="Left EE")
    ax.plot(right_path[:, 0], right_path[:, 1], right_path[:, 2],
            "r-", linewidth=1.5, alpha=0.7, label="Right EE")

    # Waypoint markers with labels
    for i, lbl in enumerate(wp_labels):
        ax.scatter(*wp_l[i], c="blue", s=40, zorder=5, edgecolors="black", linewidths=0.5)
        ax.scatter(*wp_r[i], c="red", s=40, zorder=5, edgecolors="black", linewidths=0.5)
        ax.text(wp_l[i][0], wp_l[i][1], wp_l[i][2] + 0.01, lbl,
                fontsize=7, color="blue", ha="center")
        ax.text(wp_r[i][0], wp_r[i][1], wp_r[i][2] + 0.01, lbl,
                fontsize=7, color="red", ha="center")

    # IK fail markers
    for fp in fail_l:
        ax.scatter(*fp, c="red", s=100, marker="x", linewidths=2, zorder=10)
    for fp in fail_r:
        ax.scatter(*fp, c="red", s=100, marker="x", linewidths=2, zorder=10)

    # Cable
    ax.plot(cable_xs, cable_ys, cable_zs, "y-o", linewidth=3, markersize=4,
            label="Cable (init)", alpha=0.8)

    # Clips
    ax.scatter(*CLIP1_POS, c="green", s=120, marker="^", label="Clip1", zorder=5)
    ax.scatter(*CLIP2_POS, c="lime", s=120, marker="^", label="Clip2", zorder=5)
    ax.text(*CLIP1_POS + np.array([0, 0, 0.02]), "Clip1", fontsize=9, color="green")
    ax.text(*CLIP2_POS + np.array([0, 0, 0.02]), "Clip2", fontsize=9, color="green")

    # Robot bases
    ax.scatter(*BASE_L, c="black", s=80, marker="s", label="L Base", zorder=5)
    ax.scatter(*BASE_R, c="gray", s=80, marker="s", label="R Base", zorder=5)
    ax.text(*BASE_L + np.array([0, 0, 0.02]), "L Base", fontsize=8)
    ax.text(*BASE_R + np.array([0, 0, 0.02]), "R Base", fontsize=8)

    # Table surface
    ax.plot(table_x, table_y, table_z, "k-", alpha=0.3, linewidth=0.5)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_xlim(0.0, 0.7)
    ax.set_ylim(-0.6, 0.6)
    ax.set_zlim(0.6, 1.4)

    path_3d = os.path.join(output_dir, "trajectory_3d.png")
    fig.savefig(path_3d, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {path_3d}")
    plt.close(fig)

    # ===== (b) XY Top-down =====
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Clip Routing — Top View (XY)", fontsize=14, fontweight="bold")
    ax.set_aspect("equal")

    ax.plot(left_path[:, 1], left_path[:, 0], "b-", linewidth=1.5, alpha=0.7, label="Left EE")
    ax.plot(right_path[:, 1], right_path[:, 0], "r-", linewidth=1.5, alpha=0.7, label="Right EE")

    for i, lbl in enumerate(wp_labels):
        ax.scatter(wp_l[i][1], wp_l[i][0], c="blue", s=30, zorder=5,
                   edgecolors="black", linewidths=0.5)
        ax.scatter(wp_r[i][1], wp_r[i][0], c="red", s=30, zorder=5,
                   edgecolors="black", linewidths=0.5)
        ax.annotate(lbl, (wp_l[i][1], wp_l[i][0]), fontsize=7, color="blue",
                    textcoords="offset points", xytext=(5, 5))
        ax.annotate(lbl, (wp_r[i][1], wp_r[i][0]), fontsize=7, color="red",
                    textcoords="offset points", xytext=(5, -10))

    # Cable
    ax.plot(cable_ys, cable_xs, "y-o", linewidth=3, markersize=4,
            label="Cable (init)")

    # Clips
    ax.scatter(CLIP1_POS[1], CLIP1_POS[0], c="green", s=120, marker="^",
               label="Clip1", zorder=5)
    ax.scatter(CLIP2_POS[1], CLIP2_POS[0], c="lime", s=120, marker="^",
               label="Clip2", zorder=5)

    # Bases
    ax.scatter(BASE_L[1], BASE_L[0], c="black", s=80, marker="s", label="L Base")
    ax.scatter(BASE_R[1], BASE_R[0], c="gray", s=80, marker="s", label="R Base")

    # IK fails
    for fp in fail_l:
        ax.scatter(fp[1], fp[0], c="red", s=100, marker="x", linewidths=2, zorder=10)
    for fp in fail_r:
        ax.scatter(fp[1], fp[0], c="red", s=100, marker="x", linewidths=2, zorder=10)

    ax.set_xlabel("Y (m)")
    ax.set_ylabel("X (m)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(0.0, 0.7)

    path_xy = os.path.join(output_dir, "trajectory_xy.png")
    fig.savefig(path_xy, dpi=150, bbox_inches="tight")
    print(f"Saved: {path_xy}")
    plt.close(fig)

    # ===== (c) YZ Front View =====
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("Clip Routing — Front View (YZ)", fontsize=14, fontweight="bold")

    ax.plot(left_path[:, 1], left_path[:, 2], "b-", linewidth=1.5, alpha=0.7, label="Left EE")
    ax.plot(right_path[:, 1], right_path[:, 2], "r-", linewidth=1.5, alpha=0.7, label="Right EE")

    for i, lbl in enumerate(wp_labels):
        ax.scatter(wp_l[i][1], wp_l[i][2], c="blue", s=30, zorder=5,
                   edgecolors="black", linewidths=0.5)
        ax.scatter(wp_r[i][1], wp_r[i][2], c="red", s=30, zorder=5,
                   edgecolors="black", linewidths=0.5)
        ax.annotate(lbl, (wp_l[i][1], wp_l[i][2]), fontsize=7, color="blue",
                    textcoords="offset points", xytext=(5, 5))
        ax.annotate(lbl, (wp_r[i][1], wp_r[i][2]), fontsize=7, color="red",
                    textcoords="offset points", xytext=(5, -10))

    # Cable
    ax.plot(cable_ys, cable_zs, "y-o", linewidth=3, markersize=4, label="Cable (init)")

    # Clips
    ax.scatter(CLIP1_POS[1], CLIP1_POS[2], c="green", s=120, marker="^", label="Clip1")
    ax.scatter(CLIP2_POS[1], CLIP2_POS[2], c="lime", s=120, marker="^", label="Clip2")

    # Table
    ax.axhline(y=TABLE_HEIGHT, color="gray", linestyle="--", alpha=0.5, label="Table")

    # Bases
    ax.scatter(BASE_L[1], BASE_L[2], c="black", s=80, marker="s", label="L Base")
    ax.scatter(BASE_R[1], BASE_R[2], c="gray", s=80, marker="s", label="R Base")

    # IK fails
    for fp in fail_l:
        ax.scatter(fp[1], fp[2], c="red", s=100, marker="x", linewidths=2, zorder=10)
    for fp in fail_r:
        ax.scatter(fp[1], fp[2], c="red", s=100, marker="x", linewidths=2, zorder=10)

    ax.set_xlabel("Y (m)")
    ax.set_ylabel("Z (m)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(0.6, 1.4)

    path_yz = os.path.join(output_dir, "trajectory_yz.png")
    fig.savefig(path_yz, dpi=150, bbox_inches="tight")
    print(f"Saved: {path_yz}")
    plt.close(fig)

    return path_3d, path_xy, path_yz


def print_summary(waypoints, ik_results):
    """Print summary table."""
    print("\n" + "=" * 80)
    print(f"{'Phase':<6} {'Description':<25} {'L pos':<28} {'R pos':<28} {'L IK':>6} {'R IK':>6}")
    print("=" * 80)
    for (label, ee_l, ee_r, desc), (_, l_ok, r_ok, l_m, r_m) in zip(waypoints, ik_results):
        l_str = f"({ee_l[0]:.3f},{ee_l[1]:.3f},{ee_l[2]:.3f})"
        r_str = f"({ee_r[0]:.3f},{ee_r[1]:.3f},{ee_r[2]:.3f})"
        l_ik = f"{l_m:.0f}°" if l_ok else "FAIL"
        r_ik = f"{r_m:.0f}°" if r_ok else "FAIL"
        print(f"{label:<6} {desc:<25} {l_str:<28} {r_str:<28} {l_ik:>6} {r_ik:>6}")
    print("=" * 80)

    n_fail = sum(1 for _, l, r, _, _ in ik_results if not l or not r)
    if n_fail == 0:
        print("All waypoints IK feasible.")
    else:
        print(f"WARNING: {n_fail} waypoint(s) have IK failures!")


def main():
    output_dir = "data/test_clip_routing"

    print("=" * 60)
    print("Trajectory Planning & Visualization")
    print("=" * 60)
    print(f"LEFT  Base: {ROBOT_LEFT_BASE}")
    print(f"RIGHT Base: {ROBOT_RIGHT_BASE}")
    print(f"Clip1: ({CLIP1_X},{CLIP1_Y},{CLIP1_Z})")
    print(f"Clip2: ({CLIP2_X},{CLIP2_Y},{CLIP2_Z})")
    print(f"Table H: {TABLE_HEIGHT}")
    print()

    waypoints = build_waypoints()
    ik_results = check_all_ik(waypoints)
    print_summary(waypoints, ik_results)

    paths = plot_all(waypoints, ik_results, output_dir)

    # Copy to Downloads
    dl_dir = "/home/rlrk/Downloads/clip_routing_base_fix"
    os.makedirs(dl_dir, exist_ok=True)
    import shutil
    for p in paths:
        dest = os.path.join(dl_dir, os.path.basename(p))
        shutil.copy2(p, dest)
        print(f"Copied: {dest}")

    print("\nDone.")


if __name__ == "__main__":
    main()
