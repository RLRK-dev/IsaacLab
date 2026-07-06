# Rs W0-a′ 決定 packet — P2 whole-route env + BC+RL LADDER v2 (1 回決定型)

**Status: v1.1 (2026-07-06 10:2x、W0-e close 反映)。** v1.0 ERRATUM (J-9: A1 分子 C1-leg 欠落 → 真 SR 0.494) は **W0-e chain で RESOLVED**: Rs「A」修正授権 → 修正 3 世代 (offset-follow → 150mm+lift-raise → F-1b″ snap-down) → **公式 strict_v2 = 58/81 = 0.716 [0.610, 0.803] (two-key、predicate-complete 分子 = C1 保持 ∧ C2 honest 着座、§運用29 準拠)** → Rs「A」10:0x で W0-e CLOSED (φ10 = characterized residual park)。v1.0 全文 = git 履歴 (75db227b5a 以前)。
**Author:** %12 RS-TECH-LEAD。**定義元:** spec §9-3 v1.5 (`P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md:115`)。
**Grounding:** LEDGER `BC+RL LADDER v2` 行 (W0-e close 反映済) / devplan v1.1 / spec v1.5 + artifacts v1.3 / W0-e: `RS_W0E_PACKET_V1_2.md` + PREREG 3 本 (band probes / dy-arc Stage-A / H-drape) + 二鍵 bank (75db227b5a, b7e5ec65c0) / 5体 DECIDE / %9 台帳。
**使い方 (Rs):** §1→§8 を上から順に。**全て Rs 専権事項 (env/reward/DR/UNIT) — 承認まで build なし。**

---

## §0. 決定リスト一覧 (v1.1 現況)

**承認の総体 (s1):** 本 packet の承認 = **spec v1.5 + artifacts v1.3 を P2 設計基底として採択し、§8 の staged build charter 発行を授権する** こと。

| # | 決定 | 種別 | 節 | v1.1 状態 |
|---|---|---|---|---|
| P | premise 再確認 (経路全体 1-unit) | 前提 | §1 | **Rs-PENDING** |
| DC-1 | branch α vs β | UNIT/algo | §3 | ✅ **DECIDED = α (Rs 07-06 08:3x「2:推奨」、state.md eba71929b3)** |
| DC-1s3 | α sub: **6D vs 12D** | contract | §3 | **Rs-PENDING (推奨 = α-6D)** — 08:3x 決定は α 本体のみ、sub は未提示だった |
| DC-2 | R3 既定 algo (RLPD 案) | algo | §3 | **Rs-PENDING** |
| DC-3 | AR-extend 却下 → NEW env 建設 | env | §3 | **Rs-PENDING** |
| Q1-Q11 | named-design-Q 10 項 + confirm-only 3 件 | env/reward | §4 | **Rs-PENDING** |
| T1-T3 | §4.3 数値閾値 3 pin | gate | §5 | **Rs-PENDING (T3 baseline = 0.716 に更新)** |
| P4 | credit/訓練 pre-registration 5 項 | 訓練 | §6 | **Rs-PENDING** |
| L | L-TRIAGE L2 降格 confirm | 手続 | §7 | **Rs-PENDING** |

---

## §1. premise 再確認 (1 行)

**「route 全体を 1 unit として学習する」方針を、新証拠 (R0/R1 = pure-BC/模倣系 4 path plateau + β-mix instrument 不成立 [R1 CLOSE c1-c4] + 文献では stage 分解 + 局所 RL + 高位 recovery が勝ち筋 [devplan:81、公開事例ゼロ]) の下で再確認いただく。** 変更する場合 = premise change → §3 以降は再構成 (stage 分解案 = devplan:159 (d)、STOP-and-flag)。**推奨 = 維持** (LADDER v2 は 1-unit のまま R2 で局所 RL 相当を branch 内に内蔵済み)。W0-e の追加傍証: script 側の決定論的欠陥は幾何修正で回収できる (0.494→0.716) = 「frozen script base + 小学習部品」through-line は生きている。

## §2. 実測 evidence base (v1.1 = W0-e close 後の確定値)

