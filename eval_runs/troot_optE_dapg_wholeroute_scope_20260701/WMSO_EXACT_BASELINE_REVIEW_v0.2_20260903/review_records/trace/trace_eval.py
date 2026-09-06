#!/usr/bin/env python3
"""Limited-model trace evaluator for the WMSO review candidates (v0.2.8 / v0.2.9 / v0.2.10).

NOT the WMSO implementation, NOT a formal model generated from the full text, NOT a real-machine test.
Each version's rules are hand-transcribed into small state machines; every rule cites the doc anchor it
encodes (see RULES) so an independent verifier can check fidelity. Expected results come from the pinned
trace specs (TRACES_*.json; sha256 in PIN_*.sha256) and were fixed BEFORE this evaluator existed.

Usage: python3 trace_eval.py <trace_dir> <out_results.json>
"""
import json, sys, hashlib, subprocess, os
from decimal import Decimal
TD, OUT = sys.argv[1], sys.argv[2]
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()
VERSIONS = ["v028", "v029", "v0210"]
SAFE_STOP, SAFE_HOLD, SETPOINT, STOP_PATH = "SAFE_STOP", "SAFE_HOLD", "SETPOINT", "VERIFIED_STOP_PATH"

# ---- version feature table (each entry = the doc anchor the rule is transcribed from) --------------------
RULES = {
 "latch":            {"v028": None, "v029": "05 §5.2 (i′) v0.2.9: stop_latch; 解除 = seq > latch 時観測 seq の SAFEHOLD", "v0210": "05 §5.2 (i′) v0.2.10: 解除 = SAFEHOLD ∧ SAFE_STOP ∧ stop_report_id ∈ stop_report_acks"},
 "latch_durable":    {"v028": False, "v029": False, "v0210": True},   # 05 §2 gateway 状態 (v0.2.10: gateway 局所 durable)
 "sibling_key":      {"v028": "cell_identity_hash", "v029": "(site_id, cell_id)", "v0210": "(site_id, cell_id)"},  # 05 §3.4 (i) 兄弟節
 "definition_bound": {"v028": False, "v029": True, "v0210": True},    # 05 §3.5 条件 8 / (n)（GA-02）
 "belief_at_cas":    {"v028": False, "v029": True, "v0210": True},    # 05 §3.5 条件 2 / 5（GA-03）
 "event_target":     {"v028": "log_head", "v029": "first_accepted_via_supersedes", "v0210": "first_accepted_via_supersedes"},  # 06 §8.3 状態遷移（GA-05）
 "inv02_per_kind":   {"v028": False, "v029": True, "v0210": True},    # 05 INV-02（GA-06）
 "drift_slot":       {"v028": False, "v029": True, "v0210": True},    # 05 (l) / 06 clock_drift_tolerance_s（GA-07）
 "cell_ledger":      {"v028": False, "v029": False, "v0210": True},   # 06 §8.3 CellLedger / 05 (i) cell 停止（RS-1）
 "baseline_key":     {"v028": "cell_id", "v029": "cell_id", "v0210": "(site_id, cell_id)"},  # 06 baseline registry（RS-1）
 "margin":           {"v028": False, "v029": False, "v0210": True},   # 05 (k)（RS-3）
 "pair_provenance":  {"v028": False, "v029": False, "v0210": True},   # 05 (l) host_id / boot_id（RS-3）
 "time_sync":        {"v028": False, "v029": False, "v0210": True},   # 05 (l) TIME_SYNC（RS-3）
 "safehold_verify":  {"v028": False, "v029": False, "v0210": True},   # 05 §5.2 (iii) 3 段（RS-2）
}
def F(k, v): return RULES[k][v]
def dec(x): return None if x is None else Decimal(str(x))

