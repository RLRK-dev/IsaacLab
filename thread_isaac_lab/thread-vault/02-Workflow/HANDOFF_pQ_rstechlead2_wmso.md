# HANDOFF — pane pQ (w2:pQ RS-TECH-LEAD2), node T-WMSO — 2026-07-21 01:36 JST

> Pane-specific handoff (multi-pane NEST; does not clobber the shared HANDOFF.md).
> Full detail = memory `handoff_cc_pQ_rstechlead2_wmso_d11a_freeze_2026-07-20.md`. Ground truth = frozen package + freeze record + manifest + LEDGER row44, not this narrative (§運用4).

## 要約（5 点）

1. **D1.1-A `contracts_v2` = ✅FROZEN / CUSTODY-CLOSED**（Rs 裁定「freeze + push」執行済み・remote tip `65d62d15ed` == local HEAD・parity 0/0）。
2. **FROZEN pins**: DESIGN v2.11.2 `00192d20ca00b654…` / EP v1.9 `c474acea7c58…` / JSON v1.9 `e63176af9bc3…`（def hash `e7ca43093084…`）@ bank `54f90a7de1`。freeze record = `WMSO_D11A_FREEZE_RECORD_20260720.md`（`593880be6ef9…` @ `9a13035626` — 採択文: RV7 fidelity supersede / register ⑩ 両含意 / **D1.1-A 限定・gate-1/実装許可へ非拡張**）。
3. **検証系譜**（本 session）: Rs RV7 HOLD → v2.10/EP v1.8 → pS §16 PASS → pN B1-B4 → v2.11/EP v1.9（**B4 = method registry 化・DEMO_PLUS_RL — register ⑩ Rs CONFIRMED**）→ pS §17/§18 → pN R1-R4 → v2.11.1 → pN M1-M4（M2 = manifest authoritative 化・循環断ち）→ v2.11.2 → **pN EXACT-PIN PASS-CLOSE** → OPS-SUP consultation GO → freeze+push。全 8 transcript = AUTHOR-CONFIRMED bank 済み。
4. **境界**: impl / training / authority = **CLOSED** 継続（freeze = 設計書面の確定のみ）。kinematic 全廃 HALT（p4 arc）も impl 側に継続。
5. **D1.1-B/C/slice scope 段 = ✅3 軸 CLOSE（2026-07-20 09:48）**: Rs 着手指示（08:42 頃）→ prereg v1（`7fc04d1baa`）→ pN SCOPE HOLD B1-B4 → v1.1 fold（`1da8503d2c`）→ pS B1-B4 readback PASS → v1.1.1 N-1 fix（`cf94601f7a`: prereg `ffd06623e22f…` / pS record `27e007afe244…`）→ **pN SCOPE CONCUR / PASS-CLOSE**（transcript `0a5d0969218c…` @ `ccd8342c30`）。**解錠 = D1.1-B DESIGN AUTHORING のみ**（[CHANGE]/code/run/training/authority = CLOSED 継続）。binding carries = pS C-1（METHOD_REGISTRY enum-vs-row 境界）/ C-2（drive-substrate stale taxonomy 焼込み禁止）+ prereg §6。**D1.1-B: draft v1（`31d96783c3f5…` @ `71e3985aab`）→ 5体 CC Debate cycle-1 = ⛔FAIL（CRITICAL 4 + HIGH 9 ACCEPT・全て CC1 が on-disk 実測で追認）→ DESIGN v2 = bank 済**（blob `7248de8600a454…` @ `9d5d44e329`。verdict record + fixture 3 本 @ `d0767f31f8`）。CRITICAL = ①v1 §3 の EP 不在主張が FALSE（name-scoped query 由来・SHADOW rank2 は RECONSTRUCTED_COMPATIBLE を受理）②`IDENTICAL` が sha256 不動点（M2 循環の構造的再発）③flatten 順序が両 doc とも未規定＝「全単射」主張が偽 ④fixture 未 bank（prereg IN-6/Exit 違反）。NHA 縮小要求（§5 PROVISIONAL 化・§8-2 over-claim 撤回・reuse gate 実施）も採用。**pS final-design PASS（v2）→ ⛔pN exact-pin HOLD B1-B5（11:39）→ v3 fold → pN 指示の B1-B5 限定 cycle-2（5体）→ DESIGN v4 → pS 再 PASS（12:24）**。現 pin @ `012b9bf2d4`: **v4 = `9087a2a6e01f…`**（bank `f00c02e378`）/ pS record `0aca40ff7950…` / fixtures `af90712a…`・`991651b9…`・`dd14f6b6…`・`59bbfbba…`（G-4 追加・builder は全 14 型 conformance + negative control 16/16 発火 + **`--verify` 非破壊 mode**）。
- **pN B2 の教訓（重要）**: v2 で必須化した `container_dtype` が golden 3 本とも欠落・builder 未検査。**pS は builder 再走で hash 一致を確認したが、hash 再現性 ≠ schema 適合**。pS は §10/§12 で 5/5 CONCUR + 恒久教訓「存在 ≠ 十分」を自己記録。
- **cycle-2 の安全関連 catch**: BOOL feature に normalizer/transform を付すと `v ≠ 0` 読み出し下で mask が無効化される → `E_BINDING_NUMERIC_STAGE_ON_BOOL`。また `E_BINDING_CAST_LOSSY` は到達不能（D-18 類型の再発）ゆえ削除。
- ⭐**Rs 優先順位裁定（2026-07-20 13:04:29 JST 受領・記録のみ・authority 主張なし）**: **WMSO = 最上位概念 / top L0 integration architecture**。従属作業は WMSO への寄与で順序づける。**RL/IL/Vision/WorldModel = 必須かつ conjoined**、**per-skill 実装は algorithm-agnostic**（BC+RL / 妥当なら RL-only 等）。task (d) / substrate cleanup / demo 再生成 / safety = **WMSO-enabling な前提・carry**（競合する top-level goal ではない）。⚠**physics-realism / safety / evidence / two-key / Rs run・launch gate を一切迂回しない**。⇒ 本 node の gate chain・CLOSED 境界は**不変**。反映依頼 = p6（LEDGER row44 + planning surface + state.md、13:10 dispatch 済）。私の側は design doc header に記録済。⚠p6 が Rs へ 1 点 escalate 中: task (d) node の **parent 帰属**（pN 案 = T-ROOT 直下の横断 node ／ 本裁定 = WMSO の前提・carry）。p6 は「順序付けの軸と tree 上の親の軸は別」ゆえ両立可能と判断しつつ、[DEFINE] 起草前に Rs 確認待ち。
- ⭐**v6（2026-07-20 13:06 実測、`0459a636e672…` / builder `c74ca3b36193…` @ bank `81f33ceefd`）= 著者自検出 1 件の fold**（pS の v5 PASS `4e633489a9c2…` 12:51 の**後**・pS/pN いずれの指摘でもない）。**S-1（MED）**: negative control 24 本が**生成 mode でしか走らず `--verify` では 0 本**だった ⇒ §6 が ⑤24 本と ⑥非破壊 mode を並記していたため「検証者が使う非破壊経路が guard 発火まで実証する」と読める状態 = **pN R3 と同型**（evidence 主張 > それを届ける経路）。**v5 は「何を検査するか」を絞ったが「どの経路で走るか」を検証せず、穴が一段ずれて残った**（R1 の到達性 blind spot と同型の反復 — 自己記録）。修正 = 両経路で実行（in-memory deepcopy のみ変異ゆえ非破壊性不変）。実測: `--verify .` → 4/4 conformance PASS + **24/24 fired** + rc=0 ／ 事後 fixture sha256 **4 本不変**（再 pin 不要）／ 改竄 positive control（G-1 `policy_rate_hz` ← `"Infinity"`）→ **rc=1**。pS の optional 指摘（invalid corpus の `等` 表記）= 実測で **cosmetic 確認ゆえ変更せず**（一般則 + §1.4b 表セル ⛔ + negative control #45 が実際に拒否。churn 回避）。**次 = pS delta 再 verify（13:10 dispatch 済）→ pN exact-pin 再判定（同）→ ⛔Rs の B1 裁定 → freeze**。
- ⭐**v6.1（2026-07-20 13:17 実測、`0444d71f310a…` @ bank `2c096150fc`。builder = `c74ca3b36193…` で v6 から不変 = code 無変更・fixture 4 sha 不変）= pN exact-pin HOLD H1-H3 の fold（3/3 ACCEPT）**。pN custody = PASS（3 sha + fixture 4 sha 全一致、隔離 archive で 4/4 PASS + 24/24 fired + 前後 sha 不変を実測）。
  - ⛔**H2（実質・fail-open）**: §6 の `rc=1` 主張に **interpreter/entrypoint の指定が無かった**。実測（破損 fixture）: `python3` / `/usr/bin/python3` / `env_isaaclab7` / `env_isaaclab` = **全て rc=1** だが **`./isaaclab.sh -p` のみ traceback を出しつつ rc=0** ⇒ repo 標準の呼び方をした検証者は**破損を clean と読む**。⇒ **fail-closed コマンドを §6 に事前登録**（素の `python3` 直呼び・≥3.8・stdlib のみ依存ゆえ可搬）+ wrapper 経由を明示禁止。⚠**AGENTS.md「Exit-code exception」が既に文書化している hazard**（guard wrapper が `env_isaaclab/bin/python` を直呼びする理由そのもの）で、**規約を常時ロードしていながら自分の計器に適用しなかった** — S-1 と同じ「到達性/経路の軸を見ない」盲点が**インタプリタ境界**で出た形。
  - **H3（records 矛盾）**: §12 の v5 行「`--verify` で negative control 全発火」と §6「v5 まで verify 経路 0 本」が同時成立不能 ⇒ **構造的に決着**（v5 blob `96f92af7c8` の `main()` は verify 分岐を `return` で抜けた**後**に control ループを置く ⇒ verify 経路の発火 = **0** 確定）。v5 行を records-fix。**peer の custody 報告を自分の code 構造と突き合わせず版歴へ転記していた**。
  - **H1（順序 bypass）**: v6 を pS/pN へ**同時 dispatch** し pS→pN の逐次を破った（pN 検証は成立するが pS readback 未 bank ゆえ PASS-CLOSE 不成立）。⇒ :6 に順序規律を明記、**以後 final pin への pS addendum を bank してから pN へ回す**。13:21 に pS のみへ v6.1 dispatch、pN へは順序訂正のみ通知し待機依頼。
  - 設計 semantics 不変・pN「追加 debate 不要」。
