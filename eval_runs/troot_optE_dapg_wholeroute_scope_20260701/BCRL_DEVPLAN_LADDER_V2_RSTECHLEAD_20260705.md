# THREAD BC+RL 開発全体像・開発計画 (LADDER v2) — PROPOSAL (v1.1, 5体 debate 反映済)

**Author:** RS-TECH-LEAD (%12 / w2:p4, fable5 deep-dive per Rs 委任). **Date:** 2026-07-05 08:49 JST (v1.0 08:3x → 5体 debate 08:2x-08:4x → v1.1 全 ACCEPT 修正反映).
**Status:** PROPOSAL ONLY — 0-commit / no build / no rollout / INVARIANTS 不触。RL env・reward・DR range・decision = **Rs 専権**。本 doc は skeleton (`scratchpad/fable5_bcrl_staged_ladder_handoff.txt`, 07-04 20:26) を吸収・supersede する deep 版。
**初期情報:** Rs 提供 ChatGPT Pro deep-dive ×3 (①BC/RL 勾配干渉 ②BC後RL崩壊/unlearning ③VLA接続)。**独自調査:** `thread-vault/06-Knowledge/KN-BCRL-Frontier-2026-07.md` (web-research skill, 17 検索/fetch, ~60+ 一次ソース; **方法論 fact の source of record = KN**、本 doc は pointer-summary + THREAD 接合のみ)。

**[L-TRIAGE RESULT] (本 doc 自体):** 自動昇格照合 = §0 keyword (reward/success/ik/phase 等) が新規 file diff に多数 hit + 244 行 >200 → 機械適用なら L3。**降格申告 (false-positive):** 本 doc = eval_runs/ 内 proposal 文書、コード・config・挙動 surface ゼロ — keyword 規則の対象は挙動を持つ diff であり、skill Step 6 例示「言及のみ → 関連薄」に該当。**final_L = L2 (自己申告) — Rs が W0-a review で降格を confirm すること。confirm されない場合は L3 追加 gate (層5 + §運用15 層2 事後 debate) を実施する。** L2 gate = 5体 pre-debate 実施済 (2026-07-05 08:2x-08:4x、ADDENDUM に記録)。

---

## §0. GROUNDING (anchor set, §運用4 — read + cited)

| Anchor | Cite | 使用した fact |
|---|---|---|
| LEDGER row43 | `00-DESIGN-STATUS-LEDGER.md:43` | C1→C2 square-on route = 🟢 WORKING Rs-confirmed、COMMITTED `bcb7393ec8` = demo SEED。**⚠ R re-grasp reach margin 0.9mm** (row43) = P1 carried reach-fragility |
| LEDGER row42 | `:42` | RL-Routing ⚠MIXED; **5-skill chain product P0-KILL'd** (SR乗算) |
| LEDGER row56 | `:56` (v1.0 の「row54」cite は行 shift 誤り — :54 = GD-KoShape row) | **AR mujoco-コ: single-L aerial-hold NOT durable → NEEDS-DUAL、FUNDAMENTAL** (「retain-vs-load」は scoping doc の言い換え framing `DAPG_WHOLEROUTE:15`) — 未解決 carried risk |
| **DQ1 = B (Rs 決定)** | node `state.md:38-39` + `P2_REWARD_DESIGN.md:7` | **UNIT 選択 = B (BC-imitation)、Rs verbatim「B」2026-07-02。residual-A 設計は PARKED (not killed) —「revisit iff A is later selected」**。P2 pre-check BLOCK (10 issues) は **arch A の reward 設計に対して**発行された。→ 本 plan の R2b 推奨 = **PARKED-A の un-park 提案** (§8 D-C; 復帰条件 = Rs 07-04 19:53 redirect「BC+RL 再検討」で成立と解するが、**un-park 採択は Rs 決定 + 同 turn supersession banking 必須**) |
| RS71 §0 | `RS71-System-Spec-SSOT.md:19-27` | INVARIANTS #1-5 (dual-arm / 88mm span / DiffIK-only / コ LOCK / no-kinematic-trick) |
| RS71 §4 | `RS71-System-Spec-SSOT.md:53-54` | **fidelity boundary: horizontal routing curvature = KINEMATIC** — RL は sim に無い物理を学べない |
| Env scoping | `DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2.md` §1-§5 | whole-route env **ABSENT** (:35); arch A 推奨 (:54-58; ⚠ DQ1=B で PARKED — 上記); P1-P4 費用 (:80-88); obs 42D+phase+clip-idx (:66); action 12D EE-delta+auto-close (:68); horizon>200 問題 (:68); DAPG infra EXISTS `train_common.py` (:32); Grip VBD-residue flag (:39) |
| Off-path scoping | `DQ7_OFFPATH_SCOPING_COORD2.md` §1/§3/§4/§6 | **2 failing legs — leg 1 だけ直しても GO 不能** (:34); restoring anatomy Fact A/B (:57-61); **expert は frozen-waypoint phase で state-blind** (:106); options (i)-(iv) 表 (:89-98); (i) 再 scope 先 = **B2 27D/6D contract の canonical DAPG** (:102); **P2 residual contract = 49D/12D** (:102 — 42D/12D は AC/AR env 実装。**contract は 3 系統在る**); staged 推奨 (:130-139); leg-2 teacher D-4 = adj-A + (iv) seg-co-move「both — cross-validate」(:146) |
| R0 実測 | `b2_cpE_og/bc/og_gate.json` (via DQ7 §0:16) | movable γ⊥ 2.497/1.257/1.041/1.055 all-STOP / seg-follow 0.282 / ee-only 0.973 / null-beat −0.261 |
| R0 on-path | `b2_cpD_report.md:14` | BC on-path 汎化 18× |
| B1 bank | node `state.md:35` | relative-delta open-loop BC = 0/5、5/5 REACH_WALL (**apply-path の delta 積分**で drift 蓄積→span 122.9≠88→grip 0N) = conservative-definite FAIL |
| R1 (ii) 実測 | node `state.md` 2026-07-04 15:09 | BC-(ii) = γ⊥ {0}2.497→**1.744** / {1}1.257→**1.056** (banked og anchor 07-04 01:53) — **動くが STOP 帯で plateau** |
| R1 capacity | commits `825b986390`/`94c0c4620e` | capacity pre-test **PASS** — plateau = data-correlation (copycat)、representation-attractor ではない |
| R1 DAgger de-risk | node `state.md` 2026-07-04 17:48 | β=0 single-offset minimal = **monotone-DIVERGENCE** / budget-not-fatal EXCLUDED / **A-vs-B OPEN**; β=0 = degenerate |
| mini-test 状態 | node `state.md:140-142` (2026-07-04 19:33/19:53) | resolver = β-mix + multi-offset {−20,+10}、~1-3 GPU-h。**β-mix = CODE ADDITION → L-TRIAGE 要 (L2-L3)、fire-前 gate = [DEFINE]→[L-TRIAGE]→[VERIFY]→[RULE-CHECK]→--rs-go+%12 verify+%9 metric+Rs loud-notify が全て PENDING、decision rule = draft (%9 verify 中)**。現況 HOLD (Rs redirect 19:53) |
| OG gate band | `dq7_ii_mini_spec.md:69` | ⚠ seg-follow faithful-pair ceiling ≈**0.667 < band-lo 0.8** → band 再較正 (α/β/γ) = **open Rs 決定項** |
| DAgger v2 DECIDE | commit `170b905575` | **oracle 照会 ≠ waypoint lookup**: per-step relabel + per-episode settle re-centering + in-scene IK が必要 (v1「thin-const-relabel」= 偽、debate FAIL C1) |
| 調査 | `06-Knowledge/KN-BCRL-Frontier-2026-07.md` | 手法検証+2025-26 SOTA (§3) |

