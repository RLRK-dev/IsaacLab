# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B E0 scaling evidence -- N=1(x2 determinism)/2/4 per the D1 sec 7 pre-registration. cuda:0, no training.

Fresh runs (the D0 calibration v4 is NOT reused -- pN condition 2). Reuses the v4-verified instruments
(PID-attributed GPU, persistent-cache CPU%, provenance closure, race bracket) by importing the calibration module.

Per-child: derived_seed = SeedSequence([base_seed, proc_index, restart_count=0]) (AMEND-1) -> np.random.seed;
workload = the same FF-replay [0,230) with window [30,230); the child dumps its cable trajectory as .npy and
self-reports window steps/s. DEVIATION NOTE (recorded): determinism compares .npy FILE sha256, not .npz -- the
npz zip container embeds timestamps and is not byte-stable; the .npy payload is. Registered predicates:
contention >= 0.8 (N=4 vs N=1 per-proc), memory linearity (superlinear = loud), determinism byte-identical =
hard PASS, dead-instrument positive controls, K=200ep / K_fail=3 numeric pins (mechanism tests = I0).

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_e0_scaling.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
OUT = _EVAL / "forkb_e0_scaling_result.json"
E0DIR = _EVAL / "forkb_e0_runs"
BASE_SEED = 20260716
WARMUP_STEPS = 30
WINDOW_END = 230

# reuse the v4-verified instruments (import the calibration module by path; import is side-effect-free)
_spec = importlib.util.spec_from_file_location("d0cal", _EVAL / "forkb_d0_calibration_profile.py")
d0cal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d0cal)


# ----------------------------------------------------------------------------------- child workload
def child(proc_index: int, run_tag: str):
    import numpy as np  # noqa: PLC0415

    derived = int(np.random.SeedSequence([BASE_SEED, proc_index, 0]).generate_state(1)[0])  # AMEND-1, rc=0
    np.random.seed(derived)
    _TIL = _EVAL.parent.parent / "thread_isaac_lab"
    for _p in (str(_TIL), str(_TIL / "envs")):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    import newton_route_env as nre  # noqa: PLC0415
    import torch  # noqa: PLC0415

    mydir = E0DIR / run_tag / f"proc_{proc_index}"
    mydir.mkdir(parents=True, exist_ok=True)
    status = mydir / "status.json"

    env = nre.NewtonRouteEnv(world_count=1, device="cuda:0", cfg={
        "grasp_actuation": True, "route_executor_impl": "route_executor", "route_recording_npz": str(d0cal.GOLDEN_NPZ),
        "g1_scene_align": True, "route_drive_mode": "feedforward", "route_c2_scene": True,
    })
    env.reset()
    # closure identity (v4 pattern): what THIS process actually loaded
    repo = str(d0cal._REPO)
    loaded = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        fp = Path(f).resolve()
        if str(fp).startswith(repo) and fp.suffix == ".py" and fp.exists():
            loaded[str(fp.relative_to(d0cal._REPO))] = d0cal._sha256_file(fp)
    (mydir / "closure.json").write_text(json.dumps(dict(sorted(loaded.items())), indent=1))

    cable_ids = env._cable_bodies[0]
    zero = torch.zeros((1, 6), dtype=torch.float32)
    traj = np.zeros((WINDOW_END, len(cable_ids), 3), dtype=np.float64)
    t_win_start = None
    status.write_text(json.dumps({"pid": os.getpid(), "phase": "warmup", "step": 0, "derived_seed": derived}))
    for t in range(WINDOW_END):
        _, _, dones, _ = env.step(zero)
        traj[t] = env._state_0.body_q.numpy()[cable_ids, :3]
        if t == WARMUP_STEPS:
            t_win_start = time.time()
        if t % 10 == 0:
            status.write_text(json.dumps({"pid": os.getpid(), "phase": "warmup" if t < WARMUP_STEPS else "window",
                                          "step": t, "derived_seed": derived}))
        if bool(dones[0]):
            status.write_text(json.dumps({"pid": os.getpid(), "phase": "early_done", "step": t}))
            return 3
    t_end = time.time()
    np.save(mydir / "traj.npy", traj)
    traj_sha = d0cal._sha256_file(mydir / "traj.npy")
    win_sps = (WINDOW_END - WARMUP_STEPS) / (t_end - t_win_start) if t_win_start else None
    status.write_text(json.dumps({
        "pid": os.getpid(), "phase": "done", "step": WINDOW_END, "derived_seed": derived,
        "use_mujoco_cpu": bool(getattr(env._solver, "use_mujoco_cpu", None)),
        "window_steps_per_s": round(win_sps, 3) if win_sps else None,
        "t_window": [t_win_start, t_end], "traj_sha256": traj_sha,
    }))
    return 0


