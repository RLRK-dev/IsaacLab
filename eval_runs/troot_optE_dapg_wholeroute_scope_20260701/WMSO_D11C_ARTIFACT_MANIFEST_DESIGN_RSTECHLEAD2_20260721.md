# WMSO D1.1-C `artifact_manifest` — DESIGN **v2.1（縮小版・fixture 同梱）**

- node `T-WMSO` D1.1-C／著者 = `w2:pQ` RS-TECH-LEAD2／作成 = **2026-07-21 15:1x JST**（shell 実測）
- **v1 は SUPERSEDED**（`726f684c52421928…` @ `33e67626da`）— 5 体 CC Debate cycle-1 = **FAIL**（判定記録 `9851f165a5fc45eb…` @ `7f6d038a30`・ACCEPT 24 件）
- **縮小の判断根拠 = Rs 指示「確かな前提条件があるほうを選べ」（2026-07-21 15:0x）**
- **scope の正** = prereg（`d9caaffcf29d9524…` @ `1860edcc1c`）§2 IN / §3 OUT
- 土台（凍結・編集しない・**4 file**）: contracts_v2 `00192d20ca00b654…`／EP md `c474acea7c58acc2…`／EP JSON `e63176af9bc3a246…`／tensor_binding v13 `5a1874d3be8b98b8…`
- ⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**

## 0. 本版の範囲 —「凍結が名指しで委任した 2 件」に限定

本版が設計するのは、**凍結文書が D1.1-C を名指しして委任し、他に owner が存在しない 2 件**のみ:

| 本版が設計する | 委任元（逐語確認済） |
|---|---|
| **U-5 = 両段 binding の記録機構** | 凍結 v13 `:169`「検証 = **D1.1-C の run manifest が両段に同一 `tensor_binding_hash` を記録していること**を外部照合」／`:378` |
| **`substrate_id` の必須化と区別機構** | 凍結 contracts_v2 `:570` carry (i)「旧 contaminated log は明示 **substrate_id** を付け silent pooling 禁止」／凍結 v13 `:376`「data の substrate 識別 = **D1.1-C `substrate_id`**」 |

⛔**本版が設計しないもの（隠さず宣言）**: prereg §2 **IN-1（manifest 型の全体）／IN-3（grade 別 proof obligation の供給写像）／IN-4（minimal JCS の package 展開・CI）**。
⇒ ⭐**本版で D1.1-C は閉じない**。後続版が必要であり、その版は本版の型を拡張する（この二度手間は「前提の確かさ」と引き換えに受け入れたもの）。

**選択理由（前提の確かさで比較した結果）**: 上表 2 件の前提は **凍結の逐語 2 本のみ**で、いずれも実測済み・**DDR #26 の裁定に非依存**（pS 設計軸で確認）。対して IN-1/3/4 は §8 の未決 5 件（repo 内の別 canonicalization ／ DDR #35 ／ open-5 の scope 欠落 ／ Rs 判断 (a)(b) ／ 前提訂正後の §3・§6 再導出）に乗る。

## 1. v1 の中心前提は **FALSE**（訂正記録）

- **誤っていた主張（v1 §3 open-1）**: 「required set は exact ゆえ、HB 以下の record は `TRAIN_RUN_MANIFEST` を追加携行できない ⇒ manifest は EXACT 経由でしか到達しない」。
- **正しい読み**: `E_PROOF_KIND_FOREIGN` は **component 意味論**（凍結 EP md `:114`「component に意味を持たない kind の混入」／`:129(iii)` 例示「POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH」）。`TRAIN_RUN_MANIFEST` は **EXACT 13/13 cell で required**（pQ 実測）＝ どの component にも意味を持つ ⇒ 非 foreign。
- ⭐**決定脚（pS 提示・pQ が閉じた列挙で再測）**: 凍結に **set-equality / 超過拒否の規則が存在しない**。凍結 3 file の proof 系 error 語彙 = `ARTIFACT_UNRESOLVED` / `CONFLICT` / `INSUFFICIENT` / `KIND_FOREIGN` / `MISBOUND` / `PAYLOAD_MISSING` / `REF_MALFORMED` のみで、**非 foreign な余分を拒否する code は 0 件**。`superset` / `excess` / `extraneous` = 3 file とも 0 hit。⚠**誠実な範囲 = error code 語彙上の不在**（散文規則の不在までは主張しない）。
- **誤りの型**: 「**required SET が厳密（spec の性質）**」を「**record が超過携行不可（instance の禁止）**」に取り違えた。
- ⭐**携行可 ≠ EXACT 達成**: grade は evaluator の測定値（凍結 `E_GRADE_MISMATCH`）ゆえ、HB の record が manifest を携えても昇格しない。
- **機序（自己記録）**: 凍結 EP の **JSON の 1 文字列**だけを読み、**自分が土台に挙げた EP markdown を開かなかった**。

