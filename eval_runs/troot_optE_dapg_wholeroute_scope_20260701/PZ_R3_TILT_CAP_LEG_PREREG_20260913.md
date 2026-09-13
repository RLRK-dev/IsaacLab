# pZ — pre-registered R3 (tilt-cap numbers, independent re-derivation) with the expectations computed before D4 exists

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-13 22:38 JST on m-p18-339 (p4: acceptance (iii) = pZ R3 incl. the side branches). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Rows offered** = v3 §10 R3 @ `913811bbcf`; grade and bar fixed here (this court). **Order of existence**: at **22:38:19 JST** commits touching the driver after `22feba17a6` = **0** — D4 has not landed; every number below was computed before it exists and is the expectation the landed code must meet. ⛔ No run; the driver was never imported — its lines are quoted as text (`:1263-1326`, `:594-616`, `:1329-1334`, `:619-621`, `:707-713`, `:453/:460/:471` @ `22feba17a6`); the composed model is built by the existing instrument `ur15_gripper_mirror_acceptance.py::build_side` (pin `b7a5e39ecf` == HEAD blob `17c79f596c…`), with `ur15_cell_spec` (pin `0f6b4a733e` == HEAD `d4f79856bd…`), from a `git archive` of HEAD (the shared-tree copies are dirty and were not read); assets `ur15_base.xml` `1e182d10…`, `ur15_base_mirrored.xml` `9d8700e3…`, ko `01861b95…` (disk == HEAD), mirrored ko from the archive. Env: python 3.12.3 mujoco 3.11.0; overrides unset (C-2 0.28 / 20°), and re-run at 0.22 / 45° for mount-independence.

## My derivation (from the quoted text, not from p0's or p11's arithmetic)

`AXFIX_t` rows = (c, s = a×c, a) in the tool frame, measured at the seed `[0, −1.2, 1.0, −1.4, −1.57, 0]` with fingers 0 (`:594-616`). `v_tool = R_tᵀ (slot_centre − pinch)`, normalized. `_rdes(y, r) = Rz(y)·Rz(π/2)·Ry(r)` (`:1329-1334`). With `(v_c, v_s, v_a) = AXFIX·v_tool`: `Ry(r)` gives `z = −v_c·sin r + v_a·cos r`, and `Rz` leaves z alone ⇒ **`tilt(r) = acos((v_c·sin ρ − v_a·cos ρ)/|v|)`, yaw-free, ρ = the roll the side receives** (`ρ = SIDES[t]·r`; `SIDES = {L: −1, R: +1}` spec `:485`). Measured: c ⟂ a to < 1e-4° on both sides, so `|v| = 1` and the clamp only absorbs 1e-16.

## Expectations (measured on the composed models; identical at both mountings)

| finger state (both hands) | v_c L / R | v_a L / R | cap, current formula (L data, raw r) | side-aware cap_L / cap_R / min | calibration (max upright / min tilted) L, R |
|---|---|---|---|---|---|
| symmetric, all 0 | −5e-16 / +2e-15 | −1.000000 / −1.000000 | **5.729578** | **5.729578 / 5.729578 / 5.729578** (Δ 1.3e-13) | 0.00 / 5.730, 0.00 / 5.730 |
| symmetric, all 0.3 | +8e-16 / +1e-15 | −1.000000 / −1.000000 | 5.729578 | 5.729578 / 5.729578 / 5.729578 (Δ 6.3e-14) | 0.00 / 5.730, 0.00 / 5.730 |
| asymmetric: `right_spring_link_joint` 0.3, left 0 | **−0.1494 / −0.1494** | −0.988771 / −0.988771 | 14.323945 | **2.864789 / 14.323945 / 2.864789** (Δ 11.459156) | **8.59 / 2.865, 8.59 / 14.324** |

- ⭐ **5.729578° = 0.10 rad exactly** — in the symmetric state (`v_c = 0`, `|v_a| = 1`) `tilt(r) = |r|`, so the cap is the menu's smallest non-zero roll (spec `:688`) and nothing else; the record's printed `cap 5.73 deg` (`_gen/reshoot_speccell_20260810/run.log` sha `a1ad9a2a8b0a2326…`, `_gen/dod_c2_20260810/run.log` `04599b84e34be51e…`) is reproduced. `VERTICAL_TOL_DEG` = 5.7300 sits beside it.
- Analytic formula vs model evaluation: max |Δ| **1.3e-13°** over 65 entries × 2 sides × 3 states. `AXFIX_R` vs `diag(1,−1,1)·AXFIX_L·A`: **4.9e-15** (v3 R1′ (b), bar 1e-12: holds).
- Premises ①②③ (v3 §6): `v_c^R = v_c^L` and `v_a^R = v_a^L` to the printed digits in every state ⇒ **`tilt_L(y, r) = tilt_R(y, −r)`**; at a given entry the two sides differ, by 11.46° at this asymmetry (not the linearized 2·v_c — that holds only for small v_c).
- ⚠ **Calibration, asymmetric state**: the upright entry comes out **8.59° > TILT_CAL_DEG 0.5** on both sides ⇒ the first raise (`:1301`) **fires** and no cap is printed. So D4's `(L … / R …)` can only ever print when the live jaw state passes both calibrations on both sides; v3 §6's note that the 08-02 raises fired with no recorded cause is consistent with an asymmetric jaw at print time (a hypothesis, not measured — the live state is run-only).

