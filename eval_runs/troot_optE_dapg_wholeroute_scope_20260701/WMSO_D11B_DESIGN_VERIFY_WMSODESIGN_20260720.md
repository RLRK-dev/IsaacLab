# WMSO D1.1-B `tensor_binding` DESIGN v2 — pS final-design 設計軸 verify（MWSO-DESIGN）

- node: `T-WMSO`; 検証者 = w2:pS (MWSO-DESIGN); 記録 = **2026-07-20 11:26 JST（実測 date-THEN-write）**
- 依頼元 = w2:pQ (RS-TECH-LEAD2)、dispatch 11:16 JST（5体 CC Debate cycle-1 FAIL → design v2 fold・bank → §5 chain の pS final-design PASS レグ）
- gate 位置 = prereg v1.1.1 §5 chain の「**pS final-design PASS**」段（debate 後・pN exact-pin DESIGN PASS-CLOSE 前）。D1.1-A pS FINAL CONFIRM 級の最厳格 gate。
- 0-commit: 本 record = pS 著作 verify artifact。bank = pQ/p6。

## 1. 検証対象 pin（committed blob @ HEAD `9d5d44e329`・独立確認・worktree==committed）

| artifact | sha256 | 検証 |
|---|---|---|
| DESIGN v2 (`WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md`) | `7248de8600a454181a7d9e90c64282c819fd8ce3a1b2a948b3a93431aff0564b` | ✅ = pQ 主張 |
| debate verdict (`WMSO_D11B_CC_DEBATE_CYCLE1_VERDICT_RSTECHLEAD2_20260720.md`) | 実在（blob `1dcc0a705ede…`） | ✅ |
| golden_1 / _2 / _3 (`wmso_d11b_fixtures/`) | `0cc2fc1616b64abd…` / `45cfe2c8882c2cd0…` / `e1ed424fdff50546…` | ✅ = pQ 主張・worktree==committed |

## 2. 先走り抑制 — chain 接地（design authoring 解錠の正当性）

LEDGER row44 実読: scope 段 = **3 軸 CLOSE**（Rs 着手 08:42 / pS 設計軸 PASS ×2〔09:29 初回 + 09:41 B1-B4 readback〕/ **pN exact-pin SCOPE CONCUR 09:48**〔B1-B4+N-1 ALL CLOSED〕）→ **解錠 = D1.1-B DESIGN AUTHORING のみ**。私の N-1（§5 header stale）も v1.1.1 で records-fix 済。draft v1 `31d96783` → 5体 CC Debate cycle-1 FAIL → v2。**gate skip なし・code/[CHANGE]/run/training/authority = CLOSED 継続**。

## 3. Load-bearing premise の on-disk 検証（role-lesson (c)）

| premise | v2 の主張 | on-disk 検証 | 判定 |
|---|---|---|---|
| **§4 proof_artifact_resolver（A3・frozen delta 非要）** | D-5 hash-identity 検査は frozen `certify_definition` の `proof_artifact_resolver.resolve_artifact(ref,expected_sha256)` を使用（引数追加 = 要時のみ Rs review） | frozen DESIGN L284 `certify_definition(…, proof_artifact_resolver)` + L285 `resolve_artifact(ref, expected_sha256)` 実在 | ✅ **frozen delta 非要**・既存機構使用・fallback は §10 で Rs review guard |
| **§3 EP grade 表（D-1・closed-query 再発検査）** | 全 5 grade を wildcard/`_applicable` 展開で再導出・TB は 4 authority-grade 全被覆 | frozen JSON: EXACT/HASH=per-component(TB在籍) / RECONSTRUCTED_COMPATIBLE=`_all_13_components` wildcard / DIMENSION_ONLY=`_applicable.components` **TB_in=True** / UNKNOWN=空。profiles CLOSED_LOOP rank3 / SHADOW rank2 / OFFLINE_REPLAY のみ TB not_applicable | ✅ **表は on-disk と完全一致**・D-1 error 再発なし・SHADOW rank2=RECONSTRUCTED の洞察も正 |
| **§5 PROVISIONAL 理由（§5D）** | required 化は frozen §5D「consumer required ⊆ producer」を破り major version event | frozen DESIGN L388「consumer required ⊆ producer」実在 | ✅ 理由 grounded |
| **§6 golden（D-4）** | G-1/G-2/G-3 + 生成器 bank・独立再計算可 | `build_goldens.py` 独立実行: G-1/2/3 = `0cc2fc16`/`45cfe2c8`/`e1ed424f`（1435/1967/3065 bytes）全一致・frozenset variant `7def3ff5`≠G-3（判別性実証）・型 assertion PASS | ✅ 独立再現 |

