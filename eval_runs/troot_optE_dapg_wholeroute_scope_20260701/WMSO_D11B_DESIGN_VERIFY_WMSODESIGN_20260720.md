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

**訂正後 verdict = ⛔HOLD（B1-B5 5/5 CONCUR・v3 fold + bounded cycle-2 → pS reverify 待ち）**。dispatch = pN concurrence（+ pQ 認識済）。**私 = v3 bank + cycle-2 完了 → pS reverify 待ち（self-start なし）**。→ §11 で reverify。

## 11. DESIGN v4 pS re-final-design verify（bounded cycle-2 fold 後・2026-07-20 12:24 実測）

pQ dispatch 12:15: bounded cycle-2（B1-B5 限定・5体）完了 → DESIGN **v4** bank（HEAD `f00c02e378`）→ §5 chain の pS 再 final-design PASS レグ + 3 点確認を依頼。

**pin（held commit `f00c02e378`・worktree==committed・git status clean = moving-tree hazard なし）**: DESIGN v4 `9087a2a6e01f042dc51d…`✅ / goldens `af90712a`/`991651b9`/`dd14f6b6`/`59bbfbba`（G-4 追加）✅ = pQ 主張一致。

**⭐load-bearing premise を on-disk 検証（durable lesson「存在≠十分」を全項適用）**:
| 検証 | v4 主張 | on-disk 結果 | 判定 |
|---|---|---|---|
| **B1 grade-locator 表**（Rs 裁定の前提事実） | locator は rank3 のみ有・SHADOW rank2 に無 | frozen JSON `proof_binding`: `artifact_hash==claim_target_hash` 束縛 = **FINAL_ARTIFACT_HASH / REPRODUCED_OUTPUT_HASH の 2 種のみ**。grade proof set 突合 → EXACT(4)無・**HASH_BOUND(3)有**・RECONSTRUCTED(2)無・DIMENSION(1)無 | ✅ **表 正確・rank4/3 逆転も実在** = **Rs escalation は true premise** |
| **option A′ 基盤** | frozen EvidenceRecord.source_ref を全 grade で束縛可 | frozen DESIGN L249/252 `class EvidenceRecord: … source_ref: str` = 全 record 存在・claim_target=tensor_binding slot hash | ✅ grounded（rank 非依存） |
| **ask③ §5 detect≠prevent** | validate_handoff は manifest を入力に取らない | frozen L375/381 `validate_handoff(invocation,offer,producer_def,consumer_def,…)` = manifest なし・§5D 照合のみ | ✅ 正確（ledger は detect のみ・prevent は schema delta=Rs） |
| **B2 goldens schema 完全性** | 全 golden container_dtype 込み・builder 検査 | `build_goldens.py --verify`（held pin・非破壊）= G-1〜G-4 全 conformance PASS・sha 一致・G-4=INT32/BOOL container | ✅ schema-complete + 再現 |

**pQ 指名 3 点回答**:
- **① C2-1 guard = 十分**: `E_BINDING_NUMERIC_STAGE_ON_BOOL`（§4「値/構造」= standalone・無条件発火）が BOOL feature への normalizer/transform/bounds を禁止。mask 無効化の failure mode（false→-1/true→+1 で両 valid）を閉じる。container cast BOOL→FLOAT32（0/1・read v≠0）は数値段でなく safe。§1.4b が BOOL→INT32 も禁止。⇒ 識別した failure mode を被覆。
- **② B1 3 択 = Rs 裁定に十分な事実を備える**: grade-locator 表を on-disk で正確確認（rank3 有/SHADOW rank2 無/rank4-3 逆転）。A（hash 由来 canonical ref・全 resolver=content-addressed store 要求・`E_BINDING_HASH_MISMATCH` が store 整合性検査に縮退）/ A′（既存 source_ref 束縛・rank 非依存・frozen 未規定意味論の解釈）/ B（frozen delta=Rs review）= 3 択が frozen 事実に grounded・trade-off 正直。CC1 単独確定不能を正しく Rs 上程。
- **③ §5 detect≠prevent 訂正 = 正確**（上表）。

**B1-B5 + cycle-2(C2-1..C2-7) fold fidelity**: 全て faithful（§12 v3/v4 map と §1-§10 本体が一致・私の read で確認）。特筆 = **B1 を silently 解決せず Rs escalation 化**（§4/§10・§2 DC-1 と §7 に BLOCKED flag）= over-claim なし。**面間整合**: B1 open が §2/§4/§7/§10 で一貫（v2 の §2 Exit⇔§5 不整合と対照的に、今回は矛盾なし）。C2-2 で `E_BINDING_CAST_LOSSY` を到達不能 code として削除（D-18 類型の再発を自己捕捉）。

**FOUNDATIONAL（dual-arm G-3/88mm §5 引用/DiffIK §1.4/コ/no-kinematic U-3）非抵触・C-1（B-internal enum・frozen enum member+0）・C-2（TimingSpec SI-only・U-3）・rule-g・rule-h（3 択は grounded・完全性を frozen 事実で裏打ち）clean**。

## 12. Verdict（v4）⛔SUPERSEDED（2026-07-20 12:51 — 正 = §13/§14）

> ⛔ 当初の v4 PASS は **pN exact-pin HOLD R1-R3（12:40）が supervene**（7 度目）。R1（cast 全単射破れ + 委譲先 grade 未被覆）= 私が §11 で C2-2 を sound と concur した際の miss（存在≠十分 の未適用）/ R2（§10 が A′ 欠落・§7 が G-4 欠落）= 私の「面間整合 一貫」主張自体の誤り / R3（--verify 非完全）= 私が「--verify PASS=schema-complete」と過信。3/3 own → v5 fold（§13/§14）。

