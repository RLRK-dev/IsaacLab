---
doc_class: reference
---

# P2 whole-route env — DESIGN-GATE SPEC-INPUT (W0-c) — 両枝並記

**Author:** RS-TECH-LEAD (%12). **Date:** 2026-07-05 09:2x JST → **v1.1 09:3x (%9 9-lens cross-PV = CONCUR-W-CORRECTIONS 09:28、8 修正 [E-1/E-2/D-1/H-1 + 精緻化 4] 全反映; %9 diff 再確認 = 8/8 PASS・9-lens 全 PASS 09:43)** → **v1.2 09:5x (/reward-design 4 成果物 DRAFT 発行に伴う 2 訂正: §運用22 算術 225 + β curriculum 必須)** → **v1.3 10:1x (pre-check = BLOCK 10 issues [`logs/pre-check-log.jsonl` 10:04] 全反映、artifacts v1.1 連動)** → **v1.4 10:2x (%9 cross-PV CONCUR-W-1-CORRECTION 10:19 反映: c3 oracle 役割 re 帰属 [drift-recovery 教師 / c2-sized 局所 RL = primary / 超過 = draw 会計] + obs v2.1 冒頭整合 — pre-check 再走: 10:36 WARN → fixes → spot-diff PASS、`logs/pre-check-log.jsonl` 3 entries)** → **v1.5 11:0x (env-spec 5体 [CC2 FAIL→fix / CC3・CC4・CC5 PASS-w-fixes / NHA sequencing-HOLD] 全 ACCEPT 反映 + %9 f1/f2 + common-mode 原則昇格 + P3-grid 前倒し JOINT [PREREG banked])**. **Charter:** JOINT-DECIDED [2] (banking `231639c0d1`、Rs 標準権限 08:5x)。
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
| **F2 CRIT1 phase-clock** | base が clock を所有 (script-schedule)。**named-design-Q α-PC: 逸脱時の re-sync 規約** — (a) 無条件 march (B1 型 desync risk) / (b) 逸脱>閾値で base pause + oracle 再照会 / (c) phase-predicate 到達で advance (hybrid)。推奨 = (b) 系だが **決定 = Rs** | phase = **agent-earned predicates** (CRIT1 の fork を予測子側で解消 — r_phase は「preserve」でなく「earn」になる = pre-check CRIT1 の直接 fix)。predicate 集合 = §4 reward と共通。⚠ risk (%9): predicate 正しさが reward と phase 進行の**結合単一障害点** (誤 predicate = episode deadlock) → 緩和 = **canonical demo に対する predicate unit-test (6 phase 全てが記録 frame で fire) を env DoD に**。⚠ v1.2 (reward-artifacts DRAFT): **β は curriculum が必須要素** — BC-init 閉ループの G3 以深 fire P≈0 リスク (b1p5 近傍証拠) により、curriculum 無しは G3+ DEADLOCK。⚠ v1.3 機構 pin (pre-check HIGH): **推奨 = script-run-to-phase-k 方式** (env が script を phase k まで実行して handover — DR-consistent・資産即応; β にも base 機構を再輸入する cost = §7 計上、α/oracle と共通部品化可)。npz-restore 代替は recorder に **qvel 無し (grep 実測 0)** → 全 MuJoCo state 拡張 + restore-fidelity DoD が前提。**実装 fork 3 択の明示 (v1.5、CC3-CH3 — 100-300 LOC は wrapper のみの価格だった): (a) vectorized per-step script controller = M-A 再表現そのもの (大、route-executor 抽出 §7 が前提) / (b) ⭐ precomputed phase-k state-bank = 推奨 working assumption (live state は qvel を持つ; 帰結 = DR が bank cell に量子化 — 文書化; pin ③ resample と整合; multiworld 同時 step 制約 [Newton は全 world 一斉 step] と両立する唯一の AC-reset-pattern 互換案) / (c) synchronized batch reset = 不採用 (early-finisher の loose-cage creep 汚染)。prefix 物理 overhead (G5−ε ≈ 7000 frames/収集 ~1500) を throughput smoke に計上。**付帯: 開始 mix {P0, G1/G2−ε, G3−ε, G4−ε, G5−ε} / **評価 bar = from-P0 のみ** (分布 mismatch guard) / 中途開始の gate 簿記 (既通過 = earned-without-bonus) / oracle settle-center = stored 値 (mid-route 開始対応)。v1.3-4 で α にも必須機構 (3 点: drift-recovery relabel + c2-sized 局所 RL + draw 会計) が付いたため**複雑度差は縮小 — 対称な必須機構の比較として D-C へ**。⚠ prefix RL 会計 3 pin (pre-check N3): ①scripted-prefix transitions は PPO batch から**除外** (script action ≠ policy action) ②time-penalty clock と 900 horizon は **handover 起点** (from-P0 ground-truth 表と整合) ③prefix が phase k 未達 (corner/draw offset) 時の規約 = **resample** (silent skew / generator stall 防止) — handover DoD に含める |
| **F3 Δ 非累積契約** | **必須 hard 要件**: Δ = base の絶対 target への per-step offset (積分しない) + `Δ=const → drift=0` regression test = env DoD (devplan §6-9; 既存 12D delta は accumulates `newton_approach_cable_mujoco_env.py:40` — そのまま流用禁止) | N/A (abs-target は構成上非累積 — B1′ P2a で実測済: spike 433mm→re-anchor 9-16mm) |
| **F4 OG 計器** | **port + composite 導出 + 再検証が前提** (composite base(t)+Δ(obs) は Δ→0 で γ⊥ 偽 GO 縮退 — devplan §4.3-b) → §6 work item 完了まで OG canary 非適用 | obs 拡張 re-validation のみ (probe 軸は abs-target head に直接適用可) — **計器適合は β が軽い** |
| **学習対象の実質 (M-C 接地、%9 補正で evidence-gate 化)** | ⚠ M-C 原文「sim 完全状態 + position-DR では residual 最適 ≈ 0」は **base 成功域では真・全域では偽** (%9 CHALLENGE): CP-C 実測で base は ±20mm grid の **4/18 task-FAIL** (seat 2 + R_MISS 2) = position-DR でも base-failure corner に physics-generated 学習信号が既存 (base-FAIL→SUCCESS 化 = R2b bar の定義そのもの)。α の学習信号 option = **(a) 摂動注入 training-DR ((ii) kick 転用) / (b) obs-noise・estimated-pose DR (`task_config.py:257-262`) / (c) retention margin・timing / (d) position-DR-only (base-failure corners を信号源に)** — **decider = P3 script-SR-over-DR-grid 検収を evidence-gate 化 (pre-register: base-DR-SR ≥95% → corner 稀 = M-C bites = (a)/(b) 必須 / ≤80% → (d) で開始可 / 中間 = Rs 判断; **counting rule を P3 前に pin [pre-check ISSUE 7]: per-offset unique + 決定論的 re-run は 1 扱い → 現推定 14/17=82.4% 〔11:52 訂正: 旧 13/16=81.3% は集計誤り、%9 凍結 parser の PRIOR 較正 (18→17 unique) で確定・枝判定不変〕 [run-level だと 14/18=77.8% で境界が flip するため] — 境界隣接ゆえ P3 実測が decider**)** — **named-design-Q α-DR = Rs (evidence 付きで)**。⚠ v1.3 (pre-check CRIT): **(d) 単独でも corner 補正列が PPO batch に自然発生する保証はない** (非累積 Δ + zero-mean 探索は経路を random-walk しない / BC 項は Δ≡0 prior / Δ bound 未導出) → **α の必須機構 (v1.4 = %9 CORRECTION 1 反映) = (i) oracle drift-recovery relabel (base 近傍逸脱の復帰教師 — ⚠ oracle は script-faithful で base-FAIL corner の beyond-script 補正は教えられない [機構 C と同型の限界を P2 に一貫適用]) + (ii) **structured-common-mode 探索による c2-sized 局所 RL 発見 = conditional-PRIMARY** (v1.5、CC2-CRIT fix: per-arm 独立 σ は span-noise で即 terminate [σ=7.5mm 既定は致死]、生存 σ≤~2mm では miss>3mm の p_hit ≈ 0 — **c2 は「表現可能」を作るが「発見可能」を作らない**。条件 = ①noise covariance を common-mode 主体に構造化 [原則 0、differential σ≈0] ②**p_hit(m; σ, W, window) 事前計算を discharge に追加** [c1 miss 分布 + CPU step-response で W 較正; GO bar 案 = E[discoveries/update] ≥ 1] ③**corner-mask** [P3 分類 cell 上で Δ≡0 anchor と drift-recovery relabel を mask — 両者は corner fix と衝突する持続力] ④corner/draw 境界 = discovery-feasibility で確定 [c2 被覆でなく]) + (iii) 発見不能域の miss = draw-class 会計** — β の curriculum と**対称の必須要素**として D-C 表に計上 (必須機構なしの構成は両枝とも選択肢にしない)。**α trainer 統合 (CC2-CH3、v1.5 で仕様化): 交互 aux imitation update** (relabeled (obs,Δ*) は別 buffer、phase-mask + corner-mask 重み; λ_relabel / anchor decay 選択 = P4 pre-reg 追加項; §7 cost 行) | policy が全 following/restoring を自前供給 (B2 で測った gap そのもの) → 学習信号は自明に非自明。ただし whole-route from-BC-init の exploration 負荷 = PPO sample 食い (devplan §5-R2a 弱点) |
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
| MED9 retention authority | **honest-carry (旧 Q4)**: retention は base-scheduled (α) / scripted-predicate (β) — **policy に retention 権限を渡さない** (渡す = **NO-KINEMATIC-TRICK [INV #5] 接触** = premise-Q; v1.5 renumber — pin 例外は #5 の唯一の authorized exception)。held_cable_z obs fix は両枝 ADOPT (設計正) | §4-obs |
| MED10 auto-close 誤記 | **RESOLVED (記述訂正)**: close = scripted 2-phase servo predicate、action に gripper 次元なし (B contract 整合) | §4-action |
| M-B W_ORI regression | **moot-under-sparse** (dense ori 項なし)。dense 復活時 = 0.75+W_TAIL 条件 | §4-reward |
| M-C DR redundancy | **昇格 → §2 学習対象行 + named-design-Q α-DR** (本 spec の中心論点の一つ) | §2 |
| M-D 88mm span @SEAT | **ADOPT**: env assert (REGRASP_SPAN_MAX=0.088 pattern `newton_aerial_regrasp_mujoco_env.py:306`) を SEAT まで全 phase 適用 | §4-guards |
| M-E mujoco backend | **ADOPT**: env DoD assert (Grip VBD-residue 先祖返り guard) | §4-guards |
| (新) B1 apply-path 積分 | **ADOPT**: F3 非累積契約 + drift-zero regression | §2-F3 |
| (v1.5 注記) M-D span assert | pattern-only の流用 — **assert の中心値/scope/tier は §4 guards v1.5 が正** (dual-grip 限定・informative 既定; 本表の旧 0.088 文言を根拠にしない) | §4-guards |

旧 Q1-Q7 承継: Q1=§1 / Q2=本 spec / Q3=RESOLVED / Q4=MED9 行 / Q5=HIGH4 行 / Q6=MED7 行 (900 提案) / Q7=inter-arm collision → **named-design-Q (未解決のまま)**: AC は collision sphere を落とし、arm-arm OVERLAP は確定済 (map :212 系 AC 行) → route env での扱い (re-enable + penalty vs reach-terminate のみ) = Rs。

## §4. env 仕様 core (lens C/E — devplan §6 12 項を実体化)

**⭐ 恒久原則 0 (common-mode decomposition — 2026-07-05 同型事故 3 件の収束 [INV2-ruling relabel / mini-test CRIT1 rate-limit clamp / env-spec CC2 探索ノイズ]、%9 提案・%12 採用): dual-arm pair 量に作用する全機構 (exploration noise / clamp・rate-limit / relabel / 将来の obs-DR 等) は common-mode + differential に分解して設計し、differential 成分は明示設計 + 正当化なしに導入しない。**

- **obs v2.1 (統一 contract、57D 案 — v2 53D から §A8 照合で改訂):** `[0:42]` AC/AR 基底 (current-target-clip 化含む) + `[42:48]` phase one-hot(6) + `[48]` held_cable_z (§運用21) + `[49]` seated-seg d (MED8) + `[50]` **within-phase progress scalar** (CC2-2: oracle/TD の Markov 性) + `[51:53]` next-clip xy (whole-route 一般化用; 5-clip 拡張前方互換)。**§運用21 照合表 = artifacts v1.1 §A8 に納品済** — 結果: grip-contact (G1/G4 入力) と reach-fail terminate に obs 対応なし → **obs v2.1 = 57D 案** ([53:55] per-arm contact flag + [55:57] per-arm IK-residual; 採否 = design-gate Q)。
- **action:** 両枝 §2-F1。gripper = predicate (次元なし)。
- **reward (sparse-primary 案、/reward-design の入力):** phase-completion predicates (C1 seat / pin fire / C2 regrasp gate = 既存 verdict 機構流用) + 終端 category-SUCCESS + time −0.01/step + terminates = (explosion [physics-fault invalid、PPO batch mask] / drop)。**span 逸脱・reach-fail = informative-only、terminate しない (v1.5e reconcile、line 69 参照)**。**§運用22 検算 (v1.2 訂正)**: 正 budget = **5×5 (G1-G5 phase) + 200 (G6 task) = 225** / 罰累積最悪 = 0.01×900 + 10 = 19 → **ratio 1:11.8 健全**。anti-hover: sparse ゆえ hover 正項なし; time penalty が hover を単調に罰する。**4 成果物 DRAFT = `P2_REWARD_ARTIFACTS_W0C_DRAFT_20260705.md`** (G1-G6 predicate 集合 + ground-truth 値 + 性質 pre-register [単調順位 + anti-hover + **限界比較形** — 旧「2×R_PHASE≥TERM_PEN」は Artifact 3 v1.1 で撤回済 (sunk-cost 誤り)] + branch 別 reachability)。**gate semantics 明文 (v1.5、CC3/CC2): latched-monotonic・fire-once・never-revoked; phase one-hot = argmax(earned); G6 sustain は latch 後も live d<3mm を別途監視; converter の demo phase one-hot = 記録 state 上で predicate を評価して付与 (script schedule 15-phase の写像でなく) + converter-vs-env phase 境界一致 check = DoD (repr-mismatch 防止); G4 の reach 参照 = in-scene cable-lane 相対 (β の「自 command への residual」退化 = tap-hack を封じる)。**
- **success (提案):** **strict_v2 完全 mirror (v1.5f、§運用29)**: c2_seated_honest (groove-membership + settle、raw d<3mm 単独は claw-pin gameable ゆえ不可) sustained K=10 **∧ c1_retained_final live (z_c1<840 ∧ flank_max<840、両鍵 conjunct mirror: recount_strict_v2.py:63-64 [%12 鍵] ≡ p9_recount_strict_v2.py:107-108 [%9 鍵]、flank 窓 = 各 flank_from_npz)** ∧ ¬dropped ∧ **ordered phase gating (G_k は G_{k-1}.latched 前提 — out-of-order fire/farming 防止)** ∧ span-guard PASS (**dual-grip phase scope のみ、v1.5e — 「全 phase」は transit 正当通過 [~170mm] を殺す普遍 deadlock 語ゆえ superseded、line 75 参照**)。**ori 節なし** (HIGH4 disposition; 復活条件明記)。
- **termination/time_outs (v1.5d reconcile):** done = success ∨ timeout(900) ∨ explosion (physics-fault invalid、PPO batch mask) ∨ drop; `time_outs` = timeout のみ。**span-violation / reach-fail (transit) = informative-only (terminate しない)** — 旧「∨ reach-fail ∨ span-violation」は superseded (env-core pre-check H2/N6 fold、v1.5d)。
- **DR hooks:** XY±20mm (既定 ON は Rs) + α-DR 摂動注入 hook ((ii) kick 機構転用、flag-gated) + obs-noise 軸 (Rs spec 待ち) — **全て config 化、既定 OFF**。
- **determinism/band:** seed 固定 + nomA/nomB band 計測 mode を env 標準機能に。
- **transition export / off-policy-ready (E-1、devplan §6-4):** replay 互換 (o, a, r, o′, done, phase, info) の完全記録 export を env 標準機能に — R3 (RLPD replay) の前提資産、設計時は安価・後付けは高価。
- **reward 成分ログ分離 (E-2、devplan §6-5):** 全 reward 成分を per-step 分離ログ (診断・§運用22 事後検算・hacking 検出用)。
- **smoke DoD (v1.5 = 各項に数値 bar、CC4-CH2):** ①throughput **≥9.7 実効 fps** (devplan §12 4-way 算術の成立下限) ②device parity = **per-phase predicate-fire 一致 + 終端 verdict 一致** (FAIL 分岐 pre-declare: cuda:0-only pin + throughput 再導出 — parity FAIL は banked 期待側) ③cg-GPU whole-route screen = **全 phase finite + nacon engage + no nefc overflow** ④horizon 実測 = **n=81 (P3 piggyback) の max-of-n** (n<100 につき保守方向明記; p99>810 → 900 bump) ⑤Δ=const drift-zero (α、=0.0 EXACT) ⑥predicate unit-test @cuda:0 = **6 phase 全 fire + no-re-fire + guards-quiet (guard 発火 0)** ⑦handover-fidelity (β) = **qpos/qvel L∞ ≤ 提案 1mm / 1mm/s** (state-bank 設計時に確定) ⑧corner-miss 分布 = P3 grid 供給済 (前倒し)。 **⟦v1.5d 追補⟧ DoD ⑨a predicate-port (canonical 81-grid replay 分子一致) / ⑨b online residual≡0×81→58/81 (route-executor 段 loud-carry) / ⑩ achieved hold-span 92.4±tol / ⑪ reach-error conditioning check (実 normalization 下) / ⑫ projection operator/subspace 露出 + pushforward-subspace entropy (trainer carry) — build plan §8-10 と同期。
- **guards (v1.3):** ⭐ **action-path の per-arm clamp/rate-limit 禁止 — スケーリングは全て common-mode (単一係数を両腕に適用) とし INV#2 を as-executed で保護** (mini-test 5体 CRIT1 の恒久 carry: per-arm 独立 clamp は off-path で非対称 scale → span 破壊、%9 c3) / **span 監視 (v1.5 = CC3-CRIT fix、banked ruling 忠実復元):** absolute window (92.4mm 中心 + P3 導出) は **dual-grip phase のみ — 窓 = **base grip-schedule 駆動 (v1.5d reconcile): 両腕把持全域 (G1 cage〜unclamp 直前 [G3 C1-seat 込]) ∪ (G4 regrasp 完了〜G6 dual-seat)** — 旧明示列挙 {G1〜G2}∪{G4〜G6} は G3 gap で superseded (ISSUE-1 CRIT、v1.5c/d)。gate = **base grip-schedule ALONE (決定論、fail-safe)**、both-contact [53:55] = DoD telemetry assertion のみ (gate 入力にしない — contact flicker で fail-OPEN になるため、NEW-A)** (f1)。{0} hover (span 可変 92-403mm) と unclamp→GUIDE_C2→regrasp 前区間 (single-grip、span 92→170mm を**正当**通過) は**除外** — ⚠ 旧 v1.3-4 の「全 phase 適用」は canonical route 自身を mid-route terminate させる**普遍 deadlock** だった (ruling は absolute check を grasp phase のみに scope 済み — 全次元照合の教訓)。**tier = informative 既定** (ruling の loose gross-error STOP; hard terminate 化 = P3 window 導出後の design-gate 項、f2)。除外区間の INV#2 保護 = 恒久原則 0 (common-mode) + span-PRESERVATION 規律。**DoD 追加 = guards-quiet-on-canonical-demo** (canonical demo 全 frame で guard 発火 0 の回帰 leg)。commanded-88 の INVARIANT 主張は span-PRESERVATION 判定として分離 (不変) / mujoco backend assert / arm-arm collision = named-design-Q (旧 Q7) / **不可勝 draw class 方針 = design-gate 項** (R_MISS 幾何: bow-chord 112mm > span 窓 → 局所 fix が span-guard 禁止側。選択肢 = truncate-無-penalty / DR-support 除外+limitation 文書化 / Rs-Q。**SR 上限 <100% を campaign bar に反映、draw での selective-hover は期待挙動として記録**。⚠ truncate-無-penalty の 3 注意 [pre-check N2]: (a) trigger が agent 可影響 → penalty-free 早期 exit = **quit-button hack** (b) offset-membership trigger は obs に draw-flag 無しだと V(s) が隣接 winnable corner と alias → (ii) 機構の advantage 信号を汚染 (c) draw-truncate ∉ time_outs [純度] → bootstrap-free done = quit-button の value 標的。**→ 推奨 = DR-support 除外; truncate を採るなら draw-flag obs + reset-time trigger 必須**)。

## §5. oracle API (lens D — 重量級、独立 cost 行)

| 決定項 | 内容 | 案 |
|---|---|---|
| 照会実体 | per-step relabel + settle re-center + in-scene IK (`170b905575` floor — waypoint lookup ではない) | 専用 module (~300-500 LOC) + 自前 [VERIFY] |
| mid-servo 返り値 | interp 中の中間 target か phase 終端 target か + **ACHIEVED-vs-COMMANDED 規約 (D-1、%9 catch)** | **中間 target、規約 = converter label と同一系 (`route_demo_to_bc.py:287` 準拠; 逸脱するなら正当化必須 — 07-04 demo-replay repr-mismatch 教訓: oracle 規約 ≠ training label 規約 = 系統 bias)** — design-gate 決定項 |
| phase-clock | §2-F2 と同一 fork (α: 規約 (b) 推奨 / β: predicates) | Rs |
| state-blind mask | phase 別 validity mask を API が返す (Fact A/B: EE-restoring 全 phase 有効 / cable-target 有効 = 2 点のみ) — 消費側 (IBRL proposal / relabel) が mask で重み付け | ADOPT |
| 消費者 | R3 IBRL proposal / DAgger relabel (**α drift-recovery relabel 含む — corner 教師ではない**) / R4(b) oracle-guided | 共有資産として一度だけ build |
| **named milestone (M-AB、%9 pre-register — 旧称 c2 は discharge label c1-c3 と衝突のため改名 [pre-check N5])** | oracle 稼働後に **A-vs-B 解決 probe** を実施 — state-feedback expert は機構 C (state-blind label aliasing / covariate-shift-under-feedforward-supervision) を除去し A (budget-tension) を可測化する。**de-risk の monotone-DIVERGENCE 自体が C 由来の可能性があり、C なら A-vs-B は dissolve** | R1 close 時の banked impossibility の解決先 |

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
| **route-executor 抽出** (v1.5、CC4: `_run_mujoco_grasp_route` = 2,476 行 monolith → importable/phase-indexed/resumable 化 — α base 実行 + β curriculum + oracle の共通上流) | **canonical byte-repro regression 必須** | 300-800 touched |
| batched per-world contact 抽出 (G1/G4 + obs [53:55]; 既存 = single-world event-time `:4125-4137`) | mjw buffer decode or scratch-mjd、phase-scoped lazy 評価 | 150-300 |
| α trainer 統合 (交互 aux imitation update + masks) | train_common 拡張 | 100-200 |
| 計 (v1.5 restate) | env 本体は **2.0-3.5k** に再 baseline (CC4: AC+AR=2,955/2skill 実勢) | **~3.4-6.4k LOC。gate topology = staged per-component chains (env-core → route-executor → oracle → OG → trainer、各 ≤~800 行 diff で個別 L3 chain — 単一 4k diff の 5体 は line-read 不能)。wall = W2-4 中心に再 baseline** |

## §8. conservatism + carried risks (lens H — %9 §5 表を承継)

base perfect-state targeting = 実機非保守 / retention row56 NEEDS-DUAL = FUNDAMENTAL carry / 3mm groove = 剛体 clip 非保守 / ori 無 gate 化 = 実機前に G7 再訪必須 / GPU whole-route = 未 screen (smoke で) / §4 horizontal curvature = KINEMATIC 境界 (学習成果はこの fidelity 内) / **reach 0.9mm fragility (P1 carried、H-1)**: R re-grasp reach margin 0.9mm + device-fragile (cpu 83.2mm BLOCK vs cuda:0 0.9mm) = R_MISS corner の物理源 — smoke device-parity + P3 script-SR-over-DR-grid が定量化。

## §9. gates / next (lens G/I)

1. 本 spec → **%9 9-lens cross-PV = CONCUR-W-CORRECTIONS (09:28、blocker なし)** → 8 修正反映済 (v1.1) → %9 diff 再確認 (軽量)。
2. `/reward-design` 4 成果物: **spec 段階は assumption-labeled draft、env CPU-smoke 後に実測で再 discharge** (M-A 教訓: env 不在での「PASS」を主張しない)。
3. `/pre-check` chain = **完了** (BLOCK 10:04 → 再走 WARN 10:36 → fixes+spot-diff PASS 10:45、`logs/pre-check-log.jsonl` 3 entries) → **env-spec 5体 済 (11:0x、全 ACCEPT → 本 v1.5)** → P3-grid (前倒し実行中、PREREG banked) → **Rs W0-a′ packet (v1.5 定義 — W0-a を supersede)** = {**premise 再確認 1 行** (経路全体 1-unit を新証拠 [R0/R1 plateau + divergence + 文献 stage 分解優勢] 下で Rs 再確認) + **D-C 両枝決定** [対称必須機構: α=3 点 (drift-recovery relabel + structured-common-mode 局所 RL + draw 会計、p_hit discharge 込み) / β=curriculum (state-bank + prefix 3 pin)] + **D-C 共通 comparator pre-register** (from-P0 SR / identical winnable-support [P3 draw 除外を両枝同一適用] / matched GPU budget / same env sha + cuda:0 + same seed/DR stream / per-class 内訳 [nominal SR + corner uplift] / 併用時の order-confound 明記 — N≥30 + nomA/nomB band + %12+%9 joint verdict の既存規律と同一文で束ねる) + **AR-extend disposition 段落** (NHA-3: frozen-L contract / mid-air reset / dense reward / MAX200 / row56 regression surface 結合 → NEW 選択; 実 reuse = base 2109 は両案共通) + named-design-Q 群 (α-PC/α-DR [P3 evidence 付き]/Q7/HIGH4 節/horizon 900/band α/β/γ [**provisional 明記 — §6 OG 再検証後に再 pin = 1 決定に統合**]/draw 方針/obs v2.1 57D/counting per-offset/span-window tier f2) + §4.3 数値閾値 pin 3 点 + **P4 pre-registration 提案値入り** (γ=0.997 案 [1/(1−γ)=333 vs horizon 900、smoke で再検証] / GAE λ=0.95 案 / envs×steps = smoke 実測で確定 / corner-episodes ≥8/update 案 / λ_relabel・anchor decay 選択 [α] — 空欄 provision 禁止、全て提案値+根拠付き) + **L-TRIAGE L2 降格 confirm** (devplan:7 carry — 未 confirm なら L3 追加 gate) + **D-C 採択時の DQ1=B→A′ supersession 同 turn banking 義務の明記**}。%9 cross-PV 台帳 = `P2_W0C_CROSSPV_PCT9.md` (banked、per-version scope 付き)。
4. Rs 承認後にのみ build (L3 chain + 層5 + cross-PV)。

*%12 — 2026-07-05。PAPER-ONLY。INVARIANTS 不触。*

---
**AMENDMENT (v1.5a, 2026-07-06 11:2x, Rs「推奨で」):** obs v2.1 contract = **60D** に改訂 — 57D + `[57]` near-clip crossing-x deviation (H-drape 変数) + `[58:60]` axis-resolved seat (z-gap / lateral)。既存 [0:57) index 無傷。根拠 = env-core pre-check C1 (corner 定義変数の obs 不在、[0:42] 全数列挙で確定) + §運用21。explosion velocity dim = 不追加 (Q11① justified-absent 既決)。decision-of-record = node state.md 11:2x。

**AMENDMENT (v1.5b, 2026-07-06 11:4x, Rs「推奨で」):** guards の「common-mode scaling が span を保つ」(§4) は 6D per-arm action に対し論理的に不成立 (env-core pre-check N1 CRITICAL) → **(b′) phase-conditional structural projection に置換**: dual-grip phase = Δ を common-mode 部分空間へ hard-project (INV#2 span = 構造 enforcement) / 非 dual-grip 再把持窓 = per-arm 許容 (span 非 invariant 区間) + differential-drift regression = DoD。α-6D 契約不変。decision-of-record = node state.md 11:4x。

**AMENDMENT (v1.5c, 2026-07-06 13:4x, %12):** ①f1 span 窓の明示列挙 {G1〜G2}∪{G4〜G6} は **G3 (C1 seat、両腕把持) を gap で落とす誤り** (env-core pre-check ISSUE-1 CRIT、%12 authored 誤り) → **grip-schedule 駆動窓に置換**: 両腕把持全域 (G1〜unclamp 直前 [G3 込]) ∪ (G4 完了〜G6)、gate = base grip-schedule (決定論) ∧ both-contact [53:55]。round-2 実測 (phase 1-7/13-14 = 92.42 定数) と整合。②(b′) の PPO 会計 = **pushforward-log-prob** (dual-grip では projected/common-mode marginal で log π 評価 — 6D network 出力 = α-6D 契約不変、trainer 段 L3 で再検証; env-core = projection-applied flag を info 露出 + clip-fraction smoke DoD)。③transit reach 可観測性 = **[16:19] semantics pin: 現 phase の target cable segment (再把持窓 = reaching-arm の把持対象 seg)** → 方向性 reach error は [16:19]−EE の線形導出で表現可 (新 dim 追加なし)。⚠ sub-mm (0.9mm) の FP32 conditioning 懸念は **offline conditioning check を DoD に追加** — 不成立実証時のみ +3D obs ask へ fallback (evidence-gated)。④transit per-arm = **ASYMMETRIC 採用**: reaching/free arm = full per-arm / gripping arm = σ-cap (drop 防止、(b′) intent-faithful)。decision-of-record = node state.md 13:4x。

**AMENDMENT (v1.5d, 2026-07-06 14:1x, %12):** ①v1.5c ① の gate 定義「grip-schedule ∧ both-contact」は **fail-OPEN (contact flicker で dual-grip 中に projection OFF = 保護が要る瞬間に外れる、NEW-A HIGH)** → **gate = base grip-schedule ALONE (fail-safe)、both-contact = DoD telemetry assertion のみ**に訂正。②§4 body を amendment 群と reconcile (line 69 termination / line 74 DoD ⑨-⑫ / line 75 窓 + gate、supersession pointer 付き) — addendum-only 反映は builder の先祖返り risk ([[feedback-confirmed-decision-reflect-in-authoritative-spec]]、NEW-E HIGH) のため本文へ焼き込み。decision-of-record = node state.md 14:1x。

**AMENDMENT (v1.5e, 2026-07-06 14:2x, %12):** NEW-E 完全 close — line 67 reward の旧 terminate 括弧 (span 逸脱/reach-fail を terminate 列挙) と line 68 success の「span-guard 全 phase」(line 75 自身が普遍 deadlock と警告する語) を本文 reconcile。span/reach-fail = informative-only、span-guard success 節 = dual-grip phase scope。NEW-G (release-COMPLETE boundary、fail-safe 方向の contact 使用 = projection 延長のみ) + NEW-H (evidence-gated carry) = %11 fold 承認。

**AMENDMENT (v1.5f, 2026-07-06 15:0x, %12):** env-core 5体 [VERIFY] CC2-CH1 CRIT — **success/G6 が c1_retained_final conjunct を欠落 (spec line 68 起源、J-9/§運用29 と同型の分子 hole を私が spec で再生産)** → line 68 を strict_v2 完全 mirror に修正 (C1-retention live + c2_seated_honest + ordered gating)。§運用21 корollary = C1-retention obs 入力 (+2D → 62D) は Rs confirm 待ち。adversarial-rollout (residual≠0) numerator DoD 追加 (⑨a/⑨b は base=C1 81/81 vacuous で本 hole に盲 — DoD-blind の教訓)。decision-of-record = node state.md 15:0x。

**AMENDMENT (v1.5g, 2026-07-06 15:1x, Rs「観測 +2 次元(62D」):** obs contract = **62D** — 60D + `[60]` C1-region cable-z + `[61]` C1 flank-max-z (G6 c1_retained_final live conjunct [v1.5f] の §運用21 入力)。既存 [0:60) 無傷。decision-of-record = node state.md 15:1x。

**AMENDMENT (v1.5h, 2026-07-06 17:5x, %12):** line 68 の citation 訂正 (RV NEW-1、引用先確認 hard-rule): 旧「recount_strict_v2.py:24-26」は定数行 — 正 = 両鍵 conjunct 行 (recount_strict_v2.py:63-64 / p9_recount_strict_v2.py:107-108、%12 が両 file on-disk 確認)。値は不変、pointer のみ訂正。
