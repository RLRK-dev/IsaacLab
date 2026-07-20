# WMSO D1.1-B DESIGN — 5体 CC Debate cycle-1 verdict（CC1 = w2:pQ RS-TECH-LEAD2）

- node: `T-WMSO`; 記録 = **2026-07-20 11:05 JST（実測 11:05:57）**; gate 位置 = prereg v1.1.1 §5 chain の「5体 CC Debate / pre-mortem」段。
- 対象 = **design draft v1**（`31d96783c3f5392c…` @ `71e3985aab`）。panel = lens A/B/C/D + NHA（N=5 packing、lens SSOT `percent18_lensed_v1.md` §6）。集約 = **UNION of valid catches**（select-best しない）。
- **VERDICT = ⛔FAIL（cycle-1）** — CRITICAL/HIGH 多数を ACCEPT。fix → v2 → 検証者軸（pS → pN）へ。正常な fail-closed 経路（D1.1-A cycle-1 と同型）。

## 0. 機械的検証（層3・CC1 実施、panel へ同一 bundle 提供）

- M1/M2: frozen 3 file = freeze record §2 pin と byte 一致（DESIGN `00192d20ca00b654…` / EP md `c474acea7c58acc2…` / EP json `e63176af9bc3a246…`）。design blob `31d96783c3f5392c…` @ `71e3985aab` 再現。
- M3: golden 独立再導出 PASS（当時 G-1 `f7684084…` / G-2 `4cd18a02…`）。**panel 3 体が独立実装で再現一致 — 数値自体に誤りなし**（CC4 は byte-level UTF-16-BE serializer を自作して delta 0 を確認）。
- M4: EP v1.9 抽出（**この抽出が C-1 の欠陥源** — §1 参照）。

## 1. 収束した CRITICAL — 全て CC1 が独立実測で確認 → ACCEPT

| # | 指摘 | 提起 | CC1 の独立検証 | 処置 |
|---|---|---|---|---|
| **D-1** | §3 の「RECONSTRUCTED_COMPATIBLE / DIMENSION_ONLY 行 = なし」が **FALSE**。EP は wildcard/`_applicable` の集合形で TENSOR_BINDING を被覆 | CC3 / CC4 / CC5 / CC6（**4/5**） | 実測: `RECONSTRUCTED_COMPATIBLE` = `{"_all_13_components": [...]}` / `DIMENSION_ONLY._applicable.components` に **TENSOR_BINDING を明示列挙** / profiles = CLOSED_LOOP rank3・**SHADOW rank2**・OFFLINE_REPLAY rank2、TB は 3 profile とも required | **ACCEPT** |
| **D-2** | `relation=IDENTICAL` が **自己 hash 不動点** — `demo_dataset_binding_hash` は spec 内部 field ゆえ `== H_WCJ(自身)` を要求＝構成不能。G-2 は自らの `E_BINDING_STAGE_MISMATCH` に違反 | CC3 / CC5（2/5・両者独立に実証） | 実測: G-2 `demo=0ab17d93…` vs 自 hash `4cd18a02…` → 不一致。§0 で M2 循環教訓を引きながら **同型の循環を別 field で再導入**（field 名 2 個を守り構造 pattern を見落とし） | **ACCEPT** |
| **D-3** | 多次元 shape の **flatten 順序が未規定** — `length == prod(shape)` は要素数のみ固定。§0 の「全単射」主張が偽 | CC4（1/5） | 実測: `row-major\|column-major\|行優先…` grep = **B 設計 0 hits・frozen A も 0 hits**（継承元も無い）。G-2/G-3 の `[2,3]` が該当 | **ACCEPT** |
| **D-4** | golden の **機械可読 fixture が未 bank** — prereg IN-6「機械可読 fixture を design 同梱」+ Exit「design doc（機械可読 fixture + golden 同梱）完成 → 5体 CC Debate」に違反。§6 の再現 command は存在しない path を引数に取る | CC2 / CC3 / CC4（3/5） | 実測: `git ls-files \| grep tensor_binding_golden` = **0**。prereg:34 / :43 逐語確認。fixture は session scratchpad のみ ⇒ pS/pN は独立再計算不能 | **ACCEPT** |

