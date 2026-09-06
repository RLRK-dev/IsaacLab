#!/usr/bin/env python3
"""Mechanical checks for WMSO v0.2 review-candidate documents (records-only helper; stdlib only).

Usage: python3 check_review_candidate.py <doc.md|matrix.csv> [...] [--runtime | --profile]
Checks (fail-closed; exit 1 on any FAIL):
  H1  header block present (status REVIEW CANDIDATE, 4 frozen pins full 64-hex, CLOSED line)         [md only]
  S1  mandatory sections present (中心構造 / 主張しないこと / Open points / 版歴 / Review anchors)      [md only]
  F1  forbidden identifiers absent from normative text (allowed only on 版歴/fold-map lines carrying 削除 or 不採用;
      in CSV mode allowed only on rows whose disposition/verdict column is removed / not_adopted)
  F2  NO_CHAIN never listed inside a ProducerOutcome enum block                                          [md only]
  C1  every `<frozen-file>:<line>` citation points to an existing file and line
  C2  (heuristic, WARN not FAIL) a backticked identifier from the citing sentence appears within ±3 lines of the cited line
  O1  (runtime spec only, --runtime) ordering: first mention of ReadinessAck < CommitPermit < AuthorityCas/CAS < HealthConfirmation in §3
  O2  (runtime spec only) replay/stale rules present: handoff_offer_id, authority_epoch_snapshot, E_HANDOFF_EPOCH_STALE, R_OFFER_REUSED, R_EPOCH_STALE_COMMAND
  O3  (runtime spec only) §3 CAS postcondition records the consumed offer: 'consumed_offer_ids ∪ {consume_offer_id}' (positive-control blind spot PC-05-C)
  O4  (runtime spec only) post-outcome rejection token R_POST_OUTCOME_COMMAND and one-shot permit consumption sentence present
  K1  (CSV mode, v0.2.2 / A-08) header equals the declared column list and data-row count equals the declared count (02 = 40, 03 = 14)
  O5  (runtime spec only, v0.2.3) every RuntimeFaultCode enum member has a row in the §3.7 failure table (INV-27 totality)
  O6  (runtime spec only, v0.2.3) INV-/T-/OP- ids are contiguous from 1 with no duplicates
  O7  (runtime spec only, v0.2.3) CAS condition 10 reason set == the §5.4 "追加前提" set (A2-01 / B2-07)
  O8  (runtime spec only, v0.2.3) every RuntimeTimeouts field of the sibling 06 profile spec exists in TimingBinding (INV-22 / CD-13)
  Q1  (profile spec only, --profile, v0.2.3) every P_* code used in 06 body appears in the §8.1 code list; PT-/OPP- ids contiguous, no duplicates
  Q3  (profile spec only, v0.2.8 R8-13) every P_* code in the §8.1 code list appears in the §8.1 rule (2) evaluation-point text (1st point / 1b record write / 2nd point)
  Q2  (profile spec only, v0.2.6 / R3-17 R4-02 / v0.2.7 R6-13 / v0.2.8 R7-16) every *_sha256 / *_hash field declared in 06 §2.1-2.2 is named inside the sibling 05 §3.4 (j) segment (exclusion clause stripped; allowlist = tensor_binding_hash), at least once per declaring class
CSV mode is selected by the `.csv` extension (02 / 03 matrices); H1 / S1 / F2 / O* do not apply there.
"""
import csv, io, os, re, sys

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
CSV_SPECS = {  # basename prefix -> (header, data rows, F1-exempt column, exempt values)
    "02_": ("id,item,layer_of_origin,overlaps_frozen,frozen_locus,home_v0_2,disposition_v0_2,rationale,citation", 40, "disposition_v0_2", {"removed", "not_adopted"}),
    "03_": ("class_id,change_class,example,affects_SkillDefinitionHash,affects_SkillActionId_or_ExecutionBundleHash,affects_BehaviorSignature_or_behavior_revision,affects_certificate,affects_EP_definition_hash,affects_tensor_binding_hash,runtime_records_only,verdict,citation", 14, "verdict", {"removed", "not_adopted"}),
}

def repo_root():
    here = os.path.abspath(os.getcwd())
    while here != "/":
        if os.path.isdir(os.path.join(here, D)):
            return here
        here = os.path.dirname(here)
    return os.getcwd()

def cite_check(lines, root, fails, warns):
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
    return n_cit

