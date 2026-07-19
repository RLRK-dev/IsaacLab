# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared utilities for Newton RL skill environments (ApproachCable, InsertIntoClip, AerialRegrasp).

Extracts common functions from ApproachCable env and precondition scripts into a single
importable module. ApproachCable env retains its own copies (v18 training in progress);
future refactor will replace those with imports from here.

Reference: thread-vault/06-Knowledge/LL-SkillEnvConsistency.md
"""

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import newton
import numpy as np
import warp as wp
from newton.ik import IKObjectiveJointLimit, IKObjectivePosition, IKObjectiveRotation, IKSolver
from newton.solvers import SolverMuJoCo, SolverVBD

# Ensure configs/ is importable
_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs")
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)

from task_config import (
    CABLE_CONTACT_KD,
    CABLE_CONTACT_KE,
    CABLE_CONTACT_MU,
    CABLE_RADIUS,
    CABLE_SEG_LEN,
    CABLE_SEGMENTS,
    CLIP1_X,
    CLIP1_Y,
    CLIP_BASE_HEIGHT,
    EE_TO_FINGERTIP,
    GRASP_X,
    GRIPPER_DRIVER_EFFORT_LIMIT_NM,
    GRIPPER_DRIVER_JOINT_IDX,
    GRIPPER_DRIVER_OPEN_RAD,
    GRIPPER_JOINT_RANGE,
    GRIPPER_PAD_BODY_IDX,
    GRIPPER_SERVO_TARGET_KD,
    GRIPPER_SERVO_TARGET_KE,
    JOINTS_PER_ARM,
    MAX_MOVE_STEPS,
    MUJOCO_CONTACT_CONDIM,
    MUJOCO_CONTACT_KD,
    MUJOCO_CONTACT_KE,
    MUJOCO_PAD_ROLL_FRICTION,
    MUJOCO_PAD_SOLREF,
    NJMAX,
    ROBOT_BODIES_PER_ARM,
    SIM_SUBSTEPS,
    SOLVER_BACKEND,
    TABLE_HEIGHT,
    USE_MUJOCO_CPU,
    WIDE_LEFT_Y,
    WIDE_RIGHT_Y,
)

# Ensure scripts/ is importable (for build_fk_model, add_kinematic_arm, add_cable_rod)
_scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from cable_orientation_utils import compute_cable_tangent, compute_hand_quat_for_cable
from test_newton_clip_routing import (
    EE_BODY_OFFSET,
    FRANKA_NUM_JOINTS,
    GRAVITY,
    ROBOT_LEFT_BASE,
    ROBOT_RIGHT_BASE,
    ROBOTIQ_STRIPPED_XML,
    add_cable_rod,
    add_kinematic_arm,
    add_revolute_cable,
    add_ur5e_robotiq,
    build_fk_model,
)

# =============================================================================
# Unified Constants (LL-SkillEnvConsistency.md)
# =============================================================================

DT = 1.0 / 480.0
SIM_DT = DT / SIM_SUBSTEPS
RL_SIM_SUBSTEPS = 4
RL_SIM_DT = DT / RL_SIM_SUBSTEPS
VBD_ITERATIONS = 20
IK_ITERATIONS_INIT = 100
IK_ITERATIONS_RL = 30
IK_STEP_SIZE = 1.0
ROBOT_BODY_COUNT = 2 * ROBOT_BODIES_PER_ARM  # 18
# S4a (D-S4a-3): MuJoCo contact buffer when cable contacts are enabled. Sized from the probe's
# measured naconmax (settled-flat 40-seg cable ↔ table = 80; curled gravity-off = 0) with ample
# headroom; an undersized MuJoCo nconmax silently drops contacts, so keep ≫ measured.
MUJOCO_NCONMAX = 1024


@dataclass(frozen=True)
class S1BFrankaFingerAdapterSpec:
    """Default-off metadata for the S1B Franka finger adapter.

    The spec records the official Franka hand/finger semantic baseline and
    the selected thread-local URDF candidate for future Unit A1 builder work.
    It is inert metadata only; it does not build a model, replace the current
    spring-follow finger path, or authorize success/product claims.
    """

    urdf_rel_path: str
    official_usd_name: str
    hand_link_name: str
    finger_joint_names: tuple[str, str]
    finger_child_links: tuple[str, str]
    finger_limit_m: tuple[float, float]
    open_position_m: float
    selected_urdf_effort_limit_n: float
    selected_urdf_velocity_limit_m_per_s: float
    official_effort_limit_sim_n: float
    official_stiffness_n_per_m: float
    official_damping_n_s_per_m: float
    a2_runtime_effort_limit_n: float
    a2_runtime_stiffness_n_per_m: float
    a2_runtime_damping_n_s_per_m: float
    drive_mode_name: str
    default_enabled: bool
    known_deviation: str


S1B_FRANKA_FINGER_ADAPTER_SPEC = S1BFrankaFingerAdapterSpec(
    urdf_rel_path=("source/extensions/isaaclab_tasks_thread/data/robots/panda_independent_fingers.urdf"),
    official_usd_name="panda_instanceable.usd",
    hand_link_name="panda_hand",
    finger_joint_names=("panda_finger_joint1", "panda_finger_joint2"),
    finger_child_links=("panda_leftfinger", "panda_rightfinger"),
    finger_limit_m=(0.0, 0.04),
    open_position_m=0.04,
    selected_urdf_effort_limit_n=20.0,
    selected_urdf_velocity_limit_m_per_s=0.2,
    official_effort_limit_sim_n=200.0,
    official_stiffness_n_per_m=2000.0,
    official_damping_n_s_per_m=100.0,
    a2_runtime_effort_limit_n=200.0,
    a2_runtime_stiffness_n_per_m=2000.0,
    a2_runtime_damping_n_s_per_m=100.0,
    drive_mode_name="POSITION_VELOCITY",
    default_enabled=False,
    known_deviation=(
        "Selected URDF finger effort limit remains a 20 N source fact. "
        "Reviewed Unit A2 runtime PD-drive semantics use official "
        "franka.py panda_hand values: 200 N effort, 2000 N/m stiffness, "
        "and 100 N*s/m damping. Future enablement must preserve both facts."
    ),
)


@dataclass(frozen=True)
class S1BFrankaFingerA2CommandPathSpec:
    """Default-off metadata for future S1B actuated-finger commands.

    The spec is inert. It records the reviewed Unit A2 command surface for
    future Newton URDF PD-drive wiring without replacing the current
    spring-follow finger path or authorizing reward/training/product claims.
    Finger targets are prismatic joint positions [m].
    """

    hand_scope: str
    hand_roles: tuple[str, str]
    finger_joint_names: tuple[str, str]
    target_limit_m: tuple[float, float]
    open_target_m: float
    command_shape: str
    index_source: str
    drive_mode_name: str
    runtime_effort_limit_n: float
    runtime_stiffness_n_per_m: float
    runtime_damping_n_s_per_m: float
    default_enabled: bool
    unit_b_enabled_path_replacement_allowed: bool
    detached_body_indices_allowed: bool
    spring_follow_replacement_allowed: bool
    fail_closed_conditions: tuple[str, ...]


S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC = S1BFrankaFingerA2CommandPathSpec(
    hand_scope="dual_hand_capable",
    hand_roles=("left_release_side", "right_holding_side"),
    finger_joint_names=S1B_FRANKA_FINGER_ADAPTER_SPEC.finger_joint_names,
    target_limit_m=S1B_FRANKA_FINGER_ADAPTER_SPEC.finger_limit_m,
    open_target_m=S1B_FRANKA_FINGER_ADAPTER_SPEC.open_position_m,
    command_shape="[world_count, hand_count, 2]",
    index_source="urdf_joint_indices_and_joint_world_start",
    drive_mode_name=S1B_FRANKA_FINGER_ADAPTER_SPEC.drive_mode_name,
    runtime_effort_limit_n=S1B_FRANKA_FINGER_ADAPTER_SPEC.a2_runtime_effort_limit_n,
    runtime_stiffness_n_per_m=S1B_FRANKA_FINGER_ADAPTER_SPEC.a2_runtime_stiffness_n_per_m,
    runtime_damping_n_s_per_m=S1B_FRANKA_FINGER_ADAPTER_SPEC.a2_runtime_damping_n_s_per_m,
    default_enabled=False,
    unit_b_enabled_path_replacement_allowed=False,
    detached_body_indices_allowed=False,
    spring_follow_replacement_allowed=False,
    fail_closed_conditions=(
        "a1_metadata_missing_or_invalid",
        "selected_urdf_sha_mismatch",
        "finger_joints_missing",
        "finger_joints_not_independent",
        "finger_joint_parent_not_panda_hand",
        "target_tensor_shape_mismatch",
        "world_count_mismatch",
        "target_nan_or_inf",
        "target_outside_0_to_0p04_m_without_reviewed_clamp",
        "joint_index_mapping_missing_or_stale",
        "cache_schema_not_reviewed_after_topology_change",
        "cuda1_requested",
        "spring_follow_or_kinematic_pin_counted_as_success",
    ),
)


def validate_s1b_franka_finger_adapter_spec(
    repo_root: str | os.PathLike[str] | None = None,
) -> dict[str, object]:
    """Validate the default-off S1B Franka finger adapter metadata.

    Args:
        repo_root: Repository root containing the selected URDF. If omitted,
            the root is inferred from this file location.

    Returns:
        Validation facts for the selected URDF and official semantic baseline.
    """

    spec = S1B_FRANKA_FINGER_ADAPTER_SPEC
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    urdf_path = root / spec.urdf_rel_path

    result: dict[str, object] = {
        "status": "PASS",
        "default_enabled": spec.default_enabled,
        "source_apply_ready": False,
        "urdf_path": str(urdf_path),
        "official_usd_name": spec.official_usd_name,
        "drive_mode_name": spec.drive_mode_name,
        "known_deviation": spec.known_deviation,
        "selected_urdf_source_fact": {
            "finger_effort_limit_n": spec.selected_urdf_effort_limit_n,
            "finger_velocity_limit_m_per_s": spec.selected_urdf_velocity_limit_m_per_s,
        },
        "a2_runtime_pd_drive_semantics": {
            "finger_effort_limit_n": spec.a2_runtime_effort_limit_n,
            "stiffness_n_per_m": spec.a2_runtime_stiffness_n_per_m,
            "damping_n_s_per_m": spec.a2_runtime_damping_n_s_per_m,
            "drive_mode_name": spec.drive_mode_name,
        },
        "a2_runtime_matches_official_baseline": False,
        "twenty_n_source_fact_and_200n_runtime_semantics_lockstep": False,
        "finger_joints": {},
    }
    if not urdf_path.exists():
        result["status"] = "FAIL_URDF_MISSING"
        return result

    root_xml = ET.parse(urdf_path).getroot()
    all_pass = True
    joint_facts: dict[str, dict[str, object]] = {}
    for joint_name, child_link in zip(spec.finger_joint_names, spec.finger_child_links):
        joint = root_xml.find(f"./joint[@name='{joint_name}']")
        if joint is None:
            all_pass = False
            joint_facts[joint_name] = {"status": "MISSING"}
            continue

        parent = joint.find("parent")
        child = joint.find("child")
        limit = joint.find("limit")
        lower = float(limit.attrib.get("lower", "nan")) if limit is not None else float("nan")
        upper = float(limit.attrib.get("upper", "nan")) if limit is not None else float("nan")
        effort = float(limit.attrib.get("effort", "nan")) if limit is not None else float("nan")
        velocity = float(limit.attrib.get("velocity", "nan")) if limit is not None else float("nan")
        has_mimic = joint.find("mimic") is not None
        joint_pass = (
            joint.attrib.get("type") == "prismatic"
            and parent is not None
            and parent.attrib.get("link") == spec.hand_link_name
            and child is not None
            and child.attrib.get("link") == child_link
            and lower == spec.finger_limit_m[0]
            and upper == spec.finger_limit_m[1]
            and effort == spec.selected_urdf_effort_limit_n
            and velocity == spec.selected_urdf_velocity_limit_m_per_s
            and not has_mimic
        )
        all_pass = all_pass and joint_pass
        joint_facts[joint_name] = {
            "status": "PASS" if joint_pass else "FAIL",
            "type": joint.attrib.get("type"),
            "parent_link": parent.attrib.get("link") if parent is not None else None,
            "child_link": child.attrib.get("link") if child is not None else None,
            "lower_m": lower,
            "upper_m": upper,
            "effort_limit_n": effort,
            "velocity_limit_m_per_s": velocity,
            "has_mimic": has_mimic,
        }

    result["finger_joints"] = joint_facts
    result["independent_per_finger_actuation_proven"] = bool(all_pass)
    runtime_semantics_pass = (
        spec.a2_runtime_effort_limit_n == spec.official_effort_limit_sim_n
        and spec.a2_runtime_stiffness_n_per_m == spec.official_stiffness_n_per_m
        and spec.a2_runtime_damping_n_s_per_m == spec.official_damping_n_s_per_m
        and spec.selected_urdf_effort_limit_n == 20.0
        and spec.official_effort_limit_sim_n == 200.0
        and spec.official_stiffness_n_per_m == 2000.0
        and spec.official_damping_n_s_per_m == 100.0
    )
    result["a2_runtime_matches_official_baseline"] = bool(runtime_semantics_pass)
    result["twenty_n_source_fact_and_200n_runtime_semantics_lockstep"] = bool(all_pass and runtime_semantics_pass)
    result["unit_d_label_handoff_ready"] = bool(all_pass)
    result["status"] = "PASS" if all_pass and runtime_semantics_pass else "FAIL_FINGER_MAPPING"
    return result


def validate_s1b_franka_finger_a2_command_path_spec(
    repo_root: str | os.PathLike[str] | None = None,
) -> dict[str, object]:
    """Validate inert Unit A2 finger command-path metadata.

    Args:
        repo_root: Repository root containing the selected URDF. If omitted,
            the root is inferred from this file location.

    Returns:
        Validation facts for default-off command metadata and hand scope.
    """

    adapter = validate_s1b_franka_finger_adapter_spec(repo_root)
    spec = S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC
    adapter_spec = S1B_FRANKA_FINGER_ADAPTER_SPEC
    dual_hand_scope_pass = (
        spec.hand_scope == "dual_hand_capable"
        and spec.hand_roles == ("left_release_side", "right_holding_side")
        and spec.command_shape == "[world_count, hand_count, 2]"
    )
    runtime_lockstep_pass = (
        adapter.get("twenty_n_source_fact_and_200n_runtime_semantics_lockstep") is True
        and spec.runtime_effort_limit_n == adapter_spec.a2_runtime_effort_limit_n
        and spec.runtime_stiffness_n_per_m == adapter_spec.a2_runtime_stiffness_n_per_m
        and spec.runtime_damping_n_s_per_m == adapter_spec.a2_runtime_damping_n_s_per_m
    )
    default_off_pass = (
        spec.default_enabled is False
        and spec.unit_b_enabled_path_replacement_allowed is False
        and spec.detached_body_indices_allowed is False
        and spec.spring_follow_replacement_allowed is False
    )
    command_surface_pass = (
        spec.finger_joint_names == adapter_spec.finger_joint_names
        and spec.target_limit_m == adapter_spec.finger_limit_m
        and spec.open_target_m == adapter_spec.open_position_m
        and spec.index_source == "urdf_joint_indices_and_joint_world_start"
        and spec.drive_mode_name == "POSITION_VELOCITY"
        and "cuda1_requested" in spec.fail_closed_conditions
        and "spring_follow_or_kinematic_pin_counted_as_success" in spec.fail_closed_conditions
    )
    status = (
        "PASS"
        if all((dual_hand_scope_pass, runtime_lockstep_pass, default_off_pass, command_surface_pass))
        else "FAIL_A2_COMMAND_PATH_SPEC"
    )
    return {
        "status": status,
        "source_apply_ready": False,
        "runtime_enablement_ready": False,
        "unit_b_enabled_path_replacement_allowed": False,
        "hand_scope": spec.hand_scope,
        "hand_roles": spec.hand_roles,
        "command_shape": spec.command_shape,
        "dual_hand_scope_pass": bool(dual_hand_scope_pass),
        "runtime_lockstep_pass": bool(runtime_lockstep_pass),
        "default_off_pass": bool(default_off_pass),
        "command_surface_pass": bool(command_surface_pass),
        "fail_closed_conditions": spec.fail_closed_conditions,
    }


@dataclass(frozen=True)
class S1BAxis1CalibrationPolicyDirectRunSpec:
    """Default-off contract for the first S1B faithful-finger diagnostic run.

    The contract records the Rs-selected predicate and calibration policy for
    a future standalone Newton prerequisite diagnostic. It does not authorize
    source apply, runtime launch, reward, training, product success, physical
    grasp, or sim-to-real claims. Finger target positions are prismatic joint
    positions [m]; contact stiffness and damping are penalty contact values.
    """

    route_label: str
    required_python_executable: str
    axis_1_predicate: str
    calibration_policy_id: str
    evidence_status: str
    hand_roles: tuple[str, str]
    finger_joint_names: tuple[str, str]
    target_limit_m: tuple[float, float]
    open_target_m: float
    effort_limit_n: float
    target_ke_n_per_m: float
    target_kd_n_s_per_m: float
    armature: float
    drive_mode_name: str
    soft_contact_ke: float
    soft_contact_kd: float
    soft_contact_mu: float
    shape_material_ke: float
    shape_material_kd: float
    shape_material_mu: float
    forbidden_success_paths: tuple[str, ...]
    default_enabled: bool


S1B_AXIS1_CALIBRATION_POLICY_DIRECT_RUN_SPEC = S1BAxis1CalibrationPolicyDirectRunSpec(
    route_label="STANDALONE_NEWTON_VBD_ENV_ISAACLAB6",
    required_python_executable="/home/rlrk/env_isaaclab6/bin/python",
    axis_1_predicate="REFRAME_TO_CONTINUOUS_HOLD_UNTIL_HANDOFF",
    calibration_policy_id="RS_APPROVED_DIAGNOSTIC_BASELINE_CALIBRATION_POLICY_V1",
    evidence_status="CUSTOM_NEWTON_DIAGNOSTIC_QUARANTINED",
    hand_roles=S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC.hand_roles,
    finger_joint_names=S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC.finger_joint_names,
    target_limit_m=S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC.target_limit_m,
    open_target_m=S1B_FRANKA_FINGER_A2_COMMAND_PATH_SPEC.open_target_m,
    effort_limit_n=200.0,
    target_ke_n_per_m=2000.0,
    target_kd_n_s_per_m=100.0,
    armature=0.0,
    drive_mode_name="POSITION_VELOCITY",
    soft_contact_ke=1000.0,
    soft_contact_kd=10.0,
    soft_contact_mu=0.5,
    shape_material_ke=float(CABLE_CONTACT_KE),
    shape_material_kd=float(CABLE_CONTACT_KD),
    shape_material_mu=float(CABLE_CONTACT_MU),
    forbidden_success_paths=(
        "spring_follow_success",
        "passive_fk_cache_held_success",
        "zero_inverse_mass_support_success",
        "kinematic_pin_support_success",
        "hidden_fixture_success",
        "geometry_only_credit",
        "wrapper_exit_only_success",
        "hold_to_completion_success",
        "active_at_completion_success",
        "diagnostic_contact_as_product_proof",
    ),
    default_enabled=False,
)


def resolve_s1b_axis1_diagnostic_baseline_contact_values() -> dict[str, object]:
    """Resolve source-backed contact values for the diagnostic calibration policy.

    Returns:
        Contact material facts for the rigid shape and particle/soft sides.
        The effective VBD body-particle values use arithmetic mean for
        stiffness/damping and geometric mean for friction.
    """

    model = newton.ModelBuilder().finalize(requires_grad=False)
    shape_cfg = newton.ModelBuilder.ShapeConfig()
    spec = S1B_AXIS1_CALIBRATION_POLICY_DIRECT_RUN_SPEC
    values = {
        "status": "PASS",
        "calibration_policy_id": spec.calibration_policy_id,
        "policy_scope": "diagnostic_baseline_only_not_sim2real_or_product",
        "soft_contact_ke": float(model.soft_contact_ke),
        "soft_contact_kd": float(model.soft_contact_kd),
        "soft_contact_mu": float(model.soft_contact_mu),
        "shape_material_ke": float(CABLE_CONTACT_KE),
        "shape_material_kd": float(CABLE_CONTACT_KD),
        "shape_material_mu": float(CABLE_CONTACT_MU),
        "shape_config_default_ke": float(shape_cfg.ke),
        "shape_config_default_kd": float(shape_cfg.kd),
        "shape_config_default_mu": float(shape_cfg.mu),
    }
    values["effective_vbd_ke"] = 0.5 * (values["soft_contact_ke"] + values["shape_material_ke"])
    values["effective_vbd_kd"] = 0.5 * (values["soft_contact_kd"] + values["shape_material_kd"])
    values["effective_vbd_mu"] = math.sqrt(values["soft_contact_mu"] * values["shape_material_mu"])
    expected = {
        "soft_contact_ke": spec.soft_contact_ke,
        "soft_contact_kd": spec.soft_contact_kd,
        "soft_contact_mu": spec.soft_contact_mu,
        "shape_material_ke": spec.shape_material_ke,
        "shape_material_kd": spec.shape_material_kd,
        "shape_material_mu": spec.shape_material_mu,
    }
    mismatches = {
        name: {"actual": values[name], "expected": expected[name]}
        for name in expected
        if values[name] != expected[name]
    }
    if mismatches:
        values["status"] = "FAIL_BASELINE_CONTACT_VALUES_MISMATCH"
        values["mismatches"] = mismatches
    return values


def validate_s1b_axis1_calibration_policy_direct_run_gates(
    *,
    axis_1_predicate: str,
    calibration_policy_id: str,
    route_label: str = "STANDALONE_NEWTON_VBD_ENV_ISAACLAB6",
    python_executable: str | None = None,
    forbidden_success_paths: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Validate gates for the S1B faithful-finger diagnostic run contract.

    Args:
        axis_1_predicate: Active AXIS-1 predicate disposition.
        calibration_policy_id: Active contact-calibration policy identifier.
        route_label: Runtime substrate label.
        python_executable: Python interpreter path expected for runtime.
        forbidden_success_paths: Optional explicit success-path exclusion set.

    Returns:
        Fail-closed validation facts. The result never authorizes source apply,
        runtime, reward, training, product success, physical grasp, or sim-to-real.
    """

    spec = S1B_AXIS1_CALIBRATION_POLICY_DIRECT_RUN_SPEC
    python_path = python_executable or sys.executable
    active_forbidden = forbidden_success_paths or spec.forbidden_success_paths
    forbidden_pass = (
        set(active_forbidden) == set(spec.forbidden_success_paths)
        and len(active_forbidden) == 10
        and len(set(active_forbidden)) == 10
        and "hidden_fixture_success" in active_forbidden
        and "diagnostic_contact_as_product_proof" in active_forbidden
    )
    adapter = validate_s1b_franka_finger_a2_command_path_spec()
    contact = resolve_s1b_axis1_diagnostic_baseline_contact_values()
    drive_mode = getattr(newton.JointTargetMode, spec.drive_mode_name, None)
    failures = []
    if route_label != spec.route_label:
        failures.append("substrate_route_label_mismatch")
    if python_path != spec.required_python_executable:
        failures.append("runtime_interpreter_not_env_isaaclab6")
    if axis_1_predicate != spec.axis_1_predicate:
        failures.append("axis_1_predicate_not_continuous_hold_until_handoff")
    if calibration_policy_id != spec.calibration_policy_id:
        failures.append("diagnostic_calibration_policy_not_selected")
    if adapter["status"] != "PASS":
        failures.append("a1_a2_metadata_invalid")
    if contact["status"] != "PASS":
        failures.append("contact_baseline_not_source_resolved")
    if drive_mode != newton.JointTargetMode.POSITION_VELOCITY:
        failures.append("position_velocity_mode_unavailable")
    if not forbidden_pass:
        failures.append("forbidden_success_paths_not_ssot_exact_10")

    status = "PASS" if not failures else "FAIL_CLOSED"
    return {
        "status": status,
        "failures": failures,
        "source_apply_ready": False,
        "runtime_enablement_ready": False,
        "reward_design_allowed": False,
        "training_launch_allowed": False,
        "product_go": False,
        "physical_grasp_claim": False,
        "sim2real_success_claim": False,
        "t_root95_claim": False,
        "stage2_claim": False,
        "production_claim": False,
        "route_label": route_label,
        "required_route_label": spec.route_label,
        "python_executable": python_path,
        "required_python_executable": spec.required_python_executable,
        "axis_1_predicate": axis_1_predicate,
        "calibration_policy_id": calibration_policy_id,
        "current_s1b_evidence_status": spec.evidence_status,
        "forbidden_success_paths": active_forbidden,
        "forbidden_success_paths_pass": bool(forbidden_pass),
        "hand_roles": spec.hand_roles,
        "actuation_bindset": {
            "finger_joint_names": spec.finger_joint_names,
            "target_limit_m": spec.target_limit_m,
            "effort_limit_n": spec.effort_limit_n,
            "target_ke_n_per_m": spec.target_ke_n_per_m,
            "target_kd_n_s_per_m": spec.target_kd_n_s_per_m,
            "armature": spec.armature,
            "drive_mode_name": spec.drive_mode_name,
        },
        "contact_baseline": contact,
        "proof_boundary": (
            "diagnostic prerequisite only; not L0 success, product SR, "
            "retained-zero success, physical grasp, sim2real, T_ROOT95, "
            "Stage-2, or production proof"
        ),
    }


