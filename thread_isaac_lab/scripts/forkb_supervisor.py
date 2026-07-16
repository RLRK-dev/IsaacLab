# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B supervisor: CPU-only launcher/monitor for N single-world collector processes (D1 spec sec 1/sec 5/sec 6).

Launch (R1-4): counts pre-existing compute processes on the collector GPU via nvidia-smi (process COUNT, not
MiB) and clamps N_collect = 4 - k under the <=4 procs/GPU rule, loudly. Every collector is spawned with an
explicit per-child GPU-visibility pin (R1-3); the supervisor itself never touches CUDA (python + subprocess +
nvidia-smi only, R6).

Monitor (R6-3): a collector exiting non-zero (or leaving FAILURE.json) is restarted as a NEW INDIVIDUAL --
restart_count+1 gives a new derived seed and a new proc_meta record. Consecutive failures per slot reset ONLY
on a clean rc==0 completion; when a slot's consecutive failures EXCEED K_fail the whole run halts loudly
(HALT.json + exit 2; D1 sec 5 wording "K_fail 超" taken literally -- a systemic defect must not be hidden by
endless restarts). Disk guard (sec 3): free space < 50 GB warns loudly every cycle; NOTHING is ever deleted.

Relocate lever (sec 6): ``--device-map default`` = {collector: cuda:0, trainer: cuda:2}; ``--device-map
fallback`` = {collector: cuda:0, trainer: cuda:0} with N capped at 3 -- both spawn with NO code change (the
lever-smoke leg proves it). The trainer itself arrives later (I0+); its device is carried as config so the
lever is real today.

Run:
    /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/forkb_supervisor.py \
        --run-root <dir> --base-seed 20260716 --n-collect 4 --episodes 50
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_COLLECTOR = _SCRIPTS / "forkb_collector.py"
_PY = "/home/rlrk/env_isaaclab7/bin/python"  # Option-E venv (CLAUDE.md Newton VBD section)

SEC_S_EXPOSURE = (
    "HEAD FM3/FM4 tighten code is live and UNRATIFIED (I0A_SCOPE_MANIFEST AMENDMENT 1 + sec S, ad0bb76460): "
    "r_paid/done/seat/latch semantics in this run are NOT banked-valid; infra-only claims."
)

DEVICE_MAPS = {
    "default": {"collector": "cuda:0", "trainer": "cuda:2", "n_collect_cap": 4},
    "fallback": {"collector": "cuda:0", "trainer": "cuda:0", "n_collect_cap": 3},
}


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _gpu_compute_proc_count(gpu_index, nvidia_smi_cmd="nvidia-smi"):
    """Pre-existing compute processes on the GPU (R1-4 counts PROCESSES, not memory).

    Returns None when the count is UNKNOWN (tool missing, timeout, or nonzero exit) -- the caller must
    treat None as FAIL-CLOSED: the <=4/GPU invariant can never be assumed satisfied without a measurement
    (I0-b HOLD B2). ``nvidia_smi_cmd`` is a test hook (config-passed, not environ) for the fail-closed
    controls.
    """
    try:
        r = subprocess.run(
            [nvidia_smi_cmd, "--query-compute-apps=pid", "--format=csv,noheader", "-i", str(gpu_index)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[supervisor] GPU preflight UNKNOWN ({type(e).__name__}) -- failing CLOSED", flush=True)
        return None
    if r.returncode != 0:
        print(f"[supervisor] GPU preflight UNKNOWN (rc={r.returncode}) -- failing CLOSED", flush=True)
        return None
    return len([ln for ln in r.stdout.splitlines() if ln.strip()])


def _fresh_failure_marker(run_root, slot):
    """True iff proc_{i}/FAILURE.json exists AND was written by the CURRENT individual (marker rc ==
    slot.restart_count). A stale marker from an earlier individual is not a failure signal; an unreadable
    marker is treated as a failure signal (fail-closed). I0-b HOLD B3."""
    p = run_root / f"proc_{slot.index}" / "FAILURE.json"
    if not p.exists():
        return False
    try:
        return json.loads(p.read_text()).get("rc") == slot.restart_count
    except (json.JSONDecodeError, OSError):
        return True


class Slot:
    def __init__(self, index):
        self.index = index
        self.restart_count = 0
        self.consecutive_failures = 0
        self.proc = None
        self.done = False
        self.log_path = None


def _spawn(slot, a, run_root, gpu_index):
    outbox = run_root / f"proc_{slot.index}"
    outbox.mkdir(parents=True, exist_ok=True)
    slot.log_path = outbox / f"collector.rc{slot.restart_count:03d}.log"
    cmd = [
        _PY,
        str(_COLLECTOR),
        "--outbox",
        str(outbox),
        "--proc-index",
        str(slot.index),
        "--restart-count",
        str(slot.restart_count),
        "--base-seed",
        str(a.base_seed),
        "--episodes",
        str(a.episodes),
        "--backpressure-k",
        str(a.backpressure_k),
        "--episode-steps",
        str(a.episode_steps),
        "--drive-mode",
        a.drive_mode,
    ]
    hooks_this_individual = a.test_crash_slot == slot.index and (
        a.test_crash_rc_max < 0 or slot.restart_count <= a.test_crash_rc_max
    )
    if hooks_this_individual and a.test_crash_after > 0:
        cmd += ["--test-crash-after", str(a.test_crash_after)]
    if hooks_this_individual and a.test_marker_exit_zero:
        cmd += ["--test-marker-exit-zero"]
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_index)  # cvd-child-env: R1-3 pin on the COPIED child env dict
    with open(slot.log_path, "w") as logf:  # Popen dups the fd; the child keeps writing after we close ours
        slot.proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=env)
    print(
        f"[supervisor] spawned slot {slot.index} rc={slot.restart_count} pid={slot.proc.pid} "
        f"CVD={gpu_index} log={slot.log_path.name}",
        flush=True,
    )


