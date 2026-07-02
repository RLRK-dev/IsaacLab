# OG改修 v3.1 — B1′ regression 対照表 (④ deliverable)

**og_offline_gate.py** に FINAL spec §1.4 item (1)-(4) を実装 → B1′ artifacts で新旧 OG 並走 regression。
**run:** `og_offline_gate.py --dataset-abs b1p_dataset/bc_dataset_abs.npz --policy b1p_train_e2000/policy_abs_e2000.pt --full --device cuda:0` (offline, no sim). old = `b1p_og_e2000_full/og_gate.json` / new = `b1p_og_e2000_v31regression/og_gate.json`. ruff clean / py_compile OK / locked 3-file 0-diff / 0-commit. **2026-07-03 00:16 JST.**

## (i) clip-anchored 4 seat γ⊥ = 旧と一致 (holder fix はこれらに不触 — R保持のまま)

| phase | old γ⊥ | new γ⊥ | |
|---|---|---|---|
| C1_SEAT | 0.658 | 0.658 | ✅ MATCH |
| C1_PIN | 0.716 | 0.716 | ✅ MATCH |
| C2_DUAL_SEAT | 0.83 | 0.83 | ✅ MATCH |
| C2_SETTLE | 0.732 | 0.732 | ✅ MATCH |

= item (i) PASS。§運用28: これら 4 は L_HELD_PHASES 非該当 → holder=R 不変 → γ⊥ byte 一致。%12 の pre-check 実測 (0.658/0.716/0.83/0.732) とも一致。

## (ii) C2_REGRASP: 旧 γ⊥=1.17 → 新 (b)-pair

| metric | value | band | 読み |
|---|---|---|---|
| seg_following_gain | **0.096** | PASS=[0.8,1.2] → **FAIL** | R は L保持 cable を追わない (≪1) |
| ee_only_gain | **0.929** | ≥0.9 → **STOP** | R は自身の ee drift を積分 (integrator) |
| pair verdict | **STOP** | | |

= item (ii) PASS。旧の単一 γ⊥=1.17 (integrator) を pair が正しく分解: 「cable 非追従 (seg 0.096) かつ 自己 drift 積分 (ee 0.929)」= n=1 integrator の正確な読み。単一 γ⊥≤0.5 bar が wrong-signed だった問題を解消。

## (iii) DR-movable {0-3} = 初 surface (旧は gate 集合外で不可視)

| phase | old (in gate?) | new γ⊥ | new gate |
|---|---|---|---|
| GRASP_HOVER | ❌ 不可視 | 5.279 | STOP |
| GRASP_DESCEND | ❌ 不可視 | 1.499 | STOP |
| GRASP_CLOSE | ❌ 不可視 | 0.726 | MIDDLE |
| LIFT | ❌ 不可視 | 0.968 | STOP |

= item (iii) PASS。item (4) の surface 拡張が機能: verdict 表が要求する DR-movable 行が初めて gate に出た。値は integrator 帯 (n=1 なので当然、informative)。旧 gate は VERDICT_CRITICAL のみ surface で {0-3} は計算すらされず不可視だった。

## (iv) OVERALL: 旧 STOP → 新 STOP (+ decoupled middle EXEMPT 実証)

| | old | new |
|---|---|---|
| overall | **STOP** | **STOP** |
| oga | STOP (sweep-z 3 STOP) | STOP (同 3 sweep-z decode STOP) |
| ogb | STOP (C2_REGRASP 1.17) | STOP (movable integrator + cable-pair + GUIDE_C2) |

**⚠ §運用28 reconciliation:** %12 item ④(iv) は「旧 = BLOCKED_FOR_USER」としたが、旧 json の `overall_verdict` = **STOP** (BLOCKED ではない)。旧 STOP の実体 = OG-a の sweep-z 3 STOP (GRASP_HOVER/Lz p95 23mm 等) + OG-b C2_REGRASP γ⊥1.17 STOP。新も STOP、内訳は anchor-class に分解。両者 STOP で結論同一だが、旧 verdict 名は STOP。

**⭐ NEW-1 fix 実証 (decoupled middle EXEMPT):** 新表で decoupled MIDDLE = 7 cell (ROUTE_C1 / C1_SEAT / C1_PIN / L_HALF_UNCLAMP / R_UNCLAMP_RISE / C2_DUAL_SEAT / C2_SETTLE) が **informative (GO を block しない)**。旧の uniform any-MIDDLE→BLOCKED ならこれらが BLOCKED を強制していた。新表では exempt。今回は real STOP が支配して overall=STOP だが、exempt 機構自体は動作確認済 (go_conditions に decoupled middle は不関与)。

**GO conditions (全 False = n=1 では当然):** oga_no_stop=False (sweep-z STOP) / movable_all_GO=False (integrator) / cable_pair_PASS=False (pair STOP) / null_beat_ge_margin=False (null 未供給 → None)。= n=1 では GO 不能、正常。B2 (multi-demo + null) でこれらが埋まるかが本番。

## 実装 notes (owner-verify + %12 判断待ち 2 点)

- **item (2) を og_bprime にも拡張 (%12 判断乞う):** %12 の item(2) cite は :63,:80 (og_b) のみだが、holder 原則の一貫性のため og_bprime の co-move + perturbation も holder-arm 化した (L_HELD_PHASES は L軸を perturb + co-move)。og_bprime は characterization (gate 非関与) ゆえ verdict に影響なし。R-fixed のまま残すと og_b と不整合になるため拡張したが、最小 scope 厳守なら og_bprime は据え置きも可 — 指示乞う。
- **carried-STOP 集合は B2-time 入力:** 今回 regression は `--carried-stops` 空 → 全 STOP 計上 (GUIDE_C2 decoupled STOP も計上)。GUIDE_C2 (decoupled integrator γ⊥1.015) が n=1-carried なら B2 で `--carried-stops GUIDE_C2` → informative 化。carried 集合の確定は B2 adjudication (%12/Rs)。
- **backward-compat:** 13-schema で clip-anchored γ⊥ byte 一致 = 既存 OG-a/b path 不破壊を実証。`range(13)→range(affine.shape[0])` + `PHASES=meta.phase_names` で 15-schema 対応 (B2 で自動)。
