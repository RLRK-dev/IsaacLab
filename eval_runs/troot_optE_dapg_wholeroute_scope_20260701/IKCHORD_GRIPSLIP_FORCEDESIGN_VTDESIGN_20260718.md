# ik_chord grip-slip — force-design（VT-DESIGN）

**Author:** VT-DESIGN (w2:p5)。**Drafted:** 2026-07-18 10:2x JST。**Status:** DESIGN v1.3 — 0-commit（bank = %12）。v1.1 = §10 M2-branch lever=arm-path 選択 / v1.2 = §10.6 phase 修正受領（%12 §2: mid-route 右腕離脱、approach/grasp でない）+ discriminator pre-register + guard / v1.3 = §10.7 H-b CLASS confirm・H-a REFUTED（on-disk verify）だが **lever は ~10× に未確定** — sub-fork M-b1 within-step-shape(~10×)/M-b2 endpoint config-orient divergence(cheap)、on-disk が M-b2 を示唆（position-only+held-KO IK・ik_resid=position のみ・magnitude 疑義）。 / v1.4 = §10.8 **M-b2 CONFIRMED**（%12 P2: 右腕 4.32rad 別 IK branch）→ lever 確定 = **recorded-branch IK seed（cheap、~10× でない）** + design-gate（/diffik-trajectory PASS + /pre-check inline）。 / v1.5 = §10.9 **/pre-check verdict = WARN**（0 crit/2 high/2 med/1 low + 3 guards）→ AMEND-1..5 fold（⭐**AMEND-1 confirmed defect**: seed-only は step-0 の within-step interp START[`old_fk_jq` :1246 = 別 read]を wrong branch に残す → **両 read を recorded branch に pin**; AMEND-5: arm は **kinematic re-pose**[PD でない、:236/:1272]）。design = **WARN-with-amendments**、impl は %12/Rs sign-off + L3。 / v1.6 = %12 O1（AMEND-1 side-effect）を design-axis で確定: **`_per_world_fk_jq`-ONLY**（`_settled_fk_jq` 触らず — `:1094` reset arm re-pose の arm-vs-body mismatch 回避、p5 on-disk verify）。%12 L3 CC-Debate spawned（PROPOSE=`IKCHORD_GRIPSLIP_FIX_L3_PROPOSE_RSTECHLEAD_20260718.md`）。 / **v2.0 = §10.10 L3 CC-Debate = FAIL-revise**（mechanism CONFIRMED airtight・fix DIRECTION sound だが AMEND-2 の HIGH inconsistency[branch guard 欠落]+necessity/coverage 未証）→ 設計改訂: **A1 branch/flip guard on jq_targets**（cross-branch を `:1254` に流さない、AMEND-2⇄AMEND-1 self-consistent 化）+ A2 frame spec（old_fk_jq=step_f/jq_starts=next_f）+ A3 step-0 pop accept+verify。[VERIFY] scope: B4 pin-ON necessity/B5 whole-route coverage(C2_REGRASP ~step500)/B6 boundary-crossing robustness。⭐C7 Rs surface: kinematic arm drive の §0#5 trainer 認可（§0-adjacent）。 / v2.1 = §10.11 [VERIFY] scope 精緻化(%12+pN 入力): **B4 = RESOLVED BY ANALYSIS**(p5 pin-design CONFIRM — pin call は FF-only `:1225`・pin は C1 clip segment retain で drop する gripper-midpoint segment `:1621` を hold 不能・g3=false で never fire ⇒ pin は fix を moot しない)+ B4-shadow(fire=0∧G3=false 観測、runnable now)。B5 split: B5a FF whole-route+ik_chord partial(pre-impl)/B5b post-fix ik_chord whole-route+C2_REGRASP(post-impl、drop@267 で pre-fix 到達不能)。⭐⭐**(d-b) PREREQUISITE**: #18 grip fix は (d-b) の上流 gate(grip hold→C1 seat→pin fire; 現 slip は g3 前で pin never fire)→ #18→(d-b)→training-ready(DDR 記録要=%12/p6)。measure-first pre-impl=B4-shadow+B5a+B6-char。
**Trigger:** Rs 裁定 A（grip-substep-decouple L3 [VERIFY] FAIL、前提反証）→ ik_chord grip-slip root を p5/force-design へ escalate（`IKCHORD_GRIPSLIP_FORCEDESIGN_ESCALATION_RSTECHLEAD_20260718.md`）。
**入力:** L3 verdict `GRIP_SUBSTEP_L3_DEBATE_VERDICT_RSTECHLEAD_20260718.md` + escalation + measure `grip_retention_measure/` + `ikchord_deadlock_render/{run,run_ff}.log` + p5 code 自読。
**L = L3**（solver/contact/ik = physics keyword）。**substep = REFUTED — design around しない**。**本 doc は設計であって実装認可でない**（gate PASS 後の %12 impl）。
**⭐ 前提受理**: 私の前 substep 設計は **confounded pair 比較**（recording mujoco@10 dual-arm vs measure mujoco@4 ik_chord = 2 変数差）で誤前提。L3 が **FF@4 HOLDS / ik_chord@4 DROPS**（同 substep=4、drive のみ差）で反証。slip = **drive-dependent**。SUPERSEDED = `GRIP_SUBSTEP_DECOUPLE_DESIGN_VTDESIGN_20260718.md`（mark 済）。

## §1 root（L3-established、p5 on-disk 再確認）
- **drive-dependent**: `ikchord_deadlock_render/run_ff.log`（drive=feedforward・全 300 step・reward −0.01 = HOLDS）vs `run.log`（drive=ik_chord・drop step 267・−10）。同 recording・同 `apply_recorded_grip`・同 substep=4、**arm drive のみ差**。
- **右腕 22mm 未接触 = single-arm hold**: `per_step_metrics` step 254-267 = `contact_r=False`・`r_near≈0.022m` **一定**・`grip_r=1.0` 命令（= dual-grip 相・regrasp transit でない）。GOLDEN@10 は **dual load で保持**（`l_grip_N=21.5, r_grip_N=119.3` — ⭐右腕が把持力の大半を担う）。⇒ ik_chord で右腕が 22mm off → 左単腕保持 → **fast lateral escape**（l_near 0.013→0.065 over 262-264 = axial creep floor 60.4µm/f の 10-480×、slow creep でない）。
- Rs video-GT: ik_chord で cable が **clamp 時に softens して slip out**（有効 finger↔cable friction なし）。⇒ 単腕保持下の lateral 保持失敗の視覚、または contact/solref 因子。

## §2 mechanism 曖昧性（lever 選択前に diagnose 必須 — 原因仮説を裏付けよ / 対処療法禁止）
ik_chord target = **recorded 把持 pose**（`:1187` `target_r = base_r(route recorded 6D) + proj_residual`；golden 決定 replay は residual≈0 ⇒ target = recorded 右腕 把持 pose = cable 上）。にも関わらず r_near≈22mm。**なぜ右腕が 22mm off か**は 3 機構に分岐、現データで判別不能（measure は r_near を記録するが `_last_ik_resid` を記録せず）:
| 機構 | 予測 signature | 対応 lever |
|---|---|---|
| **M1 IK 非収束** | `_last_ik_resid[R]≈22mm`（EE が target に届かない）| IK iters ↑ / warm-start / step-size（**DiffIK 内**）|
| **M2 target-vs-cable / cable 変位** | `_last_ik_resid[R]≈小`（EE は target 到達）だが r_near≈22mm（cable が target から離れた）| 左 grip contact/solref が cable を動かす → 左 contact/solref、or target/phase |
| **M3 左 contact 自体が単腕で保持不能** | 右腕を engage しても slip 継続 | MUJOCO_PAD_SOLREF（contact 二次因子）|
⭐ **key 数値証拠**: `IK_ITERATIONS_RL=30`（`:99`）≪ `_AC_IK_ITERATIONS_P0=400`（`:204`「88mm span convergence needs generous count」）⇒ **M1（per-step IK が tight dual-arm 88mm 把持を 30 iter で収束せず）は有力候補**だが未確定。

## §3 diagnostic probe（fix 前、cheap = residual は既算）
`_last_ik_resid`（`:1290-1291`、obs [55:57] = R,L IK residual、**既に毎 step 計算**）を記録する probe を ik_chord@4 slip 窓（step 254-267）で再走:
- **記録**: `_last_ik_resid[R]`（右腕 residual）/ `targets_right` vs 最近傍 cable body（target が cable 上か）/ `r_near`（EE-cable）/ recorded 右腕 EE pose vs ik_chord 解 pose（config 差）。+ 左腕同項。
- **判別**: residual[R]≈22mm → **M1**（IK 非収束）/ residual[R] 小 ∧ r_near 22mm → **M2**（target 到達だが cable 変位）。
- **control**: FF@4 の同記録（HOLDS 側の residual/r_near = baseline）— 差分で ik_chord IK path の逸脱を定量。
- ⚠ probe harness は **有効 run config を記録**（`measure_grip_retention.py:82-84` は module 定数 `RL_SIM_SUBSTEPS` を assert/記録 = 実効 config でない、CC5 CH1 = false-provenance；probe は effective substeps/backend/drive を記録）。

## §4 mechanism → lever map（/force-design、invariant 制約付き）
diagnose 結果に応じ lever を確定。**primary root = 右腕 engagement 復元**（GOLDEN dual load r_grip_N=119.3 が示す通り右腕が主把持力 ⇒ 右腕 22mm off は contact/friction lever で不可達 — solref を上げても 22mm 先の cable に触れない）:
- **M1（IK 非収束）→ lever = DiffIK 収束改善**: `IK_ITERATIONS_RL` 30→N（P0 の 400 側へ）/ warm-start 改善 / step-size。⚠ **DiffIK-only 不変**（control 方式変更でない・iter 数は tuning）。⚠ **no-kinematic-trick 不変**（teleport/強制配置でなく IK 解の収束）。cost: iter↑ は throughput 影響（N×10 frame）— sensitivity 要測。
- **M2（cable 変位）→ lever = 左 contact/solref or target**: cable が離れる機構を特定（左 grip の overdamped solref が cable を弾く? arm-path が shear?）→ MUJOCO_PAD_SOLREF softening or target/phase。
- **M3（単腕で保持不能）→ lever = MUJOCO_PAD_SOLREF**（二次、右腕復元後も slip 継続時のみ）。
**solref 単独は primary でない**（右腕 22mm off に contact lever は不可達）— M2/M3 の二次因子としてのみ。

