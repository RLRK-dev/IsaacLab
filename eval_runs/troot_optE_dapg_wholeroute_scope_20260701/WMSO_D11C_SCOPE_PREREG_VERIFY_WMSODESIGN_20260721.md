# WMSO D1.1-C `artifact_manifest` 詳細 scope prereg v1 — 設計軸 verify（pS MWSO-DESIGN）

- node: `T-WMSO` D1.1-C; 検証者 = `w2:pS` MWSO-DESIGN（0-commit・bank は pQ/他）。作成 = 2026-07-21 12:43 JST（shell 実測）。
- **検証対象** = `WMSO_D11C_SCOPE_PREREG_RSTECHLEAD2_20260721.md`（prereg v1）。依頼 = pQ 12:36 dispatch（設計軸 verify 3 点 + L 判定）。
- **私の軸 = 設計軸のみ**: 凍結忠実 / IN-OUT 境界（機構-policy 線）/ 他所管への越境 / 先祖返り・先走り。⛔**evidence 軸（pin exact 照合の正式判定・DDR 全 35 対応・OUT 過小審査）= pN 相当（現 pY）**。⛔**scope 承認（design authoring 解錠）= Rs**。本 PASS は機構・scope 設計を批准するのみで authority を解錠しない。

## 1. pin 検証（全て on-disk・producing commit で自算・dispatch 値を信用しない）

| pin | dispatch 値 | on-disk 実測 @ commit | 一致 |
|---|---|---|---|
| prereg @ `1860edcc1c` | `d9caaffcf29d9524` | `d9caaffcf29d9524cc85340701e7712ca4786ea61b244fbd9cc36c822b7c575f` | ✅ |
| DEFER-RECON @ `7effeb774f` | （filename のみ・sha 未提示） | `94c3fd2195a5981abdee7fc4b0eb7b5de39a192c419e9c24a0c44ea341ad5928` | ✅（自算・7effeb774f と 1860edcc1c で同一＝介在改変なし）|
| contracts_v2（凍結） | `00192d20ca00b654` | `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` | ✅ |
| EP md（凍結） | `c474acea7c58acc2` | `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` | ✅ |
| EP JSON（凍結） | `e63176af9bc3a246` | `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e` | ✅ |
| tensor_binding v13（凍結） | `5a1874d3be8b98b8` | `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` | ✅ |

- commit 実在確認: `1860edcc1c` = "Bank the D1.1-C detailed scope prereg (v1)" / `7effeb774f` = "Bank the D1.1-C DEFER-RECON"。全 pin 誠実（今回 fabricate なし）。
- ⚠ **start-authority「Rs 逐語 go」= pQ の transcription**（私は Rs channel に居らず逐語を独立検証しない）。私の PASS は prereg の scope 内容に対する設計軸判定であり、start 承認・scope 承認は Rs / pY の軸。

## 2. 凍結忠実（pQ 点3）— ✅ 忠実・暗黙の schema delta 要求なし

- **`substrate_id` = 凍結 B→C の明示 carry**（先祖返り・越境・暗黙 delta のいずれでもない）:
  - 凍結 tensor_binding v13 `:376` 逐語「U-3（drive-substrate lineage）= B に導入しない … **data の substrate 識別 = D1.1-C `substrate_id`**。必要が判明したら schema delta として Rs review 経由」。
  - 凍結 contracts_v2 `:570` carry「旧 contaminated log は明示 **substrate_id** を付け silent pooling 禁止」/ `:571(c)` 「drive-substrate lineage を provenance 型で明示する必要が生じた場合は D1.1-B/C の schema delta として Rs review 経由」。
  - ⇒ D1.1-C が `substrate_id` を manifest 機構として導入するのは**凍結 B が C に手渡した当のもの**。契約層束縛が要る場合の delta は prereg §3-4 / §0 が OUT（Rs review）に置き、**凍結自身の指示と一致**。
- **U-6 の delta-free 経路が成立**: 凍結 contracts_v2 `:151` `SemanticFieldSpec` = {field_id, dtype, shape, unit, frame}・`Dtype = {FLOAT32, INT32, BOOL}` = 数値専用。categorical な `chain_topology_class` は `SemanticFieldSpec` に格納不能 ⇒ manifest metadata として記録（IN）が非-delta 経路・契約層束縛（delta）は OUT が正しい。
- 凍結 4 file の byte は §1 で全一致・prereg は編集していない。§0 の「schema delta を導入しない・必要なら supersession+Rs review へ escalate」= 正しい規律。

## 3. 機構 / policy 線（pQ 点1）— ✅ 正しく切れている

- pQ が挙げた 4 項目すべてで線は一貫: **記録・区別（機構=IN）** vs **使用・判断・執行・契約層束縛（policy / authority / delta=OUT）**。

