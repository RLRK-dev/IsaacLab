#!/bin/bash
# W1-B3a DoD legs. LEG2 (capture) is the only GPU leg; the rest are CPU/offline.
# The capture rides the byte-repro driver: its sha comparison vs the golden IS the read-only proof
# (a capture that perturbed the producer would change route_demo_raw.npz and break byte-identity).
#
# leg3 v2 (2026-07-14): the v1 central-FD bar was structurally unfit -- blind to the "wrong substep" hazard
# the spec names, blind to scale, and out of band wherever the cable slews fast. Replaced by the substep-index
# readout + identifiability table (see leg3_qd_substep_readout.py).
# leg6 (2026-07-14, %12 mandated): hidden-state LIVENESS. The first capture read the never-stepped mjw_data
# mirror; every other leg passed anyway. This leg checks the captured eq_active against the recording's
# independent pin witness, so a dead mirror cannot pass.
set -u
cd /home/rlrk/IsaacLab
E=eval_runs/troot_optE_dapg_wholeroute_scope_20260701
OUT=$E/w1_b3a_dod_legs
PY=/home/rlrk/env_isaaclab7/bin/python
FAIL=0

echo "===== LEG 1: Rs-LOCK assert (run_route byte-identical vs HEAD) ====="
$PY "$OUT/leg1_lock_assert.py" || FAIL=1

echo "===== LEG 2: producer capture (BANK_CAPTURE=1 + DEMO_RECORD=1, x0_y0, cuda:0) ====="
rm -f "$OUT/bank_capture.npz"
BANK_CAPTURE=1 BANK_OUT="$OUT/bank_capture.npz" CUDA_VISIBLE_DEVICES=0 MUJOCO_GL=egl \
  $PY thread_isaac_lab/scripts/test_routeexec_byte_repro.py \
  --cells x0_y0 --nproc 1 --out-root "$OUT/capture_run" > "$OUT/leg2_capture.log" 2>&1
grep -E "npz sha256 EXACT|BANK-CAPTURE" "$OUT/leg2_capture.log" | head -5
# read-only proof: the capture run's OWN recording must still be byte-identical to the golden
grep -qE "npz sha256 EXACT \(byte-id\) : 1/1" "$OUT/leg2_capture.log" || FAIL=1
[ -f "$OUT/bank_capture.npz" ] || { echo "[LEG2] capture npz MISSING"; FAIL=1; }

echo "===== LEG 3: qd substep-index readout + identifiability table ====="
$PY "$OUT/leg3_qd_substep_readout.py" "$OUT/bank_capture.npz" || FAIL=1

echo "===== LEG 6: hidden-state liveness (eq_active vs the recording's pin witness; warmstart mechanism) ====="
$PY "$OUT/leg6_hidden_state_liveness.py" "$OUT/bank_capture.npz" || FAIL=1

echo "===== LEG 4: CPU units (bank v2 builder + guards + null control) ====="
$PY thread_isaac_lab/scripts/test_routeexec_state_bank.py > "$OUT/unit_state_bank_stdout.txt" 2>&1 || FAIL=1
tail -n 4 "$OUT/unit_state_bank_stdout.txt"

echo "===== LEG 5: producer 5-cell byte-repro (route_executor.py diff, surface conformance) ====="
CUDA_VISIBLE_DEVICES=0 $PY thread_isaac_lab/scripts/test_routeexec_byte_repro.py \
  --cells x0_y0,x-20_y-20,x-20_y20,x20_y-20,x20_y20 --nproc 4 \
  --out-root "$OUT/byte_repro_5cell" > "$OUT/leg5_byterepro.log" 2>&1
grep -E "npz sha256 EXACT" "$OUT/leg5_byterepro.log"
grep -qE "npz sha256 EXACT \(byte-id\) : 5/5" "$OUT/leg5_byterepro.log" || FAIL=1

echo "===== SUMMARY ====="
echo "W1_B3A_LEGS_FAIL=$FAIL"
exit $FAIL
