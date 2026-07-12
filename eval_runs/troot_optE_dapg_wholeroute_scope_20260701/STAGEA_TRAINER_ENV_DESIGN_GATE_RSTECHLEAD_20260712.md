# Stage-A: P2 env trainer-grade 拡張 — DESIGN-GATE SPEC (W0-c delta)

**Author:** RS-TECH-LEAD (%12/w2:p4)。**Date:** 2026-07-12 10:36 JST 初稿。**Node:** `T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA`。
**Status:** DRAFT v0.8 (design-gate 審議物)。⚠C6: §0 の cablediag 生成元 (comp5 runner _DIAG 拡張 +122/-4) は %11 の uncommitted tree — spec 最終 bank と同時に commit or sha pin (bank 手順に含む)。PAPER-ONLY / 0-build / 0-GPU (probe は既存 npz の CPU 解析のみ)。campaign は HIGH-COST + production-launch-gate + fresh Rs GO 背後で不変。
**改版:** v0.1 10:36 初稿 → v0.2 10:4x (/reward-design PASS-with-2-folds) → v0.3 11:0x (/pre-check 1走目 = BLOCK 12 issues 全 fold — §13.1。主変更: cable-metric HOLD / bank v2 昇格 / per-world route-clock / OG legs 再設計) → **v0.4 11:3x (/pre-check 2走目 = BLOCK [fold 9/12 実 + 3 partial、新規 9: N1 CRIT / N2 HIGH / 5 MED / 2 LOW] 全 fold — §13.2。主変更: 基板事実の再解釈 [N1: comp5 = residual≡0 canonical 構成 → nominal-quiet band は本基板に存在せず、HOLD@t≈343 は正しい警報 — FORK-1 実体そのもの] / div_grip segment 規則 pin [N2: held_seg_l 追従] / tail 強制 release 後 drop 無効化 [N6] / bank capture = producer 経路 [N1c] / 実測値の precise 再表記 [N5/N7])** → **v0.5 11:5x (/pre-check 3走目 = BLOCK-narrow [9 N-fold 全 VERIFIED + partial 3 CLOSED; 残 ISSUE-A HIGH 単位系 + B/C LOW] 全 fold: 全 diag 由来 rate を mm/RL-step に訂正 [charter §7 ERRATUM 連動] / D-2「構造的敗北」撤回 / claim ① 再導出 / DR-corner bar 差替え / bank capture artifact pin / resume telemetry field)** → **v0.6 12:0x (4走目 = WARN 条件付き PASS — stale 行 7 箇所の機械整合 [R1-R4 + artifacts 3 行]、verifier「diff 自己確認で足りる、再 pass 不要」)** → **v0.7 12:1x (%11 cross-PV = CONCUR-with-CORRECTIONS 6 件 fold: ⭐C1 no-C2 quiet 誤読撤回 [dd7c97d480 = byte-identical 発散、quiet は producer 経路のみ] / C2 bank = cable joint-space q/qd + qd 非 zero restore / C3 capture 実装先 = 抽出 twin or monkeypatch [locked 不触] / C4 flag-OFF byte-preserve leg / C5 env-level restore 再掲 / C6 uncommitted cite の bank 時 pin。artifact = STAGEA_CROSSPV_COORD_20260712.md fb9000b476)** → **v0.8 12:4x (5体 [VERIFY] DECIDE=FAIL cycle-1 → 27 項 fold [HIGH 7 / MED 13 / LOW 7]、§13.3 disposition)**。
**Authority chain:** trainer charter `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md` §3-A → devplan `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md` §6/§5-R2/§4.3 → 基底 spec = `P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md` v1.5h (**banked basis** — 本 doc は v1.5h を変更せず、その上の trainer-grade **delta のみ**)。
**決定権:** 数値閾値・OG band・DR 既定 ON = Rs W0-a (OPEN 維持)。設計意味論 = Rs autonomy grant (07-12 08:xx) 下の p4⇄p1 co-decide、**Rs veto point = W0-a review**。

**用語定義 (なんでも明瞭に):** oracle-query-API = 実行時に「script はこの状態で何をするか」を返す照会窓口 / Δ (residual) = policy が出す per-step 非累積補正 offset / OG (offline gate) = GPU 不要の忘却警報計器 / DR = 環境条件の意図的ばらつき / decimation = RL 1 step あたり物理 frame 数 (=10) / state-bank = phase 途中状態の保存・復元機構 / CRIT1 = 「policy 逸脱時に phase 時計を誰が進めるか」問題 / div_seg24 = 把持 cable segment の記録軌道からの乖離距離 [mm] / route_t = route 進行時計 (episode 時計と分離、§4.1) / **F-1a = W0-e seat-guide の C2-X 補償 clamp ±22mm (W0E_5TAI_DECIDE_20260705.md:23 — 累積・単軸・locked-runner 内部機構) (v0.8 5体-fold H2)**。

---

## §0. Grounding (アンカー + code 実体、全て on-disk 確認 2026-07-12 10:2x-11:0x)

