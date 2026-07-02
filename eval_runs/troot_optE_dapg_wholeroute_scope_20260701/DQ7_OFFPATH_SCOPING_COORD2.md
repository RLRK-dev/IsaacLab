# DQ7 — off-path 教師機構の設計 scoping (options + recommendation)

**Author:** COORD2 (%10, scoping/audit). **Written:** 2026-07-03 05:12 JST (same-turn `date`).
**Charter:** `charter_dq7_offpath_scoping_coord2.txt` (Rs option A verbatim「A」07-03 05:00 = B2 STOP bank + DQ7 起票).
**Status:** SCOPING ONLY — 0-commit (%12 commits at review), no implementation, no GPU, no locked-file edits. **Design decision = Rs 専権**; §6 is a labeled RECOMMENDATION, not a decision.

---

## §0. Grounding (anchor set, §運用4 — read + cited from primary instruments, not narrative)

| Anchor | Cite | Fact used |
|---|---|---|
| LEDGER row45 tail | `00-DESIGN-STATUS-LEDGER.md:45` | B2 完結 = OG STOP banked; 「restoring = DR 多様性」仮説 REFUTED (rollout GPU 0 分); fork-(iv) integrator 修復は不変; Rs「A」→ DQ7 |
| node DQ namespace | `T-ROOT-optE-route-dapg-C1C2/state.md:38-44` (:43 tail ⟦07-03 05:00⟧) | DQ7 = off-path 教師機構設計; DQ1=B / DQ4 XY±20mm / DQ6 fork-(iv) ADOPTED |
| B2 spec metrics | `B2_KICKOFF_SPEC.md:120-173` | §3.2 legs / §3.3 verdict table (:134-148) / §3.4 15-phase classes: movable={0-3}, cable-anchored={11}, decoupled=10 (:150-173); null-beat ≥0.15 (:151) |
| OG verdict (一次計器) | `b2_cpE_og/bc/og_gate.json` | overall STOP; movable γ⊥ 2.497/1.257/1.041/1.055 (all STOP); C2_REGRASP pair = seg-follow **0.282** (band [0.8,1.2] 未達) + ee-only **0.973** (≥0.9 STOP); null_beat **−0.261** (bar +0.15); carried={GUIDE_C2} |
| BC on-path result | `b2_cpD_report.md:14` | BC whole-demo val 0.000659 vs null 0.011979 = **18× on-path 汎化優位** (diversity works on-path) |
| P2 BLOCK (option (i) 制約) | `P2_REWARD_DESIGN.md:6-7` + `P2_PRECHECK_CROSSPV_OPSSUP.md` §1-§4 | 10 issues CONCUR-BLOCK (2CRIT/4HIGH/4MED, HIGH6→CRIT) + missed M-A..M-E; strategic reframe = env-ABSENT + demos-ABSENT co-roots; PARKED not killed |
| INVARIANTS | `RS71-System-Spec-SSOT.md:19-27` | #1 dual-arm / #2 88mm span / #3 DiffIK-only / #4 コ LOCK / #5 no-kinematic-trick (pin 例外 `log.md:6534`) |
| obs layout (一次) | `route_demo_to_bc.py:286,415,883` | obs = `[0:3]`R-ee, `[3:6]`L-ee, `[6:9]`seg (per `_seg_rule`), `[9:12]`next_clip, `[12:12+n]`phase one-hot; **label = per-step NEXT-WAYPOINT abs target `wp[·,6]`** (:242) |
| OG probe mechanics (一次) | `og_offline_gate.py` `og_b` (co-move: seg co-moves with `_holder_axes` post-grasp, `co_seg = p>=2`; γ⊥ = transverse worst-case SV of d(tgt)/d(ee)); pair probe (seg-follow = perturb L-ee(3+k)+seg(6+k) together / ee-only = R-ee(0+k), seg fixed) | the perturbation MODEL the gate itself uses — reused in §4-(iv) |

---

## §1. What B2 proved / what a DQ7 mechanism must supply

**Proved (measured):** pure BC on 11 diverse demos generalizes ON-path (18× val) but supplies **no off-path restoring** — γ⊥≈1-2.5 = follows/amplifies the perturbed obs; 2mm≈10mm probe = scale-invariant obs-following; null_beat −0.261 (BC WORSE than the replicate-null on the beat metric). **Structural cause:** the BC dataset contains only on-manifold (obs, wp) pairs — off-manifold states have no teacher.