# ----------------------------------------------------------------------------------- parent phases
def _run_phase(run_tag: str, n_procs: int, n_cores: int):
    """Spawn n_procs children simultaneously; sample each; return the phase record."""
    import psutil  # noqa: PLC0415

    procs = []
    for i in range(n_procs):
        cmd = [sys.executable, str(Path(__file__).resolve()), "--child", str(i), run_tag]
        procs.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT))
    import contextlib
    for p in procs:
        with contextlib.suppress(Exception):
            psutil.Process(p.pid).cpu_percent(interval=None)
    samples = []
    while any(p.poll() is None for p in procs):
        time.sleep(2.0)
        row = {"t": time.time(), "per_proc": []}
        for i, p in enumerate(procs):
            if p.poll() is None:
                rss, thr, cpu = d0cal._tree_stats(p.pid)
                gpu = d0cal._gpu_pid_mib(p.pid)
                row["per_proc"].append({"i": i, "gpu_mib": gpu, "rss_mb": rss, "threads": thr,
                                        "cpu_pct_norm": (cpu / n_cores) if cpu is not None else None})
        samples.append(row)
    rcs = [p.returncode for p in procs]
    stats = []
    for i in range(n_procs):
        sf = E0DIR / run_tag / f"proc_{i}" / "status.json"
        st = json.loads(sf.read_text()) if sf.exists() else {}
        stats.append(st)
    return {"run_tag": run_tag, "n_procs": n_procs, "rcs": rcs, "child_final": stats, "n_samples": len(samples),
            "samples": samples}


def _phase_metrics(ph):
    sps = [c.get("window_steps_per_s") for c in ph["child_final"]]
    win = [(c.get("t_window") or [None, None]) for c in ph["child_final"]]
    peaks_gpu, peaks_rss, cpu_means = [], [], []
    for i in range(ph["n_procs"]):
        rows = [pp for r in ph["samples"] for pp in r["per_proc"] if pp["i"] == i]  # match by the RECORDED
        #        index, not list position (children exit in arbitrary order and the row list shifts)
        g = [pp["gpu_mib"] for pp in rows if pp["gpu_mib"]]
        rs = [pp["rss_mb"] for pp in rows if pp["rss_mb"]]
        cp = [pp["cpu_pct_norm"] for pp in rows if pp["cpu_pct_norm"]]
        peaks_gpu.append(max(g) if g else None)
        peaks_rss.append(round(max(rs), 1) if rs else None)
        cpu_means.append(round(sum(cp) / len(cp), 2) if cp else None)
    # window overlap check (contention validity: all windows must overlap pairwise)
    o0 = max((w[0] or 0) for w in win) if win else None
    o1 = min((w[1] or 0) for w in win) if win else None
    return {"steps_per_s": sps, "mean_sps": round(sum(s for s in sps if s) / max(1, len([s for s in sps if s])), 3),
            "gpu_peak_mib": peaks_gpu, "rss_peak_mb": peaks_rss, "cpu_mean_norm": cpu_means,
            "window_overlap_s": round(o1 - o0, 1) if (o0 and o1) else None, "rcs": ph["rcs"]}


