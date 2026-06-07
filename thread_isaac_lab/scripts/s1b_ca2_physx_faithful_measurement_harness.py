#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""C-A2 faithful-Franka PhysX measurement harness for S1B prerequisite checks.

This script is a diagnostic harness entrypoint. It is intentionally import-safe:
Isaac Sim application launch, simulation construction, argument parsing, and
file output occur only through :func:`main`.

The harness is not a reward, training, scoring, or product route. It records
mechanism and measurement sufficiency evidence for later review while AXIS-1
remains open.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HARNESS_SCHEMA_VERSION = "s1b_ca2_physx_faithful_measurement_harness_v1"
AXIS_1_STATE = "OPEN"
CURRENT_S1B_EVIDENCE_STATUS = "CUSTOM_NEWTON_DIAGNOSTIC_QUARANTINED"
HIGH_COST_GATE_REQUIRED = True

ROBOT_COUNT = 2
WORLD_COUNT = 1
DEVICE_REQUIRED = "cuda:0"
CUDA_VISIBLE_DEVICES_REQUIRED = "0"

HAND_BODY_NAME = "panda_hand"
FINGER_JOINT_NAMES = ("panda_finger_joint1", "panda_finger_joint2")
FINGER_JOINT_EXPR = "panda_finger_joint.*"
FINGER_LIMITS_M = (0.0, 0.04)
HAND_ACTUATOR_SEMANTICS = {
    "effort_limit_n": 200.0,
    "stiffness_n_per_m": 2000.0,
    "damping_n_s_per_m": 100.0,
}

CLAIM_FLAGS = {
    "product_go": False,
    "physical_grasp_claim": False,
    "sim2real_success_claim": False,
    "t_root95_claim": False,
    "stage_2_claim": False,
    "production_claim": False,
}

ROUTE_FLAGS = {
    "source_apply_ready": False,
    "runtime_enablement_ready": False,
    "reward_design_allowed": False,
    "training_launch_allowed": False,
}

FORBIDDEN_SUCCESS_PATHS = (
    "spring-follow",
    "passive FK/cache-held",
    "zero-inverse-mass support",
    "geometry-only credit",
    "wrapper-exit-only success",
    "hold-to-completion",
    "active-at-completion",
    "product-credit-from-diagnostic",
)

CONTACT_FIELDS_NOT_PROOF = (
    "unavailable contact points",
    "unavailable contact normals",
    "unavailable contact impulses",
    "unavailable friction forces",
    "aggregate force without partner attribution",
)


def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    """Convert tensors, arrays, and scalar-like values into JSON values.

    Args:
        value: Value to convert.

    Returns:
        A JSON-serializable value.
    """

    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, tuple):
        return list(value)
    return value


def _write_report(path: Path, report: dict[str, Any]) -> None:
    """Write the harness report as sorted JSON.

    Args:
        path: Report path.
        report: Report object.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_error_report(stop_condition: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a fail-closed report.

    Args:
        stop_condition: Named stop condition.
        details: Optional diagnostic details.

    Returns:
        Report dictionary.
    """

    return {
        "schema_version": HARNESS_SCHEMA_VERSION,
        "status": "FAIL_CLOSED",
        "stop_condition": stop_condition,
        "details": details or {},
        "observed_at_utc": _utc_now(),
        "axis_1_state": AXIS_1_STATE,
        "current_s1b_evidence_status": CURRENT_S1B_EVIDENCE_STATUS,
        "claim_flags": CLAIM_FLAGS,
        "route_flags": ROUTE_FLAGS,
    }


