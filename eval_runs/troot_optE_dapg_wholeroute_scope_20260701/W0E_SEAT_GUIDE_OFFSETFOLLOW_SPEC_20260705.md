# W0-e: seat/guide offset-follow 修正 spec v0.7 (Rs「A」15:1x 授権 — locked file 編集承認)

**目的:** J-9 で確定した決定論的系統欠陥 (seat push / L guide が cable offset に無追従) を script 側で修正し、grid 再走で訂正 evidence を得て packet v1.1 → DC-1 再決定に接続する。
**L-TRIAGE: L3** (Rs-LOCKED production route `test_newton_clip_routing.py` の物理 choreography 変更; keyword: phase/ik。編集授権 = Rs「A」verbatim)。
**設計原則:** 恒久原則 0 (common-mode decomposition) + fix-⑤/caveat-a の確立 pattern (measure actual → common-mode compensate) の seat/guide 系への適用。**新機構の発明ではない** — 既に grasp 系で banked された offset-follow の欠落部位への展開。

**changelog:**
| 版 | 内容 |
|---|---|
| v0.1 (15:1x) | Rs「A」授権 scope 起草 = 3 leg (F-1a/F-1b/F-2)。F-3 は「要 forensics」条件付き |
| v0.2-0.5 (15:3x-16:0x) | %9 cross-PV 反映 (bright lines / SIM-ONLY / PREREG riders) + F-1b′ 数値確定 (sweep two-key) + **F-3 有効化 (15:58 F-0 監査で v0.1 の forensics 条件成立 → 4 leg 化。Rs へは v1.1 packet で明示 ack を取る)** |
| **v0.6 (16:2x)** | **5体 [VERIFY] 反映** (`W0E_5TAI_DECIDE_20260705.md` cluster A-U 全採用) + **offline 測定子検証 (81 npz、`w0e_offline_validation/`) の新事実反映** — 測定子 guarded 定義・clamp ±22・残差形式再測・strict_v2 C1 leg 再 pin (flank-z 81/81 検証済)・span as-executed 受入・RUN-2 family・pre-build probe P-1..3 |
| **v0.7 (16:5x)** | **%9 cross-PV PASS-w-fixes 反映**: w-1 (④ enumerate に PRELIFT sub-step 追加 — 自己 indict 再発の閉止) + w-2 (policy 節を node-identity/lattice-位相に scope 限定 — cable pose observable は P2 obs contract 統治で禁止対象外) + c-1 (r label 訂正: +0.195 = all-81 / **miss-22 内 r=−0.074≈0** — PARTIAL 降格を更に支持) + **新 pin vs 旧 flag = 81/81 agreement (%9 独立確認、既出数値の変更なし)** 閉包 |

## Root-cause (code cite + offline 実測、v0.6 更新)

