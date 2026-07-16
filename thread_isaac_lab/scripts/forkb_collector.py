# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B collector: one world_count=1 CPU-path route env producing atomic, byte-deterministic episode files.

One collector = one process = one env (the proven CPU path; the make_solver tripwire refuses anything else).
Episodes are published per D1 spec sec 2/sec 3 (R3-1/R3-2): write tmp -> sha256 -> manifest -> atomic rename;
the npz rename is the ONLY publication point, so a crash mid-episode leaves NO published episode (R6-1). A
manifest without its npz is in-flight garbage and consumers must ignore it (contract in I0B_BUILD doc). The
serializer is FILE-level byte-deterministic (R2-4-b): a fixed zip timestamp replaces the wall clock, so the
same (code, fingerprint, derived_seed, workload) reproduces ``ep_*.npz`` byte-for-byte.

Restart safety (R6-3/R6-4): episode numbering resumes at max(existing index)+1 so a restarted individual can
NEVER overwrite a published episode, and each individual appends its own ``proc_meta.rc{NNN}.json`` besides
overwriting the current ``proc_meta.json`` -- per-individual provenance survives restarts.

Seeding (R2-1/AMEND-1): derived_seed = SeedSequence([base_seed, process_index, restart_count]) -> the global
legacy RNG (the env's one bare np.random site, INIT_XY_NOISE at reset, consumes it). Backpressure (R3-3):
before each episode, if the outbox holds >= K unconsumed episodes the collector pauses LOUDLY until the count
drops. Test hook (mechanism legs only): ``--test-crash-after N`` hard-crashes after N published episodes --
CLI, not os.environ (D1 sec 4 carry R2-3); recorded in proc_meta.

Schema honesty (Stage-A :117 additive; sec S carry): the env exposes NO termination taxonomy yet (that is a
W1 trainer-env build item), so ``termination_reason`` is recorded as ``""`` and the additive ``truncated_by``
field says why the episode ended. ``time_out`` is all-False -- a workload step budget is NOT an env timeout
(timeouts-contamination rule). Every artifact carries ``sec_S_exposure``: reward/latch/seat semantics at HEAD
are UNRATIFIED until the gate-2 owner chain passes; claims here are infra-only.

Run (normally spawned by forkb_supervisor, which pins each child's GPU visibility per the CLAUDE.md GPU
rules; when running standalone, pin the process's GPU visibility yourself the same way):
    /home/rlrk/env_isaaclab7/bin/python \
        thread_isaac_lab/scripts/forkb_collector.py --outbox <dir> --proc-index 0 --restart-count 0 \
        --base-seed 20260716 --episodes 2 --backpressure-k 200
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import signal
import sys
import time
import traceback
import zipfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_TIL = _SCRIPTS.parent
for _p in (str(_TIL), str(_TIL / "envs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_FIXED_ZIP_DT = (1980, 1, 1, 0, 0, 0)  # R2-4-b: the zip container's ONLY nondeterminism is the timestamp

SEC_S_EXPOSURE = (
    "HEAD FM3/FM4 tighten code is live and UNRATIFIED (I0A_SCOPE_MANIFEST AMENDMENT 1 + sec S, ad0bb76460): "
    "r_paid/done/seat/latch semantics in this artifact are NOT banked-valid; infra-only claims."
)

_STOP = False


def _on_sigterm(signum, frame):
    global _STOP
    _STOP = True


def save_npz_deterministic(path, arrays):
    """``np.savez`` with a pinned zip timestamp: byte-deterministic at the FILE level (R2-4-b).

    Args:
        path: destination ``.npz`` path (written whole; callers rename atomically).
        arrays: mapping name -> ``np.ndarray``.
    """
    import numpy as np

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for name in sorted(arrays):
            buf = io.BytesIO()
            np.lib.format.write_array(buf, np.asanyarray(arrays[name]), allow_pickle=False)
            zi = zipfile.ZipInfo(name + ".npy", date_time=_FIXED_ZIP_DT)
            zi.compress_type = zipfile.ZIP_STORED
            zf.writestr(zi, buf.getvalue())


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _outbox_unconsumed(outbox):
    """Unconsumed = published episodes minus consumer acks (``.consumed`` markers; D1 sec 5 substitute)."""
    eps = {p.stem for p in outbox.glob("ep_*.npz")}
    acked = {p.name[: -len(".consumed")] for p in outbox.glob("ep_*.consumed")}
    return len(eps - acked)


def _next_episode_index(outbox):
    """Resume-safe numbering: max existing published index + 1 (a restart must never overwrite, R6-4)."""
    mx = -1
    for p in outbox.glob("ep_*.npz"):
        try:
            mx = max(mx, int(p.stem.split("_")[1]))
        except (IndexError, ValueError):
            continue
    return mx + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outbox", required=True)
    ap.add_argument("--proc-index", type=int, required=True)
    ap.add_argument("--restart-count", type=int, default=0)
    ap.add_argument("--base-seed", type=int, required=True)
    ap.add_argument("--episodes", type=int, required=True, help="episodes this individual should publish")
    ap.add_argument("--backpressure-k", type=int, default=200, help="high-water mark K (E0 pin = 200)")
    ap.add_argument("--episode-steps", type=int, default=230, help="workload RL steps per episode")
    ap.add_argument("--drive-mode", choices=("feedforward", "ik_chord"), default="feedforward")
    ap.add_argument(
        "--test-crash-after",
        type=int,
        default=0,
        help="TEST HOOK (mechanism legs): hard-crash after N published episodes (0 = off)",
    )
    a = ap.parse_args()

    signal.signal(signal.SIGTERM, _on_sigterm)

    import numpy as np

    derived = int(np.random.SeedSequence([a.base_seed, a.proc_index, a.restart_count]).generate_state(1)[0])
    np.random.seed(derived)  # R2-1: the env's bare-RNG site consumes the per-process stream

    import newton_route_env as nre
    import torch

    outbox = Path(a.outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    golden = (
        _TIL.parent
        / "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
        / "w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz"
    )

    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(golden),
            "g1_scene_align": True,
            "route_drive_mode": a.drive_mode,
            "route_c2_scene": True,
        },
    )
    obs_prev = env.reset()[0]

    # R2-2 provenance (per-process identity; fingerprint set = the v4 mechanism, scraped from the live closure)
    import re

    env_keys = set()
    repo = str(_TIL.parent)
    closure = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        fp = Path(f).resolve()
        if str(fp).startswith(repo) and fp.suffix == ".py" and fp.exists():
            closure[str(fp.relative_to(_TIL.parent))] = _sha256_file(fp)
            src = fp.read_text(errors="replace")
            env_keys.update(re.findall(r'os\.environ\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']', src))
            env_keys.update(re.findall(r'os\.environ\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]', src))
    code_sha = closure.get("thread_isaac_lab/scripts/forkb_collector.py", "")
    proc_meta = {
        "base_seed": a.base_seed,
        "process_index": a.proc_index,
        "restart_count": a.restart_count,
        "derived_seed": derived,
        "pid": os.getpid(),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),  # cvd-provenance-read
        "env_fingerprint": {k: os.environ.get(k) for k in sorted(env_keys)},
        "closure_sha256": dict(sorted(closure.items())),
        "recording_sha256": _sha256_file(golden),
        "code_sha": code_sha,
        "start_ts": time.time(),
        "drive_mode": a.drive_mode,
        "test_hooks": {"test_crash_after": a.test_crash_after} if a.test_crash_after else {},
        "sec_S_exposure": SEC_S_EXPOSURE,
    }
    meta_txt = json.dumps(proc_meta, indent=1)
    (outbox / "proc_meta.json").write_text(meta_txt)
    (outbox / f"proc_meta.rc{a.restart_count:03d}.json").write_text(meta_txt)  # per-individual, append-only

    cable_ids = env._cable_bodies[0]
    zero = torch.zeros((1, 6), dtype=torch.float32)
    ep_idx = _next_episode_index(outbox)
    published = 0
    try:
        while published < a.episodes:
            # R3-3 backpressure: pause LOUDLY while the outbox backlog is at the high-water mark
            while _outbox_unconsumed(outbox) >= a.backpressure_k:
                if _STOP:
                    print(f"[collector {a.proc_index}] SIGTERM during backpressure pause, exiting", flush=True)
                    return 0
                print(f"[collector {a.proc_index}] BACKPRESSURE: outbox >= K={a.backpressure_k}, pausing", flush=True)
                time.sleep(2.0)
            obs_l, nobs_l, act_l, rew_l, done_l = [], [], [], [], []
            traj = np.zeros((a.episode_steps, len(cable_ids), 3), dtype=np.float64)
            truncated_by = "workload_step_budget"
            aborted = False
            for _t in range(a.episode_steps):
                if _STOP:
                    aborted = True  # R6-1: the in-flight episode is dropped, never published
                    break
                obs, rewards, dones, extras = env.step(zero)
                obs_l.append(obs_prev.cpu().numpy()[0])
                nobs_l.append(obs.cpu().numpy()[0])
                act_l.append(zero.cpu().numpy()[0])
                rew_l.append(float(rewards[0]))
                done_l.append(bool(dones[0]))
                traj[_t] = env._state_0.body_q.numpy()[cable_ids, :3]
                obs_prev = obs
                if bool(dones[0]):
                    truncated_by = "env_done"
                    break
            if aborted:
                print(f"[collector {a.proc_index}] SIGTERM mid-episode: aborted WITHOUT publish", flush=True)
                return 0
            n = len(obs_l)
            arrays = {
                "o": np.asarray(obs_l, dtype=np.float32),
                "o_next": np.asarray(nobs_l, dtype=np.float32),
                "a_raw": np.asarray(act_l, dtype=np.float32),
                "a_executed": np.asarray(act_l, dtype=np.float32),  # zero-residual workload: executed == raw
                "r_paid": np.asarray(rew_l, dtype=np.float32),
                "done": np.asarray(done_l, dtype=bool),
                "time_out": np.zeros(n, dtype=bool),  # NEVER a workload truncation (timeouts-contamination rule)
                "invalid_mask": np.zeros(n, dtype=bool),
                "cable_traj": traj[:n],
            }
            # R3-1 atomic publish: tmp -> sha -> manifest -> rename; the rename is the ONLY publication point
            name = f"ep_{ep_idx:06d}"
            tmp = outbox / (name + ".tmp")
            save_npz_deterministic(tmp, arrays)
            sha = _sha256_file(tmp)
            manifest = {
                "process_index": a.proc_index,
                "derived_seed": derived,
                "pid": os.getpid(),
                "env_fingerprint_sha": hashlib.sha256(
                    json.dumps(proc_meta["env_fingerprint"], sort_keys=True).encode()
                ).hexdigest(),
                "code_sha": code_sha,
                "episode_idx": ep_idx,
                "n_steps": n,
                "termination_reason": "",  # env exposes no taxonomy yet (W1 build item) -- do not fabricate
                "truncated_by": truncated_by,
                "invalid_any": False,
                "source": "online",
                "sha256": sha,
                "drive_mode": a.drive_mode,
                "sec_S_exposure": SEC_S_EXPOSURE,
            }
            (outbox / (name + ".manifest.json")).write_text(json.dumps(manifest, indent=1))
            os.replace(tmp, outbox / (name + ".npz"))
            print(
                f"[collector {a.proc_index}] published {name} sha={sha[:12]} steps={n} end={truncated_by}", flush=True
            )
            ep_idx += 1
            published += 1
            if a.test_crash_after and published >= a.test_crash_after:
                print(f"[collector {a.proc_index}] TEST CRASH (--test-crash-after={a.test_crash_after})", flush=True)
                os._exit(17)  # simulated hard crash: no cleanup, no FAILURE.json -- the supervisor must cope
            obs_prev = env.reset()[0]
    except Exception:  # R6-1 soft-crash marker: {last_episode, reason, ts, rc}
        (outbox / "FAILURE.json").write_text(
            json.dumps(
                {
                    "last_episode": ep_idx - 1,
                    "reason": traceback.format_exc()[-2000:],
                    "ts": time.time(),
                    "rc": a.restart_count,
                },
                indent=1,
            )
        )
        print(f"[collector {a.proc_index}] FAILURE (soft): wrote FAILURE.json", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
