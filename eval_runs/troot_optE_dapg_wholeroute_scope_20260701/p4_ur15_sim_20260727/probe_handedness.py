"""Which labelled arm appears on which side of the screen?

The log calls one arm L and the other R; Rs calls one of them the right-hand one.  Nobody has tied
the two together except through the log itself, which is circular.  This resolves it from the
model and the camera parameters alone: read each gripper's world position, then project it onto
the screen-right axis of each camera actually used to render the montage.
"""

import math
import runpy
import sys
from pathlib import Path

import numpy as np

S = Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/scratchpad")
sys.argv = ["ur15_steps.py", "/dev/null"]

# Build the cell exactly as the driver does, but stop before it starts stepping: import the driver
# as a module up to the point the model exists.  Simplest reliable way is to re-run its model build
# here, so read the pieces we need out of a fresh exec of the header.
src = (S / "ur15_steps.py").read_text()
cut = src.index("# ---- start pose:")
ns: dict = {}
exec(compile(src[:cut], "ur15_header", "exec"), ns)

m, d, PAD, SIDES = ns["m"], ns["d"], ns["PAD"], ns["SIDES"]
mujoco = ns["mujoco"]
mujoco.mj_forward(m, d)

print("world position of each labelled gripper (midpoint of its two pad bodies):")
pos = {}
for t in SIDES:
    p = 0.5 * (np.array(d.xpos[PAD[t][0]]) + np.array(d.xpos[PAD[t][1]]))
    pos[t] = p
    print(f"  arm {t}: x {p[0]:+.4f}  y {p[1]:+.4f}  z {p[2]:+.4f}")


def screen_right_axis(az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    f = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    r = np.cross(f, np.array([0.0, 0.0, 1.0]))
    return r / np.linalg.norm(r)


# the montage is hstack([wide, closeup]) -- wide on the left half, close-up on the right half
for tag, az, el in (("wide  (left half, azimuth 108 +-14)", 108.0, -22.0),
                    ("close (right half, azimuth 250)", 250.0, -16.0)):
    r = screen_right_axis(az, el)
    proj = {t: float(np.dot(r, pos[t])) for t in SIDES}
    right = max(proj, key=proj.get)
    print(f"\n{tag}")
    print(f"  screen-right axis in world = ({r[0]:+.3f}, {r[1]:+.3f}, {r[2]:+.3f})")
    for t in SIDES:
        print(f"    arm {t} projects to {proj[t]:+.4f}  -> appears on the "
              f"{'RIGHT' if t == right else 'LEFT'}")
