# WMSO D1.1-B / B1 — 前提 claim-set（**evidence artifact・裁定質問を含まない**）

- node: `T-WMSO` D1.1-B; 著者 = `w2:pQ` RS-TECH-LEAD2; 作成 = **2026-07-20 16:55 JST**（shell 実測）
- **目的**: B1（hash 供給 locator）を Rs へ再上程するにあたり、**前提となる事実主張を裁定質問から分離し、独立に検証可能な artifact にする**。
- **作成理由（機構的）**: 2026-07-20 の A′ 裁定は、CC が提示した前置きに偽の主張が含まれた状態で下され **Rs により破棄**された（逐語「誤りが前提であるならそれは当然破棄にしろ」）。原因は**個人の要約ミスではない** — 当該記述は `WMSO_D11B_TENSOR_BINDING_DESIGN…` v6.1 §10:327 の逐語であり、**pS 設計軸 PASS と pN exact-pin PASS-CLOSE の両方を通過していた**。⇒ **two-key は設計判断の健全性を見るが、open point の記述に含まれる事実主張は誰も measure していなかった**。本 artifact はその穴を塞ぐために、**前提そのものを検証対象**にする。

## ⛔ 本 artifact が主張しないこと（境界）

- ⛔**選択肢（A/A′/B 等）を提示しない・推奨しない**。前回の失敗は「未確定の前提の上で選択肢を切った」ことなので、**選択肢の導出は前提確定の後**に行う。
- ⛔**A′ を復活させない**。破棄裁定の記録 = `WMSO_RS_B1_RULING_APRIME_20260720.md`（VOID・引用不可）。
- ⛔implementation / training / closed-loop authority を解錠しない。

## 検索空間（全 claim 共通・部分集合にしない）

| file | sha256 (先頭 16) |
|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md`（frozen） | `00192d20ca00b654` |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md`（frozen） | `c474acea7c58acc2` |
| `WMSO_EvidencePolicy_v1.9.json`（frozen） | `e63176af9bc3a246` |
| `WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md`（統治 prereg・`cf94601f7a`） | `ffd06623e22fa99b` |

⚠**前回の根因**: 閉じた query の対象を EvidencePolicy の md/JSON に限り、**frozen DESIGN 本体を同じ query に入れなかった**。本 artifact では **全 claim を上表 4 file 全体**に対して測る。

---

