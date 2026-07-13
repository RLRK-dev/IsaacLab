# Stage-A: P2 env trainer-grade 拡張 — DESIGN-GATE SPEC (W0-c delta)

**Author:** RS-TECH-LEAD (%12/w2:p4)。**Date:** 2026-07-12 10:36 JST 初稿。**Node:** `T-ROOT-optE-route-dapg-C1C2-P2-trainer-stageA`。
**Status:** v0.8.1 (banked + W0-a 承認済み; v0.8.1 = p1 packet 検分 M-2 の 1-line 追記 [claim ③ 正式登録] のみ)。⚠C6: §0 の cablediag 生成元 (comp5 runner _DIAG 拡張 +122/-4) は %11 の uncommitted tree — spec 最終 bank と同時に commit or sha pin (bank 手順に含む)。PAPER-ONLY / 0-build / 0-GPU (probe は既存 npz の CPU 解析のみ)。campaign は HIGH-COST + production-launch-gate + fresh Rs GO 背後で不変。
**改版:** v0.1 10:36 初稿 → v0.2 10:4x (/reward-design PASS-with-2-folds) → v0.3 11:0x (/pre-check 1走目 = BLOCK 12 issues 全 fold — §13.1。主変更: cable-metric HOLD / bank v2 昇格 / per-world route-clock / OG legs 再設計) → **v0.4 11:3x (/pre-check 2走目 = BLOCK [fold 9/12 実 + 3 partial、新規 9: N1 CRIT / N2 HIGH / 5 MED / 2 LOW] 全 fold — §13.2。主変更: 基板事実の再解釈 [N1: comp5 = residual≡0 canonical 構成 → nominal-quiet band は本基板に存在せず、HOLD@t≈343 は正しい警報 — FORK-1 実体そのもの] / div_grip segment 規則 pin [N2: held_seg_l 追従] / tail 強制 release 後 drop 無効化 [N6] / bank capture = producer 経路 [N1c] / 実測値の precise 再表記 [N5/N7])** → **v0.5 11:5x (/pre-check 3走目 = BLOCK-narrow [9 N-fold 全 VERIFIED + partial 3 CLOSED; 残 ISSUE-A HIGH 単位系 + B/C LOW] 全 fold: 全 diag 由来 rate を mm/RL-step に訂正 [charter §7 ERRATUM 連動] / D-2「構造的敗北」撤回 / claim ① 再導出 / DR-corner bar 差替え / bank capture artifact pin / resume telemetry field)** → **v0.6 12:0x (4走目 = WARN 条件付き PASS — stale 行 7 箇所の機械整合 [R1-R4 + artifacts 3 行]、verifier「diff 自己確認で足りる、再 pass 不要」)** → **v0.7 12:1x (%11 cross-PV = CONCUR-with-CORRECTIONS 6 件 fold: ⭐C1 no-C2 quiet 誤読撤回 [dd7c97d480 = byte-identical 発散、quiet は producer 経路のみ] / C2 bank = cable joint-space q/qd + qd 非 zero restore / C3 capture 実装先 = 抽出 twin or monkeypatch [locked 不触] / C4 flag-OFF byte-preserve leg / C5 env-level restore 再掲 / C6 uncommitted cite の bank 時 pin。artifact = STAGEA_CROSSPV_COORD_20260712.md fb9000b476)** → **v0.8 12:4x (5体 [VERIFY] DECIDE=FAIL cycle-1 → 27 項 fold [HIGH 7 / MED 13 / LOW 7]、§13.3 disposition)**。
**Authority chain:** trainer charter `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md` §3-A → devplan `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md` §6/§5-R2/§4.3 → 基底 spec = `P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md` v1.5h (**banked basis** — 本 doc は v1.5h を変更せず、その上の trainer-grade **delta のみ**)。
**決定権:** 数値閾値・OG band・DR 既定 ON = Rs W0-a (OPEN 維持)。設計意味論 = Rs autonomy grant (07-12 08:xx) 下の p4⇄p1 co-decide、**Rs veto point = W0-a review**。

**用語定義 (なんでも明瞭に):** oracle-query-API = 実行時に「script はこの状態で何をするか」を返す照会窓口 / Δ (residual) = policy が出す per-step 非累積補正 offset / OG (offline gate) = GPU 不要の忘却警報計器 / DR = 環境条件の意図的ばらつき / decimation = RL 1 step あたり物理 frame 数 (=10) / state-bank = phase 途中状態の保存・復元機構 / CRIT1 = 「policy 逸脱時に phase 時計を誰が進めるか」問題 / div_seg24 = 把持 cable segment の記録軌道からの乖離距離 [mm] / route_t = route 進行時計 (episode 時計と分離、§4.1) / **F-1a = W0-e seat-guide の C2-X 補償 clamp ±22mm (W0E_5TAI_DECIDE_20260705.md:23 — 累積・単軸・locked-runner 内部機構) (v0.8 5体-fold H2)**。

---

## §0. Grounding (アンカー + code 実体、全て on-disk 確認 2026-07-12 10:2x-11:0x)

| Anchor | Cite | 使用 fact |
|---|---|---|
| Stage-A DoD 列挙 | charter §3 Stage-A row | 設計対象 8 項の正典列挙 |
| P4 Δ-bound discharge | charter §7 **+ ERRATUM 2026-07-12 (単位) + %9 再検証 script v3 sha b55bc43d07 (supersedes a2ad75955d → fdcacf98; ERRATUM-2/-3 fold 済 [窓明示 + F1A_PRECEDENT_SCALE_MM 改名]; margin 10.78×、FEASIBLE 不変。経験的一致: 58mm 交差 frame == pad-drop frame == f397 → [0..397] 窓 = gripped 補正 regime そのもの)** | per-step drift \|inc\| mean 0.27 / p95 1.08 / max 1.86 — **単位は mm/RL-step (charter 原文の mm/frame は mislabel、ISSUE-A)**; 結論方向は不変 (保守側誤り) |
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
| **grounding 基準 tree (v0.8 5体-fold H4)** | git HEAD `fb9000b476` + dirty deltas: newton_route_env.py +23L (route_c1_pin、gated-OFF、FORK-1 fix 仮説 = REFUTED disposition-pending) / route_executor.py +70L (同 arc) / og_offline_gate.py (format-only)。⟦13:1x 更新⟧ cablediag 生成元 (_DIAG 拡張 +122/-4) + 一次 npz + c1pin/sub10 evidence = **banked 311f18cb9b** (%11 が runner owner として bank、authorship = 当方 FORK-1 arc、C6 解消) — envs/ の c1pin code diff (+23/+70) は残 dirty で disposition (bank or revert) = build 前提条件のまま有効 | spec の行番号 cite は dirty tree 基準。c1pin diff の disposition (bank or revert) = build 前提条件: revert なら consumer ③ は ff replay のみに縮退 / keep なら per-world 化 (route_steps[0] 単一 world 読み + global _c1_pin_done latch + mjm.eq_data 共有 = multi-world 汚染 3 点) の再設計が必須 |

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
- **HOLD 可観測性 disposition (v0.8.1 追記、5体 CC2-E / p1 M-2): 62D obs 契約は不変 (HOLD flag/div_grip を obs に追加しない)。policy の mode-blindness は falsifiable claim ③「policy は HOLD 状態を直接観測せずとも脱出を学べる (div 補正は mode 認知と独立に最適)」として登録 — ⚠discharge は §8 smoke でなく Stage-C 訓練時の HOLD-resume rate telemetry (訓練前に測定不能な唯一の claim)。反証時 contingency = obs 追加 (62D→63D+、demo 0-fill 規約 §3 準拠) を Rs へ提案。**
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

---

## §14. ERRATUM (2026-07-13 22:1x、%12 — B3 [CHECK] 実測由来、records-must-match-fact)

本 spec は v0.8.1 で banked + Rs W0-a 承認済み。以下 2 件は **設計判断・数値の変更ではなく、記述の事実訂正** (B3 builder [CHECK] の on-disk 実測 + %12 独立検証)。**Rs 承認事項 (HOLD 15/12/24 / Δ-bound 0.020 / DR±20 OFF / mix 集合) は一切不変。**

### ERRATUM-A (§0 anchor 行 N4 / §4.2 比較 frame — 本 spec の規則を CONFIRM、artifact の根本原因を pin)

