# WMSO D1.1-B / D1.1-C + boundary-only vertical slice — Decision Record and Scope Preregistration (v1.1.1)

- node: `T-WMSO`; author = w2:pQ (RS-TECH-LEAD2); 記録 = **2026-07-20 08:53 JST（実測）**; **v1.1 改訂 = 2026-07-20 09:32 JST（実測 09:32:42 — pN SCOPE HOLD B1-B4 fold）**; **v1.1.1 = 09:44 JST（実測 — pS 指摘 N-1 records-only 修正、§10 版歴参照）**
- 位置づけ: D1.1-A `contracts_v2` **FREEZE 後**の後続 chunk 群の decision record + **D1.1-B の詳細 prereg + D1.1-C / slice の banked outline**。工程ゲート順序 = D1.1 prereg v3.2.2 §9（Rs #8 一本化）を継承。
- 統治: **frozen v2.11.2 package = 不変の土台**（`WMSO_D11A_FREEZE_RECORD_20260720.md` §2 pins: DESIGN `00192d20ca00b654…` / EP v1.9 `c474acea7c58…` / JSON v1.9 `e63176af9bc3…` / def hash `e7ca43093084…`）。本 doc は frozen 3 file を編集しない。
- [DEFER-RECON] = `WMSO_D11BC_SLICE_DEFER_RECON_RSTECHLEAD2_20260720.md`（同時 bank・PASS〔設計 chunk として〕）。

## 0. Provenance（Rs verbatim — decision の出典）

> 「D1.1-B（tensor binding）/ D1.1-C（artifact manifest）/ boundary-only vertical slice 着手」

- 受信 = pQ session chat、**2026-07-20 08:42 JST 頃**（直後の `date` 実測 08:42:15 の直前受信・分解能 = 分）。
- 意味 = freeze record §5 の予告順序（B → C → slice、着手は Rs 指示 — self-start 禁止）に対する **Rs 着手指示 = 解錠**。
- 系譜: pN freeze consultation **(3) 次順序 + 要件列挙**（`WMSO_PN_FREEZE_CONSULTATION_TRANSCRIPT_20260719.md` L18、blob `db24b877d234…` @ `6af253dc14`）/ RV5 §6 carries（`WMSO_RS_PLAN_STATUS_REVIEW_V5_COPY_20260719.md` §6）/ prereg v3.2.2 §2 OUT（B/C の banked 定義）/ DESIGN v2.11.2 §10（binding carries・kinematic 写像）。

## 1. Decision（ACCEPTED — Rs authority）

1. 着手順序 = **D1.1-B（tensor binding）→ D1.1-C（artifact manifest）→ 2–3 skill boundary-only vertical slice**（pN (3) / freeze record §5 の banked 順序を保持）。
2. 本 prereg の被覆 = **3-chunk sequence の decision record + D1.1-B の詳細 scope（§2）**。**D1.1-C / slice は着手時に各自の詳細 prereg** を切る（§9 loop 再適用。本 doc §3 / §4 は banked outline — scope の先取り確定ではない）。
3. **frozen v2.11.2 は不変**。B/C の設計が contracts_v2 の schema delta を要する場合 = **supersession 記録付き新版 + Rs review 経由**（DESIGN v2.11.2 §10 kinematic 写像 (c) と同経路）。黙って編集しない（prereg v3.2.2 §9 fail-closed re-verify loop）。
4. **impl/training/authority = CLOSED 継続**（freeze record §4 逐語: impl は別 gate〔pre-check → rule-check → path freeze / impl GO〕+ kinematic 全廃 HALT 解消が前提のまま CLOSED）。本 sequence は**設計書面 chunk**。

## 2. D1.1-B `tensor_binding` — 詳細 scope

### IN（design）