def build_source_contract() -> dict[str, Any]:
    """Build the source-verifiable C-A2 harness contract.

    Returns:
        Contract dictionary for report inclusion.
    """

    return {
        "official_semantic_baseline": {
            "source_file": "source/isaaclab_assets/isaaclab_assets/robots/franka.py",
            "config_names": ["FRANKA_PANDA_CFG", "FRANKA_PANDA_HIGH_PD_CFG"],
            "usd": "panda_instanceable.usd",
            "hand_body": HAND_BODY_NAME,
            "finger_joint_expr": FINGER_JOINT_EXPR,
            "finger_joints": list(FINGER_JOINT_NAMES),
            "finger_limits_m": list(FINGER_LIMITS_M),
            "hand_actuator_semantics": HAND_ACTUATOR_SEMANTICS,
        },
        "project_reuse_surfaces": [
            "thread_isaac_lab/envs/dual_arm_cfg_opt_a.py",
            "thread_isaac_lab/envs/assets_cfg.py",
            "thread_isaac_lab/scripts/collect_demo_data_v54a.py",
            "thread_isaac_lab/scripts/verify_all_phases_fk.py",
            "scripts/test_reachability.py",
        ],
        "scene_expectation": {
            "world_count": WORLD_COUNT,
            "robot_count": ROBOT_COUNT,
            "robot_roles": ["left_release_side", "right_holding_side"],
            "single_scene_video_judgment_only": True,
            "batched_multiworld_visual_judgment_allowed": False,
        },
        "measurement_schema": {
            "source_verifiable": [
                "articulation_config_path",
                "finger_joint_names",
                "actuator_gains",
                "finger_joint_limits_m",
                "command_interface",
                "camera_manifest_schema",
                "contact_sensor_availability_schema",
                "fk_ik_reachability_hooks",
            ],
            "runtime_verifiable_future_high_cost_gate": [
                "contact_availability",
                "contact_limits",
                "contact_partner_attribution",
                "cable_position_m",
                "target_position_m",
                "frame_count",
                "video_view_coverage",
                "single_world_guarantee",
            ],
            "not_proof": list(CONTACT_FIELDS_NOT_PROOF),
        },
        "forbidden_success_paths": list(FORBIDDEN_SUCCESS_PATHS),
        "judge_fit_video_contract": {
            "global_view_required": True,
            "close_view_required": True,
            "event_window_required": True,
            "raw_video_report_pairing_required": True,
            "codex_video_judgment_authoritative": False,
            "percent9_tasking_authorized_now": False,
        },
        "high_cost_gate_required_for_runtime": HIGH_COST_GATE_REQUIRED,
    }


def _validate_common_args(args: argparse.Namespace) -> None:
    """Validate fail-closed command constraints.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ValueError: If any command constraint is violated.
    """

    if args.world_count != WORLD_COUNT:
        raise ValueError("world_count must be exactly 1 for C-A2 judge-fit measurement")
    if args.robot_count != ROBOT_COUNT:
        raise ValueError("robot_count must be exactly 2 for release-side and holding-side measurement")
    if args.device != DEVICE_REQUIRED:
        raise ValueError("device must be cuda:0")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != CUDA_VISIBLE_DEVICES_REQUIRED:
        raise ValueError("CUDA_VISIBLE_DEVICES must be 0")
    if args.event_window_steps <= 0:
        raise ValueError("event_window_steps must be positive")
    if args.settle_steps < 0:
        raise ValueError("settle_steps must be non-negative")


def _prepare_output_root(path: Path) -> Path:
    """Create a fresh output root and return the report path.

    Args:
        path: Output root.

    Returns:
        Report path inside the output root.

    Raises:
        FileExistsError: If the output root already exists.
    """

    if path.exists():
        raise FileExistsError(f"output root already exists: {path}")
    path.mkdir(parents=True)
    return path / "s1b_ca2_physx_faithful_measurement_report.json"


def _camera_manifest_schema() -> dict[str, Any]:
    """Return the future camera manifest schema."""

    return {
        "required_views": ["global_context", "close_gripper_cable_or_target"],
        "required_fields": [
            "camera_name",
            "camera_role",
            "video_path",
            "frame_count",
            "fps",
            "frame_stride",
            "event_window_start_step",
            "event_window_end_step",
            "source_shas",
            "claim_flags",
        ],
        "video_generated_by_source_contract": False,
    }


def _contact_availability_schema() -> dict[str, Any]:
    """Return contact availability fields and proof boundaries."""

    return {
        "force_available": "RUNTIME_REVIEW_REQUIRED",
        "force_matrix_available": "RUNTIME_REVIEW_REQUIRED",
        "contact_partner_attribution": "RUNTIME_REVIEW_REQUIRED",
        "contact_points_available": False,
        "contact_normals_available": False,
        "contact_impulses_available": False,
        "friction_forces_available": False,
        "aggregate_force_without_partner_attribution_is_proof": False,
    }


def _tensor_abs_max(value: Any) -> float | None:
    """Return the absolute max for tensor-like values.

    Args:
        value: Tensor-like value.

    Returns:
        Absolute max as a float, or ``None`` when unavailable.
    """

    if value is None or not hasattr(value, "abs"):
        return None
    return float(value.abs().max().item())


