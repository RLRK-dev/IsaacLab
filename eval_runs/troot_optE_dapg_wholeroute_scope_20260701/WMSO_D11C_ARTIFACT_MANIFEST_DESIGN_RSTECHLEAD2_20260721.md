# WMSO D1.1-C `artifact_manifest` — DESIGN v1

- node `T-WMSO` D1.1-C／著者 = `w2:pQ` RS-TECH-LEAD2／作成 = **2026-07-21 14:2x JST**（shell 実測）
- **解錠根拠** = Rs scope 承認（逐語「進んで」・custody `WMSO_RS_D11C_SCOPE_APPROVAL_CUSTODY_20260721.md` sha256 `2b64a66352ce5f50…` @ `d57ec90df1`）。⚠**解錠範囲の切り分けは CC1 の解釈**（同 custody §4）
- **scope の正** = `WMSO_D11C_SCOPE_PREREG_RSTECHLEAD2_20260721.md`（`d9caaffcf29d9524…` @ `1860edcc1c`）§2 IN / §3 OUT。本 doc は IN の外へ出ない
- **土台（凍結・編集しない）**: contracts_v2 `00192d20ca00b654…`／EP md `c474acea7c58acc2…`／EP JSON `e63176af9bc3a246…`／tensor_binding v13 `5a1874d3be8b98b8…`
- ⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**。本 doc は設計書面のみ

## 0. 中心構造

```text
RunArtifactManifest = 「1 回の run が実際に用いた artifact 群を content-address で pin した記録」。
役割: (a) 凍結 EP の TRAIN_RUN_MANIFEST proof が resolve する実体を与える
      (b) run の substrate を明示し、異なる substrate の silent pooling を機構で禁じる
      (c) grade 別 proof obligation に対し「どの field が実体を供給するか」の全域写像を与える
      (d) 凍結 B が C へ手渡した 3 carry（U-2 producer pin / U-5 両段 binding / U-6 topology metadata）を記録する
⛔ manifest は判断しない。何を採用し何を棄てるかの policy は本 doc の外（DDR #26 = Rs）。
```

- **反循環規則（凍結 v13 `:23` の構造 pattern を継承）**: manifest は **自身の hash・自身と同一であることを主張する任意の hash** を内包しない。⇒ ⭐**`TRAIN_TIME_CRYPTO_BINDING` blob は manifest の外部 artifact**（凍結 EP `:117` = blob が `(claim_target_hash, train_run_manifest_hash)` を束ねる）。**manifest が TTCB hash を内包すると `manifest_hash → TTCB → manifest_hash` の不動点**になり、D1.1-A M2 循環・D1.1-B D-2 と同型の再発になる。TTCB は `EvidenceRecord.proof` が携える。
- **直列化 = 凍結 §2 WCJ を適用**（新 canonicalization を作らない）。凍結 v13 `:24` の **B-declared 3 規約**（Optional は明示 `null`／`int` は `type(x) is int`（`bool` 拒否）／tuple → array）を **C も継承**する。C-declared の追加は §6 の 1 件のみ。

## 1. 型定義（C-internal 新 schema。凍結型は参照のみ・改造しない）

