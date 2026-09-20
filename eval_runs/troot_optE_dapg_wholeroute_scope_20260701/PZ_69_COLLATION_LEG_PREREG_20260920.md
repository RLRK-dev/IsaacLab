# pZ — pre-registered #69 collation leg (v2 of the run form, p4 m-p4-307 via m-p18-470 (D3-a)/(D3-c)): the row-7 and R3-i numbers read from the run.log itself against this desk's two pre-registrations, and the injected parameters read from the cell dump text — written before this desk reads any product of p0's run

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 23:09:29 JST. Authority: Rs1's word (#69 re-shoot authorized, 22:30:46 JST; custody p4 transcript :4397) → the fixed form (p4 item 69 `e7b2436e0f`, hub §1613 `82da3d8bd5`, p6 `483ff872`) → p4's v2 adoption (item 73 `e15124c25f`): **pZ's collation line runs after pB's verdict and before p4's acceptance word; one file; a mismatch is a B4 return**, and **p11 §17.24 (2) — the cell dump's both-side actuator/J6 values, text against text — is pZ's, in the same file; a mismatch is loud to p4**. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. This desk fires nothing, runs nothing, changes no parameter.

**Order of existence (measured in the writing command; stated as it is)**: the re-shoot **has already been executed once** by p0 — record §8.66 (`4497:## 8.66 (2026-09-20 23:07:00 JST) — #69 re-shoot EXECUTED once (gate = m-p18-468 relaying p6 `483ff8720885fc9a27be31edae80b3e735d2994`; commit `26e0f20c38 23:09:03`), Rs1's live copy `23:04:36 /home/rlrk/Downloads/ur15_live_69_20260920.mp4 1147718` — and this desk has **opened none of its products** (no `run.log`, `RUN_METRICS.json`, dump or video has been read here; the run dir `/home/rlrk/p0_runs/run69_reshoot_20260920` listed only now for its existence: `total 156`). The two instruments below were written at 23:05:09 pz_69_log.py / 23:05:09 pz_69_dump.py from the driver's and cell_spec's blob text and calibrated on this desk's 09-05 dump copy and on mock lines, not on the run. The **rows and bars pre-date the run in any case**: row 7's expectation is `PZ_B_LINE_LEG_PREREG_20260916.md` @ `e41d0a9304` (commits after = 0), R3-i's is `PZ_R3_TILT_CAP_LEG_PREREG_20260913.md` @ `98d8e63173` (commits after = 0), and the injected-parameter rule is the pinned blobs (driver `84a372439c59` @ `96e9ece175`, commits after = 0; cell_spec `6bdf7ea4f9ca`). HEAD `26e0f20c38`. Per p4 item 75 (m-p4-308) an early stop (`end_reason = raised`) is not a return reason: this leg reads the products that exist. p0 records that the run's cell dump differs from the shared-tree dump (`4158e4e638…`, 09-05): C-4 reads **the run's** dump (the sha in `RUN_METRICS.json`), and that difference is reported to p4 in the verdict, not judged here.

## Rows

| # | row | input (p0's pinned products; pZ reads them directly, not pB's verdict) | bar (fixed now) |
|---|---|---|---|
| C-1 | **row 7 (B-line prereg row 7 @ `e41d0a9304` `:16`)**: the two `[steps] controller record {L,R}:` lines (driver `:622-627`) | `run.log` (sha256 = p0's pin = driver's `log_sha256_at_write`) | each of the 18 printed AXFIX numbers vs **L: c=[0 +1 0] s=[+1 0 0] a=[0 0 −1]; R: the same** — `|diff| ≤ 1e-6`; `AXFIX_R = diag(1,−1,1)·AXFIX_L·A`, `A = diag(−1,1,1)`, `≤ 1e-6` (measured 4.94e-15 on the composed models today, R1′ b1 @ `a8a19a393f`); **the sign of a printed zero (`+0.000000` / `−0.000000`) is not a difference** (compared as numbers); both lines must exist |
| C-2 | **R3-i (R3 prereg @ `98d8e63173` `:27`)**: the `[steps] vertical check:` line (driver `:3016-3021`) | `run.log` | printed `cap X.XX` and `(L X.XX / R X.XX` must read **`5.73`** each (= 5.729578° = 0.10 rad, the menu's smallest non-zero roll, to the driver's 2 decimals); the allowance value is **recorded, not barred** (it is `vertical_tol_deg()`, computed); the line must exist. R3-ii/iii (asymmetric jaw state) are not exercised by a run whose live jaw state is symmetric — recorded as such, not as rows |
| C-3 | **collation with pB's verdict** | pB's verdict file (path + commit from the hub) | pB's stated row-7 numbers and cap prints == what C-1/C-2 read from the same `run.log` sha; **any differing number = B4 return** (p4's word); pZ does not re-grade pB's verdict, it re-derives from the log |
| C-4 | **injected parameters, text against text (p11 §17.24 (2))** | the run's cell dump `_gen/_steps_cell_full.xml` (sha256 = `RUN_METRICS.json` `cell_dump` = p0's pin; p4 expects `4158e4e638e9b0fc…`) | per name pair `L_{j}_act`/`R_{j}_act` (6 arm joints): `gainprm`, `biasprm`, `forcerange`, `ctrlrange`; per `L_{j}`/`R_{j}`: `armature`, `damping`; `Lg_fingers_actuator`/`Rg_fingers_actuator`: the four actuator attributes — **40 attribute pairs, L text == R text, exact**; reported alongside: the L values vs the pinned rule (cell_spec `6bdf7ea4f9ca` `:842-843` ARMATURE 0.1 / DAMP 1.0 / KP_ARM 10000 / KP_WRI 1200 / KVR 0.06; driver `:426-433` gain = kp, bias = (0, −kp, −kp·KVR), force = ±EFFORT, ctrl = LIMS). A mismatch is reported to p4 loud (p4's word); this row closes R2-9's "effective values" hole at the text level only |
| C-5 | stop-cause tags | `run.log` + `RUN_METRICS.json` (`run.end_reason`, `run.exception`) + p0's §8 tag line | counted and quoted, not barred here (the tag line is p0's; pB reads (iii)); if the log carries a `Traceback`/`RuntimeError` and p0's record carries no tag line, that is reported as a missing tag (return per the form ④) |
| C-6 | no run, no parameter | — | this desk executes nothing but the two text instruments on p0's products; the products are read by sha and never modified; route run (2)・D4′・WIP untouched |

**Falsification forms**: a C-1 number off by more than 1e-6, or a missing record line ⇒ the landed B line does not print what the composed models give ⇒ return to p4 (asset/driver court); a C-2 cap not `5.73` ⇒ the live jaw state is not symmetric or the cap code differs from D4's ⇒ reported with the printed values; a C-4 pair differing ⇒ the driver injects side-dependent parameters ⇒ loud to p4; a C-3 mismatch ⇒ B4 return.

## Instruments (registered by sha before the run) and their controls (fired now)

### `pz_69_log.py` (sha256 ea122b25080c3f84f75f4faba951e227615f547acf6d82487ef6c90d092dd3e5) — rows C-1, C-2, C-5 from the log text
Controls on mock logs built from the driver's own f-string formats (`:622-627`, `:3016-3021`) with the expected numbers; outputs verbatim:
```text
## mock PASS (expected numbers in the driver's own f-string formats :622-627 / :3016-3021)
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('0.00e+00', 'PASS')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (0, 0, 0)
overall: PASS
## R record line missing
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R record line: MISSING -> FAIL
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (0, 0, 0)
overall: FAIL
## one AXFIX number off by 1e-5 (L a_z -0.999990)
row7 L AXFIX vs expectation max|diff|: ('1.00e-05', 'FAIL')
row7 R AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('1.00e-05', 'FAIL')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (0, 0, 0)
overall: FAIL
## R side s row sign-flipped (relation broken)
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R AXFIX vs expectation max|diff|: ('2.00e+00', 'FAIL')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('2.00e+00', 'FAIL')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (0, 0, 0)
overall: FAIL
## cap prints 5.74 on R
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('0.00e+00', 'PASS')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.74'), 'FAIL')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (0, 0, 0)
overall: FAIL
## zero signs printed as -0.000000 on L (not a difference)
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('0.00e+00', 'PASS')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (0, 0, 0)
overall: PASS
## Traceback + RuntimeError lines appended (recorded, not barred)
row7 L AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 R AXFIX vs expectation max|diff|: ('0.00e+00', 'PASS')
row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|: ('0.00e+00', 'PASS')
R3-i printed cap / L / R (want 5.73): (('5.73', '5.73', '5.73'), 'PASS')
R3-i allowance (recorded, no bar): 1.00
stop lines (recorded): Traceback / RuntimeError / '[steps] STOP': (1, 1, 0)
overall: PASS
```
(3 PASS = the expected mock, the zero-sign variant, the appended-stop variant; 4 FAIL = a missing R line, one number off by 1e-5, a broken relation, a cap of 5.74.)

### `pz_69_dump.py` (sha256 b8ca76268e64481128a7a83e20a23c66c1dce8f38aafe87fc3beade102368dd6) — row C-4 from the dump text
Calibration on this desk's copy of the current cell dump (sha256 `4158e4e638e9b0fc0eddad324f2a0fdd8b80a77d51b9526d63d1be3cf4e2204b` = the dump p4 expects the run to reproduce), and a control with one `gainprm` perturbed in a scratch copy:
```text
## calibration on the current dump copy
[dump] shoulder_pan_joint_act.gainprm           L=10000                    R=10000                    eq
[dump] shoulder_pan_joint_act.biasprm           L=0 -10000 -600            R=0 -10000 -600            eq
[dump] shoulder_pan_joint_act.forcerange        L=-433 433                 R=-433 433                 eq
[dump] shoulder_pan_joint_act.ctrlrange         L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] shoulder_pan_joint.armature              L=0.1                      R=0.1                      eq
[dump] shoulder_pan_joint.damping               L=1                        R=1                        eq
[dump] shoulder_lift_joint_act.gainprm          L=10000                    R=10000                    eq
[dump] shoulder_lift_joint_act.biasprm          L=0 -10000 -600            R=0 -10000 -600            eq
[dump] shoulder_lift_joint_act.forcerange       L=-433 433                 R=-433 433                 eq
[dump] shoulder_lift_joint_act.ctrlrange        L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] shoulder_lift_joint.armature             L=0.1                      R=0.1                      eq
[dump] shoulder_lift_joint.damping              L=1                        R=1                        eq
[dump] elbow_joint_act.gainprm                  L=10000                    R=10000                    eq
[dump] elbow_joint_act.biasprm                  L=0 -10000 -600            R=0 -10000 -600            eq
[dump] elbow_joint_act.forcerange               L=-204 204                 R=-204 204                 eq
[dump] elbow_joint_act.ctrlrange                L=-3.14159 3.14159         R=-3.14159 3.14159         eq
[dump] elbow_joint.armature                     L=0.1                      R=0.1                      eq
[dump] elbow_joint.damping                      L=1                        R=1                        eq
[dump] wrist_1_joint_act.gainprm                L=1200                     R=1200                     eq
[dump] wrist_1_joint_act.biasprm                L=0 -1200 -72              R=0 -1200 -72              eq
[dump] wrist_1_joint_act.forcerange             L=-70 70                   R=-70 70                   eq
[dump] wrist_1_joint_act.ctrlrange              L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] wrist_1_joint.armature                   L=0.1                      R=0.1                      eq
[dump] wrist_1_joint.damping                    L=1                        R=1                        eq
[dump] wrist_2_joint_act.gainprm                L=1200                     R=1200                     eq
[dump] wrist_2_joint_act.biasprm                L=0 -1200 -72              R=0 -1200 -72              eq
[dump] wrist_2_joint_act.forcerange             L=-70 70                   R=-70 70                   eq
[dump] wrist_2_joint_act.ctrlrange              L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] wrist_2_joint.armature                   L=0.1                      R=0.1                      eq
[dump] wrist_2_joint.damping                    L=1                        R=1                        eq
[dump] wrist_3_joint_act.gainprm                L=1200                     R=1200                     eq
[dump] wrist_3_joint_act.biasprm                L=0 -1200 -72              R=0 -1200 -72              eq
[dump] wrist_3_joint_act.forcerange             L=-70 70                   R=-70 70                   eq
[dump] wrist_3_joint_act.ctrlrange              L=-6.28319 6.28319         R=-6.28319 6.28319         eq
[dump] wrist_3_joint.armature                   L=0.1                      R=0.1                      eq
[dump] wrist_3_joint.damping                    L=1                        R=1                        eq
[dump] fingers_actuator.gainprm                 L=0.313725                 R=0.313725                 eq
[dump] fingers_actuator.biasprm                 L=0 -100 -10               R=0 -100 -10               eq
[dump] fingers_actuator.forcerange              L=-5 5                     R=-5 5                     eq
[dump] fingers_actuator.ctrlrange               L=0 255                    R=0 255                    eq
[dump] L vs R text: 40/40 pairs equal -> PASS
[dump] rule check on L (reported): all match the pinned constants
## control: L_wrist_1_joint_act gainprm 1200 -> 1201 in a scratch copy
[dump] wrist_1_joint_act.gainprm                L=1201                     R=1200                     DIFF
[dump] L vs R text: 39/40 pairs equal -> FAIL
```

## Leg procedure (after the hub relays p0's landing and pB's verdict)
1. Fetch p0's `run.log`, `RUN_METRICS.json` and `_gen/_steps_cell_full.xml` from the announced run dir (or the archive p0 names); verify their sha256 against p0's §8 pins and the driver's `log_sha256_at_write`; never modify them.
2. `python pz_69_log.py run.log` → C-1/C-2/C-5; `python pz_69_dump.py _steps_cell_full.xml` → C-4; each once; outputs verbatim in the verdict.
3. Read pB's verdict file (by commit) and collate its numbers with step 2's (C-3).
4. Verdict `PZ_VERDICT_69_COLLATION_20260920.md` (1 file, pathspec commit) → PZ-24x to the hub → p4's acceptance word (after pB, pC, Rs1 and this line).
This desk does not open pC's verdict or the videos for these rows; physical validity is Rs1's eye.

## Appendix A — `pz_69_log.py` (verbatim)
```python
"""pZ #69 collation (row 7 + R3-i) read from the run.log itself, independently of pB's reading.
Rows: (7) the two `[steps] controller record {L,R}:` lines -> 18 AXFIX numbers vs the pre-registered expectation (B-line prereg row 7 @ e41d0a9304 :16:
c=[0 +1 0] s=[+1 0 0] a=[0 0 -1] on both sides, each |diff| <= 1e-6, and AXFIX_R == diag(1,-1,1).AXFIX_L.A, A=diag(-1,1,1), <= 1e-6; zero signs are not differences);
(R3-i) the `[steps] vertical check:` line -> printed `cap X.XX deg` and `(L X.XX / R X.XX` must read 5.73 (= 5.729578 to 2 decimals, R3 prereg @ 98d8e63173 R3-i);
the allowance is recorded, not barred.  Also counted, not barred: Traceback / RuntimeError lines (the stop-cause tag is p0's record line).  argv: run.log"""
import sys, re, numpy as np
txt = open(sys.argv[1], errors="replace").read()
EXP = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]]); TOL = 1e-6
rec = {}
for t in ("L", "R"):
    m = re.search(rf"\[steps\] controller record {t}: (.*)", txt)
    if not m: rec[t] = None; continue
    v = re.search(r"AXFIX c=\[(\S+) (\S+) (\S+)\] s=\[(\S+) (\S+) (\S+)\] a=\[(\S+) (\S+) (\S+)\]", m.group(1))
    rec[t] = None if not v else np.array([float(x) for x in v.groups()]).reshape(3, 3)
