# (d) ARM-CONTROL REMEDIATION — CONTROL DESIGN (VT-DESIGN ruling)

**Author:** VT-DESIGN (w2:p5)。**Drafted:** 2026-07-19 08:1x JST。**Status:** DESIGN v1.0 — 0-commit（bank = %12）。
**Input:** `ARM_CONTROL_REMEDIATION_D_ENGBRIEF_RSTECHLEAD_20260719.md`（commit `1ee8be5c9e` = HEAD、p5 全文読了）。
**Scope:** brief §4 Q1-Q6 + §5 staged approach への設計裁定。**実装認可ではない**（gate chain = §9）。Rs sign-off 前提（brief §0/§5-4）。

---

## §0 Grounding + gates

### §0.1 接地（p5 自読、file:line）
- 現 drive = kinematic 直書き: helper `apply_arm_only_write_broadcast`（`route_executor.py:213-215`、fk 1-world broadcast）+ `apply_arm_only_write_perworld`（`:236-238`、per-world jq_interp）— いずれも `phys_jq[arm]=target; phys_jqd[arm]=0.0`。call sites = `newton_route_env.py:1260`（RL per-step）/ `route_executor.py:5050`（§13.1 FF）/ `newton_route_env.py:810` `_broadcast_arm_jointq`（settle/hold）。
- gripper mirror（実証済 wiring）: builder proto `newton_skill_env_base.py:1636-1638`（`joint_target_mode=POSITION` + `joint_target_ke/kd`）→ SolverMuJoCo が mj actuator 合成（readback assert `newton_route_env.py:300-330`: `gainprm[0]=ke / biasprm[1]=-ke / biasprm[2]=-kd`、effort cap = **joint 側** `jnt_actfrcrange`）→ 駆動 = `control.joint_target_pos`（`route_executor.py:245+` `set_gripper_target`、solver が毎 step 読む）。
- vendor gains（UR5e MJCF）: `ur5e.xml:7-8` size3 kp=2000/kd=400/±150 N·m、`:15` size1 kp=500/kd=100/±28 N·m、`:9` armature=0.1、ctrlrange ±2π（elbow ±π `:11-12`）。
- cadence: `DT=1/480`（`newton_skill_env_base.py:93`）、RL path `RL_SIM_SUBSTEPS=4`→`RL_SIM_DT=1/1920`（`:95-96`）、producer path `SIM_SUBSTEPS=10`→`SIM_DT=1/4800`（`route_executor.py:1486-1487`、task_config.py:101）。RL step = 10 physics frame（`newton_route_env.py:404`）。solver = `SolverMuJoCo(solver="newton", integrator="implicitfast")`（`newton_skill_env_base.py:1332-1348`）= 陰積分 ⇒ 高 ke でも離散安定性は堅牢。
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

- **M-1 wiring = gripper mirror そのまま**: builder proto で **12 arm driver DOF/world**（`_ARM_OVERWRITE_LOCAL` = {0-5,14-19} 対応 qd-index）に `joint_target_mode=POSITION` + `joint_target_ke/kd`（値 = §3）+ joint 側 `jnt_actfrcrange=±effort`（`:1636-1638` 同型）。⛔ ur5e.xml の `<general>` actuator import には依存しない（operative path = proto→SolverMuJoCo 合成、gripper と同じ）。**arm-servo-readback assert**（`newton_route_env.py:300-330` の arm 版: mj actuator 存在数 = 12/world・gain/bias/effort 照合 + negative control）を build 時必須に。既存 gripper assert（`servo_acts==4` は gainprm==66.7 filter ゆえ arm 追加と非衝突 — ke=66.7 を arm に使わない限り。§3 の値は非衝突）。
- **M-2 駆動 = ctrl ストリーム置換（realization 層のみ変更）**: kinematic write が消費していた **同一 target ストリーム**を `control.joint_target_pos[arm_dofs]` に書く。`phys_jqd=0` 零化は**廃止**（速度は物理量になる）。target 生成層（IK / interp / FF indexing / `_per_world_fk_jq` chain）は**不変**。
- **M-3 command-space 原則**: interp/warm-start chain（`old_fk_jq`/`jq_starts`/`_per_world_fk_jq`）は**指令空間のまま**（realized q から再 seed しない）。理由: lag 下で measured-q 再 seed は軌道を歪め noise を target に結合する。recorded/IK 軌道 = authoritative、realized は obs/verify 用測定のみ。（#18 A2 の frame spec と整合 — あれも recorded=指令空間。）
- **M-4 teleport⇒target-sync 不変条件**: **許可される全 reset/restore teleport（§4 分類 B）は同一 turn で arm ctrl := 同じ pose を必ず設定**。さもないと PD が直後に stale target へ引き戻す（gripper が comp3 R1a で学んだ同じ罠 `newton_route_env.py:1098-1100` 系）。phase-k restore（`route_executor.py:342-344`）には banked **arm ctrl** の restore を追加（grip_target restore `:346-348` の arm 版）。
- **M-5 指令不連続の漸進化（ramp-in）**: 指令 jump > JUMP_TOL（提案 0.05 rad、任意 joint）が生じる遷移（settle→route 開始等）は **N_RAMP frame の線形 ramp**（提案 0.25s=120 frame @DT）で接続。force-design skill の「PD target 瞬間ジャンプ禁止」（FINGER_CLOSE_STEPS 先例）の arm 直適用。⇒ #18 A3 の step-0 pop は PD 下では**設計で消える**（teleport でなく bounded 物理遷移になる。kinematic 用 A3 verify leg は (d) 後 ramp-verify に置換、§7-2）。
- **M-6 anti-windup tripwire（LOUD・非 reward 結合）**: kinematic は realized≡commanded を構造保証していたが PD は乖離し得る（障害物 stall 中も指令 chain が前進 = open-loop windup）。**per-step `max|q_realized − ctrl|` > TRIP（= transient bar ×3、§3）で physics-fault 扱い**（`EXPLOSION_DIST_THRESH` `newton_route_env.py:407` と同パターン: loud 終端・⛔reward/timeouts 不配線・npz flag）。probe にも同計測 leg（§5）。

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
| TRIP（M-6） | = 過渡 bar ×3（15 mrad） | windup 検出、physics-fault 扱い |

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