def _collect_robot_measurement(robot: Any, role: str) -> dict[str, Any]:
    """Collect one robot's Franka mechanism measurement.

    Args:
        robot: IsaacLab articulation.
        role: Robot role label.

    Returns:
        Robot measurement dictionary.
    """

    hand_ids = robot.find_bodies(HAND_BODY_NAME)[0]
    finger_ids = robot.find_joints(FINGER_JOINT_EXPR)[0]
    if len(hand_ids) != 1:
        raise RuntimeError(f"{role}: expected exactly one {HAND_BODY_NAME}, got {len(hand_ids)}")
    if len(finger_ids) != 2:
        raise RuntimeError(f"{role}: expected exactly two finger joints, got {len(finger_ids)}")

    hand_id = int(hand_ids[0])
    return {
        "role": role,
        "hand_body": HAND_BODY_NAME,
        "hand_body_index": hand_id,
        "finger_joint_expr": FINGER_JOINT_EXPR,
        "finger_joint_count": len(finger_ids),
        "finger_joint_indices": [int(index) for index in finger_ids],
        "finger_joint_names_required": list(FINGER_JOINT_NAMES),
        "finger_joint_position_m": _jsonable(robot.data.joint_pos[0, finger_ids]),
        "finger_joint_velocity_m_per_s": _jsonable(robot.data.joint_vel[0, finger_ids]),
        "hand_position_m": _jsonable(robot.data.body_pos_w[0, hand_id]),
        "hand_orientation_quat_wxyz": _jsonable(robot.data.body_quat_w[0, hand_id]),
    }


def _collect_contact_measurement(scene: Any) -> dict[str, Any]:
    """Collect contact sensor availability without promoting it to proof.

    Args:
        scene: IsaacLab interactive scene.

    Returns:
        Contact measurement dictionary.
    """

    result: dict[str, Any] = {
        "schema": _contact_availability_schema(),
        "sensors": {},
        "proof_boundary": "diagnostic_only_until_partner_attribution_review",
    }
    for key in ("contact_left", "contact_right"):
        try:
            sensor = scene[key]
        except Exception:
            result["sensors"][key] = {"present": False}
            continue
        data = getattr(sensor, "data", None)
        net_forces_w = getattr(data, "net_forces_w", None)
        force_matrix_w = getattr(data, "force_matrix_w", None)
        result["sensors"][key] = {
            "present": True,
            "net_forces_abs_max": _tensor_abs_max(net_forces_w),
            "force_matrix_abs_max": _tensor_abs_max(force_matrix_w),
            "aggregate_force_without_partner_attribution_is_proof": False,
        }
    return result