## §5 candidate levers /force-design 分析
| lever | 層 | 変更 | dt 依存 | hierarchy | 感度/risk | invariant |
|---|---|---|---|---|---|---|
| **IK_ITERATIONS_RL 30→N**（M1）| IK 収束 | iter 数のみ（`:99`）| なし（iter は dt 非依存）| force param 不変・階層保存 | N↑ で収束↑・throughput↓（N×10f/RL）; over-iter で振動なし（LM step 1.0）| ✅ DiffIK-only・no-trick（IK 解の収束） |
| **MUJOCO_PAD_SOLREF softening**（M2/M3）| pad↔cable contact | solref 2 値（`task_config.py:187` −65789,−2105）| ⚠ solref は dt 依存の damped-spring — softening は creep/release 特性を変える | contact 層のみ・Arm/servo 不変 | R6 は「best」既往（SRG:109）; softening は overshoot/penetration risk | ✅ contact param（control 方式外）; ⚠ task_config = L3 SSOT |
| **target/phase**（M2）| route target | recorded 6D or phase | なし | — | recorded target 改変は S5 byte-repro risk | ⚠ recorded target 改変が dual-arm/88mm を崩すなら **STOP+Rs**（premise change） |

## §6 invariant guard（⛔ 触れたら STOP+Rs — RS71 §0）
- **dual-arm**: 右腕 engagement 復元は **dual-arm 前提を回復**する（単腕 hold = 前提逸脱の症状）⇒ 復元は invariant 遵守方向。
- **88mm span**: `GRIP_HALF_SPAN=0.044`（span 88mm）不変。IK 収束改善は span を変えない。
- **DiffIK-only**: IK iter/warm-start/step-size = DiffIK 内 tuning（control 方式変更でない）。⛔ JT-IK / kinematic teleport 禁止。
- **コ-geometry / no-kinematic-trick**: 右腕を cable へ **teleport/強制配置しない**（IK 解で到達）。gripper geometry 不変。
- ⚠ **判定基準**: どの lever も上記を変えるなら build せず **STOP → BLOCKED_FOR_USER → Rs**（premise change = Rs 専権、§0 FOUNDATIONAL）。現候補（IK iters / solref）は §0 不変前提を変えない（tuning）— ✅ build 可（gate 後）。

## §7 /pre-check failure modes（pre-empt）
| # | FM | mitigation |
|---|---|---|
| FM1 | diagnose せず lever 選択（symptom patch）| §3 diagnostic を fix 前に必須（原因仮説裏付け）|
| FM2 | IK iters↑ が 22mm を閉じない（M1 でなく M2）| diagnostic が M1/M2 判別・M2 なら別 lever |
| FM3 | solref softening が右腕 22mm off に無効（不可達）| §4「solref は primary でない」明示・M3 二次のみ |
| FM4 | re-measure harness false-provenance（CC5）| probe/re-measure は effective config 記録（module 定数でない）|
| FM5 | re-measure DoD が r_near（右腕）を見ない（CC4: §7 旧 DoD は l_near/held_z/G3 のみ）| DoD に **右腕 contact_r + r_near + dual-load** を追加 |
| FM6 | lever が §0 invariant に抵触 | §6 guard・STOP+Rs |

## §8 gate chain / DoD
1. 本 design → **design-gate**: /force-design（§5）+ /pre-check（§7）。
2. **⭐ §3 diagnostic probe 実行**（fix 前、mechanism 確定 — 原因仮説裏付け）→ M1/M2/M3 判別。
3. mechanism 確定 → §4 lever 確定 → **L3 CC-Debate**（lever の premise verify）+ rule-check。
4. **%12 impl**（確定 lever、explicit-path atomic、§6 invariant 遵守）。
5. **re-measure（FIXED harness）**: ⚠ `measure_grip_retention.py:82-84` の false-provenance 是正（effective config 記録）→ ik_chord で grip 保持（**右腕 contact_r=True + dual load 復元** + l_near<0.012 維持 + held_z floor 非 trip + **G3 到達**）。
   - holds → #18 resolved。 not → escalate（solref 二次 or Rs）。
6. wc=1 fork-B bind・L3。§DDR #18（p6）は「fix=TBD via p5 force-design（drive/solref）; substep REFUTED」へ re-qualify（p6、Rs 裁定後）。

## §10 §3 diagnostic 受領 → M2-branch lever 選択（v1.1、2026-07-18 11:0x — 入力 `IKCHORD_GRIPSLIP_DIAGNOSTIC_RESULT_RSTECHLEAD_20260718.md` + p5 on-disk 再確認）
**diagnostic 結果（airtight, control-isolated, read-only）**: `ik_resid_r=0.24mm` 両 drive（EE は target pose 到達）⇒ **M1（IK 非収束）REFUTED**（IK_ITERATIONS_RL=30 で足りる・iters lever は drop）。`fingertip_r_to_cable`: FF **6.3mm**（把持）vs ik_chord **22mm**（未把持）、**同 target pose** ⇒ **M2 CONFIRMED = ik_chord drive path が cable を FF 比 ~16mm 変位**・右腕未把持 → 左単腕 → escape。22mm は窓全体 **persistent**（displacement は **early〔approach/grasp〕確立**）。solref 単独 不採（22mm 先に不可達、再確認）。

### §10.1 🔒 lever branch 選択 = **arm-path**（target/phase は却下）
%12 提示 3 sub-branch から:
- **target/phase = ⛔ 却下**: 右腕は recorded 把持 target pose に **到達済**（ik_resid 0.24mm）。target 値・timing は正 ⇒ target/phase mismatch でない。
- **arm-path（右腕 approach 1 / 左腕 config 2）= 採択**: 同 end pose で cable が path により変位 ⇒ root は **drive の arm-PATH**（trajectory）であって end target でも contact でも IK 収束でもない。⇒ **/diffik-trajectory 領域**（/force-design の solref/contact でない）。

### §10.2 /diffik-trajectory 接地（drive mechanism、p5 自読）
ik_chord drive = **[one-shot IK solve `:1235`] + [linear JOINT interp `:1253-1254`]**（`jq_interp = old_fk_jq + (jq_targets−old_fk_jq)·t`、10 frame）。IK は previous pose から warm-start（`:1173` jq_starts = `:1246` old_fk_jq = 前 step per_world_fk_jq）⇒ per-step config jump は小（warm-start 連続）。**しかし linear JOINT interp は EE 空間で curved path**（FK 非線形）— /diffik-trajectory ⛔絶対原則「one-shot target 禁止・時間/joint 補間の大移動は curved sweep」。FF は recorded arm_q（実 smooth trajectory）を replay ゆえ非変位。⇒ ik_chord の joint-chord path が cable を sweep/変位。⚠ **本文中「early〔approach/grasp〕確立」は §10.6（%12 §2 diagnostic）が SUPERSEDE** — displacement は approach/grasp でなく **mid-route 右腕 disengagement（onset step 176）**、grasp 自体は成功（step 90 両指先 2mm）。curved-sweep 機構は成立するが phase は mid-route（下記 §10.6）。

### §10.3 ⚠ 右腕(1) vs 左腕(2) sub-mechanism 未 isolate → cheap discriminating diagnostic（%12 提示、fix 前）
現データは右腕 22mm を示すが **どちらの arm-path が cable を変位させたか**未確定（右腕 approach が knock / 左腕 config が cable を bend）。%12 提示の cheap read-only 診断で pin:
- **left-arm `fingertip_l_to_cable`**（FF vs ik_chord）: 左も off なら両腕 path・左のみ正常なら右 approach 特定。
- **cable-body displacement trace**（どの segment が・いつ・どちらの arm 運動と相関して動くか）。
- **per-phase FF-vs-ik_chord EE path + joint-config deviation**（early approach/grasp のどの phase で 16mm が入るか・config-jump か interp-curvature か）。
⇒ 結果で lever を §10.4 から確定（原因仮説裏付け・対処療法禁止 = sub-mechanism 未確定で lever 固定しない）。

### §10.4 lever map（sub-mechanism → /diffik-trajectory lever、invariant/policy/cost 付き）
| sub-mechanism | lever | /diffik-trajectory | invariant | policy 互換 | cost |
|---|---|---|---|---|---|
| **右腕 approach path curvature（H-b interp）** | **task-space 漸進 EE interp**（EE target を frame 毎に増分・IK per frame、joint-linear でなく）= 小 Δx canonical DiffIK | ⛔「one-shot 禁止・漸進目標」直適用 | ✅ DiffIK 内・no-trick | ✅ policy target にも straight path | ⚠ 10 IK solve/RL step（10×、要 sensitivity）|
| **右腕 IK config-jump（H-a）** | **IK config continuity 強化**（null-space bias / warm-start 改善で config jump↓）| config 連続 | ✅ DiffIK 内 | ✅ | 安（1 solve）|
| **左腕 config が cable を bend（2）** | 左腕 approach/config path 修正（同 /diffik-trajectory） | 同上 | ✅ | ✅ | — |
⭐**invariant guard（§6 再掲）**: task-space interp / config-continuity は **DiffIK 内 tuning**（control 方式変更でない）・右腕を **teleport せず IK 解で到達**（no-kinematic-trick）・dual-arm/88mm/コ 不変。lever が §0 前提を変えるなら STOP+Rs。**⛔ solref/contact は primary でない**（M2 = path、contact 不可達）。
⭐**policy 互換 必須**: fix は replay だけでなく **policy 駆動 target でも**変位しないこと（ik_chord drive mechanism の修正であって recording copy でない）。

### §10.5 gate chain / DoD（更新）
本 §10 lever branch（arm-path）+ §10.3 discriminating diagnostic → sub-mechanism 確定 → §10.4 lever 確定 → design-gate（/diffik-trajectory + /pre-check）→ L3 CC-Debate → impl → **re-measure（FIXED harness + 右腕 `fingertip_r_to_cable`/`contact_r`/dual-load DoD、CC4/CC5）**。wc=1 fork-B・L3。

### §10.6 phase 修正受領（%12 §2 diagnostic）→ discriminator pre-register + lever cost（v1.2, 2026-07-18 11:2x — 入力 `IKCHORD_GRIPSLIP_DIAGNOSTIC_RESULT_RSTECHLEAD_20260718.md` §2:40-47, on-disk 再確認）
**phase 修正（%12 §2、既存 per-step data・no GPU）**: displacement は approach/grasp でない — **mid-route 右腕 disengagement**。
- **grasp 成功**: step 90 両指先 ~2mm（dual grip 確立、FF 同等）⇒ approach/grasp 変位でない（§10.2「early」を supersede）。
- **右腕 mid-route 離脱**: `fingertip_r_to_cable` が FF から onset **step 176**（11mm vs FF 4.4mm）発散 → **step 195 で 52mm spike** → ~22mm 定常（route_t 177-196）。FF 右腕は全 route ~6mm 把持。
- **右腕 primary・左腕 demote**: 左腕は step 261 まで把持（5-10mm）→ drop 267 で spike。系列 = dual OK → **右腕 mid-route 離脱(176-195)** → 左単腕 → 左離脱(261) → drop(267)。左腕 sub-branch(2) は primary でない（52mm spike の coupling 要因としてのみ open）。
- ⇒ **fix surface = 右腕の 176-195 route motion に localize**（approach/grasp/grip 不触）— narrower/cheaper。

