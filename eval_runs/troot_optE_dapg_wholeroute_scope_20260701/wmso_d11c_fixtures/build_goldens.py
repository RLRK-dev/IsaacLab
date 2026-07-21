#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Golden vector builder / verifier for WMSO D1.1-C DESIGN v2.2 (carry record).

Scope (design v2.2 s0): builds ONLY the carry record defined by s2 (U-5 stage binding)
and s3 (substrate labelling). It is NOT the full artifact manifest -- prereg IN-1 is out.

Dependencies: stdlib only. No dataclasses, no PEP-604 annotations, so the module parses
and imports on the declared floor (3.8).

Registered fail-closed command (design v2.2 s7) -- call the interpreter DIRECTLY:

    env_isaaclab/bin/python .../wmso_d11c_fixtures/build_goldens.py --verify <dir>

Never verify through ``./isaaclab.sh -p``: measured C-side, the wrapper returns rc=0 on a
corrupted fixture while the script itself returns 1 (root cause: the -p handler discards
the child's returncode). AGENTS.md documents this hazard, but NOTE: at the pinned commit
that text lives only in an UNCOMMITTED working-tree edit of AGENTS.md -- it is cited here
as read-on-disk, not as committed content (cycle-2 F-7).

Cycle-2 fixes folded here: F-3 (verify now parses and re-canonicalises, and rejects
unexpected files), F-4 (argv guard: no fallthrough that writes), F-6 (lineage coherence),
F-8 (NOT_APPLICABLE no longer false-rejects a KNOWN execution binding), F-12/F-15
(E_MANIFEST_NONCANONICAL_BYTES now has controls), F-2 (encoder vectors with HAND-DERIVED
expected bytes, so a defect in this encoder cannot certify itself).
"""

import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True  # cycle-2: keep __pycache__ out of the pinned fixture dir

# --------------------------------------------------------------------------------------
# frozen vocabulary (referenced, never redefined)
# --------------------------------------------------------------------------------------

TRAINING_LINEAGES = ("RL_ONLY", "BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL", "NOT_APPLICABLE")
DEMO_LINEAGES = ("BC_ONLY", "BC_THEN_RL", "DEMO_PLUS_RL")  # frozen v13 :166
STAGE_RELATIONS = ("IDENTICAL", "EXPLICIT_SUPERSEDE")

SUBSTRATE_RE = re.compile(r"\A[A-Za-z0-9_.:-]{1,64}\Z")
HEX64_RE = re.compile(r"\A[0-9a-f]{64}\Z")

RECORD_KEYS = ("dataset_substrate_ids", "stage_bindings", "substrate_id", "training_lineage")
STAGE_KEYS = ("bc_stage_tensor_binding_hash", "execution_stage_tensor_binding_hash")

# --------------------------------------------------------------------------------------
# WMSO Canonical JSON (frozen contracts_v2 s2) -- inherited subset
# --------------------------------------------------------------------------------------


class WcjError(ValueError):
    """Raised when a value cannot be expressed under the inherited WCJ rules."""


def _wcj_scalar(value):
    if value is None:
        return "null"
    if type(value) is bool:
        raise WcjError("bool is not encodable: {!r}".format(value))
    if isinstance(value, float):
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
    """Canonical text. Object keys sorted by UTF-16-BE bytes; arrays keep declared order.

    NOTE (design v2.2 s4): this serializer does NOT reorder array elements. Set-typed
    fields are held to bytes-ascending order by ``validate()``, i.e. by REJECTION, not by
    normalisation -- a producer that hashes without validating can still emit a different
    byte string for the same set. That residue is declared open (s8 open-10).
    """
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{" + ",".join(_wcj_scalar(k) + ":" + wcj_text(v) for k, v in items) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(wcj_text(v) for v in value) + "]"
    return _wcj_scalar(value)


def wcj_bytes(value):
    return wcj_text(value).encode("utf-8")


def record_hash(record):
    return hashlib.sha256(wcj_bytes(record)).hexdigest()


# --------------------------------------------------------------------------------------
# encoder vectors -- expected bytes DERIVED BY HAND, not by this encoder (cycle-2 F-2)
# --------------------------------------------------------------------------------------

# U+FF01 encodes UTF-16-BE as FF 01 and UTF-8 as EF BC 81.
# U+1F600 encodes UTF-16-BE as D8 3D DE 00 (surrogate pair) and UTF-8 as F0 9F 98 80.
# => UTF-16-BE order puts U+1F600 FIRST; UTF-8/codepoint order puts U+FF01 first.
# A serializer that sorts by anything other than UTF-16-BE bytes fails this vector.
ENCODER_VECTORS = [
    ("utf16 key order differs from utf8", {"！": 1, "\U0001f600": 2}, '{"\U0001f600":2,"！":1}'),
    ("non-ascii is not escaped", {"k": "é"}, '{"k":"é"}'),
    ("int upper bound accepted", {"n": 2**53 - 1}, '{"n":9007199254740991}'),
    ("nested array keeps declared order", {"a": [3, 1, 2]}, '{"a":[3,1,2]}'),
    ("null is explicit", {"a": None}, '{"a":null}'),
]

ENCODER_REJECTS = [
    ("int above 2**53-1", {"n": 2**53}),
    ("float", {"n": 1.5}),
    ("bool", {"n": True}),
    ("lone surrogate", {"k": "\ud800"}),
    ("non-NFC string", {"k": "Å"}),
]


# --------------------------------------------------------------------------------------
# validation -- design v2.2 s2 (U-5) + s3 (substrate)
# --------------------------------------------------------------------------------------


def _substrate_ok(value):
    return isinstance(value, str) and SUBSTRATE_RE.match(value) is not None


def validate(record):
    """Return the fired error codes in declaration order. Empty list = conformant."""
    if not isinstance(record, dict) or tuple(sorted(record)) != RECORD_KEYS:
        return ["E_RECORD_SHAPE"]

    errors = []

    substrate = record["substrate_id"]
    if not isinstance(substrate, str) or substrate == "":
        errors.append("E_MANIFEST_SUBSTRATE_ABSENT")
    elif not _substrate_ok(substrate):
        errors.append("E_MANIFEST_SUBSTRATE_MALFORMED")

    ids = record["dataset_substrate_ids"]
    if not isinstance(ids, (list, tuple)):
        errors.append("E_RECORD_SHAPE")  # cycle-2: a type fault is not a pooling finding
    elif len(ids) == 0:
        errors.append("E_MANIFEST_SUBSTRATE_POOLED")
    elif any(not _substrate_ok(x) for x in ids):
        errors.append("E_MANIFEST_SUBSTRATE_MALFORMED")
    else:
        encoded = [x.encode("utf-8") for x in ids]
        if encoded != sorted(encoded) or len(set(encoded)) != len(encoded):
            errors.append("E_MANIFEST_SUBSTRATE_POOLED")

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
    for value in (execution, bc):
        if not (value is None or (isinstance(value, str) and HEX64_RE.match(value))):
            errors.append("E_RECORD_SHAPE")
            return errors

    # frozen v13 :166 constrains the BC stage only. The execution stage mirrors the bundle's
    # tensor_binding slot, which a SCRIPTED/WAIT skill may legitimately hold as KNOWN, so
    # NOT_APPLICABLE does NOT force it to null (cycle-2 F-8).
    if lineage in DEMO_LINEAGES:
        if execution is None or bc is None:
            errors.append("E_MANIFEST_STAGE_BINDING_MISSING")
    else:  # RL_ONLY, NOT_APPLICABLE
        if bc is not None:
            errors.append("E_MANIFEST_STAGE_BINDING_PRESENT")
        if lineage == "RL_ONLY" and execution is None:
            errors.append("E_MANIFEST_STAGE_BINDING_MISSING")

    return errors


def check_against_declaration(record, declaration):
    """Cross-artifact leg (design v2.2 s2) against the frozen LineageBindingDeclaration.

    ``declaration`` = {"training_lineage", "relation", "demo_dataset_binding_hash"}.
    Returns the fired error codes.
    """
    if validate(record):
        return ["E_RECORD_SHAPE"]
    if not isinstance(declaration, dict) or "training_lineage" not in declaration:
        return ["E_RECORD_SHAPE"]

    # cycle-2 F-6: the record's self-asserted lineage must equal the frozen declaration's.
    if record["training_lineage"] != declaration["training_lineage"]:
        return ["E_MANIFEST_LINEAGE_INCOHERENT"]  # cycle-3 G-6: a NEW C-side code. Overloading the
        # frozen E_BINDING_LINEAGE_MISMATCH (v13 :171 TrainingProvenance operand, :230 certify-time)
        # for a different operand and firing site would touch frozen semantics (pS design-axis read).

    relation = declaration.get("relation")
    if relation is None:
        return [] if record["training_lineage"] not in DEMO_LINEAGES else ["E_RECORD_SHAPE"]
    if relation not in STAGE_RELATIONS:
        return ["E_RECORD_SHAPE"]

    stages = record["stage_bindings"]
    execution = stages["execution_stage_tensor_binding_hash"]
    bc = stages["bc_stage_tensor_binding_hash"]
    if relation == "IDENTICAL":
        return [] if (bc is not None and bc == execution) else ["E_MANIFEST_STAGE_BINDING_CONFLICT"]
    expected = declaration.get("demo_dataset_binding_hash")
    return [] if (bc is not None and bc == expected) else ["E_MANIFEST_STAGE_BINDING_CONFLICT"]


# --------------------------------------------------------------------------------------
# goldens
# --------------------------------------------------------------------------------------

TB_A = "a" * 64
TB_B = "b" * 64

GOLDENS = {
    "carry_record_golden_A.json": {
        "dataset_substrate_ids": ["kinematic_pin_2026_07"],
        "stage_bindings": {"bc_stage_tensor_binding_hash": None, "execution_stage_tensor_binding_hash": None},
        "substrate_id": "kinematic_pin_2026_07",
        "training_lineage": "NOT_APPLICABLE",
    },
    "carry_record_golden_B.json": {
        "dataset_substrate_ids": ["kinematic_pin_2026_07", "physics_faithful_2026_07"],
        "stage_bindings": {"bc_stage_tensor_binding_hash": TB_A, "execution_stage_tensor_binding_hash": TB_A},
        "substrate_id": "physics_faithful_2026_07",
        "training_lineage": "DEMO_PLUS_RL",
    },
    # cycle-2 F-16: EXPLICIT_SUPERSEDE with bc != execution, so an implementation that
    # mirrors execution into bc can no longer reproduce the corpus.
    "carry_record_golden_C.json": {
        "dataset_substrate_ids": ["physics_faithful_2026_07"],
        "stage_bindings": {"bc_stage_tensor_binding_hash": TB_B, "execution_stage_tensor_binding_hash": TB_A},
        "substrate_id": "physics_faithful_2026_07",
        "training_lineage": "BC_THEN_RL",
    },
    "carry_record_golden_D.json": {
        "dataset_substrate_ids": ["physics_faithful_2026_07"],
        "stage_bindings": {"bc_stage_tensor_binding_hash": None, "execution_stage_tensor_binding_hash": TB_A},
        "substrate_id": "physics_faithful_2026_07",
        "training_lineage": "RL_ONLY",
    },
}

# cycle-3 (G-2): the pinned digests, quoted from design v2.2 s7. These are the EXTERNAL anchor
# -- they are asserted against the on-disk bytes, so a coordinated edit of GOLDENS + the .json
# files can no longer verify clean. A deliberate re-pin must update this table AND the design.
EXPECTED_SHA256 = {
    "carry_record_golden_A.json": "ce474f3ad393767a8d37e9e144d3374b896168c853bd6f3fd6a2520d77c280c8",
    "carry_record_golden_B.json": "f49d15698bf379c10517450aac12590023283b1fab8c2283a0795b05e83bcae2",
    "carry_record_golden_C.json": "1b88fdc0c95813dee54ffcc4f158b71572664e0f5af9f44c4e1d5963a9fe692b",
    "carry_record_golden_D.json": "4971d3f7a6601ff32a1b6e85791ca136de5be71848224dbab12413a0272e4174",
}

DECLARATIONS = {
    "carry_record_golden_A.json": {"training_lineage": "NOT_APPLICABLE", "relation": None},
    "carry_record_golden_B.json": {"training_lineage": "DEMO_PLUS_RL", "relation": "IDENTICAL"},
    "carry_record_golden_C.json": {
        "training_lineage": "BC_THEN_RL",
        "relation": "EXPLICIT_SUPERSEDE",
        "demo_dataset_binding_hash": TB_B,
    },
    "carry_record_golden_D.json": {"training_lineage": "RL_ONLY", "relation": None},
}


# --------------------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------------------


def _mutate(base, path, value):
    record = copy.deepcopy(base)
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return record


def _negative_controls():
    """(label, record, expected_codes) -- expected is an EXACT match, not a subset."""
    a = GOLDENS["carry_record_golden_A.json"]
    b = GOLDENS["carry_record_golden_B.json"]
    d = GOLDENS["carry_record_golden_D.json"]
    return [
        ("substrate absent", _mutate(b, ["substrate_id"], ""), ["E_MANIFEST_SUBSTRATE_ABSENT"]),
        ("substrate malformed", _mutate(b, ["substrate_id"], "bad substrate!"), ["E_MANIFEST_SUBSTRATE_MALFORMED"]),
        ("substrate too long", _mutate(b, ["substrate_id"], "x" * 65), ["E_MANIFEST_SUBSTRATE_MALFORMED"]),
        ("dataset ids empty", _mutate(b, ["dataset_substrate_ids"], []), ["E_MANIFEST_SUBSTRATE_POOLED"]),
        ("dataset ids unsorted", _mutate(b, ["dataset_substrate_ids"], ["z_sub", "a_sub"]), ["E_MANIFEST_SUBSTRATE_POOLED"]),
        ("dataset ids duplicated", _mutate(b, ["dataset_substrate_ids"], ["a_sub", "a_sub"]), ["E_MANIFEST_SUBSTRATE_POOLED"]),
        ("dataset id malformed", _mutate(b, ["dataset_substrate_ids"], ["a_sub", "b a d"]), ["E_MANIFEST_SUBSTRATE_MALFORMED"]),
        ("dataset ids wrong type", _mutate(b, ["dataset_substrate_ids"], "a_sub"), ["E_RECORD_SHAPE"]),
        ("NOT_APPLICABLE carries bc", _mutate(a, ["stage_bindings", "bc_stage_tensor_binding_hash"], TB_A), ["E_MANIFEST_STAGE_BINDING_PRESENT"]),
        ("RL_ONLY carries bc", _mutate(d, ["stage_bindings", "bc_stage_tensor_binding_hash"], TB_A), ["E_MANIFEST_STAGE_BINDING_PRESENT"]),
        ("RL_ONLY missing execution", _mutate(d, ["stage_bindings", "execution_stage_tensor_binding_hash"], None), ["E_MANIFEST_STAGE_BINDING_MISSING"]),
        ("demo lineage missing bc", _mutate(b, ["stage_bindings", "bc_stage_tensor_binding_hash"], None), ["E_MANIFEST_STAGE_BINDING_MISSING"]),
        ("unknown lineage", _mutate(b, ["training_lineage"], "PPO_ONLY"), ["E_RECORD_SHAPE"]),
        ("non-lowercase hex", _mutate(b, ["stage_bindings", "execution_stage_tensor_binding_hash"], "AB" * 32), ["E_RECORD_SHAPE"]),
        ("extra key", dict(list(b.items()) + [("extra", 1)]), ["E_RECORD_SHAPE"]),
    ]


def _declaration_controls():
    """(label, record, declaration, expected_codes)."""
    b = GOLDENS["carry_record_golden_B.json"]
    c = GOLDENS["carry_record_golden_C.json"]
    return [
        ("IDENTICAL but stages differ", _mutate(b, ["stage_bindings", "bc_stage_tensor_binding_hash"], TB_B),
         DECLARATIONS["carry_record_golden_B.json"], ["E_MANIFEST_STAGE_BINDING_CONFLICT"]),
        ("SUPERSEDE hash mismatch", c,
         {"training_lineage": "BC_THEN_RL", "relation": "EXPLICIT_SUPERSEDE", "demo_dataset_binding_hash": TB_A},
         ["E_MANIFEST_STAGE_BINDING_CONFLICT"]),
        ("lineage disagrees with frozen declaration", b,
         {"training_lineage": "BC_ONLY", "relation": "IDENTICAL"}, ["E_MANIFEST_LINEAGE_INCOHERENT"]),
    ]


def _noncanonical_control():
    """Write drifted bytes into a temp dir and assert the on-disk check fires. Never touches
    the pinned directory."""
    tmp = Path(tempfile.mkdtemp(prefix="wmso_d11c_nc_"))
    try:
        for name, record in GOLDENS.items():
            (tmp / name).write_bytes(wcj_bytes(record))
        target = tmp / "carry_record_golden_A.json"
        parsed = json.loads(target.read_bytes())
        target.write_bytes(json.dumps(parsed, separators=(", ", ": ")).encode("utf-8"))
        failures = _verify_dir(tmp, quiet=True)
        fired = any("E_MANIFEST_NONCANONICAL_BYTES" in f for f in failures)
        return fired
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_controls():
    """Run every control. Returns (fired, total, failures)."""
    fired = 0
    failures = []

    for label, record, expected in _negative_controls():
        codes = validate(record)
        if codes == expected:
            fired += 1
        else:
            failures.append("negative control: {} expected {} got {}".format(label, expected, codes))

    for label, record, declaration, expected in _declaration_controls():
        codes = check_against_declaration(record, declaration)
        if codes == expected:
            fired += 1
        else:
            failures.append("declaration control: {} expected {} got {}".format(label, expected, codes))

    # positive controls: every golden must be conformant against its own declaration
    for name, record in GOLDENS.items():
        if validate(record) == [] and check_against_declaration(record, DECLARATIONS[name]) == []:
            fired += 1
        else:
            failures.append("positive control failed for {}".format(name))

    for label, obj, expected_text in ENCODER_VECTORS:
        try:
            actual = wcj_text(obj)
        except WcjError as exc:
            failures.append("encoder vector raised: {} ({})".format(label, exc))
            continue
        if actual == expected_text:
            fired += 1
        else:
            failures.append("encoder vector: {} expected {!r} got {!r}".format(label, expected_text, actual))

    for label, obj in ENCODER_REJECTS:
        try:
            wcj_bytes(obj)
        except WcjError:
            fired += 1
        else:
            failures.append("encoder did not reject: {}".format(label))

    if _noncanonical_control():
        fired += 1
    else:
        failures.append("non-canonical bytes control did not fire")

    total = (
        len(_negative_controls())
        + len(_declaration_controls())
        + len(GOLDENS)
        + len(ENCODER_VECTORS)
        + len(ENCODER_REJECTS)
        + 1
    )
    return fired, total, failures


# --------------------------------------------------------------------------------------
# drivers
# --------------------------------------------------------------------------------------


def _verify_dir(target, quiet=False):
    """Parse, re-canonicalise and byte-compare every golden on disk. Returns failures."""
    failures = []
    # cycle-3: __pycache__ is written by the import machinery BEFORE module code runs, so
    # sys.dont_write_bytecode cannot suppress it for this module. Treating it as unexpected
    # turned an interpreter artifact into a false FAIL of the registered gate (DDR #35 class).
    allowed = set(GOLDENS) | {"build_goldens.py", "__pycache__"}
    for entry in sorted(target.iterdir()):
        if entry.name not in allowed:
            failures.append("unexpected entry in fixture dir: {}".format(entry.name))
    for name, record in GOLDENS.items():
        path = target / name
        if not path.is_file():
            failures.append("missing fixture: {}".format(name))
            continue
        raw = path.read_bytes()
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            failures.append("unparseable fixture {}: {}".format(name, exc))
            continue
        # Canonicality is diagnosed BEFORE the pinned digest: a drifted-encoding file is both
        # non-canonical and sha-mismatched, and the encoding diagnosis is the informative one.
        if wcj_bytes(parsed) != raw:
            failures.append("{}: E_MANIFEST_NONCANONICAL_BYTES".format(name))
            continue
        # cycle-3 (G-2): external anchor. Without a pinned digest, a coordinated edit of this
        # file AND the goldens verifies clean -- the tool would certify only self-consistency.
        # A tampered golden re-emitted by a tampered builder IS canonical, so only this catches it.
        expected_sha = EXPECTED_SHA256.get(name)
        actual_sha = hashlib.sha256(raw).hexdigest()
        if expected_sha is not None and actual_sha != expected_sha:
            failures.append("{}: pinned sha256 mismatch (expected {}, got {})".format(name, expected_sha[:16], actual_sha[:16]))
            continue
        codes = validate(parsed)
        if codes:
            failures.append("{} is not conformant: {}".format(name, codes))
            continue
        if parsed != record:
            failures.append("{} drifted from the expected record".format(name))
            continue
        if not quiet:
            print("PASS {}  sha256={}  bytes={}".format(name, hashlib.sha256(raw).hexdigest(), len(raw)))
    return failures


def emit(target_dir):
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    for name, record in GOLDENS.items():
        codes = validate(record)
        if codes:  # cycle-2 F-6/S-1 mirror: never bank a non-conformant golden
            print("FAIL: refusing to write non-conformant golden {}: {}".format(name, codes))
            return 1
        (target / name).write_bytes(wcj_bytes(record))
        print("wrote {}  sha256={}  bytes={}".format(name, record_hash(record), len(wcj_bytes(record))))
    fired, total, failures = run_controls()
    print("controls: {}/{} fired".format(fired, total))
    for line in failures:
        print("FAIL: " + line)
    return 1 if failures else 0


def verify(target_dir):
    target = Path(target_dir)
    if not target.is_dir():
        print("FAIL: not a directory: {}".format(target_dir))
        return 1
    failures = _verify_dir(target)
    fired, total, control_failures = run_controls()
    failures.extend(control_failures)
    print("controls: {}/{} fired".format(fired, total))
    if failures:
        for line in failures:
            print("FAIL: " + line)
        return 1
    print("conformance: {}/{} PASS".format(len(GOLDENS), len(GOLDENS)))
    return 0


def main(argv):
    # cycle-2 F-4: explicit subcommands only. No path that writes on a malformed argv.
    if len(argv) == 3 and argv[1] == "--verify":
        return verify(argv[2])
    if len(argv) == 3 and argv[1] == "--emit":
        return emit(argv[2])
    print("usage: build_goldens.py --verify <dir> | --emit <dir>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
