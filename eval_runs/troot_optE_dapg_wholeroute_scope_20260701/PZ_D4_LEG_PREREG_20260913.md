# pZ — pre-registered leg for D4 (p11 v3 §6: the vertical-cap instrument made side-aware), written before the object exists

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-13 22:26 JST on m-p18-335 (p0's announce-first) and m-p18-329 (p11's pin). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Governing design** (read at this desk, not relayed): `P11_UR15B_CONTROLLER_DESIGN_20260913.md` @ `913811bbcf` (sha256 `5a416a78…88c0`, 202 lines) — §6 (D4 spec), §13 (DoD (b), landing order), §10 (rows R0–R4 offered; grade and bar are this court's). p4's disposition: consume v3 without a third cycle (m-p4-261, relayed m-p18-330).
**Order of existence, measured in the command that wrote this file**: at **22:26:58 JST** commits touching `ur15_steps_wired.py` after `22feba17a6` = **0**; HEAD's driver blob = **`75eefef4e27e`**. The D4 window word (Rs1 via p18) has not been given; p0's candidate lives in p0's scratch worktree only (m-p18-335). ⛔ Nothing runs from this desk; #69 stays unfired.
**Object (when it exists)**: the D4 commit, judged **against the driver blob it was built on** — `75eefef4e27e` (= HEAD's, content `57de8c3e…4a98`) unless the 09-07 WIP lands first, in which case the base is re-pinned to the WIP commit and the three predicate controls are re-fired on it before judging (v3 §13 (3)). p0's record section (§8.50 @ `1fe7c84bfc`) is read **after** the blob measurement and only for its stated reason.

## Rows

| # | row | requirement (measured by me from the commit; nothing from p0's message) |
|---|---|---|
| 1 | scope | 1 file (the wired driver); every hunk inside the base's `attitude_tilt_deg` (`:1263-1286`), `vertical_cap_deg` (`:1288-1326`) and the vertical-check print (`:2985-2988`); **everything else byte-identical** to the base, checked by direct line comparison delta-aligned (above `:1263`, between `:1327-2984`, below `:2989`) — this covers the E1 block `:41-140`, `CLIPG`, `solve_ik`, `pose_menu`, `_rdes`, `aim_*`, `release_ctrl`, servo, `R_DES`, `GRASP_ATTITUDES`, `LIM`, `AXFIX`, `SIDES`, the seat gate and the `VERTICAL_TOL_DEG` gate (v3 §6 "不変"). If Rs1 adopts §1 (A), one more `Expr` (the §7 identity print) is allowed and must be named |
| 2 | DoD (b) predicate — **my own implementation, not p0's** | `pz_d4_pred.py` (appendix A): N1 import-alias sort, N2 adjacent-Constant merge in f-strings, N3 placeholder-free f-string ≡ Constant; imports compared as **name sets, removal forbidden**; module-level statements keyed and compared; allowed changed set = {`FunctionDef attitude_tilt_deg`, `FunctionDef vertical_cap_deg`, `Expr print` whose first Constant starts with `[steps] vertical check`}. **Fired before the object existed, on the base `75eefef4e27e`**: base/base → PASS (changed ∅) · literal flip `:2118` 0.05→0.06 in `solve_ik` → **FAIL** · mock-D4 (both defs touched) → PASS · mock-D4 + stray edit of the E1 announce print → **FAIL** (`_write_run_metrics` caught) · N3 (f-ify a placeholder-free print `:167`) → PASS (invisible, as N3 requires). On the object: PASS **and** the changed set printed verbatim |
| 3 | control invariance — mechanical | `pz_ctrl2.py` (appendix B; AST): live-state writes to `d.qpos/qvel/qacc/act/xfrc/mocap` **0 → 0**; `d.ctrl` writes **7 → 7, same order**; `mj_step` call sites **11 → 11**; ordered control sequence **34 lines, sha256 `a1cf9bf78a568ab6`** on the base, unchanged on the commit. ⚠ New instrument: the 09-05 instrument's class list was never banked (only its outputs: 57 lines, `426aa229deb2cb2b`), so that number is not reproducible — its content invariants (0 / 7 / 11) are, and both instruments agree on them. Lesson applied here: both instruments are banked verbatim in the appendices |
| 4 | gate-inert (static) | the only consumer of `vertical_cap_deg()`'s return stays the print (base callers: internal `:1290/:1300/:1306` + print `:2988`); the existing no-argument call form still works and is what the print uses; no new reader of the cap anywhere (grep on the commit); the gate at `:3517` and `gates`/`_grow` are inside row 1's byte-identical regions |
| 5 | the fix's structure == v3 §6, read from the landed AST | `attitude_tilt_deg(t, yaw, roll)` reads side `t`'s `slot_centre`/`pinch`/`TOOLB`/`AXFIX`; `vertical_cap_deg` builds `upright_t`/`tilted_t` per side under `(SIDES[t]·yaw, SIDES[t]·roll)`, passes **both** calibration raises per side (upright ≤ `TILT_CAL_DEG`; min(tilted) ≥ `TILT_CAL_DEG`), selects on the **input** roll `abs(r) ≥ 1e-9`, `cap_t = min(tilted_t)`, returns `min` over sides; `SIDES` is the import at `:158`, no new literal side signs in `pose_menu`/`solve_ik` (row 1 already forbids touching them) |
| 6 | print contract | the new print's first Constant begins with the base's exact prefix `[steps] vertical check: allowance {VERTICAL_TOL_DEG:4.2f} deg, cap {…:4.2f} deg` (byte-compatible; the four verbatim citations keep reading); the appended tail carries `(L … / R …)`; **no new word contains** `nan`, `inf`, `error`, `fail`, `warn` as a substring (pB's grep, `log-analyzer/SKILL.md:95`); the RUN_METRICS writer is untouched (row 1) |
| 7 | numbers = R3, a separate leg | cap_L / cap_R / v_c are **not** judged by this leg: R3 = my independent tilt derivation on the composed model (`build_side` @ `b7a5e39ecf`, no driver import) against a printed line that exists only after an authorized run — stated **unmeasured** here, not implied |
| 8 | no run | `py_compile` of the landed blob is the only execution; no driver import; no `P4_*` env; #69 unfired; the L1 cell dump is not needed for this leg |
| 9 | pins | parent-relative on the named base blob; the commit's driver content sha named; the changed-set output and the three control outputs quoted in the verdict |

## Appendix A — `pz_d4_pred.py` (the DoD (b) predicate, verbatim)
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
    return (type(st).__name__, ast.dump(st)[:60])
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
    bd={key(s):ast.dump(s) for s in b.body}; cd={key(s):ast.dump(s) for s in c.body}
    changed={k for k in set(bd)|set(cd) if bd.get(k)!=cd.get(k)}
    extra=changed-ALLOWED
    return ("PASS" if not extra else "FAIL"), f"changed={sorted(changed)} outside_allowed={sorted(extra)}"
if __name__=="__main__": print(*pred(sys.argv[1],sys.argv[2]))
```

## Appendix B — `pz_ctrl2.py` (control invariance, verbatim)
```python
import ast, sys, hashlib, subprocess
rev, path = sys.argv[1], sys.argv[2]
src = subprocess.run(["git","show",f"{rev}:{path}"],capture_output=True,text=True,check=True).stdout
tree = ast.parse(src); lines = src.split("\n")
def tgt_txt(t): return ast.unparse(t)
writes=[]; calls=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.Assign,ast.AugAssign)):
        ts = n.targets if isinstance(n,ast.Assign) else [n.target]
        for t in ts:
            s=tgt_txt(t)
            if any(k in s for k in ("d.ctrl","d.qpos","d.qvel","d.qacc","d.act","d.xfrc","d.mocap")): writes.append((n.lineno,s))
    if isinstance(n,ast.Call):
        f=ast.unparse(n.func)
        if f in ("mujoco.mj_step","mujoco.mj_forward","mj_step","mujoco.mj_step1","mujoco.mj_step2","servo","set_ctrl","release_ctrl","solve_ik"): calls.append((n.lineno,f))
live=[w for w in writes if not w[1].startswith("d.ctrl")]; ctrl=[w for w in writes if w[1].startswith("d.ctrl")]
seq=sorted(set(writes)|set(calls)); txt="\n".join(f"{ln}:{lines[ln-1].strip()}" for ln,_ in seq)
norm="\n".join(lines[ln-1].strip() for ln,_ in seq)   # line-number-free, order-preserving
print(f"{rev}: live-state writes {len(live)} {sorted(set(s for _,s in live))} | d.ctrl writes {len(ctrl)} | control calls {len(calls)} (mj_step {sum(1 for _,f in calls if 'mj_step' in f)}) | sequence {len(seq)} lines sha256 {hashlib.sha256(norm.encode()).hexdigest()[:16]}")
```

## Provenance
`git show 22feba17a6:…/ur15_steps_wired.py` for the base (never imported); `git rev-parse HEAD:…` for the blob; the two scripts above under `/home/rlrk/env_isaaclab7/bin/python` 3.12; v3 read from `913811bbcf`. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian** (or, per m-p18-331's pin law, committed by me on the custodian's word — whichever the hub says).
