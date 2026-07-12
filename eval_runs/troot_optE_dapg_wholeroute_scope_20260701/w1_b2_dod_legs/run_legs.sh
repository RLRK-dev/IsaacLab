#!/bin/bash
# W1-B2 flag-OFF surface-conformance legs (charter sec4-2 ERRATUM-2) + B2 unit/isolation/calibration legs.
# Sequential cuda:0. Comparators = full-dict-diff minus known-variant keys (B1 carry, %10 finding).
set -u
cd /home/rlrk/IsaacLab
E=eval_runs/troot_optE_dapg_wholeroute_scope_20260701
S=$E/p2_envcore_smoke_20260706_211613
OUT=$E/w1_b2_dod_legs
PY=/home/rlrk/env_isaaclab7/bin/python
FAIL=0

echo "===== LEG 1: 9a-prime rerun (env build + predicate EXACT vs banked) ====="
rm -f "$OUT/dod9a_prime.json"  # R-1: no stale-json false-PASS
CUDA_VISIBLE_DEVICES=0 $PY $S/dod9a_prime.py "$OUT" > "$OUT/leg1_9aprime.log" 2>&1 || FAIL=1
$PY - <<'EOF' || FAIL=1
import json
E = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
new = json.load(open(f"{E}/w1_b2_dod_legs/dod9a_prime.json"))
old = json.load(open(f"{E}/p2_envcore_smoke_20260706_211613/dod9a_prime.json"))
# full-dict-diff minus known-variant keys (timing/throughput; B1 leg2 substring-filter carry).
VAR = tuple(t for t in ("fps", "wall", "time_s", "sec", "duration", "timestamp", "date", "host", "throughput", "sps"))
diffs = {k: (new.get(k), old.get(k)) for k in set(old) | set(new)
         if new.get(k) != old.get(k) and not any(t in k.lower() for t in VAR)}
print(f"[LEG1] 9a' full-dict-diff vs banked (minus variant keys): {'PASS' if not diffs else 'FAIL'} diffs={diffs}")
assert not diffs
EOF

echo "===== LEG 2: DoD5 drift-zero + DoD10 span-proj rerun (c2indep) vs banked ====="
rm -f "$OUT/dod_c2indep.json"
CUDA_VISIBLE_DEVICES=0 $PY $S/dod_c2indep.py "$OUT" > "$OUT/leg2_c2indep.log" 2>&1 || FAIL=1
$PY - <<'EOF' || FAIL=1
import json
E = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
new = json.load(open(f"{E}/w1_b2_dod_legs/dod_c2indep.json"))
old = json.load(open(f"{E}/p2_envcore_smoke_20260706_211613/dod_c2indep.json"))
VAR = tuple(t for t in ("fps", "wall", "time_s", "sec", "duration", "timestamp", "date", "host", "throughput", "sps"))
diffs = {k: (new.get(k), old.get(k)) for k in set(old) | set(new)
         if new.get(k) != old.get(k) and not any(t in k.lower() for t in VAR)}
print(f"[LEG2] DoD5/10 full-dict-diff vs banked (minus variant keys): {'PASS' if not diffs else 'FAIL'} diffs={diffs}")
assert not diffs
EOF

echo "===== LEG 3: DoD6 rerun vs banked ====="
rm -f "$OUT/dod6.json"
CUDA_VISIBLE_DEVICES=0 $PY $S/dod6.py "$OUT" > "$OUT/leg3_dod6.log" 2>&1 || FAIL=1
$PY - <<'EOF' || FAIL=1
import json
E = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
new = json.load(open(f"{E}/w1_b2_dod_legs/dod6.json"))
old = json.load(open(f"{E}/p2_envcore_smoke_20260706_211613/dod6.json"))
same = new == old
if not same:
    dk = [k for k in old if new.get(k) != old.get(k)]
    print(f"[LEG3] differing keys: {dk}")
print(f"[LEG3] DoD6 vs banked: {'PASS (dict-identical)' if same else 'FAIL'}")
assert same
EOF

echo "===== LEG 4: cablediag env-trajectory byte-anchor (gate-6 runner rerun, all trainer flags OFF) ====="
rm -f "$E/comp5_c2seat_fullfire_cablediag.npz"  # R-1: comparator must see THIS run
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl CABLE_XYZ_DIAG=1 $PY $E/comp5_c2seat_fullfire.py > "$OUT/leg4_cablediag.log" 2>&1 || FAIL=1
$PY - <<'EOF' || FAIL=1
import subprocess

import numpy as np

E = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
new = np.load(f"{E}/comp5_c2seat_fullfire_cablediag.npz")
r = subprocess.run(["git", "show", "311f18cb9b:" + f"{E}/comp5_c2seat_fullfire_cablediag.npz"], capture_output=True)
open("/tmp/claude-1000/banked_cablediag_b2.npz", "wb").write(r.stdout)
old = np.load("/tmp/claude-1000/banked_cablediag_b2.npz")
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

echo "===== LEG 6: CPU unit suites (stdout pinned at run time, %12 minor-1 carry) ====="
$PY thread_isaac_lab/scripts/test_routeexec_step_target.py > "$OUT/unit_step_target.log" 2>&1 || FAIL=1
$PY thread_isaac_lab/scripts/test_routeexec_writesite.py > "$OUT/unit_writesite.log" 2>&1 || FAIL=1
$PY thread_isaac_lab/scripts/test_routeexec_state_bank.py > "$OUT/unit_state_bank.log" 2>&1 || FAIL=1
tail -n 2 "$OUT/unit_step_target.log" "$OUT/unit_writesite.log" "$OUT/unit_state_bank.log"

echo "===== LEG 7: HOLD reset isolation (env done-reset path, 2-world) ====="
rm -f "$OUT/leg7_hold_reset_isolation.json"
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl $PY $OUT/leg7_hold_reset_isolation.py > "$OUT/leg7.log" 2>&1 || FAIL=1
tail -n 2 "$OUT/leg7.log"

echo "===== LEG 8: HOLD calibration (quiet + fires; flag ON, 499 steps) ====="
rm -f "$OUT/leg8_hold_calibration.json"
CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl $PY $OUT/leg8_hold_calibration.py > "$OUT/leg8.log" 2>&1 || FAIL=1
tail -n 3 "$OUT/leg8.log"

echo "===== SUMMARY ====="
echo "W1_B2_LEGS_FAIL=$FAIL"
exit $FAIL
