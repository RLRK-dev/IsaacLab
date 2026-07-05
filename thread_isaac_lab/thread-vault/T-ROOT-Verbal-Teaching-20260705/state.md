---
node_id: T-ROOT-Verbal-Teaching-20260705
goal: scripted route の動作を人間の言葉で効率的に教示可能にする (往復数削減; Rs 意向 2026-07-03 verbatim)
means: table-driven route (target-SOURCE 型 row schema) + 教示 loop (言葉→表 param→leg-diff+参照差分動画の機械検証→Rs 確認) — 段階 build St1a(証拠ゲート)→St1b/St2/St3(実測 trigger 繰延)
status: BUILD-AUTHORIZED (paper 先行 — Rs「VT St2 着手可」2026-07-06 08:3x, eba71929b3; 順序 = φ10 追撃/DC-1 の後 [locked runner 衝突回避]、設計 paper 先行 = 即時 GO; ← DESIGN-APPROVED 03:2x / design v1.4 b17b473a15)
dependencies: precedent = T-ROOT-StepTable-Verbal-Teaching-20260703 (%10 scoping) / blocker = W0-e close (build 開始条件、charter:31)
parent_node: T-ROOT
children_nodes: []
session_history: [p5 VT-DESIGN (ccefc8f8, 2026-07-06 design chain), f5c9a26f (%12 drive)]
---

# T-ROOT-Verbal-Teaching-20260705 — state

- 2026-07-05 20:0x: Rs charter 承認 →`eval_runs/troot_verbal_teaching_20260705/CHARTER_V1.md` (a4863d9b13)。
- 2026-07-06 01:4x-03:1x (p5 VT-DESIGN + %12): **設計 chain 完結** — DESIGN_V1.md v1.0→v1.4: %12 review (修正2+注記2) → %10 author-review CONCUR (fix-⑤ 事実 §運用28 再検証) → 5体 L3 debate **FAIL** (CRIT = 撤去済み逸脱 [F-1a-v2/F-3] の class-A 混入 = 先祖返り再導入を LEDGER 行から捕捉; +6 HIGH) → v1.3 → targeted re-verify (新 7 bounded) → v1.4 grep-CLEAN = **PASS**。記録 = L3_DEBATE_PROPOSE/DECIDE.md, L3_REVERIFY_RESULT.md, RS_APPROVAL_PACKET.md。
- 2026-07-06 03:2x: **Rs 設計承認「承認」** — D-1 (St1a 証拠ゲート・HOLD 可 / St1b-St3 実測 trigger 繰延) + D-7 (class-B 基準改定 = **Rs 承認鍵** + 同ターン LEDGER 反映の正式化; 現 V2 凍結 = precedent-with-caveat) + D-2/D-5 繰延 + D-3 scope C1→C2 + D-6 実証例 両 class ≥1。durable value = param-ownership 一本化答 + class-A/B・INVARIANT・motion-standard 統治枠組み + fix-⑤-as-row thesis (St2)。build-time 項 = N5 (env 全列挙) / N6 (freeze artifact quarantine)。**本 node 起票 = この承認 ([DEFINE] 相当)。**
- 2026-07-06 06:53 (%12 formalize, Rs 質問「番人はいつアクションするのか」): build 起動条件を standing order 化 → 下記 **番人 trigger 台帳** を本 state.md に設置。p5 (VT node 番人) 常設任務 = 台帳維持 + W0-e close 時の遡及カウント。
- 2026-07-06 06:5x (Rs 追認, via %12 06:55): 「自動で最適なときに機能すれば良い」= trigger 駆動の自動発火運用を追認、台帳運用継続。**build 着手点の Rs 承認 gate は設計 v1.4 のまま不変** (St1a = D-1 提案 gate / St1b+ = L3 + Rs explicit auth)。自動化対象 = 監視・台帳・遡及報告のみ; 実 build authorization は Rs gate 維持。

## 番人 trigger 台帳 (standing order — %12 2026-07-06 06:53 formalize / Rs 06:5x 追認)

DESIGN_V1.md v1.4 evidence-gate どおり build は自動起動しない。番人 = trigger を監視・記録し、最適点 (W0-e close) で Rs 向け 1 行判断を自動発火する。実 build は Rs 承認 gate 通過後のみ。

| trigger | 定義 | 記録 → action | 接地 (DESIGN_V1.md) | 現況 |
|---|---|---|---|---|
| **T1 → St1a** | scene/global param 編集で実測コスト >> 数分 の事例 | 事例を記録 (D-1 precondition (a) 証拠蓄積)。St1a 提案は **(a) 実測 cost>>分 ∧ (b) discipline-only (既存 env-override=DoD-0) が ≤1 往復を満たさない** の両立時のみ。≈0 gap なら **HOLD St1a** | :209 (§7 D-1 (a)/(b)) | **0 triggering** (08:03 遡及済: LIFT_M/CLIP2_Y/CLIP_X/CLIP_Y 全て env-override 1発, ≈0 gap → HOLD) |
| **T2 → St2** | 新 primitive 必要 = 既存 leg の座標編集で表現できない教示 | 累計 **2 件**で St2 提案 (L3 + Rs auth) | :110 (§3.3「≥2 measured new-primitive needs」) | **T2 = 2 (fix-⑤ + F-1a), 累計 gate 到達** (%12 08:09 code-verify ACCEPT; scope=累計 確定) → St2 = **Rs-decision-ready** |
| **T3 → 即時** | Rs 直接指示 | 即時着手 | charter (Rs 専権) | — |

