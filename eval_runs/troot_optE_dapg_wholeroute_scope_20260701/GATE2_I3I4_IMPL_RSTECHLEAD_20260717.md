# gate② I3/I4 実装 chunk — impl plan + pre-registered legs (RS-TECH-LEAD %12)

Date: 2026-07-17 04:4x JST (start). Task = Rs「A着手」(04:3x) = gate② 完了 chunk の I3/I4 実装。
Design SSOT = `REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING_VTDESIGN_20260715.md` **§S3.1 (I3) / §S3.2 (I4) / §S3.3 (premise) / §S3.4 (chain)**, banked `d807d077b8`.
Input evidence = `GATE2_RERUN_FM34_RSTECHLEAD_20260717.md` leg3 OUTCOME (findings 3/4) + `gate2_rerun_fm34_probe_v2_result.json`.
L = **L3** (reward/termination semantics; L-TRIAGE self=auto=L3)。chain per §S3.4: 実装(%12) → p5 delta verify (§S3.1/S3.2 のみ) → /pre-check 再走 → §S 解除。

## Scope (touched files, pre-declared)

| # | file | change |
|---|---|---|
| 1 | `thread_isaac_lab/envs/route_env_config.py` | ADD `ROUTE_C2_SIDE_FROM_PIN = -1` (route 設計定数 1 bit、§S3.2) + grounding comment |
| 2 | `thread_isaac_lab/envs/newton_route_env.py` | I3: `_c1_escape_after_seat` → identity 計器 (`_seat_metrics`/`_c1_retention_m` の dx) を読む (signature `(dx_c1, c1_latched)`、call site :1627 は :1600 の同一測定値を渡す) / I4: `_seat_identity_segments` C2 walk を routed 側 index に限定 / docstrings (`_crossing_x_dev` = obs 専用へ、`_seat_metrics` consumers に escape guard 追記) |
| 3 | `thread_isaac_lab/scripts/test_route_reward_identity_guards.py` | 既存 FM3 test を新 signature へ + NEW: I3 fixture (a) fail-open stray-straddle → escape True / I3 fixture (b) 偽 escape → escape False / I4 feed-drape → not seated |
| 4 | NEW `eval_runs/.../gate2_rerun_i3i4_probe.py` (+ result json) | canonical per-frame divergence-0 legs (banked v2 anchor 値と厳密一致) + **positive control: canonical C2 crossing 側 == 定数** (pre-fix 両側 walk の probe-local replica で非循環測定、drift = loud) + 新 guard escape per-frame 0 |
| 5 | `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` §21.4/§21.11.1 | pointer note のみ (§S3.3 premise: pin = 既成着座の保持装置、seat f2428 ≺ onset f2544)。p5 事前授権「%12 bank 時に pointer 追加で可」(§S3.3) |

⛔ NOT in scope: pin (a)(b) 実装 / (d) containment (p5 設計) / obs[57] 意味論 (§S3.1 scope 限定で不変) / `route_executor.py` / `task_config.py` / probe v1/v2 (lineage 凍結のまま — v2 script は signature 変更後 re-run 不可になるが、banked result json が evidence であり script は lineage; 本 doc で明示)。

## Ruling verbatim bars (conformance targets)

- I3 (§S3.1): `escape := (dx == _SEAT_MISS_DX_M) ∨ (dx > DROP_LATERAL_DEV_MAX_M)`、dx = `_c1_retention_m`/`_seat_metrics(C1)` の identity-restricted 出力。`_crossing_x_dev` は obs[57] 専用に残す。fix 後 grep assert = reward/termination 系の `_crossing_x_dev` 消費者ゼロ。
- I4 (§S3.2): C2 walk を pin node から見た route 設計定数側 (cable index ±) に限定。leading-span leg は採らない (単調 span は側内で C2Y を高々 1 回)。fail-closed 不変 (routed 側に crossing 無し → MISS)。
- 検証 leg (§S3.1/S3.2): fixture 2+1 本 REJECT unit test 化 + canonical per-frame divergence 0 維持 + positive control assert。