# ---- gateway model ---------------------------------------------------------------------------------------
class Gateway:
    def __init__(self, v, st):
        self.v = v; self.link = st.get("manager_link", "up"); self.last = st.get("last_disposition")
        self.latch = bool(st.get("stop_latch", False)); self.latch_id = None; self.latch_seq = None
        self.isl = st.get("isl_heartbeat", "ok"); self.state = dict(st.get("authority_state", {"owner": "EXECUTOR", "seq": 0, "safehold_disposition": None}))
        self.state.setdefault("acks", set()); self.path_ok = bool(st.get("safehold_path_verified", True)); self.read_ok = False
    def ev(self, e):
        k = e["e"]
        if k == "GATEWAY_I_PRIME_SAFESTOP":
            self.isl = "lost"
            if F("latch", self.v): self.latch = True; self.latch_id = e["stop_report_id"]; self.latch_seq = e["latch_seq_observed"]
        elif k == "ISL_HEARTBEAT_RETURNS": self.isl = "ok"
        elif k == "MANAGER_TRANSITION":
            self.state.update(owner=e["to"], seq=e["seq"], safehold_reason=e.get("reason"), safehold_disposition=e.get("disposition"))
            if e.get("ack_of_stop_report"): self.state["acks"] = set(self.state["acks"]) | {e["ack_of_stop_report"]}
        elif k == "MANAGER_LINK_RESTORED": self.link = "up"
        elif k == "GATEWAY_LINEARIZED_READ":
            if self.link != "up": return
            self.read_ok = True; self.last = self.state.get("safehold_disposition")
            if self.latch:  # release rule per version
                if self.v == "v029" and self.state["owner"] == "SAFEHOLD" and self.state["seq"] > self.latch_seq: self.latch = False
                if self.v == "v0210" and self.state["owner"] == "SAFEHOLD" and self.state.get("safehold_disposition") == "SAFE_STOP" and self.latch_id in self.state["acks"]: self.latch = False
        elif k == "SET_SAFEHOLD_PATH_VERIFIED": self.path_ok = bool(e["value"])
        elif k == "GATEWAY_RESTART":
            self.latch = self.latch if F("latch_durable", self.v) else False
    def output(self):
        # (i′): ISL heartbeat lost or latch → SafeStop  (v028: heartbeat-lost only)
        if self.isl == "lost" or (F("latch", self.v) and self.latch): return SAFE_STOP
        if self.link == "up" and self.read_ok:   # linearized read available → (ii)/(iii) on manager state
            if self.state["owner"] == "EXECUTOR": return SETPOINT
            return SAFE_STOP if self.state.get("safehold_disposition") == "SAFE_STOP" else SAFE_HOLD
        # manager unreadable → (iii)
        if self.last == "SAFE_STOP": return SAFE_STOP
        if F("safehold_verify", self.v): return SAFE_HOLD if self.path_ok else STOP_PATH
        return SAFE_HOLD

# ---- registry / ledger model ------------------------------------------------------------------------------
class Registry:
    """profiles: {name: {cell:(site,cell), khash, head_state, reason}}; ledger (v0210): canonical ids, aliases, stops, clearances."""
    def __init__(self, v, st):
        self.v = v; self.canon = set(); self.alias = {}; self.stops = {}; self.pred = {}
        led = st.get("ledger", {})
        for c in led.get("canonical", []): self.canon.add(tuple(c))
        for a, c in led.get("aliases", {}).items(): self.alias[tuple(a.split("/"))] = tuple(c.split("/"))
        cs = st.get("cell_stop")
        if isinstance(cs, dict):
            for c, s in cs.items(): self.stops[tuple(c.split("/"))] = {"resolved": s != "unresolved"}
        elif isinstance(cs, str) and "cell" in st:      # D4 form: "cell": [site, cell], "cell_stop": "unresolved"
            self.canon.add(tuple(st["cell"])); self.stops[tuple(st["cell"])] = {"resolved": cs != "unresolved"}
        self.role_registry = st.get("role_registry", {"opA": ["INDEPENDENT_SAFETY_APPROVER"], "opB": ["FACILITY_OPERATIONS_OWNER"]})
    def resolve(self, cell):
        cell = tuple(cell)
        if not F("cell_ledger", self.v): return cell, True            # no ledger: id taken literally
        if cell in self.canon: return cell, True
        if cell in self.alias and self.alias[cell] in self.canon: return self.alias[cell], True
        return cell, False
    def unresolved_stop(self, canon):
        if not F("cell_ledger", self.v): return False
        s = self.stops.get(tuple(canon)); return bool(s and not s["resolved"])
    def stop(self, cell): self.stops[tuple(cell)] = {"resolved": False}
    def clearance(self, cell, approvals):
        roles = [r for r, _ in approvals]; ops = [o for _, o in approvals]
        ok = (set(roles) == {"INDEPENDENT_SAFETY_APPROVER", "FACILITY_OPERATIONS_OWNER"} and len(set(ops)) == 2
              and all(r in self.role_registry.get(o, []) for r, o in approvals))
        if ok and tuple(cell) in self.stops: self.stops[tuple(cell)]["resolved"] = True
        return ok