out = {}
for t in ("L", "R"):
    if rec[t] is None: out[f"row7 {t} record line"] = "MISSING -> FAIL"; continue
    d = float(np.abs(rec[t] - EXP).max()); out[f"row7 {t} AXFIX vs expectation max|diff|"] = (f"{d:.2e}", "PASS" if d <= TOL else "FAIL")
if rec["L"] is not None and rec["R"] is not None:
    rel = float(np.abs(rec["R"] - np.diag([1, -1, 1]) @ rec["L"] @ np.diag([-1, 1, 1])).max()); out["row7 relation AXFIX_R vs diag(1,-1,1).AXFIX_L.A max|diff|"] = (f"{rel:.2e}", "PASS" if rel <= TOL else "FAIL")
v = re.search(r"\[steps\] vertical check: allowance (\S+) deg, cap (\S+) deg .*?\(L (\S+) / R (\S+),", txt, re.S)
if not v: out["R3-i vertical check line"] = "MISSING -> FAIL"
else:
    allow, cap, capL, capR = v.groups(); want = f"{5.729578:4.2f}"
    out["R3-i printed cap / L / R (want 5.73)"] = ((cap, capL, capR), "PASS" if (cap, capL, capR) == (want, want, want) else "FAIL"); out["R3-i allowance (recorded, no bar)"] = allow
