# WMSO D1.1-B / B1 — 前提 claim-set **v6**（**evidence artifact・裁定質問を含まない**）

- node: `T-WMSO` D1.1-B; 著者 = `w2:pQ` RS-TECH-LEAD2; v1 = **2026-07-20 16:55 JST**; v2 = 2026-07-20 17:16 JST; v3 = 2026-07-20 17:23 JST; v4 = 2026-07-20 17:26 JST; v5 = 2026-07-20 17:39 JST; **v6 = 2026-07-20 17:48 JST**（いずれも shell 実測・v5 は未 bank のまま v6 へ）
- **v2 = pS 独立検証（record `01bd01403c8e…`）の refinement を fold**。pS 判定: C1 ✅TRUE / C2 ⚠訂正形 TRUE + refinement / C3 ✅TRUE + refinement / C4 原形 FALSE・訂正形 TRUE / **C1-C4 = Rs 質問の前提の完全集合（漏れ 0）** / consequence = SOUND（むしろ強化）。⭐**C2 の refinement は、私が本 artifact に書いた反証条件 (iii) によって私の主張が落とされた形** — claim-set 機構が設計どおり機能した実例として記録する。
- **v5 = pN の v4 exact-pin HOLD V4-R1..R4 の fold（records-only・semantic rerun なし）**。指摘 = **訂正後の結論は新節に在るが、旧節が live のまま残り同一 artifact 内で二値**（CLAIM-2 の live 本文 :46-70 が v2 のまま `rank3 のみは不完全 / 逆転は測定 artifact` と述べ、軸 A/B 表と正面矛盾）。⇒ **CLAIM-2 を現行形（軸 A/B 分離）で書き直し、v1-v3 の系譜は折りたたみへ隔離**。集計・帰結・主張 count も現行化。
- ⚠**V4-R4 = 私の判断ミス**: pN へ「LEDGER DDR#27 の訂正は不要（むしろ現状が正）」と答えたが**誤り**。headline は「locator **rank3 のみ存在し SHADOW rank2 に無**」であり、前半（rank3 のみ）は軸 B で正しいが、**後半は C3 が否定した「slice は SHADOW rank2 で動く」前提**を抱え、かつ**軸 B の qualifier（target-byte）を欠く**。⇒ **断片だけ照合して主張全体を見なかった**（本 arc で繰り返している型）。p6 へ custody sync を依頼する。
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
| **前回 Rs へ述べた形との差** | **差なし**（C1 自体は前置きの記述と現行主張が一致）。⚠**「4 主張のうち唯一そのまま成立」という v1-v5 の記述は撤回** — 現行集計では **C1 と C2（軸 B）の 2 件**が成立（pN V5 指摘）|

## CLAIM-2 — locator の可用性は **軸 B（target-byte）で rank 3 のみ**、軸 A（association）は rank 3 + rank 4

> ⭐**本 claim は v1→v5 で 3 度書き換わった。現行形は以下のみ**。v1-v3 の系譜（誤訂正 2 回を含む）は末尾の折りたたみへ隔離した（pN V4-R1）。

| 項目 | 内容 |
|---|---|
| **claim_id** | `B1-C2`（v5 現行形） |
| **主張** | (a) `ProofItem.ref: str` は**必須 field**であり、TENSOR_BINDING は**全 4 grade で非空の proof set** を持つ ⇒ **ref 自体は全 grade に存在する**。(b) ⭐**ただし「ref が在る」ことと「target 実体を解決できる」ことは別軸**。**軸 A = hash association**（claim target hash を確立/言及する）／**軸 B = target-byte resolvability**（`resolve_artifact(ref, expected_sha256)` で **target artifact 自身の bytes** を得られる）。(c) **B1 が問うのは軸 B**。(d) ⇒ **TENSOR_BINDING の軸 B locator は rank 3（`FINAL_ARTIFACT_HASH` / `REPRODUCED_OUTPUT_HASH`）にのみ存在する**。rank 4 は軸 A のみ（`TRAIN_RUN_MANIFEST` の ref は **manifest 自身**を解決し、その内容が claim_target_hash を列挙するに留まる）。rank 2 / 1 は両軸ともなし |
| **対象 slot / profile** | `tensor_binding`（`normalization` は `B1-C4b` の表で測定済） |
| **期待真偽** | **TRUE** |
| **evidence** | `…CONTRACTS_V2_DESIGN…:243-246`（`ProofItem: kind; ref: str; artifact_hash`）／`:285`（trust boundary = `resolve_artifact(ref, expected_sha256)`）／EP JSON `proof_binding` の rule 逐語 — `FINAL_ARTIFACT_HASH` = `artifact_hash == claim_target_hash of the claimed component`／`REPRODUCED_OUTPUT_HASH` = `artifact_hash == claim_target_hash`／`TRAIN_RUN_MANIFEST` = `artifact_hash = manifest sha256; manifest content lists claim_target_hash`／`TRAIN_TIME_CRYPTO_BINDING` = `artifact_hash = binding blob sha256`／EP JSON `proof_policy` の TENSOR_BINDING 行（4 grade・wildcard 展開込み） |
| **閉じた query** | ⭐**意味述語で張る**（文字列でなく）: 「その clause の `artifact_hash` は **当該 component の claim target 自身**か、それとも **別 artifact（manifest/blob）自身**か」。`proof_binding` 全 20 clause を展開して二分し、各 grade の proof set と突き合わせる |
| **反証条件** | (i) `ProofItem.ref` が Optional なら (a) FALSE ／ (ii) TENSOR_BINDING の rank 4 proof set に `artifact_hash` が **claim target 自身**である clause が在れば (d) FALSE ／ (iii) `TRAIN_RUN_MANIFEST` の ref が manifest でなく target 実体を指す旨の frozen 規定が在れば (b)(d) FALSE ／ (iv) rank 2/1 の clause に軸 B を満たすものが在れば (d) FALSE |
| **source pin** | frozen `00192d20ca00b654…` / `e63176af9bc3a246…` |
| **前回 Rs へ述べた形との差** | ⭐**軸 B では「locator は rank 3 のみ」= 原形が正しい**。ただし**当時は軸を明示していなかった**ため、軸 A と読めば偽になる曖昧な主張だった。⇒ **差は「真偽」ではなく「軸の明示」** |

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
⚠**訂正の履歴〔以下は SUPERSEDED な旧判定の叙述であり現行主張ではない〕**: v1 原形（軸未分離）→ v2「rank3 のみは不完全」（誤）→ v3「逆転は測定 artifact」（誤）→ **v4 で軸 A/B を分離し、軸 B では v1 原形が正しかったと確定**。⇒ **私は 2 度、軸を取り違えたまま『訂正』を重ねていた**。

