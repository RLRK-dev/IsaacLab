# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""fork-B E0v2a -- full fresh re-run resolving the pN E0v2 re-judgment blockers B6/B7 (v2 artifacts untouched).

Concrete deltas over v2 (the prior-art disposition -- NOT the same failed path):
(1) the CPU-dead predicate is ONE shared helper (_cpu_dead) called by BOTH the live check and the injected
selftest subprocess -- the selftest now exercises the production detector, not a reimplementation (B7);
(2) the dead-PID GPU=0 control is measured and artifacted with fail-loud (B7/D1 :111);
(3) per-child POST-run sha maps for closure+recording+harness with per-child changed_during_run=[] -- a
recording change is exit2 (B6/D1 :110); (4) explicit required-field checks per child (missing = exit2).

All four phases fresh (n1_a, n1_b, n2, n4); the v1 artifacts (forkb_e0_runs/, forkb_e0_scaling_result.json)
are NOT touched. Deltas over v1, all pinned pre-run in D1 v0.3 sec 7/7.1 (bank 3a14e38c17/c79d066109):
monotonic_ns timer with a strict 199-step window; contention basis = the n1 pair mean (fixed here, pre-run);
per-child unified 67-key fingerprint VALUES (explicit core U closure scrape U static scrape) with the n1 pair
value-match as a hard condition; per-child recording sha + load-time closure hashes + parent post-run re-hash
(changed_during_run must be []); trajectory finite (ALL elements) and nontrivial (max_t |q(t)-q(0)| > 1e-6 m);
memory bars: max(N4 per-proc peak) <= 1.25 x max(n1_a, n1_b peak) per axis (GPU, RSS); n4 overlap > 5.0 s;
an INJECTED CPU-zero self-test in a SEPARATE subprocess whose expected exit-2 marks the detector alive without
failing the real run; harness source self-hash pre/post match. Every predicate failure escalates to errors and
overall exit 2.

Run (cuda:0 pinned):
    CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
        eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_e0v2_scaling.py
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
OUT = _EVAL / "forkb_e0v2a_scaling_result.json"
E0DIR = _EVAL / "forkb_e0v2a_runs"
BASE_SEED = 20260716
WARMUP_STEPS = 30
WINDOW_END = 230
WINDOW_STEPS = 199  # strict: t_win_start is taken AFTER step 30 completes -> the interval spans steps 31..229

_spec = importlib.util.spec_from_file_location("d0cal", _EVAL / "forkb_d0_calibration_profile.py")
d0cal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d0cal)


