# %12 independent: phase-gating over ALL firing cells (unbound pure predicate, no GPU build)
import sys, os, glob, json
BASE = "/home/rlrk/IsaacLab/thread_isaac_lab"
for d in ["envs", "scripts", "configs"]:
    sys.path.insert(0, os.path.join(BASE, d))
import numpy as np
import newton_route_env as nre
import route_env_config as rc
D = "/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w0e_81rerun_snapdown_0537"
cells = sorted(c for c in glob.glob(os.path.join(D, "cell_*")) if os.path.exists(os.path.join(c, "route_demo_raw.npz")))
class Shim:
    _seat_metrics = nre.NewtonRouteEnv._seat_metrics
    _c2_seated_honest = nre.NewtonRouteEnv._c2_seated_honest
E = Shim()
firing = []
rows = []
for c in cells:
    d = np.load(os.path.join(c, "route_demo_raw.npz"), allow_pickle=True)
    cable_all = d["cable_xyz"]; phase_all = d["phase_id"]
    if not bool(E._c2_seated_honest(cable_all[-1])):
        continue
    firing.append(os.path.basename(c))
    def at(ph):
        idx = np.where(phase_all == ph)[0]
        return bool(E._c2_seated_honest(cable_all[int(idx[-1])])) if len(idx) else None
    rows.append((os.path.basename(c), at(5), at(13), at(14)))
n = len(rows)
ph5_false = sum(1 for r in rows if r[1] is False)
ph13_true = sum(1 for r in rows if r[2] is True)
ph14_true = sum(1 for r in rows if r[3] is True)
print(f"firing cells (final-frame c2=True) = {n}/81")
print(f"FALSE@ph5(C1_SEAT)   : {ph5_false}/{n}")
print(f"TRUE @ph13(DUAL_SEAT): {ph13_true}/{n}")
print(f"TRUE @ph14(C2_SETTLE): {ph14_true}/{n}")
bad = [r for r in rows if not (r[1] is False and r[3] is True)]
print(f"violations (need FALSE@5 and TRUE@14): {bad}")