### 1.1 ⛔ 凍結文書への波及（Rs 判断待ち・誰も編集していない）

- 凍結 v13 **`:256`**（一次 locus = D-1..D-4 選定表・`B1D-A`）逐語「`proof_policy._domain` = 「exact required ProofKind set」＋ `E_PROOF_KIND_FOREIGN`」／**`:471`** は「kind」を落とした再掲（pY 指摘・pQ 実測）。
- **限局している**: foreclose された案は「**rank 2 に proof kind を追加要求**（= required set の拡張 = frozen schema delta）」であり、その決定脚は **delta 要求**（`:256`「**D-3 に合流**」が証拠・pQ 実測）。`E_PROOF_KIND_FOREIGN` の併記は**不正確だが冗長な二次引用で load-bearing でない**（pS 設計軸 read）。
- **採択 D-1 は非依存**: 積極根拠 `:252`（frozen delta 不要／1 hop／B 側宣言 1 個／`:396` の provenance 意味論適合）も、自身の反証条件 `:258-262`（`source_ref` 意味論・registry 衝突・resolver 到達性・1 hop）も **proof kind 集合に言及しない**（pQ 実測）。
- ⛔**Rs 判断 2 件**: **(a)** 凍結 v13 `:256`/`:471` の併記訂正（**凍結編集 = Rs 専権**）／**(b)** 採択 D-1 が無影響であることの**正式確認**。⚠ pQ・pS・pY のいずれも「D-1 が覆る」とも「不変」とも宣言しない。
- 記録: pY custody `b602a8c8030d47a7…` @ `337d08d787`／pS consult `b4ec93173db6c24c…` @ `a31adca295`（pS は 0-commit ゆえ pQ が bank）。

## 2. U-5 — 両段 binding の記録機構

```python
@dataclass(frozen=True)
class StageBindingRecord:
    execution_stage_tensor_binding_hash: str | None  # 64-hex。NOT_APPLICABLE ⇒ null 必須 / 他 4 lineage ⇒ 必須
    bc_stage_tensor_binding_hash: str | None         # demo 系 lineage ⇒ 必須 / RL_ONLY・NOT_APPLICABLE ⇒ null 必須
```

- 命名 = 凍結の claim target（EP JSON `:29` `execution_bundle.tensor_binding.artifact_hash`）に合わせる。SCRIPTED/WAIT にも `tensor_binding` slot 概念は在るため「RL 段」と呼ばない。
- **lineage 別の全域表**（凍結 `TrainingLineage` 5 member を全被覆）:

| lineage | execution 段 | bc 段 | 違反 |
|---|---|---|---|
| `NOT_APPLICABLE` | null 必須 | null 必須 | 非 null = `E_MANIFEST_STAGE_BINDING_PRESENT` |
| `RL_ONLY` | 64-hex 必須 | null 必須 | 欠落 = `E_MANIFEST_STAGE_BINDING_MISSING`／bc 非 null = `…_PRESENT` |
| `BC_ONLY` / `BC_THEN_RL` / `DEMO_PLUS_RL` | 64-hex 必須 | 64-hex 必須 | 欠落 = `…_MISSING` |