**⭐ substep REFUTED の機構的説明（phase 修正で補強、L3 verdict と整合）**: substep（integration granularity）は 1 RL step の **fixed な jq_interp path を n_sub frame で刻むだけ**で EE の幾何 path を変えない（`_physics_step_all:799-807` は per-RL-step jq_interp を substep loop で積分）。ik_chord の 176-195 curved EE sweep は **drive の path geometry**（one-shot IK `:1235` + linear joint interp `:1253-1254`）由来ゆえ substep 4→10 で不変 = cable 依然 swept。⇒ L3 の FF@4-holds/ik_chord@4-drops は「**drive が EE path geometry を決め、substep は path 上の積分粒度のみ**」で機構的に説明（substep 前提反証の root cause）。

**pre-registered discriminator（%12 が 176-195 判別中 — lever を deterministic に、原因仮説裏付け）**: 3 仮説を **1 instrument で分離**するには per-step/frame で **joint-delta ∧ EE-vs-chord ∧ cable-motion を相関記録**が必要条件（1 量のみは confound = single-variable isolation 違反、[[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]] §0）:
| 仮説 | signature（176-195 window） | lever | /diffik-trajectory | cost |
|---|---|---|---|---|
| **H-a config-jump（右腕）** | ‖jq_targets−old_fk_jq‖[R] が特定 waypoint で spike/discontinuity（IK branch flip）・EE 曲率が config jump と相関 | IK config continuity（null-space bias / warm-start 強化）| config 連続化 | 安（1 solve/step）|
| **H-b interp-curvature（右腕）** | joint-delta smooth（flip なし）だが EE が EE-chord から bulge（FK 曲率）| task-space 漸進 EE interp（per-frame IK・joint-linear でなく）| ⛔「one-shot 禁止・漸進目標」直適用 | ⚠ ~10 IK/step（要 sensitivity）|
| **左腕 coupling（52mm spike）** | 右 EE path straight だが cable-body が左腕運動と相関して移動 | 左腕 approach/config path 修正 | 同 | — |

⭐**guard 1（confound）**: joint-delta のみ → H-a 検出可だが H-b と区別不能；EE のみ → 曲率は見えるが config-jump 由来か FK 曲率か不能；cable-motion 欠 → 右 EE 離脱か cable 移動（coupling）か不能。**3 量相関が判別の必要条件**（欠けると誤 lever = L3/impl サイクル浪費）。
⭐**guard 2（H-b の cheap lever 誤選択防止）**: H-b の fix は (a) task-space EE interp（per-frame IK、~10×）or (b) route waypoint 密度↑（joint-interp segment 短縮）のみ。**substep 増・interp frame 増は H-b を fix しない**（同 EE 幾何 path を細かく積むだけ、上記機構）。cheap lever に飛ばない。
⭐**invariant/policy**: 全 lever は DiffIK 内 tuning・右腕を IK 解で到達（no-kinematic-trick）・dual-arm/88mm/コ 不変・**policy 駆動 target でも path straight**（recording copy でない）。§0 抵触なら STOP+Rs。

**次**: %12 discriminator（3 量相関 @ 176-195）→ H-a/H-b/coupling 確定 → 本表から lever 確定 → design-gate（/diffik-trajectory + /pre-check）→ L3 CC-Debate → impl → re-measure（FIXED harness + 右腕 `fingertip_r`/`contact_r`/dual-load + **176-195 window 監視** DoD）。

### §10.7 diagnostic (2)(3) 受領 → H-b CLASS confirm・H-a REFUTED / **lever は ~10× に未確定**（on-disk 機構精査、v1.3, 2026-07-18 11:4x — 入力 `IKCHORD_GRIPSLIP_DIAGNOSTIC_RESULT_RSTECHLEAD_20260718.md` §3:49-62 + §4:64-79 + p5 code 自読 `:955`/`:970-995`/`:1005-1006`/`:1216`/`:1254`/`:1290`。§10.6 H-b row を sub-fork に分割・refine）
**diagnostic 受領（on-disk verify、両 leg 実測）**:
- **H-a（config-jump）REFUTED**: §3 `dJointQ`@176-195 = median 0.0093（max 0.0183、**no spike**）vs baseline 0.0066 ⇒ config smooth（flip なし、warm-start `:1173` 機能）。cheap H-a config-continuity lever は正当に **OUT**。
- **H-b CLASS confirmed**: §4 cable-seg world-move = ik_chord **80.8mm**（腕 END 33.4mm の **2.4×**、spike 14mm@186-187）vs FF 33.9mm（≈腕、追従）、腕 END は両 drive 同一（ik_resid 0.24mm）⇒ **cable が動いた**（右 EE 離脱でない）。機構 = ik_chord は recorded per-frame arm_q（`:1216` `apply_recorded_arm_ff`）を **linear JOINT chord**（`:1254` `jq_interp=old_fk_jq+(jq_targets−old_fk_jq)·t`）に置換 → joint trajectory 差が cable を余分に押す。

**⛔ lever = ~10× task-space に未確定（on-disk が cheap lever を示唆 — over-spend 前に verify、原因仮説裏付け）**: %12 §4 は ~10× task-space interp を recommend したが 2 点で保留:
1. **magnitude 疑義（純 M-b1 within-step-shape）**: per-step EE 移動 = 1.67mm（§3 dClampR、≤2mm）+ within-step joint span = 0.0093rad（§3 dJointQ）⇒ FK ほぼ線形 ⇒ within-step EE bow は **微小**（≪1.67mm）。純 within-step chord 曲率が cable を 2.4×（+47mm/20step = 2.35mm/step extra）押す magnitude を説明しにくい。
2. **on-disk 機構 nuance（%12 §4 未言及）**: batched IK = **position-only action + HELD-KO rotation target**（`:955` 逐語「the KO rot target (held; action is position-only)」、rot は init `:970-976` 固定・`:1005-1006` は position のみ更新）。**ik_resid 0.24mm は POSITION 残差のみ**（`:1290` = `norm(EE_body_pos − targets)`）⇒ ik_chord の **config/wrist-orientation が recorded と一致する保証なし**（position のみ一致）。recorded config/orient が held-KO position solve と異なれば ik_chord の joint trajectory は **endpoint でも** recorded から drift → 別 EE sweep（= M-b2、within-step-shape でない）。

**⇒ H-b sub-fork（lever を決める、未 isolate — §10.6 H-b row を分割）**:
| sub | 機構 | probe signature（176-195） | lever | /diffik-traj | cost |
|---|---|---|---|---|---|
| **M-b1 within-step chord shape** | endpoint は recorded 一致、within-step の linear-joint chord が EE を bow | ik_chord EE が **endpoint 直線から within-step で有意 bow**（%12 §3:62 提示 probe） | task-space 漸進 EE interp（per-frame IK・小 Δx） | ⛔「one-shot 禁止」直適用 | ⚠ ~10× IK |
| **M-b2 endpoint config/orient divergence** | ik_chord jq_targets が同 position で recorded arm_q と config/wrist-orient 差（position-only+held-KO 由来）| jq_targets vs recorded arm_q の **config/orient 差が有意**・within-step bow は小 | IK rot target を recorded orient から駆動 / null-space を recorded config へ bias | pose-mode（既存 descend/push）| 安（1 solve/step）|

**discriminating probe（%12 court、fix 前、cheap read-only）**: 176-195 で (P1) within-step EE bow（ik_chord EE vs endpoint 直線）(P2) jq_targets vs recorded arm_q の config + wrist-orientation 差 (P3) recorded within-step fingertip path length vs net。⇒ **P1 大 → M-b1 → ~10×**；**P2 大（config/orient 差）→ M-b2 → cheap**（rot-target/null-space）。⭐**bound**: これは H-b sub 空間の**最終 fork**（within-step-shape ∨ endpoint-divergence で exhaustive）— diagnostic regress でない（10× 恒久 cost が binary fork に懸かる ⇒ cheap probe が正当）。
**⚠ invariant note**: M-b2 lever（rot target を recorded orient から駆動）= DiffIK 内 mode（position→pose、CLAUDE.md DiffIK「descend/push: pose mode」既存）ゆえ control 方式変更でない。ただし held-KO orientation は設計判断（コ-gripper down 姿勢）ゆえ recorded-orient 駆動が **gripper orientation 前提に触れるなら design-gate + Rs 確認**（§0 コ-geometry 近傍、触れたら STOP+Rs）。M-b1 lever（task-space interp）は position-only のまま ⇒ orientation 前提不触。

**次**: %12 discriminating probe（P1/P2/P3 @176-195）→ M-b1/M-b2 確定 → 本表から lever 確定 → design-gate（/diffik-trajectory + /pre-check）→ L3 → impl → re-measure（FIXED harness + 右腕 fingertip_r/contact_r/dual-load + 176-195 監視 DoD）。

### §10.8 M-b2 CONFIRMED → lever 確定（recorded-branch IK seed）+ design-gate（v1.4, 2026-07-18 12:0x — 入力 DIAGNOSTIC_RESULT §5 [P2] + p5 on-disk `:1173`/`:1216`/`:1254`/`:1283`/`:1073`/`:955`/`:1005-1006`）
**M-b2 CONFIRMED（%12 §5 [P2]、on-disk verify）**: 右腕 IK が recorded と**別の discrete config branch**（|arm_joint_q ik-ff| wrap 補正 = **右腕 4.32rad**: j14 shoulder=2.37 / j16 elbow=1.96 / j17 wrist=1.89 / j19 wrist=2.37；左腕 0.034rad=recorded 一致）を解く。orientation 一致（|clampR ik-ff|=0.82mm 一定=爪先 endpoint 一致）ゆえ M-b1 within-step-bow でも orientation でもない。grasp(step90)から 3.93rad off、flip config で fragile → grip は 176 まで持つが route で剥離。⇒ root = **右腕 IK の branch 誤選択**。

