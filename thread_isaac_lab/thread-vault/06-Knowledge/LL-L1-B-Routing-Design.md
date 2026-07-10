---
title: LL-L1-B-Routing-Design
created: '2026-05-03'
tags:
  - knowledge
  - routing
  - phase5-3
  - orchestrator
  - design
  - l1b
status: 'approved (Rs batch approve 2026-05-03 T-ROOT-COORD#s11) — SSOT-grade entry official、§16 commit input 2026-05-09 cron evaluation 待ち、CLAMP-R-Train sibling PROPOSE-Prep 起票完了 2026-05-04T05:30 (T-CLAMP-R-Train-PROPOSE-Prep node、§4.3 update record 反映済)、actual T-CLAMP-R-Train 起票は per-skill ≥50% empirical floor 経 OR Rs explicit override 経で再判定'
doc_class: design-surface
---

# LL-L1-B Routing Design — SSOT-grade Design Knowledge

T-L1-B (L1.B Multi-clip routing capability) umbrella の architecture design knowledge SSOT entry。06-Knowledge LL- prefix (CC Create/Update 範囲、`Vault Write Permissions.md`)。

T-L1-B-Design-CC session (2026-05-03、L0 ★4 disposition、L=L1 bypass mode 自律) で起票。memory chronology + Vault summary を post-correction-canonical baseline で再校正、Phase 5-3 v2 §16 commit re-trigger (2026-05-09 cron) と child task 起票 trigger reassessment の input。

## §0 Vault knowledge 役割分担 (3+1 file separation)

設計レガシー散在防止のため、L1.B 関連 4 SSOT の責務を明示分離:

| File | Role | Mtime authority |
|------|------|-----------------|
| `~/.claude/projects/-home-rlrk-IsaacLab/memory/project_l1b_multi_clip_design_complete_2026-04-27.md` (595 行) | Detailed chronology + 4 sub-task design + 7-CC Pre-Debate input、line-cite 多数 + impl pseudo-code 含む、point-in-time snapshot | 2026-04-27 (frozen) |
| `Multi-Clip Routing.md` (Vault, 100 行) | Quick-ref summary + Vault graph index entry point | 2026-04-27 |
| **本 entry (`LL-L1-B-Routing-Design.md`)** | **SSOT-grade design knowledge** + code mtime integrity + impl spec summary + **trigger reassessment per latest SR** + sample-size correction integration + Vault organization meta | **2026-05-03** (本 entry update authority) |
| `T-L1-B/state.md` | NEST umbrella node (status / dependencies / session_history、KA5 minimal、children=[]) | 2026-04-28 |

将来 update authority:
- code state mtime drift detect → 本 entry §1.1 update
- per-skill SR canonical update → 本 entry §4.1 update
- §16 commit re-trigger result → 本 entry §4.2 + §5.3 update
- CLAMP-R-Train sibling 起票 → 本 entry §4.3 + state.md `children_nodes` update
- 19th fix adoption (formal §16 commit) → 本 entry §5.2 status update

`thread-vault/07-Design/RL-Routing-Design.md` (権威 spec、Rs 専権) への直接 commit 権限は本 entry にない。本 entry は §16 commit input のみ。

## §1 Architecture refinement (orchestrator multi-clip driver)

### 1.1 Code state verification (2026-05-03 baseline)

design memo (2026-04-27) 数値整合確認 — wc -l + ls -la independent verify (本 session 実行):

| File | LoC (memo cite) | LoC (2026-05-03 verify) | mtime | drift |
|------|-----------------|-------------------------|-------|-------|
| `orchestrator/routing_orchestrator.py` | 1271 | 1271 | 2026-04-26 22:36 | none |
| `skills/step_table.py` | 215 | 215 | 2026-04-05 15:53 | none |
| `scripts/eval_skill.py` | 667 | 667 | 2026-04-17 14:19 | none |
| `skills/snapshot.py` | 138 | 138 | (LoC 一致) | none |

design memo の line-cite (`routing_orchestrator.py:96` `_R_ARM_ONLY_CLAMP_STEPS`、`step_table.py:STEP_TABLE` 215 LoC、etc.) は依然 valid。今後 code edit 発生時は本 entry §1.1 update で drift 反映。

### 1.2 Sub-task 1+3 統合 spec (~+95 LoC)