def _unified_fingerprint(closure_paths):
    """The v4 67-key mechanism: explicit core U scrape(actual loaded closure) U scrape(static set)."""
    keys = set(d0cal._EXPLICIT_ENV_CORE)
    keys |= d0cal._scrape_env_keys(closure_paths)
    keys |= d0cal._scrape_env_keys(d0cal._SRC_FILES)
    return {k: os.environ.get(k) for k in sorted(keys)}


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

    env = nre.NewtonRouteEnv(
        world_count=1,
        device="cuda:0",
        cfg={
            "grasp_actuation": True,
            "route_executor_impl": "route_executor",
            "route_recording_npz": str(d0cal.GOLDEN_NPZ),
            "g1_scene_align": True,
            "route_drive_mode": "feedforward",
            "route_c2_scene": True,
        },
    )
    env.reset()
    repo = str(d0cal._REPO)
    loaded = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        fp = Path(f).resolve()
        if str(fp).startswith(repo) and fp.suffix == ".py" and fp.exists():
            loaded[str(fp.relative_to(d0cal._REPO))] = d0cal._sha256_file(fp)
    prov = {
        "loaded_closure_sha256_at_load": dict(sorted(loaded.items())),
        "env_fingerprint": _unified_fingerprint([d0cal._REPO / rel for rel in loaded]),
        "recording_sha256": d0cal._sha256_file(d0cal.GOLDEN_NPZ),
        "derived_seed": derived,
        "pid": os.getpid(),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    (mydir / "provenance.json").write_text(json.dumps(prov, indent=1))

    cable_ids = env._cable_bodies[0]
    zero = torch.zeros((1, 6), dtype=torch.float32)
    traj = np.zeros((WINDOW_END, len(cable_ids), 3), dtype=np.float64)
    t_win_start_ns = None
    status = mydir / "status.json"
    status.write_text(json.dumps({"pid": os.getpid(), "phase": "warmup", "step": 0}))
    for t in range(WINDOW_END):
        _, _, dones, _ = env.step(zero)
        traj[t] = env._state_0.body_q.numpy()[cable_ids, :3]
        if t == WARMUP_STEPS:  # AFTER step 30 completes -> window spans steps 31..229 = 199 (D1 v0.3 pinned form)
            t_win_start_ns = time.monotonic_ns()
        if t % 10 == 0:
            status.write_text(
                json.dumps({"pid": os.getpid(), "phase": "warmup" if t < WARMUP_STEPS else "window", "step": t})
            )
        if bool(dones[0]):
            status.write_text(json.dumps({"pid": os.getpid(), "phase": "early_done", "step": t}))
            return 3
    t_end_ns = time.monotonic_ns()
    # trajectory checks (child-side; the parent re-verifies from the npy)
    finite_all = bool(np.isfinite(traj).all())
    nontrivial = bool(np.max(np.linalg.norm(traj - traj[0], axis=-1)) > 1e-6)
    np.save(mydir / "traj.npy", traj)
    win_sps = WINDOW_STEPS / ((t_end_ns - t_win_start_ns) / 1e9) if t_win_start_ns else None
    status.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "phase": "done",
                "step": WINDOW_END,
                "use_mujoco_cpu": bool(getattr(env._solver, "use_mujoco_cpu", None)),
                "window_steps_per_s": round(win_sps, 3) if win_sps else None,
                "t_window_ns": [t_win_start_ns, t_end_ns],
                "t_window_wall": [time.time() - (t_end_ns - t_win_start_ns) / 1e9, time.time()],
                "traj_sha256": d0cal._sha256_file(mydir / "traj.npy"),
                "traj_finite_all": finite_all,
                "traj_nontrivial_1e6": nontrivial,
            }
        )
    )
    return 0


# ----------------------------------------------------------------------------------- detector (single source)
def _cpu_dead(samples):
    """THE production dead-CPU predicate -- the live check and the injected selftest both call THIS function
    (B7: testing a reimplementation proves the copy, not the wiring)."""
    vals = [c for c in samples if c is not None]
    return bool(vals and max(vals) == 0.0)


def selftest_cpuzero():
    """Injected self-test: feed the PRODUCTION predicate an all-zero series; it must fire (exit 2)."""
    sys.exit(2 if _cpu_dead([0.0] * 12) else 0)


