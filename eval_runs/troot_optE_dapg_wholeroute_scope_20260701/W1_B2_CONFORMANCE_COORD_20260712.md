# W1 B2 Conformance Table — HOLD + oracle API (implementation-vs-spec fidelity)

**Doc:** W1_B2_CONFORMANCE_COORD_20260712.md **v2.2** (v1 23:15 → 5体 fold v2 → %12 PASS + 裁定 fold v2.1 → %9 PASS-WITH-NOTES fold v2.2)
**%12 verify leg = PASS (23:48):** CC4-CRIT 訂正値の npz 独立再計算 = 全 EXACT。**ask B1 = CONFIRM → charter ERRATUM-3 (67d01d0c15、on-disk 照合済):** tail (iii)(iv) = B2 / (i)(ii) = B7。**ask B2 = CONFIRM:** fires bar = shadow 系列 t343±1。
**%9 verify leg = PASS-WITH-NOTES (23:42):** 入口条件 R-1..R-4 全 EXACT (B1 loop 完全 CLOSE) / CC4-CRIT ground truth = %9 banked keys と独立 double-key EXACT / R3m×spec:86 CONCUR / tail (iv) incentive 検算成立。**B2-F1 (MED) = R3h unit fencepost → fold 済 (R3h)**。LOW 3 (div=15.0 等号 / mask event-frame 検出源 pin / N-2 staleness 導出) → fold 済 (R3c/R5c/R10c)。**build GO に %9 異議なし。**
**Author:** %11 (COORD, w2:p3, builder leg) — 2026-07-12 (date-THEN-write)
**Node:** T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild / chunk B2
**Design SSOT:** `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.8.1 §4.1-:78 / §4.2 :80-100 / §4.3 :102-111 (+ §5 :120, §6.1 :132, §8 :159-177, §9 :192)
**Charter:** `W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md` v0.2 B2 行 :35 + §4-2 template (ERRATUM-2 :47)
**[L-TRIAGE]:** final_L = **L3**。直交 [DESIGN-GATE] = cite 充足 — HOLD は reward 成分でない (`STAGEA_REWARD_ARTIFACTS_20260712.md` Artifact 1)、Stage-A design-gate 全 PASS 済 + Rs W0-a 13:29。数値 = Rs W0-a 採択 (15/12/24placeholder)。
**B2 入口条件:** %9 R-1/R-4 = fold 済 (04a31e1e98、B1 CLOSE 確認済)。
**asks A1-A4 = RESOLVED** (%12 2026-07-12 23:29、§4)。
**5体 verdict:** CC2 REVISE (MED2/LOW4) / CC3 REVISE (HIGH2/MED2/LOW2) / CC4 REVISE (**CRIT1**/HIGH2/MED2/LOW3) / CC5 REVISE (HIGH1/MED2/LOW4) / CC6 REVISE (HIGH3/MED2/LOW3)。**CC1 DECIDE = 全 ACCEPT、v2 fold** (§6 fold 対応表)。

**スタイル:** 全行 sub-item 列挙 + on-disk 証拠 1:1 (feedback-conformance-row-verify-per-subitem)。

---

## §1. Scope + 境界 (silent-drop なし)

B2 = ①recording contract v2 ②div_grip metric ③HOLD 状態機械 ④HOLD 凍結面 ⑤query() API ⑥obs 62D 不変 ⑦flag gating + 表面適合 legs ⑧cuda:0 較正 legs ⑨**tail 機構 (iii)(iv) [charter ERRATUM-3 67d01d0c15 で B2 帰属確定 → R13]**。

**B2 に含まない (境界、根拠つき):**
- **recenter(w) per-world 実配線 = B4** (spec §6.1 :132 to-be-built + charter B4 行)。B2 = div 式に項 + zeros identity。
- **fork 時 route_t := bank_boundary[k] / step-0 handover = B3** (spec §4.1 :78)。
- **telemetry export = B5** (spec §5 :120)。B2 = in-memory field + leg JSON dump。
- **claim ① (drift-under-HOLD 実測) = B7** (charter 明記)。**MAX_HOLD 回復時系列の再導出 data も B7** — Δ≡0 leg に回復機構は存在しない (spec :89 stall→timeout が期待挙動; 回復 = bounded-Δ 注入 sub-leg spec §8 :167) [CC2-2 fold — v1 の「凍結後回復時系列 = MAX_HOLD 再導出 data」主張は過大、撤回]。

---

## §2. Conformance 行 (R1-R12)

### R1 — recording contract v2 (spec §4.2 N9 :95)
| sub | 内容 | 実装 site | 証拠 leg |
|---|---|---|---|
| a | `_prepare_recording` req tuple に `cable_xyz` + `held_seg_l` 昇格 | route_executor.py:3123 | unit: 欠落 key → ValueError |
| b | 形状/型検証: `cable_xyz [F, S, 3]` float32 / `held_seg_l [F]` — **`.astype(np.int64)` 正規化 (:3130 phase_id と同型、golden は int16)** [CC3-6]、frame 数一致、`0 ≤ held_seg_l < S` | 同 :3140-3146 域 | unit: 不正形状 → ValueError |
| c | 返り dict に両 array 追加 | 同 :3154-3162 | unit + grep |
| d | env loader recording dict に `z["cable_xyz"]` / `z["held_seg_l"]` 追加。**感度所在の明示 [CC4-7]: ⑨a′ は stub-route (loader 非実行)、producer leg は contract 非通過 — loader diff の被覆 = leg4 cablediag 再実行 + 較正 run** | newton_route_env.py:609-615 | leg4 + 較正 run |
| e | 正典 golden 実在確認済 (on-disk 実測 23:1x): RUN1_REFERENCE_V2 (sha 5f1c3f92…) cable_xyz (7707,40,3) float32 + held_seg_l (7707,) **int16** | — | 本表 + leg log |
| f | **合成 fixture 更新 [CC3-1/CC4-4 訂正: 正 = test_routeexec_writesite.py]:** 合成 recording dict **writesite:244-249** (`_build_executor` 内、consumer :253) + golden transit fixture **writesite:458-472** (4-key rec :464-466) + step_target fixture **test_routeexec_step_target.py:59-60** — 契約昇格で writesite 既存 unit ~10 本が ValueError (fail-loud) → fixture に合成/実 cable_xyz+held_seg_l 追加 | scripts/test_routeexec_writesite.py + test_routeexec_step_target.py | unit 全本再 PASS |
| g | **blast radius 全列挙 [CC3-3]:** RouteExecutor 構築 site = env :621 / writesite :253 + :468 / step_target :60 / state_bank :100 + :209 (**recording=None、非影響 — grep で no-recording site として pin**) / comp3_void_readback.py:350/:363 (flag-ON env 経由、golden は新 key 保有 = 非影響、caller pin に含める) | — | grep 出力 evidence pin (comment 除外 pattern 明文化) |

### R2 — div_grip metric (spec §4.2 :84-87)
| sub | 内容 | 実装 site | 証拠 leg |
|---|---|---|---|
| a | `div_grip(w,t) = ‖cable[s] − rec_cable[s, f] − recenter(w)‖ × 1000 [mm]` | route_executor.py 新 method | unit: 合成 recording 手計算一致 |
| b | `s(route_t) = rec["held_seg_l"][f(route_t)]` (固定 seg24 不採用 [N2]) | 同 | unit: held_seg_l 変化追従 |
| c | `f(route_t) = min(cf[route_t]+9, F−1)` 終端 clamp [L3]、cf 単一源 = `rec["step_f"]` (:3147-3149) — **単一源の discharge = grep pin (unit は 10t 直書きと数値判別不能 [CC4-6])** | 同 | unit: clamp 3 点 + **grep pin** |
| d | `recenter(w)`: B2 = zeros identity、B4 実配線 (§1 境界) | 同 | unit: 非零 recenter 注入で平行移動 assert |
| e | R 腕 metric なし (L-only :85 [L6]) | — | grep: R 系 div ゼロ |
| f | 全 frame 定義 (pre-grasp 含む)、pre-grasp = telemetry のみ (R3g) | 同 | 較正 leg telemetry 非 NaN |
| g | live cable 供給 = env `bq[self._cable_bodies[w], :3]` view | newton_route_env.py (view 組立) | 較正 leg |
| h | **div = 副作用なしの standalone 純関数として実装、query()/sync 更新はその消費者 [CC5-2]** — B3「restore 直後 div ≤ band」DoD が step ループ外 (fork/reset 時) から状態機械を汚さず呼べる affordance | route_executor.py | unit: 純関数呼出が sync_state 不変 assert |

### R3 — HOLD 状態機械 (spec §4.2 :88-94、数値 = Rs W0-a 15/12/24)
| sub | 内容 | 実装 site | 証拠 leg |
|---|---|---|---|
| a | `HOLD_THRESH_MM = 15.0` PROVISIONAL (provenance comment: spec :88 + Rs W0-a) | route_env_config.py (R8) | grep + comment |
| b | 発火: armed ∧ div > 15mm → HOLD | executor sync | unit 状態機械 |
| c | 復帰: div ≤ 12mm OR K=3 連続 in-band (≤15mm) (:93)。**K counter は再発火で必ず 0 リセット — unit 系列は resume→re-fire→再 resume を跨ぐ [CC6-F6]** | 同 | unit: 12 即復帰 / 13×3 復帰 / 13,16,13 非復帰 / **resume→16 再発火→13×1 で非復帰** / **div=15.0 等号境界 (>15 fire、15.0 = no-fire; 12.0 = 即復帰) [%9 LOW]** |
| d | chatter telemetry: resume event + chatter-rate (export = B5) | executor/env field | unit + leg JSON |
| e | 非有限 div = 閾値超過扱い → HOLD + loud event、明示 isfinite 分岐 (:94)。**同 step の explosion terminal との event 重複は dedup/順序 pin (HOLD fire counter を explosion step で膨張させない) [CC6-F8]** | 同 | unit: NaN 注入 |
| f | hold_count per world; `MAX_HOLD_STEPS = 24` placeholder; 超過 = informative loud event、terminate しない (:97) | 同 | unit: 25 step → event + 継続 |
| g | arming = G1-latch 後のみ (`_g_latched[w,0]` :516/:1467 を view 供給)。pre-grasp div = telemetry のみ (:92)。**⚠always-armed bug は nominal 較正 run で両 bar に不可視 (pre-grasp div≈0.007mm) — 被覆は本 unit のみ、と明示 [CC4-3]** | env view + executor | unit: g1=False ∧ div>15 → MARCH |
| h | tail: route_t ≥ n_steps → **div 計算自体を skip** (HOLD 動作無効だけでは不足 — 終端超 index で flag-ON 訓練が step~770 で必ず crash [CC6-F2])。**境界は runtime 導出 (数値 hardcode 禁止; 771-vs-770 fencepost は B7 照合 carry [CC2-5])** | executor | unit: **n=len(step_f) runtime 導出で t=n−1 (compute+clamp assert) / t=n (skip) の対** + t=899 skip [%9 B2-F1 fold: 境界 hardcode 排除で B7 照合と独立に正] |
| i | episode 時計/time-penalty/horizon 継続 — mask は route_t のみ、:1618 不触。**leg6-mirror 拡張 assert は flag-OFF run に scope 限定 (flag-ON は初回発火以降 route_t ≠ episode が正) [CC6-H4]** | env :1618-1622 | leg6 系 assert (flag-OFF scope) |
| j | HOLD 判定 step-0 有効 (§4.1 :78) — fork semantics = B3 carry | — | B3 |
| k | **reset 時 HOLD 状態 clear = 名前付き executor API (world_ids 必須引数) を `_reset_worlds` clear 域 (:1018-1028) から呼ぶ [CC6-F3]** — env は executor 所有の sync state を直接触れない; v1 互換の全 world clear 経路 (global reset :1610 のみ全 world) を per-world reset に流用しない。**neighbor 保全 unit: world A HOLD 中に world B done-reset → A の mode/hold_count/counters byte 不変** | executor 新 API + env :1018-1028 | unit: HOLD world timeout → 復帰 + **neighbor byte-intact** |
| l | **IK 残差 (obs[55:57]) = informative telemetry のみ、clock 作用なし (spec :96 負条項) [CC2-1]** — div/sync/HOLD 判定 branch は IK residual field を読まない | — (実装しない) | grep: HOLD 判定経路に IK residual 参照ゼロ |
| m | **div/HOLD 評価点の pin [CC6-F1 + CC5-3 独立収束]: `_apply_actions_batch` 後・synchronize barrier (:1223 系) 後・`route_t` increment **前**・**pre-increment route_t** で評価** (spec :86「env state は RL step 後 = 終端整合」)。step() 先頭の `_pull_route`/query は packet-read-only (fire/resume を再評価しない)。resume した step は chunk t+1 を駆動 — 凍結 chunk t の staircase を再走しない (N3) | newton_route_env.py step() :1617-1622 間 | unit: **合成 ramp で chunk-t vs t±1 比較を判別** + fire→freeze→resume trace (resume 後 staircase = t+1) |

### R4 — HOLD 凍結面 (spec §4.2 :90 N3)
| sub | 内容 | 実装 site | 証拠 leg |
|---|---|---|---|
| a | route_t 凍結 = increment mask (flag OFF = 無 mask byte-identical) | env :1619-1622 (B1 予約 seam) | R7 legs + unit |
| b | base target 凍結 = 構造的自動 (step_target :3312 純関数、CC3 実証) | — | 較正 leg target 定値 assert |
| c | grip staircase = chunk 終端 cf[t]+9 定値 clamp — **書込 site :3358 と readback assert 内の第二 frame 算出 :3374 の両方に同一適用 (片側のみ = HOLD 中 arming で readback assert 偽爆 [CC3-4])**、default 引数 None = v1 恒等 | route_executor.py:3328 (:3358+:3374) | unit: held world frame = cf[t]+9 固定 (両 site) |
| d | ff replay arm frame 同 clamp (apply_recorded_arm_ff :3381、第二算出点なし [CC3 実証]) | route_executor.py:3381 | unit 同型 |
| e | grip 由来 packet field (grip_2/is_dual/grip schedule) = 全て同一 f_end = min(cf[t]+9, F−1) 統一 (**A2 %12 CONFIRM 23:29**)。**発火 step の 1-step packet 不連続 (MARCH cf[t] → HOLD cf[t]+9) は意図挙動 — `_project_residual` mode flip は凍結 servo 実状態と整合 (CC5-7/CC6-F7 攻撃済・破綻なし)、leg JSON に expected-flip 注記** | executor query 系 | unit: 境界 frame MARCH/HOLD 別値 |
| f | obs[50] 凍結 = 構造的自動 (:1589-1596 route_t 由来、CC3 実証) | — | 較正 leg obs[50] 定値 assert |
| g | phase_id 凍結 = 構造的自動 | — | 同上 |

### R5 — query() API (spec §4.3 :102-111)
| sub | 内容 | 実装 site | 証拠 leg |
|---|---|---|---|
| a | 6-tuple 形状 (:104-108) | route_executor.py + interface | unit: 形状/型 |
| b | sync_state = {mode, hold_count, div_grip [mm], route_t} (:108) | 同 | unit |
| c | validity_mask = phase 別 state-blind mask (W0-c §5 :89、Fact A/B)、packet float32 scalar。**phase 帰属 = 機械導出 (%12 23:29 裁定、推測禁止):** 2 点 = ① grasp-entry XY 導出 (pre-hover: caveat-a Y re-center :3862-3866 + fix-⑤ X-follow、PRE-STEP :3517) ② C2_REGRASP argmin re-target (:4404) [DQ7:64-66] — event frame index を cf 境界に置いて G-clock 帰属導出 + unit pin (導出 ≠ G1/G4 なら導出が勝ち、loud note)。lookup 表に PROVISIONAL comment [CC4-7] | 同 (導出 = build 時) | unit: **導出帰属 pin + event-frame 検出源 (①② の frame index 特定方法) を unit に pin [%9 LOW]** + lookup 全 phase 被覆 |
| d | oracle 読み取り専用: 副作用 = sync_state 更新のみ (:111)。fire/resume の評価点は R3m が governs (query top-of-step = read-only) | 同 | grep: write API 呼出ゼロ |
| e | mid-servo COMMANDED 規約承継 (:110) — **query() target_6d ≡ step_target 基盤の MARCH 等価 assert を unit 化 (既存 unit 承継だけでは新 surface に感度なし [CC2-4])** | — | unit: MARCH 等価 |
| f | route clock 単一源: env 所有 route_t、view = {route_t, cable_pos, g1_latched}; oracle は sync 状態のみ所有 (CC3 実証: executor 内 clock ゼロ) | env + executor | grep |
| g | stub disposition: **init assert は impl type key (`route_executor_impl == "route_executor"` 系、:481-487 precedent) — recording 存在 key だと stub+recorded_targets (:234-238) が late-fail [CC5-5]** (A4 %12 CONFIRM: fail-loud、fail-closed) | newton_route_env.py init | unit: stub+flag → AssertionError |
| h | **query() は RouteInterfaceV1 の抽象 method として typed 6-tuple contract を durable に着地 (docstring だけの prose 契約は B5/Stage-C が再導出する [CC5-6])** | route_env_config.py:143-182 | grep + unit |

### R6 — obs 62D 不変 (spec §4.2 :91)
| sub | 内容 | 証拠 leg |
|---|---|---|
| a | obs 追加なし。claim ③ 登録 → Stage-C | grep + ⑨a′ shape |
| b | contingency (63D+) = Rs 提案経路のみ | — |

### R7 — flag gating + flag-OFF 表面適合 (spec §4.1 :77 + ERRATUM-2)
| sub | 内容 | 証拠 leg |
|---|---|---|
| a | 全機構 `_route_t_clock` gate 下 (default False) | grep |
| b | OFF: 無 mask / 従来 path / clamp 恒等 / div 実行ゼロ | unit + legs |
| c | env 側: ⑨a′ EXACT + DoD⑤⑥⑩ + cablediag byte-anchor (311f18cb9b) | leg JSON + stdout pin |
| d | producer 5-cell byte-repro (ca33d1e1a0) | leg JSON |
| e | comparator = full-dict-diff − 既知変動 key | run_legs.sh |
| f | runner exit gating + stale-artifact rm + stdout run 時 pin | run_legs.sh |
| g | **ON 時挙動 (route_t/HOLD) = Layer-B re-BASELINE として Rs-visible 宣言 — B2 commit relay + W1 完了報告に明記 (spec §4.1 :77 第 2 節) [CC2-6]** | 報告文面 |

### R8 — 定数配置 (**A3 %12 CONFIRM 23:29: rc.\***)
| sub | 内容 | 証拠 |
|---|---|---|
| a | 4 定数を route_env_config.py に配置 + PROVISIONAL/Rs W0-a provenance + 再導出条項 comment。**`_ROUTE_OWNED_PARAM_NAMES` guard set (:188-210) に 4 定数追加 (既存規約) [CC3-5]** | grep + comment |
| b | task_config.py 不触 (spec footer 宣言 + DELTA_BOUND_M precedent :405-406) | git diff file list |

### R9 — telemetry 格納 (B5 境界、spec §5 :120)
| sub | 内容 | 証拠 |
|---|---|---|
| a | per-world field: HOLD 発火/resume/chatter-rate/hold_count/**live div_grip + mode (§5 export 列の per-transition field — sync_state 返り値だけでは B5 が格納元を持たない [CC5-4])**/pre-grasp div/MAX_HOLD 超過 | leg JSON dump |
| b | B2 leg は field 直読 (export 経由でない) | leg script |
| c | **counter lifecycle 表 [CC6-F5]: 各 field に per-episode / cumulative の別 + reset site を pin** — mode/hold_count/in-band K = per-episode (R3k clear); 発火/resume/chatter/MAX_HOLD event = **per-episode counter (R3k で clear、B5 export は episode flush 単位 = spec §5 :123 per-episode shard と整合)**; leg JSON は episode 境界で segment | 実装 comment + unit (R3k neighbor unit と同居) |

### R10 — DoD legs (charter B2 行 :35) — **⭐CC4-1 CRIT fold: bar 全面訂正 (v1 の f→route_t/10 換算 = 10× index 誤読)**
**Ground truth (CC4 on-disk 実測、comp5_c2seat_fullfire_cablediag.npz — diag row = RL step):** spec :88 の f 表記 = **RL step index**。div_seg24 max (t≤336) = 10.558mm / 初回 >15mm = **t=343** / grip-loss t397 / pad 接触 t=97 / phase-1 entry t=113 / 54 = t397−343。charter「f343±1 chunk」= **RL step 343 ± 1 step** (1 chunk = 1 RL step = 10 物理 frame)。
| sub | 内容 | pin |
|---|---|---|
| a | **hold-quiet:** armed 域 **t ∈ [g1_latch_t, 336] (RL steps)** で発火 0 — **g1_latch_t を assert + JSON pin (推定 ~97-113; 未 latch なら leg FAIL = arming 検証不能) [CC4-3]** — cuda:0 (W-2) | leg JSON + stdout |
| b | **hold-fires:** **shadow 系列 (comp5 互換: 固定 seg24 @ 10t+3) の初回 >15mm crossing = t343±1** (= comp5 再現 = build 正しさの直接 bar) + **正整合 系列 (held-seg @ 10t+9、実発火 metric) の crossing/実発火 t を記録** — 正整合は系統 shift ≤~1.3 step (staleness 1.31mm ÷ ramp ~1.05mm/step [CC4-2 実測]) で t341-345 が正当 → shadow-bar PASS ∧ 正整合 shift ≤ budget = PASS-with-attribution (**bar 帰属の disposition = §4 ask B2、%12 confirm**)。同一 499-step residual≡0 replay 1 本、flag ON、world_count=1、**CUDA_VISIBLE_DEVICES=0 assert を leg script 内部に (wrapper だけでない) [CC4-8]** | 同 |
| c | leg 記録 (診断可能性 [CC4-2]): 正整合 + shadow 両系列全長 / per-t {f_used, s_used, armed, mode, done, termination_reason} / crossing−1/0/+1 の div / g1_latch_t / **zero-dones assert (mid-leg done = 系列汚染 → 発生時は episode segment 化 [CC6-F4])**。正整合健全域 max = §8/B3 band 再導出 data (spec :86)。**回復時系列は取れない (Δ≡0) — MAX_HOLD 再導出 = B7 bounded-Δ 注入 sub-leg [CC2-2]**。**staleness 予算の導出を leg JSON に pin (%9 N-2: 局所 ramp 実測 1.01-1.23mm/step × 6/10 ≈ 0.52-0.74mm ≈ 弁別力 ~0.6-0.7 step < 1.31mm 名目 — 正直注記)** | 同 |
| d | unit legs (CPU): R1a/b/f 契約 / R2a-d/h / R3b,c,e,f,g,h,k,l,m / R4c,d,e / R5a,b,c,e,g,h — **R3i (leg6 flag-OFF scope) + R3k (neighbor 保全) を roster に明記 [CC4-5]** | unit stdout pin |
| e | claim ① = B7 carry | R11 |
| f | flag-OFF legs = R7c/d | leg JSON |

### R11 — carries + 登録 claim
| 先 | 項目 |
|---|---|
| B3 | fork latch pre-set / route_t := bank_boundary[k] + post-fork assert / writesite 期待値反転 / forbid 撤去 / k0 不変量 / step-0 handover / restore 直後 div ≤ band (R10c 正整合再計測が governs、**R2h 純関数がその affordance**) |
| B4 | recenter 実配線 (R2d hook) / curriculum start-mix |
| B5 | R9 field export (R9c lifecycle 表が per-episode 単位を pin; **suppressed-drop event は tail (iv) 機構 [§4 ask B1] が前提**) |
| B7 | claim ① / **MAX_HOLD 再導出 = bounded-Δ 注入 sub-leg (spec §8 :167 EE→cable gain 実測) [CC2-2]** / gate-iii 25-set / **§8 残 leg = charter B7 catch-all (per-cell/per-seed nomA/nomB 閾値安全側検証 :88 含む) [CC2-3]** / **tail 境界 770-vs-771 horizon 算術照合 (spec :165) [CC2-5]** / **tail 検査 (i)/(ii) (spec §9 :192) [CC5-1、§4 ask B1]** |
| Stage-C | claim ③ (HOLD-resume rate telemetry) |
| 登録 claim | 「seat は HOLD を跨いで持続」(p3×HOLD :98) — G3-stall (B5) + bank-G3 fork leg (B7) |
| 報告 duty | **Layer-B re-BASELINE Rs-visible 宣言 (R7g) — B2 commit relay + W1 完了報告 [CC2-6]** |

### R13 — tail 機構 (spec §9 :192 + charter ERRATUM-3 67d01d0c15) [v2.1 新設]
| sub | 内容 | 実装 site | 証拠 leg |
|---|---|---|---|
| a | (iii) HOLD 無効 = 終端域 div 計算 skip — R3h が実装 (charter ERRATUM-3 の (iii) 文言「終端域 div 計算 skip」と一致) | R3h | R3h unit |
| b | **(iv) 予定 release (route_t ≥ release 境界) 後は drop terminal を無効化** — 根拠 (spec :192): 意図的 release 後の「drop」= category error、放置で fail-slow (−7.6) < fail-fast (−3.99) の逆転 incentive。無効化後は timeout close (+1.00 系) で S4 系 scenario 復元。**suppression scope = post-release のみ — pre-release の drop 述語は一切不変 (S5 保全) [%9 条件 fold]** | env `_compute_rewards_dones_batch` drop 述語 :1473-1480 | unit: post-release で drop 条件成立 → terminal なし + event 記録 / **pre-release drop → 従来 terminal (S5)** / flag OFF → 従来 terminal |
| c | release 境界 = 記録 grip schedule から導出 (両手 release ~frame 7617 ≈ step 762 [step_target docstring :3297-3298]; 最終 both-closed frame → chunk 境界切上げ、hardcode 禁止) — oracle 側で導出し env へ供給 | route_executor.py (導出) + env (消費) | unit: 導出値 pin |
| d | suppressed-drop event 記録 (spec §5 :120 L2 — /metrics/drop_count の cross-version 比較歪み防止; B5 export の前提 field を B2 が生成) → R9a field に追加 | env field | unit b と同居 |
| e | **flag gating: (iv) は `_route_t_clock` gate 下** (ON 時挙動 = Layer-B re-BASELINE R7g に含めて宣言; OFF = 従来 drop terminal 挙動 byte-identical — ERRATUM-2 legs が担保) | env | R7 legs |

### R12 — 変更 file 一覧 + LOC (charter est: ~200-300 + 50-100)
| file | 内容 | est LOC |
|---|---|---|
| thread_isaac_lab/envs/route_executor.py | contract v2 + div 純関数 + sync/query + clamp (両 site) + clear API | ~170-240 |
| thread_isaac_lab/envs/newton_route_env.py | view 組立 + R3m 評価点 + increment mask + init assert (impl-type key) + clear 呼出 | ~60-100 |
| thread_isaac_lab/envs/route_env_config.py | 定数 4 + guard set + RouteInterfaceV1.query 抽象 method | ~30-50 |
| thread_isaac_lab/scripts/**test_routeexec_writesite.py** | **fixture 更新 (:244-249 / :458-472) [CC3-1/2]** | ~10-25 |
| thread_isaac_lab/scripts/test_routeexec_step_target.py | fixture (:59-60) + unit legs 追加 | ~80-140 |

---

## §3. [VERIFY] 5体 — 完了 (scope = implementation-plan-vs-spec fidelity)

CC2 spec 忠実 (~35 clause 全数照合、境界 4 件 = 正当) / CC3 コード接合 (全 seam on-disk 実証、CRIT ゼロ) / CC4 leg 感度 (**CRIT: bar 10× 誤読**) / CC5 界面 (tail no-owner) / CC6 動態 (評価点/tail crash/reset 漏れ)。CC1 DECIDE = **全 finding ACCEPT → 本 v2** (設計変更なし — 全て conformance/leg/実装計画の訂正)。

## §4. asks

**RESOLVED (%12 23:29):** A1 = encoding CONFIRM + 帰属機械導出 (R5c) / A2 = CONFIRM 同一 f_end 統一 (R4e) / A3 = CONFIRM rc.* (R8) / A4 = CONFIRM fail-loud (R5g)。

**RESOLVED (%12 23:48、charter ERRATUM-3 = 67d01d0c15 on-disk 照合済):**
- **B1 (tail 所有権) = CONFIRM:** (iii)(iv) 機構 = B2 (→ R13 新設) / (i)(ii) 検証 = B7 (+ 771-vs-770 照合 carry も B7 行に pin 済)。
- **B2 (fires bar 帰属) = CONFIRM:** shadow 系列 (固定 seg24 @10t+3、diag 同一) で t343±1 = bar (n=1 基準と apples-to-apples) / 正整合系列 = 記録+帰属 (band 再導出 data、系統 shift ~1.3 step 予算明記) — spec §0 N4/L3 の再計測計画そのもの (→ R10b 確定)。

## §5. 手順 disposition

conformance v2.2 (本 doc) → %12 verify **PASS** (23:48) + %9 verify **PASS-WITH-NOTES** (23:42、fold 済) = **joint verify CLOSE、build GO** → **[RULE-CHECK] Tier0-3 (今ここ)** → build → DoD legs (R10+R13) → post-verify 3-leg → explicit-path atomic commit → p6 relay。

## §7. post-build leg 結果 (v2.3 追記、2026-07-13 00:3x JST — 全 leg PASS)

| leg | 結果 | 実測 |
|---|---|---|
| 1 ⑨a′ | **PASS** | full-dict-diff (−variant) = 空 |
| 2 DoD⑤⑩ | **PASS** | semantic diff = 空; 除外 = throughput 3 key のみ (4.60 vs 4.94 rl_sps 等、値も log 記録) — comparator VAR に throughput/sps 追加 (初回 run で filter 漏れ→FAIL を検出、修正後再走) |
| 3 DoD⑥ | **PASS** | dict-identical |
| 4 cablediag | **PASS** | 全 array EXACT vs banked 311f18cb9b |
| 5 producer 5-cell | **PASS** | npz sha256 byte-id 5/5 vs ca33d1e1a0 |
| 6 unit 3 suite | **PASS** | stdout pin 済 (step_target [B2 群 5 本込] / writesite [hold-clamp 両 site 込] / state_bank) |
| 7 reset 隔離 | **PASS** | dones=[F,T]、w0 counters (7,3,2) byte-intact / w1 cleared |
| 8 較正 | **PASS** | 下記 |

**leg8 実測 (cuda:0、499-step residual≡0、flag ON、comp5-faithful cfg):**
- g1_latch_t = **98** (予測 ~97-113 内) / armed 域 (t98-336) 発火 **0** / armed 域 aligned div max = **10.407mm** (spec §6.2 の held-seg 正整合予測 10.41 と一致 — band 再導出 data として JSON pin)
- aligned 発火 = **t342 単発** (bar {342,343,344} 内) / dones = **0** / MAX_HOLD 超過 event = informative 1 回 (terminate なし、実挙動確認)
- **⭐shadow bar の discharge 形 (ask C1) = %12 CONFIRM (2026-07-13 01:0x) + %9 CONFIRM 推奨 (00:58):** 正しい aligned HOLD (参照 6 frame 先行) は shadow 交差の ~1 step 前に発火して march を止めるため、**flag ON run では shadow の 15mm 交差は反実仮想** (live 交差を bar 化すると「HOLD が正しく働くほど FAIL」の自己反駁 bar — %12 論拠記録)。discharge 3 述語: (i) live shadow prefix ≡ **banked comp5 div_seg24 系列 EXACT (max diff 0.000000mm / 343 step)** = n=1 基準 ramp の同一性 (%9: 原 crossing bar より**厳密に強い** — 全 step 値 pin は交差 index を含意) (ii) **banked 系列の交差 = t343 ∈ bar** = ramp の index (iii) aligned 発火帰属 delta = **−1 step** (aligned は chunk 終端 = shadow の 10t+3 より 6 frame 先読みゆえ先行発火が正、系統予算 0.6-1.3 step 内)。**⭐副次 (%12): armed quiet max 10.407mm ≈ spec §6.2 L7 予測 10.41 (n=1) の独立確認 — restore-fidelity band の再計測値として governs (B3 が消費)。**
- 凍結後 drift 系列 (claim ① / MAX_HOLD 再導出の参考 data) = JSON rows に全 pin。

## §6. 5体 fold 対応表 (v1 → v2)

| finding | sev | fold 先 |
|---|---|---|
| CC4-1 bar 10× 誤読 | **CRIT** | R10a/b/c 全面訂正 + §4 ask B2 |
| CC3-1/CC4-4 fixture 誤 file | HIGH/MED | R1f/R12 |
| CC3-2 writesite file 漏れ | HIGH | R12 |
| CC5-1 tail (i)/(ii)/(iv) no-owner | HIGH | §1 ⑨ + R11 + §4 ask B1 |
| CC6-F1/CC5-3 評価点未 pin | HIGH/MED | R3m 新設 + R5d |
| CC6-F2 tail IndexError | HIGH | R3h 強化 |
| CC6-F3 reset 漏れ/clear API | HIGH | R3k 強化 + R9c |
| CC4-3 g1_latch 未記録 | HIGH | R10a |
| CC4-2 ±1 bar 誤差予算 | HIGH | R10b/c + ask B2 |
| CC2-1 IK 残差負条項 | MED | R3l 新設 |
| CC2-2 回復時系列過大主張 | MED | §1 境界 + R10c + R11 B7 |
| CC5-2 div 純関数 | MED | R2h 新設 |
| CC6-F4 leg done 汚染 | MED | R10c |
| CC6-F5 counter lifecycle | MED | R9c 新設 |
| CC3-3 blast radius | MED | R1g |
| CC3-4 clamp 第二 site | MED | R4c |
| CC4-5 roster 漏れ | MED | R10d |
| CC2-3/4/5/6, CC3-5/6, CC5-4/5/6/7, CC6-F6/F7/F8/H4, CC4-6/7/8 | LOW | R11/R5e/R3h/R7g/R8a/R1b/R9a/R5g/R5h/R4e/R3c/R4e/R3e/R3i/R2c/R5c/R10b (各行に [tag] 明記) |
