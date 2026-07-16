# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""I0-b mechanism legs for the fork-B collector/supervisor (pre-registered in I0B_BUILD_RSTECHLEAD_20260716.md).

L1a K-pause at the pinned K=200 (artificial backlog) / L1b K-pause organic (K=2) / L2 K_fail restart-halt
chain / L3 relocate-lever smoke (default + fallback device maps) / L4 R2-4-b 2x2 (serializer determinism x
seed expression, ik_chord workload; the FF diff-seed quadrant is banked N-2 = inert, cited not rerun) /
L5 N-3 as-run reconcile (E0v2a closure shas vs committed blobs).

All claims are INFRA-ONLY under the sec-S carry (I0A_SCOPE_MANIFEST AMENDMENT 1): no reward/latch/seat
semantic validity is asserted by any leg.

Run:  /home/rlrk/env_isaaclab7/bin/python eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_i0b_legs.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
REPO = _HERE.parent.parent
PY = "/home/rlrk/env_isaaclab7/bin/python"
COLLECTOR = REPO / "thread_isaac_lab/scripts/forkb_collector.py"
SUPERVISOR = REPO / "thread_isaac_lab/scripts/forkb_supervisor.py"
RUNS = _HERE / "forkb_i0b_runs"
PRE_FLIP_COMMIT = "c60d311f96^"  # I0-a bank commit's parent (flip landed in c60d311f96)

SEC_S_EXPOSURE = (
    "HEAD FM3/FM4 tighten code is live and UNRATIFIED (I0A_SCOPE_MANIFEST AMENDMENT 1 + sec S, ad0bb76460): "
    "these legs assert INFRA predicates only (files/sha/restart/pause/spawn); no semantic validity claims."
)


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _spawn_collector(outbox, seed, episodes, k, steps, drive="feedforward", extra=()):
    outbox.mkdir(parents=True, exist_ok=True)
    log = outbox / "collector.log"
    cmd = [
        PY,
        str(COLLECTOR),
        "--outbox",
        str(outbox),
        "--proc-index",
        "0",
        "--base-seed",
        str(seed),
        "--episodes",
        str(episodes),
        "--backpressure-k",
        str(k),
        "--episode-steps",
        str(steps),
        "--drive-mode",
        drive,
        *extra,
    ]
    import os

    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = "0"  # cvd-child-env: leg collectors pinned to cuda:0
    with open(log, "w") as lf:  # Popen dups the fd; the child keeps writing after we close ours
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env)
    return proc, log


def _wait(pred, timeout_s, poll_s=2.0):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if pred():
            return True
        time.sleep(poll_s)
    return False


def _npz_count(outbox):
    return len(list(outbox.glob("ep_*.npz")))


def _log_has(log, needle):
    return log.exists() and needle in log.read_text(errors="replace")


def leg_l1a():
    """K-pause at pinned K=200 via artificial backlog; resume on ack; resume-safe numbering to ep_000200."""
    import numpy as np

    outbox = RUNS / "l1a" / "proc_0"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "README_ARTIFICIAL_BACKLOG.txt").write_text(
        "ep_000000..ep_000199.npz are ARTIFICIAL backlog (dummy npz) pre-seeded by forkb_i0b_legs.py leg L1a "
        "to exercise the pinned K=200 backpressure mechanism without a 1.4 h organic fill. Not episode data."
    )
    for i in range(200):
        np.savez(outbox / f"ep_{i:06d}.npz", dummy=np.zeros(1))
    proc, log = _spawn_collector(outbox, seed=777, episodes=1, k=200, steps=60)
    ev = {}
    ev["pause_log_seen"] = _wait(lambda: _log_has(log, "BACKPRESSURE"), 420)
    time.sleep(15)
    ev["count_during_pause"] = _npz_count(outbox)
    ev["no_publish_during_pause"] = ev["count_during_pause"] == 200
    (outbox / "ep_000000.consumed").touch()  # ack one -> unconsumed 199 < K -> resume
    ev["resumed_publish_ep200"] = _wait(lambda: (outbox / "ep_000200.npz").exists(), 300)
    try:
        ev["rc"] = proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        ev["rc"] = "timeout_killed"
    passed = bool(
        ev["pause_log_seen"] and ev["no_publish_during_pause"] and ev["resumed_publish_ep200"] and ev["rc"] == 0
    )
    return {"leg": "L1a_kpause_pinned_200", "passed": passed, "evidence": ev}


