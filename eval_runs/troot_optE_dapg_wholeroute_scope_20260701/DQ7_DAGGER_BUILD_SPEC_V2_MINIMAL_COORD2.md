# DQ7 (iii) DAgger — v2 MINIMAL build spec (single-offset 1-rollout budget-test)

**Author:** COORD2 (%10). **Written:** 2026-07-04 00:43 JST (same-turn `date`).
**Supersedes:** `DQ7_DAGGER_BUILD_SPEC_COORD2.md` (v1) — 5体 pre-debate **FAIL** (3 CRIT + HIGH; direction UPHELD). **Rs 2026-07-04 00:2x = "A"** = build a **minimal single-offset 1-rollout DAgger iteration** to cheaply falsify the on-path/off-path **BUDGET** question before any full 8-proc m×k build.
**Charter:** %12 dispatch 2026-07-04 00:3x. **Status:** BUILD SPEC — **0-commit**, **INVARIANTS untouched**, **{11} OUT**. The 1 policy rollout runs only under Rs「ロールアウト承認」 + the `--rs-go` token (§3.3). Design decision = Rs 専権; §R = labeled RECOMMENDATION.
**Consumers:** %12 review → **%9 re-validate** (conformance to DECIDE §1 fixes; CP-(ii)-0→v2 precedent, NOT a new full 5体 debate) → %11 build.

---

## §0. Grounding (anchor set, §運用4 — DECIDE doc + code, all cites live-verified this session)

| Anchor | Cite | Fact used |
|---|---|---|
| DECIDE (v1 FAIL → v2 scope) | `DQ7_DAGGER_DEBATE_DECIDE_PCT12.md` §1 (fixes) / §2 (CC6 budget) / §3 (DECIDE scope) | 3 CRIT + HIGH accepted; v2 = minimal single-offset 1-rollout budget-test |
| **C1** relabel ≠ per-phase-const | DECIDE §1 C1 + live `test_newton_clip_routing.py:3941` (`GRASP_YC=mean(settled-cable-Y)`) / `:3953` (`x_grasp=mean(settled-cable-X)`, fix-⑤) | abs target **RAMPS** per control-step (Rz span p0 **392**/p1 97/p3 48mm; only p2 ~0.6mm), center = per-episode **settle** outcome → **relabel per CONTROL-STEP `T*(o,t)`**, reconstructed from THIS rollout's settle center; assert 88mm span/row |
| **C2** runner STOPs on live tree | live `sha256(test_newton_clip_routing.py)=7f5bc711…` **∉** runner `ROUTE_SHA_ACCEPT:35-38` {`9bdf8f63`,`ac0e3f53`} → `_assert_shas:131-140` STOP | route-sha re-sync REQUIRED + marker-integrity gate (⛔ANTI-REVERT verified live at `:4477/4493/4593` + pin `:1758`) |
| **C3** rollout ban is convention-only | DECIDE §1 C3 (`grep rollout prohibited.md CLAUDE.md`=0) | mechanical `--rs-go` token guard (mirror `_opt_i_prime_check:356`) |
| **C4** §9 {2,3} co_seg confound | `og_offline_gate.py:97` (co_seg p≥2) / `movable_all_go:453` / `null_beat:455` | γ⊥≤0.5 WRONG-SIGNED for {2,3} → **§9 = clean {0,1} ONLY** |
| capacity PASS (bar reachability) | `DQ7_CAPACITY_VERDICT_PCT12.md:19-20,33` | γ⊥{0,1}=**0.031/0.003** in ISOLATION → the clean-{0,1} ≤0.5 bar IS reachable by the arch (ground-truths the §9 bar, CC5 MED) |
| (ii)/(iv) budget (CC6 central) | `DQ7_II_CP5_CROSSPV_PCT9.md:27` + node `state.md:45` (iv Outcome-B) | (iv) synthetic restoring INTO on-path budget = conservative-definite-fatal; DAgger re-introduces budget via `D_base∪relabel` → the minimal tests it with REAL on-policy data |
| converter (reuse, H1) | `route_demo_to_bc.py` `PHASES15:58`, `_build_abs_affine:137`, `_abs_decode:186`, `_detect_schema:96` | per-offset raw→15-phase (obs 27D) abs+schedule, sha-pinned |
| runner rollout (extend) | `policy_route_runner.py` `_control_loop:652-778` (`obs_series.append:687`, `phase_idx:675`, `_policy_action:192/689-690`, abs-decode `:695-697`, `solve_ik_dual:721` returns residual `ik_cost`, `grasp_yc:767-776`, frame-assert `:618-619`, demo-replay `policy is None:691-693`) | closed-loop π rollout exists; per-step obs already dumped; settle-center live at `:775`; IK residual already computed |
| trainer / OG (reuse) | `bc_train_route.py:36-49` (seed-pin `:46`) / `og_offline_gate.py` `DR_MOVABLE:33`, `GPERP_GO=0.5:36` | retrain ~90s; γ⊥ metric, band=γ UNCHANGED |
| INVARIANTS | `RS71-System-Spec-SSOT.md §0:23-27` | #1 dual-arm / #2 88mm span / #3 DiffIK / #4 コ / #5 no-kinematic-trick |

