"""Does the opposing-claw distance keep growing as the jaw shuts, or does the query bottom out?

p18: the run that clamped shows pad faces +7.36 mm, which is CLOSER than the 10.16 mm at which
the opposing claws were measured to meet.  Either 10.16 does not apply in that run, or something
else changed.  Sweep the same pair on the model the run actually reads.  Gripper alone, no cable.
"""

import mujoco
import numpy as np

XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml"
m = mujoco.MjSpec.from_file(XML).compile()
d = mujoco.MjData(m)
gid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n)
PAIRS = {"pad1 x pad1": (gid("left_pad1"), gid("right_pad1")),
         "f1ext x f1ext": (gid("left_pad_f1ext"), gid("right_pad_f1ext")),
         "f2ext x f2ext": (gid("left_pad_f2ext"), gid("right_pad_f2ext"))}

print(f"{'ctrl':>5} " + " ".join(f"{k:>14}" for k in PAIRS))
for ctrl in (205, 210, 215, 219, 221, 225, 229, 233, 236, 240, 250, 255):
    mujoco.mj_resetData(m, d)
    d.ctrl[0] = ctrl
    for _ in range(2500):
        mujoco.mj_step(m, d)
    vals = [mujoco.mj_geomDistance(m, d, a, b, 1.0, None) * 1000.0 for a, b in PAIRS.values()]
    print(f"{ctrl:5d} " + " ".join(f"{v:14.2f}" for v in vals))

print("\nhalf-extents of a claw box [mm]: "
      f"{np.array(m.geom_size[gid('left_pad_f1ext')])*1000}")
print("contact exclusions in this model:", int(m.nexclude))
