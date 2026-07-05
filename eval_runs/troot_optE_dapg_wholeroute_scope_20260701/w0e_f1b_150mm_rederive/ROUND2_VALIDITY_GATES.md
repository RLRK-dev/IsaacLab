# round 2 (F-1b′′ 81 再走) — 読み前 validity gate 追記 (pre-read 固定、%9 提案 + %12 confirm 2026-07-06 05:3x)

1. **C-0 系 gate (既存)**: (0,0) npz sha == RUN1_REFERENCE_V2 `5f1c3f92…` (runner built-in early gate + 読み時再計算)。
2. **54-cell byte-identity gate (新規、%9 提案)**: 非 φ5 の 54 cell (φ0 列 27 + φ10 列 27) は `w0e_81rerun_0211` の同 cell npz と **bit 一致が構造的期待値** — F-1b′′ は φ≤7.5 snap-down 限定 + φ>7.5 fall-through、φ0 = F-1b 不発火、φ10 = 旧 B1 帯 [2.5,6.5] 外 ∧ B2 absolute 帯 grid 不該当 = 旧走行で一度も fire せず、cuda:0 決定論下で不変のはず。**乖離 cell = loud + paired 比較から隔離** (意図外汚染 or 非決定論の検出器)。
3. 期待帯 (informal、算術: φ5 列現 strict 12/27 → 全 heal で 43+15=**58**): 公式値は two-key recount のみ。
- 読み分担: %9 = 54-cell sha gate → v2.1 recount → φ5 paired 27 → 診断列 / %12 = 独立 recount + C-0 再計算 → 交換 → 確定。