- ⭐⭐**D1.1-B DESIGN = ✅two-key 充足（2026-07-20 14:35）— 残 gate は Rs の B1 裁定のみ**:
  - **pS 設計軸 PASS**（`251e8c8516f2…` @ bank `ed60396e88` §17/§18、13:29）— H2/H3 を**独立再現**（破損 fixture: `python3` rc=1 ／ `./isaaclab.sh -p` rc=0 同一 traceback ／ v5 blob の `return` が control ループ前）し、両者を**自身の v6 verify gap として own**。恒久教訓を記録:「**rc/exit 主張は downstream verifier が使う exact interpreter/entrypoint で検証し、repo 標準 wrapper が exit を mask しないか確認せよ**（AGENTS.md Exit-code exception を自分の計器にも適用）」。到達性盲点 = R1→R3→S-1→H2 の **4 度目**。
  - **pN exact-pin PASS-CLOSE**（14:35:06）— 隔離 archive で素 `python3 --verify` = rc0 / 4/4 conformance / **24/24 fired** / fixture sha 前後不変、`Infinity` 注入は direct rc1・同入力の `./isaaclab.sh -p` は traceback+rc0 を再現。H1/H2/H3 全 CLOSE、R1-R3・S-1 closure 維持、v5→v6.1 の設計 semantic 節 変更なしを diff 直読で一致確認。⚠**transcript は未 landing**（message のみ）— pN へ bank 依頼済（14:36）。
  - **私の独立検算**: v5→v6.1 の全変更行をセクション写像 = header 5 / §6 9 / §10 **1（版参照のみ・B1 の A/A′/B content は byte 同一）** / §12 10 ⇒ **設計 semantic 節（§1-5, 7-9, 11）の変更 = 0 行**。**設計は v5 で収束**、S-1/H1-H3 は全て計器・記録・手順の硬化。
  - ⛔**freeze 不可**: 唯一の gate = **Rs の B1 裁定**（hash 供給 locator。**A** = hash 由来 canonical ref〔CAS 要求・`E_BINDING_HASH_MISMATCH` が store 整合性検査に縮退〕／**A′** = frozen `EvidenceRecord.source_ref` 束縛〔全 grade 存在・最小・**pQ 推奨**〕／**B** = frozen schema delta〔supersession + Rs review〕。**`tensor_binding` + `normalization` 両 slot に同型**）。pN「追加 debate 不要」。**impl/training/authority = CLOSED 継続**。
