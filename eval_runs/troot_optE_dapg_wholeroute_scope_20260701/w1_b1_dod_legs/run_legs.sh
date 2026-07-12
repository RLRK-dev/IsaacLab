#!/bin/bash
# W1-B1 env-side flag-OFF DoD legs (conformance v2.1 R17 / spec sec8 "clock 付替え後" set). Sequential cuda:0.
set -u
cd /home/rlrk/IsaacLab
E=eval_runs/troot_optE_dapg_wholeroute_scope_20260701
S=$E/p2_envcore_smoke_20260706_211613
OUT=$E/w1_b1_dod_legs
PY=/home/rlrk/env_isaaclab7/bin/python
FAIL=0

echo "===== LEG 1: 9a-prime rerun (env build + predicate EXACT vs banked) ====="
CUDA_VISIBLE_DEVICES=0 $PY $S/dod9a_prime.py "$OUT" > "$OUT/leg1_9aprime.log" 2>&1
$PY - <<'EOF' || FAIL=1
import json
new = json.load(open("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b1_dod_legs/dod9a_prime.json"))
old = json.load(open("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p2_envcore_smoke_20260706_211613/dod9a_prime.json"))
same = all(new[k] == old[k] for k in ("env_predicate_both_count", "offline_prediction_both_count",
                                      "per_cell_EXACT_match", "per_cell_EXACT_pass", "mismatches"))
print(f"[LEG1] 9a' EXACT vs banked: {'PASS' if same else 'FAIL'} "
      f"(new both={new['env_predicate_both_count']}/81, banked={old['env_predicate_both_count']}/81)")
assert same
EOF

echo "===== LEG 2: DoD5 drift-zero + DoD10 span-proj rerun (c2indep) vs banked ====="
CUDA_VISIBLE_DEVICES=0 $PY $S/dod_c2indep.py "$OUT" > "$OUT/leg2_c2indep.log" 2>&1
$PY - <<'EOF' || FAIL=1
import json
new = json.load(open("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b1_dod_legs/dod_c2indep.json"))
old = json.load(open("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p2_envcore_smoke_20260706_211613/dod_c2indep.json"))
keys = [k for k in old if any(t in k.lower() for t in ("drift", "span", "finite", "explosion"))]
diffs = {k: (new.get(k), old[k]) for k in keys if new.get(k) != old[k]}
print(f"[LEG2] DoD5/10 keys compared={keys}")
print(f"[LEG2] {'PASS' if not diffs else 'FAIL'} diffs={diffs}")
assert not diffs
EOF

echo "===== LEG 3: DoD6 rerun vs banked ====="
CUDA_VISIBLE_DEVICES=0 $PY $S/dod6.py "$OUT" > "$OUT/leg3_dod6.log" 2>&1
$PY - <<'EOF' || FAIL=1
import json
new = json.load(open("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/w1_b1_dod_legs/dod6.json"))
old = json.load(open("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p2_envcore_smoke_20260706_211613/dod6.json"))
same = new == old
if not same:
    dk = [k for k in old if new.get(k) != old.get(k)]
    print(f"[LEG3] differing keys: {dk}")
print(f"[LEG3] DoD6 vs banked: {'PASS (dict-identical)' if same else 'FAIL'}")
assert same
EOF

echo "===== LEG 4: cablediag env-trajectory byte-anchor (gate-6 runner rerun, all trainer flags OFF) ====="
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl CABLE_XYZ_DIAG=1 $PY $E/comp5_c2seat_fullfire.py > "$OUT/leg4_cablediag.log" 2>&1
$PY - <<'EOF' || FAIL=1
import json
import numpy as np
E = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
new = np.load(f"{E}/comp5_c2seat_fullfire_cablediag.npz")
import subprocess
r = subprocess.run(["git", "show", "311f18cb9b:" + f"{E}/comp5_c2seat_fullfire_cablediag.npz"], capture_output=True)
open("/tmp/claude-1000/banked_cablediag.npz", "wb").write(r.stdout)
old = np.load("/tmp/claude-1000/banked_cablediag.npz")
same = set(new.files) == set(old.files) and all(np.array_equal(new[k], old[k]) for k in old.files)
bad = [k for k in old.files if not np.array_equal(new[k], old[k])] if not same else []
print(f"[LEG4] cablediag npz EXACT vs banked 311f18cb9b: {'PASS' if same else 'FAIL'} bad_keys={bad}")
assert same
EOF

echo "===== LEG 5: producer 5-cell byte-repro vs pinned baseline (route_executor.py diff leg) ====="
CUDA_VISIBLE_DEVICES=0 $PY thread_isaac_lab/scripts/test_routeexec_byte_repro.py \
  --cells x0_y0,x-20_y-20,x-20_y20,x20_y-20,x20_y20 --nproc 4 \
  --out-root "$OUT/byte_repro_5cell" > "$OUT/leg5_byterepro.log" 2>&1
grep -E "npz sha256 EXACT" "$OUT/leg5_byterepro.log"
grep -qE "npz sha256 EXACT \(byte-id\) : 5/5" "$OUT/leg5_byterepro.log" || FAIL=1

echo "===== SUMMARY ====="
echo "W1_B1_LEGS_FAIL=$FAIL"
exit $FAIL