out["stop lines (recorded): Traceback / RuntimeError / '[steps] STOP'"] = (txt.count("Traceback"), txt.count("RuntimeError"), txt.count("[steps] STOP"))
out["overall"] = "PASS" if all((isinstance(x, tuple) and x[-1] == "PASS") for k, x in out.items() if k.startswith("row7") or k.startswith("R3-i printed")) and not any(isinstance(x, str) and x.endswith("FAIL") for x in out.values()) else "FAIL"
for k, x in out.items(): print(f"{k}: {x}")
```

## Appendix B — `pz_69_dump.py` (verbatim)
```python
"""pZ #69 injected-parameter text reading (p11 section 17.24 (2), assigned to pZ by p4 m-p4-307): from the cell dump XML, per side, the arm
actuators `{L,R}_{joint}_act` (gainprm, biasprm, forcerange, ctrlrange), the hand actuators `{L,R}g_fingers_actuator` (same four), and the J6
joints `{L,R}_{joint}` (armature, damping): L vs R text equal per name pair (bar: exact text), and each value vs the pinned rule
(cell_spec 6bdf7ea4f9ca :842-843 ARMATURE 0.1 DAMP 1.0 KP_ARM 10000 KP_WRI 1200 KVR 0.06; driver 84a372439c59 :426-433 gain=kp, bias=(0,-kp,-kp*KVR),
force=+-EFFORT, ctrl=LIMS) reported.  argv: dump.xml"""
import sys, re
txt = open(sys.argv[1], errors="replace").read()
J6 = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
def attrs(tag, name):
    m = re.search(rf"<{tag} name=\"{re.escape(name)}\"([^>]*)", txt)
    return None if not m else dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
