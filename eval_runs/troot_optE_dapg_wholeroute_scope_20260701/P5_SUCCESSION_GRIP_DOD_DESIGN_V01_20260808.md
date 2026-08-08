# SUCCESSION #18 — PD 基盤 grip-efficacy 実測の測定系・DoD 設計（v0.1 DRAFT）

**Author**: p5 SKILL-DETAIL-DESIGN。**Status**: **DRAFT v0.1 — design-side・re-debate 前**。
**Commission**: Rs first-hand（p5 session `c2d317bc`・2026-08-08 10:4x「DoD 設計の commission を出す — 着手して」— 逐語 pin は p18 の transcript 読みで恒久化可）。lane = Q1-Q5 裁定 Q5（`P5_DDR18_PREMISE_RERULING_MATERIALS_20260808.md` §8 @ `7626027b3a`）。
**位置（gate chain）**: 本 draft → **#18 re-debate（L3）** → impl（lead lane・Rs sign-off）→ 実測。⛔ **本 doc は実行を authorize しない**（execution HOLD 継続・LEDGER row 18 の fence のまま）。⛔ code 変更 0・run 0。

**版表**（stamp = `date` 実測 JST・binding = 各行に witness commit を bank 後追記）
| 版 | 内容 | stamp |
|---|---|---|
| v0.1 | 初版 draft（本 doc） | 2026-08-08 10:45:40 |

**invariant guard**（変更しない・触れたら STOP+Rs）: **DUAL-ARM**（全 motion 両腕）/ **DiffIK-only**（PD 実現は charter `charter_v231.md:351-361` の範囲内）/ **コ gripper LOCK**（#44 arc の現行 = working asset 16.00・spec 着地済）/ **no-kinematic-trick**（唯一の例外 = clip-retention pin）。⚠ **span は述語にしない** — §0#2 は「指令 88 / 実測 75」の 2 面が既知（DDR #58）で、grip の実体は face gap 側で測る。

---

## §1 measurand（何を測るか）

**grip-efficacy** = **PD closed-loop 駆動下で、把持を保ったまま seat 段の gate に到達する能力**（succession row = LEDGER row 18 Q1(a)「PD 基盤での grip-efficacy 実測」の実測定義）。
- 報告単位 = **leg 別の条件付き成功率**（分母 = その leg に**有効到達**した episode 数）。
- ⛔ **whole-route 単一 % に潰さない**。理由 = 本 project の 3 教訓を設計に内蔵する: #49（整定ゲート未到達なら後続数値は無効）/ #56（計器が失敗を報告できない状態の走行は測定でない）/ #59（候補の二重計数・分母過大）。

## §2 段構造と validity gate（アンカー式検証の測定形）

- **段 = canonical 43-step 表の Phase 境界**（`RL-Routing-Design.md` §2 @ `59badc4b7a`・driver header `ur15_steps_wired.py:2-8` が同 commit を名指し）: **A**(STEP1-5) 初期把持 / **B**(6-10) C1 routing / **C+D**(11-18) C2 routing（**C2 REGRASP 含む**）。⚠ 表の幾何は UR5e 由来で provisional（同 header 逐語「numeric layout is provisional for UR15 … p5 governs the final geometry」）— 本 DoD は **STEP 系列と finger/clip 状態**にのみ bind し、幾何数値には bind しない。
- **entry gate**: 各 leg の測定は、直前 leg の exit gate が **実体で**確認された episode でのみ有効。
- **episode 3 値 taxonomy**: **VALID-PASS** / **VALID-FAIL**（grip 起因 = 本 measurand）/ **INVALID**（route・choreography・計器起因 = **分母から除外・ただし除外数と理由を必ず印字** — silent cap 禁止）。⇒ 「route が届かなかった」と「grip が滑った」を**構造で**分離する（旧 #18 の混同の再発防止）。

## §3 述語（実装済み surface に bind — 名前は実物・as-read 2026-08-08 10:43）

| 述語 | 定義 | bind 先 |
|---|---|---|
| **G-grip(t)** | face gap ∈ **(2.0, 8.0) mm**（Ø8 cable・設計圧縮 2mm/側 ⇒ nominal 4mm） | `ur15_steps_wired.py:570-584` `grasped(t)`・`jaw_gaps` |
| **G-seat(clip)** | xy tol 内 ∧ \|z − GROOVE_Z\| < `_tz` | `:963-968` `seated()`・`Z_SEAT = GROOVE_Z`（`:91`）・seat link = 実行時 print（`:351` `C1=cab{SEAT1} C2=cab{SEAT2}`）で **episode ごとに pin** |
| **G-dual** | 全 motion で両腕が役割を持つ（単腕化の検出 = 非把持腕 target 更新 0 の区間 flag） | DUAL-ARM invariant の測定形（新設・D-6） |
| **G-transit(t)** | leg 区間中 G-grip(t) の保持率（sampling 周期 = D-3） | `grasped(t)` の時系列 |

- ⚠ **G-grip の偽陽性 guard（D-1）**: 「gap が窓内 ∧ cable は別の場所」を排除するため **cable 最近接 link と claw の近接 bound を併置**（∧ 条件）。数値は substrate 実測で導出 — 発明しない。
- ⛔ **pin は述語に使わない**: `C1_pin`/`C2_pin`（`:282-283`・authorized clip-retention 例外）は **retention 機構であって成功の証拠ではない**。判定対象 = **pin fire *前* の seat**（旧 #18 ②の分析 = pin は slip を rescue しない、と整合）。episode log に pin 状態を必須記録（混入検出用）。
- **can-report-failure 検査（#56 対応）**: 既知の「常時 0.0% held を印字する regime」（`:1391` — 指が開かない command 経路）を **entry gate で検出して INVALID 化**。計器が失敗を報告できない状態での「成功」は数えない。