---

## §1. Rs directive (verbatim) と goal chain

> 「段階的に精度、難易度をあげていきたい。はじめは基本的なもので行いどの程度実現するかを見極め、問題点を洗い出し、それらに対応するにはどうしたらよいかを考え、最終的に最新のアルゴリズムに並ぶまたは超えるものをつくりたい」(07-04)
> 「BC+RLによる開発全体像、開発計画を立てたい。…独自に情報調査して、それらに基づき THREAD における BC+RL の開発全体像、開発計画を立てよ」(07-05 本 session message — 記録は本 doc が一次。Rs は W0-a review で本引用を confirm)

**Goal chain:** T-ROOT「5-clip cable routing を vision-based で 95%」→ T-L1C-PerSkill-RL → 本 node「whole C1→C2 route を 1 学習 unit として」(Rs 07-01「(A) 経路全体」)。**framing (Rs-caught 訂正済):** 当初計画 = **DAPG = BC+RL** — BC は放棄しない。

---

## §2. 現在地 — 実測に基づく評価 (facts only)

| Rung | 状態 | 実測 (cite = §0) |
|---|---|---|
| **R0 pure BC** | ✅ DONE = 問題の定義 | on-path 18× / off-path γ⊥ 1.0-2.5 all-STOP / null-beat −0.261 = **copycat** |
| **R1 imitation+off-path 教師** | 🟡 部分完了・**verdict 未 close** | (ii): γ⊥ ~30% 改善するが bar 0.5 の 2-3.5 倍で plateau。capacity PASS。DAgger β=0 = monotone-DIVERGENCE、**A-vs-B OPEN**。resolver mini-test = 設計 draft 段階 (**fire-前 gate 全て PENDING**、§0) で HOLD |
| **R2+ (RL leg)** | ⛔ 未着手 | whole-route RL env ABSENT = 最大律速。P1 feasibility PASS non-cons (4 carried risks) |

**R1 の含意 (機構解釈、推測ラベル):** scripted expert = 「強い EE-restoring proposer / 弱い cable-state teacher」(EE-restoring は全 phase = Fact A、cable-state 再導出は 2 点のみ = Fact B; **frozen-waypoint phase では state-blind** DQ7:106)。(a) off-path 供給を増やしても γ⊥ plateau、(b) DAgger loop 発散 (β=0 confound 未 resolve) — の 2 つが「imitation-only では GO bar に届かない公算」を示すが、A-vs-B open のため R1 の正式 close は mini-test (または Rs による close 宣言) に委ねるのが誠実。

---

## §3. 初期情報 (ChatGPT Pro) の検証結果 + 独自調査の追加発見

### 3.1 検証 verdict (source of record = KN doc; 本表は pointer + THREAD 接合)