# ----------------------------------------------------------------------------------- parent
def _run_phase(run_tag, n_procs, n_cores):
    import contextlib  # noqa: PLC0415

    import psutil  # noqa: PLC0415

    procs = [
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--child", str(i), run_tag],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        for i in range(n_procs)
    ]
    for p in procs:
        with contextlib.suppress(Exception):
            psutil.Process(p.pid).cpu_percent(interval=None)
    samples = []
    while any(p.poll() is None for p in procs):
        time.sleep(2.0)
        row = []
        for i, p in enumerate(procs):
            if p.poll() is None:
                rss, thr, cpu = d0cal._tree_stats(p.pid)
                gpu = d0cal._gpu_pid_mib(p.pid)
                row.append(
                    {
                        "i": i,
                        "gpu_mib": gpu,
                        "rss_mb": rss,
                        "threads": thr,
                        "cpu_pct_norm": (cpu / n_cores) if cpu is not None else None,
                    }
                )
        samples.append(row)
    out = {"rcs": [p.returncode for p in procs], "final": [], "prov": [], "bracket": [], "samples_n": len(samples)}
    self_path = Path(__file__).resolve()
    for i in range(n_procs):
        base = E0DIR / run_tag / f"proc_{i}"
        out["final"].append(json.loads((base / "status.json").read_text()) if (base / "status.json").exists() else {})
        prov = json.loads((base / "provenance.json").read_text()) if (base / "provenance.json").exists() else {}
        out["prov"].append(prov)
        # (B6) per-child POST-run bracket: closure files + the recording + the harness self, re-hashed NOW
        post, changed = {}, []
        for rel, load_sha in (prov.get("loaded_closure_sha256_at_load") or {}).items():
            fp = d0cal._REPO / rel
            post[rel] = d0cal._sha256_file(fp) if fp.exists() else "(deleted)"
            if post[rel] != load_sha:
                changed.append(rel)
        rec_post = d0cal._sha256_file(d0cal.GOLDEN_NPZ)
        if prov.get("recording_sha256") and rec_post != prov["recording_sha256"]:
            changed.append("RECORDING:" + str(d0cal.GOLDEN_NPZ.name))
        harness_post = d0cal._sha256_file(self_path)
        bracket = {
            "post_run_sha256": post,
            "recording_post_sha256": rec_post,
            "harness_post_sha256": harness_post,
            "changed_during_run": changed,
        }
        (base / "post_bracket.json").write_text(json.dumps(bracket, indent=1))
        out["bracket"].append(bracket)

    def _per(i, key):
        return [pp[key] for r in samples for pp in r if pp["i"] == i and pp[key] is not None]

    out["gpu_peak"] = [max(_per(i, "gpu_mib"), default=None) for i in range(n_procs)]
    out["rss_peak"] = [round(max(_per(i, "rss_mb"), default=0.0), 1) or None for i in range(n_procs)]
    out["cpu_mean"] = [
        round(sum(_per(i, "cpu_pct_norm")) / max(1, len(_per(i, "cpu_pct_norm"))), 2)
        if _per(i, "cpu_pct_norm")
        else None
        for i in range(n_procs)
    ]
    wins = [(f.get("t_window_wall") or [None, None]) for f in out["final"]]
    o0 = max((w[0] or 0) for w in wins)
    o1 = min((w[1] or 0) for w in wins)
    out["overlap_s"] = round(o1 - o0, 1) if all(w[0] for w in wins) else None
    out["sps"] = [f.get("window_steps_per_s") for f in out["final"]]
    return out


