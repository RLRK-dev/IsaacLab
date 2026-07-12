# W1 env build charter — T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild

**Author:** RS-TECH-LEAD (%12/w2:p4)。**Date:** 2026-07-12 13:51 JST。
**Status:** DRAFT v0.1 — **PENDING p1 (OPS-SUP) verify** (trainer-DEFINE precedent: p4 draft → p1 独立 verify → bank)。B0 (前提条件) のみ即時着手可 (既 co-decide 済、§2)。B1+ の builder 着手 = p1 verify PASS 後。
**これは何か:** Rs W0-a「A」一括承認 (2026-07-12 13:29、`W0A_PACKET_RSTECHLEAD_20260712.md:89` decision-of-record「W1 (env build) 着手可」) を受け、banked Stage-A 設計 (spec v0.8.1、全 gate PASS) を **実装 chunk 列 (staged ≤800 行/diff、各 chunk = 独立 L3 chain)** に分割し、担当・DoD・順序・衛生規則を確定する build 実行計画。**本 charter は新しい設計判断を含まない** — 全内容は banked 文書からの転記 + staging。設計からの逸脱が必要になった場合は build せず STOP → spec ERRATUM 手続き (§7-4)。
**Authority chain:** Rs W0-a「A」(13:29) → trainer charter `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md` §3-A → **設計 SSOT = `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.8.1** (banked d17f8f9cd6/e8d53aae10 + W0-a 承認) + `STAGEA_REWARD_ARTIFACTS_20260712.md` v3.3 → devplan `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md` §7 W1-3/4 行 (:192、担当割当の正) → LEDGER row49 (trainer) / row50 (Stage-A)。
**campaign 不発効 (不変):** 本 charter のいかなる記述も訓練 campaign を authorize しない — campaign = HIGH-COST-GATE + production-launch-gate + **fresh Rs GO** 背後 (W0A_PACKET:91)。

**用語 (初出定義):** chunk = 1 回の L3 chain で審査・commit する実装単位 (diff ≤800 行) / route_t = route 進行時計 (episode 時計と分離、HOLD で凍結) / HOLD = cable 実測乖離 (div_grip) 超過時に route_t を止める安全機構 / div_grip = 把持中 cable 節の記録軌道からの乖離 [mm] / bank v2 = phase 途中開始用の cable 込み状態保存・復元 / OG = GPU 不要の忘却警報計器 / DR = 環境条件の意図的ばらつき (cable XY offset) / byte-preserve = 全新機構 flag-OFF 時に既存挙動が byte 単位で不変であること / 抽出 twin = Rs-LOCKED producer を faithful 抽出した committed 複製 (`route_executor.run_route`:1028、byte-repro 81/81 実証)。

---

## §1. Scope 境界

- **IN:** Stage-A spec v0.8.1 の全 build 項 (§10 cost 表 8 行、est ~1.35-2.55k LOC) = oracle-query-API + per-world route_t / cable-metric HOLD / bank v2 / transition export + reward 会計 / DR wiring + per-world recenter + curriculum 統合 / OG port + legs A′B′C′ / recording contract v2 / smoke 一式 (§8 legs)。
- **OUT:** 訓練 campaign (Stage-C/D、fresh Rs GO 背後) / P3 demo-set (W3、smoke 後直列) / R3 trainer build (W4+) / **設計変更** (spec v0.8.1 が設計 SSOT — 実装中の設計疑義は STOP → §7-4) / `task_config.py` (不触、パラメータ必要時は STOP → Rs) / Rs-LOCKED `test_newton_clip_routing.py` (不触 — capture は抽出 twin に pin、spec §6.2-1 v0.7 C3)。
- **数値基盤 (Rs W0-a 採択値、smoke 再導出条項付き = その条項が governs):** HOLD_THRESH 15mm / resume ≤12mm or 3-step in-band / MAX_HOLD 24 (placeholder、§8 hold-fires leg で再導出) / `DELTA_BOUND_M=0.020` 正式授権 / DR cable XY ±20mm **既定 OFF** / curriculum 開始 mix 集合 {P0, G1−ε..G5−ε} (比率 = smoke 後 Rs 単独項、M-1 deferral)。

## §2. B0 — build 前提条件 (即時着手可、既 co-decide 済)

| # | 項 | 内容 | 根拠 |
|---|---|---|---|
| B0-1 | **c1pin dirty diff = REVERT** | `newton_route_env.py` +23 行 / `route_executor.py` +70 行 (FORK-1 fix 仮説 = REFUTED arc) を revert。執行 = **%11 (diff owner、他 pane 未 commit の silent 破棄禁止則に適合)** | spec §0-H4 (disposition = build 前提条件) + %11 推奨「dead-branch→revert」+ %12 CONCUR (COORD handoff 07-12)。on-disk 実測 13:4x: 両 diff 残 dirty 確認済 |
| B0-2 | B0-1 帰結の記録 | revert により consumer ③ (ff replay / c1-pin onset) は **ff replay のみに縮退** — §5 pin event telemetry は縮退後 wiring (spec §5 M4 の条件節どおり) | spec §0-H4 / §5 M4 |
| B0-3 | og_offline_gate.py format-only diff | disposition = %11 判断 (commit or revert、trivial)。B6 着手前に clean にする | spec §0-H4 (format-only 確認済) |
| B0-4 | **baseline sha pin** | B0-1/3 完了後、byte-repro ref-subset (`test_routeexec_byte_repro.py`) を再走 → 以後の全 flag-OFF byte-preserve leg の **pinned baseline sha** とする | spec §8 flag-OFF 行 (pinned baseline sha 要求) |

## §3. Work breakdown — chunk 列 (各 ≤800 行/diff、各自 L3 chain)

依存 DAG: **B0 → B1 → B2 → {B3, B5} → B4 → B6 → B7** (B3/B5 は B2 後に並行可; B6 は B5 の export/契約形式に依存; B7 = 総仕上げ smoke。ただし flag-OFF byte-preserve subset は **毎 chunk 実行**)。

| chunk | scope (設計 cite) | est LOC (spec §10) | chunk DoD (regression 込み) |
|---|---|---|---|
| **B1 route_t 骨格** | per-world `route_t` 新設 + 時計消費者 4 系統付替え (①step_target ②grip staircase ③ff replay ④obs[50]) + interface v2 `reset_to_phase(k, world_ids=None)` (v1 consumer 5 点 disposition + **新規 consumer #6** = step() per-world done-reset の re-fork 呼出) + **flag-gate default-OFF** (spec §4.1) | §10 行1 の route_t 側 ~200-400 | route-clock 単一源 grep leg (episode_length_buf を route 系が参照 = 0) / flag-OFF byte-preserve subset / test_routeexec_writesite・state_bank の期待値更新 (spec §4.1 H6) |
| **B2 HOLD + oracle API** | recording contract v2 (`cable_xyz`+`held_seg_l` 必須 key 昇格、spec §4.2 N9) / div_grip metric (s=held_seg_l[f]、f=chunk 終端 clamp) / arming = G1-latch 後 / resume hysteresis + chatter telemetry / 非有限 = fail-HOLD + loud event / grip = chunk 終端値 定値 hold / query() API 形状 (spec §4.2/§4.3) | §10 行1 残 ~200-300 + 行8 50-100 | **hold-quiet-pre-onset** (健全域 f0-336 発火 0) + **hold-fires-at-onset** (f343±1 chunk) — 両方 residual≡0 CPU replay で chunk 内 discharge 可 (0-GPU) / claim ① 実測 (drift-under-HOLD < 0.58mm/RL-step) は B7 に委譲可 / flag-OFF byte-preserve subset |
| **B3 bank v2** | producer-side capture dump 新規 (**抽出 twin `run_route`:1028 に pin** — locked 不触) / cable JOINT 空間 q/qd + arm/gripper q/qd + chunk 境界整列 / env-level restore = `seed_cable_joint_state` per-world 変異体 (qd 非 zero) / restore-exact + fidelity DoD (qpos/qvel L∞ ≤1mm/1mm/s ∧ div_grip ≤ 健全域 band [§8 正整合再計測値が governs] + **1-step post-restore 動力学 leg** [body_q_prev/Dahl hidden state 盲点対策、spec §6.2 M10]) / **capture は cell-parameterized に設計** (§6-5 multi-cell option 前方互換) | 150-300 | restore fidelity DoD 全数 / bank-start 正制御 per-k 差別化 bar (k=1,2: G_{k+1} 到達 / k=3-5: fidelity+HOLD 正発火+no-drop、spec §8 H1) は GPU 要 → B7 で discharge、B3 では CPU restore-exact leg まで / flag-OFF byte-preserve subset |
| **B4 DR + curriculum** | CABLE_XY_OFFSET per-world config 配列 (os.environ 経路廃止) + `_reset_worlds` 適用 / **per-world recenter 新設** (GRASP_YC/x_grasp 系譜の env-level 一般化、spec §6.1 M1) / 開始 mix 機構 (集合のみ、比率 = Rs 後決) / DR×curriculum 相互排他の LOUD 実装注記 | 100-250 + 50-150 | recenter 単体 unit leg / DR OFF 既定で flag-OFF byte-preserve subset / DR-corner 実測 leg は B7 |
| **B5 export + 会計** | transition export (core/reward 会計/projection/telemetry/provenance 5 group、spec §5 表) / r_paid・r_phase_earned・overridden 分離 / termination_reason + invalid_mask / HOLD・G3-stall・pin・suppressed-drop event / npz shard + manifest + rotation 方針 pin | 150-300 | export 完全性 2 述語 leg (¬overridden: 成分和≡r_paid / overridden: r_paid=−10 ∧ earned 保全) / time_out flag ⇔ episode_length==900 grep+unit leg (spec §5 M3) / flag-OFF byte-preserve subset |
| **B6 OG port** | legs A′B′C′ 再設計実装 (no-sim 契約保全、nominal cell scope) / og_gate.json schema_version / **13x-replicate null artifact を 62D/α-6D 契約で再生成** (leg-C′ precondition) / 旧 schema 消費者 (dagger_loop:203-208 等) = retire-or-migrate 判断は R3 build 時 (触らない) | 250-450 | legs A′B′C′ が canonical artifact 上で数値を返す (band 判定はしない — α/β/γ = Rs 後決) / no-sim 契約 grep leg (solver/mujoco/newton import 0) |
| **B7 smoke 一式** | spec §8 残 leg 全数: throughput ≥9.7fps / device-parity cuda:2 + cg-GPU whole-route screen / HOLD 込み horizon 設計算術 leg (paper) / bank-start per-k 正制御 / bank-G3 fork 摂動 (claim ② 実行 leg) / DR-corner (drift-rate 再計測 alert>10 / breach>20 mm/RL-step + per-cell div profile) / IK 残差分布 probe / claim ① 実測 | 150-350 | spec §8 表の bar が正 (転記しない — spec 参照)。**MAX_HOLD・HOLD 閾値系の再導出値 + curriculum mix 比率提案 + OG band α/β/γ 提案 → W1 完了報告で Rs 単独項として提示** (§6) |

**LOC 総和 ~1.35-2.55k = spec §10 と一致 (staged 分割で不変)。** chunk 境界は目安 — 実 diff が 800 行に迫る場合は builder 判断で更に分割 (統合は不可)。

## §4. per-chunk gate template (全 chunk 共通、L3)

1. **pre:** [L-TRIAGE] (env diff キーワードで auto-L3 想定) → [CHECK] = 対象 spec § を read + cite (**実装は spec 準拠を示す conformance 表を 1 個添付**) → [VERIFY] 5体 (scope = **implementation-vs-spec fidelity。設計の再審議は OUT** — 設計は banked spec v0.8.1; 設計疑義発見 = STOP → §7-4) → [RULE-CHECK] Tier0-3。
2. **post:** 層3 = **single-file lint のみ** (`./isaaclab.sh -f` tree-wide 禁止、spec §10 M12) + chunk DoD legs (§3 表) + **flag-OFF byte-preserve subset (毎 chunk、pinned baseline sha 比較)** + 層5 (L3 該当) + %10 audit + %12+%9 verify → **explicit-path atomic commit** → p6 relay (milestone 毎、batch 溜め禁止)。
3. **motion-bearing smoke leg (B7 の bank-start / bank-G3 / DR-corner 等) の RESULT = 視覚レグ必須** (`/verify-run` or video-analyst skill-path)。throughput/parity 等の非 motion 数値 leg = 数値のみで可 (justified: 測定対象が fps/一致性で motion 妥当性でない)。**物理妥当性の正式 verdict = Rs video human-GT (Rs 専権、autonomy grant 除外項)。**
4. GPU leg 運用: cuda:0 (route canonical) + cuda:2 (parity)。`CUDA_VISIBLE_DEVICES` 必須 / `nvidia-smi --query-compute-apps` 事前確認 / smoke 級 (≪10h) = HIGH-COST-GATE 非該当、ただし [RUN] 規律 + 検証順序 (動画→ログ→照合) は全適用。

## §5. 担当 (devplan §7 W1-3/4 行:192 が正)

- **build = %11 (COORD、w2:p3)** — standby trigger 済 (COORD handoff「trigger = W1 build charter (builder leg)」)。envbuild node と 1:1 binding。
- **audit = %10 (COORD2、w2:p2)** / **verify = %12 (本 pane) + %9 (OPS-SUP、w2:p1)**。
- Rs = video human-GT + §6 の後決項のみ。進捗 = p6 (PLAN-KEEPER) へ milestone 毎 relay。

## §6. Rs 後決項の carry (W1 を block しない、期日 = 各 trigger)

| 項 | trigger | 提示者 |
|---|---|---|
| OG band α/β/γ | B6 port + null 再生成後の実測 (W0A_PACKET §2b「open」) | %12 |
| curriculum mix 比率 | B7 smoke 後 (M-1 deferral、単独項) | %12 |
| MAX_HOLD 確定値 + HOLD 閾値系の n>1 再検証結果 | B7 hold-fires / nomA/nomB legs 後 | %12 |
| M-AB probe 発火時期 (imitation A-vs-B、pre-registered) | oracle 稼働 = W1 完了後が自然 (p1 C-1 の Rs 再提示参照) | %12 |
| multi-cell bank capture option | **W0-a 一括「A」により採 (解釈 LOUD: §2a 行の提案 = P3 収録 piggyback → 発効 = W3。veto 可)**。W1 影響 = B3 capture の cell-parameterize (前方互換のみ、追加 build なし) | — |
| C2-seating video human-GT | Stage-C (RL-deferred、既登録) | — |

## §7. 衛生・compliance (全 chunk 拘束)

1. **INVARIANTS 不触** (DUAL-ARM / 88mm span / DiffIK-only / gripper コ LOCK / no-kinematic-trick)。抵触設計が必要に見えた時点で STOP → BLOCKED_FOR_USER。
2. **共有 dirty tree 規律:** explicit-path commit のみ / tree-wide pre-commit 禁止 (M12) / 他 pane 未 commit 変更の silent 破棄禁止。
3. **timeouts 純度:** terminal (drop/explosion) ∉ time_outs (spec §5 M3 leg が discharge を機械化)。
4. **設計逸脱手続き:** 実装中に spec v0.8.1 と実体の矛盾を発見 → build 停止 → %12 へ報告 → spec ERRATUM (影響が設計 semantics に及ぶ場合は Rs surface) → 再開。builder の独自設計判断で回避しない。
5. **prior-art V7:** 各 chunk 着手前に再走 (devplan §10 準拠)。
6. 訓練プロセス kill / ハーネス停止 = Rs 承認必須 (prohibited.md、smoke でも同じ)。

## §8. Provenance / 検証記録

- prior-art guard (本 charter 起草時、13:4x): BLOCKER hits = 全て認可 Stage-A 設計系譜の自己参照 (spec v0.8.1 §13 表 / STAGEA_CROSSPV 両台帳 / stageA node state.md) — **失敗経路の再走なし → PASS disposition** (stageA node 10:31 entry と同型: 認可設計の自己 hit)。
- on-disk 実測 (13:4x): c1pin diff +23/+70 残 dirty / og_offline_gate.py dirty / `run_route` = route_executor.py:1028 実在 / 抽出 twin byte-repro 81/81 = spec §6.2 cite (`50f877c7f5`)。
- 本 charter = 転記 + staging のみ、新規設計判断なし。verify leg = p1 (OPS-SUP) 独立検分 (trainer-DEFINE precedent) — 結果は本 doc の Status 行と node state.md に反映。

*%12 — 2026-07-12 13:51 JST。PAPER-ONLY (本 doc 自体は build しない)。INVARIANTS / task_config.py / Rs-LOCKED files 不触。*
