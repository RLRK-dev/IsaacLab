# SUCCESSION #18 — PD 基盤 grip-efficacy 実測の測定系・DoD 設計（v0.3 — cycle-2 全受諾反映・REVIEW to Rs）

**Author**: p5 SKILL-DETAIL-DESIGN。**Status**: **v0.3 — re-debate cycle-2 の全受諾 challenge を fold・protocol の max-2-cycles 到達 ⇒ verdict = REVIEW（Rs 裁定へ）**。
**Commission**: Rs first-hand（`c2d317bc` 2026-08-08 01:42:56.775Z = 10:42:56 JST・p18 検証 `m-p18-78`）。lane = Q5（materials §8 @ `7626027b3a`・**§10(a) の cite は `b32263a886`**〔§10 は次 commit で landed — cycle-2 CC3/CC4/CC5 指摘〕）。
**chain**: 本 v0.3 → **Rs REVIEW**（cycle-3 要否 or 続行）→ /reward-design 全 protocol 再走（**OPEN**・D 値確定後）→ /pre-check（**OPEN**）→ rule-check → impl（Rs sign-off）→ 実測。⛔ **実行 authorize なし**（row 18 execution HOLD・fence 継続）。⚠ Q3 fence: 実測位置 = #18-last — (d) P-D1（**07-19 に走行済・evidence `e5d2dc214a`** — 完了 gate を待たない）→ gate chain 再構成の後。⚠ **DDR #38**（UR15 第 2 波「新しい腕（mirrored）」記録 open）**着地時の rebind 再確認は §2 mask・§4 windows・§7.3 ground-truth にも及ぶ**（§3 だけではない — cycle-2 CC5）。
**pins**: driver = `p4_ur15_sim_20260727/ur15_steps_wired.py` @ **`02b85fc52f`**（sha head `2ab042b6970654cc`・3,834 行）／canonical 表 @ **`59badc4b7a`**／LEDGER 行引用は **row id + as-read 時刻**で読む（bare `:NNN` は成長 file で腐る — commit 併記 or 再解決）。

**版表**
| 版 | 内容 | stamp |
|---|---|---|
| v0.1 | 初版（banked `8a3bde897a`） | 2026-08-08 10:45:40 |
| v0.2 | cycle-1 FAIL-revise 反映（cluster A-P・banked `9b5aada66d`） | 11:1x |
| v0.3 | **cycle-2 全受諾 fold**（§11 参照・panel 記録 = verification-log.jsonl CYCLE=2） | 2026-08-08 11:55:21 |

**invariant guard**（不変）: DUAL-ARM / DiffIK-only / コ LOCK（16.00 現行）/ no-kinematic-trick（pin 例外のみ）。span 非述語（#58）。

---

## §1 measurand

**grip-efficacy** = PD closed-loop 下で、**grip 義務 cell を通して把持を保ち、pin 発火前に seat に到達する能力**。**g3 = L3**。L5-L6 = ruled skeleton の拡張（明示）。報告 = **leg×side 条件付き成功率＋両側 bound**。⛔ 単一 % 化しない。
**被覆宣言**: 本 DoD = **C2 instance（STEP1-18）= 18/43 step・2/5 clip**。C3-C5（再把持 ×3 含む）・Phase E は**非被覆・transfer 主張なし**。

## §2 段構造・grip 義務 mask・taxonomy