**~~設計軸 = ✅PASS（DESIGN v4・pin `9087a2a6e01f` @ `f00c02e378`）— fold の設計軸 sound + B1 を正しく Rs escalation 化~~**（SUPERSEDED → §13）
- B1-B5 + cycle-2 fold = faithful・load-bearing premise 4/4 on-disk 検証（存在≠十分 適用）・pQ 3 点 = ①十分 ②十分 ③正確・must-fix 0。
- ⚠**B1 locator = 正当な OPEN（Rs 裁定事項・設計欠陥でない）**: §4 hash 供給レグは「設計未完」と honest に明示（§2 DC-1/§7 BLOCKED）。**Rs が A/A′/B を裁定するまで design は freeze-ready でない**。私の PASS は fold の soundness + escalation の事実正確性を確認するもので、**B1 の実体を ratify しない**（frozen 境界=Rs 専権）。
- max-2-cycles 到達（cycle-1+cycle-2）ゆえ追加 debate は Rs 裁量。B1 は debate で解けない Rs 決定。
- ⚠**two-key**: 本 PASS = 設計軸のみ・**pN exact-pin DESIGN verify を代替しない**（pN 6 度 supervene pattern 継承）。**+ freeze は Rs の B1 裁定を要する**（pS PASS → pN exact-pin → Rs B1 裁定 + freeze）。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。**私 = pN exact-pin + Rs B1 裁定 待ち（self-start なし）**。→ §13 で supersede。

## 13. pN exact-pin HOLD R1-R3 supervention + v5 re-verify（2026-07-20 12:51 実測）

pN exact-pin（12:40）= v4 に **HOLD R1-R3**、私の v4 §12 PASS を supervene（**7 度目**）。⚠**R1 は私と pQ が同じ「存在≠十分」を犯した**。held pin（v4 `9d5d44e329` / v5 `96f92af7c8`）+ frozen で全て on-disk 検証し 3/3 VALID + 私の v4 gap を own。

| # | pN finding | on-disk 検証 | 私の v4 gap |
|---|---|---|---|
| R1 (CRITICAL・全単射破れ) | INT32→FLOAT32 非単射・v4 の COMPATIBILITY_TEST 委譲が CLOSED_LOOP grade 未被覆 | float32: `16777216`==`16777217`==`16777216.0` 衝突（実測）・frozen EP: COMPATIBILITY_TEST は **rank2(RECONSTRUCTED) のみ**・CLOSED_LOOP min_grade_rank=3 → 委譲先が rank3/4 を覆わない | **C2-2(CAST_LOSSY 削除+§3 委譲)を sound と concur したが委譲先の grade 被覆を未検 = 存在≠十分 の未適用**（pQ も同型を own） |
| R2 (records) | header{1,2,3}/§7 G-4 欠落/§10 が A/B のみ(A′+normalization 脱落) | v4 で §10=A/B のみ・§7=G-1/2/3 のみ を確認 | **私の §11「面間整合 §2/§4/§7/§10 一貫」主張が誤り**（§10⇔§4 option 不一致・§7⇔§6 G-4 不一致を未照合で consistency を over-claim） |
| R3 (evidence over-claim) | builder は WCJ 完全 validator でないのに §6 がそう読める | v5 --verify に Infinity 注入 → `not a CanonicalDecimal:'Infinity'` rc=1 拒否（v4 は rc=0 通過）・self-test 24/24 fired | **--verify PASS を「schema-complete」と過信**（validator 被覆を未検 = gate-validated-under-the-bug 類型） |

**v5 fold（held pin `96f92af7c8`・tree clean・DESIGN v5 `df755007148d`・fixtures 不変〔既存 golden は禁止 cast 不使用〕）= faithful + sound**:
- **R1** = §1.4b で INT32→FLOAT32 を **⛔禁止（表セル + prose 一致 — 面間整合 実照合）**・fail-closed（INT32 は INT32 container 恒等）・将来は全 grade obligation 付き schema delta で Rs review。
- **R2** = header{1,2,3,4}・§7 に G-4・§10 が **A/A′/B × tensor_binding+normalization** に同期。
- **R3** = builder に CanonicalDecimal/NFC/64-hex 実検査（negative control 16→**24/24 発火**・Infinity 拒否 concrete 確認）+ §6 に「検査する/しない」明記・WCJ 完全性を impl `canonicalize()` leg として事前登録。
- 軽微 optional（非 blocker）: invalid corpus「表外 cast（FLOAT32→INT32 等）」の**等**が INT32→FLOAT32 を一般則で被覆・表セルも ⛔ ゆえ semantics 完全。明示列挙は cosmetic。

**B1 = 依然 open**（Rs 裁定 A/A′/B・§10 で **tensor_binding + normalization 両 slot** に拡張・grade-locator 実測 §4）。C-1/C-2/FOUNDATIONAL/rule-g/rule-h clean（v4 から不変）。

## 14. Verdict（v5）— ✅VALID（v6 delta が supersede・§15/§16。error でなく version 前進 + 私の v5 gap は §15 で own）

> v5 PASS は covered 範囲では valid。ただし pN 再判定に到達する**前**に pQ が S-1 を自検出 → v6 fold（§15）。ゆえ v5 は pN exact-pin 未到達で v6 が現行版。

**設計軸 = ✅PASS（DESIGN v5・pin `df755007148d` @ `96f92af7c8`）— R1-R3 fold faithful + sound**
- R1(cast 禁止・表/prose 一致)・R2(records sync)・R3(builder 硬化・Infinity 拒否実証)= 全て on-disk 検証・must-fix 0。今回は前回 miss(面間整合/validator 完全性)を **表セル実照合 + Infinity 注入 test** で実適用。
- ⚠**B1 locator = 依然 OPEN**（Rs 裁定・設計欠陥でない）。**freeze は Rs の A/A′/B 裁定を要す**（両 slot）。
- ⚠**two-key**: 本 PASS = 設計軸のみ・**pN exact-pin 再判定を代替しない**（pN 7 度 supervene・毎回私の後で新 surface を検出 = two-key が機能している証左ゆえ pN leg を軽視しない）。max-2-cycles 到達ゆえ追加 debate は Rs 裁量。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。**私 = pN exact-pin 再判定 + Rs B1 裁定 待ち（self-start なし）**。→ §16 で supersede。

## 15. pQ 自検出 S-1（pS v5 PASS 後・pN/pS 指摘でない）+ v6 delta re-verify（2026-07-20 13:18 実測）

私の v5 §14 PASS（`4e633489a9c2`・12:51）を pN が再判定する**前**に、pQ が自ら S-1（検証計器の欠陥・MED）を検出 → v6 fold。v5 は pN exact-pin 未到達で v6 が supersede（error でなく version 前進 + 私自身の v5 gap は下記 own）。

**Pins（held commit `81f33ceefd`・当該 6 file 全て worktree drift 無し・method=sha256sum を v5 `df755007148d` 再現で確認）**:
- DESIGN v6 = `0459a636e6722acb…` ✓ EXACT / build_goldens.py = `c74ca3b36193…` ✓ EXACT / fixtures 4本 `af90712a`/`991651b9`/`dd14f6b6`/`59bbfbba` = 不変 ✓ EXACT。