1. **`TensorBindingSpec` 型設計** — 束縛対象（prereg v3.2.2 §2 OUT 逐語 ∪ pN (3) B 要件）:
   - **obs 側**: source field 参照（`semantic_obs_schema` field_id への content 参照）/ source offset・length / **訓練時 feature 順序** / dtype・shape・unit・frame（SemanticFieldSpec との整合検証）/ normalizer（scheme + mean・std の artifact 参照）/ scale・bias / bounds / **mask** / quaternion convention / frame / **history stack** / **sampling rate・control-timing（cadence）** / **belief/vision input binding**
   - **action 側**: 順序・shape・dtype / **action scale**（DESIGN §1.2 N-a「action scale ⊂ TensorBindingSpec」の履行）/ bounds / control mode 整合（LEARNED = DIFF_IK_EE_TARGET のみ — §0 DiffIK-only の契約層執行を維持）/ control/timing
2. **BC+RL / RL-only 双方の fail-closed bind**（pN (3) 逐語）: TrainingLineage（RL_ONLY / BC_ONLY / BC_THEN_RL / DEMO_PLUS_RL）× binding の整合規則 — stage 間（BC→RL）で binding 同一か明示 supersede かを機械判定。不明・欠落 = fail-closed（E_* 発行、通さない）。
3. **hash 定義**: TensorBindingSpec の WCJ canonical 直列化 → sha256 = `ExecutionBundle.tensor_binding`（ArtifactSlot）が指す**実体**の確定。**DC-1 fail-closed 規則の実装形** = 「D1.1-B 完了前は tensor binding hash が存在しない → 当該 skill は closed-loop eligibility を得られない」の型・validator 表現。
4. **EP 整合**: TENSOR_BINDING / CONTROL_MODE component は **EP v1.9 の total map に既存**（DC-2 の component 追加レグは fold 済 — 本 session 実測 grep: 各 9 hits）。B の残作業 = 当該 component の evidence が attest する **artifact 実体と proof obligation の結合**（grade 別に何を示せば TENSOR_BINDING evidence として成立するかの明文化）。EP 本文の変更を要する場合 = EP 新版（supersession、frozen v1.9 は不変）。
5. **handoff の grasp/contact stability encode**（RV5 §6 (ii) = DESIGN §10 carry (ii) 逐語「D1.1-B semantic spec の設計入力」）: HandoffSchemaSpec fields への grasp/contact stability field 群の設計 — handoff state を arm pose だけで表現しない（1 mrad 級 arm 差が discrete chain flip と共存し得る）。
6. **golden vectors / invalid corpus**（DC-4 の B 型適用）: normalization mean・std / scale・bias / bounds 全値への isfinite、NaN/±Inf 拒否、bool-as-shape、unknown enum/JSON field、Unicode 正規化差、duplicate canonical key — B 型に対する追加 corpus + **golden hash vectors（機械可読 fixture を design 同梱** — D1.1-A §8 A/B golden と同型）。
7. **drive-substrate lineage 明示の要否判定**（DESIGN §10 kinematic 写像 (c)）: 必要と判明した場合は **schema delta として Rs review 経由**（本 chunk 内で黙って導入しない）。

### OUT

- D1.1-C の全て（§3）/ slice の全て（§4）/ **impl**（freeze record §4 CLOSED）/ frozen 3 file の編集 / reward・env・成功条件の変更（該当なし — 発生時は /reward-design + Rs、§7）。

### Exit（D1.1-B design chunk — D1.1-A と同型の「設計 chunk exit」）

- design doc（機械可読 fixture + golden 同梱）完成 → **5体 CC Debate / pre-mortem → design 修正 → pS final-design PASS → pN DESIGN PASS-CLOSE（exact-pin）→ Rs freeze 判定**（単一 chain — §5 と同一。pN B1 fold: pS を debate 後の final-design gate に置き、debate 修正による pS PASS の stale 化を除去）。
- impl レグの exit（v3.2.2 §2 milestone Exit の「tensor_binding pass」等）= **impl 解錠後の別 chunk へ carry**（milestone 条件自体は不変に保持）。

## 3. D1.1-C `artifact_manifest` — banked outline（詳細 prereg は C 着手時）

