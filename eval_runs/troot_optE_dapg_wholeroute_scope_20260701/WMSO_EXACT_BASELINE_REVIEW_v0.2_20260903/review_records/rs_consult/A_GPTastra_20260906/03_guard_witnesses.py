#!/usr/bin/env python3
"""Reviewer-written reduced witnesses, not the WMSO implementation.

No robot, simulator, network, repository writes, or production dependencies.
The ordinal labels below specify event ordering, not timeout recommendations.
Synthetic hashes are hashes of small illustrative projections, never source pins.
The controls are authored by this reviewer, not independent/blind validation.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


def projection_hash(value: Any) -> str:
    # ASCII-only illustrative JSON; this is NOT a general WCJ implementation.
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def stop_witness() -> dict[str, Any]:
    last_read_disposition = None  # Last successful read was EXECUTOR.
    def unread_output(hb_lost: bool) -> str:
        if hb_lost:
            return "SAFE_STOP"  # 05:518, branch (i').
        return "SAFE_STOP" if last_read_disposition == "SAFE_STOP" else "HOLD"
    outputs = [unread_output(True), unread_output(False)]
    assert outputs == ["SAFE_STOP", "HOLD"]
    # Local stop latch, cleared ONLY by a matching authorized clearance.
    latched_stop = False
    control_outputs = []
    for heartbeat_lost in [True, False]:
        latched_stop = latched_stop or heartbeat_lost
        control_outputs.append("SAFE_STOP" if latched_stop else "HOLD")
    assert control_outputs == ["SAFE_STOP", "SAFE_STOP"]
    return {"finding": "GA-01", "assumptions": [
        "Manager remains unreadable; gateway does not restart.",
        "No outstanding ISL SafetyDecision; heartbeat loss is detected by the consumer.",
        "No clearance occurs and no newer AuthorityState read succeeds."],
        "specified_branch_outputs": outputs, "local_latch_control": control_outputs}


def definition_witness() -> dict[str, Any]:
    identity = {"ns": "toy", "skill": "s", "bundle": "same", "variant": "v", "brev": 1}
    action_id = projection_hash(identity)
    definition_a = {"identity": identity, "provenance": "A"}
    definition_b = {"identity": identity, "provenance": "B"}
    cert = {"action_id": action_id, "definition_hash": projection_hash(definition_a)}
    lease = {"action_id": action_id, "definition_hash": projection_hash(definition_b)}
    selected_guard = cert["action_id"] == lease["action_id"]
    exact_subject = cert["definition_hash"] == lease["definition_hash"]
    assert selected_guard and not exact_subject
    assert not (selected_guard and exact_subject)
    return {"finding": "GA-02", "assumptions": [
        "Provenance-only differences do not change the action identity projection.",
        "All other relevant start guards are held constant and satisfied.",
        "These are synthetic projections, not valid full SkillDefinition fixtures."],
        "action_id_equality": selected_guard, "definition_hash_equality": exact_subject,
        "strengthened_guard_accepts": selected_guard and exact_subject}


def freshness_witness() -> dict[str, Any]:
    events = ["VALIDATE_OK", "BELIEF_EXPIRES", "CAS", "OTHER_PERMIT_TERMS_EXPIRE"]
    def before(a: str, b: str) -> bool:
        return events.index(a) < events.index(b)
    old_report_ok = True
    specified_selected_guard = old_report_ok and before("CAS", "OTHER_PERMIT_TERMS_EXPIRE")
    fresh_at_cas = before("CAS", "BELIEF_EXPIRES")
    assert specified_selected_guard and not fresh_at_cas
    return {"finding": "GA-03", "assumptions": [
        "The same belief/start report is used; owner/epoch do not change during the wait.",
        "ACK, authority decision, acceptance and deployment evidence remain valid at CAS.",
        "Event labels are an ordering only; no numerical timeout is proposed."],
        "event_order": events, "selected_guard_accepts": specified_selected_guard,
        "belief_fresh_at_cas": fresh_at_cas,
        "freshness_conjoined_control_accepts": specified_selected_guard and fresh_at_cas}


def cell_scope_witness() -> dict[str, Any]:
    left = {"resource_id": "ee_left", "serial": "L"}
    right = {"resource_id": "ee_right", "serial": "R"}
    cell_a = {"site_id": "SITE", "cell_id": "CELL", "arms": [left, right]}
    cell_b = {"site_id": "SITE", "cell_id": "CELL", "arms": [right, left]}
    hash_a, hash_b = projection_hash(cell_a), projection_hash(cell_b)
    def keyed_arms(c: dict[str, Any]) -> dict[str, str]:
        return {a["resource_id"]: a["serial"] for a in c["arms"]}
    assert keyed_arms(cell_a) == keyed_arms(cell_b)
    assert hash_a != hash_b
    specified_cell_veto_for_b = hash_b == hash_a
    stable_cell_veto_for_b = (cell_b["site_id"], cell_b["cell_id"]) == (cell_a["site_id"], cell_a["cell_id"])
    assert not specified_cell_veto_for_b and stable_cell_veto_for_b
    return {"finding": "GA-04", "assumptions": [
        "Both profile variants were separately accepted against the same baseline/role heads.",
        "Per-arm checks address resource_id; there is no normative sorting of the arms tuple.",
        "Unshown profile/cell fields are identical. This tests only the cell-veto predicate.",
        "It does not bypass an independent live safety override or establish full permit admission."],
        "same_resource_to_robot_mapping": True, "configuration_hashes_equal": False,
        "current_hash_based_cell_veto_for_b": specified_cell_veto_for_b,
        "stable_physical_cell_veto_for_b": stable_cell_veto_for_b}


def two_heads_witness() -> dict[str, Any]:
    accepted = {"id": "A_g", "state": "ACCEPTED", "generation": "g", "supersedes": None}
    proposed = {"id": "P_g_next", "state": "PROPOSED", "generation": "g_next", "supersedes": accepted["id"]}
    prior = [accepted, proposed]
    log_head = prior[-1]
    authority_head = next(r for r in reversed(prior) if r["state"] != "PROPOSED")
    suspended = {"id": "S", "state": "SUSPENDED", "generation": log_head["generation"], "supersedes": log_head["id"]}
    event_target_by_literal_rule = suspended["supersedes"]
    active_lease_acceptance = authority_head["id"]
    matches_active = event_target_by_literal_rule == active_lease_acceptance
    assert not matches_active
    corrected_causal_target = authority_head["id"]
    assert corrected_causal_target == active_lease_acceptance
    # Separate periodic head checking may still stop the lease; no permanent bypass claim.
    periodic_head_check_would_reject = suspended["state"] != "ACCEPTED"
    assert periodic_head_check_would_reject
    return {"finding": "GA-05", "assumptions": [
        "Use the state-specific SUSPENDED append rule that supersedes the log head.",
        "The transition table's omission of PROPOSED->SUSPENDED is a separate ambiguity.",
        "The literal event target is S.supersedes_record_hash, as stated in 05:249.",
        "Periodic head-check remains available and may stop the lease later."],
        "log_head": log_head["id"], "authority_head_before_suspension": authority_head["id"],
        "event_target": event_target_by_literal_rule, "active_lease_acceptance": active_lease_acceptance,
        "event_target_matches": matches_active, "corrected_causal_target_matches": True,
        "periodic_head_check_would_reject": periodic_head_check_would_reject}


def mark_boundary_witness() -> dict[str, Any]:
    before_state = {"epoch": "e", "seq": "q"}
    after_mark = {"epoch": "e", "seq": "q+1"}
    universal_expected_epoch = "e+1"
    assert after_mark["epoch"] != universal_expected_epoch
    scoped_rule = after_mark["epoch"] == before_state["epoch"] and after_mark["seq"] == "q+1"
    assert scoped_rule
    return {"finding": "GA-06", "assumptions": [
        "MARK_BOUNDARY_WAIT is an explicit CasKind with a successful transition.",
        "Symbolic ordinals stand for epoch/sequence; this is not a runtime implementation."],
        "before": before_state, "legal_mark_after": after_mark,
        "universal_INV_02_holds": False, "per_kind_control_holds": scoped_rule}


def main() -> None:
    result = {"kind": "REVIEWER_DERIVED_REDUCED_WITNESSES", "target_version": "v0.2.8",
              "target_commit": "0c6f11c91bf42f3a0c0fa9a89190c8e298bd197d",
              "not_wmso_implementation": True, "not_blind_or_independent_controls": True,
              "physical_tests_performed": False, "original_checker_run": False,
              "original_source_sha256_recomputed": False,
              "results": [stop_witness(), definition_witness(), freshness_witness(),
                          cell_scope_witness(), two_heads_witness(), mark_boundary_witness()],
              "text_only_finding_not_executed": ["GA-07"]}
    result["completed_witness_groups"] = len(result["results"])
    output = Path(__file__).with_name("04_guard_witness_results.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"completed_witness_groups": result["completed_witness_groups"],
                      "result_file": str(output), "scope": "reduced reviewer-authored models only"}))


if __name__ == "__main__":
    main()
