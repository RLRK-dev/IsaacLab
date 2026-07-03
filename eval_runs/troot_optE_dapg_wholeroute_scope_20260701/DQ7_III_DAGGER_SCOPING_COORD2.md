# DQ7 (iii) DAgger — off-path restoring scoping (movable {0-3} only)

**Author:** COORD2 (%10, scoping/audit). **Written:** 2026-07-03 18:04 JST (same-turn `date`).
**Charter:** %12 dispatch 2026-07-03 (Rs GO 17:34「推奨で進めて（並行で」) — Thread I = (iii) DAgger scoping [%10] ∥ Thread II = {11} obs-switch test [%11].
**Base doc refined+deepened:** `DQ7_OFFPATH_SCOPING_COORD2.md` §4.2-(iii) (my prior "defer (contingent)"; the contingency has now FIRED).
**Status:** SCOPING ONLY — 0-commit (%12 commits at review), no implementation / GPU / rollout / locked-file edits. **Design decision = Rs 専権**; §R is a labeled RECOMMENDATION.

---

## §0. Grounding (anchor set, §運用4 — cited from primary instruments; line numbers RE-VERIFIED live this session per the shifting-file hook)

| Anchor | Cite | Fact used |
|---|---|---|
| (ii) STOP verdict (一次) | `dq7_ii_cp3_batch/og/og_gate.json` via `DQ7_II_CP5_CROSSPV_PCT9.md:9-16` | movable γ⊥ {0}1.744/{1}1.056/{2}1.055/{3}1.034 all STOP; C2_REGRASP pair seg 0.249/ee_only 0.973 (n=2482) STOP; **null_beat 0.492=TRUE** (dr_worst 1.744−null_worst 2.236); og_bprime C2 contracted=**False** (5.0→…→3.905 divergent) |
| (ii) plateau + pivot | `DQ7_II_CP5_CROSSPV_PCT9.md:25-33,44-47` + `log.md:7486-7488` | {1} 1.257→1.098→1.056, per-rec marginal **19× collapse** (GO≤0.5 needs ~132 rec = 非現実); 3-BC-convergent (B2/iv/ii) = pure BC can't teach off-distribution restoring to bar = **IL compounding-error**; **STOP from ABSOLUTE bar, null_beat=mechanism-VALIDATED corroboration** |
| %9 sequencing + expert-dependency | `DQ7_II_CP5_CROSSPV_PCT9.md:46` | iii先行 correct (expert reuse, pre-contact movable target=fixed waypoint → waypoint-restoring **sufficient**); ⚠ iii's value depends on expert giving useful labels at visited off-path states; if iii ALSO plateaus → expert-independent (i) RL |
| ⚠ {11} separation (%9 CRITICAL) | `DQ7_II_CP5_CROSSPV_PCT9.md:33,47` + `log.md:7487` | {11} seg-follow = obs-target mismatch root-cause (obs-fix, NOT a BC/expert limit) → **do NOT lump {11} into DAgger**; {11} is Thread II (%11 obs-switch test) |
| my prior (iii) | `DQ7_OFFPATH_SCOPING_COORD2.md` §4.2-(iii) | deferred-contingent: correct asymptotics, needs rollouts (15-16min B1) + relabel machinery; revisit iff (ii) lands STOP↔GO |
| movable {0-3} = frozen waypoint (一次) | `test_newton_clip_routing.py:2806-2808` (z_grasp/approach/hover fixed offsets) + `DQ7_OFFPATH_SCOPING_COORD2.md` §3 Fact B (grasp-entry XY derived ONCE pre-hover) | the {0-3} scripted target = entry-derived-then-FROZEN abs waypoint → **perturbation-invariant expert** |
| LOCKED markers (一次, re-verified) | `test_newton_clip_routing.py:~4477/4493/4593` | all 3 Rs-LOCKED anti-revert markers (argmin R-target / square-on C2_TILT_SIGN=0 / regrasp_ok) live in the **{11} C2_REGRASP region** = OUTSIDE the {0-3} DAgger scope |
| INVARIANTS | `RS71-System-Spec-SSOT.md:23-27` | #1 dual-arm / #2 88mm span / #3 DiffIK-only / #4 コ LOCK / #5 no-kinematic-trick |

