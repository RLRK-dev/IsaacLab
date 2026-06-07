# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""S1B AXIS-1 standalone Newton diagnostic prerequisite harness.

This script is import-safe: importing it does not parse arguments, build a
Newton model, step a solver, launch GPU/sim/env/AppLauncher, or write files.
The runtime mode is for a future explicit high-cost-gate directive only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


AXIS_1_PREDICATE = "REFRAME_TO_CONTINUOUS_HOLD_UNTIL_HANDOFF"
CALIBRATION_POLICY_ID = "RS_APPROVED_DIAGNOSTIC_BASELINE_CALIBRATION_POLICY_V1"
ROUTE_LABEL = "STANDALONE_NEWTON_VBD_ENV_ISAACLAB6"
REQUIRED_PYTHON = "/home/rlrk/env_isaaclab6/bin/python"
CURRENT_EVIDENCE_STATUS = "CUSTOM_NEWTON_DIAGNOSTIC_QUARANTINED"
REPORT_NAME = "s1b_axis1_faithful_finger_diagnostic_report.json"

MUST_NOT_DECIDE = (
    "l0_success",
    "product_sr",
    "retained_zero_success",
    "physical_grasp",
    "sim2real",
    "t_root95",
    "stage2",
    "production",
)


def _repo_root() -> Path:
    """Return the repository root inferred from this script path."""

    return Path(__file__).resolve().parents[2]


def _ensure_thread_import_paths() -> None:
    """Add THREAD top-level module paths expected by standalone Newton scripts."""

    root = _repo_root()
    for rel_path in ("thread_isaac_lab/envs", "thread_isaac_lab/configs", "thread_isaac_lab/scripts"):
        path = str(root / rel_path)
        if path not in sys.path:
            sys.path.insert(0, path)


def _load_runtime_modules() -> dict[str, Any]:
    """Import standalone Newton and reviewed wiring helpers only when invoked."""

    _ensure_thread_import_paths()
    import newton
    import warp as wp
    from newton.solvers import SolverVBD
    from newton_skill_env_base import (
        S1B_AXIS1_CALIBRATION_POLICY_DIRECT_RUN_SPEC,
        S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC,
        add_s1b_axis1_faithful_finger_prismatic_joint,
        apply_s1b_axis1_diagnostic_baseline_soft_contact,
        make_s1b_axis1_diagnostic_baseline_shape_config,
        resolve_s1b_axis1_diagnostic_baseline_contact_values,
        validate_s1b_axis1_calibration_policy_direct_run_gates,
    )

    return {
        "newton": newton,
        "wp": wp,
        "SolverVBD": SolverVBD,
        "direct_run_spec": S1B_AXIS1_CALIBRATION_POLICY_DIRECT_RUN_SPEC,
        "a2_spec": S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC,
        "add_finger_joint": add_s1b_axis1_faithful_finger_prismatic_joint,
        "apply_soft_contact": apply_s1b_axis1_diagnostic_baseline_soft_contact,
        "make_shape_config": make_s1b_axis1_diagnostic_baseline_shape_config,
        "resolve_contact_values": resolve_s1b_axis1_diagnostic_baseline_contact_values,
        "validate_gates": validate_s1b_axis1_calibration_policy_direct_run_gates,
    }


