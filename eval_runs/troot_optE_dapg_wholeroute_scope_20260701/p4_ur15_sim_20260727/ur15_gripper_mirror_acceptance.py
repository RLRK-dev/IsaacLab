# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Acceptance for the mirrored ko gripper: every right-hand geom is the left one reflected.

The predicate pZ's leg names (m-p18-273): right hand == left hand reflected at x=0.  Concretely,
with the stock arm + left asset on the left mount and the mirrored arm + MIRRORED asset on the
right mount, at EQUAL arm joint values and EQUAL finger joint values, every paired geom must
satisfy

    worldpoints(geom_R) == M worldpoints(geom_L)     as SETS, M = diag(-1,1,1)

where worldpoints = mesh vertices or box corners carried through the live frames -- a SHAPE
predicate, because geom frames cannot be compared across a mirror (MuJoCo re-frames every mesh
by its principal axes at load, and a reflected vertex set earns a different principal-frame
convention; measured: positions matched to 38 nm while frames differed by 2.0 on exactly the
mesh geoms).  Checked over two arm poses x three finger states, every geom one row, written with a
denominator (the ur15_mirror_acceptance.py shape -- a number nobody can re-read is not a
result).  A NEGATIVE leg hangs the LEFT asset on the right side -- the rotated-copy defect Rs1
(the human)'s video caught -- and it MUST fail; a test that cannot come out differently is not a
test.  Plus one vertex-level spot check that the baked mesh really is A times the original.

Kinematics only (mj_kinematics); never steps.
"""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ur15_mirror_acceptance as acc  # noqa: E402
from ur15_cell_spec import HOME_POSE  # noqa: E402

KO_LEFT = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
KO_MIRROR = str(HERE / "_ur15_2f85_koshape_actuated_mirrored.xml")
M = np.diag([-1.0, 1.0, 1.0])
A = np.diag([-1.0, 1.0, 1.0])            # the measured local mirror (make_ko_mirror.py prints it)
POS_TOL_MM = 1e-3                        # symmetric Hausdorff; the bake is exact arithmetic, a real defect is mm-scale
ARM_POSES = {"HOME": list(HOME_POSE), "alt": [0.3, -1.1, 1.9, -1.2, 1.2, -0.9]}
FINGERS = {"open": 0.0, "half": 0.4, "close": 0.7407}
FINGER_JOINTS = ("right_driver_joint", "left_driver_joint")


def build_side(arm_xml: str, grip_xml: str, sign: float):
    """One arm on its mount with a gripper hung by the driver's own formula (:307-310)."""
    root = mujoco.MjSpec.from_string(
        '<mujoco model="acc"><worldbody><body name="column"/></worldbody></mujoco>')
    q = Rotation.from_euler("xyz", [0.0, sign * acc.TILT, 0.0]).as_quat()
    f = root.body("column").add_frame(
        pos=[sign * acc.YOKE_SPREAD, 0.0, acc.SHOULDER_HEIGHT],
        quat=[float(q[3]), float(q[0]), float(q[1]), float(q[2])])
    arm = mujoco.MjSpec.from_file(str(HERE / arm_xml))
    f.attach_body(arm.bodies[1], "a_", "")
    g = mujoco.MjSpec.from_file(grip_xml)
    qt = acc.R_TOOL.as_quat()
    wf = root.body("a_wrist_3_link").add_frame(
        pos=[0, 0, 0], quat=[float(qt[3]), float(qt[0]), float(qt[1]), float(qt[2])])
    wf.attach_body(g.body("base_mount"), "g_", "")
    m = root.compile()
    return m, mujoco.MjData(m)


def place(m, d, arm_pose, fing):
    for name, q in zip(acc.J6, arm_pose):
        d.qpos[m.joint(f"a_{name}").qposadr[0]] = q
    for j in FINGER_JOINTS:
        d.qpos[m.joint(f"g_{j}").qposadr[0]] = fing
    mujoco.mj_kinematics(m, d)


def geom_rows(m):
    out = {}
    for gid in range(m.ngeom):
        b = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[gid])) or "?"
        if not b.startswith("g_"):
            continue
        nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, gid)
        out[f"{b}#{nm or 'g' + str(gid - min(g for g in range(m.ngeom) if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or chr(63)).startswith('g_')))}"] = gid
    return out


