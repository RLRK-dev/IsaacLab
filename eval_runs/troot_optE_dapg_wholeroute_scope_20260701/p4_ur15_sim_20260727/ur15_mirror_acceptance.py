"""Acceptance test for the mirrored arm asset, against Rs's supplied reference cell.

WHAT THIS IS.  p5 -160 / p18 -771 defined the closure condition for the new asset: feed the
LEFT arm's banked joint values to the MIRRORED arm and the tool must land on the reference's
RIGHT tool positions.  That turns "sign convention preserved, I think" into a one-line check.

WHY IT EXISTS ON DISK.  I reported "10/10" from a check whose output I did not keep, so the
number carried no denominator and could not be re-read.  This file is the denominator: every
pose the reference publishes, both position quantities, one line each, written to a file.

WHAT IS COMPARED.  tool0 is a rotation-only chain from wrist_3 (the reference's own
flange_from_wrist_3_rpy and tool0_from_flange_rpy carry no translation), so tool0's POSITION is
the wrist_3 body origin -- no convention assumption enters the position comparison.  The grip
point is a fixed offset in the tool frame; the offset is not assumed, it is SOLVED on the left
arm from the reference's own left grip points and only then applied, unchanged, to the mirrored
arm.  If the mirror convention is wrong, that is exactly where it shows.

THREE LEGS, because a single passing leg would not say which thing passed:
  control  left arm     on LEFT mount  + left joints   -> reference LEFT
                                        (does my mounting and FK reproduce the reference at all?)
  test     mirrored arm on RIGHT mount + left joints   -> reference RIGHT
                                        (the acceptance test proper)
  formula  stock arm    on RIGHT mount + right joints  -> reference RIGHT
                                        (the reference's own route: a NON-mirrored machine needs
                                        the R-formula values to reach the mirrored pose.  Shown
                                        so the difference the test watches is visible.  ⚠ It must
                                        be the RIGHT mount -- driving the left mount with right
                                        joints measures nothing, and my first cut did exactly
                                        that and read out half a metre of nonsense.)

Mounting is imported from ur15_cell_spec, never retyped, so this cannot drift from the driver.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ur15_cell_spec import SHOULDER_HEIGHT, TILT, YOKE_SPREAD  # noqa: E402

REF_DIR = Path("/home/rlrk/Downloads/ur15-dual-arm-cell")
REF_JSON = REF_DIR / "ur15-dual-arm-cell.json"
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
      "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
SIDE_SIGN = {"L": -1.0, "R": +1.0}
# tool0 from wrist_3: the reference's two rpy rotations, in its order.  Same expression the
# driver uses to hang the gripper (ur15_steps_wired.py:270), so the two cannot disagree.
R_TOOL = (Rotation.from_euler("xyz", [0.0, -np.pi / 2, -np.pi / 2])
          * Rotation.from_euler("xyz", [np.pi / 2, 0.0, np.pi / 2]))

PASS_MM = 1.0  # a pose lands if it is within 1 mm of the reference's published position


def build(arm_xml: str, sign: float):
    """One arm, on the cell's own mount, at the side `sign` puts it.  No gripper, no table."""
    root = mujoco.MjSpec.from_string(
        '<mujoco model="acc"><worldbody><body name="column"/></worldbody></mujoco>')
    q = Rotation.from_euler("xyz", [0.0, sign * TILT, 0.0]).as_quat()
    f = root.body("column").add_frame(
        pos=[sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT],
        quat=[float(q[3]), float(q[0]), float(q[1]), float(q[2])])
    arm = mujoco.MjSpec.from_file(str(HERE / arm_xml))
    f.attach_body(arm.bodies[1], "a_", "")
    m = root.compile()
    return m, mujoco.MjData(m)


def tool_pose(m, d, joints):
    """tool0 (position, rotation) with the arm held at `joints`."""
    for name, q in zip(J6, joints):
        d.qpos[m.joint(f"a_{name}").qposadr[0]] = q
    mujoco.mj_kinematics(m, d)
    b = m.body("a_wrist_3_link").id
    return d.xpos[b].copy(), Rotation.from_matrix(d.xmat[b].reshape(3, 3)) * R_TOOL