```python
@dataclass(frozen=True)
class ArtifactRef:                  # 単一 artifact の pin
    role: str                       # 供給写像 §3 の key（ASCII・NFC・非空）
    locator: str                    # resolve_artifact に渡す ref
    artifact_hash: str              # 64-hex lowercase

@dataclass(frozen=True)
class ProducerArtifactPin:          # U-2（凍結 v13 `:375`）
    producer_role: str              # belief / vision 等、definition が宣言する producer の役割
    producer_schema_hash: str       # 64-hex — 凍結 B が identity に参加させる schema 水準の hash
    producer_artifact_hash: str     # 64-hex — encoder weights 等、artifact 水準の実体

@dataclass(frozen=True)
class StageBindingRecord:           # U-5（凍結 v13 `:169` が外部照合を要求）
    rl_stage_tensor_binding_hash: str          # 64-hex
    bc_stage_tensor_binding_hash: str | None   # demo 系 lineage ⇒ 64-hex 必須 / RL_ONLY・NOT_APPLICABLE ⇒ null 必須

@dataclass(frozen=True)
class ManifestMetadata:             # U-6（凍結 v13 `:380`）— 契約層に束縛しない記録専用
    chain_topology_class: str | None
    recorded_at_utc: str            # RFC3339・秒精度・"Z" 固定

@dataclass(frozen=True)
class RunArtifactManifest:
    manifest_schema_version: str    # "1.0"（既知版 allowlist で fail-closed）
    run_id: str                     # ASCII・NFC・非空。identity ではなく人が辿るための label
    substrate_id: str               # ⭐必須（§2）
    skill_definition_hash: str      # 64-hex — 本 run が属する definition（凍結 §1.5 の値）
    identity_kind: str              # 凍結 IdentityKind の member 名
    training_lineage: str           # 凍結 TrainingLineage の member 名
    code: CodeProvenance            # {source_commit: 40-hex}
    config: ConfigHashes            # {final_training_config_hash, bc_config_hash, runtime_config_hash: str|None}
    model: ModelArtifacts           # {final_artifact_hash, model_architecture_hash, normalization_artifact_hash: str|None}
    data: DataArtifacts             # {demo_dataset_hash: str|None}
    evaluator: tuple[ArtifactRef, ...]          # 本 run の evidence 生成に用いた evaluator artifact
    evidence_policy_definition_hash: str        # 凍結 EP `:7` = e7ca43093084c167…（版の取り違え検出）
    evidence_policy_semver: str                 # 凍結 EP `:12`
    producers: tuple[ProducerArtifactPin, ...]  # U-2
    stage_bindings: StageBindingRecord          # U-5
    claims: tuple[str, ...]                     # ⭐64-hex の claim_target_hash 群（凍結 EP `:116` の content_must_list を満たす実体）
    metadata: ManifestMetadata                  # U-6

manifest_hash = sha256(WCJ_bytes(RunArtifactManifest))
```

- ⭐**`claims` が凍結との接続点**: 凍結 EP `:116` `manifest_content_rule` =「TRAIN_RUN_MANIFEST の content が `claim_target_hash` を列挙していること、`resolve_artifact` 経由で検査」。⇒ `claims` に当該 component の `claim_target_hash` が無ければ **凍結側の `E_PROOF_MISBOUND`** で落ちる。**新 code を作らない**（reuse-first）。
- **`manifest_hash` = sha256(canonical bytes)**: 凍結 EP `:140` は TRAIN_RUN_MANIFEST の `artifact_hash` を「manifest sha256」と定義する。⇒ **配布 bytes は WCJ bytes そのものでなければならない**（§6・`E_MANIFEST_NONCANONICAL_BYTES`）。凍結 v13 §7 が負例として挙げた「`sha256(raw)` は合うが `H_WCJ(parse(raw))` が合わない」経路を、C 側でも塞ぐ。
- **識別子でないもの**: `run_id` / `metadata` は人間可読 label であって identity ではない。ただし **hash-visible**（manifest_hash に入る）— 記録の改変を検出可能にするため。⇒ 同一 run の再記録は別 manifest_hash になる（意図的）。

## 2. `substrate_id` の必須化と区別機構（IN-2）

**由来（新規要求ではない）**: 凍結 contracts_v2 `:570` carry (i) 逐語「D2 transition data = 修正済み clean substrate のみ・旧 contaminated log は明示 **substrate_id** を付け silent pooling 禁止」／凍結 v13 `:376` 逐語「data の substrate 識別 = D1.1-C `substrate_id`」。

**機構（3 述語のみ。W-1 の遵守）**:

| # | 述語 | 違反 code |
|---|---|---|
| S-1 | `substrate_id` が存在する（欠落・空文字を拒否） | `E_MANIFEST_SUBSTRATE_ABSENT` |
| S-2 | 構文適合（ASCII・NFC・`[A-Za-z0-9_.:-]{1,64}`） | `E_MANIFEST_SUBSTRATE_MALFORMED` |
| S-3 | 集約時、2 つ以上の異なる `substrate_id` を **宣言なしに** 同一集合へ入れない | `E_MANIFEST_SUBSTRATE_POOLED` |

