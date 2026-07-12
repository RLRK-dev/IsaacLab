# W0-a packet — Rs 決定事項一式 (trainer node / Stage-A 設計確定後)

**Author:** RS-TECH-LEAD (%12/w2:p4)。**Date:** 2026-07-12 13:24 JST。**宛先:** Rs。
**これは何か:** RL trainer 計画 (devplan LADDER v2) と Stage-A 設計 (spec v0.8、全 gate PASS・banked d17f8f9cd6/e8d53aae10) が Rs の決定待ちにしている項目を **1 枚に集約した決定 packet** です。内容は全て banked 文書からの転記 + 提案値であり、**本 packet 自体は新しい設計判断を含みません**。
**承認の効果:** §1+§2 の承認 → **W1 (env build) 着手可**。campaign (訓練実行、GPU 数日級) はそれでも動きません — 別途 HIGH-COST-GATE + production-launch-gate + **fresh Rs GO** が必要 (不変)。
**同梱 evidence (§4):** 全て commit 済み。two-key: 本 packet は p1 (OPS-SUP) の assembly 検分と並行提示 (検分結果は追報)。

**用語 (初出定義):** HOLD = policy 逸脱時に台本の進行時計を止める安全機構 / div_grip = 把持中 cable 節の記録軌道からの乖離 [mm] / Δ-bound = policy 補正 offset の 1 step 上限 / OG = GPU 不要の忘却警報計器 / DR = 環境条件の意図的ばらつき / bank v2 = phase 途中から episode を開始するための状態保存・復元 / R2b = 「凍結台本 + 小さな補正 policy」方式の第 1 訓練 campaign / n=1 = 実測 1 run 由来 (検証 leg で拡張予定の意)。

---

## §1. 方向性の確認 (confirm / veto) — 7 項

「はい/いいえ」で答えられる形にしています。**全て推奨 = confirm** (根拠付き)。veto の場合、影響範囲を各行に記載。

| # | 決定 | 内容 (1 行) | 推奨 + 根拠 | veto 時の影響 |
|---|---|---|---|---|
| 1-1 | **D-A** mini-test (模倣の A-vs-B 論争 close) | 再開 (timebox ≤2 日) か skip 宣言か — critical path を gate しない epistemic close | **どちらでも可 (等価)** — devplan §8: 再開は将来の模倣論争の残債を消す・skip は安い | なし (独立) |
| 1-2 | **D-B** env-build 着手 trigger | design-gate 成果物 PASS を trigger とする — **今回充足済み** | **confirm** (evidence-gated、devplan §8) | W1 停止 |
| 1-3 | **D-C** 訓練方式 | R2b = **RLPD residual-on-script を primary** (07-12 に委任 co-decide 済み、veto point = 今ここ)。R2a (PPO+BC) は条件付き予備 | **confirm** — FORK-1 (開ループ発散) の fix は閉ループ補正のみ (静的 fix 全 REFUTED)、devplan D-C 推奨と一致 | trainer node の algo 前提が崩れ、代替 = DQ7 banked の保守案 (canonical DAPG) に差戻し |
| 1-4 | **D-D** R4 (「超える」軸) | R3 の証拠が出るまで defer | **confirm** (devplan §8 のまま) | なし |
| 1-5 | **HOLD 設計** | cable 実測乖離 (div_grip) で台本時計を停止、**把持成立 (G1) 後にのみ作動**、resume に hysteresis | **confirm** — EE 基準は本基板で原理的に発火不能 (pre-check CRIT-3)、nominal 再生自体が発散する実測 (FORK-1) と整合する唯一の意味論 | Stage-A spec §4 全面再設計 |
| 1-6 | **tail 規則 (iv)** | 台本の意図的 release 後は「drop 失敗」判定を無効化 (release 後の落下は category error + 「粘るほど損」の逆 incentive を排除) | **confirm** (5体 N6、算術検証済み) | 報酬の逆転 incentive が残存 |
| 1-7 | **OG 計器の作り直し** | 旧 3-leg は residual 方式で縮退 → **A′ (経路上 ‖Δ‖ 監視) / B′ (corner での cable 感度) / C′ (null-beat)** に再設計 + 適用は nominal cell 限定 | **confirm** (縮退は数理的に確定、5体 MED-8) | OG が偽 GO を出す計器のまま |

