# W1 B3 Conformance Table — bank v2 (producer capture + env-level cable restore)

**Doc:** W1_B3_CONFORMANCE_COORD_20260713.md **v3** (v1 22:0x → 5体 fold v2 22:5x → **v3 = B3a build 中の自己捕捉 DEFECT-1/-2 + %12 ERRATUM-F/F-5/F-6 + %9 3-lens を fold**, 2026-07-14 03:0x)
**Author:** %11 (COORD, w2:p3, builder leg) — 2026-07-13/14 (date-THEN-write)
**Node:** T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild / chunk B3
**Design SSOT:** `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.8.1 §6.2 :135-147 + §4.1 :74-78 + §8 + §9 + **§14 ERRATUM-B (955ff0648f)**
**Charter:** `W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md` v0.2 B3 行 :36 + ERRATUM-1/2/3
**[L-TRIAGE]:** L3 (diff keyword + ≥5 files)。直交 [DESIGN-GATE] = cite 充足 (reward/成功条件 不変)。
**%12 裁定 (22:15、ERRATUM-B 955ff0648f):** A1 = 「state はそれが対応する記録 frame と比較する」規則 / A2 = 1 chunk 続行 (見積 delta 記録・~600 で分割) / **A3 = MOOT (Dahl/body_q_prev は本基板に不在 → 非項目、hidden-state guard は 1-step leg に昇格)**。

> ⚠⭐ **B3a-F1 — commit provenance の訂正 (%9 発見、当方 on-disk 確認済、2026-07-14 04:3x)。records-must-match-fact ゆえ loud に残す。**
> **B3a の source 730 行 (`route_executor.py` +570 / `test_routeexec_state_bank.py` +160−3) は `a00a0a97f8` に入っていない。実際の landing = `575069abe5` (%12 の BLOCKED_FOR_USER commit、03:43:50)。**
> - `a00a0a97f8` (題「W1-B3a: capture producer state …」、当方が B3a 本体と報告) の中身 = **conformance doc +20 行のみ、source ゼロ**。⇒ **当方の commit message は、その commit に入っていない source を主張している。**
> - 経緯: 当方は「defect 込みで bank しない」方針で source を意図的に未 commit のまま保持 → staged 済の index を **%12 の非 explicit-path commit が sweep** → 当方のその後の commit には差分が残っていなかった。
> - ✅ **成果物は無害**: legs 完了 **03:38:13** < sweep **03:43:50**、working tree == HEAD、DEFECT-1 fix も HEAD に在る (`route_executor.py:851` = `use_mujoco_cpu` で buffer 選択、fallback 無し) ⇒ **commit されている code は全 leg PASS した最終 code そのもの**。
> - ⛔ **history rewrite はしない** (%9/%12 一致: 不要かつ有害)。provenance の正本 = node state.md の %12 記載 (`e458bf9b9e`) + 本 note。
> - **過失の切り分け (正確に、records-must-match-fact)**:
>   - **(a) sweep 自体 = %12** — path 制限なしの `git commit` が当方の stage 済 index を巻き込んだ (%12 自認: 「貴の『未 commit を維持』判断は正しく、巻き込んだのは私」)。
>   - ⚠**(b) 当方 (%11) の過失 = 別項** — **commit 後にその commit の中身を検証せずに「B3a 本体」と報告した**。`git show --stat a00a0a97f8` を打っていれば **source ゼロ**に即気付けた。⇒ **事実と一致しない主張を当方が発信した。**
> - ⭐**教訓 (当方)**: `feedback-narrative-signal-not-established-fact-verify-on-disk` は**他者の narrative だけでなく、自分自身の commit にも適用される**。**自分が commit した内容も、主張する前に on-disk で検証せよ。** — 皮肉なことに、本 chunk 全体が「計器が生きているか先に測れ」の arc でありながら、**自分の commit という計器を測っていなかった。**

**5体 verdict (全員着弾):** CC2 REVISE (CRIT1 = **artifact 取り違え → REFUTED**、他 MED/LOW 有効) / CC3 **CRIT (Rs-LOCKED)** / CC4 CRIT×4 / CC5 CRIT×1 / CC6 CRIT×2。**CC1 DECIDE = 全 finding ACCEPT (CC2-1/2 は実測で REFUTE、ただし hazard class は採用)**。
**%12 ERRATUM 群 (本 v2.1 の SSOT):** §14 ERRATUM-B (955ff0648f、Dahl/body_q_prev = 非項目) / **§15 ERRATUM-C (aae9f78722、bar 2 本分離 + null-bank negative control を DoD 化)** / **§16 ERRATUM-D (a07b03ed69、mjWarp Data 露出 → warmstart は capture/restore 可能; 1mm bar は FORK-1 致死 seed の 6.8-50× 緩 → cable channel 再較正 + K-step growth leg; eq_active disposition 必須)** + 明確化 D (FD = consistency check) / E (FF mode leg は arm bank を構造的に検証不能)。
**%9 C-α (22:23):** hidden state は消えたのでなく**移動** (mjWarp Data) / bar は FORK-1 seed より緩い / 1-step → **K-step divergence-growth leg** へ昇格。

---

### ⭐v3 追補 — B3a build 中に自己捕捉した DEFECT 2 件 + それに伴う %12/%9 裁定 (2026-07-14 00:0x-02:5x)

**契機:** B3a の leg 一式で **LEG3 のみ FAIL** (k=2/3)。bar を緩めず root-cause に降りた結果、**実 defect 2 件**が出た (1 件は私の build、1 件は私の leg)。**bar 緩和ではなく fix-first** (%12「両方とも正しい判断」)。

| # | defect | class | 根拠 | 措置 |
|---|---|---|---|---|
| ⭐**DEFECT-1** | **capture が dead mirror (`mjw_data`) を読んでいた** ⇒ bank の hidden-state channel が **no-op** (`qacc_warmstart` 恒常 0 / `eq_active` 変動ゼロ)。k=3/4/5 の fork は **pin OFF** を restore する | ⚠**FORK-1 class (silent state mismatch)** | **F13** (§0) | `_mj_hidden_state` を **`use_mujoco_cpu` で integrated buffer 選択**に修正 (fallback 無し = 同じ silent 誤読の再来を禁ずる) + **leg6 新設** + builder に **fail-loud guard** |
| ⭐**DEFECT-2** | **leg3 の bar が構造的に不適** — (i) k=2/3 の FAIL は data 誤りでなく**計器の帯域不足** (κ=|Δqd|/|qd| が k=2:0.92 / k=3:1.81、`SIM_SUBSTEPS=10` ゆえ位置差分は必ず frame 平均 ⇒ central/backward/trapezoid/3-tap の **4 変種が同時に落ちる**) (ii) spec が名指しする **「wrong substep」hazard は κ/10 ≈ 1.6% しか動かず 20% bar で原理的に検出不能** (iii) **scale に盲目** | ⚠**感度不足 / SN 交絡** (計器が対象を測れない class) | 実測 (§0 F2 / route_executor.py:617-618/:827) | **2-param 回帰へ置換** (R7 参照) + **identifiability 表 (8 摂動)** |

**%12 ERRATUM 群 (v3 の SSOT、上記を受けて発行):**
- ⭐**§18 ERRATUM-F (f1d7d36609)** — メタ教訓: **source inspection (grep/inspect) では liveness を discharge できない。設定 backend 上の runtime 測定でのみ discharge せよ。**「verifier 2 名が同時に踏んだ = grep 由来の確信は特に危険」。**F12 の buffer 同定を撤回** (結論「capture 可能」は不変)。
- ⭐**§18 F-5 (666d22e69b)** — **(1) D-1 の bar を差替え**: 「warmstart が非ゼロか」は**再分類の bar として誤り** (E-5 (i) 違反 — 存在の有無は決定に直結しない)。正しい問い = **「restore vs zero で軌道が FORK-1 seed scale (0.147mm) 動くか」= L5a (FF) 上の A/B** ⇒ **B3b へ carry**。⭐**regret 非対称ゆえ (a) capture+restore を既定維持**: bank して inert = nv floats の無駄 / **bank せず live = k=3/4/5 で silent な FORK-1-class mismatch — DEFECT-1 がその第 2 の失敗が実在かつ silent だと実証した**。warmstart は Dahl/body_q_prev の *属性不在* と違い**実在する live field** ゆえ zeros を bank しても無害。**(2) eq_active は D-1 の対象外 = 構造的必須** (INVARIANT #5 の唯一の認可例外、k=3/4/5 の fork 境界はまさに clip が cable を保持している所 ⇒ pin OFF の fork は「数値的に微妙」でなく**物理的に誤った state**)。**(4)** DEFECT-2 の「scale 誤りは大域的ゆえ gripper が担う」は**単一 contiguous copy が前提** ⇒ cable の g も telemetry 記録。
- ⭐**§18 F-6 (8e349655fc、F-5 (3) の bool assert を supersede)** — ⭐**hidden state は「backend」でなく「model layout」で index される。** `add_c2_clip=True` は C2 clip の body/shape を追加する (newton_skill_env_base.py:1494-1517) ⇒ **C2 build と no-C2 build で layout が違う**。pin は **eqid=27 / body=55 = index** で記録されるので layout が 1 つずれれば**別の constraint を活性化 = 物理的に誤った state を silent に作る** ⇒ **backend flip より起きやすく、bool assert は素通りさせる**。⇒ **provenance = (backend_id, layout_hash) の fail-loud assert** + ⭐**eq は index でなく identity/name で解決して restore** (assert = 検出の floor / identity 解決 = 壊れない robust form、**両方**要る)。

**%9 3-lens (23:57、台帳 §5.15b):** (i) buffer 同定 = **反証を試みて不成立 → CONFIRMED** + ⭐**repo 全体で `use_mujoco_cpu` を override する caller はゼロ** ⇒ producer/env とも同一 global = **今日 cross-backend は存在しない**。**corollary: 単一 global ゆえ flip は atomic** ⇒ 唯一 cross-backend を生む経路 = **「今日 capture した bank を flip 後の env へ restore」** ⇒ **provenance assert が唯一の防壁 = load-bearing**。(ii) leg6 の 3 穴 (index-space trap / 部分修正の素通り / lag convention) → **全て fold** (R7)。(iii) provenance UPGRADE → **F-6 として %12 が裁定**。

---

## §0. [CHECK] 実測 — 修正版 (v1 の 4 事実 + 5体が捕捉した 5 事実)

| # | 事実 | 根拠 | v1 との差 |
|---|---|---|---|
| **F1** | 記録の `arm_q` = **full physics joint_q (7707, 74)** = arm 28 + cable 46 (free-root 7 + hinge 39)。46/46 列が実変動 (data-level 確認)。無いのは **joint_qd のみ** | route_demo_recorder.py:249 / 実測 shape + 変動列数 (CC6 が data-level 確認) | **維持** |
| **F2** | env の RL step t 後 = 記録 frame **10t+9**。comp5 の `10t+3` は `_nsub = RL_SIM_SUBSTEPS(=4)` の誤同定 (comp5:162→:213)。**dt = 1/480 Hz (sim_time 実測 0.002083s)** | newton_route_env.py:407 / newton_skill_env_base.py:95 / 実測 | **維持 + dt 実測追加** |
| **F3** | fork state = producer frame **cf[t_k]−1** = **convention A**。⚠**根拠は解析的強制であって経験的判別ではない**: (i) recorder は post-step sample (:561-562) (ii) chunk t は frame cf[t]..+9 を消費 (iii) 走行 div は cf[t]+9 を読む (:3419) ⇒ fork 状態は frame cf[t_k]−1 の post-step 状態でしか整合しない | CC3/CC4 が独立に導出 | ⚠**v1 の「≤1.14mm ゆえ無視不可 → R5d が判別」は誤り**: 5 境界での 2 convention 差 = **0.0008 / 0.194 / 0.0008 / 0.009 / 0.002 mm** (held-seg、CC4 実測)。⚠**正直化 (%9 minor)**: 「全て 0.15mm 床の下」は不正確 — **k=2 の 0.194mm は FORK-1 致死 seed max (0.147mm) を超える**。ただし **convention A は解析的に強制** され、**R2f (banked q == recording[capture_frame] 74 列 EXACT) が実質の pin** ゆえ実害なし。経験的判別 leg は不要 (telemetry のみ) |
| **F4** | capture = **全 frame dump** (7707 × (74 q + 73 qd) f32 ≈ 4.4MB) — boundary 選択は offline builder | — | **維持** (CC4「good design, keep it」) |
| ⭐**F5** | **`run_route` は Rs-LOCKED** (route_executor.py:**1027** banner「ANTI-REVERT / Rs-LOCKED — do NOT edit **any line of run_route** without Rs」、span :1038-3110)。**ANTI-REVERT marker の実体行 = :2474 / :2494 / :2636** (%12 実測、全て run_route 内部)。recorder の **ctor :1074 / finalize :3109 も lock 内側**。**hook :561-562 が属する `physics_step` (:503-565) だけが lock の外** | 本 turn 実測 (CC3 catch) + %12 独立確認 | ⭐**精確な記録 (records-must-match-fact、%12 指示)**: v1 の「recorder と同型に ctor/finalize を挿す」は **ANTI-REVERT marker 行そのものの改変ではない**が、**banner が禁じる「run_route のいずれかの行の編集」に該当** (lock 隣接)。→ **v2 の回避策 = capture を `physics_step` (lock 外) の遅延 init + atexit finalize に閉じ、run_route を 0 行変更 ⇒ 問い自体を消す設計**。%12 = 採択、Rs waiver 不要 |
| ⭐**F6** | **`_jws` は「関節 ID」基点であって「座標」基点でない**: 1 world = **68 関節 / 74 座標** (cable free-root = 1 関節 ↔ 7 座標 / 6 速度)。既存 :1075-1077 は `_jws[w]+28` を**関節 ID list** の生成にのみ使い、座標は `model.joint_q_start` が解決 | newton_skill_env_base.py:1088-1092 / CC6 catch | ⭐**v1 の R3b「per-world の joint offset で書く (`_jws[w] + _N_ARM_JOINTS ...`)」は座標直書きと誤読され得る → world 0 だけ正しく w≥1 が 6·w ずれる罠。** cable 書込は **必ず `model.joint_q_start` 経由**と明記 |
| ⭐**F7** | **arm の banked qd = 0 は「妥協」でなく EXACT**: 本基板は arm joint_qd を毎 frame ゼロ化 (producer physics_step:543 / env `apply_arm_only_write_perworld`) ⇒ **capture した arm qd は 1-substep の積分残渣で、次 substep に捨てられる**。**capture の真の delta = gripper_qd + cable_qd のみ** | route_executor.py:386-391 (v1 docstring が明言) / CC3+CC6 | ⭐**v1 の R2b「v1 の qd=0 は妥協」は誤読** → 訂正 |
| ⭐**F8** | **`eval_fk` は body_q **と** body_qd の両方を書く** (`outputs=[state.body_q, state.body_qd]`) ⇒ qd 保存 restore + eval_fk 1 回で **body_qd は stale にならない**。SolverMuJoCo は `update_data_interval=1` で毎 step `joint_q/joint_qd → qpos/qvel` を同期 | newton 1.2.1 articulation.py / newton_skill_env_base.py:1325/:1338 (CC3 検証) | **新規** (CC6 の H1「body_qd 分裂」仮説は REFUTED) |
| ⭐**F10** | ⭐**k-realizability + artifact-ID の罠 (本 turn 実測、CC2-1 由来)**: **正典 golden (sha 5f1c3f92 = RUN1_REFERENCE_V2、env が :621-624 で pin)** の G-phase frame 数 = `{0:1124, 1:600, 2:860, 3:3597, 4:620, 5:906}` ⇒ **k=1..5 全て実在**、f_k = 1124/1724/2584/6181/6801、**全境界で両手 grip=0.7407 (閉)**。⚠**別 artifact `p3_dod_cuda_demo_raw` (sha 509ad193) は G6=0 frames / k=4 が release 直後 (grip=開)** — CC2 はこれを読んで「k=5 不在」CRIT を出した (**REFUTED**)。⇒ **hazard class は実在**: v1 builder は frame の無い phase を**静かに skip** (:432-433)、`reset_to_phase` は bank 不在で**静かに no-op** (:3315-3317) ⇒ 非正典 recording なら**退化した bank が silent に出来る** | 本 turn 実測 | ⭐**新規** — R2 に provenance assert + missing-phase fail-loud を新設 |
| ⭐**F11** | ⭐**eq_active = THREAD 固有の第 2 channel、k≥3 で live (本 turn 実測、%9 C-α + ERRATUM-D)**: 記録の `pin_active` は **frame 2544-7706 で ON** ⇒ capture frame では **k=1,2 = OFF / k=3,4,5 = ON (eqid=27, body=55)**。clip-pin は INVARIANT #5 の**認可済み例外** ⇒ **fork で pin/eq の active flag を復元しないと cable/clip 関係が乖離**。記録は `pin_active`/`pin_eqid`/`pinned_body` を保持 → 復元可能 | 本 turn 実測 | ⭐**新規** — R3 に disposition 新設 |
| ⚠**F12** | ~~mjWarp Data は露出している (ERRATUM-D): `qacc_warmstart`/`eq_active` は mjw_data から capture/restore できる~~ → ⚠**部分 FALSIFIED (F13、本 turn の runtime 実測)。結論「capture 可能」は不変だが、buffer 同定が誤り**: 本基板の live buffer は **CPU `mj_data`** であって `mjw_data` ではない。F12 は source inspection 由来で、**私・%12・%9 の 3 名が同じ穴を踏んだ** | 実測 + ERRATUM-D → **F13 が上書き** | ⚠**ERRATUM-F §18 に昇格**: source inspection では liveness を discharge できない — **設定 backend 上の runtime 測定でのみ discharge せよ** |
| ⭐**F13** | ⭐⭐**dead mirror — 本 chunk 最大の catch (runtime 実測、他の全 leg が PASS していた)**: `task_config.py:116 USE_MUJOCO_CPU=True` ⇒ `SolverMuJoCo.step` は **`mj_step(mj_model, mj_data)`** を回す (solver_mujoco.py:3267-3273)。`mjw_data` は `put_data` で**無条件生成** (:5791、`use_mujoco_cpu` guard の外) されるが **CPU path では一度も step されない**。初版 `_mj_hidden_state` は mjw_data を先に試すため **dead mirror を capture していた**: 実測 `qacc_warmstart` 非ゼロ = **0/562611**、`eq_active` の**変動列 = ゼロ** (常時 ON = col 40-45 の 6 本 = 構造 eq [4 CONNECT + 2 follower-mirror、base:1946]、col 0-39 = 事前確保された disabled pin 候補)。⚠**記録の独立 witness は `pin_eqid=27` / `pinned_body=55` / `pin_active` ON = frame 2544-7706** ⇒ **bank は k=3/4/5 で「pin OFF」を restore する = clip が cable を保持していなければならない境界で物理的に誤った state = FORK-1 と同 class の silent mismatch**。⭐**producer は無事**: mj_data が live ゆえ clip-pin は効いている → **INVARIANT #5 intact、Rs-LOCKED producer に瑕疵なし。壊れていたのは私の read 先のみ** | 本 turn runtime 実測 (capture meta `mj_backend=mjw_data` + eq/warmstart 実測 + task_config.py:116 + solver_mujoco.py:3267-3273/:5791) | ⭐**新規 — F12 を上書き**。⭐**joint_q/joint_qd は Newton `State` 由来ゆえ無傷** (L∞(capture.joint_q − recording.arm_q) = **0.000e+00 / 全 7707 frame × 74 coord**) — 汚染は hidden-state channel のみ |
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
| d | ⭐**capture_frame instantiation guard (一般化、%12 E-5 (1))**: **`assert G(phase[capture_frame]) == k`**。当初は「`f_k % cadence == 0` の multi-cell edge」限定の想定 (CC4-F9) だったが、**本 assert は実際に %12 の手計算誤り (ceil 整列を適用せず raw 境界 f_3−1 = 2583 を capture frame にした) を落とす** — golden 実測 `phase_id[2583]=6` (G2) / `phase_id[2589]=7` (G3) ⇒ 2583 で FAIL・2589 で PASS。⇒ **「capture_frame の誤 instantiation クラス全般 (raw-boundary 誤り含む) の guard」**として一般化 | unit |
| e | `0 not in phases` 維持 (**k0 禁止不変量**) | unit |
| f | ⭐**自己整合 cross-check**: banked_v2 の **q** が recording `arm_q[capture_frame]` と **EXACT 一致** (74 列全数) | unit (最強の builder 検証) |
| g | ⭐**qd の独立検算 (CC4-F4、0-GPU)** — ⚠**v3 で手法を全面置換 (DEFECT-2)**。~~中心 FD + ≤20% bar~~ は **構造的に不適**と実測判明 (κ 帯域不足 / wrong-substep に不可視 / scale に盲目) ⇒ ⭐**substep-index readout**: `bwd = a·qd[f−1] + b·qd[f]` の LSQ から **gain / substep index m̂ / R²** の直交 3 統計を取り、**8 摂動 identifiability 表**で判別力を実証。実測 = **m̂ 9.81 (cable) / 9.89 (gripper) vs 予測 10** ∧ **gain 1.0003 (gripper)** ∧ **R² 0.93/1.00**。⚠**spec :140 が却下したのは FD による「構築」であって「検算」ではない** — 本 leg は検算のみ (§6) | **L2′ + L2″ (唯一 capture の存在理由を検証する leg)** |
| ⭐l | ⭐**hidden-state liveness guard (DEFECT-1、builder に fail-loud で内蔵)**: `_assert_eq_active_live` — 記録の独立 witness (`pin_eqid`/`pin_active`) に対し **captured `eq_active[pin_eqid]` が latch すること**を要求。**dead mirror は「どの offset でも latch しない」ので必ず raise**。lag は **実測** (±1 frame の convention 差を許容、実測 = **0**)。⇒ **dead-mirror bank を bank 時点で作れなくする** | unit (5 番目の fail-loud guard = `live_eq=False` fixture が raise) |
| ⭐m | ⭐**provenance = (backend_id, layout_hash) (F-6)**: capture 時に **runtime から** 記録 — `use_mujoco_cpu` / solver class / newton+mujoco version / **nq・nv・neq・nbody・njnt・njmax・nconmax・eq_identity・eq_names・scene_flags の sha256**。⇒ B3b restore が **backend flip / scene 変更 (C2 build) / version bump / index shift** を **1 本の fail-loud assert** で落とす。⚠**%9 corollary**: `use_mujoco_cpu` は単一 global ⇒ flip は atomic ⇒ **唯一 cross-backend を生む経路 = 「今日の bank を flip 後の env へ restore」** ⇒ 本 assert が**唯一の防壁 = load-bearing** | unit + leg6 |
| ⭐n | ⭐**index-space assert (`_assert_pin_index_spaces`)**: `pinned_body` (Newton) と `eq_obj1id` (MuJoCo) は **別空間で +1 ずれる**。offset を **hardcode せず producer 自身の eq 表から導出**し、**resolver の round-trip (identity → 元の eqid)** を assert。⇒ **F6 (index-space) の第 2 目撃例を機械化して封じる** | unit + leg6 (実測 newton 55 → mjc 56、offset +1、round-trip 27 ✓) |
| h | v1 builder 残置 (capture 不在時)、v2 は capture npz が cfg にある時のみ | grep + unit |
| i | ⭐**bank-load 時の width assert (CC6-4)**: capture joint_q 幅 == 74 == env の per-world 座標幅 / arm 28 / cable 46 == 7 + (cable_bodies_per_world − 1) / cable_bodies_per_world == 40 (producer と一致)。`route_c2_scene` の clip が座標を持てば loud FAIL | unit |
| j | ⭐**origin-sensitivity の明示 (CC3-11)**: cable free-root は**絶対 7 座標** ⇒ 全 world tiling は `scene.replicate(spacing=(0,0,0))` (newton_skill_env_base.py:1883) に依存。**cable_q は初の origin-sensitive banked 量** → spacing 非零なら loud FAIL する assert | unit |
| ⭐k | ⭐**provenance + missing-phase fail-loud (F10)**: (i) bank v2 build 前に **capture/recording の sha == RUN1_REFERENCE_V2** を assert (env は :621-624 で既に recording 側を pin — capture 側にも同 pin) (ii) **要求 phase に frame が無ければ raise** (v1 の silent `continue` :432-433 を踏襲しない) (iii) `reset_to_phase` の silent no-op 経路 (:3315-3317) は R6a の再条件付けで塞ぐ (iv) ⭐**capture_frame の pin 状態 assert** (%9/%12、%12 自己訂正で **45 frame** 確定 = 当方実測 2589−2544 と一致): k=3 の capture frame (2589) は pin onset (2544) の **45 frame = 4.5 RL step 後**。⚠**根拠の訂正 (%12 E-5 (2))**: pin onset (2544) は **phase_id 5→6 遷移と EXACT 一致** ⇒ pin は**物理イベント依存でなく phase schedule 発火** ⇒ DR/multi-cell では onset と capture_frame が **co-move** ⇒ **45-frame margin は「薄い」のでなく「構造的」**。assert は維持するが位置づけは「fragile margin の防護」→ **「(iv) と同族の instantiation guard (安価な異常検知)」**。⚠**非正典 recording は退化 bank を silent に作る** (CC2 が別 artifact で実証: sha 509ad193 は G6=0 frames) | unit: 欠落 phase → raise / sha 不一致 → raise / pin 不一致 → raise |

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
| ⭐h | ⭐**mjData warm-start = (a) capture + restore (%9 dissent を受諾、当方の (b) 案は撤回)**。**(b)「両側 zero」は実現不能**: 参照側 = 記録 (RUN1_REFERENCE_V2 = Rs-LOCKED / MOTION STANDARD) ゆえ **producer の warmstart を遡ってゼロ化できない** ⇒ 実質「fork 側のみ zero」= 非対称 = (c) と同義。対称性の利点は成立しない。加えて「warmstart は初期推定にすぎない」は **FORK-1 が反証した直感そのもの** (本基板は 0.02-0.15mm を ~100× 増幅)。**決定打 = C-β との coupling**: (b)/(c) は L5 が経験的 falsifier として機能する時のみ選べるが、C-β により現 L5 は検出力を欠く ⇒ **falsifier 不在で (b)/(c) は選べない**。低 regret = **(a)**。**impl**: capture は post-step 同一点 (cf[t_k]−1) で warmstart を読み、restore は solver の data sync **後**に書く (前に書くと上書きされる)。⚠**B3a は warmstart + eq_active を capture に含める (superset ⇒ restore の最終択が変わっても artifact は無駄にならない)** | L5a + unit |

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
| ⚠~~**L2 FD qd 検算**~~ | ~~記録 q から中心差分 `qd_fd = (q[f+1]−q[f−1])/(2dt)` を作り capture の joint_qd と ≤20% で照合~~ | ⛔**v3 で撤回 = DEFECT-2**。実行して **k=2/3 で FAIL** → root-cause の結果、**bar 自体が構造的に不適**と判明: (i) `SIM_SUBSTEPS=10` ゆえ位置差分は**必ず frame 平均**を返す ⇒ κ=\|Δqd\|/\|qd\| が大きい frame (k=2: 0.92 / k=3: 1.81 = 速度が 1 frame 内に 92-181% 変化) では **central/backward/trapezoid/3-tap の 4 変種が正しい data に対して同時に FAIL** (ii) spec が名指しする **「wrong substep」hazard を原理的に検出できない** (1-substep ずれ = κ/10 ≈ k=1 で **1.6%** ≪ 20% bar) (iii) **scale に盲目**。**⇒ L2′ へ置換** | 証拠 = `leg3_v1_SUPERSEDED_fd_FAIL_evidence.json` |
| ⭐**L2′ qd substep-index readout** (**0-GPU**、DEFECT-2 の置換) | 半陰的 Euler × S substep から **解析的に** `bwd[f] := (q[f]−q[f−1])/DT = mean_j(v_j)` ⇒ **`bwd = a·qd[f−1] + b·qd[f]` を全 frame×coord で LSQ** し、**直交 3 統計**を取る: **gain g=a+b** (scale/sign) / **substep index m̂ = S·((S+1)/(2S)+1−b/g) = 15.5−10·(b/g)** (timing) / **R²** (layout) | ⭐**m̂ ∈ [9.5, 10.5]** (= capture が **最終 substep** であることを **±0.5 substep 分解能**で読む — **frame 級 data から substep 級の主張を取る**、GPU 追加コスト 0) ∧ **gain \|g−1\| ≤ 0.005 (gripper channel)** ∧ **R² floor**。⭐**channel 分離の honest 化**: gripper は R²=1.000 / g=1.0003 = **bias なし ⇒ scale bar はここに置く**。cable は frame 内 accel が非単調ゆえ **gain に固有 bias −1.9% を実測** ⇒ **scale bar に使わず telemetry + drift tripwire (`G_CABLE_BAND`)** として持つ (F-5 (4): 単一 contiguous copy 前提が崩れた時に surface させる) | CPU |
| ⭐**L2″ identifiability 表** (**ERRATUM-E col ii の実装**) | L2′ の同一 estimator に **8 摂動 bank** をかける | ⭐**real のみ ACCEPT、他は全 REJECT + どの統計が落としたかを明示**: m=9 (1 substep 早) → m̂ 9.30 / m=8 → 8.57 / **null (qd≡0) → degenerate** / sign-flip → g=−0.98 / ×1.02 → gain / **×0.98 (逆符号) → gain** / permuted → R²=0.000 / frame-shift → m̂ 6.99。⚠**逆符号の scale 誤差も落とすことを実証**した (cable の固有 bias と相殺して素通りする穴を自己捕捉) | CPU |
| ⭐**L6′ hidden-state liveness** (**DEFECT-1 の negative control、%12 必須化**) | 記録の**独立 witness** (`pin_eqid`/`pinned_body`/`pin_active`) と capture の `eq_active` を照合 | ⭐**(1) buffer**: `use_mujoco_cpu` から導く live buffer を capture が読んでいる **(2) eq_active[pin_eqid] が pin_active を再現** — ⚠**lag は実測して pin** (記録 = script が eq を立てた frame / capture = solver が step 後に持つ値 ⇒ ±1 frame の convention ずれは許容、**dead mirror は「どの offset でも一致しない」= latch しない**ことで落ちる。EXACT を無検証で課すと fix 後に false-FAIL する [%9 (iii)]) **(3) 各 hidden field に liveness gate** = 「変動 > 0」**or**「恒常である機構の明示」(warmstart は witness 不在ゆえ変動で見る。eq_active だけ見ると **warmstart の buffer 誤選択が素通り**する [%9 (ii)]) **(4) eq は index でなく identity で解決** (`resolve_pin_eq_index`) し、**canonical cell で eqid=27 に解決されること**を assert [%9 (i)、F6 の index-space trap 再演を防ぐ] **(5) negative control**: pin 列を凍結した dead-mirror bank が **REJECT される**こと | CPU |
| ⭐**L3 null-bank negative control** (**ERRATUM-C の DoD 必須項**) | `cable_qd ≡ 0` の**偽 bank** を作って同じ fidelity/growth leg にかける | ⭐**必ず FAIL すること** — PASS したら bar に判別力が無い証明。**判別力の存在を DoD に組み込む**（CC4-F3 の根本対策） | CPU + GPU (L5 と同 harness) |
| **L4 restore-exact + 配置** | fork → joint_q/joint_qd を banked と L∞ 比較 + per-world 配置 | **L∞ == 0** ∧ 2-world で world-0 byte 不変 (座標は `model.joint_q_start` 解決、F6) | unit (infra = §5 ask B2) |
| ⭐**L5a K-step growth leg — FF mode** (%9 C-β: **cable/hidden-state channel はここ**) | fork (world_count=5、各 world を別 k) → **FF (記録 arm pin) + K=20-50 step roll** → div_grip 系列を producer 同境界と比較 (leg8 の較正手法を再利用) | ⭐**PASS = (i) HOLD 発火 0 (ii) 健全域 band 内 (iii) ramp 不在** (FORK-1 の signature は step-1 の大きさでなく **growth**)。**FF ゆえ arm は記録に pin される ⇒ 成長は cable + hidden state に一意帰属**、かつ **leg8 の band は同 mode = apples-to-apples**。restore 直後の channel 分離 bar (**cable ≤0.15mm 級 / arm・gripper ≤1mm**、div は **route_t = t_k−1** で呼ぶ [CC3-2]) + HOLD-arming sanity ≤10.407。**null-bank negative control (L3) も本 leg で発火** | 1 env build |
| ⭐**L5b fork-integrity leg — IK/residual mode** (%9 C-β: **arm channel はここ**) | 同 fork → **IK 駆動 (trainer 実使用 path、明確化 E)** で数 step | **(vi) arm が P0 に戻らない** (欠陥時 373-444mm ⇒ 3 桁 margin の直接 assert、growth metric 不要) / (vii) done == False 全 k / (viii) held_seg が記録追従 / (i) HOLD 発火 0。⚠**div band を IK で使うなら P0 起点・IK・Δ≡0 の matched control で IK baseline を実測してから** — **leg8 の FF 値を流用しない** (cross-mode 流用 = ERRATUM-A / B2 10× と同 class) | 1 env build + 1 control |
| ⭐**L6 post-fork assert leg** | fork 入口の runtime assert 7 項 (R5c) を全 k で発火確認 | 全 PASS ∧ **eq_active/pin が記録値と一致** (F11、k=3,4,5 で pin ON) | L5b と同 run |
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

⚠**見積 delta (%12 A2 条件)**: source ~500-655 (charter est 150-300)。**hard cap 800 内**。増分の主因 = 5体が要求した検証機構 (write-set 全数 / fork 入口 / post-fork assert / FD validator)。**実 diff が ~600 に迫れば分割を再提起**する → **分割実施済 (§7)**。

⭐**B3a 実測 LOC (v3、build 完了時)**: `route_executor.py` **+570** / `test_routeexec_state_bank.py` **+163/−3** = **source 733 行 (hard cap 800 内、余裕 67)**。⚠**当初 est (~300-380) を大きく超えた**。増分の内訳は**全て検証機構** — DEFECT-1/-2 の fix と、%12 F-5/F-6 + %9 3-lens が要求した項: provenance (backend_id + layout_hash + eq_identity + eq_names) / `resolve_pin_eq_index` / `_assert_pin_index_spaces` (index-space round-trip) / `_assert_eq_active_live` (dead-mirror guard) / substep-readout leg + identifiability 表 / liveness leg。**機能面 (capture + builder) 自体は est 内**。B3b は別 chunk・別 cap。

### R9 — LOUD + carries
- **DR×curriculum 相互排他** (spec §6.2-5): bank = x0_y0 単一 cell ⇒ phase-k 開始は DR 被覆ゼロ。**機械 guard を R3f に置く** (宣言だけにしない)。
- **Layer-B re-BASELINE** (spec §4.1 :77): bank v2 ON の挙動変更を Rs-visible に宣言。
- **mjData warm-start (`qacc_warmstart`)** = 本基板の唯一の未 reset hidden state (CC3-4/CC6-7)。**既存 done-reset も同じ**ゆえ B3 新規 bug ではないが、**M10 の guard は L5 (1-step + 保持 probe) が唯一**と明記。
- B4 へ: start-mix policy / recenter 実配線 / DR guard の解除条件。B5 へ: `_start_phase` の export。B7 へ: per-k 正制御 bar / bank-G3 摂動 leg / multi-cell option。
- ⭐**B3b/B4 へ (v3 新規、spec F-7.3 に登録済)**: **幾何 anchor** — cross-layout bank の真の robust 形 (producer は :2352-2364 で **world 位置一致**で eq を探している)。今日は layout_hash assert が同一 layout を保証するので banked index で足りる。**未実装 = 意図的** (charter §7-4: 設計要否は %12 が B3b conformance で裁定)。

---

## §8. ⭐本 arc の総括規律 (spec §18 F-7.4、%12 — 今後の全 leg に適用)

**捕捉された誤りの大半は「対象」でなく「計器」に在った。** 本 chunk だけで:

| # | 計器の壊れ方 | 実例 |
|---|---|---|
| 1 | **bar が対象を分解できない** (感度不足) | leg3 v1 の中心 FD: 「wrong substep」を **1.6% しか動かさず 20% bar で不可視** |
| 2 | **bar に判別力が無い** (negative control が落ちない) | B3 v1 の全 bar が **`cable_qd≡0` の偽 bank を 3.4-44× 余裕で PASS** させていた |
| 3 | **mode 交絡 / bar 流用** | FF mode で較正した band を IK mode に流用 (ERRATUM-A / B2 の 10× 誤読) |
| 4 | **source inspection が liveness を測れない** | ERRATUM-F: grep では dead buffer を見抜けない — **verifier 3 名が同時に踏んだ** |
| 5 | ⭐**死んだ計器の測定値が「事実」に見えた** | **`qacc_warmstart = 0/562611`** — dead mirror の artifact。これを根拠に「非 item 化」を提起し、危うく **absmax 1e6 の live hidden state を bank から落とす**ところだった |
| 6 | ⭐**罠を防ぐために書いた関数が、その罠を踏んだ** | `resolve_pin_eq_index` が **Newton body id を MuJoCo eq 表に照合** (worldbody +1) → 隣の constraint に着地 |

⭐**規律 (F-7.4)**: **ゼロ / 不在 / 変動なし の測定は、「対象が無い」のか「計器が死んでいる」のか区別できない。⇒ 必ず positive control (変動を示すはずの独立 witness) を併走させよ。**
本 chunk での正解形 = **leg6 が記録の `pin_active` を独立 witness にした**こと (capture 由来でない情報源との照合)。加えて **lag は仮定でなく実測して pin** した。**「変動 > 0 or 恒常である機構の明示」の per-field liveness gate** はこの規律の機械化。

---

## §2.9 ⭐DoD 規律 3 列 (spec §17 E-5、%12 23:10 — 全 fidelity DoD に必須)

本 arc の corrective 3 連続 (C-α 感度不足 / C-β SN 交絡 / E-4 cross-mode bar 流用) は全て **「計器が対象を測れていない」class**。⇒ **全 fidelity DoD に以下 3 列を必須化**:

⭐**v3 の実績**: 本 3 列を **B3a で実際に建てた結果、bar 自身の穴が 2 つ出た** — (a) leg3 の FD bar は「wrong substep」を原理的に検出できず (DEFECT-2)、(b) leg6 の scale 論証は cable の固有 bias と相殺する**逆符号 scale 誤差**を素通りさせた。**どちらも「negative control を実際に走らせる」列 (ii) が捕捉**。E-5 は形式でなく実効。

| leg | (i) この bar が落とす「間違った bank」 | (ii) negative control による実証 | (iii) bar の測定 mode == leg の駆動 mode |
|---|---|---|---|
| ⛔~~L2 FD 検算~~ | ~~cable_qd が全ゼロ / 別 buffer / 置換 / 転置 / scale 誤り~~ | ⚠**列 (i) を満たせていなかった**: 「wrong substep」を **1.6% しか動かさず 20% bar で不可視** ⇒ **撤回 (DEFECT-2)** | — |
| ⭐**L2′ substep readout** | **wrong substep (±1)** / **scale (両符号)** / **sign flip** / **permuted layout** / **frame shift** / **null** | ⭐**8 摂動を同一 estimator にかけ、real のみ ACCEPT・他は全 REJECT + 落とした統計名を出力** (L2″) | N/A (offline) |
| ⭐**L6′ hidden-state liveness** | ⭐**dead-mirror bank** (= 実際に作ってしまった bank: `eq_active` 凍結 → k=3/4/5 で **pin OFF** を restore) / **hidden field の buffer 誤選択** / **index-space 取り違え** | ⭐**(a) pin 列を凍結した dead-mirror bank が REJECT される** (unit の 5 番目 guard + leg 内) **(b) 各 field の「変動 > 0」gate** (warmstart の誤 buffer が eq_active 経由で素通りするのを防ぐ) **(c) identity round-trip** | N/A (offline、記録の独立 witness と照合) |
| **L5a K-step growth (FF)** | cable/hidden-state が誤った bank (FORK-1 同型 = 小さく始まり増幅する) | null bank + warmstart-zero bank を同 leg にかけて ramp が出ることを実証 | **FF mode ↔ leg8 の FF band** (apples-to-apples) |
| **L5b fork-integrity (IK)** | arm bank 未復元 / `_per_world_fk_jq` 未設定 (実測 signature = 373-444mm) | fk_jq を P0 のままにした control で FAIL を実証 | **IK mode ↔ 直接 assert** (div band は使わない; 使うなら IK baseline を先に実測) |
| **L4 restore-exact** | 座標解決の誤り (`_jws` 直書き = w≥1 が 6·w ずれる) | world-0 除外の 2-world control | N/A (書込比較) |

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
- ⛔**B4 (warmstart の択)** — ~~当方推奨 = (b) 両側 zero を既定・(a) capture を fallback~~ ⇒ ⭐**当方推奨は 2 度とも誤りで、2 度とも他者が正した。記録として残す (自己弁護しない)**:
  1. **(b) は実行不可能** — 参照 recording は Rs-LOCKED ゆえ遡って zero 化できない (%9 + %12 が同時に却下) → **(a) capture+restore に裁定**。当方は撤回。
  2. ⭐**その後の当方の第 2 の誤り**: dead-mirror 由来の「warmstart 非ゼロ = 0/562611」を見て、**「非 item への再分類が筋」と提起した**。%12 は **「symptom だけで再分類するな (ERRATUM-B の教訓)」+ regret 非対称**を理由にこれを退け、**(a) 据え置き**を裁定 (F-5 (1))。
  3. ⭐**実測が %12 を全面的に正当化した**: live buffer での warmstart = **非ゼロ 559764/562611、absmax 1.08e6**、`mjDSBL_WARMSTART` = OFF。**当方の提起どおり非 item 化していれば、absmax 1e6 の live hidden state を bank から落としていた** = 本 chunk が消そうとしている silent FORK-1-class defect を**自分で作っていた**。
  ⇒ **教訓 (自分向け)**: 「存在の有無」は決定の bar にならない (E-5 (i))。**dead buffer から測った値で設計判断を提起した**のが根本。**測る前に、その計器が生きているかを先に測れ** (= ERRATUM-F §18 そのもの)。disposition は L5a の A/B (B3b) が決める。
- **B5 (5体 の再走)**: 分割時、5体 は**再走不要**と判断 (panel は capture+restore の**和集合**を review 済で、CRIT は両半に跨がる)。B3a/B3b それぞれで [RULE-CHECK] → build → legs → 3-leg verify を回す。この読みの CONCUR 依頼。

## §7. ⭐分割提案 — B3a / B3b (%12 の「~600 超なら分割」条件を充足)

| chunk | scope | deliverable | files | est |
|---|---|---|---|---|
| **B3a** (producer + offline) | R1 capture (lock 外) / R2 bank v2 builder (整列・provenance・fail-loud・width/origin) / L1 capture leg / **L2 FD 検算** / **L3 null-bank negative control (offline 半)** | **検証済みの bank v2 artifact** (env 変更ゼロ) | route_executor.py (capture + builder) / test_routeexec_state_bank.py / w1_b3a_dod_legs/ | ~300-380 |
| **B3b** (env fork) | R3 restore (kwarg / joint_q_start / eq_active / warmstart) / R4 write-set 全数 / R5 **順序付き単一 fork entry** + post-fork assert / R6 guard 再条件付け / **L5 K-step growth leg (IK mode)** / L6 / L7 | **fork できる env** (B3a の artifact に依存) | newton_route_env.py / newton_skill_env_base.py / route_env_config.py / route_executor.py (guard + get_cable_bank) / test_routeexec_writesite.py / w1_b3b_dod_legs/ | ~300-370 |

**分割の seam が clean な理由:** B3a は **env を一切触らない** (capture は producer 側、builder は offline) ⇒ 表面適合 leg は producer 5-cell のみで足りる。B3b は B3a の artifact を消費するだけ ⇒ env 側 leg に集中できる。**lock risk (F5) は B3a に閉じる**。
⚠**%9 minor**: `route_executor.py` は**両 chunk で触る** (B3a = capture+builder / B3b = guard+get_cable_bank) ⇒ **producer 5-cell byte-preserve leg は両方で必要**、file-clean な seam ではない。roster の **U4 (restore) は B3b 帰属**へ訂正。

### §7.1 ⭐seam contract — B3a → B3b (%12 B5 条件: 新規設計面ゆえ **3-leg joint verify** [%12+%9+%10] で審査、5体は不要)

**artifact = bank capture npz (B3a 出力 / B3b 入力)**

⚠**npz は repo に入れない (B2 precedent と同じ)**: `bank_capture.npz` (5.8MB) と byte-repro の `route_demo_raw.npz` (12MB×6) は **再生成可能** (byte-repro が決定性を証明済) ゆえ commit しない。**provenance は sha256 で pin**:
- `bank_capture.npz` **sha256 = `312dc6389807c0202f3de84accafd6c9b64436ffb29cf6726805f7cbf17af770`** (final code / final run、2026-07-14 04:0x)
- 再生成 = `bash eval_runs/.../w1_b3a_dod_legs/run_legs.sh` の LEG2 (BANK_CAPTURE=1、cuda:0、~1 min)

| key | dtype / shape | 意味 |
|---|---|---|
| `joint_q` | float32 [F, 74] | 全 frame の physics joint_q (arm 28 + cable 46) |
| `joint_qd` | float32 [F, 73] | 全 frame の physics joint_qd (arm 28 + cable 45) |
| `grip_target` | float32 [F, 4] | driver DOF の servo target ([L,L,R,R]) |
| `phase_id` | int64 [F] | 記録 15-phase (G 分解は builder 側) |
| `qacc_warmstart` | float32 [F, nv] | mjData warm-start (ERRATUM-D / B4=(a)) |
| `eq_active` | int32 [F, neq] | 等式拘束 active flag (4-bar linkage + clip-pin、F11) |
| `frame_idx` | int64 [F] | 0..F−1 (recorder と 1:1、cross-assert 用) |
| meta | json | cadence / PHYSICS_STEPS_PER_RL / dt / cell env / recording sha256 / route_executor.py sha256 / **mj_backend (実際に読んだ buffer 名)** / ⭐**provenance** |
| ⭐meta.`provenance` | json | ⭐**(backend_id, layout_hash)** — F-6。**backend_id** = `use_mujoco_cpu` + solver class + newton/mujoco version。**layout_hash** = sha256(nq / nv / neq / nbody / njnt / njmax / nconmax / **eq_identity [(type,obj1,obj2)×neq]** / **eq_names** / scene_flags [`route_c2_scene`/`gripper_dynamic`/`perclip_pin_n`/`solver_backend`]) |

⭐**bank[k] の pin 系 key (v3 追加):** `pin_eqid` (producer layout の eq index) / **`pin_seat_body_newton` (=55)** / **`pin_seat_body_mjc` (=56)** / **`pin_body_index_offset` (=+1、実測・assert 済)** / `pin_eq_lag` (**実測 = 0**)。

⚠⭐**index space が 2 つあり +1 ずれる (v3 実測、leg6 が捕捉)**: 記録の `pinned_body` は **Newton body id**、`eq_obj1id` は **MuJoCo body id** (MuJoCo は worldbody を index 0 に持つ)。**Newton id で eq を解決すると隣の拘束に着地する** (newton 55 → eq **26**、正解は **27**) = **物理的に別の constraint を silent に pin する**。⇒ **`resolve_pin_eq_index` は MuJoCo body id を取る**。offset は hardcode せず **producer 自身の eq 表から導出 + round-trip assert** (`_assert_pin_index_spaces`)。**F6 (`_jws` = 関節 ID vs 座標) の第 2 目撃例 — しかも「その罠を防ぐために書いた関数」自身が踏んだ。**

**fail-loud 条件 (B3b 側の bank-load):** recording sha ≠ RUN1_REFERENCE_V2 → raise / 要求 phase に frame 無し → raise / joint_q 幅 ≠ env の per-world 座標幅 → raise / cable_bodies_per_world ≠ 40 → raise / world spacing ≠ 0 → raise (origin-sensitivity)。

⭐**B3b が継承する義務 (v3、%12 F-5/F-6 裁定):**
1. ⭐**provenance assert (fail-loud)**: restore 時に **`bank.provenance.backend_id` == live solver の backend_id** ∧ **`layout_hash` == live model の layout_hash**。⚠**%9 corollary で load-bearing**: `use_mujoco_cpu` は単一 global ⇒ producer/env は常に同一 backend で **flip は atomic** ⇒ **唯一 cross-backend を生む経路 = 「今日 capture した bank を flip 後の env へ restore」** ⇒ **この assert が唯一の防壁**。同様に **layout 変更 (C2 build / multi-cell / comp3b / DR) は backend flip より起きやすい** ⇒ layout_hash が本命。
2. ⭐**eq は identity で解決** (`resolve_pin_eq_index(eq_identity, pin_seat_body_mjc)`) し、**banked `pin_eqid` と一致することを assert**。index 直用は禁止 (上記 +1 罠)。
3. ⭐**L5a restore-vs-zero A/B (F-5 (1))**: warmstart を restore した場合と 0 にした場合で **軌道が FORK-1 seed scale (0.147mm) を超えて動くか**を FF mode で測る。⚠**v3 実測で warmstart は live (非ゼロ 559764/562611、absmax 1.08e6、`mjDSBL_WARMSTART` は OFF)** ⇒ **非 item 化の目は薄い**が、**決めるのは A/B であって存在の有無ではない** (E-5 (i))。
4. ⚠**cross-layout の真の robust 形は「幾何 anchor」** (producer は :2352-2364 で **world 位置一致**で eq を探している)。**将来 layout を跨ぐ bank が要るなら幾何 anchor を bank する必要がある** — **未実装、B3b/B4 への carry** (spec F-7.3 登録済、charter §7-4: 新設計は独断しない)。
   ⛔~~今日は layout_hash assert が同一 layout を保証するので banked index で足りる~~ ⇒ **本前提は FALSE (B3-α、下記 §9)。layout は同一でなく、assert は「祝福」でなく「BLOCK」する。**

---

## §9. ⛔⭐ B3-α (CRIT / STOP) — bank の `eq_active` には restore 先が存在しない (%9 発見 03:32、当方 on-disk 確認済)

**当方の独立確認 (narrative でなく on-disk):**

| # | 事実 | 根拠 (実読) |
|---|---|---|
| 1 | producer は **`PERCLIP_PIN=1` の時だけ** 40 本の pin 候補 eq (cable body 1 本につき 1 本の DISABLED connect-to-world) を事前確保。**既定 OFF**。全 route runner が `PERCLIP_PIN=1` ⇒ golden もそれで録画 | test_newton_clip_routing.py:**1405** (`if os.environ.get("PERCLIP_PIN","0")=="1" and solver_backend=="mujoco"`) |
| 2 | ⭐**RL env (`build_multiworld_scene`) は構造 eq 6 本しか作らない** (4-bar connect ×4 + follower mirror ×2)。**pin 候補ゼロ。** base 自身の comment が明言: **「Default/build_multiworld has no disabled connect」** | newton_skill_env_base.py:**1451** (comment)、:1606-1630 (connect/mirror 生成) |
| 3 | `newton_route_env.py` の pin 参照 = **0 件** (grep) | 実測 |
| 4 | c1pin wiring は **B0-1 で revert 済** ⇒ 現 env は確定的に pin 無し | B0-1 a6b7ab6007 |

⇒ **bank neq = 46 (= 40 pin 候補 + 6 構造) / env neq = 6。banked `eq_active[27]` に対応する eq が env に存在しない。**

**⭐これは index shift ではない — 「移植先に機構が無い」:**
- 私の F-6 layout_hash assert は **正しく発火する** (46 vs 6) ⇒ restore 前に fail-loud。**assert は仕事をする。** ⚠だが **私の書いた前提「assert が同一 layout を保証するので banked index で足りる」は誤り** — layout は**同一でない**。assert は通行許可でなく**通行止め**。
- ⭐⭐**より深い問題 (物理)**: **k=3/4/5 の fork state は pin に物理的に依存している。** その境界では **cable は active constraint で C1 seat に保持されたまま**、腕は離して C2 へ持ち替える。**pin 無しの env にその cable 配置を restore すると「座っているが保持されていない」= seat から出る。⇒ fork state が現 env で実現不能。** (L5a は経験的に捕捉するが、原因を知らずに「fork が壊れている」と debug する羽目になる)

**⛔ disposition は builder 判断でない (Rs専権) — B3b STOP:**
clip-pin は **INVARIANT #5 の唯一の認可例外** (`log.md:6534`)。**RL env へ配線 = 認可例外を新環境へ拡張 = 前提 scope 変更** ⇒ CLAUDE.md §0 FOUNDATIONAL INVARIANT 規則により **即 L3 + STOP → BLOCKED_FOR_USER**。

⚠⛔**歴史の罠 (明示的に踏まない)**: c1pin wiring は一度 build+test されたが、REFUTED されたのは **「FORK-1 の fix 仮説」としてのみ** → dead branch revert (B0-1)。**その revert はその仮説に対して正しい。だが bank v2 が pin を要る理由は別 (fork-state の実現可能性) であり、当時それは問われていない。** ⇒ **「REFUTED-as-FORK-1-fix」を「env に pin は不要」の verdict として流用しない** (CLAUDE.md ハードストップ「ある方針の NO_ACTION / FAIL / 弱さを、別方針の GO 根拠として扱おうとしている」の裏返し)。同時に **DISCARDED 設計の独断復活も禁止** (§運用4 restore-of-banked-DISCARDED gate) ⇒ **どちらにも倒さず Rs へ上げる。**

**選択肢 (Rs / %12 裁定、当方は推奨を付さない — 前提 scope は Rs専権):**
- **(a)** pin を RL env へ配線 (新しい正当な理由で復活) — INVARIANT #5 scope 変更ゆえ Rs
- **(b)** bank を **k=1,2 に限定** (実測どおり pin OFF) — ただし **G3-G5 curriculum を失う = bank v2 の主目的そのもの**
- **(c)** curriculum を re-scope して carry 明記

**⭐影響範囲**: **B3a (producer capture + offline builder) は完全に無傷** — 本 chunk の artifact は producer の state を pin 込みで忠実に capture しており、その検証も完結している (legs 全 PASS)。**止まるのは B3b (env restore) の設計のみ。** (%9 も同判断)

⭐**meta (本 arc の新 sub-type、%9)**: C-α = 計器の感度 / C-β = mode の交絡 / E-4 = 較正の流用 / F-7.4 = 零は「対象が無い」か「計器が死んでいる」か区別不能 — そして **B3-α = 対象機構が *移植先に存在しない***。⇒ ⭐**移植の検証は donor (capture 忠実性) だけでなく recipient (受け皿の能力) を検査せよ。我々は capture を検証したが、restore に着地先があるかを誰も検証していなかった。**

### §9.1 ⭐%12 の追加測定 (03:45) — 問題は「bank が載らない」より深い

⭐⭐**(A) env は C1 を保持できない (実測)**。C1 着座 seg 27 の C1 からの距離:

| | t=255 | … | t=396 |
|---|---|---|---|
| **記録 (pin あり)** | **4.16mm** | **4.16mm 一定** | **4.16mm** |
| **env (pin なし)** | 1.08 | 5.76 → 14.14 → 25.80 → 41.20 | **52.87mm (単調離脱)** |

⇒ **env は reference trajectory が依存する機構を欠いている。** これは「bank の restore 先が無い」より深い: **pin 無しでは C1 着座そのものが保たない**。RL success 述語は `c1_final` を conjunct に持つ ⇒ ⚠**pin 無しで task が達成可能かどうかも open**。

⚠**(B) FORK-1 の根本原因が open に戻る (%12、断定はしない)**: **C1 離脱 runaway (t≈300-320) は grip divergence runaway (t≈337) に *先行* する**。かつ **c1pin「REFUTED」の evidence (`comp5_c2seat_fullfire_c1pin_result.json`) には「pin が実際に発火した」positive control が無い** (中身 = steps_run 342 / max_phase 3 / NUMERIC_NOGO のみ)。⇒ ⭐**spec F-7.4 の規律 (零・不在の測定は計器の死と区別できない ⇒ positive control を併走させよ) が、その規律を生んだ arc 自身の過去の REFUTED に適用される** ⇒ **当該 REFUTED は再検証を要する**。
⛔ ただし **同時に「REFUTED を『env に pin 不要』の根拠に流用しない」も守る** (prohibited.md)。**どちらの方向にも断定せず、Rs 裁定に上げる。**

⇒ **停止範囲 (%12 確定)**: **B3a = 影響なし (commit 可)** / **B3b = STOP (Rs 裁定まで着手しない)** / **B4-B7 も本件に依存**。BLOCKED_FOR_USER = `575069abe5`。

### §9.2 ⭐⭐ %9 の追走 (04:1x) — leg6 の index-space catch が「c1pin REFUTED」自体を開けた

⭐**私が leg6 で踏んで直した +1 罠 (Newton body id 55 vs MuJoCo body id 56) は、私だけの罠ではなかった。** %9 が reverted c1pin 実装 (`c70ba1b849`) を実読:

| # | 事実 | 含意 |
|---|---|---|
| 1 | 07-12 の c1pin は **eq を body id 経由で解決**しており、**私が初版 `resolve_pin_eq_index` で踏んだのと同一の +1 経路** | **同じ穴に 2 度目を踏むところだった** |
| 2 | ⭐**latch が fail-SILENT**: `self._c1_pin_done = True` が mjm/mjd の None check **より前**に、コメント自身が *regardless of outcome* と書いた上で焼かれる ⇒ **解決に失敗しても pin は無言で発火せず、assert ゼロ** | **「pin が実際に発火した」positive control が構造的に存在しない** |
| 3 | ⭐**c1pin run は 342 step で死亡 vs pin-less 499** (baseline 499 / cablediag 499 = diag 非摂動)。**保持 pin が正しく効いたなら生存は延びるはず。早死には「誤 body への溶接」の signature** | **c1pin の REFUTED は unsafe — 反証されたのでなく「試されていない」公算** |

⇒ ⭐**spec F-7.4 (零・不在は「対象が無い」か「計器が死んでいる」か区別できない ⇒ positive control を併走させよ) が、その規律を生んだ arc 自身の過去の REFUTED verdict に適用され、それを開けた。** 本 chunk で建てた **index-space round-trip assert + per-field liveness gate** が無ければ、同じ穴を 2 度踏んでいた (%9)。

⭐**%9 の confound 測定 (記録の pin 発火 = golden f2544 = phase 5→6 = replay t=255、pin は記録の 67% で ON):**

| 窓 | 構造差 | div_seg24 |
|---|---|---|
| **t < 255** | **記録も env も pin 無し ⇒ 構造差ゼロ (非 confounded)** | peak **10.56mm (t=124)** → **3.36mm へ減衰** = **暴走せず回復** |
| **t ≥ 255** | **env だけ pin 無し (confounded)** | 3.78 → **129.24mm**。⭐**collapse も drop も全部この窓** |

⇒ ⚠**FORK-1 の「発散する」は生きているが、「⇒ ゆえに落とす ⇒ ゆえに RL が唯一の fix」は未確立** (%12 + Rs へ上程済)。

⭐**本 conformance / 既 banked 値への影響 (%9 が先回りで判定):**
- ✅ **B2 の armed-quiet band 10.407mm / 本測定の 10.56mm = SAFE** — max は **t=124 = 非 confounded 窓**にある ⇒ **B2 の較正は無傷**。
- ⚠ **HOLD_THRESH = 15mm は confounded** — 初交差が **t=343 (≥255 の窓)** ⇒ **parity 基板 (pin あり env) で再導出が要る**。⚠**当方 chunk の落ち度ではなく基板側の欠損** (%9 明記)。⇒ **carry**: 既存の B7「MAX_HOLD 再導出」項に **HOLD_THRESH 再導出**を併記。**B2 は CLOSED ゆえ独断で再開しない** — Rs/%12 裁定に含めて処理。

## §6. spec 却下済 代替の記録

**FD による qd の「構築」= spec :140 が却下済 → 再審しない。** 本 v2 の L2 は **capture 済 qd の「検算」** であり構築ではない (記録の joint_q は既に存在する独立情報源 = F1)。この読みに異論があれば **STOP → ERRATUM 依頼**とする。