def make_s1b_axis1_diagnostic_baseline_shape_config() -> newton.ModelBuilder.ShapeConfig:
    """Create a rigid-side contact material config for the diagnostic baseline.

    Returns:
        Shape config with source-resolved rigid contact values. Stiffness and
        damping use Newton penalty contact units; friction is unitless.
    """

    contact = resolve_s1b_axis1_diagnostic_baseline_contact_values()
    if contact["status"] != "PASS":
        raise ValueError(f"contact baseline unresolved: {contact}")
    cfg = newton.ModelBuilder.ShapeConfig()
    cfg.ke = float(contact["shape_material_ke"])
    cfg.kd = float(contact["shape_material_kd"])
    cfg.mu = float(contact["shape_material_mu"])
    return cfg


def apply_s1b_axis1_diagnostic_baseline_soft_contact(
    model: newton.Model,
    *,
    axis_1_predicate: str,
    calibration_policy_id: str,
    route_label: str = "STANDALONE_NEWTON_VBD_ENV_ISAACLAB6",
    python_executable: str | None = None,
) -> dict[str, object]:
    """Apply diagnostic baseline soft-contact values to a standalone Newton model.

    Args:
        model: Standalone Newton model to receive soft contact values.
        axis_1_predicate: Active AXIS-1 predicate disposition.
        calibration_policy_id: Active contact-calibration policy identifier.
        route_label: Runtime substrate label.
        python_executable: Python interpreter path expected for runtime.

    Returns:
        Gate and contact facts recorded for the future diagnostic report.

    Raises:
        ValueError: If the route, predicate, calibration policy, or source
            resolved baseline fails closed.
    """

    gates = validate_s1b_axis1_calibration_policy_direct_run_gates(
        axis_1_predicate=axis_1_predicate,
        calibration_policy_id=calibration_policy_id,
        route_label=route_label,
        python_executable=python_executable,
    )
    if gates["status"] != "PASS":
        raise ValueError(f"S1B diagnostic baseline gates failed: {gates}")

    contact = gates["contact_baseline"]
    model.soft_contact_ke = float(contact["soft_contact_ke"])
    model.soft_contact_kd = float(contact["soft_contact_kd"])
    model.soft_contact_mu = float(contact["soft_contact_mu"])
    return gates