## Rows (judged after D4 lands; the print's numbers only under an authorized run)

| # | row | requirement and bar |
|---|---|---|
| R3-i | symmetric no-op | landed side-aware `cap_L`, `cap_R`, `min` all == 5.729578° == current formula ≤ **1e-6°** (float64 acos floor ≈ 8e-7° near r = 0 noted); under a run, the printed `cap {min:4.2f}` prefix must still read `5.73` and the tail `(L 5.73 / R 5.73)` in a symmetric live state |
| R3-ii | asymmetric (both hands `right_spring_link_joint` = 0.3, left 0) | (a) current formula == `tilt_R(+r)`: 14.323945 both, ≤ 1e-6° · (b) `tilt_L(−r)` == the formula with `v_c → −v_c`: ≤ 1e-9° · (c) `cap_L − cap_R` = −11.459156° reported exactly, and `v_c^R == v_c^L` ≤ 1e-9 (premise ③) |
| R3-iii | calibration extremes | symmetric: upright 0.00 ≤ 0.5, min tilted 5.730 ≥ 0.5, both sides · asymmetric: upright 8.59 > 0.5 ⇒ raise fires on both sides — the landed code must raise **per side** (v3 §6-2), verified by AST read of the landed function, not by running it |
| R3-iv | side branches, text vs text (p4 (iii)) | landed `vertical_cap_deg(side=…)`: `"L"`/`"R"` return that side's `cap_t`, `None` returns `min_t cap_t`; the per-side path applies `(SIDES[t]·yaw, SIDES[t]·roll)` and both raises per side; `attitude_tilt_deg(t, …)` reads `slot_centre(t)`, `pinch(t)`, `TOOLB[t]`, `AXFIX[t]` — compared against my derivation above by reading; **no literal side sign** anywhere in the hunk |
| R3-v | mount-independence | expectations identical at 0.28/20° and 0.22/45° (measured) — a landed value that moves with the mounting would mean the code reads something outside the tool frame |
| R3-vi | negative control | my instrument on the asymmetric state distinguishes the two conventions by 11.46°: a landed side-aware code that returned 14.32 for L would fail R3-ii; the symmetric state alone cannot tell them apart (both give 5.729578) — so **R3-i is a no-op check, R3-ii is the discriminating row** |
| R3-vii | no run | everything above is `mj_forward`/`mj_kinematics` on composed models; the wired driver is text only; `P4_*` unset; #69 unfired |

