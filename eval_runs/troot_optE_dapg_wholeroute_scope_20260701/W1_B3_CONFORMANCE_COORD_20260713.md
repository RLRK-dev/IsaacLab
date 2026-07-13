# W1 B3 Conformance Table — bank v2 (producer capture + env-level cable restore)

**Doc:** W1_B3_CONFORMANCE_COORD_20260713.md **v2** (v1 22:0x → 5体 [VERIFY] 全面 fold 22:5x)
**Author:** %11 (COORD, w2:p3, builder leg) — 2026-07-13 (date-THEN-write)
**Node:** T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild / chunk B3
**Design SSOT:** `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.8.1 §6.2 :135-147 + §4.1 :74-78 + §8 + §9 + **§14 ERRATUM-B (955ff0648f)**
**Charter:** `W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md` v0.2 B3 行 :36 + ERRATUM-1/2/3
**[L-TRIAGE]:** L3 (diff keyword + ≥5 files)。直交 [DESIGN-GATE] = cite 充足 (reward/成功条件 不変)。
**%12 裁定 (22:15、ERRATUM-B 955ff0648f):** A1 = 「state はそれが対応する記録 frame と比較する」規則 / A2 = 1 chunk 続行 (見積 delta 記録・~600 で分割) / **A3 = MOOT (Dahl/body_q_prev は本基板に不在 → 非項目、hidden-state guard は 1-step leg に昇格)**。

**5体 verdict (全員着弾):** CC2 REVISE (CRIT1 = **artifact 取り違え → REFUTED**、他 MED/LOW 有効) / CC3 **CRIT (Rs-LOCKED)** / CC4 CRIT×4 / CC5 CRIT×1 / CC6 CRIT×2。**CC1 DECIDE = 全 finding ACCEPT (CC2-1/2 は実測で REFUTE、ただし hazard class は採用)**。
**%12 ERRATUM 群 (本 v2.1 の SSOT):** §14 ERRATUM-B (955ff0648f、Dahl/body_q_prev = 非項目) / **§15 ERRATUM-C (aae9f78722、bar 2 本分離 + null-bank negative control を DoD 化)** / **§16 ERRATUM-D (a07b03ed69、mjWarp Data 露出 → warmstart は capture/restore 可能; 1mm bar は FORK-1 致死 seed の 6.8-50× 緩 → cable channel 再較正 + K-step growth leg; eq_active disposition 必須)** + 明確化 D (FD = consistency check) / E (FF mode leg は arm bank を構造的に検証不能)。
**%9 C-α (22:23):** hidden state は消えたのでなく**移動** (mjWarp Data) / bar は FORK-1 seed より緩い / 1-step → **K-step divergence-growth leg** へ昇格。

---

## §0. [CHECK] 実測 — 修正版 (v1 の 4 事実 + 5体が捕捉した 5 事実)

| # | 事実 | 根拠 | v1 との差 |
|---|---|---|---|
| **F1** | 記録の `arm_q` = **full physics joint_q (7707, 74)** = arm 28 + cable 46 (free-root 7 + hinge 39)。46/46 列が実変動 (data-level 確認)。無いのは **joint_qd のみ** | route_demo_recorder.py:249 / 実測 shape + 変動列数 (CC6 が data-level 確認) | **維持** |
| **F2** | env の RL step t 後 = 記録 frame **10t+9**。comp5 の `10t+3` は `_nsub = RL_SIM_SUBSTEPS(=4)` の誤同定 (comp5:162→:213)。**dt = 1/480 Hz (sim_time 実測 0.002083s)** | newton_route_env.py:407 / newton_skill_env_base.py:95 / 実測 | **維持 + dt 実測追加** |
| **F3** | fork state = producer frame **cf[t_k]−1** = **convention A**。⚠**根拠は解析的強制であって経験的判別ではない**: (i) recorder は post-step sample (:561-562) (ii) chunk t は frame cf[t]..+9 を消費 (iii) 走行 div は cf[t]+9 を読む (:3419) ⇒ fork 状態は frame cf[t_k]−1 の post-step 状態でしか整合しない | CC3/CC4 が独立に導出 | ⚠**v1 の「≤1.14mm ゆえ無視不可 → R5d が判別」は誤り**: 5 境界での 2 convention 差 = **0.0008 / 0.194 / 0.0008 / 0.009 / 0.002 mm** (held-seg、CC4 実測) = **0.15mm settle 床の下** ⇒ 経験的判別は**不能 (vacuous)**。convention A は解析的に確定、leg は telemetry のみ |
| **F4** | capture = **全 frame dump** (7707 × (74 q + 73 qd) f32 ≈ 4.4MB) — boundary 選択は offline builder | — | **維持** (CC4「good design, keep it」) |
| ⭐**F5** | **`run_route` 自体が Rs-LOCKED** (route_executor.py:**1027** 「ANTI-REVERT / Rs-LOCKED — do NOT edit any line of run_route without Rs」、span :1038-3110)。recorder の **ctor :1074 / finalize :3109 は lock 内側**。**hook :561-562 が属する `physics_step` (:503-565) だけが lock の外** | 本 turn 実測 (CC3 catch) | ⭐**v1 は「recorder と同型に ctor/finalize を挿す」= LOCKED 関数編集 = CLAUDE.md hard-stop 違反だった。** → **回避策 = capture を physics_step 内の遅延 init + atexit finalize に閉じる (locked 行ゼロ、Rs waiver 不要)** |
| ⭐**F6** | **`_jws` は「関節 ID」基点であって「座標」基点でない**: 1 world = **68 関節 / 74 座標** (cable free-root = 1 関節 ↔ 7 座標 / 6 速度)。既存 :1075-1077 は `_jws[w]+28` を**関節 ID list** の生成にのみ使い、座標は `model.joint_q_start` が解決 | newton_skill_env_base.py:1088-1092 / CC6 catch | ⭐**v1 の R3b「per-world の joint offset で書く (`_jws[w] + _N_ARM_JOINTS ...`)」は座標直書きと誤読され得る → world 0 だけ正しく w≥1 が 6·w ずれる罠。** cable 書込は **必ず `model.joint_q_start` 経由**と明記 |
| ⭐**F7** | **arm の banked qd = 0 は「妥協」でなく EXACT**: 本基板は arm joint_qd を毎 frame ゼロ化 (producer physics_step:543 / env `apply_arm_only_write_perworld`) ⇒ **capture した arm qd は 1-substep の積分残渣で、次 substep に捨てられる**。**capture の真の delta = gripper_qd + cable_qd のみ** | route_executor.py:386-391 (v1 docstring が明言) / CC3+CC6 | ⭐**v1 の R2b「v1 の qd=0 は妥協」は誤読** → 訂正 |
| ⭐**F8** | **`eval_fk` は body_q **と** body_qd の両方を書く** (`outputs=[state.body_q, state.body_qd]`) ⇒ qd 保存 restore + eval_fk 1 回で **body_qd は stale にならない**。SolverMuJoCo は `update_data_interval=1` で毎 step `joint_q/joint_qd → qpos/qvel` を同期 | newton 1.2.1 articulation.py / newton_skill_env_base.py:1325/:1338 (CC3 検証) | **新規** (CC6 の H1「body_qd 分裂」仮説は REFUTED) |
| ⭐**F10** | ⭐**k-realizability + artifact-ID の罠 (本 turn 実測、CC2-1 由来)**: **正典 golden (sha 5f1c3f92 = RUN1_REFERENCE_V2、env が :621-624 で pin)** の G-phase frame 数 = `{0:1124, 1:600, 2:860, 3:3597, 4:620, 5:906}` ⇒ **k=1..5 全て実在**、f_k = 1124/1724/2584/6181/6801、**全境界で両手 grip=0.7407 (閉)**。⚠**別 artifact `p3_dod_cuda_demo_raw` (sha 509ad193) は G6=0 frames / k=4 が release 直後 (grip=開)** — CC2 はこれを読んで「k=5 不在」CRIT を出した (**REFUTED**)。⇒ **hazard class は実在**: v1 builder は frame の無い phase を**静かに skip** (:432-433)、`reset_to_phase` は bank 不在で**静かに no-op** (:3315-3317) ⇒ 非正典 recording なら**退化した bank が silent に出来る** | 本 turn 実測 | ⭐**新規** — R2 に provenance assert + missing-phase fail-loud を新設 |
| ⭐**F11** | ⭐**eq_active = THREAD 固有の第 2 channel、k≥3 で live (本 turn 実測、%9 C-α + ERRATUM-D)**: 記録の `pin_active` は **frame 2544-7706 で ON** ⇒ capture frame では **k=1,2 = OFF / k=3,4,5 = ON (eqid=27, body=55)**。clip-pin は INVARIANT #5 の**認可済み例外** ⇒ **fork で pin/eq の active flag を復元しないと cable/clip 関係が乖離**。記録は `pin_active`/`pin_eqid`/`pinned_body` を保持 → 復元可能 | 本 turn 実測 | ⭐**新規** — R3 に disposition 新設 |
| ⭐**F12** | ⭐**mjWarp Data は露出している (ERRATUM-D)**: SolverMuJoCo は `mjw_data`/`mj_data`/`_update_mjc_data` を持ち (`_data_is_mjwarp` 等)、`qacc_warmstart` / `act` / `eq_active` / `solver_niter` は **capture/restore できる** ⇒ 「経験 leg が唯一の guard」は over-generalization (%12 撤回) | 実測 + ERRATUM-D | ⭐**新規** — warmstart は 3 択を明示比較 (R3) |
| ⭐**F9** | **fork write-set の欠落は「クラス」であって個別 bug でない**: `_reset_worlds` が P0 から seed する per-world 派生状態を fork が書き換えない ⇒ **全数列挙して {fork-rewrite / reset OK} を分類**する必要 (R4) | CC4-F1/F6 + CC5-F1 + CC6-1/2 の**三重独立収束** | ⭐**新規** — v1 は 2 件 (body_q_prev/Dahl、しかも両方 vacuous) しか見ていなかった |

---

## §1. Scope + 境界

B3 = ①capture (lock-safe) ②bank v2 builder ③供給 API ④**fork write-set 全数** ⑤**単一の env-level fork 入口** ⑥guard 再条件付け ⑦DoD legs (再導出) ⑧LOUD。

**B3 に含まない:** per-world start-mix **policy** (どの world が k で始まるか) = B4 (B3 は入口と能力を建てる) / GPU per-k 正制御 bar = B7 / multi-cell bank = Rs 後決。

---

## §2. Conformance 行

### R1 — producer capture (⭐lock-safe 設計、spec §6.2-1)
| sub | 内容 | site | 証拠 |
|---|---|---|---|
| a | ⭐**locked 行ゼロ (F5)**: BankCapture の init も finalize も **`physics_step` (:503-565、lock 外) に閉じる** — module-global を env-var で遅延 init (初回 `physics_step` 呼出時) + `atexit` で finalize (run_route は `sys.exit` 終端 → SystemExit → atexit 発火)。**`run_route` (:1038-3110) は 1 行も触らない** | route_executor.py :503-565 のみ | **git diff で run_route span の変更行数 == 0 を機械 assert** |
| b | hook = recorder と同一 call site (post-step sample の隣、:561-562)。⚠**in-scope の control handle は `vbd_control` (:526)** — `control` は run_route ローカル (CC3-8) | 同 | unit |
| c | frame counter = 同 site で increment ⇒ recorder frame index と 1:1 (CC3 (b) が「physics_step が唯一の stepper」「recorder ctor は初回 physics_step より前」を実証)。両 flag ON 時は counter cross-assert | 同 | capture leg log |
| d | ⚠**self-disarm 対称性 (CC3-12)**: recorder は例外時に静かに自己 disarm する one-shot guard を持つ (route_demo_recorder.py:78-102) ⇒ BankCapture も**同型に wrap** し、disarm したら **loud** に記録 (capture-only run では cross-assert が効かないため) | 同 | unit |
| e | dump 内容 (全 frame): `joint_q [F,74]` / `joint_qd [F,73]` / `grip_target [F,4]` / `phase_id [F]` / meta (cadence / PHYSICS_STEPS_PER_RL / dt / cell env / route_executor.py sha / recording sha) | 同 | shape/meta unit |
| f | cell-parameterized: 既存 env-var (`CABLE_XY_OFFSET` / `CLIP_*`) + `BANK_CAPTURE=1` / `BANK_OUT` (byte-repro driver :156-169 と同形式) | 同 | leg runner |
| g | ⭐**read-only 証明**: `BANK_CAPTURE=1 ∧ DEMO_RECORD=1` の run の route_demo_raw.npz sha == **RUN1_REFERENCE_V2 (5f1c3f92…)** EXACT | — | **capture leg の一次 assert** |
| h | Rs-LOCKED producer `test_newton_clip_routing.py` 不触 (+ F5 により `run_route` も不触) | — | git diff file/行 list |

### R2 — bank v2 builder (spec §6.2-1、N8)
| sub | 内容 | 証拠 |
|---|---|---|
| a | `build_state_bank_v2_from_capture(capture, n_world, phases=(1..5))` → v1 全 key + **cable_q [46] + cable_qd [45] + bank_boundary_step + capture_frame + provenance** | unit |
| b | ⭐**qd の真の delta = gripper_qd + cable_qd (F7)**。arm_qd は**依然 0 を banked** (基板が毎 frame ゼロ化 = EXACT; capture 値を入れると R5 の qvel 比較の意味が壊れる) — v1 docstring :386-391 の判断を**維持**し、その根拠を comment に残す | unit: gripper/cable qd の非零 assert (arm は対象外) |
| c | chunk 整列: `t_k = ceil(f_k / cadence)`、**capture_frame = 10·t_k − 1** (F3)。**実測値 (CC3 検証済): f_k = 1124/1724/2584/6181/6801 → t_k = 113/173/259/619/681 → capture_frame = 1129/1729/2589/6189/6809**、全 k で `G(phase[capture_frame]) == k` ∧ `G(phase[10·t_k]) == k` | unit: 導出値 pin |
| d | ⭐**edge guard (CC4-F9)**: `f_k % cadence == 0` の cell では capture_frame が phase k−1 に落ちる → **`assert G(phase[capture_frame]) == k`** (multi-cell 前方互換) | unit |
| e | `0 not in phases` 維持 (**k0 禁止不変量**) | unit |
| f | ⭐**自己整合 cross-check**: banked_v2 の **q** が recording `arm_q[capture_frame]` と **EXACT 一致** (74 列全数) | unit (最強の builder 検証) |
| g | ⭐**qd の独立検算 = FD validator (CC4-F4、0-GPU)**: `qd_fd[f] = (q_rec[f+1] − q_rec[f−1]) / (2·dt)`、dt = 1/480 (F2 実測)。**cable + gripper** 座標群で captured qd と相対一致 (bar = 群ごと ≤20%、FD ≠ solver qd ゆえ緩め)。arm 群は**不一致が正**(F7、documented)。⚠**spec :140 が却下したのは FD による「構築」であって「検算」ではない** — 本 leg は検算のみ (§6) | **L2 (唯一 capture の存在理由を検証する leg)** |
| h | v1 builder 残置 (capture 不在時)、v2 は capture npz が cfg にある時のみ | grep + unit |
| i | ⭐**bank-load 時の width assert (CC6-4)**: capture joint_q 幅 == 74 == env の per-world 座標幅 / arm 28 / cable 46 == 7 + (cable_bodies_per_world − 1) / cable_bodies_per_world == 40 (producer と一致)。`route_c2_scene` の clip が座標を持てば loud FAIL | unit |
| j | ⭐**origin-sensitivity の明示 (CC3-11)**: cable free-root は**絶対 7 座標** ⇒ 全 world tiling は `scene.replicate(spacing=(0,0,0))` (newton_skill_env_base.py:1883) に依存。**cable_q は初の origin-sensitive banked 量** → spacing 非零なら loud FAIL する assert | unit |
| ⭐k | ⭐**provenance + missing-phase fail-loud (F10)**: (i) bank v2 build 前に **capture/recording の sha == RUN1_REFERENCE_V2** を assert (env は :621-624 で既に recording 側を pin — capture 側にも同 pin) (ii) **要求 phase に frame が無ければ raise** (v1 の silent `continue` :432-433 を踏襲しない) (iii) `reset_to_phase` の silent no-op 経路 (:3315-3317) は R6a の再条件付けで塞ぐ。⚠**非正典 recording は退化 bank を silent に作る** (CC2 が別 artifact で実証: sha 509ad193 は G6=0 frames) | unit: 欠落 phase → raise / sha 不一致 → raise |

### R3 — 供給 API + env-level cable restore
| sub | 内容 | 証拠 |
|---|---|---|
| a | executor `get_cable_bank(k)` (供給のみ、副作用ゼロ)。⭐**RouteInterfaceV1 に宣言** + 既定 `return None` ⇒ stub は継承して R5 の fail-loud に落ちる (AttributeError でなく) (CC5-7) | unit |
| b | ⭐**新 twin を作らない (CC5-5)**: 既存 `seed_cable_joint_state` (newton_skill_env_base.py:1070) に **`cable_qd: np.ndarray | None = None` kwarg を追加** (None = 現行のゼロ化 = byte-identical)。根拠: 既存 fn は既に root7/seg_angles 分解・45 幅 qd slice・per-world cable_joints・eval_fk を持ち、**差分は 1 行**。AGENTS.md「Reuse gate」+ repo の静的監査 (`scripts/s4b_reset_scoping_audit.py` / `sc3_body_q_prev_guard_audit.py`) が cable 書込面を**名前で列挙**しており、twin は監査不可視になる | **blast-radius grep (双方向)** + unit |
| c | ⭐**座標解決は必ず `model.joint_q_start` 経由 (F6)** — `_jws[w]+28` を座標基点として直書きしない (w≥1 が 6·w ずれる) | unit: **2-world、world-1 のみ fork → world-0 座標 byte 不変 + world-1 が正配置** |
| d | ⭐**eval_fk は fork 書込の後に無条件 1 回 (CC6-8)** — v1-fallback (bank 不在) 経路でも obs が P0 body_q と phase-k joint_q の混成にならない | unit |
| e | env `_restore_cable_bank(world_ids, k)` = 供給を受けて適用 (RULING: executor 供給 / env 適用) | unit |
| f | ⭐**DR×curriculum guard (CC5-10)**: `_restore_cable_bank` は `dr_xy` と `k` の両方を見る唯一の site ⇒ **DR-offset world を k>0 に fork したら loud** (B4 が DR を配線する前に guard を置く) | unit |
| ⭐g | ⭐**eq_active / clip-pin の fork disposition (F11、ERRATUM-D 必須項)**: 実測で **k=3,4,5 の capture frame は pin_active=1 (eqid=27, body=55)** / k=1,2 は 0。⇒ **fork 時に pin の active flag + eqid + pinned_body を記録値へ復元**する (記録が保持)。clip-pin は INVARIANT #5 の認可例外 (`log.md:6534`) ゆえ**新規 trick ではない**。4-bar gripper linkage の eq も同 channel — **capture に `eq_active` 全体を含め、restore で書き戻す**のが単一規則 | unit: k=3 fork 後の eq_active/pin が記録値と一致 |
| ⭐h | ⭐**mjData warm-start の disposition (F12、ERRATUM-D の 3 択)**: (a) **capture/restore する** (mjw_data 露出ゆえ可能) (b) 両側 zero (producer 側も fork 側も warmstart をゼロ化して対称化) (c) 非 restore + drift-bounded 実証。**当方案 = (b) 両側 zero を既定、(a) を fallback** — 理由: warmstart は収束の初期推定にすぎず、両側ゼロなら**再現性が構造的に保証**され capture schema が薄く済む。(c) は「盲目でないこと」を証明できない。**採否 = §5 ask B4 (%12 裁定)**。いずれの択でも **K-step growth leg (L5) が経験的 falsifier** | L5 + unit |

### R4 — ⭐fork write-set の全数分類 (F9、三重収束)
`_reset_worlds` (:1015-1087) が per-world で書く**全 field** を列挙し、fork 時の扱いを分類する。**「この 2 件を直す」ではなく「クラスを閉じる」** — 網羅を unit で強制。

| # | field | site | fork disposition |
|---|---|---|---|
| 1 | body_q / body_qd / prev | :1018-1026 | **derived** — fork 後の eval_fk (R3d) が両方書く (F8)。prev = None (ERRATUM-B) |
| 2 | ⭐`_per_world_fk_jq[w]` | :1027 | ⭐**FORK-REWRITE** — IK warm-start (:1143) ∧ **駆動補間の START** (:1215 `old_fk_jq` → `jq_interp = old + (tgt−old)·t`) ∧ obs 源 (:1364)。**P0 のままだと IK 駆動の初 frame で arm が P0 へ 90% 戻る (実測 373-444mm)** = fork 破壊。⚠FF mode は毎 frame 自己修復するため**既存 leg 全てが構造的に不可視** |
| 3 | `_ee_target_right/left[w]` | :1028-1029 | reset OK (駆動が毎 step 上書き :1166-1167; 読出 site なし — grep 証拠を pin) |
| 4 | `_prev_clamp_*_quat` / `_prev_seg_*_quat` | :1033-1037 | **要 disposition** (quat 連続性 tracker; fork 後の実 quat から再 seed が素直) |
| 5 | ⭐`_g_latched[w]` | :1039 | ⭐**FORK-REWRITE** = G1..Gk pre-set。⚠**理由の訂正 (CC3-10)**: pre-set なしだと「永久 unlatch」だけでなく**述語が成立する fork では G1..Gk を再 latch して bonus を再取得**する (free reward)。⇒ unit は **fork 直後の reward に phase bonus が乗らない**ことも assert |
| 6 | `_g6_sustain` / `_contact_loss_count` | :1040-1041 | reset OK (contact-loss counter=0 ⇒ debounce 8 により step 1 で drop 不可 = 安全、と明記) |
| 7 | `_last_executed_residual` / `_last_projection_mode` / `_last_ik_resid` | :1042-1044 | reset OK (telemetry) |
| 8 | ⭐`_phase_entry_step` / `_prev_phase_id` | :1045-1046 | ⭐**FORK-REWRITE** (fork の route_t / phase 基準 — obs[50] が fork 直後に壊れない) |
| 9 | `episode_length_buf[w] = 0` | :1047 | reset OK (spec §6.2-4「episode 時計は handover 起点」) |
| 10 | ⭐`route_t[w]` | :1048 | ⭐**FORK-REWRITE** := `bank_boundary[k]` (bank に無ければ **fail-loud**) |
| 11 | `_suppressed_drop_count` | :1051 | reset OK |
| 12 | HOLD sync clear | :1052-1054 | reset OK — fork 後は **MARCH / hold_count=0 / arming 生** が正 (CC5-8 が「正しいが未記載」と指摘) → R5 の post-fork assert に加える |
| 13 | arm/gripper joint_q/qd + grip_target | :1063-1072 | **FORK-REWRITE** = `apply_banked_restore` (⚠ **reseed_grip_open (:1072) より後**でないと banked CLOSED target が OPEN で潰れる) |
| 14 | ⭐cable joint_q/qd | :1075-1079 | ⭐**FORK-REWRITE** = banked cable q/qd (R3b/c) |
| 15 | ⭐`_target_seg_indices_{r,l}[w]` | :1081-1085 | ⭐**FORK-REWRITE** — P0 由来の ±5 seg 窓。**実測: 全 k で少なくとも片腕の窓が実把持 seg を含まない (6-13 link ずれ)** ⇒ obs[16:19] と p4 (`r_reach`) が別の cable を指し、**G4 が成立しない/報酬が汚染**。**cable restore 後に再計算** |
| 16 | Dahl | :1086 | **no-op** (ERRATUM-B / 本基板に不在) |
| 17 | ⭐**NEW `_start_phase[w]`** | — | ⭐**新設** (CC5-6): B3 が**格納**、B5 が export、B4 が選択 (charter DAG では B5 が B4 に先行するため、B3 が作らないと B5 が export 対象を持たない) |

**網羅 unit:** `_reset_worlds` の per-world 書込を**列挙**し、各々が {fork-rewrite 済 / reset OK と宣言済} のいずれかであることを assert (新 field が増えたら FAIL する構造)。

### R5 — ⭐単一の env-level fork 入口 (CC4-F5 / CC5-F3 / CC3-3)
| sub | 内容 | 証拠 |
|---|---|---|
| a | **`NewtonRouteEnv._fork_worlds_to_phase(k, world_ids)`** = R3/R4 の順序全体を包む**唯一の fork 経路**。現 code は fork 呼出が `reset_to_phase(0, ...)` の 2 箇所 (:1675 / :1707) に hardcode され **k>0 は到達不能** ⇒ 入口が無いと **leg が fork 手順を自作 = 偽検証構造** (B4 が別順序で配線しても B3 の leg は全部 PASS してしまう) | unit + 全 leg が本 API 経由 |
| b | 順序 (この API の内部): `_reset_worlds(world_ids)` → `reset_to_phase(k, world_ids)` → `_restore_cable_bank(world_ids, k)` → **eval_fk** → route_t := boundary → latch pre-set → 派生状態再計算 (R4 #2/#4/#8/#15) → `_start_phase` → **post-fork assert** | unit: 順序反転で FAIL |
| c | ⭐**post-fork assert (runtime、CC6-3)**: (i) route_t == boundary (ii) latch prefix == k (iii) **arm + 全 16 gripper 座標 + grip_target** の L∞ == 0 vs banked (**cable だけでは、arm が silent に未復元でも 3 つとも PASS する**) (iv) cable joint_q L∞ == 0 (v) seg 窓が実把持 seg を含む (vi) `_per_world_fk_jq` == 復元 row (vii) sync = MARCH/0 | unit |
| d | `reset()` の `route_t[:] = 0` (:1674) は k=0 経路のみ ⇒ fork 経路と競合しないことを明記 (CC5-F3 の clobber 指摘) | unit |

### R6 — guard は**削除でなく再条件付け** (CC5-F2)
| sub | 内容 | 証拠 |
|---|---|---|
| a | ⭐`forbid_banked_fork` を**削除しない**: `reset_to_phase(k≥1)` は **cable を持つ v2 bank が k に存在しない限り raise** (現 code は missing bank で **silent no-op** (:3316-3317) → **v1 bank (cable なし) のまま arm だけ mid-route 復元 = guard が防いでいた mismatched state に silent 回帰**)。**raise は joint 書込より前** | unit |
| b | ctor 引数の血縁: **第 2 の caller が実在** (`test_routeexec_writesite.py:245` の `_build_executor` 署名 + :271) — v1 の「呼出は env :649 の 1 箇所のみ」は**誤り** (CC3-6/CC4-F8) | grep pin |
| c | writesite `test_forbid_banked_fork` (:427) は**二腕化**: 「v2 bank あり → k≥1 成功」∧「v2 bank なし → 依然 raise」。現 test の :437-439 (「bank 無し → raise しない」assert) の disposition も明記 | unit |
| d | k=0 は依然 no-op (k0 禁止不変量と非衝突) | unit |

### R7 — ⭐DoD legs (全面再導出、ERRATUM-C/-D + %9 C-α)
**v1 の bar は二重の流用ミス**: (i) 10.407mm は **k=0 rollout の HOLD 警報域における開ループ発散包絡の peak** (CC4 実測) — restore 域の期待値は 0.02-0.15mm ⇒ **cable_qd を全ゼロにした偽 bank でも 3.4-44 倍余裕で PASS = DoD が v2 と v1 を区別できない** (ii) spec の 1mm/1mm/s も **FORK-1 致死 seed (frame0 mean 0.0200 / max 0.1469mm 実測) の 6.8-50 倍緩く、防ぐべき failure class に盲目** (%9 C-α / ERRATUM-D)。

**⭐bar 原則 (3 本立て、channel 分離):**
1. **restore-exactness (書込)**: joint_q/joint_qd L∞ **== 0** vs banked
2. **task-space fidelity (channel 分離)**: **cable = FORK-1 seed scale ≤0.15mm 級** / **arm・gripper = ≤1mm** — 1 本の 1mm bar で cable を測ると FORK-1 同型の restore を PASS させる
3. **HOLD-arming sanity**: 走行 metric (route_t = t_k、10-frame 先参照) ≤ 10.407mm = spec §6.2 の**原意**「fork が HOLD を即発火させない」— この用途に**限定**

| leg | 内容 | bar | 実行 |
|---|---|---|---|
| **L1 capture** (GPU 1 run) | 抽出 twin を `BANK_CAPTURE=1 DEMO_RECORD=1` で x0_y0 走行 | ①route_demo_raw sha == RUN1_REFERENCE_V2 **EXACT** (read-only 証明) ②capture npz shape/meta ③frame counter == recorder len ④**git diff の run_route span 変更行 == 0** (F5) | producer 1 走 |
| ⭐**L2 FD qd 検算** (**0-GPU**) | 記録 q から `qd_fd = (q[f+1]−q[f−1])/(2dt)` (dt=1/480) を作り capture の joint_qd と照合 | **cable + gripper 群で相対一致 ≤20%** (capture frame の \|qd_fd\| = 0.036-1.246 rad/s ≫ FD 打切り誤差)。arm 群は不一致が正 (F7)。⚠**明確化 D (%12)**: FD は **consistency check (buffer/置換/転置/scale の判別)** であって exactness 証明ではない — その旨を leg に明記 | CPU |
| ⭐**L3 null-bank negative control** (**ERRATUM-C の DoD 必須項**) | `cable_qd ≡ 0` の**偽 bank** を作って同じ fidelity/growth leg にかける | ⭐**必ず FAIL すること** — PASS したら bar に判別力が無い証明。**判別力の存在を DoD に組み込む**（CC4-F3 の根本対策） | CPU + GPU (L5 と同 harness) |
| **L4 restore-exact + 配置** | fork → joint_q/joint_qd を banked と L∞ 比較 + per-world 配置 | **L∞ == 0** ∧ 2-world で world-0 byte 不変 (座標は `model.joint_q_start` 解決、F6) | unit (infra = §5 ask B2) |
| ⭐**L5 K-step divergence-GROWTH leg** (GPU、⭐**IK/residual mode 必須 — FF 禁止 [明確化 E]**) | fork (world_count=5、各 world を別 k) → **residual≡0 で K=20-50 step roll** → producer の同境界 trajectory と div_grip 系列を比較 (**leg8 の較正手法を再利用**) | ⭐**PASS = (i) HOLD 発火 0 (ii) div が健全域 band 内 (iii) ⭐ramp 不在** — **FORK-1 の signature は step-1 の大きさでなく *growth*** (%9 C-α)。加えて (iv) restore 直後の channel 分離 bar (cable ≤0.15mm / arm・gripper ≤1mm; div は **route_t = t_k−1** で呼ぶ [CC3-2、比較 frame = capture_frame EXACT]) (v) HOLD-arming sanity ≤10.407 (vi) **arm が P0 に戻らない** (vii) done == False 全 k (viii) held_seg が記録追従 (ix) **視覚 leg** (motion-bearing、charter §4-3) or loud 理由 | 1 env build、cuda:0 数秒-数分 |
| ⭐**L6 post-fork assert leg** | fork 入口の runtime assert 7 項 (R5c) を全 k で発火確認 | 全 PASS ∧ **eq_active/pin が記録値と一致** (F11、k=3,4,5 で pin ON) | L5 と同 run |
| **L7 表面適合** | env 側 → ⑨a′ + DoD⑤⑥⑩ + cablediag (311f18cb9b) / executor 側 → producer 5-cell (ca33d1e1a0) | 全 EXACT | run_legs.sh |
| — | comparator = full-dict-diff − 変動 key / runner exit-gating + 事前 rm / stdout run 時 pin | — | B1/B2 carry |
| — | **runtime settle 禁止 (spec :140 N8、CC2-3)**: restore 経路に solver/settle step が無いことを grep leg で pin | 0 hit | grep |

**GPU 予算:** L7 = 4 (env) + 5-cell (producer) / L1 = 1 / L5+L6 = 1-2 ⇒ **~11-13 leg**。

### R8 — 変更 file + LOC (charter est 150-300 / hard cap 800)
| file | 内容 | est |
|---|---|---|
| envs/route_executor.py | BankCapture (physics_step 内、**lock 外**) / bank v2 builder / get_cable_bank / guard 再条件付け | ~170-210 |
| envs/newton_route_env.py | `_fork_worlds_to_phase` + write-set 全数 + post-fork assert + bank v2 分岐 | ~110-150 |
| envs/newton_skill_env_base.py | `seed_cable_joint_state` に `cable_qd` kwarg (additive、1 行 + doc) | ~10-15 |
| envs/route_env_config.py | `get_cable_bank` を interface に宣言 (既定 None) | ~10 |
| scripts/test_routeexec_state_bank.py | U1-U4 + FD validator | ~120-160 |
| scripts/test_routeexec_writesite.py | U5-U8 + guard 二腕化 | ~80-110 |
| eval_runs/.../w1_b3_dod_legs/ | capture runner + L1/L2/L4/L5 + run_legs.sh | — |

⚠**見積 delta (%12 A2 条件)**: source ~500-655 (charter est 150-300)。**hard cap 800 内**。増分の主因 = 5体が要求した検証機構 (write-set 全数 / fork 入口 / post-fork assert / FD validator)。**実 diff が ~600 に迫れば分割を再提起**する。

### R9 — LOUD + carries
- **DR×curriculum 相互排他** (spec §6.2-5): bank = x0_y0 単一 cell ⇒ phase-k 開始は DR 被覆ゼロ。**機械 guard を R3f に置く** (宣言だけにしない)。
- **Layer-B re-BASELINE** (spec §4.1 :77): bank v2 ON の挙動変更を Rs-visible に宣言。
- **mjData warm-start (`qacc_warmstart`)** = 本基板の唯一の未 reset hidden state (CC3-4/CC6-7)。**既存 done-reset も同じ**ゆえ B3 新規 bug ではないが、**M10 の guard は L5 (1-step + 保持 probe) が唯一**と明記。
- B4 へ: start-mix policy / recenter 実配線 / DR guard の解除条件。B5 へ: `_start_phase` の export。B7 へ: per-k 正制御 bar / bank-G3 摂動 leg / multi-cell option。

---

## §3. 約束 unit roster (close 時に実在照合)

| id | 対象 | file::test |
|---|---|---|
| U1 | capture artifact (shape/meta/counter/disarm) | test_routeexec_state_bank.py::test_capture_artifact |
| U2 | bank v2 builder (整列・edge guard・k0・q EXACT・width/origin assert) | ::test_bank_v2_builder |
| U3 | **FD qd validator** | ::test_bank_v2_qd_fd_validator |
| U4 | restore-exact + per-world 配置 (joint_q_start 解決) | ::test_bank_v2_restore_world_slice |
| U5 | **fork write-set 網羅** (`_reset_worlds` の per-world 書込を列挙 → 全て分類済) | test_routeexec_writesite.py::test_fork_write_set_coverage |
| U6 | fork 入口の順序 + post-fork assert (7 項) | ::test_fork_entry_ordering |
| U7 | guard 二腕化 (v2 bank あり → 成功 / なし → raise) | ::test_banked_fork_guard |
| U8 | latch pre-set = bonus 再取得なし | ::test_fork_latch_no_bonus |
| L1-L6 | 上記 legs | w1_b3_dod_legs/ |

## §4. 5体 fold 対応表

| finding | sev | fold 先 |
|---|---|---|
| CC3-1 **run_route が Rs-LOCKED** | **CRIT** | F5 + R1a (lock 外設計、locked 行 0 を機械 assert) |
| CC4-F1 / CC6-1 `_per_world_fk_jq` | **CRIT** | F9 + R4 #2 + L5 (IK mode 必須) |
| CC4-F3 / CC6-6 band 流用 (v2≡v1 判別不能) | **CRIT** | R7 全面再導出 (L4 ≤0.5mm / L5 ≤1mm、10.407 は HOLD-arming sanity に降格) |
| CC4-F4 qd の ground truth ゼロ | **CRIT** | R2g + **L2 FD validator** |
| CC5-F1 / CC4-F6 / CC6-2 `_target_seg_indices` | **CRIT×3 収束** | R4 #15 |
| CC4-F2 / CC6-5 整合判別が vacuous | CRIT/MED | F3 (解析的強制に格上げ、leg は telemetry) |
| CC5-F2 guard 削除 → silent 回帰 | HIGH | R6a (再条件付け) |
| CC4-F5 / CC5-F3 / CC3-3 fork 入口不在 | HIGH×3 | **R5 新設** |
| CC5-F4 drop-arming の根拠誤り + 引用 stale | HIGH | R4 #6 + L5 (done==False 全 k) + 引用訂正 |
| CC5-F5 twin でなく kwarg | HIGH | R3b |
| CC6-3 post-fork assert が cable のみ | HIGH | R5c (arm+gripper+grip_target) |
| CC6-4 index-space の罠 | HIGH | F6 + R3c |
| CC3-5 U3/U4/U7 の CPU infra 不在 | HIGH | **§5 ask B2** |
| CC5-F6 `_start_phase` の生産者不在 | MED | R4 #17 |
| CC5-F7 `get_cable_bank` を interface に | MED | R3a |
| CC3-7 / CC6-10 arm qd は EXACT-as-zero | MED | F7 + R2b |
| CC6-8 eval_fk 無条件化 | MED | R3d |
| CC3-8 hook の handle は `vbd_control` | MED | R1b |
| CC5-F10 DR×curriculum の機械 guard | MED | R3f |
| CC4-F9 `f_k % 10 == 0` edge | MED | R2d |
| CC4-F10 視覚 leg | MED | L5④ |
| CC3-11 origin-sensitivity | LOW | R2j |
| CC3-12 self-disarm 対称性 | LOW | R1d |
| CC3-9 引用 slip ×4 | LOW | 本 v2 で全訂正 (:1705-1706 / :1496-1512 / :1542-1552 / :372-444) |
| CC3-10 latch 再取得 bonus | LOW | R4 #5 + U8 |
| CC6-9 dead work (FK 2 回) | LOW | 実装で 1 回化 (P0 seed を fork world では skip) |
| CC6 H1/H2/H3 | REFUTED | 記録のみ (再審しない) |

## §5. asks (%12 へ)

- ⭐**B1 (lock)**: R1a の「capture を `physics_step` (lock 外) に閉じ、`run_route` は 1 行も触らない」設計で CONCUR か。**v1 のまま build していれば Rs-LOCKED 関数を無断編集していた** — 5体が build 前に捕捉。Rs waiver は**不要**と判断 (locked 行ゼロ) だが、lock 抵触の可能性がある設計を通した事実は loud に記録する。
- ⭐**B2 (CPU 検証 infra)**: U4/U5/U6 は `newton.Model` + `eval_fk` を要し、既存の CPU mock harness (array のみ mock) では構築不能 (CC3-5)。選択肢: (a) model-stub + eval_fk monkeypatch (b) joint 書込の純粋核を抽出して unit 化 (c) GPU leg に移す。**当方推奨 = (b) + (c) 併用** (純粋核 = 座標解決と書込 → CPU unit / FK と物理 = GPU leg)。
- ⭐**B3 (分割) = 当方から正式提起 (%12 の条件付き推奨を受けて)**: 見積が **~600-750** に達した (5体 + ERRATUM-C/-D が要求した検証機構 = write-set 全数 / fork 入口 / post-fork assert 7 項 / FD 検算 / null-bank 対照 / eq_active / warmstart / K-step growth leg)。⇒ **§7 の B3a / B3b 分割を推奨**。
- ⭐**B4 (warmstart の択)**: R3h の 3 択 — **当方推奨 = (b) 両側 zero を既定・(a) capture を fallback**。理由: warmstart は収束の初期推定にすぎず、両側ゼロなら再現性が構造的に保証され capture schema が薄い。(c) 非 restore は「盲目でないこと」を証明できない。
- **B5 (5体 の再走)**: 分割時、5体 は**再走不要**と判断 (panel は capture+restore の**和集合**を review 済で、CRIT は両半に跨がる)。B3a/B3b それぞれで [RULE-CHECK] → build → legs → 3-leg verify を回す。この読みの CONCUR 依頼。

## §7. ⭐分割提案 — B3a / B3b (%12 の「~600 超なら分割」条件を充足)

| chunk | scope | deliverable | files | est |
|---|---|---|---|---|
| **B3a** (producer + offline) | R1 capture (lock 外) / R2 bank v2 builder (整列・provenance・fail-loud・width/origin) / L1 capture leg / **L2 FD 検算** / **L3 null-bank negative control (offline 半)** | **検証済みの bank v2 artifact** (env 変更ゼロ) | route_executor.py (capture + builder) / test_routeexec_state_bank.py / w1_b3a_dod_legs/ | ~300-380 |
| **B3b** (env fork) | R3 restore (kwarg / joint_q_start / eq_active / warmstart) / R4 write-set 全数 / R5 **順序付き単一 fork entry** + post-fork assert / R6 guard 再条件付け / **L5 K-step growth leg (IK mode)** / L6 / L7 | **fork できる env** (B3a の artifact に依存) | newton_route_env.py / newton_skill_env_base.py / route_env_config.py / route_executor.py (guard + get_cable_bank) / test_routeexec_writesite.py / w1_b3b_dod_legs/ | ~300-370 |

**分割の seam が clean な理由:** B3a は **env を一切触らない** (capture は producer 側、builder は offline) ⇒ 表面適合 leg は producer 5-cell のみで足りる。B3b は B3a の artifact を消費するだけ ⇒ env 側 leg に集中できる。**lock risk (F5) は B3a に閉じる**ので、そこに gate を集中できる。

## §6. spec 却下済 代替の記録

**FD による qd の「構築」= spec :140 が却下済 → 再審しない。** 本 v2 の L2 は **capture 済 qd の「検算」** であり構築ではない (記録の joint_q は既に存在する独立情報源 = F1)。この読みに異論があれば **STOP → ERRATUM 依頼**とする。