- **公式 SR = strict_v2 58/81 = 0.716、Wilson95 [0.610, 0.803]** (two-key EXACT、bank `75db227b5a`; 分子 = C1 保持 [z∧flank] ∧ C2 honest 着座 ∧ SUCCESS verdict = **predicate-complete、J-9 教訓反映済**)。any-seat 相当 (regrasp_ok) = 77/81。**系譜: 0.494 (J-9 真値、75mm) → 0.531 (round-1、150mm+lift-raise) → 0.716 (round-2、+snap-down)**。geometry = **150mm spacing (CLIP2_Y=0.000、Rs 07-05 指示) + LIFT_M 0.08** — v1.0 の 75mm 時代の数値 (0.728/0.494) は旧 geometry として retire。
- **evidence-gate 判定 (J1 更新): 点推定 0.716 = ≤80% 枝 → α-DR は (d) position-DR で開始可** (CI 上端 0.803 が 0.80 を僅か跨ぐ事実は v1.0 同様併記)。≥95% 枝の決定的棄却 = 不変 (むしろ強化)。**方向 tag: conservative-definite** (two-key + 54-cell bit-identity + probe byte 再現で over-state 経路なし)。
- **⭐ 失敗構造 (v1.0 J-8 を supersede — W0-e で機構レベルまで確定)**: fail 23 = **(A) φ10 21 cell = H-drape SETTLE-BASIN** (settle 時に cable が C2 clip 構造へ drape する [crossing 848、61/62 で clip-top node 直接確認] か床へ落ちる [829.3 = floor-rest 829.0 EXACT] かの離散二値。crossing x は三峰 {0.32 R_MISS / 0.368 floor / 0.380 clip} + 空白帯 = **座標 comp で連続 steering 不可**。二鍵 `b7e5ec65c0`、O-D producer 実測 58/23 = strict と完全一致) + **(B) φ0 legacy 2 cell** (x15_y15/x20_y15、際どい seat-depth 系)。**C1 leg = 81/81 完治** (旧主因は解消済)。
- **α residual への設計含意 (J-8 の z-gap sizing を置換)**: (i) **(ii) 局所 RL 発見の corner 標的 = φ10 class が機構既知で存在** — honest-F 13 cell の crossing-x gap = **閾値 x* まで ~0-3mm / clip-basin 帯 (0.379) まで ~9-14mm** (基準 2 種併記、%9 #5; いずれも authority 22mm 内) で、per-step residual Δ が basin flip を試せる自然な発見対象。(ii) **R_MISS 型 6 cell は gap +39〜51mm** — Δ bound が cover しない場合 **draw 会計 fallback の第一候補** (v1.0 の「EMPTY provisional + fallback 規則」は維持、候補が具体化した)。(iii) c2 Δ bound は drape-basin 幾何 (crossing gap 分布) で size する — 旧 z_gap 分布 (75mm 幾何) は annex 化。
- **horizon: 900 確定を新 geometry で再検証** — round-2 grid 実測 max = 771 RL 相当 step (7710 sim-frames、tied ≥5 cells [e.g. x15_y-20]) < 810、bump 非発動 (%12 再導出 + %9 EXACT)。
- **dual-grip span: 92.42mm 定数を新 geometry で再検証** — 81 cell × dual-grip phase **{1-7, 13, 14}** で [92.38, 92.42]、phase-13 は 81 cell 全て 92.42 定数 = **INV#2 運用裏付け不変** (%12 再導出 + %9 独立再計算 EXACT)。(注: 再把持 phase 10-12 は transition/choreography [%9 実測 phase 12 = 最大 127.10] であり span 不変量の対象外 — %9 cross-PV #1 で window 訂正済。)
- device 条件・sha-epoch 注記 = v1.0 から不変 (cuda:0 条件付き決定論 / GPU1 = 独立 workload 専用)。round-2 で追加裏書き: 54-cell bit-identity + probe npz byte 再現 (生産 ≡ probe)。
- **decision-of-record**: W0-e = `RS_W0E_PACKET_V1_2.md` + node state.md 07-06 entries / H-drape = `w0e_phi10_arc_probe/PREREG_HDRAPE_ROUND.md` + 二鍵 / 旧 P3-grid = `P3_GRID_JOINTREAD_20260705.md` (75mm 幾何の historical evidence として annex)。

## §3. D-C: branch 決定 + R3 + AR-extend + supersession 義務

**DC-1 = ✅ DECIDED α (residual-on-frozen-script、Rs 07-06 08:3x)。** 対称必須機構 (α = 3 点: (i) oracle drift-recovery relabel / (ii) structured-common-mode 局所 RL 発見 / (iii) 発見不能域 = draw 会計; trainer = 交互 aux imitation update) は spec v1.5 のまま。β 行 = fallback menu 残置 (trigger: α discharge FAIL at P4)。
- **banking 義務 (devplan:236) = ✅ 執行済 (10:1x、LEDGER 行 `7d5907b44c`)**: α 採択に伴う DQ1=B→A′ supersession 正式行。決定 08:3x に対し発行遅延 = %12 見落とし、%9 cross-PV #2 が「今 due (承認時 defer は DC-1 DECIDED と不整合)」と捕捉 → 即時執行 + 行内に正直注記。
- **DC-1s3 (Rs-PENDING): residual contract = α-6D (position-only) vs α-12D (rot 込み)。推奨 = α-6D** — HIGH5 (rot 6D near-inert + demo rot-delta ≈0 [実測 per-step ≈0.13-0.16°、whole ≤0.41°]) を moot 化、G7 = base-ori 依存として明示。α-12D 選択 = HIGH5 再輸入 + Q4 再検討が連動 live 化。
- **共通 comparator pre-register (いま pin、v1.0 不変)**: from-P0 SR / identical winnable-support / matched GPU budget / same env sha + cuda:0 + same seed/DR stream / per-class 内訳 / 併用時 order-confound 明記 — N≥30 + nomA/nomB band + %12+%9 joint verdict。**v1.1 追記: per-class 内訳に φ10 class 列を常設** (characterized residual の吸収率が residual RL の看板指標になる)。

**DC-2: R3 既定 = RLPD (+ IBRL 型 proposal は BC-proposal fallback 併設で caveat 運用) + horizon 対策 arm ≥1。Cal-QL/WSRL = 条件付き (devplan:208)。** grid 非依存 — 本 packet で確定可。

**DC-3: AR-extend 却下 → NEW route env 建設 (NHA-3 disposition)**: AR は frozen-L contract / mid-air reset / dense reward / MAX200 / row56 regression surface が whole-route 要件と非互換 → NEW。実 reuse = base 2109 行は共通 (spec:115)。cost = spec §7 (staged per-component L3 chain ≤800 行/diff)。

## §4. named-design-Q 10 項 (v1.1 差分は Q2/Q5/Q7 のみ、他は v1.0 のまま)

| # | Q | 選択肢 | 推奨 (根拠) |
|---|---|---|---|
| Q1 α-PC | base clock と policy 逸脱の re-sync 規約 | (a) 無条件 march / (b) 逸脱>閾値で base pause + oracle 再照会 / (c) predicate 到達で advance | **(b) 系** (B1 型 desync 回避、spec:29) |
| Q2 α-DR | α の学習信号源 | (a) 摂動注入 / (b) obs-noise / (c) retention margin / (d) position-DR-only | **(d) position-DR で開始 = evidence-gate 実測 (0.716 = ≤80% 枝、判定不変)**。(a)/(b) = robustness OPTION retained |
| Q3 Q7 承継 | inter-arm collision | re-enable + penalty / reach-terminate のみ | **reach-terminate + 実 wrist proxy 監視** (spec:59; memory dualarm-collision) — Rs 確定要 |
| Q4 HIGH4 | success の seat-ori 節 | 含める / 外す | **外す** (G7 解決まで; α-12D 選択時のみ再検討 live — DC-1s3 連動) |
| Q5 horizon | RL horizon | 900 | **900 確定 — 新 geometry で再検証済** (round-2 実測 max 771 < 810、§2) |
| Q6 OG band | band α/β/γ | provisional / 再較正 | **provisional 明記のまま採用 → OG port+再検証後に再 pin = 1 決定に統合** |
| Q7 draw 方針 | 不可勝 cell の扱い | truncate-無-penalty / **DR-support 除外 + 文書化** | **DR-support 除外**。cell list = **EMPTY (provisional) を維持、ただし v1.1 で候補具体化: R_MISS 型 φ10 6 cell (drape-gap +39〜51mm) は Δ bound が cover しなければ draw 会計へ復帰** — 判定は P4 pre-reg の Δ bound discharge 時に機械適用 (§2)。honest-F 13 cell は winnable 扱い (crossing-x gap: x* まで ~0-3mm / basin 帯まで ~9-14mm = 発見対象、§2 基準併記) |
| Q8 obs v2.1 | 53D / 57D | — | **57D** ([53:55] contact + [55:57] IK-resid、§運用21 整合) |
| Q9 counting | SR 計数規則 | — | **confirm のみ: strict_v2 predicate-complete 分子 (C1 保持 ∧ C2 honest 着座) を P2 でも PRIMARY に承継** (J-9 教訓、§運用29) |
| Q10 span tier | span-guard window | informative 既定 / hard | **informative 既定を維持** — window = 92.42mm 定数 (新 geometry 再検証済、§2) で pin |
| Q11 confirm 群 | confirm-only 3 件 (①explosion terminate obs 非対応 rationale ②sustain-counter obs 化不要 ③oracle mid-servo label 規約) | confirm / 差戻し | **3 件とも confirm 推奨** (v1.0 不変) |

## §5. §4.3 数値閾値 3 pin (draft 値 — 本 packet で Rs 確定、確定まで HIGH-COST-GATE は GO を出さない)

1. **abort**: post_base_drop >0.20 が 2 連続 eval OR OG restoring legs 3 checkpoint 連続 monotone 悪化。
2. **actor-gate (R3)**: Q_rank_error <0.10。
3. **R2b PASS bar (v1.1 更新)**: DR±20mm in-sim category-SUCCESS **≥70%** (N≥30、band 分離) かつ script-under-DR baseline = **strict_v2 0.716 [0.610, 0.803] (W0-e 公式、150mm geometry)** を band 超えで上回る。**注: baseline の分子は strict_v2 (predicate-complete) — 学習側の成功判定も同一分子で計測 (分子非対称の禁止)。**

## §6. P4 credit/訓練 pre-registration (提案値入り)

| 項 | 提案値 | 根拠 |
|---|---|---|
| γ | **0.997** | 1/(1−γ)=333 vs horizon 900; smoke で再検証 |
| GAE λ | **0.95** | RSL-RL 標準 |
| envs×steps | **smoke 実測で確定** (仮 pin = throughput ≥9.7fps から逆算) | spec §4 DoD |
| corner-episodes | **≥8 /update、うち φ10 class を明示比率で含める (提案 ≥4)** | (ii) 発見標的が機構既知で存在する初の状態 (§2)。Δ bound discharge = P4 pre-reg 時に drape-basin 幾何 (crossing gap 分布) を入力に機械判定 — R_MISS 6 の draw 復帰判定も同時 (Q7) |
| λ_relabel / anchor decay (α のみ) | **λ_relabel = 別 buffer 交互 update 比率 1:4 案 / anchor decay = corner-mask + 線形 decay 案** | CC2-CH2/CH3 fix; ablation 予約 |

## §7. L-TRIAGE 降格 confirm

design-gate chain 完走実績 (5体 ×2 + pre-check 3-entry + %9 台帳) = v1.0 不変。W0-e chain の追加 gate 実績 (PREREG 封緘 ×3 + 二鍵 ×4 + Rs 動画 gate) も本 packet の evidence 品質を裏書き。build 段 = staged per-component charter (各 ≤800 行、個別 L3) 前提のため **packet 承認自体 = L2 扱いを confirm** (未 confirm = 層5 再実施)。

## §8. 承認後の即時 banking + 次工程 (Rs 承認と同 turn で %12 実施)

1. `BC+RL LADDER v2` 行の Rs-PENDING → DECIDED 分離解消 (DQ1 supersession 行は ✅ 10:1x 発行済 `7d5907b44c`)。
2. node state.md + 地図 (p6) + manifest §2 再生成 (確定事項の即反映 gate)。
3. staged build charter 発行順: **env-core → route-executor 抽出 → oracle → OG port → trainer** (spec §7、各個別 L3 chain)。env-core charter には W0-e 産の運用 pin (env `W0E_F1B_SNAPDOWN=1` = 0.716 再現条件 / cuda:0 canonical) を継承。
4. P4 の smoke-確定項 (envs×steps) は env-core smoke 完了時に再提示。φ10 Δ bound discharge + draw 判定 = P4 pre-reg 時。

---
*v1.0: 07-05 14:37 %9 content PV PASS → 15:0x ERRATUM/HELD (J-9)。v1.1: 07-06 10:2x %12 起草 (W0-e close 反映: 公式 0.716 / 失敗構造 supersede / horizon+span 新 geometry 再検証 / DC-1 DECIDED 化 + DC-1s3 分離 / T3 baseline 更新 / Q7 draw 候補具体化 / DQ1 banking 義務 surface) — %9 cross-PV = CONCUR-WITH-CORRECTIONS 10:10 (台帳 `W0APRIME_PACKET_V1_1_CROSSPV_PCT9.md`)、corrections 1-5 全反映 10:1x → **v1.1 final、Rs 提示可**。*
