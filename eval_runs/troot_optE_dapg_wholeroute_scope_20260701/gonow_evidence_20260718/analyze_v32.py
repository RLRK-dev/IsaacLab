# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Mechanical P / three-state analysis of the #18 grip evidence run.

Prereg: IKCHORD_GRIPSLIP_GONOW_MEASURE_PREREG_RSTECHLEAD_20260718.md (v3.1 B1/B2/B3 + v3.2 C1/C2).
v3 (OPS-SUP verdict 2026-07-18 18:27, records-fix, no sim rerun):
- B1: P-of-record uses the LITERAL prereg conjunct `config-diff-set == {route_c1_pin_effective,
  pin_seat_seg}` -> P=FALSE. The observed route-only single-variable diff is recorded as a SEPARATE
  post-run characterization (a narrower isolation), NOT a P relaxation.
- B2: required integrity (status/source_integrity_ok/device_provenance_ok/closure-sets) + M2-vs-M2b
  device/episode/drive equality + per_step exact-sequence & uniqueness are FAIL-LOUD asserts
  (nonzero exit + printed reason on any violation; the verdict is emitted only if all pass).
The three-state verdict is INCONCLUSIVE and is independent of P. Read-only over the banked
summaries/per_step; no sim.
"""

import json
import sys
from pathlib import Path

P_DIR = Path("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/gonow_evidence_20260718")
LEAF = {
    "M1": ("m1_b4shadow_ikchord", "m1_b4shadow"),
    "M2": ("m2_ff_pin_shadow", "m2_ff_pin"),
    "M2b": ("m2b_ff_shadow_nopin", "m2b_ff_nopin"),
    "M3": ("m3_ikchord_natterm", "m3_ikchord_natterm"),
}
CAUSES = ["A_held_z_floor", "B_contact_loss", "C_c1_escape", "explosion"]
WINDOW_HI = 347  # frozen post-diagnostic anchor (M2 drop)
EXPECTED = {"route_c1_pin_effective", "pin_seat_seg"}  # prereg :141 registered config-diff-set
INTEGRITY = ["changed_source_set", "missing_source_set", "added_during_drive", "build_added_unstable"]
DEV_KEYS = ["current_device", "uuid", "device_name", "device_count"]
CMP = [
    "contact_r",
    "contact_l",
    "held_z_minus_rest",
    "dx_c1",
    "g_latched",
    "held_i",
    "grasped",
    "contact_loss_count",
]


def load(leg):
    leaf, tag = LEAF[leg]
    s = json.loads((P_DIR / leaf / f"summary_{tag}.json").read_text())
    ps = json.loads((P_DIR / leaf / f"per_step_{tag}.json").read_text())
    return s, ps


S, PS = {}, {}
for leg in LEAF:
    S[leg], PS[leg] = load(leg)


def term_cause_set(s):
    """{k | first_cause_step[k] == done_step}; empty if done_step is None (v3.2 C2)."""
    ds = s["done_step"]
    if ds is None:
        return set(), None
    fcs = s["first_cause_step"]
    return {k for k in CAUSES if fcs.get(k) == ds}, ds


print("=" * 72)
print("PER-LEG SUMMARY")
print("=" * 72)
for leg in ["M1", "M2", "M2b", "M3"]:
    s = S[leg]
    prov = s["provenance"]
    eff = s["effective_config"]
    sh = s.get("shadow")
    tcs, _ = term_cause_set(s)
    print(f"\n[{leg}] {LEAF[leg][0]}")
    print(
        f"  status={s['status']}  source_integrity_ok={prov.get('source_integrity_ok')}  "
        f"device_provenance_ok={prov.get('device_provenance_ok')}"
    )
    print(
        f"  drive={eff.get('drive_mode')}  route_c1_pin_effective={eff.get('route_c1_pin_effective')}  "
        f"pin_seat_seg={eff.get('pin_seat_seg')}"
    )
    print(
        f"  RL_SIM_SUBSTEPS={eff.get('RL_SIM_SUBSTEPS')}  PHYSICS_STEPS_PER_RL={eff.get('PHYSICS_STEPS_PER_RL')}  "
        f"ep_req={s.get('episode_steps_requested')}"
    )
    print(f"  g3_reached={s['g3_reached']}  g3_step={s['g3_step']}")
    print(f"  first_cause_step={s['first_cause_step']}")
    print(f"  done_step={s['done_step']}  done_reward={s['done_reward']}  term_cause_set={sorted(tcs)}")
    if sh:
        print(
            f"  shadow.first_shadow_fire_step={sh['first_shadow_fire_step']}  max_dwell={sh.get('max_dwell')}  "
            f"shadow_fire_before_drop={sh.get('shadow_fire_before_drop')}"
        )
    else:
        print("  shadow=None")

# ---- B1: f anchor ----
f = S["M2"]["shadow"]["first_shadow_fire_step"]
print("\n" + "=" * 72)
print("B1 CAUSAL BOUNDARY: f := M2 shadow.first_shadow_fire_step")
print("=" * 72)
print(f"f = {f}   (frozen expectation f==246 -> {'PASS' if f == 246 else 'FAIL=>INCONCLUSIVE'})")


def rows_by_step(ps):
    return {r["step"]: r for r in ps}


r2, r2b = rows_by_step(PS["M2"]), rows_by_step(PS["M2b"])
need = set(range(0, f)) if isinstance(f, int) else set()
miss2, miss2b = sorted(need - set(r2)), sorted(need - set(r2b))
rows_ok = (not miss2) and (not miss2b)
first_div, ndiff = None, 0
if rows_ok:
    for st in range(0, f):
        a, b = r2[st], r2b[st]
        d = [c for c in CMP if a.get(c) != b.get(c)]
        if d:
            ndiff += 1
            if first_div is None:
                first_div = (st, {c: (a.get(c), b.get(c)) for c in d})
trace_equal = rows_ok and ndiff == 0
print("\n" + "=" * 72)
print("B1 PRE-FIRE TRACE EQUALITY  (M2 vs M2b, per_step step in [0, f-1])")
print("=" * 72)
print(f"  rows [0,{f - 1}] present: M2 missing={miss2}  M2b missing={miss2b}  -> rows_ok={rows_ok}")
print(f"  compared fields={CMP}")
print(f"  #divergent steps={ndiff}  first_divergence={first_div}  -> pre_fire_trace_equal={trace_equal}")

# ---- config-diff-set (M2 vs M2b): literal == conjunct + separate characterization ----
eff2, eff2b = S["M2"]["effective_config"], S["M2b"]["effective_config"]
cfg_diff = {k for k in sorted(set(eff2) | set(eff2b)) if eff2.get(k) != eff2b.get(k)}
cfg_conjunct = cfg_diff == EXPECTED  # prereg :98/:141 LITERAL conjunct
print("\n" + "=" * 72)
print("CONFIG DIFF-SET (M2 vs M2b)")
print("=" * 72)
print(
    f"  actual diff_set={sorted(cfg_diff)}  (pin_seat_seg={eff2.get('pin_seat_seg')} both; "
    f"equal={eff2.get('pin_seat_seg') == eff2b.get('pin_seat_seg')})"
)
print(f"  prereg P conjunct [== {sorted(EXPECTED)}] = {cfg_conjunct}   (P-of-record uses THIS literal conjunct)")

# ---- run-independent equality (M2 vs M2b): full registered set ----
p2, p2b = S["M2"]["provenance"], S["M2b"]["provenance"]
prov_keys = [
    "harness_self_sha256_post",
    "recording_sha256",
    "venv_python",
    "source_closure_run_end",
    "changed_source_set",
    "missing_source_set",
    "added_during_drive",
    "build_added_unstable",
    "requested_device",
    "env_device",
    "cvd",
    "MUJOCO_GL",
]
prov_eq = {k: (p2.get(k) == p2b.get(k)) for k in prov_keys}
tc2, tc2b = p2.get("torch_cuda", {}), p2b.get("torch_cuda", {})
dev_eq = all(tc2.get(k) == tc2b.get(k) for k in DEV_KEYS)
epi_eq = S["M2"].get("episode_steps_requested") == S["M2b"].get("episode_steps_requested")
drive_eq = eff2.get("drive_mode") == eff2b.get("drive_mode")
run_indep_eq = all(prov_eq.values()) and dev_eq and epi_eq and drive_eq
print("\n" + "=" * 72)
print("RUN-INDEPENDENT EQUALITY (M2 vs M2b) — full registered set")
print("=" * 72)
for k in prov_keys:
    print(f"  {k}: equal={prov_eq[k]}")
print(f"  torch_cuda({'/'.join(DEV_KEYS)}): equal={dev_eq}  (uuid={tc2.get('uuid')})")
print(f"  episode_steps_requested: equal={epi_eq}   drive_mode: equal={drive_eq}   -> run_indep_eq={run_indep_eq}")

# ---- B2: FAIL-LOUD invariant asserts (nonzero exit on any violation) ----
FAIL = []


def require(cond, msg):
    if not cond:
        FAIL.append(msg)


for leg in ["M1", "M2", "M2b", "M3"]:
    s = S[leg]
    pr = s["provenance"]
    require(s["status"] == "COMPLETE", f"{leg}: status != COMPLETE ({s['status']})")
    require(pr.get("source_integrity_ok") is True, f"{leg}: source_integrity_ok != True")
    require(pr.get("device_provenance_ok") is True, f"{leg}: device_provenance_ok != True")
    for k in INTEGRITY:
        require(not pr.get(k), f"{leg}: {k} nonempty ({pr.get(k)})")
    steps = [r["step"] for r in PS[leg]]
    ds = s["done_step"]
    require(len(steps) == len(set(steps)), f"{leg}: per_step has duplicate step indices")
    if ds is not None:
        require(steps == list(range(ds + 1)), f"{leg}: per_step not contiguous 0..done_step={ds}")
require(run_indep_eq, "M2 vs M2b run-independent equality failed (see section above)")
require(f == 246, f"f != 246 ({f})")
require(rows_ok, "M2/M2b missing pre-fire rows [0,f-1]")
require(trace_equal, "pre-fire trace [0,f-1] not bitwise-equal")

print("\n" + "=" * 72)
print("B2 FAIL-LOUD INVARIANTS (integrity / device-episode equality / per_step sequence+uniqueness / anchors)")
print("=" * 72)
if FAIL:
    print("!" * 72)
    print("FAIL-LOUD VIOLATION — analysis ABORTED, verdict NOT emitted:")
    for m in FAIL:
        print("  FAIL:", m)
    print("!" * 72)
    sys.exit(1)
print("  ALL required invariants PASS (4 legs COMPLETE+integrity+device_provenance, closure-sets=[],")
print("  per_step contiguous 0..done & unique, M2/M2b run-independent-equal, f==246, pre-fire bitwise-equal).")

# ---- P (of record) + separate post-run characterization (B1) ----
base_invariants = True  # guaranteed by the fail-loud asserts above (else we exited)
P_of_record = base_invariants and cfg_conjunct  # literal prereg conjunct -> FALSE here
route_only_narrower = cfg_diff < EXPECTED  # proper subset = a tighter one-variable isolation
print("\n" + "=" * 72)
print("P (common validity predicate) — prereg :98/:141 literal")
print("=" * 72)
print(f"  base invariants (asserted above) = {base_invariants}")
print(f"  config-diff conjunct [== {sorted(EXPECTED)}] = {cfg_conjunct}")
print(f"  >>> P (of record) = {P_of_record}   (FALSE: actual diff {sorted(cfg_diff)} != registered {sorted(EXPECTED)})")
print("\n  POST-RUN CHARACTERIZATION (separate axis; NOT a P relaxation):")
print(f"    actual M2-vs-M2b effective-config diff = {sorted(cfg_diff)} (single variable),")
print(
    f"    a proper subset of the registered {sorted(EXPECTED)} -> "
    f"narrower one-variable isolation = {route_only_narrower}"
)
print("    (pin_seat_seg=27 is the recording-derived C1-seat constant, shared by real pin + shadow).")


# ---- three-state (v3.2 C2) ----
def clean_B_in_window(leg):
    s = S[leg]
    ds = s["done_step"]
    if ds is None:
        return False
    tcs, _ = term_cause_set(s)
    return (f <= ds <= WINDOW_HI) and (tcs == {"B_contact_loss"})


def m2b_no_terminal_through_hi():
    ds = S["M2b"]["done_step"]
    return (ds is None) or (ds > WINDOW_HI)


m2_cleanB = clean_B_in_window("M2")
m2b_cleanB = clean_B_in_window("M2b")
m2b_noterm = m2b_no_terminal_through_hi()
pin_assoc = P_of_record and m2_cleanB and m2b_noterm
branch_intr = P_of_record and m2_cleanB and m2b_cleanB
verdict = "PIN-ASSOCIATED" if pin_assoc else ("BRANCH-INTRINSIC" if branch_intr else "INCONCLUSIVE")
indep = (not m2b_noterm) and (not m2b_cleanB)
print("\n" + "=" * 72)
print("THREE-STATE VERDICT")
print("=" * 72)
print(
    f"  M2 clean-B in [f,{WINDOW_HI}]={m2_cleanB}   M2b clean-B in [f,{WINDOW_HI}]={m2b_cleanB}   "
    f"M2b no-terminal-thru-{WINDOW_HI}={m2b_noterm}"
)
print(f"  PIN-ASSOCIATED={pin_assoc}   BRANCH-INTRINSIC={branch_intr}")
print("\n  INDEPENDENT-OF-P (M2b terminates by an other cause in-window):")
print(f"    PIN-ASSOCIATED requires M2b no-terminal-thru-{WINDOW_HI} = {m2b_noterm} -> False regardless of P")
print(f"    BRANCH-INTRINSIC requires M2b clean-B = {m2b_cleanB} -> False regardless of P")
print(f"    => verdict is INCONCLUSIVE for ANY value of P (robust) = {indep}")
print(f"\n  >>> VERDICT = {verdict} <<<")

# ---- M1 necessity + M3 B5a ----
m1, m3 = S["M1"], S["M3"]
sh1 = m1.get("shadow")
m1_fire = sh1["first_shadow_fire_step"] if sh1 else "NO-SHADOW"
nec = (m1_fire is None) and (m1["g3_reached"] is False)
print("\n" + "=" * 72)
print("M1 NECESSITY (CC6) + M3 B5a")
print("=" * 72)
print(
    f"  M1: shadow.first_shadow_fire_step={m1_fire}  g3_reached={m1['g3_reached']}  "
    f"done_step={m1['done_step']}  cause={sorted(term_cause_set(m1)[0])}"
)
print(f"     => necessity discharged (shadow-fire=0 AND g3=false) = {nec}")
print(f"  M3: done_step={m3['done_step']}  cause={sorted(term_cause_set(m3)[0])}  (B5a = BLOCKED_BY_PRE_C2_DROP)")
