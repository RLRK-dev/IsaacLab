# WMSO 後継静的契約の判断（successor contract decision）(v0.2.8 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03 16:40 UTC（file mtime 実測 16:40:49）／ v0.2.2 = 2026-09-04 15:41 UTC（`date -u` 実測）
- status: **REVIEW CANDIDATE v0.2.8（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.2 = 3 軸独立レビュー finding の fold（§7）
- 土台（凍結・編集しない・4 file）: contracts_v2 DESIGN v2.11.2 `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` @ `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` ／ EP v1.9 md `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` ／ EP JSON v1.9 `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e`（definition hash `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`）／ tensor_binding DESIGN v13 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` @ `07250f4a0208b3bbd27eae6fef7d980743c4b538`
- 前提文書: D0 architecture（EXIT GRANTED）／ Rs C3 裁定（slice EP evidence profile = SHADOW rank 2・非 authority；execution profile は別軸・未裁定）／ handoff 決定（2026-09-03）／ 05 runtime spec v0.2.2 ／ 06 industrial profile v0.2.2
- ⛔ impl / training / closed-loop authority / production / push / freeze / slice = CLOSED 継続。本 doc は設計書面のみ。`$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。

## 0. 中心構造（決定）

```text
本工程では後継静的契約を作らない。
boundary-only（TERMINAL boundary）の v0.2 runtime = 追加 runtime spec（05）+ 外部 deployment profile（06）で構成でき、
凍結 D1.1-A / D1.1-B に schema delta を導入しない。
後継契約（推奨名 = contracts_v3）を起票するのは、以下の意味論を skill-specific な認証対象（static contract の一部）にする時だけ。
```

## 1. 根拠（凍結が既に runtime 層へ委譲しているもの）

- epoch の CAS 更新・新 epoch 発行・旧 epoch command 拒否・使用済み offer 拒否・snapshot 読出し = authority manager（O0 層）の状態所有責務（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`）⇒ 05 はこの委譲を埋めるだけで契約を変えない。
- closed-loop 実運転権限 = `granted == True` を必要条件（十分条件でない・上位 gate 追加可）（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354`）⇒ lease の必要条件を runtime 側で足すことは契約の想定内。
- binding は epoch を持たない（U-1・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:374`）⇒ epoch は runtime 状態。
- frozen 型に cell / controller / calibration / deployment を表す **field は無い**（`SkillDefinition` の field 列挙 `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:127-149`・`TensorBindingSpec` `$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:176-181`。v0.2.2 A-03 / A2-10: 型レベルの事実であり語彙の不在主張ではない — 散文語の hit は `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:570`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:337`「calibrated uncertainty」・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:255`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:313`「全 deployment の resolver」で、いずれも型・field・enum ではない。EP md / JSON の 0 hit は 06 §6.2 の再現 command）⇒ deployment profile は外部で定義でき、strict codec（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385`）がその field を frozen 型へ静かに足す経路を閉じる。
- runtime 記録の content-hash 化は WCJ 対象外・方式 defer（U14・`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537`）⇒ audit は契約の外。

## 2. 後継を起票する条件（いずれか 1 つで起票）

| 意味論 | 今（v0.2）の home | 静的化すると動くもの |
|---|---|---|
| continuation predicate | runtime assessment（05 §6.3・非 certified） | `SkillDefinition` の新 field ⇒ SkillDefinitionHash（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:159`）・BehaviorSignature（補集合定義 `:218`）・certificate |
| intrinsic recovery capability | 外部 RecoveryRoutingPolicy（05 §6.4） | 同上（frozen `recovery_rollback_target` は loud-discard・再導入 = schema bump `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:148`） |
| phase-level interruptibility / atomic region | CLOSED（05 §11 項 6） | `CheckpointSpec` の拡張 = 新 field（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`） |
| skill-specific safe-hold 保証 | future static candidate（05 OP-4・06 OPP-4） | `FailClosedAction` の拡張 or 新 field（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:147`） |
| formal outcome enum の追加 | runtime disposition（05 §7） | `ProducerOutcome` / `TerminationClass` の member 追加 = enum strict の破り（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385`） |

## 3. 起票時の名称 = `contracts_v3` とする理由

1. **strict codec が unknown field を拒否**する（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:385`）ため、v2 型に field を「静かに」足す経路が無い — 新 field は新 schema 版でしか表現できない。
2. 新 field は既定で `BehaviorSignature` に入り（補集合定義・`:218`）、`SkillDefinitionHash`（`:159`）も動く。`SkillActionId` は `{ns, skill, bundle, variant, brev}` の関数ゆえ**自動では動かない**（`:158`）が、同 key での再登録は `E_BEHAVIOR_REVISION_STALE` で拒否される（`:219`「ActionId は不変のまま、忘却は登録境界で機械捕捉」）⇒ `behavior_revision` の bump（= ActionId 変更）と certificate の再発行が事実上必須になる（v0.2.2・A2-06: 旧文「全 certified skill の identity が変わり」は frozen `:219` と 03 matrix C08–C12 に反していた）。
3. certificate は `evidence_policy_definition_hash` を結合する（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`）ため、認証対象が増えれば EP の `claim_targets` / `profiles` の total map も動く（04 §4）⇒ EP 後継と同時。
4. v1→v2 で行った migration（disposition 表の total 化・loud-discard）を v2→v3 で再び行う必要がある（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:148` の「再導入 = schema bump」が示すとおり）。
⇒ 部分改訂（v2.12）ではなく **v3** として prereg を切る。

