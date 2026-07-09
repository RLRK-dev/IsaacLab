# /geometric-design — comp3 flag-ON build_multiworld table-VOID re-confirmation (Stage-B design-gate) — %11 COORD

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec — comp3 (grasp_actuation flag-flip) Stage-B design-gate.
**trigger:** %12 06:08 — /geometric-design on the flag-ON build_multiworld void (comp3 plan §6/L2 design side). PLANNING (no-GPU, paper).
**⛔ scope note:** the void is a **PROVEN, already-banked geometry** (base comment: "mirrors the PROVEN build_scene grasp_actuation slot, test:1055-1119, probe 9/9"), re-confirmed by (a) SRG void-parity gate no-GPU PASS (LEDGER:47) and (b) env-core /geometric-design table-void×C1-clip parity PASS (node state.md 05:43). This gate = **re-confirm the void×cable×C1-clip parity actualized in the RL env (flag-ON build_multiworld)** + Step-5d axis-retention (SRG-grounded). NOT a fresh geometry. Skill artifacts produced below.

---

## Step 0. Interrogate-the-mechanism (BOUNDED, one pass)
1. **Is the void necessary?** YES — the koshape f1ext UNDER-claw must reach BELOW the table-resting cable (Z=0.809) to cage it (form-closure); a SOLID table blocks f1ext at the table-top plane (0.800) → no hook → no hold (base:1743). The void is the load-bearing mechanism, not decoration.
2. **Cheaper salvage?** NO — the cable rests on the table; grasping-from-below intrinsically needs the table removed under the footprint. Alternatives (grasp-from-above, lift-then-grasp) are different tasks, out of the 0.716 MOTION STANDARD route.
3. **Downstream the real risk?** The grasp itself = SRG-PROVEN robust; the residual risk = the env-drive TRANSFER (build_scene→build_multiworld, G1 GPU), NOT the geometry. ⇒ commit the void geometry (proven); flag G1 as the live-transfer check.
**BOUND kept:** one pass, no rev-chain, no sim launched.

## Step 1. 実測 (built-model geometry, task_config + base SSOT)
| 計測対象 | 値 | source |
|---|---|---|
| Table top Z | 0.800 (TABLE_HEIGHT) | task_config:20; base table_cz+hz=0.795+0.005 |
| Table span (X,Y) | X[-0.05,0.65], Y[-0.40,0.30] | base:1736-37 (cx0.3 cy-0.05, half 0.35/0.35) |
| Cable center Z (seated) | 0.809 (GROOVE_CENTER_Z=0.80+0.005+0.004) | task_config:226 |
| Cable radius | 0.004 | task_config:137 |
| void slot Y | [0.090, 0.210] (WIDE 0.106/0.194 ±16mm) | base:1746 slot_lo/hi |
| void slot X | [0.234, 0.366] (GRASP_X 0.30 ±66mm footprint) | base:1750 |
| L grasp Y / R grasp Y | 0.106 / 0.194 (CLIP1_Y 0.150 ± GRIP_HALF_SPAN 0.044) | task_config:268-269 |
| GRASP_X | 0.30 | task_config:231 |
| f1ext claw TIP drop (closed) | 0.2758 (EE_TO_PINCH_TIP_CLOSED) below wrist_3 | task_config:321 |
| C1 target clip float | +20mm (ROUTE_CLIP_FLOAT_Z) above table | route_env_config; call :398 |
| DR amplitude | ±20mm (CABLE_XY_DR_AMPLITUDE) | task_config:264 |

## Step 2. 制約 (H = hard, S = soft)
**Hard (violation-forbidden):**
- **H1 non-penetration:** f1ext claw descends BELOW table-top (0.800) to hook under the cable → MUST be over the VOID (no solid box), else penetrates a solid table box. Grasps L=0.106/R=0.194 ∈ void-Y[0.090,0.210] ✅ and GRASP_X=0.30 ∈ void-X[0.234,0.366] ✅ → both claws over void → reach under cable WITHOUT penetration. **The void makes it non-penetrating BY CONSTRUCTION** (not a DISABLE_CONTACTS workaround).
- **H2 cable in cage:** cable Z=0.809 within the f1ext form-closure cage (claw brackets cable). SRG S1/S2 confirmed cage HOLDS (cage-escape lateral/z within DROP margins).
- **H3 cable span-support:** cable SPANS the void, supported on BOTH Y-sides (solid table at Y<0.090 and Y>0.210) → no droop (base:1743). ✅
- **H4 flag-OFF byte-preserve:** grasp_actuation=False → single solid box (env-core byte-identity). ✅ by construction (comp3 plan §5).
**Soft:**
- S1 cable centered in cage for lateral robustness — SRG worst=nominal (cable deep in void = max sag but still GRIP_GO); DR corners RELIEVE sag.
- S2 C1 target clip (+20mm float) must NOT interfere with the grasp — floats above the void, over-void but +20mm clear (node state.md 05:43). ✅