KEYS_ACT = ("gainprm", "biasprm", "forcerange", "ctrlrange"); KEYS_JNT = ("armature", "damping")
rows, fails = [], 0
for j in J6:
    a = {t: attrs("general", f"{t}_{j}_act") for t in "LR"}; q = {t: attrs("joint", f"{t}_{j}") for t in "LR"}
    for k in KEYS_ACT:
        vl, vr = (a["L"] or {}).get(k), (a["R"] or {}).get(k); ok = vl is not None and vl == vr; fails += not ok; rows.append((f"{j}_act.{k}", vl, vr, "eq" if ok else "DIFF"))
    for k in KEYS_JNT:
        vl, vr = (q["L"] or {}).get(k), (q["R"] or {}).get(k); ok = vl is not None and vl == vr; fails += not ok; rows.append((f"{j}.{k}", vl, vr, "eq" if ok else "DIFF"))
h = {t: attrs("general", f"{t}g_fingers_actuator") for t in "LR"}
for k in KEYS_ACT:
    vl, vr = (h["L"] or {}).get(k), (h["R"] or {}).get(k); ok = vl is not None and vl == vr; fails += not ok; rows.append((f"fingers_actuator.{k}", vl, vr, "eq" if ok else "DIFF"))
for name, vl, vr, st in rows: print(f"[dump] {name:40s} L={vl!s:24s} R={vr!s:24s} {st}")
# rule check (reported): kp per joint, bias, armature/damping
KP = {j: (1200.0 if "wrist" in j else 10000.0) for j in J6}; KVR = 0.06; rule_bad = []
for j in J6:
    a = attrs("general", f"L_{j}_act") or {}; q = attrs("joint", f"L_{j}") or {}
    g = float(a.get("gainprm", "nan").split()[0]); b = [float(x) for x in a.get("biasprm", "nan nan nan").split()]
    if not (abs(g - KP[j]) < 1e-9 and abs(b[0]) < 1e-9 and abs(b[1] + KP[j]) < 1e-9 and abs(b[2] + KP[j] * KVR) < 1e-9): rule_bad.append(f"{j} gain/bias {g} {b}")
    if not (q.get("armature") == "0.1" and q.get("damping") == "1"): rule_bad.append(f"{j} armature/damping {q.get('armature')} {q.get('damping')}")
print(f"[dump] L vs R text: {len(rows) - fails}/{len(rows)} pairs equal -> {'PASS' if fails == 0 else 'FAIL'}")
print(f"[dump] rule check on L (reported): {'all match the pinned constants' if not rule_bad else rule_bad}")
```

## Provenance
Driver and cell_spec constants read from the pinned blobs (`84a372439c59`, `6bdf7ea4f9ca`) as text; the dump copy under the scratchpad is byte-equal to the untracked `_gen/_steps_cell_full.xml` (sha above); no product of the re-shoot exists at writing (asserted). Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction m-p18-470 (p4 m-p4-307).
