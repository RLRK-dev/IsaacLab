#!/usr/bin/env python3
"""Mechanical checks for WMSO v0.2 review-candidate documents (records-only helper; stdlib only).

Usage: python3 check_review_candidate.py <doc.md> [<doc.md> ...]
Checks (fail-closed; exit 1 on any FAIL):
  H1  header block present (status REVIEW CANDIDATE, 4 frozen pins full 64-hex, CLOSED line)
  S1  mandatory sections present (中心構造 / 主張しないこと / Open points / 版歴 / Review anchors)
  F1  forbidden identifiers absent from normative text (allowed only on 版歴/fold-map lines carrying 削除 or 不採用)
  F2  NO_CHAIN never listed inside a ProducerOutcome enum block
  C1  every `<frozen-file>:<line>` citation points to an existing file and line
  C2  (heuristic, WARN not FAIL) a backticked identifier from the citing sentence appears within ±3 lines of the cited line
  O1  (runtime spec only, --runtime) ordering: first mention of ReadinessAck < CommitPermit < AuthorityCas/CAS < HealthConfirmation in §3
  O2  (runtime spec only) replay/stale rules present: handoff_offer_id, authority_epoch_snapshot, E_HANDOFF_EPOCH_STALE, R_OFFER_REUSED, R_EPOCH_STALE_COMMAND
  O3  (runtime spec only) §3 CAS postcondition records the consumed offer: 'consumed_offer_ids ∪ {consume_offer_id}' (positive-control blind spot PC-05-C)
  O4  (runtime spec only) post-outcome rejection token R_POST_OUTCOME_COMMAND and one-shot permit consumption sentence present
"""
import os, re, sys

D = "eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
FROZEN_PINS = [
    "00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff",
    "c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7",
    "e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e",
    "5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6",
]
FORBIDDEN = ["BeliefSnapshotRef", "continuation_overlay_hash", "recovery_overlay_hash", "ParallelExecutionProfile", "IntrinsicExecutionLimits"]
MANDATORY = ["中心構造", "主張しないこと", "Open points", "版歴", "Review anchors"]
CITE_RE = re.compile(r"(?:\$D/)?((?:WMSO_[A-Za-z0-9_.]+|thread_isaac_lab/[A-Za-z0-9_./-]+)\.(?:md|json|py)):(\d+)(?:-(\d+))?")

def repo_root():
    here = os.path.abspath(os.getcwd())
    while here != "/":
        if os.path.isdir(os.path.join(here, D)):
            return here
        here = os.path.dirname(here)
    return os.getcwd()

def check(path, root):
    fails, warns = [], []
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    head = "\n".join(lines[:15])
    # H1
    if "REVIEW CANDIDATE" not in head: fails.append("H1 status 'REVIEW CANDIDATE' missing in header")
    for pin in FROZEN_PINS:
        if pin not in head: fails.append(f"H1 frozen pin {pin[:12]}… missing in header")
    if "CLOSED" not in head: fails.append("H1 CLOSED boundary line missing in header")
    # S1
    for m in MANDATORY:
        if not re.search(r"^#+ .*" + re.escape(m), text, re.M): fails.append(f"S1 mandatory section '{m}' missing")
    # F1
    in_foldmap = False
    for i, ln in enumerate(lines, 1):
        if re.match(r"^#+ ", ln):
            in_foldmap = ("版歴" in ln) or ("fold-map" in ln.lower())
        for ident in FORBIDDEN:
            if ident in ln:
                if in_foldmap and ("削除" in ln or "不採用" in ln):
                    continue
                fails.append(f"F1 forbidden identifier '{ident}' at line {i} (outside 版歴/削除 context)")
    # F2
    for m in re.finditer(r"class\s+ProducerOutcome[^\n]*\n((?:[ \t]+[^\n]*\n)+)", text):
        if "NO_CHAIN" in m.group(1): fails.append("F2 NO_CHAIN appears inside a ProducerOutcome enum block")
    # C1 / C2
    n_cit = 0
    for i, ln in enumerate(lines, 1):
        for m in CITE_RE.finditer(ln):
            n_cit += 1
            rel, a, b = m.group(1), int(m.group(2)), m.group(3)
            fpath = os.path.join(root, D, rel) if rel.startswith("WMSO_") else os.path.join(root, rel)
            if not os.path.isfile(fpath):
                fails.append(f"C1 line {i}: cited file not found: {rel}"); continue
            src = open(fpath, encoding="utf-8", errors="replace").read().splitlines()
            last = int(b) if b else a
            if a < 1 or last > len(src):
                fails.append(f"C1 line {i}: cited line {a}{'-'+b if b else ''} out of range (file has {len(src)} lines): {rel}"); continue
            idents = [t for t in re.findall(r"`([^`]{3,})`", ln) if not re.search(r"\.(md|json|py)", t)]
            if idents:
                window = "\n".join(src[max(0, a-4):min(len(src), last+3)])
                if not any(t.split("(")[0].split(".")[-1] in window for t in idents):
                    warns.append(f"C2 line {i}: none of {idents[:3]} found near {rel}:{a}")
    if "--runtime" in sys.argv:
        sec3 = re.search(r"^## 3\..*?(?=^## 4\.)", text, re.S | re.M)
        body = sec3.group(0) if sec3 else text
        order = [body.find(k) for k in ("ReadinessAck", "CommitPermit", "AuthorityCas", "HealthConfirmation")]
        if any(o < 0 for o in order): fails.append(f"O1 §3 lacks one of ReadinessAck/CommitPermit/AuthorityCas/HealthConfirmation: {order}")
        elif order != sorted(order): fails.append(f"O1 §3 ordering violated (first-mention offsets {order}); required ACK → permit → CAS → health")
        for k in ("handoff_offer_id", "authority_epoch_snapshot", "E_HANDOFF_EPOCH_STALE", "R_OFFER_REUSED", "R_EPOCH_STALE_COMMAND"):
            if k not in text: fails.append(f"O2 required replay/stale rule token missing: {k}")
        # O3 (positive-control blind spot PC-05-C): the CAS postcondition must record the consumed offer in the tuple
        if "consumed_offer_ids ∪ {consume_offer_id}" not in body: fails.append("O3 §3 CAS postcondition lacks 'consumed_offer_ids ∪ {consume_offer_id}'")
        # O4 (v0.2.1): post-outcome admission rejection and one-shot permit consumption at the CAS point must be stated
        for k in ("R_POST_OUTCOME_COMMAND", "CONSUMED` は CAS 成功の同一線形化点でのみ設定"):
            if k not in text: fails.append(f"O4 required v0.2.1 rule token missing: {k}")
    return fails, warns, n_cit

def main():
    root = repo_root()
    rc = 0
    for p in [a for a in sys.argv[1:] if not a.startswith("--")]:
        fails, warns, n_cit = check(p, root)
        print(f"== {p}: citations={n_cit} FAIL={len(fails)} WARN={len(warns)}")
        for f in fails: print("  FAIL", f)
        for w in warns: print("  WARN", w)
        if fails: rc = 1
    sys.exit(rc)

if __name__ == "__main__":
    main()