| Anchor | Cite | 使用 fact |
|---|---|---|
| Stage-A DoD 列挙 | charter §3 Stage-A row | 設計対象 8 項の正典列挙 |
| P4 Δ-bound discharge | charter §7 **+ ERRATUM 2026-07-12 (単位) + %9 再検証 script v2 sha a2ad75955d (supersedes fdcacf98、margin 10.78×、FEASIBLE 不変)** | per-step drift \|inc\| mean 0.27 / p95 1.08 / max 1.86 — **単位は mm/RL-step (charter 原文の mm/frame は mislabel、ISSUE-A)**; 結論方向は不変 (保守側誤り) |
| decimation 確定 | `newton_route_env.py:407` ≡ `route_executor.py:88` (cross-assert `:578`) | d=10 固定 → §2 pin 可能 |
| 既存 Δ clamp / σ-cap | `newton_route_env.py:405-406` | DELTA_BOUND_M=0.020 / GRIPPING_ARM_SIGMA_CAP_M=0.002 |
| route interface | `route_env_config.py:143-180` | v1 契約 (scalar-k、per-world 無し — §4.1 で v2 拡張) |
| **⑦(b) state-bank 実能力 (v0.3 訂正)** | `route_executor.py:381-385` (qd=**zeros**)、`:427-433` (bank = arm/gripper q のみ、**cable 状態なし**)、`:3235-3240` (`reset_to_phase(k≥1)` は **raise** — cable re-seed unwired を code 自身が明示)、`newton_route_env.py:567-568` (cable-fork re-seed を本 stage に defer) | **bank は arm/gripper qpos 復元のみが既存。cable re-seed = 本 gate の build 設計項 (§6.2)。v0.2 の「qpos+qvel+cable_xyz 込 live bank」は over-read で撤回** |
| route-clock 現実装 | `newton_route_env.py:1597-1598` (`_pull_route` が `episode_length_buf` を直結)、`:1155/:1198` (grip staircase)、`:1600-1604` (obs[50] phase-entry) | 時計消費者 4 系統の列挙 (§4.1) |
| **一次データ (v0.4 precise 再表記、N1/N5/N7)** | `comp5_c2seat_fullfire_cablediag.npz` (499 frame) + 生成元 `comp5_c2seat_fullfire.py:130-155` | **⚠ 本 run = residual≡0 の canonical 構成そのもの (feedforward 駆動 + C2 scene + zero action) — 「失敗 run」ではなく nominal open-loop replay が FORK-1 で発散する基板事実の実測**。div_seg24: 健全域 (f0-336、dual-grip+transit 前半) max 10.56mm / f337 から連続 ramp、15mm 超え = f343、以後 **98.7% 単調** (2/155 step で ≤0.44mm 減少) / onset→58mm = **54 RL steps (540 frames、v0.5 単位訂正)** 猶予 / 窓別 \|inc\| mean (**絶対値 mean、単位 = mm/RL-step — diag は env.step 毎 sample [ISSUE-A]**): diag-phase0-2 = 0.077/0.287/0.159、diag-phase3 = 0.577 p95 1.229 **max 1.940** mm/RL-step (**⚠ banked charter §7 P4 の「mm/frame」は同データの mislabel — ERRATUM 発行 + p1 通知、records-must-match-fact**) / 基準 frame 整合: diag は t·10+3 比較 = 系統 staleness ≤1.07mm (固定 seg24) / ≤1.31mm (held seg 追従時) 混入 (v0.8 5体-fold L3) (§4.2 で比較 frame を pin、§8 legs で正整合再計測) |
| **FORK-1 基板事実 (v0.4 追加、N1)** | 上行 + routeexec state.md 04:18 ((a1) 確定) + no-C2 control byte-id `dd7c97d480` | **trainer env (C2 scene) 上に nominal-quiet band は存在しない** — nominal replay 自体が t≈343 で発散開始し t≈498 (mid-G4 相当) で死ぬ。quiet が成立するのは **producer 経路 (58/81 byte-repro) のみ — かつ producer 経路に HOLD 機構は無いため、full-route HOLD-quiet leg の実行基板はどこにも存在しない (quiet 検証 = 健全域 f0-336 のみ、scene 不問)** — ⚠v0.7 C1 訂正 (%11 cross-PV): no-C2 control `dd7c97d480` は「quiet」ではなく **byte-identical に発散** (grip-loss t397 / early-done t499) — それこそが comp5 exoneration の機構。v0.6 の「no-C2 = quiet」は byte-id の誤読で撤回。**帰結: HOLD が residual≡0 で発火するのは偽発火でなく正しい警報 = 本 env の存在理由。closed-loop 補正 (trainer) が唯一の fix (charter 定義) であり、FORK-1 は precondition でなく本 node の解決対象** |
| tail LOUD flag | `route_executor.py:3261-3265` | 記録終端後 ~139 step の semantics = 本 stage 帰属 (§9 行) |
| OG 現物 | `og_offline_gate.py:7-13` (**no-sim 契約**) + `:26-39` bars | port 制約 (§7) |
| CABLE_XY_OFFSET 現 reader | `test_newton_clip_routing.py:8113` (os.environ) + `route_demo_recorder.py:321` (meta 権威) | env-level wiring 不在 (§6.1) |
| base-DR-SR 82.4% | v1.5h §2 学習対象行 | **⚠ mechanism-non-transferable (pre-check MED-12): locked-runner live-recompute 経路の実測であり、recorded-staircase + stored-recenter の oracle 経路には転送不能 — 参考値に降格。oracle 経路の DR 到達性は §8 smoke leg で実測** |
| env-core 実装済 inventory | `route_env_config.py:45-67` + `newton_route_env.py:1082-1102` + env-core DoD⑤ (f6ee1443f5 (初回 build) → HEAD (lane-floor fix 等 3 commits 込み、1640L)) | §1 境界 |
| **grounding 基準 tree (v0.8 5体-fold H4)** | git HEAD `fb9000b476` + dirty deltas: newton_route_env.py +23L (route_c1_pin、gated-OFF、FORK-1 fix 仮説 = REFUTED disposition-pending) / route_executor.py +70L (同 arc) / og_offline_gate.py (format-only) | spec の行番号 cite は dirty tree 基準。c1pin diff の disposition (bank or revert) = build 前提条件: revert なら consumer ③ は ff replay のみに縮退 / keep なら per-world 化 (route_steps[0] 単一 world 読み + global _c1_pin_done latch + mjm.eq_data 共有 = multi-world 汚染 3 点) の再設計が必須 |

## §1. Scope 境界 — env-core 済み vs Stage-A delta (silent-drop なし)

| charter §3-A 項 | env-core 状態 (cite) | Stage-A 設計 delta |
|---|---|---|
| §6-2 progress scalar | 済 — obs[50] (`route_env_config.py:56`) | HOLD 凍結時の semantics のみ (§4.1) |
| §6-9 Δ 非累積 + drift-zero | 機構済 (DoD⑤ 0.0 EXACT + DoD⑩) | Δ-bound 正式 pin + **subspace 分解 D-2** (§2) |
| §6-3 contract 統一 | 決定済 62D/α-6D | demo 62D 再変換 検収設計 (§3) + OG port (§7) |
| §6-1/§6-10 oracle API + CRIT1 | 不在 (v1 契約 + stub のみ; `reset_to_phase(k≥1)` raise) | **§4 (重量級: per-world route_t + cable-metric HOLD)** |
| §6-4 transition export | 不在 (extras.info に部分土台 `:1554-1566`) | §5 |
| §6-5 reward 成分ログ + events | 不在 | §5 (override 会計込み) |
| §6-6 DR hooks | 不在 | §6.1 |
| ⑦(b) curriculum-reset | **arm/gripper 復元のみ既存 — cable re-seed unwired (`:3235-3240`)** | §6.2 (**cable re-seed build 設計 + per-world fork 昇格**) |
| §4.3-a/b/c OG port | 不在 (27D 契約) | §7 (**legs 全面再設計**) |
| §6-8 throughput + parity smoke | 半済 (19.76 fps @cuda:0; parity 未) | §8 (**+4 legs 追加**) |
| **tail semantics (~139 step、記録終端後)** | env-core 挙動のまま (LOUD flag `:3261-3265`) | **§9 行 (v0.3 追加、MED-10)** |
| **devplan §6-7 決定性/seed + nomA/nomB band** | env-core: seed 固定は既存 / band 標準機能 = 未 | **Stage-A 設計項 (v0.8 5体-fold H3): per-world seed 方針 + nomA/nomB band 計測 mode を env 標準機能に (partially §5 provenance fields で担保、機構設計 = build 項) + §10 cost 行** |
| **devplan §6-12 guards** | env-core 済 (mujoco assert :548-551 / time_outs 純度 :1539-1541 / span (b′)) | **delta 相互作用のみ (v0.8 5体-fold H3): HOLD 凍結は span-guard 窓 (grip-schedule 駆動) も単一源で凍結 = fail-safe 方向 (§4.2 既記載) — 追加設計なし** |

## §2. Δ-bound 正式 pin + subspace 分解 (§6-9 discharge)

**Pin: `DELTA_BOUND_M = 0.020` 採択。** 導出鎖 (**v0.5 単位訂正、ISSUE-A**): cablediag は env.step 毎 sample = **diff は mm/RL-step** (mm/frame は誤 — banked charter §7 の P4 も同 mislabel、ERRATUM 発行済 + p1 通知)。必要 per-RL-step 補正 = 実測 drift **max 1.94 mm/RL-step** ≪ pin 20.0 ≤ 22mm (F-1a precedent — ⚠v0.8 5体-fold H2: これは『授権 envelope』ではなく Rs 承認済み scripted 設計における最大 per-target offset の precedent/analogy。Δ-bound pin は実測 headroom (~10×) + Rs W0-a veto で自立し、この anchor に依存しない) — **headroom ~10×、v0.4 の「margin 0.6mm 危機」表現は単位二重計上による虚報として撤回**。max 基準・保守方向 (open-loop ≥ closed-loop) は不変。per-frame rate は未計測 (上界 = per-step 値のみ既知) と明記。

