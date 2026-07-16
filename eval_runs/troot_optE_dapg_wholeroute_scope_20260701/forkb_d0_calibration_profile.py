# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B D0 item-1 calibration profile -- D0_CALIBRATION_ONLY (never E0/B-accept/N-adoption evidence).

Single 1-process diagnostic run per the OPS-SUP CONCUR-WITH-CONDITIONS protocol (materials doc item-1):
parent = sampler (before/during/after positive controls, PID-attributed GPU MiB, process-tree RSS, normalized
CPU%, thread count; missing samples = fail-loud); child = the workload (real NewtonRouteEnv, world_count=1,
use_mujoco_cpu default True, FF-replay zero-residual, warmup 30 RL steps + measurement window steps 30..229).

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_d0_calibration_profile.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
STATUS = _EVAL / "forkb_d0_calibration_status.json"
OUT = _EVAL / "forkb_d0_calibration_profile_result.json"
GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"

WARMUP_STEPS = 30
WINDOW_END = 230  # measurement window = RL steps [30, 230)
CADENCE_S = 2.0


# ----------------------------------------------------------------------------------- child workload
def workload():
    _TIL = _EVAL.parent.parent / "thread_isaac_lab"
    for _p in (str(_TIL), str(_TIL / "envs")):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    import newton_route_env as nre  # noqa: PLC0415
    import torch  # noqa: PLC0415

    env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg={
        "grasp_actuation": True, "route_executor_impl": "route_executor", "route_recording_npz": str(GOLDEN_NPZ),
        "g1_scene_align": True, "route_drive_mode": "feedforward", "route_c2_scene": True,
    })
    env.reset()
    STATUS.write_text(json.dumps({"pid": os.getpid(), "phase": "warmup", "step": 0,
                                  "use_mujoco_cpu": bool(getattr(env._solver, "use_mujoco_cpu", None)),
                                  "world_count": 1}))
    zero = torch.zeros((1, 6), dtype=torch.float32)
    for t in range(WINDOW_END):
        _, _, dones, _ = env.step(zero)
        if t % 10 == 0 or t == WARMUP_STEPS:
            phase = "warmup" if t < WARMUP_STEPS else "window"
            STATUS.write_text(json.dumps({"pid": os.getpid(), "phase": phase, "step": t,
                                          "use_mujoco_cpu": bool(getattr(env._solver, "use_mujoco_cpu", None)),
                                          "world_count": 1}))
        if bool(dones[0]):
            STATUS.write_text(json.dumps({"pid": os.getpid(), "phase": "early_done", "step": t,
                                          "use_mujoco_cpu": bool(getattr(env._solver, "use_mujoco_cpu", None))}))
            return 3
    STATUS.write_text(json.dumps({"pid": os.getpid(), "phase": "done", "step": WINDOW_END,
                                  "use_mujoco_cpu": bool(getattr(env._solver, "use_mujoco_cpu", None))}))
    return 0


# ----------------------------------------------------------------------------------- parent sampler
def _gpu_pid_mib(pid):
    try:
        out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout
        for line in out.strip().splitlines():
            p, m = [x.strip() for x in line.split(",")[:2]]
            if int(p) == pid:
                return int(m)
        return 0  # PID absent = 0 MiB attributed
    except Exception:  # noqa: BLE001
        return None  # sample FAILURE (fail-loud downstream)


_PROC_CACHE = {}  # pid -> psutil.Process, PERSISTENT across samples: cpu_percent(interval=None) returns 0.0
#                   on the FIRST call of a given Process object (needs a prior baseline on the SAME object) --
#                   fresh objects per sample = a dead 0.0-flat CPU instrument (v1 artifact preserved as evidence).


def _tree_stats(pid):
    try:
        import psutil  # noqa: PLC0415
        root = _PROC_CACHE.setdefault(pid, psutil.Process(pid))
        procs = [root] + root.children(recursive=True)
        procs = [_PROC_CACHE.setdefault(p.pid, p) if p.pid != pid else p for p in procs]
        rss = sum(p.memory_info().rss for p in procs if p.is_running())
        thr = sum(p.num_threads() for p in procs if p.is_running())
        cpu = sum(p.cpu_percent(interval=None) for p in procs if p.is_running())
        return rss / 1e6, thr, cpu
    except Exception:  # noqa: BLE001
        return None, None, None


