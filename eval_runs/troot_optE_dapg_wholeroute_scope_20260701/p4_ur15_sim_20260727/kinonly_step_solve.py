# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""KINONLY solve of the canonical STEP 1-18 waypoints at the C-2 mounting.

⛔ What this is NOT: it never steps.  No mj_step, no dynamics, no route run.  It answers one
question per STEP -- *is there a joint configuration that puts both tools where the design says,
AT AN ATTITUDE THE DESIGN'S OWN MENU NAMES (spec §6.4d GRASP_ATTITUDES), without the arms
touching* -- and nothing about whether a controller could follow the path there.  Position-only
was shakedowns 1-3, and its negatives were unattributable: the design engineers its attitudes so
two arms share an 88 mm span, and an instrument that never commands an attitude cannot tell "C-2
has no clear attitude" from "I never asked for the composed one".

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
_IN_HOOK = False
_AUDITED_EVENTS = ("import", "exec", "compile", "subprocess.Popen", "os.system")


def _audit(event: str, args) -> None:
    """Record the event so it IDENTIFIES ITSELF.

    ⛔ The first version stored only args[0] for a spawn -- the executable -- so the record said
    WHAT ran and never WHO ran it, and I filled the gap by attributing the two spawns to a version
    read from memory.  That attribution was false (the version read uses importlib.metadata and
    spawns nothing) and a benign-sounding attribution RETIRES an unexplained subprocess, which is
    the exact failure this hook exists to catch.  Every record below now carries its own source:
    full argv for a spawn, and the caller's frame for exec/compile, so a count is never all a
    reader gets.
    """
    global _IN_HOOK
    if event == "import":
        _AUDIT["import"].append(str(args[0]))
        return
    # ⛔ RE-ENTRANCY GUARD.  sys._getframe RAISES ITS OWN AUDIT EVENT, so asking the hook "who
    # called you" made the hook call itself -- the instrument that measures events became a source
    # of them, and the import never returned.  Measured: the spec alone imports in 0.1 s; this
    # module timed out at 90 s until this flag existed.
    if _IN_HOOK:
        return
    _IN_HOOK = True
    try:
        f = sys._getframe(1)
        where = f"{f.f_code.co_filename.split('/')[-1]}:{f.f_lineno}"
    except Exception:
        where = "<frame unavailable>"
    finally:
        _IN_HOOK = False
    if event == "exec":
        _AUDIT["exec"].append(where)
    elif event == "compile":
        _AUDIT["compile"].append(where)
    elif event == "subprocess.Popen":
        _AUDIT["Popen"].append(f"argv={str(args[1])[:200]} from {where}")
    elif event == "os.system":
        _AUDIT["system"].append(f"{str(args[0])[:160]} from {where}")


sys.addaudithook(_audit)

import os  # noqa: E402

# The C-2 point, as env overrides against the pinned tip.  ⛔ CROWN_R_OVERRIDE accepts the literal
# string "none", which removes the crown geometry entirely (ur15_cell_spec.py:352 @ 2fba2dfd67);
# the commission's value is "0.110" and nothing else.
C2_ENV = {"YOKE_SPREAD_OVERRIDE": "0.28", "TILT_DEG_OVERRIDE": "20", "CROWN_R_OVERRIDE": "0.110"}
for _k, _v in C2_ENV.items():
    os.environ[_k] = _v

import json  # noqa: E402
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
# Horizontal targets -- acceptance D-2(c).  ⛔ NEVER INVENTED.  The referent comes from the
# design's own columns (action word, clip-state, z-continuity), resolved off THIS model's
# constants, and the resolution is PRINTED per row before the table.  ⚠ The C2 x divergence
# (cell 0.040 vs design and task_config +0.075, 35.0 mm) is p4's open deviation word; both
# values are measured where it bites.
# ---------------------------------------------------------------------------------------------
CLIP_XY = {"C1": tuple(spec.C1), "C2": tuple(spec.C2)}
REST_XY = (0.0, float(spec.REST_Y))


def referent_for(row: dict, carry: tuple | None) -> tuple[str, tuple[float, float], str]:
    """Return (referent, (x, y), rule) from the design's own columns -- three rules, D-2(c):

    1. the action names a clip -> that clip.
    2. the action names the cable while NO clip is seated (clip column '-') -> the resting
       cable: y = spec.REST_Y (the saddle row); x = 0.0 is an INSTRUMENT CHOICE inside the free
       window between the middle and right saddles (REST_X) -- the design bounds that x, it
       does not name it, and the label says so.
    3. otherwise -> the previous row's referent, carried: the design moves the hands only when
       its action word says so.  The table's own z-columns witness this -- rows 8, 12-14 and 17
       keep the previous row's z exactly; only fingers and clip state change.

    ⛔ v1 (shakedowns 1-4) resolved EVERY clipless row to (0.0, TABLE_Y) and called it "cable
    row" -- TABLE_Y is the TABLE'S CENTRELINE (spec :670 @ 2fba2dfd67), not a cable row, so rows
    8/12-14/17 were measured at a point the design never names, and rows 2-5 sat 60 mm off the
    saddle row.  Found preparing shakedown 5; v1-v4 rows carry that referent.  A second v1-v4
    defect fixed here: the rule string was RETURNED but never printed, while the section header
    claimed "published per row".
    """
    n = row["name"]
    for c in ("C1", "C2"):
        if c in n:
            return c, CLIP_XY[c], f"rule 1: action names {c}; xy = spec.{c}"
    if "ケーブル" in n and row["clip"] in ("-", ""):
        return "cable-at-rest", REST_XY, "rule 2: cable named, no clip seated; y = spec.REST_Y, x = 0.0 (instrument choice in the free saddle window)"
    if carry is None:
        raise RuntimeError(f"row {row['step']} names no referent and there is nothing to carry")
    return carry[0], carry[1], f"rule 3: no referent named, z unchanged; carried from the previous row ({carry[0]})"


