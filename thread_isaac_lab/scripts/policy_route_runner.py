# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""B0/B1 evaluator for the committed C1->C2 route (B_BC_BUILD_SPEC.md §4 + §10 ERRATA).

Replays the converted BC actions open-loop (B0: dataset lookup on the SAME code path a policy
would use) through the LOCKED route module (IMPORT-ONLY -- never edited), re-implements the route's
inline verdict at the schedule landmark frames, and emits ``runner_verdict.json`` + an optional
post-hoc video leg. Static-analysis / py_compile target only -- the GPU route is run by the parent.

Binding notes:
  * §4.1 8-step startup preamble mirrors route ``main()`` (:6494-6640).
  * §4.2 arm apply = ``solve_ik_dual`` once + sub-interpolate the joint delta across 10 frames,
    gripper coords preserved (mirror ``ik_move_both`` :1927-2007).
  * E1/E9/E10 sha pins fail-closed; E2 events fire at their recorded PHYSICS frame with NO injected
    settle steps; E6 grip columns are [L,R] (mapped by NAMED index); E8 IK non-convergence logs +
    continues + tags the frame, and the runner ALWAYS emits ``runner_verdict.json`` with a
    ``failure_mode`` field via try/finally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# --- sha pins (E1/E9/E10/E11). A sha outside these sets => fail-closed STOP. ---
ROUTE_SHA_ACCEPT = {
    "9bdf8f63c192739e6beab7c44771eec01415d2d1b03589cfae7212ddc7dcfc34",  # as-run
    "ac0e3f5311ea71943d02f2ff299f202b8796b36e4c904f9d4923891be29c6eb5",  # current committed (fd005ab83f state)
}
TASKCFG_SHA = "1a0851db9cfc2c740c98821c73c84f5405d1cc96df5fe22a71f66906bb1762bc"
BASE_SHA = "e6d3cdbca048a367d6edb8754788ef8ca3939ecb5ef8efae455d76c8fd488e00"  # WT-modified/uncommitted (E10)

PHYS_PER_CTRL = 10  # cadence (meta cadence_physics_steps_per_rl); asserted vs meta at load
GRIP_CLOSED_RAD = 0.6  # converter's grip-predicate for held_seg_l (§2.3, E6 col L)
SEAT_DIST_MM = 0.5  # canonical seat: cable<->clip touching (mirror route _c2_settled :4587)
SEAT_Z_TOL_MM = 3.0  # canonical seat: |seat-z - groove-z| (mirror route _c2_settled :4587)
REACH_88_MM = 20.0  # _at_88 wall (mirror route :4499)
GRIP_N_MIN = 0.1  # grips iff claw<->cable normal > this (mirror route :4497-4498)
SUCCESS_VERDICTS = {"SUCCESS_DUAL_LOADED_AT_88", "SUCCESS_R_GRIP_L_CAGE_AT_88"}  # E7: SET-based, never str-equal
GUARD2_M = 0.015  # E15 guard-2 v2: per-arm 3D ||tgt-ee||>15mm rate-limit


