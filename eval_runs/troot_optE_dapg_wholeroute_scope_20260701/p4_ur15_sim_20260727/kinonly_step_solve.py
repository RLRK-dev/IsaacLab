# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""KINONLY solve of the canonical STEP 1-18 waypoints at the C-2 mounting.

⛔ What this is NOT: it never steps.  No mj_step, no dynamics, no route run.  It answers one
question per STEP -- *is there a joint configuration that puts both tools where the design says,
without the arms touching* -- and nothing about whether a controller could follow the path there.

⚠ Honesty clause (acceptance (6), widened at 2026-08-09 10:56).  This measures **the design as
restated and the cell as reassembled**.  `ur15_cell_spec.py` exports constants, not a model, so the
cell below is this file's own assembly from those constants.  It is not the cell any driver builds,
and a row must not be read as "measured on the cell wired builds".
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------------
# AUDIT HOOK -- installed before anything else is imported, because a hook cannot see what preceded
# its own installation (pZ, demonstrated in this interpreter).  Its record is therefore INCOMPLETE
# BY CONSTRUCTION for imports, which is why sorted(sys.modules) is published beside it at exit.
# ⛔ No liveness control is fired from in here: an instrument that triggers events to prove its own
# hook alive puts the control inside the record it certifies.  That control is pZ's, on a stand-in.
# ---------------------------------------------------------------------------------------------
import sys  # noqa: E402

_AUDIT: dict[str, list[str]] = {"import": [], "exec": [], "compile": [], "Popen": [], "system": []}
_AUDITED_EVENTS = ("import", "exec", "compile", "subprocess.Popen", "os.system")


def _audit(event: str, args) -> None:
    if event == "import":
        _AUDIT["import"].append(str(args[0]))
    elif event == "exec":
        _AUDIT["exec"].append(str(args)[:120])
    elif event == "compile":
        _AUDIT["compile"].append(str(args[1])[:120])
    elif event == "subprocess.Popen":
        _AUDIT["Popen"].append(str(args[0])[:160])
    elif event == "os.system":
        _AUDIT["system"].append(str(args[0])[:160])


sys.addaudithook(_audit)

import os  # noqa: E402

# The C-2 point, as env overrides against the pinned tip.  ⛔ CROWN_R_OVERRIDE accepts the literal
# string "none", which removes the crown geometry entirely (ur15_cell_spec.py:352 @ 2fba2dfd67);
# the commission's value is "0.110" and nothing else.
C2_ENV = {"YOKE_SPREAD_OVERRIDE": "0.28", "TILT_DEG_OVERRIDE": "20", "CROWN_R_OVERRIDE": "0.110"}
for _k, _v in C2_ENV.items():
    os.environ[_k] = _v

import math  # noqa: E402
import pathlib  # noqa: E402
import re  # noqa: E402

import numpy as np  # noqa: E402
import mujoco  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ur15_cell_spec as spec  # noqa: E402

_GEN = HERE / "_gen"
_GEN.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# mj_step COUNTER -- a wrapper, because mj_step is a C call and never raises an audit event.
# The form is the in-file precedent (ur15_steps_wired.py:1644 raw save / :1819 rebind @ 2fba2dfd67).
# ⛔ Proving the counter counts requires one mj_step, which acceptance (5) forbids in here; that
# control lives in pZ's leg, on a stand-in.
# ---------------------------------------------------------------------------------------------
_MJ_STEP_RAW = mujoco.mj_step
_MJ_STEP_CALLS = 0


def _mj_step_counted(*a, **k):
    global _MJ_STEP_CALLS
    _MJ_STEP_CALLS += 1
    return _MJ_STEP_RAW(*a, **k)


mujoco.mj_step = _mj_step_counted

URDF = HERE / "ur15_mj.urdf"
GRIP_XML = pathlib.Path(
    "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
)
TABLE = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md")
J6 = list(spec.ARM_JOINTS)


