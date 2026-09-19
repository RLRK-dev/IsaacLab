# pZ — verdict on the B-line landing `96e9ece175`, judged against its own parent blob

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 08:03:42 JST on m-p18-374 (p4 m-p4-274: "pZ = B 行 leg on 96e9ece175（次）"). Measurements first taken 2026-09-16 18:40-18:45 JST (this desk's session paused 09-16 18:45 → 09-20 08:00 before the artifact could be written; every instrument was re-run at write time — appendix B — with identical output). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Pre-registration** = `PZ_B_LINE_LEG_PREREG_20260916.md` @ `e41d0a9304` (sha256 `7d938cfd6b82383d48f1e3e8e7dd03d278163d4d04820a47fdf616644e823bb5`, worktree byte-identical), rows 1-8 + 3′. Spec = v3 §17.2 @ `dc090f7753` (read at that commit: `:236-244`).
**Object** = commit `96e9ece175` (author date 2026-09-16 18:23:08 JST, parent `329a9c9725`), one file `p4_ur15_sim_20260727/ur15_steps_wired.py`, numstat +11/−0, one hunk `@@ -616,0 +617,11 @@`.
**Parent blob** (the base the rows were registered on) = `d2bc133e1320` = the D4 blob at `3370f7a872` (sha256 `a6a42f06a058c0ed30a53d698984de5e17a520871b2ca4a801488689fed97f72`, 4,042 lines). **Landed blob** = `84a372439c59` (sha256 `f461984bd7016a4ed66de0d9c3453f9416ca4e7d802e730dffc185da4ddd9b0f`, 4,053 lines). At writing: HEAD `98a16ead2c`, HEAD driver blob `84a372439c59`, driver commits after `96e9ece175` = 0.

## Verdict — static rows CONFIRMED; the runtime row is UNVERIFIED by design (#69 only)

| # | row (prereg) | result | measurement (all from the two blobs as text/AST; the driver was never imported) |
|---|---|---|---|
| 1 | placement + scope | **CONFIRMED** | top-level statements 292 → 293 (+1); base `AXFIX` idx 92 `:616`, `def pinch` idx 93 `:619`, 0 between; landed `AXFIX` idx 92 `:616`, `pinch` idx 94 `:630`, **1 between** = the `For` at `:621-627`. Lines 1-616 byte-identical, base 617-4042 == landed 628-4053 (delta 11). The 11 inserted lines = 4 comment lines `:617-620` + 7 code lines (comments are not statements). 1 file |
| 2 | form (AST) | **CONFIRMED** | `For(target=Name 't', iter=Name 'SIDES', body=[Expr(Call print)], orelse=[])`; print has 1 positional arg (one `JoinedStr`), 0 keywords; first Constant = `'[steps] controller record '` |
| 3 | fields (AST) | **CONFIRMED** | 17 FormattedValues; the set of `Name[t]` subscripts they read = exactly {`AXFIX[t]`, `QADR[t]`, `VADR[t]`, `AIDX[t]`, `GIDX[t]`, `PAD[t]`, `TOOLB[t]`, `SIDES[t]`} + `t` (extra ∅, missing ∅); `AXFIX[t][r][c]` covers (r,c) ∈ 0..2×0..2 exactly once, all nine `+.6f`; `SIDES[t]` `+.1f`; the six index fields and `t` carry no format spec; order in the string = t, AXFIX rows 0/1/2, QADR, VADR, AIDX, GIDX, PAD, TOOLB, SIDES = §17.2 ①-⑥ order; class literal `existing per-arm 6D DLS + position servo` present. All eight globals exist in the base: `AIDX :449 GIDX :450 QADR :451 VADR :452 PAD :453 TOOLB :471 AXFIX :616`; `SIDES` comes from the `from ur15_cell_spec import (…)` statement `:145-158` (the name is on `:158`; the prereg's "imported `:158`" is the name's line, the statement starts at `:145` — precision note, no change of substance) |
| 3′ | design literal (p4 condition (ii)) | **CONFIRMED** | the `design=` Constant tail == `P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753` by string equality |
| 4 | forbidden substrings | **CONFIRMED** | 28 string Constants in the new statement: `nan` 0 · `inf` 0 · `error` 0 · `fail` 0 · `warn` 0 (case-insensitive). Note: the 4 comment lines also contain none |
| 5 | DoD predicate — mine, v3 | **CONFIRMED** | `pz_b_pred.py` v3 (re-extracted from `e41d0a9304` appendix B, sha256 `7079641ffe…` == stated; depends on `pz_d4_pred.py` v3 sha256 `0ba3c59b58…` == stated; scratchpad copies byte-identical): base/landed **PASS** `changed=[('For','t in SIDES: print:[steps] controller record')] outside_allowed=[]`; base/base PASS `changed=[]`. Controls on the **landed** object (table below): literal flip FAIL, stray print FAIL, B line twice FAIL |
| 6 | control invariance | **CONFIRMED** | `pz_ctrl2.py` (re-extracted from `cb787871f0` appendix B, sha256 `d10b4e5c61…`; that artifact states no sha for it — the scratchpad copy is byte-identical) on `3370f7a872` and on `96e9ece175`: `live-state writes 0 [] | d.ctrl writes 7 | control calls 27 (mj_step 11) | sequence 34 lines sha256 a1cf9bf78a568ab6` — identical. The 6 `RUN_METRICS` lines identical between the blobs. `controller record` occurs once in the landed file (`:622`) ⇒ no reader (record only) |
| 7 | runtime expectation | **UNVERIFIED — not run** | #69 only (pB reads the log). The bar stays as pre-registered: each side's 9 `AXFIX` numbers vs my composed models ≤ 1e-6 and `AXFIX_R = diag(1,−1,1)·AXFIX_L·A` ≤ 1e-6, compared as numbers (the sign of a printed zero is not a difference). No physics step was executed by me (import count 0) |
| 8 | no run | **CONFIRMED** | `py_compile` of the landed blob OK; #69 unfired; route run (2), D4′, the 09-07 WIP untouched |

**Stop-cause tag (Rs1 supplement a): none** (static leg; no instrument stop, no controller failure — nothing ran).
**Rs1 supplement b**: this verdict says **landed and verified against the pre-registered static rows**; "accepted" is p4's word after this leg (v3 §17.5). Row 7 remains an open hole until #69 runs — the printed numbers are not measured here.

## Controls fired on the landed object (the instrument must be able to fail on this object)

| control | mutant | result |
|---|---|---|
| literal flip | landed `:2147` (= base `:2136` + 11) `0.05**2` → `0.06**2` inside `solve_ik`; mutant verified to differ from the landed file by `cmp` | FAIL `outside_allowed=[('FunctionDef','solve_ik')]` |
| stray statement | landed + `print("stray")` appended at module level | FAIL `outside_allowed=[('Expr','print:stray')]` |
| duplicate allowed statement | landed with the `For` (`:621-627`) inserted a second time right after itself | FAIL `allowed statement not exactly once … counts=[2]` |

**Disclosed slip in my own leg**: my first literal-flip attempt ran `sed '2136s/0\.002/0.003/'` on the **landed** file — base `:2136` had moved to landed `:2147` and the pattern `0.002` is not on that line, so the mutant was byte-identical to the landed file and the predicate's PASS was a no-op, not evidence. Re-done at `:2147` with the mutant's difference checked by `cmp` before running (table above). Lesson kept: verify a mutant differs before reading its verdict.

## Cross-check against the other desks' readings (their artifacts read by me, not their messages)

- p4 kickoff item 12 @ `7867c40c7e` (+5/−0), p0 §8.53 @ `65af36a2bf` (+91/−0) and the hub's §1483 all state: +11/−0, hunk `@-616,0 +617,11`, blob `84a372439c59`, sha `f461984bd7…`, 4,053 lines, literal `@dc090f7753`, driver commits after = 0. **All equal my measurements above.**
- p0's predicate (`ast_pred_b.py`, positional compare) is a different instrument from my banked v3 (name-key + full-dump change set); both PASS the landed blob and both FAIL the same three mutant classes. p0's control (a) "base vs base FAIL" is by p0's predicate's construction (it requires the insertion); under mine base/base is PASS (`changed=[]`). Not a discrepancy — two predicates asking different questions; I judge by mine as pre-registered.

## Holes that remain (named, not handled)

1. Row 7 (runtime values of the two printed rows) — #69 only; no authorization sought or held.
2. The comment line `:620` says the two rows are "for pB/pC to read": a comment, not a reader; row 6's "no reader" is about code and holds.
3. R0 prereg row 4 re-pin (targets' source for STEPS rows 2-5, GL/GR) waits on p11's §17 line per p4's ordering in m-p4-274; not done in this leg. The R0 harness itself landed at `d038e2536f` (new file `r0_convergence_harness.py`, +778, hub §1491); its leg is a separate verdict after the hub's relay (m-p18-378, held for this desk at the pause) reaches me.

## Provenance
Instruments: `pz_b_pred.py`/`pz_d4_pred.py` v3 from `e41d0a9304`; `pz_ctrl2.py` from `cb787871f0`; `pz_b_rows.py` (appendix A, sha256 `89b0dd6f998da70dba329bcac3602225a7166b89865d40fb5771a7c4c3baa5c9`) written for this leg. Blobs read with `git show <blob>`; the shared working copy (09-07 WIP) was not read as the object. Zero tracked-content modifications by pZ. Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction id m-p18-374.

## Appendix A — `pz_b_rows.py` (verbatim; python3, no MuJoCo, AST/text only)
```python
import ast, sys, re, py_compile
base_p, land_p = sys.argv[1], sys.argv[2]
B = open(base_p).read(); L = open(land_p).read()
bl = B.split("\n"); ll = L.split("\n")
bt = ast.parse(B); lt = ast.parse(L)
# --- row 1: placement + scope
def top_index(tree, pred):
    return [i for i, s in enumerate(tree.body) if pred(s)]
is_axfix = lambda s: isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "AXFIX" for t in s.targets)
is_pinch = lambda s: isinstance(s, ast.FunctionDef) and s.name == "pinch"
bi_ax, bi_pi = top_index(bt, is_axfix)[0], top_index(bt, is_pinch)[0]
li_ax, li_pi = top_index(lt, is_axfix)[0], top_index(lt, is_pinch)[0]
print(f"row1 top-level stmts base={len(bt.body)} landed={len(lt.body)} delta={len(lt.body)-len(bt.body)}")
print(f"row1 base: AXFIX idx={bi_ax} line={bt.body[bi_ax].lineno}, pinch idx={bi_pi} line={bt.body[bi_pi].lineno}, between={bi_pi-bi_ax-1}")
print(f"row1 landed: AXFIX idx={li_ax} line={lt.body[li_ax].lineno}, pinch idx={li_pi} line={lt.body[li_pi].lineno}, between={li_pi-li_ax-1}")
new = lt.body[li_ax+1:li_pi]
print(f"row1 new statements between AXFIX and pinch: {len(new)} at lines {[ (s.lineno, s.end_lineno) for s in new]}")
# byte identity outside the hunk (insertion 617..627 in landed, i.e. base[:616]==landed[:616], base[616:]==landed[627:])
ins_n = len(ll) - len(bl)
print(f"row1 line delta {ins_n}; prefix identical={bl[:616]==ll[:616]}; suffix identical={bl[616:]==ll[616+ins_n:]}")
print(f"row1 inserted lines 617..{616+ins_n}: comment lines={sum(1 for x in ll[616:616+ins_n] if x.lstrip().startswith('#'))}, code lines={sum(1 for x in ll[616:616+ins_n] if x.strip() and not x.lstrip().startswith('#'))}")
# --- row 2: form
st = new[0] if new else None
ok2 = (isinstance(st, ast.For) and isinstance(st.target, ast.Name) and st.target.id == "t" and isinstance(st.iter, ast.Name) and st.iter.id == "SIDES"
       and len(st.body) == 1 and not st.orelse and isinstance(st.body[0], ast.Expr) and isinstance(st.body[0].value, ast.Call)
       and isinstance(st.body[0].value.func, ast.Name) and st.body[0].value.func.id == "print")
call = st.body[0].value
print(f"row2 form For(t in SIDES) body=[Expr print] orelse=[]: {ok2}; print args={len(call.args)} keywords={len(call.keywords)}")
js = call.args[0]
first = js.values[0] if isinstance(js, ast.JoinedStr) else js
print(f"row2 first Constant startswith '[steps] controller record': {isinstance(first, ast.Constant) and first.value.startswith('[steps] controller record')!r} -> {first.value[:40]!r}")
# --- row 3: fields
def root(e):
    while isinstance(e, ast.Subscript): e = e.value
    return e
fv = [v for v in js.values if isinstance(v, ast.FormattedValue)]
fields = {}
for v in fv:
    e = v.value
    r = root(e)
    # innermost Name[t] subscript
    inner = e
    while isinstance(inner, ast.Subscript) and isinstance(inner.value, ast.Subscript): inner = inner.value
    keyt = ast.unparse(inner)
    spec = ast.unparse(v.format_spec)[2:-1] if v.format_spec else ""
    fields.setdefault(keyt, []).append((ast.unparse(e), spec, v.conversion))
print("row3 FormattedValue count:", len(fv))
for k in sorted(fields): print("   ", k, fields[k])
want = {"AXFIX[t]", "QADR[t]", "VADR[t]", "AIDX[t]", "GIDX[t]", "PAD[t]", "TOOLB[t]", "SIDES[t]", "t"}
print("row3 subscript set == pre-registered eight + t:", set(fields) == want, "extra=", set(fields)-want, "missing=", want-set(fields))
ax = sorted((a, spec) for a, spec, _ in fields.get("AXFIX[t]", []))
cells = sorted(re.findall(r"AXFIX\[t\]\[(\d)\]\[(\d)\]", " ".join(a for a, _ in ax)))
print("row3 AXFIX cells:", cells == [(str(r), str(c)) for r in range(3) for c in range(3)], "all +.6f:", all(s == "+.6f" for _, s in ax), len(ax))
print("row3 SIDES spec +.1f:", [s for _, s, _ in fields.get("SIDES[t]", [])])
print("row3 other fields no spec:", {k: [s for _, s, _ in fields[k]] for k in ["QADR[t]", "VADR[t]", "AIDX[t]", "GIDX[t]", "PAD[t]", "TOOLB[t]", "t"]})
consts = "".join(v.value for v in js.values if isinstance(v, ast.Constant))
print("row3 class literal present:", "existing per-arm 6D DLS + position servo" in consts)
m = re.findall(r"design=(\S+)", consts)
print("row3 / 3' design literal:", m, "== 'P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753':", m == ["P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753"])
# --- row 4: forbidden substrings in Constants of the new statement (case-insensitive too)
allc = [n.value for n in ast.walk(st) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
bad = {w: [c for c in allc if w in c.lower()] for w in ("nan", "inf", "error", "fail", "warn")}
print("row4 forbidden substrings in new statement Constants:", {w: len(v) for w, v in bad.items()}, "constants=", len(allc))
cm = " ".join(ll[616:616+ins_n])
print("row4 (note, comment lines too):", {w: cm.lower().count(w) for w in ("nan", "inf", "error", "fail", "warn")})
# --- globals in the base
for name in ["AXFIX", "QADR", "VADR", "AIDX", "GIDX", "PAD", "TOOLB", "SIDES"]:
    ln = [s.lineno for s in bt.body if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in s.targets)]
    if name == "SIDES":
        ln += [s.lineno for s in bt.body if isinstance(s, ast.ImportFrom) and any(a.name == "SIDES" or a.asname == "SIDES" for a in s.names)]
    print(f"   base global {name}: lines {ln}")
# --- row 6 (reader): occurrences of the print prefix in the whole landed file
print("row6 'controller record' occurrences in landed (line numbers):", [i+1 for i, x in enumerate(ll) if "controller record" in x])
print("row6 RUN_METRICS lines identical:", [x for x in bl if "RUN_METRICS" in x] == [x for x in ll if "RUN_METRICS" in x], len([x for x in ll if "RUN_METRICS" in x]))
# --- row 8
py_compile.compile(land_p, doraise=True); print("row8 py_compile landed: ok")
```

## Appendix B — instrument outputs re-run at write time (verbatim)
```text
# re-run 2026-09-20 08:03:40 JST; blobs: base=a6a42f06a058c0ed landed=f461984bd7016a4e; git show at write time: d2bc133e1320 -> a6a42f06a058c0ed, 84a372439c59 -> f461984bd7016a4e (the stray command text that stood here was my echo-quoting slip, replaced by the measured values before commit)
## pz_b_pred v3 (sha 7079641ffe254ca3)
base/landed: PASS changed=[('For', 't in SIDES: print:[steps] controller record')] outside_allowed=[]
base/base:   PASS changed=[] outside_allowed=[]
landed literal flip :2147 (cmp differs=yes): FAIL changed=[('For', 't in SIDES: print:[steps] controller record'), ('FunctionDef', 'solve_ik')] outside_allowed=[('FunctionDef', 'solve_ik')]
landed + stray print: FAIL changed=[('Expr', 'print:stray'), ('For', 't in SIDES: print:[steps] controller record')] outside_allowed=[('Expr', 'print:stray')]
landed with B line twice: FAIL allowed statement not exactly once: [('For', 't in SIDES: print:[steps] controller record')] counts=[2]
## pz_ctrl2 (sha d10b4e5c614f5ac2)
3370f7a872: live-state writes 0 [] | d.ctrl writes 7 | control calls 27 (mj_step 11) | sequence 34 lines sha256 a1cf9bf78a568ab6
96e9ece175: live-state writes 0 [] | d.ctrl writes 7 | control calls 27 (mj_step 11) | sequence 34 lines sha256 a1cf9bf78a568ab6
## pz_b_rows.py (sha 89b0dd6f998da70d)
row1 top-level stmts base=292 landed=293 delta=1
row1 base: AXFIX idx=92 line=616, pinch idx=93 line=619, between=0
row1 landed: AXFIX idx=92 line=616, pinch idx=94 line=630, between=1
row1 new statements between AXFIX and pinch: 1 at lines [(621, 627)]
row1 line delta 11; prefix identical=True; suffix identical=True
row1 inserted lines 617..627: comment lines=4, code lines=7
row2 form For(t in SIDES) body=[Expr print] orelse=[]: True; print args=1 keywords=0
row2 first Constant startswith '[steps] controller record': True -> '[steps] controller record '
row3 FormattedValue count: 17
    AIDX[t] [('AIDX[t]', '', -1)]
    AXFIX[t] [('AXFIX[t][0][0]', '+.6f', -1), ('AXFIX[t][0][1]', '+.6f', -1), ('AXFIX[t][0][2]', '+.6f', -1), ('AXFIX[t][1][0]', '+.6f', -1), ('AXFIX[t][1][1]', '+.6f', -1), ('AXFIX[t][1][2]', '+.6f', -1), ('AXFIX[t][2][0]', '+.6f', -1), ('AXFIX[t][2][1]', '+.6f', -1), ('AXFIX[t][2][2]', '+.6f', -1)]
    GIDX[t] [('GIDX[t]', '', -1)]
    PAD[t] [('PAD[t]', '', -1)]
    QADR[t] [('QADR[t]', '', -1)]
    SIDES[t] [('SIDES[t]', '+.1f', -1)]
    TOOLB[t] [('TOOLB[t]', '', -1)]
    VADR[t] [('VADR[t]', '', -1)]
    t [('t', '', -1)]
row3 subscript set == pre-registered eight + t: True extra= set() missing= set()
row3 AXFIX cells: True all +.6f: True 9
row3 SIDES spec +.1f: ['+.1f']
row3 other fields no spec: {'QADR[t]': [''], 'VADR[t]': [''], 'AIDX[t]': [''], 'GIDX[t]': [''], 'PAD[t]': [''], 'TOOLB[t]': [''], 't': ['']}
row3 class literal present: True
row3 / 3' design literal: ['P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753'] == 'P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753': True
row4 forbidden substrings in new statement Constants: {'nan': 0, 'inf': 0, 'error': 0, 'fail': 0, 'warn': 0} constants= 28
row4 (note, comment lines too): {'nan': 0, 'inf': 0, 'error': 0, 'fail': 0, 'warn': 0}
   base global AXFIX: lines [616]
   base global QADR: lines [451]
   base global VADR: lines [452]
   base global AIDX: lines [449]
   base global GIDX: lines [450]
   base global PAD: lines [453]
   base global TOOLB: lines [471]
   base global SIDES: lines [145]
row6 'controller record' occurrences in landed (line numbers): [622]
row6 RUN_METRICS lines identical: True 6
row8 py_compile landed: ok
```