**指令指状態**（driver `:2702-2721` @ `02b85fc52f`・(L,R)）: 2-3 OPEN,OPEN／**4-7 CLAMP,CLAMP**／8-11 HALF,OPEN／12-13 CLAMP,OPEN／**14-16 CLAMP,CLAMP**／17 RELEASE,RELEASE／18 HALF,OPEN。gate: grasp@4・pinC1@9・regrasp@14・pinC2@16。
- **義務 cell = 指令 CLAMP の (STEP, side)**。ただし **close ramp 中は義務外**（cycle-2: `gf=0` gate + FINGER_RAMP により **cell (14,R) は構造上 大半 un-held** — 評価瞬間 clause は **retention cell の開始にも適用** = close+settle 完了から義務開始）。**handover pin**: STEP7→8 = **L: CLAMP→HALF・R: CLAMP→OPEN**／STEP16→17 = CLAMP→RELEASE。
- **評価瞬間 clause**: 閉じ系判定は close+settle 完了後（t42 fix row C 着地済 = 実測前提・**settle の定義は D-8**〔ticks or gap-velocity bound・owner = re-debate〕）。**G-close checkpoint は 3 つ**: L1@STEP4（両側）・**STEP12 後（L・新設）**・L4@STEP14（R）。
- **episode taxonomy（4 値・cycle-2 で拡張）**: VALID-PASS ／ VALID-FAIL(grip) ／ **RELEASE-FAIL**（L-R leg での dislodge — **grip 率に不算入・ただし §5 の動画 mandatory 対象**〔Rs 目撃 class の観測義務を落とさない〕）／ INVALID（全数印字）。**帰属規則**: VALID-FAIL(grip) = 義務 cell 中の G-hold 減衰が同時 choreography event（D-7 flag: arm-arm 接触・tracking 失速・**STEP-labelled** IK fallback）なし。同時 event → INVALID（両因印字）。**曖昧 → VALID-FAIL**。⚠ arm-arm 近接の sampling は 40-tick 粗さ ⇒ 同時性が判定不能な場合も曖昧則で VALID-FAIL 側（conservative・§6 行）。

## §3 述語

| 述語 | 定義（実装 conjunction・全て @ `02b85fc52f`） | 用途 |
|---|---|---|
| **G-close(t)** | `grasped(t)` = 両側 pad1×cable 接触（`:553-566`）∧ face gap ∈ (2.0,8.0)mm（`:580-584`） | 閉じ品質（STEP4 両側・STEP12 L・STEP14 R・close+settle 後） |
| **G-hold(t)** | `held(t)`（`:855-874`）= 背板 gap < `release_floor()`（=18.19mm）∧ `cable_in_mouth(t)`（pad-local band・**実行値 (23.0, 39.0)mm** — docstring の 25-39 と差、実行値が正） | retention（義務 cell 時系列） |
| **G-seat(clip)** | `seated_any(clip)` = ANY link で `seated()` 全 conjunction = xy tol ∧ \|z−GROOVE_Z\|<_tz ∧ **clip×cable 接触（部位不問** — `:971-975` は任意の C1_*/C2_* geom との接触で、**床限定ではない**。⚠ jaw-sustained/壁接触 seat の非保守成分は §6 行＋**pin residual・axial anchor offset（`:3506-3522`）を §8 で記録**して判別・床/link 限定の強化は D-2） | seat（pre-pin 窓） |
| G-dual | D-6: per-side G-hold 非対称の持続 ＋ arm-arm 近接/接触（command 流量 proxy 不採用） | DUAL-ARM 測定形 |
- **L3 の exit 瞬間（cycle-2 で確定）**: **pin-fire tick の seated_any**（または PIN_SETTLE 持続 — 選択は D-2）。∃-tick 読みは不採用（seat 一瞬→喪失→pin 不発 の episode を PASS にしない）。**pre-fire の seat 喪失は L3 の FAIL**（L-R1 に逃さない）。
- **can-report 検査**: false-FAIL 系 = STANDING ERROR ≥ TRACK_TOL・stall RuntimeError・held-back tick 比 → INVALID。**β（訂正）**: fallback 開示は**現 driver では un-gated（`:2202-2211`）** — per-episode に**既存の開示行を集計**し、**STEP-labelled solve（`STEP{n} per-step`/`seating`）の発火 >0 → INVALID**。**start-pose solve の発火は INVALID にしない**（#57 により決定論的に発火 — これを INVALID にすると N_valid=0）— **#57 taint witness へ記録**。γ = 非該当（掃引でない）。
- **substrate census gate**: **actuator 名の set equality ∧ nu==14**（読み面 = `:351` log 行 or `_steps_cell_full.xml`）— 不一致 = INVALID（B1 = state・per-run 再確認。provenance = materials **§10(a) @ `b32263a886`**）。
- **schedule tripwire（cycle-2 新設）**: per-run で STEP 表（指状態列）echo → 本 doc の mask と比較・**不一致 = INVALID**（driver 編集で mask が黙って外れる class を封じる）。
- envelope: wc=1・単一 world・CPU mujoco。wc≠1 = INVALID。

