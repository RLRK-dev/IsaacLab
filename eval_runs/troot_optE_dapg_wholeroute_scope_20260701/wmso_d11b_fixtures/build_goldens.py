#!/usr/bin/env python3
"""D1.1-B golden fixtures — generator AND non-destructive verifier.

Usage:
  build_goldens.py <outdir>            regenerate fixtures into <outdir> (writes)
  build_goldens.py --verify <dir>      read banked fixtures, assert conformance, print sha256 (no writes)

v4 (cycle-2 folds):
- conformance asserted over EVERY declared composite type; v3 checked 5 of 14, so a member
  deleted from HistorySpec / MaskBinding / ActionTimingSpec regenerated silently — the B2
  defect verbatim (CC2-CH3 / CC3-CH1).
- --verify exists because a generator that rewrites the file it is meant to check destroys
  its own baseline (CC3-CH6).
- negative controls: every assertion class must be shown to fire (CC5-CH3).
- BOOL numeric-stage guard: a normalizer/transform on a BOOL feature silently defeats the
  mask that gates belief validity (CC4-C1 / CC2-CH5).
- G-4 added: INT32 semantic dtype, INT32 container, BOOL container — v3 exercised 2 of 5
  legal cast cells and one container_dtype value, so an implementation ignoring
  container_dtype reproduced every golden (CC3-CH2 / CC4-C10 / CC5-CH3).
- topology_ledger_hash removed (bound no fixture after the B5 fold — CC2/CC3/CC4/CC5 all).
"""
import copy
import hashlib
import re
import unicodedata
import json
import sys
from math import prod
from pathlib import Path

SCHEMA = {
    "TensorBindingSpec": ({"binding_schema_version", "obs", "action", "lineage_declaration"},
                          {"obs": "ObsBinding", "action": "ActionBinding",
                           "lineage_declaration": "LineageBindingDeclaration"}),
    "ObsBinding": ({"features", "total_dim", "history", "timing", "masks", "belief_inputs",
                    "container_dtype"},
                   {"features": ["FeatureBinding"], "history": "HistorySpec", "timing": "TimingSpec",
                    "masks": ["MaskBinding"], "belief_inputs": ["BeliefInputBinding"]}),
    "ActionBinding": ({"features", "total_dim", "control_mode", "action_scale", "timing",
                       "container_dtype"},
                      {"features": ["FeatureBinding"], "action_scale": "ValueTransform",
                       "timing": "ActionTimingSpec"}),
    "FeatureBinding": ({"field_id", "source", "offset", "length", "dtype", "shape", "unit", "frame",
                        "flatten_order", "quaternion", "normalizer", "transform", "bounds"},
                       {"normalizer": "NormalizerBinding", "transform": "ValueTransform",
                        "bounds": "BoundsSpec"}),
    "HistorySpec": ({"depth", "order", "layout", "padding"}, {}),
    "TimingSpec": ({"policy_rate_hz", "obs_sampling_rate_hz", "max_obs_staleness_s"}, {}),
    "ActionTimingSpec": ({"action_rate_hz", "hold"}, {}),
    "MaskBinding": ({"mask_field_id", "semantics", "applies_to", "scope"}, {}),
    "BeliefInputBinding": ({"belief_field_id", "producer_schema_hash"}, {}),
    "NormalizerBinding": ({"scheme", "stats_key"}, {}),
    "ValueTransform": ({"scale", "bias"}, {}),
    "BoundsSpec": ({"lower", "upper"}, {}),
    "LineageBindingDeclaration": ({"training_lineage", "bc_stage_binding"},
                                  {"bc_stage_binding": "BcStageBinding"}),
    "BcStageBinding": ({"relation", "demo_dataset_binding_hash", "superseded_detail"}, {}),
}
ENUMS = {
    "source": {"SEMANTIC_OBS", "SEMANTIC_ACTION", "BELIEF"},
    "flatten_order": {"ROW_MAJOR"},
    "order": {"OLDEST_FIRST", "NEWEST_FIRST"},
    "layout": {"STEP_MAJOR", "FEATURE_MAJOR"},
    "padding": {"ZERO_PAD", "REPEAT_OLDEST"},
    "semantics": {"ONE_IS_VALID", "ZERO_IS_VALID"},
    "scope": {"PER_STEP", "ACROSS_STACK"},
    "scheme": {"MEAN_STD", "MIN_MAX"},
    "quaternion": {"WXYZ_UNIT", "XYZW_UNIT"},
    "hold": {"ZERO_ORDER_HOLD", "LINEAR_INTERPOLATE"},
    "relation": {"IDENTICAL", "EXPLICIT_SUPERSEDE"},
    "dtype": {"FLOAT32", "INT32", "BOOL"},
    "container_dtype": {"FLOAT32", "INT32", "BOOL"},
    "control_mode": {"DIFF_IK_EE_TARGET", "SCRIPTED_SEQUENCE", "WAIT"},
    "training_lineage": {"RL_ONLY", "BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL", "NOT_APPLICABLE"},
}
KNOWN_VERSIONS = {"1.0"}
# frozen DESIGN sec.2 item 5 verbatim
CANON_DECIMAL = re.compile(r"\A(?:(0|-?[1-9][0-9]*)(\.[0-9]*[1-9])?|-0\.[0-9]*[1-9])\Z")
HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
# members typed CanonicalDecimal by the design; anything here must match the frozen regex
DECIMAL_MEMBERS = {"scale", "bias", "lower", "upper", "policy_rate_hz", "obs_sampling_rate_hz",
                   "max_obs_staleness_s", "action_rate_hz"}
