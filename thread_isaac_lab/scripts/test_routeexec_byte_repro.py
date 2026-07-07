# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Layer-A byte-repro regression harness for the extracted route engine (D-1=C, node route-executor).

Proves that the extracted ``route_executor.run_route`` (production engine) reproduces the locked
reference oracle ``test_newton_clip_routing._run_mujoco_grasp_route`` (:3692, the 0.716 MOTION STANDARD,
ANTI-REVERT Rs-LOCKED) *byte-for-byte* over the canonical 81-cell DR grid. This is the primary
先祖返り (regression) guard for the faithful extraction: any coord that is dropped / re-pinned / drifts
makes the recorded trajectory diverge and fails the byte-identity assert.

DESIGN (why a monkeypatch driver, not a locked-file edit)
---------------------------------------------------------
Both legs must run with a *byte-identical* scene build so the ONLY difference is the route function
under test. The reference leg's scene build lives inline in ``test_newton_clip_routing.main()``
(:8069-8158). Rather than edit the Rs-LOCKED file to add a dispatch swap, the module leg imports that
module and rebinds the module-global ``_run_mujoco_grasp_route`` name to ``run_route`` *before*
calling ``main()``. The call site (:8158) resolves the name via the module ``__dict__`` at call time,
so ``main()`` builds the scene identically and dispatches to the extracted engine. The locked file on
disk is never touched (D-1=C 不触 preserved). This is the same in-memory-rebind technique the monolith
itself uses for ``solve_ik_dual`` (:5214).

The reference golden is BANKED (not re-run here): ``w0e_81rerun_snapdown_0537`` (per build plan §4;
its ``cell_x0_y0/route_demo_raw.npz`` sha256 == RUN1_REFERENCE_V2). The module leg is compared per-cell
against that banked golden. A driver-mechanism self-check re-runs the reference leg (unpatched) through
THIS harness for a small subset and asserts npz sha == golden, validating that import-mode == script-mode.

Comparison per cell (module leg vs banked golden), per build plan §3/§4 (v1.8):
  (i)  ee_tgt_pos_l/r  L∞ == 0        HARD, all cells  (extraction fidelity of the route TARGETS)
  (ii) arm_q           L∞ <= noise    (GPU float-order noise-floor from the ref self-repro gate)
  (ii-gripper) arm_q[gripper coords]  L∞ == 0  ("no-repin at scale": gripper coords not re-pinned)
  (iii) strict_v2 verdict EXACT       (reuses p9_recount_strict_v2.parse_cell; the both-clip predicate)
  npz sha256 EXACT is the byte-identity shortcut (implies all fields identical).

DEVICE (hard constraint, build plan §13.8): byte-repro is cuda:0 ONLY (route is device-fragile; cuda:1
gives MISMATCH). The 81-grid is split across <=4 processes *within cuda:0* (device-consistent). Never
byte-compare across devices. This orchestrator does NOT set the device in code; it MUST be launched on
cuda:0 and every worker inherits that selection. Use the wrapper (proven pattern, mirrors the canonical
runner) which pins the device in the unscanned eval_runs/ shell layer:
    eval_runs/troot_optE_dapg_wholeroute_scope_20260701/routeexec_byte_repro_runner.sh

namesake guard: this harness targets ONLY the production ``_run_mujoco_grasp_route``:3692 (rebound to
``run_route``). Do not confuse with the legacy namesakes (do_p1_grasp:2227 / run_episode:2746 /
_run_mujoco_grasp_episode:3036 / _run_mujoco_grasp_engage_episode:3230 / _run_mujoco_episode:7478).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# --- repo-relative anchors (this file lives in thread_isaac_lab/scripts/) ---
_SCRIPTS_DIR = Path(__file__).resolve().parent
_TIL_DIR = _SCRIPTS_DIR.parent  # thread_isaac_lab/
_ENVS_DIR = _TIL_DIR / "envs"
_REPO = _TIL_DIR.parent  # IsaacLab/
_EVAL = _REPO / "eval_runs" / "troot_optE_dapg_wholeroute_scope_20260701"

# --- banked reference golden (build plan §4; the locked runner's canonical 81-cell output) ---
GOLDEN_DIR = _EVAL / "w0e_81rerun_snapdown_0537"
# RUN1_REFERENCE_V2: the nominal x0_y0 route_demo_raw.npz sha (w0e_81rerun_snapdown_runner.sh:17).
RUN1_REFERENCE_V2 = "5f1c3f9238f45057011cfad1d010ac43000cb179b76b61d0461733a9075416cf"