def check_csv(path, root):
    fails, warns = [], []
    base = os.path.basename(path)
    spec = next((v for k, v in CSV_SPECS.items() if base.startswith(k)), None)
    raw = open(path, encoding="utf-8").read()
    lines = raw.splitlines()
    rows = list(csv.reader(io.StringIO(raw)))
    if spec is None:
        fails.append("K1 no CSV spec registered for this file (expected 02_ / 03_ prefix)")
        exempt_col, exempt_vals = None, set()
    else:
        header, n_rows, exempt_col, exempt_vals = spec
        if ",".join(rows[0]) != header: fails.append("K1 header mismatch: " + ",".join(rows[0]))
        if len(rows) - 1 != n_rows: fails.append(f"K1 data-row count {len(rows)-1} != declared {n_rows}")
        width = len(header.split(","))
        for i, r in enumerate(rows[1:], 2):
            if len(r) != width: fails.append(f"K1 row {i} has {len(r)} columns (expected {width})")
    hdr = rows[0] if rows else []
    for i, r in enumerate(rows[1:], 2):
        disp = r[hdr.index(exempt_col)].strip() if (exempt_col in hdr and len(r) == len(hdr)) else ""
        joined = ",".join(r)
        for ident in FORBIDDEN:
            if ident in joined and disp not in exempt_vals:
                fails.append(f"F1 forbidden identifier '{ident}' at row {i} (disposition/verdict = '{disp}' is not removed/not_adopted)")
    n_cit = cite_check(lines, root, fails, warns)
    return fails, warns, n_cit