**exact form（p5 call、on-disk grounded）**:
- 現: `jq_starts = np.array(self._per_world_fk_jq[:N])`（`:1173`）= 前 step の ik_chord 解 → 初期 `_settled_fk_jq`（reset `:1073`）の wrong branch を warm-start 連続（`:1283` commit）で route 全体に伝播。
- **lever = IK warm-start seed を recorded arm_q から**（route step の recorded config、FF が `:1216` `apply_recorded_arm_ff` で使う同 recording source）。IK（30 iter、position + held-KO rot objective）が **recorded branch へ収束**（recorded arm_q が recorded branch の解、target = base + small residual ゆえ近傍で同 branch）。**両腕 seed**（左は一致だが symmetry/robustness、他 IC で左 flip 防止）。
- **⛔ null-space bias は不適**（6-DOF arm at 6D pose[position + held-KO rot]= 連続 null-space なし; branch は discrete、warm-start seed の basin で選択）。%12 提示 null-space option を訂正: **seed が正しい lever**。
- ⭐**within-step も同時に解決（magnitude puzzle 解消）**: endpoint が recorded branch なら `:1254` linear-joint chord は recorded-branch config 間の小補間 → EE path ≈ recorded（bow 小）。2.4× cable push は **wrong-branch fragility 由来**（within-step bow でない）ゆえ branch fix が M-b1 相当も cover。§10.7 の magnitude 疑義が本 finding で説明済。

**physical validity（p5 call）**: recorded config = 実証済み physically-valid 構成（成功 FF run）を track = 最も忠実。⛔ **kinematic trick でない**（IK は実 target[base+residual]を solve、seed は basin 選択のみ; teleport/強制配置なし、arm は physics[PD on interp path]で到達）。DiffIK-only 遵守（seed は標準 IK 入力、control 方式変更でない）。

**design-gate ①: /diffik-trajectory 分析**:
- step-size/補間: 不変（`:1254` linear-joint chord 維持、per-step EE 1.67mm ≤2mm safe）。lever は EE 軌道でなく IK config branch を変える。
- reachability/収束（LL-Process CFG-001）: recorded seed は target に近い（residual 小）⇒ 30 iter 収束は現状より**改善**（wrong-branch から遠回りしない）。recorded branch は実証済み到達可能（FF 成功 ⇒ J3/singularity 回避、demo が valid）。
- DLS/branch: discrete branch 選択は seed basin 依存（連続 DLS damping と独立）。recorded seed が recorded basin を保証。

**design-gate ②: /pre-check inline self-check**:
- [x] reachability: recorded seed → recorded-branch target 到達（residual 小で同 basin）。
- [x] no gated-deadlock: grip 復元 → G3-G6 到達路復活。
- [ ] threshold/residual: large residual で seed が target 未到達の可能性 → **sub-agent verify 対象**。
- [x] invariant: DiffIK 内・no-trick・dual-arm/88mm/コ 不変・position-only+held-KO 保持。
- [x] SRG: fidelity-bound でない（IK branch = kinematic、substrate proxy 非依存）。

**design-gate ②b: /pre-check failure-mode sub-agent** — 〔spawn 済、verdict 返り次第 fold〕。pre-empt FM: (FM1) large residual 収束 (FM2) recorded frame 選択（route step 代表 = END frame） (FM3) 左腕 seed harmless (FM4) held/frozen world の recorded lookup 整合 (FM5) reset/first-step seeding。

**invariant guard**: §0 不触（DiffIK 内 seed・no-trick・dual-arm/88mm/コ 不変・position-only+held-KO 保持）⇒ STOP 不要。ただし design-gate + /pre-check + L3 は必須（control-code 変更）。

**次**: /pre-check sub-agent verdict fold → 本 §10.8 lever を %12 court へ（L3 CC-Debate → rule-check → impl[jq_starts を recorded seed に、explicit-path] → re-measure[FIXED harness + 右腕 config vs recorded + fingertip_r/contact_r/dual-load + 176-195 DoD]）。

### §10.9 /pre-check verdict = WARN → design amendments（v1.5, 2026-07-18 12:2x — /pre-check sub-agent[general-purpose, on-disk verify] + p5 on-disk 再確認 `:860-890`/`:933`/`:942`/`:1246`/`:1229-1233`/`:236`/`:1272`）
**verdict: WARN**（0 critical / 2 high / 2 medium / 1 low + 3 impl guards）。core lever（recorded-branch seed）は residual 0 で sound・FF control（recorded 右 branch が全 route 保持）で強く裏付け。ただし下記を fold してから impl。⛔ 全 amendment を p5 が on-disk verify（sub-agent 出力を鵜呑みにせず）。

**⭐ AMEND-1（Issue 1, HIGH, confirmed defect — p5 on-disk verify 済）**: §10.8 lever は IK seed（`jq_starts` `:1173`）のみ recorded 化するが、within-step interp START（`old_fk_jq` `:1246`）は**別 read**で reset の `_per_world_fk_jq = _settled_fk_jq`（`:942`）のまま。`_settled_fk_jq` = P0 IK solve（`_solve_ik_single_ko` `:860-890`、初期 fk state seed `:863`、KO-rot）= **recording と branch 独立**（`:933`）。⇒ step 0 で `jq_interp`（`:1254`）が settled(wrong)→recorded(jq_targets) を linear joint 補間 = **cross-branch sweep**（sub-agent per-step read: R-arm ‖Δ‖≈5.7rad@step0; mechanism は p5 が code で verify）。arm は **kinematic re-pose**（AMEND-5、PD damping なし）ゆえ中間 cross-branch config が exactly realized（approach 近傍で wild EE/elbow）。FF は recorded config 直接書き（`:1229-1233`）ゆえ gap 非通過。
- **fix = 両 read を recorded branch に pin（⭐O1 解決: `_per_world_fk_jq`-ONLY、`_settled_fk_jq` は触らない — p5 on-disk verify）**: `_reset_worlds` で `_per_world_fk_jq[w] = _settled_fk_jq.copy()`（`:1057`）の**後に**、`_per_world_fk_jq[w]` の **ARM coords {0-5,14-19}**（gripper coords は `:934-940` patch 維持）を recorded arm_q[route_t0] で overwrite（FF refresh `:1229-1233` mirror）。⇒ step-0 の jq_starts(`:1173`) も old_fk_jq(`:1246`) も recorded（両 read が `_per_world_fk_jq`）→ step-0 は settled-body→recorded 単一 jump（FF 同等）で cross-branch 中間なし。per-step reseed（jq_starts、AMEND-2 robustness）で N≥1 の jq_targets を毎 step recorded に anchor。
  - ⛔ **`_settled_fk_jq` 自体は seed しない（%12 O1、p5 verify）**: `_settled_fk_jq` は reset 物理 arm re-pose `:1094`（`phys_jq[jq0:jq0+_N_ARM_JOINTS]=_settled_fk_jq[:_N_ARM_JOINTS]`）に伝播し、bodies=settled（`:1086` `assign_world_states_to_sim`）と arm=recorded の **mismatch** を生む（`_settled_fk_jq` は settled bodies の FK ゆえ現 consistent、`:931-933` 同時 capture）。`_per_world_fk_jq`-only なら `:1094` は settled のまま body-consistent、step-0 write（`:1270`）が arm を settled→recorded に jump（FF `:1094` からの jump と同）。⇒ O1 は debate 不要、`_per_world_fk_jq`-only で確定。

**⭐ AMEND-2（Issue 2, HIGH — trained-policy robustness + DoD）**: residual 0 probe は self-proving（seed=recorded=exact solution）。ただし両 branch が position+held-KO objective を満たす（§5）ゆえ basin は seed 依存で、trained policy の residual（dual-grip で最大 DELTA_BOUND_M ~20mm、transit の 2mm cap でない）が basin 境界を越え右腕を re-flip し得、residual 0 probe では surface 不能。mitigation: per-step reseed が次 step で re-anchor（flip は 1 step で self-correct）+ wrong branch は 86 step 把持（90→176）ゆえ単一 flip で即 drop せず。
- **fix**: re-measure DoD に **nonzero-deterministic-residual leg**（固定 10-20mm sweep）追加。residual 0 probe は branch-drift 除去のみ validate と明記。per-step reseed を robust form として採（reset-seed 単独は warm-start continuity 依存で mid-route flip 伝播 risk）。

**AMEND-3（Issue 3, MEDIUM — seed frame）**: seed は route step の **target frame `arm_q[next_f[t]]`**（step_target の tgt_f = ee_pos[next_f[t]]=cf[t+1] と一致）、`step_f[t]+9`（apply_recorded_arm_ff 末尾、1 frame 手前 ~1.14mm EE）でない → seed = 正確な residual-0 解（0 iter）。⚠ route_executor indexing（`:4547`/`:4760`/`:5042`）は sub-agent read、%12 が impl 時 confirm。

**AMEND-4（Issue 4, MEDIUM — DoD 強化）**: 「flipped links が cable 2.4× 変位」は inferred（config offset quasi-constant 3.93→4.40rad だが cable disp は 9→52mm GROW）。branch は FF-vs-ik の identified differential ゆえ fix は well-motivated だが branch fix 後の残差 within-step 寄与は未測。
- **fix**: re-measure は residual 0 で **cable-seg world-disp ≈1×arm（≈34mm, not 80.8mm）∧ fingertip_r_to_cable≈6mm ∧ 右 config≈recorded(~0rad) ∧ contact_r=True + dual load** を assert（「grip holds/no drop」だけでない）。

**AMEND-5（Issue 5, LOW — 事実訂正）**: §10.8 の「arm は PD control で target 到達」は**誤り**。arm は **kinematic joint_q re-pose**（`apply_arm_only_write_perworld` route_executor.py:236 が phys_jq 直接 assign・phys_jqd=0、`:1272` joint_q.assign）、gripper のみ servo/PD。これは**既存 route drive**（armqdirect、新 trick でない）ゆえ DiffIK-only/no-trick compliance 不変。physical-validity 論訂正: recorded-branch seed の valid 性 =「PD で到達」でなく「**recorded config = 実証済み valid 構成 → kinematic pose が recorded 軌道追従 → links が cable を clear（成功 FF 同様）**」。⚠ obs `_last_ik_resid`（`:1290`）は post-hoc achieved-vs-target norm で seed 独立 → semantics 不変（§10.8 item3 の懸念は unfounded）。

**impl guards（%12 court へ fold）**: (a) recording arm_q の存在 assert/fallback が ik_chord reseed に必要（現状 FF path のみ `:5033`） (b) held/frozen world は apply_recorded_arm_ff（`:5045`）と同 hold_mask frame-clamp を seed lookup に適用（wc=1 非発火、fork-B multi-world で必須） (c) recorded arm_q は 28-wide 同 layout・finger-open overwrite（`:1175-1178`）は新 seed でも実行。

**design-gate 総括**: /diffik-trajectory ①（§10.8: step/interp 不変・収束改善）+ /pre-check ②（WARN、AMEND-1..5 fold 済）⇒ **design = WARN-with-amendments**。次 = %12 court（L3 CC-Debate → rule-check → impl[AMEND-1 dual-seed + AMEND-3 frame + guards abc] → re-measure[AMEND-2 nonzero-residual leg + AMEND-4 cable-disp DoD]）。invariant 不触（seed/reset-seed は IK 入力・no-trick; drive kinematic re-pose は既存=不変）。⚠ /pre-check WARN ゆえ impl は %12/Rs sign-off + L3 で vet。

