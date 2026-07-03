# DQ7 capacity pre-test — representation-capacity screen (rollout-free, ~0 GPU)

**Author:** RS-TECH-LEAD (%12). **Written:** 2026-07-03 22:45 JST (same-turn `date`).
**Charter:** Rs GO 2026-07-03 22:4x「すすめて」= 私の推奨シーケンス採択 (capacity pre-test を前進 / DAgger rollout 5点は capacity 結果を見てから)。
**Origin:** %9 enhancement (`DQ7_III_DAGGER_CROSSPV_PCT9.md:25`, "cheapest-falsifier-first ~0-GPU representation-capacity pre-test") → %9 が obs-switch REFUTED 後に **CENTRAL discriminator** へ昇格。
**Status:** SPEC — 0-commit build, offline, no rollout / no GPU-heavy / no locked-file. **final_L = L2** (new isolated generator + reuse train/og UNCHANGED, offline, default-off, reversible — (iv) 同 class の Rs-demotable L2; [VERIFY] = adversarial planning [本 spec] + %9 独立 cross-PV [dispatch 並行])。DESIGN-GATE = **SKIP** (pure imitation on synthetic data; no reward / no env / no success / no obs-schema change)。

---

## §0. Grounding (anchor set, §運用4 — cited from primary instruments)

| Anchor | Cite | Fact used |
|---|---|---|
| fork-(iv) arch (ADOPTED) | LEDGER `fork-(iv)` row 🟢 ADOPTED (Rs 2026-07-02) + `B_BC_BUILD_SPEC.md:130` | ABSOLUTE-TARGET actions, per-phase affine `a=2(wp−lo_p)/(hi_p−lo_p)−1`, meta `abs_affine[13][6][2]`; actor MLP standard, fork-(iv) = action repr |
| (ii) STOP baseline (一次) | `dq7_ii_cp3_batch/og/og_gate.json` via `DQ7_II_CP5_CROSSPV_PCT9.md:14` | movable γ⊥ {0}1.744/{1}1.056/{2}1.055/{3}1.034 all STOP (the on-path baseline this isolated test is compared against) |
| **(iv) confound removed** (一次) | `dq7_iv_pathfinder_report.md:6,18,44` | (iv) mixed synthetic co-move INTO route data → on-path/off-path budget tension → UNMET; capacity pre-test is **isolated** (no budget competition) → pure "can the arch represent restoring?" |
| **ignore-obs trap** (一次) | `dq7_iv_pathfinder_report.md:33-41` | (iv) aug-null got LOW γ⊥ by ignoring obs (val 29× garbage) = degenerate → γ⊥-low alone is NOT sufficient; a **varying-target** design + fit-check closes this trap (§2) |
| discriminator logic | `DQ7_III_DAGGER_CROSSPV_PCT9.md:25` | capacity FAIL (isolated でも γ⊥≈1) = representation-attractor → skip DAgger → (i) RL / capacity PASS = data-correlation → DAgger justified |
| {0-3} = frozen waypoint | `DQ7_III_DAGGER_SCOPING_COORD2.md:52-54` + %9 `:11` (independent: {0-3} 領域 no per-frame cable argmin) | {0-3} target = entry-derived-then-FROZEN abs waypoint, perturbation-invariant; cable static pre-contact → cable-seg obs = stable proxy for the frozen target |
| instruments (reuse) | `bc_train_route.py:37,46,59-63,131` + `og_offline_gate.py:36,286-288` | trainer (seed-PINNED, whole-demo val), OG γ⊥ gate (movable GO≤0.5/STOP≥0.9) — the SAME instruments as the (ii)/(iv) baseline, UNCHANGED |
| INVARIANTS | `RS71-System-Spec-SSOT.md:23-27` | #1-5; this test runs NO sim (offline synthetic-data + train + offline-gate) → INVARIANTS trivially untouched |

---

## §1. The question (and the one confound it removes)

**Q:** Can the fork-(iv) actor, given PERFECT isolated decorrelated restoring data (no on-path dilution), learn to output the frozen grasp target **invariant to a transverse own-ee perturbation** (γ⊥→0)? This is a NECESSARY-condition screen the ~1.5-5h DAgger rollout depends on.

**Why it is decisive now.** Three pure-BC approaches (B2 / (iv) / (ii)) plus the {11} obs-switch all converged on γ⊥≈1 (BC copycat: policy follows its own ee, ignores the cable obs). Two hypotheses remain, and they route to different (expensive) next steps:
- **coverage-limit** (data): the on-path/injected sets never covered the policy's own drift distribution → DAgger (on-policy relabel) is the fix.
- **representation-limit** (arch): γ⊥≈1 is an attractor the abs-target actor cannot escape even with clean data (scale-invariance 2mm≈10mm + 19× marginal collapse are yellow flags) → DAgger also plateaus → go to (i) RL.

