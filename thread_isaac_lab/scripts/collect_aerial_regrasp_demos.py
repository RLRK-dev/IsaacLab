#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect AerialRegrasp demonstrations for DAPG — multi-episode wet-run.

Replays a scripted approach-and-grasp trajectory through NewtonAerialRegraspEnv,
recording (obs, action) pairs in env-matching format (42D obs, 12D act).

Scripted policy:
  Right arm: proportional control toward nearest cable point (pos + ori error from obs).
  Left arm (v18 cooperative): rotate cable to present graspable orientation for right arm
      (minimize ease_dist = quat_distance from BASE_HAND_DOWN_QUAT), maintain cable height.
  Finger close: auto-triggered by env when within pose_match threshold.

Phase 1 (approach):  Right arm moves toward cable. ~4-10 steps at 15mm/step.
Phase 2 (settle):    Right arm holds near cable, waits for auto-close + sustained clamp.
Phase 3 (hold):      Both arms hold. Record rest-state transitions.

Usage:
    source ~/env_isaaclab6/bin/activate
    cd ~/IsaacLab
    python thread_isaac_lab/scripts/collect_aerial_regrasp_demos.py \
        --num-episodes 20 --device cuda:0 \
        --output thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_v5.npz
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "envs"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"))

from newton_aerial_regrasp_env import NewtonAerialRegraspEnv
from newton_skill_env_base import compute_ori_error_axis_angle
from cable_orientation_utils import BASE_HAND_DOWN_QUAT
from task_config import LIFT_Z


# Action scaling (must match env)
POS_ACTION_SCALE = 0.015   # 15mm
ROT_ACTION_SCALE = 0.05    # ~2.9 deg
FINE_THRESHOLD = 0.050     # 50mm: adaptive scale kicks in below this
MIN_POS_SCALE = 0.0005     # 0.5mm: minimum adaptive scale

# Proportional gains (action units, not meters)
KP_POS = 0.6              # pos_error → pos_action gain (conservative, avoids overshoot)
KP_ORI = 0.4              # ori_error → rot_action gain
KP_EASE = 0.05            # v19: BC-visible cable presentation (~0.2 action units at 0.2rad error)
KP_HEIGHT = 0.01          # v18: cable height — must stay below clip
ACTION_CLIP = 1.0          # max normalized action magnitude per axis

S1B_SCHEMA_VERSION = "1.0.0"
S1B_SUPERVISOR_SCHEMA_VERSION = "s1b_post_release_supervisor_v1"
S1B_RETENTION_REPAIR_SCHEMA_VERSION = "s1b_retention_repair_v1"
S1B_GRASP_GEOMETRY_TELEMETRY_SCHEMA_VERSION = "s1b_grasp_geometry_telemetry_v2"
S1B_GRASP_GEOMETRY_TELEMETRY_ENV_CFG_KEY = "s1b_grasp_geometry_telemetry_enabled"
S1B_RETAINED_ZERO_VIDEO_RENDER_ENV_CFG_KEY = "s1b_retained_zero_video_render_enabled"
S1B_RETAINED_ZERO_VIDEO_CAMERA_SET_ENV_CFG_KEY = "s1b_retained_zero_video_camera_set"
S1B_RETAINED_ZERO_VIDEO_EPISODE_IDS_ENV_CFG_KEY = "s1b_retained_zero_video_episode_ids"
S1B_RETAINED_ZERO_VIDEO_SCHEMA_VERSION = "s1b_retained_zero_video_generation_v1"
S1B_RETAINED_ZERO_VIDEO_AUTO_SELECT_POLICIES = (
    "none",
    "first_actual_release",
    "first_retained_zero_release",
)
S1B_RETAINED_ZERO_VIDEO_DEFAULT_CAMERA_SET = "retained_zero_v1"
S1B_RETAINED_ZERO_VIDEO_DIAGNOSTIC_CAMERA_SET = "retained_zero_diagnostic_v2"
S1B_RETAINED_ZERO_VIDEO_BASE_CAMERA_SPECS = (
    ("overhead", (0.35, -0.05, 1.50), (0.35, -0.05, 0.80)),
    ("front", (1.00, -0.05, 1.05), (0.30, -0.05, 0.82)),
    ("right", (0.35, 0.55, 0.93), (0.35, -0.05, 0.82)),
    ("left", (0.35, -0.65, 0.93), (0.35, -0.05, 0.82)),
    ("back", (-0.30, -0.05, 1.05), (0.30, -0.05, 0.82)),
)
S1B_RETAINED_ZERO_VIDEO_DIAGNOSTIC_CAMERA_SPECS = S1B_RETAINED_ZERO_VIDEO_BASE_CAMERA_SPECS + (
    # Close views are diagnostic-only: they help inspect right-holding / left-release geometry.
    ("holding_right_close", (0.48, 0.34, 0.99), (0.34, 0.12, 0.87)),
    ("release_left_close", (0.48, -0.44, 0.99), (0.34, -0.16, 0.87)),
    ("cable_low_oblique", (0.78, 0.08, 0.92), (0.34, 0.00, 0.86)),
)
S1B_RETAINED_ZERO_VIDEO_CAMERA_SPECS_BY_SET = {
    S1B_RETAINED_ZERO_VIDEO_DEFAULT_CAMERA_SET: S1B_RETAINED_ZERO_VIDEO_BASE_CAMERA_SPECS,
    S1B_RETAINED_ZERO_VIDEO_DIAGNOSTIC_CAMERA_SET: S1B_RETAINED_ZERO_VIDEO_DIAGNOSTIC_CAMERA_SPECS,
}
S1B_GRASP_GEOMETRY_TELEMETRY_PRE_RELEASE_STEPS = 4
S1B_GRASP_GEOMETRY_TELEMETRY_POST_RELEASE_STEPS = 34
S1B_GRASP_GEOMETRY_TELEMETRY_MAX_WINDOW_STEPS = 40
S1B_RETENTION_REPAIR_CONTROL_ARM_NONE = "none"
S1B_RETENTION_REPAIR_CONTROL_ARM_SUPERVISOR_OFF = "supervisor_off"
S1B_RETENTION_REPAIR_CONTROL_ARM_ACTION_SPACE_HOLD_V1 = "action_space_hold_v1"
S1B_RETENTION_REPAIR_CONTROL_ARM_RELEASE_HANDOFF_LEFT_TARGET_BIAS_V1 = "release_handoff_left_target_bias_v1"
S1B_LABEL_STRING_KEYS = {
    "schema_version",
    "s1b_schema_version",
    "policy_id",
    "runner_sha",
    "dataset_source",
    "release_class",
    "release_detection_source",
    "terminal_break_reason_source",
    "post_release_terminal_break_reason",
}
S1B_LABEL_STRING_DTYPE_OVERRIDES = {
    "dataset_source": "<U128",
    "policy_id": "<U128",
}
S1B_SUPERVISOR_LABEL_STRING_KEYS = {
    "s1b_supervisor_fail_closed_reason",
    "s1b_retention_repair_control_arm",
}
S1B_LABEL_FLOAT_KEYS = {
    "retention_horizon_seconds",
}
S1B_SUPERVISOR_LABEL_FLOAT_KEYS = {
    "s1b_retention_repair_left_action_scale",
    "s1b_retention_repair_transient_blend",
    "s1b_retention_repair_target_blend",
    "s1b_retention_repair_left_target_offset_x",
    "s1b_retention_repair_left_target_offset_y",
    "s1b_retention_repair_left_target_offset_z",
}
S1B_RELEASE_LABEL_KEYS = (
    "schema_version",
    "s1b_schema_version",
    "episode_id",
    "world_id",
    "seed",
    "policy_id",
    "runner_sha",
    "dataset_source",
    "configured_release_step",
    "observed_release_step",
    "actual_release_event",
    "release_class",
    "release_detection_source",
    "release_support_removed",
    "release_gripper_opened_or_force_reduced",
    "terminal_step",
    "first_done_step",
    "terminal_before_configured_release",
    "steps_until_configured_release",
    "terminal_break_reason_source",
    "retention_horizon_steps",
    "retention_horizon_seconds",
    "post_release_steps_observed",
    "post_release_retained_horizon",
    "post_release_cable_drop",
    "post_release_explosion",
    "post_release_terminal_break_reason",
    "retained_after_release_label",
    "kinematic_support_enabled",
    "fixed_support_enabled",
    "hidden_support_enabled",
    "inv_mass_zero_support_enabled",
    "direct_sim_state_write_enabled",
    "scripted_or_oracle_support_enabled",
    "active_at_completion_counted_as_success",
    "hold_to_completion_counted_as_success",
    "external_assist_enabled",
    "no_crutch_product_label_eligible",
    "release_real_observable",
    "retention_real_observable",
    "cable_drop_real_observable",
    "explosion_or_instability_real_observable",
    "sim_only_field_used_for_product_label",
)
S1B_SUPERVISOR_LABEL_KEYS = (
    "s1b_post_release_supervisor_enabled",
    "s1b_release_transient_smoothing_enabled",
    "s1b_retention_repair_enabled",
    "s1b_retention_repair_control_arm",
    "s1b_retention_repair_supervisor_off_control_arm",
    "s1b_retention_repair_release_handoff_left_target_bias_arm",
    "s1b_retention_repair_assisted_row",
    "s1b_retention_repair_unassisted_row",
    "s1b_retention_repair_handoff_step",
    "s1b_retention_repair_authority_window_steps",
    "s1b_retention_repair_target_bias_env_cfg_present",
    "s1b_retention_repair_target_blend",
    "s1b_retention_repair_left_target_offset_x",
    "s1b_retention_repair_left_target_offset_y",
    "s1b_retention_repair_left_target_offset_z",
    "s1b_retention_repair_left_action_scale",
    "s1b_retention_repair_transient_blend",
    "s1b_supervisor_real_observable_only",
    "s1b_supervisor_no_crutch_enforced",
    "s1b_supervisor_window_steps",
    "s1b_release_transient_smoothing_steps",
    "s1b_supervisor_activation_step",
    "s1b_supervisor_steps_applied",
    "s1b_transient_smoothing_steps_applied",
    "s1b_supervisor_fail_closed",
    "s1b_supervisor_fail_closed_reason",
)

S1B_REQUIRED_PER_WORLD_KEYS = (
    "s1a_post_release_phase",
    "terminal_status_cable_not_dropped",
    "terminal_break_reason",
    "kinematic_left_finger_support_enabled",
    "s1a_active_at_completion_credit_authorized",
    "s1a_hold_to_completion_credit_authorized",
    "s1a_sim_only_crutch_credit_authorized",
)
S1B_ALLOWED_ENV_CFG_KEYS = {
    "d0_control_arm",
    "d0_control_force_scale",
    "d0_control_force_scale_min",
    "d0_control_release_step",
    "d0_control_target_blend",
    "d0_control_left_target_offset_xyz",
    "d0_human_rs_predicate_confirmed",
    S1B_GRASP_GEOMETRY_TELEMETRY_ENV_CFG_KEY,
    S1B_RETAINED_ZERO_VIDEO_RENDER_ENV_CFG_KEY,
    S1B_RETAINED_ZERO_VIDEO_CAMERA_SET_ENV_CFG_KEY,
    S1B_RETAINED_ZERO_VIDEO_EPISODE_IDS_ENV_CFG_KEY,
    "s1a_release_readiness_reward_enabled",
    "s1a_release_readiness_observation_enabled",
    "s1a_curriculum_metadata_enabled",
}
S1B_REQUIRED_RELEASE_ENV_CFG_KEYS = (
    "d0_control_arm",
    "d0_control_release_step",
    "d0_human_rs_predicate_confirmed",
    "s1a_curriculum_metadata_enabled",
)
S1B_PRODUCT_RELEASE_ARMS = {
    "oracle_pose_or_force_hold",
    "release_ramp_5",
    "release_ramp_10",
    "impedance_handoff_contact_force_limited",
    "support_removal_ablation",
}