---

## §1. Trigger & the precise gap DAgger must close

**The pre-registered contingency fired.** My DQ7 staged plan reserved (iii) for the "restoring improved but off-GO (STOP↔GO intermediate)" state; CP-(ii)-5 landed exactly there: **mechanism-VALIDATED (null_beat 0.492 = the p2r policy genuinely beats the replicate-null; {1} moved 2.497→1.744 generalizing to {0}) BUT bar-UNMET (movable γ⊥ plateau ~1.05 ≫ GO≤0.5)**. Three pure-BC approaches (B2 DR-diversity / (iv) synthetic-p2r / (ii) physical-p2r) converged on the same ceiling — the textbook IL result: **BC cannot supply restoring at states outside the demonstrated distribution** (compounding error). DAgger is the canonical remedy: it trains at the states the POLICY itself visits.

**What DAgger must close (and ONLY this):**
- **Scope = movable {0-3} restoring** (GRASP_HOVER/DESCEND/CLOSE/LIFT): drive worst-demo γ⊥ from {0}1.744/{1}1.056/{2}1.055/{3}1.034 → **≤0.5**.
- **EXCLUDED = {11} C2_REGRASP** (seg-follow 0.249 + ee_only 0.973). Per %9 CRITICAL (`:33,47`): {11}'s failure is an **obs-target 44mm mismatch = obs-fix**, not a distribution/expert problem. Throwing DAgger/RL at an obs-bug is a category error. {11} is Thread II (%11). **This doc does not touch {11}.**
- The C2_REGRASP LOCKED markers (`:4477/4493/4593`) are in the excluded region → DAgger's {0-3} work is structurally clear of the Rs-LOCKED code (governance §8).

---

## §2. Prior-art gate record (mandatory, V10)

Run: `scripts/check_thread_vault_prior_art.sh --fail-on-blocker dagger on-policy expert-query rollout aggregation` → **28 hits / 0 genuine prior-failure blockers.** Distinct sources:

| Source | Nature | Disposition |
|---|---|---|
| `DQ7_II_CP5_CROSSPV_PCT9.md`, `T-ROOT-optE-route-dapg-C1C2/state.md` | **Self-referential** — the escalation packet that RECORDS this task's trigger (mentions "iii DAgger"/"rollout") | provenance, not a prior path |
| `T-ROOT-D1-LoRA-S1-Revision-2026-05-13/state.md:63` | a **mention** of an "S2 DAgger fallback path" in a LoRA-adapter design doc | ⚠ **NOT an executed DAgger attempt** — a fallback noted, never run; env6-VBD-era track (superseded lineage). No failure to inherit; the risk-monitor idea (adapter_contribution_ratio) is a generic RL-degeneracy guard, notable but not a DAgger precedent |
| `T-Skill-IC/CR/AR/state.md`, `_edit_requests/…IC-P4…`, `project-tree-manifest-archive` | coincidental `rollout`/`aggregation` keywords (sweep grids, AR architecture, archived planning) | unrelated |

**Finding: no THREAD project has ever EXECUTED a DAgger / on-policy-relabel loop** — this would be the first. → **CLEAR** (no blocker context of the FAIL/NO_GO/do-not-rerun kind; the only DAgger mention is an un-executed fallback in a superseded track). External prior-art (labeled general knowledge, not web-researched): DAgger (Ross et al. 2011) is the standard distribution-mismatch remedy for BC; its known cost driver is the expert-query + on-policy rollout loop, and its known failure mode is exactly **expert weakness at visited states** — which is why §9's falsification is pre-registered.

