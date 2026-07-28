"""Is the mouth-to-pinch offset a property of the mechanism, or of being blocked?

probe_seat_vs_mouth.py found slot_centre - seat_point = 1.40 mm on L and 14.69 mm on R, with the
jaws open near the cable.  Two readings of that are possible and they point opposite ways:

  (a) structural -- the four-bar swings the two pads asymmetrically as the jaw opens, so the mouth
      leaves the pinch centreline by an amount that grows with opening.  Then the aim, which
      targets the pinch centreline, sends the cable to a point outside the mouth, and the jam is
      downstream of that.
  (b) contact -- the jaw was already touching the cable, one finger was held back, and the offset
      is what being blocked LOOKS like.  Then the offset is downstream of the jam, not upstream.

This separates them: the arms stay at their START pose, where the run's own check prints
"arm touching: clear" for both, so nothing is in the jaws.  Only the finger command moves.  If the
offset appears with opening and nothing touching, it is (a).  If it stays near zero, it is (b) and
the earlier reading was contact.

Measurement only.  No pose is written; the fingers are driven by their velocity servos, which is
the only finger control this project permits.
"""
import pathlib, sys, numpy as np, mujoco

S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs

print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "mouthoffset"}
exec(compile(src[:src.index("for num, name, lt, rt, lf, rf, secs, gate in STEPS:")],
             "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
pinch, slot_centre, jaw_gaps = ns["pinch"], ns["slot_centre"], ns["jaw_gaps"]
CABG, ARMG, CLAWG = ns["CABG"], ns["ARMG"], ns["CLAWG"]

ARMS = ("L", "R")
OPEN, CLAMP = ns["OPEN"], ns["CLAMP"]   # spec §4: 18 is open, 236 is clamped


def touching_cable(t):
    """Any contact between this arm's geoms and the cable, right now."""
    hit = set()
    for i in range(d.ncon):
        g1, g2 = d.contact[i].geom1, d.contact[i].geom2
        if g1 in ARMG[t] and g2 in CABG:
            hit.add(g2)
        elif g2 in ARMG[t] and g1 in CABG:
            hit.add(g1)
    return sorted(hit)


def report(tag):
    for t in ARMS:
        p, sc = pinch(t), slot_centre(t)
        R = np.array(d.xmat[ns["TOOLB"][t]]).reshape(3, 3)
        loc = R.T @ (sc - p) * 1000.0
        pad, claw = jaw_gaps(t)
        q = [float(d.qpos[a]) for a in ns["GQADR"][t]] if "GQADR" in ns else []
        print(f"[off] {tag:>10} {t}: mouth-pinch in tool axes "
              f"({loc[0]:+6.2f},{loc[1]:+6.2f},{loc[2]:+6.2f}) mm  |xy|={float(np.hypot(loc[0], loc[1])):5.2f}"
              f" | pad {pad:+7.2f} claw {claw:+7.2f} mm | touching {touching_cable(t) or 'clear'}"
              + (f" | finger q {np.round(q, 4).tolist()}" if q else ""))


# START pose, jaws closed as the model was built, then let it stand
for _ in range(int(1.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
report("as built")

# open in steps, holding each for long enough that the four-bar stops moving
for frac in (0.25, 0.5, 0.75, 1.0):
    cmd = CLAMP + frac * (OPEN - CLAMP)
    for t in ARMS:
        d.ctrl[ns["GIDX"][t]] = cmd
    for _ in range(int(1.5 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    report(f"open {frac:.2f}")

# and back closed, to see whether the offset follows the opening or sticks
for t in ARMS:
    d.ctrl[ns["GIDX"][t]] = CLAMP
for _ in range(int(2.0 / m.opt.timestep)):
    mujoco.mj_step(m, d)
report("clamped")