**D-2 subspace 分解 (v0.5 単位訂正済):** 拘束 subspace の実測 (cablediag npz、residual≡0 canonical run、単位 = mm/RL-step):
- **transit 域 (diag-phase3): drift mean 0.577 / p95 1.229 / max 1.940 mm/RL-step vs σ-cap 2mm/step** — **cap ≥ mean (max 1.94 は marginal)。v0.4 の「構造的に敗ける」は単位誤りで data-false、撤回**。正しい状況: σ-cap 補正容量は平均 drift を上回るが、**補正の十分性 (policy が実際に div を減らせるか) は未実証** — HOLD の正当化は N1 の警報 framing (march 除去 = fail-safe) に立脚し、補正十分性は §8 hold-fires leg が実測する。
- **falsifiable claim ① (v0.5 再導出): 「route_t 凍結は drift 駆動を除去する — drift-under-HOLD (Δ≡0) < drift-with-march 同区間実測 (mean 0.58 mm/RL-step)」** — march が drift の主駆動という機構主張を直接弁別する bar (v0.4 の <2mm/step bar は march 込みでも満たされ弁別力ゼロだった)。反証時 = HOLD の機構解釈見直し + σ-cap contingency (§9) 発動。
- **claim ① n=1 事前証拠 (v0.8 5体-fold M2、CC4 実測):** 記録 march 速度と |div inc| の相関 0.474; march<0.1mm の chunk (n=67) で drift 0.169mm/step vs march 込み 0.577 → 凍結で ~3.4× 減の見込み。⚠残余 creep 0.169>0: 未訓練 (Δ≈0) HOLD では ~195 step で contact-loss drop (−10) に到達し得る — 未訓練終端は timeout でなく drop の可能性 (falsifiable ① の測定対象に含める)。
- **dual-grip 域 (diag-phase0-2): 無補正 open-loop でも div ≤ 10.56mm 有界 (n=1)** — 両腕拘束が自己制限的。
- DR 条件下 drift rate 未実測 → **§8 DR-corner leg で再計測 (alert bar: >10 mm/RL-step = headroom 半減で W0-a 上程 / breach: >20 = pin 破綻)** — v0.4 の >2.0mm/frame bar は単位誤りで nominal が既に抵触する無意味 bar だったため差替え。
- **Δ-bound 飽和 telemetry** (per-step ‖Δ‖/bound 比) = §5 export 項 (R2b abort 診断一次データ)。

## §3. contract 統一の残置 leg — demo 62D 再変換 検収設計 (§6-3、v0.2 から不変)

1. phase one-hot = 記録 state 上で env 述語評価 (schedule 写像でない) + converter-vs-env 境界一致 check = 検収 DoD。
2. [50] progress = env-side と同一導出式。
3. 記録に無い dim = 0-fill + validity column (meta)。「実測 0」と区別。
4. 検収 numerator: canonical demo 全 frame で converter obs ≡ env obs (L∞ ≤ FP32 再現誤差) — ⑨a 型 leg の 62D 拡張。

## §4. oracle-query-API + CRIT1 phase-clock (§6-1/§6-10 — 本 gate の重量級、v0.3 全面改稿)

### 4.1 per-world route-clock `route_t` (CRIT-2/MED-9 fold — HOLD の前提配管)

- **新 state: `route_t[world_id]`** (per-world int)。episode 時計 (`episode_length_buf`) と分離: episode 時計は常に進む (time-penalty / horizon / timeout)、route_t は HOLD で凍結・bank 開始で `bank_boundary_step[k]` に初期化。
- **単一源規律: 時計消費者 4 系統を全て route_t に付け替える** — ① `step_target(route_t)` (`:1597-1598`) ② grip staircase frame lookup (`:1155/:1198`) ③ ff replay / c1-pin onset (`:1155-1173`) ④ obs[50] within-phase progress (`:1600-1604`、**HOLD 中は route_t と共に凍結** — policy が「進行が止まっている」を正しく観測する。phase-entry 簿記も route_t 基準に変更)。episode 時計を読む消費者を 1 つでも残すと HOLD で desync する (pre-check MED-9) — build DoD = 「episode_length_buf を route 系が参照しない」grep leg。
- **interface v2 (v0.8 5体-fold H6):** `reset_to_phase(k, world_ids=None)` — 既定 None = v1 全 world 互換 (AGENTS.md deprecation 準拠、breaking-change でない)。v1 consumer 5 点の disposition: NominalRouteStub (:241) = 互換のまま / RouteExecutor (:3224) = world-slice 実装 + `forbid_banked_fork` は bank v2 完成で撤去 (raise 条件 = cable re-seed unwired の解消) / env reset() :1617 = 互換 / test_routeexec_writesite.py:334-344 (k≥1 raise assert) = bank v2 後に期待値反転で更新 / test_routeexec_state_bank.py:120 = world-slice case 追加。**新規 consumer #6 (v0.8 H6; v1 の 5 点に追加): step() の per-world done-reset (:1631-1633 _reset_worlds) が curriculum 時に per-world re-fork を呼ぶ — 現 code は route interface を呼ばない、build で追加必須**
- **実装は flag-gate default-OFF (v0.8 5体-fold H5)** (envcore state.md:73 Rs 裁定: COMPLETE component の cross-node 編集は flag-gated + OFF byte-identical + regression leg 必須)。ON 時挙動変更 (route_t/HOLD) は Layer-B re-BASELINE として Rs-visible に宣言。
- **step-0 handover semantics:** route_t := bank_boundary[k]、grip servo = banked `grip_target` から seed (記録 staircase の frame-0 OPEN で上書きしない)、HOLD 判定は 1 step 目から有効 (metric は §4.2 の cable 基準ゆえ step-0 でも定義される)。

### 4.2 CRIT1 解決 — **(b)-hold、metric = cable-state (v0.3 再設計、CRIT-3 fold)**

**v0.2 の EE-deviation metric は撤回。** 理由 (pre-check CRIT-3、substrate 事実): 本 env の arm は毎 frame kinematic re-pose (`:1199-1228`、qd zero) ゆえ ‖achieved−base‖ ≤ ‖Δ′‖+IK 残差 ≈ 25mm が構造上界 — **EE 逸脱は IK 破綻以外で閾値を越えられず、FORK-1 の実体 (EE 追従完璧のまま cable が drift) を検出できない**。EE 基準の (b)-hold は事実上 (a) 無条件 march と同値だった。