## 4. pQ 指名 3 点の設計軸判定

- **C-1 遵守 = ✅CONFIRM**: B-internal enum（§1.1・11 個）は **新 schema 内部語彙**で frozen enum を改変せず。frozen enum 参照（`TrainingLineage`/`ControlMode`/`Dtype`）は **member 追加 0**（§1.5「member 追加なし」明記）。C-1 の「frozen enum に member を silent 追加しない」規律を **B 自身の enum にも適用**（§1.1「member 追加 = version bump + supersession + Rs review」）。METHOD_REGISTRY の method_class/lineage 追加 = **なし**。
- **C-2 遵守 = ✅CONFIRM**: §1.3 TimingSpec = **SI 物理量のみ**（policy_rate_hz/obs_sampling_rate_hz/max_obs_staleness_s・substep/solver 語彙なし）。§8 U-3 = drive-substrate lineage を **B に導入しない**（DDR #25/#26 rework 前 taxonomy 焼込回避・data 識別 = D1.1-C substrate_id・要時 Rs review）。
- **§5 PROVISIONAL 化 = ✅可（設計健全）**: required 化は (a) frozen §5D 違反（検証済）(b) 判定述語/error code 欠如 (c) **boolean-only 必須化は occlusion 下 producer に捏造圧力**（RV5 §6(iii) calibrated uncertainty + standing lesson「grasp verdict を数値で PASS 宣言するな・human GT 最終」に整合）。不確実性 channel（stability_confidence/stability_unknown）追加は正しい保守的手。RV5 §6(ii) の「設計入力」は field group 設計として充足・必須化は slice prereg+Rs へ委譲 = under-deliver でない。
- **§4 適用位置 = ✅frozen delta 非要**（上 §3 で検証済）。resolver 到達不能が impl で判明した場合のみ frozen delta → Rs review（§10 open point で guard・黙って引数追加しない）。

## 5. CRITICAL 4 + HIGH/NHA fold 忠実性

- **D-1（EP 不在主張 FALSE）** = ✅ §3 全 grade closed-query 再導出、on-disk 完全一致（§3 検証）。⭐これは私の delivery-surface lesson（[[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]]）を pQ が踏んだもので、fold は lesson 準拠に修正。
- **D-2（IDENTICAL 自己 hash 不動点）** = ✅ §1.5 IDENTICAL⇒`demo_dataset_binding_hash`=null・外部確認 = D1.1-C manifest（`E_BINDING_STAGE_IDENTICAL_UNCONFIRMED`）。§0 反循環を「自己参照 hash を preimage に置かない」構造 pattern へ一般化（M2 循環の根治）。
- **D-3（flatten 順序未規定）** = ✅ §1.2 `flatten_order`（ROW_MAJOR・hash-visible）+ §1.3 `history.layout`。
- **D-4（fixture 未 bank）** = ✅ §6 G-1/G-2/G-3 + `build_goldens.py` bank（§3 独立再現）。
- **HIGH D-5..D-13 + MED/LOW D-14..D-31** = §4 validator / §1 型 / §6 corpus / §7 test に per-item fold（doc §12 map）。NHA 縮小（§3 誤主張撤回・§5 PROVISIONAL・§8-2 降格・reuse gate §9）採用。G-2 破棄は正当に部分 REBUT（判別に必要→修正版+G-3 complement）。

## 6. 設計軸の横断チェック

- **FOUNDATIONAL invariant（RS71 §0）非抵触**: dual-arm（§6 G-3 14dim dual-arm）/ 88mm（§5 grasp_span_error が RS71 §0#2 を **引用**・改変せず）/ DiffIK-only（§1.4 control_mode LEARNED⇒DIFF_IK_EE_TARGET を契約層執行）/ コ-shape（不触）/ no-kinematic（§8 U-3 drive-substrate 非導入）。
- **rule (g)**（human-ruled 面）: 改変 0（88mm は引用・enum 変更は Rs review 経路）。
- **rule (h)**（組合せ完全性）: §3 は全 5 grade 列挙で subset 主張でない（on-disk 検証済）。§6 corpus は「impl で全列挙」と正直に scope。
- **文書自立性（role-lesson (b)）**: normative content は self-contained（frozen A = 不変土台 = 正当参照）・v1 参照は §12 版歴（歴史のみ）。
- **Rs L0 mandate（scope B2 portfolio）**: §8 U-5 が `portfolio_has_IL` を「D1.1-C 完了 ∧ kinematic 削除後 demo 再記録」に依存と loud carry・vision_belief = §1.3 producer_schema_hash bind・WM artifact 水準 = D1.1-C。整合。