def _terminate_all(slots, grace_s):
    for s in slots:
        if s.proc and s.proc.poll() is None:
            s.proc.send_signal(signal.SIGTERM)
    deadline = time.time() + grace_s
    for s in slots:
        if s.proc and s.proc.poll() is None:
            try:
                s.proc.wait(timeout=max(0.1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                s.proc.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--base-seed", type=int, required=True)
    ap.add_argument("--episodes", type=int, required=True, help="episodes per collector slot")
    ap.add_argument("--n-collect", type=int, default=0, help="requested collectors (0 = auto up to cap)")
    ap.add_argument("--backpressure-k", type=int, default=200, help="high-water mark K (E0 pin = 200)")
    ap.add_argument("--k-fail", type=int, default=3, help="halt when consecutive failures EXCEED this (E0 pin=3)")
    ap.add_argument("--episode-steps", type=int, default=230)
    ap.add_argument("--drive-mode", choices=("feedforward", "ik_chord"), default="feedforward")
    ap.add_argument("--device-map", choices=tuple(DEVICE_MAPS), default="default")
    ap.add_argument("--test-crash-slot", type=int, default=-1, help="TEST HOOK: slot receiving the crash hooks")
    ap.add_argument("--test-crash-after", type=int, default=0)
    ap.add_argument(
        "--test-crash-rc-max",
        type=int,
        default=-1,
        help="TEST HOOK: forward crash hooks only to individuals with restart_count <= this (-1 = all)",
    )
    ap.add_argument(
        "--test-marker-exit-zero",
        action="store_true",
        help="TEST HOOK: collector writes FAILURE.json then exits 0 (B3 fresh-marker control)",
    )
    ap.add_argument(
        "--nvidia-smi-cmd", default="nvidia-smi", help="TEST HOOK: preflight command (B2 fail-closed controls)"
    )
    ap.add_argument("--poll", type=float, default=2.0)
    ap.add_argument("--grace", type=float, default=20.0)
    a = ap.parse_args()

    dm = DEVICE_MAPS[a.device_map]
    gpu_index = int(dm["collector"].split(":")[1])
    run_root = Path(a.run_root)
    run_root.mkdir(parents=True, exist_ok=True)

    # D1 sec 5 order: write run_manifest FIRST, then the GPU preflight -- an aborted launch must still
    # leave artifacts (I0-b HOLD B2). Preflight UNKNOWN or no free slot => fail CLOSED with LAUNCH_ABORT.
    run_manifest = {
        "launch_ts": time.time(),
        "base_seed": a.base_seed,
        "n_collect": None,
        "requested": None,
        "preexisting_gpu_procs": None,
        "preflight": "pending",
        "device_map": dm,
        "episodes_per_slot": a.episodes,
        "episode_steps": a.episode_steps,
        "drive_mode": a.drive_mode,
        "backpressure_k": a.backpressure_k,
        "k_fail": a.k_fail,
        "code_sha": {
            "forkb_supervisor.py": _sha256_file(Path(__file__)),
            "forkb_collector.py": _sha256_file(_COLLECTOR),
        },
        "protocol_ref": "FORKB_D1_SPEC_RSTECHLEAD_20260716.md v0.3 sec1/sec5/sec6; "
        "ENV_MULTIWORLD_SUBSTRATE_CHARTER_RSTECHLEAD_20260716.md (APPROVED)",
        "test_hooks": (
            {"test_crash_slot": a.test_crash_slot, "test_crash_after": a.test_crash_after}
            if a.test_crash_after > 0
            else {}
        ),
        "sec_S_exposure": SEC_S_EXPOSURE,
    }
    (run_root / "run_manifest.json").write_text(json.dumps(run_manifest, indent=1))

    def _launch_abort(stage, detail):
        print(f"[supervisor] LAUNCH ABORT ({stage}): {detail} -- failing CLOSED, nothing spawned", flush=True)
        (run_root / "LAUNCH_ABORT.json").write_text(
            json.dumps(
                {"stage": stage, "detail": detail, "ts": time.time(), "sec_S_exposure": SEC_S_EXPOSURE}, indent=1
            )
        )
        run_manifest["preflight"] = f"ABORT:{stage}"
        (run_root / "run_manifest.json").write_text(json.dumps(run_manifest, indent=1))
        return 2

    k_pre = _gpu_compute_proc_count(gpu_index, a.nvidia_smi_cmd)
    if k_pre is None:
        return _launch_abort(
            "preflight_unknown", f"GPU compute-proc count unmeasurable via {a.nvidia_smi_cmd!r}; <=4/GPU unverifiable"
        )
    cap = min(4 - k_pre, dm["n_collect_cap"])
    requested = a.n_collect if a.n_collect > 0 else cap
    n_collect = min(requested, cap)
    print(
        f"[supervisor] {dm['collector']} pre-existing compute procs k={k_pre} -> cap={cap}, "
        f"requested={requested}, N_collect={n_collect} (<=4/GPU rule, R1-4)",
        flush=True,
    )
    if n_collect <= 0:
        return _launch_abort("no_slot", f"k={k_pre} pre-existing procs leave no slot under the <=4/GPU rule")
    run_manifest.update(
        {"n_collect": n_collect, "requested": requested, "preexisting_gpu_procs": k_pre, "preflight": "measured"}
    )
    (run_root / "run_manifest.json").write_text(json.dumps(run_manifest, indent=1))

    slots = [Slot(i) for i in range(n_collect)]
    for s in slots:
        _spawn(s, a, run_root, gpu_index)

    halted = False
    while True:
        time.sleep(a.poll)
        free_gb = shutil.disk_usage(run_root).free / 2**30
        if free_gb < 50.0:
            print(
                f"[supervisor] DISK WARN: {free_gb:.1f} GB free < 50 GB -- NOT deleting anything "
                "(human decision required, D1 sec 3)",
                flush=True,
            )
        for s in slots:
            if s.done or s.proc is None:
                continue
            rc = s.proc.poll()
            if rc is None:
                continue
            # D1 sec 5: failure = nonzero exit OR a FAILURE.json written by the CURRENT individual
            # (I0-b HOLD B3). A stale marker from an earlier individual never retriggers.
            fresh_marker = _fresh_failure_marker(run_root, s)
            if rc == 0 and not fresh_marker:
                s.done = True
                s.consecutive_failures = 0
                print(f"[supervisor] slot {s.index} rc=0 complete (restarts used={s.restart_count})", flush=True)
                continue
            s.consecutive_failures += 1
            print(
                f"[supervisor] slot {s.index} FAILED rc={rc} (fresh marker={fresh_marker}) "
                f"consecutive={s.consecutive_failures}/{a.k_fail}",
                flush=True,
            )
            if s.consecutive_failures > a.k_fail:
                print(
                    f"[supervisor] HALT: slot {s.index} consecutive failures {s.consecutive_failures} "
                    f"EXCEED K_fail={a.k_fail} -- systemic defect, refusing to mask it with restarts",
                    flush=True,
                )
                (run_root / "HALT.json").write_text(
                    json.dumps(
                        {
                            "slot": s.index,
                            "consecutive_failures": s.consecutive_failures,
                            "k_fail": a.k_fail,
                            "last_rc": rc,
                            "ts": time.time(),
                            "restart_count": s.restart_count,
                            "sec_S_exposure": SEC_S_EXPOSURE,
                        },
                        indent=1,
                    )
                )
                halted = True
                break
            s.restart_count += 1  # R6-3: a NEW INDIVIDUAL (new derived seed, new proc_meta record)
            _spawn(s, a, run_root, gpu_index)
        if halted or all(s.done for s in slots):
            break

    if halted:
        _terminate_all(slots, a.grace)
    summary = {
        "halted": halted,
        "ts": time.time(),
        "sec_S_exposure": SEC_S_EXPOSURE,
        "slots": [
            {
                "index": s.index,
                "restarts": s.restart_count,
                "done": s.done,
                "consecutive_failures": s.consecutive_failures,
            }
            for s in slots
        ],
        "episodes_published": len(list(run_root.glob("proc_*/ep_*.npz"))),
    }
    (run_root / "run_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"[supervisor] summary: {json.dumps(summary)}", flush=True)
    return 2 if halted else 0


if __name__ == "__main__":
    sys.exit(main())