- **凍結 declaration との突合**（凍結 v13 `:158-166`）: `relation == IDENTICAL` ⇒ **両 field が相等**／`relation == EXPLICIT_SUPERSEDE` ⇒ `bc_stage_tensor_binding_hash == tensor_binding_spec.demo_dataset_binding_hash`（⚠ **`data` 側の dataset content hash とは別物**・名前が近いので完全修飾する）。不一致 = `E_MANIFEST_STAGE_BINDING_CONFLICT`。
- ⛔⛔**「解消する」とは書かない（v1 の過大主張を撤回）**: 凍結 `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` は **certify 時の cross-artifact 検査**（v13 `:230`）であり、凍結 `certify_inputs`（EP JSON `:149`）に manifest は**入っていない**。§1 の訂正により record は manifest proof を携行できるが、**tensor-binding 検査器から解決済 manifest への wiring は凍結に存在しない**。⇒ **本版が与えるのは記録であって discharge ではない**（§8 open-3）。U-2・U-6 で凍結が既に行った detect-vs-prevent の区別を、U-5 でも同じ厳しさで守る。

## 3. `substrate_id` — 必須化と区別機構

```python
substrate_id: str                       # 本記録が pin する run の substrate
dataset_substrate_ids: tuple[str, ...]  # 本記録が pin する dataset の substrate 群（bytes 昇順・重複禁止）
```

| # | 述語 | 違反 code |
|---|---|---|
| S-1 | `substrate_id` が存在し非空 | `E_MANIFEST_SUBSTRATE_ABSENT` |
| S-2 | 構文適合（ASCII・NFC・`[A-Za-z0-9_.:-]{1,64}`） | `E_MANIFEST_SUBSTRATE_MALFORMED` |
| S-3 | `dataset_substrate_ids` が **非空**かつ **bytes 昇順・重複なし**（無記名 = 黙って混ぜた） | `E_MANIFEST_SUBSTRATE_POOLED` |

⚠**v2.1 訂正（fixture 作成中に判明・設計文が誤っていた）**: v2 の S-3 は「2 値以上のとき**その全値が列挙されている**」と書いていたが、これは**記録単体からは判定できない**（列挙漏れの有無は外部の dataset を見ないと分からない）。⇒ 記録内で決定可能な形（**非空・正規形**）に訂正し、**列挙の網羅性は producer の義務**として §8 open-9 へ移す。⭐**fixture が設計文を反証した実例**（凍結 v13 B-2「再現する hash は schema 適合を証明しない」と同じ効用）。

- ⛔⛔**値では弾かない（W-1）**: 述語は **存在・構文・相互比較**の 3 種のみ。allowlist も denylist も grade 係数も持たない。⇒ **DDR #26 のどちらの裁定でも機構は同一**。
- ⛔**v1 の誤りを訂正（A-22）**: v1 は「宣言すれば混成してよい」と書き、**許可を与えていた**＝ policy の先取り。本版は **検出のみ**を行い、`dataset_substrate_ids` が 2 値以上なら **MIXED として記録する**。**混成が許容されるか否かは #26（Rs）の裁定**であり本設計は述べない。
- ⚠**保証しないこと**: 値の真正性（自己申告である）。保証するのは「無記名でないこと」と「黙って混ざらないこと」。
- ⚠**host が無い case（§8 open-4）**: **run をまたぐ pooling**（別 run の記録どうしを集約する時）を宿す object は、承認済 prereg の範囲に存在しない。本版は**発明せず**、未決として上程する。

## 4. 直列化と hash

- **凍結 §2 WCJ を適用**（新 canonicalization を作らない）＋ 凍結 v13 `:24` の B-declared 3 規約（Optional は明示 `null`／`int` は `type(x) is int`／tuple → array）を継承。
- ⭐**collection は集合として正規化**（v1 の欠落・A-4）: `dataset_substrate_ids` は **要素 bytes 昇順・重複禁止**。凍結 contracts_v2 `:178`（frozenset は文字列 bytes 昇順 array）の**再利用**であり新規則ではない。⇒ 同一内容が 1 つの byte 表現にしか写らない。
- ⭐**時刻を hash preimage に入れない**（v1 の誤り・A-5）: 記録時刻は **hash 対象外の付随 metadata** に置く。凍結 EP JSON `:5` が `metadata is OUTSIDE the hash input` としている先例に従う。⇒ 記録が run から再導出可能なままになる。
- **配布 bytes は canonical bytes と byte 一致であること**（`E_MANIFEST_NONCANONICAL_BYTES`）。⚠**これは検出であって阻止ではない**（v1 の「塞ぐ」を撤回・A-21）。⇒ 検査の実行箇所は §7 の builder（`--verify`）に置く。