**採用 metric (v0.4 で規則を pin、N2/N4): `div_grip(w, t) = ‖cable[s(route_t)] − rec_cable[s(route_t), f(route_t)] − recenter(w)‖ [mm]`**
- **segment 規則 s(route_t) = 記録の `held_seg_l[f(route_t)]`** (L = cable を通し続ける holder 腕; 記録実測で把持 seg は 7→27 (pre-grasp sweep) → 27 → 24 → **連続 slide 24→…→14 (G4 窓、intra-finger pay-through、~33 回の隣接 handover)** → 13 → 14 (release 後) と移動する (t397 grip-loss 時点の held seg = 20; handover 鋸歯 ≤2.84mm n=1) (v0.8 5体-fold M5 精密化) — 固定 seg24 は G5/G6 半区間で ~10 seg ずれるため不採用 [N2])。held_seg_l は全 frame 定義済 (pre-grasp 含む) = metric が全域で定義される。**R 腕は L-only scope と宣言** (R の regrasp 品質は p4/r_reach 述語 + drop 検出が既に測る; 記録に held_seg_r が存在しない [`route_demo_recorder.py:52-61`] ため R 用 ground truth は無い — 正当化込みの設計決定、Rs veto = W0-a)。**R 側の候補 = 記録済み nearest_seg_r (v0.8 5体-fold L6)** — release/regrasp 遷移では nearest≠held のため一次 metric に不採用 (regrasp 品質は p4/r_reach + drop 検出が担当)。R-side div leg の追加是非 = Rs W0-a。
- **比較 frame 規則 f(route_t) = chunk 終端 — f = min(cf[route_t]+9, F−1) (終端 clamp、v0.8 5体-fold L3)** — env state は RL step 後 = 10 frame 駆動後ゆえ終端整合が正 (N4: diag の t·10+3 比較は系統 staleness ≤1.07mm [固定 seg24] / ≤1.31mm [held seg 追従時] (v0.8 L3) — §8 legs は正整合で band 再導出)。
- 検出対象 = FORK-1 の実測発散量 (comp5 div_seg24 系) を全 route 域に一般化したもの。
- **HOLD_THRESH 提案 = 15mm — PROVISIONAL (n=1、provenance を v0.4 で precise 化 [N5]):** 健全域 (f0-336) max 10.56mm / f337 から連続 ramp で 15mm 到達 (f343) — **transit 域に「分離帯」は存在せず、10.6→15 は既に runaway の一部**。任意の閾値 ∈ (10.6, 15] は同一 ramp を ≤6 RL steps 差で検出する — 15mm 選択のコスト = 54-step 猶予のうち ≤6 step (v0.5 単位訂正)。onset→grip-loss 域 (58mm) = **54 RL steps の補正猶予 (v0.5 単位訂正 — v0.4 の 5.4 は 10 倍過小の保守誤り)** (v0.8 5体-fold L4: 58mm 'grip-loss' は簡略 anchor — pad 接触断続の onset は t374/49.5mm [n=1、完全結合窓は onset 後 ~31 step])。**nominal band の別測定は本基板に存在しない (下記基板事実) — 閾値の安全側検証は §8 legs (per-cell/per-seed nomA/nomB) が担う。数値確定 = Rs W0-a。**
- **⚠ 基板事実の宣言 (N1 — 本設計の前提解釈):** comp5 = residual≡0 canonical 構成の実測ゆえ、**HOLD は nominal replay でも t≈343 で発火する — これは偽発火でなく正しい警報** (cable が実際に track を離れている)。未訓練 (Δ≈0) policy の episode は HOLD で stall → timeout 終端 (G1-G3 latched 部分報酬) が**期待される初期訓練挙動**。学習が進むと policy が div_grip を閾値内に維持/回復し march が続く — **HOLD-resume rate = 学習進捗の一次 telemetry** (§5 export; DR 下では leakage 実測 (§8) まで confounded と注記 — v0.8 5体-fold H7)。env は「diverged cable への march 続行 (= grip-loss 直行)」を構造的に拒否する — これが本 env の存在理由であり、FORK-1 の fix = closed-loop 補正 (charter 定義) と整合。
- **HOLD 動作:** div_grip > 閾値 → route_t 凍結 (base target / grip schedule [**chunk 終端値 cf[route_t]+9 で定値 hold — 凍結 chunk の再走は staircase 途中で servo 鋸歯を生む、N3**] / is_dual_grip_window [chunk 終端状態] / obs[50] 全て単一源凍結 = fail-safe)。episode 時計・time-penalty は継続。凍結により march (drift 駆動源) が止まり、σ-cap 下でも補正が勝つ体制へ (§2 D-2)。回復で route_t 再開。
- **arming gate (v0.8 5体-fold H7): HOLD は G1-latch 後にのみ armed** — pre-grasp は policy が cable に因果経路を持たず (grippers open)、DR offset 下で div_grip が定数的に閾値超過すると route_t が t=0 凍結の恒久 dead episode になる (CC4-C2)。pre-grasp の div_grip は telemetry のみ。
- **resume 条件 (v0.8 5体-fold M5) = div_grip ≤ 12mm (閾値 15 − hysteresis 3mm > handover 鋸歯 2.84mm n=1) or K=3 連続 in-band** — 15mm 単一 bar での MARCH/HOLD chatter (limit cycle) を排除。chatter-rate telemetry を §5 に追加。数値 = PROVISIONAL、Rs W0-a。
- **div_grip 非有限 (v0.8 5体-fold L1)** (NaN/Inf: 記録 lookup 破損/recenter NaN/bank 破損) = **閾値超過として扱い HOLD + loud event** (fail-OPEN 防止、NEW-A class; 比較は NaN>x=False で silent MARCH になるため明示分岐必須)。
- **要件 (N9): recording contract v2 = `cable_xyz` (7707,40,3) + `held_seg_l` を必須 key に昇格** (`_prepare_recording :3119-3122` は現在 optional 扱い) — §10 build 行。
- **IK 残差 (obs[55:57]) は informative telemetry のみ** (clock 作用なし — IK 破綻は別系統の異常であり、cable-desync と混ぜない)。
- MAX_HOLD_STEPS = **placeholder 24、PROVISIONAL-UNMEASURED を明示** (pre-check MED-6: 回復時間の実測は存在しない)。§8 hold-fires probe の凍結後回復時系列から導出し直し、確定 = Rs W0-a。超過 = informative event (terminate しない)。
- **p3 (`ph≥2` conjunct `:1502`) × HOLD (MED-11 fold):** seat が HOLD 中に劣化すると ordered-latch が G3 以降を恒久 block する dead-episode class が存在 (timeout 終端で部分報酬 — 訓練 deadlock ではないが零信号 episode)。**「seat は HOLD を跨いで持続する」を falsifiable claim 登録** + G3-stall event telemetry (§5) + §8 bank-G3 fork 摂動 smoke leg。頻発 = curriculum mix / HOLD 閾値の再設計 trigger。
- **tail (記録終端後 ~139 step): HOLD 無効** (route_t 終端到達後は凍結対象なし)。§9 tail 行参照。
- (c) predicate-earned・(a) 無条件 march の不採用理由は v0.2 から不変 (§13 参照)。

### 4.3 API 形状 (v0.2 から: sync_state に div_grip / route_t を追加)

```
query(t_episode, world_id, live_state_view) ->
  (target_6d, phase_id, per_arm_grip_2vec, is_dual_grip_window,
   validity_mask,              # phase 別 state-blind mask (v1.5h §5)
   sync_state)                 # {MARCH|HOLD}, hold_count, div_grip [mm], route_t
```
- mid-servo 返り値 = 補間中間 target、規約 = converter label 同一系 (COMMANDED、`route_demo_to_bc.py:287` 系) — v0.2 不変。
- oracle = 読み取り専用 (副作用は sync_state 更新のみ)。照会実体 = per-step relabel + stored settle re-center + in-scene IK 床 (v1.5h §5)。mask 消費は trainer 側 (env 挙動を変えない)。

