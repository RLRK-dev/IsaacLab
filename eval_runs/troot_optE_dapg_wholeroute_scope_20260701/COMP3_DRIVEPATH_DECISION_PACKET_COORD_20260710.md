# COMP3 drive-path decision packet — production 駆動経路 A/B/C/D (Rs 決定用)

- Date: 2026-07-10 (COORD; %12 design-gate dispatch 19:07、Rs 総括受理 16:2x 後)
- Scope: comp3 G1 診断 grid 完成後の production 駆動経路の選定材料。**決定は Rs 専権** — 本 packet は
  options + evidence + cost + 未実証 gap を提示するのみ。
- Machine evidence: `comp3_drivepath_cost_probe.py` + `comp3_drivepath_cost_probe_result.json` (再実行可能)。

## §0. Grounding (§運用4 anchor set, read + cited)

| SSOT | 位置 | 本 packet での役割 |
|---|---|---|
| fork-(iv) residual 契約 | `route_executor.py:3238-3243` (step_target: base = 録画 achieved-path waypoint `ee_pos[next_f]`) + `newton_route_env.py:956-996` (_apply_actions_batch: commanded = absolute base + projected residual、非積算) | option A/D の契約整合判定の基準 |
| drive loop | `newton_route_env.py:1016-1043` (10-frame joint 補間 + per-frame grip staircase + `_physics_step_all(RL_SIM_SUBSTEPS=4)`) | 変更対象の現行構造 |
| IK 設定 | `newton_route_env.py:895` (_solve_ik_batch) + `newton_skill_env_base.py:99-100` (IK_ITERATIONS_RL=30 / IK_STEP_SIZE=1.0) | A/C の cost 単位・config 軸 |
| substep 事前登録 | `COMP3_PLAN_ROUTEEXEC_GRASPACT_COORD_20260708.md` §2 (ISSUE-1、10→4 direction-UNKNOWN) / §13 (ISSUE-3) | 本日の診断で両方向確定 |
| 5tai verdict | `COMP3_LANEFLOOR_5TAI_VERDICT_RSTECHLEAD_20260710.md` (CC6-cond4 = AC env 床監査提案) | 併載 campaign 項目 |
| worlds≥1 | `WORLDS_FREEZE_INVESTIGATION_COORD2_20260710.md` §4 (dual-track + V0-V3 ladder + D-i..iv) | 併載 campaign 項目 |
| 本日の run chain | `39b206ddb0`→`65b5b9dd21`→`203f91594b`→`17365c922e`→`763e0e2f48`→`c2045a9a1a` | evidence grid の一次資料 (各 result JSON) |

## §1. Evidence grid — 本日 4 run (全て cell x0_y0、§運用30 単一 cell scope)

| run (commit) | floor | substep | 腕駆動 | L outcome | R outcome | 全体 |
|---|---|---|---|---|---|---|
| run-1 `13d37af1d5` | OLD (clip bug) | 4 | IK+chord | cage MISS (throat 下 +14.9mm) → lift 滑落 −42.5mm | 保持 (+23mm) | FAIL banked (Rs human-GT `6e0c7fe420`) |
| retry `17365c922e` | fixed | 4 | IK+chord | cage 成立、**axial pay −88.7mm**、rise −39.7mm | z −33.4mm、rise +16.1mm | NOGO、drop t=149 |
| sub10 `763e0e2f48` | fixed | **10** | IK+chord | 改善 (rise +19.3) だが axial pay 残存 (−60.7) | **true hold 回復** (z 3.9mm、rise +76.3) | NOGO (L)、完走 |
| armqdirect `c2045a9a1a` | fixed | 4 | **録画 arm_q 直接** | **完全回復** (lateral 0.03mm、rise +74.5) | 完全 (rise +77.1) | NOGO = 外挿 leg のみ; video: taut dual carry |

確定した機構分解: **floor clip = FIXED / ISSUE-1 (substep) = material・R 側支配 / ISSUE-3 (駆動経路) = L 側支配**。

## §2. 機構の定量注意 — capture は分岐点近傍 (packet の解釈上の鍵)

