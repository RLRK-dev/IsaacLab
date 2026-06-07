# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Option E — S1: standalone UR5e + Robotiq-2f85 DOF / index derivation (0-GPU).

Assembles the MuJoCo-Menagerie UR5e arm + Robotiq 2f85 gripper into one Newton
model by attaching the gripper's root body at the UR5e ``wrist_3`` ``attachment_site``
via ``ModelBuilder.add_mjcf(parent_body=..., floating=False, xform=...)`` (a fixed
base joint to the parent body -- the documented Newton hierarchical-composition path;
avoids MJCF ``<include>`` class-name collisions by parsing each file separately).

It then finalises on CPU and DERIVES (does not assume) the substrate-swap indices:
ARM_DOF, GRIPPER_DOF, ROBOT_NUM_JOINTS, EE_BODY_IDX (wrist_3), GRIPPER_JOINT_IDX
(actuated driver joint), ROBOT_BODIES_PER_ARM -- cross-checked vs P3 (6 / 8 / 14).

ADDITIVE / non-breaking: imports only newton/warp/numpy; does NOT touch the live
build_fk_model or task_config. CPU-only (the model finalizes on device="cpu");
run with the canonical Newton venv:

    ~/env_isaaclab6/bin/python thread_isaac_lab/scripts/derive_ur5e_robotiq_dof.py