def _parse_env_cfg_json(raw_value):
    """Parse an allowlisted env config JSON object for release telemetry."""
    if not raw_value:
        return {}
    try:
        cfg = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--env-cfg-json must be valid JSON: {exc}") from exc
    if not isinstance(cfg, dict):
        raise ValueError("--env-cfg-json must decode to a JSON object")
    unknown = sorted(set(cfg) - S1B_ALLOWED_ENV_CFG_KEYS)
    if unknown:
        raise ValueError("--env-cfg-json contains unreviewed keys: " + ", ".join(unknown))
    return cfg


def _s1b_retained_zero_video_render_requested(args, env_cfg):
    """Return whether the retained-zero video render path is explicitly enabled."""
    return bool(
        args.s1b_retained_zero_video_render
        or env_cfg.get(S1B_RETAINED_ZERO_VIDEO_RENDER_ENV_CFG_KEY, False)
    )


def _parse_s1b_retained_zero_video_episode_ids(raw_value):
    """Parse a comma-separated retained-zero video episode id allowlist."""
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, (list, tuple)):
        values = raw_value
    else:
        values = str(raw_value).split(",")
    parsed = set()
    for value in values:
        if str(value).strip() == "":
            continue
        parsed.add(int(value))
    return parsed


def _s1b_retained_zero_video_episode_selected(episode_id, selected_episode_ids):
    """Return whether one episode should be rendered under the reviewed allowlist."""
    return selected_episode_ids is None or int(episode_id) in selected_episode_ids


def _s1b_retained_zero_video_capture_episode(episode_id, selected_episode_ids, auto_select_policy):
    """Return whether the recorder should capture one episode for later filtering."""
    if auto_select_policy != "none":
        return True
    return _s1b_retained_zero_video_episode_selected(episode_id, selected_episode_ids)


def _select_s1b_retained_zero_video_save_episode_ids(label_rows, auto_select_policy):
    """Choose saved episode ids after labels are known."""
    if auto_select_policy == "none":
        return None
    if auto_select_policy == "first_actual_release":
        candidates = [row for row in label_rows if bool(row.get("actual_release_event"))]
    elif auto_select_policy == "first_retained_zero_release":
        candidates = [
            row
            for row in label_rows
            if bool(row.get("actual_release_event"))
            and not bool(row.get("retained_after_release_label"))
        ]
    else:
        raise ValueError(f"Unsupported retained-zero video auto-select policy: {auto_select_policy}")
    if not candidates:
        raise RuntimeError(
            "S1B retained-zero video auto-select found no matching episode; "
            "no videos were saved"
        )
    return {int(min(candidates, key=lambda row: int(row["episode_id"]))["episode_id"])}


def _validate_s1b_retained_zero_video_args(args, env_cfg):
    """Fail closed unless future retained-zero video generation is explicitly paired with S1B labels."""
    if not _s1b_retained_zero_video_render_requested(args, env_cfg):
        return
    if not args.emit_s1b_release_retention_labels:
        raise ValueError("S1B retained-zero video render requires --emit-s1b-release-retention-labels")
    if not args.s1b_real_observability_attested:
        raise ValueError("S1B retained-zero video render requires --s1b-real-observability-attested")
    if not args.s1b_retained_zero_video_output_root:
        raise ValueError("S1B retained-zero video render requires --s1b_retained_zero_video_output_root")
    if os.path.exists(args.s1b_retained_zero_video_output_root):
        raise ValueError("S1B retained-zero video output root must be fresh and absent")
    if "cuda:1" in args.device.lower():
        raise ValueError("S1B retained-zero video render refuses cuda:1")
    if int(args.world_count) != 1:
        raise ValueError("S1B retained-zero video render requires --world-count 1 for episode-specific inspection")
    if int(args.s1b_retained_zero_video_fps) <= 0:
        raise ValueError("--s1b_retained_zero_video_fps must be positive")
    if int(args.s1b_retained_zero_video_frame_stride) <= 0:
        raise ValueError("--s1b_retained_zero_video_frame_stride must be positive")
    if int(args.s1b_retained_zero_video_post_terminal_frames) < 0:
        raise ValueError("--s1b_retained_zero_video_post_terminal_frames must be non-negative")
    if args.s1b_retained_zero_video_auto_select_policy not in S1B_RETAINED_ZERO_VIDEO_AUTO_SELECT_POLICIES:
        raise ValueError(
            "--s1b_retained_zero_video_auto_select_policy must be one of: "
            + ", ".join(S1B_RETAINED_ZERO_VIDEO_AUTO_SELECT_POLICIES)
        )
    raw_episode_ids = env_cfg.get(
        S1B_RETAINED_ZERO_VIDEO_EPISODE_IDS_ENV_CFG_KEY,
        args.s1b_retained_zero_video_episode_ids,
    )
    if (
        args.s1b_retained_zero_video_auto_select_policy != "none"
        and _parse_s1b_retained_zero_video_episode_ids(raw_episode_ids)
    ):
        raise ValueError(
            "S1B retained-zero video auto-selection cannot be combined with explicit episode ids"
        )
    camera_set = env_cfg.get(
        S1B_RETAINED_ZERO_VIDEO_CAMERA_SET_ENV_CFG_KEY,
        args.s1b_retained_zero_video_camera_set,
    )
    if camera_set not in S1B_RETAINED_ZERO_VIDEO_CAMERA_SPECS_BY_SET:
        raise ValueError(
            "S1B retained-zero video camera set must be one of: "
            + ", ".join(sorted(S1B_RETAINED_ZERO_VIDEO_CAMERA_SPECS_BY_SET))
        )


def _s1b_retained_zero_video_camera_angles(pos, tgt):
    """Return Newton ViewerGL pitch/yaw angles for one retained-zero camera."""
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, dz / norm))))
    yaw = math.degrees(math.atan2(dy, dx))
    return pitch, yaw


def _s1b_retained_zero_video_json_safe(value):
    """Convert NumPy scalar values to JSON-safe Python values for manifests."""
    if isinstance(value, np.generic):
        return value.item()
    return value


def _s1b_retained_zero_video_label_row(label):
    """Return generated-label metadata for post-judge comparison, not blind judging."""
    keys = (
        "episode_id",
        "world_id",
        "release_class",
        "actual_release_event",
        "post_release_cable_drop",
        "post_release_explosion",
        "post_release_terminal_break_reason",
        "post_release_retained_horizon",
        "retained_after_release_label",
        "no_crutch_product_label_eligible",
        "retention_real_observable",
        "sim_only_field_used_for_product_label",
    )
    return {key: _s1b_retained_zero_video_json_safe(label.get(key)) for key in keys}


class S1BRetainedZeroVideoRecorder:
    """Generation-only retained-zero video recorder; it performs no video judgment."""

    def __init__(self, *, model, output_root, camera_set, fps, frame_stride):
        if camera_set not in S1B_RETAINED_ZERO_VIDEO_CAMERA_SPECS_BY_SET:
            raise ValueError("Unsupported retained-zero video camera set")
        from newton.viewer import ViewerGL
        import warp as wp

        self.viewer = ViewerGL(width=640, height=480, vsync=False, headless=True)
        self.viewer.set_model(model)
        self.viewer.camera.near = 0.01
        self.viewer.camera.far = 10.0
        self.output_root = output_root
        self.fps = int(fps)
        self.frame_stride = int(frame_stride)
        self._wp = wp
        self._cameras = []
        for name, pos, target in S1B_RETAINED_ZERO_VIDEO_CAMERA_SPECS_BY_SET[camera_set]:
            pitch, yaw = _s1b_retained_zero_video_camera_angles(pos, target)
            self._cameras.append((name, wp.vec3(*pos), pitch, yaw))
        self._frames = {}

    def capture(self, state, *, episode_ids, step_i):
        """Capture generation frames for selected episodes without judging them."""
        if step_i % self.frame_stride != 0:
            return
        for episode_id in episode_ids:
            episode_frames = self._frames.setdefault(int(episode_id), {name: [] for name, _, _, _ in self._cameras})
            for name, pos, pitch, yaw in self._cameras:
                self.viewer.set_camera(pos, pitch, yaw)
                self.viewer.begin_frame(float(step_i))
                self.viewer.log_state(state)
                self.viewer.end_frame()
                episode_frames[name].append(self.viewer.get_frame().numpy().copy())

    def save(self, *, selected_episode_ids=None):
        """Write videos and return a generation manifest without physical verdicts."""
        from PIL import Image

        selected_episode_ids = (
            None if selected_episode_ids is None else {int(episode_id) for episode_id in selected_episode_ids}
        )
        videos = []
        videos_root = os.path.join(self.output_root, "videos")
        os.makedirs(videos_root, exist_ok=True)
        for episode_id, camera_frames in sorted(self._frames.items()):
            if selected_episode_ids is not None and int(episode_id) not in selected_episode_ids:
                continue
            for camera_name, frames in sorted(camera_frames.items()):
                if not frames:
                    continue
                frames_dir = os.path.join(videos_root, f"_frames_ep{episode_id}_{camera_name}")
                os.makedirs(frames_dir, exist_ok=True)
                for frame_idx, frame in enumerate(frames):
                    Image.fromarray(frame).save(os.path.join(frames_dir, f"frame_{frame_idx:05d}.png"))
                video_path = os.path.join(videos_root, f"episode_{episode_id}_{camera_name}.mp4")
                command = [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(self.fps),
                    "-i",
                    os.path.join(frames_dir, "frame_%05d.png"),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-crf",
                    "23",
                    video_path,
                ]
                status = "PASS"
                stderr = ""
                try:
                    subprocess.run(command, capture_output=True, check=True, timeout=120)
                    shutil.rmtree(frames_dir, ignore_errors=True)
                except Exception as exc:  # noqa: BLE001 - manifest records generation failure evidence.
                    status = "VIDEO_GENERATION_FAIL"
                    stderr = repr(exc)
                    video_path = frames_dir
                videos.append({
                    "camera_name": camera_name,
                    "episode_id": int(episode_id),
                    "fps": self.fps,
                    "frame_count": len(frames),
                    "frame_stride": self.frame_stride,
                    "generation_status": status,
                    "generation_stderr": stderr,
                    "video_path": video_path,
                })
        return videos