## CLAIM-1 — `ArtifactSlot` は locator field を持たない

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C1` |
| **主張** | frozen `ArtifactSlot` は `{state, artifact_hash}` のみで、**artifact 実体を指す ref field を持たない** |
| **対象 slot / profile** | `tensor_binding` / `normalization` 両方・全 profile |
| **期待真偽** | **TRUE** |
| **evidence** | `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:51` = `class ArtifactSlot: state: SlotState; artifact_hash: str \| None` |
| **閉じた query** | 上表 4 file 全体に対し `ArtifactSlot` を含む行を列挙し、そのうち `ref` を与える記述を抽出 → **該当 0 件** |
| **反証条件** | 上記 4 file のいずれかに、`ArtifactSlot` に ref / locator / path / uri 相当の field を与える記述が 1 件でも存在すれば FALSE |
| **source pin** | frozen `00192d20ca00b654…` |
| **前回 Rs へ述べた形との差** | **差なし**（前置き 4 主張のうち唯一そのまま成立） |

## CLAIM-2 — locator の可用性は grade により異なるが、「rank 3 のみ」は**不正確**

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C2` |
| **主張（訂正形）** | (a) `ProofItem.ref: str` は**必須 field**であり、(b) TENSOR_BINDING は**全 4 grade で非空の proof set** を持つ ⇒ **ref 自体は全 grade に存在する**。(c) ただし **`artifact_hash == claim_target_hash` を束縛する規則を持つ ProofKind は `FINAL_ARTIFACT_HASH` / `REPRODUCED_OUTPUT_HASH` の 2 種のみ**で、これらは **HASH_BOUND_REPRODUCED（rank 3）の proof set にのみ出現**する。(d) ⇒ **rank 1/2/4 にも ref はあるが、それが当該 artifact 実体を指すことを保証する frozen 規則は無い** |
| **対象 slot / profile** | `tensor_binding`（`normalization` は別 claim で要測定 — 本 artifact では未主張） |
| **期待真偽** | **TRUE（訂正形）**／⛔**前回形は FALSE-as-stated** |
| **evidence** | `…CONTRACTS_V2_DESIGN…:243-246`（`class ProofItem: kind; ref: str; artifact_hash: str\|None`）／EP JSON `policy_definition.proof_policy` の TENSOR_BINDING 行 = EXACT `[TRAIN_RUN_MANIFEST, SOURCE_COMMIT, CONFIG_HASH]` / HBR `[SOURCE_COMMIT, CONFIG_HASH, FINAL_ARTIFACT_HASH, REPRODUCTION_PROCEDURE, REPRODUCED_OUTPUT_HASH, EVALUATOR_ARTIFACT]` / RECONSTRUCTED `_all_13_components: [RECONSTRUCTION_SOURCES, COMPATIBILITY_TEST, UNRESOLVED_DIFFERENCES, EVALUATOR_ARTIFACT]` / DIMENSION_ONLY `_applicable.required: [DIMENSION_SOURCE, UNRESOLVED_DIFFERENCES]`（TENSOR_BINDING は `_applicable.components` に明示列挙）／EP JSON `proof_binding` 全 20 規則を列挙し `== claim_target_hash` を持つのは `FINAL_ARTIFACT_HASH` と `REPRODUCED_OUTPUT_HASH` のみ |
| **閉じた query** | `proof_binding` の**全 entry を列挙**（部分 grep でない）し、`rule` に `claim_target_hash` を含むものを抽出。併せて 4 grade の proof set を wildcard `_all_13_components` / `_applicable.components` まで**展開して**取得 |
| **反証条件** | (i) `ProofItem.ref` が Optional であれば (a) が FALSE ／ (ii) いずれかの grade の TENSOR_BINDING proof set が空であれば (b) が FALSE ／ (iii) `FINAL_ARTIFACT_HASH`/`REPRODUCED_OUTPUT_HASH` 以外に `claim_target_hash` 束縛規則があれば (c) が FALSE ／ (iv) rank 1/2/4 の ProofKind のいずれかに「ref が当該 artifact を指す」旨の frozen 規則があれば (d) が FALSE |
| **source pin** | frozen `00192d20ca00b654…` / `e63176af9bc3a246…` |
| **前回 Rs へ述べた形との差** | ⛔**前回「locator は rank 3 にしか存在しない」と述べたが、scope を欠いていた**。正しくは「**artifact への束縛規則を持つ** locator が rank 3 のみ」。ref の存在自体は全 grade。**この差は選択肢の切り方に影響し得る** |