- contracts_v2 + tensor binding を **code / model / data / config / evaluator / EvidencePolicy / substrate_id の exact hash へ結合**（pN (3) 逐語）。training-time run manifest 型。
- **substrate_id 必須化**: 旧 contaminated log へ明示 substrate_id を付与し **silent pooling 禁止**（RV5 §6 (i)。D2 transition data = 修正済み clean substrate のみ — DDR #26 の恒久対策を型で実装する側）。
- minimal JCS（D1.1-A 実装分）の **package 全体への展開**（artifact manifest・証拠 bundle・配布 metadata）+ package/CI 最終整備（v3.2.2 §2 OUT 逐語）。
- DC-3 grade 別 proof obligation の実体結合（EXACT_TRAIN_TIME = training run manifest / source commit / config hash / … — C の manifest が proof の実体供給源）。

## 4. boundary-only vertical slice — banked outline（詳細 prereg は slice 着手時）

- 構成 = **2–3 skill + 1 transition/recovery、boundary-only**（mid-skill interruption なし — charter §5 Phase B）。候補 = **APPROACH_CABLE → INSERT_INTO_CLIP（必要なら → CLIP_CONFIRM）**（pN (3)）。
- **必須化項目（pN (3) 逐語）**: success だけでなく **failure / no-chain・abstain / UNKNOWN・calibrated uncertainty・invalid handoff・stale epoch・recovery / stop・grasp / contact stability・deadline 計測**。（RV5 §6 (iii): 成功 transition のみで作らない）
- 低位学習法 = **PPO 限定せず BC+RL / RL-only を許容**（METHOD_REGISTRY で担保 — B4）。高位 = **vision 由来 belief + skill-dynamics world model**（Rs L0 手段裁定〔RL+IL+vision+world model 必須〕と整合）。
- **slice acceptance の portfolio 束（pN scope verdict B2 — L0 四手段の conjoin）**: slice acceptance 述語に **`portfolio_has_RL ∧ portfolio_has_IL ∧ vision_belief_live ∧ skill_dynamics_model_live`** を明示 — **1 つでも false なら L0 進捗 / slice-success claim 不可**。per-skill の RL-only は合法だが **IL leg を代替しない**（portfolio 水準で RL・IL 両方が生きていることが必須 — per-skill 許容だけでは RL-only 構成の slice が通ってしまう穴を塞ぐ）。
- boundary（本 slice の **runtime 選択点**）= **skill 終端（TERMINAL outcome）のみ**（pN scope verdict B3 — pN (3) の「skill 終端 / 安全 checkpoint のみ」を同一著者がより厳格側へ精緻化・supersede）。**CheckpointSpec は静的契約として保持可**だが、**checkpoint 途中切替の実行 = Phase G / 別 gate**。checkpoint-enabled slice に変える場合は **chunk 改称 + scope 再審査**。mid-skill RT switching / full training-ready claim = **別 gate**（pN (3)）。
- **実行前提（slice の run レグ — 設計書面はこれらに先行可**〔RV5 §6 (5): 契約完全主義で slice を無期延期しない〕**）**: impl 解錠（freeze record §4 の別 gate + kinematic 全廃 HALT 解消）+ **clean substrate = canonical all-thread_isaac_lab Layer-8 guard（landed successor 系譜 — 例 `7803f58f17`「Expand Layer 8 guard coverage」以降）で LAYER8_FAIL = 0**（pN scope verdict B4 — **snapshot remediation + scripts closure を含む全 root 被覆の 0 のみが解錠条件**。旧 envs/scripts 限定の 0・envs のみ 0 は十分条件でない。DDR #25/#26 の解消を包含。参考実測 = pN verdict 09:31: snapshot BODY3 + scripts 125 = 128 fail @ `7803f58f17`〔pN 測定・pQ 未再測〕）+ [HIGH-COST-GATE] / production-launch-gate（該当時）+ **Rs 実行承認**。

## 5. 工程ゲート順序（v3.2.2 §9 + pN B1 明示 delta〔pS final-design PASS を debate 後に追加〕）

```text
scope prereg → pS design re-check → pN SCOPE CONCUR
→ design draft（D1.1-B DESIGN doc）→ 5体 CC Debate / pre-mortem（設計レビュー）
→ design 修正 → pS final-design PASS → pN DESIGN PASS-CLOSE（exact-pin）
→ Rs freeze 判定 →（impl 系 = CLOSED、解錠 = Rs + HALT 解消）
```