- ⛔⛔**値では弾かない（W-1）**: 本設計は **どの `substrate_id` が良い/悪いかを一切知らない**。allowlist も denylist も grade 係数も持たない。述語は **存在・構文・相互比較（等値/非等値）** の 3 種に限る。⇒ **DDR #26 のどちらの裁定でも本機構は同一**であり、裁定を先取りしない。むしろ裁定を**実行可能**にする（ラベルが無ければ選別自体ができない）。
- **S-3 の「宣言」**: 複数 substrate を混ぜること自体は禁じない。禁じるのは **黙って混ぜること**。混成は `substrate_id` を **item ごとに保持したまま**上位に `substrate_ids: tuple[str, ...]`（bytes 昇順・重複なし）を明示宣言した集合としてのみ表現できる。⇒ 「混成である」という事実が hash-visible になる。
- ⚠**本機構が保証しないもの**: `substrate_id` の値が**真実であること**は保証しない（自己申告である）。保証するのは「無記名でないこと」と「黙って混ざらないこと」。⇒ §10 の declared open に記す。

## 3. grade 別 proof obligation の実体供給写像（IN-3）

⚠**本節が設計するのは obligation の供給写像であって proof の生成ではない**（pY② の確認事項をここで明示的に discharge する）。proof を作る行為は impl leg = OUT#6（CLOSED）。

凍結 EP `:236-240` の **ProofKind 15 種を 3 class に全域分類**する（15/15・欠落 0）:

| class | ProofKind | manifest 側の供給元 |
|---|---|---|
| **A. manifest 供給**（6） | `TRAIN_RUN_MANIFEST` | manifest 自身（`artifact_hash = manifest_hash`・content = `claims`） |
| | `SOURCE_COMMIT` | `code.source_commit`（凍結 `:132-133` = LEARNED は `training_provenance.final_source_commit`／SCRIPTED・WAIT は `execution_provenance.source_commit` と一致必須） |
| | `CONFIG_HASH` | `config.*` — 凍結 `:124-129` の **(identity_kind, training_lineage, component) 全域 map** が選ぶ slot（LEARNED×{RL_ONLY,BC_ONLY,DEMO_PLUS_RL} → `final_training_config_hash`／LEARNED×BC_THEN_RL は TD のみ `bc_config_hash`・他 12 = final／SCRIPTED・WAIT → `runtime_config_hash`） |
| | `FINAL_ARTIFACT_HASH` | `model.final_artifact_hash` |
| | `NORMALIZER_HASH` | `model.normalization_artifact_hash`（凍結 `:137` = slot KNOWN 時のみ・EXPLICIT_NONE は N/A） |
| | `EVALUATOR_ARTIFACT` | `evaluator[].artifact_hash`（凍結 `:139` = `evaluator_registry` の member であること） |
| **B. definition 由来**（2） | `INPUT_SCHEMA_HASH` / `OUTPUT_SCHEMA_HASH` | ⛔**manifest は供給しない**。凍結 `:135-136` = `H_WCJ(semantic_obs/action_schema)` = definition から決まる |
| **C. evidence 過程の外部 artifact**（7） | `TRAIN_TIME_CRYPTO_BINDING` | ⛔**manifest 外**（§0 反循環）。blob が `(claim_target_hash, manifest_hash)` を束ねる |
| | `REPRODUCTION_PROCEDURE` / `REPRODUCED_OUTPUT_HASH` / `RECONSTRUCTION_SOURCES` / `COMPATIBILITY_TEST` / `UNRESOLVED_DIFFERENCES` / `DIMENSION_SOURCE` | ⛔**manifest 外**。再現・復元・評価の産物であり run の記録ではない |