## §2. 数値の確定 — 提案値一覧

**全て現状 PROVISIONAL (仮値)。** 承認 = 「この値で W1 build + smoke に進み、smoke 実測で再導出されるものはその値が governs」。太字 = 実測由来、無印 = 提案値。

### 2a. Stage-A 新規機構 (spec v0.8 §2/§4)

| param | 提案 | 根拠 (provenance) |
|---|---|---|
| HOLD 発火閾値 | **15mm** | 健全域実測 max 10.56mm と発散 onset の間 (n=1 canonical)。閾値∈(10.6,15] は同一 ramp を ≤6 step 差で検出 = 選択影響小。§8 legs で複数 cell/seed 再計測 |
| HOLD resume | ≤**12mm** or 3 step 連続 in-band | hysteresis 3mm > seg 乗換え鋸歯 2.84mm (n=1) — 発火/解除の chattering 排除 |
| MAX_HOLD | 24 step (**未実測** placeholder) | smoke の hold-fires leg で回復時間分布から導出し直し |
| Δ-bound (補正上限) | **20mm** (`DELTA_BOUND_M=0.020` 現行値の正式授権) | 必要量 = 実測 drift max **1.94mm/RL-step** ≪ 20mm (余裕 ~10×)。⚠ERRATUM-3: 従来の「±22mm 授権」は別機構の precedent であり授権でない → **本項が正式授権の場** |
| DR 範囲 | cable XY ±20mm、**既定 OFF** (campaign で ON) | devplan §6-6。corner での div 漏れは §8 leg が実測 (falsifier 付き) |
| curriculum 開始 mix | {P0, G1−ε…G5−ε} 集合のみ確定、**比率は smoke 後に再提示** | bank v2 は canonical cell 固定 → **phase 途中開始は DR ゼロ** (構造制約、LOUD 宣言済み) |
| DR×curriculum 緩和 option | P3 収録に multi-cell bank capture を相乗り (+1 cost 行) — **採否** | 採 = phase 開始にも DR 被覆 / 否 = P0 開始のみが DR 経路 (campaign 設計に明記) |

### 2b. campaign 判定 bar (devplan §4.3 draft の確定 — Stage C で効く値、今すぐは使われない)

| param | draft 提案 | 備考 |
|---|---|---|
| R2b PASS bar | DR±20mm in-sim category-SUCCESS **≥70%** (N≥30、band 分離) ∧ script-under-DR baseline を band 超え | devplan draft は illustrative 明記 — **Rs 確定が campaign GO の前提** |
| abort 規則 | post_base_drop >0.20 が 2 連続 eval OR OG restoring legs 3 checkpoint 連続悪化 | de-risk window=3 実績準拠 |
| actor-gate (R3) | Q_rank_error <0.10 | R3 段まで不使用 |
| OG band α/β/γ | **提案なし (open)** — legs A′B′C′ の bar は port + null 再生成後の実測で提示 | 旧 band は再較正前提 (0.667<0.8 問題) |
| P4 pre-reg (訓練 hyper) | γ=0.997 / GAE λ=0.95 / envs×steps = smoke 実測で確定 / corner-episodes ≥8/update | v1.5h §9-3 提案値のまま |

### 2c. 現 disposition の維持 confirm (変更なし、一括で可)

draw 方針 (DR-support 除外推奨) / Q7 arm-arm collision / HIGH4 ori 節なし (復活条件付き) / R-side div leg 不採用 (nearest_seg_r は遷移で不適) / α-DR 学習信号 option (P3 実測 = decider) — いずれも v1.5h/spec v0.8 の banked disposition のまま。

