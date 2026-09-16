# pZ — pre-registered leg for the B line (per-side controller record print, v3 §17.2), written before the object exists

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-16 18:04 JST on m-p18-356 (p11 §17.2 @ `dc090f7753`; Rs1 Q2 = B, verbatim via m-p4-265). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Object (when it exists)**: p0's commit adding one statement to the wired driver. **Base** = the driver blob at landing time — today `d2bc133e1320` @ `3370f7a872` (driver commits after it at 18:04:59 JST = 0); re-pinned and the controls re-fired if the driver moves first. Separate window from D4 (p4 item 4); Rs1 Q8's condition is met by the window being separate.

## Rows

| # | row | requirement |
|---|---|---|
| 1 | placement + scope | exactly **one** new top-level statement, inserted **after** `AXFIX = _measure_axfix()` (base `:616`) and **before** `def pinch` (base `:619`); everything else byte-identical delta-aligned; 1 file |
| 2 | form (AST) | `For(target=Name 't', iter=Name 'SIDES', body=[Expr(Call print)], orelse=[])` — one body statement; the print's first Constant starts with `[steps] controller record` |
| 3 | fields (AST) | the print's FormattedValues read **exactly** the subscripts {`AXFIX[t]` (rows c/s/a, `%+.6f`), `QADR[t]`, `VADR[t]`, `AIDX[t]`, `GIDX[t]`, `PAD[t]`, `TOOLB[t]`, `SIDES[t]` (`%+.1f`)} plus `t` — all eight globals exist in the base (`:449-453`, `:471`, `:616`, `SIDES` imported `:158`); the class literal `existing per-arm 6D DLS + position servo` present; the design literal == `P11_UR15B_CONTROLLER_DESIGN_20260913.md@<hash>` where `<hash>` is the commit whose blob contains §17 (today `dc090f7753`; checked by `git show <hash>:…` containing the §17.2 field list) |
| 4 | forbidden substrings | no Constant of the new statement contains `nan`, `inf`, `error`, `fail`, `warn` |
| 5 | DoD predicate — my own, v3 | `pz_b_pred.py` (appendix B; depends on `pz_d4_pred.py` v3, appendix A): allowed set = {that `For`}; **fired on the base before the object exists**: base/base PASS · mock B line after `AXFIX` PASS · literal flip `:2136` FAIL · mock + stray print edit FAIL · mock with two body statements FAIL · two identical B lines FAIL (v1 of the instrument passed the last two — the holes are disclosed in the D4 verdict's addendum) |
| 6 | control invariance | `pz_ctrl2.py` (`cb787871f0` appendix B): live-state writes 0, `d.ctrl` 7, `mj_step` 11, 34-line sequence sha `a1cf9bf78a568ab6` unchanged; the RUN_METRICS writer untouched (row 1); no reader of the new print anywhere (record only) |
| 7 | runtime expectation (#69 only; pB reads the log) | the two printed `AXFIX` rows vs my composed-model values (seed `:600`, finger 0, tool frame ⇒ mount-independent): **L** c=[0 +1 0] s=[+1 0 0] a=[0 0 −1], **R** c=[0 +1 0] s=[+1 0 0] a=[0 0 −1], each of the 18 numbers ≤ **1e-6**, and `AXFIX_R = diag(1,−1,1)·AXFIX_L·A` ≤ 1e-6 (measured 4.9e-15). ⚠ compare as numbers: with `%+.6f` the zeros print as `+0.000000` or `−0.000000` depending on side; a text grep must not read the sign of a zero as a difference. The index ints are a record, not a bar (Rs1's reason) |
| 8 | no run | static rows only; `py_compile`; #69 unfired |

## Appendix A — `pz_d4_pred.py` v3 (sha256 0ba3c59b583b39d10620cd482b08825fce51a34b6157658996a7e527e2a96fe8)
```python
import ast, sys
ALLOWED={("FunctionDef","attitude_tilt_deg"),("FunctionDef","vertical_cap_deg"),("Expr","print:[steps] vertical check")}
class N(ast.NodeTransformer):
    def visit_JoinedStr(s,n):
        s.generic_visit(n); vals=[]
        for v in n.values:                       # N2: merge adjacent Constants
            if isinstance(v,ast.Constant) and vals and isinstance(vals[-1],ast.Constant): vals[-1]=ast.Constant(vals[-1].value+v.value)
            else: vals.append(v)
        n.values=vals
        if all(isinstance(v,ast.Constant) for v in vals): return ast.Constant("".join(v.value for v in vals))  # N3
        return n
    def visit_Import(s,n): n.names=sorted(n.names,key=lambda a:(a.name,a.asname or "")); return n   # N1
    def visit_ImportFrom(s,n): n.names=sorted(n.names,key=lambda a:(a.name,a.asname or "")); return n
def key(st):
    if isinstance(st,ast.FunctionDef): return ("FunctionDef",st.name)
    if isinstance(st,ast.Expr) and isinstance(st.value,ast.Call) and getattr(st.value.func,"id","")=="print":
        a=st.value.args; c=a[0] if a else None
        if isinstance(c,ast.JoinedStr): c=c.values[0] if c.values else None
        s=c.value if isinstance(c,ast.Constant) and isinstance(c.value,str) else ""
        return ("Expr","print:[steps] vertical check" if s.startswith("[steps] vertical check") else "print:"+s[:30])
    return (type(st).__name__, ast.dump(st))   # v2: FULL dump -- a 60-char prefix collided for module-level `for t in SIDES:` loops (dead query caught 2026-09-16 18:00)
def imports(tree):
    out=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import): out|={a.name for a in n.names}
        if isinstance(n,ast.ImportFrom): out|={f"{n.module}.{a.name}" for a in n.names}
    return out
def load(p):
    t=N().visit(ast.parse(open(p).read())); ast.fix_missing_locations(t); return t
def pred(base_p,cand_p):
    b,c=load(base_p),load(cand_p)
    if imports(b)-imports(c): return "FAIL",f"import removed: {imports(b)-imports(c)}"
    bd={}; cd={}   # v3: key -> list of dumps (duplicates count; an allowed statement must occur exactly once in the candidate)
    for s_ in b.body: bd.setdefault(key(s_),[]).append(ast.dump(s_))
    for s_ in c.body: cd.setdefault(key(s_),[]).append(ast.dump(s_))
    changed={k for k in set(bd)|set(cd) if sorted(bd.get(k,[]))!=sorted(cd.get(k,[]))}
    dup={k for k in changed if k in ALLOWED and len(cd.get(k,[]))!=1}
    if dup: return "FAIL",f"allowed statement not exactly once: {sorted(dup)} counts={[len(cd[k]) for k in sorted(dup)]}"
    extra=changed-ALLOWED
    return ("PASS" if not extra else "FAIL"),f"changed={sorted(changed)} outside_allowed={sorted(extra)}"
if __name__=="__main__": print(*pred(sys.argv[1],sys.argv[2]))
```

## Appendix B — `pz_b_pred.py` v3 (sha256 7079641ffe254ca3eb5708071e78b3e57ca8138b7342dd50d760f89dac0ef2d8)
```python
import ast, sys, importlib.util
spec=importlib.util.spec_from_file_location("d4",__file__.replace("pz_b_pred.py","pz_d4_pred.py")); d4=importlib.util.module_from_spec(spec); spec.loader.exec_module(d4)
def key(st):
    if isinstance(st,ast.For) and isinstance(st.target,ast.Name) and isinstance(st.iter,ast.Name) and st.iter.id=="SIDES" and len(st.body)==1 and isinstance(st.body[0],ast.Expr) and isinstance(st.body[0].value,ast.Call) and getattr(st.body[0].value.func,"id","")=="print":
        a=st.body[0].value.args; c=a[0] if a else None
        if isinstance(c,ast.JoinedStr): c=c.values[0] if c.values else None
        s=c.value if isinstance(c,ast.Constant) and isinstance(c.value,str) else ""
        return ("For", f"{st.target.id} in SIDES: print:[steps] controller record" if s.startswith("[steps] controller record") else "print:"+s[:30])
    return d4.key(st)
ALLOWED={("For","t in SIDES: print:[steps] controller record")}
def pred(base_p,cand_p):
    b,c=d4.load(base_p),d4.load(cand_p)
    if d4.imports(b)-d4.imports(c): return "FAIL",f"import removed: {d4.imports(b)-d4.imports(c)}"
    bd={}; cd={}   # v3: key -> list of dumps (duplicates count; an allowed statement must occur exactly once in the candidate)
    for s_ in b.body: bd.setdefault(key(s_),[]).append(ast.dump(s_))
    for s_ in c.body: cd.setdefault(key(s_),[]).append(ast.dump(s_))
    changed={k for k in set(bd)|set(cd) if sorted(bd.get(k,[]))!=sorted(cd.get(k,[]))}
    dup={k for k in changed if k in ALLOWED and len(cd.get(k,[]))!=1}
    if dup: return "FAIL",f"allowed statement not exactly once: {sorted(dup)} counts={[len(cd[k]) for k in sorted(dup)]}"
    extra=changed-ALLOWED
    return ("PASS" if not extra else "FAIL"),f"changed={sorted(changed)} outside_allowed={sorted(extra)}"
if __name__=="__main__": print(*pred(sys.argv[1],sys.argv[2]))
```

## Provenance
v3 §17.2 read at `dc090f7753`; the landed driver blob as text; my composed models (`98d8e63173` instrument). Zero tracked-content modifications by pZ. Committed by pZ under the standing custody form (m-p18-344), pathspec-limited, --no-verify, no push.

## Addendum (2026-09-16 18:08 JST) — p4's condition (ii): the design literal is fixed to `dc090f7753` (m-p4-268 via m-p18-360)

- **Row 3′**: the design literal in the B line must be **exactly** `P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753` — the first commit containing §17. Row 3's "the commit whose blob contains §17" is withdrawn as the binding form: after appends more than one commit contains §17, so that reading would not fix the hash; `dc090f7753` does (p4's reading, adopted). Verified at leg time by string equality of the Constant. Rows 1-8 otherwise unchanged; supersedes sha `e1204ef402089c2c…` @ aed109d06f. Objects at writing: none (driver commits after `3370f7a872` = 0).