- ⭐**grade 別の帰結（凍結 EP `:76-113` から機械的に従う）**: `EXACT_TRAIN_TIME` の 13 cell は**全て** `TRAIN_RUN_MANIFEST` を要求する ⇒ **EXACT を主張する record は必ず manifest を運ぶ**。`HASH_BOUND_REPRODUCED` / `RECONSTRUCTED_COMPATIBLE` / `DIMENSION_ONLY` の required set に `TRAIN_RUN_MANIFEST` は**含まれない**。
- ⛔⛔**ここから出る構造的制約（本 doc 最重要・§10 open-1）**: 凍結 EP `:71` `_domain` 逐語「**exact** required ProofKind set」＋ `:147` `foreign_kind: E_PROOF_KIND_FOREIGN` を素直に読むと、**required set は集合として厳密**であり、HB 以下の record が `TRAIN_RUN_MANIFEST` を**追加で携えることはできない**（foreign 扱い）。⇒ **manifest は certify 時、EXACT claim 経由でしか到達できない**。
  - ⇒ §2 の substrate 機構・§4 の U-5 照合を **契約層で全 grade に効かせることはできない**。効かせるには **凍結 schema delta（Rs review）= OUT#4** が要る。
  - ⇒ 本 doc は delta を作らず、**到達できる面（EXACT）では契約層・届かない面では package 層（§6）**という 2 面構成にする。**package 層は certificate を無効化しない**（凍結 `:148-155` の trust boundary を動かさない）。
  - ⚠**この「exact set = 追加不可」は凍結の読みであり、私の断定ではない** — pS / pY に**明示の確認を依頼する**（読みが逆なら open-1 の重さが変わる）。

## 4. carry 機構（IN-5）と fail-closed 規則

### 4.1 U-2 producer artifact pin（凍結 v13 `:375`）

- definition が宣言する producer role 集合に対し、`producers` が**全 role を pin**していること。欠落 = `E_MANIFEST_PRODUCER_PIN_MISSING`。
- ⛔**detect であって prevent ではない**（凍結 v13 `:375` が v1 の over-claim を撤回した所と同一）。**発行済 certificate の下で後続 run が encoder を差し替えることを、本機構は阻止しない**。阻止は closed-loop eligibility 検査 = OUT#2。⇒ この限界を §10 に declared open として残す。

### 4.2 U-5 両段 binding 記録（凍結 v13 `:169`）

凍結 v13 は `IDENTICAL` を「hash を内包しない relation 宣言」とし、**外部照合を D1.1-C の manifest に委任**した。本 doc の履行:

| 条件（凍結 `LineageBindingDeclaration`） | manifest 側の要求 | 違反 code |
|---|---|---|
| `bc_stage_binding == None`（RL_ONLY・NOT_APPLICABLE） | `bc_stage_tensor_binding_hash` = null 必須 | `E_MANIFEST_STAGE_BINDING_MISSING` |
| `relation == IDENTICAL` | 両 field 非 null **かつ相等** | 不一致 = `E_MANIFEST_STAGE_BINDING_CONFLICT` |
| `relation == EXPLICIT_SUPERSEDE` | `bc_stage_tensor_binding_hash == demo_dataset_binding_hash`（凍結 `:161`） | 同上 |

- ⭐**discharge の向き**: 上記が満たされたときに限り、凍結側の `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED`（v13 `:230`）が**解消**する。満たされない/manifest に到達できない場合は**未解消のまま**（fail-closed・沈黙で通さない）。
- ⚠ 到達可能性は §3 open-1 に従う（EXACT 以外は package 層で検出）。

### 4.3 U-6 topology metadata（凍結 v13 `:380`・W-2）

- `chain_topology_class` は **`ManifestMetadata` の記録専用 field**。⭐**delta-free の根拠 = 凍結 `SemanticFieldSpec` = {field_id, dtype, shape, unit, frame}・`Dtype = {FLOAT32, INT32, BOOL}` は数値専用**であり、categorical な class 名を**格納できない**（pS `:27` の独立確認と一致）。⇒ 凍結型に押し込まず manifest metadata に置くのが唯一の非-delta 経路。
- ⛔**凍結 v13 `:338` が既に述べた限界をそのまま継承**: 本 carry は台帳差を **検出可能**にするだけで **§5D の穴（同 dtype/shape で意味の異なる台帳）を塞がない**。塞ぐには契約層束縛 = schema delta = OUT#4。**「carry したので閉じた」とは書かない**。

### 4.4 code / 拒否規則の呼称（P-1 の履行）

