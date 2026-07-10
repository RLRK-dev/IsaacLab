---
doc_class: reference
---
> 📖 REFERENCE / HISTORICAL (as-of 2026-07-11, COORD2 vault-audit) — tracking SSOT = LEDGER VL3 (`00-DESIGN-STATUS-LEDGER.md`). optE-W0packet: W0-e CLOSED (LEDGER row47), decision-of-record historical. Do not copy live values — pointer task_config.py / successor docs.

# Rs packet v1.1 — W0-e 訂正後 grid 成績 (81 再走、two-key 確定)

**From:** %12 RS-TECH-LEAD + %9 OPS-SUP (two-key) + %11 COORD (実行)。**Date:** 2026-07-06 04:3x。
**位置:** J-9 (packet v1.0 ERRATUM、真 both-clip SR 40/81=0.494) → Rs「A」修正授権 → W0-e chain → **本 packet = 訂正後の公式成績**。

## 1. 公式 SR (strict_v2、§運用29 predicate-complete 分子: C1 保持 ∧ C2 honest 着座 ∧ SUCCESS verdict)

- **strict_v2 = 43/81 = 0.531、Wilson95 [0.423, 0.636]** — two-key (recount_strict_v2.py / p9 parser v2.1) 全 field EXACT 一致、[FLANK-FALLBACK] loud 両表示 (受入条件充足)。
- RUN-1 受入 = 三鍵 (grid 内 nominal npz sha == RUN1_REFERENCE_V2 `5f1c3f92…`)。0 abort / 81 finite / determinism 違反 0 / wall-bar 違反 **0** (旧 2)。
- 参考 (旧 grid、旧 geometry 75mm): 40/81 = 0.494 [0.388, 0.600]。

## 2. leg 分解 — 構造転換 (数字より重要)

| leg | 旧 grid (75mm) | 新 grid (150mm + 修正一式) | 変化 |
|---|---|---|---|
| **C1 保持 (z ∧ flank)** | 45/81 | **81/81 全快** | escape class 全滅。機構 = **LIFT_M +30mm の 1 座標** (Rs 口頭教示: かすり修正) — 発明動作なしで達成 |
| **C2 (re-grasp ∧ honest 着座)** | 59/81 | **43/81 後退** | 単一 root class (下記) — 全失敗がここに集中 |

## 3. C2 後退の機械同定 (%9 診断列、81 行)

- **root class = 「低位・大 bow の lane 交差」** (crossZ 823-831mm、n≈38) の 3 段階 outcome:
  - (a) **R_MISS 13** — R が低位交差点を掴み close 0N
  - (b) **把持成功だが C2 seat 未達 20** — z_c2 860-908 = cable が C2 溝に届かず (把持 arc ズレが seat 押下点を外す)
  - (c) lucky pass 5 (knife-edge、watch 指定)
- 別小 class: 際どい seat depth 3 cell (root 別)。
- **判別子 = crossZ (dx×dy 依存)**。pin 捕捉 node shift は PASS cell にも出る = 必要条件側 (単独判別子でない、%9 精密化)。**格子整合 dy {0,±15} 列 = ほぼ全 PASS / 非格子 dy {±5,±10,±20} 列に失敗集中** — F-1b の帯 (B1/B2) は旧 75mm geometry で pin したもので、**150mm では dy 帯構造の再導出が未実施** = 最有力の狙い撃ち対象。
- 転落/回復: PASS→FAIL 27 (非格子 dy × dx+10..+20 厚) / FAIL→PASS 11 (旧 escape 隣接 = lift-raise 回復)。

## 4. 正直な総括

- Rs 教示 (間隔×2 + lift+30) + step-table-faithful 修正で: **C1 問題は完治**、動作品質は Rs 動画 gate PASS、しかし **C2 leg は 150mm × 非格子 offset の arc 再配分で後退** — net +3 (0.494→0.531)。
- 旧 geometry の PREREG 識別区間 [0.728, ~0.95] は **geometry 変更 (Rs 指示) により annex** (annotate-not-reclassize、封緘規律どおり)。本結果は新 geometry の初回公式値。

## 5. Rs 判断 (次 lever、推奨順)

- **(a) 推奨: F-1b dy 帯の 150mm 再導出** — 旧 P-1..6 と同型の帯縁 probe (~6 本、GPU 数十分)。非格子 dy 列の失敗集中と直接対応、既存機構 (GRASP_YC 座標補正 = 表-faithful) の param 再較正のみで新動作不要。
- (b) 把持 arc-aware C2 seat 補正の設計 (新設計 = Rs 専権 scope、(a) の結果を見てから)。
- (c) 0.531 を受容して DC-1 再決定へ進む (class は機械同定済みのため、後日狙い撃ち可)。
- **commit 承認**: %11 の locked runner 編集 (F-legs + LIFT_M + producer fields、動画 gate + 81 再走で検証済) の explicit-path commit — Rs OK を求む。

## 6. artifacts

- grid = `w0e_81rerun_0211/` (immutable) / 私鍵 per-cell = `w0e_offline_validation/recount_w0e_81rerun_0211.json` / %9 診断列 = parser v2.1 出力 / class map + 転落 list = %9 04:26 dispatch (joint-read 記録) / 動画 = `~/Downloads/w0e_liftraise_*.mp4` (gate PASS 済 4 本)。