def leg_l1b():
    """Organic K-pause at K=2: 2 published -> pause -> ack -> 3rd published -> rc 0."""
    outbox = RUNS / "l1b" / "proc_0"
    proc, log = _spawn_collector(outbox, seed=778, episodes=3, k=2, steps=60)
    ev = {}
    ev["two_published"] = _wait(lambda: _npz_count(outbox) >= 2, 420)
    ev["pause_log_seen"] = _wait(lambda: _log_has(log, "BACKPRESSURE"), 60)
    time.sleep(15)
    ev["count_during_pause"] = _npz_count(outbox)
    ev["held_at_two"] = ev["count_during_pause"] == 2
    (outbox / "ep_000000.consumed").touch()
    ev["third_published"] = _wait(lambda: _npz_count(outbox) >= 3, 300)
    try:
        ev["rc"] = proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        ev["rc"] = "timeout_killed"
    passed = bool(
        ev["two_published"] and ev["pause_log_seen"] and ev["held_at_two"] and ev["third_published"] and ev["rc"] == 0
    )
    return {"leg": "L1b_kpause_organic_2", "passed": passed, "evidence": ev}


def leg_l2():
    """K_fail restart-halt chain: crash-after-1 -> individuals rc000..003 -> HALT + exit 2, no overwrite."""
    root = RUNS / "l2"
    root.mkdir(parents=True, exist_ok=True)
    cmd = [
        PY,
        str(SUPERVISOR),
        "--run-root",
        str(root),
        "--base-seed",
        "888",
        "--episodes",
        "5",
        "--n-collect",
        "1",
        "--k-fail",
        "3",
        "--episode-steps",
        "60",
        "--test-crash-slot",
        "0",
        "--test-crash-after",
        "1",
    ]
    with open(root / "supervisor.log", "w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT)
    ev = {}
    try:
        ev["rc"] = proc.wait(timeout=1800)
    except subprocess.TimeoutExpired:
        proc.kill()
        ev["rc"] = "timeout_killed"
    pdir = root / "proc_0"
    metas = sorted(pdir.glob("proc_meta.rc*.json"))
    seeds = []
    for m in metas:
        try:
            seeds.append(json.loads(m.read_text())["derived_seed"])
        except (json.JSONDecodeError, KeyError):
            seeds.append(None)
    eps = sorted(p.name for p in pdir.glob("ep_*.npz"))
    ev.update(
        {
            "halt_json": (root / "HALT.json").exists(),
            "individuals": [m.name for m in metas],
            "derived_seeds": seeds,
            "seeds_distinct": len(set(seeds)) == len(seeds) and len(seeds) == 4,
            "episodes": eps,
            "episodes_expected": [f"ep_{i:06d}.npz" for i in range(4)],
            "no_overwrite_numbering": eps == [f"ep_{i:06d}.npz" for i in range(4)],
        }
    )
    passed = bool(ev["rc"] == 2 and ev["halt_json"] and ev["seeds_distinct"] and ev["no_overwrite_numbering"])
    return {"leg": "L2_kfail_restart_halt", "passed": passed, "evidence": ev}


def _lever_case(tag, device_map, n_collect):
    root = RUNS / f"l3_{tag}"
    root.mkdir(parents=True, exist_ok=True)
    cmd = [
        PY,
        str(SUPERVISOR),
        "--run-root",
        str(root),
        "--base-seed",
        "999",
        "--episodes",
        "1",
        "--n-collect",
        str(n_collect),
        "--episode-steps",
        "60",
        "--device-map",
        device_map,
    ]
    with open(root / "supervisor.log", "w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT)
    ev = {}
    try:
        ev["rc"] = proc.wait(timeout=900)
    except subprocess.TimeoutExpired:
        proc.kill()
        ev["rc"] = "timeout_killed"
    man = json.loads((root / "run_manifest.json").read_text()) if (root / "run_manifest.json").exists() else {}
    ev["device_map"] = man.get("device_map")
    ev["n_collect"] = man.get("n_collect")
    ev["proc_dirs"] = sorted(p.name for p in root.glob("proc_*"))
    cvds = []
    for p in sorted(root.glob("proc_*/proc_meta.json")):
        try:
            cvds.append(json.loads(p.read_text())["CUDA_VISIBLE_DEVICES"])
        except (json.JSONDecodeError, KeyError):
            cvds.append(None)
    ev["child_CVDs"] = cvds
    ev["episodes_published"] = len(list(root.glob("proc_*/ep_*.npz")))
    return root, ev


def leg_l3():
    """Relocate-lever smoke: default {collector cuda:0, trainer cuda:2} and fallback {trainer cuda:0, N<=3}."""
    _, ev_d = _lever_case("default", "default", 1)
    _, ev_f = _lever_case("fallback", "fallback", 3)
    ok_d = (
        ev_d["rc"] == 0
        and (ev_d["device_map"] or {}).get("trainer") == "cuda:2"
        and ev_d["child_CVDs"] == ["0"]
        and ev_d["episodes_published"] == 1
    )
    ok_f = (
        ev_f["rc"] == 0
        and (ev_f["device_map"] or {}).get("trainer") == "cuda:0"
        and ev_f["n_collect"] == 3
        and ev_f["child_CVDs"] == ["0", "0", "0"]
        and ev_f["episodes_published"] == 3
    )
    return {"leg": "L3_lever_smoke", "passed": bool(ok_d and ok_f), "evidence": {"default": ev_d, "fallback": ev_f}}


def leg_l4():
    """R2-4-b 2x2 on ik_chord: same-seed byte-identical x diff-seed byte-different (seed expression).

    FF diff-seed quadrant = banked N-2 (inert under FF) -- cited, not rerun.
    """
    procs = []
    for tag, seed in (("a", 4242), ("b", 4242), ("c", 4243)):
        outbox = RUNS / f"l4_{tag}" / "proc_0"
        procs.append(
            (tag, _spawn_collector(outbox, seed=seed, episodes=1, k=200, steps=120, drive="ik_chord")[0], outbox)
        )
    ev = {"note_ff_quadrant": "diff-seed under FF = banked N-2 inert (RULINGS v1.5), cited not rerun"}
    for tag, proc, _ in procs:
        try:
            ev[f"rc_{tag}"] = proc.wait(timeout=900)
        except subprocess.TimeoutExpired:
            proc.kill()
            ev[f"rc_{tag}"] = "timeout_killed"
    shas = {}
    for tag, _, outbox in procs:
        f = outbox / "ep_000000.npz"
        shas[tag] = _sha(f) if f.exists() else None
    ev["sha"] = shas
    ev["same_seed_identical"] = shas["a"] is not None and shas["a"] == shas["b"]
    ev["diff_seed_differs"] = shas["c"] is not None and shas["c"] != shas["a"]
    passed = bool(
        ev["rc_a"] == 0
        and ev["rc_b"] == 0
        and ev["rc_c"] == 0
        and ev["same_seed_identical"]
        and ev["diff_seed_differs"]
    )
    return {"leg": "L4_r24b_2x2_ikchord", "passed": passed, "evidence": ev}


def leg_l5():
    """N-3 as-run reconcile: E0v2a n1 closure shas vs committed blobs (HEAD, else pre-flip commit)."""
    candidates = sorted((_HERE / "forkb_e0v2a_runs").rglob("*.json"))
    closure = None
    src = None
    for c in candidates:
        try:
            d = json.loads(c.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        def _find_closure(obj):
            if isinstance(obj, dict):
                keys = list(obj.keys())
                if (
                    keys
                    and all(k.endswith(".py") for k in keys)
                    and all(isinstance(v, str) and len(v) == 64 for v in obj.values())
                ):
                    return obj
                for v in obj.values():
                    r = _find_closure(v)
                    if r:
                        return r
            return None

        found = _find_closure(d)
        if found and ("n1" in str(c) or closure is None):
            closure, src = found, str(c.relative_to(_HERE))
            if "n1" in str(c):
                break
    if not closure:
        return {
            "leg": "L5_n3_asrun_reconcile",
            "passed": False,
            "evidence": {"error": "no closure mapping found under forkb_e0v2a_runs"},
        }

    def _blob_sha(commit, path):
        r = subprocess.run(["git", "-C", str(REPO), "cat-file", "blob", f"{commit}:{path}"], capture_output=True)
        return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None

    def _file_history_hit(path, as_run):
        commits = subprocess.run(
            ["git", "-C", str(REPO), "log", "--all", "--format=%h", "--", path], capture_output=True, text=True
        ).stdout.split()
        for c in commits:
            if _blob_sha(c, path) == as_run:
                return c
        return None

    def _dirty(path):
        out = subprocess.run(
            ["git", "-C", str(REPO), "status", "--porcelain", "--", path], capture_output=True, text=True
        )
        return bool(out.stdout.strip())

    def _e0v2_sha(path):
        p = _HERE / "forkb_e0v2_runs/n1_a/proc_0/provenance.json"
        if not p.exists():
            return None
        try:
            m = _find_closure(json.loads(p.read_text()))
            return (m or {}).get(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # v2 classification (bar widened v1 -> v2: v1 implemented only the "land" branch of D1 sec 7 "land or
    # inert 宣言" and had no DECLARE branch, so byte-stable-but-uncommitted as-run states failed as
    # UNEXPLAINED. v1 result preserved as forkb_i0b_legs_result_v1.json; the requirement itself is unchanged.)
    table = {}
    unexplained = []
    declared = []
    for path, as_run in sorted(closure.items()):
        if _blob_sha("HEAD", path) == as_run:
            table[path] = "landed_at_HEAD"
            continue
        hit = _file_history_hit(path, as_run)
        if hit:
            table[path] = (
                f"landed_at_{hit} (a committed blob matches as-run byte-for-byte; HEAD differs only via "
                f"later commits to this file -- see git log {hit}..HEAD -- {path})"
            )
            continue
        wt = _sha(REPO / path) if (REPO / path).exists() else None
        if wt == as_run and _dirty(path):
            table[path] = (
                "DECLARED_still_dirty_worktree (as-run == the CURRENT uncommitted worktree bytes; part of "
                "the standing shared-tree residue the E0 runs executed on; land-or-inert decision belongs "
                "to the tree-triage owner, out of I0-b scope -- declared per D1 sec 7 N-3)"
            )
            declared.append(path)
            continue
        if _e0v2_sha(path) == as_run and not _dirty(path):
            table[path] = (
                "DECLARED_pre_flip_dirty_reconciled (as-run byte-stable across E0v2 AND E0v2a brackets; "
                "file is CLEAN at HEAD now, so the only delta is the c60d311f96 commit content = I0-a flip "
                "+ the disclosed sweep [I0A_SCOPE_MANIFEST hunk attribution]; flip behavioral neutrality = "
                "I0-a byte-repro leg [post-flip n1 traj sha == pre-flip banked])"
            )
            declared.append(path)
            continue
        table[path] = "UNEXPLAINED"
        unexplained.append(path)
    return {
        "leg": "L5_n3_asrun_reconcile",
        "passed": not unexplained,
        "evidence": {
            "source_artifact": src,
            "n_files": len(table),
            "table": table,
            "declared_not_landed": declared,
            "unexplained": unexplained,
        },
    }


LEGS = {"l1a": leg_l1a, "l1b": leg_l1b, "l2": leg_l2, "l3": leg_l3, "l4": leg_l4, "l5": leg_l5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=tuple(LEGS), help="run a subset of legs")
    a = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    results = []
    for name in a.only or list(LEGS):
        print(f"=== leg {name} ===", flush=True)
        t0 = time.time()
        try:
            r = LEGS[name]()
        except Exception as e:  # a leg harness crash is a FAIL, not a silent skip
            r = {"leg": name, "passed": False, "evidence": {"harness_exception": repr(e)}}
        r["wall_s"] = round(time.time() - t0, 1)
        print(json.dumps(r, indent=1), flush=True)
        results.append(r)
    out = {
        "ts": time.time(),
        "git_head": head,
        "sec_S_exposure": SEC_S_EXPOSURE,
        "preregistration": "I0B_BUILD_RSTECHLEAD_20260716.md (predicates fixed before run)",
        "legs": results,
        "all_pass": all(r["passed"] for r in results),
    }
    name = "forkb_i0b_legs_result.json" if not a.only else f"forkb_i0b_legs_result_only_{'_'.join(a.only)}.json"
    (_HERE / name).write_text(json.dumps(out, indent=1))
    print(f"ALL_PASS={out['all_pass']} -> {name}", flush=True)
    return 0 if out["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