(ii)/(iv) are **ambiguous** between these (`SCOPING:66`). The pre-test resolves it for ~90s: it isolates the arch's **capacity** from the data's **coverage**. The confound (iv) could not remove — it kept the on-path budget (`dq7_iv_pathfinder_report.md:6,44`) — is removed here by using ISOLATED data.

---

## §2. The isolated decorrelated set (the crux — closes the ignore-obs trap)

Build N synthetic samples over movable phases **{0-3}** (GRASP_HOVER/DESCEND/CLOSE/LIFT), in the **exact `bc_dataset_abs.npz` schema of the (ii)/(iv) baseline** (obs_dim, meta `abs_affine`, phase indices — read from the baseline npz meta; do NOT hardcode). Per sample:

1. **Sample a cable-seg position `c`** (the target source) from the plausible grasp-entry distribution (span the DR clip-Y range used in (ii); vary it **widely** so targets are non-degenerate).
2. **Frozen target `T*(c)`** = the entry-derived grasp waypoint the route would command: encode via the baseline's per-phase `abs_affine` (reuse `abs_affine`, do not invent) with the target-Y tracking `c` and X/Z at the frozen route constants (`GRASP_X` / `z_grasp`; per `SCOPING:52`). This is the abs label.
3. **Own-ee (obs own-R-ee dims) = `T*(c) + δ`**, `δ` a random transverse perturbation **decorrelated from `c`** (independent draw; magnitudes spanning the (ii) probe range incl. the 2-10mm + tail-20mm band). This is the "off-path" state.
4. **cable-seg obs dims = `c`** (stable pre-contact proxy of the target); other obs dims = plausible route constants.

