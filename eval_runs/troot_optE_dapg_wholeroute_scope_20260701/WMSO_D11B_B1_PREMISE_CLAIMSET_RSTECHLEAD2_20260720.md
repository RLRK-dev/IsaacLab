# WMSO D1.1-B / B1 — 前提 claim-set **v4**（**evidence artifact・裁定質問を含まない**）

- node: `T-WMSO` D1.1-B; 著者 = `w2:pQ` RS-TECH-LEAD2; v1 = **2026-07-20 16:55 JST**; v2 = 2026-07-20 17:16 JST; v3 = 2026-07-20 17:23 JST; **v4 = 2026-07-20 17:26 JST**（いずれも shell 実測・v3 は未 bank のまま v4 へ）
- **v2 = pS 独立検証（record `01bd01403c8e…`）の refinement を fold**。pS 判定: C1 ✅TRUE / C2 ⚠訂正形 TRUE + refinement / C3 ✅TRUE + refinement / C4 原形 FALSE・訂正形 TRUE / **C1-C4 = Rs 質問の前提の完全集合（漏れ 0）** / consequence = SOUND（むしろ強化）。⭐**C2 の refinement は、私が本 artifact に書いた反証条件 (iii) によって私の主張が落とされた形** — claim-set 機構が設計どおり機能した実例として記録する。
- **v4 = pN の v2 exact-pin HOLD V2-B1..B4 の fold**。⛔**V2-B1/V2-B2 は、v3 で私が入れた fold 自体が行き過ぎだという指摘**であり、実測で確認した:
  - ⛔**V2-B1（私の v3 が誤り）**: **「claim_target hash の間接確立」と「target artifact bytes の locator」を混同していた**。`TRAIN_RUN_MANIFEST` の rule = `artifact_hash = manifest sha256; manifest content lists claim_target_hash` ⇒ **`ref` が解決するのは manifest 自身の bytes**であり、target artifact の在処は供給されない（`TRAIN_TIME_CRYPTO_BINDING` も blob 自身）。**B1 は locator 問題**ゆえ、**hash association と target-byte locator は別軸**。⇒ **v3 の「rank 4 が rank 3 より弱い逆転は測定 artifact」は locator 軸では撤回できない**（TB rank 4 は association のみ・target-byte locator なし／rank 3 は `FINAL_ARTIFACT_HASH`・`REPRODUCED_OUTPUT_HASH` の ref + `expected_sha256 == claim_target` で locator あり）。**逆転は locator 軸では実在する**。
  - ⛔**V2-B2（私の v3 が誤り）**: C3 の「未決は SHADOW / OFFLINE_REPLAY に絞られる」は**根拠不足**。prereg:18 の着手順 = **B → C → slice** ゆえ**指定 slice は B/C の後**に走り、DC-1（prereg:31）が排除するのは「**B 完了前**の closed-loop eligibility」のみ ⇒ **DC-1 単独では CLOSED_LOOP を排除しない**。run timing が未決なら **3 profile とも未決**。正しい表現は「**pre-B の早期 run だけ CLOSED_LOOP 不可**」。⚠**私は pS の N-B を prereg:18-19 を自分で測らずに伝播した** — 本 arc で繰り返し記録している「**転記する前に読め**」の再発。
