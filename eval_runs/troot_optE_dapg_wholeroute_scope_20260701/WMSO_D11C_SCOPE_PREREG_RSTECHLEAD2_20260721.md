# WMSO D1.1-C `artifact_manifest` — 詳細 scope preregistration (v1)

- node: `T-WMSO` D1.1-C; 著者 = `w2:pQ` RS-TECH-LEAD2; 作成 = **2026-07-21 12:35 JST**（shell 実測）
- **着手指示** = Rs 逐語「go」（2026-07-21 12:1x）／**gate** = `[DEFER-RECON]` 完了・banked = `WMSO_D11C_DEFER_RECON_RSTECHLEAD2_20260721.md` @ `7effeb774f`
- **上位 prereg** = `WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md` v1.1.1（`:19`「D1.1-C / slice は着手時に各自の詳細 prereg を切る」・§3 = banked outline）
- **[L-TRIAGE] = L2**（新規 file 作成・公開 API 境界に触れない・凍結 file を編集しない）。⇒ ゲート = 設計軸 pS + evidence 軸 pN の two-key（D1.1-B prereg と同型。CC Debate は **design 段**で発火し本 prereg 段では発火しない）。

## 0. 土台（不変・本 prereg は編集しない）

| 対象 | sha256（先頭 16） | 状態 |
|---|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | `00192d20ca00b654` | **FROZEN**（D1.1-A・2026-07-20） |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` | `c474acea7c58acc2` | **FROZEN** |
| `WMSO_EvidencePolicy_v1.9.json` | `e63176af9bc3a246` | **FROZEN** |
| `WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md` | `5a1874d3be8b98b8` | ⭐**FROZEN / CUSTODY-CLOSED**（D1.1-B・2026-07-21） |

⛔**schema delta を導入しない**（必要が判明したら supersession + Rs review へ escalate し、本 chunk では閉じない）。

## 1. ⭐ 本 chunk を貫く原則 — **機構 / policy の分離**

D1.1-C が設計するのは「**何を記録し、どう区別するか（機構）**」であり、「**その記録を使ってどう判断するか（policy）**」ではない。
⇒ policy が未裁定でも機構は設計できる。**ただし機構に policy を焼き込めば、未裁定の判断を先取りすることになる**（`[DEFER-RECON]` §2）。本 prereg の IN / OUT はすべてこの線で切る。

## 2. IN（本 chunk が設計する）

1. **artifact manifest 型の定義**（training-time run manifest）— contracts_v2 + tensor_binding を **code / model / data / config / evaluator / EvidencePolicy / `substrate_id` の exact hash へ結合**する構造。
2. **`substrate_id` の必須化と区別の機構** — 旧 contaminated log にも明示 `substrate_id` を付与させ、**異なる substrate の silent pooling を禁止**する（検出・拒否の code を含む）。
3. **DC-3 grade 別 proof obligation の実体供給** — 凍結 EP の各 grade が要求する proof（`EXACT_TRAIN_TIME` = TRAIN_RUN_MANIFEST + SOURCE_COMMIT + CONFIG_HASH 等）に対し、**manifest がどの field で実体を供給するか**の写像。
4. **minimal JCS の package 全体への展開** — artifact manifest / 証拠 bundle / 配布 metadata への canonical JSON 適用 + package・CI の最終整備。
5. **carry 機構 3 件**（`[DEFER-RECON]` §3.2）:
   - **U-2**: manifest が run 毎に producer artifact を pin する機構
   - **U-5**: manifest が **両段 binding を記録**する機構（`E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` の解消経路）
   - **U-6**: `chain_topology_class` を manifest **metadata** として記録する機構

## 3. ⛔ OUT（本 chunk が閉じない・境界）

| # | OUT 事項 | 帰属 |
|---|---|---|
| 1 | **どの substrate を採用/破棄するかの選別 policy** | **DDR #26 の Rs 裁定**（機構は IN・policy は OUT — §1） |
| 2 | 発行済 certificate 下での **producer artifact 差替えの阻止**実装 | closed-loop eligibility 検査（別 chunk） |
| 3 | **demo の再記録**（198 demo・kinematic 全削除後） | 別 lane（p4 / p0）・DDR #29 #21 |
| 4 | **契約層での topology 束縛** | schema delta ⇒ Rs review・DDR #30 |
| 5 | **合成 schema delta**（`SkillCompositionDefinition` / barrier / region postcondition） | **pX SKILL-DESIGN の court**・normative closure = NOT YET |
| 6 | **implementation（code）/ training / closed-loop authority** | 別 gate（**CLOSED 継続**） |
| 7 | **slice の全て** | slice 着手時の詳細 prereg |
| 8 | 凍結 4 file（§0）の編集 | ⛔不可 |
| 9 | **腕参加の機械宣言（F4）** の source 設計 | **p5 SKILL-DETAIL-DESIGN**（p4 routing 2026-07-21 12:33） |

## 4. carry（本 chunk が受け取り、prereg 本文に明示して次へ渡す）

`[DEFER-RECON]` §4 の 5 件をそのまま継承: ①#26 選別 policy 非焼込 ②#28 阻止実装 ③#29 demo 再記録 ④#30 契約層束縛 ⑤#31 trainer 実在（manifest の**実データ充填**は trainer 実在に依存・**機構の設計は非依存**）。

## 5. 検証計画（two-key）

1. **設計軸 = pS MWSO-DESIGN** — 本 prereg が凍結（§0）に忠実か / IN-OUT 境界が機構-policy 線で正しく切れているか / 他 court（pX 合成・p5 詳細）へ越境していないか。
2. **evidence 軸 = pN 相当（現 OPS-SUP = pY）** — pin の exact 照合 / carry の DDR 対応 / OUT 宣言が過小でないか。
3. **Rs** — scope 承認（design authoring の解錠）。

⛔**本 prereg は design ではない**。承認後に authoring へ入る（D1.1-B と同型: prereg → design → CC Debate → two-key → Rs freeze）。

## 6. 本 prereg が主張しないこと

- ⛔manifest の**具体的 field 名・型・hash 順序**を確定しない（design 段）。
- ⛔`substrate_id` の**値空間**（どの substrate が存在するか）を確定しない。
- ⛔`open = 0` を宣言しない（凍結 §10 と同規律）。
