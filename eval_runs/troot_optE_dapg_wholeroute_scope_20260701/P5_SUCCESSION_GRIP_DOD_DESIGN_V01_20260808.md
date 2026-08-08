# SUCCESSION #18 — PD 基盤 grip-efficacy 実測の測定系・DoD 設計（v0.2 DRAFT・cycle-1 FAIL-revise 反映）

**Author**: p5 SKILL-DETAIL-DESIGN。**Status**: **DRAFT v0.2 — L3 re-debate cycle-1 = FAIL-revise を反映・cycle-2 前**。
**Commission**: Rs first-hand（p5 session `c2d317bc` 2026-08-08 **01:42:56.775Z = 10:42:56 JST**・p18 検証 `m-p18-78`）。lane = Q5（materials §8 @ `7626027b3a`）。
**位置（gate chain・cycle-1 で明示化）**: 本 draft → **re-debate cycle-2** → **/reward-design 全 protocol 再走（D 値確定後・現況 = OPEN・§7 は適用形であって gate PASS ではない）** → **/pre-check（現況 = OPEN）** → rule-check → impl（Rs sign-off）→ 実測。⛔ **本 doc は実行を authorize しない**（row 18 execution HOLD・fence 継続）。⚠ **Q3 fence**: 実測の位置は **#18-last** — (d) P-D1 → **gate chain 再構成の後**（LEDGER row 18 over-read guard）。⚠ **DDR #38 premise register**: 本 doc の bind 先 driver は UR15 premise 変更（第 2 波「新しい腕（mirrored）」記録 open）の上に居る — **#38 着地時に §3 の rebind 再確認**。
**pins**: driver = `p4_ur15_sim_20260727/ur15_steps_wired.py` @ **`02b85fc52f`**（sha256 head `2ab042b6970654cc`・3,834 行・worktree == HEAD で実読）／canonical 表 = `RL-Routing-Design.md` §2 @ **`59badc4b7a`**（driver header `:2-8` が名指し）。

**版表**
| 版 | 内容 | stamp |
|---|---|---|
| v0.1 | 初版 draft（banked `8a3bde897a`） | 2026-08-08 10:45:40 |
| v0.2 | **cycle-1 FAIL-revise 反映**（панель 5 体・受諾 cluster A-P — 下記 §11） | 2026-08-08 11:1x（date 実測 turn 内） |

**invariant guard**（不変・触れたら STOP+Rs）: DUAL-ARM / DiffIK-only / コ LOCK（working asset 16.00 現行）/ no-kinematic-trick（pin 例外のみ）。span は述語にしない（#58）。

---

## §1 measurand

**grip-efficacy** = PD closed-loop 駆動下で、**grip 義務 cell（後述 mask）を通して把持を保ち、pin 発火前に seat に到達する能力**。**g3（Q4 の ruled endpoint）= 本 doc の L3**。L4-L6 は Q4「C2_REGRASP を含む coverage」の実装で、**L5-L6 は ruled skeleton の拡張**（明示 mark）。
- 報告単位 = **leg 別・side 別の条件付き成功率**。⛔ whole-route 単一 % に潰さない（#49/#56/#59）。
- ⚠ **被覆宣言（cycle-1 cluster F）**: canonical 表の Phase C+D は **C2-C5（STEP11-42）+ E（43）**。本 DoD の被覆 = **C2 instance（STEP1-18 = driver 実装範囲）= 18/43 step・2/5 clip**。**C3-C5 の再把持 ×3・transit・seat・Phase E は非被覆** — L4 からの transfer 主張は **しない**（別測定要）。

## §2 段構造・grip 義務 mask（cycle-1 cluster C — 指状態 schedule に整合）