- **v3（未 bank）= pN exact-pin EVIDENCE HOLD B4-1..B4-3 の fold**（pN: custody PASS・C1/C2/C3 = **PASS-CLOSE**・C4 に 3 件の OPEN）。⭐**B4-1 は私の分類方法そのものの欠陥**を突いた: 私は rule を**文字列 `claim_target_hash`** で分類していたが、`NORMALIZER_HASH` は「`artifact_hash == normalization slot hash`」と**別表現で同じことを述べる**ため漏れた（`claim_targets.NORMALIZATION = execution_bundle.normalization.artifact_hash` ゆえ両者は同一物）。
- ⛔⛔**再発している根本原因（3 度目・本 artifact 最重要の記録）**: **閉じた query を「意味述語」ではなく「文字列/場所」で張っている**。① N-1 = 検索空間を EP md/JSON に限り frozen DESIGN 本体を外した（**空間**が狭い）／② C2 v1 = `== claim_target_hash` の完全一致で分類し**間接確立**を落とした（**述語**が狭い）／③ B4-1 = 文字列 `claim_target_hash` で分類し**別表現の直接束縛**を落とした（**表現**が狭い）。⇒ **以後、閉じた query は「何を意味する行を探しているか」を先に書き、その述語を満たす表現を列挙してから張る**。
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
| **前回 Rs へ述べた形との差** | ⛔**前回「locator は rank 3 にしか存在しない」と述べたが、scope を欠いていた**。ref の存在自体は全 grade。**この差は選択肢の切り方に影響し得る** |
| **⚠v2 refinement（pS catch・私の反証条件 (iii) で hit）** | **v1 の (c) もなお不完全**。`claim_target_hash` を確立する ProofKind は **直接**（`== claim_target_hash`）と**間接**（manifest / blob 経由で claim_target を束ねる）に分かれ、**両者を分けずに「rank 3 のみ」と述べていた**。全 `proof_binding` を分類した結果 — **直接 = `FINAL_ARTIFACT_HASH` / `REPRODUCED_OUTPUT_HASH`** ／ **間接 = `TRAIN_RUN_MANIFEST`（rule: manifest content lists claim_target_hash）/ `TRAIN_TIME_CRYPTO_BINDING`（blob が claim_target_hash を束ねる）**。⇒ **TENSOR_BINDING の claim_target 確立は rank 3（直接）に加え rank 4（間接・`TRAIN_RUN_MANIFEST`）でも成立**する |

**v2 追加測定 — claim_target 確立の grade × slot × 直接/間接（閉じた query・全 grade × 両 slot を展開）**:

| grade (rank) | TENSOR_BINDING | NORMALIZATION |
|---|---|---|
| EXACT_TRAIN_TIME (4) | **間接のみ**（`TRAIN_RUN_MANIFEST`） | **直接**（`FINAL_ARTIFACT_HASH`）+ 間接（`TRAIN_TIME_CRYPTO_BINDING`, `TRAIN_RUN_MANIFEST`） |
| HASH_BOUND_REPRODUCED (3) | **直接**（`FINAL_ARTIFACT_HASH`, `REPRODUCED_OUTPUT_HASH`） | **直接**（同左） |
| RECONSTRUCTED_COMPATIBLE (2) | なし | なし |
| DIMENSION_ONLY (1) | なし | なし |

⚠**この表は 2 つの旧主張を同時に訂正する**: (i) 「rank 3 のみ」= 不完全（rank 4 に間接確立あり）／(ii) **「rank 4 が rank 3 より弱いという逆転」= 測定 artifact だった**（v6.1 §4 に記載・現在は SUPERSEDED fold 内）。逆転は間接確立を数えなかったことによる見かけであり、**実際には rank 4 も claim_target を確立する**。
⚠**rank 4 に新たな slot 非対称**: NORMALIZATION は rank 4 で**直接**確立を持つが TENSOR_BINDING は**間接のみ**。C4 の非対称は profile 適用だけでなく **proof 構造にも及ぶ**。

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
| **⚠v2 refinement（pS 広域反証）** | pS が charter / `RL-Routing-Design.md` / LEDGER / node spec / D0 draft / SOMA / 全 prereg を対象に反証を試み、**slice の EP evidence profile を pin する記述 0 件** ⇒ **C3 成立**（私の prereg 単独探索が偶然当たったのではない）。**(N-A)** `WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:13`「WMSO may use a boundary-only or a real-time execution profile」は **execution 軸**（boundary-only / real-time）であり、**EP の evidence profile 軸（CLOSED_LOOP / SHADOW / OFFLINE_REPLAY）とは別物**。C3 は後者を測っており正しい。⚠**同名語による取り違えの危険があるため、以後「execution profile」と「EP evidence profile」を明示的に呼び分ける**。**(N-B・v4 で訂正)** prereg:31 の **DC-1** =「D1.1-B 完了前は tensor binding hash が存在しない → closed-loop eligibility を得られない」。⛔**v3 はこれを「未決は SHADOW / OFFLINE_REPLAY に絞られる」と読んだが誤り**: prereg:18 の着手順は **B → C → slice** であり **指定 slice は B/C の後**に走る ⇒ **DC-1 単独では CLOSED_LOOP を排除しない**。正しい限定は「**pre-B の早期 run だけ CLOSED_LOOP 不可**」。**run timing が未決である以上、3 profile とも未決**。⚠**私は pS の N-B を prereg:18-19 を自分で読まずに伝播した**（転記する前に読め、の再発） |

