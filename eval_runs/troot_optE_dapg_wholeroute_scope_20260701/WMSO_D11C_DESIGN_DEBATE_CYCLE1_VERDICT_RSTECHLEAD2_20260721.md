# WMSO D1.1-C DESIGN v1 — 5 体 CC Debate cycle-1 判定記録

- CC1 = `w2:pQ` RS-TECH-LEAD2／実施 = **2026-07-21 14:3x JST**（shell 実測）
- **対象** = `WMSO_D11C_ARTIFACT_MANIFEST_DESIGN_RSTECHLEAD2_20260721.md` v1 sha256 `726f684c52421928…` @ `33e67626da`
- 体制 = 4 challenger（lens: 前提/出所・規則/SSOT・hash 代数/identity・回帰/履歴〔blind〕）+ 1 NHA。全 body **read-only**（write 権限を構造的に与えない = 共有 tree 保護）
- 層3 機械的検証 = docs-only ゆえ sha 再計算 + 凍結 4 file 不変 + commit 1 file で代替（`./isaaclab.sh -f` 非該当）

## ⭐ DECIDE = **FAIL（cycle-1）** — CRITICAL 複数 ACCEPT。v2 fold 必須

⛔**two-key へ出さない**。⛔**freeze 判断へ進まない**。

## 0. ⛔⛔ 最重要 — 凍結文書へ波及する前提の誤り（§運用10 STOP 事項）

**v1 §3 open-1 の中心前提「required set は exact ゆえ HB 以下は `TRAIN_RUN_MANIFEST` を追加携行できない」= 凍結 EP markdown に反証された。**

- **CC1 自身が on-disk で確認**（challenger の主張を転記していない）:
  - 凍結 EP md `:114` 逐語「…**component に意味を持たない kind の混入** = `E_PROOF_KIND_FOREIGN`」
  - 同 `:129(iii)` 逐語「**他 component 向け kind の混入（例: POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH）→ E_PROOF_KIND_FOREIGN**」
  - ⇒ **FOREIGN は component 意味論であり grade 集合の閉包ではない**。`TRAIN_RUN_MANIFEST` は EXACT 13/13 cell で required（CC1 実測）＝ どの component にとっても「意味を持たない kind」ではない。
- **私の誤りの機序**: 凍結 EP の **JSON `_domain` の 1 文字列だけ**を読み、**同じ §0 で自分が土台として pin した EP markdown を開かなかった**。⇒ 「読んだ面が、知りたい区別をつけていなかった」型。
- ⛔⛔**波及（本 chunk の外）**: **凍結 D1.1-B v13 `:471` が同じ読みを load-bearing に使っている** — 逐語「**rank 2 への proof 追加 = FORECLOSED（`_domain` = exact set + `E_PROOF_KIND_FOREIGN`）**」（CC1 実測）。当該 arc は **B1 locator = D-1 採択**へ接続し、**Rs が 2026-07-20 21:44 に ratify** している。
  - ⚠**私は「結論は変わらない」と決める standing を持たない**（本 node の恒久教訓①「誤前提の上の裁定は結論が同じでも無効、かつ前提を出した側にその誤りが immaterial だと決める standing は無い」＝ A′ 破棄と同型）。
  - ⚠**同時に「D-1 が覆る」とも主張しない**: grade は測定値であり（凍結 `E_GRADE_MISMATCH`）、追加 proof の許容と grade 昇格の可否は**別の問い**。**どちらとも決めない**。
  - ⇒ **Rs へ報告。pS（設計軸）/ pY（evidence 軸）へ確認依頼。⛔凍結 file は編集しない・D1.1-B を自己判断で再 open しない。**

## 1. NO_ACTION_EVALUATION