- **v3.2.2 §9 からの明示 delta（pN B1・supersession）**: §9 原文の design 段 chain（draft → 5体 CC → 修正 → pN）に **pS final-design PASS を debate 後・pN 前に追加**（D1.1-A 実践で pS が §16-§18 design legs を担った形式を正式化）。**§2 Exit / 本 §5 / roadmap 記述は本 chain に一本化**（3 面一致 — pS record §8 の旧表現は本版が supersede）。**後段 finding で design が変わった場合は pS / pN 双方を再 verify**（片軸 PASS の持ち越し禁止）。

- fail-closed re-verify loop（pN C3）: 後段 finding が design を変える場合、design 再 bank →（規模に応じ CC Debate 再実施）→ pN DESIGN 再 verify。PASS-CLOSE は最終 design sha に対してのみ有効。
- lanes: dev = w2:pQ / design-ratify = w2:pS（WMSO-DESIGN）/ evidence-verify = w2:pN / custody = w2:p6。検証は fresh detached worktree（共有 dirty tree の結果を引用しない）。

## 6. Binding carries（loud — 消失防止）

- **DC-1..DC-6**（v3.2.2 §10b）— B/C の design doc へ carry。補記: **DC-2 の component 追加レグは EP v1.9 で fold 済**（§2-4）。**DC-5 は B4 METHOD_REGISTRY で処理形が確定**（algorithm 拡張 = registry 行・enum 拡張でない）— 「lineage 表は実在限定」の原則自体は carry。
- **RV5 §6 (i)–(iv)**（DESIGN v2.11.2 §10 の loud 記録と同一 — (i) clean substrate のみ + substrate_id / (ii) grasp・contact stability encode / (iii) slice は failure + calibrated uncertainty 含む / (iv) 契約完全主義で slice を遅らせない）。
- **pN consultation (3) 全文**（transcript pin `db24b877d234…` @ `6af253dc14`）。
- **kinematic COMPLETE REMOVAL 写像 (a)–(e)**（DESIGN v2.11.2 §10）— 特に (c) drive-substrate lineage delta = Rs review 経由。
- **Rs L0 手段裁定**（RL+IL+vision+world model 必須）— substrate fork / trainer 再構成で foreclose しない。

## 7. Process / L-triage

- **L = L3**（本 session /rule-check stage1: 設計変更 + 新規複数 file + charter 統治 node — v3.2.2 §11 と同型分類）。
- FOUNDATIONAL INVARIANT（RS71 §0: dual-arm / 88mm / DiffIK / コ / no-trick）= **非抵触**(WMSO = 高位 orchestration 契約層。DiffIK-only は契約が執行する側で、変更しない)。
- /reward-design = **非該当**（Phase D objective/SDM で発動 — v3.2.2 §11 と同判定）。**slice の判定定義（success/failure 判定・計測定義）を設計する段で該当性を再判定**（直交ゲートは L と独立・常時）。
- prior-art guard = rc=2・blocker 16 件 → **全件 = 認可済み次 chunk を定義する計画面への一致（FAILED path 一致 0）**、継続根拠 = Rs 08:42 頃指示。詳細 = [DEFER-RECON] record §3。

## 8. 未解決点（design draft で提案し pS/pN 検証に付す）

- **U-1**: TensorBindingSpec と handoff identity + epoch 機構の結合形（stale epoch 検査は slice 必須項目 — 型を B が持つか C の manifest 側かの分担）。
- **U-2**: belief/vision input binding の粒度（semantic field 参照までか、vision encoder artifact hash まで B で束縛するか。encoder artifact の exact-hash 結合は C と分担の可能性）。
- **U-3**: drive-substrate lineage field の要否（§2-7 — 要る場合 Rs review 経由の schema delta）。

## 9. 次アクション

1. 本 prereg + [DEFER-RECON] record を bank（explicit-path commit）→ p6 へ LEDGER row44 反映 dispatch。
2. pS へ design re-check dispatch（§5 gate 順）→ pS PASS 後、pN へ SCOPE CONCUR readback dispatch。
3. Rs へ checkpoint 報告(3 行 + artifact path / sha)。
4. pN SCOPE CONCUR 後: **D1.1-B design draft 着手**（frozen v2.11.2 を土台にした別 doc — 本 prereg §2 の IN を実装する設計書面）。