## CLAIM-4a — 両 slot は **schema 層では** locator gap が同型

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C4a`（v3 で `B1-C4` を分割） |
| **主張** | **schema 層に限れば**同型: `tensor_binding` / `normalization` とも `ArtifactSlot = {state, artifact_hash}` で ref を持たず（→ `B1-C1`）、`claim_targets` が各々 `execution_bundle.<slot>.artifact_hash` に束縛する |
| **対象 slot / profile** | 両 slot・全 profile（**schema 層のみ**） |
| **期待真偽** | **TRUE（schema 層に限定した形）** |
| **evidence** | `…CONTRACTS_V2_DESIGN…:51`／EP JSON `claim_targets`: TB → `execution_bundle.tensor_binding.artifact_hash` / NORM → `execution_bundle.normalization.artifact_hash` |
| **閉じた query** | `claim_targets` の**全 13 entry を列挙**し両 slot の右辺構造を比較 |
| **反証条件** | 両 slot の `ArtifactSlot` 型が異なる、または `claim_targets` の右辺が構造的に異なる形（一方のみ `H_WCJ(...)` 等）であれば FALSE |
| **source pin** | frozen `00192d20ca00b654…` / `e63176af9bc3a246…` |
| **⚠ 適用限界（pN B4-1）** | ⛔**「locator gap が同型」を schema 層に限定せずに述べると FALSE**。end-to-end の locator 意味論は同型でない → `B1-C4b` |

## CLAIM-4b — **end-to-end の locator 意味論は同型でない**（proof 層・profile 層とも）

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C4b`（v3 新設・pN B4-1/B4-3） |
| **主張** | (a) **proof 層**: rank 4（EXACT_TRAIN_TIME）で **NORMALIZATION は target-byte locator を持つが TENSOR_BINDING は持たない**。NORM の EXACT proof set は TB の `{TRAIN_RUN_MANIFEST, SOURCE_COMMIT, CONFIG_HASH}` に加え `FINAL_ARTIFACT_HASH` / `TRAIN_TIME_CRYPTO_BINDING` / `NORMALIZER_HASH` を持ち、`NORMALIZER_HASH` の rule = `artifact_hash == normalization slot hash`（= claim target）。trust boundary が `resolve_artifact(ref, expected_sha256)` である以上、**expected 側が byte 単位で確立されるか否かは locator 可用性の差**である。(b) **profile 層**: OFFLINE_REPLAY は TENSOR_BINDING を `not_applicable` とするが NORMALIZATION は required |
| **対象 slot / profile** | 両 slot × 全 4 grade × 全 3 profile |
| **期待真偽** | **TRUE** |
| **evidence（意味述語で再分類・v3）** | 下表 |
| **閉じた query** | ⭐**文字列でなく意味述語で張る**: 「その ProofKind の rule は、当該 component の **claim target を byte 単位で確立する**か」。該当表現を**列挙してから**照合 — (i) `== claim_target_hash`（直接）(ii) `== <slot> slot hash`（**別表現の直接** ← v2 まで漏れていた）(iii) `claim_target_hash` を manifest/blob 経由で束ねる（間接）。`proof_binding` 全 20 clause × 両 slot × 全 4 grade を展開 |
| **反証条件** | (i) rank 4 の TB proof set に (i)(ii) 型の clause が存在すれば (a) が FALSE ／ (ii) `NORMALIZER_HASH` の rule が claim target 以外を指すなら (a) が FALSE ／ (iii) ⭐**OFFLINE_REPLAY において**両 slot の required/免除が一致すれば (b) が FALSE |
| **source pin** | frozen `e63176af9bc3a246…` / `c474acea7c58acc2…` |

**⭐2 軸に分離（v4・pN V2-B1）— 混同すると B1 の問いが解けない**:
- **軸 A = hash association**: その grade の proof が claim_target hash を**何らかの形で確立/言及**するか。
- **軸 B = target-byte resolvability（＝ B1 が問う locator）**: `resolve_artifact(ref, expected_sha256)` に渡して **target artifact 自身の bytes** を取り出せる `ref` が在るか。`ref` が manifest / blob を指す clause は**軸 A のみ**を満たす。

