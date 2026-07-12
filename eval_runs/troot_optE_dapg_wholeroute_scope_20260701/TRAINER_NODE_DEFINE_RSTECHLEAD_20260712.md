# Trainer node DEFINE (charter) — T-ROOT-optE-route-dapg-C1C2-P2-trainer

**Author:** RS-TECH-LEAD (%12/w2:p4). **Date:** 2026-07-12 09:34 JST.
**Status:** DEFINE **BANKED** — pivot co-decided p4⇄p1 (OPS-SUP) under Rs autonomy grant (2026-07-12 08:xx「ユーザ動画確認以外は君の判断か T-ROOT-OPS-SUPERVISOR と相談してきめていい」). p1 verify = **PASS** + P4 Δ-bound discharge = **PASS both conjuncts** (09:31, script `p9_p4_deltabound_discharge.py` sha fdcacf98). **DEFINE ≠ launch:** no build/GPU in this doc; every campaign stays behind HIGH-COST-GATE + production-launch-gate + fresh Rs GO. Rs veto point = W0-a review (devplan §7/§8 decisions + numeric thresholds remain genuinely OPEN).
**Authority:** `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md` (LEDGER row47, Rs W0-a′ v1.1 approved). ⚠ `DAPG_DESIGN.md` cited at CLAUDE.md:288 = phantom (never tracked, confirmed absent) — flagged to Rs, pointer fix = Rs-gated.

**Term defs:** RLPD = SAC + 50/50 demo/online replay + LayerNorm ensemble critic + high UTD (no-pretrain online RL with prior data). residual-on-script = policy outputs a small per-step non-cumulative offset Δ on the frozen scripted route's absolute target. oracle-query-API = runtime "what would the script do here" interface. OG = offline gate (0-GPU 3-leg forgetting alarm). FORK-1 = confirmed root cause: open-loop scripted replay chaotically amplifies a ~0.15mm builder-fork cable-settle micro-difference → grip loss; closed-loop feedback is the only fix (static param/build/pin/substep fixes all REFUTED; routeexec state.md 04:18).

---

## 1. Node identity (NEST §2.1)

- **node_id:** `T-ROOT-optE-route-dapg-C1C2-P2-trainer` (p1 Q-a: P2-sibling consistency; algo in name below)
- **node_name:** "P2 whole-route RL trainer (RLPD residual-on-script) — FORK-1 closed-loop fix + carry-forward"
- **parent_node:** `T-ROOT-optE-route-dapg-C1C2`. Sibling of P2-envcore (部品①) + P2-routeexec (部品②); this = 部品③ (staged chain: env-core → route-executor → oracle → OG → trainer).
- **children_nodes:** [] — Stage-A (P2 env design-gate) lazy-spawns as first child when the L3 design-gate work starts (p1 Q-b; env-core/routeexec precedent). Pre-creating all 4 stage nodes = premature.
- **existence/scope authority:** W0-a′ bulk-approval staged chain includes trainer (`b7d7857dfc`) = charter-authorized (same precedent as env-core/routeexec; NEST §3.1 satisfied). Pivot decision = Rs delegation + p4⇄p1 co-decide (CONCUR-with-corrections, no blocker).

## 2. goal

Build + train an RL **closed-loop** policy (RLPD; residual-on-script primary per devplan D-C) achieving the whole C1→C2 route under DR ±20mm — **fixing FORK-1** by per-step feedback correction of open-loop drift. Frozen base = banked byte-repro oracle (`6d1cee5874`). Same env/yardstick as devplan ladder.

## 3. goal_verification / DoD — STAGED + GATED