## §4 coverage（legs × sides・entry gate 列 復活）

| leg | 内容 | entry gate | 義務 cell（side） | exit gate |
|---|---|---|---|---|
| L1 | 初期把持（STEP2-4） | episode 開始・census PASS | STEP4 close+settle 後: L+R | G-close 両側 |
| L2 | C1 搬送+押込（STEP5-7） | L1 PASS | STEP5-7: L+R | G-hold 両側 ≥ bound（D-3） |
| **L3 = g3** | C1 seat（pre-pin 窓 STEP7末-9） | L2 PASS | — | **G-seat(C1) @ pin-fire**（found link 記録） |
| L-R1 | C1 解放遷移＋C2 上空搬送（**STEP8-11**・cycle-2 で 11 を包含） | L3 PASS | — | seated_any(C1) 持続（**FAIL → 下流 INVALID(route)・理由印字**）。dislodge = **RELEASE-FAIL** |
| L4 | C2 REGRASP（STEP12-14） | L-R1 PASS | STEP12-13: L（12 close+settle 後）・STEP14: R は close+settle 後のみ | G-close(R)＋G-close(L)@12 |
| L5 | C2 押込（**STEP15-16**・cycle-2 で 14 を除外 — 二重計数と ramp false-FAIL の除去） | L4 PASS | STEP15-16: L+R | G-hold 両側 ≥ bound |
| L6 | C2 seat（pre-pin 窓 STEP15末-16） | L5 entry と同時進行・L5 PASS で有効 | — | **G-seat(C2) @ pin-fire** |
| L-R2 | 最終解放（STEP17-18） | L6 PASS | — | seated_any(C2) 持続（dislodge = RELEASE-FAIL・pin 有効下の挙動として別帰属） |
- 分母 = entry gate 通過数・side 列・**STEP11 は L-R1 に帰属**（無主 STEP を残さない）・二重計数禁止（STEP14 = L4 のみ）。
- N = D-4（Wilson: 20/20 → LB 0.839・95% LB には N≥73 全 PASS・連鎖 ~119/~170）。IC 固定先行・ランダム化 = 第 2 段。

## §5 視覚レグ（mandatory）

動画 → ログ → 照合・**skill-path 必須**（/verify-run or /video-analyzer + video-analyst）。対象 = 各 leg 代表 + **全 VALID-FAIL + 全 RELEASE-FAIL** + INVALID sample。Rs 動画確認 = critical アンカー。

## §6 conservatism

| 対象 | 方向 |
|---|---|
| G-close/G-hold 窓・floor | 狭く/高く = conservative（緩和 = Rs） |
| G-seat | tol 小 = conservative。⚠ **接触 conjunct は「clip 接触（部位不問）」** — jaw-sustained/壁接触 seat は **non-conservative 成分**（pin residual・axial offset で判別・D-2 で強化判断） |
| 帰属 | 曖昧 = VALID-FAIL 側（40-tick sampling の同時性不能も同側） |
| transfer | scripted-PD → trainer の方向は未宣言のまま測定しない（fixed IC・scripted choreography = non-conservative 成分として記録） |

## §7 /reward-design 4 artifact（適用形 — ⛔ gate PASS ではない）

1. 到達可能性 = per-leg「driver がその leg の STEP まで green」。**#57 open 中の L1-L2 左腕 = measure-and-mark**（**taint flag は §8 field ＋ §4 集計列に実装** — cycle-2 CC5。start-pose fallback 行が観測面）。
2. DAG: G-close → G-hold(義務 cell) → G-seat(pre-pin) ↛ pin。
3. ground-truth: release_floor 18.19mm・**MOUTH_BAND_Z 実行値 (23.0,39.0)mm**・(2.0,8.0) 窓・seat tol ±22/±7.5/±6mm・**動作点 6.81mm（`:104`・⚠ ctrl 255 指令下の測定 — CLAMP 235.5 との条件差は明記の上使用）**・HALF 12mm = 2×`task_config.py:275`。**SSOT home**: interim = driver/cell-spec @ `02b85fc52f`・**task_config landing 時は同域の PhysX 期定数（`T_GROOVE`/`GROOVE_CENTER_Z`/`GROOVE_BODIES_MIN`）の supersede/整合を明示**（= 二重 regime を作らない・L3/Rs）。
4. episode trace: STEP 列 × mask × gate 値（v0.3 表準拠）。