# ---------------------------------------------------------------------------------------------
# THE CELL, REASSEMBLED.  ⚠ The cable is DELIBERATELY ABSENT: its degrees of freedom are the open
# §0 item (row 48) and building it here would import an unruled question into a clearance number.
# ⇒ "collision-free" in this table means ARM-vs-ARM, ARM-vs-CLIP, ARM-vs-TABLE and ARM-vs-COLUMN.
# It says NOTHING about the cable, and a row must not be read as if it did.
# ---------------------------------------------------------------------------------------------
def build_cell() -> tuple[mujoco.MjModel, dict]:
    """Reassemble the cell from spec constants, mirroring the driver's own world part list at the
    tip (mast trio :244-247, saddles :186-194, clips from spec.CLIP_PARTS :148-161, crown capsule
    :182-183, all @ 2fba2dfd67).  ⛔ Shakedowns 1-7 ran on a cell missing foot, crown and saddles,
    with the stem at the spec's own retired "⛔ Was SHOULDER_HEIGHT/2" form and clips hand-restated
    -- the exact drift spec.CLIP_PARTS exists to prevent.  §8.43 find 2."""
    prov = {}
    zc = float(spec.TABLE_TOP)

    def clip_xml(name, cx, cy):
        parts = "".join(
            f'\n        <geom name="{name}_{i}" type="box" size="{hx:.4f} {hy:.4f} {hz:.4f}" '
            f'pos="{dx:.4f} {dy:.4f} {dz + spec.FLOAT_Z:.4f}"/>'
            for i, (dx, dy, dz, hx, hy, hz) in enumerate(spec.CLIP_PARTS)
        )
        return f"""
      <body name="{name}" pos="{cx} {cy} {zc}">{parts}
      </body>"""

    def rest_xml(i, cx):
        h = float(spec.REST_TOP) - zc
        return f"""
      <body name="S{i}" pos="{cx} {spec.REST_Y} {zc}">
        <geom name="S{i}_post" type="box" size="{spec.REST_POST_HALF} {spec.REST_POST_HALF} {h / 2:.4f}" pos="0 0 {h / 2:.4f}"/>
        <geom name="S{i}_la" type="box" size="{spec.REST_POST_HALF} {spec.REST_LIP_HY} {spec.REST_LIP_HZ}" pos="0 {-spec.REST_LIP_DY} {h + spec.REST_LIP_HZ:.4f}"/>
        <geom name="S{i}_lb" type="box" size="{spec.REST_POST_HALF} {spec.REST_LIP_HY} {spec.REST_LIP_HZ}" pos="0 {spec.REST_LIP_DY} {h + spec.REST_LIP_HZ:.4f}"/>
      </body>"""

    crown = (f'<geom name="crown" type="capsule" size="{spec.CROWN_R}" '
             f'fromto="{-spec.YOKE_SPREAD} 0 {spec.CROWN_ZC} {spec.YOKE_SPREAD} 0 {spec.CROWN_ZC}"/>'
             if spec.CROWN_R > 0.0 else "")
    if not crown:
        print("[cell] ⚠ CROWN REMOVED (CROWN_R=0): announced, not absorbed -- an instrument that "
              "silently stops measuring a part reads exactly like a part that is clear")
    saddles = "".join(rest_xml(i, cx) for i, cx in enumerate(spec.REST_X))
    world = f"""<mujoco model="c2_kinonly">
  <compiler angle="radian" autolimits="true"/>
  <worldbody>
    <geom name="floor" type="plane" size="6 6 0.1" pos="0 0 0" contype="0" conaffinity="0"/>
    <body name="column" pos="0 0 0">
      <geom name="stem" type="cylinder" size="{float(spec.COLUMN_R):.4f} {spec.COLUMN_HZ:.4f}"
            pos="0 0 {spec.COLUMN_STEM_BOTTOM + spec.COLUMN_HZ:.4f}"/>
      <geom name="foot" type="cylinder" size="{spec.PEDESTAL_R} {spec.PEDESTAL_HZ}"
            pos="0 0 {spec.PEDESTAL_HZ}"/>
      {crown}
    </body>
    <body name="table" pos="0 {spec.TABLE_Y} 0">
      <geom name="table_top" type="box" size="{spec.TABLE_HX} {spec.TABLE_HY} {spec.TABLE_HZ}"
            pos="0 0 {zc - spec.TABLE_HZ:.4f}"/>
    </body>
    {clip_xml("C1", *CLIP_XY["C1"])}
    {clip_xml("C2", *CLIP_XY["C2"])}
    {saddles}
  </worldbody>
</mujoco>
"""
    prov["mast"] = f"stem(0.37->1.53) + foot(r{spec.PEDESTAL_R}) + " + (
        f"crown(capsule r{spec.CROWN_R} @ z{spec.CROWN_ZC:.3f})" if crown else "crown ABSENT")
    prov["saddles"] = f"{len(spec.REST_X)} @ REST_X on y={spec.REST_Y}"
    prov["clips"] = f"spec.CLIP_PARTS x{len(spec.CLIP_PARTS)} boxes, FLOAT_Z={spec.FLOAT_Z}"
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
    """Partition geoms into moving arms vs static structure, by WELD then by body prefix.

    ⛔ Not by geom name: the URDF import leaves every arm geom UNNAMED, so a name-prefix predicate
    returns two empty arm groups and the clearance check then compares empty sets and reports
    CLEAR.  That happened here on the first run.  Bodies carry the `L_`/`R_` prefix; geoms do not.

    ⛔ And not by prefix ALONE: the arms' base links are BOLTED to the yoke -- `L_base_link_inertia`
    is welded to the world with zero joints on its path -- and the crown intersects it by 79.2 mm
    BY CONSTRUCTION (shakedown 8; the spec's own crown text REQUIRES the head to reach the mounts,
    :421-424 @ 2fba2dfd67).  A pair with zero relative freedom has a constant distance, and a
    constant -79.2 floor under every row is not a reading -- it drowned every real one (env-clear
    0/0, clear-pairs 0, all 25 rows).  So: a geom whose body is welded to the world is STRUCTURE
    (column, table, clips, saddles, and the bolted arm bases alike); only bodies with a joint
    between them and the world are an arm.  A moving body with neither prefix would be
    unclassifiable and raises."""
    out = {"L": [], "R": [], "env": []}
    static_weld = int(m.body_weldid[0])
    for g in range(m.ngeom):
        if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "") == "floor":
            continue
        b = int(m.geom_bodyid[g])
        if int(m.body_weldid[b]) == static_weld:
            out["env"].append(g)
            continue
        bn = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or ""
        if bn.startswith("L"):
            out["L"].append(g)
        elif bn.startswith("R"):
            out["R"].append(g)
        else:
            raise RuntimeError(f"moving body {bn!r} (geom {g}) has neither arm prefix -- refusing "
                               f"to classify it silently")
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

    # ⛔ mj_geomDistance SATURATES: it returns the cutoff itself for a pair that is farther, so a
    # saturated value wears a distance's clothes and carries a pair name exactly like a real one.
    # The wired driver names this failure in its own arm query and returns None instead; same rule
    # here -- a reading at or past the cutoff is ABSENT, (None, "-"), never a number.
    best, who = None, "-"
    ft = np.zeros(6)
    skip = _adjacent_body_pairs(m)
    for a in A:
        for b in B:
            ba, bb = int(m.geom_bodyid[a]), int(m.geom_bodyid[b])
            if (min(ba, bb), max(ba, bb)) in skip:
                continue
            dist = mujoco.mj_geomDistance(m, d, a, b, cutoff, ft)
            if dist >= cutoff:
                continue
            tag = ""
            seg = float(np.linalg.norm(ft[3:] - ft[:3]))
            if dist == 0.0 or abs(seg - abs(dist)) > 1e-6 + 0.01 * abs(dist):
                # ⛔ SUSPECT READING -- two measured failure modes on this cell (mujoco 3.10.0,
                # reproduction = probe_geomdistance_exact_zero.py): a mesh pair 61.590 mm apart
                # returns EXACTLY 0.0 under one ulp of pose arithmetic; a pad<->table pair at
                # 301.9 mm centre distance returns 0.0 STABLY, with a witness segment ~520 mm
                # long for a claimed zero -- self-contradiction the reading carries with it.
                # Resolution: a PROVABLE lower bound (bounding radii, and exact point-to-
                # primitive where a primitive is involved).  Positive bound -> the pair is
                # provably clear and the bound stands in as a CONSERVATIVE reading (it
                # understates the distance; the pair name says ">=bound").  No positive bound
                # -> the raw reading is kept as contact, the conservative direction.
                _GUARD[0] += 1
                lb = _provable_lower_bound(m, d, a, b)
                if lb > 0.0:
                    _GUARD[1] += 1
                    dist, tag = lb, " >=bound"
                else:
                    _GUARD[2] += 1
                if dist >= cutoff:
                    continue
            if best is None or dist < best:
                best, who = dist, f"{nm(a)} <-> {nm(b)}{tag}"
    return best, who