## §4 coverage set（legs × sides の列挙・#59 対応）

| leg | 内容 | 段 | 分母の entry gate |
|---|---|---|---|
| L1 | 初期把持成立（**両側**） | A exit | STEP1-5 完走 ∧ 整定 |
| L2 | C1 transit 保持 | B | L1 PASS |
| L3 | **C1 seat**（G-seat@C1） | B exit | L2 PASS |
| L4 | **C2 REGRASP**（fresh 右腕把持 = 旧 #18 coverage gap ③ の主対象・最高 risk） | C | L3 PASS |
| L5 | C2 transit 保持 | C+D | L4 PASS |
| L6 | **C2 seat**（G-seat@C2） | D exit | L5 PASS |

- **報告 = leg 別 分子/分母 ＋ INVALID 数と理由分布**。候補・episode の二重計数禁止。
- **N（各 leg 有効 episode 数）= 提案 20**（D-4 で CI と共に確定 — re-debate 論点）。
- **IC**: v0.1 = **固定 IC**（到達可能性を先に確立）。cable pos/pose ランダム化は DEPLOY 要件（RS71 §0-A）として**第 2 段**に明示 defer（隠さない）。

## §5 視覚レグ（mandatory — numeric 単独 PASS 禁止）

- 判定順序 = **動画 → ログ → 照合**（三者一致・ログ数値で動画解釈を上書きしない）。
- 対象 = 各 leg の代表 episode ＋ **全 VALID-FAIL** ＋ INVALID の sample。
- **judge-fit 要件**: 把持部・seat 部が判定可能な視点を撮影計画に含める（⚠ `ee_pos` は手首 flange で爪先ではない — 撮影と判定の対象を爪・cable・groove にする）。
- **Rs 動画確認 = critical アンカー**（把持・着座の weight-test は Rs 専権・数値と agent 判定のみで成功を主張しない）。

## §6 conservatism 方向の宣言（§運用15）

| 述語 | conservative 側 | 備考 |
|---|---|---|
| G-grip 窓 (2,8)mm | **窓を狭く**読む側 | 広げる変更は non-conservative ⇒ Rs 承認要 |
| G-seat tol | **tol 小** | UR15 値の妥当性 = D-2 |
| INVALID 判定 | **広く**取る側（分母を削る方向） | ただし除外は全数印字 — 隠れた severity 上げを可視化 |
- non-conservative PASS は転移前に高 fidelity 確認 / conservative FAIL は bank 可。

## §7 /reward-design 4 artifact（本 DoD への適用形）

1. **到達可能性テーブル** = §4（各 leg の entry gate と現況）。⚠ **測定開始条件 = driver が L3 まで green**（現況の既知課題: STEP13 open question `:467`・start-pose 系 #57 — これらが解ける前は **L1-L2 のみ測定可**と明示。choreography-blocked（L-P0）の教訓 = 「route が組めること」は grip 測定の前提であって一部ではない）。
2. **因果 DAG**: grasp(face gap) → transit hold → seat(xy,z) ↛ pin（pin は下流・測定外・混入検出のみ）。
3. **ground-truth 値の現況**: 既知 = `CLAW_RELEASE_GAP`・CLAMP ctrl map（80mm→17.7 / 12mm→214.1 / 4mm→235.5・`:97-99`）・`GROOVE_Z`/`Z_SEAT`・seat link 同定・grasped 窓 (2,8)mm。**導出待ち D-list**: D-1 cable-claw 近接 bound / D-2 seat tol の UR15 妥当性 / D-3 G-transit sampling 周期 / D-4 N と CI / D-5 REGRASP 窓（時間条件） / D-6 G-dual の実装形。⛔ **各 D は測定手順つきで re-debate に出す — 数値を発明しない**。
4. **episode trace（PASS の形）**: STEP1-5（整定・両腕把持 G-grip 両側）→ STEP6-10（G-transit ≥ bound・C1 で G-seat）→ STEP11-18（REGRASP 窓で右腕 G-grip 再成立 → G-transit → C2 G-seat）— 各境界で gate 値を log。

## §8 出力契約（binding 規則内蔵）

- per-episode JSON: leg 到達 flag 列・述語時系列（gap / claw_gap / seat 距離）・INVALID 理由・pin 状態・**witness pin**（model sha・driver commit・config・seat link 実名）— **各値は自分の出所 object を名乗る**（値と witness を同じ record に）。
- 集計: leg 別 分子/分母・除外の全数と分布。**印字に無い数を報告しない**（§運用27）。

## §9 lane（Q5 裁定の実施形）

- **p5** = 本 DoD 設計・D-list の設計側導出・verdict の設計軸検証。**p11** = PD 前提（gains・整定基準・ramp 条件）の供給。**lead lane** = runner 実装・実測。**Rs** = 動画 GT・re-debate 後の sign-off。
- ⛔ 本 doc から実装へ進む前に: **#18 re-debate（L3）** → rule-check → impl は fenced（gate chain どおり）。

## §10 re-debate へ回す open 問い

1. N=20/leg の統計的十分性（D-4）。2. IC ランダム化の段階設計（v0.1 固定 → 第 2 段）。3. REGRASP 窓の定義（D-5）。4. held% 計器 regime（`:1391`）の修理 owner。5. G-dual の具体形（D-6）。6. L1-L2 先行測定の可否（driver green 前の部分測定に価値があるか）。
