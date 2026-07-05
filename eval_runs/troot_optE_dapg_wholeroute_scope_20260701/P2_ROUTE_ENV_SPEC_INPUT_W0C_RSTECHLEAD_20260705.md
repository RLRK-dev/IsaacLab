# P2 whole-route env — DESIGN-GATE SPEC-INPUT (W0-c) — 両枝並記

**Author:** RS-TECH-LEAD (%12). **Date:** 2026-07-05 09:2x JST → **v1.1 09:3x (%9 9-lens cross-PV = CONCUR-W-CORRECTIONS 09:28、8 修正 [E-1/E-2/D-1/H-1 + 精緻化 4] 全反映; %9 diff 再確認 = 8/8 PASS・9-lens 全 PASS 09:43)** → **v1.2 09:5x (/reward-design 4 成果物 DRAFT 発行に伴う 2 訂正: §運用22 算術 225 + β curriculum 必須)** → **v1.3 10:1x (pre-check = BLOCK 10 issues [`logs/pre-check-log.jsonl` 10:04] 全反映、artifacts v1.1 連動 — pre-check 再走が 5体 の前提)**. **Charter:** JOINT-DECIDED [2] (banking `231639c0d1`、Rs 標準権限 08:5x)。
**Status:** PAPER-ONLY / 0-build / 0-commit(本 doc は W0-c 審議物)。**env/reward/DR/UNIT = Rs 専権** — 本 doc は design-gate (`/reward-design`+`/pre-check`+5体) への INPUT であり決定しない。R2b 方向 = working assumption (un-park 正式決定 = 本 gate で Rs)。
**cross-PV:** %9 9-lens checklist (09:08) を本 doc の受入基準として採用 — 各 § に lens 対応を明記。

## §0. Grounding (増分のみ — 基底 = devplan v1.1 §0 を参照 [reference-over-copy])

| Anchor | Cite | 使用 fact |
|---|---|---|
| P2 v1 設計 (PARKED) | `P2_REWARD_DESIGN.md` §0-§8 | 49D/12D residual 案 + §運用21 held_cable_z fix (正) + 6-phase 縮約 + reward 8 成分案 + Q1-Q7 |
| pre-check BLOCK 全文 | `P2_PRECHECK_CROSSPV_OPSSUP.md` §1-§5 | 10 issues (CRIT1 phase-advance / CRIT2 demos / HIGH3 anti-hover / HIGH4 seat-ori / HIGH5 rot-inert / HIGH6→CRIT env-absent / MED7 horizon / MED8 seated-seg / MED9 retention authority / MED10 auto-close) + M-A..M-E + **M-C: base は sim 完全状態で argmin-follow するため position-DR を既に無効化 = residual の DR 吸収は redundant** + conservatism 表 |
| canonical demo 実測 | LEDGER row44 (`fd005ab83f`) | **T=7707 physics frames** (whole C1→C2、cadence 10) → **~771 RL steps** = horizon 導出の一次データ |
| B2 contract | `route_demo_to_bc.py:286,415,883` (via DQ7:20) | 27D obs / 6D abs-target / label = next-waypoint |
| oracle 照会実体 | DECIDE `170b905575` | per-step relabel + per-episode settle re-center + in-scene IK (thin-const-relabel = 偽) |
| oracle 有効性 | DQ7:57-61 (Fact A/B) + :106 | EE-restoring = 全 phase 有効 / cable-state 再導出 = 2 点のみ → **frozen-waypoint phase では state-blind** |

## §1. 決定構造 (lens I) — この gate で Rs が決めること

**D-C 本体 = UNIT の再選択 (DQ1=B の後継)**: B (pure BC 系) は R0-R1 で測定済み (plateau/発散) → 本 gate で **branch α vs β (± 併用順序)** を決定。旧 Q1-Q7 は本 doc §3-§5 の named-design-Q に承継 (対応表 §3 末尾)。

## §2. 両枝 decision-grade 並記 (lens A — 4 分岐点)