## Grounding measurements (done PRE-implementation, read-only, 04:4x)

- **ROUTE_C2_SIDE_FROM_PIN = -1 の接地**: canonical golden (`w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz`、pin_seat_seg=27) の全 313 C2-seated frame で、seat 述語が選ぶ crossing segment = **{16: 313}** — 全て pin より下位 index (below_pin)。feed 側 (seg≥27) の C2Y straddle は stride-25 全走査で **0 frame**。⇒ 定数 = −1、かつ canonical では side 制限が除去する crossing ゼロ = divergence 0 の事前根拠。
- 測定計器の忠実性: replica が banked v2 の 313 seated frames を正確に再現。

## Pre-registered verification legs (run at [RUN], all must PASS to bank)

| leg | 内容 | expected |
|---|---|---|
| V1 | 新 unit tests (I3a/I3b/I4) + 既存 4 tests、env7 直呼び | ALL PASS |
| V2 | probe: canonical anchors 厳密一致 (c1 first 2428 / pre-onset 116 / post-onset 5163/5163 / c2 first 7394 / 313/313 / c2 max dx 3.183mm) + positive control side==−1 + 新 guard escape 0 | ALL PASS |
| V3 | grep: `_crossing_x_dev` 消費者 = def + obs :1550 のみ (reward/done path ゼロ) | 対称差 = ∅ |
| V4 | ruff + py_compile (変更 4 py file のみ、tree-wide -f は禁止 [known trap]) | clean |
| V5 | 既存 FM4 ×2 + recording-fields test 不変 PASS | PASS |
| V6 | **fails-without-fix**: 変更前 code で新 fixture 3 本の OLD 挙動を実測記録 (I3a: escape=False [fail-open] / I3b: escape=True [偽] / I4: seated=True [誤 credit]) → 変更後に反転 | 反転確認 |

## §S exposure

本 chunk は §S carry 下 (swept FM3/FM4 = HEAD live 未批准) の**その批准 chain 自体**。本 doc の全 run artifact は canonical npz (banked golden) の read-only 再計算 + 合成 fixture のみ — 新規 sim run なし、motion 妥当性の新主張なし (視覚レグ省略 justified、§13.3 の Rs 動画 standing に従う)。

## [VERIFY] (L3 事前) — panel record

- 試行: 3-lens adversarial panel (CC2 exploit/correctness / CC3 THREAD-geometry / CC6 NHA)。5 体からの縮小 = 07-16 infra 劣化実績 (seat fix で CC1 self-review fallback 実績) + 本 design は既に two-key (p5 §S3 + leg3 verifier) 済で、panel の対象は【実装計画】。panel 出力は本 § に追記。
- 下流独立検証 = p5 delta verify + /pre-check 再走 (chain 構造、§S3.4)。

### OUTCOME (2026-07-17 04:5x 追記)

**3 体とも BLOCK なし**: CC2 = PASS-WITH-REFINEMENTS / CC3 = PASS-WITH-REFINEMENTS / CC6 NHA = 5 null 中 3 REFUTED・2 PARTIALLY-SUSTAINED (documentation/refinement のみ)。design-breaker ゼロ。

**⭐CC3 の追加実測 (panel の主要 yield): 81-grid 全数スキャン** — per-cell pin seat_k は **{27:19, 28:17, 26:15, 32:9, 33:9, 34:9, 29:2, 25:1}** と変動 (canonical の 27 は 19/81 のみ) だが、**side=−1 は 81/81 で成立** (feed 側 [seg≥seat_k] の C2Y straddle = 全 frame 全 cell で 0、frame-0 node order は Y-ascending 81/81)。⇒ canonical 単独接地の gap は panel が閉じた (有利方向)。