- ⚠⚠**上記 :26 の A/A′/B 枠組みは SUPERSEDED（14:39 以降の arc で解体済）— 引用しないこと**。以下が現行。
- ⭐⭐**B1 = ✅CLOSED 確定（2026-07-20 21:44 Rs ratify・veto 不行使）— 3 軸すべて CLOSE**（機構 = pS §27(A)/§28 ／ pin = pN exact-pin ／ authority = Rs）:
  - **現行 pin**: DESIGN **v12 `62d4e44f959b2702eaf8ac266c82b1262d3c571bc329eb81b1d9e7d1c0f9787c` @ `f8b34bbd98`**（v11 `4aa797f477…` @ `95deebe66b` = Rs ratify fold ／ v10 `4851e1ec7e1d…` @ `d67773b63f` = PROVISIONAL 期） ／ 委譲 custody `e119b94e2ed2ff07bd931a05f59f4693d41c4f8a1c68b4182280271d2b33da8a` ／ pS §28 `96c08eb4458db968c4f0403948bd2c6bba8ad8c6d410bd651e9574201a5ee397` @ `5c01273c50` ／ pN transcript `2456eb8bbd71aa71376625b008ebb52aaadf1c1a23f11f01ea4c1bdf2110d407` @ `d30fc2e4ad`。builder `c74ca3b36193…` + fixture 4 sha = **v6 以降不変**。
  - **解**: **D-1 = `EvidenceRecord.source_ref` を locator に束縛**（frozen delta 不要・1 hop・B 側宣言 1 個・意味論適合）。⚠**Rs 裁定ではなく CC1 の設計判断**ゆえ **Rs 拒否権が残る**。落選 = D-2（2 hop・宣言 2 個。到達可能性は否定せず）／D-3（frozen を開ける必要なし。**必要時は Rs 専権**）／D-4（**失格** — 凍結が要求しない CAS を課す + `E_BINDING_HASH_MISMATCH` 失効）／rank 2 への proof 追加（**FORECLOSED**）。
  - ⛔**唯一の open = Rs confirm**: 「20:41 の『はい』= B1 の解法選択（D-3 除く）を CC1 裁量に委ねる意味か」。**私の narrative で on-disk 未検証**。custody record を bank したが **bank は可視化であって検証ではない**（pN transcript も独立に同旨を明記）。**否なら B1 は OPEN へ戻す**。
  - **arc（14:39→21:15）**: Rs 裁定 A′ → ⛔**Rs が破棄**（逐語「誤りが前提であるならそれは当然破棄にしろ」— 私が提示した前置き「両 slot に同型」が偽・**しかも v6.1 §10:327 の逐語で two-key を通過済だった**）→ B1 OPEN 復帰 → 前提 claim-set（C1-C4b）two-key → **Rs 裁定 C3 = slice の EP profile = SHADOW（rank 2・非 authority）**〔1 回目 17:57 も同結論だが **私の未検証の言い換えを前提にしたため Rs が破棄・逐語「前提が違ったので選び直す」**〕→ 導出 claim-set（D-A..D-D・選択肢 0/推奨 0）two-key → **D-1 採択（v9）** → **pS §27(B) LOUD FLAG**（authority が narrative）→ **v10 fold** → pS §28 + pN PASS-WITH-PROVISIONAL。
  - ⛔**grounding から除外**: v7.1 `9b0c229a0695` = VOID ／ A′ 裁定 record `WMSO_RS_B1_RULING_APRIME_20260720.md` = VOID（引用不可・「破棄の経緯記録」用途のみ）。