IDENT_MEMBERS = {"field_id", "unit", "frame", "stats_key", "mask_field_id", "belief_field_id",
                 "binding_schema_version"}
HASH_MEMBERS = {"producer_schema_hash", "demo_dataset_binding_hash"}
# v5 (pN R1): INT32->FLOAT32 is FORBIDDEN in v1.0. float32 has a 24-bit significand, so
# 16777216 and 16777217 both round to 16777216.0 — the cast is not injective, which breaks the
# bijection the artifact exists to declare. v4 delegated reversibility to COMPATIBILITY_TEST,
# but that proof is required only at RECONSTRUCTED_COMPATIBLE (rank 2); CLOSED_LOOP (rank 3/4)
# certifies without it, so the delegation did not cover the grades that matter.
CAST_OK = {("FLOAT32", "FLOAT32"), ("BOOL", "FLOAT32"), ("INT32", "INT32"), ("BOOL", "BOOL")}
NORM_SCHEMES = {"MEAN_STD", "MIN_MAX"}


def check_type(obj, tname, path, errs):
    req, children = SCHEMA[tname]
    if not isinstance(obj, dict):
        errs.append(f"{path}: expected object for {tname}")
        return
    if set(obj) != req:
        errs.append(f"{path} [{tname}] member set differs: {set(obj) ^ req}")
        return
    for k, v in obj.items():
        if k in ENUMS and v is not None and v not in ENUMS[k]:
            errs.append(f"{path}.{k}: unknown enum member {v!r}")
        if k in DECIMAL_MEMBERS and v is not None:
            if not isinstance(v, str) or not CANON_DECIMAL.fullmatch(v):
                errs.append(f"{path}.{k}: not a CanonicalDecimal: {v!r}")
        if k in IDENT_MEMBERS and v is not None:
            if not isinstance(v, str) or not v or unicodedata.normalize("NFC", v) != v:
                errs.append(f"{path}.{k}: identifier must be non-empty NFC: {v!r}")
        if k in HASH_MEMBERS and v is not None and not HEX64.fullmatch(v):
            errs.append(f"{path}.{k}: not 64-hex: {v!r}")
        child = children.get(k)
        if child is None or v is None:
            continue
        if isinstance(child, list):
            for i, e in enumerate(v):
                check_type(e, child[0], f"{path}.{k}[{i}]", errs)
        else:
            check_type(v, child, f"{path}.{k}", errs)