### §10.10 L3 CC-Debate = FAIL → design revision（v2.0, 2026-07-18 13:4x — 入力 `IKCHORD_GRIPSLIP_FIX_L3_DEBATE_VERDICT_RSTECHLEAD_20260718.md` 全文 + p5 on-disk 再確認 `:1235`/`:1246`/`:1254`/`:1283`/`:402`/`:1094`）
**L3 verdict = FAIL-revise（not abandon）**。⭐ mechanism CONFIRMED（airtight、5 challenger; CC2 全数値再現[右腕 4.324rad/endpoint 0.24mm/fingertip 22 vs 6.3mm/drop@267]・CC4 IK=deterministic LM で seed が genuinely branch 選択・CC3 §0 no-STOP・fidelity-framing REJECTED[−10=drive-artifact]）。fix DIRECTION（recorded-branch seed）sound。FAIL 根拠 = 私の設計の HIGH inconsistency + necessity/coverage 未証。design revision は私の court、[VERIFY] は %12 court（read-only）。

**⭐ §A 設計改訂（私の court）**:
- **A1（HIGH — branch/flip GUARD、AMEND-2 の inconsistency 修正）**: 私の AMEND-2 per-step reseed は `jq_starts`（`:1173`）のみ pin し `old_fk_jq`（`:1246` = 前 step commit `:1283`）を pin しない ⇒ trained residual（≤`DELTA_BOUND_M=0.020` `:402`）が step *t* で branch flip すると `:1254` が右腕を ~4.4rad/10frame **cross-branch sweep**（kinematic・PD damping なし）= AMEND-1 が step-0 で防ぐ catastrophe を mid-route（gripper CLOSED）で再導入。「1 step で self-correct」は endpoint には真だが **path には偽**。
  - **fix = jq_targets に branch guard**（`:1235` IK solve 後・`:1236-1243` NaN/finger 処理後・`:1246` old_fk_jq/`:1254` interp 前に挿入）: 各 arm joint の **wrap-distance(jq_targets[j], recorded arm_q[next_f[t]][j])** を計算 → max > branch threshold なら **fall back: jq_targets[arm] = recorded arm_q[next_f[t]][arm]**（cross-branch delta を `:1254` に絶対流さない）。⇒ jq_targets は常に recorded branch（IK の recorded-branch 解 or recorded fallback）→ interp 常に on-branch。AMEND-2 が AMEND-1 と self-consistent 化。
  - **threshold**: 正常 on-branch per-step joint 運動（20mm residual でも数°、≪0.5rad）と branch flip（~2-4rad）の間（例 ~0.5-1.0rad/joint）で well-separated。⚠ **singularity 近傍で minima merge**（CC4 CH-D）ゆえ固定 magic number でなく **B6 で実測 tune/verify**（false-trigger も miss も無いこと + trigger 頻度 = 頻発なら residual 頻繁 reject で訓練信号劣化 → design 再考）。
  - ⛔ **LOUD fail**（CC5 CH-4）: recorded arm_q が None（ik_chord は arm_q OPTIONAL）なら silent に buggy settled seed へ fallback せず **raise/log**。
- **A2（MEDIUM — frame spec、CC5 CH-2）**: 2 consumer は distinct frame を要す。**`old_fk_jq[0] = arm_q[step_f[0]]`**（step-START frame、interp 起点）/ **`jq_starts[0] = arm_q[next_f[0]]`**（target frame、IK seed）。単一 `_per_world_fk_jq` seed で両立不可 ⇒ jq_starts は `_per_world_fk_jq` から decouple し **step 0 含め毎 step recorded[next_f[t]] から reseed**（AMEND-2+AMEND-3 統合）。`_per_world_fk_jq`（→old_fk_jq）は reset で recorded[step_f[0]]、N≥1 は commit chain（recorded[step_f[N]]）。
- **A3（MEDIUM — step-0 teleport、CC5 CH-1/6）**: `_per_world_fk_jq`-only（O1）は `:1094` を settled P0 branch に残すため step-0 で settled→recorded ~4.32rad **arm pop**（現コード非生成の NEW）。probably benign（open gripper・qd=0・cable at rest・FK-recomputed bodies）で FF も同 pop を survive。**決定 = accept `_per_world_fk_jq`-only + step-0 visual/measurement verify leg**（DoD）。tradeoff 明記: 完全回避には reset で physics arm+bodies を recorded FK に re-pose（大 reset 改変）要 → verify FAIL 時のみ revisit。

**⭐ §B [VERIFY] read-only measurement scope（%12 court、HOLD/scope concurrence 要）— re-measure DoD**:
| # | 測定 | DoD gate |
|---|---|---|
| **B4 necessity（CC6 NHA HOLD）** | `grip_retention_measure` を **`route_c1_pin=True`**（trainer 構成）で再走。現 drop は pin-OFF 測定・trainer は pin-ON。⭐`g3_reached=false` ゆえ pin（fires-on-seat）は rescue できない見込み → fix は likely 必要だが **未証** | pin-ON で A_held_z_floor drop 持続 ⇒ fix necessity 確定 |
| **B5 coverage（CC2 CH-1）** | whole-route ik_chord + FF baseline を **G6 / C2_REGRASP（~step500）past** まで（現 probe は ~40%=~step300 のみ）。⭐**C2_REGRASP = FRESH 右腕 IK branch 選択**（cable-derived target `route_executor.py:105`）= 最高 grip-slip risk・未測 | slip が C1-half-only か whole-route か / C2_REGRASP が第 2 slip site か |
| **B6 robustness（CC4 CH-D/CH-E）** | residual sweep が **≥1 route step で basin boundary を provably CROSS** + within-step config-path logging + branch-guard check。fixed nonzero-residual は「変わり得ない test」= 非 test | guard が flip を捕捉し on-branch 維持・false-trigger なし・trigger 頻度 acceptable |
| AMEND-4（CC4 CH-A、falsifiable 保持） | residual 0 で **cable-seg world-disp ≈1×arm（≈34mm, not 80.8mm）∧ fingertip_r≈6mm ∧ 右 config≈recorded ∧ contact_r=True + dual-load** | branch fix が 2.4× push を除去（inferred ゆえ falsifiable gate、confirmation でない） |
| A3 step-0 | step-0 visual + arm pop 測定 | pop が benign（cable 非撹乱、FF 同等） |
| guard wc>1（CC5 CH-5） | guard(b) held-world frame-clamp を wc>1（held world + mid-batch reset）で validate | fork-B 前に multi-world 整合 |

**⭐ §C Rs surface（FOUNDATIONAL 近傍 — loud）**:
- **C7（CC3 CH-1、§0-adjacent、fix-blocker でない）**: 既存の **kinematic arm joint_q drive**（`route_executor.py:236` qd=0 / `:1272` joint_q.assign）は §0 invariant #5「no kinematic trick、例外は clip-pin のみ」に **adjacent**。scripted-verification stage には sanctioned だが **trainer/production control method としての認可は未 ratify**。私の #18 fix は本 drive 内で動作（seed+guard）ゆえ compliance は inheritance-based（fix は本前提を変えない）だが、**kinematic arm drive が trainer の physics-faithful position control か §0#5 例外かの Rs 1 行確認を要請**（私の判断: build-first でなく surface — my fix は前提を変えないため STOP 不要だが、前提自体の ratify は Rs 専権）。
- provenance/wording（CC3 CH-2 / CC4 CH-A,C / CC2 nits）: 「banked c2045a9a1a」= diagnosis commit（acceptance = `cdac6b6972`+`f8b1ff6b4c`）; AMEND-3 seed は **position-exact であって 0-iter でない**（held-KO rot w=0.5 + jlimit w=10.0 が recorded arm_q で nonzero、CC4 CH-C）→ IK cost 0→30 log; window label = 248-270; drop@267 の proximate = **LEFT 腕**（correct branch）が単腕負荷で lateral escape・右 wrong-branch が ROOT（~195 から単腕）。

**design-gate（改訂）**: /diffik-trajectory（guard = joint-space branch clamp = 「no large joint jump / on-branch」原則の直適用、step/interp geometry 不変）+ /pre-check inline（guard の FM: threshold tuning[B6]・LOUD fail[CC5 CH-4]・singularity 近傍 false-trigger[CC4 CH-D]）。invariant 不触（guard=IK 出力 clamp、DiffIK 内・no new trick; C7 は既存 drive の surface で私の fix 起因でない）。**次（order = %12 提案の measure-first、p5 CONCUR 2026-07-18 13:4x）**: **[VERIFY] B4/B5/B6-char（re-debate 前、read-only current-system characterization）→ %12 re-debate（L3）v2.0 WITH evidence → impl（fenced; §C ratify + Rs sign-off 要）→ B6 guard-verification（post-impl）**。理由: B4 が fix を moot し得る（pin-ON で drop 消滅なら不要）/ B5 が scope 決定（C2_REGRASP 要否）/ ⭐B6-char が A1 の threshold/basin evidence（speculation でなく実測で re-debate が vet）。⚠ B6-char が bad basin（singularity 近傍で seed 非保持 / clean threshold なし / 頻繁 trigger）を示せば **A1 を refine**（threshold/fall-back の feedback loop）。B6 guard-verification のみ impl 依存で post-impl（正）。

### §10.11 B4/B5 scope 精緻化 + B4-by-analysis 確認 + ⭐(d-b) PREREQUISITE（v2.1, 2026-07-18 14:0x — 入力 %12 14:00 + OPS-SUP-CODEX 13:51 + p5 on-disk verify `:1225`/`:1821`/`:1620-1621`/`:1629`）
**⭐ B4 necessity = RESOLVED BY ANALYSIS（p5 pin-design CONFIRM、on-disk verified — empirical「ik_chord pin-ON」は今 unrunnable ゆえ analysis 接地）**:
- **Fact 1（p5 verify: `_maybe_activate_c1_pin` = `:1225`[FF branch loop 内] + `:1821`[定義] のみ、ik_chord loop `:1252-1281` に call なし）**: ik_chord run で `route_c1_pin=True` は pin を pre-allocate するが **never fire**（no call）= no-op 交絡。empirical pinned-ik_chord B4 は今 runnable でない（(d-b) impl PREREG:34 が ik_chord へ call 挿入、未 land）。
- **Fact 2（p5 verify: `mid_xy=0.5*(clamp_r+clamp_l)` `:1620` → `held_i=argmin(cable_pos−mid_xy)` `:1621`）**: A_held_z_floor drop の held segment = **gripper-midpoint 近傍**（ARMS held）。pin が retain = **C1 clip crossing**（`c1_retained=c1_seated` `:1629` = 別 segment）⇒ pin は drop する midpoint segment を hold 不能。+ g3_reached=false ⇒ pin（fires-on-seat）は drop 前 never fire。
- ⇒ **necessity ESTABLISHED**: grip fix IS needed、pin は moot しない。**p5 pin-design CONFIRM**（%12 B4-by-analysis 正当）。
- **residual（small、unmeasured、p5 physics-reasoning）**: C1-pin tension が cable stiffness 経由で midpoint segment を INDIRECT hold し得るか → **UNLIKELY**（RS71 §4 = floppy planar-bender・sag-only、held 点間で sag ⇒ 遠 segment への hold 伝達 negligible）。FF では pin 有無に関わらず grip holds ゆえ isolate 不能。post-(d-b)-land で要 check なら可（低優先）。
- **B4-shadow（empirical corroboration、pN 提案、runnable NOW）**: ik_chord run で pin-trigger 条件（capture ∧ depth Z_FIRE_DEPTH_M=0.831 ∧ K=3 dwell）を **観測のみ**（fire しない）→ **fire=0 ∧ G3=false** なら pin never-fire を empirical 確認 → necessity。(d-b) pin call の land 不要。⇒ B4 = analysis CONFIRM + shadow corroboration（両建て）。