- ⭐**本 arc の恒久教訓（3 件・いずれも「未検証の主張が決定面に載る」の変奏）**: ①**誤前提の上の裁定は結論が同じでも無効**、かつ **前提を出した側にその誤りが immaterial だと決める standing は無い**（A′ / C3#1 の 2 例）②**two-key は open point 内の事実主張を measure していなかった** — banked かつ両 key 通過は、その事実主張が検証済である意味ではない ③**human 発話に依拠する権威を設計面に書くなら、同一ターンでその発話を custody record にする**（structured-select か自由発話かで扱いを変えない）。⚠③は**自検出できず pS が検出**。
- **次 = ⛔D1.1-B freeze の Rs 判断待ち（別 gate・Rs 専権・self-start 禁止）**。v12 = freeze 直前の records-fix（§10 の版自参照が v6.1 のまま v7〜v11 を通過していた — freeze は誤記ごと固定するため）。**freeze 時に残る declared open 4 件**を §12 に明記済: ①`stats_key` 一意性（⚠**length 不一致は fail-closed だが、同一 length 共有は検出 code 不在ゆえ一意必須読みで silent-pass** — v13 で訂正。旧「どちらの読みでも fail-closed」は過剰主張）②§7 到達性負例（impl leg）③§5 閾値系（slice prereg + Rs）④U-2/U-5/U-6。⚠**D1.1-A も §10 に open を残して freeze した先例**あり。freeze 後 = D1.1-C（artifact manifest）→ boundary-only vertical slice。**impl / training / closed-loop authority = CLOSED 継続**。
- **DDR carry**: #27 B1-locator = ✅**CLOSED 確定**（p6 `1ba11fdf31`）／ #28 U-2 ／ #29 U-5 ／ #30 U-6 ／ ⭐**#32（新）= D0 slow-path rollout H<5 と実測 routing 周期長 7 の緊張**（p6 `472b693109`→`738eed3c67`。出所 = p4 実測 `dcc280855476` @ `0e1589c931`・⚠**probe/pd1-arm-pd branch のみ在中ゆえ commit 併記必須**）。⚠honest scope: step 数の比較であって実時間の主張でない ／ receding-horizon replan（D0 `:210`）がある以上「張れない = 破綻」ではない — **真の未測点は horizon 打ち切り時の終端 value 推定の有無** ／ owner = pQ + pS が未判断。
- ✅**解決（Rs 裁定 2026-07-20 23:4x・逐語「SKILLについてはpX:SKILL-DESIGNが決めることとなった。整合性を持つように」）**: **SKILL の細分化・分解能は `w2:pX SKILL-DESIGN` が決める** — ⛔**本 node の割当ではない**。（経緯: Rs 逐語は p4 経由の伝聞で届いたため割当として接地せず Rs へ照会 → 本裁定で「否」に決着）。custody = `WMSO_RS_SKILL_OWNERSHIP_RULING_20260720.md`。
  - **本 node に残る scope** = `SkillLifecycleContract` schema ／ `tensor_binding` 契約 ／ EP evidence 束縛 ／ **SDM 単位** = 「どの skill が在るかによらず、その上に載る契約層」。
  - ⚠**DDR#32 は両側にまたがる**（周期長 = 分割の関数 = pX ／ `H` = SDM 設計 = 本 node）⇒ owner をどちらか単独にしない。

