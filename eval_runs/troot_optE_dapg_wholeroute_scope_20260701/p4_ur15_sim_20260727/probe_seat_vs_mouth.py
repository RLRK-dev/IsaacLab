"""Where the aim sends the cable, versus where the mouth actually is -- per arm.

The aim targets seat_point(), whose x and y come from the PINCH, because the pinch is on the
jaw centreline by construction.  The place the cable has to reach to be inside the ko is
slot_centre(), the midpoint of the two claws.  seat_point's own docstring says those two differ
by up to 21 mm, because the four-bar does not swing the two pads symmetrically -- it takes only
z from the claws for exactly that reason.

So the residual is whatever slot_centre - seat_point comes to in x and y at the pose each arm
actually holds.  That is what this measures.  It matters because the two arms do not hold the
same attitude: the run's aim gives L a +17 deg tilt and R a +32 deg tilt, and a four-bar
asymmetry that depends on tilt will not be equal between them.

Measurement only.  Nothing is written into a pose; the arms reach the aim through their servos,
and the cable is left where it rests.  Reuses r6_positive.py's scaffolding, so this is a
driver-side selection path (aim_slot_at) -- NOT the route loop's selector, which passes other=.
"""
import pathlib, sys, numpy as np, mujoco

S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs

print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "seatvsmouth"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
pinch, seat_point, slot_centre = ns["pinch"], ns["seat_point"], ns["slot_centre"]
cable_at, cable_perp = ns["cable_at"], ns["cable_perp"]

ARMS = ("L", "R")
for t in ns["SIDES"]:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)

q_now = {t: np.array([d.qpos[a] for a in ns["QADR"][t]]) for t in ns["SIDES"]}
W, MAG = {}, {}
for T in ARMS:
    x_design = (ns["GL"] if T == "L" else ns["GR"])[0]
    c, _ = cable_at(x_design)
    W[T], _tg, MAG[T] = ns["aim_slot_at"](T, c, q_now[T], seed=41 + (T == "R"), fix_x=x_design)
    print(f"[svm] {T}: aim seat error {MAG[T]*1000:5.2f} mm")

RAMP = int(4.0 / m.opt.timestep)
for s_ in range(RAMP + int(8.0 / m.opt.timestep)):
    f = min(1.0, s_ / RAMP)
    for T in ARMS:
        for k, i in enumerate(ns["AIDX"][T]):
            d.ctrl[i] = (1.0 - f) * q_now[T][k] + f * W[T][k]
    mujoco.mj_step(m, d)

print()
for T in ARMS:
    p = pinch(T)
    sp = seat_point(T)
    sc = slot_centre(T)
    res = (sc - sp) * 1000.0
    resid = max(abs(float(np.array([d.qpos[a] for a in ns["QADR"][T]])[k] - W[T][k]))
                for k in range(len(W[T]))) * 1000.0
    print(f"[svm] {T}: servo residual {resid:6.2f} mrad")
    print(f"[svm] {T}: pinch      [{p[0]:+.4f} {p[1]:+.4f} {p[2]:+.4f}]")
    print(f"[svm] {T}: seat_point [{sp[0]:+.4f} {sp[1]:+.4f} {sp[2]:+.4f}]  <- what the aim targets")
    print(f"[svm] {T}: slot_centre[{sc[0]:+.4f} {sc[1]:+.4f} {sc[2]:+.4f}]  <- where the ko mouth is")
    print(f"[svm] {T}: slot_centre - seat_point = ({res[0]:+6.2f},{res[1]:+6.2f},{res[2]:+6.2f}) mm"
          f"   |xy| = {float(np.hypot(res[0], res[1])):5.2f} mm")
    # and what that means for the cable: distance from each of the two points to the centreline
    for nm, q in (("seat_point", sp), ("slot_centre", sc)):
        dist, _pt, _k, _u = cable_perp(q)
        print(f"[svm] {T}:   cable is {dist*1000:6.2f} mm from {nm}")
    # the mouth's own axes, so the residual can be read as along/closing/across
    R = np.array(d.xmat[ns["TOOLB"][T]]).reshape(3, 3)
    loc = R.T @ (sc - sp) * 1000.0
    print(f"[svm] {T}:   in the tool's axes that residual is "
          f"({loc[0]:+6.2f},{loc[1]:+6.2f},{loc[2]:+6.2f}) mm")
    print()
