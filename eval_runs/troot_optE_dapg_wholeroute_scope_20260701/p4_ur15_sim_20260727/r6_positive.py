"""R6's positive leg, statically: cover the cable and close on it.

p5 -102(2): not "place the cable in the jaw" -- that failed and moved it further away -- but leave
the cable where it rests and bring the OPEN jaw over it using the aim from clip design §4 (y and z
only, x a design constant), then close to CLAMP and evaluate.

⛔ Aiming is not optional here: without it this measures whether a 70 mm window happens to land on
the cable, which is luck, not the predicate.

⛔ This is instrument evidence, not a task-success claim: one step, no route, and the arm gets
there through its servos -- nothing is written into a pose.  p18 -438(2) classes it with today's
negative control and settle sweeps.  A False is as informative as a True.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "r6positive"}
# cut at the step loop, not at the start pose: solve_ik is defined further down, and
# aim_slot_at calls it -- cutting early gave a NameError rather than a measurement.
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
held, claw_gap, cable_in_mouth, grasped = ns["held"], ns["claw_gap"], ns["cable_in_mouth"], ns["grasped"]
jaw_gaps, pinch, cable_at = ns["jaw_gaps"], ns["pinch"], ns["cable_at"]

T = "R"
for t in ns["SIDES"]:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)

x_design = ns["GR"][0]                      # the design x for this hand -- NOT re-aimed (§4)
c, _ = cable_at(x_design)
q_now = {t: np.array([d.qpos[a] for a in ns["QADR"][t]]) for t in ns["SIDES"]}
w, tgt, mag = ns["aim_slot_at"](T, c, q_now[T], seed=41, fix_x=x_design)
print(f"[pos] aim at the resting cable: seat error {mag*1000:5.2f} mm, target {np.round(tgt,4)}")

# servo there, the way the step loop does: ramp the command, no writes to any pose
q_from = q_now[T].copy()
RAMP = int(4.0 / m.opt.timestep)
for s_ in range(RAMP + int(2.0 / m.opt.timestep)):
    f = min(1.0, s_ / RAMP)
    for k, i in enumerate(ns["AIDX"][T]):
        d.ctrl[i] = (1.0 - f) * q_from[k] + f * w[k]
    mujoco.mj_step(m, d)
resid = float(np.abs(np.array([d.qpos[a] for a in ns["QADR"][T]]) - w).max())
inb, z = cable_in_mouth(T)
print(f"[pos] arrived: residual {resid*1000:6.2f} mrad | backplate {jaw_gaps(T)[0]:6.2f} mm | "
      f"pad-local z {z:7.2f} mm (band 25.00-39.00) in-band={inb}")

for _ in range(int(ns['FINGER_RAMP'] / m.opt.timestep)):
    d.ctrl[ns["GIDX"][T]] = ns["CLAMP"]
    mujoco.mj_step(m, d)
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
inb, z = cable_in_mouth(T)
pad = jaw_gaps(T)[0]
print(f"\n[pos] CLOSED: backplate {pad:6.2f} mm (floor {_cs.release_floor():5.2f}) -> past floor="
      f"{pad < _cs.release_floor()}")
print(f"[pos]          pad-local z {z:7.2f} mm in band 25.00-39.00 -> {inb}")
print(f"[pos]          R6 held() = {held(T)}   (old grasped() = {grasped(T)})")