# ---------------------------------------------------------------------------------------------
# The canonical process table -- acceptance (1)(a): every row cites this document, never wired.
# SCAN RULES, published with the pattern (p11's law: a pattern's control does not test the scan
# that drives it):
#   anchor      = the first table header line matching `^\| STEP \| Ph \|`
#   accepted    = lines of the form `^\| <int> \|` immediately following, contiguously
#   TERMINATION = the first line that is not that form (rows 19-43 use ranges, e.g. "19-26")
# ---------------------------------------------------------------------------------------------
def read_canonical() -> tuple[list[dict], dict]:
    text = TABLE.read_text()
    lines = text.splitlines()
    heads = [i for i, s in enumerate(lines) if re.match(r"^\| STEP \| Ph \|", s)]
    rows, meta = [], {"anchors_matched": len(heads), "rows_from": "the first"}
    if not heads:
        raise RuntimeError("canonical STEP header not found")
    i = heads[0] + 2  # skip the |---| separator
    while i < len(lines):
        m = re.match(r"^\| *(\d+) *\|", lines[i])
        if not m:
            break
        c = [x.strip().strip("*") for x in lines[i].split("|")[1:-1]]
        rows.append(
            {
                "step": int(c[0]), "phase": c[1], "name": c[2],
                "zL": float(c[3]), "zR": float(c[4]),
                "fL": float(c[5]), "fR": float(c[6]), "clip": c[7],
                "src_line": i + 1,
            }
        )
        i += 1
    meta["rows_read"] = len(rows)
    meta["termination"] = f"first non-`| <int> |` line at :{i + 1}"
    return rows, meta


# ---------------------------------------------------------------------------------------------
# Horizontal targets -- acceptance D-2(c).  ⛔ NEVER INVENTED.  The design names the clip by
# identity ("C1上空へ", "C2へ押し込み"); the referent is resolved off THIS model's clip constants,
# and the resolution rule is published per row.  ⚠ The C2 x divergence (cell 0.040 vs design and
# task_config +0.075, 35.0 mm) is p4's open deviation word; both values are printed where it bites.
# ---------------------------------------------------------------------------------------------
CLIP_XY = {"C1": tuple(spec.C1), "C2": tuple(spec.C2)}


def referent_for(row: dict) -> tuple[str, tuple[float, float], str]:
    """Return (referent, (x, y), rule).  The rule string goes into the row."""
    n = row["name"]
    for c in ("C1", "C2"):
        if c in n:
            return c, CLIP_XY[c], f"design names {c}; xy = spec.{c} on this model"
    return "cable", (0.0, float(spec.TABLE_Y)), "design names the cable; xy = cable row on this model"


