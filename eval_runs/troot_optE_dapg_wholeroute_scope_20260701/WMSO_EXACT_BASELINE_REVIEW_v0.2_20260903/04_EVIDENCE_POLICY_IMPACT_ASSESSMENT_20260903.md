# WMSO EvidencePolicy v1.9 — 影響評価（v0.2 runtime / profile に対して）(v0.2.2 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03（UTC・`date -u` 実測）
- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.2 = 3 軸独立レビュー finding A2-10 の fold（§8）
- 土台（凍結・編集しない・4 file）: contracts_v2 DESIGN v2.11.2 `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` @ `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` ／ EP v1.9 md `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` ／ EP JSON v1.9 `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e`（definition hash `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`）／ tensor_binding DESIGN v13 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` @ `07250f4a0208b3bbd27eae6fef7d980743c4b538`
- 前提文書: D0 architecture（EXIT GRANTED）／ Rs C3 裁定（slice EP evidence profile = SHADOW rank 2・非 authority；execution profile は別軸・未裁定）／ handoff 決定（2026-09-03）／ 05 runtime spec v0.2 ／ 06 industrial profile v0.2
- ⛔ impl / training / closed-loop authority / production / push / freeze / slice = CLOSED 継続。本 doc は設計書面のみ。`$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。

## 0. 中心構造（結論）

```text
修正版 runtime（05）+ 産業用 profile（06）だけであれば、凍結 EvidencePolicy v1.9 は変更しない。
  runtime 判断・epoch・lease・fault   → runtime audit evidence（05 §8）      … EP の claim_target / ProofKind / grade ではない
  cell・controller・tool・calibration・gateway・fault injection → DeploymentEvidencePolicy（06 §6） … EP の外
  continuation / recovery / interruptibility / safe-hold を **静的に認証**する場合のみ → EP 後継（07 の contracts_v3 と同時）
```

## 1. 判定根拠（何が hash-visible か）

- `evidence_policy_definition_hash = H_WCJ(policy_definition)`、metadata は hash 入力の外（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`・`$D/WMSO_EvidencePolicy_v1.9.json:5`）。
- `policy_definition` の 17 member = {policy_semver, grades, component_groups, claim_targets, projection_rules, proof_policy, reproduction_rules, proof_item_canonical_order, proof_conflict_rules, proof_binding, payload_rules, trust_boundary, evaluator_registry_rule, applicability_rules, profiles, exemption_reporting, usage_ceiling}（本 session で JSON を実読・`03_evidence_policy_map.md`）。
- 05 / 06 はこの 17 member のいずれにも項目を足さず、値も変えない ⇒ definition hash `e7ca4309…` は不変（本 package の `verify_exact_baseline_pins.sh` が埋込 command で再計算 = 一致）。

## 2. runtime audit evidence は EP の外

- EP の `claim_targets`（13 component・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:101` 付近の表）は skill 定義の**静的** component（POLICY_ARTIFACT … HANDOFF_SCHEMA）を対象とし、epoch / lease / permit / fault という **runtime 事象**の語彙を持たない（EP md / JSON で `epoch` / `lease` = 0 hit — 再現 command は 06 §6.2・v0.2.2 A2-10 で package 外の scratch 参照を除去）。
- `usage_ceiling`（`$D/WMSO_EvidencePolicy_v1.9.json:213`）と `closed_loop_authority` の conjoin 規則（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:156`）は不変。05 の `CLOSED_LOOP_AUTHORITY` lease は frozen `granted == True`（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:354`）を**必要条件として読むだけ**で、ceiling を動かさない。
- runtime 記録の content-hash 化は frozen U14 で defer（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:537`）。05 §8 はこれに従い方式を定めない。

## 3. `DeploymentEvidencePolicy` は別 policy

- 06 §6 の `DeploymentEvidenceKind`（CELL_COMMISSIONING … FAULT_INJECTION_RESULT）は EP の `ComponentKind` / `ProofKind` / grade 名のいずれとも共有しない。
- deployment evidence は skill の certification に影響しない — certificate は runtime 事象で無効化されない（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:39`）。
- 名前空間: EP の `evaluator_registry_rule` は certification 用であり、06 の `HealthCheckSpec.evaluator_ref` は別 registry（06 OPP-9）。