**α = R2b: residual-on-frozen-script** (PARKED-A の un-park 候補; ResiP 系譜) / **β = R2a′: canonical-DAPG on B2-contract** (DQ7:102 banked escalation; policy が abs-target を直接出力、script は demo/BC 項 + oracle として関与)。

| 分岐点 | α residual | β canonical-on-B2 |
|---|---|---|
| **F1 contract** | 12D EE-delta residual (+auto-close predicate)。**HIGH5 再輸入** (rot 6D は G7 で near-inert + demo rot-delta ≡0) → **sub-option α-6D: position-only 6D residual** = HIGH5 moot 化、G7 は base-ori 依存を明示 (HIGH4 と同根) | 6D abs-target (B2 実証済 contract、fork-(iv) ADOPTED と同型)。HIGH5/MED10 = **moot by construction** (DQ7:102)。obs は §4 v2 に拡張 (27D→~52D) — **B2 の 27D で測った OG 検証状態は obs 拡張でも RESET** (devplan §4.3-a と同じ扱い) |
| **F2 CRIT1 phase-clock** | base が clock を所有 (script-schedule)。**named-design-Q α-PC: 逸脱時の re-sync 規約** — (a) 無条件 march (B1 型 desync risk) / (b) 逸脱>閾値で base pause + oracle 再照会 / (c) phase-predicate 到達で advance (hybrid)。推奨 = (b) 系だが **決定 = Rs** | phase = **agent-earned predicates** (CRIT1 の fork を予測子側で解消 — r_phase は「preserve」でなく「earn」になる = pre-check CRIT1 の直接 fix)。predicate 集合 = §4 reward と共通。⚠ risk (%9): predicate 正しさが reward と phase 進行の**結合単一障害点** (誤 predicate = episode deadlock) → 緩和 = **canonical demo に対する predicate unit-test (6 phase 全てが記録 frame で fire) を env DoD に**。⚠ v1.2 (reward-artifacts DRAFT): **β は curriculum が必須要素** — BC-init 閉ループの G3 以深 fire P≈0 リスク (b1p5 近傍証拠) により、curriculum 無しは G3+ DEADLOCK。⚠ v1.3 機構 pin (pre-check HIGH): **推奨 = script-run-to-phase-k 方式** (env が script を phase k まで実行して handover — DR-consistent・資産即応; β にも base 機構を再輸入する cost = §7 計上、α/oracle と共通部品化可)。npz-restore 代替は recorder に **qvel 無し (grep 実測 0)** → 全 MuJoCo state 拡張 + restore-fidelity DoD が前提。付帯: 開始 mix {P0, G1/G2−ε, G3−ε, G4−ε, G5−ε} / **評価 bar = from-P0 のみ** (分布 mismatch guard) / 中途開始の gate 簿記 (既通過 = earned-without-bonus) / oracle settle-center = stored 値 (mid-route 開始対応)。v1.3 で α にも必須機構 (oracle corner-relabel) が付いたため**複雑度差は縮小 — 対称な必須機構の比較として D-C へ** |
| **F3 Δ 非累積契約** | **必須 hard 要件**: Δ = base の絶対 target への per-step offset (積分しない) + `Δ=const → drift=0` regression test = env DoD (devplan §6-9; 既存 12D delta は accumulates `newton_approach_cable_mujoco_env.py:40` — そのまま流用禁止) | N/A (abs-target は構成上非累積 — B1′ P2a で実測済: spike 433mm→re-anchor 9-16mm) |
| **F4 OG 計器** | **port + composite 導出 + 再検証が前提** (composite base(t)+Δ(obs) は Δ→0 で γ⊥ 偽 GO 縮退 — devplan §4.3-b) → §6 work item 完了まで OG canary 非適用 | obs 拡張 re-validation のみ (probe 軸は abs-target head に直接適用可) — **計器適合は β が軽い** |
| **学習対象の実質 (M-C 接地、%9 補正で evidence-gate 化)** | ⚠ M-C 原文「sim 完全状態 + position-DR では residual 最適 ≈ 0」は **base 成功域では真・全域では偽** (%9 CHALLENGE): CP-C 実測で base は ±20mm grid の **4/18 task-FAIL** (seat 2 + R_MISS 2) = position-DR でも base-failure corner に physics-generated 学習信号が既存 (base-FAIL→SUCCESS 化 = R2b bar の定義そのもの)。α の学習信号 option = **(a) 摂動注入 training-DR ((ii) kick 転用) / (b) obs-noise・estimated-pose DR (`task_config.py:257-262`) / (c) retention margin・timing / (d) position-DR-only (base-failure corners を信号源に)** — **decider = P3 script-SR-over-DR-grid 検収を evidence-gate 化 (pre-register: base-DR-SR ≥95% → corner 稀 = M-C bites = (a)/(b) 必須 / ≤80% → (d) で開始可 / 中間 = Rs 判断; **counting rule を P3 前に pin [pre-check ISSUE 7]: per-offset unique + 決定論的 re-run は 1 扱い → 現推定 13/16=81.3% [run-level だと 77.8% で境界が flip するため] — 境界隣接ゆえ P3 実測が decider**)** — **named-design-Q α-DR = Rs (evidence 付きで)**。⚠ v1.3 (pre-check CRIT): **(d) 単独でも corner 補正列が PPO batch に自然発生する保証はない** (非累積 Δ + zero-mean 探索は経路を random-walk しない / BC 項は Δ≡0 prior / Δ bound 未導出) → **α の必須機構 = oracle corner-relabel/proposal (§5 oracle の消費者に追加) + Δ bound 導出 (P3 corner-miss magnitude 実測から)** — β の curriculum と**対称の必須要素**として D-C 表に計上 (必須機構なしの構成は両枝とも選択肢にしない) | policy が全 following/restoring を自前供給 (B2 で測った gap そのもの) → 学習信号は自明に非自明。ただし whole-route from-BC-init の exploration 負荷 = PPO sample 食い (devplan §5-R2a 弱点) |
| **R3 接続** | residual を off-policy 化 (arXiv:2509.19301 系譜) or R3 で abs head に乗換え | **そのまま R3 の既定 actor 形態** (devplan §5-R3-3) — 接続が最短 |
| **費用差** | oracle API は共通。α 固有 = Δ 契約 + composite OG 導出 | β 固有 = obs 拡張 converter 再変換 (資産済、~100-200 LOC) |