`comp5_c2seat_fullfire.py:162,213` の diag 比較 frame `10t+3` の由来 = **定数の誤同定**: `_cad, _nsub = 10, int(nre.RL_SIM_SUBSTEPS)` → `_recf = t*_cad + (_nsub − 1)`。`RL_SIM_SUBSTEPS = 4` (`newton_skill_env_base.py:95` = **solver 内 substep 数**) は `PHYSICS_STEPS_PER_RL = 10` (`newton_route_env.py:407` = **RL step あたり physics frame 数 = chunk cadence**) と別物であり、`_nsub−1 = 3` は chunk 終端 index (= `_cad−1 = 9`) の誤用。

⇒ **本 spec §4.2 の `f(route_t) = cf[t]+9` (chunk 終端) が正であることの独立確認**。diag の 10t+3 = 6-frame stale artifact (§0 の「系統 staleness ≤1.07/1.31mm」記述は結果として正、機構がこれで確定)。B2 leg8 の aligned max 10.407mm < shadow max 10.558mm もこの 6-frame stale で説明される。**設計変更ゼロ (規則は既に正しかった)。**

### ERRATUM-B (§6.2-3 M10 の hidden-state write-set clause = **本基板では VACUOUS**)

M10 は restore-exact の write-set に **`body_q_prev` (solver double-buffer) + Dahl friction state** を含めることを要求していたが、**この 2 つは env7 (Newton 1.2.1 / SolverMuJoCo) 基板に存在しない**:
- installed `newton/solvers/` grep = `body_q_prev` / `joint_C_fric` / `enable_dahl_friction` **0 hit** (Newton 1.2.1)。
- THREAD 側で set しているのは **VBD 専用経路のみ** (`generate_demos_mppi.py:508,604` = `solver_vbd`) + test mock。route env の solver = `SolverMuJoCo` (`newton_skill_env_base.py:1322/1332`)。
- 帰結: `newton_route_env.py:1015` の `prev` = **None**、`:1086` の `reset_dahl_friction_for_envs` = **no-op** (両方 `hasattr` guard)。
- 原因 = env6-VBD 期の hidden state を基板検証せず本 spec に carry した %12 の誤り (prohibited.md「PhysX/Newton 環境規約の混同禁止」の同型 = **VBD 規約を mujoco 基板に適用**)。

⇒ **B3 は body_q_prev / Dahl の capture・restore・reset を実装しない (非項目)。** ただし **hidden-state の懸念クラス自体は消えない** — 本基板の hidden state = **MuJoCo `mjData` 内部** (qacc_warmstart / efc contact warm-start cache 等) であり、qpos/qvel 復元はこれに盲目。**M10 の経験 leg (= 1-step post-restore 動力学 leg: bank+1 step の state を producer の同 frame と比較) は基板非依存ゆえ STANDS、かつ本 ERRATUM により hidden-state の *唯一の* guard に昇格する (bar = fidelity band 内)。** 名前付き属性の write-set では mjData を捕捉できなかったため、本訂正は検証を弱めず強める。

### 併記 (B3 [CHECK] 実測、設計に影響する事実 — %12 独立確認済)

- **記録は既に cable の joint_q を保持**: `route_demo_recorder.py:231` `jq = state.joint_q.numpy()` (PHYSICS joint vector) → `route_demo_raw.npz["arm_q"]` shape **(7707, 74)** = arm 28 + cable 46。⇒ bank v2 capture の真の delta = **joint_qd のみ** (FD 代替は M10 が却下済、再審しない)。
- **restore-fidelity の比較 frame (%12 catch)**: fork state = producer frame `cf[t_k]−1` 終了時点 (chunk t_k 駆動直前) ゆえ、**restore 直後の div_grip は記録 frame `cf[t_k]−1` を参照する** (走行中 metric の `cf[t]+9` を流用しない)。誤用時は cable の実運動 10-frame 分が偽 divergence として混入 (実測: 境界 sample で 0.0–1.67mm、t=200 で 1.67mm)。規則は 1 本: **「state はそれが対応する記録 frame と比較する」**。

*%12 — 2026-07-13。PAPER-ONLY。設計判断・Rs 承認数値の変更ゼロ。INVARIANTS 不触。*

## §15. ERRATUM-C / 明確化 D-E (2026-07-13 22:2x、%12 — B3 5体 CC4/CC5 の CRIT 由来、%12 on-disk 検証済)

### ⭐ERRATUM-C (§6.2 restore fidelity DoD の bar = **domain 転用の誤り**、%12 own)

**誤**: §6.2-1 / §8 の restore fidelity DoD 「restore 直後 div_grip ≤ 健全域 band (10.4-10.6mm)」。
**事実 (B3 5体 CC4 実測)**: restore 域の期待誤差は **0.02-0.15mm** であり、**cable_qd を全ゼロにした bank (= bank v1 相当の null) でも 10.407mm bar を 3.4-44 倍の余裕で PASS する** ⇒ **本 DoD は bank v2 と v1 を区別できない = B3 chunk の存在理由 (cable 速度を含む fork state) が未検証のまま通る**。
**原因**: 10.4mm は **HOLD arming の健全域 band** (open-loop replay 中の divergence 分布) であって *state 復元* の期待誤差ではない。spec §6.2 L7 が両者を同一視し、%12 が B2 CLOSE 申し送りで「10.407 = restore band governs」と伝播した (domain 転用)。

**訂正 (bar を 2 本に分離 — §14 の規則『state はそれが対応する記録 frame と比較する』と整合)**:
- **(α) restore-exactness bar = 本 DoD**: div_grip(復元 state vs 記録 frame `cf[t_k]−1`) ≤ **~0.5mm (提案、確定 = B3 実測)** + fork 後 1-chunk 走行時 ≤ **~1mm**。値は **null bank の失敗 signature (0.5-2mm 級) を確実に分離する**ことを条件とする。
- **(β) no-immediate-HOLD sanity assert** (§6.2 原意の保全): 走行 metric (vs `cf[t_k]+9`) ≤ 10.407mm。**fidelity bar ではない。**
- **⭐判別力要件 (新規・一般則)**: fidelity DoD は **null bank (cable_qd ≡ 0 / arm-only v1 bank) で必ず FAIL すること** を negative-control leg で実証する。「PASS する DoD」ではなく「間違った bank を落とす DoD」を要求する。

### 明確化 D (FD による qd の *検算* は却下対象外)

§6.2-1 が却下したのは **FD による qd の「構築」** (記録位置列の差分を qd の *source* にすること) であり、**capture した qd の「検算」ではない**。記録に速度が無い以上、capture した joint_qd には独立 ground truth が存在せず、wrong state buffer (`_state_0`/`_state_1` の substep swap) / permutation / transpose / scale の誤りが **全 leg を素通りする** (CC4)。
⇒ **記録 joint_q の FD (dt=1/480 実測) を qd の consistency cross-check として採用する** (capture frame の |qd_fd| = 0.036-1.246 rad/s ≫ FD 打切り誤差 ⇒ 判別力あり)。**FD は ground truth ではない** ため bar は consistency (相関・相対誤差・符号・index 対応) であり exactness 証明ではない、と明記して用いる。

### 明確化 E (leg の駆動 mode 要件 — false-verification class の再発防止)

**feedforward (FF) mode の leg は arm 側の bank/restore を構造的に検証できない**: FF は毎 physics frame で arm を記録から上書きし `_per_world_fk_jq` も `jq_ff` から更新するため、arm bank の誤りが観測不能 (CC4)。B2 系 leg は全て FF ゆえ **arm bank を一度も検証していない**。
⇒ **fork/restore の fidelity leg は trainer が実際に使う IK/residual mode で走らせる** (B1 CRIT「producer harness が env を実行しない」/ B2 CRIT「10x index 誤読」と同じ **false-verification class**)。B3+ の標準。

### fork write-set の追加 (%12 on-disk 検証済 — 名前付き属性の欠落 2 件)