**Folded refinements (実装へ反映、番号 = 発見者-番号):**
1. [CC2-2] V2 escape leg の frame 窓を**今**事前固定: **post-onset (f ≥ 2544)** で escape 0 (v2 の窓と同一)。pre-onset は latched=True 評価だと dx=MISS → True が設計どおり出る (fail-closed) ため全 frame 窓は無効な leg。
2. [CC2-3] V3 grep scope を事前固定: **`newton_route_env.py` 内** (ruling bar = reward/termination 系消費者ゼロ)。test/probe (lineage) の hit は期待集合に列挙。`_crossing_x_dev` docstring の「post-G3 guard が消費」文の書換えを diff に含む。
3. [CC2-4] **I4 は obs[49]/[58]/[59] にも継承される** (post-G4 の active clip = C2 ⇒ `_seat_metrics(active_xy)` 経由)。ruling の instrument-attribute 原則 + c2_honest auto-follow 前例 (§11) の範囲内・canonical divergence 0 (証明的: 縮小候補集合は seated 判定を非 seated 化できず、313 winner [seg16] は全て制限を生存)。**p5 delta verify に明示 surface** (undeclared obs delta にしない)。
4. [CC2-5] 静的関係 assert を test 化: `_SEAT_MISS_DX_M > DROP_LATERAL_DEV_MAX_M` (将来の定数編集で net が破れたら loud)。
5. [CC2-10 + CC6-N5] `_c1_escape_after_seat` docstring: (a)「渡す dx は同 step の `_seat_metrics(cable_pos, _C1_XY)` 出力」契約 (b) **z 域外逸脱は本 guard の対象外** (G6 `c1_retained` の z-band leg が封じる; escape は lateral + crossing-loss のみ) — ruling §S3.1 の機構節の scope を明文化。
6. [CC3-R1] V2 に **81-cell leg** を昇格: 全 81 cell で (a) feed 側 straddle 0 (b) c2-seated frame の選択 crossing seg < その cell の seat_k (c) seat trace の pre/post 一致。
7. [CC3-R2 + CC6-N3 + CC2-7] 定数の grounding comment に構造 anchor 2 本を cite (cable build direction=(0,1,0) で node 0 = 低 Y 端 [`newton_skill_env_base.py:1587-1590`] + C2Y 0.000 < C1Y 0.150 ⇒ side = sign(C2Y−C1Y) の帰結) + **将来 route (C3-C5 / 他端 routing) は自 route の定数を再接地 + positive control 再走が必須** + N-clip 一般化は per-hop side map (本定数は single-hop scope)。
8. [CC3-R3] **below-pin tail-return REJECT fixture** を unit test 化 (16/81 cell で実在する下位 index 側の戻り crossing [例 cell_x0_y-5 straddle {7,20}] は side でなく **monotone walk が棄却**している — walk の load-bearing 性を将来の編集から守る)。
9. [CC6-N4] V3 を one-off grep から**committed standing assertion** に昇格: reward/done path 関数 source に `_crossing_x_dev` 参照ゼロを test 内で assert。
10. [CC2-1] 項 5 (RLENV_PIN_DESIGN pointer note) に **identity-persistence coupling** を明記: (a)(b) lifecycle 実装は「物理 eq のみ lifecycle 管理し、identity (seat seg index) は episode 内で永続」でなければならない — G3 latch 後に identity を null 化すると escape guard が偽 −10 を打つ (CC2 finding 1 の将来 coupling)。
11. [CC2-9] I3(b) fixture 制約: stray は identity window {pin−1, pin} 外の segment に置く (lexsort 検証済: in-band 優先は OLD global picker で stray を選ぶ)。

**Declined / deferred (理由付き):**
- [CC3-R2 後半] ingest 時 runtime sanity assert (frame-0 node-0 Y < pin Y) = ruling §S3.2 が選んだ contract (設計定数 + probe 制御) の外・ingest path への scope creep ⇒ 実装せず **p5 delta verify で optional hardening として提示**。
- probe v1/v2 の signature 追従 = しない (lineage 凍結、banked result json が evidence。plan 本文どおり)。

## [RESULT] — 全 leg 実測 (2026-07-17 05:0x-05:1x JST)