def run_trace(tr, v, control=False, amend=None):
    tid = tr["id"]; st = json.loads(json.dumps(tr["initial_state"])); events = tr["control"]["events"] if control else tr["events"]
    if control and amend: st.update(amend.get("initial_state_override", {})); events = amend.get("events", events)
    obs = {}
    # ----------------------------------------------------------------- GA-01 / D5 / D6 / D11 (gateway)
    if tid in ("GA-01", "D5", "D6", "D11"):
        if control and tid == "D5" and v == "v028": return "N/A", {"note": "v028 has no latch structure (spec v028_note)"}
        g = Gateway(v, st)
        for e in events: g.ev(e)
        out = g.output(); obs["output"] = out; obs["latch"] = g.latch
        if tid == "GA-01": ok = (out == SAFE_HOLD) if control else (out == SAFE_STOP)
        elif tid == "D5": ok = (out == SAFE_STOP) if not control else (out == SAFE_STOP and not g.latch)
        elif tid == "D6": ok = (out == SETPOINT) if control else (out == SAFE_STOP)
        else: ok = (out == SAFE_HOLD) if control else (out == STOP_PATH)
        return ("PASS" if ok else "VIOLATION"), obs
    # ----------------------------------------------------------------- GA-02
    if tid == "GA-02":
        cert = st["certificate"]; e = events[0]
        accept = e["skill_action_id"] == cert["skill_action_id"] and (not F("definition_bound", v) or e["skill_definition_hash"] == cert["skill_definition_hash"])
        obs["lease_accepted"] = accept
        return ("PASS" if (accept if control else not accept) else "VIOLATION"), obs
    # ----------------------------------------------------------------- GA-03
    if tid == "GA-03":
        t = [e for e in events if e["e"] == "CAS_AT"][0]["t"]
        accept = t < st["effective_expires_at"] and (not F("belief_at_cas", v) or t < st["belief_valid_until"])
        obs["cas_accepted"] = accept
        return ("PASS" if (accept if control else not accept) else "VIOLATION"), obs
    # ----------------------------------------------------------------- GA-04
    if tid == "GA-04":
        me, sib = st["this_profile"], dict(st["sibling"])
        for e in events:
            if e["e"] == "SET_SIBLING_CELL": sib["site_id"], sib["cell_id"] = e["site_id"], e["cell_id"]
        same = (sib["cell_identity_hash"] == me["cell_identity_hash"]) if F("sibling_key", v) == "cell_identity_hash" else ((sib["site_id"], sib["cell_id"]) == (me["site_id"], me["cell_id"]))
        issued = not (same and sib["head_state"] in ("SUSPENDED", "REVOKED")); obs["permit_issued"] = issued
        return ("PASS" if (issued if control else not issued) else "VIOLATION"), obs
    # ----------------------------------------------------------------- GA-05
    if tid == "GA-05":
        recs = {r["hash"]: r for r in st["records"]}; sus = [e for e in events if e["e"] == "SUSPENDED_APPENDED"][0]
        target = sus["supersedes"]
        if F("event_target", v) == "first_accepted_via_supersedes":
            while recs[target]["state"] != "ACCEPTED": target = recs[target]["supersedes"]
        stopped = target == st["active_lease_record_hash"]; obs["event_target"] = target; obs["lease_stopped"] = stopped
        return ("PASS" if stopped else "VIOLATION"), obs
    # ----------------------------------------------------------------- GA-06
    if tid == "GA-06":
        epoch = st["control_epoch"]; ok = True
        for e in events:
            if e["e"] == "CAS":
                new = epoch + 1 if e["kind"].startswith("TRANSFER") else epoch   # MARK_BOUNDARY_WAIT is epoch-invariant in the text of all versions
                stated_plus1 = (new == epoch + 1)
                if not F("inv02_per_kind", v) and not stated_plus1: ok = False   # v028 states "+1 on every CAS success" → violated by MARK
                epoch = new
        obs["final_epoch"] = epoch; return ("PASS" if ok else "VIOLATION"), obs
    # ----------------------------------------------------------------- GA-07
    if tid == "GA-07":
        b = dict(st["baseline"])
        for e in events:
            if e["e"] == "SET_BASELINE_FIELD": b.update({k: x for k, x in e.items() if k != "e"})
        if control and v == "v028": return "N/A", {"note": "v028 has no tolerance slot (spec v028_note)"}
        if F("drift_slot", v): tol = dec(b.get("clock_drift_tolerance_s"))
        else: tol = dec(b["diagnostic_items"][0][2])   # v028 (l): "drift が baseline diagnostic item の許容内" — item carries (period, worst-case detection) only
        drift = dec(st["drift_observed_s"]); issued = tol is not None and drift <= tol; obs["tolerance_used"] = str(tol); obs["permit_issued"] = issued
        return ("PASS" if (issued if control else not issued) else "VIOLATION"), obs
    # ----------------------------------------------------------------- D1 (baseline key)
    if tid == "D1":
        heads = {}
        for k, h in st["baseline_head"].items():
            site, cell = k.split("/"); key = cell if F("baseline_key", v) == "cell_id" else (site, cell); heads[key] = h
        rec = st["record"]; fired = None
        for e in events:
            if e["e"] == "BASELINE_SUPERSEDED":
                site, cell = e["cell"]; key = cell if F("baseline_key", v) == "cell_id" else (site, cell); heads[key] = e["new_head"]
            elif e["e"] == "HEAD_CHECK":
                site, cell = e["for_record_cell"]; key = cell if F("baseline_key", v) == "cell_id" else (site, cell)
                fired = heads.get(key) != rec["timing_baseline_hash"]
        obs["baseline_superseded_fired_for_S1"] = fired
        return ("PASS" if (fired if control else not fired) else "VIOLATION"), obs
    # ----------------------------------------------------------------- D2 / D3 / D4 (ledger)
    if tid in ("D2", "D3", "D4"):
        R = Registry(v, st); prof_cell = tuple(st.get("profile_cell", st.get("cell", ["S1", "C1"]))); accepted = True; sibling_suspended = False; unresolvable = False
        if tid == "D2": R.canon.add(("S1", "C1"))
        for e in events:
            k = e["e"]
            if k == "CELL_STOP_RECORDED":
                cell = tuple(e.get("cell", prof_cell))
                if F("cell_ledger", v): R.stop(cell)
                else: sibling_suspended = True          # v028/v029: cell trigger = SUSPENDED on all records of the cell
            elif k == "CELL_CLEARANCE":
                if F("cell_ledger", v): R.clearance(tuple(st.get("cell", prof_cell)), [tuple(a) for a in e["approvals"]])
                # v028/v029: no cell-stop clearance structure (analog = profile re-acceptance two-key, a different operation)
            elif k == "REACCEPT":
                accepted = True; sibling_suspended = False   # ACCEPTED(gen+1) replaces the SUSPENDED head in the profile registry
            elif k == "REGISTER_PROFILE":
                if "profile_cell" in e: prof_cell = tuple(e["profile_cell"])
                if e.get("alias_to"): R.alias[prof_cell] = tuple(e["alias_to"].split("/")); R.canon.add(tuple(e["alias_to"].split("/")))
                if e.get("cell_stop", "keep") is None: R.stops.pop(tuple(e["alias_to"].split("/")), None)
            elif k == "PERMIT_REQUEST":
                canon, ok = R.resolve(prof_cell)
                if not ok: unresolvable = True
                issued = accepted and not sibling_suspended and ok and not R.unresolved_stop(canon)
                obs.update(canonical=list(canon), resolved=ok, unresolved_stop=R.unresolved_stop(canon), sibling_suspended=sibling_suspended, permit_issued=issued)
        issued = obs.get("permit_issued"); expect_issue = control
        if tid == "D4" and not control and not F("cell_ledger", v):
            obs["note"] = "structure absent: no cell-stop clearance record in this version; profile re-acceptance two-key is a different operation"
            return "VIOLATION", obs
        return ("PASS" if (issued if expect_issue else not issued) else "VIOLATION"), obs
    # ----------------------------------------------------------------- D7 / D8 / D9 / D10 (clock)
    if tid in ("D7", "D8", "D9", "D10"):
        b = dict(st["baseline"]); pair = dict(st["ref_pair"]); now = dict(st.get("now", {})); ts = dict(st.get("time_sync", {}))   # inputs absent from the spec = held constant and satisfied
        deadline = None; issued = None; queried = None
        for e in events:
            k = e["e"]
            if k == "SET_BASELINE_FIELD": b.update({x: y for x, y in e.items() if x != "e"})
            elif k == "SET_NOW_BOOT": now["boot_id"] = e["boot_id"]
            elif k == "SET_TIME_SYNC": ts.update({x: y for x, y in e.items() if x != "e"})
            elif k == "PERMIT_REQUEST":
                ok = True
                # (l) drift check
                if now:
                    drift = abs((dec(now["wall"]) - dec(pair["wall_ref"])) - (dec(now["mono"]) - dec(pair["mono_ref"])))
                    tol = dec(b.get("clock_drift_tolerance_s")); ok = ok and tol is not None and drift <= tol
                    if F("pair_provenance", v): ok = ok and pair.get("host_id") == now.get("host_id") and pair.get("boot_id") == now.get("boot_id")
                    if F("time_sync", v) and "time_sync" in st:   # inputs absent from the spec are held constant and satisfied
                        ok = ok and bool(ts.get("synchronized")) and ts.get("est_error_s") is not None and dec(ts["est_error_s"]) <= dec(b["clock_sync_error_bound_s"]) and dec(ts["ref_age_s"]) <= dec(b["clock_sync_max_ref_age_s"])
                # (k) deadline conversion
                if "wall_deadline" in st:
                    m = dec(b.get("clock_correspondence_margin_s")) if F("margin", v) else Decimal(0)
                    if F("margin", v) and m is None: ok = False
                    else: deadline = dec(pair["mono_ref"]) + (dec(st["wall_deadline"]) - dec(pair["wall_ref"])) - m
                issued = ok
            elif k == "CLOCK_REF_UPDATED": pair.update(wall_ref=e["wall_ref"], mono_ref=e["mono_ref"])   # (k): permit deadline fixed at issuance in every version
            elif k == "DEADLINE_QUERY": queried = deadline
        obs.update(permit_issued=issued, validity_deadline_mono=(str(deadline) if deadline is not None else None))
        if tid == "D8":
            return ("PASS" if (issued and queried == deadline) else "VIOLATION"), obs
        if control and tid == "D7" and issued and tr["control"].get("expected_deadline_mono_v0210") is not None and v == "v0210":
            obs["deadline_matches_pinned"] = (deadline == dec(tr["control"]["expected_deadline_mono_v0210"]))
        return ("PASS" if (issued if control else not issued) else "VIOLATION"), obs
    raise SystemExit("unknown trace " + tid)

