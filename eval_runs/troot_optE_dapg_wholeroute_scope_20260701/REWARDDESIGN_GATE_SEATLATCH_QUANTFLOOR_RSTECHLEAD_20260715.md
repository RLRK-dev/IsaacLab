# Reward-Design Gate ② — Stage-A G1–G6 latched reward, seat-latch reachability

**Author:** RS-TECH-LEAD (w2:p4). **Date:** 2026-07-15 20:07 JST (date-THEN-write).
**Node:** `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild`.
**Trigger:** Rs directive 2026-07-15 ~19:5x = "②reward-design + G3上程" (run the reward-design 直交ゲート that gates W1 build B3b-B7 per `00-DESIGN-STATUS-LEDGER.md:57`; escalate the G3 latch quantization blocker).
**Role boundary:** This is a **gate ANALYSIS of the banked design** (verifier). It does **NOT** design a fix — a broken success/reward predicate is a *design* change = Rs/p5 専権 (`CLAUDE.md` 設計ゲート; `feedback-design-ask-vt-design-never-self-derive`). The fix candidate in §Escalation is a *pointer for Rs/p5*, not a decision.

---

## 0. What is under the gate (the CURRENT banked design, on-disk)

The Stage-A whole-route env reward is **sparse-primary G1–G6, latched-monotonic, fire-once, never-revoked, ORDERED** (`newton_route_env.py:39-41`). It is **not** the parked dense residual design in `P2_REWARD_DESIGN.md` (that was `/pre-check`=BLOCK + DQ1→"B", 2026-07-02).

Full reward assembly (`newton_route_env.py:1581`):
```
r = TIME_PENALTY(-0.01/step)  +  r_phase(+5 per G1..G5 latch)  +  (G6_TASK_BONUS +200 if success)
explosion|drop -> r = TERM_PENALTY(-10)          # :1578-1580
```
There is **NO dense shaping term** (no r_pos / r_seat gradient). The only learning signal toward seating is the discrete G-latch events. Constants: `route_env_config.py:106-108` (G_PHASE_BONUS 5.0 / G6_TASK_BONUS 200.0 / TIME_PENALTY −0.01).

Raw predicates (`newton_route_env.py:1544-1552`):
| G | predicate | code |
|---|---|---|
| G1 | grip cage (grip_r/l≥0.5 ∧ contact ∧ span) | `p1` :1545-1549 |
| G2 | lift (`held_z − cable_z_rest ≥ LIFT_RISE_MIN`) | `p2` :1550 |
| **G3** | **`c1_seat < T_GROOVE` ∧ `ph≥2`** | `p3` :1550 |
| G4 | regrasp (`r_reach ≤ REGRASP_REACH_TOL` ∧ contact_r) | `p4` :1551 |
| **G5** | **`c2_seat < T_GROOVE`** | `p5` :1552 |
| G6 | SUCCESS: `G5 latched` ∧ `c2_honest` ∧ `c1_retained` ∧ ¬drop ∧ span, sustained K_ROUTE_SEAT=10 | :1570-1574 |

ORDERED latch (`:1556-1563`): `G_k` fires only if `G_{k-1}` latched (`if k>0 and not _g_latched[k-1]: break`). G6 needs G5 (`if _g_latched[w,4]:` :1570).

### The instrument under all of G3/G5/G6
`_seat_metrics(cable_pos, clip_xy)` (`:1300-1311`):
```
near = argmin(|cable_pos[:,1] - clip_xy[1]|)   # SINGLE nearest-in-Y cable body — NO interpolation  :1306
p    = cable_pos[near]
z_gap   = p[2] - ROUTE_GROOVE_Z(0.829)         # :1308 / route_env_config.py:144
lateral = ||p[:2] - clip_xy||                    # :1309
seat_dist = sqrt(lateral^2 + z_gap^2)            # :1310  == c1_seat / c2_seat
```
- `T_GROOVE = 0.003` (3 mm) — `task_config.py:368`.
- Cable = **40 rigid capsule segments × 15 mm** — `task_config.py:135-136` (`CABLE_SEGMENTS=40`, `CABLE_SEG_LEN=0.015`).
- G6's `c2_honest` = `_c2_seated_honest` (`:1313-1320`): `wall_ok = seat_dist·1e3 ≤ C2_WALL_SEAT_TOL_MM(0.5)+T_GROOVE·1e3(3) = 3.5 mm` — **same quantized `seat_dist`**.
- G6's `c1_retained` = `_c1_retention_m` (`:1282-1298`): `z_c1<840 ∧ flank<840` — **z-only, no X** (a ceiling; 81/81 no-op per `CATCHUP...COORD2_20260714.md:41,58`).