## Step 3. 断面図 (Y-Z plane at GRASP_X=0.30, scale mm)
```
Z[mm]
 830 ─   wrist_3 (both arms) ── claw drop 275.8mm ──┐
        L-claw(Y106)      R-claw(Y194)              │
 809 ─      │ ═══════ cable (Z809, r4) ═══════ │    ← H2 cable center
 800 ─▓▓▓▓▓▓┤                              ├▓▓▓▓▓▓▓  ← TABLE top (solid)
      solid │        VOID (no box)         │ solid
 795 ─▓▓▓▓▓▓┤  Y[90..210], X[234..366]     ├▓▓▓▓▓▓▓  ← table box bottom
            ▼ f1ext reaches UNDER cable ▼            (H1 ✅ no penetration:
        Y=90────106────150────194────210             claws over VOID)
        solid│ L-grasp    R-grasp │solid
      ← ±16mm void-cradle → | ← DR ±20 → one claw over table edge (SRG S2: GRIP_GO)
```
- H1 ✅ (claws over void, no solid-box penetration) / H2 ✅ (cable Z809 in cage) / H3 ✅ (span supported both Y-sides) / H4 ✅ (flag-OFF solid box).

## Step 4. トレード (flag state — the only design fork; H-satisfying rows only)
| option | grasp_actuation | table under footprint | f1ext reach | H1 | H2 | H4 byte | verdict |
|---|---|---|---|---|---|---|---|
| flag-OFF (default) | False | SOLID box | blocked (no grip) | ✅ (no claw-descent) | n/a (no grip) | ✅ env-core identity | env-core preserve |
| **flag-ON (comp3) ★** | True | VOID 4-box | under cable ✅ | ✅ over void | ✅ cage holds (SRG) | ✅ (gated, off=identity) | **live grip** |
No H❌ rows (the void is the proven non-penetrating design; the solid-box alternative simply has no grip, correctly = env-core).

## Step 5. 物理妥当性 + 5a 感度 + 5c 因果 + 5d 軸保持
**5 reality-check:** the void mirrors build_scene(grasp_actuation=True) (probe 9/9, test:1055-1119); SRG void-parity gate confirmed build_multiworld void == build_scene void == FIXED [0.090,0.210], CPU readback NO artifact (badqacc0, no claw↔table contact, grip engages). ⇒ real-substrate-valid.
**5a sensitivity (DR ±20mm, the live variation):** void FIXED [0.090,0.210]; DR shifts CABLE not void. ±16mm = void-cradle-max (both claws in void); ±20mm = one claw over table edge (+4mm past void). **SRG S2 measured this** (4 corners ±20/±16) = GRIP_GO all, WORST=nominal (offset RELIEVES sag). H1 stays ✅ (the claw over the table edge is at the void boundary; SRG readback no artifact). ✅
**5c causality trace (grasp_actuation ON → 5 steps):** flag-ON build → f1ext over void → servo close (recorded ramp) → 4-bar cages cable Z809 → cable spans supported void (no droop) → route drag (downstream). No irreversible/adversarial state in the grasp (SRG S0/S1/S2). Downstream seat/guide = J-9 (route-exec/comp, NOT grasp). ✅
**5d axis-resolved retention (μ0 form-closure, SRG-grounded):**
| cable DOF | enclosed / carried | SRG evidence |
|---|---|---|
| vertical (z-drop) | enclosed (form-closure cage) | S1/S2 z-drop within DROP_LIFT margin |
| lateral (x) | enclosed (cage) | S1/S2 lateral within DROP_LATERAL margin |
| axial slide (com_y) | carried (benign) | S0 axial floor 1.29µm/f (benign, per design §13) |
| up-escape / roll-out | enclosed (condim6 rolling rows + PAD_SOLREF) | S1 GRIP_GO (rolling rows ACTIVE) |
SRG's creep-budgeted criterion already handles the "cage≠hold" caveat (form-closure cage, not friction-pinch). Axial = carried residue (benign). ✅

## Step 6. 記録 + 変更ファイル
- **task_config.py / base geometry change = NONE.** comp3 = flag-wire only; the void geometry is PROVEN + inherited.
- **06-Knowledge GD record = DEFER** (skill: 未承認設計は記録しない; the void is already banked via SRG + env-core parity PASS; this doc = design-gate re-confirmation, → post-approval GD update is a PLAN-KEEPER/%12 surface, not self-written now).
- **L2 no-GPU leg (comp3 plan §8):** re-confirm on the BUILT flag-ON build_multiworld model — void formula readback [0.090,0.210], no claw↔table contact artifact, f1ext reaches under cable (reuse SRG s2_void_check.py pattern, adapted to build_multiworld directly, multi-world).

## VERDICT = PASS (re-confirmation — proven + SRG-validated geometry)
- H1-H4 all satisfied (void enables non-penetrating f1ext reach; cable spans supported; flag-OFF byte-preserve).
- Sensitivity (DR ±20mm) SRG-measured = GRIP_GO, worst=nominal (offset relieves).
- Axis-retention μ0-grounded via SRG (vertical/lateral/roll enclosed; axial carried benign).
- **Residual:** the void is validated in build_scene (SRG) + parity to build_multiworld formula; the flag-ON actualization in the RL-env built model = **L2 no-GPU readback (structural leg)** + live grip = G1 GPU-deferred.

---
*%11 COORD (w2:p3) 2026-07-10. /geometric-design comp3 void. No-GPU paper. PASS (re-confirmation). Pairs with COMP3_FORCE_DESIGN (servo). → both PASS → %12 5体 [VERIFY].*