| leg | 結果 | 証拠 |
|---|---|---|
| **V6 fails-without-fix (変更前)** | ✅ 3/3 再現: I3(a) OLD escape=**False** (fail-open、identity=MISS 9.0) / I3(b) OLD escape=**True** (偽、identity dx=0.0・z=0.900 帯外) / I4 OLD seated=**True** (feed-drape 誤 credit、両側候補 0..38 実測) | scratchpad `v6_oldbehavior_capture.py` 出力 (04:5x、本 doc bank 時の会話 log) |
| **V1+V5 unit tests (変更後)** | ✅ **exact-landed 9/10 — §S3.1/S3.2 bar 該当 leg = 9/9 PASS**〔⚠scope 訂正 05:5x、pN B1〕: FAIL 1 本 = `test_pin_identity_fields_survive_recording_prepare` (V5 系 pre-existing invariant、**bar 外**) — 未 commit `route_executor.py` pin-fields 差分に依存 = **landed tree で invariant FALSE** (owner chain finding)。**disposition (b) 採択**: V5 recording-fields leg は本 chunk acceptance から除外、当該差分の land + exact-landed 10/10 再走 = **(a)(b) chunk precondition** へ登録。〔HISTORICAL: 当初報告 = main working tree で 10/10・exit 0 — 測定値は真だが code-state scope 誤帰属。教訓 = test-run claim の code-state surface は test の **import+call 閉包**が定義する (実装 diff の scope ではない)〕 | pN 隔離 worktree exact-landed readback (dfbdd 単体 9 leg PASS / 親 commit V6 旧挙動再現) + p5 §S3.5a 自己再現 (9/10、同 FAIL message) |
| **V2 probe** | ✅ **ALL_PASS exit 0**: leg A = canonical anchor **厳密一致・対称差 = {}** (2428/116/5163⁄5163/7394/313⁄313/3.183mm) / leg B = 新 guard escape post-onset (f≥2544 事前固定窓) = **0** / leg C = **81/81 cell feed 側 straddle 総数 0** (per-cell seat_k 25..34、histogram = panel 実測一致) ⇒ side 制限は全記録 cell で除去ゼロ = **per-frame 計器等価の証明** / leg D = obs[49]/[58]/[59] 継承を宣言 | `gate2_rerun_i3i4_probe_result.json` |
| **V3 grep** | ✅ `_crossing_x_dev` @ newton_route_env.py = **def :1426 + obs :1566 のみ** (旧 guard 消費 :1433 は消滅、対称差 = ∅)。standing 化 = `test_crossing_x_dev_is_obs_only` (inspect.getsource で reward/done 関数 source に参照ゼロを常時 assert) | grep 出力 + committed test |
| **V4 lint** | ✅ ruff "All checks passed!" + py_compile OK (変更 4 py file; tree-wide `-f` は known trap ゆえ不使用 [pN format 事故前例、targeted lint = seat-fix 前例踏襲]) | 同ターン出力 |

**残留 catch (self)**: obs[57] 隣接コメント (:1567-1568) が旧 guard 挙動 (「reward-side guard が None を保持」) を記述したまま → 同 chunk 内で修正済 (docs-must-not-lie、CC2 finding 3 の残り火)。

**§S 露出宣言**: 本 chunk の全実行 = banked npz の read-only 再計算 + 合成 fixture。新規 sim rollout ゼロ・HEAD 実 run ゼロ ⇒ §S exposure なし。視覚レグ省略 = justified (幾何述語の数値検証のみ、motion 新主張なし)。

**chain 位置 (§S3.4)**: 実装 = 本 doc で完 → **次 = p5 delta verify (§S3.1/S3.2 条項のみ)** → /pre-check 再走 → §S 解除判定。pin (a)(b)/(d) = 別 chunk (pN と分割 co-decide)。〔⚠この段落は下記「pN HOLD 対応」で supersede — FENCE 順序が正〕

## pN HOLD (B1-B3) 対応 + chain 再配列 (2026-07-17 05:5x 追記)

