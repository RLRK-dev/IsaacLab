# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bake the mirrored ko gripper: the arm mirror's own landed method, applied to the hand.

Rs1 (the human)'s video verdict named the mechanism (m-p18-273): the driver hangs ONE left-hand
gripper MJCF on both wrists, so the right hand is a rotated copy -- and a chiral ko claw carried
by any rotation stays a rotated copy (the banked arm ruling's own fact: a sign flip does not
make a mirror, P4_RS_RULING_20260727_ROBOT_UR15.md:67-69).  The arm's cure is landed precedent
(3e24574d9f): the right side loads a mirrored BUILD -- baked mirrored vertex sets, frames
conjugated numerically, axis flips travelling with value semantics.  This generator produces the
same three artifacts for the gripper:

  ko_mirror_meshes/*.stl                       vertices v -> A v, triangle winding flipped
  _ur15_2f85_koshape_actuated_mirrored.xml     pos -> A p, quat -> A R A, joint axis -> -A a
                                               (so ranges, springref, tendon coefs, ctrl
                                               semantics stay byte-identical: one command
                                               closes both hands)

⭐ A IS MEASURED, NOT REASONED (the arm commit's own law: "M R M taken numerically rather than
by reasoning about signs"): A = R_t^T R_R^T M R_L R_t, where M = diag(-1,1,1) is the world
mirror, R_L/R_R are the wrist_3 rotations the stock and mirrored arms deliver at EQUAL joint
values on their own mounts, and R_t is the driver's own hang rotation
(ur15_steps_wired.py:307).  Pose-independence of A is checked at a second arm pose, and A must
be a signed permutation (else box geoms could not stay boxes and this generator refuses).

Reads the authoritative asset READ-ONLY.  Kinematics only; never steps.
"""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ur15_mirror_acceptance as acc  # noqa: E402  (build(), R_TOOL, J6 -- reuse, never retype)
from ur15_cell_spec import HOME_POSE  # noqa: E402

KO_XML = Path("/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml")
KO_MESHDIR = KO_XML.parent / "assets"
OUT_XML = HERE / "_ur15_2f85_koshape_actuated_mirrored.xml"
OUT_MESHDIR = HERE / "ko_mirror_meshes"
M_WORLD = np.diag([-1.0, 1.0, 1.0])


def derive_A() -> np.ndarray:
    """The gripper-local mirror, measured on the built mounts at two arm poses."""
    mL, dL = acc.build("ur15_base.xml", acc.SIDE_SIGN["L"])
    mR, dR = acc.build("ur15_base_mirrored.xml", acc.SIDE_SIGN["R"])
    rt = acc.R_TOOL.as_matrix()
    A_at = []
    for pose in (list(HOME_POSE), [0.3, -1.1, 1.9, -1.2, 1.2, -0.9]):
        frames = []
        for m, d in ((mL, dL), (mR, dR)):
            for name, q in zip(acc.J6, pose):
                d.qpos[m.joint(f"a_{name}").qposadr[0]] = q
            mujoco.mj_kinematics(m, d)
            b = m.body("a_wrist_3_link").id
            frames.append((d.xpos[b].copy(), d.xmat[b].reshape(3, 3).copy()))
        (tL, RL), (tR, RR) = frames
        gap = float(np.linalg.norm(tR - M_WORLD @ tL))
        if gap > 1e-9:
            raise RuntimeError(f"wrist origins are not world mirrors at {pose}: {gap * 1000:.6f} mm "
                               f"-- the arm mirror premise failed; stop before baking on it")
        A_at.append(rt.T @ RR.T @ M_WORLD @ RL @ rt)
    if float(np.abs(A_at[0] - A_at[1]).max()) > 1e-9:
        raise RuntimeError("A is pose-DEPENDENT -- the mirrored arm is not an exact mirror "
                           f"mechanism; delta={np.abs(A_at[0] - A_at[1]).max():.3e}")
    A = A_at[0]
    if abs(float(np.linalg.det(A)) + 1.0) > 1e-9:
        raise RuntimeError(f"A is not improper (det {np.linalg.det(A):+.9f}); not a mirror")
    snapped = np.round(A)
    if float(np.abs(A - snapped).max()) > 1e-9 or not np.array_equal(np.abs(snapped).sum(0), [1, 1, 1]):
        raise RuntimeError(f"A is not a signed permutation:\n{A}\n-- box geoms could not stay "
                           f"boxes; refusing to bake a skewed mirror")
    return snapped


def _v3(s: str) -> np.ndarray:
    return np.array([float(x) for x in s.split()], dtype=float)


def _fmt(v, nd=8) -> str:
    return " ".join(f"{x:.{nd}g}" for x in v)


def mirror_xml(A: np.ndarray) -> str:
    """Transform every geometric attribute; carry everything else byte-for-byte."""
    text = KO_XML.read_text()

    def sub_attr(name, fn, s):
        def repl(mo):
            return f'{name}="{fn(_v3(mo.group(1)))}"'
        return re.sub(rf'{name}="([^"]+)"', repl, s)

    def mirror_pos(p):
        return _fmt(A @ p)

    def mirror_quat(q):
        R = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()  # wxyz -> xyzw
        q2 = Rotation.from_matrix(A @ R @ A).as_quat()
        return _fmt([q2[3], q2[0], q2[1], q2[2]])

    def mirror_axis(a):
        return _fmt(-(A @ a), nd=6)

    out_lines = []
    for line in text.splitlines():
        # Order matters only in that each attribute appears at most once per line in this asset.
        if "pos=" in line:
            line = sub_attr("pos", mirror_pos, line)
        if "quat=" in line:
            line = sub_attr("quat", mirror_quat, line)
        if "axis=" in line:
            line = sub_attr("axis", mirror_axis, line)
        if "anchor=" in line:
            line = sub_attr("anchor", mirror_pos, line)
        out_lines.append(line)
    out = "\n".join(out_lines) + "\n"
    out = out.replace('meshdir="assets"', f'meshdir="{OUT_MESHDIR.name}"')
    out = out.replace('<mujoco model="robotiq_2f85">',
                      '<mujoco model="robotiq_2f85_mirrored">\n'
                      '  <!-- GENERATED by make_ko_mirror.py: the ko gripper reflected by the\n'
                      '       MEASURED local mirror A (see the generator for its derivation and\n'
                      '       controls).  The authoritative source is the left-hand asset; edit\n'
                      '       THAT and regenerate, never this file. -->')
    return out


def mirror_stl(src: Path, dst: Path, A: np.ndarray) -> int:
    """v -> A v with winding flipped and normals recomputed.  Binary STL only."""
    raw = src.read_bytes()
    n = struct.unpack_from("<I", raw, 80)[0]
    assert len(raw) == 84 + n * 50, f"{src.name}: not a plain binary STL"
    out = bytearray(raw[:80] + struct.pack("<I", n))
    for i in range(n):
        off = 84 + i * 50
        tri = np.frombuffer(raw, dtype="<f4", count=12, offset=off).reshape(4, 3)
        v = (A @ tri[1:].T).T
        v = v[[0, 2, 1]]                       # winding flip: a reflection inverts orientation
        nrm = np.cross(v[1] - v[0], v[2] - v[0])
        ln = float(np.linalg.norm(nrm))
        nrm = nrm / ln if ln > 0 else nrm
        out += np.vstack([nrm, v]).astype("<f4").tobytes()
        out += raw[off + 48:off + 50]
    dst.write_bytes(bytes(out))
    return n


def main() -> int:
    A = derive_A()
    print(f"[mirror] A (measured, pose-independent, det {np.linalg.det(A):+.0f}):\n{A}")
    OUT_MESHDIR.mkdir(exist_ok=True)
    for stl in sorted(KO_MESHDIR.glob("*.stl")):
        n = mirror_stl(stl, OUT_MESHDIR / stl.name, A)
        print(f"[mirror] {stl.name}: {n} triangles baked")
    OUT_XML.write_text(mirror_xml(A))
    mujoco.MjModel.from_xml_path(str(OUT_XML))   # the baked asset must at least compile alone
    print(f"[mirror] wrote {OUT_XML.name} (compiles standalone)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