# ---------------------------------------------------------------------------------------------
# THE CELL, REASSEMBLED.  ⚠ The cable is DELIBERATELY ABSENT: its degrees of freedom are the open
# §0 item (row 48) and building it here would import an unruled question into a clearance number.
# ⇒ "collision-free" in this table means ARM-vs-ARM, ARM-vs-CLIP, ARM-vs-TABLE and ARM-vs-COLUMN.
# It says NOTHING about the cable, and a row must not be read as if it did.
# ---------------------------------------------------------------------------------------------
def build_cell() -> tuple[mujoco.MjModel, dict]:
    prov = {}
    zc, half = float(spec.TABLE_TOP), 0.016 / 2.0

    def clip_xml(name, cx, cy):
        return f"""
      <body name="{name}" pos="{cx} {cy} {zc}">
        <geom name="{name}_base" type="box" size="0.030 0.022 0.006" pos="0 0 0.006"/>
        <geom name="{name}_wl" type="box" size="0.006 0.022 0.035" pos="{-(half + 0.006):.4f} 0 0.047"/>
        <geom name="{name}_wr" type="box" size="0.006 0.022 0.035" pos="{(half + 0.006):.4f} 0 0.047"/>
        <geom name="{name}_floor" type="box" size="{half:.4f} 0.022 0.006" pos="0 0 0.018"/>
      </body>"""

    world = f"""<mujoco model="c2_kinonly">
  <compiler angle="radian" autolimits="true"/>
  <worldbody>
    <geom name="floor" type="plane" size="6 6 0.1" pos="0 0 0" contype="0" conaffinity="0"/>
    <body name="column" pos="0 0 0">
      <geom name="stem" type="cylinder" size="0.102 {spec.SHOULDER_HEIGHT / 2:.4f}"
            pos="0 0 {spec.SHOULDER_HEIGHT / 2:.4f}"/>
    </body>
    <body name="table" pos="0 {spec.TABLE_Y} 0">
      <geom name="table_top" type="box" size="{spec.TABLE_HX} {spec.TABLE_HY} 0.02"
            pos="0 0 {zc - 0.02:.4f}"/>
    </body>
    {clip_xml("C1", *CLIP_XY["C1"])}
    {clip_xml("C2", *CLIP_XY["C2"])}
  </worldbody>
</mujoco>
"""
    wp = _GEN / "_kinonly_world.xml"
    wp.write_text(world)
    cell = mujoco.MjSpec.from_file(str(wp))
    column = cell.body("column")
    prov["YOKE_SPREAD"] = spec.YOKE_SPREAD
    prov["TILT_rad"] = spec.TILT
    prov["SHOULDER_HEIGHT"] = spec.SHOULDER_HEIGHT

    for tag, sign in spec.SIDES.items():
        q = Rotation.from_euler("xyz", [0.0, sign * spec.TILT, 0.0]).as_quat()
        f = column.add_frame(
            pos=[sign * spec.YOKE_SPREAD, 0.0, spec.SHOULDER_HEIGHT],
            quat=[float(q[3]), float(q[0]), float(q[1]), float(q[2])],
        )
        arm = mujoco.MjSpec.from_file(str(URDF))
        f.attach_body(arm.bodies[1], f"{tag}_", "")
        if GRIP_XML.is_file():
            g = mujoco.MjSpec.from_file(str(GRIP_XML))
            Rt = Rotation.from_euler("xyz", [0, -np.pi / 2, -np.pi / 2]) * Rotation.from_euler(
                "xyz", [np.pi / 2, 0, np.pi / 2]
            )
            qt = Rt.as_quat()
            wf = cell.body(f"{tag}_wrist_3_link").add_frame(
                pos=[0, 0, 0], quat=[float(qt[3]), float(qt[0]), float(qt[1]), float(qt[2])]
            )
            wf.attach_body(g.body("base_mount"), f"{tag}g_", "")
            prov["gripper"] = str(GRIP_XML)
        else:
            prov["gripper"] = "ABSENT -- tool frame is the wrist flange"
    return cell.compile(), prov


def geom_groups(m: mujoco.MjModel) -> dict[str, list[int]]:
    """Partition geoms by the BODY they hang off.

    ⛔ Not by geom name: the URDF import leaves every arm geom UNNAMED, so a name-prefix predicate
    returns two empty arm groups and the clearance check then compares empty sets and reports
    CLEAR.  That happened here on the first run.  Bodies carry the `L_`/`R_` prefix; geoms do not.
    """
    out = {"L": [], "R": [], "env": []}
    for g in range(m.ngeom):
        if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "") == "floor":
            continue
        b = int(m.geom_bodyid[g])
        bn = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or ""
        out["L" if bn.startswith("L") else "R" if bn.startswith("R") else "env"].append(g)
    return out


def require_non_empty(grp: dict[str, list[int]]) -> None:
    """⛔ An empty group makes every clearance vacuously CLEAR.  Fail loudly instead of reporting."""
    empty = [k for k in ("L", "R", "env") if not grp[k]]
    if empty:
        raise RuntimeError(
            f"geom group(s) empty: {empty} -- a clearance over an empty set is not a measurement. "
            f"counts L={len(grp['L'])} R={len(grp['R'])} env={len(grp['env'])}"
        )


def closest(m, d, A: list[int], B: list[int], cutoff: float = 0.5) -> tuple[float, str]:
    """Minimum surface-to-surface distance [m] over A x B, and the geom pair that produced it.

    ⭐ Acceptance (2) v2: this is ACTUAL INTER-LINK GEOMETRY.  A geom-distance quantity always has
    a pair; a commanded-span quantity has none, because it never compared two geoms.  The pair name
    in every row is what lets a reader tell which kind the row is.
    """
    def nm(g: int) -> str:
        """Name the geom, falling back to `body#index` -- the URDF import leaves arm geoms unnamed.

        ⛔ A row that cannot name its pair cannot be told apart from a commanded-span quantity,
        which is the whole point of pZ's control, so "None" is never an acceptable pair name.
        """
        n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g)
        if n:
            return n
        b = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or "?"
        return f"{b}#{g}"

    best, who = 1e9, "none"
    for a in A:
        for b in B:
            dist = mujoco.mj_geomDistance(m, d, a, b, cutoff, None)
            if dist < best:
                best, who = dist, f"{nm(a)} <-> {nm(b)}"
    return best, who