**pN 二層判定 (05:3x)**: I3/I4 **mechanism semantics = PASS** (隔離 worktree exact-landed readback: dfbdd 単体 9 leg PASS / 親 = V6 旧挙動再現 / 81-grid recompute banked 値一致 / §S3.1-S3.2 整合) ／ **evidence/bank acceptance = HOLD (B1-B3)**。p5 = §S3.5a 訂正 (10 件目) banked `2dbc21d178` (pN pre-bank readback CONTENT PASS)。

| # | 内容 | 対応 |
|---|---|---|
| B1 | exact-landed 10/10 不成立 (recording-fields test = 未 commit route_executor.py 依存) | **disposition (b)**: V5 leg を本 chunk acceptance から除外・claim 9/9 (bar) へ訂正 (上表)。**route_executor.py pin-fields 差分 (実測: 全 5 hunk が `_prepare_recording` 内、19+/1−) の land = (a)(b) chunk precondition** — 着手時に著者 claim + producer-unbanked〔Rs 待ち〕系との関係特定 + scope prereg を先行 (pN 推奨手順に concur) |
| B2 | 新規 artifact が pre-commit-clean でない (V6: SPDX 欠落+lint / probe: format / json: EOF newline) | **修正済** (本 commit): V6 = SPDX 2026 + docstring 統合 + import 整列 + 行長 / probe = 下記 B3 と同時に整形 / json = probe が trailing newline を emit (再生成で反映) |
| B3 | result json に git/source SHA・81-grid input hash・pre/post bracket なし + 入力 untracked | **probe に leg E (evidence closure) を実装**: git HEAD + closure file の git status + **sys.modules 由来 source closure sha256** (hand-list でない、E0 v4 教訓) + **81-cell 入力 manifest sha256** (162 file + aggregate digest — 入力は録画 data ゆえ tracked 化せず hash で pin) + pre/post source bracket (changed=[] fail-loud)。--grid/--out 引数化 (worktree exact-landed 実行用) → **本 commit 後、隔離 worktree @ 本 commit で fresh 再生成** |

**co-decide 決着 (pN 非 CONCUR を受諾)**: pin (a)(b) は本セッション続行**せず** — I3/I4 correction CLOSE 後の **fresh session/chunk**。開始手順 = banked lifecycle design (§21.11.1 + identity-persistence coupling) readback → file/hunk scope prereg → prior-art → 実装。precondition = route_executor pin-fields land (B1)。

**現 chain (LEDGER `bf5feef0bd` = 正)**: correction bank (本 commit) → **exact-landed closure probe 再生成** → **pN readback (evidence HOLD 解除判定)** → FENCE 解除 → **/pre-check 再走** → §S 解除判定。tri-state: design = CONFORM banked (§S3.5+§S3.5a) / evidence = pN HOLD 中 / adversarial = FENCE 待ち。⚠05:2x に spawn した /pre-check verifier は API 529 で 2 回死亡 — FENCE 発効により**再 spawn せず** (解除後に再走)。

**V6 恒久 artifact**: `gate2_i3i4_v6_precheck_oldbehavior.py` + `_output.txt` (⚠ script は本 commit の **parent でのみ実行可** — 新 signature で loud に壊れる。それ自体が V6 の主旨)。

## staged-hunk 検査の開示 (add 前 hard step、B2 再発防止の実施記録)

- `route_env_config.py` の working tree に**自分の編集でない comment-only hunk 2 つ**を検出 (:21 obs layout 表の [60:62] 記述 / :65-73 OBS_C1_* コメント群 — いずれも banked 済み Files A の interp 意味論へ stale コメントを直す内容、code 変更なし、著者 unclaimed = ambient residue)。**選択 stage (git apply --cached、自 hunk のみ) で除外し working tree に保全** — staged 側 = `@@ +148,13` の 1 hunk のみを diff で確認済。巻込みゼロ。
- `newton_route_env.py` 11 hunk / test file 3 hunk / RLENV_PIN_DESIGN 2 hunk = 全て自分の編集領域と一致 (hunk header 照合済)。AGENTS.md 等の他 dirty file は不触。