## CLAIM-3 — slice が動作する profile は**統治文書で未指定**

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C3` |
| **主張** | boundary-only vertical slice が**どの EP profile（CLOSED_LOOP / SHADOW / OFFLINE_REPLAY）で動作するかは、統治 prereg に規定が存在しない** |
| **対象 slot / profile** | slice 全体（profile 自体が対象） |
| **期待真偽** | **TRUE（＝未指定であることが事実）** |
| **evidence** | `WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md` 全文に対する出現数: `SHADOW` = **0** / `CLOSED_LOOP` = **0** / `OFFLINE_REPLAY` = **0** / `profile`（大小無視）= **0** / `grade` = 2（:32 = EP total map への component 存在確認、:51 = DC-3 grade 別 proof obligation の一般記述。**いずれも slice の実行 profile を定めていない**） |
| **閉じた query** | prereg 全文に対する 5 語の出現数計測 + `grade` 2 件の逐語確認 |
| **反証条件** | prereg（または他の統治文書）に slice の実行 profile / 目標 grade を定める記述が存在すれば FALSE。⚠**本 claim は「未指定」という不在主張ゆえ、検証者は prereg 以外の統治面（`RL-Routing-Design.md` / `00-DESIGN-STATUS-LEDGER.md` / node spec / D0 architecture draft）も探索対象に含めて反証を試みること** |
| **source pin** | prereg `ffd06623e22fa99b…` @ `cf94601f7a` |
| **前回 Rs へ述べた形との差** | ⛔**前回「最初の slice が動く SHADOW（rank 2）」と事実として述べたが、根拠が無い**。これは**私の想定**であり、統治文書は沈黙している。⇒ **profile は決定事項であって観測事項ではない** |

## CLAIM-4 — 両 slot は locator gap については同型だが、**profile 適用は非対称**

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C4` |
| **主張（訂正形）** | (a) `tensor_binding` と `normalization` は **locator gap の構造については同型**（両者とも `ArtifactSlot` で ref を持たず、`claim_targets` が各 slot hash に束縛）。(b) ⛔しかし **profile 適用は非対称**: OFFLINE_REPLAY は **TENSOR_BINDING を `not_applicable`**（"replay does not re-execute binding"）とする一方 **NORMALIZATION は required**。(c) proof obligation も非対称（EXACT/NORMALIZATION のみ `NORMALIZER_HASH` を要求） |
| **対象 slot / profile** | 両 slot × 全 3 profile |
| **期待真偽** | **TRUE（訂正形）**／⛔**前回形「両 slot に同型で効きます」は FALSE** |
| **evidence** | EP JSON `policy_definition.profiles`: CLOSED_LOOP `min_grade_rank=3` 両 required / SHADOW `min_grade_rank=2` 両 required / OFFLINE_REPLAY `min_grade_rank=2` `not_applicable=[CONTROL_MODE, TENSOR_BINDING, TRAINING_DATASET, TRAINING_PROVENANCE]`（NORMALIZATION は非含有）／`claim_targets`: TB → `execution_bundle.tensor_binding.artifact_hash` / NORM → `execution_bundle.normalization.artifact_hash`／EP md `:142` の grade 別表 |
| **閉じた query** | `profiles` 配下の**全 profile を列挙**し、各 `not_applicable` 集合に対する両 slot の membership を判定（片方だけ grep しない） |
| **反証条件** | いずれかの profile で両 slot の required/免除が一致すれば (b) が FALSE。`claim_targets` が両 slot で異なる構造を取れば (a) が FALSE |
| **source pin** | frozen `e63176af9bc3a246…` / `c474acea7c58acc2…` |
| **前回 Rs へ述べた形との差** | ⛔**前回「両 slot に同型で効きます」と述べた — これが破棄の直接原因**。出所は v6.1 §10:327 の逐語（**banked かつ two-key 通過済**） |

---

## 集計

| claim | 前回 Rs へ述べた形 | 実測 |
|---|---|---|
| B1-C1 | `ArtifactSlot` に ref 無し | ✅ **そのまま成立** |
| B1-C2 | locator は rank 3 のみ | ⚠ **under-scoped**（訂正形で成立） |
| B1-C3 | 最初の slice は SHADOW rank 2 | ⛔ **根拠なし**（統治文書は沈黙・決定事項） |
| B1-C4 | 両 slot に同型で効く | ⛔ **偽**（訂正形で成立） |

**⇒ 4 主張中、そのまま成立するのは 1 件のみ。**

## 帰結（事実の記述であり提案ではない）

- **B1-C3 が未決である限り、「locator がどの grade / profile を覆う必要があるか」が定まらない。**
- **B1-C2 の訂正により、「rank 2 に locator が無い」という前回の動機づけは成立しない**（ref は在るが artifact への束縛規則が無い、が正しい問題設定）。
- ⇒ **前提が確定するまで選択肢の集合を確定できない**。本 artifact は選択肢を提示しない。

## 未測定（本 artifact が主張していない事項）

- `normalization` slot の grade 別 proof set（B1-C2 は `tensor_binding` のみ測定）
- slice の実行 profile を定める**べき**主体（Rs / VT-DESIGN のいずれか）— これは統治の問題であり本 artifact の射程外
- 選択肢の集合（A/A′/B が正しい分割かを含む）
