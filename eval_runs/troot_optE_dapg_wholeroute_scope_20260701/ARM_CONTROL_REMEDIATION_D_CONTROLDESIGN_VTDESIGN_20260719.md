# (d) ARM-CONTROL REMEDIATION — CONTROL DESIGN (VT-DESIGN ruling)

**Author:** VT-DESIGN (w2:p5)。**Status:** DESIGN **v1.6（bank 待ち）** — **BANKED series**（最新 banked = v1.5 `a584be8545`、full 系譜 = 下記版表。A-P0-1′ 対応: 本 doc は banked 資産であり「0-commit」は doc 状態でなく**著者 pane 規律**〔p5 は commit しない・bank 執行 = %12〕を指す）。**(d) arc = Rs review v3 下 — 凍結/走行 gate = v1.6 bank + prereg v1.2 凍結後（Rs 順序 §7-7）**。probe evidence = 現在ゼロ（5-run batch = DIAGNOSTIC/非 evidence、`fa1e786b46` §2）。

### 版表（①、full SHA + stamp = dispatch 時 `date` 実測 JST）
| 版 | banked SHA | stamp (07-19) | 内容（1 行） |
|---|---|---|---|
| v1.0 | `0f39f7b598` | 08:14 | 初版: Q1-Q6 裁定 + M-1..M-6 + P-D1 probe spec |
| v1.1 | `ed24470097` | 08:26 | 訂正 #1: §5⇄§8-3 cadence 矛盾 → @4 走行（§0.0） |
| v1.2 | `3b5f75c131` | 09:02 | 訂正 #2: imported actuator 12 本発見 → Option B（M-1、§0.0） |
| v1.3 | `054ccf139a` | 09:42 | 訂正 #3: route-start pose bridge → (a-2) 境界 re-pose（§4 新 B row、§0.0） |
| v1.4 | `e32c75c3a4` | 10:45 | Rs review 対応: ③B1 裁定 / ④§7-5 supersede + L-P0 REQUIRED / ⑤仮説 tag / ⑥guard rename+時間意味論 / ⑦§8-2 UNVERIFIED / L-P5 再設計 mark |
| v1.5 | `a584be8545` | 11:26/11:43 | §12 = prereg v1.1 L-P5′/L-P2′ RATIFY + 精密化 2（11:26 dispatch）→ **Rs review v2 残 6 点 fold（11:43）**: ①A-P0-5 FF 実経路 site 列挙（§5 修正）②A-P0-6 run-matrix 表 ③A-P0-3 L-P0 defer 句削除+役割宣言 ④A-P1-3 negative control 再設計 = stale-target PRIMARY（§12.1、**§12-① L-P5′ を supersede**）⑤A-P1-4 re-pose 受入検査群 spec（§12.2）⑥P-P1-2 stamp 規約注記 |
| v1.6 | `f200bfd78c` | 12:30/12:44 | §12.2-R: Declared bands readback = **全 5 項 ACCEPT**（12:30。走行 GO は v3 §7-7 に superseded — 注記済）→ **Rs review v3 lane 4 点 fold（12:44）**: ①header BANKED 形式化 ②B2 fallback = STOP+design delta+p5/pN 再レビュー gate 明文 ③implicitfast 安定性 = 仮説 tag 軟化（authority = 経験 gate）④A-7 pin/eq ownership 検査を §12.2 suite へ追加 |

> **stamp/placeholder 規約（⑥ P-P1-2）**: stamp = dispatch 時 `date` 実測 JST。「bank = %12」SHA cell = bank 待ち placeholder（bank 後に %12 records-fix で実 SHA 充填、v1.4 先例 `c951a072d7`）。§0.0 narrative 内の「HH:2x」型 = 当時 verbatim の分丸め表記（exact anchor = 本表）。歴史注記: v1.4/v1.5 の stamp は当初 予測時刻を記入→dispatch 前に実測へ訂正した（10:52→10:45 / 11:29→11:26、date-THEN-write 違反の自己捕捉 2 回）。

### §0.0 訂正 narrative 履歴（v1.1-v1.3、verbatim — 各裁定の本文 fold 先は版表参照）
- v1.1 = **訂正 #1（%12 catch、08:23）**: §5⇄§8-3 の cadence 矛盾（§5=newton_route_env は RL path @4 ハード定数 `newton_skill_env_base.py:95`、§8-3 は「FF@producer-cadence(10)」と記載）→ **裁定 (a) P-D1 = @4 で走行**（§5/§8-3 を整合化。@10 被覆は S-2 producer gate へ移設、knob 追加なし）。
- v1.2 = **訂正 #2（%12 P-D1 pre-run finding `b9eaaf9d93`、08:54）**: M-1 の「XML actuator import に依存しない」前提が実測反転（flag-off build に imported arm actuator 12 本既存 nu=16・未配線 ctrl≡0 = 飽和 torque 隠れ綱引き・proto 配線は重複 24 本、p5 が diag log 3 本を自読 spot-check 済）→ **Option B 採択**（imported 無効化 + proto 配線、§1 M-1 改訂 + §5 L-P0 追加 + §7-5 substrate finding disposition）。M-1 旧前提 = 未検証 build 仮定（#11 と同 class の自認）。⭐L-P6 fail-able assert が走行前に捕捉 = 計器設計の vindication。
- v1.3 = **訂正 #3（%12 finding #2 `c1da5dcf54`、09:37）**: reset home ≠ recording frame-0（j0 |Δ|5.6 rad 級・p5 検算 = j4 3.57/左 j2 3.56 rad が wrap 非約分 = 別 configuration。banked kinematic FF は初回 RL step 内の hard teleport で橋渡し = 実測）→ **裁定 (a) 精密化採択 = route-start 境界の 1 回 re-pose（a-2）**: arm q := recording frame-0 **正確な記録 q 値**（winding 曖昧性も自動処理）+ qd:=0 + **ctrl := 同 pose（M-4）**、flag-gated・B-class（phase-k restore `:342-344` と同 class の 1 回/episode 境界 init）。**whole-reset seed（a-1）却下**: settle 条件まで変わり第 2 の delta + 81-cell 期の per-world settle 機構化 — (a-2) は banked kinematic が teleport で到達していた同一状態を同一 boundary で作る = 最小 delta。**(b) ramp+clock hold 却下**: 新 hold 機構 scope + 5.6 rad sweep の cable/table 衝突 risk + banked lineage が一度も物理 transit しなかった区間を transit する（忠実度は上がらない）+ episode 毎訓練 cost。guard: re-pose 境界で gripper OPEN ∧ 非把持 assert + LOUD log + npz flag。RL/trainer path へは「episode 開始 = script frame-0 seed」として同機構が退化適用。§1 FF-site impl gap fix（`apply_recorded_arm_ff` ctrl branch）= **spec-conformant ACK**（v1.2 §2 は両 site を規定済・plumbing 検証 PASS を確認）。§4 observation fold: **asserts は `mjw_data.ctrl` mirror を読まない**（gripper 実駆動中も all-zero = stale/非 operative 面 — Option A 却下理由②の追加 vindication: あの面への書込は inert だった可能性）。L-P4 は再目的化 = route-start teleport+sync 後 |q−ctrl| が frame 0 から transient bar 内に留まること（haul なし）の検証 + M-5 ramp は phase-k restore 等の残余不連続のみに適用。
**Input:** `ARM_CONTROL_REMEDIATION_D_ENGBRIEF_RSTECHLEAD_20260719.md`（commit `1ee8be5c9e` = HEAD、p5 全文読了）。
**Scope:** brief §4 Q1-Q6 + §5 staged approach への設計裁定。**実装認可ではない**（gate chain = §9）。Rs sign-off 前提（brief §0/§5-4）。