"""

import contextlib
import math
import os

import newton
import numpy as np
import warp as wp

_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSET = os.path.join(_HERE, "..", "assets", "ur5e_robotiq")
UR5E_XML = os.path.join(_ASSET, "ur5e", "ur5e.xml")
ROBOTIQ_XML = os.path.join(_ASSET, "robotiq_2f85", "2f85.xml")

# UR5e wrist_3 attachment_site, ur5e.xml:114 -- local frame in wrist_3_link.
ATTACH_POS = (0.0, 0.1, 0.0)
ATTACH_QUAT_MJCF_WXYZ = (-1.0, 1.0, 0.0, 0.0)  # MuJoCo (w, x, y, z)

# P3 cross-check references (P3_NUMERIC_DESIGN_DRAFT.md / DECIDE.md).
P3_ARM_DOF = 6
P3_GRIPPER_DOF = 8
P3_ROBOT_NUM_JOINTS = 14
P3_ATTACH_TO_PINCH = 0.156  # base_mount 0.007 + base 0.0038 + pinch 0.145


def mjcf_wxyz_to_wp(w, x, y, z):
    """MuJoCo quat (w, x, y, z) -> normalized warp wp.quat (x, y, z, w)."""
    n = math.sqrt(w * w + x * x + y * y + z * z)
    return wp.quat(x / n, y / n, z / n, w / n)


def _attr(obj, *names):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def _as_list(x):
    if x is None:
        return None
    try:
        return list(x.numpy()) if hasattr(x, "numpy") else list(x)
    except Exception:
        return list(x)


def build(collapse_fixed_joints: bool):
    """Assemble UR5e + Robotiq into one builder. Returns (builder, wrist3_body_idx)."""
    b = newton.ModelBuilder()
    # 1. UR5e arm (fixed base to world).
    b.add_mjcf(
        UR5E_XML,
        floating=False,
        collapse_fixed_joints=collapse_fixed_joints,
        enable_self_collisions=False,
        parse_meshes=False,  # kinematics only -- no mesh files needed for DOF derivation
    )
    body_key = _as_list(_attr(b, "body_label", "body_key", "body_name")) or []
    wrist3 = [i for i, k in enumerate(body_key) if "wrist_3" in str(k)]
    if not wrist3:
        raise RuntimeError(f"wrist_3 body not found after UR5e add_mjcf; body_key={body_key}")
    wrist3_idx = wrist3[0]
    n_arm_bodies = len(body_key)
    n_arm_joints = len(_as_list(_attr(b, "joint_label", "joint_key", "joint_name")) or [])
    print(f"[UR5e] bodies={n_arm_bodies} joints={n_arm_joints} wrist_3_idx={wrist3_idx}")
    print(f"[UR5e] body_key={body_key}")
    # 2. Robotiq gripper -- fixed to wrist_3 at the attachment_site frame.
    xform = wp.transform(wp.vec3(*ATTACH_POS), mjcf_wxyz_to_wp(*ATTACH_QUAT_MJCF_WXYZ))
    b.add_mjcf(
        ROBOTIQ_XML,
        parent_body=wrist3_idx,
        floating=False,  # fixed base joint to parent_body
        xform=xform,
        collapse_fixed_joints=collapse_fixed_joints,
        enable_self_collisions=False,
        parse_meshes=False,
    )
    return b, wrist3_idx


def report(collapse_fixed_joints: bool):
    print("=" * 78)
    print(f"BUILD with collapse_fixed_joints={collapse_fixed_joints}")
    print("=" * 78)
    b, wrist3_idx = build(collapse_fixed_joints)

    body_key = _as_list(_attr(b, "body_label", "body_key", "body_name")) or []
    joint_key = _as_list(_attr(b, "joint_label", "joint_key", "joint_name")) or []
    joint_type = _as_list(_attr(b, "joint_type")) or []
    print(f"[FULL] bodies={len(body_key)} joints={len(joint_key)}")
    print(f"[FULL] body_key={body_key}")
    print(f"[FULL] joint_key={joint_key}")
    print(f"[FULL] joint_type={joint_type}")

    # Joint-type DOF accounting (revolute/prismatic = 1 DOF; fixed = 0).
    jt_names = {}
    JT = newton.JointType if hasattr(newton, "JointType") else None
    if JT is not None:
        for nm in dir(JT):
            if not nm.startswith("_"):
                with contextlib.suppress(Exception):
                    jt_names[int(getattr(JT, nm))] = nm
    print(f"[JointType enum] {jt_names}")

    # Derived counts.
    gripper_joints = [j for j in joint_key if any(s in str(j) for s in ("driver", "coupler", "spring", "follower"))]
    arm_joints = [j for j in joint_key if j not in gripper_joints and "fixed" not in str(j).lower()]
    print(f"[DERIVED] arm_joint_keys={arm_joints}")
    print(f"[DERIVED] gripper_joint_keys={gripper_joints}")

    driver_idx = [
        i for i, j in enumerate(joint_key) if str(j).split("/")[-1] in ("right_driver_joint", "left_driver_joint")
    ]
    arm_dof = len(arm_joints)
    print(f"[DERIVED] GRIPPER_JOINT_IDX model-idx={driver_idx} local={[i - arm_dof for i in driver_idx]}")

    # FK at zero config -> attachment_site->pinch cross-check via base body world pos.
    try:
        model = b.finalize(device="cpu")
        wp.synchronize_device("cpu")
        with contextlib.suppress(Exception):
            newton.eval_fk(model, model.joint_q, model.joint_qd, model.state())
        body_q = _as_list(model.body_q)
        mb_body_key = _as_list(_attr(model, "body_label", "body_key", "body_name")) or body_key
        # locate gripper 'base' body and wrist_3 for the offset check
        base_i = next((i for i, k in enumerate(mb_body_key) if "robotiq" in str(k) and str(k).endswith("/base")), None)
        w3_i = next((i for i, k in enumerate(mb_body_key) if "wrist_3" in str(k)), None)
        print(f"[FK] body_count={getattr(model, 'body_count', '?')} base_idx={base_i} wrist3_idx={w3_i}")
        if body_q and base_i is not None and w3_i is not None:

            def _pos(t):
                a = np.array(t, dtype=float).ravel()
                return a[:3]

            d = np.linalg.norm(_pos(body_q[base_i]) - _pos(body_q[w3_i]))
            print(f"[FK] |wrist_3 -> base| = {d:.4f} m  (P3 attach->pinch ~{P3_ATTACH_TO_PINCH})")
    except Exception as e:
        print(f"[FK] finalize/eval skipped: {e!r}")

    print(f"[CROSS-CHECK vs P3] ARM_DOF: model_arm_joints={len(arm_joints)} vs P3={P3_ARM_DOF}")
    print(f"[CROSS-CHECK vs P3] GRIPPER_DOF: model_gripper_joints={len(gripper_joints)} vs P3={P3_GRIPPER_DOF}")
    print(f"[CHECK] ROBOT_NUM_JOINTS={len(arm_joints) + len(gripper_joints)} vs P3={P3_ROBOT_NUM_JOINTS}")
    print(f"[CHECK] EE_BODY_IDX (wrist_3) = {wrist3_idx} (P3 draft 6; debate+DERIVED 5)")
    return b


if __name__ == "__main__":
    for collapse in (True, False):
        try:
            report(collapse)
        except Exception as e:
            import traceback

            print(f"BUILD collapse={collapse} FAILED: {e!r}")
            traceback.print_exc()
        print()
    print("DERIVE_DONE")