_GUARD = [0, 0, 0]   # [suspect readings, bound-substituted (provably clear), kept as contact]
_ADJ_CACHE: dict[int, frozenset] = {}


def _adjacent_body_pairs(m: mujoco.MjModel) -> frozenset:
    """Body pairs joined by at most ONE joint along the ancestor chain -- mount interfaces.

    Their separation is a property of the ASSEMBLY, not of a pose: after the weld partition
    removed the crown<->bolted-base constant (-79.2 mm, every row of shakedown 8), the very next
    reading was the shoulder against ITS OWN base at a constant +0.1 mm -- the pan joint's
    designed interface, one level up, same class.  A pair whose bodies are rigidly connected or
    separated by one joint sits at a designed clearance in every pose, so measuring it floors
    every row with a constant and drowns the pose-dependent readings the table exists for.
    Ancestor-chain form, NOT mj_collision's weld-parent filter: that filter would also blind the
    first moving link against ALL static geometry (table included), which is a real collision
    question.  Sibling statics (table, clips, saddles) are never ancestors, so they stay
    measured against every link."""
    key = id(m)
    if key not in _ADJ_CACHE:
        pairs = set()
        for b in range(m.nbody):
            x, cnt = b, 0
            while x != 0:
                cnt += int(m.body_jntnum[x])
                x = int(m.body_parentid[x])
                if cnt <= 1:
                    pairs.add((min(b, x), max(b, x)))
                else:
                    break
        _ADJ_CACHE[key] = frozenset(pairs)
    return _ADJ_CACHE[key]