---

## §0 Grounding + gates

### §0.1 接地（p5 自読、file:line）
- 現 drive = kinematic 直書き: helper `apply_arm_only_write_broadcast`（`route_executor.py:213-215`、fk 1-world broadcast）+ `apply_arm_only_write_perworld`（`:236-238`、per-world jq_interp）— いずれも `phys_jq[arm]=target; phys_jqd[arm]=0.0`。call sites = `newton_route_env.py:1260`（RL per-step）/ `route_executor.py:5050`（§13.1 FF）/ `newton_route_env.py:810` `_broadcast_arm_jointq`（settle/hold）。
- gripper mirror（実証済 wiring）: builder proto `newton_skill_env_base.py:1636-1638`（`joint_target_mode=POSITION` + `joint_target_ke/kd`）→ SolverMuJoCo が mj actuator 合成（readback assert `newton_route_env.py:300-330`: `gainprm[0]=ke / biasprm[1]=-ke / biasprm[2]=-kd`、effort cap = **joint 側** `jnt_actfrcrange`）→ 駆動 = `control.joint_target_pos`（`route_executor.py:245+` `set_gripper_target`、solver が毎 step 読む）。
- vendor gains（UR5e MJCF）: `ur5e.xml:7-8` size3 kp=2000/kd=400/±150 N·m、`:15` size1 kp=500/kd=100/±28 N·m、`:9` armature=0.1、ctrlrange ±2π（elbow ±π `:11-12`）。
- cadence: `DT=1/480`（`newton_skill_env_base.py:93`）、RL path `RL_SIM_SUBSTEPS=4`→`RL_SIM_DT=1/1920`（`:95-96`）、producer path `SIM_SUBSTEPS=10`→`SIM_DT=1/4800`（`route_executor.py:1486-1487`、task_config.py:101）。RL step = 10 physics frame（`newton_route_env.py:404`）。solver = `SolverMuJoCo(solver="newton", integrator="implicitfast")`（`newton_skill_env_base.py:1332-1348`）— 陰積分ゆえ高 ke での離散安定性が**期待される〔一般論・仮説 tag、v1.6-③〕**。**安定性の authority = 経験 gate（probe 実測）であり本文言でない**（振動/発散が観測されれば文言でなく実測が governs、§8-4 感度枠へ）。
- 先行実測: arm PD on MuJoCo solver = **max_err 0.002 rad**（`LL-Newton.md:98` Franka Phase7、cable hybrid lift PASS）/ UR10e j0→0.5000 exact（`:189`）。

### §0.2 prior-art disposition（V7 gate 実行済）
`check_thread_vault_prior_art.sh --fail-on-blocker PD "arm control" kinematic joint_q gainprm` = BLOCKER_CONTEXT_FOUND。**内容 = comp3 gripper kinematic→POSITION-servo 移行（成功例・/pre-check PASS・same-pattern 先行事例）であり failed path ではない**。続行根拠 = (1) Rs 明示新 directive（"実施" L3 GO、brief `1ee8be5c9e`）(2) 発見 context は本移行の設計テンプレート（`COMP3_RULECHECK_STAGE2_COORD_20260708.md`: 「:670 28-wide reset-init = sanctioned reset-init」の分類先例を §4 で採用）。

### §0.3 [DEFER-RECON]（DDR × 本 chunk、reconciliation record）
| DDR | 依存判定 |
|---|---|
| #18 grip-slip（FOUNDATIONAL、IN-RESOLUTION） | **相互作用あり・GATE ではない**（#18=target 生成層、(d)=realization 層で直交）。sequencing 裁定 = §6 R-SEQ。(d) probe は #18 と独立に走行可 |
| #4 (d-b) non-crutch / #12 fork-B V0 | (d) rollout 後に (d-a)/(d-b) の anchor 再基線が必要（§7-3）。本設計 chunk 自体は非依存 |
| #19 ENV-MULTIWORLD（wc=1/proc） | probe/rollout は wc=1 で実行（fork-B 整合）。ctrl は per-world 配列ゆえ機構は wc 非依存 |
| #21 FM2 demos regen | **(d) stage-2 が demo 再生成をトリガ ⇒ #21 と単一 regen event に fold**（§6 R-SEQ2） |
| #2 P3 body_q sync-premise | 非依存（joint_q/ctrl 系、body_q 直書きなし） |

FOUNDATIONAL 未解決依存で本 **設計** chunk を block するものなし（#18 は impl sequencing のみ拘束）。

---

## §1 機構裁定 M-1〜M-6（HOW の骨格）

