"""Newton Cable Physics - Video Verification

Records cable simulation at N=1 and N=10, generates side-by-side
comparison video to visually confirm N-dependency is zero.

Also records the kinematic gripper approach test.

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_cable_video.py
"""

import os
import time
import sys

import numpy as np
import warp as wp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle

import newton
from newton.solvers import SolverVBD

DEVICE = "cuda:1"
DT = 1.0 / 480.0
VBD_ITER = 20
CABLE_SEGMENTS = 10
CABLE_SEG_LEN = 0.03
CABLE_RADIUS = 0.005
CABLE_START_Z = 0.30

OUTPUT_DIR = os.path.expanduser("~/IsaacLab/results/newton_cable_video")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_and_run(N, steps, record_interval=4):
    """Build N-world cable sim, run steps, record body positions."""
    main_builder = newton.ModelBuilder()
    main_builder.add_ground_plane()

    world_builder = newton.ModelBuilder()
    positions = [
        (0.0, -CABLE_SEGMENTS * CABLE_SEG_LEN / 2 + i * CABLE_SEG_LEN, CABLE_START_Z)
        for i in range(CABLE_SEGMENTS + 1)
    ]
    world_builder.add_rod(
        positions=positions, radius=CABLE_RADIUS,
        stretch_stiffness=1e5, bend_stiffness=0.1,
        cfg=newton.ModelBuilder.ShapeConfig(
            mu=0.8, density=1100.0, ke=500.0, kd=50.0,
        ),
    )

    main_builder.replicate(world_builder, world_count=N)
    main_builder.color()
    model = main_builder.finalize(device=DEVICE)

    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    contacts = model.contacts()
    control = model.control()
    solver = SolverVBD(model, iterations=VBD_ITER)
    state_out = model.state()

    frames = []
    for step in range(steps):
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state

        if step % record_interval == 0:
            bq = state.body_q.numpy()
            # Record world 0 cable body positions
            world0_cable = []
            for i in range(CABLE_SEGMENTS):
                world0_cable.append(bq[i][:3].copy())
            frames.append(np.array(world0_cable))

    return frames