IK 駆動 (retry/確認計測) と録画経路の**測定可能な幾何差は全て sub-mm・左右対称**:
- claw park z bias: **−0.04mm** (確認計測)
- EE 姿勢差: park **≤0.094°** / descend 運動中 **≤0.097°** = claw 先端換算 **≤0.44mm** (probe leg Q、対称)
- EE 位置 chord 偏差 (10-frame 補間 vs 録画 per-frame): close/lift 全窓 **≤0.28mm**

にも関わらず armqdirect は L 結果を反転させた → **cage capture は sub-mm/sub-degree の駆動差で outcome が
flip する分岐点近傍のプロセス** (4-sub では特に; 10-sub は margin を広げ R を単独回復)。
**帰結: option A の効果は幾何解析からは予測不能 — 実測 probe でのみ実証可能** (§8)。

## §3. /diffik-trajectory 枠組み出力 (強制ゲート)

**移動量 (Step 1):** 録画 waypoint 移動 = 全 route max **11.39mm/step** (p99 11.24 / mean 1.37) → 現行 drive の
×10 分割で実効 **1.14mm/frame** = 判定 ✅ (≤2mm 局所線形域)。close 窓 max 2.24mm/step → 0.22mm/frame ✅✅。
option A の per-frame target も同 1.14mm/frame max ✅。D の feedforward は joint 空間直接 (録画実績値) ✅。

**補間方式 (Step 2):** 現行 = 非積算 absolute base + clip (time-based+velocity-clamp 正帰還 LL-TIM-003 の
構造なし)。A は target 密度を ×10 にするのみで方式不変。D は scripted 窓で補間自体を録画 joint feedforward
に置換 (armqdirect 実証済の機構そのもの)。

**DLS/damping (Step 3):** 本 env は DiffIK-DLS ではなく LM IKSolver (iterations=30, rot-weight 0.5,
jlimit 10, OPEN-finger warm start)。config 軸は §2 の通り実測で sub-degree — ただし分岐点近傍のため
config 差の影響は解析不能 (A 未実証 gap の実体)。

**THREAD 固有リスク (Step 4):** 全 option とも write-site は現行の kinematic joint_q overwrite で不変
(prohibited 制御 API 制約に非抵触)。D のみ fork-(iv) 契約に影響 (§5)。

## §4. Options 比較表 (cost = CPU probe 実測比、leg T; 効果 = §1 grid)

| option | 内容 | cost (throughput 対現行) | 効果 evidence | 未実証 (loud) |
|---|---|---|---|---|
| **A** per-frame base+IK | step_target を per-frame 化し毎 frame IK | **0.13×** (7.5× 遅、IK=現行 step の 72.3%) | **なし** — armqdirect は録画 arm_q そのものを使用 = **A の実証ではない** | per-frame IK 解 ≈ 録画 arm_q の等価性 (分岐点近傍で解析不能) → §8 A-probe 必須 |
| **B** substep 10 | RL drive を 10-sub (録画一致) | **0.75×** (25% 減) | **R = 実証済** (sub10) / 録画生成条件と一致 = ISSUE-1 軸消滅 | **L 未回復** (sub10 で L fail 残存) — 単独では不十分 |
| **C** A+B | 併用 | **0.13×** | 録画条件に最接近だが armqdirect と非等価 (IK 解 branch 残存) | A と同じ gap + 最高 cost |
| **D** hybrid | scripted phase = 録画 arm_q feedforward / residual 窓のみ IK+chord | **ρ=0: 3.61×高速 / ρ=0.25: 0.48×** | **feedforward 部 = armqdirect そのもの = 両腕実証済** | residual 窓の契約設計が必要 (§5); 窓境界の遷移挙動未検証 |

**cost 実測値 (leg T、CPU ratio; loud: production は warp/IK が cuda:0 — 比率近似、絶対値は ~1min GPU
micro-probe で確定可能・要請あれば実行):** t_IK=120.5ms / t_frame4=4.62ms / t_frame10=10.25ms →
current 166.7ms/step。**IK が現行 step の 72% を占める**ため A/C の ×10 IK が支配的 cost。