def _validate_static_gates(modules: dict[str, Any]) -> dict[str, Any]:
    """Validate policy, substrate, contact baseline, and no-claim gates."""

    gates = modules["validate_gates"](
        axis_1_predicate=AXIS_1_PREDICATE,
        calibration_policy_id=CALIBRATION_POLICY_ID,
        route_label=ROUTE_LABEL,
        python_executable=sys.executable,
    )
    direct_spec = modules["direct_run_spec"]
    a2_spec = modules["a2_spec"]
    actuation = gates["actuation_bindset"]
    actuation_cross_check = {
        "effort_limit_matches_direct_spec": actuation["effort_limit_n"] == direct_spec.effort_limit_n,
        "target_ke_matches_direct_spec": actuation["target_ke_n_per_m"] == direct_spec.target_ke_n_per_m,
        "target_kd_matches_direct_spec": actuation["target_kd_n_s_per_m"] == direct_spec.target_kd_n_s_per_m,
        "armature_matches_direct_spec": actuation["armature"] == direct_spec.armature,
        "target_limits_match_a2": tuple(actuation["target_limit_m"]) == a2_spec.target_limit_m,
        "drive_mode_matches_a2": actuation["drive_mode_name"] == a2_spec.drive_mode_name,
        "dual_hand_roles_match_a2": tuple(gates["hand_roles"]) == a2_spec.hand_roles,
    }
    gates["actuation_cross_check"] = actuation_cross_check
    if not all(actuation_cross_check.values()):
        gates["status"] = "FAIL_CLOSED"
        gates["failures"] = list(gates["failures"]) + ["actuation_bindset_drift_from_reviewed_specs"]
    gates["must_not_decide"] = MUST_NOT_DECIDE
    gates["retained_zero_role"] = "diagnostic_comparator_only_not_product_success"
    gates["source_apply_ready"] = False
    gates["runtime_enablement_ready"] = False
    return gates


def _diagnostic_report_metadata(*, hand_role: str | None = None, finger_side: str | None = None) -> dict[str, Any]:
    """Return diagnostic-only metadata stored in report JSON, not Newton calls."""

    metadata: dict[str, Any] = {
        "axis_1_predicate": AXIS_1_PREDICATE,
        "calibration_policy_id": CALIBRATION_POLICY_ID,
        "route_label": ROUTE_LABEL,
        "diagnostic_only": true_bool(),
        "diagnostic_prerequisite": true_bool(),
        "synthetic_fixture_first_scope": true_bool(),
        "custom_attributes_on_newton_calls": false_bool(),
        "metadata_recorded_in_report_json": true_bool(),
        "must_not_decide": MUST_NOT_DECIDE,
        "proof_boundary": (
            "synthetic mechanism-wiring smoke test only; not real S1B scene, "
            "not retention, not product SR"
        ),
    }
    if hand_role is not None:
        metadata["s1b_hand_role"] = hand_role
    if finger_side is not None:
        metadata["s1b_finger_side"] = finger_side
    return metadata


def _add_hand_fixture(
    builder: Any,
    modules: dict[str, Any],
    *,
    hand_role: str,
    x_offset_m: float,
) -> dict[str, Any]:
    """Add one diagnostic hand fixture with two actuated prismatic fingers."""

    newton = modules["newton"]
    wp = modules["wp"]
    shape_cfg = modules["make_shape_config"]()
    hand_body = builder.add_body(
        xform=wp.transform((x_offset_m, 0.0, 0.045), wp.quat_identity()),
        mass=1.0,
        label=f"{hand_role}_panda_hand_diagnostic_body",
        is_kinematic=False,
    )
    builder.add_shape_box(
        body=hand_body,
        xform=wp.transform_identity(),
        hx=0.025,
        hy=0.018,
        hz=0.012,
        cfg=shape_cfg,
        label=f"{hand_role}_panda_hand_diagnostic_shape",
    )

    joint_facts = []
    for side, y_offset_m, axis_sign in (
        ("finger1", -0.026, -1.0),
        ("finger2", 0.026, 1.0),
    ):
        finger_body = builder.add_body(
            xform=wp.transform((x_offset_m, y_offset_m, 0.045), wp.quat_identity()),
            mass=0.05,
            label=f"{hand_role}_{side}_diagnostic_body",
            is_kinematic=False,
        )
        builder.add_shape_box(
            body=finger_body,
            xform=wp.transform_identity(),
            hx=0.006,
            hy=0.004,
            hz=0.02,
            cfg=shape_cfg,
            label=f"{hand_role}_{side}_diagnostic_contact_shape",
        )
        joint_idx = modules["add_finger_joint"](
            builder,
            parent=hand_body,
            child=finger_body,
            label=f"{hand_role}_panda_{side}_diagnostic_prismatic",
            axis=wp.vec3(0.0, axis_sign, 0.0),
            target_pos_m=0.02,
            target_vel_m_per_s=0.0,
        )
        joint_facts.append(
            {
                "joint_index": int(joint_idx),
                "label": f"{hand_role}_panda_{side}_diagnostic_prismatic",
                "finger_side": side,
                "diagnostic_metadata": _diagnostic_report_metadata(
                    hand_role=hand_role,
                    finger_side=side,
                ),
            }
        )

    return {
        "hand_role": hand_role,
        "hand_body_index": int(hand_body),
        "finger_joints": joint_facts,
        "diagnostic_metadata": _diagnostic_report_metadata(hand_role=hand_role),
    }