計: **A=11（migrate）/ B=5（許可+target-sync）**。Layer 8 baseline は A 消滅 + B 残置を反映して更新（B は「reset-init 例外」として checker に註記 — checker 変更は %12 court、L3）。

---

## §5 Q4 裁定 — de-risk probe spec（P-D1、%12 実行）

**目的 = brief §3 の pivotal unknown を最小コストで裁定**: 「MuJoCo arm PD は ±150/±28 N·m 下で（cable+gripper 負荷込み）記録軌道を bar 内追従するか」。

- **環境**: `newton_route_env` **FF whole-route**（(d-a) probe infra 再利用、nominal cell、wc=1、deterministic、cable ON・grasp ON・pin ON）。**移行対象 = per-step drive（:1270 系）のみ**を実験 flag（例 `ARM_PD_DRIVE=1`）で切替 — reset 系 B は不変。read-only branch / 未 land。
- **基線**: 同 build・同 seed の kinematic 走行（**1 変数差 = realization のみ**。[[feedback-same-constant-is-not-same-measurement-surface]] の統制直適用）。
- **測定 legs**:
  1. **L-P1 tracking**: per-joint |q−ctrl| 時系列 → phase 別 max/p99（§3.2 bar 採点）+ EE 誤差（FK(q) vs FK(ctrl)）。
  2. **L-P2 predicate parity**: grasp（fingertip l/r_near）/ G1-G3 latch / pin fire（fire_step・anchor）/ seat metrics / retention / drop 有無 — kinematic 基線との対照表。⚠ **一致は期待値でない**（timing shift は想定内）: 採点は「G 系到達 + fire≺release + retention 保持」の述語成立で行い、frame 番号差は宣言 delta として記録。
  3. **L-P3 effort**: per-joint actuator force 時系列 → saturation 率（cap 到達 frame 数 / 全 frame）。**saturation >1% で WARN、>5% で bar FAIL**（力不足 = 追従不能の前兆）。
  4. **L-P4 step-response**: settle→route 開始遷移（M-5 ramp 有/無 各 1 走行）で overshoot / settle time 実測 → JUMP_TOL/N_RAMP 数値確定。
  5. **L-P5 negative control（fail-able 計器の証明）**: gains ×0.1 走行 = bar **FAIL すること**（[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test]]）。
  6. **L-P6 build readback**: arm-servo-readback assert（M-1）が 12 actuator/world・gain/bias/effort 一致を報告。
- **成立 bar**: L-P1/L-P3 が §3.2 暫定 bar 内 ∧ L-P2 述語成立 ∧ L-P5 FAIL ∧ L-P6 PASS。
- **規模/コスト**: 走行 = 基線1 + PD1 + ramp1 + neg1 = **4 走行 ×〜771 frame、GPU 数分・訓練なし**。
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
| 層 | ke | 上位との関係 | 判定 |
|---|---|---|---|
| Arm PD | 2000/500 | 最上位（位置を決める） | ✅ |
| Gripper servo | 66.7（`task_config.py:314`） | < Arm ✅（把持は arm 位置に従属） | ✅ |
| effort: arm ±150/±28 ≫ gripper 2.5 N·m | — | arm が把持反力に負けない | ✅（定量は L-P3 実測） |
| cable/contact（mujoco solref 系） | — | Arm PD が接触力に勝つこと = **L-P3 saturation leg で実測検証**（既知負荷: dual-load r_grip_N=119.3 @GOLDEN、静的 cable 45g は無視可） | probe 待ち |

「Arm positioning > contact transmission > grasp compliance」の設計序列は保存（gripper 66.7 と arm 2000/500 の比較は座標次第 [rad vs m] ゆえ、序列の最終確認も L-P3 の実測 effort で行う）。

### 8-3 dt 依存性
- 積分 = `implicitfast`（陰）⇒ ke=2000 @ dt=1/1920〜1/4800 の離散安定性は堅牢（陽積分の ke·dt² 制約に非拘束）。
- ⚠ **2 cadence を両方検証**: RL path（substeps=4、dt=1/1920）と producer path（substeps=10、dt=1/4800）で PD 実効挙動が異なり得る（既知の 10-vs-4 mismatch と同根）。P-D1 は FF@producer-cadence で実行、S-1 gate に RL-cadence leg を含める。

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

## §10 p5 が %12 に要るもの（次 action）
1. P-D1 prereg 起草 + 走行（§5、4 走行 + readback）→ 結果 dispatch（artifact path）。
2. probe 結果を受け p5 が bar 凍結 + §3 gains 最終化（FAIL 分岐なら感度枠 §8-4 へ）。
3. R-SEQ 順序（#18 先行 landing）の %12 court 側 concur or 逆順希望の表明（逆順条件 = §6）。
4. bank 時: 本 doc + brief の LEDGER/DDR 反映（(d) 行新設）は %12 → p6 relay。
