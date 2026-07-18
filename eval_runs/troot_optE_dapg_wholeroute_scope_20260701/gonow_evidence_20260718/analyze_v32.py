#!/usr/bin/env python3
"""Mechanical P / three-state analysis of the v3.2 evidence run (prereg §CORRECTION v3.1/v3.2)."""
import json, sys
from pathlib import Path

P = Path("eval_runs/troot_optE_dapg_wholeroute_scope_20260701/gonow_evidence_20260718")
LEAF = {
    "M1":  ("m1_b4shadow_ikchord",  "m1_b4shadow"),
    "M2":  ("m2_ff_pin_shadow",     "m2_ff_pin"),
    "M2b": ("m2b_ff_shadow_nopin",  "m2b_ff_nopin"),
    "M3":  ("m3_ikchord_natterm",   "m3_ikchord_natterm"),
}
CAUSES = ["A_held_z_floor", "B_contact_loss", "C_c1_escape", "explosion"]

def load(leg):
    leaf, tag = LEAF[leg]
    s = json.loads((P / leaf / f"summary_{tag}.json").read_text())
    ps = json.loads((P / leaf / f"per_step_{tag}.json").read_text())
    return s, ps

S, PS = {}, {}
for leg in LEAF:
    S[leg], PS[leg] = load(leg)

def term_cause_set(s):
    ds = s["done_step"]
    if ds is None:
        return set(), None
    fcs = s["first_cause_step"]
    return {k for k in CAUSES if fcs.get(k) == ds}, ds

print("="*70)
print("PER-LEG SUMMARY")
print("="*70)
for leg in ["M1", "M2", "M2b", "M3"]:
    s = S[leg]
    prov = s["provenance"]
    eff = s["effective_config"]
    sh = s.get("shadow")
    tcs, ds = term_cause_set(s)
    print(f"\n[{leg}] {LEAF[leg][0]}")
    print(f"  status={s['status']}  source_integrity_ok={prov.get('source_integrity_ok')}")
    print(f"  drive={eff.get('drive_mode')}  route_c1_pin_effective={eff.get('route_c1_pin_effective')}  pin_seat_seg={eff.get('pin_seat_seg')}")
    print(f"  RL_SIM_SUBSTEPS={eff.get('RL_SIM_SUBSTEPS')}  PHYSICS_STEPS_PER_RL={eff.get('PHYSICS_STEPS_PER_RL')}  ep_req={s.get('episode_steps_requested')}")
    print(f"  g3_reached={s['g3_reached']}  g3_step={s['g3_step']}")
    print(f"  first_cause_step={s['first_cause_step']}")
    print(f"  done_step={s['done_step']}  done_reward={s['done_reward']}  term_cause_set={sorted(tcs)}")
    if sh:
        print(f"  shadow.first_shadow_fire_step={sh['first_shadow_fire_step']}  max_dwell={sh.get('max_dwell')}  shadow_fire_before_drop={sh.get('shadow_fire_before_drop')}")
    else:
        print(f"  shadow=None")

# ---- f anchor ----
f = S["M2"]["shadow"]["first_shadow_fire_step"]
print("\n" + "="*70)
print("B1 CAUSAL BOUNDARY: f := M2 shadow.first_shadow_fire_step")
print("="*70)
print(f"f = {f}   (frozen expectation f==246 -> {'PASS' if f==246 else 'FAIL=>INCONCLUSIVE'})")

# ---- pre-fire trace equality on [0, f-1] (M2 vs M2b) ----
CMP = ["contact_r", "contact_l", "held_z_minus_rest", "dx_c1", "g_latched", "held_i", "grasped", "contact_loss_count"]
def rows_by_step(ps):
    return {r["step"]: r for r in ps}
r2, r2b = rows_by_step(PS["M2"]), rows_by_step(PS["M2b"])
need = set(range(0, f)) if isinstance(f, int) else set()
miss2 = sorted(need - set(r2)); miss2b = sorted(need - set(r2b))
rows_ok = (not miss2) and (not miss2b)
first_div = None
ndiff = 0
if rows_ok:
    for st in range(0, f):
        a, b = r2[st], r2b[st]
        d = [c for c in CMP if a.get(c) != b.get(c)]
        if d:
            ndiff += 1
            if first_div is None:
                first_div = (st, {c: (a.get(c), b.get(c)) for c in d})
trace_equal = rows_ok and (ndiff == 0)
print("\n" + "="*70)
print("B1 PRE-FIRE TRACE EQUALITY  (M2 vs M2b, per_step step in [0, f-1])")
print("="*70)
print(f"  rows [0,{f-1}] present: M2 missing={miss2}  M2b missing={miss2b}  -> rows_ok={rows_ok}")
print(f"  compared fields={CMP}")
print(f"  #divergent steps={ndiff}  first_divergence={first_div}")
print(f"  => pre_fire_trace_equal = {trace_equal}")

