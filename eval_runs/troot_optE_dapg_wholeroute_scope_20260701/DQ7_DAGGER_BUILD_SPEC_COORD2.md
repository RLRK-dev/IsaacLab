---
doc_class: reference
---

# DQ7 (iii) DAgger machinery — BUILD SPEC (movable {0-3}, rollout-free-first)

**Author:** COORD2 (%10, scoping/audit). **Written:** 2026-07-03 23:56 JST (same-turn `date`).
**Charter:** %12 dispatch 2026-07-03 23:4x — turn `DQ7_III_DAGGER_SCOPING_COORD2.md` §5/§R/§9 into a buildable spec. Capacity pre-test = **%12+%9 CONCUR PASS** (`DQ7_CAPACITY_VERDICT_PCT12.md`, node 23:33 `825b986390`) → fork-(iv) arch CAN represent restoring in isolation → the (ii)/(iv)/{11} γ⊥≈1 plateau was **data-correlation, NOT a representation limit** → **DAgger justified**. Rs 2026-07-03 23:3x「推奨で良い」= DAgger §D **D-1..D-5 all approved** + 「GPU 最大活用」= **8-proc/2-GPU** rollout parallelism.
**Status:** BUILD SPEC — **0-commit** (%12 commits at review), **rollout PROHIBITED** in this doc and in the build stage (the rollout leg is a separate HIGH-COST-GATE + fresh Rs GO). **Design decision = Rs 専権**; §R is a labeled RECOMMENDATION, judgment calls are OPTIONS+推奨 (§10). No implementation performed here.
**Consumers:** %12 review → 5体 pre-debate (%12 lead) → %11 build (rollout-free first).

---

## §0. Grounding (anchor set, §運用4 — primary instruments, line numbers RE-VERIFIED live this session)