def main():
    pin = {l.split()[1]: l.split()[0] for l in open(f"{TD}/PIN_20260906.sha256") if l.strip()}
    amend_fn = "TRACES_CONTROL_AMENDMENT_20260906.json"; amend = {}
    if os.path.exists(f"{TD}/{amend_fn}"):
        raw = open(f"{TD}/{amend_fn}", "rb").read(); h = hashlib.sha256(raw).hexdigest()
        pin2 = {l.split()[1]: l.split()[0] for l in open(f"{TD}/PIN_20260906_v2.sha256") if l.strip()}; assert pin2[amend_fn] == h, (amend_fn, h)
        amend = {a["id"]: a for a in json.loads(raw)["amendments"]}; results_amend = {"file": amend_fn, "sha256": h}
    results = {"kind": "TRACE_EVAL_RESULTS", "evaluation_kind": "限定モデル（trace_eval.py）— WMSO 実装 / 形式モデル / 実機ではない", "evaluated_utc": NOW, "spec_sha256_verified": {}, "sets": []}
    if amend: results["control_amendment"] = results_amend
    tot = {"match": 0, "mismatch": 0}
    for fn in ("TRACES_GA_posthoc_20260906.json", "TRACES_v0210_prepinned_20260906.json"):
        raw = open(f"{TD}/{fn}", "rb").read(); h = hashlib.sha256(raw).hexdigest(); assert pin[fn] == h, (fn, h, pin[fn]); results["spec_sha256_verified"][fn] = h
        spec = json.loads(raw); rows = []
        for tr in spec["traces"]:
            row = {"id": tr["id"], "title": tr["title"], "per_version": {}, "control": {}}
            for v in VERSIONS:
                res, obs = run_trace(tr, v); exp = tr["expected"][v]; ok = (res == exp)
                row["per_version"][v] = {"expected": exp, "observed": res, "match": ok, "obs": obs}; tot["match" if ok else "mismatch"] += 1
                cres, cobs = run_trace(tr, v, control=True)
                row["control"][v] = {"expected": tr["control"]["expected_all"] if cres != "N/A" else "N/A", "observed": cres, "match": (cres in ("PASS", "N/A")), "obs": cobs}
                if tr["id"] in amend:   # original control kept and reported as-is; amended control evaluated separately (spec not overwritten)
                    ares, aobs = run_trace(tr, v, control=True, amend=amend[tr["id"]])
                    row["control"][v]["amended"] = {"observed": ares, "match": (ares in ("PASS", "N/A")), "obs": aobs, "reason": amend[tr["id"]]["reason"]}
                    if ares not in ("PASS", "N/A"): tot["mismatch"] += 1
                    tot.setdefault("control_spec_defects_original", 0); tot["control_spec_defects_original"] += (1 if cres not in ("PASS", "N/A") else 0)
                elif cres not in ("PASS", "N/A"): tot["mismatch"] += 1
            rows.append(row)
        results["sets"].append({"spec": fn, "label": spec["label"], "pinned_before_fix": spec["pinned_before_fix"], "rows": rows})
    results["summary"] = tot
    json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
    # console table
    for s in results["sets"]:
        print(f"== {s['spec']} [{s['label']}]")
        print("| id | v028 exp/obs | v029 exp/obs | v0210 exp/obs | control v028/v029/v0210 |")
        for r in s["rows"]:
            pv = r["per_version"]; c = r["control"]
            cell = lambda v: f"{pv[v]['expected']}/{pv[v]['observed']}{'' if pv[v]['match'] else ' ✗'}"
            am = lambda v: (f"→{c[v]['amended']['observed']}" if 'amended' in c[v] else "")
            print(f"| {r['id']} | {cell('v028')} | {cell('v029')} | {cell('v0210')} | {c['v028']['observed']}{am('v028')}/{c['v029']['observed']}{am('v029')}/{c['v0210']['observed']}{am('v0210')} |")
    print("summary:", tot)
if __name__ == "__main__": main()