def add_s1b_axis1_faithful_finger_prismatic_joint(
    builder: newton.ModelBuilder,
    *,
    parent: int,
    child: int,
    label: str,
    axis: object = newton.Axis.X,
    parent_xform: object | None = None,
    child_xform: object | None = None,
    target_pos_m: float | None = None,
    target_vel_m_per_s: float | None = None,
) -> int:
    """Add one reviewed Franka finger prismatic joint to a Newton builder.

    Args:
        builder: Standalone Newton model builder.
        parent: Parent body index for the hand body.
        child: Child body index for the finger body.
        label: Stable joint label for report/contact handoff.
        axis: Prismatic axis in the parent frame.
        parent_xform: Parent joint transform [m].
        child_xform: Child joint transform [m].
        target_pos_m: Optional target position [m].
        target_vel_m_per_s: Optional target velocity [m/s].

    Returns:
        Joint index returned by :meth:`newton.ModelBuilder.add_joint_prismatic`.
    """

    spec = S1B_AXIS1_CALIBRATION_POLICY_DIRECT_RUN_SPEC
    return builder.add_joint_prismatic(
        parent=parent,
        child=child,
        parent_xform=parent_xform,
        child_xform=child_xform,
        axis=axis,
        target_pos=target_pos_m,
        target_vel=target_vel_m_per_s,
        target_ke=spec.target_ke_n_per_m,
        target_kd=spec.target_kd_n_s_per_m,
        limit_lower=spec.target_limit_m[0],
        limit_upper=spec.target_limit_m[1],
        armature=spec.armature,
        effort_limit=spec.effort_limit_n,
        actuator_mode=newton.JointTargetMode.POSITION_VELOCITY,
        label=label,
    )


# IK rotation targets: hand down, fingers perpendicular to cable Y-axis.
# Newton IK wp.vec4 uses (x, y, z, w) convention — same as wp.quat.
_cos_pi8 = math.cos(math.pi / 8)
_sin_pi8 = math.sin(math.pi / 8)
IK_ROT_TARGET_XYZW = (_cos_pi8, _sin_pi8, 0.0, 0.0)

# =============================================================================
# Quaternion Math Utilities (xyzw convention)
# =============================================================================


def quat_rotate_vec(quat_xyzw, vec):
    """Rotate a 3D vector by a quaternion in [qx, qy, qz, qw] convention."""
    qx, qy, qz, qw = quat_xyzw
    q = np.array([qx, qy, qz], dtype=np.float64)
    v = np.asarray(vec, dtype=np.float64)
    t = 2.0 * np.cross(q, v)
    return (v + qw * t + np.cross(q, t)).astype(np.float32)


def normalize_quat_w_positive(quat_xyzw):
    """Normalize quaternion and enforce w >= 0 (double-cover convention)."""
    q = np.asarray(quat_xyzw, dtype=np.float32)
    norm = np.linalg.norm(q)
    if norm < 1e-8:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    q = q / norm
    if q[3] < 0:
        q = -q
    return q


def axis_angle_to_quat_xyzw(axis_angle):
    """Convert axis-angle (rotation vector) to quaternion [qx, qy, qz, qw]."""
    aa = np.asarray(axis_angle, dtype=np.float64)
    angle = np.linalg.norm(aa)
    if angle < 1e-8:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    axis = aa / angle
    half = angle / 2.0
    s = math.sin(half)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, math.cos(half)], dtype=np.float32)


def quat_multiply_xyzw(q1, q2):
    """Multiply two quaternions in [qx, qy, qz, qw] convention.

    Returns q1 * q2 (q2 applied first, then q1).
    """
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array(
        [
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        ],
        dtype=np.float32,
    )


def quat_to_axis_angle(q_xyzw):
    """Convert quaternion [qx, qy, qz, qw] to axis-angle (rotation vector) [3]."""
    q = np.asarray(q_xyzw, dtype=np.float64)
    if q[3] < 0:
        q = -q
    sin_half = np.linalg.norm(q[:3])
    if sin_half < 1e-8:
        return np.array([0.0, 0.0, 0.0], dtype=np.float32)
    half_angle = math.atan2(sin_half, float(q[3]))
    angle = 2.0 * half_angle
    axis = q[:3] / sin_half
    return (axis * angle).astype(np.float32)


def compute_ori_error_axis_angle(hand_quat_xyzw, target_quat_xyzw):
    """Compute orientation error as axis-angle [3] in world frame.

    Returns q_error such that target = q_error * hand (left-multiply).
    """
    hand_inv = np.array(
        [-hand_quat_xyzw[0], -hand_quat_xyzw[1], -hand_quat_xyzw[2], hand_quat_xyzw[3]], dtype=np.float64
    )
    q_error = quat_multiply_xyzw(target_quat_xyzw, hand_inv)
    return quat_to_axis_angle(q_error)


def quat_distance(q1_xyzw, q2_xyzw):
    """Compute angular distance between two quaternions [rad].

    Returns angle in [0, pi]. Handles double-cover.
    """
    dot = float(np.dot(q1_xyzw, q2_xyzw))
    dot = min(1.0, max(-1.0, abs(dot)))
    return 2.0 * math.acos(dot)


def temporal_quat_consistency(q: np.ndarray, q_prev: np.ndarray) -> np.ndarray:
    """Enforce temporal sign consistency between consecutive quaternions.

    Flips ``q`` to ``-q`` if the dot product with ``q_prev`` is negative,
    keeping the quaternion in the same hemisphere as the previous frame.
    Avoids sign flip discontinuity at w≈0 boundary (Bug #2 fix in env code).

    Args:
        q: Current quaternion ``[qx, qy, qz, qw]``, shape ``[4]``, dtype float32.
        q_prev: Previous-frame quaternion ``[qx, qy, qz, qw]``, shape ``[4]``,
            dtype float32. Must already be normalized.

    Returns:
        Quaternion in the same hemisphere as ``q_prev``, shape ``[4]``, dtype
        float32. Returns ``q`` unchanged if ``dot(q, q_prev) >= 0``.

    Notes:
        - This function does **not** normalize ``q``; caller must normalize first.
        - Idempotent: ``temporal_quat_consistency(q, q) == q`` always.
    """
    if np.dot(q, q_prev) < 0:
        q = -q
    return q


# =============================================================================
# Cable / Clamp Utilities
# =============================================================================


def find_nearest_cable_point(cable_pos, query_pos, search_indices):
    """Find the closest point on the piecewise-linear cable to query_pos.

    Projects query_pos onto each edge (seg[i] -> seg[i+1]) within the search
    window and returns the nearest projected point, its tangent, and distance.

    Args:
        cable_pos: [n_cable, 3] cable body positions for one world.
        query_pos: [3] query position (clamp pos or clip pos, skill-dependent).
        search_indices: array of cable body indices to search within.

    Returns:
        (proj_pos [3], tangent [3], dist float)
    """
    n_cable = len(cable_pos)
    best_dist_sq = float("inf")
    best_pos = cable_pos[search_indices[0]]
    best_tangent = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    idx_min = max(0, int(search_indices[0]) - 1)
    idx_max = min(n_cable - 1, int(search_indices[-1]) + 1)
    for i in range(idx_min, idx_max):
        a = cable_pos[i]
        b = cable_pos[i + 1]
        ab = b - a
        ab_len_sq = np.dot(ab, ab)
        if ab_len_sq < 1e-12:
            t = 0.0
        else:
            t = np.clip(np.dot(query_pos - a, ab) / ab_len_sq, 0.0, 1.0)
        proj = a + t * ab
        d_sq = float(np.sum((query_pos - proj) ** 2))
        if d_sq < best_dist_sq:
            best_dist_sq = d_sq
            best_pos = proj
            norm = np.sqrt(ab_len_sq)
            best_tangent = ab / norm if norm > 1e-8 else np.array([0.0, 1.0, 0.0], dtype=np.float32)

    return best_pos.copy(), best_tangent, float(np.sqrt(best_dist_sq))


def compute_grasp_target_quat(cable_positions, nearest_body_idx):
    """Derive ideal grasp quaternion from cable tangent at nearest body.

    Uses cable_orientation_utils to compute the hand-down orientation
    that tracks the cable tangent direction.

    Returns:
        [4] quaternion (x, y, z, w).
    """
    tangent = compute_cable_tangent(cable_positions, nearest_body_idx)
    return compute_hand_quat_for_cable(tangent)


def compute_clamp_pos(ee_pos, ee_quat_xyzw):
    """Compute fingertip (clamp) position from EE body pose.

    clamp_pos = ee_pos + quat_rotate(ee_quat, [0, 0, +EE_TO_FINGERTIP])
    """
    offset_local = np.array([0.0, 0.0, +EE_TO_FINGERTIP], dtype=np.float32)
    offset_world = quat_rotate_vec(ee_quat_xyzw, offset_local)
    return ee_pos + offset_world