## §5. transition export + reward 成分ログ (§6-4/§6-5、v0.3: override 会計 fold)

| group | fields | v0.3 変更 |
|---|---|---|
| core | o, a_raw, a_executed, **r_paid**, o′, done, time_out flag, **termination_reason ∈ {success, timeout, drop, explosion} + invalid_mask (explosion = PPO batch mask、env-core LOUD-CARRY :1554 の discharge) (v0.8 5体-fold M3)** | r → r_paid に改名 (下記) |
| reward 会計 | **r_phase_earned (latch 事実) / r_paid (実支払) / overridden flag** / G fire event は **fired vs pre_latched を区別** | **MED-7 fold: drop/explosion step は `r_paid = −10` が earned を破棄する (`:1530-1533`) — 成分和 ≡ r_paid は override 步で成立しない。再構成一致 leg (§8) は「¬overridden 步: 成分和 ≡ r_paid」+「overridden 步: r_paid = TERM_PENALTY ∧ earned 記録保全」の 2 述語に分割** |
| projection | mode, operator basis (or a_executed) | 不変 (NEW-C 承継) |
| telemetry | ‖Δ‖/bound 飽和比 (§2) / HOLD {発火, hold_count, div_grip, **resume event (§4.2 resume-rate telemetry の一次 field、ISSUE-C)**, **chatter-rate (§4.2 resume 条件、v0.8 5体-fold M5)**} / **G3-stall event** (§4.2) / guard fires / seat sustain / **pin event (C1 pin 活性化 frame/route_t/world — charter §3-A 'phase/seat/pin events' の pin 項、c1pin diff の disposition に従い wire) (v0.8 5体-fold M4)** / **suppressed-drop event (tail (iv) で無効化された post-release drop の記録 — /metrics/drop_count の cross-version 比較歪み防止) (v0.8 5体-fold L2)** | v0.3: HOLD 系 + G3-stall 追加 |
| provenance | world_id, seed, DR (dx,dy), start_phase k, **route_t**, env sha, nomA/nomB stream id | route_t 追加 (MED-9) |

- 形式: per-episode npz shard + JSON manifest。episode 終端 flush。既定 ON。fps 影響 = §8 実測。
- **build DoD (v0.8 5体-fold M3): time_out flag ⇔ episode_length==900 (terminal 混入ゼロ) の grep + unit leg (§6-12 純度の明示 discharge)。**
- **export disk budget (v0.8 5体-fold L2): ~0.5MB/episode × 81 worlds 級 — rotation/retention 方針 = build 時 pin (一行)。**

## §6. DR hooks + curriculum-reset (§6-6 + ⑦(b)、v0.3 全面改稿)

### 6.1 CABLE_XY_OFFSET per-world wiring (v0.2 から微修正)

- env config 経由 per-world 配列 (os.environ 経路は multi-world 不可)。適用点 = `_reset_worlds` cable 初期配置 (`:727` 平行移動)。sampling = {OFF (既定) / grid / uniform ±20mm} — ON は Rs W0-a。
- oracle 整合 = per-world stored settle re-center (recenter = **to-be-built** (v0.8 5体-fold M1: 現 code に recenter 実装は無い [grep 0 hits] — 最近縁 = producer の GRASP_YC/x_grasp (route_executor.py:1127/:1482/:1529、grasp 域 one-shot common-mode)。これを per-world env-level に一般化して新設、§10 cost 行 +50-150))。**dy=+10→+2.5mm の減衰実測は 1 点 — ±20mm への外挿は未検証と明示し、§8 DR-corner leg で実測** (MED-12)。
- provenance = §5 export + meta per-world 化。

### 6.2 curriculum-reset (phase-k fork) — **bank 実能力の honest 再設計 (CRIT-1/HIGH-5 fold)**

**既存部品の実能力 (§0 訂正済):** bank = arm/gripper qpos (+qd=zeros) のみ。cable 状態なし。`reset_to_phase(k≥1)` は raise (code 自身が「mismatched state」を disclaim)。**v0.2 の「接続+会計 flag 中心」見積は撤回。**