## §3. 正直な限界 (承認前に知っておくべきこと)

1. **n=1**: HOLD 閾値系の実測は canonical cell 1 run 由来。§8 smoke legs (複数 cell/seed) が拡張するまで仮値。
2. **falsifiable claims 登録済み** (反証されたら設計へ戻る): ①「時計停止で drift の駆動が消える」②「C1 座りは HOLD を跨いで持続」③「policy は HOLD 状態を直接観測せずとも脱出を学べる」— 全て §8 に反証 leg あり。
3. **未訓練 policy は HOLD で停滞 → timeout が期待挙動** (nominal 自体が発散する基板のため)。学習進捗は HOLD-resume 率で観測。
4. **実機非保守**: HOLD は sim 固有機構 (実機の base controller に同等物が要る)。sim2real 面は従来 carry のまま。
5. ERRATUM 3 件 (単位 / 統計窓 / F-1a) は p1 が独立再計算で全て実証確認済み (script v3 `b55bc43d07`)。

## §4. 同梱 evidence (全て commit 済み pointer)

| 種別 | 所在 |
|---|---|
| 設計 spec v0.8 (全 gate PASS) | `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` (d17f8f9cd6 + e8d53aae10) |
| reward 4 成果物 v3.3 | `STAGEA_REWARD_ARTIFACTS_20260712.md` |
| charter + ERRATUM 1-3 | `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md` |
| %9 検証台帳 (9-lens + ERRATUM 実証 + script v3 + §0b) | `STAGEA_DESIGNGATE_CROSSPV_PCT9.md` |
| %11 検証台帳 (builder 6-corrections) | `STAGEA_CROSSPV_COORD_20260712.md` (fb9000b476) |
| 5体 debate 記録 (cycle 1 FAIL → cycle 2 PASS) | `harness-vault/verification-log/verification-log.jsonl` task_id `stageA-designgate-5tai-20260712` |
| 層5 3 視点 PASS + 一次データ | node state.md 13:04 entry + `comp5_c2seat_fullfire_cablediag.npz` (311f18cb9b) |
| 計画 surface | LEDGER stageA row + map (9f26bd19a3、p6) |

## §5. 承認の形式 (お好みで)

- **A) 一括承認**: 「§1 全 confirm + §2 提案値で進め」 → W1 build charter 起草に入ります (staged ≤800 行/diff、L3 chain 毎)
- **B) 項目別**: 番号指定で veto/修正 (例: 「2a の DR×curriculum 緩和は否」)
- **C) 質疑**: 不明点はどの行でも — 各値の導出は spec v0.8 の該当 § に 1:1 対応しています

いずれの場合も **node COMPLETE 宣言は本 review の結果と同時に行います** (数値 harden 前に COMPLETE にしない — 5体 NHA 条件)。

---

## 決定記録 (decision-of-record)

**Rs verbatim「A」(2026-07-12 13:29 JST) = 一括承認**: §1 全 7 項 confirm + §2 提案値採択 (smoke 再導出条項付きの値はその条項ごと有効)。
- D-A (1-1) は「どちらでも可 (等価)」の disposition のまま承認 → **運用 default = close 宣言 (A-vs-B OPEN を log に残す)**。再開希望が生じた場合は別 node で (この解釈は %12 判断・autonomy grant 内、veto 可)。
- 帰結: **W1 (env build) 着手可**。campaign は不変で HIGH-COST + production-launch + fresh Rs GO 背後。
- pending leg: p1 assembly 検分 (提示と並行) — CORRECTIONS が出た場合は該当項のみ Rs へ loud に再提示。

*%12 — 2026-07-12。本 packet = 転記 + 提案のみ、新規設計判断なし。INVARIANTS/task_config 不触。*