def extract_clamp_pose(
    bq: np.ndarray,
    ws: int,
    arm_offset: int,
    prev_clamp_quat: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract one arm's clamp (fingertip) pose with quat normalization + temporal consistency.

    Reads the EE body row from ``bq`` at ``ws + arm_offset``, computes the
    clamp position via :func:`compute_clamp_pos`, and returns a quaternion
    that is both ``w >= 0`` normalized and sign-consistent with
    ``prev_clamp_quat`` (avoids w≈0 sign flip discontinuity, Bug #2 fix).

    Args:
        bq: World body_q numpy view, shape ``[total_bodies, 7]``.
        ws: World start body index (``bws[w]``).
        arm_offset: EE body offset within the arm. Use ``EE_BODY_OFFSET`` for
            left arm, ``FRANKA_NUM_JOINTS + EE_BODY_OFFSET`` for right arm.
        prev_clamp_quat: Previous-frame clamp quat ``[qx, qy, qz, qw]``,
            shape ``[4]``, dtype float32. Caller is responsible for updating
            this with the returned ``clamp_quat`` after the call.

    Returns:
        Two-tuple ``(clamp_pos, clamp_quat)``:
        - ``clamp_pos``: Fingertip world position ``[3]`` [m] (NEW array).
        - ``clamp_quat``: Fingertip orientation ``[qx, qy, qz, qw]``,
          ``w >= 0`` normalized + temporally consistent with ``prev_clamp_quat``
          (NEW array, not a view into ``bq``).

    Notes:
        - This function does **not** update ``prev_clamp_quat``; the caller
          must do ``self._prev_clamp_X_quat[w] = clamp_quat.copy()`` after.
        - Returned arrays are NEW allocations (not views into ``bq``).
        - For envs that do not need temporal consistency (e.g., AC reward
          path uses the un-temporally-corrected quat), call instead the
          underlying primitives ``normalize_quat_w_positive`` directly.
    """
    ee_idx = ws + arm_offset
    ee_pos = bq[ee_idx][:3]
    ee_quat = bq[ee_idx][3:7]
    clamp_pos = compute_clamp_pos(ee_pos, ee_quat)
    clamp_quat = normalize_quat_w_positive(ee_quat)
    clamp_quat = temporal_quat_consistency(clamp_quat, prev_clamp_quat)
    return clamp_pos, clamp_quat


def make_arm_joint_mask(coord_count):
    """Create boolean mask: True for arm joints, False for finger joints.

    Gripper joints: GRIPPER_JOINT_RANGE (left arm) and JOINTS_PER_ARM + GRIPPER_JOINT_RANGE (right arm).
    """
    mask = np.ones(coord_count, dtype=bool)
    for fc in (*GRIPPER_JOINT_RANGE, *(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)):
        mask[fc] = False
    return mask


FINGER_JOINT_INDICES = tuple(GRIPPER_JOINT_RANGE) + tuple(JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE)


# =============================================================================
# Per-World Reset Helpers (Item 1 refactor, DEFINE.md v6 / api-design.md v5 §2)
# =============================================================================


def restore_world_body_state(
    *,
    bq: np.ndarray,
    bqd: np.ndarray,
    prev: np.ndarray | None,
    settled_body_q: np.ndarray,
    settled_body_qd: np.ndarray,
    w: int,
    bws: np.ndarray,
) -> None:
    """Restore one world's body state slice from the settled-state cache.

    Keyword-only arguments (``*,``) to prevent positional swap bugs (e.g.,
    accidentally passing ``bqd`` where ``bq`` expected — same shape/dtype,
    would silently corrupt state).

    Performs three slice copies for world index ``w``:
    - ``bq[start:end] <- settled_body_q[start:end]``
    - ``bqd[start:end] <- settled_body_qd[start:end]``
    - ``prev[start:end] <- settled_body_q[start:end]`` (skipped when ``prev`` is None)

    Where ``start, end = bws[w], bws[w + 1]``.

    Args:
        bq: Live ``state_0.body_q`` numpy view, shape ``[total_bodies, 7]``.
            Mutated in place (slice assignment).
        bqd: Live ``state_0.body_qd`` numpy view, shape ``[total_bodies, 6]``
            (vel: lin [m/s] + ang [rad/s]). Mutated in place.
        prev: Live ``solver.body_q_prev`` numpy view, shape
            ``[total_bodies, 7]``, mutated in place — or ``None`` on the
            SolverMuJoCo path (S4b: no ``body_q_prev`` buffer exists; the
            reset is carried by joint_q seeding instead, so the prev
            maintenance is correctly skipped).
        settled_body_q: Cached settled state ``body_q``, shape
            ``[total_bodies, 7]``, taken from a prior P0 settle.
        settled_body_qd: Cached settled state ``body_qd``, shape
            ``[total_bodies, 6]``.
        w: World index (0-based).
        bws: ``model.body_world_start`` numpy view, shape
            ``[world_count + 1]``.

    Raises:
        ValueError: If ``settled_body_q.shape != bq.shape`` or
            ``settled_body_qd.shape != bqd.shape`` (shape mismatch indicates
            cache/live state divergence).

    Returns:
        None. Mutates ``bq``, ``bqd``, ``prev`` in place.
    """
    if settled_body_q.shape != bq.shape:
        raise ValueError(f"settled_body_q shape {settled_body_q.shape} != bq shape {bq.shape}")
    if settled_body_qd.shape != bqd.shape:
        raise ValueError(f"settled_body_qd shape {settled_body_qd.shape} != bqd shape {bqd.shape}")
    start, end = bws[w], bws[w + 1]
    bq[start:end] = settled_body_q[start:end]
    bqd[start:end] = settled_body_qd[start:end]
    if prev is not None:
        prev[start:end] = settled_body_q[start:end]


def derive_cable_joint_q_from_tangents(
    body_q_np: np.ndarray, cable_bodies: list[int]
) -> tuple[list[float], list[float]]:
    """Derive the rigid-link cable joint coordinates from segment poses (S4b reset-path, C-1 PRIMARY).

    The settled cable's ``state.joint_q`` is reconstructed from the live ``body_q`` alone — NO
    cross-script cache state (the C-1 decision; a settle-time joint_q cache stays optional/secondary).
    The FREE root takes body[0]'s pose verbatim (7 coords [m + unit quat]); each REVOLUTE segment
    angle is the SIGNED angle between consecutive segment tangents (quat-rotated local +Z) about the
    joint's bend axis (the parent segment's local +X in world).

    The X-axis chain cannot represent out-of-plane (non-bend-axis) tangent components, so the
    derive→FK roundtrip carries a metric floor ~1e-3 (rad / m-scale) on a contact-settled cable —
    callers assert reconstruction at that tolerance, not exactness.

    Returns:
        (root7, seg_angles): the FREE-root 7 coords and the per-segment-joint angles [rad].
    """
    b0 = body_q_np[cable_bodies[0]]
    root7 = [float(x) for x in b0[:7]]
    seg_angles: list[float] = []
    for i in range(1, len(cable_bodies)):
        qp = [float(x) for x in body_q_np[cable_bodies[i - 1]][3:7]]
        qc = [float(x) for x in body_q_np[cable_bodies[i]][3:7]]
        tp = wp.quat_rotate(wp.quat(*qp), wp.vec3(0.0, 0.0, 1.0))
        tc = wp.quat_rotate(wp.quat(*qc), wp.vec3(0.0, 0.0, 1.0))
        ax = wp.quat_rotate(wp.quat(*qp), wp.vec3(1.0, 0.0, 0.0))
        tpn = np.array([tp[0], tp[1], tp[2]])
        tcn = np.array([tc[0], tc[1], tc[2]])
        axn = np.array([ax[0], ax[1], ax[2]])
        s = float(np.dot(np.cross(tpn, tcn), axn))
        c = float(np.dot(tpn, tcn))
        seg_angles.append(float(np.arctan2(s, c)))
    return root7, seg_angles


def seed_cable_joint_state(
    state,
    model,
    cable_joints: list[int],
    root7: list[float],
    seg_angles: list[float],
    *,
    dr_xy: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Seed ``state.joint_q``/``joint_qd`` for the rigid-link cable at reset (S4b, mujoco path).

    Writes the FREE-root 7 coords — with the cable-XY-DR offset ``dr_xy`` added to the root x/y
    translation DOFs (the S4b DR seam) — plus the derived segment angles, zeros the cable
    ``joint_qd`` slice (post-settle rest), and runs ``eval_fk`` so ``body_q`` is consistent before
    the next physics step. The ARM joint slice is untouched (the per-step arm overwrite owns it).
    This replaces the VBD ``body_q_prev`` reset maintenance on the mujoco path (MuJoCo derives
    velocity from qvel, not a previous-position buffer).
    """
    jqs = model.joint_q_start.numpy()
    jqds = model.joint_qd_start.numpy()
    free_jid = cable_joints[0]
    q0 = int(jqs[free_jid])
    qd0 = int(jqds[free_jid])
    jq = state.joint_q.numpy()
    jqd = state.joint_qd.numpy()
    jq[q0 : q0 + 7] = root7
    jq[q0] += dr_xy[0]
    jq[q0 + 1] += dr_xy[1]
    jq[q0 + 7 : q0 + 7 + len(seg_angles)] = seg_angles
    jqd[qd0 : qd0 + 6 + len(seg_angles)] = 0.0
    state.joint_q.assign(jq)
    state.joint_qd.assign(jqd)
    newton.eval_fk(model, state.joint_q, state.joint_qd, state)


def restore_ee_targets_per_world(
    *,
    ee_target_right: np.ndarray,
    ee_target_left: np.ndarray,
    ee_quat_right: np.ndarray,
    ee_quat_left: np.ndarray,
    settled_ee_r_pos: np.ndarray,
    settled_ee_l_pos: np.ndarray,
    settled_ee_r_quat: np.ndarray,
    settled_ee_l_quat: np.ndarray,
    w: int,
) -> None:
    """Restore both arms' EE target pose for world ``w`` from the settled cache.

    Keyword-only arguments (``*,``) to prevent R/L swap bugs.

    Replaces the per-world EE target/quat slots with the settled values
    (deep-copy via ``.copy()`` to prevent shared-reference mutation across
    worlds). Used inside ``_reset_worlds`` per-env-id loop.

    Args:
        ee_target_right: Per-world right EE target positions
            ``[world_count, 3]`` in world frame [m]. Mutated at index ``w``.
        ee_target_left: Per-world left EE target positions, same shape.
        ee_quat_right: Per-world right EE target quats ``[world_count, 4]``
            (qx, qy, qz, qw). Mutated at index ``w``.
        ee_quat_left: Per-world left EE target quats, same shape.
        settled_ee_r_pos: Cached settled right EE position ``[3]`` [m].
        settled_ee_l_pos: Cached settled left EE position ``[3]`` [m].
        settled_ee_r_quat: Cached settled right EE quat ``[4]``.
        settled_ee_l_quat: Cached settled left EE quat ``[4]``.
        w: World index (0-based).

    Returns:
        None. Mutates the four ``ee_target_*`` / ``ee_quat_*`` arrays at
        row ``w``.
    """
    ee_target_right[w] = settled_ee_r_pos.copy()
    ee_target_left[w] = settled_ee_l_pos.copy()
    ee_quat_right[w] = settled_ee_r_quat.copy()
    ee_quat_left[w] = settled_ee_l_quat.copy()


def assign_world_states_to_sim(
    state_0,
    solver,
    bq: np.ndarray,
    bqd: np.ndarray,
    prev: np.ndarray,
) -> None:
    """Push CPU-side ``bq``/``bqd``/``prev`` arrays back to the GPU sim state.

    Three ``warp.array.assign`` calls. Use this after a per-world reset loop
    completes its CPU mutations and before the next physics step.

    Args:
        state_0: Newton ``State`` instance whose ``body_q`` and ``body_qd``
            are being updated.
        solver: Newton ``SolverVBD`` instance whose ``body_q_prev`` is being
            updated (separate buffer for VBD prev-frame integration).
        bq: Updated CPU view of ``state_0.body_q``, shape
            ``[total_bodies, 7]``.
        bqd: Updated CPU view of ``state_0.body_qd``, shape
            ``[total_bodies, 6]``.
        prev: Updated CPU view of ``solver.body_q_prev``, shape
            ``[total_bodies, 7]``.

    Returns:
        None. Mutates ``state_0.body_q``, ``state_0.body_qd``, and
        ``solver.body_q_prev`` (GPU side) in place.
    """
    state_0.body_q.assign(bq)
    state_0.body_qd.assign(bqd)
    # SC3 flip-prep: SolverMuJoCo has no body_q_prev (VBD-only); hasattr-skip is VBD-byte-identical.
    if hasattr(solver, "body_q_prev") and solver.body_q_prev is not None:
        solver.body_q_prev.assign(prev)


def reset_dahl_friction_for_envs(
    solver,
    jws: np.ndarray,
    env_ids: np.ndarray | list[int],
) -> None:
    """Reset per-joint Dahl friction state for the specified env ids (no-op if disabled).

    Zeros ``joint_C_fric`` and ``joint_sigma_prev`` slices for each world in
    ``env_ids``. Skipped silently when the solver has no Dahl friction
    enabled.

    Args:
        solver: Newton ``SolverVBD`` instance. Inspected for
            ``enable_dahl_friction`` attribute (truthy -> reset, else no-op).
        jws: Joint world start indices, shape ``[world_count + 1]``. Used to
            compute per-world joint slice ``[js, je) = [jws[w], jws[w + 1])``.
        env_ids: World indices to reset (any iterable of ints; cast inside).

    Returns:
        None. Mutates ``solver.joint_C_fric`` and
        ``solver.joint_sigma_prev`` in place (GPU side).
    """
    if not (hasattr(solver, "enable_dahl_friction") and solver.enable_dahl_friction):
        return
    cf = solver.joint_C_fric.numpy()
    sp = solver.joint_sigma_prev.numpy()
    for w in env_ids:
        w = int(w)
        js, je = jws[w], jws[w + 1]
        cf[js:je] = 0.0
        sp[js:je] = 0.0
    solver.joint_C_fric.assign(cf)
    solver.joint_sigma_prev.assign(sp)


# =============================================================================
# FK / IK Utilities (precondition building)
# =============================================================================


def build_fk_and_init(left_finger_pos, right_finger_pos, device=None):
    """Build FK model and set initial finger positions.

    Args:
        left_finger_pos: Left finger joint position.
        right_finger_pos: Right finger joint position.
        device: Warp device string (e.g. "cuda:0"). Defaults to module DEVICE.

    Returns:
        (fk_model, fk_state, fk_jq_np) tuple.
    """
    fk_model = build_fk_model(device=device)
    fk_state = fk_model.state()

    fk_jq = fk_state.joint_q.numpy()
    fk_tp = fk_model.joint_target_pos.numpy()
    fk_jq[:] = fk_tp[:]
    fk_jq[GRIPPER_DRIVER_JOINT_IDX[0]] = left_finger_pos
    fk_jq[GRIPPER_DRIVER_JOINT_IDX[1]] = left_finger_pos
    fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[0]] = right_finger_pos
    fk_jq[JOINTS_PER_ARM + GRIPPER_DRIVER_JOINT_IDX[1]] = right_finger_pos
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    return fk_model, fk_state, fk_jq.copy()


def solve_ik_single(fk_model, fk_state, target_left, target_right, device):
    """Solve IK for both arms (single problem, used for precondition init).

    Returns:
        [joint_coord_count] numpy array of solved joint positions.
    """
    left_ee = EE_BODY_OFFSET
    right_ee = FRANKA_NUM_JOINTS + EE_BODY_OFFSET

    target_rot = wp.array(
        [wp.vec4(*IK_ROT_TARGET_XYZW)],
        dtype=wp.vec4,
        device=device,
    )
    objectives = [
        IKObjectivePosition(
            link_index=left_ee,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.array([target_left], dtype=wp.vec3, device=device),
            weight=1.0,
        ),
        IKObjectivePosition(
            link_index=right_ee,
            link_offset=wp.vec3(0, 0, 0),
            target_positions=wp.array([target_right], dtype=wp.vec3, device=device),
            weight=1.0,
        ),
        IKObjectiveRotation(
            link_index=left_ee, link_offset_rotation=wp.quat_identity(), target_rotations=target_rot, weight=0.5
        ),
        IKObjectiveRotation(
            link_index=right_ee, link_offset_rotation=wp.quat_identity(), target_rotations=target_rot, weight=0.5
        ),
        IKObjectiveJointLimit(
            joint_limit_lower=fk_model.joint_limit_lower, joint_limit_upper=fk_model.joint_limit_upper, weight=10.0
        ),
    ]
    ik_solver = IKSolver(fk_model, n_problems=1, objectives=objectives)

    fk_jq = fk_state.joint_q.numpy()
    jq_in = wp.array(fk_jq.reshape(1, -1), dtype=float, device=device)
    jq_out = wp.zeros((1, fk_model.joint_coord_count), dtype=float, device=device)
    ik_solver.step(jq_in, jq_out, iterations=IK_ITERATIONS_INIT, step_size=IK_STEP_SIZE)

    return jq_out.numpy()[0]


# =============================================================================
# Solver Factory (Option-E SOLVER_BACKEND SSOT)
# =============================================================================