def build_and_run_gripper(steps, record_interval=4):
    """Run cable + kinematic gripper approach simulation."""
    builder = newton.ModelBuilder()
    builder.add_ground_plane()

    positions = [
        (0.0, -CABLE_SEGMENTS * CABLE_SEG_LEN / 2 + i * CABLE_SEG_LEN, CABLE_START_Z)
        for i in range(CABLE_SEGMENTS + 1)
    ]
    cable_bodies, cable_joints = builder.add_rod(
        positions=positions, radius=CABLE_RADIUS,
        stretch_stiffness=1e5, bend_stiffness=0.1,
        cfg=newton.ModelBuilder.ShapeConfig(
            mu=0.8, density=1100.0, ke=500.0, kd=50.0,
        ),
    )

    # Kinematic fingers
    lf = builder.add_link(
        xform=wp.transform((-0.08, 0.0, CABLE_START_Z), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(body=lf, radius=0.006, half_height=0.02,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=500.0, kd=50.0, density=0.0))

    rf = builder.add_link(
        xform=wp.transform((0.08, 0.0, CABLE_START_Z), wp.quat_identity()),
        mass=1.0, is_kinematic=True,
    )
    builder.add_shape_capsule(body=rf, radius=0.006, half_height=0.02,
        cfg=newton.ModelBuilder.ShapeConfig(mu=1.0, ke=500.0, kd=50.0, density=0.0))

    builder.color()
    model = builder.finalize(device=DEVICE)

    state = model.state()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state)
    contacts = model.contacts()
    control = model.control()
    solver = SolverVBD(model, iterations=VBD_ITER)
    state_out = model.state()

    LF_IDX = CABLE_SEGMENTS
    RF_IDX = CABLE_SEGMENTS + 1
    SETTLE = 960
    APPROACH = 480

    frames = []  # (cable_positions, lf_pos, rf_pos)

    # Phase 1: Settle
    for step in range(SETTLE):
        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)
        state, state_out = state_out, state

        if step % record_interval == 0:
            bq = state.body_q.numpy()
            cable = np.array([bq[i][:3].copy() for i in range(CABLE_SEGMENTS)])
            lf_p = bq[LF_IDX][:3].copy()
            rf_p = bq[RF_IDX][:3].copy()
            frames.append((cable, lf_p, rf_p, "settle"))

    bq = state.body_q.numpy()
    cable_z = bq[CABLE_SEGMENTS // 2][2]

    # Phase 2: Approach fingers from X (stop before contact)
    for step in range(APPROACH):
        t = (step + 1) / APPROACH
        x = 0.08 + (0.025 - 0.08) * t  # 80mm → 25mm (no contact)
        fz = 0.026  # ground level for capsule

        state.clear_forces()
        model.collide(state, contacts)
        solver.step(state, state_out, control, contacts, DT)

        # Override fingers on output
        q = state_out.body_q.numpy()
        q[LF_IDX][:3] = [-x, 0.0, fz]
        q[LF_IDX][3:] = [0, 0, 0, 1]
        q[RF_IDX][:3] = [x, 0.0, fz]
        q[RF_IDX][3:] = [0, 0, 0, 1]
        state_out.body_q.assign(q)
        qd = state_out.body_qd.numpy()
        qd[LF_IDX] = [0, 0, 0, 0, 0, 0]
        qd[RF_IDX] = [0, 0, 0, 0, 0, 0]
        state_out.body_qd.assign(qd)

        state, state_out = state_out, state

        if step % record_interval == 0:
            bq = state.body_q.numpy()
            cable = np.array([bq[i][:3].copy() for i in range(CABLE_SEGMENTS)])
            lf_p = bq[LF_IDX][:3].copy()
            rf_p = bq[RF_IDX][:3].copy()
            frames.append((cable, lf_p, rf_p, "approach"))

    return frames


def render_n_dependency_video(frames_n1, frames_n10, output_path):
    """Render side-by-side N=1 vs N=10 comparison video."""
    n_frames = min(len(frames_n1), len(frames_n10))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Newton VBD: N-dependency Test (Cable Drop)", fontsize=14, fontweight="bold")

    def draw_cable(ax, cable_pos, title, frame_idx):
        ax.clear()
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Y [m]")
        ax.set_ylabel("Z [m]")
        ax.set_xlim(-0.20, 0.20)
        ax.set_ylim(-0.02, 0.35)
        ax.set_aspect("equal")
        ax.axhline(y=0, color="brown", linewidth=2, label="ground")

        # Cable segments
        ys = cable_pos[:, 1]
        zs = cable_pos[:, 2]
        ax.plot(ys, zs, "b-o", markersize=4, linewidth=2, label="cable")

        # Cable capsule circles
        for j in range(len(cable_pos)):
            circle = Circle((ys[j], zs[j]), CABLE_RADIUS, fill=False,
                            edgecolor="blue", alpha=0.3)
            ax.add_patch(circle)

        t = frame_idx * 4 * DT
        ax.text(0.02, 0.95, f"t={t:.3f}s", transform=ax.transAxes,
                fontsize=10, verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
        ax.text(0.02, 0.85, f"z_center={cable_pos[5][2]:.6f}",
                transform=ax.transAxes, fontsize=9, verticalalignment="top",
                fontfamily="monospace")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

    def update(frame_idx):
        draw_cable(ax1, frames_n1[frame_idx], f"N=1 (1 environment)", frame_idx)
        draw_cable(ax2, frames_n10[frame_idx], f"N=10 (10 environments)", frame_idx)

        # Diff annotation
        z1 = frames_n1[frame_idx][5][2]
        z10 = frames_n10[frame_idx][5][2]
        diff = abs(z1 - z10)
        fig.texts = [t for t in fig.texts if "diff" not in getattr(t, "_text", "")]
        color = "green" if diff == 0.0 else "red"
        fig.text(0.5, 0.02, f"diff = {diff:.2e} {'(IDENTICAL)' if diff == 0 else ''}",
                 ha="center", fontsize=12, fontweight="bold", color=color)

    ani = animation.FuncAnimation(fig, update, frames=n_frames, interval=33, blit=False)
    ani.save(output_path, writer="pillow", fps=30)
    plt.close(fig)
    print(f"  Saved: {output_path} ({n_frames} frames)")


def render_gripper_video(frames, output_path):
    """Render cable + gripper approach video (XZ top-down view)."""
    n_frames = len(frames)

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    fig.suptitle("Newton VBD: Cable + Kinematic Gripper", fontsize=14, fontweight="bold")

    def update(frame_idx):
        cable, lf_p, rf_p, phase = frames[frame_idx]
        ax.clear()
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Z [m]")
        ax.set_xlim(-0.12, 0.12)
        ax.set_ylim(-0.02, 0.35)
        ax.set_aspect("equal")
        ax.axhline(y=0, color="brown", linewidth=2)

        # Cable (XZ view, looking along Y)
        xs = cable[:, 0]
        zs = cable[:, 2]
        # Show cable as circles (cross-section)
        for j in range(len(cable)):
            circle = Circle((xs[j], zs[j]), CABLE_RADIUS, fill=True,
                            facecolor="dodgerblue", edgecolor="blue", alpha=0.6)
            ax.add_patch(circle)

        # Cable center marker
        cx, cz = cable[5][0], cable[5][2]
        ax.plot(cx, cz, "r+", markersize=10, markeredgewidth=2)

        # Fingers (capsule cross-section)
        for fp, color, label in [(lf_p, "orange", "L finger"), (rf_p, "green", "R finger")]:
            circle = Circle((fp[0], fp[2]), 0.006, fill=True,
                            facecolor=color, edgecolor="black", alpha=0.7, label=label)
            ax.add_patch(circle)

        t = frame_idx * 4 * DT
        phase_color = {"settle": "gray", "approach": "blue"}.get(phase, "black")
        ax.text(0.02, 0.95, f"t={t:.3f}s  [{phase}]", transform=ax.transAxes,
                fontsize=10, verticalalignment="top", color=phase_color,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
        ax.text(0.02, 0.85, f"cable_z={cz:.6f}", transform=ax.transAxes,
                fontsize=9, verticalalignment="top", fontfamily="monospace")
        ax.text(0.02, 0.78, f"finger_x=±{abs(lf_p[0]):.4f}", transform=ax.transAxes,
                fontsize=9, verticalalignment="top", fontfamily="monospace")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

    ani = animation.FuncAnimation(fig, update, frames=n_frames, interval=33, blit=False)
    ani.save(output_path, writer="pillow", fps=30)
    plt.close(fig)
    print(f"  Saved: {output_path} ({n_frames} frames)")


def main():
    print("Newton Cable Physics - Video Verification")
    print(f"Device: {DEVICE}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Test 1: N-dependency comparison
    print("Recording N=1 cable drop...")
    t0 = time.time()
    frames_n1 = build_and_run(N=1, steps=960, record_interval=4)
    print(f"  {len(frames_n1)} frames, {time.time()-t0:.1f}s")

    print("Recording N=10 cable drop...")
    t0 = time.time()
    frames_n10 = build_and_run(N=10, steps=960, record_interval=4)
    print(f"  {len(frames_n10)} frames, {time.time()-t0:.1f}s")

    print("Rendering N-dependency video...")
    render_n_dependency_video(
        frames_n1, frames_n10,
        os.path.join(OUTPUT_DIR, "n_dependency_comparison.gif"),
    )

    # Final frame comparison
    z1 = frames_n1[-1][5][2]
    z10 = frames_n10[-1][5][2]
    print(f"  Final frame: N=1 z={z1:.10f}, N=10 z={z10:.10f}, diff={abs(z1-z10):.2e}")

    # Test 2: Gripper approach
    print()
    print("Recording gripper approach...")
    t0 = time.time()
    frames_grip = build_and_run_gripper(steps=1440, record_interval=4)
    print(f"  {len(frames_grip)} frames, {time.time()-t0:.1f}s")

    print("Rendering gripper video...")
    render_gripper_video(
        frames_grip,
        os.path.join(OUTPUT_DIR, "gripper_approach.gif"),
    )

    # Summary frame (static image)
    print()
    print("Generating summary image...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Newton Cable Physics - Visual Verification Summary", fontsize=14, fontweight="bold")

    # Panel 1: N=1 final state (YZ)
    cable = frames_n1[-1]
    axes[0].set_title("N=1 Final State (YZ)")
    axes[0].plot(cable[:, 1], cable[:, 2], "b-o", markersize=5)
    for j in range(len(cable)):
        axes[0].add_patch(Circle((cable[j, 1], cable[j, 2]), CABLE_RADIUS,
                                  fill=False, edgecolor="blue", alpha=0.3))
    axes[0].axhline(y=0, color="brown", linewidth=2)
    axes[0].set_xlabel("Y [m]"); axes[0].set_ylabel("Z [m]")
    axes[0].set_xlim(-0.2, 0.2); axes[0].set_ylim(-0.02, 0.05)
    axes[0].set_aspect("equal"); axes[0].grid(True, alpha=0.3)
    axes[0].text(0.5, 0.9, f"z_center={cable[5, 2]:.8f}", transform=axes[0].transAxes,
                 ha="center", fontfamily="monospace", fontsize=10,
                 bbox=dict(facecolor="lightgreen", alpha=0.5))

    # Panel 2: N=10 final state (YZ)
    cable10 = frames_n10[-1]
    axes[1].set_title("N=10 Final State (YZ)")
    axes[1].plot(cable10[:, 1], cable10[:, 2], "r-o", markersize=5)
    for j in range(len(cable10)):
        axes[1].add_patch(Circle((cable10[j, 1], cable10[j, 2]), CABLE_RADIUS,
                                  fill=False, edgecolor="red", alpha=0.3))
    axes[1].axhline(y=0, color="brown", linewidth=2)
    axes[1].set_xlabel("Y [m]"); axes[1].set_ylabel("Z [m]")
    axes[1].set_xlim(-0.2, 0.2); axes[1].set_ylim(-0.02, 0.05)
    axes[1].set_aspect("equal"); axes[1].grid(True, alpha=0.3)
    axes[1].text(0.5, 0.9, f"z_center={cable10[5, 2]:.8f}", transform=axes[1].transAxes,
                 ha="center", fontfamily="monospace", fontsize=10,
                 bbox=dict(facecolor="lightyellow", alpha=0.5))

    # Panel 3: Z trajectory comparison
    z_traj_n1 = [f[5][2] for f in frames_n1]
    z_traj_n10 = [f[5][2] for f in frames_n10]
    t_axis = np.arange(len(z_traj_n1)) * 4 * DT

    axes[2].set_title("Cable Center Z Trajectory")
    axes[2].plot(t_axis, z_traj_n1, "b-", linewidth=2, label="N=1")
    axes[2].plot(t_axis[:len(z_traj_n10)], z_traj_n10, "r--", linewidth=2, label="N=10")
    axes[2].set_xlabel("Time [s]"); axes[2].set_ylabel("Z [m]")
    axes[2].legend(fontsize=10)
    axes[2].grid(True, alpha=0.3)

    diff_arr = np.array(z_traj_n1[:len(z_traj_n10)]) - np.array(z_traj_n10)
    max_diff = np.max(np.abs(diff_arr))
    axes[2].text(0.5, 0.15, f"max |diff| = {max_diff:.2e}\n{'IDENTICAL' if max_diff == 0 else 'DIFFERENT'}",
                 transform=axes[2].transAxes, ha="center", fontsize=12, fontweight="bold",
                 color="green" if max_diff == 0 else "red",
                 bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"))

    plt.tight_layout()
    summary_path = os.path.join(OUTPUT_DIR, "summary.png")
    fig.savefig(summary_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {summary_path}")

    print()
    print("=" * 50)
    print("VIDEO VERIFICATION COMPLETE")
    print(f"  Output dir: {OUTPUT_DIR}")
    print(f"  Files:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, f)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"    {f} ({size_kb:.0f} KB)")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