| grade (rank) | TB 軸A（association） | **TB 軸B（target-byte locator）** | NORM 軸A | **NORM 軸B** |
|---|---|---|---|---|
| EXACT_TRAIN_TIME (4) | あり（`TRAIN_RUN_MANIFEST`） | ⛔**なし** | あり | ✅**あり**（`FINAL_ARTIFACT_HASH` / `NORMALIZER_HASH`） |
| HASH_BOUND_REPRODUCED (3) | あり | ✅**あり**（`FINAL_ARTIFACT_HASH` / `REPRODUCED_OUTPUT_HASH`） | あり | ✅あり |
| RECONSTRUCTED_COMPATIBLE (2) | なし | ⛔なし | なし | ⛔なし |
| DIMENSION_ONLY (1) | なし | ⛔なし | なし | ⛔なし |

⚠**この表が確定させること**: (i) **「locator は rank 3 のみ」は TB の軸 B では正しい**（v1 の原形が結果的に正しく、v2/v3 の「不完全」判定こそが軸を取り違えていた）／(ii) ⛔**「rank 4 が rank 3 より弱い逆転」は軸 B で実在**する（v3 の「測定 artifact」撤回は誤り・再撤回）／(iii)「両 slot 同型」は **schema 層のみ真**で、**軸 B では rank 4 において非対称が最も強い**（NORM あり・TB なし）。
⚠**訂正の履歴**: v1 原形（軸未分離）→ v2「rank3 のみは不完全」→ v3「逆転は測定 artifact」→ **v4 で軸 A/B を分離し、軸 B では v1 原形が正しかったと確定**。⇒ **私は 2 度、軸を取り違えたまま『訂正』を重ねていた**。

**profile 適用（v2 から不変・pN 追認済）**: CLOSED_LOOP（rank 3）両 required ／ SHADOW（rank 2）両 required ／ OFFLINE_REPLAY（rank 2）**TB 免除・NORM required**。

---

## 集計

| claim | 前回 Rs へ述べた形 | 実測 |
|---|---|---|
| B1-C1 | `ArtifactSlot` に ref 無し | ✅ **そのまま成立** |
| B1-C2 | locator は rank 3 のみ | ⚠ **under-scoped**（訂正形で成立） |
| B1-C3 | 最初の slice は SHADOW rank 2 | ⛔ **根拠なし**（統治文書は沈黙・決定事項） |
| B1-C4a | 両 slot に同型で効く | ⛔ **偽** — **schema 層に限定してのみ成立** |
| B1-C4b | （前回は主張していない） | ⚠ **end-to-end は非同型**（proof 層 rank4 + profile 層 OFFLINE_REPLAY） |

**⇒ 4 主張中、そのまま成立するのは 1 件のみ。**

⚠**訂正の回数**: C2 は v1 訂正形でも不完全（直接/間接の分離欠落）→ v2 で訂正 → **v3 で再訂正**（別表現の直接束縛を文字列 query が落としていた）。C4 は v2 で訂正 → **v3 で分割**（schema 層 / end-to-end）。⇒ **同一主張に 2〜3 回の訂正**。**under-scope は 1 回の訂正で底を打たない**。

## 帰結（事実の記述であり提案ではない）

- **B1-C3 が未決である限り、「locator がどの grade / profile を覆う必要があるか」が定まらない。**
- **B1-C2 の訂正により、「rank 2 に locator が無い」という前回の動機づけは成立しない**（ref は在るが artifact への束縛規則が無い、が正しい問題設定）。
- ⇒ **前提が確定するまで選択肢の集合を確定できない**。本 artifact は選択肢を提示しない。
- ⛔**v2/v3 の「絞り込み」は v4 で撤回**: DC-1 は **pre-B の早期 run にのみ効く**ため、B/C 後に走る指定 slice では **CLOSED_LOOP を含む 3 profile すべてが未決**。
- **残る帰結（弱めた形で成立）**: **OFFLINE_REPLAY は TENSOR_BINDING を免除する**（C4b）ため、**C3 の決定が「TB の locator が slice に必要か否か」自体を左右する** ⇒ **C3 は locator 設計の上流**。この帰結は 3 profile 未決のままでも成立する。

## 未測定（本 artifact が主張していない事項）

- ~~`normalization` slot の grade 別 proof set~~ → **v3 で測定済**（`B1-C4b` の表）。⚠v2 は「未測定」と書きながら C4 で全 profile の locator gap を総括しており **scope 不整合**だった（pN B4-3）。
- slice の実行 profile を定める**べき**主体（Rs / VT-DESIGN のいずれか）— これは統治の問題であり本 artifact の射程外
- 選択肢の集合（A/A′/B が正しい分割かを含む）