| 項目 | 機構（IN） | policy/authority/delta（OUT） | 判定 |
|---|---|---|---|
| substrate_id | 付与・区別・silent pooling 禁止 | どの substrate を採用/破棄か（#26 Rs 裁定） | ✅ |
| U-2 (#28) | run 毎に producer artifact を pin する記録 | certificate 下での差替え阻止（closed-loop 実装） | ✅ |
| U-5 (#29) | 両段 binding の記録（`E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` 解消経路） | demo の再記録（p4/p0 lane・実体） | ✅ |
| U-6 (#30) | `chain_topology_class` を metadata 記録 | 契約層束縛（schema delta⇒Rs review） | ✅ |

- ⭐**#26 の outcome 非依存性（DEFER-RECON §3.1 の核心）が設計軸で妥当**: IN 各項（1 manifest hash 結合 / 2 substrate_id 区別 / 3 grade 別 proof 写像 / 4 JCS 展開 / 5 U-2/U-5/U-6 記録）は **#26 のどちらの裁定でも同一**。#26 に依存する唯一物（選別 policy = どの substrate を使うか）は §3-1 OUT。⇒ FOUNDATIONAL 依存 #26 が IN scope を地面無しにしていない ⇒ **着手可は妥当**。
- **silent pooling 禁止は #26 に中立**: ラベル付け強制は「汚染を使ってよいか」の結論に依らず、**どちらの裁定も監査可能にする前段**。裁定を焼き込まない・むしろ実行可能にする。この論理は健全。

## 4. 他所管への越境（pQ 点2）— ✅ なし

- **合成 schema delta（`SkillCompositionDefinition` / barrier / region postcondition）= pX 所管** → §3-5 OUT。`normative closure = NOT YET` の表記は「pQ review 準備完了だが未批准/未凍結」を正確に反映（先走りなし）。私の合成 form も未批准であり、この表記と整合。
- **腕参加の機械宣言（F4）の source 設計 = p5 所管**（p4 routing 12:33）→ §3-9 OUT。⚠ 私の合成 form §3 は合成層の**検査**（各腕の資源 claim 非空）を定義し、F4 の **source**（各 skill がどう資源を宣言するか）は p5 の skill 詳細。両者は別レイヤで衝突しない。pQ の manifest はどちらにも触れず OUT に置く＝正しい。

## 5. L 判定（pQ 依頼「triage 自体も確認」）— ✅ L2 妥当・むしろ保守側

- 質的トリガ「新規ファイル作成」該当 ⇒ **L2**（行数 66 は L1 の ≤50 を超えるが、質的トリガが line 数に優先）。凍結非編集・公開 API 境界不変・reward/env/success/physics/phase いずれの L3 diff pattern も非該当・§0 不変前提 非該当 ⇒ L3 auto-escalation なし。
- **two-key（設計軸 pS + evidence 軸 pN/pY）+ CC Debate を design 段へ deferred** = D1.1-A/B 先例と同型（prereg=SCOPE CONCUR two-key / CC Debate=design authoring）。scope-prereg は field 名・型・hash 順序を確定しないため debate が噛む対象が無く、design 段発火が正しい。
- ⚠ **L2 の 5 体 CC Debate 義務は waived でなく deferred** — design authoring で必ず発火させること（本 prereg で消えない）。

## 6. 先祖返り / 先走り — なし

- **先祖返り なし**: 凍結 A + B v13 の上に構築・A′ / 旧 model の復活なし・合成は「未批准」と正しく表記。
- **先走り なし**: design authoring は Rs scope 承認を要する（§5-3・自己解錠しない）。#26 選別 policy は焼き込まず carry。pN→pY OPS-SUP 移譲を §5-2 が正しく反映。impl/training/closed-loop authority は OUT-6 で CLOSED 継続。

## 7. precision note（非-blocking）+ design 段 watch（既に OUT で正しく囲われている）

- **P-1（design/impl 語の曖昧さ）**: IN-2「検出・拒否の **code** を含む」と IN-4「package・CI の**最終整備**」は、OUT-6（implementation=CLOSED）と読み方が触れ得る。§3-6 が implementation を OUT に置く以上、意図は **error-code / 拒否規則の設計** と **package/CI 構造・check の仕様**（＝設計レベル）と読むのが自然（D1.1-B が `E_BINDING_*`/`E_PROOF_*` を実装せず設計したのと同型）。⇒ **design doc で「code = error-code/拒否規則（設計）」「package/CI = 構造・check の仕様（build でない）」と明記**を推奨。prereg 段の欠陥ではない（IN/OUT の内的整合の明確化）。
- **W-1（design 段 watch・機構/policy 線の最鋭漏出点）**: substrate 拒否機構は **不在/silent pooling のみ拒否**（substrate_id 欠落・無ラベル混在 → `E_SUBSTRATE_*`）でなければならず、**substrate の値に基づく拒否**（汚染だから弾く）を入れると #26 選別 policy を先取りする。prereg §3-1 は値選別を正しく OUT に置いており、**design でこの OUT を機構が守るか**を確認する（prereg 段の欠陥ではない・最も漏れやすい 1 点の明示）。
- **W-2（design 段 watch）**: U-6 metadata 記録が真に delta-free か（`chain_topology_class` を凍結型に押し込まない）を design で確認。現時点で成立見込み（`SemanticFieldSpec` 数値専用ゆえ）。

## 8. 判定

✅ **DESIGN-AXIS PASS（scope prereg v1）**。

- 凍結 4 file に忠実・`substrate_id` は凍結 B→C の明示 carry・暗黙 schema delta 要求なし（§2）。
- 機構/policy 線は 4 項目すべてで正しく切れ、#26 の outcome 非依存性が設計軸で妥当 ⇒ 着手可は正当（§3）。
- pX 合成 / p5 F4 への越境なし（§4）。L2 triage 妥当・保守側・CC Debate は design 段へ deferred（§5）。先祖返り・先走りなし（§6）。
- non-blocking = P-1（design/impl 語の明確化）; design 段 watch = W-1（不在拒否であって値拒否でない）/ W-2（metadata delta-free）。いずれも prereg で正しく OUT に囲われており、design 段の確認事項（§7）。

**two-key の所在**: 私の設計軸 key = 本 PASS。evidence 軸 key = pN/pY（pin 正式照合・DDR 全 35 対応・OUT 過小審査）。Rs = scope 承認（design authoring 解錠）。⛔本 PASS は authoring を解錠しない。