**Acceptance geometry (the §3.3 GO conditions a mechanism must flip):**
1. **Restoring leg:** movable {0-3} γ⊥ ≤0.5 (now 2.497/1.257/1.041/1.055) AND C2_REGRASP ee-only ≤0.3 (now 0.973).
2. **Following leg:** C2_REGRASP seg-follow ∈[0.8,1.2] (now **0.282 = UNDER-following** — the policy partially ignores the cable seg dims).
3. **Attribution:** beat the replicate-null by ≥0.15 (now −0.261).

⚠ **Two failing legs, not one.** Off-path supervision (the DQ7 headline) addresses leg 1; leg 2 (seg-follow undershoot) is a *different* deficiency (on-manifold input-sensitivity) that off-path data does not automatically fix. **Any package that fixes only leg 1 still cannot reach GO.** Both are covered in §4 (leg 2 = (iv)'s seg-co-move leg and/or adj-A densification).

---

## §2. Prior-art gate record (V10, mandatory)

Run: `scripts/check_thread_vault_prior_art.sh --fail-on-blocker dagger offpath off-path restoring perturb bc-augment denoising dart` → **8 BLOCKER hits → 3 distinct source lines**:

| # | Source | Nature | Disposition |
|---|---|---|---|
| 1 | `state.md:43` (5 keywords) | **Self-referential** — the line that RECORDS the B2 STOP + DQ7 起票 | Not a prior failed path; it is this task's provenance. B2's refuted hypothesis (「DR 多様性だけで restoring」) is absent from the DQ7 option space — every option ADDS a supervision mechanism |
| 2 | `LEDGER:45` (2 keywords) | Same self-reference | Same |
| 3 | `B_BC_BUILD_SPEC.md:158` (`perturb`) | **Substantive prior art:** E15 fork debate 棄却 of「augmented corrective (synthetic restoring labels)」— reasons (a) post-grasp EE/seg obs 不整合, (b) 新 perturbation 設計面 | Deltas ①-④ below; reasons (a)(b) carried as first-class constraints in §4-(iv) |

**Continuation deltas (documented per V10 before proceeding):** ① 目的相違 — E15 chose an action REPR (integrator fix); DQ7 adds supervision ON TOP of the adopted fork-(iv) repr. ② 証拠状態相違 — at E15 time「restoring = B2-DR の学習対象」was live (LEDGER:45 clean separation); B2 REFUTED it. ③ 計器化 — the OG gate was then a design, now implemented + **2× validated** (B1′, B2: offline predicted in-sim, 0 GPU surprise) → rejection reason (b)'s design-surface risk is now measurable. ④ spec 自身 (:158) が将来再訪可を明記。
**%12 裁定 (07-03 05:1x): 続行承認** + sharpening directive: (a) obs 物理整合性 (EE/seg 連動 — 次元独立 noise = 物理不可能 obs) を option (iv) で明示解決し、**(ii) vs (iv) の判別軸として §4 表に出す** → done (§4 axis column + §4-(iv) detail).

---

## §3. Restoring anatomy of the scripted route (the factual basis for options (ii)/(iii))

**Charter question: which phases have state-derived targets vs frozen waypoints?**

**Fact A — EE-state perturbations are restored at EVERY phase.** All EE motion = `ik_move_both` interp-to-IK toward per-phase ABSOLUTE targets → wherever the EE is, the servo converges to the target (B1′ P2a measured precedent: approach spike 433mm → re-anchor to 9-16mm, corr(t,drift) negative — LEDGER:45). So the scripted controller is a valid **EE-restoring** expert everywhere, by construction.

**Fact B — cable-state re-derivation exists at exactly 2 points** (everything else = frozen clip-anchored constants / relative schedules; concurs with the pre-registered §3.4 END-anchor classes):
1. **Grasp-entry XY derivation** (once, pre-hover): caveat-a Y re-center (`test_newton_clip_routing.py:3862-3866`, PRE-STEP :3517) + fix-⑤ X-follow (dx≠0 gate, committed `0b711c6b31`); `x_grasp` otherwise = `GRASP_X` const (:3564).
2. **C2_REGRASP argmin re-target** to the ACTUAL settled cable (`:4404` `_kR` argmin, under Rs-LOCKED anti-revert markers :4401/:4417; square-on span-preserving), then cage servo (:4431 region). ⟦line numbers corrected by %12 at commit review — the doc's original :4335-4340/:4335/:4350 were stale pre-shift coordinates; the FACTS (argmin re-target, Rs-LOCKED) verified unchanged⟧

**Injection-point map (15-phase; mechanism = EE-target detour unless noted):**

| 15-idx | phase | cable-target source | EE-detour injection | rationale |
|---|---|---|---|---|
| 0,1 | HOVER / DESCEND | derived-at-entry (A+B1) | ✅ **SAFE, primary** | pre-contact; recovery = next absolute waypoint; the 2 worst γ⊥ cells (2.497/1.257) live here |
| 2 | GRASP_CLOSE | — (servo) | ⛔ skip | close servo interference |
| 3 | LIFT | relative 12-substep | ⚠ tiny-only / avoid | retention choreography-sensitive (RS71:26 WR recipe); drop risk |
| 4 | ROUTE_C1 | frozen (C1 const) | ✅ small | cable under tension; drag = conservative-definite banked |
| 5 | C1_SEAT | frozen | ⚠ small, pre-seat only | verdict-critical precision |
| 6 | C1_PIN | pin event (:4063-4071) | ⛔ skip | authorized kinematic exception fires |
| 7,8 | UNCLAMP / RISE | relative | ⛔ skip | gripper state changes mid-phase |
| 9,10 | GUIDE_C2 / PRELIFT | frozen guide | ✅ small | post-pin, cable anchored at C1 |
| 11 | C2_REGRASP | **derived (B2 argmin)** | ✅ **SAFE (R-arm detour pre-contact), primary** | directly teaches ee-only↓ (now 0.973) |
| 12 | C2_TRANSPORT | frozen | ✅ small | as 4 |
| 13,14 | C2_DUAL_SEAT / SETTLE | frozen | ⚠ small, pre-seat only | verdict-critical |

**Injection legality (INVARIANTS):** EE-target detour = DiffIK-legal (targets via IK, no teleport; both arms remain engaged → INV#1 OK; magnitude bounded → INV#2 span watch). Cable **xfrc push** = physics-faithful force (instrument precedent: xfrc inert-force true-positive) but = a new recording-time disturbance class → Rs authorization needed if wanted. Cable **teleport = forbidden** (`prohibited.md` kinematic trick). IC offsets = already DR (that lever is exhausted for restoring — B2's finding).

**Label structure (why recordings supervise restoring at all):** the converter's label = per-step **next-waypoint** absolute target (`route_demo_to_bc.py:242`). During a detour's RECOVERY the recorded obs are off-path while wp = the script's legit route target = a restoring label, automatically. ⚠ The detour's OUTBOUND frames have wp = the detour waypoint = **ANTI-restoring labels → must be masked** (recorder marks injection windows in meta; converter drops outbound, keeps recovery). This mask is (ii)'s one converter build item.

---

## §4. Options

### 4.1 Summary table

| option | mechanism (1 line) | predicted effect 〔推測 — mechanism-reasoned〕 γ⊥ mov / pair / beat | **off-path obs 物理整合性 (%12 判別軸)** | falsifier (OG) independence | cost build / GPU | key risks | touch-points (locked?) |
|---|---|---|---|---|---|---|---|
| **(i) DAPG RL leg** | BC-init + RL fine-tune in a whole-route MDP env; reward = route-progress + seat predicates (sparse) + BC anchor | γ⊥↓ IF reward correct — no offline guarantee; pair/beat n/a pre-hoc; OG still applies offline post-train | ✅ physics (rollouts) | ✅ independent | **weeks-class** (env = ABSENT co-root) / high (PPO + HIGH-COST-GATE) | P2 BLOCK anatomy §4.2-(i); reward pathologies; exploration on long horizon | NEW env file(s) + task_config = **L3 + design gates + HIGH-COST-GATE** |
| **(ii) perturb-and-recover recordings** ⭐ | EE-target detours at safe phases (§3 map) mid-recording; script restores; record; mask outbound; BC on augmented set | movable γ⊥ ↓ (direct supervision at {0,1}); ee-only ↓ ({11} R-detour); seg-follow ~unchanged; beat ↑ | ✅ **physics-generated obs — structurally consistent (E15-(a) 構造回避)** | ✅ **independent** (probe ≠ data generator) | small (injection hooks flag-gated + outbound mask) / **~2-3h wall** (≈20-30 rec, GPU-0 4-way, CP-C actuals basis) | injection alters downstream validity (reuse CP-C filters); recovery frames cluster near-manifold (dwell/magnitude schedule); LIFT drop risk (avoid) | `test_newton_clip_routing.py` = committed canonical → **flag-gated default-off + byte-identity proof (precedent 2×: recorder, fix-⑤)** = L3-lite |
| (ii-b) DART-style noisy expert | continuous small action noise during recording instead of discrete detours | as (ii) but denser small-perturbation coverage; less far-off-path reach | ✅ physics | ✅ independent | same as (ii) | noise during close/seat = validity risk → phase-gate it = converges to (ii) | same as (ii) |
| **(iii) DAgger** | roll out policy, query scripted expert at VISITED states, relabel, retrain, iterate | γ⊥ ↓ at policy-visited neighborhoods (distribution-matched — best asymptotics) | ✅ physics (visited states) | ✅ independent | moderate (runner full-state dump + relabel script) / **GPU: rollouts 15-16 min each** (B1 actuals) × m × k rounds ≈ 4-5h+ | early rollouts visit FAR-off states where the frozen-waypoint expert is least valid (state-blind outside §3-B points); machinery before evidence | runner ext + new relabel script (route untouched) |
| **(iv) restoring-augmented BC (denoising)** | synthetic obs perturbation + label preservation (ee legs) / label co-move (seg legs), sampler = the OG co-move model | movable γ⊥ ↓ **on the probe family**; ee-only ↓; **seg-follow ↑ via seg-co-move leg**; beat needs augmented-null | ⚠ **model-consistent only** — sampler constrained to the co-move manifold (`og_b` `_holder_axes` coupling); linear approx of grasp coupling = residual E15-(a) risk | ⚠ **circularity** — trains on the same perturbation family the gate probes (teach-to-the-test); mitigations §4.2-(iv) | small (converter augmentation branch) / **~0 GPU-h** (train 90s + OG offline) | 「ignore obs」memorization endpoint (= CP-D null, measured); circular GO not bankable alone | converter only (+og held-out-direction param) — **no locked-file touch** |
| (adj-A) DR densification | more/denser offsets (e.g. 5mm grid) — on-manifold diversity | seg-follow ↑ (leg 2); γ⊥ mov ~unchanged (B2 proved) | ✅ physics | ✅ | 0 build / ~recording cost | not an off-path mechanism — adjunct only | none (existing flow) |
| (deprioritized) offline-RL (IQL/CQL) on (ii)-data | value-weighted imitation | — | ✅ | ✅ | new trainer + reward anyway | superset of (i)'s reward problem at lower authority | listed for completeness (charter「add others」), not scoped further |
| (deprioritized) HG-DAgger / human labels | human corrective labels | — | — | — | human-in-loop at scale = infeasible here | — | — |

### 4.2 Per-option detail

**(i) DAPG RL leg — P2 BLOCK addressability (charter: addressable or structural?).** Delta vs the P2 BLOCK state: **demos now EXIST** (B2 banked 11 survivors + recorder committed `fd005ab83f`) — but under the **B2 contract (obs 27D / 6D abs-target)**, NOT P2's 49D/12D residual contract. Re-scoping (i) onto the B2 contract dissolves several issues: CRIT2 (demos) largely RESOLVED; HIGH5 (rot dims inert) **moot by construction** (6D position-only); MED10 (gripper channel) moot (scripted, B contract). What STANDS: **M-A/HIGH6 (whole-route MDP env ABSENT) = the co-root — a from-scratch L3 build re-expressing the imperative choreography (servos :3358-3369/:4430-4436, eq-pin :4063-4071, variable-convergence ik_move) as a per-RL-step VecEnv**, incl. the CRIT1 phase-advance fork (script-schedule vs agent-earned); HIGH4 (seat-ori clause — undischarged, G7); HIGH3 (anti-hover calibration if any dense terms); MED8 (seated-seg obs index); M-B (W_ORI); retention authority partially returns in the full-policy (non-residual) framing (policy drives EE targets directly) but close/pin stay scripted. **Verdict: addressable-by-large-build + Rs design decisions — NOT permanently structural, but the cost class is weeks + design gates + HIGH-COST-GATE, and B2 showed the cheap-offline path is not yet exhausted.** Reward sketch if revived: sparse route-progress (phase-completion predicates from the recorder's own phase events) + seat predicates + DAPG BC anchor (`train_common.py:87-92` α anneal exists) — sidesteps P2's dense-reward pathologies (HIGH3-class) but inherits sparse-exploration risk; BC init (B2 policy) mitigates on-path, NOT off-path (that is DQ7's own gap — circular unless (ii)/(iv) data feeds the init).