def _build_diagnostic_model(modules: dict[str, Any], *, device: str) -> dict[str, Any]:
    """Build a minimal standalone Newton diagnostic model for future runtime."""

    newton = modules["newton"]
    wp = modules["wp"]
    builder = newton.ModelBuilder(gravity=(0.0, 0.0, -9.81))
    shape_cfg = modules["make_shape_config"]()
    hand_facts = [
        _add_hand_fixture(builder, modules, hand_role="left_release_side", x_offset_m=-0.04),
        _add_hand_fixture(builder, modules, hand_role="right_holding_side", x_offset_m=0.04),
    ]
    cable_positions = [
        wp.vec3(-0.055, 0.0, 0.042),
        wp.vec3(-0.018, 0.0, 0.042),
        wp.vec3(0.018, 0.0, 0.042),
        wp.vec3(0.055, 0.0, 0.042),
    ]
    cable_body_ids, cable_joint_ids = builder.add_rod(
        positions=cable_positions,
        radius=0.004,
        cfg=shape_cfg,
        stretch_stiffness=1.0e6,
        stretch_damping=0.0,
        bend_stiffness=1.0,
        bend_damping=0.01,
        label="s1b_axis1_diagnostic_cable",
        wrap_in_articulation=True,
    )
    model = builder.finalize(device=device, requires_grad=False)
    gates = modules["apply_soft_contact"](
        model,
        axis_1_predicate=AXIS_1_PREDICATE,
        calibration_policy_id=CALIBRATION_POLICY_ID,
        route_label=ROUTE_LABEL,
        python_executable=sys.executable,
    )
    return {
        "model": model,
        "hand_facts": hand_facts,
        "cable_body_ids": [int(idx) for idx in cable_body_ids],
        "cable_joint_ids": [int(idx) for idx in cable_joint_ids],
        "gates": gates,
    }


def run_source_check() -> dict[str, Any]:
    """Run import/API-only checks without building or stepping a model."""

    modules = _load_runtime_modules()
    gates = _validate_static_gates(modules)
    contact = modules["resolve_contact_values"]()
    return {
        "status": "PASS" if gates["status"] == "PASS" and contact["status"] == "PASS" else "FAIL_CLOSED",
        "mode": "source_check",
        "axis_1_state": AXIS_1_PREDICATE,
        "current_s1b_evidence_status": CURRENT_EVIDENCE_STATUS,
        "gates": gates,
        "contact_baseline": contact,
        "report_metadata": _diagnostic_report_metadata(),
        "video_generated": false_bool(),
        "must_not_decide": MUST_NOT_DECIDE,
        "proof_boundary": "diagnostic prerequisite only; no product, physical grasp, sim2real, retained-zero success, or production claim",
    }


