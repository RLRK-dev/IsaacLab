# F-1b dy 帯 150mm 再導出 — 帯縁 probe PREREG (two-key 封緘、%9 起草 → %12 countersign 待ち)

- **起草: %9 OPS-SUP 2026-07-06 05:0x JST** — Rs lever (a) 決定「a commit」(04:57) を受領。two-key 標準形 step 1 (PREREG first、bars + consequence mapping = pre-data 固定)。
- **substrate**: runner commit `8185b2561f` (Rs 承認 landing、F-1b = :3952-3967) / 150mm+lift-raise geometry (RUN1_REFERENCE_V2 = `5f1c3f92…`) / device cuda:0 固定 / 世代 tag dir + immutable-until-joint-read-close。
- **仮説 (81-run data 由来、packet v1.1 §3)**: 150mm では C2-regrasp は **格子整合 phase (φ=0) を好む** — dy 列 {0,±15} (φ0) ≈ 全 PASS vs {±5,±10,±20} (φ5/φ10) に失敗集中。旧 B1 目標 7.5 (mid-node、75mm C1-escape 帯からの退避) は 150mm では**逆効果候補** (7.5 退避後の cell が現に FAIL)。**再導出仮説 H-lattice: dy_target = nearest lattice (φ→0/15)、Δ = −φ (φ≤7.5) / +(15−φ) (φ>7.5)、全対象で |Δ|=5 ≤ 実証済範囲 7.5**。
- **C1 安全性の前提根拠**: φ0 目標 = 旧 75mm の escape 縞 phase だが、150mm+lift-raise では φ0 列 (dy 0/±15) 含め **C1-retained 81/81** (81-run two-key) → φ0 retreat は C1-safe と予測。ただし下記 (i) で cell 毎に強制検証 (predicate 完全性: C1 leg を落とさない)。

## Probe set (6 + control 1; paired 設計 — baseline = w0e_81rerun_0211 の同 cell 実測)

| # | cell (dx,dy) | φ | Δy_grasp | baseline (81-run) | H-lattice 予測 | H-persist 予測 |
|---|---|---|---|---|---|---|
| P-1′ | (0, +5) | 5 | **−5** | R_MISS, crossZ 825.6, crossX 0.317 | crossZ ≥840 ∧ C2 PASS | ≈baseline (LOW/MISS) |
| P-2′ | (0, −5) | 10 | **+5** | honest-F z_c2 894.2, crossZ 830.9 | 同上 | ≈baseline |
| P-3′ | (5, +10) | 10 | **+5** | honest-F z_c2 882.8, crossZ 830.6 | 同上 | ≈baseline |
| P-4′ | (0, −10) | 5 | **−5** | honest-F z_c2 875.0, crossZ 825.5 | 同上 | ≈baseline |
| P-5′ | (0, +20) | 5 | **−5** | R_MISS, crossZ 825.8, crossX 0.319 | 同上 | ≈baseline |
| P-6′ | (20, −20) | 10 | **+5** | R_MISS, crossZ 828.3, crossX 0.315 | 同上 | ≈baseline |
| C-0 | (0, 0) nominal | 0 | (fire なし) | s2, sha 5f1c3f92 | **npz sha == 5f1c3f92 EXACT** | 同左 (必須 gate) |

- 選定根拠: 失敗 3 grade の代表 (R_MISS ×3 + honest-F 高所 ×3)、φ5/φ10 両方、dx 多様 (0/5/20)。Δ は全て nearest-lattice = ±5。
- 実装要件 (%11): dy_target 差替は **offset-gated + probe-env-gated** (例 W0E_F1B_TARGET_LATTICE=1) — C-0 nominal byte-id を破らないこと。Δ 適用 log 行 (`[W0E-F1B]`) の (dy, φ, Δ, GRASP_YC) を各 cell で emit (as-executed 照合用)。

## 読み列 (機械適用、開封前固定)

- **(i) C1-leg guard**: z_c1_final < 840 ∧ flank10 < 840 (strict_v2 C1 定義、flank = [FLANK-FALLBACK] npz 経路 loud)。
- **(ii) crossZ class** (v2.1 診断列): **HIGH = ≥ 840.0mm / LOW = < 840.0** (観測 cluster 分離: LOW max 831.3 vs HIGH min 846.7、840 = 物理境界 [low-wall top] 兼 mid-gap)。⚠ [835, 846.7) = 観測空白帯 — 着弾したら bar どおり分類 + anomaly 行 (annotate-not-reclassify)。
- **(iii) C2-leg**: verdict ∈ {SUCCESS_DUAL_LOADED_AT_88, SUCCESS_R_GRIP_L_CAGE_AT_88} ∧ c2_seated_honest。
- 診断列 (gate でない): z_c2 / crossX / pin node / R grip N / 床 bar (producer nonpin + 必要時 %9 method-1)。

