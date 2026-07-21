# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Arm-control design-time measurement harness (p0 / IMPL-BUILDER).

Implements ``ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_ARMCONTROLDESIGN_20260721.md``
**v1.3** (p11 ARM-CONTROL-DESIGN, bank ``c8c326e00b``).

What this is
------------
A *design-time measurement instrument*. It reports facts about the model that the
env actually runs. It is **not** training, **not** a production launch, and it
makes **no design decision**.

Structural rule inherited from spec section 0 (the v0.4 root cause)
------------------------------------------------------------------
**The harness must not assemble a model.** It receives the physics ``Model`` that a
production-path env instance handed to ``SolverMuJoCo`` and measures *that*.

* This module never calls ``add_ur5e_robotiq`` / ``build_multiworld_scene``.
* ``env._fk_model`` (the IK-only robot model) is explicitly excluded from
  measurement, and is additionally used as the AC-9 negative control.

Identity is taken from the reference, not from content (spec v1.3 section 1.1)
------------------------------------------------------------------------------
The primary legs are ``is`` comparisons, because a fingerprint can never beat a
reference: matching contents do not prove identical objects, which is exactly how
v0.4 analysed the wrong model while its content check agreed.

* **I-1** measured ``Model`` **is** ``scene["model"]`` (``newton_route_env.py:725``)
* **I-2** ``scene["solver"].model`` **is** the measured ``Model`` (``SolverBase.__init__``
  sets ``self.model = model``) -- the object the solver actually integrates
* **I-3** measured ``Model`` **is not** ``env._fk_model`` (``newton_route_env.py:690``)

Content witnesses are a backstop only, and their roles were settled by measurement
rather than assumption:

* ``cable`` -- the ONLY leg that discriminates. Grounded in ``scene["cable_bodies"]``
  (``newton_route_env.py:733``); the FK model fails index resolution.
* ``a1_visible`` -- CONTEXT ONLY. Measured pass=true on both the 68-body as-built model
  and the 28-body FK model, so it identifies nothing. Recorded, never required.
* ``world_count`` -- configuration cross-check, not a discriminator.
* ``clip`` -- REMOVED. The scene key set is closed and has no clip key
  (``newton_route_env.py:725-734``); clip bodies carry the auto-label ``body_N``, so
  substring matching would return 0 and read as "no clip" -- a false negative.

Note that ``build_fk_and_init(left_finger_pos, right_finger_pos, ...)`` takes finger
positions, so the FK model carries gripper joints too, and ``newton_route_env.py:712``
passes ``self._fk_model`` *into* ``build_multiworld_scene``. DOF counts and "gripper
joints exist" are therefore structurally incapable of discriminating.

Fidelity caveat (spec section 1.2) -- do not describe this as a faithful 2F-85
-------------------------------------------------------------------------------
The scene builds each arm with ``robotiq_xml=ROBOTIQ_STRIPPED_XML``
(``2f85_koshape.xml``, the KO-shape claw with ``<tendon>`` removed) and
``skip_equality_constraints=True`` (``newton_skill_env_base.py:1561-1572``). Every
model description this harness emits is therefore qualified as
"KO-shape stripped asset, gripper built with equality disabled".

Boundaries (spec section 5)
---------------------------
* p0 (this file): implement + measure. Reports "works / does not work" as fact only.
* pZ: verifies H-0 model-identity and the AC-9 negative control against a real build.
* p4: landing.
* Adoption of any mechanism measured here (gravity compensation, ``joint_f``, 4-bar)
  touches the control method and is **Rs's decision**, not this harness's.

Usage
-----
``--stage h0`` runs only model acquisition + identity + witnesses + provenance +
the AC-9 negative control. It is cheap and self-contained so pZ can verify the
fail-closed foundation without paying for the sweeps.

.. code-block:: bash

    /home/rlrk/env_isaaclab7/bin/python arm_control_measurement_harness.py \
        --stage h0 --out h0_report.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# --------------------------------------------------------------------------------------