**Scope（先祖返り/先走り guard・diff 実測）**:
- design doc = 10+/4-・**全 hunk = 3 個のみ = header(`@@ -1`) + §6(`@@ -279`) + §12(`@@ -357`)**（全 hunk header 列挙で確定）。**設計 semantic 節（§1-§5,§7-§11・§1.4b cast 表/§4 grade-locator/§10 A/A′/B）は diff に一切不在** → 設計 semantics 不変。
- build_goldens.py = 37+/16-・**negative-control loop の `run_negative_controls()` 抽出 + `--verify` 経路への追加のみ**・golden 生成コード（`for name,spec,_ in FIXTURES:` write loop）無変更（∴ fixture 不変と整合・生成 semantics へのしみ込み無し）。

**S-1 fix efficacy（到達性 — doc を読まず私が実行して確保）**:

| leg | 実測（scratch 複製・held-commit 版で実行） |
|---|---|
| --verify が negative control を実走するか | `--verify .` → `negative controls: 24/24 fired` を出力 + G-1..G-4 conformance PASS（sha=banked）+ rc=0（v5 なら当該経路 0 本） |
| 非破壊 | 事後 fixture sha256 = pre と一致（`copy.deepcopy(G2)` の in-memory 変異のみ） |
| guard live（positive control） | G-1 `policy_rate_hz`←`"Infinity"` 注入 → `AssertionError: … not a CanonicalDecimal: 'Infinity'` rc=1（R3 硬化が v6 で活きている） |
| cosmetic-unchanged 判断の健全性 | INT32→FLOAT32 拒否 = CAST_OK allowlist(不在) + conformance assert(line149) + negative control(line357/list 24番目) が 24/24 に実含 ⇒ pQ の「churn 回避で不変」は 先走り隠しでなく健全 |

**面間整合（R2 教訓 実適用）**: §12 が参照する「§6 の v6 訂正ブロック」= §6 line285 に**実在**・記載実測値（`24/24 fired`・rc=0・Infinity→rc=1）は私の run と**完全一致**・§12 は私の v5 record sha `4e633489a9c2` を正引用。header v1–v6 整合。

⚠**私の v5 gap（own）**: v5 verify で私は Infinity 注入 → rc=1 を確認したが、それは**改竄ファイルへの conformance leg** の検査であり、**§6 ⑤「24/24 negative control」が `--verify` 経路で実走するか**は検証せず §6 記載を信用した。S-1 は exactly この gap。これで **R1（委譲先の到達性）→ R3（validator の経路）→ S-1（negative-control の経路）** の**同型 3 度目**。恒久教訓に追加: **「N 本発火 / guard 実在」主張の検証は、downstream verifier が使う exact command を実走し、その主張の evidence が当該経路の出力に現れることを確認せよ（doc 記載を信用しない）**。pQ が pN 到達前に自検出した点は健全（team lesson が proactive 実践へ成熟）。

**records nit（非 blocker・honest 記録）**: §12 line363 が INT32→FLOAT32 拒否の根拠を「negative control #45」と引用するが、当該 control は build_goldens.py line357（list 24番目/最終）。「#45」は ordinal でも現行 line でもなく出所不明 — **事実は真（実測済）だが label が不正確**。churn 不要ゆえ v6 での修正不要に同意するが、pN exact-pin が拾い得る（v2 debate D-29 mis-citation 前例）。

**FOUNDATIONAL（dual-arm/88mm/DiffIK/コ/no-kinematic）非抵触・C-1/C-2・rule-g・rule-h clean（v5 から不変・delta は設計 semantics 不変ゆえ再抵触なし）**。

## 16. Verdict（v6・delta）— ⛔SUPERSEDED（pN が v6 を並行 exact-pin で HOLD H1-H3・§17/§18 が正）

> ⛔ 本 v6 PASS は **未 bank のまま pN が v6 を並行 dispatch で HOLD H1-H3**（H1=その並行 dispatch 自体が pS→pN 順序違反）。**H2（wrapper fail-open）と H3（v5 行 records 矛盾）は私が v6 verify で見逃した gap**（§17 で own）。v6.1 が supersede。

**設計軸 = ✅PASS（DESIGN v6・pin `0459a636e672` @ `81f33ceefd`）— S-1 fold は tooling/records のみ・設計 semantics 不変・fix は実行で確保**
- delta scope（header + §6 + §12 + build_goldens.py）= diff 全 hunk 実測で確定・設計節不変（先祖返り/先走り 無し）。
- S-1 fix = `--verify` で `24/24 fired` + 非破壊 + Infinity→rc=1 を**私が実行して確保**（到達性を doc 記載でなく実測）。must-fix 0。
- ⚠**B1 locator = 依然 OPEN**（v5 から不変・Rs 裁定 A/A′/B × tensor_binding + normalization 両 slot）。**freeze は Rs の B1 裁定を要す**（設計欠陥でない — §4 hash 供給レグを honest に未完明示）。
- ⚠**two-key**: 本 PASS = 設計軸のみ・**pN exact-pin 再判定を代替しない**。v5 は pN 到達前に v6 が supersede ゆえ pN は **v6** を exact-pin 判定する。pN が私の後で毎回新 surface を検出してきた pattern を軽視しない。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。**私 = pN exact-pin（v6）+ Rs B1 裁定 待ち（self-start なし）**。→ §18 で supersede。

## 17. pN exact-pin HOLD H1-H3 + v6.1 delta re-verify（2026-07-20 13:2x 実測）

pN exact-pin が v6（`0459a636e672`）を **HOLD H1-H3**。⚠v6 は pS→pN の逐次でなく **pS/pN へ並行 dispatch**（13:10）されており、私の §16 v6 PASS は**未 bank・並行**ゆえ moot（H1 = その並行 dispatch 自体が順序違反）。pQ が v6.1（`0444d71f310a` @ `2c096150fc`）へ fold。**H2/H3 は私が v6 verify で見逃した gap**（H1 は pQ 手順誤り）。