⭐ **Why this closes the ignore-obs trap (`dq7_iv_pathfinder_report.md:33-41`):** because `T*` **varies with `c`**, a policy can only achieve LOW val by **reading the cable-seg obs** to emit the right target — a constant/ignore-obs output has HIGH val across the varying-target holdout. So **val-low ⟹ reads-target** (can't be the (iv) degenerate null). The copycat (follow own-ee = `T*+δ`) ALSO fails val, because `δ` is decorrelated from `T*`. The ONLY low-val solution is **read cable-seg → emit `T*`, ignore own-ee perturbation** = genuine restoring. This is exactly the "genuinely ee⊥target decorrelated" design %9 required (`CROSSPV:25,45`).

**Split:** generate a train set + an independent **varying-target holdout** (same distribution, disjoint `c`,`δ` draws) for `--val-dataset`. A separate **OG eval npz** (isolated states) feeds `og_offline_gate.py`.

---

## §3. Train + measure (reuse validated instruments UNCHANGED)

| step | command (schematic) | output |
|---|---|---|
| train | `bc_train_route.py --dataset <isolated_train>.npz --val-dataset <isolated_val>.npz --seed 0 --device cuda:1` | `policy_abs.pt` + `whole_demo_val_loss` (fit check) + sidecar (sha/seed/repr) |
| γ⊥ | `og_offline_gate.py --dataset-abs <isolated_eval>.npz --policy policy_abs.pt --out-dir <og>` | movable {0-3} `gamma_perp_mean` (SAME instrument/band as the (ii)/(iv) baseline) |

GPU: BC train is tiny (~90s), **GPU-1** (`CUDA_VISIBLE_DEVICES=1`, keep GPU-0 free for any recording). No sim, no rollout.

---

## §4. PASS / FAIL (three signals) + conservatism direction (§運用15, mandatory)

Read γ⊥ **jointly with val** (never γ⊥ alone — the (iv) trap):

- **PASS (arch CAN represent restoring → DAgger justified):** isolated `whole_demo_val_loss` LOW (fits the varying-target holdout ⟹ reads cable-seg) **AND** movable {0-3} γ⊥ drops toward **≤0.5** (ignores own-ee δ). ⇒ the (ii)/(iv)/{11} plateau was **data-correlation**, which DAgger's on-policy relabel breaks. → proceed to the DAgger 5-point decisions (Rs).
- **FAIL (representation-attractor → skip DAgger):** movable {0-3} γ⊥ stays **≈1** (still follows δ) despite low val AND perfect isolated decorrelated data. ⇒ the abs-target actor cannot separate "emit frozen target" from "follow own-ee" even when the data forces it → pure imitation (BC-family) is **capacity-exhausted** → **skip the rollout GPU, escalate to (i) expert-independent DAPG-RL** (P2-CRITICAL env build, separate Rs scoping).
- **⚠ degenerate guard (inconclusive, re-design):** if val is HIGH (can't fit even varying targets) with γ⊥ low → the ignore-ALL-obs collapse (the (iv) null signature) → NOT a genuine result; the set/schema is mis-built → fix + re-run, do NOT read as PASS or FAIL.

**Conservatism direction (mandatory):** the isolated capacity test is **EASIER** than closed-loop DAgger (perfect decorrelated labels, no compounding drift, no on-path budget). Therefore:
- **PASS = NECESSARY but NON-CONSERVATIVE** for DAgger success → it justifies *trying* DAgger, it does NOT promise the rollout works (rollout SR / §9 falsification still gate the GO).
- **FAIL = CONSERVATIVE-DEFINITE** → if the arch cannot learn restoring from PERFECT isolated data, it certainly cannot from harder on-policy data → **bank the FAIL, skip DAgger → (i)**. This is the strong, cheap screen (`CROSSPV:30,45`; same asymmetry that made the (ii)/(iv) STOP bankable).

---

## §5. L-triage + gates

| item | disposition |
|---|---|
| final_L | **L2** — new isolated generator (small, default-off) + reuse `bc_train_route.py`/`og_offline_gate.py` UNCHANGED; offline; reversible; no task_config / no locked-file / no reward-env-success keyword. (iv)-class, Rs-demotable. |
| [VERIFY] | adversarial planning (this spec §1-4) + **%9 independent cross-PV of the DESIGN** (dispatched in parallel). Full 5体 debate available if %9 contests the design; else the %9 cross-PV is the independent leg (the (ii)/(iv)/DAgger-scoping precedent). |
| DESIGN-GATE (`/reward-design`,`/pre-check`) | **SKIP (recorded):** pure imitation on synthetic data; no reward, no env, no success-condition, no obs-schema change. |
| HIGH-COST-GATE | **not triggered** — ~90s BC train, 0 rollout, 0 sim; « the 10h threshold. |
| rollout | **NONE** — this test contains no rollout; the rollout prohibition (fresh-Rs-GO) is untouched and remains for the DAgger leg. |
| locked-file | `test_newton_clip_routing.py` (markers 4477/4493/4593) UNTOUCHED — the generator reads route CONSTANTS (GRASP_X/z_grasp) but edits no marker; movable {0-3} is structurally clear of the {11} LOCKED region. |
| commit | build 0-commit; %12 commits the spec + (post-cross-PV) the generator as governance checkpoints (explicit-path, `--no-verify`, no AI attribution). |

---

## §6. THREAD-conditions + INVARIANTS

Runs **no sim** (offline synthetic-data → train → offline-gate) → INV#1 dual-arm / #2 88mm span / #3 DiffIK / #4 コ / #5 no-kinematic-trick all **trivially untouched** (no motion, no control, no geometry). obs schema UNCHANGED (generator matches the baseline npz schema). This is a property-of-the-trained-network probe, not a behavior.

---

## §R. Build items (%11) + cross-PV items (%9)

**%11 (build + produce numbers, HOLD verdict for %12+%9):**
1. Read the (ii)/(iv) baseline `bc_dataset_abs.npz` meta → obs_dim, `abs_affine`, phase indices, own-R-ee obs dims, cable-seg obs dims (**verify indices against the real npz — do not trust recalled indices**).
2. Build the isolated generator (§2): varying `c` → `T*(c)` label (reuse `abs_affine`) + decorrelated own-ee `δ`; emit train / varying-target-val / OG-eval npz. Small, default-off, 0-commit.
3. Run train (§3, GPU-1, seed 0) → val + policy; run `og_offline_gate.py` → movable {0-3} γ⊥.
4. Report the three signals (val, γ⊥ per {0-3}, and a spot check that output tracks varying `T*`); **do NOT self-declare PASS/FAIL** — that is the %12+%9 joint call (feedback-consult-percent2 / grasp-verdict deferral).

**%9 (independent cross-PV of the DESIGN, parallel, pre-verdict):**
- Is the isolated set genuinely ee⊥target-decorrelated (does val-low truly force reading cable-seg, closing the (iv) ignore-obs trap)?
- Is reusing `og_offline_gate.py` γ⊥ on isolated states a valid apples-to-apples vs the on-path baseline (any route-structure assumption in the gate that the isolated set violates)?
- Is the PASS/FAIL + conservatism direction (§4) correctly signed (isolated=easier ⟹ PASS non-conservative / FAIL conservative-definite)?
- Any missed degenerate solution beyond the ignore-obs null?

---
*RS-TECH-LEAD %12 — 2026-07-03 22:45 JST (書込前 `date`). 0-commit build / no rollout / INVARIANTS untouched / band=γ = CP-(ii)-5 unchanged.*