**%12 所見 (推奨ではなく整理):** α の売り (copycat 構造回避) は M-C により「sim 完全状態では学習対象が痩せる」制約と対で成立する — α を採るなら α-DR の摂動注入/obs-noise が実質必須。β は計器・contract・R3 接続で軽いが、whole-route exploration を PPO で払う。**併用順序 (α→β / β→α / β-only / α-only) を含め Rs 決定。**

## §3. P2-BLOCK 15 項 disposition 表 (lens B — silent drop なし)

| issue | disposition | 根拠/先 |
|---|---|---|
| CRIT1 phase-advance | **named-design-Q** (F2、両枝で解が異なる) | §2-F2 |
| CRIT2 demos absent | **RESOLVED** (recorder `fd005ab83f` + B2 demo set; 契約統一後に converter 再変換) | §4-obs |
| HIGH3 anti-hover | **mitigated-by-design + named-design-Q**: reward は sparse-primary (dense 正項を初期不採用) → mid-episode 正 basin を構造回避。dense 項を後日入れる場合は phase-aware R_PENALTY 較正を条件化 | §4-reward |
| HIGH4 seat-ori cos>0.85 | **named-design-Q (旧 Q5)**: 初期 success から ori 節を **外す** ことを提案 (base-route が ori を供給、G7 未解決のまま gate しない; 位置 + seat/pin predicates + retention で定義) — 復活条件 = G7 解決後。⚠ **α-12D 選択時は rot dims が live → ori 節再検討** (§2-F1 G7 cross-ref) | §4-success |
| HIGH5 rot near-inert | **branch 依存**: β/α-6D = moot / α-12D = 再輸入 | §2-F1 |
| HIGH6 / M-A env absent | **本 spec の主題** (build 対象そのもの; imperative→MDP 再表現の項目列挙 = §5) | §5 |
| MED7 horizon 未導出 | **RESOLVED-by-derivation**: canonical T=7707 frames ÷ cadence 10 = **771 RL steps** → `ROUTE_TERMINAL_STEPS = 900` 提案 (×~1.17 margin、DR 下で再実測を smoke DoD に)。旧 400 案は**不足**だった。time_outs = timeout のみ (純度不変) | §4-termination |
| MED8 seated-seg obs | **ADOPT**: 専用 seated-seg index を obs に追加 (R-clamp-nearest の ~44mm off を排除) | §4-obs |
| MED9 retention authority | **honest-carry (旧 Q4)**: retention は base-scheduled (α) / scripted-predicate (β) — **policy に retention 権限を渡さない** (渡す = INVARIANT#4 接触 = premise-Q)。held_cable_z obs fix は両枝 ADOPT (設計正) | §4-obs |
| MED10 auto-close 誤記 | **RESOLVED (記述訂正)**: close = scripted 2-phase servo predicate、action に gripper 次元なし (B contract 整合) | §4-action |
| M-B W_ORI regression | **moot-under-sparse** (dense ori 項なし)。dense 復活時 = 0.75+W_TAIL 条件 | §4-reward |
| M-C DR redundancy | **昇格 → §2 学習対象行 + named-design-Q α-DR** (本 spec の中心論点の一つ) | §2 |
| M-D 88mm span @SEAT | **ADOPT**: env assert (REGRASP_SPAN_MAX=0.088 pattern `newton_aerial_regrasp_mujoco_env.py:306`) を SEAT まで全 phase 適用 | §4-guards |
| M-E mujoco backend | **ADOPT**: env DoD assert (Grip VBD-residue 先祖返り guard) | §4-guards |
| (新) B1 apply-path 積分 | **ADOPT**: F3 非累積契約 + drift-zero regression | §2-F3 |

旧 Q1-Q7 承継: Q1=§1 / Q2=本 spec / Q3=RESOLVED / Q4=MED9 行 / Q5=HIGH4 行 / Q6=MED7 行 (900 提案) / Q7=inter-arm collision → **named-design-Q (未解決のまま)**: AC は collision sphere を落とし、arm-arm OVERLAP は確定済 (map :212 系 AC 行) → route env での扱い (re-enable + penalty vs reach-terminate のみ) = Rs。

## §4. env 仕様 core (lens C/E — devplan §6 12 項を実体化)

- **obs v2 (統一 contract、~53D 案):** `[0:42]` AC/AR 基底 (current-target-clip 化含む) + `[42:48]` phase one-hot(6) + `[48]` held_cable_z (§運用21) + `[49]` seated-seg d (MED8) + `[50]` **within-phase progress scalar** (CC2-2: oracle/TD の Markov 性) + `[51:53]` next-clip xy (whole-route 一般化用; 5-clip 拡張前方互換)。**§運用21 照合表 = artifacts v1.1 §A8 に納品済** — 結果: grip-contact (G1/G4 入力) と reach-fail terminate に obs 対応なし → **obs v2.1 = 57D 案** ([53:55] per-arm contact flag + [55:57] per-arm IK-residual; 採否 = design-gate Q)。
- **action:** 両枝 §2-F1。gripper = predicate (次元なし)。
- **reward (sparse-primary 案、/reward-design の入力):** phase-completion predicates (C1 seat / pin fire / C2 regrasp gate = 既存 verdict 機構流用) + 終端 category-SUCCESS + time −0.01/step + terminates (explosion/drop/span 逸脱/reach-fail)。**§運用22 検算 (v1.2 訂正)**: 正 budget = **5×5 (G1-G5 phase) + 200 (G6 task) = 225** / 罰累積最悪 = 0.01×900 + 10 = 19 → **ratio 1:11.8 健全**。anti-hover: sparse ゆえ hover 正項なし; time penalty が hover を単調に罰する。**4 成果物 DRAFT = `P2_REWARD_ARTIFACTS_W0C_DRAFT_20260705.md`** (G1-G6 predicate 集合 + ground-truth 値 + 単調 attempt-incentive 性質 [2×R_PHASE ≥ TERM_PEN] + branch 別 reachability)。
- **success (提案):** 位置系 predicates (cable-C2 groove < 3mm + seat predicates sustained K=10) ∧ ¬dropped ∧ span-guard 全 phase PASS。**ori 節なし** (HIGH4 disposition; 復活条件明記)。
- **termination/time_outs:** done = success ∨ timeout(900) ∨ explosion ∨ drop ∨ reach-fail ∨ span-violation; `time_outs` = timeout のみ。
- **DR hooks:** XY±20mm (既定 ON は Rs) + α-DR 摂動注入 hook ((ii) kick 機構転用、flag-gated) + obs-noise 軸 (Rs spec 待ち) — **全て config 化、既定 OFF**。
- **determinism/band:** seed 固定 + nomA/nomB band 計測 mode を env 標準機能に。
- **transition export / off-policy-ready (E-1、devplan §6-4):** replay 互換 (o, a, r, o′, done, phase, info) の完全記録 export を env 標準機能に — R3 (RLPD replay) の前提資産、設計時は安価・後付けは高価。
- **reward 成分ログ分離 (E-2、devplan §6-5):** 全 reward 成分を per-step 分離ログ (診断・§運用22 事後検算・hacking 検出用)。
- **smoke DoD:** throughput steps/s + device parity (cuda:0 pinned vs cuda:2) + **cg-GPU whole-route screen** (P1 carried) + horizon 実測 (DR 下分布; **pre-register: DR±20 の episode-length p99 > 810 なら 900 を bump**) + Δ=const drift-zero (α) + **predicate unit-test (canonical demo で 6 phase 全 fire、@cuda:0 pin — route は device-fragile)** + **curriculum handover-fidelity test (β: script-run-to-phase-k の handover 点で状態連続性を band 内確認)** + **corner-miss magnitude 分布計測を P3 grid に同梱 (α の Δ bound 導出材料 c1)**。
- **guards (v1.3):** ⭐ **action-path の per-arm clamp/rate-limit 禁止 — スケーリングは全て common-mode (単一係数を両腕に適用) とし INV#2 を as-executed で保護** (mini-test 5体 CRIT1 の恒久 carry: per-arm 独立 clamp は off-path で非対称 scale → span 破壊、%9 c3) / span assert = **92.4mm achieved-coupling 中心 + P3 分布導出 window** (banked INV#2 ruling `DQ7_DAGGER_BUILD_SPEC_V2_MINIMAL_COORD2.md:71` — 88±5 は誤中心 [margin 0.6mm]; commanded-88 の INVARIANT 主張は span-PRESERVATION 判定として分離) / mujoco backend assert / arm-arm collision = named-design-Q (旧 Q7) / **不可勝 draw class 方針 = design-gate 項** (R_MISS 幾何: bow-chord 112mm > span 窓 → 局所 fix が span-guard 禁止側。選択肢 = truncate-無-penalty / DR-support 除外+limitation 文書化 / Rs-Q。**SR 上限 <100% を campaign bar に反映、draw での selective-hover は期待挙動として記録**)。

## §5. oracle API (lens D — 重量級、独立 cost 行)

| 決定項 | 内容 | 案 |
|---|---|---|
| 照会実体 | per-step relabel + settle re-center + in-scene IK (`170b905575` floor — waypoint lookup ではない) | 専用 module (~300-500 LOC) + 自前 [VERIFY] |
| mid-servo 返り値 | interp 中の中間 target か phase 終端 target か + **ACHIEVED-vs-COMMANDED 規約 (D-1、%9 catch)** | **中間 target、規約 = converter label と同一系 (`route_demo_to_bc.py:287` 準拠; 逸脱するなら正当化必須 — 07-04 demo-replay repr-mismatch 教訓: oracle 規約 ≠ training label 規約 = 系統 bias)** — design-gate 決定項 |
| phase-clock | §2-F2 と同一 fork (α: 規約 (b) 推奨 / β: predicates) | Rs |
| state-blind mask | phase 別 validity mask を API が返す (Fact A/B: EE-restoring 全 phase 有効 / cable-target 有効 = 2 点のみ) — 消費側 (IBRL proposal / relabel) が mask で重み付け | ADOPT |
| 消費者 | R3 IBRL proposal / DAgger relabel (**α corner-relabel 含む**) / R4(b) oracle-guided | 共有資産として一度だけ build |
| **named milestone (c2、%9 pre-register)** | oracle 稼働後に **A-vs-B 解決 probe** を実施 — state-feedback expert は機構 C (state-blind label aliasing / covariate-shift-under-feedforward-supervision) を除去し A (budget-tension) を可測化する。**de-risk の monotone-DIVERGENCE 自体が C 由来の可能性があり、C なら A-vs-B は dissolve** | R1 close 時の banked impossibility の解決先 |

## §6. OG 計器 work item (lens F precondition)

port (obs v2 契約) + composite γ⊥/seg-follow 導出 (α 用) + 再検証 (B1′/B2 相当の 2× 検証を新契約で再取得) — **完了まで OG canary を R2 abort 規則に使わない** (devplan §4.3 precondition を abort 条項自身に明記)。band α/β/γ 再較正 = Rs (W0-a′ packet 同梱)。

## §7. cost / LOC (lens: 実勢 anchor)

| item | LOC 実勢根拠 | est |
|---|---|---|
| env 本体 | AC 1278 / AR 1677 / Grip 1798、base 2109 再利用 | **1.5-2.5k** |
| oracle API | relabel+IK floor | 300-500 |
| converter 再変換 (obs v2.1) | 資産済 branch | 100-200 |
| curriculum 機構 (β: script-run-to-phase-k) | base 実行部 = oracle/env と共通部品化 | 100-300 |
| OG port+composite | 既存 og_offline_gate 拡張 | 200-400 |
| smoke 一式 | 既存 harness 流用 | 100-200 |
| 計 | | **~2.3-4.1k LOC、W1-3/4 wall (gates 込み)** |

## §8. conservatism + carried risks (lens H — %9 §5 表を承継)

base perfect-state targeting = 実機非保守 / retention row56 NEEDS-DUAL = FUNDAMENTAL carry / 3mm groove = 剛体 clip 非保守 / ori 無 gate 化 = 実機前に G7 再訪必須 / GPU whole-route = 未 screen (smoke で) / §4 horizontal curvature = KINEMATIC 境界 (学習成果はこの fidelity 内) / **reach 0.9mm fragility (P1 carried、H-1)**: R re-grasp reach margin 0.9mm + device-fragile (cpu 83.2mm BLOCK vs cuda:0 0.9mm) = R_MISS corner の物理源 — smoke device-parity + P3 script-SR-over-DR-grid が定量化。

## §9. gates / next (lens G/I)

1. 本 spec → **%9 9-lens cross-PV = CONCUR-W-CORRECTIONS (09:28、blocker なし)** → 8 修正反映済 (v1.1) → %9 diff 再確認 (軽量)。
2. `/reward-design` 4 成果物: **spec 段階は assumption-labeled draft、env CPU-smoke 後に実測で再 discharge** (M-A 教訓: env 不在での「PASS」を主張しない)。
3. `/pre-check` (v1.0→**BLOCK 10 issues** → v1.3/artifacts-v1.1 で全反映 → **再走要**) → 5体 [VERIFY] (env=L3) → **Rs W0-a′ packet** = {D-C 両枝決定 [対称必須機構: α=oracle corner-relabel / β=curriculum 込み] + named-design-Q 群 (α-PC/α-DR/Q7/HIGH4 節/horizon 900/band α/β/γ/**不可勝 draw 方針/obs v2.1 57D/counting rule per-offset**) + §4.3 数値閾値 pin 3 点 + **P4 credit-assignment pre-registration (γ≥0.995 or 正当化 / GAE λ / envs×steps / corner-episodes 下限 — HIGH-COST-GATE 前必須)**}。
4. Rs 承認後にのみ build (L3 chain + 層5 + cross-PV)。

*%12 — 2026-07-05。PAPER-ONLY。INVARIANTS 不触。*
