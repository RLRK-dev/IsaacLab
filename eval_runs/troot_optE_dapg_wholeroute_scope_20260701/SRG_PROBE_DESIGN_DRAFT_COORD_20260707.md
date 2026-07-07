# SRG PROBE DESIGN — DRAFT (Stage-B first step) — %11 COORD (w2:p3)

**node:** T-ROOT-optE-route-dapg-C1C2-P2-routeexec (IN_PROGRESS) — charter %12, D-1=C.
**scope:** **DESIGN DRAFT only — no-GPU, PLANNING-only, no code/config edit.** Authorizes nothing to build/run. `/force-design` design-gate + %12 [VERIFY] gate any implementation; GPU measure gated on design-gate PASS + %12 授権.
**rev:** v0.1-draft (2026-07-07 18:22 JST). Supersedes nothing (first SRG design artifact).
**re-trigger:** %12 Stage-B RE-TRIGGER 18:06 (in-scope, no-GPU DESIGN only; build/GPU HOLD comp3-8).

---

## §0. Grounding (anchor set, §運用4) — read + cited
- LEDGER route-executor row (`00-DESIGN-STATUS-LEDGER.md:47`, ⟦17:29 Stage-A COMPLETE⟧ marker) — Stage-A 3-leg PASS, Stage-B remain incl "minimal SRG probe = 別 gate, build/GPU HOLD".
- node `state.md:16` (現況 17:29) + `:30` (newest session_history) — Stage-B HOLD carry incl minimal SRG probe FIRST.
- build plan v0.2.2 `BUILD_PLAN_ROUTEEXEC_LAYERB_COORD_20260707.md` §7 (SRG revised) + §5 Stage-B gate + §11 design-gate.
- 5体 verdict `LAYERB_5TAI_VERIFY_VERDICT_RSTECHLEAD_20260707.md` CC3 §20-26 (CH1 CRITICAL creep-budgeted).
- creep SSOT: `LL-Creep-Characterization.md` + `LL-G3-Vacuity.md` + `LL-Condim-Rolling-Mechanism.md`.
- pre-check I1 (grip-efficacy fidelity-bound) = node `state.md:43` (design-gate 05:43 §11 fold).

## §1. [L-TRIAGE] = L3 (subject), PLANNING-only (this deliverable)
- Subject keywords = grip / creep / physics / substep / solver / force → §0 L3 auto-escalation (path-independent). Implementation of the SRG probe (a new measurement script + a temporary grasp_actuation=ON toggle) is **L3**.
- **This deliverable (the DRAFT doc) = planning artifact, no code/config change → no build gate fires yet.** Gate chain before ANY implementation: `/force-design` design-gate → %12 [VERIFY] (depth %12) → RULE-CHECK → build. Mirrors how BUILD_PLAN v0.1 was handled (L3 subject, planning-only doc, gated).
- Prior-art guard (§運用4) run: `BLOCKER_CONTEXT_FOUND` on {no-slip, creep, 4-substep} — the blocker context IS the CC3-CH1 / G3-vacuity lesson this design **implements**. **Delta from failed path:** design does NOT use the banked-UNREACHABLE no-slip criterion; it uses the creep-budgeted redesign that `LL-G3-Vacuity.md:29-36` mandates + re-measures the untransferred 4-substep floor. Sanctioned redesign, not repeat. Disposition = PROCEED.

## §2. Purpose (what the SRG gate decides)
- **SRG = the grip-efficacy go/no-go** that resolves the 4-substep grip UNKNOWN (pre-check I1, node `state.md:43`) **BEFORE** committing to build comp3/comp4/comp5. Rationale = CC6 (`verdict:42`): building comp3/4/5 on the unverified 4-substep grip premise = "building on sand" → if SRG FAILs and fix = PD/substep, those components need rework.
- **What it must show:** the RL-fidelity (4-substep) grip can hold C1's cable well enough — over the actual route service exposure — that a downstream trainer can learn C1-retention→C2-seat. NOT "no-slip" (physically unreachable).