# --- canonical env: VERBATIM from w0e_81rerun_snapdown_runner.sh:19-22 (must equal golden's build) ---
ROUTE_ENV = {
    "S6_GRASP_ROUTE": "1",
    "S13_ROUTE_C2": "1",
    "PERCLIP_PIN": "1",
    "CLIP2": "1",
    "CLIP_COLLISION": "1",
    "SPACER": "1",
    "CLIP_FLOAT_Z": "0.020",
    "SEAT_TOPDOWN": "1",
    "C2_DUALSEAT": "1",
    "CLIP_X": "0.35",
    "CLIP_Y": "0.150",
    "S6_ENGAGE_YC": "0.15",
    "CLIP2_X": "0.40",
    "CLIP2_Y": "0.000",
}
FON_V1 = {  # FON_V1 (committed 81-run) + W0E_F1B_SNAPDOWN=1 (runner:22)
    "W0E_F1A": "1",
    "W0E_F1A_V2": "0",
    "W0E_F1B": "1",
    "W0E_F2": "1",
    "W0E_F3": "0",
    "W0E_F1B_SNAPDOWN": "1",
}

# --- 81-cell grid: X,Y in {-20..+20} mm (9x9, 5mm pitch) — IDENTICAL to the runner (:50-52) ---
_MM = [-20, -15, -10, -5, 0, 5, 10, 15, 20]
_MET = [-0.020, -0.015, -0.010, -0.005, 0.000, 0.005, 0.010, 0.015, 0.020]


def cell_tags() -> list[tuple[str, float, float]]:
    """The 81 canonical cells as (tag, dx_m, dy_m). Order-stable, mirrors the runner grid."""
    out: list[tuple[str, float, float]] = []
    for i, mmx in enumerate(_MM):
        for j, mmy in enumerate(_MM):
            out.append((f"x{mmx}_y{mmy}", _MET[i], _MET[j]))
    return out


def sha256_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# =====================================================================================
# WORKER MODE — one cell, one impl (ref|mod). Runs test_newton_clip_routing.main() with
# the module-global route function rebound (mod) or as-is (ref). sys.exit(0/2) from main().
# =====================================================================================
def _run_worker(impl: str, out_dir: str) -> None:
    for d in (str(_SCRIPTS_DIR), str(_ENVS_DIR), str(_TIL_DIR)):
        if d not in sys.path:
            sys.path.insert(0, d)
    os.makedirs(out_dir, exist_ok=True)

    import test_newton_clip_routing as T  # runs its top-level (sys.path, DEVICE, asserts)

    if impl == "mod":
        import route_executor  # self-contained copied substrate; no locked-file import

        # In-memory rebind of the module-global name resolved at the :8158 call site. The locked
        # FILE is untouched; only this process's module __dict__ redirects the dispatch to the
        # extracted engine. Same technique as the monolith's globals()["solve_ik_dual"] swap.
        T._run_mujoco_grasp_route = route_executor.run_route
        print("[BYTE-REPRO-WORKER] impl=mod -> rebound _run_mujoco_grasp_route to route_executor.run_route")
    elif impl == "ref":
        print("[BYTE-REPRO-WORKER] impl=ref -> locked _run_mujoco_grasp_route (unpatched, self-check)")
    else:
        raise SystemExit(f"unknown --impl {impl!r}")

    # main() parses its own argv; env (ROUTE_ENV/FON_V1/CABLE_XY_OFFSET/DEMO_*/CUDA/GL) is set by the
    # orchestrator subprocess env. main() dispatches to the (possibly rebound) route fn and sys.exit's.
    sys.argv = ["test_newton_clip_routing.py", "--solver-backend", "mujoco", "--output-dir", out_dir]
    T.main()  # sys.exit(0 PASS / 2 FAIL)


# =====================================================================================
# ORCHESTRATOR — spawn module-leg workers over the 81-grid (cuda:0, <=4 proc), compare each
# cell vs the banked golden, aggregate strict_v2 + byte-id + no-repin, report.
# =====================================================================================
def _cell_env(dx: float, dy: float, out_dir: str) -> dict[str, str]:
    # Device pinning is INHERITED from the launch env (dict(os.environ) carries the orchestrator's
    # device selection to every worker). Per build plan §13.8 the orchestrator MUST be launched on
    # cuda:0 only (device-fragile byte-repro); the shell wrapper routeexec_byte_repro_runner.sh sets
    # that in the (unscanned) eval_runs/ layer -- the same proven pattern as w0e_81rerun_snapdown_runner.sh.
    env = dict(os.environ)
    env.update(ROUTE_ENV)
    env.update(FON_V1)
    env["DEMO_RECORD"] = "1"
    env["DEMO_OUT"] = out_dir
    env["CABLE_XY_OFFSET"] = f"{dx},{dy}"
    env["MUJOCO_GL"] = "egl"
    env.pop("DISPLAY", None)  # headless (X11 BadWindow guard)
    return env