| 初期情報の主張 | verdict | 補正・詳細 |
|---|---|---|
| IN-RIL: 周期 IL 注入 + gradient separation、Transport 12%→88% | ✅ VERIFIED | arXiv:2505.10442。**preprint (査読未確認)**・sim 中心。R2 arm には**採用しない** (再現実装コスト + preprint risk、KN:48) — interleave 概念のみ R2/R3 の BC 更新方式として利用 |
| Cal-QL: Q 校正で dip 防止 | ✅ VERIFIED | NeurIPS 2023。**前提 = offline-RL (TD) pretrain path** — 本 plan の既定経路では不使用、pretrain 採用時のみ (§5-R3) |
| OLLIE: discriminator 整合初期化 | ✅ VERIFIED | ICML 2024。THREAD 適合低 (sim 内 reward 定義可) |
| IBRL: 凍結 IL policy 提案 + Q 選択 | ✅ VERIFIED | TD3 backbone; actor-proposal + bootstrap-proposal (**Q point-estimate の argmax** — uncertainty gate とは別物)。**前例の正確な範囲: Meta-World = scripted demos で訓練した IL policy を提案に使った** (KN:35) — **script-oracle を直接提案にするのは未検証の THREAD 変形** (§5-R3 で caveat 込み設計)。実機 deformable 布 Hang 85% / RLPD 比 6.4× |
| RLPD: 50/50 replay + LayerNorm ensemble critic + 高 UTD | ✅ VERIFIED | ICML 2023。**offline pretrain なしで最初から online が設計点** — 本 plan の R3 既定 |
| 勾配干渉: 測定→交互→分離→(残りだけ) surgery | ✅ 文献整合 | THREAD 補正: 低次元 state obs → encoder-drift 系は現 phase N/A (vision phase で復活) |
| unlearning: policy だけ初期化しない / post-BC-drop KPI / rollback | ✅ 文献整合 | **⚠ 機構限定 (debate CC2-1 反映):** 我々の de-risk monotone-DIVERGENCE は **critic 無しの模倣 loop** で起きた — offline→online *RL* unlearning (Q 較正問題) とは機構が別。正しい文献 anchor = DAgger の β-schedule 論 (Ross et al. 2011)、resolver = mini-test。**Q 較正系対策 (Cal-QL/WSRL/Q_rank 監視) が意味を持つのは critic が存在する R2+ から** |
| RECAP/π*0.6: throughput 2×、failure 半減 | ✅ VERIFIED | arXiv:2511.14759。分布型 value + advantage-conditioning token + AWR 系。**5B VLA + 大 infra 前提 → R4 発想源** |
| RL Token: 凍結 VLA + 小型 RL head が action 編集 | ✅ VERIFIED (機構・task・3×・実機データ 15 分〜) | arXiv:2604.23073。zip-tie/Ethernet/charger = ケーブル系精密実タスク、改善サイクル ~2h。**⚠「ねじ 20%→65%」の数値は KN で確認できず = 未検証 (ChatGPT 由来)** — 採用判断に使わない |
| 「DAPG = Residual-PPO+BC」 | ⚠ **命名補正** | canonical DAPG (RSS 2018) = BC 正則化 on-policy PG (**decay→0**)。residual 系譜 = ResiP (arXiv:2407.16677) + Residual Off-Policy (arXiv:2509.19301)。**on-disk 注意: `train_common.py` の α は 0.7→0.5 床への線形 anneal (`:49,:91,:166-171`) で decay→0 でない (床 0.5 = VBD-track historical)** — R2a を canonical に寄せるなら α→0 schedule 追加が必要 (§5-R2) |

### 3.2 独自調査の追加発見

1. **WSRL** (ICLR 2025, arXiv:2412.07762): **offline-RL pretrain 済み Q を warmup rollouts で online 分布に再較正**する手法 (offline データ保持不要)。**⚠ 適用前提 = 「再較正すべき pretrained Q が在る」こと** — pretrain 無し + demos は RLPD の設計点。→ 位置づけ: R2→R3 で **actor/critic weight を warm-start する場合のみ**の条件付き部品 (§5-R3; 既定は weight 非転送 = WSRL 不使用)。
2. **Three Regimes** (arXiv:2510.01460): π0 と D の優劣で保持対象を選ぶ taxonomy — THREAD script demos 高品質 → policy-superior regime → **π0 (script/BC) 保持側**の手法が整合 (凍結 base 路線の独立支持)。
3. **Q-chunking** (NeurIPS 2025, arXiv:2507.07969): chunked action 空間の TD — long-horizon sparse の credit assignment。**R3 内 horizon-mitigation arm 候補** (R4 送りにしない — KN:111/116 は「whole-route 適用には追加設計が必要」を文献の一致点とする)。
4. **JSRL 系 roll-in curriculum** (Uchendu et al., arXiv:2204.02372) + **demo-state reset curriculum** (Nair et al. 2018; Salimans & Chen 2018): guide-policy/デモ状態から後ろ向きに開始分布を広げる horizon killer。**sim-native (full state 制御 + queryable script) で「経路全体 1 unit」の premise を崩さない** (policy は 1 つ、開始分布だけ変える)。⚠ KN 未収載 → KN 追補対象 (一次確認の上)。
5. **HIL-SERL** (Science Robotics 2025): 実機 1-2.5h 近完全、dual-arm 協調含む — real phase / Rs「言葉で教示」との長期整合。
6. **Gap 確認:** dual-arm whole-route cable-clip routing の demo-augmented RL 公開事例 = **ゼロ**。文献の勝ち筋 = stage 分解 + 局所 RL + 高位 recovery — 「経路全体 1 unit」directive との緊張は §8 D-D (premise 変更は提案しない; 上記 4 が directive 内の代替)。

---

## §4. 開発全体像 (the big picture)

### 4.1 through-line (全 rung 共通の設計原理)

**「信頼済み凍結 base + 小さな学習部品 + 参照 anchor 付き探索 + 較正済み critic + gate された更新」** — base を script → BC → (将来) vision/VLA と swap しながら同一原理でスケールする。深掘り①②の処方は「L_RL+λL_BC 同時 backward」を避け構造分離 (base/residual or 凍結 proposal、交互更新) を本命とする — 本 plan は R2 から構造分離を**推奨する** (既定化は D-C の Rs 承認後)。勾配 surgery 級の複雑さは「共有 trunk を選んだ場合のみ」に限定。

```
                    [γ data engine]                       [β env & instruments]
 demos (P3, DR±20mm) ─┐                                   whole-route env (P2)
 (ii) kick-recover  ──┼→ replay {demo / online-succ /     ├ script-oracle query API (§6-1 ⚠設計重量級)
 adj-A + (iv)seg-co-move┘        online-fail 分離}        ├ off-policy-ready (transition export)
                                                          ├ phase predicates / seat・pin events
        ┌─────────────────────────────┐                   ├ og §3.3 offline gate (要 port+再検証 §4.3)
 obs →  │ frozen BASE (script route)  │→ base action ┐    └ nomA/nomB band (#562)
        └─────────────────────────────┘              ├→ 合成 (Q-gate は R3) → DiffIK → sim
        ┌─────────────────────────────┐              │      (span-guard / time_outs 純度)
 obs →  │ small policy (residual Δ /  │→ Δ or 提案 ──┘
        │  abs-target) + critic       │   ↑ anchor: ‖Δ‖ bound (非累積 §6-9) + BC 交互更新
        └─────────────────────────────┘   ↑ gate: post_drop / Q_rank_error / rollback
```