## ⭐ pX:SKILL-DESIGN との連携（2026-07-20 23:5x → 07-21 00:2x・Rs 指示「連携して」「不整合がないように」）

- **pane 再導出（必須・stored map 信用禁止）**: `w2:pX SKILL-DESIGN`（SKILL 決定権）／⭐**`w2:pN` T-ROOT-OPS-SUPERVISOR-CODEX = 停止**（Rs 2026-07-21 00:2x）→ **`w2:pY` = T-ROOT-OPS-SUPERVISOR**（label 無し・peek で導出・Rs が直接指名し pN から引き継ぎ中）。
- ⛔**未処理 = OPS-SUP consultation leg 1 件のみ**（D1.1-B freeze 前）。pN が停止前に「**exact-pin は consultation を兼ねない・別 leg 必要**」と判定（transcript `3432de3c3462…` @ `7ce2a520c9`）。D1.1-A 先例は **Rs 指示**で実施（形式参考 = `db24b877d234…` @ `6af253dc14`）。⇒ **pY へ引き継ぎ済・自己起動しない**。

### ⛔ FOUNDATIONAL INVARIANT 系の発見（Rs 判断待ち・私は編集していない）

- ⛔**`RL-Routing-Design.md:1032`「構造: 排他的単腕 (RIGHT→CLIP0,1 / LEFT→CLIP2,3,4)」** = §0 不変前提 **DUAL-ARM** に触れる。**live section**（`:1028 ## 1. 概要` 直下）・**supersession marker 無し**（同 doc は marker を 15 箇所で使用）・同 doc `:20`/`:1635`/`:2486` は両腕と記述 = **内部矛盾**。⚠**違反と断定していない**（label の誤りである読みを `:1635`/`:2486` が支持）。**07-Design は CC read-only・p5 管理・不変前提は Rs 専権**ゆえ未編集。p5 + pX + Rs へ通知済。
- ⛔**層 1（工程表）の欠落**: `thread_isaac_lab/skills/step_table.py:60 StepDef` に `target_left`/`target_right`/`l_finger`/`r_finger` は在るが、**`None` が「保持」と「不関与」を潰す**。保持の意味論は行コメント `None = keep current` のみで、**4 field 中 1 つ（`l_finger`）だけ**（pX 指摘）。⇒ **腕の「参加」を機械判定できない**。
- ✅**層 3（契約層）は欠落なし** — ⚠**私の当初主張「契約層は駆動と保持を区別できない」は撤回**（pS §33 で検証済）。実測: `:61 IdentityKind = LEARNED|SCRIPTED|WAIT` / `:62 ControlMode = DIFF_IK_EE_TARGET|SCRIPTED_SEQUENCE|WAIT` / `:83` 表で **kind → control_mode が決まる** / `:151 ControlResourceSpec` = **所有宣言で behavior と直交**。⇒ hold = `kind=WAIT ∧ control_mode=WAIT ∧ 資源 claim` で表現可。**誤りの型 = 1 型だけ見て「無い」と結論し、同じ凍結 file の enum を述語で引かなかった**。