---

## 1. The mechanism (why the bar is below the instrument's floor)

`seat_dist ≥ lateral ≥ |dy|`, where `dy` = Y-offset of the **nearest-in-Y cable node** from the clip center. Node Y-positions are discretized at the 15 mm arc-spacing of the 40-segment cable. The nearest node to `clip_y` therefore sits at `|dy| ∈ [0, ~7.5 mm]` (half the segment Y-pitch) — **and this offset is set by where the cable's discrete nodes happen to fall, not by how well the policy physically seats the cable.**

⇒ Even a **physically perfectly-seated** cable yields `seat_dist ≈ |dy|` up to ~7.5 mm. The `< 3 mm` bar (`T_GROOVE`) is **below** this quantization floor.

Documented floor values (same mechanism, two panes): **7.32 mm** (`C1_XSEC_VIDEO_LEG_CANONICAL_pC_20260715.md:31`, pC), **±7.5 mm** (`CATCHUP_FOR_RSTECHLEAD_FROM_COORD2_20260714.md:38-39`, COORD2). First-principles bound = half-segment = 7.5 mm. All ≫ 3 mm.

`P(seat_dist < 3 mm | physically seated) ≤ P(|dy| < 3 mm) ≈ 3/7.32 ≈ 41%` (uniform node phase) ⇒ **≥59% of seatings cannot fire the latch** — stricter once `dx`, `z_gap` are added. Documented estimate = **~70% unreachable** (`CATCHUP...:59`). The policy has **no gradient** to align a node to `clip_y` (discrete, non-differentiable, DR-set), and the reward is sparse ⇒ no bridge.

---

## 2. Artifact 1 — REACHABILITY TABLE

P0 = start of a seated dwell after a physically-correct route (BC/demo prior places the cable in the groove). "Reachable" = can the sparse latch fire from a physically-correct behavior?

| G component | Gate (latch condition) | Reachable when physically correct? | Signal/gradient toward gate | Dead zone? |
|---|---|---|---|---|
| G1 grip | grip∧contact∧span | yes | grasp phase (BC prior) | no |
| G2 lift | held_z rise ≥ margin | yes | lift phase | no |
| **G3 C1-seat** | `seat_dist(C1) < 3 mm` ∧ ph≥2 | **~30–41% only (node-alignment lottery)** | **none — sparse latch; no shaping; node phase not policy-controllable** | **YES** |
| **G4 regrasp** | reach∧contact **AND G3 latched** | blocked whenever G3 fails to latch | inherits G3 | **YES (inherited)** |
| **G5 C2-seat** | `seat_dist(C2) < 3 mm` **AND G4 latched** | same ~30–41% × G4 | none (same instrument) | **YES** |
| **G6 SUCCESS** | G5 latched ∧ `seat_dist(C2)≤3.5` ∧ z-only c1_retained ∧ sustained | product of two quantized gates; retention conjunct is a no-op | +200 unreachable | **YES** |

**≥3 rows Dead-zone=YES on the same quantized instrument ⇒ Artifact 1 = FAIL.** (Skill rule: "If any row has Dead zone = YES, STOP. Do not implement.")

---

## 3. Artifact 2 — CAUSAL GATE DAG