### 4.2 4 stream 構造

| stream | 中身 | 状態 |
|---|---|---|
| **α policy ladder** | R0→R4 (§5) | R0 済 / R1 close 待ち |
| **β env & instruments** | P2 env + oracle API + off-policy-ready + **OG port/再検証** + band 法 | env ABSENT = 律速 |
| **γ data engine** | P3 demo-set (DR + **script-SR-over-DR-grid 検収**)、(ii) recordings、**leg-2 teacher (adj-A + (iv) seg-co-move、DQ7 D-4)**、replay 3-buffer | recorder/converter/trainer 済 |
| **δ vision/VLA (将来)** | state teacher → vision student 蒸留 or VLA-base+residual (RL Token 型) | 現 phase 対象外。I/F の base-swap 可能性のみ担保 |

### 4.3 共通 yardstick — 計器の妥当性境界を明示 (debate CC3-4/6 反映)

- **OG §3.3 3 legs** (①movable γ⊥≤0.5 + ee-only≤0.3 ②seg-follow∈[0.8,1.2] ③null-beat≥0.15)。**適用限界 3 点:**
  (a) **contract-bound:** 「2× validated」は 27D obs/6D abs-target 契約上の実績。**schema 統一 (§6-3) は検証状態を RESET する** → β stream に「OG port + 再検証」work item (それまで canary 主張は abs-target head にのみ適用)。
  (b) **composite 縮退:** R2b の測定対象 = base(t)+Δ(obs) — Δ→0 で γ⊥≈0 = restoring legs が**偽 GO 方向に縮退** (canary が residual 崩壊に盲目)。composite 用の γ⊥/seg-follow 導出 = 上記 work item に含める。
  (c) **band 再較正** (seg-follow ceiling 0.667 < 0.8) = open Rs 項 — **W0 に前出し**。
- **per-rung 適用宣言:** R1 (abs-target BC) = 3 legs 全適用 / R2a = port 後 3 legs / R2b = leg①③ は composite 導出後、**leg② は構造的に composite で成立しない → 代替 metric (例: Δ の cable-obs 感度) を design-gate で Rs 決定** / R3 = R2 と同じ。
- **拡張指標 (R2+ で critic が存在してから意味を持つ):** post_base_drop / post_BC_drop / Q_rank_error (fail-set は **契約統一後に再変換した** B1+budget-test rollouts) / action_drift_to_base / (共有 trunk 時のみ) 層別 grad-cos。
- **eval 規律:** #562 → nomA/nomB re-sim band + N≥30 + §運用14 video-first + %12+%9 joint verdict。
- **数値閾値 (draft 提案値 — W0-a で Rs 確定、確定まで HIGH-COST-GATE は GO を出さない):** abort = post_base_drop >0.20 が 2 連続 eval OR OG restoring legs が 3 checkpoint 連続 monotone 悪化 (de-risk の window=3 実績準拠) / actor-gate (R3) = Q_rank_error <0.10 / R2b PASS bar = DR±20mm in-sim category-SUCCESS ≥70% (N≥30、band 分離) かつ script-under-DR baseline を band 超えで上回る。

---

## §5. LADDER v2 — per-rung deep 設計

### R0 — pure BC (済 = 問題の定義)
実測 §2。**拘束 (banked):** fork-(iv) absolute-target repr ADOPTED — 「絶対 anchor を失う action 表現は不採用」。residual の適合条件は §6-9 (非累積契約) — B1 の drift は **apply-path の delta 積分**が機構であり、residual が安全なのは「base の絶対 target への per-step offset (非累積)」と契約で固定した場合**のみ** (既存 12D EE-delta は accumulates into IK target `newton_approach_cable_mujoco_env.py:40` — そのまま流用すると B1 機構が policy channel 内で再現する)。

### R1 — imitation + off-path 教師 (close 手順が残る)
- **残作業 = mini-test (A-vs-B resolver)。状態を正確に:** 設計 = draft (decision rule %9 verify 中)、**fire-前 gate = [L-TRIAGE β-mix (CODE ADDITION、L2-L3)]→[VERIFY 5体]→[RULE-CHECK]→--rs-go + %12 verify + %9 metric + Rs loud-notify が全て未完** (state.md:140-142)。再開 = これら gate の完走が前提 — 「Rs 判断のみ」ではない。
- **価値の正直な定義 (debate CC4-5 反映):** D-B が env 建設を mini-test 結果から独立させたため、**critical path 上の決定は gate しない — 価値は A-vs-B open verdict の epistemic close** (放置すると将来の全 imitation 論争に remnant として再燃する)。β-mix **code** は B2 契約 (27D/6D) 束縛で P2 契約に非可搬 — 「R3 資産」は **concept precedent に降格**。
- **timebox 提案:** 再開する場合 ≤2 wall-days。超過時は「plateau + A-vs-B OPEN (logged)」として R1 を close し先へ進む。**skip (close 宣言) は等価な選択肢** — D-A で Rs が選ぶ。
- **leg-2 (γ stream):** adj-A 密度化 + (iv) seg-co-move (DQ7 D-4「both — cross-validate」) を P3 batch に同梱 (~0 marginal build)。

