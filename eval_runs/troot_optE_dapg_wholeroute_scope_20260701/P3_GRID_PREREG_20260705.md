# P3-grid 前倒し実行 — PRE-REGISTRATION (データ取得前に確定、g2)

**Authority:** %12+%9 JOINT 2026-07-05 10:59 (g1-g4; 3 者収束 = env-spec 5体 NHA-b + CC4-3 + CC2-c1) / Rs loud-notify = 10:54 report(「止める場合は一言」) + 本 turn 再通知。two-key = 本 joint + %12 charter verify。script-only (policy rollout でない) = rollout HALT 非抵触。cost ~5.2h (81×15.5min/4-way) < HIGH-COST 10h。
**目的:** Rs W0-a′ packet を evidence 付き 1 回決定可能にする — D-C decider (SR@DR) + c1 (corner-miss magnitude) + span window 導出 + draw-class 分類 + horizon 分布を 1 batch で供給。

## 1. Grid 定義
- offsets = X×Y ∈ {−20,−15,−10,−5,0,+5,+10,+15,+20}² mm = **81 cells** (5mm pitch)。
- 実行 = canonical route script (`test_newton_clip_routing.py --solver-backend mujoco`) + `CABLE_XY_OFFSET` per cell。**cuda:0 + MUJOCO_GL=egl + headless** (device-fragile pin + BadWindow 回避)。4-way 並列 wave (CP-C 実績方式)。
- validity filter = CP-C 準拠 (seat 検収 + R_MISS 分類) + **guards-quiet 期待** (canonical-valid 軌道で guard 相当条件の fire を記録 — env 未在のため log 上の等価量)。

## 2. Counting rule (pinned — 事後変更禁止)
- **per-offset unique** 計数。決定論的 re-run = 1 offset。
- SR 分母 = **winnable-support cells** (draw-class 除外を両枝同一適用)。**≥95% 枝の certify には n_winnable ≥ 59 が必要** (rule-of-3: (0.95)^n ≤ 0.05 → n ≥ 58.4; %9 独立再計算一致)。81 − 予想 draw 数点 > 59 ✓。Wilson 95% CI を併記。
- evidence-gate 閾値 (spec §2 既 pin): SR ≥95% → M-C bites → α-DR = (a) 摂動注入 or (b) obs-noise 必須 / ≤80% → (d) position-DR + c2-sized で開始可 / 中間 → Rs 判断。
- **AMENDMENT A1 (2026-07-05 11:21 JST, pre-data — 77/81 cell 未実施時点で追記; two-key = %12 提案 11:19 + %9 CO-SIGN 11:20):** SR **numerator** pin — **PRIMARY = strict (verdict=SUCCESS* ∧ c2_seated_honest=True)** / SECONDARY (diagnostic) = SUCCESS any-seat。根拠 = task product-predicate は seat を含む (spec §2 G6 / T_SEAT; producer 定義 = test_newton_clip_routing.py:4756 c2_wall_dist≤0.5 ∧ c2_in_groove) — predicate 由来の導出であり grid data の覗き見でない (materiality 参照 = PRIOR data CP-C のみ: any-seat 16/17 vs strict 14/17)。**rider 1 (%9):** any-seat∧¬strict class (= delivery-ok/seat-miss) を **per-cell 明示報告** — この class は seat-margin 学習信号カテゴリ + c1 corner-miss forensics の seat 側入力で、aggregate のみだと消える。runner 出力は verdict/seated 別列で既に適合 (runner 変更なし、読み方の pin)。

## 3. Draw-class 分類 = 2 段手続き
1. task-level FAIL cell 抽出 → per-cell forensics (miss magnitude / 幾何: bow-chord vs span 窓 / R_MISS vs seat-miss 分類)。
2. c1 (miss 分布) → p_hit model (σ_common-mode, W, window) → **discovery-feasibility 境界**で corner (学習対象) / draw (不可勝: 幾何 infeasible OR p_hit < floor [提案 floor: E[discoveries/update] ≥ 1]) を線引き。draw = policy 非依存 (script 幾何由来) を per-cell 根拠で明記。

## 4. 導出物と供給先 (列挙 — 事後解釈余地ゼロ化)
| 産出 | 供給先 |
|---|---|
| per-offset SR (winnable 分母) | D-C evidence-gate (spec §2) + Rs packet |
| corner-miss magnitude 分布 | c1 → c2 Δ bound 導出 + p_hit 計算 (CC2-CRIT discharge) |
| dual-grip phase span 分布 | G1 window + span-guard window 導出 ([p1,p99]±margin; **tier = informative 既定** per banked ruling — hard 化は design-gate) |
| episode 長分布 (n=81) | horizon p99 検証 (900 bump 規則; n<100 につき max-of-n 保守注記) |
| draw-class cell list + 根拠 | DR-support 定義 + SR 上限 + 両枝共通 comparator support |
| verdict JSON + npz (全 run 保存、~1GB 可) | corner forensics + 将来 curriculum state-bank 種 |

## 5. 実行規律
- wave-granular early-abort (wave 内 ≥50% 想定外 FAIL or NaN/explosion cluster → STOP → %12)。
- 0-commit (結果 dir のみ)。検収 = %9 (unique-offset 再計数 + counting 準拠) → %12+%9 joint read → packet fold。
- conservatism: script grid = α の base 挙動そのもの / β には「script が解ける support」の上界情報 (β の from-P0 SR ではない) — 方向明記。

*%12 起草 10:5x-11:0x、%9 g2 条件準拠。0-commit (P3-grid 完了時に結果と同 commit)。*