**D-1 の自己評価（loud）**: 原因は `pp[grade].get('TENSOR_BINDING')` という **name-scoped query** で「無い」を導出したこと。これは自分の banked lesson [[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]] / [[feedback-absence-claims-need-closed-query-and-moving-tree-provenance-2026-07-18]] が禁じている形そのもの（不在主張は閉じた query で裏付けよ）。lesson を持ちながら同じ形で踏んだ ⇒ v2 では EP 由来主張を **全 grade 列挙 + group/wildcard 展開**で再導出する。

## 2. HIGH — ACCEPT（全て on-disk 確認済み）

- **D-5 hash-identity 検査が不在**（CC2）: §4 が「全 E_ 列挙」と称しながら `H_WCJ(spec) == bundle.tensor_binding.artifact_hash` の検査も供給経路も無い。frozen `certify_definition` は spec を受け取る引数を持たない ⇒ 宣言 hex 64 桁だけで closed-loop eligible になり得る。**ACCEPT**（v2 §4 に `E_BINDING_ARTIFACT_UNRESOLVED` / `E_BINDING_HASH_MISMATCH` + 供給経路 = `proof_artifact_resolver` 明示。7 引数化が要るなら frozen delta として Rs review — 黙って追加しない）。
- **D-6 history stack layout 未規定**（CC3/CC4/CC5 = 3/5）: `HistoryOrder` は時間方向のみ。step-major / feature-major が同一 hash。**ACCEPT**（`HistorySpec.layout` 追加）。
- **D-7 `E_BINDING_NORM_COHERENCE` の双条件**（CC2/CC3/CC4/CC5 = 4/5）: ⇐ 方向が未論証で frozen §1.2†（evidence-gated EXPLICIT_NONE）と deadlock。THREAD の実 default（`empirical_normalization: False`）で誤発火。**ACCEPT**（一方向 implication 化 + 全 operand KNOWN 時のみ発火）。
- **D-8 action feature の source 制約が comment のみ**（CC2）: obs field を action にbind可能。**ACCEPT**（`E_BINDING_SOURCE_FORBIDDEN`）。
- **D-9 `FeatureSource.HANDOFF` に producer 特定が無い**（CC2/CC3）: `accepted_handoff` は tuple ＝ 複数 producer。frozen が `producer_handoff_schema_hash` で解いた曖昧性を再導入。**ACCEPT** — v1 語彙から **HANDOFF を削除**（最小手・NHA の縮小方針と整合）。
- **D-10 bool-as-int**（CC4）: `isinstance(True,int)` ゆえ `offset/length/total_dim/depth` に bool が通り、同一 layout が 2 hash。**ACCEPT**（`type(x) is int`）。
- **D-11 再現 command が WCJ 非忠実**（CC4）: `json.load→dumps` は duplicate key/NaN/Infinity/float を通す（§6 invalid corpus が拒否必須とするもの）。**ACCEPT**（fixture builder を bank し、拒否 hook 付きに）。
- **D-12 demo 198 件が bind 不能 → `portfolio_has_IL` 到達不能**（CC5）: `demo_dataset_binding_hash: str`（非 Optional）+ absent-reason 無し。**ACCEPT**（v2 では IDENTICAL=null 化に伴い構造変更 + 移行 blocker を §8 に loud 宣言）。
- **D-13 `binding_schema_version` 無検証 + churn**（CC5）: version 検査コード無し、bump が全 SkillActionId を churn し certificate/transition row を stranding。**ACCEPT**。

## 3. MEDIUM/LOW — ACCEPT（v2 で処置）