## Consequence mapping (優先順位順、機械適用)

1. **D (C1 regression、最優先)**: いずれかの probe で (i) FAIL → **即 STOP + Rs escalate** (C1 全快 = banked 成果、再破壊は lever (a) の変種でなく前提違反)。
2. **A (adopt)**: D なし ∧ 6/6 で (iii) PASS ∧ (ii) HIGH → **H-lattice 採択** → %11 が F-1b′′ (150mm 帯規則 = 非格子 φ → nearest-lattice retreat) を build → 再 grid 81 で確定 (two-key)。
3. **B (partial)**: D なし ∧ (iii) PASS が 1-5/6 → **column/φ 毎の部分帯** — PASS した φ/列のみ採択候補、残余は Rs へ (失敗 cell の (ii)/(iii) 組を添付)。
4. **C (mechanism flag)**: (ii) HIGH ∧ (iii) FAIL が 2 cell 以上 → **crossZ 機構不十分** → 帯再導出を停止し joint 再分析 (crossZ を治しても C2 が治らない = 別 root)。
- C-0 gate: nominal sha ≠ 5f1c3f92 → **全 probe INVALID** (build が nominal を汚染、開封しない)。
- validity: finite ∧ qvel_ok 全 cell、violation は cell 単位 INVALID + loud。

## Predicate 完全性 (標準形 4 節)

本 mapping が conjoin する leg = C1 retention (i) ∧ C2 regrasp+seat (iii) ∧ validity。**cover しない leg** = 床/壁 bar (診断列のみ — lever (a) の対象外、re-grid 時に再評価) / R grip force の量 (verdict enum で代理) / GUIDE slip (F-2 領域、不変更)。scope: 本 probe は**帯規則の再導出のみ**を決める — 採択後の面の主張は再 grid 81 で行う (単点 PASS の過大一般化禁止、§運用30)。

## 封緘・交換手順

1. %12 countersign (本 doc 編集 or 承諾行追記) → 凍結 commit (%12)。
2. %11 実行 (7 run、tagged dir、immutable) → 完了通知。
3. SEALED 読み: %9 = v2.1 parser + 診断列 / %12 = 独立 recount — 交換後に mapping 機械適用 → joint verdict → Rs 報告。

## %12 COUNTERSIGN (2026-07-06 05:0x) + pre-data 修正 1 (mapping 完全性)

- **検証済**: H-lattice Δ 算術 6/6 整合 (floor_mod 込み再計算 EXACT) / crossZ bar 840 = cluster 空白帯の物理境界で妥当 / D>A>B>C 優先順・C-0 gate・predicate 節 = 標準形適合。
- **修正 1 (interpretation-restricting、未 mapping outcome の封鎖)**: **A′** = D なし ∧ (iii) 6/6 PASS だが (ii) HIGH が 6/6 でない → **採択 (A と同処置) + anomaly 行「crossZ 機構モデル不完全 — C2 が LOW crossing でも治った cell を列挙」**。目的変数は C2 healing であり crossZ は機構 probe — 治癒を機構モデルの都合で棄却しない。ただし機構理解の gap として joint 再分析 item に登録 (re-grid 前に closure 不要、annotate-not-reclassify)。
- 本 countersign をもって **SEALED** — 以後の変更は不可、%11 実行 → sealed 読み → 交換 → 機械適用。

## SEALED v2 (2026-07-06 05:0x — %9 完全性再点検 2 件、%12 confirm; read-side のみ、probe 実行に非干渉)

- **R (refute) 追加**: D なし ∧ (iii) 0/6 PASS → **H-lattice 棄却 + Rs 報告** (採択なし、joint 再分析)。全 (ii) LOW = clean 棄却 / (ii) HIGH 混在 = C flag 併記。
- **B ∧ C 優先解釈の明文化**: (iii) 1-5/6 で (ii) HIGH ∧ (iii) FAIL ≥2 が併存する場合 — **B の部分採択は維持** (治癒列の empirical heal は機構モデル非依存、A′ 哲学) + **C は全体停止でなく「crossZ 機構 gap」item として joint 再分析に登録**。C 単独での全体停止 = 部分採択が 1 列も無い場合のみ。
- 以上 2 件で outcome 空間は全列挙済 (D / A / A′ / B[+C-item] / R[+C-flag] / C-stop / C-0 INVALID / validity INVALID)。**SEALED v2 確定。**