| # | 部位 | 現状 | 欠陥 (v0.6 実測更新) |
|---|---|---|---|
| RC-1 統一像 | `C1_SEAT` :4169-4175 降下 target = `tgt2(x_clip, y_clip, zk)` = 純 nominal | **ROUTE-end の crossing X 変位 δx が C1 escape 36/36 を予測 (FP 2 = dx−5 knife-edge 生還、FN 0)**。変位は bimodal {≈+0.2, ≈−16.3mm} で **dx 非比例** (ph5 行は dx=+20 でも −16.3; dx=−20 で −19..−20)。亜類 (i) ph0∧dx≤−10 = **平行 offset** (span 一様 −16 → common-mode 並進で完全補正) / (ii) ph5 = **斜行 buckle** (crossing −16.3 + 勾配 ~17°) — slack held-span (achieved 92.4 vs target 88mm) の横座屈 mode を node 位相 + drag 履歴が選択、と統一解釈 (micro 機構の pin は不要 — F-1a は閉ループ)。ROUTE-end cable 高度 z≈846-851 ≈ 外壁上端 850 同高 = offset 時は降下前から壁に掛かる。旧 RC-1a z-class「843-854」は不正確 — stripe に 857.3/858.8 を含む (CC4-CH6; 同 2 cell も変位 map 上 −16.0/−16.3 = 第 3 機構不要、named watch cell 化) | 発現 = 帯行 (ph5 全 dx + ph0 の dx≤−10)。z 終値 [843,881] は座屈亜類と降下動態の合成。**実機 cable に node 位相は無し → sim 固有 (転移 conservative、ただし DR evidence / 学習 curriculum を汚染するため修正必須)** |
| RC-2 | `GUIDE_C2` :4336-4342 L path = 直線 (per-leg lx,ly 線形補間)、cable 実線と横乖離 | cradle 0/8 (offset) vs 8/8 (nominal) — **ただし 0/8 は全て seat 失敗下の測定 = 汚染帰属 (CC2-CH5)。良 seat 下の in-guide 逸脱は未観測** → F-2 は build するが **RUN-2a (F-1a 単独) で帰属してから re-grid 構成を確定** |
| RC-3 | `C2_DUAL_SEAT` :4651-4656 = 両腕 pure-nominal 降下 (F-0 監査で code 確認) | **PARTIAL 機構に降格 (offline 実測)**: C2-miss 22 中 11 は \|δx_c2\|>3.5mm (max −24.4 → F-3 対象)、**11 は ≤3.5mm (横捕捉済み high-seat = F-3 非対象、z 帯機構は残 unknown → re-grid watch)**。相関 r(\|δx_c2\|, c2z_gap) = +0.195 (all-81) / **miss-22 内 r=−0.074≈0 [v0.7 c-1 label 訂正 — PARTIAL 降格を更に支持]**。S-2 機構 (R 再 grasp cable-X follow :4477-4489 → TRANSPORT :4635 が nominal へ carry) は成立 |
| (取下げ) B2→C2 静的位相結合 | — | **機構主張は撤回 (CC4-CH3 + %12 再計算 CONFIRM)**: 静的位相は C2-entry まで生存しない (scrambling 実測: 0→7.1 / 5→4.2 / 5→11.5 非共通)。B2 の C2 同時落ちは n=1 の観測 correlate として記録のみ |

## Fix 設計 (4 leg、全て offset-active 時のみ発火 = None-path byte-identity 保存)

**測定子の共通 guarded 定義 (全 lane 義務、5体 cluster A):** 対象 crossing の測定 = **Y 窓 \|y−y_ref\| ≤ 7.5mm ∧ X 妥当窓 \|x−x_ref\| ≤ 30mm** 内の node 平均 (81/81 で node 数=1・tail 混入 0 を offline 検証済)。**plausibility gate: 窓内 0 node または \|δ\| > 30mm → 補償 0 + loud flag** (失敗分岐 = 無補償 = 現状 class → 単調安全は gate 条件付きで成立)。