def main() -> int:
    ref = json.loads(REF_JSON.read_text())
    poses = ref["poses"]
    grip_len = ref["end_effector"]["grip_point_offset_from_tool0_m"]

    mL, dL = build("ur15_base.xml", SIDE_SIGN["L"])           # stock arm, left mount
    mM, dM = build("ur15_base_mirrored.xml", SIDE_SIGN["R"])  # mirrored arm, right mount
    mF, dF = build("ur15_base.xml", SIDE_SIGN["R"])           # stock arm, right mount

    out = []
    out.append("UR15 MIRRORED-ARM ACCEPTANCE TEST vs Rs's supplied reference cell")
    out.append(f"reference : {REF_JSON}")
    out.append(f"asset     : ur15_base_mirrored.xml  (mirrored build) / ur15_base.xml (left)")
    out.append(f"mounting  : YOKE_SPREAD={YOKE_SPREAD}  TILT={np.degrees(TILT):.4f} deg  "
               f"SHOULDER_HEIGHT={SHOULDER_HEIGHT}  (imported from ur15_cell_spec, not retyped)")
    out.append(f"lands if within {PASS_MM:.1f} mm of the reference's published position")
    out.append("")

    # --- the grip offset is SOLVED on the left arm, not assumed -------------------------------
    solved = []
    for name, p in poses.items():
        pos, rot = tool_pose(mL, dL, p["left"]["joints_on_yoke_rad"])
        want = np.array(p["left"]["grip_point_position_m"])
        solved.append(rot.inv().apply(want - pos))
    solved = np.array(solved)
    v_local = solved.mean(axis=0)
    spread_mm = np.abs(solved - v_local).max() * 1e3
    out.append(f"grip offset solved in the tool frame from the reference's own LEFT grip points:")
    out.append(f"  v_local = [{v_local[0]:+.6f} {v_local[1]:+.6f} {v_local[2]:+.6f}] m   "
               f"|v| = {np.linalg.norm(v_local):.6f} m vs the reference's stated {grip_len} m")
    out.append(f"  worst deviation of any one pose from that constant = {spread_mm:.4f} mm "
               f"(a constant offset is what makes it a rigid tool point)")
    out.append("")

    legs = {
        "control": (mL, dL, "left", "left", "stock arm on the LEFT mount"),
        "test": (mM, dM, "left", "right", "MIRRORED arm on the RIGHT mount"),
        "formula": (mF, dF, "right", "right", "stock arm on the RIGHT mount"),
        # A test that cannot come out differently is not a test.  This leg is the mistake the
        # acceptance test exists to catch -- the mirrored arm fed the R-formula values, i.e. the
        # convention applied twice.  It MUST miss.  If it ever lands, the other three legs are
        # measuring something that does not depend on the convention at all.
        "negative": (mM, dM, "right", "right", "MIRRORED arm on the RIGHT mount"),
    }
    tally = {k: [0, 0] for k in legs}
    worst = {k: (0.0, "") for k in legs}

    for leg, (m, d, drive, want_side, what) in legs.items():
        out.append(f"=== LEG {leg}: {what} driven by the "
                   f"{drive.upper()} joint values, compared to the reference's "
                   f"{want_side.upper()} positions ===")
        hdr = f"{'pose':24s} {'tool0 err mm':>13s} {'grip err mm':>12s}   verdict"
        out.append(hdr)
        for name, p in poses.items():
            pos, rot = tool_pose(m, d, p[drive]["joints_on_yoke_rad"])
            grip = pos + rot.apply(v_local)
            e_t = np.linalg.norm(pos - np.array(p[want_side]["tool0_position_m"])) * 1e3
            e_g = np.linalg.norm(grip - np.array(p[want_side]["grip_point_position_m"])) * 1e3
            ok_t, ok_g = e_t <= PASS_MM, e_g <= PASS_MM
            tally[leg][0] += int(ok_t) + int(ok_g)
            tally[leg][1] += 2
            for e in (e_t, e_g):
                if e > worst[leg][0]:
                    worst[leg] = (e, name)
            note = ""
            if p[want_side].get("retarget_residual_m"):
                # ⚠ NOT a tolerance on this test.  The reference's residual measures its ON-YOKE
                # pose against its own earlier FLAT-mounting pose; this test measures joints
                # against the on-yoke tool position the reference publishes beside them.  The two
                # do not overlap, so this row is held to the same 1 mm as every other row.
                note = (f"  <- the reference's own on-yoke-vs-tuned residual here is "
                        f"{p[want_side]['retarget_residual_m'] * 1e3:.1f} mm; it is not a "
                        f"tolerance on this test and this row is held to the same {PASS_MM:.1f} mm")
            out.append(f"{name:24s} {e_t:13.4f} {e_g:12.4f}   "
                       f"{'lands' if ok_t and ok_g else 'MISSES'}{note}")
        n, tot = tally[leg]
        out.append(f"-- {leg}: {n}/{tot} position pairs land within {PASS_MM:.1f} mm "
                   f"(worst {worst[leg][0]:.4f} mm at {worst[leg][1]})")
        out.append("")

    out.append("DENOMINATOR, stated so it cannot be read as more than it is:")
    out.append(f"  {len(poses)} poses the reference publishes x 2 position quantities "
               f"(tool0, grip point) = {len(poses) * 2} L/R position pairs per leg.")
    resid = [k for k, p in poses.items() if p["left"].get("retarget_residual_m")]
    out.append(f"  Nothing is excluded: all {len(poses) * 2} are compared on every leg.  "
               f"{len(resid)} pose ({resid}) carries a non-zero on-yoke-vs-tuned residual in the "
               f"reference, which this test does not measure and does not relax for.")
    out.append("  The test leg IS the acceptance test.  Control says whether my mounting and FK "
               "reproduce the reference at all -- without it, a passing test leg could be two "
               "errors cancelling.  Formula is the reference's own non-mirrored route, and its "
               "size is the difference the mirrored asset removes.")
    out.append("  ⛔ What this does NOT cover: joint LIMITS (the sign convention is checked here "
               "by where the tool lands, and the atomic axis-and-limit inversion is not exercised "
               "by poses that all sit inside symmetric ranges), collision geometry, inertias, "
               "and anything dynamic.  This is a kinematics-of-position test.")

    passed = (tally["test"][0] == tally["test"][1]      # the acceptance test lands, and
              and tally["negative"][0] == 0)            # the convention-applied-twice leg misses
    out.append("")
    out.append(f"RESULT: {'PASS' if passed else 'FAIL'} -- acceptance leg "
               f"{tally['test'][0]}/{tally['test'][1]}, and the negative leg lands "
               f"{tally['negative'][0]}/{tally['negative'][1]} (it must land 0, "
               f"or the test is not reading the convention).")

    text = "\n".join(out) + "\n"
    (HERE / "UR15_MIRROR_ACCEPTANCE_20260729.txt").write_text(text)
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