**Pins（held commit `2c096150fc`・当該 6 file worktree drift 無し・method=sha256sum）**:
- design v6.1 = `0444d71f310a…` ✓ EXACT / builder = `c74ca3b36193…` ✓（**v6 から code diff = 0 行**確認）/ fixtures 4 本 `af90712a`/`991651b9`/`dd14f6b6`/`59bbfbba` = 不変 ✓。⚠HEAD は pQ dispatch 後に `f2eda5b403` へ前進（moving-tree）— pin `2c096150fc` に対して検証（held-commit 規律）。

**Scope（先祖返り/先走り guard・全 hunk 実測）**: design doc = 18+/5-・全変更 = header + §6 + §10(版参照行) + §12（4 hunk）・**全て H1/H2/H3 の records/doc/process**。**設計 semantic 節（§1/§1.4b cast 表/§2/§3/§4 grade-locator/§5/§7/§8/§10 の B1 A/A′/B content/§11）は diff に不在**・**builder code 不変** → 設計 semantics 不変。

| # | pN finding | on-disk 検証（私が実測） | 私の v6 gap |
|---|---|---|---|
| **H2**（fail-open・CRITICAL 相当） | §6 の rc=1 主張が interpreter 未指定・repo 標準 wrapper が exit を mask | **独立再現**: 破損 fixture に `python3`→**rc=1**（`not a CanonicalDecimal:'Infinity'`）/ `./isaaclab.sh -p`→**rc=0**（同一 traceback 出力しつつ）= fail-open。⇒ v6.1 §6 の fail-closed コマンド登録（素 python3・≥3.8・stdlib のみ）+ wrapper 禁止 = 正 | **positive control を素 python3 で走らせ rc=1 を得たが wrapper を試さず interpreter 依存を surface しなかった**。AGENTS.md「Exit-code exception」を常時ロードしながら自計器に未適用（pQ と同型・R1→R3→S-1→H2 の 4 度目の到達性盲点） |
| **H3**（records 矛盾） | §12 v5 行「--verify 全発火」⇔ §6「v5 verify 経路 0 本」が同時成立不能 | **構造確認**: v5 blob `96f92af7c8` main() は L359 `if verify:`→L367 `return`、neg-control ループは L386+（return の後）＝ **--verify 発火 0 で確定**。⇒ v6.1 の v5 行 records-fix「生成経路のみ/verify 未発火」= 正 | **v6 verify で §12-v6-entry ⇔ §6-v6-block の面間整合は照合したが、§12-v5-行 ⇔ §6-v5-主張 の surface pair を再走査せず矛盾を見逃した**（R2「全 surface pair 照合」の不完全適用） |
| **H1**（順序 bypass・process） | v6 を pS/pN 同時 dispatch し pS→pN 逐次を bypass | pN v6 検証は成立も pS v6 readback 未 bank で PASS-CLOSE 不成立。⇒ :6 に順序規律明記・以後 pS addendum bank 後に pN | pQ 手順誤り（私の miss でない）。**本 v6.1 addendum を bank してから pN へ回す = 是正の実行** |

**v6.1 fold = faithful + sound**: H2 コマンド登録・H3 records-fix・H1 順序規律 = 全て on-disk 実測で追認。custody 行（§12 v6.1 entry）も pN 検証内容と整合。**B1 locator は v5 から不変で OPEN**。**FOUNDATIONAL/C-1/C-2/rule-g/rule-h clean（設計 semantics 不変ゆえ再抵触なし）**。

## 18. Verdict（v6.1・delta）

**設計軸 = ✅PASS（DESIGN v6.1・pin `0444d71f310a` @ `2c096150fc`）— H1-H3 fold は records/doc/process のみ・設計 semantics 不変・H2/H3 を独立実測で追認**
- delta scope = header / §6 / §10 版参照 / §12 のみ・**builder code 不変・fixtures 不変**（diff 全 hunk 実測で確定）。設計節不変（先祖返り/先走り 無し）。
- **H2 = 私が wrapper fail-open を独立再現**（python3 rc=1 / `./isaaclab.sh -p` rc=0・同一 traceback）→ §6 fail-closed コマンド登録は必須かつ正。**H3 = v5 blob 構造**（return が control ループの前）で決着確認。**H1 = 順序是正**（本 addendum を先 bank）。must-fix 0。
- ⚠**私の v6 gap（own）**: H2（wrapper 未試行・interpreter 依存を未 surface）+ H3（v5 行 surface pair 未再走査）。到達性/経路の盲点の **4 度目**。恒久教訓に追加: **「rc/exit 主張は downstream verifier が使う exact interpreter/entrypoint で検証し、repo 標準 wrapper（`./isaaclab.sh -p`）が exit を mask しないか確認せよ（AGENTS.md Exit-code exception を自分の計器にも適用）」**。
- ⚠**B1 locator = 依然 OPEN**（v5 から不変・Rs 裁定 A/A′/B × `tensor_binding` + `normalization` 両 slot・設計欠陥でない）。**freeze は Rs の B1 裁定を要す**。
- ⚠**two-key**: 本 PASS = 設計軸のみ・**pN exact-pin（v6.1）再判定を代替しない**。H1 是正順で **本 addendum bank → pN 再判定 → Rs B1 → freeze**。
- ⭐**設計 content は v5（R1-R3）以降不変** — S-1/H1-H3 は全て verification 計器・records・process の硬化であり設計 semantics に触れていない。設計は収束済で、残 churn は harness 健全性のみ。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。**私 = pN exact-pin（v6.1）+ Rs B1 裁定 待ち（self-start なし）**。→ §20 で supersede（v7 = Rs A′ の semantic fold）。

## 19. Rs 裁定 A′ の v7 fold — 設計 semantic verify（2026-07-20 15:0x 実測）

⭐**Rs が B1（hash 供給 locator）= A′ を裁定**（14:39・frozen `EvidenceRecord.source_ref` を束縛）。⚠**v6.1 で chain 初の完全 two-key close 成立**（pS `251e8c8516f2` @ `ed60396e88` / pN exact-pin PASS-CLOSE `a31498dd0582` @ `ccff616b89`・14:35 — **pN も私の H2 fail-open を独立再現**: Infinity 注入 direct rc1 / `./isaaclab.sh -p` traceback+rc0）→ Rs A′ → **v7**（`6bbf64b3575f` @ `a8b9d4004a`）。**v5 以来はじめて設計 semantic 節（§2/§4/§7/§10）に触れる** ⇒ v6.1 two-key は v7 を覆わず、**full semantic verify**（delta scope でない）。