## 7. Carry（downstream 入力・本 PASS の blocker でない・doc が既に明記）

- **D1.1-C prereg 必須入力**: U-2（producer artifact 差替え阻止は C の closed-loop eligibility 検査）/ U-5（demo 移行 blocker = IL 到達条件）/ IDENTICAL の両段一致確認（manifest）。
- **slice 詳細 prereg**: §5 必須化可否・class 台帳・窓幅・閾値 / `/reward-design`+`/pre-check`（判定式・閾値を定める段で発火・直交ゲート）。
- **impl 解錠時**: §4 resolver 到達性の実証（偽なら frozen delta→Rs review・§10）/ producer↔binding 対応の owner 指名（§9 reuse gate carry・ABSENT-IN-CODE 類型）。

## 8. Honest scope（私が検証した / debate・pQ 主張として受けた の切り分け）

- **私が on-disk 独立検証**: §1 pin 3種 / §3 の 4 premise（resolver・EP grade 表・§5D・golden 再計算）/ C-1/C-2/§5/§4 の設計判断 / FOUNDATIONAL・rule-g・rule-h・自立性。
- **debate（CC6）検証済として受領・私は再 grep せず**: §9 reuse gate の fail-open 行 cite（`observation_manager.py:271-272`）/ obs_builder dead code / D-29 mis-citation 修正後の cite。いずれも保守的方向（custom spec 正当化・records 精度）で **設計軸 blocker でない**。

## 9. Verdict ⛔SUPERSEDED（2026-07-20 11:45 — 正 = §10）

> ⛔ 当初の「pS final-design PASS」は**誤り**。pN exact-pin DESIGN HOLD B1-B5（11:39:03）が supervene し、私は 5/5 を held v2 pin + frozen で on-disk CONCUR（§10）。当初 verdict（下記・打消）を撤回。訂正後 = **⛔HOLD（v3 fold + bounded cycle-2 → pS reverify 待ち）**。

**~~設計軸 = ✅PASS（DESIGN v2・pin `7248de8600a4` @ `9d5d44e329`）= pS final-design PASS~~**（SUPERSEDED → §10 HOLD）
- CRITICAL 4 fold 全て faithful（**D-1 再導出 = on-disk 完全一致 = closed-query error 再発なし**）・load-bearing premise 4/4 on-disk 検証・C-1/C-2 遵守・§5 PROVISIONAL 健全・§4 frozen delta 非要・FOUNDATIONAL/rule-g/rule-h/自立性 clean・**must-fix 0**。
- **cycle-2 debate = 私は不要と判断**（v2 は 31 項の忠実 fold・私の独立検証で新規 CRITICAL/HIGH = 0）。ただし skill max-2-cycles ゆえ **pN/Rs 裁量は残る**。
- ⚠**two-key**: 本 PASS = **設計軸のみ**・**pN exact-pin DESIGN PASS-CLOSE を代替しない**。§5 chain = pS final-design PASS → **pN DESIGN PASS-CLOSE（exact-pin）** → Rs freeze。D1.1-A で pN が私の PASS を 5 度 supervene した pattern を継承 — pN が design 変更 finding を出せば fail-closed loop 再起動（pS/pN 双方再 verify）。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。次 = pN exact-pin DESIGN verify → Rs freeze。**私 = pN verdict 待ち（self-start なし）**。→ §10 で supersede。

## 10. ⛔pN exact-pin DESIGN HOLD B1-B5 supervention — 5/5 CONCUR + own（2026-07-20 11:45 実測）

pN（w2:pN）dispatch 11:39:03: DESIGN v2（pin `7248de8600a4`）exact-pin evidence verdict = **DESIGN HOLD B1-B5**、私の pS final-design PASS を supervene。**私は 5 項を held v2 pin（`git show 9d5d44e329:…`）+ stable frozen に対し on-disk 検証し 5/5 CONCUR。私の PASS は誤り。** WMSO chain で pN が私の PASS を supervene した **6 度目**・⚠**B1+B2 は 5体 CC Debate cycle-1 と私の pS PASS の両方を escape**（= 私が設計軸を実際に見逃した）。

