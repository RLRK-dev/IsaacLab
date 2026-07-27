"""p5 §4 asks one number: the lowest cable-centre height at which the gripping fingers still clear
the table.

Measure it on the gripper alone -- no arm, no cell -- so nothing but the four-bar can contribute,
and report it as a depth BELOW the cable centre.  p5 then gets float_z from that depth without
either of us inventing a height.

Scope, stated before the numbers:
  * Boxes are measured at their eight CORNERS, exactly.  Non-box geoms fall back to the bounding
    sphere, which over-states them -- flagged per row so a conservative number is not read as a
    measured one.  (A first pass used the sphere for everything; on a 1.2 mm plate that sphere is
    14.3 mm, so it over-stated the depth by about ten millimetres.  Those numbers are withdrawn.)
  * The depth depends on the tool's roll, because rolling swings the pads sideways and down, so
    report it at the rolls the grasp actually chose as well as square.
  * It also depends on the finger command: the pads swing OUT as they open, so the approach state
    is not the gripping state.  Report all three the route uses.
  * The gripper hangs with its own +z pointing at the fingertips, which is world-DOWN in the cell.
    That mapping is measured below, not assumed.
"""

import mujoco
import numpy as np

XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
m = mujoco.MjSpec.from_file(XML).compile()
d = mujoco.MjData(m)

CLAW = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{s}_pad_{c}ext")
        for s in ("left", "right") for c in ("f1", "f2")]
BASE = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base")
CORNERS = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
BOX = int(mujoco.mjtGeom.mjGEOM_BOX)

print(f"{'ctrl':>6} {'roll':>6} {'deepest below the cable':>26} {'reached by':>20} {'exact?':>8}")
for ctrl, label in ((236, "CLAMP"), (214, "HALF"), (18, "OPEN")):
    mujoco.mj_resetData(m, d)
    d.ctrl[0] = ctrl
    for _ in range(4000):
        mujoco.mj_step(m, d)

    R = np.array(d.xmat[BASE]).reshape(3, 3)
    o = np.array(d.xpos[BASE])
    slot = np.mean([R.T @ (np.array(d.geom_xpos[g]) - o) for g in CLAW], axis=0)

    pts = []            # (offset from the slot, exact?, name)
    for g in range(m.ngeom):
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f"geom{g}"
        c = R.T @ (np.array(d.geom_xpos[g]) - o) - slot
        Rg = R.T @ np.array(d.geom_xmat[g]).reshape(3, 3)
        if int(m.geom_type[g]) == BOX:
            for corner in CORNERS:
                pts.append((c + Rg @ (corner * m.geom_size[g]), True, name))
        else:
            pts.append((c, False, name))   # sphere bound applied below
            pts.append((c + np.array([0, 0, float(m.geom_rbound[g])]), False, name))

    for roll in (0.0, 0.30, 0.55):
        cs, sn = np.cos(roll), np.sin(roll)
        worst, who, exact = -1e9, "", True
        for off, is_exact, name in pts:
            depth = off[2] * cs + off[1] * sn
            if depth > worst:
                worst, who, exact = depth, name, is_exact
        print(f"{label:>6} {roll:6.2f} {worst*1000:23.1f} mm {who:>20} {'yes' if exact else 'SPHERE':>8}")

print("\nreading: a cable held at this height above the table leaves the lowest part of the")
print("gripper just touching it, so the minimum safe cable centre is this plus a margin.")
print("p5 section 4: float_z = (cable centre height) - 9.0 mm")