## 10. 版歴 / record-fix（fail-closed loop 記録）

- **v1**（2026-07-20 08:53、blob `87f348540c93f0f2…` @ `7fc04d1baa`）: 初版。**pS 設計軸 re-check = PASS**（must-fix 0・carry C-1/C-2、record `bed5133fb28a…` @ `652ff63a60`）→ **pN scope verdict = SCOPE HOLD B1-B4 + N1**（09:31:43、transcript = `WMSO_PN_D11BC_SCOPE_HOLD_B1B4_TRANSCRIPT_20260720.md`。exact pins 3/3 CONFIRM・DEFER 26/26 被覆・frozen A 不触・design-only/impl CLOSED・C/slice 詳細 prereg 分離 = PASS 側）。
- **v1.1**（2026-07-20 09:32 実測、本版）— **pN B1-B4 fold**:
  - **B1** = design 段 gate chain を「draft → 5体 CC Debate → 修正 → **pS final-design PASS** → **pN DESIGN PASS-CLOSE（exact-pin）** → Rs freeze」に**一本化**（§2 Exit / §5 / roadmap の 3 面一致・v3.2.2 §9 からの明示 delta として §5 に記録・後段 finding 時は pS/pN 双方再 verify。pS record §8 の旧 chain 表現は本版が supersede — pS B1-B4 readback で確認予定）。
  - **B2** = §4 に slice acceptance の portfolio 4-conjunct（`portfolio_has_RL ∧ portfolio_has_IL ∧ vision_belief_live ∧ skill_dynamics_model_live`、いずれか false = L0/slice-success claim 不可）。
  - **B3** = §4 boundary（runtime 選択点）= **TERMINAL outcome のみ**（CheckpointSpec = 静的契約保持・checkpoint 途中切替 = Phase G/別 gate・checkpoint-enabled 化は chunk 改称 + scope 再審査）。
  - **B4** = §4 run 前提の clean substrate 条件を **canonical all-thread_isaac_lab Layer-8 guard LAYER8_FAIL=0**（snapshot + scripts closure 含む全 root）へ強化（DDR #25/#26 包含・guard 系譜 anchor = `7803f58f17` 実在確認済み）。
  - **N1（NON-BLOCK provenance）** = pS record bank commit **`652ff63a60` は p6 staged 5 path（LEDGER row44 / T-WMSO・T-ROOT-RS-TECH-LEAD2 state.md / \_handoff sidecar sha256 ×2）を co-land**（pQ の非 pathspec 限定 commit による掃き込み — 内容 = p6 staging snapshot 無改変・p6 へ records-fix 通知済 09:29）。**semantic blob（pS record `bed5133fb28a…`）は exact pin で不変**。以後の pQ commit = pathspec 限定（`git commit -- <paths>`）。
- 本 v1.1 は v1 の §2 Exit / §5 / §4 該当 3 箇所を supersede。**次 = 本版 bank → pS B1-B4 readback → pN re-readback**（両 PASS まで **design authoring / [CHANGE] = CLOSED 継続**）。
- **v1.1 検証結果**: **pS B1-B4 readback = ✅設計軸 PASS**（09:41・fold 4/4 faithful〔transcript 逐語照合〕・§8 supersede 確認・N1 acknowledge・record 同 file §10-§11 に amend = sha `27e007afe2443447…`〔旧 v1-era blob `bed5133fb28a…` @ `652ff63a60` は履歴に保存〕）。residual = **指摘 N-1（minor・records-only・非 blocking）**: §5 header「継承 — 変更なし」が body の「明示 delta」と矛盾。
- **v1.1.1**（09:44 実測、本版）: **N-1 修正のみ** — §5 header を「v3.2.2 §9 + pN B1 明示 delta〔pS final-design PASS を debate 後に追加〕」へ（gate semantics 変更なし・records-only）。**次 = 本版 + pS amended record を bank → pN re-readback → SCOPE CONCUR**（それまで design authoring / [CHANGE] = CLOSED 継続）。