def run_runtime_measurement(args: argparse.Namespace) -> dict[str, Any]:
    """Build and step the diagnostic model for a future gated run."""

    if args.output_root is None:
        raise ValueError("--output_root is required for runtime_measurement")
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=False)

    modules = _load_runtime_modules()
    gates = _validate_static_gates(modules)
    if gates["status"] != "PASS":
        report = {
            "status": "FAIL_CLOSED",
            "mode": "runtime_measurement",
            "axis_1_state": AXIS_1_PREDICATE,
            "current_s1b_evidence_status": CURRENT_EVIDENCE_STATUS,
            "gates": gates,
            "report_metadata": _diagnostic_report_metadata(),
            "video_generated": false_bool(),
            "must_not_decide": MUST_NOT_DECIDE,
            "proof_boundary": "diagnostic prerequisite only",
        }
        _write_report(output_root, report)
        return report

    newton = modules["newton"]
    SolverVBD = modules["SolverVBD"]
    scene = _build_diagnostic_model(modules, device=args.device)
    model = scene["model"]
    state_0 = model.state()
    state_1 = model.state()
    control = model.control()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state_0)
    solver = SolverVBD(model, iterations=args.vbd_iterations)

    for _ in range(args.step_count):
        state_0.clear_forces()
        contacts = model.collide(state_0)
        solver.step(state_0, state_1, control, contacts, args.sim_dt)
        state_0, state_1 = state_1, state_0

    joint_q = state_0.joint_q.numpy().copy() if hasattr(state_0, "joint_q") else model.joint_q.numpy().copy()
    report = {
        "status": "PASS_DIAGNOSTIC_MEASUREMENT_WRITTEN",
        "mode": "runtime_measurement",
        "axis_1_state": AXIS_1_PREDICATE,
        "current_s1b_evidence_status": CURRENT_EVIDENCE_STATUS,
        "claim_flags": {
            "product_go": false_bool(),
            "physical_grasp_claim": false_bool(),
            "sim2real_success_claim": false_bool(),
            "t_root95_claim": false_bool(),
            "stage2_claim": false_bool(),
            "production": false_bool(),
        },
        "route_flags": {
            "source_apply_ready": false_bool(),
            "runtime_enablement_ready": false_bool(),
            "reward_design_allowed": false_bool(),
            "training_launch_allowed": false_bool(),
        },
        "device": args.device,
        "step_count": args.step_count,
        "sim_dt": args.sim_dt,
        "vbd_iterations": args.vbd_iterations,
        "hand_facts": scene["hand_facts"],
        "report_metadata": _diagnostic_report_metadata(),
        "cable_body_count": len(scene["cable_body_ids"]),
        "cable_joint_count": len(scene["cable_joint_ids"]),
        "joint_q_min": float(joint_q.min()) if joint_q.size else math.nan,
        "joint_q_max": float(joint_q.max()) if joint_q.size else math.nan,
        "gates": scene["gates"],
        "must_not_decide": MUST_NOT_DECIDE,
        "video_generated": false_bool(),
        "proof_boundary": (
            "diagnostic prerequisite only; does not decide L0 success, product SR, "
            "retained-zero success, physical grasp, sim2real, T_ROOT95, Stage-2, or production"
        ),
    }
    _write_report(output_root, report)
    return report


def false_bool() -> bool:
    """Return ``False`` while making false claim flags easy to grep."""

    return False


def true_bool() -> bool:
    """Return ``True`` for diagnostic metadata markers."""

    return True


def _write_report(output_root: Path, report: dict[str, Any]) -> Path:
    """Write the future runtime diagnostic report."""

    report_path = output_root / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line parser without parsing at import time."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("source_check", "runtime_measurement"), required=True)
    parser.add_argument("--output_root", type=str, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--step_count", type=int, default=8)
    parser.add_argument("--sim_dt", type=float, default=1.0 / 240.0)
    parser.add_argument("--vbd_iterations", type=int, default=20)
    return parser


def main() -> int:
    """Run the selected future harness mode."""

    args = build_arg_parser().parse_args()
    if os.path.realpath(sys.executable) != os.path.realpath(REQUIRED_PYTHON):
        raise SystemExit(
            f"FAIL_CLOSED_WRONG_INTERPRETER: expected {REQUIRED_PYTHON}, got {sys.executable}"
        )
    if args.mode == "source_check":
        report = run_source_check()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    report = run_runtime_measurement(args)
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
