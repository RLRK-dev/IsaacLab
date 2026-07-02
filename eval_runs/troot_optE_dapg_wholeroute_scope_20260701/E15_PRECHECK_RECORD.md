# E15 (fork-(iv)) /pre-check R1+R2 記録 (2026-07-02、durable copy)

⚠ 注意: 同 dir の `B_EVALUATOR_PRECHECK.md` / `_R2.md` は**旧 B-evaluator gate (E1-E11 期)** の記録であり本 gate とは別物。E15 の pre-check 正本 = 本 file + `logs/pre-check-log.jsonl` (repo root、末尾 2 entry) + spec §10 E15 header の版歴。

## R1 (対象 = E15 v2) — **BLOCK** (CRIT 1 / HIGH 1 / MED 3)

- **CRIT**: 旧 OG-b「β≈1 → STOP」は構造欠陥。obs layout に progress clock が無く、GRASP_HOVER は corr(wp_Rz, ee_Rz)=1.0000 (verifier 実測) — **OG-a を通る正しい policy も data-forced β≈1** → 全健全 policy を偽 STOP する protocol deadlock。collinear seg channel (corr 0.9996) に credit が逃げた場合のみ偽 GO = 排除対象の構成を選択する gate だった。verifier 結論:「CRITICAL は判別器にあり、fork 方向にはない」。
- HIGH: OG-a p95>5mm STOP が unscoped — HOVER の 471mm box (392.4mm range ×1.2) で健全 policy が偽 STOP。
- MED×3: ±10mm probe が clamp と干渉し偽低 β / P1 FAIL が fork 反証と cuda:0 reach-wall class を混同 / P2 bar が最尤解 (γ∥≈1 sawtooth) を誤 FAIL する誤較正。
- 処置 → **v2.1**: OG-b = co-moving (ee+seg) 摂動 + tangent/transverse 分解 (γ∥≈1 benign、gate = verdict-critical γ⊥ ≤0.5 GO / ≥0.9 STOP / 中間 BLOCKED) + OG-b′ 閉ループ収縮 probe + OG-c 回帰化 + phase-scoped bar + two-scale probe + P1 帰属判別 + P2a/P2b 分割。

## R2 (対象 = v2.1) — **WARN → v2.2 で CLOSED**

- Issues 1/2/3/5 = RESOLVED、Issue 4 = PARTIALLY (catch-all 欠け)。新規 = definition pin 4 + 文言 2 (設計変更なし):
  1. OG-b tangent = **per-step** `t̂[t]=normalize(wp[t+1]−wp[t])` (C2_REGRASP は実測 80.1° 屈曲 — per-phase 単一方向は γ∥ 漏れ)。**dwell cell (C1_PIN / C2_SETTLE = wp range 0.0mm) は γ⊥ := 総 gain γ** (healthy ≈ 0 = 最清浄な integrator 検出器)。
  2. OG-a 中間帯 (GO/STOP 非該当) = BLOCKED_FOR_USER。P4 anomaly 框付けは **δ ≤ 1mm 条件付き** (δ≥1.18mm では fire = EXPECTED 側)。
  3. OG-b′ metric = moving phase は demo path への transverse 距離 / dwell は固定点距離。**OG-b vs OG-b′ 不一致 = any-STOP-wins** (fail-closed)。
  4. P1 分類不能 FAIL (resid 30-50mm 帯 / ≥50 非単調 / <30 単調 / IK-spike 無し) = **BLOCKED_FOR_USER + banking 禁止 + 両系列 Rs 提出**。
  - 文言訂正: guard-2 引用 norm を per-arm (R 8.53 / L 11.39mm、headroom 3.61mm) に / guard-1「seat 系で常時発火」→ 低 range 軸のみ (C2_DUAL_SEAT z 38.3mm box は非発火)。
- R2 の整合 verify: P4 1.68±δ ↔ E14 ✓ / decode 式 ×(hi−lo)/2 + 30mm 床 → 0.3mm ✓ / P3 span 95.2mm = B0a 実値 (B1 resid 95.2mm との数値一致は偶然と確認済) ✓ / probe scale 階層 (jitter±1 < ±2 < ±5 < ±10mm) ✓。

## 最終判定

**v2.2 = CLOSED → B1′ charter 発行可** (Rs 標準指示「pre-check が通ったら %11 に B1′ charter まで進めて」+ WARN=fix-closed disposition [B-evaluator gate の BLOCK→errata→closed と同型])。