- **M-1 wiring = imported 無効化 + proto 配線（訂正 #2 = Option B）**: 実測（`pd1_probe_20260719/diag/dump_actuators_baseline.log`、p5 自読）= flag-off build は **nu=16 で ur5e.xml `<actuator>` が既に import 済**（act4-15 = 12 arm、vendor gains、両腕 joint 0-5/14-19 に name-map）だが **未配線**（arm dof `joint_target_mode=0`・`mjw_data.ctrl≡0`、`dump_ctrl_wiring.log`）。proto 配線を足すと**重複 24 本**（`run_smoke_pd.log` assert 実証）。⇒ 設計 = **(i) imported 12 本を無効化**（**裁定 v1.4-③（Rs 推奨 B1 に concur）: B1 strip-at-import = PRIMARY**〔nu=16 [12 proto + 4 gripper]・census 清潔・inert 検証負担なし・零化 actuator を solver 経路が別解釈する risk ゼロ〕。**B2 零化 = importer/builder 機構上 strip 不可能な場合のみの fallback — ⛔ 実装者単独では選択不可（v1.6-②、A-P0-2′）: B2 へ落ちる事象 = STOP + design delta 文書化（何が strip を阻むかの実測根拠）+ p5/pN 再レビュー gate を通過してのみ採択**。採る場合は static assert〔gainprm=biasprm=0 ∧ forcerange=0〕に加え **動的 force≡0 受入試験 REQUIRED**〔無効化 12 本の actuator force 読出 ≡0 を全 route horizon で assert、Rs 条件〕。現 probe 実装 = B2 ゆえ %12 が B1 再実装 → **O-1 の L-P0 診断は裁定機構下で再測**）**+ (ii) proto 配線**（12 arm driver DOF/world に `joint_target_mode=POSITION` + ke/kd + joint 側 `jnt_actfrcrange`、`:1636-1638` 同型）。**Option A（imported を直接駆動）却下 3 点**: ① fail-open — ctrl 書込漏れ経路の既定 = 飽和 pull-to-zero = 本 finding の欠陥そのもの（B の漏れ既定 = 直前 target 保持 = 良性）② `mjw_data.ctrl` 直書きは新規手書き device 面（wc>1 layout 未検証、pin arc の書込面 hazard class）vs `joint_target_pos` = 実証済み面 ③ gripper との機構統一。**L-P6 census 改訂**: 選択機構に応じ「arm 上の実効力源 = design 値の 12 本のみ」（重複ゼロ・inert 検証・gripper 4 本不触・**proto 値 ≡ 無効化した imported 値の数値一致 cross-check**〔同じ vendor 値を別機構で再実装するだけであることの証明〕）+ negative control。
- **M-2 駆動 = ctrl ストリーム置換（realization 層のみ変更）**: kinematic write が消費していた **同一 target ストリーム**を `control.joint_target_pos[arm_dofs]` に書く。`phys_jqd=0` 零化は**廃止**（速度は物理量になる）。target 生成層（IK / interp / FF indexing / `_per_world_fk_jq` chain）は**不変**。
- **M-3 command-space 原則**: interp/warm-start chain（`old_fk_jq`/`jq_starts`/`_per_world_fk_jq`）は**指令空間のまま**（realized q から再 seed しない）。理由: lag 下で measured-q 再 seed は軌道を歪め noise を target に結合する。recorded/IK 軌道 = authoritative、realized は obs/verify 用測定のみ。（#18 A2 の frame spec と整合 — あれも recorded=指令空間。）
- **M-4 teleport⇒target-sync 不変条件**: **許可される全 reset/restore teleport（§4 分類 B）は同一 turn で arm ctrl := 同じ pose を必ず設定**。さもないと PD が直後に stale target へ引き戻す（gripper が comp3 R1a で学んだ同じ罠 `newton_route_env.py:1098-1100` 系）。phase-k restore（`route_executor.py:342-344`）には banked **arm ctrl** の restore を追加（grip_target restore `:346-348` の arm 版）。
- **M-5 指令不連続の漸進化（ramp-in）**: 指令 jump > JUMP_TOL（提案 0.05 rad、任意 joint）が生じる遷移（settle→route 開始等）は **N_RAMP frame の線形 ramp**（提案 0.25s=120 frame @DT）で接続。force-design skill の「PD target 瞬間ジャンプ禁止」（FINGER_CLOSE_STEPS 先例）の arm 直適用。⇒ #18 A3 の step-0 pop は PD 下では**設計で消える**（teleport でなく bounded 物理遷移になる。kinematic 用 A3 verify leg は (d) 後 ramp-verify に置換、§7-2）。
- **M-6 arm tracking-divergence guard（v1.4-⑥ rename、旧称 anti-windup tripwire — 既存「tripwire」語彙〔make_solver 等〕との衝突回避。LOUD・非 reward 結合）**: kinematic は realized≡commanded を構造保証していたが PD は乖離し得る（障害物 stall 中も指令 chain が前進 = open-loop windup）。**時間意味論（v1.4-⑥ で明示）: per-joint `|q_realized − ctrl|` > `ARM_DIVERGENCE_BAR_RAD` が【N_DIV 連続 physics frame 持続】で発火**（瞬時 1-frame spike でも episode-max でもない — windup = 持続乖離ゆえ持続条件が正・正当な過渡 spike を false-trigger しない。counter は bar 下回りで reset — (d-b) K-dwell gap-reset と同規律）。発火 = physics-fault invalid episode（`EXPLOSION_DIST_THRESH` `newton_route_env.py:407` 同パターン: loud 終端・⛔reward/timeouts 不配線・npz flag）。**暫定値: N_DIV = 48 frame（0.1 s @DT=1/480）・bar = 訂正 probe の清潔基盤実測から導出して run 前凍結**（O-4 の持続 0.5 rad は confound 込みゆえ bar 導出に不使用）。probe にも同計測 leg（§5）。

---

## §2 Q1 裁定 — target-setting scheme

**採択 = (A) per-physics-frame ctrl ストリーム（kinematic が書いていたものと恒等）**:
- ik_chord/RL path: `ctrl := jq_interp[w]` を毎 physics frame（`newton_route_env.py:1260` の置換）。
- FF path: `ctrl := jq_ff[frame]` を毎 frame（`route_executor.py:5050` の置換、grip の `_REC_CADENCE` 1:1 と同型）。
- settle/hold: `ctrl := home 定数`（`_broadcast_arm_jointq` 系の置換 — PD 静的保持は最易ケース）。
- **IK 層は target 供給源のまま**（`solve_ik_dual`→jq_targets→interp→ctrl）。recorded `arm_q` 直結は FF path のみ（現状どおり）。

**却下 = (B) RL-step endpoint のみ ctrl 設定**（PD のステップ応答が軌道形状を変える・overshoot・recorded 軌道との対応喪失）。(A) は interp ランプを PD が追う形 = 速度比例の小さな定常 lag のみで軌道形状保存。

**§0#3 との関係**: target は従来どおり IK が生成（IK-based control 保存）、realization が forced-placement→物理 torque path になる = **#3/#5 を同時に満たす**（brief §6 と一致）。

---

## §3 Q2 裁定 — gains / limits / tolerance bar

### §3.1 gains v0（vendor 値採択、probe で検証）
| param | 値 | 根拠 |
|---|---|---|
| ARM_SERVO_KE size3（sh_pan/sh_lift/elbow） | **2000** | `ur5e.xml:7`（vendor/Menagerie 実績値） |
| ARM_SERVO_KD size3 | **400** | `ur5e.xml:7` biasprm[2] |
| ARM_SERVO_KE size1（wrist1/2/3） | **500** | `ur5e.xml:15` |
| ARM_SERVO_KD size1 | **100** | `ur5e.xml:15` |
| effort cap size3 | **±150 N·m** | `ur5e.xml:8` = **実機 spec。⛔上げるの禁止**（超過は sim-cheat = non-conservative、RS71 fidelity） |
| effort cap size1 | **±28 N·m** | `ur5e.xml:15` 同上 |
| armature | 0.1（既存 `:9`、不変更） | joint 既定 |