def shape_points(m, gid):
    """The geom's own shape as points in its frame: mesh vertices or box corners.

    ⛔ geom_xmat CANNOT be compared across a mirror for mesh geoms: MuJoCo re-frames every mesh
    by its principal axes at load, and a reflected vertex set earns a different principal-frame
    convention -- the SHAPE is right while the frame differs by that convention (measured: pos
    error 38 nm, frame error 2.0 on exactly the mesh geoms).  So the predicate compares WORLD
    POINT SETS, which no frame convention can touch."""
    t = m.geom_type[gid]
    if t == mujoco.mjtGeom.mjGEOM_MESH:
        mid = int(m.geom_dataid[gid])
        return m.mesh_vert[m.mesh_vertadr[mid]: m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
    if t == mujoco.mjtGeom.mjGEOM_BOX:
        s_ = m.geom_size[gid]
        return np.array([[sx * s_[0], sy * s_[1], sz * s_[2]]
                         for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    return np.zeros((1, 3))


def run_leg(mL, dL, mR, dR, label, out):
    rowsL, rowsR = geom_rows(mL), geom_rows(mR)
    assert rowsL.keys() == rowsR.keys(), "geom sets differ between the two hands"
    worst, n, bad = 0.0, 0, 0
    for pname, pose in ARM_POSES.items():
        for fname, fing in FINGERS.items():
            place(mL, dL, pose, fing)
            place(mR, dR, pose, fing)
            for key, gl in rowsL.items():
                gr = rowsR[key]
                PL = dL.geom_xpos[gl] + shape_points(mL, gl) @ dL.geom_xmat[gl].reshape(3, 3).T
                PR = dR.geom_xpos[gr] + shape_points(mR, gr) @ dR.geom_xmat[gr].reshape(3, 3).T
                want = PL @ M.T
                # ⛔ Symmetric Hausdorff via KD-trees, NOT a sorted-list compare: dense symmetric
                # parts carry many vertices sharing a coordinate, lexicographic sort pairs them
                # across branches at rounding boundaries, and the first cut read 27 mm of
                # "mismatch" on shapes whose centroids and NN profiles matched a passing geom
                # exactly (probe _gen/probe_coupler_miss.py).  A set metric has no pairing to get
                # wrong.
                if want.shape != PR.shape:
                    ep = 1e9
                else:
                    ta, tb = cKDTree(PR), cKDTree(want)
                    ep = max(float(ta.query(want)[0].max()),
                             float(tb.query(PR)[0].max())) * 1e3
                n += 1
                worst = max(worst, ep)
                ok = ep < POS_TOL_MM
                bad += 0 if ok else 1
                if not ok and bad <= 6:
                    out.append(f"    MISS {pname}/{fname} {key}: Hausdorff {ep:.4f} mm")
    out.append(f"  {label}: {n - bad}/{n} geom-instances hold (worst Hausdorff {worst:.6f} mm)")
    return bad == 0, n


def main() -> int:
    out = ["KO GRIPPER MIRROR ACCEPTANCE (predicate: right == left reflected at x=0)",
           f"assets: L={Path(KO_LEFT).name}  R={Path(KO_MIRROR).name}  A=diag(-1,1,1)",
           f"tolerance: symmetric Hausdorff {POS_TOL_MM} mm; "
           f"poses {list(ARM_POSES)} x fingers {list(FINGERS)}"]
    mL, dL = build_side("ur15_base.xml", KO_LEFT, acc.SIDE_SIGN["L"])
    mR, dR = build_side("ur15_base_mirrored.xml", KO_MIRROR, acc.SIDE_SIGN["R"])
    ok_test, n_test = run_leg(mL, dL, mR, dR, "TEST (mirrored asset on the right)", out)

    mN, dN = build_side("ur15_base_mirrored.xml", KO_LEFT, acc.SIDE_SIGN["R"])
    ok_neg, _ = run_leg(mL, dL, mN, dN, "NEGATIVE (LEFT asset on the right -- the rotated-copy "
                                        "defect; MUST fail)", out)

    # Vertex spot check AT THE FILE LEVEL: the baked STL's raw vertices == A x the original
    # STL's raw vertices, exactly.  ⛔ NOT compared through the loaded model: mj re-frames each
    # mesh by principal axes at load, so post-load arrays carry a per-mesh convention -- the
    # first cut compared those and measured its own docstring's warning.  Files carry none.
    import struct as _st

    def _stl_verts(path):
        raw = Path(path).read_bytes()
        n = _st.unpack_from("<I", raw, 80)[0]
        V = np.zeros((n * 3, 3))
        for i in range(n):
            tri = np.frombuffer(raw, dtype="<f4", count=12, offset=84 + i * 50).reshape(4, 3)
            V[3 * i: 3 * i + 3] = tri[1:]
        return V

    name = "spring_link"
    VL = _stl_verts("/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets/spring_link.stl")
    VR = _stl_verts(HERE / "ko_mirror_meshes" / "spring_link.stl")
    ta, tb = cKDTree(VR), cKDTree(VL @ A.T)
    hd = max(float(ta.query(VL @ A.T)[0].max()), float(tb.query(VR)[0].max()))
    vert_ok = VL.shape == VR.shape and hd < 1e-9
    out.append(f"  VERTEX SPOT CHECK ({name}, file-level): baked == A x original, Hausdorff "
               f"{hd:.3e} m over {len(VL)} verts: {vert_ok}")

    verdict = ok_test and (not ok_neg) and vert_ok
    out.append(f"VERDICT: {'PASS' if verdict else 'FAIL'}  "
               f"(test holds: {ok_test}; negative fails as it must: {not ok_neg}; "
               f"vertices: {vert_ok}; denominator {n_test} geom-instances)")
    text = "\n".join(out) + "\n"
    (HERE / "_gen" / "ko_mirror_acceptance.txt").write_text(text)
    print(text)
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