- **何も変えない場合**: 凍結 v13 `:169`/`:378` が C へ委任した `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` の解消経路が存在しないままになる（ただし fail-closed ゆえ誤 certify は起きない）。
- **KNOWN_ALTERNATIVES で既に PASS のもの**: なし。ただし **(d) 既存 manifest の再利用 = 私の調査が不足**（下記 A-13）。
- **CC6 NHA = HOLD**（棄却ではなく「縮小せよ」）。**部分 ACCEPT**: NHA は **U-5 と `substrate_id` の必要性は証明済**と認めており、§3 供給写像・§6 package 層・§7 golden は**前提決着まで時期尚早**と判定。⇒ v2 は **縮小 + 前提の上程**へ。
- **No Action を採らない理由**: 凍結が名指しで C へ委任した項目（U-5・`substrate_id`）は C 以外に owner が無い。

## 2. ACCEPT した指摘（CC1 が自分で実測して確認したもの）

| # | 指摘 | 提起 body 数 | CC1 の実測 |
|---|---|---|---|
| A-1 | open-1 の前提が誤り（§0） | 4/5 | ✅ EP md `:114`/`:129` を自分で開いて確認 |
| A-2 | `FINAL_ARTIFACT_HASH` を単一 slot に平坦化 = 5 component 中 **3 が誤り** | 2/5 | ✅ 凍結 EP を parse: 要求 cell = POLICY_ARTIFACT / MODEL_ARCHITECTURE / NORMALIZATION / TRAINING_DATASET / TRAINING_PROVENANCE、claim_target は各々別 |
| A-3 | `substrate_ids` を要求する S-3 に**容器型が無い**（M-4 も構築不能） | 4/5 | ✅ §1 型 block に不在 |
| A-4 | `claims`/`producers`/`evaluator` に**順序規約が無い** ⇒ `manifest_hash` が内容の関数でない（TTCB が壊れる） | 3/5 | ✅ 継承規約は tuple→宣言順・bytes 昇順は frozenset のみ |
| A-5 | `recorded_at_utc` を hash preimage に入れた ⇒ 再生成不能・TTCB stranding | 3/5 | ✅ 凍結 EP JSON `:5` は metadata を hash 外に置く先例 |
| A-6 | U-5 の「**解消する**」= 過大主張（certify_inputs に manifest 無し・wiring 未定義）。**detect-vs-prevent の 3 度目** | 2/5 | ✅ 凍結 `certify_inputs` に manifest 不在 |
| A-7 | U-5 の等値検査は **RL 段 hash の複写で常に通る**（D-2/D-12 の捏造経路を manifest 層で再開） | 1/5 | ✅ v1 に解決不能性の負例なし |
| A-8 | `EVALUATOR_ARTIFACT` は manifest 供給でない（class A = **5**） | 3/5 | ✅ EXACT 13 cell 中 **0** が要求（parse 実測） |
| A-9 | 引用 host 誤り `凍結 EP :236-240` → 実体は **contracts_v2 `:236-240`** | 4/5 | ✅ EP md=165 行 / JSON=215 行・contracts_v2:236 = `class ProofKind(Enum)` |
| A-10 | 計数誤り: §5「7 件」→ 実際 **8**／§9「凍結 code 4 種」→ 実際 3 + decoder／§9「3 file」→ 凍結は **4** | 3/5 | ✅ grep 実測 = 8 種 |
| A-11 | **prereg §4 carry ③#29（demo 再記録）/ ⑤#31（trainer 実在）が脱落** | 1/5 | ✅ design 内 hit = **0**（`#29` `#31` `trainer` `demo 再記録` すべて 0） |
| A-12 | IN-4 の **CI 半分が未着手**（見出しのみ・trigger/stage/interpreter 契約なし） | 1/5 | ✅ §6 に実体なし（⚠ challenger の「1 occurrence」計数は不正確・実体不在の指摘は成立） |
| A-13 | **reuse gate の探索面が狭い** — repo を探していない。`thread_isaac_lab/wmso/d1/identity.py:80-82` に既存 `canonical_json()`（`sort_keys` / `ensure_ascii=False`）が在り **凍結 WCJ と別物** | 2/5 | ✅ 実物を確認。⚠ 同 node 内に**互換でない正規化が 2 つ**生じる危険 |
| A-14 | `E_MANIFEST_PRODUCER_PIN_MISSING` に**定義域が無い**（凍結側に producer role 集合が無い） | 2/5 | ✅ 凍結に role 語彙なし |
| A-15 | OUT#4 の誤引用（topology 専用行を一般 delta 行として使用） | 1/5 | ✅ prereg §3 row 4 は topology 限定 |
| A-16 | `evidence_policy_definition_hash` の定数一致 ⇒ EP 版上げで正当な過去 manifest を全落とし | 2/5 | ✅ allowlist 方式へ |
| A-17 | manifest と definition の **coherence 未検査**（kind/lineage/definition_hash） | 3/5 | ✅ 凍結 `E_BINDING_LINEAGE_MISMATCH` の再利用で閉じる |
| A-18 | `rl_stage_tensor_binding_hash` が非 Optional ⇒ NOT_APPLICABLE 系と M-1 が構築不能 | 1/5 | ✅ 型矛盾 |
| A-19 | **AGENTS.md の引用が原文と違う**（認可されているのは `env_isaaclab/bin/python` 直呼び。`:45` はむしろ `./isaaclab.sh -p` を prefer）＋ rc 実測は v13 のものを C が自分の実測のように書いた | 1/5 | ✅ 原文確認。`prohibited.md`「原文を確認してから引用」に抵触 |
| A-20 | §4.2 row-1 の code 極性が逆（MISSING ↔ PRESENT） | 2/5 | ✅ 凍結先例 `E_BINDING_IDENTICAL_HASH_PRESENT` |
| A-21 | §1 の「**塞ぐ**」= 阻止の過大主張（package 層は検出のみ）／`E_MANIFEST_NONCANONICAL_BYTES` に**実行箇所が無い**（到達不能 code の再発） | 1/5 | ✅ §6 check 列に不在 |
| A-22 | S-3 が「宣言すれば混成可」= **許可の付与**＝ policy 先取り（#26 中立でない） | 1/5 | ✅ 凍結 carry は「clean のみ」+「黙って混ぜない」の 2 連言。片方を許可に緩めていた |
| A-23 | SCRIPTED/WAIT × EXACT = `E_GRADE_INAPPLICABLE` ⇒ open-1 の下では SCRIPTED 系の行と golden M-1 が到達不能 | 2/5 | ✅ open-1 が偽と判れば解消（A-1 に従属） |
| A-24 | **debate の順序が 1 段早い** — 上位 prereg の design Exit = 「機械可読 fixture 同梱 → 5 体 debate」 | 2/5 | ✅ ACCEPT。fixture bank 後に **cycle-2 を必ず回す** |