**Stage-A 設計 (build 項に昇格):**
1. **bank v2 = cable 込み fork state:** phase 境界 frame の **cable joint-space q/qd (v0.7 C2) + arm/gripper q/qd** を capture → bank v2 生成。**capture 基板 = producer 経路 — env feedforward replay は t≈498 で死ぬため k≥4 境界に到達できない (N1c)。実装先 pin (v0.7 C3 + %9 C-3): **committed 抽出 twin `route_executor.run_route` (byte-repro 81/81 実証 `50f877c7f5`) に pin** — Rs-LOCKED file への新規計測 edit (rule-10 再演) を回避 + unbanked producer diff (+2036/-812、Rs 裁定待ち) から provenance を分離。monkeypatch harness は locked 内部 hook が必須と判明した場合のみの fallback (その際は locked edit + Rs surface)**。cross-builder transplant (producer state → env build) の妥当性 = restore-fidelity DoD が担う ((a1) 確定により両 builder は同等 — 差は ~0.15mm settle 微差で、DoD band が包含)。**capture frame は RL-step (chunk) 境界に整列** (bank_boundary を次 chunk 境界へ切上げ — grip staircase との ≤9 frame 不整合を排除、N8)。**runtime restore = restore-exact (bank には post-settle 状態を格納、settle 検証は bank build 時の一回のみ — per-fork runtime settle は全 world 一斉 step で他 world を汚染するため禁止、N8)**。**restore fidelity DoD: qpos/qvel L∞ ≤ 1mm / 1mm/s ∧ restore 直後 div_grip ≤ 健全域 band (§8 正整合再計測で確定; 現行推定 10.4-10.6mm [f+3 旧整合 10.56 / f+9 正整合 held-seg 10.41 n=1]) — 再計測値が governs (v0.8 5体-fold L7)** — fork 起点が HOLD を即発火させない構造保証。**capture artifact の pin (ISSUE-B + v0.7 C2): 既存 route_demo_raw.npz は速度を持たない → bank capture = 専用 producer-side dump を新規定義。cable 表現 = JOINT 空間 q/qd (mujoco restore は joint-space が正 — body_q は派生量で単独 assign は上書きされる、seed_cable_joint_state docstring 根拠) + arm/gripper q/qd + chunk 整列 frame index + provenance sha。restore は qd を zero しない変異体 (mid-route 境界の cable は運動中 — apply_banked_restore の qd=zeros 系は P0 用)** — §10 bank v2 行に含む。
2. **per-world fork:** interface v2 `reset_to_phase(k, world_ids)` (§4.1) + bank slice (`apply_banked_restore :334-340` の全 world tile 書込を world-slice 化)。
3. **cable restore の所在 = env-level (v0.7 C5、%12 RULING 07-07 17:13 / routeexec node state.md:8 再掲 — route_executor は capture/供給、適用は env `_reset_worlds` 系)。cable restore 機構 (v0.8 5体-fold M10、⑦(b) RULING 遵守): env-level `seed_cable_joint_state` (per-world offset-aware) — route_executor 側 joint-index 直書きは world≥1 誤配置の documented bug (routeexec state ②)。restore-exact の write-set に body_q_prev (solver double-buffer :997) + Dahl friction state (:1061) を含める (or 明示 reset とその正当化) — qpos/qvel L∞ DoD はこれら hidden state に盲目のため、1-step post-restore 動力学 leg (t=bank+1 の state を producer の同 frame と比較) を fidelity DoD に追加。drop-arming 整合 (CRIT-1 帰結):** cable re-seed により phase-k 復元直後の held_z は記録値近傍 → G1/G2 pre-latch と drop 述語 (`:1481-1488`) が矛盾しない。**positive-control smoke leg = §8 の per-k 差別化 bar に従う (v0.8 H1 整合: k=1,2 は G_{k+1} 到達 / k=3-5 は restore fidelity + HOLD 正発火 + no-drop-under-HOLD)**。
4. **会計 (HIGH-5 fold): 機構 = bank-only に一本化。** v0.2 の prefix pins ①③ (scripted-prefix 除外 / prefix-fail resample) は instantaneous restore に対し無対象 = **削除**。残置 pin = 「episode 時計・time-penalty・horizon は handover 起点」のみ。export `start_phase` field が全会計を担う。
5. **⚠ DR × curriculum の相互排他 (HIGH-5、LOUD 宣言):** bank v2 は canonical x0_y0 単一 cell 由来 → **phase-k 開始は DR 被覆ゼロ (offset 固定)。DR は P0 開始でのみ全域**。campaign 帰結 (phase 条件付き能力が DR-free で訓練される confound) を §9 行 + campaign 設計への carry として明示。緩和 option (採否 = Rs W0-a): P3 batch に multi-cell bank capture を piggyback (+1 行 §10 cost)。
6. earned-without-bonus pre-latch は ordered-loop (`:1508-1518`) と両立 (pre-check verified-OK #8) — 二重取得経路なし。
7. 開始 mix 集合 {P0, G1−ε..G5−ε} 提案、比率 = Rs W0-a。**評価 bar = from-P0 のみ** (不変)。

## §7. OG port + composite (§4.3-a/b/c、v0.3 全面再設計 — MED-8 fold)

- **no-sim 契約の保全:** OG は「policy forward + decode のみ、solver/mujoco/newton import 禁止」(`og_offline_gate.py:7-13`)。**composite の base 供給 = 事前計算済み記録 target 列** (in-scene IK を OG 内に持ち込まない)。**帰結 = OG の適用 scope は nominal cell canary に限定** (nominal では stored recenter ≈ identity → deployed 経路と parity 成立; DR cell では recorded base ≠ live recentered base → parity 不成立を明示、DR 挙動の計器は §8 smoke / in-sim eval 側)。
- **旧 v0.2 の「leg①③ は composite で再定義可」は撤回:** anchored residual では on-path ∂(base+Δ)/∂obs = ∂Δ/∂obs ≈ 0 → γ⊥/γ∥ とも縮退 (leg② を殺すのと同一機構が leg①③ も殺す — 縮退の全数照合、pre-check MED-8)。
- **再設計 legs (residual head 用、bars = Rs W0-a):**
  - **leg-A′ anchor 適合:** on-path ‖Δ(obs_demo)‖ 分布 (p95/max)。健全な residual は canonical 経路上 Δ≈0 — **on-path ‖Δ‖ の経時増大 = drift/忘却警報** (OG-a の decode 忠実度の residual 版として意味が立つ)。
  - **leg-B′ 復元感度:** corner/off-path 状態 (B1+budget-test rollouts を 62D 再変換した fail-set、devplan §4.3 承継) で cable-obs dims を摂動 → ‖∂Δ/∂(cable obs)‖ 方向 gain。**Δ が cable 状態に応答する能力** = 縮退しない復元計器 (v0.2 の leg② 代替案を全 leg に一般化)。
  - **leg-C′ null-beat:** replicate-null に対する margin (機構不変 `:39`)。
- **og_gate.json に schema_version field (v0.8 5体-fold M11)。** 現 schema 消費者の disposition: dagger_loop.py:203-208 (γ⊥ regression baseline 読み) = B2/27D lane 専用として retire-or-migrate 判断を R3 build 時に / perrow_nullbeat.py = 同。**leg-C′ precondition = 62D/α-6D 契約下で 13x-replicate null artifact を再生成** (旧 null との比較は schema 非互換)。
- 「2× validated」主張の RESET (port+再検証まで新契約に主張しない) — 不変。band 再較正 = Rs W0-a、完了まで OG を R2b abort 条項に使わない — 不変。

## §8. throughput + parity + 検証 smoke 計画 (§6-8、v0.3: +4 legs)

| leg | bar | v0.3 |
|---|---|---|
| throughput (oracle+export ON) | 実効 ≥9.7 fps | 不変 |
| device-parity (cuda:2 vs cuda:0) | predicate-fire + 終端 verdict 一致; FAIL 分岐 = cuda:0 pin | 不変 |
| HOLD 込み horizon 再検証 (v0.7 %9 C-2 re-scope) | (a) 設計算術 leg: 771 + MAX_HOLD 予算 × 想定 hold 回数 ≤ 900 の再導出 (paper) (b) p99 実測は **trained-policy 前提 = campaign 時測定に defer** — residual≡0 基板では N1 により全 episode timeout@900 が期待値で、p99 bar は測定不能 (S3 系 scenario は学習後にのみ実現) | **re-scope** |
| **hold-quiet-pre-onset (v0.4 reframe、N1)** | residual≡0 replay の**健全域 (t<340 相当)** で HOLD 発火 0 — 全 route quiet は本基板に存在しない (N1) ため健全域 leg のみ。**v0.7 C1: 旧「no-C2 scene 全 route quiet leg」は削除** — no-C2 も byte-identical に発散する (`dd7c97d480`、%11 実測) ため当該 leg は必ず FAIL し偽発火と誤読される | **reframe** |
| **hold-fires-at-onset 較正 (v0.4 reframe、N1)** | residual≡0 replay (canonical、C2 scene) で HOLD が f343±1 chunk で発火 = 警報較正そのもの + **凍結後 div 時系列で drift-under-HOLD < drift-with-march (mean 0.58mm/RL-step) を実測 (§2 falsifiable ①、v0.6 bar 整合) + 回復時間分布 → MAX_HOLD 導出 + EE→cable displacement gain 実測 (凍結中に bounded Δ 注入 → d(div)/d(EE)) (v0.8 5体-fold M2)** | **reframe (正制御が nominal replay で直接実行可能に)** |
| **bank-start 正制御 (CRIT-1、v0.8 5体-fold H1 per-k 差別化)** | **k=1,2 (dual-grip 域):** drop なし + G_{k+1} 到達 + restore 後 div_grip ≤ band / **k=3..5 (transit 跨ぎ):** restore fidelity PASS + HOLD が onset で正しく発火 + HOLD 下で drop なし — **G_{k+1} 到達は要求しない** (N1 基板事実により Δ≡0 では到達不能が期待値) | **v0.8 H1** |
| **bank-G3 fork 摂動 leg (v0.4 追加、#11 partial 解消)** | G3−ε fork + cable 摂動注入 → HOLD 中の seat 述語持続を実測 (falsifiable claim ② の実行 leg) + G3-stall 頻度 | **追加** |
| **DR-corner leg (新、MED-12)** | ±20mm corner cells を oracle 経路で grasp+G1 到達 + **drift-rate 再計測 (§2 bar: alert >10 / breach >20 mm/RL-step、v0.6 整合)** + **reset 時 + per-phase div_grip profile per DR cell (bar = 健全域 band ≤~10.6mm; これが recenter 漏れの falsifier — 正しい DR 経路自体が非零 div を持つ構造 [clip 不動] のため) (v0.8 5体-fold H7)** | **追加** |
| **IK 残差分布 probe (新、MED-6)** | canonical replay + full-authority Δ 注入時の per-step IK 残差分布 (informative telemetry の較正) | **追加 (0-GPU 級)** |
| state-bank restore fidelity | qpos/qvel L∞ ≤ 1mm / 1mm/s + div_grip ≤ 健全域 band (§6.2 v0.8 5体-fold L7 定義 — 再計測値が governs) | §6.2 DoD に統合 |
| export 完全性 | ¬overridden: 成分和 ≡ r_paid / overridden: r_paid=−10 ∧ earned 保全 (2 述語) | **MED-7 修正** |
| route-clock 単一源 | route 系消費者の episode_length_buf 参照 = 0 (grep leg) | **追加 (§4.1)** |
| **flag-OFF byte-preserve (v0.7 C4)** | Stage-A 全 flag OFF で env 挙動 byte-preserve (comp3/comp5 で確立した invariant の regression leg) + **具体 legs (v0.8 5体-fold H5): gate-iii 25/81 flag-OFF byte-identity (pinned baseline sha) / ⑨a′ per-cell EXACT 81/81 再実行 / DoD⑤ Δ=const drift-zero 0.0 EXACT + DoD⑥ predicate unit-test + DoD⑩ span-projection 0.0mm の再 run (clock 付替え後) / route_executor.py diff 毎の byte-repro ref-subset 再実行 (test_routeexec_byte_repro.py)** | **追加 (%11 cross-PV)** |
| **cg-GPU whole-route screen (devplan §6 gates 注記) (v0.8 5体-fold H3)** | device-parity leg に同梱 (全 phase finite + nacon engage) | **追加** |

## §9. 決定 disposition 表 (v0.3 更新)

| 決定項 | 本 gate での扱い | 最終決定 |
|---|---|---|
| α-PC 再同期規約 | **(b)-hold 採用、metric = cable-state div_grip** (§4.2、EE 基準は substrate 事実で撤回) | Rs veto = W0-a |
| HOLD_THRESH | **15mm (実測 pin、n=1 provenance 明示 + §8 再検証 leg)** | **Rs W0-a (数値確定)** |
| MAX_HOLD_STEPS | placeholder 24 = **PROVISIONAL-UNMEASURED** (§8 で導出し直し) | **Rs W0-a** |
| Δ-bound | pin 0.020 + D-2 subspace 分解 (§2) | Rs veto = W0-a |
| σ-cap contingency | 2 段 bar (v0.6 注記): 機構 bar = claim ① (drift-under-HOLD ≥ 0.58mm/RL-step で HOLD 機構解釈見直し) / 容量 bar = drift-under-HOLD ≥ 2mm/RL-step (σ-cap 容量超過) で σ-cap 再導出を W0-a に上程 | **条件付き Rs 項** |
| OG legs A′/B′/C′ + nominal-cell scope | 採用提案 (§7) | Rs veto = W0-a |
| OG band α/β/γ 数値 | 提案せず | **Rs W0-a (OPEN)** |
| DR 既定 ON + range | OFF 既定、wiring 設計のみ | **Rs W0-a (OPEN)** |
| **DR-corner div 漏れ contingency (v0.8 5体-fold H7)** | per-region recenter or DR-scaled HOLD_THRESH (leg 実測で発動判断) | **Rs W0-a** |
| **DR × curriculum 相互排他** | **LOUD 宣言 (§6.2-5) + 緩和 option (multi-cell bank) 提示** | **Rs W0-a (option 採否)** |
| **tail semantics (~139 step)** | **4 checks を build DoD 化 (v0.4 で (iv) 追加、N6): (i) seated 枝: drop held-z 非発火確認 (seated z 0.829 > rest+10mm) (ii) G6 sustain の release 境界跨ぎ連続性 (iii) HOLD 無効化 (iv) 非 seated 枝: 予定 release (route_t ≥ release 境界) 後は drop terminal を無効化** — 意図的 release 後の「drop」は category error であり、放置すると fail-slow (−7.6) < fail-fast (−3.99) の逆転 incentive (粘るほど損 = 早期放棄の誘因) を作る。無効化後は timeout close (+1.00 系) で S4 系 scenario が復元される (Artifact 3 v3 反映) | 本 gate (Rs veto = W0-a) |
| α-DR option (a)-(d) / draw / Q7 / HIGH4 / 開始 mix 比率 | 触れない (v1.5h 不変) | **Rs W0-a + P3** |

## §10. cost / LOC (v0.3 再見積)

| item | est LOC | v0.3 変更 |
|---|---|---|
| oracle query wrapper + **per-world route_t 付替え 4 系統** (§4) | 400-700 | +100-200 (CRIT-2) |
| **bank v2 (cable capture + restore + fidelity DoD)** (§6.2) | **150-300 (新規行)** | CRIT-1 昇格 |
| transition export + 会計 (§5) | 150-300 | 不変 |
| DR wiring + curriculum 統合 (§6) | 100-250 | prefix 機構削除で微減 |
| OG port + legs A′B′C′ (§7) | 250-450 | 再設計で微増 |
| **per-world recenter 新設 (§6.1、v0.8 M1)** | **50-150 (新規行、cycle-2 fix-1)** | GRASP_YC/x_grasp 系譜の env-level 一般化 |
| smoke 一式 (§8、+5 legs) | 150-350 | +50-100 |
| **recording contract v2 (cable_xyz + held_seg_l 必須化 + shape/frames 検証)** (§4.2 要件) | **50-100 (新規行、N9)** | v0.4 追加 |
| **計** | **~1.35-2.55k** | staged ≤800 行/diff の個別 L3 chain 分割 (不変) |

- **build hygiene (v0.8 5体-fold M12): 全 build chunk = explicit-path commit + single-file lint のみ (tree-wide ./isaaclab.sh -f 禁止 — 共有 dirty tree での2度の実績事故 [envcore --all-files / routeexec pB tree-wide -f]、feedback-no-tree-wide-precommit-f rule)。**

## §11. conservatism + carried risks (v0.3 追記)

- v1.5h §8 carry 全数継続。
- **n=1 provenance:** HOLD 閾値 15mm / 健全域 band 10.56mm / transit rate mean 0.577mm/RL-step は residual≡0 canonical 構成 run 1 本 (canonical cell) の実測 — §8 legs が拡張するまで n=1 と常時明記。**transit 域の nominal band は本基板に定義不能 (nominal 自体が発散する、N1) — 閾値の偽発火安全性は健全域 (f0-336) に対してのみ主張。**
- **substrate 明示:** arm は kinematic re-pose (EE 追従は構造的に完璧) → 本 env の desync は cable 側にのみ現れる。HOLD が cable-metric なのはこの substrate 事実の帰結であり、実機 (EE 追従誤差が実在) への転移では EE 系 guard の再設計が必要 (非保守方向として明記)。
- HOLD 機構自体が sim 固有 (実機 base controller に同等物要) — v0.2 から不変。
- bank 量子化 = DR 被覆の下限側 (保守) だが §6.2-5 の相互排他は campaign confound (非保守) — 両面明記。
- P4 honest limit 不変: 本 spec は「RLPD が補正を学べる」を主張しない。

## §12. gates / next

1. (完了) /pre-check 4 往復収束 (v0.6) + %9/%11 cross-PV fold (v0.7) + 5体 [VERIFY] cycle-1 fold (v0.8)。次 = targeted re-verify (cycle 2) → PASS 判定。(v0.8 5体-fold M8)
2. 5体 [VERIFY] → %9 9-lens cross-PV + %10/%11 audit → 層5 → [RULE-CHECK] → explicit-path bank → p6 cascade。
3. **bank 時に v1.5h §termination 行 (line 74) へ supersession pointer を stamp: 「tail 非 seated 枝は STAGEA spec §9-(iv) が supersede (Rs veto = W0-a)」(v1.5d precedent の in-place annotation 方式) (v0.8 5体-fold M6)。**
4. build 着手 = 本 gate PASS + D-B trigger。campaign = HIGH-COST + production-launch + fresh Rs GO (不変)。**build hygiene = §10 M12 行 (explicit-path commit + single-file lint のみ、tree-wide -f 禁止) (v0.8 5体-fold M12)。**

## §13. /pre-check disposition 全数表

### §13.1 — 1走目 (BLOCK → v0.3 fold)

| # | SEV | 要旨 | disposition |
|---|---|---|---|
| 1 | CRIT | bank に cable 状態なし・qd=zeros — spec grounding 虚偽 | **FOLD**: §0 訂正 + §6.2 bank v2 build 昇格 + 正制御 leg |
| 2 | CRIT | route-clock remap / per-world fork 未設計 | **FOLD**: §4.1 route_t + interface v2 + step-0 semantics |
| 3 | CRIT | EE-deviation HOLD は substrate 上発火不能 = (a) と同値 | **FOLD**: §4.2 cable-metric 再設計 + 実測閾値 + 正制御 leg |
| 4 | HIGH | Δ-bound が σ-cap/dual subspace を覆わない | **FOLD**: §2 D-2 実測分解 + falsifiable claim + contingency 行 |
| 5 | HIGH | prefix pins 無対象 + DR×curriculum 相互排他 | **FOLD**: §6.2 bank-only 一本化 + LOUD 宣言 + 緩和 option |
| 6 | MED | 30mm margin 根拠薄 + MAX_HOLD 捏造根拠 | **FOLD**: metric 変更で 30mm 廃止; MAX_HOLD = PROVISIONAL 明示 + §8 導出 leg |
| 7 | MED | 成分和 ≡ reward が override 步で不成立 | **FOLD**: §5 r_paid/earned/overridden 分離 + §8 2 述語化 |
| 8 | MED | OG no-sim 契約違反 + leg①③ 縮退 | **FOLD**: §7 全面再設計 (nominal scope + A′B′C′) |
| 9 | MED | 時計消費者 4 系統 + obs[50] 不整合 | **FOLD**: §4.1 単一源 + grep leg |
| 10 | MED | tail ~139 step silent drop | **FOLD**: §1/§9 行 + 3 checks |
| 11 | MED | p3 live-seat × HOLD の恒久 stall class | **FOLD**: §4.2 falsifiable + G3-stall telemetry + smoke leg |
| 12 | MED | DR 到達性の 1 点外挿 + 82.4% mechanism 不転送 | **FOLD**: §0 降格 + §6.1 明示 + §8 DR-corner leg |

### §13.2 — 2走目 (BLOCK: fold 9/12 実 + 3 partial、新規 9 → v0.4 fold)

| # | SEV | 要旨 | disposition |
|---|---|---|---|
| N1 | CRIT | comp5 = residual≡0 canonical 構成 — nominal-quiet 前提が自己矛盾、bank k≥4 capture 不能、FORK-1 依存未宣言 | **FOLD**: §0 基板事実行 + §4.2 警報再解釈 (HOLD@nominal = 正、stall = 期待初期挙動、resume-rate telemetry) + §8 quiet/fires legs reframe + §6.2 capture = producer 経路。FORK-1 は precondition でなく本 node の解決対象 (charter 定義) と明記 |
| N2 | HIGH | div_grip の「把持 seg」が route 全域で不定 (27→24→14→13 移動、held_seg_r 不在) | **FOLD**: §4.2 metric 規則 pin (s = held_seg_l[f(route_t)]、全 frame 定義、L-only scope 宣言 + 正当化) |
| N3 | MED | HOLD 凍結 chunk 再走 = grip staircase 途中で servo 鋸歯 | **FOLD**: §4.2 grip = chunk 終端値 定値 hold |
| N4 | MED | diag 比較 frame が 6-frame stale (~1.07mm 系統誤差) + div_grip 比較 frame 未 pin | **FOLD**: §4.2 f(route_t) = chunk 終端 pin + §8 正整合再計測 |
| N5 | MED | band 10.6 の scope 誤表記 (真の pre-onset max 14.84) / 100% 単調は 98.7% / mean は \|inc\| | **FOLD**: §0/§4.2 precise 再表記 (分離帯は存在しない — 閾値正当化を ramp 検出遅延 ≤6 frame 論法に差替え) |
| N6 | MED | tail 強制 release → 非 seated 枝で drop −10 = S4 到達不能 + fail-slow<fail-fast 逆転 | **FOLD**: §9 tail (iv) release 後 drop 無効化 + Artifact 3 v3 |
| N7 | LOW | §2 chain が P4 1.86 のまま (comp5 実測 1.94) | **FOLD**: §2 更新 (必要 19.4、margin 0.6mm、W0-a 引上げ条項) |
| N8 | MED | restore-then-settle 曖昧 + capture frame cadence 不整合 | **FOLD**: §6.2 restore-exact + chunk 境界整列 |
| N9 | LOW | recording contract 拡張が cost 表に不在 | **FOLD**: §10 新規行 + §4.2 要件 |

partial 3 件の解消: #3 → N1/N2/N4/N5 fold で完結 / #10 → N6 fold で完結 / #11 → §8 bank-G3 摂動 leg 追加で完結。

### §13.3 — 3走目/4走目 + 5体 cycle-1 (要約、v0.8 5体-fold M8)

3走目 = BLOCK-narrow (ISSUE-A 単位系 → v0.5) / 4走目 = WARN 条件付き PASS (stale 7 行 → v0.6) / %11+%9 cross-PV = CONCUR-w-CORRECTIONS (→v0.7) / 5体 cycle-1 = FAIL (HIGH 7 ACCEPT → 本 v0.8; CRITICAL 0; NHA = CHANGE_JUSTIFIED)。
bank-start 正制御の per-k 差別化 (§8 H1) は comp3b NULL-analysis (re-seed は phase-3 INTRA drift を直せない) と整合 — bank fork は『開始状態供給』であり drift fix ではない、fix = 閉ループ policy (per charter §6 comp3b-retirement)。(v0.8 5体-fold H1)

*%12 — 2026-07-12。PAPER-ONLY。INVARIANTS 不触 (DUAL-ARM / 88mm span / DiffIK-only / gripper LOCK / no-kinematic-trick)。task_config.py 不触。*
