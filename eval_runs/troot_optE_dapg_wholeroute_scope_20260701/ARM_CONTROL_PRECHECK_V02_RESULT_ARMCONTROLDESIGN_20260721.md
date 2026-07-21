# `/pre-check` 結果 — 前向き腕制御設計 v0.2 = **BLOCK**（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**対象:** `ARM_CONTROL_FORWARD_DESIGN_V02_ARMCONTROLDESIGN_20260721.md`（私 = p11 の設計）。
**Verdict: ⛔ BLOCK**（13 issues = CRITICAL 4 / HIGH 5 / MEDIUM 4）。⇒ **redesign + pre-check 再実行が要る**（skill Step 4）。
**検証者:** Claude sub-agent（`/pre-check` protocol Step 3）。⚠ 検証者は **MuJoCo 3.8.1 で `mj_fullM` を計算し、ramp→stop→settle を直接 sim** して数値を出している（doc 読解のみでない）。

⛔ **私は検証者の報告をそのまま採らない。** 主要 3 件は **私が原文で独立確認**した（下記「私の確認」列）。

---

## 1. CRITICAL 4 件

### C-1 ⛔ §2.3 の一次系近似が高慣性関節で成立しない（＝ 本設計の中心結論が崩れる）

- 検証者: 実慣性 `M(shoulder_pan)=3.498`, `M(shoulder_lift)=3.294 kg·m²`。servo 則 `f = kp(ctrl−q) − kd·q̇` ⇒ `ζ = kd/(2√(kp·M))`。
  → **vendor ζ≈2.4（過減衰・一次系近似 OK）／C-1 ζ≈0.60／C-2 ζ≈0.42 = いずれも不足減衰**。
  → 不足減衰域では包絡減衰は `exp(−kd·t/2m)`、時定数 `τ = 2m/kd` で **`ke` に依存しない**。C-1/C-2 は `kd=100` 共通 ⇒ **τ 同一**。
  → sim 実測: 整定 vendor 0.864 s（予測 0.93・整合）/ **C-1 0.196 s（予測 0.16）/ C-2 0.202 s（予測 0.064 = 216% 過小・しかも C-1 より遅い）**。
- ⭐**根本原因（私が原文確認 ✅）**: banked の `0.512 rad` は **`wrist_2`** の値。
  `ARM_CONTROL_PD1_RESULT_RSTECHLEAD_20260719.md:35` 逐語「**worst joint = wrist_2**（both arms, symmetric 0.512）」。
  `wrist_2` は size1（`ke=500`・armature 支配の低慣性）。**私はそれを 30 倍以上重い肩関節へ一般化した。**
- ⛔ **失敗の型 = 同じ定数を別の測定面へ持ち込んだ**（[[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]]）。⚠ **私が §14.27 の訂正で他者に指摘したのと同じ型を、自分が踏んだ。**
- **FIX 方向**: `t_settle` を二次系形へ。gain 候補は **`ζ ≥ 1`（最高慣性配置で）**を制約にする。`T_lag = kd/ke` を下げたいなら **`kd` を切るのでなく `ke` を上げる**（`kd` を切ると ζ が落ちる）。

### C-2 ⛔ 重力ドループで bar (i)(iii) が広範囲で到達不能

- **私が原文確認 ✅**: `test_newton_clip_routing.py:125` `GRAVITY = -9.81`、`:1058` / `:1731` `ModelBuilder(gravity=GRAVITY)`。⇒ **env7 は重力 ON**。
  ⚠ PhysX/Franka 側の `disable_gravity=True`（`CLAUDE.md` DiffIK 節）を**流用してはならない**（substrate 混同）。
- 純 PD（重力補償なし）は定常誤差 `err = τ_gravity/ke` が**恒久的に残る**（整定時間の問題ではない）。検証者測定 = **13.1〜26.2 mrad**。
  → bar (i) 2 mrad = grid の **0%**、bar (iii) 5 mrad = **8.3%** しか満たさない（vendor）。
- **FIX 方向**: **重力フィードフォワード**。`Control.joint_f` は `SolverMuJoCo` で support（`solvers.py:308`）、`gravcomp` も配線済（`solver_mujoco.py:717-724`）だが **`newton_route_env.py` では未使用**。⇒ bar (i)(iii) は **重力補償を前提条件として宣言**するか、`q − q_equilibrium` の bar に置き換える。

### C-3 ⛔ 飽和余裕の読み違い + C-1/C-2 は肩で cap に当たる

