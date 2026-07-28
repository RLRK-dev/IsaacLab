"""What touches the cable during the descent, and when does it start moving?

The run's own numbers say the cable moves 10-13 mm between being aimed at and being closed on.
The single-shot probe moves it 0.00 mm.  The difference is the run's approach: aim high at STEP 2,
descend and re-aim at STEP 3, close at STEP 4.  So replay that, and report the FIRST geom to touch
the cable and the cable's displacement from then on.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "descent"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
ARMS, CAB, CABG = ("L", "R"), ns["CAB"], ns["CABG"]

def cable_xyz():
    return np.array([np.array(d.xpos[b]) for b in CAB])

def cable_contacts():
    out = set()
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        for a, b in ((g1, g2), (g2, g1)):
            if b in CABG and a not in CABG:
                out.add(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, a) or f"g{a}")
    return out

for t in ARMS:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
q0 = {t: np.array([d.qpos[a] for a in ns["QADR"][t]]) for t in ARMS}
cl, _ = ns["cable_at"](ns["GL"][0]); cr, _ = ns["cable_at"](ns["GR"][0])
got = ns["aim_both"](cl, cr, q0, seed=30)
grasp_pose = {t: got[t] for t in ARMS}

# STEP 2: go to the aim point but at the REST height, as the run does
tgt2 = {t: np.array([got[t][1][0], got[t][1][1], ns["Z_RISE_REST"]]) for t in ARMS}
W2 = {}
for t in ARMS:
    W2[t] = ns["solve_ik"](t, tgt2[t], seed=30 + (t == "R"), near=q0[t], warm=q0[t],
                           quiet=True, wide=True, pose_rd=got[t][2])
def move_to(W, seconds, label, ref):
    q_from = {t: np.array([d.qpos[a] for a in ns["QADR"][t]]) for t in ARMS}
    RAMP = int(seconds / m.opt.timestep)
    first = None
    for s_ in range(RAMP + int(1.5 / m.opt.timestep)):
        f = min(1.0, s_ / RAMP)
        for t in ARMS:
            for k, i in enumerate(ns["AIDX"][t]):
                d.ctrl[i] = (1.0 - f) * q_from[t][k] + f * W[t][k]
        mujoco.mj_step(m, d)
        c = cable_contacts()
        if c - {"table_top"} - {f"S{i}_post" for i in (1,2,3)} - {f"S{i}_la" for i in (1,2,3)} - {f"S{i}_lb" for i in (1,2,3)} and first is None:
            first = (s_ * m.opt.timestep, sorted(c))
    moved = np.linalg.norm(cable_xyz() - ref, axis=1).max() * 1000
    print(f"[dsc] {label}: cable max displacement {moved:7.2f} mm | first non-support contact "
          f"{('t=%.2f s %s' % first) if first else 'none'}")
    return cable_xyz()

ref = cable_xyz()
ref = move_to(W2, 2.2, "STEP 2 (up to the rest height)", ref)
# STEP 3: the standoff re-aim, y and z only
W3 = {}
for t in ARMS:
    c, _ = ns["cable_at"]((ns["GL"] if t == "L" else ns["GR"])[0])
    wq, tg, mag = ns["aim_slot_at"](t, c, np.array([d.qpos[a] for a in ns["QADR"][t]]),
                                    seed=40 + (t == "R"), pose_rd=got[t][2],
                                    fix_x=(ns["GL"] if t == "L" else ns["GR"])[0])
    W3[t] = wq
    print(f"[dsc] STEP 3 {t}: standoff re-aim, seat error {mag*1000:5.2f} mm")
ref = move_to(W3, 4.5, "STEP 3 (descend to the standoff)", ref)
print(f"[dsc] contacts on the cable right before the close: {sorted(cable_contacts())}")