**STEP 表の指令指状態**（driver `:2702-2721` @ `02b85fc52f`・(L,R)）: 2-3 = OPEN,OPEN ／ **4-7 = CLAMP,CLAMP** ／ 8-11 = HALF,OPEN ／ 12-13 = CLAMP,OPEN ／ **14-16 = CLAMP,CLAMP** ／ 17 = RELEASE,RELEASE ／ 18 = HALF,OPEN。gate 印: grasp@4・pinC1@9・regrasp@14・pinC2@16。
- **grip 義務 cell = 指令が CLAMP の (STEP, side) のみ**。HALF = 誘導（12mm 面 gap・設計上 非把持）・OPEN/RELEASE = 非義務。⇒ **G-grip/G-transit は義務 cell 上でのみ評価**（v0.1 の「leg 区間全体」は HALF/OPEN 区間を偽 FAIL 化する欠陥だった — L2 の保持率上限 0.52 が設計から出る）。
- **handover 瞬間を pin**: STEP7→8（CLAMP→HALF 指令境界）・STEP16→17（CLAMP→RELEASE）。**G-seat の評価瞬間 = pin gate 発火前**（C1 = STEP7 末〜9 の pre-pin 窓・C2 = STEP15 末〜16 の pre-pin 窓）。
- **述語の評価瞬間 clause（cluster E・#56 α leg）**: 閉じ動作に対する判定は **close+settle 完了後**に評価（t42 verdict §3-1「grasp check evaluated before the jaw closes」の再輸入防止・fix row C の owner = p4・着地状態を実測前提に carry）。
- **episode 3 値 taxonomy**: VALID-PASS / VALID-FAIL(grip) / INVALID（除外は全数印字）。**within-leg 帰属規則（cluster D）**: VALID-FAIL(grip) = **義務 cell 中の held() 減衰が、同時 choreography event（arm-arm 接触・tracking-gate 失速・IK fallback 発火）を伴わずに**起きた場合。同時 event あり → INVALID（**両因を印字**）。**曖昧 → VALID-FAIL（conservative 側）**。報告は **両側 bound**: 「曖昧を FAIL に数えた率（conservative）」と「除外した率（上界）」の 2 本。

## §3 述語（cycle-1 cluster A/B — 計器の選択を明示・全 conjunction・superseded 形を排す）

**計器選択（G-grip 系は 2 本在る — 選択理由を書く）**: driver には `grasped()`（`:570-584`）と **`held()`（`:855-874`・R6 conjunction）**が在り、held() の docstring が retention 用途での grasped() を両方向で弾劾している（「claws closed through each other で held と言い、cable surrounded のまま released と言う」）。driver 自身の per-STEP grip 表示は held()（`:3615`）。⇒ **役割分担**:
| 述語 | 定義（**実装の全 conjunction**） | 用途 |
|---|---|---|
| **G-close(t)** | `grasped(t)` = **両側 pad1×cable 接触** ∧ face gap ∈ (2.0,8.0)mm（`:553-556`+`:580-584`） | **閉じ品質 gate**（grasp@4・regrasp@14 の瞬間・close+settle 後） |
| **G-hold(t)** | **`held(t)`** = 背板 gap < `release_floor()`（≈18.19mm・爪先 channel 飽和回避のため背板で読む） ∧ `cable_in_mouth(t)`（pad-local band・spec 導出） | **retention**（義務 cell の時系列 = G-transit） |
| **G-seat(clip)** | **`seated_any(clip)`** = **ANY link で** `seated()` 全 conjunction（xy tol ∧ \|z−GROOVE_Z\|<_tz **∧ groove 床接触** `:971-975`）・**見つかった link を witness 記録** | seat 判定（pre-pin 窓） |
| G-dual | **D-6 再 seed（cluster H）**: 義務 cell での per-side G-hold 非対称の持続 ＋ arm-arm 近接/接触 — **command 流量 proxy は不採用**（park は指令上 正常・#18 の実失敗は接触喪失） | DUAL-ARM 測定形 |
- ⛔ **`:351` の SEAT1/SEAT2 print は build-time guess**（`seated_any` docstring・Rs 2026-07-28 目撃の欠陥そのもの）— **episode の link witness は seated_any の返す link**。v0.1 の「:351 で episode ごとに pin」は撤回。
- **D-1 は削除** → **D-1′**: `cable_in_mouth`/`MOUTH_BAND_Z`（実装・測定済）を**そのまま採用** ＋ **link-identity 追跡**（leg 入口/出口で把持中の最近接 link id を記録・axial slip の観測子）。
- **can-report 検査（cluster E 訂正）**: ⛔ v0.1 の「#56 = 失敗を報告できない」「:1391 = 指が開かない」は**両方 誤読**だった。正 = **#56 は「うまくいったと報告できない」**（LEDGER `:160`）・`:1391` の機構 = **arm tracking gate**（右腕 53° short・TRACK_TOL 5.18mrad で gate 不開・`:2573-2592` 同機構）。検出子（方向別）: **false-FAIL 系** = STANDING ERROR ≥ TRACK_TOL print・stall RuntimeError（`:3777-3792`）・held-back tick 比 → **INVALID**。**false-PASS 系（#56 の実 leg）** = α: 評価瞬間 clause（§2）で構造閉鎖／β: per-step IK fallback（quiet=True 残 site）発火数を per-episode 印字・>0 は INVALID／γ: 掃引截断 = 本測定は掃引でないため非該当と明記。
- **substrate 健全性 entry gate（cluster J・#26 系譜）**: **per-run actuator census = nu==14 相当**（名前一致・材料 doc §10(a) provenance）— 不一致 = INVALID（B1 は state であって機構でないため run ごとに再確認する）。
- **envelope（cluster P）**: 本測定の妥当域 = **wc=1・単一 world・CPU mujoco**（eq/pin の CPU 書込は wc>1 で GPU-inert — 既知 lesson）。wc≠1 の run は witness 条件で INVALID。