新 method `RoutingOrchestrator.drive_full_routing(start_step, end_step) -> RoutingResult` + `_validate_clip_index_for_step` 統合実装:

- 既存 `execute_step(step_id)` (1002-1078) を STEP 1..43 順次呼出 sequential driver
- `RoutingResult` NamedTuple (8 lines): `completed_steps / final_step_id / final_result / per_clip_status / per_step_results / rollback_count / explosion_step`
- `_validate_clip_index_for_step(step_id)` orchestrator-local validation (~15 lines): `step_table.STEP_BY_ID[step_id].clip_index` と `current_clip_idx` の drift check (STEP 11-42 範囲、外で permissive)
- LoC breakdown: NamedTuple 8 + drive_full_routing impl ~50 + validate ~15 + import/docstring ~22 = **~+95**
- Detailed pseudo-code: design memo §2.3 + §4.4 (本 entry duplicate せず、reference 維持)
- Test target (impl task で実装): `tests/test_orchestrator_drive.py` で `drive_full_routing(start=1, end=10)` (C1 only)、`(1, 18)` (2-clip)、`(1, 43)` (5-clip with mock policy)

### 1.3 Architectural rationale (Sequential clip-by-clip + global state cumulative)

3 候補比較 (design memo §2.1 抜粋):

| 候補 | 概要 | LoC | 採用判定 |
|------|------|-----|----------|
| (a) 5 clip 並列 state | 各 clip 独立 RoutingOrchestrator instance × 5 | ~+250 | REJECTED (single-world contract 違反、cable 1 本 physics nonsense、5x VRAM) |
| **(b) Sequential clip-by-clip + global state** | 単一 RoutingOrchestrator × execute_step を STEP 1..43 連続 driver wrap | **~+80** | **採用** |
| (c) Hierarchical (per-clip sub-FSM × 5 + master) | OuterFSM + InnerFSM 2-tier | ~+200 | REJECTED (既存 execute_step + step_table 2 重抽象、SSOT divergence) |

採用根拠 (b):
1. **既実装活用**: `execute_step` が per-step granular driver として完成 (Cluster G recovery + snapshot/restore + retry)
2. **SSOT 整合**: `step_table.py:STEP_TABLE` (215 LoC) は既に 5-clip 対応 (`_build_clip_routing(1,11)..(4,35)` で C2-C5 全展開)
3. **State 機構既実装**: `clip_status[5]` (line 749) + `current_clip_idx` (line 733) + `capture/restore_snapshot` (1209-1262)、追加 state 不要
4. **Rollback 制約 acceptable**: cross-clip rollback は spec 外 (各 clip 内 MAX_ROLLBACK_DEPTH=3 で十分)、Phase 5-3 短期 G6 ≥40% 期待 ROI 高い (cross-clip rollback は WM Cascade Gate 4 領域)
5. **CLAMP-R B1 既 fix**: `_R_ARM_ONLY_CLAMP_STEPS={14,22,30,38}` (line 96) で C2-C5 RL CLAMP_R dispatch live

### 1.4 TOUCH FORBIDDEN (CC#3 Option D 完全準拠、本 entry SSOT 化)

- `task_config.py` (SSOT)
- `newton_*_env.py` (env 改変、env CREATE/UPDATE 含)
- `mpc_config_*.py` (frozen)
- `step_table.py` (43 STEP table 安定)
- `RoutingOrchestrator.__init__` (single-world contract num_envs==1 維持)

本 design は **add-only** (orchestrator + eval_skill.py 既存 method 改変なし、新 method/CLI/SKILL_REGISTRY entry 追加のみ)。

## §2 Mirror transforms spec (CLAMP-R B2 fix orchestrator-local mask)

### 2.1 既実装 mirror (`routing_orchestrator.py:691-770`)

- `_CLIP_PLUS_Y_ARM = {0:R, 1:L, 2:L, 3:L, 4:L}` (line 691-693): mirror gate vector
- `_needs_clip_relative(skill)` (line 764-766): AR + IC のみ True
- `_needs_mirror(skill, clip_idx)` (line 768-770): IC + clip>=1 (C2-C5) True
- `get_action(...)` (line 772+): clip_relative + mirror 適用済 + un-mirror 自動