# Spec pin. Kept as data so the output can state which document it was built against.
# --------------------------------------------------------------------------------------
SPEC_PATH = (
    "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/"
    "ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_ARMCONTROLDESIGN_20260721.md"
)
SPEC_VERSION = "v1.3"
SPEC_BANK_SHA = "c8c326e00b"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --------------------------------------------------------------------------------------
# Import bootstrap -- reuse of the proven sibling-probe pattern
# (comp3_perarm_cell_grasplift.py:59-74, same node directory).
#
# The env module is imported as a TOP-LEVEL module with ``thread_isaac_lab/envs`` on
# sys.path, NOT as ``thread_isaac_lab.envs.newton_route_env``. Going through the package
# ``__init__`` pulls in ``assets_cfg`` -> ``isaaclab_physx``, which does not exist in the
# env7 (mujoco/Newton) venv -- that is the PhysX/Newton split, not a packaging accident.
# This is the established local convention, not a workaround invented here.
# --------------------------------------------------------------------------------------
_TIL = os.path.join(REPO_ROOT, "thread_isaac_lab")
for _p in (_TIL, os.path.join(_TIL, "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# --------------------------------------------------------------------------------------
# Recording primitives
#
# Everything this harness learns is recorded as an explicit outcome. "Could not
# determine" is a first-class result: spec H-6 requires that a mechanism with no
# reachable path be reported as absent rather than silently skipped.
# --------------------------------------------------------------------------------------
PRESENT = "PRESENT"
ABSENT = "ABSENT"
UNAVAILABLE = "UNAVAILABLE"  # attribute/route does not exist on this build
ERROR = "ERROR"  # probing raised


def probe(fn, *, note: str = "") -> dict[str, Any]:
    """Evaluate ``fn`` and record the outcome instead of propagating failure.

    Args:
        fn: Zero-argument callable producing a JSON-encodable value.
        note: Free-text provenance carried into the record.

    Returns:
        A record with ``status`` in {PRESENT, UNAVAILABLE, ERROR} and either
        ``value`` or ``error``.
    """
    try:
        value = fn()
    except AttributeError as exc:
        return {"status": UNAVAILABLE, "error": f"{type(exc).__name__}: {exc}", "note": note}
    except Exception as exc:  # noqa: BLE001 - probing must never abort the report
        return {"status": ERROR, "error": f"{type(exc).__name__}: {exc}", "note": note}
    if value is None:
        return {"status": UNAVAILABLE, "note": note}
    return {"status": PRESENT, "value": _jsonable(value), "note": note}


def _jsonable(value: Any) -> Any:
    """Coerce numpy / warp values into JSON-encodable Python objects."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if hasattr(value, "numpy"):  # warp array
        return _jsonable(value.numpy())
    return value


def _to_numpy(arr: Any) -> np.ndarray:
    """Return ``arr`` as a numpy array, unwrapping warp arrays."""
    if arr is None:
        raise AttributeError("array is None")
    if isinstance(arr, np.ndarray):
        return arr
    if hasattr(arr, "numpy"):
        return arr.numpy()
    return np.asarray(arr)


# --------------------------------------------------------------------------------------
# Section 1.3 / AC-10 -- provenance
#
# pZ reproduces at the same point, so the exact tree matters: this repo is checked out
# as several worktrees and newton_route_env.py:690 is tree-dependent.
# --------------------------------------------------------------------------------------
def _git(*args: str) -> str | None:
    """Run a read-only git command in the repo, returning stripped stdout or None."""
    try:
        out = subprocess.run(
            ["git", "-C", REPO_ROOT, *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def collect_provenance() -> dict[str, Any]:
    """Collect build tree / branch / commit / venv / solver-stack versions (AC-10)."""

    def _ver(mod_name: str) -> dict[str, Any]:
        try:
            mod = __import__(mod_name)
        except Exception as exc:  # noqa: BLE001
            return {"status": UNAVAILABLE, "error": f"{type(exc).__name__}: {exc}"}
        return {
            "status": PRESENT,
            "version": getattr(mod, "__version__", "<no __version__>"),
            "file": getattr(mod, "__file__", None),
        }

    dirty = _git("status", "--porcelain")
    return {
        "spec": {"path": SPEC_PATH, "version": SPEC_VERSION, "bank_sha": SPEC_BANK_SHA},
        "tree": REPO_ROOT,
        "git_common_dir": _git("rev-parse", "--git-common-dir"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": _git("rev-parse", "HEAD"),
        # A dirty tree means the measured code is NOT the commit. pZ must be able to see
        # that, because a hash pin over a dirty shared tree does not reproduce on a clean
        # checkout.
        "worktree_dirty": bool(dirty),
        "worktree_dirty_count": len(dirty.splitlines()) if dirty else 0,
        "python": sys.executable,
        "venv": os.environ.get("VIRTUAL_ENV"),
        "versions": {name: _ver(name) for name in ("newton", "mujoco", "warp")},
    }


# --------------------------------------------------------------------------------------
# H-0 -- model acquisition and identity (spec section 1)
# --------------------------------------------------------------------------------------
@dataclass
class ModelHandles:
    """The objects H-0 reasons about, kept distinct so they cannot be conflated."""

    env: Any
    as_built: Any  # env._model -- the Model handed to SolverMuJoCo
    solver: Any
    fk_model: Any | None  # env._fk_model -- EXCLUDED from measurement; AC-9 control
    # Scene-declared cable handles (newton_route_env.py:733-734). The cable witness is
    # grounded in these rather than in body-label substrings, which do not exist.
    cable_bodies: Any = None
    cable_bodies_per_world: int | None = None
    notes: list[str] = field(default_factory=list)


def acquire_models(env: Any) -> ModelHandles:
    """Take the as-built ``Model`` off a constructed env instance.

    The harness does not build anything here; it only reads attributes that the
    production path already populated (``newton_route_env.py:725``
    ``self._model = scene["model"]``).

    Args:
        env: A fully constructed production-path env instance.

    Returns:
        Handles to the as-built model, the solver, and the excluded FK model.
    """
    notes: list[str] = []
    as_built = getattr(env, "_model", None)
    if as_built is None:
        raise RuntimeError("env has no _model -- cannot measure the as-built model (fail-closed)")
    solver = getattr(env, "_solver", None)
    if solver is None:
        raise RuntimeError("env has no _solver -- cannot establish the SolverMuJoCo path (fail-closed)")
    fk_model = getattr(env, "_fk_model", None)
    if fk_model is None:
        notes.append("env._fk_model absent; AC-9 negative control cannot use it on this build")
    cable_bodies = getattr(env, "_cable_bodies", None)
    per_world = getattr(env, "_cable_bodies_per_world", None)
    if cable_bodies is None or per_world is None:
        notes.append("env exposes no _cable_bodies/_cable_bodies_per_world; the cable witness cannot be grounded")
    return ModelHandles(
        env=env,
        as_built=as_built,
        solver=solver,
        fk_model=fk_model,
        cable_bodies=cable_bodies,
        cable_bodies_per_world=per_world,
        notes=notes,
    )


def identity_record(h: ModelHandles) -> dict[str, Any]:
    """Record the V-1 identity chain: as-built Model -> SolverMuJoCo -> derived mj_model.

    Two distinct objects matter and must not be conflated:

    * ``env._model`` -- the Newton ``Model`` handed to ``SolverMuJoCo(model, ...)``
      (``newton_skill_env_base.py:1332`` / ``:1342``).
    * ``solver.mj_model`` -- the MuJoCo model *derived* from it, where the dynamics
      quantities (``qfrc_bias``, ``qM``) actually live.

    Measuring dynamics on the derived model is measuring the running model, but the
    derivation link must be stated rather than assumed.
    """
    solver = h.solver
    measured = h.as_built  # the object every downstream measurement reads
    env_model = getattr(h.env, "_model", None)
    solver_model = getattr(solver, "model", None)

    # I-1..I-3 are ``is`` comparisons. A fingerprint (matching contents) can never beat a
    # reference: identical contents do not prove identical objects, which is precisely how
    # v0.4 analysed the wrong model while its content check agreed.
    # R1 (pZ, 62ec7583d0): I-1 was tautological. acquire_models takes `measured` FROM
    # env._model, so `measured is env_model` could never be false, yet it was counted in
    # identity_all_pass -- three legs that were really two. It is retained below as a
    # provenance record and EXCLUDED from the verdict.
    i1_tautological = measured is env_model
    i2 = (solver_model is measured) if solver_model is not None else None
    i3 = (measured is not h.fk_model) if h.fk_model is not None else None

    return {
        "I-1_EXCLUDED_tautological": i1_tautological,
        "I-1_why_excluded": (
            "measured is taken from env._model, so this comparison cannot fail. It does not "
            "discriminate and is not counted (pZ finding R1 on 62ec7583d0)."
        ),
        "I-2_solver_model_is_measured": i2,
        "I-2_grounding": "SolverBase.__init__ sets self.model = model (newton/_src/solvers/solver.py)",
        "I-3_measured_is_not_fk_model": i3,
        "I-3_grounding": "newton_route_env.py:690 -- self._fk_model = build_fk_and_init(...)",
        # Only the two legs that can actually fail.
        "identity_all_pass": bool(i2 and i3),
        "identity_legs_counted": ["I-2", "I-3"],
        "object_ids": {
            "measured": id(measured),
            "env_model": id(env_model) if env_model is not None else None,
            "solver_model": id(solver_model) if solver_model is not None else None,
            "fk_model": id(h.fk_model) if h.fk_model is not None else None,
        },
        "measured_model_type": type(measured).__name__,
        "solver_type": type(solver).__name__,
        "fk_model_excluded_from_measurement": True,
        # Dynamics quantities live on the MuJoCo model DERIVED from the measured Model;
        # the derivation link is recorded rather than assumed.
        "derived_mj_model": probe(lambda: type(solver.mj_model).__name__),
        "derived_mj_model_id": probe(lambda: id(solver.mj_model)),
        "notes": h.notes,
    }


def inventory(model: Any, solver: Any | None = None) -> dict[str, Any]:
    """Record the H-0 inventory of a model (recorded, not judged).

    Args:
        model: A Newton ``Model``.
        solver: Optional solver, used to reach the derived MuJoCo model for the
            actuator/effort fields that only exist there.
    """
    inv: dict[str, Any] = {
        "body_count": probe(lambda: int(model.body_count)),
        "joint_count": probe(lambda: int(model.joint_count)),
        "world_count": probe(lambda: int(model.world_count)),
        "shape_count": probe(lambda: int(model.shape_count)),
        "body_mass": probe(lambda: _to_numpy(model.body_mass)),
        "joint_names": probe(lambda: [str(x) for x in model.joint_key]),
        "body_labels": probe(lambda: [str(x) for x in model.body_label]),
        "shape_labels": probe(lambda: [str(x) for x in model.shape_label]),
        "joint_effort_limit": probe(lambda: _to_numpy(model.joint_effort_limit)),
        "joint_q_start": probe(lambda: _to_numpy(model.joint_q_start)),
        "joint_qd_start": probe(lambda: _to_numpy(model.joint_qd_start)),
    }
    if solver is not None:
        inv["mj"] = {
            "nu": probe(lambda: int(solver.mj_model.nu)),
            "nq": probe(lambda: int(solver.mj_model.nq)),
            "nv": probe(lambda: int(solver.mj_model.nv)),
            "nbody": probe(lambda: int(solver.mj_model.nbody)),
            "neq": probe(lambda: int(solver.mj_model.neq)),
            "eq_type": probe(lambda: _to_numpy(solver.mj_model.eq_type)),
            # H-6a inputs. DDR#26: the imported ur5e.xml <actuator> block carries the
            # only real forcerange, so the actuator inventory is what makes the hidden
            # tug-of-war visible in the output.
            "actuator_forcerange": probe(lambda: _to_numpy(solver.mj_model.actuator_forcerange)),
            "actuator_trnid": probe(lambda: _to_numpy(solver.mj_model.actuator_trnid)),
            "jnt_actfrcrange": probe(lambda: _to_numpy(solver.mj_model.jnt_actfrcrange)),
            "actuator_ctrlrange": probe(lambda: _to_numpy(solver.mj_model.actuator_ctrlrange)),
        }
    return inv


# --------------------------------------------------------------------------------------
# Section 1.1 -- witnesses. Scene-specific content ONLY.
#
# Forbidden as witnesses (they cannot discriminate, spec section 1.1):
#   * DOF / joint / body counts matching
#   * "gripper joints exist"
# --------------------------------------------------------------------------------------
FORBIDDEN_WITNESS_NOTE = (
    "DOF count and 'gripper joints exist' are deliberately NOT used: the FK model "
    "carries gripper joints too (build_fk_and_init takes finger positions) and is "
    "passed into build_multiworld_scene, so those predicates cannot discriminate."
)


def witness_cable(model: Any, cable_bodies: Any, per_world: int | None) -> dict[str, Any]:
    """Cable witness: the REVOLUTE chain issued AFTER both arms (``:1587``).

    Grounded in the scene's own declaration, not in a label guess. The cable segments
    are auto-labelled ``body_N`` (measured: 40 of 68 bodies carry no descriptive label),
    so substring matching on ``body_label`` finds nothing and would silently report
    "no cable" for a scene that has one.

    The discriminating test is whether the scene-declared cable body indices actually
    resolve inside the measured model's body range. On the as-built model they do; on a
    robot-only FK model the indices fall outside it. This is structural content, not a
    count comparison.

    Args:
        model: The model being measured.
        cable_bodies: Per-world cable body index arrays from ``scene["cable_bodies"]``.
        per_world: ``scene["cable_bodies_per_world"]``.
    """

    def _check() -> dict[str, Any]:
        if cable_bodies is None or per_world is None:
            raise AttributeError("scene cable descriptors absent (env exposes no _cable_bodies)")
        idx = np.asarray(_to_numpy(cable_bodies)).ravel()
        # R2 (pZ, 62ec7583d0): the previous test was idx.max() < body_count -- an inequality
        # on a count, which any object exposing a large enough body_count satisfies. Read the
        # LABELS AT THE DECLARED INDICES instead. This is verification at known indices, not a
        # label SEARCH, so it does not inherit the clip false-negative problem.
        labels = [str(x) for x in _to_numpy(model.body_label)]
        n_bodies = int(model.body_count)
        in_range = bool(idx.size > 0 and int(idx.min()) >= 0 and int(idx.max()) < n_bodies)
        robot_prefixes = ("ur5e/", "robotiq_2f85/")
        at_idx, robot_labelled = [], 0
        if in_range and len(labels) >= n_bodies:
            for i in idx.tolist():
                lbl = labels[int(i)]
                at_idx.append(lbl)
                if lbl.startswith(robot_prefixes):
                    robot_labelled += 1
        # Measured on the as-built model: 68 bodies = 40 auto-labelled + 28 robot-prefixed,
        # with no third category. So cable indices must point at NON-robot-labelled bodies.
        non_robot_ok = bool(at_idx and robot_labelled == 0)
        return {
            "cable_bodies_per_world": int(per_world),
            "cable_index_count": int(idx.size),
            "indices_resolve_in_measured_model": in_range,
            "labels_readable_at_indices": bool(at_idx),
            "robot_prefixed_at_cable_indices": robot_labelled,
            "all_cable_indices_are_non_robot_bodies": non_robot_ok,
            "sample_labels_at_cable_indices": at_idx[:4],
            "measured_model_body_count": n_bodies,
        }

    rec = probe(_check, note="scene['cable_bodies'] (newton_route_env.py:733-734); add_revolute_cable :1587")
    val = rec.get("value") or {}
    rec["predicate"] = (
        "scene-declared cable bodies exist AND their indices resolve in the measured model "
        "AND the bodies AT those indices carry non-robot labels (read, not counted)"
    )
    rec["pass"] = bool(
        rec.get("status") == PRESENT
        and val.get("cable_bodies_per_world", 0) > 0
        and val.get("indices_resolve_in_measured_model") is True
        and val.get("all_cable_indices_are_non_robot_bodies") is True
    )
    return rec


def witness_a1_visible(model: Any) -> dict[str, Any]:
    """A-1 VISIBLE-pass witness (``:1574-1583``).

    The scene clears COLLIDE on non-pad arm shapes while keeping COLLIDE on the
    gripper pad geoms. The signature is therefore *mixed*: pad shapes collide,
    non-pad arm shapes do not. A robot-only FK model never went through this pass.
    """

    def _split() -> dict[str, Any]:
        import newton

        labels = [str(x) for x in _to_numpy(model.shape_label)]
        flags = _to_numpy(model.shape_flags)
        # Newton names this COLLIDE_SHAPES; there is no ShapeFlags.COLLIDE.
        collide_bit = int(newton.ShapeFlags.COLLIDE_SHAPES)
        pad_collide, nonpad_collide, nonpad_total, pad_total = 0, 0, 0, 0
        for idx, lbl in enumerate(labels):
            if idx >= len(flags):
                break
            is_pad = "pad" in lbl.lower()
            collides = bool(int(flags[idx]) & collide_bit)
            if is_pad:
                pad_total += 1
                pad_collide += int(collides)
            else:
                nonpad_total += 1
                nonpad_collide += int(collides)
        return {
            "pad_shapes": pad_total,
            "pad_with_collide": pad_collide,
            "nonpad_shapes": nonpad_total,
            "nonpad_with_collide": nonpad_collide,
        }

    rec = probe(_split, note="A-1 VISIBLE-only pass, newton_skill_env_base.py:1574-1583")
    val = rec.get("value") or {}
    rec["predicate"] = "pad shapes retain COLLIDE AND at least one non-pad shape had COLLIDE cleared"
    rec["pass"] = bool(
        rec.get("status") == PRESENT
        and val.get("pad_with_collide", 0) > 0
        and val.get("nonpad_shapes", 0) > val.get("nonpad_with_collide", 0)
    )
    return rec


# Removed in spec v1.3, recorded here so the deletion is visible rather than silent.
CLIP_WITNESS_REMOVED = (
    "clip: REMOVED as a witness in spec v1.3. The scene's key set is closed and contains no "
    "clip key (newton_route_env.py:725-734: model / solver / state_0 / state_1 / control / "
    "contacts / bws / jws / cable_bodies / cable_bodies_per_world). Clip bodies carry the "
    "auto-label body_N, so substring matching would return 0 and read as 'no clip' -- a false "
    "negative dressed as a measurement. No clip handle is fabricated here; exposing one would "
    "be an env change (p4's court)."
)


def witness_world_count(model: Any, declared: int | None) -> dict[str, Any]:
    """world_count witness: matches the declared multi-world configuration."""
    rec = probe(lambda: int(model.world_count), note="declared vs model.world_count")
    rec["declared"] = declared
    rec["predicate"] = "model.world_count == declared world_count"
    rec["pass"] = bool(rec.get("status") == PRESENT and (declared is None or rec.get("value") == declared))
    return rec


# Spec v1.3 leg roles. Content witnesses are a BACKSTOP; identity is settled by I-1..I-3.
#
#   cable       -- the only leg that actually discriminates (measured: rejects the FK model)
#   world_count -- configuration cross-check, NOT a discriminator (passes on both models)
#   a1_visible  -- context only. Measured pass=true on BOTH the 68-body as-built model and
#                  the 28-body FK model, so it identifies nothing. Recorded, never required.
REQUIRED_WITNESS_LEGS = ("cable", "world_count")
DISCRIMINATING_LEGS = ("cable",)
CONTEXT_ONLY_LEGS = ("a1_visible",)


def run_witness_battery(
    model: Any, declared_worlds: int | None, cable_bodies: Any = None, per_world: int | None = None
) -> dict[str, Any]:
    """Run the section 1.1 content witnesses against ``model`` and summarise.

    The identical battery, with identical inputs, is applied to the FK model for AC-9,
    where **failing** is the required outcome. A battery that returns the same verdict on
    both models is not a witness -- see :func:`negative_control`.
    """
    w = {
        "cable": witness_cable(model, cable_bodies, per_world),
        "a1_visible": witness_a1_visible(model),
        "world_count": witness_world_count(model, declared_worlds),
    }
    w["a1_visible"]["role"] = "CONTEXT ONLY -- passes on the FK model too; identifies nothing"
    passed = [k for k, v in w.items() if v.get("pass")]
    failed = [k for k, v in w.items() if not v.get("pass")]
    required_failed = [k for k in REQUIRED_WITNESS_LEGS if k in failed]
    return {
        "witnesses": w,
        "passed": passed,
        "failed": failed,
        "required_legs": list(REQUIRED_WITNESS_LEGS),
        "discriminating_legs": list(DISCRIMINATING_LEGS),
        "context_only_legs": list(CONTEXT_ONLY_LEGS),
        "required_failed": required_failed,
        "all_pass": len(required_failed) == 0,
        "removed_legs": [CLIP_WITNESS_REMOVED],
        "forbidden_witness_note": FORBIDDEN_WITNESS_NOTE,
    }


def fidelity_record() -> dict[str, Any]:
    """Section 1.2 -- state the gripper build conditions rather than claiming '2F-85'."""
    return {
        "gripper_asset": "ROBOTIQ_STRIPPED_XML = 2f85_koshape.xml (KO-shape claw, <tendon> stripped)",
        "gripper_asset_source": "test_newton_clip_routing.py:161",
        "skip_equality_constraints": True,
        "skip_equality_source": "newton_skill_env_base.py:1561-1572 (both arms)",
        "model_description": (
            "UR5e x2 with a KO-shape STRIPPED Robotiq asset, gripper built with equality "
            "constraints DISABLED. This is NOT a faithful 2F-85: the 4-bar coupling is absent "
            "by construction, so H-6d asks whether a 4-bar-coupled gripper can be built UNDER "
            "THESE CONDITIONS."
        ),
    }


# --------------------------------------------------------------------------------------
# AC-9 -- negative control
# --------------------------------------------------------------------------------------
def negative_control(h: ModelHandles, declared_worlds: int | None, as_built_battery: dict[str, Any]) -> dict[str, Any]:
    """Deliberately measure the FK robot-only model and require H-0 to fail on it.

    A one-sided check ("the FK model failed") is not a negative control: a battery that
    is simply broken fails on *everything*, including the real model, and would report
    success. This was observed on the first run of this harness -- both models failed the
    same three legs and the check still reported PASS.

    AC-9 therefore requires all three of:

    1. the as-built model **passes** the required legs,
    2. the FK model **fails**, and
    3. at least one leg **differs** between them -- the evidence that the battery can
       come out differently at all.
    """
    if h.fk_model is None:
        return {
            "status": UNAVAILABLE,
            "reason": "env._fk_model absent on this build",
            "ac9_pass": False,
            "note": "AC-9 cannot be demonstrated; treat H-0 as unverified (fail-closed)",
        }
    fk_battery = run_witness_battery(h.fk_model, declared_worlds, h.cable_bodies, h.cable_bodies_per_world)

    as_built_ok = bool(as_built_battery["all_pass"])
    fk_rejected = not fk_battery["all_pass"]
    # Which legs actually split the two models -- the evidence that the battery can come
    # out differently at all. Spec v1.3 requires naming them explicitly.
    rejected_on = [
        leg
        for leg in REQUIRED_WITNESS_LEGS
        if as_built_battery["witnesses"].get(leg, {}).get("pass")
        and not fk_battery["witnesses"].get(leg, {}).get("pass")
    ]
    fk_failed_legs = fk_battery["required_failed"]
    non_discriminating = [
        leg
        for leg in fk_battery["witnesses"]
        if fk_battery["witnesses"][leg].get("pass") and as_built_battery["witnesses"].get(leg, {}).get("pass")
    ]
    return {
        "status": PRESENT,
        "target": "env._fk_model (IK robot-only), measured with the IDENTICAL battery and inputs",
        "battery": fk_battery,
        "as_built_passed": as_built_ok,
        "fk_rejected": fk_rejected,
        "fk_failed_on_legs": fk_failed_legs,
        "rejected_on_legs": rejected_on,
        "non_discriminating_legs": non_discriminating,
        "discrimination_margin": len(rejected_on),
        "ac9_pass": bool(as_built_ok and fk_rejected and rejected_on),
        "interpretation": (
            "PASS requires the battery to ACCEPT the real model and REJECT the FK model on at "
            "least one leg. If both models fail, the battery is broken rather than discriminating, "
            "and every downstream number is void."
        ),
    }


# --------------------------------------------------------------------------------------
# H-1 -- envelope declaration (spec section 2)
# --------------------------------------------------------------------------------------
def declare_envelope(joint_names: list[str], lo: float, hi: float, step: float) -> dict[str, Any]:
    """Declare the provisional sweep box.

    W-b waypoints are undetermined, so spec section 2 requires the box be declared
    explicitly and attached to the output. Nothing here may be called a "maximum";
    it is a grid over a declared range, and outside it the quantities are UNMEASURED.
    """
    # R4 (pZ, 62ec7583d0): with an empty joint list this used to emit a well-formed
    # PROVISIONAL envelope declaring samples_per_joint over ZERO joints -- and it satisfied
    # AC-2, because the range/step/count fields were all present. Fail closed instead. The
    # guard is on whether the joint source RESOLVED, not on "is the list empty", because an
    # empty list is the symptom; the cause was that joint names never resolved at all.
    if not joint_names:
        return {
            "status": "INVALID",
            "STOP_required": True,
            "reason": (
                "No joints resolved, so no envelope can be declared. An envelope over zero "
                "joints would satisfy AC-2 while describing nothing."
            ),
            "fix": "Resolve joint names via solver.mj_model (mj_id2name); the Newton Model has no joint_key.",
            "joints": [],
        }
    n_per_joint = max(1, int(round((hi - lo) / step)) + 1)
    return {
        "status": "PROVISIONAL",
        "reason": "W-b waypoints undetermined; re-run is required once they are fixed",
        "joints": joint_names,
        "lower_rad": lo,
        "upper_rad": hi,
        "step_rad": step,
        "samples_per_joint": n_per_joint,
        "grasp_state_included": False,
        "grasp_state_caveat": (
            "Cable-grasped inertia is NOT included. Inertia is therefore on the LOW side, "
            "which makes damping ratios OPTIMISTIC."
        ),
        "validity": (
            "All numbers derived from this envelope are valid INSIDE it only. "
            "Outside is UNMEASURED (not safe)."
        ),
    }


# --------------------------------------------------------------------------------------
# H-2 / H-3 / H-4 -- dynamics, measured on the solver-derived MuJoCo model
# --------------------------------------------------------------------------------------
def _mj_pair(solver: Any) -> tuple[Any, Any]:
    """Return the solver's ``(mj_model, mj_data)``, raising if unavailable."""
    mj_model = getattr(solver, "mj_model", None)
    mj_data = getattr(solver, "mj_data", None)
    if mj_model is None or mj_data is None:
        raise AttributeError("solver does not expose mj_model/mj_data")
    return mj_model, mj_data


def dense_mass_matrix(solver: Any) -> np.ndarray:
    """Densify MuJoCo's sparse ``qM`` into a full coupled mass matrix ``M(q)``."""
    import mujoco

    mj_model, mj_data = _mj_pair(solver)
    nv = int(mj_model.nv)
    dense = np.zeros((nv, nv), dtype=np.float64)
    mujoco.mj_fullM(mj_model, dense, mj_data.qM)
    return dense


def modal_damping(mass: np.ndarray, k_d: np.ndarray, k_e: np.ndarray) -> dict[str, Any]:
    """Solve the quadratic eigenvalue problem ``det(l^2 M + l K_d + K_e) = 0`` (H-2).

    The extraction formula is fixed here and reported with the numbers, because v0.4
    mixed two different definitions of zeta. For a real root pair this uses
    ``zeta = -(l1 + l2) / (2 * sqrt(l1 * l2))``, which can exceed 1. It never uses
    ``zeta = -Re(l) / |l|``, which saturates at 1 and hides overdamping.

    Args:
        mass: Coupled mass matrix, shape ``[n, n]``.
        k_d: Damping matrix, shape ``[n, n]``.
        k_e: Stiffness matrix, shape ``[n, n]``.

    Returns:
        The modal damping record including the formula actually used.
    """
    n = mass.shape[0]
    # Companion linearisation of the quadratic eigenvalue problem.
    zeros, eye = np.zeros((n, n)), np.eye(n)
    a_top = np.hstack([zeros, eye])
    minv = np.linalg.solve(mass, np.hstack([-k_e, -k_d]))
    companion = np.vstack([a_top, minv])
    eigs = np.linalg.eigvals(companion)

    ratios: list[float] = []
    used_pairs = 0
    unpaired = 0
    consumed = np.zeros(len(eigs), dtype=bool)
    for i, lam in enumerate(eigs):
        if consumed[i]:
            continue
        # Pair each root with its conjugate/partner to apply the product form.
        partner = None
        for j in range(i + 1, len(eigs)):
            if consumed[j]:
                continue
            if abs(eigs[j] - np.conj(lam)) < 1e-9 * max(1.0, abs(lam)):
                partner = j
                break
        if partner is None:
            unpaired += 1
            consumed[i] = True
            continue
        l1, l2 = lam, eigs[partner]
        consumed[i] = consumed[partner] = True
        prod = l1 * l2
        if abs(prod) < 1e-30:
            continue
        zeta = -(l1 + l2) / (2.0 * np.sqrt(prod))
        ratios.append(float(np.real(zeta)))
        used_pairs += 1

    diag_ratio = None
    with np.errstate(divide="ignore", invalid="ignore"):
        denom = 2.0 * np.sqrt(np.clip(np.diag(mass) * np.diag(k_e), 1e-30, None))
        diag = np.diag(k_d) / denom
        if diag.size:
            diag_ratio = float(np.min(diag))

    return {
        "formula": "zeta = -(l1 + l2) / (2 * sqrt(l1 * l2))  [real-root-pair form; may exceed 1]",
        "formula_not_used": "zeta = -Re(l)/|l|  [saturates at 1 -- deliberately NOT mixed in]",
        "zeta_modal_min": float(min(ratios)) if ratios else None,
        "zeta_diagonal_approx_min": diag_ratio,
        "diag_vs_modal_delta": (
            float(diag_ratio - min(ratios)) if (ratios and diag_ratio is not None) else None
        ),
        "paired_roots": used_pairs,
        "unpaired_roots": unpaired,
        "n_dof_solved": int(n),
    }


def torque_budget(solver: Any, cap: float | None) -> dict[str, Any]:
    """H-3: ``tau_bias(q, qd) = qfrc_bias`` and the acceleration headroom.

    ``qfrc_bias`` carries gravity *and* Coriolis/centrifugal terms, so this is swept
    over ``(q, qd)`` rather than gravity alone. Headroom divides by the largest
    eigenvalue of the coupled mass matrix, not by a diagonal element.
    """
    _, mj_data = _mj_pair(solver)
    bias = np.abs(_to_numpy(mj_data.qfrc_bias))
    mass = dense_mass_matrix(solver)
    lam_max = float(np.max(np.linalg.eigvalsh(0.5 * (mass + mass.T))))
    max_bias = float(np.max(bias)) if bias.size else None
    a_max = None
    if cap is not None and max_bias is not None and lam_max > 0:
        a_max = (cap - max_bias) / lam_max
    return {
        "tau_bias_includes": "gravity + Coriolis/centrifugal (qfrc_bias)",
        "max_abs_tau_bias": max_bias,
        "lambda_max_M": lam_max,
        "cap_used": cap,
        "cap_source": "H-6a measured value (NOT a declared constant)" if cap is not None else None,
        "a_max": a_max,
        "a_max_formula": "a_max = (cap - max|tau_bias|) / lambda_max(M(q))",
    }


def grasp_jacobian(solver: Any, model: Any) -> dict[str, Any]:
    """H-4: Jacobian at the pad body -- the body that actually contacts the cable.

    ``wrist_3_link`` is not used (its wrist_2/wrist_3 position columns are structurally
    zero) and the ``pinch`` site alone is not used (``collapse_fixed_joints`` rigidly
    fixes it to ``wrist_3_link``, zeroing all eight gripper DOF columns).

    The pad body is discovered from labels. Note the scene marks pads on *shape*
    labels (``shape_label`` at ``:1576-1583``); the owning body is resolved from the
    shape, and if only shape labels carry 'pad' that resolution path is recorded.
    """
    import mujoco

    mj_model, mj_data = _mj_pair(solver)

    def _pad_body_ids() -> list[tuple[int, str]]:
        out: list[tuple[int, str]] = []
        for bid in range(int(mj_model.nbody)):
            name = mujoco.mj_id2name(mj_model, mujoco.mjtObj.mjOBJ_BODY, bid) or ""
            if "pad" in name.lower():
                out.append((bid, name))
        return out

    pads = _pad_body_ids()
    if not pads:
        return {
            "status": ABSENT,
            "reference_frame": None,
            "note": (
                "No MuJoCo body name contains 'pad'. The scene tags pads on shape_label "
                "(newton_skill_env_base.py:1576-1583), so the pad->body resolution must be "
                "supplied from the Newton model; reporting ABSENT rather than substituting "
                "wrist_3_link, which is explicitly forbidden."
            ),
        }

    nv = int(mj_model.nv)
    results = []
    for bid, name in pads:
        jacp = np.zeros((3, nv), dtype=np.float64)
        jacr = np.zeros((3, nv), dtype=np.float64)
        mujoco.mj_jacBody(mj_model, mj_data, jacp, jacr, bid)
        results.append(
            {
                "body_id": bid,
                "body_name": name,
                # mm of pad translation per rad of joint motion.
                "translation_mm_per_rad": (np.abs(jacp) * 1000.0).max(axis=0).tolist(),
                # mrad of pad rotation per rad of joint motion, evaluated separately.
                "rotation_mrad_per_rad": (np.abs(jacr) * 1000.0).max(axis=0).tolist(),
            }
        )
    return {
        "status": PRESENT,
        "reference_frame": "pad body (cable-contacting), discovered by name",
        "excluded_frames": [
            "wrist_3_link (position columns structurally zero)",
            "pinch site alone (gripper DOF columns zero)",
        ],
        "gripper_dof_contribution_included": True,
        "error_direction_note": (
            "Using the pad body includes the gripper DOF columns. Had a wrist frame been used, "
            "gripper compliance would be omitted and the reported sensitivity would be an UNDER-estimate."
        ),
        "pads": results,
    }


# --------------------------------------------------------------------------------------
# H-6 -- does the mechanism exist? (measure, never adopt)
# --------------------------------------------------------------------------------------
def mechanism_survey(solver: Any, model: Any) -> dict[str, Any]:
    """H-6a..H-6d: report what exists. Adoption is Rs's decision, not this harness's."""
    mj_model = getattr(solver, "mj_model", None)

    h6a = {
        "question": "What are the REAL effort caps, and does a cap survive the strip?",
        "joint_effort_limit": probe(lambda: _to_numpy(model.joint_effort_limit)),
        "jnt_actfrcrange": probe(lambda: _to_numpy(mj_model.jnt_actfrcrange)),
        "actuator_forcerange": probe(lambda: _to_numpy(mj_model.actuator_forcerange)),
        "nu": probe(lambda: int(mj_model.nu)),
        "ddr26_note": (
            "DDR#26 (LEDGER:57): ur5e.xml imports 12 <actuator> entries (nu=16 on the flag-OFF "
            "build) whose saturating torque at ctrl==0 was masked by kinematic overwrite; the "
            "smoke build at nu=28 double-actuates the same joints. The actuator inventory above "
            "is what makes that state visible -- H-3 is uninterpretable without it."
        ),
        "prior_art": (
            "task_config.py:316-318 -- GRIPPER_DRIVER_EFFORT_LIMIT_NM = 2.5 restores the force cap "
            "the tendon strip removed (D-S5-2); accepted via a one-frame post-clamp "
            "|qfrc_actuator| <= 2.5. Same constant placement and same acceptance shape apply here."
        ),
    }

    h6b = {
        "question": "Is there a reachable gravity-compensation path, proven by a positive control?",
        "body_gravcomp": probe(lambda: _to_numpy(mj_model.body_gravcomp)),
        "ngravcomp": probe(lambda: int(mj_model.ngravcomp)),
        "qfrc_gravcomp": probe(lambda: _to_numpy(_mj_pair(solver)[1].qfrc_gravcomp)),
        "positive_control_required": (
            "A write is not proof. The path counts as working only if qfrc_gravcomp or qacc CHANGES "
            "after the write. If no route produces a state change, the correct report is 'absent'."
        ),
        "multiworld_caveat": (
            "With world_count > 1 a CPU-side mj_model write can be GPU-inert (the mjw/warp copy is "
            "what steps). A positive control must be read back from the representation that steps."
        ),
    }

    h6c = {
        "question": "Is Control.joint_f inside or outside the effort cap?",
        "expectation_to_falsify": "predicted OUTSIDE the cap (applied via qfrc_applied)",
        "qfrc_applied_present": probe(lambda: _to_numpy(_mj_pair(solver)[1].qfrc_applied).shape),
        "note": "If it lands outside the cap, using it makes the sim STRONGER than the real robot.",
    }

    h6d = {
        "question": "Can a 4-bar-coupled gripper be built under the current conditions?",
        "current_conditions": "KO-shape stripped asset + skip_equality_constraints=True (section 1.2)",
        "neq": probe(lambda: int(mj_model.neq)),
        "eq_type": probe(lambda: _to_numpy(mj_model.eq_type)),
        "stop_condition": (
            "The KO-shape asset is human-LOCKED. If enabling the 4-bar turns out to require EDITING "
            "that asset, this harness STOPS and escalates p4 -> Rs. It does not edit the asset."
        ),
    }

    return {"H-6a": h6a, "H-6b": h6b, "H-6c": h6c, "H-6d": h6d}


# --------------------------------------------------------------------------------------
# H-2 -- coupled modal damping (spec v1.2 sections H-2.1 / H-2.2 / H-2.3)
#
# DOF declaration by p11 (2026-07-21), checked against measurement rather than assumed:
#   target   12  UR5e revolute            (ARM_DOF = 6 x 2, task_config.py:27)
#   excl A    4  gripper driver           (GRIPPER_DRIVER_JOINT_IDX = [6, 10] x 2, :34)
#   excl B   12  gripper passive 4-bar    (GRIPPER_JOINT_RANGE 8 - driver 2 = 6, x 2, :35)
#   outside  >=40 cable joints
# Arm-side total must be 28 = 12 + 16. If it is not, p11's premise is wrong and we STOP.
# --------------------------------------------------------------------------------------
# Joint names are underscore-joined (ur5e_worldbody_base_...), unlike BODY labels which are
# slash-joined (ur5e/worldbody/...). Matching joints with the body-label form classified all
# 68 joints as "cable" and tripped the STOP. Measured against real names instead.
ARM_TOKEN = "ur5e"
GRIPPER_TOKEN = "robotiq"
# The driver joints are ids 6 and 10 per arm (task_config.py:34). A bare "driver" substring
# over the full path also catches right_driver_right_coupler_joint, whose PARENT is the
# driver -- 8 hits instead of 4. Anchor on the joint's own trailing name.
DRIVER_JOINT_RE = re.compile(r"_driver_joint(_\d+)?$")


def resolve_joint_table(solver: Any) -> dict[str, Any]:
    """Build the measured joint name -> index table (spec H-2.1, and the V-4 fix).

    Joint names are read from ``solver.mj_model`` via ``mj_id2name``. The Newton ``Model``
    has no ``joint_key`` on this build, so names never resolved through it -- that was the
    real cause behind pZ's G3 finding, and it made V-4 unsatisfiable by that route.

    Classification is by name prefix, and the resulting counts are CHECKED against p11's
    declaration. A mismatch is a STOP, not something to quietly reconcile.
    """
    import mujoco

    mj_model, _ = _mj_pair(solver)
    names, arm, driver, passive, other = [], [], [], [], []
    for jid in range(int(mj_model.njnt)):
        nm = mujoco.mj_id2name(mj_model, mujoco.mjtObj.mjOBJ_JOINT, jid) or ""
        dofadr = int(mj_model.jnt_dofadr[jid])
        entry = {"joint_id": jid, "name": nm, "dof_adr": dofadr, "jnt_type": int(mj_model.jnt_type[jid])}
        names.append(entry)
        low = nm.lower()
        if ARM_TOKEN in low:
            arm.append(entry)
        elif GRIPPER_TOKEN in low:
            (driver if DRIVER_JOINT_RE.search(low) else passive).append(entry)
        else:
            other.append(entry)

    arm_side = len(arm) + len(driver) + len(passive)
    expected = {"arm": 12, "driver": 4, "passive": 12, "arm_side_total": 28}
    measured = {
        "arm": len(arm),
        "driver": len(driver),
        "passive": len(passive),
        "arm_side_total": arm_side,
        "cable_or_other": len(other),
    }
    mismatch = {k: (expected[k], measured[k]) for k in expected if expected[k] != measured[k]}
    return {
        "resolved_via": "solver.mj_model + mj_id2name (Newton Model has no joint_key on this build)",
        "n_joints_named": sum(1 for e in names if e["name"]),
        "n_joints_total": len(names),
        "expected_by_p11": expected,
        "measured": measured,
        "mismatch": mismatch,
        "STOP_required": bool(mismatch),
        "stop_reason": (
            "Measured joint classification does not match p11's declaration (28 = 12 + 16). "
            "EITHER the declaration or this classifier is wrong -- inspect the emitted names "
            "before attributing the mismatch. Report; do not silently adjust either side."
            if mismatch
            else None
        ),
        "table": names,
        "arm_dof_adr": [e["dof_adr"] for e in arm],
        "excluded_dof_adr": [e["dof_adr"] for e in driver + passive],
        "cable_dof_adr": [e["dof_adr"] for e in other],
    }


def stiffness_damping_diagonals(solver: Any, n_dof: int) -> dict[str, Any]:
    """Assemble K_e and K_d diagonals from the model's own fields (never invented).

    Passive terms come from ``jnt_stiffness`` and ``dof_damping``; driven terms from
    position-servo actuators (``actuator_gainprm``/``actuator_biasprm``). The source of
    every contribution is recorded so the H-2.2 self-check (passive 4-bar entries should
    be about zero) is testing measured values, not assumptions.
    """
    mj_model, _ = _mj_pair(solver)
    k_e = np.zeros(n_dof, dtype=np.float64)
    k_d = np.asarray(_to_numpy(mj_model.dof_damping), dtype=np.float64)[:n_dof].copy()

    jnt_stiff = np.asarray(_to_numpy(mj_model.jnt_stiffness), dtype=np.float64)
    for jid in range(int(mj_model.njnt)):
        adr = int(mj_model.jnt_dofadr[jid])
        if 0 <= adr < n_dof:
            k_e[adr] += float(jnt_stiff[jid])

    # A position servo carries kp/kv in biasprm ([0, -kp, -kv]); gainprm[0] mirrors kp, so
    # reading bias alone is sufficient and avoids double-counting.
    servo = 0
    bias = np.asarray(_to_numpy(mj_model.actuator_biasprm), dtype=np.float64)
    trnid = np.asarray(_to_numpy(mj_model.actuator_trnid), dtype=np.int64)
    for aid in range(int(mj_model.nu)):
        jid = int(trnid[aid][0])
        if not (0 <= jid < int(mj_model.njnt)):
            continue
        adr = int(mj_model.jnt_dofadr[jid])
        if not (0 <= adr < n_dof):
            continue
        # MuJoCo position servo: bias = [0, -kp, -kv].
        kp, kv = -float(bias[aid][1]), -float(bias[aid][2])
        if kp or kv:
            k_e[adr] += max(kp, 0.0)
            k_d[adr] += max(kv, 0.0)
            servo += 1
    return {
        "k_e_diag": k_e,
        "k_d_diag": k_d,
        "sources": "K_e = jnt_stiffness + position-servo kp; K_d = dof_damping + servo kv",
        "servo_actuators_contributing": servo,
    }


def _zeta_from_qep(mass: np.ndarray, k_d: np.ndarray, k_e: np.ndarray) -> dict[str, Any]:
    """Quadratic eigenvalue solve returning the damping ratios and the modes."""
    n = mass.shape[0]
    companion = np.vstack(
        [np.hstack([np.zeros((n, n)), np.eye(n)]), np.linalg.solve(mass, np.hstack([-k_e, -k_d]))]
    )
    eigs, vecs = np.linalg.eig(companion)
    return {"eigs": eigs, "vecs": vecs, "n": n}


def _pair_zetas(eigs: np.ndarray, vecs: np.ndarray | None = None, n: int | None = None) -> list[float]:
    """Apply the spec's zeta form to the two roots of each second-order mode.

    Uses ``zeta = -(l1 + l2) / (2 sqrt(l1 l2))``, which can exceed 1. Never mixes in
    ``-Re(l)/|l|``, which saturates at 1 and hides overdamping (spec H-2).

    Pairing is by MODE SHAPE, not by conjugacy. An earlier version paired only complex
    conjugates, which silently produced zero mode pairs on this model: the measured system
    is overdamped (diagonal zeta ~3.2), so each mode's two roots are DISTINCT REALS and are
    not each other's conjugate. The spec's own wording ("for real root pairs") assumes those
    pairs exist, so the pairing has to find them. Two roots belong to the same mode when
    their companion-form mode shapes are parallel.
    """
    m = len(eigs)
    out, used = [], np.zeros(m, dtype=bool)

    if vecs is not None and n:
        shapes = vecs[:n, :]
        norms = np.linalg.norm(shapes, axis=0)
        norms[norms == 0] = 1.0
        unit = shapes / norms

    for i in range(m):
        if used[i]:
            continue
        partner, best = None, -1.0
        for j in range(i + 1, m):
            if used[j]:
                continue
            if vecs is not None and n:
                sim = float(abs(np.vdot(unit[:, i], unit[:, j])))
            else:
                sim = 1.0 if abs(eigs[j] - np.conj(eigs[i])) < 1e-9 * max(1.0, abs(eigs[i])) else 0.0
            if sim > best:
                best, partner = sim, j
        if partner is None or best < 0.9:
            used[i] = True
            continue
        used[i] = used[partner] = True
        l1, l2 = eigs[i], eigs[partner]
        prod = l1 * l2
        if abs(prod) < 1e-30:
            continue
        out.append(float(np.real(-(l1 + l2) / (2.0 * np.sqrt(prod)))))
    return out


def run_h2(solver: Any, table: dict[str, Any]) -> dict[str, Any]:
    """H-2: coupled modal damping over the three reductions, with the self-checks."""
    mj_model, _ = _mj_pair(solver)
    nv = int(mj_model.nv)
    mass_full = dense_mass_matrix(solver)
    diag = stiffness_damping_diagonals(solver, nv)
    k_e_full, k_d_full = np.diag(diag["k_e_diag"]), np.diag(diag["k_d_diag"])

    arm = [a for a in table["arm_dof_adr"] if 0 <= a < nv]
    excl = [a for a in table["excluded_dof_adr"] if 0 <= a < nv]
    cable = [a for a in table["cable_dof_adr"] if 0 <= a < nv]
    arm_side = arm + excl

    # --- H-2.3 self-check: p11 predicts the arm/cable mass coupling is exactly zero -------
    coupling = float(np.linalg.norm(mass_full[np.ix_(arm_side, cable)])) if (arm_side and cable) else None
    coupling_zero = coupling is not None and coupling < 1e-12

    # --- H-2.2 self-check: passive 4-bar stiffness should be about zero ------------------
    ke_arm_side = diag["k_e_diag"][arm_side] if arm_side else np.array([])
    passive_adr = [a for a in excl if a not in set(table["arm_dof_adr"])]
    ke_passive = diag["k_e_diag"][passive_adr] if passive_adr else np.array([])

    def _reduce(idx: list[int]) -> dict[str, Any]:
        if not idx:
            return {"status": UNAVAILABLE}
        sl = np.ix_(idx, idx)
        sol = _zeta_from_qep(mass_full[sl], k_d_full[sl], k_e_full[sl])
        z = _pair_zetas(sol["eigs"], sol["vecs"], sol["n"])
        return {"zeta_min": float(min(z)) if z else None, "n_dof": len(idx), "mode_pairs": len(z)}

    # (i) fixed: leading 12x12 principal minor -- the conservative bar
    red_i = _reduce(arm)
    # (ii) mass condensation: excluded DOF are force-free -> optimistic lower bound
    red_ii: dict[str, Any] = {"status": UNAVAILABLE}
    if arm and excl:
        m_aa, m_ab = mass_full[np.ix_(arm, arm)], mass_full[np.ix_(arm, excl)]
        m_bb = mass_full[np.ix_(excl, excl)]
        try:
            m_red = m_aa - m_ab @ np.linalg.solve(m_bb, mass_full[np.ix_(excl, arm)])
            sl = np.ix_(arm, arm)
            sol2 = _zeta_from_qep(m_red, k_d_full[sl], k_e_full[sl])
            z = _pair_zetas(sol2["eigs"], sol2["vecs"], sol2["n"])
            red_ii = {"zeta_min": float(min(z)) if z else None, "n_dof": len(arm), "mode_pairs": len(z)}
        except np.linalg.LinAlgError as exc:
            red_ii = {"status": ERROR, "error": str(exc)}
    # (iii) full arm-side 28 DOF with real stiffness; zeta read ONLY on arm-dominated modes
    red_iii: dict[str, Any] = {"status": UNAVAILABLE}
    if arm_side:
        sl = np.ix_(arm_side, arm_side)
        sol = _zeta_from_qep(mass_full[sl], k_d_full[sl], k_e_full[sl])
        pos = {a: k for k, a in enumerate(arm_side)}
        arm_rows = [pos[a] for a in arm]
        eigs, vecs, n = sol["eigs"], sol["vecs"], sol["n"]
        dominated = []
        for m in range(len(eigs)):
            shape = np.abs(vecs[:n, m])
            tot = float(np.sum(shape))
            if tot <= 0:
                continue
            part = float(np.sum(shape[arm_rows]) / tot)
            if part > 0.5:
                # Keep the INDEX. Storing the eigenvalue and recovering the index via `is`
                # fails: numpy scalars are fresh objects on every access.
                dominated.append((m, part))
        dom_idx = [m for m, _ in dominated]
        z = _pair_zetas(eigs[dom_idx], vecs[:, dom_idx], n) if dom_idx else []
        red_iii = {
            "zeta_min_arm_dominated": float(min(z)) if z else None,
            "n_dof": len(arm_side),
            "arm_dominated_modes": len(dominated),
            "note": "zeta read only on modes whose arm-coordinate participation exceeds 0.5",
        }

    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.diag(mass_full)[arm] * diag["k_e_diag"][arm] if arm else np.array([])
        diag_zeta = diag["k_d_diag"][arm] / (2.0 * np.sqrt(np.clip(d, 1e-30, None))) if arm else np.array([])

    return {
        "zeta_formula": "zeta = -(l1 + l2) / (2 sqrt(l1 l2))  [may exceed 1]",
        "zeta_formula_not_used": "zeta = -Re(l)/|l|  [saturates at 1 -- deliberately not mixed in]",
        "dof_sets": {"target_arm": arm, "excluded": excl, "cable_outside": len(cable)},
        "reduction_i_fixed_12x12_BAR": red_i,
        "reduction_ii_mass_condensation_lower_bound": red_ii,
        "reduction_iii_full_armside_arm_dominated": red_iii,
        "diagonal_approx_zeta_min": float(np.min(diag_zeta)) if len(diag_zeta) else None,
        "self_check_H2_3_arm_cable_mass_coupling": {
            "norm_M_arm_cable": coupling,
            "p11_prediction": 0.0,
            "matches_prediction": coupling_zero,
            "STOP_required": bool(coupling is not None and not coupling_zero),
            "meaning": "Non-zero means the cable IS in the arm's kinematic tree; the DOF declaration is void.",
        },
        "self_check_H2_2_passive_stiffness_near_zero": {
            "k_e_diag_arm_side": ke_arm_side.tolist(),
            "k_e_diag_passive": ke_passive.tolist(),
            "passive_max_abs": float(np.max(np.abs(ke_passive))) if ke_passive.size else None,
            "p11_prediction": "passive 4-bar entries approximately 0",
            "meaning": "If passive stiffness is NOT ~0, p11's explanation for the structural zeta=0 is wrong.",
        },
        "raw_matrices_arm_side": {
            "dof_order": arm_side,
            "note": "Raw blocks are emitted so the reduction can be re-adjudicated without re-measuring.",
            "M": mass_full[np.ix_(arm_side, arm_side)].tolist() if arm_side else [],
            "K_e": k_e_full[np.ix_(arm_side, arm_side)].tolist() if arm_side else [],
            "K_d": k_d_full[np.ix_(arm_side, arm_side)].tolist() if arm_side else [],
        },
        "stiffness_sources": diag["sources"],
        "servo_actuators_contributing": diag["servo_actuators_contributing"],
        "grasp_caveat": "Cable inertia while grasped does NOT enter M, so zeta is on the optimistic side.",
    }


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def run_h0(env: Any, declared_worlds: int | None) -> dict[str, Any]:
    """Run the fail-closed foundation: identity + witnesses + fidelity + AC-9."""
    h = acquire_models(env)
    ident = identity_record(h)
    battery = run_witness_battery(h.as_built, declared_worlds, h.cable_bodies, h.cable_bodies_per_world)
    neg = negative_control(h, declared_worlds, battery)

    # V-1 is now settled by object reference (I-1..I-3), not by content agreement.
    v1 = ident.get("identity_all_pass") is True
    v3 = battery["all_pass"]
    report = {
        "identity": ident,
        "inventory": inventory(h.as_built, h.solver),
        "witness_battery": battery,
        "fidelity": fidelity_record(),
        "negative_control_ac9": neg,
        "verdicts_for_pZ": {
            "V-1_identity_by_reference_I1_I2_I3": v1,
            "V-3_content_backstop_required_legs": v3,
            "AC-9_wrong_model_rejected": neg.get("ac9_pass"),
            "AC-9_rejected_on_legs": neg.get("rejected_on_legs"),
            "note": (
                "V-1 is settled by 'is' comparisons (I-1..I-3), not by content agreement. "
                "V-2 and V-4 are pZ-side predicates (independent rebuild / joint-name resolution)."
            ),
        },
        # Fail-closed: downstream numbers are void unless the foundation holds.
        "downstream_valid": bool(v1 and v3 and neg.get("ac9_pass")),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["h0", "all"], default="h0", help="h0 = fail-closed foundation only")
    ap.add_argument("--out", default="arm_control_measurement_report.json")
    ap.add_argument("--world-count", type=int, default=1, help="env world_count (newton_route_env.py:419 default)")
    ap.add_argument("--device", default="cuda:0", help="env device (newton_route_env.py:419 default)")
    ap.add_argument("--worlds", type=int, default=None, help="declared world_count for the witness check")
    ap.add_argument("--sweep-lo", type=float, default=-0.5, help="provisional envelope lower bound [rad]")
    ap.add_argument("--sweep-hi", type=float, default=0.5, help="provisional envelope upper bound [rad]")
    ap.add_argument("--sweep-step", type=float, default=0.25, help="provisional envelope step [rad]")
    args = ap.parse_args(argv)

    report: dict[str, Any] = {
        "harness": "arm_control_measurement_harness",
        "role": "p0 / IMPL-BUILDER -- design-time measurement only (no design decision, no training)",
        "provenance": collect_provenance(),
        "stage": args.stage,
    }

    try:
        # The env is constructed through the PRODUCTION path. The harness assembles nothing.
        # Headless MuJoCo, matching the sibling probes (comp3_perarm_cell_grasplift.py:70-71).
        os.environ.setdefault("MUJOCO_GL", "egl")
        os.environ.pop("DISPLAY", None)

        import newton_route_env as nre  # noqa: PLC0415

        # Production-path construction. The harness assembles no model of its own; it only
        # supplies the documented constructor arguments and records what it supplied.
        env = nre.NewtonRouteEnv(world_count=args.world_count, device=args.device)
        report["env_construction"] = {
            "class": "newton_route_env.NewtonRouteEnv",
            "module_file": getattr(nre, "__file__", None),
            "import_route": (
                "top-level module with thread_isaac_lab/envs on sys.path (reuse of "
                "comp3_perarm_cell_grasplift.py:59-74). The package __init__ route imports "
                "assets_cfg -> isaaclab_physx, which is absent from the env7 mujoco/Newton venv."
            ),
            "signature_source": "newton_route_env.py:419 (world_count=1, device='cuda:0', cfg=None)",
            "world_count": args.world_count,
            "device": args.device,
            "note": (
                "world_count > 1 under USE_MUJOCO_CPU=True would leave every non-template world "
                "silently frozen; the solver factory refuses that combination mechanically "
                "(newton_skill_env_base.py:1324-1330)."
            ),
        }
        declared_worlds = args.worlds if args.worlds is not None else args.world_count
        report["h0"] = run_h0(env, declared_worlds)

        if args.stage == "all":
            if not report["h0"]["downstream_valid"]:
                report["downstream"] = {
                    "skipped": True,
                    "reason": "H-0 fail-closed: V-1/V-3/AC-9 did not all pass, so every downstream number is void.",
                }
            else:
                h = acquire_models(env)
                # V-4 / R3: names come from solver.mj_model. The Newton Model has no
                # joint_key, so the old inventory route silently yielded nothing.
                table = resolve_joint_table(h.solver)
                report["h2_joint_table"] = table
                names = [e["name"] for e in table["table"] if e["name"]]
                report["h1_envelope"] = declare_envelope(names, args.sweep_lo, args.sweep_hi, args.sweep_step)
                if table["STOP_required"]:
                    report["h2_modal_damping"] = {
                        "status": "STOP",
                        "reason": table["stop_reason"],
                        "mismatch_expected_vs_measured": table["mismatch"],
                    }
                else:
                    report["h2_modal_damping"] = probe(lambda: run_h2(h.solver, table))
                report["h6_mechanisms"] = mechanism_survey(h.solver, h.as_built)
                cap_rec = report["h6_mechanisms"]["H-6a"]["jnt_actfrcrange"]
                cap = None
                if cap_rec.get("status") == PRESENT:
                    arr = np.asarray(cap_rec["value"], dtype=float)
                    finite = arr[np.isfinite(arr) & (arr != 0)]
                    cap = float(np.min(np.abs(finite))) if finite.size else None
                report["h3_torque_budget"] = probe(lambda: torque_budget(h.solver, cap))
                report["h4_grasp_jacobian"] = probe(lambda: grasp_jacobian(h.solver, h.as_built))
                report["h5_transmission"] = {
                    "status": UNAVAILABLE,
                    "reason": "Requires stepping the sim through grasp/seat phases; not run in this stage.",
                }
    except Exception as exc:  # noqa: BLE001 - always emit a report, even on failure
        report["fatal"] = {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}

    # A relative --out is resolved against the repo root, not the caller's cwd: an entire
    # env build was once lost to a FileNotFoundError raised only at the final write.
    out_path = args.out if os.path.isabs(args.out) else os.path.join(REPO_ROOT, args.out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(json.dumps(report.get("h0", {}).get("verdicts_for_pZ", report.get("fatal", {})), indent=2))
    print(f"[harness] wrote {out_path}")
    return 0 if "fatal" not in report else 1


if __name__ == "__main__":
    raise SystemExit(main())
