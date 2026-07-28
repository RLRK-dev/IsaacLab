"""How long does the jaw-close PREDICTION actually need?

The attitude search runs a scratch settle per candidate -- 65 attitudes x 2 arms -- and each one
now costs 5 s of simulated time, which at the producer's timestep is 24000 steps.  That is where
the twenty-five minute startup goes.

⛔ Not a design question: the 5 s is what the RUN waits, and that stays.  This asks a measurement
question instead -- has the prediction already converged well before 5 s?  If the seat it predicts
stops moving at, say, 1.5 s, then settling for 5 s is buying nothing, and the search can use the
shorter one without any number changing.
"""
import pathlib, sys, numpy as np, mujoco
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
import ur15_cell_spec as _cs
print(f"[stack] {_cs.stack_line()}")
src = (S / "ur15_steps_wired.py").read_text()
ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": "predsettle"}
exec(compile(src[:src.index("# ---- start pose:")], "ur15_steps_wired.py", "exec"), ns)
m, d = ns["m"], ns["d"]
CLAMP, PAD, AIDX, GIDX = ns["CLAMP"], ns["PAD"], ns["AIDX"], ns["GIDX"]

def predict(t, qarm, seconds):
    """slot_after_close's body, with the settle length as a parameter."""
    sc = mujoco.MjData(m)
    sc.qpos[:] = d.qpos
    sc.ctrl[:] = d.ctrl
    for k, i in enumerate(AIDX[t]):
        sc.qpos[ns["QADR"][t][k]] = qarm[k]
        sc.ctrl[i] = qarm[k]
    sc.ctrl[GIDX[t]] = CLAMP
    for _ in range(int(seconds / m.opt.timestep)):
        mujoco.mj_step(m, sc)
    return ns["slot_centre"](t, sc)

print(f"\n{'settle s':>9} {'steps':>7}   " + "   ".join(f"{t} seat (mm from the 5 s answer)" for t in ("L", "R")))
ref = {}
for t in ("L", "R"):
    ref[t] = predict(t, np.array([d.qpos[a] for a in ns["QADR"][t]]), 5.0)
for sec in (0.5, 1.0, 1.5, 2.0, 3.0, 5.0):
    row = []
    for t in ("L", "R"):
        p = predict(t, np.array([d.qpos[a] for a in ns["QADR"][t]]), sec)
        row.append(f"{np.linalg.norm(p - ref[t])*1000:31.4f}")
    print(f"{sec:9.1f} {int(sec/m.opt.timestep):7d}   " + "   ".join(row))
print("\nif a shorter settle reproduces the 5 s answer to well under the 1 micron level, the search")
print("is paying for time that changes nothing -- and the loop gets that time back.")