**pins（held commit `a8b9d4004a`・6 file worktree drift 無し・method=sha256sum）**: design v7 `6bbf64b3575f` ✓ EXACT / builder `c74ca3b36193`（不変・code diff 0）✓ / fixtures 4 本不変 ✓。**Scope**: design doc 51+/9-・touched = header + §2（DC-1 unblock）+ §4（A′ 確定形 +30 行）+ §7（test）+ §10（B1 CLOSED）+ §12（v7 entry）。設計 semantic 変更ゆえ内容を frozen に対し on-disk 実測（frozen sha 一致: DESIGN `00192d20ca00` / EP JSON `e63176af9bc3` / EP md `c474acea7c58`）:

| A′ 主張 | frozen 実測（私） | 判定 |
|---|---|---|
| `expected_sha256`=claim_target_hash（凍結側束縛済） | EP JSON `claim_targets`: TB→`execution_bundle.tensor_binding.artifact_hash` / NORM→`…normalization.artifact_hash`・不一致=E_PROOF_MISBOUND（frozen `:253`） | ✓ |
| `ref`=`source_ref`（B 側束縛=B1 実体） | `:252 source_ref: str`（非 Optional）/ `:269 records: tuple[EvidenceRecord]`（全 component が record）/ `:551` source_ref=hashed（差替→evidence_bundle_hash に出る=tamper-evident） | ✓ **全 grade に locator**（rank3 限定旧表を解消） |
| ArtifactSlot に ref 無（B1 root） | `:51 ArtifactSlot={state, artifact_hash}` ref field 無し | ✓ |
| source_ref 指示対象=frozen 未規定（non-delta） | EP JSON source_ref=0 / EP md（`c474acea7c58`）source_ref=0（閉じた query） | ✓（N-1 参照） |
| E_BINDING_ARTIFACT_UNRESOLVED 撤回→frozen E_PROOF_ARTIFACT_UNRESOLVED | frozen `:615`/`:285` に実在・v7 の撤回 code = closed query で **active 宣言 0**（4 箇所全て strike/撤回文/SUPERSEDED-`<details>`/§12 記録） | ✓ 面間整合 |
| EXPLICIT_NONE 免除・UNKNOWN 非免除 | EP JSON `exemption_reporting.explicit_none="recorded loud in UsageEligibilityReport.exemptions"` / `unknown_slots="never exempt"` | ✓ |

⭐**profile 非対称を私が独立実測で追認**: OFFLINE_REPLAY は **TB を `not_applicable`「replay does not re-execute binding」・NORM は required**（CLOSED_LOOP rank3 / SHADOW rank2 は両 required）。加えて proof_policy も EXACT/TB=[MANIFEST,COMMIT,CONFIG] vs EXACT/NORM=[…,NORMALIZER_HASH] と非対称。⇒ **v7 §4 表の slot 分離は正**。⚠**私の v4-v6.1「両 slot 同型」PASS は不正確**（locator-gap の同型は検証したが per-slot profile 適用を未測＝存在≠十分 / 全 surface 未照合の再発。A′ は壊れない=source_ref は required record 毎に locator 供給）。**own**。

**先祖返り/先走り**: v7 は A′ を faithful 実装（A/B に戻さず）・§10 B1 を CLOSED 化・旧上程資料は `<details>` SUPERSEDED に正しく格納（active §10 と矛盾せず）・§7 到達性負例は「impl leg で実証必須」と honest（freeze-ready を主張せず）。**FOUNDATIONAL 非抵触**（source_ref=evidence provenance・control/geometry/kinematic 不触・ControlMode 不変）・**rule-g**（Rs A′ を反映・C-1 custody 条件付）・**rule-h**（profile 全列挙・subset 一般化なし＝むしろ旧 over-generalization を訂正）。

**条件（fold 欠陥でなく downstream custody/records）**:
- **C-1（custody）**: **Rs の 14:39 A′ 裁定の standalone verbatim が未 bank**（v7 doc + pQ relay のみ・grep で独立 Rs 記録 0）。pN PASS-CLOSE transcript は bank 済（`ccff616b89`）なのと対照。freeze は A′ を Rs 権威で確定するゆえ **freeze 前に Rs A′ verbatim を bank 推奨**（過去の pN transcript custody flag と同型）。
- **C-2（records freshness）**: **LEDGER D1.1 行 + DDR #27 が stale** — 両者「B1 BLOCKED / Rs 裁定待ち」+ #27 は「normalization slot も同型」（v7 が訂正した非対称）のまま。B1 CLOSED/A′ + 非対称を反映要（確定事項即反映 gate・**#27 は D1.1-C [DEFER-RECON] を gate** ゆえ特に）。
- **N-1（minor・非 blocker）**: frozen DESIGN `:396` は source_ref を migration-fixture provenance に使用 ⇒ v7 §4「frozen 一切規定していない」は「**TB/NORM の artifact 解決用途で未規定**」に scope 限定が精確（A′ は provenance role と整合する refinement ゆえ依然 non-frozen-delta）。

## 20. Verdict（v7・A′ fold）

> ⛔**INVALIDATED（2026-07-20 15:55 Rs A′ 破棄・§23）**: 本 verdict は Rs の A′ 裁定を前提とするが、Rs が「誤りが前提であるならそれは当然破棄にしろ」で A′ を破棄。B1 = 再 OPEN。measurement（source_ref/claim_targets/profile 非対称）は retained（§23）。

**~~設計軸 = ✅PASS-WITH-CONDITIONS（DESIGN v7・pin `6bbf64b3575f` @ `a8b9d4004a`）— Rs 裁定 A′ の fold faithful + sound・B1 CLOSED~~**（INVALIDATED → §23）
- A′ 全前提を frozen（sha 一致）に対し on-disk 実測（source_ref 必須/全 record/hashed・claim_targets 両 slot・E_PROOF_* 実在・EXPLICIT_NONE 免除・source_ref 未規定 closed query）・fold は A′ を faithful 実装・must-fix 0。
- ⭐**profile 非対称（OFFLINE_REPLAY: TB 免除/NORM required）を独立追認** → v7 §4 分離は正・**私の v4-v6.1「両 slot 同型」の不正確を own**（locator 同型は真だが profile 適用は未測）。
- error-code reuse-first（E_BINDING_ARTIFACT_UNRESOLVED 撤回・closed query で active 0）+ E_BINDING_HASH_MISMATCH 限定 + §7 到達性負例必須（R1 教訓の自適用）= sound。
- **条件（downstream・fold 欠陥でない）**: **C-1** Rs A′ verbatim 未 bank / **C-2** LEDGER+DDR #27 stale（B1→CLOSED/A′ + 非対称）/ **N-1** §4「frozen 未規定」scope 精確化（非 blocker）。§7 到達性負例 = impl leg。
- ⚠**two-key**: 本 PASS = 設計軸のみ・**pN exact-pin（v7）再判定を代替しない**（pN が semantic 変更を exact-pin 判定）。H1 順序で **本 addendum bank → pN exact-pin（v7）→ Rs freeze**。
- ⚠**freeze gate**: v6.1 と異なり B1 は CLOSED（Rs A′）ゆえ freeze の残 gate = **pN exact-pin（v7）PASS-CLOSE + C-1/C-2 custody 反映**。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。**私 = pN exact-pin（v7）待ち（self-start なし）**。→ §21/§22 で条件 C-1/N-1 処理（v7.1）。

