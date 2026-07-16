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
CLOSURE = _EVAL / "forkb_d0_calibration_closure.json"  # v4: the child's ACTUAL import closure + load-time sha
OUT = _EVAL / "forkb_d0_calibration_profile_result.json"
GOLDEN_NPZ = _EVAL / "w0e_81rerun_snapdown_0537" / "cell_x0_y0" / "route_demo_raw.npz"

# v4 (OPS-SUP v3-HOLD finding 2): the recorder's EXPLICIT core (route_demo_recorder.py:330-350, verbatim 19)
# -- the fingerprint is explicit-core UNION loaded-source scrape, per the b7553662a4 mechanism.
_EXPLICIT_ENV_CORE = (
    "DEMO_RECORD", "S6_GRASP_ROUTE", "S13_ROUTE_C2", "SEAT_TOPDOWN", "C2_DUALSEAT", "PERCLIP_PIN",
    "CLIP_FLOAT_Z", "SPACER", "CLIP2", "CLIP_COLLISION", "CLIP_X", "CLIP_Y", "CLIP2_X", "CLIP2_Y",
    "C2_TILT_SIGN", "S6_ENGAGE_YC", "NEWTON_DEVICE", "CUDA_VISIBLE_DEVICES", "CABLE_XY_OFFSET",
)