## 5. 新規 error code = **7 件**（C 側のみ）= 拒否規則 6 件 ＋ builder 側 1 件（§4 の `E_MANIFEST_NONCANONICAL_BYTES`）

`E_MANIFEST_SUBSTRATE_ABSENT` / `E_MANIFEST_SUBSTRATE_MALFORMED` / `E_MANIFEST_SUBSTRATE_POOLED` / `E_MANIFEST_STAGE_BINDING_MISSING` / `E_MANIFEST_STAGE_BINDING_PRESENT` / `E_MANIFEST_STAGE_BINDING_CONFLICT`

- **再利用（新設しない）**: 解決不能・sha 不一致 = 凍結 `E_PROOF_ARTIFACT_UNRESOLVED`／未知 JSON field・duplicate key = 凍結 §5C strict decoder（**code ではなく decoder**）。
- ⚠ `E_MANIFEST_NONCANONICAL_BYTES` は §4 の検出用で builder 側。ProofKind enum の出典は **contracts_v2 `:236-240`**（v1 の引用 host 誤りを訂正・A-9）。

## 6. Reuse gate（AGENTS.md「Reuse / official-specification gate」）— **repo に対して再実行**

- ⚠**v1 の探索面は狭すぎた**（凍結 3 file と記載・実際は 4 file、しかも repo を見ていない）。
- ⭐**発見（未決）**: `thread_isaac_lab/wmso/d1/identity.py:80-82` に既存 `canonical_json()` = `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",",":"))` があり、**凍結 WCJ とは別物**（UTF-16 key 順・JCS escape・int 限定・NFC を課さない）。同 node 内に**互換でない正規化が 2 つ**存在する。⇒ **本版は判定しない**（§8 open-5）。
- **実行系の呼び方（原文どおりに引用する）**: AGENTS.md `:68` は guard wrapper が **`env_isaaclab/bin/python` を直接呼ぶ**理由として「`./isaaclab.sh -p` can mask non-zero Python exits」と述べる。⚠ v1 は「素の `python3`」と書き、AGENTS.md `:45` がむしろ `./isaaclab.sh -p` を prefer している点も落としていた（A-19）。⚠ rc の実測値は **凍結 v13 の測定**であり **C 側は未実測**。

## 7. Fixtures / test（**v2.1 で bank 済 — 宣言でなく実物**）

**banked**（`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11c_fixtures/` @ `b1053db355`）:

| file | 内容 | sha256（先頭 16） | canonical bytes |
|---|---|---|---|
| `carry_record_golden_A.json` | `NOT_APPLICABLE`（両段 null・単一 substrate） | `ce474f3ad393767a` | 224 |
| `carry_record_golden_B.json` | `DEMO_PLUS_RL` × `IDENTICAL`（両段一致・`dataset_substrate_ids` 2 値 = MIXED） | `f49d15698bf379c1` | 376 |
| `build_goldens.py` | 生成器 + 非破壊 `--verify`（stdlib のみ・dataclass 不使用ゆえ **3.8 で import 可**） | `837dc37ffd2d69b5` | 15819 |

- **negative control = 19 本**（拒否 14 + cross-artifact 2 + encoder 3）。⭐**生成経路と `--verify` 経路の両方で 19/19 発火**を実測（凍結 v13 の S-1 = 「control が生成 mode でしか走らない」の再発を回避）。変異は in-memory deepcopy のみ ⇒ `--verify` は非破壊（事後 sha256 2 本不変を実測）。
- ⛔**fail-closed 実行コマンド（事前登録・C 側で実測済）**:
  ```
  env_isaaclab/bin/python eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11c_fixtures/build_goldens.py \
      --verify eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11c_fixtures
  ```
  **実測（非 canonical bytes を注入・注入で sha が `ce474f3ad393767a` → `555ffe870dc6e899` に実際に変化したことを先に確認してから測定）**:

  | 呼び方 | rc |
  |---|---|
  | `python3` / `/usr/bin/python3` / `env_isaaclab/bin/python` / `env_isaaclab7/bin/python` | **1** |
  | `./isaaclab.sh -p` | ⛔**0（fail-open）** |

  ⇒ **AGENTS.md `:68` が明記する hazard を C 側で再現**（同 `:68` は guard wrapper が `env_isaaclab/bin/python` を直接呼ぶ理由として「`./isaaclab.sh -p` can mask non-zero Python exits」と述べる）。⛔**wrapper 経由で検証してはならない**。復元後 sha 一致・clean rc=0 も実測。
  ⚠**最初の測定は空振りだった**（key 順を変えたつもりが byte 同一で、全 interpreter rc=0 になった）。**壊れたことを sha で確認してから測る**手順に変更した — 「違う結果が出得ない試験は試験でない」の直接適用。