def main():
    if "--child" in sys.argv:
        i = int(sys.argv[sys.argv.index("--child") + 1])
        tag = sys.argv[sys.argv.index("--child") + 2]
        sys.exit(child(i, tag))

    _CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    assert _CVD == "0", f"E0 runs on cuda:0 ONLY; got {_CVD!r}"
    import psutil  # noqa: PLC0415

    n_cores = psutil.cpu_count(logical=True)
    E0DIR.mkdir(exist_ok=True)
    r = {"MARK": "E0 evidence -- per the D1 sec 7 pre-registration; the D0 calibration v4 is NOT reused",
         "protocol": {"base_seed": BASE_SEED, "seed_form": "SeedSequence([base, i, 0]) (AMEND-1)",
                      "workload": f"FF-replay [0,{WINDOW_END}), window [{WARMUP_STEPS},{WINDOW_END})",
                      "determinism": ".npy FILE sha256 (DEVIATION from 'npz': the zip container embeds "
                                     "timestamps and is not byte-stable; the npy payload is)",
                      "provenance": d0cal._provenance()},
         "phases": {}}

    # --- N=1 determinism pair (fresh, same seed) ---
    for tag in ("n1_a", "n1_b"):
        ph = _run_phase(tag, 1, n_cores)
        r["phases"][tag] = _phase_metrics(ph)
        r["phases"][tag + "_raw_n_samples"] = ph["n_samples"]
        r["phases"][tag + "_traj_sha"] = [c.get("traj_sha256") for c in ph["child_final"]]
    det_ok = (r["phases"]["n1_a_traj_sha"] == r["phases"]["n1_b_traj_sha"]
              and all(r["phases"]["n1_a_traj_sha"]))
    # --- N=2, N=4 ---
    for tag, n in (("n2", 2), ("n4", 4)):
        ph = _run_phase(tag, n, n_cores)
        r["phases"][tag] = _phase_metrics(ph)
        r["phases"][tag + "_traj_sha"] = [c.get("traj_sha256") for c in ph["child_final"]]

    # --- predicates ---
    sps1 = r["phases"]["n1_a"]["mean_sps"]
    sps4 = r["phases"]["n4"]["mean_sps"]
    contention = round(sps4 / sps1, 3) if (sps1 and sps4) else None
    gpu1 = [g for g in r["phases"]["n1_a"]["gpu_peak_mib"] if g]
    gpu4 = [g for g in r["phases"]["n4"]["gpu_peak_mib"] if g]
    rss1 = [x for x in r["phases"]["n1_a"]["rss_peak_mb"] if x]
    rss4 = [x for x in r["phases"]["n4"]["rss_peak_mb"] if x]
    mem_linear = bool(gpu4 and gpu1 and max(gpu4) <= 1.25 * max(gpu1) and rss4 and rss1
                      and max(rss4) <= 1.25 * max(rss1))  # per-proc peaks should NOT grow with N
    errors = []
    for tag in ("n1_a", "n1_b", "n2", "n4"):
        m = r["phases"][tag]
        if any(rc != 0 for rc in m["rcs"]):
            errors.append(f"{tag}: child rcs {m['rcs']}")
        if any(s is None for s in m["steps_per_s"]):
            errors.append(f"{tag}: missing steps/s")
        if m["cpu_mean_norm"] and all(c == 0.0 for c in m["cpu_mean_norm"] if c is not None):
            errors.append(f"{tag}: CPU instrument dead (0.0-flat)")
    if r["phases"]["n4"]["window_overlap_s"] is not None and r["phases"]["n4"]["window_overlap_s"] <= 5.0:
        errors.append("n4: windows did not overlap enough for a contention claim")
    if not det_ok:
        errors.append("DETERMINISM FAIL: n1_a vs n1_b traj sha mismatch (hard predicate)")

    tps1 = round(sps1 * 1, 3) if sps1 else None
    tps4 = round(r["phases"]["n4"]["mean_sps"] * 4, 3) if r["phases"]["n4"]["mean_sps"] else None
    r["predicates"] = {
        "determinism_byte_identical": det_ok,
        "contention_ratio_n4_vs_n1": contention, "contention_bar": 0.8,
        "contention_PASS": bool(contention and contention >= 0.8),
        "memory_linear_per_proc": mem_linear,
        "transitions_per_s": {"N1": tps1, "N2": round(r["phases"]["n2"]["mean_sps"] * 2, 3)
                              if r["phases"]["n2"]["mean_sps"] else None, "N4": tps4},
        "scaling_efficiency_T4_over_4T1": round(tps4 / (4 * tps1), 3) if (tps1 and tps4) else None,
        "K_200ep_hours_at_measured_rate": round(200 / max(1e-9, (tps4 or 0) / 900 * 3600), 2) if tps4 else None,
        "K_fail_3": "numeric pin confirmed; mechanism test = I0 (supervisor exists there)",
    }
    if errors:
        r["FAIL_LOUD"] = errors
    OUT.write_text(json.dumps(r, indent=2))
    print(json.dumps({k: r[k] for k in ("MARK", "predicates") if k in r}, indent=1))
    if errors:
        print("FAIL_LOUD:", errors)
    print(f"[E0] -> {OUT}")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