## 4. 起票手続（本 doc は起票しない）

1. scope prereg（[DEFER-RECON] 含む）→ pS 設計軸 → pY/pN evidence 軸 → Rs scope 承認（D1.1-A / B / C と同型）。
2. 凍結 v2 / v13 は編集しない。supersession record を別 artifact で置く（freeze record = snapshot / LEDGER = current の convention）。
3. v3 の migration 表（v2 全 root field の disposition・silent drop なし）を design に inline。
4. EP 後継（04 §4）と同一 chunk で扱うか分割するかは prereg で決める（Rs）。

## 5. 主張しないこと（境界）

1. contracts_v3 の起票・設計・freeze を行わない。
2. 凍結 v2 / v13 の編集・schema delta を提案しない。
3. impl / training / closed-loop authority / two-key / gate PASS を主張しない。

## 6. Open points（⛔ open = 0 を宣言しない）

- OPS-1: 5 条件のどれが最初に必要になるか（slice の結果依存・DDR#32 の帰趨）。
- OPS-2: v3 と D1.1-C（未凍結・open-11）の順序。
- OPS-3: 本 doc 自体の two-key・Rs 裁定 = 未。

## 7. 版歴 / fold-map

- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 E を根拠に再構成。旧 v0.1 の識別子は本 doc に無い（05/06 で 削除）。
- v0.2 → **v0.2.2**（2026-09-04 15:41 UTC）: 3 軸独立レビューの finding A-03 / A2-10（§1 根拠 4 を型レベルの事実へ・package 外 scratch 参照の除去）・A2-06（§3 理由 2 の identity 文言を frozen `:158` / `:219` に整合）を fold。v0.2.1 は本 doc には無い（05 / 06 のみ）。verdict = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`（A-03=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED; A2-10=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED; A2-06=CONFIRMED（MEDIUM）/ v0.2.2 fold = RESOLVED）。

## 8. Review anchors

1. 委譲の根拠 4 点 — §1 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`・`:354`・`:537`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:374`・型レベルの不在 = `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:127-149`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:176-181`（v0.2.2）。
2. 5 条件それぞれが frozen hash 面を動かす — §2 ↔ `:159`・`:218`・`:151`・`:147`・`:148`。
3. v3 名称の 4 理由 — §3 ↔ `:385`・`:218`・`:158`・`:219`（v0.2.2）・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`。