- **`_per_world_fk_jq`** (`:667` alloc / `:915`・`:1027` = P0 settle 値に reset / `:1143`・`:1199` = IK 補間開始点 old_fk_jq + obs 源) — fork write-set に**必須**。欠落すると IK/residual mode で **arm が P0 へ引き戻される** (cable だけ mid-route)。
- **`_target_seg_indices_{r,l}`** — refresh 自体は `:1081-1085` に存在するが、`_reset_worlds` 内で **P0-seeded cable (`:1079` seed_cable_joint_state ← `_settled_body_q`) の後・fork restore の前**に計算される。consumer #6 (`:1633`) の `reset_to_phase` は `_reset_worlds` の**後**に走るため、fork 後の seg 窓は **P0 由来のまま stale** → `p4`/G4 述語が誤 seg を測り **G4 が永久に latch しない** (CC4+CC5 独立収束)。⇒ **順序付き単一 fork entry point を env に建て、restore → seg 窓再計算 → `_per_world_fk_jq` 再設定 → route_t := bank_boundary[k] → G1..Gk latch pre-set の順**を強制する。
- **`forbid_banked_fork`**: 「撤去」ではなく **再条件付け** — v2 bank 不在時は書込*前*に raise (現 code の missing-bank silent no-op は「P0 cable に arm だけ mid-route 復元」を生む)。
- **cable restore は新関数を作らず既存 `seed_cable_joint_state` に `cable_qd=None` kwarg を追加** (AGENTS.md reuse gate + repo の静的監査 script が書込面を関数名で列挙するため、twin 新設は監査不可視になる)。

*%12 — 2026-07-13。PAPER-ONLY。Rs 承認数値 (HOLD 15/12/24 / Δ 0.020 / DR±20 OFF / mix 集合) は不変。INVARIANTS 不触。*

## §16. ERRATUM-D (2026-07-13 22:2x、%12 — %9 corrective C-α を受諾。**§14 ERRATUM-B の over-generalization を訂正**)

§14 ERRATUM-B は「body_q_prev / Dahl は本基板に存在しない」までは正しい (%9 独立 CONFIRM、反証不成立)。しかし続く **「本基板の hidden state = mjData 内部 → 1-step leg が *唯一の* guard に昇格」は誤り** (%9 C-α、%12 on-disk 再検証で CONFIRM)。訂正:

### D-1. hidden state は「消えた」のでなく「移動した」— しかも **捕捉可能**

- `SolverMuJoCo` の source に **`mjw_data` / `mj_data` / `mujoco_warp` / `eq_active` が実在** (inspect.getsource 実測) ⇒ **mjWarp `Data` は露出しており、B3 は capture/restore *できる*。**
- 本基板の carried state (%9 実測) = **`qacc_warmstart` / `act` / `act_dot` / `eq_active` / `solver_niter` / `contact`**。
- ⇒ 「触れないから経験 leg が唯一の guard」は **成立しない**。warmstart 系の disposition は **B3 の明示設計判断** (3 択、下記 D-3) であり、既定でも自明でもない。

### D-2. ⭐`eq_active` = THREAD 固有の第 2 channel (見落とすと invariant 抵触)