- **F-1a (C1 seat X-follow、両縞の primary):** `ROUTE_C1` 到着後 settle 済み状態で guarded δx を測定 → `C1_SEAT` 降下 target を両腕 common-mode で −δx 補償 (**注入 = tgt2 の共有 x 引数、scalar clamp を fan-out 前に適用**)。**clamp ±22mm (v0.5 の ±12 は観測必要量 max 20.1mm に不足 — offline 実測で改訂)**。降下中 k=4 で再測 1 回 — **残差形式で凍結: comp ← clamp(comp + (measured_crossing − current_target_x), ±22)** (nominal 参照だと補償を自己解除する — CC2-CH2)。**再測前 30-step settle**。測定順 = F-1b shift → settle → F-1a 測定。斜行 buckle 類の局所勾配 (3-node) を診断 log (制御には不使用)。
- **F-1b′ (Y 位相退避、経験則 = 座屈 mode の trigger 回避):** **operand δ := config `CABLE_XY_OFFSET[1]` [mm] の floor-mod 15 (Python `%`; −10→5)。config 導出のみ・node 状態読取禁止** (fix-⑤ :3950 と同 gating 系; state 位相は未較正 + bright-line 抵触)。trigger: δ ∈ [2.5,6.5] ∪ [11.5, **UB**] → common-mode Δy で δ_target=7.5 へ退避、**\|Δy\| ≤ 7.5mm (H2 整合; B2 縁 13.5 で必要 6.0 — v0.5 の ≤5 は算術誤り)**。**UB = 13.5 を pre-build probe P-2/P-3 (dy=13.5/14.0) で build 前に確定**。適用点 = 降下前・壁上端より上で完了。**achieved-phase log (退避後 pre-seat の nearest-node Δy) + \|achieved−commanded\| < 1mm を RUN-2c 受入に**。評価注記: 87/87 走査は **in-sample fit** (規則を構築した点集合上の走査)、out-of-sample = dy10.5 の 1 cell → RUN-2c/2d の数値受入で介入を初実行。B1 margin = 区間 [1.5,2.5]mm (単点 6.0 O は n=1)。帯定数の provenance = cuda:0 + 本 build sha (PREREG に stamp、migration 時は {4.5,7.5,12.5} spot-check)。**scope 条項: F-1b は帯 trigger の回避のみ — F-1a と AND。F-1b の必要性自体を RUN-2c (F-1a 単独 → +F-1b) で帰属** (F-1a が斜行類も救う場合、F-1b は conservative 退避として維持されるが機構主張はしない)。
- **F-1b 許容性 (kinematic-trick 線引き、%9 4 bright lines — v0.6 で ④ を操作的に再定義 [CC5-CH2、%9 付議]):** 許容形 = 命令系 (EE target) への common-mode Δ を episode 内で適用し arm が物理的に動く (settle-center recenter / E15 / fix-⑤ / :4477 と同 class)。**禁止 = ①cable qpos/node 直接書込・teleport ②pin の node 選択規則の改変 ③span-bearing 両腕把持 phase (C1_SEAT / C2_DUAL_SEAT) での per-arm 差動 (INV#2; F-2 は R 解放済 :4274 の単腕 guide phase ゆえ非該当と明記) ④per-physics-step の node-identity/位相 servoing、および学習 policy rollout 内の **node-identity/lattice-位相 (sim 固有量) の feedback — cable pose 系 observable は P2 obs contract 側で統治し本禁止の対象外 [v0.7 w-2]** (許容されるのは phase 境界の scheduled measure→compensate = 本 spec の enumerate された測定点のみ: ROUTE-end settle 後 / k=4 / per-guide-leg **+ PRELIFT sub-step [v0.7 w-1]** / F-3 settle 後 / k=6)**。**SIM-ONLY provenance tag 必須**: F-1b は node lattice (sim 固有量) で command を決める sim-artifact 補償器 — 実機 playbook から明示除外 (実 cable に位相は存在しない)。
- **F-2 (L guide cable-line follow):** 各 GUIDE leg + **PRELIFT 8 sub-step** で、次 leg 目標 Y での guarded cable X を測定 (**新規 per-leg read [write なし] — v0.5「追加計装なし」は誤りと訂正; :4354 は cradle bool で X を持たず、:4305 guide_body は開始時固定で不適**) → lx に偏差補正。参照 = nominal 直線 lx(k)、per-leg ±8mm clamp、**累積 cap = throat 半幅**。**is_cradle=True の時のみ発火 (逸脱防止であり、脱落後の re-capture は主張しない)**。
- **F-3 (C2 seat crossing 補償) — PARTIAL 機構 (対象 = \|δx_c2\|>3.5 の miss 類、offline で 11/22・max −24.4mm):** **測定前 60-step settle (offset-gated; TRANSPORT 末尾は無 settle :4651)** → guarded δx_c2 測定 → 両腕 common-mode 補償 (**単一 `_c2x_comp` を :4655-4656 の両 tuple に注入 — per-arm tuple 手組箇所ゆえ注入点を明示固定 [CC5-CH3]**)、clamp ±22 + plausibility gate。**降下中 k=6/12 で残差形式の再測 1 回** (F-1a と同形 — 非対称の解消 [CC3-CH5])。**grip 保持 monitor (補償前後の L/R claw-cable N) を RUN-2 受入に**。⚠ 二重補償 guard: R-follow (掴み=cable-X) と seat 補償 (=crossing) の座標系一貫・単一適用 (%11 S-2)。pin は DUAL_SEAT まで活性 (解除 code なし、grep 確認) — 共 mode ≤22mm は pin-grip 間張力変化として因果連鎖に記載済。
- **F-0 監査結果 (15:58 納品、`W0E_F0_TARGET_AUDIT_COORD.md`):** in-scope `ik_move_both` 15 call 全数分類 (calibration 4/4) — canonical path に未 cover の新規 F-leg なし = 本 spec 4 leg で過不足なし。43-step 整合の per-leg map: **F-1a/1b → step 7 (Push into C1) / F-2 → steps 10-11 (Rise/Above C2) / F-3 → step 15 (Push into C2)** — 測定は step 内 target 計算であり step 増減・順序変更なし (「しごき誘導」なる step 名は存在しないため v0.5 文言を訂正 [CC5-CH5])。

## Gating / 不変条件

- 全 leg `CABLE_XY_OFFSET` 非 0 時のみ active (**RUN-1: offset=(0,0) で従来と byte-identical** が hard gate)。**per-leg env flag (W0E_F1A/F1B/F2/F3、default = offset 時 ON) を建て帰属 run を可能に**。
- INVARIANTS 不触: DUAL-ARM / 88mm span (common-mode のみ + **as-executed span 受入列を常設** [CC5-CH3]) / DiffIK-only / コ geometry / no-kinematic-trick (補償 = EE target 修正。pin は既存承認 scope 不変)。

## PREREG v2 (再走の成功判定、pre-data pin — v0.6 で凍結、%9 riders ①-④ + 5体 cluster F/K/M/R 反映)

- **strict_v2 = verdict ∈ {SUCCESS_DUAL_LOADED_AT_88, SUCCESS_R_GRIP_L_CAGE_AT_88} ∧ c2_seated_honest ∧ c1_retained_final** (SUCCESS glob を enumerate [CC5-CH7]; L_CAGE の「verify RETAIN via video」意味論は Rs 動画 gate + CC 動画 leg が cover)。
- **c1_retained_final := `route_c2_metrics.z_c1_final_mm` < 840 ∧ 新設 `c1_flank_max_z_final_mm` < 840** (±10mm Y 窓の max cable z、final frame) — **旧 v0.5 の `route_c2_summary.c1_retained_lowwall` は dangling 参照 (producer に不存在; 同名 decoy は guide-end 時点値) につき再 pin [CC5-CH1]。flank 項 = pin 同語反復の回避 (pinned node z は pin 剛性を測る — 周辺 node の乗り越え逸脱 [Rs-①類] を捕捉) [CC3-CH2]。offline 検証: 81/81 完全分離 (retained 45 false-fire 0・余裕 7.1mm / escape 36 miss 0) = 運用18 ground-truth 済。**新 pin (z ∧ flank10) vs 旧 flag = 81/81 agreement (%9 独立確認 [v0.7]) — 再 pin による既出数値 (40/81 等) の変更なし**。producer への field 追加は in-scope code 宣言。`all_c1_retained_lowwall` は guide-scope 診断列 (rider ① 注記)。vacuous-truth 注記: 把持不成立で cable が卓上 (~804) の場合 z 条件は空虚に真 — verdict ∧ c2_honest との conjunction が実質 cover (記録)。
- **predicate-completeness 行 (rider ②、運用29):** 分子 conjoin legs = {route 完遂 verdict (再 grasp scope; 初期把持/lift/transport は verdict 文字列の前提条件として implicit cover — 明示列挙 [CC5-CH7]), C1 final 保持 (z + flank), C2 honest 着座}。**cover しない leg** = {C1 着座深さ (床 829 到達 — 診断列で分布監視), しごき係合率 (cradle 診断列), penetration (下記 bar), tilt/slip 系 (既存診断列), 横捕捉済み C2-miss 11 cell の z 帯機構 (unknown — watch 列)}。
- **penetration bar (field-scope 明示 [CC4-CH9]):** 床 undershoot ≥ −1mm (出所: strict-59 実測 min −0.39 + margin) ∧ 壁 overlap ≥ −4mm (= cable 半径 1 本; **baseline は C1 側壁 2 違反 −5.05/−4.02 [x-20_y-15 final / x-10_y-15 seat] = bar は判別力あり・fix 対象そのもの**)。対象 field = {cable_c1_seat/final, c2_seat, c2_wall} + **build で新設する episode-min channel** (snapshot だけでは whole-route を主張できない)。
- **denominator 意味論 (rider ③):** F-1b 適用後の再走は「Y 位相整列済み分布」— denominator 81 は同格子だが位相 artifact 退避後の分布と v1.1 §2 に明記。**帯規則の標本 = 10 位相点、trigger は連続 DR の ~41% で発火** (v1.1 §2 に明記 [CC4-CH8])。
- **T3 baseline (rider ④):** R2b PASS bar は re-grid の strict_v2 実測で再導出 (旧 0.728/0.494 不使用)。
- **一次予測子 (v0.6 で識別区間形式に書換 [CC4-CH1/CH2]):** fix 後 strict_v2 の**識別区間 = [0.728 (C2 動態不変・C1 全回復のみ), ~0.95 上限 (F-3 が band 内 residual を全回復)]** — ただし offline 実測で F-3 対象は miss の ≈半数 (11/22) → 上限は減衰。0.80 branch 境界が区間内 → **DC-1 は再走実測でのみ決定可 = fix→re-grid→一回決定 sequencing の根拠 (「実数支持」表現は撤回)**。Wilson 法 pin: 40/45 = [0.765, 0.952]。
- secondary: any-seat / seat-miss class / z_c1・z_gap 列 / **as-executed span 列** / counting per-offset unique 不変。evidence-gate 枝 (≥95%/≤80%) は strict_v2 で読む。
- **re-grid 選点:** primary = 同一 81 格子 + **δ-probe annex 8 cell {−2.5, 1.25, 5.75, 9.25, 11.5, 12.5, 13.5, 14.0}** (帯縁 pin + 最大 gap 縮小 [CC4-CH8]) + **named watch cell (x-10,y0)/(x-20,y+15)** (旧 858-class の帰属)。

## 受け入れ (acceptance、v0.6 拡張)

0. **pre-build probe (build 前、既存 runner、~5min GPU):** P-1 dy=−2.5 (位相 12.5 の周期性 falsifier — B2 が位相か絶対 dy か) / P-2 dy=13.5 / P-3 dy=14.0 (B2 上縁 UB 確定) / **reach probe (補償極値 4 隅 [x_clip±22, y_clip±7.5] の空中 IK 残差、両腕・seat z)** [CC3-CH6]。
1. RUN-1: nominal byte-identity (sha 一致、%12 独立再計算)。
2. **RUN-2 family (数値受入、81 再走前):**
   - **2a** x-20_y-15、**F-1a 単独** (F-2/F-3 OFF): z@C1→829±1 + c1_retained_final + **良 seat 下の per-leg cradle 初観測 → RC-2 帰属** [CC2-CH5]。
   - **2b** x-20_y-15、全 leg ON: cradle 8/8 目標 + penetration (field-scope) + span 列 + per-phase IK 収束 log + F-3 fire/grip monitor。
   - **2c** x0_y+5 (斜行 buckle 類)、F-1a 単独 → +F-1b の 2 走: **F-1a 単独充足性と F-1b 必要性の帰属** + F-1b fire assert + achieved-phase < 1mm [CC3-CH4, CC4-CH5]。
   - **2d** x0_y+12.5 (B2)、全 ON: C2 honest watch (B2 の C2 相関 n=1 の再観測)。
3. **CC 動画 leg (運用14 skill-path、Rs gate の前):** RUN-2 系 + 代表 cell を video-analyst で C1/C2 contact-zoom 検証 (manual frame Read では不充足) [CC5-CH10]。
4. **Rs 動画 gate (Rs 15:5x「修正後、再度、動画で確認したい」— 81 再走の前):** whole-route 動画 4 本を ~/Downloads へ — ①x-20_y-15 ②x0_y+5 ③x0_y+12.5 ④nominal (0,0)。crop は C1 と C2 の両方 + whole-route (§運用30)。**Rs 確認 OK が出てから 81 再走に進む**。**F-3 の scope 拡大 (3→4 leg) を同時に明示 ack** [CC5-CH6, NHA r3]。
5. 81-cell 再走 (cuda:0、runner 流用、~2h) → strict_v2 + 独立再計数 (two-key 標準形) + penetration/span/watch 列常設。
6. joint read v2 → packet v1.1 (§2 差替 + DC-1 再検討 [識別区間形式] + F-1b SIM-ONLY・P2 再分割将来項の明記 [NHA r1]) → %9 PV → Rs。

## 工程 (v0.6 更新)

5体 [VERIFY] **済** (`W0E_5TAI_DECIDE_20260705.md` = PASS-with-amendments、本 v0.6 が反映版) → **%9 cross-PV (v0.6 + DECIDE + offline 検証、bright-line ④ 再定義を明示付議)** ∥ **%11 build charter (per-leg flag / producer field / probe P-0..3 / RUN-1 / RUN-2 family)** → CC 動画 leg → Rs 動画 gate → 再 grid → v1.1。banking HELD 継続 (訂正 evidence まで)。本 spec + GD + F-0 + DECIDE + offline 検証を **git commit (本 turn、CC5-CH6 provenance)**。

*v0.1 %12 15:1x 起草 → v0.6 %12 16:2x (5体反映)。root-cause cite = JOINTREAD J-9 + 本 spec RC 表 + `w0e_offline_validation/percell.csv`。*