```
action(EE residual) -> arms drag cable -> cable physically enters C1 groove
        |                                                     |
        |                                    nearest-in-Y NODE offset dy (0..7.5mm)  <-- set by cable discretization + DR, NOT by policy
        v                                                     v
   seat_dist = sqrt(lateral^2 + z_gap^2) >= |dy|      ---[GATE G3: seat_dist < 3mm]--- latch G3 (+5)
                                                              |
                             floor(seat_dist) ~ 7.32mm  >  3mm bar   ==> gate unreachable ~70%
                                                              |  no shaping reward, no gradient to node-align
                                                              v
                                                        *** DEADLOCK ***  (sparse latch cannot fire)
                                                              |
                       ORDERED: G4 needs G3, G5 needs G4, G6 needs G5  (:1560-1570)
                                                              v
                              G4 / G5 / G6(+200 SUCCESS) all never fire  ==>  RL task signal never materializes
                                                              |
                              only TIME_PENALTY(-0.01/step) remains  ==>  degenerate objective (terminate-fast / hover)
```
The G3 gate has **no driving reward** toward it (sparse; the physical seat is done by the BC prior, but the *measurement* floor blocks the latch). By the skill's rule "a GATE with no reward signal driving toward it is a DEADLOCK" ⇒ **Artifact 2 = FAIL.**

---

## 4. Artifact 3 — GROUND-TRUTH VALUES (computed from grounded params)

Clip C1 = (0.35, 0.150), `ROUTE_GROOVE_Z = 0.829`, bar `T_GROOVE = 3 mm`. Cable physically seated (dx, z_gap small); vary only the **uncontrolled** nearest-node Y-offset `dy`:

| State | phys. seated? | node `dy` | `dx` | `z_gap` | `seat_dist` | G3 `<3mm`? |
|---|---|---|---|---|---|---|
| S0 node-aligned | **yes** | 0.0 mm | 0.5 | 0.5 | **0.71 mm** | ✅ fires (lucky) |
| S1 node half-off | **yes** | 3.66 mm | 0.5 | 0.5 | **3.73 mm** | ❌ **NO — seated but rejected** |
| S2 node worst-off | **yes** | 7.32 mm | 0.5 | 0.5 | **7.35 mm** | ❌ NO |
| S3 not seated, node-aligned | **no** | 0.0 mm | 20 mm | 5 mm | 20.6 mm | ❌ NO (correct) |

⇒ The instrument returns the **same "NO"** for a physically-seated cable (S1/S2) as for an unseated one (S3) whenever `dy>~3mm`. It **cannot distinguish "seated but node-misaligned" from "not seated."** A success predicate whose PASS value is unreachable by correct behavior ⇒ **Artifact 3 = FAIL** (Pattern-4 Success-Condition Disconnect).

---

## 5. Artifact 4 — EPISODE TRACE

```
Step 0:  BC prior + residual drive the committed route. G1(grip),G2(lift) latch. +10 so far.
Step k:  cable physically seated in C1 groove. nearest node dy = 4.1mm (this episode's lottery, DR-set, static during dwell).
         seat_dist = 4.2mm > 3mm  -> G3 does NOT latch.
Step k+1..k+N (whole seated dwell): dy stays ~4.1mm (cable not sliding through grippers); seat_dist stays >3mm.
         G3 never latches. ORDERED chain: G4 gated on G3 -> also frozen. G5,G6 unreachable.
         Reward each step = -0.01 (TIME_PENALTY). No gradient, no latch, no bridge.
Step T:  timeout. Episode return = +10 (G1+G2) - 0.01*T. SUCCESS(+200) never seen.
```
For the ~70% of episodes whose seat-time node offset exceeds ~3 mm, **no action sequence can fire G3** (the offset is not a policy DOF and there is no shaping reward to chase it). The RL objective's terminal signal (+200) is therefore unreachable for the majority of correct rollouts ⇒ **Artifact 4 = FAIL** (dead-step / Pattern-1 no-bridge under a sparse reward).

---

## 6. GATE DECISION

```
[REWARD DESIGN GATE]
Reachability : FAIL — G3/G5/G6 dead-zone: bar 3mm < seat_dist quantization floor ~7.32mm (nearest-in-Y node, 15mm segments)
Causal DAG   : FAIL — G3 gate is a DEADLOCK (no shaping reward toward it; measurement floor blocks the latch); ORDERED chain freezes G4/G5/G6
Ground-truth : FAIL — physically-seated cable (S1/S2) scores identically to unseated (S3) once node dy>3mm; PASS value unreachable by correct behavior
Episode trace: FAIL — ~70% of correct rollouts can never fire G3 -> +200 SUCCESS unreachable -> degenerate objective

GATE: FAIL -> implementation BLOCKED. Redesign of the seat success/latch predicate required (Rs/p5).
```