def make_solver(model, backend=SOLVER_BACKEND, use_mujoco_cpu=USE_MUJOCO_CPU, enable_cable_contacts=False):
    """Construct the physics solver for ``model`` per the ``SOLVER_BACKEND`` SSOT.

    Args:
        model: the finalized Newton model the solver steps.
        backend: ``"vbd"`` (default) or ``"mujoco"`` -- selects :class:`SolverVBD`
            vs :class:`SolverMuJoCo`. Defaults to ``task_config.SOLVER_BACKEND``.
        use_mujoco_cpu: run MuJoCo on CPU (Opt-1/S4-S7 smoke); ``False`` = GPU (S8).
            Only consulted by the ``"mujoco"`` backend.
        enable_cable_contacts: S4a (D-S4a-3) -- ``True`` enables MuJoCo contacts
            (``disable_contacts=False``) with ``nconmax=MUJOCO_NCONMAX`` for the
            rigid-link cable scene. Default ``False`` keeps the Opt-1 contact-free
            arm smoke EXACTLY as before; the ``"vbd"`` branch never reads it.

    Returns:
        The constructed solver. With the default ``"vbd"`` backend this is
        byte-identical to ``SolverVBD(model, iterations=VBD_ITERATIONS)``.
    """
    if backend == "mujoco":
        # fork-B R5-2/R-b tripwire (D1 spec sec 4; charter sec 4-B): use_mujoco_cpu steps ONLY the single-world
        # CPU template -- worlds>0 would be silently frozen garbage. The factory is the last common point that
        # sees both flags, so the wrong combination is refused HERE, mechanically, for every caller.
        if use_mujoco_cpu and model.world_count > 1 and os.environ.get("THREAD_ALLOW_CPU_MULTIWORLD") != "1":
            raise RuntimeError(
                "use_mujoco_cpu=True steps ONLY the single-world CPU template -- worlds>0 would be silently "
                "frozen (COMP3_PLAN_ROUTEEXEC_GRASPACT_COORD_20260708.md:79; ENV_MULTIWORLD_SUBSTRATE_CHARTER_"
                "RSTECHLEAD_20260716.md). Use world_count=1 (fork B), or use_mujoco_cpu=False (S8, unvalidated), "
                "or set THREAD_ALLOW_CPU_MULTIWORLD=1 (diagnostics ONLY -- record the use in your artifact)."
            )
        if enable_cable_contacts:
            return SolverMuJoCo(
                model,
                use_mujoco_cpu=use_mujoco_cpu,
                separate_worlds=(model.world_count > 1),
                update_data_interval=1,
                disable_contacts=False,
                nconmax=MUJOCO_NCONMAX,
                solver="newton",
                integrator="implicitfast",
            )
        return SolverMuJoCo(
            model,
            use_mujoco_cpu=use_mujoco_cpu,
            separate_worlds=(model.world_count > 1),
            update_data_interval=1,
            disable_contacts=True,
            solver="newton",
            integrator="implicitfast",
        )
    return SolverVBD(model, iterations=VBD_ITERATIONS)


def _wire_s6_grasp_solref(solver, scene_info=None):
    """Post-``make_solver`` S6_GRASP wiring: poke the negative ``MUJOCO_PAD_SOLREF`` into BOTH ``mj_model``
    AND ``mjw_model.geom_solref`` (the GPU/step-read array), then stiffen the gripper 4-bar CONNECT
    equalities + run the I11 readback asserts. Relocated from ``test_newton_clip_routing.py`` to base +
    GENERALIZED for multi-world: ``build_multiworld_scene(grasp_actuation=True)`` calls this after
    ``make_solver`` (``world_count`` worlds); ``build_scene`` calls it single-world (byte-identical here).

    Multi-world structure (empirically verified, ``log.md`` 2026-06-28): ``solver.mj_model`` is a SINGLE
    1-world host template (``nbody``/``ngeom``/``neq`` invariant across ``world_count``) while
    ``solver.mjw_model`` carries the leading world axis (``geom_solref`` shape ``(world_count, ngeom, 2)``;
    ``geom_condim`` shape ``(ngeom,)`` shared, no world axis). Hence the mjw ``geom_solref`` poke writes ALL
    worlds (``arr[:, g, :]``) while the eq-stiffen on the single-template ``mj_model`` finds the per-template
    4 CONNECT eqs (``_n_stiff == 4`` regardless of ``world_count`` -- the ``6*world_count`` scaling is on the
    NEWTON ``model.equality_constraint_count``, asserted build-side). mjw eq re-poke is DEFERRED (the proven
    faithful config is CPU/``mj_model``; GPU/cg eq re-poke is a separate later gap).

    solref is NOTIFY-FRAGILE (``_update_geom_properties`` re-derives ``geom_solref`` from ke/kd on any SHAPE
    notify); durable here only because production issues no post-construct SHAPE notify.
    """
    import mujoco

    m = solver.mj_model
    mjw = getattr(solver, "mjw_model", None)
    GEOM_CAPSULE = int(mujoco.mjtGeom.mjGEOM_CAPSULE)

    def _mjw_row(field, g):
        arr = getattr(mjw, field).numpy()
        if arr.ndim == 1:  # (ngeom,)  e.g. geom_condim (shared across worlds)
            return arr[g]
        if arr.ndim == 3:  # (world_count, ngeom, k)  leading world axis -> world 0 (representative)
            return arr[0][g]
        return arr[g]  # (ngeom, k)  e.g. geom_solref without a world axis

    pad_geoms, cable_geoms = [], []
    for g in range(m.ngeom):
        gname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bid = int(m.geom_bodyid[g])
        bname = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, bid) or "").lower()
        if "pad" in (gname + bname):
            pad_geoms.append(g)
        elif int(m.geom_type[g]) == GEOM_CAPSULE:
            cable_geoms.append(g)
    assert pad_geoms, "S6_GRASP: no pad geoms located in mj_model"

    # Poke the negative PAD_SOLREF into BOTH mj_model AND mjw_model (the GPU/step-read array, ALL worlds).
    pad_solref = np.array(MUJOCO_PAD_SOLREF, dtype=m.geom_solref.dtype)
    for g in pad_geoms:
        m.geom_solref[g] = pad_solref
    mjw_solref_rb = None
    if mjw is not None:
        arr = mjw.geom_solref.numpy()
        val = np.array(MUJOCO_PAD_SOLREF, dtype=arr.dtype)
        if arr.ndim == 3:  # (world_count, ngeom, 2) -> write ALL worlds (covers world_count in {1, N})
            for g in pad_geoms:
                arr[:, g, :] = val
        else:  # (ngeom, 2)
            for g in pad_geoms:
                arr[g, :] = val
        mjw.geom_solref.assign(arr)
        mjw_solref_rb = [float(x) for x in np.asarray(_mjw_row("geom_solref", pad_geoms[0])).ravel()[:2]]

    # I11 readbacks + fail-loud asserts.
    want = int(MUJOCO_CONTACT_CONDIM)
    mj_pad_condim = int(m.geom_condim[pad_geoms[0]])
    mj_cable_condim = int(m.geom_condim[cable_geoms[0]]) if cable_geoms else None
    mjw_pad_condim = int(np.asarray(_mjw_row("geom_condim", pad_geoms[0])).ravel()[0]) if mjw is not None else None
    mjw_cable_condim = (
        int(np.asarray(_mjw_row("geom_condim", cable_geoms[0])).ravel()[0])
        if (cable_geoms and mjw is not None)
        else None
    )
    mj_priority = int(m.geom_priority[pad_geoms[0]]) if hasattr(m, "geom_priority") else None
    mj_roll = float(m.geom_friction[pad_geoms[0]][2])

    assert mj_pad_condim == want, f"S6_GRASP: mj pad condim={mj_pad_condim}!={want}"
    if mj_cable_condim is not None:
        assert mj_cable_condim == want, f"S6_GRASP: mj cable condim={mj_cable_condim}!={want}"
    if mjw is not None:
        assert mjw_pad_condim == want, f"S6_GRASP: mjw pad condim={mjw_pad_condim}!={want} (GPU-inert!)"
        if mjw_cable_condim is not None:
            assert mjw_cable_condim == want, f"S6_GRASP: mjw cable condim={mjw_cable_condim}!={want}"
        assert (
            mjw_solref_rb is not None
            and abs(mjw_solref_rb[0] - MUJOCO_PAD_SOLREF[0]) < 1e-3
            and abs(mjw_solref_rb[1] - MUJOCO_PAD_SOLREF[1]) < 1e-3
        ), f"S6_GRASP: mjw solref={mjw_solref_rb}!={list(MUJOCO_PAD_SOLREF)} (GPU-inert!)"
    assert mj_priority == 1, f"S6_GRASP: pad geom_priority={mj_priority}!=1 (H4: keep shipped, don't poke 0)"
    assert abs(mj_roll - float(MUJOCO_PAD_ROLL_FRICTION)) < 1e-6, (
        f"S6_GRASP: pad rolling friction={mj_roll}!={MUJOCO_PAD_ROLL_FRICTION}"
    )

    # FAITHFUL 4-bar: stiffen the gripper CONNECT equalities (soft default eq_solref lets the 4-bar LOOP
    # flop). mj_model is the SINGLE-world template -> 4 CONNECT eqs regardless of world_count (the per-world
    # replication lives on the NEWTON model / mjw; mjw eq re-poke deferred -- CPU/mj_model is the proven
    # faithful config). The negative geom_solref poke above is what reaches the GPU step per-world.
    _n_stiff = 0
    _n_stiff_enabled = 0
    for i in range(int(m.neq)):
        if int(m.eq_type[i]) == int(mujoco.mjtEq.mjEQ_CONNECT):
            m.eq_solref[i] = [0.001, 1.0]
            m.eq_solimp[i] = [0.99, 0.9995, 0.0001, 0.5, 2.0]
            _n_stiff += 1
            if int(m.eq_active0[i]) == 1:
                _n_stiff_enabled += 1
    # The PERCLIP_PIN test harness (test_newton_clip_routing.py) may pre-allocate one DISABLED connect PER cable body
    # (e.g. 40 -- the per-clip clip-retention pin candidates; exactly one is activated mid-episode on the verified
    # seat). They are stiffened here too (so the activated one is rigid) but the 4-bar invariant asserts on the
    # ENABLED count -> 4. Default/build_multiworld has no disabled connect, so _n_stiff_enabled == _n_stiff == 4
    # (backward-identical, regardless of how many disabled connects exist).
    assert _n_stiff_enabled == 4, (
        f"S6_GRASP: expected 4 ENABLED CONNECT 4-bar eqs to stiffen, got {_n_stiff_enabled} "
        f"(neq={int(m.neq)}, total connect stiffened={_n_stiff})"
    )

    rb = {
        "pad_geoms": len(pad_geoms),
        "cable_geoms": len(cable_geoms),
        "mj_pad_condim": mj_pad_condim,
        "mjw_pad_condim": mjw_pad_condim,
        "mj_cable_condim": mj_cable_condim,
        "mjw_cable_condim": mjw_cable_condim,
        "mjw_solref": mjw_solref_rb,
        "mj_priority": mj_priority,
        "mj_roll": mj_roll,
        "connects_stiffened": _n_stiff,
    }
    print(
        f"  [S6_GRASP] solref poked + I11 asserts OK: pad_geoms={len(pad_geoms)} "
        f"condim mj_pad={mj_pad_condim}/mjw_pad={mjw_pad_condim} mj_cable={mj_cable_condim}/"
        f"mjw_cable={mjw_cable_condim} solref_mjw={mjw_solref_rb} priority={mj_priority} roll={mj_roll} "
        f"connects_stiffened={_n_stiff}(eq_solref->[0.001,1])"
    )
    return rb


# =============================================================================
# Scene Building
# =============================================================================