- **私が原文確認 ✅**: `…PD1_RESULT…:33` 逐語「**0.0% on every joint. Max |f_raw| at the worst joint = 25.1 N·m < 28 cap**」。
  ⇒ **25.1/28 = cap の 89.6% 消費・余裕 10.4%**。私は v0.2 §2 で「力 = FEASIBLE 確立」と**余裕があるように書いた** = 過大表現。
- 検証者 sim: **C-1 / C-2 とも shoulder_lift が 150 N·m = cap 100% 到達**（飽和 frame 1.4% / 7.0%）。
- ⛔ **含意が重い**: 飽和すると servo は開ループになり、**§2.1 の lag 則 `err = T_lag·ω` が成立しなくなる** ⇒ bar 構造の前提そのものが、bar が効くべき過渡でだけ消える。
- ⚠ 出典の推奨とも矛盾: `:59` は「**kd/ke 比であって ke 絶対値ではない**」を lever としているのに、C-2 は ke 絶対値を変える。
- **FIX 方向**: saturation leg を **bar 凍結の前**に置く。高慣性×重力負荷配置で掃く（wrist 支配の記録軌道の再生では出ない）。

### C-4 ⛔ R-ROBUST の根拠が出典を反転していた（**私の誤読**）

- **私が原文確認 ✅**（`…PD1_RESULT…:20-24` 逐語）:
  > 「Same build, same seed, **kinematic drive both**; ONLY the imported-actuator tug removed … Arm q divergence R0-vs-R1 ≤ **1.1 mrad**（**the kinematic drive forces the same arm poses**）⇒ the flip is carried **entirely by the CABLE-side physics response** to the hidden saturated tug.」
- ⇒ **arm q は統制変数（動かさなかった側）**。1.1 mrad はその残差であり、**arm q 感度の証拠ではない**。実証された感度は **cable 側の接触/引張応答**。
- 私は v0.2 §3 で「arm q 差 ≤1.1 mrad で連鎖が全滅する」と書いた ＝ **「arm は原因ではない」を「arm が 1 mrad 感度の原因」へ反転**させた。
- ⇒ **R-ROBUST-1/2（cable 初期姿勢・毎ステップ指令摂動）は、実証された故障ドライバを一切励起しない。** 摂動軸の再導出が要る（**cable 側の接触力/摩擦/保持**）。
- ⚠ **上流にも緩い表現**: charter `:334`「1mrad 級で連鎖が flip する振付」は、同 charter `:331`「flip は **cable 側** knife-edge 応答」と食い違う。⇒ **charter も訂正対象**（現 owner = p11）。
- ⚠ **W-2 却下の根拠にも波及**（v0.1 §1.1 で R-ROBUST 不適合を理由の 1 つにしていた）⇒ 却下自体は L-P0 本体（旧振付は清潔基盤で連鎖しない）で立つが、**理由の 1 本は撤回**。

---

## 2. HIGH / MEDIUM（要点のみ・全文は検証者出力）

| # | 指摘 | 私の扱い |
|---|---|---|
| H-1 | 「`T_lag` 高レバレッジ・減速は低レバレッジ」論は自己矛盾（C-2 の利得は結局 `ln` 経路＝自分が低レバレッジと切り捨てた channel から来る。減速は**飽和とリンギングの両方**に線形に効く唯一の lever） | ✅ 受理。§2.3 の結論を撤回し、lever を **整定・飽和・ζ の 3 制約**で再序列化する |
| H-2 | bar (iv) no-ringing を「C-1/C-2 の probe 出力」で決めるのは**別様に出得ない test**（提案 gain 自身が生むリンギングが bar になる）。検証者 sim の overshoot = C-1 20.3 / C-2 29.9 mrad（重力 ON で 45.5 / 70.9） | ✅ 受理。(iv) は **task 要件（clip 着座が許す overshoot）から probe 前に決める** |
| H-3 | M-6 guard は重力ドループで常時発火し、かつ「ドループ/障害/飽和/真の故障」を判別しない | ✅ 受理。`q − q_equilibrium` 化 or 飽和・接触フラグで分離 |
| H-4 | §4.2 の指令空間積分に **anti-windup が無い** — 障害物で `cmd` が進み続け cap 張り付きの持続押し込みになる。`IKObjectiveJointLimit` は weight=10 の**軟**目的（`newton_route_env.py:883`）で硬拘束でない | ✅ 受理。⭐**M-3 を壊さない解**あり = realized q を **seed でなく guard** に使い、`|q−ctrl|` 超過時に `cmd` の前進を**凍結**（reset しない） |
| H-5 | §4.1「EE 空間は余裕」は自分の banked 証拠と矛盾（`tr_EE_max` = **99.9 mm** vs bar 3 mm）。指令 step と追従誤差を混同 | ✅ 受理。§4.1 を追従誤差の言葉で書き直す |
| M-1 | W-1 は循環を**移設**した（振付←residual←trainer←振付 / bar←probe←W-b） | 🔶 部分受理。**制御側から外乱抑圧 budget を宣言して trainer へ渡す**（借りるのでなく上限を与える）で loop 1 を切る |
| M-2 | R-ROBUST は摂動量も合格率も未定＝**反証不能**なのに W-2 却下に使われている | ✅ 受理（C-4 と同根）。数値を入れるか「未だ要件でない」と明示するまで却下根拠から外す |
| M-3 | M-1 は既存 `servo_readback_assert` の負対照（「arm に servo は無い」）を**無言で空洞化**する | ✅ 受理。M-1 と**同じ変更で** 12 本の arm DOF readback assert を出す |
| M-4 | bar (i) 2 mrad は kinematic 駆動下（`\|q−ctrl\|≈0` が恒等）で得た値 ⇒ PD 面では情報を持たない | ✅ 受理。(i) も**未凍結**へ戻す |