| Stage | Deliverable | Gate |
|---|---|---|
| **A. P2 env** (devplan §6) | whole-route env off-policy+oracle-ready: oracle-query-API (**CRIT1 phase-clock ownership resolved** §6-1/§6-10) + within-phase progress scalar in obs (§6-2) + contract unified 1-schema (§6-3, HIGH5 disposition) + **Δ non-cumulative contract + Δ=const zero-drift regression test** (§6-9, envelope = P4 result below) + transition export + reward-component logs + phase/seat/pin events + DR hooks (subsumes routeexec-⑦ env-level CABLE_XY_OFFSET) + **⑦(b) cable-fork curriculum-reset machinery** (banked phase-k cable_xyz capture + env seed, routeexec LOUD-CARRY) + throughput & device-parity smoke (§6-8) + **OG port + composite 導出 + band 再較正** (§4.3-a/b/c) | **L3 design-gate:** `/reward-design` + `/pre-check` + 5体 [VERIFY] + %9/%11 cross-PV + 層5 (W0-c; can draft in parallel with Rs W0-a) |
| **B. P3 demos** | DR±20mm demo-set + script-SR-over-DR-grid 検収 (survivor-bias falsifier) + leg-2 batch (adj-A + seg-co-move) | 代表性 gate |
| **C. R2b campaign** | residual-on-script RLPD. Bar = DR±20mm in-sim category-SUCCESS beating script-under-DR baseline by band separation, N≥30 — **exact bar TBD = Rs W0-a §4.3** (devplan draft値 ≥70% は illustrative; p1 correction-2)。carries routeexec-③ ⑨b live-numerator + routeexec-④ closed-loop full-fire + **C2-seating video (Rs human-GT = Rs-exclusive, anchor point3 / r5 CLASS-R)** | ⛔ HIGH-COST + production-launch-gate + **fresh Rs GO (no GO until thresholds fixed — devplan §4.3)**。R2a = contingent-only |
| **D. R3** | new off-policy trainer build ~500-800 LOC (SAC/TD3/replay = ZERO in repo; 2nd cost cliff) + campaign | L3 build + HIGH-COST + Rs GO |

**Node success predicate:** closed-loop whole-route policy meets the Rs-fixed Stage-C/D bar under DR; motion-bearing verdicts = video-first + %12+%9 joint + **Rs video human-GT for physical validity (Rs-exclusive per autonomy grant)**.

## 4. means

devplan §5 (R2b/R3) + §6 (env) + §7 (gate plan) + §8 D-C: R2b residual-on-script primary (PARKED-A un-park; adopted via delegated co-decision under Rs autonomy grant — **DQ1=B→A′ supersession to be banked in LEDGER same-turn; Rs veto at W0-a**) / R2a contingent-only / R3 RLPD default + BC-proposal fallback (oracle-direct = unverified THREAD variant, caveat) + horizon-arm ≥1.

## 5. dependencies

- **precedent (satisfied):** P2-routeexec COMPLETE-with-carry-forward (oracle banked `6d1cee5874`, byte-repro re-verified x0_y0 09:0x) / P2-envcore COMPLETE (valid RL substrate — FORK-1 (a1) exonerates the builder; Option B vindicated).
- **blocker (gate the CAMPAIGNS, not the Stage-A design work):** Rs W0-a — D-A〜D-D confirm + numeric thresholds (§4.3) + OG band α/β/γ. oracle-API CRIT1 semantics = Stage-A design-gate item.

## 6. routeexec disposition — COMPLETE-with-carry-forward (orphan-zero, p1 correction-1 resolved)

Full DoD ①-⑧ enumeration (evidence-cited):