def conformance(spec, name):
    errs = []
    check_type(spec, "TensorBindingSpec", name, errs)
    assert not errs, f"{name}: " + " | ".join(errs)
    assert spec["binding_schema_version"] in KNOWN_VERSIONS, f"{name}: unknown binding_schema_version"
    for side in ("obs", "action"):
        blk, pos, ids = spec[side], 0, set()
        assert blk["features"], f"{name}/{side}: empty features"
        cdt = blk["container_dtype"]
        for f in blk["features"]:
            assert f["offset"] == pos, f"{name}/{side}/{f['field_id']}: offset {f['offset']} != {pos}"
            assert f["length"] == prod(f["shape"]), f"{name}/{side}/{f['field_id']}: length != prod(shape)"
            assert type(f["offset"]) is int and type(f["length"]) is int, f"{name}: bool-as-int"
            assert f["field_id"] not in ids, f"{name}/{side}: duplicate field_id {f['field_id']}"
            ids.add(f["field_id"])
            assert (f["dtype"], cdt) in CAST_OK, f"{name}: cast {f['dtype']}->{cdt} not in v1.0 table"
            if f["dtype"] == "BOOL":
                assert f["normalizer"] is None and f["transform"] is None and f["bounds"] is None, \
                    f"{name}/{side}/{f['field_id']}: numeric stage on BOOL feature"
            if f["quaternion"] is not None:
                assert f["shape"][-1] == 4, f"{name}: quaternion on shape[-1] != 4"
            if f["normalizer"] is not None:
                assert f["normalizer"]["scheme"] in NORM_SCHEMES, f"{name}: unknown normalizer scheme"
            if f["bounds"] is not None:
                lo, hi = f["bounds"]["lower"], f["bounds"]["upper"]
                assert not (lo is None and hi is None), f"{name}: bounds both null"
            if side == "action":
                assert f["source"] == "SEMANTIC_ACTION", f"{name}: action source must be SEMANTIC_ACTION"
                assert f["bounds"] is not None or f["dtype"] == "BOOL", f"{name}: action feature needs bounds"
            else:
                assert f["source"] != "SEMANTIC_ACTION", f"{name}: obs side may not bind action source"
            pos += f["length"]
        assert pos == blk["total_dim"], f"{name}/{side}: coverage {pos} != total_dim"
    obs = spec["obs"]
    if obs["history"] is not None:
        assert type(obs["history"]["depth"]) is int and obs["history"]["depth"] >= 1, f"{name}: depth"
    fid = {f["field_id"] for f in obs["features"]}
    belief = {f["field_id"] for f in obs["features"] if f["source"] == "BELIEF"}
    bound = [b["belief_field_id"] for b in obs["belief_inputs"]]
    assert set(bound) == belief, f"{name}: belief coverage {set(bound) ^ belief}"
    assert len(bound) == len(set(bound)), f"{name}: duplicate belief_inputs entry"
    for m in obs["masks"]:
        mf = [f for f in obs["features"] if f["field_id"] == m["mask_field_id"]]
        assert mf and mf[0]["dtype"] == "BOOL", f"{name}: mask field must exist and be BOOL"
        assert m["mask_field_id"] not in m["applies_to"], f"{name}: mask self-reference"
        assert set(m["applies_to"]) <= fid, f"{name}: mask target absent"
        assert m["applies_to"] == sorted(m["applies_to"]), f"{name}: applies_to must be byte-ascending"
    ld = spec["lineage_declaration"]
    bsb = ld["bc_stage_binding"]
    if ld["training_lineage"] in ("BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL"):
        assert bsb is not None, f"{name}: demo lineage requires bc_stage_binding"
        if bsb["relation"] == "IDENTICAL":
            assert bsb["demo_dataset_binding_hash"] is None, f"{name}: IDENTICAL must carry null hash"
        else:
            assert bsb["demo_dataset_binding_hash"] and bsb["superseded_detail"], \
                f"{name}: EXPLICIT_SUPERSEDE needs hash + detail"
    else:
        assert bsb is None, f"{name}: non-demo lineage must have null bc_stage_binding"


def wcj_bytes(obj):
    def check(o, path="$"):
        if isinstance(o, dict):
            for k, v in o.items():
                assert isinstance(k, str) and k.isascii(), f"non-ASCII key at {path}: {k!r}"
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


belief_schema_hash = hashlib.sha256(b"WMSO-D11B-GOLDEN-BELIEF-SCHEMA-V1").hexdigest()
superseded_demo_hash = hashlib.sha256(b"WMSO-D11B-GOLDEN-SUPERSEDED-DEMO-BINDING-V1").hexdigest()


def feat(fid, src, off, shape, dtype, unit, frame, *, quat=None, norm=None, tf=None, bounds=None):
    return {"field_id": fid, "source": src, "offset": off, "length": prod(shape), "dtype": dtype,
            "shape": list(shape), "unit": unit, "frame": frame, "flatten_order": "ROW_MAJOR",
            "quaternion": quat, "normalizer": norm, "transform": tf, "bounds": bounds}