## 21. 条件 C-1/N-1 の v7.1 fold + Rs 裁定 custody 評価（2026-07-20 15:16 実測）

pQ が私の v7 条件 **C-1（Rs 裁定 custody bank）+ N-1（scope 限定）を v7.1 に fold**（C-2 は p6 へ dispatch）。**pins（held `b53c9e5e4d`・6 file drift 無し・method sha256sum）**: design v7.1 `9b0c229a06` ✓ EXACT / Rs 裁定 custody `20d88fc1b3` ✓ EXACT / builder `c74ca3b36193` 不変 ✓ / fixtures 4 本不変 ✓。**design delta = 8+/3-・header + §4（N-1）+ §12・builder 0**。

**N-1 fix = faithful**: §4「束縛の宣言」の**束縛内容は不変**（source_ref が slot artifact を解決する ref = 同一・diff で確認）・justification のみ scope 限定（frozen `:396` が source_ref を registry-fixture provenance に使うゆえ「一切規定せず」→「**TB/NORM の artifact 解決用途で未規定**」+ A′ は provenance role と整合する refinement）・非 frozen-delta 結論不変。pQ が根因（**closed query が frozen DESIGN 本体を含まず EP md/JSON のみ対象**）を own。⇒ 設計 semantic の追加変更 0。

**C-1 custody = RESOLVED（exemplary）**: Rs A′ 裁定を `WMSO_RS_B1_RULING_APRIME_20260720.md`（`20d88fc1b3`）に bank。評価:
- ⭐**honest scope**: 裁定 = single-select ゆえ Rs prose 無し → 「問い + 選択肢文言 + 選択」を逐語保持し **prose 引用を捏造しない**旨明記（records-must-match-fact / [[feedback-human-gt-is-fetched-not-cited-2026-07-14]] 遵守）。
- ⭐**「(推奨)」は CC mark で Rs の語でないと明記**（framing 影響を開示）。§4 境界（裁定は impl/training/authority を解錠せず・freeze でなく・§4 逐条検証を意味しない）明記。
- ⚠**custody の限界**: single-select ゆえ ground truth は pQ の忠実記録に依存（Rs-authored artifact は format 上存在しない）。honest scope でこの限界自体が開示済 = 現 format で最善の custody。

⭐**不正確前置きの独立評価（rule-g）**: 問いの前置き「両 slot に同型で効く」は不正確（profile 非対称）と custody record が loud 開示。**私の評価 = 当該不正確は A/A′/B 選択に orthogonal ゆえ Rs の A′ 裁定は STANDS**:
- 選択に効く前置きの accurate 部分（ArtifactSlot に ref 無・locator rank3 限定・**locator-gap の同型**）は全て真。
- 不正確部分（profile 対称性）は「どの profile が slot を要求するか」の軸で、選択（locator **供給機構** A/A′/B）と**独立**。A′ は source_ref を required record 毎に locator 供給ゆえ非対称でも壊れない・A/B も非対称に favor されない。
- ⇒ Rs は対称/非対称いずれでも A′ を選ぶ。**再裁定は不要**（immaterial）。ただし freeze 時に訂正 framing を Rs へ surface し「A′ stands」を軽く confirm 推奨（Rs 権威尊重・私の materiality 評価への veto 余地）。

**残条件**: **C-2**（LEDGER + DDR #27 の B1→CLOSED/A′ + profile 非対称 反映）= p6 へ dispatch 済・**freeze 前反映要**（#27 は D1.1-C [DEFER-RECON] を gate）。

## 22. Verdict（v7.1・delta）

> ⛔**INVALIDATED（2026-07-20 15:55 Rs A′ 破棄・§23）**: ⭐**§21 の orthogonality 分析（「A′ STANDS」）は不当** — 誤った前提を出した側が、その誤りが Rs 判断に効かなかったと判定できない（§23）。C-1 custody record が記録した A′ 裁定も破棄対象。N-1 の measurement（frozen :396）は retained。

**~~設計軸 = ✅PASS（DESIGN v7.1・pin `9b0c229a06` @ `b53c9e5e4d`）— C-1/N-1 処理 faithful~~**（INVALIDATED → §23）
- N-1 = justification の scope 限定のみ（束縛内容不変・非 frozen-delta 結論不変・根因 own）・diff で binding 不変を確認。C-1 = Rs 裁定 custody bank = **exemplary**（single-select honest scope・prose 捏造せず・(推奨) 開示・境界明記・限界も自己開示）。builder/fixtures 不変。
- ⭐**不正確前置き（両 slot 同型）= custody が loud 開示 + 私の独立評価 = A/A′/B 選択に orthogonal ゆえ A′ STANDS**（accurate 部分＝locator-gap 同型が選択に効く・不正確部分＝profile 対称性は独立）。freeze 時に Rs へ訂正 framing surface + 軽 confirm 推奨（再裁定不要）。
- **残条件**: **C-2**（LEDGER/DDR#27 反映）= p6 dispatch 済・freeze 前要。
- ⚠**two-key**: 本 PASS = 設計軸のみ・**pN exact-pin（v7.1）を代替しない**。freeze 残 gate = pN(v7.1) PASS-CLOSE + C-2 反映。
- **impl/training/authority = CLOSED 継続**。dispatch = pQ。**私 = pN exact-pin（v7.1）待ち（self-start なし）**。→ ⛔§23 で INVALIDATED（Rs A′ 破棄）。