### schema delta（Rs review へ上げる・私が上程）

- **1 件に束ねる**（pX 受諾）: **合成グラフ容器 + barrier を不可分**（barrier は容器の edge/node 属性ゆえ**容器なしに独立 landing 不可**。分けると「列は表現できるが合流は表現できない容器」が先に landing し、並行合成が合流意味論なしに宣言可能 = silent gap）。
- ⚠**存在理由の訂正**: **DUAL-ARM 検証は delta を必要としない**（案 (B) なら claim の全称検査で足りる）。**delta の理由 = Rs の並行合成 MVP 裁定**（並行合成そのものの表現）。受入条件としての DUAL-ARM 検証可能性は維持。
- **凍結側は触らない**: `ControlResourceSpec` も `ControlMode` も改造不要。
- **不在確認（私が実施・pX 依頼）**: 合成容器の候補語（Composition / composition_graph / SkillGraph / PlanDefinition / CompositionEdge / multi-skill / DAG / successor / predecessor / next_skill / sequence）= **凍結 3 file 全域で 0 hit**。`:139 accepted_handoff: tuple[AcceptedHandoffSpec, ...]` = **pairwise 表現**。
- **Q1(c) 確認**: `SKILL_ID_REGISTRY` 更新 = **Rs 承認事項**（`:436`）+ invariant test `SKILL_ID_REGISTRY == EXPECTED_SKILL_IDS`（`:556`）= **二重制約**。pX の「最大の衝突点」判断は正しい。

### ⛔ pX へ返した未決（層 1 を確定する前に選択が要る）

- **(A) 単腕レーン + 合成/barrier**（保持 = `kind=WAIT` の別単位。delta 必須） vs **(B) 両腕 skill + 静止目標**（保持 = 同一 skill 内の静止 target。DUAL-ARM 検査は claim の全称検査で足り delta 不要）。
- ⚠**pX の「凍結が単腕レーンを強制する」は too strong**（反例 = (B)）。**選択は pX 所管**（skill 分解の形）。**層 1 の記録形式は選択に依存**するので選ぶ前に確定しない、と依頼済。
- **層 1 → 契約層の写像（(A) の場合・pX 受諾済）**: 駆動 = claim あり + `control_mode` 非 WAIT ／ 保持 = claim あり + `control_mode` WAIT ／ 不関与 = claim なし。

### ⚠ delta 仕様 — **Rs bank 判定 = ADOPTED DESIGN DECISION / ⛔NOT YET: normative delta closure**（2026-07-21 01:34）

⛔**閉じた normative delta として表現しないこと**（Rs 明示）。**OPEN 継続 = runtime containment ／ predicate projection closure**。
⚠**本節の旧版（01:34 bank `ed627314f2`）は「delta 仕様 = 確定」と書いており over-claim だった** — Rs 裁定受領の 1 分前に bank したもの。訂正済。