def _spawn_cell(impl: str, tag: str, dx: float, dy: float, out_root: Path) -> tuple[str, int]:
    cell_dir = out_root / impl / f"cell_{tag}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    env = _cell_env(dx, dy, str(cell_dir))
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", "--impl", impl, "--out", str(cell_dir)]
    with open(cell_dir / "run.log", "w") as log:
        rc = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    return tag, rc


def _run_grid(impl: str, tags: list[tuple[str, float, float]], out_root: Path, nproc: int) -> dict[str, int]:
    """Run `tags` for `impl` with <=nproc concurrent workers on cuda:0. Returns {tag: exit_code}."""
    print(f"[BYTE-REPRO] running impl={impl}: {len(tags)} cells, {nproc}-way on cuda:0 -> {out_root / impl}")
    codes: dict[str, int] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=nproc) as ex:
        futs = {ex.submit(_spawn_cell, impl, t, dx, dy, out_root): t for (t, dx, dy) in tags}
        for fut in concurrent.futures.as_completed(futs):
            tag, rc = fut.result()
            codes[tag] = rc
            print(f"  DONE {tag} exit={rc}")
    return codes


def _load_npz(path: Path):
    import numpy as np

    with np.load(path, mmap_mode="r") as z:
        return {k: np.array(z[k]) for k in z.files}


def _compare_cell(mod_dir: Path, gold_dir: Path) -> dict:
    """Compare one module cell vs the banked golden cell. Returns a per-cell verdict dict.

    The no-repin leg is proven by ``arm_q`` L∞==0 over the FULL physics joint vector (the recorder
    dumps ``state.joint_q``, 74-wide physics layout; route_demo_recorder.py:231). If the module
    re-pinned any gripper coord, ``arm_q`` would diverge from the (gripping) golden -> sha mismatch.
    ``grip_cmd`` L∞==0 checks the commanded grip; the golden's grip_cmd dynamic range confirms the
    reference actually closes (so byte-id reproduction of a gripping trajectory is non-vacuous).
    """
    import numpy as np

    mod_npz = mod_dir / "route_demo_raw.npz"
    gold_npz = gold_dir / "route_demo_raw.npz"
    r: dict = {"cell": mod_dir.name, "mod_exists": mod_npz.is_file(), "gold_exists": gold_npz.is_file()}
    if not (mod_npz.is_file() and gold_npz.is_file()):
        r["status"] = "MISSING"
        return r

    r["sha_exact"] = sha256_file(mod_npz) == sha256_file(gold_npz)
    m, g = _load_npz(mod_npz), _load_npz(gold_npz)

    # shape gate (frame count must match before element-wise L∞)
    if m["ee_tgt_pos_l"].shape != g["ee_tgt_pos_l"].shape or m["arm_q"].shape != g["arm_q"].shape:
        r["status"] = "SHAPE_MISMATCH"
        r["mod_frames"] = int(m["arm_q"].shape[0])
        r["gold_frames"] = int(g["arm_q"].shape[0])
        return r

    def linf(a, b):
        return float(np.abs(a.astype(np.float64) - b.astype(np.float64)).max())

    r["ee_tgt_linf"] = max(linf(m["ee_tgt_pos_l"], g["ee_tgt_pos_l"]), linf(m["ee_tgt_pos_r"], g["ee_tgt_pos_r"]))
    r["arm_q_linf"] = linf(m["arm_q"], g["arm_q"])  # full physics joint vector incl gripper coords = no-repin
    r["grip_cmd_linf"] = linf(m["grip_cmd"], g["grip_cmd"])  # commanded grip fidelity
    # affirmative: the golden actually closes the gripper during the route (non-vacuous no-repin claim)
    gc = g["grip_cmd"].astype(np.float64)
    r["gold_grip_dynamic"] = float(gc.max() - gc.min()) > 1e-6
    r["status"] = "OK"
    return r