- ⛔**builder が検査しないもの**: 非 ASCII key の UTF-16 順の全域／JCS escape の全域／duplicate key（Python dict では表現不能）。**WCJ 完全性は impl の `canonicalize()` leg**（凍結 v13 と同じ境界宣言）。
- ⚠**代表性を主張しない**（合成物・型網羅が目的）。
- **次段の順序（A-24 の訂正）**: **fixture bank → cycle-2 の 5 体 debate → two-key（pS 設計軸 / pY evidence 軸）→ ⛔Rs freeze 判断**。上位 prereg の design Exit は「**機械可読 fixture 同梱 → debate**」であり、v1 の debate は 1 段早かった。

## 8. Open points（⛔`open = 0` を宣言しない）

1. ⛔**Rs 判断 2 件**（§1.1 (a)(b)）。
2. **本版が設計しない prereg IN-1 / IN-3 / IN-4** — 後続版。**D1.1-C は本版で閉じない**。
3. **U-5 は記録であって discharge でない**（§2）— certify 側の wiring が凍結に無い。
4. **run をまたぐ pooling を宿す object が承認済 scope に無い**（§3）。
5. **`identity.py:80-82` の別 canonicalization との関係**（supersede / 共存 / 衝突）が未測定（§6）。
6. **凍結 v13 `:185` が委任した版 bump 移行手続が、承認済 prereg §2 IN に無い**（v1 open-5 を継承）⇒ **IN 集合が既知の不完全**。scope 裁定 = Rs / pS。
7. **U-5 の捏造経路**（debate CC5 指摘）: `IDENTICAL` の等値検査は execution 段 hash の複写でも通る。⚠ ただし **凍結が委任したのは「両段に同一 hash を記録していること」の照合**であり、解決可能性の要求は**凍結を超える強化**になる ⇒ 本版は凍結どおりに実装し、**強化案として上程**する（pS / Rs）。
8. **prereg §4 carry の再掲（v1 で脱落・A-11）**: ③**#29 = demo 再記録**（198 demo・OUT#3）／⑤**#31 = trainer 実在**（manifest の実データ充填は trainer 実在に依存・機構の設計は非依存）。⇒ **`portfolio_has_IL` は本 chunk 完了だけでは true にならない**。
9. **`dataset_substrate_ids` の列挙が網羅的であること**は記録単体から判定できない（§3 の v2.1 訂正）。⇒ **producer 側の義務**として残る。機構で閉じるには dataset 実体を入力に取る検査が要り、それは本版の外。

## 9. 版歴

- **v1**（14:2x・`726f684c52421928…` @ `33e67626da`）= 初版。**debate cycle-1 = FAIL**（`9851f165a5fc45eb…` @ `7f6d038a30`・ACCEPT 24 件）。
- **v2.1**（本版・15:2x）= **fixture bank 済**（golden 2 + builder @ `b1053db355`）＋ **fail-closed rc を C 側で実測**（wrapper のみ rc=0 = fail-open を再現）＋ **§3 S-3 を判定可能な形へ訂正**（fixture が設計文を反証・残余は open-9）。
- **v2**（15:1x）= **縮小 + 全 fold**。中心前提 FALSE を §1 に訂正記録し、**v1 の 2 面構成（契約層 / package 層）を削除**（前提が落ちたため不要）。U-5 を discharge から**記録**へ降格、`substrate_id` の許可付与を**検出のみ**へ訂正、collection の正規化と時刻の preimage 除外を追加、引用 host・code 計数・AGENTS.md 引用・reuse gate 探索面を訂正、脱落していた carry #29/#31 を復活。IN-1/3/4 は**明示的に本版の外**。
