#!/usr/bin/env python3
"""Build D1.1-B v2 golden fixtures (post-debate schema) and emit them as banked JSON.

Changes vs v1 (debate folds):
- IDENTICAL carries NO hash (fixpoint removed)   [CC3-CH2 / CC5-C2]
- flatten_order declared per feature             [CC4-C4-03]
- history.layout declared                        [CC3-CH6 / CC4 / CC5-C5]
- HANDOFF source removed from v1 vocabulary      [CC2-C5 / CC3-CH10]
- G-3 added: >=2-element frozenset, action_scale, EXPLICIT_SUPERSEDE, MIN_MAX,
  XYZW_UNIT, ZERO_IS_VALID, OLDEST_FIRST/ZERO_PAD, one-sided bounds, dual-arm width
"""
import hashlib
import json
import sys
from math import prod
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")


def wcj_bytes(obj):
    """Canonical bytes. ASCII-key subset of frozen DESIGN sec.2 WCJ.

    Rejects: float type, bool where int is required, non-ASCII keys, duplicate keys
    (json.dumps cannot produce duplicates from a dict, so the guard is on load).
    """
    def check(o, path="$"):
        if isinstance(o, dict):
            for k, v in o.items():
                if not isinstance(k, str) or not k.isascii():
                    raise ValueError(f"non-ASCII key at {path}: {k!r}")
                check(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                check(v, f"{path}[{i}]")
        elif isinstance(o, bool):
            raise ValueError(f"bool is not a permitted WCJ scalar at {path}")
        elif isinstance(o, float):
            raise ValueError(f"float type rejected at {path} (use CanonicalDecimal string)")
    check(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def h(obj):
    b = wcj_bytes(obj)
    return hashlib.sha256(b).hexdigest(), len(b)


belief_schema_hash = hashlib.sha256(b"WMSO-D11B-GOLDEN-BELIEF-SCHEMA-V1").hexdigest()
superseded_demo_hash = hashlib.sha256(b"WMSO-D11B-GOLDEN-SUPERSEDED-DEMO-BINDING-V1").hexdigest()
topology_ledger_hash = hashlib.sha256(b"WMSO-D11B-GOLDEN-TOPOLOGY-LEDGER-V1").hexdigest()


def feat(fid, src, off, shape, dtype, unit, frame, *, quat=None, norm=None, tf=None, bounds=None):
    return {
        "field_id": fid, "source": src, "offset": off, "length": prod(shape),
        "dtype": dtype, "shape": list(shape), "unit": unit, "frame": frame,
        "flatten_order": "ROW_MAJOR",
        "quaternion": quat, "normalizer": norm, "transform": tf, "bounds": bounds,
    }


G1 = {
    "binding_schema_version": "1.0",
    "obs": {
        "features": [
            feat("ee_pos_right", "SEMANTIC_OBS", 0, [3], "FLOAT32", "m", "world"),
            feat("gripper_width_right", "SEMANTIC_OBS", 3, [1], "FLOAT32", "m", "none"),
        ],
        "total_dim": 4, "history": None,
        "timing": {"policy_rate_hz": "30", "obs_sampling_rate_hz": "30", "max_obs_staleness_s": None},
        "masks": [], "belief_inputs": [], "container_dtype": "FLOAT32",
    },
    "action": {
        "features": [
            feat("ee_delta_right", "SEMANTIC_ACTION", 0, [3], "FLOAT32", "m", "world",
                 tf={"scale": "0.01", "bias": "0"}, bounds={"lower": "-0.02", "upper": "0.02"}),
            feat("gripper_cmd_right", "SEMANTIC_ACTION", 3, [1], "FLOAT32", "dimensionless", "none",
                 bounds={"lower": "-1", "upper": "1"}),
        ],
        "total_dim": 4, "control_mode": "DIFF_IK_EE_TARGET", "action_scale": None,
        "timing": {"action_rate_hz": "30", "hold": "ZERO_ORDER_HOLD"},
        "container_dtype": "FLOAT32",
    },
    "lineage_declaration": {"training_lineage": "RL_ONLY", "bc_stage_binding": None},
}

G2 = {
    "binding_schema_version": "1.0",
    "obs": {
        "features": [
            feat("ee_quat_right", "SEMANTIC_OBS", 0, [4], "FLOAT32", "dimensionless", "world",
                 quat="WXYZ_UNIT"),
            feat("cable_kp", "BELIEF", 4, [2, 3], "FLOAT32", "m", "world",
                 norm={"scheme": "MEAN_STD", "stats_key": "obs_norm_v1"}),
            feat("cable_kp_valid", "BELIEF", 10, [1], "BOOL", "dimensionless", "none"),
        ],
        "total_dim": 11,
        "history": {"depth": 3, "order": "NEWEST_FIRST", "padding": "REPEAT_OLDEST", "layout": "STEP_MAJOR"},
        "timing": {"policy_rate_hz": "30", "obs_sampling_rate_hz": "120", "max_obs_staleness_s": "0.1"},
        "masks": [{"mask_field_id": "cable_kp_valid", "semantics": "ONE_IS_VALID",
                   "applies_to": ["cable_kp"], "scope": "PER_STEP"}],
        "belief_inputs": [
            {"belief_field_id": "cable_kp", "producer_schema_hash": belief_schema_hash},
            {"belief_field_id": "cable_kp_valid", "producer_schema_hash": belief_schema_hash},
        ],
        "container_dtype": "FLOAT32",
    },
    "action": {
        "features": [
            feat("ee_delta_dual", "SEMANTIC_ACTION", 0, [2, 3], "FLOAT32", "m", "world",
                 tf={"scale": "0.005", "bias": "0"}, bounds={"lower": "-0.01", "upper": "0.01"}),
        ],
        "total_dim": 6, "control_mode": "DIFF_IK_EE_TARGET", "action_scale": None,
        "timing": {"action_rate_hz": "30", "hold": "ZERO_ORDER_HOLD"},
        "container_dtype": "FLOAT32",
    },
    # IDENTICAL carries NO hash — fixpoint removed
    "lineage_declaration": {
        "training_lineage": "DEMO_PLUS_RL",
        "bc_stage_binding": {"relation": "IDENTICAL", "demo_dataset_binding_hash": None,
                             "superseded_detail": None},
    },
}

# G-3: complement coverage — dual-arm width, >=2 frozenset, action_scale, EXPLICIT_SUPERSEDE,
# MIN_MAX, XYZW_UNIT, ZERO_IS_VALID, OLDEST_FIRST/ZERO_PAD/FEATURE_MAJOR, one-sided bounds.
G3 = {
    "binding_schema_version": "1.0",
    "obs": {
        "features": [
            feat("ee_quat_left", "SEMANTIC_OBS", 0, [4], "FLOAT32", "dimensionless", "world",
                 quat="XYZW_UNIT"),
            feat("z_cable_tension", "BELIEF", 4, [1], "FLOAT32", "N", "world",
                 norm={"scheme": "MIN_MAX", "stats_key": "tension_v1"}),
            feat("a_cable_kp", "BELIEF", 5, [4, 3], "FLOAT32", "m", "world"),
            feat("belief_invalid", "BELIEF", 17, [1], "BOOL", "dimensionless", "none"),
        ],
        "total_dim": 18,
        "history": {"depth": 2, "order": "OLDEST_FIRST", "padding": "ZERO_PAD", "layout": "FEATURE_MAJOR"},
        "timing": {"policy_rate_hz": "20", "obs_sampling_rate_hz": "60", "max_obs_staleness_s": "0.05"},
        # applies_to has 2 members inserted in NON-sorted order -> canonical form must sort them
        "masks": [{"mask_field_id": "belief_invalid", "semantics": "ZERO_IS_VALID",
                   "applies_to": sorted(["z_cable_tension", "a_cable_kp"]), "scope": "ACROSS_STACK"}],
        "belief_inputs": [
            {"belief_field_id": "a_cable_kp", "producer_schema_hash": belief_schema_hash},
            {"belief_field_id": "belief_invalid", "producer_schema_hash": belief_schema_hash},
            {"belief_field_id": "z_cable_tension", "producer_schema_hash": belief_schema_hash},
        ],
        "container_dtype": "FLOAT32",
    },
    "action": {
        "features": [
            # dual-arm 12-dim action width
            feat("ee_delta_both", "SEMANTIC_ACTION", 0, [2, 3], "FLOAT32", "m", "world",
                 bounds={"lower": "-0.01", "upper": "0.01"}),
            feat("ee_rot_delta_both", "SEMANTIC_ACTION", 6, [2, 3], "FLOAT32", "rad", "world",
                 bounds={"lower": "-0.05", "upper": "0.05"}),
            # one-sided bounds case
            feat("gripper_cmd_both", "SEMANTIC_ACTION", 12, [2], "FLOAT32", "dimensionless", "none",
                 bounds={"lower": "-1", "upper": None}),
        ],
        "total_dim": 14, "control_mode": "DIFF_IK_EE_TARGET",
        "action_scale": {"scale": "0.02", "bias": "0"},
        "timing": {"action_rate_hz": "20", "hold": "ZERO_ORDER_HOLD"},
        "container_dtype": "FLOAT32",
    },
    "lineage_declaration": {
        "training_lineage": "BC_THEN_RL",
        "bc_stage_binding": {"relation": "EXPLICIT_SUPERSEDE",
                             "demo_dataset_binding_hash": superseded_demo_hash,
                             "superseded_detail": "BC stage bound obs without belief tension; RL stage added z_cable_tension at offset 4 and re-indexed subsequent features."},
    },
}

for name, spec in [("G-1", G1), ("G-2", G2), ("G-3", G3)]:
    for side in ("obs", "action"):
        pos = 0
        for f in spec[side]["features"]:
            assert f["offset"] == pos, f"{name}/{side}/{f['field_id']}: offset {f['offset']} != {pos}"
            assert f["length"] == prod(f["shape"]), f"{name}/{side}/{f['field_id']}: length mismatch"
            if side == "action":
                assert f["source"] == "SEMANTIC_ACTION", f"{name}: action feature source must be SEMANTIC_ACTION"
                assert f["bounds"] is not None, f"{name}: action feature needs bounds"
            pos += f["length"]
        assert pos == spec[side]["total_dim"], f"{name}/{side}: coverage {pos} != total_dim"
    ld = spec["lineage_declaration"]
    bsb = ld["bc_stage_binding"]
    if ld["training_lineage"] in ("BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL"):
        assert bsb is not None, f"{name}: demo lineage requires bc_stage_binding"
        if bsb["relation"] == "IDENTICAL":
            assert bsb["demo_dataset_binding_hash"] is None, f"{name}: IDENTICAL must carry null hash"
        else:
            assert bsb["demo_dataset_binding_hash"] is not None and bsb["superseded_detail"], f"{name}: SUPERSEDE needs hash+detail"
    else:
        assert bsb is None, f"{name}: non-demo lineage must have null bc_stage_binding"

# schema conformance: every REQUIRED top-level member must be present (pN B2 - a reproducible
# hash proves reproducibility, not conformance; this loop is what makes the corpus self-checking)
REQ_OBS = {"features", "total_dim", "history", "timing", "masks", "belief_inputs", "container_dtype"}
REQ_ACT = {"features", "total_dim", "control_mode", "action_scale", "timing", "container_dtype"}
REQ_FEAT = {"field_id", "source", "offset", "length", "dtype", "shape", "unit", "frame",
            "flatten_order", "quaternion", "normalizer", "transform", "bounds"}
CAST_OK = {("FLOAT32", "FLOAT32"), ("BOOL", "FLOAT32"), ("INT32", "FLOAT32"),
           ("INT32", "INT32"), ("BOOL", "BOOL")}
NORM_STATS = {"MEAN_STD": {"mean", "std"}, "MIN_MAX": {"min", "max"}}
for name, spec in [("G-1", G1), ("G-2", G2), ("G-3", G3)]:
    assert set(spec) == {"binding_schema_version", "obs", "action", "lineage_declaration"}, name
    assert set(spec["obs"]) == REQ_OBS, f"{name}/obs members: {set(spec['obs']) ^ REQ_OBS}"
    assert set(spec["action"]) == REQ_ACT, f"{name}/action members: {set(spec['action']) ^ REQ_ACT}"
    for side in ("obs", "action"):
        cdt = spec[side]["container_dtype"]
        for f in spec[side]["features"]:
            assert set(f) == REQ_FEAT, f"{name}/{side}/{f['field_id']} members: {set(f) ^ REQ_FEAT}"
            assert (f["dtype"], cdt) in CAST_OK, f"{name}: cast {f['dtype']}->{cdt} not in v1.0 table"
            if f["normalizer"] is not None:
                assert set(f["normalizer"]) == {"scheme", "stats_key"}, name
                assert f["normalizer"]["scheme"] in NORM_STATS, name
    for m in spec["obs"]["masks"]:
        mf = [f for f in spec["obs"]["features"] if f["field_id"] == m["mask_field_id"]]
        assert mf and mf[0]["dtype"] == "BOOL", f"{name}: mask field must exist and be BOOL"
        assert m["mask_field_id"] not in m["applies_to"], f"{name}: mask self-reference"
        assert m["applies_to"] == sorted(m["applies_to"]), f"{name}: applies_to must be byte-ascending"

print("assertions: PASS (schema conformance incl. container_dtype + cast table + normalizer payload +"
      " mask dtype/self/sort, coverage arithmetic, action source+bounds, lineage/stage — 3 fixtures)")
print(f"belief_schema_hash   = {belief_schema_hash}")
print(f"superseded_demo_hash = {superseded_demo_hash}")
print(f"topology_ledger_hash = {topology_ledger_hash}")
for name, spec, fn in [("G-1", G1, "tensor_binding_golden_1.json"),
                       ("G-2", G2, "tensor_binding_golden_2.json"),
                       ("G-3", G3, "tensor_binding_golden_3.json")]:
    digest, nbytes = h(spec)
    p = OUT / fn
    p.write_bytes(wcj_bytes(spec))
    print(f"{name} H_WCJ = {digest}  ({nbytes} canonical bytes)  -> {p.name}")
# frozenset discrimination proof: sorted vs insertion order must differ for G-3's mask
import copy
g3_bad = copy.deepcopy(G3)
g3_bad["obs"]["masks"][0]["applies_to"] = ["z_cable_tension", "a_cable_kp"]  # insertion order
print(f"G-3 insertion-order variant = {h(g3_bad)[0]}  (MUST differ from G-3 -> frozenset sort is discriminated)")