def main() -> int:
    rows, meta = read_canonical()
    print(f"[table] {TABLE.name} anchors matched: {meta['anchors_matched']}, rows from {meta['rows_from']}")
    print(f"[table] rows read: {meta['rows_read']}   termination: {meta['termination']}")
    print(f"[c2]  resolved triple: YOKE_SPREAD={spec.YOKE_SPREAD} TILT={math.degrees(math.pi/2-spec.TILT):.1f}deg "
          f"CROWN_R={spec.CROWN_R}")
    print(f"[c2]  WORK_ROW_DY effective = {os.environ.get('WORK_ROW_DY', '<unset> -> 0.0')}  "
          f"(it moves both clip rows; C1's agreement with task_config is conditional on it)")
    print(f"[c2]  clips on this model: C1={CLIP_XY['C1']} C2={CLIP_XY['C2']}")
    print(f"[stack] {spec.stack_line()}")

    m, prov = build_cell()
    d = mujoco.MjData(m)
    grp = geom_groups(m)
    require_non_empty(grp)
    print(f"[cell] nq={m.nq} nu={m.nu} nbody={m.nbody} ngeom={m.ngeom}  "
          f"geoms L={len(grp['L'])} R={len(grp['R'])} env={len(grp['env'])}")
    print(f"[cell] provenance: {prov}")
    print("[cell] ⚠ the CABLE IS ABSENT by design -- clearance covers arm/arm, arm/clip, arm/table, "
          "arm/column ONLY, and says nothing about the cable (row 48 is open)")

    qadr = {t: [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6]
            for t in ("L", "R")}
    TOOL = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_base_mount") for t in ("L", "R")}
    if min(TOOL.values()) < 0:
        TOOL = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}_wrist_3_link") for t in ("L", "R")}
    print(f"[cell] tool point per arm = body {[mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) for b in TOOL.values()]}")
    home = np.asarray(spec.HOME_POSE, dtype=float)
    for t in ("L", "R"):
        for k, a in enumerate(qadr[t]):
            d.qpos[a] = home[k]
    mujoco.mj_forward(m, d)

    # STEP 1 -- the ASSIGNED start pose.  ⛔ The existence predicate is banned: "a pose exists" is
    # true by construction when the pose is written.  The question is whether THIS pose is clear.
    aa, pair = closest(m, d, grp["L"], grp["R"])
    ae_l, pair_l = closest(m, d, grp["L"], grp["env"])
    ae_r, pair_r = closest(m, d, grp["R"], grp["env"])
    print()
    print("| STEP | referent | rule | arms-closest mm (pair) | arm-env mm (pair) | verdict |")
    print("|---|---|---|---|---|---|")
    print(f"| 1 | ASSIGNED start pose (spec.HOME_POSE) | not solved -- read from the design | "
          f"{aa * 1000:+.1f} ({pair}) | {min(ae_l, ae_r) * 1000:+.1f} "
          f"({pair_l if ae_l <= ae_r else pair_r}) | "
          f"{'CLEAR' if min(aa, ae_l, ae_r) > 0 else 'TOUCHING OR THROUGH'} |")
    # ---- STEP 2-18 -----------------------------------------------------------------------
    # Damped-least-squares IK on the tool point, kinematics only.  SEARCH BUDGET IS PART OF THE
    # CONCLUSION (acceptance (6)): a "not solved" row means not solved WITHIN THIS BUDGET.
    RESTARTS, ITERS, SEED, TOL = 24, 160, 20260809, 2e-3
    rng = np.random.default_rng(SEED)
    lims = np.asarray(spec.LIMS, dtype=float)
    solved_q = {1: {t: home.copy() for t in ("L", "R")}}

    def solve_arm(t: str, target: np.ndarray) -> tuple[np.ndarray | None, float, int]:
        tool = TOOL[t]
        best_q, best_e, used = None, 1e9, 0
        for r in range(RESTARTS):
            q = home.copy() if r == 0 else rng.uniform(lims[:, 0].clip(-np.pi), lims[:, 1].clip(None, np.pi))
            for _ in range(ITERS):
                used += 1
                for k, a in enumerate(qadr[t]):
                    d.qpos[a] = q[k]
                mujoco.mj_kinematics(m, d)
                err = target - d.xpos[tool]
                e = float(np.linalg.norm(err))
                if e < best_e:
                    best_e, best_q = e, q.copy()
                if e < TOL:
                    break
                jacp = np.zeros((3, m.nv))
                mujoco.mj_jacBody(m, d, jacp, None, tool)
                J = jacp[:, [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6]]
                dq = J.T @ np.linalg.solve(J @ J.T + 1e-4 * np.eye(3), err)
                q = np.clip(q + dq, lims[:, 0], lims[:, 1])
            if best_e < TOL:
                break
        return best_q, best_e, used

    def place(qs: dict) -> None:
        for t in ("L", "R"):
            for k, a in enumerate(qadr[t]):
                d.qpos[a] = qs[t][k]
        mujoco.mj_kinematics(m, d)

    for row in rows[1:]:
        ref, (cx, cy), rule = referent_for(row)
        tl = np.array([cx - spec.GRIP_HALF_SPAN, cy, row["zL"]])
        tr = np.array([cx + spec.GRIP_HALF_SPAN, cy, row["zR"]])
        qL, eL, uL = solve_arm("L", tl)
        qR, eR, uR = solve_arm("R", tr)
        ok = (eL < TOL) and (eR < TOL)
        if qL is None or qR is None:
            print(f"| {row['step']} | {ref} | {rule} | not solved | - | NOT SOLVED (budget) |")
            continue
        qs = {"L": qL, "R": qR}
        place(qs)
        aa, pair = closest(m, d, grp["L"], grp["R"])
        ae_l, pl = closest(m, d, grp["L"], grp["env"])
        ae_r, pr = closest(m, d, grp["R"], grp["env"])
        ae, pe = (ae_l, pl) if ae_l <= ae_r else (ae_r, pr)

        # along-path: linear interpolation from the previous solved pose.  ⛔ stamped i/n, a PATH
        # FRACTION -- this sampler has no clock; only a stepping loop does.
        prev = solved_q[row["step"] - 1] if (row["step"] - 1) in solved_q else qs
        N = 20
        worst, worst_at, worst_pair = 1e9, "-", "-"
        for i in range(1, N):
            f = i / N
            place({t: (1 - f) * prev[t] + f * qs[t] for t in ("L", "R")})
            v, pp = closest(m, d, grp["L"], grp["R"])
            if v < worst:
                worst, worst_at, worst_pair = v, f"at {i}/{N}", pp
        place(qs)
        solved_q[row["step"]] = qs
        verdict = "CLEAR" if (ok and min(aa, ae, worst) > 0) else ("TOUCHING OR THROUGH" if ok else "NOT SOLVED")
        print(f"| {row['step']} | {ref} | {rule} | {aa * 1000:+.1f} ({pair}) | {ae * 1000:+.1f} ({pe}) | "
              f"{worst * 1000:+.1f} {worst_at} ({worst_pair}) | err L{eL * 1000:.1f}/R{eR * 1000:.1f} mm, "
              f"iters {uL + uR} | {verdict} |")

    print()
    print(f"[budget] restarts {RESTARTS} x iters {ITERS}, seed {SEED}, tol {TOL * 1000:.1f} mm; "
          f"along-path samples N={N - 1} interior, endpoints excluded")
    print(f"[audit] mj_step calls: {_MJ_STEP_CALLS}")
    for k, v in _AUDIT.items():
        print(f"[audit] {k}: {len(v)}" + (f"  e.g. {v[:3]}" if v and k != "import" else ""))
    print(f"[audit] sys.modules at exit: {len(sys.modules)} (published because the hook cannot see "
          f"what preceded its installation)")
    fam = [n for n in sorted(sys.modules) if n in ("ur15_steps_wired", "ur15_route", "ur15_steps",
                                                   "ur15_steps_reaim", "ur15_steps_c1seat")]
    print(f"[audit] DRIVER-FAMILY modules present: {fam if fam else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
