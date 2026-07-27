"""R6(iii): the negative control.  Can the predicate come out False when it should?

p5 requires it for the conjunction, and the reason is the day's own lesson -- a predicate that
cannot discriminate is not evidence.  Four states, two of which the predicate MUST reject:

    fingers wide open      -> nothing between the claws            -> must be False
    cable moved out of the mouth, jaw closed -> tips shut on air   -> must be False
    half closed, jaw away  -> tips 1.8 mm, cable NOT inside        -> must be False
    clamped, jaw away      -> tips through each other, no cable    -> must be False

⚠ Every state here has the jaw away from the cable, so the mouth-band leg is False throughout and
only ever the same leg is doing the rejecting.  That is what r6_flip.py is for: the same finger
commands from the AIMED pose, where the band leg starts True and the claw leg alone decides.
This file's header used to claim a "cable inside -> must be True" row; the body never did that,
and a header promising what the code does not do is the defect this whole day has been about.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "negcontrol"}
exec(compile(src[:src.index("# ---- start pose:")], "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
held, claw_gap, cable_in_mouth, grasped = ns["held"], ns["claw_gap"], ns["cable_in_mouth"], ns["grasped"]

def settle(ctrl, seconds=2.0):
    for t in ns["SIDES"]:
        d.ctrl[ns["GIDX"][t]] = ctrl
    for _ in range(int(seconds / m.opt.timestep)):
        mujoco.mj_step(m, d)

print(f"\n{'state':34s} {'claw':>8} {'mouth z':>9} {'in band':>8} {'held':>6} {'grasped':>8}  expect")
for label, ctrl, expect in (("wide open, nothing between", ns["OPEN"], "False"),
                            ("half closed", ns["HALF"], "-"),
                            ("clamped", ns["CLAMP"], "-")):
    settle(ctrl)
    inb, z = cable_in_mouth("R")
    print(f"{label:34s} {claw_gap('R'):8.2f} {z:9.2f} {str(inb):>8} {str(held('R')):>6} "
          f"{str(grasped('R')):>8}  {expect}")

# ⛔ The positive case is NOT here: placing the cable in the jaw moved it further away
# (491 mm) and measured nothing.  p5's covering approach works and lives in
# r6_positive.py -- keep the two apart so this file stays the negatives.

# now take the cable away and close on nothing: the predicate must reject it
free = m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "cable_free")]
d.qpos[free + 1] += 0.5          # slide the whole cable half a metre in y
mujoco.mj_forward(m, d)
settle(ns["CLAMP"])
inb, z = cable_in_mouth("R")
print(f"{'cable moved away, jaw CLAMPED':34s} {claw_gap('R'):8.2f} {z:9.2f} {str(inb):>8} "
      f"{str(held('R')):>6} {str(grasped('R')):>8}  False")