def run_runtime_measurement(args: argparse.Namespace) -> int:
    """Run the future HIGH-COST-GATE measurement.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    try:
        _validate_common_args(args)
        report_path = _prepare_output_root(Path(args.output_root))
    except Exception as exc:
        fallback = Path(args.output_root) / "s1b_ca2_physx_faithful_measurement_report.json"
        if not Path(args.output_root).exists():
            Path(args.output_root).mkdir(parents=True, exist_ok=True)
        _write_report(fallback, _make_error_report("PRECHECK_FAILED", {"error": str(exc)}))
        return 2

    from isaaclab.app import AppLauncher

    app_parser = argparse.ArgumentParser(add_help=False)
    AppLauncher.add_app_launcher_args(app_parser)
    app_args, _ = app_parser.parse_known_args([])
    app_args.headless = True
    app_args.enable_cameras = bool(args.enable_cameras)
    app_args.device = args.device
    app_launcher = AppLauncher(app_args)
    simulation_app = app_launcher.app

    try:
        import isaaclab.sim as sim_utils
        from isaaclab.scene import InteractiveScene
        from isaaclab.sensors import ContactSensorCfg
        from isaaclab.utils import configclass

        from thread_isaac_lab.envs.dual_arm_cfg_opt_a import DualArmSceneCfg

        @configclass
        class CA2MeasurementSceneCfg(DualArmSceneCfg):
            """Single-scene C-A2 measurement scene."""

            contact_left: ContactSensorCfg = ContactSensorCfg(
                prim_path="{ENV_REGEX_NS}/Robot_Left/panda_leftfinger",
                update_period=0.0,
                history_length=1,
                track_air_time=False,
                filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"],
                debug_vis=False,
            )
            contact_right: ContactSensorCfg = ContactSensorCfg(
                prim_path="{ENV_REGEX_NS}/Robot_Right/panda_leftfinger",
                update_period=0.0,
                history_length=1,
                track_air_time=False,
                filter_prim_paths_expr=["{ENV_REGEX_NS}/Cable/.*"],
                debug_vis=False,
            )

        sim_cfg = sim_utils.SimulationCfg(dt=args.sim_dt, render_interval=args.render_interval)
        sim = sim_utils.SimulationContext(sim_cfg)
        scene_cfg = CA2MeasurementSceneCfg(num_envs=args.world_count, env_spacing=args.env_spacing)
        scene = InteractiveScene(scene_cfg)
        sim.reset()
        scene.reset()
        for _ in range(args.settle_steps):
            scene.write_data_to_sim()
            sim.step()
            scene.update(sim.get_physics_dt())

        left = scene["robot_left"]
        right = scene["robot_right"]
        cable = scene["cable"]
        report = {
            "schema_version": HARNESS_SCHEMA_VERSION,
            "status": "MEASUREMENT_COMPLETE_DIAGNOSTIC_ONLY",
            "observed_at_utc": _utc_now(),
            "axis_1_state": AXIS_1_STATE,
            "current_s1b_evidence_status": CURRENT_S1B_EVIDENCE_STATUS,
            "claim_flags": CLAIM_FLAGS,
            "route_flags": ROUTE_FLAGS,
            "source_contract": build_source_contract(),
            "camera_manifest_schema": _camera_manifest_schema(),
            "runtime": {
                "world_count": args.world_count,
                "robot_count": args.robot_count,
                "device": args.device,
                "single_scene": True,
                "event_window_steps": args.event_window_steps,
                "left_release_side": _collect_robot_measurement(left, "left_release_side"),
                "right_holding_side": _collect_robot_measurement(right, "right_holding_side"),
                "cable_position_m": _jsonable(cable.data.root_pos_w[0]),
                "cable_orientation_quat_wxyz": _jsonable(cable.data.root_quat_w[0]),
                "contact_measurement": _collect_contact_measurement(scene),
                "video_generated": False,
                "judge_fit_video_future_contract": _camera_manifest_schema(),
            },
            "proof_boundary": {
                "physical_grasp_proven": False,
                "sim2real_proven": False,
                "product_predicate_decided": False,
                "not_proof": list(CONTACT_FIELDS_NOT_PROOF),
                "forbidden_success_paths": list(FORBIDDEN_SUCCESS_PATHS),
            },
        }
        _write_report(report_path, report)
        return 0
    except Exception as exc:
        _write_report(report_path, _make_error_report("RUNTIME_MEASUREMENT_FAILED", {"error": str(exc)}))
        return 2
    finally:
        simulation_app.close()


def emit_source_contract(args: argparse.Namespace) -> int:
    """Emit a source-contract report without launching simulation.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code.
    """

    try:
        report_path = _prepare_output_root(Path(args.output_root))
    except Exception as exc:
        fallback = Path(args.output_root) / "s1b_ca2_physx_faithful_measurement_report.json"
        if not Path(args.output_root).exists():
            Path(args.output_root).mkdir(parents=True, exist_ok=True)
        _write_report(fallback, _make_error_report("SOURCE_CONTRACT_PRECHECK_FAILED", {"error": str(exc)}))
        return 2

    report = {
        "schema_version": HARNESS_SCHEMA_VERSION,
        "status": "SOURCE_CONTRACT_ONLY_NO_RUNTIME_MEASUREMENT",
        "observed_at_utc": _utc_now(),
        "axis_1_state": AXIS_1_STATE,
        "current_s1b_evidence_status": CURRENT_S1B_EVIDENCE_STATUS,
        "claim_flags": CLAIM_FLAGS,
        "route_flags": ROUTE_FLAGS,
        "source_contract": build_source_contract(),
        "camera_manifest_schema": _camera_manifest_schema(),
        "contact_availability_schema": _contact_availability_schema(),
        "high_cost_gate_required_for_runtime": HIGH_COST_GATE_REQUIRED,
    }
    _write_report(report_path, report)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument vector.

    Returns:
        Parsed arguments.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("runtime_measurement", "source_contract"), default="runtime_measurement")
    parser.add_argument("--output_root", required=True)
    parser.add_argument("--device", default=DEVICE_REQUIRED)
    parser.add_argument("--world_count", type=int, default=WORLD_COUNT)
    parser.add_argument("--robot_count", type=int, default=ROBOT_COUNT)
    parser.add_argument("--settle_steps", type=int, default=60)
    parser.add_argument("--event_window_steps", type=int, default=120)
    parser.add_argument("--sim_dt", type=float, default=1.0 / 240.0)
    parser.add_argument("--render_interval", type=int, default=1)
    parser.add_argument("--env_spacing", type=float, default=2.0)
    parser.add_argument("--enable_cameras", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the selected harness mode.

    Args:
        argv: Optional argument vector.

    Returns:
        Process exit code.
    """

    args = parse_args(argv)
    if args.mode == "source_contract":
        return emit_source_contract(args)
    return run_runtime_measurement(args)


if __name__ == "__main__":
    raise SystemExit(main())