def check(path, root):
    if path.lower().endswith(".csv"):
        return check_csv(path, root)
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
    n_cit = cite_check(lines, root, fails, warns)
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
        # O5 (v0.2.3): every RuntimeFaultCode member has a failure-table row
        i = text.find("class RuntimeFaultCode"); enum = text[i:text.find("```", i)] if i >= 0 else ""
        r_enum = set(re.findall(r"R_[A-Z_]+", enum))
        sec37 = text[text.find("## 3.7"):text.find("## 4.")]
        ftbl = sec37[sec37.find("| 失敗 | 検出者 | fault |"):]
        r_fail = set(re.findall(r"`(R_[A-Z_]+)`", ftbl))
        if not r_enum: fails.append("O5 RuntimeFaultCode enum block not found")
        for r in sorted(r_enum - r_fail): fails.append(f"O5 fault code {r} has no §3.7 failure-table row (INV-27)")
        # O6: contiguous ids
        for name, pat in (("INV", r"^\| (INV-\d+) \|"), ("T", r"^\| (T-\d+) \|"), ("OP", r"^\| (OP-\d+) \|")):
            ids = re.findall(pat, text, re.M); nums = sorted(int(x.split("-")[1]) for x in ids)
            if not nums: fails.append(f"O6 no {name}- rows found"); continue
            dup = sorted({x for x in ids if ids.count(x) > 1}); gaps = [n for n in range(1, max(nums) + 1) if n not in nums]
            if dup or gaps: fails.append(f"O6 {name}- ids not contiguous/unique: dup={dup} gaps={gaps}")
        # O7: cond 10 set == §5.4 set
        c10 = [l for l in lines if l.startswith("10. `safehold_reason ∈")]
        s54 = [l for l in lines if "CAS 条件 10 の集合" in l]
        if not c10 or not s54: fails.append("O7 condition 10 line or §5.4 set line not found")
        else:
            a = set(re.findall(r"[A-Z_]{4,}", re.search(r"\{[^}]+\}", c10[0]).group(0)))
            b = set(re.findall(r"[A-Z_]{4,}", re.search(r"\{[^}]+\}", s54[0]).group(0)))
            if a != b: fails.append(f"O7 condition 10 set {sorted(a)} != §5.4 set {sorted(b)}")
        # O8: sibling 06 RuntimeTimeouts ⊆ TimingBinding
        sib = os.path.join(os.path.dirname(os.path.abspath(path)), "06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
        if os.path.isfile(sib):
            g = open(sib, encoding="utf-8").read(); j = g.find("class RuntimeTimeouts:"); rt = g[j:g.find("\n\n", j)] if j >= 0 else ""
            k = text.find("class TimingBinding:"); tb = text[k:text.find("\n\n", k)] if k >= 0 else ""
            rtf = set(re.findall(r"^\s{4}(\w+):", rt, re.M)); tbf = set(re.findall(r"^\s{4}(\w+):", tb, re.M))
            for fld in sorted(rtf - tbf): fails.append(f"O8 RuntimeTimeouts.{fld} (06) has no TimingBinding field (05)")
        else:
            warns.append("O8 sibling 06 not found; RuntimeTimeouts ⊆ TimingBinding not checked")
    if "--profile" in sys.argv:
        pl = [l for l in lines if l.startswith("`P_INTRINSIC_OVERRIDE` / ")]
        if not pl: fails.append("Q1 §8.1 code list line not found")
        else:
            listed = set(re.findall(r"`(P_[A-Z_]+)`", pl[0])); used = set(re.findall(r"`(P_[A-Z_]+)`", text))
            for c in sorted(used - listed): fails.append(f"Q1 code {c} used in body but absent from §8.1 code list")
        # Q2 (v0.2.6): declared hash fields in §2.1 ⊆ 05 §3.4 (j) enumeration
        # v0.2.7 (R6-13): scan §2.1 AND §2.2, match only inside the (j) segment, and require one mention per declaring class
        s2 = text[text.find("### 2.1"):text.find("### 2.3")]
        decl = {}
        for cls, body in re.findall(r"^class (\w+)[^\n]*\n((?:^    [^\n]*\n?)+)", s2, re.M):
            for h in re.findall(r"^\s{4}(\w+(?:_sha256|_hash)):", body, re.M): decl.setdefault(h, set()).add(cls)
        sib05 = os.path.join(os.path.dirname(os.path.abspath(path)), "05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
        if os.path.isfile(sib05):
            t05 = open(sib05, encoding="utf-8").read(); jl = [l for l in t05.splitlines() if "(j) profile が宣言する" in l]
            if not jl: fails.append("Q2 05 §3.4 (j) enumeration line not found")
            else:
                a = jl[0].find("(j) profile が宣言する"); b = jl[0].find("が解決先の内容と一致", a)
                seg = jl[0][a:b] if b > a else jl[0][a:]
                if b <= a: warns.append("Q2 (j) segment end marker not found; matching against the whole (j) tail")
                # v0.2.8 (R7-16): the exclusion clause '(j) の対象外 = …' is stripped before counting; excluded names pass only via the allowlist
                ex = seg.find("(j) の対象外 =")
                ex_end = seg.find("。", ex) + 1 if ex >= 0 and seg.find("。", ex) >= 0 else len(seg)
                excl_txt = seg[ex:ex_end] if ex >= 0 else ""; seg = (seg[:ex] + seg[ex_end:]) if ex >= 0 else seg
                excluded = set(re.findall(r"(\w+(?:_sha256|_hash))", excl_txt)); ALLOW_EXCLUDED = {"tensor_binding_hash"}
                for h, cls in sorted(decl.items()):
                    if h in excluded:
                        if h in ALLOW_EXCLUDED: continue
                        fails.append(f"Q2 06 hash field '{h}' is excluded in 05 §3.4 (j) but is not on the checker allowlist"); continue
                    n = len(re.findall(r"(?<![\w.])" + re.escape(h) + r"(?!\w)", seg.replace("`", " "))) + len(re.findall(r"\." + re.escape(h) + r"(?!\w)", seg))
                    if n == 0: fails.append(f"Q2 06 §2.1/2.2 hash field '{h}' ({'/'.join(sorted(cls))}) is not named in 05 §3.4 (j)")
                    elif n < len(cls): fails.append(f"Q2 06 hash field '{h}' is declared by {len(cls)} classes ({'/'.join(sorted(cls))}) but named {n} time(s) in 05 §3.4 (j)")
        else:
            warns.append("Q2 sibling 05 not found; hash enumeration not checked")
        # Q3 (v0.2.8, R8-13): every P_* code in the §8.1 code list is placed in the §8.1 rule (2) evaluation-point text
        if pl:
            rl = [l for l in lines if l.startswith("規則: (1) 全検査は fail-closed")]
            if not rl: fails.append("Q3 §8.1 rule (2) line not found")
            else:
                placed = set(re.findall(r"`(P_[A-Z_]+)`", rl[0]))
                for cde in sorted(set(re.findall(r"`(P_[A-Z_]+)`", pl[0])) - placed): fails.append(f"Q3 code {cde} is listed in §8.1 but has no evaluation point in rule (2)")
        for name, pat in (("PT", r"^\| (PT-\d+) \|"), ("OPP", r"^\| (OPP-\d+) \|")):
            ids = re.findall(pat, text, re.M); nums = sorted(int(x.split("-")[1]) for x in ids)
            if not nums: fails.append(f"Q1 no {name}- rows found"); continue
            dup = sorted({x for x in ids if ids.count(x) > 1}); gaps = [n for n in range(1, max(nums) + 1) if n not in nums]
            if dup or gaps: fails.append(f"Q1 {name}- ids not contiguous/unique: dup={dup} gaps={gaps}")
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