再 tune は probe が bar FAIL を示した時のみ（fix-first: まず iterations/経路で切り分け、gains は §8-4 感度枠内で）。⚠ MJCF `<default class>` 由来の joint 別差（size3 vs size1）を proto 書込時に正しく振り分けること（一律 2000 は wrist 過剛性）。

### §3.2 tolerance bar（暫定 → probe 後に凍結）
**参照 = 指令ストリーム（ctrl）**。kinematic はこれを恒等実現していたので、PD-vs-ctrl 誤差が移行 delta の全体。recorded 軌道比較は FF path（ctrl=recorded）で自動的に兼ねる。

| leg | bar（暫定） | 根拠 |
|---|---|---|
| per-joint 準静的（route/seat 中） | ≤ **2 mrad** | Phase7 実測 0.002 rad（`LL-Newton.md:98`）と同水準を要求 |
| per-joint 過渡（transit/ramp 中） | ≤ **5 mrad** | 準静的×2.5、probe で実測分布確認 |
| EE 位置 準静的（G3-G6 seat/push 中） | ≤ **1.5 mm** | seat lateral bar 3.5mm（`route_env_config` SEAT_LAT_BAR）の余裕を半分以上残す（tracking が bar margin を食い潰さない） |
| EE 位置 過渡 | ≤ **3 mm** | grasp 判別スケール（fingertip 6.3mm 把持 vs 22mm 逸脱、#18 実測）より十分下 |
| ARM_DIVERGENCE_BAR_RAD（M-6 guard） | 訂正 probe 実測から導出・run 前凍結（暫定発想 = 過渡 bar ×3） | windup 検出（N_DIV=48 frame 持続条件、v1.4-⑥）、physics-fault 扱い |

**凍結手順**: probe 実測 → p5 が bar を最終化 → **run 前凍結**（[[feedback-freeze-then-verify-then-bank-the-exact-sha]] / R4 先例「run 前固定」）。⛔ probe 結果を見て bar を後決めして PASS 宣言（gate-validated-under-the-bug）は禁止 — 暫定 bar で probe を採点し、変更するなら差分を宣言して再走。

---

## §4 Q3 裁定 — 16 sites 分類

**分類 A = per-step control-loop（migrate 必須 = 違反本体）** / **分類 B = reset/init/restore（許可・現状維持 + M-4 target-sync 追加）**

| site | 分類 | 処置 |
|---|---|---|
| `route_executor.py:213-215`（broadcast helper） | A（settle/hold 系 caller） | helper に ctrl 版を併設、caller 移行 |
| `route_executor.py:236-238`（perworld helper） | A（per-step drive 本体） | 同上 |
| `route_executor.py:342-343`（phase-k arm restore） | **B**（banked snapshot 復元 = reset-class） | 維持 + **arm ctrl restore 追加**（M-4） |
| `route_executor.py:344`（gripper restore） | B（既存分類どおり） | 不変 |
| `route_executor.py:1817/:1820`（STEP-1 probe/init block） | A（loop 内 per-step、`:1826` solver.step 直前） | 移行（probe infra ごと） |
| `newton_route_env.py:827`（settle hold） | A（持続 hold） | ctrl:=home 化 |
| `newton_route_env.py:1094`（reset re-pose） | **B**（sanctioned reset-init、comp3 「:670 28-wide」先例） | 維持 + ctrl:=settled 同 turn 設定（M-4） |
| `newton_route_env.py:1270`（RL per-step drive） | A（**主違反**） | ctrl:=jq_interp 化（§2） |
| `newton_skill_env_base.py:2080`（`broadcast_jointq_to_all_worlds`） | A（docstring 自認「every step, not a single set」） | ctrl 版へ |
| `aerial:475` | A（per-step arm write） | 移行 |
| `aerial:1090` | B（reset re-pose） | 維持 + M-4 |
| `aerial:1575` | A（per-step drive） | 移行 |
| `approach:419` | A（settle hold） | 移行 |
| `approach:746` | B（reset re-pose） | 維持 + M-4 |
| `approach:1203` | A（per-step drive） | 移行 |

| **route-start re-pose（新設、訂正 #3）** | **B**（1 回/episode 境界 init、phase-k restore 同 class） | arm q:=rec frame-0 正確値 + qd:=0 + ctrl 同期（M-4）+ OPEN∧非把持 assert + LOUD + npz flag |

計: **A=11（migrate）/ B=5+1 新設（許可+target-sync）**。Layer 8 baseline は A 消滅 + B 残置を反映して更新（B は「reset-init 例外」として checker に註記 — checker 変更は %12 court、L3）。

---

## §5 Q4 裁定 — de-risk probe spec（P-D1、%12 実行）

**目的 = brief §3 の pivotal unknown を最小コストで裁定**: 「MuJoCo arm PD は ±150/±28 N·m 下で（cable+gripper 負荷込み）記録軌道を bar 内追従するか」。

