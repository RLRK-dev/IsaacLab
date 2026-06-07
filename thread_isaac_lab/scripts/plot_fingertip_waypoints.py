#!/usr/bin/env python3
"""Plot intended fingertip trajectories for 43-step routing plan.

No Newton/Warp required — pure waypoint geometry.

Usage:
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/plot_fingertip_waypoints.py          # C1 only
    python thread_isaac_lab/scripts/plot_fingertip_waypoints.py --all    # C1-C5 full 43-step
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_config_dir = os.path.join(_SCRIPT_DIR, "..", "configs")
sys.path.insert(0, _config_dir)

from task_config import (
    TABLE_HEIGHT, APPROACH_Z, GRASP_Z, LIFT_Z,
    GRASP_X, CLIP_POSITIONS, GRIP_HALF_SPAN,
    EE_TO_FINGERTIP,
    FINGER_OPEN_POS, FINGER_HALF_OPEN_POS, FINGER_CLOSE_POS,
)

Z_UP = LIFT_Z
Z_DOWN = GRASP_Z
CABLE_X = GRASP_X
OPEN = FINGER_OPEN_POS
HALF = FINGER_HALF_OPEN_POS
CLOSE = FINGER_CLOSE_POS

CLIP_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def ee_to_fingertip(ee_pos):
    return (ee_pos[0], ee_pos[1], ee_pos[2] - EE_TO_FINGERTIP)


def build_c1_waypoints():
    """C1 routing only."""
    c1x, c1y = CLIP_POSITIONS[0]
    gl = c1y - GRIP_HALF_SPAN
    gr = c1y + GRIP_HALF_SPAN
    # (step_num, label, clip_index, L_target, R_target, is_contact)
    return [
        (2,  "approach", 0, (CABLE_X, gl, Z_UP),   (CABLE_X, gr, Z_UP),   False),
        (3,  "descend",  0, (CABLE_X, gl, Z_DOWN), (CABLE_X, gr, Z_DOWN), False),
        (4,  "clamp",    0, (CABLE_X, gl, Z_DOWN), (CABLE_X, gr, Z_DOWN), True),
        (5,  "lift",     0, (CABLE_X, gl, Z_UP),   (CABLE_X, gr, Z_UP),   False),
        (6,  "move",     0, (c1x, gl, Z_UP),       (c1x, gr, Z_UP),       False),
        (7,  "push",     0, (c1x, gl, Z_DOWN),     (c1x, gr, Z_DOWN),     True),
        (8,  "release",  0, (c1x, gl, Z_DOWN),     (c1x, gr, Z_DOWN),     False),
        (10, "rise",     0, (c1x, gl, Z_UP),       (c1x, gr, Z_UP),       False),
    ]


def build_all_waypoints():
    """Full 43-step routing C1-C5. Returns list of (step_num, label, clip_idx, L, R, contact)."""
    wps = []
    c1x, c1y = CLIP_POSITIONS[0]
    gl = c1y - GRIP_HALF_SPAN
    gr = c1y + GRIP_HALF_SPAN

    # Phase A: steps 2-5
    wps.append((2,  "approach", 0, (CABLE_X, gl, Z_UP),   (CABLE_X, gr, Z_UP),   False))
    wps.append((3,  "descend",  0, (CABLE_X, gl, Z_DOWN), (CABLE_X, gr, Z_DOWN), False))
    wps.append((4,  "clamp",    0, (CABLE_X, gl, Z_DOWN), (CABLE_X, gr, Z_DOWN), True))
    wps.append((5,  "lift",     0, (CABLE_X, gl, Z_UP),   (CABLE_X, gr, Z_UP),   False))

    # Phase B: C1 steps 6-10
    wps.append((6,  "move",    0, (c1x, gl, Z_UP),   (c1x, gr, Z_UP),   False))
    wps.append((7,  "push",    0, (c1x, gl, Z_DOWN), (c1x, gr, Z_DOWN), True))
    wps.append((8,  "release", 0, (c1x, gl, Z_DOWN), (c1x, gr, Z_DOWN), False))
    wps.append((10, "rise",    0, (c1x, gl, Z_UP),   (c1x, gr, Z_UP),   False))

    # C2-C5: 8 steps each (incl. L-clamp), starting at step 11
    step_num = 11
    for ci in range(1, 5):
        cx, cy = CLIP_POSITIONS[ci]
        prev_cy = CLIP_POSITIONS[ci - 1][1]
        gl_c = cy - GRIP_HALF_SPAN
        gr_c = cy + GRIP_HALF_SPAN
        regrab_y = (prev_cy + cy) / 2.0

        wps.append((step_num,     "above",   ci, (cx, gl_c, Z_UP),   (cx, gr_c, Z_UP),          False))
        wps.append((step_num + 1, "L-clamp", ci, (cx, gl_c, Z_UP),   (cx, gr_c, Z_UP),          False))
        wps.append((step_num + 2, "regrab",  ci, (cx, gl_c, Z_UP),   (cx, regrab_y, Z_UP),      False))
        wps.append((step_num + 3, "clamp",   ci, (cx, gl_c, Z_UP),   (cx, regrab_y, Z_UP),      False))
        wps.append((step_num + 4, "push",    ci, (cx, gl_c, Z_DOWN), (cx, gr_c, Z_DOWN),          True))
        wps.append((step_num + 5, "hold",    ci, (cx, gl_c, Z_DOWN), (cx, gr_c, Z_DOWN),          True))
        wps.append((step_num + 6, "release", ci, (cx, gl_c, Z_DOWN), (cx, gr_c, Z_DOWN),          False))
        wps.append((step_num + 7, "rise",    ci, (cx, gl_c, Z_UP),   (cx, gr_c, Z_UP),            False))
        step_num += 8

    return wps


def plot_all(wps, out_path):
    """C1-C5 per-clip strip + XY overview."""
    ft_l = [ee_to_fingertip(w[3]) for w in wps]
    ft_r = [ee_to_fingertip(w[4]) for w in wps]

    # ---- Figure 1: Per-clip YZ strip ----
    fig, axes = plt.subplots(1, 5, figsize=(28, 7), sharey=True)

    for ci in range(5):
        ax = axes[ci]
        cx, cy = CLIP_POSITIONS[ci]
        cname = f"C{ci+1}"
        color = CLIP_COLORS[ci]

        # Grip span band + center line
        ax.axvspan(cy - GRIP_HALF_SPAN, cy + GRIP_HALF_SPAN, alpha=0.10, color=color)
        ax.axvline(cy, color=color, linestyle="-.", alpha=0.5, linewidth=1.5)
        ax.plot(cy, TABLE_HEIGHT, "D", color=color, markersize=12, zorder=5)
        ax.axhline(TABLE_HEIGHT, color="brown", linestyle="--", alpha=0.4)

        for i in range(len(wps)):
            snum, lab, clip_idx = wps[i][0], wps[i][1], wps[i][2]
            is_contact = wps[i][5]

            # Only show this clip's phases (+ initial grasp for C1)
            is_this = (clip_idx == ci) or (ci == 0 and clip_idx == 0)
            if not is_this:
                continue

            ly_i, lz_i = ft_l[i][1], ft_l[i][2]
            ry_i, rz_i = ft_r[i][1], ft_r[i][2]

            if is_contact:
                ax.plot(ly_i, lz_i, "bo", markersize=8, zorder=4)
                ax.plot(ry_i, rz_i, "rs", markersize=8, zorder=4)
                ax.plot([ly_i, ry_i], [lz_i, rz_i], "k-", alpha=0.25, linewidth=0.8)
                # Step number + label below
                ax.annotate(f"S{snum} {lab}", ((ly_i + ry_i) / 2, min(lz_i, rz_i)),
                            textcoords="offset points", xytext=(0, -14),
                            fontsize=7, ha="center", fontweight="bold")
            else:
                ax.plot(ly_i, lz_i, "bo", markersize=3, alpha=0.35)
                ax.plot(ry_i, rz_i, "rs", markersize=3, alpha=0.35)
                # Step number only, small
                mid_y = (ly_i + ry_i) / 2
                mid_z = max(lz_i, rz_i)
                ax.annotate(f"S{snum}", (mid_y, mid_z),
                            textcoords="offset points", xytext=(0, 5),
                            fontsize=6, ha="center", alpha=0.5)

        ax.set_title(f"{cname} ({cx}, {cy:+.3f})", fontsize=11, color=color, fontweight="bold")
        ax.set_xlabel("Y (m)")
        if ci == 0:
            ax.set_ylabel("Z (m) — fingertip")
        ax.set_xlim(cy - 0.10, cy + 0.10)
        ax.grid(True, alpha=0.2)

    # Legend outside plots
    handles = [
        plt.Line2D([], [], color="blue", marker="o", linestyle="None", markersize=7, label="L arm (contact)"),
        plt.Line2D([], [], color="blue", marker="o", linestyle="None", markersize=3, alpha=0.4, label="L arm (transit)"),
        plt.Line2D([], [], color="red", marker="s", linestyle="None", markersize=7, label="R arm (contact)"),
        plt.Line2D([], [], color="red", marker="s", linestyle="None", markersize=3, alpha=0.4, label="R arm (transit)"),
        plt.Line2D([], [], color="brown", linestyle="--", label="Table Z=0.800"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=9,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("Fingertip Positions at Each Clip — 43-Step Plan (S=step number)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()

    # ---- Figure 2: XY overview with step numbers ----
    fig2, ax = plt.subplots(1, 1, figsize=(10, 9))

    lx_all = [p[0] for p in ft_l]
    ly_all = [p[1] for p in ft_l]
    rx_all = [p[0] for p in ft_r]
    ry_all = [p[1] for p in ft_r]

    # Transit lines dimmed
    ax.plot(lx_all, ly_all, "b-", alpha=0.15, linewidth=1)
    ax.plot(rx_all, ry_all, "r-", alpha=0.15, linewidth=1)

    # Plot all points with step numbers
    for i in range(len(wps)):
        snum = wps[i][0]
        is_contact = wps[i][5]
        if is_contact:
            ax.plot(lx_all[i], ly_all[i], "bo", markersize=7, zorder=4)
            ax.plot(rx_all[i], ry_all[i], "rs", markersize=7, zorder=4)
            ax.annotate(f"S{snum}", (rx_all[i], ry_all[i]),
                        textcoords="offset points", xytext=(6, 2),
                        fontsize=7, fontweight="bold")
        else:
            ax.plot(lx_all[i], ly_all[i], "bo", markersize=3, alpha=0.3)
            ax.plot(rx_all[i], ry_all[i], "rs", markersize=3, alpha=0.3)
            ax.annotate(f"{snum}", (rx_all[i], ry_all[i]),
                        textcoords="offset points", xytext=(4, 1),
                        fontsize=5, alpha=0.4)

    # Clips
    for ci, (cx, cy) in enumerate(CLIP_POSITIONS):
        ax.plot(cx, cy, "D", color=CLIP_COLORS[ci], markersize=11, zorder=5)
        ax.annotate(f"C{ci+1}", (cx, cy), xytext=(9, 0), textcoords="offset points",
                    fontsize=11, color=CLIP_COLORS[ci], fontweight="bold", va="center")
        ax.axhspan(cy - GRIP_HALF_SPAN, cy + GRIP_HALF_SPAN,
                   alpha=0.05, color=CLIP_COLORS[ci])

    # Legend outside
    handles = [
        plt.Line2D([], [], color="blue", marker="o", linestyle="None", markersize=7, label="L arm (contact)"),
        plt.Line2D([], [], color="red", marker="s", linestyle="None", markersize=7, label="R arm (contact)"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=9, framealpha=0.9)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("XY Overview — 43-Step C1→C5 Routing (S=step number)", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")
    fig2.tight_layout()

    out2 = out_path.replace(".png", "_xy.png")
    fig2.savefig(out2, dpi=150, bbox_inches="tight")
    print(f"Saved: {out2}")
    plt.close()

    return _check_geometry(wps, "C1-C5")


def plot_c1(wps, out_path):
    """C1-only 3-panel plot."""
    ft_l = [ee_to_fingertip(w[3]) for w in wps]
    ft_r = [ee_to_fingertip(w[4]) for w in wps]

    lx = [p[0] for p in ft_l]
    ly = [p[1] for p in ft_l]
    lz = [p[2] for p in ft_l]
    rx = [p[0] for p in ft_r]
    ry = [p[1] for p in ft_r]
    rz = [p[2] for p in ft_r]

    c1x, c1y = CLIP_POSITIONS[0]
    fig, axes = plt.subplots(1, 3, figsize=(22, 7))

    for ax_idx, (xs_l, xs_r, ys_l, ys_r, xlabel, ylabel, title) in enumerate([
        (lx, rx, lz, rz, "X (m)", "Z (m) — fingertip", "XZ Side"),
        (ly, ry, lz, rz, "Y (m)", "Z (m) — fingertip", "YZ Side"),
        (lx, rx, ly, ry, "X (m)", "Y (m)", "XY Top"),
    ]):
        ax = axes[ax_idx]
        ax.plot(xs_l, ys_l, "b-o", markersize=5, alpha=0.6)
        ax.plot(xs_r, ys_r, "r-s", markersize=5, alpha=0.6)
        ax.axhline(TABLE_HEIGHT if ax_idx < 2 else c1y, color="brown", linestyle="--", alpha=0.5)

        # Step numbers
        for i in range(len(wps)):
            snum = wps[i][0]
            is_contact = wps[i][5]
            mid_x = (xs_l[i] + xs_r[i]) / 2
            mid_y = max(ys_l[i], ys_r[i])
            weight = "bold" if is_contact else "normal"
            alpha = 1.0 if is_contact else 0.5
            ax.annotate(f"S{snum}", (mid_x, mid_y), textcoords="offset points",
                        xytext=(0, 6), fontsize=7, ha="center",
                        fontweight=weight, alpha=alpha)

        # Clip marker
        if ax_idx == 0:  # XZ
            ax.plot(c1x, TABLE_HEIGHT, "gD", markersize=10, zorder=5)
        elif ax_idx == 1:  # YZ
            ax.plot(c1y, TABLE_HEIGHT, "gD", markersize=10, zorder=5)
            ax.axvline(c1y, color="green", linestyle="-.", alpha=0.4)
            ax.axvspan(c1y - GRIP_HALF_SPAN, c1y + GRIP_HALF_SPAN,
                       alpha=0.1, color="green")
        else:  # XY
            for ci, (cx, cy) in enumerate(CLIP_POSITIONS):
                ax.plot(cx, cy, "D", color=CLIP_COLORS[ci], markersize=8, zorder=5)
                ax.annotate(f"C{ci+1}", (cx, cy), xytext=(6, 3),
                            textcoords="offset points", fontsize=8,
                            color=CLIP_COLORS[ci], fontweight="bold")
            ax.set_aspect("equal")

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    # Legend outside
    handles = [
        plt.Line2D([], [], color="blue", marker="o", linestyle="-", label="L arm"),
        plt.Line2D([], [], color="red", marker="s", linestyle="-", label="R arm"),
        plt.Line2D([], [], color="green", marker="D", linestyle="None", markersize=8, label="C1"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9,
               bbox_to_anchor=(0.5, -0.01))

    fig.suptitle("Fingertip Trajectories — C1 Routing (S=step number)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()
    return _check_geometry(wps, "C1")


def _check_geometry(wps, scope):
    ft_l = [ee_to_fingertip(w[3]) for w in wps]
    ft_r = [ee_to_fingertip(w[4]) for w in wps]

    print(f"\n=== Geometric Checks ({scope}) ===")
    issues = []

    for i in range(len(wps)):
        snum, lab = wps[i][0], wps[i][1]
        l, r = ft_l[i], ft_r[i]

        if l[2] < TABLE_HEIGHT - 0.001:
            msg = f"  WARN: S{snum} {lab} L Z={l[2]:.3f} < table"
            issues.append(msg)
            print(msg)
        if r[2] < TABLE_HEIGHT - 0.001:
            msg = f"  WARN: S{snum} {lab} R Z={r[2]:.3f} < table"
            issues.append(msg)
            print(msg)

        if "push" in lab or "hold" in lab:
            ci = wps[i][2]
            cx, cy = CLIP_POSITIONS[ci]
            cname = f"C{ci+1}"
            if l[1] < cy < r[1]:
                print(f"  OK: S{snum} {lab} — {cname} Y={cy:+.3f} in [{l[1]:+.3f}, {r[1]:+.3f}]")
            else:
                msg = f"  FAIL: S{snum} {lab} — {cname} Y={cy:+.3f} NOT in [{l[1]:+.3f}, {r[1]:+.3f}]"
                issues.append(msg)
                print(msg)

    if not issues:
        print("  ALL CHECKS PASSED")
    else:
        print(f"  {len(issues)} issue(s) found")
    return len(issues) == 0


def main():
    do_all = "--all" in sys.argv
    if do_all:
        wps = build_all_waypoints()
        ok = plot_all(wps, os.path.expanduser("~/Downloads/fingertip_43step.png"))
    else:
        wps = build_c1_waypoints()
        ok = plot_c1(wps, os.path.expanduser("~/Downloads/fingertip_c1.png"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