**B5 coverage split（pN 提案、reachability 制約 fold — ik_chord は drop@267 で C2_REGRASP ~step500 未到達）**:
- **B5a（pre-impl、runnable NOW）**: FF whole-route baseline（FF holds ゆえ ~step771 全走）+ ik_chord **current reachability**（drop@267 まで = C1-half のみ）。→ slip が C1-half-only か whole-route かの baseline。
- **B5b（post-impl）**: post-fix ik_chord **whole-route efficacy**（fix 後 ik_chord が hold して初めて C2_REGRASP ~step500 到達可）。⭐**C2_REGRASP = FRESH 右腕 IK branch 選択**（cable-derived target `route_executor.py:105`）= 第 2 grip-slip site 候補 → **B5b で A1 guard が C2_REGRASP でも branch を保つか検証**（whole-route DoD）。
- ⇒ pre-fix の ik_chord whole-route は物理的に不能（drop@267）ゆえ B5 whole-route ik_chord は inherently post-impl（B5b）。pre-impl は FF baseline + ik_chord partial（B5a）。

**⭐⭐ (d-b) PREREQUISITE dependency（%12 + pN、p5 mechanism CONFIRM）**: **#18 grip fix は (d-b) の PREREQUISITE**。理由（on-disk）: (d-b) の C1 pin は **seat（capture ∧ depth）で fire**（(d) charter）。現 ik_chord は grip slip（drop@267）が **g3=seat より前** ⇒ pin never fire ⇒ (d-b) 動作不能。⇒ 依存順 = **#18 (grip) → (d-b) (pin) → training-ready**。⚠ 本 dependency を DDR/LEDGER に記録要（%12/PLAN-KEEPER、07-Design/LEDGER は私 read-only ゆえ surface のみ）。earlier session で (d-b) を primary 扱いしたが、#18 が上流 gate。

**B4/B5 order 影響（measure-first に fold）**: pre-impl [VERIFY] = **B4-shadow + B5a + B6-char**（全て runnable now、re-debate 前）/ post-impl = B4-shadow 再確認不要（analysis 確定）+ **B5b（whole-route + C2_REGRASP）+ B6 guard-verify**。§10.10 §B の B4「pin-ON re-run」は **B4-by-analysis + B4-shadow へ supersede**（empirical pinned-ik_chord は un-landed pin ゆえ unrunnable）。

### §10.12 B4-shadow fire-predicate spec（p5 pin-design、%12 要請）+ GO-now scoping（v2.2, 2026-07-18 14:2x — 入力 %12 14:23 + p5 on-disk verify `_maybe_activate_c1_pin` `:1821-1860`）
**⭐ B4-shadow が faithful に replicate すべき EXACT fire predicate（source = `_maybe_activate_c1_pin` `:1821-1860`、観測のみ・fire/weld/authorizer/physics 変更なし）**。**per PHYSICS FRAME（各 sub_i、intended ik_chord pre-step 位置 = (d-b) PREREG:34 挿入点）で**:
1. **precondition（`:1841`）**: identity `_pin_seat_seg` present（pin recording 要; None = fail-closed 非評価）。route_c1_pin gating は fire 用ゆえ shadow は観測するが identity は必須。
2. **seat body（`:1848`）**: `seat_body = int(self._cable_bodies[0][int(self._pin_seat_seg)])`（identity body only、recording-derived）。
3. **snapshot（`:1849`）**: `seat_world = bq[seat_body, :3]`（**単一 per-frame snapshot**、capture と authorizer が同値を読む = same-snapshot）。
4. **capture（`:1850`）**: `rex.clip_capture_check(self._solver, seat_world)`（authorizer と **SAME predicate + cache** = containment-by-identity）。
5. **depth（`:1851`）**: `float(seat_world[2]) <= rc.Z_FIRE_DEPTH_M`（=0.831m）。
6. **fire-cond = capture ∧ depth（`:1851`）**; どちらか False で **dwell=0 reset（`:1852`、strict consecutive）**。
7. **K-dwell（`:1854-1855`）**: (capture∧depth) で `_c1_pin_dwell += 1`; **shadow-fire when dwell ≥ rc.PIN_TRIGGER_DWELL_K（=3 consecutive physics frames）**。
8. ⛔ **WITHOUT `authorize_clip_pin`（`:1857`）**: weld/authorizer/physics 変更なし（観測 count のみ）。
- **outcome**: ik_chord run 全体の shadow-fire count（dwell≥K イベント）。**shadow-fire=0 ∧ g3=false → necessity discharged**（pin は drop 前 never fire）。**shadow-fire>0 → real pin counterfactual = separate gate**（pin が fire し得る ⇒ pin の rescue 可能性を別途 measure）。held_i(gripper-midpoint) vs C1-clip-segment analysis（§10.11）と complementary。
- ⚠ **faithfulness**: (a) **per PHYSICS FRAME（sub_i cadence）** で観測（K は physics-frame consecutive、per-RL-step でない）(b) intended ik_chord pre-step 位置（PREREG:34、physics step 前）(c) identity `_pin_seat_seg` は pin recording 由来（無ければ :1841 fail-closed で非評価 = shadow も走らない → pin recording で走らせる）。

**⭐ GO-now scoping（%12 verdict-authorized、v2.1 の order を精緻化）**: 本 L3 FAIL verdict が authorize する pre-re-debate read-only [VERIFY] = **B4-shadow + FF whole-route + ik_chord-natural-term（=B5a、BLOCKED_BY_PRE_C2_DROP@267）** のみ。**B6(basin) + impl は本 verdict で NOT authorized** → **B6-char + B6 guard-verify + B5b（post-fix whole-route）= deferred**（separate auth / re-auth）。⇒ A1 の **threshold は B6-char（post-auth）で tune**、re-debate は **A1 の mechanism を threshold-TBD で vet**（mechanism 承認 → threshold は後続）。%12 が prereg/bank してから B4-shadow+FF whole-route+ik_chord-natural-term を run。

### §10.13 substrate fidelity gap — diagnostic ruling（Rs finding、p5 設計court、%12 照会 2026-07-18 23:27 / p5 on-disk verify `:650`/`:648`/`:1647-1657`/`:1443`）
**finding（Rs 質疑 surface）**: 現 fork-B は golden（RUN1_REFERENCE_V2 sha 5f1c3f92、pin ON from step254、**771 完走**）を **faithful FF replay でも再現不可**（FF+pin drop B_contact_loss@347 / FF-nopin C_c1_escape@342 / ik_chord A@267）。⇒ gap は #18（ik_chord）より**上流の substrate fidelity**（FF ですら fail）。Rs 仮説: cable 柔軟性/条件が golden-record env と fork-B で差。

**design-correct diagnostic = (b) → (a) → (c)**（cheapest-discriminating-first; predicate-gap vs physics-gap を先に分離）:
1. **(b) FIRST — golden 自身の stored states を現 drop 述語 A/B/C に通す（cheapest、no-sim）**: golden は `cable_xyz`（`:650`）+ `arm_q`（`:648`）を per-frame stored ⇒ 現述語（A_held_z_floor[held_z] / B_contact_loss[`_contact_loss_count` `:1647-1657`] / C_c1_escape[`:1443`,`:1652`]）を golden の cable_xyz + arm_q(→clamp via FK) で評価可能。
   - golden states が **drop 述語 trigger** → **PREDICATE gap**（現 fork-B 述語が golden より strict: golden は 771 完走なのに現述語で drop = 「drop」は instrument artifact ⇒ **#18 grip-slip も部分/全て predicate 由来の可能性**、major reframe）。= [[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]] 直適用（known-good golden で gate 検証）。
   - golden states が全述語 **PASS**（771 drop なし）→ **PHYSICS gap**（replay cable_xyz が golden stored と diverge）→ (a)。
2. **(a) — golden stored cable_xyz vs 既存 replay（FF+pin）cable_xyz を step-wise 比較 → divergence onset localize**（既存 replay data、new run 不要）: early=IC/param / late=accumulation。
3. **(c) — divergence 点で cable bend/stretch stiffness（+damping/contact/solver params）golden-env vs fork-B 比較**（Rs param 仮説を (a) の localization で test）。

**⭐ reframe（design-axis）**: substrate gap は **#18 の上流**（FF replay ですら fail ゆえ #18 の A1/A2/A3 は ik_chord=FF にするが FF=drop@347 のまま = substrate gap が両者を cap）。⇒ **(b) を #18 impl より先に**（predicate-gap なら #18「drop」自体が再解釈要）。⚠ **invariant**: diagnostic (b/a/c) は read-only（安全）。ただし (c) で cable param 差が判明しても、fork-B の cable 物理変更は RS71 §0/banked cable design に触れる可能性 ⇒ **変更前に design-gate + Rs**（fidelity 復元 = fork-B を golden-record substrate に合わせる、でも触れたら STOP+Rs）。⚠ (b) 実行の前提: golden.cable_xyz が world-frame・全 771 frame coverage か %12 が実行時 confirm。

### §10.13.1 Phase0 comparability gate（pN co-decide 23:32、p5 CONCUR + design fields）
**pN 判定: substrate fidelity gap は現時点 UNPROVEN** — golden = **producer** 7707-frame recording vs current FF+pin = **consumer**（NewtonRouteEnv）= role 差、かつ同一 npz sha 5f1c3f92 に **sidecar provenance 競合**（w0e cell_x0_y0: meta 9346d7c2/head bc09a2de/recorder bd5457f3 vs seatgate r2b: meta d8e44a19/head 5b7afd5a/recorder 6eace080）。⇒ **(b)→(a)→(c) の UPSTREAM に Phase0 = canonical-lineage + producer/consumer comparability audit**。exact as-run closure 再構成不能なら **golden=TRACE_ORACLE_ONLY**・divergence 語 = **TRACE_CONTRACT_DIVERGENCE / NOT_COMPARABLE**（substrate regression 昇格不可）。= [[feedback-code-sha-match-is-necessary-not-sufficient-env-is-a-separate-axis-2026-07-15]] 直適用（sha 一致でも lineage/env は別軸）。