---

## §1. Purpose — the ONE question this minimal answers (CC6 central risk)

**The budget question (why v1's premise mattered):** the capacity pre-test PASSed on an **isolated, decorrelated** synthetic set (no on-path budget competition) → the arch *can* represent restoring. But (iv) Outcome-B found that mixing synthetic restoring **into the on-path budget** was **conservative-definite-fatal** (couldn't teach off-path restoring without degrading on-path). DAgger re-introduces exactly that budget via `D = D_base ∪ relabel(on-policy off-path states)`. **The minimal tests whether ONE real on-policy iteration, aggregated under budget, moves clean-{0,1} γ⊥ toward ≤0.5** — i.e. whether REAL on-policy off-path data (unlike (iv)'s synthetic) breaks the plateau under budget, or reproduces (iv)'s conservative-definite tension.

**Read:** clean-{0,1} γ⊥ (+ off-path-row γ⊥, H4) moves toward ≤0.5 under budget → budget not fatal → scale to full 8-proc m×k. Plateau like (iv) → budget tension confirmed → route to (i)-RL (P2-CRITICAL, Rs re-decide). **This is a falsification, not a GO.**

---

## §2. Minimal scope (DECIDE §3 — nothing beyond)

ONE DR offset → ONE **β=0 pure-π** rollout of the current BC-(ii) policy, **truncated {0-3}** → **per-step relabel** `T*(o,t)` (C1) + **in-scene IK feasibility** (H2/H3) → **aggregate into D_base under budget** → **retrain** (seed-pin) → **OG γ⊥ on clean {0,1}** (C4) + **off-path-row γ⊥** (H4). β=0 ⇒ **no β-mix machinery** in v2 (per-step target is needed only for RELABEL, not rollout execution). Single-offset single-GPU ⇒ device-parity moot (H5 deferred).

---

## §3. Components (buildable — all DECIDE §1 fixes folded)

### §3.1 [H1] Per-offset 15-phase dataset-dir — reuse `route_demo_to_bc.py`  [BUILD, 0 rollout]
The chosen offset's `route_demo_raw.npz` → `route_demo_to_bc.py` → 15-phase `bc_dataset_abs.npz` (obs 27D) + `schedule.json` + `bc_dataset_abs_meta.json` (`abs_affine[15,6,2]`), **sha-pinned**. (Old b0/b1p dirs are 13-phase/25-D → unusable; H1.) **DoD:** conversion emits a 15-phase dir whose `meta.phase_names==PHASES15` (`:105` assert) + `obs_dim==27`; record the raw + converted shas.

### §3.2 [C2] Runner route-sha re-sync + marker-integrity gate — edit `policy_route_runner.py:35-38`  [BUILD]
Add the live route sha `7f5bc711…` to `ROUTE_SHA_ACCEPT` **only after** a marker-integrity grep confirms the 3 ⛔ANTI-REVERT markers are still present at `:4477/4493/4593` (text grep, not arithmetic — mirrors the demo-meta pin `:1758`). **The bless is gated on the grep** so a re-sync cannot launder a reverted marker into the accept-set. **DoD:** with the sha added + markers verified, `_assert_shas` returns (no STOP) on the live tree; a synthetic marker-removed tree FAILS the gate (grep-absent → do NOT bless).

### §3.3 [C3] Mechanical `--rs-go <token>` rollout guard — `policy_route_runner.py` `--policy` path + `dagger_loop.py`  [BUILD]
The `--policy` (policy-rollout) path and `dagger_loop.py` `SystemExit` unless `--rs-go <token>` is present (mirror `_opt_i_prime_check:356` fail-closed). **`policy is None` demo-replay is EXEMPT** (not a policy rollout, §3.4/H6). Spec states explicitly: **"rollout PROHIBITED" is a session convention, in no rule file** — this guard makes it airtight. **DoD:** `--policy` without `--rs-go` → SystemExit before any sim; demo-replay (no `--policy`) runs freely.

### §3.4 [runner] {0-3} truncation + state-dump — extend `_control_loop`  [BUILD via demo-replay / ROLLOUT-GATED for π]
- `--truncate-after-phase 3`: `break` `_control_loop` (`:672`) once `phase_idx>3` (`:675`). Reuse **`smoke`/`smoke_partial` semantics** so `_finalize_verdict` does NOT mark INVALID (MED). **Write the obs/phase/IK dump BEFORE `_finalize_verdict`** (`:621`).
- **frame-assert (not tautological, MED):** derive the **expected** truncation control-step from `schedule["phase_transitions"]` (the first step with `to_phase==4`) and assert `total == expected_steps*PHYS_PER_CTRL` — a real check, not `total==total`.
- **[%9 re-validate — MUST-HANDLE build-item, build-blocker] runner `:772` hardcoded settle assert:** `assert abs(grasp_yc − 0.150) < 0.010` (±10mm) sits on the `t==0` `_control_loop` path that the **π rollout also traverses** (NOT policy-gated) → for a DR offset with `|dy|>10mm` the settled `grasp_yc` deviates → the assert FIRES and crashes **before** the relabel dump (`ctx["grasp_yc"]:775`) = build-blocker. **FIX (same §3.4 runner touch):** make the assert **offset-aware** — expected settled center = nominal `0.150` + the rollout's offset `dy` (verify whether `ctx["grasp_y"]` is already offset-adjusted; if not, add the `--rollout-offset` `dy`); preserves the partition-corrupt safety intent. **Minimal fallback:** constrain the chosen offset to `|dy|≤8mm` (no assert edit). Recommended = offset-aware (enables any DR offset + correct for the full build).
- **Dump:** `obs_series` (already `:687`) + per-step `phase` (recoverable via one-hot argmax, `og:318`) + the §3.6 IK residual → `rollout_states.npz`. Default-off (`--truncate-after-phase` unset) = **byte-identical** untouched path.
- **[H6] Build-test via demo-replay** (`policy is None:691-693`, NOT a rollout → permitted at build): validate truncation + byte-identity + dump on a demo-replay run; the **π rollout** (`policy is not None`) stays `--rs-go`-gated. **DoD:** demo-replay `--truncate-after-phase 3` stops at LIFT, dump has one-hot only in {0-3}, default-off byte-identical, frame-assert passes on the derived-expected step.

### §3.5 [C1] Per-control-step relabel `T*(o,t)` — new `dagger_relabel.py`  [BUILD]
**The expert is OPEN-LOOP in {0-3}** (its target depends on the settle center + the schedule step, NOT on the live perturbed ee — that is *why* it is a valid restoring label). So for the rollout at schedule-step `t` (phase `p∈{0-3}`):
```
T*(o,t) = wp_demo[t]  +  (rollout_center − demo_center)          # per-STEP, settle-recentered
   where wp_demo[t]   = _abs_decode(demo_abs_labels[t], p, abs_affine)   # the demo's per-step target (the 392/97/48mm ramp)
         *_center     = (x_grasp, GRASP_YC) settle centre         # demo's from its dir; rollout's from ctx["grasp_yc"]:775 (+ x_grasp analog)
```
- **Per-step, NOT per-phase** (C1 supersedes the void constant-lookup). The rollout shares the demo's schedule clock (`:675`) → `wp_demo[t]` aligns step-for-step.
- **Settle re-center:** the rollout dumps its own settle center at `t=0` (`grasp_yc:775` for Y; **add the x_grasp analog** mirroring `test:3953` if the runner does not already expose it — small build-item). This makes `T*` faithful to THIS rollout's physics (C1 "reconstructed from THIS rollout's own settled centre"), not the demo's.
- **[INV#2] assert 88mm span/row:** for every relabeled row, assert `‖T*_R(t).Y − T*_L(t).Y‖ ≈ 88mm` (±tol) — the grasp span (arms ±44mm, `test:3942` "88 span"). A row violating it is a reconstruction bug → STOP.
- **DoD:** on the demo-replay dump, `T*(o,t)` round-trips to the demo's own per-step targets within float tol when rollout_center==demo_center; 88mm-span assert holds every row; a hand-injected wrong-center row trips the assert.

### §3.6 [H2/H3] In-scene IK feasibility filter + off-path coverage log — runner dump + `dagger_relabel.py`  [BUILD via demo-replay / π under token]
- **[H2] in-scene IK ground-truth:** during the rollout, at each {0-3} step compute one extra `solve_ik_dual(T*_p)` (the runner already computes `ik_cost` for the executed target `:721-722`) and **dump the `(s,T*_p)` IK residual**. The relabeler **drops** rows whose residual exceeds a feasibility threshold (ground-truth, NOT a post-hoc analytic screen — analytic is false-negative on the <1mm-fragile route, H2). A cheap analytic reach test may pre-filter only.
- **[H3] off-path coverage log:** record the **distribution** of `‖ee − on-path‖` for the KEPT (post-filter) states, not just counts. **Guard:** require off-path-but-feasible states to SURVIVE the filter before any plateau is attributed to representation (else the filter silently strips the restoring states DAgger needs → a false (iv)-tension→representation mislabel, H3). Emit `relabel_report.json` = `{kept, dropped, drop_reasons, offpath_dist_mm}`.
- **DoD:** relabeler drops rows above the IK-residual threshold with logged reasons; the kept-state `‖ee−on-path‖` histogram is emitted and shows surviving off-path mass.

### §3.7 [aggregate + retrain] under budget — new `dagger_aggregate.py` + reuse `bc_train_route.py`  [BUILD]
`D = D_base ∪ kept_relabel(S)` into a 15-phase `bc_dataset_abs.npz` with the **SAME meta** (`abs_affine`, `phase_names`, `obs_dim=27` — assert). **Fixed base composition** (anti-confound). Retrain: `bc_train_route.py --dataset D --val-dataset <FIXED sha-pinned holdout> --seed <PIN> --out-dir iter_1/` (~90s). **DoD:** `D_base + kept batch` trains to a ckpt; provenance sha-chain (base→D) recorded; `obs_dim==27` assert fires on a mismatched aggregate.

### §3.8 [C4/H4] §9 OG eval = clean {0,1} + off-path rows — reuse `og_offline_gate.py`  [BUILD, 0 GPU]
- **[C4] clean {0,1} ONLY:** `og_offline_gate.py --dataset-abs <FIXED sha-pinned {0,1} eval set> --policy iter_1/policy_abs.pt --full`. Read γ⊥ off **clean {0,1}** cells (co_seg OFF, `:97` p<2). **Do NOT** read `movable_all_go:453`/`null_beat:455` ({2,3} co_seg contamination). Goal renamed **"movable {0-3}" → "clean {0,1}"**. {2,3} are NOT γ⊥≤0.5-gated (co-moving → γ⊥≈1 correct; a co_seg-free {2,3} probe is a separate later code-add, NOT in the minimal).
- **[H4] off-path-row γ⊥:** ALSO run og on the policy's **visited off-path rows** (the rollout dump's `‖ee−on-path‖>thr` obs) — the budget question is off-path restoring; the on-manifold og is blind to it. Keep the fixed {0,1} eval as the anchor. **Strengthen rollout-SR-confirm into a HARD gate** before any GO (γ⊥≤0.5 offline = NECESSARY-non-conservative).
- **DoD:** OG on `(baseline BC-(ii), FIXED {0,1} set)` reproduces the CP-(ii)-5 {0}1.744/{1}1.056 baseline (metric-wiring regression); off-path-row og runs on the dump.

---

## §4. §9 read + decision (budget falsification — pre-registered before retrain)

**Metric:** clean-{0,1} γ⊥ (fixed eval anchor, C4) + off-path-row γ⊥ (H4). Baseline BC-(ii) {0}1.744/{1}1.056. **Bar reachable** (capacity {0,1}=0.031/0.003 in isolation).
- **Budget-NOT-fatal (→ scale to full):** clean-{0,1} γ⊥ AND off-path-row γ⊥ move toward ≤0.5 after the one aggregated retrain → real on-policy off-path data breaks the plateau under budget → justify full 8-proc m×k.
- **Budget-tension-confirmed (→ (i)-RL) — ONLY if off-path mass is MATERIAL:** γ⊥ plateaus at ~1 like (iv) Outcome-B **AND** the relabel's off-path fraction (H3 `relabel_report.json`) is material → **conservative-definite** (a real on-policy iteration WITH material off-path data under budget failing ⇒ the budget tension is real) → route to (i)-RL (Rs re-decide, P2-CRITICAL; NOT auto-abandon).
- **[%9 re-validate pin] INCONCLUSIVE (→ NOT (i)-RL):** γ⊥ plateaus BUT the off-path fraction is too small (the single minimal batch was **under-powered** relative to `D_base`, not budget-fatal) → **INCONCLUSIVE** → more iterations / larger batch, do NOT route to (i)-RL. §3.6 H3 MUST report the off-path fraction and this gate reads it — the minimal is ONE iteration vs (iv)'s ladder that proved the floor, so the under-power caveat is mandatory (do not over-claim conservative-definite from an under-powered single batch).
- **conservatism direction (§運用15):** offline OG is EASIER than closed-loop → γ⊥≤0.5 = NECESSARY-but-NON-CONSERVATIVE (needs the H4 hard rollout-SR-confirm before a GO); γ⊥ plateau = CONSERVATIVE-DEFINITE. Minimal single-offset = NECESSARY-but-non-conservative for the full multi-offset DAgger (a minimal PASS justifies the full build; a minimal plateau is conservative-definite).

---

## §5. Gate plan

| stage | gate | fires? |
|---|---|---|
| this v2 spec | 0-commit design | — → %12 review → **%9 re-validate** (§1-fix conformance, not a new 5体 debate) |
| build (§3.1-3.8: new scripts + runner touch) | **L3** → §運用15 層3 (`./isaaclab.sh -f` + tests) / 層5 (3+ file → 幾何/物理/SSOT) | ✅ pre-build |
| runner touch | §3.4 default-off = **byte-identical**; §3.2 sha-add gated on marker-grep; edits **no LOCKED marker** ({11} region) | ✅ verify |
| build-test (truncation/dump/relabel) | **demo-replay** (`policy is None`, H6 — permitted) | ✅ 0 rollout |
| **the 1 π rollout** | Rs「ロールアウト承認」 + `--rs-go` token (C3); single truncated {0-3} ≈**5-6min single-proc = NOT HIGH-COST-GATE** | ✅ the one gated step |
| `/reward-design` DESIGN-GATE | pure imitation, no reward/obs change | **SKIP** — but **ground-truth the {0,1} bar reachability** (capacity {0,1}=0.031/0.003) so SKIP does not hide an unreachable bar (CC5 MED) |
| OG eval | §4 checkpoint | ✅ 0 GPU |

---

## §6. INVARIANTS #1-5 (RS71 §0)
#1 dual-arm ✅ (both arms approach; policy = dual-arm fork-(iv)) / **#2 88mm span ✅ — actively ASSERTED per relabeled row (§3.5)** / #3 DiffIK ✅ (expert = abs target → `solve_ik_dual`) / #4 コ ✅ (untouched) / #5 no-kinematic-trick ✅ (rollout=physics; pin {6} excluded). LOCKED markers `:4477/4493/4593` ({11} region) verified present (§3.2) + untouched.

---

## §7. {11} framing (CC6 reconcile — corrected from v1)
**v1 said "{11} = obs-target mismatch = obs-fix = separate thread." This is a STALE premise** — the obs-switch test was **REFUTED same-day** (obs-mismatch is NOT the {11} cause; `project-bc-copycat-offpath-dagger-lever`). **Corrected framing: {11} shares the SAME BC-copycat root as {0-3}** (ON-PATH inert / off-path un-taught) and is **DEFERRED until {0-3} success**, NOT routed to a separate obs-fix. The minimal neither touches nor gates on {11}; {11} folds into the DAgger lever after {0-3} lands.

---

## §8. DEFER to full build (NOT in v2 — only if the minimal passes)
8-proc/2-GPU + device-parity (H5) / multi-iteration β-schedule + β-confound (CC4) / dead-band (0.5,0.7]+K_max + projected-iters-slope≥0⇒ABORT (CC4) / cudnn-determinism γ⊥ noise-floor (CC2). These are full-multi-iteration concerns; the minimal is ONE β=0 iteration.

---

## §9. Build order + DoD (for %11)
1. **§3.8 OG-eval wiring + {0,1} baseline regression** (0 GPU) — reproduce CP-(ii)-5 {0}1.744/{1}1.056.
2. **§3.1 H1 per-offset 15-phase conversion** — 27D dir, sha-pinned.
3. **§3.5 C1 relabel + §3.6 H2/H3 filter** (on the converted demo as a mock dump) — per-step `T*(o,t)`, 88mm assert, IK-residual drop, off-path histogram.
4. **§3.7 aggregate + retrain** (existing data) — `D_base+mock` → ckpt, obs_dim assert.
5. **§3.2 C2 sha re-sync + marker gate** + **§3.3 C3 `--rs-go` guard** + **§3.4 runner truncation/dump** — verified via **demo-replay** (H6, 0 rollout): byte-identity, frame-assert, `--policy` blocked without token.
6. **`dagger_loop.py` end-to-end on demo-replay** (0 π rollout) — one full pipeline `[3.4-replay]→[3.5]→[3.6]→[3.7]→[3.8]` producing an `og_gate.json` + a §4 verdict, **without a single π rollout**.

**Build-stage exit = step 6 green + 層3/層5 + %9 re-validate PASS.** THEN the 1 π rollout runs under Rs「ロールアウト承認」 + `--rs-go` token.

---

## §R. RECOMMENDATION (推奨 — decision = Rs)
Build the minimal per §3/§4 in the §9 order (all C1-C4/H1-H4/H6 folded), exit at a green demo-replay end-to-end + %9 re-validate, then run the ONE `--rs-go`-gated β=0 rollout to read the budget verdict on clean-{0,1} + off-path-row γ⊥. The capacity PASS makes the arch capable; this minimal tests whether REAL on-policy off-path data breaks the (iv) budget tension cheaply, before any full-build spend — γ⊥↓ under budget → scale to full 8-proc; plateau like (iv) → conservative-definite → (i)-RL.

**Conservatism (§運用15):** capacity/{0,1}-bar numbers = measured (cited); cost ≈5-6min = 推測 (only the 15-16min B1 rollout measured); the budget-fatal-or-not outcome is genuinely OPEN (that is the point of the test). 0-commit pending %12 review + %9 re-validate; NO rollout executed in this doc (π rollout = Rs approval + `--rs-go` token). {11} OUT; INVARIANTS untouched (INV#2 actively asserted).

*COORD2 %10 — 2026-07-04 00:43 JST*