def main():
    if "--workload" in sys.argv:
        sys.exit(workload())

    _CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    assert _CVD == "0", f"protocol fixes CUDA_VISIBLE_DEVICES=0; got {_CVD!r}"
    import psutil  # noqa: PLC0415

    code_sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=str(_EVAL.parent.parent)).stdout.strip()
    n_cores = psutil.cpu_count(logical=True)
    env_overrides = {k: v for k, v in os.environ.items()
                     if k.startswith(("W0E_", "CLIP", "ROUTE_", "SEAT_", "PERCLIP", "C1_", "SOLVER"))}
    cmd = [sys.executable, str(Path(__file__).resolve()), "--workload"]
    r = {
        "MARK": "D0_CALIBRATION_ONLY -- not evidence for B-accept or N-adoption; E0 re-runs N=1 fresh",
        "protocol": {"commit_sha": code_sha, "command": " ".join(cmd), "CUDA_VISIBLE_DEVICES": _CVD,
                     "world_count": 1, "workload": f"FF-replay zero-residual RL steps [0,{WINDOW_END})",
                     "warmup_steps": WARMUP_STEPS, "window": [WARMUP_STEPS, WINDOW_END],
                     "sampling_cadence_s": CADENCE_S, "cpu_normalization": f"sum(proc-tree cpu%) / {n_cores} cores",
                     "recording": str(GOLDEN_NPZ), "env_overrides_present": env_overrides},
        "before": [], "during": [], "after": [], "phases_seen": [],
    }

    # BEFORE control (child absent): global GPU used + compute-apps snapshot
    for _ in range(2):
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout.strip().splitlines()
        r["before"].append({"t": time.time(), "gpu_used_mib_all": [int(x) for x in out]})
        time.sleep(1.0)

    STATUS.unlink(missing_ok=True)
    child = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    ps_child = psutil.Process(child.pid)
    ps_child.cpu_percent(interval=None)  # prime the cpu% counter

    while child.poll() is None:
        time.sleep(CADENCE_S)
        st = {}
        try:
            st = json.loads(STATUS.read_text()) if STATUS.exists() else {}
        except Exception:  # noqa: BLE001
            st = {}
        phase = st.get("phase", "init")
        rss_mb, thr, cpu = _tree_stats(child.pid)
        gpu = _gpu_pid_mib(child.pid)
        r["during"].append({"t": time.time(), "phase": phase, "step": st.get("step"),
                            "gpu_pid_mib": gpu, "tree_rss_mb": rss_mb, "threads": thr,
                            "cpu_pct_norm": (cpu / n_cores) if cpu is not None else None})
        if phase not in r["phases_seen"]:
            r["phases_seen"].append(phase)
    rc = child.returncode

    # AFTER control (child absent again)
    time.sleep(2.0)
    ga = _gpu_pid_mib(child.pid)
    r["after"].append({"t": time.time(), "gpu_pid_mib_for_dead_pid": ga})

    st = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    r["workload_exit"] = rc
    r["use_mujoco_cpu_observed"] = st.get("use_mujoco_cpu")

    # ---- aggregate (fail-loud on missing samples) ----
    win = [s for s in r["during"] if s["phase"] == "window"]
    wu = [s for s in r["during"] if s["phase"] in ("warmup", "init")]
    gpu_ok = [s["gpu_pid_mib"] for s in win if s["gpu_pid_mib"] is not None]
    rss_ok = [s["tree_rss_mb"] for s in win if s["tree_rss_mb"] is not None]
    cpu_ok = [s["cpu_pct_norm"] for s in win if s["cpu_pct_norm"] is not None]
    thr_ok = [s["threads"] for s in win if s["threads"] is not None]
    errors = []
    if rc != 0:
        errors.append(f"workload exit {rc} (3=early_done)")
    if not win:
        errors.append("ZERO window-phase samples")
    if not gpu_ok or max(gpu_ok) == 0:
        errors.append("no PID-attributed GPU samples in window (attribution failed)")
    if not rss_ok or not cpu_ok:
        errors.append("missing RSS/CPU samples in window")
    if cpu_ok and max(cpu_ok) == 0.0:
        errors.append("CPU instrument DEAD (0.0-flat on a CPU-bound workload -- positive control failed)")
    if errors:
        r["FAIL_LOUD"] = errors
    else:
        base_gpu = min([min((s["gpu_pid_mib"] for s in wu if s["gpu_pid_mib"]), default=min(gpu_ok))] + gpu_ok)
        r["profile"] = {
            "gpu_mib": {"baseline_min": base_gpu, "window_mean": round(sum(gpu_ok) / len(gpu_ok), 1),
                        "peak": max(gpu_ok), "delta_peak_minus_baseline": max(gpu_ok) - base_gpu},
            "tree_rss_mb": {"window_mean": round(sum(rss_ok) / len(rss_ok), 1), "peak": round(max(rss_ok), 1)},
            "cpu_pct_norm": {"window_mean": round(sum(cpu_ok) / len(cpu_ok), 2), "peak": round(max(cpu_ok), 2)},
            "threads": {"window_max": max(thr_ok)},
            "n_window_samples": len(win),
        }
    OUT.write_text(json.dumps(r, indent=2))
    print(json.dumps({k: r[k] for k in ("MARK", "workload_exit", "use_mujoco_cpu_observed", "phases_seen")}, indent=1))
    print(json.dumps(r.get("profile", {"FAIL_LOUD": r.get("FAIL_LOUD")}), indent=1))
    print(f"[D0-cal] -> {OUT}")
    return 0 if "profile" in r else 2


if __name__ == "__main__":
    sys.exit(main())