---

## §3. The scripted expert — design + the honest expert-dependency question

**Expert definition (queryable, cheap):** for a policy-visited state `s` at phase `p∈{0-3}`, the expert returns the scripted route's absolute EE target for `p` = the **entry-derived-then-frozen grasp waypoint** `T*_p` (hover/descend/close/lift toward the caveat-a-Y + fix-⑤-X grasp point; Z = fixed offsets `test:2806-2808`). The expert does NOT re-run the whole route — it returns the per-phase target the route WOULD command, a stored constant per episode. In the fork-(iv) **absolute-target** action space, the expert label IS `T*_p` directly (no delta conversion) → maximally clean relabeling.

**⭐ Why this expert is valid off-path at {0-3} (the good case):** because `T*_p` is **perturbation-invariant** — derived once at entry, frozen for the phase. From ANY off-path `s`, the expert says "target `T*_p`", i.e. "return to the demonstrated waypoint" = a correct restoring label. This is precisely %9's "pre-contact target=fixed waypoint → waypoint-restoring sufficient" (`:46`), and it is the mechanistic reason DAgger CAN work at {0-3} where it could not at a cable-tracking phase.

**⚠ The honest expert-dependency question (%9's core doubt, `:46`):** is a *perturbation-invariant waypoint label* enough to TEACH γ⊥≤0.5, or only enough to DEFINE it? The label is correct; whether the policy can LEARN to output a fixed target under perturbed obs is a separate (capacity/distribution) question — answered only empirically (§9 falsification). At {11}-type cable-aware phases the expert would additionally need to know where the cable actually is (obs-dependent) — that is the obs-fix thread, not DAgger, and is why {11} is excluded.

---

## §4. Why DAgger might succeed where (ii) failed — and why it might not (the crux)

Both (ii) and (iii) use the SAME frozen-waypoint expert and add off-path→waypoint restoring pairs. (ii) plateaued at ~1.05. The load-bearing question for spending rollout GPU: **what does DAgger change?**

**The optimistic mechanism (distribution):** (ii)'s off-path states were **designer-injected** (fixed magnitudes 2-10mm+tail-20mm at {0,1}). After BC on that set, the policy still errs into a DIFFERENT state distribution (its own compounding error) that the injected set did not cover. DAgger rolls out THAT policy, finds where it actually drifts, and relabels THERE — the no-regret guarantee matches training distribution to the policy's induced distribution. If the (ii) plateau was a **coverage** failure, DAgger breaks it.

**⚠ The pessimistic mechanism (representation) — surfaced honestly:** the B2/(ii) probes found **γ⊥ scale-invariant (2mm ≈ 10mm obs-following)** and the marginal collapse was **19×**. Both are yellow flags that γ⊥≈1 may be a **representation-level attractor** (the absolute-target policy has learned target≈f(obs) near-identity in the perturbed direction, at ALL tested scales), not merely an uncovered-region artifact. If so, DAgger — which only changes the *state distribution*, not the network's capacity to separate "follow obs" from "emit fixed target" — would **also plateau**. The (ii) result is genuinely **ambiguous** between coverage-limit (DAgger fixes) and representation-limit (DAgger does not); this ambiguity is the reason a pre-registered early-abort is mandatory (§9), and the reason the prior on DAgger here is **more guarded than (ii)'s was**.

**Net:** DAgger is the correct NEXT lever (it tries the one untried thing — on-policy distribution matching — reusing the (ii) expert + machinery at moderate cost), but it is a **bet with a known way to lose**, and the losing outcome is itself valuable (it discriminates coverage vs representation and routes to expert-independent (i) RL).

---

## §5. DAgger loop design (variants, budget, aggregation, convergence)

**Loop (per iteration k):** rollout current policy π_k on {0-3} → collect visited states `S_k` → expert relabel `{(s, T*_p) : s∈S_k}` → aggregate `D ← D ∪ relabel(S_k)` → retrain BC on `D` (fork-(iv) abs-target, seed-pinned) → OG γ⊥ eval on {0-3} (offline, §9) → decide continue/abort.

| knob | scoped value / options | rationale |
|---|---|---|
| **rollout truncation** ⭐ | run only phases {0-3} then STOP (grasp approach = the FIRST 4 phases) | {0-3} are episode-initial → a rollout can terminate after LIFT → **~1/3 of the 15-16min whole-route** ≈ 5-6 min/rollout. The single biggest cost lever; no need to run C1→C2 tail for a movable-restoring study |
| **rollouts / iter (m)** | 5-10 (start 5) | enough on-policy states to estimate γ⊥; matched to B1's 5-rollout precedent |
| **iterations (k)** | 3-5 with early-abort (§9) | DAgger typically converges in a few rounds if coverage-limited; the abort fires if not |
| **aggregation** | classic DAgger dataset-aggregation (D grows); β-mixing (π_exec = β·expert + (1−β)·π) with β↓ from 1 | β-mixing early keeps rollouts near-manifold (safe) then hands control to π; **NO SafeDAgger uncertainty-gating needed** — the expert is cheap (scripted), so query cost is not the bottleneck (rollout is) |
| **convergence / abort** | §9 pre-registered γ⊥ trajectory rule | contrasts the (ii) 19× marginal collapse |
| **cost estimate (推測)** | m·k rollouts × ~5-6 min ≈ **15-50 rollouts ≈ 1.5-5h GPU** + retrains (~90s each, negligible) + OG evals (0 GPU) | **UNDER the 10h HIGH-COST-GATE threshold** for one pass; but rollout-bearing → Rs GO required (§8) |

**Machinery needed (build, all rollout-free until the gated rollout leg):** (a) on-policy {0-3} rollout with per-step state dump (extend `policy_route_runner.py` — the committed-unused runner v2); (b) expert-relabel = emit `T*_p` per visited state (reuse the route's stored per-phase targets); (c) aggregate + retrain (reuse `bc_train_route.py`, seed-pin); (d) OG eval = the CP-(ii)-5 `og_offline_gate.py` on {0-3} (band=γ, already the applied instrument).

---

## §6. Scope discipline (restate — %9 CRITICAL)

**IN scope:** movable {0-3} restoring only. **OUT of scope, do NOT lump:** {11} C2_REGRASP seg-follow (0.249) + ee_only (0.973) = obs-target 44mm mismatch = **obs-fix** (Thread II, %11 obs-switch test running in parallel). Rationale (`:33,47`): the remedy differs — movable→distribution-matching (DAgger); {11}→obs integrity. Throwing DAgger/RL at an obs-bug wastes GPU and confounds the falsification. If DAgger's {0-3} rollouts happen to traverse phases 4-14 (untruncated), those phases are **recorded but NOT relabeled/gated** — only {0-3} enters `D` and the γ⊥ gate.

---

## §7. THREAD-conditions checklist

| condition | DAgger fit | note |
|---|---|---|
| **dual-arm (UR5e×2)** | ✅ preserved | {0-3} both arms approach the 88mm grasp; the policy is the existing dual-arm fork-(iv) — no single-arm reduction (INV#1) |
| **88mm span (INV#2)** | ✅ | {0-3} is the approach TO the grasp; span is set at CLOSE; expert targets preserve it |
| **DiffIK-only (INV#3)** | ✅ | expert labels = abs EE targets → DiffIK; no teleport |
| **Newton (not PhysX)** | ✅ | env7 mujoco-コ; rollouts on cuda:0 (canonical-route device-fragility — `project-canonical-route-device-fragile`) |
| **LOCKED (regrasp_ok / markers 4477/4493/4593 / test_newton)** | ✅ untouched | all in {11} region = excluded scope; DAgger reads {0-3}, adds no marker |
| **obs** | ✅ uses EXISTING obs (27D) | DAgger does NOT change obs — it changes the state DISTRIBUTION. ⚠ the {11} obs-mismatch is a SEPARATE thread; DAgger must not be conflated with it or used to paper over an obs gap |
| **no-kinematic-trick (INV#5)** | ✅ | rollout = physics; expert = target only; the pin (excluded {6}) unaffected |

---

## §8. Gate plan (which gate fires at each stage)

| stage | gate | fires? |
|---|---|---|
| this scoping | none (0-commit design) | — → %12 review → Rs decision |
| build DAgger machinery (runner dump / relabel / aggregate) | L3 (new script + `policy_route_runner.py`/recorder touch) → §運用2 5体 pre-debate + byte-identity for any locked-file touch + §運用15 層3/層5 | rollout-free build → **no** HIGH-COST-GATE |
| **rollout leg** (collect on-policy {0-3} states) | **HIGH-COST-GATE / `/production-launch-gate` + Rs explicit GO** | ✅ **YES** — rollout is currently PROHIBITED (`band=γ CP-(ii)-5` era rule); even at <10h, the rollout leg needs a fresh Rs GO. This is THE gated step |
| relabel + aggregate + retrain | none (0 GPU, BC ~90s) | — |
| **`/reward-design` DESIGN-GATE** | reward/env/success change? | **SKIP (recorded rationale):** DAgger is pure IMITATION on relabeled data — no reward, no success-condition, no obs change → design-gate not triggered. (If a future variant adds a reward term → gate fires.) |
| **OG gate** (offline γ⊥ on {0-3}) | the §9 falsification checkpoint | ✅ every retrain (0 GPU) |
| iterate k=2-5 | each rollout leg re-fires HIGH-COST-GATE, OR one batched Rs GO for K iterations with the §9 early-abort as the spend cap | ✅ |

---

## §9. Expert-dependency falsification (pre-registered — before any train, per %9)

**Metric:** OG movable-{0-3} worst-demo γ⊥ (the SAME CP-(ii)-5 instrument `og_offline_gate.py`, band=γ), computed offline after each DAgger retrain. Baseline = current BC-(ii) policy {0}1.744/{1}1.056/{2}1.055/{3}1.034.

**Pre-registered decision rule (mirrors the (ii) 19×-collapse logic):**
- **CONTINUE / GO-candidate:** worst-{0-3} γ⊥ decreases monotonically toward ≤0.5 AND per-iteration marginal Δγ⊥ does NOT collapse (>10× drop between iters) → coverage was the limit, DAgger is working.
- **ABORT → escalate to (i) expert-independent RL:** after K_min=3 iterations, worst-{0-3} γ⊥ still >0.7 AND marginal Δγ⊥/iter collapsing >10× (the (ii) signature) AND projected iters-to-0.5 >~10 (economically unreachable) → **the plateau is expert/representation-limited, not coverage-limited** → pure-imitation (BC-family) is exhausted → route to reward-driven (i). This is the strong, cheap discrimination %9 asked for.
- **conservatism direction (§運用15, mandatory):** OG offline is EASIER than closed-loop (small-perturbation local probe vs compounding drift — %9 §4). Therefore: an OG γ⊥ **reaching ≤0.5 = NECESSARY but NON-CONSERVATIVE** for closed-loop → a rollout SR / high-fidelity confirm is required BEFORE banking a GO (silent over-claim guard). An OG γ⊥ **plateau >0.5 = CONSERVATIVE-DEFINITE FAIL** (easy-test fail ⇒ hard reality fails) → bank the abort → (i). Same asymmetry that made the (ii) STOP bankable.
- ⚠ **anti-confound:** hold the null/base composition fixed across iterations (only relabeled on-policy states added) so the γ⊥ trajectory is a true marginal (the (ii) cross-PV flagged composition-confound; pre-register a fixed base here).

---

## §10. Reuse inventory (charter reuse-first)

| Asset | Path | Reuse |
|---|---|---|
| OG offline gate (band=γ, movable {0-3}) | `og_offline_gate.py` (`942ce85f1c`+) | the falsification metric — 2× validated, 0 GPU |
| Runner v2 (per-offset schedule, committed UNUSED) | `policy_route_runner.py` | the rollout + state-dump base (extend for on-policy {0-3} dump) |
| BC trainer + seed-pin + replicate-null | `bc_train_route.py` + `b2_cpD_report.md` | retrain per iteration (~90s); null-composition control |
| (ii) expert = the scripted route's per-phase targets | `test_newton_clip_routing.py` `_run_mujoco_grasp_route` {0-3} | the relabel oracle (frozen waypoints); NO new expert needed |
| CP-C validity filters / EGL / cuda:0 pin | (ii) flow + `reference-mujoco-headless-egl`, `project-canonical-route-device-fragile` | rollout validity + device |

---

## §R. RECOMMENDATION (推奨 — labeled; decision = Rs)

**Run ONE instrumented DAgger pass on movable {0-3}, rollout-truncated, with the §9 early-abort as the spend cap — but enter with a guarded prior and the falsification as the primary deliverable, not a GO.**

1. **Build rollout-free first** (runner {0-3} state-dump + expert-relabel + aggregate + retrain), L3-gated, 0 rollout — this is cheap and reversible.
2. **Rollout leg = the one Rs-GO'd expensive step** (~1.5-5h GPU, cuda:0, truncated {0-3}); pre-register §9 BEFORE the first train.
3. **The pass's PRIMARY output is the coverage-vs-representation discrimination** (§4/§9): γ⊥ moves → DAgger is the remedy, continue toward a rollout-SR-confirmed GO; γ⊥ plateaus with the (ii) 19× signature → conservative-definite evidence that pure imitation is exhausted → **escalate to expert-independent (i) DAPG-RL** (whose standing cost is the whole-route MDP env, P2's CRITICAL — a separate Rs scoping).
4. **{11} stays OUT** — parallel obs-fix thread (%11); DAgger neither touches nor is gated on it.

**Why guarded:** the scale-invariance + 19× collapse (§4) make the representation-limit hypothesis plausible, so this is a bet with a known loss path — but it is the CHEAPEST way to either (a) reach movable restoring or (b) earn the evidence that justifies the expensive (i) env build. It reuses the (ii) expert + machinery, adds only on-policy rollouts, and every spend increment is γ⊥-gated offline.

## §D. Rs decision points

- **D-1:** run the DAgger pass, or skip straight to (i) expert-independent RL? (recommend: run — it is cheaper and its abort earns (i)'s justification)
- **D-2:** rollout budget authorization — m=5 × k=3-5 truncated {0-3} rollouts (~1.5-5h cuda:0), as ONE batched Rs GO with the §9 abort as cap, or per-iteration GO?
- **D-3:** confirm §9 abort thresholds (γ⊥>0.7 + >10× marginal collapse after K_min=3 → (i))? or Rs-set different bar?
- **D-4:** β-mixing schedule (safe near-manifold start) vs classic DAgger (π-only rollouts from iter 1)?
- **D-5:** on a §9 ABORT, pre-authorize the (i) DAPG-RL scoping (env-build cost), or re-decide then?

---
**Conservatism note (§運用15):** cost/iteration figures = 推測 (mechanism-reasoned; only the 15-16min B1 rollout is measured). All (ii)/OG numbers = measured, cited to primary instruments (%9 §運用28 independent extraction). The coverage-vs-representation ambiguity is stated as genuinely OPEN — not resolved in either direction by this scoping. 0-commit pending %12 review; no rollout proposed to execute here (rollout remains PROHIBITED until Rs GO).

*COORD2 %10 — 2026-07-03 18:04 JST*
