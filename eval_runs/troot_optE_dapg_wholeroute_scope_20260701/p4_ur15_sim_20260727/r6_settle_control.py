"""Why does the aimed pose not settle, when the start pose does?

⛔ First, a retraction of mine.  I reported that "adding an arm kills convergence", comparing a
single-arm run with a two-arm one.  The same artifact refutes it: at STEP1 BOTH arms sit at 0.00
mrad with zero actuator force and nothing saturated.  Two arms settle.  What does not settle is
one particular pose, so the contrast is STEP1 vs [pos] inside one run -- p11's correction, and it
is the same defect I keep finding elsewhere: comparing across setups when the run already held
the control.

The test, to p11's requirements:
  1. FREEZE the joint targets from the failed [pos].  Re-aiming would move two axes at once,
     because a cable somewhere else produces a different aim.
  2. Do not delete the cable -- move it.  Same model, same masses, same contact set, same nq.
  3. Print what STEP1 prints while the settle is being attempted: what the arm touches, the
     actuator forces, and which of them are saturated.  One run, and the breakdown comes with it.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "settlecontrol"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
ARMS, AIDX, QADR, EFFORT = ("L", "R"), ns["AIDX"], ns["QADR"], ns["EFFORT"]
touching, jaw_gaps = ns["touching"], ns["jaw_gaps"]

def instruments(tag):
    for t in ARMS:
        af = np.array([d.actuator_force[i] for i in AIDX[t]])
        qe = (np.array([d.qpos[a] for a in QADR[t]]) - W[t]) * 1000.0
        sat = [bool(x) for x in (np.abs(af) >= np.array(EFFORT) * 0.999)]
        print(f"[ctl] {tag} {t}: joint err max {np.abs(qe).max():7.2f} mrad | touching "
              f"{sorted(touching(t, d)) or 'clear'}")
        print(f"[ctl] {tag} {t}: act force {np.round(af, 1)} N.m | saturated {sat}")

# the aim, taken once and FROZEN
for t in ARMS:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
q_start = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in ARMS}
W = {}
for t in ARMS:
    x_design = (ns["GL"] if t == "L" else ns["GR"])[0]
    c, _ = ns["cable_at"](x_design)
    W[t], _tg, mag = ns["aim_slot_at"](t, c, q_start[t], seed=41 + (t == "R"), fix_x=x_design)
    print(f"[ctl] aim {t}: seat error {mag*1000:5.2f} mm -- FROZEN for both conditions")
span = abs(ns["GL"][0] - ns["GR"][0]) * 1000.0
print(f"[ctl] grasp span in this cell: {span:.1f} mm\n")

def drive(seconds=18.0):
    RAMP = int(4.0 / m.opt.timestep)
    for s_ in range(RAMP + int(seconds / m.opt.timestep)):
        f = min(1.0, s_ / RAMP)
        for t in ARMS:
            for k, i in enumerate(AIDX[t]):
                d.ctrl[i] = (1.0 - f) * q_start[t][k] + f * W[t][k]
        mujoco.mj_step(m, d)

print("=== A: cable where it rests ===")
drive()
instruments("A")

# B: same frozen targets, cable moved -- not deleted
free = m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "cable_free")]
mujoco.mj_resetData(m, d)
for t in ARMS:
    for k, i in enumerate(AIDX[t]):
        d.ctrl[i] = q_start[t][k]
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
d.qpos[free + 1] += 0.60
mujoco.mj_forward(m, d)
for _ in range(int(3.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
print("\n=== B: same frozen targets, cable moved 600 mm in y (same model, same nq) ===")
drive()
instruments("B")