## 3. REBUT（challenge を退けた／設計として生き残った点）

- **反循環（TTCB を manifest 外に置く）= 健全**。CC4 が独立に検算し「`manifest → claims → {claim_target_hash}` のいずれも manifest hash でない・TTCB hash は preimage に不在 ⇒ **不動点なし**」と明記。**3 度目の不動点は無い**（代わりに出たのは A-4 の正規化非関数性 = 同族の別 member）。
- **`claims` が凍結 `manifest_content_rule` を満たす形である**こと自体は成立（ただし A-4 の順序規約が要る）。
- **ProofKind の 15/15 分類は kind 軸では総和・排他**（CC4 が enumerate して確認）。誤りは **class の割当**（A-2 / A-8）であって全域性ではない。
- **EXACT 13/13 が `TRAIN_RUN_MANIFEST` を要求**する事実は正しい（CC1 実測）。誤りは「だから他 grade は携行できない」という含意（A-1）。
- **#26 の値空間・pX 合成・p5 F4 への越境は無し**（NHA + CC3 が独立に 0 hit を確認）。

## 4. 次の行動（順序を変えない）

1. ⛔**Rs 報告 + pS/pY への確認依頼**（§0 の凍結波及）。**これが先**。
2. v2 fold（A-1〜A-24）＋ NHA の縮小勧告の反映。
3. **fixture bank**（golden + builder・stdlib のみ・fail-closed コマンドは原文どおり `env_isaaclab/bin/python` 直呼びで登録）。
4. **cycle-2 debate**（fixture 同梱版に対して）。
5. two-key（pS 設計軸 / pY evidence 軸）→ ⛔Rs freeze 判断。

⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**（本 debate は何も解錠しない）。
