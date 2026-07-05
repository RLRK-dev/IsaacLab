# W0-e spec 5体 [VERIFY] — REBUT_OR_ACCEPT + NO_ACTION_EVALUATION + DECIDE (%12 CC1)

対象 = `W0E_SEAT_GUIDE_OFFSETFOLLOW_SPEC_20260705.md` (旧 v0.1 stamp / 実 v0.5 内容) + `W0E_GEOMETRIC_DESIGN_20260705.md` + `W0E_F0_TARGET_AUDIT_COORD.md`。
panel = CC2 (測定/timing、8 CH) / CC3 (物理/動力学、6 CH) / CC4 (evidence/統計、11 CH) / CC5 (rule/不変条件、10 CH) / CC6 (NHA)。
CC1 独立検証 = code cite 全読 (:3937-3963/:4155-4234/:4295-4359/:4625-4668/eq_active grep) + **offline 測定子検証 (81 npz、GPU 0)** = `w0e_offline_validation/{validate_measurands.py,percell.csv}`。

## 0. offline 検証の新事実 (DECIDE の一次 evidence)

1. **ROUTE-end crossing 変位 δx (guarded 選択子) が C1 escape を 36/36 TP / FP 2 / FN 0 で予測** (しきい値非依存: >3.5〜>12 で同一)。FP 2 = (dx−5,dy0) −15.9 / (dx−5,dy+15) −14.6 の knife-edge 生還。
2. **変位は bimodal {≈+0.2, ≈−16.3mm} で dx に比例しない** (ph5 行は dx=+20 でも −16.3; dx=−20 で −19..−20 に増幅)。spec v0.5 の「X-bow ≥7.5mm @dx=−20」把握は不正確 → **±12mm clamp は不足** (観測必要量 max 20.1mm)。
3. **亜類 2 種** (局所 3-4 node 形状): (i) ph0∧dx≤−10 = **平行 offset** (span 一様 −16 → common-mode 並進で完全補正) / (ii) ph5 = **斜行 buckle** (crossing −16.3 + 勾配 ~0.31mm/mm≈17°; slack 92.4mm span の横座屈 mode 選択が node 位相依存)。RC-1a/RC-1b は「slack held-span の横座屈」で統一され、CC4-CH6 の 857/858 anomaly 2 cell も同 map 上 (−16.0/−16.3) = 第 3 機構不要。
4. **flank-z 判別子 (|y−y_clip|≤10mm 窓の max z < 840、final frame): 81/81 完全分離** (retained 45 false-fire 0、max 832.9 = 余裕 7.1mm / escape 36 miss 0) → 修正 strict_v2 C1 leg として凍結可 (運用18 ground-truth 検証済)。
5. **F-1a 選択子検証**: 窓内 node 数 = 全 81 cell で 1 (存在保証)、tail 混入 0/81、bare argmin ≡ guarded (C1 では hijack 不発現 — ただし guard は無コストで維持)。naive ±100mm 平均は max 3.58mm 汚染 (CC2-CH1 の poisoning は C1 では軽度、guard 採用で消滅)。
6. **F-3 測定子**: TRANSPORT-end で bare argmin hijack 0/81 (この時点では tail 不在; guard は維持)。**|δx_c2| と c2z_gap の相関 r=+0.195 (弱)**。C2-miss 22 中 **11 は |δx_c2|≤3.5 (横捕捉済み miss = F-3 の対象外)**、11 は >3.5 (max −24.4) = F-3 対象。→ RC-3 は**部分機構 (≈半数)**。
7. C2-entry 位相の再計算 = CC4-CH3 の scrambling を CONFIRM (x0_y0: 0→7.08 / x0_y5: 5→4.16 / x0_y-10: 5→11.54; 非共通 shift) — 静的位相は C2 まで生存しない。
8. ROUTE-end cable 高度 z≈846-851 ≈ 外壁上端 850 と同高 — offset 時は降下開始前から壁に掛かり得る (静的 wall-rest class と整合)。

## 1. REBUT_OR_ACCEPT (cluster 別; 提起者併記)