def _point_to_geom(m, d, g: int, p: np.ndarray) -> float:
    """Signed distance from world point `p` to geom `g`: exact for primitives, AABB bound else."""
    t = m.geom_type[g]
    size = m.geom_size[g]
    q = d.geom_xmat[g].reshape(3, 3).T @ (np.asarray(p) - d.geom_xpos[g])
    if t == mujoco.mjtGeom.mjGEOM_SPHERE:
        return float(np.linalg.norm(q)) - float(size[0])
    if t == mujoco.mjtGeom.mjGEOM_BOX:
        e = np.abs(q) - size
        return float(np.linalg.norm(np.maximum(e, 0.0)) + min(0.0, float(np.max(e))))
    if t == mujoco.mjtGeom.mjGEOM_CYLINDER:
        dr = math.hypot(q[0], q[1]) - float(size[0])
        dz = abs(float(q[2])) - float(size[1])
        if dr <= 0.0 and dz <= 0.0:
            return max(dr, dz)
        return math.hypot(max(dr, 0.0), max(dz, 0.0))
    if t == mujoco.mjtGeom.mjGEOM_CAPSULE:
        qz = float(np.clip(q[2], -size[1], size[1]))
        return float(np.linalg.norm(q - np.array([0.0, 0.0, qz]))) - float(size[0])
    # Any other type (meshes): the geom's own model-computed AABB, an OBB in the geom frame that
    # CONTAINS the shape -- distance to the containing box lower-bounds distance to the contained
    # mesh.  Much tighter than the bounding sphere for elongated links and couplers: shakedown 8b
    # left 144,933 suspect readings unprovable (37%) on the sphere bound alone, flooring the
    # along-path column with kept-as-contact zeros at pairs tens of mm apart.
    c, h = m.geom_aabb[g, :3], m.geom_aabb[g, 3:]
    e = np.abs(q - c) - h
    return float(np.linalg.norm(np.maximum(e, 0.0)) + min(0.0, float(np.max(e))))


def _provable_lower_bound(m, d, a: int, b: int) -> float:
    """Best available lower bound on the surface-surface distance of a suspect pair.

    Three valid bounds, take the max: centre distance minus both bounding radii; and, where
    either geom is a primitive, the exact point-to-primitive distance from the OTHER geom's
    centre minus that other geom's bounding radius.  Every one understates the true distance,
    so substituting one for a garbage reading can only make a row read TIGHTER than reality.
    """
    pa, pb = d.geom_xpos[a], d.geom_xpos[b]
    lbs = [float(np.linalg.norm(pa - pb)) - float(m.geom_rbound[a]) - float(m.geom_rbound[b])]
    for g, p, other in ((b, pa, a), (a, pb, b)):
        lbs.append(_point_to_geom(m, d, g, p) - float(m.geom_rbound[other]))
    return max(lbs)


def gap_say(v: float | None, who: str, cutoff: float = 0.5) -> str:
    """One spelling for a reading or its absence -- never a sentinel in a millimetre slot."""
    if v is None:
        return f"nothing within the {cutoff * 1000:.0f} mm search radius"
    return f"{v * 1000:+.1f} ({who})"


def gap_worst(*vs: float | None) -> float | None:
    """Minimum over readings; absent means beyond the cutoff, which no reading is larger than."""
    present = [v for v in vs if v is not None]
    return min(present) if present else None


# ---------------------------------------------------------------------------------------------
# ATTITUDE, FROM THE DESIGN'S OWN MENU -- D-2(c): the design names the attitudes, the instrument
# never invents one.  Both functions below are ports of the driver's canonical form, cited line
# by line, because the attitude a row certifies must be the attitude the design's own machinery
# would produce for that menu entry -- a home-grown parametrisation would certify something else.
# ---------------------------------------------------------------------------------------------
def rdes(yaw: float, roll: float = 0.0) -> np.ndarray:
    """Desired tool orientation for a menu entry.  Port of `_rdes` (driver :1174-1181 @
    2fba2dfd67): closing axis across the cable, approach down; yaw spins about the vertical,
    roll tips about the closing axis -- 'Rolling is what lets two arms share an 88 mm span
    without their wrists meeting'."""
    base = Rotation.from_euler("z", yaw) * Rotation.from_euler("z", math.pi / 2.0)
    return (base * Rotation.from_euler("y", roll)).as_matrix()