- **環境**: `newton_route_env` **FF whole-route**（(d-a) probe infra 再利用、nominal cell、wc=1、deterministic、cable ON・grasp ON・pin ON）。**cadence = RL path @4 のまま**（`RL_SIM_SUBSTEPS=4` `newton_skill_env_base.py:95`、knob 追加せず）— 根拠: ①trainer 基盤 = @4（DDR #18 title と同一 substrate、(d) の第一目的 = trainer 準拠基盤）②【**仮説 tag（v1.4-⑤）**】ctrl は frame 単位保持で substep はその内部積分 ⇒ @4 = 粗積分 = PD に等しいか厳しい側 = conservative — **解析的導出であり未実測**（PASS@4⇒@10 も推論。S-2 で confirm、反例 = loud re-open。裁定 (a) の非仮説根拠は ①③）③基線対照は @4-vs-@4 の同 cadence で cadence 効果が contrast から消える（1 変数規律。@10 knob 追加は #18 substep-confound 軸への再進入 + scope creep）。**probe の PD-write surface 全列挙（v1.5-①、A-P0-5 修正）**: (s1) `apply_recorded_arm_ff` の ctrl 書込（`route_executor.py`、**FF 実経路 = 本 probe の主 site**）/ (s2) `newton_route_env.py:1270` 系 = **RL path であり FF probe では不実行**（S-1 移行対象、probe 対象外）/ (s3) route-start re-pose（訂正 #3 (a-2)、B-class）/ (s4) harness M-4 ctrl sync。⚠honest note: v1.0-v1.4 §5 の「移行対象 = :1270 系のみ」は誤り — §2 は FF site（route_executor `:5050` 域）を正しく規定しており **§2⇄§5 の自己不整合**が %12 初回 branch の mis-wiring（finding#2 §1）に寄与した（%12 は自己帰属したが設計 doc 側の誤導が先行）。実験 flag（`ARM_PD_DRIVE=1` 系）で切替 — reset 系 B は不変。read-only branch / 未 land。
- **基線**: 同 build・同 seed の kinematic 走行 = **flag-off AS-IS（imported 綱引き込み・banked substrate と byte 同一）**。**宣言 delta 裁定（訂正 #2）**: PD-vs-基線 contrast = 移行 delta = 〔realization 置換 + artifact（綱引き）除去〕の合成。artifact は現 arm-drive realization の一部（準拠 PD 設計なら必然的に消える）ゆえ主 contrast から除去すべき confound ではない — **成分分離は L-P0 が担う**。
  0. **L-P0 contamination magnitude（v1.4-④: REQUIRED に昇格）**: kinematic + imported 無効化（③裁定 = B1 機構）vs kinematic 現状、同 seed — 綱引き成分単独の軌道/述語 divergence を定量。**banked evidence caveat の規模判定材料**（Rs 材料、§7-5）。O-1 diagnostic（B2 機構下）= g3 242→never の完全消滅を既に示唆 — B1 下で evidence-grade 再測（verification legs + video leg 付き）。
- **測定 legs**:
  1. **L-P1 tracking**: per-joint |q−ctrl| 時系列 → phase 別 max/p99（§3.2 bar 採点）+ EE 誤差（FK(q) vs FK(ctrl)）。
  2. **L-P2 predicate parity**: grasp（fingertip l/r_near）/ G1-G3 latch / pin fire（fire_step・anchor）/ seat metrics / retention / drop 有無 — kinematic 基線との対照表。⚠ **一致は期待値でない**（timing shift は想定内）: 採点は「G 系到達 + fire≺release + retention 保持」の述語成立で行い、frame 番号差は宣言 delta として記録。⚠**v1.4 re-scope（O-1/O-4 confound）: 基線連鎖自体が artifact 依存と判明 ⇒ 「基線との parity」= characterization に降格（acceptance でない）。acceptance 意味論（清潔基盤で何を要求するか）= prereg v1.1 で再定義**（「PD が recording を追従できない」と「recording の連鎖が artifact を要求する」の分離が訂正 probe の中心課題）。
  3. **L-P3 effort**: per-joint actuator force 時系列 → saturation 率（cap 到達 frame 数 / 全 frame）。**saturation >1% で WARN、>5% で bar FAIL**（力不足 = 追従不能の前兆）。
  4. **L-P4 route-start 整合（v1.3 再目的化を本文 fold）**: route-start teleport+ctrl 同期（訂正 #3 (a-2)）後、**|q−ctrl| が frame 0 から過渡 bar 内に留まること**（haul なし）の検証。M-5 ramp は phase-k restore 等の残余不連続のみに適用（O-2 diagnostic: 同期開始下で ramp 有無 = byte 恒等 = 再目的化の期待どおり、corroboration）。
  5. **L-P5 negative control（fail-able 計器の証明）**: gains ×0.1 走行 = bar **FAIL すること**（[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test]]）。⚠**v1.4: 設計どおりでは判別失敗（O-3 diagnostic: ×0.1 max 0.493 vs ×1.0 0.512 rad — 分離せず）→ prereg v1.1 前に再設計 REQUIRED**（方向 = step-response/settling time 観測量 or bar-set 変更。%12 input → p5 ratify。この regime では tracking-max が gains に鈍感 = 計器として dead という実測）。
  6. **L-P6 build readback**: arm-servo-readback assert（M-1）が 12 actuator/world・gain/bias/effort 一致を報告。
- **成立 bar**: L-P1/L-P3 が §3.2 暫定 bar 内 ∧ L-P2 述語成立 ∧ L-P5 FAIL ∧ L-P6 PASS。
- **run matrix（v1.5-②、A-P0-6。REQUIRED 5 + exploratory 1、GPU 数分・訓練なし）**:

| run | 内容 | pass-role（decision での役割） |
|---|---|---|
| R0 | 汚染基盤 kinematic AS-IS | characterization のみ（acceptance でない）+ L-P0 入力 |
| R0b | 清潔基盤 kinematic（B1-strip） | **L-P2′ acceptance 参照** + L-P0 入力 |
| R1 | PD（system under test） | L-P1/L-P3/L-P4/L-P2′ の被験体 |
| R2 | PD + ramp | 機構 no-regression（≈R1 期待、乖離 = LOUD 異常報告・bar なし） |
| R3 | **stale-target negative control（§12.1 PRIMARY）** | 計器較正 + bar fail-ability 実証（採点 = intended-stream 比、§12.1 条件） |
| R4（optional） | ×0.1 gains | **exploratory 降格**（§12.1）— 非 gating・走れば gain 感度の参考 |

- **L-P0 の役割宣言（v1.5-③、A-P0-3 残）**: L-P0（= R0-vs-R0b 対照）は **REQUIRED-to-RUN**（欠落 = probe 成果物不完全）だが **probe の pass 条件ではない** — 出力 = **impact assessment であり、banked（歴史）evidence の再利用を gate する**（§7-5 caveat row に接続、再利用可否の scope 判断 = Rs）。probe verdict（PD feasibility）とは独立に報告される。旧「defer するなら 4 走行」句は v1.4-④ REQUIRED と矛盾のため削除。
- **video leg**: PD 走行の動画を Rs へ（motion-bearing sim ⇒ mandatory；Rs motion 標準 `p2r_c11_route.mp4` と並べて）。

**probe 結果の分岐**: PASS → §6 rollout へ / FAIL(tracking) → gains 感度枠（§8-4）→ 再走 / FAIL(saturation) → **軌道再設計 or 速度 profile 検討 = 別チャンク**（brief §3「re-tuning / re-trajectory effort」側へ分岐、Rs 報告）。

---

## §6 Q5 裁定 — staged rollout + sequencing