**profile 適用（v2 から不変・pN 追認済）**: CLOSED_LOOP（rank 3）両 required ／ SHADOW（rank 2）両 required ／ OFFLINE_REPLAY（rank 2）**TB 免除・NORM required**。

---

## 集計

| claim | 前回 Rs へ述べた形 | 実測 |
|---|---|---|
| B1-C1 | `ArtifactSlot` に ref 無し | ✅ **そのまま成立** |
| B1-C2 | locator は rank 3 のみ | ✅ **軸 B では成立**（原形が正・当時は軸が未明示で曖昧） |
| B1-C3 | 最初の slice は SHADOW rank 2 | ⛔ **根拠なし**（統治文書は沈黙・決定事項） |
| B1-C4a | 両 slot に同型で効く | ⛔ **偽** — **schema 層に限定してのみ成立** |
| B1-C4b | （前回は主張していない） | ⚠ **end-to-end は非同型**（proof 層 rank4 + profile 層 OFFLINE_REPLAY） |

**⇒ 集計（v5 現行・C4 分割後は 5 項目）**: **そのまま成立 = C1 / C2（軸 B）の 2 件**、**軸の明示が要った = C2**、**根拠なし = C3**、**schema 層のみ成立 = C4a**、**前回未主張 = C4b**。⚠**v1-v4 の「そのまま成立は 1 件のみ」は、C2 を誤って否定していた期間の集計であり撤回**する。

⚠**訂正の系譜（v6 現行形・pN V5 指摘で置換）**: **C2 = v1 原形「locator は rank 3 のみ」は軸 B において正しかった**。v2（「不完全」）と v3（「逆転は測定 artifact」）は**いずれも誤訂正**であり、原因は**軸 A（hash association）と軸 B（target-byte locator）の混同**。**v4 で軸を分離し、原形が正しいと確定**。⇒ **訂正が誤りだったのであって、原主張が誤りだったのではない**。C4 = v2 で profile 非対称を訂正 → **v4 で C4a（schema 層・真）/ C4b（end-to-end・非同型）に分割**。
⚠**この事例の教訓**: **「訂正を重ねること」自体は正しさに近づく保証にならない**。軸を取り違えたまま訂正すると、**正しい主張から遠ざかる方向に 2 回進んだ**（v1 正 → v2 誤 → v3 更に誤 → v4 で復帰）。

## 帰結（事実の記述であり提案ではない）

- **B1-C3 が未決である限り、「locator がどの grade / profile を覆う必要があるか」が定まらない。**
- ⛔**【撤回・v5】** ~~B1-C2 の訂正により「rank 2 に locator が無い」という前回の動機づけは成立しない~~ — **この記述は軸の取り違えに基づく誤り**。軸 B では **rank 2 に locator が無いことは TRUE のまま**であり、動機づけの成否は **C3 が決まるまで判定できない**（下の行が現行形）。
- ⇒ **前提が確定するまで選択肢の集合を確定できない**。本 artifact は選択肢を提示しない。
- ⚠**「rank 2 に locator が無いこと」は依然 TRUE**（軸 B）。⛔ただし v2/v3 が書いた「**だから A′ の動機づけが成立しない**」は撤回済 — 動機づけの成否は **C3（slice がどの profile / grade で走るか）が決まってはじめて言える**。
- ⛔**v2/v3 の「絞り込み」は v4 で撤回**: DC-1 は **pre-B の早期 run にのみ効く**ため、B/C 後に走る指定 slice では **CLOSED_LOOP を含む 3 profile すべてが未決**。
- **残る帰結（弱めた形で成立）**: **OFFLINE_REPLAY は TENSOR_BINDING を免除する**（C4b）ため、**C3 の決定が「TB の locator が slice に必要か否か」自体を左右する** ⇒ **C3 は locator 設計の上流**。この帰結は 3 profile 未決のままでも成立する。

## 未測定（本 artifact が主張していない事項）

- ~~`normalization` slot の grade 別 proof set~~ → **v3 で測定済**（`B1-C4b` の表）。⚠v2 は「未測定」と書きながら C4 で全 profile の locator gap を総括しており **scope 不整合**だった（pN B4-3）。
- slice の実行 profile を定める**べき**主体（Rs / VT-DESIGN のいずれか）— これは統治の問題であり本 artifact の射程外
- 選択肢の集合（A/A′/B が正しい分割かを含む）