**p5 CONCUR（全条件 design-sound）**: (i) producer/consumer role 差 (ii) provenance 競合解消先行 (iii) current FF+pin 2 fresh same-seed で **current env 自己 determinism 先行確認**（env が自己 non-deterministic なら golden-vs-current 比較が交絡）(iv) per-physics-frame **earliest divergence + pre-divergence equality + single-delta のみ LOCALIZED** (v) 動画 RECORDED_STATE_RENDER(NO PHYSICS) vs CURRENT_PHYSICS 明示・V12 blind path。

**p5 design-field 追加（→ %12 prereg）**:
1. **(b) を Phase0 後も保持**（cheapest・predicate-gap discriminator）: pN prereg は (a) sim divergence 中心だが、Phase0 で comparability 確立後は **(b) predicate-on-golden-states を (a) sim より先に**（no-sim で predicate-gap vs physics-gap を分離 → sim 前に class 確定、GPU 節約）。⚠(b) も producer/consumer contract 差の影響を受ける（consumer 述語を producer stored states に適用）ゆえ Phase0 comparability が (b) の前提でもある。
2. **cable topology/segment-count match（Phase0 必須 field）**: golden.cable_xyz と consumer cable_pos が **同一 cable body 数/discretization** か。差あれば per-body cable_xyz 非比較 = NOT_COMPARABLE（(a)/(b) 双方の前提）。
3. **IC equality（step0 cable state、pre-divergence equality の明示 baseline）**: golden step0 cable_xyz vs fresh same-seed settled IC 一致か。step0 mismatch = **IC 差（substrate physics でない）** ⇒ divergence を substrate に帰属前に IC を統制（[[feedback-confirming-measurement-is-not-root-cause-isolation-reconcile-the-control-2026-07-18]]）。

**統合 sequence**: **Phase0（lineage + producer/consumer comparability + cable topology + IC equality）→ [comparable なら] (b) predicate-on-golden [no-sim] → (a) 2-fresh-same-seed earliest-divergence [physics-gap 時] → (c) param compare**。[comparable でないなら] golden=TRACE_ORACLE_ONLY・NOT_COMPARABLE で停止（substrate regression と呼ばない）。design owner 不足 field は上記 3 点、他は pN 条件で充足。

### §10.13.2 Phase0 result caveats + (b) GO（p5 design review、%12 Phase0 banked a5b6b341db、2026-07-18 23:5x）
Phase0 = **COMPARABLE-with-caveats**（cable topology 40-seg MATCH✓ / timebase 10f/RL MATCH✓ / IC z-level 0.8040 MATCH / ⚠ golden inner nsubstep **UNRECORDED**[consumer=4] / golden=**TRACE_ORACLE_ONLY**[2 as-run metas]）。p5 review:
- **(b) GO（no objection）**: offline predicate-on-golden は sim なし ⇒ **nsubstep caveat 影響なし**、TRACE_ORACLE_ONLY 下でも valid（predicate-calibration は substrate lineage 独立）。
  - ⚠ **(b) C-predicate caveat**: g_latched/grasped は grip_cmd+phase から offline 導出 = **live latch の近似** ⇒ C（c1_escape、c1_latched 依存）の offline eval は approximate。**A（held_z）/B（contact_loss）は robust**（cable_xyz+ee_pos+grip_cmd から直接導出）。⭐ FF+pin drop は **B@347**（robust）・FF-nopin は C@342（derived-latch caveat）⇒ **(b) は A/B を weight**、C は近似扱い。
- ⭐⭐ **nsubstep caveat = (a)/(c) physics-gap の CONFOUND**: consumer FF@**4**（RL_SIM_SUBSTEPS）vs golden@**?**（unrecorded; faithful pipeline なら 10=SIM_SUBSTEPS）。FF@4-vs-golden divergence は **substep-granularity（4 vs 10）で説明可能 = KNOWN throughput/fidelity tradeoff、substrate regression でない**。⇒ **(a) は FF@4 AND FF@10（SIM_SUBSTEPS）を golden vs で bracket**（substep 単一変数統制）: FF@10 が golden 再現 → gap=substep（throughput 設定、not substrate）/ FF@10 も diverge → deeper（c）。⚠ earlier substep 反証は **ik_chord-vs-FF@4（同 substep）** で、**FF-vs-golden@≠4 には未適用** ⇒ [[feedback-confirming-measurement-is-not-root-cause-isolation-reconcile-the-control-2026-07-18]]（帰属前に変数統制）。
- **IC equality（(a) 用）**: Phase0 は z-level（0.8040）のみ確認。**(a) の fresh run は full step0 cable_xyz（40-seg X/Y/Z）を golden step0 と照合**（z-level は必要十分でない; X/Y shape 差が divergence を confound）。(b) は IC 無関係（golden 自身の trajectory）。

**判定**: **(b) GO**（A/B weight、C 近似ラベル）。**(a) は substep-bracket（FF@4+FF@10）+ full-IC 照合を条件**に。**(c) は (a) が substep で説明できない残余にのみ**。全結果 **TRACE_ORACLE_ONLY / TRACE_CONTRACT_DIVERGENCE / NOT_COMPARABLE** ラベル（substrate regression 昇格不可）。cable param 変更（(c) 由来）は §0/banked cable 触れ得る → 変更前 design-gate+Rs。

### §10.13.3 (b) outcome-language CORRECTION + substep-match decisive（pN readback HOLD、p5 ACCEPT、2026-07-19 00:0x）
pN Phase0 evidence readback = **HOLD**。2 design-impact correction（**p5 ACCEPT** — §10.13/§10.13.2 の (b) dichotomy を supersede）:
1. **nsubstep = KNOWN mismatch（not "unrecorded"）**: producer meta は **SIM_SUBSTEPS=10 を明記**、consumer=4 ⇒ §10.13.2「UNRECORDED caveat」を **「既知 10-vs-4 mismatch」に訂正**。⭐ my substep-confound は caveat でなく **confirmed known mismatch** ⇒ substep-match が decisive control。
2. **(b) offline = state-only PROJECTED characterization のみ（gap dichotomy 不可）**: golden npz は consumer hidden state（`_g_latched` / `contact_loss_count` / `contact_r/l`）を **持たず**、grip_cmd+phase_id からの導出は consumer hidden state と **同値でない**。⇒ **§10.13 の「(b) → PREDICATE gap vs PHYSICS gap 二分」を supersede**: (b) は golden states 上の PROJECTED predicate characterization まで。**PROJECTED_HIT ≠ clean predicate-gap**（projection artifact 可能）・**CLEAR ≠ clean physics-gap**（projection miss 可能）。pin_active の C 明示 suppression branch も **on-disk 不在** ⇒ C-suppression claim 撤回・C caveat 強化。

**⭐ 訂正後 diagnostic（decisive = substep-matched consumer run）**:
- **(b) offline = CHEAP PRELIMINARY のみ**（PROJECTED、dichotomy 出さない、weak first look; pN B1-B7 correction 適用後）。
- **DECISIVE = consumer FF@10（SIM_SUBSTEPS、golden meta 一致）vs golden**: (i) KNOWN substep mismatch を統制 (ii) **LIVE consumer hidden state** を持つ ⇒ offline (b) が出せない clean discrimination が可能。結果: **consumer@10 が golden 再現 → gap=substep（throughput 設定、not substrate）、resolved** / consumer@10 も diverge → live-state で predicate-vs-physics 判別（predicate が cable_xyz 一致中に fire=predicate gap / cable_xyz diverge 後に fire=physics gap）→ 残余のみ (c)。⚠ FF@10 は diagnostic-config run（substeps=10 for measurement、production code 変更でない）。
- 全結果 **TRACE_ORACLE_ONLY / TRACE_CONTRACT_DIVERGENCE / NOT_COMPARABLE** ラベル。(b)/P1 は pN B1-B7 correction まで FENCE 継続。

**p5 ACCEPT + design-owner note**: pN correction は design-sound（consumer hidden-state 非可用 = offline dichotomy 不可）。§10.13/§10.13.2 の (b) outcome language を本 §10.13.3 に scope-down。§10.13.2 の substep-bracket は **consumer FF@10-vs-golden を PRIMARY decisive** に昇格（FF@4 は現 throughput baseline として保持）。

### §10.13.4 §10.13.3 CORRECTION（pN design correction 00:22、p5 ACCEPT + prior-art miss own、2026-07-19 00:2x）
pN: §10.13.3 = **PARTIAL PASS**（静的 PROJECTED-only correction は PASS✓）、FF@10 framing に correction（**p5 ACCEPT** — §10.13.3 の substep/decisive 表現を supersede）:
1. ⚠ **FF@10 = PRIOR-ART（私の miss）**: whole-route FF@10 artifact 既存 = `comp5_c2seat_fullfire_sub10_result.json`（sha 6057802、commit 311f18cb9b、early_done 538、phase3、**NOGO**）。node 既判定 = **sub10 NOT cause・open-loop drift**。⇒ 私の「FF@10 run → gap=substep resolved」は **prior-art repeat + 誤 framing**。再走は prior-art disposition + concrete delta 必須。**own**: FF@10 推奨前に prior-art check（§運用4 / VaultProtocol V7/V10）を怠った。
2. **clean single-variable substep control = current-FF@4 vs current-FF@10**（同 current source/build/IC/pin/seed、substeps + paired dt のみ差）。**current-FF@10-vs-golden は NOT clean/decisive**（producer code/build/pin mechanism 差が残る = secondary trace-oracle）。§10.13.3「decisive」撤回。
3. **golden-vs-current は PRE-PIN（pre-step246）のみ clean**: golden pin onset step254 vs current live trigger step246 ⇒ **post-246 は pin-confounded**。trace comparison は pre-246 限定。
4. ⭐ **residual mechanism = open-loop drift**（prior-art node 判定）: FF@10 は sub4 より further（538>347）だが NOGO = 純 substep でなく **open-loop drift**。⇒ 「substrate gap」は substrate-param regression と限らず **open-loop replay drift**（closed-loop RL が本来 correct する対象）を含む。

