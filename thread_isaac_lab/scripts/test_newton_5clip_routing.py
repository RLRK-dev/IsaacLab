"""Newton 5-Clip Cable Routing — VBD Rod Architecture

Routes cable through 5 clips using generalized inchworm regrasp.
Builds on newton_routing_utils.py shared infrastructure.

Phase structure (per episode):
  P1:   Wide-stance approach + grasp (both arms)
  P2:   Micro-lift (grip confirmation)
  For each clip i in [0..4]:
    MOVE-i:  Move to clip i position
    PUSH-i:  Push down into clip i
    (if i < 4):
      INCH-i:  Inchworm regrasp (verify → unclamp → rise → slide → regrasp)

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_5clip_routing.py
    # IK-only (no cable):
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_5clip_routing.py --no-cable
    # With video:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_5clip_routing.py --record-video
    # Custom seed:
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/test_newton_5clip_routing.py --seed 99
"""

import argparse
import json
import math
import os
import time

import numpy as np
import warp as wp
import newton
from newton.solvers import SolverVBD

from newton_routing_utils import (
    # Constants
    TABLE_HEIGHT, FRANKA_NUM_JOINTS, GRASP_X,
    FINGER_OPEN_POS, CABLE_RADIUS,
    NJMAX, SIM_SUBSTEPS, SETTLE_STEPS,
    # Functions
    build_fk_model, init_fk_state,
    build_scene, settle_scene,
    do_initial_grasp, do_micro_lift, do_move_to_clip, do_push_to_clip,
    do_inchworm_regrasp,
    generate_positions, compute_route_order, assign_groove_angles,
    analyze_bends, cable_path_length,
    get_ee_positions, update_kinematic_bodies,
    hold_position,
    save_state_snapshot, restore_state_snapshot, reset_physics_buffer,
    VideoRecorder, set_scene_colors, NumpyEncoder,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0
GRAVITY = -9.81
VBD_ITERATIONS = 20

# Cable: sized for 5-clip route (~400mm path + slack)
CABLE_SEGMENTS = 50
CABLE_SEG_LEN = 0.015   # 50 × 15mm = 750mm total


# ---------------------------------------------------------------------------
# Layout presets (hand-picked from 20-clip reachability test, seed=42)
# ---------------------------------------------------------------------------
def layout_from_20clip_seed42():
    """Pick 5 consecutive clips from the 20-clip route (seed=42).

    Selected: C01 → C16 → C05 → C17 → C08
    - Centered around X=0.38-0.44, Y=-0.05 to -0.15
    - All IK err < 0.001mm, all bends feasible
    - Total path ~192mm
    """
    clips_20 = [
        (0.3174, 0.1532), (0.4103, 0.0335), (0.2606, -0.1170),
        (0.2351, 0.1245), (0.3763, 0.0707), (0.4364, -0.0978),
        (0.2991, 0.0084), (0.3323, -0.0710), (0.3791, -0.1226),
        (0.3393, 0.0969), (0.4712, 0.1047), (0.3983, -0.0204),
        (0.2517, -0.0019), (0.2867, 0.0553), (0.3746, 0.1427),
        (0.2318, -0.0587), (0.4347, -0.0493), (0.4207, -0.1446),
        (0.3133, -0.1306), (0.2279, 0.0459),
    ]
    # Pick indices: C01, C16, C05, C17, C08
    pick = [1, 16, 5, 17, 8]
    return [clips_20[i] for i in pick]


def layout_smooth_s_curve():
    """5-clip S-curve layout with no backtracking.

    Smooth monotonic path from +Y to -Y with gentle X oscillation.
    Tests diverse routing directions without sharp reversals.

    Routing directions:
      0->1: (0.53, -0.85) ~94mm  — Y-dominant, +X
      1->2: (0.41, -0.92) ~98mm  — Y-dominant, +X
      2->3: (-0.50, -0.87) ~81mm — Y-dominant, -X (reversal ~68°)
      3->4: (-0.77, -0.64) ~78mm — X-dominant, -X
    Total path: ~351mm, cable 750mm = 399mm slack.
    """
    return [
        (0.33, 0.10),   # CLIP0: near cable center, +Y
        (0.38, 0.02),   # CLIP1: +X shift
        (0.42, -0.07),  # CLIP2: +X continues
        (0.38, -0.14),  # CLIP3: -X reversal (gentle ~68°)
        (0.32, -0.19),  # CLIP4: -X continues, X-dominant
    ]


def generate_layout(n_clips=5, seed=42, preset=None):
    """Generate or load a 5-clip layout.

    Returns: (positions, route, thetas, segments)
    """
    if preset == "20clip":
        positions = layout_from_20clip_seed42()
        route = list(range(len(positions)))  # already in route order
        thetas = assign_groove_angles(positions, route, seed=seed)
    elif preset == "s_curve":
        positions = layout_smooth_s_curve()
        route = list(range(len(positions)))  # already in route order
        thetas = assign_groove_angles(positions, route, seed=seed)
    else:
        positions = generate_positions(n_clips, seed=seed,
                                       x_range=(0.28, 0.46),
                                       y_range=(-0.15, 0.15))
        route = compute_route_order(positions)
        thetas = assign_groove_angles(positions, route, seed=seed)

    segments = analyze_bends(positions, thetas, route)
    return positions, route, thetas, segments


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------
def run_episode(model, state, scene_info, solver, contacts, episode_idx,
                clip_positions_xy, route):
    """Run one episode of 5-clip routing.

    Returns (state, result_dict).
    """
    results = {"episode": episode_idx, "overall": "FAIL", "clips": {}}
    n_clips = len(route)

    # P1: Initial grasp
    state, p1 = do_initial_grasp(model, state, scene_info, solver, contacts)
    results["P1"] = p1
    if not p1["pass"]:
        results["fail_reason"] = "P1_grasp_fail"
        return state, results

    # P2: Micro-lift
    state, p2 = do_micro_lift(model, state, scene_info, solver, contacts)
    results["P2"] = p2

    for ci in range(n_clips):
        clip_idx = route[ci]
        cx, cy = clip_positions_xy[clip_idx]
        clip_label = f"CLIP{ci}"
        print(f"\n  {'='*60}")
        print(f"  {clip_label}: ({cx:.3f}, {cy:.3f})")
        print(f"  {'='*60}")

        # Move to clip (asymmetric placement if we have a previous clip)
        prev_xy = None
        if ci > 0:
            prev_idx = route[ci - 1]
            prev_xy = clip_positions_xy[prev_idx]
        state, move_r = do_move_to_clip(
            model, state, scene_info, solver, contacts,
            cx, cy, label=f"MOVE-{ci}", prev_clip_xy=prev_xy)
        results["clips"][f"move_{ci}"] = move_r

        # Push into clip
        state, push_r = do_push_to_clip(
            model, state, scene_info, solver, contacts,
            cx, cy, label=f"PUSH-{ci}")
        results["clips"][f"push_{ci}"] = push_r

        if not push_r["pass"]:
            results["fail_reason"] = f"push_{ci}_fail"
            results["last_clip_passed"] = ci - 1
            return state, results

        # Inchworm regrasp (if not last clip, and cable present)
        has_cable = len(scene_info.get("cable_bodies", [])) > 0
        if ci < n_clips - 1 and has_cable:
            next_clip_idx = route[ci + 1]
            ncx, ncy = clip_positions_xy[next_clip_idx]
            state, inch_r = do_inchworm_regrasp(
                model, state, scene_info, solver, contacts,
                current_clip_xy=(cx, cy),
                next_clip_xy=(ncx, ncy),
                label_prefix=f"INCH-{ci}",
            )
            results["clips"][f"inch_{ci}"] = inch_r
            if not inch_r["pass"]:
                results["fail_reason"] = f"inch_{ci}_fail"
                results["last_clip_passed"] = ci
                return state, results
        elif ci < n_clips - 1:
            print(f"  [INCH-{ci}] Skipped (no cable)")
            results["clips"][f"inch_{ci}"] = {"pass": True, "skipped": True}

    # All clips passed
    results["overall"] = "PASS"
    results["last_clip_passed"] = n_clips - 1
    return state, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Newton 5-clip routing test")
    parser.add_argument("--no-cable", action="store_true")
    parser.add_argument("--num-episodes", type=int, default=1)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--preset", type=str, default="s_curve",
                        choices=["20clip", "s_curve"],
                        help="Use a hand-picked clip layout (default: s_curve)")
    args = parser.parse_args()

    use_cable = not args.no_cable
    if not args.no_video and os.environ.get("HARNESS_RECORD_VIDEO", "") == "1":
        args.record_video = True

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/newton_5clip_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate layout
    print(f"[5CLIP] Device={DEVICE}, seed={args.seed}")
    print(f"[5CLIP] Newton: {newton.__version__}, Warp: {wp.__version__}")
    positions, route, thetas, segments = generate_layout(
        n_clips=5, seed=args.seed, preset=args.preset)
    clip_positions_3d = [(x, y, TABLE_HEIGHT) for x, y in positions]
    path_len = cable_path_length(positions, route)

    print(f"[5CLIP] {len(positions)} clips, cable path = {path_len*1000:.0f}mm")
    print(f"[5CLIP] Cable: {CABLE_SEGMENTS} seg × {CABLE_SEG_LEN*1000:.0f}mm "
          f"= {CABLE_SEGMENTS*CABLE_SEG_LEN*1000:.0f}mm")
    for ci, idx in enumerate(route):
        cx, cy = positions[idx]
        th_deg = math.degrees(thetas[idx])
        seg_info = ""
        if ci < len(segments):
            s = segments[ci]
            seg_info = f" → {s['dist_mm']:.0f}mm"
        print(f"  Clip{ci}: ({cx:.3f}, {cy:.3f}) theta={th_deg:+.0f}°{seg_info}")

    # Bend check
    bend_pass = sum(1 for s in segments if s["feasible"])
    bend_fail = len(segments) - bend_pass
    if bend_fail > 0:
        print(f"  [WARN] {bend_fail} bend segments infeasible!")
        for s in segments:
            if not s["feasible"]:
                print(f"    C{s['from']}->C{s['to']}: dist={s['dist_mm']:.0f}mm, "
                      f"arc={s['arc_needed_mm']:.0f}mm")

    # Build FK model
    print("\n[BUILD] Building FK model...")
    fk_model = build_fk_model(DEVICE, gravity=GRAVITY)
    fk_state = init_fk_state(fk_model, finger_open=True)

    # Build physics scene
    print("[BUILD] Building physics scene...")
    scene_info = build_scene(
        device=DEVICE, clip_positions=clip_positions_3d,
        fk_model=fk_model, fk_state=fk_state,
        use_cable=use_cable, cable_segments=CABLE_SEGMENTS,
        cable_seg_len=CABLE_SEG_LEN, gravity=GRAVITY,
    )
    model = scene_info["model"]
    cable_bodies = scene_info.get("cable_bodies", [])

    state = model.state()
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control

    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    print(f"  [SOLVER] VBD (iterations={VBD_ITERATIONS})")

    # Video recorder
    # Compute camera focus from clip layout
    mean_x = np.mean([p[0] for p in positions])
    mean_y = np.mean([p[1] for p in positions])
    focus = (mean_x, mean_y, TABLE_HEIGHT + 0.02)
    cameras = [
        ("overhead", (mean_x, mean_y, 1.60), focus),
        ("front",    (mean_x + 0.75, mean_y, 1.05), focus),
        ("left",     (mean_x, mean_y - 0.65, 0.93), focus),
        ("right",    (mean_x, mean_y + 0.65, 0.93), focus),
        ("diag",     (mean_x + 0.35, mean_y - 0.40, 1.00), focus),
    ]
    recorder = VideoRecorder(args.output_dir, model, enabled=args.record_video,
                             cameras=cameras, dt=DT)
    scene_info["recorder"] = recorder
    set_scene_colors(recorder, scene_info)

    # Settle cable
    print("[INIT] Settling (2s)...")
    state = settle_scene(model, state, scene_info, solver, contacts,
                         duration_s=2.0, dt=DT)

    # Save settled state
    snapshot = save_state_snapshot(model, state, fk_state)

    # Run episodes
    all_results = {
        "test": "newton_5clip_routing",
        "device": DEVICE,
        "seed": args.seed,
        "preset": args.preset,
        "clips": [
            {"id": i, "x": round(positions[i][0], 4),
             "y": round(positions[i][1], 4),
             "theta_deg": round(math.degrees(thetas[i]), 1)}
            for i in range(len(positions))
        ],
        "route_order": route,
        "cable_path_mm": round(path_len * 1000, 1),
        "cable_length_mm": CABLE_SEGMENTS * CABLE_SEG_LEN * 1000,
        "bend_results": segments,
        "episodes": [],
        "n_pass": 0, "n_fail": 0,
    }

    start_time = time.time()
    for ep in range(args.num_episodes):
        print(f"\n{'='*60}")
        print(f"  EPISODE {ep+1}/{args.num_episodes}")
        print(f"{'='*60}")

        if ep > 0:
            state = model.state()
            restore_state_snapshot(model, state, solver, fk_state, fk_model,
                                   scene_info, snapshot)
        recorder.reset()

        try:
            state, ep_result = run_episode(
                model, state, scene_info, solver, contacts, ep,
                positions, route)
        except Exception as e:
            print(f"\n  [ERROR] Episode {ep+1} crashed: {e}")
            import traceback
            traceback.print_exc()
            ep_result = {"episode": ep, "overall": "CRASH", "error": str(e)}

        video_paths = recorder.finalize(ep)
        if video_paths:
            ep_result["videos"] = video_paths
        all_results["episodes"].append(ep_result)

        if ep_result["overall"] == "PASS":
            all_results["n_pass"] += 1
            print(f"\n  >>> EPISODE {ep+1}: PASS — all 5 clips routed <<<")
        else:
            all_results["n_fail"] += 1
            reason = ep_result.get("fail_reason", "unknown")
            last = ep_result.get("last_clip_passed", -1)
            print(f"\n  >>> EPISODE {ep+1}: {ep_result['overall']} "
                  f"({reason}, {last+1}/5 clips) <<<")

    elapsed = time.time() - start_time
    all_results["elapsed_s"] = round(elapsed, 1)
    all_results["overall"] = "PASS" if all_results["n_fail"] == 0 else "FAIL"
    all_results["pass_rate"] = f"{all_results['n_pass']}/{args.num_episodes}"

    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(all_results, f, indent=2, cls=NumpyEncoder)

    print(f"\n{'='*60}")
    print(f"  SUMMARY: {all_results['pass_rate']} pass, {elapsed:.1f}s")
    print(f"  Metrics: {metrics_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