| Anchor | Cite | Fact used |
|---|---|---|
| capacity PASS (routes to DAgger) | `DQ7_CAPACITY_VERDICT_PCT12.md:29-46` + node `state.md:45` (⟦23:33⟧) | val 5.56e-05 ≪ Var(δ) 0.0842 (**1515×**) AND γ⊥{0,1}=0.031/0.003 ≤0.5 (co_seg OFF, clean primary) → **PASS = arch CAN represent restoring** → plateau was **data-correlation** → DAgger justified. **PASS = NECESSARY-but-NON-CONSERVATIVE** (isolated set EASIER than on-policy) |
| (ii) STOP baseline (§9 baseline) | `DQ7_II_CP5_CROSSPV_PCT9.md:13-15` | movable γ⊥ {0}1.744/{1}1.056/{2}1.055/{3}1.034 all STOP; plateau {1} 1.257→1.098→1.056, per-rec marginal **19× collapse** |
| my scoping (this spec operationalizes) | `DQ7_III_DAGGER_SCOPING_COORD2.md` §5/§9/§R/§D | loop design, falsification, recommendation, the 5 Rs-approved decision points |
| %9 build-items | `DQ7_III_DAGGER_CROSSPV_PCT9.md:38,40,29` | Pitfall A **feasibility-filter** (drop IK-infeasible visited states); **{2,3} coverage positive** (DAgger visits CLOSE/LIFT that (ii) skipped); §9 robust-fit extrapolation (all-K, not 2-point) |
| runner (extend) | `policy_route_runner.py` `_control_loop:652-778` (`obs_series.append:687`, `phase_idx:675`, `_policy_action:192/689-690`, abs-decode `:695-697`, frame-assert `:618-619`, Opt-i' guard `:91/:340-356`) | closed-loop policy rollout ALREADY exists; obs dump ALREADY persisted; phase recoverable from obs one-hot |
| trainer (reuse) | `bc_train_route.py:36-49` (`--dataset/--val-dataset/--seed/--out-dir`), reuse `bc_pretrain` `:56` | retrain per iter, seed-PINNED (`:46,59-63`), ~90s, RSL-RL ckpt + sidecar |
| OG gate (reuse = §9 metric) | `og_offline_gate.py` `DR_MOVABLE:33`, `GPERP_GO=0.5:36`, `og_b:80-140` (co_seg `:97`), gate `movable_all_go:453` / `null_beat:455` / phase from obs one-hot `:318` | movable {0-3} γ⊥ (band=γ), 0 GPU — the CP-(ii)-5 applied instrument, UNCHANGED |
| {0-3} frozen-target (expert validity) | production `_run_mujoco_grasp_route` `test_newton_clip_routing.py:3503+` — `z_grasp=1.0668:3635`, `z_high:3636`/`z_lift:3638`, descend interp `:3974`, `GRASP_X:3564`, caveat-a Y `:3857`, fix-⑤ X `:3870`; %9 independent confirm no per-frame cable-argmin in `test:3888-3932` | {0-3} target = entry-derived-then-FROZEN abs waypoint → **perturbation-invariant expert = trivial constant lookup** (⚠ NOT the stale `:2806-2808` infra-smoke — corrected per `reference-test-newton-legacy-vs-production-route-namesake-functions`) |
| LOCKED markers (out of scope) | `test_newton_clip_routing.py:~4477/4493/4593` | all 3 Rs-LOCKED anti-revert markers live in the **{11} C2_REGRASP** region = OUTSIDE {0-3} → runner touches no marker |
| INVARIANTS | `RS71-System-Spec-SSOT.md §0:23-27` | #1 dual-arm / #2 88mm span / #3 DiffIK-only / #4 コ LOCK / #5 no-kinematic-trick |

**Reuse-first finding:** the DAgger loop reuses 3 existing scripts (`policy_route_runner.py` closed-loop path, `bc_train_route.py`, `og_offline_gate.py`) + adds only 2 thin new scripts (`dagger_relabel.py`, `dagger_aggregate.py`) + 1 orchestrator (`dagger_loop.py`). No new expert, no new obs, no new reward, no new gate instrument.

---

## §1. What this spec builds (and the hard boundary it must NOT cross)

**Goal (movable {0-3} ONLY):** drive worst-demo movable-{0-3} γ⊥ from {0}1.744/{1}1.056/{2}1.055/{3}1.034 → **≤0.5** by on-policy DAgger (train at the states the policy itself visits, decorrelating own-ee from target — the lever the capacity pre-test proves the arch can exploit).

**⛔ The rollout-free / gated-rollout boundary (§8 charter core; the spine of this spec):**
- **BUILD STAGE (this spec, L3, 0 GPU rollout):** implement + **unit-test all machinery** (runner dump path, relabel, feasibility-filter, aggregate, OG-eval wiring, β-mix, 8-proc harness) on **existing data / a mock dump / a single minimal dry rollout**. NO full `m×k` on-policy collection.
- **ROLLOUT LEG (separate, HIGH-COST-GATE + fresh Rs GO):** the actual `m×k` on-policy `{0-3}` collection. **PROHIBITED until Rs GO.** The 8-proc/2-GPU plan is *presented at that gate* as a wall-clock input, not executed here.
- Every component below is tagged **[BUILD]** (implement+unit-test now, rollout-free) or **[ROLLOUT-GATED]** (wired now, exercised only after Rs GO).

**{11} is OUT (%9 CRITICAL, `DQ7_III_DAGGER_CROSSPV_PCT9.md:28`):** C2_REGRASP seg-follow (0.249) + ee_only (0.973) = obs-target 44 mm mismatch = **obs-fix** (Thread II, %11 obs-switch test in parallel), NOT a distribution/expert problem. This spec neither touches nor gates on {11}. If a `{0-3}` rollout traverses phases 4-14, those steps are **recorded but NOT relabeled and NOT gated** (§3.1 truncation makes this the default; §8).

---

## §2. Architecture — the DAgger loop (per iteration k)

```
              ┌─────────────────────── iteration k ───────────────────────┐
 π_{k}  ──►  [3.1] runner rollout {0-3}, β-mix(β_k), dump obs_series.npy  (ROLLOUT-GATED)
              │        × m rollouts  (8-proc/2-GPU, §3.6)                   │
              ▼                                                             │
        visited states S_k (obs[N,27], phase = argmax one-hot)             │
              │                                                            │
 [3.2] relabel: label(s)=T*_p (frozen per-phase abs target)  + feasibility-filter (drop IK-infeasible T*_p)  (BUILD)
              ▼                                                             │
 [3.3] aggregate D ← D_base ∪ Σ_{j≤k} relabel(S_j)   (fixed base, anti-confound)  (BUILD)
              ▼                                                             │
 [3.3] retrain: bc_train_route.py --dataset D --seed <pin>  → π_{k+1}  (~90s, BUILD)
              ▼                                                             │
 [3.4] OG eval: og_offline_gate.py --policy π_{k+1} --dataset-abs <FIXED eval set>  → γ⊥ movable {0-3}  (0 GPU, BUILD)
              ▼                                                             │
 [3.5/§5] §9 decision: CONTINUE (γ⊥↓ toward ≤0.5) / GO-candidate (≤0.5, needs rollout-SR confirm) / ABORT→(i)
              └────────────────────────────────────────────────────────────┘
```

The **only** GPU-rollout-bearing box is `[3.1]`. Everything downstream (`[3.2]`–`[3.4]`) is 0-GPU and is the entire BUILD-stage deliverable's testable surface.

---

## §3. Component specs (buildable)

### §3.1 Runner {0-3} on-policy state-dump  — extend `policy_route_runner.py`  [BUILD wiring / ROLLOUT-GATED exercise]

**Reuse (already present):** the closed-loop policy path (`--policy --policy-absolute`, `_policy_action:192` = deterministic actor-mean `:200-204`), per-step `obs_series.append(obs_vec)` (`:687`), abs-decode `tgt6 = abs_decode(a, phase, abs_affine)` (`:695-697`), and the persisted `obs_series.npy` (consumed today by `og_c` via `b0a_full/obs_series.npy`). Phase per step is recoverable downstream from the obs one-hot (`argmax(obs[:,12:12+n_phases])`, identical to `og_offline_gate.py:318`) → **no separate phase dump needed.**

**Changes (thin, all additive / default-off = byte-identical when unused):**
1. **`--truncate-after-phase P` (default `None`):** in `_control_loop` (`:672` loop), after computing `phase_idx` (`:675`), **`break` once `phase_idx > P`** (P=3 → stop after LIFT; collects only {0-3} = grasp-approach ≈ the first ~1/3 of the whole route).
   - ⚠ **build-item (frame-count assert):** truncation makes `total < n_ctrl * PHYS_PER_CTRL`, tripping the assert `:618-619`. Change: when `--truncate-after-phase` is set, **skip / re-scope that assert** to `total == (#control-steps executed) * PHYS_PER_CTRL` (record the truncation-step count in the verdict). Do NOT weaken the assert on the untruncated path (default-off preserves it).
2. **`--dagger-dump <path>` (default `None`):** on rollout end, write `obs_series` (already accumulated) + the executed β-mix flag + `rollout_offset` to `<path>/rollout_states.npz` (`obs[N,27]`, `beta` scalar, `offset` [dx,dy]). (obs_series.npy is already written; this just names it per-rollout for the aggregator and stamps provenance.)
3. **β-mixing hook `--beta B` (default `1.0`=pure-π; see §3.5).**
   - **Opt-i' guard preserved:** each rollout keeps its own-offset schedule (`_opt_i_prime_check:91`, `--rollout-offset:352`); DAgger rollouts pass the DR-set offset → guard stays live (a wrong-offset schedule still `SystemExit`s before GPU).

**DoD [BUILD]:** (a) `--truncate-after-phase 3` on a **single minimal dry rollout** (1 rollout, existing seed/offset) stops at LIFT, writes `rollout_states.npz` with `obs[:,12:16]` one-hot only in cols {0-3}; (b) default-off run is **byte-identical** to the current runner output (diff `og_gate`-relevant artifacts); (c) frame-assert re-scope verified on both paths.

### §3.2 Expert-relabel  — new `dagger_relabel.py`  [BUILD]

**Expert (trivial, perturbation-invariant):** for a visited state `s` at phase `p∈{0-3}`, `label(s) = T*_p` = the **frozen per-phase abs EE target** the scripted route commands at `p`. In the fork-(iv) **absolute-target** action space the label IS `T*_p` (6D) directly — no delta conversion. `T*_p` is **entry-derived-then-frozen** (production `_run_mujoco_grasp_route`, §0) → the SAME constant for every visited `s` at phase `p` in a given offset's episode → the relabel is a **constant per-phase lookup**, NOT a route re-run.

**Source of `T*_p` (reuse, no new derivation):** the base demo's abs labels for phase `p` at the rollout's offset. Concretely: read the base `bc_dataset_abs.npz` (`actions[N,6]` = abs labels, `meta.abs_affine`), select the rows with `phase==p`, and (since {0-3} labels are frozen per phase per offset) take the phase-`p` label constant. `dagger_relabel.py` maps each dumped `rollout_states.npz` row `(obs, p)` → `(obs, T*_p)`.

**Feasibility-filter (%9 Pitfall A, `DQ7_III_DAGGER_CROSSPV_PCT9.md:38`) — mandatory build-item:** a γ⊥≈1 policy drifts off-path; on the reach-fragile canonical route (`project-canonical-route-device-fragile`: cpu 83 mm ↔ cuda 0.9 mm) it may reach states from which `T*_p` is **IK-infeasible / joint-limit / reach-wall** → an un-followable label **poisons D**. **Drop** any visited `s` whose `(s, T*_p)` fails a reach/IK screen. Reuse the **CP-C validity** + **fix-⑤ reach-screen** (the existing offset-reachability screen) — NOT a full IK solve in the relabeler; a cheap analytic reach/limit test (B1′ lesson: unreachable-target ≠ IK-fail — screen reachability, not solver convergence). Emit `relabel_report.json`: `{kept, dropped, drop_reasons}` per phase.

**DoD [BUILD]:** on a **mock/synthetic dump** (hand-built obs rows at {0-3} incl. deliberately unreachable ones), relabel emits `T*_p` for reachable rows and drops the unreachable ones with logged reasons; kept labels round-trip through `_abs_decode` to the demo `T*_p` within float tol.

### §3.3 Aggregate + retrain  — new `dagger_aggregate.py` + reuse `bc_train_route.py`  [BUILD]

**Aggregate (classic DAgger, anti-confound):** `D_k = D_base ∪ Σ_{j≤k} relabel(S_j)`. `dagger_aggregate.py` concatenates the **fixed base demo dataset** + all kept relabeled on-policy rows into a new `bc_dataset_abs.npz` with the **SAME `meta`** (`abs_affine`, `phase_names`, `obs_dim=27`).
- ⚠ **anti-confound (%9 §9, `DQ7_III_DAGGER_CROSSPV_PCT9.md:31`):** the **base composition is FROZEN** across iterations — only relabeled on-policy states are ADDED. This makes the γ⊥ trajectory a **true marginal** (policy change), not an eval/base-set change (the CP-(ii)-5 composition-confound this pre-registers against).

**Retrain (reuse `bc_train_route.py`, unmodified):** `bc_train_route.py --dataset D_k.npz --val-dataset <FIXED whole-demo holdout> --seed <PINNED> --out-dir iter_k/` → `policy_abs.pt` + sidecar (~90s, `:78`). Seed-pin (`:46,59-63`) = reproducible init per iter. `whole_demo_val_loss` (`:88-95`) tracked per iter as a secondary health signal.

**DoD [BUILD]:** aggregate of `D_base + one mock relabel batch` loads in `bc_train_route.py` and trains to a ckpt (existing data, 0 rollout); sidecar records the exact `dataset_sha256` chain (base→D_1→D_2…) so aggregation provenance is auditable.

### §3.4 OG eval per retrain  — reuse `og_offline_gate.py` (UNCHANGED)  [BUILD]

**Reuse (the §9 metric, band=γ, 0 GPU):** `og_offline_gate.py --dataset-abs <FIXED EVAL SET> --policy iter_k/policy_abs.pt --full --null-og <FIXED null> --out-dir iter_k/og/`. Reads movable-{0-3} γ⊥ from `ogb_anchor_gate` (`DR_MOVABLE:33`, `GPERP_GO=0.5:36`, gate `:414-421`), `movable_all_go` (`:453`), `null_beat` (`:455`).
- ⚠ **build-item (FIXED eval-obs set, not the growing D):** `--dataset-abs` MUST point at a **frozen reference obs set** held constant across all K iterations (the CP-(ii)-5 eval set / a fixed {0-3} perturbation set), so the per-iteration γ⊥ reflects ONLY the policy's Jacobian change (`og_b` measures `d(tgt)/d(ee)` at the dataset's obs rows, `:99-117`). Pointing it at the growing aggregated D would confound the γ⊥ trajectory with the eval distribution. **This is the operative anti-confound for the §9 comparison** (complements §3.3's fixed-base training anti-confound).
- **{2,3} co_seg note:** `og_offline_gate.py:97` co-moves seg for `p≥2` (post-grasp coupling), which reads as γ⊥≈1.4 for a correct seg-tracker (`reference-og-gate-moving-target-gamma-perp-wrong-sign`). For DAgger's movable-{0-3} **restoring** question, the load-bearing cells are the **clean {0,1}** (co_seg OFF); {2,3} corroborate via the co_seg-FREE path (as the capacity verdict §3 established). §5 reads the falsification off {0,1} primary + {2,3} co_seg-free, NOT the raw co_seg γ⊥.

**DoD [BUILD]:** OG eval on `(baseline BC-(ii) policy, FIXED eval set)` reproduces the CP-(ii)-5 baseline γ⊥ {0}1.744/{1}1.056 (regression anchor) → confirms the metric is wired identically before any DAgger iter.

### §3.5 β-mixing + feasibility-filter (D-4, Rs-approved)  [BUILD wiring / ROLLOUT-GATED exercise]

**β-mixing (D-4 = β-mixing + feasibility-filter, Rs-approved `DQ7_CAPACITY_VERDICT_PCT12.md:50`):** executed target = `tgt_exec = β_k·T*_p + (1−β_k)·decode(a_π)` at the §3.1 abs-decode point (`:695-697`), with **β↓ from 1** (iter-0 near-manifold safe start → hands control to π). Target-space mix (not action-space) because the per-phase affine is linear → equivalent up to the clamp, and `T*_p` is already the abs target. Schedule (推奨, §10): `β = [1.0(warm dry), 0.7, 0.4, 0.0…]` — Rs-tunable.
- **Rationale (%9 `:38`):** β-mix early keeps rollouts near-manifold (safe on the reach-fragile route) but is NOT itself a feasibility filter — the **§3.2 feasibility-filter is the actual poison guard**; β-mix is the safe-exploration schedule. Both are required (D-4).
- **No SafeDAgger uncertainty-gating** — the expert is a cheap scripted constant; query cost is not the bottleneck (rollout is).

**DoD [BUILD]:** β=1.0 reproduces pure-expert targets (= the demo), β=0.0 reproduces pure-π (= §3.1 default), a mid-β dry step blends them at the decode point — all verifiable on a **single dry step**, 0 rollout.

### §3.6 8-proc/2-GPU rollout parallelism (Rs「GPU 最大活用」)  — new `dagger_loop.py` orchestrator  [BUILD harness / ROLLOUT-GATED exercise]

**Design (Rs directive `DQ7_CAPACITY_VERDICT_PCT12.md:50`, node `:45`):** distribute the `m` per-iteration rollouts across **2 GPU × ≤4 proc = 8 proc** (respecting the CLAUDE.md GPU per-process cap: A6000 48 GB / PRO4000 24 GB, ≤4 proc each). Each proc runs one truncated-{0-3} rollout (`§3.1`, `CUDA_VISIBLE_DEVICES` pinned, EGL headless per `reference-mujoco-headless-egl-video-x11-badwindow` = `MUJOCO_GL=egl` + unset `DISPLAY`). `dagger_loop.py` fans out rollouts, barrier-joins, then runs the 0-GPU `[3.2]`–`[3.4]` serially. Expected wall-clock **~5-8× lower** than serial (GPU-hours ≈ same).

**⚠ build-item (both-GPU route-physics parity — MANDATORY before any parallel rollout):** the canonical route is **device-fragile** (`project-canonical-route-device-fragile`: cpu 83.2 mm BLOCK ↔ cuda:0 0.9 mm SUCCESS at the re-grasp reach-wall) — and **A6000 vs PRO4000 parity is UNVERIFIED**. **Pre-rollout gate:** run the SAME truncated-{0-3} canonical route on **both** GPUs and assert `{0-3}` physics agree (EE/seg trajectories within a tight tol). **If parity breaks → FALLBACK to single-GPU × ≤4 proc** (still 4× parallel; log the drop loudly, do NOT silently run cross-device). This parity check is itself a small rollout → it lives at the **ROLLOUT-GATED** boundary (runs at the rollout leg's start under the Rs GO, as the first action before the m×k spend), but the harness + assertion logic is **[BUILD]** (coded + unit-tested on a mock now).

**DoD [BUILD]:** `dagger_loop.py` fans out `m` **mock** rollout-commands across 8 slots (no real sim), collects their dump paths, and drives `[3.2]`–`[3.4]`; the parity-assert function is unit-tested on two synthetic trajectories (one agreeing, one diverging → asserts/falls back correctly).

---

## §4. The rollout-free / gated-rollout boundary (explicit — §8 charter core)

| Machinery | Stage | Rollout? | Tested at BUILD by |
|---|---|---|---|
| §3.1 runner truncation + dump + β hook | BUILD wiring | 1 minimal **dry** rollout only | single dry rollout + default-off byte-identity |
| §3.2 relabel + feasibility-filter | BUILD | none | mock/synthetic dump |
| §3.3 aggregate + retrain | BUILD | none | `D_base + mock batch` → ckpt |
| §3.4 OG eval | BUILD | none | baseline-policy γ⊥ regression |
| §3.5 β-mix | BUILD wiring | 1 dry step | β∈{0,mid,1} dry-step blend |
| §3.6 8-proc harness + parity-assert | BUILD harness | mock fan-out | mock rollouts + synthetic parity |
| **full `m×k` on-policy collection** | **ROLLOUT LEG** | **yes — PROHIBITED until Rs GO** | — (HIGH-COST-GATE) |
| both-GPU parity check (real) | ROLLOUT LEG (first action) | small real rollout | runs under the same Rs GO |

**The build stage produces a fully unit-tested loop with a single "insert real rollouts here" seam.** The rollout leg is one `/production-launch-gate` + Rs GO away, and its cost input (8-proc wall-clock) is prepared but not spent.

---

## §5. §9 falsification — pre-registered (BEFORE any train; Rs-approved D-3)

**Metric:** OG movable-{0-3} worst-demo γ⊥ (`og_offline_gate.py`, band=γ, FIXED eval set §3.4), read off **clean {0,1} primary** + {2,3} co_seg-free. Baseline = BC-(ii) {0}1.744/{1}1.056/{2}1.055/{3}1.034.

**Decision rule (Rs-approved D-3 = K_min=3, γ⊥>0.7 ∧ 10×-collapse → (i)):**
- **CONTINUE / GO-candidate:** worst-{0-3} γ⊥ decreases toward ≤0.5 AND per-iter marginal Δγ⊥ does NOT collapse >10× → coverage was the limit, DAgger working. **Reaching ≤0.5 = GO-CANDIDATE only** (needs a rollout-SR / high-fidelity confirm before banking — conservatism below).
- **ABORT → (i) expert-independent RL:** after **K_min=3** iters, worst-{0-3} γ⊥ still **>0.7** AND marginal Δγ⊥/iter collapsing **>10×** AND **projected iters-to-0.5 >~10** (economically unreachable) → plateau is representation/expert-limited → pure-imitation exhausted → route to (i).
  - ⚠ **projected-iters via robust fit over ALL K** (%9 `:29`), NOT a 2-point linear extrapolation (noisy-γ⊥ mis-extrapolation guard).
- **conservatism direction (§運用15, mandatory):** OG offline is EASIER than closed-loop (local small-perturbation probe vs compounding drift). ∴ γ⊥ **≤0.5 = NECESSARY but NON-CONSERVATIVE** → a rollout-SR/high-fidelity confirm is required before a GO is banked (silent over-claim guard); γ⊥ **plateau >0.5 = CONSERVATIVE-DEFINITE FAIL** → bank the abort → (i). (Same asymmetry that made the (ii) STOP bankable.)
- ⚠ **anti-confound:** fixed base composition (§3.3) + fixed eval-obs set (§3.4) → the γ⊥ trajectory is a true policy marginal.

**Prior shift from the capacity PASS (record):** capacity PASS refuted the representation-attractor branch of scoping-§4 → the expected outcome is now **CONTINUE** (plateau was data-correlation, which on-policy relabel decorrelates). §9 ABORT still guards against the OTHER loss paths (reach-infeasibility poison despite the filter, on-policy compounding not reaching ≤0.5). The pass's PRIMARY deliverable remains the **coverage-confirm vs abort discrimination**, now with a PASS-informed prior toward success.

---

## §6. L3 gate plan + byte-identity + DESIGN-GATE

| stage | gate | fires? |
|---|---|---|
| this build spec | none (0-commit design) | — → %12 review → 5体 pre-debate |
| build machinery (§3.1-3.6, new scripts + `policy_route_runner.py` touch) | **L3** (new scripts + runner touch, scoping §8) → §運用2 **5体 pre-debate** (%12 lead) + §運用15 層3 (`./isaaclab.sh -f` + module tests) / 層5 (3+ file → 幾何/物理/SSOT 3-view) | ✅ pre-build |
| runner touch byte-identity | all §3.1 changes **default-off** → untouched path **byte-identical**; runner edits **no LOCKED marker** (all in {11} region, §0) | ✅ verify |
| `/reward-design` DESIGN-GATE | reward/env/success change? | **SKIP (recorded):** pure IMITATION on relabeled data — no reward, no success-condition, **no obs change** (obs 27D unchanged; DAgger changes the state DISTRIBUTION only). If a future variant adds a reward term → gate fires. |
| **rollout leg** | **HIGH-COST-GATE / `/production-launch-gate` + fresh Rs GO** | ✅ **the gated step** — rollout PROHIBITED until then; 8-proc plan presented as cost input |
| OG gate (per retrain) | the §5 checkpoint | ✅ every retrain (0 GPU) |

---

## §7. INVARIANTS #1-5 preservation checklist (RS71 §0)

| INV | status | note |
|---|---|---|
| #1 DUAL-ARM | ✅ | {0-3} = both arms approach the 88 mm grasp; policy = existing dual-arm fork-(iv); no single-arm reduction |
| #2 88 mm span / fixed bases | ✅ | {0-3} is the approach TO the grasp; span set at CLOSE; expert `T*_p` preserves it |
| #3 DiffIK-only | ✅ | expert labels = abs EE targets → DiffIK; no teleport; runner uses `solve_ik_dual` (`:721`) |
| #4 コ LOCKED | ✅ | no geometry touched |
| #5 no-kinematic-trick | ✅ | rollout = physics; expert = target only; the pin ({6}, excluded) unaffected |
| obs integrity | ✅ | obs 27D UNCHANGED; DAgger ≠ the {11} obs-fix (do not conflate) |
| LOCKED markers | ✅ | `:4477/4493/4593` in {11} region = out of scope; runner adds/edits no marker |

---

## §8. Scope discipline (restate — %9 CRITICAL)

**IN:** movable {0-3} restoring only. **OUT (do NOT lump):** {11} C2_REGRASP (obs-fix, Thread II / %11). Truncation (§3.1) makes {4-14} un-relabeled/un-gated by default. First pass = {0-3} clean; {11} folds only after {0-3} success OR Rs decision (§R of scoping). This spec adds no {11} work and gates on no {11} metric.

---

## §9. Build order + DoD (for %11)

1. **§3.4 OG-eval wiring + baseline regression** (0 GPU, cheapest, anchors the metric) — DoD: reproduce CP-(ii)-5 baseline γ⊥.
2. **§3.2 relabel + feasibility-filter** (mock dump) — DoD: `T*_p` emit + unreachable drop.
3. **§3.3 aggregate + retrain** (existing data) — DoD: `D_base+mock` → ckpt, provenance chain.
4. **§3.1 runner truncation + dump + β hook** (1 dry rollout) — DoD: {0-3} stop + byte-identity default-off + frame-assert re-scope.
5. **§3.5 β-mix dry-step** + **§3.6 8-proc harness + parity-assert** (mock) — DoD: β blend + mock fan-out + synthetic parity/fallback.
6. **`dagger_loop.py` end-to-end on the mock path** (0 real rollout) — DoD: one full iteration runs `[3.1-dry]→[3.2]→[3.3]→[3.4]→[3.5 decision]` producing an `og_gate.json` + a §5 verdict, **without a single real rollout**.

**Build-stage exit = step 6 green + §運用15 層3/層5 + 5体 pre-debate PASS.** Then STOP → the rollout leg awaits a separate HIGH-COST-GATE + fresh Rs GO.

---

## §10. Judgment calls (OPTIONS + 推奨 — decision = Rs / %12)

- **JC-1 rollout-free boundary depth (§4):** (a) **mock-only build** (no real dry rollout at build) / (b) **build + 1 real minimal dry rollout** to exercise the runner dump path end-to-end. **推奨 (b)** — one short real dry rollout de-risks the dump/truncation wiring cheaply (single rollout ≪ the gated m×k); still 0 collection. (Rs may prefer (a) if even 1 rollout must wait for the GO.)
- **JC-2 8-proc device parity (§3.6):** (a) **fail-closed** (parity break → single-GPU×4, log loud) / (b) attempt per-GPU calibration. **推奨 (a)** — calibrating across A6000/PRO4000 = a SIM2REAL-trap-adjacent rabbit hole; 4× parallel single-GPU is ample for m=5. Never silently cross-device.
- **JC-3 feasibility-filter depth (§3.2):** (a) **cheap analytic reach/limit screen** (reuse fix-⑤ reach-screen + CP-C validity) / (b) full IK-solve per visited state. **推奨 (a)** — B1′ lesson (unreachable ≠ IK-fail); a full solve per state is costly and conflates reach with solver convergence. (b) only if (a) proves too permissive.
- **JC-4 β schedule (§3.5):** `[1.0(dry), 0.7, 0.4, 0.0]` vs classic DAgger (β=0 from iter-1). **推奨 the decaying schedule** (Rs D-4 approved β-mixing) — near-manifold safe start on the reach-fragile route.
- **JC-5 §9 eval-set (§3.4):** the CP-(ii)-5 eval set vs a fresh fixed {0-3} perturbation set. **推奨 the CP-(ii)-5 set** — direct baseline comparability (the baseline γ⊥ is already measured on it).

---

## §R. RECOMMENDATION (推奨 — labeled; decision = Rs / %12)

**Build the full DAgger loop rollout-free-first per §3/§9 in the §9 order, exit at a green mock end-to-end + 5体 pre-debate, then STOP at the rollout-leg boundary.** The capacity PASS shifts the prior toward success (plateau = decorrelatable data-correlation), so the loop is worth building now; but the actual on-policy spend stays behind the HIGH-COST-GATE + fresh Rs GO, and the §9 falsification (with the PASS-informed prior) remains the discriminating deliverable — γ⊥↓ → continue toward a rollout-SR-confirmed GO; γ⊥ plateau with the (ii) 19× signature → conservative-definite → (i). Reuse is maximal (3 existing scripts + 2 thin new + 1 orchestrator); INVARIANTS untouched; {11} strictly OUT.

---
**Conservatism note (§運用15):** capacity PASS = NECESSARY-but-NON-CONSERVATIVE (isolated ≪ on-policy) — it justifies building/trying, not a GO. Cost figures = 推測 (mechanism-reasoned; only the 15-16 min B1 rollout measured; truncated {0-3} ≈ 5-6 min = 推測). All (ii)/OG/capacity numbers = measured, cited to primary instruments. 0-commit pending %12 review + 5体 pre-debate; NO rollout proposed to execute here (rollout PROHIBITED until Rs GO). Design decision = Rs 専権; §R + §10 are labeled recommendations, not a method-swap.

*COORD2 %10 — 2026-07-03 23:56 JST*