## §3. THE substrate constraint that shapes the whole gate (cited)
- **Intrinsic creep is unavoidable + load-insensitive** (`LL-Creep-Characterization.md:10-15`): R4=134.9 µm/f, **R6=60.4 µm/f @F=0**; 2.2 N (5× service) modulates only −7~14%; no runaway, no slip-onset event; slip linear at all loads.
- **"no-slip / slip-onset ≤2mm" gate = physically UNREACHABLE** on every tested config (intrinsic creep crosses 2mm in ~15f R4 / ~33f R6); caused 2× false-PASS (`LL-G3-Vacuity.md:16-18`). Grip = form-closure **CAGE**, not a slip-onset hold (cage ≠ hold).
- **Creep-budgeted re-design rule** (`LL-G3-Vacuity.md:29-36`): (a) rate-under-load = rate_load/rate_unloaded ≤ ~1.2 (runaway check); (b) service-exposure window = (frames exposed to load) × creep_rate ≤ displacement budget. Never an absolute mm cap without measuring the floor.
- **⚠ ALL banked creep = 10-substep** (`s5_calib_bench3r.py:163` uses `T.SIM_SUBSTEPS`=10; `task_config.py:101`). **RL runs 4-substep** (`newton_skill_env_base.py:95` RL_SIM_SUBSTEPS=4, coarser integration). **4-substep creep floor = UNMEASURED** ("10-substep bank doesn't transfer, likely worse" — plan §7:76). This is the single load-bearing gap the probe must close FIRST.
- **frame-comparability note:** RL_SIM_DT = DT/4 (`newton_skill_env_base.py:96`), SIM_DT = DT/SIM_SUBSTEPS ⇒ one physics frame = DT (=N·substep_dt) in BOTH regimes → "µm/f" is directly comparable 10-vs-4-substep (same f duration = DT; the difference is integration granularity, not frame length). (verify in harness.)

## §4. [CHECK] Inventory — reuse-first (AGENTS.md gate; feedback-inventory-existing-results)
**REUSE (proven):**
- `s5_calib_bench3r.py` (285L) — THE corrected creep instrument. `landing_control()` (rule-2 free-body true-positive, fail-closed) + `pinch_axial_cell()` (creep µm/f = `com_y` polyfit slope over post-grace hold `:229`; slip-vs-pads series; N/collapse/blink stats; per-substep `body_f` readback assert `:176-177`). Force path = `state.body_f` LIN-first f_y per-substep after clear_forces (the CORRECTED instrument; `d.xfrc_applied` = INERT no-op on SolverMuJoCo CPU — `LL-G3-Vacuity.md:12`).
- Companion benches: `s5_calib_bench.md` (§3b consolidated re-design rule), `s5b_p1v.md` (vertical static slip 49-202 µm/f), AR creep renders (`troot_ar_*_20260627/28`).
- Production contact SSOT already pins the best passive levers: `task_config.py:187` MUJOCO_PAD_SOLREF = **R6-b×4 (already the default** — creep already at the 60.4 floor, NOT 134.9); `:196` impratio=10; `:176` condim=6 (rolling rows present → friction levers ACTIVE, `LL-Condim-Rolling-Mechanism.md:14`).
**GAP (confirmed absent):**
- **No 4-substep creep measurement exists** — all benches are 10-substep. Re-measure genuinely needed.
- **`noslip_iterations` is NOT wired into the newton route path** (grep = comment-only, `task_config.py:178`). The 110×-best lever (`LL-Creep-Characterization.md:39`) requires a **code change to access**, not a config flip. Material for the lever ranking (§7).

## §5. Probe design — staged, early-exit, cheapest-first
The probe is ONE harness with the creep-floor re-measure as its FIRST internal step (plan §7:75-76), then go/no-go, then tail screening. Each stage early-exits to STOP+surface on catastrophic result (no threshold-relax, plan §5:64).