## §4 coverage set（legs × **sides** — mask 整合版）

| leg | 内容 | 義務 cell（side） | exit gate |
|---|---|---|---|
| L1 | 初期把持（STEP2-4） | STEP4: **L+R** | grasp gate 後 close+settle 済で **G-close 両側** |
| L2 | C1 搬送+押込（STEP5-7） | STEP5-7: **L+R** | G-hold 両側の義務 cell 保持率 ≥ bound（D-3） |
| **L3 = g3** | C1 seat（pre-pin 窓 STEP7末-9） | （seat は cable 状態） | **G-seat(C1) pre-pin**・found link 記録 |
| L-R1 | C1 解放遷移（STEP8-10・**帰属 = choreography/release**） | — | seated_any(C1) 持続（pin 発火後は pin 挙動として別帰属・grip 測定外） |
| L4 | **C2 REGRASP**（STEP12-14） | STEP12-13: **L**・STEP14: **L+R** | regrasp gate 後 **G-close(R)**（fresh 右腕） |
| L5 | C2 搬送+押込（STEP14-16） | **L+R** | G-hold 両側 ≥ bound |
| L6 | C2 seat（pre-pin 窓 STEP15末-16） | — | **G-seat(C2) pre-pin** |
| L-R2 | 最終解放（STEP17-18・**帰属 = release/choreography・grip 測定外**） | — | seated_any(C2) 持続（pin 有効下） |
- 分母 = 各 leg の entry gate 通過数・**side 列つき**・二重計数禁止・INVALID は理由分布つき全数印字。
- **N（D-4・cycle-1 で bound 添付）**: 提案 20 は **20/20 でも Wilson-95 下界 0.839** — **≥84% の主張は不能**（95% 下界には N≥73 全 PASS 相当）。⇒ **N は主張したい下界から逆算して re-debate で確定**（連鎖分母: 0.7/leg 仮定で L6 有効 20 に L1 入口 ~119・INVALID 30% で ~170 launch）。
- IC: v0.1 どおり固定 IC 先行・ランダム化 = DEPLOY 要件として第 2 段（defer 明示）。

## §5 視覚レグ（mandatory）

- 判定順序 = 動画 → ログ → 照合。**skill-path 必須**: `/verify-run` または `/video-analyzer` + `video-analyst`（manual 単一フレーム Read はレグを満たさない — CLAUDE.md テスト検証プロトコル）。
- 対象 = 各 leg 代表 + 全 VALID-FAIL + INVALID sample。**Rs 動画確認 = critical アンカー**。

## §6 conservatism（cluster D で方向訂正）

| 対象 | conservative 側 |
|---|---|
| G-close/G-hold 窓・floor | 狭く/高く読む側（緩める変更 = Rs 承認） |
| G-seat tol | 小さい側（+ **接触 conjunct 必須** — 幾何のみは降下透過の偽 PASS = non-conservative） |
| **within-leg 帰属** | **曖昧 = VALID-FAIL に数える側**（⛔ v0.1 の「INVALID 広く = conservative」は**逆** — 分母を削ると率が上がる。INVALID を広く取ってよいのは**計器起因が実証された**場合のみ） |
| **transfer 方向（新規行）** | scripted-PD driver → trainer env/policy の転移方向は**未宣言のまま測定しない** — 実測時に fidelity 差を明示（fixed IC・choreography scripted は success を易しくする側 = non-conservative 成分として記録） |