⚠ 本 doc で **「code」= error code と拒否規則の *設計*** を指し、**実装（動く code）を含まない**。同様に **「package / CI」= 構造と check の *仕様*** であって build ではない。**実装・実行は OUT#6（CLOSED）**。D1.1-B が `E_BINDING_*` を実装せず設計したのと同型。

## 5. 新規 error code 一覧（7 件・C 側のみ。凍結 code は再利用し複製しない）

`E_MANIFEST_SUBSTRATE_ABSENT` / `E_MANIFEST_SUBSTRATE_MALFORMED` / `E_MANIFEST_SUBSTRATE_POOLED` / `E_MANIFEST_STAGE_BINDING_MISSING` / `E_MANIFEST_STAGE_BINDING_CONFLICT` / `E_MANIFEST_PRODUCER_PIN_MISSING` / `E_MANIFEST_NONCANONICAL_BYTES` ＋ 版 allowlist の `E_MANIFEST_SCHEMA_VERSION_UNKNOWN`（凍結 v13 `E_BINDING_SCHEMA_VERSION_UNKNOWN` と同型）。

- ⭐**再利用（新設しない）**: `claims` 欠落 = 凍結 `E_PROOF_MISBOUND`／manifest 解決不能・sha 不一致 = 凍結 `E_PROOF_ARTIFACT_UNRESOLVED`（`:152`）／evaluator 非登録 = 凍結 `E_EVALUATOR_UNKNOWN`（`:158`）／未知 JSON field・duplicate key = 凍結 §5C strict decoder。

## 6. minimal JCS の package 展開（IN-4）

- **canonical 適用対象** = ①`RunArtifactManifest` ②evidence bundle ③配布 metadata。いずれも **凍結 §2 WCJ + 凍結 v13 `:24` の B-declared 3 規約**で直列化する。
- **C-declared 追加は 1 件のみ**: ⭐**配布 artifact の bytes は canonical bytes と byte 一致でなければならない**（`E_MANIFEST_NONCANONICAL_BYTES`）。理由 = 凍結 EP `:140` が `artifact_hash = manifest sha256` を **bytes に対して**定義するため、非 canonical bytes を配ると `sha256(bytes)` と `H_WCJ(parse(bytes))` が乖離する。
- **package 層 check（仕様のみ・実装は OUT）**: 配布 package は manifest を 1 本必ず含む／`evidence_policy_definition_hash` が凍結値と一致／§2 S-1..S-3 が成立／§4.2 の stage 記録が成立／§4.1 の producer pin が完備。**これは検出であり、certificate の可否を変えない**（§3 open-1）。
- ⛔**fail-closed 実行コマンドの事前登録（凍結 v13 `:356` H2 教訓の継承）**: package check は **素の `python3` を直接呼ぶ**こと。**`./isaaclab.sh -p` 経由で検証してはならない** — 同 wrapper は破損入力に対し traceback を出しつつ **rc=0** を返す（v13 実測・AGENTS.md「Exit-code exception」が明記する既知 hazard）。⇒ 本 doc の fixture builder も **stdlib のみ**に依存させ、任意の `python3`（≥3.8）で可搬に fail-closed とする。

## 7. Golden vectors / invalid corpus（**設計宣言・fixture の bank は次版**）

⚠ D1.1-B v1 は **fixture 未 bank で prereg 違反**（v13 §12 D-4）。同じ轍を踏まないため、**本 v1 は「fixture 未 bank」を明示**し、two-key 提出前に bank する。

- **golden（4 本予定）**: M-1 最小 SCRIPTED（learned 系 field は全 null）／M-2 LEARNED × RL_ONLY（`bc_stage` null）／M-3 LEARNED × BC_THEN_RL（`IDENTICAL` 両段一致・`bc_config_hash` 非 null）／M-4 混成 substrate 宣言（`substrate_ids` 2 値）。
- **判別性の positive control**: M-3 の両段 hash を 1 文字変えた variant が **別 hash になり `E_MANIFEST_STAGE_BINDING_CONFLICT` を発火**すること。
- **invalid corpus（拒否必須）**: `substrate_id` 欠落・空・構文違反／無宣言の混成／`IDENTICAL` で両段不一致／RL_ONLY で `bc_stage` 非 null／producer role 欠落／64-hex 違反／40-hex 違反（`source_commit`）／float・NaN・`"Infinity"`／bool を int field に混入／未知 enum member／未知 JSON field／duplicate key／未知 `manifest_schema_version`／非 canonical bytes／`claims` に当該 `claim_target_hash` 不在。
- ⚠**代表性を主張しない**（v13 D-31 と同じ規律）: golden は型網羅が目的の合成物であり、実 run の代表性は主張しない。

