# lane-aware EE-Z floor (65b5b9dd21) tight 5体 VERDICT — RS-TECH-LEAD (%12, CC1) — 2026-07-10

**Object:** commit 65b5b9dd21 (lane-aware floor fix, Rs 案B) + COMP3_GEOMETRIC_DESIGN_LANEFLOOR doc。CC2 回帰 / CC3 物理 / CC4 幾何 / CC5 process / CC6 NHA、並列独立。

## DECIDE = **PASS-WITH-FOLDS**(採択; fold 後に確認計測→G1 再試行 = Rs 承認済み chain)

- ブロッキング欠陥ゼロ。全数値 claim が 2 体 (CC5 全掃引 / CC3+CC4 部分) により**生データから独立再現・一致**。CC2 = NO CHALLENGE。CC6 NHA = CHANGE_JUSTIFIED (status quo は trainer 段も毒する — 旧床は実証把持深度を policy にも禁止)。
- **L3 手順記録 (CC5-M3、明示)**: 本 fix は L3 (diff keyword)。pre-implementation 5体をスキップして build が先行した (Rs 案B 裁定 13:4x が commit 13:50 に先行 + 根因 diag が別 commit で証拠確定済という状況判断)。本 tight 5体が pre-acceptance 補償 + §運用15 層2 (on-disk) + 層5 (多視点) を同時 discharge。以後の同型 fix も「Rs 裁定→build→即 tight 5体 (acceptance 前)」を最短形とする。

## 鍵となる相互作用 (CC3×CC4、CC1 裁定)

CC3-M1: 「境界の 5mm 段差に replay/残差が届かない」性質は nominal-cell の余裕 16.00mm > 残差上限 15mm という**未 pin の 1.0mm 不等式**に依存。しかし **CC4-F2 の 81-cell 実測: R park の lane 端余裕は最小 11.3mm** → off-cell では残差 15mm が境界に**届く** = CC3-M2 の「片腕だけ +3.12mm 持ち上がる span 破れ channel」(b′ 射影の z-span 不変量を破る新規 channel、G1 根因と同じ変位クラス) が trainer 段で実現可能。
**⇒ 裁定 R-A: 共有床 (structural fix) を採択** — mode-0 (dual、span 不変量が主張される射影) では両腕の床を `max(floor_R, floor_L)` に統一して両方を clip。境界 excursion 時は両腕が一緒に持ち上がる = span 保存 (conservative 方向)。mode-1 (transit、span 主張なし) は per-arm 維持。**replay-neutral 証明済み** (replay の低 z frame は全 cell 両腕 in-lane → 共有床 ≡ lane 床)。fragile な global 不等式 assert は採らない (81-cell で偽)。

## 裁定一覧 (REBUT なし、全 ACCEPT + 処置)

- **CC3-M2 + CC3-M1** → R-A 共有床 (上記) + L4 data assert (replay 低 z frame 全て in-lane / 81-cell 最小端余裕 11.3mm を記録) + z-equality 保存 unit。
- **CC4-F1 (C1 島)** → **R-B: float-aware carve-out 採択** — 島 footprint X[0.330,0.370]×Y[0.135,0.165] 内は floor = `EE_Z_FLOOR_KO + rc.ROUTE_CLIP_FLOAT_Z` (=1.08992 現行; float が 0 になれば自動的に 1.06992 = 正しい table-mount graze 境界に退化)。旧床値でなく float-aware 値 (旧床は死んだ境界 — CC4 が私の seed 前提を訂正、正)。replay-neutral (81-cell 実測: C1 近傍最低 z +63mm、到達 gap +13.7mm)。CC3-L4 の float-removal coupling も本式で自動解消。
- **CC5-M1** → 掃引 artifact 永続化: CC5 の再現 script を採用 (scratchpad cc5_lane_floor_sweep_repro.py → comp3_lane_floor_sweep.py + result JSON)、**TARGET 列に拡張** (CC3-L3: clamp が作用するのは target 列 — 旧床 bind は target 264 frames / achieved 250、両列 label 明記)。
- **CC5-M2** → supersession 注記: plan §D/§5「flag-OFF byte-identity」・rulecheck doc・layer25 verdict「PRESERVED」に一行 dated 注記 (COORD)。node/LEDGER に supersession + **re-bank 規則** (CC6-cond3: 旧床時代の ⑨a′ 級 runtime 数値は新床で再 bank、pre-fix banked と diff しない) 行 (%12)。
- **CC3-L3 / CC4-F2 / CC5-L5** → doc 訂正一括: target/achieved 列 relabel・81-cell envelope (R/Y_hi 11.3mm)・島の明記・window start {896..900}・frame 数 {7706..7710}・+24/−4・flag-OFF は close 窓外 37 frame (descend) も変化する旨。
- **CC5-L4** → code comment に flag-OFF 挙動変化 + supersession 一行 (COORD)。
- **CC2-INFO2 / CC6-cond2** → **R-C: flag-ON build 時 lane-vs-as-built-void parity assert 採択** (leg-C 型 readback を `_build_model` flag-ON に ~10 行; 将来の void 変更 drift を build 時に fail-loud 化)。flag-OFF 無影響。
- **CC6-cond1** → G1 再試行 = 十分性 gate; 単一 cell PASS はその cell のみ主張 (§運用30) — G1 verdict 文言に拘束。
- **CC6-cond4** → **AC env 同型床 (newton_approach_cable_mujoco_env.py:200) の監査 = 別タスク提案として Rs へ** (実装しない、§運用24)。

## 実行順

COORD fold chunk (R-A/R-B/R-C + unit + artifact + doc/注記) → %12 verify → 確認計測 (~2min、爪高さ=録画一致) → G1 再試行 (~6min、動画 + Rs human-GT)。確認計測・G1 は Rs 承認済み chain 内。R-A/R-B/R-C は案B 方向内の conservative 精密化 + replay-neutral 証明付き — Rs 異議あれば revert 容易 (fold 報告で明示)。

---
*%12 RS-TECH-LEAD 2026-07-10。5/5 完了、独立再現 2 系統一致、REBUT 0、DECIDE=PASS-WITH-FOLDS。*