---

## 3. 検証者が「健全」と確認した部分（過剰に広く読まないため明示）

- **substrate 主張は全て成立**: `joint_target_mode`（`solvers.py:301`）/ `joint_effort_limit`（`:263`）/ `joint_target_ke,kd`（`:294`）/ equality（`:330`）/ mimic（`:337`・脚注 REVOLUTE・PRISMATIC 限定 = 2F-85 4-bar に十分）。POSITION mode は `gainprm=[kp]`, `biasprm=[0,−kp,−kd]` に写り、effort は `actfrcrange`（`solver_mujoco.py:4976-4978`, `:5048`）。⇒ **§1 M-1 の可用性判定は維持**。
- **§2.1 の lag 則は正しい**（二次系でも ramp 定常で `err = T_lag·ω` が成立。実測 470.2/123.1/59.0 mrad vs 予測 512/128/64）。
- **§2.1 / §2.3 の算術は全セル再計算して一致**。⇒ **算術は正しく、実装している模型が誤り**。
- **§4.3 の IK 事実は一致**（`IK_ITERATIONS_RL=30` / `IK_STEP_SIZE=1.0` / `DT=1/480`）。Franka/PhysX の λ を持ち込まなかったのは正しい。

⚠ **未検証（検証者申告）**: ζ は配置依存で、W-b の実 waypoint が無いため「実経路のどれだけが不足減衰域か」は不明。§4.4 の substep 保持仮説も未検証。

---

## 4. 私の結論

1. **v0.2 は設計前提として使えない**（BLOCK）。§2.3 の中心結論は撤回。
2. ⭐**最も重いのは C-4（私の誤読）** — 数値の誤りでなく **証拠の向きを反転**させ、それを R-ROBUST の設計根拠と W-2 却下理由に使った。**同型の誤りを §14.27 で他者に指摘した直後に自分が踏んだ**ことを記録する。
3. **C-1/C-2 probe（prereg v1.4 `3793258e7c`）は再改訂が要る**: 現 scope のままでは **既に反証された模型を確認するだけ**になる。測るべきは per-joint の **ζ / overshoot / 飽和**を**重力負荷・高慣性配置**で。
4. ⛔ **p0 は動けない**（BLOCK・gates 未通過）。

## 5. 次版で直す順（fix-first・緩和でなく根治）

1. **重力補償を設計に入れる**（`Control.joint_f` or `gravcomp`）— これ無しでは bar が原理的に満たせない。
2. **gain 選定基準を `kd/ke` 比から `ζ`（最高慣性配置）へ**。`ke` を上げる方向は **cap 飽和**と衝突するので、飽和余裕と同時に解く。
3. **R-ROBUST の摂動軸を cable 側へ再導出**（+ 摂動量と合格率を数値化して反証可能にする）。
4. **bar (i)(iv) を probe 前に task 要件から決める**（probe 出力で決めない）。
5. **anti-windup を M-3 非破壊の形で追加**（realized q は guard 用途に限る）。
6. **M-1 に arm DOF の readback assert を同梱**。
7. → **`/pre-check` 再実行**（skill Step 4: BLOCK は再設計 + 再検証が必須）。

## 6. 非主張
- 検証者の sim 数値（ζ・整定・飽和・overshoot）は **私が再現していない**。私が独立確認したのは **原文 3 件（wrist_2 / 重力 ON / 25.1 vs 28）** のみ。⇒ sim 由来の値は **検証者帰属**として扱う。
- 設計を修正していない（本書は gate 記録）。bar を動かしていない。実装していない。