## 8. Test plan（impl GO 後 — 設計時宣言）

型 round-trip（encode→decode→encode の bytes 同一）／golden 4 本の hash 一致 ＋ 判別 variant が別 hash ／invalid corpus 全拒否 ／**凍結 code が発火することの positive control**（`claims` 欠落 → 凍結 `E_PROOF_MISBOUND`／解決不能 locator → 凍結 `E_PROOF_ARTIFACT_UNRESOLVED`。**C 側 code でなく凍結 code が出ること** = reuse の正しさの実証）／§3 class A 6 種の供給写像が凍結 `proof_binding` と一致すること（表駆動）／⭐**到達性の負例**: HB grade の record に `TRAIN_RUN_MANIFEST` を足すと `E_PROOF_KIND_FOREIGN` になること（open-1 の読みの真偽を機械で決着させる test）。

## 9. Reuse gate 記録（AGENTS.md「Reuse / official-specification gate」）

- 既存の再利用 = 凍結 WCJ（新 canonicalization を作らない）／凍結 error code 4 種（§5）／凍結 `resolve_artifact` `resolve_git_commit`（新 resolver を作らない）／v13 の fixture builder 方式（`--verify` 非破壊 + negative control 両経路）。
- 新規作成が必要だった理由 = **run 単位の artifact 記録型が凍結側に存在しない**（凍結の 3 file 全域で `RunArtifactManifest` 相当の型は 0 件・pQ 実測）。凍結 EP は `TRAIN_RUN_MANIFEST` を **proof kind として参照する**のみで、その**中身の型を定義していない**。

## 10. Open points（⛔`open = 0` を宣言しない）

1. ⭐**manifest の到達可能性が EXACT に限られる**（§3）— 凍結の「exact required set」読みに依存。**pS / pY に読みの確認を依頼**。読みが正なら、HB 以下での substrate / stage 照合は package 層 = 検出のみ。契約層で閉じる路は schema delta（Rs review）。
2. **U-2 は detect であって prevent でない**（§4.1）— 凍結 v13 の撤回済 over-claim を再導入しない。
3. **U-6 は §5D の穴を塞がない**（§4.3）— 凍結 v13 `:338` の限界をそのまま継承。
4. **`substrate_id` の値の真正性は保証しない**（§2）— 自己申告。真正性を要求するなら TTCB 相当の束縛が要り、それは本 chunk の外。
5. ⭐⭐**prereg に無い凍結からの委任を 1 件発見**: 凍結 v13 `:185` は **`binding_schema_version` bump 時の移行手続（再 certify + transition 行の系譜記録）を「D1.1-C の manifest 側で定義」と委任**している。しかし**承認済 prereg §2 IN の 5 項に本項は無い**。⇒ **本 doc は設計しない**（scope 自己拡張の禁）。**scope 判断を Rs / pS へ上程**する。
6. **fixture 未 bank**（§7）— two-key 提出前に bank する。本版は宣言のみ。

## 11. Module layout（impl GO 時に確定 — 宣言のみ）

`manifest.py`（型 + WCJ 直列化）／`manifest_validate.py`（§2/§4/§5 の拒否規則）／`wmso_d11c_fixtures/`（golden + `build_goldens.py`・stdlib のみ）。

## 12. 版歴

- **v1**（2026-07-21 14:2x）= 初版。Rs scope 承認後の最初の authoring。prereg IN 5 項 + design 段 carry 4 件（P-1 §4.4／W-1 §2／W-2 §4.3／pY② §3 冒頭）を fold 済。
- **次段** = fixture bank → ⛔**5 体 CC Debate（L2 の debate は本 design 段で発火・waived ではない）** → 設計軸 pS + evidence 軸 pY の two-key → ⛔Rs freeze 判断。