- **build 最速点** = W0-e close 後 (charter:31)。%12 06:53 時点で round-2 grid 48/81 走行中 → 本日 close 見込み (%12 projection)。
- **W0-e close アクション (%12 banking signal 受領で発火):** W0-e 全史に対し T1/T2 を遡及 count → Rs 向け 1 行「HOLD 継続 or St1a 提案」。%12 provisional read = 今夜の修正は全て座標編集 = **T2 0/2**、遡及 count は私 (番人) が close 時に確定させる (T1 も同時 count)。
- **honest 既定 = HOLD 継続** (D-1: St1a の 4 param は既に env-override 有 → ROI≈0 なら HOLD が正直な帰結。RS_APPROVAL_PACKET.md §3)。

- 2026-07-06 08:03 (**番人 遡及 count 実行** — %12 banking signal 07:57 受領 [round-2 official SR = 58/81 = 0.716, commit 75db227b5a; W0-e fix 全史 close]): **W0-e 全史 T1/T2 遡及 count 完了。**
  - **T1 (St1a) = 0 triggering** — W0-e の scene/global param (LIFT_M :3642 / CLIP2_Y :3688 / CLIP_X :3645 / CLIP_Y :3646) は全て env-override 1 発 = ≈0 gap。→ **HOLD St1a**（D-1 どおり ROI≈0、%12 read と一致）。
  - **T2 (St2 / derived-source) = W0-e 1 / 累計 2** — ⚠ %12 provisional read「0/2 = 全 fix 座標編集」は **F-1a-v2 を見落とし**。F-1a (C1-seat X-follow, test_newton_clip_routing.py:4224-4277) は **runtime cable-DERIVED comp** (`-(1-λ)·_dx0`, _dx0 = 実行時 crossing 実測 :4234/4240) + **leg-adding** (2 lift/3 shift/trim/8 descent) = 純座標編集ではなく **St2 derived-source class**（07-03 scoping STEPTABLE_SCOPING_COORD2.md:52/:69/:81 の caveat-a/fix-⑤/argmin と同族の新規メンバー）。W0-e 追加 derived-source = F-1a 1 件。**累計 = fix-⑤ (07-03, ~1.5h 実測, :3870) + F-1a (W0-e) = 2 → St2「≥2 累計」gate 到達。**
  - **scope caveat:** %12 の count 指示は「W0-e 全史」(→ F-1a 1 件)、gate 文言は「累計」(→ +fix-⑤ = 2)。counting scope (W0-e-only vs 設計全史累計) は Rs 判断事項。
  - **番人 verdict:** **St1a = HOLD 継続**（明確、T1=0 / ROI≈0）。**St2 = evidence gate が累計で到達 → "build" ではなく "Rs-decision-ready 提案" に status 昇格**（St2 は L3 + Rs explicit auth・DEFERRED のまま; 実 build 判断は Rs 専権。gate 到達 ≠ build 承認）。%12 へ 1 行 verdict 返送済。

- 2026-07-06 08:09 (**%12 §運用28 照合 ACCEPT** — 貴 count confirmed): %12 が code 独立検証 (test:4234-4240 `_dx0=_cx0-x_clip`, `comp=-(1-λ)dx0` = `_w0e_guarded_cx` runtime 実測由来 = 静的 row 表現不能 = DESIGN_V1.md:147 St2 class) → **T2 = 2 (fix-⑤ + F-1a) gate 到達を ACCEPT**、counting scope = **累計で確定** (St2 行が fix-⑤ を名指しゆえ自然)、Rs 向け 1 行案採用 (%12 が本 turn Rs 提示)。
  - **factual refinement (%12, 記録整合):** round-2 grid の active 実行系 = **v1 flat comp** (leg-diff 全 cell SAME-STRUCTURE → v2 lift/shift/trim = default-OFF 実効; code 上 v2 leg-adding は初期 guarded 測定 PASS gated, test:4235-4237 REJECT→fallback)。**St2-classification の basis = cable-derived comp (`-(1-λ)dx0`, v1 flat / v2 不問で present) ゆえ T2=1(W0-e)/累計2 は v1/v2 refinement に不変** (leg-adding は 2 次記述、count の根拠にあらず)。
  - **status 確定:** St2 = **Rs-decision-ready** (gate 到達確定; 実 build = L3 + Rs explicit auth 維持・deferred)。**番人 台帳運用 初回発火 = 完了。** 次アクション = Rs の St2 判断 or 次 trigger 発生。

- 2026-07-06 08:4x (PLAN-KEEPER p6、%12 反映依頼 08:46): **⭐Rs St2 判断 = 「可」(08:3x、active-node state.md 記録 `eba71929b3`) → status = DESIGN-APPROVED → BUILD-AUTHORIZED (paper 先行) に現行化。** 上記「Rs-decision-ready」への Rs 回答 = 本決定。順序 = φ10 追撃 / DC-1 kickoff の後 (locked runner 衝突回避)、**p5 の設計 paper 先行 = 即時 GO**。全 charter に env pin `W0E_F1B_SNAPDOWN=1` 明記 (08:2x addendum 運用)。台帳の St2 行現況の更新 = p5 (番人) 管轄。