**Stage 0 — 4-substep creep-floor re-measure (FIRST, cheapest, single nominal):**
- Reuse `s5_calib_bench3r.pinch_axial_cell` measurement method, swapping the substep loop `T.SIM_SUBSTEPS`→`RL_SIM_SUBSTEPS`(=4) and pinning the R6 production solref (`task_config.py:187` = the default). Cells = R6 × {F=0, F=0.44 service}. Keep landing_control + body_f readback (rule-2 fail-closed).
- Output = creep µm/f @4-substep vs the 10-substep R6 bank (60.4). Quantifies the transfer factor.
- **Early-exit:** if 4-substep floor ≫ pre-registered multiple of the 10-substep bank (e.g. > K× — K to pin in design-gate), STOP+surface: the RL fidelity can't hold before spending on grasp/tail. (per-axis conservatism §8: creep-floor = unknown-until-measured.)

**Stage 1 — C1-grasp+hold go/no-go (single nominal, real route geometry):**
- Grasp_actuation=ON 4-substep servo-close at nominal C1, hold over the **service-exposure window** (route episode's under-load hold-frame count W_svc — pin from the recorded route; horizon 900 RL steps per LEDGER but only the held legs count), service load 0.44 N via corrected body_f.
- **PASS criterion = creep-BUDGETED (NOT no-slip):**
  - (b) service-exposure: `creep_rate(4-substep) × W_svc ≤ retention_margin_budget`, where the budget is tied to the retention predicate (C1-retention flank/z margin `z_c1<840 ∧ flank<840` — plan §3:46; C2-seat wall-dist≤0.5mm — plan §3:47). If total held-creep stays within the cage/seat tolerance, PASS.
  - (a) runaway check: `rate_load / rate_unloaded ≤ ~1.2` (from Stage 0 pair). Substrate is load-insensitive so this should pass trivially — a FAIL here = a new regime, surface it.
- **per-axis:** Stage 0/1 measure axial `com_y` (the s5 method). Retention-relevant axis = cable escaping the claw (lateral/flank + z). Measure both; report per-axis (§8 conservatism).

**Stage 2 — tail-cell screening (CC3-CH2, plan §7:77):**
- Repeat Stage 1 at: nominal + **DR-corner (±16mm table-void edge)** + known-hard cell. **gate = worst-screened** (nominal-only is banked-insufficient — nominal is easiest).

## §6. Levers (CC3-CH3, ranked cheap→campaign — plan §7:78) — with wiring reality
Ranked by cost to try IF a stage FAILs (do NOT pre-apply; measure first):
1. **impratio** (config knob, ACTIVE: condim=6 rolling rows) — rate ∝ 1/impratio (`LL-Creep-Characterization.md:39`). Cheapest (constant edit, but L3/SSOT `task_config.py:196`).
2. **solver iterations** (config knob) — cheap.
3. **pad friction / solref** (config; R6 already the best passive form — headroom limited, `task_config.py:187`).
4. **`noslip_iterations`** (110× banked-BEST, `LL-Creep-Characterization.md:39`) — ⚠ **NOT wired in the newton route path** (§4): requires a code change to access, so it is NOT "cheap" here despite being the strongest lever. Reclassify: high-value / medium-cost (wiring).
5. **substep 4→N** = **LAST / Rs-level** (campaign-affecting: raises RL step cost across all training; plan §7:78). Not a COORD-level lever.
- **SRG FAIL → STOP + surface decision point (NO threshold-relax)** (plan §5:64). Lever choice on FAIL is surfaced to %12/Rs, not self-applied.

## §7. Conservatism (per-axis, CC3-CH5 — plan §7:79) + observable-bound (CC3-CH4 — plan §7:80)
- **substep** = conservative-with-caveat (4-substep coarser than the 10-substep oracle → measures the HARDER regime; but if a lever later changes substep, re-validate).
- **offset** = non-conservative (nominal easiest → tail screening §5 Stage 2 is mandatory, not optional).
- **creep-floor** = unknown-until-measured (Stage 0 is the resolver).
- **observable-bound, no silent MARGINAL-ACCEPT:** verdict binds to (i) creep metric µm/f, (ii) tail-cell results, (iii) **quantified slip-time-series** (not start/end only — `LL-G3-Vacuity.md:26`). **Single nominal video + human-GT is INSUFFICIENT** (CC3-CH4). Final physical-validity verdict = human-GT (`feedback-grasp-verdict-numeric-and-video-analyst-both-unreliable-human-ground-truth`) + video-first leg (§運用14) on the grasp/hold with claw-zoom for intra-finger slip (`feedback-video-detect-intra-finger-cable-slip`).

## §8. Device + env (surfaced) 
- Stage 0 (isolated pinch, s5 pattern) = CPU-OK (s5 precedent all 0-GPU, `s5_calib_bench3r.py:70` device="cpu").
- Stage 1/2 (real route grasp geometry) = **cuda:0 ONLY** (route device-fragile; `project-canonical-route-device-fragile-cpu-vs-cuda`: cuda:1 3/3 MISMATCH → GPU1 independent-workload-only). This is the "GPU measure" the re-trigger gates.

## §9. Decision structure (the gate output)
- **PASS** (all stages, worst-screened tail within budget) → unblock comp3 (grasp_actuation flag-flip) / comp4 (write-site FLAG-GATED) / comp5 (C2 scene) → live DoD ⑨b/⑥/⑦(b)/C2-seating video → HIGH-COST → **/production-launch-gate** before any training.
- **FAIL** → STOP + surface decision point; lever selection (§6) surfaced to %12/Rs; substep 4→N = Rs-level. NO threshold-relax (plan §5:64).

## §10. Design decisions to surface (§運用18, no-speculation) — %12 rulings requested
- **D1 — env for Stage 0/1.** Recommend: Stage 0 in the ISOLATED s5 pinch env (creep floor = substrate property, representative via shared task_config pad/solref/condim SSOT; cheapest, CPU); Stage 1/2 in the REAL route geometry (representativeness gate — C1@X=0.35 over-void, `reference-clip-positions-vs-grasp-void-geometry`; the go/no-go must be the real grasp). **Alternative:** unify both in the real route env (more representative for the floor too, but heavier + needs grasp_actuation=ON earlier). REQUEST %12 ruling.
- **D2 — grasp_actuation=ON for the probe without building comp3.** The probe must toggle grasp_actuation=ON in a STANDALONE probe (temporary, measurement-only), NOT the comp3 production build (which stays HELD with its write-site flag-gating). Confirm this separation is acceptable (it is the only way to exercise the 4-substep grip before the gate it feeds — CC6 intent).
- **D3 — W_svc (service-exposure window) source.** Pin the under-load held-frame count from the recorded route (which legs hold C1's cable under load). Need %12 confirm the recorded route exposes this cleanly, or whether to bound it conservatively (full-horizon 900).
- **D4 — early-exit multiple K (Stage 0).** The pre-registered multiple of the 10-substep bank above which Stage 0 STOPs. Propose to pin at design-gate (/force-design) with a physical rationale (budget-vs-margin), not an arbitrary number.

## §11. Next step
- `/force-design` design-gate (grip servo PD close + 4-substep contact + creep budget) — pins K (D4), W_svc (D3), the exact criterion arithmetic, and the servo/contact fidelity analysis. `/geometric-design` skippable IFF Stage 0/1 use existing route geometry (no new scene geom) — confirm with D1.
- Then surface DRAFT + design-gate output to %12 for [VERIFY] (depth %12). PASS → %12 GPU-measure 授権.

---

## §12. DESIGN-GATE OUTPUT (/force-design, no-GPU) — %12 D1-D4 rulings folded (18:33)
%12 rulings: D1 ACCEPT (S0 isolated pinch / S1-2 real route; representativeness caveat = HARD-verify contact-SSOT-share + frame-comparability) / D2 ACCEPT (standalone probe, proven servo, locked-file 不触, production config 不編集) / D3 = W_svc from recorded route C1-under-grip-load window (surface if ambiguous) / D4 ACCEPT (K from physical budget-vs-margin). **/geometric-design SKIP justified** (D1: S0=existing s5 geom, S1-2=existing route geom, NO new scene geometry).

### Step 1 — Parameters (MEASURED, not changed; D2 = production config 不編集)
| param | value | file:line | role in probe |
|---|---|---|---|
| GRIPPER_SERVO_TARGET_KE | 66.7 | task_config.py:314 | 2f85 driver servo (soft, force-capped close = CAGE) |
| GRIPPER_SERVO_TARGET_KD | 2.0 | task_config.py:315 | servo damping |
| GRIPPER_DRIVER_CLOSE_RAD | 0.7407 | task_config.py:291 | close target (CONTACT/FORCE-based, NOT position-reached — :293-295) |
| MUJOCO_PAD_SOLREF | R6-b×4 (−65789,−2105.3) | task_config.py:187 | pad↔cable contact (production default; creep floor 60.4µm/f) |
| MUJOCO_CONTACT_CONDIM | 6 | task_config.py:176 | rolling rows → friction levers ACTIVE |
| MUJOCO_OPT_IMPRATIO | 10.0 | task_config.py:196 | friction-cone impratio (lever, ∝1/creep) |
| RL_SIM_SUBSTEPS | 4 | newton_skill_env_base.py:95 | THE regime under test |
| SIM_SUBSTEPS | 10 | task_config.py:101 | the banked (non-transferring) regime |
**No force-param CHANGE.** The probe toggles ONLY `grasp_actuation=ON` (standalone, temporary — D2). The measured hierarchy is the production SSOT, unperturbed.

### Step 2 — Force-hierarchy consistency (probe preserves production hierarchy)
- 2f85 servo (ke=66.7, force/effort-capped close) < contact (R6 stiff-overdamped + MUJOCO_CONTACT_KE=40000, task_config.py:168) ⇒ servo COMMANDS close, contact TRANSMITS the cage force, cable is CAGED (form-closure, not position-squeeze). This is the "cage≠hold" of CC3-CH1 — the servo does not chase a position; it holds a force-capped cage. ✓ hierarchy intact, probe non-perturbing (D2).

### Step 3 — dt-dependency (THE crux; /force-design Step 3 = why the floor may not transfer)
- PD/contact force is integrated PER SUBSTEP: `F = ke·err − kd·(Δq/dt)`. RL_SIM_DT = DT/4 (newton_skill_env_base.py:96) vs SIM_DT = DT/10 ⇒ one physics frame = DT in BOTH (N·substep_dt=DT), so µm/f is comparable, BUT the 4-substep path takes 4 LARGE steps vs 10 small steps per DT → coarser contact/friction resolution per frame → the regularized-friction creep (no stick-state, LL-Creep-Characterization.md:35) integrates differently. **Direction of transfer = UNKNOWN-until-measured** (CC3: "likely worse"); S0 is the resolver. This is the single load-bearing dt-fidelity gap the whole gate exists to close.

### Step 4 — Sensitivity / FAIL-response levers (do NOT pre-apply; measure first)
The substep sweep (4 vs 10) IS the primary measurement. IF a stage FAILs, levers ranked (§6, cheap→campaign): impratio (config, active) → solver iters → pad friction/solref (R6 already best) → **noslip_iterations (110× best but NEEDS code-wiring, §4)** → substep 4→N (LAST, Rs-level). FAIL → STOP+surface, NO threshold-relax (plan §5:64).

### Step 5 — Changed files = NONE (this gate). Build (Stage-B, HELD): 1 NEW standalone probe script (scripts/), + a temporary grasp_actuation=ON toggle inside it. task_config / locked file / route_env_config UNCHANGED (D2).

## §13. PINNED (criterion arithmetic, W_svc, K) — ⚠ per-axis (supersedes DRAFT §5 single-axis)
**⭐ Per-axis refinement (design-gate discovery, grounds CC3-CH5):** intrinsic creep is **AXIAL** (−y along cable, LL-Creep-Characterization.md:15); the retention predicate is **z/lateral** (z_c1<0.840m ∧ flank_max<0.840m, route_env_config.py:105-106; cage-escape). **Different axes.** Axial creep = cable sliding *through* the cage lengthwise → benign for retention (a different cable body becomes nearest-C1Y, still low-z). Lateral/z creep = cage escape → drops the cable. ⇒ the s5 `com_y` method measures the AXIAL floor (necessary-condition characterization); the GO/NO-GO gate is the LATERAL/z cage-escape over the hold. This also explains why "no-slip" was mis-specified (conflated benign axial slide with cage loss).

- **W_svc (D3):** grip holds continuously (L close always; both close except the phase-3 transit re-grasp within<0.5 — newton_route_env.py:210-212) across the 900-RL horizon (ROUTE_TERMINAL_STEPS=900, route_env_config.py:91). PHYSICS_STEPS_PER_RL=10 (newton_route_env.py:237) → **conservative upper bound W_svc = 900×10 = 9000 physics frames** (each=DT). ⚠ the under-LOAD subset (transit/lift legs where the cable resists — not the settled legs) is smaller; **SURFACED (§14, §運用18): the exact load-leg count needs route-mechanics read of run_route, not speculated.** Use 9000 as the conservative bound for the design; refine at measurement.
- **K (D4) — early-exit multiple, physical rationale (NOT arbitrary):** granularity-coarsening ALONE should scale creep by ≤ the substep ratio 10/4 = **2.5×**. So **K ≈ 3-4× (2.5× granularity + margin)** as a REGIME-CHANGE screen: S0 axial floor > K× the 10-substep R6 bank (60.4µm/f) ⇒ a NEW mechanism appeared at 4-substep (not mere coarsening) → STOP+surface. Also STOP on any qualitative breakdown (collapse>0 / badqacc>0 / NaN / never-engage — the s5 bench already emits these, s5_calib_bench3r.py:222-226,239). Below K → expected coarsening → proceed to S1 (the real budget). Confirm exact K at measurement.
- **Criterion (creep-BUDGETED, per-axis, per LL-G3-Vacuity.md:29-36):**
  - S0: axial floor r4 at 4-substep (R6, F∈{0, 0.44N service}); early-exit vs K.
  - S1 (a) runaway: `rate_load / rate_unloaded ≤ ~1.2` (from the S0 F-pair; substrate load-insensitive −7~14% so passes unless a new regime).
  - S1 (b) service-exposure (THE go/no-go): LATERAL/z cage-escape deviation over W_svc within the DIRECT cage-escape margins (DROP_LATERAL_DEV_MAX=60mm gross / DROP_LIFT_MARGIN=10mm / GRIPPING_ARM_SIGMA_CAP=2mm intent — newton_route_env.py:236,243,245) AND no DROP trip (contact-loss debounce=8, :244) AND end-of-hold task predicates hold (C1 z<0.840, C2-seat wall≤0.5mm — route_env_config.py:105,114). NOT no-slip.

## §14. Residual SURFACED (§運用18, no-speculation)
1. **W_svc under-LOAD subset** — the recorded route's exact load-bearing hold legs (vs settled legs) require reading run_route mechanics; I used the conservative full-horizon 9000-frame bound. Not speculated; flagged for the measurement build (or a cheap route-mechanics read if %12 wants it pinned tighter now).
2. **retention_margin → creep linkage is INDIRECT** — grip creep feeds C1-retention/C2-seat via route dynamics, not a closed-form arithmetic. The design gates on the DIRECT cage-escape margins (DROP thresholds) + measures the task predicates live at hold-end, rather than a mis-specified axial-creep→C1-z proxy (the exact trap that voided G3, LL-G3-Vacuity.md). Honest + conservative.
3. **per-axis conservatism (CC3-CH5):** substep = conservative-w-caveat (coarser=harder regime) / offset = non-conservative (→ S2 tail mandatory) / creep-floor = unknown-until-S0 / axial-vs-lateral = the §13 split.

---
*%11 COORD (w2:p3) 2026-07-07 18:48 JST. DESIGN DRAFT + /force-design DESIGN-GATE OUTPUT — PLANNING only, no-GPU, nothing built/run. %12 D1-D4 folded; /geometric-design skip justified. Force-hierarchy ✓ (non-perturbing, D2), dt-dependency = the crux, per-axis criterion pinned (⭐supersedes DRAFT §5 single-axis), W_svc/K grounded + residual surfaced (§運用18). Next = surface to %12 for [VERIFY] (depth %12: focused-or-5体). PASS → %12 Rs surface → GPU measure 授権. build/GPU HOLD comp3-8.*