| # | cluster (提起) | 判定 | 内容 / spec v0.6 反映 |
|---|---|---|---|
| A | 測定子未定義・tail hijack・単調安全の偽り (CC2-1 CRIT, CC3-1 CRIT, CC5-8) | **ACCEPT** | guarded 選択子 (Y窓±7.5 ∧ X妥当窓±30mm) を F-1a/F-2/F-3 全 lane に義務化 + **plausibility gate (\|δ\|>30mm → 補償 0 + loud flag)**。gate により失敗分岐 = 無補償 = 現状 class → 単調安全が gate 条件付きで回復 (GD 5c 書換)。offline 検証で選択子は 81/81 健全 (§0-5,6) |
| B | k=4 再測の意味論 (nominal 参照だと補償を自己解除) + 無 settle (CC2-2, CC3-5b) | **ACCEPT** | 残差形式で凍結: comp ← clamp(comp + (measured − current_target_x), ±22) / 再測前 30-step settle / 測定順 = F-1b shift → settle → F-1a 測定。F-3 にも k=6/12 で同形を付与 (CC3 の非対称指摘採用) |
| C | F-1b operand 未定義 + mod 規約 (dy=−10 行 9 cell の silent miss) (CC2-3, CC5-9) | **ACCEPT** | δ := config `CABLE_XY_OFFSET[1]` の floor-mod 15 (Python `%`; −10→5)。**config 導出・node 状態読取なし** (fix-⑤ :3950 と同 gating 系)。state 導出位相は禁止 (未較正+bright-line 抵触) |
| D | F-2 の「追加計装なし」は偽 + guide_body 固定 + 非係合時無効 (CC2-4, CC3-5a, CC5-8) | **ACCEPT** | 制御入力 = **新規** per-leg guarded read (write なし) と訂正。参照 = nominal 直線 lx(k)、累積 cap = throat 半幅、**is_cradle=True gate (逸脱防止であり re-capture ではない)**。PRELIFT 8 sub-step にも同 follow を適用 |
| E | RC-2 帰属汚染 (cradle 0/8 は seat 失敗下の測定; F-2 は幻影補償の可能性) (CC2-5) | **ACCEPT** | per-leg env flag (W0E_F1A/F1B/F2/F3) を建て、**RUN-2a = F-1a 単独で良 seat 下の cradle を初観測**→ F-2 必要性を帰属。re-grid 構成は全 ON で PREREG (帰属 run は診断) |
| F | strict_v2 C1 leg: 参照 field が dangling + decoy + pin 同語反復 (pinned node z は pin 剛性を測る; Rs-① 周辺逸脱が不可視) (CC5-1, CC3-2, CC5-7c) | **ACCEPT** | 再 pin: `route_c2_metrics.z_c1_final_mm < 840` **∧ 新設 `c1_flank_max_z_final_mm` (±10mm 窓) < 840** — offline で 81/81 検証済 (§0-4)。producer field 追加は in-scope 宣言。`all_c1_retained_lowwall` = guide-scope と注記。vacuous-truth mode 記録 |
| G | INV#2 span as-executed 未検収 (DUAL_SEAT は per-arm tuple 手組 :4655-4656) (CC5-3) | **ACCEPT** | 注入点固定 = tgt2 の共有引数 (F-1a/1b) / 単一 `_c2x_comp` を両 tuple に (F-3)、scalar clamp は fan-out 前。受入に **as-executed target span == 88.0mm (C1_SEAT/C2_DUAL_SEAT) + achieved span 列**を常設 |
| H | F-1b 帯 map の dx 条件付け + 干渉 (ph10 は dx−20 生還) + joint 受入 cell ゼロ (CC3-3, CC4-CH5) | **ACCEPT-PARTIAL** | offline 新事実 (§0-2,3) で再解釈: X×Y は座屈 mode で結合済み、F-1a は閉ループゆえ dx 依存を per-cell 吸収。**RUN-2c (x0_y5: F-1a 単独 → +F-1b) を新設** = 斜行類での F-1a 単独充足性と F-1b 必要性を実測帰属。\|Δy\| cap は 6.5mm 必要 → **≤7.5 (H2 整合) に訂正** (CC3 算術指摘採用) |
| I | 87/87 は in-sample fit + retreat 介入は未実行 + RUN-2 で F-1b 不発 (CC4-CH5) | **ACCEPT** | spec に in-sample label 明記。RUN-2c/2d (B1=x0_y5, B2=x0_y12.5) の**数値**受入を 81 再走前に新設。over-trigger 良性は retreat-safety 実証に条件付くと明記 |
| J | B2→C2 静的位相結合は n=1 + 機構は実測で不成立 (scrambling) (CC4-CH3) | **ACCEPT** | 機構文言を削除 → 「観測 n=1 の correlate; 静的位相は C2 に不伝播 (実測)」。**pre-build probe P-1 dy=−2.5 (位相12.5 再現性) / P-2 dy=13.5 / P-3 dy=14.0 (B2 上縁)** を band_edge_sweep 拡張として即時実行 (~5min) — B2 trigger 窓 [11.5, UB] を build 前に確定 |
| K | 88.9% 予測子は自己の仮定と不整合; 識別区間 [0.728, ~0.95] が両 branch 境界を跨ぐ (CC4-CH1, CH2) | **ACCEPT** | v0.6 で識別区間形式に書換 (Wilson 法 pin [0.765,0.952])。「実数支持」削除。F-3-works branch (~0.95) 併記、ただし offline §0-6 により F-3 は miss の ≈半数のみ対象 → 上端は減衰。**sequencing 結論 (fix→re-grid→一回決定) はむしろ強化** (今は識別不能) |
| L | RC-3 CONFIRMED は過剰 (lateral 非分離 J-8 と衝突) (CC4-CH2) | **ACCEPT-PARTIAL** | offline §0-6 で定量決着: **PARTIAL 機構 (11/22)** に降格。F-3 は維持 (対象 11 cell、max −24.4mm は実在) + guard で無害化。横捕捉済み 11 miss は F-3 非対象と明記 (z 帯機構は残 unknown → re-grid watch) |
| M | penetration 「85/85 clean」は field-scope 不足 (C1 側壁 −5.05/−4.02 の 2 違反) (CC4-CH9) | **ACCEPT** | 主張を scope 訂正 (床+C2壁 = clean / C1 側壁 = escape 状態で 2 違反 — **fix 対象そのもの**)。re-grid 常設列に field 別 bar + **episode-min penetration channel を build で新設**。Rs へ訂正報告 (records-must-match-fact) |
| N | 帯 map 標本 10 点 / trigger は DR の ~41% / (12.5,15) 無測定 (CC4-CH8, CH7) | **ACCEPT** | annex を 8 cell に拡張 {−2.5, 1.25, 5.75, 9.25, 11.5, 12.5, 13.5, 14.0}。B1 margin は区間 [1.5,2.5] と記載。v1.1 §2 に標本点数と trigger 率を明記 |
| O | bright-line ④ が自 leg (F-1a k=4 / F-2 per-leg) を文面上 indict (CC5-2) + H1/③ が F-2 と矛盾 (CC5-4) | **ACCEPT** | ④ 操作的再定義: 禁止 = per-physics-step の node-identity/位相 servoing + 学習 policy rollout 内の node-state feedback / 許容 = phase 境界の scheduled measure→compensate (enumerate)。H1/③ は span-bearing 両腕把持 phase に scope、F-2 除外根拠 = R 解放済 :4274。**%9 (bright lines 起草者) の cross-PV に明示付議** |
| P | 43-step 整合の主張精度 (しごき誘導という step 名は不存在; F-3 未 map) (CC5-5) | **ACCEPT** | per-leg map 記載: F-1a/1b→step7 (Push into C1) / F-2→steps10-11 / F-3→step15 (Push into C2)。測定 = step 内 target 計算、step 増減なし |
| Q | 版・統治記録 (v0.1 stamp vs v0.5 引用 / 3 leg vs 4 leg / untracked) (CC2-8, CC5-6) | **ACCEPT** | v0.6 へ bump + changelog 表 / leg 数を 4 で統一 / **本 DECIDE と同 turn で spec+GD+F-0+offline を git commit** / F-3 scope 拡大は v1.1 packet で Rs に明示 (NHA r3 同旨) |
| R | 運用29 rider ② の残欠 (把持/lift/transport 未列挙、SUCCESS* glob、−1/−4mm 出所) (CC5-7) | **ACCEPT** | 分子 SUCCESS set を {SUCCESS_DUAL_LOADED_AT_88, SUCCESS_R_GRIP_L_CAGE_AT_88} と enumerate (L_CAGE の video-flag 意味論は Rs 動画 gate が cover と注記)。grasp/lift/transport → uncovered 列挙 + coverage 経路。bar 出所: 床 −1mm = strict-59 実測 min −0.39 + margin / 壁 −4mm = cable 半径 1 本分 + CH9 の 2 違反が判別力を実証 |
| S | reach 1.2mm の外挿 (regrasp/R-arm field のみ) (CC3-6, CC4-CH10) | **ACCEPT** | 主張 scope 訂正 + **pre-build reach probe (補償極値 4 隅の空中 IK 残差)** + RUN-2 で補償 target の per-phase 収束 log。clamp ±22 への拡大 (§0-2) でこの probe の重要度は上昇 |
| T | F-3 測定点に settle 不在 + pin が DUAL_SEAT まで活性 (CC2-6) | **ACCEPT** | F-3 測定前 60-step settle (offset-gated) + B の k=6/12 再測 + **grip 保持 monitor (補償前後の L/R claw-cable N)** を RUN-2 受入に追加。pin 常時活性は事実 (eq 解除なし grep 確認) — F-3 の共mode ≤22mm は pin-grip 間 span への張力変化として 5c に追記 |
| U | 帯定数の device/build 条件性 (CC4-CH11) | **ACCEPT** | 定数に provenance stamp (cuda:0 + build sha) を script comment + PREREG に記載。migration checklist に 3-cell spot-check {4.5, 7.5, 12.5} |