def _sha256(path: str) -> str:
    """Return the hex sha256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_rec_offset(path_str: str):
    """Parse the ``rec_<x>_<y>`` grasp start-offset [mm] from a path (dir or file) for the Opt-i' guard.

    Mirrors the ``route_demo_to_bc._offset_from_npz_path`` (:498-505) token rule byte-for-byte:
    ``z0``/``0``/``z`` -> 0, ``p<N>`` -> +N, ``m<N>`` -> -N (the CP-C offsets are integer mm, e.g.
    ``rec_p8_p8`` -> (8, 8), ``rec_m20_0`` -> (-20, 0), ``rec_z0_m10`` -> (0, -10)). Walks the path's own
    basename then its parents and returns the CLOSEST ``rec_<x>_<y>`` component as an ``(dx_mm, dy_mm)`` int
    tuple; a trailing suffix (e.g. ``rec_m8_p8_rerun``) is tolerated (x/y = the two tokens right after ``rec``,
    a deliberate ``>=3`` relaxation of the converter's strict ``==3`` so rerun dirs still resolve). Returns
    ``None`` when NO ``rec_``-prefixed component exists (nominal dir -> the caller SKIPs the assert, per brief).
    A ``rec_``-prefixed component with a MALFORMED token is fail-loud (``SystemExit``).
    """

    def _tok(t):  # byte-identical to route_demo_to_bc._offset_from_npz_path::_tok
        if t in ("z0", "0", "z"):
            return 0
        if t and t[0] == "p" and t[1:].isdigit():
            return int(t[1:])
        if t and t[0] == "m" and t[1:].isdigit():
            return -int(t[1:])
        raise SystemExit(f"Opt-i' STOP: bad rec_ offset token {t!r} in path {path_str!r}")

    p = Path(os.path.abspath(path_str))
    for name in (p.name, *(par.name for par in p.parents)):
        parts = name.split("_")
        if len(parts) >= 3 and parts[0] == "rec":
            return (_tok(parts[1]), _tok(parts[2]))
    return None


def _opt_i_prime_check(schedule_source_offset, rollout_offset):
    """TASK B (Opt-i') guard: the schedule-source offset MUST equal the rollout's target offset (rounded mm).

    %12 empirically REFUTED frame-invariance (18 demos -> 6 raw phase_id signatures / 3 at +-1 control-step), so a
    shared/wrong-offset schedule misfires grip/pin by <=1 control step. Compares as rounded-mm tuples; a mismatch is
    a **loud SystemExit** so the rollout stops before consuming GPU time. Returns a status string:
    ``"ok"`` (offsets match), ``"skip_no_source"`` (source offset unknown -> nominal dir; caller warns + skips, per
    brief item 2), or ``"inert"`` (no ``--rollout-offset`` given -> guard off for 13-phase / B0 / B0b back-compat).
    """
    if rollout_offset is None:
        return "inert"
    if schedule_source_offset is None:
        return "skip_no_source"
    if tuple(schedule_source_offset) != tuple(rollout_offset):
        raise SystemExit(
            f"Opt-i' STOP: schedule from offset {tuple(schedule_source_offset)} != rollout offset "
            f"{tuple(rollout_offset)} -- each rollout must use its OWN demo's schedule"
        )
    return "ok"


def _set_env_gates(env_gates: dict, device: str) -> dict:
    """§4.1-1 / E9: write env-gates BEFORE importing the route module.

    Skips null-valued keys (never writes the string "None"), FORCES ``DEMO_RECORD=0`` (E9/E1 dead-code
    the batch-fix delta), and pins ``NEWTON_DEVICE``. Returns the gates actually written.
    """
    written = {}
    for key, val in env_gates.items():
        if val is None:  # E9: skip null keys (e.g. C2_TILT_SIGN) -- never write "None"
            continue
        os.environ[key] = str(val)
        written[key] = str(val)
    os.environ["DEMO_RECORD"] = "0"  # E9/E1: force recorder OFF so the batch-fix delta is dead code here
    written["DEMO_RECORD"] = "0"
    os.environ["NEWTON_DEVICE"] = device
    written["NEWTON_DEVICE"] = device
    return written


def _assert_shas(route_path: str, taskcfg_path: str, base_path: str) -> dict:
    """E1/E9/E10: fail-closed sha pins. Returns the shas actually seen (recorded in the verdict)."""
    seen = {
        "route": _sha256(route_path),
        "task_config": _sha256(taskcfg_path),
        "base": _sha256(base_path),
    }
    if seen["route"] not in ROUTE_SHA_ACCEPT:  # E1/E11
        raise SystemExit(f"[STOP] route sha {seen['route']} not in accept-set {sorted(ROUTE_SHA_ACCEPT)}")
    if seen["task_config"] != TASKCFG_SHA:  # E9
        raise SystemExit(f"[STOP] task_config sha {seen['task_config']} != {TASKCFG_SHA}")
    if seen["base"] != BASE_SHA:  # E10
        raise SystemExit(f"[STOP] newton_skill_env_base sha {seen['base']} != {BASE_SHA}")
    return seen


def _phase_index_at_frame(frame: int, phase_transitions: list) -> int:
    """Phase id (0-12) whose window contains ``frame``; pre-phase (-1) -> 0 GRASP_HOVER (§2.3)."""
    idx = 0
    for tr in phase_transitions:
        if frame >= int(tr["frame"]):
            idx = int(tr["to_phase"])
        else:
            break
    return max(idx, 0)


def _live_seg_pos(phase_idx, cable_pos, ee_r, ee_l, grip_l_closed, seated_body_row, c2_xy):
    """§2.3 seg(t) rule re-implemented on LIVE state (SF-1: converter used recorded npz indices).

    Returns the world xyz of the active-target cable body. The SEG-INDEX selection here is a live
    argmin (nearest cable body to the relevant EE / to C2-xy); it mirrors the converter's per-phase
    seg_rule_by_phase but the recorder's exact nearest-seg metric is UNVERIFIED against this argmin
    (flagged -- a B1 obs-distribution concern; B0 ignores obs because the action is looked up).
    """
    if phase_idx <= 4:  # GRASP_HOVER..ROUTE_C1 -> nearest_seg_r
        return cable_pos[int(np.argmin(np.linalg.norm(cable_pos - ee_r, axis=1)))]
    if phase_idx <= 6:  # C1_SEAT, C1_PIN -> seated seg (schedule pinned-28 body row; E4')
        return cable_pos[seated_body_row]
    if phase_idx <= 8:  # L_HALF_UNCLAMP, R_UNCLAMP_RISE -> grip-predicated held seg
        ref = ee_l if grip_l_closed else ee_r
        return cable_pos[int(np.argmin(np.linalg.norm(cable_pos - ref, axis=1)))]
    # GUIDE_C2..C2_SETTLE -> nearest-to-C2 (2D)
    return cable_pos[int(np.argmin(np.linalg.norm(cable_pos[:, :2] - np.asarray(c2_xy), axis=1)))]


def _build_obs(ee_r, ee_l, seg_pos, next_clip, phase_idx, n_phases=13) -> np.ndarray:
    """§2.3 obs [12+n_phases]: R EE(0:3) + L EE(3:6) + seg(6:9) + next-clip(9:12) + phase one-hot n_phases(12:).

    ``n_phases`` defaults to 13 -> obs[25] (13-phase back-compat, byte-identical to the frozen v1 path);
    the B2 15-phase abs schema -> obs[27]. ``phase_idx`` (0..n_phases-1) indexes the one-hot at ``12+phase_idx``.
    """
    obs = np.zeros(12 + n_phases, dtype=np.float32)
    obs[0:3] = ee_r
    obs[3:6] = ee_l
    obs[6:9] = seg_pos
    obs[9:12] = next_clip
    obs[12 + int(phase_idx)] = 1.0
    return obs


def _policy_action(ctx, obs_vec):
    """B1 (§3) DETERMINISTIC actor-MEAN inference (CC2-7/CC5-6).

    Uses ``policy.actor(obs)`` = the raw MLP forward = EXACTLY train_bc's MSE target (bc_pretrain.py:103).
    This constructs NO Normal distribution, so it CANNOT sample -- the guaranteed mean, never
    ``policy.act()`` (which samples with ``init_noise_std=0.1`` -> ~1.5mm/axis/step noise on a 0.9mm-margin
    route). Returns (clipped action [6], per-axis |raw|>1 clamp mask [6]) -- R(0:3)+L(3:6) (E15 item-8).
    """
    torch = ctx["torch"]
    with torch.no_grad():
        ot = torch.as_tensor(obs_vec, dtype=torch.float32, device=ctx["device"]).unsqueeze(0)
        a = ctx["policy"].actor(ot)  # MEAN forward (no distribution -> cannot sample)
    raw = a.squeeze(0).detach().cpu().numpy()  # pre-clip actor output (unbounded terminal Linear)
    # E15 item-8: clipped a (byte-unchanged for relative-delta callers) + per-axis |raw|>1 mask (off-manifold diag)
    return np.clip(raw, -1.0, 1.0), (np.abs(raw) > 1.0)


def _arm_split(mujoco, mjm, mjd, f1_geoms, f2_geoms, grasp_yc):
    """Split both claw-sets into (f1_L, f1_R, f2_L, f2_R) by world-Y about the grasp centre (:3689)."""
    mujoco.mj_forward(mjm, mjd)
    gy = mjd.geom_xpos[:, 1]
    return (
        [g for g in f1_geoms if gy[g] < grasp_yc],
        [g for g in f1_geoms if gy[g] >= grasp_yc],
        [g for g in f2_geoms if gy[g] < grasp_yc],
        [g for g in f2_geoms if gy[g] >= grasp_yc],
    )


def _claw_cable_load(mujoco, mjm, mjd, claw_set, cable_geoms):
    """(claw<->cable) total NORMAL force [N] via mj_forward + mj_contactForce geom-ID filtering (:4033)."""
    mujoco.mj_forward(mjm, mjd)
    cs, cab = set(claw_set), set(cable_geoms)
    tot, f6 = 0.0, np.zeros(6)
    for ci in range(int(mjd.ncon)):
        c = mjd.contact[ci]
        if (int(c.geom1) in cs and int(c.geom2) in cab) or (int(c.geom2) in cs and int(c.geom1) in cab):
            mujoco.mj_contactForce(mjm, mjd, ci, f6)
            tot += abs(float(f6[0]))
    return tot


def _min_dist_mm(mujoco, mjm, mjd, set_a, set_b):
    """Min mj_geomDistance [mm] between two geom sets (:3606). <=0 => touching/penetrating."""
    mujoco.mj_forward(mjm, mjd)
    d = 1e9
    for a in set_a:
        for b in set_b:
            d = min(d, mujoco.mj_geomDistance(mjm, mjd, a, b, 0.05, np.zeros(6)))
    return d * 1000.0


def _discover_geoms(mujoco, mjm, mjd, x_clip, y_clip, c2x, c2y):
    """Locate the claw / cable / clip / table geom-ID sets on mj_model (mirror route :3576-3639)."""
    box = int(mujoco.mjtGeom.mjGEOM_BOX)
    cap = int(mujoco.mjtGeom.mjGEOM_CAPSULE)

    def _gn(gi):
        return (mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_GEOM, int(gi)) or "").lower()

    mujoco.mj_forward(mjm, mjd)
    f1 = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == box and "f1ext" in _gn(g)]
    f2 = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == box and "f2ext" in _gn(g)]
    cable = [g for g in range(mjm.ngeom) if int(mjm.geom_type[g]) == cap]
    clip1 = [
        g
        for g in range(mjm.ngeom)
        if int(mjm.geom_type[g]) == box
        and int(mjm.geom_bodyid[g]) == 0
        and abs(float(mjd.geom_xpos[g][0]) - x_clip) < 0.03
        and abs(float(mjd.geom_xpos[g][1]) - y_clip) < 0.03
    ]
    clip2 = [
        g
        for g in range(mjm.ngeom)
        if int(mjm.geom_type[g]) == box
        and int(mjm.geom_bodyid[g]) == 0
        and abs(float(mjd.geom_xpos[g][0]) - c2x) < 0.03
        and abs(float(mjd.geom_xpos[g][1]) - c2y) < 0.03
    ]
    return {"f1": f1, "f2": f2, "cable": cable, "clip1": clip1, "clip2": clip2}


def _pin_replay(rt, wp, mujoco, mjm, mjd, state, seated_body, geoms, groove_z_mm, out):
    """REMOVED replay pin re-fire: raises unconditionally (Rs directive 2026-07-19).

    The clip-retention pin (RS71 sec0#5's former sole kinematic exception) is superseded. A
    recording whose verdict depends on the pin is kinematic-lineage evidence and cannot be
    replayed as valid. Historical implementation: git 9d00a15276 and earlier.
    """
    del rt, wp, mujoco, mjm, mjd, state, seated_body, geoms, groove_z_mm, out
    raise RuntimeError(
        "replay pin re-fire REMOVED (Rs directive 2026-07-19 kinematic complete-removal): the "
        "sec0#5 pin exception is superseded -- clip retention must be physical contact (sec14.10)"
    )


def _run(args, out_dir) -> dict:  # noqa: C901 (linear 8-step preamble + single replay loop; mccabe cap 30)
    """Build the scene, replay the converted actions open-loop, re-implement the verdict."""
    ds = Path(args.dataset_dir)
    schedule = json.loads((ds / "schedule.json").read_text())
    cmeta = json.loads((ds / "bc_dataset_meta.json").read_text())
    rmeta = json.loads(Path(args.raw_meta).read_text())
    data = np.load(ds / "bc_dataset.npz")
    actions = data["actions"]  # [770,6] R-then-L achieved-delta / scale
    conv_obs = data["obs"]  # [n_ctrl, obs_dim] converter obs -- SF-1/6 obs-parity reference (B1-前 gate)
    scale = float(cmeta["pos_action_scale"])
    cadence = int(cmeta["cadence_physics_steps_per_rl"])
    assert cadence == PHYS_PER_CTRL, f"cadence {cadence} != {PHYS_PER_CTRL}"
    n_ctrl = actions.shape[0]
    k = min(args.max_control_steps, n_ctrl) if args.max_control_steps else n_ctrl
    smoke = k < n_ctrl

    # ---- schema detection (④ OG-gate pattern): n_phases/obs_dim from bc_dataset_abs_meta if present, else 13.
    # A 13-phase dataset-dir has NO abs_meta -> n_phases=13 -> obs[25], byte-identical to the frozen v1 path.
    # The B2 15-phase abs schema ships bc_dataset_abs_meta.json (abs_affine.shape[0]=15) -> obs[27]. ----
    _abs_meta_path = ds / "bc_dataset_abs_meta.json"
    if _abs_meta_path.exists():
        _schema_meta = json.loads(_abs_meta_path.read_text())
        n_phases = int(np.asarray(_schema_meta["abs_affine"]).shape[0])  # SAME source the OG gate uses (④)
    else:
        n_phases = 13
    obs_dim = 12 + n_phases
    print(f"[runner] SCHEMA={n_phases}-phase (obs {obs_dim}D)")

    # ---- Opt-i' (TASK B, %12 correction): frame-invariance was REFUTED (18 demos -> 6 raw phase_id signatures /
    # 3 at +-1 control-step), so a SHARED schedule misfires grip/pin by <=1 control step on some offsets. Each
    # rollout MUST use ITS OWN offset's demo schedule. Guard: the schedule-source offset (parsed from the
    # rec_<x>_<y> path of --dataset-dir, falling back to --raw-meta, then a source_offset meta field) MUST equal
    # the rollout's target offset (--rollout-offset). Fires BEFORE the scene build so a wrong-offset schedule
    # stops with zero GPU work. Absent --rollout-offset the guard is inert (13-phase/B0/B0b back-compat). ----
    schedule_source_offset = _parse_rec_offset(args.dataset_dir) or _parse_rec_offset(args.raw_meta)
    if schedule_source_offset is None:
        _src_field = cmeta.get("source_offset") or rmeta.get("source_offset")
        if _src_field is not None:
            schedule_source_offset = (round(float(_src_field[0])), round(float(_src_field[1])))
    rollout_offset = None
    if args.rollout_offset is not None:
        _ro = [x.strip() for x in str(args.rollout_offset).split(",")]
        assert len(_ro) == 2, f"--rollout-offset must be 'dx,dy' (mm); got {args.rollout_offset!r}"
        rollout_offset = (round(float(_ro[0])), round(float(_ro[1])))
    _opt_status = _opt_i_prime_check(schedule_source_offset, rollout_offset)  # loud SystemExit on offset mismatch
    if _opt_status == "ok":
        print(f"[runner] Opt-i' OK: schedule-source {tuple(schedule_source_offset)} == rollout {tuple(rollout_offset)}")
    elif _opt_status == "skip_no_source":
        print(
            f"[runner] Opt-i' WARN: no rec_<x>_<y> in --dataset-dir/--raw-meta path and no source_offset field -- "
            f"SKIPPING the schedule==rollout assert (nominal dir; rollout offset {tuple(rollout_offset)})"
        )

    # ---- §4.1-1 env-gates BEFORE import (E9: skip null, force DEMO_RECORD=0) ----
    env_gates = rmeta.get("env_gates", cmeta.get("env_gates", {}))
    device = args.device or rmeta.get("device", "cuda:0")
    gates_written = _set_env_gates(env_gates, device)
    c1_xy = [float(x) for x in cmeta["resolved_clip_c1_xy"]]
    c2_xy = [float(x) for x in cmeta["resolved_clip_c2_xy"]]

    # ---- §4.1-2 imports + sha asserts (E1/E9/E10) ----
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    envs_dir = os.path.join(scripts_dir, "..", "envs")
    for p in (scripts_dir, envs_dir):
        if p not in sys.path:
            sys.path.insert(0, p)
    route_path = os.path.join(scripts_dir, "test_newton_clip_routing.py")
    taskcfg_path = os.path.join(scripts_dir, "..", "configs", "task_config.py")
    base_path = os.path.join(envs_dir, "newton_skill_env_base.py")
    shas_seen = _assert_shas(route_path, os.path.normpath(taskcfg_path), base_path)

    import mujoco
    import newton
    import test_newton_clip_routing as rt
    import warp as wp
    from newton_skill_env_base import _wire_s6_grasp_solref, make_solver
    from test_newton_clip_routing import (
        CLIP_POSITIONS,
        FINGER_OPEN_POS,
        FRANKA_NUM_JOINTS,
        GRIPPER_DRIVER_OPEN_RAD,
        GRIPPER_JOINT_RANGE,
        GROOVE_CENTER_Z,
        JOINTS_PER_ARM,
        MUJOCO_PAD_SOLREF,
        NJMAX,
        build_fk_model,
        build_scene,
        get_ee_positions,
        physics_step,
        solve_ik_dual,
    )

    # ---- E15 (§10 fork-(iv)): --policy-absolute requires --policy; abs-decode XOR relative-delta WITHIN policy ----
    if args.policy_absolute:
        assert args.policy, "--policy-absolute (E15) requires --policy (decodes the POLICY action, not a lookup)"

    # ---- B1 (§3): optional deterministic-actor-mean policy (REUSE bc_pretrain.build_actor_critic) ----
    policy, policy_sha, torch_mod = None, None, None
    abs_affine, abs_decode_fn, abs_axis_names, dataset_abs_sha = None, None, None, None
    if args.policy:
        assert not (args.macro_ik_replay or args.absolute_waypoints), (
            "--policy (B1) uses the relative-delta loop; not combinable with --macro-ik-replay/--absolute-waypoints"
        )
        import torch
        from bc_pretrain import build_actor_critic

        policy = build_actor_critic(obs_dim, 6, (128, 128), device)  # §3: obs obs_dim (25/27) / act 6D / (128,128)
        policy.load_state_dict(torch.load(args.policy, map_location=device)["model_state_dict"])  # save fmt :143
        policy.eval()
        policy_sha, torch_mod = _sha256(args.policy), torch
        if args.policy_absolute:  # E15 fork-(iv): decode a[t] as an ABSOLUTE per-phase-affine EE target
            from route_demo_to_bc import ABS_AXIS_NAMES, _abs_decode

            abs_meta = json.loads((ds / "bc_dataset_abs_meta.json").read_text())
            assert abs_meta.get("action_repr") == "abs", (
                f"E15 STOP: bc_dataset_abs_meta.action_repr={abs_meta.get('action_repr')!r} != 'abs' (fail-closed)"
            )
            abs_affine = np.asarray(abs_meta["abs_affine"], np.float64)  # [n_phases,6,2] per-phase per-axis [lo,hi] [m]
            assert abs_affine.shape == (n_phases, 6, 2), (  # schema-aware: accepts 13 or 15 (validates the 6x2 axes)
                f"E15 STOP: abs_affine shape {abs_affine.shape} != ({n_phases}, 6, 2)"
            )
            abs_decode_fn, abs_axis_names = _abs_decode, list(ABS_AXIS_NAMES)
            dataset_abs_sha = _sha256(str(ds / "bc_dataset_abs.npz"))
            sidecar_path = Path(args.policy).with_name(Path(args.policy).stem + "_sidecar.json")
            assert sidecar_path.exists(), f"E15 STOP: policy sidecar {sidecar_path.name} missing"
            sidecar = json.loads(sidecar_path.read_text())
            assert sidecar.get("action_repr") == "abs", (
                f"E15 STOP: sidecar {sidecar_path.name} action_repr={sidecar.get('action_repr')!r} != 'abs'"
            )
        else:  # relative-delta policy: if the delta meta tags a repr it MUST be 'delta' (soft -- only if present)
            _dr = cmeta.get("action_repr")
            assert _dr in (None, "delta"), f"E15 STOP: delta meta action_repr={_dr!r} != 'delta'"

    # ---- §4.1-3 FK: home config + FINGER_OPEN_POS on +7/+8 + eval_fk (mirror :6545-6562) ----
    fk_model = build_fk_model()
    fk_state = fk_model.state()
    fk_jq = fk_state.joint_q.numpy()
    fk_jq[:] = fk_model.joint_target_pos.numpy()[:]
    for arm_offset in (0, FRANKA_NUM_JOINTS):
        fk_jq[arm_offset + 7] = FINGER_OPEN_POS
        fk_jq[arm_offset + 8] = FINGER_OPEN_POS
    fk_state.joint_q.assign(fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)

    # ---- §4.1-4 build_scene (grasp_y from env S6_ENGAGE_YC) ----
    grasp_y = float(env_gates["S6_ENGAGE_YC"])
    scene_info = build_scene(
        use_cable=True,
        fk_model=fk_model,
        fk_state=fk_state,
        solver_backend="mujoco",
        grasp_actuation=True,
        grasp_y=grasp_y,
    )
    model = scene_info["model"]
    # assert scene C1/C2 == meta resolved_clip (env_gates echo incomplete for C2 -- CC5-7b)
    scene_c1 = [float(env_gates["CLIP_X"]), float(env_gates["CLIP_Y"])]
    scene_c2 = [
        float(env_gates.get("CLIP2_X", CLIP_POSITIONS[1][0])),
        float(env_gates.get("CLIP2_Y", CLIP_POSITIONS[1][1])),
    ]
    assert np.allclose(scene_c1, c1_xy) and np.allclose(scene_c2, c2_xy), (
        f"clip drift {scene_c1}/{scene_c2} vs {c1_xy}/{c2_xy}"
    )

    # ---- §4.1-5 wire scene_info; §4.1-5b state = model.state() ----
    scene_info["fk_model"] = fk_model
    scene_info["fk_state"] = fk_state
    vbd_control = model.control()
    scene_info["vbd_control"] = vbd_control
    model.rigid_contact_max = NJMAX
    contacts = model.contacts()
    state = model.state()
    # BUG-2 fix (smoke-caught by COORD): the route's grasp fn sets a specific grasp-approach SEED config (NOT
    # main()'s plain home/joint_target_pos config) right before its settle (test_newton_clip_routing.py:3839-3847);
    # the demo's frame-0 arm == this seed (EE ~[0.267,0.202,1.560]). The runner mirrored main()'s home init but
    # MISSED the route-fn seed, so the physics arm started ~1.1m off (EE X=-0.817) and the open-loop replay
    # (tgt = live_ee + demo_delta) anchored to a wrong origin => a PERSISTENT metre of EE drift-from-demo
    # (per-step tracking stays <1mm; absolute pose is a metre off -> grasp/seat would all fail). Replicate the
    # seed, eval_fk, then sync the physics body_q to it (update_kinematic_bodies :1725) before obs[0].
    _seed_l = [3.194257, -1.979768, 1.6, -1.853054, 2.0, -1.518132]
    _seed_r = [-0.052664, -1.161825, -1.6, -1.288538, -2.0, -1.62346]
    _fk_jq = fk_state.joint_q.numpy()
    _fk_jq[0 : len(_seed_l)] = _seed_l
    _fk_jq[JOINTS_PER_ARM : JOINTS_PER_ARM + len(_seed_r)] = _seed_r
    for _j in GRIPPER_JOINT_RANGE:
        _fk_jq[_j] = 0.0
        _fk_jq[JOINTS_PER_ARM + _j] = 0.0
    fk_state.joint_q.assign(_fk_jq)
    newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
    rt.update_kinematic_bodies(state, fk_state, scene_info["robot_body_count"])

    # ---- §4.1-6 gripper_dynamic (else physics_step FK-overwrites the gripper coords => inert servo) ----
    scene_info["gripper_dynamic"] = True
    assert scene_info["gripper_dynamic"] is True, "B0 DoD: gripper_dynamic must be True before the loop"

    # ---- §4.1-7 make_solver + _wire_s6_grasp_solref + solref parity readback ----
    solver = make_solver(model, backend="mujoco", enable_cable_contacts=True)
    _wire_s6_grasp_solref(solver, scene_info)  # runs its own I11 solref readback asserts internally
    mjm, mjd = solver.mj_model, solver.mj_data
    pad_solref_rb = [float(x) for x in np.asarray(mjm.geom_solref[_first_pad_geom(mujoco, mjm)]).ravel()[:2]]
    assert np.allclose(pad_solref_rb, list(MUJOCO_PAD_SOLREF)), (
        f"solref parity {pad_solref_rb} != {list(MUJOCO_PAD_SOLREF)}"
    )

    # ---- §4.1-8 initial open servo + perclip_pin_n assert ----
    driver_joints = scene_info["driver_joints"]  # [6,10,20,24] = L drivers + R drivers
    l_drv, r_drv = driver_joints[:2], driver_joints[2:]
    rt._set_gripper_target(vbd_control, driver_joints, GRIPPER_DRIVER_OPEN_RAD)
    assert scene_info.get("perclip_pin_n", 0) > 0, "PERCLIP_PIN=1 must pre-allocate eqs before the loop"

    # ---- geom sets + fixed-schedule replay setup ----
    geoms = _discover_geoms(mujoco, mjm, mjd, scene_c1[0], scene_c1[1], scene_c2[0], scene_c2[1])
    # BUG-1: the _arm_split centre is NOT 0.0 -- caveat-a re-centres GRASP_YC on the SETTLED cable
    # (route :3858-3862). Deferred to None; computed inside the loop at t==0 (the pre-grasp settle).
    groove_z_mm = (GROOVE_CENTER_Z + float(env_gates["CLIP_FLOAT_Z"])) * 1e3
    z_top = float(cmeta["next_clip_z_top"])
    cable_bodies = scene_info["cable_bodies"]
    seated_seg = int(schedule["pin_event"]["seated_seg"])  # E4': B0 uses the scheduled seg
    seated_body = int(cable_bodies[seated_seg])
    finger_coords = set(GRIPPER_JOINT_RANGE) | {JOINTS_PER_ARM + j for j in GRIPPER_JOINT_RANGE}  # :1991
    fk_coord_count = fk_model.joint_coord_count
    lm = schedule["verdict_landmarks"]
    hov_r = schedule["ee_tgt_pos_r_at_c2_hover_end"]  # reach target (:4470-4471)

    # B0a (spec E13): absolute-waypoint targets = seeded origin + cumsum(actions*scale). Consumes ONLY the
    # converter output; by §2.6 recon this reconstructs the demo's ABSOLUTE EE waypoints, breaking the
    # open-loop landing-error accumulation chain (B0-(i)'s ~14mm->23mm-cable-miss failure). state here is the
    # post-seed-init pose (BUG-2 fix) => get_ee_positions == the demo frame-0 origin. Pipeline-validation leg.
    _o_l, _o_r = get_ee_positions(state, scene_info)
    cum_r = np.asarray(_o_r, dtype=np.float64) + np.cumsum(actions[:, 0:3].astype(np.float64) * scale, axis=0)
    cum_l = np.asarray(_o_l, dtype=np.float64) + np.cumsum(actions[:, 3:6].astype(np.float64) * scale, axis=0)

    ctx = {
        "rt": rt,
        "wp": wp,
        "newton": newton,
        "mujoco": mujoco,
        "model": model,
        "solver": solver,
        "contacts": contacts,
        "scene_info": scene_info,
        "fk_state": fk_state,
        "fk_model": fk_model,
        "mjm": mjm,
        "mjd": mjd,
        "geoms": geoms,
        "grasp_yc": None,  # BUG-1: set at loop t==0 (caveat-a, route :3858-3862)
        "grasp_y": grasp_y,  # S6_ENGAGE_YC (=0.15) -- the caveat-a re-centre anchor
        "groove_z_mm": groove_z_mm,
        "seated_body": seated_body,
        "seated_seg": seated_seg,
        "cable_bodies": cable_bodies,
        "finger_coords": finger_coords,
        "fk_coord_count": fk_coord_count,
        "physics_step": physics_step,
        "solve_ik_dual": solve_ik_dual,
        "get_ee_positions": get_ee_positions,
        "l_drv": l_drv,
        "r_drv": r_drv,
        "z_top": z_top,
        "c1_xy": c1_xy,
        "c2_xy": c2_xy,
        "hov_r": hov_r,
        "lm": lm,
        "scale": scale,
        "absolute_waypoints": args.absolute_waypoints,  # B0a (E13)
        "cum_r": cum_r,
        "cum_l": cum_l,
        "policy": policy,  # B1 (§3): deterministic actor-mean, or None
        "torch": torch_mod,
        "device": device,
        "policy_path": args.policy,
        "policy_sha256": policy_sha,
        "policy_absolute": bool(args.policy_absolute),  # E15 item-6
        "abs_affine": abs_affine,  # E15 item-6: [n_phases,6,2] per-phase per-axis [lo,hi], or None
        "_abs_decode": abs_decode_fn,  # E15: route_demo_to_bc._abs_decode (threaded like solve_ik_dual), or None
        "abs_axis_names": abs_axis_names,  # E15: ["Rx".."Lz"] for the per-axis clamp verdict, or None
        "dataset_abs_sha256": dataset_abs_sha,  # E15 item-12: sha of bc_dataset_abs.npz when abs, else None
        "n_phases": n_phases,  # TASK A: schema (13 back-compat / 15 B2) -> obs one-hot width + affine phase count
        "obs_dim": obs_dim,  # TASK A: 12 + n_phases (25 / 27)
        "rollout_offset": rollout_offset,  # TASK B (Opt-i'): the offset THIS rollout targets, or None
        "schedule_source_offset": schedule_source_offset,  # TASK B (Opt-i'): offset parsed from the rec_ path, or None
    }
    # §4.7/E8 offscreen video leg (behind --record-video; frames captured in-loop, mp4 stitched post-hoc).
    ctx["_renderer"] = mujoco.Renderer(mjm, height=480, width=640) if args.record_video else None
    ctx["_frames"] = []
    ctx["_capture_every"] = 50
    ctx["macro"] = bool(args.macro_ik_replay)  # B0b (E14): route ik_move_both per macro-leg
    caps: dict = {"partition": None, "reach": None, "grip": None}
    seat_state: dict = {}
    ik_fail_steps: list[int] = []
    grip_state = {"L": GRIPPER_DRIVER_OPEN_RAD, "R": GRIPPER_DRIVER_OPEN_RAD}
    obs_series, ee_err_series = [], []
    # E15 accumulators (items 8/9/11) threaded via ctx (like solve_ik_dual/get_ee_positions); empty for macro mode
    ctx["clamp_counts"] = np.zeros(6, int)  # item-8: per-axis |raw|>1 counts
    ctx["guard2_fires"], ctx["tgt_ee_series"], ctx["ik_resid_series"] = [], [], []  # items 9/9/11

    if args.macro_ik_replay:  # B0b (E14): route's OWN ik_move_both per macro-leg -- validate pin/C1/C2/verdict legs
        macro = json.loads((ds / "macro_schedule.json").read_text())
        total = _macro_ik_loop(ctx, state, macro, caps, seat_state, ik_fail_steps)  # variable frame count; NO ==7700
    else:
        total = _control_loop(
            ctx, state, actions, k, schedule, caps, seat_state, ik_fail_steps, grip_state, obs_series, ee_err_series
        )
        if not smoke:
            assert total == n_ctrl * PHYS_PER_CTRL, f"E2: total_physics_frames {total} != {n_ctrl * PHYS_PER_CTRL}"

    verdict = _finalize_verdict(
        ctx,
        caps,
        seat_state,
        ik_fail_steps,
        shas_seen,
        gates_written,
        obs_series,
        ee_err_series,
        smoke,
        total,
        n_ctrl,
        conv_obs,
        out_dir,
    )
    video_path = _video_finalize(ctx, out_dir)  # post-hoc mp4 (only when --record-video)
    if video_path:
        verdict["video_path"] = video_path
    return verdict


def _first_pad_geom(mujoco, mjm) -> int:
    """First pad geom id (for the solref parity readback)."""
    for g in range(mjm.ngeom):
        gname = (mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_GEOM, g) or "").lower()
        bname = (mujoco.mj_id2name(mjm, mujoco.mjtObj.mjOBJ_BODY, int(mjm.geom_bodyid[g])) or "").lower()
        if "pad" in gname + bname:
            return g
    raise SystemExit("[STOP] no pad geom for solref parity readback")


def _control_loop(
    ctx, state, actions, k, schedule, caps, seat_state, ik_fail_steps, grip_state, obs_series, ee_err_series
) -> int:  # noqa: C901
    """§4.2 replay loop x K control steps: build obs, apply action, sub-interpolate 10 frames,
    fire scheduled events at exact physics-frame indices (E2), capture verdict landmarks."""
    rt, wp, newton, mujoco = ctx["rt"], ctx["wp"], ctx["newton"], ctx["mujoco"]
    fk_state, fk_model, phys = ctx["fk_state"], ctx["fk_model"], ctx["physics_step"]
    scene_info, model, solver, contacts = ctx["scene_info"], ctx["model"], ctx["solver"], ctx["contacts"]
    finger_coords, fk_cc, scale = ctx["finger_coords"], ctx["fk_coord_count"], ctx["scale"]
    cable_bodies, lm = ctx["cable_bodies"], ctx["lm"]
    # E15: bind ctx accumulators (same objects -> += / .append mutate in place, ctx reflects them)
    clamp_counts = ctx["clamp_counts"]
    guard2_fires, tgt_ee_series, ik_resid_series = ctx["guard2_fires"], ctx["tgt_ee_series"], ctx["ik_resid_series"]
    abs_decode = ctx.get("_abs_decode")
    # index events by physics frame
    grip_by_frame: dict = {}
    for ev in schedule["grip_events"]:
        grip_by_frame.setdefault(int(ev["frame"]), []).append(ev)
    pin_frame = int(schedule["pin_event"]["frame"])
    total = 0
    for t in range(k):
        ee_l, ee_r = ctx["get_ee_positions"](state, scene_info)
        cable_pos = state.body_q.numpy()[cable_bodies][:, :3]
        phase_idx = _phase_index_at_frame(t * PHYS_PER_CTRL, schedule["phase_transitions"])
        seg = _live_seg_pos(
            phase_idx,
            cable_pos,
            ee_r,
            ee_l,
            grip_state["L"] >= GRIP_CLOSED_RAD,
            ctx["seated_seg"],
            ctx["c2_xy"],
        )
        next_clip = np.array([*(ctx["c1_xy"] if phase_idx <= 6 else ctx["c2_xy"]), ctx["z_top"]], dtype=np.float32)
        obs_vec = _build_obs(ee_r, ee_l, seg, next_clip, phase_idx, ctx["n_phases"])  # TASK A: schema-aware width
        obs_series.append(obs_vec)
        # §4.2-2/3 action -> EE targets (R=0:3, L=3:6)
        if ctx.get("policy") is not None:  # B1 (§3): DETERMINISTIC actor-mean on the LIVE obs (obs IS consumed now)
            a, clamp_mask = _policy_action(ctx, obs_vec)
        else:  # B0-(i)/B0a: converted-demo action lookup (SAME code path a policy uses)
            a = np.clip(actions[t], -1.0, 1.0)
            clamp_mask = np.abs(actions[t]) > 1.0  # E15 item-8: lookup labels are pre-clipped (mask ~all-False)
        clamp_counts += clamp_mask.astype(int)  # E15 item-8: per-axis off-manifold accumulation
        if ctx.get("policy_absolute"):  # E15 item-7 fork-(iv): decode a as an ABSOLUTE per-phase-affine target (TOP)
            tgt6 = abs_decode(a[None, :], np.array([int(phase_idx)]), ctx["abs_affine"])[0]  # [6] abs EE target
            tgt_r, tgt_l = np.array(tgt6[0:3], float), np.array(tgt6[3:6], float)
        elif ctx.get("absolute_waypoints"):  # B0a (E13): absolute demo waypoints -> no live-anchor accumulation
            tgt_r, tgt_l = ctx["cum_r"][t], ctx["cum_l"][t]
        else:  # B0-(i)/B1: live-anchored relative delta
            tgt_r = np.asarray(ee_r) + a[0:3] * scale
            tgt_l = np.asarray(ee_l) + a[3:6] * scale
        if ctx.get("policy_absolute"):  # E15 items 9/10: t=0 canary + guard-2 v2 (abs-decode path only)
            if t == 0:  # item-10 canary: seeded start ee vs abs decode must agree within 30mm per arm
                for _arm, _ee, _tg in (("R", ee_r, tgt_r), ("L", ee_l, tgt_l)):
                    _c0 = float(np.linalg.norm(np.asarray(_tg, float) - np.asarray(_ee, float)) * 1e3)
                    if _c0 >= 30.0:
                        raise SystemExit(f"[STOP] E15 t=0 canary {_arm}: ||decode(a0)-ee||={_c0:.2f}mm>=30mm (seed)")
            _te = {"step": t, "phase": int(phase_idx)}  # item-9: per-arm PRE-clamp ||tgt-ee|| (P1 attribution)
            for _arm, _ee, _tg in (("R", ee_r, tgt_r), ("L", ee_l, tgt_l)):
                _dv = np.asarray(_tg, float) - np.asarray(_ee, float)
                _mag = float(np.linalg.norm(_dv))
                _te[_arm + "_mm"] = round(_mag * 1e3, 3)
                if _mag > GUARD2_M:  # guard-2 v2: direction-preserving 15mm magnitude rate-limit
                    _tg[:] = np.asarray(_ee, float) + _dv * (GUARD2_M / _mag)
                    guard2_fires.append(
                        {"step": t, "phase": int(phase_idx), "arm": _arm, "mag_mm": round(_mag * 1e3, 2)}
                    )
            tgt_ee_series.append(_te)
        jq_start = fk_state.joint_q.numpy().copy()
        jq_end, ik_cost = ctx["solve_ik_dual"](scene_info, tuple(tgt_l), tuple(tgt_r))
        ik_resid_series.append(float(ik_cost))  # E15 item-11: 2nd return = combined IK objective cost (test:1908)
        ik_ok = not np.any(np.isnan(jq_end))  # E8: non-convergence -> log + continue + tag (route returns no-raise)
        if not ik_ok:
            ik_fail_steps.append(t)
        for fi in range(PHYS_PER_CTRL):
            f = t * PHYS_PER_CTRL + fi
            for ev in grip_by_frame.get(f, []):  # E2: grip fires BEFORE this frame's physics_step
                drv = ctx["l_drv"] if ev["arm"] == "L" else ctx["r_drv"]  # E6: map by NAMED arm, not positional
                rt._set_gripper_target(scene_info["vbd_control"], drv, float(ev["target_rad"]))
                grip_state[ev["arm"]] = float(ev["target_rad"])
            if f == pin_frame:  # E2/§4.5: seat-verify then fire (no injected settle frames)
                _pin_replay(
                    rt,
                    wp,
                    mujoco,
                    ctx["mjm"],
                    ctx["mjd"],
                    state,
                    ctx["seated_body"],
                    ctx["geoms"],
                    ctx["groove_z_mm"],
                    seat_state,
                )
            if ik_ok:  # §4.2-4 sub-interpolate the joint delta across 10 frames, gripper coords preserved
                frac = (fi + 1) / PHYS_PER_CTRL
                jq_interp = jq_start.copy()
                for d in range(fk_cc):
                    if d not in finger_coords:
                        jq_interp[d] = jq_start[d] + (jq_end[d] - jq_start[d]) * frac
                fk_state.joint_q.assign(jq_interp)
                newton.eval_fk(fk_model, fk_state.joint_q, fk_state.joint_qd, fk_state)
            state = phys(model, state, solver, contacts, scene_info)
            total += 1
            _capture_landmark(ctx, state, f, lm, caps)
            if ctx["_renderer"] is not None and f % ctx["_capture_every"] == 0:
                _video_capture(ctx)
        # §9-B0 per-step tracking error (achieved EE vs the commanded target this step)
        pl, pr = ctx["get_ee_positions"](state, scene_info)
        ee_err_series.append(
            [
                float(np.linalg.norm(np.asarray(pr) - tgt_r) * 1e3),
                float(np.linalg.norm(np.asarray(pl) - tgt_l) * 1e3),
            ]
        )
        # BUG-1 caveat-a: re-centre GRASP_YC on the SETTLED cable (route :3858-3862; t==0 = the pre-grasp settle)
        if t == 0:
            wp.synchronize()
            cy_all = state.body_q.numpy()[cable_bodies, 1]
            near = cy_all[np.abs(cy_all - ctx["grasp_y"]) < 0.10]  # grasp-region cable bodies (|Y - grasp_at| < 100mm)
            grasp_yc = float(np.mean(near)) if near.size else ctx["grasp_y"]
            assert abs(grasp_yc - 0.150) < 0.010, (
                f"BUG-1: GRASP_YC {grasp_yc * 1e3:.2f}mm != ~150mm (partition corrupt)"
            )
            ctx["grasp_yc"] = grasp_yc  # the C1_SEAT-landmark _arm_split (frame 2084 >> 10) reads this
            print(f"  [RUNNER] caveat-a GRASP_YC={grasp_yc * 1e3:+.2f}mm (settled-cable-centre; arms +-44mm = 88 span)")
    ctx["_final_state"] = state
    return total


class _LegVideoHook:
    """B0b: ik_move_both calls ``recorder.capture(state)`` per internal physics frame (route :2009-2012).

    Counts frames (exact ``total_physics_frames``) and renders every ``_capture_every`` when --record-video.
    """

    def __init__(self, ctx):
        self.ctx, self.n = ctx, 0

    def capture(self, state):
        if self.ctx["_renderer"] is not None and self.n % self.ctx["_capture_every"] == 0:
            _video_capture(self.ctx)
        self.n += 1


def _macro_ik_loop(ctx, state, macro, caps, seat_state, ik_fail_steps) -> int:  # noqa: C901
    """B0b (E14): drive each macro-leg with the route's OWN ik_move_both (byte-identical apply) so the
    pin-FIRE / C1-held / C2-seat / §4.4 FULL-verdict legs get exercised. NOT policy semantics -- purpose-
    scoped to event+verdict-mechanism validation. Per-leg converge_mm/speed_factor were NOT recorded ->
    ik_move_both defaults used (noted in verdict)."""
    rt, wp, mujoco = ctx["rt"], ctx["wp"], ctx["mujoco"]
    scene_info, model, solver, contacts = ctx["scene_info"], ctx["model"], ctx["solver"], ctx["contacts"]
    lm = ctx["lm"]
    # §4.3: replay uses PLAIN solve_ik_dual (no monkeypatch); the schedule quat-default assert guarantees it.
    assert rt.solve_ik_dual is ctx["solve_ik_dual"], "§4.3: solve_ik_dual is monkeypatched (unexpected in B0b)"
    grip_by_leg: dict = {}
    for ev in macro["event_leg_map"]["grip_events"]:
        grip_by_leg.setdefault(int(ev["leg_idx"]), []).append(ev)
    pin_leg = int(macro["event_leg_map"]["pin_event"]["leg_idx"])
    pin_frame = int(macro["event_leg_map"]["pin_event"]["frame"])
    lm_leg = {k: int(v["leg_idx"]) for k, v in macro["landmark_leg_map"].items()}
    hook = _LegVideoHook(ctx)  # frame count (+ video via route hook :2009-2012)
    scene_info["recorder"] = hook
    leg_ok: dict = {}

    def _fire(ev):  # E6 named-arm gripper servo through vbd_control (what physics_step consumes)
        drv = ctx["l_drv"] if ev["arm"] == "L" else ctx["r_drv"]
        rt._set_gripper_target(scene_info["vbd_control"], drv, float(ev["target_rad"]))

    for leg in macro["legs"]:
        li = int(leg["leg_idx"])
        is_pin_leg = li == pin_leg
        grips = grip_by_leg.get(li, [])
        # STOP-FLAG (macro granularity): the pin leg ALSO carries POST-pin grip events (leg 35 = the L
        # half-unclamp ramp 2598-2654 + R->0 2694, all frame > 2544=pin). E2 order => pre-pin grips fire at
        # leg start; AT/AFTER-pin grips fire AFTER the pin so it captures the CLOSED-gripper seat (else the
        # L half-unclamp would shift the cable off the <=0.5mm seat -> false unseated-pin, defeating B0b).
        for ev in grips:
            if not (is_pin_leg and int(ev["frame"]) >= pin_frame):
                _fire(ev)
        state, ok = rt.ik_move_both(
            model, state, scene_info, solver, contacts, tuple(leg["target_l"]), tuple(leg["target_r"])
        )
        leg_ok[li] = bool(ok)
        if not ok:
            ik_fail_steps.append(li)  # NOTE: macro mode -> ik_fail_steps holds LEG indices
        if is_pin_leg:  # §4.5 seat-verify FIRST -> fire iff seated (the leg we most want to VALIDATE)
            _pin_replay(
                rt,
                wp,
                mujoco,
                ctx["mjm"],
                ctx["mjd"],
                state,
                ctx["seated_body"],
                ctx["geoms"],
                ctx["groove_z_mm"],
                seat_state,
            )
            for ev in grips:  # the pin leg's post-pin grips (L half-unclamp) AFTER the seat is pinned
                if int(ev["frame"]) >= pin_frame:
                    _fire(ev)
        if li == 0:  # BUG-1 caveat-a: GRASP_YC after the pre-grasp settle leg (route :3858-3862)
            wp.synchronize()
            cy = state.body_q.numpy()[ctx["cable_bodies"], 1]
            near = cy[np.abs(cy - ctx["grasp_y"]) < 0.10]
            gyc = float(np.mean(near)) if near.size else ctx["grasp_y"]
            assert abs(gyc - 0.150) < 0.010, f"BUG-1: GRASP_YC {gyc * 1e3:.2f}mm != ~150mm (partition corrupt)"
            ctx["grasp_yc"] = gyc
        for key in ("c1_seat_landmark_frame", "c2_hover_end_frame", "post_close_settle_end_frame"):
            if lm_leg.get(key) == li:  # capture the landmark on the leg that contains its frame (leg-end state)
                _capture_landmark(ctx, state, int(lm[key]), lm, caps)
    ctx["_final_state"] = state
    ctx["_leg_ok"] = leg_ok
    ctx["_n_legs"] = len(macro["legs"])
    return hook.n  # actual physics frames driven by ik_move_both (NOT 7700)


def _capture_landmark(ctx, state, frame, lm, caps):
    """Capture the verdict inputs at the schedule landmark frames (§4.4)."""
    mujoco, mjm, mjd = ctx["mujoco"], ctx["mjm"], ctx["mjd"]
    if frame == int(lm["c1_seat_landmark_frame"]) and caps["partition"] is None:
        caps["partition"] = _arm_split(mujoco, mjm, mjd, ctx["geoms"]["f1"], ctx["geoms"]["f2"], ctx["grasp_yc"])
    if frame == int(lm["c2_hover_end_frame"]) and caps["reach"] is None:
        _pl, pr = ctx["get_ee_positions"](state, ctx["scene_info"])
        hov = ctx["hov_r"]
        reach = float(np.hypot(hov[0] - float(pr[0]), hov[1] - float(pr[1])) * 1e3)
        caps["reach"] = {
            "reach_mm": round(reach, 1),
            "at_88": bool(reach <= REACH_88_MM),
            "r_ee_xy": [round(float(pr[0]), 4), round(float(pr[1]), 4)],
        }
    if frame == int(lm["post_close_settle_end_frame"]) and caps["grip"] is None and caps["partition"] is not None:
        f1l, f1r, f2l, f2r = caps["partition"]
        nlg = _claw_cable_load(mujoco, mjm, mjd, f1l + f2l, ctx["geoms"]["cable"])
        nrg = _claw_cable_load(mujoco, mjm, mjd, f1r + f2r, ctx["geoms"]["cable"])
        pl, pr = ctx["get_ee_positions"](state, ctx["scene_info"])
        span = float(np.linalg.norm(np.asarray(pl) - np.asarray(pr)) * 1e3)
        caps["grip"] = {
            "l_grip_N": round(nlg, 2),
            "r_grip_N": round(nrg, 2),
            "l_grips": bool(nlg > GRIP_N_MIN),
            "r_grips": bool(nrg > GRIP_N_MIN),
            "achieved_3d_span_mm": round(span, 1),
        }


def _finalize_verdict(
    ctx,
    caps,
    seat_state,
    ik_fail_steps,
    shas_seen,
    gates_written,
    obs_series,
    ee_err_series,
    smoke,
    total,
    n_ctrl,
    conv_obs,
    out_dir,
) -> dict:
    """§4.4 assemble runner_verdict.json (mirror _c2_regrasp_rec fields; categories set-based,
    numerics reported). C2 seat computed at loop end (c2_settle_end_frame 7706 is in the zero-motion
    tail beyond the 7700-frame stream -- captured on the final state)."""
    mujoco, mjm, mjd, wp = ctx["mujoco"], ctx["mjm"], ctx["mjd"], ctx["wp"]
    state = ctx.get("_final_state")
    is_macro = bool(ctx.get("macro"))  # B0b (E14)
    is_policy = ctx.get("policy") is not None  # B1 (§3)
    # C2 seat (mirror route :4578-4590): cable<->C2 touch + near-C2 cable z ~ groove
    wp.synchronize()
    cab_c2_mm = _min_dist_mm(mujoco, mjm, mjd, ctx["geoms"]["cable"], ctx["geoms"]["clip2"])
    cbq = state.body_q.numpy()[ctx["cable_bodies"]]
    nk = int(np.argmin(np.abs(cbq[:, 1] - ctx["c2_xy"][1])))
    z_c2_mm = float(cbq[nk][2]) * 1e3
    c2_settled = bool(cab_c2_mm <= SEAT_DIST_MM and abs(z_c2_mm - ctx["groove_z_mm"]) <= SEAT_Z_TOL_MM)

    reach = caps["reach"] or {}
    grip = caps["grip"] or {}
    at_88 = bool(reach.get("at_88", False))
    r_grips = bool(grip.get("r_grips", False))
    l_grips = bool(grip.get("l_grips", False))
    if not at_88:  # 4-way split (mirror :4507-4515)
        verdict = "BLOCKED_REACH_WALL"
    elif not r_grips:
        verdict = "R_MISS_AT_88"
    elif l_grips:
        verdict = "SUCCESS_DUAL_LOADED_AT_88"
    else:
        verdict = "SUCCESS_R_GRIP_L_CAGE_AT_88"
    regrasp_ok = bool(at_88 and r_grips)

    fired = seat_state.get("fired", False)
    c1_held = bool(seat_state.get("seated", False))  # C1-held = FULL multi-criterion seat incl z (§4.4/§4.5)
    if ik_fail_steps:
        failure_mode = "ik_failure"
    elif not fired:
        failure_mode = "unseated_pin"  # §4.5: pin did not fire => rollout INVALID
    elif smoke:
        failure_mode = "smoke_partial"
    else:
        failure_mode = "none"

    # c2_regrasp_rec mirror: measured-from-state fields populated; route-CONTROL-derived fields are
    # NOT recoverable from an open-loop joint replay (SF-2) -> null with provenance.
    tilt_sign_gate = os.environ.get("C2_TILT_SIGN")
    regrasp_rec = {
        "r_target_x": None,
        "r_target_y": None,
        "r_target_z": None,  # SF-2 route-control-derived
        "r_old_fixed_x": round(float(ctx["c2_xy"][0]), 3),
        "r_x_offset_from_fixed_mm": None,  # SF-2 needs r_target_x
        "picked_body_dy_from_lane_mm": None,  # SF-2 route cable-body selection
        "target_y_span_mm": 88.0,  # INVARIANT#2 constant
        "achieved_3d_span_mm": grip.get("achieved_3d_span_mm"),
        "tilt_theta_deg": None,  # SF-2 route tilt computation
        "tilt_sign": float(tilt_sign_gate) if tilt_sign_gate is not None else 0.0,
        "r_reach_resid_mm": reach.get("reach_mm"),
        "reached_88mm_lane": at_88,
        "l_grip_N": grip.get("l_grip_N"),
        "r_grip_N": grip.get("r_grip_N"),
        "l_grips": l_grips,
        "r_grips": r_grips,
        "regrasp_verdict": verdict,
        "regrasp_ok": regrasp_ok,
    }

    # SF-1/6 (%12-APPROVED as B1-前 measurement): obs-parity vs the converter obs + raw obs_series dump.
    runner_obs = np.asarray(obs_series, dtype=np.float32) if obs_series else np.zeros((0, ctx["obs_dim"]), np.float32)
    np.save(Path(out_dir) / "obs_series.npy", runner_obs)  # raw runner obs for audit
    if smoke or runner_obs.shape[0] != conv_obs.shape[0]:
        obs_parity = {
            "skipped": True,
            "note": (
                "obs_parity: skipped (B0b macro -- validates events+verdict, not the obs stream)"
                if is_macro
                else "obs_parity: skipped (smoke, partial)"
            ),
        }
    else:
        dif = np.abs(runner_obs - conv_obs.astype(np.float32))
        obs_parity = {
            "per_dim_max": [round(float(x), 6) for x in dif.max(axis=0)],
            "per_dim_mean": [round(float(x), 6) for x in dif.mean(axis=0)],
            "overall_max": round(float(dif.max()), 6),
            "note": "B0 obs unused (action=lookup); B1-前 obs-distribution parity gate (SF-1/6)",
        }

    # E15 (§10) provenance + off-manifold + rate-limit + IK-residual diagnostics (threaded via ctx)
    _self_p = os.path.abspath(__file__)
    _conv_p = os.path.join(os.path.dirname(_self_p), "route_demo_to_bc.py")
    _te_series = ctx.get("tgt_ee_series") or []
    _ir_series = ctx.get("ik_resid_series") or []
    _cc = ctx.get("clamp_counts")
    e15 = {
        "runner_self_sha256": _sha256(_self_p),
        "converter_sha256": _sha256(_conv_p) if os.path.exists(_conv_p) else None,
        "dataset_abs_sha256": ctx.get("dataset_abs_sha256"),
        "gl_backend": os.environ.get("MUJOCO_GL", "<unset>"),
        "display": os.environ.get("DISPLAY", "<unset>"),
        "per_axis_clamp_counts": (
            dict(zip(ctx["abs_axis_names"], _cc.tolist()))
            if (ctx.get("policy_absolute") and _cc is not None and ctx.get("abs_axis_names"))
            else None
        ),
        "guard2_fires": {"count": len(ctx.get("guard2_fires") or []), "entries": ctx.get("guard2_fires") or []},
        "tgt_ee_series_summary": {
            arm: {
                "max_mm": round(max((e[f"{arm}_mm"] for e in _te_series), default=0.0), 3),
                "mean_mm": round(float(np.mean([e[f"{arm}_mm"] for e in _te_series])) if _te_series else 0.0, 3),
            }
            for arm in ("R", "L")
        },
        "ik_resid_series_summary": {
            "max": round(max(_ir_series, default=0.0), 6),
            "mean": round(float(np.mean(_ir_series)) if _ir_series else 0.0, 6),
        },
    }

    return {
        "source": (
            "b1_policy_rollout" if is_policy else ("b0b_macro_ik_replay" if is_macro else "b0_open_loop_replay")
        ),
        "inference_mode": ("actor_mean" if is_policy else ("route_ik_move_both" if is_macro else "dataset_lookup")),
        "policy_path": ctx.get("policy_path"),
        "policy_sha256": ctx.get("policy_sha256"),
        "sub_interp_mode": "route_ik_move_both(B0b)" if is_macro else "joint_delta_lerp_10frame",
        "waypoint_mode": (
            "macro_ik(B0b,E14)"
            if is_macro
            else (
                "absolute_policy(B1p,E15)"
                if (is_policy and ctx.get("policy_absolute"))
                else (
                    "absolute_cumsum(B0a,E13)"
                    if ctx.get("absolute_waypoints")
                    else ("relative_delta(B1-policy)" if is_policy else "relative_delta(B0-i)")
                )
            )
        ),
        "seat_state_at_pin_fire": seat_state,
        "shas_seen": shas_seen,
        "env_gates_written": gates_written,
        "schema": {"n_phases": ctx.get("n_phases"), "obs_dim": ctx.get("obs_dim")},  # TASK A: detected obs schema
        "opt_i_prime": {  # TASK B: per-offset schedule guard provenance (frame-invariance REFUTED)
            "rollout_offset": list(ctx["rollout_offset"]) if ctx.get("rollout_offset") is not None else None,
            "schedule_source_offset": (
                list(ctx["schedule_source_offset"]) if ctx.get("schedule_source_offset") is not None else None
            ),
            "assert_active": ctx.get("rollout_offset") is not None and ctx.get("schedule_source_offset") is not None,
        },
        "regrasp": regrasp_rec,
        "c2_settle": {
            "cable_c2_released_mm": round(cab_c2_mm, 3),
            "near_c2_cable_z_mm": round(z_c2_mm, 1),
            "groove_z_mm": round(ctx["groove_z_mm"], 1),
            "settled_in_notch": c2_settled,
        },
        "c1_held": c1_held,
        "c1_seat_criterion": (
            "cable<->clip1 <= 0.5mm AND |seat_z - groove_z(829mm)| <= 3.0mm "
            "(borrowed from route _c2_settled :4587; %12-APPROVED SF-3)"
        ),
        "grasp_yc_mm": round(ctx["grasp_yc"] * 1e3, 2) if ctx.get("grasp_yc") is not None else None,
        "obs_parity": obs_parity,
        "categories": {
            "regrasp_ok": regrasp_ok,
            "verdict": verdict,
            "verdict_is_success": verdict in SUCCESS_VERDICTS,
            "c2_settled": c2_settled,
            "c1_held": c1_held,
        },
        "tracking": {
            "n_control_steps": len(ee_err_series),
            "max_ee_err_mm": [round(max((e[i] for e in ee_err_series), default=0.0), 2) for i in (0, 1)],
            "terminal_ee_err_mm": ee_err_series[-1] if ee_err_series else None,
        },
        "ik_failure_steps": ik_fail_steps,  # macro mode: LEG indices (not control-step indices)
        "total_physics_frames": total,  # macro mode: actual ik_move_both frame count (NOT 7700)
        "smoke": smoke,
        "failure_mode": failure_mode,
        "macro": (
            {
                "n_legs": ctx.get("_n_legs"),
                "leg_success": ctx.get("_leg_ok"),
                "note": "B0b (E14): ik_move_both per leg; per-leg converge/speed NOT recorded -> defaults used",
            }
            if is_macro
            else None
        ),
        **e15,  # E15 item-12: provenance + gl/display + clamp/guard2/tgt-ee/ik-resid diag
    }


def _video_capture(ctx):
    """§4.7/E8: capture one offscreen frame (mirror route _cap: mj_forward + Renderer.update_scene+render)."""
    ctx["mujoco"].mj_forward(ctx["mjm"], ctx["mjd"])
    ctx["_renderer"].update_scene(ctx["mjd"])
    ctx["_frames"].append(ctx["_renderer"].render().copy())


def _video_finalize(ctx, out_dir):
    """§4.7/E8: stitch captured frames -> mp4 POST-HOC (only reached when --record-video captured frames)."""
    frames = ctx.get("_frames") or []
    if not frames:
        return None
    import imageio.v2 as imageio  # optional dep; only imported when a video was requested

    path = str(Path(out_dir) / "runner_route.mp4")
    imageio.mimsave(path, frames, fps=20)
    return path


def main():
    parser = argparse.ArgumentParser(description="B0/B1 policy_route_runner (spec §4)")
    parser.add_argument(
        "--dataset-dir", required=True, help="dir with bc_dataset.npz + schedule.json + bc_dataset_meta.json"
    )
    parser.add_argument("--raw-meta", required=True, help="route_demo_raw_meta.json (env_gates source, §0)")
    parser.add_argument("--output-dir", default=None, help="verdict + video output dir")
    parser.add_argument("--device", default=None, help="override NEWTON_DEVICE (default = raw meta device)")
    parser.add_argument("--max-control-steps", type=int, default=0, help="§4.6 smoke: stop early (0 = full 770)")
    parser.add_argument("--record-video", action="store_true", help="§4.7 offscreen post-hoc render (parent runs it)")
    parser.add_argument(
        "--absolute-waypoints",
        action="store_true",
        help="B0a (spec E13): tgt = seeded-origin + cumsum(actions*scale) as ABSOLUTE demo waypoints -- breaks the "
        "open-loop landing-error accumulation; pipeline-validation leg, NOT a B0-(i) pass-bar substitute",
    )
    parser.add_argument(
        "--macro-ik-replay",
        action="store_true",
        help="B0b (spec E14): drive each macro-leg with the route's OWN ik_move_both to REACH the seat and "
        "exercise pin/C1-held/C2-seat/verdict legs -- event+verdict validation, NOT policy semantics",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="B1 (spec §3): checkpoint.pt -> DETERMINISTIC actor-mean inference on the DEFAULT relative-delta "
        "loop (obs consumed; NOT --absolute-waypoints, NOT --macro-ik-replay)",
    )
    parser.add_argument(
        "--policy-absolute",
        action="store_true",
        help="E15: decode policy action as an absolute per-phase-affine target (not relative delta)",
    )
    parser.add_argument(
        "--rollout-offset",
        default=None,
        help="Opt-i' (TASK B): 'dx,dy' in MILLIMETRES -- the grasp start-offset THIS rollout targets. Asserted "
        "== the schedule-source offset parsed from the --dataset-dir (else --raw-meta) rec_<x>_<y> path "
        "(frame-invariance REFUTED: each rollout MUST use its OWN demo's schedule; mismatch = loud SystemExit). "
        "Omit to leave the guard inert (13-phase / B0 / B0b back-compat).",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir or f"data/policy_route_runner_{time.strftime('%Y%m%d_%H%M%S')}")
    out_dir.mkdir(parents=True, exist_ok=True)
    verdict = {"source": "b0_open_loop_replay", "failure_mode": "hard_crash", "artifacts_valid": False}
    try:
        verdict = _run(args, out_dir)
        verdict["artifacts_valid"] = verdict.get("failure_mode") not in ("hard_crash",)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 -- E8: hard crash => artifacts tagged INVALID, never counted in a rate
        verdict.update(failure_mode="hard_crash", artifacts_valid=False, error=repr(exc))
        raise
    finally:
        (out_dir / "runner_verdict.json").write_text(json.dumps(verdict, indent=2))
        print(f"[RUNNER] wrote {out_dir / 'runner_verdict.json'} failure_mode={verdict.get('failure_mode')}")
    return verdict


if __name__ == "__main__":
    main()
