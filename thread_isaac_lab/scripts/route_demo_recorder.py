# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Whole-route demo RAW recorder (``ROUTE_DEMO_RAW_v1``).

Additive, READ-ONLY recorder for the committed square-on C1->C2 route
(``_run_mujoco_grasp_route``); records a UNIT-independent per-frame superset into
``route_demo_raw.npz`` + a meta sidecar for an offline (obs, actions) converter.
NEVER writes physics/control state and issues NO solver call (``mj_forward``/
``mj_step``/``eval_fk``/``model.collide``/solver are forbidden in :meth:`sample`
and the notes -- P3_DEMO_RECORDER_SPEC.md v2.1 §2). Env-gated ``DEMO_RECORD=1``;
when off the module is not imported (byte-identical).

Robustness (層2/層5 batch-fix, 2026-07-02): every public entry point is wrapped in a
ONE-SHOT self-disarm guard so a recorder exception can never kill the observed route
(:func:`_guarded`); :meth:`sample` appends atomically (all-or-nothing) so a mid-sample
raise leaves the buffers length-consistent (no torn frame); provenance (git + source
sha256) is pinned at CONSTRUCT (import time), not at finalize, and re-checked at the end
(``changed_during_run``); the npz gets an integrity ``npz_sha256`` and is written via
tmp+rename.
"""

from __future__ import annotations

import atexit
import functools
import hashlib
import json
import os
import subprocess

import numpy as np

RECORDER_VERSION = "ROUTE_DEMO_RAW_v1"
# Default effective EE rotation = Rx(-90 deg), xyzw (the solve_ik_dual constant, test_newton_clip_routing.py:1858).
_DEFAULT_QUAT = np.array([-0.7071067811865476, 0.0, 0.0, 0.7071067811865476], dtype=np.float32)
_STACK_KEYS = (
    "ee_pos_l",
    "ee_pos_r",
    "ee_quat_l",
    "ee_quat_r",
    "ee_tgt_pos_l",
    "ee_tgt_pos_r",
    "ee_tgt_quat_effective_l",
    "ee_tgt_quat_effective_r",
    "arm_q",
    "grip_cmd",
    "cable_xyz",
    "cable_quat",
)
_INT_KEYS = (
    ("phase_id", np.int16),
    ("ik_rot_override_active", np.int8),
    ("nearest_seg_l", np.int16),
    ("nearest_seg_r", np.int16),
    ("held_seg_l", np.int16),
    ("pin_active", np.int8),
    ("pinned_body", np.int16),
    ("pin_eqid", np.int16),
)
# Source files pinned by ``as_run_sha256`` (relative to this module's dir).
_PROV_RELPATHS = (
    ("test_newton_clip_routing.py",),
    ("route_demo_recorder.py",),
    ("..", "configs", "task_config.py"),
)


def _sha256_file(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _guarded(method):
    """Wrap a public entry point in a ONE-SHOT self-disarm guard.

    An observer must NEVER kill the observed route: on the first exception in any wrapped
    method the recorder disarms (``_armed = False``; all later calls become no-ops) and the
    run keeps going. Combined with the atomic append in :meth:`sample`, the partial npz stays
    length-consistent. The disarm reason is recorded into the meta sidecar.
    """

    @functools.wraps(method)
    def _wrap(self, *args, **kwargs):
        if not self._armed:
            return None
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - deliberate: never propagate into the route
            self._armed = False
            self._disarm_reason = f"{method.__name__}: {exc!r}"
            print(
                f"  [DEMO_REC] DISARMED ({self._disarm_reason}) at frame "
                f"{len(self._buf['phase_id'])} -- route continues, npz stays consistent"
            )
            return None

    return _wrap


class RouteDemoRecorder:
    """Append-only per-frame recorder for the committed square-on C1->C2 route (spec §2/§3)."""

    def __init__(self, scene_info, ee_body_offset, l_drv, r_drv, out_dir, meta):
        self._out_dir = os.path.expanduser(out_dir)
        self._l_ee = int(scene_info["left_body_start"]) + int(ee_body_offset)
        self._r_ee = int(scene_info["right_body_start"]) + int(ee_body_offset)
        self._cable = [int(b) for b in scene_info["cable_bodies"]]
        self._l_drv, self._r_drv = {int(d) for d in l_drv}, {int(d) for d in r_drv}
        self._meta = dict(meta)
        # State stamped onto EVERY frame (held between the sparse note_* events).
        self._tgt_l = self._tgt_r = None  # filled on first note_targets, else EE at frame 0
        self._rot_l, self._rot_r = _DEFAULT_QUAT.copy(), _DEFAULT_QUAT.copy()
        self._override = 0
        self._grip = np.zeros(2, dtype=np.float32)  # [L, R] last-commanded servo rad
        self._pin_on, self._pin_body, self._pin_eqid = 0, -1, -1
        self._cur_phase, self._phase_names, self._phase_map = -1, [], {}
        # DQ7 stage-(ii) kick-and-recover: injection windows recorded into the META only (NOT the npz arrays ->
        # a None-path run [no mark_injection call] leaves _injection_windows=[] and the npz byte-identical).
        self._injection_windows, self._inj_open = [], None
        self._n_grip_events, self._n_grip_unmatched = 0, 0
        self._armed, self._done, self._disarm_reason = True, False, None
        self._buf = {k: [] for k in (*_STACK_KEYS, *(name for name, _ in _INT_KEYS))}
        self._prov0 = self._capture_provenance()  # F5: pin provenance at construct (import time)
        os.makedirs(self._out_dir, exist_ok=True)  # N4: fail fast on a bad DEMO_OUT (not at finalize)
        atexit.register(self.finalize)  # backstop: npz written even on a mid-fn sys.exit

    # --- provenance ----------------------------------------------------------
    def _capture_provenance(self):
        """Snapshot git head/dirty/diff + source sha256 [dict]. Called at construct AND finalize."""
        here = os.path.dirname(os.path.abspath(__file__))
        try:
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=here).decode().strip()
            dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=here).decode().strip())
            diff_sha = hashlib.sha256(subprocess.check_output(["git", "diff", "HEAD"], cwd=here)).hexdigest()
        except Exception:  # noqa: BLE001 - loud nulls in meta on any git failure (concurrent-pane lock etc.)
            head, dirty, diff_sha = None, None, None
        src = {rel[-1]: _sha256_file(os.path.join(here, *rel)) for rel in _PROV_RELPATHS}
        return {"head_sha": head, "git_dirty": dirty, "git_diff_sha256": diff_sha, "as_run_sha256": src}

    # --- sparse register notes (all one-shot self-disarm guarded) -------------
    @_guarded
    def set_phase(self, name):  # current native route section [str], stamped onto subsequent frames
        if self._inj_open is not None:  # DQ7 (ii): a still-open injection window closes at the phase boundary (defensive)
            self._inj_open["end_frame"] = len(self._buf["phase_id"])
            self._injection_windows.append(self._inj_open)
            self._inj_open = None
        if name not in self._phase_map:
            self._phase_map[name] = len(self._phase_names)
            self._phase_names.append(str(name))
        self._cur_phase = self._phase_map[name]

    @_guarded
    def note_targets(self, tgt_l, tgt_r):  # last-COMMANDED EE positions [m] (ik_move_both entry)
        self._tgt_l = np.asarray(tgt_l, dtype=np.float32).reshape(3).copy()
        self._tgt_r = np.asarray(tgt_r, dtype=np.float32).reshape(3).copy()

    @_guarded
    def note_grip(self, driver_joints, target_rad):
        """Record a servo command [rad] at the gripper chokepoint; per-arm via driver-index intersection."""
        dj = {int(d) for d in driver_joints}
        matched = False
        if dj & self._l_drv:
            self._grip[0] = float(target_rad)
            matched = True
        if dj & self._r_drv:
            self._grip[1] = float(target_rad)
            matched = True
        if matched:
            self._n_grip_events += 1
        else:  # F1: a no-arm-match command used to be silently dropped (grip_cmd froze) -- warn + count it
            self._n_grip_unmatched += 1
            print(
                f"  [DEMO_REC] grip cmd matched NO arm (drivers={sorted(dj)}, "
                f"L={sorted(self._l_drv)}, R={sorted(self._r_drv)}) -- unrecorded"
            )

    @_guarded
    def note_ik_rot(self, quat_l, quat_r, override_active):
        """Update the DERIVED effective EE-rotation register [xyzw]; ``None`` restores the default Rx(-90 deg)."""
        self._rot_l = _DEFAULT_QUAT.copy() if quat_l is None else np.asarray(quat_l, dtype=np.float32).reshape(4).copy()
        self._rot_r = _DEFAULT_QUAT.copy() if quat_r is None else np.asarray(quat_r, dtype=np.float32).reshape(4).copy()
        self._override = int(override_active)

    @_guarded
    def note_pin(self, eqid, body_idx):  # eq-pin AFTER activation, stamped onto subsequent frames
        self._pin_on, self._pin_eqid, self._pin_body = 1, int(eqid), int(body_idx)

    @_guarded
    def mark_injection(self, phase=None, arm=None, offset_m=None, kick_calls=None, seed=None, event="start"):
        """DQ7 stage-(ii) kick-and-recover: stamp an injection window into the META (NOT the npz arrays).

        ``event="start"`` opens a window at the current frame (the first KICKED frame, commanded target = script
        + offset); ``event="end"`` closes it at the current frame (the first RELEASED/recovery frame, commanded =
        script). The offline converter DROPs the frames in ``[start_frame, end_frame)`` (the anti-restoring kick)
        and KEEPs the rest (mini-spec v2 §F; %9 C1 command-key: KEEP/DROP is keyed on window membership, NOT the
        achieved ee_pos, because a recovery frame's achieved is legitimately off-path). Recorded frames are the
        ``route_demo_raw`` ``frame_idx``; per-frame arrays are untouched so a None-path run stays byte-identical.
        """
        f = len(self._buf["phase_id"])  # current frame index (== route_demo_raw frame_idx)
        if event == "start":
            if self._inj_open is not None:  # defensive: a prior window never closed -> close it at this frame
                self._inj_open["end_frame"] = f
                self._injection_windows.append(self._inj_open)
            self._inj_open = {
                "phase": str(phase),
                "arm": str(arm),
                "offset_mm": [round(float(o) * 1e3, 4) for o in (offset_m or ())],
                "start_frame": int(f),
                "end_frame": None,
                "kick_calls": int(kick_calls) if kick_calls is not None else None,
                "seed": seed,
            }
        elif event == "end" and self._inj_open is not None:
            self._inj_open["end_frame"] = int(f)
            self._injection_windows.append(self._inj_open)
            self._inj_open = None

    # --- per-frame sample (guarded + ATOMIC append: F3 torn-frame defense) ----
    @_guarded
    def sample(self, state, scene_info=None):
        # Read-only: every stored .numpy() slice is .copy()-ed to defeat double-buffer view aliasing
        # (test:1741/:1806). No solver call is issued. ``scene_info`` kept for hook-signature stability (unused).
        bq = state.body_q.numpy()  # [nbody, 7] pos(xyz) + quat(xyzw)
        jq = state.joint_q.numpy()  # PHYSICS joint vector (NOT fk_state: FK fingers stay frozen, spec §3)
        le, r, cab = self._l_ee, self._r_ee, self._cable
        pl, pr = bq[le, :3].astype(np.float32).copy(), bq[r, :3].astype(np.float32).copy()
        if self._tgt_l is None:  # pre-first-command frames -> actual EE (no undefined frames, spec §3)
            self._tgt_l, self._tgt_r = pl.copy(), pr.copy()
        cxyz = bq[cab][:, :3].astype(np.float32).copy()
        cxy = cxyz[:, :2]  # argmin seg indices (pure numpy; NO solver call)
        # Compute ALL values first; NOTHING is appended until every value exists -> a mid-compute raise
        # (MemoryError in .astype / norm, index drift on a future scene) leaves the buffers untouched (no torn frame).
        row = {
            "ee_pos_l": pl,
            "ee_pos_r": pr,
            "ee_quat_l": bq[le, 3:7].astype(np.float32).copy(),
            "ee_quat_r": bq[r, 3:7].astype(np.float32).copy(),
            "ee_tgt_pos_l": self._tgt_l.copy(),
            "ee_tgt_pos_r": self._tgt_r.copy(),
            "ee_tgt_quat_effective_l": self._rot_l.copy(),
            "ee_tgt_quat_effective_r": self._rot_r.copy(),
            "arm_q": jq.astype(np.float32).copy(),
            "grip_cmd": self._grip.copy(),
            "cable_xyz": cxyz,
            "cable_quat": bq[cab][:, 3:7].astype(np.float32).copy(),
            "ik_rot_override_active": self._override,
            "phase_id": self._cur_phase,
            "pin_active": self._pin_on,
            "pinned_body": self._pin_body,
            "pin_eqid": self._pin_eqid,
            "nearest_seg_l": int(np.argmin(np.linalg.norm(cxy - pl[:2], axis=1))),
            "nearest_seg_r": int(np.argmin(np.linalg.norm(cxy - pr[:2], axis=1))),
            "held_seg_l": int(np.argmin(np.abs(cxyz[:, 1] - pl[1]))),
        }
        buf = self._buf
        for k, v in row.items():  # atomic append: reached only after every value computed OK
            buf[k].append(v)

    # --- finalize ------------------------------------------------------------
    def finalize(self, out_path=None, verdict=None):
        """Write the npz + meta sidecar once (idempotent). ``verdict`` [dict] = the run's own regrasp verdict."""
        if self._done:
            return
        self._done = True
        os.makedirs(self._out_dir, exist_ok=True)
        b = self._buf
        lens = {k: len(v) for k, v in b.items()}
        t = min(lens.values()) if lens else 0
        torn = any(v != t for v in lens.values())  # F3 defense-2: atomic append makes this an invariant check
        arrays = {
            "frame_idx": np.arange(t, dtype=np.int64),
            "sim_time": np.arange(t, dtype=np.float64) * float(self._meta.get("dt", 0.0)),
        }
        for name, dt in _INT_KEYS:
            arrays[name] = np.array(b[name][:t], dtype=dt)
        for k in _STACK_KEYS:
            arrays[k] = np.stack(b[k][:t]).astype(np.float32) if t else np.zeros((0,), dtype=np.float32)
        npz_path = os.path.join(self._out_dir, "route_demo_raw.npz")
        self._atomic_savez(npz_path, arrays)  # F6: tmp + os.replace
        self._write_meta(npz_path, t, verdict, torn)
        print(
            f"  [DEMO_REC] wrote {npz_path} (T={t} frames, {len(self._phase_names)} phases, "
            f"{self._n_grip_events} grip events{', TORN_TAIL' if torn else ''}"
            f"{', DISARMED' if self._disarm_reason else ''})"
        )

    @staticmethod
    def _atomic_savez(npz_path, arrays):
        tmp = npz_path + ".tmp"  # np.savez appends .npz if the path lacks it -> resolve the real written path
        np.savez(tmp, **arrays)
        written = tmp if os.path.exists(tmp) else tmp + ".npz"
        os.replace(written, npz_path)

    def _write_meta(self, npz_path, t, verdict, torn):
        env_keys = (
            "DEMO_RECORD",
            "S6_GRASP_ROUTE",
            "S13_ROUTE_C2",
            "SEAT_TOPDOWN",
            "C2_DUALSEAT",
            "PERCLIP_PIN",
            "CLIP_FLOAT_Z",
            "SPACER",
            "CLIP2",
            "CLIP_COLLISION",
            "CLIP_X",
            "CLIP_Y",
            "CLIP2_X",
            "CLIP2_Y",
            "C2_TILT_SIGN",
            "S6_ENGAGE_YC",
            "NEWTON_DEVICE",
            "CUDA_VISIBLE_DEVICES",
            "CABLE_XY_OFFSET",  # W0: IC cable-XY offset [m, "dx,dy"] -> META-authoritative for the converter (_offset_from_meta); meta-only, npz byte-identical
        )
        if self._inj_open is not None:  # DQ7 (ii): close a window still open at finalize (defensive, to frame t)
            self._inj_open["end_frame"] = int(t)
            self._injection_windows.append(self._inj_open)
            self._inj_open = None
        prov, prov_now = self._prov0, self._capture_provenance()  # F5: pinned-at-construct vs end-of-run
        changed = sorted(k for k, v in prov["as_run_sha256"].items() if prov_now["as_run_sha256"].get(k) != v)
        meta = dict(self._meta)  # construct-hook fields (resolved_clip_c1/c2, joint_names, markers) flow through
        meta.update(
            {
                "recorder_version": RECORDER_VERSION,
                "npz": os.path.basename(npz_path),
                "npz_sha256": _sha256_file(npz_path),  # F6: bind meta <-> npz
                "n_frames": t,
                "torn_tail": bool(torn),  # F3
                "quat_convention": "xyzw (warp)",
                "head_sha": prov["head_sha"],  # F5: pinned at construct (not end-of-run)
                "git_dirty": prov["git_dirty"],
                "git_diff_sha256": prov["git_diff_sha256"],
                "as_run_sha256": prov["as_run_sha256"],
                "changed_during_run": changed,  # F5: sources whose sha256 moved between construct and finalize
                "env_gates": {k: os.environ.get(k) for k in env_keys},
                "phase_names": self._phase_names,
                "injection_windows": self._injection_windows,  # DQ7 (ii): kick windows [start_frame,end_frame) (meta-only; [] on None-path)
                "n_grip_events": self._n_grip_events,
                "n_grip_unmatched": self._n_grip_unmatched,  # F1
                "driver_joints_l": sorted(self._l_drv),
                "driver_joints_r": sorted(self._r_drv),
                "disarmed": self._disarm_reason is not None,  # F4
                "disarm_reason": self._disarm_reason,
                "verdict": verdict,
            }
        )
        meta.setdefault("resolved_clip_c1_xy", None)  # provided by the construct hook (env-resolved, no hardcode here)
        meta.setdefault("resolved_clip_c2_xy", None)
        tmp = os.path.join(self._out_dir, "route_demo_raw_meta.json.tmp")
        with open(tmp, "w") as fh:
            json.dump(meta, fh, indent=2, default=str)
        os.replace(tmp, os.path.join(self._out_dir, "route_demo_raw_meta.json"))  # F6: atomic meta write