def _write_s1b_retained_zero_video_manifests(
    *,
    output_root,
    npz_path,
    video_manifest,
    label_rows,
    args,
    collection_counts,
):
    """Write generation and blind-bundle manifests; do not produce video judgments."""
    os.makedirs(output_root, exist_ok=True)
    generation_manifest = {
        "schema_version": S1B_RETAINED_ZERO_VIDEO_SCHEMA_VERSION,
        "executor_role": "GENERATION_ONLY_NO_VIDEO_JUDGMENT",
        "codex_video_judgment_valid": False,
        "codex_video_judgment_disposition": "DISCARDED_IF_PRESENT",
        "independent_video_judge_required": True,
        "independent_video_judge_protocol": "blind_physical_observation_then_separate_label_comparison",
        "blind_bundle_must_hide_expected_results": True,
        "deterministic_count_reproduction_status": "PENDING_EXTERNAL_VALIDATION",
        "deterministic_count_mismatch_stop": "NONDETERMINISTIC_REPLAY_BLOCKED",
        "baseline_selection": "d245_seed42_same_env_cfg_same_protected_shas_same_scripted_collector",
        "npz_path": npz_path,
        "collection_counts": collection_counts,
        "label_rows_for_post_judge_comparison": label_rows,
        "video_auto_select_policy": args.s1b_retained_zero_video_auto_select_policy,
        "saved_episode_ids": sorted({int(item["episode_id"]) for item in video_manifest}),
        "videos": video_manifest,
        "collector_sha": args.s1b_collector_sha,
        "env_sha": args.s1b_env_sha,
        "task_config_sha": args.s1b_task_config_sha,
        "contract_sha": args.s1b_contract_sha,
        "claim_flags": {
            "physical_grasp_claim": False,
            "product_go": False,
            "production_claim": False,
            "sim2real_success_claim": False,
            "stage2_claim": False,
            "troot_95_claim": False,
        },
    }
    blind_bundle = {
        "schema_version": S1B_RETAINED_ZERO_VIDEO_SCHEMA_VERSION,
        "judge_stage": "BLIND_PHYSICAL_OBSERVATION_ONLY",
        "must_not_read_run_metrics_or_expected_results": True,
        "videos": [
            {
                "camera_name": item["camera_name"],
                "episode_id": item["episode_id"],
                "fps": item["fps"],
                "frame_count": item["frame_count"],
                "frame_stride": item["frame_stride"],
                "video_path": item["video_path"],
            }
            for item in video_manifest
        ],
        "forbidden_fields": [
            "actual_release_event",
            "post_release_cable_drop",
            "post_release_explosion",
            "retained_after_release_label",
            "expected_d245_counts",
            "run_metrics",
        ],
    }
    with open(os.path.join(output_root, "s1b_retained_zero_video_generation_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(generation_manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    with open(os.path.join(output_root, "s1b_retained_zero_video_blind_bundle_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(blind_bundle, f, indent=2, sort_keys=True)
        f.write("\n")


def _validate_s1b_release_env_cfg(env_cfg):
    """Fail closed unless S1B labels can observe an actual release surface."""
    missing = [key for key in S1B_REQUIRED_RELEASE_ENV_CFG_KEYS if key not in env_cfg]
    if missing:
        raise ValueError("S1B labels require env cfg keys: " + ", ".join(missing))
    d0_arm = str(env_cfg.get("d0_control_arm") or "")
    if d0_arm not in S1B_PRODUCT_RELEASE_ARMS:
        raise ValueError(
            "S1B labels require d0_control_arm to be a reviewed product release arm "
            f"(got {d0_arm!r})"
        )
    if not bool(env_cfg.get("d0_human_rs_predicate_confirmed")):
        raise ValueError("S1B labels require d0_human_rs_predicate_confirmed=true")
    release_step = int(env_cfg.get("d0_control_release_step"))
    if release_step < 0:
        raise ValueError("S1B labels require d0_control_release_step >= 0")
    if not bool(env_cfg.get("s1a_curriculum_metadata_enabled")):
        raise ValueError("S1B labels require s1a_curriculum_metadata_enabled=true")
    if bool(env_cfg.get("s1a_release_readiness_reward_enabled")) and not bool(
        env_cfg.get("s1a_release_readiness_observation_enabled")
    ):
        raise ValueError(
            "s1a_release_readiness_reward_enabled=true requires "
            "s1a_release_readiness_observation_enabled=true"
        )


def _s1b_configured_release_step(env_cfg):
    """Return reviewed configured release step for S1B provenance."""
    if "d0_control_release_step" not in env_cfg:
        return -1
    return int(env_cfg["d0_control_release_step"])


def compute_scripted_action(obs_np, action_noise_xy=0.0):
    """Compute 12D action from 42D obs using proportional control.

    Right arm: proportional approach toward cable target.
    Left arm (v18 cooperative): rotate to present cable for right arm,
        maintain cable height at LIFT_Z.

    Args:
        obs_np: [42] observation array.
        action_noise_xy: Gaussian sigma for XY action noise (action units).

    Returns:
        [12] action array (normalized, before env scaling).
    """
    action = np.zeros(12, dtype=np.float32)

    # Right arm position error: obs[33:36] = clamp_r_pos - seg_pos
    # We want to move toward target, so action = -error / scale * gain
    pos_error = obs_np[33:36]  # [3] meters
    dist_r = np.linalg.norm(pos_error)
    r_pos_scale = max(MIN_POS_SCALE, POS_ACTION_SCALE * min(1.0, dist_r / FINE_THRESHOLD))
    pos_action = -pos_error / r_pos_scale * KP_POS
    pos_action = np.clip(pos_action, -ACTION_CLIP, ACTION_CLIP)
    action[0:3] = pos_action

    # Right arm orientation error: obs[30:33] = axis-angle from hand to grasp target
    # We want to rotate toward target, so action = error / scale * gain
    # Note: ori_error_aa IS the rotation needed (hand→target), so action = +error
    ori_error = obs_np[30:33]  # [3] radians
    rot_action = ori_error / ROT_ACTION_SCALE * KP_ORI
    rot_action = np.clip(rot_action, -ACTION_CLIP, ACTION_CLIP)
    action[3:6] = rot_action

    # Left arm v18: cooperative cable presentation
    # Goal: rotate cable so tangent at R target → grasp quat close to BASE_HAND_DOWN
    # obs[19:23] = target cable segment quat (= compute_hand_quat_for_cable(tangent))
    seg_quat = obs_np[19:23]  # [4] xyzw
    # Ease error: rotation from BASE_HAND_DOWN to current cable target orientation
    # Negative = rotate LEFT arm to REDUCE this error (push cable toward ideal)
    ease_error_aa = compute_ori_error_axis_angle(BASE_HAND_DOWN_QUAT, seg_quat)
    rot_action_l_ease = -ease_error_aa / ROT_ACTION_SCALE * KP_EASE
    rot_action_l_ease = np.clip(rot_action_l_ease, -ACTION_CLIP, ACTION_CLIP)
    action[9:12] = rot_action_l_ease

    # Left arm Z: maintain cable height at R target zone
    cable_target_z = obs_np[18]   # seg_pos Z (right arm's target cable segment)
    height_error = LIFT_Z - cable_target_z  # positive if cable too low
    pos_action_l_z = height_error / POS_ACTION_SCALE * KP_HEIGHT
    action[8] = np.clip(pos_action_l_z, -0.3, 0.3)

    # Action noise: XY for both arms
    if action_noise_xy > 0:
        noise = np.random.randn(4) * action_noise_xy
        action[0] += noise[0]  # right dx
        action[1] += noise[1]  # right dy
        action[6] += noise[2]  # left dx
        action[7] += noise[3]  # left dy

    return action


def _s1b_supervisor_requested(args):
    """Return whether any opt-in S1B post-release control repair is requested."""
    return bool(
        args.s1b_post_release_supervisor
        or args.s1b_release_transient_smoothing
        or args.s1b_retention_repair
        or args.s1b_retention_repair_control_arm != S1B_RETENTION_REPAIR_CONTROL_ARM_NONE
    )


def _s1b_retention_repair_requested(args):
    """Return whether the v1 retention-repair control-arm surface is requested."""
    return bool(
        args.s1b_retention_repair
        or args.s1b_retention_repair_control_arm != S1B_RETENTION_REPAIR_CONTROL_ARM_NONE
    )


def _s1b_release_handoff_left_target_bias_requested(args):
    """Return whether the release-handoff target-bias repair arm is requested."""
    return (
        args.s1b_retention_repair_control_arm
        == S1B_RETENTION_REPAIR_CONTROL_ARM_RELEASE_HANDOFF_LEFT_TARGET_BIAS_V1
    )


def _s1b_release_handoff_left_target_bias_values(env_cfg):
    """Return reviewed target-bias provenance from allowlisted env cfg."""
    target_blend = float(env_cfg.get("d0_control_target_blend", 0.0))
    offset_raw = env_cfg.get("d0_control_left_target_offset_xyz", (0.0, 0.0, 0.0))
    if not isinstance(offset_raw, (list, tuple)) or len(offset_raw) != 3:
        raise ValueError(
            "release_handoff_left_target_bias_v1 requires "
            "d0_control_left_target_offset_xyz as a length-3 list"
        )
    left_target_offset = tuple(float(v) for v in offset_raw)
    return target_blend, left_target_offset


def _validate_s1b_release_handoff_left_target_bias_env_cfg(args, env_cfg):
    """Fail closed unless release-handoff target-bias provenance is explicit."""
    if not _s1b_release_handoff_left_target_bias_requested(args):
        return
    required = ("d0_control_target_blend", "d0_control_left_target_offset_xyz")
    missing = [key for key in required if key not in env_cfg]
    if missing:
        raise ValueError(
            "release_handoff_left_target_bias_v1 requires env cfg keys: " + ", ".join(missing)
        )
    target_blend, left_target_offset = _s1b_release_handoff_left_target_bias_values(env_cfg)
    if not (0.0 < target_blend <= 1.0):
        raise ValueError("release_handoff_left_target_bias_v1 requires d0_control_target_blend in (0, 1]")
    if not any(abs(v) > 0.0 for v in left_target_offset):
        raise ValueError("release_handoff_left_target_bias_v1 requires a nonzero left target offset")


def _s1b_grasp_geometry_telemetry_requested(args):
    """Return whether S1B grasp-geometry telemetry persistence is requested."""
    return bool(args.emit_s1b_grasp_geometry_telemetry)


def _validate_s1b_grasp_geometry_telemetry_args(args, env_cfg):
    """Validate default-off S1B geometry telemetry request parameters."""
    if not _s1b_grasp_geometry_telemetry_requested(args):
        return
    if not args.emit_s1b_release_retention_labels:
        raise ValueError("S1B geometry telemetry requires --emit-s1b-release-retention-labels")
    if not args.s1b_real_observability_attested:
        raise ValueError("S1B geometry telemetry requires --s1b-real-observability-attested")
    if not bool(env_cfg.get(S1B_GRASP_GEOMETRY_TELEMETRY_ENV_CFG_KEY, False)):
        raise ValueError(
            "S1B geometry telemetry requires env cfg "
            f"{S1B_GRASP_GEOMETRY_TELEMETRY_ENV_CFG_KEY}=true"
        )
    expected = {
        "--s1b-telemetry-history-pre-release-steps": (
            args.s1b_telemetry_history_pre_release_steps,
            S1B_GRASP_GEOMETRY_TELEMETRY_PRE_RELEASE_STEPS,
        ),
        "--s1b-telemetry-history-post-release-steps": (
            args.s1b_telemetry_history_post_release_steps,
            S1B_GRASP_GEOMETRY_TELEMETRY_POST_RELEASE_STEPS,
        ),
        "--s1b-telemetry-history-max-window-steps": (
            args.s1b_telemetry_history_max_window_steps,
            S1B_GRASP_GEOMETRY_TELEMETRY_MAX_WINDOW_STEPS,
        ),
    }
    mismatches = [name for name, (actual, want) in expected.items() if int(actual) != int(want)]
    if mismatches:
        raise ValueError("S1B geometry telemetry window values are fixed for v1: " + ", ".join(mismatches))


def _validate_s1b_supervisor_args(args):
    """Validate opt-in S1B supervisor controls before env construction."""
    if not _s1b_supervisor_requested(args):
        return
    if not args.emit_s1b_release_retention_labels:
        raise ValueError("S1B supervisor controls require --emit-s1b-release-retention-labels")
    if not args.s1b_real_observability_attested:
        raise ValueError("S1B supervisor controls require --s1b-real-observability-attested")
    if args.s1b_post_release_supervisor_window_steps <= 0:
        raise ValueError("--s1b-post-release-supervisor-window-steps must be positive")
    if args.s1b_release_transient_smoothing_steps < 0:
        raise ValueError("--s1b-release-transient-smoothing-steps must be non-negative")
    if args.s1b_retention_repair_handoff_steps < 0:
        raise ValueError("--s1b-retention-repair-handoff-steps must be non-negative")
    if args.s1b_retention_repair_authority_window_steps <= 0:
        raise ValueError("--s1b-retention-repair-authority-window-steps must be positive")
    if not (0.0 <= args.s1b_transient_action_blend <= 1.0):
        raise ValueError("--s1b-transient-action-blend must be in [0, 1]")
    if not (0.0 <= args.s1b_post_release_left_action_scale <= 1.0):
        raise ValueError("--s1b-post-release-left-action-scale must be in [0, 1]")
    if not (0.0 <= args.s1b_retention_repair_left_action_scale <= 1.0):
        raise ValueError("--s1b-retention-repair-left-action-scale must be in [0, 1]")
    if not (0.0 <= args.s1b_retention_repair_transient_blend <= 1.0):
        raise ValueError("--s1b-retention-repair-transient-blend must be in [0, 1]")


def _s1b_post_release_window_active(label, step_i, args):
    """Return whether the current step is inside the reviewed retention window."""
    configured_step = int(label["configured_release_step"])
    observed_step = int(label["observed_release_step"])
    window_steps = int(args.s1b_post_release_supervisor_window_steps)
    if observed_step >= 0:
        return observed_step <= int(step_i) < observed_step + window_steps
    if configured_step >= 0:
        return configured_step <= int(step_i) < configured_step + window_steps
    return False


def _s1b_release_transient_active(label, step_i, args):
    """Return whether the current step is inside the release-transient window."""
    if int(args.s1b_release_transient_smoothing_steps) <= 0:
        return False
    configured_step = int(label["configured_release_step"])
    observed_step = int(label["observed_release_step"])
    anchor_step = observed_step if observed_step >= 0 else configured_step
    if anchor_step < 0:
        return False
    transient_steps = int(args.s1b_release_transient_smoothing_steps)
    return anchor_step <= int(step_i) < anchor_step + transient_steps


def _apply_s1b_post_release_control_repair(action, label, step_i, args):
    """Apply default-off S1B post-release supervisor and transient smoothing."""
    if not _s1b_supervisor_requested(args):
        return action
    if label is None:
        raise RuntimeError("S1B supervisor controls require initialized S1B labels")
    if int(label["configured_release_step"]) < 0:
        label["s1b_supervisor_fail_closed"] = True
        label["s1b_supervisor_fail_closed_reason"] = "missing_configured_release_step"
        return action

    repaired = action.copy()
    supervisor_active = (
        args.s1b_post_release_supervisor
        and _s1b_post_release_window_active(label, step_i, args)
    )
    smoothing_active = (
        args.s1b_release_transient_smoothing
        and _s1b_release_transient_active(label, step_i, args)
    )
    if supervisor_active and int(label["s1b_supervisor_activation_step"]) < 0:
        label["s1b_supervisor_activation_step"] = int(step_i)

    if supervisor_active:
        # Preserve left hold by damping only robot-commanded left-arm deltas.
        # This does not add hidden support or write direct simulator state.
        repaired[6:12] *= float(args.s1b_post_release_left_action_scale)
        label["s1b_supervisor_steps_applied"] += 1

    if smoothing_active:
        repaired = (float(args.s1b_transient_action_blend) * repaired).astype(np.float32)
        label["s1b_transient_smoothing_steps_applied"] += 1

    if _s1b_retention_repair_requested(args):
        control_arm = args.s1b_retention_repair_control_arm
        if control_arm == S1B_RETENTION_REPAIR_CONTROL_ARM_SUPERVISOR_OFF:
            label["s1b_retention_repair_supervisor_off_control_arm"] = True
            label["s1b_retention_repair_unassisted_row"] = True
        elif control_arm == S1B_RETENTION_REPAIR_CONTROL_ARM_ACTION_SPACE_HOLD_V1:
            handoff_steps = int(args.s1b_retention_repair_handoff_steps)
            observed_step = int(label["observed_release_step"])
            configured_step = int(label["configured_release_step"])
            anchor_step = observed_step if observed_step >= 0 else configured_step
            in_handoff = anchor_step >= 0 and anchor_step <= int(step_i) < anchor_step + handoff_steps
            if in_handoff and int(label["s1b_retention_repair_handoff_step"]) < 0:
                label["s1b_retention_repair_handoff_step"] = int(step_i)
            if in_handoff:
                repaired = (
                    float(args.s1b_retention_repair_transient_blend) * repaired
                ).astype(np.float32)
                label["s1b_transient_smoothing_steps_applied"] += 1

            repair_window = int(args.s1b_retention_repair_authority_window_steps)
            in_repair_window = (
                anchor_step >= 0 and anchor_step <= int(step_i) < anchor_step + repair_window
            )
            if in_repair_window:
                repaired[6:12] *= float(args.s1b_retention_repair_left_action_scale)
                label["s1b_supervisor_steps_applied"] += 1
                label["s1b_retention_repair_assisted_row"] = True
                label["s1b_retention_repair_unassisted_row"] = False
        elif control_arm == S1B_RETENTION_REPAIR_CONTROL_ARM_RELEASE_HANDOFF_LEFT_TARGET_BIAS_V1:
            observed_step = int(label["observed_release_step"])
            configured_step = int(label["configured_release_step"])
            anchor_step = observed_step if observed_step >= 0 else configured_step
            handoff_steps = int(args.s1b_retention_repair_handoff_steps)
            in_handoff = anchor_step >= 0 and anchor_step <= int(step_i) < anchor_step + handoff_steps
            if in_handoff and int(label["s1b_retention_repair_handoff_step"]) < 0:
                label["s1b_retention_repair_handoff_step"] = int(step_i)
            label["s1b_retention_repair_release_handoff_left_target_bias_arm"] = True
            label["s1b_retention_repair_assisted_row"] = True
            label["s1b_retention_repair_unassisted_row"] = False
            label["scripted_or_oracle_support_enabled"] = True
            label["external_assist_enabled"] = True
            label["no_crutch_product_label_eligible"] = False
            label["retained_after_release_label"] = False

    return np.clip(repaired, -ACTION_CLIP, ACTION_CLIP)


def _world_value(log_per_world, key, world_idx):
    """Return one world-indexed value from an env ``log_per_world`` field."""
    if key not in log_per_world:
        raise RuntimeError(f"S1B label emission requires log_per_world['{key}']")

    value = log_per_world[key]
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    if isinstance(value, np.ndarray):
        if value.shape == ():
            return value.item()
        return value[world_idx].item() if hasattr(value[world_idx], "item") else value[world_idx]
    if isinstance(value, (list, tuple)):
        return value[world_idx]
    if isinstance(value, dict):
        if world_idx in value:
            return value[world_idx]
        if str(world_idx) in value:
            return value[str(world_idx)]
        raise RuntimeError(f"S1B label emission missing world {world_idx} for '{key}'")
    return value


def _bool_value(log_per_world, key, world_idx):
    """Read one required per-world value as a fail-closed boolean."""
    value = _world_value(log_per_world, key, world_idx)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
        raise RuntimeError(f"S1B label emission cannot parse bool '{value}' for '{key}'")
    return bool(value)


def _float_value(log_per_world, key, world_idx):
    """Read one required per-world value as a fail-closed float."""
    return float(_world_value(log_per_world, key, world_idx))


def _str_value(log_per_world, key, world_idx):
    """Read one required per-world value as a string."""
    return str(_world_value(log_per_world, key, world_idx))


def _s1b_supervisor_label_defaults(args, env_cfg):
    """Create optional S1B supervisor label fields for requested control repair."""
    target_bias_requested = _s1b_release_handoff_left_target_bias_requested(args)
    if target_bias_requested:
        target_blend, left_target_offset = _s1b_release_handoff_left_target_bias_values(env_cfg)
    else:
        target_blend, left_target_offset = 0.0, (0.0, 0.0, 0.0)
    return {
        "s1b_post_release_supervisor_enabled": bool(args.s1b_post_release_supervisor),
        "s1b_release_transient_smoothing_enabled": bool(args.s1b_release_transient_smoothing),
        "s1b_retention_repair_enabled": bool(_s1b_retention_repair_requested(args)),
        "s1b_retention_repair_control_arm": str(args.s1b_retention_repair_control_arm),
        "s1b_retention_repair_supervisor_off_control_arm": (
            args.s1b_retention_repair_control_arm
            == S1B_RETENTION_REPAIR_CONTROL_ARM_SUPERVISOR_OFF
        ),
        "s1b_retention_repair_release_handoff_left_target_bias_arm": target_bias_requested,
        "s1b_retention_repair_assisted_row": target_bias_requested,
        "s1b_retention_repair_unassisted_row": (
            args.s1b_retention_repair_control_arm
            == S1B_RETENTION_REPAIR_CONTROL_ARM_SUPERVISOR_OFF
        ),
        "s1b_retention_repair_handoff_step": -1,
        "s1b_retention_repair_authority_window_steps": (
            int(args.s1b_retention_repair_authority_window_steps)
        ),
        "s1b_retention_repair_left_action_scale": float(
            args.s1b_retention_repair_left_action_scale
        ),
        "s1b_retention_repair_transient_blend": float(
            args.s1b_retention_repair_transient_blend
        ),
        "s1b_retention_repair_target_bias_env_cfg_present": target_bias_requested,
        "s1b_retention_repair_target_blend": float(target_blend),
        "s1b_retention_repair_left_target_offset_x": float(left_target_offset[0]),
        "s1b_retention_repair_left_target_offset_y": float(left_target_offset[1]),
        "s1b_retention_repair_left_target_offset_z": float(left_target_offset[2]),
        "s1b_supervisor_real_observable_only": True,
        "s1b_supervisor_no_crutch_enforced": True,
        "s1b_supervisor_window_steps": int(args.s1b_post_release_supervisor_window_steps),
        "s1b_release_transient_smoothing_steps": int(args.s1b_release_transient_smoothing_steps),
        "s1b_supervisor_activation_step": -1,
        "s1b_supervisor_steps_applied": 0,
        "s1b_transient_smoothing_steps_applied": 0,
        "s1b_supervisor_fail_closed": False,
        "s1b_supervisor_fail_closed_reason": "none",
    }


def _init_s1b_label(args, env_cfg, episode_id, world_idx):
    """Create an S1B release-retention label state for one episode/world."""
    configured_release_step = _s1b_configured_release_step(env_cfg)
    label = {
        "schema_version": S1B_SCHEMA_VERSION,
        "s1b_schema_version": S1B_SCHEMA_VERSION,
        "episode_id": int(episode_id),
        "world_id": int(world_idx),
        "seed": int(args.seed),
        "policy_id": str(args.s1b_policy_id),
        "runner_sha": str(args.s1b_collector_sha),
        "dataset_source": str(args.s1b_dataset_source),
        "configured_release_step": configured_release_step,
        "observed_release_step": -1,
        "actual_release_event": False,
        "release_class": "never_reached_release_predicate",
        "release_detection_source": "s1a_post_release_phase",
        "release_support_removed": False,
        "release_gripper_opened_or_force_reduced": False,
        "terminal_step": -1,
        "first_done_step": -1,
        "terminal_before_configured_release": False,
        "steps_until_configured_release": -1,
        "terminal_break_reason_source": "not_observed",
        "retention_horizon_steps": int(args.retention_horizon_steps),
        "retention_horizon_seconds": float(args.retention_horizon_seconds),
        "post_release_steps_observed": 0,
        "post_release_retained_horizon": False,
        "post_release_cable_drop": False,
        "post_release_explosion": False,
        "post_release_terminal_break_reason": "none",
        "retained_after_release_label": False,
        "kinematic_support_enabled": False,
        "fixed_support_enabled": False,
        "hidden_support_enabled": False,
        "inv_mass_zero_support_enabled": False,
        "direct_sim_state_write_enabled": False,
        "scripted_or_oracle_support_enabled": False,
        "active_at_completion_counted_as_success": False,
        "hold_to_completion_counted_as_success": False,
        "external_assist_enabled": False,
        "no_crutch_product_label_eligible": False,
        "release_real_observable": bool(args.s1b_real_observability_attested),
        "retention_real_observable": bool(args.s1b_real_observability_attested),
        "cable_drop_real_observable": bool(args.s1b_real_observability_attested),
        "explosion_or_instability_real_observable": bool(args.s1b_real_observability_attested),
        "sim_only_field_used_for_product_label": False,
    }
    if _s1b_supervisor_requested(args):
        label.update(_s1b_supervisor_label_defaults(args, env_cfg))
        if _s1b_release_handoff_left_target_bias_requested(args):
            label["scripted_or_oracle_support_enabled"] = True
            label["external_assist_enabled"] = True
            label["no_crutch_product_label_eligible"] = False
    return label


def _update_s1b_label(label, log_per_world, world_idx, step_i, args):
    """Update one S1B label state from raw per-world telemetry."""
    if not isinstance(log_per_world, dict):
        raise RuntimeError("S1B label emission requires extras['log_per_world'] as a dict")
    for key in S1B_REQUIRED_PER_WORLD_KEYS:
        if key not in log_per_world:
            raise RuntimeError(f"S1B label emission requires log_per_world['{key}']")

    post_release_phase = _float_value(log_per_world, "s1a_post_release_phase", world_idx)
    terminal_cable_not_dropped = _bool_value(
        log_per_world, "terminal_status_cable_not_dropped", world_idx)
    terminal_break_reason = _str_value(log_per_world, "terminal_break_reason", world_idx)
    kinematic_support_enabled = _bool_value(
        log_per_world, "kinematic_left_finger_support_enabled", world_idx)
    active_credit = _bool_value(
        log_per_world, "s1a_active_at_completion_credit_authorized", world_idx)
    hold_credit = _bool_value(
        log_per_world, "s1a_hold_to_completion_credit_authorized", world_idx)
    sim_only_credit = _bool_value(
        log_per_world, "s1a_sim_only_crutch_credit_authorized", world_idx)

    if post_release_phase > 0.0 and not label["actual_release_event"]:
        label["actual_release_event"] = True
        label["observed_release_step"] = int(step_i)
        label["release_class"] = "actual_release"
        label["release_support_removed"] = True
        label["release_gripper_opened_or_force_reduced"] = True

    label["kinematic_support_enabled"] = (
        label["kinematic_support_enabled"] or kinematic_support_enabled)
    label["active_at_completion_counted_as_success"] = (
        label["active_at_completion_counted_as_success"] or active_credit)
    label["hold_to_completion_counted_as_success"] = (
        label["hold_to_completion_counted_as_success"] or hold_credit)
    label["sim_only_field_used_for_product_label"] = (
        label["sim_only_field_used_for_product_label"] or sim_only_credit)
    label["post_release_terminal_break_reason"] = terminal_break_reason
    label["terminal_break_reason_source"] = "log_per_world.terminal_break_reason"

    if not label["actual_release_event"]:
        return

    post_release_steps = max(0, int(step_i) - int(label["observed_release_step"]))
    label["post_release_steps_observed"] = max(
        int(label["post_release_steps_observed"]), post_release_steps)
    label["post_release_retained_horizon"] = (
        int(label["post_release_steps_observed"]) >= int(args.retention_horizon_steps))

    if not terminal_cable_not_dropped:
        label["post_release_cable_drop"] = True
    if terminal_break_reason == "explosion":
        label["post_release_explosion"] = True

    label["no_crutch_product_label_eligible"] = not any((
        label["kinematic_support_enabled"],
        label["fixed_support_enabled"],
        label["hidden_support_enabled"],
        label["inv_mass_zero_support_enabled"],
        label["direct_sim_state_write_enabled"],
        label["scripted_or_oracle_support_enabled"],
        label["active_at_completion_counted_as_success"],
        label["hold_to_completion_counted_as_success"],
        label["external_assist_enabled"],
        label["sim_only_field_used_for_product_label"],
    ))
    real_observable = all((
        label["release_real_observable"],
        label["retention_real_observable"],
        label["cable_drop_real_observable"],
        label["explosion_or_instability_real_observable"],
    ))
    label["retained_after_release_label"] = all((
        label["actual_release_event"],
        label["release_support_removed"],
        label["post_release_retained_horizon"],
        not label["post_release_cable_drop"],
        not label["post_release_explosion"],
        label["no_crutch_product_label_eligible"],
        real_observable,
    ))


def _mark_s1b_terminal_step(label, step_i, *, first_done):
    """Record terminal-step provenance without granting product credit."""
    if step_i is None or int(step_i) < 0:
        return
    step_i = int(step_i)
    if int(label["terminal_step"]) < 0:
        label["terminal_step"] = step_i
    if first_done and int(label["first_done_step"]) < 0:
        label["first_done_step"] = step_i

    configured_release_step = int(label["configured_release_step"])
    if configured_release_step >= 0 and int(label["terminal_step"]) >= 0:
        label["terminal_before_configured_release"] = (
            int(label["terminal_step"]) < configured_release_step)
        label["steps_until_configured_release"] = max(
            configured_release_step - int(label["terminal_step"]), 0)


def _finalize_s1b_label(label, episode_done, hold_complete, final_step):
    """Finalize release class without granting product credit."""
    if int(label["terminal_step"]) < 0:
        _mark_s1b_terminal_step(label, final_step, first_done=False)
    if not label["actual_release_event"]:
        if episode_done:
            label["release_class"] = "aborted_before_release"
        elif hold_complete:
            label["release_class"] = "hold_to_completion_no_release"
        else:
            label["release_class"] = "never_reached_release_predicate"
    if label["release_class"] != "actual_release":
        label["retained_after_release_label"] = False


def _s1b_labels_to_arrays(labels, *, include_supervisor_fields=False):
    """Convert episode/world S1B labels into NPZ-ready arrays."""
    arrays = {}
    label_keys = list(S1B_RELEASE_LABEL_KEYS)
    if include_supervisor_fields:
        label_keys.extend(S1B_SUPERVISOR_LABEL_KEYS)
    string_keys = S1B_LABEL_STRING_KEYS | S1B_SUPERVISOR_LABEL_STRING_KEYS
    float_keys = S1B_LABEL_FLOAT_KEYS | S1B_SUPERVISOR_LABEL_FLOAT_KEYS
    for key in label_keys:
        values = [label[key] for label in labels]
        if key in string_keys:
            dtype = S1B_LABEL_STRING_DTYPE_OVERRIDES.get(key, "<U64")
            arrays[key] = np.asarray(values, dtype=dtype)
        elif key in float_keys:
            arrays[key] = np.asarray(values, dtype=np.float32)
        elif isinstance(values[0], (bool, np.bool_)):
            arrays[key] = np.asarray(values, dtype=np.bool_)
        else:
            arrays[key] = np.asarray(values, dtype=np.int32)
    return arrays


def _refresh_s1b_grasp_geometry_telemetry_records(per_world_records, telemetry_payload, world_count):
    """Replace per-world telemetry records with the env-provided bounded history."""
    if not isinstance(telemetry_payload, dict):
        raise RuntimeError("S1B geometry telemetry requires extras['s1b_grasp_geometry_telemetry']")
    if telemetry_payload.get("schema_version") != S1B_GRASP_GEOMETRY_TELEMETRY_SCHEMA_VERSION:
        raise RuntimeError("S1B geometry telemetry schema version mismatch")
    records_by_world = telemetry_payload.get("records_by_world")
    if not isinstance(records_by_world, list) or len(records_by_world) != int(world_count):
        raise RuntimeError("S1B geometry telemetry requires one records_by_world entry per world")
    for world_idx in range(int(world_count)):
        per_world_records[world_idx] = [dict(record) for record in records_by_world[world_idx]]


def _annotate_s1b_grasp_geometry_records(records, *, episode_id, control_arm):
    """Add collector-owned identity/provenance to env-owned telemetry rows."""
    annotated = []
    assisted = control_arm not in (
        S1B_RETENTION_REPAIR_CONTROL_ARM_NONE,
        S1B_RETENTION_REPAIR_CONTROL_ARM_SUPERVISOR_OFF,
    )
    for record in records:
        row = dict(record)
        row["episode_id"] = int(episode_id)
        row["control_arm"] = str(control_arm)
        row["assisted_row"] = bool(assisted)
        row["unassisted_row"] = not bool(assisted)
        row["product_credit_authorized"] = False
        annotated.append(row)
    return annotated


def _vector3_value(record, key):
    """Return a float32 xyz vector from one telemetry record."""
    return np.asarray(record.get(key, (0.0, 0.0, 0.0)), dtype=np.float32).reshape(3)


def _vector4_value(record, key):
    """Return a float32 xyzw quaternion from one telemetry record."""
    return np.asarray(record.get(key, (0.0, 0.0, 0.0, 1.0)), dtype=np.float32).reshape(4)


def _s1b_grasp_geometry_records_to_arrays(records):
    """Convert flattened S1B geometry telemetry records into NPZ-ready arrays."""
    arrays = {
        "s1b_grasp_geometry_telemetry_record_count": np.asarray(len(records), dtype=np.int32),
    }
    if not records:
        return arrays
    string_keys = (
        "schema_version",
        "anchor_event",
        "release_class",
        "release_detection_source",
        "terminal_break_reason",
        "control_arm",
    )
    int_keys = (
        "episode_id",
        "world_id",
        "step",
        "anchor_step",
        "configured_release_step",
        "observed_release_step",
        "first_cable_drop_step",
        "first_clamp_loss_step",
        "first_explosion_step",
    )
    float_keys = (
        "post_release_phase",
        "finger_opening_right",
        "finger_opening_left",
        "contact_force_norm",
        "contact_force_matrix_norm",
        "slip_proxy_left",
        "slip_proxy_right",
        "right_gripper_to_cable_distance",
        "left_gripper_to_cable_distance",
        "right_cable_finger0_distance",
        "right_cable_finger1_distance",
        "right_cable_finger_min_distance",
        "right_cable_finger_line_distance",
        "right_cable_finger_line_t",
        "right_finger_span_distance",
        "left_cable_finger0_distance",
        "left_cable_finger1_distance",
        "left_cable_finger_min_distance",
        "left_cable_finger_line_distance",
        "left_cable_finger_line_t",
        "left_finger_span_distance",
        "left_finger0_fk_error_distance",
        "left_finger1_fk_error_distance",
        "left_finger_fk_error_max",
        "right_finger0_fk_error_distance",
        "right_finger1_fk_error_distance",
        "right_finger_fk_error_max",
        "left_ee_angular_speed",
        "left_ee_linear_speed",
        "left_finger0_angular_speed",
        "left_finger0_linear_speed",
        "left_finger1_angular_speed",
        "left_finger1_linear_speed",
        "right_ee_angular_speed",
        "right_ee_linear_speed",
        "right_finger0_angular_speed",
        "right_finger0_linear_speed",
        "right_finger1_angular_speed",
        "right_finger1_linear_speed",
    )
    bool_keys = (
        "actual_release_event",
        "d0_contact_telemetry_enabled",
        "contact_sensor_present",
        "contact_force_available",
        "contact_force_matrix_available",
        "contact_force_matrix_vector_persisted",
        "contact_time_available",
        "contact_points_available",
        "contact_normals_available",
        "contact_impulses_available",
        "friction_forces_available",
        "force_matrix_history_available",
        "assisted_row",
        "unassisted_row",
        "product_credit_authorized",
    )
    vector_keys = (
        "cable_point_right_xyz",
        "cable_point_left_xyz",
        "gripper_right_xyz",
        "gripper_left_xyz",
        "left_ee_xyz",
        "left_ee_angular_velocity",
        "left_ee_linear_velocity",
        "left_finger0_xyz",
        "left_finger0_angular_velocity",
        "left_finger0_linear_velocity",
        "left_finger1_xyz",
        "left_finger1_angular_velocity",
        "left_finger1_linear_velocity",
        "right_ee_xyz",
        "right_ee_angular_velocity",
        "right_ee_linear_velocity",
        "right_finger0_xyz",
        "right_finger0_angular_velocity",
        "right_finger0_linear_velocity",
        "right_finger1_xyz",
        "right_finger1_angular_velocity",
        "right_finger1_linear_velocity",
    )
    vector4_keys = (
        "left_ee_quat_xyzw",
        "left_finger0_quat_xyzw",
        "left_finger1_quat_xyzw",
        "right_ee_quat_xyzw",
        "right_finger0_quat_xyzw",
        "right_finger1_quat_xyzw",
    )
    for key in string_keys:
        arrays[f"s1b_telemetry_{key}"] = np.asarray([str(record.get(key, "")) for record in records], dtype="<U64")
    for key in int_keys:
        arrays[f"s1b_telemetry_{key}"] = np.asarray([int(record.get(key, -1)) for record in records], dtype=np.int32)
    for key in float_keys:
        arrays[f"s1b_telemetry_{key}"] = np.asarray(
            [float(record.get(key, 0.0)) for record in records], dtype=np.float32
        )
    for key in bool_keys:
        arrays[f"s1b_telemetry_{key}"] = np.asarray(
            [bool(record.get(key, False)) for record in records], dtype=np.bool_
        )
    for key in vector_keys:
        arrays[f"s1b_telemetry_{key}"] = np.asarray(
            [_vector3_value(record, key) for record in records], dtype=np.float32
        )
    for key in vector4_keys:
        arrays[f"s1b_telemetry_{key}"] = np.asarray(
            [_vector4_value(record, key) for record in records], dtype=np.float32
        )
    return arrays


def main():
    parser = argparse.ArgumentParser(description="AerialRegrasp demo collection (wet-run)")
    parser.add_argument("--num-episodes", type=int, default=20,
                        help="Number of episode batches to collect")
    parser.add_argument("--world-count", type=int, default=4,
                        help="Parallel worlds (total episodes = num-episodes × world-count)")
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument("--output", type=str,
                        default="thread_isaac_lab/data/bc_demos/aerial_regrasp_demos_v5.npz")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for NumPy and torch")
    parser.add_argument("--action-noise-xy", type=float, default=0.02,
                        help="Gaussian sigma for XY action noise (action units)")
    parser.add_argument("--max-steps", type=int, default=120,
                        help="Max steps per episode (approach + settle + hold)")
    parser.add_argument("--hold-steps", type=int, default=30,
                        help="Hold steps after approach completes (near-zero action)")
    parser.add_argument("--approach-threshold", type=float, default=0.005,
                        help="Position error threshold (m) to switch from approach to hold")
    parser.add_argument("--warmup-steps", type=int, default=5,
                        help="Random action steps before recording (diversify initial state)")
    parser.add_argument("--warmup-pos-sigma", type=float, default=0.5,
                        help="Gaussian sigma for warmup pos actions (action units)")
    parser.add_argument("--warmup-rot-sigma", type=float, default=0.3,
                        help="Gaussian sigma for warmup rot actions (action units)")
    parser.add_argument("--success-only", action="store_true",
                        help="Only keep transitions from successful episodes")
    parser.add_argument("--emit-s1b-release-retention-labels", action="store_true",
                        help="Opt in to fail-closed S1B release-retention label emission")
    parser.add_argument("--env-cfg-json", type=str, default="",
                        help="Allowlisted JSON cfg passed to NewtonAerialRegraspEnv")
    parser.add_argument("--retention-horizon-steps", type=int, default=30,
                        help="Required post-release observation horizon in env steps")
    parser.add_argument("--retention-horizon-seconds", type=float, default=0.5,
                        help="Required post-release observation horizon in seconds")
    parser.add_argument("--s1b-contract-sha", type=str, default="",
                        help="SHA256 of the bound S1B release-retention label contract")
    parser.add_argument("--s1b-collector-sha", type=str, default="",
                        help="SHA256 of the source collector used for this dataset")
    parser.add_argument("--s1b-env-sha", type=str, default="",
                        help="SHA256 of newton_aerial_regrasp_env.py used for this dataset")
    parser.add_argument("--s1b-task-config-sha", type=str, default="",
                        help="SHA256 of task_config.py used for this dataset")
    parser.add_argument("--s1b-policy-id", type=str, default="scripted_aerial_regrasp_collector",
                        help="Collector policy identifier to persist in dataset provenance")
    parser.add_argument("--s1b-dataset-source", type=str, default="s1b_collection_runtime",
                        help="Dataset source identifier to persist in S1B provenance")
    parser.add_argument("--s1b-real-observability-attested", action="store_true",
                        help="Assert release/retention/drop/instability labels have real-robot proxies")
    parser.add_argument("--s1b-post-release-supervisor", action="store_true",
                        help="Opt in to reviewed S1B post-release retention action supervision")
    parser.add_argument("--s1b-release-transient-smoothing", action="store_true",
                        help="Opt in to reviewed S1B release-transient action smoothing")
    parser.add_argument("--s1b-post-release-supervisor-window-steps", type=int, default=30,
                        help="Post-release action-supervisor window in env steps")
    parser.add_argument("--s1b-release-transient-smoothing-steps", type=int, default=4,
                        help="Release-transient smoothing window in env steps")
    parser.add_argument("--s1b-post-release-left-action-scale", type=float, default=0.25,
                        help="Scale for left-arm action deltas while the S1B supervisor is active")
    parser.add_argument("--s1b-transient-action-blend", type=float, default=0.5,
                        help="Multiplicative action blend during release-transient smoothing")
    parser.add_argument("--s1b-retention-repair", action="store_true",
                        help="Opt in to reviewed S1B retention repair control-arm telemetry")
    parser.add_argument("--s1b-retention-repair-control-arm", type=str, default="none",
                        choices=(
                            S1B_RETENTION_REPAIR_CONTROL_ARM_NONE,
                            S1B_RETENTION_REPAIR_CONTROL_ARM_SUPERVISOR_OFF,
                            S1B_RETENTION_REPAIR_CONTROL_ARM_ACTION_SPACE_HOLD_V1,
                            S1B_RETENTION_REPAIR_CONTROL_ARM_RELEASE_HANDOFF_LEFT_TARGET_BIAS_V1,
                        ),
                        help="Control arm for future S1B retention-repair diagnostics")
    parser.add_argument("--s1b-retention-repair-handoff-steps", type=int, default=8,
                        help="Release-handoff telemetry/action smoothing window in env steps")
    parser.add_argument("--s1b-retention-repair-authority-window-steps", type=int, default=30,
                        help="Post-release retention repair authority window in env steps")
    parser.add_argument("--s1b-retention-repair-left-action-scale", type=float, default=0.10,
                        help="Scale for left-arm action deltas in the retention repair arm")
    parser.add_argument("--s1b-retention-repair-transient-blend", type=float, default=0.35,
                        help="Multiplicative action blend during retention repair handoff")
    parser.add_argument("--emit-s1b-grasp-geometry-telemetry", action="store_true",
                        help="Opt in to default-off S1B grasp-geometry telemetry persistence")
    parser.add_argument("--s1b-telemetry-history-pre-release-steps", type=int, default=4,
                        help="Telemetry pre-release window; fixed to 4 for v1")
    parser.add_argument("--s1b-telemetry-history-post-release-steps", type=int, default=34,
                        help="Telemetry post-release observation window; fixed to 34 for v1")
    parser.add_argument("--s1b-telemetry-history-max-window-steps", type=int, default=40,
                        help="Telemetry bounded history cap; fixed to 40 for v1")
    parser.add_argument("--s1b_retained_zero_video_render", action="store_true",
                        help="Opt in to generation-only retained-zero video rendering")
    parser.add_argument("--s1b_retained_zero_video_episode_ids", type=str, default="",
                        help="Comma-separated episode ids to render; empty renders all episodes")
    parser.add_argument("--s1b_retained_zero_video_output_root", type=str, default="",
                        help="Fresh output root for retained-zero videos and manifests")
    parser.add_argument("--s1b_retained_zero_video_camera_set", type=str,
                        default=S1B_RETAINED_ZERO_VIDEO_DEFAULT_CAMERA_SET,
                        help="Reviewed retained-zero video camera set")
    parser.add_argument("--s1b_retained_zero_video_fps", type=int, default=30,
                        help="Frames per second for retained-zero video generation")
    parser.add_argument("--s1b_retained_zero_video_frame_stride", type=int, default=1,
                        help="Capture every Nth collector step for retained-zero video generation")
    parser.add_argument("--s1b_retained_zero_video_post_terminal_frames", type=int, default=0,
                        help="Additional terminal-state frames to render after a selected episode ends")
    parser.add_argument("--s1b_retained_zero_video_auto_select_policy", type=str, default="none",
                        choices=S1B_RETAINED_ZERO_VIDEO_AUTO_SELECT_POLICIES,
                        help="Capture episodes for generation-only video, then save the first matching label row")
    args = parser.parse_args()

    if "cuda:1" in args.device.lower():
        parser.error("S1B collection refuses cuda:1; use cuda:0 or a separately reviewed device")
    try:
        env_cfg = _parse_env_cfg_json(args.env_cfg_json)
    except ValueError as exc:
        parser.error(str(exc))
    if args.emit_s1b_release_retention_labels:
        if args.success_only:
            parser.error("S1B labels refuse --success-only because it filters by legacy success")
        if args.retention_horizon_steps <= 0:
            parser.error("--retention-horizon-steps must be positive for S1B labels")
        if args.retention_horizon_seconds <= 0.0:
            parser.error("--retention-horizon-seconds must be positive for S1B labels")
        required_provenance = {
            "--s1b-contract-sha": args.s1b_contract_sha,
            "--s1b-collector-sha": args.s1b_collector_sha,
            "--s1b-env-sha": args.s1b_env_sha,
            "--s1b-task-config-sha": args.s1b_task_config_sha,
        }
        missing = [name for name, value in required_provenance.items() if not value]
        if missing:
            parser.error("S1B labels require explicit provenance: " + ", ".join(missing))
        if not args.s1b_real_observability_attested:
            parser.error("S1B labels require --s1b-real-observability-attested")
        try:
            _validate_s1b_release_env_cfg(env_cfg)
        except ValueError as exc:
            parser.error(str(exc))
    try:
        _validate_s1b_supervisor_args(args)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        _validate_s1b_release_handoff_left_target_bias_env_cfg(args, env_cfg)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        _validate_s1b_grasp_geometry_telemetry_args(args, env_cfg)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        _validate_s1b_retained_zero_video_args(args, env_cfg)
    except ValueError as exc:
        parser.error(str(exc))

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = args.device
    world_count = args.world_count
    action_noise_sigma = args.action_noise_xy
    collection_started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    print(f"=== AerialRegrasp Demo Collection (wet-run) ===")
    print(f"  Episodes: {args.num_episodes} batches × {world_count} worlds "
          f"= {args.num_episodes * world_count} total")
    print(f"  Max steps/ep: {args.max_steps}")
    print(f"  Hold steps: {args.hold_steps}")
    print(f"  Approach threshold: {args.approach_threshold*1000:.1f}mm")
    print(f"  Action noise σ(XY): {action_noise_sigma}")
    print(f"  Proportional gains: KP_POS={KP_POS}, KP_ORI={KP_ORI}")
    print(f"  Warmup: {args.warmup_steps} steps (pos_σ={args.warmup_pos_sigma}, rot_σ={args.warmup_rot_sigma})")
    print(f"  Device: {device} (cuda:1 refused)")
    print(f"  Seed: {args.seed}")
    print(f"  S1B labels: {args.emit_s1b_release_retention_labels}")
    print(f"  S1B retained-zero video render: {_s1b_retained_zero_video_render_requested(args, env_cfg)}")
    if _s1b_supervisor_requested(args):
        print(f"  S1B post-release supervisor: {args.s1b_post_release_supervisor}")
        print(f"  S1B release-transient smoothing: {args.s1b_release_transient_smoothing}")
    print(f"  Env cfg keys: {sorted(env_cfg)}")

    # Build env
    print(f"\n[BUILD] Constructing env (world_count={world_count})...")
    env = NewtonAerialRegraspEnv(
        world_count=world_count,
        device=device,
        cfg=env_cfg,
        freeze_left_anchor=False,
    )
    print(f"  obs_dim={env.num_obs}, act_dim={env.num_actions}")

    retained_zero_video_enabled = _s1b_retained_zero_video_render_requested(args, env_cfg)
    retained_zero_video_selected_ids = _parse_s1b_retained_zero_video_episode_ids(
        env_cfg.get(
            S1B_RETAINED_ZERO_VIDEO_EPISODE_IDS_ENV_CFG_KEY,
            args.s1b_retained_zero_video_episode_ids,
        )
    )
    retained_zero_video_auto_select_policy = args.s1b_retained_zero_video_auto_select_policy
    retained_zero_video_recorder = None
    retained_zero_video_label_rows = []
    retained_zero_video_post_terminal_remaining = None
    if retained_zero_video_enabled:
        retained_zero_video_recorder = S1BRetainedZeroVideoRecorder(
            model=env._model,
            output_root=args.s1b_retained_zero_video_output_root,
            camera_set=env_cfg.get(
                S1B_RETAINED_ZERO_VIDEO_CAMERA_SET_ENV_CFG_KEY,
                args.s1b_retained_zero_video_camera_set,
            ),
            fps=args.s1b_retained_zero_video_fps,
            frame_stride=args.s1b_retained_zero_video_frame_stride,
        )
        retained_zero_video_post_terminal_remaining = np.zeros(world_count, dtype=np.int32)

    # Collect
    all_obs = []
    all_act = []
    all_transition_episode_id = []
    all_transition_world_id = []
    all_transition_step = []
    all_s1b_labels = []
    all_s1b_grasp_geometry_telemetry_records = []
    success_count = 0
    total_episodes = 0
    total_transitions = 0

    for batch_i in range(args.num_episodes):
        t0 = time.time()
        obs, info = env.reset()

        # Warmup: random actions to diversify initial state (not recorded)
        warmup_done = False
        for _wu in range(args.warmup_steps):
            wu_act = np.zeros((world_count, 12), dtype=np.float32)
            wu_act[:, 0:3] = np.random.randn(world_count, 3) * args.warmup_pos_sigma
            wu_act[:, 3:6] = np.random.randn(world_count, 3) * args.warmup_rot_sigma
            wu_act[:, 6:9] = np.random.randn(world_count, 3) * args.warmup_pos_sigma
            wu_act[:, 9:12] = np.random.randn(world_count, 3) * args.warmup_rot_sigma
            wu_act = np.clip(wu_act, -ACTION_CLIP, ACTION_CLIP)
            obs, _, done_wu, _ = env.step(
                torch.tensor(wu_act, dtype=torch.float32, device=device))
            if done_wu.any():
                print(f"  [WARN] Batch {batch_i}: warmup triggered done at step {_wu}, re-resetting")
                obs, info = env.reset()
                warmup_done = True
                break

        obs_np = obs.cpu().numpy()  # [W, 42]

        per_world_obs = [[] for _ in range(world_count)]
        per_world_act = [[] for _ in range(world_count)]
        per_world_step = [[] for _ in range(world_count)]
        per_world_episode_id = [batch_i * world_count + w for w in range(world_count)]
        per_world_s1b_labels = [
            _init_s1b_label(args, env_cfg, per_world_episode_id[w], w)
            for w in range(world_count)
        ] if args.emit_s1b_release_retention_labels else None
        per_world_s1b_grasp_geometry_telemetry = (
            [[] for _ in range(world_count)]
            if _s1b_grasp_geometry_telemetry_requested(args)
            else None
        )
        ep_done = np.zeros(world_count, dtype=bool)
        ep_success = np.zeros(world_count, dtype=bool)

        # Per-world approach state
        approach_done = np.zeros(world_count, dtype=bool)
        hold_remaining = np.full(world_count, args.hold_steps, dtype=int)

        for step_i in range(args.max_steps):
            # Compute per-world actions
            actions_np = np.zeros((world_count, 12), dtype=np.float32)
            for w in range(world_count):
                if ep_done[w]:
                    continue
                obs_w = obs_np[w]
                pos_err_norm = np.linalg.norm(obs_w[33:36])

                if not approach_done[w] and pos_err_norm < args.approach_threshold:
                    approach_done[w] = True

                if not approach_done[w]:
                    # Approach: proportional control
                    actions_np[w] = compute_scripted_action(
                        obs_w, action_noise_xy=action_noise_sigma)
                else:
                    # Hold: same proportional control, reduced noise
                    actions_np[w] = compute_scripted_action(
                        obs_w, action_noise_xy=action_noise_sigma * 0.5)
                    hold_remaining[w] -= 1
                if _s1b_supervisor_requested(args):
                    actions_np[w] = _apply_s1b_post_release_control_repair(
                        actions_np[w],
                        per_world_s1b_labels[w],
                        step_i,
                        args,
                    )

            # Record (obs, action) per-world
            for w in range(world_count):
                if not ep_done[w]:
                    per_world_obs[w].append(obs_np[w].copy())
                    per_world_act[w].append(actions_np[w].copy())
                    per_world_step[w].append(step_i)

            # Step env. Video capture needs post-terminal physics frames; step()
            # auto-resets done worlds before returning.
            action_tensor = torch.tensor(actions_np, dtype=torch.float32, device=device)
            if retained_zero_video_recorder is not None:
                obs_next, rew, done, extras = env.step_chain(action_tensor, auto_reset=False)
            else:
                obs_next, rew, done, extras = env.step(action_tensor)
            obs_np = obs_next.cpu().numpy()
            done_np = done.cpu().numpy().astype(bool)
            if args.emit_s1b_release_retention_labels:
                log_per_world = extras.get("log_per_world")
                for w in range(world_count):
                    if not ep_done[w]:
                        _update_s1b_label(
                            per_world_s1b_labels[w], log_per_world, w, step_i, args)
            if _s1b_grasp_geometry_telemetry_requested(args):
                _refresh_s1b_grasp_geometry_telemetry_records(
                    per_world_s1b_grasp_geometry_telemetry,
                    extras.get("s1b_grasp_geometry_telemetry"),
                    world_count,
                )
            if retained_zero_video_recorder is not None:
                capture_episode_ids = [
                    per_world_episode_id[w]
                    for w in range(world_count)
                    if (
                        (
                            not ep_done[w]
                            or retained_zero_video_post_terminal_remaining[w] > 0
                        )
                        and _s1b_retained_zero_video_capture_episode(
                            per_world_episode_id[w],
                            retained_zero_video_selected_ids,
                            retained_zero_video_auto_select_policy,
                        )
                    )
                ]
                if capture_episode_ids:
                    retained_zero_video_recorder.capture(
                        env._state_0,
                        episode_ids=capture_episode_ids,
                        step_i=step_i,
                    )
                for w in range(world_count):
                    if (
                        ep_done[w]
                        and retained_zero_video_post_terminal_remaining[w] > 0
                        and _s1b_retained_zero_video_capture_episode(
                            per_world_episode_id[w],
                            retained_zero_video_selected_ids,
                            retained_zero_video_auto_select_policy,
                        )
                    ):
                        retained_zero_video_post_terminal_remaining[w] -= 1

            # Check success from extras
            success_rate = extras.get("log", {}).get("/episode/success", 0.0)

            # Update per-world done
            for w in range(world_count):
                if done_np[w] and not ep_done[w]:
                    if args.emit_s1b_release_retention_labels:
                        _mark_s1b_terminal_step(
                            per_world_s1b_labels[w], step_i, first_done=True)
                    if (
                        retained_zero_video_post_terminal_remaining is not None
                        and _s1b_retained_zero_video_capture_episode(
                            per_world_episode_id[w],
                            retained_zero_video_selected_ids,
                            retained_zero_video_auto_select_policy,
                        )
                    ):
                        retained_zero_video_post_terminal_remaining[w] = max(
                            retained_zero_video_post_terminal_remaining[w],
                            int(args.s1b_retained_zero_video_post_terminal_frames),
                        )
                    ep_done[w] = True
                    # Check if success (finger_closed + sustained clamp)
                    if success_rate > 0:
                        ep_success[w] = True

            # Stop early if all done or all hold complete
            retained_zero_video_extra_active = (
                retained_zero_video_post_terminal_remaining is not None
                and bool((retained_zero_video_post_terminal_remaining > 0).any())
            )
            if ep_done.all() and not retained_zero_video_extra_active:
                break
            if (approach_done & (hold_remaining <= 0)).all():
                break

        # Aggregate this batch (per-world filtering)
        batch_transitions = 0
        for w in range(world_count):
            if len(per_world_obs[w]) == 0:
                continue
            if args.success_only and not ep_success[w]:
                continue
            all_obs.append(np.array(per_world_obs[w]))
            all_act.append(np.array(per_world_act[w]))
            if args.emit_s1b_release_retention_labels:
                transition_count = len(per_world_obs[w])
                all_transition_episode_id.append(
                    np.full(transition_count, per_world_episode_id[w], dtype=np.int32))
                all_transition_world_id.append(
                    np.full(transition_count, w, dtype=np.int32))
                all_transition_step.append(
                    np.asarray(per_world_step[w], dtype=np.int32))
                _finalize_s1b_label(
                    per_world_s1b_labels[w],
                    episode_done=bool(ep_done[w]),
                    hold_complete=bool(approach_done[w] and hold_remaining[w] <= 0),
                    final_step=per_world_step[w][-1] if per_world_step[w] else -1,
                )
                all_s1b_labels.append(per_world_s1b_labels[w])
                if (
                    retained_zero_video_recorder is not None
                    and _s1b_retained_zero_video_capture_episode(
                        per_world_episode_id[w],
                        retained_zero_video_selected_ids,
                        retained_zero_video_auto_select_policy,
                    )
                ):
                    retained_zero_video_label_rows.append(
                        _s1b_retained_zero_video_label_row(per_world_s1b_labels[w])
                    )
                if _s1b_grasp_geometry_telemetry_requested(args):
                    all_s1b_grasp_geometry_telemetry_records.extend(
                        _annotate_s1b_grasp_geometry_records(
                            per_world_s1b_grasp_geometry_telemetry[w],
                            episode_id=per_world_episode_id[w],
                            control_arm=args.s1b_retention_repair_control_arm,
                        )
                    )
            batch_transitions += len(per_world_obs[w])
        total_transitions += batch_transitions

        batch_success = int(ep_success.sum())
        batch_approach_done = int(approach_done.sum())
        success_count += batch_success
        total_episodes += world_count

        elapsed = time.time() - t0
        print(f"  Batch {batch_i+1}/{args.num_episodes}: "
              f"{step_i+1} steps, {batch_transitions} transitions, "
              f"approach_done={batch_approach_done}/{world_count}, "
              f"success={batch_success}/{world_count}, {elapsed:.1f}s")

    # Aggregate all
    if len(all_obs) == 0:
        print("[ERROR] No transitions collected!")
        sys.exit(1)

    all_obs_flat = np.concatenate(all_obs, axis=0)  # [N, 42]
    all_act_flat = np.concatenate(all_act, axis=0)  # [N, 12]
    if args.emit_s1b_release_retention_labels:
        transition_episode_id_flat = np.concatenate(all_transition_episode_id, axis=0)
        transition_world_id_flat = np.concatenate(all_transition_world_id, axis=0)
        transition_step_flat = np.concatenate(all_transition_step, axis=0)

    print(f"\n=== COLLECTION SUMMARY ===")
    print(f"  Total episodes: {total_episodes}")
    print(f"  Success rate: {success_count}/{total_episodes} "
          f"({100*success_count/total_episodes:.0f}%)")
    print(f"  Transitions: {all_obs_flat.shape[0]}")
    print(f"  obs: {all_obs_flat.shape}, act: {all_act_flat.shape}")

    # Action statistics
    act_pos_r = all_act_flat[:, 0:3]
    act_rot_r = all_act_flat[:, 3:6]
    act_pos_l = all_act_flat[:, 6:9]
    print(f"  Action stats (right pos): mean={np.mean(np.abs(act_pos_r)):.4f}, "
          f"max={np.max(np.abs(act_pos_r)):.4f}")
    print(f"  Action stats (right rot): mean={np.mean(np.abs(act_rot_r)):.4f}, "
          f"max={np.max(np.abs(act_rot_r)):.4f}")
    print(f"  Action stats (left pos):  mean={np.mean(np.abs(act_pos_l)):.4f}, "
          f"max={np.max(np.abs(act_pos_l)):.4f}")

    # Obs error statistics (initial vs final)
    n_per_ep = all_obs_flat.shape[0] // total_episodes if total_episodes > 0 else 1
    if n_per_ep > 5:
        first_5 = all_obs_flat[:5]
        last_5 = all_obs_flat[-5:]
        print(f"  Initial pos_err: {np.mean(np.linalg.norm(first_5[:, 33:36], axis=1))*1000:.1f}mm")
        print(f"  Final pos_err:   {np.mean(np.linalg.norm(last_5[:, 33:36], axis=1))*1000:.1f}mm")
        print(f"  Initial ori_err: {np.mean(np.linalg.norm(first_5[:, 30:33], axis=1)):.4f} rad")
        print(f"  Final ori_err:   {np.mean(np.linalg.norm(last_5[:, 30:33], axis=1)):.4f} rad")

    # Save
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    save_payload = {
        "obs": all_obs_flat,
        "actions": all_act_flat,
    }
    if args.emit_s1b_release_retention_labels:
        save_payload.update({
            "transition_episode_id": transition_episode_id_flat,
            "transition_world_id": transition_world_id_flat,
            "transition_step": transition_step_flat,
            "collector_sha": np.asarray(args.s1b_collector_sha, dtype="<U64"),
            "env_sha": np.asarray(args.s1b_env_sha, dtype="<U64"),
            "task_config_sha": np.asarray(args.s1b_task_config_sha, dtype="<U64"),
            "contract_sha": np.asarray(args.s1b_contract_sha, dtype="<U64"),
            "collector_policy_id": np.asarray(args.s1b_policy_id, dtype="<U96"),
            "schema_version": np.asarray(S1B_SCHEMA_VERSION, dtype="<U64"),
            "policy_id": np.asarray(args.s1b_policy_id, dtype="<U96"),
            "runner_sha": np.asarray(args.s1b_collector_sha, dtype="<U64"),
            "dataset_source": np.asarray(args.s1b_dataset_source, dtype="<U128"),
            "env_cfg_json": np.asarray(
                json.dumps(env_cfg, sort_keys=True, separators=(",", ":")),
                dtype="<U512",
            ),
            "env_cfg_keys": np.asarray(sorted(env_cfg), dtype="<U64"),
            "device": np.asarray(device, dtype="<U32"),
            "cuda_visible_devices": np.asarray(
                os.environ.get("CUDA_VISIBLE_DEVICES", ""), dtype="<U64"),
            "collection_started_at": np.asarray(collection_started_at, dtype="<U32"),
            "product_go": np.asarray(False, dtype=np.bool_),
            "physical_grasp_claim": np.asarray(False, dtype=np.bool_),
            "sim2real_success_claim": np.asarray(False, dtype=np.bool_),
            "troot_95_claim": np.asarray(False, dtype=np.bool_),
            "stage2_claim": np.asarray(False, dtype=np.bool_),
        })
        if _s1b_supervisor_requested(args):
            target_blend, left_target_offset = (
                _s1b_release_handoff_left_target_bias_values(env_cfg)
                if _s1b_release_handoff_left_target_bias_requested(args)
                else (0.0, (0.0, 0.0, 0.0))
            )
            save_payload.update({
                "s1b_supervisor_schema_version": np.asarray(
                    S1B_SUPERVISOR_SCHEMA_VERSION, dtype="<U64"),
                "s1b_retention_repair_schema_version": np.asarray(
                    S1B_RETENTION_REPAIR_SCHEMA_VERSION, dtype="<U64"),
                "s1b_supervisor_requested": np.asarray(True, dtype=np.bool_),
                "s1b_supervisor_post_release_enabled": np.asarray(
                    args.s1b_post_release_supervisor, dtype=np.bool_),
                "s1b_supervisor_release_transient_smoothing_enabled": np.asarray(
                    args.s1b_release_transient_smoothing, dtype=np.bool_),
                "s1b_retention_repair_requested": np.asarray(
                    _s1b_retention_repair_requested(args), dtype=np.bool_),
                "s1b_retention_repair_control_arm": np.asarray(
                    args.s1b_retention_repair_control_arm, dtype="<U64"),
                "s1b_retention_repair_handoff_steps_configured": np.asarray(
                    args.s1b_retention_repair_handoff_steps, dtype=np.int32),
                "s1b_retention_repair_authority_window_steps_configured": np.asarray(
                    args.s1b_retention_repair_authority_window_steps, dtype=np.int32),
                "s1b_retention_repair_release_handoff_left_target_bias_configured": np.asarray(
                    _s1b_release_handoff_left_target_bias_requested(args),
                    dtype=np.bool_,
                ),
                "s1b_retention_repair_target_bias_assisted_product_credit_authorized": np.asarray(
                    False, dtype=np.bool_),
                "s1b_retention_repair_target_blend_configured": np.asarray(
                    target_blend, dtype=np.float32),
                "s1b_retention_repair_left_target_offset_xyz_configured": np.asarray(
                    left_target_offset,
                    dtype=np.float32,
                ),
                "s1b_retention_repair_target_bias_source": np.asarray(
                    "env_cfg.d0_control_target_blend+d0_control_left_target_offset_xyz",
                    dtype="<U96"),
                "s1b_supervisor_window_steps_configured": np.asarray(
                    args.s1b_post_release_supervisor_window_steps, dtype=np.int32),
                "s1b_supervisor_transient_smoothing_steps_configured": np.asarray(
                    args.s1b_release_transient_smoothing_steps, dtype=np.int32),
                "s1b_supervisor_left_action_scale": np.asarray(
                    args.s1b_post_release_left_action_scale, dtype=np.float32),
                "s1b_supervisor_transient_action_blend": np.asarray(
                    args.s1b_transient_action_blend, dtype=np.float32),
                "s1b_supervisor_product_credit_authorized": np.asarray(
                    False, dtype=np.bool_),
            })
        save_payload.update(_s1b_labels_to_arrays(
            all_s1b_labels,
            include_supervisor_fields=_s1b_supervisor_requested(args),
        ))
        if _s1b_grasp_geometry_telemetry_requested(args):
            save_payload.update({
                "s1b_grasp_geometry_telemetry_schema_version": np.asarray(
                    S1B_GRASP_GEOMETRY_TELEMETRY_SCHEMA_VERSION, dtype="<U64"),
                "s1b_grasp_geometry_telemetry_enabled": np.asarray(True, dtype=np.bool_),
                "s1b_grasp_geometry_telemetry_default_off": np.asarray(True, dtype=np.bool_),
                "s1b_grasp_geometry_telemetry_product_credit_authorized": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_telemetry_pre_release_steps": np.asarray(
                    args.s1b_telemetry_history_pre_release_steps, dtype=np.int32),
                "s1b_grasp_geometry_telemetry_post_release_steps": np.asarray(
                    args.s1b_telemetry_history_post_release_steps, dtype=np.int32),
                "s1b_grasp_geometry_telemetry_max_window_steps": np.asarray(
                    args.s1b_telemetry_history_max_window_steps, dtype=np.int32),
                "s1b_grasp_geometry_telemetry_anchor_policy": np.asarray(
                    "observed_release_step_else_first_terminal_or_failure", dtype="<U64"),
                "s1b_grasp_geometry_contact_force_requires_availability_flag": np.asarray(
                    True, dtype=np.bool_),
                "s1b_grasp_geometry_rigid_body_motion_telemetry_available": np.asarray(
                    True, dtype=np.bool_),
                "s1b_grasp_geometry_contact_points_available": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_contact_normals_available": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_contact_impulses_available": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_friction_forces_available": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_contact_time_available": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_force_matrix_vector_persisted": np.asarray(False, dtype=np.bool_),
                "s1b_grasp_geometry_force_matrix_history_available": np.asarray(False, dtype=np.bool_),
            })
            save_payload.update(_s1b_grasp_geometry_records_to_arrays(
                all_s1b_grasp_geometry_telemetry_records
            ))
        positive_labels = int(np.sum(save_payload["retained_after_release_label"]))
        actual_release_count = int(np.sum(save_payload["actual_release_event"]))
        print(f"  S1B actual releases: {actual_release_count}/{len(all_s1b_labels)}")
        print(f"  S1B retained-after-release labels: {positive_labels}/{len(all_s1b_labels)}")

    np.savez(args.output, **save_payload)
    print(f"  Saved: {args.output}")
    print(f"  Size: {os.path.getsize(args.output) / 1024:.0f} KB")

    if retained_zero_video_recorder is not None:
        retained_zero_video_save_episode_ids = _select_s1b_retained_zero_video_save_episode_ids(
            retained_zero_video_label_rows,
            retained_zero_video_auto_select_policy,
        )
        video_manifest = retained_zero_video_recorder.save(
            selected_episode_ids=retained_zero_video_save_episode_ids
        )
        collection_counts = {
            "actual_release_count": int(np.sum(save_payload["actual_release_event"])),
            "post_release_cable_drop_count": int(np.sum(save_payload["post_release_cable_drop"])),
            "post_release_explosion_count": int(np.sum(save_payload["post_release_explosion"])),
            "retained_after_release_count": int(np.sum(save_payload["retained_after_release_label"])),
        }
        _write_s1b_retained_zero_video_manifests(
            output_root=args.s1b_retained_zero_video_output_root,
            npz_path=args.output,
            video_manifest=video_manifest,
            label_rows=retained_zero_video_label_rows,
            args=args,
            collection_counts=collection_counts,
        )


if __name__ == "__main__":
    main()
