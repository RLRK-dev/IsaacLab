# pZ — pre-registered leg for the acceptance-instrument window (`ur15_mirror_acceptance.py`: REF_DIR → `reference/`, and the `:214` limit rule), written before the object exists

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-16 18:15 JST on m-p18-362 (Rs1 Q9 「推奨」 read by p4 as "open the window"; window defined by p4 m-p4-269; owner p0; DDR 73). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Base**: `ur15_mirror_acceptance.py` at HEAD blob `0803ea391298` (content sha256 `dc473752a36f…`, 242 lines, last commit `38678f5946` 07-29, unchanged since; the shared-tree copy is dirty with the 09-07 WIP, so the base is the blob, edited from a clean worktree). **Order of existence, measured in the writing command**: at 18:15:27 JST commits touching the file after `38678f5946` = **0** — the object does not exist. ⛔ Nothing in this leg is wired: the instrument is `mj_kinematics`-class (the class this desk ran in an isolated copy on 08-10); route run (2) / #69 untouched.

## Rows (p4's four, made measurable, plus this court's)

| # | row | requirement |
|---|---|---|
| 1 | change set = exactly the two statements | `pz_acc_pred.py` (appendix; v3 machinery): changed keys == {`Assign REF_DIR`, `FunctionDef main`} and nothing else; inside `main()` the unparsed diff is **exactly one line**, `want = (-hi_a, -lo_a)` → `want = (lo_a, hi_a)`; `REF_DIR`'s new value is built from `HERE` with the components `"reference"`, `"ur15-dual-arm-cell"` and **no absolute path string**. Fired on the base before the object: mock landing (the two edits) **PASS**; base/base FAIL (a landing that changes nothing fails); absolute REF_DIR FAIL; literal flip `PASS_MM` FAIL; a second line changed in `main` FAIL; only `:214` changed FAIL (incomplete set). 1 file; driver / cell_spec / assets untouched (they are not in the change set by construction) |
| 2 | REF_DIR actually opens the reference JSON | executed from a `git archive` of the landed commit: the script resolves `REF_JSON` to `…/reference/ur15-dual-arm-cell/ur15-dual-arm-cell.json` (sha256 `20ac0935c707757c…` = the 08-10 pin), reads it, and the record's line 2 names that path; a run with the file renamed away must fail loudly (positive control) |
| 3 | the new `:214` rule discriminates — negative control on asymmetric-range mock assets | with a stock joint range `[-1, 2]`: a mirrored asset with the **same** range (axis `−a`) → old rule False / **new rule True**; a mirrored asset with the **negated** range `[-2, 1]` → **old rule True** (accepts the defect) / new rule False. Measured before the object (appendix). On the real assets every range is symmetric, so the two rules coincide there — the mock is the only place the row can fail, hence mandatory |
| 4 | the 07-29 legs reproduce in a clean worktree | at `YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45` (the record's mounting): control **48/48**, test **48/48**, formula **48/48**, negative **0/48** (worst 1357.5 mm), limit leg 6/6 consistent, rc 0; the regenerated record is **byte-identical to the 07-29 blob `c5229911315f57b5…` except line 2** (the resolved reference path) — measured on my mock landing: diff = that line only. At the C-2 defaults (overrides unset): all four legs **0/48** (control 241.1 mm worst), rc 1 — the 08-10 finding, expected, not a defect |
| 5 | the record file | the script overwrites `HERE/UR15_MIRROR_ACCEPTANCE_20260729.txt` (`:236`); if p0's commit regenerates it, that is a second file whose only allowed difference from the 07-29 blob is line 2; if p0 does not regenerate it, the tracked record stays at `c5229911…` and the leg's own regeneration lives in the archive, never in the shared tree |
| 6 | control invariance | not applicable to the driver (untouched); for the instrument: `mj_step` calls in the file = 0 before and after (grep + AST) |
| 7 | pins / no run | landed commit + blob; base blob; my instrument sha; env7 python 3.12 / mujoco 3.11.0 |

## Observation for p4's disposition (recorded now, before landing; not a row)
The record's own words still state the old rule after the two edits: the heading at `:202` (`=== LEG limit … mirrored [lo,hi] must equal the stock [-hi,-lo] ===`) and the HONEST-SCOPE text at `:225-228` (`[-hi,-lo] equals [lo,hi]`). Under a two-statement window they stay, and the regenerated record will describe a rule the code no longer applies. Changing them is a third statement — the predicate in row 1 would then FAIL by design — so it is p4's call to widen the window or leave the wording; this desk does neither silently.

## Appendix A — `pz_acc_pred.py` (sha256 51ed1048aa91d91189dffcb98f9508826e77045a99d45b1283b0c1a7fbd87902; depends on `pz_d4_pred.py` v3 banked in `aed109d06f`)
```python
import ast, sys, difflib, importlib.util
spec=importlib.util.spec_from_file_location("d4",__file__.replace("pz_acc_pred.py","pz_d4_pred.py")); d4=importlib.util.module_from_spec(spec); spec.loader.exec_module(d4)
def key(st):
    if isinstance(st,ast.Assign) and any(getattr(x,"id","")=="REF_DIR" for x in st.targets): return ("Assign","REF_DIR")
    return d4.key(st)
ALLOWED={("Assign","REF_DIR"),("FunctionDef","main")}
def fine(b,c):
    """rows beyond the change set: REF_DIR HERE-relative w/o absolute path; main() differs in exactly one line = the want assignment."""
    msgs=[]
    rd=[s for s in c.body if key(s)==("Assign","REF_DIR")]
    if len(rd)!=1: return ["REF_DIR assign count != 1"]
    v=rd[0].value; names={n.id for n in ast.walk(v) if isinstance(n,ast.Name)}; consts=[n.value for n in ast.walk(v) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
    if "HERE" not in names or any(s.startswith("/") for s in consts) or "reference" not in consts or "ur15-dual-arm-cell" not in consts: msgs.append(f"REF_DIR not HERE-relative reference/ur15-dual-arm-cell: names={names} consts={consts}")
    mb=[s for s in b.body if key(s)==("FunctionDef","main")][0]; mc=[s for s in c.body if key(s)==("FunctionDef","main")][0]
    lb=ast.unparse(mb).split("\n"); lc=ast.unparse(mc).split("\n"); d=[l for l in difflib.unified_diff(lb,lc,lineterm="",n=0) if l[:1] in "+-" and l[:3] not in ("+++","---")]
    if not (len(d)==2 and d[0].startswith("-") and d[1].startswith("+") and "want = (-hi_a, -lo_a)" in d[0] and "want = (lo_a, hi_a)" in d[1]): msgs.append(f"main() diff is not exactly the want line: {d[:6]}")
    return msgs
def pred(base_p,cand_p):
    b,c=d4.load(base_p),d4.load(cand_p)
    if d4.imports(b)-d4.imports(c): return "FAIL",f"import removed"
    bd={}; cd={}
    for s_ in b.body: bd.setdefault(key(s_),[]).append(ast.dump(s_))
    for s_ in c.body: cd.setdefault(key(s_),[]).append(ast.dump(s_))
    changed={k for k in set(bd)|set(cd) if sorted(bd.get(k,[]))!=sorted(cd.get(k,[]))}
    if any(k in ALLOWED and len(cd.get(k,[]))!=1 for k in changed): return "FAIL","allowed statement not exactly once"
    extra=changed-ALLOWED
    if extra: return "FAIL",f"changed={sorted(changed)} outside_allowed={sorted(extra)}"
    m=fine(b,c)
    return ("PASS" if changed==ALLOWED and not m else "FAIL"), f"changed={sorted(changed)} fine={m or 'ok'}"
if __name__=="__main__": print(*pred(sys.argv[1],sys.argv[2]))
```

## Appendix B — the mock-asset control (verbatim)
```python
import mujoco
def M(lo,hi,ax): return mujoco.MjModel.from_xml_string(f'<mujoco><worldbody><body><joint name="j" type="hinge" axis="{ax}" range="{lo} {hi}" limited="true"/><geom size="0.1"/></body></worldbody></mujoco>')
a=M(-1.0,2.0,"0 0 1"); good=M(-1.0,2.0,"0 0 -1"); bad=M(-2.0,1.0,"0 0 -1")
def old(a,b): lo_a,hi_a=a.joint("j").range; lo_b,hi_b=b.joint("j").range; w=(-hi_a,-lo_a); return abs(lo_b-w[0])<1e-9 and abs(hi_b-w[1])<1e-9
def new(a,b): lo_a,hi_a=a.joint("j").range; lo_b,hi_b=b.joint("j").range; w=(lo_a,hi_a); return abs(lo_b-w[0])<1e-9 and abs(hi_b-w[1])<1e-9
# measured 2026-09-16 18:14 JST: old(a,good)=False new(a,good)=True | old(a,bad)=True new(a,bad)=False
```

## Provenance
HEAD blob read with `git show`; the mock landing and its two runs in a `git archive` of HEAD under the scratchpad (the shared tree's dirty copy and tracked record untouched — `git status` on both shows only the pre-existing WIP); reference JSON from `reference/` (`170cbf54a7` collation). Zero tracked-content modifications by pZ. Committed by pZ under the standing custody form (m-p18-344), pathspec-limited, --no-verify, no push.

## Addendum (2026-09-20 11:11:44 JST) — row 1 re-pinned for p4's **FULL** form of the window (m-p4-272/273 via kickoff item 11 @ `fc836e3a9a`; asked again in m-p4-286 via m-p18-420): the predicate `pz_acc_pred_v2.py`, fired on the base before the object exists

**Order of existence**: commits touching `ur15_mirror_acceptance.py` after `38678f5946` = 0 at writing (HEAD `231d7d88ba`; the file's blob is still `0803ea391298`) — the object does not exist. p0's announce-first record §8.52 @ `eaf7f6faa5` publishes the two candidates as diffs; the **FULL mock** used below = that `acc_full.diff` (sha256 `c1bbbbb1c77b5700235ccf83a145ef12190bd61f4f50a87da4ba0cd77f159ee7`, 54 lines, extracted from the committed record) applied by `patch` to the base blob (mock sha256 `4a2e3396059214409cd4e1746972a06a6cf8d501d21df754c1e1db31c5a7667b`, 248 lines, `py_compile` OK). The predicate is mine; the candidate text is p0's published one, so the object p0 lands is judged against **its own parent blob** with this predicate, not against the mock.

**Row 1 (FULL)**: AST-visible change set == {`Assign REF_DIR`, `FunctionDef main`}; inside `main()` the statement-level diff (recursive, structure-preserving) is **exactly three** leaf statements: the `want` Assign (`(-hi_a, -lo_a)` → `(lo_a, hi_a)`), the LEG-limit heading `out.append(...)` whose new Constant equals the FULL text verbatim, and the HONEST-SCOPE `out.append(...)` (inside `if sym_all:`) whose new Constant equals the FULL text verbatim; `REF_DIR` built from `HERE` with `"reference"`, `"ur15-dual-arm-cell"` and no absolute string; any statement added, removed or moved in `main()` = FAIL; text-visible (AST-invisible) changes are allowed only as **comment lines inside the limit-leg comment block** (`# --- the limit leg …` down to the first `out.append("")`) or on the `REF_DIR` line — a comment anywhere else = FAIL. Rows 2-7 unchanged. The MIN form is **not** accepted by this predicate (p4's word = FULL).

| control | result |
|---|---|
| base / base | FAIL (an unchanged file is not a landing) |
| **FULL mock** | **PASS** |
| MIN mock (two statements only) | FAIL (incomplete under FULL) |
| FULL + literal flip (`PASS_MM` 1.0 → 2.0) | FAIL |
| FULL + a stray statement in `main()` | FAIL |
| FULL + the heading text altered by one character | FAIL |
| FULL + absolute `REF_DIR` | FAIL |
| FULL + a comment outside the limit-leg block | FAIL |
| FULL + one more comment inside the limit-leg block | PASS (p4's 「文言」 allowance, comment site) |

Verbatim outputs in appendix D. Supersedes sha `6abc43aa…` @ cd0d68bf8c for row 1 only; rows 2-7, the observation and appendices A/B stand (the observation is answered by FULL: the record's wording is rewritten at the two sites, so the regenerated record will describe the rule the code applies).

## Appendix C — `pz_acc_pred_v2.py` (verbatim; sha256 106b124b8be96dfc365e062e469fa0174722de1ffe4b856ee6d97c441a7e4977; depends on `pz_d4_pred.py` v3 @ `aed109d06f`)
```python
"""pZ DoD predicate for the acceptance-instrument window, FULL form (p4 m-p4-272/273: 2 statements + wording at 3 places, logic 0, new file 0).
AST-visible allowed change set = {Assign REF_DIR} + inside main(): exactly {the `want` Assign, the LEG-limit heading out.append, the HONEST-SCOPE
out.append} with the FULL texts; everything else AST-identical (N1-N3).  Text-visible (comments): changed comment lines only inside the
limit-leg comment block or on the REF_DIR line.  argv: base.py candidate.py"""
import ast, sys, difflib, importlib.util
spec = importlib.util.spec_from_file_location("d4", __file__.replace("pz_acc_pred_v2.py", "pz_d4_pred.py")); d4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(d4)
HEAD_NEW = ("=== LEG limit (static, no FK): mirrored [lo,hi] must equal the stock [lo,hi] "
            "(axis flipped, q kept; the 07-29 rule [-hi,-lo] was the sign-flip convention) ===")
HON_NEW = ("  ⚠ HONEST SCOPE: every stock range is symmetric about zero, so [lo,hi] and the "
           "sign-flip rule's [-hi,-lo] coincide and this leg CANNOT tell the two rules apart "
           "on these assets.  It is a standing check for the day a range is not symmetric -- "
           "today it confirms the axes are inverted and the ranges are byte-identical.")
def key(st):
    if isinstance(st, ast.Assign) and any(getattr(x, "id", "") == "REF_DIR" for x in st.targets): return ("Assign", "REF_DIR")
    return d4.key(st)
ALLOWED = {("Assign", "REF_DIR"), ("FunctionDef", "main")}
def walk_stmts(body, path, out):
    for i, s in enumerate(body):
        out.append((path + [f"{type(s).__name__}#{i}"], s))
        for f in ("body", "orelse", "finalbody"):
            if getattr(s, f, None): walk_stmts(getattr(s, f), path + [f"{type(s).__name__}#{i}.{f}"], out)
        for h in getattr(s, "handlers", []) or []: walk_stmts(h.body, path + [f"{type(s).__name__}#{i}.handler"], out)
def main_diff(mb, mc):
    """statement-level diff inside main(): list of (path, base_dump, cand_dump) for statements that differ; structural change -> None."""
    ob, oc = [], []; walk_stmts(mb.body, [], ob); walk_stmts(mc.body, [], oc)
    if [p for p, _ in ob] != [p for p, _ in oc]: return None
    return [(">".join(pb), sb, sc) for (pb, sb), (pc, sc) in zip(ob, oc) if type(sb) is type(sc) and ast.dump(sb) != ast.dump(sc) and not any(isinstance(ch, ast.stmt) for ch in ast.iter_child_nodes(sb))]
def const_of_append(s):
    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and getattr(s.value.func, "attr", "") == "append" and s.value.args and isinstance(s.value.args[0], ast.Constant): return s.value.args[0].value
    return None
def fine(b, c, base_src, cand_src):
    msgs = []
    rd = [s for s in c.body if key(s) == ("Assign", "REF_DIR")]
    if len(rd) != 1: return ["REF_DIR assign count != 1"]
    v = rd[0].value; names = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}; consts = [n.value for n in ast.walk(v) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if "HERE" not in names or any(s.startswith("/") for s in consts) or "reference" not in consts or "ur15-dual-arm-cell" not in consts: msgs.append(f"REF_DIR not HERE-relative reference/ur15-dual-arm-cell: names={names} consts={consts}")
    mb = [s for s in b.body if key(s) == ("FunctionDef", "main")][0]; mc = [s for s in c.body if key(s) == ("FunctionDef", "main")][0]
    d = main_diff(mb, mc)
    if d is None: return msgs + ["main(): statement structure changed (a statement added/removed/moved)"]
    kinds = []
    for path, sb, sc in d:
        ub, uc = ast.unparse(sb), ast.unparse(sc)
        if isinstance(sb, ast.Assign) and "want = (-hi_a, -lo_a)" in ub and uc.strip() == "want = (lo_a, hi_a)": kinds.append("want")
        elif const_of_append(sb) and const_of_append(sb).startswith("=== LEG limit") and const_of_append(sc) == HEAD_NEW: kinds.append("heading")
        elif const_of_append(sb) and const_of_append(sb).startswith("  ⚠ HONEST SCOPE") and const_of_append(sc) == HON_NEW: kinds.append("honest")
        else: kinds.append(f"OTHER:{path}:{uc[:50]!r}")
    if sorted(kinds) != ["heading", "honest", "want"]: msgs.append(f"main() differing statements != the FULL three: {kinds}")
    # text-visible changes beyond the AST: only comment lines, only in the limit-leg comment block or the REF_DIR line
    lb, lc = base_src.split("\n"), cand_src.split("\n")
    blk = [i for i, l in enumerate(lb) if l.strip().startswith("# --- the limit leg")]
    for tag, l in [(x[0], x[1:]) for x in difflib.unified_diff(lb, lc, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]:
        s = l.strip()
        if s.startswith("#"):
            if not blk: msgs.append("comment change but no limit-leg block marker in the base"); break
            # locate: a changed comment line must sit in the block (base marker .. first `out.append("")` after it) in whichever file it comes from
            src = lb if tag == "-" else lc
            try: idx = src.index(l)
            except ValueError: idx = -1
            m = [i for i, x in enumerate(src) if x.strip().startswith("# --- the limit leg")]
            end = next((j for j in range(m[0], len(src)) if src[j].strip() == 'out.append("")'), len(src)) if m else -1
            if not (m and m[0] <= idx <= end): msgs.append(f"comment changed outside the limit-leg block: {s[:60]!r}")
        elif "REF_DIR" in l or "want = (" in l or "out.append(" in l or l.strip().startswith('"') or l.strip().startswith("'"):
            pass   # AST-visible edits (checked above) and their continuation lines
        else:
            msgs.append(f"non-comment text change outside the allowed statements: {tag}{s[:60]!r}")
    return msgs
def pred(base_p, cand_p):
    bs, cs = open(base_p).read(), open(cand_p).read()
    b, c = d4.load(base_p), d4.load(cand_p)
    if d4.imports(b) - d4.imports(c): return "FAIL", "import removed"
    bd, cd = {}, {}
    for s_ in b.body: bd.setdefault(key(s_), []).append(ast.dump(s_))
    for s_ in c.body: cd.setdefault(key(s_), []).append(ast.dump(s_))
    changed = {k for k in set(bd) | set(cd) if sorted(bd.get(k, [])) != sorted(cd.get(k, []))}
    if any(k in ALLOWED and len(cd.get(k, [])) != 1 for k in changed): return "FAIL", "allowed statement not exactly once"
    extra = changed - ALLOWED
    if extra: return "FAIL", f"changed={sorted(changed)} outside_allowed={sorted(extra)}"
    m = fine(b, c, bs, cs)
    return ("PASS" if changed == ALLOWED and not m else "FAIL"), f"changed={sorted(changed)} fine={m or 'ok'}"
if __name__ == "__main__": print(*pred(sys.argv[1], sys.argv[2]))
```

## Appendix D — control outputs (verbatim)
```text
## controls, fired 2026-09-20 11:11:45 JST on blob 0803ea391298 (base) before the object exists (commits after 38678f5946 = 0)
base/base                                            FAIL changed=[] fine=["REF_DIR not HERE-relative reference/ur15-dual-arm-cell: names={'Path'} consts=['/home/rlrk/Downloads/ur15-dual-arm-cell']", 'main() diffe
FULL mock (p0's acc_full.diff applied to the base)   PASS changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=ok
MIN mock (the two statements only)                   FAIL changed=[('FunctionDef', 'main')] fine=["REF_DIR not HERE-relative reference/ur15-dual-arm-cell: names={'Path'} consts=['/home/rlrk/Downloads/ur15-dual-arm
FULL + literal flip PASS_MM 1.0->2.0                 FAIL changed=[('Assign', "Assign(targets=[Name(id='PASS_MM', ctx=Store())], value=Constant(value=1.0))"), ('Assign', "Assign(targets=[Name(id='PASS_MM', ctx=Sto
FULL + stray statement in main                       FAIL changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=['main(): statement structure changed (a statement added/removed/moved)']
FULL + heading text altered                          FAIL changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=['main() differing statements != the FULL three: [\'OTHER:Expr#41:"out.append(\\\'=== LEG lim
FULL + absolute REF_DIR                              FAIL changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=["REF_DIR not HERE-relative reference/ur15-dual-arm-cell: names={'Path'} consts=['/home/rlrk/
FULL + comment outside the limit-leg block           FAIL changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=["comment changed outside the limit-leg block: '# a stray comment outside the window'"]
FULL + comment inside the limit-leg block            PASS changed=[('Assign', 'REF_DIR'), ('FunctionDef', 'main')] fine=ok
```