**(ii) perturb-and-recover ⭐ — the evidence-bearing leg.** Mechanism: flag-gated (default-off, byte-identity proof like `DEMO_RECORD`/fix-⑤ None-path) EE-target detour injections at §3-map SAFE phases: hold-at-offset dwell (so off-path obs frames accumulate) → release → script's absolute-target servo restores → recorder captures; converter masks outbound frames (meta injection windows). Magnitudes: probe-matched 2-10mm + tail to ~20mm (Rs envelope decision D-3); per-arm single-sided detours (INV#1: both arms stay engaged; INV#2: span-preserving bound). Teaches exactly the two worst movable cells ({0,1} = 2.497/1.257) + the ee-only leg ({11} = 0.973). **What OG measures:** full §3.3 table re-run offline (0 GPU) — genuinely independent (the probe did not generate the data). Attribution: replicate-null re-train (~90s) → beat. Est: ~20-30 recordings ≈ 2-3h wall (GPU-0 4-way; CP-C actual: 18 runs ≈ 1.5-2h) + convert/train ~minutes. Risks: (r1) injections change downstream outcomes → reuse CP-C validity/seat filters; (r2) recovery transient short → few far-off frames → dwell scheduling; (r3) LIFT/seat phases = avoid or tiny per §3 map; (r4) locked-file touch = L3-lite with the established byte-identity pattern.