## 4. EP 後継が必要になる条件

| 条件 | EP のどこが動くか | 併せて動くもの |
|---|---|---|
| continuation predicate を skill-specific な認証対象にする | `claim_targets` に新 component ／ `profiles` の required set | SkillDefinitionHash / BehaviorSignature（`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:218`）⇒ contracts_v3（07） |
| intrinsic recovery capability / phase-level interruptibility・atomic region / skill-specific safe-hold を認証対象にする | 同上 + 必要なら `ProofKind`（`proof_binding` の total map） | 同上 |
| 新 profile（例: deployment 別 evidence profile）を EP に入れる | `profiles` / `applicability_rules.profile_overlay` | usage matrix = ceiling の再裁定（Rs） |
| deployment evidence を EP の grade で格付けする | `grades` / `proof_policy` | 本 doc は**採らない**（06 §6.2） |

いずれも `policy_definition` の member を変えるため definition hash が変わり、certificate が結合する `evidence_policy_definition_hash` も動く ⇒ **EP 後継 + contracts_v3 + migration** を同時に扱う（07 §3）。

## 5. SHADOW / CLOSED_LOOP / OFFLINE_REPLAY との整合（lease mode）

- EP の SHADOW = 「非 authority」（`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:155`）。05 の `SHADOW_NON_AUTHORITY` lease は actuation を出さない runtime 層の定義であり、EP の profile 定義（required set + min_grade・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:154`）を変えない。
- OFFLINE_REPLAY は制御を発行しない（TENSOR_BINDING / CONTROL_MODE 免除）ため lease を必要としない — 05 は OFFLINE_REPLAY 用の lease mode を定義しない（replay は runtime の外）。
- slice の EP evidence profile = SHADOW（`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:5`）は evidence 側の裁定であり、execution profile 軸（`:65`）とも deployment profile（06）とも別。

## 6. 主張しないこと（境界）

1. EP v1.9 の改訂・後継の起票を行わない（条件の列挙のみ）。
2. certification / eligibility / authority grant の結果に触れない。
3. impl / training / closed-loop authority / freeze / two-key / gate PASS を主張しない。

## 7. Open points（⛔ open = 0 を宣言しない）

- OPE-1: deployment evidence を将来 EP に統合するか（本 doc は分離を推奨・裁定は Rs）。
- OPE-2: runtime audit の hash 方式（U14）が確定した際、EP の `reproduction_rules` との関係を再評価する必要があるか。
- OPE-3: 本 doc 自体の two-key・Rs 裁定 = 未。

## 8. 版歴 / fold-map

- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 F を根拠に再構成。旧 v0.1 の識別子（`BeliefSnapshotRef` 等）は本 doc に無い（05/06 で 削除）。
- v0.2 → **v0.2.2**（2026-09-04 15:41 UTC）: A2-10（package 外 scratch 参照）を fold。判断内容は不変。verdict = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`（A2-10=起草者再検証=CONFIRMED（独立 verifier 未了・11_ §4））。

## 9. Review anchors

1. definition hash の projection 規則と 17 member の不変 — §1 ↔ `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`・`$D/WMSO_EvidencePolicy_v1.9.json:5`。
2. runtime 事象語彙が EP に無い（grep 0 hit）— §2。
3. usage ceiling / closed_loop_authority 不変 — §2 ↔ `$D/WMSO_EvidencePolicy_v1.9.json:213`・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:156`。
4. EP 後継の条件が BehaviorSignature 補集合定義と連動 — §4 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:218`。
5. SHADOW = 非 authority の帰属 — §5 ↔ `$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:155`。