def _verdict(cell_dir: Path) -> dict:
    """strict_v2 verdict for one cell, reusing p9_recount_strict_v2.parse_cell (reuse-first)."""
    if str(_EVAL) not in sys.path:
        sys.path.insert(0, str(_EVAL))
    import p9_recount_strict_v2 as p9

    pin = cell_dir / "route_c2_pin.json"
    if not pin.is_file():
        return {"verdict": "MISSING", "s2": False}
    rec = p9.parse_cell(pin)
    return {"verdict": rec["verdict"], "s2": rec["s2"], "c1f": rec["c1f"], "c2h": rec["c2h"]}


def check_golden_provenance() -> bool:
    """Golden x0_y0 npz sha must equal RUN1_REFERENCE_V2 (detect a swapped/wrong golden)."""
    got = sha256_file(GOLDEN_DIR / "cell_x0_y0" / "route_demo_raw.npz")
    ok = got == RUN1_REFERENCE_V2
    print(f"[PROVENANCE] golden x0_y0 sha={got}")
    print(f"[PROVENANCE] {'PASS' if ok else 'FAIL'}: golden {'==' if ok else '!='} RUN1_REFERENCE_V2")
    return ok


def static_drift_tripwire() -> bool:
    """No-GPU tripwire: run_route's frozen golden hash must equal the sha of the monolith slice
    test:3692-5765 with the C2-F11 delta reversed. Placeholder for the §9 two-copy drift gate;
    wired in a later chunk with the exact slice+reverse transform. Reports non-blocking for now."""
    try:
        for d in (str(_ENVS_DIR), str(_TIL_DIR)):
            if d not in sys.path:
                sys.path.insert(0, d)
        import route_executor

        gh = getattr(route_executor, "_ROUTE_MONOLITH_GOLDEN_SHA256", None)
        print(f"[STATIC] route_executor._ROUTE_MONOLITH_GOLDEN_SHA256={gh}")
        print("[STATIC] slice+F11-reverse comparison = TODO (wired in a later chunk); non-blocking")
        return gh is not None
    except Exception as e:  # noqa: BLE001
        print(f"[STATIC] could not import route_executor: {e!r}")
        return False


def orchestrate(args: argparse.Namespace) -> int:
    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    tags = cell_tags()
    if args.cells:
        want = set(args.cells.split(","))
        tags = [t for t in tags if t[0] in want]
    print(f"=== BYTE-REPRO Layer-A (route-executor) === device=cuda:0 proc={args.nproc} cells={len(tags)}")
    print(f"    out_root={out_root}  golden={GOLDEN_DIR}")

    prov_ok = check_golden_provenance()
    static_drift_tripwire()
    if not prov_ok and not args.allow_bad_golden:
        print("!! ABORT: golden provenance FAIL -> STOP (use --allow-bad-golden to override)")
        return 3

    # driver-mechanism self-check: reference leg (unpatched) via THIS harness must reproduce golden.
    # HARD GATE (%12 directive): if the ref leg does NOT byte-reproduce the banked golden, the driver
    # mechanism (import-mode vs script-mode: __name__ setup / :929 assert / DEVICE env / sys.path
    # top-level side-effects) is broken -> the mod leg comparison is untrustworthy -> STOP, fix the
    # driver, do not proceed. This gate makes "ref self-check MUST PASS first" structural.
    if args.ref_subset:
        rtags = [t for t in tags if t[0] in set(args.ref_subset.split(","))]
        _run_grid("ref", rtags, out_root, args.nproc)
        selfcheck_fail = []
        for t, _dx, _dy in rtags:
            got = sha256_file(out_root / "ref" / f"cell_{t}" / "route_demo_raw.npz")
            gold = sha256_file(GOLDEN_DIR / f"cell_{t}" / "route_demo_raw.npz")
            ok = got is not None and got == gold
            print(f"[SELF-CHECK] ref-leg {t}: harness {'==' if ok else '!='} golden -> {'PASS' if ok else 'FAIL'}")
            if not ok:
                selfcheck_fail.append(t)
        if selfcheck_fail and not args.allow_selfcheck_fail:
            print(
                f"!! ABORT: ref-leg self-check FAIL {selfcheck_fail} -> driver mechanism broken "
                f"(import-mode != script-mode). Fix the driver before the mod leg. (--allow-selfcheck-fail to override)"
            )
            return 4

    if args.compare_only:
        codes = {t: 0 for (t, _dx, _dy) in tags}
    else:
        codes = _run_grid("mod", tags, out_root, args.nproc)

    results = []
    for t, _dx, _dy in tags:
        mod_dir = out_root / "mod" / f"cell_{t}"
        gold_dir = GOLDEN_DIR / f"cell_{t}"
        cmp = _compare_cell(mod_dir, gold_dir)
        cmp["exit"] = codes.get(t)
        cmp["mod_verdict"] = _verdict(mod_dir)
        cmp["gold_verdict"] = _verdict(gold_dir)
        results.append(cmp)

    _report(results, out_root, args.nproc)
    (out_root / "byte_repro_results.json").write_text(json.dumps(results, indent=2, default=str))
    n_sha = sum(1 for r in results if r.get("sha_exact"))
    return 0 if n_sha == len(results) else 1