### R-SEQ（#18 との順序）
**裁定 = probe は今すぐ並行可、impl landing は #18 が先**:
1. **P-D1 probe（§5）= 今**（read-only、#18 と非干渉 — #18 の GO-now 測定も read-only で完了済）。
2. **#18 impl（A1/A2/A3）を現 kinematic 基盤で land + 再測**（v2.2 re-debate → impl。#18 の evidence base は kinematic 上で構築済 — その基盤で決着させる = 1 変数規律）。
3. **(d) rollout（下記 stage）**: #18 決着後に drive 移行 → #18 DoD（ik_chord=FF match）を **PD 基盤で再検証**（stage gate に内蔵）。
- 根拠: 逆順（(d)→#18）は「新 PD 動力学 × 既知 wrong-branch 破局」の 2 未知同時になる。また A1 branch guard は PD 下で**より load-bearing**（cross-branch target jump が物理 sweep として実行され cable を実力で撹乱するため）— #18 は (d) によって不要化しない（re-debate でこの点を明示可）。
- Rs/%12 が逆順を選ぶ場合の条件: #18 の全 evidence を PD 基盤で取り直すこと（現 evidence の substrate が変わるため）。

### stages（各 stage: L3 chain + Rs sign-off + video leg）
| stage | 内容 | re-validation gate |
|---|---|---|
| S-0 | P-D1 probe（§5） | probe bar 全成立 + bar 凍結 |
| S-1 | `newton_route_env` + `newton_skill_env_base:2080` 移行（FF+ik_chord+settle） | route 再現 vs Rs 動画標準 / grasp G1-G3 / seat parity / **(d-a) probe 再走 + anchor 再基線（宣言 delta、§7-3）** / #18 DoD 再検証 |
| S-2 | `route_executor`（producer）移行 | **golden/demo 再記録 = DDR #21 と単一 regen event**（旧 lineage は NOT_COMPARABLE 明示 — Phase0 規律） |
| S-3 | `aerial` / `approach` skill envs | 各 env smoke + 既存 test suite（route track 非依存ゆえ最後） |

**R-SEQ2（計画面反映）**: (d) は training-ready critical path に挿入される（trainer は準拠基盤で走るべき、C7 の解消として Rs が remediation を選択）。plan surface 反映 = %12 bank 後に p6 custody。

---

## §7 Q6 裁定 — trainer / pin / anchors 相互作用

1. **pin 例外 = 不変**: pin は body_q/eq 書込（`route_executor.py:792-794` 系 + eq 機構）で joint_q に触れない ⇒ Layer 8 非対象のまま・本移行と直交。**(d) は pin の実装面を 1 行も変えない**（brief Q6 の confirm、p5 設計として保証）。
2. **residual-on-script**: 意味論が「script が recorded **状態**を実現」→「script が recorded **target** を指令、PD が実現」へ精密化。obs は実状態を読むので closed-loop 補償可能 = **#18 と同じ closed-loop 動機の強化**。ただし **demos は kinematic 実現状態の記録**ゆえ S-2 で再記録必須（§6）。obs の joint 速度由来量は零→実速度に分布変化（bounded by tracking bar、regen で吸収）。
3. **(d-a)/(d-b) anchors**: fire_step/anchor 凍結値（live 2462 等）は kinematic-lineage。S-1 で **(d-a) probe を PD 基盤で再走し、§8.13 drift-loud 原則そのままに新 standing anchor を宣言 delta 付きで再基線**（bar 構造 = fire≺release / band / 順序は不変、番号のみ更新）。(d-b) は onset 窓を持たない設計（§9 charter）ゆえ構造変更なし — K-dwell の K=3 は physics-frame 単位で PD 下でも同一 cadence（`:1221` per-frame call 不変）、ただし **K の余裕（flicker）を S-1 で 1 leg 再確認**（PD の微小追従振動が capture 述語を flicker させないか）。
4. **fork-B/#19**: wc=1/proc に ctrl 機構は自然適合。wc>1 復活時は arm-servo readback の per-world 複製 assert（gripper `:314-317` 同型）が守る。
5. **substrate finding disposition（v1.4-④ で SUPERSEDE — v1.2 文言は over-claim を含んだ、旧文 = `3b5f75c131` 参照）**: 旧「banked contrast verdict は内部的に有効・遡及 flip なし」を**軟化・再述**: banked verdict が有効なのは【汚染基盤上の記録として】のみ。**O-1（diagnostic-grade、`fa1e786b46` §3）= 零化のみ（kinematic drive 不変）で banked 把持連鎖が消滅（g3 242→never / pin never / done=horizon）= 綱引きは banked 連鎖に load-bearing**（受動的背景でない — review P0-4「state-dependent, can interact」の実証形）⇒ **基盤を超えて意味を持つ主張（物理妥当性・RS71 §4 fidelity・transfer・「route は物理的に成立する」）= 清潔基盤上で UNVERIFIED**。review P0-4 に従い、decision-critical contrast は訂正基盤での再走対象。**L-P0 = REQUIRED に昇格**（旧 RECOMMENDED を supersede）— ③裁定機構（B1）下で再測 + verification legs + video leg を伴って evidence 化。**#18-contributor 仮説 = 推測 tag 維持・ただし plausibility 上方更新**（把持連鎖の tug 感度が単一 diagnostic で実測された — fold は依然禁止〔single run・video なし・B2 機構 caveat・O-4 confound〕）。caveat custody = %12 bank → DDR/LEDGER + p6 relay、scope 判断 = Rs。

---

## §8 force-design protocol 出力（skill 必須 4 点）

### 8-1 パラメータ表
| param | 現在 | 変更後 | 置場 |
|---|---|---|---|
| arm drive 方式 | kinematic 直書き（16 sites） | POSITION servo（A=11 migrate / B=5 維持+sync） | §4 |
| ARM_SERVO_KE/KD size3 | —（未配線） | 2000 / 400 | **task_config.py 新設**（SSOT、gripper `:314-316` 並び） |
| ARM_SERVO_KE/KD size1 | —（未配線） | 500 / 100 | 同上 |
| ARM_EFFORT size3/size1 | —（∞ 相当 = kinematic） | ±150 / ±28 N·m | 同上 + `jnt_actfrcrange` |
| JUMP_TOL / N_RAMP / TRIP | — | 0.05 rad / 120 frame / 15 mrad（暫定） | 同上（probe 後凍結） |

### 8-2 階層整合性
| 層 | ke | 上位との関係 | 判定（v1.4-⑦: 全行 = 設計意図、実測検証 = L-P3 + 訂正 probe） |
|---|---|---|---|
| Arm PD | 2000/500 | 最上位（位置を決める） | **UNVERIFIED** |
| Gripper servo | 66.7（`task_config.py:314`） | < Arm（把持は arm 位置に従属） | **UNVERIFIED** |
| effort: arm ±150/±28 ≫ gripper 2.5 N·m | — | arm が把持反力に負けない | **UNVERIFIED**（⚠ O-4 diagnostic: wrist_2 持続 ~0.5 rad 誤差 = size1 28 N·m 飽和の示唆 — ただし O-1 confound 込みゆえ結論不可、訂正 probe の仕事） |
| cable/contact（mujoco solref 系） | — | Arm PD が接触力に勝つこと = **L-P3 saturation leg で実測検証**（既知負荷: dual-load r_grip_N=119.3 @GOLDEN、静的 cable 45g は無視可） | probe 待ち |