**REBUT (棄却・限定) した点:** (1) CC2-CH1 の「C1 でも argmin hijack」— offline で C1/TRANSPORT-end とも hijack 0/81 (ただし guard は無コストで採用 = 設計は CC2 案のまま)。(2) CC2-CH4 の「高所 traverse では cable が throat に居ない」— nominal cradle 8/8 (J-9 g3) が高所係合を実証済み; 非係合となるのは escape 後のみで、is_cradle gate が定義域を閉じる。(3) CC3-CH3 の「dx=0 帯 map は転移不能」— F-1a が閉ループで per-cell 吸収するため帯 map の役割は Y 退避 trigger のみに縮小 (RUN-2c で実測帰属)。いずれも fix 形は挑戦者提案と同一に収束するため実害なし。

## 2. NO_ACTION_EVALUATION

CC6 (NHA) = **CHANGE_JUSTIFIED** — null + 代替 4 案 (α学習吸収 / DR envelope 縮小 / defer / F-1b 除外) を project 自身の SSOT で反証: script は DAPG の **teacher** (決定論的 41/81 欠陥 = curriculum でなく汚染教師; spec RC-1b 自認) / ±20mm は Rs 確認済み deploy 要件で縮小不可 (SOMA:28) / 同 pattern は本 file に 3 実装済 (1 つは Rs-LOCKED anti-revert :4477) で fix は安価 / defer は rider ④ で数日内に自己無効化。Gate-FAIL default (fix root cause first) + prohibited.md hard-stop に整合。**No Action 棄却。** NHA riders r1-r4 (SIM-ONLY 維持 / 設計方針違反の cite 化 / 3→4 leg 明示 / RUN-1+rider ③④ hard gate) = 全採用。トレード表に除外 2 行 (envelope 縮小 / defer) を追補 (CC6 弱点 1 の完了)。

## 3. DECIDE

**PASS-with-mandatory-amendments** — ACCEPT した CRITICAL 2 / HIGH 8 は全て spec v0.6 の設計文面・受入基準の修正で解消可能 (機構再設計・premise 変更なし)。v0.6 を本 turn で発行し、**再検証 = %9 cross-PV (bright-line ④ 再定義の起草者付議を含む) + offline 検証済み項の機械照合**。build は v0.6 準拠で %11 charter (per-leg flag / producer field / probe P-1..3 / RUN-2 family を含む)。

**残 unknown (loud 記録):** (a) 斜行 buckle 類で F-1a 単独が充足するか (RUN-2c が帰属) / (b) B2 上縁 (P-2/P-3 が確定) / (c) 横捕捉済み C2-miss 11 cell の z 帯機構 (F-3 対象外; re-grid watch 列) / (d) 座屈 mode 選択の micro 機構 (経験則で design は非依存)。

*%12 CC1、5体 = background agent 5 本 (CC2-6)、offline 検証 = `w0e_offline_validation/`。2026-07-05 16:2x JST 起草。*