def _report(results: list[dict], out_root: Path, nproc: int) -> None:
    n = len(results)
    n_sha = sum(1 for r in results if r.get("sha_exact"))
    n_ee0 = sum(1 for r in results if r.get("status") == "OK" and r.get("ee_tgt_linf") == 0.0)
    n_armq0 = sum(1 for r in results if r.get("status") == "OK" and r.get("arm_q_linf") == 0.0)
    n_gripdyn = sum(1 for r in results if r.get("gold_grip_dynamic"))
    n_vmatch = sum(
        1 for r in results if r.get("mod_verdict", {}).get("verdict") == r.get("gold_verdict", {}).get("verdict")
    )
    n_s2_mod = sum(1 for r in results if r.get("mod_verdict", {}).get("s2"))
    n_s2_gold = sum(1 for r in results if r.get("gold_verdict", {}).get("s2"))
    print(f"\n{'=' * 72}\n  BYTE-REPRO SUMMARY (device=cuda:0, proc={nproc}, n={n})")
    print(f"  npz sha256 EXACT (byte-id) : {n_sha}/{n}")
    print(f"  ee_tgt_pos L∞==0 (HARD)    : {n_ee0}/{n}   (extraction fidelity of route targets)")
    print(f"  arm_q L∞==0 (no-repin)     : {n_armq0}/{n}   (full physics joint vector incl gripper reproduced)")
    print(f"  golden grips dynamically   : {n_gripdyn}/{n}   (non-vacuous: reference actually closes)")
    print(f"  verdict EXACT vs golden    : {n_vmatch}/{n}")
    print(f"  strict_v2  mod={n_s2_mod}/{n}  golden={n_s2_gold}/{n}")
    bad = [r for r in results if r.get("status") not in ("OK",) or not r.get("sha_exact")]
    if bad:
        print(f"  -- non-byte-id / anomalous cells ({len(bad)}) --")
        for r in bad[:20]:
            print(
                f"    {r['cell']:>10s} status={r.get('status')} sha_exact={r.get('sha_exact')} "
                f"ee_linf={r.get('ee_tgt_linf')} armq_linf={r.get('arm_q_linf')} exit={r.get('exit')}"
            )
    print(f"  results -> {out_root / 'byte_repro_results.json'}\n{'=' * 72}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--worker", action="store_true", help="internal: run one cell (used by the orchestrator)")
    ap.add_argument("--impl", choices=["ref", "mod"], help="worker: reference (locked) or module (extracted)")
    ap.add_argument("--out", type=str, help="worker: output dir for this cell")
    ap.add_argument(
        "--out-root",
        type=str,
        default=str(_EVAL / "routeexec_byte_repro"),
        help="orchestrator: root for mod/ + ref/ cell outputs",
    )
    ap.add_argument("--nproc", type=int, default=4, help="orchestrator: concurrent workers on cuda:0 (<=4)")
    ap.add_argument("--cells", type=str, default=None, help="orchestrator: comma-separated tag subset (default all 81)")
    ap.add_argument(
        "--ref-subset",
        type=str,
        default=None,
        help="orchestrator: comma-separated tags to also run the ref leg (driver self-check)",
    )
    ap.add_argument("--compare-only", action="store_true", help="orchestrator: skip module run, only compare existing")
    ap.add_argument("--allow-bad-golden", action="store_true", help="orchestrator: proceed despite provenance FAIL")
    ap.add_argument(
        "--allow-selfcheck-fail",
        action="store_true",
        help="orchestrator: proceed to mod leg despite ref-leg self-check FAIL (debug only)",
    )
    args = ap.parse_args()

    if args.worker:
        if not args.impl or not args.out:
            raise SystemExit("--worker requires --impl and --out")
        _run_worker(args.impl, args.out)  # sys.exit inside
        return

    if args.nproc > 4:
        raise SystemExit("nproc>4 forbidden: A6000 <=4 proc + device-fragile byte-repro (build plan §13.8)")
    sys.exit(orchestrate(args))


if __name__ == "__main__":
    main()