G1 = {
    "binding_schema_version": "1.0",
    "obs": {"features": [feat("ee_pos_right", "SEMANTIC_OBS", 0, [3], "FLOAT32", "m", "world"),
                         feat("gripper_width_right", "SEMANTIC_OBS", 3, [1], "FLOAT32", "m", "none")],
            "total_dim": 4, "history": None,
            "timing": {"policy_rate_hz": "30", "obs_sampling_rate_hz": "30", "max_obs_staleness_s": None},
            "masks": [], "belief_inputs": [], "container_dtype": "FLOAT32"},
    "action": {"features": [feat("ee_delta_right", "SEMANTIC_ACTION", 0, [3], "FLOAT32", "m", "world",
                                 tf={"scale": "0.01", "bias": "0"},
                                 bounds={"lower": "-0.02", "upper": "0.02"}),
                            feat("gripper_cmd_right", "SEMANTIC_ACTION", 3, [1], "FLOAT32",
                                 "dimensionless", "none", bounds={"lower": "-1", "upper": "1"})],
               "total_dim": 4, "control_mode": "DIFF_IK_EE_TARGET", "action_scale": None,
               "timing": {"action_rate_hz": "30", "hold": "ZERO_ORDER_HOLD"},
               "container_dtype": "FLOAT32"},
    "lineage_declaration": {"training_lineage": "RL_ONLY", "bc_stage_binding": None},
}

G2 = {
    "binding_schema_version": "1.0",
    "obs": {"features": [feat("ee_quat_right", "SEMANTIC_OBS", 0, [4], "FLOAT32", "dimensionless",
                              "world", quat="WXYZ_UNIT"),
                         feat("cable_kp", "BELIEF", 4, [2, 3], "FLOAT32", "m", "world",
                              norm={"scheme": "MEAN_STD", "stats_key": "cable_kp_norm_v1"}),
                         feat("cable_kp_valid", "BELIEF", 10, [1], "BOOL", "dimensionless", "none")],
            "total_dim": 11,
            "history": {"depth": 3, "order": "NEWEST_FIRST", "padding": "REPEAT_OLDEST",
                        "layout": "STEP_MAJOR"},
            "timing": {"policy_rate_hz": "30", "obs_sampling_rate_hz": "120",
                       "max_obs_staleness_s": "0.1"},
            "masks": [{"mask_field_id": "cable_kp_valid", "semantics": "ONE_IS_VALID",
                       "applies_to": ["cable_kp"], "scope": "PER_STEP"}],
            "belief_inputs": [{"belief_field_id": "cable_kp", "producer_schema_hash": belief_schema_hash},
                              {"belief_field_id": "cable_kp_valid",
                               "producer_schema_hash": belief_schema_hash}],
            "container_dtype": "FLOAT32"},
    "action": {"features": [feat("ee_delta_dual", "SEMANTIC_ACTION", 0, [2, 3], "FLOAT32", "m", "world",
                                 tf={"scale": "0.005", "bias": "0"},
                                 bounds={"lower": "-0.01", "upper": "0.01"})],
               "total_dim": 6, "control_mode": "DIFF_IK_EE_TARGET", "action_scale": None,
               "timing": {"action_rate_hz": "30", "hold": "ZERO_ORDER_HOLD"},
               "container_dtype": "FLOAT32"},
    "lineage_declaration": {"training_lineage": "DEMO_PLUS_RL",
                            "bc_stage_binding": {"relation": "IDENTICAL",
                                                 "demo_dataset_binding_hash": None,
                                                 "superseded_detail": None}},
}