equality constraint の活性 flag は **4-bar linkage eq (`newton_skill_env_base.py:1446` の ENABLED-count assert 4)** と **clip-retention pin (`pin_eqid`、INVARIANT #5 の唯一の認可例外)** の両方を担う。fork 時に `eq_active` が不整合だと linkage/pin が producer と乖離する。**B3 は eq_active の fork disposition を明示すること** (capture/restore or 明示再構成 + 正当化)。

### D-3. ⭐fidelity bar の calibration 不整合 (%9 主 finding — ERRATUM-C の cable channel を **supersede**)

**事実 (npz 実測、%12 再現)**: FORK-1 の致死 seed = `frame0_perseg_mm` **mean 0.0200 / max 0.1469 mm** → t280 で 1.29mm → t343 で 16.07mm (HOLD 発火) = **~100× / 300 step の増幅**。
**⇒ spec DoD の `qpos/qvel L∞ ≤ 1mm / 1mm/s` (§6.2-1 / §8) は、致死 seed の max より ~6.8× / mean より ~50× 緩い。** warmstart 由来 0.5mm の restore 誤差は 1mm bar を PASS した上で **FORK-1 と同一機構で発散する** = **本 node が防ぐべき当の failure class に盲目**。本 node の存在理由自体が「本基板は 0.02-0.15mm を増幅する」ことの実証である以上、そこに 1mm bar を当てるのは自己矛盾。

**訂正 (bar の再設計)**:
1. **channel 分離**: arm/gripper = 毎 frame kinematic re-pose ゆえ **非増幅** → 1mm/1mm/s 可。**cable = 増幅 channel → 1mm bar を適用しない。**
2. **⭐1-step → K-step divergence-GROWTH leg に昇格 (本命 DoD)**: FORK-1 の signature は step-1 の *大きさ* でなく *成長* である。`G_k−ε` fork → Δ≡0 で **K ≈ 20-50 step** roll → producer 同境界 trajectory と `div_grip` 系列を比較。**PASS = 窓内 HOLD 発火 0 ∧ 健全域 band 内 (≤10.41mm aligned、B2 leg8) ∧ ramp signature (持続 ~1mm/step 単調増) 不在**。cuda:0 数秒、leg8 の較正手法を再利用。
3. **warmstart disposition = 3 択を明示比較して選ぶ**: (i) capture+restore / (ii) 両側 zero 化 / (iii) 非 restore + K-step leg で drift-bounded を実証。
4. **honest limit (bar の意味論)**: 全 solver state を復元しない限り fork は producer の連続軌道を **byte 再現できない**。⇒ 到達可能な bar は byte-parity ではなく **「physically valid ∧ drift-bounded continuation」** (= HOLD を発火させずに学習可能な episode を供給できること)。DoD はこの言葉で書く。
5. **⚠P0-reset precedent を転用しない**: P0 = settled/quiescent (warmstart ≈ 静的平衡) ゆえ非復元でも ⑨a′ EXACT が成立した。**G3-G5 fork は mid-route・把持中・接触 rich で warmstart は実情報を持つ** — 「reset で問題ないから fork も」は非転移 (%9)。

### D-4. ERRATUM-C との関係

ERRATUM-C (§15) の **判別力要件 (null bank = cable_qd≡0 で必ず FAIL)** は不変・強化。ただし C の「(α) restore-exactness ≤ ~0.5mm」提案は **cable channel については本 D-3 が supersede** — cable の bar は FORK-1 seed scale (≪0.147mm) か、さもなくば K-step growth leg による drift-bounded 証明に置き換える。arm/gripper の 1mm は残置。

*%12 — 2026-07-13。%9 C-α = 全面受諾 (over-generalization の own)。Rs 承認数値不変。INVARIANTS 不触。*

## §17. ERRATUM-E (2026-07-13 22:4x、%12 — %9 corrective C-β 受諾。**§15 明確化 E の over-generalization を訂正**)

§15 明確化 E は「fidelity/fork leg は trainer 実使用の IK/residual mode で走らせる (FF leg は arm bank を構造的に検証できない)」とした。**arm channel については正しい。しかし cable channel (K-step growth leg) に同要求を適用すると交絡が生じ、検出力がゼロになる** (%9 C-β、%12 CONFIRM)。

### E-1. 交絡の機構と大きさ

IK/residual mode では Δ≡0 でも arm は **IK 解**で駆動される ⇒ producer (FF = 記録 arm_q 直書き) と **arm 軌道が一致しない**。よって div_grip の成長が **(a) bank/hidden-state の誤り** と **(b) IK 追従誤差** の双方に起因し、**分離不能**。
**大きさ (%9 実測)**: 本基板の IK-path delta は **mm 級** (env batched-IK の L 腕 / EE_Z_FLOOR_KO +3.12mm) ⇒ 測ろうとしている信号 (FORK-1 致死 seed **max 0.147mm**) の **~20× の交絡**を注入する = **検出力ゼロ**。

### E-2. 訂正 = **leg の channel 分解** (C-α の channel 分離原則を leg 設計へ一貫適用)

1. **cable / hidden-state** → **K-step growth leg は FF mode** (arm を記録に pin) で走らせる。arm が固定されるので div 成長は cable + hidden state に**一意帰属**し、比較対象 = producer 同境界の FF trajectory = apples-to-apples。
2. **arm-bank** → **別 leg・非 FF (IK/residual)**。`arm_q`/`arm_qd == bank` ∧ **`_per_world_fk_jq` 設定済** (未設定 = arm が P0 へ引戻される) を直接 assert。← 明確化 E の本来の対象。
3. **統合 leg** → trainer の**実 mode** で 1 本。⚠実 mode は **hybrid** (L 腕 = feedforward 窓 + 他 = residual; routeexec node 参照) ⇒ 「IK/residual で」という blanket 要求は **phase 依存の実 mode で qualify** する。
4. **null-bank negative control (§15) は 1・2 の両方に適用**: cable null (cable_qd≡0) → leg 1 で FAIL / arm-only v1 bank → leg 2 で FAIL。

### E-3. メタ教訓 (2 度目、明示記録)

ERRATUM-B (Dahl/body_q_prev 不在 → 「capture 不能・経験 leg が唯一の guard」へ over-generalize → %9 C-α が是正) と、本 E (FF leg は arm に盲目 → 「全 leg を IK mode で」へ over-generalize → %9 C-β が是正) は**同型**である。
⇒ **規律: 訂正は「実際に検証した channel / domain」に scope を限定せよ。正しい訂正でも over-generalize すると隣接する正しい要件を消す。**

*%12 — 2026-07-13。%9 C-β = 全面受諾。Rs 承認数値不変。INVARIANTS 不触。*

### E-4 (追補 2026-07-13 22:5x、%9 B3-verify — **cross-mode bar transfer の禁止**)

**10.407mm の健全域 band は B2 leg8 = FF mode の実測値である。** これを IK/residual rollout の leg に当てるのは **cross-mode bar transfer** であり、ERRATUM-A (10× index) / B2 CRIT と同じ class の誤り (**IK mode の baseline は未測定**)。
⇒ **規律: div band を IK mode の leg で使うなら、先に IK-mode matched control (同 mode の nominal rollout) で band を実測してから。FF 由来の band を流用しない。**
⇒ leg 分解の最終形: **L5a = FF mode** (cable / hidden-state の K-step growth + null-bank negative control をここに置く) / **L5b = IK mode** (arm-bank + 統合; div band を用いる場合は IK-mode matched control が precondition)。
なお **`_per_world_fk_jq` 未設定の signature は 373-444mm 級**と巨大 (%9 実測) ゆえ、arm-bank leg に growth metric は不要 — **直接 assert (arm_q/qd == bank ∧ fk_jq 設定済) で十分**。

*%12 — 2026-07-13。%9 double-key: golden G-phase Σ=7707 EXACT + 別系統 (B2 leg8 cablediag の phase 遷移 113/173/259 == 導出 t_1/t_2/t_3) で ceil 整列も確証。*

### E-5 (追補 2026-07-13 23:0x — %9 副次発見 2 件 + p6 所見。%12 実測 CONFIRM)

**(1) guard の rationale を「最初に想定した trigger」に狭めるな (E-3 の対偶)。**
%12 は minor(4) で capture frame を手計算し、ceil 整列 (N8/R2c) を適用せず **raw phase 境界 f_3−1 = 2583** を用いて誤った (正 = chunk 整列 **2589**、margin 45 frame = 4.5 RL step、%9 が捕捉)。
⭐**この誤り class は builder の既存 guard R2d (`assert G(phase_id[capture_frame]) == k`) が build 時に落とす**: golden 実測で `phase_id[2583] = 6` / `phase_id[2589] = 7` (G3 = 15-phase 7) ⇒ **2583 で FAIL / 2589 で PASS**。
⇒ **R2d の正当化を「f_k %% 10 == 0 の multi-cell edge」に限定せず「capture_frame instantiation guard 一般 (raw-boundary 誤り class を含む)」へ広げる。guard を弱めない。**

**(2) k=3 の 45-frame margin は「薄い」のではなく「構造的」** (%9 の自己訂正、%12 実測 CONFIRM): `pin_active` の onset (frame 2544) は **phase_id 5→6 遷移と EXACT に一致** ⇒ **pin は phase schedule で発火する** (物理イベント依存でない) ⇒ DR / multi-cell では pin onset と capture_frame が **同一 schedule から co-move** する。⇒ R2k の pin 状態 assert は維持するが、**根拠は「fragile margin」ではなく「instantiation guard (上記 (1) と同族)」**と書く。

**(3) ⭐本 arc の corrective 3 連続 (C-α / C-β / E-4) は全て同一 class = 「計器が対象を測れていない」** (p6 所見、%12 同意):
- **C-α**: bar (1mm) が防ぐべき failure (FORK-1 致死 seed 0.147mm) より緩い = **感度不足**。
- **C-β**: 測定 mode (IK) が信号 (0.147mm) を交絡 (IK 追従誤差 mm 級) = **SN 比の破綻**。
- **E-4**: bar を別 mode (FF) から流用 = **較正の不整合**。
⇒ **DoD 設計の規律: 「PASS する DoD」ではなく「間違った成果物を落とす DoD」を書け。** 全ての fidelity DoD に対し **(i) この bar が落とす『間違った bank / 壊れた leg』を具体的に述べよ (ii) negative control (null bank 等) で実際に落ちることを実証せよ (iii) bar の測定 mode と leg の駆動 mode が一致していることを示せ** — 3 点を conformance の必須列とする。

*%12 — 2026-07-13。%9 副次 2 件 = 実測 CONFIRM (phase_id[2583]=6 / [2589]=7 / pin onset == phase 5→6 遷移 2544 EXACT)。*

## §18. ERRATUM-F (2026-07-13 24:0x、%12 — B3a leg の実測 DEFECT-1 を受諾。**§16 ERRATUM-D の前提を訂正**)

### F-1. 訂正: 本基板の live hidden state は `mjw_data` ではなく **`mj_data`**

§16 D-1 は「`SolverMuJoCo` の source に `mjw_data` が実在する ⇒ mjWarp Data は露出しており capture/restore できる」とした (%12 inspect + %9 独立 inspect)。**結論 (capture 可能) は正しいが、buffer の同定が誤り**:

- **`task_config.py:116` `USE_MUJOCO_CPU = True`** — かつ `make_solver(..., use_mujoco_cpu=USE_MUJOCO_CPU)` (`newton_skill_env_base.py:1302`) が既定 ⇒ **producer も route env も MuJoCo-C の CPU backend で走っている** (%12 実測)。
- `solver_mujoco.py:3267-3273`: `if self.use_mujoco_cpu:` → **`mj_step(self.mj_model, self.mj_data)`** = **CPU path が step するのは `mj_data`**。`mjw_data` を使うのは `else` (GPU) 分岐のみ。
- `mjw_data` は `mujoco_warp.put_data(...)` で**無条件に生成される**が、CPU path では **一度も step されない dead mirror**。
- ⇒ B3a の capture が `mjw_data` を読んでいたため **hidden-state channel が完全に inert** だった (実測: `qacc_warmstart` 非ゼロ = **0/562611**、`eq_active` は全 7707 frame で変動ゼロ)。記録側の独立 witness (`pin_active` = frame 2544-7706 ON / `pin_eqid`=27 / `pinned_body`=55) と矛盾する。
- ⭐**producer は無事**: `mj_data` が実 buffer ゆえ clip-pin は効いている ⇒ **RS71 INVARIANT #5 intact、Rs-LOCKED producer に欠陥なし**。壊れていたのは capture の read 先のみ。

**訂正**: hidden-state の capture/restore は **`use_mujoco_cpu` で buffer を選択** (`mj_data` / `mjw_data`) し、**liveness assert を必須**とする (下記 F-3)。

### F-2. ⭐メタ教訓 (3 度目、E-3/E-5 と同族): **source 上の存在 ≠ 設定 backend での liveness**

%12 も %9 も `inspect.getsource` / grep で **attribute の存在**を確認し、そこから **liveness を推論**した。**実際に走っている backend では死んでいた。** 捕捉したのは builder の **runtime 実測 leg** (0/562611)。
⇒ **規律: solver / hidden state に関する主張は、source inspection では discharge できない。設定 backend 上の runtime 測定でのみ discharge せよ。** (既存 memory `feedback-reuse-validate-by-build-run-not-import` = 「existence ≠ function、real BUILD+RUN on CURRENT substrate で検証」の再演。verifier 2 名が同時に踏んだ = grep 由来の確信は特に危険。)

### F-3. 裁定 (B3a ask D-1 / D-2)

**D-1 (warmstart は実 buffer で非ゼロか)**: 0/562611 は **dead mirror の測定ゆえ情報ゼロ** — 再測定は正しい。⚠ただし **「ゼロだったから非 item」と symptom だけで再分類するな (ERRATUM-B の教訓)**: **(i) `mj_data.qacc_warmstart` の実測 (live buffer) に加え、(ii) 機構の確認 = `mj_model.opt.disableflags & mjDSBL_WARMSTART` (warmstart が model option で無効化されているか) を必ず取れ。** 非 item への再分類は **(i) 恒常ゼロ ∧ (ii) 機構がそれを説明する** の両方が揃った時のみ。片方だけなら **B4=(a) capture+restore を維持**。

**D-2 (cross-backend transplant)**: **(a) を一般則 + (c) を W1 の instantiation** として採る。**(b) は D-1 の機構確認が済むまで不可。**
- **(a) 一般則**: bank の provenance に **backend 識別子 (`use_mujoco_cpu` / newton version / solver config hash)** を記録し、**restore 時に backend 不一致で fail-loud**。cross-backend transplant を **構造的に silent 不可能**にする (安価・恒久)。
- **(c) W1 instantiation**: env は producer と同一 backend (CPU) に **pin** — **現状すでにそうなっている** (`make_solver` 既定、%12 実測) ゆえ変更不要。**明示 assert として LOUD 化するのみ。**
- ⚠**campaign への含意 (W1 完了報告で Rs へ上程)**: trainer が throughput のため GPU backend を要するなら、**bank はその backend で再 capture が必要** ((a) が強制する)。さらに **B0 baseline (ca33d1e1a0) / B2 較正 / golden byte-repro は全て CPU 基準**ゆえ、**backend 切替 = substrate 変更 = Rs-gated** (builder 判断で行わない)。

### F-4. DEFECT-2 (leg3 の bar) = **CONCUR。E-5 (ii) の模範実行**

frame 級 FD が原理的に不適 (κ = |Δqd|/|qd| が k=2 で 0.92 / k=3 で 1.81、SIM_SUBSTEPS=10 ゆえ位置差分は frame 平均しか返さない ⇒ 4 変種が同時に落ちる = **data でなく計器の帯域不足**) + spec が名指しした hazard (wrong substep) は frame 級 FD を κ/10 ≈ 1.6% しか動かさず **20% bar では原理的に検出不能** = **感度不足/SN 交絡 class そのもの**。
置換 (2-param 回帰 → gain g / substep index m̂ / R²) と **identifiability 表 (m=9/m=8/null/sign-flip/×1.02/×0.98/permuted/frame-shift = 全 reject、real のみ accept)** は **E-5 の 3 必須列 (i)(ii)(iii) を満たす模範**。cable の gain 固有 bias −1.9% ゆえ scale bar は gripper (R²=1.000) が担う、の honest 分離も採用。
**leg6 (hidden-state liveness: captured `eq_active[27]` ≡ recording `pin_active` を per-frame EXACT 照合) = 今回の DEFECT-1 を必ず落とす negative control** ⇒ **必須化**。

*%12 — 2026-07-13。DEFECT-1/-2 とも builder の runtime leg が捕捉 (bar 緩和ゼロ = fix-first 遵守)。B3a の未 commit 判断も正 (defect を bank しない)。Rs 承認数値不変。INVARIANTS 不触。*

### F-5 (追補 2026-07-14 00:0x — %9 B3a 検分。**D-1 裁定を %9 の refinement で置換** + 戦略 risk 1 件)

**(1) D-1 の bar を訂正 (%9、%12 受諾)**: 「warmstart が非ゼロか」は **再分類の bar として誤り (E-5 (i) 違反)**。問うべきは **「restore vs zero で軌道が FORK-1 seed scale (0.147mm) で変わるか」= L5a (FF) 上の A/B**。
⭐**regret 非対称ゆえ (a) 据え置き**: bank して inert = nv floats の無駄 / **bank せず live = k=3/4/5 で silent な FORK-1-class mismatch**。**DEFECT-1 はその第 2 の失敗が実在かつ silent であることの実証**。warmstart は (Dahl/body_q_prev の *属性不在* と違い) **実在する live field** ゆえ zeros を bank しても無害。
⇒ **(a) capture+restore を既定として維持。非 item 化は L5a の A/B が ≪0.147mm を示した時のみ。** 機構確認 (`mjDSBL_WARMSTART` flag) は *説明*として取るが、**再分類の bar は A/B が担う** (%12 の当初裁定 = 機構確認を bar にする、を撤回)。

**(2) ⭐`eq_active` は D-1 の対象外 = 構造的要件 (経験問題でない)**: clip-pin (eqid 27 / body 55 / ON f2544-7706、%9+%12 golden 実測) は **INVARIANT #5 の唯一の認可例外**であり、**k=3/4/5 の fork 境界はまさに clip が cable を保持していなければならない所**。pin OFF の fork は「数値的に微妙」なのではなく **物理的に誤った state**。⇒ **warmstart の disposition に関わらず、eq_active/pin の capture+restore は必須。**

**(3) D-2 = 今日 cross-backend transplant は不在、やるべきは 1 行** (%9): `USE_MUJOCO_CPU` は **global** で producer/env とも `make_solver` 経由 ⇒ (a)/(c) は既に構造的に成立。bank meta は既に `use_mujoco_cpu` を記録 (:726) ⇒ **restore で `bank.meta.use_mujoco_cpu == solver.use_mujoco_cpu` を assert (fail-loud)** — 将来の flip が silent corruption → loud failure に変わる。

**(4) ⭐⭐ 戦略 risk (B3 より大 — trainer node / W0-a 級 risk register + Rs surface、%9 escalate、%12 CONCUR)**:
`task_config.py:116` の comment は「GPU (`use_mujoco_cpu=False`) = S8」、dual-track にも Track-2 (GPU-mjwarp)。**campaign が GPU backend へ flip する場合、W1 の calibration stack は全て CPU 実測である**: FORK-1 特性 / 健全域 band 10.407 / HOLD 15・12 / ramp signature / 全 fidelity bar / **さらに 0.716 = Rs-DECLARED MOTION STANDARD と golden byte-repro (B0 pin ca33d1e1a0)**。
**同一 backend 内の builder fork 0.15mm が致命だった系で、solver 実装ごと替える摂動は自明に大きい** ⇒ **flip すれば W1 検証 stack 全体が再検証対象**。⚠**campaign 時に発見してはならない。**
⇒ **(i) `task_config.py` = Rs SSOT ゆえ flip は L3 + Rs 専権 (builder 判断で行わない) (ii) 本項を trainer node の risk register に登録 (iii) W1 完了報告で Rs に決定項として上程: 「campaign は CPU-MuJoCo か GPU-mjwarp か。GPU なら W1 calibration stack の再検証が必要」。** devplan の「device-parity (cuda:2 vs cuda:0)」は **warp device の parity であって backend parity ではない** — 別項として明示する。

**(5) DEFECT-2 の pin (%9)**: 「scale 誤りは大域的ゆえ gripper が担う」の前提は **capture が単一 contiguous copy であること**。将来 group 別 slice になると group-local scale 誤りが素通り ⇒ **(i) 単一 copy を assert、or (ii) cable の g も telemetry 記録 (bias −1.9% からの *変化* が surface する)** を 1 行入れる。

**(6) ⭐E-5 の適用範囲を拡張 (%9 提案、%12 採択)**: **E-5 の 3 必須列は DoD だけでなく verify claim 自体にも適用される。**「機構が存在する」は **grep / inspect では discharge できない — run で検証せよ**。%9 の C-α と %12 の ERRATUM-D は共に静的検証で buffer liveness を主張し、**両者とも誤った** (= 計器 [inspect] が対象 [liveness] を測れていない = 自分たちが指摘した 3 class と同型)。

*%12 — 2026-07-14。%9 が自らの C-α sub-claim を own、%12 は D-1 裁定を %9 の refinement で置換。Rs 承認数値不変。*

### F-6 (追補 2026-07-14 00:0x — %9 D-2 UPGRADE を採択。**F-5 (3) の bool assert を supersede**)

**⭐hidden state は「backend」ではなく「model layout」で index される。** F-5 (3) が指示した `bank.meta.use_mujoco_cpu == solver.use_mujoco_cpu` の **bool assert は床にすぎない** (%9)。

**より起きやすい失敗 (実在確認済、%12)**: **同一 backend でも scene が違う bank を restore すると eq/body index が shift して silent corruption**。
- `add_c2_clip=True` は **C2 V-groove clip の body/shape を追加する** (`newton_skill_env_base.py:1494-1517` docstring: "add a second collidable C2 V-groove clip") ⇒ **C2 build と no-C2 build で model layout が異なる**。
- 本 project は scene variant を**日常的に**使う: `route_c2_scene` (既定 False = byte-identical baseline / True = comp5・route-executor) / no-C2 control run (`dd7c97d480`) / multi-cell / comp3b / DR。
- ⇒ **backend flip より遥かに起きやすく、bool assert は素通りさせる。** pin は `eqid=27` / `pinned_body=55` という **index** で記録されているため、layout が 1 つずれれば **別の constraint を活性化する = 物理的に誤った state を silent に作る**。

**訂正 (provenance の格上げ)**:
1. **provenance = (backend_id, layout_hash)**:
   - `backend_id` = `use_mujoco_cpu` + solver class + newton / mujoco version
   - **`layout_hash`** = `nq` / `nv` / `neq` / `nefc-max` + **eq の name→index 写像** + **scene flags** (`route_c2_scene` / `grasp_actuation` / clip config)
2. **restore で両方の一致を fail-loud assert** ⇒ **backend flip / scene 変更 / version bump / index shift の class 全体が 1 本の guard に畳まれる** (E-5 の「間違った成果物を落とす」を provenance 層で実装)。
3. ⭐**eq は index でなく name で解決して restore する** — assert = 「**変わったことを検出する**」floor / name 解決 = 「**変わっても壊れない**」robust form。**両方要る** (%9)。
4. cost = `layout_hash` は構築時 1 回。

**corollary (%9)**: repo 全体で `use_mujoco_cpu` を override する caller は**ゼロ** ⇒ producer (`test:8146`) と RL env (`base:1938`) は同一 global に従う ⇒ **flip は atomic (片方だけ飛ばない)**。**唯一 cross-backend を生む経路 = 「今日 capture した bank を flip 後の env へ restore」** ⇒ **provenance assert が唯一の防壁**であり、これを layout_hash 込みにしておけば scene 変更も同時に守られる。

**leg6 の穴 3 件 (%9 → p3、build 中に塞ぐ)**: (i) index-space trap (`eqid=27` の hardcode) (ii) 部分修正の素通り (warmstart の buffer 誤選択でも leg6 は PASS する → **各 hidden field に「変動 > 0」の liveness gate** を課す) (iii) lag convention (記録 `pin_active` と solver `eq_active` に 1 frame lag があり得る → EXACT を課すと fix 後に false-FAIL → **実測して pin**)。

*%12 — 2026-07-14。F-5 (3) の bool assert は本 F-6 が supersede。%9 の upgrade を実在確認の上 採択。*

### F-7 (追補 2026-07-14 03:4x — B3a re-capture の実測。**warmstart は LIVE / index-space trap / 幾何 anchor carry**)

#### F-7.1 ⭐warmstart は「非 item」どころか **massively LIVE** — 実害を寸前で回避

**実測 (B3a re-capture、%12 独立検証済)**:
- dead mirror (`mjw_data`): 非ゼロ **0 / 562611**  →  **live (`mj_data`): 非ゼロ 559764 / 562611、absmax 1.08e6**。
- 機構: `mjDSBL_WARMSTART` = **512** / モデルの `disableflags` = **524288** (= `mjDSBL_MULTICCD` のみ) ⇒ **524288 & 512 = 0 ⇒ warmstart は無効化されていない = LIVE** (%12 が mujoco module で独立確認)。
- ⇒ **「0/562611」は substrate の事実ではなく、死んだ buffer を読んだ計器の artifact だった。**

⚠**もし当初の D-1 bar (「非ゼロか?」) で非 item に再分類していたら、absmax 1e6 の live hidden state を bank から落としていた** — **本 chunk が消そうとしている silent FORK-1-class defect を、自分の手で作るところだった。**
**防いだのは 2 本の独立な guard**: (i) %12 の「symptom だけで再分類するな = 機構 (`mjDSBL_WARMSTART`) も確認せよ」(ERRATUM-B の教訓) — flag は ENABLED を示すので zeros と矛盾し、必ず調査に回った。(ii) %9 の **regret 非対称** (bank して inert = 無駄 / bank せず live = silent 致命) ⇒ **(a) 据え置き**。
⇒ **B4 = (a) capture+restore は「保守的選択」ではなく実測上の必須事項に格上げ。** disposition (restore vs zero が軌道を動かすか) は F-5 (1) 通り **L5a の A/B** が答えるが、**bank から落とす選択肢は消滅した**。

#### F-7.2 ⭐index-space trap: Newton body id ≠ MuJoCo body id (**+1**)

記録の `pinned_body` = **Newton body id (55)** / model の `eq_obj1id` = **MuJoCo body id (56)** — **MuJoCo は worldbody を index 0 に置くため +1 ずれる**。
⇒ 初版 resolver に Newton id を渡すと **eq 26 に着地** (正解 27) = **物理的に別の constraint を silent に pin する**。
= **F6 (`_jws` の関節 ID vs 座標) に続く index-space 混同の第 2 目撃例**。⚠**罠を防ぐために書いた関数自身が罠を踏んだ**。
**規則**: (i) **offset を hardcode しない** — producer 自身の eq 表から導出する (ii) **round-trip assert を必須**にする (identity → 元の eqid に戻ることを要求) (iii) bank は **newton / mjc 両 id + 実測 offset** を保持する。

#### F-7.3 honest limit + carry (B3b/B4)

layout_hash assert (F-6) が同一 layout を保証するので、**今日は banked index で足りる**。
**cross-layout の真に robust な形 = 幾何 anchor** — producer 自身は `:2352-2364` で **world 位置一致**で eq を探している。**未実装 ⇒ B3b/B4 の carry として登録** (charter §7-4: builder は新設計を独断しない。設計要否は %12 が B3b conformance で裁定する)。

#### F-7.4 メタ (5 度目): **計器そのものが第一の誤差源**

本 arc で捕捉された誤りの大半は「対象」ではなく「計器」に在った: bar が failure より緩い (C-α) / 測定 mode が信号を交絡 (C-β) / bar を別 mode から流用 (E-4) / source inspection が liveness を測れない (F-2) / **死んだ buffer を読んだ測定が substrate の事実に見えた (本 F-7.1)**。
⇒ **規律 (再掲・強化): 測定値を substrate の事実として扱う前に、「その計器は対象を測れているか」を先に discharge せよ。** 特に **ゼロ / 不在 / 変動なし** の測定は、**対象が無い**のか **計器が死んでいる**のかを区別できない — **必ず positive control (変動を示すはずの独立 witness) を併走させよ** (B3a leg6 = 記録 `pin_active` を独立 witness にした形が正解)。

*%12 — 2026-07-14。F-7.1 の機構 (disableflags=524288 / WARMSTART bit=512 未設定) は %12 が mujoco module で独立確認。B4=(a) 確定。*

## §19. F-8 — ⭐**本 arc の最終規律: guard 自身の positive control** (2026-07-14 05:3x、%9 escalate、%12 受諾)

### F-8.1 事実

我々は一晩で多数の guard を建てた (F-6 layout_hash / index-space assert / liveness / null-bank negative control)。**しかし guard が *発火すること* を一度も test していない。**
- leg6 = **データ**が live であることの positive control ✅
- **guard が live であることの positive control = ゼロ** ❌

**具体的破れ (%9 が自らの保証を撤回、%12 verify)**: %9 と %12 は Rs 上程で「**bank 46 eq vs env 6 eq ゆえ layout_hash assert は必ず発火し、physics 前に fail-loud で BLOCK する**」と断言した。しかし **layout_hash は provenance が運んでおり**、provenance reader は当時 **meta 欠落 / parse 失敗 / key 欠落 の 3 経路すべてで無言 None** を返していた ⇒ 無言 None → eq_identity 空 → 無言 return None → **比較対象が消える** ⇒ ⛔ **assert は発火しない**。
⇒ **「fail-loud に守られている」という保証自体が、保証されていなかった。** (⚠ 2026-07-14 05:1x に %12 の adversarial pass が発見 → %11 が同 turn で修正 [`_capture_provenance(capture, required)` = 必須時は RAISE、docstring に旧挙動を明記] — 修正済だが、**規律としては未確立だった**。)

### F-8.2 ⭐規律 (F-7.4 の guard への適用)

> **F-7.4** (零/不在の測定は「対象が無い」のか「計器が死んでいる」のか区別できない ⇒ positive control を併走させよ) は **guard 自身にも適用される。**
> ⭐ **一度も発火しない guard は、発火 *できない* guard と区別がつかない。**

### F-8.3 必須 DoD: **guard identifiability 表** (leg3 の 8/8 手法を「データ」でなく「guard」に当てる)

全ての guard に対し、**それが落とすべき入力で実際に落ちること**を表で実証する。B3b の restore guard の場合:

| # | 入力 | 期待 |
|---|---|---|
| (a) | provenance **欠落**の bank | **RAISE** |
| (b) | provenance **破損** (parse 不能) の bank | **RAISE** |
| (c) | **別 layout** の bank (neq=46 vs env neq=6 = **B3-α そのもの**) | **RAISE** |
| (d) | **pin 無し** (k=1,2 = 正当) の bank | **PASS**、かつ (a)(b) と **`pin_active` 全ゼロの assert で区別されること** |

⇒ **修正前は (a)(b)(d) が全て同一の無言 None を返していた = guard は 3 者を区別できなかった。** (a)-(c) が RAISE し (d) が PASS して初めて **guard は「生きている」**と言える。

### F-8.4 併せて撤去すべき無言吸収の機構 (%9 roster、HEAD 実読)

- **broad `except Exception` → `return None`** (mujoco import 経路 :537-542) — enum が動いただけで resolver が無言で「pin 無し」を返す。**narrow + raise へ。**
- **`(prov or {}).get(...) or {} ... or []` の 3 連 fallback** — **無言吸収の機構本体**。明示的存在確認 → raise へ。
- **「caller must fail loud」を *契約* で済ませない** (:544-549 のコメントが自認) — **機構にする** (呼ばれ方に依存させない)。
- **「記録に pin 無し」と「witness field が無い」の同一視** (:611-617) — 前者は **assert された正当条件** (`pin_active` 全ゼロを実測)、後者は **raise**。

### F-8.5 メタ (%9 の自己申告、記録として)

%9 は「(d) は de-risk された」という**自分が欲しかった結論**を支持する証拠 (raise の多い assert 本体) を見つけて**そこで止め**、否定する証拠 (entry point の無言 None) を先に探さなかった — **prohibited.md「確証バイアス禁止」の明文違反、本 session 2 度目** (1 度目 = mjw_data の静的検証を全体に一般化) と自ら申告。**%12 も同型を 2 度踏んでいる** (ERRATUM-B の over-generalize / 明確化 E の over-generalize)。
⇒ **verify 側の確証バイアスは、独立な adversarial pass (「自分が欲しい結論を否定する証拠を先に探す」担当) を per-chunk で立てることでしか捕まらない。** 本 arc では %12 の class 狙い read と %10 の通し精読が交互にそれを果たした。**B3b 以降も 2 系統を維持する。**

*%12 — 2026-07-14。F-8 は本 arc の締めくくり。Rs 上程の「assert が守る」主張は F-8.1 のとおり *当時は* 保証されていなかった — 訂正済 (修正 landed、ただし F-8.3 の identifiability 表で実証するまで「発火する」とは主張しない)。*

### F-8.6 (追補 — artifact provenance の再 pin、%10 実測 → %12 裁定)

**規則: artifact を生成した code を訂正 commit が触る場合、artifact は再生成して pin を張り直す — さもなくば artifact を明示的に retire する。**

**実例 (B3a)**: bank_capture.npz の meta は `route_executor_sha256 = _self_sha256()` を埋め込む。訂正 commit の途中で **banked meta = d8a1a3c8… vs on-disk module = 37041dac… ⇒ MATCH False** (%10 実測) ⇒ **「final code == final run」アンカーが失効**。しかも A-2 (BANK_OUT) の fix は **capture 側 code** を触るので「builder 側だけだから artifact に影響しない」も成立しない。
⇒ **stale pin は「pin 無し」より悪い — 偽の同一性を *主張する* から。** = **F-8 class (生きているように見えて死んでいる計器)**。かつ **B3a の artifact は B3b の入力**ゆえ、濁すと **もう存在しない code が作った bank の上に build する**ことになる。

**⭐ さらに「再走」を positive control に格上げする (裁定)**: 再走後、**新旧 npz の *データ配列* が byte-identical (meta/sha のみ差分) であることを assert** せよ。
- **一致** = 「guard/validation の訂正は、捕捉されるデータを一切変えていない」の **実証** (単なる「再走した」が「訂正が副作用を持たなかった証明」に格上げされる)。
- **不一致** = **発見** (訂正が capture 挙動を変えた) → **STOP して調査**。
⇒ **どちらに転んでも情報が出る leg** = 本 arc の規律 (「PASS する DoD」でなく「間違いを落とす DoD」) の適用。

*%12 — 2026-07-14。%10 が commit 前の再走で 2 連続 in-flight 破綻を捕捉 (arity TypeError / import json 欠落 NameError) — 「commit 前に必ず再走」を B3b 以降も維持。*

### F-8.7 (追補 — %10 catch: **検証手順が自分の baseline を破壊する** / **容器 hash で比較しない**)

**(1) ⭐検証手順は自分の baseline を破壊してはならない。**
F-8.6 で「再走して新旧 npz の data 配列 byte-identity を assert せよ (= positive control)」と裁定した。**しかし `run_legs.sh` の LEG2 は再走前に `rm -f bank_capture.npz` する (:23)、かつ npz は非 commit (5.8MB)** ⇒ **そのまま再走すれば比較対象 (pre-fix artifact) が消滅し、裁定した assert が *永久に実行不能* になる**。
⚠ **「再走を positive control に格上げする」という裁定そのものが、再走の副作用で失われる構図だった** (%10 が先回りで pre-fix npz [sha256 312dc638…770 = §7.1 の現 pin と EXACT、由来 module d8a1a3c8] を退避)。
⇒ **規則: artifact を再生成する前に、pre-change artifact を保全し provenance を pin せよ。** 正式 baseline は **builder 側 (leg script が参照する場所)** に置く (verifier の session-local scratchpad は消える)。

**(2) ⭐容器 (container) の hash で比較しない — 必ず false-FAIL する。**
**npz は zip** ゆえ **file 単位の sha256 は圧縮 metadata で必ず変わる** ⇒ **file-sha を byte-identity の assert にすると、データが完全に同一でも必ず不一致 = false-FAIL** (= 「計器が対象を測れていない」class の再演)。
⇒ **正しい assert は array 単位**: `joint_q` / `joint_qd` / `grip_target` / `qacc_warmstart` / `eq_active` / `frame_idx` の **6 配列すべてが `np.array_equal`** ∧ **meta のみ差分** (`route_executor_sha256` は更新される / `frames` / `backend` / `cell_env` は不変であるべき)。
⇒ **一般則: 「同一性」を assert する時は、意味的な単位 (配列・field) で比較する。容器の hash は同一性の proxy にならない。**

*%12 — 2026-07-14。%10 が裁定の自己破壊性と false-FAIL trap を同時に捕捉し、baseline を先回り保全。verify 側の 2 系統 (通し精読 + class 狙い) が、裁定側 (%12) の見落としを 2 回連続で捕まえた形。*

---

## §20. F-9 — ⛔ **着座計器が拘束の軸と一致していない** ⇒ 成功条件が demo 分布の 70% で到達不能 (2026-07-14 06:4x、%12 起票 / p1 独立 CONFIRM / **Rs 裁定要 — STOP**)

### F-9.1 事実 (全て on-disk、file:line)

**(1) 溝が拘束する軸は X と Z であって Y ではない。**
`create_clip.py:68` — "extrude a 2D cross-section profile **along Y-axis (cable direction)**"、断面は **XZ 平面** (`:76`)、`:52` BASE_DEPTH = "30mm pedestal depth (**Y-axis, cable direction**)"。
⇒ **Y = 押し出し軸 = 設計上ケーブルが滑ってよい自由軸 / X・Z = 断面 = 跨げば脱落する致命軸。**

**(2) しかし計器は XY ノルムで測っている。**
`newton_route_env.py:1299-1310` `_seat_metrics`:
- `:1305` `near = argmin |cable_y - clip_y|` — **nearest-in-Y の node を 1 つ取る**
- `:1308` `lateral = ||p[:2] - clip_xy||` — **XY ノルム (dx と dy を混ぜる)**
- `:1309` `seat_dist = sqrt(lateral² + z_gap²)`
⇒ **自由軸の残差 dy を「着座誤差」として課金している。** dy は物理的な着座の良し悪しと無関係。

**(3) dy には node 離散化の床がある。**
golden 実測 (`route_demo_raw.npz`, `cable_xyz` [7707, 40, 3] final frame、%12 実測): **median node Y-spacing = 14.64mm**。
⇒ nearest-node の |dy| は **[0, 7.32mm] にほぼ一様**。**これが計器の分解能の床。**

**(4) bar はその床の半分以下。**
`:1549` `p3 = (c1_seat < T_GROOVE) and (ph >= 2)`、`T_GROOVE = 0.003` (`task_config.py:368`)。
⇒ **bar 3.0mm < 量子化床 7.32mm** ⇒ **G3 の発火は「node がたまたま溝の Y 中心の 3mm 以内に落ちたか」の抽選。**
**算術整合 (script 非依存の独立レグ)**: P(|dy| < 3mm) = 3 / 7.32 = **41% が上界** (dx・z_gap がさらに予算を食うので実際は下回る) ⇒ **観測 24/81 = 30% は量子化抽選仮説と機構的に整合。**

**(5) ORDERED latch により、G3 の取りこぼしは +200 を殺す。**
`:1556-1565` `if k > 0 and not self._g_latched[w, k-1]: break` (ORDERED) + `:1569` `if self._g_latched[w, 4]:` (G6 は G5 latch を要求)。
⇒ **G3 未発火 ⇒ G4/G5/G6 到達不能** ⇒ **SHIPPED env は demo 分布の 57/81 (70%) で +200 を一度も出せない。**
**実測 24/81 到達 = %12 と p1 の 2 者独立 recount で一致** (⚠ 同一 artifact 上の決定論的 recount ゆえ Δ=0 は構造上の必然 — **独立ノイズの一致ではない**。独立レグは上記 (4) の算術)。

**(6) 同じ計器を C2 側も使う。**
`:1312-1319` `_c2_seated_honest` → `wall_ok = seat_dist*1e3 <= C2_WALL_SEAT_TOL_MM (0.5) + T_GROOVE*1e3 (3.0)` = **3.5mm bar** に同じ `seat_dist` を適用 ⇒ **G5 と G6 の c2 連言も同じ量子化欠陥。**

**(7) 対になる第 2 の欠陥: FAIL できない述語。**
`:1490-1494` `c1_retained = (z_c1 < 0.840) and (flank == flank) and (flank < 0.840)` = **天井チェックのみ、X を読まない** ⇒ 溝から外れて机に落ちた cable も PASS ⇒ **81/81 no-op。**
⚠ **訂正 (commit `32e6bde9ad` の記述は on-disk と不一致)**: 「retention is never re-checked at success time」は**誤り**。`:1570` `g6_live = c2_honest and c1_retained and (not dropped) and span_ok` ⇒ **成功時に再評価されている**。
⇒ **欠陥は「評価場所」ではなく「述語の中身」。「成功時に再チェックを足す」fix は何も変えない。**

### F-9.2 ⭐ 二重の病理 (同じ成功条件の連言に同居)

| # | 述語 | file:line | 病理 |
|---|------|-----------|------|
| (a) | `c1_retained` | `:1490-1494` | ⛔ **FAIL できない述語** (天井のみ、81/81 no-op) |
| (b) | `p3` (G3) / `p5` (G5) | `:1549` / `:1551` | ⛔ **PASS できない述語** (bar 3.0mm < 量子化床 7.32mm、70% の cell で不発) |
| (c) | `_c2_seated_honest` | `:1312-1319` | ⛔ (b) と同じ計器・同じ欠陥 |

⇒ **「常に PASS する述語は FAIL *できない* 述語と区別がつかない」(F-8 class) の対偶 = 「常に FAIL する述語も同じく無用」。本 env は両方を同時に踏んでいる。**

### F-9.3 物理は無効化されない — 危険は遡及でなく**前向き**

**公式 0.716 (58/81, `recount_w0e_81rerun_snapdown_0537.json`) は生存。** 58 SUCCESS 全部で C1 は最終フレームに**実際に溝の中**にある: 補間計器 (下記 F-9.4) で **across-groove |dx| med 0.94mm / max 1.94mm、3mm bar 超過 0/58**。producer 側の `cable_c1_seat_dist_mm` は `mj_geomDistance` の符号付き geom 間距離ゆえ lateral-sensitive で、50mm 横にずれた cable が −0.67mm を記録することはあり得ない。
⇒ ⭐ **計器の欠陥は採点を無効にするが、物理を無効にしない。** scripted producer は穴を exploit しない。**RL は必ずする。** ⇒ **危険は「過去の 0.716 が嘘だった」ではなく「これから訓練する env の計器が壊れている」。**

### F-9.4 campaign への含意 (= B3b STOP の根拠、⭐これが本 ERRATUM の stake)

**70% の cell で +200 が到達不能** ⇒ **agent は成功信号を一度も受け取らない** ⇒ **SR は述語を測っていない** ⇒ campaign は「RL が効かない / task が難しすぎる」と**誤診**される。
⇒ ⭐ **数週間の GPU を、壊れた計器の上で焼くことになる。SR は無意味であるどころか積極的に誤導的。**
⇒ **B3b-B7 = STOP 継続。本件裁定まで trainer campaign の launch gate は開かない。**

### F-9.5 提案する fix (⛔ **Rs 裁定要 — %12 は実装しない**)

**⛔ 権限**: success condition の変更 = **直交 DESIGN-GATE** (CLAUDE.md §運用2、L0-L3 に関わらず常時必須) + **spec = Rs 専権**。⇒ **STOP → 本 ERRATUM → Rs 上程。CC は patch しない。**

**(1) 計器を拘束の軸に合わせる (bar は緩めない)。**
- ❌ **nearest-node の XY ノルム**をやめる。
- ⚠ **「dy 項を落とすだけ」では不十分** (p1 案の方向は正しいが未完): nearest-node は溝中心から**最大 7.32mm ずれた Y** にいるため、そこで dx を測ると**湾曲した cable では別の Y での dx** を測ることになる。
- ✅ **正しい計器 = cable 折れ線を `y = CLIP_Y` で補間し、致命軸 `|dx|` と `z_gap` で採点する。**
- ✅ **bar 3.0mm は据置** (実測 |dx| max 1.94mm ⇒ 3mm は妥当)。⇒ **計器を直すのであって bar を緩めるのではない** = §運用15 の conservatism 方向を満たす。

**(2) `c1_retained` に X の溝内条件を足す** (現状は天井のみ = FAIL できない)。

**(3) ⛔ env 単独修正は不可 — DoD-9a parity 契約を破る。**
欠陥は env への port ミスではなく**凍結 PREREG 定義**の側に在る (env docstring `:1287-1289` が自ら "the EXACT frozen def" と宣言、`:1313-1314` は "Geometric **proxy** of the runner producer" と自認)。
⇒ **env だけ直すと offline recount (strict_v2) との parity が壊れる。**
⇒ **env + offline (strict_v2) + PREREG 定義 の 3 点同時改訂が必要** = **spec 層 = Rs 専権。**

**(4) 真の reuse**: producer は量子化フリーの `mj_geomDistance` を既に持っている。**env はそれを mirror せず、proxy を自作した。** ⇒ 修正の第一候補は「producer の測定量を env が使う」。

### F-9.6 メタ教訓 (本 arc の型の反復)

- ⭐ **拘束系をノルムで測るな — 自由軸が致命軸を隠す。** 拘束の軸を **built model から読み** (`create_clip.py:68`)、**軸ごとに分解**して報告する。rope/cable は **nearest-node でなく補間**。
- ⭐ **正しい答えは、誤った答えの *すぐ隣に* 既に在った** (今夜 3 回): `_seat_metrics` は壊れた retention 述語の 4 行上 / offline は 81 cell 全てに `cable_c1_final_dist_mm` を保持 / producer は量子化フリーの wall 距離を持っている。⇒ **再利用せず、作り直した。**
- ⭐ **verdict 文字列を script に hardcode するな** (p1 own): p1 の検証 script は「%12 の [R4] CONFIRMED」と**印字しながら**、自分が測った数値 (0% unreachable) と矛盾していた。**verdict は必ず測定値から導出する。** p1 は数値を読んだから捕まえた — 要約行を信じていれば、本 arc 最大の発見が偽の反証で潰されていた。
- ⭐ **発見が劇的で、かつ自分の立場を強くする方向のときこそ手を止める** (%12 own): 私は同じ XY ノルムで測って「58 SUCCESS のうち 41/58 が bar 超過」= 0.716 を崩す劇的数字を出した。**artifact だった。**
- ⇒ **双方向の adversarial pass が無ければ、p1 の偽反証と %12 の偽陽性は両方通っていた。**

*%12 — 2026-07-14 06:4x。p1 独立 CONFIRM (24/81 完全一致、fix 方向 一致)。⛔ **本 ERRATUM は Rs 裁定待ち。B3b-B7 STOP 継続。実装は行わない。***
