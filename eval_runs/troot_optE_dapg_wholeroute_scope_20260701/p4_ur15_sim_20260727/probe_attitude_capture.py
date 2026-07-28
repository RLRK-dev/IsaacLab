"""Which grasp attitudes actually CAPTURE the cable -- not which ones land the seat well?

The right hand jams every run at a pad gap of 16.2 mm, which is two cable diameters: the cable is
sitting between the claw TIPS instead of down at the pads.  Its attitude is rolled 32 degrees; the
left hand, which clamps, is rolled 17.

Reading the selection code, the attitude is chosen by ONE number -- how close the seat lands to
where it was wanted (`land = slot_after_close(...) - want`).  Nothing in that asks whether the
CABLE ends up in the seat.  A pose can put the seat exactly where it belongs and still present the
mouth at an angle the cable cannot enter.

So: sweep the menu, close for real, and report capture.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "attcap"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
T = "R"
x_design = ns["GR"][0]
for t in ns["SIDES"]:
    d.ctrl[ns["GIDX"][t]] = ns["OPEN"]
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
q0 = np.array([d.qpos[a] for a in ns["QADR"][T]])
qpos0, qvel0, ctrl0 = d.qpos.copy(), d.qvel.copy(), d.ctrl.copy()
c, _ = ns["cable_at"](x_design)

print(f"\n{'yaw':>6} {'roll deg':>9} {'seat err':>9} {'pad faces':>10} {'centre off':>11} "
      f"{'pads on cable':>14} {'R6 held':>8}")
rows = []
for (yaw, roll) in [(0.0, r) for r in (0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.55, 0.65, 0.75)]:
    try:
        w, tg, mag = ns["aim_slot_at"](T, c, q0, seed=41, pose_rd=(yaw, roll), fix_x=x_design)
    except RuntimeError:
        print(f"{yaw:6.2f} {np.degrees(roll):9.1f}   no IK solution")
        continue
    # restore the VELOCITIES too: without them the cable kept the motion the previous
    # attitude's clamp gave it, and by the third row it had been dragged 800 mm away --
    # every row after the first was measuring a different cable.
    d.qpos[:], d.qvel[:], d.ctrl[:] = qpos0, qvel0, ctrl0
    mujoco.mj_forward(m, d)
    RAMP = int(4.0 / m.opt.timestep)
    for s_ in range(RAMP + int(2.0 / m.opt.timestep)):
        f = min(1.0, s_ / RAMP)
        for k, i in enumerate(ns["AIDX"][T]):
            d.ctrl[i] = (1.0 - f) * q0[k] + f * w[k]
        mujoco.mj_step(m, d)
    for _ in range(int(ns["FINGER_RAMP"] / m.opt.timestep)):
        d.ctrl[ns["GIDX"][T]] = ns["CLAMP"]
        mujoco.mj_step(m, d)
    for _ in range(int(2.0 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    pad = ns["jaw_gaps"](T)[0]
    off = ns["cable_perp"](ns["seat_point"](T))[0] * 1000
    pf, _lf, _cf = ns["clamp_faces"](T)
    held = ns["held"](T)
    print(f"{yaw:6.2f} {np.degrees(roll):9.1f} {mag*1000:9.2f} {pad:10.2f} {off:11.2f} "
          f"{str(sorted(pf) or 'none'):>14} {str(held):>8}")
    rows.append((roll, mag, pad, held))
ok = [r for r in rows if r[3]]
print(f"\ncaptured at {len(ok)} of {len(rows)} attitudes: "
      f"{[f'{np.degrees(r[0]):.0f} deg' for r in ok] or 'none'}")
