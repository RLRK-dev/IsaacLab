#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Golden vector builder / verifier for WMSO D1.1-C DESIGN v2 (carry record).

Scope note (design v2 s0): this builds the CARRY RECORD defined by v2 s2 (U-5 stage
binding) and v2 s3 (substrate labelling) ONLY. It is deliberately NOT the full
artifact manifest type -- prereg IN-1 stays out of v2.

Dependencies: stdlib only, Python >= 3.8. No dataclasses, no PEP-604 annotations,
so the module imports cleanly on the declared floor.

Fail-closed usage (registered in design v2 s7):

    env_isaaclab/bin/python .../wmso_d11c_fixtures/build_goldens.py --verify <dir>

AGENTS.md:68 verbatim authorises calling ``env_isaaclab/bin/python`` directly
because ``./isaaclab.sh -p`` "can mask non-zero Python exits". Any interpreter
works (stdlib only); the wrapper must not be used.
"""

import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

# --------------------------------------------------------------------------------------
# frozen vocabulary (referenced, never redefined here)
# --------------------------------------------------------------------------------------

TRAINING_LINEAGES = ("RL_ONLY", "BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL", "NOT_APPLICABLE")
DEMO_LINEAGES = ("BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL")
STAGE_RELATIONS = ("IDENTICAL", "EXPLICIT_SUPERSEDE")

SUBSTRATE_RE = re.compile(r"\A[A-Za-z0-9_.:-]{1,64}\Z")
HEX64_RE = re.compile(r"\A[0-9a-f]{64}\Z")

RECORD_KEYS = ("dataset_substrate_ids", "stage_bindings", "substrate_id", "training_lineage")
STAGE_KEYS = ("bc_stage_tensor_binding_hash", "execution_stage_tensor_binding_hash")

# --------------------------------------------------------------------------------------
# WMSO Canonical JSON (frozen contracts_v2 s2) -- inherited subset, no new rules
# --------------------------------------------------------------------------------------


class WcjError(ValueError):
    """Raised when a value cannot be expressed under the inherited WCJ rules."""


def _wcj_scalar(value):
    if value is None:
        return "null"
    if type(value) is bool:  # B-declared (2): bool is not an int, and no bool fields exist here
        raise WcjError("bool is not encodable: {!r}".format(value))
    if isinstance(value, float):  # frozen s2: float type rejected
        raise WcjError("float is not encodable: {!r}".format(value))
    if isinstance(value, int):
        if abs(value) > 2**53 - 1:
            raise WcjError("int out of range: {!r}".format(value))
        return str(value)
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise WcjError("string is not NFC: {!r}".format(value))
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise WcjError("lone surrogate: {!r}".format(value))
        return json.dumps(value, ensure_ascii=False)
    raise WcjError("unsupported type: {!r}".format(type(value)))


def wcj_text(value):
    """Serialize to canonical text: object keys sorted by UTF-16-BE bytes, tight separators."""
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{" + ",".join(_wcj_scalar(k) + ":" + wcj_text(v) for k, v in items) + "}"
    if isinstance(value, (list, tuple)):  # B-declared (3): tuple -> array
        return "[" + ",".join(wcj_text(v) for v in value) + "]"
    return _wcj_scalar(value)


def wcj_bytes(value):
    return wcj_text(value).encode("utf-8")


def record_hash(record):
    return hashlib.sha256(wcj_bytes(record)).hexdigest()


# --------------------------------------------------------------------------------------
# validation -- design v2 s2 (U-5) + s3 (substrate). Returns the fired error codes.
# --------------------------------------------------------------------------------------


def _substrate_ok(value):
    return isinstance(value, str) and SUBSTRATE_RE.match(value) is not None and unicodedata.normalize("NFC", value) == value


def validate(record):
    """Return the list of fired error codes, in declaration order. Empty list = conformant."""
    errors = []

    if not isinstance(record, dict) or tuple(sorted(record)) != RECORD_KEYS:
        return ["E_RECORD_SHAPE"]  # strict decoder territory (frozen s5C): unknown/missing field

    # ---- v2 s3: substrate ----------------------------------------------------------
    substrate = record["substrate_id"]
    if not isinstance(substrate, str) or substrate == "":
        errors.append("E_MANIFEST_SUBSTRATE_ABSENT")
    elif not _substrate_ok(substrate):
        errors.append("E_MANIFEST_SUBSTRATE_MALFORMED")

    ids = record["dataset_substrate_ids"]
    if not isinstance(ids, (list, tuple)):
        errors.append("E_MANIFEST_SUBSTRATE_POOLED")
    elif len(ids) == 0:
        # unlabelled data = silently pooled (v2 s3 S-3)
        errors.append("E_MANIFEST_SUBSTRATE_POOLED")
    else:
        if any(not _substrate_ok(x) for x in ids):
            errors.append("E_MANIFEST_SUBSTRATE_MALFORMED")
        encoded = [x.encode("utf-8") for x in ids if isinstance(x, str)]
        if encoded != sorted(encoded) or len(set(encoded)) != len(encoded):
            # v2 s4: collections are canonicalised sets (bytes ascending, no duplicates)
            errors.append("E_MANIFEST_SUBSTRATE_POOLED")

    # ---- v2 s2: stage bindings ------------------------------------------------------
    lineage = record["training_lineage"]
    if lineage not in TRAINING_LINEAGES:
        errors.append("E_RECORD_SHAPE")
        return errors

    stages = record["stage_bindings"]
    if not isinstance(stages, dict) or tuple(sorted(stages)) != STAGE_KEYS:
        errors.append("E_RECORD_SHAPE")
        return errors

    execution = stages["execution_stage_tensor_binding_hash"]
    bc = stages["bc_stage_tensor_binding_hash"]

    def _hex_or_none(v):
        return v is None or (isinstance(v, str) and HEX64_RE.match(v) is not None)

    if not _hex_or_none(execution) or not _hex_or_none(bc):
        errors.append("E_RECORD_SHAPE")
        return errors

    if lineage == "NOT_APPLICABLE":
        if execution is not None or bc is not None:
            errors.append("E_MANIFEST_STAGE_BINDING_PRESENT")
    elif lineage == "RL_ONLY":
        if execution is None:
            errors.append("E_MANIFEST_STAGE_BINDING_MISSING")
        if bc is not None:
            errors.append("E_MANIFEST_STAGE_BINDING_PRESENT")
    else:  # demo lineages
        if execution is None or bc is None:
            errors.append("E_MANIFEST_STAGE_BINDING_MISSING")

    return errors


def check_against_declaration(record, relation, superseded_binding_hash):
    """Cross-artifact leg (v2 s2): compare the record against the frozen LineageBindingDeclaration.

    ``relation`` / ``superseded_binding_hash`` come from the frozen TensorBindingSpec
    (v13 s1.5). Returns the fired error codes.
    """
    if relation not in STAGE_RELATIONS:
        return ["E_RECORD_SHAPE"]
    stages = record["stage_bindings"]
    execution = stages["execution_stage_tensor_binding_hash"]
    bc = stages["bc_stage_tensor_binding_hash"]
    if relation == "IDENTICAL":
        if execution is None or bc is None or execution != bc:
            return ["E_MANIFEST_STAGE_BINDING_CONFLICT"]
        return []
    if bc is None or bc != superseded_binding_hash:
        return ["E_MANIFEST_STAGE_BINDING_CONFLICT"]
    return []


# --------------------------------------------------------------------------------------
# goldens
# --------------------------------------------------------------------------------------

TB_A = "a" * 64
TB_B = "b" * 64

GOLDENS = {
    # M-A: no training stage at all (SCRIPTED / WAIT side), single substrate.
    "carry_record_golden_A.json": {
        "dataset_substrate_ids": ["kinematic_pin_2026_07"],
        "stage_bindings": {
            "bc_stage_tensor_binding_hash": None,
            "execution_stage_tensor_binding_hash": None,
        },
        "substrate_id": "kinematic_pin_2026_07",
        "training_lineage": "NOT_APPLICABLE",
    },
    # M-B: demo lineage with IDENTICAL relation, and a MIXED dataset label set.
    "carry_record_golden_B.json": {
        "dataset_substrate_ids": ["kinematic_pin_2026_07", "physics_faithful_2026_07"],
        "stage_bindings": {
            "bc_stage_tensor_binding_hash": TB_A,
            "execution_stage_tensor_binding_hash": TB_A,
        },
        "substrate_id": "physics_faithful_2026_07",
        "training_lineage": "DEMO_PLUS_RL",
    },
}


# --------------------------------------------------------------------------------------
# negative controls -- each mutates an in-memory deepcopy only (non-destructive)
# --------------------------------------------------------------------------------------


def _mutate(base, path, value):
    record = copy.deepcopy(base)
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return record


def negative_controls():
    """Return (label, record, expected_code) triples. Every declared predicate gets one."""
    a = GOLDENS["carry_record_golden_A.json"]
    b = GOLDENS["carry_record_golden_B.json"]
    cases = [
        ("substrate absent", _mutate(b, ["substrate_id"], ""), "E_MANIFEST_SUBSTRATE_ABSENT"),
        ("substrate malformed", _mutate(b, ["substrate_id"], "bad substrate!"), "E_MANIFEST_SUBSTRATE_MALFORMED"),
        ("substrate too long", _mutate(b, ["substrate_id"], "x" * 65), "E_MANIFEST_SUBSTRATE_MALFORMED"),
        ("dataset ids empty", _mutate(b, ["dataset_substrate_ids"], []), "E_MANIFEST_SUBSTRATE_POOLED"),
        ("dataset ids unsorted", _mutate(b, ["dataset_substrate_ids"], ["z_sub", "a_sub"]), "E_MANIFEST_SUBSTRATE_POOLED"),
        ("dataset ids duplicated", _mutate(b, ["dataset_substrate_ids"], ["a_sub", "a_sub"]), "E_MANIFEST_SUBSTRATE_POOLED"),
        ("dataset id malformed", _mutate(b, ["dataset_substrate_ids"], ["ok", "b a d"]), "E_MANIFEST_SUBSTRATE_MALFORMED"),
        (
            "NOT_APPLICABLE with execution hash",
            _mutate(a, ["stage_bindings", "execution_stage_tensor_binding_hash"], TB_A),
            "E_MANIFEST_STAGE_BINDING_PRESENT",
        ),
        (
            "NOT_APPLICABLE with bc hash",
            _mutate(a, ["stage_bindings", "bc_stage_tensor_binding_hash"], TB_A),
            "E_MANIFEST_STAGE_BINDING_PRESENT",
        ),
        (
            "RL_ONLY missing execution",
            {
                "dataset_substrate_ids": ["s"],
                "stage_bindings": {"bc_stage_tensor_binding_hash": None, "execution_stage_tensor_binding_hash": None},
                "substrate_id": "s",
                "training_lineage": "RL_ONLY",
            },
            "E_MANIFEST_STAGE_BINDING_MISSING",
        ),
        (
            "RL_ONLY carries bc",
            {
                "dataset_substrate_ids": ["s"],
                "stage_bindings": {"bc_stage_tensor_binding_hash": TB_A, "execution_stage_tensor_binding_hash": TB_A},
                "substrate_id": "s",
                "training_lineage": "RL_ONLY",
            },
            "E_MANIFEST_STAGE_BINDING_PRESENT",
        ),
        (
            "demo lineage missing bc",
            _mutate(b, ["stage_bindings", "bc_stage_tensor_binding_hash"], None),
            "E_MANIFEST_STAGE_BINDING_MISSING",
        ),
        ("unknown lineage", _mutate(b, ["training_lineage"], "PPO_ONLY"), "E_RECORD_SHAPE"),
        ("non-hex binding", _mutate(b, ["stage_bindings", "execution_stage_tensor_binding_hash"], "AB" * 32), "E_RECORD_SHAPE"),
    ]
    return cases


def cross_artifact_controls():
    """Cross-artifact leg negative controls (v2 s2 declaration comparison)."""
    b = GOLDENS["carry_record_golden_B.json"]
    return [
        ("IDENTICAL but stages differ", _mutate(b, ["stage_bindings", "bc_stage_tensor_binding_hash"], TB_B), "IDENTICAL", None),
        ("EXPLICIT_SUPERSEDE mismatch", b, "EXPLICIT_SUPERSEDE", TB_B),
    ]


def positive_controls():
    """Encoder-level rejections that must raise WcjError (frozen s2 inheritance)."""
    b = GOLDENS["carry_record_golden_B.json"]
    return [
        ("float rejected", _mutate(b, ["substrate_id"], 1.5)),
        ("bool rejected", _mutate(b, ["substrate_id"], True)),
        ("non-NFC rejected", _mutate(b, ["substrate_id"], "Å")),
    ]


# --------------------------------------------------------------------------------------
# drivers
# --------------------------------------------------------------------------------------


def run_controls():
    """Run every control. Returns (fired, total, failures)."""
    fired = 0
    failures = []
    cases = negative_controls()
    for label, record, expected in cases:
        codes = validate(record)
        if expected in codes:
            fired += 1
        else:
            failures.append("negative control did not fire: {} (expected {}, got {})".format(label, expected, codes))
    for label, record, relation, superseded in cross_artifact_controls():
        codes = check_against_declaration(record, relation, superseded)
        if "E_MANIFEST_STAGE_BINDING_CONFLICT" in codes:
            fired += 1
        else:
            failures.append("cross-artifact control did not fire: {} (got {})".format(label, codes))
    for label, record in positive_controls():
        try:
            wcj_bytes(record)
        except WcjError:
            fired += 1
        else:
            failures.append("encoder control did not reject: {}".format(label))
    total = len(cases) + len(cross_artifact_controls()) + len(positive_controls())
    return fired, total, failures


def emit(target_dir):
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    for name, record in GOLDENS.items():
        (target / name).write_bytes(wcj_bytes(record))
        print("wrote {}  sha256={}  bytes={}".format(name, record_hash(record), len(wcj_bytes(record))))
    fired, total, failures = run_controls()
    print("negative controls: {}/{} fired".format(fired, total))
    for line in failures:
        print("FAIL: " + line)
    return 1 if failures else 0


def verify(target_dir):
    """Non-destructive: recompute every golden and run every control. Never writes."""
    target = Path(target_dir)
    failures = []
    for name, record in GOLDENS.items():
        path = target / name
        if not path.is_file():
            failures.append("missing fixture: {}".format(name))
            continue
        on_disk = path.read_bytes()
        expected = wcj_bytes(record)
        if on_disk != expected:
            failures.append("non-canonical or drifted bytes: {} (E_MANIFEST_NONCANONICAL_BYTES)".format(name))
            continue
        codes = validate(record)
        if codes:
            failures.append("golden is not conformant: {} -> {}".format(name, codes))
            continue
        print("PASS {}  sha256={}  bytes={}".format(name, hashlib.sha256(on_disk).hexdigest(), len(on_disk)))
    fired, total, control_failures = run_controls()
    failures.extend(control_failures)
    print("negative controls: {}/{} fired".format(fired, total))
    if failures:
        for line in failures:
            print("FAIL: " + line)
        return 1
    print("conformance: {}/{} PASS".format(len(GOLDENS), len(GOLDENS)))
    return 0


def main(argv):
    if len(argv) == 3 and argv[1] == "--verify":
        return verify(argv[2])
    if len(argv) == 2:
        return emit(argv[1])
    print("usage: build_goldens.py <out_dir> | --verify <dir>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