**Rs 承認済（pX 経由）**: 単位 = **片腕レーン** ／ **並行合成を最初のマイルストーン**に。

**Rs 提示の確定形**: `SkillCompositionDefinition` + 逐次 + 並行 + **必須 barrier/join** + **region-level postcondition** + ⭐**required_belief_fields based scope projection** + ⭐**raw `Ownership.resource` exclusion** + `OutcomeEffectSpec` + `CompositionCertificate`。

⚠**旧構成（`BranchEffectScope` + evaluator registry + 適合試験）は SUPERSEDED** — 下記「Rs による置換」参照。

- ⭐⭐**Rs による置換（strictly better）**: raw ownership を**境界づけるのをやめ**、**述語に見せる入力を静的 projection に限定**する。`predicate_input = project(joint_snapshot, RegionPostconditionSpec.required_belief_fields)`。
  - **不変条件 6 点**: (1) evaluator へ **raw joint snapshot を渡さない** (2) **raw `Ownership.resource` を渡さない** (3) `required_belief_fields` の全 field を **typed schema で解決** (4) 各 field が **指定 evaluation cut で取得可能** (5) **projection schema + field 集合を `CompositionDefinitionHash` へ含める** (6) **未宣言 field access は fail-closed**。
  - ⭐**(a)/(b) の再帰が消える**: 「evaluator が宣言 scope を守ることを**信頼する**」必要が無い — **見せていないから**。runtime state の広さと postcondition が主張し得る scope の広さが**構造的に切り離される**。
  - ⇒ **適合試験（識別不能性）は主機構から回帰検査へ降格**。不要ではない（side channel に有効）が **(b) を背負わせない**。cable 差分 fixture も同じ位置づけ。
  - ⚠**pX の自己申告**: containment（runtime ⊆ definition）要求は、`required_control_resources` を**上限**として再解釈するもので、**凍結 `:380` の `required ⊆ offered`（下限制約）の意味そのものを変える**ところだった。
- **certificate 検査**: `required_belief_fields` ⊆ joint snapshot の typed field closure ／ ⊆ 子の observation・handoff・effect から供給可能な集合 ／ evaluator input schema == projected joint belief schema ／ **raw `Ownership.resource` dependency == none**。
- **error code**: `E_REGION_FIELD_UNDECLARED` / `E_REGION_FIELD_UNAVAILABLE` / `E_REGION_SCOPE_ESCAPE` / `E_REGION_PREDICATE_SCHEMA_MISMATCH` / `E_REGION_RAW_OWNERSHIP_FORBIDDEN`。
- **cable は ownership 経由でなく typed belief field として宣言**: `cable_span_seated` / `cable_clip_contact_state` / `cable_span_tension` / `left_grasp_stability` / `right_grasp_stability`。導出値なら evaluator は宣言 primitive field のみを入力とし、**evaluator artifact hash を certificate へ結合**。

- ⭐**核心不変式**: **merged branch effects does NOT entail region success**。`region_success = branch_readiness ∧ region_postcondition(joint_snapshot) ∧ planned_events_completed ∧ join_completion`。
  - **根拠 = 型論証**（動画ではない）: `OutcomeEffectSpec` は branch-local ／ 凍結 `ControlResourceSpec` の 4 key に **cable は存在しない**（`:142` definition 級 claim は `ControlResourceSpec` のみ・`:424` で untyped dict を pin 語彙へ**意図的に置換済**）／ region success は joint snapshot 上の述語 ⇒ **どの branch も cable を claim できず、branch postcondition は cable を参照できない** ⇒ merge しても含意しない。∎
  - ⚠**動画は「この gap が空でないことの存在証人」に降格**（本 project では動画由来の物理妥当性判定は Rs 専権・独立 judge 経路が要るため、根拠を frame 番号に置くと delta の受入がその経路に従属する）。
  - ⭐**より強い形**: 「**cable が絡む成功条件を持つタスクは region postcondition を構造上必然的に要する**」= 存在主張でなく**証明**。上程はこれを使う。