## §5. Trainer 段への含意 (fork-(iv) residual 契約)

- **A/B/C: 契約不変。** base = 録画 ee_pos waypoint (A は per-frame 化のみ)、residual = 加算、非積算
  (`newton_route_env.py:984-996`)。obs 意味論も不変。
- **D: 契約変更を伴う。** feedforward 窓では task-space residual の印加経路 (base+residual→IK) が存在しない
  → policy residual は窓内で不活性。設計案 (Rs 判断材料):
  - D-a: **stage 分離** — comp3 の scripted 検証 legs (G1-G6 DoD) は ρ=0 feedforward (実証済 harness =
    armqdirect、3.6× 高速)、trainer 段 (BC/DAgger) は別 option。fork-(iv) は trainer 段のみの契約なので
    scripted 検証段の feedforward 化は契約非抵触。
  - D-b: **窓付き trainer** — 把持 critical 窓 (descend~close~lift onset) は feedforward、それ以外は
    現行 IK+residual。DAgger の off-path 補正 (project-bc-copycat-offpath-dagger-lever) が窓内で不能に
    なる trade-off を E15/B_BC_BUILD_SPEC §10 と突き合わせる必要 → 独立設計ゲート案件。
- 注: BC 教師データ生成 (residual=0 経路) は D-a の feedforward と完全整合 (教師 = 録画経路そのもの)。

## §6. 併載 campaign 項目 (Rs packet 同梱、実装なし §運用24)

1. **worlds≥1 凍結 (COORD2 doc §4):** dual-track 推奨 (Track-1 = single-world × process 並列で即時
   unblock / Track-2 = GPU-mjwarp+cg 配管) + V0-V3 検証 ladder。**Rs 決定点 D-i..iv**: D-i dual-track 採否 /
   D-ii eq-gap disposition (mjw eq re-poke 起票 vs 不要 bank) / D-iii R3 trainer base-case = RLPD 小 n_env
   前提化 / D-iv 上流 newton CPU-multiworld TODO の watch 扱い。
2. **substep 4→N (campaign 級、SRG banked 規則):** sub10 の R 回復 + option B evidence がそのまま材料。
   B 採用なら本項は駆動経路決定に吸収される (同一変更)。
3. **AC env 床監査 (5tai CC6-cond4 提案):** `newton_approach_cable_mujoco_env.py:200` に同型
   EE_Z_FLOOR_KO 式 — route env で実証された latent-defect class の水平展開監査を別タスクとして提案。

## §7. 未実証 gap + falsification tests (loud、§運用30)

- **A-probe (~6min GPU、要 GO):** G1 harness で step_target を per-frame 化 (probe-level) → L 回復すれば
  A 実証、しなければ A/C 除外で D/B に収束。分岐点近傍性 (§2) により**これ以外に A を実証する方法はない**。
- **D 窓境界遷移 (~6min GPU、要 GO):** feedforward→IK 切替 frame での関節不連続の有無 (切替時の
  jq 整合は設計で吸収可能だが未検証)。
- **81-cell 一般性:** 本日の全 evidence は cell x0_y0 のみ。option 決定後の受入は tail-cell を含む
  sweep が必要 (comp3b DoD⑦ 系列と接続)。
- **GPU 絶対 cost:** leg T は CPU 比率 — 絶対 steps/s は cuda:0 micro-probe で確定可能 (surfaced)。

## §8. COORD 推奨 (参考、決定は Rs)

- **comp3 の scripted 検証段 (G1 再判定〜G6):** **D ρ=0 (純 feedforward)** — 実証済 (armqdirect =
  同一機構)・最速 (3.61×)・契約非抵触 (fork-(iv) は trainer 段の契約)。
- **trainer 段:** まず **A-probe (~6min) を実行して A/C の生死を確定**させてから決定するのが最小後悔:
  A 生存なら A (契約不変で録画忠実) vs B の cost 比較 (0.13× vs 0.75×) を Rs 判断、A 死亡なら
  **B + D-b 窓設計** の組が残る。B は単独で L を救わない (sub10 実証) ため B 単独案は非推奨。