### R2 — 基本 BC+RL (env の崖を渡る最初の rung)
**命名補正済:「demo-anchored RL 第 1 実装」。両 arm とも §6-3 統一 schema に bind** (v1.0 の 27D/6D vs 42D/12D 混在は解消 — 契約統一が先)。
- **R2a = PPO+BC-aux (DAPG-style):** demo BC 補助 loss。**canonical 化には α→0 decay schedule を追加** (現行 `train_common.py` は床 0.5 = VBD historical — copycat を構造温存するため、そのままでは R2b との比較が foregone conclusion になる)。α は {→0, →0.5} の dual-schedule も可 (BC 維持自体を test したい場合)。
- **R2b = ResiP 型 residual-on-script (D-C の un-park 提案):** 凍結 base = committed route、policy = **非累積** per-step offset (§6-9) + auto-close。BC 項 = Δ≈0 anchor — **⚠ これは文献 recipe でなく THREAD 追加であり、実体は Δ の L2 penalty と等価 (residual の demo label は構成上 Δ≡0)** — P3 demos の実消費者は R2a の BC 項 / R3 replay / eval。
- **P2-BLOCK 10 issues との照合 (un-park の代償を明示; CC3-1):** CRIT2 (demos absent) = 解消済 (recorder + B2 demos) / HIGH5 (rot dims inert) = 12D 採用なら**再輸入** (6D pos-only 統一が代替 — design-gate Q) / MED10 (gripper ch) = auto-close で moot / **CRIT1 (phase-advance fork: script-schedule vs agent-earned) = residual 構成で再輸入 — §6-10 の設計必須項** (base が time-indexed のまま進む間に Δ が cable 状態を変える desync が B1 とは別系統の失敗モード)。
- **horizon:** >200 steps → episode 長 or **demo-state reset curriculum (§3.2-4: 開始分布だけ変える sim-native horizon killer、premise 不触)** — design-gate 項。sparse の phase-completion predicates は暗黙の ~16 段 credit assignment 分解として機能する、という主張を **falsifiable claim として登録** (学習が全く進まない = 反証 → curriculum/shaping へ)。
- **reward sketch (design-gate INPUT; 決定 = Rs):** sparse 主体 — phase-completion predicates + 終端 category-SUCCESS + 微小 time penalty + span-guard (88mm 逸脱 = invalid 終了)。dense distance shaping 初期不採用 (HIGH3 anti-hover 教訓)。§運用21 (reward が読む状態は obs に) / §運用22 (penalty:reward ≤5:1 検算) / time_outs 純度。
- **比較の正直な位置づけ:** R2a vs R2b は obs/action/anchor 種が異なる **system-level A/B** (clean ablation ではない)。**R2a は contingent-only (CC4-6): R2b が §4.3 bar に不合格 AND 診断が residual 構造 (Δ-bound 飽和 / base-fighting signature) を指す場合のみ起動** — でなければ campaign 予算 ~半減。
- **eval/gate:** §4.3。abort/PASS bar = §4.3 draft 値 (Rs 確定必須)。GPU 10h+ 級 → HIGH-COST-GATE + production-launch-gate + Rs GO。

### R3 — SOTA 並走 (off-policy demo-anchored stack) — **新規 trainer BUILD (差し替えではない)**
- **on-disk 事実 (CC4-2):** SAC/TD3/replay/ensemble-critic infra = repo に **ゼロ** (`train_common.py` = PPO+BC 615 LOC のみ) → R3 = **新規 build ~500-800 LOC + 自前の L3/debate/HIGH-COST gate 負荷** (= 第 2 の cost cliff、§7 に独立行)。env/replay/oracle API は P2 と共有。
- **構成 (検証済み部品の合成):**
  1. **RLPD 機構 (既定):** SAC + symmetric 50/50 replay (demo/online) + critic LayerNorm + ensemble + 高 UTD — **no-pretrain + demos の検証済み設計点** (warmup 較正は不要)。Cal-QL = offline-RL pretrain 採用時のみ / WSRL = R2b→R3 で actor/critic weight を warm-start する場合のみ (**既定 = weight 非転送** → 両方不使用)。
  2. **提案機構 (IBRL 型、caveat 込み):** 凍結 proposal 候補 = (a) script-oracle (⚠ **未検証 THREAD 変形**; oracle は EE-restoring 有効 / **cable-state blind** DQ7:106; 照会は waypoint lookup でなく per-step relabel+settle re-center+in-scene IK 級 = §0 DAgger v2 DECIDE) / (b) **fallback arm = BC(R1-data) policy を提案に** (= IBRL の検証済み形)。実行時 {proposal, RL 案} を **Q point-estimate argmax** で選択。**t-indexing 問題 (CC2-2): obs に within-phase progress scalar を追加 (§6-2) しないと oracle 照会も TD も hidden-time 依存で非 Markov 化** — §6 必須要件に昇格。
  3. **R3 actor 形態 = abs-target head (統一 schema 上) を既定** (OG canary の契約適合 + IBRL の非拘束 actor 前提と整合)。residual 形態は R2b の lane に留める。**expressiveness ceiling risk (Δ-bound / 提案近接) の緩和 = reference-action dropout (RL Token 検証済み機構) を pre-register**。
  4. **horizon-mitigation arm を R3 内に pre-register (CC2-4):** {Q-chunking / JSRL 型 script roll-in / demo-state reset curriculum} から ≥1 を R3 設計時に選定 — 「単段 whole-route で 10-100K step 級手法をそのまま」は文献一致点に反する。
  5. **unlearning/干渉 instrumentation:** §4.3 拡張指標 + actor-update gate + best_safe_checkpoint rollback + BC 交互更新 (常時加算しない)。

### R4 — 超える (EXPLORATION ラベル — 全て推測)
候補 (優先順は R3 証拠で — D-D): (a) OG-gate curriculum/shaping 転用 (⚠ teach-to-the-test → held-out 方向 + physics eval m1-m4) / (b) queryable expert 活用 (oracle-guided exploration / RECAP 型 advantage-conditioning) / (c) 摂動 curriculum ((ii) 注入機構の訓練時 DR 化) / (d) stage 分解 + 高位 recovery — **premise 変更になり得るため提案時 STOP-and-flag** / (e) HIL (real phase、scope 外記録のみ)。

### δ — vision/VLA 転換 (現 scope 外、前方互換のみ)
(1) obs-schema 抽象で置換点を 1 箇所に (2) R3 の凍結-base+小-head+anchor 構造は RL Token と同型 → 将来 VLA-base に置換可能 (3) 既定経路 = state teacher → vision student 蒸留。今 VLA を導入しない理由: sim-only + 低次元 obs + 単一 task family で 5B 級は cost/benefit 不成立。

---