D-14 ≥2 要素 frozenset golden 欠落（frozen §2 item 8 の要件・4/5）/ D-15 mask の shape 整合・`dtype=BOOL` 制約なし / D-16 混在 dtype と container dtype 未規定 / D-17 `normalization mean/std` isfinite 義務が frozen §5 U13 で **B に名指し委譲**されているのに落ちた / D-18 `E_BINDING_OVERLAP` が §4 算法下で到達不能 / D-19 空 feature tuple が通る / D-20 `belief_inputs` の重複規則なし / D-21 §5 「必須化」に error code・機械可読述語なし・§5D 互換破壊 / D-22 §5 に不確実性 channel が無く、banked lesson（grasp verdict を数値で PASS 宣言するな）+ RV5 §6(iii) calibrated uncertainty と衝突 / D-23 AGENTS.md reuse gate 未実施（4/5） / D-24 prereg §7 の `/reward-design` 該当性 **再判定**が §5 で trigger したのに未実施 / D-25 §3 が frozen `manifest_content_rule` を超える義務を追加 / D-26 §3 CONFIG_HASH「導出可能」が反証不能 / D-27 §8-2「両失敗を塞ぐ」over-claim / D-28 §1.1 の enum 改訂手続が Rs review を欠く / D-29 mis-citation 2 件（frozen §7c は**不在** — 正 §8 / RV5-W-P0-5 → RV7-P0-3）/ D-30 88mm を SSOT 引用せず prose 内在化 / D-31 fixture が single-arm・6dim（実 demo は 12dim）。

## 4. REBUT / PARTIAL

- **NHA = HOLD（縮小方針）**: 「defer D1.1-B」自体は NHA も FAIL 判定（RV5 §6.5 + DC-1）。**PARTIAL ACCEPT** — 縮小提案のうち §3 の誤主張撤回・§8-2 の降格・§5 の PROVISIONAL 化（`required_field_ids` 強制の取り下げ）・reuse gate 追記は**採用**。G-2 を捨てて G-1 のみ残す案は**部分 REBUT**: G-2 級被覆（belief/mask/history）は D-3/D-6 の判別に必要ゆえ、捨てずに**修正版で再生成**し、さらに G-3（complement）を追加する。
- **CC4「alternatives 3 は upstream で決着」**（NHA も同旨）: **REBUT ではなく訂正** — frozen `tensor_binding: ArtifactSlot` により artifact 形は上流確定。v2 では KNOWN_ALTERNATIVES #3 を NOT_EVALUATED → **FORECLOSED（frozen §1.2 により）** に訂正する。
- **CC6 の reuse 調査結果は採用**: `source/isaaclab/.../observation_manager.py:271-272` の `except Exception: print(...)` は **fail-open**（descriptor 取得失敗 term が silent 脱落）⇒ certification 基盤に不適 = 独自 spec の**最強の正当化**。加えて `thread_isaac_lab/models/obs_builder.py:30` が `task_config` に存在しない 4 symbol を import（dead code）・`OBS_DIM` が 6 箇所 4 値に分裂。v2 に reuse 記録として fold し、**producer↔binding 対応の owner 不在**を carry として明記。

## 5. NO_ACTION_EVALUATION（必須）

- 何もしない場合: DC-1 により closed-loop eligibility は永続的に取得不能。RV5 §6(5)（Rs review 逐語「契約完全主義で slice を無期延期しない」）に反する。
- KNOWN_ALTERNATIVES に既存 PASS: **なし**（#1/#2 = FAIL 確定、#3/#4 = frozen/prereg により foreclosed、#5 = 実在するが fail-open ゆえ不適）。
- NHA judgment: **HOLD（= 縮小せよ。着手自体は CHANGE_JUSTIFIED）**。
- No Action を退ける理由: 上記 3 点。ただし **NHA の縮小要求は verdict に反映**（§3 縮小・§5 PROVISIONAL 化・§8-2 降格）。

## 6. DECIDE

**⛔FAIL（cycle-1）**。CRITICAL 4 + HIGH 9 を ACCEPT。**fix → design v2 → pS final-design PASS → pN DESIGN PASS-CLOSE（exact-pin）→ Rs freeze 判定**（prereg v1.1.1 §5 chain）。

- cycle-2 debate の要否 = **pS/pN の裁量 + Rs 裁量**（skill の max-2-cycles 規律。CC1 は自己起動しない）。fold の検証は §5 chain の pS/pN 両軸が担う。
- **impl / training / authority = CLOSED 継続**（本 debate は設計書面の検証のみ）。
- panel の raw 出力は本 record §1-§4 に per-item で fold 済（union 集約・invented issue は不採用 0 件 — 全 31 項が on-disk 実測で追認可能）。