def main():  # noqa: C901 (deliberate: every predicate check is inline so the source readback maps 1:1 to the pinned bars)
    if "--child" in sys.argv:
        i = int(sys.argv[sys.argv.index("--child") + 1])
        sys.exit(child(i, sys.argv[sys.argv.index("--child") + 2]))
    if "--selftest-cpuzero" in sys.argv:
        selftest_cpuzero()

    _CVD = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    assert _CVD == "0", f"E0v2 runs on cuda:0 ONLY; got {_CVD!r}"
    import psutil  # noqa: PLC0415

    self_path = Path(__file__).resolve()
    self_sha_pre = d0cal._sha256_file(self_path)
    n_cores = psutil.cpu_count(logical=True)
    E0DIR.mkdir(exist_ok=True)
    errors = []

    # injected dead-instrument self-test (separate subprocess; expected exit 2 = detector alive)
    st = subprocess.run([sys.executable, str(self_path), "--selftest-cpuzero"], capture_output=True)
    self_test_pass = st.returncode == 2
    if not self_test_pass:
        errors.append(f"SELF-TEST FAIL: injected CPU-zero subprocess exited {st.returncode} (expected 2)")

    r = {
        "MARK": "E0v2a evidence -- D1 v0.3 sec 7 + sec 7.1 exact bars (bank 3a14e38c17/c79d066109); v1 untouched",
        "protocol": {
            "base_seed": BASE_SEED,
            "seed_form": "SeedSequence([base, i, 0]) (AMEND-1)",
            "window": f"steps 31..229 = {WINDOW_STEPS} (monotonic_ns; t0 after step 30 completes)",
            "contention_basis": "mean(n1_a, n1_b) per-proc sps (pre-fixed)",
            "memory_bar": "max(N4 per-proc peak) <= 1.25 x max(n1_a, n1_b peak), per axis (GPU, RSS)",
            "overlap_bar_s": 5.0,
            "nontrivial_bar_m": 1e-6,
            "self_test_cpuzero_pass": self_test_pass,
            "harness_self_sha_pre": self_sha_pre,
            "provenance": d0cal._provenance(),
        },
        "phases": {},
    }

    dead_pid_control = None
    REQ_STATUS = ("window_steps_per_s", "t_window_ns", "traj_sha256", "traj_finite_all", "traj_nontrivial_1e6")
    REQ_PROV = ("loaded_closure_sha256_at_load", "env_fingerprint", "recording_sha256")
    for tag, n in (("n1_a", 1), ("n1_b", 1), ("n2", 2), ("n4", 4)):
        ph = _run_phase(tag, n, n_cores)
        r["phases"][tag] = ph
        if any(rc != 0 for rc in ph["rcs"]):
            errors.append(f"{tag}: child rcs {ph['rcs']}")
        if any(s is None for s in ph["sps"]):
            errors.append(f"{tag}: missing steps/s")
        if _cpu_dead(ph["cpu_mean"]):
            errors.append(f"{tag}: CPU instrument dead (0.0-flat)")
        # (B7) dead-PID GPU=0 control: the exited child must attribute 0 MiB (run once, after the first phase)
        if dead_pid_control is None:
            dead_pid = (ph["final"][0] or {}).get("pid")
            g = d0cal._gpu_pid_mib(int(dead_pid)) if dead_pid else None
            dead_pid_control = {"dead_pid": dead_pid, "gpu_mib_attributed": g, "PASS": g == 0}
            if g != 0:
                errors.append(f"DEAD-PID CONTROL FAIL: exited pid {dead_pid} attributed {g} MiB (expected 0)")
        # (B6) per-child bracket + (4) required-field checks
        for i in range(n):
            br = ph["bracket"][i] if i < len(ph["bracket"]) else {}
            if br.get("changed_during_run"):
                errors.append(f"{tag}/proc_{i}: RACE {br['changed_during_run']}")
            if not br.get("post_run_sha256"):
                errors.append(f"{tag}/proc_{i}: post-run bracket missing")
            fin, pv = ph["final"][i] or {}, ph["prov"][i] or {}
            for k in REQ_STATUS:
                if fin.get(k) is None:
                    errors.append(f"{tag}/proc_{i}: status field missing: {k}")
            for k in REQ_PROV:
                if not pv.get(k):
                    errors.append(f"{tag}/proc_{i}: provenance field missing: {k}")
        for i, f in enumerate(ph["final"]):
            if not f.get("traj_finite_all"):
                errors.append(f"{tag}/proc_{i}: trajectory not all-finite")
            if not f.get("traj_nontrivial_1e6"):
                errors.append(f"{tag}/proc_{i}: trajectory trivial (max disp <= 1e-6 m)")
        for i, pv in enumerate(ph["prov"]):
            if not pv.get("loaded_closure_sha256_at_load"):
                errors.append(f"{tag}/proc_{i}: closure missing")
            if not pv.get("env_fingerprint"):
                errors.append(f"{tag}/proc_{i}: fingerprint missing")

    # global roll-up of the per-child brackets (the per-child maps are the B6 requirement; this is a summary)
    r["changed_during_run_union"] = sorted(
        {
            c
            for tag in ("n1_a", "n1_b", "n2", "n4")
            for br in r["phases"][tag]["bracket"]
            for c in br.get("changed_during_run", [])
        }
    )
    r["dead_pid_control"] = dead_pid_control

    # determinism (hard): n1 pair traj sha match
    sha_a = [f.get("traj_sha256") for f in r["phases"]["n1_a"]["final"]]
    sha_b = [f.get("traj_sha256") for f in r["phases"]["n1_b"]["final"]]
    det = bool(sha_a and sha_a == sha_b and all(sha_a))
    if not det:
        errors.append(f"DETERMINISM FAIL: n1 pair traj sha {sha_a} vs {sha_b}")
    # fingerprint hard: n1 pair values identical
    fp_a = r["phases"]["n1_a"]["prov"][0].get("env_fingerprint") if r["phases"]["n1_a"]["prov"] else None
    fp_b = r["phases"]["n1_b"]["prov"][0].get("env_fingerprint") if r["phases"]["n1_b"]["prov"] else None
    if not (fp_a and fp_a == fp_b):
        errors.append("FINGERPRINT FAIL: n1 pair unified fingerprint values differ or missing")

    # contention (basis pre-fixed = n1 pair mean)
    n1_mean = None
    n1_vals = [s for s in (r["phases"]["n1_a"]["sps"] + r["phases"]["n1_b"]["sps"]) if s]
    if n1_vals:
        n1_mean = sum(n1_vals) / len(n1_vals)
    n4_sps = [s for s in r["phases"]["n4"]["sps"] if s]
    contention = round((sum(n4_sps) / len(n4_sps)) / n1_mean, 3) if (n1_mean and n4_sps) else None
    if contention is None or contention < 0.8:
        errors.append(f"CONTENTION FAIL: ratio {contention} < 0.8")
    # overlap
    if r["phases"]["n4"]["overlap_s"] is None or r["phases"]["n4"]["overlap_s"] <= 5.0:
        errors.append(f"OVERLAP FAIL: n4 overlap {r['phases']['n4']['overlap_s']} <= 5.0 s")

    # memory bars (sec 7.1 #1)
    def _bar(axis):
        n1p = [x for x in (r["phases"]["n1_a"][axis] + r["phases"]["n1_b"][axis]) if x]
        n4p = [x for x in r["phases"]["n4"][axis] if x]
        if not n1p or not n4p:
            errors.append(f"MEMORY FAIL: missing {axis} peaks")
            return None
        ok = max(n4p) <= 1.25 * max(n1p)
        if not ok:
            errors.append(f"MEMORY FAIL: {axis} max(N4)={max(n4p)} > 1.25 x max(n1)={max(n1p)}")
        return ok

    gpu_ok = _bar("gpu_peak")
    rss_ok = _bar("rss_peak")

    self_sha_post = d0cal._sha256_file(self_path)
    if self_sha_post != self_sha_pre:
        errors.append("HARNESS RACE: the harness source changed during the run")

    tps = {tag: round(sum(s for s in r["phases"][tag]["sps"] if s), 3) for tag in ("n1_a", "n1_b", "n2", "n4")}
    r["predicates"] = {
        "determinism_traj_npy_byte_identical": det,
        "fingerprint_n1_pair_match": bool(fp_a and fp_a == fp_b),
        "contention_ratio_vs_n1_pair_mean": contention,
        "contention_PASS": bool(contention and contention >= 0.8),
        "memory_gpu_bar_PASS": gpu_ok,
        "memory_rss_bar_PASS": rss_ok,
        "overlap_n4_s": r["phases"]["n4"]["overlap_s"],
        "self_test_cpuzero_pass": self_test_pass,
        "transitions_per_s": {"N1_pair_mean": round(n1_mean, 3) if n1_mean else None, "N2": tps["n2"], "N4": tps["n4"]},
        "scaling_efficiency": round(tps["n4"] / (4 * n1_mean), 3) if (n1_mean and tps["n4"]) else None,
        "K_200ep_hours_at_N4": round(200 / max(1e-9, tps["n4"] / 900 * 3600), 2) if tps["n4"] else None,
        "transferred_to_I0": "K/K_fail mechanisms + R2-4-b 2x2 + N-2 + N-3 (post-E0 amendments; not counted)",
    }
    r["harness_self_sha_post"] = self_sha_post
    if errors:
        r["FAIL_LOUD"] = errors
    OUT.write_text(json.dumps(r, indent=2, default=lambda o: None))
    print(json.dumps(r["predicates"], indent=1))
    if errors:
        print("FAIL_LOUD:", errors)
    print(f"[E0v2a] -> {OUT}")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
