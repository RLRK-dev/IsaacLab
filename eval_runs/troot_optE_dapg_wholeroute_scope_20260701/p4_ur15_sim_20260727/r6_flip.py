"""Does the CLAW leg alone flip the verdict, with the cable in the mouth throughout?

p0's finding 5.  The negative control and the positive leg use different scenes, so between them
they show the predicate saying True somewhere and False elsewhere -- which is not the same as
showing either leg deciding.  In all four negative states the cable is 160-210 mm outside the
band, so the band leg is False no matter what the claws do.

So: take the AIMED pose from the positive leg, where the cable is in the mouth, and move only the
finger command.  The band leg should stay True while the claw leg crosses the floor, and the
verdict should flip in one column of one table.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "r6flip"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
held, cable_in_mouth, jaw_gaps, grasped = ns["held"], ns["cable_in_mouth"], ns["jaw_gaps"], ns["grasped"]
T = "R"

for t in ns["SIDES"]:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)

x_design = ns["GR"][0]
c, _ = ns["cable_at"](x_design)
q_from = np.array([d.qpos[a] for a in ns["QADR"][T]])
w, tgt, mag = ns["aim_slot_at"](T, c, q_from, seed=41, fix_x=x_design)
RAMP = int(4.0 / m.opt.timestep)
for s_ in range(RAMP + int(2.0 / m.opt.timestep)):
    f = min(1.0, s_ / RAMP)
    for k, i in enumerate(ns["AIDX"][T]):
        d.ctrl[i] = (1.0 - f) * q_from[k] + f * w[k]
    mujoco.mj_step(m, d)
print(f"[flip] aimed and arrived: seat error {mag*1000:.2f} mm\n")

floor = _cs.release_floor()
# p11 -100's requirement table.  A conjunction that comes out False does not say WHICH leg said
# so, which is why one control per leg is needed rather than a pile of Falses:
#   A-control  claws OPEN, cable IN the band   -> False expected: can the CLAW leg reject?
#   B-control  claws CLOSED, cable OUT of band -> False expected: can the BAND leg reject?
#              (that is r6_negcontrol.py -- every state there has the jaw away from the cable)
#   positive   both legs true                  -> True
print(f"{'finger cmd':>11} {'role':>10} {'backplate':>10} {'past floor':>11} {'mouth z':>9} "
      f"{'in band':>8} {'R6 held':>8} {'grasped':>8}")
for label, ctrl, role in (("OPEN", ns["OPEN"], "A-control"), ("HALF", ns["HALF"], "positive"),
                          ("release~197", 197, "A-control"), ("mid 215", 215, "positive"),
                          ("CLAMP", ns["CLAMP"], "positive")):
    d.ctrl[ns["GIDX"][T]] = ctrl
    for _ in range(int(2.5 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    pad = jaw_gaps(T)[0]
    inb, z = cable_in_mouth(T)
    print(f"{label:>11} {role:>10} {pad:10.2f} {str(pad < floor):>11} {z:9.2f} {str(inb):>8} "
          f"{str(held(T)):>8} {str(grasped(T)):>8}")
print(f"\nfloor = {floor:.2f} mm.  The band leg should hold True down the column while the claw leg "
      f"crosses;\nif held never changes, the verdict is not being decided by the claws.")