# ---- config-diff-set (M2 vs M2b) ----
eff2, eff2b = S["M2"]["effective_config"], S["M2b"]["effective_config"]
keys = sorted(set(eff2) | set(eff2b))
cfg_diff = {k for k in keys if eff2.get(k) != eff2b.get(k)}
# prereg bar = "{route_c1_pin_effective, pin_seat_seg} ONLY; any other diff -> INCONCLUSIVE" => SUBSET (no diff outside).
cfg_diff_ok = cfg_diff <= {"route_c1_pin_effective", "pin_seat_seg"}
print("\n" + "="*70)
print("CONFIG DIFF-SET (M2 vs M2b) — subset bar: no diff outside {route_c1_pin_effective, pin_seat_seg}")
print("="*70)
print(f"  diff_set={sorted(cfg_diff)}  (pin_seat_seg equal={eff2.get('pin_seat_seg')==eff2b.get('pin_seat_seg')}={eff2.get('pin_seat_seg')})  -> subset_ok={cfg_diff_ok}")

# ---- run-independent provenance equality (M2 vs M2b) ----
p2, p2b = S["M2"]["provenance"], S["M2b"]["provenance"]
prov_keys = ["harness_self_sha256_post", "recording_sha256", "venv_python",
             "source_closure_run_end", "changed_source_set", "missing_source_set",
             "added_during_drive", "build_added_unstable"]
prov_eq = {}
for k in prov_keys:
    prov_eq[k] = (p2.get(k) == p2b.get(k))
# clean source-integrity sets ([]):
clean2 = all(not p2.get(k) for k in ["changed_source_set","missing_source_set","added_during_drive","build_added_unstable"])
clean2b = all(not p2b.get(k) for k in ["changed_source_set","missing_source_set","added_during_drive","build_added_unstable"])
prov_all_eq = all(prov_eq.values())
print("\n" + "="*70)
print("RUN-INDEPENDENT PROVENANCE EQUALITY (M2 vs M2b)")
print("="*70)
for k in prov_keys:
    print(f"  {k}: equal={prov_eq[k]}")
print(f"  integrity sets clean: M2={clean2} M2b={clean2b}")
print(f"  => prov_all_equal={prov_all_eq}")

# ---- P predicate ----
def leg_ok(leg):
    s = S[leg]; return s["status"] == "COMPLETE" and s["provenance"].get("source_integrity_ok") is True
P_pred = (leg_ok("M2") and leg_ok("M2b") and prov_all_eq and cfg_diff_ok
          and (f == 246) and trace_equal and rows_ok)
print("\n" + "="*70)
print("P (common validity predicate)")
print("="*70)
print(f"  M2 COMPLETE+integrity={leg_ok('M2')}  M2b COMPLETE+integrity={leg_ok('M2b')}")
print(f"  prov_all_equal={prov_all_eq}  cfg_diff_ok={cfg_diff_ok}  f==246={(f==246)}  trace_equal={trace_equal}  rows_ok={rows_ok}")
print(f"  => P = {P_pred}")

# ---- three-state ----
def clean_B_in_window(leg):
    s = S[leg]; ds = s["done_step"]
    if ds is None: return False
    tcs, _ = term_cause_set(s)
    return (f <= ds <= 347) and (tcs == {"B_contact_loss"})
def m2b_no_terminal_through_347():
    ds = S["M2b"]["done_step"]
    return (ds is None) or (ds > 347)

m2_cleanB = clean_B_in_window("M2")
m2b_cleanB = clean_B_in_window("M2b")
m2b_noterm = m2b_no_terminal_through_347()
PIN_ASSOC   = P_pred and m2_cleanB and m2b_noterm
BRANCH_INTR = P_pred and m2_cleanB and m2b_cleanB
INCONCLUSIVE = not (PIN_ASSOC or BRANCH_INTR)
verdict = "PIN-ASSOCIATED" if PIN_ASSOC else ("BRANCH-INTRINSIC" if BRANCH_INTR else "INCONCLUSIVE")
print("\n" + "="*70)
print("THREE-STATE VERDICT")
print("="*70)
print(f"  M2 clean-B in [f,347]={m2_cleanB}   M2b clean-B in [f,347]={m2b_cleanB}   M2b no-terminal-thru-347={m2b_noterm}")
print(f"  PIN-ASSOCIATED={PIN_ASSOC}  BRANCH-INTRINSIC={BRANCH_INTR}  INCONCLUSIVE={INCONCLUSIVE}")
print(f"\n  >>> VERDICT = {verdict} <<<")

# ---- M1 necessity + M3 B5a ----
m1 = S["M1"]; sh1 = m1.get("shadow")
m1_fire = sh1["first_shadow_fire_step"] if sh1 else "NO-SHADOW"
print("\n" + "="*70)
print("M1 NECESSITY (CC6) + M3 B5a")
print("="*70)
print(f"  M1: shadow.first_shadow_fire_step={m1_fire}  g3_reached={m1['g3_reached']}  done_step={m1['done_step']}  cause={sorted(term_cause_set(m1)[0])}")
nec = (m1_fire in (None,) ) and (m1["g3_reached"] is False)
print(f"     => necessity discharged (shadow-fire=0 AND g3=false) = {nec}")
print(f"  M3: done_step={m3['done_step'] if (m3:=S['M3']) else '?'}  cause={sorted(term_cause_set(S['M3'])[0])}  (B5a = BLOCKED_BY_PRE_C2_DROP if A@~267)")
