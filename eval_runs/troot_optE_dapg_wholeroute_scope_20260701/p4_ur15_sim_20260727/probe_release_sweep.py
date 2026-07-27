"""How far does the gripper hang below the cable, as a function of how far it is told to open?

p5 needs this to settle the release phase, and p11 added the point that decides it: the cable
escapes between the CLAW TIPS, which stand proud of the flat pads, not between the pads.  So the
release threshold is not "pad faces reach 8 mm" -- it is whatever pad-face gap puts the claw tips
8 mm apart, which p11 puts at a pad gap near 18 mm.  Measure the gap pair, do not assume it.

ctrl 214 is included by name: p11 extrapolates that HALF leaves the claw tips about 2 mm apart,
which would mean the step table's "half open" never releases the cable at all.  Extrapolation
through a four-bar is not evidence either way, so measure it.

Method is the one used for ctrl 219: gripper alone, no arm, no cell, no cable, each command
settled, boxes evaluated at their eight corners exactly.
"""

import mujoco
import numpy as np

XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
m = mujoco.MjSpec.from_file(XML).compile()
d = mujoco.MjData(m)

gid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n)
CLAW = [gid(f"{s}_pad_{c}ext") for s in ("left", "right") for c in ("f1", "f2")]
PADS = (gid("left_pad1"), gid("right_pad1"))
F1 = (gid("left_pad_f1ext"), gid("right_pad_f1ext"))
BASE = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base")
CORNERS = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
BOX = int(mujoco.mjtGeom.mjGEOM_BOX)
ROLLS = (0.0, 0.30, 0.55)

CTRLS = [0, 18, 40, 60, 80, 100, 120, 140, 160, 170, 180, 190, 200, 205, 210,
         214, 219, 225, 230, 236, 240, 250, 255]

rows = []
for ctrl in CTRLS:
    mujoco.mj_resetData(m, d)
    d.ctrl[0] = ctrl
    for _ in range(3000):
        mujoco.mj_step(m, d)

    pad_gap = mujoco.mj_geomDistance(m, d, PADS[0], PADS[1], 1.0, None) * 1000.0
    claw_gap = mujoco.mj_geomDistance(m, d, F1[0], F1[1], 1.0, None) * 1000.0

    R = np.array(d.xmat[BASE]).reshape(3, 3)
    o = np.array(d.xpos[BASE])
    slot = np.mean([R.T @ (np.array(d.geom_xpos[g]) - o) for g in CLAW], axis=0)

    pts = []
    for g in range(m.ngeom):
        c = R.T @ (np.array(d.geom_xpos[g]) - o) - slot
        Rg = R.T @ np.array(d.geom_xmat[g]).reshape(3, 3)
        if int(m.geom_type[g]) == BOX:
            pts.extend(c + Rg @ (k * m.geom_size[g]) for k in CORNERS)
        else:
            pts.append(c + np.array([0, 0, float(m.geom_rbound[g])]))

    reach = [max(p[2] * np.cos(r) + p[1] * np.sin(r) for p in pts) * 1000.0 for r in ROLLS]
    rows.append((ctrl, pad_gap, claw_gap, reach))

print(f"{'ctrl':>5} {'pad1 gap':>10} {'claw gap':>10}   "
      + " ".join(f"{'reach@roll ' + f'{r:.2f}':>17}" for r in ROLLS))
for ctrl, pg, cg, reach in rows:
    mark = "  <- HALF" if ctrl == 214 else ("  <- CLAMP" if ctrl == 236 else
                                            ("  <- OPEN" if ctrl == 18 else ""))
    print(f"{ctrl:5d} {pg:10.2f} {cg:10.2f}   "
          + " ".join(f"{v:17.1f}" for v in reach) + mark)

print("\n-- the release point p11 asks for: the pad gap whose CLAW gap is 8.00 mm (a O8 cable) --")
seq = [(r[0], r[1], r[2], r[3]) for r in rows]
found = False
for (c0, p0, g0, r0), (c1, p1, g1, r1) in zip(seq, seq[1:]):
    if (g0 - 8.0) * (g1 - 8.0) <= 0 and g0 != g1:
        f = (8.0 - g0) / (g1 - g0)
        print(f"claw gap crosses 8.00 mm between ctrl {c0} and {c1}: ctrl ~ {c0 + f*(c1-c0):.1f}, "
              f"pad gap ~ {p0 + f*(p1-p0):.2f} mm")
        for k, rr in enumerate(ROLLS):
            print(f"    reach below the cable at roll {rr:.2f} = {r0[k] + f*(r1[k]-r0[k]):.1f} mm")
        found = True
if not found:
    print("the claw gap never crosses 8.00 mm over this command range -- read the table above")

print("\n-- and at ctrl 214 exactly (p11's suspicion that HALF does not release) --")
for ctrl, pg, cg, reach in rows:
    if ctrl == 214:
        print(f"pad1 gap {pg:.2f} mm, claw tips {cg:.2f} mm apart"
              f"  -> a O8 cable {'CAN' if cg >= 8.0 else 'CANNOT'} pass between the claws")
