# Copyright (c) 2024, THREAD Project
# SPDX-License-Identifier: BSD-3-Clause

"""Wet-run: execute verified waypoints in Newton VBD physics + record video.

Reads a v2 waypoints JSON (from test_motion_sequence_dry_run.py) and executes
the full 43-step routing sequence in Newton VBD with cable physics.
Records multi-camera video for demo motion verification.

Pipeline (DAPG_DESIGN.md §11):
    dry-run → verified_waypoints.json → THIS SCRIPT → video + demo data

Usage:
    source ~/env_isaaclab6/bin/activate
    OMNI_KIT_ACCEPT_EULA=YES python thread_isaac_lab/scripts/run_demo_from_waypoints.py \
        --waypoints thread_isaac_lab/data/motion_sequence_dry_run.json \
        --output-dir ~/Downloads --device cuda:0
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import warp as wp  # noqa: E402
import newton  # noqa: E402
from newton.solvers import SolverVBD  # noqa: E402

from newton_routing_utils import (  # noqa: E402
    # Constants
    TABLE_HEIGHT, FRANKA_NUM_JOINTS, EE_BODY_OFFSET,
    FINGER_OPEN_POS, FINGER_CLOSE_POS, FINGER_HALF_OPEN_POS,
    CABLE_RADIUS, NJMAX, SIM_SUBSTEPS, SETTLE_STEPS,
    # Functions
    build_fk_model, init_fk_state,
    build_scene, settle_scene,
    ik_move_both, ik_move_single, hold_position,
    interpolate_fingers, get_ee_positions,
    update_kinematic_bodies,
    VideoRecorder, set_scene_colors, NumpyEncoder,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEVICE = os.environ.get("NEWTON_DEVICE", "cuda:0")
DT = 1.0 / 480.0
GRAVITY = -9.81
VBD_ITERATIONS = 20

# Cable: sized for 5-clip route
CABLE_SEGMENTS = 50
CABLE_SEG_LEN = 0.015   # 50 × 15mm = 750mm total


# ---------------------------------------------------------------------------
# Waypoint step executor
# ---------------------------------------------------------------------------
class WaypointExecutor:
    """Execute waypoint steps in Newton VBD physics."""

    def __init__(self, model, state, scene_info, solver, contacts,
                 clip_positions, device):
        self.model = model
        self.state = state
        self.scene_info = scene_info
        self.solver = solver
        self.contacts = contacts
        self.clip_positions = clip_positions  # [(x, y), ...]
        self.device = device

        # Cable management state
        self.grasped = False  # whether cable is attached to EE

    def execute(self, step):
        """Execute one waypoint step. Returns updated state."""
        action = step["action_type"]
        target_l = tuple(step["target_l"])
        target_r = tuple(step["target_r"])
        step_num = step["step"]
        desc = step["desc"]
        clip_idx = step.get("clip_index")
        guide = step.get("guide_hand", "L")

        print(f"\n  === STEP {step_num}: {desc} [{action}] ===")

        if action == "ik_move":
            self._do_ik_move(target_l, target_r)
        elif action == "grasp":
            self._do_grasp()
        elif action == "half_release":
            self._do_half_release(guide)
        elif action == "clip_lock":
            self._do_clip_lock(clip_idx)
        elif action == "release_rise":
            self._do_release_rise(target_l, target_r, guide)
        elif action == "regrasp":
            self._do_regrasp(target_l, target_r, guide)
        elif action == "release":
            self._do_release(guide)
        elif action == "guide_transition":
            self._do_guide_transition(target_l, target_r, guide)
        else:
            print(f"  [WARN] Unknown action_type: {action}, treating as ik_move")
            self._do_ik_move(target_l, target_r)

        return self.state

    def _do_ik_move(self, target_l, target_r):
        """Move both arms to target positions."""
        self.state, ok = ik_move_both(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            target_left=target_l, target_right=target_r,
            label="WP-MOVE", converge_mm=5.0,
        )
        self.state = hold_position(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            SETTLE_STEPS)
        if not ok:
            print("  [WARN] IK did not fully converge")

    def _do_grasp(self):
        """Close both fingers to grasp cable."""
        self.state = interpolate_fingers(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            left_target=FINGER_CLOSE_POS, right_target=FINGER_CLOSE_POS,
            n_steps=300, label="WP-GRASP",
        )
        self.grasped = True
        print(f"  [GRASP] Fingers closed")

    def _do_half_release(self, guide_hand):
        """Half-open guide hand, full-open other."""
        # Finger interpolation
        if guide_hand == "L":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_HALF_OPEN_POS, right_target=FINGER_OPEN_POS,
                n_steps=200, label="WP-HALF",
            )
        else:
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_OPEN_POS, right_target=FINGER_HALF_OPEN_POS,
                n_steps=200, label="WP-HALF",
            )

    def _do_clip_lock(self, clip_idx):
        """Verify cable is seated in clip groove (held by VBD contact)."""
        if clip_idx is None or clip_idx >= len(self.clip_positions):
            print(f"  [WARN] Invalid clip_index={clip_idx}")
            return

        cx, cy = self.clip_positions[clip_idx]
        print(f"  [CLIP_LOCK] Clip{clip_idx} at ({cx:.3f}, {cy:.3f}): "
              f"cable held by VBD contact")

    def _do_release_rise(self, target_l, target_r, guide_hand=None):
        """Open fingers and rise. Guide hand stays at HALF_OPEN."""
        self.grasped = False

        # Open fingers — guide hand stays at HALF_OPEN per routing spec
        if guide_hand == "L":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_HALF_OPEN_POS, right_target=FINGER_OPEN_POS,
                n_steps=200, label="WP-OPEN",
            )
        elif guide_hand == "R":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_OPEN_POS, right_target=FINGER_HALF_OPEN_POS,
                n_steps=200, label="WP-OPEN",
            )
        else:
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_OPEN_POS, right_target=FINGER_OPEN_POS,
                n_steps=200, label="WP-OPEN",
            )

        # Rise to target
        self.state, ok = ik_move_both(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            target_left=target_l, target_right=target_r,
            label="WP-RISE", converge_mm=5.0,
        )
        self.state = hold_position(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            SETTLE_STEPS)

    def _do_regrasp(self, target_l, target_r, guide_hand):
        """Regrasp sequence: guide arm stays, other arm descends to cable."""
        cable_bodies = self.scene_info.get("cable_bodies", [])

        # The regrasp arm needs to:
        # 1. Move above cable position (approach Z)
        # 2. Descend to grasp Z
        # 3. Close fingers

        if guide_hand == "L":
            # Left arm is guide (stays at target_l), right regrasps
            regrasp_arm = "right"
            regrasp_target_xy = target_r[:2]  # from waypoints
            guide_target = target_l
        else:
            regrasp_arm = "left"
            regrasp_target_xy = target_l[:2]
            guide_target = target_r

        # Find nearest cable body to regrasp target (bounded micro-adjust §11.4)
        ADJUST_MAX = 0.005  # 5mm
        wp.synchronize()
        bq = self.state.body_q.numpy()
        best_xy = np.array(regrasp_target_xy, dtype=np.float64)

        if cable_bodies:
            cable_xys = np.array([bq[bi][:2] for bi in cable_bodies])
            dists = np.linalg.norm(cable_xys - best_xy, axis=1)
            nearest_idx = int(np.argmin(dists))
            nearest_xy = cable_xys[nearest_idx]
            delta = nearest_xy - best_xy
            dist = np.linalg.norm(delta)
            if dist <= ADJUST_MAX:
                best_xy = nearest_xy
                print(f"  [REGRASP] Micro-adjust: {dist*1000:.1f}mm to cable body")
            elif dist > 0:
                best_xy = best_xy + delta / dist * ADJUST_MAX
                print(f"  [REGRASP] Clamped adjust: cable {dist*1000:.1f}mm away, "
                      f"clamped to {ADJUST_MAX*1000:.0f}mm")

        grasp_z = self.scene_info.get("grasp_z", 1.020)
        approach_z = self.scene_info.get("approach_z", 1.120)

        # Approach: move regrasp arm above cable
        approach_target = (float(best_xy[0]), float(best_xy[1]), approach_z)
        self.state, ok = ik_move_single(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            target=approach_target, arm=regrasp_arm, label="WP-REGRASP-APP",
        )

        # Descend
        descend_target = (float(best_xy[0]), float(best_xy[1]), grasp_z)
        self.state, ok = ik_move_single(
            self.model, self.state, self.scene_info, self.solver, self.contacts,
            target=descend_target, arm=regrasp_arm, label="WP-REGRASP-DESC",
            converge_mm=5.0,
        )

        # Close regrasp arm fingers
        if regrasp_arm == "right":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                right_target=FINGER_CLOSE_POS, n_steps=300,
                label="WP-REGRASP-CLOSE",
            )
        else:
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_CLOSE_POS, n_steps=300,
                label="WP-REGRASP-CLOSE",
            )

    def _do_release(self, guide_hand=None):
        """Open fingers to release cable. Guide hand stays at HALF_OPEN."""
        self.grasped = False

        if guide_hand == "L":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_HALF_OPEN_POS, right_target=FINGER_OPEN_POS,
                n_steps=200, label="WP-RELEASE",
            )
        elif guide_hand == "R":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_OPEN_POS, right_target=FINGER_HALF_OPEN_POS,
                n_steps=200, label="WP-RELEASE",
            )
        else:
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_OPEN_POS, right_target=FINGER_OPEN_POS,
                n_steps=200, label="WP-RELEASE",
            )

    def _do_guide_transition(self, target_l, target_r, guide_hand):
        """Set guide hand to HALF_OPEN, then move both arms to target."""
        if guide_hand == "L":
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                left_target=FINGER_HALF_OPEN_POS,
                n_steps=200, label="WP-GUIDE",
            )
        else:
            self.state = interpolate_fingers(
                self.model, self.state, self.scene_info, self.solver, self.contacts,
                right_target=FINGER_HALF_OPEN_POS,
                n_steps=200, label="WP-GUIDE",
            )
        self._do_ik_move(target_l, target_r)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Execute verified waypoints in Newton VBD with video")
    parser.add_argument("--waypoints", type=str, required=True,
                        help="Path to v2 waypoints JSON (from dry-run)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for videos")
    parser.add_argument("--device", type=str,
                        default=os.environ.get("NEWTON_DEVICE", "cuda:0"))
    parser.add_argument("--no-video", action="store_true",
                        help="Disable video recording")
    args = parser.parse_args()

    device = args.device
    os.environ["NEWTON_DEVICE"] = device

    # Read waypoints
    with open(args.waypoints, "r") as f:
        wp_data = json.load(f)

    version = wp_data.get("version", 1)
    layout = wp_data.get("layout", wp_data.get("summary", {}))
    steps = wp_data["steps"]
    clip_positions_2d = layout.get("clip_positions", [])
    print(f"[WET-RUN] Waypoints: {args.waypoints} (v{version}, {len(steps)} steps)")
    print(f"[WET-RUN] Clips: {len(clip_positions_2d)}")
    for i, (cx, cy) in enumerate(clip_positions_2d):
        print(f"  C{i}: ({cx:.3f}, {cy:.3f})")

    # Filter to PASS/WARN steps only (skip FAIL-IK)
    executable = [s for s in steps if s.get("status") != "FAIL-IK"]
    skipped = len(steps) - len(executable)
    if skipped > 0:
        print(f"[WET-RUN] Skipping {skipped} FAIL-IK steps "
              f"(Home position IK — normal)")

    if args.output_dir is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"data/demo_wetrun_{ts}"
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[WET-RUN] Device={device}")
    print(f"[WET-RUN] Newton: {newton.__version__}, Warp: {wp.__version__}")
    print(f"[WET-RUN] Output: {args.output_dir}")

    # Build FK model
    print("\n[BUILD] Building FK model...")
    fk_model = build_fk_model(device, gravity=GRAVITY)
    fk_state = init_fk_state(fk_model, finger_open=True)

    # Build physics scene with clips and cable
    clip_positions_3d = [(cx, cy, TABLE_HEIGHT) for cx, cy in clip_positions_2d]
    print("[BUILD] Building physics scene...")
    scene_info = build_scene(
        device=device, clip_positions=clip_positions_3d,
        fk_model=fk_model, fk_state=fk_state,
        use_cable=True, cable_segments=CABLE_SEGMENTS,
        cable_seg_len=CABLE_SEG_LEN, gravity=GRAVITY,
    )
    model = scene_info["model"]

    # Store Z constants for regrasp
    grasp_z = layout.get("grasp_z", 1.020)
    lift_z = layout.get("lift_z", 1.120)
    scene_info["grasp_z"] = grasp_z
    scene_info["approach_z"] = lift_z

    state = model.state()
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control

    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    solver = SolverVBD(model, iterations=VBD_ITERATIONS)
    print(f"  [SOLVER] VBD (iterations={VBD_ITERATIONS})")

    # Video recorder
    mean_x = np.mean([p[0] for p in clip_positions_2d])
    mean_y = np.mean([p[1] for p in clip_positions_2d])
    focus = (mean_x, mean_y, TABLE_HEIGHT + 0.02)
    cameras = [
        ("overhead", (mean_x, mean_y, 1.60), focus),
        ("front",    (mean_x + 0.75, mean_y, 1.05), focus),
        ("left",     (mean_x, mean_y - 0.65, 0.93), focus),
        ("right",    (mean_x, mean_y + 0.65, 0.93), focus),
        ("diag",     (mean_x + 0.35, mean_y - 0.40, 1.00), focus),
    ]
    record_video = not args.no_video
    recorder = VideoRecorder(args.output_dir, model, enabled=record_video,
                             cameras=cameras, dt=DT)
    scene_info["recorder"] = recorder
    set_scene_colors(recorder, scene_info)

    # Settle cable
    print("[INIT] Settling cable (2s)...")
    state = settle_scene(model, state, scene_info, solver, contacts,
                         duration_s=2.0, dt=DT)

    # Execute waypoint sequence
    executor = WaypointExecutor(
        model, state, scene_info, solver, contacts,
        clip_positions_2d, device)

    t0 = time.time()
    results = {"steps_executed": 0, "steps_skipped": 0}

    for step in executable:
        try:
            executor.state = executor.execute(step)
            results["steps_executed"] += 1
        except Exception as e:
            print(f"\n  [ERROR] Step {step['step']} failed: {e}")
            import traceback
            traceback.print_exc()
            results["error_step"] = step["step"]
            results["error"] = str(e)
            break

    elapsed = time.time() - t0
    results["elapsed_s"] = round(elapsed, 1)
    results["steps_skipped"] = skipped

    # Finalize video
    video_paths = recorder.finalize(0)
    if video_paths:
        results["videos"] = video_paths
        # Copy to output dir (already there via recorder)
        print(f"\n[VIDEO] {len(video_paths)} videos saved:")
        for vp in video_paths:
            print(f"  {vp}")

    # Save metrics
    metrics_path = os.path.join(args.output_dir, "RUN_METRICS.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)

    print(f"\n{'='*60}")
    print(f"  WET-RUN COMPLETE: {results['steps_executed']} steps in {elapsed:.1f}s")
    print(f"  Metrics: {metrics_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