Conservatism note (§運用15): this FAIL is **conservative** — sim/instrument makes success *harder to register* than physical reality (it rejects genuine seatings). A conservative FAIL is bankable. It does **not** claim the physics is wrong; it claims the *measurement* used as the reward/success gate is below its own quantization floor.

---

## 7. ⛔ ESCALATION to Rs / VT-DESIGN (the fix is a design change = not mine)

The seat-latch predicate family (`_seat_metrics` nearest-in-Y node) is a **success-condition design** surface. Redesigning it is Rs/p5 専権. I surface, I do not decide.

**Three coupled defects the redesign must address (all on-disk, `CATCHUP...COORD2_20260714.md:31-61`):**
1. **PASS-unable (this gate):** G3/G5 bar 3 mm < nearest-node |dy| quantization floor ~7.32 mm ⇒ ~70% unreachable; ORDERED ⇒ blocks G6 SUCCESS.
2. **FAIL-unable:** `c1_retained` (`:1282-1298`) is z-only (no X) ⇒ 81/81 no-op ⇒ contributes no seating discrimination to G6.
3. **Lateral capture is Rs-video-gated, not numeric-alone (standing Rs rule):** `_seat_metrics` is lateral-blind by construction (a wall/adjacent contact can score like a groove seat). Any numeric seat fix is necessary-not-sufficient — the design must still gate on Rs video.
   > ⚠ **ERRATUM 2026-07-15 20:4x (p6 catch, %12 verified on-disk):** an earlier draft cited "cell-2037 = all-numeric-PASS yet Rs-GT REJECTED" as proof of "no numeric can measure capture." **That evidence is FALSE/retracted** — on cell-2037 numeric and Rs-GT **AGREED** (Rs video 2026-07-14「溝に入っているし底にもついている ok」, commit `3168e0e197`; the 07-12 proof is retracted at `ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:101-110` — the very lines the draft mis-cited **are** the retraction). The conclusion **survives as a standing Rs directive** (numeric-alone PASS forbidden; CLASS-R maintained on 専権 grounds per `:108-109`), **not** as a numeric/Rs discrepancy. **The gate FAIL above rests on defects #1/#2 (pure code-grounded), independent of this item.**

**Candidate the redesign could consider (COORD2 §5, `CATCHUP...:75-79` — a POINTER, not my decision):** interpolate the cable X at exactly `y=clip_y` (removes Y-quantization), then a 3-conjunct honest predicate `|dx|≤3mm ∧ |z−ROUTE_GROOVE_Z|≤3mm ∧ wall-only-contact≤0.5mm`. ⚠ `c1_wall_dist_spacer_excluded_mm` is **not emitted** ⇒ producer re-run needed (COORD2 §5 leg 3). Even this does not resolve defect #3 (Rs-video-only capture GT).

**Open decisions returned to Rs/p5:**
- (a) Redesign the seat latch to remove the node-quantization (interpolation vs finer segmentation vs a different measurable)? — success-condition change, L3, `/reward-design` re-run + `/pre-check` after.
- (b) Does G6 SUCCESS keep the z-only `c1_retained` conjunct, or replace it with a lateral-aware predicate?
- (c) Accept that lateral capture is gated on Rs video (numeric-alone PASS forbidden — standing Rs rule, CLASS-R on 専権 grounds, `ANCHOR...:108-109`) and gate the campaign on video milestones?

**Downstream status:** W1 build B3b-B7 (incl. `authorize_clip_pin` implementation) stays **gated** — reward-design ② = FAIL until (a)/(b)/(c) are resolved by Rs/p5. `authorize_clip_pin` design-of-record (v2, §15) is unaffected by this gate (it is a *pin-authorization geometry* gate, not the *RL success* predicate); but the env it wires into cannot train a valid seat-success signal until this is fixed.