## §8 出力契約

per-episode JSON: leg/side flag・G-close/G-hold/G-seat 時系列・found seat link・把持 link（入口/出口）・**#57 taint flag**・**pin residual（engagement 時+settle 後）・axial anchor offset**・**STEP-labelled fallback 数／start-pose fallback 数（別 field）**・4 値 taxonomy 理由・pin 状態・census 結果・**schedule echo 照合結果**・witness（model sha・driver commit・config・**env freeze: newton/mujoco/mujoco-warp/warp 版 + venv 名**・wc=1）。集計 = leg×side 分子/分母・**taint 列**・除外全数・両側 bound。

## §9 lane

p5 = 設計・D-list・設計軸検証／p11 = PD 前提／lead = runner・実測／Rs = 動画 GT・sign-off。⛔ 実行 authorize なし。

## §10 D-list

D-1′ link-identity（cable_in_mouth 採用済）／D-2 seat 強化判断（床/link 限定・PIN_SETTLE 持続 vs pin-fire tick）＋ tol 妥当性／D-3 G-hold bound・sampling／D-4 N（Wilson 表つき）／D-5 REGRASP 窓／D-6 G-dual／D-7 event flag 実装形（既存観測面: held_ticks `:3630`・arm-arm path `:3735`・fallback 行）／**D-8 settle 定義（新設・owner = re-debate）**。

## §11 debate 記録

- **cycle-1**（v0.1・panel 5 体）: 36 challenges → cluster A-P **全 ACCEPT**（REBUT 0）・NHA CHANGE_JUSTIFIED ⇒ **FAIL-revise** → v0.2。
- **cycle-2**（v0.2 banked `9b5aada66d`・panel 5 体）: cluster **discharge 16/16（内容）** — CC2 15/16（B = 文言）・CC3 16/16・CC4 16/16・CC5 14/16（I/J = 配線）。**新規 challenge**: CC2 = G-seat conjunct 文言（HIGH）・cell(14,R) ramp false-FAIL（HIGH）・β 規則が #57 下で N_valid=0（HIGH）・L3/L-R1 瞬間・entry 列・小 bundle／CC3 = β 記述 stale・§10(a) pin・landing 衝突集合・ほか LOW／CC4 = N1 (14,R)（M-H）・N2 STEP11 無主（M）・N3 jaw-sustained seat（L-M）・N4 pin／CC5 = taint 配線（HIGH）・dislodge が taxonomy/video から漏れ（HIGH）・settle 未定義（M-H）・census 述語形（M）・schedule tripwire（M）／NHA = CHANGE_JUSTIFIED・cycle-3 は「新情報なき再審」として不要見解。**CC1 = 全 ACCEPT（REBUT 0）→ 本 v0.3 に全 fold**（§2 ramp 除外+4 値 taxonomy+評価瞬間拡張／§3 conjunct 文言訂正+β 訂正+census 述語+tripwire／§4 entry 列+STEP11 帰属+L5 再定義+L3 瞬間／§7 taint 配線+条件差+衝突集合／§8 拡張／D-8）。
- **protocol 到達点**: max 2 cycles 消化・cycle-2 で HIGH が出て受諾された ⇒ 機械判定は FAIL-revise だが **fix は全て文書内の bounded edit で v0.3 に反映済み**（architecture 変更なし・計器選択と mask と統計は cycle-2 で全数 recompute 済み）。⇒ **verdict = REVIEW: Rs が ①cycle-3（v0.3 への第 3 panel）を要求する ②v0.3 を design-side accept とし、残余検証を chain の OPEN station（/reward-design 全走・/pre-check）に委ねる — のいずれかを裁定**。panel 逐語 = verification-log.jsonl（task-p5-succession-dod-redebate-001・CYCLE=1,2）。