## 23. ⛔Rs が A′ 裁定を破棄 — 私の orthogonality 分析は不当（2026-07-20 15:57 実測）

**Rs 裁定（pQ relay・15:55:58）逐語**: 「誤りが前提であるならそれは当然破棄にしろ」⇒ **A′ 裁定を破棄**。Rs は私の §21/§22 orthogonality 分析（裁定 STANDS）と pQ の同意を**両方 overrule**: **誤った前提を出した側が、その誤りが Rs の判断に効かなかったと判定することはできない**。

**私の error（own・番人としての中核的失敗）**:
- 私は Rs の single-select に**何が効いたかを Rs に代わって判定**した（materiality は decision-maker 専権・私に standing 無し）。
- **誤りを出した側が「無害」を self-certify** した = 利益相反・[[feedback-refutation-is-self-certifying-agreement-is-not-2026-07-14]] 違反（pQ の同意も独立確認でない・[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test-2026-07-14]]）。orthogonality 論は「都合の良い結論の確証」で、否定証拠を先に探す規律（anti-確証バイアス）に反した。
- ⭐**meta-failure**: 私の banked lesson [[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]] の **human-decision 版そのもの** — 偽の前提の下で下された裁定は「偽の前提に validate されている」。remedy は正しい前提での**再裁定**であり、error-producer/downstream verifier の事後無害論ではない。lesson を持ちながら人間決定 case に適用しなかった。
- ⭐**番人 role の反転**: 「裁定が偽の前提の下で下された」を検出した時、正しい stewardly action = **⛔tainted ゆえ正しい前提で再上程を要する**（結論を pre-judge しない）。私は逆に「STANDS」を構築し §21/§22 で「再裁定不要」と書いた = 先祖返り/先走り抑制の逆。

**恒久教訓（v7.1 の「materiality 独立評価」lesson を訂正・置換）**: human 決定が後に偽と判明した前提の下で下された時、**auto-accept も、error-producer による orthogonality/無害 判定もしない**。前提の偽が裁定を tainted にする（materiality 判定は decision-maker 専権ゆえ error 側が下せない）。**正しい前提を明示して再上程し、結論を pre-judge しない**。

**invalidation scope**:
- §19/§20（v7 A′ verify + verdict）+ §21/§22（v7.1 条件処理 + orthogonality）= **INVALIDATED**（A′-premised）。C-1 が bank した Rs A′ 裁定（`WMSO_RS_B1_RULING_APRIME`）も破棄対象。
- **retained（Rs 明示）**: 独立実測は保持 — source_ref `:252`/`:269`/`:551`・claim_targets 両 slot・**profile 非対称**（OFFLINE_REPLAY TB 免除/NORM required・proof_policy も非対称）・frozen `:396`（source_ref=provenance）・ArtifactSlot ref 無 `:51`。これらが A/A′/B 再上程の**正しい前提**を成す。
- v6.1 の two-key PASS-CLOSE（pS `251e8c8516f2` / pN `a31498dd0582`）は A′ 以前ゆえ**有効**（B1 を OPEN として扱う版）。

**現状**: **B1 = ⛔OPEN**。pQ が正しい前提（profile 非対称を明示）で A/A′/B を再上程。**Rs 指示「再裁定まで設計軸 verify は保留」ゆえ、私は再上程を待って verify を保留**（self-start なし）。impl/training/authority = CLOSED 継続。dispatch = pQ（本 record を bank 対象に含める）。

## 24. B1 premise claim-set の独立検証（2026-07-20 17:10 実測）

Rs の A′ 破棄後、pQ が **B1 前提 claim-set**（evidence artifact・選択肢/推奨 0・`WMSO_D11B_B1_PREMISE_CLAIMSET_RSTECHLEAD2_20260720.md` `41c6b1df54` @ `52aa75176f`・pin EXACT・clean）を作成 = 前回 Rs へ渡した 4 前提を裁定質問から分離し検証可能化。⚠**本検証は純粋な premise-fact 照合（materiality/選択判定を一切含まない — Rs 破棄の教訓の直接適用）**。frozen sha 全一致（DESIGN `00192d20ca00` / EP JSON `e63176af9bc3` / EP md `c474acea7c58` / prereg `ffd06623e22f`）。

| claim | pQ 実測 | 私の独立検証 |
|---|---|---|
| **C1** ArtifactSlot に ref 無 | TRUE | ✅ **TRUE** — 全 4 file の closed query で ArtifactSlot に ref/locator/path/uri 付与 = 0（def `:51` `{state, artifact_hash}` のみ） |
| **C2** locator rank3 のみ→under-scoped | 訂正形 TRUE | ✅ (a) `ProofItem.ref: str` 必須 ✓ (b) TENSOR_BINDING は 4 evidence grade で非空 ✓（UNKNOWN=空は無 proof で整合）(c) `artifact_hash == claim_target_hash` **直接**束縛 = FINAL_ARTIFACT_HASH/REPRODUCED_OUTPUT_HASH の 2 種＝rank3(HBR) ✓。⛔~~私の REFINEMENT「rank4 で間接確立ゆえ rank3 のみ不完全」~~ = **撤回（pN V2-B1・§24 訂正表）**: hash **association**（軸A・TRAIN_RUN_MANIFEST 等が rank4 で claim_target を列挙）と target-byte **locator**（軸B・ref が target 実体を解決）は別軸。B1 は軸B ゆえ **原形「rank3 のみ」が正**。私は 2 軸を混同した |
| **C3** slice の EP profile 未規定 | TRUE（不在） | ✅ **TRUE + refinement**: prereg で SHADOW/CLOSED_LOOP/OFFLINE_REPLAY/profile = 0（再現）。**広域反証（charter/RL-Routing/LEDGER/node/D0/SOMA/全 prereg）でも slice の EP evidence profile を pin する記述 0**。⚠**(N-A) 用語衝突** — charter `:13`「boundary-only or real-time **execution** profile」は execution 軸（project は real-time を retain）で EP evidence profile と別（C3 は後者を測っており正）。⛔~~**(N-B) DC-1 が CLOSED_LOOP を除外し SHADOW/OFFLINE に限定**~~ = **撤回（pN V2-B2・§24 訂正表）**: prereg:18 着手順 = B→C→slice ゆえ slice は B/C **後**に走り、DC-1（pre-B 排除）は適用されず **3 profile とも未決**（C3 の「完全未決」を**強める**、限定ではない）。私は prereg:18 を目にしながら run-timing の含意を誤読 |
| **C4** 両 slot 同型 | 偽（訂正形で成立） | ✅ **原形 FALSE / 訂正形 TRUE** — OFFLINE_REPLAY: TB=not_applicable / NORM=required（他 2 profile は両 required）・proof_policy も EXACT で NORM のみ NORMALIZER_HASH+FINAL_ARTIFACT_HASH。locator gap 構造は同型・profile/proof 適用は非対称 |