「Arm positioning > contact transmission > grasp compliance」の設計序列は保存（gripper 66.7 と arm 2000/500 の比較は座標次第 [rad vs m] ゆえ、序列の最終確認も L-P3 の実測 effort で行う）。

### 8-3 dt 依存性
- 積分 = `implicitfast`（陰）⇒ ke=2000 @ dt=1/1920〜1/4800 の離散安定性は堅牢（陽積分の ke·dt² 制約に非拘束）。
- ⚠ **2 cadence を両方検証（訂正 #1 で整合化）**: RL path（substeps=4、dt=1/1920）と producer path（substeps=10、dt=1/4800）で PD 実効挙動が異なり得る（既知の 10-vs-4 mismatch と同根）。**P-D1 = @4**（trainer 基盤〔事実〕・conservative 側〔**仮説 tag、v1.4-⑤**〕・1 変数対照〔事実〕= §5 根拠 ①-③）/ **@10 = S-2 producer 移行 gate で native 検証**（route_executor は @10 が native ゆえ knob 不要、基線も @10 同士）。PASS@4⇒PASS@10 は推論であり S-2 で confirm — S-2 @10 が @4 より悪い追従を示したら（予想と逆方向）loud 異常として gains re-open。

### 8-4 感度テスト枠（probe 内 or FAIL 時）
| leg | 範囲 | 期待 |
|---|---|---|
| ×0.1（negative control、必須） | ke/kd ×0.1 | bar FAIL（計器が fail-able である証明） |
| ×0.5 | | 追従劣化の傾向確認（FAIL 時の下界） |
| ×1.0（v0） | | bar 内 |
| ×2.0（optional、FAIL 時のみ） | | 振動/overshoot 有無（⛔ effort cap は不変のまま） |

---

## §9 invariants / STOP / gate chain

- **§0#1-#5 不触**を設計で保証: dual-arm（両腕とも同機構で移行）/ 88mm・base 不変 / **#3 = IK が target 源のまま**（強化: 実現が物理化）/ コ-gripper 不触（gripper servo 系は 1 行も変えない — `:344` restore の B 維持含む）/ **#5 = pin 例外のみ**（§7-1）。設計 option が invariant に触れる分岐（例: 軌道再設計で grasp span 変更が浮上）= **STOP + Rs**。
- **effort cap を実機 spec 超に上げる提案は本設計で禁止**（fidelity 非保守方向）。追従不能なら軌道/速度 profile 側で解く（別チャンク、Rs）。
- gate chain（brief §5 を具体化）: **P-D1 probe（%12、prereg + 基線 + bar 凍結）→ p5 probe 結果裁定（bar 凍結最終化）→ L3 chain（rule-check → CC-Debate、impl diff 対象）→ S-1 impl（fenced、Rs sign-off）→ stage gates（§6）→ two-key（p5 設計軸 + pN evidence 軸）**。
- 本 doc = 設計裁定であり **実装認可でない**。probe prereg は %12 起草（P-D1 spec を §5 から転記 + run 前固定）。

## §10 p5 が %12 に要るもの（次 action、v1.4 = Rs HOLD 下の訂正 chain）
1. v1.4 bank + ③ B1-strip 再実装（+ B1 census readback）。
2. L-P5 再設計 input（O-3 対応、step-response/settling 方向 or bar-set 変更案）→ **p5 ratify**。
3. prereg v1.1 再凍結（review ①-④ 着地後。L-P0 REQUIRED + L-P2 acceptance 意味論再定義 + L-P5 新観測量込み）→ evidence-grade 走行（video leg 付き）→ 結果 dispatch。
4. probe 結果を受け p5 が bar 凍結 + §3 gains 最終化（FAIL 分岐なら感度枠 §8-4 / effort 飽和なら軌道側 = 別チャンク + Rs）。
5. bank 時: LEDGER/DDR 反映（(d) 行 + §7-5 caveat row）= %12 → p6 relay。R-SEQ（#18 先行 landing）の court 側 concur は継続項目。

## §12 prereg v1.1 ratification（v1.5、設計軸 — 対象 = `ARM_CONTROL_PD1_PROBE_PREREG_RSTECHLEAD_20260719.md` draft、p5 全文読了）

**① L-P5′ = RATIFY（as-is）**。p5 独立検算: {lift, elbow}（arm-local {1,2,7,8}）は size3 cap 150 N·m ≫ UR5e 重力 torque（~50-60 N·m 級）ゆえ **両 gain scale で非飽和線形域** → 定常誤差 = G/(scale·kp) ∝ 1/scale、×0.1 で ~10× 期待・bar 3× は margin。O-3 の死因（wrist_2 = 飽和域では誤差が cap 支配 = ke 鈍感）を正しく回避する観測量選択。ratio 基準 = scale-free で noise floor にも robust。W = min(14000, 10·done_R1, 10·done_R3) = 共通 prefix 保証（R1 早期 drop でも成立）。「不分離 = probe INVALID（FAIL でなく計器無効）」の意味論 = 正。

**② L-P2′ = RATIFY + 精密化 2（freeze 前 fold、bar 追加なし）**。3 分離（追従性 = L-P1/L-P3 自 ctrl stream 比〔chain 非依存〕/ artifact 依存 = L-P0 / acceptance = 清潔基盤 R0b parity）は v1.4 §5 L-P2 re-scope の正確な操作化。
- **P-1（parity-in-failure 対策）**: O-1 diagnostic のとおり R0b が把持連鎖を失うなら、R1-vs-R0b の predicate parity は「両者同 class で失敗」に退化し判別力が落ちる（a-test-that-cannot-come-out-differently の部分形）。→ **R1-vs-R0b の連続量 divergence（EE 軌道 + body_q 由来 cable proxy、per-frame、既存 log から offline 導出）を REPORTED leg として追加**（本 probe は bar なし・S-1 で bar 候補化）。predicate 行が退化しても比較が情報を保つ。
- **P-2（空窓の採点意味論）**: phase split の quasi-static 窓 = [g3_step, done] は **g3 不発火で空窓** → その場合 quasi-static bar（≤2 mrad）は **PASS でなく N/A-empty-window と報告**（vacuous PASS 禁止 — 採点されなかった leg を PASS と記録しない、records-match-fact）。transient bar（≤5 mrad）は全 frame で bind し続ける。
- 非 block nit 2: (n-1) §2 の「TRIP (M-6)」行名 → v1.4-⑥ 改名に合わせ `ARM_DIVERGENCE_BAR_RAD` candidate（informational、意味論不変）。(n-2) R0 の census は assert なしの**記述的記録**（nu=16・imported LIVE）を provenance に残す（N/A 扱いのままで可）。
- **sequencing note（prereg 変更でない、Rs surface）**: L-P0 が清潔基盤での連鎖崩壊を evidence 化した場合、S-1 の再検証 gate「route 再現 vs Rs 動画標準」は **choreography 側で blocked** になる（realization の問題でなく記録された振付が artifact 依存）→ (d) rollout の再 sequencing（清潔基盤での demo 再記録を S-1 検証より前へ = #21 fold の前倒し）が必要になり得る。判断 = Rs。