**(iii) DAgger — defer (contingent).** Correct asymptotics (trains at the policy's OWN visited states) but: (a) needs rollouts (15-16 min each, B1 actuals) × m × k + runner full-cable-state dump + relabel machinery; (b) the expert is state-blind at frozen-waypoint phases (§3-B) — its answer to a far-off-path query is「the waypoint」, a valid restoring label toward the path but blind to where the cable actually is → early DAgger rounds (policy still integrator-ish off-path) query exactly where the expert is weakest; (c) strictly dominated as a FIRST step by (ii) (same teacher, no policy-in-loop, physics-consistent, cheaper). Revisit iff (ii)+(iv) land between STOP and GO (γ⊥ improved but off-GO), where distribution-matching is the known remaining gap.

**(iv) restoring-augmented BC — 0-GPU pathfinder with two eyes open.**
- **E15-(a) resolution (%12 directive, explicit):** dimension-independent noise produces physically impossible obs post-grasp (EE and held seg are mechanically coupled). Constraint: the augmentation sampler is **restricted to the co-move manifold** — perturb (holder-EE, seg) JOINTLY per the holder coupling, exactly the model the committed gate already encodes (`og_b`: seg co-moves with `_holder_axes(phase)` for `p>=2`; pre-close = free dims). ee-legs: perturb R-ee (or non-holder) with seg fixed + label PRESERVED → teaches ee-only→0 / γ⊥→0. seg-legs: perturb (L-ee+seg) jointly + label CO-MOVED → teaches seg-follow→1 (**the only option that directly teaches leg 2**). Residual risk stated honestly: the co-move model is a LINEAR approximation of grasp coupling — synthetic obs are *model*-consistent, not *physics*-consistent; **this is the (ii)-vs-(iv) discriminating axis** (%12): (ii) gets consistency from physics for free; (iv) buys it with a model.
- **Falsifier circularity (new risk, surfaced here):** (iv) trains on the SAME perturbation family the OG gate probes → an OG GO on those cells is partially teach-to-the-test. Mitigations (pre-registerable): (m1) hold out perturbation DIRECTIONS/magnitudes from training, gate on the full set; (m2) **augmented-null** (replicate-null + the same augmentation) so beat isolates diversity-vs-augmentation; (m3) final arbiter = physics-generated off-path frames — i.e., **(ii)'s recordings double as (iv)'s independent eval set**; (m4) closed-loop rollout stays the ultimate test. Consequence: **(iv) alone is not bankable**; its value = a ~0-cost pathfinder — if γ⊥ does NOT move even under teach-to-the-test conditions, that is a strong capacity/data structural finding at zero spend (and the detection the charter asks for —「how would we detect ignore-obs?」— is (m2) + the pair seg-follow band: an obs-ignoring policy fails [0.8,1.2] by construction, as the CP-D null's measured endpoint shows).
- Cost: converter augmentation branch + og held-out-direction param; train 90s; OG offline. No locked-file touch → lowest governance of all options.

---

## §5. Reuse-first inventory (charter §3 mandatory — explicit paths)

| Asset | Path | Reuse in DQ7 |
|---|---|---|
| **OG offline gate** (§3.3 verdict table, γ⊥, pair probe, co-move model, carried-stops) | `thread_isaac_lab/scripts/og_offline_gate.py` (committed `942ce85f1c`+) | **The falsifier for ALL options** — offline, 0 GPU, 2× validated (B1′/B2 predicted in-sim, 0 surprise). Caveat: (iv) circularity → (m1)-(m4) |
| Demo recorder (per-frame superset, DEMO_RECORD-gated) | `thread_isaac_lab/scripts/route_demo_recorder.py` (`fd005ab83f`) | (ii) recording base; NEW: injection-window meta marks |
| Converter v2 (union affine 15-phase; label = next-waypoint) | `thread_isaac_lab/scripts/route_demo_to_bc.py` (`c5e58d5636`) | (ii): outbound-frame mask; (iv): augmentation branch; labels already restoring-structured (§3) |
| BC trainer + replicate-null protocol | `thread_isaac_lab/scripts/bc_train_route.py` + `b2_cpD_report.md` | 90s/2000ep retrains; attribution nulls (incl. augmented-null) |
| Runner v2 (per-offset schedule, committed unused) | `thread_isaac_lab/scripts/policy_route_runner.py` | (iii) rollouts; any post-GO closed-loop leg |
| CP-C validity filters (seat-filter, R_MISS exclusion) | B2 CP-C flow (`state.md:43`) | (ii) run validity |
| Canonical route + fix-⑤/byte-identity pattern | `test_newton_clip_routing.py` (`0b711c6b31`) | (ii) injection hooks follow the established flag-gated + None-path sha proof pattern |
| Device/EGL pins | memory: canonical route device-fragile (cuda:0), MUJOCO_GL=egl | all recordings on cuda:0 |

---

## §6. RECOMMENDATION (推奨 — labeled, decision = Rs)

**Staged package, cheapest-falsifier-first; every stage OG-gated offline before any further spend:**

1. **(iv) pathfinder first** — ~0 GPU-h, small converter branch. Pre-register (m1) held-out directions + (m2) augmented-null. Outcome A (γ⊥ moves): proceed to 2 with confidence + keep (iv) as a regularizer. Outcome B (γ⊥ immobile even teach-to-test): structural capacity/data finding → escalate design question to Rs before spending GPU.
2. **(ii) as the evidence-bearing leg** — injections at {0,1} + {11} (+small at transports), ~2-3h GPU + small flag-gated build with byte-identity proof. Independent OG re-run; (ii) frames also serve as (iv)'s independent eval set (m3). **Bankable** if OG GO → held-out rollout per §8-1 bars. Fold adj-A (denser offsets) into the same recording batch for leg 2 at ~0 marginal build.
3. **(iii) deferred-contingent** — only if 1+2 land between STOP and GO (restoring improved, off-GO): distribution-matching is then the known residual gap; reuse (ii) machinery.
4. **(i) escalation path** — re-scoped DAPG on the B2 contract (6D abs, demos exist; §4.2-(i) anatomy: env build = the standing CRITICAL cost). Revisit only if the imitation family is exhausted — mirrors the DQ1 structure (A/C retained, not killed).

**Why this order:** maximizes evidence-per-GPU-hour; addresses BOTH failing legs (§1); keeps the falsifier independent where it matters (bankable claims ride on (ii)/physics, not (iv)/model); INVARIANTS untouched at every stage; the only locked-file touch ((ii) hooks) follows a twice-proven pattern.

## §7. Rs decision points

- **D-1:** adopt the staged package (iv)→(ii) [→(iii) contingent / (i) escalation]? or reorder (e.g., (ii)-only)?
- **D-2:** injection mechanism envelope — EE-target detour only (recommended)? cable-xfrc push also (new disturbance class)?
- **D-3:** (ii) magnitude envelope: probe-matched 2-10mm + tail to 20mm?
- **D-4:** leg-2 (seg-follow) teacher: (iv) seg-co-move leg / adj-A densification / both (recommended: both — they cross-validate)?
- **D-5:** (i) re-scope spec: draft now (parallel paper exercise) or after the (ii) verdict (recommended: after)?

---
**Conservatism note (§運用15):** every "predicted effect" above = 推測 (mechanism-reasoned, no new measurement — offline predictions to be settled by the OG gate itself); all quoted numbers = measured, cited to primary instruments. This doc changes no code and is 0-commit pending %12 review.

*COORD2 %10 — 2026-07-03 05:12 JST*