def _sha256_file(p):
    import hashlib

    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _scrape_env_keys(paths):
    """Every env var the given sources read (recorder pattern b7553662a4 _env_keys_read_by)."""
    import re

    keys = set()
    for p in paths:
        try:
            src = Path(p).read_text(errors="replace")
        except OSError:
            continue
        keys.update(re.findall(r'os\.environ\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']', src))
        keys.update(re.findall(r'os\.environ\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]', src))
    return keys

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
    # v4 (OPS-SUP v3-HOLD findings 1/4): the ACTUAL import closure, auto-enumerated from THIS process's
    # sys.modules (no hand-list to rot) + sha256 at load time (what this process runs is what it hashed).
    repo = str(_REPO)
    loaded = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        fp = Path(f).resolve()  # some modules carry a RELATIVE __file__ (e.g. '_ops.py') -- resolve() then
        #                         maps them spuriously under CWD; the exists() check drops those phantoms.
        if str(fp).startswith(repo) and fp.suffix == ".py" and fp.exists():
            loaded[str(fp.relative_to(_REPO))] = _sha256_file(fp)
    CLOSURE.write_text(json.dumps({
        "loaded_repo_modules_sha256": dict(sorted(loaded.items())),
        "scraped_env_keys": sorted(_scrape_env_keys([_REPO / rel for rel in loaded])),
    }, indent=1))
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


_REPO = _EVAL.parent.parent
_SRC_FILES = [  # the sources the workload actually imports -- as-run identity (the recorded HEAD sha alone
    #             does NOT identify a dirty tree: OPS-SUP E0-fence HOLD finding 1, 2026-07-16)
    _REPO / "thread_isaac_lab/envs/newton_route_env.py",
    _REPO / "thread_isaac_lab/envs/route_executor.py",
    _REPO / "thread_isaac_lab/envs/route_env_config.py",
    _REPO / "thread_isaac_lab/envs/newton_skill_env_base.py",
    _REPO / "thread_isaac_lab/configs/task_config.py",
    Path(__file__).resolve(),
]


def _provenance():
    """git head + dirty state + as-run source sha256 + the scraped env fingerprint (recorder pattern
    b7553662a4: every env the pinned sources read, not a hand-written subset) + machine denominators."""
    import hashlib
    import re

    def _git(*args):
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=str(_REPO)).stdout.strip()

    as_run = {}
    env_keys = set()
    for p in _SRC_FILES:
        src = p.read_text(errors="replace")
        as_run[str(p.relative_to(_REPO))] = hashlib.sha256(src.encode()).hexdigest()
        env_keys.update(re.findall(r'os\.environ\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']', src))
        env_keys.update(re.findall(r'os\.environ\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]', src))
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.total,memory.used,memory.free",
                          "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.strip()
    mem = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k = line.split(":")[0]
        if k in ("MemTotal", "MemAvailable"):
            mem[k] = line.split()[1] + " kB"
    import psutil  # noqa: PLC0415
    dirty_all = _git("status", "--short")
    rels = [str(p.relative_to(_REPO)) for p in _SRC_FILES]
    return {
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty_total_lines": len(dirty_all.splitlines()) if dirty_all else 0,
        "git_dirty_as_run_files": _git("diff", "--stat", "HEAD", "--", *rels) or "(as_run set clean vs HEAD)",
        "as_run_sha256_static_prelaunch": as_run,
        "recording_sha256": _sha256_file(GOLDEN_NPZ),  # v4 finding 3: the workload INPUT is pinned too
        "static_scraped_env_keys": sorted(env_keys),
        "denominators": {"gpu_mib(index,total,used,free)": gpu.splitlines(), "meminfo": mem,
                         "cpu_cores_logical": psutil.cpu_count(logical=True),
                         "cpu_cores_physical": psutil.cpu_count(logical=False)},
    }


def main():
    if "--workload" in sys.argv:
        sys.exit(workload())

    _CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    assert _CVD == "0", f"protocol fixes CUDA_VISIBLE_DEVICES=0; got {_CVD!r}"
    import psutil  # noqa: PLC0415

    n_cores = psutil.cpu_count(logical=True)
    cmd = [sys.executable, str(Path(__file__).resolve()), "--workload"]
    r = {
        "MARK": "D0_CALIBRATION_ONLY -- not evidence for B-accept or N-adoption; E0 re-runs N=1 fresh",
        "protocol": {"command": " ".join(cmd), "CUDA_VISIBLE_DEVICES": _CVD,
                     "world_count": 1, "workload": f"FF-replay zero-residual RL steps [0,{WINDOW_END})",
                     "warmup_steps": WARMUP_STEPS, "window": [WARMUP_STEPS, WINDOW_END],
                     "sampling_cadence_s": CADENCE_S, "cpu_normalization": f"sum(proc-tree cpu%) / {n_cores} cores",
                     "recording": str(GOLDEN_NPZ),
                     "provenance": _provenance()},
        "before": [], "during": [], "after": [], "phases_seen": [],
    }

    # BEFORE control (child absent): global GPU used + compute-apps snapshot
    for _ in range(2):
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout.strip().splitlines()
        r["before"].append({"t": time.time(), "gpu_used_mib_all": [int(x) for x in out]})
        time.sleep(1.0)

    STATUS.unlink(missing_ok=True)
    CLOSURE.unlink(missing_ok=True)
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

    # ---- v4 (findings 1/2/4): closure identity + unified fingerprint + pre/post race bracket ----
    closure = json.loads(CLOSURE.read_text()) if CLOSURE.exists() else {}
    loaded = closure.get("loaded_repo_modules_sha256", {})
    changed = []
    post = {}
    for rel, load_sha in loaded.items():
        p = _REPO / rel
        post[rel] = _sha256_file(p) if p.exists() else "(deleted)"
        if post[rel] != load_sha:
            changed.append(rel)
    npz_post = _sha256_file(GOLDEN_NPZ)
    if npz_post != r["protocol"]["provenance"]["recording_sha256"]:
        changed.append(str(GOLDEN_NPZ.relative_to(_REPO)))
    fp_keys = set(_EXPLICIT_ENV_CORE) | set(closure.get("scraped_env_keys", [])) \
        | set(r["protocol"]["provenance"].pop("static_scraped_env_keys", []))
    r["protocol"]["provenance"].update({
        "loaded_closure_sha256_at_load": loaded,
        "loaded_closure_n": len(loaded),
        "post_run_sha256": post,
        "changed_during_run": changed,  # expect [] -- a nonempty list means the run raced a writer
        "env_fingerprint": {k: os.environ.get(k) for k in sorted(fp_keys)},
        "env_fingerprint_source": "explicit core (route_demo_recorder.py:330-350, 19) UNION scrape over the "
                                  "child's ACTUAL loaded closure (sys.modules) UNION static-set scrape "
                                  "(b7553662a4 mechanism)",
    })

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
    if not loaded:
        errors.append("closure MISSING (child never wrote the loaded-modules identity)")
    if changed:
        errors.append(f"RACE: sources/input changed during the run: {changed}")
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