def measure_axfix(m: mujoco.MjModel, qadr: dict, pad: dict, toolb: dict) -> dict:
    """Where the closing and approach axes sit in each tool body's own frame.  Port of
    `_measure_axfix` (driver :426-448 @ 2fba2dfd67), measured on a throwaway MjData at the
    driver's own reference pose -- the relation is rigid, so any non-singular pose gives the
    same local matrix; using the driver's keeps the numerics identical."""
    sc = mujoco.MjData(m)
    for t in ("L", "R"):
        for k, a in enumerate(qadr[t]):
            sc.qpos[a] = [0.0, -1.2, 1.0, -1.4, -1.57, 0.0][k]
    mujoco.mj_forward(m, sc)
    out = {}
    for t in ("L", "R"):
        pl, pr = np.array(sc.xpos[pad[t][0]]), np.array(sc.xpos[pad[t][1]])
        c_w = (pr - pl) / max(np.linalg.norm(pr - pl), 1e-9)
        pinch_w = 0.5 * (pl + pr)
        a_w = np.array(sc.xpos[toolb[t]]) - pinch_w
        a_w = a_w / max(np.linalg.norm(a_w), 1e-9)
        Rt = np.array(sc.xmat[toolb[t]]).reshape(3, 3)
        c_l, a_l = Rt.T @ c_w, Rt.T @ a_w
        s_l = np.cross(a_l, c_l)
        out[t] = np.column_stack([c_l, s_l, a_l]).T
    return out


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
    # ⭐ The tool point is the PINCH SITE, not the coupler base.  The design's z is the height of
    # the grasp, so a coupler-base target sits a gripper length away from where the design puts it
    # -- that was defect (b) of the first run.
    TOOL = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, f"{t}g_pinch") for t in ("L", "R")}
    if min(TOOL.values()) < 0:
        raise RuntimeError("pinch sites absent -- refusing to substitute a different tool point silently")
    print(f"[cell] tool point per arm = SITE {[mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_SITE, s) for s in TOOL.values()]}")
    # Attitude datum bodies -- same loud-failure rule as the sites: substituting a different body
    # would silently change WHAT ATTITUDE MEANS on this instrument.
    PADB = {t: [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_{s}_pad") for s in ("left", "right")]
            for t in ("L", "R")}
    TOOLB = {t: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{t}g_base") for t in ("L", "R")}
    if min(min(v) for v in PADB.values()) < 0 or min(TOOLB.values()) < 0:
        raise RuntimeError("pad or tool-base bodies absent -- the attitude datum cannot be measured")
    DOF = {t: [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{t}_{j}")] for j in J6]
           for t in ("L", "R")}
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
    ae = gap_worst(ae_l, ae_r)
    ae_pair = pair_l if (ae_r is None or (ae_l is not None and ae_l <= ae_r)) else pair_r
    print(f"| 1 | ASSIGNED start pose (spec.HOME_POSE) | not solved -- read from the design | "
          f"{gap_say(aa, pair)} | {gap_say(ae, ae_pair)} | "
          f"{'CLEAR' if all(v is None or v > 0 for v in (aa, ae_l, ae_r)) else 'TOUCHING OR THROUGH'} |")
    # ---- STEP 2-18 -----------------------------------------------------------------------
    # Damped-least-squares IK on the tool point, kinematics only.  SEARCH BUDGET IS PART OF THE
    # CONCLUSION (acceptance (6)): a "not solved" row means not solved WITHIN THIS BUDGET.
    ITERS, SEED, TOL = 260, 20260809, 2e-3
    # Attitude acceptance: 0.02 rad is the driver's own seat-solve tolerance (re_max=0.02,
    # :733 @ 2fba2dfd67) AND it sits under half the menu's finest roll spacing (0.05 between
    # 0.50 and 0.55), so a converged attitude names ONE menu entry rather than a blur of
    # neighbours -- the same identifiability rule the spec applies to the vertical check.
    RE_TOL = 0.02
    MENU = list(spec.GRASP_ATTITUDES)      # the design's menu, verbatim (spec §6.4d)
    TRIES = 2 * len(MENU)                  # p11 -147 (driver :1424-1429): never LESS than one
    #                                        full pass over the menu; two, so each entry gets a
    #                                        second seed.  The menu's own length, not a round number.
    POOL_MIN_DQ = 0.10                     # pool admission floor, L2 rad over 6 joints: under
    #                                        branch separation (~1 rad), over solver jitter
    #                                        (TOL-scale).  Two poses closer than this are one
    #                                        branch refined twice, not two candidates.
    rng = np.random.default_rng(SEED)
    lims = np.asarray(spec.LIMS, dtype=float)
    solved_q = {1: {t: home.copy() for t in ("L", "R")}}
    AXFIX = measure_axfix(m, qadr, PADB, TOOLB)
    print(f"[att] menu = spec.GRASP_ATTITUDES: {len(MENU)} entries (spec §6.4d @ 2fba2dfd67); "
          f"sign per arm on BOTH yaw and roll (spec.SIDES; p5 -167, driver :1414); "
          f"AXFIX datum measured per arm at the driver's reference pose (driver :426-448 port)")

    def solve_arm(t: str, target: np.ndarray, seed_q: np.ndarray | None = None):
        """DLS position+attitude IK against the design's own menu.

        Each try commands ONE menu entry (yaw, roll), signed for this arm on both components
        (p5 -167, driver :1414 @ 2fba2dfd67); the try order is the menu's own order, twice
        (p11 -147: never less than one full pass).  Solver numerics are the driver's 6D form
        verbatim (:1448-1462): error = [ep, 0.6*er], damping 0.05^2, half-step relaxation,
        step-norm cap 0.15.  Seeding: pass 1 = the previous STEP's pose (driver :1434-1436
        warm-starts every tool pose from the previous waypoint), pass 2 = prev + N(0, 0.35);
        home / uniform when no prev exists.

        ⛔ DEFECT FIXED IN THIS REVISION, found while porting the 6D form: shakedowns 1-3 called
        mj_kinematics then mj_jacSite, and mj_jac* reads cdof, WHICH mj_kinematics DOES NOT
        UPDATE -- mj_comPos does.  cdof stayed where the one mj_forward at the home pose left
        it, so every earlier iterate descended a home-pose Jacobian.  Measurements (geom_xpos)
        were unaffected; convergence was slowed, not falsified -- and "not solved within budget"
        rows from those shakedowns carried that solver in their budget.

        Pool = every distinct converged candidate (position TOL AND attitude RE_TOL), where
        distinct = L2 joint distance >= POOL_MIN_DQ to every member; first arrival in menu
        order is kept.  ⛔ No early break during collection: the menu is roll-ascending, so
        stopping at the first few converged entries would bias the pool to near-upright and
        starve exactly the high-roll attitudes the design engineered for clearance.
        """
        tool, toolb, dof = TOOL[t], TOOLB[t], DOF[t]
        sgn = float(spec.SIDES[t])
        best_pe, best_re, used = 1e9, 1e9, 0
        cands: list[tuple] = []      # (q, (yaw, roll) as commanded, pe, re)
        for ri in range(TRIES):
            yaw, roll = MENU[ri % len(MENU)]
            yaw, roll = sgn * yaw, sgn * roll
            RDA = rdes(yaw, roll) @ AXFIX[t]
            if seed_q is not None and ri < len(MENU):
                q = np.asarray(seed_q, dtype=float).copy()
            elif seed_q is not None:
                q = np.clip(np.asarray(seed_q, dtype=float) + rng.normal(0.0, 0.35, 6),
                            lims[:, 0], lims[:, 1])
            elif ri == 0:
                q = home.copy()
            else:
                q = rng.uniform(lims[:, 0].clip(-np.pi), lims[:, 1].clip(None, np.pi))
            for _ in range(ITERS):
                used += 1
                for k, a in enumerate(qadr[t]):
                    d.qpos[a] = q[k]
                mujoco.mj_kinematics(m, d)
                mujoco.mj_comPos(m, d)
                ep = target - d.site_xpos[tool]
                Rt = np.array(d.xmat[toolb]).reshape(3, 3)
                er = Rotation.from_matrix(RDA @ Rt.T).as_rotvec()
                if float(np.linalg.norm(ep)) < TOL and float(np.linalg.norm(er)) < RE_TOL:
                    break
                jacp = np.zeros((3, m.nv))
                jacr = np.zeros((3, m.nv))
                mujoco.mj_jacSite(m, d, jacp, None, tool)
                mujoco.mj_jacBody(m, d, None, jacr, toolb)
                J = np.vstack([jacp[:, dof], 0.6 * jacr[:, dof]])
                e6 = np.concatenate([ep, 0.6 * er])
                dq = 0.5 * (J.T @ np.linalg.solve(J @ J.T + 0.05**2 * np.eye(6), e6))
                n = float(np.linalg.norm(dq))
                if n > 0.15:
                    dq *= 0.15 / n
                q = np.clip(q + dq, lims[:, 0], lims[:, 1])
            # Final measure at the pose the loop actually left, driver-style (:1466-1469).
            for k, a in enumerate(qadr[t]):
                d.qpos[a] = q[k]
            mujoco.mj_kinematics(m, d)
            pe = float(np.linalg.norm(target - d.site_xpos[tool]))
            Rt = np.array(d.xmat[toolb]).reshape(3, 3)
            re_ = float(np.linalg.norm(Rotation.from_matrix(RDA @ Rt.T).as_rotvec()))
            best_pe = min(best_pe, pe)
            if pe < TOL:
                best_re = min(best_re, re_)
            if pe < TOL and re_ < RE_TOL:
                if all(float(np.linalg.norm(q - c[0])) >= POOL_MIN_DQ for c in cands):
                    cands.append((q.copy(), (yaw, roll), pe, re_))
        return cands, best_pe, best_re, used

    def place(qs: dict) -> None:
        for t in ("L", "R"):
            for k, a in enumerate(qadr[t]):
                d.qpos[a] = qs[t][k]
        mujoco.mj_kinematics(m, d)

    def env_scan(t: str, cands: list, other_q: np.ndarray) -> list:
        """Per-candidate env clearance, measured ONCE per candidate: env is a property of ONE
        arm and the static world, so it does not belong inside the pair loop.  ⚠ Ranking, not
        rejection -- the spec's own recorded lesson (SIGMA_FLOOR: 'the 0.12 floor starved the
        solver ... ranking, not rejection, is the way to do this'): an env-touching candidate
        stays scoreable, and the row REPORTS how many candidates were env-clear, which is what
        makes a TOUCHING verdict attributable to the design point rather than to my selection."""
        other = "R" if t == "L" else "L"
        out = []
        for c in cands:
            place({t: c[0], other: other_q})
            v, p = closest(m, d, grp[t], grp["env"])
            out.append((c, v, p))
        return out

    # ⭐ DEV-C2X (p4, 2026-08-09 11:09, provisional, D-5-adjacent).  clip C2's x disagrees between
    # the reassembled cell (0.040) and both the design table and task_config (+0.075) -- 35.0 mm.
    # The (c) resolution chain names no single source where the sources fight, so clip-C2-consuming
    # rows fall to form (d) and are measured at BOTH candidates.
    # MAPPING, DECLARED IN ONE LINE: design (across, along) -> cell (x, y) by transposition, i.e.
    # design C1 (30/+0.150) -> cell (0.150, 0.350) and design clip C2 (25/+0.075) -> cell (0.075, 0.400).
    # ⚠ clip C1 is the POSITIVE CONTROL that fixes this mapping: expect 0.0 mm.  A clip-C2-only
    # report leaves the mapping unstated and 35.0 mm reads as an x-error.
    C2_CAND = {"cell(0.040)": CLIP_XY["C2"], "design(+0.075)": (0.075, CLIP_XY["C2"][1])}
    print(f"[dev-c2x] mapping: design (across,along) -> cell (x,y) by transposition; "
          f"clip C1 control = {abs(CLIP_XY['C1'][0] - 0.150) * 1000:.1f} mm (expect 0.0), "
          f"clip C2 = {abs(CLIP_XY['C2'][0] - 0.075) * 1000:.1f} mm (expect 35.0)")
    # Resolve every referent FIRST and print the resolution block, so the rule each row used is
    # on the record before any solving starts (and mid-table prints cannot break the markdown).
    resolved, carry = [], None
    for row in rows[1:]:
        ref, xy, rule = referent_for(row, carry)
        carry = (ref, xy)
        resolved.append((row, ref, xy, rule))
    print()
    for row, ref, xy, rule in resolved:
        print(f"[referent] STEP {row['step']:>2} -> {ref} ({xy[0]:+.3f}, {xy[1]:+.3f})  {rule}")

    bank: list[dict] = []
    print()
    print("| STEP | referent | candidate | attitude L(yaw,roll)/R [rad] | arms-closest mm (pair) | "
          "arm-env mm (pair) | along-path worst mm (i/n, pair) | winner pe mm / re rad (L, R) | "
          "budget | verdict |")
    print("|---|---|---|---|---|---|---|---|---|---|")

    def row_at(row, ref, cx, cy, label, prev):
        tl = np.array([cx - spec.GRIP_HALF_SPAN, cy, row["zL"]])
        tr = np.array([cx + spec.GRIP_HALF_SPAN, cy, row["zR"]])
        cL, peL, reL, uL = solve_arm("L", tl, prev["L"])
        cR, peR, reR, uR = solve_arm("R", tr, prev["R"])
        # ⛔ The reach-only fallback of shakedowns 1-3 is GONE, by construction: a position-only
        # pose has no menu name, so measuring it would reintroduce exactly the ambiguity the
        # attitude iteration removes.  An empty pool is a NOT SOLVED row, with the best position
        # and attitude residuals printed so the blocker is legible (attitude blocked if pe
        # converged and re never did).
        if not cL or not cR:
            def _diag(bpe, bre):
                return f"{bpe * 1000:.1f}mm/" + (f"{bre:.3f}rad" if bre < 1e9 else "no att-conv try")
            print(f"| {row['step']} | {ref} | {label} | - | - | - | - | "
                  f"best L {_diag(peL, reL)}, R {_diag(peR, reR)} | "
                  f"{uL + uR} it, pool L{len(cL)}/R{len(cR)} | NOT SOLVED (within this budget) |")
            bank.append({
                "step": row["step"], "referent": ref, "candidate": label,
                "target_L": [float(x) for x in tl], "target_R": [float(x) for x in tr],
                "best_pe_mm": [peL * 1000.0, peR * 1000.0],
                "best_re_rad": [None if reL >= 1e9 else reL, None if reR >= 1e9 else reR],
                "pool": [len(cL), len(cR)], "iters": uL + uR,
                "verdict": "NOT SOLVED (within this budget)",
            })
            return None
        # ⭐ Fix (a): choose AMONG reaching solutions by clearance.  Without this the row answers
        # "does the first reaching solution collide", never "does a clear one exist".
        # ⛔ FULL-POOL pair ranking.  Shakedown 4 ranked 6x6 finalists out of pools of 50-82, so
        # a clear pair could sit in the pool and never be scored -- that truncation was MY
        # selection, not the design's, and a TOUCHING it produced was unattributable.  Env is
        # precomputed per candidate (env_scan), so each pair costs one arm-arm query.
        sL = env_scan("L", cL, prev["R"])
        sR = env_scan("R", cR, prev["L"])
        ncL = sum(1 for _c, v, _p in sL if v is None or v > 0)
        ncR = sum(1 for _c, v, _p in sR if v is None or v > 0)
        # ⛔ SELECTION = THE DRIVER'S OWN RULE, learned from shakedown 5: among CLEAR pairs, take
        # the one NEAREST prev in joint space -- solve_ik "returns the one closest to `near` (so
        # the servo move stays short)" (:1376-1378 @ 2fba2dfd67), and the aim loop pins entries
        # because that "holds each arm on one IK branch across the correction rounds" (:753-756).
        # Shakedown 5 ranked by clearance ALONE: every endpoint came out clear, and 23 of 25
        # along-path columns read +0.0 at 1/20, because consecutive winners sat on different IK
        # branches and the straight joint path between branches sweeps through the scene.  Those
        # path negatives were MY selection's, not the design's.  Max-min clearance remains only
        # as the fallback when no clear pair exists, and the row says so.
        best, nearest, n_clear = None, None, 0
        for a, vL, pL in sL:
            for b, vR, pR in sR:
                place({"L": a[0], "R": b[0]})
                v, pr_ = closest(m, d, grp["L"], grp["R"])
                we, pe_ = (vL, pL) if (vR is None or (vL is not None and vL <= vR)) else (vR, pR)
                # Ranking key only, never printed: absent ranks as the cutoff -- the roomiest a
                # reading could be.  The printed cell keeps the absence sentence.
                score = min(0.5 if v is None else v,
                            0.5 if vL is None else vL,
                            0.5 if vR is None else vR)
                if best is None or score > best[0]:
                    best = (score, a, b, v, pr_, we, pe_)
                if all(x is None or x > 0 for x in (v, vL, vR)):
                    n_clear += 1
                    dq = (float(np.linalg.norm(a[0] - prev["L"]))
                          + float(np.linalg.norm(b[0] - prev["R"])))
                    if nearest is None or dq < nearest[0]:
                        nearest = (dq, a, b, v, pr_, we, pe_)
        picked = nearest if nearest is not None else best
        _sel, wa, wb, aa, pair, ae, pe = picked
        sel = ("nearest-prev among clear pairs" if nearest is not None
               else "max-min clearance (NO clear pair exists in the pool)")
        qs = {"L": wa[0], "R": wb[0]}
        N = 20
        worst, at, wp = None, "-", "-"
        for i in range(1, N):
            f = i / N
            place({t2: (1 - f) * prev[t2] + f * qs[t2] for t2 in ("L", "R")})
            # ⛔ v1-v4 sampled ARM-ARM only along the path, so a path diving through the TABLE
            # was unreported.  All three readings now.
            for v, pp in (closest(m, d, grp["L"], grp["R"]),
                          closest(m, d, grp["L"], grp["env"]),
                          closest(m, d, grp["R"], grp["env"])):
                if v is not None and (worst is None or v < worst):
                    worst, at, wp = v, f"{i}/{N}", pp
        place(qs)
        clear = all(x is None or x > 0 for x in (aa, ae, worst))
        capped = [t2 for t2, n in (("L", ncL), ("R", ncR)) if n == 0]
        cap = ""
        if not clear and capped and ae is not None and ae <= 0:
            cap = (f" (env-capped {'&'.join(capped)}: 0 env-clear candidates in the pool -- "
                   f"within this budget the touching is the design point's, not the selection's)")
        elif not clear and n_clear == 0:
            cap = " (no clear pair in the full pool within this budget -- max-min fallback shown)"
        verdict = ("CLEAR" if clear else "TOUCHING OR THROUGH") + cap
        along = gap_say(worst, wp) if worst is None else f"{worst * 1000:+.1f} at {at} ({wp})"
        att_s = (f"L({wa[1][0]:+.2f},{wa[1][1]:+.2f}) R({wb[1][0]:+.2f},{wb[1][1]:+.2f})")
        print(f"| {row['step']} | {ref} | {label} | {att_s} | {gap_say(aa, pair)} | {gap_say(ae, pe)} | "
              f"{along} | L {wa[2] * 1000:.1f}/{wa[3]:.3f}, R {wb[2] * 1000:.1f}/{wb[3]:.3f} | "
              f"{uL + uR} it, pool L{len(cL)}/R{len(cR)}, env-clear L{ncL}/R{ncR}, "
              f"clear-pairs {n_clear}, sel={'near' if nearest is not None else 'maxmin'} | {verdict} |")
        bank.append({
            "step": row["step"], "referent": ref, "candidate": label,
            "target_L": [float(x) for x in tl], "target_R": [float(x) for x in tr],
            "q_L": [float(x) for x in wa[0]], "q_R": [float(x) for x in wb[0]],
            "att_L": list(wa[1]), "att_R": list(wb[1]),
            "pe_re_L": [wa[2], wa[3]], "pe_re_R": [wb[2], wb[3]],
            "arms_mm": None if aa is None else aa * 1000.0, "arms_pair": pair,
            "env_mm": None if ae is None else ae * 1000.0, "env_pair": pe,
            "along_worst_mm": None if worst is None else worst * 1000.0,
            "along_at": at, "along_pair": wp,
            "path_from_L": [float(x) for x in prev["L"]],
            "path_from_R": [float(x) for x in prev["R"]],
            "selection": sel, "clear_pairs": n_clear,
            "dq_to_prev_rad": None if nearest is None else nearest[0],
            "pool": [len(cL), len(cR)], "env_clear": [ncL, ncR], "iters": uL + uR,
            "verdict": verdict,
        })
        return qs

    prev = solved_q[1]
    for row, ref, (cx, cy), rule in resolved:
        if ref == "C2":
            got = None
            for label, (ax, ay) in C2_CAND.items():
                r = row_at(row, "clip C2", ax, ay, label, prev)
                got = got or r
            prev = got or prev
        else:
            shown = {"C1": "clip C1", "C2": "clip C2"}.get(ref, ref)
            r = row_at(row, shown, cx, cy, "single", prev)
            prev = r or prev

    print()
    print(f"[budget] tries {TRIES} = 2 full passes over the design menu ({len(MENU)} attitudes, "
          f"spec §6.4d; p11 -147: never fewer than one pass) x iters {ITERS}, seed {SEED}; "
          f"acceptance = {TOL * 1000:.1f} mm position AND {RE_TOL} rad attitude (driver's "
          f"seat-solve re_max :733, and under half the menu's finest roll spacing 0.05 so a "
          f"converged attitude names ONE entry); solver numerics = driver's 6D DLS verbatim "
          f"(:1448-1462: 0.6 rot weight, 0.05^2 damping, half-step, 0.15 cap); pool = every "
          f"distinct converged candidate, floor {POOL_MIN_DQ} rad L2/6 joints; pairs scored over "
          f"the FULL pool (LxR), env precomputed per candidate, ranking never rejection; "
          f"SELECTION = nearest-prev among clear pairs (driver :1376-1378 'closest to near so "
          f"the servo move stays short'; branch-pinning :753-756), max-min clearance only as the "
          f"no-clear-pair fallback, and the row says which; seeding pass 1 = prev pose, pass 2 = "
          f"prev+N(0,0.35), home/uniform without prev; along-path samples 19 interior (arm-arm "
          f"AND arm-env), endpoints excluded, path start = the previous row's SELECTED pose "
          f"(banked as path_from)")
    sol = _GEN / "kinonly_solutions.json"
    sol.write_text(json.dumps({
        "meta": {
            "tries": TRIES, "iters": ITERS, "seed": SEED, "tol_m": TOL, "re_tol_rad": RE_TOL,
            "pool_min_dq_rad": POOL_MIN_DQ, "menu_len": len(MENU), "c2_env": C2_ENV,
            "stack": spec.stack_line(), "cell_provenance": {k: str(v) for k, v in prov.items()},
            "purpose": "winner joint vectors per row so a verifier can PLACE and re-measure "
                       "every reading without re-running the search",
        },
        "rows": bank,
    }, indent=1))
    print(f"[bank] winner joint vectors -> {sol} ({len(bank)} row-instances)")
    print(f"[audit] mj_step calls: {_MJ_STEP_CALLS}")
    print(f"[audit] suspect distance readings (exact-0.0 or witness-inconsistent): {_GUARD[0]}; "
          f"provably clear, bound substituted: {_GUARD[1]}; kept as contact: {_GUARD[2]}")
    import collections as _c
    for k, v in _AUDIT.items():
        print(f"[audit] {k}: {len(v)}")
        if v and k == "Popen":
            for one in v:
                print(f"[audit]   SPAWN {one}")
        elif v and k in ("exec", "compile"):
            for src, n in _c.Counter(v).most_common(4):
                print(f"[audit]   {n:>4} from {src}")
    print(f"[audit] sys.modules at exit: {len(sys.modules)} (published because the hook cannot see "
          f"what preceded its installation)")
    fam = [n for n in sorted(sys.modules) if n in ("ur15_steps_wired", "ur15_route", "ur15_steps",
                                                   "ur15_steps_reaim", "ur15_steps_c1seat")]
    print(f"[audit] DRIVER-FAMILY modules present: {fam if fam else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
