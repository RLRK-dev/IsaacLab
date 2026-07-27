"""R6's positive leg, statically: cover the cable and close on it -- BOTH arms.

p5 -106: a quantity that comes in pairs gets written down in pairs.  The first version
ran one arm (R) and reported 6.67 mm without saying so; the other side was not dropped,
it was never taken.  Both are aimed and closed here.

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

ARMS = ("L", "R")
for t in ns["SIDES"]:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)

q_now = {t: np.array([d.qpos[a] for a in ns["QADR"][t]]) for t in ns["SIDES"]}
W, MAG = {}, {}
for T in ARMS:
    x_design = (ns["GL"] if T == "L" else ns["GR"])[0]   # design x per hand -- NOT re-aimed (§4)
    c, _ = cable_at(x_design)
    W[T], _tg, MAG[T] = ns["aim_slot_at"](T, c, q_now[T], seed=41 + (T == "R"), fix_x=x_design)
    print(f"[pos] {T}: aim at the resting cable, seat error {MAG[T]*1000:5.2f} mm")

# servo there, the way the step loop does: ramp the command, no writes to any pose
# Wait for the arms to SETTLE before closing, the way the driver's own gate does -- the fixed
# ramp left them at 12-20 mrad, ten times SETTLE_TOL, so the first pair I took was measured on
# arms still moving.  The driver does not close the fingers in that state and neither should this.
RAMP = int(4.0 / m.opt.timestep)
settled_at = None
for s_ in range(RAMP + int(20.0 / m.opt.timestep)):
    f = min(1.0, s_ / RAMP)
    for T in ARMS:
        for k, i in enumerate(ns["AIDX"][T]):
            d.ctrl[i] = (1.0 - f) * q_now[T][k] + f * W[T][k]
    mujoco.mj_step(m, d)
    if s_ > RAMP:
        r = max(float(np.abs(np.array([d.qpos[a] for a in ns["QADR"][T2]]) - W[T2]).max())
                for T2 in ARMS)
        if r < ns["SETTLE_TOL"]:
            settled_at = s_
            break
print(f"[pos] settle gate: {'reached ' + format(settled_at * m.opt.timestep, '.2f') + ' s' if settled_at else 'NOT REACHED in 20 s -- numbers below are from moving arms'}"
      f" (tolerance {ns['SETTLE_TOL']*1000:.1f} mrad)")
for T in ARMS:
    resid = float(np.abs(np.array([d.qpos[a] for a in ns["QADR"][T]]) - W[T]).max())
    inb, z = cable_in_mouth(T)
    print(f"[pos] {T}: arrived, residual {resid*1000:6.2f} mrad | backplate {jaw_gaps(T)[0]:6.2f} mm "
          f"| pad-local z {z:7.2f} mm in-band={inb}")

for _ in range(int(ns['FINGER_RAMP'] / m.opt.timestep)):
    for T in ARMS:
        d.ctrl[ns["GIDX"][T]] = ns["CLAMP"]
    mujoco.mj_step(m, d)
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
print(f"\n[pos] CLOSED (floor {_cs.release_floor():5.2f} mm) -- the pair:")
for T in ARMS:
    inb, z = cable_in_mouth(T)
    pad = jaw_gaps(T)[0]
    print(f"[pos] {T}: backplate {pad:6.2f} mm past-floor={pad < _cs.release_floor()} | "
          f"pad-local z {z:7.2f} in band={inb} | R6 held={held(T)} (old grasped={grasped(T)})")