→ IC C2-C5 で `mirror=True` 自動適用、追加 mirror design 不要。

### 2.2 Sub-task 2 spec (CLAMP-R B2 fix、~+15 LoC)

新 method `RoutingOrchestrator._mask_l_arm_action_for_clamp_r(action_env, skill_type) -> action_env`:

- **Issue**: env `_apply_actions_batch` の dual_arm branch が `action[6:12]` (L EE) を unconditional 適用 → CLAMP_R STEP (14/22/30/38) で policy が L-arm grip を破壊
- **Solution**: orchestrator-side mask (env touch FORBIDDEN per CC#3 Option D)
- **Impl**: `if skill_type != SkillType.CLAMP_R: return action_env` early-return + `masked = action_env.clone(); masked[..., 6:12] = 0.0; return masked`
- **Call site**: `_run_rl_episode` (line 901-940) の `expand_action_for_env` 直後
- **LoC**: ~+15 (method + call site)
- **Test target**: `test_orchestrator_clamp_r_mask.py` で CLAMP_R に対し action[6:12] zero、CLAMP/AR/IC で no-op assert

### 2.3 CLAMP-R B1-B5 audit blocker resolution map (本 entry SSOT 統合)

| Blocker | 解決状態 | scope |
|---------|---------|-------|
| B1 (`_R_ARM_ONLY_CLAMP_STEPS` off-by-one) | **FIXED** in `routing_orchestrator.py:96` (2026-04-25) | 既 fix、本 design 前提 |
| **B2** (env L-arm action 非mask) | **本 design Sub-task 2 で orchestrator-local fix** | T-L1-B-Mirror-Transforms-Impl child task (~+15 LoC) |
| B3 (R-only demos なし) | **CLAMP-R-Train 別 task** (T-Skill-CR sibling、env touch なし) | demo collection script + train_grip.py 拡張 |
| B4 (env `_target_seg_indices_l` P0 fixed) | **CLAMP-R-Train 別 task** (env method `refresh_target_segs`) | env touch 必要、本 entry scope 外 |
| B5 (env success `clamp_r_ok AND clamp_l_ok` hardcoded) | **CLAMP-R-Train 別 task** (env per-arm success path) | 同上 |

本 design (L1.B 4 sub-task) で CLAMP-R **B1+B2 解決**、B3+B4+B5 は CLAMP-R-Train 別 task で env touch + per-arm DAPG training 必要。Phase 5-3 v2 §16 spec の "CLAMP-R 91.84% target path (短期)" は **L1.B impl + CLAMP-R-Train 両方完了が前提**。

## §3 Multi-clip eval methodology (eval_skill.py extension)

### 3.1 Sub-task 4 spec (~+80 LoC)

新 SKILL_REGISTRY entry `"routing_orchestrator"` + CLI flag + 5 checkpoint args:

- `--orchestrator-mode={1clip|2clip|5clip}` mapping `(start_step, end_step)`:
  - 1clip → (1, 10) | 2clip → (1, 18) | 5clip → (1, 43)
- 5 checkpoint args: `--checkpoint` (AC default) + `--ar-checkpoint` + `--clamp-checkpoint` + `--clamp-r-checkpoint` + `--ic-checkpoint`
- `build_multi_skill_policy(base, adapter_paths)` で 5 LoRA adapter (~10MB each) + base (~50MB) ≈ ~100MB VRAM (cuda:2 24GB 余裕)
- env CREATE 不要 (既存 NewtonGripEnv reuse via orchestrator wrap)
- LoC: ~+50 main + ~+30 helper = **~+80**

### 3.2 Chain success metric definition (本 entry SSOT 統合)

| metric | definition | mode usage |
|--------|------------|------------|
| **chain_success** | all `per_clip_status[:n_clips]` == True (clip 全 latch) | G6 (≥40% @ 2clip), G7 (≥30% @ 5clip) |
| **per_clip_success_rate** | per-clip latch ratio across episodes | per-clip difficulty 比較 (C2 vs C5) |
| **per_step_success_rate** | RL step ごと SUCCESS ratio | bottleneck STEP 同定 |
| **explosion_count** | episode 内 explosion 発生 ep 数 | physics stability indicator |

### 3.3 RUN_METRICS schema 拡張 (Cluster G failure rate measurement)

draft v2 §16.5 で要求された Cluster G recovery floor failure rate measurement 用 logging field (Phase 4+ task #1 と同期起票候補):

| field | 内容 | source |
|-------|------|--------|
| `cluster_g_recovery_attempts` | recovery escalation trigger 発動回数 (per episode) | `routing_orchestrator.py` recovery_engine |
| `cluster_g_recovery_failures` | recovery escalation 失敗回数 (per episode) | 同上 |
| `cluster_g_failure_reasons` | failure 原因 enum (cable_loss / explosion / step_budget_over) (list per episode) | env event log |

`_aggregate_routing_metrics` 内で per-episode 集計、`scripts/aggregate_cluster_g_metrics.py` (Phase 4+ task #1 起票候補) で cross-run 統計化。本 entry は spec 記録のみ、aggregator script 起票は §16 commit + Phase 4+ task #1 並行起票に同期。

## §4 Children 起票 trigger reassessment (2026-05-03 update)

T-L1-B/state.md §2 で確定した child task 起票 trigger 条件 (3 件 AND):
1. per-skill RL ≥50% 達成 (AR/IC/Grip-CLAMP)
2. Phase 5-3 v2 §16 commit re-trigger PASS (2026-05-09 cron)
3. CLAMP-R-Train (T-Skill-CR sibling) 起票 + B3+B4+B5 env-touch fix progress

### 4.1 Trigger 1 status (latest per-skill SR、canonical post-correction 2026-04-26)

`scheduled_section16_recheck_2026-05-09.md:108` (CC-Source-Memo-Correction Path Y empirical 25 例目、2026-04-26 ~20:25 Rs Option A authorization) で確定 canonical:

| Skill | Latest SR canonical | Trigger gap (50%) | Source mtime |
|-------|---------------------|-------------------|---------------|
| AC | **49%** (multi-seed deploy) | -1% (近接、ただし trigger list 含まれず) | `project_ac_v30_sweep_complete_2026-04-26.md:20` (mtime 2026-04-26 15:02) |
| AR | **10.0%** (eval det) | -40% (87.5% gap、Phase α.4b BLOCKED 2026-04-30) | `project_ar_phase_alpha4a_complete_2026-04-26.md:16` (mtime 2026-04-26 10:39) |
| IC | 39.2% | -10.8% (近接、未達) | design memo 2026-04-27 cite (source unclear、re-verify 候補 OQ) |
| Grip-CLAMP | 0% (G7 sweep S3=0%、N=0.1 finding pending) | -50% (full gap) | design memo 2026-04-27 |

**Trigger 1 verdict**: 全 3 skill (AR/IC/Grip-CLAMP) **未達** → children 起票 BLOCKED。

注意: 2026-04-26 source-memo-correction で AR "10.0%" / AC "49%" は当初 "factual errors" として flag されたが実は **正しい canonical 参照** だった (eval det canonical / multi-seed deploy canonical の metric 区別、CC2 CRITICAL #1-2 が older training-summary memos のみ cite した evidence base 不完全が原因)。本 entry は post-correction baseline を採用。詳細: `handoff_cc_source_memo_correction_close_2026-04-26.md` + `feedback_cc1_launch_instruction_quality.md` (Path Y 6 evidence #5)。

### 4.2 Trigger 2 status (2026-05-09 §16 commit re-trigger cron)

`scheduled_section16_recheck_2026-05-09.md` (cron `trig_0186rZzNh8MLLzhNPCg4vYa8`、09:00 JST) で評価:
- **Phase 5-2 G5 wet-run COMPLETE 確認** (success ≥50% wet-run)
- **6 OQs empirical correlation 校正可否** (draft v2 §16.4 ±10% empirical deviation budget)

CC4 D2 finding (2026-04-26): G5 slip risk past 2026-05-09 — IC unblock (Item 2 A path) progress unclear。G5 NOT COMPLETE なら memo L37-39 defer path (auto-extend to 2026-05-23)。

**Trigger 2 verdict (2026-05-03 時点)**: 未確定、cron fire 待機 (2026-05-09)、defer の場合は 2026-05-23 に umbrella status reassessment。

### 4.3 Trigger 3 status (CLAMP-R-Train sibling 起票)

`T-Skill-CR/state.md:30` で「Mirror transforms refinement: L1.B.2 multi-clip routing と shared」明示 (dual-attribution 認識、CC4-HIGH-4 ACCEPT)。CLAMP-R-Train は master list v2 で明示 entry なし (CC5-MED-3 ACCEPT)、Skill axis formalize 後に master list addendum 起票候補。

**Trigger 3 verdict (2026-05-03 時点)**: 起票未着手、Skill axis formalize 待機。

**Trigger 3 verdict (2026-05-04T05:30 update)**: **T-CLAMP-R-Train-PROPOSE-Prep 起票完了** (T-ROOT-COORD#s11 ~05:00 JST L0 Rs proxy approve、`feedback_autonomous_full_authority_2026-05-03` 3-step expansion 全 tier 適用)。Design memo (`T-CLAMP-R-Train-PROPOSE-Prep/clamp_r_train_spec_propose_prep.md`、~530 行) で B3+B4+B5 env-touch design + per-skill ≥50% empirical trigger reassessment + 5-CC Pre-Debate L3 input ready PROPOSE skeleton (KA1-KA8 + Risk register R1-R10) 完備。actual T-CLAMP-R-Train (env touch L3 cascade + R-only demos collection + DAPG train + eval) は subsequent NEST node、起票 trigger は (a) sister skill ≥50% empirical floor (5 skill 中 ≥1 達成、AC 49% near most likely path) + (b) Rs §3.1 #4 起動承認 + (c) env touch L3 cascade ready (5-CC Pre-Debate launch + /handoff prerequisite) + (d) GPU resource budget ~30-50h cuda:2 で gate。Estimated 起票 timing (本 design memo §4.3 内): Optimistic 15-25% ~2026-05-15 / Realistic 40-50% ~2026-06-01 / Pessimistic 25-40% ~2026-07-04+。Skill axis formalize は 5 skill 全 PROPOSE-Prep / active task complete (2026-05-04T05:30 経) で部分達成、master list addendum 起票候補は actual T-CLAMP-R-Train 起票時に discharge。本 entry §4.3 trigger 3 status は本 turn で 起票未着手 → PROPOSE-Prep 起票完了 へ進展、本 §4 全体 trigger AND status update は次 reassessment cycle (~2026-05-09 §16 cron OR ~2026-05-28 1-month idle) で同期。

**Trigger 3 verdict (2026-05-04T14:00 update)**: **T-CLAMP-R-Train-Phase-1-PROPOSE 起票完了** (T-ROOT-COORD#s11 ~14:00 JST L0 Rs proxy approve、`feedback_autonomous_full_authority_2026-05-03` 3-step expansion 全 tier 適用、Wk 45% HARD stop)。PROPOSE write-up (`T-CLAMP-R-Train-Phase-1-PROPOSE/phase_1_propose.md`、~700 行 §0-§8) で **launch-ready concrete artifact** 完備 — §1 PROPOSE template (CC1 lead 全 field 具体化、launch-ready format、variant + goal + L=L3 + disposition L3 ★ + touched files concrete diff size 6 files × ~170-300 LoC + 1 NEW dataset + core SSOT references + KNOWN_ALTERNATIVES KA1-KA8 expanded with sufficiency analysis + counter-evidence + NHA HOLD candidate detail + risks R1-R10 expanded with severity matrix + mitigation procedural detail + monitoring hook + disposition rationale 5 core values DOMINATE) + §2 Model architecture details (DAPG mirror + network spec + observation/action per-arm decoupling + hyperparameter initial values + LoC estimate breakdown) + §3 Training data spec (R-only demos collection pipeline + mirror coordinate transform Y-axis flip detail concrete impl spec + dataset format/storage + validation gates + KEY DISCOVERY orthogonal P3 inheritance) + §4 Reward function spec (R-only success path with B5 fix + per-arm reward formulas concrete impl spec + initial parameter values + penalty:reward ratio 4.3:1 enforce derivation + /reward-design 4 出力物 placeholder + episode termination semantics timeouts vs terminal state distinction) + §5 Abort criterion (training-time hard stops + soft stops + auto-kill authority) + §6 5-CC Pre-Debate ready spec (PROPOSE artifact location + KA challenge expected per CC2-5 + NHA HOLD STRONG ★ candidate per KA8 + spawn instructions + pre-spawn /handoff requirement + decision matrix + most likely outcome NO_ACTION) + §7 Execution sequencing for actual T-CLAMP-R-Train (Phase A-G concrete + total wall-clock ~12-20h estimate) + §8 Cross-references + caveats C1-C12。**Sibling pattern with PROPOSE-Prep distinction**: PROPOSE-Prep (design rationale phase) と Phase-1-PROPOSE (launch-ready artifact phase) は sibling NEST nodes (parent T-Skill-CR、children_nodes 並列)、本 Phase-1-PROPOSE は PROPOSE-Prep の direct concretization downstream (sibling not child、AR 軸の Prep → Final と同 pattern)。本 Phase-1-PROPOSE 経で actual T-CLAMP-R-Train 5-CC Pre-Debate launch input artifact ready (lead time elimination)、actual T-CLAMP-R-Train 起票 trigger 4 condition wait (sister skill ≥50% floor + Rs approve + env L3 ready + GPU budget) で artifact ready preserve。本 entry §4.3 trigger 3 status は本 turn で PROPOSE-Prep 起票完了 → Phase 1 PROPOSE write-up 完備、actual T-CLAMP-R-Train 5-CC launch input ready へ further 進展、actual T-CLAMP-R-Train 起票 (subsequent NEST node) は per-skill ≥50% empirical floor 経 OR Rs explicit override で immediate launch path 開放。本 turn 経で 2 skill (AR + CLAMP-R) で Prep → 次 step concretization complete (AR=verdict integration step PROPOSE-Final / CLAMP-R=launch-ready artifact step Phase-1-PROPOSE、orthogonal concretization 種、structural sibling pattern)。

### 4.4 Stall risk + escalation path (本 entry 2026-05-03 update)

state.md §2 で確定 (CC5-HIGH-4 ACCEPT):
- **Probability 70%+** で AC/AR 50% 到達不能 (F1 partial-falsification)
- 1 month idle で本 umbrella status review (coordinator drift framework feedback signal)
- 3 month+ idle で architecture rethink (Option C/D / WM Cascade 並行) escalation candidate
- §16 cron 2026-05-09 deferred to 2026-05-23 case で本 umbrella status PARTIAL_HOLD 候補

2026-05-03 update:
- AR Phase α.4b **BLOCKED_FOR_USER** (2026-04-30 ~16:00、`handoff_cc_ar_phase_alpha_4b_blocked_for_user_2026-04-30.md` per: V7.1 baseline mismatch env mtime 15:13 + r_drift partial observable not noise + model_117 resume prohibited.md L40 violation)、AR retrain 進捗 stall
- KA7 noise sweep (grid.1 fresh boot、`handoff.md` s8 close 2026-04-30 22:15) 結果待機 + Cluster G recovery 動作実績待機 が **Phase α.4b unblock 経由** で trigger 1 progress を駆動
- 1 month idle target ≈ **2026-05-28** (T-L1-B 起票 2026-04-28 + 1 mo)、その時点で AR/IC/Grip 状況 reassessment + umbrella status review

## §5 Chain math sample-size correction (CC3 D2 19th fix candidate integration)

### 5.1 Background (draft v2 §16.4 empirical deviation budget)

draft v2 §16.4 で chain math empirical deviation budget = **±10% absolute deviation** で independence assumption 再検討 trigger 確定。

CC3 Debate-2 finding C3 (2026-04-26、`scheduled_section16_recheck_2026-05-09.md:105`): **±10% は statistically inadequate at n<100 episodes** per binomial CI math:
- σ@p=0.918, n=30 = 4.95% → 95% CI = ±9.7% (実測 sampling noise 内に ±10% budget が含まれる)
- 結論: n<100 sample size で ±10% threshold は signal/noise 区別不能

### 5.2 19th fix candidate (本 entry SSOT 統合)

OQ-A re-derivation triggers:
- `|Δ| > 2σ_binomial(n, p)` が proper threshold (sample size adaptive)
- For n<100, use **relative deviation > 15%** OR require **n≥100 sample size constraint**

draft v2 への適用 (formal §16 commit 時 19 件目 fix として参照):
- §16.4 chain math empirical deviation 行を「`|predicted - empirical| > 2σ_binomial(n, p)` (n<100 時は relative deviation > 15% OR n≥100 mandate)」に書換
- §16.7.1 W2-3 row「seed 数は actual nvidia-smi 結果で動的決定」に「+ binomial CI requirement (n≥100 推奨、n<100 時は relative deviation > 15% threshold)」追記候補

### 5.3 Phase 5-3 v2 §16 commit re-trigger 連携 (2026-05-09 cron evaluator input)

2026-05-09 cron evaluator は本 §5 sample-size correction を以下手順で適用:
1. G5 wet-run + 短期 milestone (2-clip 60%) 後 empirical SR data の n 値確認
2. n<100 の場合 `|Δ| > 2σ_binomial(n, p)` re-derivation で OQ-A correlation 校正 (relative > 15% 採用)
3. n≥100 確保可能なら ±10% threshold 維持で校正

trigger interaction: 本 §5 は §16 formal commit に同期 candidate、本 entry が L1.B subtree responsibility の single-source。§16 commit 時は本 §5 を 19th fix として cite。

## §6 Open questions for future revision

| OQ | topic | trigger |
|----|-------|---------|
| OQ1 | IC 39.2% canonical SR の source re-verify (design memo 2026-04-27 cite source unclear、AC/AR 同等 canonical correction memo 不在) | 2026-05-09 §16 cron evaluator が IC unblock progress 確認時 |
| OQ2 | KA7 noise sweep (grid.1) 結果が AR Phase α.4b unblock を駆動するか (本 entry §4.4 stall risk update 候補) | grid.1 fresh boot 完了後 result memo 起票時 |
| OQ3 | T-L1-B umbrella と Cluster G failure rate measurement (Phase 4+ task #1 + draft v2 §16.5) の SSOT 重複可能性 — 本 entry §3.3 で field spec 記録、Phase 4+ task #1 で aggregator script 起票候補、責務分担確定 | Phase 4+ task #1 起票 trigger (§16 commit 後) |
| OQ4 | CLAMP-R-Train (T-Skill-CR sibling) 起票時に env-touch fix scope (B3+B4+B5) を本 entry §2.3 から removal するか (sibling SSOT に move) | CLAMP-R-Train 起票時 |
| OQ5 | 1 month idle (~2026-05-28) reassessment 時に T-L1-B 全 children 不在で umbrella status を PARTIAL_HOLD or DORMANT に格下げするか、IN_PROGRESS 維持か | 2026-05-28 NEST coordinator drift review |

## §7 Caveats

- **C1 (memory stale risk)**: design memo (2026-04-27、6-day stale at write time) の line-cite は本 entry §1.1 で code mtime 整合確認済 (2026-05-03 baseline)。今後 code edit 発生時は本 entry §1.1 update で drift 反映
- **C2 (canonical SR baseline)**: per-skill SR は CC-Source-Memo-Correction (2026-04-26) Path Y empirical 25 例目で訂正済、本 entry は post-correction baseline 採用 (older training-summary memos の値を cite せず)
- **C3 (sample-size correction adoption)**: §5 19th fix candidate は **draft level**、formal §16 commit (2026-05-09 cron 後) で正式 adoption。本 entry は knowledge として記録のみ、§16 直接 edit 権限なし (Rs 専権)
- **C4 (env file UNCHANGED 不変)**: CC#3 Option D 完全準拠、本 design 範囲は orchestrator + eval_skill.py edit のみ。CLAMP-R-Train (B3+B4+B5 env touch) は別 task (T-Skill-CR sibling)
- **C5 (children 起票 trigger AND condition)**: 3 trigger AND 成立で発動、現状 (2026-05-03) 全未達 → children 起票 BLOCKED。1 month idle (~2026-05-28) で umbrella status reassessment、3 month+ idle で architecture rethink escalation
- **C6 (Vault write permission)**: 本 entry は CC Create/Update 範囲 (06-Knowledge SSOT、`Vault Write Permissions.md`)、`07-Design/RL-Routing-Design.md` への直接 commit は Rs 専権 (本 entry は §16 commit input のみ)
- **C7 (multi-world deferred)**: Phase 5-3 multi-world (Phase 5-2+ deferred per orchestrator module docstring) は本 entry 範囲外、single-world contract (num_envs==1) 維持

## §8 Cross-references

### 上流 SSOT (Vault)
- [[Multi-Clip Routing]] — Vault summary 100 行 quick-ref + index
- [[../07-Design/RL-Routing-Design]] §15 (Phase 5-2 1-clip E2E)、§16 (vault target、未 commit、draft v2 in memory)
- `07-Design/RL-Routing-Design.md:519-531` (RL=15 STEP SSOT、本 entry §3.1 LoC 参照基準)
- [[../04-Specs/SOMA]] (5-clip 95% L0 final goal)

### NEST node (Vault)
- `00-Project-Management/T-L1-B/state.md` (NEST umbrella、KA5 minimal、children=[])
- `00-Project-Management/operational-rule-LTM-1.md` (LTM-1 v1.1 spec)
- `00-Project-Management/nest-adoption-runbook.md` (v1.1)
- `00-Project-Management/project-tree-manifest.md` (本 umbrella 起票済)

### Memory references (frozen point-in-time、auto-load)
- `project_l1b_multi_clip_design_complete_2026-04-27.md` (595 行 design chronology、本 entry の上流 source)
- `handoff_cc_l1b_multi_clip_design_close_2026-04-27.md` (Main CC B sub-agent 2 close)
- `project_l1b_node_creation_propose_2026-04-28.md` (CC1 PROPOSE、γ→KA3 STRONG ★)
- `project_l1b_node_creation_decide_2026-04-28.md` (47 challenge ACCEPT + Y2 KA5 minimal disposition、本 entry KA5 採択 evidence chain)
- `handoff_cc_l1b_node_creation_predebate_2026-04-28.md` (§運用25 mandatory)
- `draft_phase5_3_v2_spec_2026-04-25.md` (§16 v2 draft、未 commit、18 fix applied)
- `scheduled_section16_recheck_2026-05-09.md` (cron + CC3 D2 sample-size finding §5 source + CC4 D2 G5 slip risk + CC-Source-Memo-Correction Path Y 25 例目 §4.1 source)
- `handoff_cc_source_memo_correction_close_2026-04-26.md` (per-skill SR canonical 訂正、Path Y empirical 25 例目)
- `project_clamp_r_audit_result_2026-04-25.md` (B1-B5 audit、§2.3 source)
- `handoff_cc_ar_phase_alpha_4b_blocked_for_user_2026-04-30.md` (Phase α.4b BLOCKED、§4.4 stall risk update source)

### Cross-tree (informational)
- `T-Skill-CR/state.md:30` (Mirror transforms refinement L1.B.2 と shared、§2.3 dual-attribution evidence)
- `T-Skill/state.md` (parent skill axis、本 umbrella と orthogonal)
- T-CLAMP-R-Train (CLAMP-R-Train sibling 候補、未起票、§4.3 trigger 3 source)

### Schedule (cron)
- `scheduled_section16_recheck_2026-05-09.md` (§16 commit re-trigger 2026-05-09 09:00 JST、§4.2 + §5.3 source)
- `scheduled_layer4b_c5_check_2026-05-09.md` (Phase 4+ task #1 C5 cable loss 2-week follow-up、§3.3 aggregator script 起票候補 trigger)

## §9 Update record

- 2026-05-03: 本 entry 起票 (T-L1-B-Design-CC session、L0 ★4 disposition、L=L1 bypass mode 自律進行)
  - 起票 deliverables (L0 disposition):
    - ✅ orchestrator architecture refinement (§1) — code mtime integrity + Sub-task 1+3 統合 spec + 採用根拠 + TOUCH FORBIDDEN
    - ✅ mirror transforms spec (§2) — 既実装 mirror + Sub-task 2 CLAMP-R B2 fix + B1-B5 resolution map
    - ✅ multi-clip eval methodology (§3) — eval_skill.py extension + chain success metrics + RUN_METRICS Cluster G schema 拡張
    - ✅ children 起票 trigger reassessment per latest per-skill SR (§4) — 3 trigger AND status (AR 10.0% / IC 39.2% / Grip 0% canonical post-correction、§16 cron 2026-05-09 待機、CLAMP-R-Train 未起票)
    - ✅ chain math sample-size correction integration (§5) — CC3 D2 19th fix candidate (binomial CI、n<100 で relative > 15%)
    - ✅ Vault knowledge organization 役割分担 (§0) — 3+1 file separation (memory chronology / Vault summary / 本 entry SSOT-grade / NEST node)
