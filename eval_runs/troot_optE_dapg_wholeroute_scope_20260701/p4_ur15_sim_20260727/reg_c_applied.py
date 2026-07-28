"""② Was the joint limit APPLIED in variant C, or applied and not effective?

p18/pB: the distinction is not in the log -- my probe printed the module attribute, which says
what I set, not what the model got.  So build both ways and count the limited cable joints.
"""
import pathlib, sys, mujoco
S = pathlib.Path("/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727")
sys.path.insert(0, str(S))
for variant, rng in (("A (as it stands)", None), ("C (limit restored)", (-1.2, 1.2))):
    for mod in [m for m in list(sys.modules) if m.startswith("ur15_cell_spec")]:
        del sys.modules[mod]
    import ur15_cell_spec as cs
    cs.CABLE_JOINT_RANGE = rng
    src = (S / "ur15_steps_wired.py").read_text()
    ns = {"__file__": str(S / "ur15_steps_wired.py"), "__name__": f"regc{variant[0]}"}
    exec(compile(src[:src.index("# ---- start pose:")], "ur15_steps_wired.py", "exec"), ns)
    m = ns["m"]
    cab = [i for i in range(m.njnt)
           if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i) or "").startswith("cab")]
    lim = [i for i in cab if m.jnt_limited[i]]
    rngs = {tuple(round(float(x), 3) for x in m.jnt_range[i]) for i in lim} or {"-"}
    print(f"[regc] {variant:22s}: {len(lim)} of {len(cab)} cable joints limited, ranges {rngs}")