**完全性**: custody record 質問（§2）は C1(ref無)+C2(rank3 locator)+C3(slice=SHADOW rank2)+C4(両slot同型)を逐語含む ⇒ **C1-C4 = Rs へ渡した事実主張の完全集合**（漏れ 0）。

**consequence（pQ 主張）評価**: 「C3 未決 + C2 訂正で rank2-locator 動機づけ不成立 ⇒ 前提確定まで選択肢集合を確定できない」= **SOUND**。私の C2 refinement（rank4 間接確立）+ C3 refinement（DC-1 + run-timing 未決）が consequence を**強める**（未決 premise が記載より多い）⇒ **本 artifact が選択肢を提示しないのは正しい**。

**未測定への追加事実（pQ の deferred NORM に関連）**: NORM の EXACT proof set は **FINAL_ARTIFACT_HASH（直接束縛）**を含む一方 TB の EXACT は含まない ⇒ **rank4 での直接/間接も slot 間で非対称**（NORM 測定時に反映すべき）。

**役割の境界（Rs 破棄の教訓を適用）**: 本検証は on-disk fact の照合のみ。**A/A′/B の選択・materiality・profile 決定は一切判定しない**（premise 確定=Rs、profile 決定=Rs/VT-DESIGN）。**B1 = OPEN 継続**。私 = 正しい前提での再上程を待って verify 保留（self-start なし）。impl/training/authority CLOSED。

### §24 訂正 — pN EVIDENCE HOLD V2-B1..B4（私の refinement over-reach、on-disk で pN 正を確認・2026-07-20 17:30 実測）

pN が claim-set v2（私の §24 refinement を fold した版）に **V2-B1..B4** を出し、**私の §24 の 2 refinement（C2 の rank4・C3 の N-B）が over-reach**と判明。全 4 点 on-disk 確認 = pN 正。⚠**前回の materiality 越権とは別種の失敗** = verifier として under-grounded な「refinement」を足し、正しい premise を濁した（観察「X を見た」から推論「ゆえに premise は Y」へ grounding 無しに飛んだ）。上表 C2/C3 セルに strike 反映済。

| # | pN 指摘 | on-disk 確認（私） | 私の §24 error |
|---|---|---|---|
| **V2-B1 (CRIT)** | hash **association** と target-byte **locator** は別軸 | TRAIN_RUN_MANIFEST rule=`artifact_hash=manifest sha256; manifest lists claim_target` ⇒ ref は **manifest bytes** を解決（target 実体でない）/ TRAIN_TIME_CRYPTO_BINDING は blob 自身。FINAL/REPRODUCED のみ `artifact_hash==claim_target`＝ref が **target 実体**を解決 | **C2 refinement 撤回**: 私の「rank4 で claim_target 確立ゆえ rank3 のみ不完全」は **軸A(association)**。B1 は **軸B(target-byte locator)** で軸B では **原形「rank3 のみ」が正**。2 軸混同 |
| **V2-B2 (CRIT)** | DC-1 は pre-B early run のみ排除 | prereg:18 着手順 = **B→C→slice** ⇒ slice は B/C **後**に走る ⇒ DC-1（pre-B 完了排除）適用されず **CLOSED_LOOP 排除されない・3 profile 未決** | **N-B 撤回**: 私の「DC-1 が CLOSED_LOOP 除外」は誤り。prereg:18 を目にしながら run-timing の含意を誤読（**転記/伝播前に読め の再発**）。正 = 3 profile 全開＝C3「未決」を**強める** |
| **V2-B3** | locator-gap 同型 = schema 層のみ | schema 層（ArtifactSlot ref無・claim_targets 束縛）同型 / **end-to-end 非対称**: NORM の EXACT は FINAL_ARTIFACT_HASH（rank4 直接 locator）在・TB は無 | **「locator gap 同型」を schema 層限定に訂正**、end-to-end FALSE（私の §24「追加事実」の NORM/TB rank4 差が exactly これ — 観察したが「同型」訂正に繋げず） |
| **V2-B4** | C4 反証条件が自己矛盾 | CLOSED_LOOP/SHADOW は既に両 required で「一致」⇒ 条件常時発火し (b) を偽化 | claim-set 側 fix（「**OFFLINE_REPLAY でも一致すれば FALSE**」へ）。私は C4 真偽は検証したが**反証条件の coherence を未検査** |

**訂正後の premise（正）**: C1=TRUE / **C2**=軸B(locator)は **rank3 のみ**（原形正）・軸A(association)は rank3+rank4（2 軸分離）/ **C3**=slice の EP profile **完全未決**（3 profile 全開・DC-1 は bound しない）/ **C4**=schema 同型・end-to-end 非対称。**consequence（前提確定まで選択肢不能）= 変わらず SOUND**（私の誤 refinement を除いても C3 完全未決で locator が覆う grade/profile が定まらない）。

⭐**恒久教訓（verifier refinement over-reach）**: verifier の第一義務は claim を on-disk で **clean に確認/反証**すること。**refinement/elaboration を足す時、その結論を primary claim と同等に grounding せよ** —「X を観察した」は「ゆえに premise は Y」を grounding 無しに licenses しない（推論は別 claim）。正しい premise を under-grounded な refinement で濁すのは net-negative。技術面: **hash association ≠ target-byte locator**（hash 値の確立 ≠ 実体を fetch する ref）を分離せよ。[[feedback-an-absence-claim-must-be-read-not-relayed-2026-07-15]]（prereg:18 を読まず伝播）+ [[feedback-the-boundary-question-and-the-identity-question-are-different-2026-07-15]]（軸A/軸B）。

**pN 指定順**: pS §24 訂正（本節）→ 先 bank → claim-set 再 bank → pN 再依頼。dispatch = pQ。**私 = claim-set 再 verify 依頼を待つ（self-start なし）**。impl/training/authority CLOSED。
