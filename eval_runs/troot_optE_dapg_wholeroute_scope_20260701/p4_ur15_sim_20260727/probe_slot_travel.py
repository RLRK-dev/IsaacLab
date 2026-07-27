"""How far, and which way, does the ko mouth move while the jaw closes?

p5 added a requirement: the cable must be inside the mouth for the WHOLE closing motion, not just
at the end.  If the mouth travels further than its own height (10.00 mm) then the open-pose band
and the closed-pose band do not overlap, no single aim point can satisfy that, and the design has
to change from "avoid contact" to "do not flick the cable out".  So measure the travel.

Gripper alone, no arm, no cell: the arm cannot contribute, so whatever moves is the four-bar.
"""

import mujoco
import numpy as np

XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
m = mujoco.MjSpec.from_file(XML).compile()
d = mujoco.MjData(m)

CLAW = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{s}_pad_{c}ext")
        for s in ("left", "right") for c in ("f1", "f2")]
PADB = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{s}_pad") for s in ("left", "right")]
BASE = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base")


def state():
    """mouth centre and the two same-pad claw z positions, in the gripper base frame."""
    R = np.array(d.xmat[BASE]).reshape(3, 3)
    o = np.array(d.xpos[BASE])
    g = {n: R.T @ (np.array(d.geom_xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n)]) - o)
         for n in ("left_pad_f1ext", "left_pad_f2ext", "right_pad_f1ext", "right_pad_f2ext")}
    mouth = np.mean([g[k] for k in g], axis=0)
    pinch = np.mean([R.T @ (np.array(d.xpos[b]) - o) for b in PADB], axis=0)
    return mouth, pinch, g


rows = []
for ctrl in (18, 60, 100, 140, 180, 214, 236):
    mujoco.mj_resetData(m, d)
    d.ctrl[0] = ctrl
    for _ in range(4000):
        mujoco.mj_step(m, d)
    mouth, pinch, g = state()
    rows.append((ctrl, mouth, pinch, g))

m0 = rows[0][1]
print(f"{'ctrl':>5} {'mouth x':>9} {'mouth y':>9} {'mouth z':>9} {'travel from OPEN':>18} "
      f"{'mouth height':>13}")
for ctrl, mouth, pinch, g in rows:
    trav = (mouth - m0) * 1000.0
    # the mouth opening is the same-pad claw separation, along the pad's own long axis
    h = abs(g["left_pad_f1ext"][2] - g["left_pad_f2ext"][2]) * 1000.0
    print(f"{ctrl:5d} {mouth[0]*1000:9.2f} {mouth[1]*1000:9.2f} {mouth[2]*1000:9.2f} "
          f"  ({trav[0]:+6.2f},{trav[1]:+6.2f},{trav[2]:+6.2f}) {np.linalg.norm(trav):6.2f}"
          f" {h:13.2f}")

tot = (rows[-1][1] - m0) * 1000.0
print(f"\ntotal mouth travel OPEN->CLAMP = ({tot[0]:+.2f}, {tot[1]:+.2f}, {tot[2]:+.2f}) mm, "
      f"magnitude {np.linalg.norm(tot):.2f} mm")
print(f"mouth height (same-pad claw gap) = {abs(rows[-1][3]['left_pad_f1ext'][2] - rows[-1][3]['left_pad_f2ext'][2])*1000:.2f} mm")
print("-> bands OVERLAP, one aim point can work" if np.linalg.norm(tot) < 10.0
      else "-> travel EXCEEDS the mouth height: no single aim point stays inside throughout")