**訂正後 scope（pN 指示、§10.13/§10.13.2/§10.13.3 の substep-resolved/decisive を supersede）**: 
- **(b) PROJECTED-only preliminary**（PASS、offline、dichotomy 出さない）。
- **current-pair sensitivity = FF@4 vs FF@10（同 current build）** — substep 感度のみ isolate（既存 FF@10 が同 build なら pair 流用、異 build なら concrete-delta 明示で re-run）。
- **pre-pin（pre-246）trace comparison** — golden vs current の cable_xyz を pin-confound 前に限定（secondary trace-oracle）。
- **「gap=substep resolved」「FF@10-vs-golden decisive」= 撤回**。全結果 TRACE_ORACLE_ONLY / TRACE_CONTRACT_DIVERGENCE / NOT_COMPARABLE。cable param (c) は未 authorize（open-loop drift が主因なら (c) 不要の可能性）。

**p5 note**: pN correction は全て design-sound。open-loop drift が residual なら、これは #18（closed-loop ik_chord drive の branch fix）の motivation を強化する（open-loop FF は drift、closed-loop RL が correct、その ik_chord drive の M-b2 bug を #18 が直す）。cable-param regression の証拠は現時点なし（prior-art は open-loop drift を指す）。

### §10.13.5 substrate-gap WIND-DOWN disposition（p5 CONCUR、%12 Phase0 v0.3 f280cbe15e、2026-07-19 02:1x）
%12 結論（**p5 全 CONCUR** — design-sound、comp5 prior-art + Phase0 に接地）:
- **divergence = KNOWN open-loop FF drift**（comp5 FF@10 early_done 538/NOGO 実在、sub10 not cause）。
- **substrate-gap UNPROVEN = re-discovery**（既知 open-loop drift の再発見; substrate-param regression の証拠なし、Phase0 = TRACE_ORACLE_ONLY/NOT_COMPARABLE）。
- **(c) cable-param compare = unneeded**（param regression 証拠なし; 追求は SRG「one more sourced param」spiral）。
- **#18 closed-loop motivation 強化**（open-loop FF は drift、closed-loop RL が correct、その ik_chord drive の M-b2 bug を #18 が直す）。

**p5 design note**:
- **(b) PROJECTED preliminary も低価値**（divergence 説明済、(b) は dichotomy 出せず）→ wind-down。**current-pair FF@4-vs-FF@10 = optional low-value**（comp5 が既に substep-mitigates-not-fixes を示す）→ skip 可。
- **FF baseline は open-loop-drift-limited**: #18 re-measure DoD = **ik_chord が FF に match**（open-loop で 771 完走でなく; closed-loop RL correction は別 stage）。#18 A1/A2/A3 の目標は **ik_chord=FF**、golden 771 の open-loop 再現でない。

**disposition**: substrate-gap thread = **WIND-DOWN / CLOSED-as-re-discovery**（not a substrate regression; open-loop drift = known）。⇒ **#18 arc が primary に復帰**（substrate-gap は #18 を reframe/強化した detour）。#18 flow 再開: revised design v2.2（A1/A2/A3、§10.10-10.12）→ GO-now（B4-shadow + B5a、pN B1-B7 適用後）→ re-debate（L3、A1 mechanism threshold-TBD）→ impl（fenced、§C ratify + Rs sign-off）。再 open は training が substrate 問題を示した時のみ（新 node + evidence）。⭐**learned**: 診断推奨前に prior-art check（§運用4/V7-V10）— FF@10 は comp5 既存だった（p5/p4 双方 miss）。

## §11 REVISED DESIGN v2.2 — CONSOLIDATED（re-debate-ready、2026-07-19 02:3x — §10.10-10.12 を統合。substrate-gap CLOSED §10.13.5、#18 primary）
**root（§10.8/§10.11、M-b2 CONFIRMED）**: 右腕 IK が recorded と別 discrete config branch（4.32rad off: shoulder j14/elbow j16/wrist j17,j19）を解く。grasp(step90) から wrong branch、warm-start 連続で route 全体に伝播、flip config が fragile → mid-route(176-195) で grip 剥離 → drop。左腕は recorded 一致。orientation 一致(clampR 0.82mm)ゆえ within-step-bow でも orientation でもない。fix DIRECTION = recorded-branch へ IK を pin（L3 が airtight 確認）。

### §11.1 A1 — branch/flip guard on jq_targets（HIGH、AMEND-2⇄AMEND-1 self-consistent 化）
- **挿入点**: `_apply_actions_batch` の ik_chord branch、`jq_targets = _solve_ik_batch(...)`（`:1235`）後・NaN/finger 処理（`:1236-1243`）後・`old_fk_jq`（`:1246`）/interp（`:1254`）**前**。
- **guard**: 各 arm joint で `wrap_dist(jq_targets[j], recorded_arm_q[next_f[t]][j])` を計算 → max > **branch_threshold** なら **fall back: jq_targets[arm] = recorded_arm_q[next_f[t]][arm]**（cross-branch delta を `:1254` に絶対流さない）。⇒ jq_targets 常に recorded branch（IK 解 or recorded fallback）→ interp 常に on-branch。
- **fall-back**（primary）= recorded[next_f] 差し替え（residual をその step reject、on-branch 維持、LOUD log）。**alt**（B6-char が頻繁 trigger 示せば）= clamped-IK（joint-space step 制限で partial residual を on-branch 保持）。
- ⛔ **LOUD fail**（CC5 CH-4）: `recorded arm_q` None（ik_chord は arm_q OPTIONAL）なら silent に settled seed へ fallback せず **raise/log**。
- **branch_threshold = TBD via B6-char（post-auth）**: 正常 per-step joint 運動（≪0.5rad）と branch flip（~2-4rad）の間。re-debate は **mechanism を threshold-TBD で vet**（threshold は B6-char 実測後 tune、singularity 近傍 minima-merge に注意 CC4 CH-D）。

### §11.2 A2 — frame spec（2 consumer distinct frame、CC5 CH-2）
- **`old_fk_jq[0] = recorded arm_q[step_f[0]]`**（interp START、step-START frame）: reset で **`_per_world_fk_jq`-ONLY** の ARM coords {0-5,14-19} を recorded[step_f[0]] で seed（`:1057` copy 後、gripper coords は `:934-940` patch 維持、`_settled_fk_jq` 不触=O1）。N≥1 は commit chain（`:1283`）で recorded[step_f[N]]。
- **`jq_starts[t] = recorded arm_q[next_f[t]]`**（IK seed、target frame）: `_per_world_fk_jq` から **decouple** し毎 step（step 0 含む）recorded[next_f[t]] から reseed。
- ⇒ 両 read が recorded branch、distinct frame。⚠ route_executor indexing（`:4547`/`:4760`/`:5042`）は impl 時 %12 confirm。

### §11.3 A3 — step-0 pop（accept + verify、CC5 CH-1/6）
- `_per_world_fk_jq`-only（A2/O1）は `:1094` を settled に残す ⇒ step-0 で settled→recorded ~4.32rad **arm pop**（kinematic、PD damping なし）。**FF 同等**（FF も `:1094` からの pop を survive）ゆえ **accept** + **step-0 visual/measurement verify leg**（DoD）。verify FAIL 時のみ revisit（reset で physics arm+bodies を recorded FK に re-pose = 大 reset 改変）。

### §11.4 DoD（re-measure、§10.13.5 confirm: **ik_chord = FF に match**、golden 771 open-loop 完走でない）
FF は open-loop-drift-limited ゆえ #18 success = **ik_chord が FF に一致**（closed-loop RL correction は別 stage）。residual 0 で:
- **cable-seg world-disp ≈ 1×arm**（≈34mm, not 80.8mm、AMEND-4 falsifiable gate）∧ **fingertip_r_to_cable ≈ 6mm** ∧ **右 config ≈ recorded(~0rad)** ∧ **contact_r=True + dual-load**（held_z floor 非 trip、G3 到達）。
- **step-0 visual**（A3 pop benign 確認）。
- **guard LOUD-fail 検証** + **wc>1 validation**（held-world frame-clamp、fork-B 前、CC5 CH-5）。
- **nonzero-residual leg**（AMEND-2/B6、post-auth: basin 境界を cross、guard verify、within-step log）。

### §11.5 invariant + C7 Rs surface
- **invariant 不触**: seed/guard = 標準 IK 入力（DiffIK 内、control 方式変更でない）・no-kinematic-trick（IK 解で到達）・dual-arm/88mm/コ 不変・position-only+held-KO 保持。§0 抵触なし。
- ⭐ **C7 Rs surface（§0-adjacent、fix-blocker でない、要 Rs 1 行）**: 既存 kinematic arm joint_q drive（`route_executor.py:236` qd=0 / `:1272`）の trainer 認可未 ratify（§0#5「no-trick 例外=clip-pin のみ」に adjacent）。私の fix は本 drive 内=inheritance-compliant だが前提 ratify=Rs 専権。

### §11.6 impl guards + gate chain
- impl guards: (a) `recorded arm_q` 存在 assert/LOUD（現 FF path のみ `:5033`）(b) held/frozen world は `apply_recorded_arm_ff`（`:5045`）と同 hold_mask frame-clamp を seed lookup に (c) recorded arm_q 28-wide 同 layout・finger-open overwrite（`:1175-1178`）を新 seed で維持。
- gate chain: 本 §11（design）→ **%12 re-debate（L3、A1 mechanism threshold-TBD）** → rule-check → impl（AMEND-1..3 + guards）→ re-measure（§11.4 DoD）。**fenced until re-debate PASS + §C ratify + Rs sign-off**。A1 threshold は B6-char（post-auth、re-debate 後）で tune。

## §9 cites（p5 自読 2026-07-18）
| 項 | cite |
|---|---|
| drive-dependent | `ikchord_deadlock_render/run.log`（ik_chord drop 267 −10）/ `run_ff.log`（FF holds 300 −0.01）/ L3 verdict `:17-21` |
| 右腕 22mm / dual load | `grip_retention_measure/per_step_metrics.json`（step 254-267 contact_r=False・r_near~22mm・grip_r=1.0）/ L3 verdict `:23-24`（GOLDEN dual r_grip_N=119.3）|
| ik_chord IK | `newton_route_env.py:1158-1197`（target = recorded base + residual）/ `:1003-1008`（`_solve_ik_batch` IK_ITERATIONS_RL）/ `:1290-1291`（`_last_ik_resid` obs[55:57]）|
| IK iters | `newton_skill_env_base.py:99`（IK_ITERATIONS_RL=30）/ `newton_route_env.py:204`（_AC_IK_ITERATIONS_P0=400「88mm span」）|
| solref | `task_config.py:187`（MUJOCO_PAD_SOLREF=−65789,−2105 TRUE-overdamp）/ SRG `:109`（R6 best）|
| invariant | RS71 §0（dual-arm/88mm/DiffIK/コ/no-trick）/ `task_config.py:235`（GRIP_HALF_SPAN=0.044）|
| harness false-prov | `measure_grip_retention.py:82-84`（module 定数 assert、CC5 CH1）|