## §7 /reward-design 4 artifact（適用形 — ⛔ **gate PASS ではない**・D 値確定後に全 protocol 再走）

1. **到達可能性**: §4 の leg 可用性は **「driver がその leg の STEP まで green」の per-leg 関数**（v0.1 の「L3 まで green」単一条件は撤回 — STEP13 の open は L4 系の話で L3 を塞がない）。**#57（左 start pose = 棄却群からの最良）open の間の L1-L2 左腕値は「measure-and-mark」**（#57 taint を witness に記録して測る・disposition は re-debate）。
2. 因果 DAG: G-close → G-hold(義務 cell) → G-seat(pre-pin) ↛ pin。
3. **ground-truth 現況**: 既知 = release_floor ≈18.19mm・MOUTH_BAND_Z（spec 導出）・(2.0,8.0) 窓・seat tol（±22/±7.5/±6mm・`seat_tolerances()`）・**実測動作点 = 背板 6.81mm（`:104`・60N 飽和下）— 窓上端まで 1.19mm** ⇒ **窓端 margin は動作点基準で設計**（nominal 4mm 基準は誤り）。**SSOT home（cluster K）**: 窓・tol・floor の現住所 = driver/cell-spec（interim SSOT @ `02b85fc52f`）— impl 時に task_config へ landing（= L3・Rs）。
4. episode trace: STEP 列 × mask × gate 値の期待レンジ（v0.2 の mask 表準拠）。

## §8 出力契約

per-episode JSON: leg/side 到達 flag・G-close/G-hold/G-seat 時系列・**found seat link id・把持 link id（入口/出口）**・INVALID 理由（両因印字含む）・pin 状態・**substrate census 結果**・witness（model sha・**driver commit**・config・wc=1 確認）。集計 = leg×side 分子/分母 + 除外全数 + **両側 bound**。

## §9 lane（不変）

p5 = 本 DoD 設計・D-list 設計側・verdict 設計軸検証／p11 = PD 前提供給／lead lane = runner 実装・実測／Rs = 動画 GT・sign-off。⛔ 実行 authorize なし。

## §10 D-list（cycle-1 反映版）

D-1′ link-identity 追跡（cable_in_mouth/MOUTH_BAND_Z は既存採用）／D-2 seat tol の UR15 妥当性／D-3 G-hold 保持率 bound（義務 cell 上・sampling 周期）／**D-4 N（Wilson 下界表つきで確定）**／D-5 REGRASP 窓（STEP12-14 の時間条件）／**D-6 G-dual（接触/G-hold 非対称 + arm-arm 近接で再 seed — command 流量は不採用）**／D-7（新）**帰属規則の event flag 実装形**（arm-arm 接触・tracking 失速・IK fallback の観測面）。各 D は測定手順つき・数値の発明なし。

## §11 cycle-1 記録（2026-08-08・panel 5 体・verdict = FAIL-revise）

- 受諾 cluster: **A** grasped→held 計器選択（4/4 収束・CRITICAL）／**B** seated 固定 link→seated_any（Rs 目撃欠陥の再輸入・HIGH）／**C** mask 欠落（保持率上限 0.52 が設計から出る・HIGH）／**D** conservatism 逆転＋帰属規則欠落（HIGH）／**E** #56 誤読・:1391 機構誤り（4/4・HIGH）／**F** 被覆 18/43 未宣言（HIGH）／**G** /pre-check 欠落・§7 の gate 扱い（HIGH）／H G-dual proxy／I 開始条件の非整合・#57／J substrate gate／K SSOT home／L driver pin／M g3 名指し／N N 統計限界／O 動作点 6.81mm／P wc envelope。**REBUT = 0**（全受諾 — 反証可能な挑戦はなかった）。
- NHA = CHANGE_JUSTIFIED（PD 期 DoD の既存 artifact 0・commission 実在・(c) 全面 defer は内蔵の開始条件に支配される）。
- **⇒ 本 v0.2 が cycle-2 の対象**。cycle-2 で CRITICAL/HIGH 残 0 なら PASS → §0 の chain（/reward-design 全走 → /pre-check → rule-check → impl[Rs sign-off]）へ。
