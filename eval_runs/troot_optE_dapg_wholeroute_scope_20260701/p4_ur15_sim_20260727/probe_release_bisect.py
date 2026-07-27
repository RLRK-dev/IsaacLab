"""Re-derive the release opening with the margin taken from the right axis.

My first attempt added half the mouth's surplus, 3.00 mm.  p5 caught that this crosses axes: the
mouth opening is measured ACROSS the mouth, while the claw tips separate along the CLOSING
direction, and a margin from one axis says nothing about play in the other.

The margin belongs to whatever constrains the cable sideways at the moment of release, and at
STEP 17 that is the clip groove, which runs along the same axis as the claw gap.  So:

    max sideways offset = (groove width - cable diameter) / 2
    claw tips must clear = cable diameter + that offset

Both terms are read off sources -- the groove from the env's own clip table, the cable from
task_config -- so the margin follows the clip rather than being chosen.

p5 interpolated the command as roughly 188 but was explicit that the interpolation is not the
instruction: bisect for it, and if the two disagree the bisection is the answer.
"""

import sys

import mujoco
import numpy as np

sys.path.insert(0, "/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/"
                   "p4_ur15_sim_20260727")
import ur15_cell_spec as S   # noqa: E402

XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
m = mujoco.MjSpec.from_file(XML).compile()
d = mujoco.MjData(m)
gid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n)
PADS = (gid("left_pad1"), gid("right_pad1"))
TIPS = (gid("left_pad_f1ext"), gid("right_pad_f1ext"))
CLAW = [gid(f"{s}_pad_{c}ext") for s in ("left", "right") for c in ("f1", "f2")]
BASE = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base")
CORNERS = np.array([[a, b, c] for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)], float)
BOX = int(mujoco.mjtGeom.mjGEOM_BOX)

# the groove, off the clip table the module reads from the env source
walls = [p for p in S.CLIP_PARTS if abs(p[2] - 0.0125) < 1e-9]
groove = 2.0 * (abs(walls[0][1]) - walls[0][4])
cable = 2.0 * S.CABLE_R
offset = 0.5 * (groove - cable)
want_tips = cable + offset
print(f"groove width read from the clip table: {groove*1000:.2f} mm")
print(f"cable {cable*1000:.2f} mm -> it can sit up to {offset*1000:.2f} mm off the groove centre")
print(f"=> claw tips must clear {want_tips*1000:.2f} mm  (p5 states 11.50)\n")


def settle(ctrl):
    mujoco.mj_resetData(m, d)
    d.ctrl[0] = ctrl
    for _ in range(3000):
        mujoco.mj_step(m, d)
    pad = mujoco.mj_geomDistance(m, d, PADS[0], PADS[1], 1.0, None)
    tip = mujoco.mj_geomDistance(m, d, TIPS[0], TIPS[1], 1.0, None)
    return pad, tip


def bisect(fn, target, lo=120.0, hi=255.0, n=18):
    """Smallest command whose gap is still at least `target` (the gap shrinks as ctrl rises)."""
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if fn(settle(mid)) >= target:
            lo = mid
        else:
            hi = mid
    return lo


c_tip = bisect(lambda g: g[1], want_tips)
c_pad = bisect(lambda g: g[0], 0.02170)
for label, c in (("claw tips clear 11.50", c_tip), ("pad faces reach 21.70", c_pad)):
    pad, tip = settle(c)
    print(f"{label:24s} -> ctrl {c:7.2f}   pad {pad*1000:6.2f} mm   tips {tip*1000:6.2f} mm")
print(f"\nthe two agree to {abs(c_tip - c_pad):.2f} ctrl counts"
      f"  (p5's interpolation said about 188)")

# how far the gripper hangs below the cable at that command
mujoco.mj_resetData(m, d)
d.ctrl[0] = c_tip
for _ in range(3000):
    mujoco.mj_step(m, d)
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
print("\nreach below the cable at the release command:")
for roll in (0.0, 0.30, 0.55):
    print(f"    roll {roll:.2f}: {max(p[2]*np.cos(roll) + p[1]*np.sin(roll) for p in pts)*1000:6.1f} mm")
print("(for comparison the sweep gave 19.7 mm at roll 0.55 for the old 18.19 mm crossing,")
print(" and 35.7 mm at full open)")