## Appendix — `pz_r3.py` (the instrument, verbatim; sha256 134bc663354f43ad8bd97f8a82c633a150165df971bb9834959954ab317fdbc8)
```python
import sys, math, os, numpy as np, mujoco
from scipy.spatial.transform import Rotation
W=sys.argv[1]; sys.path.insert(0,W); os.chdir(W)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import ur15_gripper_mirror_acceptance as g; import ur15_cell_spec as spec
SEED=[0.0,-1.2,1.0,-1.4,-1.57,0.0]
def rdes(y,r): return (Rotation.from_euler("z",y)*Rotation.from_euler("z",math.pi/2)*Rotation.from_euler("y",r)).as_matrix()
def build(t): return g.build_side("ur15_base.xml",g.KO_LEFT,g.acc.SIDE_SIGN["L"]) if t=="L" else g.build_side("ur15_base_mirrored.xml",g.KO_MIRROR,g.acc.SIDE_SIGN["R"])
def ids(m):
    B=lambda n: mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,n); G=lambda n: mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,n)
    toolb=B("g_base"); pad=[B("g_left_pad"),B("g_right_pad")]; claw=[G(f"g_{s}_pad_{c}ext") for s in ("left","right") for c in ("f1","f2")]
    assert toolb>=0 and min(pad)>=0 and min(claw)>=0,(toolb,pad,claw); return toolb,pad,claw
def state(m,fingers):
    dd=mujoco.MjData(m)
    for name,v in zip(g.acc.J6,SEED): dd.qpos[m.joint(f"a_{name}").qposadr[0]]=v
    for j in range(m.njnt):
        n=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,j) or ""
        if n.startswith("g_"): dd.qpos[m.jnt_qposadr[j]]=fingers.get(n[2:],0.0)
    mujoco.mj_forward(m,dd); return dd
def axfix(m,toolb,pad):
    dd=state(m,{}); pl,pr=dd.xpos[pad[0]].copy(),dd.xpos[pad[1]].copy(); c_w=(pr-pl)/max(np.linalg.norm(pr-pl),1e-9); pinch=0.5*(pl+pr)
    a_w=dd.xpos[toolb]-pinch; a_w=a_w/max(np.linalg.norm(a_w),1e-9); Rt=dd.xmat[toolb].reshape(3,3); c_l,a_l=Rt.T@c_w,Rt.T@a_w
    return np.column_stack([c_l,np.cross(a_l,c_l),a_l]).T
def vtool(m,toolb,pad,claw,fingers):
    dd=state(m,fingers); v=np.mean([dd.geom_xpos[k] for k in claw],axis=0)-0.5*(dd.xpos[pad[0]]+dd.xpos[pad[1]])
    vt=dd.xmat[toolb].reshape(3,3).T@v; return vt/max(1e-12,np.linalg.norm(vt))
def tilt(AX,vt,y,r): w=(rdes(y,r)@AX)@vt; w=w/max(1e-12,np.linalg.norm(w)); return math.degrees(math.acos(min(1.0,max(-1.0,float(-w[2])))))
FJ=[mujoco.mj_id2name(build("L")[0],mujoco.mjtObj.mjOBJ_JOINT,j)[2:] for j in range(build("L")[0].njnt) if (mujoco.mj_id2name(build("L")[0],mujoco.mjtObj.mjOBJ_JOINT,j) or "").startswith("g_")]
STATES={"sym0":{}, "sym0.3":{j:0.3 for j in FJ}, "asym(R_spring 0.3)":{"right_spring_link_joint":0.3}}
MENU=spec.GRASP_ATTITUDES; UP=[(y,r) for y,r in MENU if abs(r)<1e-9]; TL=[(y,r) for y,r in MENU if abs(r)>=1e-9]
print(f"mount: yoke {spec.YOKE_SPREAD} tilt_deg {math.degrees(math.pi/2-spec.TILT):.1f} | menu {len(MENU)} entries ({len(UP)} upright) | TILT_CAL {spec.TILT_CAL_DEG} VERTICAL_TOL {spec.VERTICAL_TOL_DEG:.4f} | finger joints {FJ}")
M={t:build(t) for t in "LR"}; I={t:ids(M[t][0]) for t in "LR"}; AX={t:axfix(M[t][0],I[t][0],I[t][1]) for t in "LR"}
print("AXFIX_R vs diag(1,-1,1)·AXFIX_L·A (v3 R1' (b)):", f"{np.abs(AX['R']-np.diag([1,-1,1])@AX['L']@np.diag([-1,1,1])).max():.2e}", "| c·a (closing vs approach axis, deg from 90):", {t: f"{math.degrees(math.acos(float(AX[t][0]@AX[t][2])))-90:+.4f}" for t in "LR"})
for sname,f in STATES.items():
    VT={t:vtool(M[t][0],*I[t],f) for t in "LR"}; comp={t:AX[t]@VT[t] for t in "LR"}   # (v_c, v_s, v_a) per side
    cur=min(tilt(AX["L"],VT["L"],y,r) for y,r in TL)                                  # wired formula: L data, raw entries
    cap={}; cal={}
    for t in "LR":
        s=spec.SIDES[t]; ups=[tilt(AX[t],VT[t],s*y,s*r) for y,r in UP]; tls=[tilt(AX[t],VT[t],s*y,s*r) for y,r in TL]
        cap[t]=min(tls); cal[t]=(max(ups),min(tls))
    # analytic (my derivation): tilt = acos(v_c*sin(rho) - v_a*cos(rho)), rho = received roll; yaw-free
    def an_t(t,y,r):
        s_=spec.SIDES[t]; vc,vs,va=comp[t]; z=(vc*math.sin(s_*r)-va*math.cos(s_*r))/math.sqrt(vc*vc+vs*vs+va*va); return math.degrees(math.acos(min(1.0,max(-1.0,z))))
    an=max(abs(tilt(AX[t],VT[t],spec.SIDES[t]*y,spec.SIDES[t]*r)-an_t(t,y,r)) for t in "LR" for y,r in MENU)
    print(f"[{sname:18s}] v_c L {comp['L'][0]:+.3e} R {comp['R'][0]:+.3e} | v_a L {comp['L'][2]:+.6f} R {comp['R'][2]:+.6f} | cap current(L data,raw) {cur:.6f} | side-aware cap_L {cap['L']:.6f} cap_R {cap['R']:.6f} min {min(cap.values()):.6f} | |cap_L-cap_R| {abs(cap['L']-cap['R']):.2e} | cal(max upright, min tilted) L {cal['L'][0]:.2e}/{cal['L'][1]:.3f} R {cal['R'][0]:.2e}/{cal['R'][1]:.3f} | analytic-vs-model max {an:.1e} deg")
```

## Provenance
`git archive HEAD` of the sim directory into the scratchpad; `git show` for every pin; my own code above under env7. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian (or my pathspec commit on the hub's word, as m-p18-331).**