| routeexec DoD | Disposition | Evidence |
|---|---|---|
| ① byte-repro 58/81 EXACT | **DONE** (core deliverable) | oracle banked `6d1cee5874`; ref-leg self-check x0_y0 == golden RUN1_REFERENCE_V2 PASS (09:0x); node:16 |
| ② ⑦(a) restore-L∞ static | **DONE** | comp2 `433ba6b246` (node goal_verification) |
| ② ⑦(b) live 1-step + cable-fork LOUD-CARRY | **TRANSFER → Stage A** (curriculum-fork reset machinery: banked phase-k cable_xyz capture + env-level seed) | node:13 ⑦(b) REQUIREMENT %12 RULING 17:13 |
| ③ ⑨b online-numerator (residual≡0 ×81 live) | **TRANSFER → Stage C** (FORK-1-blocked for scripted; becomes the trainer's live-eval leg) | node:16 arc 残 |
| ④ ⑥ 6-phase full-fire live | **DONE-as-diagnostic** (NUMERIC_NOGO banked = the FORK-1 finding `85b8982546`/`65ae2c17fa`); closed-loop success criterion **TRANSFER → Stage C** | node:16/:30 |
| ⑤ 58/81 wall/spacer exact predicate | **DONE** — strict_v2 counting uses c2_seated_honest (wall-dist ≤0.5 spacer-excluded + groove-z) ∧ c1_final | `p9_recount_strict_v2.py:6,:108`; producer :5565-5580. ⚠ numeric ≠ capture (r5 §1.4 #3): Rs-video stays GT for physical validity |
| ⑥ C2-seating video gate | **TRANSFER → Stage C** with honest status: single-world cell-2037 video = **Rs human-GT REJECTED** (cable off C1); scripted path FORK-1-fragile → RL-deferred (gate-2 recommendation) | Rs 2026-07-12; r5 §1.4 STEP16 CLASS-R |
| ⑦ CABLE_XY_OFFSET per-cell wiring | **DONE at harness level** (byte-repro per-cell `CABLE_XY_OFFSET=dx,dy`); env-level DR wiring **TRANSFER → Stage A DR-hooks** (§6-6) | `test_routeexec_byte_repro.py:166`; module envs grep = absent |
| ⑧ ⑬-enabler | **precursor DONE** (single-source w/ BC/trainer base, node:77 Stage-A deliverable); remainder (C1-escape non-vacuous cell 供給) + ⑬-VERDICT **TRANSFER** (VERDICT already trainer-deferred per Rs D-2 23:5x) | node:24,:77,:112,:127 |
| (arc) comp3b re-seed | **retired as standalone** — p1 NULL-analysis: re-seed can't fix phase-3 INTRA drift (t280 pre-boundary) + fixed-traj can't yield DR generalization; its machinery = ⑦(b) transfer above | p1 09:11 |
| (arc) FORK-1 別 MW-node (option A, unbuilt) | **SUBSUMED into this node** (1-node; RL closed-loop on env-core MW = the fix itself; legal — unbuilt ≠ DISCARDED, no §3.7 conflict) | p1 Q-c/NEST verify |

## 7. P4 Δ-bound — DISCHARGED (p1 leg, 09:31, both conjuncts PASS)

- **(i) magnitude FEASIBLE:** per-step drift-rate `diff(div_seg24_mm)` (pB cablediag.npz, 499-frame): |inc| mean 0.27 / p95 1.08 / max 1.86 mm/frame (accumulated 58.13mm = 397-frame integral). Δ-bound outpaces per-step ~1-2mm/frame, NOT the accumulated 58mm — why closed-loop saves what open-loop can't. max 1.86×decimation d < F-1a ±22mm authority for d∈{1,5,10} → residual regime holds at all plausible control freqs. **Exact Δ-bound = per-step-rate × d, pinned at Stage-A §6-9 after control-freq fixed.** Conservative: sized on open-loop rate ≥ closed-loop rate.
- **(ii) expressibility PASS:** seg24 = grip seg (rigid-grip, EE-position directly governs); FORK-1 drift = lateral ∈ EE-controllable position subspace; α-6D dual-arm position-only expresses the correction (rotation not required); grip-held window long (drift-rate small pre-t397).
- **Honest limit:** feasibility = necessary-not-sufficient — whether RLPD LEARNS the correction = Stage-C campaign question (non-conservative claim; P4 removes the architectural blocker only).

## 8. Compliance

- DEFINE = planning artifact on banked devplan; **no future gate pre-empted** (devplan §10). L3 design-gates fire at Stage-A. Campaigns = HIGH-COST + production-launch-gate + fresh Rs GO.
- Banking (this turn): this charter + trainer node state.md + routeexec disposition entry (commit, explicit-path) → p6 relay for LEDGER (row47-adjacent trainer row + **D-C DQ1=B→A′ supersession note**) + map + manifest cascade.
- Rs-専権 untouched: 07-Design/04-Specs, CLAUDE.md:288 pointer (flagged only), video human-GT.

---

## ERRATUM (2026-07-12 11:5x, %12 — Stage-A /pre-check 3走目 ISSUE-A、records-must-match-fact)

§7 (i) の drift-rate 単位表記を訂正する: `diff(div_seg24_mm)` の元データ (pB cablediag npz) は **env.step 毎 (= RL step、10 physics frames 間隔) の sample** であり、|inc| mean 0.27 / p95 1.08 / max 1.86 の単位は **mm/RL-step** (原文の mm/frame は誤り)。従って「Δ-bound = per-step-rate × decimation」の × d は二重計上 — 正: 必要 per-RL-step 補正 ≈ 実測 max ~1.9 mm/RL-step ≪ DELTA_BOUND 20mm ≤ F-1a 22mm。**結論 (magnitude FEASIBLE) は不変で余裕は ~10× に拡大 (保守側誤り)**。expressibility (ii) は非影響。詳細 = `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.5 §2 + §13。p1 (OPS-SUP、P4 discharge leg 実施者) へ通知済み。