## §6. β stream — P2 env 要求仕様 (design-gate への INPUT; 決定 = Rs)

**中核推奨:「off-policy-ready + oracle-ready」で一度だけ建てる** (env は共有資産。trainer は R2/R3 で別 build):
1. **script-oracle query API — ⚠ 重量級の設計対象 (bullet ではない; CC3-3/CC4-1):** 意味論を design-gate 成果物で確定 — mid-servo (interp loop 中) の返り値 / **phase-clock の所有者 (policy 逸脱時に t を誰が進めるか = CRIT1 fork)** / state-blind phase の扱い / 照会実体 = per-step relabel + settle re-center + in-scene IK (§0 DECIDE)。**§7 に独立 cost 行**。
2. **within-phase progress scalar を obs に追加** (oracle 照会と TD の Markov 性の前提; CC2-2)。
3. **contract 統一:** 現状 3 系統 — B2 27D/6D abs / P2 scope 49D/12D residual (DQ7:102) / AC-AR 実装 42D/12D delta。**単一 schema に統一し demo 側を再変換** (converter 資産済)。12D なら HIGH5 (rot dims inert — demo rot-delta ≡0 実測) の disposition 必須; 6D pos-only 統一が代替 — design-gate Q。
4. **transition export / replay 互換** (R3)。
5. **reward 成分ログ分離 + phase predicates + seat/pin events。**
6. **DR hooks** (XY±20mm から; pose/shape 軸 = Rs spec 待ち `task_config.py:257-262`)。
7. **決定性/seed 方針 + nomA/nomB band を env 標準機能に。**
8. **throughput smoke = P2 DoD** (steps/s 実測 + **device 検証: route は cuda:0 pinned (device-fragile banked) — cuda:2 訓練前提の parity check を smoke に含める**)。
9. **Δ 非累積契約 (R2b 前提):** Δ = base の絶対 target への per-step offset (積分しない) + **Δ=const で drift ゼロの regression test** を env DoD に。
10. **CRIT1 phase-advance fork = 命名済み design-gate 決定項** (script-schedule vs agent-earned; 逸脱時の同期規約)。
11. **OG port + composite 導出 + 再検証** work item (§4.3-a/b; 完了まで OG の「2× validated」を新契約に主張しない)。
12. **safety/invariant guards:** 88mm Y-span / time_outs 純度 / **mujoco backend 強制** (Grip VBD-residue 教訓)。
- **gates:** env/reward = L3 → `/reward-design` + `/pre-check` + 5体 [VERIFY] + %9/%11 cross-PV + 層5。P1 PASS は non-cons — cg-GPU whole-route screen 未を smoke に編入。

---

## §7. 開発計画 (gate 駆動; 日程は目安・非拘束。**builder 割当を明記**)

| step | 内容 | 規模/費用 (実勢ベース) | gate | builder/verifier |
|---|---|---|---|---|
| **W0-a** | 本 plan Rs 審査 + D-A〜D-D + **数値閾値 (§4.3 draft) 確定 + OG band α/β/γ + L-TRIAGE 降格 confirm** | — | Rs | %12 提示 |
| **W0-b (Rs 選択時)** | mini-test 再開 — **fire-前 gate 完走から** ([L-TRIAGE β-mix]→[VERIFY]→[RULE-CHECK]→--rs-go+loud-notify)、timebox ≤2 wall-days | ~1-3 GPU-h | 既定の L3 chain (全 PENDING) | %11 build / %9 metric / %12 verify |
| **W0-c (並行)** | **P2 design-gate 審議** (spec 起草; §5-R2 reward sketch + §6 要件が INPUT) | CPU/paper | `/reward-design`+`/pre-check`+5体 | %12 起草 / %10 audit / %9 cross-PV |
| **W1-3/4** | P2 env build — **LOC 実勢: 既存単 skill env が AC 1278 / AR 1677 / Grip 1798 (+base 2109) → whole-route = 1.5-2.5k LOC 級** + **oracle API 独立行 (in-scene IK 床)** + smoke (throughput + device parity + cg whole-route) | CPU→GPU smoke | L3 + 層5 + cross-PV | %11 build / %10 audit / %12+%9 verify |
| **W3 (P2 smoke 後に直列)** | P3 demo-set: DR±20mm + **script-SR-over-DR-grid 検収 (survivor-bias falsifier; reach 0.9mm/CP-A 床割れ precedent → 被覆 metric 必須)** + leg-2 batch (adj-A + (iv) seg-co-move) | ~2-3h GPU-light | 代表性 gate | %11 / %9 |
| **W3-4** | **R2b campaign** (R2a は contingent-only §5-R2) | **eval 床込み 2-4 GPU-days 級/arm (§12 算術) — "10h+" は下限** | ⛔ HIGH-COST + production-launch-gate + **Rs GO (閾値 TBD が残る限り GO 不可)** | %11 run / %12+%9 joint verdict |
| **W4+** | **R3 = 新規 off-policy trainer build (~500-800 LOC + 自前 gate) → campaign** | build CPU + campaign GPU | 同上 (build = L3) | 同上 |
| **W5+** | R4 探索 (D-D) / δ 別途 Rs scoping | — | 都度 | — |

**cost cliff は 2 つ (honest):** W1+ の env と W4+ の R3 trainer。「見極めてから投資」順序は維持 — 崖の手前に W0 の全決定・全閾値・smoke を置いた。

---

## §8. Rs 決定点 (D-A〜D-D) — 推奨付き

