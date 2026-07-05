# Rs packet v1.2 — W0-e round-2 (F-1b″ snap-down) 公式成績 + 決定事項

**From:** %12 RS-TECH-LEAD + %9 OPS-SUP (two-key) + %11 COORD (実行)。**Date:** 2026-07-06 08:0x。
**位置:** packet v1.1 (43/81) → Rs「a commit」= F-1b 帯 150mm 再導出 → 帯 probe verdict B (φ5 snap-down 3/3) → Rs「進めて」→ F-1b″ build + 81 再走 → **本 packet = round-2 公式成績**。

## 1. 公式 SR (strict_v2、two-key EXACT)

- **strict_v2 = 58/81 = 0.716、Wilson95 [0.610, 0.803]** — 私鍵 (recount_strict_v2.py) + %9 鍵 (parser v2.1 sha 170de62e) 全 field EXACT、[FLANK-FALLBACK npz] loud 両表示。
- **SR 系譜: 0.494 (J-9 真値、75mm) → 0.531 (round-1、150mm+lift-raise) → 0.716 (round-2、+snap-down)**。
- 受入 gate 全 PASS: C-0 nominal sha EXACT (`5f1c3f92…`、三者独立) / **54-cell bit-identity 54/54 MATCH**(snap-down は φ5 27 cell のみに外科的作用、確証) / wall-bar 違反 0 / 0 abort / determinism 違反 0。

## 2. 効果の質 (paired 分析)

| 指標 | 値 | 意味 |
|---|---|---|
| φ5 列 (狙った 27 cell) | **F→P 15 / P→F 0** | 27/27 全 PASS 化、**後退ゼロ** |
| 事前算術 | 43+15 = **58 EXACT** | PREREG 予測どおり |
| C1 保持 leg | **81/81 継続** | lift-raise の完治が維持 |
| probe 再現性 | P1/P4/P5 npz **byte-MATCH** | 生産 build ≡ probe 軌道 (bit 再現) |

## 3. 残余 23 failure (機械同定済)

- **φ10 21 cell** (dy∈{−20,−5,+10} × dx≥−10 の 3列×7): 既知別機構 — snap-up は probe 1/3 で非採択、fall-through 挙動のまま。判別変数 = dy 自体 (arc 配置)。R_MISS 残 4 は全てここ。
- **φ0 legacy 2 cell** (x15_y15 / x20_y15): round-1 から不変の隅 class (際どい seat depth 系)。
- anomaly annotate 1: 旧 (−20,+20) HIGH-crossZ R_MISS が Δ−5 で heal — crossZ = necessary-not-sufficient の追加例 (機構 item 維持)。

## 4. Rs 決定事項

- **(1) F-1b″ snap-down diff の正式 commit** (locked runner、現在 uncommitted; 検証 = 本 grid + 54-cell bit-identity + probe byte 再現) — 承認を求む。
- **(2) φ10 21 cell の処置**: (a) 追撃 (dy-arc 機構の probe 設計、新 sub-arc) / (b) 0.716 で受容し DC-1 再決定へ (class は機械同定済、後日狙い撃ち可)。
- **(3) DC-1 (α residual vs β canonical) 再決定 context**: W0-a′ packet の評価依存項は本 0.716 を基準に更新可。

## 5. artifacts

- grid = `w0e_81rerun_snapdown_0537/` (immutable) / 私鍵 = `w0e_offline_validation/recount_w0e_81rerun_snapdown_0537.json` / %9 鍵 = `w0e_offline_validation/p9_recount_w0e_81rerun_snapdown_0537.txt` / PREREG = `w0e_f1b_150mm_rederive/PREREG_BAND_PROBES.md` (SEALED v2) / gates = `ROUND2_VALIDITY_GATES.md`。
