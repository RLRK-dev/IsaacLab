# 深押込み disposition — pre-read classification pin (two-key 封緘、開封前固定)

- **封緘: 2026-07-05 19:0x JST** — %12 提案 (2 列分離) + %9 COUNTERSIGN (6-cell 完全性検証) + 精密化 2 点反映。
- **対象**: W0-e slow-seat 判別再走 (sf=8、2 offset cell) の読み。開封 = %11 rerun 完了時点、mapping は機械適用 (two-key 標準形: PREREG first / exchange-after-fixing)。
- **背景**: F-1a v2 smoke で offset cell の C1 seat が 827.4mm (床 undershoot −1.6mm、PREREG floor bar −1mm 超過)。pin が 38N 押圧状態を凍結する機構は診断済。問い = 深さは降下 dynamics か static か、および bar 適合の帰属。

## 読み列 (2 列、conflation 禁止)

- **列(i) = pinned-depth の sf=8 応答** (z_c1 undershoot、fast 基準 −1.6mm):
  - recovered: ≥ −1.0mm
  - non-recovered: ≤ −1.4mm (深化含む — slow は pre-pin 接触時間 4.16× で creep 深化が機構的に可能; 深化は anti-momentum 方向の証拠)。**−2.2 より深い場合は joint read に anomaly 行 1 本** (帰結は変えない)
  - partial: −1.0〜−1.4 (排他的中間)
- **列(ii) = final settled frame の pin-除外 free-node floor min-dist**:
  - PASS: ≥ −1mm / VIOLATION: < −1mm
  - episode-min は classifier に使わない別診断列 (wall 系と同種の physics-validity; c1_retained_final の final-frame 前例と整合)

## 6-cell mapping (機械適用、優先順位 = specific-over-general)

| (i) \ (ii) | PASS (≥−1mm) | VIOLATION (<−1mm) |
|---|---|---|
| recovered | **①** slow-seat 採用、bar 不変、production = offset-gated slowseat ON | **data-quality escalate** (free node が pinned より深い = 幾何矛盾) |
| non-recovered | **②a** mesh bar v1.1 文言 = 受け皿どおり PASS、pinned depth = 強制状態列 (38N×剛性 bound)、slowseat OFF (最小 delta) | **②b** loud escalate — 文言では救済しない real violation 候補 → fix path or Rs 明示 (PREREG 緩和禁止) |
| partial | **escalate** (wording+slowseat の選択不能; bar 帰結は両案 PASS で共通) | **②b** |

- ②b = {non-recovered, partial} ∧ VIOL。recovered ∧ VIOL のみ data-quality (specific-over-general、%9 (a) 読みで confirm 済)。
- gap なし・全 6 cell 帰結あり (%9 完全性検証 ✓)。

## rerun validity gates (3 本 — 満たさなければその走行は INVALID、開封しない)

1. run.log の slowseat 対象 leg に steps>50
2. slowseat npz sha ≠ 同 offset f2 cell sha (silent-identical 検知)
3. as-executed 式整合: (dist, steps) pair が steps==int(dist_cm×50×8) を満たす

## 予約済 joint-read 項目

- 新 field (pin-除外) が既存 pin 込み print (cable↔C1 = −3.421) と分離した値を示すこと (%9 reserved check)
- C2-HALF normal 38N (nom 5.7N) incidental の追跡 (v0.10 深押込み narrative 行き)

根拠 exchange: %12↔%9 pane dispatch 18:57–19:03 JST (INVALID 独立確認 3 経路 / sf=8 検算 EXACT / 6-cell 列挙)。floor trap footnote (sf<1.92 で短 leg 常時 50 束縛) は spec v0.10 行き。