G3 = {
    "binding_schema_version": "1.0",
    "obs": {"features": [feat("ee_quat_left", "SEMANTIC_OBS", 0, [4], "FLOAT32", "dimensionless",
                              "world", quat="XYZW_UNIT"),
                         feat("z_cable_tension", "BELIEF", 4, [1], "FLOAT32", "N", "world",
                              norm={"scheme": "MIN_MAX", "stats_key": "tension_v1"}),
                         feat("a_cable_kp", "BELIEF", 5, [4, 3], "FLOAT32", "m", "world"),
                         feat("belief_invalid", "BELIEF", 17, [1], "BOOL", "dimensionless", "none")],
            "total_dim": 18,
            "history": {"depth": 2, "order": "OLDEST_FIRST", "padding": "ZERO_PAD",
                        "layout": "FEATURE_MAJOR"},
            "timing": {"policy_rate_hz": "20", "obs_sampling_rate_hz": "60",
                       "max_obs_staleness_s": "0.05"},
            "masks": [{"mask_field_id": "belief_invalid", "semantics": "ZERO_IS_VALID",
                       "applies_to": sorted(["z_cable_tension", "a_cable_kp"]),
                       "scope": "ACROSS_STACK"}],
            "belief_inputs": [{"belief_field_id": "a_cable_kp", "producer_schema_hash": belief_schema_hash},
                              {"belief_field_id": "belief_invalid",
                               "producer_schema_hash": belief_schema_hash},
                              {"belief_field_id": "z_cable_tension",
                               "producer_schema_hash": belief_schema_hash}],
            "container_dtype": "FLOAT32"},
    "action": {"features": [feat("ee_delta_both", "SEMANTIC_ACTION", 0, [2, 3], "FLOAT32", "m", "world",
                                 bounds={"lower": "-0.01", "upper": "0.01"}),
                            feat("ee_rot_delta_both", "SEMANTIC_ACTION", 6, [2, 3], "FLOAT32", "rad",
                                 "world", bounds={"lower": "-0.05", "upper": "0.05"}),
                            feat("gripper_cmd_both", "SEMANTIC_ACTION", 12, [2], "FLOAT32",
                                 "dimensionless", "none", bounds={"lower": "-1", "upper": None})],
               "total_dim": 14, "control_mode": "DIFF_IK_EE_TARGET",
               "action_scale": {"scale": "0.02", "bias": "0"},
               "timing": {"action_rate_hz": "20", "hold": "ZERO_ORDER_HOLD"},
               "container_dtype": "FLOAT32"},
    "lineage_declaration": {"training_lineage": "BC_THEN_RL",
                            "bc_stage_binding": {"relation": "EXPLICIT_SUPERSEDE",
                                                 "demo_dataset_binding_hash": superseded_demo_hash,
                                                 "superseded_detail": "BC stage bound obs without belief tension; RL stage added z_cable_tension at offset 4 and re-indexed subsequent features."}},
}

G4 = {
    "binding_schema_version": "1.0",
    "obs": {"features": [feat("chain_topology_class", "BELIEF", 0, [1], "INT32", "dimensionless", "none"),
                         feat("clip_index", "SEMANTIC_OBS", 1, [1], "INT32", "dimensionless", "none")],
            "total_dim": 2, "history": None,
            "timing": {"policy_rate_hz": "10", "obs_sampling_rate_hz": "10",
                       "max_obs_staleness_s": None},
            "masks": [],
            "belief_inputs": [{"belief_field_id": "chain_topology_class",
                               "producer_schema_hash": belief_schema_hash}],
            "container_dtype": "INT32"},
    "action": {"features": [feat("gripper_close_both", "SEMANTIC_ACTION", 0, [2], "BOOL",
                                 "dimensionless", "none")],
               "total_dim": 2, "control_mode": "DIFF_IK_EE_TARGET", "action_scale": None,
               "timing": {"action_rate_hz": "10", "hold": "ZERO_ORDER_HOLD"},
               "container_dtype": "BOOL"},
    "lineage_declaration": {"training_lineage": "NOT_APPLICABLE", "bc_stage_binding": None},
}

FIXTURES = [("G-1", G1, "tensor_binding_golden_1.json"), ("G-2", G2, "tensor_binding_golden_2.json"),
            ("G-3", G3, "tensor_binding_golden_3.json"), ("G-4", G4, "tensor_binding_golden_4.json")]