| # | 問い | **推奨** | 根拠 / 代替 |
|---|---|---|---|
| **D-A** | entry: mini-test 再開 vs close 宣言 | **再開 (timebox ≤2 wall-days) + W0-c を並行** — ただし価値は epistemic close のみ (critical path を gate しない) と明示した上で | skip = 等価選択肢: 安いが A-vs-B OPEN の remnant が将来の imitation 論争に残る。再開時も fire-前 gate 完走が前提 (§5-R1) |
| **D-B** | env-build commit trigger | **mini-test 結果から独立、design-gate 成果物 PASS を trigger** (evidence-gated) | R2-R4 全てが env を要する。mini-test (B) でも full-DAgger は γ stream 部品で env の代替でない |
| **D-C** | R2/R3 の algo | **R2b residual-on-script を primary として PARKED-A を un-park** (採択時 = LEDGER/state 同 turn supersession banking) / **R2a は contingent-only** / **R3 既定 = RLPD (+提案機構は BC-proposal fallback 併設、oracle-direct は未検証変形として caveat 運用) + horizon arm ≥1** / Cal-QL・WSRL は条件付き (§5-R3-1) | 代替: DQ7 banked escalation の (i) canonical DAPG on B2 contract (residual を開かず 6D abs のまま) — CRIT1/HIGH5 再輸入を避けられる保守案。**P2-BLOCK 10 issues の再輸入対照表 = §5-R2** を見て Rs 判断 |
| **D-D** | R4 の「超える」軸 | **R3 証拠まで defer**。暫定 lead = (a) OG-gate curriculum + (b) queryable-expert 活用 | (d) stage 分解 = STOP-and-flag 手続き。horizon 対策自体は §5-R3-4 で R3 内に前倒し済 |

---

## §9. リスク台帳 (top12 + 反証手段)

| # | risk | 対策 / falsifier |
|---|---|---|
| 1 | **§4-kinematic + NEEDS-DUAL (LEDGER:56)** — RL は sim に無い物理を学べない | 全 verdict に conservatism 方向明示; kinematic 区間の成果は fidelity 内と常に限定 |
| 2 | PPO sample 食い × 未知 throughput | P2 smoke (falsifier); off-policy 繰上げ規則 pre-register |
| 3 | reward 設計失敗 (P2 BLOCK 10 issues 再演) | sparse 主体 + design-gate 4 成果物 + §運用21/22 + **再輸入対照表 (§5-R2)** |
| 4 | unlearning/発散再演 | §4.3 指標 + actor-gate + rollback + OG canary (**port/再検証後に有効**) |
| 5 | horizon >200 + time_outs 純度 | episode 設計 = design-gate; demo-state reset curriculum; terminal ∉ time_outs |
| 6 | **contract 3 系統の不統一** | §6-3 統一 + demo 再変換 + HIGH5 disposition |
| 7 | #562 非決定性 | band 法 + N≥30 + joint verdict |
| 8 | **OG 計器: band 較正 (0.667<0.8) + contract-bound 検証 RESET + composite 縮退** | W0 前出し (Rs) + §6-11 work item + per-rung 適用宣言 (§4.3) |
| 9 | teach-to-the-test ((iv)/R4a) | held-out 方向 + physics eval (m1-m4) |
| 10 | **CRIT1 phase-advance fork (residual 構成で再輸入)** | §6-10 命名済み design-gate 決定項 + desync 監視 |
| 11 | **P3 survivor bias** (reach 0.9mm; CP-A 床割れ precedent) | script-SR-over-DR-grid 検収 = P3 DoD (R2b viability precondition を兼ねる) |
| 12 | **eval cost 床 + device pinning** (cuda:0 fragile-pinned; cuda:2 parity 未検証) | §12 算術を GO 判断の前提に; parity = smoke DoD |

---

## §10. Compliance map

- proposal→build 境界: 本 doc は build しない。各 step の gate (L3 / design-gate / HIGH-COST / cross-PV / two-key) を都度完走 — **本 doc のいかなる記述も将来 gate の完了を先取りしない** (v1.0 の「済み扱い」表現は誤りとして v1.1 で全訂正)。
- verdict: %12+%9 joint + motion-bearing RESULT は video-first。
- banking: Rs 決定は同 turn で LEDGER + map + node state 反映。**D-C 採択時は DQ1=B→A' の supersession を LEDGER/state に明記** (PARKED un-park の記録)。
- prior-art V10: 各実行 step 前に再走。

## §11. 全体像の一言 (Rs 向け要約)

**「動く script を凍結 base に、少数の学習部品 (residual/proposal + 較正 critic) を gate 付きで載せ、OG offline gate を (port・再検証の上) 0-GPU 忘却警報に使いながら、R1(模倣の天井の誠実な close)→R2(基本 BC+RL、env の崖)→R3(off-policy SOTA 並走、第 2 の崖=新 trainer)→R4(THREAD 固有資産で超える) と、同一 env・同一 yardstick 上で段階昇段する」** — 調査 (干渉・unlearning・VLA) と THREAD 実測 (copycat/plateau/発散) の両方に整合する BC+RL の全体像。

## §12. cost 総括 — eval 床の算術 (印字済み、smoke で更新)

- **前提 (実測 anchor):** rollout ≈15-16 min/本 (B1 actuals; in-env episode の実測は smoke で更新) / eval 点 = N=30 / band = nomA+nomB ×2 legs / checkpoints ≈5 / 4-way 並列 (CP-C 実績)。
- **算術:** 30×15.5min ≈ 7.75h/eval 点 (single-stream) → 4-way ≈ **2h/eval 点** → ×(1+band 0.5) ×5 ckpt ≈ **~15h eval 床/arm** + train 本体 (10h+ 級、smoke 待ち) → **R2 campaign ≈ 2-4 GPU-days 級/arm**。R2a を contingent-only にする理由 (予算 ~半減) はここから。
- **device:** route = cuda:0 pinned (device-fragile banked)。cuda:2 (PRO 4000 24GB) 訓練前提は **未検証 → parity check = P2 smoke DoD**。
- R1 close ~1-3 GPU-h / P2+P3 = 2-4 週 wall 級 (LOC 実勢 §7) / R3 = trainer build + campaign (第 2 崖)。

## §13. Provenance / 検証記録

