"""Can three saddles hold a 600 mm cable inside +-300 mm and still stay clear of both grasp spans?

p5's ruling leaves a better option open: if the cable is the SSOT's 600 mm rather than the cell's
960 mm, both authorities agree and the link count drops.  The condition p5 set is the one already
recorded in the driver -- `ur15_steps.py:53` "saddles kept clear of both 88 mm grasp spans" -- and
the present saddles fail it only because one of them sits at -340, outside the shorter cable.

So measure the windows: where along the cable is a saddle forbidden, and what is left.

Nothing here places a saddle.  It reports the free intervals; choosing from them is p5's.
"""

import mujoco
import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).parent))
import ur15_cell_spec as _cellspec  # noqa: E402
import numpy as np

print(f"[stack] {_cellspec.stack_line()}")   # which substrate this was measured on -- byte identity alone cannot say

XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
m = mujoco.MjSpec.from_file(XML).compile()
d = mujoco.MjData(m)
d.ctrl[0] = 236                      # closed: the state it is in while it sits over a saddle
for _ in range(3000):
    mujoco.mj_step(m, d)

# the gripper's half-extent along the cable axis, measured off the asset rather than assumed
BASE = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base")
R = np.array(d.xmat[BASE]).reshape(3, 3)
o = np.array(d.xpos[BASE])
CORNERS = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
CLAW = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{s_}_pad_{c_}ext")
        for s_ in ("left", "right") for c_ in ("f1", "f2")]
slot_z = float(np.mean([(R.T @ (np.array(d.geom_xpos[g]) - o))[2] for g in CLAW]))

# Only the parts that reach down to saddle height can hit a saddle.  Taking every geom lets the
# base mesh's bounding sphere -- 150 mm up the tool and nowhere near a saddle -- set the answer,
# which inflated this to 78.6 mm on the first pass.  That figure is withdrawn.
half, who = 0.0, ""
for g in range(m.ngeom):
    c = R.T @ (np.array(d.geom_xpos[g]) - o)
    Rg = R.T @ np.array(d.geom_xmat[g]).reshape(3, 3)
    if int(m.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_BOX):
        pts = [c + Rg @ (k * m.geom_size[g]) for k in CORNERS]
        low = max(p_[2] for p_ in pts)
        ext = max(abs(p_[0]) for p_ in pts)
    else:
        low = c[2] + float(m.geom_rbound[g])
        ext = abs(c[0]) + float(m.geom_rbound[g])
    if low < slot_z:          # sits entirely above the cable -> cannot touch a saddle
        continue
    if ext > half:
        half, who = ext, mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f"geom{g}"
print(f"gripper half-extent across the cable axis, closed, counting only the parts that")
print(f"reach down to the cable or below: {half*1000:.1f} mm  (widest: {who})")

SADDLE_HALF = 0.014                  # ur15_steps.py rest_xml: post half-size
GRIP_HALF_SPAN = 0.044               # task_config.py:235
C1_X, C2_X = 0.150, 0.040            # driver clip x
RX_MID = 0.5 * (C1_X + C2_X)         # the re-grasp position, ur15_steps.py:818

hands = {"C1 left": C1_X - GRIP_HALF_SPAN, "C1 right": C1_X + GRIP_HALF_SPAN,
         "C2 left": C2_X - GRIP_HALF_SPAN, "C2 right": C2_X + GRIP_HALF_SPAN,
         "re-grasp": RX_MID}
keep = half + SADDLE_HALF            # centre-to-centre needed so the two solids do not overlap
print(f"a saddle centre must stay {keep*1000:.1f} mm from any hand centre\n")

blocked = []
for name, x in sorted(hands.items(), key=lambda kv: kv[1]):
    lo, hi = x - keep, x + keep
    print(f"  {name:10s} hand at {x*1000:+7.1f} mm  blocks [{lo*1000:+7.1f}, {hi*1000:+7.1f}]")
    blocked.append((lo, hi))

merged = []
for lo, hi in sorted(blocked):
    if merged and lo <= merged[-1][1]:
        merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
    else:
        merged.append((lo, hi))

for total, label in ((0.600, "SSOT 600 mm (40 x 15)"), (0.960, "the cell's 960 mm")):
    lo_end, hi_end = -total / 2, total / 2
    free, cur = [], lo_end
    for lo, hi in merged:
        if hi < lo_end or lo > hi_end:
            continue
        if lo > cur:
            free.append((cur, min(lo, hi_end)))
        cur = max(cur, hi)
    if cur < hi_end:
        free.append((cur, hi_end))
    free = [(a, b) for a, b in free if b - a >= 2 * SADDLE_HALF]
    print(f"\n{label}: cable spans [{lo_end*1000:+.0f}, {hi_end*1000:+.0f}] mm")
    for a, b in free:
        print(f"    free for a saddle: [{a*1000:+7.1f}, {b*1000:+7.1f}]  "
              f"width {(b-a)*1000:6.1f} mm  -> fits {int((b-a)//(2*SADDLE_HALF))} saddle(s)")
    fits = sum(int((b - a) // (2 * SADDLE_HALF)) for a, b in free)
    print(f"    total saddles that fit: {fits}  -> three saddles "
          f"{'FIT' if fits >= 3 else 'DO NOT FIT'}")