**verdict: 両 leg RATIFY〔設計軸〕・P-1/P-2 fold 後に凍結 → evidence 走行可**。凍結 commit の版表反映 + 走行後の bar 凍結最終化 = §10 chain のまま。⚠ §12-① L-P5′ は **§12.1 で supersede**（11:31 %12 自己 supersede 提案 → p5 精査の上 RATIFY。§12-① の検算自体は当時の設計に対し健全 — より強い計器への置換であり撤回でない）。

### §12.1 A-P1-3 negative control 再設計 = stale-target PRIMARY を RATIFY（v1.5-④、条件 1 付き）

- **採択**: R3 = **決定論 stale-target**（ctrl を recording frame-0 に全走行凍結）。期待誤差曲線 = **`|rec[t] − rec[0]|` per joint = npz から閉形式 precompute 可能** ⇒ (i) 計器配線の end-to-end 較正（測定 curve が precomputed curve と一致すること）(ii) bar fail-ability の実証（rad 級誤差が L-P1 bar を必ず超える = fail する走行が実在しパイプラインが flag する）を **1 走行で両立**。×0.1（旧 L-P5′）より強い: 期待値が物理仮定なしの決定論・smoke-2 で偶然実証済み。**×0.1 = R4 exploratory 降格 concur**（非 gating）。
- **⛔ RATIFY 条件（p5 検出の罠）**: stale 走行の採点 stream を **明示的に intended-stream（recording）比 `|q − rec[t]|`** と定義すること。自 ctrl stream 比（L-P1 の既定 = `|q − ctrl|`）で採点すると q ≈ frozen ctrl → 誤差極小 → **negative control が vacuous PASS 化**（計器を検証するはずの走行が計器の既定に騙される、gate-validated-under-the-bug の直系）。一致判定 = precomputed curve との per-joint 偏差 ≤ band（band = PD hold 定常誤差 G/kp 級 + noise、prereg で宣言・凍結）。INVALID 意味論継承: band 超過 = **計器 INVALID**（probe FAIL でない）。
- 副次: stale 走行は arm が frame-0 保持のまま = cable 不接触の良性走行（把持なし・horizon 完走見込み）。

### §12.2 A-P1-4 route-start re-pose 受入検査群 spec（v1.5-⑤、p5 spec → %12 実装）

全て LOUD-fail（raise、probe-blocking）。発火回数 = episode 毎 exactly 1（`route_start_repose_count==1`）。

| # | 検査 | 述語（exact） |
|---|---|---|
| A-1 | 値の忠実性 + limits + winding | seeded q[arm 12] == rec[frame0] を許容 ε=1e-9 で一致（**正規化・wrap 折返し禁止** — winding は正確値継承で自動保存）∧ 全 seeded q ∈ [qmin, qmax]（model limits） |
| A-2 | M-4 sync | 直後に ctrl[arm] == seeded q（ε=1e-9）∧ qd[arm] == 0 |
| A-3 | cable 不変 | re-pose 書込の前後（solver step を挟まず）で cable 状態 slice（pos+vel）が byte 恒等（teleport は arm joint_q/ctrl のみに触れる証明） |
| A-4 | 貫通/接触 impulse | re-pose 直後の初 physics frame: arm 関与 contact pair の penetration ≤ ε_pen（宣言値）∧ cable の frame 間 `max\|Δv\|` ≤ band（R0b 同 frame 比、宣言値）— teleport された arm が cable/table/clip と交差していないこと |
| A-5 | gripper 状態 | OPEN ∧ 非把持（訂正 #3 既存 guard を本 suite に fold） |
| A-6 | provenance | recording sha256 == prereg pin ∧ frame-0 行 index == 0 を記録 |
| A-7 | pin/eq ownership 不整合なし（v1.6-④、A-P1-1 残） | re-pose 書込の前後（solver step を挟まず）で clip-pin eq 状態 slice（eq_active flags + eq anchor/data 配列）が byte 恒等 ∧ 境界での期待状態 = pin 未発火（fired flag False・onset None・audit counter 0）を assert — **re-pose は eq を activate/deactivate/re-anchor しない・eq ownership は pin 機構（authorize_clip_pin 経路）に排他帰属のまま**（INVARIANT#5 の例外面に re-pose が触れないことの機械保証） |

band/ε_pen の数値 = prereg 凍結時に %12 が宣言（p5 readback で確認）。

**§12.2-R readback 完（v1.6、12:30）**: prereg v1.1 凍結 `879df7945a` の §3 Declared bands 表を on-disk 照合 = message と全 5 項一致、p5 独立検算で **全 ACCEPT**: ①較正 band 0.06+5%·predicted（hold sag ≲0.04 基礎と整合・罠実証 0.007 vs 0.758 = catch class を桁判別）②ε_pen 3mm（正常貫通 1.1mm と teleport 交差を分離・GLOBAL min = spec の保守的上位集合）③Δv max(2×R0b 同 frame, 0.01)（scale-free + floor、R0b 先行順序確認）④M-6 48frame/15mrad report-only（v1.4-⑥ 一致）⑤L-P1 = |q−ctrl| + `max|ctrl−intended|≤1e-9` cross-check・R3 のみ intended 比（**§12.1 ⛔条件 discharge + R1/R2 配線 bug も封じる強化形として ACK**）。註 1: ①の band class = stream 同一性/粗配線の較正であり frame-exactness は A-2/A-6 が担う（band を frame offset 検出に読み替えない）。**6 走行（R4 exploratory 込み）開始 OK**。⚠**12:35 SUPERSEDED（Rs review v3 §7-7）**: 本 GO は v3 の gate（凍結/走行 = v1.6 bank + prereg v1.2 凍結後）に先行して発行されたため無効 — 走行保留、band ACCEPT 自体は有効のまま（v1.2 凍結時に継承）。
