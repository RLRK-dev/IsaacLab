"""Which of today's cable changes stops the right jaw from closing?

The regression, from the two logs: at the first grasp the judged run had both jaws at ~22 mm pad
separation with the flat pads on the cable; this run has the right jaw stuck at 30.4 mm with only
the claws touching.  In the same log the cable moves 10-13 mm between being aimed at and being
closed on -- so the question is what makes it move that much.

Three things about the cable changed today, and this changes ONE at a time:
  A  as it stands now              (mass 1.1243 g/link, no joint limit)
  B  the old mass                  (4.0 g/link, everything else as now)
  C  the old joint limit restored  (+-1.2 rad, everything else as now)

⛔ B and C are not proposals -- reverting either would put back a value the SSOT contradicts.  They
are here to say which change the symptom follows.
"""
import os, pathlib, sys, numpy as np, mujoco
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
VARIANT = sys.argv[1]
if VARIANT == "B":
    _cs.cable_seg_mass = lambda: 0.004
elif VARIANT == "C":
    _cs.CABLE_JOINT_RANGE = (-1.2, 1.2)
print(f"[reg] variant {VARIANT}: mass {_cs.cable_seg_mass()*1000:.4f} g/link, "
      f"joint range {_cs.CABLE_JOINT_RANGE}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": f"reg{VARIANT}"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
ARMS = ("L", "R")
for t in ARMS:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
q0 = {t: np.array([d.qpos[a] for a in ns["QADR"][t]]) for t in ARMS}
cl, _ = ns["cable_at"](ns["GL"][0])
cr, _ = ns["cable_at"](ns["GR"][0])
aimed_at = {"L": np.array(cl, float), "R": np.array(cr, float)}
got = ns["aim_both"](cl, cr, q0, seed=30)
W = {t: got[t][0] for t in ARMS}
RAMP = int(4.0 / m.opt.timestep)
for s_ in range(RAMP + int(3.0 / m.opt.timestep)):
    f = min(1.0, s_ / RAMP)
    for t in ARMS:
        for k, i in enumerate(ns["AIDX"][t]):
            d.ctrl[i] = (1.0 - f) * q0[t][k] + f * W[t][k]
    mujoco.mj_step(m, d)
moved = {}
for t in ARMS:
    c_now, _ = ns["cable_at"]((ns["GL"] if t == "L" else ns["GR"])[0])
    moved[t] = np.linalg.norm(np.array(c_now, float) - aimed_at[t]) * 1000.0
for _ in range(int(ns["FINGER_RAMP"] / m.opt.timestep)):
    for t in ARMS:
        d.ctrl[ns["GIDX"][t]] = ns["CLAMP"]
    mujoco.mj_step(m, d)
for _ in range(int(2.5 / m.opt.timestep)):
    mujoco.mj_step(m, d)
print(f"\n[reg] {VARIANT}  {'arm':>4} {'cable moved':>12} {'pad faces':>10} {'pad sep':>9} "
      f"{'pads on cable':>14} {'clamped':>8}")
for t in ARMS:
    pad = ns["jaw_gaps"](t)[0]
    sep = float(np.linalg.norm(np.array(d.xpos[ns["PAD"][t][0]]) - np.array(d.xpos[ns["PAD"][t][1]]))) * 1000
    pf, lf, cf = ns["clamp_faces"](t)
    print(f"[reg] {VARIANT}  {t:>4} {moved[t]:11.2f}m {pad:10.2f} {sep:9.2f} {str(sorted(pf) or 'none'):>14} "
          f"{str(ns['grasped'](t)):>8}")