- supersedes: scratchpad skeleton (+ memory handoff の skeleton pointer は本 doc へ差替え済)。reference-over-copy: DQ7/DAPG scoping + KN が各領域の source of record。
- prior-art gate (起草時): BLOCKER hits = P4 HIGH-COST 標準 gate / §4・NEEDS-DUAL honest caveats / DAgger v1→v2 Rs 新 directive — 同一 failed path の再走なし。
- **5体 pre-debate (L2): 実施 2026-07-05 08:2x-08:4x (fable5 期)。verdict = CC2/CC3/CC4/CC5 全て PASS-with-fixes + CC6 NHA = CHANGE_JUSTIFIED。CRITICAL 0 / HIGH 12 / MED-LOW 9。全 HIGH ACCEPT → 本 v1.1 に反映 (08:49)。詳細 disposition = 下記 ADDENDUM。**

---

## ADDENDUM — 5体 debate disposition (REBUT_OR_ACCEPT 記録)

| ch | lens | 要旨 | disposition → v1.1 反映箇所 |
|---|---|---|---|
| CC2-1 H | algo | de-risk 発散 ≠ RL-unlearning (critic 無し; DAgger β-schedule 論が正 anchor) | ACCEPT → §3.1 unlearning 行 |
| CC2-2 H | algo | oracle-as-proposal: t-indexing 非 Markov / state-blind 省略 / 前例誤帰属 / 「同型」誤 | ACCEPT → §5-R3-2/3, §6-1/2, §3.1 IBRL 行 |
| CC2-3 H | algo | WSRL 前提逆転 (pretrained Q が無ければ再較正対象なし; no-pretrain+demos = RLPD 設計点) | ACCEPT → §3.2-1, §5-R3-1 |
| CC2-4 H | algo | horizon 対策を R4 送りは文献一致点に反する; JSRL/demo-reset 欠落 | ACCEPT → §3.2-3/4, §5-R3-4, §5-R2 horizon |
| CC2-5 M | algo | R2a 非 canonical (α 床 0.5=VBD historical→foregone conclusion) / contract 矛盾 / 3 択→2 無断 | ACCEPT → §3.1 DAPG 行, §5-R2 |
| CC2-6 M | algo | RL Token 20%→65% = KN に無い (citation integrity) | ACCEPT → §3.1 RL Token 行 |
| CC3-1 H | THREAD | DQ1=B / PARKED-A 供覧欠落 = 接地 gate 欠陥 | ACCEPT → §0 anchor 行, §8 D-C, §5-R2 対照表 |
| CC3-2 H | THREAD | 「Δは積分されない」は非累積契約を pin しない限り偽 (env:40 accumulates); CRIT1 欠落 | ACCEPT → §5-R0, §6-9/10, §9-10 |
| CC3-3 H | THREAD | oracle API = P2 co-root の bullet 化; 「trainer 差し替えのみ」過大 | ACCEPT → §6-1, §5-R3 冒頭, §7 |
| CC3-4 H | THREAD | OG canary: contract-bound 検証 RESET / composite Δ→0 偽 GO / 49D-12D 誤 cite / HIGH5 / fail-set 契約 | ACCEPT → §4.3, §6-3/11, §0 |
| CC3-5 M | THREAD | P3 survivor bias (script-SR-over-DR-grid 欠落); R2b の demo label ≡ Δ=0 | ACCEPT → §7 W3, §9-11, §5-R2b |
| CC3-6 M | THREAD | leg-2 無所有; per-rung yardstick 適用未宣言; composite seg-follow 構造不成立 | ACCEPT → §4.3, §4.2 γ, §5-R1 |
| CC4-1 H | cost | LOC 半分見積 (実勢 AC1278/AR1677/Grip1798+base2109); oracle 未予算; builder 未割当; P3 直列化 | ACCEPT → §7 全面 |
| CC4-2 H | cost | 「trainer 差し替え」on-disk 反証 (off-policy infra ゼロ) → R3 = 新 build = 第 2 崖 | ACCEPT → §5-R3 冒頭, §7, §11, §12 |
| CC4-3 H | cost | eval 床は今計算可能 (15-16min×N30×band×ckpt) → 2-4 GPU-days/arm; device parity 未検証 | ACCEPT → §12, §7 W3-4, §9-12 |
| CC4-4 H | cost | pre-registration が nominal (閾値・SR bar・window 無名; leg-2 band 不通のまま campaign) | ACCEPT → §4.3 draft 値 + W0-a DoD + 「TBD 中 GO 不可」 |
| CC4-5 M | cost | mini-test 3 根拠中 2 つ不成立 (code 非可搬 / RESOLVE 産物の消費者なし) | PARTIAL-ACCEPT (epistemic close 価値は維持・明示) → §5-R1, §8 D-A |
| CC4-6 M | cost | R2a 常設は決定価値なく費用倍 | ACCEPT → §5-R2 contingent-only, §8 D-C |
| CC5-1 H | gov | W0-b「済み扱い/既設/pre-registered」= state.md:140-142 と矛盾 (gate 全 PENDING) | ACCEPT → §0 mini-test 行, §5-R1, §7 W0-b |
| CC5-2 H | gov | 「5体 debate 実施済 + ADDENDUM」が書込時点で虚偽 (records-vs-fact) | ACCEPT → §13 を事後の事実で記載 + 本 ADDENDUM 追記 (同 turn) |
| CC5-3 M | gov | L-TRIAGE 自動昇格 hit の無言迂回 | ACCEPT → 冒頭 [L-TRIAGE RESULT] + W0-a Rs confirm 項 |
| CC5-4 M | gov | DQ1=B anchor 欠落 + 「既定にする」decision voice | ACCEPT → §0, §4.1 (推奨へ), §8 D-C |
| CC5-5 LM | gov | row54 cite 行 shift (正 = :56) + §6.2 dangling | ACCEPT → §0 row56 行, §5-R0 |
| CC6 | NHA | **CHANGE_JUSTIFIED** (条件: KN=source of record 明示 / PROPOSAL 維持 / 07-05 verbatim の Rs confirm / memory pointer 差替え) | 条件 4 点すべて反映 (§冒頭, §1, §13) |

*RS-TECH-LEAD %12 — 2026-07-05 JST. 0-commit. INVARIANTS 不触.*