| # | pN finding | on-disk 検証（held v2 pin / frozen — stable 面） | 私の miss | 分類 |
|---|---|---|---|---|
| B1 | ArtifactSlot は hash only・resolver は `(ref,expected)` 要・grade 横断の uniform TensorBindingSpec locator/proof 無 → frozen-delta-非要 は **unproven** | frozen L51 `ArtifactSlot={state, artifact_hash}`（**ref なし**）・resolver の `ref` は ProofItem(L245) 側 | **§4/A3 over-claim**: resolver 実在は確認したが **ref 供給（全 grade で uniform proof/locator）を未検証**。「機構の実在」を「機構が invoke 可能」と混同 | 設計軸・私の §4 直撃 |
| B2 | 3 golden 全て required obs/action.container_dtype を欠く・builder assertion も欠く | **held v2 golden_1 の container_dtype = 0**（`git show 9d5d44e329:golden_1`）・v2 §1.3/§1.4 は container_dtype 必須 → goldens schema-invalid | **fixture の schema 完全性を未検**（hash 再現・builder「PASS」だけ見た＝**bug の下で緑**〔assertion が container_dtype 未検〕）。⚠**本 turn 私は最初 worktree(v3 WIP)を読み「container_dtype 在」と誤認 → held pin で 0 を再確認**（moving-tree hazard 実例） | 設計軸・私の golden 検証直撃 |
| B3 | MIN_MAX 在・G-3 使用だが validator は mean/std のみ | v2 §4 `E_BINDING_NORMALIZER_VALUE`=mean/std のみ・§1.1 MIN_MAX・G-3 使用 | **面間整合 miss**（scheme × validator 被覆未照合） | 設計軸 |
| B4 | container dtype の cast semantics / lossless-reject 不在 | v2 §1.3「cast が起きることを明示」のみ・§4 に cast error code 無 | **B2 随伴の未完**（container_dtype を足したが semantics 欠） | 設計軸 |
| B5 | topology_ledger_hash は frozen HandoffSchemaSpec に representable location 無 | frozen `HandoffSchemaSpec.fields=SemanticFieldSpec{dtype∈FLOAT32/INT32/BOOL}`・v2 §5 topology_ledger_hash dtype「—」 | **「—」dtype を red flag と見ず**（schema 表現可能性未検） | 設計軸 |

**U-5 ↔ portfolio_has_IL = pN も consistent PASS**（私の §6 評価が持った軸）。

**⭐own（恒久・durable lesson）**: 私の supervene 6 回に共通する root = **「存在 ≠ 十分」**（resolver 存在≠ref 供給 / component 存在≠proof 供給 / golden hash 再現≠schema 完全性 / scheme 存在≠validator 被覆 / 「—」placeholder≠representable）。設計軸 verify では **機構の存在に加え、それが available data で invoke 可能・全 grade/scheme を被覆・schema-complete** まで確認する。加えて本 turn の **moving-tree near-miss**（v3 WIP を held v2 と混同しかけた）= verify-at-producing-commit を fixture にも徹底（[[feedback-pin-over-committed-state-not-dirty-tree-verify-in-worktree-2026-07-19]]）。

**cycle-2「不要」判断 = 誤り**: pN 正当に override（**B1+B2 が cycle-1+私の PASS を escape した事実自体が cycle-2 必要の証拠**）。**bounded cycle-2 = REQUIRED**。

**disposition**:
- pQ = B1-B5 を fold（worktree に **v3 WIP** 進行中: §1.4b cast table・golden 再生成〔container_dtype 込み・worktree sha `af90712a`/`9ddeafc8`/`dd14f6b6`〕等を実測 — ⚠**uncommitted・未 bank ゆえ私は v3 を verify しない**）。
- 順序（pN 指定）= **v3 fold bank → bounded cycle-2 debate → pS final-design reverify（私の次レグ）→ pN exact-pin**。
- **impl/training/authority = CLOSED 継続**。

**訂正後 verdict = ⛔HOLD（B1-B5 5/5 CONCUR・v3 fold + bounded cycle-2 → pS reverify 待ち）**。dispatch = pN concurrence（+ pQ 認識済）。**私 = v3 bank + cycle-2 完了 → pS reverify 待ち（self-start なし）**。