- ⭐⭐**最大価値 = 安全帰結**: region postcondition を **support lane 解放前**に joint snapshot 上で評価し **PASS 時のみ** release event を発行 ⇒ **「成功確認前に支持 hold を解除する」経路が型で禁止**（既定値の議論でなく構造）。FAIL/UNKNOWN なら release せず hold 維持。
- **級の分離（必須・同名で級だけ違う形にしない）**: **branch 級** = 自 claim の 4 key 語彙のみ ／ **region 級** = 宣言された joint belief field（**cable 含む**）。⚠一律適用すると **region postcondition が機能を失い delta が自壊**する。
- **reuse（新機構を作らない）**: scope 規則 = 凍結 `InitiationSpec.required_belief_fields`（`:151`）pattern の合成層への適用 ／ evaluator registry = `SKILL_ID_REGISTRY`（`:436`）/ `METHOD_REGISTRY`（`:109`）と同 pattern。⭐`:109` 逐語「**schema 変更なしで algorithm を拡張可能**」⇒ **evaluator 追加は freeze 後も凍結を開け直さず Rs 承認だけで済む** = 上程の強い論点。
- **再帰の停止条件**（「その規則は何が強制するのか」への答え）: **artifact identity + 人間承認**に着地。⚠ただし **method_id 追加 = label の追加**に対し **evaluator 追加 = 信頼基盤に実行コードを入れる行為**で類推は非対称 ⇒ **適合試験**を必須化して人間審査でなく機構で閉じる。
- **適合試験の形**: 宣言 scope S 上で一致し **S の外だけが異なる 2 joint snapshot** に**同一 verdict** を要求（scope 外を読んでいれば verdict が割れて落ちる）。⚠**健全な反証器であって証明ではない** — 「banked pair 集合上で scope 違反を**反証する**」と書き「**保証する**」とは書かない。⚠⚠**fixture 選択が強度を決める**: 差分 pair に「**4 key 語彙上で一致し cable 状態だけが異なる**」ものを**必ず含める**（一般の S 外 pair では実際の懸念を識別しない = 「違う結果が出得ない試験は試験でない」の直接適用）。
- **凍結側は触らない**: `ControlResourceSpec` / `ControlMode` とも改造不要。
- ⚠**外部依存 1 件**: Rs 裁定（43-step の step 9,12,20,28,36 で右腕が保持も指令もされない件）が **ParallelRegion に単一 branch を許すか**を決める ⇒ **裁定前に branch 数の下限を型に焼き込まない**。
- **containment（測定済・結論）**: 凍結の包含規則は `:380` の **`required ⊆ offered`（充足性）1 件のみ**で、**`runtime ⊆ declaration`（包含性）は強制されていない**。⇒ ただし scope を **definition 級に束縛**すれば runtime は宣言 scope の外ゆえ containment 検査は不要。

### 本 arc の恒久教訓（今夜追加分）

- ⛔**「D0 draft を現行として引く」= pane 横断で本日 4 度（p4 が 3・私が 1）**。私は **pX へ送った「凍結済だから束縛せよ」の目録が 6/6 誤り**だった（凍結は `:416`-`:425` の migration 表で全部を改名/discard 済）。**原因 = D0 は自分が書いたので記憶から引用し、同じ message で pin した凍結 file を読まなかった**。⇒ **WMSO 契約 field は必ず `contracts_v2`（凍結）を読んでから引く**。
- ⭐**pS の監視 duty = 3 軸に拡張**（受諾済）: ①subdivision 決定への over-reach ②over-claim ③⭐**frozen-vocabulary の under-statement**（過小申告は「凍結が既に持つ機能の delta 提案」= 不要な Rs review と「偽 absence 主張」を生む — 今夜どちらも起こりかけた）。**方法 = 凍結を述語で引く（何が X を表現するかを全空間に問う・1 型で「無い」としない）**。
- **今夜の訂正 5 件はすべて、主張した側でない方が測って見つけた**（私の目録 → pX ／ pX の「分解で検証可能」→ 私 ／ 私の「区別できない」→ pX の筋 ／ pX の「レーン強制」→ 私 ／ 私の「delta は DUAL-ARM のため」→ 自己）。

## 参照（正）
- 成否 SSOT: `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` row44（p6 反映 `65d62d15ed`）
- pin authoritative 面: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_DELIVERABLES_MANIFEST_20260719.md`（最終 `9708c1d1b361…`）
- Rs 納品 bundle: `~/Downloads/WMSO_*`（全 sha = manifest と一致同期済み）