def build_multiworld_scene(  # noqa: C901 (pre-existing scene-builder complexity; minimal additive float param)
    fk_model,
    fk_state,
    world_count,
    device,
    cable_start_pos=None,
    add_support_clips=True,
    add_target_clip=False,
    grasp_actuation=False,
    target_clip_float_z=0.0,
    add_c2_clip=False,
    c2_xy=None,
    perclip_pin=False,
):
    """Build multi-world physics scene with kinematic arms + cable.

    Args:
        fk_model: FK model.
        fk_state: FK state (initialized with finger positions).
        world_count: number of parallel worlds.
        device: CUDA device string.
        cable_start_pos: (x, y, z) 3D start position for cable.
            Defaults to table-level: (GRASP_X, cable_y_start, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS).
        add_support_clips: If True, add static support clips (ApproachCable).
            If False, omit them (InsertIntoClip, AerialRegrasp).
        add_target_clip: If True, add clip C1 V-groove geometry at (CLIP1_X, CLIP1_Y).
            Used by Grip (Clamp/Unclamp) and InsertIntoClip envs.
        add_c2_clip: If True, add a second collidable C2 V-groove clip at :paramref:`c2_xy` (route-executor
            comp5: multi-world env-core route seating + C2-seating video). Ports the proven single-world CLIP2
            contact config (:data:`MUJOCO_CONTACT_KE` [Pa], :data:`MUJOCO_CONTACT_KD` [Pa·s/m]). Default False
            keeps the build byte-identical.
        c2_xy: C2 clip center (x, y) [m], param-sourced by the caller (the route env passes
            :data:`route_env_config.ROUTE_C2_XY`). Required when :paramref:`add_c2_clip` is True.
        grasp_actuation: ``mujoco`` backend only. If True, wire the DYNAMIC dual-arm gripper (the
            AerialRegrasp L-hold precondition): L+R POSITION servo on the driver joints, the koshape
            4-bar CONNECT + L-R follower-mirror equalities (by label), and the S5 contact families
            (condim=6 + pad rolling friction). Mirrors the proven ``build_scene(grasp_actuation=True)``
            (``test_newton_clip_routing.py``) and calls :func:`_wire_s6_grasp_solref` after ``make_solver``.
            Default ``False`` keeps the build byte-identical (ApproachCable / Grip NON-breaking).
        target_clip_float_z: Height [m] to float the C1 target clip above the table (route
            ``CLIP_FLOAT_Z`` env-gate override). Default ``0.0`` = table-level, non-breaking.
    """
    # Default cable position: on table
    if cable_start_pos is None:
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = CLIP1_Y - cable_half_len
        cable_start_pos = (GRASP_X, cable_y_start, TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS)
    else:
        cable_half_len = CABLE_SEGMENTS * CABLE_SEG_LEN / 2
        cable_y_start = CLIP1_Y - cable_half_len
        cable_start_pos = (cable_start_pos[0], cable_y_start, cable_start_pos[2])

    proto = newton.ModelBuilder()

    # Robot arms: VBD = jointless kinematic bodies (FK body_q); MuJoCo = articulated UR5e+Robotiq.
    if SOLVER_BACKEND == "mujoco":
        # Option-E Opt-1 (SC2a, D-Opt1-1): articulated UR5e+Robotiq per arm via the probe-validated
        # add_mjcf recipe (Robotiq <tendon> stripped so SolverMuJoCo constructs). S4a (D-S4a-4):
        # the cable is the rigid-link REVOLUTE chain (CABLE joints are MuJoCo-rejected,
        # solver_mujoco.py:292); contacts enabled via make_solver(enable_cable_contacts=True), so
        # the A-1 VISIBLE-only pass below is LOAD-BEARING (cycle-2 CRITICAL: without it the whole
        # arm collision set goes live). joint_q kinematic re-pose driving = SC2b.
        if grasp_actuation:
            # warm-register the SHAPE custom attrs (mujoco:condim) BEFORE finalize so put_model bakes
            # condim into BOTH mj_model and mjw_model (mirror build_scene test:1169-1173; idempotent).
            SolverMuJoCo.register_custom_attributes(proto)
        mj_left_ss = proto.shape_count
        add_ur5e_robotiq(
            proto,
            wp.transform(ROBOT_LEFT_BASE, wp.quat_identity()),
            robotiq_xml=ROBOTIQ_STRIPPED_XML,
            skip_equality_constraints=True,
        )
        add_ur5e_robotiq(
            proto,
            wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
            robotiq_xml=ROBOTIQ_STRIPPED_XML,
            skip_equality_constraints=True,
        )
        mj_arm_se = proto.shape_count
        # A-1 VISIBLE-only pass (probe-proven, F4c): clear COLLIDE on non-pad arm shapes (→ MuJoCo
        # contype=conaffinity=0); KEEP COLLIDE on the gripper PAD geoms (cable grasp).
        _labels = list(getattr(proto, "shape_label", []) or [])
        pad_shape_idx = []  # gripper PAD collision shapes (S6_GRASP condim/rolling targets; [] if no grasp)
        for si in range(mj_left_ss, mj_arm_se):
            lbl = str(_labels[si]) if si < len(_labels) else ""
            if "pad" not in lbl.lower():
                proto.shape_flags[si] = int(newton.ShapeFlags.VISIBLE)
            else:
                pad_shape_idx.append(si)

        # Cable: rigid-link REVOLUTE chain AFTER both arms (D-S4a-1/4; registers the MuJoCo custom
        # JOINT_DOF attrs + issues the FREE root + segment joints consecutively).
        cable_bodies_proto, cable_joints_proto, _cable_sr = add_revolute_cable(
            proto,
            start_pos=cable_start_pos,
            direction=(0, 1, 0),
        )
        cable_bodies_per_world = len(cable_bodies_proto)
        cable_body_offset = cable_bodies_proto[0]

        # (d2) PERCLIP_PIN -- pre-allocate ONE DISABLED connect-to-world eq PER cable body, mirroring the
        # producer (test_newton_clip_routing.py:1405). The route drive activates exactly the one bound to the
        # runtime C1 seat, mid-episode, by WORLD-POSITION match. Default OFF keeps the build byte-identical
        # (an eq with enabled=False registers but never constrains; the 4-bar ENABLED-count assert stays 4).
        #
        # This is the mechanism the multi-world env-core was MISSING while the single-world producer had it --
        # i.e. the env was built non-conformant to the banked spec, which NAMES the clip-retention pin as the
        # routing mechanism (RS71 §4). Wiring it is compliance, not a new exception. But it is wired here ONLY
        # to MEASURE (the (d2) question: does open-loop actually fail when the pin genuinely holds?) -- making
        # it permanent is a premise-scope decision and belongs to Rs, not to this flag.
        if perclip_pin:
            for _pb in cable_bodies_proto:
                proto.add_equality_constraint_connect(
                    body1=int(_pb),
                    body2=-1,  # world
                    anchor=wp.vec3(0.0, 0.0, 0.0),
                    label=f"perclip_pin_{int(_pb)}",
                    enabled=False,
                )
            print(
                f"  [PERCLIP_PIN] pre-allocated {len(cable_bodies_proto)} DISABLED connect-to-world eqs/world "
                f"(inert until the route drive activates the C1 seat body)"
            )

        # Cable ↔ non-pad-arm filter pairs (explicit, label-based; pads keep cable contacts).
        for cable_si in range(_cable_sr[0], _cable_sr[1]):
            for arm_si in range(mj_left_ss, mj_arm_se):
                lbl = str(_labels[arm_si]) if arm_si < len(_labels) else ""
                if "pad" not in lbl.lower():
                    proto.add_shape_collision_filter_pair(cable_si, arm_si)

        # --- S6_GRASP actuation + 4-bar equalities + S5 contact families (gated; mirrors the proven
        # build_scene grasp_actuation, test:1336-1421). default False -> skipped -> AC/Grip byte-identical.
        # Wired on the proto BEFORE replicate so every world inherits the servo + eqs + condim. ---
        if grasp_actuation:
            # POSITION drivers on [6,10,20,24] = GRIPPER_DRIVER_JOINT_IDX + right arm (+JOINTS_PER_ARM).
            grasp_driver_joints = list(GRIPPER_DRIVER_JOINT_IDX) + [
                j + JOINTS_PER_ARM for j in GRIPPER_DRIVER_JOINT_IDX
            ]
            assert grasp_driver_joints == [6, 10, 20, 24], f"S6_GRASP driver index drift: {grasp_driver_joints}"
            for dof in grasp_driver_joints:
                proto.joint_target_mode[dof] = int(newton.JointTargetMode.POSITION)
                proto.joint_target_ke[dof] = GRIPPER_SERVO_TARGET_KE
                proto.joint_target_kd[dof] = GRIPPER_SERVO_TARGET_KD
                proto.joint_effort_limit[dof] = GRIPPER_DRIVER_EFFORT_LIMIT_NM
                proto.joint_target_pos[dof] = GRIPPER_DRIVER_OPEN_RAD  # start OPEN; runner schedules CLOSE
            # --- (d) P-D1 Option B (design doc ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md
            # v1.2 M-1): (i) NEUTRALIZE the imported ur5e.xml arm actuators (they are unwired from Newton
            # control -- ctrl==0 saturated pull, the tug-of-war finding b9eaaf9d93) + (ii) wire proto
            # POSITION servos (gripper mirror). Probe-only, flag-gated, default OFF -> byte-identical.
            # ARM_XML_ACT_NEUTRALIZE=1 alone = L-P0 mode (neutralize only, kinematic drive unchanged);
            # ARM_PD_DRIVE=1 implies neutralize + servo wiring + the ctrl drive branch (route env).
            # ARM_PD_GAINS_SCALE scales the SERVO ke/kd ONLY (L-P5 negative control) -- effort caps stay
            # at the real-robot spec (+-150/+-28 N.m, sec3.1 raise-forbidden). ---
            _apd_drive = os.environ.get("ARM_PD_DRIVE") == "1"
            _apd_neutralize = _apd_drive or os.environ.get("ARM_XML_ACT_NEUTRALIZE") == "1"
            if _apd_neutralize:
                _apd_ga = proto.custom_attributes.get("mujoco:actuator_gainprm")
                _apd_ba = proto.custom_attributes.get("mujoco:actuator_biasprm")
                assert (
                    _apd_ga is not None
                    and _apd_ba is not None
                    and len(_apd_ga.values) == 12
                    and len(_apd_ba.values) == 12
                ), (
                    "armpd-neutralize: expected EXACTLY the 12 imported ur5e arm actuators in the proto "
                    f"custom attrs, got gain={None if _apd_ga is None else len(_apd_ga.values)} "
                    f"bias={None if _apd_ba is None else len(_apd_ba.values)}"
                )
                # Capture the vendor values BEFORE stripping (L-P6 numeric-equality cross-check source).
                _apd_vendor = sorted(
                    (round(float(g[0]), 3), round(float(b[1]), 3), round(float(b[2]), 3))
                    for g, b in zip(_apd_ga.values, _apd_ba.values)
                )
                _apd_vendor_want = sorted([(2000.0, -2000.0, -400.0)] * 6 + [(500.0, -500.0, -100.0)] * 6)
                assert _apd_vendor == _apd_vendor_want, (
                    f"armpd-neutralize vendor cross-check: imported (gain0,bias1,bias2) set {_apd_vendor} != "
                    f"design table {_apd_vendor_want} -- the proto servo values would NOT re-implement the "
                    "same vendor actuators (design M-1 census)"
                )
                # v1.4-③ B1-STRIP (PRIMARY ruling): REMOVE the 12 imported actuator entries from EVERY
                # proto custom attribute of the mujoco:actuator frequency (list-based storage; the
                # same-count-per-frequency finalize validation requires clearing them all consistently).
                # At this build point ONLY the imported arm actuators exist in these attrs (asserted
                # above via the gain/bias tables) -- the gripper servos come from joint_target wiring,
                # not from these attrs. Result: nu = 16 (12 proto-wired arm + 4 gripper), NO inert set.
                for _apd_attr in proto.custom_attributes.values():
                    if getattr(_apd_attr, "frequency", None) == "mujoco:actuator":
                        assert isinstance(_apd_attr.values, list), (
                            f"armpd-strip: attr {_apd_attr.name} values is {type(_apd_attr.values).__name__}, not list"
                        )
                        if len(_apd_attr.values) == 0:
                            continue  # runtime/Control-assignment attr (e.g. 'ctrl') -- nothing to strip
                        assert len(_apd_attr.values) == 12, (
                            f"armpd-strip: attr {_apd_attr.name} count {len(_apd_attr.values)} != 12 "
                            "(unexpected non-imported actuator entries)"
                        )
                        del _apd_attr.values[:]
            if _apd_drive:
                # v1.7 §13 R-2: independent ke/kd scales (the kd/ke viscous-lag lever). Back-compat:
                # ARM_PD_GAINS_SCALE sets both unless the specific scale overrides it.
                _apd_scale = float(os.environ.get("ARM_PD_GAINS_SCALE", "1.0"))
                _apd_ke_scale = float(os.environ.get("ARM_PD_KE_SCALE", str(_apd_scale)))
                _apd_kd_scale = float(os.environ.get("ARM_PD_KD_SCALE", str(_apd_scale)))
                # local arm joint -> (ke, kd, effort cap): 0-2 = shoulder_pan/lift, elbow (size3);
                # 3-5 = wrist_1/2/3 (size1). ur5e.xml document order (cross-checked against the
                # captured vendor set above), same index space as the gripper drivers (gripper
                # starts at local 6).
                _apd_gains = {
                    0: (2000.0, 400.0, 150.0),
                    1: (2000.0, 400.0, 150.0),
                    2: (2000.0, 400.0, 150.0),
                    3: (500.0, 100.0, 28.0),
                    4: (500.0, 100.0, 28.0),
                    5: (500.0, 100.0, 28.0),
                }
                for _base in (0, JOINTS_PER_ARM):
                    for _j, (_ke, _kd, _eff) in _apd_gains.items():
                        _dof = _base + _j
                        proto.joint_target_mode[_dof] = int(newton.JointTargetMode.POSITION)
                        proto.joint_target_ke[_dof] = _ke * _apd_ke_scale
                        proto.joint_target_kd[_dof] = _kd * _apd_kd_scale
                        proto.joint_effort_limit[_dof] = _eff
                        proto.joint_target_pos[_dof] = float(proto.joint_q[_dof])
            # Restore the 4 gripper 4-bar connect equalities (follower<->coupler), BY LABEL for both arms
            # (the shipped XML <connect> loaded with skip_equality_constraints=True). 4 connects / proto.
            _blabel = [str(x) for x in (getattr(proto, "body_label", None) or getattr(proto, "body_key", []))]

            def _bodies_ending(suffix, lo, hi):
                return [i for i in range(lo, hi) if _blabel[i].endswith(suffix)]

            grasp_connects = []
            for lo, hi in [(0, ROBOT_BODIES_PER_ARM), (ROBOT_BODIES_PER_ARM, 2 * ROBOT_BODIES_PER_ARM)]:
                for side in ("right", "left"):
                    fb = _bodies_ending(f"{side}_follower", lo, hi)
                    cb = _bodies_ending(f"{side}_coupler", lo, hi)
                    if fb and cb:
                        grasp_connects.append((fb[0], cb[0]))
            for fb, cbb in grasp_connects:
                proto.add_equality_constraint_connect(
                    body1=fb, body2=cbb, anchor=wp.vec3(0.0, 0.0, 0.0), label=f"fourbar_{fb}_{cbb}", enabled=True
                )
            # FAITHFUL L-R FOLLOWER MIRROR per gripper (right_follower_joint = left_follower_joint,
            # polycoef [0,1,0,0,0]); the tendon-stripped XML dropped the symmetric coupling -> couple the
            # FOLLOWERS (the 4-bar is bistable; a driver mirror leaves each follower free to flip branch).
            _jlabel = [str(x) for x in (getattr(proto, "joint_label", None) or [])]

            def _joints_ending(suffix, lo, hi):
                return [i for i in range(lo, hi) if _jlabel[i].endswith(suffix)]

            grasp_mirrors = []
            for lo, hi in [(0, JOINTS_PER_ARM), (JOINTS_PER_ARM, 2 * JOINTS_PER_ARM)]:
                rf = _joints_ending("right_follower_joint", lo, hi)
                lf = _joints_ending("left_follower_joint", lo, hi)
                assert rf and lf, (
                    f"S6_GRASP: follower-mirror joints unresolved by label in [{lo},{hi}): rf={rf} lf={lf}"
                )
                proto.add_equality_constraint_joint(
                    joint1=rf[0],
                    joint2=lf[0],
                    polycoef=[0.0, 1.0, 0.0, 0.0, 0.0],
                    label=f"follower_mirror_{rf[0]}_{lf[0]}",
                    enabled=True,
                )
                grasp_mirrors.append((rf[0], lf[0]))
            assert sorted(j for p in grasp_mirrors for j in p) == sorted(d + 3 for d in grasp_driver_joints), (
                f"S6_GRASP: follower-mirror by-label {grasp_mirrors} != "
                f"SSOT followers {[d + 3 for d in grasp_driver_joints]}"
            )
            # Build-time S5 contact families: condim=6 on pad+cable shapes + rolling friction on pads ->
            # baked into BOTH mj_model AND mjw_model at put_model (the negative PAD_SOLREF has no build-time
            # path -> poked post-make_solver by _wire_s6_grasp_solref).
            _condim_attr = proto.custom_attributes.get("mujoco:condim")
            assert _condim_attr is not None, "S6_GRASP: mujoco:condim custom attribute not registered"
            if _condim_attr.values is None:
                _condim_attr.values = {}
            _condim_shapes = list(pad_shape_idx) + list(range(_cable_sr[0], _cable_sr[1]))
            for si in _condim_shapes:
                _condim_attr.values[si] = int(MUJOCO_CONTACT_CONDIM)
            for si in pad_shape_idx:
                if si < len(proto.shape_material_mu_rolling):
                    proto.shape_material_mu_rolling[si] = float(MUJOCO_PAD_ROLL_FRICTION)
            print(
                f"  [S6_GRASP] actuation wired (multiworld proto): drivers={grasp_driver_joints} "
                f"servo(ke={GRIPPER_SERVO_TARGET_KE},kd={GRIPPER_SERVO_TARGET_KD},"
                f"eff={GRIPPER_DRIVER_EFFORT_LIMIT_NM}) "
                f"connects={grasp_connects} mirrors={grasp_mirrors} condim6 on {len(_condim_shapes)} shapes "
                f"({len(pad_shape_idx)} pad + cable) rolling={MUJOCO_PAD_ROLL_FRICTION}"
            )
    else:
        left_info = add_kinematic_arm(
            proto,
            fk_model,
            fk_state,
            arm_body_offset=0,
            label_prefix="left",
        )
        right_info = add_kinematic_arm(
            proto,
            fk_model,
            fk_state,
            arm_body_offset=FRANKA_NUM_JOINTS,
            label_prefix="right",
        )
        left_body_start, left_shape_start, left_shape_end, left_fv = left_info
        right_body_start, right_shape_start, right_shape_end, right_fv = right_info
        all_finger_visual = set(left_fv + right_fv)

        # Contact filtering: non-pad bodies -> VISIBLE only, pad followers (GRIPPER_PAD_BODY_IDX) -> COLLIDE
        for arm_ss, arm_se, arm_bs in [
            (left_shape_start, left_shape_end, left_body_start),
            (right_shape_start, right_shape_end, right_body_start),
        ]:
            for si in range(arm_ss, arm_se):
                local = proto.shape_body[si] - arm_bs
                if local not in GRIPPER_PAD_BODY_IDX or si in all_finger_visual:
                    proto.shape_flags[si] = 1  # VISIBLE only
                elif local in GRIPPER_PAD_BODY_IDX:
                    proto.shape_flags[si] = 0x6  # COLLIDE_SHAPES | COLLIDE_PARTICLES

        # Cable (add_rod: rigid-capsule CABLE-joint chain / rigid-link REVOLUTE on SolverMuJoCo; NOT Cosserat)
        cable_shape_start_idx = proto.shape_count
        cable_bodies_proto, cable_joints_proto = add_cable_rod(
            proto,
            start_pos=cable_start_pos,
            direction=(0, 1, 0),
        )
        cable_shape_end_idx = proto.shape_count
        cable_bodies_per_world = len(cable_bodies_proto)
        cable_body_offset = cable_bodies_proto[0]

        # Cable-arm filter pairs (arm bodies 0-6 don't collide with cable)
        for cable_si in range(cable_shape_start_idx, cable_shape_end_idx):
            for arm_ss, arm_se, arm_bs in [
                (left_shape_start, left_shape_end, left_body_start),
                (right_shape_start, right_shape_end, right_body_start),
            ]:
                for arm_si in range(arm_ss, arm_se):
                    local = proto.shape_body[arm_si] - arm_bs
                    if local not in GRIPPER_PAD_BODY_IDX:
                        proto.add_shape_collision_filter_pair(cable_si, arm_si)

    bodies_per_world = proto.body_count

    # --- Scene: global entities + replicate ---
    scene = newton.ModelBuilder(gravity=GRAVITY)

    # Ground plane
    scene.add_ground_plane()

    # Table
    table_cfg = newton.ModelBuilder.ShapeConfig()
    if SOLVER_BACKEND == "mujoco":
        # D-S4a-3: ke/kd → solref=(2/kd, (kd/2)√(1/ke)); MuJoCo mixes BOTH geoms' solref per
        # contact, so the table is stiffened alongside the cable (≤~mm rest compression).
        table_cfg.ke = MUJOCO_CONTACT_KE
        table_cfg.kd = MUJOCO_CONTACT_KD
    else:
        table_cfg.ke = 500.0
        table_cfg.kd = 100.0
    table_cfg.mu = 1.0
    table_cfg.gap = 0.002
    table_cx, table_cy, table_cz = 0.3, -0.05, TABLE_HEIGHT - 0.005
    table_half = (0.35, 0.35, 0.005)
    if SOLVER_BACKEND == "mujoco" and grasp_actuation:
        # S6_GRASP table VOID (mirrors the PROVEN build_scene grasp_actuation slot, test:1055-1119, grasp_y
        # =None case; probe 9/9). The gripper's lower flank (f1ext) must reach UNDER the table-resting cable
        # to cage it; a SOLID table blocks f1ext at table_top → no hook → no hold. Split into 2 Y-boxes (the
        # slot at the WIDE grasps ±16mm) + 2 X-fill boxes (void ONLY under the gripper footprint); the cable
        # SPANS the void, supported on BOTH Y-sides (no droop). Default grasp_actuation=False keeps the single
        # solid box (AC/Grip byte-identical).
        y_floor, y_ceil = table_cy - table_half[1], table_cy + table_half[1]  # [-0.40, +0.30]
        slot_lo, slot_hi = WIDE_LEFT_Y - 0.016, WIDE_RIGHT_Y + 0.016  # [0.090, 0.210] under the L+R grasps
        cyl, hyl = (y_floor + slot_lo) / 2.0, (slot_lo - y_floor) / 2.0
        cyh, hyh = (slot_hi + y_ceil) / 2.0, (y_ceil - slot_hi) / 2.0
        x_floor, x_ceil = table_cx - table_half[0], table_cx + table_half[0]  # [-0.05, 0.65]
        slot_x_lo, slot_x_hi = table_cx - 0.066, table_cx + 0.066  # [0.234, 0.366] gripper footprint ±15mm
        cyv, hyv = (slot_lo + slot_hi) / 2.0, (slot_hi - slot_lo) / 2.0
        cxc, hxc = (x_floor + slot_x_lo) / 2.0, (slot_x_lo - x_floor) / 2.0  # -X void fill
        cxd, hxd = (slot_x_hi + x_ceil) / 2.0, (x_ceil - slot_x_hi) / 2.0  # +X void fill
        for _hx, _hy, _cx, _cy in [
            (table_half[0], hyl, table_cx, cyl),  # -Y solid table
            (table_half[0], hyh, table_cx, cyh),  # +Y solid table
            (hxc, hyv, cxc, cyv),  # -X void fill (inside the slot Y, X < footprint)
            (hxd, hyv, cxd, cyv),  # +X void fill (inside the slot Y, X > footprint)
        ]:
            scene.add_shape_box(
                body=-1,
                hx=_hx,
                hy=_hy,
                hz=table_half[2],
                xform=wp.transform((_cx, _cy, table_cz), wp.quat_identity()),
                cfg=table_cfg,
            )
        print(
            f"  [SCENE] Table → 4 boxes (S6_GRASP void): VOID Y[{slot_lo:.3f},{slot_hi:.3f}] "
            f"X[{slot_x_lo:.3f},{slot_x_hi:.3f}] (gripper f1ext reaches under the cable)"
        )
    else:
        scene.add_shape_box(
            body=-1,
            hx=table_half[0],
            hy=table_half[1],
            hz=table_half[2],
            xform=wp.transform((table_cx, table_cy, table_cz), wp.quat_identity()),
            cfg=table_cfg,
        )

    # Support clips (optional — ApproachCable only)
    if add_support_clips:
        clip_cfg = newton.ModelBuilder.ShapeConfig()
        clip_cfg.ke = 2500.0
        clip_cfg.kd = 100.0
        clip_cfg.mu = 1.0
        clip_cfg.gap = 0.001
        clip_parts = [
            (0, 0, 0.0025, 0.020, 0.015, 0.0025),
            (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
            (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),
            (-0.013, 0, 0.025, 0.002, 0.015, 0.005),
            (+0.013, 0, 0.025, 0.002, 0.015, 0.005),
        ]
        support_clip_ys = [-0.100, +0.050, +0.300, +0.450]  # cover full cable Y range
        for clip_y in support_clip_ys:
            for dx, dy, dz, hx, hy, hz in clip_parts:
                xf = wp.transform(
                    (GRASP_X + dx, clip_y + dy, TABLE_HEIGHT + dz),
                    wp.quat_identity(),
                )
                idx = scene.add_shape_box(
                    body=-1,
                    xform=xf,
                    hx=hx,
                    hy=hy,
                    hz=hz,
                    cfg=clip_cfg,
                )
                scene.shape_flags[idx] = 0x6

    # V-groove clip geometry (5 boxes: base + 2 lower walls + 2 lips), shared by C1 (add_target_clip) and
    # C2 (add_c2_clip). Defined once to avoid a 3rd literal copy (route-executor comp5 L1).
    _v_groove_clip_parts = [
        (0, 0, 0.0025, 0.020, 0.015, 0.0025),  # base plate
        (-0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # left lower wall
        (+0.009, 0, 0.0125, 0.0015, 0.015, 0.0075),  # right lower wall
        (-0.013, 0, 0.025, 0.002, 0.015, 0.005),  # left lip
        (+0.013, 0, 0.025, 0.002, 0.015, 0.005),  # right lip
    ]

    # Target clip at C1 (V-groove geometry for Grip/InsertIntoClip envs)
    if add_target_clip:
        clip_cfg = newton.ModelBuilder.ShapeConfig()
        # (d2) arm D -- MEASUREMENT ONLY, flag-gated, default OFF (byte-preserve).
        #
        # The env's C1 clip is hardcoded 16x SOFTER than the producer's C1, which is what the canonical golden
        # was recorded against: producer C1 uses MUJOCO_CONTACT_KE/KD = 40000/400 with gap 0.002
        # (test_newton_clip_routing.py:1179-1185), and so does this env's C2 (:1886-1889) -- only C1 does not.
        # The comment 18 lines below says so in as many words ("record-matched, NOT C1's soft 2500"): it was
        # noticed, written down, and left. The cable's rest shape is straight (springref = 0), so it pushes
        # outward against the groove wall -- and here the wall it pushes against is 16x softer than the one the
        # reference was made against. That is a far simpler mechanism for the 52.87mm lateral escape than the
        # "chaotic amplification" FORK-1 assumes, and arm D tests it for the cost of one run.
        #
        # ⚠ FORK-1's own refutation of the contact-param hypothesis rested on the SHARED CONSTANTS being
        # identical. They are. But this clip does not USE them -- it hardcodes 2500. "The constant is the same"
        # is not "the value in force is the same", which is the trap this whole arc keeps finding.
        #
        # ⛔ Making this permanent is a producer<->env parity change and belongs to Rs, not to a flag.
        _c1_match = os.environ.get("ROUTE_C1_STIFF_MATCH", "0") == "1"
        clip_cfg.ke = MUJOCO_CONTACT_KE if _c1_match else 2500.0
        clip_cfg.kd = MUJOCO_CONTACT_KD if _c1_match else 100.0
        clip_cfg.mu = 1.0
        clip_cfg.gap = 0.002 if _c1_match else 0.001
        if _c1_match:
            print(
                f"  [d2 arm D] C1 clip contact MATCHED to the producer: ke={clip_cfg.ke} kd={clip_cfg.kd} "
                f"gap={clip_cfg.gap} (default build is ke=2500 kd=100 gap=0.001 = 16x softer)"
            )
        for dx, dy, dz, hx, hy, hz in _v_groove_clip_parts:
            xf = wp.transform(
                (CLIP1_X + dx, CLIP1_Y + dy, TABLE_HEIGHT + dz + target_clip_float_z),
                wp.quat_identity(),
            )
            idx = scene.add_shape_box(
                body=-1,
                xform=xf,
                hx=hx,
                hy=hy,
                hz=hz,
                cfg=clip_cfg,
            )
            scene.shape_flags[idx] = 0x6  # COLLIDE | BROADPHASE

    # Second clip C2 (route-executor comp5): the real C2 V-groove for multi-world env-core route seating +
    # DoD6 C2-seating video. PORTS the proven single-world CLIP2 build (test_newton_clip_routing.py:1214-1247):
    # the same 5 V-groove parts + a spacer, collidable MUJOCO_CONTACT_KE/KD (record-matched, NOT C1's soft
    # 2500), floated by target_clip_float_z; c2_xy is param-sourced by the caller (rc.ROUTE_C2_XY -- NO
    # os.environ). Additive: add_c2_clip default False -> byte-identical for AC/Grip/IC/env-core.
    if add_c2_clip:
        c2x, c2y = float(c2_xy[0]), float(c2_xy[1])
        c2_cfg = newton.ModelBuilder.ShapeConfig()
        c2_cfg.ke = MUJOCO_CONTACT_KE
        c2_cfg.kd = MUJOCO_CONTACT_KD
        c2_cfg.mu = 1.0
        c2_cfg.gap = 0.002
        for dx, dy, dz, hx, hy, hz in _v_groove_clip_parts:
            xf = wp.transform((c2x + dx, c2y + dy, TABLE_HEIGHT + dz + target_clip_float_z), wp.quat_identity())
            idx = scene.add_shape_box(body=-1, xform=xf, hx=hx, hy=hy, hz=hz, cfg=c2_cfg)
            scene.shape_flags[idx] = 0x6  # COLLIDE | BROADPHASE
        # Spacer under C2 (record parity: recording SPACER=1) -- a 6th box filling the float gap. The C2-seat
        # EXACT predicate is spacer-EXCLUDED (5 groove walls only), so it is seat-measurement-independent.
        _c2_sp_cfg = newton.ModelBuilder.ShapeConfig()
        _c2_sp_cfg.ke = MUJOCO_CONTACT_KE
        _c2_sp_cfg.kd = MUJOCO_CONTACT_KD
        _c2_sp_cfg.mu = 1.0
        _c2_sp_cfg.gap = 0.002
        _c2_sp_xf = wp.transform((c2x, c2y, TABLE_HEIGHT + target_clip_float_z / 2.0), wp.quat_identity())
        _c2_sp_idx = scene.add_shape_box(
            body=-1, xform=_c2_sp_xf, hx=0.020, hy=0.015, hz=max(target_clip_float_z / 2.0, 1e-4), cfg=_c2_sp_cfg
        )
        scene.shape_flags[_c2_sp_idx] = 0x6  # COLLIDE | BROADPHASE

    # Replicate
    scene.replicate(proto, world_count=world_count)
    scene.color()
    model = scene.finalize(device=device, requires_grad=False)

    # World index arrays
    bws = model.body_world_start.numpy()
    jws = model.joint_world_start.numpy()  # joint-world-start (joint axis; per-world joint_q slicing)

    # D-S4a-4 joint-layout assert (mujoco): per-world joints = arm 28 + cable FREE+REVOLUTE —
    # guards the arm joint_q slice (broadcast_jointq_to_all_worlds writes [jws[w]:jws[w]+28]).
    if SOLVER_BACKEND == "mujoco":
        expected = 2 * JOINTS_PER_ARM + len(cable_joints_proto)
        for w in range(world_count):
            assert jws[w + 1] - jws[w] == expected, (
                f"mujoco joint layout drift (world {w}): {jws[w + 1] - jws[w]} != {expected}"
            )

    # Zero inv_mass for robot bodies (kinematic) -- VBD ONLY. The MuJoCo articulated arm keeps its
    # REAL masses: zeroing => infinite mass + inertia => degenerate joint-space M(q); the STEP-1 probe
    # validated the REAL-mass arm + per-step re-pose (track_err 0.030 rad), not a massless build (§28).
    if SOLVER_BACKEND != "mujoco":
        inv_mass = model.body_inv_mass.numpy()
        inv_inertia = model.body_inv_inertia.numpy()
        for w in range(world_count):
            start = bws[w]
            for bi in range(ROBOT_BODY_COUNT):
                inv_mass[start + bi] = 0.0
                inv_inertia[start + bi] = np.zeros(3, dtype=np.float32)
        model.body_inv_mass = wp.array(inv_mass, dtype=model.body_inv_mass.dtype, device=device)
        model.body_inv_inertia = wp.array(inv_inertia, dtype=model.body_inv_inertia.dtype, device=device)

    # Post-finalize: pad-follower BOX->collision / MESH->visual (no-op in S2: gripper bare; faithful pads built at S5)
    model_sflags = model.shape_flags.numpy()
    model_stypes = model.shape_type.numpy()
    model_sbodies = model.shape_body.numpy()
    for si in range(len(model_stypes)):
        bi = model_sbodies[si]
        if bi < 0:
            continue
        for w in range(world_count):
            ws, we = bws[w], bws[w + 1]
            if ws <= bi < we:
                local = bi - ws
                local_l = local - 0
                local_r = local - ROBOT_BODIES_PER_ARM
                if local_l in GRIPPER_PAD_BODY_IDX or local_r in GRIPPER_PAD_BODY_IDX:
                    if model_stypes[si] == 7:  # BOX = collision only
                        model_sflags[si] = 0x6
                    elif model_stypes[si] == 8:  # MESH = visual only
                        model_sflags[si] = 0x1
                break
    model.shape_flags = wp.array(model_sflags, dtype=model.shape_flags.dtype, device=device)

    # solver via the SOLVER_BACKEND factory (default "vbd" => byte-identical to the prior SolverVBD).
    # S4a: under mujoco the cable is present -> contacts enabled (D-S4a-3); vbd ignores the kwarg.
    solver = make_solver(model, enable_cable_contacts=(SOLVER_BACKEND == "mujoco"))
    # Both ceilings (D-S4a-3): rigid_contact_max NOT auto-raised (undersized raises ValueError,
    # solver_mujoco.py:3981) -> max(NJMAX, measured naconmax) = NJMAX. Probe-measured naconmax:
    # SETTLED-flat cable<->table = 80; the curled gravity-off config = 0 (S4b fix: the prior
    # comment misattributed the 80 to "curled"). MuJoCo's own nconmax is set in make_solver.
    model.rigid_contact_max = NJMAX

    # S6_GRASP (grasp_actuation=True): in-builder registration check (mirrors build_scene test:1485-1491,
    # ×world_count) then the post-make_solver poke. 6 eqs/world (4 CONNECT + 2 follower-mirror), replicated.
    # _wire pokes the negative PAD_SOLREF into mjw (ALL worlds) + stiffens the mj_model-template 4-bar.
    if SOLVER_BACKEND == "mujoco" and grasp_actuation:
        _neq = int(getattr(model, "equality_constraint_count", 0) or 0)
        # (d2): with perclip_pin the model also carries one DISABLED connect per cable body, per world. They are
        # inert (enabled=False) but they MUST all have registered -- a short count means the pin the run depends
        # on may not exist, and the activation would then silently find nothing. Fail loud here, not there.
        if perclip_pin:
            _want = (6 + cable_bodies_per_world) * world_count
            if _neq != _want:
                raise AssertionError(
                    f"PERCLIP_PIN: eqs did not all register/replicate: neq={_neq} != "
                    f"(6 + {cable_bodies_per_world}) * {world_count} = {_want}"
                )
            print(f"  [PERCLIP_PIN] neq={_neq} = (6 structural + {cable_bodies_per_world} pin) x {world_count} worlds")
        assert perclip_pin or _neq == 6 * world_count, (
            f"S6_GRASP: 4-bar+mirror eqs did not all register/replicate: neq={_neq} != 6*world_count={6 * world_count}"
        )
        _wire_s6_grasp_solref(solver)

    # Physics states
    state_0 = model.state()
    state_1 = model.state()
    control = model.control()
    contacts = model.contacts()

    # Cable body indices per world
    cable_bodies = []
    for w in range(world_count):
        start = bws[w] + cable_body_offset
        cable_bodies.append(list(range(start, start + cable_bodies_per_world)))

    return {
        "model": model,
        "solver": solver,
        "state_0": state_0,
        "state_1": state_1,
        "control": control,
        "contacts": contacts,
        "bws": bws,
        "jws": jws,
        "cable_bodies": cable_bodies,
        "cable_bodies_per_world": cable_bodies_per_world,
        "cable_body_offset": cable_body_offset,
        "bodies_per_world": bodies_per_world,
    }


# =============================================================================
# Physics Stepping
# =============================================================================


def broadcast_fk_to_all_worlds(fk_state, state_0, bws, world_count):
    """Copy FK body transforms to all worlds' robot bodies."""
    fk_bq = fk_state.body_q.numpy()[:ROBOT_BODY_COUNT]
    phys_bq = state_0.body_q.numpy()
    for w in range(world_count):
        start = bws[w]
        phys_bq[start : start + ROBOT_BODY_COUNT] = fk_bq
    state_0.body_q.assign(phys_bq)


def broadcast_jointq_to_all_worlds(fk_state, state_0, jws, world_count):
    """Copy FK joint coords to all worlds' robot joints (MuJoCo articulated kinematic re-pose).

    The joint-space analog of :func:`broadcast_fk_to_all_worlds`: writes ``fk_state.joint_q`` into
    each world's robot joint slice ``[jws[w] : jws[w] + 2*JOINTS_PER_ARM]`` (28) and zeros the
    matching ``joint_qd`` -- the per-step OVERWRITE re-pose the STEP-1 probe validated (every step,
    not a single set). Used under ``SOLVER_BACKEND == "mujoco"`` (MuJoCo poses bodies from joint_q).
    """
    n = 2 * JOINTS_PER_ARM
    fk_jq = fk_state.joint_q.numpy()[:n]
    phys_jq = state_0.joint_q.numpy()
    phys_jqd = state_0.joint_qd.numpy()
    for w in range(world_count):
        start = jws[w]
        phys_jq[start : start + n] = fk_jq
        phys_jqd[start : start + n] = 0.0
    state_0.joint_q.assign(phys_jq)
    state_0.joint_qd.assign(phys_jqd)


def physics_step(model, solver, state_0, state_1, control, contacts, substeps=None, sim_dt=None):
    """One physics frame for all worlds.

    Returns:
        (state_0, state_1) — swapped after stepping.
    """
    n_sub = substeps if substeps is not None else SIM_SUBSTEPS
    dt = sim_dt if sim_dt is not None else SIM_DT
    for _ in range(n_sub):
        state_0.clear_forces()
        model.collide(state_0, contacts)
        solver.step(state_0, state_1, control, contacts, dt)
        state_0, state_1 = state_1, state_0
    return state_0, state_1


def ik_move_all_worlds(
    fk_model, fk_state, scene, target_left, target_right, world_count, device, label="MOVE", converge_mm=5.0
):
    """Move both arms to target positions via IK — all worlds get same solution.

    Returns:
        True if converged, False if IK failed (NaN).
    """
    jq_target = solve_ik_single(fk_model, fk_state, target_left, target_right, device)
    if np.any(np.isnan(jq_target)):
        print(f"  [{label}] IK FAILED (NaN)")
        return False

    jq_start = fk_state.joint_q.numpy().copy()
    n_coords = fk_model.joint_coord_count

    state_0, state_1 = scene["state_0"], scene["state_1"]
    err_l, err_r = 0.0, 0.0

    for step in range(MAX_MOVE_STEPS):
        t = min((step + 1) / MAX_MOVE_STEPS, 1.0)
        jq_interp = jq_start.copy()
        for d in range(n_coords):
            if d not in FINGER_JOINT_INDICES:
                jq_interp[d] = jq_start[d] + (jq_target[d] - jq_start[d]) * t

        fk_state.joint_q.assign(jq_interp)
        newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
        if SOLVER_BACKEND == "mujoco":
            broadcast_jointq_to_all_worlds(fk_state, state_0, scene["jws"], world_count)
        else:
            broadcast_fk_to_all_worlds(fk_state, state_0, scene["bws"], world_count)
        state_0, state_1 = physics_step(
            scene["model"],
            scene["solver"],
            state_0,
            state_1,
            scene["control"],
            scene["contacts"],
        )
        scene["state_0"], scene["state_1"] = state_0, state_1

        if (step + 1) % 10 == 0:
            wp.synchronize()
            bq = state_0.body_q.numpy()
            w0_start = scene["bws"][0]
            left_ee_pos = bq[w0_start + EE_BODY_OFFSET][:3]
            right_ee_pos = bq[w0_start + FRANKA_NUM_JOINTS + EE_BODY_OFFSET][:3]
            err_l = np.linalg.norm(left_ee_pos - np.array(target_left)) * 1000
            err_r = np.linalg.norm(right_ee_pos - np.array(target_right)) * 1000
            if max(err_l, err_r) < converge_mm:
                break

    print(f"  [{label}] Done: steps={step + 1}, err_L={err_l:.1f}mm, err_R={err_r:.1f}mm")
    return True


def hold_position(fk_state, scene, world_count, n_frames):
    """Hold current position for n_frames physics frames."""
    state_0, state_1 = scene["state_0"], scene["state_1"]
    for _ in range(n_frames):
        if SOLVER_BACKEND == "mujoco":
            broadcast_jointq_to_all_worlds(fk_state, state_0, scene["jws"], world_count)
        else:
            broadcast_fk_to_all_worlds(fk_state, state_0, scene["bws"], world_count)
        state_0, state_1 = physics_step(
            scene["model"],
            scene["solver"],
            state_0,
            state_1,
            scene["control"],
            scene["contacts"],
        )
    scene["state_0"], scene["state_1"] = state_0, state_1


# =============================================================================
# Precondition Cache I/O
# =============================================================================


def save_precondition_cache(path, scene, fk_state, world_count, extra_keys=None):
    """Save precondition state to npz file.

    Args:
        path: Output file path (.npz).
        scene: Scene dict from build_multiworld_scene.
        fk_state: FK state.
        world_count: Number of worlds.
        extra_keys: Optional dict of additional numpy arrays to include.
    """
    wp.synchronize()
    state_0 = scene["state_0"]

    data = {
        "body_q": state_0.body_q.numpy().copy(),
        "body_qd": state_0.body_qd.numpy().copy(),
        "fk_jq": fk_state.joint_q.numpy().copy(),
        "inv_mass": scene["model"].body_inv_mass.numpy().copy(),
        "inv_inertia": scene["model"].body_inv_inertia.numpy().copy(),
        "world_count": np.array([world_count], dtype=np.int32),
        "body_count": np.array([scene["model"].body_count], dtype=np.int32),
    }
    if extra_keys:
        data.update(extra_keys)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, **data)
    size_kb = os.path.getsize(path) / 1024
    print(f"[base] Cache saved: {path} ({size_kb:.1f} KB)")
    return path


def load_precondition_cache(path):
    """Load precondition cache from npz file.

    Returns:
        dict of numpy arrays (keys depend on what was saved).
    """
    data = np.load(path)
    return dict(data)