NEGATIVE_CONTROLS = [
    ("container_dtype deleted", lambda s: s["obs"].pop("container_dtype")),
    ("history.layout deleted", lambda s: s["obs"]["history"].pop("layout")),
    ("mask.scope deleted", lambda s: s["obs"]["masks"][0].pop("scope")),
    ("action.timing.hold deleted", lambda s: s["action"]["timing"].pop("hold")),
    ("belief producer_schema_hash deleted", lambda s: s["obs"]["belief_inputs"][0].pop("producer_schema_hash")),
    ("unknown enum member", lambda s: s["obs"]["history"].__setitem__("order", "RANDOM")),
    ("unknown extra field", lambda s: s["obs"].__setitem__("bogus", 1)),
    ("unknown schema version", lambda s: s.__setitem__("binding_schema_version", "9.9")),
    ("normalizer on BOOL feature", lambda s: s["obs"]["features"][2].__setitem__(
        "normalizer", {"scheme": "MEAN_STD", "stats_key": "x"})),
    ("belief entry dropped", lambda s: s["obs"]["belief_inputs"].pop()),
    ("belief entry duplicated", lambda s: s["obs"]["belief_inputs"].append(
        dict(s["obs"]["belief_inputs"][0]))),
    ("forbidden cast", lambda s: s["obs"].__setitem__("container_dtype", "INT32")),
    ("mask applies_to unsorted", lambda s: s["obs"]["masks"][0].__setitem__(
        "applies_to", ["cable_kp_valid_x", "cable_kp"])),
    ("IDENTICAL carries a hash", lambda s: s["lineage_declaration"]["bc_stage_binding"].__setitem__(
        "demo_dataset_binding_hash", "0" * 64)),
    ("coverage arithmetic broken", lambda s: s["obs"].__setitem__("total_dim", 12)),
    ("bool-as-int", lambda s: s["obs"]["features"][0].__setitem__("offset", False)),
    ("Infinity as CanonicalDecimal", lambda s: s["obs"]["timing"].__setitem__("policy_rate_hz", "Infinity")),
    ("NaN as CanonicalDecimal", lambda s: s["action"]["features"][0]["transform"].__setitem__("scale", "NaN")),
    ("non-normalized decimal 1.10", lambda s: s["obs"]["timing"].__setitem__("policy_rate_hz", "1.10")),
    ("leading-zero decimal 01", lambda s: s["obs"]["timing"].__setitem__("policy_rate_hz", "01")),
    ("exponent notation 1e3", lambda s: s["obs"]["timing"].__setitem__("policy_rate_hz", "1e3")),
    ("non-NFC identifier", lambda s: s["obs"]["features"][0].__setitem__("field_id", "e\u0301e_quat")),
    ("malformed producer hash", lambda s: s["obs"]["belief_inputs"][0].__setitem__("producer_schema_hash", "zz")),
    ("INT32->FLOAT32 now forbidden", lambda s: (s["obs"]["features"][1].__setitem__("dtype", "INT32"),
                                                s["obs"]["features"][1].__setitem__("normalizer", None))),
]


def main():
    args = sys.argv[1:]
    verify = bool(args) and args[0] == "--verify"
    if verify and len(args) < 2:
        sys.exit("--verify requires a directory")
    target = Path(args[1]) if verify else Path(args[0] if args else ".")

    if verify:
        print(f"VERIFY mode (no writes) — {target}")
        for name, _, fn in FIXTURES:
            raw = (target / fn).read_bytes()
            data = json.loads(raw)
            conformance(data, name)
            assert raw == wcj_bytes(data), f"{name}: banked bytes are not canonical WCJ"
            print(f"{name} conformance PASS  sha256={hashlib.sha256(raw).hexdigest()}  bytes={len(raw)}")
        return

    for name, spec, _ in FIXTURES:
        conformance(spec, name)
    print("conformance: PASS over all 14 declared types — member-set equality both directions, enum "
          "allowlists, known version, cast table, BOOL numeric-stage guard, mask dtype/self/target/"
          "sort, belief coverage+duplicate, coverage arithmetic, bool-as-int, CanonicalDecimal/NFC/64-hex, "
          "lineage/stage (4 fixtures)")
    print(f"belief_schema_hash   = {belief_schema_hash}")
    print(f"superseded_demo_hash = {superseded_demo_hash}")
    for name, spec, fn in FIXTURES:
        b = wcj_bytes(spec)
        (target / fn).write_bytes(b)
        print(f"{name} H_WCJ = {hashlib.sha256(b).hexdigest()}  ({len(b)} canonical bytes)  -> {fn}")

    bad = copy.deepcopy(G3)
    bad["obs"]["masks"][0]["applies_to"] = ["z_cable_tension", "a_cable_kp"]
    print(f"G-3 insertion-order variant = {hashlib.sha256(wcj_bytes(bad)).hexdigest()}  (MUST differ from G-3)")

    fired = []
    for label, mut in NEGATIVE_CONTROLS:
        t = copy.deepcopy(G2)
        try:
            mut(t)
            conformance(t, "NEG")
            fired.append(f"DID-NOT-FIRE: {label}")
        except AssertionError:
            pass
        except (KeyError, IndexError):
            fired.append(f"MALFORMED-CONTROL: {label}")
    print(f"negative controls: {len(NEGATIVE_CONTROLS) - len(fired)}/{len(NEGATIVE_CONTROLS)} fired"
          + ("" if not fired else " — " + "; ".join(fired)))
    assert not fired, "a declared assertion did not fire: " + "; ".join(fired)


main()
